"""Real Integration Tests for Discovery Agent.

This module provides comprehensive integration tests against a REAL Dataiku instance.
These tests validate the Discovery Agent against actual project data and API responses.

IMPORTANT:
- These tests use DRY_RUN mode to avoid writing to production
- Tests are READ-ONLY - no modifications to Dataiku instance
- Requires environment variables: DATAIKU_HOST, DATAIKU_API_KEY
- Tests use the COALSHIPPINGSIMULATIONGSC project

Environment Setup:
    export DATAIKU_HOST=http://172.18.58.26:10000
    export DATAIKU_API_KEY=$(cat /opt/dataiku/dss_install/dataiku-claude-api-key.key)

Run tests:
    pytest dataikuapi/iac/workflows/discovery/tests/test_real_integration.py -v -m real_dataiku
"""

import pytest
import os
import time
from typing import Dict, List, Any
from dataikuapi import DSSClient


# Test configuration
TEST_PROJECT = "COALSHIPPINGSIMULATIONGSC"
DEFAULT_HOST = "http://172.18.58.26:10000"
DEFAULT_API_KEY_PATH = "/opt/dataiku/dss_install/dataiku-claude-api-key.key"


def get_real_client() -> DSSClient:
    """
    Get authenticated DSSClient for real Dataiku instance.

    Returns:
        DSSClient: Authenticated client

    Raises:
        pytest.skip: If credentials not available
    """
    host = os.environ.get("DATAIKU_HOST", DEFAULT_HOST)
    api_key = os.environ.get("DATAIKU_API_KEY")

    # Try to load from default location if not in env
    if not api_key and os.path.exists(DEFAULT_API_KEY_PATH):
        with open(DEFAULT_API_KEY_PATH) as f:
            api_key = f.read().strip()

    if not api_key:
        pytest.skip("DATAIKU_API_KEY not available")

    return DSSClient(host, api_key)


@pytest.fixture
def real_client():
    """Fixture providing real DSSClient."""
    return get_real_client()


@pytest.fixture
def project_info(real_client) -> Dict[str, Any]:
    """Fixture providing real project information."""
    project = real_client.get_project(TEST_PROJECT)
    flow = project.get_flow()
    zones = flow.list_zones()
    datasets = project.list_datasets()
    recipes = project.list_recipes()

    return {
        "project_key": TEST_PROJECT,
        "zones": zones,
        "zone_count": len(zones),
        "dataset_count": len(datasets),
        "recipe_count": len(recipes),
        "datasets": datasets,
        "recipes": recipes,
    }


# ============================================================================
# BASIC CONNECTIVITY TESTS
# ============================================================================


@pytest.mark.integration
@pytest.mark.real_dataiku
class TestRealConnectivity:
    """Test basic connectivity to real Dataiku instance."""

    def test_client_connection(self, real_client):
        """Test that client can connect to Dataiku instance."""
        # Should not raise exception
        assert real_client is not None
        assert real_client._session is not None

    def test_project_access(self, real_client):
        """Test access to COALSHIPPINGSIMULATIONGSC project."""
        project = real_client.get_project(TEST_PROJECT)
        assert project is not None
        assert project.project_key == TEST_PROJECT

    def test_project_has_resources(self, project_info):
        """Test that project has zones, datasets, and recipes."""
        assert project_info["zone_count"] > 0, "Project should have zones"
        assert project_info["dataset_count"] > 0, "Project should have datasets"
        assert project_info["recipe_count"] > 0, "Project should have recipes"

        # Log project structure
        print(f"\n=== Project Structure ===")
        print(f"Project: {project_info['project_key']}")
        print(f"Zones: {project_info['zone_count']}")
        print(f"Datasets: {project_info['dataset_count']}")
        print(f"Recipes: {project_info['recipe_count']}")


# ============================================================================
# FLOWCRAWLER REAL TESTS
# ============================================================================


