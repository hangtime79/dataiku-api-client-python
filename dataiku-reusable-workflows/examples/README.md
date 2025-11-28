# Example Configurations

This directory contains example YAML configurations demonstrating how to use the Dataiku Reusable Workflows system with IaC.

## Examples Overview

| Example | Description | Complexity |
|---------|-------------|------------|
| [01-simple-block.yaml](01-simple-block.yaml) | Single block with basic I/O | Beginner |
| [02-chained-blocks.yaml](02-chained-blocks.yaml) | Multiple blocks in sequence | Beginner |
| [03-block-with-recipe-override.yaml](03-block-with-recipe-override.yaml) | Custom recipe replacing block recipe | Intermediate |
| [04-block-with-class-extension.yaml](04-block-with-class-extension.yaml) | Injecting custom class into recipe | Intermediate |
| [05-multi-instance-blocks.yaml](05-multi-instance-blocks.yaml) | Same block instantiated multiple times | Intermediate |
| [06-solution-block.yaml](06-solution-block.yaml) | Pre-composed multi-block solution | Advanced |

## Quick Start

### Validate Configuration

```bash
# Using the IaC CLI
python -m dataikuapi.iac.cli.validate -c examples/01-simple-block.yaml

# Expected output:
# Configuration valid!
# - 1 block reference(s)
# - 2 dataset(s)
```

### Generate Plan

```bash
# Generate execution plan
python -m dataikuapi.iac.cli.plan -c examples/01-simple-block.yaml -e dev

# Expected output:
# Plan for SIMPLE_BLOCK_EXAMPLE:
#
# Block Operations:
#   + instantiate FEATURE_ENG@1.2.0 as feature_instance
#     zone: feature_zone
#     inputs:
#       RAW_DATA → source_sensors
#     outputs:
#       FEATURES → computed_features
#
# Dataset Operations:
#   + create source_sensors (sql_table)
#   + create computed_features (managed)
#
# Plan: 1 block to instantiate, 2 datasets to create
```

### Apply Configuration

```bash
# Apply to Dataiku (requires confirmation)
python -m dataikuapi.iac.cli.apply -c examples/01-simple-block.yaml -e dev

# With auto-approve
python -m dataikuapi.iac.cli.apply -c examples/01-simple-block.yaml -e dev --yes
```

## Example Details

### 01 - Simple Block

**When to use:** You want to use a pre-built block with your data.

```yaml
blocks:
  - ref: "BLOCKS_REGISTRY/FEATURE_ENG@1.2.0"
    instance_name: feature_instance
    zone_name: feature_zone
    inputs:
      RAW_DATA: source_sensors
    outputs:
      FEATURES: computed_features
```

**Key concepts:**
- `ref` - Reference to block in registry
- `inputs` - Map block ports to your datasets
- `outputs` - Name your output datasets

---

### 02 - Chained Blocks

**When to use:** Building a pipeline with multiple processing stages.

```yaml
blocks:
  - ref: "BLOCKS_REGISTRY/FEATURE_ENG@1.2.0"
    outputs:
      FEATURES: intermediate_features  # Output of block 1

  - ref: "BLOCKS_REGISTRY/ANOMALY_DET@2.0.0"
    inputs:
      FEATURES: intermediate_features  # Input to block 2 (connected!)
```

**Key concepts:**
- Blocks connect via shared dataset names
- Output of one block = Input of next block
- IaC handles dependency ordering

---

### 03 - Recipe Override

**When to use:** You need to completely replace a recipe's logic.

```yaml
blocks:
  - ref: "BLOCKS_REGISTRY/FEATURE_ENG@1.2.0"
    extends:
      - recipe: signal_smoothing       # Recipe in the block
        override_with: custom_smoothing  # Your custom recipe
```

**Key concepts:**
- `extends` - List of extensions to apply
- `override_with` - Name of your custom recipe
- Custom recipe must have compatible I/O

---

### 04 - Class Extension

