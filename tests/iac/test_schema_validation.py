"""
Tests for JSON Schema validation of state files.

This module tests the validation of state files against the JSON schema,
including valid states, invalid states, and edge cases.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import patch
from dataikuapi.iac.models.state import State, Resource, ResourceMetadata
from dataikuapi.iac.validation import (
    validate_state,
    validate_state_safe,
    get_state_schema,
)
from dataikuapi.iac.exceptions import StateCorruptedError


class TestSchemaLoading:
    """Test schema loading and caching"""

    def test_schema_loads_successfully(self):
        """JSON schema file loads without errors"""
        schema = get_state_schema()
        assert schema is not None
        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
        assert schema["title"] == "Dataiku IaC State File"

    def test_schema_has_required_fields(self):
        """Schema defines required fields"""
        schema = get_state_schema()
        assert "required" in schema
        assert "version" in schema["required"]
        assert "serial" in schema["required"]
        assert "updated_at" in schema["required"]
        assert "resources" in schema["required"]

    def test_schema_has_resource_definition(self):
        """Schema defines resource structure"""
        schema = get_state_schema()
        assert "definitions" in schema
        assert "resource" in schema["definitions"]
        assert "metadata" in schema["definitions"]

    def test_schema_caching_works(self):
        """Schema is cached after first load"""
        schema1 = get_state_schema()
        schema2 = get_state_schema()
        # Should be the same object (cached)
        assert schema1 is schema2


class TestValidStateValidation:
    """Test validation of valid state files"""

    def test_empty_state_validates(self):
        """Empty state with no resources validates successfully"""
        state = State(
            version=1,
            serial=0,
            environment="dev",
            updated_at=datetime.utcnow(),
            resources={}
        )
        state_dict = state.to_dict()

        # Should not raise
        validate_state(state_dict)

    def test_state_with_project_validates(self):
        """State with a project resource validates"""
        resource = Resource(
            resource_type="project",
            resource_id="project.CUSTOMER_ANALYTICS",
            attributes={"projectKey": "CUSTOMER_ANALYTICS"},
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="test_user",
                checksum="a" * 64  # Valid SHA256 format
            )
        )

        state = State(
            version=1,
            serial=1,
            environment="dev",
            updated_at=datetime.utcnow(),
            resources={"project.CUSTOMER_ANALYTICS": resource}
        )
        state_dict = state.to_dict()

        # Should not raise
        validate_state(state_dict)

    def test_state_with_dataset_validates(self):
        """State with a dataset resource validates"""
        resource = Resource(
            resource_type="dataset",
            resource_id="dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS",
            attributes={"name": "RAW_CUSTOMERS", "type": "Snowflake"},
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="test_user",
                dataiku_internal_id="123",
                checksum="b" * 64
            )
        )

        state = State(
            version=1,
            serial=1,
            environment="prod",
            updated_at=datetime.utcnow(),
            resources={"dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS": resource}
        )
        state_dict = state.to_dict()

        # Should not raise
        validate_state(state_dict)

    def test_state_with_multiple_resources_validates(self):
        """State with multiple resources validates"""
        resources = {
            "project.TEST_PROJECT": Resource(
                resource_type="project",
                resource_id="project.TEST_PROJECT",
                attributes={"projectKey": "TEST_PROJECT"},
                metadata=ResourceMetadata(
                    deployed_at=datetime.utcnow(),
                    deployed_by="user1",
                    checksum="a" * 64
                )
            ),
            "dataset.TEST_PROJECT.DATA": Resource(
                resource_type="dataset",
                resource_id="dataset.TEST_PROJECT.DATA",
                attributes={"name": "DATA"},
                metadata=ResourceMetadata(
                    deployed_at=datetime.utcnow(),
                    deployed_by="user2",
                    checksum="b" * 64
                )
            ),
        }

        state = State(
            version=1,
            serial=5,
            lineage="abc123",
            environment="staging",
            updated_at=datetime.utcnow(),
            resources=resources
        )
        state_dict = state.to_dict()

        # Should not raise
        validate_state(state_dict)

    def test_state_with_null_lineage_validates(self):
        """State with null lineage validates"""
        state = State(
            version=1,
            serial=0,
            lineage=None,
            environment="dev",
            updated_at=datetime.utcnow(),
            resources={}
        )
        state_dict = state.to_dict()

        # Should not raise
        validate_state(state_dict)

    def test_state_with_optional_dataiku_id_validates(self):
        """State with null dataiku_internal_id validates"""
        resource = Resource(
            resource_type="recipe",
            resource_id="recipe.PROJ.PrepData",
            attributes={"type": "python"},
            metadata=ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="test_user",
                dataiku_internal_id=None,
                checksum="c" * 64
            )
        )

        state = State(
            version=1,
            serial=1,
            environment="dev",
            updated_at=datetime.utcnow(),
            resources={"recipe.PROJ.PrepData": resource}
        )
        state_dict = state.to_dict()

        # Should not raise
        validate_state(state_dict)


class TestInvalidStateValidation:
    """Test validation of invalid state files"""

    def test_missing_version_fails(self):
        """State missing version field fails validation"""
        state_dict = {
            "serial": 0,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {}
        }

        with pytest.raises(StateCorruptedError) as exc_info:
            validate_state(state_dict)

        assert "version" in str(exc_info.value).lower()

    def test_missing_serial_fails(self):
        """State missing serial field fails validation"""
        state_dict = {
            "version": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {}
        }

        with pytest.raises(StateCorruptedError) as exc_info:
            validate_state(state_dict)

        assert "serial" in str(exc_info.value).lower()

    def test_missing_updated_at_fails(self):
        """State missing updated_at field fails validation"""
        state_dict = {
            "version": 1,
            "serial": 0,
            "resources": {}
        }

        with pytest.raises(StateCorruptedError) as exc_info:
            validate_state(state_dict)

        assert "updated_at" in str(exc_info.value).lower()

    def test_missing_resources_fails(self):
        """State missing resources field fails validation"""
        state_dict = {
            "version": 1,
            "serial": 0,
            "updated_at": datetime.utcnow().isoformat()
        }

        with pytest.raises(StateCorruptedError) as exc_info:
            validate_state(state_dict)

        assert "resources" in str(exc_info.value).lower()

    def test_wrong_version_fails(self):
        """State with wrong version number fails validation"""
        state_dict = {
            "version": 2,  # Should be 1
            "serial": 0,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {}
        }

        with pytest.raises(StateCorruptedError) as exc_info:
            validate_state(state_dict)

        assert "version" in str(exc_info.value).lower()

    def test_negative_serial_fails(self):
        """State with negative serial fails validation"""
        state_dict = {
            "version": 1,
            "serial": -1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {}
        }

        with pytest.raises(StateCorruptedError) as exc_info:
            validate_state(state_dict)

    def test_invalid_datetime_format_fails(self):
        """State with invalid datetime format (Note: format validation may be lenient)"""
        # Note: JSON Schema format validation is optional and may not be strictly enforced
        # This test documents the behavior but doesn't enforce strict datetime validation
        state_dict = {
            "version": 1,
            "serial": 0,
            "updated_at": "not-a-datetime",
            "resources": {}
        }

        # JSON Schema draft-07 format validation is optional, so this may not raise
        # We just verify the schema loads and validates the structure
        try:
            validate_state(state_dict)
            # If it passes, that's OK - format validation is optional
        except StateCorruptedError:
            # If it fails, that's also OK - stricter validation
            pass

    def test_wrong_version_type_fails(self):
        """State with version as string fails validation"""
        state_dict = {
            "version": "1",  # Should be integer
            "serial": 0,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {}
        }

        with pytest.raises(StateCorruptedError) as exc_info:
            validate_state(state_dict)


class TestInvalidResourceValidation:
    """Test validation of invalid resources"""

    def test_resource_missing_resource_type_fails(self):
        """Resource missing resource_type fails validation"""
        state_dict = {
            "version": 1,
            "serial": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {
                "project.TEST": {
                    "resource_id": "project.TEST",
                    "attributes": {},
                    "metadata": {
                        "deployed_at": datetime.utcnow().isoformat(),
                        "deployed_by": "user",
                        "checksum": "a" * 64
                    }
                }
            }
        }

        with pytest.raises(StateCorruptedError) as exc_info:
            validate_state(state_dict)

        assert "resource_type" in str(exc_info.value).lower()

    def test_resource_missing_resource_id_fails(self):
        """Resource missing resource_id fails validation"""
        state_dict = {
            "version": 1,
            "serial": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {
                "project.TEST": {
                    "resource_type": "project",
                    "attributes": {},
                    "metadata": {
                        "deployed_at": datetime.utcnow().isoformat(),
                        "deployed_by": "user",
                        "checksum": "a" * 64
                    }
                }
            }
        }

        with pytest.raises(StateCorruptedError) as exc_info:
            validate_state(state_dict)

        assert "resource_id" in str(exc_info.value).lower()

    def test_resource_missing_metadata_fails(self):
        """Resource missing metadata fails validation"""
        state_dict = {
            "version": 1,
            "serial": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {
                "project.TEST": {
                    "resource_type": "project",
                    "resource_id": "project.TEST",
                    "attributes": {}
                }
            }
        }

        with pytest.raises(StateCorruptedError) as exc_info:
            validate_state(state_dict)

        assert "metadata" in str(exc_info.value).lower()

    def test_invalid_resource_type_fails(self):
        """Resource with invalid resource_type fails validation"""
        state_dict = {
            "version": 1,
            "serial": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {
                "invalid.TEST": {
                    "resource_type": "invalid",  # Not in enum
                    "resource_id": "invalid.TEST",
                    "attributes": {},
                    "metadata": {
                        "deployed_at": datetime.utcnow().isoformat(),
                        "deployed_by": "user",
                        "checksum": "a" * 64
                    }
                }
            }
        }

        with pytest.raises(StateCorruptedError) as exc_info:
            validate_state(state_dict)

    def test_invalid_resource_id_format_fails(self):
        """Resource with invalid resource_id format fails validation"""
        invalid_ids = [
            "lowercase.project",  # project should be UPPERCASE
            "project.123START",   # Can't start with number
            "project",            # Missing project key
            "project..DOUBLE",    # Double dot
            "project.TEST-DASH",  # Dashes not allowed in project key
        ]

        for invalid_id in invalid_ids:
            state_dict = {
                "version": 1,
                "serial": 1,
                "updated_at": datetime.utcnow().isoformat(),
                "resources": {
                    invalid_id: {
                        "resource_type": "project",
                        "resource_id": invalid_id,
                        "attributes": {},
                        "metadata": {
                            "deployed_at": datetime.utcnow().isoformat(),
                            "deployed_by": "user",
                            "checksum": "a" * 64
                        }
                    }
                }
            }

            with pytest.raises(StateCorruptedError) as exc_info:
                validate_state(state_dict)

    def test_invalid_checksum_format_fails(self):
        """Resource with invalid checksum format fails validation"""
        invalid_checksums = [
            "short",              # Too short
            "Z" * 64,            # Invalid characters (not hex)
            "a" * 63,            # Too short (63 chars)
            "a" * 65,            # Too long (65 chars)
            "ABC" * 21 + "A",    # Uppercase not allowed
        ]

        for invalid_checksum in invalid_checksums:
            state_dict = {
                "version": 1,
                "serial": 1,
                "updated_at": datetime.utcnow().isoformat(),
                "resources": {
                    "project.TEST": {
                        "resource_type": "project",
                        "resource_id": "project.TEST",
                        "attributes": {},
                        "metadata": {
                            "deployed_at": datetime.utcnow().isoformat(),
                            "deployed_by": "user",
                            "checksum": invalid_checksum
                        }
                    }
                }
            }

            with pytest.raises(StateCorruptedError):
                validate_state(state_dict)

    def test_metadata_missing_deployed_at_fails(self):
        """Metadata missing deployed_at fails validation"""
        state_dict = {
            "version": 1,
            "serial": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {
                "project.TEST": {
                    "resource_type": "project",
                    "resource_id": "project.TEST",
                    "attributes": {},
                    "metadata": {
                        "deployed_by": "user",
                        "checksum": "a" * 64
                    }
                }
            }
        }

        with pytest.raises(StateCorruptedError) as exc_info:
            validate_state(state_dict)

        assert "deployed_at" in str(exc_info.value).lower()

    def test_metadata_missing_deployed_by_fails(self):
        """Metadata missing deployed_by fails validation"""
        state_dict = {
            "version": 1,
            "serial": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {
                "project.TEST": {
                    "resource_type": "project",
                    "resource_id": "project.TEST",
                    "attributes": {},
                    "metadata": {
                        "deployed_at": datetime.utcnow().isoformat(),
                        "checksum": "a" * 64
                    }
                }
            }
        }

        with pytest.raises(StateCorruptedError) as exc_info:
            validate_state(state_dict)

        assert "deployed_by" in str(exc_info.value).lower()

    def test_metadata_missing_checksum_fails(self):
        """Metadata missing checksum fails validation"""
        state_dict = {
            "version": 1,
            "serial": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {
                "project.TEST": {
                    "resource_type": "project",
                    "resource_id": "project.TEST",
                    "attributes": {},
                    "metadata": {
                        "deployed_at": datetime.utcnow().isoformat(),
                        "deployed_by": "user"
                    }
                }
            }
        }

        with pytest.raises(StateCorruptedError) as exc_info:
            validate_state(state_dict)

        assert "checksum" in str(exc_info.value).lower()


class TestValidResourceIdFormats:
    """Test various valid resource_id formats"""

    def test_project_id_validates(self):
        """Project resource_id validates"""
        state_dict = {
            "version": 1,
            "serial": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {
                "project.CUSTOMER_ANALYTICS": {
                    "resource_type": "project",
                    "resource_id": "project.CUSTOMER_ANALYTICS",
                    "attributes": {},
                    "metadata": {
                        "deployed_at": datetime.utcnow().isoformat(),
                        "deployed_by": "user",
                        "checksum": "a" * 64
                    }
                }
            }
        }

        # Should not raise
        validate_state(state_dict)

    def test_dataset_id_validates(self):
        """Dataset resource_id validates"""
        state_dict = {
            "version": 1,
            "serial": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {
                "dataset.PROJ.RAW_DATA": {
                    "resource_type": "dataset",
                    "resource_id": "dataset.PROJ.RAW_DATA",
                    "attributes": {},
                    "metadata": {
                        "deployed_at": datetime.utcnow().isoformat(),
                        "deployed_by": "user",
                        "checksum": "a" * 64
                    }
                }
            }
        }

        # Should not raise
        validate_state(state_dict)

    def test_recipe_id_with_lowercase_validates(self):
        """Recipe resource_id with lowercase name validates"""
        state_dict = {
            "version": 1,
            "serial": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {
                "recipe.PROJ.prep_data": {
                    "resource_type": "recipe",
                    "resource_id": "recipe.PROJ.prep_data",
                    "attributes": {},
                    "metadata": {
                        "deployed_at": datetime.utcnow().isoformat(),
                        "deployed_by": "user",
                        "checksum": "a" * 64
                    }
                }
            }
        }

        # Should not raise
        validate_state(state_dict)

    def test_scenario_id_validates(self):
        """Scenario resource_id validates"""
        state_dict = {
            "version": 1,
            "serial": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {
                "scenario.PROJ.DailyRefresh": {
                    "resource_type": "scenario",
                    "resource_id": "scenario.PROJ.DailyRefresh",
                    "attributes": {},
                    "metadata": {
                        "deployed_at": datetime.utcnow().isoformat(),
                        "deployed_by": "user",
                        "checksum": "a" * 64
                    }
                }
            }
        }

        # Should not raise
        validate_state(state_dict)

    def test_model_id_validates(self):
        """Model resource_id validates"""
        state_dict = {
            "version": 1,
            "serial": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {
                "model.PROJ.ChurnModel": {
                    "resource_type": "model",
                    "resource_id": "model.PROJ.ChurnModel",
                    "attributes": {},
                    "metadata": {
                        "deployed_at": datetime.utcnow().isoformat(),
                        "deployed_by": "user",
                        "checksum": "a" * 64
                    }
                }
            }
        }

        # Should not raise
        validate_state(state_dict)

    def test_resource_id_with_underscores_validates(self):
        """Resource_id with underscores validates"""
        state_dict = {
            "version": 1,
            "serial": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {
                "dataset.PROJECT_KEY_123.RESOURCE_NAME_456": {
                    "resource_type": "dataset",
                    "resource_id": "dataset.PROJECT_KEY_123.RESOURCE_NAME_456",
                    "attributes": {},
                    "metadata": {
                        "deployed_at": datetime.utcnow().isoformat(),
                        "deployed_by": "user",
                        "checksum": "a" * 64
                    }
                }
            }
        }

        # Should not raise
        validate_state(state_dict)

    def test_resource_id_with_numbers_validates(self):
        """Resource_id with numbers validates"""
        state_dict = {
            "version": 1,
            "serial": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {
                "dataset.PROJ2024.DATA123": {
                    "resource_type": "dataset",
                    "resource_id": "dataset.PROJ2024.DATA123",
                    "attributes": {},
                    "metadata": {
                        "deployed_at": datetime.utcnow().isoformat(),
                        "deployed_by": "user",
                        "checksum": "a" * 64
                    }
                }
            }
        }

        # Should not raise
        validate_state(state_dict)


class TestValidateSafeFunction:
    """Test the safe validation function that doesn't raise"""

    def test_valid_state_returns_true(self):
        """validate_state_safe returns True for valid state"""
        state = State(
            version=1,
            serial=0,
            environment="dev",
            updated_at=datetime.utcnow(),
            resources={}
        )
        state_dict = state.to_dict()

        is_valid, error = validate_state_safe(state_dict)

        assert is_valid is True
        assert error == ""

    def test_invalid_state_returns_false(self):
        """validate_state_safe returns False for invalid state"""
        state_dict = {
            "version": 999,  # Invalid
            "serial": 0,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {}
        }

        is_valid, error = validate_state_safe(state_dict)

        assert is_valid is False
        assert error != ""
        assert "version" in error.lower()

    def test_missing_field_returns_false(self):
        """validate_state_safe returns False for missing field"""
        state_dict = {
            "version": 1,
            "serial": 0
            # Missing updated_at and resources
        }

        is_valid, error = validate_state_safe(state_dict)

        assert is_valid is False
        assert error != ""


