# Planning Summary: Dataiku Reusable Workflows

## Executive Summary

Build a system that enables Dataiku users to discover, catalog, compose, and deploy reusable workflow components (blocks). The system comprises three agents and extends the existing IaC engine.

---

## What We're Building

### Component 1: Discovery Agent

**Purpose:** Crawl Dataiku projects and build a structured catalog of reusable blocks.

**Inputs:**
- Dataiku project key
- Configuration (what to catalog, hierarchy settings)

**Outputs:**
- Wiki articles (human-readable block documentation)
- JSON index (machine-parseable block catalog)
- Schema definitions (input/output contracts)

**Key Operations:**
1. Connect to Dataiku project
2. Traverse flow graph (datasets, recipes, zones)
3. Identify zone boundaries as potential blocks
4. Extract metadata (inputs, outputs, dependencies)
5. Write structured catalog to Wiki
6. Write JSON index to project library
7. Preserve manual edits on re-crawl

### Component 2: Executing Agent

**Purpose:** Take user intent, match against available blocks, generate deployment plan.

**Inputs:**
- User intent (natural language or structured query)
- Block catalog (from Discovery Agent)
- Filtering options (blocked-only, hierarchy level, domain)

**Outputs:**
- IaC configuration YAML
- Deployment plan (what will be created)

**Key Operations:**
1. Parse user intent
2. Read block catalog from BLOCKS_REGISTRY
3. Match intent to available blocks
4. Resolve dependencies between blocks
5. Generate IaC configuration
6. Present plan for user review

### Component 3: IaC Block Extension

**Purpose:** Extend existing IaC engine to support block references and composition.

**Inputs:**
- IaC configuration with `blocks:` section
- Block definitions from registry

**Outputs:**
- Plan with block operations
- Deployed project with instantiated blocks

**Key Operations:**
1. Parse block references in config
2. Validate block existence and version
3. Resolve block dependencies
4. Generate plan including block instantiation
5. Apply: create zones, copy recipes, wire connections
6. Create bundle snapshot of new version

---

## Data Flow

```
┌──────────────────┐
│  Source Project  │
│  (has zones to   │
│   publish)       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌─────────────────────────────┐
│ Discovery Agent  │────▶│      BLOCKS_REGISTRY        │
│                  │     │  ┌───────┐ ┌─────────────┐  │
└──────────────────┘     │  │ Wiki  │ │   Library   │  │
                         │  │       │ │ index.json  │  │
                         │  └───────┘ └─────────────┘  │
                         └──────────────┬──────────────┘
                                        │
                                        ▼
┌──────────────────┐     ┌─────────────────────────────┐
│ User + AI Agent  │────▶│     Executing Agent         │
│ "I need          │     │  - Reads catalog            │
│  compressor      │     │  - Matches blocks           │
│  monitoring"     │     │  - Generates config         │
└──────────────────┘     └──────────────┬──────────────┘
                                        │
                                        ▼
                         ┌─────────────────────────────┐
                         │   Generated IaC Config      │
                         │   (blocks + datasets +      │
                         │    recipes)                 │
                         └──────────────┬──────────────┘
                                        │
                                        ▼
                         ┌─────────────────────────────┐
                         │   IaC Engine (Extended)     │
                         │   Plan → Review → Apply     │
                         └──────────────┬──────────────┘
                                        │
                                        ▼
                         ┌─────────────────────────────┐
                         │   New Deployed Project      │
                         │   (composed from blocks)    │
                         └─────────────────────────────┘
```

---

## Key Interfaces

### Block Definition (What Gets Stored)

```yaml
block_id: COMPRESSOR_FEATURE_ENG
version: 1.2.0
type: zone                    # zone | solution
blocked: true                 # Protected from modification
source_project: COMPRESSOR_SOLUTIONS
source_zone: feature_engineering

hierarchy_level: equipment    # Organization-defined
domain: rotating_equipment
tags: [compressor, vibration, feature-engineering]

inputs:
  - name: RAW_VIBRATION
    type: dataset
    schema_ref: schemas/raw_vibration.json
    required: true
  - name: OPERATING_CONDITIONS
    type: dataset
    required: false

outputs:
  - name: ENGINEERED_FEATURES
    type: dataset
    schema_ref: schemas/engineered_features.json

contains:
  datasets:
    - SMOOTHED_SIGNAL
    - FFT_RESULTS
    - ROLLING_STATS
  recipes:
    - signal_smoothing
    - fft_analysis
    - rolling_stats
    - feature_combine

dependencies:
  python:
    - scipy>=1.7
    - numpy>=1.20
  plugins: []

bundle_ref: bundles/COMPRESSOR_FEATURE_ENG_v1.2.0.zip
```

