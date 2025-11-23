"""
Unit tests for RecipeSync with mocked DSSClient.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from dataikuapi.iac.sync import RecipeSync
from dataikuapi.iac.models import Resource, make_resource_id
from dataikuapi.iac.exceptions import ResourceNotFoundError


class TestRecipeSync:
    """Test RecipeSync implementation"""

    @pytest.fixture
    def mock_client(self):
        """Create a mock DSSClient"""
        return Mock()

    @pytest.fixture
    def recipe_sync(self, mock_client):
        """Create RecipeSync instance with mock client"""
        return RecipeSync(mock_client)

    def test_resource_type(self, recipe_sync):
        """Test resource_type property returns 'recipe'"""
        assert recipe_sync.resource_type == "recipe"

    def test_fetch_python_recipe(self, mock_client, recipe_sync):
        """Test fetching a Python recipe with payload"""
        # Setup mock
        mock_project = Mock()
        mock_recipe = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "type": "python",
            "inputs": {"main": {"items": [{"ref": "input_dataset"}]}},
            "outputs": {"main": {"items": [{"ref": "output_dataset"}]}},
            "params": {"envSelection": {"envMode": "INHERIT"}},
            "tags": ["etl", "transform"]
        }
        mock_recipe.get_settings.return_value = mock_settings
        mock_recipe.get_payload.return_value = "# Python code\nprint('Hello')"
        mock_project.get_recipe.return_value = mock_recipe
        mock_client.get_project.return_value = mock_project

        # Fetch recipe
        resource_id = "recipe.TEST_PROJECT.prep_data"
        resource = recipe_sync.fetch(resource_id)

        # Verify
        assert isinstance(resource, Resource)
        assert resource.resource_type == "recipe"
        assert resource.resource_id == resource_id
        assert resource.attributes["name"] == "prep_data"
        assert resource.attributes["type"] == "python"
        assert "payload" in resource.attributes
        assert resource.attributes["payload"] == "# Python code\nprint('Hello')"
        assert resource.attributes["inputs"] == {"main": {"items": [{"ref": "input_dataset"}]}}
        assert resource.attributes["outputs"] == {"main": {"items": [{"ref": "output_dataset"}]}}
        assert resource.attributes["params"] == {"envSelection": {"envMode": "INHERIT"}}
        assert resource.attributes["tags"] == ["etl", "transform"]
        assert resource.metadata.deployed_by == "system"
        assert resource.metadata.dataiku_internal_id == "prep_data"
        assert resource.metadata.checksum != ""

        # Verify mock calls
        mock_client.get_project.assert_called_once_with("TEST_PROJECT")
        mock_project.get_recipe.assert_called_once_with("prep_data")
        mock_recipe.get_settings.assert_called_once()
        mock_recipe.get_payload.assert_called_once()

    def test_fetch_sql_recipe(self, mock_client, recipe_sync):
        """Test fetching a SQL recipe with payload"""
        # Setup mock
        mock_project = Mock()
        mock_recipe = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "type": "sql",
            "inputs": {},
            "outputs": {"main": {"items": [{"ref": "sql_output"}]}},
            "params": {"engineParams": {"hive": {}}},
            "tags": []
        }
        mock_recipe.get_settings.return_value = mock_settings
        mock_recipe.get_payload.return_value = "SELECT * FROM table"
        mock_project.get_recipe.return_value = mock_recipe
        mock_client.get_project.return_value = mock_project

        # Fetch recipe
        resource_id = "recipe.TEST_PROJECT.sql_transform"
        resource = recipe_sync.fetch(resource_id)

        # Verify
        assert resource.attributes["type"] == "sql"
        assert "payload" in resource.attributes
        assert resource.attributes["payload"] == "SELECT * FROM table"
        mock_recipe.get_payload.assert_called_once()

    def test_fetch_r_recipe(self, mock_client, recipe_sync):
        """Test fetching an R recipe with payload"""
        # Setup mock
        mock_project = Mock()
        mock_recipe = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "type": "r",
            "inputs": {"main": {"items": [{"ref": "input_data"}]}},
            "outputs": {"main": {"items": [{"ref": "output_data"}]}},
            "params": {},
            "tags": ["analytics"]
        }
        mock_recipe.get_settings.return_value = mock_settings
        mock_recipe.get_payload.return_value = "# R code\nlibrary(dplyr)"
        mock_project.get_recipe.return_value = mock_recipe
        mock_client.get_project.return_value = mock_project

        # Fetch recipe
        resource_id = "recipe.TEST_PROJECT.r_analysis"
        resource = recipe_sync.fetch(resource_id)

        # Verify
        assert resource.attributes["type"] == "r"
        assert "payload" in resource.attributes
        assert resource.attributes["payload"] == "# R code\nlibrary(dplyr)"
        mock_recipe.get_payload.assert_called_once()

    def test_fetch_visual_recipe(self, mock_client, recipe_sync):
        """Test fetching a visual recipe (no payload)"""
        # Setup mock
        mock_project = Mock()
        mock_recipe = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "type": "grouping",
            "inputs": {"main": {"items": [{"ref": "input_dataset"}]}},
            "outputs": {"main": {"items": [{"ref": "output_dataset"}]}},
            "params": {"keys": [{"column": "customer_id"}]},
            "tags": []
        }
        mock_recipe.get_settings.return_value = mock_settings
        # Visual recipes don't have get_payload
        mock_project.get_recipe.return_value = mock_recipe
        mock_client.get_project.return_value = mock_project

        # Fetch recipe
        resource_id = "recipe.TEST_PROJECT.group_customers"
        resource = recipe_sync.fetch(resource_id)

        # Verify
        assert resource.attributes["type"] == "grouping"
        assert "payload" not in resource.attributes
        assert resource.attributes["params"] == {"keys": [{"column": "customer_id"}]}

    def test_fetch_code_recipe_payload_failure(self, mock_client, recipe_sync):
        """Test fetching code recipe when payload fetch fails"""
        # Setup mock
        mock_project = Mock()
        mock_recipe = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "type": "python",
            "inputs": {},
            "outputs": {},
            "params": {},
            "tags": []
        }
        mock_recipe.get_settings.return_value = mock_settings
        mock_recipe.get_payload.side_effect = Exception("Payload fetch failed")
        mock_project.get_recipe.return_value = mock_recipe
        mock_client.get_project.return_value = mock_project

        # Fetch recipe (should not fail, just no payload)
        resource_id = "recipe.TEST_PROJECT.broken_recipe"
        resource = recipe_sync.fetch(resource_id)

        # Verify - should succeed without payload
        assert resource.attributes["type"] == "python"
        assert "payload" not in resource.attributes

    def test_fetch_invalid_resource_id_format(self, recipe_sync):
        """Test fetch with invalid resource_id format"""
        with pytest.raises(ValueError, match="Invalid recipe resource_id"):
            recipe_sync.fetch("invalid_id")

        with pytest.raises(ValueError, match="Invalid recipe resource_id"):
            recipe_sync.fetch("project.TEST")

        with pytest.raises(ValueError, match="Invalid recipe resource_id"):
            recipe_sync.fetch("dataset.TEST.my_dataset")

    def test_fetch_wrong_resource_type(self, recipe_sync):
        """Test fetch with wrong resource type in ID"""
        with pytest.raises(ValueError, match="Invalid recipe resource_id"):
            recipe_sync.fetch("project.TEST_PROJECT.recipe_name")

    def test_fetch_recipe_not_found(self, mock_client, recipe_sync):
        """Test fetching non-existent recipe"""
        # Setup mock to raise exception
        mock_project = Mock()
        mock_project.get_recipe.side_effect = Exception("Recipe not found")
        mock_client.get_project.return_value = mock_project

        # Fetch should raise ResourceNotFoundError
        with pytest.raises(ResourceNotFoundError, match="Recipe.*not found"):
            recipe_sync.fetch("recipe.TEST_PROJECT.nonexistent")

    def test_fetch_project_not_found(self, mock_client, recipe_sync):
        """Test fetching recipe when project doesn't exist"""
        # Setup mock to raise exception
        mock_client.get_project.side_effect = Exception("Project not found")

        # Fetch should raise ResourceNotFoundError
        with pytest.raises(ResourceNotFoundError, match="Recipe.*not found"):
            recipe_sync.fetch("recipe.NONEXISTENT.some_recipe")

    def test_fetch_recipe_with_minimal_settings(self, mock_client, recipe_sync):
        """Test fetching recipe with minimal settings"""
        # Setup mock with minimal settings
        mock_project = Mock()
        mock_recipe = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "type": "sync"
            # Missing optional fields
        }
        mock_recipe.get_settings.return_value = mock_settings
        mock_project.get_recipe.return_value = mock_recipe
        mock_client.get_project.return_value = mock_project

        # Fetch recipe
        resource = recipe_sync.fetch("recipe.TEST.minimal_recipe")

        # Verify defaults are used for missing fields
        assert resource.attributes["type"] == "sync"
        assert resource.attributes["inputs"] == {}
        assert resource.attributes["outputs"] == {}
        assert resource.attributes["params"] == {}
        assert resource.attributes["tags"] == []

    def test_list_all_recipes(self, mock_client, recipe_sync):
        """Test listing all recipes in a project"""
        # Setup mock to return multiple recipes
        mock_project = Mock()
        mock_project.list_recipes.return_value = [
            {"name": "recipe_a"},
            {"name": "recipe_b"},
            {"name": "recipe_c"}
        ]
        mock_client.get_project.return_value = mock_project

        # Mock get_recipe for each recipe
        def get_recipe_side_effect(recipe_name):
            mock_recipe = Mock()
            mock_settings = Mock()
            mock_settings.settings = {
                "type": "python",
                "inputs": {},
                "outputs": {},
                "params": {},
                "tags": []
            }
            mock_recipe.get_settings.return_value = mock_settings
            mock_recipe.get_payload.return_value = f"# Code for {recipe_name}"
            return mock_recipe

        mock_project.get_recipe.side_effect = get_recipe_side_effect

        # List all recipes
        resources = recipe_sync.list_all(project_key="TEST_PROJECT")

        # Verify
        assert len(resources) == 3
        assert all(isinstance(r, Resource) for r in resources)
        assert resources[0].resource_id == "recipe.TEST_PROJECT.recipe_a"
        assert resources[1].resource_id == "recipe.TEST_PROJECT.recipe_b"
        assert resources[2].resource_id == "recipe.TEST_PROJECT.recipe_c"
        assert all(r.attributes["type"] == "python" for r in resources)

        # Verify mock calls
        mock_client.get_project.assert_called_with("TEST_PROJECT")
        mock_project.list_recipes.assert_called_once()
        assert mock_project.get_recipe.call_count == 3

    def test_list_all_recipes_empty(self, mock_client, recipe_sync):
        """Test listing recipes when none exist"""
        # Setup mock to return empty list
        mock_project = Mock()
        mock_project.list_recipes.return_value = []
        mock_client.get_project.return_value = mock_project

        # List all recipes
        resources = recipe_sync.list_all(project_key="EMPTY_PROJECT")

        # Verify
        assert len(resources) == 0
        assert resources == []

    def test_list_all_without_project_key(self, recipe_sync):
        """Test list_all requires project_key parameter"""
        # Should raise ValueError
        with pytest.raises(ValueError, match="project_key required"):
            recipe_sync.list_all()

        with pytest.raises(ValueError, match="project_key required"):
            recipe_sync.list_all(project_key=None)

    def test_list_all_recipes_failure(self, mock_client, recipe_sync):
        """Test list_all when API call fails"""
        # Setup mock to raise exception
        mock_project = Mock()
        mock_project.list_recipes.side_effect = Exception("API error")
        mock_client.get_project.return_value = mock_project

        # List should raise RuntimeError
        with pytest.raises(RuntimeError, match="Failed to list recipes"):
            recipe_sync.list_all(project_key="TEST_PROJECT")

    def test_list_all_project_not_found(self, mock_client, recipe_sync):
        """Test list_all when project doesn't exist"""
        # Setup mock to raise exception
        mock_client.get_project.side_effect = Exception("Project not found")

        # List should raise RuntimeError
        with pytest.raises(RuntimeError, match="Failed to list recipes"):
            recipe_sync.list_all(project_key="NONEXISTENT")

    def test_fetch_preserves_recipe_name_case(self, mock_client, recipe_sync):
        """Test that recipe name case is preserved"""
        # Setup mock
        mock_project = Mock()
        mock_recipe = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "type": "python",
            "inputs": {},
            "outputs": {},
            "params": {},
            "tags": []
        }
        mock_recipe.get_settings.return_value = mock_settings
        mock_recipe.get_payload.return_value = "# code"
        mock_project.get_recipe.return_value = mock_recipe
        mock_client.get_project.return_value = mock_project

        # Fetch with mixed case
        resource = recipe_sync.fetch("recipe.MY_PROJECT.MixedCase_Recipe_123")

        # Verify case is preserved
        assert resource.attributes["name"] == "MixedCase_Recipe_123"
        assert resource.resource_id == "recipe.MY_PROJECT.MixedCase_Recipe_123"

    def test_resource_metadata_fields(self, mock_client, recipe_sync):
        """Test that resource metadata is properly populated"""
        # Setup mock
        mock_project = Mock()
        mock_recipe = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "type": "sync",
            "inputs": {},
            "outputs": {},
            "params": {},
            "tags": []
        }
        mock_recipe.get_settings.return_value = mock_settings
        mock_project.get_recipe.return_value = mock_recipe
        mock_client.get_project.return_value = mock_project

        # Fetch recipe
        resource = recipe_sync.fetch("recipe.TEST.my_recipe")

        # Verify metadata
        assert resource.metadata is not None
        assert resource.metadata.deployed_by == "system"
        assert resource.metadata.dataiku_internal_id == "my_recipe"
        assert isinstance(resource.metadata.deployed_at, datetime)
        assert resource.metadata.checksum != ""

    def test_checksum_computation(self, mock_client, recipe_sync):
        """Test that checksum is computed correctly"""
        # Setup mock
        mock_project = Mock()
        mock_recipe = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "type": "python",
            "inputs": {},
            "outputs": {},
            "params": {"key": "value"},
            "tags": ["tag1"]
        }
        mock_recipe.get_settings.return_value = mock_settings
        mock_recipe.get_payload.return_value = "# code"
        mock_project.get_recipe.return_value = mock_recipe
        mock_client.get_project.return_value = mock_project

        # Fetch same recipe twice
        resource1 = recipe_sync.fetch("recipe.TEST.my_recipe")
        resource2 = recipe_sync.fetch("recipe.TEST.my_recipe")

        # Checksums should be identical
        assert resource1.metadata.checksum == resource2.metadata.checksum

        # Change settings
        mock_settings.settings["params"] = {"key": "different"}
        resource3 = recipe_sync.fetch("recipe.TEST.my_recipe")

        # Checksum should be different
        assert resource1.metadata.checksum != resource3.metadata.checksum

    def test_project_key_property(self, mock_client, recipe_sync):
        """Test project_key property extraction"""
        # Setup mock
        mock_project = Mock()
        mock_recipe = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "type": "sync",
            "inputs": {},
            "outputs": {},
            "params": {},
            "tags": []
        }
        mock_recipe.get_settings.return_value = mock_settings
        mock_project.get_recipe.return_value = mock_recipe
        mock_client.get_project.return_value = mock_project

        # Fetch recipe
        resource = recipe_sync.fetch("recipe.MY_PROJECT.my_recipe")

        # Verify project_key property
        assert resource.project_key == "MY_PROJECT"

    def test_resource_name_property(self, mock_client, recipe_sync):
        """Test resource_name property extraction"""
        # Setup mock
        mock_project = Mock()
        mock_recipe = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "type": "sync",
            "inputs": {},
            "outputs": {},
            "params": {},
            "tags": []
        }
        mock_recipe.get_settings.return_value = mock_settings
        mock_project.get_recipe.return_value = mock_recipe
        mock_client.get_project.return_value = mock_project

        # Fetch recipe
        resource = recipe_sync.fetch("recipe.MY_PROJECT.my_recipe")

        # Verify resource_name property
        assert resource.resource_name == "my_recipe"


class TestRecipeSyncEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def mock_client(self):
        """Create a mock DSSClient"""
        return Mock()

    @pytest.fixture
    def recipe_sync(self, mock_client):
        """Create RecipeSync instance with mock client"""
        return RecipeSync(mock_client)

    def test_fetch_with_special_characters_in_settings(self, mock_client, recipe_sync):
        """Test fetching recipe with special characters in settings"""
        # Setup mock with special characters
        mock_project = Mock()
        mock_recipe = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "type": "python",
            "inputs": {"main": {"items": []}},
            "outputs": {"main": {"items": []}},
            "params": {"description": "Test with 'quotes' and \"double quotes\""},
            "tags": ["tag-with-dash", "tag_with_underscore", "émoji🎉"]
        }
        mock_recipe.get_settings.return_value = mock_settings
        mock_recipe.get_payload.return_value = "# Code with\nnewlines\tand\ttabs"
        mock_project.get_recipe.return_value = mock_recipe
        mock_client.get_project.return_value = mock_project

        # Fetch should work
        resource = recipe_sync.fetch("recipe.TEST.special_recipe")

        # Verify special characters are preserved
        assert "quotes" in resource.attributes["params"]["description"]
        assert "\n" in resource.attributes["payload"]
        assert "émoji🎉" in resource.attributes["tags"]

    def test_fetch_with_none_values_in_settings(self, mock_client, recipe_sync):
        """Test fetching recipe with None values in settings"""
        # Setup mock with None values
        mock_project = Mock()
        mock_recipe = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "type": None,
            "inputs": None,
            "outputs": None,
            "params": None,
            "tags": None
        }
        mock_recipe.get_settings.return_value = mock_settings
        mock_project.get_recipe.return_value = mock_recipe
        mock_client.get_project.return_value = mock_project

        # Fetch should handle None values
        resource = recipe_sync.fetch("recipe.TEST.none_recipe")

        # Verify None values are handled (defaults used)
        assert resource.attributes["type"] is None or resource.attributes["type"] == ""

    def test_list_all_with_mixed_recipe_types(self, mock_client, recipe_sync):
        """Test list_all with mix of code and visual recipes"""
        # Setup mock to return mixed recipes
        mock_project = Mock()
        mock_project.list_recipes.return_value = [
            {"name": "python_recipe"},
            {"name": "visual_recipe"},
            {"name": "sql_recipe"}
        ]
        mock_client.get_project.return_value = mock_project

        # Mock get_recipe for each recipe
        def get_recipe_side_effect(recipe_name):
            mock_recipe = Mock()
            mock_settings = Mock()
            if recipe_name == "python_recipe":
                mock_settings.settings = {"type": "python", "inputs": {}, "outputs": {}, "params": {}, "tags": []}
                mock_recipe.get_payload.return_value = "# python code"
            elif recipe_name == "visual_recipe":
                mock_settings.settings = {"type": "grouping", "inputs": {}, "outputs": {}, "params": {}, "tags": []}
            elif recipe_name == "sql_recipe":
                mock_settings.settings = {"type": "sql", "inputs": {}, "outputs": {}, "params": {}, "tags": []}
                mock_recipe.get_payload.return_value = "SELECT * FROM table"
            mock_recipe.get_settings.return_value = mock_settings
            return mock_recipe

        mock_project.get_recipe.side_effect = get_recipe_side_effect

        # List all recipes
        resources = recipe_sync.list_all(project_key="TEST_PROJECT")

        # Verify
        assert len(resources) == 3
        assert resources[0].attributes["type"] == "python"
        assert "payload" in resources[0].attributes
        assert resources[1].attributes["type"] == "grouping"
        assert "payload" not in resources[1].attributes
        assert resources[2].attributes["type"] == "sql"
        assert "payload" in resources[2].attributes

    def test_list_all_with_fetch_failure_on_one_recipe(self, mock_client, recipe_sync):
        """Test list_all when fetching one recipe fails"""
        # Setup mock to return multiple recipes
        mock_project = Mock()
        mock_project.list_recipes.return_value = [
            {"name": "recipe_a"},
            {"name": "recipe_b"}
        ]
        mock_client.get_project.return_value = mock_project

        # First recipe succeeds, second fails
        def get_recipe_side_effect(recipe_name):
            if recipe_name == "recipe_a":
                mock_recipe = Mock()
                mock_settings = Mock()
                mock_settings.settings = {
                    "type": "sync",
                    "inputs": {},
                    "outputs": {},
                    "params": {},
                    "tags": []
                }
                mock_recipe.get_settings.return_value = mock_settings
                return mock_recipe
            else:
                raise Exception("Failed to fetch recipe_b")

        mock_project.get_recipe.side_effect = get_recipe_side_effect

        # list_all should raise RuntimeError (wraps underlying exception)
        with pytest.raises(RuntimeError, match="Failed to list recipes"):
            recipe_sync.list_all(project_key="TEST_PROJECT")

    def test_fetch_with_complex_inputs_outputs(self, mock_client, recipe_sync):
        """Test fetching recipe with complex inputs and outputs"""
        # Setup mock with complex I/O
        mock_project = Mock()
        mock_recipe = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "type": "python",
            "inputs": {
                "main": {
                    "items": [
                        {"ref": "input1", "deps": []},
                        {"ref": "input2", "deps": []}
                    ]
                }
            },
            "outputs": {
                "main": {
                    "items": [
                        {"ref": "output1", "appendMode": False},
                        {"ref": "output2", "appendMode": True}
                    ]
                }
            },
            "params": {"containerSelection": {"containerMode": "INHERIT"}},
            "tags": []
        }
        mock_recipe.get_settings.return_value = mock_settings
        mock_recipe.get_payload.return_value = "# complex code"
        mock_project.get_recipe.return_value = mock_recipe
        mock_client.get_project.return_value = mock_project

        # Fetch recipe
        resource = recipe_sync.fetch("recipe.TEST.complex_recipe")

        # Verify complex structures are preserved
        assert len(resource.attributes["inputs"]["main"]["items"]) == 2
        assert len(resource.attributes["outputs"]["main"]["items"]) == 2
        assert resource.attributes["inputs"]["main"]["items"][0]["ref"] == "input1"
        assert resource.attributes["outputs"]["main"]["items"][1]["appendMode"] is True

    def test_make_resource_id_helper(self, mock_client, recipe_sync):
        """Test that make_resource_id helper works correctly"""
        # Test the helper function
        resource_id = make_resource_id("recipe", "MY_PROJECT", "my_recipe")
        assert resource_id == "recipe.MY_PROJECT.my_recipe"

    def test_fetch_with_empty_payload(self, mock_client, recipe_sync):
        """Test fetching code recipe with empty payload"""
        # Setup mock
        mock_project = Mock()
        mock_recipe = Mock()
        mock_settings = Mock()
        mock_settings.settings = {
            "type": "python",
            "inputs": {},
            "outputs": {},
            "params": {},
            "tags": []
        }
        mock_recipe.get_settings.return_value = mock_settings
        mock_recipe.get_payload.return_value = ""
        mock_project.get_recipe.return_value = mock_recipe
        mock_client.get_project.return_value = mock_project

        # Fetch recipe
        resource = recipe_sync.fetch("recipe.TEST.empty_code")

        # Verify - empty string payload should still be included
        assert "payload" in resource.attributes
        assert resource.attributes["payload"] == ""
