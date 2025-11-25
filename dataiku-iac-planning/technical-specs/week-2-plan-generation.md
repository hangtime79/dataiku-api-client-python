# Week 2: Plan Generation - Technical Specification

**Document Status:** Implementation Guide
**Created:** 2025-11-24
**Prerequisites:** Week 1 (State Management) Complete
**Session:** claude/review-design-wave-3-01B2tGJohDT7YBCHYePGoYTc

---

## Overview

Week 2 builds on the state management foundation to implement the **plan/apply workflow**. Users will be able to define desired state in YAML configuration files, compare against current Dataiku state, and generate execution plans.

### Goals

1. **Parse YAML configs** - Read and validate project configuration files
2. **Build desired state** - Convert configs into internal State model
3. **Generate plans** - Compare desired vs current state, produce action list
4. **Format output** - Human-readable plan output (Terraform-style)
5. **Validate configs** - Catch errors before execution

### Success Criteria

- ✅ Can parse simple YAML project config
- ✅ Plan shows: 1 to add, 1 to change, 0 to destroy
- ✅ Output is clear and actionable
- ✅ Validation catches common errors
- ✅ >90% test coverage

---

## Architecture Overview

```
YAML Config File(s)
    ↓
ConfigParser (Package 1)
    ↓
Config Validation (Package 2)
    ↓
Desired State Builder (Package 3)
    ↓
Plan Generator (Package 4) ← Uses DiffEngine from Week 1
    ↓
Plan Formatter (Package 5)
    ↓
Human-Readable Plan Output
```

---

## Package Breakdown (6 Independent Packages)

### Package Dependencies

```
Package 1: Config Parser (independent, depends on Week 1)
    ↓
Package 2: Config Validation ←── Depends on Package 1
    ↓
Package 3: Desired State Builder ←── Depends on Packages 1, 2
    ↓
Package 4: Plan Generator ←── Depends on Package 3
Package 5: Plan Formatter ←── Depends on Package 4
    ↓
Package 6: CLI Integration ←── Depends on all packages
```

---

## Package 1: Configuration Parser

**Branch:** `claude/week2-package-1-config-parser`
**Dependencies:** Week 1 (State, Resource models)
**Estimated Effort:** 4-5 hours
**Owner:** Agent 1

### Deliverables

**Files to Create:**
- `dataikuapi/iac/config/__init__.py`
- `dataikuapi/iac/config/parser.py` - YAML parser
- `dataikuapi/iac/config/models.py` - Config data models
- `tests/iac/test_config_parser.py` - Parser tests
- `tests/iac/fixtures/config_simple.yml` - Test fixture
- `tests/iac/fixtures/config_complete.yml` - Test fixture

### Implementation Details

**Config Data Models** (`config/models.py`):

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class ProjectConfig:
    """Project configuration from YAML."""
    key: str
    name: str
    description: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DatasetConfig:
    """Dataset configuration from YAML."""
    name: str
    type: str  # sql, filesystem, snowflake, etc.
    connection: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    schema: Optional[Dict[str, Any]] = None
    format_type: Optional[str] = None

@dataclass
class RecipeConfig:
    """Recipe configuration from YAML."""
    name: str
    type: str  # python, sql, join, group, etc.
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    code: Optional[str] = None

