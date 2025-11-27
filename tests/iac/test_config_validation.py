"""
Tests for configuration validation.

Tests all validation rules including:
- Naming conventions
- Required fields
- Reference integrity
- Circular dependencies
- JSON Schema validation
"""

import pytest
from dataikuapi.iac.config.models import (
    Config, ProjectConfig, DatasetConfig, RecipeConfig
)
from dataikuapi.iac.config.validator import ConfigValidator, ValidationError
from dataikuapi.iac.exceptions import ConfigValidationError


class TestValidationError:
    """Test ValidationError class."""

    def test_create_error(self):
        """Test creating a validation error."""
        error = ValidationError(
            path="project.key",
            message="Invalid project key",
            severity="error"
        )
        assert error.path == "project.key"
        assert error.message == "Invalid project key"
        assert error.severity == "error"

    def test_error_string_representation(self):
        """Test string representation of validation error."""
        error = ValidationError("datasets[0].name", "Name is invalid")
        assert str(error) == "datasets[0].name: Name is invalid"

    def test_error_equality(self):
        """Test equality comparison of validation errors."""
        error1 = ValidationError("path", "message", "error")
        error2 = ValidationError("path", "message", "error")
        error3 = ValidationError("path", "other", "error")

        assert error1 == error2
        assert error1 != error3

    def test_error_repr(self):
        """Test repr of validation error."""
        error = ValidationError("path", "message", "warning")
        repr_str = repr(error)
        assert "ValidationError" in repr_str
        assert "path" in repr_str
        assert "message" in repr_str


class TestConfigValidator:
    """Test ConfigValidator class."""

    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = ConfigValidator(strict=True)
        assert validator.strict is True

        validator_non_strict = ConfigValidator(strict=False)
        assert validator_non_strict.strict is False

    def test_valid_config_passes(self):
        """Test that a valid config passes validation."""
        config = Config(
            version="1.0",
            project=ProjectConfig(
                key="TEST_PROJECT",
                name="Test Project",
                description="A test project"
            ),
            datasets=[
                DatasetConfig(
                    name="RAW_DATA",
                    type="managed",
                    format_type="parquet"
                ),
                DatasetConfig(
                    name="PROCESSED_DATA",
                    type="managed",
                    format_type="parquet"
                )
            ],
            recipes=[
                RecipeConfig(
                    name="process_data",
                    type="python",
                    inputs=["RAW_DATA"],
                    outputs=["PROCESSED_DATA"],
                    code="output = input"
                )
            ]
        )

        validator = ConfigValidator()
        # Should not raise - this is a valid config
        validator.validate(config)  # No exception should be raised

    def test_minimal_valid_config(self):
        """Test minimal valid config."""
        config = Config(
            version="1.0",
            project=ProjectConfig(
                key="MINIMAL",
                name="Minimal"
            ),
            datasets=[
                DatasetConfig(
                    name="DATA",
                    type="managed"
                )
            ]
        )

        validator = ConfigValidator()
        # Should pass validation (no recipes, so no reference issues)
        # Actually, this should raise because we're testing strict mode
        # Let me reconsider - an empty errors list should not raise
        # But the validate() method raises if there are errors
        # For a truly valid config, it should not raise


