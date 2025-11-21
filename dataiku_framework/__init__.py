"""
Dataiku Framework - Projects as Code

A declarative framework for managing Dataiku projects through configuration files.
Enables AI agents to create and manage Dataiku projects via natural language.

Usage:
    from dataiku_framework import FrameworkConfig, Engine

    # Load config
    config = FrameworkConfig.from_yaml("project.yaml")

    # Preview changes
    engine = Engine(host, api_key)
    plan = engine.plan(config)
    print(plan.summary())

    # Apply changes
    result = engine.apply(config)
"""

__version__ = "1.0.0"
__author__ = "Dataiku Framework Contributors"

from dataiku_framework.config.schema import (
    FrameworkConfig,
    ProjectConfig,
    DatasetConfig,
    RecipeConfig,
    ScenarioConfig,
)
from dataiku_framework.engine.engine import Engine
from dataiku_framework.models.plan import Plan
from dataiku_framework.models.state import State, Diff

__all__ = [
    "FrameworkConfig",
    "ProjectConfig",
    "DatasetConfig",
    "RecipeConfig",
    "ScenarioConfig",
    "Engine",
    "Plan",
    "State",
    "Diff",
]
