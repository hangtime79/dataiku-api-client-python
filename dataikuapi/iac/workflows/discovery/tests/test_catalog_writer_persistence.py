"""Unit tests for CatalogWriter persistence operations.

This module tests write operations to project-local registries using mocked
Dataiku API calls. Tests verify that the correct API methods are called with
the correct parameters, without actually writing to a real Dataiku instance.

Test Coverage:
- write_to_project_registry() method
- _ensure_project_registry_exists() method
- _write_wiki_article() method
- _write_schemas() method
- _update_discovery_index() method
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import json
from datetime import datetime

from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
from dataikuapi.iac.workflows.discovery.models import (
    BlockMetadata,
    BlockPort,
    BlockContents,
)
from dataikuapi.iac.workflows.discovery.exceptions import CatalogWriteError


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_client():
    """Create mock DSSClient."""
    client = Mock()
    return client


@pytest.fixture
def mock_project(mock_client):
    """Create mock DSSProject with library and wiki."""
    project = Mock()
    project.project_key = "TEST_PROJECT"

    # Create a stateful folder structure
    # Track folders that have been created
    folder_state = {}

    # Create mock folders
    schemas_folder = Mock()
    schemas_folder.get_child = Mock(return_value=None)
    schemas_folder.add_file = Mock(return_value=Mock())

    discovery_folder = Mock()

    def discovery_get_child(name):
        if name == "schemas":
            return folder_state.get("schemas")
        elif name == "index.json":
            return folder_state.get("index.json")
        return None

    discovery_folder.get_child = Mock(side_effect=discovery_get_child)

    def discovery_add_folder(name):
        if name == "schemas":
            folder_state["schemas"] = schemas_folder
        return schemas_folder

    discovery_folder.add_folder = Mock(side_effect=discovery_add_folder)

    def discovery_add_file(name):
        file_mock = Mock()
        file_mock.write = Mock()
        file_mock.read = Mock(
            return_value='{"blocks": [], "last_updated": "2024-01-01T00:00:00Z"}'
        )
        folder_state[name] = file_mock
        return file_mock

    discovery_folder.add_file = Mock(side_effect=discovery_add_file)

    # Root folder
    root_folder = Mock()

    def root_get_child(name):
        if name == "discovery":
            return folder_state.get("discovery")
        return None

    root_folder.get_child = Mock(side_effect=root_get_child)

    def root_add_folder(name):
        if name == "discovery":
            folder_state["discovery"] = discovery_folder
        return discovery_folder

    root_folder.add_folder = Mock(side_effect=root_add_folder)
    root_folder.add_file = Mock(return_value=Mock())

    # Mock library
    library = Mock()
    library.root = root_folder
    library.get_file = Mock()
    library.get_folder = Mock()
    project.get_library = Mock(return_value=library)

    # Mock wiki
    wiki = Mock()
    wiki.get_article = Mock(side_effect=Exception("Article not found"))
    wiki.create_article = Mock(return_value=Mock())
    project.get_wiki = Mock(return_value=wiki)

    # Connect to client
    mock_client.get_project = Mock(return_value=project)

    return project


@pytest.fixture
def sample_block():
    """Create sample BlockMetadata for testing."""
    block = BlockMetadata(
        block_id="TEST_BLOCK",
        version="1.0.0",
        type="zone",
        blocked=False,
        name="Test Block",
        description="Test block for unit testing",
        source_project="TEST_PROJECT",
        source_zone="test_zone",
        hierarchy_level="process",
        domain="test",
        inputs=[
            BlockPort(
                name="input1",
                type="dataset",
                required=True,
                description="Test input",
                schema_ref="schemas/TEST_BLOCK_input1.schema.json",
            )
        ],
        outputs=[
            BlockPort(
                name="output1",
                type="dataset",
                required=True,
                description="Test output",
                schema_ref="schemas/TEST_BLOCK_output1.schema.json",
            )
        ],
        contains=BlockContents(datasets=["dataset1"], recipes=["recipe1"], models=[]),
        tags=["test"],
        dependencies={},
    )

    # Dynamically add schema attribute (as schema_extractor might do)
    block.inputs[0].schema = {"columns": [{"name": "col1", "type": "string"}]}
    block.outputs[0].schema = {"columns": [{"name": "col2", "type": "int"}]}

    return block


@pytest.fixture
def sample_blocks():
    """Create list of sample blocks."""
    return [
        BlockMetadata(
            block_id=f"TEST_BLOCK_{i}",
            version="1.0.0",
            type="zone",
            blocked=False,
            name=f"Test Block {i}",
            description=f"Test block {i}",
            source_project="TEST_PROJECT",
            inputs=[],
            outputs=[],
            contains=BlockContents(datasets=[], recipes=[], models=[]),
        )
        for i in range(3)
    ]


# ============================================================================
# Test Class 1: TestWriteToProjectRegistry
# ============================================================================


class TestWriteToProjectRegistry:
    """Test main write_to_project_registry() method."""

    def test_write_single_block_calls_all_methods(
        self, mock_client, mock_project, sample_block
    ):
        """Verify write orchestration calls all sub-methods."""
        writer = CatalogWriter(client=mock_client)

        # Execute
        result = writer.write_to_project_registry("TEST_PROJECT", [sample_block])

        # Verify results structure
        assert "project_key" in result
        assert "blocks_written" in result
        assert "wiki_articles" in result
        assert "schemas_written" in result
        assert "index_updated" in result

        # Verify counts
        assert result["blocks_written"] == 1
        assert len(result["wiki_articles"]) == 1
        assert result["index_updated"] == True

    def test_write_multiple_blocks(self, mock_client, mock_project, sample_blocks):
        """Verify batch write of multiple blocks."""
        writer = CatalogWriter(client=mock_client)

        # Execute
        result = writer.write_to_project_registry("TEST_PROJECT", sample_blocks)

        # Verify all blocks written
        assert result["blocks_written"] == 3
        assert len(result["wiki_articles"]) == 3

    def test_write_returns_correct_statistics(
        self, mock_client, mock_project, sample_block
    ):
        """Verify return value contains expected fields."""
        writer = CatalogWriter(client=mock_client)

        # Execute
        result = writer.write_to_project_registry("TEST_PROJECT", [sample_block])

        # Verify all required fields present
        required_fields = [
            "project_key",
            "blocks_written",
            "wiki_articles",
            "schemas_written",
            "index_updated",
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

        # Verify types
        assert isinstance(result["project_key"], str)
        assert isinstance(result["blocks_written"], int)
        assert isinstance(result["wiki_articles"], list)
        assert isinstance(result["schemas_written"], int)
        assert isinstance(result["index_updated"], bool)

    def test_write_without_client_raises_error(self):
        """Verify error when CatalogWriter has no client."""
        writer = CatalogWriter(client=None)

        with pytest.raises(CatalogWriteError, match="requires DSSClient"):
            writer.write_to_project_registry("MY_PROJECT", [])

    def test_write_empty_block_list(self, mock_client, mock_project):
        """Verify handling of empty block list."""
        writer = CatalogWriter(client=mock_client)

        # Execute
        result = writer.write_to_project_registry("TEST_PROJECT", [])

        # Should create structure but write 0 blocks
        assert result["blocks_written"] == 0
        assert len(result["wiki_articles"]) == 0
        assert result["index_updated"] == True  # Index still updated


# ============================================================================
# Test Class 2: TestEnsureProjectRegistryExists
# ============================================================================


class TestEnsureProjectRegistryExists:
    """Test registry structure initialization."""

    def test_creates_discovery_folder(self, mock_client, mock_project):
        """Verify discovery folder created in library."""
        writer = CatalogWriter(client=mock_client)

        # Mock: discovery folder doesn't exist
        library = mock_project.get_library()
        library.root.get_child.return_value = None

        # Execute
        project = writer._ensure_project_registry_exists("TEST_PROJECT")

        # Verify folder creation attempted
        library.root.add_folder.assert_called()
        # Check discovery folder was requested
        add_folder_calls = [
            call[0][0] for call in library.root.add_folder.call_args_list
        ]
        assert "discovery" in add_folder_calls

    def test_creates_schemas_subfolder(self, mock_client, mock_project):
        """Verify schemas subfolder created."""
        writer = CatalogWriter(client=mock_client)

        # Mock: discovery exists but schemas doesn't
        library = mock_project.get_library()
        discovery_folder = Mock()
        discovery_folder.get_child = Mock(return_value=None)
        discovery_folder.add_folder = Mock(return_value=Mock())
        discovery_folder.add_file = Mock(return_value=Mock())

        # First call returns None (doesn't exist), second call returns the folder
        library.root.get_child = Mock(side_effect=[None, discovery_folder])
        library.root.add_folder = Mock(return_value=discovery_folder)

        # Execute
        writer._ensure_project_registry_exists("TEST_PROJECT")

        # Verify schemas folder created within discovery
        discovery_folder.add_folder.assert_called()

    def test_creates_initial_index_json(self, mock_client, mock_project):
        """Verify index.json initialized with correct structure."""
        writer = CatalogWriter(client=mock_client)

        # Mock: index.json doesn't exist
        library = mock_project.get_library()
        discovery_folder = Mock()
        schemas_folder = Mock()

        discovery_folder.get_child = Mock(
            side_effect=[
                None,  # schemas folder doesn't exist
                None,  # index.json doesn't exist
            ]
        )
        discovery_folder.add_folder = Mock(return_value=schemas_folder)

        mock_index_file = Mock()
        discovery_folder.add_file = Mock(return_value=mock_index_file)

        library.root.get_child = Mock(return_value=discovery_folder)

        # Execute
        writer._ensure_project_registry_exists("TEST_PROJECT")

        # Verify index.json created
        discovery_folder.add_file.assert_called_with("index.json")

        # Verify initial content written
        mock_index_file.write.assert_called_once()
        written_content = mock_index_file.write.call_args[0][0]
        index_data = json.loads(written_content)

        assert index_data["version"] == "1.0"
        assert index_data["project_key"] == "TEST_PROJECT"
        assert index_data["blocks"] == []
        assert index_data["last_updated"] is None

    def test_handles_existing_structure(self, mock_client, mock_project):
        """Verify graceful handling when structure already exists."""
        writer = CatalogWriter(client=mock_client)

        # Mock: everything already exists
        library = mock_project.get_library()
        discovery_folder = Mock()
        schemas_folder = Mock()
        index_file = Mock()

        discovery_folder.get_child = Mock(side_effect=[schemas_folder, index_file])
        library.root.get_child = Mock(return_value=discovery_folder)

        # Execute - should not raise error
        project = writer._ensure_project_registry_exists("TEST_PROJECT")

        assert project is not None
        # Verify no creation calls made
        library.root.add_folder.assert_not_called()

    def test_raises_error_on_project_not_found(self, mock_client):
        """Verify error when project doesn't exist."""
        mock_client.get_project.side_effect = Exception("Project not found")

        writer = CatalogWriter(client=mock_client)

        with pytest.raises(CatalogWriteError, match="Failed to access project"):
            writer._ensure_project_registry_exists("NONEXISTENT")


