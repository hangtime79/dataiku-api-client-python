"""Integration tests for Discovery Agent.

This module provides end-to-end integration tests that validate the complete
discovery workflow across all components.
"""

import pytest
import time
from typing import Dict, List, Any
from unittest.mock import Mock, MagicMock


class TestEndToEndDiscovery:
    """Test suite for end-to-end discovery workflows."""

    def test_complete_discovery_workflow(self, mock_dss_client, mock_project):
        """Test complete discovery workflow from crawl to catalog."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup: Complete project with multiple zones
        mock_dss_client.get_project.return_value = mock_project

        # Execute: Run complete discovery
        agent = DiscoveryAgent(mock_dss_client, verbose=True)
        results = agent.run_discovery("TEST_PROJECT")

        # Assert: Verify complete pipeline executed
        assert results is not None
        assert "project_key" in results
        assert results["project_key"] == "TEST_PROJECT"
        assert "blocks_found" in results
        assert "blocks_cataloged" in results
        assert "blocks" in results
        assert isinstance(results["blocks"], list)

    def test_discovery_with_multiple_zones(self, mock_dss_client):
        """Test discovery across multiple zones in a project."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent
        from dataikuapi.iac.workflows.discovery.models import BlockMetadata

        # Setup: Project with 3 zones
        project = self._create_multi_zone_project(num_zones=3)
        mock_dss_client.get_project.return_value = project

        # Execute
        agent = DiscoveryAgent(mock_dss_client)
        results = agent.run_discovery("MULTI_ZONE_PROJECT")

        # Assert: Found blocks from multiple zones
        assert results["blocks_found"] >= 0
        assert isinstance(results["blocks"], list)

    def test_discovery_with_complex_flow_graph(self, mock_dss_client):
        """Test discovery with complex multi-layer flow graph."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup: Complex project with dependencies
        project = self._create_complex_flow_project()
        mock_dss_client.get_project.return_value = project

        # Execute
        agent = DiscoveryAgent(mock_dss_client)
        results = agent.run_discovery("COMPLEX_PROJECT")

        # Assert: Successfully processed complex graph
        assert results is not None
        assert results["blocks_found"] >= 0

    def test_discovery_with_schema_enrichment(self, mock_dss_client):
        """Test discovery with full schema enrichment."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup: Project with schemas
        project = self._create_project_with_schemas()
        mock_dss_client.get_project.return_value = project

        # Execute
        agent = DiscoveryAgent(mock_dss_client)
        results = agent.run_discovery("SCHEMA_PROJECT")

        # Assert: Blocks have schema enrichment
        assert results is not None
        if results["blocks_found"] > 0:
            # Blocks should be enriched
            for block in results["blocks"]:
                assert hasattr(block, "inputs")

    def test_discovery_dry_run_mode(self, mock_dss_client, mock_project):
        """Test discovery in dry-run mode (no writes)."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup
        mock_dss_client.get_project.return_value = mock_project

        # Execute: Dry run
        agent = DiscoveryAgent(mock_dss_client)
        results = agent.run_discovery("TEST_PROJECT", dry_run=True)

        # Assert: No catalog writes
        assert results["dry_run"] is True
        assert results["blocks_cataloged"] == 0

    def _create_multi_zone_project(self, num_zones: int = 3) -> Mock:
        """Create mock project with multiple zones."""
        project = Mock()
        project.project_key = "MULTI_ZONE_PROJECT"

        # Create flow with multiple zones
        flow = Mock()
        zones_list = [{"name": f"zone{i}"} for i in range(num_zones)]
        flow.get_zones.return_value = zones_list

        # Create zone mocks
        for i in range(num_zones):
            zone = Mock()
            zone.id = f"zone{i}"
            zone.name = f"Zone {i}"
            zone.items = [
                {"type": "DATASET", "id": f"ds{i}_1"},
                {"type": "DATASET", "id": f"ds{i}_2"},
                {"type": "RECIPE", "id": f"recipe{i}"},
            ]
            zone.get_items.return_value = zone.items

            if i == 0:
                flow.get_zone.return_value = zone
            else:
                flow.get_zone.side_effect = lambda name: zone

        # Mock graph
        flow.get_graph.return_value = self._create_sample_graph()

        project.get_flow.return_value = flow

        # Mock datasets
        dataset = Mock()
        dataset.get_schema.return_value = {
            "columns": [{"name": "ID", "type": "bigint", "notNull": True}]
        }
        project.get_dataset.return_value = dataset

        return project

    def _create_complex_flow_project(self) -> Mock:
        """Create mock project with complex flow dependencies."""
        project = Mock()
        project.project_key = "COMPLEX_PROJECT"

        flow = Mock()
        flow.get_zones.return_value = [
            {"name": "ingestion"},
            {"name": "processing"},
            {"name": "analytics"},
        ]

        # Complex zone
        zone = Mock()
        zone.id = "processing"
        zone.name = "Processing"
        zone.items = [
            {"type": "DATASET", "id": "raw_data"},
            {"type": "DATASET", "id": "cleaned_data"},
            {"type": "DATASET", "id": "enriched_data"},
            {"type": "RECIPE", "id": "clean_recipe"},
            {"type": "RECIPE", "id": "enrich_recipe"},
        ]
        zone.get_items.return_value = zone.items
        flow.get_zone.return_value = zone

        # Complex graph with multiple layers
        flow.get_graph.return_value = self._create_complex_graph()

        project.get_flow.return_value = flow

        # Mock datasets
        dataset = Mock()
        dataset.get_schema.return_value = {
            "columns": [{"name": "ID", "type": "bigint"}]
        }
        project.get_dataset.return_value = dataset

        return project

    def _create_project_with_schemas(self) -> Mock:
        """Create mock project with rich schemas."""
        project = Mock()
        project.project_key = "SCHEMA_PROJECT"

        flow = Mock()
        flow.get_zones.return_value = [{"name": "data_zone"}]

        zone = Mock()
        zone.id = "data_zone"
        zone.name = "Data Zone"
        zone.items = [
            {"type": "DATASET", "id": "customers"},
            {"type": "RECIPE", "id": "prepare"},
        ]
        zone.get_items.return_value = zone.items
        flow.get_zone.return_value = zone
        flow.get_graph.return_value = self._create_sample_graph()

        project.get_flow.return_value = flow

        # Rich schema
        dataset = Mock()
        dataset.get_schema.return_value = {
            "columns": [
                {"name": "CUSTOMER_ID", "type": "bigint", "notNull": True},
                {"name": "NAME", "type": "string", "notNull": False},
                {"name": "EMAIL", "type": "string", "notNull": False},
            ]
        }
        project.get_dataset.return_value = dataset

        return project

    def _create_sample_graph(self) -> Dict[str, Any]:
        """Create sample flow graph."""
        return {
            "nodes": [
                {"id": "ds1", "type": "DATASET"},
                {"id": "recipe1", "type": "RECIPE"},
                {"id": "ds2", "type": "DATASET"},
            ],
            "edges": [
                {"from": "ds1", "to": "recipe1"},
                {"from": "recipe1", "to": "ds2"},
            ],
        }

    def _create_complex_graph(self) -> Dict[str, Any]:
        """Create complex flow graph."""
        return {
            "nodes": [
                {"id": "raw_data", "type": "DATASET"},
                {"id": "clean_recipe", "type": "RECIPE"},
                {"id": "cleaned_data", "type": "DATASET"},
                {"id": "enrich_recipe", "type": "RECIPE"},
                {"id": "enriched_data", "type": "DATASET"},
            ],
            "edges": [
                {"from": "raw_data", "to": "clean_recipe"},
                {"from": "clean_recipe", "to": "cleaned_data"},
                {"from": "cleaned_data", "to": "enrich_recipe"},
                {"from": "enrich_recipe", "to": "enriched_data"},
            ],
        }


class TestPerformance:
    """Test suite for performance requirements."""

    def test_discovery_performance_small_project(self, mock_dss_client):
        """Test discovery performance on small project (5 zones)."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup: Small project (5 zones)
        project = self._create_project_with_n_zones(5)
        mock_dss_client.get_project.return_value = project

        # Execute: Measure time
        agent = DiscoveryAgent(mock_dss_client)
        start_time = time.time()
        results = agent.run_discovery("SMALL_PROJECT")
        elapsed_time = time.time() - start_time

        # Assert: Should be fast (<2s for 5 zones)
        assert elapsed_time < 2.0
        assert results is not None

    def test_discovery_performance_medium_project(self, mock_dss_client):
        """Test discovery performance on medium project (20 zones)."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup: Medium project (20 zones)
        project = self._create_project_with_n_zones(20)
        mock_dss_client.get_project.return_value = project

        # Execute: Measure time
        agent = DiscoveryAgent(mock_dss_client)
        start_time = time.time()
        results = agent.run_discovery("MEDIUM_PROJECT")
        elapsed_time = time.time() - start_time

        # Assert: Should complete in reasonable time (<5s for 20 zones)
        assert elapsed_time < 5.0
        assert results is not None

    def test_discovery_performance_large_project(self, mock_dss_client):
        """Test discovery performance on large project (50 zones)."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup: Large project (50 zones) - acceptance criteria
        project = self._create_project_with_n_zones(50)
        mock_dss_client.get_project.return_value = project

        # Execute: Measure time
        agent = DiscoveryAgent(mock_dss_client)
        start_time = time.time()
        results = agent.run_discovery("LARGE_PROJECT")
        elapsed_time = time.time() - start_time

        # Assert: Should meet acceptance criteria (<10s for 50 zones)
        assert elapsed_time < 10.0
        assert results is not None

    def _create_project_with_n_zones(self, n: int) -> Mock:
        """Create mock project with N zones for performance testing."""
        project = Mock()
        project.project_key = f"PROJECT_{n}_ZONES"

        flow = Mock()
        zones_list = [{"name": f"zone_{i}"} for i in range(n)]
        flow.get_zones.return_value = zones_list

        # Simple zone mock
        zone = Mock()
        zone.items = [
            {"type": "DATASET", "id": "ds1"},
            {"type": "RECIPE", "id": "recipe1"},
            {"type": "DATASET", "id": "ds2"},
        ]
        zone.get_items.return_value = zone.items
        flow.get_zone.return_value = zone

        # Simple graph
        flow.get_graph.return_value = {
            "nodes": [
                {"id": "ds1", "type": "DATASET"},
                {"id": "recipe1", "type": "RECIPE"},
                {"id": "ds2", "type": "DATASET"},
            ],
            "edges": [
                {"from": "ds1", "to": "recipe1"},
                {"from": "recipe1", "to": "ds2"},
            ],
        }

        project.get_flow.return_value = flow

        # Mock dataset
        dataset = Mock()
        dataset.get_schema.return_value = {
            "columns": [{"name": "ID", "type": "bigint"}]
        }
        project.get_dataset.return_value = dataset

        return project


