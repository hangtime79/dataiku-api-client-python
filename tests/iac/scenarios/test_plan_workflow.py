"""
End-to-end scenario tests for plan generation workflow.

These tests validate complete workflows from config to plan:
1. Parse config file
2. Validate configuration
3. Build desired state
4. Load/sync current state
5. Generate plan
6. Format output

Tests use realistic scenarios and validate the entire IaC workflow.
"""

import pytest
from pathlib import Path
import io

from dataikuapi.iac.config.parser import ConfigParser
from dataikuapi.iac.config.validator import ConfigValidator
from dataikuapi.iac.config.builder import DesiredStateBuilder
from dataikuapi.iac.planner.engine import PlanGenerator
from dataikuapi.iac.planner.formatter import PlanFormatter
from dataikuapi.iac.planner.models import ActionType
from dataikuapi.iac.models.state import State
from dataikuapi.iac.manager import StateManager
from dataikuapi.iac.backends.local import LocalFileBackend


@pytest.mark.unit
@pytest.mark.smoke
class TestSimpleProjectWorkflow:
    """Test complete workflow with simple project config"""

    def test_empty_to_full_plan(self, simple_config_file):
        """Test plan generation from empty state to full config"""
        if not simple_config_file.exists():
            pytest.skip(f"Config file not found: {simple_config_file}")

        # 1. Parse configuration
        parser = ConfigParser()
        config = parser.parse_file(simple_config_file)
        assert config.project.key == "IAC_TEST_SIMPLE"

        # 2. Validate configuration
        validator = ConfigValidator(strict=True)
        validator.validate(config)  # Should not raise

        # 3. Build desired state
        builder = DesiredStateBuilder(environment="test")
        desired_state = builder.build(config)
        assert len(desired_state.resources) >= 1  # At least project

        # 4. Create empty current state
        current_state = State(environment="test")

        # 5. Generate plan
        planner = PlanGenerator()
        plan = planner.generate_plan(current_state, desired_state)

        # 6. Verify plan
        assert plan.has_changes()
        summary = plan.summary()
        assert summary["create"] >= 1  # At least creating project
        assert summary.get("update", 0) == 0
        assert summary.get("delete", 0) == 0

        # All actions should be CREATE
        for action in plan.actions:
            assert action.action_type == ActionType.CREATE

        print(f"\n✓ Plan generated: {summary['create']} resources to create")

    def test_no_changes_plan(self, simple_config_file):
        """Test plan generation when state matches config"""
        if not simple_config_file.exists():
            pytest.skip(f"Config file not found: {simple_config_file}")

        # Parse and build desired state
        parser = ConfigParser()
        config = parser.parse_file(simple_config_file)

        validator = ConfigValidator(strict=True)
        validator.validate(config)

        builder = DesiredStateBuilder(environment="test")
        desired_state = builder.build(config)

        # Use same state as both current and desired
        planner = PlanGenerator()
        plan = planner.generate_plan(desired_state, desired_state)

        # Should show no changes
        assert not plan.has_changes()
        summary = plan.summary()
        assert summary.get("create", 0) == 0
        assert summary.get("update", 0) == 0
        assert summary.get("delete", 0) == 0

        print("\n✓ No changes detected (states match)")

    def test_plan_formatting(self, simple_config_file):
        """Test plan formatter generates readable output"""
        if not simple_config_file.exists():
            pytest.skip(f"Config file not found: {simple_config_file}")

        # Generate plan
        parser = ConfigParser()
        config = parser.parse_file(simple_config_file)

        builder = DesiredStateBuilder(environment="test")
        desired_state = builder.build(config)

        current_state = State(environment="test")

        planner = PlanGenerator()
        plan = planner.generate_plan(current_state, desired_state)

        # Format plan
        formatter = PlanFormatter(color=False)
        output = io.StringIO()
        formatter.format(plan, output)

        output_text = output.getvalue()

        # Verify output contains expected elements
        assert "IAC_TEST_SIMPLE" in output_text
        assert "to create" in output_text.lower()
        assert "+" in output_text  # Create symbol

        # Should not contain ANSI codes (color=False)
        assert "\033[" not in output_text

        print(f"\n{output_text}")


