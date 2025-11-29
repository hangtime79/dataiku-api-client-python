# Discovery Agent Specification

## Overview

The Discovery Agent is responsible for crawling Dataiku projects and cataloging discovered blocks using a **two-tier registry architecture**:

1. **Project-Local Registries**: Full discovery results written to each source project's Wiki and Library, inheriting project-level Dataiku permissions
2. **BLOCKS_REGISTRY**: Central catalog containing production-ready blocks (full content) and links to project-local registries (references only)

This architecture enables security-aware discovery while maintaining cross-project discoverability.

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

### FR-4: Project-Local Registry Writing

The agent MUST write to the source project's local registry:
- Wiki articles in `PROJECT/Wiki/_DISCOVERED_BLOCKS/by-hierarchy/{level}/{block_id}.md`
- Cross-references in `PROJECT/Wiki/_DISCOVERED_BLOCKS/by-domain/{domain}/`
- Index in `PROJECT/Library/discovery/index.json`
- Schemas in `PROJECT/Library/discovery/schemas/{block_id}/{port}.json`
- Discovery metadata in `PROJECT/Library/discovery/metadata.json`

### FR-5: Project Registration

The agent MUST register the project in BLOCKS_REGISTRY:
- Create link page in `BLOCKS_REGISTRY/Wiki/_PROJECT_REGISTRIES/{project_key}.md`
- Write project metadata to `BLOCKS_REGISTRY/Library/projects/{project_key}.json`
- Update `BLOCKS_REGISTRY/Library/projects/project_index.json`
- Include links to project-local discoveries (NOT full content replication)

### FR-6: Manual Edit Preservation

On re-crawl, the agent MUST:
- Preserve manually added content in Wiki articles (changelogs, custom descriptions)
- Merge rather than replace index entries
- Not delete manually added blocks
- Maintain version history

### FR-7: Version Management

The agent MUST manage block versions:
- Auto-increment minor version when block metadata changes
- Keep version unchanged when block is identical
- Support manual version override
- Store version in YAML frontmatter and index

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

### Algorithm 7: Wiki-Based Diff

```
FUNCTION compare_with_existing_wiki(project, new_blocks)
  INPUT: Dataiku project, List of newly discovered blocks
  OUTPUT: ChangeSet with new/updated/deleted/unchanged blocks

  1. Read existing Wiki articles
     existing_blocks = []
     wiki = project.get_wiki()
     articles = wiki.list_articles(path="_DISCOVERED_BLOCKS/by-hierarchy")

     FOR EACH article IN articles:
       content = article.get_content()
       frontmatter = parse_yaml_frontmatter(content)
       metadata = BlockMetadata.from_dict(frontmatter)
       existing_blocks.append(metadata)

  2. Compare block IDs
     new_ids = {b.block_id for b in new_blocks}
     existing_ids = {b.block_id for b in existing_blocks}

  3. Classify changes
     changes = {
       'new': [],
       'updated': [],
       'unchanged': [],
       'deleted': []
     }

     # New blocks
     FOR EACH block IN new_blocks:
       IF block.block_id NOT IN existing_ids:
         changes['new'].append(block)

     # Deleted blocks
     FOR EACH block IN existing_blocks:
       IF block.block_id NOT IN new_ids:
         changes['deleted'].append(block)

     # Updated or unchanged blocks
     FOR EACH new_block IN new_blocks:
       IF new_block.block_id IN existing_ids:
         existing_block = find_by_id(existing_blocks, new_block.block_id)
         IF blocks_differ(existing_block, new_block):
           changes['updated'].append(new_block)
         ELSE:
           changes['unchanged'].append(new_block)

  4. Return changes
END FUNCTION

FUNCTION blocks_differ(block1, block2)
  INPUT: Two BlockMetadata objects
  OUTPUT: Boolean (true if different)

  # Compare relevant fields (ignore timestamps, created_by)
  RETURN (
    block1.inputs != block2.inputs OR
    block1.outputs != block2.outputs OR
    block1.contains != block2.contains OR
    block1.hierarchy_level != block2.hierarchy_level OR
    block1.domain != block2.domain OR
    block1.dependencies != block2.dependencies
  )
END FUNCTION
```

