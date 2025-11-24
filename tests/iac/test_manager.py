"""
Tests for StateManager - Main orchestrator
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from dataikuapi.iac.manager import StateManager
from dataikuapi.iac.models.state import State, Resource, make_resource_id
from dataikuapi.iac.backends.base import StateBackend
from dataikuapi.iac.exceptions import ResourceNotFoundError


@pytest.fixture
def mock_client():
    """Mock DSSClient"""
    return Mock()


@pytest.fixture
def mock_backend():
    """Mock StateBackend"""
    backend = Mock(spec=StateBackend)
    backend.exists.return_value = False
    return backend


@pytest.fixture
def manager(mock_backend, mock_client):
    """StateManager fixture"""
    return StateManager(mock_backend, mock_client, "test")


class TestStateManagerInit:
    """Test StateManager initialization"""

    def test_init_sets_properties(self, mock_backend, mock_client):
        """StateManager initializes with correct properties"""
        manager = StateManager(mock_backend, mock_client, "prod")

        assert manager.backend == mock_backend
        assert manager.client == mock_client
        assert manager.environment == "prod"
        assert manager.project_sync is not None
        assert manager.dataset_sync is not None
        assert manager.recipe_sync is not None

    def test_init_creates_sync_registry(self, manager):
        """StateManager creates sync registry"""
        assert "project" in manager._sync_registry
        assert "dataset" in manager._sync_registry
        assert "recipe" in manager._sync_registry


class TestLoadState:
    """Test load_state method"""

    def test_load_state_when_exists(self, manager, mock_backend):
        """load_state returns state from backend when it exists"""
        mock_backend.exists.return_value = True
        expected_state = State(environment="test", serial=5)
        mock_backend.load.return_value = expected_state

        state = manager.load_state()

        assert state == expected_state
        mock_backend.exists.assert_called_once()
        mock_backend.load.assert_called_once()

    def test_load_state_when_not_exists(self, manager, mock_backend):
        """load_state returns empty state when backend doesn't exist"""
        mock_backend.exists.return_value = False

        state = manager.load_state()

        assert isinstance(state, State)
        assert len(state.resources) == 0
        assert state.environment == "test"
        mock_backend.exists.assert_called_once()
        mock_backend.load.assert_not_called()


class TestSaveState:
    """Test save_state method"""

    def test_save_state(self, manager, mock_backend):
        """save_state persists to backend"""
        state = State(environment="dev")

        manager.save_state(state)

        mock_backend.save.assert_called_once()
        saved_state = mock_backend.save.call_args[0][0]
        assert saved_state.environment == "test"  # Manager's environment

    def test_save_state_updates_environment(self, manager, mock_backend):
        """save_state updates state environment"""
        state = State(environment="wrong")

        manager.save_state(state)

        saved_state = mock_backend.save.call_args[0][0]
        assert saved_state.environment == "test"


class TestSyncResource:
    """Test sync_resource method"""

    def test_sync_resource_project(self, manager):
        """sync_resource delegates to project sync"""
        expected_resource = Resource("project", "project.TEST", {})
        manager.project_sync.fetch = Mock(return_value=expected_resource)

        resource = manager.sync_resource("project.TEST")

        assert resource == expected_resource
        manager.project_sync.fetch.assert_called_once_with("project.TEST")

    def test_sync_resource_dataset(self, manager):
        """sync_resource delegates to dataset sync"""
        expected_resource = Resource("dataset", "dataset.TEST.CUSTOMERS", {})
        manager.dataset_sync.fetch = Mock(return_value=expected_resource)

        resource = manager.sync_resource("dataset.TEST.CUSTOMERS")

        assert resource == expected_resource
        manager.dataset_sync.fetch.assert_called_once_with("dataset.TEST.CUSTOMERS")

    def test_sync_resource_recipe(self, manager):
        """sync_resource delegates to recipe sync"""
        expected_resource = Resource("recipe", "recipe.TEST.prep", {})
        manager.recipe_sync.fetch = Mock(return_value=expected_resource)

        resource = manager.sync_resource("recipe.TEST.prep")

        assert resource == expected_resource
        manager.recipe_sync.fetch.assert_called_once_with("recipe.TEST.prep")

    def test_sync_resource_unknown_type(self, manager):
        """sync_resource raises ValueError for unknown resource type"""
        with pytest.raises(ValueError, match="Unknown resource type"):
            manager.sync_resource("unknown.TEST.something")


