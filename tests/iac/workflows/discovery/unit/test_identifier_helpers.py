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


class TestGetRecipeConfig:
    """Tests for _get_recipe_config helper method."""

    @pytest.fixture
    def mock_recipe(self):
        """Mock recipe with standard configuration."""
        recipe = MagicMock()
        settings = MagicMock()
        settings.get_raw.return_value = {
            "type": "python",
            "params": {"engineType": "DSS"},
            "inputs": {"main": {"ref": "input_ds"}},
            "outputs": {"main": {"ref": "output_ds"}}
        }
        recipe.get_settings.return_value = settings
        return recipe

    @pytest.fixture
    def mock_recipe_minimal(self):
        """Mock recipe with minimal/missing fields."""
        recipe = MagicMock()
        settings = MagicMock()
        settings.get_raw.return_value = {}
        recipe.get_settings.return_value = settings
        return recipe

    def test_extracts_basic_fields(self, mock_crawler, mock_recipe):
        """Test extraction of type, engine, inputs, outputs."""
        identifier = BlockIdentifier(mock_crawler)
        config = identifier._get_recipe_config(mock_recipe)

        assert config["type"] == "python"
        assert config["engine"] == "DSS"
        assert isinstance(config["inputs"], list)
        assert isinstance(config["outputs"], list)
        assert "input_ds" in config["inputs"]
        assert "output_ds" in config["outputs"]

    def test_handles_missing_fields(self, mock_crawler, mock_recipe_minimal):
        """Test graceful handling of missing fields."""
        identifier = BlockIdentifier(mock_crawler)
        config = identifier._get_recipe_config(mock_recipe_minimal)

        assert config["type"] == "unknown"
        assert config["engine"] == "DSS"
        assert config["inputs"] == []
        assert config["outputs"] == []


class TestExtractCodeSnippet:
    """Tests for _extract_code_snippet helper method."""

    def test_extracts_first_10_lines(self, mock_crawler):
        """Test extraction of first 10 lines with truncation."""
        identifier = BlockIdentifier(mock_crawler)
        settings = {"payload": "\n".join([f"line{i}" for i in range(20)])}

        snippet = identifier._extract_code_snippet(settings)

        assert snippet.count("\n") == 10  # 10 lines + truncation msg
        assert "truncated" in snippet
        assert "line0" in snippet
        assert "line9" in snippet
        assert "line10" not in snippet

    def test_returns_none_for_no_payload(self, mock_crawler):
        """Test None return when no code present."""
        identifier = BlockIdentifier(mock_crawler)
        settings = {}

        snippet = identifier._extract_code_snippet(settings)

        assert snippet is None

    def test_no_truncation_for_short_code(self, mock_crawler):
        """Test no truncation indicator for <= 10 lines."""
        identifier = BlockIdentifier(mock_crawler)
        settings = {"payload": "line1\nline2\nline3"}

        snippet = identifier._extract_code_snippet(settings)

        assert "truncated" not in snippet
        assert snippet == "line1\nline2\nline3"


@pytest.fixture
def mock_library():
    """Create a mock library with python and R folders."""
    library = Mock()
    root = Mock()

    # Mock python folder with 2 files
    python_folder = Mock()
    python_file1 = Mock()
    python_file1.name = "utils.py"
    python_file1.children = None  # File indicator
    python_file2 = Mock()
    python_file2.name = "helpers.py"
    python_file2.children = None
    python_folder.children = {python_file1, python_file2}
    python_folder.list.return_value = [python_file1, python_file2]

    # Mock R folder with 1 file
    r_folder = Mock()
    r_file = Mock()
    r_file.name = "analysis.R"
    r_file.children = None
    r_folder.children = {r_file}
    r_folder.list.return_value = [r_file]

    # Wire up get_child
    def get_child_side_effect(name):
        if name == "python":
            return python_folder
        elif name == "R":
            return r_folder
        return None

    root.get_child.side_effect = get_child_side_effect
    library.root = root

    return library


@pytest.fixture
def mock_notebooks():
    """Create mock notebook list items."""
    nb1 = Mock()
    nb1.name = "exploration.ipynb"
    nb1.language = "python"

    nb2 = Mock()
    nb2.name = "analysis.ipynb"
    nb2.language = "python"

    return [nb1, nb2]


class TestExtractLibraryRefs:
    """Tests for _extract_library_refs method."""

    def test_extract_library_refs_success(self, identifier, mock_library):
        """Test successful extraction of library files."""
        project = Mock()
        project.get_library.return_value = mock_library

        refs = identifier._extract_library_refs(project)

        assert len(refs) == 3  # 2 python + 1 R

        # Check python files
        python_refs = [r for r in refs if r.type == "python"]
        assert len(python_refs) == 2
        assert any(r.name == "utils.py" for r in python_refs)
        assert any(r.name == "helpers.py" for r in python_refs)

        # Check R files
        r_refs = [r for r in refs if r.type == "R"]
        assert len(r_refs) == 1
        assert r_refs[0].name == "analysis.R"

    def test_extract_library_refs_empty_library(self, identifier):
        """Test extraction with no library files."""
        project = Mock()
        library = Mock()
        root = Mock()
        root.get_child.return_value = None  # No python or R folders
        library.root = root
        project.get_library.return_value = library

        refs = identifier._extract_library_refs(project)

        assert refs == []

    def test_extract_library_refs_error(self, identifier, capsys):
        """Test extraction handles errors gracefully."""
        project = Mock()
        project.get_library.side_effect = Exception("Library access failed")

        refs = identifier._extract_library_refs(project)

        assert refs == []  # Should return empty list, not raise


class TestExtractNotebookRefs:
    """Tests for _extract_notebook_refs method."""

    def test_extract_notebook_refs_success(self, identifier, mock_notebooks):
        """Test successful extraction of notebooks."""
        project = Mock()
        project.list_jupyter_notebooks.return_value = mock_notebooks

        refs = identifier._extract_notebook_refs(project)

        assert len(refs) == 2
        assert all(r.type == "jupyter" for r in refs)
        assert any(r.name == "exploration.ipynb" for r in refs)
        assert any(r.name == "analysis.ipynb" for r in refs)

        # Verify correct API call
        project.list_jupyter_notebooks.assert_called_once_with(
            active=False, as_type="listitems"
        )

    def test_extract_notebook_refs_empty(self, identifier):
        """Test extraction with no notebooks."""
        project = Mock()
        project.list_jupyter_notebooks.return_value = []

        refs = identifier._extract_notebook_refs(project)

        assert refs == []

    def test_extract_notebook_refs_error(self, identifier, capsys):
        """Test extraction handles errors gracefully."""
        project = Mock()
        project.list_jupyter_notebooks.side_effect = Exception("Notebook access failed")

        refs = identifier._extract_notebook_refs(project)

        assert refs == []  # Should return empty list, not raise
