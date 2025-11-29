# Executing Agent Specification

## Overview

The Executing Agent reads the block catalog and generates IaC configurations that compose blocks into new projects. It bridges user intent to deployable infrastructure.

---

## Functional Requirements

### FR-1: Catalog Reading

The agent MUST be able to read from BLOCKS_REGISTRY:
- JSON index from project library (`blocks/index.json`)
- Full block metadata from manifests (`blocks/manifests/*.json`)
- Schema definitions (`blocks/schemas/*`)
- Wiki articles for additional context (optional)

### FR-2: Query Processing

The agent MUST support queries via:
- Structured `BlockQuery` objects with explicit filters
- Natural language intent parsing (basic keyword matching)

Query parameters:
- `hierarchy_level` - Filter by hierarchy (e.g., "equipment")
- `domain` - Filter by domain (e.g., "rotating_equipment")
- `tags` - Filter by tags (any match)
- `capabilities` - Match blocks by capability keywords
- `blocked_only` - Only return protected blocks
- `exclude_blocked` - Exclude protected blocks
- `input_types` - Required input dataset types
- `output_types` - Required output dataset types

### FR-3: Block Matching

The agent MUST match blocks to queries using:
- Exact match on hierarchy_level, domain
- Fuzzy match on tags and capabilities
- Schema compatibility checking
- Scoring and ranking of matches

### FR-4: Dependency Resolution

The agent MUST resolve dependencies:
- Between blocks in a solution
- Between block outputs and inputs
- Detect circular dependencies
- Topological sort for execution order

### FR-5: Configuration Generation

The agent MUST generate valid IaC configuration:
- Project definition
- Block references with version
- Input/output mappings
- Extension declarations (if any)
- Local dataset definitions
- Local recipe definitions

### FR-6: Wiring Automation

The agent MUST automatically wire:
- Block outputs to downstream block inputs
- External inputs to first block(s)
- Final block outputs to external outputs
- Handle fan-in and fan-out patterns

---

## Query Model

### BlockQuery Structure

```yaml
# All fields optional - empty query returns all blocks
hierarchy_level: string       # Filter by hierarchy
domain: string                # Filter by domain
tags: list[string]            # Filter by tags (OR)
capabilities: list[string]    # Keywords to match
blocked_only: bool            # Only protected blocks
exclude_blocked: bool         # Exclude protected blocks
min_version: string           # Minimum semantic version
max_results: int              # Limit results (default: 10)

# Schema requirements
input_requirements:
  - name: string              # Expected input name pattern
    type: string              # dataset | model | folder
    schema_contains: list     # Required column names

output_requirements:
  - name: string
    type: string
    schema_contains: list
```

### Natural Language Intent

The agent should parse simple intents like:
- "I need feature engineering for compressors"
- "Find anomaly detection blocks in rotating equipment domain"
- "Get all equipment-level blocks tagged with vibration"

Parsing extracts:
- Action keywords → capability matching
- Domain keywords → domain filter
- Hierarchy keywords → hierarchy filter
- Object keywords → tag matching

---

## Algorithm Specifications

### Algorithm 1: Catalog Loading

```
FUNCTION load_catalog(registry_project)
  INPUT: Registry project reference
  OUTPUT: BlockCatalog object

  1. Get project library
     library = registry_project.get_library()

  2. Read master index
     index_file = library.get_file("blocks/index.json")
     index_data = parse_json(index_file.read())

  3. Create catalog
     catalog = BlockCatalog()
     catalog.format_version = index_data["format_version"]
     catalog.updated_at = index_data["updated_at"]

  4. Load block summaries
     For each block_entry in index_data["blocks"]:
       summary = BlockSummary.from_dict(block_entry)
       catalog.add_block(summary)

  5. Build indexes for fast lookup
     catalog.build_hierarchy_index()
     catalog.build_domain_index()
     catalog.build_tag_index()

  6. Return catalog
END FUNCTION
```

### Algorithm 2: Block Matching

