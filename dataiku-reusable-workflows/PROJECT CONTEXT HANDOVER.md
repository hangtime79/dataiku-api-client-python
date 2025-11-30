# PROJECT CONTEXT HANDOVER

## Document Purpose

This document is a complete context transfer for the **Dataiku Reusable Workflows - Discovery Agent Enhancement** project. A fresh AI instance receiving this document, along with the `FEATURE_DECOMPOSITION_GUIDE.md` and `FEATURE_SPEC_TEMPLATE.md`, should be able to immediately generate all Feature Specifications for all Phases without requesting clarification.

**Document Version:** 1.0 **Created:** November 30, 2025 **Status:** Ready for handover

------

# SECTION 1: PROJECT CORE

## 1.1 High-Level Objective

Build extensions to the Dataiku API client (`dataiku/dataiku-api-client-python` fork) that enable **agent-based development workflows**. The system allows AI coding agents (Claude Code, Gemini CLI, Qwen Coder, etc.) to discover, understand, and compose reusable workflow components within Dataiku projects.

## 1.2 User Persona

**Name:** Grant **Role:** Field Chief Data Officer for APJ at Dataiku (7.5 years tenure) **Technical Level:** Can hack code but is not a professional developer **Working Style:**

- Solo developer, exploratory R&D (no timeline pressure)
- Needs structure and guidance for decomposition
- Works top-down (architecture) AND bottom-up (seeing outputs to react)
- Prefers markdown documentation in repo
- Uses GitHub for version control and project tracking

**Key Constraint:** "I need structure. I'm not a developer, I can hack code, but I need structure."

**What Grant Can Do:**

- ✅ Envision high-level architecture
- ✅ Write integration tests to validate outcomes
- ✅ Create good documentation when guided
- ✅ Implement code when given clear specs

**What Grant Struggles With:**

- ❌ Breaking down large features into granular specs at scale
- ❌ Keeping Claude Code sessions within context limits
- ❌ Determining appropriate boundaries for "one feature"

## 1.3 Value Proposition

Enable Grant to delegate implementation work to multiple AI coding agents working in parallel, without context overflow, by providing:

1. A systematic process for decomposing phases into atomic features
2. Feature specs explicit enough for less capable models (Haiku, Qwen) to execute
3. Independence between features enabling parallel development on separate branches

## 1.4 The Three Interconnected Extensions

Grant is building three major capabilities. They are related but can function independently:

### Extension 1: Discovery Agent (CURRENT FOCUS)

**Purpose:** Inventory Dataiku projects and reusable block components in a Claude.md-style format that coding agents can understand and navigate.

**Location:** `/dataikuapi/iac/workflows/discovery/`

**Key Characteristics:**

- Library component (NOT a CLI tool)
- Generates scannable, modular Wiki documentation
- Enables Executor Agent to understand "what exists" without scanning entire platform
- Writes to project-local registries + registers in BLOCKS_REGISTRY

**Current Status:** Phase 1 complete (2,598 LOC, 37 passing tests). Phase 2 enhancement plan approved, ready for implementation.

### Extension 2: Executor Agent (FUTURE)

**Purpose:** Use Discovery output to build/deploy new Dataiku components via CLI coding platforms.

**Key Characteristics:**

- Consumes Discovery Agent output
- Traverses existing projects and reusable components
- Builds and deploys new components on the fly
- CLI-driven interaction model

**Status:** Conceptual/architectural phase only.

### Extension 3: Infrastructure as Code (IaC) (INDEPENDENT)

**Purpose:** Terraform/dbt-style declarative configuration for Dataiku components.

**Location:** `/dataikuapi/iac/`

**Key Characteristics:**

- Declarative YAML configs
- Project-based and CI/CD-ready
- Drift detection at project level
- Independent tool (separate from agent components)

**Status:** Well developed, extensive implementation exists.

------

# SECTION 2: ARCHITECTURE & TECH STACK

## 2.1 Repository Structure

```
dataiku-api-client-python/
├── dataikuapi/
│   ├── iac/                          # IaC component (well developed)
│   │   ├── backends/
│   │   ├── cli/
│   │   ├── config/
│   │   ├── models/
│   │   ├── planner/
│   │   ├── workflows/
│   │   │   └── discovery/            # ← DISCOVERY AGENT LIVES HERE
│   │   │       ├── __init__.py       # Package exports
│   │   │       ├── agent.py          # DiscoveryAgent orchestrator (218 LOC)
│   │   │       ├── crawler.py        # FlowCrawler (406 LOC)
│   │   │       ├── identifier.py     # BlockIdentifier (454 LOC)
│   │   │       ├── schema_extractor.py # SchemaExtractor (250 LOC)
│   │   │       ├── catalog_writer.py # CatalogWriter (706 LOC)
│   │   │       ├── models.py         # Data models (444 LOC)
│   │   │       └── exceptions.py     # Custom exceptions (83 LOC)
│   │   └── ...
│   └── dss/                          # Base Dataiku DSS API
│
├── docs/                             # IaC-focused docs
├── dataiku-reusable-workflows/       # Block architecture docs
│   ├── architecture/
│   ├── components/
│   │   ├── discovery-agent/
│   │   ├── executing-agent/
│   │   └── iac-extension/
│   └── schemas/
├── dataiku_framework_reference/      # API reference materials
├── claude-guides/                    # Agent interaction guides
└── tests/
    └── iac/
        └── discovery/                # Discovery Agent tests
            ├── unit/                 (2,925 LOC, 20 tests)
            └── integration/          (1,880 LOC, 17 tests)
```

