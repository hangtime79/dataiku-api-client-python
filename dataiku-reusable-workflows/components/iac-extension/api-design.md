# IaC Block Extension API Design

## Module Structure

```
dataikuapi/iac/
├── config/
│   ├── parser.py              # MODIFY: Add blocks parsing
│   └── validator.py           # MODIFY: Add block validation
├── models/
│   ├── state.py               # MODIFY: Add BLOCK resource type
│   └── block.py               # NEW: Block config models
├── planner/
│   └── engine.py              # MODIFY: Add block planning
├── sync/
│   └── block.py               # NEW: BlockSync implementation
└── workflows/
    └── blocks/
        ├── __init__.py
        ├── instantiator.py    # NEW: Block instantiation logic
        └── resolver.py        # NEW: Block reference resolution
```

---

## Data Models (models/block.py)

```python
"""Data models for IaC block support."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class ExtensionType(Enum):
    """Type of block extension."""
    RECIPE_OVERRIDE = "recipe_override"
    CLASS_OVERRIDE = "class_override"


@dataclass
class RecipeOverrideConfig:
    """
    Recipe override extension configuration.

    Replaces a recipe within a block with a custom implementation.
    The custom recipe must have compatible inputs/outputs.
    """

    recipe: str                       # Original recipe name in block
    override_with: str                # Custom recipe name defined in config

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recipe": self.recipe,
            "override_with": self.override_with,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecipeOverrideConfig":
        return cls(
            recipe=data["recipe"],
            override_with=data["override_with"],
        )


@dataclass
class ClassOverrideConfig:
    """
    Class override extension configuration.

    Injects a custom class into a recipe that uses base class inheritance.
    The class is imported and instantiated with the provided config.
    """

    recipe: str                       # Recipe to modify
    use_class: str                    # Fully qualified class name (module.ClassName)
    class_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recipe": self.recipe,
            "use_class": self.use_class,
            "class_config": self.class_config,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClassOverrideConfig":
        return cls(
            recipe=data["recipe"],
            use_class=data["use_class"],
            class_config=data.get("class_config", {}),
        )


@dataclass
class ExtensionConfig:
    """
    Generic extension configuration.

    Can represent either a recipe override or class override.
    Exactly one of override_with or use_class must be specified.
    """

    recipe: str                             # Target recipe name
    override_with: Optional[str] = None     # For recipe override
    use_class: Optional[str] = None         # For class override
    class_config: Dict[str, Any] = field(default_factory=dict)

    @property
    def extension_type(self) -> ExtensionType:
        """Get the type of extension."""
        if self.override_with:
            return ExtensionType.RECIPE_OVERRIDE
        return ExtensionType.CLASS_OVERRIDE

    def to_dict(self) -> Dict[str, Any]:
        result = {"recipe": self.recipe}
        if self.override_with:
            result["override_with"] = self.override_with
        if self.use_class:
            result["use_class"] = self.use_class
            if self.class_config:
                result["class_config"] = self.class_config
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtensionConfig":
        return cls(
            recipe=data["recipe"],
            override_with=data.get("override_with"),
            use_class=data.get("use_class"),
            class_config=data.get("class_config", {}),
        )

    def validate(self) -> List[str]:
        """Validate extension configuration. Returns list of errors."""
        errors = []

        if not self.recipe:
            errors.append("Extension must specify target recipe")

        if self.override_with and self.use_class:
            errors.append("Extension cannot have both override_with and use_class")

        if not self.override_with and not self.use_class:
            errors.append("Extension must specify override_with or use_class")

        if self.use_class and "." not in self.use_class:
            errors.append(f"Invalid class path '{self.use_class}' - must be fully qualified (module.ClassName)")

        return errors


@dataclass
class BlockReferenceConfig:
    """
    Block reference configuration in IaC.

    References a block from BLOCKS_REGISTRY and specifies how to
    instantiate it in the target project.
    """

    ref: str                                  # "REGISTRY/BLOCK_ID@VERSION"
    instance_name: str                        # Local instance name
    zone_name: str                            # Target zone name

    inputs: Dict[str, str] = field(default_factory=dict)    # port_name -> dataset_name
    outputs: Dict[str, str] = field(default_factory=dict)   # port_name -> dataset_name

    extends: List[ExtensionConfig] = field(default_factory=list)

    # Parsed from ref (populated by parse_ref)
    registry: str = ""
    block_id: str = ""
    version: str = ""

    def parse_ref(self) -> None:
        """
        Parse ref string into components.

        Format: "REGISTRY/BLOCK_ID@VERSION"
        Examples:
          - "BLOCKS_REGISTRY/FEATURE_ENG@1.2.0"
          - "BLOCKS_REGISTRY/ANOMALY_DET@latest"
          - "BLOCKS_REGISTRY/MY_BLOCK" (implies @latest)

        Raises:
            ValueError: If ref format is invalid
        """
        if "/" not in self.ref:
            raise ValueError(
                f"Invalid block ref format: '{self.ref}'. "
                f"Expected 'REGISTRY/BLOCK_ID@VERSION'"
            )

        parts = self.ref.split("/", 1)
        self.registry = parts[0]
        block_version = parts[1]

        if "@" in block_version:
            self.block_id, self.version = block_version.split("@", 1)
        else:
            self.block_id = block_version
            self.version = "latest"

        # Validate components
        if not self.registry:
            raise ValueError(f"Missing registry in ref: '{self.ref}'")
        if not self.block_id:
            raise ValueError(f"Missing block_id in ref: '{self.ref}'")

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "ref": self.ref,
            "instance_name": self.instance_name,
            "zone_name": self.zone_name,
            "inputs": self.inputs,
            "outputs": self.outputs,
        }
        if self.extends:
            result["extends"] = [e.to_dict() for e in self.extends]
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlockReferenceConfig":
        extends = [
            ExtensionConfig.from_dict(e)
            for e in data.get("extends", [])
        ]

        config = cls(
            ref=data["ref"],
            instance_name=data.get("instance_name", ""),
            zone_name=data.get("zone_name", ""),
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", {}),
            extends=extends,
        )
        config.parse_ref()
        return config

    def validate(self) -> List[str]:
        """Validate block reference configuration. Returns list of errors."""
        errors = []

        if not self.ref:
            errors.append("Block reference must have 'ref' field")
        else:
            try:
                self.parse_ref()
            except ValueError as e:
                errors.append(str(e))

        if not self.instance_name:
            errors.append("Block reference must have 'instance_name'")

        if not self.zone_name:
            errors.append("Block reference must have 'zone_name'")

        # Validate extensions
        for i, ext in enumerate(self.extends):
            ext_errors = ext.validate()
            for err in ext_errors:
                errors.append(f"extends[{i}]: {err}")

        return errors


@dataclass
class SolutionBlockConfig:
    """
    Solution block configuration for multi-model orchestration.

    A solution block composes multiple regular blocks with defined
    sequencing and data flow.
    """

    ref: str                                  # Solution block reference
    instance_name: str
    zone_prefix: str                          # Prefix for generated zones

    inputs: Dict[str, str] = field(default_factory=dict)
    outputs: Dict[str, str] = field(default_factory=dict)

    # Override configs for contained blocks
    block_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Parsed components
    registry: str = ""
    block_id: str = ""
    version: str = ""

    def parse_ref(self) -> None:
        """Parse solution reference."""
        # Same parsing as BlockReferenceConfig
        if "/" not in self.ref:
            raise ValueError(f"Invalid solution ref format: '{self.ref}'")

        parts = self.ref.split("/", 1)
        self.registry = parts[0]
        block_version = parts[1]

        if "@" in block_version:
            self.block_id, self.version = block_version.split("@", 1)
        else:
            self.block_id = block_version
            self.version = "latest"


@dataclass
class BlockState:
    """
    State of an instantiated block in a project.

    Tracks what was created and the mappings applied.
    """

    resource_id: str                          # Unique ID for this instantiation
    block_ref: str                            # Original reference string
    block_id: str                             # Block ID
    version: str                              # Block version
    instance_name: str                        # Local instance name
    zone_name: str                            # Zone name in project

    inputs: Dict[str, str] = field(default_factory=dict)    # port -> actual dataset
    outputs: Dict[str, str] = field(default_factory=dict)   # port -> actual dataset

    extensions: List[Dict[str, Any]] = field(default_factory=list)

    # Internal tracking
    created_datasets: List[str] = field(default_factory=list)
    created_recipes: List[str] = field(default_factory=list)

    status: str = "pending"                   # pending | applied | failed
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "block_ref": self.block_ref,
            "block_id": self.block_id,
            "version": self.version,
            "instance_name": self.instance_name,
            "zone_name": self.zone_name,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "extensions": self.extensions,
            "created_datasets": self.created_datasets,
            "created_recipes": self.created_recipes,
            "status": self.status,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlockState":
        return cls(
            resource_id=data["resource_id"],
            block_ref=data["block_ref"],
            block_id=data["block_id"],
            version=data["version"],
            instance_name=data["instance_name"],
            zone_name=data["zone_name"],
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", {}),
            extensions=data.get("extensions", []),
            created_datasets=data.get("created_datasets", []),
            created_recipes=data.get("created_recipes", []),
            status=data.get("status", "pending"),
            error_message=data.get("error_message"),
        )


@dataclass
class BlockOperation:
    """
    Operation on a block resource in a plan.
    """

    operation_type: str                       # create | update | delete
    block_ref: str                            # Block reference
    instance_name: str
    zone_name: str

    inputs: Dict[str, str] = field(default_factory=dict)
    outputs: Dict[str, str] = field(default_factory=dict)
    extensions: List[ExtensionConfig] = field(default_factory=list)

    # For updates
    previous_version: Optional[str] = None
    changes: List[str] = field(default_factory=list)

    def to_display_string(self) -> str:
        """Format operation for display."""
        op_symbol = {"create": "+", "update": "~", "delete": "-"}.get(
            self.operation_type, "?"
        )

        lines = [f"  {op_symbol} {self.operation_type} {self.block_ref} as {self.instance_name}"]
        lines.append(f"    zone: {self.zone_name}")

        if self.inputs:
            lines.append("    inputs:")
            for port, ds in self.inputs.items():
                lines.append(f"      {port} → {ds}")

        if self.outputs:
            lines.append("    outputs:")
            for port, ds in self.outputs.items():
                lines.append(f"      {port} → {ds}")

        if self.extensions:
            lines.append("    extends:")
            for ext in self.extensions:
                if ext.override_with:
                    lines.append(f"      - recipe {ext.recipe} → {ext.override_with} (override)")
                elif ext.use_class:
                    lines.append(f"      - recipe {ext.recipe}: use {ext.use_class} (class)")

        if self.changes:
            lines.append("    changes:")
            for change in self.changes:
                lines.append(f"      - {change}")

        return "\n".join(lines)
```