```
FUNCTION match_blocks(catalog, query)
  INPUT: BlockCatalog, BlockQuery
  OUTPUT: List of MatchResult (block + score)

  1. Start with all blocks
     candidates = catalog.all_blocks()

  2. Apply exact filters
     If query.hierarchy_level:
       candidates = filter(c.hierarchy_level == query.hierarchy_level)

     If query.domain:
       candidates = filter(c.domain == query.domain)

     If query.blocked_only:
       candidates = filter(c.blocked == True)

     If query.exclude_blocked:
       candidates = filter(c.blocked == False)

     If query.min_version:
       candidates = filter(semver_compare(c.version, query.min_version) >= 0)

  3. Score remaining candidates
     results = []
     For each candidate in candidates:
       score = compute_match_score(candidate, query)
       If score > 0:
         results.append(MatchResult(candidate, score))

  4. Sort by score descending
     results.sort(key=lambda r: r.score, reverse=True)

  5. Apply limit
     If query.max_results:
       results = results[:query.max_results]

  6. Return results
END FUNCTION

FUNCTION compute_match_score(block, query)
  INPUT: BlockSummary, BlockQuery
  OUTPUT: float score (0.0 to 1.0)

  score = 0.0
  max_score = 0.0

  1. Tag matching (if tags specified)
     If query.tags:
       max_score += 1.0
       matching_tags = intersection(block.tags, query.tags)
       score += len(matching_tags) / len(query.tags)

  2. Capability matching (if capabilities specified)
     If query.capabilities:
       max_score += 1.0
       # Check block name, description, tags for capability keywords
       block_text = lower(block.name + " " + block.description + " " + join(block.tags))
       matches = 0
       For cap in query.capabilities:
         If lower(cap) in block_text:
           matches += 1
       score += matches / len(query.capabilities)

  3. Input requirements (if specified)
     If query.input_requirements:
       max_score += 1.0
       matched_inputs = 0
       For req in query.input_requirements:
         For inp in block.inputs:
           If matches_requirement(inp, req):
             matched_inputs += 1
             break
       score += matched_inputs / len(query.input_requirements)

  4. Output requirements (if specified)
     If query.output_requirements:
       max_score += 1.0
       matched_outputs = 0
       For req in query.output_requirements:
         For out in block.outputs:
           If matches_requirement(out, req):
             matched_outputs += 1
             break
       score += matched_outputs / len(query.output_requirements)

  5. Normalize score
     If max_score > 0:
       Return score / max_score
     Else:
       Return 1.0  # No criteria = everything matches
END FUNCTION
```

### Algorithm 3: Intent Parsing

```
FUNCTION parse_intent(text)
  INPUT: Natural language string
  OUTPUT: BlockQuery

  1. Tokenize and normalize
     tokens = lowercase(text).split()
     tokens = remove_stopwords(tokens)

  2. Extract hierarchy keywords
     hierarchy_keywords = {
       "sensor": "sensor",
       "equipment": "equipment",
       "process": "process",
       "plant": "plant",
       "business": "business"
     }
     hierarchy = None
     For token in tokens:
       If token in hierarchy_keywords:
         hierarchy = hierarchy_keywords[token]
         break

  3. Extract domain keywords
     domain_keywords = {
       "compressor": "rotating_equipment",
       "pump": "rotating_equipment",
       "turbine": "rotating_equipment",
       "motor": "rotating_equipment",
       "vibration": "rotating_equipment",
       "control": "process_control",
       "maintenance": "predictive_maintenance"
     }
     domain = None
     For token in tokens:
       If token in domain_keywords:
         domain = domain_keywords[token]
         break

  4. Extract capability keywords
     action_verbs = ["feature", "anomaly", "predict", "detect", "classify", "monitor", "alert"]
     capabilities = []
     For token in tokens:
       If any(verb in token for verb in action_verbs):
         capabilities.append(token)

  5. Extract tag candidates
     # Remaining meaningful tokens become tag candidates
     tags = [t for t in tokens if len(t) > 3 and t not in stopwords]

  6. Build query
     Return BlockQuery(
       hierarchy_level=hierarchy,
       domain=domain,
       capabilities=capabilities,
       tags=tags
     )
END FUNCTION
```

### Algorithm 4: Dependency Resolution