### Block Reference (How Blocks Are Used)

```yaml
version: "1.0"

project:
  key: NEW_PLANT_MONITORING
  name: "New Plant Monitoring"

blocks:
  - ref: "BLOCKS_REGISTRY/COMPRESSOR_FEATURE_ENG@1.2.0"
    instance_name: COMPRESSOR_A_FEATURES
    zone_name: compressor_a_prep
    inputs:
      RAW_VIBRATION: raw_compressor_a_data
    outputs:
      ENGINEERED_FEATURES: compressor_a_features
    extends:
      - recipe: signal_smoothing
        override_with: custom_smoothing

  - ref: "BLOCKS_REGISTRY/ANOMALY_DETECTION@1.0.0"
    instance_name: COMPRESSOR_A_ANOMALY
    zone_name: compressor_a_analytics
    inputs:
      FEATURES: compressor_a_features  # Wired from previous block
    outputs:
      ANOMALIES: compressor_a_anomalies

datasets:
  - name: raw_compressor_a_data
    type: sql_table
    connection: PLANT_DW
    table: raw_compressor_a

recipes:
  - name: custom_smoothing
    type: python
    inputs: [RAW_VIBRATION]
    outputs: [SMOOTHED_SIGNAL]
    code_ref: lib/custom_smoothing.py
```

### Solution Block (Multi-Model Orchestration)

```yaml
block_id: EQUIPMENT_HEALTH_SOLUTION
version: 1.0.0
type: solution
blocked: true

description: "Complete equipment health monitoring with multiple models"

# Explicit sequence (when order is known)
sequence:
  - block_ref: FEATURE_ENGINEERING@1.2.0
    alias: features
  - block_ref: ANOMALY_DETECTION@1.0.0
    alias: anomaly
    depends_on: features
  - block_ref: RUL_PREDICTION@1.0.0
    alias: rul
    depends_on: features
  - block_ref: ALERTING@1.0.0
    alias: alerts
    depends_on: [anomaly, rul]  # Fan-in

# OR dependency-based (when system should resolve)
# dependencies:
#   ALERTING:
#     requires: [ANOMALY_DETECTION, RUL_PREDICTION]
#   RUL_PREDICTION:
#     requires: [FEATURE_ENGINEERING]
#   ANOMALY_DETECTION:
#     requires: [FEATURE_ENGINEERING]

inputs:
  - name: RAW_DATA
    maps_to: features.RAW_VIBRATION

outputs:
  - name: ALERTS
    maps_from: alerts.ALERT_OUTPUT
  - name: RUL_SCORES
    maps_from: rul.RUL_OUTPUT
```

---

## Catalog Structure in BLOCKS_REGISTRY

```
BLOCKS_REGISTRY/
├── Wiki/
│   ├── Home.md                      # Registry overview
│   ├── _BLOCKS/
│   │   ├── _INDEX.md                # Human-readable index
│   │   ├── by-hierarchy/
│   │   │   ├── equipment/
│   │   │   │   ├── COMPRESSOR_FEATURE_ENG.md
│   │   │   │   └── PUMP_MONITORING.md
│   │   │   └── process/
│   │   │       └── GAS_SEPARATION.md
│   │   └── by-domain/
│   │       └── rotating_equipment/
│   │           └── ...
│   └── _SOLUTIONS/
│       ├── _INDEX.md
│       └── EQUIPMENT_HEALTH.md
│
├── Library/
│   └── blocks/
│       ├── index.json               # Machine-parseable index
│       ├── hierarchy_config.json    # Org-defined hierarchy levels
│       └── schemas/
│           ├── raw_vibration.json
│           └── engineered_features.json
│
└── Bundles/
    ├── COMPRESSOR_FEATURE_ENG_v1.2.0.zip
    └── ANOMALY_DETECTION_v1.0.0.zip
```

---

## Extension Patterns

### Pattern 1: Recipe Override

Replace a recipe within a block with a custom implementation.

```yaml
blocks:
  - ref: "BLOCKS_REGISTRY/FEATURE_ENG@1.0.0"
    extends:
      - recipe: signal_smoothing
        override_with: my_custom_smoothing

recipes:
  - name: my_custom_smoothing
    type: python
    # Must have same inputs/outputs as original
    inputs: [RAW_SIGNAL]
    outputs: [SMOOTHED_SIGNAL]
    code: |
      # Custom implementation
      import dataiku
      # ...
```

