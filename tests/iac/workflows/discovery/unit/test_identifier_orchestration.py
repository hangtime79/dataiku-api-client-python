"""Unit tests for BlockIdentifier orchestration methods."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler
from dataikuapi.iac.workflows.discovery.models import DatasetDetail


@pytest.fixture
def mock_crawler():
    """Create a mock FlowCrawler."""
    return Mock(spec=FlowCrawler)


@pytest.fixture
def identifier(mock_crawler):
    """Create a BlockIdentifier with mock crawler."""
    return BlockIdentifier(mock_crawler)


@pytest.fixture
def mock_project():
    """Create a mock project object."""
    project = Mock()
    return project


@pytest.fixture
def mock_dataset():
    """Create a properly configured mock dataset."""
    dataset = Mock()
    settings = Mock()

    raw_data = {
        "type": "Snowflake",
        "params": {"connection": "DW_CONNECTION"},
        "formatType": "parquet",
        "partitioning": {"dimensions": [{"name": "year"}]},
        "description": "Test dataset",
        "tags": ["tag1"],
    }

    settings.get_raw.return_value = raw_data
    dataset.get_settings.return_value = settings
    dataset.get_schema.return_value = {
        "columns": [{"name": f"col_{i}"} for i in range(5)]
    }

    return dataset


class TestExtractDatasetDetails:
    """Tests for _extract_dataset_details method."""

    def test_extract_dataset_details_success(self, identifier, mock_project, mock_dataset):
        """Test successful orchestration of dataset detail extraction."""
        # Setup
        mock_project.get_dataset.return_value = mock_dataset

        # Execute
        details = identifier._extract_dataset_details(mock_project, ["ds1"])

        # Verify
        assert len(details) == 1
        assert isinstance(details[0], DatasetDetail)
        assert details[0].name == "ds1"
        assert details[0].type == "Snowflake"
        assert details[0].connection == "DW_CONNECTION"
        assert details[0].format_type == "parquet"
        assert details[0].partitioning == "1 dims"
        assert details[0].description == "Test dataset"
        assert details[0].tags == ["tag1"]
        assert details[0].schema_summary["columns"] == 5
        assert len(details[0].schema_summary["sample"]) == 5

    def test_extract_dataset_details_multiple(self, identifier, mock_project, mock_dataset):
        """Test extraction of multiple datasets."""
        # Setup
        mock_project.get_dataset.return_value = mock_dataset

        # Execute
        details = identifier._extract_dataset_details(
            mock_project, ["ds1", "ds2", "ds3"]
        )

        # Verify
        assert len(details) == 3
        assert all(isinstance(d, DatasetDetail) for d in details)
        assert details[0].name == "ds1"
        assert details[1].name == "ds2"
        assert details[2].name == "ds3"

    def test_extract_dataset_details_empty_list(self, identifier, mock_project):
        """Test extraction with empty dataset list."""
        details = identifier._extract_dataset_details(mock_project, [])

        assert len(details) == 0
        assert details == []

    def test_extract_dataset_details_with_failure(
        self, identifier, mock_project, mock_dataset, capsys
    ):
        """Test that failures on individual datasets don't crash the whole extraction."""

        # Setup: First dataset succeeds, second fails, third succeeds
        def get_dataset_side_effect(name):
            if name == "ds2":
                raise Exception("Dataset not found")
            return mock_dataset

        mock_project.get_dataset.side_effect = get_dataset_side_effect

        # Execute
        details = identifier._extract_dataset_details(
            mock_project, ["ds1", "ds2", "ds3"]
        )

        # Verify
        assert len(details) == 2  # Only ds1 and ds3 succeeded
        assert details[0].name == "ds1"
        assert details[1].name == "ds3"

        # Verify error was logged
        captured = capsys.readouterr()
        assert "Warning: Failed to extract details for ds2" in captured.out

    def test_extract_dataset_details_all_fail(
        self, identifier, mock_project, capsys
    ):
        """Test behavior when all datasets fail to extract."""
        # Setup
        mock_project.get_dataset.side_effect = Exception("API Error")

        # Execute
        details = identifier._extract_dataset_details(mock_project, ["ds1", "ds2"])

        # Verify
        assert len(details) == 0
        captured = capsys.readouterr()
        assert "Warning: Failed to extract details for ds1" in captured.out
        assert "Warning: Failed to extract details for ds2" in captured.out

    def test_extract_dataset_details_integration(self, identifier, mock_project):
        """Test full integration of all helper methods."""
        # Create a dataset with complete data
        dataset = Mock()
        settings = Mock()

        raw_data = {
            "type": "PostgreSQL",
            "params": {"connection": "PG_CONN"},
            "formatType": "csv",
            "partitioning": {"dimensions": []},
            "description": "Customer data",
            "tags": ["pii", "production"],
        }

        settings.get_raw.return_value = raw_data
        dataset.get_settings.return_value = settings
        dataset.get_schema.return_value = {
            "columns": [
                {"name": "customer_id"},
                {"name": "email"},
                {"name": "created_at"},
            ]
        }

        mock_project.get_dataset.return_value = dataset

        # Execute
        details = identifier._extract_dataset_details(mock_project, ["CUSTOMERS"])

        # Verify all pieces were assembled correctly
        detail = details[0]
        assert detail.name == "CUSTOMERS"
        assert detail.type == "PostgreSQL"
        assert detail.connection == "PG_CONN"
        assert detail.format_type == "csv"
        assert detail.partitioning is None  # No partitioning
        assert detail.description == "Customer data"
        assert detail.tags == ["pii", "production"]
        assert detail.schema_summary["columns"] == 3
        assert detail.schema_summary["sample"] == ["customer_id", "email", "created_at"]