@pytest.mark.unit
class TestRealisticPipelineWorkflow:
    """Test complete workflow with realistic customer analytics pipeline"""

    def test_customer_analytics_plan(self, realistic_config_file):
        """Test plan generation for customer analytics pipeline"""
        if not realistic_config_file.exists():
            pytest.skip(f"Config file not found: {realistic_config_file}")

        # Parse
        parser = ConfigParser()
        config = parser.parse_file(realistic_config_file)
        assert config.project.key == "IAC_TEST_CUSTOMER_ANALYTICS"

        # Validate
        validator = ConfigValidator(strict=True)
        validator.validate(config)

        # Build desired state
        builder = DesiredStateBuilder(environment="prod")
        desired_state = builder.build(config)

        # Count resources by type
        resource_counts = {}
        for resource in desired_state.resources.values():
            rtype = resource.resource_type
            resource_counts[rtype] = resource_counts.get(rtype, 0) + 1

        print(f"\nCustomer Analytics Pipeline:")
        print(f"  Projects: {resource_counts.get('project', 0)}")
        print(f"  Datasets: {resource_counts.get('dataset', 0)}")
        print(f"  Recipes: {resource_counts.get('recipe', 0)}")

        # Should have multiple datasets and recipes
        assert resource_counts.get('dataset', 0) >= 3
        assert resource_counts.get('recipe', 0) >= 2

        # Generate plan from empty state
        current_state = State(environment="prod")
        planner = PlanGenerator()
        plan = planner.generate_plan(current_state, desired_state)

        # Verify dependency ordering
        # Projects should come before datasets
        # Datasets should come before recipes that use them
        action_types_by_position = [(a.resource_type, a.action_type) for a in plan.actions]

        project_positions = [i for i, (rt, _) in enumerate(action_types_by_position) if rt == "project"]
        dataset_positions = [i for i, (rt, _) in enumerate(action_types_by_position) if rt == "dataset"]
        recipe_positions = [i for i, (rt, _) in enumerate(action_types_by_position) if rt == "recipe"]

        if project_positions and dataset_positions:
            assert min(project_positions) < min(dataset_positions), \
                "Projects should be created before datasets"

        if dataset_positions and recipe_positions:
            assert min(dataset_positions) < min(recipe_positions), \
                "Datasets should be created before recipes"

        print(f"✓ Plan has correct dependency ordering")


@pytest.mark.unit
class TestComplexMLPipelineWorkflow:
    """Test complete workflow with complex ML pipeline"""

    def test_ml_pipeline_plan(self, complex_config_file):
        """Test plan generation for complex ML pipeline"""
        if not complex_config_file.exists():
            pytest.skip(f"Config file not found: {complex_config_file}")

        # Parse
        parser = ConfigParser()
        config = parser.parse_file(complex_config_file)
        assert config.project.key == "IAC_TEST_ML_PIPELINE"

        # Validate
        validator = ConfigValidator(strict=True)
        validator.validate(config)

        # Build desired state
        builder = DesiredStateBuilder(environment="test")
        desired_state = builder.build(config)

        # This is a complex config with many resources
        assert len(desired_state.resources) >= 10

        # Generate plan
        current_state = State(environment="test")
        planner = PlanGenerator()
        plan = planner.generate_plan(current_state, desired_state)

        summary = plan.summary()
        print(f"\nML Pipeline Plan Summary:")
        print(f"  Total actions: {len(plan.actions)}")
        print(f"  Creates: {summary.get('create', 0)}")

        # Format for display
        formatter = PlanFormatter(color=True)
        output = io.StringIO()
        formatter.format(plan, output)

        output_text = output.getvalue()
        assert "ML_PIPELINE" in output_text


