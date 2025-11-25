"""
Tests for Plan Formatter (Package 5).

Tests comprehensive formatting of execution plans including:
- All action types (create, update, delete)
- Color and no-color modes
- Summary formatting
- Empty plans
- Complex plans
- Attribute diff formatting
"""

import pytest
from io import StringIO
from datetime import datetime

from dataikuapi.iac.planner.models import ActionType, PlannedAction, ExecutionPlan
from dataikuapi.iac.planner.formatter import PlanFormatter
from dataikuapi.iac.models.state import Resource, ResourceMetadata, make_resource_id
from dataikuapi.iac.models.diff import ResourceDiff, ChangeType


# Helper functions for test data
def make_resource(resource_type: str, project_key: str, 
                  resource_name: str = None, **attributes) -> Resource:
    """Helper to create test resources."""
    resource_id = make_resource_id(resource_type, project_key, resource_name)
    metadata = ResourceMetadata(
        deployed_at=datetime.utcnow(),
        deployed_by="test"
    )
    return Resource(
        resource_type=resource_type,
        resource_id=resource_id,
        attributes=attributes,
        metadata=metadata
    )


def make_create_action(resource_type: str, project_key: str, 
                       resource_name: str = None, **attributes) -> PlannedAction:
    """Helper to create CREATE action."""
    resource = make_resource(resource_type, project_key, resource_name, **attributes)
    diff = ResourceDiff(
        change_type=ChangeType.ADDED,
        resource_id=resource.resource_id,
        resource_type=resource.resource_type,
        new_resource=resource
    )
    return PlannedAction(
        action_type=ActionType.CREATE,
        resource_id=resource.resource_id,
        resource_type=resource.resource_type,
        diff=diff
    )


def make_update_action(resource_type: str, project_key: str, 
                       resource_name: str = None, 
                       old_attrs: dict = None, 
                       new_attrs: dict = None,
                       attr_diffs: dict = None) -> PlannedAction:
    """Helper to create UPDATE action."""
    resource_id = make_resource_id(resource_type, project_key, resource_name)
    old_resource = make_resource(resource_type, project_key, resource_name, **(old_attrs or {}))
    new_resource = make_resource(resource_type, project_key, resource_name, **(new_attrs or {}))
    
    diff = ResourceDiff(
        change_type=ChangeType.MODIFIED,
        resource_id=resource_id,
        resource_type=resource_type,
        old_resource=old_resource,
        new_resource=new_resource,
        attribute_diffs=attr_diffs or {}
    )
    return PlannedAction(
        action_type=ActionType.UPDATE,
        resource_id=resource_id,
        resource_type=resource_type,
        diff=diff
    )


def make_delete_action(resource_type: str, project_key: str, 
                       resource_name: str = None, **attributes) -> PlannedAction:
    """Helper to create DELETE action."""
    resource = make_resource(resource_type, project_key, resource_name, **attributes)
    diff = ResourceDiff(
        change_type=ChangeType.REMOVED,
        resource_id=resource.resource_id,
        resource_type=resource.resource_type,
        old_resource=resource
    )
    return PlannedAction(
        action_type=ActionType.DELETE,
        resource_id=resource.resource_id,
        resource_type=resource.resource_type,
        diff=diff
    )


class TestPlanFormatterBasics:
    """Test basic formatter functionality."""

    def test_formatter_initialization(self):
        """Test formatter can be initialized."""
        formatter = PlanFormatter(color=True)
        assert formatter.color is True
        
        formatter_no_color = PlanFormatter(color=False)
        assert formatter_no_color.color is False

    def test_format_empty_plan(self):
        """Test formatting an empty plan."""
        plan = ExecutionPlan()
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert "Dataiku IaC Execution Plan" in result
        assert "No changes. Infrastructure is up-to-date." in result

    def test_format_plan_with_no_changes(self):
        """Test plan with NO_CHANGE actions (should be filtered out)."""
        resource = make_resource("project", "TEST_PROJECT", name="Test Project")
        diff = ResourceDiff(
            change_type=ChangeType.UNCHANGED,
            resource_id=resource.resource_id,
            resource_type=resource.resource_type
        )
        action = PlannedAction(
            action_type=ActionType.NO_CHANGE,
            resource_id=resource.resource_id,
            resource_type=resource.resource_type,
            diff=diff
        )
        
        plan = ExecutionPlan(actions=[action])
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert "No changes. Infrastructure is up-to-date." in result
        assert "TEST_PROJECT" not in result  # NO_CHANGE actions are filtered


