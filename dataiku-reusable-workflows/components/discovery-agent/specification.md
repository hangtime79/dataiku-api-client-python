# Discovery Agent Specification

## Overview

The Discovery Agent is responsible for crawling Dataiku projects and cataloging reusable blocks in the BLOCKS_REGISTRY.

---

## Functional Requirements

### FR-1: Project Crawling

The agent MUST be able to traverse a Dataiku project and extract:
- All datasets (name, type, schema, zone membership)
- All recipes (name, type, inputs, outputs, zone membership)
- All zones (name, datasets, recipes)
- All saved models (id, type, active version)
- Project metadata (name, description, tags)

### FR-2: Block Identification

The agent MUST identify valid block candidates by:
- Analyzing zone boundaries
- Determining inputs (datasets entering zone from outside)
- Determining outputs (datasets consumed outside zone)
- Validating containment (no orphaned references)

### FR-3: Metadata Extraction

For each identified block, the agent MUST extract:
- Block identity (generated ID from zone name)
- Version (from configuration or auto-generated)
- Input ports with schemas
- Output ports with schemas
- Internal components (datasets, recipes, models)
- Dependencies (Python packages, plugins)

### FR-4: Wiki Catalog Writing

The agent MUST write to the BLOCKS_REGISTRY Wiki:
- Block article in correct hierarchy location
- Cross-reference in domain location
- Index update

### FR-5: Library Index Writing

The agent MUST write to the BLOCKS_REGISTRY Library:
- Master index.json update
- Schema files for each port
- Version manifest

### FR-6: Manual Edit Preservation

On re-crawl, the agent MUST:
- Preserve manually added content in Wiki articles
- Merge rather than replace index entries
- Not delete manually added blocks

---

## Algorithm Specifications

### Algorithm 1: Zone Boundary Analysis

```
FUNCTION analyze_zone_boundary(zone, project_flow)
  INPUT: zone object, project flow graph
  OUTPUT: ZoneBoundary object with inputs, outputs, internals

  1. Initialize sets:
     - zone_datasets = set of all datasets in zone
     - zone_recipes = set of all recipes in zone
     - inputs = empty set
     - outputs = empty set
     - internals = empty set

  2. For each dataset in zone_datasets:
     a. Get upstream recipes (recipes that produce this dataset)
     b. Get downstream recipes (recipes that consume this dataset)

     c. If no upstream recipes in zone_recipes:
        - Add dataset to inputs (it comes from outside)

     d. If any downstream recipes NOT in zone_recipes:
        - Add dataset to outputs (it goes outside)

     e. If has upstream in zone AND all downstream in zone:
        - Add dataset to internals

  3. Validate containment:
     a. For each recipe in zone_recipes:
        - All input datasets must be in (inputs ∪ internals)
        - All output datasets must be in (outputs ∪ internals)
     b. If validation fails, mark zone as invalid block candidate

  4. Return ZoneBoundary(inputs, outputs, internals, is_valid)
END FUNCTION
```

### Algorithm 2: Block Identification

```
FUNCTION identify_blocks(project)
  INPUT: Dataiku project
  OUTPUT: List of BlockCandidate objects

  1. Get project flow
  2. Get all zones from flow

  3. candidates = empty list

  4. For each zone in zones:
     a. If zone is default zone AND has no explicit name:
        - Skip (default zones without structure are not blocks)

     b. boundary = analyze_zone_boundary(zone, flow)

     c. If boundary.is_valid:
        - Create BlockCandidate from zone and boundary
        - Add to candidates

     d. Else:
        - Log warning: "Zone {zone.name} cannot be a block: {reason}"

  5. Return candidates
END FUNCTION
```

### Algorithm 3: Schema Extraction

```
FUNCTION extract_schema(dataset)
  INPUT: Dataiku dataset object
  OUTPUT: Schema dict

  1. Try to get schema from dataset:
     schema_raw = dataset.get_schema()

  2. If schema_raw is empty or has no columns:
     - Return None (schema unknown)

  3. columns = empty list

  4. For each column in schema_raw['columns']:
     column_def = {
       'name': column['name'],
       'type': map_dataiku_type_to_standard(column['type']),
       'description': column.get('comment', ''),
       'nullable': not column.get('notNull', False)
     }
     columns.append(column_def)

  5. Return {
       'format_version': '1.0',
       'columns': columns
     }
END FUNCTION

FUNCTION map_dataiku_type_to_standard(dataiku_type)
  mapping = {
    'string': 'string',
    'int': 'integer',
    'bigint': 'integer',
    'float': 'double',
    'double': 'double',
    'boolean': 'boolean',
    'date': 'date',
    'array': 'array',
    'object': 'object',
    'map': 'object'
  }
  Return mapping.get(dataiku_type.lower(), 'string')
END FUNCTION
```