### Pattern 2: Python Class Inheritance

Extend block logic through project library inheritance.

```python
# In source block's library: blocks/feature_eng/base.py
class BaseFeatureEngineer:
    def extract_features(self, df):
        # Base implementation
        return df.with_columns([...])

# In consumer's library: lib/custom_features.py
from blocks.feature_eng.base import BaseFeatureEngineer

class CustomFeatureEngineer(BaseFeatureEngineer):
    def extract_features(self, df):
        # Call parent
        df = super().extract_features(df)
        # Add custom features
        return df.with_columns([...])
```

### Pattern 3: Composition (Post-Processing)

Add recipes downstream of block outputs.

```yaml
blocks:
  - ref: "BLOCKS_REGISTRY/FEATURE_ENG@1.0.0"
    outputs:
      FEATURES: base_features

datasets:
  - name: extended_features
    type: managed

recipes:
  - name: add_custom_features
    type: python
    inputs: [base_features]
    outputs: [extended_features]
    # Extends block output with additional processing
```

---

## Error Handling

### Discovery Agent Errors

| Error | Handling |
|-------|----------|
| Project not found | Fail with clear message |
| No zones defined | Warn, offer to create default zone |
| Zone has no clear I/O | Warn, mark as non-publishable |
| Wiki write fails | Retry with backoff, then fail |
| Schema extraction fails | Log warning, continue with partial schema |

### Executing Agent Errors

| Error | Handling |
|-------|----------|
| Block not found | List similar blocks, suggest alternatives |
| Version not found | List available versions |
| Incompatible inputs | Show type mismatch, suggest fixes |
| Circular dependency | Detect and report cycle |
| No matching blocks | Return empty result with search tips |

### IaC Block Errors

| Error | Handling |
|-------|----------|
| Block reference invalid | Validate syntax, show correct format |
| Override recipe type mismatch | Validate I/O compatibility |
| Missing required input | List required inputs with types |
| Bundle not found | Offer to re-publish from source |

---

## Test Strategy (TDD)

### Discovery Agent Tests

1. **Unit Tests**
   - Zone boundary detection
   - Input/output identification
   - Metadata extraction
   - Wiki markdown generation
   - JSON index generation
   - Merge logic for manual edits

2. **Integration Tests**
   - Full project crawl
   - Wiki write/read roundtrip
   - Re-crawl with existing catalog

### Executing Agent Tests

1. **Unit Tests**
   - Intent parsing
   - Block matching algorithms
   - Dependency resolution
   - Config generation

2. **Integration Tests**
   - Catalog read from registry
   - End-to-end intent → config

### IaC Extension Tests

1. **Unit Tests**
   - Block config parsing
   - Block reference validation
   - Override validation
   - Solution sequence resolution

2. **Integration Tests**
   - Plan generation with blocks
   - Apply with block instantiation
   - Bundle snapshot creation

---

## Implementation Order

```
Week 1-2: Discovery Agent
├── Core crawling logic
├── Zone boundary detection
├── Wiki writer
├── JSON index writer
└── Tests

Week 3-4: IaC Extension
├── Block config model
├── Solution config model
├── Parser updates
├── Validation rules
└── Tests

Week 5-6: Executing Agent
├── Catalog reader
├── Block matching
├── Config generator
└── Tests

Week 7-8: Plan/Apply
├── Block instantiation
├── Recipe override
├── Cross-block wiring
├── Bundle snapshots
└── Integration tests
```

---

## Success Criteria

1. **Discovery Agent** can crawl any Dataiku project and produce a valid catalog
2. **Catalog** is both human-browsable (Wiki) and machine-parseable (JSON)
3. **Executing Agent** can match natural language intent to blocks with >80% accuracy
4. **IaC Extension** can plan and apply block compositions
5. **Extension patterns** work without modifying source blocks
6. **Solution blocks** correctly orchestrate multi-model sequences
7. **Versioning** provides immutable snapshots via bundles
8. **Re-crawl** preserves manual catalog edits

---

## Out of Scope (This Phase)

- Scenarios (orchestration/scheduling)
- Dashboards
- Dataiku Applications (app designer)
- Administration elements
- Dataiku Govern integration
- Updating existing projects (new project creation only)
- Cross-instance block sharing
- Automatic block discovery (user must run Discovery Agent)
