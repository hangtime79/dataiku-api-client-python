"""
Configuration validation engine.

Validates configuration objects against business rules and schema definitions.
"""

import re
from typing import List, Dict, Set
from pathlib import Path
from .models import Config
from ..exceptions import ConfigValidationError

try:
    import jsonschema

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


class ValidationError:
    """
    Single validation error.

    Represents a validation issue with its location and description.
    """

    def __init__(self, path: str, message: str, severity: str = "error"):
        """
        Initialize validation error.

        Args:
            path: Path to the invalid field (e.g., "datasets[0].name")
            message: Human-readable error message
            severity: Error severity ("error", "warning", "info")
        """
        self.path = path
        self.message = message
        self.severity = severity

    def __str__(self) -> str:
        """String representation of the error."""
        return f"{self.path}: {self.message}"

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"ValidationError(path={self.path!r}, message={self.message!r}, severity={self.severity!r})"

    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, ValidationError):
            return False
        return (
            self.path == other.path
            and self.message == other.message
            and self.severity == other.severity
        )


class ConfigValidator:
    """
    Validate configuration objects against rules.

    Validates:
    - Required fields present
    - Valid resource names (UPPERCASE for projects/datasets, lowercase for recipes)
    - Valid dataset types and recipe types
    - Recipe inputs/outputs reference existing datasets
    - No circular dependencies
    """

    # Valid dataset types
    VALID_DATASET_TYPES = {
        "sql",
        "filesystem",
        "snowflake",
        "managed",
        "postgresql",
        "mysql",
        "s3",
        "hdfs",
        "azure_blob",
    }

    # Valid recipe types
    VALID_RECIPE_TYPES = {
        "python",
        "sql",
        "join",
        "group",
        "window",
        "sort",
        "topn",
        "distinct",
        "grouping",
        "pivot",
        "split",
    }

    # Naming patterns
    UPPERCASE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
    LOWERCASE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

    def __init__(self, strict: bool = True):
        """
        Initialize validator.

        Args:
            strict: If True, treat warnings as errors
        """
        self.strict = strict
        self._schema = None

    def validate(self, config: Config) -> List[ValidationError]:
        """
        Validate complete configuration.

        Args:
            config: Config object to validate

        Returns:
            List of validation errors (empty if valid)

        Raises:
            ConfigValidationError: If errors found
        """
        errors = []

        # Schema validation
        errors.extend(self._validate_schema(config))

        # Business rules
        errors.extend(self._validate_naming_conventions(config))
        errors.extend(self._validate_required_fields(config))
        errors.extend(self._validate_types(config))
        errors.extend(self._validate_references(config))
        errors.extend(self._validate_dependencies(config))

        # Filter by severity if not strict
        if not self.strict:
            errors = [e for e in errors if e.severity == "error"]

        # Raise if errors found
        if errors:
            raise ConfigValidationError(errors)

        return errors

    def _validate_schema(self, config: Config) -> List[ValidationError]:
        """
        Validate against JSON Schema.

        Args:
            config: Configuration to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Skip if jsonschema not available
        if not HAS_JSONSCHEMA:
            return errors

        # Load schema if not loaded
        if self._schema is None:
            schema_path = (
                Path(__file__).parent.parent / "schemas" / "config_v1.schema.json"
            )
            if schema_path.exists():
                import json

                with open(schema_path) as f:
                    self._schema = json.load(f)
            else:
                # Schema not available yet
                return errors

        # Convert config to dict for validation
        # This is a simple conversion - Package 1 will provide better serialization
        config_dict = {
            "version": config.version,
            "metadata": config.metadata,
        }

        if config.project:
            config_dict["project"] = {
                "key": config.project.key,
                "name": config.project.name,
                "description": config.project.description,
                "settings": config.project.settings,
            }

        config_dict["datasets"] = [
            {
                "name": ds.name,
                "type": ds.type,
                "connection": ds.connection,
                "params": ds.params,
                "schema": ds.schema,
                "format_type": ds.format_type,
            }
            for ds in config.datasets
        ]

        config_dict["recipes"] = [
            {
                "name": r.name,
                "type": r.type,
                "inputs": r.inputs,
                "outputs": r.outputs,
                "params": r.params,
                "code": r.code,
            }
            for r in config.recipes
        ]

        # Validate
        try:
            jsonschema.validate(config_dict, self._schema)
        except jsonschema.ValidationError as e:
            errors.append(
                ValidationError(
                    path=".".join(str(p) for p in e.path) if e.path else "root",
                    message=e.message,
                    severity="error",
                )
            )
        except jsonschema.SchemaError as e:
            # Schema itself is invalid
            errors.append(
                ValidationError(
                    path="schema",
                    message=f"Invalid schema: {e.message}",
                    severity="error",
                )
            )

        return errors

    def _validate_naming_conventions(self, config: Config) -> List[ValidationError]:
        """
        Validate naming conventions.

        Rules:
        - Project keys: UPPERCASE_WITH_UNDERSCORES
        - Dataset names: UPPERCASE_WITH_UNDERSCORES
        - Recipe names: lowercase_with_underscores

        Args:
            config: Configuration to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Validate project key
        if config.project:
            if not self.UPPERCASE_PATTERN.match(config.project.key):
                errors.append(
                    ValidationError(
                        path="project.key",
                        message=f"Project key '{config.project.key}' must be UPPERCASE_WITH_UNDERSCORES",
                        severity="error",
                    )
                )

        # Validate dataset names
        for i, dataset in enumerate(config.datasets):
            if not self.UPPERCASE_PATTERN.match(dataset.name):
                errors.append(
                    ValidationError(
                        path=f"datasets[{i}].name",
                        message=f"Dataset name '{dataset.name}' must be UPPERCASE_WITH_UNDERSCORES",
                        severity="error",
                    )
                )

        # Validate recipe names
        for i, recipe in enumerate(config.recipes):
            if not self.LOWERCASE_PATTERN.match(recipe.name):
                errors.append(
                    ValidationError(
                        path=f"recipes[{i}].name",
                        message=f"Recipe name '{recipe.name}' must be lowercase_with_underscores",
                        severity="error",
                    )
                )

        return errors

    def _validate_required_fields(self, config: Config) -> List[ValidationError]:
        """
        Validate required fields are present.

        Rules:
        - Project: key, name
        - Dataset: name, type
        - Recipe: name, type, outputs (at least one)

        Args:
            config: Configuration to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Validate project required fields
        if config.project:
            if not config.project.key:
                errors.append(
                    ValidationError(
                        path="project.key",
                        message="Project key is required",
                        severity="error",
                    )
                )
            if not config.project.name:
                errors.append(
                    ValidationError(
                        path="project.name",
                        message="Project name is required",
                        severity="error",
                    )
                )

        # Validate dataset required fields
        for i, dataset in enumerate(config.datasets):
            if not dataset.name:
                errors.append(
                    ValidationError(
                        path=f"datasets[{i}].name",
                        message="Dataset name is required",
                        severity="error",
                    )
                )
            if not dataset.type:
                errors.append(
                    ValidationError(
                        path=f"datasets[{i}].type",
                        message="Dataset type is required",
                        severity="error",
                    )
                )

        # Validate recipe required fields
        for i, recipe in enumerate(config.recipes):
            if not recipe.name:
                errors.append(
                    ValidationError(
                        path=f"recipes[{i}].name",
                        message="Recipe name is required",
                        severity="error",
                    )
                )
            if not recipe.type:
                errors.append(
                    ValidationError(
                        path=f"recipes[{i}].type",
                        message="Recipe type is required",
                        severity="error",
                    )
                )
            if not recipe.outputs:
                errors.append(
                    ValidationError(
                        path=f"recipes[{i}].outputs",
                        message="Recipe must have at least one output",
                        severity="error",
                    )
                )

        return errors

    def _validate_types(self, config: Config) -> List[ValidationError]:
        """
        Validate resource types are valid.

        Args:
            config: Configuration to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Validate dataset types
        for i, dataset in enumerate(config.datasets):
            if dataset.type and dataset.type not in self.VALID_DATASET_TYPES:
                errors.append(
                    ValidationError(
                        path=f"datasets[{i}].type",
                        message=f"Invalid dataset type '{dataset.type}'. Valid types: {', '.join(sorted(self.VALID_DATASET_TYPES))}",
                        severity="warning",
                    )
                )

        # Validate recipe types
        for i, recipe in enumerate(config.recipes):
            if recipe.type and recipe.type not in self.VALID_RECIPE_TYPES:
                errors.append(
                    ValidationError(
                        path=f"recipes[{i}].type",
                        message=f"Invalid recipe type '{recipe.type}'. Valid types: {', '.join(sorted(self.VALID_RECIPE_TYPES))}",
                        severity="warning",
                    )
                )

        return errors

    def _validate_references(self, config: Config) -> List[ValidationError]:
        """
        Validate references.

        Rules:
        - Recipe inputs must reference existing datasets
        - Recipe outputs must be defined datasets

        Args:
            config: Configuration to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Build set of dataset names
        dataset_names = {ds.name for ds in config.datasets}

        # Validate recipe inputs and outputs
        for i, recipe in enumerate(config.recipes):
            # Validate inputs
            for input_name in recipe.inputs:
                if input_name not in dataset_names:
                    errors.append(
                        ValidationError(
                            path=f"recipes[{i}].inputs",
                            message=f"Recipe input '{input_name}' references non-existent dataset",
                            severity="error",
                        )
                    )

            # Validate outputs
            for output_name in recipe.outputs:
                if output_name not in dataset_names:
                    errors.append(
                        ValidationError(
                            path=f"recipes[{i}].outputs",
                            message=f"Recipe output '{output_name}' references non-existent dataset",
                            severity="error",
                        )
                    )

        return errors

    def _validate_dependencies(self, config: Config) -> List[ValidationError]:
        """
        Validate no circular dependencies.

        Builds dependency graph and detects cycles.

        Args:
            config: Configuration to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Build dependency graph: dataset -> list of datasets it depends on
        dependencies: Dict[str, Set[str]] = {}

        # Initialize all datasets
        for dataset in config.datasets:
            dependencies[dataset.name] = set()

        # Add dependencies from recipes
        for recipe in config.recipes:
            # Each output depends on all inputs
            for output in recipe.outputs:
                if output in dependencies:
                    dependencies[output].update(recipe.inputs)

        # Detect cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node: str, path: List[str]) -> bool:
            """Check if node has cycle using DFS."""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            # Check all dependencies
            for dep in dependencies.get(node, []):
                if dep not in visited:
                    if has_cycle(dep, path):
                        return True
                elif dep in rec_stack:
                    # Found cycle
                    cycle_start = path.index(dep)
                    cycle = path[cycle_start:] + [dep]
                    errors.append(
                        ValidationError(
                            path="recipes",
                            message=f"Circular dependency detected: {' -> '.join(cycle)}",
                            severity="error",
                        )
                    )
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        # Check each dataset
        for dataset_name in dependencies:
            if dataset_name not in visited:
                has_cycle(dataset_name, [])

        return errors
