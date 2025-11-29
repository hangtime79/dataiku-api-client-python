# Executing Agent API Design

## Module Structure

```
dataikuapi/iac/workflows/executing/
├── __init__.py           # Public exports
├── agent.py              # Main ExecutingAgent class
├── catalog.py            # CatalogReader class
├── matcher.py            # BlockMatcher class
├── resolver.py           # DependencyResolver class
├── generator.py          # ConfigGenerator class
├── intent.py             # IntentParser class
└── models.py             # Data models
```

---

## Public API

### __init__.py

```python
"""Executing Agent for Dataiku Reusable Workflows."""

from .agent import ExecutingAgent
from .models import (
    BlockQuery,
    MatchResult,
    ResolvedPlan,
    Wire,
    CompositionConfig,
    CompositionResult,
    ExecutingAgentConfig,
    ExtensionConfig,
    RecipeOverride,
    ClassOverride,
)

__all__ = [
    "ExecutingAgent",
    "BlockQuery",
    "MatchResult",
    "ResolvedPlan",
    "Wire",
    "CompositionConfig",
    "CompositionResult",
    "ExecutingAgentConfig",
    "ExtensionConfig",
    "RecipeOverride",
    "ClassOverride",
]
```

---

## Data Models (models.py)

```python
"""Data models for Executing Agent."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import yaml


@dataclass
class BlockQuery:
    """Query for finding blocks in catalog."""

    # Filters
    hierarchy_level: Optional[str] = None
    domain: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)

    # Protection filters
    blocked_only: bool = False
    exclude_blocked: bool = False

    # Version filter
    min_version: Optional[str] = None

    # Result limits
    max_results: int = 10

    # Schema requirements
    input_requirements: List[Dict[str, Any]] = field(default_factory=list)
    output_requirements: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MatchResult:
    """Result of block matching."""

    block_id: str
    version: str
    score: float
    block_summary: Dict[str, Any]
    match_details: Dict[str, Any] = field(default_factory=dict)

    @property
    def ref(self) -> str:
        """Get block reference string."""
        return f"BLOCKS_REGISTRY/{self.block_id}@{self.version}"


@dataclass
class Wire:
    """Connection between block ports."""

    source_block: str
    source_port: str
    target_block: str
    target_port: str
    dataset_name: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "source_block": self.source_block,
            "source_port": self.source_port,
            "target_block": self.target_block,
            "target_port": self.target_port,
            "dataset_name": self.dataset_name,
        }


@dataclass
class ResolvedPlan:
    """Resolved execution plan for blocks."""

    execution_order: List[str]
    wiring: List[Wire]
    stages: List[List[str]] = field(default_factory=list)

    def get_stage_for_block(self, block_id: str) -> int:
        """Get stage number for a block."""
        for i, stage in enumerate(self.stages):
            if block_id in stage:
                return i
        return -1


@dataclass
class WiringHint:
    """Explicit wiring hint from user."""

    source_block: str
    source_port: str
    target_block: str
    target_port: str


@dataclass
class RecipeOverride:
    """Override a recipe within a block."""

    recipe: str
    override_with: str


@dataclass
class ClassOverride:
    """Override a class within a block."""

    recipe: str
    use_class: str
    class_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtensionConfig:
    """Extension configuration for a block."""

    block_id: str
    recipe_overrides: List[RecipeOverride] = field(default_factory=list)
    class_overrides: List[ClassOverride] = field(default_factory=list)


@dataclass
class BlockReferenceConfig:
    """Block reference in generated config."""

    ref: str
    instance_name: str
    zone_name: str
    inputs: Dict[str, str] = field(default_factory=dict)
    outputs: Dict[str, str] = field(default_factory=dict)
    extends: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "ref": self.ref,
            "instance_name": self.instance_name,
            "zone_name": self.zone_name,
            "inputs": self.inputs,
            "outputs": self.outputs,
        }
        if self.extends:
            result["extends"] = self.extends
        return result


@dataclass
class ProjectConfig:
    """Project configuration."""

    key: str
    name: str
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
        }


@dataclass
class DatasetConfig:
    """Dataset configuration."""

    name: str
    type: str
    connection: Optional[str] = None
    table: Optional[str] = None
    path: Optional[str] = None
    format_type: Optional[str] = None
    comment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"name": self.name, "type": self.type}
        if self.connection:
            result["connection"] = self.connection
        if self.table:
            result["table"] = self.table
        if self.path:
            result["path"] = self.path
        if self.format_type:
            result["format_type"] = self.format_type
        if self.comment:
            result["comment"] = self.comment
        return result


@dataclass
class RecipeConfig:
    """Recipe configuration."""

    name: str
    type: str
    inputs: List[Dict[str, str]] = field(default_factory=list)
    outputs: List[Dict[str, str]] = field(default_factory=list)
    code: Optional[str] = None
    code_ref: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "type": self.type,
            "inputs": self.inputs,
            "outputs": self.outputs,
        }
        if self.code:
            result["code"] = self.code
        if self.code_ref:
            result["code_ref"] = self.code_ref
        return result


@dataclass
class CompositionConfig:
    """Complete composition configuration."""

    version: str = "1.0"
    project: ProjectConfig = None
    blocks: List[BlockReferenceConfig] = field(default_factory=list)
    datasets: List[DatasetConfig] = field(default_factory=list)
    recipes: List[RecipeConfig] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "project": self.project.to_dict() if self.project else {},
            "blocks": [b.to_dict() for b in self.blocks],
            "datasets": [d.to_dict() for d in self.datasets],
            "recipes": [r.to_dict() for r in self.recipes],
        }

    def to_yaml(self) -> str:
        """Serialize to YAML string."""
        return yaml.dump(
            self.to_dict(),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )


@dataclass
class CompositionResult:
    """Result of composition operation."""

    success: bool
    config: Optional[CompositionConfig] = None
    matches: List[MatchResult] = field(default_factory=list)
    plan: Optional[ResolvedPlan] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_yaml(self) -> str:
        """Get config as YAML."""
        if self.config:
            return self.config.to_yaml()
        return ""


@dataclass
class ExecutingAgentConfig:
    """Configuration for ExecutingAgent."""

    registry_project_key: str = "BLOCKS_REGISTRY"
    default_max_results: int = 10
    min_match_score: float = 0.3
    prefer_newer_versions: bool = True
    auto_wire: bool = True
    strict_schema_matching: bool = False
    generate_placeholders: bool = True
    include_comments: bool = True


# Catalog models (internal but exported for typing)

@dataclass
class BlockSummary:
    """Summary of a block from catalog index."""

    block_id: str
    version: str
    type: str
    blocked: bool
    hierarchy_level: str
    domain: str
    tags: List[str]
    name: str
    description: Optional[str]
    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]
    source_project: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlockSummary":
        return cls(
            block_id=data["block_id"],
            version=data["version"],
            type=data.get("type", "zone"),
            blocked=data.get("blocked", False),
            hierarchy_level=data.get("hierarchy_level", ""),
            domain=data.get("domain", ""),
            tags=data.get("tags", []),
            name=data.get("name", data["block_id"]),
            description=data.get("description"),
            inputs=data.get("inputs", []),
            outputs=data.get("outputs", []),
            source_project=data.get("source_project", ""),
        )


@dataclass
class BlockCatalog:
    """Loaded block catalog."""

    format_version: str = "1.0"
    updated_at: Optional[str] = None
    blocks: Dict[str, BlockSummary] = field(default_factory=dict)

    # Indexes for fast lookup
    _hierarchy_index: Dict[str, List[str]] = field(default_factory=dict)
    _domain_index: Dict[str, List[str]] = field(default_factory=dict)
    _tag_index: Dict[str, List[str]] = field(default_factory=dict)

    def add_block(self, summary: BlockSummary):
        """Add a block to the catalog."""
        key = f"{summary.block_id}@{summary.version}"
        self.blocks[key] = summary

    def get_block(self, block_id: str, version: str = None) -> Optional[BlockSummary]:
        """Get a block by ID and optional version."""
        if version:
            return self.blocks.get(f"{block_id}@{version}")

        # Find latest version
        matches = [
            (k, v) for k, v in self.blocks.items()
            if v.block_id == block_id
        ]
        if not matches:
            return None

        # Sort by version descending
        matches.sort(key=lambda x: x[1].version, reverse=True)
        return matches[0][1]

    def all_blocks(self) -> List[BlockSummary]:
        """Get all blocks."""
        return list(self.blocks.values())

    def build_indexes(self):
        """Build lookup indexes."""
        self._hierarchy_index = {}
        self._domain_index = {}
        self._tag_index = {}

        for key, block in self.blocks.items():
            # Hierarchy index
            if block.hierarchy_level:
                if block.hierarchy_level not in self._hierarchy_index:
                    self._hierarchy_index[block.hierarchy_level] = []
                self._hierarchy_index[block.hierarchy_level].append(key)

            # Domain index
            if block.domain:
                if block.domain not in self._domain_index:
                    self._domain_index[block.domain] = []
                self._domain_index[block.domain].append(key)

            # Tag index
            for tag in block.tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = []
                self._tag_index[tag].append(key)

    def get_by_hierarchy(self, level: str) -> List[BlockSummary]:
        """Get blocks by hierarchy level."""
        keys = self._hierarchy_index.get(level, [])
        return [self.blocks[k] for k in keys]

    def get_by_domain(self, domain: str) -> List[BlockSummary]:
        """Get blocks by domain."""
        keys = self._domain_index.get(domain, [])
        return [self.blocks[k] for k in keys]

    def get_by_tag(self, tag: str) -> List[BlockSummary]:
        """Get blocks by tag."""
        keys = self._tag_index.get(tag, [])
        return [self.blocks[k] for k in keys]
```

