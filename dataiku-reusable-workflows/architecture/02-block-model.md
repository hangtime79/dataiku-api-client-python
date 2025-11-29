# Block Model Specification

## Definition

A **Block** is a reusable workflow component represented as a Dataiku Flow Zone. It encapsulates datasets, recipes, and optionally models, with clearly defined input and output boundaries.

---

## Block Types

### Type 1: Zone Block (Primary)

A standard block representing a single flow zone.

```
┌─────────────────────────────────────────────┐
│              Zone Block                      │
│                                             │
│  [INPUT_A] ──┐                              │
│              ├──▶ [recipe_1] ──▶ [ds_1]     │
│  [INPUT_B] ──┘         │                    │
│                        ▼                    │
│                   [recipe_2] ──▶ [ds_2]     │
│                        │                    │
│                        ▼                    │
│                   [recipe_3] ──▶ [OUTPUT]   │
│                                             │
└─────────────────────────────────────────────┘

Inputs: INPUT_A, INPUT_B
Outputs: OUTPUT
Internal: ds_1, ds_2, recipe_1, recipe_2, recipe_3
```

**Characteristics:**
- Single zone boundary
- 1+ inputs (datasets entering the zone)
- 1+ outputs (datasets leaving the zone)
- Contains internal datasets and recipes
- May contain trained models

### Type 2: Solution Block

A composite block that orchestrates multiple zone blocks.

```
┌─────────────────────────────────────────────────────────────┐
│                    Solution Block                           │
│                                                             │
│  [INPUT] ──▶ ┌──────────┐    ┌──────────┐                  │
│              │ Block A  │───▶│ Block B  │───▶ [OUTPUT_1]   │
│              │ (zone)   │    │ (zone)   │                  │
│              └──────────┘    └────┬─────┘                  │
│                                   │                         │
│                                   ▼                         │
│                              ┌──────────┐                  │
│                              │ Block C  │───▶ [OUTPUT_2]   │
│                              │ (zone)   │                  │
│                              └──────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Inputs: INPUT (maps to Block A input)
Outputs: OUTPUT_1, OUTPUT_2
Contains: Block A, Block B, Block C (as zones)
```

**Characteristics:**
- Contains multiple zone blocks
- Defines sequence or dependencies between blocks
- Maps external inputs to internal block inputs
- Maps internal block outputs to external outputs
- Represents a complete "solution" or capability

---

## Block Lifecycle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Draft     │────▶│  Published  │────▶│  Deprecated │
└─────────────┘     └─────────────┘     └─────────────┘
      │                   │
      │                   ├────▶ v1.0.0 (bundle)
      │                   ├────▶ v1.1.0 (bundle)
      │                   └────▶ v2.0.0 (bundle)
      │
      └──── Not in registry, development only
```

### States

| State | In Registry | Has Bundle | Can Reference |
|-------|-------------|------------|---------------|
| Draft | No | No | No |
| Published | Yes | Optional | Yes |
| Deprecated | Yes (marked) | Yes | Yes (with warning) |

### Versioning

Semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR:** Breaking changes (input/output schema change)
- **MINOR:** New features, backward compatible
- **PATCH:** Bug fixes, no interface change

Each version can have an associated bundle snapshot (immutable).

---

## Block Metadata Schema

### Full Specification

```yaml
# Required fields
block_id: string              # Unique identifier (UPPERCASE_WITH_UNDERSCORES)
version: string               # Semantic version (e.g., "1.2.0")
type: enum                    # "zone" | "solution"
blocked: boolean              # Protection flag

# Source information
source_project: string        # Origin project key
source_zone: string           # Origin zone name (for zone blocks)

# Classification (organization-configurable)
hierarchy_level: string       # e.g., "equipment", "process", "plant"
domain: string                # e.g., "rotating_equipment", "process_control"
tags: list[string]            # Searchable tags

# Description
name: string                  # Human-readable name
description: string           # Detailed description
owner: string                 # Owner email or team

# Interface definition
inputs: list[BlockPort]       # Input ports
outputs: list[BlockPort]      # Output ports

# Contents (for zone blocks)
contains:
  datasets: list[string]      # Internal dataset names
  recipes: list[string]       # Internal recipe names
  models: list[string]        # Internal saved model IDs

# Contents (for solution blocks)
sequence: list[SequenceStep]  # Ordered block sequence
# OR
dependencies: dict            # Dependency graph for resolution

# Dependencies
dependencies:
  python: list[string]        # Python packages with versions
  plugins: list[string]       # Dataiku plugins

# Artifacts
bundle_ref: string            # Path to bundle (optional)
schema_refs:
  inputs: dict[string, string]   # Port name -> schema file
  outputs: dict[string, string]  # Port name -> schema file