---

## Parser Extension (config/parser.py modifications)

```python
"""Modifications to ConfigParser for block support."""

from typing import List, Dict, Any
from ..models.block import BlockReferenceConfig, SolutionBlockConfig, ExtensionConfig


class ConfigParserBlockExtension:
    """
    Block-related parsing methods to add to ConfigParser.

    Add these methods to the existing ConfigParser class.
    """

    def _parse_blocks(self, blocks_list: List[Dict]) -> List[BlockReferenceConfig]:
        """
        Parse blocks section of configuration.

        Args:
            blocks_list: List of block configuration dicts

        Returns:
            List of parsed BlockReferenceConfig objects
        """
        blocks = []

        for block_dict in blocks_list:
            block = self._parse_single_block(block_dict)
            blocks.append(block)

        return blocks

    def _parse_single_block(self, block_dict: Dict) -> BlockReferenceConfig:
        """
        Parse a single block reference.

        Args:
            block_dict: Block configuration dict

        Returns:
            BlockReferenceConfig

        Raises:
            ValueError: If required fields missing or invalid
        """
        # Required fields
        if "ref" not in block_dict:
            raise ValueError("Block must have 'ref' field")

        # Parse extensions
        extends = []
        if "extends" in block_dict:
            extends = self._parse_extensions(block_dict["extends"])

        # Create config
        config = BlockReferenceConfig(
            ref=block_dict["ref"],
            instance_name=block_dict.get("instance_name", self._generate_instance_name(block_dict["ref"])),
            zone_name=block_dict.get("zone_name", self._generate_zone_name(block_dict["ref"])),
            inputs=block_dict.get("inputs", {}),
            outputs=block_dict.get("outputs", {}),
            extends=extends,
        )

        # Parse reference into components
        config.parse_ref()

        return config

    def _parse_extensions(self, extends_list: List[Dict]) -> List[ExtensionConfig]:
        """
        Parse extension configurations.

        Args:
            extends_list: List of extension config dicts

        Returns:
            List of ExtensionConfig objects
        """
        extensions = []

        for ext_dict in extends_list:
            if "recipe" not in ext_dict:
                raise ValueError("Extension must have 'recipe' field")

            ext = ExtensionConfig(
                recipe=ext_dict["recipe"],
                override_with=ext_dict.get("override_with"),
                use_class=ext_dict.get("use_class"),
                class_config=ext_dict.get("class_config", {}),
            )

            # Validate extension
            errors = ext.validate()
            if errors:
                raise ValueError(f"Invalid extension: {'; '.join(errors)}")

            extensions.append(ext)

        return extensions

    def _parse_solutions(self, solutions_list: List[Dict]) -> List[SolutionBlockConfig]:
        """
        Parse solutions section of configuration.

        Args:
            solutions_list: List of solution configuration dicts

        Returns:
            List of SolutionBlockConfig objects
        """
        solutions = []

        for sol_dict in solutions_list:
            config = SolutionBlockConfig(
                ref=sol_dict["ref"],
                instance_name=sol_dict.get("instance_name", ""),
                zone_prefix=sol_dict.get("zone_prefix", ""),
                inputs=sol_dict.get("inputs", {}),
                outputs=sol_dict.get("outputs", {}),
                block_overrides=sol_dict.get("block_overrides", {}),
            )
            config.parse_ref()
            solutions.append(config)

        return solutions

    def _generate_instance_name(self, ref: str) -> str:
        """Generate default instance name from ref."""
        # Extract block_id from ref
        if "/" in ref:
            block_part = ref.split("/")[1]
            if "@" in block_part:
                block_id = block_part.split("@")[0]
            else:
                block_id = block_part
            return f"{block_id.lower()}_instance"
        return "block_instance"

    def _generate_zone_name(self, ref: str) -> str:
        """Generate default zone name from ref."""
        if "/" in ref:
            block_part = ref.split("/")[1]
            if "@" in block_part:
                block_id = block_part.split("@")[0]
            else:
                block_id = block_part
            return f"{block_id.lower()}_zone"
        return "block_zone"


# Integration example showing how to modify existing parse() method:
"""
class ConfigParser:
    # ... existing code ...

    def parse(self, config_dict: dict) -> ParsedConfig:
        parsed = ParsedConfig()

        # Existing parsing...
        if "project" in config_dict:
            parsed.project = self._parse_project(config_dict["project"])
        if "datasets" in config_dict:
            parsed.datasets = self._parse_datasets(config_dict["datasets"])
        if "recipes" in config_dict:
            parsed.recipes = self._parse_recipes(config_dict["recipes"])

        # NEW: Parse blocks
        if "blocks" in config_dict:
            parsed.blocks = self._parse_blocks(config_dict["blocks"])

        # NEW: Parse solutions
        if "solutions" in config_dict:
            parsed.solutions = self._parse_solutions(config_dict["solutions"])

        return parsed
"""
```