---

## ExecutingAgent (agent.py)

```python
"""Main Executing Agent class."""

from typing import Dict, List, Optional
from dataikuapi import DSSClient
from .models import (
    BlockQuery,
    CompositionConfig,
    CompositionResult,
    ExecutingAgentConfig,
    ExtensionConfig,
    WiringHint,
)
from .catalog import CatalogReader
from .matcher import BlockMatcher
from .resolver import DependencyResolver
from .generator import ConfigGenerator
from .intent import IntentParser


class ExecutingAgent:
    """
    Agent for composing blocks into new projects.

    Reads from BLOCKS_REGISTRY and generates IaC configurations
    based on user queries.

    Usage:
        agent = ExecutingAgent(client)
        result = agent.compose(
            query=BlockQuery(domain="rotating_equipment"),
            target_project_key="NEW_PROJECT"
        )
        print(result.config.to_yaml())
    """

    def __init__(
        self,
        client: DSSClient,
        config: ExecutingAgentConfig = None
    ):
        """
        Initialize Executing Agent.

        Args:
            client: Authenticated DSSClient instance
            config: Agent configuration (optional)
        """
        self.client = client
        self.config = config or ExecutingAgentConfig()

        # Initialize components
        self._catalog_reader = CatalogReader(
            client,
            self.config.registry_project_key
        )
        self._matcher = None  # Lazy init after catalog load
        self._resolver = DependencyResolver()
        self._generator = ConfigGenerator(self.config)
        self._intent_parser = None  # Lazy init after catalog load

    def compose(
        self,
        query: BlockQuery,
        target_project_key: str,
        external_inputs: Dict[str, str] = None,
        external_outputs: Dict[str, str] = None,
        extensions: List[ExtensionConfig] = None,
        wiring_hints: List[WiringHint] = None
    ) -> CompositionResult:
        """
        Compose blocks matching query into a new project configuration.

        Args:
            query: Block query with filters
            target_project_key: Key for target project
            external_inputs: Map block input names to external datasets
            external_outputs: Map block output names to external datasets
            extensions: Block extensions (recipe/class overrides)
            wiring_hints: Explicit wiring between blocks

        Returns:
            CompositionResult with config and metadata
        """
        result = CompositionResult(success=False)

        try:
            # 1. Load catalog
            catalog = self._catalog_reader.load_catalog()

            # 2. Initialize matcher with catalog
            self._matcher = BlockMatcher(catalog, self.config)

            # 3. Find matching blocks
            matches = self._matcher.match(query)

            if not matches:
                result.errors.append("No blocks match the query")
                result.warnings.append(
                    "Try relaxing filters or broadening capabilities"
                )
                return result

            result.matches = matches

            # 4. Get block summaries for matched blocks
            blocks = [m.block_summary for m in matches]

            # 5. Resolve dependencies
            try:
                plan = self._resolver.resolve(blocks, wiring_hints)
                result.plan = plan
            except CircularDependencyError as e:
                result.errors.append(f"Circular dependency: {e}")
                return result

            # 6. Generate configuration
            config = self._generator.generate(
                plan=plan,
                target_project_key=target_project_key,
                external_inputs=external_inputs or {},
                external_outputs=external_outputs or {},
                extensions=extensions or [],
                blocks_metadata={m.block_id: m for m in matches}
            )

            result.config = config
            result.success = True

        except Exception as e:
            result.errors.append(str(e))

        return result

    def compose_from_intent(
        self,
        intent: str,
        target_project_key: str,
        external_inputs: Dict[str, str] = None,
        external_outputs: Dict[str, str] = None
    ) -> CompositionResult:
        """
        Compose blocks from natural language intent.

        Args:
            intent: Natural language description of needs
            target_project_key: Key for target project
            external_inputs: External input mappings
            external_outputs: External output mappings

        Returns:
            CompositionResult with config and metadata
        """
        # Load catalog for intent parser
        catalog = self._catalog_reader.load_catalog()
        self._intent_parser = IntentParser(catalog)

        # Parse intent to query
        query = self._intent_parser.parse(intent)

        # Compose using parsed query
        return self.compose(
            query=query,
            target_project_key=target_project_key,
            external_inputs=external_inputs,
            external_outputs=external_outputs
        )

    def search(self, query: BlockQuery) -> List[MatchResult]:
        """
        Search for blocks without generating config.

        Args:
            query: Block query

        Returns:
            List of matching blocks with scores
        """
        catalog = self._catalog_reader.load_catalog()
        self._matcher = BlockMatcher(catalog, self.config)
        return self._matcher.match(query)

    def get_block_details(self, block_id: str, version: str = None) -> Optional[dict]:
        """
        Get full details for a specific block.

        Args:
            block_id: Block identifier
            version: Specific version (optional, defaults to latest)

        Returns:
            Block metadata dict or None if not found
        """
        return self._catalog_reader.get_block(block_id, version)

    def list_hierarchy_levels(self) -> List[str]:
        """Get available hierarchy levels from catalog."""
        catalog = self._catalog_reader.load_catalog()
        return list(catalog._hierarchy_index.keys())

    def list_domains(self) -> List[str]:
        """Get available domains from catalog."""
        catalog = self._catalog_reader.load_catalog()
        return list(catalog._domain_index.keys())

    def list_tags(self) -> List[str]:
        """Get available tags from catalog."""
        catalog = self._catalog_reader.load_catalog()
        return list(catalog._tag_index.keys())

    def refresh_catalog(self):
        """Force refresh of cached catalog."""
        self._catalog_reader.refresh()
        self._matcher = None
        self._intent_parser = None


class CircularDependencyError(Exception):
    """Raised when circular dependency detected."""
    pass
```

