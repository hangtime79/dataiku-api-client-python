# Dataiku Framework Architecture

**Version:** 1.0
**Last Updated:** 2025-11-21
**Purpose:** Projects as Code for Dataiku - AI-driven infrastructure management

---

## Vision

Enable AI agents (Claude Code, etc.) to translate natural language into Dataiku projects through declarative configuration files.

**User Experience:**
```
User: "Create a customer analytics pipeline from Snowflake"
  ↓
Agent: Generates customer_analytics.yaml
  ↓
User: Reviews/modifies YAML (iterative refinement)
  ↓
Agent: Applies configuration → Dataiku project created
  ↓
User: "Change scenario to run at 3 AM"
  ↓
Agent: Updates YAML + re-applies → Only scenario modified
```

---

## Core Principles

1. **Declarative Configuration** - Describe WHAT you want, not HOW to build it
2. **Infrastructure as Code** - Version-controlled YAML/JSON configurations
3. **Idempotent Operations** - Apply same config multiple times = same result
4. **State Management** - Track desired vs. actual state, calculate diffs
5. **Git-Backed Versioning** - Leverage Dataiku's built-in git for rollback/rollforward
6. **Iterative Refinement** - Support incremental changes, not just full rebuilds
7. **Dataiku-Native** - Follow Dataiku patterns and conventions

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User / AI Agent                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ├─> Natural Language (AI translates)
                      │
                      ├─> YAML/JSON Config (human editable)
                      │
                      ├─> Python API (programmatic)
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Dataiku Framework                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Config Layer                                        │   │
│  │  - YAML/JSON Parser                                  │   │
│  │  - Pydantic Models (validation)                      │   │
│  │  - Schema Versioning                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                      │                                       │
│  ┌──────────────────▼──────────────────────────────────┐   │
│  │  State Management                                    │   │
│  │  - Current State (query Dataiku)                     │   │
│  │  - Desired State (from config)                       │   │
│  │  - Diff Calculation (create/update/delete)           │   │
│  │  - Git Integration (versioning/rollback)             │   │
│  └──────────────────────────────────────────────────────┘   │
│                      │                                       │
│  ┌──────────────────▼──────────────────────────────────┐   │
│  │  Execution Engine                                    │   │
│  │  - Plan (preview changes)                            │   │
│  │  - Apply (execute changes)                           │   │
│  │  - Rollback (revert to previous)                     │   │
│  │  - Verify (check consistency)                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                      │                                       │
│  ┌──────────────────▼──────────────────────────────────┐   │
│  │  Builders (create/update resources)                  │   │
│  │  - ProjectBuilder                                    │   │
│  │  - DatasetBuilder (SQL, Filesystem, etc.)            │   │
│  │  - RecipeBuilder (Python, Visual, etc.)              │   │
│  │  - ScenarioBuilder                                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              Dataiku Python API (dataikuapi)                │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  Dataiku DSS Instance                       │
│              (Projects, Datasets, Recipes, etc.)            │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### A. Configuration Format

**Primary:** YAML (human-readable, AI-friendly, supports comments)
**Secondary:** JSON (machine-readable, strict parsing)

**Features:**
- Inline code blocks (short recipes)
- External file references (long recipes)
- Comments preserved (for documentation)
- Multi-document support (split large configs)

**Example:**
```yaml
# customer_analytics.yaml
project:
  key: CUSTOMER_ANALYTICS
  name: "Customer Analytics Pipeline"

datasets:
  - name: RAW_CUSTOMERS
    type: SQL
    connection: snowflake_prod  # Reference only, not defined

recipes:
  - name: clean_customers
    type: python
    code: |
      # Inline code for short recipes
      df = dataiku.Dataset("RAW_CUSTOMERS").get_dataframe()
      df.dropna()

  - name: complex_transformation
    type: python
    code_file: recipes/complex_transformation.py  # External file
```

### B. State Management

**State Storage:**
- Stored in Dataiku project's git repository
- File: `.dataiku_framework/state.json`
- Versioned alongside project changes
- Enables audit trail and rollback

