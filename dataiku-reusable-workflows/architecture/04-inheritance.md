# Extension and Inheritance Model

## Overview

Blocks support two primary extension patterns that allow consumers to customize behavior without modifying the source block:

1. **Python Class Inheritance** - Extend block logic through project library code
2. **Recipe Override** - Replace specific recipes with custom implementations

Both patterns ensure:
- Source block remains unchanged
- Other consumers are not affected
- Extensions are explicit and traceable
- Compatible interfaces are enforced

---

## Pattern 1: Python Class Inheritance

### Concept

Block authors expose extension points as Python base classes in project libraries. Consumers inherit from these classes to customize behavior.

### Architecture

```
Source Block Project               Consumer Project
┌────────────────────────┐        ┌────────────────────────┐
│ Library/               │        │ Library/               │
│ └── blocks/            │        │ └── custom/            │
│     └── feature_eng/   │        │     └── my_features.py │
│         ├── __init__.py│        │         │              │
│         └── base.py    │◀───────│         └── imports    │
│             │          │        │                        │
│             └── class  │        │                        │
│                BaseEng │        │                        │
└────────────────────────┘        └────────────────────────┘
```

### Implementation

#### Step 1: Block Author Defines Extension Points

```python
# Source: COMPRESSOR_SOLUTIONS/Library/blocks/feature_eng/base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import pandas as pd

class BaseFeatureEngineer(ABC):
    """
    Base class for feature engineering.

    Extend this class to customize feature computation while
    maintaining compatibility with the block's pipeline.

    Extension Points:
    - preprocess(): Override to add custom preprocessing
    - compute_features(): Override to add/modify features
    - postprocess(): Override to add custom postprocessing

    Required Interface:
    - Input: DataFrame with columns: timestamp, sensor_id, value
    - Output: DataFrame with original columns plus feature columns
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocessing step. Override to customize.

        Default: No-op, returns input unchanged.
        """
        return df

    @abstractmethod
    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Main feature computation. Must be implemented.

        Args:
            df: Preprocessed input DataFrame

        Returns:
            DataFrame with computed features added
        """
        pass

    def postprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Postprocessing step. Override to customize.

        Default: No-op, returns input unchanged.
        """
        return df

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Full pipeline execution. Do not override.
        """
        df = self.preprocess(df)
        df = self.compute_features(df)
        df = self.postprocess(df)
        return df


class StandardFeatureEngineer(BaseFeatureEngineer):
    """
    Standard implementation used by the block.

    This is what runs if no override is provided.
    """

    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        # Standard feature computation
        df['rolling_mean'] = df.groupby('sensor_id')['value'].transform(
            lambda x: x.rolling(window=10).mean()
        )
        df['rolling_std'] = df.groupby('sensor_id')['value'].transform(
            lambda x: x.rolling(window=10).std()
        )
        return df
```

#### Step 2: Block Author Documents Extension Points

The block's Wiki article includes:

```markdown
## Extension Points

This block supports Python class inheritance for customization.

### Available Base Classes

| Class | Location | Purpose |
|-------|----------|---------|
| `BaseFeatureEngineer` | `blocks.feature_eng.base` | Feature computation |
| `BaseAnomalyDetector` | `blocks.anomaly.base` | Anomaly detection |

### How to Extend

1. Import the base class in your project library
2. Create a subclass with your customizations
3. Reference your class in the recipe override

```python
# Your project: Library/custom/my_features.py
from blocks.feature_eng.base import BaseFeatureEngineer

class MyFeatureEngineer(BaseFeatureEngineer):
    def compute_features(self, df):
        # Call parent for standard features
        df = super().compute_features(df)
        # Add custom features
        df['my_custom_feature'] = df['value'] ** 2
        return df
```

### Interface Contract

Input DataFrame must have:
- `timestamp`: datetime
- `sensor_id`: string
- `value`: float

Output DataFrame must include input columns plus any feature columns.
```

#### Step 3: Consumer Extends the Class

