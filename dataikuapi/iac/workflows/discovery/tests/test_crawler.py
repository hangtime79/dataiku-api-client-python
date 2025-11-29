"""Tests for FlowCrawler component."""

import pytest
from typing import Dict, List, Any


class TestFlowCrawler:
    """Test suite for FlowCrawler class."""

    def test_create_flow_crawler(self, mock_dss_client):
        """Test creating FlowCrawler instance."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        assert crawler.client == mock_dss_client

    def test_get_project_flow(self, mock_dss_client, mock_project):
        """Test retrieving project flow graph."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project

        crawler = FlowCrawler(mock_dss_client)
        flow = crawler.get_project_flow("TEST_PROJECT")

        assert flow is not None
        mock_dss_client.get_project.assert_called_once_with("TEST_PROJECT")
        mock_project.get_flow.assert_called_once()

    def test_list_zones(self, mock_dss_client, mock_project):
        """Test listing all zones in a project."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project

        crawler = FlowCrawler(mock_dss_client)
        zones = crawler.list_zones("TEST_PROJECT")

        assert isinstance(zones, list)
        assert len(zones) > 0

    def test_get_zone_items(self, mock_dss_client, mock_project, mock_zone):
        """Test getting datasets and recipes in a zone."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project
        mock_project.get_flow.return_value.get_zone.return_value = mock_zone

        crawler = FlowCrawler(mock_dss_client)
        zone_items = crawler.get_zone_items("TEST_PROJECT", "test_zone")

        assert "datasets" in zone_items
        assert "recipes" in zone_items
        assert isinstance(zone_items["datasets"], list)
        assert isinstance(zone_items["recipes"], list)

    def test_build_dependency_graph(
        self, mock_dss_client, mock_project, sample_flow_graph
    ):
        """Test building dependency graph from flow."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project
        mock_project.get_flow.return_value.get_graph.return_value = sample_flow_graph

        crawler = FlowCrawler(mock_dss_client)
        dep_graph = crawler.build_dependency_graph("TEST_PROJECT")

        assert isinstance(dep_graph, dict)
        assert "nodes" in dep_graph
        assert "edges" in dep_graph

    def test_analyze_zone_boundary(
        self, mock_dss_client, mock_project, sample_flow_graph
    ):
        """Test analyzing zone boundary to identify inputs/outputs."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project
        mock_project.get_flow.return_value.get_graph.return_value = sample_flow_graph

        crawler = FlowCrawler(mock_dss_client)
        boundary = crawler.analyze_zone_boundary("TEST_PROJECT", "test_zone")

        assert "inputs" in boundary
        assert "outputs" in boundary
        assert "internals" in boundary
        assert "is_valid" in boundary
        assert isinstance(boundary["inputs"], list)
        assert isinstance(boundary["outputs"], list)
        assert isinstance(boundary["internals"], list)
        assert isinstance(boundary["is_valid"], bool)

    def test_get_dataset_upstream(self, mock_dss_client, mock_project, mock_dataset):
        """Test getting upstream recipes for a dataset."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project
        mock_project.get_dataset.return_value = mock_dataset

        crawler = FlowCrawler(mock_dss_client)
        upstream = crawler.get_dataset_upstream("TEST_PROJECT", "test_dataset")

        assert isinstance(upstream, list)

    def test_get_dataset_downstream(self, mock_dss_client, mock_project, mock_dataset):
        """Test getting downstream recipes for a dataset."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project
        mock_project.get_dataset.return_value = mock_dataset

        crawler = FlowCrawler(mock_dss_client)
        downstream = crawler.get_dataset_downstream("TEST_PROJECT", "test_dataset")

        assert isinstance(downstream, list)


class TestZoneBoundaryAnalysis:
    """Test suite for zone boundary analysis logic."""

    def test_identify_inputs_no_upstream_in_zone(self, mock_dss_client):
        """Test identifying inputs when dataset has no upstream recipes in zone."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # This dataset comes from outside the zone
        crawler = FlowCrawler(mock_dss_client)
        # Will implement with mock data

    def test_identify_outputs_downstream_outside_zone(self, mock_dss_client):
        """Test identifying outputs when dataset consumed outside zone."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # This dataset goes outside the zone
        crawler = FlowCrawler(mock_dss_client)
        # Will implement with mock data

    def test_identify_internals_fully_contained(self, mock_dss_client):
        """Test identifying internal datasets fully contained in zone."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # This dataset is produced and consumed within zone
        crawler = FlowCrawler(mock_dss_client)
        # Will implement with mock data

    def test_validate_containment_valid_zone(self, mock_dss_client):
        """Test containment validation for valid zone."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # All recipe inputs/outputs are in zone boundary
        crawler = FlowCrawler(mock_dss_client)
        # Will implement with mock data

    def test_validate_containment_invalid_zone(self, mock_dss_client):
        """Test containment validation for invalid zone."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # Some recipe references dataset outside zone boundary
        crawler = FlowCrawler(mock_dss_client)
        # Will implement with mock data


class TestEmptyZoneHandling:
    """Test suite for empty zone edge cases."""

    def test_crawl_empty_zone_no_datasets(self, mock_dss_client, mock_project):
        """Test crawling zone with no datasets."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        # Should handle gracefully without errors

    def test_crawl_empty_zone_no_recipes(self, mock_dss_client, mock_project):
        """Test crawling zone with no recipes."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        # Should handle gracefully without errors


class TestCrossZoneDependencies:
    """Test suite for cross-zone dependency handling."""

    def test_dataset_consumed_by_multiple_zones(self, mock_dss_client):
        """Test handling dataset consumed by recipes in multiple zones."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # Output of one zone is input to multiple other zones
        crawler = FlowCrawler(mock_dss_client)
        # Will implement with mock data

    def test_dataset_produced_outside_consumed_inside(self, mock_dss_client):
        """Test handling dataset produced outside zone, consumed inside."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # This should be identified as an input
        crawler = FlowCrawler(mock_dss_client)
        # Will implement with mock data


class TestErrorHandling:
    """Test suite for error handling."""

    def test_project_not_found(self, mock_dss_client):
        """Test handling when project doesn't exist."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # Setup mock to raise exception
        mock_dss_client.get_project.side_effect = Exception("Project not found")

        crawler = FlowCrawler(mock_dss_client)

        with pytest.raises(Exception, match="Project not found"):
            crawler.get_project_flow("NONEXISTENT_PROJECT")

    def test_zone_not_found(self, mock_dss_client, mock_project):
        """Test handling when zone doesn't exist."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # Setup mock to raise exception
        mock_dss_client.get_project.return_value = mock_project
        mock_project.get_flow.return_value.get_zone.side_effect = Exception(
            "Zone not found"
        )

        crawler = FlowCrawler(mock_dss_client)

        with pytest.raises(Exception, match="Zone not found"):
            crawler.get_zone_items("TEST_PROJECT", "nonexistent_zone")

    def test_flow_api_error(self, mock_dss_client, mock_project):
        """Test handling Flow API errors."""
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # Setup mock to raise exception
        mock_dss_client.get_project.return_value = mock_project
        mock_project.get_flow.side_effect = Exception("Flow API error")

        crawler = FlowCrawler(mock_dss_client)

        with pytest.raises(Exception, match="Flow API error"):
            crawler.get_project_flow("TEST_PROJECT")
