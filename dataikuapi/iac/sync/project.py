"""
Project synchronization from Dataiku to state.
"""

from typing import Optional
from datetime import datetime

from .base import ResourceSync
from ..models import Resource, ResourceMetadata, make_resource_id
from ..exceptions import ResourceNotFoundError


class ProjectSync(ResourceSync):
    """Sync projects from Dataiku"""

    @property
    def resource_type(self) -> str:
        return "project"

    def fetch(self, resource_id: str) -> Resource:
        """
        Fetch project from Dataiku.

        Args:
            resource_id: "project.PROJECT_KEY"

        Returns:
            Resource object with project attributes

        Raises:
            ResourceNotFoundError: If project doesn't exist
            ValueError: If resource_id format is invalid
        """
        # Parse resource_id
        parts = resource_id.split('.')
        if len(parts) != 2 or parts[0] != "project":
            raise ValueError(f"Invalid project resource_id: {resource_id}")

        project_key = parts[1]

        try:
            # Get project from Dataiku
            project = self.client.get_project(project_key)

            # Get settings
            settings = project.get_settings()

            # Build attributes dict
            attributes = {
                "projectKey": project_key,
                "name": settings.settings.get("name", ""),
                "description": settings.settings.get("description", ""),
                "shortDesc": settings.settings.get("shortDesc", ""),
                "tags": settings.settings.get("tags", []),
                "checklists": settings.settings.get("checklists", {}),
            }

            # Create resource
            metadata = ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="system",  # TODO: get actual user
                dataiku_internal_id=None  # Projects use key as ID
            )

            return Resource(
                resource_type="project",
                resource_id=resource_id,
                attributes=attributes,
                metadata=metadata
            )

        except Exception as e:
            raise ResourceNotFoundError(f"Project {project_key} not found: {e}")

    def list_all(self, project_key: Optional[str] = None) -> list:
        """
        List all projects (project_key filter ignored for projects).

        Args:
            project_key: Ignored for projects (projects are top-level)

        Returns:
            List of Resource objects for all accessible projects

        Raises:
            RuntimeError: If listing projects fails
        """
        try:
            projects = self.client.list_projects()
            resources = []

            for project_info in projects:
                project_key = project_info["projectKey"]
                resource_id = make_resource_id("project", project_key)

                # Fetch full details for each project
                resource = self.fetch(resource_id)
                resources.append(resource)

            return resources

        except Exception as e:
            raise RuntimeError(f"Failed to list projects: {e}")
