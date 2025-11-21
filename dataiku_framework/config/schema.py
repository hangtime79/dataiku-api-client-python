"""
Pydantic models for configuration validation

Defines the schema for YAML/JSON configuration files that describe Dataiku projects.
"""

from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path
import re


class ProjectConfig(BaseModel):
    """Project-level configuration"""

    key: str = Field(
        ...,
        description="Project key (must be uppercase alphanumeric + underscore)",
        examples=["CUSTOMER_ANALYTICS", "SALES_REPORTING"],
    )
    name: str = Field(..., description="Human-readable project name")
    description: Optional[str] = Field(None, description="Project description")
    owner: Optional[str] = Field(None, description="Project owner username")
    settings: Dict[str, Any] = Field(
        default_factory=dict, description="Additional project settings"
    )

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        """Validate project key format"""
        if not re.match(r"^[A-Z][A-Z0-9_]*$", v):
            raise ValueError(
                f"Project key '{v}' must start with uppercase letter "
                f"and contain only uppercase letters, numbers, and underscores"
            )
        return v


class DatasetConfig(BaseModel):
    """Dataset configuration"""

    name: str = Field(
        ...,
        description="Dataset name (UPPERCASE recommended for Snowflake compatibility)",
    )
    type: Literal[
        "SQL",
        "Filesystem",
        "UploadedFiles",
        "HTTP",
        "S3",
        "HDFS",
        "Snowflake",
        "BigQuery",
        "Redshift",
        "Synapse",
    ] = Field(..., description="Dataset type")
    connection: str = Field(..., description="Connection name (must exist in Dataiku)")
    managed: bool = Field(
        False, description="Whether this is a managed (internal) dataset"
    )
    format_type: Optional[str] = Field(
        None, description="Format for filesystem datasets (csv, parquet, json, etc.)"
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dataset-specific parameters (schema, table, path, etc.)",
    )
    schema: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Dataset schema definition (list of {name, type} dicts)",
    )
    build_mode: Optional[Literal["NON_RECURSIVE", "RECURSIVE"]] = Field(
        None, description="Build mode for dataset"
    )
    partition_spec: Optional[str] = Field(
        None, description="Partition specification (e.g., '%Y-%m-%d')"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Warn if name is not uppercase (Snowflake best practice)"""
        if v != v.upper():
            # Note: We allow lowercase, but recommend uppercase
            pass
        return v

    @model_validator(mode="after")
    def validate_sql_params(self):
        """Validate SQL dataset parameters"""
        if self.type == "SQL" and "table" not in self.params:
            if "query" not in self.params:
                raise ValueError(
                    f"SQL dataset '{self.name}' must have either 'table' or 'query' in params"
                )
        return self


class RecipeConfig(BaseModel):
    """Recipe configuration"""

    name: str = Field(..., description="Recipe name")
    type: Literal[
        "python",
        "sql",
        "r",
        "shell",
        "grouping",
        "window",
        "join",
        "vstack",
        "hstack",
        "sort",
        "topn",
        "distinct",
        "prepare",
        "split",
        "sampling",
        "pivot",
    ] = Field(..., description="Recipe type")
    inputs: List[str] = Field(..., description="List of input dataset names")
    outputs: List[str] = Field(..., description="List of output dataset names")

    # Code recipes (python, sql, r, shell)
    code: Optional[str] = Field(None, description="Inline code for the recipe")
    code_file: Optional[str] = Field(
        None, description="Path to external code file (relative to config)"
    )

    # Visual recipes
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Recipe-specific parameters"
    )

    # Execution settings
    engine: Optional[str] = Field(
        None, description="Execution engine (DSS, SPARK, SQL, etc.)"
    )
    compute_schema_updates: bool = Field(
        True, description="Whether to auto-compute schema updates before running"
    )

    @model_validator(mode="after")
    def validate_code_recipes(self):
        """Validate code recipe configuration"""
        code_types = {"python", "sql", "r", "shell"}

        if self.type in code_types:
            # Must have either code or code_file
            if not self.code and not self.code_file:
                raise ValueError(
                    f"Code recipe '{self.name}' must have either 'code' or 'code_file'"
                )
            # Cannot have both
            if self.code and self.code_file:
                raise ValueError(
                    f"Code recipe '{self.name}' cannot have both 'code' and 'code_file'"
                )
        else:
            # Visual recipes should not have code
            if self.code or self.code_file:
                raise ValueError(
                    f"Visual recipe '{self.name}' (type={self.type}) should use 'params', not code"
                )

        return self


class TriggerConfig(BaseModel):
    """Scenario trigger configuration"""

    type: Literal["manual", "temporal", "dataset", "sql"] = Field(
        ..., description="Trigger type"
    )

    # Temporal trigger
    frequency: Optional[Literal["hourly", "daily", "weekly", "monthly"]] = None
    hour: Optional[int] = Field(None, ge=0, le=23)
    minute: Optional[int] = Field(None, ge=0, le=59)
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    day_of_month: Optional[int] = Field(None, ge=1, le=31)

    # Dataset trigger
    dataset: Optional[str] = None
    event_type: Optional[Literal["modified", "created"]] = None

    # SQL trigger
    connection: Optional[str] = None
    sql: Optional[str] = None

    @model_validator(mode="after")
    def validate_trigger_params(self):
        """Validate trigger-specific parameters"""
        if self.type == "temporal" and not self.frequency:
            raise ValueError("Temporal trigger must have 'frequency'")

        if self.type == "dataset" and not self.dataset:
            raise ValueError("Dataset trigger must have 'dataset'")

        if self.type == "sql":
            if not self.connection or not self.sql:
                raise ValueError("SQL trigger must have 'connection' and 'sql'")

        return self


class ScenarioStepConfig(BaseModel):
    """Scenario step configuration"""

    type: Literal[
        "build_flowitem",
        "build_dataset",
        "run_recipe",
        "run_scenario",
        "execute_sql",
        "python",
        "shell",
    ] = Field(..., description="Step type")

    # Build steps
    items: Optional[List[str]] = Field(
        None, description="Items to build (datasets, recipes)"
    )
    build_mode: Optional[Literal["NON_RECURSIVE", "RECURSIVE"]] = Field(
        None, description="Build mode"
    )

    # Execute steps
    code: Optional[str] = Field(None, description="Code to execute")
    code_file: Optional[str] = Field(None, description="Path to code file")
    connection: Optional[str] = Field(None, description="Connection for SQL steps")

    # Run scenario
    scenario: Optional[str] = Field(None, description="Scenario to run")

    @model_validator(mode="after")
    def validate_step_params(self):
        """Validate step-specific parameters"""
        if self.type in ["build_flowitem", "build_dataset"] and not self.items:
            raise ValueError(f"Build step must have 'items'")

        if self.type == "execute_sql":
            if not self.connection or not self.code:
                raise ValueError("SQL step must have 'connection' and 'code'")

        if self.type == "run_scenario" and not self.scenario:
            raise ValueError("Run scenario step must have 'scenario'")

        return self


class ScenarioConfig(BaseModel):
    """Scenario configuration"""

    name: str = Field(..., description="Scenario name")
    active: bool = Field(True, description="Whether scenario is active")
    triggers: List[TriggerConfig] = Field(
        default_factory=list, description="Scenario triggers"
    )
    steps: List[ScenarioStepConfig] = Field(
        default_factory=list, description="Scenario steps"
    )
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Additional scenario parameters"
    )


class FrameworkConfig(BaseModel):
    """Complete framework configuration"""

    version: str = Field(
        default="1.0", description="Config schema version", pattern=r"^\d+\.\d+$"
    )
    project: ProjectConfig = Field(..., description="Project configuration")
    datasets: List[DatasetConfig] = Field(
        default_factory=list, description="Dataset definitions"
    )
    recipes: List[RecipeConfig] = Field(
        default_factory=list, description="Recipe definitions"
    )
    scenarios: List[ScenarioConfig] = Field(
        default_factory=list, description="Scenario definitions"
    )

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="User-defined metadata (not applied to Dataiku)",
    )

    @classmethod
    def from_dict(cls, data: dict) -> "FrameworkConfig":
        """Create config from dictionary"""
        return cls.model_validate(data)

    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "FrameworkConfig":
        """Load config from YAML file"""
        from dataiku_framework.config.parser import ConfigParser

        return ConfigParser.parse_yaml(path)

    @classmethod
    def from_json(cls, path: Union[str, Path]) -> "FrameworkConfig":
        """Load config from JSON file"""
        from dataiku_framework.config.parser import ConfigParser

        return ConfigParser.parse_json(path)

    def to_dict(self) -> dict:
        """Export config to dictionary"""
        return self.model_dump(exclude_none=True)

    def to_yaml(self, path: Union[str, Path]) -> None:
        """Save config to YAML file"""
        from dataiku_framework.config.parser import ConfigParser

        ConfigParser.write_yaml(self, path)

    def to_json(self, path: Union[str, Path]) -> None:
        """Save config to JSON file"""
        from dataiku_framework.config.parser import ConfigParser

        ConfigParser.write_json(self, path)

    def validate_dependencies(self) -> List[str]:
        """
        Validate recipe dependencies.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Get all dataset names
        dataset_names = {ds.name for ds in self.datasets}

        # Check each recipe's inputs/outputs
        for recipe in self.recipes:
            # Check inputs exist
            for input_name in recipe.inputs:
                if input_name not in dataset_names:
                    errors.append(
                        f"Recipe '{recipe.name}' references unknown input '{input_name}'"
                    )

            # Check outputs exist
            for output_name in recipe.outputs:
                if output_name not in dataset_names:
                    errors.append(
                        f"Recipe '{recipe.name}' references unknown output '{output_name}'"
                    )

        # Check for circular dependencies
        # (Will implement in dependency.py)

        return errors

    def get_dependency_order(self) -> List[str]:
        """
        Calculate dependency order for recipes.

        Returns:
            List of recipe names in execution order
        """
        from dataiku_framework.engine.dependency import DependencyResolver

        return DependencyResolver.resolve(self.recipes)
