# Dataiku Framework - Projects as Code

**Status:** Phase 1 - Core Foundation (In Progress)
**Version:** 1.0.0-alpha
**Last Updated:** 2025-11-21

---

## Overview

Dataiku Framework is a **declarative, configuration-driven framework** for managing Dataiku projects. It enables AI agents (Claude Code, etc.) to translate natural language into Dataiku projects through YAML/JSON configuration files.

**Think:** Terraform for Dataiku - define infrastructure as code, version it with git, apply changes incrementally.

### Key Features

✅ **Declarative Configuration** - Define projects in YAML/JSON
✅ **AI-Friendly** - Designed for AI agent code generation
✅ **State Management** - Track desired vs. actual state
✅ **Dependency Resolution** - Automatic recipe execution ordering
✅ **Incremental Updates** - Modify config, re-apply only changes
✅ **Git-Backed Versioning** - Leverage Dataiku's git for rollback
✅ **Validation** - Catch errors before deployment

---

## Quick Example

**1. Define your project in YAML:**

```yaml
# customer_analytics.yaml
version: "1.0"

project:
  key: CUSTOMER_ANALYTICS
  name: "Customer Analytics Pipeline"

datasets:
  - name: RAW_CUSTOMERS
    type: SQL
    connection: snowflake_prod
    params:
      schema: RAW
      table: CUSTOMERS

  - name: CLEAN_CUSTOMERS
    type: Filesystem
    managed: true
    format_type: parquet

recipes:
  - name: clean_customers
    type: python
    inputs: [RAW_CUSTOMERS]
    outputs: [CLEAN_CUSTOMERS]
    code: |
      import dataiku
      df = dataiku.Dataset("RAW_CUSTOMERS").get_dataframe()
      df = df.dropna()
      dataiku.Dataset("CLEAN_CUSTOMERS").write_with_schema(df)

scenarios:
  - name: daily_refresh
    active: true
    triggers:
      - type: temporal
        frequency: daily
        hour: 2
        minute: 0
    steps:
      - type: build_flowitem
        items: [CLEAN_CUSTOMERS]
        build_mode: RECURSIVE
```

**2. Apply the configuration:**

```python
from dataiku_framework import FrameworkConfig, Engine

# Load config
config = FrameworkConfig.from_yaml("customer_analytics.yaml")

# Preview changes
engine = Engine(host="https://dss.company.com", api_key="your-key")
plan = engine.plan(config)
print(plan.to_markdown())

# Apply changes
result = engine.apply(config)
print(result.summary())
```

**3. Modify and re-apply:**

```yaml
# Update scenario to run at 3 AM
scenarios:
  - name: daily_refresh
    triggers:
      - type: temporal
        hour: 3  # Changed from 2
```

```python
# Re-apply - only updates scenario
config = FrameworkConfig.from_yaml("customer_analytics.yaml")
result = engine.apply(config)  # Only modifies scenario
```

---

## Architecture

