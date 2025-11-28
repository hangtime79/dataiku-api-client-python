# Discovery Agent API Design

## Module Structure

```
dataikuapi/iac/workflows/discovery/
├── __init__.py           # Public exports
├── agent.py              # DiscoveryAgent main class
├── crawler.py            # ProjectCrawler
├── identifier.py         # BlockIdentifier
├── extractor.py          # MetadataExtractor
├── writer.py             # CatalogWriter
└── models.py             # Data models
```

---

## Public API

### __init__.py

```python
"""Discovery Agent for Dataiku Reusable Workflows."""

from .agent import DiscoveryAgent
from .models import (
    DiscoveryConfig,
    DiscoveryResult,
    BlockMetadata,
    BlockPort,
    BlockContents,
    Dependencies,
)

__all__ = [
    "DiscoveryAgent",
    "DiscoveryConfig",
    "DiscoveryResult",
    "BlockMetadata",
    "BlockPort",
    "BlockContents",
    "Dependencies",
]
```

---

## Data Models (models.py)

```python
"""Data models for Discovery Agent."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class BlockType(Enum):
    """Type of block."""
    ZONE = "zone"
    SOLUTION = "solution"


class PortType(Enum):
    """Type of block port."""
    DATASET = "dataset"
    MODEL = "model"
    FOLDER = "folder"


@dataclass
class DiscoveryConfig:
    """Configuration for discovery operation."""

    # Classification (required)
    hierarchy_level: str
    domain: str

    # Version and protection
    version: str = "1.0.0"
    blocked: bool = False
    tags: List[str] = field(default_factory=list)

    # Behavior
    publish_all_zones: bool = False
    overwrite_existing: bool = False
    create_registry_if_missing: bool = True
    extract_schemas: bool = True
    extract_dependencies: bool = True

    # Filtering
    zone_filter: Optional[List[str]] = None
    exclude_zones: Optional[List[str]] = None

    # Registry
    registry_project_key: str = "BLOCKS_REGISTRY"


@dataclass
class BlockPort:
    """Definition of a block input or output port."""

    name: str
    type: PortType
    required: bool = True
    description: str = ""
    schema: Optional[Dict[str, Any]] = None
    schema_ref: Optional[str] = None


@dataclass
class BlockContents:
    """Internal contents of a block."""

    datasets: List[str] = field(default_factory=list)
    recipes: List[str] = field(default_factory=list)
    models: List[str] = field(default_factory=list)


@dataclass
class Dependencies:
    """Block dependencies."""

    python: List[str] = field(default_factory=list)
    plugins: List[str] = field(default_factory=list)


@dataclass
class BlockMetadata:
    """Complete metadata for a block."""

    # Identity
    block_id: str
    version: str
    type: BlockType = BlockType.ZONE
    blocked: bool = False

    # Source
    source_project: str = ""
    source_zone: str = ""

    # Classification
    hierarchy_level: str = ""
    domain: str = ""
    tags: List[str] = field(default_factory=list)

    # Description
    name: str = ""
    description: str = ""
    owner: str = ""

    # Interface
    inputs: List[BlockPort] = field(default_factory=list)
    outputs: List[BlockPort] = field(default_factory=list)

    # Contents
    contains: BlockContents = field(default_factory=BlockContents)

    # Dependencies
    dependencies: Dependencies = field(default_factory=Dependencies)

    # Artifacts
    bundle_ref: Optional[str] = None

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "block_id": self.block_id,
            "version": self.version,
            "type": self.type.value,
            "blocked": self.blocked,
            "source_project": self.source_project,
            "source_zone": self.source_zone,
            "hierarchy_level": self.hierarchy_level,
            "domain": self.domain,
            "tags": self.tags,
            "name": self.name,
            "description": self.description,
            "owner": self.owner,
            "inputs": [
                {
                    "name": p.name,
                    "type": p.type.value,
                    "required": p.required,
                    "description": p.description,
                }
                for p in self.inputs
            ],
            "outputs": [
                {
                    "name": p.name,
                    "type": p.type.value,
                    "description": p.description,
                }
                for p in self.outputs
            ],
            "contains": {
                "datasets": self.contains.datasets,
                "recipes": self.contains.recipes,
                "models": self.contains.models,
            },
            "dependencies": {
                "python": self.dependencies.python,
                "plugins": self.dependencies.plugins,
            },
            "bundle_ref": self.bundle_ref,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlockMetadata":
        """Create from dictionary."""
        return cls(
            block_id=data["block_id"],
            version=data["version"],
            type=BlockType(data.get("type", "zone")),
            blocked=data.get("blocked", False),
            source_project=data.get("source_project", ""),
            source_zone=data.get("source_zone", ""),
            hierarchy_level=data.get("hierarchy_level", ""),
            domain=data.get("domain", ""),
            tags=data.get("tags", []),
            name=data.get("name", ""),
            description=data.get("description", ""),
            owner=data.get("owner", ""),
            inputs=[
                BlockPort(
                    name=p["name"],
                    type=PortType(p.get("type", "dataset")),
                    required=p.get("required", True),
                    description=p.get("description", ""),
                )
                for p in data.get("inputs", [])
            ],
            outputs=[
                BlockPort(
                    name=p["name"],
                    type=PortType(p.get("type", "dataset")),
                    description=p.get("description", ""),
                )
                for p in data.get("outputs", [])
            ],
            contains=BlockContents(
                datasets=data.get("contains", {}).get("datasets", []),
                recipes=data.get("contains", {}).get("recipes", []),
                models=data.get("contains", {}).get("models", []),
            ),
            dependencies=Dependencies(
                python=data.get("dependencies", {}).get("python", []),
                plugins=data.get("dependencies", {}).get("plugins", []),
            ),
            bundle_ref=data.get("bundle_ref"),
            created_by=data.get("created_by", ""),
        )


@dataclass
class DiscoveryResult:
    """Result of discovery operation."""

    success: bool
    blocks_written: int = 0
    blocks_failed: int = 0
    blocks_skipped: int = 0
    written_blocks: List[str] = field(default_factory=list)
    failed_blocks: List[tuple] = field(default_factory=list)  # (block_id, error)
    skipped_blocks: List[tuple] = field(default_factory=list)  # (zone, reason)
    warnings: List[str] = field(default_factory=list)


# Internal models (not exported)

@dataclass
class DatasetInfo:
    """Internal: Dataset information from crawl."""

    name: str
    type: str
    zone: Optional[str]
    schema: Optional[Dict[str, Any]]
    settings: Dict[str, Any]
    upstream_recipes: List[str]
    downstream_recipes: List[str]


@dataclass
class RecipeInfo:
    """Internal: Recipe information from crawl."""

    name: str
    type: str
    zone: Optional[str]
    inputs: List[str]
    outputs: List[str]
    settings: Dict[str, Any]
    code: Optional[str]


@dataclass
class ZoneInfo:
    """Internal: Zone information from crawl."""

    id: str
    name: str
    datasets: List[str]
    recipes: List[str]
    color: str


@dataclass
class ProjectData:
    """Internal: Complete project data from crawl."""

    project_key: str
    name: str
    description: str
    tags: List[str]
    datasets: Dict[str, DatasetInfo]
    recipes: Dict[str, RecipeInfo]
    zones: Dict[str, ZoneInfo]
    saved_models: List[Dict[str, Any]]


@dataclass
class ZoneBoundary:
    """Internal: Analyzed zone boundary."""

    inputs: List[str]
    outputs: List[str]
    internals: List[str]
    is_valid: bool
    validation_error: Optional[str] = None


@dataclass
class BlockCandidate:
    """Internal: Block candidate from identification."""

    zone: ZoneInfo
    boundary: ZoneBoundary
```

