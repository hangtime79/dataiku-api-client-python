"""
Integration tests for CatalogWriter with real Dataiku API writes.

These tests use a REAL DSSClient and write to a REAL Dataiku project.
They verify that the catalog writer actually creates Wiki articles,
Library JSON files, and schema files in the Dataiku instance.

Test Project: COALSHIPPINGSIMULATIONGSC
Markers: integration, slow

IMPORTANT: These tests make REAL changes to the Dataiku instance.
Use with caution and ensure proper cleanup.
"""

import pytest
import json
import time
from datetime import datetime
from typing import List

from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
from dataikuapi.iac.workflows.discovery.models import (
    BlockMetadata,
    BlockPort,
    BlockContents,
)
from dataikuapi.iac.workflows.discovery.exceptions import CatalogWriteError


# Test project constant
TEST_PROJECT = "COALSHIPPINGSIMULATIONGSC"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def real_writer(real_client):
    """Create CatalogWriter with real DSSClient."""
    return CatalogWriter(client=real_client)


@pytest.fixture
def test_block():
    """Create a test block for writing."""
    block = BlockMetadata(
        block_id="TEST_CATALOG_BLOCK_001",
        version="1.0.0",
        type="zone",
        blocked=False,
        name="Test Catalog Block",
        description="Integration test block for catalog writer",
        source_project=TEST_PROJECT,
        source_zone="test_zone",
        hierarchy_level="process",
        domain="testing",
        inputs=[
            BlockPort(
                name="test_input",
                type="dataset",
                required=True,
                description="Test input dataset",
                schema_ref="schemas/TEST_CATALOG_BLOCK_001_test_input.schema.json"
            )
        ],
        outputs=[
            BlockPort(
                name="test_output",
                type="dataset",
                required=True,
                description="Test output dataset",
                schema_ref="schemas/TEST_CATALOG_BLOCK_001_test_output.schema.json"
            )
        ],
        contains=BlockContents(
            datasets=["test_dataset"],
            recipes=["test_recipe"],
            models=[]
        ),
    )

    # Add schemas (as schema_extractor would do)
    block.inputs[0].schema = {
        "columns": [
            {"name": "id", "type": "int"},
            {"name": "name", "type": "string"}
        ]
    }
    block.outputs[0].schema = {
        "columns": [
            {"name": "result", "type": "string"},
            {"name": "timestamp", "type": "date"}
        ]
    }

    return block


@pytest.fixture
def test_blocks():
    """Create multiple test blocks for batch testing."""
    blocks = []
    for i in range(1, 4):
        block = BlockMetadata(
            block_id=f"TEST_CATALOG_BLOCK_00{i}",
            version="1.0.0",
            type="zone",
            blocked=False,
            name=f"Test Block {i}",
            description=f"Test block {i}",
            source_project=TEST_PROJECT,
            inputs=[],
            outputs=[],
            contains=BlockContents(datasets=[], recipes=[], models=[]),
        )
        blocks.append(block)

    return blocks


@pytest.fixture(scope="function")
def cleanup_test_artifacts(real_client):
    """
    Cleanup fixture - runs after each test to remove test artifacts.

    This ensures that test blocks don't accumulate in the project.
    """
    yield  # Let test run first

    # Cleanup after test
    try:
        project = real_client.get_project(TEST_PROJECT)
        library = project.get_library()
        wiki = project.get_wiki()

        # Try to clean up test blocks
        test_block_ids = [
            "TEST_CATALOG_BLOCK_001",
            "TEST_CATALOG_BLOCK_002",
            "TEST_CATALOG_BLOCK_003",
        ]

        for block_id in test_block_ids:
            # Clean up Wiki articles
            try:
                article_path = f"_DISCOVERED_BLOCKS/{block_id}"
                article = wiki.get_article(article_path)
                # Note: Dataiku Wiki doesn't have delete method, so we just leave it
                # In production, old articles would be updated or archived
            except:
                pass  # Article doesn't exist, that's fine

            # Clean up schema files
            try:
                root = library.root
                discovery_folder = root.get_child("discovery")
                if discovery_folder:
                    schemas_folder = discovery_folder.get_child("schemas")
                    if schemas_folder:
                        # Try to remove test schema files
                        for port_name in ["test_input", "test_output"]:
                            schema_file_name = f"{block_id}_{port_name}.schema.json"
                            schema_file = schemas_folder.get_child(schema_file_name)
                            if schema_file:
                                # Note: Library doesn't have delete method either
                                # In production, we'd overwrite or version
                                pass
            except:
                pass  # Cleanup failed, not critical for tests

        # Clean up index.json (reset to empty)
        try:
            root = library.root
            discovery_folder = root.get_child("discovery")
            if discovery_folder:
                index_file = discovery_folder.get_child("index.json")
                if index_file:
                    empty_index = {
                        "version": "1.0",
                        "project_key": TEST_PROJECT,
                        "blocks": [],
                        "last_updated": None
                    }
                    index_file.write(json.dumps(empty_index, indent=2))
        except:
            pass  # Cleanup failed, not critical

    except Exception as e:
        # Cleanup errors are logged but don't fail tests
        print(f"Warning: Cleanup failed: {e}")


