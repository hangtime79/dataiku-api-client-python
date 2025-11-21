"""
State management models

Tracks desired vs. actual state and calculates diffs.
"""

from dataclasses import dataclass, field
from typing import Set, Dict, Any, List
from enum import Enum


class ChangeType(Enum):
    """Type of change to a resource"""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    NONE = "none"


@dataclass
class ResourceState:
    """State of a single resource"""

    name: str
    type: str  # dataset, recipe, scenario, etc.
    properties: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.name, self.type))

    def __eq__(self, other):
        if not isinstance(other, ResourceState):
            return False
        return self.name == other.name and self.type == other.type


@dataclass
class State:
    """
    Current or desired state of a Dataiku project.

    Represents all resources in a project at a point in time.
    """

    project_key: str = ""
    datasets: Set[str] = field(default_factory=set)
    recipes: Set[str] = field(default_factory=set)
    scenarios: Set[str] = field(default_factory=set)

    # Detailed resource information
    dataset_details: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    recipe_details: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    scenario_details: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Export state to dictionary"""
        return {
            "project_key": self.project_key,
            "datasets": sorted(list(self.datasets)),
            "recipes": sorted(list(self.recipes)),
            "scenarios": sorted(list(self.scenarios)),
            "dataset_details": self.dataset_details,
            "recipe_details": self.recipe_details,
            "scenario_details": self.scenario_details,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "State":
        """Load state from dictionary"""
        return cls(
            project_key=data.get("project_key", ""),
            datasets=set(data.get("datasets", [])),
            recipes=set(data.get("recipes", [])),
            scenarios=set(data.get("scenarios", [])),
            dataset_details=data.get("dataset_details", {}),
            recipe_details=data.get("recipe_details", {}),
            scenario_details=data.get("scenario_details", {}),
        )

    def resource_count(self) -> int:
        """Total number of resources"""
        return len(self.datasets) + len(self.recipes) + len(self.scenarios)

    def is_empty(self) -> bool:
        """Check if state has any resources"""
        return self.resource_count() == 0


@dataclass
class ResourceChange:
    """Details of a change to a resource"""

    resource_type: str  # dataset, recipe, scenario
    name: str
    change_type: ChangeType
    current_state: Dict[str, Any] = field(default_factory=dict)
    desired_state: Dict[str, Any] = field(default_factory=dict)
    diff: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Export change to dictionary"""
        return {
            "resource_type": self.resource_type,
            "name": self.name,
            "change_type": self.change_type.value,
            "current_state": self.current_state,
            "desired_state": self.desired_state,
            "diff": self.diff,
        }

    def summary(self) -> str:
        """Human-readable summary"""
        type_emoji = {
            ChangeType.CREATE: "+",
            ChangeType.UPDATE: "~",
            ChangeType.DELETE: "-",
            ChangeType.NONE: "=",
        }
        emoji = type_emoji.get(self.change_type, "?")
        return f"{emoji} {self.resource_type}: {self.name}"