---

## DiscoveryAgent (agent.py)

```python
"""Main Discovery Agent class."""

from typing import Optional
from dataikuapi import DSSClient
from .models import DiscoveryConfig, DiscoveryResult, BlockMetadata
from .crawler import ProjectCrawler
from .identifier import BlockIdentifier
from .extractor import MetadataExtractor
from .writer import CatalogWriter


class DiscoveryAgent:
    """
    Agent for discovering and cataloging reusable blocks in Dataiku projects.

    Usage:
        agent = DiscoveryAgent(client)
        result = agent.discover_project(
            "MY_PROJECT",
            DiscoveryConfig(hierarchy_level="equipment", domain="rotating_equipment")
        )
    """

    def __init__(
        self,
        client: DSSClient,
        registry_project_key: str = "BLOCKS_REGISTRY"
    ):
        """
        Initialize Discovery Agent.

        Args:
            client: Authenticated DSSClient instance
            registry_project_key: Project key for blocks registry
        """
        self.client = client
        self.registry_project_key = registry_project_key

        # Initialize components
        self._crawler = ProjectCrawler(client)
        self._identifier = BlockIdentifier()
        self._writer = CatalogWriter(client, registry_project_key)

    def discover_project(
        self,
        source_project_key: str,
        config: DiscoveryConfig
    ) -> DiscoveryResult:
        """
        Discover and catalog blocks from a source project.

        Args:
            source_project_key: Key of project to discover
            config: Discovery configuration

        Returns:
            DiscoveryResult with summary of operations

        Raises:
            ProjectNotFoundError: If source project doesn't exist
            RegistryNotFoundError: If registry doesn't exist and create_registry_if_missing=False
        """
        result = DiscoveryResult(success=False)

        try:
            # 1. Crawl source project
            project_data = self._crawler.crawl(source_project_key)

            # 2. Identify block candidates
            candidates = self._identifier.identify_blocks(project_data)

            # 3. Apply filters
            candidates = self._apply_filters(candidates, config)

            # 4. Extract metadata for each candidate
            extractor = MetadataExtractor(config)
            blocks = []
            for candidate in candidates:
                try:
                    metadata = extractor.extract_metadata(candidate, project_data)
                    blocks.append(metadata)
                except Exception as e:
                    result.failed_blocks.append((candidate.zone.name, str(e)))
                    result.blocks_failed += 1

            # 5. Write to registry
            write_result = self._writer.write_catalog(blocks)

            # 6. Compile results
            result.success = write_result.success
            result.blocks_written = write_result.blocks_written
            result.written_blocks = write_result.written_blocks
            result.warnings = write_result.warnings

        except Exception as e:
            result.warnings.append(f"Discovery failed: {str(e)}")
            raise

        return result

    def _apply_filters(self, candidates, config):
        """Apply zone filters from config."""
        filtered = candidates

        if config.zone_filter:
            filtered = [
                c for c in filtered
                if c.zone.name in config.zone_filter
            ]

        if config.exclude_zones:
            filtered = [
                c for c in filtered
                if c.zone.name not in config.exclude_zones
            ]

        if not config.publish_all_zones:
            # Only include valid candidates
            filtered = [c for c in filtered if c.boundary.is_valid]

        return filtered

    def discover_zone(
        self,
        source_project_key: str,
        zone_name: str,
        config: DiscoveryConfig
    ) -> Optional[BlockMetadata]:
        """
        Discover a single zone as a block.

        Args:
            source_project_key: Key of project
            zone_name: Name of zone to discover
            config: Discovery configuration

        Returns:
            BlockMetadata if successful, None if zone not found or invalid
        """
        config.zone_filter = [zone_name]
        result = self.discover_project(source_project_key, config)

        if result.written_blocks:
            return self._writer.get_block(result.written_blocks[0])
        return None
```

