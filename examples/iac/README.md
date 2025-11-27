# IaC Configuration Examples

This directory contains example YAML configurations demonstrating various use cases for Dataiku IaC.

**Status:** 🚧 Experimental (Waves 1-3 Complete)

---

## Available Examples

### 1. Simple Project (`simple-project.yml`)

**Complexity:** ⭐ Beginner
**Resources:** 1 project, 1 dataset
**Best For:** Learning, testing, quick validation

The most minimal example - perfect for understanding the basic YAML structure.

```yaml
project:
  key: SIMPLE_PROJECT
  name: Simple Project

datasets:
  - name: SAMPLE_DATA
    type: managed
    format_type: csv
```

**Use Cases:**
- First-time IaC users learning the format
- Testing IaC installation
- Validating configuration syntax
- CI/CD smoke tests

**Try it:**
```bash
python -m dataikuapi.iac.cli.plan -c simple-project.yml -e dev
```

---

### 2. ML Pipeline (`ml-pipeline.yml`)

**Complexity:** ⭐⭐⭐ Intermediate
**Resources:** 1 project, 6 datasets, 4 recipes
**Best For:** Machine learning workflows, data science projects

A realistic ML pipeline for customer churn prediction:
- Load data from Snowflake
- Clean and prepare data
- Engineer features
- Split train/test sets
- Generate predictions

```yaml
project:
  key: CHURN_PREDICTION
  name: Customer Churn Prediction

datasets:
  - name: RAW_CUSTOMERS
    type: snowflake
    connection: "{{ env.DB_CONNECTION }}"
  - name: CLEANED_CUSTOMERS
    type: managed
    format_type: parquet
  # ... more datasets

recipes:
  - name: clean_customers
    type: python
    inputs: [RAW_CUSTOMERS]
    outputs: [CLEANED_CUSTOMERS]
  # ... more recipes
```

**Key Features:**
- External data source (Snowflake)
- Environment variables for connections
- Multiple transformation steps
- Python recipes with realistic code
- Schema definitions

**Use Cases:**
- ML model training pipelines
- Feature engineering workflows
- Customer analytics projects
- Data science team collaboration

**Try it:**
```bash
export DB_CONNECTION=snowflake_prod
python -m dataikuapi.iac.cli.plan -c ml-pipeline.yml -e prod
```

---

### 3. Multi-Dataset Pipeline (`multi-dataset.yml`)

**Complexity:** ⭐⭐⭐⭐ Advanced
**Resources:** 1 project, 9 datasets, 5 recipes
**Best For:** Data integration, ETL pipelines, multi-source analytics

A comprehensive data integration pipeline:
- Load from multiple sources (Snowflake, PostgreSQL, S3)
- Join and enrich data
- Compute aggregations
- Generate business metrics

```yaml
project:
  key: SALES_ANALYTICS
  name: Sales Analytics Pipeline

datasets:
  - name: SNOWFLAKE_CUSTOMERS
    type: snowflake
    connection: "{{ env.SNOWFLAKE_CONN }}"

  - name: POSTGRES_SALES
    type: postgresql
    connection: "{{ env.POSTGRES_CONN }}"

  - name: S3_PRODUCTS
    type: s3
    connection: "{{ env.S3_CONN }}"

  # ... intermediate and final datasets

recipes:
  - name: enrich_sales_with_customers
    type: sql
    inputs: [POSTGRES_SALES, SNOWFLAKE_CUSTOMERS]
    outputs: [ENRICHED_SALES]
  # ... more recipes
```

**Key Features:**
- Multiple data sources (Snowflake, PostgreSQL, S3)
- Complex dependency chains
- SQL and Python recipes
- Multi-step transformations
- Business metrics computation

**Use Cases:**
- Data warehouse ETL
- Multi-source data integration
- Business intelligence pipelines
- Cross-platform analytics
- Enterprise data consolidation

**Try it:**
```bash
export SNOWFLAKE_CONN=snowflake_prod
export POSTGRES_CONN=postgres_prod
export S3_CONN=s3_data_lake
python -m dataikuapi.iac.cli.plan -c multi-dataset.yml -e prod
```

---

## Common Patterns Demonstrated

### Environment Variables

All examples use environment variables for environment-specific configuration:

```yaml
datasets:
  - name: SOURCE_DATA
    type: snowflake
    connection: "{{ env.DB_CONNECTION }}"
```

**Dev environment:**
```bash
export DB_CONNECTION=snowflake_dev
python -m dataikuapi.iac.cli.plan -c config.yml -e dev
```

**Prod environment:**
```bash
export DB_CONNECTION=snowflake_prod
python -m dataikuapi.iac.cli.plan -c config.yml -e prod
```

### Schema Definitions

Define dataset schemas for validation and documentation:

```yaml
datasets:
  - name: CUSTOMER_DATA
    type: snowflake
    schema:
      columns:
        - name: CUSTOMER_ID
          type: bigint
        - name: EMAIL
          type: string
        - name: CREATED_AT
          type: timestamp
```

### Recipe Dependencies

Recipes automatically determine execution order based on inputs/outputs:

```yaml
recipes:
  - name: clean_data
    inputs: [RAW_DATA]
    outputs: [CLEAN_DATA]

  - name: compute_metrics
    inputs: [CLEAN_DATA]      # Depends on clean_data
    outputs: [METRICS]
```

IaC ensures `clean_data` runs before `compute_metrics`.

### Python vs SQL Recipes

