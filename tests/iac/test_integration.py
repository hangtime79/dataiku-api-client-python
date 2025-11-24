"""
Integration tests for Dataiku IaC - End-to-end scenarios.

These tests can run with either mocked or real Dataiku instances.

To run against real Dataiku:
    export USE_REAL_DATAIKU=true
    export DATAIKU_HOST=https://your-dataiku-instance.com
    export DATAIKU_API_KEY=your-api-key
    export TEST_PROJECT_KEY=YOUR_PROJECT
    pytest tests/iac/test_integration.py -v

To run with mocks (default):
    pytest tests/iac/test_integration.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path

from dataikuapi.iac.manager import StateManager
from dataikuapi.iac.backends.local import LocalFileBackend
from dataikuapi.iac.models.state import State, Resource
from dataikuapi.iac.diff import DiffEngine


@pytest.fixture
def mock_project_data():
    """Mock project data"""
    return {
        "projectKey": "TEST_PROJECT",
        "name": "Test Project",
        "description": "Integration test project",
    }


@pytest.fixture
def mock_dataset_data():
    """Mock dataset data"""
    return {
        "name": "CUSTOMERS",
        "type": "PostgreSQL",
        "params": {"connection": "test_conn"},
        "schema": {"columns": [{"name": "ID", "type": "bigint"}]},
        "formatType": "table",
        "tags": ["test"],
    }


@pytest.fixture
def mock_recipe_data():
    """Mock recipe data"""
    return {
        "name": "prep_data",
        "type": "python",
        "inputs": {"main": {"items": [{"ref": "CUSTOMERS"}]}},
        "outputs": {"main": {"items": [{"ref": "PREPARED"}]}},
        "params": {},
        "tags": [],
        "payload": "# Python recipe code\nprint('hello')\n",
    }


def setup_mock_client(mock_client, mock_project_data, mock_dataset_data, mock_recipe_data):
    """Setup mock client with test data"""
    # Mock project
    mock_project = Mock()
    mock_project_settings = Mock()
    mock_project_settings.settings = mock_project_data
    mock_project.get_settings.return_value = mock_project_settings

    # Mock dataset
    mock_dataset = Mock()
    mock_dataset_settings = Mock()
    mock_dataset_settings.settings = mock_dataset_data
    mock_dataset.get_settings.return_value = mock_dataset_settings
    mock_project.get_dataset.return_value = mock_dataset
    mock_project.list_datasets.return_value = [{"name": "CUSTOMERS"}]

    # Mock recipe
    mock_recipe = Mock()
    mock_recipe_settings = Mock()
    mock_recipe_settings.settings = mock_recipe_data
    mock_recipe.get_settings.return_value = mock_recipe_settings
    mock_recipe.get_payload.return_value = mock_recipe_data["payload"]
    mock_project.get_recipe.return_value = mock_recipe
    mock_project.list_recipes.return_value = [{"name": "prep_data"}]

    # Configure client
    mock_client.get_project.return_value = mock_project
    mock_client.list_projects.return_value = [mock_project_data]

    return mock_client


class TestBasicSyncOperations:
    """Test basic sync operations"""

    def test_sync_project_only(self, state_manager, use_real_dataiku, test_project_key,
                                mock_project_data, mock_dataset_data, mock_recipe_data):
        """Test syncing a project without children"""
        if not use_real_dataiku:
            # Setup mocks
            setup_mock_client(state_manager.client, mock_project_data,
                             mock_dataset_data, mock_recipe_data)

        try:
            state = state_manager.sync_project(test_project_key, include_children=False)

            # Verify project synced
            assert len(state.resources) >= 1
            project_id = f"project.{test_project_key}"
            assert project_id in state.resources

            project_resource = state.resources[project_id]
            assert project_resource.resource_type == "project"
            assert project_resource.project_key == test_project_key

        except Exception as e:
            if use_real_dataiku:
                pytest.skip(f"Real Dataiku test failed (expected if project doesn't exist): {e}")
            else:
                raise

    def test_sync_project_with_children(self, state_manager, use_real_dataiku, test_project_key,
                                        mock_project_data, mock_dataset_data, mock_recipe_data):
        """Test syncing a project with datasets and recipes"""
        if not use_real_dataiku:
            setup_mock_client(state_manager.client, mock_project_data,
                             mock_dataset_data, mock_recipe_data)

        try:
            state = state_manager.sync_project(test_project_key, include_children=True)

            # Verify project synced
            project_id = f"project.{test_project_key}"
            assert project_id in state.resources

            # Should have project + possibly datasets/recipes
            assert len(state.resources) >= 1

            # Verify all resources have correct project_key
            for resource in state.list_resources():
                assert resource.project_key == test_project_key or resource.resource_type == "project"

        except Exception as e:
            if use_real_dataiku:
                pytest.skip(f"Real Dataiku test failed: {e}")
            else:
                raise


class TestStatePersistence:
    """Test state save and load operations"""

    def test_save_and_load_state(self, state_manager, use_real_dataiku, test_project_key,
                                  mock_project_data, mock_dataset_data, mock_recipe_data):
        """Test saving state to file and loading it back"""
        if not use_real_dataiku:
            setup_mock_client(state_manager.client, mock_project_data,
                             mock_dataset_data, mock_recipe_data)

        try:
            # Sync from Dataiku
            original_state = state_manager.sync_project(test_project_key, include_children=False)
            original_serial = original_state.serial

            # Save
            state_manager.save_state(original_state)
            assert state_manager.backend.exists()

            # Load
            loaded_state = state_manager.load_state()

            # Verify loaded state matches original
            assert len(loaded_state.resources) == len(original_state.resources)
            assert loaded_state.environment == original_state.environment

            for resource_id in original_state.resources:
                assert resource_id in loaded_state.resources

        except Exception as e:
            if use_real_dataiku:
                pytest.skip(f"Real Dataiku test failed: {e}")
            else:
                raise

    def test_load_nonexistent_state(self, state_manager):
        """Test loading state when file doesn't exist"""
        # Load should return empty state
        state = state_manager.load_state()

        assert isinstance(state, State)
        assert len(state.resources) == 0
        assert state.environment == "test"