@dataclass
class Config:
    """Complete project configuration."""
    version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    project: Optional[ProjectConfig] = None
    datasets: List[DatasetConfig] = field(default_factory=list)
    recipes: List[RecipeConfig] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create Config from parsed YAML dict."""
        pass
```

**Config Parser** (`config/parser.py`):

```python
import yaml
from pathlib import Path
from typing import Union
from .models import Config
from ..exceptions import ConfigParseError

class ConfigParser:
    """
    Parse YAML configuration files into Config objects.

    Supports:
    - Single file configs
    - Multi-file configs (project/, datasets/, recipes/)
    - Variable substitution (handled separately)
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
        """
        path = Path(path)
        if not path.exists():
            raise ConfigParseError(f"Config file not found: {path}")

        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigParseError(f"Invalid YAML: {e}")

        return Config.from_dict(data)

    def parse_directory(self, path: Union[str, Path]) -> Config:
        """
        Parse directory of config files.

        Expected structure:
            config/
                project.yml       # Project config
                datasets/         # Dataset configs
                    *.yml
                recipes/          # Recipe configs
                    *.yml

        Args:
            path: Path to config directory

        Returns:
            Merged Config object

        Raises:
            ConfigParseError: If structure invalid
        """
        pass
```

### Test Fixtures

**Simple Config** (`tests/iac/fixtures/config_simple.yml`):

```yaml
version: "1.0"

metadata:
  description: "Simple test project"

project:
  key: TEST_PROJECT
  name: Test Project
  description: A simple test project

datasets:
  - name: TEST_DATASET
    type: managed
    format_type: parquet

recipes:
  - name: prep_data
    type: python
    inputs: [TEST_DATASET]
    outputs: [PREPPED_DATA]
    code: |
      # Simple transformation
      output = input
```

### Acceptance Criteria

```bash
# Tests pass
pytest tests/iac/test_config_parser.py -v

# Coverage check
pytest tests/iac/test_config_parser.py \
  --cov=dataikuapi.iac.config.parser \
  --cov=dataikuapi.iac.config.models \
  --cov-report=term-missing

# Must achieve >90% coverage
```

### Checklist

- [ ] Implement Config data models (ProjectConfig, DatasetConfig, RecipeConfig, Config)
- [ ] Implement Config.from_dict() factory method
- [ ] Implement ConfigParser.parse_file()
- [ ] Implement ConfigParser.parse_directory()
- [ ] Create test fixtures (simple and complete configs)
- [ ] Write unit tests for parsing valid configs
- [ ] Write unit tests for error handling (missing files, invalid YAML)
- [ ] Achieve >90% test coverage
- [ ] Add docstrings to all public APIs
- [ ] Update dataikuapi/iac/__init__.py exports

---

## Package 2: Configuration Validation

**Branch:** `claude/week2-package-2-config-validation`
**Dependencies:** Package 1 (Config models)
**Estimated Effort:** 3-4 hours
**Owner:** Agent 2

### Deliverables

**Files to Create:**
- `dataikuapi/iac/config/validator.py` - Validation engine
- `dataikuapi/iac/config/rules.py` - Validation rules
- `dataikuapi/iac/schemas/config_v1.schema.json` - JSON Schema
- `tests/iac/test_config_validation.py` - Validation tests

### Implementation Details

**Validation Engine** (`config/validator.py`):

```python
from typing import List, Dict, Any
from .models import Config
from ..exceptions import ConfigValidationError

class ValidationError:
    """Single validation error."""
    def __init__(self, path: str, message: str, severity: str = "error"):
        self.path = path  # e.g., "datasets[0].name"
        self.message = message
        self.severity = severity  # "error", "warning", "info"

class ConfigValidator:
    """
    Validate configuration objects against rules.

    Checks:
    - Required fields present
    - Valid resource names (uppercase, no spaces)
    - Valid connections exist
    - Valid dataset types
    - Recipe inputs/outputs reference existing datasets
    - No circular dependencies
    """

    def __init__(self, strict: bool = True):
        """
        Initialize validator.

        Args:
            strict: If True, treat warnings as errors
        """
        self.strict = strict

    def validate(self, config: Config) -> List[ValidationError]:
        """
        Validate complete configuration.

        Args:
            config: Config object to validate

        Returns:
            List of validation errors (empty if valid)

        Raises:
            ConfigValidationError: If critical errors found
        """
        errors = []

        # Schema validation
        errors.extend(self._validate_schema(config))

        # Business rules
        errors.extend(self._validate_naming_conventions(config))
        errors.extend(self._validate_references(config))
        errors.extend(self._validate_dependencies(config))

        # Raise if errors found
        if errors:
            raise ConfigValidationError(errors)

        return errors

    def _validate_schema(self, config: Config) -> List[ValidationError]:
        """Validate against JSON Schema."""
        pass

    def _validate_naming_conventions(self, config: Config) -> List[ValidationError]:
        """
        Validate naming conventions.
        - Project keys: UPPERCASE, alphanumeric + underscore
        - Dataset names: UPPERCASE, alphanumeric + underscore
        - Recipe names: lowercase, alphanumeric + underscore
        """
        pass

    def _validate_references(self, config: Config) -> List[ValidationError]:
        """
        Validate references.
        - Recipe inputs reference existing datasets
        - Recipe outputs are defined datasets
        - Connections exist (if checkable)
        """
        pass

    def _validate_dependencies(self, config: Config) -> List[ValidationError]:
        """
        Validate no circular dependencies.
        - Build dependency graph
        - Detect cycles
        """
        pass
```

### Validation Rules

**Key Rules**:

1. **Naming Conventions** (compatible with Snowflake):
   - Project keys: `UPPERCASE_WITH_UNDERSCORES`
   - Dataset names: `UPPERCASE_WITH_UNDERSCORES`
   - Recipe names: `lowercase_with_underscores`

2. **Required Fields**:
   - Project: `key`, `name`
   - Dataset: `name`, `type`
   - Recipe: `name`, `type`, `outputs` (at least one)

3. **Reference Integrity**:
   - Recipe inputs must reference existing datasets
   - Recipe outputs must be defined datasets
   - No circular dependencies

4. **Type Validation**:
   - Valid dataset types: `sql`, `filesystem`, `snowflake`, `managed`, etc.
   - Valid recipe types: `python`, `sql`, `join`, `group`, etc.

### Acceptance Criteria

```bash
# Tests pass
pytest tests/iac/test_config_validation.py -v

# Coverage check
pytest tests/iac/test_config_validation.py \
  --cov=dataikuapi.iac.config.validator \
  --cov-report=term-missing
```

### Checklist

- [ ] Implement ValidationError class
- [ ] Implement ConfigValidator class
- [ ] Implement schema validation
- [ ] Implement naming convention validation
- [ ] Implement reference validation
- [ ] Implement dependency graph validation
- [ ] Create JSON Schema for config files
- [ ] Write unit tests for valid configs
- [ ] Write unit tests for invalid configs (all rule violations)
- [ ] Achieve >90% test coverage
- [ ] Add docstrings

---

## Package 3: Desired State Builder

**Branch:** `claude/week2-package-3-desired-state-builder`
**Dependencies:** Packages 1, 2 (Config models, validation)
**Estimated Effort:** 4-5 hours
**Owner:** Agent 3

### Deliverables

**Files to Create:**
- `dataikuapi/iac/config/builder.py` - State builder
- `tests/iac/test_state_builder.py` - Builder tests

### Implementation Details

**State Builder** (`config/builder.py`):

```python
from typing import Dict, Any
from .models import Config, ProjectConfig, DatasetConfig, RecipeConfig
from ..models.state import State, Resource, ResourceMetadata, make_resource_id
from ..exceptions import BuildError

class DesiredStateBuilder:
    """
    Build State object from Config.

    Converts declarative configuration into internal State model
    that can be compared with current Dataiku state.
    """

    def __init__(self, environment: str = "default"):
        """
        Initialize builder.

        Args:
            environment: Target environment name
        """
        self.environment = environment

    def build(self, config: Config) -> State:
        """
        Build State from Config.

        Args:
            config: Validated configuration

        Returns:
            State object representing desired state

        Raises:
            BuildError: If conversion fails
        """
        state = State(environment=self.environment)

        # Build project resource
        if config.project:
            resource = self._build_project(config.project)
            state.add_resource(resource)

        # Build dataset resources
        for dataset_cfg in config.datasets:
            resource = self._build_dataset(dataset_cfg, config.project.key)
            state.add_resource(resource)

        # Build recipe resources
        for recipe_cfg in config.recipes:
            resource = self._build_recipe(recipe_cfg, config.project.key)
            state.add_resource(resource)

        return state

    def _build_project(self, cfg: ProjectConfig) -> Resource:
        """
        Convert ProjectConfig to Resource.

        Args:
            cfg: Project configuration

        Returns:
            Resource object for project
        """
        resource_id = make_resource_id("project", cfg.key)

        attributes = {
            "projectKey": cfg.key,
            "name": cfg.name,
            "description": cfg.description,
            "settings": cfg.settings
        }

        metadata = ResourceMetadata(
            created_by="config",
            config_source="yaml"
        )

        return Resource(
            resource_id=resource_id,
            resource_type="project",
            attributes=attributes,
            metadata=metadata
        )

    def _build_dataset(self, cfg: DatasetConfig, project_key: str) -> Resource:
        """Convert DatasetConfig to Resource."""
        pass

    def _build_recipe(self, cfg: RecipeConfig, project_key: str) -> Resource:
        """Convert RecipeConfig to Resource."""
        pass
```

### Acceptance Criteria

```bash
pytest tests/iac/test_state_builder.py -v
pytest tests/iac/test_state_builder.py \
  --cov=dataikuapi.iac.config.builder \
  --cov-report=term-missing
```

### Checklist

- [ ] Implement DesiredStateBuilder class
- [ ] Implement build() method
- [ ] Implement _build_project()
- [ ] Implement _build_dataset()
- [ ] Implement _build_recipe()
- [ ] Write unit tests for building each resource type
- [ ] Write unit tests for complete configs
- [ ] Test error handling
- [ ] Achieve >90% test coverage
- [ ] Add docstrings

---

## Package 4: Plan Generator

**Branch:** `claude/week2-package-4-plan-generator`
**Dependencies:** Package 3 (DesiredStateBuilder), Week 1 (DiffEngine)
**Estimated Effort:** 4-5 hours
**Owner:** Agent 4

### Deliverables

**Files to Create:**
- `dataikuapi/iac/planner/__init__.py`
- `dataikuapi/iac/planner/engine.py` - Plan generator
- `dataikuapi/iac/planner/models.py` - Plan data models
- `tests/iac/test_planner.py` - Planner tests

### Implementation Details

**Plan Models** (`planner/models.py`):

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum
from ..models.diff import ResourceDiff, ChangeType

class ActionType(Enum):
    """Type of action in execution plan."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    NO_CHANGE = "no-change"

