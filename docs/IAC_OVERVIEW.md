# Infrastructure as Code (IaC) Overview

**Status:** 🚧 Experimental (Waves 1-3 Complete: State + Plan + Tests)
**Version:** 0.3.0 (Comprehensive Testing Complete)
**Target Users:** DevOps Engineers, Platform Teams, GitOps Practitioners

---

## What is Dataiku IaC?

**Dataiku IaC** is a declarative, Git-native infrastructure-as-code layer for managing Dataiku projects, datasets, recipes, and workflows. Think **Terraform for Dataiku** - define your desired state in YAML, version it in Git, and let the tool handle the deployment.

### The Problem It Solves

Enterprise DevOps teams are blocked from adopting Dataiku due to:

1. **No declarative IaC** - Everything is imperative, click-based, or script-based
2. **Poor CI/CD integration** - Manual processes, no GitOps workflows
3. **State management issues** - No HA on Automation nodes, no recovery from failures
4. **Lack of testing framework** - Can't validate configurations before deployment
5. **Manual environment management** - Connection remapping requires manual intervention

### The Solution

```yaml
# project.yml - Your entire project defined declaratively
version: "1.0"

project:
  key: CUSTOMER_ANALYTICS
  name: Customer Analytics
  description: Customer segmentation pipeline

datasets:
  - name: RAW_CUSTOMERS
    type: sql
    connection: snowflake_prod
    params:
      schema: PUBLIC
      table: customers

  - name: PREPARED_CUSTOMERS
    type: managed
    format_type: parquet

recipes:
  - name: prep_customers
    type: python
    inputs: [RAW_CUSTOMERS]
    outputs: [PREPARED_CUSTOMERS]
    code: |
      import dataiku
      df = dataiku.Dataset("RAW_CUSTOMERS").get_dataframe()
      df_clean = df.dropna()
      dataiku.Dataset("PREPARED_CUSTOMERS").write_with_schema(df_clean)
```

```bash
# Plan what will change (like Terraform plan)
python -m dataikuapi.iac.cli.plan -c project.yml -e prod

# Output:
# + project.CUSTOMER_ANALYTICS
# + dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS
# + dataset.CUSTOMER_ANALYTICS.PREPARED_CUSTOMERS
# + recipe.CUSTOMER_ANALYTICS.prep_customers
#
# Plan: 4 to create, 0 to update, 0 to destroy.

# Apply changes (coming in Wave 4)
# python -m dataikuapi.iac.cli.apply -c project.yml -e prod
```

---

## API Client vs IaC: When to Use Which?

### Use the **Python API Client** (Imperative) When:

✅ Writing automation scripts
✅ Building custom integrations
✅ Need programmatic control with loops, conditionals, dynamic logic
✅ Existing Python codebase
✅ One-off operations or maintenance tasks
✅ Complex orchestration requiring code

**Example:**
```python
# Imperative - You control HOW things happen
from dataikuapi import DSSClient

client = DSSClient(host, api_key)
project = client.get_project("MY_PROJECT")

# Dynamic logic based on runtime conditions
for dataset_name in get_datasets_from_somewhere():
    dataset = project.get_dataset(dataset_name)
    job = dataset.build(wait=True)
    if job.get_status()['state'] == 'FAILED':
        send_alert(dataset_name)
```

---

### Use **IaC** (Declarative) When:

✅ Managing infrastructure in Git (GitOps)
✅ Need reproducible deployments
✅ Multi-environment management (dev/staging/prod)
✅ Team collaboration with version control
✅ CI/CD pipelines
✅ Compliance and audit requirements
✅ Disaster recovery and environment rebuilds

**Example:**
```yaml
# Declarative - You define WHAT you want, tool figures out HOW
version: "1.0"

project:
  key: ANALYTICS
  name: Analytics

datasets:
  - name: SALES_DATA
    type: sql
    connection: "{{ env.DB_CONNECTION }}"

  - name: METRICS
    type: managed

recipes:
  - name: calculate_metrics
    type: python
    inputs: [SALES_DATA]
    outputs: [METRICS]
```

---

## Quick Comparison Table

| Feature | Python API Client | IaC (YAML) |
|---------|------------------|------------|
| **Style** | Imperative (HOW) | Declarative (WHAT) |
| **Use Case** | Scripts, automation | Infrastructure, GitOps |
| **Version Control** | Manual | Native Git integration |
| **State Management** | None | Built-in state tracking |
| **Plan/Preview** | No | Yes (Terraform-style) |
| **Rollback** | Manual | Git-based |
| **Environment Management** | Manual remapping | Templating + variables |
| **Learning Curve** | Python knowledge | YAML + IaC concepts |
| **Testing** | Manual | Built-in validation |
| **Team Collaboration** | Code sharing | Git workflows |
| **Current Status** | Production (stable) | Experimental (in progress) |