```python
# Consumer: MY_PROJECT/Library/custom/enhanced_features.py

from blocks.feature_eng.base import BaseFeatureEngineer
import numpy as np
from scipy import signal

class EnhancedFeatureEngineer(BaseFeatureEngineer):
    """
    Enhanced feature engineering with FFT and custom features.
    """

    def __init__(self, config=None):
        super().__init__(config)
        self.fft_window = config.get('fft_window', 256) if config else 256

    def preprocess(self, df):
        """Add custom preprocessing: outlier removal."""
        df = super().preprocess(df)

        # Remove outliers using IQR
        Q1 = df['value'].quantile(0.25)
        Q3 = df['value'].quantile(0.75)
        IQR = Q3 - Q1
        df = df[(df['value'] >= Q1 - 1.5*IQR) & (df['value'] <= Q3 + 1.5*IQR)]

        return df

    def compute_features(self, df):
        """Add FFT-based features in addition to standard features."""
        # Get standard features from parent
        df = super().compute_features(df)

        # Add FFT features
        for sensor in df['sensor_id'].unique():
            mask = df['sensor_id'] == sensor
            values = df.loc[mask, 'value'].values

            if len(values) >= self.fft_window:
                fft_result = np.abs(np.fft.fft(values[-self.fft_window:]))
                df.loc[mask, 'fft_peak_freq'] = np.argmax(fft_result[:self.fft_window//2])
                df.loc[mask, 'fft_energy'] = np.sum(fft_result ** 2)

        return df
```

#### Step 4: Consumer References Extension in Config

```yaml
# Consumer's IaC config
blocks:
  - ref: "BLOCKS_REGISTRY/FEATURE_ENGINEERING@1.2.0"
    instance_name: my_features
    extends:
      - recipe: compute_features
        use_class: custom.enhanced_features.EnhancedFeatureEngineer
        class_config:
          fft_window: 512
```

#### Step 5: IaC Engine Wires Extension

When instantiating the block, the IaC engine:

1. Creates the zone with all block components
2. Modifies the recipe to use the custom class
3. Updates recipe parameters to reference the class

```python
def apply_class_extension(
    project: DSSProject,
    recipe_name: str,
    custom_class: str,
    class_config: dict
):
    """
    Modify recipe to use custom class.

    Args:
        project: Target project
        recipe_name: Recipe to modify
        custom_class: Fully qualified class name (e.g., custom.enhanced_features.EnhancedFeatureEngineer)
        class_config: Configuration to pass to class __init__
    """
    recipe = project.get_recipe(recipe_name)
    settings = recipe.get_settings()

    # Get current code
    code = settings.get_code()

    # Inject class override
    override_code = f'''
# AUTO-GENERATED: Class extension
from {".".join(custom_class.split(".")[:-1])} import {custom_class.split(".")[-1]}
_engineer_class = {custom_class.split(".")[-1]}
_engineer_config = {repr(class_config)}

# Replace standard class with extension
engineer = _engineer_class(_engineer_config)
'''

    # Prepend to existing code
    new_code = override_code + "\n\n# Original code follows\n" + code

    settings.set_code(new_code)
    settings.save()
```

---

## Pattern 2: Recipe Override

### Concept

Replace an entire recipe within a block with a custom implementation that has the same input/output signature.

### Architecture

```
Block (as instantiated)
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  [INPUT] ──▶ [recipe_1] ──▶ [ds_1]                        │
│                               │                            │
│                               ▼                            │
│                          ╔═════════════╗                   │
│                          ║ recipe_2    ║ ◀── OVERRIDDEN   │
│                          ║ (custom)    ║                   │
│                          ╚═════════════╝                   │
│                               │                            │
│                               ▼                            │
│                          [recipe_3] ──▶ [OUTPUT]           │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Implementation

#### Step 1: Identify Override Target

The block documentation lists which recipes can be overridden:

```markdown
## Overridable Recipes

| Recipe | Inputs | Outputs | Purpose |
|--------|--------|---------|---------|
| `signal_smoothing` | RAW_DATA | SMOOTHED_DATA | Signal preprocessing |
| `feature_compute` | SMOOTHED_DATA | FEATURES | Feature calculation |
| `anomaly_score` | FEATURES | SCORES | Anomaly scoring |

Note: Overrides must maintain the same input/output datasets.
```

#### Step 2: Consumer Defines Override Recipe

```yaml
# Consumer's IaC config

blocks:
  - ref: "BLOCKS_REGISTRY/ANOMALY_DETECTION@1.0.0"
    instance_name: my_anomaly
    zone_name: anomaly_zone
    inputs:
      FEATURES: my_features
    outputs:
      ANOMALIES: my_anomalies
    extends:
      - recipe: anomaly_score
        override_with: my_custom_scorer