---

## Validator Extension (config/validator.py modifications)

```python
"""Modifications to ConfigValidator for block support."""

from typing import List, Dict, Any, Optional
from ..models.block import BlockReferenceConfig, ExtensionConfig


class ValidationError:
    """Validation error with path and severity."""

    def __init__(self, message: str, path: str, severity: str = "error"):
        self.message = message
        self.path = path
        self.severity = severity

    def __str__(self):
        return f"[{self.severity}] {self.path}: {self.message}"


class ConfigValidatorBlockExtension:
    """
    Block-related validation methods to add to ConfigValidator.

    Add these methods to the existing ConfigValidator class.
    """

    def _validate_blocks(self, config) -> List[ValidationError]:
        """
        Validate all block references in configuration.

        Args:
            config: ParsedConfig object

        Returns:
            List of ValidationError objects
        """
        errors = []

        for i, block in enumerate(config.blocks):
            path = f"blocks[{i}]"
            block_errors = self._validate_single_block(block, config, path)
            errors.extend(block_errors)

        # Validate no duplicate instance names
        instance_names = [b.instance_name for b in config.blocks]
        duplicates = [name for name in instance_names if instance_names.count(name) > 1]
        if duplicates:
            errors.append(ValidationError(
                message=f"Duplicate block instance names: {set(duplicates)}",
                path="blocks",
                severity="error"
            ))

        return errors

    def _validate_single_block(
        self,
        block: BlockReferenceConfig,
        config,
        path: str
    ) -> List[ValidationError]:
        """
        Validate a single block reference.

        Checks:
        - Ref format is valid
        - Block exists in registry
        - Version exists
        - Required inputs are mapped
        - Input types are compatible
        - Extensions are valid
        """
        errors = []

        # Validate ref format
        try:
            block.parse_ref()
        except ValueError as e:
            errors.append(ValidationError(
                message=str(e),
                path=f"{path}.ref",
                severity="error"
            ))
            return errors  # Can't continue without valid ref

        # Validate block exists in registry
        block_exists, version_exists = self._check_block_exists(
            block.registry, block.block_id, block.version
        )

        if not block_exists:
            errors.append(ValidationError(
                message=f"Block '{block.block_id}' not found in registry '{block.registry}'",
                path=f"{path}.ref",
                severity="error"
            ))
            return errors

        if not version_exists:
            available = self._get_available_versions(block.registry, block.block_id)
            errors.append(ValidationError(
                message=f"Version '{block.version}' not found. Available: {available}",
                path=f"{path}.ref",
                severity="error"
            ))
            return errors

        # Get block metadata for further validation
        block_meta = self._get_block_metadata(block.registry, block.block_id, block.version)

        if block_meta:
            # Validate required inputs are mapped
            input_errors = self._validate_input_mappings(block, block_meta, config, path)
            errors.extend(input_errors)

            # Validate extensions
            ext_errors = self._validate_extensions(block, block_meta, config, path)
            errors.extend(ext_errors)

        return errors

    def _validate_input_mappings(
        self,
        block: BlockReferenceConfig,
        block_meta: dict,
        config,
        path: str
    ) -> List[ValidationError]:
        """Validate block input mappings."""
        errors = []

        for inp in block_meta.get("inputs", []):
            port_name = inp["name"]
            is_required = inp.get("required", True)

            if is_required and port_name not in block.inputs:
                errors.append(ValidationError(
                    message=f"Required input '{port_name}' is not mapped",
                    path=f"{path}.inputs",
                    severity="error"
                ))

            # Check mapped dataset exists
            if port_name in block.inputs:
                dataset_name = block.inputs[port_name]
                if not self._dataset_exists_in_config(dataset_name, config):
                    # Could be external, just warn
                    errors.append(ValidationError(
                        message=f"Input '{port_name}' mapped to '{dataset_name}' which is not defined in config",
                        path=f"{path}.inputs.{port_name}",
                        severity="warning"
                    ))

        return errors

    def _validate_extensions(
        self,
        block: BlockReferenceConfig,
        block_meta: dict,
        config,
        path: str
    ) -> List[ValidationError]:
        """Validate block extensions."""
        errors = []

        block_recipes = block_meta.get("contains", {}).get("recipes", [])

        for i, ext in enumerate(block.extends):
            ext_path = f"{path}.extends[{i}]"

            # Validate recipe exists in block
            if ext.recipe not in block_recipes:
                errors.append(ValidationError(
                    message=f"Recipe '{ext.recipe}' not found in block. Available: {block_recipes}",
                    path=ext_path,
                    severity="error"
                ))
                continue

            # Validate override_with recipe exists
            if ext.override_with:
                recipe_names = [r.name for r in getattr(config, 'recipes', [])]
                if ext.override_with not in recipe_names:
                    errors.append(ValidationError(
                        message=f"Override recipe '{ext.override_with}' not defined in config",
                        path=f"{ext_path}.override_with",
                        severity="error"
                    ))

            # Validate use_class format
            if ext.use_class and "." not in ext.use_class:
                errors.append(ValidationError(
                    message=f"Invalid class path '{ext.use_class}' - must be fully qualified",
                    path=f"{ext_path}.use_class",
                    severity="error"
                ))

        return errors

    def _check_block_exists(
        self,
        registry: str,
        block_id: str,
        version: str
    ) -> tuple:
        """
        Check if block and version exist.

        Returns:
            (block_exists, version_exists) tuple
        """
        try:
            from ..workflows.executing.catalog import CatalogReader
            reader = CatalogReader(self.client, registry)
            catalog = reader.load_catalog()

            # Check block exists
            block_summary = catalog.get_block(block_id)
            if not block_summary:
                return False, False

            # Check version exists
            if version == "latest":
                return True, True

            version_summary = catalog.get_block(block_id, version)
            return True, version_summary is not None

        except Exception:
            return False, False

    def _get_block_metadata(
        self,
        registry: str,
        block_id: str,
        version: str
    ) -> Optional[dict]:
        """Get full block metadata from registry."""
        try:
            from ..workflows.executing.catalog import CatalogReader
            reader = CatalogReader(self.client, registry)
            return reader.get_block(block_id, version if version != "latest" else None)
        except Exception:
            return None

    def _get_available_versions(self, registry: str, block_id: str) -> List[str]:
        """Get available versions for a block."""
        try:
            from ..workflows.executing.catalog import CatalogReader
            reader = CatalogReader(self.client, registry)
            catalog = reader.load_catalog()

            versions = []
            for key, block in catalog.blocks.items():
                if block.block_id == block_id:
                    versions.append(block.version)
            return versions
        except Exception:
            return []

    def _dataset_exists_in_config(self, name: str, config) -> bool:
        """Check if dataset is defined in config."""
        dataset_names = [d.name for d in getattr(config, 'datasets', [])]
        return name in dataset_names
```

