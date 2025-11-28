# IaC Block Extension Specification

## Overview

This specification defines how the existing IaC engine is extended to support block references. The extension follows the established patterns in the IaC codebase (Waves 1-3) and integrates cleanly with existing components.

---

## Functional Requirements

### FR-1: Configuration Parsing

The parser MUST support a `blocks:` section in IaC configuration:

```yaml
blocks:
  - ref: "REGISTRY/BLOCK_ID@VERSION"
    instance_name: string
    zone_name: string
    inputs:
      PORT_NAME: dataset_name
    outputs:
      PORT_NAME: dataset_name
    extends:
      - recipe: recipe_name
        override_with: custom_recipe_name
      - recipe: recipe_name
        use_class: module.ClassName
        class_config:
          key: value
```

### FR-2: Block Reference Validation

The validator MUST check:
- Block reference format (`REGISTRY/BLOCK_ID@VERSION`)
- Block exists in registry
- Version exists (or "latest" resolves)
- All required inputs are mapped
- Input types are compatible
- Override recipes have compatible I/O
- No circular dependencies in solution blocks

### FR-3: State Management

State MUST track:
- Block resource type (`ResourceType.BLOCK`)
- Instantiated blocks with their configuration
- Mapping from block ports to actual datasets
- Applied extensions

### FR-4: Plan Generation

Plans MUST include:
- Block instantiation operations
- Zone creation operations
- Recipe copy/override operations
- Wiring operations (connecting datasets)
- Dependency ordering

### FR-5: Apply Execution

Apply MUST:
- Create zones for blocks
- Copy block recipes to target project
- Apply recipe overrides
- Apply class extensions
- Wire inputs and outputs
- Validate final flow structure

---

## Integration with Existing IaC

### Existing Architecture (Reference)

```
dataikuapi/iac/
├── __init__.py
├── cli/                    # CLI interface
│   ├── __init__.py
│   ├── main.py
│   └── plan.py
├── config/                 # Configuration parsing
│   ├── __init__.py
│   ├── parser.py          # ← MODIFY
│   ├── validator.py       # ← MODIFY
│   └── schemas/
├── models/                 # Data models
│   ├── __init__.py
│   ├── config.py
│   └── state.py           # ← MODIFY
├── planner/               # Plan generation
│   ├── __init__.py
│   └── engine.py          # ← MODIFY
├── sync/                  # Resource synchronization
│   ├── __init__.py
│   ├── base.py
│   ├── project.py
│   ├── dataset.py
│   └── recipe.py
├── diff.py
└── manager.py             # ← MODIFY (register BlockSync)
```

### New Files to Create

```
dataikuapi/iac/
├── models/
│   └── block.py           # NEW: Block config models
├── sync/
│   └── block.py           # NEW: BlockSync implementation
└── workflows/
    └── blocks/
        ├── __init__.py
        ├── instantiator.py # NEW: Block instantiation logic
        └── resolver.py     # NEW: Block reference resolution
```

---

## Configuration Schema

### BlockReference Schema

```python
@dataclass
class BlockReferenceConfig:
    """Block reference in IaC configuration."""

    ref: str                          # "REGISTRY/BLOCK_ID@VERSION"
    instance_name: str                # Local instance name
    zone_name: str                    # Target zone name

    inputs: Dict[str, str]            # port_name -> dataset_name
    outputs: Dict[str, str]           # port_name -> dataset_name

    extends: List[ExtensionConfig]    # Optional extensions

    # Parsed from ref
    registry: str = ""
    block_id: str = ""
    version: str = ""

    def parse_ref(self):
        """Parse ref string into components."""
        # Format: "REGISTRY/BLOCK_ID@VERSION"
        parts = self.ref.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid block ref format: {self.ref}")

        self.registry = parts[0]
        block_version = parts[1]

        if "@" in block_version:
            self.block_id, self.version = block_version.split("@")
        else:
            self.block_id = block_version
            self.version = "latest"
```

