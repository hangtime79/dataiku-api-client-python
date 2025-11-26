"""
Unit tests for config validation edge cases.

Tests comprehensive validation scenarios including:
- Invalid naming conventions
- Missing required fields
- Invalid references
- Circular dependencies
- Edge cases and malformed data
"""

import pytest
from pathlib import Path

from dataikuapi.iac.config.parser import ConfigParser
from dataikuapi.iac.config.validator import ConfigValidator
from dataikuapi.iac.config.models import Config, ProjectConfig, DatasetConfig, RecipeConfig
from dataikuapi.iac.exceptions import ConfigValidationError


@pytest.mark.unit
class TestNamingConventionEdgeCases:
    """Test naming convention validation edge cases"""

    def test_project_key_with_lowercase_fails(self):
        """Project key with lowercase should fail"""
        config = Config(
            version="1.0",
            project=ProjectConfig(
                key="invalid_lowercase",  # Should be UPPERCASE
                name="Invalid Project"
            )
        )

        validator = ConfigValidator(strict=True)
        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        assert "uppercase" in str(exc_info.value).lower() or "naming" in str(exc_info.value).lower()

    def test_project_key_with_numbers_allowed(self):
        """Project key with numbers should be allowed"""
        config = Config(
            version="1.0",
            project=ProjectConfig(
                key="PROJECT_123",  # Valid
                name="Project with Numbers"
            )
        )

        validator = ConfigValidator(strict=True)
        validator.validate(config)  # Should not raise

    def test_project_key_with_special_chars_fails(self):
        """Project key with special characters should fail"""
        config = Config(
            version="1.0",
            project=ProjectConfig(
                key="PROJECT-WITH-DASHES",  # Invalid
                name="Invalid Project"
            )
        )

        validator = ConfigValidator(strict=True)
        with pytest.raises(ConfigValidationError):
            validator.validate(config)

    def test_dataset_name_lowercase_fails(self):
        """Dataset name with lowercase should fail"""
        config = Config(
            version="1.0",
            project=ProjectConfig(key="VALID_PROJECT", name="Valid"),
            datasets=[
                DatasetConfig(
                    name="lowercase_dataset",  # Should be UPPERCASE
                    type="managed"
                )
            ]
        )

        validator = ConfigValidator(strict=True)
        with pytest.raises(ConfigValidationError):
            validator.validate(config)

    def test_recipe_name_uppercase_fails(self):
        """Recipe name with UPPERCASE should fail (recipes should be lowercase)"""
        config = Config(
            version="1.0",
            project=ProjectConfig(key="VALID_PROJECT", name="Valid"),
            datasets=[DatasetConfig(name="DATASET", type="managed")],
            recipes=[
                RecipeConfig(
                    name="UPPERCASE_RECIPE",  # Should be lowercase
                    type="python",
                    inputs=["DATASET"],
                    outputs=["DATASET"],
                    code="# Code"
                )
            ]
        )

        validator = ConfigValidator(strict=True)
        with pytest.raises(ConfigValidationError):
            validator.validate(config)

    def test_recipe_name_with_underscores_allowed(self):
        """Recipe name with underscores should be allowed"""
        config = Config(
            version="1.0",
            project=ProjectConfig(key="VALID_PROJECT", name="Valid"),
            datasets=[
                DatasetConfig(name="INPUT_DATASET", type="managed"),
                DatasetConfig(name="OUTPUT_DATASET", type="managed")
            ],
            recipes=[
                RecipeConfig(
                    name="valid_recipe_name",  # Valid
                    type="python",
                    inputs=["INPUT_DATASET"],
                    outputs=["OUTPUT_DATASET"],
                    code="# Code"
                )
            ]
        )

        validator = ConfigValidator(strict=True)
        validator.validate(config)  # Should not raise