---

## IaC Capabilities Status

### ✅ Complete (Available Now)

#### Wave 1: State Management
- ✅ **State models** - Resource, State, StateMetadata
- ✅ **State backends** - Local file storage (JSON)
- ✅ **State sync** - ProjectSync, DatasetSync, RecipeSync
- ✅ **Diff engine** - Compare states, detect changes
- ✅ **State manager** - Save/load/sync orchestration
- **Test Coverage:** >90% (171 tests passing)

#### Wave 2: Plan Generation
- ✅ **Config parser** - YAML file/directory parsing
- ✅ **Config validator** - Syntax, naming, references, dependencies
- ✅ **Desired state builder** - Convert YAML to State objects
- ✅ **Plan generator** - Dependency-aware action ordering
- ✅ **Plan formatter** - Terraform-style output
- ✅ **CLI integration** - `python -m dataikuapi.iac.cli.plan`
- **Test Coverage:** 85% (107 tests passing)

#### Wave 3: Comprehensive Testing
- ✅ **Unit tests** - Individual component testing
- ✅ **Integration tests** - End-to-end workflow testing
- ✅ **Scenario tests** - Real-world use case testing
- ✅ **Real Dataiku tests** - Integration with actual DSS instances
- **Test Coverage:** 278+ tests, 98% pass rate

**Status:** Waves 1-3 complete. Plan generation fully functional.

---

### 🚧 Next Up (Wave 4)

#### Apply Execution
- ⏳ Apply engine with checkpointing
- ⏳ Resource creation/update/deletion via Dataiku API
- ⏳ Rollback on failure
- ⏳ Progress reporting
- ⏳ Dry-run mode
- ⏳ State update after successful apply

---

### 📅 Planned (Wave 5+)

#### Enhanced Workflow
- ⏳ State refresh from Dataiku
- ⏳ Import existing projects to YAML
- ⏳ Drift detection and reporting
- ⏳ State locking for team collaboration
- ⏳ Destroy command for cleanup

#### Future Phases
- ⏳ Additional resource types (scenarios, models, connections)
- ⏳ Remote state backends (S3, Git)
- ⏳ CI/CD integration templates (GitHub Actions, GitLab CI)
- ⏳ Govern approval workflows
- ⏳ Advanced templating (Jinja2, modules)
- ⏳ Testing framework for pipelines
- ⏳ Module system for reusable configs

---

## Quick Start with IaC

### 1. Create a YAML Config

```yaml
# my_project.yml
version: "1.0"

project:
  key: MY_PROJECT
  name: My First IaC Project
  description: Learning Dataiku IaC

datasets:
  - name: SAMPLE_DATA
    type: managed
    format_type: csv
```

### 2. Validate the Config

```python
from dataikuapi.iac.config import ConfigParser, ConfigValidator

parser = ConfigParser()
config = parser.parse_file("my_project.yml")

validator = ConfigValidator(strict=True)
try:
    validator.validate(config)
    print("✓ Config is valid")
except Exception as e:
    print(f"✗ Validation failed: {e}")
```

### 3. Generate a Plan

```bash
python -m dataikuapi.iac.cli.plan -c my_project.yml -e dev

# Output:
# Dataiku IaC Execution Plan
#
# + project.MY_PROJECT
#     name: "My First IaC Project"
#     description: "Learning Dataiku IaC"
#
# + dataset.MY_PROJECT.SAMPLE_DATA
#     name: "SAMPLE_DATA"
#     type: "managed"
#     format_type: "csv"
#
# Plan: 2 to create, 0 to update, 0 to destroy.
```

### 4. Apply Changes (Coming in Wave 4)

```bash
# Not yet available - Wave 4 deliverable
# python -m dataikuapi.iac.cli.apply -c my_project.yml -e dev
```

---

