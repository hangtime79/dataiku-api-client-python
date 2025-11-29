# Registry Design Specification

## Overview

The **BLOCKS_REGISTRY** is a dedicated Dataiku project that serves as the central catalog in a **two-tier registry architecture**:

1. **Production Blocks**: Full content (wiki, schemas, manifests) for blocks explicitly published/promoted for reuse
2. **Project Registrations**: Links to project-local registries for cross-project discoverability while respecting Dataiku permissions

This design enables security-aware discovery where project-local registries inherit Dataiku project permissions, while the central BLOCKS_REGISTRY provides searchability across the organization.

---

## Registry Architecture

### BLOCKS_REGISTRY Structure

```
BLOCKS_REGISTRY (Dataiku Project)
│
├── Wiki/
│   ├── Home.md                          # Registry overview
│   │
│   ├── _CONFIG/
│   │   ├── hierarchy.md                 # Hierarchy level definitions
│   │   └── domains.md                   # Domain definitions
│   │
│   ├── _BLOCKS/                         # Production blocks (full content)
│   │   ├── _INDEX.md                    # Master block index (human)
│   │   │
│   │   ├── by-hierarchy/
│   │   │   ├── sensor/
│   │   │   │   └── *.md                 # Block articles
│   │   │   ├── equipment/
│   │   │   │   └── *.md
│   │   │   ├── process/
│   │   │   │   └── *.md
│   │   │   ├── plant/
│   │   │   │   └── *.md
│   │   │   └── business/
│   │   │       └── *.md
│   │   │
│   │   └── by-domain/
│   │       ├── rotating_equipment/
│   │       │   └── *.md
│   │       ├── process_control/
│   │       │   └── *.md
│   │       └── ...
│   │
│   ├── _PROJECT_REGISTRIES/            # NEW: Project links (references only)
│   │   ├── _INDEX.md                   # List of registered projects
│   │   ├── HR_ANALYTICS.md             # Link page for HR project
│   │   ├── PRODUCTION_ETL.md           # Link page for ETL project
│   │   └── ...                         # One page per registered project
│   │
│   └── _SOLUTIONS/
│       ├── _INDEX.md                   # Solution index
│       └── *.md                        # Solution articles
│
├── Library/
│   ├── blocks/                         # Production blocks
│   │   ├── index.json                  # Master index (machine)
│   │   ├── hierarchy_config.json       # Hierarchy definitions
│   │   ├── domain_config.json          # Domain definitions
│   │   │
│   │   ├── schemas/
│   │   │   ├── block_id/
│   │   │   │   ├── input_port.json
│   │   │   │   └── output_port.json
│   │   │   └── ...
│   │   │
│   │   └── manifests/
│   │       ├── BLOCK_ID_v1.0.0.json    # Version-specific manifests
│   │       └── ...
│   │
│   └── projects/                       # NEW: Project registrations
│       ├── project_index.json          # All registered projects
│       ├── HR_ANALYTICS.json           # Project metadata + block list
│       ├── PRODUCTION_ETL.json
│       └── ...                         # One JSON per registered project
│
└── Bundles/ (conceptual - stored via bundle API)
    ├── BLOCK_ID_v1.0.0.zip
    └── ...
```

### Project-Local Registry Structure

Each project with discovered blocks has its own local registry:

```
PROJECT_KEY (Dataiku Project)
│
├── Wiki/
│   └── _DISCOVERED_BLOCKS/
│       ├── _INDEX.md                    # Human-readable index
│       │
│       ├── by-hierarchy/
│       │   ├── sensor/
│       │   ├── equipment/
│       │   ├── process/
│       │   │   └── BLOCK_ID.md         # Full block documentation
│       │   ├── plant/
│       │   └── business/
│       │
│       └── by-domain/
│           └── {domain}/
│               └── BLOCK_ID.md         # Cross-reference
│
└── Library/
    └── discovery/
        ├── index.json                   # Machine-readable catalog
        ├── metadata.json                # Discovery run metadata
        └── schemas/
            └── BLOCK_ID/
                ├── INPUT_PORT.json
                └── OUTPUT_PORT.json
```

