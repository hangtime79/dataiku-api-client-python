# IaC Quick Start Guide

**Status:** 🚧 Experimental (Waves 1-3 Complete)
**Time to Complete:** 5 minutes
**Prerequisites:** Python 3.7+, Dataiku DSS instance

---

## What You'll Learn

In 5 minutes, you'll:
1. Create a simple YAML configuration
2. Validate your configuration
3. Generate a Terraform-style execution plan
4. Understand what IaC can do for you

---

## Step 1: Install the Package

```bash
# From the repository root
pip install -e .
```

---

## Step 2: Create Your First Config

Create a file named `my_first_project.yml`:

```yaml
version: "1.0"

project:
  key: MY_FIRST_PROJECT
  name: My First IaC Project
  description: Learning Dataiku IaC

datasets:
  - name: SAMPLE_DATA
    type: managed
    format_type: csv
```

**What this does:**
- Defines a new Dataiku project called "MY_FIRST_PROJECT"
- Creates one managed dataset named "SAMPLE_DATA" (CSV format)

---

## Step 3: Validate Your Config

Run the validation to catch errors before deployment:

```python
from dataikuapi.iac.config import ConfigParser, ConfigValidator

# Parse the config
parser = ConfigParser()
config = parser.parse_file("my_first_project.yml")

# Validate it
validator = ConfigValidator(strict=True)
try:
    validator.validate(config)
    print("✓ Config is valid!")
except Exception as e:
    print(f"✗ Validation failed: {e}")
```

**Expected output:**
```
✓ Config is valid!
```

---

## Step 4: Generate a Plan

See what changes would be made (Terraform-style):

```bash
python -m dataikuapi.iac.cli.plan -c my_first_project.yml -e dev
```

**Expected output:**
```
Dataiku IaC Execution Plan

The following actions will be performed:

+ project.MY_FIRST_PROJECT
    key: "MY_FIRST_PROJECT"
    name: "My First IaC Project"
    description: "Learning Dataiku IaC"

+ dataset.MY_FIRST_PROJECT.SAMPLE_DATA
    name: "SAMPLE_DATA"
    type: "managed"
    format_type: "csv"

Plan: 2 to create, 0 to update, 0 to destroy.
```

**Understanding the output:**
- `+` (green) = Resources to be created
- `~` (yellow) = Resources to be updated
- `-` (red) = Resources to be deleted
- `=` (gray) = No changes

---

## Step 5: Add a Recipe

Let's make it more interesting. Update your config to add a transformation:

```yaml
version: "1.0"

project:
  key: MY_FIRST_PROJECT
  name: My First IaC Project
  description: Learning Dataiku IaC

datasets:
  - name: SAMPLE_DATA
    type: managed
    format_type: csv

  - name: CLEANED_DATA
    type: managed
    format_type: parquet

recipes:
  - name: clean_sample_data
    type: python
    inputs: [SAMPLE_DATA]
    outputs: [CLEANED_DATA]
    code: |
      import dataiku
      import pandas as pd

      # Read input
      df = dataiku.Dataset("SAMPLE_DATA").get_dataframe()

      # Clean data
      df_clean = df.dropna()

      # Write output
      dataiku.Dataset("CLEANED_DATA").write_with_schema(df_clean)
```

Run the plan again:

```bash
python -m dataikuapi.iac.cli.plan -c my_first_project.yml -e dev
```

**New output:**
```
Dataiku IaC Execution Plan

The following actions will be performed:

+ project.MY_FIRST_PROJECT
    key: "MY_FIRST_PROJECT"
    name: "My First IaC Project"
    description: "Learning Dataiku IaC"

+ dataset.MY_FIRST_PROJECT.SAMPLE_DATA
    name: "SAMPLE_DATA"
    type: "managed"
    format_type: "csv"

+ dataset.MY_FIRST_PROJECT.CLEANED_DATA
    name: "CLEANED_DATA"
    type: "managed"
    format_type: "parquet"

+ recipe.MY_FIRST_PROJECT.clean_sample_data
    name: "clean_sample_data"
    type: "python"
    inputs: ["SAMPLE_DATA"]
    outputs: ["CLEANED_DATA"]

Plan: 4 to create, 0 to update, 0 to destroy.
```