```
Natural Language (User)
    ↓
AI Agent (Claude Code)
    ↓
YAML Config (Version Controlled)
    ↓
Framework (Parse, Validate, Plan)
    ↓
Dataiku API
    ↓
Dataiku DSS
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design documentation.

---

## Current Status - Phase 1

### ✅ Completed Components

#### 1. Configuration Schema (`config/schema.py`)
- Pydantic models for validation
- Support for Projects, Datasets, Recipes, Scenarios
- Dataset types: SQL, Filesystem, S3, Snowflake, BigQuery, etc.
- Recipe types: Python, SQL, R, Shell + Visual recipes (join, grouping, etc.)
- Scenario triggers: Temporal, Dataset, SQL, Manual
- Scenario steps: Build, Execute, Run

#### 2. Configuration Parser (`config/parser.py`)
- YAML and JSON parsing
- External file references (`code_file: recipes/clean.py`)
- Validation and error reporting
- Bidirectional conversion (load/save)

#### 3. State Management (`models/state.py`)
- `State` - Current/desired project state
- `Diff` - Changes between states
- `calculate_diff()` - Determines create/update/delete operations
- Markdown formatting for human review

#### 4. Execution Planning (`models/plan.py`)
- `Plan` - Preview of changes (like `terraform plan`)
- `Result` - Execution outcome
- `ResourceResult` - Per-resource status
- Success/failure tracking

#### 5. Dependency Resolution (`engine/dependency.py`)
- Topological sort for recipe ordering
- Circular dependency detection
- Execution group calculation (parallel execution support)
- Transitive dependency tracking

#### 6. Examples (`config/examples/`)
- `simple_project.yaml` - Basic ETL pipeline
- `snowflake_pipeline.yaml` - Complex multi-stage pipeline
- External code files (`recipes/*.py`)

### 🚧 In Progress Components

#### 7. State Manager (`engine/state_manager.py`) - **NEXT**
- Query Dataiku for current state
- Save state to project git
- Git integration for versioning
- Rollback support

#### 8. Builders (`builders/`) - **NEXT**
- `ProjectBuilder` - Create/update projects
- `DatasetBuilder` - SQL, Filesystem, managed datasets
- `RecipeBuilder` - Python, Visual recipes
- `ScenarioBuilder` - Scenarios and triggers

#### 9. Execution Engine (`engine/engine.py`) - **NEXT**
- `Engine.plan()` - Calculate changes
- `Engine.apply()` - Execute changes
- `Engine.rollback()` - Revert changes
- Error handling and retries

### 📋 Planned Components

#### 10. CLI (`cli/commands.py`)
- `dss-framework plan <config.yaml>`
- `dss-framework apply <config.yaml>`
- `dss-framework rollback <project-key>`
- `dss-framework validate <config.yaml>`

#### 11. Utilities (`utils/`)
- Error handling
- Logging
- Git helpers
- Connection validation

#### 12. Tests (`tests/`)
- Unit tests for all components
- Integration tests with mock Dataiku
- Example-based tests

---

## File Structure

```
dataiku_framework/
├── README.md                        # This file
├── ARCHITECTURE.md                  # Detailed architecture doc
├── __init__.py                      # Package exports
├── config/
│   ├── __init__.py
│   ├── schema.py                    # ✅ Pydantic models
│   ├── parser.py                    # ✅ YAML/JSON parser
│   └── examples/                    # ✅ Example configs
│       ├── simple_project.yaml
│       ├── snowflake_pipeline.yaml
│       └── recipes/
│           ├── clean_customers.py
│           ├── clean_orders.py
│           └── clean_products.py
├── models/
│   ├── __init__.py
│   ├── state.py                     # ✅ State, Diff
│   └── plan.py                      # ✅ Plan, Result
├── engine/
│   ├── __init__.py
│   ├── dependency.py                # ✅ Dependency resolver
│   ├── state_manager.py             # 🚧 State management
│   ├── engine.py                    # 🚧 Execution engine
│   └── executor.py                  # 📋 Execution logic
├── builders/
│   ├── __init__.py
│   ├── base.py                      # 📋 Base builder
│   ├── project.py                   # 📋 Project builder
│   ├── dataset.py                   # 📋 Dataset builder
│   ├── recipe.py                    # 📋 Recipe builder
│   └── scenario.py                  # 📋 Scenario builder
├── client/
│   ├── __init__.py
│   └── wrapper.py                   # 📋 Enhanced client
├── cli/
│   ├── __init__.py
│   └── commands.py                  # 📋 CLI commands
├── utils/
│   ├── __init__.py
│   ├── errors.py                    # 📋 Custom exceptions
│   ├── helpers.py                   # 📋 Utilities
│   └── git.py                       # 📋 Git integration
└── tests/
    ├── __init__.py
    ├── test_config.py               # 📋 Config tests
    ├── test_state.py                # 📋 State tests
    └── fixtures/                    # 📋 Test data
```

**Legend:** ✅ Complete | 🚧 In Progress | 📋 Planned

---

## Next Steps

### Immediate (This Week)

1. **Build StateManager** - Query Dataiku, save to git
2. **Build Builders** - Create/update resources
3. **Build Engine** - Plan and apply logic
4. **Write tests** - Validate core functionality

### Short-Term (Next 2 Weeks)

5. **Add scenario support** - Full automation
6. **CLI implementation** - Command-line tools
7. **Documentation** - Usage guides
8. **Examples** - More templates

### Medium-Term (Month 2)

9. **Advanced features** - ML workflows, dashboards
10. **Templates library** - Reusable patterns
11. **Import tool** - Existing projects → config
12. **Multi-project** - Orchestrate multiple projects

---

## Usage Patterns

### For AI Agents (Claude Code)

**Pattern 1: Generate from Natural Language**

```python
# User: "Create a sales analytics project with Snowflake"

# AI generates config
config_dict = {
    "project": {"key": "SALES_ANALYTICS", "name": "Sales Analytics"},
    "datasets": [
        {"name": "RAW_SALES", "type": "SQL", "connection": "snowflake_prod"}
    ],
    # ...
}

config = FrameworkConfig.from_dict(config_dict)
engine = Engine(host, api_key)
result = engine.apply(config)
```

**Pattern 2: Modify Existing Config**

```python
# User: "Change the scenario to run at 3 AM"

# AI loads existing config
config = FrameworkConfig.from_yaml("project.yaml")

# AI modifies
for scenario in config.scenarios:
    if scenario.name == "daily_refresh":
        scenario.triggers[0].hour = 3

# Save and apply
config.to_yaml("project.yaml")
engine.apply(config)
```

**Pattern 3: Iterative Refinement**

```python
# User: "Add a new dataset for product data"

# AI loads config
config = FrameworkConfig.from_yaml("project.yaml")

# AI adds dataset
from dataiku_framework.config.schema import DatasetConfig
new_dataset = DatasetConfig(
    name="RAW_PRODUCTS",
    type="SQL",
    connection="snowflake_prod",
    params={"schema": "RAW", "table": "PRODUCTS"}
)
config.datasets.append(new_dataset)

# Apply (only creates new dataset)
config.to_yaml("project.yaml")
result = engine.apply(config)
```

### For Developers

**Pattern 1: Programmatic API**

```python
from dataiku_framework import FrameworkConfig, ProjectConfig, DatasetConfig

# Build config programmatically
config = FrameworkConfig(
    project=ProjectConfig(key="MY_PROJECT", name="My Project"),
    datasets=[
        DatasetConfig(name="RAW_DATA", type="SQL", connection="postgres"),
        DatasetConfig(name="CLEAN_DATA", type="Filesystem", managed=True)
    ]
)

# Apply
engine = Engine(host, api_key)
result = engine.apply(config)
```

**Pattern 2: Template-Based**

```python
# Load template
template = FrameworkConfig.from_yaml("templates/snowflake_etl.yaml")

# Customize
template.project.key = "CUSTOM_PROJECT"
template.datasets[0].params["schema"] = "MY_SCHEMA"

# Apply
result = engine.apply(template)
```

---

## Design Decisions

### Why YAML?
- Human-readable (users can modify)
- AI-friendly (Claude generates clean YAML)
- Supports comments and multi-line strings
- Industry standard (Kubernetes, Ansible, Terraform)

### Why State Management?
- Enables incremental updates (only apply changes)
- Supports rollback (revert to previous state)
- Provides audit trail (git history)
- Prevents accidental deletions

### Why Dataiku-Native Patterns?
- Follows Dataiku conventions (uppercase names, connection references)
- Respects Dataiku permissions (users only see accessible connections)
- Leverages Dataiku features (git, managed datasets, scenarios)
- Matches Dataiku behavior (delete config, not data by default)

### Why Dependency Resolution?
- Ensures correct recipe execution order
- Prevents errors from missing inputs
- Enables parallel execution (future optimization)
- Validates configuration before deployment

---

## Contributing

This is currently in development. Next steps:

1. Complete StateManager implementation
2. Build core Builders
3. Implement Engine logic
4. Add comprehensive tests
5. Create CLI
6. Write documentation

---

## License

[To be determined]

---

## Contact

For questions or feedback, please [create an issue](https://github.com/hangtime79/dataiku-api-client-python/issues).

---

**Version:** 1.0.0-alpha
**Status:** Phase 1 - Core Foundation
**Next Milestone:** Complete StateManager + Builders (Week 1)