---

## ProjectCrawler (crawler.py)

```python
"""Project crawler for extracting project structure."""

from typing import Dict, List
from dataikuapi import DSSClient
from .models import (
    ProjectData, DatasetInfo, RecipeInfo, ZoneInfo
)


class ProjectCrawler:
    """Crawls a Dataiku project to extract its structure."""

    def __init__(self, client: DSSClient):
        """
        Initialize crawler.

        Args:
            client: Authenticated DSSClient
        """
        self.client = client

    def crawl(self, project_key: str) -> ProjectData:
        """
        Crawl project and extract all structural information.

        Args:
            project_key: Project to crawl

        Returns:
            ProjectData containing all project information

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        project = self.client.get_project(project_key)

        # Get project metadata
        summary = project.get_summary()
        metadata = project.get_metadata()

        # Get flow for zone information
        flow = project.get_flow()

        # Build zone mapping
        zones = self._crawl_zones(flow)

        # Crawl datasets
        datasets = self._crawl_datasets(project, flow)

        # Crawl recipes
        recipes = self._crawl_recipes(project, flow)

        # Add upstream/downstream info to datasets
        self._link_dataset_recipes(datasets, recipes)

        # Crawl saved models
        saved_models = self._crawl_saved_models(project)

        return ProjectData(
            project_key=project_key,
            name=summary.get("name", project_key),
            description=metadata.get("description", ""),
            tags=metadata.get("tags", []),
            datasets=datasets,
            recipes=recipes,
            zones=zones,
            saved_models=saved_models,
        )

    def _crawl_zones(self, flow) -> Dict[str, ZoneInfo]:
        """Extract zone information from flow."""
        zones = {}
        for zone in flow.list_zones():
            zone_data = zone.get_settings()
            items = zone.get_items()

            zone_datasets = [
                item["id"] for item in items
                if item.get("type") == "DATASET"
            ]
            zone_recipes = [
                item["id"] for item in items
                if item.get("type") == "RECIPE"
            ]

            zones[zone.id] = ZoneInfo(
                id=zone.id,
                name=zone_data.get("name", zone.id),
                datasets=zone_datasets,
                recipes=zone_recipes,
                color=zone_data.get("color", "#2ab1ac"),
            )

        return zones

    def _crawl_datasets(self, project, flow) -> Dict[str, DatasetInfo]:
        """Extract dataset information."""
        datasets = {}

        for ds_item in project.list_datasets():
            ds = project.get_dataset(ds_item.name)
            settings = ds.get_settings()

            # Get zone membership
            try:
                zone = flow.get_zone_of_object(ds)
                zone_id = zone.id if zone else None
            except:
                zone_id = None

            # Get schema
            try:
                schema = ds.get_schema()
            except:
                schema = None

            datasets[ds_item.name] = DatasetInfo(
                name=ds_item.name,
                type=ds_item.type,
                zone=zone_id,
                schema=schema,
                settings=settings.get_raw(),
                upstream_recipes=[],  # Filled later
                downstream_recipes=[],  # Filled later
            )

        return datasets

    def _crawl_recipes(self, project, flow) -> Dict[str, RecipeInfo]:
        """Extract recipe information."""
        recipes = {}

        for recipe_item in project.list_recipes():
            recipe = project.get_recipe(recipe_item.name)
            settings = recipe.get_settings()
            raw = settings.get_raw()

            # Get zone membership
            try:
                zone = flow.get_zone_of_object(recipe)
                zone_id = zone.id if zone else None
            except:
                zone_id = None

            # Extract inputs and outputs
            inputs = []
            for input_role in raw.get("inputs", {}).values():
                for item in input_role.get("items", []):
                    inputs.append(item.get("ref", ""))

            outputs = []
            for output_role in raw.get("outputs", {}).values():
                for item in output_role.get("items", []):
                    outputs.append(item.get("ref", ""))

            # Get code if applicable
            code = None
            if hasattr(settings, 'get_code'):
                try:
                    code = settings.get_code()
                except:
                    pass

            recipes[recipe_item.name] = RecipeInfo(
                name=recipe_item.name,
                type=recipe_item.type,
                zone=zone_id,
                inputs=inputs,
                outputs=outputs,
                settings=raw,
                code=code,
            )

        return recipes

    def _link_dataset_recipes(
        self,
        datasets: Dict[str, DatasetInfo],
        recipes: Dict[str, RecipeInfo]
    ):
        """Link datasets to their upstream/downstream recipes."""
        for recipe_name, recipe in recipes.items():
            # Recipe outputs -> dataset upstream
            for output in recipe.outputs:
                if output in datasets:
                    datasets[output].upstream_recipes.append(recipe_name)

            # Recipe inputs -> dataset downstream
            for input_ds in recipe.inputs:
                if input_ds in datasets:
                    datasets[input_ds].downstream_recipes.append(recipe_name)

    def _crawl_saved_models(self, project) -> List[Dict]:
        """Extract saved model information."""
        models = []
        for sm in project.list_saved_models():
            model = project.get_saved_model(sm["id"])
            try:
                active_version = model.get_active_version()
            except:
                active_version = None

            models.append({
                "id": sm["id"],
                "name": sm.get("name", sm["id"]),
                "type": sm.get("type"),
                "active_version": active_version.get("id") if active_version else None,
            })

        return models
```

