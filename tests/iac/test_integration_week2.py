"""
Week 2 (Plan Generation) integration tests.

Tests the complete workflow from config parsing through plan generation.
"""

import pytest
from pathlib import Path
import tempfile

from dataikuapi.iac.config.parser import ConfigParser
from dataikuapi.iac.config.validator import ConfigValidator
from dataikuapi.iac.config.builder import DesiredStateBuilder
from dataikuapi.iac.planner.engine import PlanGenerator
from dataikuapi.iac.planner.models import ActionType
from dataikuapi.iac.planner.formatter import PlanFormatter
from dataikuapi.iac.models.state import State
from dataikuapi.iac.exceptions import ConfigValidationError


class TestWeek2Integration:
    """Integration tests for Week 2 plan workflow."""

    def test_complete_workflow_simple_config(self, tmp_path):
        """Test complete workflow with simple config."""
        # Create config file
        config_file = tmp_path / "project.yml"
        config_file.write_text("""
version: "1.0"
project:
  key: INTEGRATION_TEST
  name: Integration Test Project
datasets:
  - name: TEST_DATA
    type: managed
    format_type: parquet
""")

        # 1. Parse
        parser = ConfigParser()
        config = parser.parse_file(config_file)
        assert config.project.key == "INTEGRATION_TEST"

        # 2. Validate
        validator = ConfigValidator()
        validator.validate(config)  # Should not raise

        # 3. Build desired state
        builder = DesiredStateBuilder(environment="test")
        desired_state = builder.build(config)
        assert len(desired_state.resources) == 2  # project + dataset

        # 4. Generate plan (empty current state)
        current_state = State(environment="test")
        planner = PlanGenerator()
        plan = planner.generate_plan(current_state, desired_state)

        # 5. Verify plan
        assert len(plan.actions) == 2
        assert all(a.action_type == ActionType.CREATE for a in plan.actions)
        assert plan.has_changes()

        # 6. Format plan (should not raise)
        formatter = PlanFormatter(color=False)
        import io
        output = io.StringIO()
        formatter.format(plan, output)
        output_text = output.getvalue()
        assert "INTEGRATION_TEST" in output_text
        assert "to create" in output_text

    def test_workflow_with_updates(self, tmp_path):
        """Test workflow that detects updates."""
        config_file = tmp_path / "project.yml"
        config_file.write_text("""
project:
  key: UPDATE_TEST
  name: Update Test
  description: Original description
datasets:
  - name: DATA1
    type: managed
""")

        parser = ConfigParser()
        config = parser.parse_file(config_file)

        validator = ConfigValidator()
        validator.validate(config)

        builder = DesiredStateBuilder(environment="test")
        desired_state = builder.build(config)

        # Modify the state to simulate existing different state
        from dataikuapi.iac.models.state import Resource, ResourceMetadata
        current_state = State(environment="test")
        for resource_id, resource in desired_state.resources.items():
            if resource.resource_type == "project":
                # Different description
                modified_attrs = resource.attributes.copy()
                modified_attrs["description"] = "Different description"
                modified_resource = Resource(
                    resource_id=resource.resource_id,
                    resource_type=resource.resource_type,
                    attributes=modified_attrs,
                    metadata=resource.metadata
                )
                current_state.add_resource(modified_resource)
            else:
                current_state.add_resource(resource)

        planner = PlanGenerator()
        plan = planner.generate_plan(current_state, desired_state)

        # Should detect one update
        updates = [a for a in plan.actions if a.action_type == ActionType.UPDATE]
        assert len(updates) == 1
        assert updates[0].resource_type == "project"

    def test_workflow_no_changes(self, tmp_path):
        """Test workflow when states match (no changes)."""
        config_file = tmp_path / "project.yml"
        config_file.write_text("""
project:
  key: NO_CHANGE_TEST
  name: No Change Test
""")

        parser = ConfigParser()
        config = parser.parse_file(config_file)

        validator = ConfigValidator()
        validator.validate(config)

        builder = DesiredStateBuilder(environment="test")
        desired_state = builder.build(config)

        # Use same state for current
        planner = PlanGenerator()
        plan = planner.generate_plan(desired_state, desired_state)

        # Should show no changes
        assert not plan.has_changes()
        assert all(a.action_type == ActionType.NO_CHANGE for a in plan.actions)

    def test_workflow_with_recipes(self, tmp_path):
        """Test workflow with recipes."""
        config_file = tmp_path / "project.yml"
        config_file.write_text("""
project:
  key: RECIPE_TEST
  name: Recipe Test
datasets:
  - name: INPUT_DATA
    type: managed
  - name: OUTPUT_DATA
    type: managed
recipes:
  - name: transform
    type: python
    inputs: [INPUT_DATA]
    outputs: [OUTPUT_DATA]
    code: |
      df = input.get_dataframe()
      output = df
""")

        parser = ConfigParser()
        config = parser.parse_file(config_file)

        validator = ConfigValidator()
        validator.validate(config)

        builder = DesiredStateBuilder(environment="test")
        desired_state = builder.build(config)

        # Should have project + 2 datasets + 1 recipe
        assert len(desired_state.resources) == 4

        planner = PlanGenerator()
        current_state = State(environment="test")
        plan = planner.generate_plan(current_state, desired_state)

        assert len(plan.actions) == 4
        assert all(a.action_type == ActionType.CREATE for a in plan.actions)

    def test_workflow_validation_failure(self, tmp_path):
        """Test that validation errors are caught."""
        config_file = tmp_path / "invalid.yml"
        config_file.write_text("""
project:
  key: invalid-key  # Lowercase, should fail
  name: Invalid
""")

        parser = ConfigParser()
        config = parser.parse_file(config_file)

        validator = ConfigValidator()
        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        assert "key" in str(exc_info.value).lower() or "uppercase" in str(exc_info.value).lower()

    def test_workflow_reference_validation(self, tmp_path):
        """Test that reference validation works."""
        config_file = tmp_path / "bad_ref.yml"
        config_file.write_text("""
project:
  key: REF_TEST
  name: Reference Test
datasets:
  - name: DATASET1
    type: managed
recipes:
  - name: recipe1
    type: python
    inputs: [NONEXISTENT]  # Bad reference
    outputs: [DATASET1]
""")

        parser = ConfigParser()
        config = parser.parse_file(config_file)

        validator = ConfigValidator()
        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        assert "nonexistent" in str(exc_info.value).lower()

    def test_workflow_directory_config(self, tmp_path):
        """Test workflow with directory-based config."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Project
        (config_dir / "project.yml").write_text("""