### Algorithm 8: Manual Edit Preservation

```
FUNCTION merge_wiki_article(existing_content, new_metadata)
  INPUT: Existing Wiki article content (string), New block metadata
  OUTPUT: Merged Wiki article content (string)

  1. Parse existing article
     frontmatter, body = split_yaml_frontmatter(existing_content)
     sections = parse_markdown_sections(body)

  2. Generate new article from metadata
     new_article = generate_wiki_article(new_metadata)
     new_frontmatter, new_body = split_yaml_frontmatter(new_article)
     new_sections = parse_markdown_sections(new_body)

  3. Identify sections to preserve
     preserved_sections = {}

     # Always preserve Changelog
     IF 'Changelog' IN sections:
       preserved_sections['Changelog'] = sections['Changelog']

     # Preserve custom notes
     IF 'Notes' IN sections OR 'Custom Notes' IN sections:
       preserved_sections['Notes'] = sections.get('Notes') OR sections.get('Custom Notes')

     # Preserve manually edited description
     IF sections.get('Description') != auto_generated_description(frontmatter):
       preserved_sections['Description'] = sections['Description']

  4. Merge sections
     merged_article = new_article

     FOR section_name, section_content IN preserved_sections:
       merged_article = replace_or_append_section(
         merged_article,
         section_name,
         section_content
       )

  5. Update changelog if version changed
     old_version = frontmatter.get('version')
     new_version = new_frontmatter.get('version')

     IF old_version != new_version:
       changelog_entry = f"- {new_version}: Updated by Discovery Agent"
       merged_article = append_to_changelog(merged_article, changelog_entry)

  6. Return merged article
END FUNCTION

FUNCTION generate_version(block_id, previous_metadata, current_metadata)
  INPUT: Block ID, Previous metadata (or None), Current metadata
  OUTPUT: Version string (semver format)

  1. IF previous_metadata IS None:
     RETURN "1.0.0"  # New block

  2. IF blocks_differ(previous_metadata, current_metadata):
     # Increment minor version
     previous_version = parse_semver(previous_metadata.version)
     RETURN f"{previous_version.major}.{previous_version.minor + 1}.{previous_version.patch}"

  3. ELSE:
     # No changes, keep existing version
     RETURN previous_metadata.version
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

**Responsibility:** Write discovery results to project-local registries and/or BLOCKS_REGISTRY.

**Inputs:**
- DSSClient
- Target type (project-local, central registry, or both)
- List of BlockMetadata

**Outputs:**
- Write results (success/failure per block)

**Methods:**

```python
class CatalogWriter:
    def __init__(
        self,
        client: DSSClient,
        target_type: str = "project",  # "project" | "registry" | "both"
        registry_key: str = "BLOCKS_REGISTRY"
    ):
        """
        Initialize catalog writer with configurable targets.

        Args:
            client: DSSClient for API access
            target_type: Where to write - project-local, central registry, or both
            registry_key: BLOCKS_REGISTRY project key
        """

    def write_to_project_registry(
        self,
        project_key: str,
        blocks: List[BlockMetadata]
    ) -> Dict[str, Any]:
        """
        Write discovery to project's local registry.

        Creates:
        - PROJECT/Wiki/_DISCOVERED_BLOCKS/{hierarchy}/{block_id}.md
        - PROJECT/Library/discovery/index.json
        - PROJECT/Library/discovery/schemas/{block_id}/{port}.json
        - PROJECT/Library/discovery/metadata.json

        Preserves:
        - Manual edits in Wiki (changelogs, custom descriptions)
        - Existing index entries for blocks not in current discovery

        Returns:
            {
                'project': project_key,
                'blocks_written': int,
                'blocks_updated': int,
                'blocks_unchanged': int,
                'wiki_articles': [article_ids],
                'index_updated': bool
            }
        """

    def initialize_project_registry(self, project: DSSProject) -> bool:
        """
        Create discovery registry structure in project.

        Creates:
        - Wiki/_DISCOVERED_BLOCKS/ (with by-hierarchy folders)
        - Library/discovery/ folder
        - Library/discovery/index.json (empty initial)
        - Library/discovery/schemas/ folder
        """

    def compare_with_existing(
        self,
        project: DSSProject,
        new_blocks: List[BlockMetadata]
    ) -> Dict[str, List[BlockMetadata]]:
        """
        Compare new discovery with existing Wiki articles.

        Uses Algorithm 7 (Wiki-Based Diff).

        Returns:
            {
                'new': [blocks not in existing wiki],
                'updated': [blocks with changes],
                'unchanged': [blocks identical],
                'deleted': [blocks in wiki but not discovered]
            }
        """

    def merge_wiki_article(
        self,
        existing_content: str,
        new_metadata: BlockMetadata
    ) -> str:
        """
        Merge new discovery with existing Wiki article.

        Uses Algorithm 8 (Manual Edit Preservation).

        Preserves:
        - Changelog section (appends new version)
        - Custom descriptions (if manually edited)
        - Manual tags/notes

        Updates:
        - Inputs/outputs tables
        - Schemas
        - Metadata frontmatter
        """

    def _write_wiki_article(
        self,
        project: DSSProject,
        block: BlockMetadata,
        existing_content: Optional[str] = None
    ) -> str:
        """
        Write single wiki article to project.

        Steps:
        1. If existing_content provided, merge with new metadata
        2. Otherwise, generate fresh article
        3. Write to Wiki at correct hierarchy path
        4. Return article ID
        """

    def _write_schemas(
        self,
        project: DSSProject,
        block: BlockMetadata
    ):
        """
        Write schema files to project library.

        Creates:
        - Library/discovery/schemas/{block_id}/{port_name}.json
        """

    def _update_project_index(
        self,
        project: DSSProject,
        blocks: List[BlockMetadata]
    ):
        """
        Update project's discovery index.json.

        Steps:
        1. Read existing Library/discovery/index.json
        2. Merge with new blocks (using Algorithm 6)
        3. Write updated index atomically
        """

    def _update_discovery_metadata(
        self,
        project: DSSProject,
        run_info: Dict[str, Any]
    ):
        """
        Update discovery metadata.json with run information.

        Appends:
        - Run timestamp
        - Blocks found/new/updated/unchanged
        - Configuration used
        """