### Algorithm 4: Dependency Extraction

```
FUNCTION extract_dependencies(zone, project)
  INPUT: Zone, Project
  OUTPUT: Dependencies object

  python_deps = set()
  plugin_deps = set()

  1. For each recipe in zone.recipes:
     a. If recipe is code recipe (python, pyspark, etc):
        - Parse code for import statements
        - For each import:
          - If not standard library:
            - Add to python_deps

     b. If recipe is plugin recipe:
        - Get plugin ID
        - Add to plugin_deps

  2. Check project libraries:
     a. Get list of libraries used in zone recipes
     b. For each library, extract its requirements if available

  3. Return Dependencies(
       python=list(python_deps),
       plugins=list(plugin_deps)
     )
END FUNCTION

FUNCTION parse_imports(code)
  INPUT: Python code string
  OUTPUT: List of package names

  imports = empty list

  1. For each line in code:
     a. If line matches "import X" pattern:
        - Extract X (first part before dot)
        - Add to imports
     b. If line matches "from X import" pattern:
        - Extract X (first part before dot)
        - Add to imports

  2. Filter out standard library modules

  3. Return imports
END FUNCTION
```

### Algorithm 5: Wiki Article Generation

```
FUNCTION generate_wiki_article(block_metadata)
  INPUT: BlockMetadata object
  OUTPUT: Markdown string

  1. Generate YAML frontmatter:
     ---
     block_id: {block_metadata.block_id}
     version: {block_metadata.version}
     type: {block_metadata.type}
     blocked: {block_metadata.blocked}
     source_project: {block_metadata.source_project}
     source_zone: {block_metadata.source_zone}
     hierarchy_level: {block_metadata.hierarchy_level}
     domain: {block_metadata.domain}
     tags: {block_metadata.tags}
     ---

  2. Generate title:
     # {block_metadata.name or block_metadata.block_id}

  3. Generate description section:
     ## Description

     {block_metadata.description or "No description provided."}

  4. Generate inputs table:
     ## Inputs

     | Name | Type | Required | Description |
     |------|------|----------|-------------|
     For each input in block_metadata.inputs:
       | {input.name} | {input.type} | {input.required} | {input.description} |

  5. Generate outputs table:
     ## Outputs

     | Name | Type | Description |
     |------|------|-------------|
     For each output in block_metadata.outputs:
       | {output.name} | {output.type} | {output.description} |

  6. Generate contains section:
     ## Contains

     **Datasets:** {comma-separated list}
     **Recipes:** {comma-separated list}
     If models: **Models:** {comma-separated list}

  7. Generate dependencies section:
     ## Dependencies

     If python deps:
       - Python: {comma-separated list}
     If plugin deps:
       - Plugins: {comma-separated list}

  8. Generate usage example:
     ## Usage

     ```yaml
     blocks:
       - ref: "BLOCKS_REGISTRY/{block_id}@{version}"
         inputs:
           {first_input.name}: your_dataset
         outputs:
           {first_output.name}: your_output
     ```

  9. Generate changelog section (empty for new blocks):
     ## Changelog

     - {version}: Initial release

  10. Return concatenated markdown
END FUNCTION
```

### Algorithm 6: Index Merge

```
FUNCTION merge_index(existing_index, new_blocks)
  INPUT: Existing index dict, List of new block summaries
  OUTPUT: Merged index dict

  1. Create lookup of existing blocks by (block_id, version)
     existing_lookup = {}
     For each block in existing_index['blocks']:
       key = (block['block_id'], block['version'])
       existing_lookup[key] = block

  2. Create lookup of new blocks
     new_lookup = {}
     For each block in new_blocks:
       key = (block['block_id'], block['version'])
       new_lookup[key] = block

  3. Merge:
     merged_blocks = []

     a. Add all existing blocks that are NOT in new_lookup
        (preserves manually added blocks)
        For each key, block in existing_lookup:
          If key not in new_lookup:
            merged_blocks.append(block)

     b. Add all new blocks (updates or new entries)
        For each block in new_blocks:
          merged_blocks.append(block)

  4. Update metadata:
     merged_index = {
       'format_version': '1.0',
       'updated_at': current_timestamp_iso(),
       'block_count': count unique block_ids,
       'blocks': merged_blocks
     }

  5. Return merged_index
END FUNCTION
```