@dataclass
class PlannedAction:
    """
    Single action in execution plan.
    """
    action_type: ActionType
    resource_id: str
    resource_type: str
    diff: ResourceDiff
    dependencies: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        """Human-readable action description."""
        pass

@dataclass
class ExecutionPlan:
    """
    Complete execution plan.

    Ordered list of actions to transform current state
    into desired state.
    """
    actions: List[PlannedAction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> Dict[str, int]:
        """
        Get plan summary.

        Returns:
            Dict with counts: {create: N, update: N, delete: N, no_change: N}
        """
        pass

    def has_changes(self) -> bool:
        """Check if plan has any changes."""
        return any(a.action_type != ActionType.NO_CHANGE for a in self.actions)
```

**Plan Generator** (`planner/engine.py`):

```python
from ..models.state import State
from ..diff import DiffEngine, ChangeType
from .models import ExecutionPlan, PlannedAction, ActionType

class PlanGenerator:
    """
    Generate execution plans.

    Compares desired state vs current state and produces
    ordered list of actions to achieve desired state.
    """

    def __init__(self):
        self.diff_engine = DiffEngine()

    def generate_plan(
        self,
        current_state: State,
        desired_state: State
    ) -> ExecutionPlan:
        """
        Generate execution plan.

        Args:
            current_state: Current state from Dataiku
            desired_state: Desired state from config

        Returns:
            ExecutionPlan with ordered actions
        """
        # Compute diffs
        diffs = self.diff_engine.diff(current_state, desired_state)

        # Convert diffs to actions
        actions = []
        for diff in diffs:
            action = self._diff_to_action(diff)
            actions.append(action)

        # Order actions by dependencies
        ordered_actions = self._order_by_dependencies(actions)

        return ExecutionPlan(
            actions=ordered_actions,
            metadata={
                "current_serial": current_state.serial,
                "total_actions": len(ordered_actions)
            }
        )

    def _diff_to_action(self, diff: ResourceDiff) -> PlannedAction:
        """Convert ResourceDiff to PlannedAction."""
        action_map = {
            ChangeType.ADDED: ActionType.CREATE,
            ChangeType.REMOVED: ActionType.DELETE,
            ChangeType.MODIFIED: ActionType.UPDATE,
            ChangeType.UNCHANGED: ActionType.NO_CHANGE
        }

        return PlannedAction(
            action_type=action_map[diff.change_type],
            resource_id=diff.resource_id,
            resource_type=diff.resource_type,
            diff=diff
        )

    def _order_by_dependencies(
        self,
        actions: List[PlannedAction]
    ) -> List[PlannedAction]:
        """
        Order actions respecting dependencies.

        Rules:
        - Projects before datasets/recipes
        - Datasets before recipes that use them
        - Creates before updates
        - Deletes after everything else
        """
        pass
```

### Acceptance Criteria

```bash
pytest tests/iac/test_planner.py -v
pytest tests/iac/test_planner.py \
  --cov=dataikuapi.iac.planner \
  --cov-report=term-missing
```

### Checklist

- [ ] Implement ActionType enum
- [ ] Implement PlannedAction class
- [ ] Implement ExecutionPlan class
- [ ] Implement PlanGenerator class
- [ ] Implement generate_plan()
- [ ] Implement action ordering by dependencies
- [ ] Write unit tests for plan generation
- [ ] Test dependency ordering
- [ ] Test all change types (create, update, delete)
- [ ] Achieve >90% test coverage
- [ ] Add docstrings

---

## Package 5: Plan Formatter

**Branch:** `claude/week2-package-5-plan-formatter`
**Dependencies:** Package 4 (PlanGenerator)
**Estimated Effort:** 3-4 hours
**Owner:** Agent 5

### Deliverables

**Files to Create:**
- `dataikuapi/iac/planner/formatter.py` - Output formatter
- `tests/iac/test_plan_formatter.py` - Formatter tests

### Implementation Details

**Plan Formatter** (`planner/formatter.py`):

```python
from typing import TextIO
import sys
from .models import ExecutionPlan, PlannedAction, ActionType

class PlanFormatter:
    """
    Format execution plans for human-readable output.

    Terraform-style output with color coding and symbols.
    """

    # ANSI color codes
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Action symbols
    SYMBOLS = {
        ActionType.CREATE: "+",
        ActionType.UPDATE: "~",
        ActionType.DELETE: "-",
        ActionType.NO_CHANGE: " "
    }

    def __init__(self, color: bool = True):
        """
        Initialize formatter.

        Args:
            color: Enable color output (disable for CI/logs)
        """
        self.color = color

    def format(self, plan: ExecutionPlan, output: TextIO = sys.stdout) -> None:
        """
        Format plan to output stream.

        Args:
            plan: ExecutionPlan to format
            output: Output stream (default: stdout)
        """
        # Header
        output.write(self._format_header(plan))
        output.write("\n\n")

        # Actions
        for action in plan.actions:
            if action.action_type != ActionType.NO_CHANGE:
                output.write(self._format_action(action))
                output.write("\n")

        # Summary
        output.write("\n")
        output.write(self._format_summary(plan))
        output.write("\n")

    def _format_header(self, plan: ExecutionPlan) -> str:
        """Format plan header."""
        return f"{self.BOLD}Dataiku IaC Execution Plan{self.RESET}"

    def _format_action(self, action: PlannedAction) -> str:
        """
        Format single action.

        Example outputs:
          + project.CUSTOMER_ANALYTICS
              name: "Customer Analytics"
              description: "Customer analytics pipeline"

          ~ dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS
              ~ description: "Raw data" => "Raw customer data"
              ~ schema.columns[0].type: "int" => "bigint"

          - recipe.CUSTOMER_ANALYTICS.old_recipe
        """
        symbol = self.SYMBOLS[action.action_type]
        color = self._get_color(action.action_type)

        lines = []

        # Action line
        lines.append(f"{color}{symbol} {action.resource_id}{self.RESET}")

        # Attribute changes (for UPDATE)
        if action.action_type == ActionType.UPDATE:
            for attr_diff in action.diff.attribute_diffs:
                old = attr_diff.get("old_value")
                new = attr_diff.get("new_value")
                path = attr_diff.get("path")
                lines.append(f"    {color}~{self.RESET} {path}: {old} => {new}")

        # New attributes (for CREATE)
        elif action.action_type == ActionType.CREATE:
            for key, value in action.diff.new_resource.attributes.items():
                if key not in ["checksum"]:  # Skip internal fields
                    lines.append(f"    {key}: {self._format_value(value)}")

        return "\n".join(lines)

    def _format_summary(self, plan: ExecutionPlan) -> str:
        """
        Format plan summary.

        Example:
          Plan: 2 to create, 1 to update, 0 to destroy.
        """
        summary = plan.summary()

        parts = []
        if summary.get("create", 0) > 0:
            parts.append(f"{self.GREEN}{summary['create']} to create{self.RESET}")
        if summary.get("update", 0) > 0:
            parts.append(f"{self.YELLOW}{summary['update']} to update{self.RESET}")
        if summary.get("delete", 0) > 0:
            parts.append(f"{self.RED}{summary['delete']} to destroy{self.RESET}")

        if not parts:
            return f"{self.BOLD}No changes. Infrastructure is up-to-date.{self.RESET}"

        return f"{self.BOLD}Plan:{self.RESET} {', '.join(parts)}."

    def _get_color(self, action_type: ActionType) -> str:
        """Get color for action type."""
        if not self.color:
            return ""

        return {
            ActionType.CREATE: self.GREEN,
            ActionType.UPDATE: self.YELLOW,
            ActionType.DELETE: self.RED,
            ActionType.NO_CHANGE: self.RESET
        }.get(action_type, self.RESET)

    def _format_value(self, value: any) -> str:
        """Format attribute value for display."""
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, (list, dict)):
            return "..."  # Truncate complex types
        else:
            return str(value)