# ============================================================================
# Test Class 3: TestWriteWikiArticle
# ============================================================================


class TestWriteWikiArticle:
    """Test Wiki article writing."""

    def test_creates_new_article(self, mock_client, mock_project, sample_block):
        """Verify new Wiki article created with correct parent."""
        writer = CatalogWriter(client=mock_client)

        # Mock: parent folder article
        wiki = mock_project.get_wiki()
        parent_article = Mock()
        parent_article.article_id = "parent_id"

        def get_article_side_effect(name):
            if name == "_DISCOVERED_BLOCKS":
                return parent_article
            raise Exception("Not found")

        wiki.get_article.side_effect = get_article_side_effect

        # Execute
        article_name = writer._write_wiki_article(mock_project, sample_block)

        # Verify correct name returned
        assert article_name == sample_block.block_id

        # Verify create_article called with parent_id
        wiki.create_article.assert_called_once()
        call_args = wiki.create_article.call_args

        # Check arguments
        assert call_args[0][0] == sample_block.block_id  # article name
        assert call_args[1]["parent_id"] == "parent_id"  # parent ID
        assert sample_block.block_id in call_args[1]["content"]  # content

    def test_updates_existing_article(self, mock_client, mock_project, sample_block):
        """Verify existing article updated (merged) correctly."""
        writer = CatalogWriter(client=mock_client)

        # Mock: both parent and article exist
        wiki = mock_project.get_wiki()

        # Parent article
        parent_article = Mock()
        parent_article.article_id = "parent_id"

        # Existing article with data
        existing_article_data = Mock()
        existing_article_data.get_body = Mock(
            return_value="Existing content\n\n## Changelog\n- 0.9.0: Old version"
        )
        existing_article_data.set_body = Mock()
        existing_article_data.save = Mock()

        existing_article = Mock()
        existing_article.get_data = Mock(return_value=existing_article_data)

        def get_article_side_effect(name):
            if name == "_DISCOVERED_BLOCKS":
                return parent_article
            elif name == sample_block.block_id:
                return existing_article
            raise Exception("Not found")

        wiki.get_article.side_effect = get_article_side_effect

        # Execute
        article_name = writer._write_wiki_article(mock_project, sample_block)

        # Verify update called, not create
        wiki.create_article.assert_not_called()
        existing_article_data.set_body.assert_called_once()
        existing_article_data.save.assert_called_once()

        # Verify merged content
        merged_content = existing_article_data.set_body.call_args[0][0]
        assert "0.9.0: Old version" in merged_content  # Preserved changelog

    def test_article_path_structure(self, mock_client, mock_project, sample_block):
        """Verify article name returned is block_id."""
        writer = CatalogWriter(client=mock_client)

        # Mock parent
        wiki = mock_project.get_wiki()
        parent_article = Mock()
        parent_article.article_id = "parent_id"

        def get_article_side_effect(name):
            if name == "_DISCOVERED_BLOCKS":
                return parent_article
            raise Exception("Not found")

        wiki.get_article.side_effect = get_article_side_effect

        # Execute
        article_name = writer._write_wiki_article(mock_project, sample_block)

        # Verify name is block_id
        assert article_name == sample_block.block_id


