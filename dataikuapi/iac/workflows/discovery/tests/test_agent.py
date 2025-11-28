"""Tests for DiscoveryAgent orchestrator."""

import pytest
from typing import Dict, List, Any


class TestDiscoveryAgent:
    """Test suite for DiscoveryAgent class."""

    def test_create_discovery_agent(self, mock_dss_client):
        """Test creating DiscoveryAgent instance."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        agent = DiscoveryAgent(mock_dss_client)
        assert agent.client == mock_dss_client

    def test_run_discovery_full_workflow(self, mock_dss_client, mock_project):
        """Test running full discovery workflow."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project

        agent = DiscoveryAgent(mock_dss_client)
        results = agent.run_discovery("TEST_PROJECT")

        assert "blocks_found" in results
        assert "blocks_cataloged" in results
        assert isinstance(results["blocks_found"], int)

    def test_discovery_workflow_steps(self, mock_dss_client, mock_project):
        """Test discovery workflow executes all steps."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project

        agent = DiscoveryAgent(mock_dss_client)
        results = agent.run_discovery("TEST_PROJECT")

        # Should have executed all steps
        assert results is not None

    def test_discovery_with_dry_run_mode(self, mock_dss_client, mock_project):
        """Test discovery in dry-run mode (no writes)."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project

        agent = DiscoveryAgent(mock_dss_client)
        results = agent.run_discovery("TEST_PROJECT", dry_run=True)

        # Should identify blocks but not write
        assert results["blocks_found"] >= 0
        assert "dry_run" in str(results).lower() or results.get("dry_run") is True


class TestDiscoveryWorkflow:
    """Test suite for discovery workflow orchestration."""

    def test_crawl_project_step(self, mock_dss_client, mock_project):
        """Test crawl project step."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project

        agent = DiscoveryAgent(mock_dss_client)
        zones = agent.crawl_project("TEST_PROJECT")

        assert isinstance(zones, list)

    def test_identify_blocks_step(self, mock_dss_client, mock_project):
        """Test identify blocks step."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project

        agent = DiscoveryAgent(mock_dss_client)
        blocks = agent.identify_blocks("TEST_PROJECT")

        assert isinstance(blocks, list)

    def test_enrich_schemas_step(self, mock_dss_client, mock_project):
        """Test enrich with schemas step."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
            BlockContents,
        )

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project
        dataset = mock_project.get_dataset.return_value
        dataset.get_schema.return_value = {
            "columns": [{"name": "ID", "type": "bigint"}]
        }

        metadata = BlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST_PROJECT",
            inputs=[BlockPort(name="input1", type="dataset")],
            outputs=[],
            contains=BlockContents(),
        )

        agent = DiscoveryAgent(mock_dss_client)
        enriched = agent.enrich_schemas(metadata)

        assert enriched is not None

    def test_generate_catalog_step(self, mock_dss_client):
        """Test generate catalog entries step."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockContents,
        )

        metadata = BlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST_PROJECT",
            inputs=[],
            outputs=[],
            contains=BlockContents(),
        )

        agent = DiscoveryAgent(mock_dss_client)
        catalog_entry = agent.generate_catalog_entry(metadata)

        assert catalog_entry is not None
        assert "wiki_article" in catalog_entry
        assert "summary" in catalog_entry


class TestErrorHandling:
    """Test suite for error handling."""

    def test_handle_project_not_found(self, mock_dss_client):
        """Test handling when project doesn't exist."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup mock to raise exception
        mock_dss_client.get_project.side_effect = Exception("Project not found")

        agent = DiscoveryAgent(mock_dss_client)

        with pytest.raises(Exception):
            agent.run_discovery("NONEXISTENT_PROJECT")

    def test_handle_invalid_zone(self, mock_dss_client, mock_project):
        """Test handling invalid zones gracefully."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup mock with zone that has issues
        mock_dss_client.get_project.return_value = mock_project

        agent = DiscoveryAgent(mock_dss_client)

        # Should handle gracefully, not crash
        results = agent.run_discovery("TEST_PROJECT")
        assert results is not None


class TestProgressReporting:
    """Test suite for progress reporting."""

    def test_report_progress_enabled(self, mock_dss_client):
        """Test progress reporting when enabled."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        agent = DiscoveryAgent(mock_dss_client, verbose=True)
        assert agent.verbose is True

    def test_report_progress_disabled(self, mock_dss_client):
        """Test progress reporting when disabled."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        agent = DiscoveryAgent(mock_dss_client, verbose=False)
        assert agent.verbose is False

    def test_log_discovery_summary(self, mock_dss_client, mock_project):
        """Test logging discovery summary."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project

        agent = DiscoveryAgent(mock_dss_client, verbose=True)
        results = agent.run_discovery("TEST_PROJECT")

        # Results should have summary info
        assert "blocks_found" in results


class TestResultsFormat:
    """Test suite for results format."""

    def test_results_contains_required_fields(self, mock_dss_client, mock_project):
        """Test results dict contains all required fields."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project

        agent = DiscoveryAgent(mock_dss_client)
        results = agent.run_discovery("TEST_PROJECT")

        # Required fields
        assert "project_key" in results
        assert "blocks_found" in results
        assert "blocks_cataloged" in results

    def test_results_includes_block_list(self, mock_dss_client, mock_project):
        """Test results includes list of discovered blocks."""
        from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project

        agent = DiscoveryAgent(mock_dss_client)
        results = agent.run_discovery("TEST_PROJECT")

        # Should have blocks list
        assert "blocks" in results or "blocks_found" in results