---

## CatalogReader (catalog.py)

```python
"""Catalog reader for BLOCKS_REGISTRY."""

import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataikuapi import DSSClient
from .models import BlockCatalog, BlockSummary


class CatalogReader:
    """Reads block catalog from BLOCKS_REGISTRY."""

    # Cache duration in minutes
    CACHE_DURATION_MINUTES = 5

    def __init__(self, client: DSSClient, registry_key: str = "BLOCKS_REGISTRY"):
        """
        Initialize reader.

        Args:
            client: Authenticated DSSClient
            registry_key: Registry project key
        """
        self.client = client
        self.registry_key = registry_key
        self._catalog: Optional[BlockCatalog] = None
        self._cache_time: Optional[datetime] = None

    def load_catalog(self) -> BlockCatalog:
        """
        Load catalog from registry.

        Returns cached catalog if still valid.

        Returns:
            BlockCatalog with all block summaries

        Raises:
            RegistryNotFoundError: If registry project doesn't exist
            CatalogLoadError: If index.json cannot be read
        """
        # Check cache
        if self._is_cache_valid():
            return self._catalog

        # Load fresh
        try:
            registry = self.client.get_project(self.registry_key)
        except Exception as e:
            raise RegistryNotFoundError(
                f"Registry project '{self.registry_key}' not found: {e}"
            )

        try:
            library = registry.get_library()
            index_file = library.get_file("blocks/index.json")
            index_data = json.loads(index_file.read())
        except Exception as e:
            raise CatalogLoadError(f"Cannot read catalog index: {e}")

        # Build catalog
        catalog = BlockCatalog(
            format_version=index_data.get("format_version", "1.0"),
            updated_at=index_data.get("updated_at"),
        )

        for block_data in index_data.get("blocks", []):
            summary = BlockSummary.from_dict(block_data)
            catalog.add_block(summary)

        # Build indexes
        catalog.build_indexes()

        # Cache
        self._catalog = catalog
        self._cache_time = datetime.utcnow()

        return catalog

    def get_block(self, block_id: str, version: str = None) -> Optional[Dict[str, Any]]:
        """
        Get full metadata for a specific block.

        Loads from manifest file for complete details.

        Args:
            block_id: Block identifier
            version: Specific version (optional)

        Returns:
            Full block metadata dict or None
        """
        # First find in catalog to get version if not specified
        catalog = self.load_catalog()
        summary = catalog.get_block(block_id, version)

        if not summary:
            return None

        version = summary.version

        # Load full manifest
        try:
            registry = self.client.get_project(self.registry_key)
            library = registry.get_library()
            manifest_path = f"blocks/manifests/{block_id}_v{version}.json"
            manifest_file = library.get_file(manifest_path)
            return json.loads(manifest_file.read())
        except Exception:
            # Fall back to summary data
            return {
                "block_id": summary.block_id,
                "version": summary.version,
                "type": summary.type,
                "blocked": summary.blocked,
                "hierarchy_level": summary.hierarchy_level,
                "domain": summary.domain,
                "tags": summary.tags,
                "name": summary.name,
                "description": summary.description,
                "inputs": summary.inputs,
                "outputs": summary.outputs,
                "source_project": summary.source_project,
            }

    def get_schema(self, block_id: str, port_name: str, is_input: bool = True) -> Optional[dict]:
        """
        Get schema for a specific block port.

        Args:
            block_id: Block identifier
            port_name: Port name
            is_input: True for input port, False for output

        Returns:
            Schema dict or None
        """
        try:
            registry = self.client.get_project(self.registry_key)
            library = registry.get_library()
            suffix = "input" if is_input else "output"
            schema_path = f"blocks/schemas/{block_id}/{port_name}_{suffix}.json"
            schema_file = library.get_file(schema_path)
            return json.loads(schema_file.read())
        except Exception:
            return None

    def refresh(self):
        """Force refresh of cached catalog."""
        self._catalog = None
        self._cache_time = None

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if self._catalog is None or self._cache_time is None:
            return False

        age = datetime.utcnow() - self._cache_time
        return age < timedelta(minutes=self.CACHE_DURATION_MINUTES)


class RegistryNotFoundError(Exception):
    """Raised when registry project not found."""
    pass


class CatalogLoadError(Exception):
    """Raised when catalog cannot be loaded."""
    pass
```

