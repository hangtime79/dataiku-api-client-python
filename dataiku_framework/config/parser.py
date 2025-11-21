"""
Configuration file parser

Handles loading YAML/JSON configs and resolving external file references.
"""

import json
import yaml
from pathlib import Path
from typing import Union, Dict, Any

from dataiku_framework.config.schema import FrameworkConfig


class ConfigParser:
    """Parse and write configuration files"""

    @staticmethod
    def parse_yaml(path: Union[str, Path]) -> FrameworkConfig:
        """
        Load configuration from YAML file.

        Args:
            path: Path to YAML file

        Returns:
            Validated FrameworkConfig

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is invalid
            ValidationError: If config doesn't match schema
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        # Resolve external file references
        data = ConfigParser._resolve_file_references(data, path.parent)

        return FrameworkConfig.from_dict(data)

    @staticmethod
    def parse_json(path: Union[str, Path]) -> FrameworkConfig:
        """
        Load configuration from JSON file.

        Args:
            path: Path to JSON file

        Returns:
            Validated FrameworkConfig

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
            ValidationError: If config doesn't match schema
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r") as f:
            data = json.load(f)

        # Resolve external file references
        data = ConfigParser._resolve_file_references(data, path.parent)

        return FrameworkConfig.from_dict(data)

    @staticmethod
    def write_yaml(config: FrameworkConfig, path: Union[str, Path]) -> None:
        """
        Write configuration to YAML file.

        Args:
            config: FrameworkConfig to write
            path: Destination file path
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = config.to_dict()

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)

    @staticmethod
    def write_json(config: FrameworkConfig, path: Union[str, Path]) -> None:
        """
        Write configuration to JSON file.

        Args:
            config: FrameworkConfig to write
            path: Destination file path
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = config.to_dict()

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def _resolve_file_references(
        data: Dict[str, Any], base_path: Path
    ) -> Dict[str, Any]:
        """
        Resolve external file references in config.

        Looks for 'code_file' fields in recipes and loads the content.

        Args:
            data: Config dictionary
            base_path: Base directory for resolving relative paths

        Returns:
            Config dictionary with file contents loaded
        """
        if "recipes" not in data:
            return data

        for recipe in data["recipes"]:
            if "code_file" in recipe and recipe["code_file"]:
                code_path = base_path / recipe["code_file"]

                if not code_path.exists():
                    raise FileNotFoundError(
                        f"Recipe '{recipe.get('name', 'unknown')}' references "
                        f"code file that doesn't exist: {code_path}"
                    )

                # Read file content
                with open(code_path, "r") as f:
                    recipe["code"] = f.read()

                # Remove code_file reference (we've loaded it into code)
                # Keep it for reference
                # del recipe["code_file"]

        return data

    @staticmethod
    def validate_file(path: Union[str, Path]) -> bool:
        """
        Validate a config file without loading it fully.

        Args:
            path: Path to config file

        Returns:
            True if valid, raises exception otherwise

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError or json.JSONDecodeError: If parsing fails
            ValidationError: If config doesn't match schema
        """
        path = Path(path)

        # Determine format from extension
        if path.suffix in [".yaml", ".yml"]:
            ConfigParser.parse_yaml(path)
        elif path.suffix == ".json":
            ConfigParser.parse_json(path)
        else:
            raise ValueError(
                f"Unknown config file format: {path.suffix}. "
                f"Supported: .yaml, .yml, .json"
            )

        return True


class ConfigValidator:
    """Additional validation beyond Pydantic schema"""

    @staticmethod
    def validate_connections_exist(
        config: FrameworkConfig, available_connections: list[str]
    ) -> list[str]:
        """
        Validate that all referenced connections exist.

        Args:
            config: FrameworkConfig to validate
            available_connections: List of connection names available in Dataiku

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        referenced_connections = set()

        # Collect connections from datasets
        for dataset in config.datasets:
            referenced_connections.add(dataset.connection)

        # Collect connections from SQL scenario steps
        for scenario in config.scenarios:
            for step in scenario.steps:
                if step.connection:
                    referenced_connections.add(step.connection)

        # Collect connections from SQL triggers
        for scenario in config.scenarios:
            for trigger in scenario.triggers:
                if trigger.connection:
                    referenced_connections.add(trigger.connection)

        # Check all exist
        for conn in referenced_connections:
            if conn not in available_connections:
                errors.append(
                    f"Connection '{conn}' not found. "
                    f"Available: {', '.join(sorted(available_connections))}"
                )

        return errors

    @staticmethod
    def validate_circular_dependencies(config: FrameworkConfig) -> list[str]:
        """
        Check for circular dependencies in recipes.

        Args:
            config: FrameworkConfig to validate

        Returns:
            List of validation errors (empty if valid)
        """
        from dataiku_framework.engine.dependency import DependencyResolver

        try:
            DependencyResolver.resolve(config.recipes)
            return []
        except ValueError as e:
            return [str(e)]

    @staticmethod
    def validate_all(
        config: FrameworkConfig, available_connections: list[str] = None
    ) -> list[str]:
        """
        Run all validations.

        Args:
            config: FrameworkConfig to validate
            available_connections: Optional list of available connections

        Returns:
            List of all validation errors (empty if valid)
        """
        errors = []

        # Schema validation (already done by Pydantic)
        # Dependency validation
        errors.extend(config.validate_dependencies())

        # Circular dependency validation
        errors.extend(ConfigValidator.validate_circular_dependencies(config))

        # Connection validation (if connections provided)
        if available_connections is not None:
            errors.extend(
                ConfigValidator.validate_connections_exist(config, available_connections)
            )

        return errors
