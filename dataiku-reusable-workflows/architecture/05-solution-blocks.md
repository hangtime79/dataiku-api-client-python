# Solution Blocks: Multi-Model Orchestration

## Overview

A **Solution Block** is a special block type that orchestrates multiple zone blocks (including model blocks) into a cohesive capability. Solutions define the sequence or dependencies between component blocks.

---

## Solution Block Concept

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Solution: Equipment Health Monitoring                │
│                                                                         │
│  [RAW_DATA] ──▶ ┌───────────────┐                                      │
│                 │ Block: Feature │                                      │
│                 │ Engineering    │                                      │
│                 └───────┬───────┘                                      │
│                         │                                               │
│                         ▼                                               │
│                 ┌───────────────┐    ┌───────────────┐                 │
│                 │ Block: Anomaly│    │ Block: RUL    │                 │
│                 │ Detection     │    │ Prediction    │                 │
│                 └───────┬───────┘    └───────┬───────┘                 │
│                         │                    │                          │
│                         └────────┬───────────┘                          │
│                                  │                                      │
│                                  ▼                                      │
│                         ┌───────────────┐                              │
│                         │ Block: Alert  │                              │
│                         │ Generation    │ ──▶ [ALERTS]                 │
│                         └───────────────┘                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Solution Block Types

### Type 1: Explicit Sequence

The solution author explicitly defines the execution order.

```yaml
block_id: EQUIPMENT_HEALTH_SOLUTION
version: 1.0.0
type: solution

sequence:
  - block_ref: FEATURE_ENGINEERING@1.2.0
    alias: features
    order: 1

  - block_ref: ANOMALY_DETECTION@1.0.0
    alias: anomaly
    order: 2
    depends_on: features

  - block_ref: RUL_PREDICTION@1.0.0
    alias: rul
    order: 2  # Same order = parallel execution possible
    depends_on: features

  - block_ref: ALERT_GENERATION@1.0.0
    alias: alerts
    order: 3
    depends_on: [anomaly, rul]  # Fan-in from multiple blocks
```

**Use when:**
- Execution order is critical
- Author knows the optimal sequence
- Simple linear or DAG structure

### Type 2: Dependency-Based Resolution

The solution declares dependencies, and the system resolves execution order.

```yaml
block_id: FLEXIBLE_ANALYTICS_SOLUTION
version: 1.0.0
type: solution

dependencies:
  features:
    block_ref: FEATURE_ENGINEERING@1.2.0
    requires: []  # No dependencies, runs first

  anomaly:
    block_ref: ANOMALY_DETECTION@1.0.0
    requires: [features]

  rul:
    block_ref: RUL_PREDICTION@1.0.0
    requires: [features]

  classification:
    block_ref: FAILURE_CLASSIFICATION@1.0.0
    requires: [features, anomaly]

  alerts:
    block_ref: ALERT_GENERATION@1.0.0
    requires: [anomaly, rul, classification]
```

**Use when:**
- Complex dependency graphs
- Order should be computed
- Dynamic composition scenarios

### Type 3: Hybrid (Recommended)

Combine explicit sequence with dependency resolution fallback.

```yaml
block_id: HYBRID_SOLUTION
version: 1.0.0
type: solution

# Explicit sequence where known
sequence:
  - block_ref: FEATURE_ENGINEERING@1.2.0
    alias: features
    order: 1

# Dependency-based for the rest
dependencies:
  anomaly:
    block_ref: ANOMALY_DETECTION@1.0.0
    requires: [features]

  rul:
    block_ref: RUL_PREDICTION@1.0.0
    requires: [features]

  alerts:
    block_ref: ALERT_GENERATION@1.0.0
    requires: [anomaly, rul]
```

---

## Solution Block Schema

### Full Specification

