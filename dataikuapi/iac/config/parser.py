"""
Configuration parser for Dataiku IaC.

Parses YAML configuration files and directories into Config objects.
"""

import yaml
from pathlib import Path
from typing import Union, Dict, Any, List
from .models import Config
from ..exceptions import ConfigParseError


class ConfigParser:
    """
    Parse YAML configuration files into Config objects.

    Supports:
    - Single file configs
    - Multi-file configs (project/, datasets/, recipes/)
    - Variable substitution (handled separately in validator)

    Example:
        >>> parser = ConfigParser()
        >>> config = parser.parse_file("projects/customer_analytics.yml")
        >>> print(config.project.key)
        CUSTOMER_ANALYTICS
    """

    def parse_file(self, path: Union[str, Path]) -> Config:
        """
        Parse single YAML config file.

        Args:
            path: Path to YAML file

        Returns:
            Config object

        Raises:
            ConfigParseError: If file invalid or malformed

        Example:
            >>> parser = ConfigParser()
            >>> config = parser.parse_file("project.yml")
        """
        path = Path(path)

        if not path.exists():
            raise ConfigParseError(f"Config file not found: {path}")

        if not path.is_file():
            raise ConfigParseError(f"Path is not a file: {path}")

        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigParseError(f"Invalid YAML in {path}: {e}")
        except Exception as e:
            raise ConfigParseError(f"Error reading {path}: {e}")

        if data is None:
            raise ConfigParseError(f"Empty YAML file: {path}")

        if not isinstance(data, dict):
            raise ConfigParseError(
                f"Invalid config structure in {path}: expected dict, got {type(data).__name__}"
            )

        try:
            return Config.from_dict(data)
        except KeyError as e:
            raise ConfigParseError(f"Missing required field in {path}: {e}")
        except Exception as e:
            raise ConfigParseError(f"Error parsing config from {path}: {e}")

    def parse_directory(self, path: Union[str, Path]) -> Config:
        """
        Parse directory of config files.

        Expected structure:
            config/
                project.yml       # Project config (required)
                datasets/         # Dataset configs (optional)
                    *.yml
                recipes/          # Recipe configs (optional)
                    *.yml

        Args:
            path: Path to config directory

        Returns:
            Merged Config object with all resources

        Raises:
            ConfigParseError: If structure invalid or files malformed

        Example:
            >>> parser = ConfigParser()
            >>> config = parser.parse_directory("config/")
        """
        path = Path(path)

        if not path.exists():
            raise ConfigParseError(f"Config directory not found: {path}")

        if not path.is_dir():
            raise ConfigParseError(f"Path is not a directory: {path}")

        # Parse project.yml (required)
        project_file = path / "project.yml"
        if not project_file.exists():
            raise ConfigParseError(
                f"project.yml not found in {path}. "
                "Directory-based configs require a project.yml file."
            )

        # Start with project config
        config = self.parse_file(project_file)

        # Parse datasets/ directory (optional)
        datasets_dir = path / "datasets"
        if datasets_dir.exists():
            if not datasets_dir.is_dir():
                raise ConfigParseError(
                    f"datasets path is not a directory: {datasets_dir}"
                )

            dataset_configs = self._parse_yaml_files(datasets_dir)
            for ds_data in dataset_configs:
                # Merge datasets into config
                for ds in ds_data.get("datasets", []):
                    from .models import DatasetConfig

                    dataset = DatasetConfig(
                        name=ds["name"],
                        type=ds["type"],
                        connection=ds.get("connection"),
                        params=ds.get("params", {}),
                        schema=ds.get("schema"),
                        format_type=ds.get("format_type"),
                    )
                    config.datasets.append(dataset)

        # Parse recipes/ directory (optional)
        recipes_dir = path / "recipes"
        if recipes_dir.exists():
            if not recipes_dir.is_dir():
                raise ConfigParseError(
                    f"recipes path is not a directory: {recipes_dir}"
                )

            recipe_configs = self._parse_yaml_files(recipes_dir)
            for rec_data in recipe_configs:
                # Merge recipes into config
                for rec in rec_data.get("recipes", []):
                    from .models import RecipeConfig

                    recipe = RecipeConfig(
                        name=rec["name"],
                        type=rec["type"],
                        inputs=rec.get("inputs", []),
                        outputs=rec.get("outputs", []),
                        params=rec.get("params", {}),
                        code=rec.get("code"),
                    )
                    config.recipes.append(recipe)

        return config

    def _parse_yaml_files(self, directory: Path) -> List[Dict[str, Any]]:
        """
        Parse all YAML files in a directory.

        Args:
            directory: Directory to parse

        Returns:
            List of parsed YAML data dicts

        Raises:
            ConfigParseError: If any file fails to parse
        """
        yaml_files = sorted(directory.glob("*.yml")) + sorted(directory.glob("*.yaml"))

        if not yaml_files:
            return []

        results = []
        for yaml_file in yaml_files:
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)
                if data is not None:
                    results.append(data)
            except yaml.YAMLError as e:
                raise ConfigParseError(f"Invalid YAML in {yaml_file}: {e}")
            except Exception as e:
                raise ConfigParseError(f"Error reading {yaml_file}: {e}")

        return results
