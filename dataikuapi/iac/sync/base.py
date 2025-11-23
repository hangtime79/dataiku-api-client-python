"""
Abstract base class for resource synchronization.
"""

from abc import ABC, abstractmethod
from typing import Optional

# Import DSSClient type
try:
    from dataikuapi import DSSClient
except ImportError:
    # For type checking when dataikuapi is not installed
    DSSClient = None

# Import models
from ..models import Resource


class ResourceSync(ABC):
    """
    Abstract interface for syncing resources from Dataiku.

    Each resource type (project, dataset, recipe) has its own implementation.
    """

    def __init__(self, client):
        """
        Args:
            client: Dataiku API client (DSSClient)
        """
        self.client = client

    @abstractmethod
    def fetch(self, resource_id: str) -> Resource:
        """
        Fetch single resource from Dataiku.

        Args:
            resource_id: Full resource ID (e.g., "project.CUSTOMER_ANALYTICS")

        Returns:
            Resource object

        Raises:
            ResourceNotFoundError: If resource doesn't exist in Dataiku
        """
        pass

    @abstractmethod
    def list_all(self, project_key: Optional[str] = None) -> list:
        """
        List all resources of this type.

        Args:
            project_key: Optional filter by project

        Returns:
            List of Resource objects
        """
        pass

    @property
    @abstractmethod
    def resource_type(self) -> str:
        """Resource type identifier"""
        pass