**When to use:** You want to customize behavior while keeping the recipe structure.

```yaml
blocks:
  - ref: "BLOCKS_REGISTRY/FEATURE_ENG@1.2.0"
    extends:
      - recipe: feature_compute
        use_class: custom_features.turbine.TurbineFeatureExtractor
        class_config:
          window_size: 1024
          include_fft_features: true
```

**Key concepts:**
- `use_class` - Fully qualified class path
- `class_config` - Parameters for class constructor
- Class must extend the block's base class

---

### 05 - Multiple Instances

**When to use:** Same processing for different data sources.

```yaml
blocks:
  # Same block, different data
  - ref: "BLOCKS_REGISTRY/FEATURES@1.0.0"
    instance_name: compressor_features  # Unique name
    inputs:
      RAW_DATA: compressor_data

  - ref: "BLOCKS_REGISTRY/FEATURES@1.0.0"
    instance_name: pump_features        # Different unique name
    inputs:
      RAW_DATA: pump_data
```

**Key concepts:**
- Each instance must have unique `instance_name`
- Each instance gets its own zone
- Outputs can be combined downstream

---

### 06 - Solution Block

**When to use:** Deploy a complete pre-built solution.

```yaml
solutions:
  - ref: "BLOCKS_REGISTRY/MONITORING_SOLUTION@1.0.0"
    instance_name: monitoring_solution
    zone_prefix: monitoring
    inputs:
      RAW_DATA: my_data
    outputs:
      ALERTS: my_alerts
    block_overrides:
      FEATURE_ENG:
        extends:
          - recipe: smoothing
            use_class: custom.MySmoother
```

**Key concepts:**
- Solutions contain multiple blocks
- `zone_prefix` creates organized zones
- `block_overrides` customize internal blocks

## Pattern Reference

### Input/Output Mapping

```yaml
inputs:
  BLOCK_PORT_NAME: your_dataset_name
outputs:
  BLOCK_PORT_NAME: your_output_name
```

### Recipe Override

```yaml
extends:
  - recipe: original_recipe_name
    override_with: your_custom_recipe
```

### Class Extension

```yaml
extends:
  - recipe: recipe_name
    use_class: module.path.ClassName
    class_config:
      param1: value1
      param2: value2
```

## Common Patterns

### Data Source Variations

Different environments might use different data sources:

```yaml
# dev.yaml
datasets:
  - name: source_data
    type: filesystem
    path: /data/samples/

# prod.yaml
datasets:
  - name: source_data
    type: sql_table
    connection: PRODUCTION_DW
    table: sensor_readings
```

### Version Pinning

Always pin block versions in production:

```yaml
# Development - use latest
blocks:
  - ref: "BLOCKS_REGISTRY/FEATURE_ENG@latest"

# Production - pin specific version
blocks:
  - ref: "BLOCKS_REGISTRY/FEATURE_ENG@1.2.0"
```

### Protected Blocks Only

For production, use only blocked (protected) blocks:

```python
# In your CI/CD validation
agent = ExecutingAgent(client)
results = agent.search(BlockQuery(blocked_only=True))
```

## Troubleshooting

### Block Not Found

```
Error: Block 'FEATURE_ENG' not found in registry 'BLOCKS_REGISTRY'
```

**Fix:** Verify block exists with:
```bash
python -c "
from dataikuapi import DSSClient
client = DSSClient('https://dss.example.com', 'api-key')
project = client.get_project('BLOCKS_REGISTRY')
print(project.get_library().list_files('blocks/'))
"
```

### Required Input Not Mapped

```
Error: Required input 'RAW_DATA' is not mapped
```

**Fix:** Add the input mapping:
```yaml
inputs:
  RAW_DATA: your_source_dataset
```

### Invalid Class Path

```
Error: Invalid class path 'MyClass' - must be fully qualified
```

**Fix:** Use full module path:
```yaml
use_class: mypackage.mymodule.MyClass  # Not just 'MyClass'
```
