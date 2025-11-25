"""
Plan formatting for Dataiku IaC.

This module provides human-readable formatting for execution plans:
- PlanFormatter: Terraform-style output with color coding and symbols
"""

from typing import TextIO, Any
import sys
from .models import ExecutionPlan, PlannedAction, ActionType


class PlanFormatter:
    """
    Format execution plans for human-readable output.

    Terraform-style output with color coding and symbols.
    
    Symbols:
        + : CREATE
        ~ : UPDATE
        - : DELETE
        
    Colors:
        Green: CREATE
        Yellow: UPDATE
        Red: DELETE
    """

    # ANSI color codes
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Action symbols
    SYMBOLS = {
        ActionType.CREATE: "+",
        ActionType.UPDATE: "~",
        ActionType.DELETE: "-",
        ActionType.NO_CHANGE: " "
    }

    def __init__(self, color: bool = True):
        """
        Initialize formatter.

        Args:
            color: Enable color output (disable for CI/logs)
        """
        self.color = color

    def format(self, plan: ExecutionPlan, output: TextIO = sys.stdout) -> None:
        """
        Format plan to output stream.

        Args:
            plan: ExecutionPlan to format
            output: Output stream (default: stdout)
        """
        # Header
        output.write(self._format_header(plan))
        output.write("\n\n")

        # Actions (skip NO_CHANGE)
        for action in plan.actions:
            if action.action_type != ActionType.NO_CHANGE:
                output.write(self._format_action(action))
                output.write("\n")

        # Summary
        output.write("\n")
        output.write(self._format_summary(plan))
        output.write("\n")

    def _format_header(self, plan: ExecutionPlan) -> str:
        """Format plan header."""
        if self.color:
            return f"{self.BOLD}Dataiku IaC Execution Plan{self.RESET}"
        else:
            return "Dataiku IaC Execution Plan"

    def _format_action(self, action: PlannedAction) -> str:
        """
        Format single action.

        Example outputs:
          + project.CUSTOMER_ANALYTICS
              name: "Customer Analytics"
              description: "Customer analytics pipeline"

          ~ dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS
              ~ description: "Raw data" => "Raw customer data"
              ~ schema.columns[0].type: "int" => "bigint"

          - recipe.CUSTOMER_ANALYTICS.old_recipe
        """
        symbol = self.SYMBOLS[action.action_type]
        color = self._get_color(action.action_type)
        reset = self.RESET if self.color else ""

        lines = []

        # Action line
        lines.append(f"{color}{symbol} {action.resource_id}{reset}")

        # Handle different action types
        if action.action_type == ActionType.CREATE:
            # For CREATE: show new resource attributes
            if action.diff.new_resource and action.diff.new_resource.attributes:
                for key, value in action.diff.new_resource.attributes.items():
                    if key not in ["checksum"]:  # Skip internal fields
                        formatted_value = self._format_value(value)
                        lines.append(f"    {key}: {formatted_value}")

        elif action.action_type == ActionType.UPDATE:
            # For UPDATE: show attribute changes (old => new)
            if action.diff.attribute_diffs:
                for attr_key, attr_change in action.diff.attribute_diffs.items():
                    old_value = self._format_value(attr_change.get("old"))
                    new_value = self._format_value(attr_change.get("new"))
                    lines.append(f"    {color}~{reset} {attr_key}: {old_value} => {new_value}")

        # For DELETE: just show the resource ID (already in action line)

        return "\n".join(lines)

    def _format_summary(self, plan: ExecutionPlan) -> str:
        """
        Format plan summary.

        Example:
          Plan: 2 to create, 1 to update, 0 to destroy.
        """
        summary = plan.summary()

        # Check if there are any changes
        if not plan.has_changes():
            if self.color:
                return f"{self.BOLD}No changes. Infrastructure is up-to-date.{self.RESET}"
            else:
                return "No changes. Infrastructure is up-to-date."

        # Build summary parts
        parts = []
        if summary.get("create", 0) > 0:
            count = summary["create"]
            text = f"{count} to create"
            if self.color:
                parts.append(f"{self.GREEN}{text}{self.RESET}")
            else:
                parts.append(text)
                
        if summary.get("update", 0) > 0:
            count = summary["update"]
            text = f"{count} to update"
            if self.color:
                parts.append(f"{self.YELLOW}{text}{self.RESET}")
            else:
                parts.append(text)
                
        if summary.get("delete", 0) > 0:
            count = summary["delete"]
            text = f"{count} to destroy"
            if self.color:
                parts.append(f"{self.RED}{text}{self.RESET}")
            else:
                parts.append(text)

        summary_text = ", ".join(parts) + "."
        
        if self.color:
            return f"{self.BOLD}Plan:{self.RESET} {summary_text}"
        else:
            return f"Plan: {summary_text}"

    def _get_color(self, action_type: ActionType) -> str:
        """Get color for action type."""
        if not self.color:
            return ""

        return {
            ActionType.CREATE: self.GREEN,
            ActionType.UPDATE: self.YELLOW,
            ActionType.DELETE: self.RED,
            ActionType.NO_CHANGE: self.RESET
        }.get(action_type, self.RESET)

    def _format_value(self, value: Any) -> str:
        """Format attribute value for display."""
        if value is None:
            return "null"
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (list, dict)):
            # Truncate complex types
            return "..."
        else:
            return str(value)
