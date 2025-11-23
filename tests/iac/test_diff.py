"""
Unit tests for diff models and DiffEngine.
"""

import pytest
from dataikuapi.iac.models import ChangeType, ResourceDiff, Resource, State
from dataikuapi.iac.diff import DiffEngine


class TestChangeType:
    """Test ChangeType enum"""

    def test_change_type_values(self):
        """ChangeType has correct values"""
        assert ChangeType.ADDED.value == "added"
        assert ChangeType.REMOVED.value == "removed"
        assert ChangeType.MODIFIED.value == "modified"
        assert ChangeType.UNCHANGED.value == "unchanged"


class TestResourceDiff:
    """Test ResourceDiff model"""

    def test_create_added_diff(self):
        """Can create diff for added resource"""
        resource = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test"}
        )
        diff = ResourceDiff(
            change_type=ChangeType.ADDED,
            resource_id="project.TEST",
            resource_type="project",
            new_resource=resource
        )
        assert diff.change_type == ChangeType.ADDED
        assert diff.resource_id == "project.TEST"
        assert diff.new_resource is not None
        assert diff.old_resource is None

    def test_create_removed_diff(self):
        """Can create diff for removed resource"""
        resource = Resource(
            resource_type="dataset",
            resource_id="dataset.TEST.DATA",
            attributes={"type": "Snowflake"}
        )
        diff = ResourceDiff(
            change_type=ChangeType.REMOVED,
            resource_id="dataset.TEST.DATA",
            resource_type="dataset",
            old_resource=resource
        )
        assert diff.change_type == ChangeType.REMOVED
        assert diff.old_resource is not None
        assert diff.new_resource is None

    def test_create_modified_diff(self):
        """Can create diff for modified resource"""
        old_resource = Resource(
            resource_type="recipe",
            resource_id="recipe.TEST.PREP",
            attributes={"type": "python", "version": 1}
        )
        new_resource = Resource(
            resource_type="recipe",
            resource_id="recipe.TEST.PREP",
            attributes={"type": "python", "version": 2}
        )
        diff = ResourceDiff(
            change_type=ChangeType.MODIFIED,
            resource_id="recipe.TEST.PREP",
            resource_type="recipe",
            old_resource=old_resource,
            new_resource=new_resource,
            attribute_diffs={
                "added": {},
                "removed": {},
                "modified": {"version": {"old": 1, "new": 2}}
            }
        )
        assert diff.change_type == ChangeType.MODIFIED
        assert diff.old_resource is not None
        assert diff.new_resource is not None
        assert diff.attribute_diffs is not None

    def test_diff_str_added(self):
        """String representation for added resource"""
        diff = ResourceDiff(
            change_type=ChangeType.ADDED,
            resource_id="project.TEST",
            resource_type="project"
        )
        assert str(diff) == "+ project.TEST"

    def test_diff_str_removed(self):
        """String representation for removed resource"""
        diff = ResourceDiff(
            change_type=ChangeType.REMOVED,
            resource_id="dataset.TEST.DATA",
            resource_type="dataset"
        )
        assert str(diff) == "- dataset.TEST.DATA"

    def test_diff_str_modified(self):
        """String representation for modified resource"""
        diff = ResourceDiff(
            change_type=ChangeType.MODIFIED,
            resource_id="recipe.TEST.PREP",
            resource_type="recipe"
        )
        assert str(diff) == "~ recipe.TEST.PREP"

    def test_diff_str_unchanged(self):
        """String representation for unchanged resource"""
        diff = ResourceDiff(
            change_type=ChangeType.UNCHANGED,
            resource_id="model.TEST.PREDICTOR",
            resource_type="model"
        )
        assert str(diff) == "  model.TEST.PREDICTOR"