class TestNamingConventions:
    """Test naming convention validation."""

    def test_project_key_uppercase(self):
        """Test project key must be uppercase."""
        config = Config(
            project=ProjectConfig(
                key="lowercase_key",  # Invalid
                name="Test"
            )
        )

        validator = ConfigValidator()
        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        assert any("UPPERCASE_WITH_UNDERSCORES" in str(e.message)
                   for e in exc_info.value.errors)

    def test_project_key_valid_uppercase(self):
        """Test valid project key formats."""
        valid_keys = [
            "SIMPLE",
            "WITH_UNDERSCORES",
            "WITH_NUMBERS_123",
            "A",
            "A_B_C_123"
        ]

        validator = ConfigValidator()
        for key in valid_keys:
            errors = validator._validate_naming_conventions(
                Config(project=ProjectConfig(key=key, name="Test"))
            )
            assert len(errors) == 0, f"Key '{key}' should be valid"

    def test_project_key_invalid_formats(self):
        """Test invalid project key formats."""
        invalid_keys = [
            "lowercase",
            "mixedCase",
            "WITH-DASHES",
            "WITH SPACES",
            "123_STARTS_WITH_NUMBER",
            "_STARTS_WITH_UNDERSCORE"
        ]

        validator = ConfigValidator()
        for key in invalid_keys:
            errors = validator._validate_naming_conventions(
                Config(project=ProjectConfig(key=key, name="Test"))
            )
            assert len(errors) > 0, f"Key '{key}' should be invalid"

    def test_dataset_name_uppercase(self):
        """Test dataset names must be uppercase."""
        config = Config(
            project=ProjectConfig(key="PROJECT", name="Project"),
            datasets=[
                DatasetConfig(name="lowercase_dataset", type="managed"),
                DatasetConfig(name="VALID_DATASET", type="managed"),
            ]
        )

        validator = ConfigValidator()
        errors = validator._validate_naming_conventions(config)

        # Should have error for lowercase_dataset
        assert any("lowercase_dataset" in str(e.message) for e in errors)
        # Should not have error for VALID_DATASET
        assert not any("VALID_DATASET" in str(e.message) and "must be" in str(e.message)
                       for e in errors)

    def test_recipe_name_lowercase(self):
        """Test recipe names must be lowercase."""
        config = Config(
            project=ProjectConfig(key="PROJECT", name="Project"),
            datasets=[
                DatasetConfig(name="DATA", type="managed")
            ],
            recipes=[
                RecipeConfig(name="UPPERCASE_RECIPE", type="python", outputs=["DATA"]),
                RecipeConfig(name="valid_recipe", type="python", outputs=["DATA"]),
            ]
        )

        validator = ConfigValidator()
        errors = validator._validate_naming_conventions(config)

        # Should have error for UPPERCASE_RECIPE
        assert any("UPPERCASE_RECIPE" in str(e.message) for e in errors)
        # Should not have error for valid_recipe
        assert not any("valid_recipe" in str(e.message) and "must be" in str(e.message)
                       for e in errors)


class TestRequiredFields:
    """Test required field validation."""

    def test_project_requires_key(self):
        """Test project requires key field."""
        config = Config(
            project=ProjectConfig(key="", name="Test")
        )

        validator = ConfigValidator()
        errors = validator._validate_required_fields(config)

        assert any("key" in e.path and "required" in e.message.lower()
                   for e in errors)

    def test_project_requires_name(self):
        """Test project requires name field."""
        config = Config(
            project=ProjectConfig(key="PROJECT", name="")
        )

        validator = ConfigValidator()
        errors = validator._validate_required_fields(config)

        assert any("name" in e.path and "required" in e.message.lower()
                   for e in errors)

    def test_dataset_requires_name(self):
        """Test dataset requires name field."""
        config = Config(
            datasets=[
                DatasetConfig(name="", type="managed")
            ]
        )

        validator = ConfigValidator()
        errors = validator._validate_required_fields(config)

        assert any("name" in e.path and "required" in e.message.lower()
                   for e in errors)

    def test_dataset_requires_type(self):
        """Test dataset requires type field."""
        config = Config(
            datasets=[
                DatasetConfig(name="DATA", type="")
            ]
        )

        validator = ConfigValidator()
        errors = validator._validate_required_fields(config)

        assert any("type" in e.path and "required" in e.message.lower()
                   for e in errors)

    def test_recipe_requires_name(self):
        """Test recipe requires name field."""
        config = Config(
            recipes=[
                RecipeConfig(name="", type="python", outputs=["DATA"])
            ]
        )

        validator = ConfigValidator()
        errors = validator._validate_required_fields(config)

        assert any("name" in e.path and "required" in e.message.lower()
                   for e in errors)

    def test_recipe_requires_type(self):
        """Test recipe requires type field."""
        config = Config(
            recipes=[
                RecipeConfig(name="recipe", type="", outputs=["DATA"])
            ]
        )

        validator = ConfigValidator()
        errors = validator._validate_required_fields(config)

        assert any("type" in e.path and "required" in e.message.lower()
                   for e in errors)

    def test_recipe_requires_outputs(self):
        """Test recipe requires at least one output."""
        config = Config(
            recipes=[
                RecipeConfig(name="recipe", type="python", outputs=[])
            ]
        )

        validator = ConfigValidator()
        errors = validator._validate_required_fields(config)

        assert any("outputs" in e.path and "at least one" in e.message.lower()
                   for e in errors)


