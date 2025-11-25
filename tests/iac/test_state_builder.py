"""
Tests for DesiredStateBuilder.

Tests conversion of Config objects to State objects.
"""

import pytest
from pathlib import Path
import yaml

from dataikuapi.iac.config.models import (
    Config,
    ProjectConfig,
    DatasetConfig,
    RecipeConfig
)
from dataikuapi.iac.config.builder import DesiredStateBuilder
from dataikuapi.iac.models.state import State, Resource, make_resource_id
from dataikuapi.iac.exceptions import BuildError


class TestDesiredStateBuilder:
    """Test DesiredStateBuilder class"""

    def test_builder_initialization(self):
        """Test builder can be initialized"""
        builder = DesiredStateBuilder(environment="test")
        assert builder.environment == "test"

    def test_builder_default_environment(self):
        """Test builder has default environment"""
        builder = DesiredStateBuilder()
        assert builder.environment == "default"

    def test_build_simple_config(self):
        """Test building state from simple config"""
        # Create simple config
        config = Config(
            version="1.0",
            project=ProjectConfig(
                key="TEST_PROJECT",
                name="Test Project",
                description="A test project"
            ),
            datasets=[
                DatasetConfig(
                    name="TEST_DATASET",
                    type="managed",
                    format_type="parquet"
                )
            ]
        )

        # Build state
        builder = DesiredStateBuilder(environment="test")
        state = builder.build(config)

        # Verify state
        assert isinstance(state, State)
        assert state.environment == "test"
        assert len(state.resources) == 2  # 1 project + 1 dataset

        # Verify project resource
        project_id = "project.TEST_PROJECT"
        assert state.has_resource(project_id)
        project = state.get_resource(project_id)
        assert project.resource_type == "project"
        assert project.attributes["projectKey"] == "TEST_PROJECT"
        assert project.attributes["name"] == "Test Project"
        assert project.attributes["description"] == "A test project"
        assert project.metadata.deployed_by == "config"

        # Verify dataset resource
        dataset_id = "dataset.TEST_PROJECT.TEST_DATASET"
        assert state.has_resource(dataset_id)
        dataset = state.get_resource(dataset_id)
        assert dataset.resource_type == "dataset"
        assert dataset.attributes["name"] == "TEST_DATASET"
        assert dataset.attributes["type"] == "managed"
        assert dataset.attributes["formatType"] == "parquet"
        assert dataset.metadata.deployed_by == "config"

    def test_build_complete_config(self):
        """Test building state from complete config"""
        # Create complete config
        config = Config(
            version="1.0",
            project=ProjectConfig(
                key="ANALYTICS",
                name="Analytics Project",
                description="Complete analytics project",
                settings={"exposed": True}
            ),
            datasets=[
                DatasetConfig(
                    name="RAW_DATA",
                    type="snowflake",
                    connection="snowflake_prod",
                    params={"table": "raw_data", "schema": "public"}
                ),
                DatasetConfig(
                    name="CLEAN_DATA",
                    type="managed",
                    format_type="parquet",
                    schema={"columns": [{"name": "id", "type": "int"}]}
                )
            ],
            recipes=[
                RecipeConfig(
                    name="clean_data",
                    type="python",
                    inputs=["RAW_DATA"],
                    outputs=["CLEAN_DATA"],
                    code="output = input"
                )
            ]
        )

        # Build state
        builder = DesiredStateBuilder(environment="prod")
        state = builder.build(config)

        # Verify state
        assert len(state.resources) == 4  # 1 project + 2 datasets + 1 recipe

        # Verify all resources exist
        assert state.has_resource("project.ANALYTICS")
        assert state.has_resource("dataset.ANALYTICS.RAW_DATA")
        assert state.has_resource("dataset.ANALYTICS.CLEAN_DATA")
        assert state.has_resource("recipe.ANALYTICS.clean_data")

    def test_build_project_resource(self):
        """Test building project resource"""
        config = Config(
            project=ProjectConfig(
                key="TEST_PROJ",
                name="Test",
                description="Description",
                settings={"key": "value"}
            )
        )

        builder = DesiredStateBuilder()
        state = builder.build(config)

        project = state.get_resource("project.TEST_PROJ")
        assert project.resource_type == "project"
        assert project.resource_id == "project.TEST_PROJ"
        assert project.attributes["projectKey"] == "TEST_PROJ"
        assert project.attributes["name"] == "Test"
        assert project.attributes["description"] == "Description"
        assert project.attributes["settings"] == {"key": "value"}

    def test_build_dataset_resource_minimal(self):
        """Test building minimal dataset resource"""
        config = Config(
            project=ProjectConfig(key="PROJ", name="Project"),
            datasets=[
                DatasetConfig(
                    name="DATASET",
                    type="managed"
                )
            ]
        )

        builder = DesiredStateBuilder()
        state = builder.build(config)

        dataset = state.get_resource("dataset.PROJ.DATASET")
        assert dataset.resource_type == "dataset"
        assert dataset.resource_id == "dataset.PROJ.DATASET"
        assert dataset.attributes["name"] == "DATASET"
        assert dataset.attributes["type"] == "managed"
        assert "connection" not in dataset.attributes or dataset.attributes["connection"] is None

    def test_build_dataset_resource_complete(self):
        """Test building complete dataset resource"""
        config = Config(
            project=ProjectConfig(key="PROJ", name="Project"),
            datasets=[
                DatasetConfig(
                    name="DATASET",
                    type="snowflake",
                    connection="snowflake",
                    params={"table": "my_table"},
                    schema={"columns": []},
                    format_type="parquet"
                )
            ]
        )

        builder = DesiredStateBuilder()
        state = builder.build(config)

        dataset = state.get_resource("dataset.PROJ.DATASET")
        assert dataset.attributes["name"] == "DATASET"
        assert dataset.attributes["type"] == "snowflake"
        assert dataset.attributes["connection"] == "snowflake"
        assert dataset.attributes["params"] == {"table": "my_table"}
        assert dataset.attributes["schema"] == {"columns": []}
        assert dataset.attributes["formatType"] == "parquet"

    def test_build_recipe_resource_minimal(self):
        """Test building minimal recipe resource"""
        config = Config(
            project=ProjectConfig(key="PROJ", name="Project"),
            recipes=[
                RecipeConfig(
                    name="recipe",
                    type="python",
                    outputs=["OUTPUT"]
                )
            ]
        )

        builder = DesiredStateBuilder()
        state = builder.build(config)

        recipe = state.get_resource("recipe.PROJ.recipe")
        assert recipe.resource_type == "recipe"
        assert recipe.resource_id == "recipe.PROJ.recipe"
        assert recipe.attributes["name"] == "recipe"
        assert recipe.attributes["type"] == "python"
        assert recipe.attributes["inputs"] == []
        assert recipe.attributes["outputs"] == ["OUTPUT"]

    def test_build_recipe_resource_complete(self):
        """Test building complete recipe resource"""
        config = Config(
            project=ProjectConfig(key="PROJ", name="Project"),
            recipes=[
                RecipeConfig(
                    name="recipe",
                    type="python",
                    inputs=["INPUT1", "INPUT2"],
                    outputs=["OUTPUT"],
                    params={"key": "value"},
                    code="# Recipe code\noutput = input"
                )
            ]
        )

        builder = DesiredStateBuilder()
        state = builder.build(config)

        recipe = state.get_resource("recipe.PROJ.recipe")
        assert recipe.attributes["name"] == "recipe"
        assert recipe.attributes["type"] == "python"
        assert recipe.attributes["inputs"] == ["INPUT1", "INPUT2"]
        assert recipe.attributes["outputs"] == ["OUTPUT"]
        assert recipe.attributes["params"] == {"key": "value"}
        assert recipe.attributes["code"] == "# Recipe code\noutput = input"

    def test_resource_ids_format(self):
        """Test that resource IDs follow correct format"""
        config = Config(
            project=ProjectConfig(key="MY_PROJECT", name="Project"),
            datasets=[
                DatasetConfig(name="MY_DATASET", type="managed")
            ],
            recipes=[
                RecipeConfig(name="my_recipe", type="python", outputs=["OUTPUT"])
            ]
        )

        builder = DesiredStateBuilder()
        state = builder.build(config)

        # Check format: {type}.{project_key}[.{resource_name}]
        assert state.has_resource("project.MY_PROJECT")
        assert state.has_resource("dataset.MY_PROJECT.MY_DATASET")
        assert state.has_resource("recipe.MY_PROJECT.my_recipe")

        # Verify using make_resource_id helper
        assert state.has_resource(make_resource_id("project", "MY_PROJECT"))
        assert state.has_resource(make_resource_id("dataset", "MY_PROJECT", "MY_DATASET"))
        assert state.has_resource(make_resource_id("recipe", "MY_PROJECT", "my_recipe"))

    def test_metadata_set_correctly(self):
        """Test that resource metadata is set correctly"""
        config = Config(
            project=ProjectConfig(key="PROJ", name="Project"),
            datasets=[
                DatasetConfig(name="DATASET", type="managed")
            ]
        )

        builder = DesiredStateBuilder(environment="test_env")
        state = builder.build(config)

        # Check project metadata
        project = state.get_resource("project.PROJ")
        assert project.metadata.deployed_by == "config"
        assert project.metadata.dataiku_internal_id is None
        assert project.metadata.deployed_at is not None
        assert project.metadata.checksum != ""

        # Check dataset metadata
        dataset = state.get_resource("dataset.PROJ.DATASET")
        assert dataset.metadata.deployed_by == "config"
        assert dataset.metadata.dataiku_internal_id is None
        assert dataset.metadata.deployed_at is not None
        assert dataset.metadata.checksum != ""

    def test_build_empty_datasets_and_recipes(self):
        """Test building with empty datasets and recipes lists"""
        config = Config(
            project=ProjectConfig(key="PROJ", name="Project"),
            datasets=[],
            recipes=[]
        )

        builder = DesiredStateBuilder()
        state = builder.build(config)

        assert len(state.resources) == 1  # Only project
        assert state.has_resource("project.PROJ")

    def test_build_multiple_datasets(self):
        """Test building with multiple datasets"""
        config = Config(
            project=ProjectConfig(key="PROJ", name="Project"),
            datasets=[
                DatasetConfig(name="DS1", type="managed"),
                DatasetConfig(name="DS2", type="managed"),
                DatasetConfig(name="DS3", type="managed")
            ]
        )

        builder = DesiredStateBuilder()
        state = builder.build(config)

        assert len(state.resources) == 4  # 1 project + 3 datasets
        assert state.has_resource("dataset.PROJ.DS1")
        assert state.has_resource("dataset.PROJ.DS2")
        assert state.has_resource("dataset.PROJ.DS3")

    def test_build_multiple_recipes(self):
        """Test building with multiple recipes"""
        config = Config(
            project=ProjectConfig(key="PROJ", name="Project"),
            recipes=[
                RecipeConfig(name="r1", type="python", outputs=["O1"]),
                RecipeConfig(name="r2", type="sql", outputs=["O2"]),
                RecipeConfig(name="r3", type="join", outputs=["O3"])
            ]
        )

        builder = DesiredStateBuilder()
        state = builder.build(config)

        assert len(state.resources) == 4  # 1 project + 3 recipes
        assert state.has_resource("recipe.PROJ.r1")
        assert state.has_resource("recipe.PROJ.r2")
        assert state.has_resource("recipe.PROJ.r3")

    def test_build_without_project_raises_error(self):
        """Test that building without project raises BuildError"""
        config = Config(
            project=None,
            datasets=[
                DatasetConfig(name="DS", type="managed")
            ]
        )

        builder = DesiredStateBuilder()
        with pytest.raises(BuildError, match="must include a project"):
            builder.build(config)

    def test_state_serial_incremented(self):
        """Test that state serial is incremented for each resource"""
        config = Config(
            project=ProjectConfig(key="PROJ", name="Project"),
            datasets=[
                DatasetConfig(name="DS1", type="managed"),
                DatasetConfig(name="DS2", type="managed")
            ]
        )

        builder = DesiredStateBuilder()
        state = builder.build(config)

        # Serial should be incremented for each resource added
        assert state.serial >= 3  # At least 3 resources added


