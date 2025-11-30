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
        },
        "description": "Test dataset description",
        "tags": ["tag1", "tag2", "production"]
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


class TestSummarizeSchema:
    """Tests for _summarize_schema method."""

    def test_summarize_schema_success(self, identifier, mock_dataset):
        """Test successful schema summarization."""
        summary = identifier._summarize_schema(mock_dataset)

        assert summary["columns"] == 10
        assert len(summary["sample"]) == 5
        assert summary["sample"][0] == "col_0"
        assert summary["sample"][4] == "col_4"

    def test_summarize_schema_less_than_five_columns(self, identifier):
        """Test schema with fewer than 5 columns."""
        dataset = Mock()
        dataset.get_schema.return_value = {
            "columns": [{"name": f"col_{i}"} for i in range(3)]
        }

        summary = identifier._summarize_schema(dataset)

        assert summary["columns"] == 3
        assert len(summary["sample"]) == 3
        assert summary["sample"] == ["col_0", "col_1", "col_2"]

    def test_summarize_schema_empty(self, identifier):
        """Test dataset with no columns."""
        dataset = Mock()
        dataset.get_schema.return_value = {"columns": []}

        summary = identifier._summarize_schema(dataset)

        assert summary["columns"] == 0
        assert summary["sample"] == []

    def test_summarize_schema_error_handling(self, identifier):
        """Test graceful error handling when schema fetch fails."""
        dataset = Mock()
        dataset.get_schema.side_effect = Exception("API Error")

        summary = identifier._summarize_schema(dataset)

        assert summary["columns"] == 0
        assert summary["sample"] == []

    def test_summarize_schema_missing_columns_key(self, identifier):
        """Test handling of malformed schema response."""
        dataset = Mock()
        dataset.get_schema.return_value = {}

        summary = identifier._summarize_schema(dataset)

        assert summary["columns"] == 0
        assert summary["sample"] == []


class TestGetDatasetDocs:
    """Tests for _get_dataset_docs method."""

    def test_get_dataset_docs_complete(self, identifier, mock_dataset):
        """Test extraction of complete documentation."""
        docs = identifier._get_dataset_docs(mock_dataset)

        assert docs["description"] == "Test dataset description"
        assert "tag1" in docs["tags"]
        assert "tag2" in docs["tags"]
        assert "production" in docs["tags"]
        assert len(docs["tags"]) == 3

    def test_get_dataset_docs_no_description(self, identifier):
        """Test dataset without description."""
        dataset = Mock()
        settings = Mock()
        raw_data = {"tags": ["tag1"]}

        settings.get_raw.return_value = raw_data
        dataset.get_settings.return_value = settings

        docs = identifier._get_dataset_docs(dataset)

        assert docs["description"] == ""
        assert docs["tags"] == ["tag1"]

    def test_get_dataset_docs_no_tags(self, identifier):
        """Test dataset without tags."""
        dataset = Mock()
        settings = Mock()
        raw_data = {"description": "A dataset"}

        settings.get_raw.return_value = raw_data
        dataset.get_settings.return_value = settings

        docs = identifier._get_dataset_docs(dataset)

        assert docs["description"] == "A dataset"
        assert docs["tags"] == []

    def test_get_dataset_docs_empty(self, identifier):
        """Test dataset with no documentation."""
        dataset = Mock()
        settings = Mock()
        raw_data = {}

        settings.get_raw.return_value = raw_data
        dataset.get_settings.return_value = settings

        docs = identifier._get_dataset_docs(dataset)

        assert docs["description"] == ""
        assert docs["tags"] == []