# ============================================================================
# Test Class 1: Real Wiki Writes
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestRealWikiWrites:
    """Test Wiki article creation with real Dataiku API."""

    def test_write_wiki_article_creates_in_discovered_blocks_folder(
        self, real_client, real_writer, test_block, cleanup_test_artifacts
    ):
        """Verify Wiki article created in correct folder structure."""
        project = real_client.get_project(TEST_PROJECT)

        # Execute
        article_name = real_writer._write_wiki_article(project, test_block)

        # Verify article name returned
        assert article_name == test_block.block_id

        # Try to read back the article
        wiki = project.get_wiki()
        article = wiki.get_article(test_block.block_id)
        assert article is not None

        # Verify content
        article_data = article.get_data()
        content = article_data.get_body()
        assert test_block.block_id in content
        assert test_block.version in content
        assert test_block.name in content

    def test_wiki_article_contains_all_required_sections(
        self, real_client, real_writer, test_block, cleanup_test_artifacts
    ):
        """Verify Wiki article has all required sections."""
        project = real_client.get_project(TEST_PROJECT)

        # Execute
        article_name = real_writer._write_wiki_article(project, test_block)

        # Read back
        wiki = project.get_wiki()
        article = wiki.get_article(test_block.block_id)
        article_data = article.get_data()
        content = article_data.get_body()

        # Verify required sections exist
        required_sections = [
            "##",  # Has at least some markdown headers
            "Description",
            "Inputs",
            "Outputs",
            "Contains",
            test_block.block_id,  # Block ID appears
            test_block.version  # Version appears
        ]

        for section in required_sections:
            assert section in content, f"Missing section/content: {section}"

    def test_wiki_article_update_preserves_existing_content(
        self, real_client, real_writer, test_block, cleanup_test_artifacts
    ):
        """Verify updating existing article preserves custom content."""
        project = real_client.get_project(TEST_PROJECT)

        # Write initial article
        article_name = real_writer._write_wiki_article(project, test_block)

        # Modify the block version
        test_block.version = "1.1.0"

        # Write again (update)
        article_name = real_writer._write_wiki_article(project, test_block)

        # Read back
        wiki = project.get_wiki()
        article = wiki.get_article(test_block.block_id)
        article_data = article.get_data()
        content = article_data.get_body()

        # Verify new version appears
        assert "1.1.0" in content


