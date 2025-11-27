"""
Desired State Builder for Dataiku IaC.

Converts declarative configuration (Config objects) into internal State model
that can be compared with current Dataiku state.
"""

from datetime import datetime

from .models import Config, ProjectConfig, DatasetConfig, RecipeConfig
from ..models.state import State, Resource, ResourceMetadata, make_resource_id
from ..exceptions import BuildError


class DesiredStateBuilder:
    """
    Build State object from Config.

    Converts declarative configuration into internal State model
    that can be compared with current Dataiku state.
    """

    def __init__(self, environment: str = "default"):
        """
        Initialize builder.

        Args:
            environment: Target environment name
        """
        self.environment = environment

    def build(self, config: Config) -> State:
        """
        Build State from Config.

        Args:
            config: Validated configuration

        Returns:
            State object representing desired state

        Raises:
            BuildError: If conversion fails
        """
        try:
            state = State(environment=self.environment)

            # Validate project exists
            if not config.project:
                raise BuildError("Configuration must include a project")

            project_key = config.project.key

            # Build project resource
            resource = self._build_project(config.project)
            state.add_resource(resource)

            # Build dataset resources
            for dataset_cfg in config.datasets:
                resource = self._build_dataset(dataset_cfg, project_key)
                state.add_resource(resource)

            # Build recipe resources
            for recipe_cfg in config.recipes:
                resource = self._build_recipe(recipe_cfg, project_key)
                state.add_resource(resource)

            return state

        except BuildError:
            raise
        except Exception as e:
            raise BuildError(f"Failed to build state from config: {e}") from e

    def _build_project(self, cfg: ProjectConfig) -> Resource:
        """
        Convert ProjectConfig to Resource.

        Args:
            cfg: Project configuration

        Returns:
            Resource object for project
        """
        resource_id = make_resource_id("project", cfg.key)

        attributes = {
            "projectKey": cfg.key,
            "name": cfg.name,
            "description": cfg.description,
            "settings": cfg.settings
        }

        metadata = ResourceMetadata(
            deployed_at=datetime.utcnow(),
            deployed_by="config",
            dataiku_internal_id=None,
            checksum=""
        )

        return Resource(
            resource_id=resource_id,
            resource_type="project",
            attributes=attributes,
            metadata=metadata
        )

    def _build_dataset(self, cfg: DatasetConfig, project_key: str) -> Resource:
        """
        Convert DatasetConfig to Resource.

        Args:
            cfg: Dataset configuration
            project_key: Project key this dataset belongs to

        Returns:
            Resource object for dataset
        """
        resource_id = make_resource_id("dataset", project_key, cfg.name)

        attributes = {
            "name": cfg.name,
            "type": cfg.type,
            "params": cfg.params
        }

        # Add optional attributes if present
        if cfg.connection:
            attributes["connection"] = cfg.connection
        if cfg.schema:
            attributes["schema"] = cfg.schema
        if cfg.format_type:
            attributes["formatType"] = cfg.format_type

        metadata = ResourceMetadata(
            deployed_at=datetime.utcnow(),
            deployed_by="config",
            dataiku_internal_id=None,
            checksum=""
        )

        return Resource(
            resource_id=resource_id,
            resource_type="dataset",
            attributes=attributes,
            metadata=metadata
        )

    def _build_recipe(self, cfg: RecipeConfig, project_key: str) -> Resource:
        """
        Convert RecipeConfig to Resource.

        Args:
            cfg: Recipe configuration
            project_key: Project key this recipe belongs to

        Returns:
            Resource object for recipe
        """
        resource_id = make_resource_id("recipe", project_key, cfg.name)

        attributes = {
            "name": cfg.name,
            "type": cfg.type,
            "inputs": cfg.inputs,
            "outputs": cfg.outputs,
            "params": cfg.params
        }

        # Add code if present (for code recipes like python/sql)
        if cfg.code:
            attributes["code"] = cfg.code

        metadata = ResourceMetadata(
            deployed_at=datetime.utcnow(),
            deployed_by="config",
            dataiku_internal_id=None,
            checksum=""
        )

        return Resource(
            resource_id=resource_id,
            resource_type="recipe",
            attributes=attributes,
            metadata=metadata
        )
