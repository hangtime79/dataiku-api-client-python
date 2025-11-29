"""Discovery Agent orchestrator.

This module implements the DiscoveryAgent class which orchestrates the
complete discovery workflow across all components.
"""

from typing import Dict, List, Any, Optional
from dataikuapi import DSSClient
from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler
from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
from dataikuapi.iac.workflows.discovery.schema_extractor import SchemaExtractor
from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
from dataikuapi.iac.workflows.discovery.models import BlockMetadata


class DiscoveryAgent:
    """
    Orchestrates the complete discovery workflow.

    The DiscoveryAgent coordinates all discovery components to:
    1. Crawl project flows
    2. Identify valid blocks
    3. Enrich with schemas
    4. Generate catalog entries

    Attributes:
        client: DSSClient instance
        verbose: Enable progress logging
        crawler: FlowCrawler instance
        identifier: BlockIdentifier instance
        schema_extractor: SchemaExtractor instance
        catalog_writer: CatalogWriter instance

    Example:
        >>> client = DSSClient(host, api_key)
        >>> agent = DiscoveryAgent(client, verbose=True)
        >>> results = agent.run_discovery("MY_PROJECT")
        >>> print(f"Found {results['blocks_found']} blocks")
    """

    def __init__(self, client: DSSClient, verbose: bool = False):
        """
        Initialize DiscoveryAgent with DSSClient.

        Args:
            client: Authenticated DSSClient instance
            verbose: Enable progress logging (default: False)
        """
        self.client = client
        self.verbose = verbose

        # Initialize components
        self.crawler = FlowCrawler(client)
        self.identifier = BlockIdentifier(self.crawler)
        self.schema_extractor = SchemaExtractor(client)
        self.catalog_writer = CatalogWriter(client=client)  # Pass client for persistence

    def run_discovery(self, project_key: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        Run complete discovery workflow on a project.

        Orchestrates the full discovery process:
        1. Crawl project to find zones
        2. Identify valid blocks
        3. Enrich blocks with schemas
        4. Generate catalog entries (unless dry_run)

        Args:
            project_key: Project identifier
            dry_run: If True, identify blocks but don't write catalog

        Returns:
            Dictionary with discovery results:
            {
                'project_key': str,
                'blocks_found': int,
                'blocks_cataloged': int,
                'blocks': List[BlockMetadata],
                'dry_run': bool
            }

        Example:
            >>> results = agent.run_discovery("MY_PROJECT")
            >>> print(f"Cataloged {results['blocks_cataloged']} blocks")
        """
        if self.verbose:
            print(f"Starting discovery for project: {project_key}")

        # Step 1: Crawl project
        if self.verbose:
            print("Step 1: Crawling project zones...")
        zones = self.crawl_project(project_key)
        if self.verbose:
            print(f"  Found {len(zones)} zones")

        # Step 2: Identify blocks
        if self.verbose:
            print("Step 2: Identifying valid blocks...")
        blocks = self.identify_blocks(project_key)
        if self.verbose:
            print(f"  Identified {len(blocks)} valid blocks")

        # Step 3: Enrich with schemas
        if self.verbose:
            print("Step 3: Enriching blocks with schemas...")
        enriched_blocks = []
        for block in blocks:
            enriched = self.enrich_schemas(block)
            enriched_blocks.append(enriched)
        if self.verbose:
            print(f"  Enriched {len(enriched_blocks)} blocks with schemas")

        # Step 4: Write to project-local registry (unless dry_run)
        write_results = None
        if not dry_run:
            if self.verbose:
                print("Step 4: Writing blocks to project-local registry...")

            write_results = self.catalog_writer.write_to_project_registry(
                project_key, enriched_blocks
            )

            if self.verbose:
                print(f"  Wrote {write_results['blocks_written']} blocks")
                print(f"  Wiki articles: {len(write_results['wiki_articles'])}")
                print(f"  Schemas: {write_results['schemas_written']}")
                print(f"  Index updated: {write_results['index_updated']}")
        else:
            if self.verbose:
                print("Step 4: Skipped (dry-run mode)")

        # Build results
        results = {
            "project_key": project_key,
            "blocks_found": len(blocks),
            "blocks_cataloged": write_results['blocks_written'] if write_results else 0,
            "blocks": enriched_blocks,
            "dry_run": dry_run,
        }

        # Add write details if available
        if write_results:
            results["write_results"] = write_results

        if self.verbose:
            print(f"\nDiscovery complete!")
            print(f"  Project: {project_key}")
            print(f"  Blocks found: {results['blocks_found']}")
            if not dry_run:
                print(f"  Blocks cataloged: {results['blocks_cataloged']}")
                print(f"  Location: {project_key}/Wiki/_DISCOVERED_BLOCKS/")
            else:
                print(f"  Mode: DRY RUN (no catalog writes)")

        return results

    def crawl_project(self, project_key: str) -> List[str]:
        """
        Crawl project to find zones.

        Args:
            project_key: Project identifier

        Returns:
            List of zone names
        """
        return self.crawler.list_zones(project_key)

    def identify_blocks(self, project_key: str) -> List[BlockMetadata]:
        """
        Identify valid blocks in project.

        Args:
            project_key: Project identifier

        Returns:
            List of BlockMetadata for valid blocks
        """
        return self.identifier.identify_blocks(project_key)

    def enrich_schemas(self, metadata: BlockMetadata) -> BlockMetadata:
        """
        Enrich block metadata with schemas.

        Args:
            metadata: BlockMetadata to enrich

        Returns:
            Enriched BlockMetadata with schema references
        """
        return self.schema_extractor.enrich_block_with_schemas(metadata)

    def generate_catalog_entry(self, metadata: BlockMetadata) -> Dict[str, Any]:
        """
        Generate catalog entry for a block.

        Creates wiki article and summary for catalog index.

        Args:
            metadata: BlockMetadata to catalog

        Returns:
            Dictionary with catalog entry:
            {
                'wiki_article': str,
                'summary': str,
                'wiki_path': str
            }
        """
        wiki_article = self.catalog_writer.generate_wiki_article(metadata)
        summary = self.catalog_writer.generate_block_summary(metadata)
        wiki_path = self.catalog_writer.get_wiki_path(metadata)

        return {
            "wiki_article": wiki_article,
            "summary": summary,
            "wiki_path": wiki_path,
        }