---

## BlockMatcher (matcher.py)

```python
"""Block matching logic."""

from typing import List, Set
from .models import (
    BlockQuery, BlockCatalog, BlockSummary, MatchResult,
    ExecutingAgentConfig
)


class BlockMatcher:
    """Matches blocks to queries with scoring."""

    def __init__(self, catalog: BlockCatalog, config: ExecutingAgentConfig = None):
        """
        Initialize matcher.

        Args:
            catalog: Loaded block catalog
            config: Agent configuration
        """
        self.catalog = catalog
        self.config = config or ExecutingAgentConfig()

    def match(self, query: BlockQuery) -> List[MatchResult]:
        """
        Find blocks matching query.

        Args:
            query: Block query with filters

        Returns:
            List of MatchResult sorted by score descending
        """
        # Start with all blocks
        candidates = self.catalog.all_blocks()

        # Apply exact filters
        candidates = self._apply_filters(candidates, query)

        # Score remaining candidates
        results = []
        for block in candidates:
            score, details = self._compute_score(block, query)
            if score >= self.config.min_match_score:
                results.append(MatchResult(
                    block_id=block.block_id,
                    version=block.version,
                    score=score,
                    block_summary=self._summary_to_dict(block),
                    match_details=details,
                ))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)

        # Apply limit
        max_results = query.max_results or self.config.default_max_results
        return results[:max_results]

    def _apply_filters(
        self,
        candidates: List[BlockSummary],
        query: BlockQuery
    ) -> List[BlockSummary]:
        """Apply exact match filters."""
        filtered = candidates

        if query.hierarchy_level:
            filtered = [
                b for b in filtered
                if b.hierarchy_level == query.hierarchy_level
            ]

        if query.domain:
            filtered = [b for b in filtered if b.domain == query.domain]

        if query.blocked_only:
            filtered = [b for b in filtered if b.blocked]

        if query.exclude_blocked:
            filtered = [b for b in filtered if not b.blocked]

        if query.min_version:
            filtered = [
                b for b in filtered
                if self._version_gte(b.version, query.min_version)
            ]

        return filtered

    def _compute_score(
        self,
        block: BlockSummary,
        query: BlockQuery
    ) -> tuple:
        """
        Compute match score for a block.

        Returns:
            Tuple of (score, details dict)
        """
        score = 0.0
        max_score = 0.0
        details = {}

        # Tag matching
        if query.tags:
            max_score += 1.0
            block_tags_lower = {t.lower() for t in block.tags}
            query_tags_lower = {t.lower() for t in query.tags}
            matching = block_tags_lower & query_tags_lower
            tag_score = len(matching) / len(query.tags) if query.tags else 0
            score += tag_score
            details["tag_matches"] = list(matching)
            details["tag_score"] = tag_score

        # Capability matching
        if query.capabilities:
            max_score += 1.0
            searchable = (
                block.name.lower() + " " +
                (block.description or "").lower() + " " +
                " ".join(block.tags).lower()
            )
            matches = sum(
                1 for cap in query.capabilities
                if cap.lower() in searchable
            )
            cap_score = matches / len(query.capabilities)
            score += cap_score
            details["capability_score"] = cap_score

        # Input requirements
        if query.input_requirements:
            max_score += 1.0
            matched = 0
            for req in query.input_requirements:
                for inp in block.inputs:
                    if self._port_matches_requirement(inp, req):
                        matched += 1
                        break
            inp_score = matched / len(query.input_requirements)
            score += inp_score
            details["input_score"] = inp_score

        # Output requirements
        if query.output_requirements:
            max_score += 1.0
            matched = 0
            for req in query.output_requirements:
                for out in block.outputs:
                    if self._port_matches_requirement(out, req):
                        matched += 1
                        break
            out_score = matched / len(query.output_requirements)
            score += out_score
            details["output_score"] = out_score

        # Normalize score
        if max_score > 0:
            final_score = score / max_score
        else:
            final_score = 1.0  # No criteria = everything matches

        details["total_score"] = final_score
        return final_score, details

    def _port_matches_requirement(self, port: dict, requirement: dict) -> bool:
        """Check if port matches a requirement."""
        # Name pattern match
        if "name" in requirement:
            if requirement["name"].lower() not in port.get("name", "").lower():
                return False

        # Type match
        if "type" in requirement:
            if port.get("type") != requirement["type"]:
                return False

        return True

    def _version_gte(self, version: str, min_version: str) -> bool:
        """Check if version >= min_version using semver."""
        try:
            v_parts = [int(p) for p in version.split(".")]
            m_parts = [int(p) for p in min_version.split(".")]

            # Pad to same length
            while len(v_parts) < len(m_parts):
                v_parts.append(0)
            while len(m_parts) < len(v_parts):
                m_parts.append(0)

            return v_parts >= m_parts
        except ValueError:
            return True  # Can't parse, assume compatible

    def _summary_to_dict(self, block: BlockSummary) -> dict:
        """Convert BlockSummary to dict."""
        return {
            "block_id": block.block_id,
            "version": block.version,
            "type": block.type,
            "blocked": block.blocked,
            "hierarchy_level": block.hierarchy_level,
            "domain": block.domain,
            "tags": block.tags,
            "name": block.name,
            "description": block.description,
            "inputs": block.inputs,
            "outputs": block.outputs,
            "source_project": block.source_project,
        }

    def find_compatible_blocks(self, source_block: BlockSummary) -> List[BlockSummary]:
        """
        Find blocks that can consume source block's outputs.

        Args:
            source_block: Block to find consumers for

        Returns:
            List of compatible blocks
        """
        compatible = []
        source_output_types = {o.get("type") for o in source_block.outputs}

        for block in self.catalog.all_blocks():
            if block.block_id == source_block.block_id:
                continue

            input_types = {i.get("type") for i in block.inputs}
            if source_output_types & input_types:
                compatible.append(block)

        return compatible
```