```

### Component 5: ProjectRegistrar

**Responsibility:** Manage project registration in BLOCKS_REGISTRY.

**Inputs:**
- DSSClient
- BLOCKS_REGISTRY key
- Project key and discovered blocks

**Outputs:**
- Registration results

**Methods:**

```python
class ProjectRegistrar:
    def __init__(self, client: DSSClient, registry_key: str = "BLOCKS_REGISTRY"):
        """Initialize with client and registry project key."""
        self.client = client
        self.registry_key = registry_key

    def register_project(
        self,
        project_key: str,
        blocks: List[BlockMetadata]
    ) -> RegistrationResult:
        """
        Create/update project registration in BLOCKS_REGISTRY.

        Creates:
        - Wiki article: _PROJECT_REGISTRIES/{project_key}.md
        - Project metadata: Library/projects/{project_key}.json
        - Updates Library/projects/project_index.json

        Returns:
            {
                'registry': 'BLOCKS_REGISTRY',
                'project_registered': bool,
                'blocks_linked': int,
                'link_article': article_id
            }
        """

    def initialize_project_registries(self) -> bool:
        """
        Initialize BLOCKS_REGISTRY project registries structure.

        Creates:
        - Wiki/_PROJECT_REGISTRIES/ section
        - Library/projects/ folder
        - Library/projects/project_index.json
        """

    def get_registered_projects(self) -> List[ProjectRegistration]:
        """List all registered projects from BLOCKS_REGISTRY."""

    def unregister_project(self, project_key: str) -> bool:
        """Remove project registration (cleanup)."""

    def _generate_project_link_article(
        self,
        project_key: str,
        project_name: str,
        blocks: List[BlockMetadata]
    ) -> str:
        """
        Generate Wiki article for project registration.

        Includes:
        - Project metadata
        - List of discovered blocks with links
        - Access information
        """

    def _write_project_metadata(
        self,
        project_key: str,
        blocks: List[BlockMetadata]
    ):
        """
        Write project metadata JSON.

        Format: See Section 2.3 of planning docs
        """
