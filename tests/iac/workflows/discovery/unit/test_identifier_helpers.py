"""Unit tests for BlockIdentifier helper methods."""

import pytest
from unittest.mock import Mock, MagicMock
from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler


@pytest.fixture
def mock_crawler():
    """Create a mock FlowCrawler."""
    return Mock(spec=FlowCrawler)


@pytest.fixture
def identifier(mock_crawler):
    """Create a BlockIdentifier with mock crawler."""
    return BlockIdentifier(mock_crawler)


@pytest.fixture
def mock_dataset():
    """Create a mock dataset object."""
    dataset = Mock()
    settings = Mock()

    # Default mock data - Snowflake dataset
    raw_data = {
        "type": "Snowflake",
        "params": {
            "connection": "DW_CONNECTION"
        },
        "formatType": "parquet",
        "partitioning": {
            "dimensions": [
                {"name": "year"},
                {"name": "month"}
            ]
        }
    }

    settings.get_raw.return_value = raw_data
    dataset.get_settings.return_value = settings

    # Add schema mock for schema tests
    dataset.get_schema.return_value = {
        "columns": [{"name": f"col_{i}"} for i in range(10)]
    }

    return dataset


class TestGetDatasetConfig:
    """Tests for _get_dataset_config method."""

    def test_get_dataset_config_complete(self, identifier, mock_dataset):
        """Test extraction of complete dataset configuration."""
        config = identifier._get_dataset_config(mock_dataset)

        assert config["type"] == "Snowflake"
        assert config["connection"] == "DW_CONNECTION"
        assert config["format_type"] == "parquet"
        assert config["partitioning"] == "2 dims"

    def test_get_dataset_config_no_partitioning(self, identifier, mock_dataset):
        """Test dataset without partitioning."""
        settings = mock_dataset.get_settings()
        raw_data = settings.get_raw()
        raw_data["partitioning"] = {"dimensions": []}

        config = identifier._get_dataset_config(mock_dataset)

        assert config["partitioning"] is None

    def test_get_dataset_config_missing_fields(self, identifier):
        """Test dataset with missing optional fields."""
        dataset = Mock()
        settings = Mock()

        # Minimal data
        raw_data = {
            "type": "PostgreSQL"
        }

        settings.get_raw.return_value = raw_data
        dataset.get_settings.return_value = settings

        config = identifier._get_dataset_config(dataset)

        assert config["type"] == "PostgreSQL"
        assert config["connection"] == ""
        assert config["format_type"] == ""
        assert config["partitioning"] is None

    def test_get_dataset_config_unknown_type(self, identifier):
        """Test dataset with unknown type."""
        dataset = Mock()
        settings = Mock()

        raw_data = {}

        settings.get_raw.return_value = raw_data
        dataset.get_settings.return_value = settings

        config = identifier._get_dataset_config(dataset)

        assert config["type"] == "unknown"