---

## DependencyResolver (resolver.py)

```python
"""Dependency resolution for block composition."""

from typing import List, Dict, Set, Optional
from collections import defaultdict
from .models import ResolvedPlan, Wire, WiringHint


class DependencyResolver:
    """Resolves execution order and wiring between blocks."""

    def resolve(
        self,
        blocks: List[dict],
        wiring_hints: List[WiringHint] = None
    ) -> ResolvedPlan:
        """
        Resolve dependencies and generate execution plan.

        Args:
            blocks: List of block summary dicts
            wiring_hints: Explicit wiring from user

        Returns:
            ResolvedPlan with execution order and wiring

        Raises:
            CircularDependencyError: If cycle detected
        """
        # Build graph
        graph = defaultdict(list)  # block_id -> list of dependent block_ids
        in_degree = defaultdict(int)
        block_lookup = {b["block_id"]: b for b in blocks}

        # Initialize nodes
        for block in blocks:
            if block["block_id"] not in in_degree:
                in_degree[block["block_id"]] = 0

        # Infer dependencies from outputs/inputs
        for block_a in blocks:
            for block_b in blocks:
                if block_a["block_id"] == block_b["block_id"]:
                    continue

                if self._can_wire(block_a, block_b):
                    # block_a -> block_b (b depends on a)
                    graph[block_a["block_id"]].append(block_b["block_id"])
                    in_degree[block_b["block_id"]] += 1

        # Apply wiring hints
        if wiring_hints:
            for hint in wiring_hints:
                if hint.target_block not in graph[hint.source_block]:
                    graph[hint.source_block].append(hint.target_block)
                    in_degree[hint.target_block] += 1

        # Detect cycles
        cycle = self._find_cycle(graph, set(in_degree.keys()))
        if cycle:
            raise CircularDependencyError(
                f"Circular dependency detected: {' -> '.join(cycle)}"
            )

        # Topological sort with stages (for parallelization)
        stages = self._topological_sort_stages(graph, in_degree)
        execution_order = [block_id for stage in stages for block_id in stage]

        # Generate wiring
        wiring = self._generate_wiring(execution_order, block_lookup, wiring_hints)

        return ResolvedPlan(
            execution_order=execution_order,
            wiring=wiring,
            stages=stages,
        )

    def _can_wire(self, source: dict, target: dict) -> bool:
        """Check if source outputs can wire to target inputs."""
        source_outputs = {o.get("type", "dataset") for o in source.get("outputs", [])}
        target_inputs = {i.get("type", "dataset") for i in target.get("inputs", [])}
        return bool(source_outputs & target_inputs)

    def _find_cycle(self, graph: Dict[str, List[str]], nodes: Set[str]) -> Optional[List[str]]:
        """Find cycle in graph using DFS."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {n: WHITE for n in nodes}
        parent = {}

        def dfs(node):
            color[node] = GRAY
            for neighbor in graph.get(node, []):
                if neighbor not in color:
                    continue
                if color[neighbor] == GRAY:
                    # Found cycle
                    cycle = [neighbor, node]
                    current = node
                    while parent.get(current) and parent[current] != neighbor:
                        current = parent[current]
                        cycle.append(current)
                    return list(reversed(cycle))
                if color[neighbor] == WHITE:
                    parent[neighbor] = node
                    result = dfs(neighbor)
                    if result:
                        return result
            color[node] = BLACK
            return None

        for node in nodes:
            if color[node] == WHITE:
                cycle = dfs(node)
                if cycle:
                    return cycle

        return None

    def _topological_sort_stages(
        self,
        graph: Dict[str, List[str]],
        in_degree: Dict[str, int]
    ) -> List[List[str]]:
        """
        Topological sort returning stages for parallel execution.

        Returns list of stages, where each stage contains blocks
        that can run in parallel.
        """
        in_degree = dict(in_degree)  # Copy
        remaining = set(in_degree.keys())
        stages = []

        while remaining:
            # Find all nodes with no incoming edges
            ready = [n for n in remaining if in_degree[n] == 0]

            if not ready:
                # Should not happen if no cycles
                break

            stages.append(ready)

            # Remove ready nodes and update degrees
            for node in ready:
                remaining.remove(node)
                for neighbor in graph.get(node, []):
                    in_degree[neighbor] -= 1

        return stages

    def _generate_wiring(
        self,
        execution_order: List[str],
        block_lookup: Dict[str, dict],
        wiring_hints: List[WiringHint] = None
    ) -> List[Wire]:
        """Generate wiring between blocks."""
        wires = []
        hint_lookup = {}

        if wiring_hints:
            for hint in wiring_hints:
                key = (hint.source_block, hint.target_block)
                hint_lookup[key] = hint

        for i, block_id in enumerate(execution_order):
            if i == 0:
                continue  # First block has no upstream

            block = block_lookup[block_id]

            # For each input, find source
            for inp in block.get("inputs", []):
                # Check explicit hint first
                source = self._find_source_from_hints(
                    block_id, inp["name"], hint_lookup
                )

                if not source:
                    # Try to infer from previous blocks
                    source = self._infer_source(
                        execution_order[:i],
                        block_lookup,
                        inp
                    )

                if source:
                    wire = Wire(
                        source_block=source["block_id"],
                        source_port=source["port_name"],
                        target_block=block_id,
                        target_port=inp["name"],
                        dataset_name=f"{source['block_id']}_{source['port_name']}",
                    )
                    wires.append(wire)

        return wires

    def _find_source_from_hints(
        self,
        target_block: str,
        target_port: str,
        hint_lookup: dict
    ) -> Optional[dict]:
        """Find source from explicit wiring hints."""
        for (src_block, tgt_block), hint in hint_lookup.items():
            if tgt_block == target_block and hint.target_port == target_port:
                return {
                    "block_id": src_block,
                    "port_name": hint.source_port,
                }
        return None

    def _infer_source(
        self,
        previous_blocks: List[str],
        block_lookup: Dict[str, dict],
        target_input: dict
    ) -> Optional[dict]:
        """Infer source output for a target input."""
        target_type = target_input.get("type", "dataset")

        # Search previous blocks in reverse order (prefer closer blocks)
        for block_id in reversed(previous_blocks):
            block = block_lookup[block_id]
            for out in block.get("outputs", []):
                if out.get("type", "dataset") == target_type:
                    return {
                        "block_id": block_id,
                        "port_name": out["name"],
                    }

        return None


class CircularDependencyError(Exception):
    """Raised when circular dependency detected in blocks."""
    pass
```

