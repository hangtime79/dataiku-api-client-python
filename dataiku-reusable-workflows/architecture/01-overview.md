# Architecture Overview

## System Context

The Dataiku Reusable Workflows System enables enterprise data science teams to shift from project-based delivery to component-based composition. It integrates with the existing Dataiku DSS platform and extends the IaC (Infrastructure as Code) engine.

---

## System Layers

### Layer 1: Dataiku DSS API

The foundation layer providing programmatic access to Dataiku resources.

**Key Capabilities Used:**
- Project CRUD and export/import
- Flow graph traversal
- Zone management
- Dataset/Recipe operations
- Wiki read/write
- Project library management
- Bundle export

**API Client Location:** `dataikuapi/dss/`

### Layer 2: IaC Engine

The existing Infrastructure as Code engine (Waves 1-3 complete, Wave 4 in progress).

**Current Capabilities:**
- YAML configuration parsing
- Validation (syntax, references, naming)
- State management (current vs desired)
- Plan generation (diff-based)
- Dependency resolution

**Extension Required:**
- Block resource type
- Solution resource type
- Block instantiation in apply phase

**IaC Location:** `dataikuapi/iac/`

### Layer 3: Catalog Layer (BLOCKS_REGISTRY)

A dedicated Dataiku project serving as the central registry.

**Components:**
- **Wiki:** Human-readable block documentation
- **Library:** Machine-parseable JSON index
- **Bundles:** Versioned, immutable block snapshots

**Structure:**
```
BLOCKS_REGISTRY/
├── Wiki/
│   └── _BLOCKS/           # Block documentation
├── Library/
│   └── blocks/
│       └── index.json     # Agent-readable index
└── Bundles/
    └── *.zip              # Versioned snapshots
```

### Layer 4: Agent Layer

Two agents that interact with the system:

**Discovery Agent:**
- Input: Dataiku project to catalog
- Process: Crawl flow, identify blocks, extract metadata
- Output: Wiki articles + JSON index in BLOCKS_REGISTRY

**Executing Agent:**
- Input: User intent + block filters
- Process: Read catalog, match blocks, resolve dependencies
- Output: IaC configuration YAML

### Layer 5: User Interface Layer

External AI coding agents (Claude Code, Codex, Gemini CLI) that:
- Take natural language input from users
- Call the Executing Agent to get configs
- Review plans with users
- Trigger apply via IaC engine

---

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           User Workflow                             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────────┐         ┌─────────────┐
│ Publish Flow  │         │ Compose Solution  │         │ Deploy Proj │
└───────┬───────┘         └─────────┬─────────┘         └──────┬──────┘
        │                           │                          │
        ▼                           ▼                          ▼
┌───────────────┐         ┌───────────────────┐         ┌─────────────┐
│   Discovery   │         │    Executing      │         │    IaC      │
│     Agent     │         │      Agent        │         │   Engine    │
└───────┬───────┘         └─────────┬─────────┘         └──────┬──────┘
        │                           │                          │
        │                           │                          │
        ▼                           ▼                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        BLOCKS_REGISTRY                              │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │
│  │    Wiki     │  │     Library     │  │        Bundles          │ │
│  │             │  │                 │  │                         │ │
│  │ Block docs  │  │  index.json     │  │  BLOCK_v1.0.0.zip       │ │
│  │ (human)     │  │  schemas/       │  │  BLOCK_v1.1.0.zip       │ │
│  │             │  │  (machine)      │  │  (immutable)            │ │
│  └─────────────┘  └─────────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Dataiku DSS API                             │
│  Projects | Datasets | Recipes | Zones | Wiki | Library | Bundles  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Workflow Sequences

### Workflow 1: Publish a Block

```
1. User identifies a zone to publish in their project
2. User runs Discovery Agent on their project
3. Discovery Agent:
   a. Connects to source project
   b. Traverses flow graph
   c. Identifies zone as block candidate
   d. Extracts inputs/outputs from zone boundary
   e. Extracts internal datasets/recipes
   f. Extracts dependencies (Python, plugins)
   g. Generates block metadata
   h. Writes Wiki article to BLOCKS_REGISTRY
   i. Updates JSON index in BLOCKS_REGISTRY library
   j. (Optional) Creates bundle snapshot
4. Block is now available in catalog
```

### Workflow 2: Compose a Solution

```
1. User describes intent to their AI coding agent
   "I need compressor monitoring for Plant X"
2. AI agent calls Executing Agent with:
   - Intent description
   - Filters (hierarchy level, domain, blocked-only)
3. Executing Agent:
   a. Reads JSON index from BLOCKS_REGISTRY
   b. Matches intent to available blocks
   c. Identifies: FEATURE_ENG, ANOMALY_DETECTION blocks
   d. Resolves dependencies between blocks
   e. Generates IaC configuration YAML
4. AI agent presents plan to user
5. User reviews, requests changes
6. User approves
7. AI agent calls IaC engine with config
8. IaC engine:
   a. Validates configuration
   b. Generates plan (what will be created)
   c. User confirms apply
   d. Creates new project
   e. Instantiates blocks as zones
   f. Wires block outputs to inputs
   g. Creates any custom datasets/recipes
9. New project is deployed
```