class TestSyncProject:
    """Test sync_project method"""

    def test_sync_project_without_children(self, manager):
        """sync_project syncs only project when include_children=False"""
        project_resource = Resource("project", "project.TEST", {"name": "Test"})
        manager.project_sync.fetch = Mock(return_value=project_resource)

        state = manager.sync_project("TEST", include_children=False)

        assert len(state.resources) == 1
        assert "project.TEST" in state.resources
        manager.project_sync.fetch.assert_called_once_with("project.TEST")

    def test_sync_project_with_children(self, manager):
        """sync_project includes datasets and recipes when include_children=True"""
        project_resource = Resource("project", "project.TEST", {"name": "Test"})
        dataset_resource = Resource("dataset", "dataset.TEST.CUSTOMERS", {})
        recipe_resource = Resource("recipe", "recipe.TEST.prep", {})

        manager.project_sync.fetch = Mock(return_value=project_resource)
        manager.dataset_sync.list_all = Mock(return_value=[dataset_resource])
        manager.recipe_sync.list_all = Mock(return_value=[recipe_resource])

        state = manager.sync_project("TEST", include_children=True)

        assert len(state.resources) == 3
        assert "project.TEST" in state.resources
        assert "dataset.TEST.CUSTOMERS" in state.resources
        assert "recipe.TEST.prep" in state.resources

        manager.project_sync.fetch.assert_called_once_with("project.TEST")
        manager.dataset_sync.list_all.assert_called_once_with("TEST")
        manager.recipe_sync.list_all.assert_called_once_with("TEST")

    def test_sync_project_continues_on_child_failures(self, manager):
        """sync_project continues if datasets or recipes fail"""
        project_resource = Resource("project", "project.TEST", {"name": "Test"})
        manager.project_sync.fetch = Mock(return_value=project_resource)
        manager.dataset_sync.list_all = Mock(side_effect=Exception("Dataset error"))
        manager.recipe_sync.list_all = Mock(side_effect=Exception("Recipe error"))

        state = manager.sync_project("TEST", include_children=True)

        # Should still have project even if children fail
        assert len(state.resources) == 1
        assert "project.TEST" in state.resources

    def test_sync_project_sets_environment(self, manager):
        """sync_project creates state with correct environment"""
        project_resource = Resource("project", "project.TEST", {"name": "Test"})
        manager.project_sync.fetch = Mock(return_value=project_resource)

        state = manager.sync_project("TEST", include_children=False)

        assert state.environment == "test"


class TestSyncAll:
    """Test sync_all method"""

    def test_sync_all(self, manager):
        """sync_all syncs all projects and their resources"""
        project1 = Resource("project", "project.PROJECT1", {"name": "Project 1"})
        project2 = Resource("project", "project.PROJECT2", {"name": "Project 2"})
        dataset1 = Resource("dataset", "dataset.PROJECT1.DATA", {})
        recipe1 = Resource("recipe", "recipe.PROJECT1.PREP", {})

        manager.project_sync.list_all = Mock(return_value=[project1, project2])
        manager.dataset_sync.list_all = Mock(side_effect=[
            [dataset1],  # For PROJECT1
            [],          # For PROJECT2
        ])
        manager.recipe_sync.list_all = Mock(side_effect=[
            [recipe1],  # For PROJECT1
            [],         # For PROJECT2
        ])

        state = manager.sync_all()

        assert len(state.resources) == 4
        assert "project.PROJECT1" in state.resources
        assert "project.PROJECT2" in state.resources
        assert "dataset.PROJECT1.DATA" in state.resources
        assert "recipe.PROJECT1.PREP" in state.resources

    def test_sync_all_continues_on_failures(self, manager):
        """sync_all continues syncing even if some projects fail"""
        project1 = Resource("project", "project.PROJECT1", {"name": "Project 1"})
        project2 = Resource("project", "project.PROJECT2", {"name": "Project 2"})

        manager.project_sync.list_all = Mock(return_value=[project1, project2])
        manager.dataset_sync.list_all = Mock(side_effect=Exception("Dataset error"))
        manager.recipe_sync.list_all = Mock(side_effect=Exception("Recipe error"))

        state = manager.sync_all()

        # Should have both projects even if children fail
        assert len(state.resources) == 2
        assert "project.PROJECT1" in state.resources
        assert "project.PROJECT2" in state.resources


class TestIntegration:
    """Integration tests with real objects"""

    def test_full_workflow(self, mock_client, tmp_path):
        """Test complete workflow: sync → save → load"""
        from dataikuapi.iac.backends.local import LocalFileBackend

        # Setup
        state_file = tmp_path / "test.state.json"
        backend = LocalFileBackend(state_file)
        manager = StateManager(backend, mock_client, "test")

        # Mock project sync
        project_resource = Resource("project", "project.TEST", {"name": "Test"})
        manager.project_sync.fetch = Mock(return_value=project_resource)
        manager.dataset_sync.list_all = Mock(return_value=[])
        manager.recipe_sync.list_all = Mock(return_value=[])

        # Sync project
        state = manager.sync_project("TEST", include_children=True)
        assert len(state.resources) == 1

        # Save
        manager.save_state(state)
        assert state_file.exists()

        # Load
        loaded_state = manager.load_state()
        assert len(loaded_state.resources) == 1
        assert "project.TEST" in loaded_state.resources