### ExtensionConfig Schema

```python
@dataclass
class RecipeOverrideConfig:
    """Recipe override extension."""

    recipe: str                       # Original recipe name in block
    override_with: str                # Custom recipe name in config

@dataclass
class ClassOverrideConfig:
    """Class override extension."""

    recipe: str                       # Recipe to modify
    use_class: str                    # Fully qualified class name
    class_config: Dict[str, Any]      # Config for class __init__

@dataclass
class ExtensionConfig:
    """Extension configuration (union type)."""

    recipe: str                       # Target recipe

    # One of:
    override_with: Optional[str] = None
    use_class: Optional[str] = None
    class_config: Dict[str, Any] = field(default_factory=dict)
```

---

## Parser Extension

### Modification to parser.py

```python
# In ConfigParser class

def parse(self, config_dict: dict) -> ParsedConfig:
    """Parse configuration dictionary."""
    parsed = ParsedConfig()

    # ... existing parsing ...

    # NEW: Parse blocks section
    if "blocks" in config_dict:
        parsed.blocks = self._parse_blocks(config_dict["blocks"])

    return parsed

def _parse_blocks(self, blocks_list: list) -> List[BlockReferenceConfig]:
    """Parse blocks section."""
    blocks = []

    for block_dict in blocks_list:
        block = BlockReferenceConfig(
            ref=block_dict["ref"],
            instance_name=block_dict.get("instance_name", ""),
            zone_name=block_dict.get("zone_name", ""),
            inputs=block_dict.get("inputs", {}),
            outputs=block_dict.get("outputs", {}),
            extends=self._parse_extensions(block_dict.get("extends", []))
        )
        block.parse_ref()
        blocks.append(block)

    return blocks

def _parse_extensions(self, extends_list: list) -> List[ExtensionConfig]:
    """Parse extension configurations."""
    extensions = []

    for ext_dict in extends_list:
        ext = ExtensionConfig(
            recipe=ext_dict["recipe"],
            override_with=ext_dict.get("override_with"),
            use_class=ext_dict.get("use_class"),
            class_config=ext_dict.get("class_config", {})
        )
        extensions.append(ext)

    return extensions
```

---

## Validator Extension

### Modification to validator.py