---

## ConfigGenerator (generator.py)

```python
"""Configuration generator for block compositions."""

from typing import Dict, List, Optional
from .models import (
    ResolvedPlan,
    CompositionConfig,
    ProjectConfig,
    BlockReferenceConfig,
    DatasetConfig,
    RecipeConfig,
    ExtensionConfig,
    MatchResult,
    ExecutingAgentConfig,
)


class ConfigGenerator:
    """Generates IaC configuration from resolved plan."""

    def __init__(self, config: ExecutingAgentConfig = None):
        """
        Initialize generator.

        Args:
            config: Agent configuration
        """
        self.config = config or ExecutingAgentConfig()

    def generate(
        self,
        plan: ResolvedPlan,
        target_project_key: str,
        external_inputs: Dict[str, str],
        external_outputs: Dict[str, str],
        extensions: List[ExtensionConfig],
        blocks_metadata: Dict[str, MatchResult]
    ) -> CompositionConfig:
        """
        Generate complete IaC configuration.

        Args:
            plan: Resolved execution plan
            target_project_key: Target project key
            external_inputs: External input mappings
            external_outputs: External output mappings
            extensions: Block extensions
            blocks_metadata: Block metadata keyed by block_id

        Returns:
            CompositionConfig ready for serialization
        """
        config = CompositionConfig(version="1.0")

        # Generate project config
        config.project = self._generate_project_config(
            target_project_key, plan, blocks_metadata
        )

        # Generate block references
        config.blocks = self._generate_block_refs(
            plan, external_inputs, external_outputs, extensions, blocks_metadata
        )

        # Generate placeholder datasets
        if self.config.generate_placeholders:
            config.datasets = self._generate_placeholder_datasets(
                config.blocks, external_inputs
            )

        return config

    def _generate_project_config(
        self,
        project_key: str,
        plan: ResolvedPlan,
        blocks_metadata: Dict[str, MatchResult]
    ) -> ProjectConfig:
        """Generate project configuration."""
        # Generate name from blocks
        if plan.execution_order:
            first_block = blocks_metadata.get(plan.execution_order[0])
            if first_block:
                name = f"Composed: {first_block.block_summary.get('name', plan.execution_order[0])}"
            else:
                name = f"Composed Project"
        else:
            name = "Composed Project"

        return ProjectConfig(
            key=project_key,
            name=name,
            description=f"Composed from {len(plan.execution_order)} blocks",
        )

    def _generate_block_refs(
        self,
        plan: ResolvedPlan,
        external_inputs: Dict[str, str],
        external_outputs: Dict[str, str],
        extensions: List[ExtensionConfig],
        blocks_metadata: Dict[str, MatchResult]
    ) -> List[BlockReferenceConfig]:
        """Generate block reference configurations."""
        refs = []
        extension_lookup = {e.block_id: e for e in extensions}

        # Build wire lookup for fast access
        wire_lookup = {}  # (target_block, target_port) -> Wire
        for wire in plan.wiring:
            key = (wire.target_block, wire.target_port)
            wire_lookup[key] = wire

        for i, block_id in enumerate(plan.execution_order):
            match = blocks_metadata.get(block_id)
            if not match:
                continue

            block = match.block_summary

            ref_config = BlockReferenceConfig(
                ref=f"BLOCKS_REGISTRY/{block_id}@{match.version}",
                instance_name=self._generate_instance_name(block_id, i),
                zone_name=self._generate_zone_name(block_id),
            )

            # Generate input mappings
            for inp in block.get("inputs", []):
                port_name = inp["name"]
                wire_key = (block_id, port_name)

                if wire_key in wire_lookup:
                    # Wired from previous block
                    wire = wire_lookup[wire_key]
                    ref_config.inputs[port_name] = wire.dataset_name
                elif port_name in external_inputs:
                    # External input
                    ref_config.inputs[port_name] = external_inputs[port_name]
                else:
                    # Placeholder
                    ref_config.inputs[port_name] = f"INPUT_{port_name}"

            # Generate output mappings
            for out in block.get("outputs", []):
                port_name = out["name"]
                if port_name in external_outputs:
                    ref_config.outputs[port_name] = external_outputs[port_name]
                else:
                    ref_config.outputs[port_name] = f"{block_id}_{port_name}"

            # Add extensions if any
            if block_id in extension_lookup:
                ext = extension_lookup[block_id]
                extends = []

                for ro in ext.recipe_overrides:
                    extends.append({
                        "recipe": ro.recipe,
                        "override_with": ro.override_with,
                    })

                for co in ext.class_overrides:
                    extends.append({
                        "recipe": co.recipe,
                        "use_class": co.use_class,
                        "class_config": co.class_config,
                    })

                if extends:
                    ref_config.extends = extends

            refs.append(ref_config)

        return refs

    def _generate_placeholder_datasets(
        self,
        block_refs: List[BlockReferenceConfig],
        external_inputs: Dict[str, str]
    ) -> List[DatasetConfig]:
        """Generate placeholder datasets for unmapped inputs."""
        placeholders = []
        seen = set(external_inputs.values())

        for ref in block_refs:
            for port_name, dataset_name in ref.inputs.items():
                if dataset_name.startswith("INPUT_") and dataset_name not in seen:
                    placeholders.append(DatasetConfig(
                        name=dataset_name,
                        type="TODO_SPECIFY_TYPE",
                        comment=f"Placeholder for '{port_name}' - configure connection and type",
                    ))
                    seen.add(dataset_name)

        return placeholders

    def _generate_instance_name(self, block_id: str, index: int) -> str:
        """Generate instance name for block."""
        return f"{block_id.lower()}_instance"

    def _generate_zone_name(self, block_id: str) -> str:
        """Generate zone name for block."""
        return f"{block_id.lower()}_zone"

    def to_yaml(self, config: CompositionConfig) -> str:
        """Serialize configuration to YAML."""
        return config.to_yaml()

    def validate_config(self, config: CompositionConfig) -> List[str]:
        """
        Validate generated configuration.

        Returns list of validation errors (empty if valid).
        """
        errors = []

        if not config.project:
            errors.append("Missing project configuration")

        if not config.blocks:
            errors.append("No blocks in configuration")

        # Check for unmapped required inputs
        for block in config.blocks:
            for port, dataset in block.inputs.items():
                if dataset.startswith("INPUT_"):
                    errors.append(
                        f"Block '{block.instance_name}' has unmapped input '{port}'"
                    )

        return errors
```