---

## Block Sync Implementation (sync/block.py)

```python
"""Block synchronization for IaC."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from ..sync.base import ResourceSync
from ..models.state import ResourceType
from ..models.block import (
    BlockReferenceConfig,
    BlockState,
    ExtensionConfig,
)


@dataclass
class InstantiationResult:
    """Result of block instantiation."""

    success: bool = False
    created_datasets: List[str] = field(default_factory=list)
    created_recipes: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class BlockSync(ResourceSync):
    """
    Synchronizes block resources with Dataiku.

    Handles:
    - Block instantiation (creating zones, recipes, datasets)
    - Input/output wiring
    - Extensions (recipe overrides, class overrides)
    - Block updates and deletion
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
        self._instantiator = None  # Lazy init

    @property
    def instantiator(self):
        """Get or create BlockInstantiator."""
        if self._instantiator is None:
            from ..workflows.blocks.instantiator import BlockInstantiator
            self._instantiator = BlockInstantiator(self.client)
        return self._instantiator

    def create(self, config: BlockReferenceConfig) -> BlockState:
        """
        Instantiate a block in the project.

        Steps:
        1. Resolve block metadata from registry
        2. Create zone in project
        3. Instantiate block contents (datasets, recipes)
        4. Wire inputs and outputs
        5. Apply extensions

        Args:
            config: Block reference configuration

        Returns:
            BlockState with instantiation details

        Raises:
            BlockInstantiationError: If instantiation fails
        """
        # Resolve block metadata
        block_meta = self._resolve_block(config)

        if not block_meta:
            raise BlockInstantiationError(
                f"Block not found: {config.ref}"
            )

        # Create zone
        zone = self._create_zone(config.zone_name)

        # Instantiate block contents
        result = self.instantiator.instantiate(
            project=self.project,
            block_meta=block_meta,
            zone=zone,
            input_mapping=config.inputs,
            output_mapping=config.outputs,
            extensions=config.extends,
        )

        if not result.success:
            raise BlockInstantiationError(
                f"Failed to instantiate {config.ref}: {result.errors}"
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
            extensions=[e.to_dict() for e in config.extends],
            created_datasets=result.created_datasets,
            created_recipes=result.created_recipes,
            status="applied",
        )

    def update(
        self,
        config: BlockReferenceConfig,
        existing: BlockState
    ) -> BlockState:
        """
        Update an existing block instantiation.

        Currently implements update as delete + recreate.
        Future enhancement: incremental updates for efficiency.

        Args:
            config: New block configuration
            existing: Existing block state

        Returns:
            Updated BlockState
        """
        # For now, delete and recreate
        # TODO: Implement incremental updates
        self.delete(existing)
        return self.create(config)

    def delete(self, state: BlockState) -> None:
        """
        Remove a block instantiation.

        Deletes the zone and all contained resources.

        Args:
            state: Block state to delete
        """
        flow = self.project.get_flow()

        # Delete zone (cascades to contents)
        try:
            zone = flow.get_zone(state.zone_name)
            zone.delete()
        except Exception:
            # Zone may already be deleted
            pass

        # Clean up any orphaned resources
        for ds_name in state.created_datasets:
            try:
                ds = self.project.get_dataset(ds_name)
                ds.delete()
            except Exception:
                pass

        for recipe_name in state.created_recipes:
            try:
                recipe = self.project.get_recipe(recipe_name)
                recipe.delete()
            except Exception:
                pass

    def _resolve_block(self, config: BlockReferenceConfig) -> Optional[dict]:
        """
        Resolve block reference to metadata.

        Args:
            config: Block reference configuration

        Returns:
            Block metadata dict or None
        """
        from ..workflows.executing.catalog import CatalogReader

        reader = CatalogReader(self.client, config.registry)
        version = config.version if config.version != "latest" else None
        return reader.get_block(config.block_id, version)

    def _create_zone(self, zone_name: str):
        """
        Create zone in project flow.

        Returns existing zone if already exists.

        Args:
            zone_name: Name for the zone

        Returns:
            Zone object
        """
        flow = self.project.get_flow()

        try:
            # Check if zone exists
            return flow.get_zone(zone_name)
        except Exception:
            # Create new zone
            return flow.create_zone(zone_name)

    def diff(
        self,
        config: BlockReferenceConfig,
        existing: Optional[BlockState]
    ) -> Dict[str, Any]:
        """
        Calculate differences between config and existing state.

        Args:
            config: Desired block configuration
            existing: Existing block state (or None)

        Returns:
            Dict describing the differences
        """
        if existing is None:
            return {"action": "create"}

        changes = []

        # Version change
        if existing.version != config.version:
            changes.append(f"version: {existing.version} → {config.version}")

        # Input mapping changes
        for port, ds in config.inputs.items():
            if existing.inputs.get(port) != ds:
                changes.append(f"input {port}: {existing.inputs.get(port)} → {ds}")

        # Output mapping changes
        for port, ds in config.outputs.items():
            if existing.outputs.get(port) != ds:
                changes.append(f"output {port}: {existing.outputs.get(port)} → {ds}")

        # Extension changes
        if len(existing.extensions) != len(config.extends):
            changes.append(f"extensions count: {len(existing.extensions)} → {len(config.extends)}")

        if changes:
            return {"action": "update", "changes": changes}

        return {"action": "none"}


class BlockInstantiationError(Exception):
    """Raised when block instantiation fails."""
    pass
```