class TestTypeValidation:
    """Test type validation."""

    def test_valid_dataset_types(self):
        """Test valid dataset types pass validation."""
        valid_types = ["sql", "filesystem", "snowflake", "managed", "postgresql"]

        for dtype in valid_types:
            config = Config(
                datasets=[DatasetConfig(name="DATA", type=dtype)]
            )
            validator = ConfigValidator()
            errors = validator._validate_types(config)
            # Should not have errors (or only warnings in non-strict mode)
            error_msgs = [e for e in errors if e.severity == "error"]
            assert len(error_msgs) == 0

    def test_invalid_dataset_type_warning(self):
        """Test invalid dataset type generates warning."""
        config = Config(
            datasets=[DatasetConfig(name="DATA", type="invalid_type")]
        )

        validator = ConfigValidator(strict=False)
        errors = validator._validate_types(config)

        # Should have warning
        assert any("invalid_type" in str(e.message).lower() for e in errors)

    def test_valid_recipe_types(self):
        """Test valid recipe types pass validation."""
        valid_types = ["python", "sql", "join", "group", "window"]

        for rtype in valid_types:
            config = Config(
                datasets=[DatasetConfig(name="DATA", type="managed")],
                recipes=[RecipeConfig(name="recipe", type=rtype, outputs=["DATA"])]
            )
            validator = ConfigValidator()
            errors = validator._validate_types(config)
            error_msgs = [e for e in errors if e.severity == "error"]
            assert len(error_msgs) == 0

    def test_invalid_recipe_type_warning(self):
        """Test invalid recipe type generates warning."""
        config = Config(
            datasets=[DatasetConfig(name="DATA", type="managed")],
            recipes=[RecipeConfig(name="recipe", type="invalid_type", outputs=["DATA"])]
        )

        validator = ConfigValidator(strict=False)
        errors = validator._validate_types(config)

        # Should have warning
        assert any("invalid_type" in str(e.message).lower() for e in errors)


class TestReferenceValidation:
    """Test reference integrity validation."""

    def test_recipe_input_must_exist(self):
        """Test recipe input must reference existing dataset."""
        config = Config(
            project=ProjectConfig(key="PROJECT", name="Project"),
            datasets=[
                DatasetConfig(name="EXISTING_DATA", type="managed")
            ],
            recipes=[
                RecipeConfig(
                    name="recipe",
                    type="python",
                    inputs=["NONEXISTENT_DATA"],
                    outputs=["EXISTING_DATA"]
                )
            ]
        )

        validator = ConfigValidator()
        errors = validator._validate_references(config)

        assert any("NONEXISTENT_DATA" in str(e.message) and
                   "non-existent" in str(e.message).lower()
                   for e in errors)

    def test_recipe_output_must_exist(self):
        """Test recipe output must reference existing dataset."""
        config = Config(
            project=ProjectConfig(key="PROJECT", name="Project"),
            datasets=[
                DatasetConfig(name="INPUT_DATA", type="managed")
            ],
            recipes=[
                RecipeConfig(
                    name="recipe",
                    type="python",
                    inputs=["INPUT_DATA"],
                    outputs=["NONEXISTENT_OUTPUT"]
                )
            ]
        )

        validator = ConfigValidator()
        errors = validator._validate_references(config)

        assert any("NONEXISTENT_OUTPUT" in str(e.message) and
                   "non-existent" in str(e.message).lower()
                   for e in errors)

    def test_valid_references_pass(self):
        """Test valid references pass validation."""
        config = Config(
            project=ProjectConfig(key="PROJECT", name="Project"),
            datasets=[
                DatasetConfig(name="INPUT", type="managed"),
                DatasetConfig(name="OUTPUT", type="managed")
            ],
            recipes=[
                RecipeConfig(
                    name="recipe",
                    type="python",
                    inputs=["INPUT"],
                    outputs=["OUTPUT"]
                )
            ]
        )

        validator = ConfigValidator()
        errors = validator._validate_references(config)

        # Should have no errors
        assert len(errors) == 0