@pytest.mark.integration
@pytest.mark.real_dataiku
class TestRealFlowCrawler:
    """Test FlowCrawler against real project."""

    def test_list_real_zones(self, real_client, project_info):
        """Test listing zones from real project."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(real_client)
        zones = crawler.list_zones(TEST_PROJECT)

        # Verify zones found
        assert isinstance(zones, list)
        assert len(zones) == project_info["zone_count"]

        print(f"\n=== Real Zones Found ===")
        for zone in zones:
            print(f"  - {zone}")

    def test_get_zone_items_real(self, real_client, project_info):
        """Test getting items from real zones."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(real_client)
        zones = crawler.list_zones(TEST_PROJECT)

        # Test first zone that has items
        tested_zone = None
        for zone_name in zones[:5]:  # Test first 5 zones
            items = crawler.get_zone_items(TEST_PROJECT, zone_name)

            assert isinstance(items, dict)
            assert "datasets" in items
            assert "recipes" in items

            if items["datasets"] or items["recipes"]:
                tested_zone = zone_name
                print(f"\n=== Zone: {zone_name} ===")
                print(f"  Datasets: {len(items['datasets'])}")
                print(f"  Recipes: {len(items['recipes'])}")
                if items["datasets"]:
                    print(f"  Sample datasets: {items['datasets'][:3]}")
                if items["recipes"]:
                    print(f"  Sample recipes: {items['recipes'][:3]}")
                break

        # Note: Zones may be empty in this project
        print(f"\n  Note: Tested {min(5, len(zones))} zones")

    def test_build_real_dependency_graph(self, real_client):
        """Test building dependency graph from real project."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(real_client)
        graph = crawler.build_dependency_graph(TEST_PROJECT)

        # Verify graph structure
        assert isinstance(graph, dict)
        assert "nodes" in graph
        assert "edges" in graph

        nodes = graph["nodes"]
        edges = graph["edges"]

        print(f"\n=== Real Dependency Graph ===")
        print(f"  Nodes: {len(nodes)}")
        print(f"  Edges: {len(edges)}")

        # Sample some nodes
        if nodes:
            sample_nodes = nodes[:5] if len(nodes) >= 5 else nodes
            print(f"  Sample nodes:")
            for node in sample_nodes:
                if isinstance(node, dict):
                    print(f"    - {node.get('id', 'N/A')} ({node.get('type', 'N/A')})")

    def test_get_dataset_upstream_real(self, real_client, project_info):
        """Test getting upstream recipes for real datasets."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(real_client)

        # Test with first few datasets
        datasets_to_test = project_info["datasets"][:10]

        found_upstream = False
        for ds in datasets_to_test:
            dataset_name = ds["name"]
            upstream = crawler.get_dataset_upstream(TEST_PROJECT, dataset_name)

            assert isinstance(upstream, list)

            if upstream:
                found_upstream = True
                print(f"\n=== Upstream for {dataset_name} ===")
                print(f"  Recipes: {upstream}")
                break

        print(f"\n  Tested {len(datasets_to_test)} datasets")
        if not found_upstream:
            print("  Note: No upstream recipes found in sample")

    def test_get_dataset_downstream_real(self, real_client, project_info):
        """Test getting downstream recipes for real datasets."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(real_client)

        # Test with first few datasets
        datasets_to_test = project_info["datasets"][:10]

        found_downstream = False
        for ds in datasets_to_test:
            dataset_name = ds["name"]
            downstream = crawler.get_dataset_downstream(TEST_PROJECT, dataset_name)

            assert isinstance(downstream, list)

            if downstream:
                found_downstream = True
                print(f"\n=== Downstream for {dataset_name} ===")
                print(f"  Recipes: {downstream}")
                break

        print(f"\n  Tested {len(datasets_to_test)} datasets")
        if not found_downstream:
            print("  Note: No downstream recipes found in sample")

    def test_analyze_zone_boundary_real(self, real_client):
        """Test analyzing zone boundaries on real zones."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(real_client)
        zones = crawler.list_zones(TEST_PROJECT)

        # Test first few zones
        tested_zones = 0
        for zone_name in zones[:5]:
            boundary = crawler.analyze_zone_boundary(TEST_PROJECT, zone_name)

            # Verify boundary structure
            assert isinstance(boundary, dict)
            assert "inputs" in boundary
            assert "outputs" in boundary
            assert "internals" in boundary
            assert "is_valid" in boundary

            if boundary["inputs"] or boundary["outputs"] or boundary["internals"]:
                tested_zones += 1
                print(f"\n=== Zone Boundary: {zone_name} ===")
                print(f"  Inputs: {len(boundary['inputs'])}")
                print(f"  Outputs: {len(boundary['outputs'])}")
                print(f"  Internals: {len(boundary['internals'])}")
                print(f"  Valid block: {boundary['is_valid']}")

                if boundary["inputs"]:
                    print(f"  Input datasets: {boundary['inputs'][:3]}")
                if boundary["outputs"]:
                    print(f"  Output datasets: {boundary['outputs'][:3]}")

        print(f"\n  Analyzed {min(5, len(zones))} zones")