---

## Registry Setup

### Initial Creation

```python
def setup_blocks_registry(client: DSSClient, project_key: str = "BLOCKS_REGISTRY"):
    """
    Create and configure the BLOCKS_REGISTRY project.

    Args:
        client: Authenticated DSSClient
        project_key: Registry project key (default: BLOCKS_REGISTRY)

    Returns:
        DSSProject: The configured registry project
    """
    # Create project if not exists
    try:
        project = client.get_project(project_key)
    except:
        project = client.create_project(project_key, "Blocks Registry")

    # Initialize wiki structure
    wiki = project.get_wiki()

    # Create home page
    home = wiki.create_article("Home", content=HOME_TEMPLATE)

    # Create config section
    wiki.create_article("_CONFIG", parent_id=home.article_id)
    wiki.create_article("hierarchy", parent_id="_CONFIG", content=HIERARCHY_TEMPLATE)
    wiki.create_article("domains", parent_id="_CONFIG", content=DOMAINS_TEMPLATE)

    # Create blocks section
    wiki.create_article("_BLOCKS", parent_id=home.article_id)
    wiki.create_article("_INDEX", parent_id="_BLOCKS", content=BLOCKS_INDEX_TEMPLATE)
    wiki.create_article("by-hierarchy", parent_id="_BLOCKS")
    wiki.create_article("by-domain", parent_id="_BLOCKS")

    # Create solutions section
    wiki.create_article("_SOLUTIONS", parent_id=home.article_id)
    wiki.create_article("_INDEX", parent_id="_SOLUTIONS", content=SOLUTIONS_INDEX_TEMPLATE)

    # Initialize library structure
    library = project.get_library()
    library.add_folder("blocks")
    library.add_folder("blocks/schemas")
    library.add_folder("blocks/manifests")

    # Create initial index
    index_file = library.add_file("blocks/index.json")
    index_file.write(json.dumps(INITIAL_INDEX, indent=2))

    # Create hierarchy config
    hierarchy_file = library.add_file("blocks/hierarchy_config.json")
    hierarchy_file.write(json.dumps(DEFAULT_HIERARCHY, indent=2))

    # Create domain config
    domain_file = library.add_file("blocks/domain_config.json")
    domain_file.write(json.dumps(DEFAULT_DOMAINS, indent=2))

    return project
```

### Templates

```python
HOME_TEMPLATE = """
# Blocks Registry

Welcome to the centralized registry of reusable workflow blocks.

## Quick Links

- [Block Index](_BLOCKS/_INDEX) - All available blocks
- [Solution Index](_SOLUTIONS/_INDEX) - Multi-block solutions
- [Hierarchy Configuration](_CONFIG/hierarchy) - Hierarchy level definitions
- [Domain Configuration](_CONFIG/domains) - Domain definitions

## How to Use

### Finding Blocks

1. Browse by hierarchy level (sensor → equipment → process → plant → business)
2. Browse by domain (rotating_equipment, process_control, etc.)
3. Search by tags

### Using Blocks

Reference a block in your IaC configuration:

```yaml
blocks:
  - ref: "BLOCKS_REGISTRY/BLOCK_ID@VERSION"
    inputs:
      INPUT_PORT: your_dataset
    outputs:
      OUTPUT_PORT: your_output