class TestConfigFromDict:
    """Test Config.from_dict() method"""

    def test_from_dict_simple(self):
        """Test creating config from simple dict"""
        data = {
            "version": "1.0",
            "project": {
                "key": "PROJ",
                "name": "Project"
            }
        }

        config = Config.from_dict(data)
        assert config.version == "1.0"
        assert config.project.key == "PROJ"
        assert config.project.name == "Project"

    def test_from_dict_complete(self):
        """Test creating config from complete dict"""
        data = {
            "version": "1.0",
            "metadata": {"author": "test"},
            "project": {
                "key": "PROJ",
                "name": "Project",
                "description": "Desc",
                "settings": {"key": "value"}
            },
            "datasets": [
                {
                    "name": "DS",
                    "type": "managed",
                    "format_type": "parquet"
                }
            ],
            "recipes": [
                {
                    "name": "recipe",
                    "type": "python",
                    "inputs": ["DS"],
                    "outputs": ["OUT"],
                    "code": "code"
                }
            ]
        }

        config = Config.from_dict(data)
        assert config.metadata == {"author": "test"}
        assert config.project.settings == {"key": "value"}
        assert len(config.datasets) == 1
        assert config.datasets[0].name == "DS"
        assert len(config.recipes) == 1
        assert config.recipes[0].name == "recipe"


