"""
Unit tests for Resource model and validation.
"""

import pytest
from datetime import datetime
from dataikuapi.iac.models import Resource, ResourceMetadata, make_resource_id


class TestMakeResourceId:
    """Test make_resource_id helper function"""

    def test_project_resource_id(self):
        """Can create project resource ID"""
        resource_id = make_resource_id("project", "CUSTOMER_ANALYTICS")
        assert resource_id == "project.CUSTOMER_ANALYTICS"

    def test_dataset_resource_id(self):
        """Can create dataset resource ID"""
        resource_id = make_resource_id("dataset", "CUSTOMER_ANALYTICS", "RAW_CUSTOMERS")
        assert resource_id == "dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS"

    def test_recipe_resource_id(self):
        """Can create recipe resource ID"""
        resource_id = make_resource_id("recipe", "CUSTOMER_ANALYTICS", "prep_customers")
        assert resource_id == "recipe.CUSTOMER_ANALYTICS.prep_customers"

    def test_model_resource_id(self):
        """Can create model resource ID"""
        resource_id = make_resource_id("model", "ML_PROJECT", "churn_prediction")
        assert resource_id == "model.ML_PROJECT.churn_prediction"

    def test_resource_id_without_name(self):
        """Can create resource ID without resource name"""
        resource_id = make_resource_id("project", "TEST_PROJECT")
        assert resource_id == "project.TEST_PROJECT"


class TestResourceValidation:
    """Test Resource ID validation"""

    def test_valid_project_resource_id(self):
        """Valid project resource ID is accepted"""
        resource = Resource(
            resource_type="project",
            resource_id="project.TEST_PROJECT",
            attributes={}
        )
        assert resource.resource_id == "project.TEST_PROJECT"

    def test_valid_dataset_resource_id(self):
        """Valid dataset resource ID is accepted"""
        resource = Resource(
            resource_type="dataset",
            resource_id="dataset.TEST_PROJECT.MY_DATASET",
            attributes={}
        )
        assert resource.resource_id == "dataset.TEST_PROJECT.MY_DATASET"

    def test_invalid_resource_id_too_short(self):
        """Resource ID with only one part is rejected"""
        with pytest.raises(ValueError, match="Invalid resource_id format"):
            Resource(
                resource_type="project",
                resource_id="project",
                attributes={}
            )

    def test_invalid_resource_id_type_mismatch(self):
        """Resource ID with mismatched type prefix is rejected"""
        with pytest.raises(ValueError, match="doesn't match resource_type"):
            Resource(
                resource_type="project",
                resource_id="dataset.TEST_PROJECT",
                attributes={}
            )

    def test_invalid_resource_id_empty(self):
        """Empty resource ID is rejected"""
        with pytest.raises(ValueError, match="Invalid resource_id format"):
            Resource(
                resource_type="project",
                resource_id="",
                attributes={}
            )


class TestResourceChecksum:
    """Test Resource checksum computation"""

    def test_checksum_is_computed_automatically(self):
        """Checksum is computed automatically on creation"""
        resource = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test"}
        )
        assert resource.metadata.checksum != ""
        assert len(resource.metadata.checksum) == 64  # SHA256 hex length

    def test_checksum_is_deterministic(self):
        """Same attributes produce same checksum"""
        resource1 = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test", "key": "value"}
        )
        resource2 = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test", "key": "value"}
        )
        assert resource1.compute_checksum() == resource2.compute_checksum()

    def test_checksum_ignores_key_order(self):
        """Checksum is same regardless of key order"""
        resource1 = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"a": 1, "b": 2, "c": 3}
        )
        resource2 = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"c": 3, "a": 1, "b": 2}
        )
        assert resource1.compute_checksum() == resource2.compute_checksum()

    def test_checksum_differs_for_different_attributes(self):
        """Different attributes produce different checksums"""
        resource1 = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test1"}
        )
        resource2 = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test2"}
        )
        assert resource1.compute_checksum() != resource2.compute_checksum()

    def test_checksum_differs_for_nested_changes(self):
        """Checksum detects changes in nested attributes"""
        resource1 = Resource(
            resource_type="dataset",
            resource_id="dataset.TEST.DATA",
            attributes={"params": {"connection": "snowflake", "table": "customers"}}
        )
        resource2 = Resource(
            resource_type="dataset",
            resource_id="dataset.TEST.DATA",
            attributes={"params": {"connection": "snowflake", "table": "orders"}}
        )
        assert resource1.compute_checksum() != resource2.compute_checksum()


class TestResourceComparison:
    """Test Resource has_changed method"""

    def test_has_changed_same_attributes(self):
        """Resources with same attributes have not changed"""
        resource1 = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test"}
        )
        resource2 = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test"}
        )
        assert not resource1.has_changed(resource2)

    def test_has_changed_different_attributes(self):
        """Resources with different attributes have changed"""
        resource1 = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test1"}
        )
        resource2 = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test2"}
        )
        assert resource1.has_changed(resource2)

    def test_has_changed_different_resource_id_raises(self):
        """Comparing different resources raises error"""
        resource1 = Resource(
            resource_type="project",
            resource_id="project.TEST1",
            attributes={}
        )
        resource2 = Resource(
            resource_type="project",
            resource_id="project.TEST2",
            attributes={}
        )
        with pytest.raises(ValueError, match="Cannot compare different resources"):
            resource1.has_changed(resource2)

    def test_has_changed_added_attribute(self):
        """Adding an attribute is detected as changed"""
        resource1 = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test"}
        )
        resource2 = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test", "description": "New"}
        )
        assert resource1.has_changed(resource2)

    def test_has_changed_removed_attribute(self):
        """Removing an attribute is detected as changed"""
        resource1 = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test", "description": "Old"}
        )
        resource2 = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test"}
        )
        assert resource1.has_changed(resource2)