---

## Block Instantiator (workflows/blocks/instantiator.py)

```python
"""Block instantiation logic."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json


@dataclass
class InstantiationResult:
    """Result of block instantiation."""

    success: bool = False
    created_datasets: List[str] = field(default_factory=list)
    created_recipes: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class BlockInstantiator:
    """
    Instantiates blocks in target projects.

    Handles:
    - Creating internal datasets
    - Copying recipes from source project
    - Applying recipe overrides
    - Applying class extensions
    - Wiring inputs and outputs
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
        project,
        block_meta: dict,
        zone,
        input_mapping: Dict[str, str],
        output_mapping: Dict[str, str],
        extensions: List[Any],
    ) -> InstantiationResult:
        """
        Instantiate a block in the target project.

        Args:
            project: Target DSSProject
            block_meta: Block metadata from registry
            zone: Target zone in project
            input_mapping: Input port name -> dataset name
            output_mapping: Output port name -> dataset name
            extensions: List of ExtensionConfig

        Returns:
            InstantiationResult with created resources
        """
        result = InstantiationResult()

        try:
            # Build override lookup
            override_lookup = self._build_override_lookup(extensions)

            # 1. Create internal datasets
            internal_ds = self._create_internal_datasets(
                project, zone, block_meta, output_mapping
            )
            result.created_datasets.extend(internal_ds)

            # 2. Create/copy recipes
            created_recipes = self._create_recipes(
                project, zone, block_meta, override_lookup
            )
            result.created_recipes.extend(created_recipes)

            # 3. Wire inputs (update recipe input references)
            self._wire_inputs(project, block_meta, input_mapping, created_recipes)

            # 4. Wire outputs
            self._wire_outputs(project, block_meta, output_mapping, created_recipes)

            # 5. Apply class extensions
            self._apply_class_extensions(project, extensions)

            result.success = True

        except Exception as e:
            result.errors.append(str(e))
            result.success = False

        return result

    def _build_override_lookup(
        self,
        extensions: List[Any]
    ) -> Dict[str, Any]:
        """Build lookup of recipe overrides."""
        lookup = {}
        for ext in extensions:
            if hasattr(ext, 'override_with') and ext.override_with:
                lookup[ext.recipe] = ext
        return lookup

    def _create_internal_datasets(
        self,
        project,
        zone,
        block_meta: dict,
        output_mapping: Dict[str, str],
    ) -> List[str]:
        """
        Create internal datasets for block.

        Internal datasets are those in the block that are not
        exposed as inputs or outputs.
        """
        created = []

        internal_datasets = block_meta.get("contains", {}).get("datasets", [])
        input_names = [inp["name"] for inp in block_meta.get("inputs", [])]
        output_names = [out["name"] for out in block_meta.get("outputs", [])]

        for ds_name in internal_datasets:
            # Skip if it's an input or output (handled by wiring)
            if ds_name in input_names or ds_name in output_names:
                continue

            # Skip if already mapped to output
            if ds_name in output_mapping:
                continue

            try:
                # Create managed dataset
                builder = project.new_managed_dataset(ds_name)
                builder.with_store_into("filesystem_managed")
                dataset = builder.create()

                # Move to zone
                zone.add_item(dataset)

                created.append(ds_name)
            except Exception as e:
                # May already exist
                if "already exists" not in str(e).lower():
                    raise

        return created

    def _create_recipes(
        self,
        project,
        zone,
        block_meta: dict,
        override_lookup: Dict[str, Any],
    ) -> List[str]:
        """
        Create recipes for block.

        Either copies from source project or skips if overridden.
        """
        created = []

        source_project_key = block_meta.get("source_project")
        if not source_project_key:
            return created

        source_project = self.client.get_project(source_project_key)
        recipes = block_meta.get("contains", {}).get("recipes", [])

        for recipe_name in recipes:
            # Skip if user provides override
            if recipe_name in override_lookup:
                continue

            try:
                # Copy recipe from source
                self._copy_recipe(source_project, project, recipe_name, zone)
                created.append(recipe_name)
            except Exception as e:
                # Log warning but continue
                pass

        return created

    def _copy_recipe(
        self,
        source_project,
        target_project,
        recipe_name: str,
        zone,
    ):
        """
        Copy a recipe from source to target project.

        This is a simplified implementation. A full implementation
        would handle different recipe types appropriately.
        """
        source_recipe = source_project.get_recipe(recipe_name)
        source_settings = source_recipe.get_settings()
        raw = source_settings.get_raw()

        recipe_type = raw.get("type", "")

        # Create recipe based on type
        if recipe_type == "python":
            self._create_python_recipe(target_project, recipe_name, raw, zone)
        elif recipe_type == "sql_query":
            self._create_sql_recipe(target_project, recipe_name, raw, zone)
        elif recipe_type == "sync":
            self._create_sync_recipe(target_project, recipe_name, raw, zone)
        elif recipe_type == "prepare":
            self._create_prepare_recipe(target_project, recipe_name, raw, zone)
        else:
            # Generic handling for other types
            self._create_generic_recipe(target_project, recipe_name, raw, zone)

    def _create_python_recipe(
        self,
        project,
        recipe_name: str,
        raw: dict,
        zone,
    ):
        """Create Python recipe."""
        inputs = list(raw.get("inputs", {}).keys())
        outputs = list(raw.get("outputs", {}).keys())

        builder = project.new_recipe("python", recipe_name)

        # Add inputs/outputs
        for inp in inputs:
            items = raw["inputs"][inp].get("items", [])
            for item in items:
                builder.with_input(item.get("ref", ""), role=inp)

        for out in outputs:
            items = raw["outputs"][out].get("items", [])
            for item in items:
                builder.with_output(item.get("ref", ""), role=out)

        recipe = builder.create()

        # Set code
        code = raw.get("payload", {}).get("code", "")
        if code:
            settings = recipe.get_settings()
            settings.set_code(code)
            settings.save()

        # Move to zone
        zone.add_item(recipe)

    def _create_sql_recipe(self, project, recipe_name, raw, zone):
        """Create SQL recipe."""
        # Simplified - implement based on your needs
        pass

    def _create_sync_recipe(self, project, recipe_name, raw, zone):
        """Create sync recipe."""
        pass

    def _create_prepare_recipe(self, project, recipe_name, raw, zone):
        """Create prepare recipe."""
        pass

    def _create_generic_recipe(self, project, recipe_name, raw, zone):
        """Create generic recipe - placeholder."""
        pass

    def _wire_inputs(
        self,
        project,
        block_meta: dict,
        input_mapping: Dict[str, str],
        created_recipes: List[str],
    ):
        """
        Wire external inputs to block recipes.

        Updates recipe input references to point to mapped datasets.
        """
        # For each input port, find recipes that use it and update
        for inp in block_meta.get("inputs", []):
            port_name = inp["name"]
            if port_name not in input_mapping:
                continue

            external_ds = input_mapping[port_name]

            # Update recipes that reference this input
            # This requires understanding the recipe structure
            # Simplified: recipes with input matching port_name
            pass

    def _wire_outputs(
        self,
        project,
        block_meta: dict,
        output_mapping: Dict[str, str],
        created_recipes: List[str],
    ):
        """
        Wire block outputs to external datasets.

        Either renames output datasets or creates sync recipes.
        """
        for out in block_meta.get("outputs", []):
            port_name = out["name"]
            if port_name not in output_mapping:
                continue

            external_ds = output_mapping[port_name]

            # Option 1: Rename internal output to external name
            # Option 2: Create sync recipe from internal to external
            # Implementation depends on requirements
            pass

    def _apply_class_extensions(
        self,
        project,
        extensions: List[Any],
    ):
        """
        Apply class override extensions to recipes.

        Injects import and class instantiation code.
        """
        for ext in extensions:
            if not hasattr(ext, 'use_class') or not ext.use_class:
                continue

            try:
                recipe = project.get_recipe(ext.recipe)
                settings = recipe.get_settings()

                # Get current code
                current_code = settings.get_code() or ""

                # Generate and prepend class override code
                override_code = self._generate_class_override_code(
                    ext.use_class,
                    getattr(ext, 'class_config', {})
                )

                new_code = override_code + "\n\n" + current_code
                settings.set_code(new_code)
                settings.save()

            except Exception:
                pass  # Log warning

    def _generate_class_override_code(
        self,
        class_path: str,
        class_config: dict,
    ) -> str:
        """Generate Python code for class override injection."""
        parts = class_path.rsplit(".", 1)
        if len(parts) != 2:
            return ""

        module_path, class_name = parts

        return f'''# AUTO-GENERATED: Class extension override
from {module_path} import {class_name}

# Override class and configuration
_block_override_class = {class_name}
_block_override_config = {json.dumps(class_config)}

# Instantiate if needed
def _get_override_instance():
    return _block_override_class(**_block_override_config)
'''
```