```yaml
# Identity
block_id: string              # Unique identifier
version: string               # Semantic version
type: "solution"              # Must be "solution"
blocked: boolean              # Protection flag

# Metadata
name: string                  # Human-readable name
description: string           # Detailed description
owner: string                 # Owner email or team
hierarchy_level: string       # e.g., "plant", "business"
domain: string                # Business domain
tags: list[string]            # Searchable tags

# External Interface
inputs:                       # Solution-level inputs
  - name: string
    maps_to: string           # alias.port_name
    type: string              # dataset | model | folder
    required: boolean

outputs:                      # Solution-level outputs
  - name: string
    maps_from: string         # alias.port_name
    type: string

# Block Orchestration (choose one or combine)
sequence:                     # Explicit sequence
  - block_ref: string         # BLOCK_ID@VERSION
    alias: string             # Local name
    order: integer            # Execution order (1, 2, 3...)
    depends_on: string | list # Dependency aliases
    input_mapping: dict       # port -> alias.port or external
    output_mapping: dict      # port -> alias.port or external
    extends: list             # Recipe overrides (optional)

dependencies:                 # Dependency-based
  alias_name:
    block_ref: string
    requires: list[string]    # Dependency aliases
    input_mapping: dict
    output_mapping: dict
    extends: list

# Execution Configuration
execution:
  parallel_enabled: boolean   # Allow parallel block execution
  max_parallel: integer       # Max concurrent blocks
  failure_mode: string        # "fail_fast" | "continue" | "rollback"
  timeout_minutes: integer    # Solution-level timeout

# Artifacts
bundle_ref: string            # Path to solution bundle
```

---

## Wiring Model

### Input Mapping

Map solution inputs to component block inputs:

```yaml
inputs:
  - name: RAW_SENSOR_DATA
    maps_to: features.RAW_DATA
    type: dataset
    required: true

sequence:
  - block_ref: FEATURE_ENGINEERING@1.2.0
    alias: features
    input_mapping:
      RAW_DATA: $solution.RAW_SENSOR_DATA  # External input
```

### Inter-Block Wiring

Wire outputs from one block to inputs of another:

```yaml
sequence:
  - block_ref: FEATURE_ENGINEERING@1.2.0
    alias: features
    # Outputs: FEATURES

  - block_ref: ANOMALY_DETECTION@1.0.0
    alias: anomaly
    input_mapping:
      INPUT_FEATURES: features.FEATURES  # Wire from previous block
```

### Output Mapping

Map component outputs to solution outputs:

```yaml
outputs:
  - name: EQUIPMENT_ALERTS
    maps_from: alerts.ALERT_OUTPUT
    type: dataset

sequence:
  # ...
  - block_ref: ALERT_GENERATION@1.0.0
    alias: alerts
    output_mapping:
      ALERT_OUTPUT: $solution.EQUIPMENT_ALERTS  # External output
```

### Wiring Diagram

```
Solution Inputs                 Solution Outputs
      │                               ▲
      │                               │
      ▼                               │
┌─────────────────────────────────────┴─────────────────────┐
│                                                           │
│  $solution.RAW_SENSOR_DATA                               │
│         │                                                │
│         ▼                                                │
│  ┌─────────────┐                                         │
│  │  features   │                                         │
│  │  (block)    │──▶ features.FEATURES                    │
│  └─────────────┘          │                              │
│                           │                              │
│         ┌─────────────────┼─────────────────┐            │
│         │                 │                 │            │
│         ▼                 ▼                 │            │
│  ┌─────────────┐   ┌─────────────┐         │            │
│  │  anomaly    │   │    rul      │         │            │
│  │  (block)    │   │  (block)    │         │            │
│  └──────┬──────┘   └──────┬──────┘         │            │
│         │                 │                 │            │
│         ▼                 ▼                 │            │
│      anomaly.OUT      rul.OUT               │            │
│         │                 │                 │            │
│         └────────┬────────┘                 │            │
│                  │                          │            │
│                  ▼                          │            │
│           ┌─────────────┐                   │            │
│           │   alerts    │                   │            │
│           │  (block)    │──▶ $solution.EQUIPMENT_ALERTS  │
│           └─────────────┘                                │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Dependency Resolution

### Algorithm

```python
def resolve_execution_order(solution: SolutionConfig) -> List[List[str]]:
    """
    Resolve block execution order from dependencies.

    Returns:
        List of lists, where each inner list contains blocks
        that can execute in parallel.

    Example output:
        [
            ['features'],           # Stage 1: Run first
            ['anomaly', 'rul'],     # Stage 2: Run in parallel
            ['alerts']              # Stage 3: Run after stage 2
        ]
    """
    # Build dependency graph
    graph = {}
    in_degree = {}

    for alias, block_def in solution.dependencies.items():
        graph[alias] = block_def.requires
        in_degree[alias] = len(block_def.requires)

    # Kahn's algorithm for topological sort with levels
    stages = []
    remaining = set(graph.keys())

    while remaining:
        # Find all nodes with no remaining dependencies
        ready = [
            alias for alias in remaining
            if all(dep not in remaining for dep in graph[alias])
        ]

        if not ready:
            # Circular dependency detected
            raise CircularDependencyError(
                f"Circular dependency detected among: {remaining}"
            )

        stages.append(ready)
        remaining -= set(ready)

    return stages