```python
# In ConfigValidator class

def validate(self, config: ParsedConfig) -> List[ValidationError]:
    """Validate parsed configuration."""
    errors = []

    # ... existing validation ...

    # NEW: Validate blocks
    if config.blocks:
        errors.extend(self._validate_blocks(config))

    return errors

def _validate_blocks(self, config: ParsedConfig) -> List[ValidationError]:
    """Validate block references."""
    errors = []

    for i, block in enumerate(config.blocks):
        path = f"blocks[{i}]"

        # Validate ref format
        try:
            block.parse_ref()
        except ValueError as e:
            errors.append(ValidationError(
                message=str(e),
                path=f"{path}.ref",
                severity="error"
            ))
            continue

        # Validate block exists in registry
        if not self._block_exists(block.registry, block.block_id, block.version):
            errors.append(ValidationError(
                message=f"Block not found: {block.ref}",
                path=f"{path}.ref",
                severity="error"
            ))
            continue

        # Get block metadata for further validation
        block_meta = self._get_block_metadata(block.block_id, block.version)

        # Validate required inputs are mapped
        for inp in block_meta.get("inputs", []):
            if inp.get("required", True) and inp["name"] not in block.inputs:
                errors.append(ValidationError(
                    message=f"Required input '{inp['name']}' not mapped",
                    path=f"{path}.inputs",
                    severity="error"
                ))

        # Validate extensions
        for j, ext in enumerate(block.extends):
            ext_errors = self._validate_extension(
                ext, block_meta, config, f"{path}.extends[{j}]"
            )
            errors.extend(ext_errors)

    return errors

def _validate_extension(
    self,
    ext: ExtensionConfig,
    block_meta: dict,
    config: ParsedConfig,
    path: str
) -> List[ValidationError]:
    """Validate a single extension."""
    errors = []

    # Check recipe exists in block
    block_recipes = block_meta.get("contains", {}).get("recipes", [])
    if ext.recipe not in block_recipes:
        errors.append(ValidationError(
            message=f"Recipe '{ext.recipe}' not found in block",
            path=path,
            severity="error"
        ))
        return errors

    # If override_with, check custom recipe exists in config
    if ext.override_with:
        recipe_names = [r.name for r in config.recipes]
        if ext.override_with not in recipe_names:
            errors.append(ValidationError(
                message=f"Override recipe '{ext.override_with}' not defined",
                path=f"{path}.override_with",
                severity="error"
            ))

    # If use_class, validate class path format
    if ext.use_class:
        if "." not in ext.use_class:
            errors.append(ValidationError(
                message=f"Invalid class path: {ext.use_class}",
                path=f"{path}.use_class",
                severity="error"
            ))

    return errors

def _block_exists(self, registry: str, block_id: str, version: str) -> bool:
    """Check if block exists in registry."""
    # Implementation uses CatalogReader
    try:
        from ..workflows.executing.catalog import CatalogReader
        reader = CatalogReader(self.client, registry)
        block = reader.get_block(block_id, version)
        return block is not None
    except Exception:
        return False

def _get_block_metadata(self, block_id: str, version: str) -> dict:
    """Get block metadata from registry."""
    from ..workflows.executing.catalog import CatalogReader
    reader = CatalogReader(self.client, "BLOCKS_REGISTRY")
    return reader.get_block(block_id, version) or {}
```

---

## State Extension

### Modification to state.py

```python
# Add to ResourceType enum
class ResourceType(Enum):
    PROJECT = "project"
    DATASET = "dataset"
    RECIPE = "recipe"
    BLOCK = "block"          # NEW
    SOLUTION = "solution"    # NEW (for solution blocks)

# Add BlockState model
@dataclass
class BlockState:
    """State of an instantiated block."""

    resource_id: str              # Unique ID for this instantiation
    block_ref: str                # Original reference
    block_id: str                 # Block ID
    version: str                  # Block version
    instance_name: str            # Local instance name
    zone_name: str                # Zone name in project

    inputs: Dict[str, str]        # port -> actual dataset
    outputs: Dict[str, str]       # port -> actual dataset

    extensions: List[dict]        # Applied extensions

    # Internal tracking
    created_datasets: List[str]   # Datasets created by block
    created_recipes: List[str]    # Recipes created by block

    status: str = "pending"       # pending | applied | failed
```

---

## Plan Engine Extension

### Modification to engine.py

```python
# In PlanEngine class

def generate_plan(
    self,
    config: ParsedConfig,
    current_state: State
) -> Plan:
    """Generate execution plan."""
    plan = Plan()

    # ... existing planning for projects, datasets, recipes ...

    # NEW: Plan block operations
    if config.blocks:
        block_operations = self._plan_block_operations(config, current_state)
        plan.operations.extend(block_operations)

    # Order operations by dependencies
    plan.operations = self._order_operations(plan.operations)

    return plan

def _plan_block_operations(
    self,
    config: ParsedConfig,
    current_state: State
) -> List[Operation]:
    """Plan operations for blocks."""
    operations = []

    for block_ref in config.blocks:
        # Check if block already instantiated
        existing = current_state.get_resource(
            ResourceType.BLOCK,
            block_ref.instance_name
        )

        if existing is None:
            # Create instantiation operation
            op = Operation(
                type=OperationType.CREATE,
                resource_type=ResourceType.BLOCK,
                resource_id=block_ref.instance_name,
                config=block_ref,
                description=f"Instantiate {block_ref.block_id}@{block_ref.version}"
            )
            operations.append(op)

        elif self._block_needs_update(existing, block_ref):
            # Update operation
            op = Operation(
                type=OperationType.UPDATE,
                resource_type=ResourceType.BLOCK,
                resource_id=block_ref.instance_name,
                config=block_ref,
                previous_config=existing,
                description=f"Update {block_ref.instance_name}"
            )
            operations.append(op)

    return operations

def _block_needs_update(
    self,
    existing: BlockState,
    new_config: BlockReferenceConfig
) -> bool:
    """Check if block needs update."""
    # Version change
    if existing.version != new_config.version:
        return True

    # Input mapping change
    if existing.inputs != new_config.inputs:
        return True

    # Output mapping change
    if existing.outputs != new_config.outputs:
        return True

    # Extension change
    if len(existing.extensions) != len(new_config.extends):
        return True

    return False
```

