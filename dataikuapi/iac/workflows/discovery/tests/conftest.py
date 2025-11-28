"""Shared test fixtures for Discovery Agent tests."""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime


@pytest.fixture
def mock_dss_client():
    """
    Mock DSSClient for testing.

    Returns:
        Mock: Configured mock DSSClient
    """
    client = Mock()
    client.host = "https://dss.example.com"
    return client


@pytest.fixture
def mock_project(mock_zone, sample_flow_graph):
    """
    Mock DSSProject for testing.

    Returns:
        Mock: Configured mock project with flow
    """
    project = Mock()
    project.project_key = "TEST_PROJECT"
    project.get_metadata.return_value = {
        "name": "Test Project",
        "description": "Test project for discovery",
    }

    # Mock flow with comprehensive setup
    flow = Mock()
    flow.list_zones.return_value = [
        {"name": "test_zone"},
        {"name": "zone2"},
    ]
    flow.get_zone.return_value = mock_zone
    flow.get_graph.return_value = sample_flow_graph
    project.get_flow.return_value = flow

    # Mock dataset operations
    dataset = Mock()
    dataset.name = "TEST_DATASET"
    project.get_dataset.return_value = dataset

    return project


@pytest.fixture
def mock_zone():
    """
    Mock Flow Zone for testing.

    Returns:
        Mock: Configured mock zone
    """
    zone = Mock()
    zone.id = "test_zone"
    zone.name = "Test Zone"

    # Mock zone items
    zone.items = [
        {"type": "DATASET", "id": "ds1"},
        {"type": "DATASET", "id": "ds2"},
        {"type": "RECIPE", "id": "recipe1"},
    ]
    zone.get_items.return_value = zone.items

    return zone


@pytest.fixture
def mock_dataset():
    """
    Mock Dataset for testing.

    Returns:
        Mock: Configured mock dataset
    """
    dataset = Mock()
    dataset.name = "TEST_DATASET"
    dataset.type = "Snowflake"

    # Mock settings
    settings = Mock()
    settings.get_raw.return_value = {
        "type": "Snowflake",
        "params": {
            "connection": "WAREHOUSE",
            "table": "TEST_TABLE",
        },
    }
    dataset.get_settings.return_value = settings

    # Mock schema
    dataset.get_schema.return_value = {
        "columns": [
            {"name": "ID", "type": "bigint"},
            {"name": "VALUE", "type": "double"},
        ]
    }

    return dataset


@pytest.fixture
def mock_recipe():
    """
    Mock Recipe for testing.

    Returns:
        Mock: Configured mock recipe
    """
    recipe = Mock()
    recipe.name = "test_recipe"
    recipe.type = "python"

    # Mock settings
    settings = Mock()
    settings.get_raw.return_value = {
        "type": "python",
        "inputs": {"main": {"items": [{"ref": "input_ds"}]}},
        "outputs": {"main": {"items": [{"ref": "output_ds"}]}},
    }
    recipe.get_settings.return_value = settings

    return recipe


@pytest.fixture
def sample_block_metadata():
    """
    Sample BlockMetadata for testing.

    Returns:
        dict: Sample block metadata as dict
    """
    return {
        "block_id": "TEST_BLOCK",
        "version": "1.0.0",
        "type": "zone",
        "blocked": False,
        "name": "Test Block",
        "description": "A test block for unit testing",
        "hierarchy_level": "equipment",
        "domain": "testing",
        "tags": ["test", "sample"],
        "source_project": "TEST_PROJECT",
        "source_zone": "test_zone",
        "inputs": [
            {
                "name": "INPUT_DATA",
                "type": "dataset",
                "required": True,
                "description": "Test input",
            }
        ],
        "outputs": [
            {
                "name": "OUTPUT_DATA",
                "type": "dataset",
                "description": "Test output",
            }
        ],
        "contains": {
            "datasets": ["INTERMEDIATE_DS"],
            "recipes": ["process_recipe"],
            "models": [],
        },
        "dependencies": {
            "python_packages": ["pandas>=1.0"],
            "connections": ["Snowflake"],
        },
        "created_at": "2024-01-15T10:00:00Z",
        "created_by": "test_user",
    }


@pytest.fixture
def sample_flow_graph():
    """
    Sample flow dependency graph for testing.

    Returns:
        dict: Flow graph with dataset dependencies
    """
    return {
        "nodes": {
            "INPUT_DATA": {"type": "dataset", "zone": "test_zone"},
            "INTERMEDIATE_DS": {"type": "dataset", "zone": "test_zone"},
            "OUTPUT_DATA": {"type": "dataset", "zone": "test_zone"},
            "process_recipe": {"type": "recipe", "zone": "test_zone"},
        },
        "edges": [
            {"from": "INPUT_DATA", "to": "process_recipe"},
            {"from": "process_recipe", "to": "INTERMEDIATE_DS"},
            {"from": "INTERMEDIATE_DS", "to": "OUTPUT_DATA"},
        ],
    }


@pytest.fixture
def mock_registry_project():
    """
    Mock BLOCKS_REGISTRY project for testing.

    Returns:
        Mock: Configured mock registry project
    """
    project = Mock()
    project.project_key = "BLOCKS_REGISTRY"

    # Mock wiki
    wiki = Mock()
    project.get_wiki.return_value = wiki

    # Mock library
    library = Mock()
    project.get_library.return_value = library

    # Mock library files
    index_file = Mock()
    index_file.read.return_value = '{"blocks": []}'
    library.get_file.return_value = index_file

    return project
