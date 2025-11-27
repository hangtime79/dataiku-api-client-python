# Dataiku Infrastructure as Code (IaC)

**Status:** 🚧 Experimental (Waves 1-3 Complete)
**Version:** 0.3.0

---

## What is Dataiku IaC?

Dataiku IaC brings **declarative, Git-native infrastructure management** to Dataiku DSS. Think **Terraform for Dataiku** - define your desired state in YAML, version it in Git, and let the tool handle deployment.

### The Problem

Enterprise DevOps teams are blocked from adopting Dataiku due to:
- No declarative IaC (everything is imperative or click-based)
- Poor CI/CD integration (manual processes, no GitOps)
- State management issues (no HA, no recovery from failures)
- Lack of testing framework (can't validate before deployment)

### The Solution

```yaml
# project.yml - Define WHAT you want, not HOW to create it
version: "1.0"

project:
  key: CUSTOMER_ANALYTICS
  name: Customer Analytics

datasets:
  - name: RAW_CUSTOMERS
    type: snowflake
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
# Plan what will change (Terraform-style)
python -m dataikuapi.iac.cli.plan -c project.yml -e prod

# Output:
# + project.CUSTOMER_ANALYTICS
# + dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS
# + dataset.CUSTOMER_ANALYTICS.PREPARED_CUSTOMERS
# + recipe.CUSTOMER_ANALYTICS.prep_customers
#
# Plan: 4 to create, 0 to update, 0 to destroy.
```

---

## Quick Start

### 1. Install

```bash
pip install -e .
```

### 2. Create a Config

```yaml
# my_project.yml
version: "1.0"

project:
  key: MY_PROJECT
  name: My First IaC Project

datasets:
  - name: SAMPLE_DATA
    type: managed
    format_type: csv
```

### 3. Validate

```python
from dataikuapi.iac.config import ConfigParser, ConfigValidator

parser = ConfigParser()
config = parser.parse_file("my_project.yml")

validator = ConfigValidator()
validator.validate(config)  # Raises exception if invalid
```

### 4. Generate Plan

```bash
python -m dataikuapi.iac.cli.plan -c my_project.yml -e dev
```

**Output:**
```
Dataiku IaC Execution Plan

+ project.MY_PROJECT
    name: "My First IaC Project"

+ dataset.MY_PROJECT.SAMPLE_DATA
    type: "managed"
    format_type: "csv"

Plan: 2 to create, 0 to update, 0 to destroy.
```

---

## Current Status (Waves 1-3 Complete)

### ✅ State Management (Wave 1)
- State models (Resource, State, StateMetadata)
- State backends (local file storage)
- State sync (ProjectSync, DatasetSync, RecipeSync)
- Diff engine (compare states, detect changes)
- **Test Coverage:** >90% (171 tests passing)

### ✅ Plan Generation (Wave 2)
- Config parser (YAML file/directory parsing)
- Config validator (syntax, naming, references, dependencies)
- Desired state builder (YAML → State objects)
- Plan generator (dependency-aware action ordering)
- Plan formatter (Terraform-style output)
- CLI integration (`python -m dataikuapi.iac.cli.plan`)
- **Test Coverage:** 85% (107 tests passing)

### ✅ Comprehensive Testing (Wave 3)
- Unit tests (individual components)
- Integration tests (end-to-end workflows)
- Scenario tests (real-world use cases)
- **Total:** 278+ tests, 98% pass rate

---

## Coming Soon

### 🚧 Wave 4: Apply Execution (In Progress)
- Apply engine with checkpointing
- Resource creation/update/deletion via Dataiku API
- Rollback on failure
- Progress reporting
- Dry-run mode

### 📅 Future Waves
- State refresh from Dataiku
- Import existing projects to YAML
- Drift detection and reporting
- State locking for team collaboration
- Remote state backends (S3, Git)
- CI/CD integration templates
- Govern approval workflows

---

## Architecture

### Directory Structure

```
dataikuapi/iac/
├── models/           # State, Resource, Diff models
├── backends/         # State storage (local, future: S3, Git)
├── sync/             # Sync Dataiku → State
├── config/           # YAML parsing, validation, state building
├── planner/          # Plan generation, formatting
├── cli/              # CLI commands (plan, apply)
├── schemas/          # JSON schemas for validation
├── diff.py           # State diffing engine
├── manager.py        # StateManager orchestration
├── validation.py     # Schema validation
└── exceptions.py     # Custom exceptions
```

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│ 1. User creates YAML config (project.yml)              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. ConfigParser → Parse YAML to Config objects         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. ConfigValidator → Validate (syntax, naming, refs)   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 4. DesiredStateBuilder → Config → State (desired)      │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 5. StateManager → Load current state from backend      │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 6. PlanGenerator → Generate ExecutionPlan from diff    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 7. PlanFormatter → Display Terraform-style plan        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 8. ApplyEngine → Execute plan (Wave 4) 🚧              │
└─────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. Declarative Configuration

Define **WHAT** you want, not **HOW** to create it:

```yaml
# You define the desired state
datasets:
  - name: CUSTOMER_DATA
    type: snowflake
    connection: prod

# IaC figures out:
# - Whether to create or update
# - Correct API calls
# - Dependency ordering
# - Error handling
```

### 2. Git-Native Workflow

```bash
# Make changes in YAML
vim project.yml

# See what would change
git diff project.yml
python -m dataikuapi.iac.cli.plan -c project.yml -e prod

# Commit and version
git add project.yml
git commit -m "Add customer analytics pipeline"
git push

# Deploy via CI/CD
# (apply coming in Wave 4)
```

### 3. Terraform-Style Plan/Apply

```bash
# Plan - Preview changes (safe, read-only)
python -m dataikuapi.iac.cli.plan -c project.yml -e prod

# Apply - Execute changes (coming in Wave 4)
# python -m dataikuapi.iac.cli.apply -c project.yml -e prod
```

### 4. Multi-Environment Support

```yaml
# Use environment variables
datasets:
  - name: SOURCE_DATA
    connection: "{{ env.DB_CONNECTION }}"
```

```bash
# Dev
export DB_CONNECTION=snowflake_dev
python -m dataikuapi.iac.cli.plan -c project.yml -e dev

# Prod
export DB_CONNECTION=snowflake_prod
python -m dataikuapi.iac.cli.plan -c project.yml -e prod
```

### 5. Comprehensive Validation

Multi-level validation catches errors before deployment:

```python
validator = ConfigValidator(strict=True)
validator.validate(config)

# Validates:
# ✓ YAML syntax
# ✓ Required fields
# ✓ Naming conventions (UPPERCASE for Snowflake)
# ✓ Reference integrity (recipe inputs exist)
# ✓ Circular dependencies
# ✓ Valid resource types
```

### 6. Dependency Management

Automatically orders operations based on dependencies:

```yaml
# You can define in any order
recipes:
  - name: final_metrics
    inputs: [PREPARED_DATA]
    outputs: [METRICS]

datasets:
  - name: METRICS
    type: managed

  - name: RAW_DATA
    type: sql

  - name: PREPARED_DATA
    type: managed

recipes:
  - name: prepare_data
    inputs: [RAW_DATA]
    outputs: [PREPARED_DATA]

# IaC executes in correct order:
# 1. Create datasets (RAW_DATA, PREPARED_DATA, METRICS)
# 2. Create prepare_data recipe (depends on RAW_DATA, PREPARED_DATA)
# 3. Create final_metrics recipe (depends on PREPARED_DATA, METRICS)
```

---

## Usage Examples

### Simple Project

```yaml
version: "1.0"

project:
  key: ANALYTICS
  name: Analytics Project

datasets:
  - name: DATA
    type: managed
    format_type: csv
```

### ML Pipeline

```yaml
version: "1.0"

project:
  key: CHURN_MODEL
  name: Churn Prediction

datasets:
  - name: RAW_CUSTOMERS
    type: snowflake
    connection: "{{ env.DB_CONN }}"

  - name: FEATURES
    type: managed
    format_type: parquet

  - name: PREDICTIONS
    type: managed
    format_type: parquet

recipes:
  - name: engineer_features
    type: python
    inputs: [RAW_CUSTOMERS]
    outputs: [FEATURES]
    code: |
      import dataiku
      # Feature engineering code

  - name: predict
    type: python
    inputs: [FEATURES]
    outputs: [PREDICTIONS]
    code: |
      import dataiku
      # Prediction code
```

**More examples:** [`../../examples/iac/`](../../examples/iac/)

---

## API Reference

### ConfigParser

```python
from dataikuapi.iac.config import ConfigParser

parser = ConfigParser()

# Parse single file
config = parser.parse_file("project.yml")

# Parse directory (project.yml + datasets/*.yml + recipes/*.yml)
config = parser.parse_directory("config/")
```

### ConfigValidator

```python
from dataikuapi.iac.config import ConfigValidator

validator = ConfigValidator(strict=True)

try:
    validator.validate(config)
    print("✓ Valid")
except ConfigValidationError as e:
    print(f"✗ Validation failed: {e}")
    for error in e.errors:
        print(f"  - {error.path}: {error.message}")
```

### DesiredStateBuilder

```python
from dataikuapi.iac.config import DesiredStateBuilder

builder = DesiredStateBuilder(environment="prod")
desired_state = builder.build(config)

print(f"Resources: {len(desired_state.resources)}")
for resource in desired_state.resources.values():
    print(f"  - {resource.resource_id}")
```

### PlanGenerator

```python
from dataikuapi.iac.planner import PlanGenerator

planner = PlanGenerator()
plan = planner.generate_plan(current_state, desired_state)

print(f"Actions: {len(plan.actions)}")
for action in plan.actions:
    print(f"  {action.action_type}: {action.resource.resource_id}")
```

### PlanFormatter

```python
from dataikuapi.iac.planner import PlanFormatter

formatter = PlanFormatter(color=True)
formatter.format(plan)  # Prints Terraform-style output
```

---

## Documentation

### Getting Started
- **Quick Start:** [`../../docs/IAC_QUICKSTART.md`](../../docs/IAC_QUICKSTART.md) - 5-minute guide
- **Overview:** [`../../docs/IAC_OVERVIEW.md`](../../docs/IAC_OVERVIEW.md) - Full IaC overview
- **Examples:** [`../../examples/iac/`](../../examples/iac/) - Sample configurations

### Architecture & Design
- **Planning Docs:** [`../../dataiku-iac-planning/README.md`](../../dataiku-iac-planning/README.md)
- **Architecture:** [`../../dataiku-iac-planning/architecture/`](../../dataiku-iac-planning/architecture/)
- **Design Specs:** [`../../dataiku-iac-planning/design/`](../../dataiku-iac-planning/design/)

### Implementation Details
- **Week 1 Spec:** [`../../dataiku-iac-planning/technical-specs/week-1-state-management.md`](../../dataiku-iac-planning/technical-specs/week-1-state-management.md)
- **Week 2 Spec:** [`../../dataiku-iac-planning/technical-specs/week-2-plan-generation.md`](../../dataiku-iac-planning/technical-specs/week-2-plan-generation.md)
- **Wave 2 Report:** [`../../WAVE_2_COMPLETION_REPORT.md`](../../WAVE_2_COMPLETION_REPORT.md)
- **Wave 3 Report:** [`../../WAVE_3_COMPLETION_REPORT.md`](../../WAVE_3_COMPLETION_REPORT.md)

### Working Demos
- **State Management:** [`../../demos/week1_state_workflow.py`](../../demos/week1_state_workflow.py)
- **Plan Workflow:** [`../../demos/week2_plan_workflow.py`](../../demos/week2_plan_workflow.py)

---

## Testing

Comprehensive test suite with 278+ tests:

```bash
# Run all IaC tests
pytest tests/iac/

# Run specific test categories
pytest tests/iac/unit/          # Unit tests
pytest tests/iac/integration/   # Integration tests
pytest tests/iac/scenarios/     # Scenario tests

# Run with coverage
pytest tests/iac/ --cov=dataikuapi.iac --cov-report=html
```

---

## Contributing

### Development Setup

```bash
# Clone repository
git clone <repo-url>
cd dataiku-api-client-python

# Install in editable mode
pip install -e .

# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/iac/
```

### Code Structure

- **models/**: Data models (State, Resource, Diff)
- **backends/**: State storage backends
- **sync/**: Sync Dataiku → State
- **config/**: YAML parsing, validation, state building
- **planner/**: Plan generation and formatting
- **cli/**: Command-line interface

### Adding a New Resource Type

1. Add resource schema to `schemas/config_v1.schema.json`
2. Add config model to `config/models.py`
3. Add state builder logic to `config/builder.py`
4. Add tests to `tests/iac/`

---

## Limitations & Gotchas

### Current Limitations (Wave 3)

1. **Apply not available** - Can plan but not execute (coming Wave 4)
2. **Limited resource types** - Only projects, datasets, recipes
3. **No remote state** - Local file only
4. **No state locking** - Team coordination required
5. **No import** - Can't import existing projects yet

### Known Gotchas

1. **UPPERCASE required** - For Snowflake compatibility
   ```yaml
   # ❌ Wrong
   project:
     key: my_project

   # ✓ Correct
   project:
     key: MY_PROJECT
   ```

2. **Recipe names lowercase** - By convention
   ```yaml
   recipes:
     - name: prepare_data  # lowercase_with_underscores
   ```

3. **All recipe inputs must exist**
   ```yaml
   # ❌ Wrong - RAW_DATA not defined
   recipes:
     - name: clean
       inputs: [RAW_DATA]

   # ✓ Correct
   datasets:
     - name: RAW_DATA
       type: managed

   recipes:
     - name: clean
       inputs: [RAW_DATA]
   ```

---

## FAQ

**Q: Is this production-ready?**
A: Not yet. Experimental. Wave 4 (apply) needed for full workflow.

**Q: Can I use both IaC and the Python API?**
A: Yes, but be careful. IaC manages state, so manual API changes cause drift.

**Q: What resource types are supported?**
A: Currently: projects, datasets, recipes. More coming in future waves.

**Q: How do I handle secrets/credentials?**
A: Use environment variables: `{{ env.SECRET_NAME }}`. Never commit secrets to Git.

**Q: Can I import existing projects?**
A: Not yet. Coming in future wave.

---

**Version:** 0.3.0
**Last Updated:** 2025-11-27
**Status:** Experimental (Waves 1-3 Complete)
**Next Milestone:** Wave 4 (Apply Execution)
