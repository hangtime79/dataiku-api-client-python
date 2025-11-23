"""
Unit tests for State and related models.
"""

import pytest
from datetime import datetime
from dataikuapi.iac.models import State, Resource, ResourceMetadata, make_resource_id


class TestResourceMetadata:
    """Test ResourceMetadata model"""

    def test_create_metadata(self):
        """Can create resource metadata"""
        now = datetime.utcnow()
        metadata = ResourceMetadata(
            deployed_at=now,
            deployed_by="test_user",
            dataiku_internal_id="test_id",
            checksum="abc123"
        )
        assert metadata.deployed_at == now
        assert metadata.deployed_by == "test_user"
        assert metadata.dataiku_internal_id == "test_id"
        assert metadata.checksum == "abc123"

    def test_metadata_to_dict(self):
        """Metadata can be converted to dict"""
        now = datetime.utcnow()
        metadata = ResourceMetadata(
            deployed_at=now,
            deployed_by="test_user",
            checksum="abc123"
        )
        data = metadata.to_dict()
        assert data["deployed_at"] == now.isoformat()
        assert data["deployed_by"] == "test_user"
        assert data["checksum"] == "abc123"

    def test_metadata_from_dict(self):
        """Metadata can be created from dict"""
        now = datetime.utcnow()
        data = {
            "deployed_at": now.isoformat(),
            "deployed_by": "test_user",
            "dataiku_internal_id": "test_id",
            "checksum": "abc123"
        }
        metadata = ResourceMetadata.from_dict(data)
        assert metadata.deployed_by == "test_user"
        assert metadata.dataiku_internal_id == "test_id"
        assert metadata.checksum == "abc123"

    def test_metadata_roundtrip(self):
        """Metadata to_dict/from_dict round-trip preserves data"""
        now = datetime.utcnow()
        original = ResourceMetadata(
            deployed_at=now,
            deployed_by="test_user",
            dataiku_internal_id="test_id",
            checksum="abc123"
        )
        data = original.to_dict()
        restored = ResourceMetadata.from_dict(data)
        assert restored.deployed_by == original.deployed_by
        assert restored.dataiku_internal_id == original.dataiku_internal_id
        assert restored.checksum == original.checksum


