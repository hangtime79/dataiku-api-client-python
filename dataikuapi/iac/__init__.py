"""
Dataiku Infrastructure as Code (IaC) module.

This module provides infrastructure-as-code capabilities for Dataiku,
including state management, resource synchronization, and diff detection.
"""

from .models import State, Resource, ResourceMetadata, make_resource_id, ChangeType, ResourceDiff
from .diff import DiffEngine
from .exceptions import (
    DataikuIaCError,
    StateNotFoundError,
    StateCorruptedError,
    StateWriteError,
    ResourceNotFoundError,
)

__all__ = [
    # Models
    'State',
    'Resource',
    'ResourceMetadata',
    'make_resource_id',
    'ChangeType',
    'ResourceDiff',
    # Diff Engine
    'DiffEngine',
    # Exceptions
    'DataikuIaCError',
    'StateNotFoundError',
    'StateCorruptedError',
    'StateWriteError',
    'ResourceNotFoundError',
]