**State Contents:**
```json
{
  "version": "1.0",
  "project_key": "CUSTOMER_ANALYTICS",
  "last_applied": "2025-11-21T10:30:00Z",
  "config_hash": "sha256:abc123...",
  "resources": {
    "datasets": ["RAW_CUSTOMERS", "CLEAN_CUSTOMERS"],
    "recipes": ["clean_customers"],
    "scenarios": ["daily_refresh"]
  },
  "git_commit": "a1b2c3d4"
}
```

**Git Integration:**
- Every apply → git commit with message
- Rollback = git revert + re-apply previous config
- History = git log
- Diff = git diff

### C. Destructive Changes

**Dataiku-Native Pattern:**

| Action | Behavior | Data Impact |
|--------|----------|-------------|
| Remove from config | Delete dataset **definition** only | Data preserved |
| `--delete-data` flag | Delete dataset + data | Data destroyed |
| Update config | Update definition in-place | Data preserved |

**Example:**
```bash
# Safe: removes definition, keeps data
dss-framework apply customer_analytics.yaml

# Destructive: removes definition AND data
dss-framework apply customer_analytics.yaml --delete-data
```

**Framework tracks:**
- Created by framework = can delete
- Pre-existing = warn before deleting

### D. Connection Security

**Reference-Only Model:**

Config references connections by name, does not define credentials:

```yaml
datasets:
  - name: RAW_CUSTOMERS
    connection: snowflake_prod  # ← Reference only
    # No credentials, no host, no schema details
```

**Connection must exist in Dataiku:**
- Admin creates connection in Dataiku UI
- Framework validates connection exists
- Framework respects Dataiku permissions
- Users only see connections they have access to

**Validation:**
```python
# Framework checks connection exists
if not client.connection_exists("snowflake_prod"):
    raise ConnectionNotFoundError(
        "Connection 'snowflake_prod' not found. "
        "Create it in Dataiku first."
    )
```

### E. Code Storage

**Dual Support:**

**1. Inline (short recipes):**
```yaml
recipes:
  - name: simple_clean
    code: |
      df = dataiku.Dataset("input").get_dataframe()
      df = df.dropna()
      dataiku.Dataset("output").write_with_schema(df)
```

**2. External files (long recipes):**
```yaml
recipes:
  - name: complex_transform
    code_file: recipes/complex_transform.py
```

**File Resolution:**
- Relative to config file location
- Can use glob patterns: `code_files: recipes/*.py`
- Framework reads + validates before apply

---

## Component Details

### 1. Config Schema

**Models (Pydantic for validation):**

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class ProjectConfig(BaseModel):
    key: str = Field(..., regex=r'^[A-Z_][A-Z0-9_]*$')
    name: str
    description: Optional[str] = None
    owner: Optional[str] = None

class DatasetConfig(BaseModel):
    name: str = Field(..., regex=r'^[A-Z_][A-Z0-9_]*$')
    type: Literal['SQL', 'Filesystem', 'HTTP', ...]
    connection: str  # Reference to existing connection
    managed: bool = False
    params: dict = {}

class RecipeConfig(BaseModel):
    name: str
    type: Literal['python', 'sql', 'grouping', 'join', ...]
    inputs: List[str]
    outputs: List[str]
    code: Optional[str] = None
    code_file: Optional[str] = None
    params: dict = {}

class ScenarioConfig(BaseModel):
    name: str
    active: bool = True
    triggers: List[dict]
    steps: List[dict]

class FrameworkConfig(BaseModel):
    version: str = "1.0"
    project: ProjectConfig
    datasets: List[DatasetConfig] = []
    recipes: List[RecipeConfig] = []
    scenarios: List[ScenarioConfig] = []