class TestResourceSerialization:
    """Test Resource serialization"""

    def test_resource_to_dict(self):
        """Resource can be converted to dict"""
        resource = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test Project"}
        )
        data = resource.to_dict()

        assert data["resource_type"] == "project"
        assert data["resource_id"] == "project.TEST"
        assert data["attributes"]["name"] == "Test Project"
        assert "metadata" in data
        assert "checksum" in data["metadata"]

    def test_resource_from_dict(self):
        """Resource can be created from dict"""
        now = datetime.utcnow()
        data = {
            "resource_type": "dataset",
            "resource_id": "dataset.TEST.DATA",
            "attributes": {"type": "Snowflake"},
            "metadata": {
                "deployed_at": now.isoformat(),
                "deployed_by": "test_user",
                "dataiku_internal_id": "DATA",
                "checksum": "abc123"
            }
        }
        resource = Resource.from_dict(data)

        assert resource.resource_type == "dataset"
        assert resource.resource_id == "dataset.TEST.DATA"
        assert resource.attributes["type"] == "Snowflake"
        assert resource.metadata.deployed_by == "test_user"

    def test_resource_to_dict_from_dict_roundtrip(self):
        """Resource serialization round-trip preserves data"""
        original = Resource(
            resource_type="recipe",
            resource_id="recipe.TEST.PREP",
            attributes={
                "type": "python",
                "inputs": {"main": "input_dataset"},
                "outputs": {"main": "output_dataset"}
            }
        )

        # Convert to dict and back
        data = original.to_dict()
        restored = Resource.from_dict(data)

        assert restored.resource_type == original.resource_type
        assert restored.resource_id == original.resource_id
        assert restored.attributes == original.attributes
        # Checksums should match
        assert restored.metadata.checksum == original.metadata.checksum


class TestResourceProperties:
    """Test Resource property accessors"""

    def test_project_key_extraction_project(self):
        """Can extract project key from project resource"""
        resource = Resource(
            resource_type="project",
            resource_id="project.CUSTOMER_ANALYTICS",
            attributes={}
        )
        assert resource.project_key == "CUSTOMER_ANALYTICS"

    def test_project_key_extraction_dataset(self):
        """Can extract project key from dataset resource"""
        resource = Resource(
            resource_type="dataset",
            resource_id="dataset.CUSTOMER_ANALYTICS.RAW_DATA",
            attributes={}
        )
        assert resource.project_key == "CUSTOMER_ANALYTICS"

    def test_resource_name_extraction_dataset(self):
        """Can extract resource name from dataset resource"""
        resource = Resource(
            resource_type="dataset",
            resource_id="dataset.CUSTOMER_ANALYTICS.RAW_DATA",
            attributes={}
        )
        assert resource.resource_name == "RAW_DATA"

    def test_resource_name_extraction_recipe(self):
        """Can extract resource name from recipe resource"""
        resource = Resource(
            resource_type="recipe",
            resource_id="recipe.ML_PROJECT.prep_data",
            attributes={}
        )
        assert resource.resource_name == "prep_data"

    def test_resource_name_empty_for_project(self):
        """Resource name is empty for project resources"""
        resource = Resource(
            resource_type="project",
            resource_id="project.TEST_PROJECT",
            attributes={}
        )
        assert resource.resource_name == ""

    def test_complex_resource_id_parsing(self):
        """Can parse complex resource IDs with dots in name"""
        resource = Resource(
            resource_type="dataset",
            resource_id="dataset.MY_PROJECT.data.with.dots",
            attributes={}
        )
        # Note: This extracts the third part only
        # If names can have dots, we might need to adjust parsing logic
        assert resource.project_key == "MY_PROJECT"
        assert resource.resource_name == "data.with.dots"


class TestResourceMetadata:
    """Test Resource metadata handling"""

    def test_default_metadata_created(self):
        """Default metadata is created if not provided"""
        resource = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={}
        )
        assert resource.metadata is not None
        assert resource.metadata.deployed_by == "system"
        assert isinstance(resource.metadata.deployed_at, datetime)

    def test_custom_metadata(self):
        """Can provide custom metadata"""
        now = datetime.utcnow()
        metadata = ResourceMetadata(
            deployed_at=now,
            deployed_by="custom_user",
            dataiku_internal_id="test_id",
            checksum=""  # Will be computed
        )
        resource = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test"},
            metadata=metadata
        )

        assert resource.metadata.deployed_by == "custom_user"
        assert resource.metadata.dataiku_internal_id == "test_id"
        # Checksum should be computed even if provided as empty
        assert resource.metadata.checksum != ""

    def test_empty_attributes(self):
        """Resource can have empty attributes"""
        resource = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={}
        )
        assert resource.attributes == {}
        assert resource.metadata.checksum != ""  # Checksum still computed

    def test_complex_attributes(self):
        """Resource can have complex nested attributes"""
        resource = Resource(
            resource_type="dataset",
            resource_id="dataset.TEST.DATA",
            attributes={
                "type": "Snowflake",
                "params": {
                    "connection": "my_connection",
                    "table": "customers",
                    "catalog": "production"
                },
                "schema": {
                    "columns": [
                        {"name": "id", "type": "int"},
                        {"name": "name", "type": "string"}
                    ]
                },
                "tags": ["important", "pii"]
            }
        )

        assert resource.attributes["type"] == "Snowflake"
        assert resource.attributes["params"]["connection"] == "my_connection"
        assert len(resource.attributes["schema"]["columns"]) == 2
        assert "important" in resource.attributes["tags"]
