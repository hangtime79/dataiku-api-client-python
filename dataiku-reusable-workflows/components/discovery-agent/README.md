# Discovery Agent

## Purpose

The Discovery Agent crawls a Dataiku project and inventories its components, writing a structured catalog to the BLOCKS_REGISTRY project. This catalog becomes the interface layer that other agents read.

## What It Does

1. **Crawls** a source project's flow (datasets, recipes, zones, models)
2. **Identifies** zones that could be reusable blocks
3. **Extracts** metadata (inputs, outputs, dependencies, schemas)
4. **Writes** structured Markdown to the Wiki
5. **Writes** JSON index to the project library
6. **Preserves** manual edits on re-crawl

## Key Files

| File | Purpose |
|------|---------|
| [specification.md](specification.md) | Detailed requirements and algorithms |
| [api-design.md](api-design.md) | Python interfaces and classes |
| [test-cases.md](test-cases.md) | TDD test definitions |

## Quick Reference

### Input
- Source project key
- Registry project key (default: BLOCKS_REGISTRY)
- Configuration options (hierarchy level, domain, tags, etc.)

### Output
- Wiki articles in BLOCKS_REGISTRY
- JSON index in BLOCKS_REGISTRY/Library
- Schema files in BLOCKS_REGISTRY/Library/blocks/schemas/

### Core Classes

```python
from dataikuapi.iac.workflows.discovery import DiscoveryAgent

agent = DiscoveryAgent(client, registry_project_key="BLOCKS_REGISTRY")
result = agent.discover_project(
    source_project_key="MY_PROJECT",
    config=DiscoveryConfig(
        hierarchy_level="equipment",
        domain="rotating_equipment",
        publish_all_zones=False
    )
)
```

## Implementation Location

When implementing, create files at:
```
dataikuapi/iac/workflows/discovery/
├── __init__.py
├── agent.py          # Main DiscoveryAgent class
├── crawler.py        # ProjectCrawler class
├── identifier.py     # BlockIdentifier class
├── extractor.py      # MetadataExtractor class
├── writer.py         # CatalogWriter class
└── models.py         # Data models
```

## Dependencies

- `dataikuapi.dss.project` - Project access
- `dataikuapi.dss.flow` - Flow graph traversal
- `dataikuapi.dss.wiki` - Wiki write
- `dataikuapi.dss.projectlibrary` - Library write

## See Also

- [Architecture: Block Model](../../architecture/02-block-model.md)
- [Architecture: Registry](../../architecture/03-registry.md)