def detect_circular_dependencies(solution: SolutionConfig) -> Optional[List[str]]:
    """
    Detect circular dependencies in solution.

    Returns:
        List of aliases forming a cycle, or None if no cycle.
    """
    # DFS-based cycle detection
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {alias: WHITE for alias in solution.dependencies}
    parent = {}

    def dfs(node):
        color[node] = GRAY
        for dep in solution.dependencies[node].requires:
            if color[dep] == GRAY:
                # Found cycle - reconstruct path
                cycle = [dep, node]
                current = node
                while parent.get(current) != dep:
                    current = parent[current]
                    cycle.append(current)
                return cycle
            if color[dep] == WHITE:
                parent[dep] = node
                result = dfs(dep)
                if result:
                    return result
        color[node] = BLACK
        return None

    for alias in solution.dependencies:
        if color[alias] == WHITE:
            cycle = dfs(alias)
            if cycle:
                return cycle

    return None
```

---

## Execution Modes

### Mode 1: Fail Fast

Stop solution execution on first block failure.

```yaml
execution:
  failure_mode: fail_fast
```

```python
def execute_fail_fast(solution, stages):
    results = {}
    for stage in stages:
        stage_results = execute_stage_parallel(stage)
        for alias, result in stage_results.items():
            if result.failed:
                raise SolutionExecutionError(
                    f"Block '{alias}' failed: {result.error}",
                    partial_results=results
                )
            results[alias] = result
    return results
```

### Mode 2: Continue on Failure

Continue executing independent blocks, skip dependents of failed blocks.

```yaml
execution:
  failure_mode: continue
```

```python
def execute_continue(solution, stages):
    results = {}
    failed_aliases = set()

    for stage in stages:
        # Filter out blocks that depend on failed blocks
        runnable = [
            alias for alias in stage
            if not any(dep in failed_aliases for dep in get_dependencies(alias))
        ]

        stage_results = execute_stage_parallel(runnable)
        for alias, result in stage_results.items():
            results[alias] = result
            if result.failed:
                failed_aliases.add(alias)

    return SolutionResult(results, failed_aliases)
```

### Mode 3: Rollback on Failure

Attempt to undo completed blocks if any block fails.

```yaml
execution:
  failure_mode: rollback
```

```python
def execute_with_rollback(solution, stages):
    completed = []

    try:
        for stage in stages:
            stage_results = execute_stage_parallel(stage)
            for alias, result in stage_results.items():
                if result.failed:
                    raise BlockFailedError(alias, result.error)
                completed.append((alias, result))
        return SolutionResult(completed)

    except BlockFailedError as e:
        # Rollback in reverse order
        for alias, result in reversed(completed):
            try:
                rollback_block(alias, result)
            except Exception as rollback_error:
                log.error(f"Rollback failed for {alias}: {rollback_error}")
        raise SolutionRollbackError(e.alias, e.error, completed)
```

---

## Solution Instantiation

### Process

```
1. Validate Solution
   ├── Check all block refs exist
   ├── Validate wiring (types match)
   └── Detect circular dependencies

2. Resolve Execution Order
   ├── Parse sequence/dependencies
   ├── Compute topological order
   └── Identify parallelizable stages

3. Create Project Structure
   ├── Create project
   ├── Create zones (one per block)
   └── Setup shared datasets

4. Instantiate Blocks (per stage)
   ├── For each block in stage:
   │   ├── Instantiate zone
   │   ├── Apply extensions
   │   └── Wire inputs
   └── Wait for stage completion

5. Wire Inter-Block Connections
   ├── Connect block outputs to inputs
   └── Create pass-through datasets if needed

6. Wire Solution I/O
   ├── Connect solution inputs to first blocks
   └── Connect last block outputs to solution outputs

7. Finalize
   ├── Validate all connections
   ├── Create bundle snapshot
   └── Return project reference