class TestActionFormatting:
    """Test formatting of individual actions."""

    def test_format_create_action(self):
        """Test formatting CREATE action."""
        action = make_create_action(
            "project", "CUSTOMER_ANALYTICS",
            name="Customer Analytics",
            description="Customer analytics pipeline"
        )
        
        plan = ExecutionPlan(actions=[action])
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert "+ project.CUSTOMER_ANALYTICS" in result
        assert 'name: "Customer Analytics"' in result
        assert 'description: "Customer analytics pipeline"' in result

    def test_format_update_action(self):
        """Test formatting UPDATE action."""
        action = make_update_action(
            "dataset", "CUSTOMER_ANALYTICS", "RAW_CUSTOMERS",
            attr_diffs={
                "description": {"old": "Raw data", "new": "Raw customer data"},
                "format_type": {"old": "csv", "new": "parquet"}
            }
        )
        
        plan = ExecutionPlan(actions=[action])
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert "~ dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS" in result
        assert '~ description: "Raw data" => "Raw customer data"' in result
        assert '~ format_type: "csv" => "parquet"' in result

    def test_format_delete_action(self):
        """Test formatting DELETE action."""
        action = make_delete_action(
            "recipe", "CUSTOMER_ANALYTICS", "old_recipe"
        )
        
        plan = ExecutionPlan(actions=[action])
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert "- recipe.CUSTOMER_ANALYTICS.old_recipe" in result


class TestComplexPlans:
    """Test formatting of complex plans with multiple actions."""

    def test_format_mixed_actions(self):
        """Test plan with create, update, and delete actions."""
        actions = [
            make_create_action("project", "TEST_PROJECT", name="Test"),
            make_update_action("dataset", "TEST_PROJECT", "DATA", 
                             attr_diffs={"description": {"old": "old", "new": "new"}}),
            make_delete_action("recipe", "TEST_PROJECT", "old_recipe")
        ]
        
        plan = ExecutionPlan(actions=actions)
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert "+ project.TEST_PROJECT" in result
        assert "~ dataset.TEST_PROJECT.DATA" in result
        assert "- recipe.TEST_PROJECT.old_recipe" in result
        assert "Plan: 1 to create, 1 to update, 1 to destroy." in result

    def test_format_multiple_creates(self):
        """Test plan with multiple CREATE actions."""
        actions = [
            make_create_action("project", "PROJ1", name="Project 1"),
            make_create_action("dataset", "PROJ1", "DATASET1", type="sql"),
            make_create_action("dataset", "PROJ1", "DATASET2", type="managed"),
        ]
        
        plan = ExecutionPlan(actions=actions)
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert "+ project.PROJ1" in result
        assert "+ dataset.PROJ1.DATASET1" in result
        assert "+ dataset.PROJ1.DATASET2" in result
        assert "Plan: 3 to create, 0 to update, 0 to destroy." in result


class TestSummaryFormatting:
    """Test summary formatting."""

    def test_summary_only_creates(self):
        """Test summary with only creates."""
        actions = [
            make_create_action("project", "P1"),
            make_create_action("dataset", "P1", "D1")
        ]
        plan = ExecutionPlan(actions=actions)
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert "Plan: 2 to create." in result

    def test_summary_only_updates(self):
        """Test summary with only updates."""
        actions = [
            make_update_action("dataset", "P1", "D1", 
                             attr_diffs={"description": {"old": "a", "new": "b"}})
        ]
        plan = ExecutionPlan(actions=actions)
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert "Plan: 1 to update." in result

    def test_summary_only_deletes(self):
        """Test summary with only deletes."""
        actions = [
            make_delete_action("recipe", "P1", "R1"),
            make_delete_action("recipe", "P1", "R2"),
            make_delete_action("recipe", "P1", "R3")
        ]
        plan = ExecutionPlan(actions=actions)
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert "Plan: 3 to destroy." in result

    def test_summary_all_types(self):
        """Test summary with all action types."""
        actions = [
            make_create_action("project", "P1"),
            make_create_action("dataset", "P1", "D1"),
            make_update_action("dataset", "P1", "D2", 
                             attr_diffs={"desc": {"old": "a", "new": "b"}}),
            make_delete_action("recipe", "P1", "R1")
        ]
        plan = ExecutionPlan(actions=actions)
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert "Plan: 2 to create, 1 to update, 1 to destroy." in result