```

### Publishing Blocks

Run the Discovery Agent on your project to publish blocks to this registry.
"""

INITIAL_INDEX = {
    "format_version": "1.0",
    "updated_at": None,
    "block_count": 0,
    "blocks": []
}

DEFAULT_HIERARCHY = {
    "levels": [
        {"name": "sensor", "order": 1, "description": "Raw signal processing"},
        {"name": "equipment", "order": 2, "description": "Equipment-level analytics"},
        {"name": "process", "order": 3, "description": "Process unit monitoring"},
        {"name": "plant", "order": 4, "description": "Plant-wide analytics"},
        {"name": "business", "order": 5, "description": "Cross-plant business metrics"}
    ]
}

DEFAULT_DOMAINS = {
    "domains": [
        {"name": "rotating_equipment", "description": "Pumps, compressors, turbines"},
        {"name": "process_control", "description": "Process control systems"},
        {"name": "predictive_maintenance", "description": "Failure prediction"},
        {"name": "quality_control", "description": "Product quality analytics"},
        {"name": "energy_optimization", "description": "Energy efficiency"}
    ]
}
```

---

## Registry Operations

### Operation 1: Register Block

```python
def register_block(
    registry: DSSProject,
    block_metadata: BlockMetadata,
    wiki_content: str,
    schemas: Dict[str, dict],
    bundle_path: Optional[str] = None
) -> str:
    """
    Register a new block or update existing block in the registry.

    Args:
        registry: BLOCKS_REGISTRY project
        block_metadata: Block metadata object
        wiki_content: Markdown content for Wiki article
        schemas: Dict of port_name -> schema dict
        bundle_path: Optional path to bundle file

    Returns:
        str: Block reference (e.g., "BLOCKS_REGISTRY/BLOCK_ID@1.0.0")
    """
    wiki = registry.get_wiki()
    library = registry.get_library()

    # 1. Create/update Wiki article
    article_path = f"_BLOCKS/by-hierarchy/{block_metadata.hierarchy_level}/{block_metadata.block_id}"
    try:
        article = wiki.get_article(article_path)
        article_data = article.get_data()
        article_data.set_body(wiki_content)
        article_data.save()
    except:
        # Create parent if needed
        parent = f"_BLOCKS/by-hierarchy/{block_metadata.hierarchy_level}"
        try:
            wiki.get_article(parent)
        except:
            wiki.create_article(block_metadata.hierarchy_level, parent_id="_BLOCKS/by-hierarchy")

        wiki.create_article(block_metadata.block_id, parent_id=parent, content=wiki_content)

    # 2. Also link in by-domain
    domain_path = f"_BLOCKS/by-domain/{block_metadata.domain}"
    # ... similar article creation/linking

    # 3. Store schemas
    for port_name, schema in schemas.items():
        schema_path = f"blocks/schemas/{block_metadata.block_id}/{port_name}.json"
        try:
            schema_file = library.get_file(schema_path)
        except:
            library.add_folder(f"blocks/schemas/{block_metadata.block_id}")
            schema_file = library.add_file(schema_path)
        schema_file.write(json.dumps(schema, indent=2))

    # 4. Store version manifest
    manifest = block_metadata.to_dict()
    manifest_path = f"blocks/manifests/{block_metadata.block_id}_v{block_metadata.version}.json"
    manifest_file = library.add_file(manifest_path)
    manifest_file.write(json.dumps(manifest, indent=2))

    # 5. Update master index
    update_master_index(registry, block_metadata)

    # 6. Handle bundle (if provided)
    if bundle_path:
        # Store bundle reference in metadata
        # Actual bundle stored via Dataiku bundle API
        pass

    return f"BLOCKS_REGISTRY/{block_metadata.block_id}@{block_metadata.version}"
```

### Operation 2: Read Block