## 2.2 Technology Stack

| Component       | Technology                                    |
| --------------- | --------------------------------------------- |
| Language        | Python 3.10+                                  |
| API Client      | dataikuapi (Dataiku's official Python client) |
| Testing         | pytest with pytest-cov                        |
| Formatting      | black                                         |
| Type Hints      | Required on all functions/methods             |
| Docstrings      | Google style                                  |
| Version Control | Git with feature branch workflow              |

## 2.3 Key Dataiku API Patterns

The Discovery Agent uses these Dataiku API patterns:

```python
# Get project
project = client.get_project(project_key)

# Get flow and zones
flow = project.get_flow()
zones = flow.list_zones()
zone = flow.get_zone(zone_name)

# Get zone items
zone.items  # List of {"type": "DATASET", "id": "name"} or {"type": "RECIPE", "id": "name"}

# Get dataset
dataset = project.get_dataset(dataset_name)
settings = dataset.get_settings()
schema = dataset.get_schema()

# Get recipe
recipe = project.get_recipe(recipe_name)
settings = recipe.get_settings()

# Project library (for writing discovery output)
library = project.get_library()
root = library.root
folder = root.get_child("folder_name")
folder = root.add_folder("new_folder")
file = folder.add_file("filename.json")
file.write(content_string)
content = file.read()

# Project wiki (for writing documentation)
wiki = project.get_wiki()
wiki.create_article(path, content)
article = wiki.get_article(path)
article.get_body()
article.set_body(new_content)
```

## 2.4 Data Models (Current - Phase 1)

Located in `dataikuapi/iac/workflows/discovery/models.py`:

```python
@dataclass
class BlockPort:
    """Input/Output port definition."""
    name: str
    type: str  # "dataset", "model", "folder"
    required: bool = True
    description: str = ""
    schema_ref: Optional[str] = None

@dataclass
class BlockContents:
    """Internal block resources."""
    datasets: List[str] = field(default_factory=list)
    recipes: List[str] = field(default_factory=list)
    models: List[str] = field(default_factory=list)

@dataclass
class BlockMetadata:
    """Core block representation."""
    block_id: str
    version: str
    type: str  # "zone" or "solution"
    source_project: str
    blocked: bool = False
    name: str = ""
    description: str = ""
    hierarchy_level: str = ""
    domain: str = ""
    tags: List[str] = field(default_factory=list)
    source_zone: str = ""
    inputs: List[BlockPort] = field(default_factory=list)
    outputs: List[BlockPort] = field(default_factory=list)
    contains: BlockContents = field(default_factory=BlockContents)
    dependencies: Dict[str, Any] = field(default_factory=dict)
    bundle_ref: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: str = ""

@dataclass
class BlockSummary:
    """Lightweight summary for catalog index."""
    block_id: str
    version: str
    type: str
    name: str = ""
    description: str = ""
    hierarchy_level: str = ""
    domain: str = ""
    tags: List[str] = field(default_factory=list)
    blocked: bool = False
    inputs: List[Dict[str, Any]] = field(default_factory=list)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    manifest_path: str = ""
```

## 2.5 Data Models (Planned - Phase 2 Enhancement)

These models need to be created in Phase 0:

```python
@dataclass
class DatasetDetail:
    """Rich dataset metadata."""
    name: str
    type: str  # "Snowflake", "S3", "PostgreSQL", etc.
    connection: str
    format_type: str  # "parquet", "csv", etc.
    schema_summary: Dict  # {column_count: 50, sample_cols: ["ID", "NAME", ...]}
    partitioning: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    description: str = ""
    estimated_size: Optional[str] = None  # "1.2GB", "unknown"
    last_built: Optional[str] = None

@dataclass
class RecipeDetail:
    """Rich recipe metadata."""
    name: str
    type: str  # "python", "sql", "sync", etc.
    engine: str  # "DSS", "Spark", "Snowflake", etc.
    inputs: List[str]  # Dataset names
    outputs: List[str]  # Dataset names
    description: str = ""
    tags: List[str] = field(default_factory=list)
    code_snippet: Optional[str] = None  # First 10 lines for context
    config_summary: Dict = field(default_factory=dict)

@dataclass
class LibraryReference:
    """Project library reference."""
    name: str
    type: str  # "python", "R"
    description: str = ""

@dataclass
class NotebookReference:
    """Project notebook reference."""
    name: str
    type: str  # "jupyter", "SQL"
    description: str = ""
    tags: List[str] = field(default_factory=list)

@dataclass
class EnhancedBlockMetadata(BlockMetadata):
    """Extended metadata with rich component details."""
    dataset_details: List[DatasetDetail] = field(default_factory=list)
    recipe_details: List[RecipeDetail] = field(default_factory=list)
    library_refs: List[LibraryReference] = field(default_factory=list)
    notebook_refs: List[NotebookReference] = field(default_factory=list)
    flow_graph: Optional[Dict] = None  # Simplified graph for visualization
    estimated_complexity: str = ""  # "simple", "moderate", "complex"
    estimated_size: str = ""  # Total data volume estimate
```

## 2.6 Discovery Agent Architecture

```
DiscoveryAgent (orchestrator) - agent.py
  │
  ├──> FlowCrawler (discovers projects/zones/datasets/recipes) - crawler.py
  │     └─ Methods: list_zones(), get_zone_items(), build_dependency_graph()
  │                 analyze_zone_boundary(), get_dataset_upstream/downstream()
  │
  ├──> BlockIdentifier (identifies block boundaries) - identifier.py
  │     └─ Methods: identify_blocks(), is_valid_block(), extract_block_metadata()
  │                 generate_block_id(), create_block_ports()
  │
  ├──> SchemaExtractor (extracts dataset schemas) - schema_extractor.py
  │     └─ Methods: extract_schema(), map_dataiku_type_to_standard()
  │                 enrich_block_with_schemas(), validate_schema()
  │
  └──> CatalogWriter (persists to Wiki + Library) - catalog_writer.py
        └─ Methods: generate_wiki_article(), generate_block_summary()
                    merge_catalog_index(), write_to_project_registry()
```

## 2.7 Output Structure (Project-Local Registry)

When Discovery Agent runs on a project, it writes to:

```
TARGET_PROJECT/
├── Wiki/
│   └── _DISCOVERED_BLOCKS/
│       └── {BLOCK_ID}.md           # Wiki article per block
│
└── Library/
    └── discovery/
        ├── index.json              # Master catalog index
        ├── metadata.json           # Discovery run metadata
        └── schemas/
            └── {BLOCK_ID}_{PORT}.schema.json
```

## 2.8 Enhanced Wiki Structure (Phase 2 Target)

The Phase 2 enhancement will generate CLAUDE.md-style wiki articles:

~~~markdown
---
block_id: FEATURE_ENGINEERING
version: 1.0.0
type: zone
---

# Feature Engineering Block

> **Quick Summary**: Transforms raw sensor data into ML-ready features
> **Complexity**: Moderate | **Data Volume**: ~2.5GB | **Recipes**: 5

## 🗺️ Quick Navigation

- [Overview](#overview)
- [Inputs & Outputs](#inputs--outputs)
- [Internal Components](#internal-components)
  - [Datasets (12)](#datasets)
  - [Recipes (5)](#recipes)
  - [Libraries](#project-libraries)
- [Flow Diagram](#flow-diagram)
- [Usage Guide](#usage-guide)
- [Technical Details](#technical-details)

---

## Internal Components

### Datasets

<details>
<summary><b>12 internal datasets</b> - Click to expand</summary>

#### `SMOOTHED_READINGS` (Snowflake, partitioned by sensor_id)
- **Purpose**: Noise-reduced sensor readings
- **Schema**: 52 columns (see [schema file](schemas/...))
- **Size**: ~800MB
- **Tags**: `intermediate`, `time-series`

</details>

### Recipes

<details>
<summary><b>5 recipes</b> - Click to expand</summary>

#### `smooth_signal` (Python/Pandas)
**Purpose**: Apply moving average smoothing
**Inputs**: RAW_SENSOR_DATA
**Outputs**: SMOOTHED_READINGS
**Logic Preview**:
```python
df['smooth_value'] = df.groupby('sensor_id')['value'].rolling(window=10).mean()
~~~

</details>

## Flow Diagram

```mermaid
graph LR
    RAW[RAW_SENSOR_DATA] --> smooth[smooth_signal]
    smooth --> SMOOTH[SMOOTHED_READINGS]
    ...
---

# SECTION 3: THE MASTER PLAN (PHASING)

## 3.1 Phase Overview

The Discovery Agent Enhancement Plan has **13 phases** (Phase 0-12). Each phase is designed to be independent and can be implemented/tested separately.

## 3.2 Phase Definitions

### Phase 0: Foundation (Data Models)
**Goal:** Create extensible data models for rich metadata
**Dependencies:** None
**Deliverable:** New dataclasses in `models.py`

**Tasks:**
- Create `DatasetDetail` dataclass with serialization (to_dict/from_dict)
- Create `RecipeDetail` dataclass with serialization
- Create `LibraryReference` dataclass with serialization
- Create `NotebookReference` dataclass with serialization
- Create `EnhancedBlockMetadata` extending `BlockMetadata`
- Write unit tests for model serialization

**Files to Modify:** `dataikuapi/iac/workflows/discovery/models.py`
**Estimated LOC:** ~150

---

### Phase 1: Dataset Metadata Extraction
**Goal:** Capture rich dataset metadata from Dataiku API
**Dependencies:** Phase 0 (DatasetDetail model)
**Deliverable:** `_extract_dataset_details()` method in `identifier.py`

**Tasks:**
- Implement `_extract_dataset_details(project, dataset_names)` in `identifier.py`
- Extract: type, connection, format_type from dataset settings
- Implement `_summarize_schema()` helper (column_count, sample columns)
- Extract tags, description from dataset settings
- Add error handling for inaccessible datasets
- Integrate into `extract_block_metadata()` method
- Write unit tests with mocked DSSClient

**Files to Modify:** `dataikuapi/iac/workflows/discovery/identifier.py`
**Estimated LOC:** ~80

---

### Phase 2: Recipe Metadata Extraction
**Goal:** Capture rich recipe metadata from Dataiku API
**Dependencies:** Phase 0 (RecipeDetail model)
**Deliverable:** `_extract_recipe_details()` method in `identifier.py`

**Tasks:**
- Implement `_extract_recipe_details(project, recipe_names)` in `identifier.py`
- Extract: type, engine from recipe settings
- Extract inputs/outputs from recipe definition
- Extract description, tags from recipe metadata
- Implement `_extract_code_snippet()` (first 10 lines)
- Add error handling for inaccessible recipes
- Integrate into `extract_block_metadata()` method
- Write unit tests with mocked recipes

**Files to Modify:** `dataikuapi/iac/workflows/discovery/identifier.py`
**Estimated LOC:** ~80

---

### Phase 3: Libraries & Notebooks Extraction
**Goal:** Capture project libraries and notebooks
**Dependencies:** Phase 0 (LibraryReference, NotebookReference models)
**Deliverable:** `_extract_library_refs()` and `_extract_notebook_refs()` in `identifier.py`

**Tasks:**
- Implement `_extract_library_refs(project)` in `identifier.py`
- Implement `_extract_notebook_refs(project)` in `identifier.py`
- Extract library names, types, descriptions from project
- Extract notebook names, types, tags from project
- Add error handling for missing libraries/notebooks
- Integrate into `extract_block_metadata()` method
- Write unit tests with mocked project

**Files to Modify:** `dataikuapi/iac/workflows/discovery/identifier.py`
**Estimated LOC:** ~60

---

### Phase 4: Flow Graph Extraction
**Goal:** Extract flow graph data for visualization
**Dependencies:** Phase 0 (EnhancedBlockMetadata model)
**Deliverable:** `_extract_flow_graph()` method in `identifier.py`

**Tasks:**
- Implement `_extract_flow_graph(boundary)` in `identifier.py`
- Convert boundary data to simplified graph structure
- Create node list (datasets, recipes)
- Create edge list (recipe inputs/outputs)
- Optimize for Mermaid rendering
- Integrate into `extract_block_metadata()` method
- Write unit tests with sample boundary data

**Files to Modify:** `dataikuapi/iac/workflows/discovery/identifier.py`
**Estimated LOC:** ~50

---

### Phase 5: Wiki Quick Summary Generation
**Goal:** Add quick summary box at top of Wiki articles
**Dependencies:** Phase 0 (EnhancedBlockMetadata model)
**Deliverable:** `_generate_quick_summary()` method in `catalog_writer.py`

**Tasks:**
- Implement `_generate_quick_summary(metadata)` in `catalog_writer.py`
- Generate complexity estimate from component counts
- Calculate estimated data volume from dataset details
- Format as blockquote with key metrics
- Integrate into `generate_wiki_article()` method
- Write unit tests for summary generation

**Files to Modify:** `dataikuapi/iac/workflows/discovery/catalog_writer.py`
**Estimated LOC:** ~30

---

### Phase 6: Wiki Navigation Menu Generation
**Goal:** Add quick navigation menu for scannability
**Dependencies:** None (uses existing BlockMetadata)
**Deliverable:** `_generate_navigation_menu()` method in `catalog_writer.py`

**Tasks:**
- Implement `_generate_navigation_menu(metadata)` in `catalog_writer.py`
- Generate section links based on available metadata
- Add component counts to navigation (e.g., "Datasets (12)")
- Format as markdown list with anchor links
- Integrate into `generate_wiki_article()` method
- Write unit tests for navigation generation

**Files to Modify:** `dataikuapi/iac/workflows/discovery/catalog_writer.py`
**Estimated LOC:** ~30

---

### Phase 7: Wiki Components Section Generation
**Goal:** Generate detailed components section with collapsible details
**Dependencies:** Phases 1, 2, 3 (DatasetDetail, RecipeDetail, LibraryReference, NotebookReference)
**Deliverable:** `_generate_components_section()` method in `catalog_writer.py`

**Tasks:**
- Implement `_generate_components_section(metadata)` in `catalog_writer.py`
- Generate datasets subsection with collapsible details
- Generate recipes subsection with code previews
- Generate libraries subsection
- Generate notebooks subsection
- Format with HTML details/summary tags
- Integrate into `generate_wiki_article()` method
- Write unit tests for component section generation

**Files to Modify:** `dataikuapi/iac/workflows/discovery/catalog_writer.py`
**Estimated LOC:** ~100

---

### Phase 8: Wiki Flow Diagram Generation
**Goal:** Add Mermaid flow diagram visualization
**Dependencies:** Phase 4 (flow_graph data)
**Deliverable:** `_generate_flow_diagram()` method in `catalog_writer.py`

**Tasks:**
- Implement `_generate_flow_diagram(flow_graph)` in `catalog_writer.py`
- Convert flow_graph to Mermaid syntax
- Format nodes (datasets vs recipes)
- Format edges (data flow)
- Add mermaid code block wrapper
- Integrate into `generate_wiki_article()` method
- Write unit tests for Mermaid generation

**Files to Modify:** `dataikuapi/iac/workflows/discovery/catalog_writer.py`
**Estimated LOC:** ~40

---

### Phase 9: Wiki Technical Details Section
**Goal:** Add collapsible technical details section
**Dependencies:** Phase 1 (schema summaries)
**Deliverable:** `_generate_technical_details()` method in `catalog_writer.py`

**Tasks:**
- Implement `_generate_technical_details(metadata)` in `catalog_writer.py`
- Generate schema detail tables for inputs/outputs
- Add links to full schema JSON files
- Format with collapsible details/summary
- Integrate into `generate_wiki_article()` method
- Write unit tests for technical section generation

**Files to Modify:** `dataikuapi/iac/workflows/discovery/catalog_writer.py`
**Estimated LOC:** ~50

---

### Phase 10: Enhanced I/O Section
**Goal:** Enhance inputs/outputs table with schema links
**Dependencies:** Phase 1 (DatasetDetail for ports)
**Deliverable:** Enhanced `_generate_io_section()` in `catalog_writer.py`

**Tasks:**
- Enhance `_generate_io_section(metadata)` in `catalog_writer.py`
- Add dataset type column to tables
- Add schema column with anchor links
- Link to schema details section
- Write unit tests for enhanced I/O tables

**Files to Modify:** `dataikuapi/iac/workflows/discovery/catalog_writer.py`
**Estimated LOC:** ~30

---

### Phase 11: Integration Testing
**Goal:** Test complete enhanced discovery on real project
**Dependencies:** All previous phases
**Deliverable:** Validated Wiki articles in test project (COALSHIPPINGSIMULATIONGSC)

**Tasks:**
- Run enhanced discovery on COALSHIPPINGSIMULATIONGSC
- Verify all Wiki sections present
- Verify collapsible sections work in Dataiku UI
- Verify schema links work
- Verify Mermaid diagrams render
- Test scannability (can understand in <30s)
- Iterate based on feedback

**Files to Create:** `tests/iac/workflows/discovery/integration/test_enhanced_discovery.py`
**Estimated LOC:** ~100

---

### Phase 12: Documentation
**Goal:** Document new capabilities
**Dependencies:** Phase 11 (verified working)
**Deliverable:** Updated README and examples

**Tasks:**
- Update README with new Wiki structure
- Add "Before/After" examples
- Document metadata extraction approach
- Document scannability features
- Update Phase 1 completion criteria

**Files to Modify:** Various documentation files
**Estimated LOC:** N/A (documentation)

---

## 3.3 Phase Dependency Graph
```

Phase 0 (Foundation) │ ├─────────────────────────────────────────────┐ │                     │                       │ ▼                     ▼                       ▼ Phase 1              Phase 2                 Phase 3 (Dataset)            (Recipe)                (Lib/Notebook) │                     │                       │ ├─────────────────────┼───────────────────────┤ │                     │                       │ ▼                     ▼                       ▼ Phase 5              Phase 4                 Phase 6 (no deps) (Quick Summary)      (Flow Graph)            (Nav Menu) │                     │ │                     ▼ │                Phase 8 │                (Flow Diagram) │ ├─────────────────────────────────────────────┐ ▼                                             ▼ Phase 9                                      Phase 10 (Tech Details)                               (Enhanced I/O) │                                             │ └──────────────────┬──────────────────────────┘ │ ▼ Phase 7 (Components Section) │ ▼ Phase 11 (Integration Testing) │ ▼ Phase 12 (Documentation)

```
## 3.4 Parallelism Opportunities

**Can start immediately (no dependencies):**
- Phase 0: Foundation
- Phase 6: Wiki Navigation Menu

**After Phase 0:**
- Phase 1, 2, 3, 4, 5 can ALL run in parallel

**After Phase 1:**
- Phase 9, Phase 10 can run in parallel

**After Phase 4:**
- Phase 8 can start

**After Phases 1, 2, 3:**
- Phase 7 can start

**Sequential at end:**
- Phase 11 → Phase 12

---

# SECTION 4: IMPLICIT CONTEXT & RULES

## 4.1 Coding Standards

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Block ID | UPPERCASE_WITH_UNDERSCORES | `FEATURE_ENGINEERING` |
| Method names | lowercase_with_underscores | `_extract_dataset_details` |
| Class names | PascalCase | `DatasetDetail` |
| Private methods | Leading underscore | `_summarize_schema` |
| Constants | UPPERCASE | `DEFAULT_VERSION = "1.0.0"` |

### Docstring Format

Use Google-style docstrings:

```python
def method_name(self, param1: str, param2: List[str]) -> Dict[str, Any]:
    """
    One-line summary.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ExceptionType: When this happens

    Example:
        >>> result = obj.method_name("value", ["a", "b"])
        >>> print(result)
        {'key': 'value'}
    """
```

### Type Hints

Required on ALL:

- Function parameters
- Return types
- Class attributes in dataclasses

### Error Handling Pattern

Use custom exceptions from `exceptions.py`:

```python
from dataikuapi.iac.workflows.discovery.exceptions import SchemaExtractionError

try:
    schema = dataset.get_schema()
except Exception as e:
    raise SchemaExtractionError(
        f"Failed to extract schema from {dataset_name}: {e}"
    ) from e
```

### Serialization Pattern

All dataclasses must have `to_dict()` and `from_dict()` methods:

```python
@dataclass
class MyModel:
    field1: str
    field2: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field1": self.field1,
            "field2": self.field2,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MyModel":
        return cls(
            field1=data["field1"],
            field2=data.get("field2", 0),  # Default if missing
        )
```

## 4.2 Testing Standards

### Test File Location

```
tests/iac/workflows/discovery/
├── unit/
│   ├── test_models.py
│   ├── test_crawler.py
│   ├── test_identifier.py
│   ├── test_schema_extractor.py
│   └── test_catalog_writer.py
└── integration/
    ├── test_discovery_real.py
    └── conftest.py  # Real Dataiku fixtures
```

### Test Naming

```python
def test_method_name_scenario():
    """Test [method] when [scenario]."""
```

Examples:

- `test_extract_dataset_details_basic()`
- `test_extract_dataset_details_empty_input()`
- `test_extract_dataset_details_missing_schema()`

### Test Structure (AAA Pattern)

```python
def test_something(self, mock_fixture):
    """Test description."""
    # Arrange
    input_data = {...}
    expected = {...}

    # Act
    result = instance.method(input_data)

    # Assert
    assert result == expected
```

### Mock Patterns

Mock at the API boundary (DSSClient), not internal methods:

```python
@pytest.fixture
def mock_project():
    project = Mock()
    project.get_dataset.return_value = mock_dataset
    return project

@pytest.fixture
def mock_dataset():
    dataset = Mock()
    dataset.get_settings.return_value = Mock(
        get_raw=lambda: {"type": "PostgreSQL", "params": {"connection": "WAREHOUSE"}}
    )
    dataset.get_schema.return_value = {
        "columns": [
            {"name": "id", "type": "bigint"},
            {"name": "value", "type": "double"}
        ]
    }
    return dataset
```

### Integration Test Markers

```python
@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("USE_REAL_DATAIKU") != "true",
    reason="Set USE_REAL_DATAIKU=true to run"
)
def test_real_dataiku_connection(real_client):
    """Test against real Dataiku instance."""
```

## 4.3 Git Workflow

### Branch Naming

```
feature/P{phase}-F{feature}-{short-description}

Examples:
feature/P0-F001-dataset-detail-model
feature/P1-F003-extract-dataset-properties
```

### Commit Message Format

```
feat(discovery): Add {short description}

- Implements P{phase}-F{feature}: {Feature Name}
- [Brief description of what was added]

Part of Phase {N}: {Phase Name}
```

### Merge Strategy

1. Feature branches merge to `Reusable_Workflows`
2. Use fast-forward merges when possible
3. Run full test suite before merge
4. Tag releases after phase completion

## 4.4 Wiki Generation Rules

### Frontmatter (YAML)

Always include at top of generated wiki articles:

```yaml
---
block_id: BLOCK_NAME
version: 1.0.0
type: zone
blocked: false
source_project: PROJECT_KEY
source_zone: zone_name
hierarchy_level: equipment
domain: analytics
tags: ["tag1", "tag2"]
---
```

### Collapsible Sections

Use HTML for collapsible content (supported in Dataiku Wiki):

```html
<details>
<summary><b>Section Title</b> - Click to expand</summary>

Content goes here...

</details>
```

### Mermaid Diagrams

Dataiku Wiki supports Mermaid. Use `graph LR` for flow diagrams:

~~~markdown
```mermaid
graph LR
    INPUT[Input Dataset] --> recipe[recipe_name]
    recipe --> OUTPUT[Output Dataset]
### Schema References

Link to schema files in Library:

```markdown
**Schema**: 52 columns (see [schema file](schemas/BLOCK_ID_DATASET.schema.json))
~~~

## 4.5 Feature Spec Rules

### Target Size

- **15-30 lines of implementation code** (excluding tests)
- **1-2 files modified** per feature
- **1 clear purpose** per feature

### Independence

Features should be implementable without requiring other features to be complete, wherever possible. When dependencies exist, they must be explicit.

### Explicit Boundaries

Every feature spec must include:

- `DO NOT TOUCH` list of files
- `READ ONLY` list of files
- Exact method signatures
- Exact test assertions

### Validation Path

Every feature must have:

1. Unit test (always)
2. Integration test (when touching external APIs)
3. Quick sanity check (always)

------

# SECTION 5: THE "BRIDGE" INSTRUCTION

## Instructions for the Next AI Instance

You are receiving this document along with two companion files:

1. `FEATURE_DECOMPOSITION_GUIDE.md` - The process for breaking phases into features
2. `FEATURE_SPEC_TEMPLATE.md` - The template for each feature specification

### Your Task

Generate ALL Feature Specifications for ALL 13 Phases (Phase 0 through Phase 12) of the Discovery Agent Enhancement Plan.

### How to Execute

1. **Read this document completely** to understand:
   - The project structure and architecture
   - The existing code that features will modify
   - The data models and their relationships
   - The coding standards and conventions
2. **Read the Feature Decomposition Guide** to understand:
   - The 5-step decomposition process
   - How to identify dependencies
   - How to maximize parallelism
   - Feature sizing guidelines
3. **For each Phase**, apply the decomposition process:
   - List all outputs (methods, classes, tests)
   - Identify dependencies between outputs
   - Group into features of ~15-30 LOC
   - Maximize parallelism
4. **For each Feature**, use the template to create a complete spec:
   - Fill in ALL sections
   - Be explicit about file paths
   - Include exact method signatures
   - Include exact test assertions
   - Include quick sanity check with expected output

### Output Structure

Create feature specs in this directory structure:

```
features/
├── phase-0/
│   ├── P0-F001-dataset-detail-model.md
│   ├── P0-F002-recipe-detail-model.md
│   ├── P0-F003-library-reference-model.md
│   ├── P0-F004-notebook-reference-model.md
│   └── P0-F005-enhanced-block-metadata.md
├── phase-1/
│   ├── P1-F001-...
│   └── ...
├── phase-2/
│   └── ...
...
└── phase-12/
    └── ...
```

### Quality Checklist

Before considering a feature spec complete, verify:

- [ ] Feature ID follows format `P{phase}-F{number}`
- [ ] Estimated LOC is 15-30 (flag if outside range)
- [ ] Context is 2-3 sentences max
- [ ] IN SCOPE has specific checkboxes
- [ ] OUT OF SCOPE has explicit "DO NOT" statements
- [ ] Dependencies list specific feature IDs
- [ ] File paths are exact (not relative)
- [ ] Method signature is copy-pasteable
- [ ] Implementation guidance has numbered steps
- [ ] Test file path is exact
- [ ] Test assertions are specific values (not "assert works")
- [ ] Quick sanity check shows expected output
- [ ] Acceptance criteria are checkboxes
- [ ] Branch name follows convention

### Special Considerations

1. **Phase 0 features have no dependencies** - they can all be worked in parallel
2. **Phase 6 has no dependencies on Phase 0** - it only uses existing BlockMetadata
3. **Phase 7 depends on Phases 1, 2, 3** - wait for those to complete
4. **Phase 11 is integration testing** - depends on ALL previous phases
5. **Phase 12 is documentation** - depends on Phase 11
6. **The test project is COALSHIPPINGSIMULATIONGSC** - use this for integration tests
7. **Real Dataiku instance is at http://172.18.58.26:10000** - for integration tests

### Estimated Feature Count

Based on the phase definitions, expect approximately:

- Phase 0: 5-6 features
- Phase 1: 5-7 features
- Phase 2: 5-7 features
- Phase 3: 3-4 features
- Phase 4: 3-4 features
- Phase 5: 2-3 features
- Phase 6: 2-3 features
- Phase 7: 4-5 features
- Phase 8: 2-3 features
- Phase 9: 2-3 features
- Phase 10: 2-3 features
- Phase 11: 3-4 features
- Phase 12: 2-3 features

**Total: ~40-55 features**

### Begin

Start with Phase 0. Create all feature specs for that phase. Then proceed to subsequent phases in dependency order, maximizing parallelism where possible.

------

# APPENDIX A: EXISTING CODE REFERENCE

## A.1 Current identifier.py Methods (to extend)

```python
class BlockIdentifier:
    def __init__(self, crawler: FlowCrawler)
    def identify_blocks(self, project_key: str) -> List[BlockMetadata]
    def is_valid_block(self, boundary: Dict[str, Any]) -> bool
    def should_skip_zone(self, zone_name: str) -> bool
    def extract_block_metadata(self, project_key, zone_name, boundary) -> BlockMetadata
    def generate_block_id(self, zone_name: str) -> str
    def create_block_ports(self, dataset_names, port_type) -> List[BlockPort]
    def extract_block_contents(self, boundary, zone_items) -> BlockContents
    def classify_hierarchy(self, zone_metadata) -> str
    def extract_domain(self, zone_metadata) -> str
    def extract_tags(self, zone_metadata) -> List[str]
    def generate_version(self, block_id: str) -> str
    def get_validation_message(self, boundary) -> str
    def _get_zone_metadata(self, project_key, zone_name) -> Dict[str, Any]
    def _format_block_name(self, zone_name) -> str
```

## A.2 Current catalog_writer.py Methods (to extend)

```python
class CatalogWriter:
    def __init__(self, client: Optional[DSSClient] = None)
    def generate_wiki_article(self, metadata: BlockMetadata) -> str
    def _generate_frontmatter(self, metadata) -> str
    def generate_block_summary(self, metadata) -> str
    def merge_catalog_index(self, existing_index, metadata) -> Dict[str, Any]
    def generate_schema_file(self, schema) -> str
    def extract_changelog(self, existing_article) -> str
    def merge_wiki_article(self, existing_article, metadata) -> str
    def get_wiki_path(self, metadata) -> str
    def write_to_project_registry(self, project_key, blocks) -> Dict[str, Any]
    def _ensure_project_registry_exists(self, project_key)
    def _write_wiki_article(self, project, block) -> str
    def _write_schemas(self, project, block) -> int
    def _update_discovery_index(self, project, blocks)
```

## A.3 Dataiku API Reference (Key Methods)

```python
# Project
project = client.get_project(project_key)
project.get_dataset(dataset_name)
project.get_recipe(recipe_name)
project.get_flow()
project.get_library()
project.get_wiki()
project.list_datasets()
project.list_recipes()

# Dataset
dataset.get_settings()  # Returns DSSDatasetSettings
dataset.get_schema()    # Returns {"columns": [...]}
settings.get_raw()      # Returns full settings dict

# Recipe
recipe.get_settings()   # Returns recipe settings
settings.get_raw()      # Returns full settings dict with inputs/outputs

# Flow
flow.list_zones()       # Returns list of zones
flow.get_zone(zone_id)  # Returns zone object
zone.items              # List of {"type": "DATASET/RECIPE", "id": "name"}

# Library
library.root            # Root folder
folder.get_child(name)  # Get child file/folder or None
folder.add_folder(name) # Create folder
folder.add_file(name)   # Create file
file.read()             # Read content
file.write(content)     # Write content

# Wiki
wiki.create_article(path, content)
wiki.get_article(path)
article.get_body()
article.set_body(content)
```

------

# APPENDIX B: TEST PROJECT DETAILS

## B.1 COALSHIPPINGSIMULATIONGSC

This is the real Dataiku project used for integration testing.

**Project Key:** `COALSHIPPINGSIMULATIONGSC` **Instance:** `http://172.18.58.26:10000`

**Known Zones:** (Discovered in Phase 1)

- Multiple zones with datasets and recipes
- Real flow graph with dependencies
- Suitable for testing boundary analysis

**Integration Test Environment Variables:**

```bash
export DSS_HOST="http://172.18.58.26:10000"
export DSS_API_KEY="your_api_key"
export USE_REAL_DATAIKU="true"
```

------

# APPENDIX C: GLOSSARY

| Term             | Definition                                                   |
| ---------------- | ------------------------------------------------------------ |
| Block            | A reusable workflow component represented as a Dataiku Flow Zone |
| Zone             | A logical grouping of datasets and recipes in a Dataiku project flow |
| Port             | An input or output connection point of a block               |
| Boundary         | The set of inputs, outputs, and internals that define a block's interface |
| Discovery        | The process of crawling a project to identify and catalog blocks |
| Catalog          | The collection of block metadata stored in Wiki + Library    |
| Registry         | The project-local storage for discovery results              |
| BLOCKS_REGISTRY  | Central catalog project (future - for cross-project discovery) |
| Phase            | High-level component of work (~200-500 LOC)                  |
| Feature          | Atomic unit of work (~15-30 LOC) executable by a coding agent |
| Enhancement Plan | The 13-phase plan for Discovery Agent Phase 2                |

------

**END OF HANDOVER DOCUMENT**

**Document Statistics:**

- Sections: 5 main + 3 appendices
- Phases documented: 13
- Estimated features: 40-55
- Ready for feature spec generation: YES