# Metadata
created_at: datetime
updated_at: datetime
created_by: string
deprecated: boolean           # Deprecation flag
deprecated_message: string    # Migration guidance
```

### BlockPort Schema

```yaml
name: string                  # Port name (UPPERCASE)
type: enum                    # "dataset" | "model" | "folder"
required: boolean             # For inputs only
description: string           # Human-readable description

# Schema definition (for datasets)
schema:
  columns: list[ColumnDef]    # Column definitions
  # OR
  schema_ref: string          # Reference to schema file
```

### ColumnDef Schema

```yaml
name: string                  # Column name
type: enum                    # "string" | "int" | "double" | "boolean" | "date" | "array" | "object"
description: string           # Column description
nullable: boolean             # Whether null is allowed
```

### SequenceStep Schema (for solutions)

```yaml
block_ref: string             # Block reference (ID@VERSION)
alias: string                 # Local alias for this instance
depends_on: string | list[string]  # Dependencies (other aliases)
input_mapping: dict           # Map solution inputs to block inputs
output_mapping: dict          # Map block outputs to solution outputs
```

---

## Block Identification Rules

The Discovery Agent uses these rules to identify valid blocks:

### Rule 1: Zone Boundary

A zone is a valid block candidate if:
- It has at least one dataset that receives data from outside the zone (input)
- It has at least one dataset that sends data outside the zone (output)
- Internal recipes are fully contained within the zone

```python
def is_valid_block_candidate(zone):
    inputs = find_external_inputs(zone)
    outputs = find_external_outputs(zone)

    return len(inputs) > 0 and len(outputs) > 0
```

### Rule 2: Input Identification

A dataset is a block input if:
- It belongs to the zone (or is shared to the zone)
- It has no upstream recipes within the zone
- It receives data from outside the zone OR is a sync/reference dataset

```python
def find_block_inputs(zone):
    inputs = []
    for dataset in zone.datasets:
        upstream_recipes = get_upstream_recipes(dataset)
        internal_upstream = [r for r in upstream_recipes if r in zone.recipes]

        if len(internal_upstream) == 0:
            inputs.append(dataset)

    return inputs
```

### Rule 3: Output Identification

A dataset is a block output if:
- It belongs to the zone
- It is consumed by recipes/datasets outside the zone
- OR it is the terminal dataset of a recipe chain

```python
def find_block_outputs(zone):
    outputs = []
    for dataset in zone.datasets:
        downstream = get_downstream_consumers(dataset)
        external_downstream = [d for d in downstream if d not in zone]

        if len(external_downstream) > 0:
            outputs.append(dataset)
        elif is_terminal_dataset(dataset, zone):
            outputs.append(dataset)

    return outputs
```

### Rule 4: Containment Validation

A zone is fully contained if:
- All recipes reference only datasets within the zone (for intermediate datasets)
- No recipe has outputs outside the zone except designated output datasets

---

## Block Naming Conventions

### Block ID

- Format: `UPPERCASE_WITH_UNDERSCORES`
- Max length: 64 characters
- Must be unique within registry
- Should be descriptive

**Good examples:**
- `COMPRESSOR_FEATURE_ENGINEERING`
- `PUMP_ANOMALY_DETECTION`
- `GAS_SEPARATION_MONITORING`

**Bad examples:**
- `block1` (not descriptive)
- `CompressorFeatures` (wrong case)
- `compressor-features` (wrong separator)

### Internal Datasets/Recipes

Within a block, naming should follow:
- Prefix with block context: `FE_` for feature engineering
- Descriptive names: `FE_SMOOTHED_SIGNAL`, `FE_FFT_RESULTS`
- Consistent casing (UPPERCASE recommended for Snowflake compatibility)

---

## Block Constraints

### Size Constraints

| Constraint | Limit | Rationale |
|------------|-------|-----------|
| Max inputs | 10 | Complexity management |
| Max outputs | 10 | Complexity management |
| Max internal datasets | 50 | Performance |
| Max internal recipes | 50 | Performance |
| Max dependencies | 20 | Dependency hell prevention |

### Interface Constraints

- Input names must be unique within block
- Output names must be unique within block
- Input/output names should not collide
- Schema changes require major version bump

### Compatibility Constraints

- Recipe override must have identical I/O signature
- Python inheritance requires compatible method signatures
- Solution blocks must have resolvable dependency graph

---

## Block Storage

### In Registry Wiki

```markdown
---
block_id: COMPRESSOR_FEATURE_ENG
version: 1.2.0
type: zone
blocked: true
source_project: COMPRESSOR_SOLUTIONS
source_zone: feature_engineering
hierarchy_level: equipment
domain: rotating_equipment
tags: [compressor, vibration, feature-engineering]
---

