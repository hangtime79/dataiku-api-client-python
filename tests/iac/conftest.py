"""
Pytest fixtures for integration tests.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock
from dataikuapi import DSSClient
from dataikuapi.iac.backends.local import LocalFileBackend
from dataikuapi.iac.manager import StateManager


@pytest.fixture
def dataiku_host():
    """Dataiku host URL from environment or default"""
    return os.environ.get("DATAIKU_HOST", "https://dataiku-dev.company.com")


@pytest.fixture
def dataiku_api_key():
    """Dataiku API key from environment or mock"""
    return os.environ.get("DATAIKU_API_KEY", "test-api-key")


@pytest.fixture
def use_real_dataiku():
    """Whether to use real Dataiku instance (from environment)"""
    return os.environ.get("USE_REAL_DATAIKU", "false").lower() == "true"


@pytest.fixture
def dataiku_client(dataiku_host, dataiku_api_key, use_real_dataiku):
    """Dataiku API client - real or mocked"""
    if use_real_dataiku:
        return DSSClient(dataiku_host, dataiku_api_key)
    else:
        # Return mock client
        return Mock(spec=DSSClient)


@pytest.fixture
def state_manager(dataiku_client, tmp_path):
    """StateManager with temporary backend"""
    state_file = tmp_path / "test.state.json"
    backend = LocalFileBackend(state_file)
    return StateManager(backend, dataiku_client, "test")


@pytest.fixture
def test_project_key():
    """Test project key from environment or default"""
    return os.environ.get("TEST_PROJECT_KEY", "TEST_PROJECT")