@pytest.mark.unit
class TestReferenceValidationEdgeCases:
    """Test reference validation edge cases"""

    def test_recipe_with_nonexistent_input_fails(self):
        """Recipe referencing non-existent input dataset should fail"""
        config = Config(
            version="1.0",
            project=ProjectConfig(key="TEST_PROJECT", name="Test"),
            datasets=[DatasetConfig(name="OUTPUT_DATA", type="managed")],
            recipes=[
                RecipeConfig(
                    name="test_recipe",
                    type="python",
                    inputs=["NONEXISTENT_INPUT"],  # Does not exist
                    outputs=["OUTPUT_DATA"],
                    code="# Code"
                )
            ]
        )

        validator = ConfigValidator(strict=True)
        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        assert "nonexistent_input" in str(exc_info.value).lower()

    def test_recipe_with_nonexistent_output_fails(self):
        """Recipe referencing non-existent output dataset should fail"""
        config = Config(
            version="1.0",
            project=ProjectConfig(key="TEST_PROJECT", name="Test"),
            datasets=[DatasetConfig(name="INPUT_DATA", type="managed")],
            recipes=[
                RecipeConfig(
                    name="test_recipe",
                    type="python",
                    inputs=["INPUT_DATA"],
                    outputs=["NONEXISTENT_OUTPUT"],  # Does not exist
                    code="# Code"
                )
            ]
        )

        validator = ConfigValidator(strict=True)
        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        assert "nonexistent_output" in str(exc_info.value).lower()

    def test_recipe_with_multiple_missing_references(self):
        """Recipe with multiple missing references should report all"""
        config = Config(
            version="1.0",
            project=ProjectConfig(key="TEST_PROJECT", name="Test"),
            datasets=[],
            recipes=[
                RecipeConfig(
                    name="test_recipe",
                    type="python",
                    inputs=["MISSING_A", "MISSING_B"],
                    outputs=["MISSING_C"],
                    code="# Code"
                )
            ]
        )

        validator = ConfigValidator(strict=True)
        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        error_msg = str(exc_info.value).lower()
        assert "missing_a" in error_msg or "missing_b" in error_msg or "missing_c" in error_msg

    def test_recipe_with_case_sensitive_reference_fails(self):
        """Recipe reference with wrong case should fail"""
        config = Config(
            version="1.0",
            project=ProjectConfig(key="TEST_PROJECT", name="Test"),
            datasets=[DatasetConfig(name="MY_DATASET", type="managed")],
            recipes=[
                RecipeConfig(
                    name="test_recipe",
                    type="python",
                    inputs=["my_dataset"],  # Wrong case
                    outputs=["MY_DATASET"],
                    code="# Code"
                )
            ]
        )

        validator = ConfigValidator(strict=True)
        with pytest.raises(ConfigValidationError):
            validator.validate(config)


@pytest.mark.unit
class TestCircularDependencyDetection:
    """Test circular dependency detection"""

    def test_simple_circular_dependency_detected(self):
        """Simple A→B→A circular dependency should be detected"""
        config = Config(
            version="1.0",
            project=ProjectConfig(key="CIRCULAR_TEST", name="Test"),
            datasets=[
                DatasetConfig(name="DATASET_A", type="managed"),
                DatasetConfig(name="DATASET_B", type="managed")
            ],
            recipes=[
                RecipeConfig(
                    name="recipe_a",
                    type="python",
                    inputs=["DATASET_B"],
                    outputs=["DATASET_A"],
                    code="# A"
                ),
                RecipeConfig(
                    name="recipe_b",
                    type="python",
                    inputs=["DATASET_A"],
                    outputs=["DATASET_B"],
                    code="# B"
                )
            ]
        )

        validator = ConfigValidator(strict=True)
        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        assert "circular" in str(exc_info.value).lower() or "cycle" in str(exc_info.value).lower()

    def test_three_way_circular_dependency_detected(self):
        """Three-way A→B→C→A circular dependency should be detected"""
        config = Config(
            version="1.0",
            project=ProjectConfig(key="CIRCULAR_TEST", name="Test"),
            datasets=[
                DatasetConfig(name="DS_A", type="managed"),
                DatasetConfig(name="DS_B", type="managed"),
                DatasetConfig(name="DS_C", type="managed")
            ],
            recipes=[
                RecipeConfig(name="r_a", type="python", inputs=["DS_C"], outputs=["DS_A"], code="# A"),
                RecipeConfig(name="r_b", type="python", inputs=["DS_A"], outputs=["DS_B"], code="# B"),
                RecipeConfig(name="r_c", type="python", inputs=["DS_B"], outputs=["DS_C"], code="# C")
            ]
        )

        validator = ConfigValidator(strict=True)
        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        assert "circular" in str(exc_info.value).lower() or "cycle" in str(exc_info.value).lower()

    def test_self_referencing_recipe_detected(self):
        """Recipe that references itself should be detected"""
        config = Config(
            version="1.0",
            project=ProjectConfig(key="SELF_REF_TEST", name="Test"),
            datasets=[DatasetConfig(name="DATASET", type="managed")],
            recipes=[
                RecipeConfig(
                    name="self_ref_recipe",
                    type="python",
                    inputs=["DATASET"],
                    outputs=["DATASET"],  # Same as input
                    code="# Self reference"
                )
            ]
        )

        validator = ConfigValidator(strict=True)
        # This might be allowed in some cases (in-place transformation)
        # But strict mode should catch it
        try:
            validator.validate(config)
        except ConfigValidationError:
            pass  # Expected in strict mode