```

**Validation:**
- Project key: uppercase, alphanumeric + underscore
- Dataset names: uppercase (Snowflake compatibility)
- Recipe dependencies: inputs/outputs exist
- No circular dependencies
- Code XOR code_file (not both)

### 2. State Management

**StateManager Class:**

```python
class StateManager:
    def __init__(self, client: DSSClient, project_key: str):
        self.client = client
        self.project_key = project_key
        self.state_path = f".dataiku_framework/state.json"

    def get_current_state(self) -> State:
        """Query Dataiku for actual state"""
        project = self.client.get_project(self.project_key)
        return State(
            datasets=[ds['name'] for ds in project.list_datasets()],
            recipes=[r['name'] for r in project.list_recipes()],
            scenarios=[s['name'] for s in project.list_scenarios()]
        )

    def get_desired_state(self, config: FrameworkConfig) -> State:
        """Extract state from config"""
        return State(
            datasets=[ds.name for ds in config.datasets],
            recipes=[r.name for r in config.recipes],
            scenarios=[s.name for s in config.scenarios]
        )

    def calculate_diff(self, current: State, desired: State) -> Diff:
        """Calculate what needs to change"""
        return Diff(
            create=desired - current,
            delete=current - desired,
            update=current & desired  # Exists in both, may need updates
        )

    def save_state(self, config: FrameworkConfig, commit_msg: str):
        """Save state to git"""
        project = self.client.get_project(self.project_key)

        # Save state file
        state = {
            "version": "1.0",
            "last_applied": datetime.now().isoformat(),
            "config_hash": hash_config(config),
            "resources": {...}
        }

        # Commit to git (if project has git enabled)
        project.write_file(self.state_path, json.dumps(state))
        # Git commit happens automatically in Dataiku
```

### 3. Execution Engine

**Engine Class:**

```python
class Engine:
    def __init__(self, host: str, api_key: str):
        self.client = DSSClient(host, api_key)
        self.state_manager = None

    def plan(self, config: FrameworkConfig) -> Plan:
        """Preview what will change (like terraform plan)"""
        self.state_manager = StateManager(self.client, config.project.key)

        current = self.state_manager.get_current_state()
        desired = self.state_manager.get_desired_state(config)
        diff = self.state_manager.calculate_diff(current, desired)

        return Plan(diff=diff, config=config)

    def apply(self, config: FrameworkConfig,
              auto_approve: bool = False,
              delete_data: bool = False) -> Result:
        """Execute changes"""
        plan = self.plan(config)

        if not auto_approve:
            print(plan.summary())
            if not confirm("Apply these changes?"):
                return Result(status="cancelled")

        # Execute in dependency order
        results = []

        # 1. Create/update project
        project_result = self._apply_project(config.project)
        results.append(project_result)

        # 2. Create/update datasets
        for dataset_config in config.datasets:
            result = self._apply_dataset(dataset_config)
            results.append(result)

        # 3. Create/update recipes (dependency order)
        for recipe_config in dependency_order(config.recipes):
            result = self._apply_recipe(recipe_config)
            results.append(result)

        # 4. Create/update scenarios
        for scenario_config in config.scenarios:
            result = self._apply_scenario(scenario_config)
            results.append(result)

        # 5. Handle deletions
        if plan.diff.delete:
            self._handle_deletions(plan.diff.delete, delete_data)

        # 6. Save state
        self.state_manager.save_state(config, "Applied configuration")

        return Result(status="success", results=results)

    def rollback(self, project_key: str, steps: int = 1):
        """Rollback to previous state"""
        # Use Dataiku git to revert
        project = self.client.get_project(project_key)

        # Read previous state from git history
        # Re-apply previous config
        pass
```

### 4. Builders

**DatasetBuilder Example:**

```python
class DatasetBuilder:
    def __init__(self, project: DSSProject):
        self.project = project

    def build_sql_dataset(self, config: DatasetConfig) -> DSSDataset:
        """Create or update SQL dataset"""

        # Check if exists
        if self._exists(config.name):
            return self._update(config)

        # Create new
        dataset = self.project.create_dataset(
            config.name,
            type="SQL",
            params={
                "connection": config.connection,
                "mode": config.params.get("mode", "table"),
                "schema": config.params.get("schema"),
                "table": config.params.get("table")
            }
        )

        return dataset

    def _exists(self, name: str) -> bool:
        try:
            self.project.get_dataset(name)
            return True
        except:
            return False

    def _update(self, config: DatasetConfig) -> DSSDataset:
        """Update existing dataset"""
        dataset = self.project.get_dataset(config.name)
        settings = dataset.get_settings()

        # Update settings from config
        settings.settings['params'] = config.params
        settings.save()

        return dataset