---

## Component Specifications

### Component 1: ProjectCrawler

**Responsibility:** Extract raw data from a Dataiku project.

**Inputs:**
- DSSClient
- Project key

**Outputs:**
- ProjectData object containing:
  - Project metadata
  - List of datasets with full settings
  - List of recipes with full settings
  - List of zones with membership
  - List of saved models
  - Flow graph

**Methods:**

```python
class ProjectCrawler:
    def __init__(self, client: DSSClient):
        """Initialize with authenticated client."""

    def crawl(self, project_key: str) -> ProjectData:
        """
        Crawl entire project and return structured data.

        Steps:
        1. Get project handle
        2. Get project metadata (get_summary, get_metadata)
        3. List all datasets (list_datasets with full settings)
        4. List all recipes (list_recipes with full settings)
        5. Get flow and zones (get_flow, list_zones)
        6. List saved models (list_saved_models)
        7. Build and return ProjectData
        """

    def _get_dataset_details(self, project, dataset_name) -> DatasetInfo:
        """Get full details for a single dataset."""

    def _get_recipe_details(self, project, recipe_name) -> RecipeInfo:
        """Get full details for a single recipe."""

    def _get_zone_membership(self, flow) -> Dict[str, ZoneInfo]:
        """Map items to their zones."""
```

### Component 2: BlockIdentifier

**Responsibility:** Analyze project structure and identify block candidates.

**Inputs:**
- ProjectData from crawler

**Outputs:**
- List of BlockCandidate objects

**Methods:**

```python
class BlockIdentifier:
    def __init__(self):
        """Initialize identifier."""

    def identify_blocks(self, project_data: ProjectData) -> List[BlockCandidate]:
        """
        Identify all valid block candidates in project.

        Steps:
        1. Build flow graph from project data
        2. For each zone, analyze boundary
        3. Filter to valid candidates
        4. Return candidates
        """

    def _analyze_zone_boundary(
        self,
        zone: ZoneInfo,
        datasets: Dict[str, DatasetInfo],
        recipes: Dict[str, RecipeInfo]
    ) -> ZoneBoundary:
        """Analyze a single zone's boundary."""

    def _validate_block_candidate(
        self,
        zone: ZoneInfo,
        boundary: ZoneBoundary
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if zone is valid block candidate.

        Returns: (is_valid, error_message)
        """
```

### Component 3: MetadataExtractor

**Responsibility:** Extract detailed metadata from block candidates.

**Inputs:**
- BlockCandidate
- ProjectData

**Outputs:**
- BlockMetadata

**Methods:**

```python
class MetadataExtractor:
    def __init__(self, config: DiscoveryConfig):
        """Initialize with configuration."""

    def extract_metadata(
        self,
        candidate: BlockCandidate,
        project_data: ProjectData
    ) -> BlockMetadata:
        """
        Extract full metadata for a block candidate.

        Steps:
        1. Generate block ID from zone name
        2. Get or generate version
        3. Extract input port metadata
        4. Extract output port metadata
        5. List internal components
        6. Extract dependencies
        7. Build BlockMetadata
        """

    def _generate_block_id(self, zone_name: str) -> str:
        """
        Generate block ID from zone name.

        Rules:
        - Convert to UPPERCASE
        - Replace spaces with underscores
        - Remove invalid characters
        - Truncate to 64 chars
        """

    def _extract_port_metadata(
        self,
        dataset: DatasetInfo
    ) -> BlockPort:
        """Extract port metadata from dataset."""

    def _extract_schema(self, dataset: DatasetInfo) -> Optional[dict]:
        """Extract and normalize schema from dataset."""

    def _extract_dependencies(
        self,
        candidate: BlockCandidate,
        project_data: ProjectData
    ) -> Dependencies:
        """Extract Python and plugin dependencies."""
```

### Component 4: CatalogWriter

**Responsibility:** Write catalog to BLOCKS_REGISTRY.

**Inputs:**
- List of BlockMetadata
- BLOCKS_REGISTRY project

**Outputs:**
- Write results (success/failure per block)

**Methods:**