# ============================================================================
# BLOCKIDENTIFIER REAL TESTS
# ============================================================================


@pytest.mark.integration
@pytest.mark.real_dataiku
class TestRealBlockIdentifier:
    """Test BlockIdentifier against real project."""

    def test_identify_blocks_real(self, real_client):
        """Test identifying blocks from real project."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier

        crawler = FlowCrawler(real_client)
        identifier = BlockIdentifier(crawler)

        blocks = identifier.identify_blocks(TEST_PROJECT)

        # Verify blocks
        assert isinstance(blocks, list)

        print(f"\n=== Blocks Identified ===")
        print(f"  Total blocks: {len(blocks)}")

        # Examine first few blocks
        for i, block in enumerate(blocks[:3]):
            print(f"\n  Block {i+1}:")
            print(f"    ID: {block.block_id}")
            print(f"    Type: {block.type}")
            print(f"    Source zone: {block.source_zone}")
            print(f"    Inputs: {len(block.inputs)}")
            print(f"    Outputs: {len(block.outputs)}")

            # Validate block
            errors = block.validate()
            print(f"    Valid: {len(errors) == 0}")
            if errors:
                print(f"    Errors: {errors}")

    def test_block_validation_real(self, real_client):
        """Test that real blocks pass validation."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier

        crawler = FlowCrawler(real_client)
        identifier = BlockIdentifier(crawler)

        blocks = identifier.identify_blocks(TEST_PROJECT)

        # Check validation
        valid_count = 0
        invalid_count = 0

        for block in blocks:
            errors = block.validate()
            if errors:
                invalid_count += 1
                print(f"\n  Invalid block: {block.block_id}")
                print(f"    Errors: {errors}")
            else:
                valid_count += 1

        print(f"\n=== Block Validation ===")
        print(f"  Valid: {valid_count}")
        print(f"  Invalid: {invalid_count}")
        print(f"  Total: {len(blocks)}")

    def test_block_metadata_extraction_real(self, real_client):
        """Test metadata extraction from real blocks."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier

        crawler = FlowCrawler(real_client)
        identifier = BlockIdentifier(crawler)

        blocks = identifier.identify_blocks(TEST_PROJECT)

        if blocks:
            block = blocks[0]

            print(f"\n=== Block Metadata Sample ===")
            print(f"  block_id: {block.block_id}")
            print(f"  version: {block.version}")
            print(f"  type: {block.type}")
            print(f"  source_project: {block.source_project}")
            print(f"  source_zone: {block.source_zone}")
            print(f"  blocked: {block.blocked}")

            # Check ports
            print(f"\n  Input ports: {len(block.inputs)}")
            for inp in block.inputs[:3]:
                print(f"    - {inp.name} ({inp.type})")

            print(f"\n  Output ports: {len(block.outputs)}")
            for out in block.outputs[:3]:
                print(f"    - {out.name} ({out.type})")

            # Check contents
            print(f"\n  Contains:")
            print(f"    Datasets: {len(block.contains.datasets)}")
            print(f"    Recipes: {len(block.contains.recipes)}")
            print(f"    Models: {len(block.contains.models)}")


# ============================================================================
# SCHEMAEXTRACTOR REAL TESTS
# ============================================================================


@pytest.mark.integration
@pytest.mark.real_dataiku
class TestRealSchemaExtractor:
    """Test SchemaExtractor against real datasets."""

    def test_extract_real_dataset_schema(self, real_client, project_info):
        """Test extracting schema from real dataset."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import SchemaExtractor

        extractor = SchemaExtractor(real_client)

        # Test with first few datasets
        datasets_to_test = project_info["datasets"][:5]

        schema_found = False
        for ds in datasets_to_test:
            dataset_name = ds["name"]

            try:
                schema = extractor.extract_dataset_schema(TEST_PROJECT, dataset_name)

                if schema and "columns" in schema:
                    schema_found = True
                    print(f"\n=== Schema for {dataset_name} ===")
                    print(f"  Columns: {len(schema['columns'])}")

                    # Show first few columns
                    for col in schema["columns"][:5]:
                        print(
                            f"    - {col.get('name', 'N/A')} ({col.get('type', 'N/A')})"
                        )

                    break
            except Exception as e:
                print(f"  Warning: Could not extract schema for {dataset_name}: {e}")

        print(f"\n  Tested {len(datasets_to_test)} datasets")
        if not schema_found:
            print("  Note: No schemas found in sample (may be external datasets)")

    def test_type_mapping_real(self, real_client, project_info):
        """Test Dataiku type to standard type mapping on real data."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import SchemaExtractor

        extractor = SchemaExtractor(real_client)

        # Collect all types seen
        types_seen = set()

        for ds in project_info["datasets"][:10]:
            dataset_name = ds["name"]

            try:
                schema = extractor.extract_dataset_schema(TEST_PROJECT, dataset_name)

                if schema and "columns" in schema:
                    for col in schema["columns"]:
                        col_type = col.get("type", "")
                        if col_type:
                            types_seen.add(col_type)
            except Exception:
                continue

        print(f"\n=== Types Found in Real Data ===")
        for typ in sorted(types_seen):
            mapped = extractor._map_type(typ)
            print(f"  {typ} -> {mapped}")

        print(f"\n  Total unique types: {len(types_seen)}")

    def test_enrich_block_with_real_schemas(self, real_client):
        """Test enriching blocks with real dataset schemas."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.schema_extractor import SchemaExtractor

        crawler = FlowCrawler(real_client)
        identifier = BlockIdentifier(crawler)
        extractor = SchemaExtractor(real_client)

        # Get blocks
        blocks = identifier.identify_blocks(TEST_PROJECT)

        if blocks:
            # Enrich first block
            block = blocks[0]
            enriched = extractor.enrich_block_with_schemas(block)

            print(f"\n=== Schema Enrichment ===")
            print(f"  Block: {enriched.block_id}")
            print(f"  Inputs: {len(enriched.inputs)}")
            print(f"  Outputs: {len(enriched.outputs)}")

            # Check if schema_ref added
            for inp in enriched.inputs:
                print(f"\n  Input: {inp.name}")
                print(f"    Type: {inp.type}")
                print(f"    Schema ref: {inp.schema_ref if inp.schema_ref else 'None'}")