---

## Plan Engine Extension (planner/engine.py modifications)

```python
"""Modifications to PlanEngine for block support."""

from typing import List, Optional
from ..models.block import BlockReferenceConfig, BlockState, BlockOperation
from ..models.state import ResourceType


class PlanEngineBlockExtension:
    """
    Block-related planning methods to add to PlanEngine.

    Add these methods to the existing PlanEngine class.
    """

    def _plan_block_operations(
        self,
        config,
        current_state,
    ) -> List[BlockOperation]:
        """
        Plan operations for blocks section.

        Args:
            config: ParsedConfig with blocks
            current_state: Current state from State Manager

        Returns:
            List of BlockOperation
        """
        operations = []

        for block_ref in config.blocks:
            # Check if block already instantiated
            existing = current_state.get_resource(
                ResourceType.BLOCK,
                block_ref.instance_name
            )

            if existing is None:
                # Create operation
                op = BlockOperation(
                    operation_type="create",
                    block_ref=block_ref.ref,
                    instance_name=block_ref.instance_name,
                    zone_name=block_ref.zone_name,
                    inputs=block_ref.inputs,
                    outputs=block_ref.outputs,
                    extensions=block_ref.extends,
                )
                operations.append(op)

            elif self._block_needs_update(existing, block_ref):
                # Update operation
                changes = self._compute_block_changes(existing, block_ref)
                op = BlockOperation(
                    operation_type="update",
                    block_ref=block_ref.ref,
                    instance_name=block_ref.instance_name,
                    zone_name=block_ref.zone_name,
                    inputs=block_ref.inputs,
                    outputs=block_ref.outputs,
                    extensions=block_ref.extends,
                    previous_version=existing.version,
                    changes=changes,
                )
                operations.append(op)

        # Check for blocks to delete (in state but not in config)
        config_instances = {b.instance_name for b in config.blocks}
        for resource_id, state in current_state.get_resources_by_type(ResourceType.BLOCK):
            if resource_id not in config_instances:
                op = BlockOperation(
                    operation_type="delete",
                    block_ref=state.block_ref,
                    instance_name=state.instance_name,
                    zone_name=state.zone_name,
                )
                operations.append(op)

        return operations

    def _block_needs_update(
        self,
        existing: BlockState,
        new_config: BlockReferenceConfig,
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

        # Extension count change
        if len(existing.extensions) != len(new_config.extends):
            return True

        return False

    def _compute_block_changes(
        self,
        existing: BlockState,
        new_config: BlockReferenceConfig,
    ) -> List[str]:
        """Compute list of changes between existing and new config."""
        changes = []

        if existing.version != new_config.version:
            changes.append(f"version: {existing.version} → {new_config.version}")

        # Input changes
        for port in set(existing.inputs.keys()) | set(new_config.inputs.keys()):
            old_val = existing.inputs.get(port)
            new_val = new_config.inputs.get(port)
            if old_val != new_val:
                changes.append(f"input.{port}: {old_val} → {new_val}")

        # Output changes
        for port in set(existing.outputs.keys()) | set(new_config.outputs.keys()):
            old_val = existing.outputs.get(port)
            new_val = new_config.outputs.get(port)
            if old_val != new_val:
                changes.append(f"output.{port}: {old_val} → {new_val}")

        # Extension changes
        if len(existing.extensions) != len(new_config.extends):
            changes.append(
                f"extensions: {len(existing.extensions)} → {len(new_config.extends)}"
            )

        return changes

    def _format_block_plan(self, operations: List[BlockOperation]) -> str:
        """Format block operations for display."""
        if not operations:
            return ""

        lines = ["Block Operations:"]

        creates = [op for op in operations if op.operation_type == "create"]
        updates = [op for op in operations if op.operation_type == "update"]
        deletes = [op for op in operations if op.operation_type == "delete"]

        for op in creates:
            lines.append(op.to_display_string())

        for op in updates:
            lines.append(op.to_display_string())

        for op in deletes:
            lines.append(op.to_display_string())

        lines.append("")
        lines.append(
            f"Plan: {len(creates)} to instantiate, "
            f"{len(updates)} to update, "
            f"{len(deletes)} to destroy"
        )

        return "\n".join(lines)
```

