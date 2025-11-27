"""
Diff data models for Dataiku IaC.

This module contains data models for representing changes between states:
- ChangeType: Enum for types of changes
- ResourceDiff: Represents a change to a resource
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

# Import Resource for type hints
# Use TYPE_CHECKING to avoid circular imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import Resource


class ChangeType(Enum):
    """Type of change"""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class ResourceDiff:
    """Represents a change to a resource"""

    change_type: ChangeType
    resource_id: str
    resource_type: str
    old_resource: Optional["Resource"] = None
    new_resource: Optional["Resource"] = None
    attribute_diffs: dict = None

    def __str__(self) -> str:
        """Human-readable representation"""
        symbol = {
            ChangeType.ADDED: "+",
            ChangeType.REMOVED: "-",
            ChangeType.MODIFIED: "~",
            ChangeType.UNCHANGED: " ",
        }[self.change_type]

        return f"{symbol} {self.resource_id}"