# Compressor Feature Engineering

## Description

Feature engineering pipeline for centrifugal compressor monitoring.
Performs signal processing, FFT analysis, and rolling statistics.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| RAW_VIBRATION | dataset | yes | Raw vibration sensor data |
| OPERATING_CONDITIONS | dataset | no | Operating parameters |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| ENGINEERED_FEATURES | dataset | Computed features for ML |

## Contains

**Datasets:** SMOOTHED_SIGNAL, FFT_RESULTS, ROLLING_STATS
**Recipes:** signal_smoothing, fft_analysis, rolling_stats, feature_combine

## Dependencies

- Python: scipy>=1.7, numpy>=1.20

## Usage

```yaml
blocks:
  - ref: "BLOCKS_REGISTRY/COMPRESSOR_FEATURE_ENG@1.2.0"
    inputs:
      RAW_VIBRATION: my_raw_data
    outputs:
      ENGINEERED_FEATURES: my_features
```

## Changelog

- 1.2.0: Added operating conditions as optional input
- 1.1.0: Improved FFT windowing
- 1.0.0: Initial release
```

### In Registry Library (JSON Index)

```json
{
  "format_version": "1.0",
  "updated_at": "2024-01-15T10:30:00Z",
  "blocks": [
    {
      "block_id": "COMPRESSOR_FEATURE_ENG",
      "version": "1.2.0",
      "type": "zone",
      "blocked": true,
      "source_project": "COMPRESSOR_SOLUTIONS",
      "source_zone": "feature_engineering",
      "hierarchy_level": "equipment",
      "domain": "rotating_equipment",
      "tags": ["compressor", "vibration", "feature-engineering"],
      "inputs": [
        {"name": "RAW_VIBRATION", "type": "dataset", "required": true},
        {"name": "OPERATING_CONDITIONS", "type": "dataset", "required": false}
      ],
      "outputs": [
        {"name": "ENGINEERED_FEATURES", "type": "dataset"}
      ],
      "bundle_ref": "bundles/COMPRESSOR_FEATURE_ENG_v1.2.0.zip",
      "wiki_ref": "_BLOCKS/by-hierarchy/equipment/COMPRESSOR_FEATURE_ENG.md"
    }
  ]
}
```

---

## Block Validation Rules

### On Publish (Discovery Agent)

1. Block ID is valid format
2. Version is valid semantic version
3. At least one input defined
4. At least one output defined
5. All internal datasets exist in source zone
6. All internal recipes exist in source zone
7. Zone boundary is valid (no leaking references)
8. Dependencies are resolvable

### On Reference (IaC Validation)

1. Block exists in registry
2. Version exists (or "latest" resolves)
3. All required inputs are mapped
4. Input types are compatible
5. Override recipes have compatible I/O
6. No circular dependencies (for solutions)

---

## Example Blocks

### Example 1: Simple Feature Engineering Block

```yaml
block_id: SIMPLE_FEATURE_ENG
version: 1.0.0
type: zone
blocked: false

source_project: DEMOS
source_zone: feature_prep

hierarchy_level: equipment
domain: general

inputs:
  - name: RAW_DATA
    type: dataset
    required: true

outputs:
  - name: FEATURES
    type: dataset

contains:
  datasets: [CLEANED_DATA, NORMALIZED_DATA]
  recipes: [clean_data, normalize, compute_features]

dependencies:
  python: [pandas>=1.0]
```

### Example 2: Multi-Model Solution Block

```yaml
block_id: EQUIPMENT_HEALTH_SOLUTION
version: 1.0.0
type: solution
blocked: true

hierarchy_level: plant
domain: predictive_maintenance

sequence:
  - block_ref: FEATURE_ENGINEERING@1.2.0
    alias: features
    input_mapping:
      RAW_DATA: EQUIPMENT_SENSORS

  - block_ref: ANOMALY_DETECTION@1.0.0
    alias: anomaly
    depends_on: features
    input_mapping:
      FEATURES: features.OUTPUT

  - block_ref: RUL_PREDICTION@1.0.0
    alias: rul
    depends_on: features
    input_mapping:
      FEATURES: features.OUTPUT

  - block_ref: ALERTING@1.0.0
    alias: alerts
    depends_on: [anomaly, rul]
    input_mapping:
      ANOMALIES: anomaly.OUTPUT
      RUL_SCORES: rul.OUTPUT
    output_mapping:
      ALERTS: EQUIPMENT_ALERTS

inputs:
  - name: EQUIPMENT_SENSORS
    type: dataset
    required: true

outputs:
  - name: EQUIPMENT_ALERTS
    type: dataset
```
