"""
Plan generation engine for Dataiku IaC.

This module provides the PlanGenerator class for comparing desired state
vs current state and producing ordered execution plans.
"""

from typing import List
from ..models.state import State
from ..diff import DiffEngine
from ..models.diff import ChangeType
from .models import ExecutionPlan, PlannedAction, ActionType


class PlanGenerator:
    """
    Generate execution plans.

    Compares desired state vs current state and produces
    ordered list of actions to achieve desired state.
    """

    def __init__(self):
        """Initialize plan generator with diff engine."""
        self.diff_engine = DiffEngine()

    def generate_plan(
        self,
        current_state: State,
        desired_state: State
    ) -> ExecutionPlan:
        """
        Generate execution plan.

        Args:
            current_state: Current state from Dataiku
            desired_state: Desired state from config

        Returns:
            ExecutionPlan with ordered actions
        """
        # Compute diffs
        diffs = self.diff_engine.diff(current_state, desired_state)

        # Convert diffs to actions
        actions = []
        for diff in diffs:
            action = self._diff_to_action(diff)
            actions.append(action)

        # Compute dependencies
        actions = self._compute_dependencies(actions, desired_state)

        # Order actions by dependencies
        ordered_actions = self._order_by_dependencies(actions)

        return ExecutionPlan(
            actions=ordered_actions,
            metadata={
                "current_serial": current_state.serial,
                "desired_serial": desired_state.serial,
                "total_actions": len(ordered_actions),
                "has_changes": any(a.action_type != ActionType.NO_CHANGE for a in ordered_actions)
            }
        )

    def _diff_to_action(self, diff) -> PlannedAction:
        """
        Convert ResourceDiff to PlannedAction.

        Args:
            diff: ResourceDiff object

        Returns:
            PlannedAction with appropriate action type
        """
        action_map = {
            ChangeType.ADDED: ActionType.CREATE,
            ChangeType.REMOVED: ActionType.DELETE,
            ChangeType.MODIFIED: ActionType.UPDATE,
            ChangeType.UNCHANGED: ActionType.NO_CHANGE
        }

        return PlannedAction(
            action_type=action_map[diff.change_type],
            resource_id=diff.resource_id,
            resource_type=diff.resource_type,
            diff=diff
        )

    def _compute_dependencies(
        self,
        actions: List[PlannedAction],
        desired_state: State
    ) -> List[PlannedAction]:
        """
        Compute dependencies for each action.

        Args:
            actions: List of planned actions
            desired_state: Desired state to analyze for dependencies

        Returns:
            Actions with dependencies populated
        """
        for action in actions:
            deps = self._get_resource_dependencies(action, desired_state)
            action.dependencies = deps

        return actions

    def _get_resource_dependencies(
        self,
        action: PlannedAction,
        state: State
    ) -> List[str]:
        """
        Get dependencies for a resource.

        Dependencies:
        - Projects have no dependencies
        - Datasets depend on their project
        - Recipes depend on their project and input datasets

        Args:
            action: PlannedAction to analyze
            state: State containing resource information

        Returns:
            List of resource IDs this action depends on
        """
        deps = []
        resource_type = action.resource_type
        resource_id = action.resource_id

        # Extract parts from resource_id
        parts = resource_id.split('.')
        if len(parts) < 2:
            return deps

        project_key = parts[1]

        # All non-project resources depend on their project
        if resource_type != "project":
            project_id = f"project.{project_key}"
            deps.append(project_id)

        # Recipes depend on their input datasets
        if resource_type == "recipe":
            resource = state.get_resource(resource_id)
            if resource and action.action_type in [ActionType.CREATE, ActionType.UPDATE]:
                # Get inputs from resource attributes
                inputs = resource.attributes.get("inputs", [])
                for input_ref in inputs:
                    # Input refs might be dataset names or full refs
                    if isinstance(input_ref, str):
                        # Assume it's a dataset name in the same project
                        dataset_id = f"dataset.{project_key}.{input_ref}"
                        deps.append(dataset_id)
                    elif isinstance(input_ref, dict):
                        # Handle structured input refs
                        input_name = input_ref.get("ref", "")
                        if input_name:
                            dataset_id = f"dataset.{project_key}.{input_name}"
                            deps.append(dataset_id)

        return deps

    def _order_by_dependencies(
        self,
        actions: List[PlannedAction]
    ) -> List[PlannedAction]:
        """
        Order actions respecting dependencies.

        Ordering rules:
        1. Projects before datasets/recipes
        2. Datasets before recipes that use them
        3. Creates before updates
        4. Deletes after everything else

        Args:
            actions: List of actions to order

        Returns:
            Ordered list of actions
        """
        # Separate by action type
        creates = [a for a in actions if a.action_type == ActionType.CREATE]
        updates = [a for a in actions if a.action_type == ActionType.UPDATE]
        deletes = [a for a in actions if a.action_type == ActionType.DELETE]
        no_changes = [a for a in actions if a.action_type == ActionType.NO_CHANGE]

        # Order creates by dependencies (topological sort)
        ordered_creates = self._topological_sort(creates)

        # Order updates by dependencies
        ordered_updates = self._topological_sort(updates)

        # Order deletes in reverse (delete children before parents)
        ordered_deletes = self._topological_sort(deletes, reverse=True)

        # Combine in order: creates, updates, deletes, no-changes
        return ordered_creates + ordered_updates + ordered_deletes + no_changes

    def _topological_sort(
        self,
        actions: List[PlannedAction],
        reverse: bool = False
    ) -> List[PlannedAction]:
        """
        Topological sort of actions based on dependencies.

        Args:
            actions: List of actions to sort
            reverse: If True, reverse dependency order (for deletes)

        Returns:
            Sorted list of actions
        """
        if not actions:
            return []

        # Build action map
        action_map = {a.resource_id: a for a in actions}

        # Build dependency graph
        graph = {}
        in_degree = {}

        for action in actions:
            resource_id = action.resource_id
            graph[resource_id] = []
            in_degree[resource_id] = 0

        # Add edges
        for action in actions:
            resource_id = action.resource_id
            deps = action.dependencies if not reverse else []

            # Filter dependencies to only those in our action list
            valid_deps = [d for d in deps if d in action_map]

            if reverse:
                # For reverse (deletes), reverse the edges
                for dep in valid_deps:
                    graph[dep].append(resource_id)
                    in_degree[resource_id] += 1
            else:
                # Normal order
                graph[resource_id] = valid_deps
                in_degree[resource_id] = len(valid_deps)

        # Kahn's algorithm for topological sort
        queue = [rid for rid in in_degree if in_degree[rid] == 0]
        result = []

        # Sort queue for deterministic ordering
        # Priority: projects, then datasets, then recipes
        def get_priority(resource_id: str) -> tuple:
            parts = resource_id.split('.')
            resource_type = parts[0] if parts else ""

            type_order = {
                "project": 0,
                "dataset": 1,
                "recipe": 2,
                "model": 3,
            }

            return (type_order.get(resource_type, 99), resource_id)

        while queue:
            # Sort queue by priority
            queue.sort(key=get_priority)

            # Pop first item
            current = queue.pop(0)
            result.append(action_map[current])

            # Process neighbors
            if not reverse:
                # For normal order, check what depends on current
                for action in actions:
                    if current in action.dependencies:
                        in_degree[action.resource_id] -= 1
                        if in_degree[action.resource_id] == 0:
                            queue.append(action.resource_id)
            else:
                # For reverse order, use the graph
                for neighbor in graph[current]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        # Check for cycles
        if len(result) != len(actions):
            # Circular dependency detected
            # Return actions sorted by type priority for now
            return sorted(actions, key=lambda a: get_priority(a.resource_id))

        return result