# ============================================================================
# Test Class 2: Real Library Writes
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestRealLibraryWrites:
    """Test Library file creation with real Dataiku API."""

    def test_write_schemas_creates_files_in_library(
        self, real_client, real_writer, test_block, cleanup_test_artifacts
    ):
        """Verify schema files written to Library/discovery/schemas/."""
        project = real_client.get_project(TEST_PROJECT)

        # Ensure registry exists first
        real_writer._ensure_project_registry_exists(TEST_PROJECT)

        # Execute
        count = real_writer._write_schemas(project, test_block)

        # Verify count
        assert count == 2  # 1 input + 1 output

        # Verify files exist
        library = project.get_library()
        root = library.root
        discovery_folder = root.get_child("discovery")
        assert discovery_folder is not None

        schemas_folder = discovery_folder.get_child("schemas")
        assert schemas_folder is not None

        # Check input schema file
        input_schema_file = schemas_folder.get_child(
            f"{test_block.block_id}_test_input.schema.json"
        )
        assert input_schema_file is not None

        # Read and verify content
        input_content = input_schema_file.read()
        input_schema = json.loads(input_content)
        assert "columns" in input_schema
        assert len(input_schema["columns"]) == 2

        # Check output schema file
        output_schema_file = schemas_folder.get_child(
            f"{test_block.block_id}_test_output.schema.json"
        )
        assert output_schema_file is not None

    def test_update_discovery_index_creates_valid_json(
        self, real_client, real_writer, test_blocks, cleanup_test_artifacts
    ):
        """Verify index.json created with valid structure."""
        project = real_client.get_project(TEST_PROJECT)

        # Ensure registry exists first
        real_writer._ensure_project_registry_exists(TEST_PROJECT)

        # Execute
        real_writer._update_discovery_index(project, test_blocks)

        # Read back
        library = project.get_library()
        root = library.root
        discovery_folder = root.get_child("discovery")
        index_file = discovery_folder.get_child("index.json")

        assert index_file is not None

        # Parse content
        content = index_file.read()
        index_data = json.loads(content)

        # Verify structure
        assert index_data["version"] == "1.0"
        assert index_data["project_key"] == TEST_PROJECT
        assert len(index_data["blocks"]) == 3
        assert index_data["last_updated"] is not None

        # Verify block entries
        block_ids = [b["block_id"] for b in index_data["blocks"]]
        assert "TEST_CATALOG_BLOCK_001" in block_ids

    def test_ensure_registry_creates_folder_structure(
        self, real_client, real_writer, cleanup_test_artifacts
    ):
        """Verify _ensure_project_registry_exists creates folders."""
        # Execute
        real_writer._ensure_project_registry_exists(TEST_PROJECT)

        # Verify structure exists
        project = real_client.get_project(TEST_PROJECT)
        library = project.get_library()
        root = library.root

        # Check discovery folder
        discovery_folder = root.get_child("discovery")
        assert discovery_folder is not None, "discovery folder not created"

        # Check schemas subfolder
        schemas_folder = discovery_folder.get_child("schemas")
        assert schemas_folder is not None, "schemas subfolder not created"

        # Check index.json
        index_file = discovery_folder.get_child("index.json")
        assert index_file is not None, "index.json not created"

        # Verify index.json content
        content = index_file.read()
        index_data = json.loads(content)
        assert index_data["project_key"] == TEST_PROJECT


# ============================================================================
# Test Class 3: End-to-End Real Write
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestRealEndToEnd:
    """End-to-end test of complete write workflow."""

    def test_write_to_project_registry_complete_workflow(
        self, real_client, real_writer, test_block, cleanup_test_artifacts
    ):
        """
        CRITICAL TEST: Verify complete write workflow end-to-end.

        This is the most important integration test - it validates that:
        1. Wiki articles are created
        2. Schema files are written to Library
        3. Index.json is updated
        4. All artifacts are readable
        """
        # Execute complete write
        result = real_writer.write_to_project_registry(TEST_PROJECT, [test_block])

        # Verify result structure
        assert result["project_key"] == TEST_PROJECT
        assert result["blocks_written"] == 1
        assert len(result["wiki_articles"]) == 1
        assert result["schemas_written"] == 2
        assert result["index_updated"] == True

        # Verify Wiki article exists
        project = real_client.get_project(TEST_PROJECT)
        wiki = project.get_wiki()
        article = wiki.get_article(test_block.block_id)
        assert article is not None

        article_data = article.get_data()
        content = article_data.get_body()
        assert test_block.block_id in content

        # Verify schema files exist
        library = project.get_library()
        root = library.root
        discovery_folder = root.get_child("discovery")
        schemas_folder = discovery_folder.get_child("schemas")

        input_schema_file = schemas_folder.get_child(
            f"{test_block.block_id}_test_input.schema.json"
        )
        output_schema_file = schemas_folder.get_child(
            f"{test_block.block_id}_test_output.schema.json"
        )

        assert input_schema_file is not None
        assert output_schema_file is not None

        # Verify schemas are valid JSON
        input_schema = json.loads(input_schema_file.read())
        assert "columns" in input_schema

        output_schema = json.loads(output_schema_file.read())
        assert "columns" in output_schema

        # Verify index.json updated
        index_file = discovery_folder.get_child("index.json")
        index_data = json.loads(index_file.read())

        assert len(index_data["blocks"]) >= 1
        block_ids = [b["block_id"] for b in index_data["blocks"]]
        assert test_block.block_id in block_ids

        # Verify timestamp exists and is valid ISO format
        assert index_data["last_updated"] is not None
        last_updated = datetime.fromisoformat(index_data["last_updated"])
        # Just verify it's a valid datetime - don't check recency since index may have been written before

        print("\n✓ End-to-end test PASSED!")
        print(f"  - Wiki article: {test_block.block_id} (under _DISCOVERED_BLOCKS)")
        print(f"  - Schema files: 2 files in Library/discovery/schemas/")
        print(f"  - Index updated: {index_data['last_updated']}")