```
FUNCTION resolve_dependencies(blocks, wiring_hints)
  INPUT: List of matched blocks, optional wiring hints
  OUTPUT: ResolvedPlan with ordered blocks and wiring

  1. Build dependency graph
     graph = DirectedGraph()

     For each block in blocks:
       graph.add_node(block.block_id)

     # Infer dependencies from inputs/outputs
     For each block_a in blocks:
       For each block_b in blocks:
         If block_a != block_b:
           # Check if block_a outputs match block_b inputs
           If can_wire(block_a.outputs, block_b.inputs):
             graph.add_edge(block_a.block_id, block_b.block_id)

  2. Apply explicit wiring hints
     If wiring_hints:
       For hint in wiring_hints:
         graph.add_edge(hint.source_block, hint.target_block)

  3. Detect cycles
     cycle = find_cycle(graph)
     If cycle:
       Raise CircularDependencyError(cycle)

  4. Topological sort
     execution_order = topological_sort(graph)

  5. Generate wiring plan
     wiring = []
     For i, block_id in enumerate(execution_order):
       If i > 0:
         # Find which previous block outputs connect to this block's inputs
         block = get_block(block_id)
         For inp in block.inputs:
           source = find_source_output(execution_order[:i], inp)
           If source:
             wiring.append(Wire(source, block_id, inp.name))

  6. Return ResolvedPlan(execution_order, wiring)
END FUNCTION

FUNCTION can_wire(outputs, inputs)
  INPUT: List of output ports, list of input ports
  OUTPUT: bool

  For out in outputs:
    For inp in inputs:
      If types_compatible(out.type, inp.type):
        If schemas_compatible(out.schema, inp.schema):
          Return True
  Return False
END FUNCTION

FUNCTION schemas_compatible(source_schema, target_schema)
  INPUT: Two schema dicts
  OUTPUT: bool

  # If no schemas, assume compatible
  If source_schema is None or target_schema is None:
    Return True

  # Target columns must be subset of source columns
  source_columns = {c["name"] for c in source_schema.get("columns", [])}
  target_columns = {c["name"] for c in target_schema.get("columns", [])}

  Return target_columns.issubset(source_columns)
END FUNCTION
```

### Algorithm 5: Configuration Generation

```
FUNCTION generate_config(resolved_plan, target_project_key, external_inputs, external_outputs)
  INPUT: ResolvedPlan, target project key, external mappings
  OUTPUT: IaC configuration dict

  config = {
    "version": "1.0",
    "project": {
      "key": target_project_key,
      "name": generate_project_name(resolved_plan)
    },
    "blocks": [],
    "datasets": [],
    "recipes": []
  }

  1. Generate block references
     For i, block_id in enumerate(resolved_plan.execution_order):
       block = get_block_metadata(block_id)

       block_config = {
         "ref": f"BLOCKS_REGISTRY/{block_id}@{block.version}",
         "instance_name": generate_instance_name(block_id, i),
         "zone_name": generate_zone_name(block_id),
         "inputs": {},
         "outputs": {}
       }

       # Map inputs
       For inp in block.inputs:
         wire = find_wire_for_input(resolved_plan.wiring, block_id, inp.name)
         If wire:
           # Wired from previous block
           block_config["inputs"][inp.name] = wire.source_dataset
         Elif inp.name in external_inputs:
           # External input
           block_config["inputs"][inp.name] = external_inputs[inp.name]
         Else:
           # Generate placeholder
           block_config["inputs"][inp.name] = f"INPUT_{inp.name}"

       # Map outputs
       For out in block.outputs:
         If out.name in external_outputs:
           block_config["outputs"][out.name] = external_outputs[out.name]
         Else:
           # Generate internal name
           block_config["outputs"][out.name] = f"{block_id}_{out.name}"

       config["blocks"].append(block_config)

  2. Generate placeholder datasets for unmapped inputs
     For block_config in config["blocks"]:
       For input_name, dataset_name in block_config["inputs"].items():
         If dataset_name.startswith("INPUT_"):
           config["datasets"].append({
             "name": dataset_name,
             "type": "TODO_SPECIFY_TYPE",
             "comment": f"Placeholder for {input_name} - configure connection"
           })

  3. Return config
END FUNCTION
```

---

## Component Specifications

### Component 1: CatalogReader

**Responsibility:** Read and cache block catalog from registry.

**Methods:**

