"""
Plan data models for Dataiku IaC.

This module contains data models for representing execution plans:
- ActionType: Enum for types of actions (create, update, delete)
- PlannedAction: Single action in execution plan
- ExecutionPlan: Complete execution plan with ordered actions
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum
from ..models.diff import ResourceDiff


class ActionType(Enum):
    """Type of action in execution plan."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    NO_CHANGE = "no-change"


@dataclass
class PlannedAction:
    """
    Single action in execution plan.

    Attributes:
        action_type: Type of action (create, update, delete, no-change)
        resource_id: Unique identifier for the resource
        resource_type: Type of resource (project, dataset, recipe, etc.)
        diff: ResourceDiff containing the change details
        dependencies: List of resource IDs this action depends on
    """

    action_type: ActionType
    resource_id: str
    resource_type: str
    diff: ResourceDiff
    dependencies: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        """Human-readable action description."""
        symbol = {
            ActionType.CREATE: "+",
            ActionType.UPDATE: "~",
            ActionType.DELETE: "-",
            ActionType.NO_CHANGE: " ",
        }[self.action_type]
        return f"{symbol} {self.resource_id}"


@dataclass
class ExecutionPlan:
    """
    Complete execution plan.

    Ordered list of actions to transform current state
    into desired state.

    Attributes:
        actions: Ordered list of PlannedAction objects
        metadata: Additional metadata about the plan
    """

    actions: List[PlannedAction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> Dict[str, int]:
        """
        Get plan summary.

        Returns:
            Dict with counts: {create: N, update: N, delete: N, no_change: N}
        """
        summary = {"create": 0, "update": 0, "delete": 0, "no_change": 0}

        for action in self.actions:
            if action.action_type == ActionType.CREATE:
                summary["create"] += 1
            elif action.action_type == ActionType.UPDATE:
                summary["update"] += 1
            elif action.action_type == ActionType.DELETE:
                summary["delete"] += 1
            elif action.action_type == ActionType.NO_CHANGE:
                summary["no_change"] += 1

        return summary

    def has_changes(self) -> bool:
        """
        Check if plan has any changes.

        Returns:
            True if plan contains create, update, or delete actions
        """
        return any(a.action_type != ActionType.NO_CHANGE for a in self.actions)