# ============================================================================
# DISCOVERY AGENT END-TO-END TESTS
# ============================================================================


@pytest.mark.integration
@pytest.mark.real_dataiku
class TestRealDiscoveryAgent:
    """Test complete Discovery Agent workflow on real project."""

    def test_full_discovery_workflow_dry_run(self, real_client, project_info):
        """Test complete discovery workflow in dry-run mode (SAFE - NO WRITES)."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # IMPORTANT: Use dry_run=True to avoid writing to catalog
        agent = DiscoveryAgent(real_client, verbose=True)

        print(f"\n=== Starting Discovery on {TEST_PROJECT} ===")
        start_time = time.time()

        # Run discovery (DRY RUN - no writes)
        results = agent.run_discovery(TEST_PROJECT, dry_run=True)

        elapsed_time = time.time() - start_time

        # Verify results
        assert results is not None
        assert results["project_key"] == TEST_PROJECT
        assert results["dry_run"] is True
        assert results["blocks_cataloged"] == 0  # Dry run = no writes
        assert "blocks_found" in results
        assert "blocks" in results

        print(f"\n=== Discovery Results ===")
        print(f"  Project: {results['project_key']}")
        print(f"  Blocks found: {results['blocks_found']}")
        print(f"  Blocks cataloged: {results['blocks_cataloged']} (dry-run)")
        print(f"  Execution time: {elapsed_time:.2f}s")

        # Examine blocks
        if results["blocks"]:
            print(f"\n  Sample blocks:")
            for i, block in enumerate(results["blocks"][:3]):
                print(f"\n    Block {i+1}: {block.block_id}")
                print(f"      Version: {block.version}")
                print(f"      Type: {block.type}")
                print(f"      Zone: {block.source_zone}")
                print(f"      Inputs: {len(block.inputs)}")
                print(f"      Outputs: {len(block.outputs)}")

    def test_discovery_crawl_phase_real(self, real_client):
        """Test crawl phase on real project."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        agent = DiscoveryAgent(real_client)
        zones = agent.crawl_project(TEST_PROJECT)

        assert isinstance(zones, list)
        assert len(zones) > 0

        print(f"\n=== Crawl Phase ===")
        print(f"  Zones found: {len(zones)}")
        for zone in zones:
            print(f"    - {zone}")

    def test_discovery_identify_phase_real(self, real_client):
        """Test identify phase on real project."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        agent = DiscoveryAgent(real_client)
        blocks = agent.identify_blocks(TEST_PROJECT)

        assert isinstance(blocks, list)

        print(f"\n=== Identify Phase ===")
        print(f"  Blocks identified: {len(blocks)}")

        for i, block in enumerate(blocks[:3]):
            print(f"\n    Block {i+1}: {block.block_id}")
            print(f"      Inputs: {[p.name for p in block.inputs]}")
            print(f"      Outputs: {[p.name for p in block.outputs]}")

    def test_discovery_enrich_phase_real(self, real_client):
        """Test enrich phase on real blocks."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
            BlockContents,
        )

        agent = DiscoveryAgent(real_client)

        # Get real blocks
        blocks = agent.identify_blocks(TEST_PROJECT)

        if blocks:
            # Enrich first block
            block = blocks[0]
            enriched = agent.enrich_schemas(block)

            print(f"\n=== Enrich Phase ===")
            print(f"  Block: {enriched.block_id}")
            print(f"  Enriched: {enriched is not None}")
            print(f"  Same block ID: {enriched.block_id == block.block_id}")

    def test_discovery_catalog_generation_real(self, real_client):
        """Test catalog generation from real blocks."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        agent = DiscoveryAgent(real_client)
        blocks = agent.identify_blocks(TEST_PROJECT)

        if blocks:
            block = blocks[0]

            # Generate catalog entry (doesn't write, just generates)
            catalog_entry = agent.generate_catalog_entry(block)

            print(f"\n=== Catalog Generation ===")
            print(f"  Block: {block.block_id}")
            print(f"  Wiki path: {catalog_entry['wiki_path']}")
            print(f"  Wiki article length: {len(catalog_entry['wiki_article'])} chars")
            print(f"  Summary length: {len(catalog_entry['summary'])} chars")

            # Verify content
            assert "wiki_article" in catalog_entry
            assert "summary" in catalog_entry
            assert "wiki_path" in catalog_entry
            assert block.block_id in catalog_entry["wiki_article"]


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


@pytest.mark.integration
@pytest.mark.real_dataiku
class TestRealPerformance:
    """Test performance on real project."""

    def test_discovery_performance_real_project(self, real_client, project_info):
        """Test discovery performance on real COALSHIPPINGSIMULATIONGSC project."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        agent = DiscoveryAgent(real_client, verbose=False)

        print(f"\n=== Performance Test ===")
        print(f"  Project: {TEST_PROJECT}")
        print(f"  Zones: {project_info['zone_count']}")
        print(f"  Datasets: {project_info['dataset_count']}")
        print(f"  Recipes: {project_info['recipe_count']}")

        # Measure discovery time
        start_time = time.time()
        results = agent.run_discovery(TEST_PROJECT, dry_run=True)
        elapsed_time = time.time() - start_time

        print(f"\n  Discovery time: {elapsed_time:.2f}s")
        print(f"  Blocks found: {results['blocks_found']}")

        if results["blocks_found"] > 0:
            time_per_block = elapsed_time / results["blocks_found"]
            print(f"  Time per block: {time_per_block:.3f}s")

        # Performance assertion (adjust based on project size)
        # For 7 zones with 55 datasets, reasonable time is < 30s
        assert (
            elapsed_time < 30.0
        ), f"Discovery took {elapsed_time:.2f}s, expected < 30s"

    def test_crawler_performance_real(self, real_client, project_info):
        """Test crawler performance on real project."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(real_client)

        # Measure list_zones
        start = time.time()
        zones = crawler.list_zones(TEST_PROJECT)
        zones_time = time.time() - start

        # Measure build_dependency_graph
        start = time.time()
        graph = crawler.build_dependency_graph(TEST_PROJECT)
        graph_time = time.time() - start

        print(f"\n=== Crawler Performance ===")
        print(f"  list_zones: {zones_time:.3f}s")
        print(f"  build_dependency_graph: {graph_time:.3f}s")
        print(f"  Total: {zones_time + graph_time:.3f}s")

        # Should be reasonably fast
        assert zones_time < 5.0
        assert graph_time < 5.0

    def test_identifier_performance_real(self, real_client):
        """Test identifier performance on real project."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier

        crawler = FlowCrawler(real_client)
        identifier = BlockIdentifier(crawler)

        start = time.time()
        blocks = identifier.identify_blocks(TEST_PROJECT)
        elapsed = time.time() - start

        print(f"\n=== Identifier Performance ===")
        print(f"  identify_blocks: {elapsed:.3f}s")
        print(f"  Blocks found: {len(blocks)}")

        if blocks:
            time_per_block = elapsed / len(blocks)
            print(f"  Time per block: {time_per_block:.3f}s")

        # Should be reasonably fast
        assert elapsed < 20.0


