"""Unit tests for BlockIdentifier main integration."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler
from dataikuapi.iac.workflows.discovery.models import (
    EnhancedBlockMetadata,
    DatasetDetail,
    BlockContents,
)


@pytest.fixture
def mock_client():
    """Create a mock DSSClient."""
    return Mock()


@pytest.fixture
def mock_crawler(mock_client):
    """Create a mock FlowCrawler with client."""
    crawler = Mock(spec=FlowCrawler)
    crawler.client = mock_client
    return crawler


@pytest.fixture
def identifier(mock_crawler):
    """Create a BlockIdentifier with mock crawler."""
    return BlockIdentifier(mock_crawler)


@pytest.fixture
def sample_boundary():
    """Create a sample zone boundary."""
    return {
        "is_valid": True,
        "inputs": ["input_dataset"],
        "outputs": ["output_dataset"],
        "internals": ["internal_dataset_1", "internal_dataset_2"],
    }


@pytest.fixture
def sample_zone_items():
    """Create sample zone items."""
    return {
        "datasets": ["input_dataset", "internal_dataset_1", "internal_dataset_2", "output_dataset"],
        "recipes": ["recipe1", "recipe2"],
    }


@pytest.fixture
def mock_dataset():
    """Create a mock dataset with complete data."""
    dataset = Mock()
    settings = Mock()

    raw_data = {
        "type": "Snowflake",
        "params": {"connection": "DW_CONNECTION"},
        "formatType": "parquet",
        "partitioning": {"dimensions": [{"name": "year"}]},
        "description": "Internal dataset",
        "tags": ["internal"],
    }

    settings.get_raw.return_value = raw_data
    dataset.get_settings.return_value = settings
    dataset.get_schema.return_value = {
        "columns": [{"name": f"col_{i}"} for i in range(3)]
    }

    return dataset


@pytest.fixture
def mock_project(mock_dataset):
    """Create a mock project that returns datasets."""
    project = Mock()
    project.get_dataset.return_value = mock_dataset
    return project


class TestExtractBlockMetadataIntegration:
    """Tests for extract_block_metadata main entry point."""

    def test_extract_block_metadata_includes_dataset_details(
        self, identifier, mock_crawler, mock_client, mock_project,
        sample_boundary, sample_zone_items
    ):
        """Test that extract_block_metadata now includes dataset details."""
        # Setup mocks
        mock_crawler.get_zone_items.return_value = sample_zone_items
        mock_client.get_project.return_value = mock_project

        # Execute
        metadata = identifier.extract_block_metadata("TEST_PROJECT", "test_zone", sample_boundary)

        # Verify type
        assert isinstance(metadata, EnhancedBlockMetadata)

        # Verify basic metadata
        assert metadata.block_id == "TEST_ZONE"
        assert metadata.version == "1.0.0"
        assert metadata.type == "zone"
        assert metadata.source_project == "TEST_PROJECT"
        assert metadata.source_zone == "test_zone"

        # Verify dataset details were extracted
        assert hasattr(metadata, "dataset_details")
        assert isinstance(metadata.dataset_details, list)
        assert len(metadata.dataset_details) == 2  # Two internal datasets

        # Verify dataset details content
        for detail in metadata.dataset_details:
            assert isinstance(detail, DatasetDetail)
            assert detail.type == "Snowflake"
            assert detail.connection == "DW_CONNECTION"
            assert detail.format_type == "parquet"
            assert detail.schema_summary["columns"] == 3

    def test_extract_block_metadata_with_no_internal_datasets(
        self, identifier, mock_crawler, mock_client, mock_project, sample_boundary
    ):
        """Test extraction when there are no internal datasets."""
        # Setup - zone with no internals
        sample_boundary["internals"] = []
        zone_items = {
            "datasets": ["input_dataset", "output_dataset"],
            "recipes": ["recipe1"],
        }

        mock_crawler.get_zone_items.return_value = zone_items
        mock_client.get_project.return_value = mock_project

        # Execute
        metadata = identifier.extract_block_metadata("TEST_PROJECT", "test_zone", sample_boundary)

        # Verify
        assert isinstance(metadata, EnhancedBlockMetadata)
        assert len(metadata.dataset_details) == 0

    def test_extract_block_metadata_preserves_existing_functionality(
        self, identifier, mock_crawler, mock_client, mock_project,
        sample_boundary, sample_zone_items
    ):
        """Test that existing BlockMetadata fields are still populated correctly."""
        # Setup
        mock_crawler.get_zone_items.return_value = sample_zone_items
        mock_client.get_project.return_value = mock_project

        # Execute
        metadata = identifier.extract_block_metadata("TEST_PROJECT", "test_zone", sample_boundary)

        # Verify all existing fields still work
        assert len(metadata.inputs) == 1
        assert metadata.inputs[0].name == "input_dataset"

        assert len(metadata.outputs) == 1
        assert metadata.outputs[0].name == "output_dataset"

        assert isinstance(metadata.contains, BlockContents)
        assert metadata.contains.datasets == ["internal_dataset_1", "internal_dataset_2"]
        assert metadata.contains.recipes == ["recipe1", "recipe2"]

    def test_extract_block_metadata_handles_dataset_extraction_failures(
        self, identifier, mock_crawler, mock_client, sample_boundary, sample_zone_items, capsys
    ):
        """Test that failures in dataset detail extraction don't crash metadata extraction."""
        # Setup - project that fails to get datasets
        mock_project = Mock()
        mock_project.get_dataset.side_effect = Exception("Dataset not found")

        mock_crawler.get_zone_items.return_value = sample_zone_items
        mock_client.get_project.return_value = mock_project

        # Execute - should not crash
        metadata = identifier.extract_block_metadata("TEST_PROJECT", "test_zone", sample_boundary)

        # Verify
        assert isinstance(metadata, EnhancedBlockMetadata)
        assert len(metadata.dataset_details) == 0  # All extractions failed

        # Verify warnings were logged
        captured = capsys.readouterr()
        assert "Warning: Failed to extract details for internal_dataset_1" in captured.out
        assert "Warning: Failed to extract details for internal_dataset_2" in captured.out

    def test_extract_block_metadata_serialization(
        self, identifier, mock_crawler, mock_client, mock_project,
        sample_boundary, sample_zone_items
    ):
        """Test that EnhancedBlockMetadata can be serialized to dict."""
        # Setup
        mock_crawler.get_zone_items.return_value = sample_zone_items
        mock_client.get_project.return_value = mock_project

        # Execute
        metadata = identifier.extract_block_metadata("TEST_PROJECT", "test_zone", sample_boundary)

        # Verify serialization works
        metadata_dict = metadata.to_dict()

        assert isinstance(metadata_dict, dict)
        assert "block_id" in metadata_dict
        assert "dataset_details" in metadata_dict
        assert isinstance(metadata_dict["dataset_details"], list)
        assert len(metadata_dict["dataset_details"]) == 2

        # Verify dataset details are serialized
        for ds_detail in metadata_dict["dataset_details"]:
            assert isinstance(ds_detail, dict)
            assert "name" in ds_detail
            assert "type" in ds_detail
            assert "schema_summary" in ds_detail