---

## BlockIdentifier (identifier.py)

```python
"""Block identification from project structure."""

from typing import List, Tuple, Optional, Set
from .models import (
    ProjectData, ZoneInfo, ZoneBoundary, BlockCandidate,
    DatasetInfo, RecipeInfo
)


class BlockIdentifier:
    """Identifies valid block candidates from project structure."""

    def identify_blocks(self, project_data: ProjectData) -> List[BlockCandidate]:
        """
        Identify all valid block candidates in project.

        Args:
            project_data: Crawled project data

        Returns:
            List of BlockCandidate objects
        """
        candidates = []

        for zone_id, zone in project_data.zones.items():
            # Skip default zone if it has no meaningful structure
            if self._is_empty_default_zone(zone):
                continue

            # Analyze zone boundary
            boundary = self._analyze_zone_boundary(
                zone,
                project_data.datasets,
                project_data.recipes
            )

            # Create candidate
            candidate = BlockCandidate(zone=zone, boundary=boundary)
            candidates.append(candidate)

        return candidates

    def _is_empty_default_zone(self, zone: ZoneInfo) -> bool:
        """Check if zone is an empty default zone."""
        return (
            zone.name.lower() == "default" and
            len(zone.datasets) == 0 and
            len(zone.recipes) == 0
        )

    def _analyze_zone_boundary(
        self,
        zone: ZoneInfo,
        datasets: Dict[str, DatasetInfo],
        recipes: Dict[str, RecipeInfo]
    ) -> ZoneBoundary:
        """
        Analyze a zone's boundary to identify inputs, outputs, internals.

        Args:
            zone: Zone to analyze
            datasets: All project datasets
            recipes: All project recipes

        Returns:
            ZoneBoundary with inputs, outputs, internals, validity
        """
        zone_dataset_set = set(zone.datasets)
        zone_recipe_set = set(zone.recipes)

        inputs = []
        outputs = []
        internals = []

        for ds_name in zone.datasets:
            if ds_name not in datasets:
                continue

            ds = datasets[ds_name]

            # Check if input (no upstream recipes in zone)
            upstream_in_zone = [
                r for r in ds.upstream_recipes
                if r in zone_recipe_set
            ]
            is_input = len(upstream_in_zone) == 0

            # Check if output (has downstream consumers outside zone)
            downstream_outside = [
                r for r in ds.downstream_recipes
                if r not in zone_recipe_set
            ]
            is_output = len(downstream_outside) > 0

            # Also check if terminal (output of recipe with no further processing)
            is_terminal = (
                len(ds.downstream_recipes) == 0 and
                len(ds.upstream_recipes) > 0
            )

            if is_input:
                inputs.append(ds_name)
            elif is_output or is_terminal:
                outputs.append(ds_name)
            else:
                internals.append(ds_name)

        # Validate containment
        is_valid, error = self._validate_containment(
            zone, zone_dataset_set, zone_recipe_set, recipes
        )

        # Must have at least one input and one output
        if is_valid and (len(inputs) == 0 or len(outputs) == 0):
            is_valid = False
            error = "Zone must have at least one input and one output"

        return ZoneBoundary(
            inputs=inputs,
            outputs=outputs,
            internals=internals,
            is_valid=is_valid,
            validation_error=error,
        )

    def _validate_containment(
        self,
        zone: ZoneInfo,
        zone_datasets: Set[str],
        zone_recipes: Set[str],
        recipes: Dict[str, RecipeInfo]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that zone is properly contained.

        All recipe inputs must be in zone or be explicit inputs.
        All recipe outputs must be in zone.
        """
        for recipe_name in zone.recipes:
            if recipe_name not in recipes:
                continue

            recipe = recipes[recipe_name]

            # Check outputs are in zone
            for output in recipe.outputs:
                if output not in zone_datasets:
                    return False, f"Recipe {recipe_name} output {output} is outside zone"

        return True, None
```