# ============================================================================
# Test Class 4: TestWriteSchemas
# ============================================================================


class TestWriteSchemas:
    """Test schema file writing."""

    def test_writes_input_and_output_schemas(
        self, mock_client, mock_project, sample_block
    ):
        """Verify input and output schemas written to library."""
        writer = CatalogWriter(client=mock_client)

        # Mock library structure
        library = mock_project.get_library()
        discovery_folder = Mock()
        schemas_folder = Mock()
        schemas_folder.get_child = Mock(return_value=None)  # Files don't exist

        mock_schema_file = Mock()
        schemas_folder.add_file = Mock(return_value=mock_schema_file)

        discovery_folder.get_child = Mock(return_value=schemas_folder)
        library.root.get_child = Mock(return_value=discovery_folder)

        # Execute
        count = writer._write_schemas(mock_project, sample_block)

        # Verify count (1 input + 1 output = 2)
        assert count == 2

        # Verify file writes called
        assert schemas_folder.add_file.call_count == 2

    def test_schema_file_naming(self, mock_client, mock_project, sample_block):
        """Verify schema file names: {block_id}_{port_name}.schema.json"""
        writer = CatalogWriter(client=mock_client)

        # Mock library
        library = mock_project.get_library()
        discovery_folder = Mock()
        schemas_folder = Mock()
        schemas_folder.get_child = Mock(return_value=None)
        schemas_folder.add_file = Mock(return_value=Mock())

        discovery_folder.get_child = Mock(return_value=schemas_folder)
        library.root.get_child = Mock(return_value=discovery_folder)

        # Execute
        writer._write_schemas(mock_project, sample_block)

        # Verify file names
        add_file_calls = [call[0][0] for call in schemas_folder.add_file.call_args_list]

        expected_input_name = f"{sample_block.block_id}_input1.schema.json"
        expected_output_name = f"{sample_block.block_id}_output1.schema.json"

        assert expected_input_name in add_file_calls
        assert expected_output_name in add_file_calls

    def test_updates_existing_schemas(self, mock_client, mock_project, sample_block):
        """Verify existing schema files updated."""
        writer = CatalogWriter(client=mock_client)

        # Mock: schema files exist
        library = mock_project.get_library()
        discovery_folder = Mock()
        schemas_folder = Mock()

        existing_file = Mock()
        schemas_folder.get_child = Mock(return_value=existing_file)

        discovery_folder.get_child = Mock(return_value=schemas_folder)
        library.root.get_child = Mock(return_value=discovery_folder)

        # Execute
        writer._write_schemas(mock_project, sample_block)

        # Verify write called on existing file (not add_file)
        assert existing_file.write.call_count == 2  # input + output

    def test_skips_ports_without_schemas(self, mock_client, mock_project):
        """Verify ports without schemas don't create files."""
        # Create block without schemas
        block = BlockMetadata(
            block_id="NO_SCHEMAS",
            version="1.0.0",
            type="zone",
            blocked=False,
            source_project="TEST",
            inputs=[BlockPort(name="in", type="dataset", required=True)],
            outputs=[],
            contains=BlockContents(datasets=[], recipes=[], models=[]),
        )
        # No schema attribute added - ports have no schemas

        writer = CatalogWriter(client=mock_client)

        # Mock library
        library = mock_project.get_library()
        discovery_folder = Mock()
        schemas_folder = Mock()
        discovery_folder.get_child = Mock(return_value=schemas_folder)
        library.root.get_child = Mock(return_value=discovery_folder)

        # Execute
        count = writer._write_schemas(mock_project, block)

        # No schemas should be written
        assert count == 0