---

## What's Working Now (Waves 1-3)

✅ **State Management**
- Track infrastructure state in JSON files
- Sync state from Dataiku instances
- Detect drift between desired and actual state

✅ **Plan Generation**
- Parse YAML configurations
- Validate configs (syntax, naming, references, dependencies)
- Generate Terraform-style execution plans
- Dependency-aware action ordering

✅ **Comprehensive Testing**
- 278+ tests with 98% pass rate
- Unit, integration, and scenario tests
- Real Dataiku instance integration tests

---

## What's Coming Next (Wave 4)

🚧 **Apply Execution** (In Progress)
- Execute plans to create/update/delete resources
- Rollback on failure
- Progress reporting
- Dry-run mode

📅 **Future Enhancements**
- State refresh from Dataiku
- Import existing projects to YAML
- Drift detection and reporting
- Remote state backends (S3, Git)
- CI/CD integration templates

---

## Next Steps

### Learn More
- **Full IaC Overview:** [`docs/IAC_OVERVIEW.md`](IAC_OVERVIEW.md)
- **Example Configs:** [`examples/iac/`](../examples/iac/)
- **Architecture & Design:** [`dataiku-iac-planning/README.md`](../dataiku-iac-planning/README.md)

### Try More Examples
- Simple project: [`examples/iac/simple-project.yml`](../examples/iac/simple-project.yml)
- ML pipeline: [`examples/iac/ml-pipeline.yml`](../examples/iac/ml-pipeline.yml)
- Multi-dataset: [`examples/iac/multi-dataset.yml`](../examples/iac/multi-dataset.yml)

### Working Demos
- State management: [`demos/week1_state_workflow.py`](../demos/week1_state_workflow.py)
- Plan workflow: [`demos/week2_plan_workflow.py`](../demos/week2_plan_workflow.py)

---

## Common Questions

**Q: Can I use this in production?**
A: Not yet. IaC is experimental. Wave 4 (apply execution) is needed for full workflow.

**Q: Why UPPERCASE for project keys and dataset names?**
A: Snowflake requires UPPERCASE for table and column names. Using UPPERCASE in Dataiku prevents case-sensitivity issues.

**Q: Can I use lowercase for recipe names?**
A: Yes! Recipe names use `lowercase_with_underscores` by convention.

**Q: What if I make a mistake in my YAML?**
A: The validator catches errors before deployment:
- Syntax errors (invalid YAML)
- Naming violations (lowercase where UPPERCASE required)
- Missing references (recipe inputs that don't exist)
- Circular dependencies
- Invalid resource types

**Q: How do I handle multiple environments (dev/staging/prod)?**
A: Use environment variables in your config:
```yaml
datasets:
  - name: SOURCE_DATA
    type: sql
    connection: "{{ env.DB_CONNECTION }}"
```
Then set different values per environment:
```bash
# Dev
export DB_CONNECTION=snowflake_dev
python -m dataikuapi.iac.cli.plan -c project.yml -e dev

# Prod
export DB_CONNECTION=snowflake_prod
python -m dataikuapi.iac.cli.plan -c project.yml -e prod
```

---

## Troubleshooting

### "Config validation failed: Project key must be UPPERCASE"
Use UPPERCASE with underscores: `MY_PROJECT` not `my_project`

### "Recipe references non-existent dataset"
All recipe inputs and outputs must be defined in the `datasets` section.

### "Circular dependency detected"
Check your recipe dependencies. Recipe A can't depend on Recipe B if Recipe B depends on Recipe A.

### "Cannot parse config file"
- Check YAML syntax (use a YAML validator)
- Ensure proper indentation (2 spaces, not tabs)
- Verify file exists and is readable

---

**Congratulations!** You've completed the IaC quick start. You now understand the basics of declarative infrastructure management for Dataiku.

**Version:** 1.0
**Last Updated:** 2025-11-27
**IaC Status:** Experimental (Waves 1-3 Complete)