```

---

## File Structure

```
dataiku_framework/
├── __init__.py
├── ARCHITECTURE.md                 # This file
├── config/
│   ├── __init__.py
│   ├── schema.py                   # Pydantic models
│   ├── parser.py                   # YAML/JSON parsing
│   ├── validator.py                # Validation rules
│   └── examples/                   # Example configs
│       ├── simple_project.yaml
│       ├── snowflake_pipeline.yaml
│       └── ml_workflow.yaml
├── models/
│   ├── __init__.py
│   ├── state.py                    # State, Diff classes
│   ├── plan.py                     # Plan, Result classes
│   └── resource.py                 # Resource base class
├── builders/
│   ├── __init__.py
│   ├── base.py                     # BaseBuilder
│   ├── project.py                  # ProjectBuilder
│   ├── dataset.py                  # DatasetBuilder
│   ├── recipe.py                   # RecipeBuilder
│   └── scenario.py                 # ScenarioBuilder
├── engine/
│   ├── __init__.py
│   ├── engine.py                   # Engine class
│   ├── state_manager.py            # StateManager class
│   ├── executor.py                 # Execution logic
│   └── dependency.py               # Dependency resolution
├── client/
│   ├── __init__.py
│   └── wrapper.py                  # Enhanced DSSClient wrapper
├── cli/
│   ├── __init__.py
│   └── commands.py                 # CLI commands (plan/apply/etc.)
├── utils/
│   ├── __init__.py
│   ├── errors.py                   # Custom exceptions
│   ├── helpers.py                  # Utility functions
│   └── git.py                      # Git integration
└── tests/
    ├── __init__.py
    ├── test_config.py
    ├── test_state.py
    ├── test_builders.py
    └── fixtures/
        └── sample_configs/
```

---

## Usage Examples

### Example 1: AI Agent Generates Config

```python
# Claude Code generates this
from dataiku_framework import FrameworkConfig, Engine

# 1. AI translates natural language to config
config_dict = {
    "project": {
        "key": "CUSTOMER_ANALYTICS",
        "name": "Customer Analytics"
    },
    "datasets": [
        {
            "name": "RAW_CUSTOMERS",
            "type": "SQL",
            "connection": "snowflake_prod",
            "params": {"schema": "RAW", "table": "CUSTOMERS"}
        }
    ]
}

# 2. Validate
config = FrameworkConfig.from_dict(config_dict)

# 3. Show plan
engine = Engine(host, api_key)
plan = engine.plan(config)
print(plan.to_markdown())

# 4. Apply
result = engine.apply(config)
```

### Example 2: User Modifies YAML

```yaml
# User edits customer_analytics.yaml
project:
  key: CUSTOMER_ANALYTICS

datasets:
  - name: RAW_CUSTOMERS
    type: SQL
    connection: snowflake_prod

  # User adds new dataset
  - name: RAW_ORDERS
    type: SQL
    connection: snowflake_prod
```

```python
# Agent re-applies
config = FrameworkConfig.from_yaml("customer_analytics.yaml")
engine.apply(config)  # Only creates RAW_ORDERS (incremental)
```

### Example 3: Rollback

```python
# Something went wrong, rollback
engine.rollback(project_key="CUSTOMER_ANALYTICS", steps=1)
```

---

## Phase 1 Implementation Scope

**Focus:** Core functionality for projects, datasets, recipes

### Week 1: Foundation
- [ ] Config schema (Pydantic models)
- [ ] YAML/JSON parser
- [ ] Basic validation
- [ ] State management (without git)

### Week 2: Builders
- [ ] Project builder
- [ ] SQL dataset builder
- [ ] Filesystem dataset builder
- [ ] Python recipe builder
- [ ] Grouping recipe builder

### Week 3: Engine
- [ ] Plan calculation
- [ ] Apply execution
- [ ] Dependency resolution
- [ ] Error handling

### Week 4: Git Integration
- [ ] State storage in project git
- [ ] Commit on apply
- [ ] Rollback support
- [ ] Version tracking

---

## Success Criteria

Phase 1 complete when:

1. **AI can generate valid configs** from natural language
2. **Users can modify YAML** and re-apply incrementally
3. **State is tracked** in Dataiku project git
4. **Rollback works** to restore previous state
5. **Basic resources work**: Projects, SQL/Filesystem datasets, Python/Visual recipes

---

## Future Enhancements (Phase 2+)

- Scenario automation
- ML workflows
- Dashboard/webapp deployment
- Templates library (common patterns)
- Import existing projects to config
- Multi-project orchestration
- Terraform provider (integration)
- Web UI for config generation
- Plugin system

---

**Ready to build!** 🚀
