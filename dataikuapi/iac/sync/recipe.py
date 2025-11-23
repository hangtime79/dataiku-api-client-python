"""
Recipe synchronization from Dataiku to state.
"""

from typing import Optional
from datetime import datetime

from .base import ResourceSync
from ..models import Resource, ResourceMetadata, make_resource_id
from ..exceptions import ResourceNotFoundError


class RecipeSync(ResourceSync):
    """Sync recipes from Dataiku"""

    @property
    def resource_type(self) -> str:
        return "recipe"

    def fetch(self, resource_id: str) -> Resource:
        """
        Fetch recipe from Dataiku.

        Args:
            resource_id: "recipe.PROJECT_KEY.RECIPE_NAME"

        Returns:
            Resource object with recipe attributes

        Raises:
            ResourceNotFoundError: If recipe doesn't exist
            ValueError: If resource_id format is invalid
        """
        # Parse resource_id
        parts = resource_id.split('.')
        if len(parts) != 3 or parts[0] != "recipe":
            raise ValueError(f"Invalid recipe resource_id: {resource_id}")

        project_key = parts[1]
        recipe_name = parts[2]

        try:
            # Get recipe from Dataiku
            project = self.client.get_project(project_key)
            recipe = project.get_recipe(recipe_name)

            # Get settings
            settings = recipe.get_settings()

            # Get payload (code for code recipes)
            payload = None
            recipe_type = settings.settings.get("type", "")
            if recipe_type in ["python", "sql", "r"]:
                try:
                    payload = recipe.get_payload()
                except:
                    payload = None

            # Build attributes dict
            attributes = {
                "name": recipe_name,
                "type": recipe_type,
                "inputs": settings.settings.get("inputs", {}),
                "outputs": settings.settings.get("outputs", {}),
                "params": settings.settings.get("params", {}),
                "tags": settings.settings.get("tags", []),
            }

            # Include code if available
            if payload is not None:
                attributes["payload"] = payload

            # Create resource
            metadata = ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="system",
                dataiku_internal_id=recipe_name
            )

            return Resource(
                resource_type="recipe",
                resource_id=resource_id,
                attributes=attributes,
                metadata=metadata
            )

        except Exception as e:
            raise ResourceNotFoundError(
                f"Recipe {project_key}.{recipe_name} not found: {e}"
            )

    def list_all(self, project_key: Optional[str] = None) -> list:
        """
        List all recipes, optionally filtered by project.

        Args:
            project_key: Required for listing recipes

        Returns:
            List of Resource objects for all recipes in the project

        Raises:
            ValueError: If project_key is not provided
            RuntimeError: If listing recipes fails
        """
        if not project_key:
            raise ValueError("project_key required for listing recipes")

        try:
            project = self.client.get_project(project_key)
            recipes = project.list_recipes()
            resources = []

            for recipe_info in recipes:
                recipe_name = recipe_info["name"]
                resource_id = make_resource_id("recipe", project_key, recipe_name)

                # Fetch full details
                resource = self.fetch(resource_id)
                resources.append(resource)

            return resources

        except Exception as e:
            raise RuntimeError(f"Failed to list recipes for {project_key}: {e}")
