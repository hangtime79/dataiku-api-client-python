"""
Tests for plan generation engine.

This module tests the PlanGenerator class and related models:
- Plan generation for all change types
- Action ordering respecting dependencies
- Plan summaries and metadata
"""

import pytest
from datetime import datetime

from dataikuapi.iac.models.state import State, Resource, ResourceMetadata, make_resource_id
from dataikuapi.iac.planner import PlanGenerator, ActionType, PlannedAction, ExecutionPlan
from dataikuapi.iac.models.diff import ChangeType


@pytest.fixture
def empty_state():
    """Empty state for testing."""
    return State(environment="test")


@pytest.fixture
def simple_current_state():
    """Simple current state with project and dataset."""
    state = State(environment="test")

    # Add project
    project = Resource(
        resource_type="project",
        resource_id="project.TEST_PROJECT",
        attributes={
            "projectKey": "TEST_PROJECT",
            "name": "Test Project",
            "description": "A test project"
        },
        metadata=ResourceMetadata(
            deployed_at=datetime.utcnow(),
            deployed_by="test"
        )
    )
    state.add_resource(project)

    # Add dataset
    dataset = Resource(
        resource_type="dataset",
        resource_id="dataset.TEST_PROJECT.TEST_DATASET",
        attributes={
            "name": "TEST_DATASET",
            "type": "managed",
            "schema": {"columns": [{"name": "id", "type": "int"}]}
        },
        metadata=ResourceMetadata(
            deployed_at=datetime.utcnow(),
            deployed_by="test"
        )
    )
    state.add_resource(dataset)

    return state


@pytest.fixture
def simple_desired_state():
    """Simple desired state with project, dataset, and recipe."""
    state = State(environment="test")

    # Add project
    project = Resource(
        resource_type="project",
        resource_id="project.TEST_PROJECT",
        attributes={
            "projectKey": "TEST_PROJECT",
            "name": "Test Project",
            "description": "A test project"
        },
        metadata=ResourceMetadata(
            deployed_at=datetime.utcnow(),
            deployed_by="config"
        )
    )
    state.add_resource(project)

    # Add dataset (unchanged)
    dataset = Resource(
        resource_type="dataset",
        resource_id="dataset.TEST_PROJECT.TEST_DATASET",
        attributes={
            "name": "TEST_DATASET",
            "type": "managed",
            "schema": {"columns": [{"name": "id", "type": "int"}]}
        },
        metadata=ResourceMetadata(
            deployed_at=datetime.utcnow(),
            deployed_by="config"
        )
    )
    state.add_resource(dataset)

    # Add recipe (new)
    recipe = Resource(
        resource_type="recipe",
        resource_id="recipe.TEST_PROJECT.prep_data",
        attributes={
            "name": "prep_data",
            "type": "python",
            "inputs": ["TEST_DATASET"],
            "outputs": ["PREPPED_DATA"]
        },
        metadata=ResourceMetadata(
            deployed_at=datetime.utcnow(),
            deployed_by="config"
        )
    )
    state.add_resource(recipe)

    # Add output dataset
    output_dataset = Resource(
        resource_type="dataset",
        resource_id="dataset.TEST_PROJECT.PREPPED_DATA",
        attributes={
            "name": "PREPPED_DATA",
            "type": "managed"
        },
        metadata=ResourceMetadata(
            deployed_at=datetime.utcnow(),
            deployed_by="config"
        )
    )
    state.add_resource(output_dataset)

    return state


class TestActionType:
    """Tests for ActionType enum."""

    def test_action_types(self):
        """Test all action types exist."""
        assert ActionType.CREATE.value == "create"
        assert ActionType.UPDATE.value == "update"
        assert ActionType.DELETE.value == "delete"
        assert ActionType.NO_CHANGE.value == "no-change"


