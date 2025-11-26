"""
Pytest fixtures for IaC test suite.

Provides fixtures for both unit tests (mock-based) and integration tests (real Dataiku).
"""

import pytest
import os
import json
from pathlib import Path
from unittest.mock import Mock
from datetime import datetime
from dataikuapi import DSSClient
from dataikuapi.iac.backends.local import LocalFileBackend
from dataikuapi.iac.manager import StateManager
from dataikuapi.iac.models.state import State, Resource, ResourceMetadata


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def dataiku_host():
    """Dataiku host URL from environment or default (local box)"""
    return os.environ.get("DATAIKU_HOST", "http://172.18.58.26:10000")


@pytest.fixture
def dataiku_api_key():
    """Dataiku API key from environment (None for local execution)"""
    return os.environ.get("DATAIKU_API_KEY", None)


@pytest.fixture
def use_real_dataiku():
    """Whether to use real Dataiku instance (from environment)"""
    return os.environ.get("USE_REAL_DATAIKU", "false").lower() == "true"


@pytest.fixture
def test_project_prefix():
    """Prefix for test projects to avoid collision with real projects"""
    return os.environ.get("TEST_PROJECT_PREFIX", "IAC_TEST_")


@pytest.fixture
def test_project_key(test_project_prefix):
    """Test project key from environment or generated"""
    return os.environ.get("TEST_PROJECT_KEY", f"{test_project_prefix}PROJECT")


# ============================================================================
# Client Fixtures
# ============================================================================

@pytest.fixture
def mock_client():
    """Mock DSSClient for unit tests"""
    return Mock(spec=DSSClient)


@pytest.fixture
def real_client(dataiku_host, dataiku_api_key):
    """Real DSSClient for integration tests"""
    # Try to use provided API key, or use empty string for local execution
    api_key = dataiku_api_key if dataiku_api_key else ""
    try:
        return DSSClient(dataiku_host, api_key)
    except Exception as e:
        pytest.skip(f"Could not create DSSClient: {e}. Try setting DATAIKU_API_KEY environment variable.")


@pytest.fixture
def dataiku_client(dataiku_host, dataiku_api_key, use_real_dataiku, mock_client, real_client):
    """Dataiku API client - real or mocked based on USE_REAL_DATAIKU"""
    if use_real_dataiku:
        return real_client
    else:
        return mock_client


# ============================================================================
# State Management Fixtures
# ============================================================================

@pytest.fixture
def state_manager(dataiku_client, tmp_path):
    """StateManager with temporary backend"""
    state_file = tmp_path / "test.state.json"
    backend = LocalFileBackend(state_file)
    return StateManager(backend, dataiku_client, "test")


@pytest.fixture
def empty_state():
    """Empty state for testing"""
    return State(environment="test")


@pytest.fixture
def simple_state():
    """State with a simple project and dataset"""
    state = State(environment="test")

    # Add project
    project = Resource(
        resource_type="project",
        resource_id="project.TEST_PROJECT",
        attributes={
            "projectKey": "TEST_PROJECT",
            "name": "Test Project",
            "description": "A test project"
        },
        metadata=ResourceMetadata(
            deployed_by="test",
            deployed_at=datetime.now()
        )
    )
    state.add_resource(project)

    # Add dataset
    dataset = Resource(
        resource_type="dataset",
        resource_id="dataset.TEST_PROJECT.TEST_DATASET",
        attributes={
            "name": "TEST_DATASET",
            "type": "managed",
            "formatType": "parquet"
        },
        metadata=ResourceMetadata(
            deployed_by="test",
            deployed_at=datetime.now()
        )
    )
    state.add_resource(dataset)

    return state


# ============================================================================
# Fixture File Fixtures
# ============================================================================

@pytest.fixture
def fixtures_dir():
    """Path to test fixtures directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def configs_dir(fixtures_dir):
    """Path to config fixtures directory"""
    return fixtures_dir / "configs"


@pytest.fixture
def states_dir(fixtures_dir):
    """Path to state fixtures directory"""
    return fixtures_dir / "states"


@pytest.fixture
def simple_config_file(configs_dir):
    """Path to simple config fixture"""
    return configs_dir / "simple" / "project.yml"


@pytest.fixture
def realistic_config_file(configs_dir):
    """Path to realistic config fixture"""
    return configs_dir / "realistic" / "customer_analytics.yml"


@pytest.fixture
def complex_config_file(configs_dir):
    """Path to complex config fixture"""
    return configs_dir / "complex" / "ml_pipeline.yml"


# ============================================================================
# Integration Test Helpers
# ============================================================================

@pytest.fixture
def integration_test_marker(request):
    """Check if test is marked as integration test"""
    return request.node.get_closest_marker("integration") is not None


@pytest.fixture
def skip_if_no_real_dataiku(use_real_dataiku, integration_test_marker):
    """Skip integration tests if USE_REAL_DATAIKU is not set"""
    if integration_test_marker and not use_real_dataiku:
        pytest.skip("Integration test requires USE_REAL_DATAIKU=true")


# ============================================================================
# Cleanup Helpers
# ============================================================================

@pytest.fixture
def cleanup_tracker():
    """Track resources created during tests for manual inspection"""
    created_resources = {
        "projects": [],
        "datasets": [],
        "recipes": []
    }

    yield created_resources

    # Print summary of created resources (not auto-deleted)
    if any(created_resources.values()):
        print("\n" + "="*80)
        print("RESOURCES CREATED (left for inspection):")
        print("="*80)
        for resource_type, resources in created_resources.items():
            if resources:
                print(f"\n{resource_type.upper()}:")
                for resource in resources:
                    print(f"  - {resource}")
        print("\nTo clean up manually, delete these resources from Dataiku UI")
        print("="*80)