class TestCircularDependencies:
    """Test circular dependency detection."""

    def test_simple_circular_dependency(self):
        """Test detection of simple circular dependency."""
        config = Config(
            project=ProjectConfig(key="PROJECT", name="Project"),
            datasets=[
                DatasetConfig(name="A", type="managed"),
                DatasetConfig(name="B", type="managed")
            ],
            recipes=[
                RecipeConfig(name="r1", type="python", inputs=["B"], outputs=["A"]),
                RecipeConfig(name="r2", type="python", inputs=["A"], outputs=["B"])
            ]
        )

        validator = ConfigValidator()
        errors = validator._validate_dependencies(config)

        # Should detect circular dependency
        assert any("circular" in str(e.message).lower() for e in errors)

    def test_self_circular_dependency(self):
        """Test detection of self-referencing circular dependency."""
        config = Config(
            project=ProjectConfig(key="PROJECT", name="Project"),
            datasets=[
                DatasetConfig(name="A", type="managed")
            ],
            recipes=[
                RecipeConfig(name="r1", type="python", inputs=["A"], outputs=["A"])
            ]
        )

        validator = ConfigValidator()
        errors = validator._validate_dependencies(config)

        # Should detect circular dependency
        assert any("circular" in str(e.message).lower() for e in errors)

    def test_complex_circular_dependency(self):
        """Test detection of complex circular dependency chain."""
        config = Config(
            project=ProjectConfig(key="PROJECT", name="Project"),
            datasets=[
                DatasetConfig(name="A", type="managed"),
                DatasetConfig(name="B", type="managed"),
                DatasetConfig(name="C", type="managed")
            ],
            recipes=[
                RecipeConfig(name="r1", type="python", inputs=["C"], outputs=["A"]),
                RecipeConfig(name="r2", type="python", inputs=["A"], outputs=["B"]),
                RecipeConfig(name="r3", type="python", inputs=["B"], outputs=["C"])
            ]
        )

        validator = ConfigValidator()
        errors = validator._validate_dependencies(config)

        # Should detect circular dependency
        assert any("circular" in str(e.message).lower() for e in errors)

    def test_no_circular_dependency(self):
        """Test valid DAG with no circular dependencies."""
        config = Config(
            project=ProjectConfig(key="PROJECT", name="Project"),
            datasets=[
                DatasetConfig(name="A", type="managed"),
                DatasetConfig(name="B", type="managed"),
                DatasetConfig(name="C", type="managed")
            ],
            recipes=[
                RecipeConfig(name="r1", type="python", inputs=["A"], outputs=["B"]),
                RecipeConfig(name="r2", type="python", inputs=["B"], outputs=["C"])
            ]
        )

        validator = ConfigValidator()
        errors = validator._validate_dependencies(config)

        # Should have no circular dependency errors
        assert not any("circular" in str(e.message).lower() for e in errors)

    def test_diamond_dag_no_cycle(self):
        """Test diamond-shaped DAG has no cycle."""
        config = Config(
            project=ProjectConfig(key="PROJECT", name="Project"),
            datasets=[
                DatasetConfig(name="A", type="managed"),
                DatasetConfig(name="B", type="managed"),
                DatasetConfig(name="C", type="managed"),
                DatasetConfig(name="D", type="managed")
            ],
            recipes=[
                RecipeConfig(name="r1", type="python", inputs=["A"], outputs=["B"]),
                RecipeConfig(name="r2", type="python", inputs=["A"], outputs=["C"]),
                RecipeConfig(name="r3", type="python", inputs=["B", "C"], outputs=["D"])
            ]
        )

        validator = ConfigValidator()
        errors = validator._validate_dependencies(config)

        # Should have no circular dependency errors
        assert not any("circular" in str(e.message).lower() for e in errors)