---

## Block Sync Implementation

### New file: sync/block.py

```python
"""Block synchronization for IaC."""

from typing import Dict, Any, Optional
from ..sync.base import ResourceSync
from ..models.state import ResourceType, BlockState
from ..models.block import BlockReferenceConfig
from .instantiator import BlockInstantiator


class BlockSync(ResourceSync):
    """
    Synchronizes block resources with Dataiku.

    Handles:
    - Block instantiation (creating zones, recipes)
    - Input/output wiring
    - Extensions (recipe overrides, class overrides)
    """

    resource_type = ResourceType.BLOCK

    def __init__(self, client, project):
        """
        Initialize BlockSync.

        Args:
            client: DSSClient
            project: Target DSSProject
        """
        super().__init__(client, project)
        self._instantiator = BlockInstantiator(client)

    def create(self, config: BlockReferenceConfig) -> BlockState:
        """
        Instantiate a block in the project.

        Args:
            config: Block reference configuration

        Returns:
            BlockState with instantiation details
        """
        # Resolve block metadata
        block_meta = self._resolve_block(config)

        # Create zone
        zone = self._create_zone(config.zone_name)

        # Instantiate block contents
        result = self._instantiator.instantiate(
            project=self.project,
            block_meta=block_meta,
            zone=zone,
            input_mapping=config.inputs,
            output_mapping=config.outputs,
            extensions=config.extends
        )

        return BlockState(
            resource_id=config.instance_name,
            block_ref=config.ref,
            block_id=config.block_id,
            version=config.version,
            instance_name=config.instance_name,
            zone_name=config.zone_name,
            inputs=config.inputs,
            outputs=config.outputs,
            extensions=[e.__dict__ for e in config.extends],
            created_datasets=result.created_datasets,
            created_recipes=result.created_recipes,
            status="applied"
        )

    def update(
        self,
        config: BlockReferenceConfig,
        existing: BlockState
    ) -> BlockState:
        """
        Update an existing block instantiation.

        For now, delete and recreate. Future: incremental updates.
        """
        self.delete(existing)
        return self.create(config)

    def delete(self, state: BlockState):
        """
        Remove a block instantiation.

        Deletes zone and all contained resources.
        """
        flow = self.project.get_flow()

        # Delete zone (cascades to contents)
        try:
            zone = flow.get_zone(state.zone_name)
            zone.delete()
        except Exception:
            pass  # Zone may already be deleted

    def _resolve_block(self, config: BlockReferenceConfig) -> dict:
        """Resolve block reference to metadata."""
        from ..workflows.executing.catalog import CatalogReader

        reader = CatalogReader(self.client, config.registry)
        return reader.get_block(config.block_id, config.version)

    def _create_zone(self, zone_name: str):
        """Create zone in project flow."""
        flow = self.project.get_flow()

        try:
            return flow.get_zone(zone_name)
        except Exception:
            return flow.create_zone(zone_name)
```

---

## Block Instantiator

### New file: workflows/blocks/instantiator.py