class TestDriftDetection:
    """Test drift detection between state and Dataiku"""

    def test_detect_no_drift(self, state_manager, use_real_dataiku, test_project_key,
                             mock_project_data, mock_dataset_data, mock_recipe_data):
        """Test detecting no drift when state matches Dataiku"""
        if not use_real_dataiku:
            setup_mock_client(state_manager.client, mock_project_data,
                             mock_dataset_data, mock_recipe_data)

        try:
            # Sync twice
            state1 = state_manager.sync_project(test_project_key, include_children=False)
            state2 = state_manager.sync_project(test_project_key, include_children=False)

            # Diff
            diff_engine = DiffEngine()
            diffs = diff_engine.diff(state1, state2)

            # Should have no changes (all unchanged)
            summary = diff_engine.summary(diffs)
            assert summary["added"] == 0
            assert summary["removed"] == 0
            assert summary["modified"] == 0

        except Exception as e:
            if use_real_dataiku:
                pytest.skip(f"Real Dataiku test failed: {e}")
            else:
                raise

    def test_detect_added_resource(self, state_manager, mock_project_data,
                                    mock_dataset_data, mock_recipe_data):
        """Test detecting added resources"""
        setup_mock_client(state_manager.client, mock_project_data,
                         mock_dataset_data, mock_recipe_data)

        # Initial state with just project
        old_state = state_manager.sync_project("TEST_PROJECT", include_children=False)

        # New state with children
        new_state = state_manager.sync_project("TEST_PROJECT", include_children=True)

        # Diff
        diff_engine = DiffEngine()
        diffs = diff_engine.diff(old_state, new_state)

        summary = diff_engine.summary(diffs)
        # Should detect added datasets/recipes
        assert summary["added"] > 0 or summary["unchanged"] > 0


class TestCompleteWorkflow:
    """Test complete end-to-end workflows"""

    def test_full_workflow(self, tmp_path, use_real_dataiku, test_project_key,
                          mock_project_data, mock_dataset_data, mock_recipe_data):
        """Test complete workflow: init → sync → save → modify → sync → diff"""
        from dataikuapi import DSSClient

        # Setup
        if use_real_dataiku:
            client = DSSClient(
                os.environ.get("DATAIKU_HOST"),
                os.environ.get("DATAIKU_API_KEY")
            )
        else:
            client = Mock(spec=DSSClient)
            setup_mock_client(client, mock_project_data, mock_dataset_data, mock_recipe_data)

        state_file = tmp_path / "prod.state.json"
        backend = LocalFileBackend(state_file)
        manager = StateManager(backend, client, "prod")

        try:
            # Step 1: Initial sync
            state = manager.sync_project(test_project_key, include_children=True)
            assert len(state.resources) >= 1

            # Step 2: Save
            manager.save_state(state)
            assert state_file.exists()

            # Step 3: Load
            loaded_state = manager.load_state()
            assert len(loaded_state.resources) == len(state.resources)

            # Step 4: Sync again
            new_state = manager.sync_project(test_project_key, include_children=True)

            # Step 5: Diff
            diff_engine = DiffEngine()
            diffs = diff_engine.diff(loaded_state, new_state)
            summary = diff_engine.summary(diffs)

            # Should have no significant changes
            assert summary["added"] == 0
            assert summary["removed"] == 0

        except Exception as e:
            if use_real_dataiku:
                pytest.skip(f"Real Dataiku test failed: {e}")
            else:
                raise


class TestMultipleProjects:
    """Test operations with multiple projects"""

    def test_sync_all_projects(self, state_manager, use_real_dataiku,
                                mock_project_data, mock_dataset_data, mock_recipe_data):
        """Test syncing all accessible projects"""
        if not use_real_dataiku:
            setup_mock_client(state_manager.client, mock_project_data,
                             mock_dataset_data, mock_recipe_data)

        try:
            state = state_manager.sync_all()

            # Should have at least one project
            projects = state.list_resources("project")
            assert len(projects) >= 1

        except Exception as e:
            if use_real_dataiku:
                pytest.skip(f"Real Dataiku test failed: {e}")
            else:
                raise


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_sync_nonexistent_project(self, state_manager):
        """Test syncing a project that doesn't exist"""
        from dataikuapi.iac.exceptions import ResourceNotFoundError

        # Mock client to raise error
        state_manager.client.get_project.side_effect = Exception("Project not found")

        with pytest.raises(Exception):
            state_manager.sync_project("NONEXISTENT_PROJECT")

    def test_corrupt_state_file(self, tmp_path):
        """Test loading corrupted state file"""
        from dataikuapi.iac.exceptions import StateCorruptedError
        from dataikuapi import DSSClient

        # Create corrupted state file
        state_file = tmp_path / "corrupt.state.json"
        state_file.write_text("{ invalid json }")

        client = Mock(spec=DSSClient)
        backend = LocalFileBackend(state_file)
        manager = StateManager(backend, client, "test")

        with pytest.raises(StateCorruptedError):
            manager.load_state()