```

### Component 6: StateTracker

**Responsibility:** Track discovery state for diff/update workflows.

**Inputs:**
- DSSProject
- Current and previous BlockMetadata

**Outputs:**
- ChangeSet
- Version recommendations

**Methods:**

```python
class StateTracker:
    """Wiki-based state tracking for discovery updates."""

    def get_previous_discovery(
        self,
        project: DSSProject
    ) -> List[BlockMetadata]:
        """
        Read existing Wiki articles to reconstruct previous discovery.

        Parses YAML frontmatter from _DISCOVERED_BLOCKS articles.
        Uses Algorithm 7 (Wiki-Based Diff).
        """

    def compute_changes(
        self,
        previous: List[BlockMetadata],
        current: List[BlockMetadata]
    ) -> ChangeSet:
        """
        Compare previous and current discoveries.

        Returns:
            ChangeSet with new/updated/deleted/unchanged blocks
        """

    def generate_version(
        self,
        block_id: str,
        previous: Optional[BlockMetadata],
        current: BlockMetadata
    ) -> str:
        """
        Generate version based on changes.

        Uses Algorithm 8 (generate_version function).

        - New block: 1.0.0
        - Metadata change: bump minor (1.0.0 -> 1.1.0)
        - Schema change: bump minor
        - No change: keep version
        """
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
    """Configuration for discovery workflow."""

    # Target project
    project_key: str

    # Output destinations
    write_to_project_registry: bool = True      # Write to source project's local registry
    register_in_blocks_registry: bool = True    # Register in BLOCKS_REGISTRY
    blocks_registry_key: str = "BLOCKS_REGISTRY"

    # Filtering
    include_zones: List[str] = field(default_factory=list)  # Whitelist (empty = all)
    exclude_zones: List[str] = field(default_factory=list)  # Blacklist

    # Metadata classification (overrides for all blocks)
    hierarchy_level: Optional[str] = None       # e.g., "equipment", "process"
    domain: Optional[str] = None                # e.g., "rotating_equipment", "etl"
    tags: List[str] = field(default_factory=list)

    # Version management
    auto_increment_version: bool = True         # Auto-bump minor version on update
    version_override: Optional[str] = None      # Force specific version for all blocks

    # Behavior options
    initialize_if_missing: bool = True          # Create registry structure if needed
    preserve_manual_edits: bool = True          # Keep Wiki customizations on re-discovery
    extract_schemas: bool = True                # Extract dataset schemas
    extract_dependencies: bool = True           # Extract Python/plugin dependencies
    dry_run: bool = False                       # Generate but don't write
```

### DiscoveryResult

```python
@dataclass
class DiscoveryResult:
    """Results of a discovery run."""

    project_key: str
    blocks_found: int

    # Change summary
    blocks_new: int = 0
    blocks_updated: int = 0
    blocks_unchanged: int = 0
    blocks_deleted: int = 0  # Found in previous but not current

    # Detailed changes
    new_blocks: List[BlockMetadata] = field(default_factory=list)
    updated_blocks: List[BlockMetadata] = field(default_factory=list)
    unchanged_blocks: List[BlockMetadata] = field(default_factory=list)
    deleted_blocks: List[BlockMetadata] = field(default_factory=list)

    # Write results
    project_write_result: Optional[Dict[str, Any]] = None
    registration_result: Optional[Dict[str, Any]] = None

    # Runtime info
    duration_seconds: float = 0.0
    dry_run: bool = False

    def summary(self) -> str:
        """Generate human-readable summary."""
        return (
            f"Discovery completed for {self.project_key}:\n"
            f"  Found: {self.blocks_found} blocks\n"
            f"  New: {self.blocks_new}, Updated: {self.blocks_updated}, "
            f"  Unchanged: {self.blocks_unchanged}, Deleted: {self.blocks_deleted}\n"
            f"  Duration: {self.duration_seconds:.1f}s"
        )