```python
"""Block instantiation logic."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from dataikuapi.dss.project import DSSProject


@dataclass
class InstantiationResult:
    """Result of block instantiation."""

    success: bool
    created_datasets: List[str] = field(default_factory=list)
    created_recipes: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class BlockInstantiator:
    """
    Instantiates blocks in target projects.

    Handles:
    - Copying recipes from source
    - Creating internal datasets
    - Wiring inputs/outputs
    - Applying extensions
    """

    def __init__(self, client):
        """
        Initialize instantiator.

        Args:
            client: DSSClient
        """
        self.client = client

    def instantiate(
        self,
        project: DSSProject,
        block_meta: dict,
        zone,
        input_mapping: Dict[str, str],
        output_mapping: Dict[str, str],
        extensions: List[Any]
    ) -> InstantiationResult:
        """
        Instantiate a block in the target project.

        Args:
            project: Target project
            block_meta: Block metadata from registry
            zone: Target zone
            input_mapping: Input port -> dataset name
            output_mapping: Output port -> dataset name
            extensions: Extension configurations

        Returns:
            InstantiationResult with created resources
        """
        result = InstantiationResult(success=False)

        try:
            # 1. Create internal datasets
            internal_datasets = self._create_internal_datasets(
                project, zone, block_meta
            )
            result.created_datasets.extend(internal_datasets)

            # 2. Copy/create recipes
            created_recipes = self._create_recipes(
                project, zone, block_meta, extensions
            )
            result.created_recipes.extend(created_recipes)

            # 3. Wire inputs
            self._wire_inputs(
                project, block_meta, input_mapping
            )

            # 4. Wire outputs
            self._wire_outputs(
                project, block_meta, output_mapping
            )

            # 5. Apply extensions
            self._apply_extensions(project, extensions)

            result.success = True

        except Exception as e:
            result.errors.append(str(e))

        return result

    def _create_internal_datasets(
        self,
        project: DSSProject,
        zone,
        block_meta: dict
    ) -> List[str]:
        """Create internal datasets for block."""
        created = []

        internal_datasets = block_meta.get("contains", {}).get("datasets", [])

        for ds_name in internal_datasets:
            # Create managed dataset
            try:
                builder = project.new_managed_dataset(ds_name)
                builder.with_store_into("filesystem_managed")
                dataset = builder.create()

                # Move to zone
                zone.add_item(dataset)

                created.append(ds_name)
            except Exception:
                # May already exist
                pass

        return created

    def _create_recipes(
        self,
        project: DSSProject,
        zone,
        block_meta: dict,
        extensions: List[Any]
    ) -> List[str]:
        """
        Create recipes for block.

        Copies from source or creates based on block definition.
        """
        created = []

        # Build override lookup
        override_lookup = {}
        for ext in extensions:
            if hasattr(ext, 'override_with') and ext.override_with:
                override_lookup[ext.recipe] = ext

        recipes = block_meta.get("contains", {}).get("recipes", [])

        for recipe_name in recipes:
            # Check for override
            if recipe_name in override_lookup:
                # Skip - user provides custom recipe
                continue

            # Copy recipe from source
            # This is simplified - real implementation would copy recipe definition
            try:
                source_project = self.client.get_project(block_meta["source_project"])
                source_recipe = source_project.get_recipe(recipe_name)
                source_settings = source_recipe.get_settings()

                # Create recipe in target
                # ... implementation depends on recipe type ...

                created.append(recipe_name)
            except Exception as e:
                # Log warning and continue
                pass

        return created

    def _wire_inputs(
        self,
        project: DSSProject,
        block_meta: dict,
        input_mapping: Dict[str, str]
    ):
        """Wire external inputs to block input datasets."""
        # For each block input, create connection to external dataset
        for inp in block_meta.get("inputs", []):
            port_name = inp["name"]
            if port_name in input_mapping:
                external_ds = input_mapping[port_name]
                # Create sync recipe or shared dataset reference
                # ... implementation ...

    def _wire_outputs(
        self,
        project: DSSProject,
        block_meta: dict,
        output_mapping: Dict[str, str]
    ):
        """Wire block outputs to external datasets."""
        for out in block_meta.get("outputs", []):
            port_name = out["name"]
            if port_name in output_mapping:
                external_ds = output_mapping[port_name]
                # Create sync or rename output
                # ... implementation ...

    def _apply_extensions(
        self,
        project: DSSProject,
        extensions: List[Any]
    ):
        """Apply class extensions to recipes."""
        for ext in extensions:
            if hasattr(ext, 'use_class') and ext.use_class:
                recipe = project.get_recipe(ext.recipe)
                settings = recipe.get_settings()

                # Inject class override code
                current_code = settings.get_code()
                override_code = self._generate_class_override(
                    ext.use_class,
                    ext.class_config
                )
                new_code = override_code + "\n\n" + current_code

                settings.set_code(new_code)
                settings.save()

    def _generate_class_override(
        self,
        class_path: str,
        class_config: dict
    ) -> str:
        """Generate Python code for class override."""
        module_path = ".".join(class_path.split(".")[:-1])
        class_name = class_path.split(".")[-1]

        return f'''
# AUTO-GENERATED: Class extension
from {module_path} import {class_name}
_override_class = {class_name}
_override_config = {repr(class_config)}
'''
```