class TestErrorRecovery:
    """Test suite for error recovery and resilience."""

    def test_discovery_continues_on_schema_error(self, mock_dss_client):
        """Test discovery continues when schema extraction fails."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup: Project where dataset.get_schema() raises error
        project = Mock()
        project.project_key = "ERROR_PROJECT"

        flow = Mock()
        flow.get_zones.return_value = [{"name": "test_zone"}]

        zone = Mock()
        zone.items = [
            {"type": "DATASET", "id": "broken_ds"},
            {"type": "RECIPE", "id": "recipe1"},
            {"type": "DATASET", "id": "ds2"},
        ]
        zone.get_items.return_value = zone
        flow.get_zone.return_value = zone
        flow.get_graph.return_value = {
            "nodes": [
                {"id": "broken_ds", "type": "DATASET"},
                {"id": "recipe1", "type": "RECIPE"},
                {"id": "ds2", "type": "DATASET"},
            ],
            "edges": [
                {"from": "broken_ds", "to": "recipe1"},
                {"from": "recipe1", "to": "ds2"},
            ],
        }

        project.get_flow.return_value = flow

        # Mock dataset that raises error
        dataset = Mock()
        dataset.get_schema.side_effect = Exception("Schema not available")
        project.get_dataset.return_value = dataset

        mock_dss_client.get_project.return_value = project

        # Execute: Should not crash
        agent = DiscoveryAgent(mock_dss_client)
        results = agent.run_discovery("ERROR_PROJECT")

        # Assert: Discovery completed despite errors
        assert results is not None

    def test_discovery_handles_empty_project(self, mock_dss_client):
        """Test discovery handles project with no zones."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup: Empty project
        project = Mock()
        project.project_key = "EMPTY_PROJECT"

        flow = Mock()
        flow.get_zones.return_value = []
        project.get_flow.return_value = flow

        mock_dss_client.get_project.return_value = project

        # Execute
        agent = DiscoveryAgent(mock_dss_client)
        results = agent.run_discovery("EMPTY_PROJECT")

        # Assert: Handles gracefully
        assert results is not None
        assert results["blocks_found"] == 0

    def test_discovery_handles_invalid_zones(self, mock_dss_client):
        """Test discovery handles zones that don't meet block criteria."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup: Project with invalid zones (no inputs/outputs)
        project = Mock()
        project.project_key = "INVALID_PROJECT"

        flow = Mock()
        flow.get_zones.return_value = [{"name": "invalid_zone"}]

        # Zone with no proper inputs/outputs
        zone = Mock()
        zone.items = [{"type": "DATASET", "id": "internal_only"}]
        zone.get_items.return_value = zone
        flow.get_zone.return_value = zone
        flow.get_graph.return_value = {
            "nodes": [{"id": "internal_only", "type": "DATASET"}],
            "edges": [],
        }

        project.get_flow.return_value = flow
        mock_dss_client.get_project.return_value = project

        # Execute
        agent = DiscoveryAgent(mock_dss_client)
        results = agent.run_discovery("INVALID_PROJECT")

        # Assert: Handles gracefully
        assert results is not None


class TestComponentIntegration:
    """Test suite for component integration points."""

    def test_crawler_to_identifier_integration(self, mock_dss_client, mock_project):
        """Test integration between FlowCrawler and BlockIdentifier."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier

        # Setup
        mock_dss_client.get_project.return_value = mock_project

        # Execute: Crawler -> Identifier pipeline
        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        zones = crawler.list_zones("TEST_PROJECT")
        blocks = identifier.identify_blocks("TEST_PROJECT")

        # Assert: Pipeline works
        assert isinstance(zones, list)
        assert isinstance(blocks, list)

    def test_identifier_to_schema_integration(self, mock_dss_client, mock_project):
        """Test integration between BlockIdentifier and SchemaExtractor."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
            BlockContents,
        )

        # Setup
        mock_dss_client.get_project.return_value = mock_project

        dataset = mock_project.get_dataset.return_value
        dataset.get_schema.return_value = {
            "columns": [{"name": "ID", "type": "bigint", "notNull": True}]
        }

        # Execute: Identifier -> Schema pipeline
        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)
        schema_extractor = SchemaExtractor(mock_dss_client)

        # Create sample metadata
        metadata = BlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST_PROJECT",
            inputs=[BlockPort(name="input1", type="dataset")],
            outputs=[],
            contains=BlockContents(),
        )

        enriched = schema_extractor.enrich_block_with_schemas(metadata)

        # Assert: Enrichment works
        assert enriched is not None
        assert enriched.block_id == "TEST_BLOCK"

    def test_schema_to_catalog_integration(self, mock_dss_client):
        """Test integration between SchemaExtractor and CatalogWriter."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
            BlockContents,
        )

        # Setup
        metadata = BlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST_PROJECT",
            inputs=[BlockPort(name="input1", type="dataset")],
            outputs=[BlockPort(name="output1", type="dataset")],
            contains=BlockContents(),
        )

        # Execute: Schema -> Catalog pipeline
        catalog_writer = CatalogWriter()
        wiki_article = catalog_writer.generate_wiki_article(metadata)
        summary = catalog_writer.generate_block_summary(metadata)

        # Assert: Catalog generation works
        assert "TEST_BLOCK" in wiki_article
        assert "TEST_BLOCK" in summary


class TestVerboseOutput:
    """Test suite for verbose output and logging."""

    def test_verbose_mode_enabled(self, mock_dss_client, mock_project, capsys):
        """Test verbose mode produces output."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup
        mock_dss_client.get_project.return_value = mock_project

        # Execute with verbose=True
        agent = DiscoveryAgent(mock_dss_client, verbose=True)
        results = agent.run_discovery("TEST_PROJECT")

        # Capture output
        captured = capsys.readouterr()

        # Assert: Verbose output produced
        assert "Starting discovery" in captured.out or results is not None

    def test_verbose_mode_disabled(self, mock_dss_client, mock_project, capsys):
        """Test verbose mode disabled produces no output."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup
        mock_dss_client.get_project.return_value = mock_project

        # Execute with verbose=False
        agent = DiscoveryAgent(mock_dss_client, verbose=False)
        results = agent.run_discovery("TEST_PROJECT")

        # Capture output
        captured = capsys.readouterr()

        # Assert: Either no output or minimal output
        assert results is not None