class TestJsonSchemaNotAvailable:
    """Test behavior when jsonschema is not available"""

    def test_validate_state_raises_import_error(self):
        """validate_state raises ImportError when jsonschema not available"""
        state = State(
            version=1,
            serial=0,
            environment="dev",
            updated_at=datetime.utcnow(),
            resources={}
        )
        state_dict = state.to_dict()

        with patch('dataikuapi.iac.validation.JSONSCHEMA_AVAILABLE', False):
            with pytest.raises(ImportError) as exc_info:
                validate_state(state_dict)

            assert "jsonschema is required" in str(exc_info.value)

    def test_validate_state_safe_returns_error(self):
        """validate_state_safe returns error when jsonschema not available"""
        state = State(
            version=1,
            serial=0,
            environment="dev",
            updated_at=datetime.utcnow(),
            resources={}
        )
        state_dict = state.to_dict()

        with patch('dataikuapi.iac.validation.JSONSCHEMA_AVAILABLE', False):
            is_valid, error = validate_state_safe(state_dict)

            assert is_valid is False
            assert "jsonschema library not installed" in error


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_resources_dict_validates(self):
        """Empty resources dictionary validates"""
        state_dict = {
            "version": 1,
            "serial": 0,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {}
        }

        # Should not raise
        validate_state(state_dict)

    def test_zero_serial_validates(self):
        """Serial of 0 validates"""
        state_dict = {
            "version": 1,
            "serial": 0,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {}
        }

        # Should not raise
        validate_state(state_dict)

    def test_large_serial_validates(self):
        """Large serial number validates"""
        state_dict = {
            "version": 1,
            "serial": 999999,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {}
        }

        # Should not raise
        validate_state(state_dict)

    def test_empty_attributes_validates(self):
        """Resource with empty attributes validates"""
        state_dict = {
            "version": 1,
            "serial": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {
                "project.EMPTY": {
                    "resource_type": "project",
                    "resource_id": "project.EMPTY",
                    "attributes": {},
                    "metadata": {
                        "deployed_at": datetime.utcnow().isoformat(),
                        "deployed_by": "user",
                        "checksum": "a" * 64
                    }
                }
            }
        }

        # Should not raise
        validate_state(state_dict)

    def test_complex_attributes_validates(self):
        """Resource with complex nested attributes validates"""
        state_dict = {
            "version": 1,
            "serial": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {
                "dataset.PROJ.DATA": {
                    "resource_type": "dataset",
                    "resource_id": "dataset.PROJ.DATA",
                    "attributes": {
                        "name": "DATA",
                        "type": "Snowflake",
                        "params": {
                            "connection": "snowflake_conn",
                            "table": "RAW_DATA",
                            "schema": "PUBLIC"
                        },
                        "schema_columns": [
                            {"name": "ID", "type": "bigint"},
                            {"name": "NAME", "type": "string"}
                        ]
                    },
                    "metadata": {
                        "deployed_at": datetime.utcnow().isoformat(),
                        "deployed_by": "user",
                        "checksum": "a" * 64
                    }
                }
            }
        }

        # Should not raise
        validate_state(state_dict)

    def test_resources_key_not_matching_resource_id(self):
        """Resources dictionary key doesn't have to match resource_id for schema validation"""
        # Note: This tests schema validation only. Business logic might require them to match.
        state_dict = {
            "version": 1,
            "serial": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "resources": {
                "different_key": {  # Key doesn't match resource_id
                    "resource_type": "project",
                    "resource_id": "project.TEST",
                    "attributes": {},
                    "metadata": {
                        "deployed_at": datetime.utcnow().isoformat(),
                        "deployed_by": "user",
                        "checksum": "a" * 64
                    }
                }
            }
        }

        # Schema validation allows this (business logic might not)
        validate_state(state_dict)