---

## Manager Registration

### Modification to manager.py

```python
# In StateManager.__init__

def __init__(self, client, project_key):
    # ... existing init ...

    # Register sync handlers
    self._sync_handlers = {
        ResourceType.PROJECT: ProjectSync(client),
        ResourceType.DATASET: DatasetSync(client, self.project),
        ResourceType.RECIPE: RecipeSync(client, self.project),
        ResourceType.BLOCK: BlockSync(client, self.project),  # NEW
    }
```

---

## Error Handling

### Error Types

| Error | When | Handling |
|-------|------|----------|
| `BlockRefParseError` | Invalid ref format | Clear syntax error message |
| `BlockNotFoundError` | Block not in registry | List available blocks |
| `VersionNotFoundError` | Version not found | List available versions |
| `InputMappingError` | Required input not mapped | List required inputs |
| `ExtensionError` | Invalid extension config | Show valid options |
| `InstantiationError` | Failed to create zone/recipes | Rollback and report |

---

## Plan Output Format

### Block Operation Output

```
Block Operations:
  + instantiate FEATURE_ENG@1.2.0 as feature_instance
    zone: feature_zone
    inputs:
      RAW_DATA → source_sensors (dataset)
      METADATA → equipment_metadata (dataset)
    outputs:
      FEATURES → computed_features (dataset)
    extends:
      - recipe signal_smoothing → custom_smoothing (override)
      - recipe feature_compute: use MyFeatureClass (class)

  ~ update ANOMALY_DET instance
    version: 1.0.0 → 1.1.0

  - destroy OLD_BLOCK instance
    zone: old_zone will be deleted
```

---

## Dependency Ordering

Block operations must be ordered considering:

1. **Projects before blocks** - Project must exist
2. **External datasets before blocks** - Inputs must exist
3. **Blocks before dependent blocks** - For solution blocks
4. **Custom recipes before blocks** - Override recipes must exist

```python
def _order_operations(self, operations: List[Operation]) -> List[Operation]:
    """Order operations by dependencies."""

    # Group by type
    project_ops = [o for o in operations if o.resource_type == ResourceType.PROJECT]
    dataset_ops = [o for o in operations if o.resource_type == ResourceType.DATASET]
    recipe_ops = [o for o in operations if o.resource_type == ResourceType.RECIPE]
    block_ops = [o for o in operations if o.resource_type == ResourceType.BLOCK]

    # Order: project → datasets → recipes → blocks
    return project_ops + dataset_ops + recipe_ops + block_ops
```