```

### Acceptance Criteria

```bash
pytest tests/iac/test_plan_formatter.py -v
pytest tests/iac/test_plan_formatter.py \
  --cov=dataikuapi.iac.planner.formatter \
  --cov-report=term-missing
```

### Checklist

- [ ] Implement PlanFormatter class
- [ ] Implement format() method
- [ ] Implement _format_header()
- [ ] Implement _format_action() for all action types
- [ ] Implement _format_summary()
- [ ] Support color and no-color modes
- [ ] Write unit tests for formatting
- [ ] Test with various plan scenarios
- [ ] Achieve >90% test coverage
- [ ] Add docstrings

---

## Package 6: CLI Integration & End-to-End

**Branch:** `claude/week2-package-6-cli-integration`
**Dependencies:** All packages 1-5
**Estimated Effort:** 4-5 hours
**Owner:** Agent 6

### Deliverables

**Files to Create:**
- `dataikuapi/iac/cli/plan.py` - Plan command
- `tests/iac/test_cli_plan.py` - CLI tests
- `demos/week2_plan_workflow.py` - Demo script
- `dataiku-iac-planning/technical-specs/week-2-completion-checklist.md`

### Implementation Details

**Plan Command** (`cli/plan.py`):

```python
import click
from pathlib import Path
from ..config.parser import ConfigParser
from ..config.validator import ConfigValidator
from ..config.builder import DesiredStateBuilder
from ..planner.engine import PlanGenerator
from ..planner.formatter import PlanFormatter
from ..manager import StateManager
from ..backends.local import LocalFileBackend

