# IaC Block Extension

## Purpose

The IaC Block Extension adds block support to the existing Infrastructure as Code engine. It enables the IaC system to parse, validate, plan, and apply configurations that reference reusable blocks from BLOCKS_REGISTRY.

## What It Does

1. **Parses** block references in IaC configuration (`blocks:` section)
2. **Validates** block references, versions, and wiring compatibility
3. **Plans** block instantiation operations
4. **Applies** blocks by creating zones, copying recipes, and wiring connections
5. **Supports** block extensions (recipe overrides, class inheritance)

## Key Files

| File | Purpose |
|------|---------|
| [specification.md](specification.md) | Detailed requirements and integration points |
| [api-design.md](api-design.md) | Python interfaces and classes |
| [test-cases.md](test-cases.md) | TDD test definitions |

## Integration Points

This component integrates with existing IaC modules:

| Existing Module | Integration |
|-----------------|-------------|
| `dataikuapi/iac/config/parser.py` | Add `blocks:` section parsing |
| `dataikuapi/iac/config/validator.py` | Add block reference validation |
| `dataikuapi/iac/models/state.py` | Add `BLOCK` resource type |
| `dataikuapi/iac/planner/engine.py` | Add block operations to plans |
| `dataikuapi/iac/sync/` | Add `BlockSync` resource sync |

## Quick Reference

### Configuration Format

```yaml
version: "1.0"

project:
  key: NEW_PROJECT
  name: "New Project"

blocks:
  - ref: "BLOCKS_REGISTRY/FEATURE_ENG@1.2.0"
    instance_name: feature_instance
    zone_name: feature_zone
    inputs:
      RAW_DATA: source_sensors
    outputs:
      FEATURES: computed_features
    extends:
      - recipe: signal_smoothing
        override_with: custom_smoothing

datasets:
  - name: source_sensors
    type: sql_table
    connection: WAREHOUSE
    table: sensor_readings

recipes:
  - name: custom_smoothing
    type: python
    inputs: [RAW_DATA]
    outputs: [SMOOTHED_DATA]
    code_ref: lib/custom_smoothing.py
```

### Plan Output

```
Block Operations:
  + instantiate FEATURE_ENG@1.2.0 as feature_instance
    zone: feature_zone
    inputs:
      RAW_DATA → source_sensors
    outputs:
      FEATURES → computed_features
    extends:
      - recipe signal_smoothing → custom_smoothing

Dataset Operations:
  + create source_sensors (sql_table)

Recipe Operations:
  + create custom_smoothing (python)

Plan: 1 block to instantiate, 1 dataset to create, 1 recipe to create
```

## Implementation Location

When implementing, create/modify files at:
```
dataikuapi/iac/
├── config/
│   ├── parser.py           # MODIFY: Add blocks parsing
│   └── validator.py        # MODIFY: Add block validation
├── models/
│   ├── state.py            # MODIFY: Add BLOCK resource type
│   └── block.py            # NEW: Block config models
├── planner/
│   └── engine.py           # MODIFY: Add block planning
├── sync/
│   └── block.py            # NEW: BlockSync implementation
└── workflows/
    └── blocks/
        └── instantiator.py # NEW: Block instantiation logic
```

## Dependencies

- `dataikuapi.iac.config.parser` - Config parsing
- `dataikuapi.iac.config.validator` - Validation
- `dataikuapi.iac.planner.engine` - Plan generation
- `dataikuapi.iac.sync.base` - ResourceSync base class
- `dataikuapi.iac.workflows.executing` - Catalog access

## See Also

- [Existing IaC Documentation](../../dataiku-iac-planning/)
- [Architecture: Block Model](../../architecture/02-block-model.md)
- [Architecture: Inheritance](../../architecture/04-inheritance.md)
- [Discovery Agent](../discovery-agent/) - Creates blocks in registry
- [Executing Agent](../executing-agent/) - Generates configs with blocks
