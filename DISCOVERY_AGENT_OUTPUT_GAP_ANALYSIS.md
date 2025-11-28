# Discovery Agent Output Gap Analysis

**Date:** 2025-11-28
**Status:** ⚠️ **CRITICAL GAP IDENTIFIED**

---

## Executive Summary

The Discovery Agent is **functionally complete** for discovery workflows but **missing critical output persistence** required for the Executor Agent to consume results.

**Current State:**
- ✅ Discovers blocks from projects
- ✅ Validates blocks
- ✅ Extracts metadata
- ✅ Enriches with schemas
- ✅ **Generates** catalog content (wiki, JSON, schemas)
- ❌ **Does NOT write** catalog content to disk/Dataiku

**Impact:**
- Executor Agent **cannot** consume Discovery Agent results
- Blocks are identified but not persisted to BLOCKS_REGISTRY
- Manual intervention required to use discovered blocks

---

## What's Implemented (Current State)

### ✅ Discovery Pipeline (Complete)

**4-Step Workflow:**
1. **Crawl Project** - ✅ Lists zones, builds dependency graph
2. **Identify Blocks** - ✅ Validates zones, extracts metadata
3. **Enrich Schemas** - ✅ Adds dataset schemas to block metadata
4. **Generate Catalog** - ✅ Creates wiki articles, JSON summaries, schema refs

**Output Format (In-Memory):**
```python
results = {
    "project_key": "COALSHIPPINGSIMULATIONGSC",
    "blocks_found": 7,
    "blocks_cataloged": 0,  # Always 0 because no actual writes!
    "blocks": [
        BlockMetadata(
            block_id="NEW_SIM",
            version="1.0.0",
            inputs=[...],
            outputs=[...],
            # ... full metadata
        ),
        # ... more blocks
    ],
    "dry_run": False
}
```

**Catalog Entry Generation (In-Memory):**
```python
catalog_entry = {
    "wiki_article": "# Block Name\n\n## Description\n...",  # Markdown string
    "summary": '{"block_id": "...", "version": "..."}',     # JSON string
    "wiki_path": "BLOCKS_REGISTRY/process/BLOCK_ID"        # Path string
}
```

### ❌ Catalog Persistence (Missing)

**What's NOT Implemented:**
- No file system writes
- No Dataiku Wiki API writes
- No Dataiku Library writes
- No index.json updates
- No BLOCKS_REGISTRY project creation

**Current CatalogWriter Methods:**
```python
class CatalogWriter:
    def generate_wiki_article(metadata) -> str:
        # ✅ Generates markdown content

    def generate_block_summary(metadata) -> str:
        # ✅ Generates JSON summary

    def get_wiki_path(metadata) -> str:
        # ✅ Determines wiki article path

    def merge_catalog_index(existing, metadata) -> dict:
        # ✅ Merges index data structures

    # ❌ MISSING: No write_catalog() method
    # ❌ MISSING: No _write_wiki_article() method
    # ❌ MISSING: No _write_schemas() method
    # ❌ MISSING: No _update_index() method
```

---

## What's Required (Per Specification)

### 📋 Specification Requirements

From `dataiku-reusable-workflows/components/discovery-agent/specification.md`:

**CatalogWriter Should Have:**

```python
class CatalogWriter:
    def __init__(self, client: DSSClient, registry_key: str = "BLOCKS_REGISTRY"):
        """Initialize with client and registry project key."""

    def write_catalog(self, blocks: List[BlockMetadata]) -> CatalogWriteResult:
        """
        Write all blocks to registry.

        Steps:
        1. Ensure registry exists and is initialized
        2. For each block:
           a. Write wiki article
           b. Write schema files
           c. Update index
        3. Return results
        """

    def _ensure_registry_exists(self) -> DSSProject:
        """Create registry if it doesn't exist."""

    def _write_wiki_article(self, block: BlockMetadata, wiki: DSSWiki) -> bool:
        """
        Write single wiki article.

        Steps:
        1. Generate article content
        2. Determine article path (by-hierarchy)
        3. Create or update article
        4. Also link in by-domain
        """

    def _write_schemas(self, block: BlockMetadata, library: DSSProjectLibrary):
        """Write schema files to library."""

    def _update_index(self, blocks: List[BlockMetadata], library: DSSProjectLibrary):
        """
        Update master index.json.

        Steps:
        1. Read existing index
        2. Merge with new blocks
        3. Write updated index
        """
```

**Expected Output Structure in BLOCKS_REGISTRY:**

```
BLOCKS_REGISTRY (Dataiku Project)
├── Wiki
│   ├── by-hierarchy/
│   │   ├── sensor/
│   │   ├── equipment/
│   │   ├── process/
│   │   │   └── NEW_SIM.md              # Wiki article for block
│   │   ├── plant/
│   │   └── business/
│   └── by-domain/
│       ├── analytics/
│       ├── ml/
│       └── etl/
└── Library
    ├── index.json                       # Master catalog index
    └── schemas/
        ├── NEW_SIM_input1.schema.json   # Input dataset schema
        └── NEW_SIM_output1.schema.json  # Output dataset schema
```