---

## MetadataExtractor (extractor.py)

```python
"""Metadata extraction from block candidates."""

import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from .models import (
    DiscoveryConfig, BlockMetadata, BlockPort, BlockContents,
    Dependencies, BlockCandidate, ProjectData, PortType, BlockType
)


class MetadataExtractor:
    """Extracts detailed metadata from block candidates."""

    # Standard library modules to exclude from dependencies
    STDLIB_MODULES = {
        'os', 'sys', 'json', 'datetime', 'time', 'math', 'random',
        're', 'collections', 'itertools', 'functools', 'typing',
        'pathlib', 'io', 'csv', 'logging', 'copy', 'pickle',
    }

    def __init__(self, config: DiscoveryConfig):
        """
        Initialize extractor.

        Args:
            config: Discovery configuration
        """
        self.config = config

    def extract_metadata(
        self,
        candidate: BlockCandidate,
        project_data: ProjectData
    ) -> BlockMetadata:
        """
        Extract complete metadata for a block candidate.

        Args:
            candidate: Block candidate
            project_data: Source project data

        Returns:
            BlockMetadata with all extracted information
        """
        zone = candidate.zone
        boundary = candidate.boundary

        # Generate block ID
        block_id = self._generate_block_id(zone.name)

        # Extract inputs
        inputs = [
            self._extract_port_metadata(
                project_data.datasets[ds_name],
                required=True
            )
            for ds_name in boundary.inputs
            if ds_name in project_data.datasets
        ]

        # Extract outputs
        outputs = [
            self._extract_port_metadata(
                project_data.datasets[ds_name],
                required=False
            )
            for ds_name in boundary.outputs
            if ds_name in project_data.datasets
        ]

        # Extract contents
        contains = BlockContents(
            datasets=boundary.internals,
            recipes=zone.recipes,
            models=self._find_models_in_zone(zone, project_data),
        )

        # Extract dependencies
        dependencies = Dependencies()
        if self.config.extract_dependencies:
            dependencies = self._extract_dependencies(zone, project_data)

        return BlockMetadata(
            block_id=block_id,
            version=self.config.version,
            type=BlockType.ZONE,
            blocked=self.config.blocked,
            source_project=project_data.project_key,
            source_zone=zone.name,
            hierarchy_level=self.config.hierarchy_level,
            domain=self.config.domain,
            tags=self.config.tags.copy(),
            name=zone.name,
            description=f"Block from zone '{zone.name}' in project '{project_data.project_key}'",
            inputs=inputs,
            outputs=outputs,
            contains=contains,
            dependencies=dependencies,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def _generate_block_id(self, zone_name: str) -> str:
        """
        Generate block ID from zone name.

        Rules:
        - Convert to UPPERCASE
        - Replace spaces and hyphens with underscores
        - Remove invalid characters
        - Truncate to 64 chars
        """
        # Uppercase
        block_id = zone_name.upper()

        # Replace spaces and hyphens
        block_id = block_id.replace(" ", "_").replace("-", "_")

        # Remove invalid characters (keep only alphanumeric and underscore)
        block_id = re.sub(r"[^A-Z0-9_]", "", block_id)

        # Remove consecutive underscores
        block_id = re.sub(r"_+", "_", block_id)

        # Remove leading/trailing underscores
        block_id = block_id.strip("_")

        # Truncate
        if len(block_id) > 64:
            block_id = block_id[:64]

        return block_id

    def _extract_port_metadata(
        self,
        dataset_info,
        required: bool
    ) -> BlockPort:
        """Extract port metadata from dataset info."""
        schema = None
        if self.config.extract_schemas and dataset_info.schema:
            schema = self._normalize_schema(dataset_info.schema)

        return BlockPort(
            name=dataset_info.name,
            type=PortType.DATASET,
            required=required,
            description=dataset_info.settings.get("description", ""),
            schema=schema,
        )

    def _normalize_schema(self, raw_schema: Dict) -> Dict:
        """Normalize Dataiku schema to standard format."""
        if not raw_schema or "columns" not in raw_schema:
            return None

        columns = []
        for col in raw_schema["columns"]:
            columns.append({
                "name": col.get("name", ""),
                "type": self._map_dataiku_type(col.get("type", "string")),
                "description": col.get("comment", ""),
                "nullable": not col.get("notNull", False),
            })

        return {
            "format_version": "1.0",
            "columns": columns,
        }

    def _map_dataiku_type(self, dataiku_type: str) -> str:
        """Map Dataiku column type to standard type."""
        mapping = {
            "string": "string",
            "int": "integer",
            "bigint": "integer",
            "smallint": "integer",
            "tinyint": "integer",
            "float": "double",
            "double": "double",
            "boolean": "boolean",
            "date": "date",
            "array": "array",
            "object": "object",
            "map": "object",
        }
        return mapping.get(dataiku_type.lower(), "string")

    def _find_models_in_zone(
        self,
        zone,
        project_data: ProjectData
    ) -> List[str]:
        """Find saved models associated with zone recipes."""
        # Models are typically created by specific recipe types
        # This is a simplified implementation
        return []

    def _extract_dependencies(
        self,
        zone,
        project_data: ProjectData
    ) -> Dependencies:
        """Extract Python and plugin dependencies from zone recipes."""
        python_deps = set()
        plugin_deps = set()

        for recipe_name in zone.recipes:
            if recipe_name not in project_data.recipes:
                continue

            recipe = project_data.recipes[recipe_name]

            # Check for plugin recipes
            if recipe.type.startswith("Custom"):
                # Extract plugin ID from recipe type
                plugin_deps.add(recipe.type)

            # Parse Python imports from code recipes
            if recipe.code:
                imports = self._parse_python_imports(recipe.code)
                python_deps.update(imports)

        return Dependencies(
            python=sorted(python_deps),
            plugins=sorted(plugin_deps),
        )

    def _parse_python_imports(self, code: str) -> List[str]:
        """
        Parse Python code for import statements.

        Returns top-level package names, excluding standard library.
        """
        imports = set()

        # Pattern for "import X" or "import X as Y"
        import_pattern = r"^import\s+(\w+)"

        # Pattern for "from X import Y"
        from_pattern = r"^from\s+(\w+)"

        for line in code.split("\n"):
            line = line.strip()

            match = re.match(import_pattern, line)
            if match:
                module = match.group(1)
                if module not in self.STDLIB_MODULES:
                    imports.add(module)
                continue

            match = re.match(from_pattern, line)
            if match:
                module = match.group(1)
                if module not in self.STDLIB_MODULES:
                    imports.add(module)

        return list(imports)
```