# Custom recipe definition
recipes:
  - name: my_custom_scorer
    type: python
    inputs:
      - name: FEATURES
        dataset: my_features
    outputs:
      - name: SCORES
        dataset: my_anomalies
    code: |
      import dataiku
      import pandas as pd
      from sklearn.ensemble import IsolationForest

      # Read input
      input_ds = dataiku.Dataset("FEATURES")
      df = input_ds.get_dataframe()

      # Custom anomaly detection
      model = IsolationForest(contamination=0.1, random_state=42)
      df['anomaly_score'] = model.fit_predict(df.select_dtypes(include=['float64']))
      df['is_anomaly'] = df['anomaly_score'] == -1

      # Write output
      output_ds = dataiku.Dataset("SCORES")
      output_ds.write_with_schema(df)
```

#### Step 3: Validation

The IaC engine validates override compatibility:

```python
def validate_recipe_override(
    block_metadata: BlockMetadata,
    override_recipe_name: str,
    custom_recipe: RecipeConfig
) -> List[ValidationError]:
    """
    Validate that custom recipe is compatible with block recipe.

    Checks:
    1. Override target exists in block
    2. Input count matches
    3. Output count matches
    4. Input types are compatible
    5. Output types are compatible
    """
    errors = []

    # Find original recipe in block
    original = None
    for recipe in block_metadata.contains.recipes:
        if recipe.name == override_recipe_name:
            original = recipe
            break

    if original is None:
        errors.append(ValidationError(
            f"Recipe '{override_recipe_name}' not found in block. "
            f"Overridable recipes: {[r.name for r in block_metadata.contains.recipes]}"
        ))
        return errors

    # Check input count
    if len(custom_recipe.inputs) != len(original.inputs):
        errors.append(ValidationError(
            f"Input count mismatch. Expected {len(original.inputs)}, got {len(custom_recipe.inputs)}"
        ))

    # Check output count
    if len(custom_recipe.outputs) != len(original.outputs):
        errors.append(ValidationError(
            f"Output count mismatch. Expected {len(original.outputs)}, got {len(custom_recipe.outputs)}"
        ))

    # Check input names (order matters)
    for i, (orig_input, custom_input) in enumerate(zip(original.inputs, custom_recipe.inputs)):
        if orig_input.name != custom_input.name:
            errors.append(ValidationError(
                f"Input {i} name mismatch. Expected '{orig_input.name}', got '{custom_input.name}'"
            ))

    # Check output names
    for i, (orig_output, custom_output) in enumerate(zip(original.outputs, custom_recipe.outputs)):
        if orig_output.name != custom_output.name:
            errors.append(ValidationError(
                f"Output {i} name mismatch. Expected '{orig_output.name}', got '{custom_output.name}'"
            ))

    return errors
```

#### Step 4: Application

```python
def apply_recipe_override(
    project: DSSProject,
    zone_name: str,
    original_recipe_name: str,
    custom_recipe: RecipeConfig,
    input_mapping: Dict[str, str],
    output_mapping: Dict[str, str]
):
    """
    Replace a block recipe with custom implementation.

    Args:
        project: Target project
        zone_name: Zone where block is instantiated
        original_recipe_name: Recipe to replace
        custom_recipe: Custom recipe definition
        input_mapping: Block input name -> actual dataset name
        output_mapping: Block output name -> actual dataset name
    """
    # 1. Delete original recipe (if it was created)
    try:
        original = project.get_recipe(original_recipe_name)
        original.delete()
    except:
        pass  # Recipe might not exist yet

    # 2. Create custom recipe with proper wiring
    creator = project.new_recipe(custom_recipe.type, custom_recipe.name)

    # Map inputs
    for input_def in custom_recipe.inputs:
        actual_dataset = input_mapping.get(input_def.name, input_def.dataset)
        creator.with_input(actual_dataset)

    # Map outputs
    for output_def in custom_recipe.outputs:
        actual_dataset = output_mapping.get(output_def.name, output_def.dataset)
        creator.with_output(actual_dataset)

    recipe = creator.build()

    # 3. Set recipe code/configuration
    settings = recipe.get_settings()
    if hasattr(custom_recipe, 'code'):
        settings.set_code(custom_recipe.code)
    settings.save()

    # 4. Move to zone
    flow = project.get_flow()
    zone = flow.get_zone(zone_name)
    zone.add_item(recipe)