```python
class CatalogReader:
    def __init__(self, client: DSSClient, registry_key: str = "BLOCKS_REGISTRY"):
        """Initialize reader with client and registry key."""

    def load_catalog(self) -> BlockCatalog:
        """
        Load full catalog from registry.

        Returns cached catalog if already loaded and not stale.
        """

    def get_block(self, block_id: str, version: str = None) -> BlockMetadata:
        """
        Get full metadata for a specific block.

        Loads from manifest file for complete details.
        """

    def get_schema(self, block_id: str, port_name: str) -> Optional[dict]:
        """Get schema for a specific block port."""

    def refresh(self):
        """Force refresh of cached catalog."""
```

### Component 2: BlockMatcher

**Responsibility:** Match blocks to queries with scoring.

**Methods:**

```python
class BlockMatcher:
    def __init__(self, catalog: BlockCatalog):
        """Initialize with loaded catalog."""

    def match(self, query: BlockQuery) -> List[MatchResult]:
        """
        Find blocks matching query.

        Returns list of MatchResult sorted by score descending.
        """

    def match_by_capability(self, capabilities: List[str]) -> List[MatchResult]:
        """Match blocks by capability keywords."""

    def find_compatible_blocks(self, source_block: BlockSummary) -> List[BlockSummary]:
        """Find blocks that can consume source block's outputs."""
```

### Component 3: DependencyResolver

**Responsibility:** Resolve execution order and wiring between blocks.

**Methods:**

```python
class DependencyResolver:
    def __init__(self):
        """Initialize resolver."""

    def resolve(
        self,
        blocks: List[BlockSummary],
        wiring_hints: List[WiringHint] = None
    ) -> ResolvedPlan:
        """
        Resolve dependencies and generate execution plan.

        Raises CircularDependencyError if cycle detected.
        """

    def infer_wiring(
        self,
        source: BlockSummary,
        target: BlockSummary
    ) -> List[Wire]:
        """Infer possible wiring between two blocks."""

    def validate_wiring(self, wiring: List[Wire], blocks: List[BlockSummary]) -> List[str]:
        """Validate wiring is complete and correct. Returns list of errors."""
```

### Component 4: ConfigGenerator

**Responsibility:** Generate IaC configuration YAML.

**Methods:**

```python
class ConfigGenerator:
    def __init__(self):
        """Initialize generator."""

    def generate(
        self,
        resolved_plan: ResolvedPlan,
        target_project_key: str,
        external_inputs: Dict[str, str] = None,
        external_outputs: Dict[str, str] = None,
        extensions: List[ExtensionConfig] = None
    ) -> CompositionConfig:
        """
        Generate complete IaC configuration.

        Returns CompositionConfig that can be serialized to YAML.
        """

    def to_yaml(self, config: CompositionConfig) -> str:
        """Serialize configuration to YAML string."""

    def validate_config(self, config: CompositionConfig) -> List[ValidationError]:
        """Validate generated configuration."""
```

### Component 5: IntentParser

**Responsibility:** Parse natural language intent to structured query.

**Methods:**

```python
class IntentParser:
    def __init__(self, catalog: BlockCatalog = None):
        """
        Initialize parser.

        If catalog provided, uses block metadata for better parsing.
        """

    def parse(self, text: str) -> BlockQuery:
        """
        Parse natural language to BlockQuery.

        Extracts hierarchy, domain, capabilities, tags from text.
        """

    def suggest_refinements(self, text: str, results: List[MatchResult]) -> List[str]:
        """
        Suggest query refinements if results are poor.

        Returns list of suggested modified queries.
        """
```

---

## Error Handling

### Error Types

| Error | When | Handling |
|-------|------|----------|
| `RegistryNotFoundError` | Registry project missing | Fail with clear message |
| `CatalogLoadError` | Cannot read index.json | Fail with details |
| `BlockNotFoundError` | Referenced block not in catalog | List available blocks |
| `VersionNotFoundError` | Specific version not found | List available versions |
| `CircularDependencyError` | Cycle in block dependencies | Show cycle path |
| `IncompatibleWiringError` | Cannot wire blocks together | Show type mismatch |
| `NoMatchError` | No blocks match query | Suggest relaxed query |

### Error Messages