---

## CatalogWriter (writer.py)

```python
"""Catalog writer for BLOCKS_REGISTRY."""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataikuapi import DSSClient
from .models import BlockMetadata, DiscoveryResult


class CatalogWriter:
    """Writes block catalog to BLOCKS_REGISTRY."""

    def __init__(self, client: DSSClient, registry_key: str = "BLOCKS_REGISTRY"):
        """
        Initialize writer.

        Args:
            client: Authenticated DSSClient
            registry_key: Registry project key
        """
        self.client = client
        self.registry_key = registry_key
        self._registry = None

    def write_catalog(self, blocks: List[BlockMetadata]) -> DiscoveryResult:
        """
        Write blocks to registry.

        Args:
            blocks: List of blocks to write

        Returns:
            DiscoveryResult with write summary
        """
        result = DiscoveryResult(success=True)

        # Ensure registry exists
        registry = self._get_or_create_registry()

        wiki = registry.get_wiki()
        library = registry.get_library()

        written = []
        for block in blocks:
            try:
                # Write wiki article
                self._write_wiki_article(block, wiki)

                # Write schemas to library
                self._write_schemas(block, library)

                written.append(block)
                result.written_blocks.append(block.block_id)
                result.blocks_written += 1

            except Exception as e:
                result.failed_blocks.append((block.block_id, str(e)))
                result.blocks_failed += 1

        # Update master index
        if written:
            try:
                self._update_index(written, library)
            except Exception as e:
                result.warnings.append(f"Index update failed: {e}")

        return result

    def _get_or_create_registry(self):
        """Get registry project, creating if needed."""
        if self._registry:
            return self._registry

        try:
            self._registry = self.client.get_project(self.registry_key)
        except:
            # Create registry
            self._registry = self._create_registry()

        return self._registry

    def _create_registry(self):
        """Create new registry project with structure."""
        project = self.client.create_project(
            self.registry_key,
            "Blocks Registry"
        )

        # Initialize wiki structure
        wiki = project.get_wiki()
        wiki.create_article("Home", content=self._get_home_template())
        wiki.create_article("_BLOCKS")
        wiki.create_article("_INDEX", parent_id="_BLOCKS")

        # Initialize library structure
        library = project.get_library()
        library.add_folder("blocks")
        library.add_folder("blocks/schemas")
        library.add_folder("blocks/manifests")

        # Create initial index
        index_file = library.add_file("blocks/index.json")
        index_file.write(json.dumps({
            "format_version": "1.0",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "block_count": 0,
            "blocks": []
        }, indent=2))

        return project

    def _write_wiki_article(self, block: BlockMetadata, wiki):
        """Write block as wiki article."""
        content = self._generate_wiki_content(block)

        # Article path based on hierarchy
        article_name = block.block_id

        # Try to create/update article
        try:
            # Check if exists
            article = wiki.get_article(article_name)
            article_data = article.get_data()

            # Preserve manual additions (content after "## Manual Notes")
            existing_content = article_data.get_body()
            manual_section = self._extract_manual_section(existing_content)
            if manual_section:
                content += f"\n\n{manual_section}"

            article_data.set_body(content)
            article_data.save()

        except:
            # Create new article under _BLOCKS
            wiki.create_article(
                article_name,
                parent_id="_BLOCKS",
                content=content
            )

    def _generate_wiki_content(self, block: BlockMetadata) -> str:
        """Generate markdown content for block."""
        lines = []

        # YAML frontmatter
        lines.append("---")
        lines.append(f"block_id: {block.block_id}")
        lines.append(f"version: {block.version}")
        lines.append(f"type: {block.type.value}")
        lines.append(f"blocked: {str(block.blocked).lower()}")
        lines.append(f"source_project: {block.source_project}")
        lines.append(f"source_zone: {block.source_zone}")
        lines.append(f"hierarchy_level: {block.hierarchy_level}")
        lines.append(f"domain: {block.domain}")
        lines.append(f"tags: [{', '.join(block.tags)}]")
        lines.append("---")
        lines.append("")

        # Title
        lines.append(f"# {block.name or block.block_id}")
        lines.append("")

        # Description
        lines.append("## Description")
        lines.append("")
        lines.append(block.description or "No description provided.")
        lines.append("")

        # Inputs
        lines.append("## Inputs")
        lines.append("")
        lines.append("| Name | Type | Required | Description |")
        lines.append("|------|------|----------|-------------|")
        for inp in block.inputs:
            lines.append(f"| {inp.name} | {inp.type.value} | {'yes' if inp.required else 'no'} | {inp.description} |")
        lines.append("")

        # Outputs
        lines.append("## Outputs")
        lines.append("")
        lines.append("| Name | Type | Description |")
        lines.append("|------|------|-------------|")
        for out in block.outputs:
            lines.append(f"| {out.name} | {out.type.value} | {out.description} |")
        lines.append("")

        # Contains
        lines.append("## Contains")
        lines.append("")
        if block.contains.datasets:
            lines.append(f"**Datasets:** {', '.join(block.contains.datasets)}")
        if block.contains.recipes:
            lines.append(f"**Recipes:** {', '.join(block.contains.recipes)}")
        if block.contains.models:
            lines.append(f"**Models:** {', '.join(block.contains.models)}")
        lines.append("")

        # Dependencies
        if block.dependencies.python or block.dependencies.plugins:
            lines.append("## Dependencies")
            lines.append("")
            if block.dependencies.python:
                lines.append(f"- Python: {', '.join(block.dependencies.python)}")
            if block.dependencies.plugins:
                lines.append(f"- Plugins: {', '.join(block.dependencies.plugins)}")
            lines.append("")

        # Usage
        lines.append("## Usage")
        lines.append("")
        lines.append("```yaml")
        lines.append("blocks:")
        lines.append(f'  - ref: "BLOCKS_REGISTRY/{block.block_id}@{block.version}"')
        if block.inputs:
            lines.append("    inputs:")
            lines.append(f"      {block.inputs[0].name}: your_dataset")
        if block.outputs:
            lines.append("    outputs:")
            lines.append(f"      {block.outputs[0].name}: your_output")
        lines.append("```")
        lines.append("")

        # Changelog
        lines.append("## Changelog")
        lines.append("")
        lines.append(f"- {block.version}: Initial release")

        return "\n".join(lines)

    def _extract_manual_section(self, content: str) -> Optional[str]:
        """Extract manually added content from existing article."""
        marker = "## Manual Notes"
        if marker in content:
            idx = content.index(marker)
            return content[idx:]
        return None

    def _write_schemas(self, block: BlockMetadata, library):
        """Write schema files for block ports."""
        # Ensure directory exists
        try:
            library.get_folder(f"blocks/schemas/{block.block_id}")
        except:
            library.add_folder(f"blocks/schemas/{block.block_id}")

        # Write input schemas
        for port in block.inputs:
            if port.schema:
                path = f"blocks/schemas/{block.block_id}/{port.name}_input.json"
                try:
                    f = library.get_file(path)
                except:
                    f = library.add_file(path)
                f.write(json.dumps(port.schema, indent=2))

        # Write output schemas
        for port in block.outputs:
            if port.schema:
                path = f"blocks/schemas/{block.block_id}/{port.name}_output.json"
                try:
                    f = library.get_file(path)
                except:
                    f = library.add_file(path)
                f.write(json.dumps(port.schema, indent=2))

    def _update_index(self, blocks: List[BlockMetadata], library):
        """Update master index.json with new blocks."""
        # Read existing index
        try:
            index_file = library.get_file("blocks/index.json")
            index = json.loads(index_file.read())
        except:
            index = {
                "format_version": "1.0",
                "updated_at": None,
                "block_count": 0,
                "blocks": []
            }

        # Create summaries for new blocks
        new_summaries = [self._create_summary(b) for b in blocks]

        # Merge with existing
        index = self._merge_index(index, new_summaries)

        # Write back
        index_file = library.get_file("blocks/index.json")
        index_file.write(json.dumps(index, indent=2))

    def _create_summary(self, block: BlockMetadata) -> Dict[str, Any]:
        """Create index summary for block."""
        return {
            "block_id": block.block_id,
            "version": block.version,
            "type": block.type.value,
            "blocked": block.blocked,
            "hierarchy_level": block.hierarchy_level,
            "domain": block.domain,
            "tags": block.tags,
            "name": block.name,
            "inputs": [
                {"name": p.name, "type": p.type.value, "required": p.required}
                for p in block.inputs
            ],
            "outputs": [
                {"name": p.name, "type": p.type.value}
                for p in block.outputs
            ],
            "source_project": block.source_project,
        }

    def _merge_index(
        self,
        existing: Dict[str, Any],
        new_summaries: List[Dict]
    ) -> Dict[str, Any]:
        """Merge new summaries with existing index."""
        # Build lookup of existing
        existing_lookup = {}
        for block in existing.get("blocks", []):
            key = (block["block_id"], block["version"])
            existing_lookup[key] = block

        # Build lookup of new
        new_lookup = {}
        for block in new_summaries:
            key = (block["block_id"], block["version"])
            new_lookup[key] = block

        # Merge: keep existing not in new, add all new
        merged = []

        for key, block in existing_lookup.items():
            if key not in new_lookup:
                merged.append(block)

        merged.extend(new_summaries)

        # Sort by block_id, version
        merged.sort(key=lambda b: (b["block_id"], b["version"]))

        return {
            "format_version": "1.0",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "block_count": len(set(b["block_id"] for b in merged)),
            "blocks": merged,
        }

    def _get_home_template(self) -> str:
        """Get template for registry home page."""
        return """# Blocks Registry

Welcome to the centralized registry of reusable workflow blocks.

## Quick Links

- [Block Index](_BLOCKS/_INDEX) - All available blocks

## How to Use

Reference a block in your IaC configuration:

```yaml
blocks:
  - ref: "BLOCKS_REGISTRY/BLOCK_ID@VERSION"
    inputs:
      INPUT_PORT: your_dataset
    outputs:
      OUTPUT_PORT: your_output
```
"""
```
