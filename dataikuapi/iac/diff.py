"""
DiffEngine for comparing Dataiku IaC states.

This module provides the DiffEngine class for comparing two State objects
and identifying changes (added, removed, modified, unchanged resources).
"""

from typing import List
from .models.state import State
from .models.diff import ChangeType, ResourceDiff


class DiffEngine:
    """
    Compare two states and generate diff.

    Identifies:
        - Resources added in new state
        - Resources removed from old state
        - Resources modified between states
        - Resources unchanged
    """

    def diff(self, old_state: State, new_state: State) -> List[ResourceDiff]:
        """
        Compare two states.

        Args:
            old_state: Previous state
            new_state: Current state

        Returns:
            List of ResourceDiff objects
        """
        diffs = []

        old_ids = set(old_state.resources.keys())
        new_ids = set(new_state.resources.keys())

        # Resources added
        for resource_id in new_ids - old_ids:
            diffs.append(
                ResourceDiff(
                    change_type=ChangeType.ADDED,
                    resource_id=resource_id,
                    resource_type=new_state.resources[resource_id].resource_type,
                    new_resource=new_state.resources[resource_id],
                )
            )

        # Resources removed
        for resource_id in old_ids - new_ids:
            diffs.append(
                ResourceDiff(
                    change_type=ChangeType.REMOVED,
                    resource_id=resource_id,
                    resource_type=old_state.resources[resource_id].resource_type,
                    old_resource=old_state.resources[resource_id],
                )
            )

        # Resources potentially modified
        for resource_id in old_ids & new_ids:
            old_resource = old_state.resources[resource_id]
            new_resource = new_state.resources[resource_id]

            if old_resource.has_changed(new_resource):
                # Detailed attribute diff
                attr_diffs = self._diff_attributes(
                    old_resource.attributes, new_resource.attributes
                )

                diffs.append(
                    ResourceDiff(
                        change_type=ChangeType.MODIFIED,
                        resource_id=resource_id,
                        resource_type=new_resource.resource_type,
                        old_resource=old_resource,
                        new_resource=new_resource,
                        attribute_diffs=attr_diffs,
                    )
                )
            else:
                # Unchanged (optional: exclude from output)
                diffs.append(
                    ResourceDiff(
                        change_type=ChangeType.UNCHANGED,
                        resource_id=resource_id,
                        resource_type=new_resource.resource_type,
                        old_resource=old_resource,
                        new_resource=new_resource,
                    )
                )

        return diffs

    def _diff_attributes(self, old_attrs: dict, new_attrs: dict) -> dict:
        """
        Detailed diff of attribute dictionaries.

        Returns:
            Dict with keys: added, removed, modified
        """
        old_keys = set(old_attrs.keys())
        new_keys = set(new_attrs.keys())

        result = {"added": {}, "removed": {}, "modified": {}}

        # Added attributes
        for key in new_keys - old_keys:
            result["added"][key] = new_attrs[key]

        # Removed attributes
        for key in old_keys - new_keys:
            result["removed"][key] = old_attrs[key]

        # Modified attributes
        for key in old_keys & new_keys:
            if old_attrs[key] != new_attrs[key]:
                result["modified"][key] = {"old": old_attrs[key], "new": new_attrs[key]}

        return result

    def summary(self, diffs: List[ResourceDiff]) -> dict:
        """
        Summarize diffs.

        Returns:
            Dict with counts: {added: N, removed: N, modified: N, unchanged: N}
        """
        summary = {"added": 0, "removed": 0, "modified": 0, "unchanged": 0}

        for diff in diffs:
            summary[diff.change_type.value] += 1

        return summary

    def format_output(
        self, diffs: List[ResourceDiff], include_unchanged: bool = False
    ) -> str:
        """
        Format diffs for human readability.

        Args:
            diffs: List of diffs
            include_unchanged: Show unchanged resources

        Returns:
            Formatted string
        """
        lines = []

        # Summary
        summary = self.summary(diffs)
        lines.append("Diff Summary:")
        lines.append(f"  {summary['added']} added")
        lines.append(f"  {summary['removed']} removed")
        lines.append(f"  {summary['modified']} modified")
        if include_unchanged:
            lines.append(f"  {summary['unchanged']} unchanged")
        lines.append("")

        # Details
        for diff in diffs:
            if diff.change_type == ChangeType.UNCHANGED and not include_unchanged:
                continue

            lines.append(str(diff))

            if diff.change_type == ChangeType.MODIFIED and diff.attribute_diffs:
                for key, change in diff.attribute_diffs.get("modified", {}).items():
                    lines.append(f"    {key}: {change['old']} → {change['new']}")

        return "\n".join(lines)
