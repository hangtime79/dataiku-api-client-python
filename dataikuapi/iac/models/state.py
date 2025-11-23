"""
State management data models for Dataiku IaC.

This module contains the core data models for managing Dataiku resource state:
- State: Container for all tracked resources
- Resource: Generic representation of any Dataiku resource
- ResourceMetadata: Tracking metadata for resources
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json


@dataclass
class ResourceMetadata:
    """Tracking metadata for a resource"""
    deployed_at: datetime
    deployed_by: str
    dataiku_internal_id: Optional[str] = None
    checksum: str = ""

    def to_dict(self) -> dict:
        return {
            "deployed_at": self.deployed_at.isoformat(),
            "deployed_by": self.deployed_by,
            "dataiku_internal_id": self.dataiku_internal_id,
            "checksum": self.checksum
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ResourceMetadata':
        return cls(
            deployed_at=datetime.fromisoformat(data["deployed_at"]),
            deployed_by=data["deployed_by"],
            dataiku_internal_id=data.get("dataiku_internal_id"),
            checksum=data.get("checksum", "")
        )


@dataclass
class Resource:
    """
    Generic resource representation.

    Resource ID Format:
        {resource_type}.{project_key}[.{resource_name}]

    Examples:
        - project.CUSTOMER_ANALYTICS
        - dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS
        - recipe.CUSTOMER_ANALYTICS.prep_customers
        - model.CUSTOMER_ANALYTICS.churn_prediction

    Attributes:
        resource_type: Type of resource (project, dataset, recipe, etc.)
        resource_id: Unique identifier (see format above)
        attributes: Resource-specific attributes from Dataiku
        metadata: Tracking metadata (deployment info, checksums, etc.)
    """
    resource_type: str
    resource_id: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    metadata: ResourceMetadata = field(default_factory=lambda: ResourceMetadata(
        deployed_at=datetime.utcnow(),
        deployed_by="system"
    ))

    def __post_init__(self):
        """Validate and compute checksum"""
        self._validate_resource_id()
        if not self.metadata.checksum:
            self.metadata.checksum = self.compute_checksum()

    def _validate_resource_id(self) -> None:
        """Validate resource_id format"""
        parts = self.resource_id.split('.')

        if len(parts) < 2:
            raise ValueError(
                f"Invalid resource_id format: {self.resource_id}. "
                f"Expected: {self.resource_type}.PROJECT_KEY[.RESOURCE_NAME]"
            )

        if parts[0] != self.resource_type:
            raise ValueError(
                f"resource_id prefix '{parts[0]}' doesn't match "
                f"resource_type '{self.resource_type}'"
            )

    def compute_checksum(self) -> str:
        """Compute SHA256 checksum of attributes"""
        # Sort keys for consistent hashing
        normalized = json.dumps(self.attributes, sort_keys=True)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def has_changed(self, other: 'Resource') -> bool:
        """Check if resource has changed compared to another"""
        if self.resource_id != other.resource_id:
            raise ValueError("Cannot compare different resources")
        return self.compute_checksum() != other.compute_checksum()

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        return {
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "attributes": self.attributes,
            "metadata": self.metadata.to_dict()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Resource':
        """Create from dict"""
        return cls(
            resource_type=data["resource_type"],
            resource_id=data["resource_id"],
            attributes=data.get("attributes", {}),
            metadata=ResourceMetadata.from_dict(data.get("metadata", {}))
        )

    @property
    def project_key(self) -> str:
        """Extract project key from resource_id"""
        parts = self.resource_id.split('.')
        return parts[1] if len(parts) > 1 else ""

    @property
    def resource_name(self) -> str:
        """Extract resource name from resource_id"""
        parts = self.resource_id.split('.')
        return '.'.join(parts[2:]) if len(parts) > 2 else ""


def make_resource_id(resource_type: str, project_key: str,
                     resource_name: Optional[str] = None) -> str:
    """
    Helper to construct resource IDs.

    Examples:
        make_resource_id("project", "CUSTOMER_ANALYTICS")
        -> "project.CUSTOMER_ANALYTICS"

        make_resource_id("dataset", "CUSTOMER_ANALYTICS", "RAW_CUSTOMERS")
        -> "dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS"
    """
    if resource_name:
        return f"{resource_type}.{project_key}.{resource_name}"
    return f"{resource_type}.{project_key}"


@dataclass
class State:
    """
    Represents the complete state of tracked Dataiku resources.

    Attributes:
        version: State file format version (currently 1)
        serial: Incrementing counter for state changes
        lineage: Git commit or identifier for tracking
        environment: Target environment (dev, prod, etc.)
        updated_at: Last update timestamp
        resources: Map of resource_id -> Resource
    """
    version: int = 1
    serial: int = 0
    lineage: Optional[str] = None
    environment: str = ""
    updated_at: datetime = field(default_factory=datetime.utcnow)
    resources: Dict[str, 'Resource'] = field(default_factory=dict)

    def get_resource(self, resource_id: str) -> Optional['Resource']:
        """Get resource by ID"""
        return self.resources.get(resource_id)

    def add_resource(self, resource: 'Resource') -> None:
        """Add or update resource"""
        self.resources[resource.resource_id] = resource
        self.serial += 1
        self.updated_at = datetime.utcnow()

    def remove_resource(self, resource_id: str) -> Optional['Resource']:
        """Remove resource, return removed resource or None"""
        resource = self.resources.pop(resource_id, None)
        if resource:
            self.serial += 1
            self.updated_at = datetime.utcnow()
        return resource

    def has_resource(self, resource_id: str) -> bool:
        """Check if resource exists"""
        return resource_id in self.resources

    def list_resources(self, resource_type: Optional[str] = None) -> list['Resource']:
        """List all resources, optionally filtered by type"""
        resources = self.resources.values()
        if resource_type:
            resources = [r for r in resources if r.resource_type == resource_type]
        return list(resources)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        return {
            "version": self.version,
            "serial": self.serial,
            "lineage": self.lineage,
            "environment": self.environment,
            "updated_at": self.updated_at.isoformat(),
            "resources": {
                rid: resource.to_dict()
                for rid, resource in self.resources.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'State':
        """Create from dict"""
        resources = {
            rid: Resource.from_dict(rdata)
            for rid, rdata in data.get("resources", {}).items()
        }
        return cls(
            version=data.get("version", 1),
            serial=data.get("serial", 0),
            lineage=data.get("lineage"),
            environment=data.get("environment", ""),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            resources=resources
        )