---

## Gap Analysis

### Critical Gaps (Blocking Executor Agent)

| Feature | Status | Impact |
|---------|--------|--------|
| **Write wiki articles** | ❌ Missing | Executor can't read block documentation |
| **Write schema files** | ❌ Missing | Executor can't validate dataset schemas |
| **Write index.json** | ❌ Missing | Executor can't discover available blocks |
| **Create BLOCKS_REGISTRY** | ❌ Missing | No central catalog location |
| **Update existing catalog** | ❌ Missing | Can't incrementally add blocks |

### Implementation Gaps

| Component | Implemented | Missing |
|-----------|------------|---------|
| Content generation | ✅ 100% | - |
| Wiki article format | ✅ 100% | - |
| JSON index format | ✅ 100% | - |
| Schema format | ✅ 100% | - |
| **File system writes** | ❌ 0% | All write operations |
| **Dataiku Wiki API** | ❌ 0% | Wiki creation/update |
| **Dataiku Library API** | ❌ 0% | File writes to library |
| **Registry management** | ❌ 0% | Project creation/init |

---

## Required Implementation

### Phase 1.5: Add Catalog Persistence

**Priority:** P0 (Blocking)
**Complexity:** Medium
**Estimated Effort:** 4-6 hours

#### Tasks

**1. Add DSSClient to CatalogWriter**

```python
class CatalogWriter:
    def __init__(self, client: DSSClient = None, registry_key: str = "BLOCKS_REGISTRY"):
        """
        Initialize CatalogWriter with optional DSSClient.

        Args:
            client: DSSClient for writing to Dataiku (None = generate only)
            registry_key: Registry project key (default: BLOCKS_REGISTRY)
        """
        self.client = client
        self.registry_key = registry_key
```

**2. Implement Registry Initialization**

```python
def _ensure_registry_exists(self) -> DSSProject:
    """
    Ensure BLOCKS_REGISTRY project exists.

    Returns:
        DSSProject instance

    Creates:
        - Project if doesn't exist
        - Wiki structure (by-hierarchy, by-domain)
        - Library folder (schemas/)
        - index.json file
    """
    try:
        project = self.client.get_project(self.registry_key)
    except:
        # Create registry project
        project = self.client.create_project(
            self.registry_key,
            "Reusable Workflow Blocks Registry",
            owner="admin"
        )

        # Initialize wiki structure
        # Initialize library
        # Create index.json

    return project
```

**3. Implement Wiki Writing**

```python
def _write_wiki_article(self, block: BlockMetadata) -> str:
    """
    Write wiki article for block.

    Returns:
        Wiki article ID

    Writes to:
        - BLOCKS_REGISTRY/Wiki/by-hierarchy/{level}/{block_id}.md
        - BLOCKS_REGISTRY/Wiki/by-domain/{domain}/{block_id}.md (link)
    """
    project = self._ensure_registry_exists()
    wiki = project.get_wiki()

    # Generate content
    article_content = self.generate_wiki_article(block)

    # Determine path
    wiki_path = self.get_wiki_path(block)

    # Write article
    article = wiki.create_article(wiki_path, article_content)
    # Or update if exists

    return article.id
```

**4. Implement Schema Writing**

```python
def _write_schemas(self, block: BlockMetadata):
    """
    Write schema files to library.

    Writes:
        - schemas/{block_id}_{port_name}.schema.json for each port
    """
    project = self._ensure_registry_exists()
    library = project.get_library()

    # Write input schemas
    for inp in block.inputs:
        if inp.schema_ref:
            schema_path = f"schemas/{block.block_id}_{inp.name}.schema.json"
            schema_content = self.generate_schema_file(inp.schema)
            library.write_file(schema_path, schema_content)

    # Write output schemas
    for out in block.outputs:
        if out.schema_ref:
            schema_path = f"schemas/{block.block_id}_{out.name}.schema.json"
            schema_content = self.generate_schema_file(out.schema)
            library.write_file(schema_path, schema_content)
```

**5. Implement Index Updates**

```python
def _update_index(self, blocks: List[BlockMetadata]):
    """
    Update master index.json.

    Reads existing index, merges new blocks, writes back.
    """
    project = self._ensure_registry_exists()
    library = project.get_library()

    # Read existing index
    try:
        index_content = library.read_file("index.json")
        existing_index = json.loads(index_content)
    except:
        existing_index = {"blocks": [], "version": "1.0"}

    # Merge each block
    for block in blocks:
        existing_index = self.merge_catalog_index(existing_index, block)

    # Write updated index
    index_content = json.dumps(existing_index, indent=2)
    library.write_file("index.json", index_content)
```

**6. Implement Main Write Method**