class TestState:
    """Test State model"""

    def test_create_empty_state(self):
        """Can create empty state"""
        state = State(environment="dev")
        assert state.version == 1
        assert state.serial == 0
        assert state.environment == "dev"
        assert state.lineage is None
        assert len(state.resources) == 0

    def test_create_state_with_defaults(self):
        """State has sensible defaults"""
        state = State()
        assert state.version == 1
        assert state.serial == 0
        assert state.environment == ""
        assert isinstance(state.updated_at, datetime)

    def test_add_resource(self):
        """Can add resource to state"""
        state = State()
        resource = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test Project"}
        )
        state.add_resource(resource)
        assert state.has_resource("project.TEST")
        assert len(state.resources) == 1

    def test_add_resource_increments_serial(self):
        """Adding resource increments serial"""
        state = State()
        initial_serial = state.serial

        resource = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test Project"}
        )
        state.add_resource(resource)

        assert state.serial == initial_serial + 1

    def test_add_resource_updates_timestamp(self):
        """Adding resource updates timestamp"""
        state = State()
        initial_time = state.updated_at

        # Sleep briefly to ensure time difference
        import time
        time.sleep(0.01)

        resource = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test Project"}
        )
        state.add_resource(resource)

        assert state.updated_at > initial_time

    def test_get_resource(self):
        """Can retrieve resource by ID"""
        state = State()
        resource = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test Project"}
        )
        state.add_resource(resource)

        retrieved = state.get_resource("project.TEST")
        assert retrieved is not None
        assert retrieved.resource_id == "project.TEST"
        assert retrieved.attributes["name"] == "Test Project"

    def test_get_nonexistent_resource(self):
        """Getting nonexistent resource returns None"""
        state = State()
        assert state.get_resource("project.NONEXISTENT") is None

    def test_remove_resource(self):
        """Can remove resource from state"""
        state = State()
        resource = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test Project"}
        )
        state.add_resource(resource)

        removed = state.remove_resource("project.TEST")
        assert removed is not None
        assert removed.resource_id == "project.TEST"
        assert not state.has_resource("project.TEST")
        assert len(state.resources) == 0

    def test_remove_resource_increments_serial(self):
        """Removing resource increments serial"""
        state = State()
        resource = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test Project"}
        )
        state.add_resource(resource)

        serial_after_add = state.serial
        state.remove_resource("project.TEST")

        assert state.serial == serial_after_add + 1

    def test_remove_nonexistent_resource(self):
        """Removing nonexistent resource returns None and doesn't increment serial"""
        state = State()
        initial_serial = state.serial

        removed = state.remove_resource("project.NONEXISTENT")

        assert removed is None
        assert state.serial == initial_serial

    def test_has_resource(self):
        """Can check if resource exists"""
        state = State()
        resource = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test Project"}
        )

        assert not state.has_resource("project.TEST")
        state.add_resource(resource)
        assert state.has_resource("project.TEST")

    def test_list_all_resources(self):
        """Can list all resources"""
        state = State()

        # Add multiple resources
        state.add_resource(Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test"}
        ))
        state.add_resource(Resource(
            resource_type="dataset",
            resource_id="dataset.TEST.DATA1",
            attributes={"name": "Data1"}
        ))
        state.add_resource(Resource(
            resource_type="dataset",
            resource_id="dataset.TEST.DATA2",
            attributes={"name": "Data2"}
        ))

        resources = state.list_resources()
        assert len(resources) == 3

    def test_list_resources_filtered_by_type(self):
        """Can list resources filtered by type"""
        state = State()

        # Add multiple resources
        state.add_resource(Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test"}
        ))
        state.add_resource(Resource(
            resource_type="dataset",
            resource_id="dataset.TEST.DATA1",
            attributes={"name": "Data1"}
        ))
        state.add_resource(Resource(
            resource_type="dataset",
            resource_id="dataset.TEST.DATA2",
            attributes={"name": "Data2"}
        ))

        # Filter by type
        datasets = state.list_resources(resource_type="dataset")
        projects = state.list_resources(resource_type="project")

        assert len(datasets) == 2
        assert len(projects) == 1
        assert all(r.resource_type == "dataset" for r in datasets)
        assert all(r.resource_type == "project" for r in projects)

    def test_list_resources_empty_state(self):
        """Listing resources on empty state returns empty list"""
        state = State()
        assert state.list_resources() == []
        assert state.list_resources(resource_type="project") == []

    def test_state_to_dict(self):
        """State can be converted to dict"""
        state = State(environment="dev", serial=5, lineage="git:abc123")
        state.add_resource(Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test"}
        ))

        data = state.to_dict()

        assert data["version"] == 1
        assert data["serial"] == 6  # Incremented when resource added
        assert data["environment"] == "dev"
        assert data["lineage"] == "git:abc123"
        assert "updated_at" in data
        assert "resources" in data
        assert "project.TEST" in data["resources"]

    def test_state_from_dict(self):
        """State can be created from dict"""
        now = datetime.utcnow()
        data = {
            "version": 1,
            "serial": 5,
            "lineage": "git:abc123",
            "environment": "prod",
            "updated_at": now.isoformat(),
            "resources": {
                "project.TEST": {
                    "resource_type": "project",
                    "resource_id": "project.TEST",
                    "attributes": {"name": "Test"},
                    "metadata": {
                        "deployed_at": now.isoformat(),
                        "deployed_by": "test_user",
                        "checksum": "abc123"
                    }
                }
            }
        }

        state = State.from_dict(data)

        assert state.version == 1
        assert state.serial == 5
        assert state.lineage == "git:abc123"
        assert state.environment == "prod"
        assert state.has_resource("project.TEST")

    def test_state_to_dict_from_dict_roundtrip(self):
        """State serialization round-trip preserves data"""
        original = State(environment="prod", serial=5, lineage="git:abc123")
        original.add_resource(Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"key": "value"}
        ))
        original.add_resource(Resource(
            resource_type="dataset",
            resource_id="dataset.TEST.DATA",
            attributes={"type": "Snowflake"}
        ))

        # Convert to dict and back
        data = original.to_dict()
        restored = State.from_dict(data)

        assert restored.version == original.version
        assert restored.serial == original.serial
        assert restored.environment == original.environment
        assert restored.lineage == original.lineage
        assert len(restored.resources) == len(original.resources)
        assert restored.has_resource("project.TEST")
        assert restored.has_resource("dataset.TEST.DATA")

    def test_update_resource(self):
        """Adding resource with same ID updates it"""
        state = State()

        # Add initial resource
        resource1 = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Original"}
        )
        state.add_resource(resource1)

        # Update with new attributes
        resource2 = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Updated"}
        )
        state.add_resource(resource2)

        # Should have only one resource
        assert len(state.resources) == 1
        retrieved = state.get_resource("project.TEST")
        assert retrieved.attributes["name"] == "Updated"

    def test_multiple_resource_types(self):
        """State can hold multiple resource types"""
        state = State()

        state.add_resource(Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={}
        ))
        state.add_resource(Resource(
            resource_type="dataset",
            resource_id="dataset.TEST.DATA",
            attributes={}
        ))
        state.add_resource(Resource(
            resource_type="recipe",
            resource_id="recipe.TEST.PREP",
            attributes={}
        ))
        state.add_resource(Resource(
            resource_type="model",
            resource_id="model.TEST.PREDICTOR",
            attributes={}
        ))

        assert len(state.resources) == 4
        assert len(state.list_resources(resource_type="project")) == 1
        assert len(state.list_resources(resource_type="dataset")) == 1
        assert len(state.list_resources(resource_type="recipe")) == 1
        assert len(state.list_resources(resource_type="model")) == 1
