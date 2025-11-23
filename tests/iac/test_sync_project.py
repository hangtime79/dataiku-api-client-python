"""
Unit tests for ProjectSync with mocked DSSClient.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from dataikuapi.iac.sync import ProjectSync
from dataikuapi.iac.models import Resource, make_resource_id
from dataikuapi.iac.exceptions import ResourceNotFoundError


class TestProjectSync:
    """Test ProjectSync implementation"""

    @pytest.fixture
    def mock_client(self):
        """Create a mock DSSClient"""
        return Mock()

    @pytest.fixture
    def project_sync(self, mock_client):
        """Create ProjectSync instance with mock client"""
        return ProjectSync(mock_client)

    def test_resource_type(self, project_sync):
        """Test resource_type property returns 'project'"""
        assert project_sync.resource_type == "project"

    def test_fetch_valid_project(self, mock_client, project_sync):
        """Test fetching a valid project"""
        # Setup mock
        mock_project = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "name": "Test Project",
            "description": "A test project",
            "shortDesc": "Test",
            "tags": ["test", "demo"],
            "checklists": {}
        }
        mock_project.get_settings.return_value = mock_settings
        mock_client.get_project.return_value = mock_project

        # Fetch project
        resource_id = "project.TEST_PROJECT"
        resource = project_sync.fetch(resource_id)

        # Verify
        assert isinstance(resource, Resource)
        assert resource.resource_type == "project"
        assert resource.resource_id == resource_id
        assert resource.attributes["projectKey"] == "TEST_PROJECT"
        assert resource.attributes["name"] == "Test Project"
        assert resource.attributes["description"] == "A test project"
        assert resource.attributes["shortDesc"] == "Test"
        assert resource.attributes["tags"] == ["test", "demo"]
        assert resource.attributes["checklists"] == {}
        assert resource.metadata.deployed_by == "system"
        assert resource.metadata.checksum != ""

        # Verify mock calls
        mock_client.get_project.assert_called_once_with("TEST_PROJECT")
        mock_project.get_settings.assert_called_once()

    def test_fetch_invalid_resource_id_format(self, project_sync):
        """Test fetch with invalid resource_id format"""
        with pytest.raises(ValueError, match="Invalid project resource_id"):
            project_sync.fetch("invalid_id")

        with pytest.raises(ValueError, match="Invalid project resource_id"):
            project_sync.fetch("dataset.TEST.my_dataset")

    def test_fetch_wrong_resource_type(self, project_sync):
        """Test fetch with wrong resource type in ID"""
        with pytest.raises(ValueError, match="Invalid project resource_id"):
            project_sync.fetch("dataset.TEST_PROJECT")

    def test_fetch_project_not_found(self, mock_client, project_sync):
        """Test fetching non-existent project"""
        # Setup mock to raise exception
        mock_client.get_project.side_effect = Exception("Project not found")

        # Fetch should raise ResourceNotFoundError
        with pytest.raises(ResourceNotFoundError, match="Project.*not found"):
            project_sync.fetch("project.NONEXISTENT")

    def test_fetch_project_with_minimal_settings(self, mock_client, project_sync):
        """Test fetching project with minimal settings"""
        # Setup mock with minimal settings
        mock_project = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "name": "Minimal Project"
            # Missing optional fields
        }
        mock_project.get_settings.return_value = mock_settings
        mock_client.get_project.return_value = mock_project

        # Fetch project
        resource = project_sync.fetch("project.MINIMAL")

        # Verify defaults are used for missing fields
        assert resource.attributes["name"] == "Minimal Project"
        assert resource.attributes["description"] == ""
        assert resource.attributes["shortDesc"] == ""
        assert resource.attributes["tags"] == []
        assert resource.attributes["checklists"] == {}

    def test_list_all_projects(self, mock_client, project_sync):
        """Test listing all projects"""
        # Setup mock to return multiple projects
        mock_client.list_projects.return_value = [
            {"projectKey": "PROJECT_A"},
            {"projectKey": "PROJECT_B"},
            {"projectKey": "PROJECT_C"}
        ]

        # Mock get_project for each project
        def get_project_side_effect(project_key):
            mock_project = Mock()
            mock_settings = Mock()
            mock_settings.settings = {
                "name": f"Name of {project_key}",
                "description": f"Description of {project_key}",
                "shortDesc": "",
                "tags": [],
                "checklists": {}
            }
            mock_project.get_settings.return_value = mock_settings
            return mock_project

        mock_client.get_project.side_effect = get_project_side_effect

        # List all projects
        resources = project_sync.list_all()

        # Verify
        assert len(resources) == 3
        assert all(isinstance(r, Resource) for r in resources)
        assert resources[0].resource_id == "project.PROJECT_A"
        assert resources[1].resource_id == "project.PROJECT_B"
        assert resources[2].resource_id == "project.PROJECT_C"
        assert resources[0].attributes["name"] == "Name of PROJECT_A"

        # Verify mock calls
        mock_client.list_projects.assert_called_once()
        assert mock_client.get_project.call_count == 3

    def test_list_all_projects_empty(self, mock_client, project_sync):
        """Test listing projects when none exist"""
        # Setup mock to return empty list
        mock_client.list_projects.return_value = []

        # List all projects
        resources = project_sync.list_all()

        # Verify
        assert len(resources) == 0
        assert resources == []

    def test_list_all_ignores_project_key_param(self, mock_client, project_sync):
        """Test that list_all ignores project_key parameter for projects"""
        # Setup mock
        mock_client.list_projects.return_value = [
            {"projectKey": "PROJECT_A"}
        ]

        mock_project = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "name": "Project A",
            "description": "",
            "shortDesc": "",
            "tags": [],
            "checklists": {}
        }
        mock_project.get_settings.return_value = mock_settings
        mock_client.get_project.return_value = mock_project

        # List all with project_key parameter (should be ignored)
        resources = project_sync.list_all(project_key="IGNORED")

        # Verify all projects are returned
        assert len(resources) == 1
        assert resources[0].resource_id == "project.PROJECT_A"

    def test_list_all_projects_failure(self, mock_client, project_sync):
        """Test list_all when API call fails"""
        # Setup mock to raise exception
        mock_client.list_projects.side_effect = Exception("API error")

        # List should raise RuntimeError
        with pytest.raises(RuntimeError, match="Failed to list projects"):
            project_sync.list_all()

    def test_fetch_preserves_project_key_case(self, mock_client, project_sync):
        """Test that project key case is preserved"""
        # Setup mock
        mock_project = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "name": "Mixed Case Project",
            "description": "",
            "shortDesc": "",
            "tags": [],
            "checklists": {}
        }
        mock_project.get_settings.return_value = mock_settings
        mock_client.get_project.return_value = mock_project

        # Fetch with mixed case
        resource = project_sync.fetch("project.MixedCase_123")

        # Verify case is preserved
        assert resource.attributes["projectKey"] == "MixedCase_123"
        assert resource.resource_id == "project.MixedCase_123"

    def test_resource_metadata_fields(self, mock_client, project_sync):
        """Test that resource metadata is properly populated"""
        # Setup mock
        mock_project = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "name": "Test",
            "description": "",
            "shortDesc": "",
            "tags": [],
            "checklists": {}
        }
        mock_project.get_settings.return_value = mock_settings
        mock_client.get_project.return_value = mock_project

        # Fetch project
        resource = project_sync.fetch("project.TEST")

        # Verify metadata
        assert resource.metadata is not None
        assert resource.metadata.deployed_by == "system"
        assert resource.metadata.dataiku_internal_id is None
        assert isinstance(resource.metadata.deployed_at, datetime)
        assert resource.metadata.checksum != ""

    def test_checksum_computation(self, mock_client, project_sync):
        """Test that checksum is computed correctly"""
        # Setup mock
        mock_project = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "name": "Test",
            "description": "Description",
            "shortDesc": "",
            "tags": ["tag1"],
            "checklists": {}
        }
        mock_project.get_settings.return_value = mock_settings
        mock_client.get_project.return_value = mock_project

        # Fetch same project twice
        resource1 = project_sync.fetch("project.TEST")
        resource2 = project_sync.fetch("project.TEST")

        # Checksums should be identical
        assert resource1.metadata.checksum == resource2.metadata.checksum

        # Change settings
        mock_settings.settings["description"] = "Different"
        resource3 = project_sync.fetch("project.TEST")

        # Checksum should be different
        assert resource1.metadata.checksum != resource3.metadata.checksum

    def test_project_key_property(self, mock_client, project_sync):
        """Test project_key property extraction"""
        # Setup mock
        mock_project = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "name": "Test",
            "description": "",
            "shortDesc": "",
            "tags": [],
            "checklists": {}
        }
        mock_project.get_settings.return_value = mock_settings
        mock_client.get_project.return_value = mock_project

        # Fetch project
        resource = project_sync.fetch("project.MY_PROJECT")

        # Verify project_key property
        assert resource.project_key == "MY_PROJECT"

    def test_resource_name_property_empty_for_projects(self, mock_client, project_sync):
        """Test resource_name property is empty for projects"""
        # Setup mock
        mock_project = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "name": "Test",
            "description": "",
            "shortDesc": "",
            "tags": [],
            "checklists": {}
        }
        mock_project.get_settings.return_value = mock_settings
        mock_client.get_project.return_value = mock_project

        # Fetch project
        resource = project_sync.fetch("project.MY_PROJECT")

        # Verify resource_name is empty for project-level resources
        assert resource.resource_name == ""


class TestProjectSyncEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def mock_client(self):
        """Create a mock DSSClient"""
        return Mock()

    @pytest.fixture
    def project_sync(self, mock_client):
        """Create ProjectSync instance with mock client"""
        return ProjectSync(mock_client)

    def test_fetch_with_special_characters_in_settings(self, mock_client, project_sync):
        """Test fetching project with special characters in settings"""
        # Setup mock with special characters
        mock_project = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "name": "Test Project with 'quotes' and \"double quotes\"",
            "description": "Description with\nnewlines\tand\ttabs",
            "shortDesc": "Short with émojis 🎉",
            "tags": ["tag-with-dash", "tag_with_underscore"],
            "checklists": {"key": "value"}
        }
        mock_project.get_settings.return_value = mock_settings
        mock_client.get_project.return_value = mock_project

        # Fetch should work
        resource = project_sync.fetch("project.TEST")

        # Verify special characters are preserved
        assert "quotes" in resource.attributes["name"]
        assert "\n" in resource.attributes["description"]
        assert "émojis" in resource.attributes["shortDesc"]

    def test_fetch_with_none_values_in_settings(self, mock_client, project_sync):
        """Test fetching project with None values in settings"""
        # Setup mock with None values
        mock_project = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "name": None,
            "description": None,
            "shortDesc": None,
            "tags": None,
            "checklists": None
        }
        mock_project.get_settings.return_value = mock_settings
        mock_client.get_project.return_value = mock_project

        # Fetch should handle None values
        resource = project_sync.fetch("project.TEST")

        # Verify None values are handled (defaults used)
        # .get() returns "" for missing keys, but None is present
        # This tests that we handle None properly
        assert resource.attributes["name"] is None or resource.attributes["name"] == ""

    def test_list_all_with_fetch_failure_on_one_project(self, mock_client, project_sync):
        """Test list_all when fetching one project fails"""
        # Setup mock to return multiple projects
        mock_client.list_projects.return_value = [
            {"projectKey": "PROJECT_A"},
            {"projectKey": "PROJECT_B"}
        ]

        # First project succeeds, second fails
        def get_project_side_effect(project_key):
            if project_key == "PROJECT_A":
                mock_project = Mock()
                mock_settings = Mock()
                mock_settings.settings = {
                    "name": "Project A",
                    "description": "",
                    "shortDesc": "",
                    "tags": [],
                    "checklists": {}
                }
                mock_project.get_settings.return_value = mock_settings
                return mock_project
            else:
                raise Exception("Failed to fetch PROJECT_B")

        mock_client.get_project.side_effect = get_project_side_effect

        # list_all should raise RuntimeError (wraps underlying exception)
        with pytest.raises(RuntimeError, match="Failed to list projects"):
            project_sync.list_all()