**Python recipes** for complex transformations:
```yaml
recipes:
  - name: feature_engineering
    type: python
    inputs: [CLEAN_DATA]
    outputs: [FEATURES]
    code: |
      import dataiku
      import pandas as pd
      df = dataiku.Dataset("CLEAN_DATA").get_dataframe()
      # Complex transformations
      dataiku.Dataset("FEATURES").write_with_schema(df)
```

**SQL recipes** for aggregations and joins:
```yaml
recipes:
  - name: daily_aggregation
    type: sql
    inputs: [TRANSACTION_DATA]
    outputs: [DAILY_METRICS]
    code: |
      SELECT
        transaction_date,
        COUNT(*) as total_transactions,
        SUM(amount) as total_revenue
      FROM TRANSACTION_DATA
      GROUP BY transaction_date
```

---

## Quick Start Guide

### 1. Choose an Example

- **New to IaC?** Start with `simple-project.yml`
- **Building ML pipeline?** Use `ml-pipeline.yml`
- **Multi-source ETL?** Use `multi-dataset.yml`

### 2. Customize for Your Environment

Edit the YAML file:
- Update project key and name
- Change dataset names
- Modify connections (use your Dataiku connection names)
- Adjust recipe code

### 3. Validate Configuration

```bash
python -m dataikuapi.iac.cli.plan -c your-config.yml -e dev
```

### 4. Review the Plan

The plan shows what would be created:
- `+` (green) = Resources to create
- `~` (yellow) = Resources to update
- `-` (red) = Resources to delete

---

## Naming Conventions

All examples follow Dataiku IaC naming conventions:

| Resource | Convention | Example |
|----------|-----------|---------|
| Project Keys | UPPERCASE_WITH_UNDERSCORES | `CUSTOMER_ANALYTICS` |
| Dataset Names | UPPERCASE_WITH_UNDERSCORES | `RAW_CUSTOMERS` |
| Recipe Names | lowercase_with_underscores | `clean_customers` |

**Why UPPERCASE?**
- Snowflake requires UPPERCASE for tables/columns
- Prevents case-sensitivity issues
- Maintains SQL compatibility

---

## File Organization Patterns

### Single File (Simple Projects)

```
simple-project.yml
```

Good for small projects (< 10 resources).

### Directory Structure (Large Projects)

```
my-project/
├── project.yml          # Project metadata
├── datasets/
│   ├── sources.yml      # External data sources
│   ├── prepared.yml     # Prepared datasets
│   └── outputs.yml      # Final outputs
└── recipes/
    ├── cleaning.yml     # Data cleaning recipes
    ├── features.yml     # Feature engineering
    └── metrics.yml      # Metric computation
```

Good for large projects (10+ resources). Use `ConfigParser().parse_directory()`.

---

## Testing Your Configs

### Syntax Validation

```python
from dataikuapi.iac.config import ConfigParser, ConfigValidator

parser = ConfigParser()
config = parser.parse_file("your-config.yml")

validator = ConfigValidator(strict=True)
validator.validate(config)  # Raises exception if invalid
```

### Plan Generation

```bash
# See what would be created
python -m dataikuapi.iac.cli.plan -c your-config.yml -e dev
```

### Common Validation Errors

**Error:** "Project key must be UPPERCASE"
```yaml
# ❌ Wrong
project:
  key: my_project

# ✓ Correct
project:
  key: MY_PROJECT
```

**Error:** "Recipe references non-existent dataset"
```yaml
# ❌ Wrong - RAW_DATA not defined
recipes:
  - name: clean_data
    inputs: [RAW_DATA]

# ✓ Correct - RAW_DATA defined
datasets:
  - name: RAW_DATA
    type: managed

recipes:
  - name: clean_data
    inputs: [RAW_DATA]
```

**Error:** "Circular dependency detected"
```yaml
# ❌ Wrong - circular dependency
recipes:
  - name: recipe_a
    inputs: [DATASET_B]
    outputs: [DATASET_A]
  - name: recipe_b
    inputs: [DATASET_A]    # Circular!
    outputs: [DATASET_B]
```

---

## Next Steps

### Learn More
- **Quick Start:** [`../docs/IAC_QUICKSTART.md`](../docs/IAC_QUICKSTART.md)
- **Full Overview:** [`../docs/IAC_OVERVIEW.md`](../docs/IAC_OVERVIEW.md)
- **Planning Docs:** [`../dataiku-iac-planning/README.md`](../dataiku-iac-planning/README.md)

### Working Demos
- **State Management:** [`../demos/week1_state_workflow.py`](../demos/week1_state_workflow.py)
- **Plan Workflow:** [`../demos/week2_plan_workflow.py`](../demos/week2_plan_workflow.py)

### Build Your Own
1. Copy one of these examples
2. Customize for your project
3. Validate with `ConfigValidator`
4. Generate plan to preview changes
5. (Coming soon) Apply to deploy to Dataiku

---

## Status & Roadmap

### ✅ What Works Now (Waves 1-3)
- Parse YAML configurations
- Validate syntax, naming, references
- Generate execution plans
- Detect dependencies automatically

### 🚧 Coming Soon (Wave 4)
- Apply execution (actually create resources)
- Rollback on failure
- Progress reporting

### 📅 Future
- Import existing projects to YAML
- Drift detection
- Remote state backends
- CI/CD templates

---

**Questions or Issues?**
- Review [`../docs/TROUBLESHOOTING.md`](../docs/TROUBLESHOOTING.md)
- Check [`../docs/IAC_OVERVIEW.md`](../docs/IAC_OVERVIEW.md) FAQ section

**Version:** 1.0
**Last Updated:** 2025-11-27
**IaC Status:** Experimental (Waves 1-3 Complete)
