"""
Dataiku Infrastructure as Code (IaC) module.

This module provides infrastructure-as-code capabilities for Dataiku,
including state management, resource synchronization, and diff detection.
"""

from .models import State, Resource, ResourceMetadata, make_resource_id, ChangeType, ResourceDiff
from .diff import DiffEngine
from .manager import StateManager
from .config import (
    ProjectConfig,
    DatasetConfig,
    RecipeConfig,
    Config,
    ConfigParser,
    DesiredStateBuilder,
)
from .planner import (
    ActionType,
    PlannedAction,
    ExecutionPlan,
    PlanGenerator,
)
from .exceptions import (
    DataikuIaCError,
    StateNotFoundError,
    StateCorruptedError,
    StateWriteError,
    ResourceNotFoundError,
    ConfigParseError,
    ConfigValidationError,
    BuildError,
)

__all__ = [
    # Models
    'State',
    'Resource',
    'ResourceMetadata',
    'make_resource_id',
    'ChangeType',
    'ResourceDiff',
    # Config Models
    'ProjectConfig',
    'DatasetConfig',
    'RecipeConfig',
    'Config',
    'ConfigParser',
    # Diff Engine
    'DiffEngine',
    # State Manager
    'StateManager',
    # Config Builder
    'DesiredStateBuilder',
    # Planner
    'ActionType',
    'PlannedAction',
    'ExecutionPlan',
    'PlanGenerator',
    # Exceptions
    'DataikuIaCError',
    'StateNotFoundError',
    'StateCorruptedError',
    'StateWriteError',
    'ResourceNotFoundError',
    'ConfigParseError',
    'ConfigValidationError',
    'BuildError',
]