```python
def get_block(
    registry: DSSProject,
    block_id: str,
    version: Optional[str] = None
) -> BlockMetadata:
    """
    Get block metadata from registry.

    Args:
        registry: BLOCKS_REGISTRY project
        block_id: Block identifier
        version: Specific version or None for latest

    Returns:
        BlockMetadata: Block metadata object

    Raises:
        BlockNotFoundError: If block doesn't exist
        VersionNotFoundError: If version doesn't exist
    """
    library = registry.get_library()

    # Read master index
    index_file = library.get_file("blocks/index.json")
    index = json.loads(index_file.read())

    # Find block
    block_entries = [b for b in index["blocks"] if b["block_id"] == block_id]
    if not block_entries:
        raise BlockNotFoundError(f"Block not found: {block_id}")

    # Find version
    if version is None or version == "latest":
        # Get latest version
        versions = [b["version"] for b in block_entries]
        version = max(versions, key=parse_semver)

    block_entry = next((b for b in block_entries if b["version"] == version), None)
    if not block_entry:
        available = [b["version"] for b in block_entries]
        raise VersionNotFoundError(f"Version {version} not found. Available: {available}")

    # Load full manifest
    manifest_path = f"blocks/manifests/{block_id}_v{version}.json"
    manifest_file = library.get_file(manifest_path)
    manifest = json.loads(manifest_file.read())

    return BlockMetadata.from_dict(manifest)
```

### Operation 3: Search Blocks

```python
def search_blocks(
    registry: DSSProject,
    hierarchy_level: Optional[str] = None,
    domain: Optional[str] = None,
    tags: Optional[List[str]] = None,
    blocked_only: bool = False,
    text_query: Optional[str] = None
) -> List[BlockSummary]:
    """
    Search for blocks in registry.

    Args:
        registry: BLOCKS_REGISTRY project
        hierarchy_level: Filter by hierarchy level
        domain: Filter by domain
        tags: Filter by tags (any match)
        blocked_only: Only return protected blocks
        text_query: Free-text search in name/description

    Returns:
        List[BlockSummary]: Matching blocks
    """
    library = registry.get_library()

    # Read master index
    index_file = library.get_file("blocks/index.json")
    index = json.loads(index_file.read())

    results = []
    for block in index["blocks"]:
        # Apply filters
        if hierarchy_level and block["hierarchy_level"] != hierarchy_level:
            continue
        if domain and block["domain"] != domain:
            continue
        if blocked_only and not block.get("blocked", False):
            continue
        if tags and not any(t in block.get("tags", []) for t in tags):
            continue
        if text_query:
            searchable = f"{block['block_id']} {block.get('name', '')} {block.get('description', '')}"
            if text_query.lower() not in searchable.lower():
                continue

        results.append(BlockSummary.from_dict(block))

    return results
```

### Operation 4: Update Master Index

```python
def update_master_index(registry: DSSProject, block_metadata: BlockMetadata):
    """
    Update the master JSON index with new/updated block.

    Maintains backward compatibility by:
    - Preserving manual additions
    - Merging rather than replacing

    Args:
        registry: BLOCKS_REGISTRY project
        block_metadata: Block to add/update
    """
    library = registry.get_library()

    # Read current index
    index_file = library.get_file("blocks/index.json")
    index = json.loads(index_file.read())

    # Find existing entry
    existing_idx = None
    for i, block in enumerate(index["blocks"]):
        if block["block_id"] == block_metadata.block_id and block["version"] == block_metadata.version:
            existing_idx = i
            break

    # Create summary entry
    summary = {
        "block_id": block_metadata.block_id,
        "version": block_metadata.version,
        "type": block_metadata.type,
        "blocked": block_metadata.blocked,
        "hierarchy_level": block_metadata.hierarchy_level,
        "domain": block_metadata.domain,
        "tags": block_metadata.tags,
        "name": block_metadata.name,
        "description": block_metadata.description[:200] if block_metadata.description else None,
        "inputs": [{"name": p.name, "type": p.type, "required": p.required} for p in block_metadata.inputs],
        "outputs": [{"name": p.name, "type": p.type} for p in block_metadata.outputs],
        "bundle_ref": block_metadata.bundle_ref,
        "wiki_ref": f"_BLOCKS/by-hierarchy/{block_metadata.hierarchy_level}/{block_metadata.block_id}.md"
    }

    # Update or append
    if existing_idx is not None:
        index["blocks"][existing_idx] = summary
    else:
        index["blocks"].append(summary)

    # Update metadata
    index["updated_at"] = datetime.utcnow().isoformat() + "Z"
    index["block_count"] = len(set(b["block_id"] for b in index["blocks"]))

    # Write back (atomic)
    temp_content = json.dumps(index, indent=2)
    index_file.write(temp_content)
```