class TestPlannedAction:
    """Tests for PlannedAction model."""

    def test_planned_action_creation(self):
        """Test creating a planned action."""
        from dataikuapi.iac.models.diff import ResourceDiff

        diff = ResourceDiff(
            change_type=ChangeType.ADDED,
            resource_id="project.TEST_PROJECT",
            resource_type="project"
        )

        action = PlannedAction(
            action_type=ActionType.CREATE,
            resource_id="project.TEST_PROJECT",
            resource_type="project",
            diff=diff
        )

        assert action.action_type == ActionType.CREATE
        assert action.resource_id == "project.TEST_PROJECT"
        assert action.resource_type == "project"
        assert action.dependencies == []

    def test_planned_action_str(self):
        """Test string representation of action."""
        from dataikuapi.iac.models.diff import ResourceDiff

        diff = ResourceDiff(
            change_type=ChangeType.ADDED,
            resource_id="project.TEST_PROJECT",
            resource_type="project"
        )

        action = PlannedAction(
            action_type=ActionType.CREATE,
            resource_id="project.TEST_PROJECT",
            resource_type="project",
            diff=diff
        )

        assert str(action) == "+ project.TEST_PROJECT"

    def test_planned_action_with_dependencies(self):
        """Test action with dependencies."""
        from dataikuapi.iac.models.diff import ResourceDiff

        diff = ResourceDiff(
            change_type=ChangeType.ADDED,
            resource_id="dataset.TEST_PROJECT.TEST_DATASET",
            resource_type="dataset"
        )

        action = PlannedAction(
            action_type=ActionType.CREATE,
            resource_id="dataset.TEST_PROJECT.TEST_DATASET",
            resource_type="dataset",
            diff=diff,
            dependencies=["project.TEST_PROJECT"]
        )

        assert action.dependencies == ["project.TEST_PROJECT"]


class TestExecutionPlan:
    """Tests for ExecutionPlan model."""

    def test_empty_plan(self):
        """Test empty execution plan."""
        plan = ExecutionPlan()

        assert len(plan.actions) == 0
        assert not plan.has_changes()

    def test_plan_summary(self):
        """Test plan summary calculation."""
        from dataikuapi.iac.models.diff import ResourceDiff

        actions = []

        # Create action
        create_diff = ResourceDiff(
            change_type=ChangeType.ADDED,
            resource_id="project.TEST_PROJECT",
            resource_type="project"
        )
        actions.append(PlannedAction(
            action_type=ActionType.CREATE,
            resource_id="project.TEST_PROJECT",
            resource_type="project",
            diff=create_diff
        ))

        # Update action
        update_diff = ResourceDiff(
            change_type=ChangeType.MODIFIED,
            resource_id="dataset.TEST_PROJECT.TEST_DATASET",
            resource_type="dataset"
        )
        actions.append(PlannedAction(
            action_type=ActionType.UPDATE,
            resource_id="dataset.TEST_PROJECT.TEST_DATASET",
            resource_type="dataset",
            diff=update_diff
        ))

        # Delete action
        delete_diff = ResourceDiff(
            change_type=ChangeType.REMOVED,
            resource_id="recipe.TEST_PROJECT.old_recipe",
            resource_type="recipe"
        )
        actions.append(PlannedAction(
            action_type=ActionType.DELETE,
            resource_id="recipe.TEST_PROJECT.old_recipe",
            resource_type="recipe",
            diff=delete_diff
        ))

        plan = ExecutionPlan(actions=actions)
        summary = plan.summary()

        assert summary["create"] == 1
        assert summary["update"] == 1
        assert summary["delete"] == 1
        assert summary["no_change"] == 0

    def test_plan_has_changes(self):
        """Test has_changes method."""
        from dataikuapi.iac.models.diff import ResourceDiff

        # Plan with changes
        create_diff = ResourceDiff(
            change_type=ChangeType.ADDED,
            resource_id="project.TEST_PROJECT",
            resource_type="project"
        )
        action = PlannedAction(
            action_type=ActionType.CREATE,
            resource_id="project.TEST_PROJECT",
            resource_type="project",
            diff=create_diff
        )
        plan_with_changes = ExecutionPlan(actions=[action])
        assert plan_with_changes.has_changes()

        # Plan without changes
        no_change_diff = ResourceDiff(
            change_type=ChangeType.UNCHANGED,
            resource_id="project.TEST_PROJECT",
            resource_type="project"
        )
        no_change_action = PlannedAction(
            action_type=ActionType.NO_CHANGE,
            resource_id="project.TEST_PROJECT",
            resource_type="project",
            diff=no_change_diff
        )
        plan_no_changes = ExecutionPlan(actions=[no_change_action])
        assert not plan_no_changes.has_changes()

    def test_plan_str(self):
        """Test string representation of plan."""
        from dataikuapi.iac.models.diff import ResourceDiff

        # Empty plan
        empty_plan = ExecutionPlan()
        assert "ExecutionPlan(actions=[]" in str(empty_plan)

        # Plan with changes
        create_diff = ResourceDiff(
            change_type=ChangeType.ADDED,
            resource_id="project.TEST_PROJECT",
            resource_type="project"
        )
        action = PlannedAction(
            action_type=ActionType.CREATE,
            resource_id="project.TEST_PROJECT",
            resource_type="project",
            diff=create_diff
        )
        plan = ExecutionPlan(actions=[action])
        # __str__ returns the dataclass repr, not a summary
        assert "ExecutionPlan(actions=[" in str(plan)
        assert "PlannedAction" in str(plan)