```

### ChangeSet

```python
@dataclass
class ChangeSet:
    """Set of changes between two discoveries."""

    new: List[BlockMetadata] = field(default_factory=list)
    updated: List[BlockMetadata] = field(default_factory=list)
    unchanged: List[BlockMetadata] = field(default_factory=list)
    deleted: List[BlockMetadata] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        """Count of blocks that changed (new + updated + deleted)."""
        return len(self.new) + len(self.updated) + len(self.deleted)

    @property
    def has_changes(self) -> bool:
        """True if any blocks changed."""
        return self.total_changes > 0
```

### ProjectRegistration

```python
@dataclass
class ProjectRegistration:
    """Project registration information."""

    project_key: str
    project_name: str
    registered_at: str  # ISO timestamp
    last_discovered: str  # ISO timestamp
    discovery_runs: int
    blocks_discovered: int
    blocks: List[Dict[str, Any]]  # Block summaries with links
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

### Basic Discovery (Two-Tier)

```python
from dataikuapi import DSSClient
from dataikuapi.iac.workflows.discovery import DiscoveryAgent, DiscoveryConfig

client = DSSClient("https://dss.example.com", "api_key")

agent = DiscoveryAgent(client)

# Discover project: writes to local registry + registers in BLOCKS_REGISTRY
config = DiscoveryConfig(
    project_key="HR_ANALYTICS",
    hierarchy_level="business",
    domain="hr_analytics",
    tags=["hr", "analytics"]
)

result = agent.run_discovery(config)

print(result.summary())
# Output:
# Discovery completed for HR_ANALYTICS:
#   Found: 12 blocks
#   New: 2, Updated: 3, Unchanged: 7, Deleted: 0
#   Duration: 45.2s
```

### Discovery with Zone Filtering

```python
config = DiscoveryConfig(
    project_key="PRODUCTION_ETL",
    include_zones=["data_preparation", "feature_engineering"],  # Only these
    exclude_zones=["staging", "test"],  # Skip these
    hierarchy_level="process",
    domain="etl"
)

result = agent.run_discovery(config)

for block in result.new_blocks:
    print(f"New block: {block.block_id} v{block.version}")
```

### Re-Discovery (Update with Diff)

```python
# Re-run discovery on project
config = DiscoveryConfig(
    project_key="HR_ANALYTICS",
    auto_increment_version=True,  # Auto-bump versions on changes
    preserve_manual_edits=True    # Keep manual Wiki edits
)

result = agent.run_discovery(config)

# Show what changed
if result.blocks_updated:
    print(f"\nUpdated blocks ({len(result.blocks_updated)}):")
    for block in result.blocks_updated:
        print(f"  {block.block_id}: v{block.version}")

if result.blocks_deleted:
    print(f"\nDeleted blocks ({len(result.blocks_deleted)}):")
    for block in result.blocks_deleted:
        print(f"  {block.block_id} (no longer in project)")
```

### Dry Run (Preview Changes)

```python
config = DiscoveryConfig(
    project_key="MY_PROJECT",
    dry_run=True  # Don't write, just show what would happen
)

result = agent.run_discovery(config)

print(f"Would create {result.blocks_new} new blocks")
print(f"Would update {result.blocks_updated} blocks")
```

### Project-Local Only (No BLOCKS_REGISTRY)

```python
# Write to project registry only, don't register in BLOCKS_REGISTRY
config = DiscoveryConfig(
    project_key="SANDBOX_PROJECT",
    write_to_project_registry=True,
    register_in_blocks_registry=False  # Skip central registration
)

result = agent.run_discovery(config)
```

### List Registered Projects

```python
from dataikuapi.iac.workflows.discovery import ProjectRegistrar

registrar = ProjectRegistrar(client)
projects = registrar.get_registered_projects()

for project in projects:
    print(f"{project.project_key}: {project.blocks_discovered} blocks")
    print(f"  Last discovered: {project.last_discovered}")
```
