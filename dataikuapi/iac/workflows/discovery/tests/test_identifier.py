"""Tests for BlockIdentifier component."""

import pytest
from typing import Dict, List, Any


class TestBlockIdentifier:
    """Test suite for BlockIdentifier class."""

    def test_create_block_identifier(self, mock_dss_client):
        """Test creating BlockIdentifier instance."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)
        assert identifier.crawler == crawler

    def test_identify_blocks_in_project(self, mock_dss_client, mock_project):
        """Test identifying all blocks in a project."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)
        blocks = identifier.identify_blocks("TEST_PROJECT")

        assert isinstance(blocks, list)

    def test_is_valid_block_with_inputs_and_outputs(self, mock_dss_client):
        """Test zone with both inputs and outputs is valid block."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        boundary = {
            "inputs": ["input1"],
            "outputs": ["output1"],
            "internals": ["temp1"],
            "is_valid": True,
        }

        assert identifier.is_valid_block(boundary) is True

    def test_is_valid_block_without_inputs(self, mock_dss_client):
        """Test zone without inputs is not a valid block."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        boundary = {
            "inputs": [],  # No inputs
            "outputs": ["output1"],
            "internals": [],
            "is_valid": True,
        }

        assert identifier.is_valid_block(boundary) is False

    def test_is_valid_block_without_outputs(self, mock_dss_client):
        """Test zone without outputs is not a valid block."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        boundary = {
            "inputs": ["input1"],
            "outputs": [],  # No outputs
            "internals": [],
            "is_valid": True,
        }

        assert identifier.is_valid_block(boundary) is False

    def test_is_valid_block_with_containment_violation(self, mock_dss_client):
        """Test zone with containment violation is not valid."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        boundary = {
            "inputs": ["input1"],
            "outputs": ["output1"],
            "internals": [],
            "is_valid": False,  # Containment violation
        }

        assert identifier.is_valid_block(boundary) is False


class TestBlockMetadataExtraction:
    """Test suite for block metadata extraction."""

    def test_extract_block_metadata(self, mock_dss_client, mock_project):
        """Test extracting complete block metadata from zone."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        zone_name = "test_zone"
        boundary = {
            "inputs": ["input1"],
            "outputs": ["output1"],
            "internals": ["temp1"],
            "is_valid": True,
        }

        metadata = identifier.extract_block_metadata(
            "TEST_PROJECT", zone_name, boundary
        )

        assert metadata is not None
        assert metadata.block_id is not None
        assert metadata.source_project == "TEST_PROJECT"
        assert metadata.source_zone == zone_name
        assert len(metadata.inputs) > 0
        assert len(metadata.outputs) > 0

    def test_generate_block_id_from_zone_name(self, mock_dss_client):
        """Test generating block ID from zone name."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        # Zone name: "Feature Engineering" → Block ID: "FEATURE_ENGINEERING"
        block_id = identifier.generate_block_id("Feature Engineering")
        assert block_id == "FEATURE_ENGINEERING"

        # Zone name: "data-ingestion" → Block ID: "DATA_INGESTION"
        block_id = identifier.generate_block_id("data-ingestion")
        assert block_id == "DATA_INGESTION"

    def test_create_block_ports_from_datasets(self, mock_dss_client):
        """Test creating BlockPort objects from dataset names."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        dataset_names = ["input1", "input2"]
        ports = identifier.create_block_ports(dataset_names, "dataset")

        assert len(ports) == 2
        assert all(port.type == "dataset" for port in ports)
        assert ports[0].name == "input1"
        assert ports[1].name == "input2"

    def test_extract_block_contents(self, mock_dss_client, mock_project):
        """Test extracting block contents (internal datasets/recipes)."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        boundary = {
            "inputs": ["input1"],
            "outputs": ["output1"],
            "internals": ["temp1", "temp2"],
            "is_valid": True,
        }

        zone_items = {
            "datasets": ["input1", "temp1", "temp2", "output1"],
            "recipes": ["recipe1", "recipe2"],
        }

        contents = identifier.extract_block_contents(boundary, zone_items)

        assert len(contents.datasets) == 2  # temp1, temp2
        assert "temp1" in contents.datasets
        assert "temp2" in contents.datasets
        assert len(contents.recipes) == 2


