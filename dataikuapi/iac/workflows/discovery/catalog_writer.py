"""Catalog Writer for Discovery Agent.

This module implements the CatalogWriter class which writes block metadata
to the catalog including wiki articles, JSON index, and schema files.
"""

from typing import Dict, List, Any, Optional
import json
import re
from dataikuapi import DSSClient
from dataikuapi.iac.workflows.discovery.models import BlockMetadata, BlockSummary
from dataikuapi.iac.workflows.discovery.exceptions import CatalogWriteError


class CatalogWriter:
    """
    Writes block metadata to the catalog.

    The CatalogWriter implements Algorithm 5 (Wiki Article Generation) and
    handles writing blocks to project-local registries and BLOCKS_REGISTRY:
    - Project-local: Full discovery written to PROJECT/Wiki/_DISCOVERED_BLOCKS/
    - BLOCKS_REGISTRY: Links to project-local registries (references only)

    Supports two modes:
    1. Content generation only (client=None): For testing/dry-run
    2. Full persistence (client provided): Writes to Dataiku

    Example:
        >>> # Generation only
        >>> writer = CatalogWriter()
        >>> article = writer.generate_wiki_article(block_metadata)

        >>> # With persistence
        >>> writer = CatalogWriter(client=client)
        >>> result = writer.write_to_project_registry(project_key, blocks)
    """

    def __init__(self, client: Optional[DSSClient] = None):
        """
        Initialize CatalogWriter.

        Args:
            client: Optional DSSClient for write operations.
                   If None, only content generation is available.
        """
        self.client = client

    def generate_wiki_article(self, metadata: BlockMetadata) -> str:
        """
        Generate wiki article from block metadata.

        Implements Algorithm 5 from the specification:
        - YAML frontmatter with metadata
        - Title and description
        - Inputs and outputs tables
        - Contains section
        - Dependencies section
        - Usage example
        - Changelog

        Args:
            metadata: BlockMetadata object

        Returns:
            Markdown string for wiki article

        Example:
            >>> article = writer.generate_wiki_article(metadata)
            >>> print("---" in article)  # Has frontmatter
            True
        """
        if metadata is None:
            raise CatalogWriteError("Cannot generate article from None metadata")

        sections = []

        # 1. YAML Frontmatter
        sections.append(self._generate_frontmatter(metadata))

        # 2. Title
        title = metadata.name or metadata.block_id
        sections.append(f"# {title}")
        sections.append("")

        # 3. Description
        sections.append("## Description")
        sections.append("")
        description = metadata.description or "No description provided."
        sections.append(description)
        sections.append("")

        # 4. Inputs Table
        if metadata.inputs:
            sections.append("## Inputs")
            sections.append("")
            sections.append("| Name | Type | Required | Description |")
            sections.append("|------|------|----------|-------------|")
            for inp in metadata.inputs:
                required = "Yes" if inp.required else "No"
                desc = inp.description or ""
                sections.append(f"| {inp.name} | {inp.type} | {required} | {desc} |")
            sections.append("")

        # 5. Outputs Table
        if metadata.outputs:
            sections.append("## Outputs")
            sections.append("")
            sections.append("| Name | Type | Description |")
            sections.append("|------|------|-------------|")
            for out in metadata.outputs:
                desc = out.description or ""
                sections.append(f"| {out.name} | {out.type} | {desc} |")
            sections.append("")

        # 6. Contains Section
        sections.append("## Contains")
        sections.append("")
        if metadata.contains.datasets:
            datasets_list = ", ".join(metadata.contains.datasets)
            sections.append(f"**Datasets:** {datasets_list}")
            sections.append("")
        if metadata.contains.recipes:
            recipes_list = ", ".join(metadata.contains.recipes)
            sections.append(f"**Recipes:** {recipes_list}")
            sections.append("")
        if metadata.contains.models:
            models_list = ", ".join(metadata.contains.models)
            sections.append(f"**Models:** {models_list}")
            sections.append("")

        # 7. Dependencies Section
        if metadata.dependencies:
            sections.append("## Dependencies")
            sections.append("")
            if metadata.dependencies.get("python"):
                python_deps = ", ".join(metadata.dependencies["python"])
                sections.append(f"- **Python:** {python_deps}")
                sections.append("")
            if metadata.dependencies.get("plugins"):
                plugin_deps = ", ".join(metadata.dependencies["plugins"])
                sections.append(f"- **Plugins:** {plugin_deps}")
                sections.append("")

        # 8. Usage Example
        sections.append("## Usage")
        sections.append("")
        sections.append("```yaml")
        sections.append("blocks:")
        sections.append(
            f'  - ref: "BLOCKS_REGISTRY/{metadata.block_id}@{metadata.version}"'
        )
        if metadata.inputs:
            sections.append("    inputs:")
            first_input = metadata.inputs[0]
            sections.append(f"      {first_input.name}: your_dataset")
        if metadata.outputs:
            sections.append("    outputs:")
            first_output = metadata.outputs[0]
            sections.append(f"      {first_output.name}: your_output")
        sections.append("```")
        sections.append("")

        # 9. Changelog
        sections.append("## Changelog")
        sections.append("")
        sections.append(f"- {metadata.version}: Initial release")
        sections.append("")

        return "\n".join(sections)

    def _generate_frontmatter(self, metadata: BlockMetadata) -> str:
        """
        Generate YAML frontmatter for wiki article.

        Args:
            metadata: BlockMetadata object

        Returns:
            YAML frontmatter string
        """
        frontmatter = ["---"]
        frontmatter.append(f"block_id: {metadata.block_id}")
        frontmatter.append(f"version: {metadata.version}")
        frontmatter.append(f"type: {metadata.type}")
        frontmatter.append(f"blocked: {metadata.blocked}")
        frontmatter.append(f"source_project: {metadata.source_project}")
        if metadata.source_zone:
            frontmatter.append(f"source_zone: {metadata.source_zone}")
        if metadata.hierarchy_level:
            frontmatter.append(f"hierarchy_level: {metadata.hierarchy_level}")
        if metadata.domain:
            frontmatter.append(f"domain: {metadata.domain}")
        if metadata.tags:
            tags_yaml = json.dumps(metadata.tags)
            frontmatter.append(f"tags: {tags_yaml}")
        frontmatter.append("---")
        frontmatter.append("")

        return "\n".join(frontmatter)

    def generate_block_summary(self, metadata: BlockMetadata) -> str:
        """
        Generate block summary JSON for catalog index.

        Args:
            metadata: BlockMetadata object

        Returns:
            JSON string with block summary
        """
        summary = BlockSummary.from_metadata(metadata)
        return json.dumps(summary.to_dict(), indent=2)

    def merge_catalog_index(
        self, existing_index: Dict[str, Any], metadata: BlockMetadata
    ) -> Dict[str, Any]:
        """
        Merge block into catalog index.

        Adds new block or updates existing block in the index.

        Args:
            existing_index: Existing catalog index dict
            metadata: BlockMetadata to merge

        Returns:
            Updated catalog index dict

        Example:
            >>> index = {"blocks": []}
            >>> updated = writer.merge_catalog_index(index, metadata)
            >>> len(updated["blocks"])
            1
        """
        # Ensure blocks list exists
        if "blocks" not in existing_index:
            existing_index["blocks"] = []

        # Create summary for this block
        summary = BlockSummary.from_metadata(metadata)
        summary_dict = summary.to_dict()

        # Check if block already exists
        found = False
        for i, block in enumerate(existing_index["blocks"]):
            if block.get("block_id") == metadata.block_id:
                # Update existing block
                existing_index["blocks"][i] = summary_dict
                found = True
                break

        # Add new block if not found
        if not found:
            existing_index["blocks"].append(summary_dict)

        return existing_index

    def generate_schema_file(self, schema: Dict[str, Any]) -> str:
        """
        Generate schema file content.

        Args:
            schema: Schema dict

        Returns:
            JSON string with pretty-printed schema
        """
        return json.dumps(schema, indent=2)

    def extract_changelog(self, existing_article: str) -> str:
        """
        Extract changelog section from existing wiki article.

        Args:
            existing_article: Existing article markdown

        Returns:
            Changelog section content or empty string
        """
        # Find changelog section
        changelog_pattern = r"## Changelog\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(changelog_pattern, existing_article, re.DOTALL)

        if match:
            return match.group(1).strip()

        return ""

    def merge_wiki_article(self, existing_article: str, metadata: BlockMetadata) -> str:
        """
        Merge new metadata with existing wiki article.

        Preserves manual edits like changelog while updating metadata.

        Args:
            existing_article: Existing article markdown
            metadata: New BlockMetadata

        Returns:
            Merged article markdown

        Example:
            >>> merged = writer.merge_wiki_article(existing, new_metadata)
            >>> "1.0.0: Initial release" in merged  # Preserves old changelog
            True
        """
        # Extract changelog from existing article
        old_changelog = self.extract_changelog(existing_article)

        # Generate new article
        new_article = self.generate_wiki_article(metadata)

        # If we have old changelog, append it to new article
        if old_changelog:
            # Replace the default changelog with merged version
            new_changelog_line = f"- {metadata.version}: Initial release"

            # Build merged changelog
            merged_changelog = f"- {metadata.version}: Updated\n{old_changelog}"

            # Replace in article
            new_article = new_article.replace(new_changelog_line, merged_changelog)

        return new_article

    def get_wiki_path(self, metadata: BlockMetadata) -> str:
        """
        Get wiki path for block based on hierarchy.

        Organizes blocks by hierarchy level in wiki structure.

        Args:
            metadata: BlockMetadata object

        Returns:
            Wiki path string

        Example:
            >>> path = writer.get_wiki_path(metadata)
            >>> "process" in path  # If hierarchy_level is "process"
            True
        """
        # Base path
        base = "BLOCKS_REGISTRY"

        # Organize by hierarchy if available
        if metadata.hierarchy_level:
            path = f"{base}/{metadata.hierarchy_level}/{metadata.block_id}"
        else:
            path = f"{base}/other/{metadata.block_id}"

        return path

    # -------------------------------------------------------------------------
    # Project-Local Registry Write Operations
    # -------------------------------------------------------------------------

    def write_to_project_registry(
        self, project_key: str, blocks: List[BlockMetadata]
    ) -> Dict[str, Any]:
        """
        Write blocks to project-local registry.

        Writes discovery results to:
        - Wiki: PROJECT/Wiki/_DISCOVERED_BLOCKS/{block_id}.md
        - Library: PROJECT/Library/discovery/index.json
        - Library: PROJECT/Library/discovery/schemas/{block_id}_{port}.schema.json

        Args:
            project_key: Project to write to
            blocks: List of blocks to write

        Returns:
            Dict with write results:
            {
                'project_key': str,
                'blocks_written': int,
                'wiki_articles': List[str],
                'schemas_written': int,
                'index_updated': bool
            }

        Raises:
            CatalogWriteError: If client is None or write fails

        Example:
            >>> result = writer.write_to_project_registry("MY_PROJECT", blocks)
            >>> print(f"Wrote {result['blocks_written']} blocks")
        """
        if not self.client:
            raise CatalogWriteError(
                "CatalogWriter requires DSSClient for write operations. "
                "Initialize with: CatalogWriter(client=client)"
            )

        results = {
            "project_key": project_key,
            "blocks_written": 0,
            "wiki_articles": [],
            "schemas_written": 0,
            "index_updated": False,
        }

        # Ensure project registry structure exists
        project = self._ensure_project_registry_exists(project_key)

        # Write each block
        for block in blocks:
            # Write wiki article
            article_id = self._write_wiki_article(project, block)
            results["wiki_articles"].append(article_id)

            # Write schemas
            schema_count = self._write_schemas(project, block)
            results["schemas_written"] += schema_count

            results["blocks_written"] += 1

        # Update discovery index
        self._update_discovery_index(project, blocks)
        results["index_updated"] = True

        return results

    def _ensure_project_registry_exists(self, project_key: str):
        """
        Ensure project has discovery registry structure.

        Creates if missing:
        - Wiki folder: _DISCOVERED_BLOCKS/
        - Library folder: discovery/
        - Library file: discovery/index.json

        Args:
            project_key: Project identifier

        Returns:
            DSSProject instance

        Raises:
            CatalogWriteError: If project doesn't exist or access denied
        """
        try:
            project = self.client.get_project(project_key)
        except Exception as e:
            raise CatalogWriteError(
                f"Failed to access project {project_key}: {e}"
            )

        # Initialize discovery index if it doesn't exist
        try:
            # Get fresh library instance each time to avoid caching issues
            library = project.get_library()
            root_folder = library.root

            # Ensure discovery folder exists
            discovery_folder = root_folder.get_child("discovery")
            if discovery_folder is None:
                # Create discovery folder
                discovery_folder = root_folder.add_folder("discovery")

            # Ensure schemas subfolder exists
            schemas_folder = discovery_folder.get_child("schemas")
            if schemas_folder is None:
                # Create schemas folder within discovery
                schemas_folder = discovery_folder.add_folder("schemas")

            # Check if discovery/index.json exists
            index_file = discovery_folder.get_child("index.json")
            if index_file is None:
                # Create initial index
                initial_index = {
                    "version": "1.0",
                    "project_key": project_key,
                    "blocks": [],
                    "last_updated": None,
                }
                index_file = discovery_folder.add_file("index.json")
                index_file.write(json.dumps(initial_index, indent=2))

        except Exception as e:
            raise CatalogWriteError(
                f"Failed to initialize project registry for {project_key}: {e}"
            )

        return project

    def _ensure_discovered_blocks_folder(self, wiki) -> str:
        """
        Ensure _DISCOVERED_BLOCKS parent article exists.

        Args:
            wiki: DSSWiki instance

        Returns:
            Parent article ID

        Raises:
            CatalogWriteError: If folder creation fails
        """
        try:
            # Try to get existing parent article
            parent_article = wiki.get_article("_DISCOVERED_BLOCKS")
            return parent_article.article_id

        except:
            # Parent doesn't exist, create it
            try:
                parent_content = """# Discovered Blocks

This folder contains automatically discovered reusable blocks from this project.

**Auto-generated by Discovery Agent** - Do not manually create articles here.
"""
                parent_article = wiki.create_article("_DISCOVERED_BLOCKS", parent_id=None, content=parent_content)
                return parent_article.article_id

            except Exception as e:
                raise CatalogWriteError(f"Failed to create _DISCOVERED_BLOCKS folder: {e}")

    def _write_wiki_article(self, project, block: BlockMetadata) -> str:
        """
        Write wiki article for block to project-local registry.

        Creates article as child of _DISCOVERED_BLOCKS parent article.

        If article exists, merges with existing content to preserve
        manual edits (changelogs, custom descriptions).

        Args:
            project: DSSProject instance
            block: BlockMetadata to write

        Returns:
            Article name (block_id)

        Raises:
            CatalogWriteError: If write fails
        """
        try:
            wiki = project.get_wiki()

            # Ensure parent folder exists
            parent_id = self._ensure_discovered_blocks_folder(wiki)

            # Check if article exists (try to get by name)
            try:
                existing_article = wiki.get_article(block.block_id)
                existing_data = existing_article.get_data()
                existing_content = existing_data.get_body()

                # Merge with existing to preserve manual edits
                article_content = self.merge_wiki_article(existing_content, block)

                # Update existing article
                existing_data.set_body(article_content)
                existing_data.save()
                return block.block_id

            except:
                # Article doesn't exist, create new as child of parent
                article_content = self.generate_wiki_article(block)
                new_article = wiki.create_article(
                    block.block_id,
                    parent_id=parent_id,
                    content=article_content
                )
                return block.block_id

        except Exception as e:
            raise CatalogWriteError(
                f"Failed to write wiki article for {block.block_id}: {e}"
            )

    def _write_schemas(self, project, block: BlockMetadata) -> int:
        """
        Write schema files to project-local registry.

        Writes to: PROJECT/Library/discovery/schemas/{block_id}_{port}.schema.json

        Args:
            project: DSSProject instance
            block: BlockMetadata with schemas

        Returns:
            Number of schema files written

        Raises:
            CatalogWriteError: If write fails
        """
        try:
            library = project.get_library()
            root_folder = library.root

            # Get discovery/schemas folder
            discovery_folder = root_folder.get_child("discovery")
            if discovery_folder is None:
                raise CatalogWriteError("discovery folder not found - should have been created in _ensure_project_registry_exists")

            schemas_folder = discovery_folder.get_child("schemas")
            if schemas_folder is None:
                raise CatalogWriteError("schemas folder not found - should have been created in _ensure_project_registry_exists")

            schemas_written = 0

            # Write input schemas
            for inp in block.inputs:
                if hasattr(inp, 'schema') and inp.schema:
                    file_name = f"{block.block_id}_{inp.name}.schema.json"
                    schema_content = self.generate_schema_file(inp.schema)

                    # Check if file exists, update or create
                    schema_file = schemas_folder.get_child(file_name)
                    if schema_file is not None:
                        schema_file.write(schema_content)
                    else:
                        schema_file = schemas_folder.add_file(file_name)
                        schema_file.write(schema_content)

                    schemas_written += 1

            # Write output schemas
            for out in block.outputs:
                if hasattr(out, 'schema') and out.schema:
                    file_name = f"{block.block_id}_{out.name}.schema.json"
                    schema_content = self.generate_schema_file(out.schema)

                    # Check if file exists, update or create
                    schema_file = schemas_folder.get_child(file_name)
                    if schema_file is not None:
                        schema_file.write(schema_content)
                    else:
                        schema_file = schemas_folder.add_file(file_name)
                        schema_file.write(schema_content)

                    schemas_written += 1

            return schemas_written

        except Exception as e:
            raise CatalogWriteError(
                f"Failed to write schemas for {block.block_id}: {e}"
            )

    def _update_discovery_index(self, project, blocks: List[BlockMetadata]):
        """
        Update project-local discovery index.

        Updates: PROJECT/Library/discovery/index.json

        Merges new blocks with existing index, updating versions
        and metadata for existing blocks.

        Args:
            project: DSSProject instance
            blocks: List of blocks to merge into index

        Raises:
            CatalogWriteError: If update fails
        """
        try:
            library = project.get_library()
            root_folder = library.root

            # Get discovery folder
            discovery_folder = root_folder.get_child("discovery")
            if discovery_folder is None:
                raise CatalogWriteError("discovery folder not found - should have been created in _ensure_project_registry_exists")

            # Read existing index
            index_file = discovery_folder.get_child("index.json")
            if index_file is not None:
                index_content = index_file.read()
                existing_index = json.loads(index_content)
            else:
                # Create new index if doesn't exist (shouldn't happen)
                existing_index = {
                    "version": "1.0",
                    "project_key": project.project_key,
                    "blocks": [],
                }

            # Merge each block
            for block in blocks:
                existing_index = self.merge_catalog_index(existing_index, block)

            # Add timestamp
            from datetime import datetime
            existing_index["last_updated"] = datetime.utcnow().isoformat()

            # Write updated index
            index_content = json.dumps(existing_index, indent=2)

            # Write to file (get it again to handle cache refresh)
            index_file = discovery_folder.get_child("index.json")
            if index_file is not None:
                index_file.write(index_content)
            else:
                # File doesn't exist, create it
                index_file = discovery_folder.add_file("index.json")
                index_file.write(index_content)

        except Exception as e:
            raise CatalogWriteError(
                f"Failed to update discovery index: {e}"
            )