@click.command()
@click.option(
    "-c", "--config",
    type=click.Path(exists=True),
    required=True,
    help="Path to configuration file or directory"
)
@click.option(
    "-e", "--environment",
    default="dev",
    help="Target environment"
)
@click.option(
    "--state-file",
    type=click.Path(),
    help="Path to state file (default: .dataiku/state/{env}.state.json)"
)
@click.option(
    "--no-color",
    is_flag=True,
    help="Disable color output"
)
def plan(config: str, environment: str, state_file: str, no_color: bool):
    """
    Generate execution plan.

    Compares configuration file against current Dataiku state
    and shows what actions would be taken.

    Examples:
        dataiku-iac plan -c projects/customer_analytics.yml -e dev
        dataiku-iac plan -c config/ -e prod --no-color
    """
    try:
        # Parse config
        click.echo("Parsing configuration...")
        parser = ConfigParser()
        config_obj = parser.parse_file(config)

        # Validate config
        click.echo("Validating configuration...")
        validator = ConfigValidator()
        validator.validate(config_obj)

        # Build desired state
        click.echo("Building desired state...")
        builder = DesiredStateBuilder(environment)
        desired_state = builder.build(config_obj)

        # Load current state
        click.echo("Loading current state...")
        if not state_file:
            state_file = Path(f".dataiku/state/{environment}.state.json")
        backend = LocalFileBackend(state_file)
        current_state = State(environment=environment)
        if backend.exists():
            current_state = backend.load()

        # Generate plan
        click.echo("Generating plan...")
        planner = PlanGenerator()
        plan = planner.generate_plan(current_state, desired_state)

        # Format output
        click.echo("\n")
        formatter = PlanFormatter(color=not no_color)
        formatter.format(plan)

        # Exit code
        if plan.has_changes():
            raise click.exceptions.Exit(2)  # Changes detected
        else:
            raise click.exceptions.Exit(0)  # No changes

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.exceptions.Exit(1)
```

### Demo Script

**Week 2 Demo** (`demos/week2_plan_workflow.py`):

```python
#!/usr/bin/env python3
"""
Week 2 Demo: Plan Workflow

Demonstrates:
1. Parsing YAML config
2. Validating config
3. Building desired state
4. Generating plan
5. Formatting plan output
"""