class TestDiffEngine:
    """Test DiffEngine class"""

    def test_diff_empty_states(self):
        """Diff between two empty states produces no changes"""
        engine = DiffEngine()
        old_state = State(environment="dev")
        new_state = State(environment="dev")

        diffs = engine.diff(old_state, new_state)

        assert len(diffs) == 0

    def test_diff_detects_added_resource(self):
        """DiffEngine detects added resources"""
        engine = DiffEngine()
        old_state = State(environment="dev")
        new_state = State(environment="dev")

        # Add resource to new state
        resource = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test Project"}
        )
        new_state.add_resource(resource)

        diffs = engine.diff(old_state, new_state)

        assert len(diffs) == 1
        assert diffs[0].change_type == ChangeType.ADDED
        assert diffs[0].resource_id == "project.TEST"
        assert diffs[0].new_resource is not None
        assert diffs[0].old_resource is None

    def test_diff_detects_removed_resource(self):
        """DiffEngine detects removed resources"""
        engine = DiffEngine()
        old_state = State(environment="dev")
        new_state = State(environment="dev")

        # Add resource to old state
        resource = Resource(
            resource_type="dataset",
            resource_id="dataset.TEST.DATA",
            attributes={"type": "Snowflake"}
        )
        old_state.add_resource(resource)

        diffs = engine.diff(old_state, new_state)

        assert len(diffs) == 1
        assert diffs[0].change_type == ChangeType.REMOVED
        assert diffs[0].resource_id == "dataset.TEST.DATA"
        assert diffs[0].old_resource is not None
        assert diffs[0].new_resource is None

    def test_diff_detects_modified_resource(self):
        """DiffEngine detects modified resources"""
        engine = DiffEngine()
        old_state = State(environment="dev")
        new_state = State(environment="dev")

        # Add same resource with different attributes to both states
        old_resource = Resource(
            resource_type="recipe",
            resource_id="recipe.TEST.PREP",
            attributes={"type": "python", "version": 1}
        )
        new_resource = Resource(
            resource_type="recipe",
            resource_id="recipe.TEST.PREP",
            attributes={"type": "python", "version": 2}
        )

        old_state.add_resource(old_resource)
        new_state.add_resource(new_resource)

        diffs = engine.diff(old_state, new_state)

        assert len(diffs) == 1
        assert diffs[0].change_type == ChangeType.MODIFIED
        assert diffs[0].resource_id == "recipe.TEST.PREP"
        assert diffs[0].old_resource is not None
        assert diffs[0].new_resource is not None
        assert diffs[0].attribute_diffs is not None

    def test_diff_detects_unchanged_resource(self):
        """DiffEngine detects unchanged resources"""
        engine = DiffEngine()
        old_state = State(environment="dev")
        new_state = State(environment="dev")

        # Add identical resource to both states
        old_resource = Resource(
            resource_type="model",
            resource_id="model.TEST.PREDICTOR",
            attributes={"algorithm": "random_forest", "version": 1}
        )
        new_resource = Resource(
            resource_type="model",
            resource_id="model.TEST.PREDICTOR",
            attributes={"algorithm": "random_forest", "version": 1}
        )

        old_state.add_resource(old_resource)
        new_state.add_resource(new_resource)

        diffs = engine.diff(old_state, new_state)

        assert len(diffs) == 1
        assert diffs[0].change_type == ChangeType.UNCHANGED
        assert diffs[0].resource_id == "model.TEST.PREDICTOR"

    def test_diff_mixed_changes(self):
        """DiffEngine handles multiple different changes"""
        engine = DiffEngine()
        old_state = State(environment="dev")
        new_state = State(environment="dev")

        # Added resource (only in new)
        new_state.add_resource(Resource(
            resource_type="project",
            resource_id="project.NEW",
            attributes={"name": "New Project"}
        ))

        # Removed resource (only in old)
        old_state.add_resource(Resource(
            resource_type="dataset",
            resource_id="dataset.OLD.DATA",
            attributes={"type": "SQL"}
        ))

        # Modified resource (different in both)
        old_state.add_resource(Resource(
            resource_type="recipe",
            resource_id="recipe.TEST.PREP",
            attributes={"version": 1}
        ))
        new_state.add_resource(Resource(
            resource_type="recipe",
            resource_id="recipe.TEST.PREP",
            attributes={"version": 2}
        ))

        # Unchanged resource (same in both)
        old_state.add_resource(Resource(
            resource_type="model",
            resource_id="model.TEST.PREDICTOR",
            attributes={"algorithm": "rf"}
        ))
        new_state.add_resource(Resource(
            resource_type="model",
            resource_id="model.TEST.PREDICTOR",
            attributes={"algorithm": "rf"}
        ))

        diffs = engine.diff(old_state, new_state)

        # Should have 4 diffs: 1 added, 1 removed, 1 modified, 1 unchanged
        assert len(diffs) == 4

        change_types = [d.change_type for d in diffs]
        assert ChangeType.ADDED in change_types
        assert ChangeType.REMOVED in change_types
        assert ChangeType.MODIFIED in change_types
        assert ChangeType.UNCHANGED in change_types

    def test_diff_attributes_added(self):
        """_diff_attributes detects added attributes"""
        engine = DiffEngine()
        old_attrs = {"name": "test", "version": 1}
        new_attrs = {"name": "test", "version": 1, "description": "new field"}

        diff = engine._diff_attributes(old_attrs, new_attrs)

        assert "description" in diff["added"]
        assert diff["added"]["description"] == "new field"
        assert len(diff["removed"]) == 0
        assert len(diff["modified"]) == 0

    def test_diff_attributes_removed(self):
        """_diff_attributes detects removed attributes"""
        engine = DiffEngine()
        old_attrs = {"name": "test", "version": 1, "deprecated": True}
        new_attrs = {"name": "test", "version": 1}

        diff = engine._diff_attributes(old_attrs, new_attrs)

        assert "deprecated" in diff["removed"]
        assert diff["removed"]["deprecated"] is True
        assert len(diff["added"]) == 0
        assert len(diff["modified"]) == 0

    def test_diff_attributes_modified(self):
        """_diff_attributes detects modified attributes"""
        engine = DiffEngine()
        old_attrs = {"name": "test", "version": 1}
        new_attrs = {"name": "test", "version": 2}

        diff = engine._diff_attributes(old_attrs, new_attrs)

        assert "version" in diff["modified"]
        assert diff["modified"]["version"]["old"] == 1
        assert diff["modified"]["version"]["new"] == 2
        assert len(diff["added"]) == 0
        assert len(diff["removed"]) == 0

    def test_diff_attributes_all_changes(self):
        """_diff_attributes handles all change types together"""
        engine = DiffEngine()
        old_attrs = {
            "name": "test",
            "version": 1,
            "deprecated": True,
            "type": "python"
        }
        new_attrs = {
            "name": "test",
            "version": 2,
            "description": "new field",
            "type": "python"
        }

        diff = engine._diff_attributes(old_attrs, new_attrs)

        # Added
        assert "description" in diff["added"]
        # Removed
        assert "deprecated" in diff["removed"]
        # Modified
        assert "version" in diff["modified"]
        assert diff["modified"]["version"]["old"] == 1
        assert diff["modified"]["version"]["new"] == 2

    def test_summary_empty(self):
        """Summary of empty diff list"""
        engine = DiffEngine()
        diffs = []

        summary = engine.summary(diffs)

        assert summary["added"] == 0
        assert summary["removed"] == 0
        assert summary["modified"] == 0
        assert summary["unchanged"] == 0

    def test_summary_counts(self):
        """Summary counts each change type correctly"""
        engine = DiffEngine()
        diffs = [
            ResourceDiff(ChangeType.ADDED, "r1", "project"),
            ResourceDiff(ChangeType.ADDED, "r2", "project"),
            ResourceDiff(ChangeType.REMOVED, "r3", "dataset"),
            ResourceDiff(ChangeType.MODIFIED, "r4", "recipe"),
            ResourceDiff(ChangeType.MODIFIED, "r5", "recipe"),
            ResourceDiff(ChangeType.MODIFIED, "r6", "recipe"),
            ResourceDiff(ChangeType.UNCHANGED, "r7", "model"),
        ]

        summary = engine.summary(diffs)

        assert summary["added"] == 2
        assert summary["removed"] == 1
        assert summary["modified"] == 3
        assert summary["unchanged"] == 1

    def test_format_output_without_unchanged(self):
        """Format output excludes unchanged resources by default"""
        engine = DiffEngine()
        diffs = [
            ResourceDiff(ChangeType.ADDED, "project.NEW", "project"),
            ResourceDiff(ChangeType.REMOVED, "dataset.OLD.DATA", "dataset"),
            ResourceDiff(ChangeType.UNCHANGED, "model.TEST.PRED", "model"),
        ]

        output = engine.format_output(diffs, include_unchanged=False)

        # Should have summary
        assert "Diff Summary:" in output
        assert "1 added" in output
        assert "1 removed" in output
        assert "0 modified" in output
        # Should NOT list unchanged count without include_unchanged

        # Should show added and removed, not unchanged
        assert "+ project.NEW" in output
        assert "- dataset.OLD.DATA" in output
        assert "model.TEST.PRED" not in output

    def test_format_output_with_unchanged(self):
        """Format output includes unchanged resources when requested"""
        engine = DiffEngine()
        diffs = [
            ResourceDiff(ChangeType.ADDED, "project.NEW", "project"),
            ResourceDiff(ChangeType.UNCHANGED, "model.TEST.PRED", "model"),
        ]

        output = engine.format_output(diffs, include_unchanged=True)

        # Should show unchanged count
        assert "1 unchanged" in output

        # Should show both
        assert "+ project.NEW" in output
        assert "model.TEST.PRED" in output

    def test_format_output_shows_attribute_changes(self):
        """Format output shows detailed attribute changes for modified resources"""
        engine = DiffEngine()

        old_resource = Resource(
            resource_type="recipe",
            resource_id="recipe.TEST.PREP",
            attributes={"type": "python", "version": 1}
        )
        new_resource = Resource(
            resource_type="recipe",
            resource_id="recipe.TEST.PREP",
            attributes={"type": "python", "version": 2}
        )

        diffs = [
            ResourceDiff(
                change_type=ChangeType.MODIFIED,
                resource_id="recipe.TEST.PREP",
                resource_type="recipe",
                old_resource=old_resource,
                new_resource=new_resource,
                attribute_diffs={
                    "added": {},
                    "removed": {},
                    "modified": {
                        "version": {"old": 1, "new": 2}
                    }
                }
            )
        ]

        output = engine.format_output(diffs)

        # Should show the resource
        assert "~ recipe.TEST.PREP" in output

        # Should show the attribute change
        assert "version: 1 → 2" in output

    def test_diff_maintains_resource_order(self):
        """Diff results maintain consistent ordering"""
        engine = DiffEngine()
        old_state = State(environment="dev")
        new_state = State(environment="dev")

        # Add multiple resources
        for i in range(5):
            old_state.add_resource(Resource(
                resource_type="dataset",
                resource_id=f"dataset.TEST.DATA{i}",
                attributes={"index": i}
            ))
            new_state.add_resource(Resource(
                resource_type="dataset",
                resource_id=f"dataset.TEST.DATA{i}",
                attributes={"index": i}
            ))

        # Run diff multiple times
        diffs1 = engine.diff(old_state, new_state)
        diffs2 = engine.diff(old_state, new_state)

        # Should be identical
        assert len(diffs1) == len(diffs2)
        for i in range(len(diffs1)):
            assert diffs1[i].resource_id == diffs2[i].resource_id
            assert diffs1[i].change_type == diffs2[i].change_type