```python
class NoMatchError(Exception):
    def __init__(self, query: BlockQuery, suggestions: List[str]):
        self.query = query
        self.suggestions = suggestions
        message = f"No blocks match query. Suggestions:\n"
        for s in suggestions:
            message += f"  - {s}\n"
        super().__init__(message)
```

---

## Configuration

### ExecutingAgentConfig

```python
@dataclass
class ExecutingAgentConfig:
    # Registry settings
    registry_project_key: str = "BLOCKS_REGISTRY"

    # Matching behavior
    default_max_results: int = 10
    min_match_score: float = 0.3
    prefer_newer_versions: bool = True

    # Wiring behavior
    auto_wire: bool = True
    strict_schema_matching: bool = False

    # Generation behavior
    generate_placeholders: bool = True
    include_comments: bool = True
```

---

## Output Formats

### MatchResult

```python
@dataclass
class MatchResult:
    block: BlockSummary
    score: float                    # 0.0 to 1.0
    match_details: Dict[str, Any]   # Which criteria matched
```

### ResolvedPlan

```python
@dataclass
class ResolvedPlan:
    execution_order: List[str]      # Block IDs in order
    wiring: List[Wire]              # Connection definitions
    stages: List[List[str]]         # Parallelizable stages
```

### Wire

```python
@dataclass
class Wire:
    source_block: str
    source_port: str
    target_block: str
    target_port: str
    dataset_name: str               # Generated dataset name
```

### CompositionConfig

```python
@dataclass
class CompositionConfig:
    version: str
    project: ProjectConfig
    blocks: List[BlockReferenceConfig]
    datasets: List[DatasetConfig]
    recipes: List[RecipeConfig]

    def to_yaml(self) -> str:
        """Serialize to YAML."""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
```

---

## Usage Examples

### Basic Composition

```python
from dataikuapi import DSSClient
from dataikuapi.iac.workflows.executing import (
    ExecutingAgent, BlockQuery, ExecutingAgentConfig
)

client = DSSClient("https://dss.example.com", "api_key")

agent = ExecutingAgent(client)

# Query for blocks
query = BlockQuery(
    hierarchy_level="equipment",
    domain="rotating_equipment",
    capabilities=["feature_engineering", "anomaly_detection"]
)

# Compose solution
result = agent.compose(
    query=query,
    target_project_key="NEW_COMPRESSOR_MONITORING"
)

# Get generated config
print(result.config.to_yaml())
```

### Natural Language Query

```python
# Parse intent
result = agent.compose_from_intent(
    intent="I need compressor monitoring with anomaly detection",
    target_project_key="NEW_PROJECT"
)

print(f"Matched {len(result.matches)} blocks")
for match in result.matches:
    print(f"  {match.block.block_id}: {match.score:.2f}")
```

### With External Mappings

```python
result = agent.compose(
    query=BlockQuery(domain="rotating_equipment"),
    target_project_key="PLANT_X_MONITORING",
    external_inputs={
        "RAW_VIBRATION": "PLANT_X_SENSORS"
    },
    external_outputs={
        "ALERTS": "PLANT_X_ALERTS"
    }
)
```

### With Extensions

```python
from dataikuapi.iac.workflows.executing import ExtensionConfig, RecipeOverride

result = agent.compose(
    query=BlockQuery(capabilities=["feature_engineering"]),
    target_project_key="CUSTOM_PROJECT",
    extensions=[
        ExtensionConfig(
            block_id="FEATURE_ENGINEERING",
            overrides=[
                RecipeOverride(
                    recipe="signal_smoothing",
                    override_with="my_custom_smoothing"
                )
            ]
        )
    ]
)
```

---

## Integration with IaC Engine

The generated configuration is designed to be consumed by the IaC engine:

```python
# Generate config with Executing Agent
result = agent.compose(query, "NEW_PROJECT")
config_yaml = result.config.to_yaml()

# Save to file
with open("project.yml", "w") as f:
    f.write(config_yaml)

# Use IaC engine to plan and apply
from dataikuapi.iac.cli import plan, apply

plan_result = plan(config_path="project.yml", environment="prod")
print(plan_result)

# User reviews...

apply_result = apply(config_path="project.yml", environment="prod")
```