class TestColorFormatting:
    """Test color and no-color output modes."""

    def test_color_enabled(self):
        """Test that color codes are included when color=True."""
        action = make_create_action("project", "TEST")
        plan = ExecutionPlan(actions=[action])
        formatter = PlanFormatter(color=True)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        # Should contain ANSI color codes
        assert "\033[" in result

    def test_color_disabled(self):
        """Test that color codes are excluded when color=False."""
        action = make_create_action("project", "TEST")
        plan = ExecutionPlan(actions=[action])
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        # Should not contain ANSI color codes
        assert "\033[" not in result

    def test_color_codes_for_action_types(self):
        """Test different colors for different action types."""
        actions = [
            make_create_action("project", "P1"),  # GREEN
            make_update_action("dataset", "P1", "D1", 
                             attr_diffs={"desc": {"old": "a", "new": "b"}}),  # YELLOW
            make_delete_action("recipe", "P1", "R1")  # RED
        ]
        plan = ExecutionPlan(actions=actions)
        formatter = PlanFormatter(color=True)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        # Check for green (create), yellow (update), red (delete)
        assert "\033[92m" in result  # GREEN
        assert "\033[93m" in result  # YELLOW
        assert "\033[91m" in result  # RED


class TestValueFormatting:
    """Test formatting of different value types."""

    def test_format_string_values(self):
        """Test string values are quoted."""
        action = make_create_action("project", "P1", name="Test Project")
        plan = ExecutionPlan(actions=[action])
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert 'name: "Test Project"' in result

    def test_format_boolean_values(self):
        """Test boolean values."""
        action = make_create_action("dataset", "P1", "D1", enabled=True, archived=False)
        plan = ExecutionPlan(actions=[action])
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert "enabled: true" in result
        assert "archived: false" in result

    def test_format_numeric_values(self):
        """Test numeric values."""
        action = make_create_action("dataset", "P1", "D1", size=1024, count=42)
        plan = ExecutionPlan(actions=[action])
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert "size: 1024" in result
        assert "count: 42" in result

    def test_format_null_values(self):
        """Test null values."""
        action = make_create_action("dataset", "P1", "D1", optional_field=None)
        plan = ExecutionPlan(actions=[action])
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert "optional_field: null" in result

    def test_format_complex_values(self):
        """Test complex values (list/dict) are truncated."""
        action = make_create_action(
            "dataset", "P1", "D1", 
            schema={"columns": [{"name": "col1"}]},
            tags=["tag1", "tag2"]
        )
        plan = ExecutionPlan(actions=[action])
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert "schema: ..." in result
        assert "tags: ..." in result


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_format_resource_without_attributes(self):
        """Test formatting resource with empty attributes."""
        action = make_create_action("project", "EMPTY_PROJECT")
        plan = ExecutionPlan(actions=[action])
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert "+ project.EMPTY_PROJECT" in result

    def test_format_update_without_diffs(self):
        """Test UPDATE action with no attribute diffs."""
        action = make_update_action("dataset", "P1", "D1", attr_diffs={})
        plan = ExecutionPlan(actions=[action])
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert "~ dataset.P1.D1" in result

    def test_checksum_attribute_excluded(self):
        """Test that checksum attribute is not displayed."""
        # Create resource with checksum (automatically added)
        resource = make_resource("project", "P1", name="Test")
        # Checksum is automatically computed, so it should exist
        assert resource.metadata.checksum
        
        diff = ResourceDiff(
            change_type=ChangeType.ADDED,
            resource_id=resource.resource_id,
            resource_type=resource.resource_type,
            new_resource=resource
        )
        action = PlannedAction(
            action_type=ActionType.CREATE,
            resource_id=resource.resource_id,
            resource_type=resource.resource_type,
            diff=diff
        )
        
        plan = ExecutionPlan(actions=[action])
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        # Checksum should not appear in output
        assert "checksum:" not in result.lower()


class TestPlanMetadata:
    """Test plan metadata handling."""

    def test_plan_with_metadata(self):
        """Test that plan metadata doesn't break formatting."""
        action = make_create_action("project", "P1")
        plan = ExecutionPlan(
            actions=[action],
            metadata={
                "current_serial": 5,
                "total_actions": 1,
                "created_by": "test"
            }
        )
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert "Dataiku IaC Execution Plan" in result
        assert "+ project.P1" in result
        assert "Plan: 1 to create." in result


class TestOutputStreams:
    """Test writing to different output streams."""

    def test_format_to_stringio(self):
        """Test formatting to StringIO buffer."""
        action = make_create_action("project", "TEST")
        plan = ExecutionPlan(actions=[action])
        formatter = PlanFormatter(color=False)
        
        output = StringIO()
        formatter.format(plan, output)
        result = output.getvalue()
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_multiple_formats_same_plan(self):
        """Test formatting same plan multiple times."""
        action = make_create_action("project", "TEST")
        plan = ExecutionPlan(actions=[action])
        formatter = PlanFormatter(color=False)
        
        output1 = StringIO()
        formatter.format(plan, output1)
        result1 = output1.getvalue()
        
        output2 = StringIO()
        formatter.format(plan, output2)
        result2 = output2.getvalue()
        
        assert result1 == result2