---

## State Extension (models/state.py modifications)

```python
"""Modifications to state.py for block support."""

from enum import Enum


# Modification to ResourceType enum
class ResourceType(Enum):
    """Types of IaC-managed resources."""

    PROJECT = "project"
    DATASET = "dataset"
    RECIPE = "recipe"
    SCENARIO = "scenario"
    ZONE = "zone"
    BLOCK = "block"           # NEW
    SOLUTION = "solution"     # NEW (for solution blocks)


# The BlockState class should be imported from models/block.py
# and used by StateManager for tracking block resources.
```

---

## Error Types

```python
"""Error types for block extension."""


class BlockError(Exception):
    """Base class for block-related errors."""
    pass


class BlockRefParseError(BlockError):
    """Invalid block reference format."""

    def __init__(self, ref: str, message: str):
        self.ref = ref
        super().__init__(f"Invalid block ref '{ref}': {message}")


class BlockNotFoundError(BlockError):
    """Block not found in registry."""

    def __init__(self, block_id: str, registry: str):
        self.block_id = block_id
        self.registry = registry
        super().__init__(
            f"Block '{block_id}' not found in registry '{registry}'"
        )


class VersionNotFoundError(BlockError):
    """Block version not found."""

    def __init__(self, block_id: str, version: str, available: List[str]):
        self.block_id = block_id
        self.version = version
        self.available = available
        super().__init__(
            f"Version '{version}' of block '{block_id}' not found. "
            f"Available versions: {available}"
        )


class InputMappingError(BlockError):
    """Required input not mapped."""

    def __init__(self, block_id: str, input_name: str):
        self.block_id = block_id
        self.input_name = input_name
        super().__init__(
            f"Block '{block_id}' requires input '{input_name}' to be mapped"
        )


class ExtensionError(BlockError):
    """Invalid extension configuration."""
    pass


class BlockInstantiationError(BlockError):
    """Block instantiation failed."""
    pass


class CircularBlockDependencyError(BlockError):
    """Circular dependency detected in blocks."""

    def __init__(self, cycle: List[str]):
        self.cycle = cycle
        super().__init__(
            f"Circular dependency detected: {' -> '.join(cycle)}"
        )
```

---

## Public Exports (__init__.py)

```python
"""IaC Block Extension - Public API."""

from .models.block import (
    BlockReferenceConfig,
    SolutionBlockConfig,
    ExtensionConfig,
    RecipeOverrideConfig,
    ClassOverrideConfig,
    BlockState,
    BlockOperation,
)

from .sync.block import (
    BlockSync,
    BlockInstantiationError,
)

from .workflows.blocks.instantiator import (
    BlockInstantiator,
    InstantiationResult,
)

__all__ = [
    # Config models
    "BlockReferenceConfig",
    "SolutionBlockConfig",
    "ExtensionConfig",
    "RecipeOverrideConfig",
    "ClassOverrideConfig",

    # State models
    "BlockState",
    "BlockOperation",

    # Sync
    "BlockSync",

    # Instantiation
    "BlockInstantiator",
    "InstantiationResult",

    # Errors
    "BlockInstantiationError",
]
```