```

### Implementation

```python
def instantiate_solution(
    client: DSSClient,
    solution: SolutionConfig,
    target_project_key: str,
    input_datasets: Dict[str, str],
    output_datasets: Dict[str, str]
) -> DSSProject:
    """
    Instantiate a solution block as a new project.

    Args:
        client: Dataiku client
        solution: Solution configuration
        target_project_key: Key for new project
        input_datasets: Map solution input names to actual datasets
        output_datasets: Map solution output names to actual datasets

    Returns:
        DSSProject: The created project
    """
    # 1. Validate
    errors = validate_solution(solution, input_datasets, output_datasets)
    if errors:
        raise SolutionValidationError(errors)

    # 2. Resolve order
    if solution.sequence:
        stages = parse_sequence(solution.sequence)
    else:
        stages = resolve_execution_order(solution)

    # 3. Create project
    project = client.create_project(target_project_key, solution.name)

    try:
        # 4. Instantiate blocks by stage
        block_instances = {}
        for stage in stages:
            for alias in stage:
                block_def = get_block_definition(solution, alias)
                instance = instantiate_block(
                    project=project,
                    block_ref=block_def.block_ref,
                    zone_name=f"{alias}_zone",
                    extensions=block_def.extends
                )
                block_instances[alias] = instance

        # 5. Wire inter-block connections
        for alias, block_def in get_all_blocks(solution):
            for input_port, source in block_def.input_mapping.items():
                if source.startswith('$solution.'):
                    # External input
                    external_name = source.replace('$solution.', '')
                    actual_dataset = input_datasets[external_name]
                else:
                    # Inter-block wire
                    source_alias, source_port = source.split('.')
                    actual_dataset = block_instances[source_alias].outputs[source_port]

                wire_input(project, block_instances[alias], input_port, actual_dataset)

        # 6. Wire solution outputs
        for output in solution.outputs:
            source_alias, source_port = output.maps_from.split('.')
            actual_source = block_instances[source_alias].outputs[source_port]
            actual_target = output_datasets[output.name]
            create_sync_recipe(project, actual_source, actual_target)

        # 7. Finalize
        validate_project_flow(project)

        return project

    except Exception as e:
        # Cleanup on failure
        project.delete()
        raise SolutionInstantiationError(f"Failed to instantiate solution: {e}")
```

---

## Model Blocks in Solutions

### Trained Model Blocks

Blocks that include trained models for inference:

```yaml
block_id: ANOMALY_DETECTOR_MODEL
version: 1.0.0
type: zone

inputs:
  - name: FEATURES
    type: dataset

outputs:
  - name: PREDICTIONS
    type: dataset

contains:
  datasets: [FEATURES_PREPARED, PREDICTIONS]
  recipes: [prepare_features, score_model]
  models: [isolation_forest_v2]  # Trained model ID
```

### Model Deployment Pattern

```yaml
# Solution using model blocks
block_id: PREDICTIVE_MAINTENANCE_SOLUTION
version: 1.0.0
type: solution

sequence:
  - block_ref: FEATURE_ENGINEERING@1.2.0
    alias: features

  - block_ref: ANOMALY_DETECTOR_MODEL@1.0.0
    alias: anomaly_model
    depends_on: features
    input_mapping:
      FEATURES: features.OUTPUT

  - block_ref: RUL_PREDICTOR_MODEL@1.0.0
    alias: rul_model
    depends_on: features
    input_mapping:
      FEATURES: features.OUTPUT

  - block_ref: ALERT_RULES@1.0.0
    alias: alerts
    depends_on: [anomaly_model, rul_model]
    input_mapping:
      ANOMALY_SCORES: anomaly_model.PREDICTIONS
      RUL_SCORES: rul_model.PREDICTIONS
```

### Model Version Pinning

```yaml
sequence:
  - block_ref: ANOMALY_DETECTOR_MODEL@1.0.0
    alias: anomaly
    model_versions:
      isolation_forest_v2: "v3"  # Pin specific model version