from pathlib import Path
from dataikuapi.iac.config.parser import ConfigParser
from dataikuapi.iac.config.validator import ConfigValidator
from dataikuapi.iac.config.builder import DesiredStateBuilder
from dataikuapi.iac.planner.engine import PlanGenerator
from dataikuapi.iac.planner.formatter import PlanFormatter
from dataikuapi.iac.models.state import State

def main():
    print("=== Week 2 Demo: Plan Workflow ===\n")

    # 1. Parse config
    print("Step 1: Parsing configuration...")
    parser = ConfigParser()
    config = parser.parse_file("tests/iac/fixtures/config_simple.yml")
    print(f"✓ Parsed config for project: {config.project.key}\n")

    # 2. Validate config
    print("Step 2: Validating configuration...")
    validator = ConfigValidator()
    errors = validator.validate(config)
    print(f"✓ Validation passed (0 errors)\n")

    # 3. Build desired state
    print("Step 3: Building desired state...")
    builder = DesiredStateBuilder(environment="demo")
    desired_state = builder.build(config)
    print(f"✓ Built desired state with {len(desired_state.resources)} resources\n")

    # 4. Generate plan (empty current state)
    print("Step 4: Generating plan...")
    current_state = State(environment="demo")
    planner = PlanGenerator()
    plan = planner.generate_plan(current_state, desired_state)
    print(f"✓ Generated plan with {len(plan.actions)} actions\n")

    # 5. Format plan
    print("Step 5: Plan output:\n")
    formatter = PlanFormatter(color=True)
    formatter.format(plan)

    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    main()