class TestMultipleInputsOutputs:
    """Test suite for blocks with multiple inputs/outputs."""

    def test_identify_block_with_multiple_inputs(self, mock_dss_client):
        """Test identifying block with multiple input datasets."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        boundary = {
            "inputs": ["input1", "input2", "input3"],
            "outputs": ["output1"],
            "internals": [],
            "is_valid": True,
        }

        assert identifier.is_valid_block(boundary) is True

    def test_identify_block_with_multiple_outputs(self, mock_dss_client):
        """Test identifying block with multiple output datasets."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        boundary = {
            "inputs": ["input1"],
            "outputs": ["output1", "output2", "output3"],
            "internals": [],
            "is_valid": True,
        }

        assert identifier.is_valid_block(boundary) is True


class TestHierarchyClassification:
    """Test suite for hierarchy level classification."""

    def test_classify_hierarchy_from_zone_tags(self, mock_dss_client):
        """Test classifying hierarchy level from zone tags."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        # Zone tagged with hierarchy level
        zone_metadata = {"tags": ["level:process"]}
        hierarchy = identifier.classify_hierarchy(zone_metadata)
        assert hierarchy == "process"

    def test_classify_hierarchy_default(self, mock_dss_client):
        """Test default hierarchy classification when no tags."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        # No hierarchy tags
        zone_metadata = {"tags": ["other_tag"]}
        hierarchy = identifier.classify_hierarchy(zone_metadata)
        assert hierarchy == ""  # Default/unknown


class TestDomainExtraction:
    """Test suite for domain extraction."""

    def test_extract_domain_from_zone_tags(self, mock_dss_client):
        """Test extracting domain from zone tags."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        zone_metadata = {"tags": ["domain:analytics"]}
        domain = identifier.extract_domain(zone_metadata)
        assert domain == "analytics"

    def test_extract_domain_default(self, mock_dss_client):
        """Test default domain when no domain tags."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        zone_metadata = {"tags": ["other_tag"]}
        domain = identifier.extract_domain(zone_metadata)
        assert domain == ""


class TestTagExtraction:
    """Test suite for tag extraction."""

    def test_extract_tags_from_zone(self, mock_dss_client):
        """Test extracting tags from zone metadata."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        zone_metadata = {
            "tags": ["ml", "feature-engineering", "domain:analytics", "level:process"]
        }

        # Should filter out special tags (domain:, level:)
        tags = identifier.extract_tags(zone_metadata)
        assert "ml" in tags
        assert "feature-engineering" in tags
        assert "domain:analytics" not in tags  # Filtered
        assert "level:process" not in tags  # Filtered


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_skip_default_zone_without_name(self, mock_dss_client):
        """Test skipping default zone with no explicit name."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        # Default zone (empty or "default" name)
        assert identifier.should_skip_zone("") is True
        assert identifier.should_skip_zone("default") is True
        assert identifier.should_skip_zone("Default") is True

    def test_process_named_zone(self, mock_dss_client):
        """Test processing zone with explicit name."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        # Named zone should be processed
        assert identifier.should_skip_zone("processing") is False
        assert identifier.should_skip_zone("Feature Engineering") is False

    def test_handle_zone_with_no_internals(self, mock_dss_client):
        """Test handling zone with no internal datasets."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        # Zone with direct input→output mapping (no internals)
        boundary = {
            "inputs": ["input1"],
            "outputs": ["output1"],
            "internals": [],  # No internals
            "is_valid": True,
        }

        assert identifier.is_valid_block(boundary) is True


class TestVersionGeneration:
    """Test suite for version generation."""

    def test_generate_initial_version(self, mock_dss_client):
        """Test generating initial version for new block."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        # New block gets version 1.0.0
        version = identifier.generate_version("NEW_BLOCK")
        assert version == "1.0.0"


class TestValidationMessages:
    """Test suite for validation error messages."""

    def test_validation_message_no_inputs(self, mock_dss_client):
        """Test validation message for zone without inputs."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        boundary = {
            "inputs": [],
            "outputs": ["output1"],
            "internals": [],
            "is_valid": True,
        }

        message = identifier.get_validation_message(boundary)
        assert "input" in message.lower()

    def test_validation_message_no_outputs(self, mock_dss_client):
        """Test validation message for zone without outputs."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        boundary = {
            "inputs": ["input1"],
            "outputs": [],
            "internals": [],
            "is_valid": True,
        }

        message = identifier.get_validation_message(boundary)
        assert "output" in message.lower()

    def test_validation_message_containment_violation(self, mock_dss_client):
        """Test validation message for containment violation."""
        from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
        from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler

        crawler = FlowCrawler(mock_dss_client)
        identifier = BlockIdentifier(crawler)

        boundary = {
            "inputs": ["input1"],
            "outputs": ["output1"],
            "internals": [],
            "is_valid": False,
        }

        message = identifier.get_validation_message(boundary)
        assert "containment" in message.lower() or "valid" in message.lower()