```python
class CatalogWriter:
    def __init__(self, client: DSSClient, registry_key: str = "BLOCKS_REGISTRY"):
        """Initialize with client and registry project key."""

    def write_catalog(
        self,
        blocks: List[BlockMetadata]
    ) -> CatalogWriteResult:
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

    def _write_wiki_article(
        self,
        block: BlockMetadata,
        wiki: DSSWiki
    ) -> bool:
        """
        Write single wiki article.

        Steps:
        1. Generate article content
        2. Determine article path (by-hierarchy)
        3. Create or update article
        4. Also link in by-domain
        """

    def _write_schemas(
        self,
        block: BlockMetadata,
        library: DSSProjectLibrary
    ):
        """Write schema files to library."""

    def _update_index(
        self,
        blocks: List[BlockMetadata],
        library: DSSProjectLibrary
    ):
        """
        Update master index.json.

        Steps:
        1. Read existing index
        2. Merge with new blocks
        3. Write updated index
        """

    def _read_existing_index(self, library) -> dict:
        """Read and parse existing index.json."""

    def _merge_indexes(self, existing: dict, new_blocks: List[dict]) -> dict:
        """Merge new blocks with existing index."""
```

---

## Error Handling

### Error Types

| Error | When | Handling |
|-------|------|----------|
| `ProjectNotFoundError` | Project key doesn't exist | Fail with clear message |
| `RegistryNotFoundError` | Registry project missing | Create registry or fail |
| `ZoneAccessError` | Cannot access zone data | Log warning, skip zone |
| `SchemaExtractionError` | Cannot get dataset schema | Log warning, continue with None |
| `WikiWriteError` | Cannot write wiki article | Retry once, then fail block |
| `IndexWriteError` | Cannot update index | Fail entire operation |

### Error Recovery

```python
class DiscoveryAgent:
    def discover_project(self, project_key, config):
        try:
            # ... discovery logic
        except ProjectNotFoundError:
            raise  # Let caller handle
        except RegistryNotFoundError:
            if config.create_registry_if_missing:
                self._create_registry()
                return self.discover_project(project_key, config)
            raise
        except WikiWriteError as e:
            # Retry once
            try:
                self._write_wiki_article(e.block)
            except:
                self.results.add_failure(e.block, str(e))
```

---

## Configuration

### DiscoveryConfig

```python
@dataclass
class DiscoveryConfig:
    # Required
    hierarchy_level: str          # e.g., "equipment"
    domain: str                   # e.g., "rotating_equipment"

    # Optional with defaults
    version: str = "1.0.0"        # Default version for new blocks
    blocked: bool = False         # Mark as protected
    tags: List[str] = field(default_factory=list)

    # Behavior options
    publish_all_zones: bool = False        # Publish even invalid candidates
    overwrite_existing: bool = False       # Overwrite existing blocks
    create_registry_if_missing: bool = True
    extract_schemas: bool = True
    extract_dependencies: bool = True

    # Filtering
    zone_filter: Optional[List[str]] = None  # Only these zones
    exclude_zones: Optional[List[str]] = None  # Skip these zones
```

---

## Output Formats

### CatalogWriteResult

```python
@dataclass
class CatalogWriteResult:
    success: bool
    blocks_written: int
    blocks_failed: int
    blocks_skipped: int
    written_blocks: List[str]    # Block IDs
    failed_blocks: List[Tuple[str, str]]  # (block_id, error)
    skipped_blocks: List[Tuple[str, str]]  # (zone_name, reason)
    warnings: List[str]
```

---

## Usage Examples

### Basic Discovery

```python
from dataikuapi import DSSClient
from dataikuapi.iac.workflows.discovery import DiscoveryAgent, DiscoveryConfig

client = DSSClient("https://dss.example.com", "api_key")

agent = DiscoveryAgent(client)
result = agent.discover_project(
    source_project_key="COMPRESSOR_SOLUTIONS",
    config=DiscoveryConfig(
        hierarchy_level="equipment",
        domain="rotating_equipment",
        tags=["compressor", "vibration"]
    )
)

print(f"Written: {result.blocks_written}")
print(f"Failed: {result.blocks_failed}")
for block_id in result.written_blocks:
    print(f"  - {block_id}")
```

### Discovery with Zone Filter

```python
result = agent.discover_project(
    source_project_key="MY_PROJECT",
    config=DiscoveryConfig(
        hierarchy_level="process",
        domain="process_control",
        zone_filter=["data_preparation", "feature_engineering"]
    )
)
```

### Re-Discovery (Update)

```python
result = agent.discover_project(
    source_project_key="COMPRESSOR_SOLUTIONS",
    config=DiscoveryConfig(
        hierarchy_level="equipment",
        domain="rotating_equipment",
        version="1.1.0",  # New version
        overwrite_existing=True
    )
)
```
