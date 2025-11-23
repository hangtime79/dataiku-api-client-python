"""
Unit tests for diff models.
"""

import pytest
from dataikuapi.iac.models import ChangeType, ResourceDiff, Resource


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