```

### Acceptance Criteria

```bash
# CLI tests pass
pytest tests/iac/test_cli_plan.py -v

# Demo script works
python demos/week2_plan_workflow.py

# End-to-end integration test
# (Create config, generate plan, verify output)
pytest tests/iac/test_integration_week2.py -v
```

### Checklist

- [ ] Implement plan CLI command
- [ ] Write CLI tests
- [ ] Create demo script
- [ ] Write integration test for complete workflow
- [ ] Test with various config scenarios
- [ ] Test error handling
- [ ] Achieve >90% test coverage
- [ ] Create completion checklist document
- [ ] Update main CLI entry point

---

## Testing Strategy

### Unit Tests

Each package must have comprehensive unit tests:

- **Package 1:** Parse valid/invalid YAML, test all config types
- **Package 2:** Validate all rules, test error messages
- **Package 3:** Build state from configs, test all resource types
- **Package 4:** Generate plans for all change scenarios
- **Package 5:** Format all action types, test color/no-color
- **Package 6:** CLI integration, error handling

### Integration Tests

**End-to-End Scenarios:**

1. **Basic Plan** - Config with 1 project, 1 dataset → Plan shows 2 creates
2. **Update Detection** - Modify config → Plan shows 1 update
3. **Delete Detection** - Remove resource from config → Plan shows 1 delete
4. **No Changes** - Config matches state → Plan shows no changes
5. **Complex Project** - Multiple datasets, recipes → Plan orders correctly
6. **Invalid Config** - Bad YAML → Error with helpful message
7. **Validation Errors** - Invalid resource names → Validation errors

### Fixtures

**Required Test Fixtures:**

- `config_simple.yml` - Minimal valid config (1 project, 1 dataset)
- `config_complete.yml` - Complex config (project, 3 datasets, 2 recipes)
- `config_invalid_yaml.yml` - Invalid YAML syntax
- `config_invalid_names.yml` - Invalid resource names
- `config_circular_deps.yml` - Circular dependencies

---

## Documentation Updates

### Files to Update

1. **README.md** - Add Week 2 status
2. **WAVE_3_COMPLETION_REPORT.md** - Create completion report
3. **dataikuapi/iac/__init__.py** - Export new classes
4. **docs/** - Add plan workflow guide

### New Documentation

Create `dataiku-iac-planning/guides/02-plan-workflow.md`:

```markdown
# Plan Workflow Guide