```

---

## Pattern 3: Composition (Post-Processing)

### Concept

Add additional processing downstream of block outputs without modifying the block itself.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Consumer Project                         │
│                                                                 │
│  ┌─────────────────────────────┐                               │
│  │   Block (unmodified)        │                               │
│  │                             │                               │
│  │  [INPUT] ──▶ ... ──▶ [OUT] ─┼──▶ [custom_recipe] ──▶ [EXT] │
│  │                             │                               │
│  └─────────────────────────────┘                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

```yaml
# Consumer's IaC config

blocks:
  - ref: "BLOCKS_REGISTRY/FEATURE_ENGINEERING@1.2.0"
    instance_name: base_features
    inputs:
      RAW_DATA: my_raw_data
    outputs:
      FEATURES: base_features_output  # Block output

# Extend via additional datasets and recipes
datasets:
  - name: extended_features
    type: managed
    format_type: parquet

recipes:
  - name: add_custom_features
    type: python
    inputs:
      - name: base_features
        dataset: base_features_output  # Consumes block output
    outputs:
      - name: extended
        dataset: extended_features
    code: |
      import dataiku
      import pandas as pd

      # Read block output
      input_ds = dataiku.Dataset("base_features")
      df = input_ds.get_dataframe()

      # Add custom features
      df['custom_ratio'] = df['feature_a'] / df['feature_b']
      df['custom_product'] = df['feature_a'] * df['feature_c']

      # Write extended output
      output_ds = dataiku.Dataset("extended")
      output_ds.write_with_schema(df)
```

This pattern:
- Leaves block completely unmodified
- Adds new processing after block outputs
- Can be combined with other patterns

---

## Extension Resolution Order

When multiple extension patterns are used together:

```
1. Block instantiation (copy zone structure)
       │
       ▼
2. Class extensions applied (modify recipe code)
       │
       ▼
3. Recipe overrides applied (replace recipes)
       │
       ▼
4. Wiring completed (connect inputs/outputs)
       │
       ▼
5. Composition recipes created (post-processing)
```

---

## Extension Compatibility Matrix

| Extension Type | Affects Source | Affects Others | Requires Schema Match | Versioned |
|---------------|----------------|----------------|----------------------|-----------|
| Python Inheritance | No | No | Method signature | Via class |
| Recipe Override | No | No | Yes (I/O) | Via config |
| Composition | No | No | Output schema | Via config |

---

## Best Practices

### For Block Authors

1. **Design for Extension**
   - Identify logical extension points
   - Create base classes with clear interfaces
   - Document extension contracts

2. **Use Dependency Injection**
   - Pass configurable components as parameters
   - Allow class substitution

3. **Maintain Backward Compatibility**
   - Don't change base class signatures in minor versions
   - Deprecate before removing

### For Block Consumers

1. **Prefer Composition**
   - Composition is safest (no coupling to internals)
   - Use when adding new features

2. **Use Inheritance for Behavior Changes**
   - When you need to modify existing logic
   - Always call `super()` methods

3. **Use Override for Complete Replacement**
   - When you need entirely different implementation
   - Validate I/O compatibility carefully

4. **Document Extensions**
   - Note which blocks are extended
   - Document why extension was needed
   - Track version compatibility

---

## Error Handling

### Class Extension Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| `ImportError` | Base class not found | Check block library is accessible |
| `TypeError` | Incompatible method signature | Match parent method signature |
| `AttributeError` | Missing required method | Implement all abstract methods |

### Recipe Override Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| `InputMismatchError` | Wrong number of inputs | Match original recipe inputs |
| `OutputMismatchError` | Wrong number of outputs | Match original recipe outputs |
| `TypeMismatchError` | Incompatible data types | Ensure schema compatibility |

---

## Testing Extensions

### Unit Tests

```python
def test_class_extension_compatibility():
    """Test that extension class is compatible with base."""
    from blocks.feature_eng.base import BaseFeatureEngineer
    from custom.enhanced_features import EnhancedFeatureEngineer

    # Check inheritance
    assert issubclass(EnhancedFeatureEngineer, BaseFeatureEngineer)

    # Check interface
    engineer = EnhancedFeatureEngineer()
    assert hasattr(engineer, 'run')
    assert hasattr(engineer, 'compute_features')

    # Check output schema
    test_df = create_test_input()
    output = engineer.run(test_df)
    assert_schema_compatible(output, expected_schema)
```

### Integration Tests

```python
def test_recipe_override_execution():
    """Test that overridden recipe produces valid output."""
    # Setup: Create test project with block + override
    # Execute: Run the overridden recipe
    # Verify: Output schema matches, data is valid
    pass
```