---

## Project Registration Operations

### Operation 5: Register Project

```python
def register_project(
    registry: DSSProject,
    project_key: str,
    project_name: str,
    blocks: List[BlockMetadata]
) -> Dict[str, Any]:
    """
    Register a project in BLOCKS_REGISTRY with link entries.

    Creates:
    - Wiki article: _PROJECT_REGISTRIES/{project_key}.md
    - Project metadata: Library/projects/{project_key}.json
    - Updates Library/projects/project_index.json

    Does NOT replicate block content, only creates references.

    Args:
        registry: BLOCKS_REGISTRY project
        project_key: Source project key
        project_name: Source project name
        blocks: List of discovered blocks (for linking)

    Returns:
        {
            'project_registered': bool,
            'blocks_linked': int,
            'link_article_id': str
        }
    """
    wiki = registry.get_wiki()
    library = registry.get_library()

    # 1. Generate project link Wiki article
    article_content = generate_project_link_article(project_key, project_name, blocks)
    article_path = f"_PROJECT_REGISTRIES/{project_key}"

    try:
        article = wiki.get_article(article_path)
        article_data = article.get_data()
        article_data.set_body(article_content)
        article_data.save()
    except:
        # Create parent if needed
        try:
            wiki.get_article("_PROJECT_REGISTRIES")
        except:
            wiki.create_article("_PROJECT_REGISTRIES", parent_id="Home")

        article = wiki.create_article(project_key, parent_id="_PROJECT_REGISTRIES", content=article_content)

    # 2. Write project metadata JSON
    project_metadata = {
        "project_key": project_key,
        "project_name": project_name,
        "registered_at": datetime.utcnow().isoformat() + "Z",
        "last_discovered": datetime.utcnow().isoformat() + "Z",
        "discovery_runs": 1,
        "blocks_discovered": len(blocks),
        "blocks": [
            {
                "block_id": block.block_id,
                "version": block.version,
                "hierarchy_level": block.hierarchy_level,
                "domain": block.domain,
                "wiki_link": f"{project_key}/Wiki/_DISCOVERED_BLOCKS/by-hierarchy/{block.hierarchy_level}/{block.block_id}.md",
                "index_link": f"{project_key}/Library/discovery/index.json",
                "discovered_at": datetime.utcnow().isoformat() + "Z"
            }
            for block in blocks
        ]
    }

    metadata_path = f"projects/{project_key}.json"
    library.write_file(metadata_path, json.dumps(project_metadata, indent=2))

    # 3. Update project index
    update_project_index(registry, project_key, project_name, len(blocks))

    return {
        'project_registered': True,
        'blocks_linked': len(blocks),
        'link_article_id': article.article_id
    }


def generate_project_link_article(
    project_key: str,
    project_name: str,
    blocks: List[BlockMetadata]
) -> str:
    """
    Generate Wiki article for project registration.

    Format includes:
    - Project metadata (YAML frontmatter)
    - Access information
    - List of discovered blocks with links
    - Link to full discovery catalog
    """
    # Group blocks by hierarchy level
    by_hierarchy = {}
    for block in blocks:
        level = block.hierarchy_level or "other"
        if level not in by_hierarchy:
            by_hierarchy[level] = []
        by_hierarchy[level].append(block)

    # Generate article
    article = f"""---
project_key: {project_key}
project_name: {project_name}
registered_at: {datetime.utcnow().isoformat()}Z
last_discovered: {datetime.utcnow().isoformat()}Z
blocks_discovered: {len(blocks)}
---

# {project_name}

**Project Key:** `{project_key}`
**Last Discovery:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
**Blocks Discovered:** {len(blocks)}

## Access

This project's discoveries are subject to Dataiku project permissions.
You must have access to the {project_key} project to view block details.

## Discovered Blocks

"""

    # Add blocks by hierarchy
    for level in sorted(by_hierarchy.keys()):
        article += f"\n### {level.title()} Level\n\n"
        for block in sorted(by_hierarchy[level], key=lambda b: b.block_id):
            wiki_link = f"{project_key}/Wiki/_DISCOVERED_BLOCKS/by-hierarchy/{level}/{block.block_id}.md"
            article += f"- [{block.block_id}]({wiki_link}) - v{block.version}\n"

    article += f"""

## Discovery Details

View full discovery catalog:
- [Wiki Index]({project_key}/Wiki/_DISCOVERED_BLOCKS/_INDEX.md)
- [JSON Index]({project_key}/Library/discovery/index.json)
"""

    return article


def update_project_index(
    registry: DSSProject,
    project_key: str,
    project_name: str,
    blocks_discovered: int
):
    """
    Update Library/projects/project_index.json with new/updated project.

    Maintains list of all registered projects.
    """
    library = registry.get_library()

    # Read existing index
    try:
        index_content = library.read_file("projects/project_index.json")
        index = json.loads(index_content)
    except:
        index = {
            "format_version": "1.0",
            "updated_at": None,
            "project_count": 0,
            "projects": []
        }

    # Find existing project
    existing_idx = None
    for i, proj in enumerate(index["projects"]):
        if proj["project_key"] == project_key:
            existing_idx = i
            break

    # Create/update project entry
    project_entry = {
        "project_key": project_key,
        "project_name": project_name,
        "registered_at": datetime.utcnow().isoformat() + "Z",
        "last_discovered": datetime.utcnow().isoformat() + "Z",
        "blocks_discovered": blocks_discovered,
        "metadata_path": f"projects/{project_key}.json",
        "wiki_path": f"_PROJECT_REGISTRIES/{project_key}.md"
    }

    if existing_idx is not None:
        index["projects"][existing_idx] = project_entry
    else:
        index["projects"].append(project_entry)

    # Update metadata
    index["updated_at"] = datetime.utcnow().isoformat() + "Z"
    index["project_count"] = len(index["projects"])

    # Write back
    library.write_file("projects/project_index.json", json.dumps(index, indent=2))
```