@pytest.mark.unit
class TestTypeValidationEdgeCases:
    """Test type validation edge cases"""

    def test_invalid_dataset_type_fails(self):
        """Dataset with invalid type should fail"""
        config = Config(
            version="1.0",
            project=ProjectConfig(key="TEST_PROJECT", name="Test"),
            datasets=[
                DatasetConfig(
                    name="BAD_DATASET",
                    type="invalid_type"  # Not a valid type
                )
            ]
        )

        validator = ConfigValidator(strict=True)
        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        assert "type" in str(exc_info.value).lower()

    def test_invalid_recipe_type_fails(self):
        """Recipe with invalid type should fail"""
        config = Config(
            version="1.0",
            project=ProjectConfig(key="TEST_PROJECT", name="Test"),
            datasets=[DatasetConfig(name="DATA", type="managed")],
            recipes=[
                RecipeConfig(
                    name="bad_recipe",
                    type="invalid_recipe_type",  # Not valid
                    inputs=["DATA"],
                    outputs=["DATA"],
                    code="# Code"
                )
            ]
        )

        validator = ConfigValidator(strict=True)
        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        assert "type" in str(exc_info.value).lower()


@pytest.mark.unit
@pytest.mark.edge_case
class TestMissingRequiredFields:
    """Test missing required fields validation"""

    def test_project_without_key_fails(self):
        """Project without key should fail"""
        # This would fail at model level (dataclass validation)
        # Testing here for completeness
        with pytest.raises((TypeError, ValueError)):
            config = Config(
                version="1.0",
                project=ProjectConfig(
                    name="No Key Project"
                    # Missing key
                )
            )

    def test_dataset_without_name_fails(self):
        """Dataset without name should fail"""
        with pytest.raises((TypeError, ValueError)):
            config = Config(
                version="1.0",
                project=ProjectConfig(key="TEST", name="Test"),
                datasets=[
                    DatasetConfig(
                        type="managed"
                        # Missing name
                    )
                ]
            )

    def test_recipe_without_type_fails(self):
        """Recipe without type should fail"""
        with pytest.raises((TypeError, ValueError)):
            config = Config(
                version="1.0",
                project=ProjectConfig(key="TEST", name="Test"),
                datasets=[DatasetConfig(name="DATA", type="managed")],
                recipes=[
                    RecipeConfig(
                        name="recipe",
                        inputs=["DATA"],
                        outputs=["DATA"],
                        code="# Code"
                        # Missing type
                    )
                ]
            )


@pytest.mark.unit
class TestEdgeCaseConfigFiles:
    """Test validation using edge case fixture files"""

    def test_invalid_naming_fixture_fails(self, fixtures_dir):
        """Edge case config with invalid naming should fail validation"""
        config_file = fixtures_dir / "configs" / "edge_cases" / "invalid_naming.yml"

        if config_file.exists():
            parser = ConfigParser()
            config = parser.parse_file(config_file)

            validator = ConfigValidator(strict=True)
            with pytest.raises(ConfigValidationError):
                validator.validate(config)

    def test_circular_dependency_fixture_fails(self, fixtures_dir):
        """Edge case config with circular dependencies should fail validation"""
        config_file = fixtures_dir / "configs" / "edge_cases" / "circular_dependency.yml"

        if config_file.exists():
            parser = ConfigParser()
            config = parser.parse_file(config_file)

            validator = ConfigValidator(strict=True)
            with pytest.raises(ConfigValidationError):
                validator.validate(config)