## IaC Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      User Workflow                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. Define Config (YAML)                                     │
│    project.yml, datasets/*.yml, recipes/*.yml               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Parse & Validate                                         │
│    ConfigParser → ConfigValidator                           │
│    ✓ Syntax  ✓ Naming  ✓ References  ✓ Dependencies       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Build Desired State                                      │
│    DesiredStateBuilder → State(resources=[...])             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Load Current State                                       │
│    StateManager.load() → State (from .state.json or Dataiku)│
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Generate Plan                                            │
│    PlanGenerator → ExecutionPlan                            │
│    (CREATE, UPDATE, DELETE actions with dependencies)       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Format Output                                            │
│    PlanFormatter → Terraform-style display                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Apply (Wave 4) 🚧                                        │
│    ApplyEngine → Execute actions → Update Dataiku           │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
dataiku-api-client-python/
├── dataikuapi/iac/              # IaC implementation
│   ├── models/                  # State, Resource, Diff models
│   ├── backends/                # State storage (local, future: S3, Git)
│   ├── sync/                    # Sync Dataiku → State
│   ├── config/                  # YAML parsing, validation
│   ├── planner/                 # Plan generation, formatting
│   ├── cli/                     # CLI commands (plan, apply)
│   ├── schemas/                 # JSON schemas for validation
│   ├── diff.py                  # State diffing engine
│   ├── manager.py               # StateManager orchestration
│   ├── validation.py            # Schema validation
│   └── exceptions.py            # Custom exceptions
│
├── dataiku-iac-planning/        # Planning & design docs
│   ├── README.md                # Planning overview
│   ├── architecture/            # System architecture
│   ├── design/                  # Design specifications
│   ├── api-specs/               # API specifications
│   ├── roadmap/                 # Implementation roadmap
│   ├── technical-specs/         # Week-by-week specs
│   └── examples/                # Example configs
│
├── demos/                       # Working demos
│   ├── week1_state_workflow.py  # State management demo
│   └── week2_plan_workflow.py   # Plan generation demo
│
└── tests/iac/                   # Comprehensive test suite
    ├── test_state_*.py          # State management tests (Week 1)
    ├── test_config_*.py         # Config tests (Week 2)
    ├── test_planner.py          # Planner tests (Week 2)
    └── test_integration_*.py    # Integration tests
```

---

## Documentation Navigation

### For IaC Users

**Start Here:**
1. **This document** - Understand IaC vs API, current status
2. [`dataiku-iac-planning/README.md`](../dataiku-iac-planning/README.md) - Full planning overview
3. [`dataiku-iac-planning/technical-specs/week-1-state-management.md`](../dataiku-iac-planning/technical-specs/week-1-state-management.md) - State management details
4. [`dataiku-iac-planning/technical-specs/week-2-plan-generation.md`](../dataiku-iac-planning/technical-specs/week-2-plan-generation.md) - Plan generation details
5. [`demos/week2_plan_workflow.py`](../demos/week2_plan_workflow.py) - Working example

**Architecture & Design:**
- [`dataiku-iac-planning/architecture/`](../dataiku-iac-planning/architecture/) - System architecture
- [`dataiku-iac-planning/design/01-config-format.md`](../dataiku-iac-planning/design/01-config-format.md) - YAML format spec
- [`WAVE_2_COMPLETION_REPORT.md`](../WAVE_2_COMPLETION_REPORT.md) - Week 1 completion
- [`WAVE_3_COMPLETION_REPORT.md`](../WAVE_3_COMPLETION_REPORT.md) - Week 2 completion

### For API Users

**Start Here:**
1. [`CLAUDE.md`](../CLAUDE.md) - Repository navigation hub
2. [`docs/QUICK_START.md`](QUICK_START.md) - 5-minute quick start
3. [`docs/PATTERNS.md`](PATTERNS.md) - Common code patterns
4. [`claude-guides/`](../claude-guides/) - Comprehensive workflow guides

---

## Key Concepts

### 1. State Management

**State** is the source of truth about your Dataiku infrastructure:

```json
{
  "version": "1.0",
  "environment": "prod",
  "resources": [
    {
      "id": "project.CUSTOMER_ANALYTICS",
      "type": "project",
      "name": "CUSTOMER_ANALYTICS",
      "attributes": {
        "name": "Customer Analytics",
        "description": "Customer segmentation pipeline"
      },
      "metadata": {
        "managed_by": "iac",
        "last_synced": "2025-11-26T10:30:00Z"
      }
    }
  ],
  "metadata": {
    "created_at": "2025-11-26T10:00:00Z",
    "updated_at": "2025-11-26T10:30:00Z"
  }
}
```

**State Backends:**
- Local file (`.state.json`) - Available now
- Git repository - Planned
- S3/GCS - Planned

### 2. Plan Workflow (Terraform-style)

```bash
# 1. Plan - Preview changes
python -m dataikuapi.iac.cli.plan -c project.yml -e prod

# Shows:
# + Resources to create (green)
# ~ Resources to update (yellow)
# - Resources to delete (red)
# = Resources unchanged (gray)

# 2. Apply - Execute changes (Week 3)
# python -m dataikuapi.iac.cli.apply -c project.yml -e prod

# 3. Destroy - Remove infrastructure (Future)
# python -m dataikuapi.iac.cli.destroy -c project.yml -e prod
```

### 3. Config Validation

Multi-level validation catches errors before deployment:

```yaml
# ❌ Invalid - lowercase project key (Snowflake incompatible)
project:
  key: customer_analytics  # Should be CUSTOMER_ANALYTICS

# ❌ Invalid - recipe references non-existent dataset
recipes:
  - name: process_data
    inputs: [MISSING_DATASET]  # Dataset not defined

# ❌ Invalid - circular dependency
recipes:
  - name: recipe_a
    inputs: [DATASET_B]
    outputs: [DATASET_A]
  - name: recipe_b
    inputs: [DATASET_A]  # Circular!
    outputs: [DATASET_B]
```

**Validation Levels:**
1. **Syntax** - Valid YAML structure
2. **Schema** - Matches JSON schema
3. **Naming** - UPPERCASE for Snowflake compatibility
4. **References** - All inputs/outputs exist
5. **Dependencies** - No circular dependencies

### 4. Dependency Ordering

IaC automatically orders operations based on dependencies:

```yaml
# You define resources in any order:
recipes:
  - name: final_output
    inputs: [PREPARED_DATA]
    outputs: [FINAL_DATA]

datasets:
  - name: FINAL_DATA
    type: managed

  - name: RAW_DATA
    type: sql

  - name: PREPARED_DATA
    type: managed

recipes:
  - name: prepare_data
    inputs: [RAW_DATA]
    outputs: [PREPARED_DATA]

# IaC executes in correct dependency order:
# 1. Create datasets: RAW_DATA, PREPARED_DATA, FINAL_DATA
# 2. Create recipe: prepare_data (after RAW_DATA, PREPARED_DATA exist)
# 3. Create recipe: final_output (after PREPARED_DATA, FINAL_DATA exist)
```

---

## Examples

### Basic Project

```yaml
version: "1.0"

project:
  key: HELLO_DATAIKU
  name: Hello Dataiku IaC
  description: My first IaC project

datasets:
  - name: SAMPLE_DATA
    type: managed
    format_type: csv
```

### SQL Dataset with Connection

```yaml
datasets:
  - name: CUSTOMER_DATA
    type: sql
    connection: snowflake_prod
    params:
      mode: table
      schema: PUBLIC
      table: customers
    schema:
      columns:
        - name: CUSTOMER_ID
          type: bigint
        - name: NAME
          type: string
        - name: EMAIL
          type: string
```

### Python Recipe

```yaml
recipes:
  - name: clean_data
    type: python
    inputs: [RAW_DATA]
    outputs: [CLEAN_DATA]
    code: |
      import dataiku
      import pandas as pd

      # Read input
      df = dataiku.Dataset("RAW_DATA").get_dataframe()

      # Clean data
      df_clean = df.dropna()
      df_clean = df_clean[df_clean['value'] > 0]

      # Write output
      dataiku.Dataset("CLEAN_DATA").write_with_schema(df_clean)
```

### Multi-Environment with Variables

```yaml
version: "1.0"

project:
  key: ANALYTICS
  name: Analytics Pipeline

datasets:
  - name: SOURCE_DATA
    type: sql
    connection: "{{ env.DB_CONNECTION }}"  # dev vs prod connection
    params:
      schema: "{{ env.DB_SCHEMA }}"        # Different schemas per env
      table: customers

  - name: PROCESSED_DATA
    type: managed
    format_type: parquet
```

```bash
# Dev environment
export DB_CONNECTION=snowflake_dev
export DB_SCHEMA=DEV_SCHEMA
python -m dataikuapi.iac.cli.plan -c project.yml -e dev

# Prod environment
export DB_CONNECTION=snowflake_prod
export DB_SCHEMA=PUBLIC
python -m dataikuapi.iac.cli.plan -c project.yml -e prod
```

---

## Migration from API to IaC

### Before (API Client)

```python
from dataikuapi import DSSClient

client = DSSClient(host, api_key)

# Create project
project = client.create_project("ANALYTICS", "Analytics", "admin")

# Create dataset
dataset = project.create_dataset("RAW_DATA", "managed")
settings = dataset.get_settings()
settings.settings['type'] = 'sql'
settings.settings['params']['connection'] = 'snowflake_prod'
settings.save()

# Create recipe
recipe = project.create_recipe("prepare_data", "python")
settings = recipe.get_settings()
settings.set_code("import dataiku\n...")
settings.save()

# Build
job = dataset.build(wait=True)
```

### After (IaC)

```yaml
# project.yml
version: "1.0"

project:
  key: ANALYTICS
  name: Analytics

datasets:
  - name: RAW_DATA
    type: sql
    connection: snowflake_prod

recipes:
  - name: prepare_data
    type: python
    inputs: [RAW_DATA]
    code: |
      import dataiku
      ...
```

```bash
# Plan and apply
python -m dataikuapi.iac.cli.plan -c project.yml -e prod
# python -m dataikuapi.iac.cli.apply -c project.yml -e prod  # Week 3
```

**Benefits:**
- ✅ Version controlled in Git
- ✅ Reproducible across environments
- ✅ Plan/preview before changes
- ✅ Easier to read and maintain
- ✅ Team collaboration via Git workflows

---

## Limitations & Gotchas

### Current Limitations (Wave 3)

1. **Apply not available** - Can plan but not execute (coming Wave 4)
2. **Limited resource types** - Only projects, datasets, recipes (scenarios/models coming in future waves)
3. **No remote state** - Local file only (S3/Git coming later)
4. **No state locking** - Team collaboration requires coordination
5. **No import** - Can't import existing projects to YAML yet
6. **No destroy** - Can't remove infrastructure yet

### Known Gotchas

1. **UPPERCASE naming required** - For Snowflake compatibility
   ```yaml
   # ❌ Wrong
   project:
     key: my_project

   # ✓ Correct
   project:
     key: MY_PROJECT
   ```

2. **State file location** - Defaults to `./.state.json`
   ```bash
   # Specify custom location
   python -m dataikuapi.iac.cli.plan -c project.yml --state-file custom.state.json
   ```

3. **Config vs State** - Don't confuse them
   - **Config (YAML)** = What you want (desired state)
   - **State (JSON)** = What exists (current state)

4. **Recipe names lowercase** - Convention for recipes
   ```yaml
   recipes:
     - name: prepare_data  # lowercase_with_underscores
   ```

---

## Getting Help

### Documentation
- **IaC Planning:** [`dataiku-iac-planning/README.md`](../dataiku-iac-planning/README.md)
- **API Client:** [`CLAUDE.md`](../CLAUDE.md)
- **Quick Start:** [`docs/QUICK_START.md`](QUICK_START.md)

### Examples
- **Working Demos:** `demos/week2_plan_workflow.py`
- **Test Examples:** `tests/iac/test_*.py`

### Status & Progress
- **Week 1 Report:** [`WAVE_2_COMPLETION_REPORT.md`](../WAVE_2_COMPLETION_REPORT.md)
- **Week 2 Report:** [`WAVE_3_COMPLETION_REPORT.md`](../WAVE_3_COMPLETION_REPORT.md)

---

## FAQ

**Q: Should I use IaC or the Python API?**
A: Use IaC for infrastructure management in Git (GitOps). Use API for scripts and automation with complex logic.

**Q: Can I use both together?**
A: Yes, but be careful. IaC manages state, so manual API changes can cause drift. Prefer one approach per resource.

**Q: Is IaC production-ready?**
A: Not yet (experimental). Wave 4 (apply) is needed for full workflow. Use for testing and development only.

**Q: When will apply be available?**
A: Wave 4 is being planned. See Wave 4 planning documents for details.

**Q: Can I import existing projects to YAML?**
A: Not yet. Coming in Week 4+ roadmap.

**Q: Does IaC support scenarios, models, ML?**
A: Not yet. Currently projects, datasets, recipes only. More resource types coming in future waves (Wave 5+).

**Q: How does state locking work for teams?**
A: Not implemented yet. For now, coordinate manually or use separate state files.

**Q: Can I use variables/templating?**
A: Basic templating with `{{ env.VAR }}` works. More advanced templating coming later.

---

**Version:** 1.1
**Last Updated:** 2025-11-27
**IaC Status:** Waves 1-3 Complete (State + Plan + Comprehensive Tests)
**Next Milestone:** Wave 4 (Apply Execution)