### Operation 6: Get Registered Projects

```python
def get_registered_projects(registry: DSSProject) -> List[Dict[str, Any]]:
    """
    List all registered projects.

    Returns:
        List of project metadata dicts
    """
    library = registry.get_library()

    # Read project index
    index_content = library.read_file("projects/project_index.json")
    index = json.loads(index_content)

    return index["projects"]
```

---

## Hierarchy Configuration

Organizations can customize the hierarchy levels:

### Configuration Format

```json
{
  "levels": [
    {
      "name": "sensor",
      "order": 1,
      "description": "Raw signal processing and basic quality checks",
      "examples": ["Signal smoothing", "Outlier detection", "Unit conversion"]
    },
    {
      "name": "equipment",
      "order": 2,
      "description": "Equipment-level analytics and feature engineering",
      "examples": ["Compressor monitoring", "Pump analysis", "Motor diagnostics"]
    },
    {
      "name": "process",
      "order": 3,
      "description": "Process unit monitoring combining multiple equipment",
      "examples": ["Gas separation", "Distillation", "Reactor monitoring"]
    },
    {
      "name": "plant",
      "order": 4,
      "description": "Plant-wide analytics across process units",
      "examples": ["Plant efficiency", "Cross-unit optimization"]
    },
    {
      "name": "business",
      "order": 5,
      "description": "Cross-plant business metrics and portfolio analytics",
      "examples": ["Portfolio optimization", "Benchmarking", "KPI dashboards"]
    }
  ],
  "allow_custom": true,
  "default_level": "equipment"
}
```