### Workflow 3: Extend a Block

```
1. User references a block in their IaC config
2. User adds `extends:` section to override a recipe
3. User defines override recipe in `recipes:` section
4. IaC engine:
   a. Validates override recipe has compatible I/O
   b. Instantiates block
   c. Replaces specified recipe with override
   d. Wires everything together
5. Block is instantiated with customization
```

---

## Data Models

### Block Metadata

```python
@dataclass
class BlockMetadata:
    block_id: str              # Unique identifier
    version: str               # Semantic version
    type: BlockType            # zone | solution
    blocked: bool              # Protected flag

    source_project: str        # Origin project key
    source_zone: str           # Origin zone name

    hierarchy_level: str       # Organization-defined
    domain: str                # Business domain
    tags: List[str]            # Searchable tags

    inputs: List[BlockPort]    # Input definitions
    outputs: List[BlockPort]   # Output definitions

    contains: BlockContents    # Internal datasets/recipes
    dependencies: Dependencies # Python packages, plugins

    bundle_ref: Optional[str]  # Path to bundle snapshot

    created_at: datetime
    updated_at: datetime
    created_by: str
```

### Block Port (Input/Output)

```python
@dataclass
class BlockPort:
    name: str                  # Port name
    type: PortType             # dataset | model | folder
    schema_ref: Optional[str]  # Path to schema definition
    required: bool             # For inputs only
    description: str           # Human-readable
```

### Block Contents

```python
@dataclass
class BlockContents:
    datasets: List[str]        # Internal dataset names
    recipes: List[str]         # Internal recipe names
    models: List[str]          # Internal model IDs
```

### Block Reference (in IaC config)

```python
@dataclass
class BlockReference:
    ref: str                   # "REGISTRY/BLOCK_ID@VERSION"
    instance_name: str         # Local instance name
    zone_name: str             # Target zone name

    inputs: Dict[str, str]     # Port name -> local dataset
    outputs: Dict[str, str]    # Port name -> local dataset

    extends: List[RecipeOverride]  # Optional overrides
```

---

## Integration with Existing IaC

### Config Parser Extension

The existing parser at `dataikuapi/iac/config/parser.py` will be extended to handle:

```yaml
# New top-level sections
blocks:
  - ref: "..."
    # ...

solutions:
  - ref: "..."
    # ...
```

### State Model Extension

The existing state model at `dataikuapi/iac/models/state.py` will add:

```python
class ResourceType(Enum):
    PROJECT = "project"
    DATASET = "dataset"
    RECIPE = "recipe"
    BLOCK = "block"          # NEW
    SOLUTION = "solution"    # NEW
```

### Validation Extension

The validator at `dataikuapi/iac/config/validator.py` will add:

- Block reference format validation
- Version format validation
- Input/output compatibility validation
- Override recipe I/O validation
- Circular dependency detection for solutions

### Plan Engine Extension

The planner at `dataikuapi/iac/planner/engine.py` will add:

- Block instantiation operations
- Solution expansion operations
- Cross-block wiring operations

---

## Security Considerations

### Block Protection

- `blocked: true` blocks cannot have their source modified
- Source project should have restricted permissions
- Bundle snapshots provide immutable versions

### Registry Access

- BLOCKS_REGISTRY project has read access for all users
- Write access limited to block publishers
- Bundle creation requires special permissions

### API Key Handling

- Follows existing IaC patterns for API key management
- Keys stored in `config/APIKEY.txt` (never committed)
- Environment variable support for CI/CD

---

## Performance Considerations

### Catalog Size

- JSON index kept under 1MB for fast parsing
- Full block details in separate Wiki articles
- Pagination for large catalogs

### Crawling

- Incremental crawl option (only changed zones)
- Caching of project metadata
- Parallel schema extraction

### Block Instantiation

- Lazy loading of bundle contents
- Parallel zone creation
- Progress reporting for long operations

---

## Error Recovery

### Discovery Agent

- Atomic writes (temp file + rename)
- Preserves previous index on failure
- Detailed error logging

### Executing Agent

- Graceful degradation (partial matches)
- Suggestions on no match
- Clear error messages

### IaC Apply

- Follows Wave 4 checkpointing design
- Rollback on failure
- State preserved for recovery

---

## Future Extensions

### Phase 2 Possibilities

1. **Cross-Instance Sharing** - Blocks shared between DSS instances
2. **Automatic Discovery** - Background crawl of all projects
3. **Block Marketplace** - Curated, rated blocks
4. **Govern Integration** - Workflow approval for block publishing
5. **Update Propagation** - Notify consumers of block updates
6. **Visual Composer** - UI for block composition