@dataclass
class Diff:
    """
    Difference between current and desired state.

    Tracks what resources need to be created, updated, or deleted.
    """

    # Resource names by change type
    create_datasets: Set[str] = field(default_factory=set)
    update_datasets: Set[str] = field(default_factory=set)
    delete_datasets: Set[str] = field(default_factory=set)

    create_recipes: Set[str] = field(default_factory=set)
    update_recipes: Set[str] = field(default_factory=set)
    delete_recipes: Set[str] = field(default_factory=set)

    create_scenarios: Set[str] = field(default_factory=set)
    update_scenarios: Set[str] = field(default_factory=set)
    delete_scenarios: Set[str] = field(default_factory=set)

    # Detailed changes
    changes: List[ResourceChange] = field(default_factory=list)

    def has_changes(self) -> bool:
        """Check if there are any changes"""
        return (
            bool(self.create_datasets)
            or bool(self.update_datasets)
            or bool(self.delete_datasets)
            or bool(self.create_recipes)
            or bool(self.update_recipes)
            or bool(self.delete_recipes)
            or bool(self.create_scenarios)
            or bool(self.update_scenarios)
            or bool(self.delete_scenarios)
        )

    def total_changes(self) -> int:
        """Total number of changes"""
        return (
            len(self.create_datasets)
            + len(self.update_datasets)
            + len(self.delete_datasets)
            + len(self.create_recipes)
            + len(self.update_recipes)
            + len(self.delete_recipes)
            + len(self.create_scenarios)
            + len(self.update_scenarios)
            + len(self.delete_scenarios)
        )

    def summary(self) -> dict:
        """Summary statistics"""
        return {
            "datasets": {
                "create": len(self.create_datasets),
                "update": len(self.update_datasets),
                "delete": len(self.delete_datasets),
            },
            "recipes": {
                "create": len(self.create_recipes),
                "update": len(self.update_recipes),
                "delete": len(self.delete_recipes),
            },
            "scenarios": {
                "create": len(self.create_scenarios),
                "update": len(self.update_scenarios),
                "delete": len(self.delete_scenarios),
            },
            "total": self.total_changes(),
        }

    def to_markdown(self) -> str:
        """Format diff as markdown"""
        lines = ["# Planned Changes\n"]

        if not self.has_changes():
            lines.append("No changes required - state already matches configuration.\n")
            return "\n".join(lines)

        # Datasets
        if self.create_datasets or self.update_datasets or self.delete_datasets:
            lines.append("## Datasets\n")
            for name in sorted(self.create_datasets):
                lines.append(f"+ **{name}** (create)")
            for name in sorted(self.update_datasets):
                lines.append(f"~ **{name}** (update)")
            for name in sorted(self.delete_datasets):
                lines.append(f"- **{name}** (delete)")
            lines.append("")

        # Recipes
        if self.create_recipes or self.update_recipes or self.delete_recipes:
            lines.append("## Recipes\n")
            for name in sorted(self.create_recipes):
                lines.append(f"+ **{name}** (create)")
            for name in sorted(self.update_recipes):
                lines.append(f"~ **{name}** (update)")
            for name in sorted(self.delete_recipes):
                lines.append(f"- **{name}** (delete)")
            lines.append("")

        # Scenarios
        if self.create_scenarios or self.update_scenarios or self.delete_scenarios:
            lines.append("## Scenarios\n")
            for name in sorted(self.create_scenarios):
                lines.append(f"+ **{name}** (create)")
            for name in sorted(self.update_scenarios):
                lines.append(f"~ **{name}** (update)")
            for name in sorted(self.delete_scenarios):
                lines.append(f"- **{name}** (delete)")
            lines.append("")

        # Summary
        summary = self.summary()
        lines.append("## Summary\n")
        lines.append(f"**Total changes:** {summary['total']}\n")
        lines.append(
            f"- Datasets: {summary['datasets']['create']} create, "
            f"{summary['datasets']['update']} update, "
            f"{summary['datasets']['delete']} delete"
        )
        lines.append(
            f"- Recipes: {summary['recipes']['create']} create, "
            f"{summary['recipes']['update']} update, "
            f"{summary['recipes']['delete']} delete"
        )
        lines.append(
            f"- Scenarios: {summary['scenarios']['create']} create, "
            f"{summary['scenarios']['update']} update, "
            f"{summary['scenarios']['delete']} delete"
        )

        return "\n".join(lines)


def calculate_diff(current: State, desired: State) -> Diff:
    """
    Calculate difference between current and desired state.

    Args:
        current: Current state from Dataiku
        desired: Desired state from config

    Returns:
        Diff object with changes needed
    """
    diff = Diff()

    # Datasets
    diff.create_datasets = desired.datasets - current.datasets
    diff.delete_datasets = current.datasets - desired.datasets
    diff.update_datasets = current.datasets & desired.datasets  # Potentially updated

    # Recipes
    diff.create_recipes = desired.recipes - current.recipes
    diff.delete_recipes = current.recipes - desired.recipes
    diff.update_recipes = current.recipes & desired.recipes  # Potentially updated

    # Scenarios
    diff.create_scenarios = desired.scenarios - current.scenarios
    diff.delete_scenarios = current.scenarios - desired.scenarios
    diff.update_scenarios = current.scenarios & desired.scenarios  # Potentially updated

    # Build detailed changes list
    for name in diff.create_datasets:
        diff.changes.append(
            ResourceChange(
                resource_type="dataset",
                name=name,
                change_type=ChangeType.CREATE,
                desired_state=desired.dataset_details.get(name, {}),
            )
        )

    for name in diff.update_datasets:
        diff.changes.append(
            ResourceChange(
                resource_type="dataset",
                name=name,
                change_type=ChangeType.UPDATE,
                current_state=current.dataset_details.get(name, {}),
                desired_state=desired.dataset_details.get(name, {}),
            )
        )

    for name in diff.delete_datasets:
        diff.changes.append(
            ResourceChange(
                resource_type="dataset",
                name=name,
                change_type=ChangeType.DELETE,
                current_state=current.dataset_details.get(name, {}),
            )
        )

    # Similar for recipes and scenarios...
    # (Abbreviated for brevity)

    return diff