---

## IntentParser (intent.py)

```python
"""Natural language intent parsing."""

from typing import List, Set, Optional
from .models import BlockQuery, BlockCatalog


class IntentParser:
    """Parses natural language intent to BlockQuery."""

    # Stopwords to remove
    STOPWORDS = {
        "i", "need", "want", "get", "find", "looking", "for", "the", "a", "an",
        "with", "that", "can", "do", "does", "have", "has", "is", "are", "be",
        "to", "and", "or", "in", "on", "at", "by", "from", "all", "some", "any",
        "me", "my", "we", "our", "please", "help", "show",
    }

    # Hierarchy keyword mappings
    HIERARCHY_KEYWORDS = {
        "sensor": "sensor",
        "sensors": "sensor",
        "signal": "sensor",
        "raw": "sensor",
        "equipment": "equipment",
        "machine": "equipment",
        "device": "equipment",
        "asset": "equipment",
        "process": "process",
        "unit": "process",
        "system": "process",
        "plant": "plant",
        "facility": "plant",
        "site": "plant",
        "business": "business",
        "enterprise": "business",
        "portfolio": "business",
    }

    # Domain keyword mappings
    DOMAIN_KEYWORDS = {
        "compressor": "rotating_equipment",
        "pump": "rotating_equipment",
        "turbine": "rotating_equipment",
        "motor": "rotating_equipment",
        "fan": "rotating_equipment",
        "bearing": "rotating_equipment",
        "vibration": "rotating_equipment",
        "rotating": "rotating_equipment",
        "control": "process_control",
        "controller": "process_control",
        "pid": "process_control",
        "valve": "process_control",
        "maintenance": "predictive_maintenance",
        "failure": "predictive_maintenance",
        "rul": "predictive_maintenance",
        "health": "predictive_maintenance",
        "predictive": "predictive_maintenance",
        "quality": "quality_control",
        "defect": "quality_control",
        "energy": "energy_optimization",
        "efficiency": "energy_optimization",
    }

    # Capability action verbs
    CAPABILITY_VERBS = {
        "feature", "engineer", "engineering", "extract",
        "anomaly", "detect", "detection", "identify",
        "predict", "prediction", "forecast",
        "classify", "classification", "categorize",
        "monitor", "monitoring", "track",
        "alert", "alerting", "notify",
        "score", "scoring", "rank",
        "clean", "cleaning", "prepare", "preparation",
        "transform", "transformation",
    }

    def __init__(self, catalog: BlockCatalog = None):
        """
        Initialize parser.

        Args:
            catalog: Block catalog for enhanced parsing (optional)
        """
        self.catalog = catalog

        # Build additional keywords from catalog if available
        self._catalog_tags: Set[str] = set()
        if catalog:
            for block in catalog.all_blocks():
                self._catalog_tags.update(t.lower() for t in block.tags)

    def parse(self, text: str) -> BlockQuery:
        """
        Parse natural language to BlockQuery.

        Args:
            text: Natural language intent

        Returns:
            BlockQuery with extracted parameters
        """
        # Tokenize and normalize
        tokens = self._tokenize(text)

        # Extract components
        hierarchy = self._extract_hierarchy(tokens)
        domain = self._extract_domain(tokens)
        capabilities = self._extract_capabilities(tokens)
        tags = self._extract_tags(tokens)

        # Check for protection modifiers
        blocked_only = self._check_blocked_only(text)
        exclude_blocked = self._check_exclude_blocked(text)

        return BlockQuery(
            hierarchy_level=hierarchy,
            domain=domain,
            capabilities=capabilities,
            tags=tags,
            blocked_only=blocked_only,
            exclude_blocked=exclude_blocked,
        )

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize and normalize text."""
        # Lowercase
        text = text.lower()

        # Remove punctuation
        for char in ".,!?;:'\"()[]{}":
            text = text.replace(char, " ")

        # Split and filter
        tokens = text.split()
        tokens = [t for t in tokens if t not in self.STOPWORDS]
        tokens = [t for t in tokens if len(t) > 1]

        return tokens

    def _extract_hierarchy(self, tokens: List[str]) -> Optional[str]:
        """Extract hierarchy level from tokens."""
        for token in tokens:
            if token in self.HIERARCHY_KEYWORDS:
                return self.HIERARCHY_KEYWORDS[token]
        return None

    def _extract_domain(self, tokens: List[str]) -> Optional[str]:
        """Extract domain from tokens."""
        for token in tokens:
            if token in self.DOMAIN_KEYWORDS:
                return self.DOMAIN_KEYWORDS[token]
        return None

    def _extract_capabilities(self, tokens: List[str]) -> List[str]:
        """Extract capability keywords from tokens."""
        capabilities = []
        for token in tokens:
            if token in self.CAPABILITY_VERBS:
                capabilities.append(token)
        return capabilities

    def _extract_tags(self, tokens: List[str]) -> List[str]:
        """Extract potential tags from tokens."""
        tags = []

        # Check against catalog tags
        for token in tokens:
            if token in self._catalog_tags:
                tags.append(token)

        # Also include meaningful tokens not matched elsewhere
        for token in tokens:
            if (
                len(token) > 3 and
                token not in self.HIERARCHY_KEYWORDS and
                token not in self.DOMAIN_KEYWORDS and
                token not in self.CAPABILITY_VERBS and
                token not in tags
            ):
                tags.append(token)

        return tags[:5]  # Limit to 5 tags

    def _check_blocked_only(self, text: str) -> bool:
        """Check if query requests blocked/protected blocks only."""
        indicators = ["blocked", "protected", "published", "stable", "official"]
        text_lower = text.lower()
        return any(ind in text_lower for ind in indicators)

    def _check_exclude_blocked(self, text: str) -> bool:
        """Check if query excludes blocked blocks."""
        indicators = ["not blocked", "unblocked", "editable", "modifiable"]
        text_lower = text.lower()
        return any(ind in text_lower for ind in indicators)

    def suggest_refinements(
        self,
        text: str,
        results: List[any]  # MatchResult
    ) -> List[str]:
        """
        Suggest query refinements if results are poor.

        Args:
            text: Original intent text
            results: Match results (empty or low score)

        Returns:
            List of suggested refined queries
        """
        suggestions = []

        if not results:
            # No results - suggest relaxing
            suggestions.append("Try removing specific keywords")
            suggestions.append("Try searching by domain only (e.g., 'rotating equipment blocks')")

            if self.catalog:
                # Suggest available domains
                domains = list(self.catalog._domain_index.keys())[:3]
                if domains:
                    suggestions.append(f"Available domains: {', '.join(domains)}")

        elif results and results[0].score < 0.5:
            # Low confidence - suggest being more specific
            suggestions.append("Try adding more specific capability keywords")
            suggestions.append("Try specifying hierarchy level (sensor/equipment/process/plant)")

        return suggestions
```