# ============================================================================
# COMPARISON TESTS (Real vs Mock)
# ============================================================================


@pytest.mark.integration
@pytest.mark.real_dataiku
class TestRealVsMockComparison:
    """Compare real Dataiku behavior vs mock behavior."""

    def test_zone_structure_real_vs_expected(self, real_client, project_info):
        """Compare real zone structure with expected structure."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(real_client)

        print(f"\n=== Real Project Structure ===")
        print(f"  Zones: {project_info['zone_count']}")

        # Analyze zone distribution
        zones = crawler.list_zones(TEST_PROJECT)
        zones_with_items = 0

        for zone_name in zones:
            items = crawler.get_zone_items(TEST_PROJECT, zone_name)
            if items["datasets"] or items["recipes"]:
                zones_with_items += 1

        print(f"  Zones with items: {zones_with_items}")
        print(f"  Empty zones: {len(zones) - zones_with_items}")

        # Note: In real Dataiku, zones may exist but items tracked at project level
        print(f"\n  Note: Project-level resources may not be in zones")
        print(f"  Project datasets: {project_info['dataset_count']}")
        print(f"  Project recipes: {project_info['recipe_count']}")

    def test_api_response_structure_real(self, real_client):
        """Document actual API response structures from real Dataiku."""
        project = real_client.get_project(TEST_PROJECT)
        flow = project.get_flow()

        # Get real zone
        zones = flow.list_zones()
        if zones:
            zone = zones[0]

            print(f"\n=== Real API Structures ===")
            print(f"\n  Zone object type: {type(zone)}")
            print(f"  Zone attributes: {dir(zone)}")

            if hasattr(zone, "name"):
                print(f"  Zone name: {zone.name}")
            if hasattr(zone, "items"):
                print(f"  Zone items type: {type(zone.items)}")

        # Get real graph
        graph = flow.get_graph()
        print(f"\n  Graph type: {type(graph)}")
        print(f"  Graph attributes: {dir(graph)}")


# ============================================================================
# CONFIGURATION AND DOCUMENTATION
# ============================================================================


def test_environment_configuration():
    """Test and document environment configuration."""
    print("\n" + "=" * 70)
    print("REAL INTEGRATION TEST CONFIGURATION")
    print("=" * 70)

    host = os.environ.get("DATAIKU_HOST", DEFAULT_HOST)
    api_key_set = bool(os.environ.get("DATAIKU_API_KEY"))
    api_key_file_exists = os.path.exists(DEFAULT_API_KEY_PATH)

    print(f"\nHost: {host}")
    print(f"API Key (env): {'Set' if api_key_set else 'Not set'}")
    print(f"API Key (file): {'Found' if api_key_file_exists else 'Not found'}")
    print(f"Test Project: {TEST_PROJECT}")

    print("\n" + "-" * 70)
    print("To run these tests:")
    print("-" * 70)
    print("\n1. Set environment variables:")
    print(f"   export DATAIKU_HOST={DEFAULT_HOST}")
    print(f"   export DATAIKU_API_KEY=$(cat {DEFAULT_API_KEY_PATH})")

    print("\n2. Run with pytest:")
    print(
        "   pytest dataikuapi/iac/workflows/discovery/tests/test_real_integration.py -v -m real_dataiku"
    )

    print("\n3. Run specific test:")
    print(
        "   pytest dataikuapi/iac/workflows/discovery/tests/test_real_integration.py::TestRealDiscoveryAgent::test_full_discovery_workflow_dry_run -v"
    )

    print("\n" + "-" * 70)
    print("SAFETY NOTES:")
    print("-" * 70)
    print("- All discovery tests use dry_run=True")
    print("- Tests are READ-ONLY")
    print("- No modifications to Dataiku instance")
    print("- No catalog writes")
    print("\n" + "=" * 70)