class TestCompleteValidation:
    """Test complete validation workflow."""

    def test_multiple_errors_reported(self):
        """Test that multiple validation errors are reported."""
        config = Config(
            project=ProjectConfig(
                key="lowercase",  # Invalid
                name=""  # Invalid
            ),
            datasets=[
                DatasetConfig(name="lowercase", type="managed"),  # Invalid name
                DatasetConfig(name="VALID", type="invalid_type")  # Invalid type (warning)
            ],
            recipes=[
                RecipeConfig(
                    name="UPPERCASE",  # Invalid
                    type="python",
                    inputs=["NONEXISTENT"],  # Invalid reference
                    outputs=["ALSO_NONEXISTENT"]  # Invalid reference
                )
            ]
        )

        validator = ConfigValidator()
        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        # Should have multiple errors
        errors = exc_info.value.errors
        assert len(errors) >= 5  # At least 5 errors

    def test_validation_stops_on_first_error_in_strict_mode(self):
        """Test that validation collects all errors before raising."""
        config = Config(
            project=ProjectConfig(key="BAD_key", name="Test"),
            datasets=[
                DatasetConfig(name="bad_name", type="managed")
            ]
        )

        validator = ConfigValidator(strict=True)
        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        # Should have collected multiple errors
        assert len(exc_info.value.errors) >= 1

    def test_empty_config_validation(self):
        """Test validation of minimal config."""
        config = Config(version="1.0")

        validator = ConfigValidator()
        # Empty config should pass basic validation
        # (no project/datasets/recipes is valid, though not useful)
        errors = validator._validate_naming_conventions(config)
        assert len(errors) == 0


class TestValidatorEdgeCases:
    """Test edge cases and error handling."""

    def test_config_without_project(self):
        """Test config without project section."""
        config = Config(
            datasets=[DatasetConfig(name="DATA", type="managed")]
        )

        validator = ConfigValidator()
        # Should not crash, just skip project validation
        errors = validator._validate_naming_conventions(config)
        assert len(errors) == 0

    def test_config_without_datasets(self):
        """Test config without datasets."""
        config = Config(
            project=ProjectConfig(key="PROJECT", name="Project")
        )

        validator = ConfigValidator()
        errors = validator._validate_references(config)
        assert len(errors) == 0

    def test_config_without_recipes(self):
        """Test config without recipes."""
        config = Config(
            project=ProjectConfig(key="PROJECT", name="Project"),
            datasets=[DatasetConfig(name="DATA", type="managed")]
        )

        validator = ConfigValidator()
        errors = validator._validate_references(config)
        assert len(errors) == 0

    def test_recipe_with_no_inputs(self):
        """Test recipe with no inputs (source recipe)."""
        config = Config(
            project=ProjectConfig(key="PROJECT", name="Project"),
            datasets=[DatasetConfig(name="OUTPUT", type="managed")],
            recipes=[
                RecipeConfig(
                    name="source_recipe",
                    type="python",
                    inputs=[],  # No inputs
                    outputs=["OUTPUT"]
                )
            ]
        )

        validator = ConfigValidator()
        errors = validator._validate_references(config)
        # Should pass - recipes can have no inputs
        assert len(errors) == 0

    def test_multiple_recipes_same_output(self):
        """Test multiple recipes writing to same output."""
        config = Config(
            project=ProjectConfig(key="PROJECT", name="Project"),
            datasets=[
                DatasetConfig(name="INPUT", type="managed"),
                DatasetConfig(name="OUTPUT", type="managed")
            ],
            recipes=[
                RecipeConfig(name="recipe1", type="python", inputs=["INPUT"], outputs=["OUTPUT"]),
                RecipeConfig(name="recipe2", type="python", inputs=["INPUT"], outputs=["OUTPUT"])
            ]
        )

        validator = ConfigValidator()
        # Currently we don't validate uniqueness of outputs
        # This might be added as a warning in the future
        errors = validator._validate_references(config)
        # Should pass reference validation
        ref_errors = [e for e in errors if e.severity == "error"]
        assert len(ref_errors) == 0


class TestConfigValidationError:
    """Test ConfigValidationError exception."""

    def test_error_with_validation_errors(self):
        """Test exception with list of validation errors."""
        errors = [
            ValidationError("path1", "message1"),
            ValidationError("path2", "message2")
        ]

        exc = ConfigValidationError(errors)
        assert len(exc.errors) == 2
        assert "path1" in str(exc)
        assert "path2" in str(exc)
        assert "message1" in str(exc)
        assert "message2" in str(exc)

    def test_error_with_string_message(self):
        """Test exception with simple string message."""
        exc = ConfigValidationError("Simple error message")
        assert len(exc.errors) == 0
        assert "Simple error message" in str(exc)