### Alternative Hierarchies

Organizations can define entirely different taxonomies:

```json
{
  "levels": [
    {"name": "raw", "order": 1, "description": "Raw data processing"},
    {"name": "bronze", "order": 2, "description": "Cleaned, typed data"},
    {"name": "silver", "order": 3, "description": "Enriched, joined data"},
    {"name": "gold", "order": 4, "description": "Business-ready aggregates"}
  ]
}
```

---

## Domain Configuration

### Configuration Format

```json
{
  "domains": [
    {
      "name": "rotating_equipment",
      "description": "Pumps, compressors, turbines, motors",
      "keywords": ["vibration", "bearing", "rpm", "torque"]
    },
    {
      "name": "process_control",
      "description": "Process control and automation",
      "keywords": ["pid", "setpoint", "valve", "controller"]
    },
    {
      "name": "predictive_maintenance",
      "description": "Failure prediction and RUL estimation",
      "keywords": ["rul", "failure", "degradation", "health"]
    }
  ],
  "allow_custom": true
}
```

---

## Access Control

### Permission Model

| Role | Wiki Read | Wiki Write | Library Read | Library Write | Bundles |
|------|-----------|------------|--------------|---------------|---------|
| All Users | Yes | No | Yes | No | Download |
| Block Publishers | Yes | Yes (own blocks) | Yes | Yes (own schemas) | Upload |
| Registry Admins | Yes | Yes | Yes | Yes | Manage |

### Implementation

```python
def check_registry_permission(user: str, operation: str, block_id: Optional[str] = None) -> bool:
    """
    Check if user has permission for registry operation.

    Args:
        user: User login
        operation: "read" | "write" | "admin"
        block_id: Block being accessed (for write checks)

    Returns:
        bool: Permission granted
    """
    # Read is always allowed
    if operation == "read":
        return True

    # Get user's groups
    groups = get_user_groups(user)

    # Admin check
    if "registry_admins" in groups:
        return True

    # Write check - must be block owner or publisher
    if operation == "write":
        if "block_publishers" not in groups:
            return False
        if block_id:
            block = get_block_metadata(block_id)
            return block.created_by == user or user in block.allowed_editors

    return False
```

---

## Registry Maintenance

### Cleanup Operations

```python
def cleanup_registry(registry: DSSProject, dry_run: bool = True):
    """
    Clean up orphaned entries in registry.

    - Remove index entries without manifests
    - Remove manifests without wiki articles
    - Remove old versions (configurable retention)
    """
    pass

def rebuild_index(registry: DSSProject):
    """
    Rebuild master index from manifests.

    Use when index is corrupted or out of sync.
    """
    pass

def validate_registry(registry: DSSProject) -> List[ValidationError]:
    """
    Validate registry consistency.

    - All index entries have manifests
    - All manifests have wiki articles
    - All schemas are valid JSON
    - No orphaned bundles
    """
    pass
```

### Backup and Recovery

```python
def export_registry(registry: DSSProject, output_path: str):
    """
    Export entire registry for backup.

    Includes:
    - Master index
    - All manifests
    - All schemas
    - Wiki content (exported as markdown)
    """
    pass

def import_registry(client: DSSClient, input_path: str, project_key: str):
    """
    Import registry from backup.

    Creates new project if needed.
    """
    pass
```

---

## Integration Points

### With Discovery Agent

The Discovery Agent writes to the registry via:
1. `register_block()` - Add/update blocks
2. `update_master_index()` - Keep index current
3. Schema writes to Library

### With Executing Agent

The Executing Agent reads from the registry via:
1. `search_blocks()` - Find matching blocks
2. `get_block()` - Get full metadata
3. Schema reads from Library

### With IaC Engine

The IaC engine resolves block references via:
1. Parse `ref: "BLOCKS_REGISTRY/BLOCK_ID@VERSION"`
2. `get_block()` - Get block metadata
3. Download bundle (if needed) for instantiation