project:
  key: DIR_TEST
  name: Directory Test
""")

        # Datasets
        datasets_dir = config_dir / "datasets"
        datasets_dir.mkdir()
        (datasets_dir / "ds1.yml").write_text("""
datasets:
  - name: DS1
    type: managed
""")

        parser = ConfigParser()
        config = parser.parse_directory(config_dir)

        validator = ConfigValidator()
        validator.validate(config)

        builder = DesiredStateBuilder(environment="test")
        desired_state = builder.build(config)

        assert len(desired_state.resources) == 2  # project + 1 dataset

    def test_workflow_plan_summary(self, tmp_path):
        """Test plan summary is correct."""
        config_file = tmp_path / "project.yml"
        config_file.write_text("""
project:
  key: SUMMARY_TEST
  name: Summary Test
datasets:
  - name: DS1
    type: managed
  - name: DS2
    type: managed
  - name: DS3
    type: managed
""")

        parser = ConfigParser()
        config = parser.parse_file(config_file)

        validator = ConfigValidator()
        validator.validate(config)

        builder = DesiredStateBuilder(environment="test")
        desired_state = builder.build(config)

        planner = PlanGenerator()
        current_state = State(environment="test")
        plan = planner.generate_plan(current_state, desired_state)

        summary = plan.summary()
        assert summary["create"] == 4  # 1 project + 3 datasets
        assert summary.get("update", 0) == 0
        assert summary.get("delete", 0) == 0

    def test_cli_integration(self, tmp_path):
        """Test CLI plan command integration."""
        config_file = tmp_path / "project.yml"
        config_file.write_text("""
project:
  key: CLI_TEST
  name: CLI Test
datasets:
  - name: CLI_DATA
    type: managed
""")

        # Import CLI plan function
        from dataikuapi.iac.cli.plan import plan

        # Run plan command
        exit_code = plan([
            "-c", str(config_file),
            "-e", "test",
            "--no-color"
        ])

        # Exit code 2 means changes detected (which is correct for empty state)
        assert exit_code == 2

    def test_cli_no_changes(self, tmp_path):
        """Test CLI returns 0 when no changes."""
        # This would require setting up state file, skipping for now
        pass

    def test_formatter_no_color(self, tmp_path):
        """Test formatter works without color."""
        config_file = tmp_path / "project.yml"
        config_file.write_text("""
project:
  key: FORMAT_TEST
  name: Format Test
""")

        parser = ConfigParser()
        config = parser.parse_file(config_file)

        validator = ConfigValidator()
        validator.validate(config)

        builder = DesiredStateBuilder(environment="test")
        desired_state = builder.build(config)

        planner = PlanGenerator()
        current_state = State(environment="test")
        plan = planner.generate_plan(current_state, desired_state)

        # Format without color
        formatter = PlanFormatter(color=False)
        import io
        output = io.StringIO()
        formatter.format(plan, output)
        output_text = output.getvalue()

        # Should not contain ANSI codes
        assert "\033[" not in output_text
        assert "FORMAT_TEST" in output_text
