# JSON Schemas for Dataiku Reusable Workflows

This directory contains JSON Schema definitions for validating configuration files used in the Dataiku Reusable Workflows system.

## Schema Files

| Schema | Description | Used By |
|--------|-------------|---------|
| [`block-reference.schema.json`](block-reference.schema.json) | Block reference in IaC config | IaC Extension |
| [`block-manifest.schema.json`](block-manifest.schema.json) | Block manifest in registry | Discovery Agent |
| [`catalog-index.schema.json`](catalog-index.schema.json) | Catalog index file | Executing Agent |
| [`iac-config.schema.json`](iac-config.schema.json) | Complete IaC config with blocks | IaC Engine |

## Schema Relationships

```
iac-config.schema.json
    └── blocks: [block-reference.schema.json]  (references)

BLOCKS_REGISTRY/blocks/
    ├── index.json ─────────── catalog-index.schema.json
    └── manifests/
        └── BLOCK_v1.0.0.json ── block-manifest.schema.json
```

## Usage

### Validating Configuration Files

Using Python with `jsonschema`:

```python
import json
import jsonschema

# Load schema
with open("schemas/iac-config.schema.json") as f:
    schema = json.load(f)

# Load config
with open("my-project.yaml") as f:
    config = yaml.safe_load(f)

# Validate
jsonschema.validate(config, schema)
```

### IDE Integration

For VS Code, add to `.vscode/settings.json`:

```json
{
  "yaml.schemas": {
    "schemas/iac-config.schema.json": ["*.iac.yaml", "*.iac.yml"]
  }
}
```

### CLI Validation

Using `ajv-cli`:

```bash
npm install -g ajv-cli
ajv validate -s schemas/iac-config.schema.json -d my-project.yaml
```

## Schema Versions

All schemas use JSON Schema Draft-07.

| Schema | Current Version |
|--------|-----------------|
| block-reference | 1.0 |
| block-manifest | 1.0 |
| catalog-index | 1.0 |
| iac-config | 1.0 |

## Quick Reference

### Block Reference Format

```yaml
blocks:
  - ref: "REGISTRY/BLOCK_ID@VERSION"
    instance_name: my_instance
    zone_name: my_zone
    inputs:
      PORT_NAME: dataset_name
    outputs:
      PORT_NAME: dataset_name
    extends:
      - recipe: recipe_name
        override_with: custom_recipe
      - recipe: recipe_name
        use_class: module.ClassName
        class_config:
          key: value
```

### Block Manifest Structure

```json
{
  "block_id": "FEATURE_ENG",
  "version": "1.2.0",
  "type": "zone",
  "blocked": true,
  "name": "Feature Engineering",
  "hierarchy_level": "equipment",
  "domain": "rotating_equipment",
  "tags": ["feature", "engineering"],
  "source_project": "SOURCE_PROJECT",
  "inputs": [{"name": "RAW_DATA", "type": "dataset", "required": true}],
  "outputs": [{"name": "FEATURES", "type": "dataset"}],
  "contains": {
    "datasets": ["ds1", "ds2"],
    "recipes": ["recipe1", "recipe2"]
  }
}
```

### Catalog Index Structure

```json
{
  "format_version": "1.0",
  "updated_at": "2024-01-20T15:30:00Z",
  "blocks": [
    {
      "block_id": "FEATURE_ENG",
      "version": "1.2.0",
      "name": "Feature Engineering",
      "hierarchy_level": "equipment",
      "domain": "rotating_equipment",
      "inputs": [...],
      "outputs": [...],
      "manifest_path": "manifests/FEATURE_ENG_v1.2.0.json"
    }
  ]
}
```

## Validation Rules Summary

### Block Reference Rules
- `ref` must match pattern: `REGISTRY/BLOCK_ID@VERSION`
- `instance_name` and `zone_name` must be lowercase with underscores
- Extensions must have exactly one of `override_with` or `use_class`
- `use_class` must be fully qualified (contain at least one dot)

### Block Manifest Rules
- `block_id` must be UPPERCASE_WITH_UNDERSCORES
- `version` must be semantic versioning (X.Y.Z)
- `type` must be "zone" or "solution"
- `hierarchy_level` must be ISA-95 level (sensor/equipment/process/plant/business)

### IaC Config Rules
- `project.key` must be UPPERCASE_WITH_UNDERSCORES
- `version` must match pattern X.Y
- Block instance names must be unique

## Contributing

When modifying schemas:

1. Maintain backwards compatibility
2. Increment version in `$id` for breaking changes
3. Update examples in schema files
4. Update this README
5. Add migration notes if needed
