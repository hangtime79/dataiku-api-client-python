"""
Dataset synchronization from Dataiku to state.
"""

from typing import Optional
from datetime import datetime

from .base import ResourceSync
from ..models import Resource, ResourceMetadata, make_resource_id
from ..exceptions import ResourceNotFoundError


class DatasetSync(ResourceSync):
    """Sync datasets from Dataiku"""

    @property
    def resource_type(self) -> str:
        return "dataset"

    def fetch(self, resource_id: str) -> Resource:
        """
        Fetch dataset from Dataiku.

        Args:
            resource_id: "dataset.PROJECT_KEY.DATASET_NAME"

        Returns:
            Resource object with dataset attributes

        Raises:
            ResourceNotFoundError: If dataset doesn't exist
            ValueError: If resource_id format is invalid
        """
        # Parse resource_id
        parts = resource_id.split('.')
        if len(parts) != 3 or parts[0] != "dataset":
            raise ValueError(f"Invalid dataset resource_id: {resource_id}")

        project_key = parts[1]
        dataset_name = parts[2]

        try:
            # Get dataset from Dataiku
            project = self.client.get_project(project_key)
            dataset = project.get_dataset(dataset_name)

            # Get settings
            settings = dataset.get_settings()

            # Build attributes dict
            attributes = {
                "name": dataset_name,
                "type": settings.settings.get("type", ""),
                "params": settings.settings.get("params", {}),
                "schema": settings.settings.get("schema", {}),
                "formatType": settings.settings.get("formatType", ""),
                "tags": settings.settings.get("tags", []),
            }

            # Create resource
            metadata = ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="system",
                dataiku_internal_id=dataset_name  # Datasets use name within project
            )

            return Resource(
                resource_type="dataset",
                resource_id=resource_id,
                attributes=attributes,
                metadata=metadata
            )

        except Exception as e:
            raise ResourceNotFoundError(
                f"Dataset {project_key}.{dataset_name} not found: {e}"
            )

    def list_all(self, project_key: Optional[str] = None) -> list:
        """
        List all datasets, optionally filtered by project.

        Args:
            project_key: Required for listing datasets

        Returns:
            List of Resource objects for all datasets in the project

        Raises:
            ValueError: If project_key is not provided
            RuntimeError: If listing datasets fails
        """
        if not project_key:
            raise ValueError("project_key required for listing datasets")

        try:
            project = self.client.get_project(project_key)
            datasets = project.list_datasets()
            resources = []

            for dataset_info in datasets:
                dataset_name = dataset_info["name"]
                resource_id = make_resource_id("dataset", project_key, dataset_name)

                # Fetch full details
                resource = self.fetch(resource_id)
                resources.append(resource)

            return resources

        except Exception as e:
            raise RuntimeError(f"Failed to list datasets for {project_key}: {e}")