```

---

## Solution Validation

### Validation Rules

```python
def validate_solution(solution: SolutionConfig) -> List[ValidationError]:
    errors = []

    # 1. All block refs must exist
    for alias, block_def in get_all_blocks(solution):
        if not block_exists(block_def.block_ref):
            errors.append(ValidationError(
                f"Block not found: {block_def.block_ref}",
                path=f"blocks.{alias}"
            ))

    # 2. All dependencies must be valid aliases
    for alias, block_def in get_all_blocks(solution):
        deps = get_dependencies(block_def)
        for dep in deps:
            if dep not in get_all_aliases(solution):
                errors.append(ValidationError(
                    f"Unknown dependency: {dep}",
                    path=f"blocks.{alias}.depends_on"
                ))

    # 3. No circular dependencies
    cycle = detect_circular_dependencies(solution)
    if cycle:
        errors.append(ValidationError(
            f"Circular dependency: {' -> '.join(cycle)}",
            path="dependencies"
        ))

    # 4. Input mappings are valid
    for alias, block_def in get_all_blocks(solution):
        block_meta = get_block_metadata(block_def.block_ref)
        for input_port, source in block_def.input_mapping.items():
            # Check port exists
            if input_port not in [p.name for p in block_meta.inputs]:
                errors.append(ValidationError(
                    f"Unknown input port: {input_port}",
                    path=f"blocks.{alias}.input_mapping"
                ))
            # Check source is valid
            if not is_valid_source(source, solution):
                errors.append(ValidationError(
                    f"Invalid source: {source}",
                    path=f"blocks.{alias}.input_mapping.{input_port}"
                ))

    # 5. All required inputs are mapped
    for alias, block_def in get_all_blocks(solution):
        block_meta = get_block_metadata(block_def.block_ref)
        for input_port in block_meta.inputs:
            if input_port.required and input_port.name not in block_def.input_mapping:
                errors.append(ValidationError(
                    f"Required input not mapped: {input_port.name}",
                    path=f"blocks.{alias}"
                ))

    # 6. Solution outputs map from valid sources
    for output in solution.outputs:
        if not is_valid_output_source(output.maps_from, solution):
            errors.append(ValidationError(
                f"Invalid output source: {output.maps_from}",
                path=f"outputs.{output.name}"
            ))

    return errors
```

---

## Example: Complete Equipment Health Solution

```yaml
block_id: EQUIPMENT_HEALTH_SOLUTION
version: 2.0.0
type: solution
blocked: true

name: "Complete Equipment Health Monitoring"
description: |
  End-to-end solution for equipment health monitoring including
  feature engineering, anomaly detection, remaining useful life
  prediction, and automated alerting.

hierarchy_level: plant
domain: predictive_maintenance
tags: [equipment, health, anomaly, rul, alerts]

# Solution-level interface
inputs:
  - name: SENSOR_DATA
    maps_to: features.RAW_DATA
    type: dataset
    required: true
    description: "Raw sensor readings from equipment"

  - name: EQUIPMENT_METADATA
    maps_to: features.METADATA
    type: dataset
    required: false
    description: "Equipment specifications and thresholds"

outputs:
  - name: HEALTH_SCORES
    maps_from: rul.RUL_SCORES
    type: dataset
    description: "Equipment health scores and RUL estimates"

  - name: ALERTS
    maps_from: alerting.ALERT_OUTPUT
    type: dataset
    description: "Generated alerts for action"

# Block orchestration
sequence:
  - block_ref: SENSOR_FEATURE_ENGINEERING@1.2.0
    alias: features
    order: 1
    input_mapping:
      RAW_DATA: $solution.SENSOR_DATA
      METADATA: $solution.EQUIPMENT_METADATA

  - block_ref: ISOLATION_FOREST_ANOMALY@2.0.0
    alias: anomaly
    order: 2
    depends_on: features
    input_mapping:
      FEATURES: features.ENGINEERED_FEATURES

  - block_ref: LSTM_RUL_PREDICTOR@1.5.0
    alias: rul
    order: 2
    depends_on: features
    input_mapping:
      FEATURES: features.ENGINEERED_FEATURES

  - block_ref: RULE_BASED_ALERTING@1.0.0
    alias: alerting
    order: 3
    depends_on: [anomaly, rul]
    input_mapping:
      ANOMALY_SCORES: anomaly.SCORES
      RUL_PREDICTIONS: rul.RUL_SCORES
    output_mapping:
      ALERT_OUTPUT: $solution.ALERTS

# Execution configuration
execution:
  parallel_enabled: true
  max_parallel: 2
  failure_mode: fail_fast
  timeout_minutes: 60

# Artifacts
bundle_ref: bundles/EQUIPMENT_HEALTH_SOLUTION_v2.0.0.zip
```
