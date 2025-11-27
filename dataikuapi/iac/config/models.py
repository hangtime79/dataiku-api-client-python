"""
Configuration data models for Dataiku IaC.

These models represent the structure of YAML configuration files
that define desired Dataiku project state.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class ProjectConfig:
    """
    Project configuration from YAML.

    Attributes:
        key: Project key (e.g., "CUSTOMER_ANALYTICS")
        name: Human-readable project name
        description: Project description
        settings: Additional project settings
    """

    key: str
    name: str
    description: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DatasetConfig:
    """
    Dataset configuration from YAML.

    Attributes:
        name: Dataset name (e.g., "RAW_CUSTOMERS")
        type: Dataset type (sql, filesystem, snowflake, managed, etc.)
        connection: Connection name (if applicable)
        params: Dataset-specific parameters
        schema: Dataset schema definition
        format_type: Format type for managed datasets (parquet, csv, etc.)
    """

    name: str
    type: str
    connection: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    schema: Optional[Dict[str, Any]] = None
    format_type: Optional[str] = None


@dataclass
class RecipeConfig:
    """
    Recipe configuration from YAML.

    Attributes:
        name: Recipe name (e.g., "prep_customers")
        type: Recipe type (python, sql, join, group, etc.)
        inputs: List of input dataset names
        outputs: List of output dataset names
        params: Recipe-specific parameters
        code: Recipe code (for code recipes like python/sql)
    """

    name: str
    type: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    code: Optional[str] = None


@dataclass
class Config:
    """
    Complete project configuration from YAML.

    Attributes:
        version: Configuration format version (default: "1.0")
        metadata: Configuration metadata
        project: Project configuration
        datasets: List of dataset configurations
        recipes: List of recipe configurations
    """

    version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    project: Optional[ProjectConfig] = None
    datasets: List[DatasetConfig] = field(default_factory=list)
    recipes: List[RecipeConfig] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """
        Create Config from parsed YAML dict.

        Args:
            data: Dictionary from YAML file

        Returns:
            Config object
        """
        # Parse project
        project = None
        if "project" in data:
            proj_data = data["project"]
            project = ProjectConfig(
                key=proj_data["key"],
                name=proj_data["name"],
                description=proj_data.get("description", ""),
                settings=proj_data.get("settings", {}),
            )

        # Parse datasets
        datasets = []
        for ds_data in data.get("datasets", []):
            dataset = DatasetConfig(
                name=ds_data["name"],
                type=ds_data["type"],
                connection=ds_data.get("connection"),
                params=ds_data.get("params", {}),
                schema=ds_data.get("schema"),
                format_type=ds_data.get("format_type"),
            )
            datasets.append(dataset)

        # Parse recipes
        recipes = []
        for rec_data in data.get("recipes", []):
            recipe = RecipeConfig(
                name=rec_data["name"],
                type=rec_data["type"],
                inputs=rec_data.get("inputs", []),
                outputs=rec_data.get("outputs", []),
                params=rec_data.get("params", {}),
                code=rec_data.get("code"),
            )
            recipes.append(recipe)

        return cls(
            version=data.get("version", "1.0"),
            metadata=data.get("metadata", {}),
            project=project,
            datasets=datasets,
            recipes=recipes,
        )