# ============================================================================
# Test Class 5: TestUpdateDiscoveryIndex
# ============================================================================


class TestUpdateDiscoveryIndex:
    """Test index.json update logic."""

    def test_creates_new_index(self, mock_client, mock_project, sample_block):
        """Verify new index created if doesn't exist."""
        writer = CatalogWriter(client=mock_client)

        # Mock: index doesn't exist
        library = mock_project.get_library()
        discovery_folder = Mock()
        discovery_folder.get_child = Mock(
            side_effect=[None, None]
        )  # index doesn't exist both times

        mock_index_file = Mock()
        discovery_folder.add_file = Mock(return_value=mock_index_file)

        library.root.get_child = Mock(return_value=discovery_folder)

        # Execute
        writer._update_discovery_index(mock_project, [sample_block])

        # Verify index file created and written
        discovery_folder.add_file.assert_called_with("index.json")
        mock_index_file.write.assert_called_once()

    def test_merges_with_existing_index(self, mock_client, mock_project, sample_blocks):
        """Verify new blocks merged into existing index."""
        writer = CatalogWriter(client=mock_client)

        # Mock: index exists with some blocks
        existing_index = {
            "version": "1.0",
            "project_key": "TEST_PROJECT",
            "blocks": [{"block_id": "EXISTING_BLOCK", "version": "1.0.0"}],
        }

        library = mock_project.get_library()
        discovery_folder = Mock()
        mock_index_file = Mock()
        mock_index_file.read = Mock(return_value=json.dumps(existing_index))
        discovery_folder.get_child = Mock(return_value=mock_index_file)
        library.root.get_child = Mock(return_value=discovery_folder)

        # Execute
        writer._update_discovery_index(mock_project, sample_blocks)

        # Verify write called
        mock_index_file.write.assert_called_once()

        # Verify merged content
        written_content = mock_index_file.write.call_args[0][0]
        merged_index = json.loads(written_content)

        # Should have original + new blocks
        assert len(merged_index["blocks"]) >= 3

    def test_updates_timestamp(self, mock_client, mock_project, sample_block):
        """Verify last_updated timestamp added."""
        writer = CatalogWriter(client=mock_client)

        # Mock: index exists
        library = mock_project.get_library()
        discovery_folder = Mock()
        mock_index_file = Mock()
        mock_index_file.read = Mock(
            return_value=json.dumps(
                {"version": "1.0", "project_key": "TEST_PROJECT", "blocks": []}
            )
        )
        discovery_folder.get_child = Mock(return_value=mock_index_file)
        library.root.get_child = Mock(return_value=discovery_folder)

        # Execute
        writer._update_discovery_index(mock_project, [sample_block])

        # Verify timestamp added
        written_content = mock_index_file.write.call_args[0][0]
        updated_index = json.loads(written_content)

        assert "last_updated" in updated_index
        assert updated_index["last_updated"] is not None


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