```python
def write_catalog(self, blocks: List[BlockMetadata]) -> Dict[str, Any]:
    """
    Write all blocks to registry.

    Args:
        blocks: List of blocks to write

    Returns:
        {
            'registry': registry_key,
            'blocks_written': count,
            'wiki_articles': [article_ids],
            'schemas_written': count,
            'index_updated': bool
        }
    """
    if not self.client:
        raise ValueError("CatalogWriter requires DSSClient for write operations")

    results = {
        'registry': self.registry_key,
        'blocks_written': 0,
        'wiki_articles': [],
        'schemas_written': 0,
        'index_updated': False
    }

    # Write each block
    for block in blocks:
        # Write wiki
        article_id = self._write_wiki_article(block)
        results['wiki_articles'].append(article_id)

        # Write schemas
        self._write_schemas(block)
        results['schemas_written'] += len(block.inputs) + len(block.outputs)

        results['blocks_written'] += 1

    # Update index
    self._update_index(blocks)
    results['index_updated'] = True

    return results
```

**7. Update DiscoveryAgent to Use Write**

```python
# In agent.py, update Step 4:
if not dry_run:
    if self.verbose:
        print("Step 4: Writing blocks to catalog...")

    # Write to BLOCKS_REGISTRY
    write_results = self.catalog_writer.write_catalog(enriched_blocks)
    blocks_cataloged = write_results['blocks_written']

    if self.verbose:
        print(f"  Wrote {blocks_cataloged} blocks to {write_results['registry']}")
        print(f"  Wiki articles: {len(write_results['wiki_articles'])}")
        print(f"  Schemas: {write_results['schemas_written']}")
```

---

## Testing Requirements

### New Tests Needed

**test_catalog_writer_persistence.py:**

```python
@pytest.mark.integration
@pytest.mark.real_dataiku
class TestCatalogPersistence:
    """Test writing catalog to real Dataiku registry."""

    def test_ensure_registry_exists(self, real_client):
        """Test registry creation/access."""

    def test_write_wiki_article(self, real_client):
        """Test writing wiki article to registry."""

    def test_write_schemas(self, real_client):
        """Test writing schema files to library."""

    def test_update_index(self, real_client):
        """Test updating master index.json."""

    def test_write_catalog_full(self, real_client):
        """Test complete catalog write workflow."""

    def test_incremental_updates(self, real_client):
        """Test adding blocks to existing catalog."""
```

---

## Impact on Executor Agent

### Without Catalog Persistence

❌ **Executor Agent CANNOT:**
- Discover available blocks (no index.json)
- Read block metadata (no wiki articles)
- Validate schemas (no schema files)
- Use blocks in configurations

### With Catalog Persistence

✅ **Executor Agent CAN:**
- Query index.json for available blocks
- Read wiki articles for block documentation
- Load schema files for validation
- Instantiate blocks in projects

**Example Executor Workflow:**

```python
# 1. Discover blocks
registry = client.get_project("BLOCKS_REGISTRY")
library = registry.get_library()
index = json.loads(library.read_file("index.json"))

# 2. Find block
block_ref = next(b for b in index["blocks"] if b["block_id"] == "NEW_SIM")

# 3. Read metadata
wiki = registry.get_wiki()
article = wiki.get_article(f"by-hierarchy/process/NEW_SIM")

# 4. Load schemas
input_schema = json.loads(library.read_file(f"schemas/NEW_SIM_input1.schema.json"))

# 5. Use block in project
# ... instantiate block with metadata and schemas
```

---

## Recommendations

### Immediate Actions (Phase 1.5)

1. **Implement Catalog Persistence** (P0)
   - Add write_catalog() method
   - Implement all _write_* helper methods
   - Update DiscoveryAgent to call write_catalog()

2. **Add Real Write Tests** (P0)
   - Test against real BLOCKS_REGISTRY project
   - Verify wiki article creation
   - Verify library file writes
   - Verify index updates

3. **Update Documentation** (P1)
   - Update PHASE1_COMPLETION_SUMMARY.md with gap
   - Create Phase 1.5 implementation plan
   - Document BLOCKS_REGISTRY structure

### Alternative: File System Output (Quick Fix)

If Dataiku Wiki/Library API is complex, could implement file system output first:

```python
def write_catalog_to_filesystem(
    blocks: List[BlockMetadata],
    output_dir: str = "./blocks_catalog"
):
    """
    Write catalog to local filesystem.

    Creates:
        output_dir/
        ├── wiki/
        │   └── by-hierarchy/
        │       └── process/
        │           └── BLOCK_ID.md
        ├── schemas/
        │   └── BLOCK_ID_port.schema.json
        └── index.json
    """
```

This would allow Executor Agent development to proceed while Dataiku integration is completed.

---

## Conclusion

**Current State:** Discovery Agent is **95% complete**
- ✅ Core discovery logic: 100%
- ✅ Content generation: 100%
- ❌ **Output persistence: 0%** ⚠️

**Blocking Issue:** Without catalog persistence, Executor Agent **cannot consume** Discovery Agent results.

**Solution:** Implement Phase 1.5 (Catalog Persistence) to add write operations to BLOCKS_REGISTRY.

**Estimated Effort:** 4-6 hours of development + 2 hours testing

**Priority:** **CRITICAL** - Must be completed before Executor Agent development.

---

**Status:** ⚠️ Discovery Agent needs Phase 1.5 to be production-ready for Executor Agent consumption.