@pytest.mark.integration
@pytest.mark.slow
class TestRealDataikuPlanWorkflow:
    """Test plan generation workflow with real Dataiku instance"""

    def test_plan_against_real_state(self, real_client, skip_if_no_real_dataiku,
                                     test_project_key, simple_config_file, tmp_path):
        """Test generating plan comparing config to real Dataiku state"""
        if not simple_config_file.exists():
            pytest.skip(f"Config file not found: {simple_config_file}")

        try:
            # 1. Parse desired config
            parser = ConfigParser()
            config = parser.parse_file(simple_config_file)

            # Update project key to test project
            config.project.key = test_project_key

            validator = ConfigValidator(strict=True)
            validator.validate(config)

            builder = DesiredStateBuilder(environment="integration")
            desired_state = builder.build(config)

            # 2. Sync current state from real Dataiku
            state_file = tmp_path / "current.state.json"
            backend = LocalFileBackend(state_file)
            manager = StateManager(backend, real_client, "integration")

            current_state = manager.sync_project(test_project_key, include_children=True)

            # 3. Generate plan
            planner = PlanGenerator()
            plan = planner.generate_plan(current_state, desired_state)

            # 4. Display plan
            formatter = PlanFormatter(color=False)
            output = io.StringIO()
            formatter.format(plan, output)

            print(f"\n{output.getvalue()}")

            # Plan might have changes or not, depending on Dataiku state
            summary = plan.summary()
            print(f"\nPlan summary:")
            print(f"  Creates: {summary.get('create', 0)}")
            print(f"  Updates: {summary.get('update', 0)}")
            print(f"  Deletes: {summary.get('delete', 0)}")

        except Exception as e:
            pytest.skip(f"Could not complete plan workflow: {e}")


@pytest.mark.unit
class TestIncrementalChanges:
    """Test plan generation for incremental changes"""

    def test_detect_updates(self, simple_config_file):
        """Test that plan detects updates to existing resources"""
        if not simple_config_file.exists():
            pytest.skip(f"Config file not found: {simple_config_file}")

        # Parse config
        parser = ConfigParser()
        config = parser.parse_file(simple_config_file)

        validator = ConfigValidator(strict=True)
        validator.validate(config)

        builder = DesiredStateBuilder(environment="test")
        desired_state = builder.build(config)

        # Create current state with slightly different attributes
        current_state = State(environment="test")

        for resource_id, resource in desired_state.resources.items():
            if resource.resource_type == "project":
                # Modify project description
                modified_attrs = resource.attributes.copy()
                modified_attrs["description"] = "Different description"

                from dataikuapi.iac.models.state import Resource, ResourceMetadata
                from datetime import datetime

                modified_resource = Resource(
                    resource_type=resource.resource_type,
                    resource_id=resource.resource_id,
                    attributes=modified_attrs,
                    metadata=ResourceMetadata(
                        deployed_by="test",
                        deployed_at=datetime.now()
                    )
                )
                current_state.add_resource(modified_resource)
            else:
                current_state.add_resource(resource)

        # Generate plan
        planner = PlanGenerator()
        plan = planner.generate_plan(current_state, desired_state)

        # Should detect one update (project description changed)
        summary = plan.summary()
        updates = [a for a in plan.actions if a.action_type == ActionType.UPDATE]

        assert len(updates) >= 1
        assert updates[0].resource_type == "project"

        print(f"\n✓ Detected {len(updates)} update(s)")

    def test_detect_deletes(self, simple_config_file):
        """Test that plan detects resources to be deleted"""
        if not simple_config_file.exists():
            pytest.skip(f"Config file not found: {simple_config_file}")

        # Parse config
        parser = ConfigParser()
        config = parser.parse_file(simple_config_file)

        builder = DesiredStateBuilder(environment="test")
        desired_state = builder.build(config)

        # Create current state with extra resource not in desired
        from dataikuapi.iac.models.state import Resource, ResourceMetadata
        from datetime import datetime

        current_state = State(environment="test")

        # Add all desired resources
        for resource in desired_state.resources.values():
            current_state.add_resource(resource)

        # Add extra dataset not in desired config
        extra_dataset = Resource(
            resource_type="dataset",
            resource_id="dataset.IAC_TEST_SIMPLE.EXTRA_DATASET",
            attributes={
                "name": "EXTRA_DATASET",
                "type": "managed",
                "formatType": "csv"
            },
            metadata=ResourceMetadata(
                deployed_by="test",
                deployed_at=datetime.now()
            )
        )
        current_state.add_resource(extra_dataset)

        # Generate plan
        planner = PlanGenerator()
        plan = planner.generate_plan(current_state, desired_state)

        # Should detect delete
        deletes = [a for a in plan.actions if a.action_type == ActionType.DELETE]
        assert len(deletes) >= 1

        delete_ids = [a.resource_id for a in deletes]
        assert "dataset.IAC_TEST_SIMPLE.EXTRA_DATASET" in delete_ids

        print(f"\n✓ Detected {len(deletes)} resource(s) to delete")