class TestIntegrationWithYAML:
    """Integration tests with YAML fixture files"""

    def test_build_from_simple_yaml(self):
        """Test building state from simple YAML fixture"""
        fixture_path = Path(__file__).parent / "fixtures" / "config_simple.yml"
        
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")
        
        # Load YAML
        with open(fixture_path) as f:
            data = yaml.safe_load(f)
        
        # Parse config
        config = Config.from_dict(data)
        
        # Build state
        builder = DesiredStateBuilder(environment="test")
        state = builder.build(config)
        
        # Verify
        assert state.environment == "test"
        assert state.has_resource("project.TEST_PROJECT")
        assert state.has_resource("dataset.TEST_PROJECT.TEST_DATASET")
        assert state.has_resource("recipe.TEST_PROJECT.prep_data")

    def test_build_from_complete_yaml(self):
        """Test building state from complete YAML fixture"""
        fixture_path = Path(__file__).parent / "fixtures" / "config_complete.yml"
        
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")
        
        # Load YAML
        with open(fixture_path) as f:
            data = yaml.safe_load(f)
        
        # Parse config
        config = Config.from_dict(data)
        
        # Build state
        builder = DesiredStateBuilder(environment="prod")
        state = builder.build(config)
        
        # Verify
        assert state.environment == "prod"
        assert len(state.resources) == 6  # 1 project + 3 datasets + 2 recipes
        
        # Verify project
        project = state.get_resource("project.CUSTOMER_ANALYTICS")
        assert project.attributes["name"] == "Customer Analytics Project"
        assert project.attributes["settings"]["exposed"] == True
        
        # Verify datasets
        raw_ds = state.get_resource("dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS")
        assert raw_ds.attributes["type"] == "snowflake"
        assert raw_ds.attributes["connection"] == "snowflake_prod"
        
        cleaned_ds = state.get_resource("dataset.CUSTOMER_ANALYTICS.CLEANED_CUSTOMERS")
        assert cleaned_ds.attributes["type"] == "managed"
        assert cleaned_ds.attributes["formatType"] == "parquet"
        
        # Verify recipes
        clean_recipe = state.get_resource("recipe.CUSTOMER_ANALYTICS.clean_customers")
        assert clean_recipe.attributes["type"] == "python"
        assert clean_recipe.attributes["inputs"] == ["RAW_CUSTOMERS"]
        assert clean_recipe.attributes["outputs"] == ["CLEANED_CUSTOMERS"]
        
        metrics_recipe = state.get_resource("recipe.CUSTOMER_ANALYTICS.compute_metrics")
        assert metrics_recipe.attributes["type"] == "sql"