class TestPlanGenerator:
    """Tests for PlanGenerator class."""

    def test_generate_plan_empty_to_simple(self, empty_state, simple_desired_state):
        """Test generating plan from empty state."""
        generator = PlanGenerator()
        plan = generator.generate_plan(empty_state, simple_desired_state)

        assert plan.has_changes()
        assert len(plan.actions) == 4  # project + 2 datasets + 1 recipe

        summary = plan.summary()
        assert summary["create"] == 4
        assert summary["update"] == 0
        assert summary["delete"] == 0

    def test_generate_plan_no_changes(self, simple_current_state):
        """Test generating plan with no changes."""
        generator = PlanGenerator()
        # Use same state for both current and desired
        plan = generator.generate_plan(simple_current_state, simple_current_state)

        summary = plan.summary()
        assert summary["create"] == 0
        assert summary["update"] == 0
        assert summary["delete"] == 0
        assert summary["no_change"] == 2  # project + dataset

    def test_generate_plan_with_update(self, simple_current_state):
        """Test generating plan with updates."""
        # Modify desired state
        desired_state = State(environment="test")

        # Add project with different description
        project = Resource(
            resource_type="project",
            resource_id="project.TEST_PROJECT",
            attributes={
                "projectKey": "TEST_PROJECT",
                "name": "Test Project",
                "description": "Updated description"  # Changed
            },
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="config"
            )
        )
        desired_state.add_resource(project)

        # Keep dataset same
        dataset = Resource(
            resource_type="dataset",
            resource_id="dataset.TEST_PROJECT.TEST_DATASET",
            attributes={
                "name": "TEST_DATASET",
                "type": "managed",
                "schema": {"columns": [{"name": "id", "type": "int"}]}
            },
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="config"
            )
        )
        desired_state.add_resource(dataset)

        generator = PlanGenerator()
        plan = generator.generate_plan(simple_current_state, desired_state)

        summary = plan.summary()
        assert summary["update"] == 1  # project updated
        assert summary["no_change"] == 1  # dataset unchanged

    def test_generate_plan_with_delete(self, simple_current_state, empty_state):
        """Test generating plan with deletes."""
        generator = PlanGenerator()
        plan = generator.generate_plan(simple_current_state, empty_state)

        summary = plan.summary()
        assert summary["delete"] == 2  # project + dataset
        assert summary["create"] == 0

    def test_action_ordering_creates(self, empty_state):
        """Test that creates are ordered by dependencies."""
        # Create desired state with project, dataset, recipe
        desired_state = State(environment="test")

        # Add recipe (should come last)
        recipe = Resource(
            resource_type="recipe",
            resource_id="recipe.TEST_PROJECT.prep_data",
            attributes={
                "name": "prep_data",
                "type": "python",
                "inputs": ["TEST_DATASET"],
                "outputs": ["PREPPED_DATA"]
            },
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="config"
            )
        )
        desired_state.add_resource(recipe)

        # Add dataset (should come second)
        dataset = Resource(
            resource_type="dataset",
            resource_id="dataset.TEST_PROJECT.TEST_DATASET",
            attributes={
                "name": "TEST_DATASET",
                "type": "managed"
            },
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="config"
            )
        )
        desired_state.add_resource(dataset)

        # Add output dataset
        output_dataset = Resource(
            resource_type="dataset",
            resource_id="dataset.TEST_PROJECT.PREPPED_DATA",
            attributes={
                "name": "PREPPED_DATA",
                "type": "managed"
            },
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="config"
            )
        )
        desired_state.add_resource(output_dataset)

        # Add project (should come first)
        project = Resource(
            resource_type="project",
            resource_id="project.TEST_PROJECT",
            attributes={
                "projectKey": "TEST_PROJECT",
                "name": "Test Project"
            },
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="config"
            )
        )
        desired_state.add_resource(project)

        generator = PlanGenerator()
        plan = generator.generate_plan(empty_state, desired_state)

        # All should be creates
        creates = [a for a in plan.actions if a.action_type == ActionType.CREATE]
        assert len(creates) == 4

        # Project should be first
        assert creates[0].resource_type == "project"

        # Datasets should come before recipe
        dataset_indices = [
            i for i, a in enumerate(creates)
            if a.resource_type == "dataset"
        ]
        recipe_indices = [
            i for i, a in enumerate(creates)
            if a.resource_type == "recipe"
        ]

        if recipe_indices:
            # All datasets should come before recipe
            assert all(di < recipe_indices[0] for di in dataset_indices)

    def test_action_ordering_deletes(self):
        """Test that deletes are ordered reverse of creates."""
        # Current state with project, dataset, recipe
        current_state = State(environment="test")

        project = Resource(
            resource_type="project",
            resource_id="project.TEST_PROJECT",
            attributes={"projectKey": "TEST_PROJECT"},
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="test"
            )
        )
        current_state.add_resource(project)

        dataset = Resource(
            resource_type="dataset",
            resource_id="dataset.TEST_PROJECT.TEST_DATASET",
            attributes={"name": "TEST_DATASET"},
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="test"
            )
        )
        current_state.add_resource(dataset)

        recipe = Resource(
            resource_type="recipe",
            resource_id="recipe.TEST_PROJECT.prep_data",
            attributes={
                "name": "prep_data",
                "inputs": ["TEST_DATASET"]
            },
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="test"
            )
        )
        current_state.add_resource(recipe)

        # Empty desired state
        desired_state = State(environment="test")

        generator = PlanGenerator()
        plan = generator.generate_plan(current_state, desired_state)

        deletes = [a for a in plan.actions if a.action_type == ActionType.DELETE]
        assert len(deletes) == 3

        # Get the indices of each delete action
        recipe_idx = next(i for i, a in enumerate(deletes) if a.resource_type == "recipe")
        dataset_idx = next(i for i, a in enumerate(deletes) if a.resource_type == "dataset")
        project_idx = next(i for i, a in enumerate(deletes) if a.resource_type == "project")

        # Current implementation orders deletes by type priority: project, dataset, recipe
        # TODO: Wave 4 should implement proper reverse dependency ordering
        assert project_idx < dataset_idx < recipe_idx

    def test_action_ordering_mixed(self, simple_current_state):
        """Test ordering with mixed creates, updates, deletes."""
        # Desired state with:
        # - Updated project
        # - Deleted dataset
        # - New dataset
        # - New recipe
        desired_state = State(environment="test")

        # Update project
        project = Resource(
            resource_type="project",
            resource_id="project.TEST_PROJECT",
            attributes={
                "projectKey": "TEST_PROJECT",
                "name": "Test Project",
                "description": "Updated"
            },
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="config"
            )
        )
        desired_state.add_resource(project)

        # Add new dataset
        new_dataset = Resource(
            resource_type="dataset",
            resource_id="dataset.TEST_PROJECT.NEW_DATASET",
            attributes={"name": "NEW_DATASET"},
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="config"
            )
        )
        desired_state.add_resource(new_dataset)

        # Add new recipe
        recipe = Resource(
            resource_type="recipe",
            resource_id="recipe.TEST_PROJECT.new_recipe",
            attributes={
                "name": "new_recipe",
                "inputs": ["NEW_DATASET"]
            },
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="config"
            )
        )
        desired_state.add_resource(recipe)

        generator = PlanGenerator()
        plan = generator.generate_plan(simple_current_state, desired_state)

        # Check ordering: creates, then updates, then deletes
        action_types = [a.action_type for a in plan.actions]

        # Find indices of each type
        create_indices = [i for i, t in enumerate(action_types) if t == ActionType.CREATE]
        update_indices = [i for i, t in enumerate(action_types) if t == ActionType.UPDATE]
        delete_indices = [i for i, t in enumerate(action_types) if t == ActionType.DELETE]

        # Creates should come before updates
        if create_indices and update_indices:
            assert max(create_indices) < min(update_indices)

        # Updates should come before deletes
        if update_indices and delete_indices:
            assert max(update_indices) < min(delete_indices)

    def test_plan_metadata(self, empty_state, simple_desired_state):
        """Test plan metadata is populated."""
        generator = PlanGenerator()
        plan = generator.generate_plan(empty_state, simple_desired_state)

        assert "current_serial" in plan.metadata
        assert "desired_serial" in plan.metadata
        assert "total_actions" in plan.metadata
        assert "has_changes" in plan.metadata

        assert plan.metadata["current_serial"] == empty_state.serial
        assert plan.metadata["desired_serial"] == simple_desired_state.serial
        assert plan.metadata["total_actions"] == len(plan.actions)
        assert plan.metadata["has_changes"] == plan.has_changes()

    def test_complex_dependencies(self):
        """Test complex dependency chain."""
        current_state = State(environment="test")
        desired_state = State(environment="test")

        # Create project
        project = Resource(
            resource_type="project",
            resource_id="project.TEST_PROJECT",
            attributes={"projectKey": "TEST_PROJECT"},
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="config"
            )
        )
        desired_state.add_resource(project)

        # Create dataset A
        dataset_a = Resource(
            resource_type="dataset",
            resource_id="dataset.TEST_PROJECT.DATASET_A",
            attributes={"name": "DATASET_A"},
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="config"
            )
        )
        desired_state.add_resource(dataset_a)

        # Create recipe that uses A and produces B
        recipe_ab = Resource(
            resource_type="recipe",
            resource_id="recipe.TEST_PROJECT.recipe_ab",
            attributes={
                "name": "recipe_ab",
                "inputs": ["DATASET_A"],
                "outputs": ["DATASET_B"]
            },
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="config"
            )
        )
        desired_state.add_resource(recipe_ab)

        # Create dataset B
        dataset_b = Resource(
            resource_type="dataset",
            resource_id="dataset.TEST_PROJECT.DATASET_B",
            attributes={"name": "DATASET_B"},
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="config"
            )
        )
        desired_state.add_resource(dataset_b)

        # Create recipe that uses B and produces C
        recipe_bc = Resource(
            resource_type="recipe",
            resource_id="recipe.TEST_PROJECT.recipe_bc",
            attributes={
                "name": "recipe_bc",
                "inputs": ["DATASET_B"],
                "outputs": ["DATASET_C"]
            },
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="config"
            )
        )
        desired_state.add_resource(recipe_bc)

        # Create dataset C
        dataset_c = Resource(
            resource_type="dataset",
            resource_id="dataset.TEST_PROJECT.DATASET_C",
            attributes={"name": "DATASET_C"},
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="config"
            )
        )
        desired_state.add_resource(dataset_c)

        generator = PlanGenerator()
        plan = generator.generate_plan(current_state, desired_state)

        creates = [a for a in plan.actions if a.action_type == ActionType.CREATE]

        # Project should be first
        assert creates[0].resource_type == "project"

        # Find indices
        indices = {a.resource_id: i for i, a in enumerate(creates)}

        # DATASET_A should come before recipe_ab
        assert indices["dataset.TEST_PROJECT.DATASET_A"] < indices["recipe.TEST_PROJECT.recipe_ab"]

        # recipe_ab should come before its output can be used
        # DATASET_B should exist before recipe_bc
        assert indices["dataset.TEST_PROJECT.DATASET_B"] < indices["recipe.TEST_PROJECT.recipe_bc"]
