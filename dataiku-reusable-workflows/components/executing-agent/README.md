# Executing Agent

## Purpose

The Executing Agent reads the block catalog from BLOCKS_REGISTRY and generates IaC configurations based on user intent. It matches available blocks to requirements and produces deployment-ready YAML configurations.

## What It Does

1. **Reads** the block catalog from BLOCKS_REGISTRY (Wiki + JSON index)
2. **Parses** user intent (structured query or natural language)
3. **Matches** intent to available blocks based on criteria
4. **Resolves** dependencies between matched blocks
5. **Generates** IaC configuration YAML for deployment
6. **Supports** filtering by hierarchy, domain, blocked status, tags

## Key Files

| File | Purpose |
|------|---------|
| [specification.md](specification.md) | Detailed requirements and algorithms |
| [api-design.md](api-design.md) | Python interfaces and classes |
| [test-cases.md](test-cases.md) | TDD test definitions |

## Quick Reference

### Input
- User intent (structured BlockQuery or natural language)
- Filter options (hierarchy, domain, blocked-only, tags)
- BLOCKS_REGISTRY project reference

### Output
- IaC configuration YAML
- Match results with confidence scores
- Wiring plan between blocks

### Core Classes

```python
from dataikuapi.iac.workflows.executing import ExecutingAgent, BlockQuery

agent = ExecutingAgent(client, registry_project_key="BLOCKS_REGISTRY")

# Structured query
result = agent.compose(
    query=BlockQuery(
        hierarchy_level="equipment",
        domain="rotating_equipment",
        capabilities=["feature_engineering", "anomaly_detection"],
        blocked_only=True
    ),
    target_project_key="NEW_PLANT_MONITORING"
)

# Generate config
config_yaml = result.to_yaml()
```

## Implementation Location

When implementing, create files at:
```
dataikuapi/iac/workflows/executing/
├── __init__.py
├── agent.py           # Main ExecutingAgent class
├── catalog.py         # CatalogReader class
├── matcher.py         # BlockMatcher class
├── resolver.py        # DependencyResolver class
├── generator.py       # ConfigGenerator class
├── intent.py          # IntentParser class
└── models.py          # Data models
```

## Dependencies

- `dataikuapi.dss.project` - Registry access
- `dataikuapi.dss.wiki` - Wiki read
- `dataikuapi.dss.projectlibrary` - Library read
- `dataikuapi.iac.workflows.discovery.models` - Shared block models

## See Also

- [Architecture: Block Model](../../architecture/02-block-model.md)
- [Architecture: Registry](../../architecture/03-registry.md)
- [Architecture: Solution Blocks](../../architecture/05-solution-blocks.md)
- [Discovery Agent](../discovery-agent/) - Creates the catalog this agent reads