## Overview

The plan workflow allows you to preview changes before applying them.

## Quick Start

```bash
# Create config
cat > project.yml <<EOF
project:
  key: TEST_PROJECT
  name: Test Project
datasets:
  - name: TEST_DATA
    type: managed
EOF

# Generate plan
dataiku-iac plan -c project.yml -e dev

# Output:
#  + project.TEST_PROJECT
#  + dataset.TEST_PROJECT.TEST_DATA
#
# Plan: 2 to create, 0 to update, 0 to destroy.
```

## Configuration Format

See [Configuration Format Guide](config-format.md) for details.

## Validation

See [Validation Rules](validation-rules.md) for details.
```

---

## Coordination

### Branch Strategy

Each agent creates own branch:
```
claude/week2-package-1-config-parser
claude/week2-package-2-config-validation
claude/week2-package-3-desired-state-builder
claude/week2-package-4-plan-generator
claude/week2-package-5-plan-formatter
claude/week2-package-6-cli-integration
```

### Merge Order

1. **Package 1** (Config Parser) - Independent, merge first
2. **Package 2** (Validation) - Depends on Package 1
3. **Package 3** (State Builder) - Depends on Packages 1, 2
4. **Packages 4 & 5** (Planner & Formatter) - Can be parallel
5. **Package 6** (CLI Integration) - Final integration

### Success Criteria

Week 2 complete when:

- [ ] All 6 packages merged
- [ ] All tests passing
- [ ] >90% coverage
- [ ] Demo script works
- [ ] Can generate plans from YAML configs
- [ ] Plan output is clear and actionable
- [ ] Ready for Week 3 (Apply execution)

---

## Next: Week 3 (Apply Execution)

Week 3 will implement:
- Apply engine
- Resource creation/update/deletion
- Checkpointing and rollback
- Progress reporting

---

**Document Version:** 1.0
**Status:** Ready for Implementation
**Next Review:** After all packages complete
