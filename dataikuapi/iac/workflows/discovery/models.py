"""Data models for Discovery Agent."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import re


@dataclass
class BlockPort:
    """
    Represents an input or output port of a block.

    A port defines a connection point for data flowing into or out of a block.
    Each port has a name, type, and optionally a description and schema.

    Attributes:
        name: Port name (e.g., "INPUT_DATA", "OUTPUT_FEATURES")
        type: Port type ("dataset", "model", or "folder")
        required: Whether this input is required (for inputs only)
        description: Human-readable description of the port
        schema_ref: Optional path to schema file in registry

    Example:
        >>> port = BlockPort(
        >>>     name="RAW_DATA",
        >>>     type="dataset",
        >>>     required=True,
        >>>     description="Raw sensor readings"
        >>> )
    """

    name: str
    type: str  # "dataset" | "model" | "folder"
    required: bool = True
    description: str = ""
    schema_ref: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize BlockPort to dictionary.

        Returns:
            Dict representation of the port
        """
        return {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlockPort":
        """
        Deserialize BlockPort from dictionary.

        Args:
            data: Dictionary containing port data

        Returns:
            BlockPort instance
        """
        return cls(
            name=data["name"],
            type=data["type"],
            required=data.get("required", True),
            description=data.get("description", ""),
            schema_ref=data.get("schema_ref"),
        )


@dataclass
class BlockContents:
    """
    Represents the internal contents of a block.

    Contains lists of datasets, recipes, and models that are internal
    to the block (not exposed as inputs/outputs).

    Attributes:
        datasets: List of internal dataset names
        recipes: List of internal recipe names
        models: List of internal saved model IDs

    Example:
        >>> contents = BlockContents(
        >>>     datasets=["SMOOTHED_SIGNAL", "FFT_RESULTS"],
        >>>     recipes=["smooth_signal", "compute_fft"],
        >>>     models=[]
        >>> )
    """

    datasets: List[str] = field(default_factory=list)
    recipes: List[str] = field(default_factory=list)
    models: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize BlockContents to dictionary.

        Returns:
            Dict representation of contents
        """
        return {
            "datasets": self.datasets,
            "recipes": self.recipes,
            "models": self.models,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlockContents":
        """
        Deserialize BlockContents from dictionary.

        Args:
            data: Dictionary containing contents data

        Returns:
            BlockContents instance
        """
        return cls(
            datasets=data.get("datasets", []),
            recipes=data.get("recipes", []),
            models=data.get("models", []),
        )


@dataclass
class BlockMetadata:
    """
    Complete metadata for a reusable block.

    This class represents all the information about a block that is
    stored in the BLOCKS_REGISTRY and used for discovery, validation,
    and instantiation.

    Attributes:
        block_id: Unique identifier (UPPERCASE_WITH_UNDERSCORES)
        version: Semantic version (X.Y.Z)
        type: Block type ("zone" or "solution")
        blocked: Whether block is protected/published
        name: Human-readable name
        description: Detailed description
        hierarchy_level: ISA-95 level (sensor/equipment/process/plant/business)
        domain: Business/technical domain
        tags: Searchable tags
        source_project: Origin project key
        source_zone: Origin zone name
        inputs: List of input ports
        outputs: List of output ports
        contains: Internal datasets/recipes/models
        dependencies: External dependencies
        bundle_ref: Path to bundle snapshot
        created_at: Creation timestamp
        updated_at: Last update timestamp
        created_by: Creator user

    Example:
        >>> metadata = BlockMetadata(
        >>>     block_id="FEATURE_ENGINEERING",
        >>>     version="1.2.0",
        >>>     type="zone",
        >>>     name="Feature Engineering Block",
        >>>     source_project="ANALYTICS_PROJECT",
        >>>     inputs=[BlockPort(name="RAW_DATA", type="dataset")],
        >>>     outputs=[BlockPort(name="FEATURES", type="dataset")]
        >>> )
    """

    # Required fields
    block_id: str
    version: str
    type: str  # "zone" | "solution"
    source_project: str

    # Optional fields with defaults
    blocked: bool = False
    name: str = ""
    description: str = ""
    hierarchy_level: str = ""
    domain: str = ""
    tags: List[str] = field(default_factory=list)
    source_zone: str = ""

    # Relationships
    inputs: List[BlockPort] = field(default_factory=list)
    outputs: List[BlockPort] = field(default_factory=list)
    contains: BlockContents = field(default_factory=BlockContents)

    # Dependencies
    dependencies: Dict[str, Any] = field(default_factory=dict)

    # Artifacts
    bundle_ref: Optional[str] = None

    # Metadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: str = ""

    def validate(self) -> List[str]:
        """
        Validate block metadata.

        Checks:
        - Block ID format (UPPERCASE_WITH_UNDERSCORES)
        - Version format (semantic versioning X.Y.Z)
        - At least one input defined
        - At least one output defined
        - Type is valid ("zone" or "solution")

        Returns:
            List of error messages (empty if valid)

        Example:
            >>> metadata = BlockMetadata(...)
            >>> errors = metadata.validate()
            >>> if errors:
            >>>     print(f"Validation failed: {errors}")
        """
        errors = []

        # Validate block_id format
        if not self.block_id:
            errors.append("block_id is required")
        elif not re.match(r"^[A-Z][A-Z0-9_]*$", self.block_id):
            errors.append(
                f"block_id '{self.block_id}' must be UPPERCASE_WITH_UNDERSCORES"
            )

        # Validate version format (semantic versioning)
        if not self.version:
            errors.append("version is required")
        elif not re.match(r"^\d+\.\d+\.\d+$", self.version):
            errors.append(f"version '{self.version}' must be semantic (X.Y.Z format)")

        # Validate type
        if self.type not in ["zone", "solution"]:
            errors.append(f"type must be 'zone' or 'solution', got '{self.type}'")

        # Validate inputs (must have at least one)
        if not self.inputs:
            errors.append("block must have at least one input")

        # Validate outputs (must have at least one)
        if not self.outputs:
            errors.append("block must have at least one output")

        # Validate source_project
        if not self.source_project:
            errors.append("source_project is required")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize BlockMetadata to dictionary.

        Returns:
            Dict representation suitable for JSON serialization
        """
        return {
            "block_id": self.block_id,
            "version": self.version,
            "type": self.type,
            "blocked": self.blocked,
            "name": self.name,
            "description": self.description,
            "hierarchy_level": self.hierarchy_level,
            "domain": self.domain,
            "tags": self.tags,
            "source_project": self.source_project,
            "source_zone": self.source_zone,
            "inputs": [inp.to_dict() for inp in self.inputs],
            "outputs": [out.to_dict() for out in self.outputs],
            "contains": self.contains.to_dict(),
            "dependencies": self.dependencies,
            "bundle_ref": self.bundle_ref,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlockMetadata":
        """
        Deserialize BlockMetadata from dictionary.

        Args:
            data: Dictionary containing block metadata

        Returns:
            BlockMetadata instance
        """
        return cls(
            block_id=data["block_id"],
            version=data["version"],
            type=data["type"],
            blocked=data.get("blocked", False),
            name=data.get("name", ""),
            description=data.get("description", ""),
            hierarchy_level=data.get("hierarchy_level", ""),
            domain=data.get("domain", ""),
            tags=data.get("tags", []),
            source_project=data["source_project"],
            source_zone=data.get("source_zone", ""),
            inputs=[BlockPort.from_dict(inp) for inp in data.get("inputs", [])],
            outputs=[BlockPort.from_dict(out) for out in data.get("outputs", [])],
            contains=BlockContents.from_dict(data.get("contains", {})),
            dependencies=data.get("dependencies", {}),
            bundle_ref=data.get("bundle_ref"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            created_by=data.get("created_by", ""),
        )


@dataclass
class BlockSummary:
    """
    Lightweight summary of a block for catalog listings.

    This is a subset of BlockMetadata optimized for catalog index files
    and search results. It contains just enough information for users
    to browse and select blocks without loading full metadata.

    Attributes:
        block_id: Block identifier
        version: Block version
        type: Block type
        blocked: Protection status
        name: Block name
        description: Brief description (truncated if needed)
        hierarchy_level: Hierarchy classification
        domain: Domain classification
        tags: Search tags
        inputs: Simplified input port info
        outputs: Simplified output port info
        manifest_path: Path to full manifest in registry

    Example:
        >>> summary = BlockSummary.from_metadata(full_metadata)
        >>> print(f"{summary.block_id} v{summary.version}")
    """

    block_id: str
    version: str
    type: str
    name: str = ""
    description: str = ""
    hierarchy_level: str = ""
    domain: str = ""
    tags: List[str] = field(default_factory=list)
    blocked: bool = False
    inputs: List[Dict[str, Any]] = field(default_factory=list)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    manifest_path: str = ""

    @classmethod
    def from_metadata(cls, metadata: BlockMetadata) -> "BlockSummary":
        """
        Create BlockSummary from full BlockMetadata.

        Args:
            metadata: Full block metadata

        Returns:
            BlockSummary with essential information
        """
        # Truncate description for summary
        description = metadata.description
        if len(description) > 200:
            description = description[:197] + "..."

        # Simplify port information
        inputs = [
            {"name": inp.name, "type": inp.type, "required": inp.required}
            for inp in metadata.inputs
        ]
        outputs = [{"name": out.name, "type": out.type} for out in metadata.outputs]

        return cls(
            block_id=metadata.block_id,
            version=metadata.version,
            type=metadata.type,
            name=metadata.name,
            description=description,
            hierarchy_level=metadata.hierarchy_level,
            domain=metadata.domain,
            tags=metadata.tags,
            blocked=metadata.blocked,
            inputs=inputs,
            outputs=outputs,
            manifest_path=f"manifests/{metadata.block_id}_v{metadata.version}.json",
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize BlockSummary to dictionary.

        Returns:
            Dict representation
        """
        return {
            "block_id": self.block_id,
            "version": self.version,
            "type": self.type,
            "blocked": self.blocked,
            "name": self.name,
            "description": self.description,
            "hierarchy_level": self.hierarchy_level,
            "domain": self.domain,
            "tags": self.tags,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "manifest_path": self.manifest_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlockSummary":
        """
        Deserialize BlockSummary from dictionary.

        Args:
            data: Dictionary containing summary data

        Returns:
            BlockSummary instance
        """
        return cls(
            block_id=data["block_id"],
            version=data["version"],
            type=data["type"],
            blocked=data.get("blocked", False),
            name=data.get("name", ""),
            description=data.get("description", ""),
            hierarchy_level=data.get("hierarchy_level", ""),
            domain=data.get("domain", ""),
            tags=data.get("tags", []),
            inputs=data.get("inputs", []),
            outputs=data.get("outputs", []),
            manifest_path=data.get("manifest_path", ""),
        )


@dataclass
class LibraryReference:
    """
    Reference to a file or module in the project library.
    """

    name: str
    type: str  # "python", "R", "resource"
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LibraryReference":
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            type=data["type"],
            description=data.get("description", ""),
        )


@dataclass
class NotebookReference:
    """
    Reference to a Jupyter or SQL notebook.
    """

    name: str
    type: str  # "jupyter", "sql"
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotebookReference":
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            type=data["type"],
            description=data.get("description", ""),
            tags=data.get("tags", []),
        )


@dataclass
class DatasetDetail:
    """
    Rich metadata for a dataset.
    """

    name: str
    type: str
    connection: str
    format_type: str
    schema_summary: Dict[str, Any]  # e.g. {"columns": 10, "sample": ["id", "val"]}
    partitioning: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    description: str = ""
    estimated_size: Optional[str] = None
    last_built: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "connection": self.connection,
            "format_type": self.format_type,
            "schema_summary": self.schema_summary,
            "partitioning": self.partitioning,
            "tags": self.tags,
            "description": self.description,
            "estimated_size": self.estimated_size,
            "last_built": self.last_built,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetDetail":
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            type=data["type"],
            connection=data["connection"],
            format_type=data["format_type"],
            schema_summary=data["schema_summary"],
            partitioning=data.get("partitioning"),
            tags=data.get("tags", []),
            description=data.get("description", ""),
            estimated_size=data.get("estimated_size"),
            last_built=data.get("last_built"),
        )


@dataclass
class RecipeDetail:
    """
    Rich metadata for a recipe.
    """

    name: str
    type: str
    engine: str
    inputs: List[str]
    outputs: List[str]
    description: str = ""
    tags: List[str] = field(default_factory=list)
    code_snippet: Optional[str] = None
    config_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "engine": self.engine,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "description": self.description,
            "tags": self.tags,
            "code_snippet": self.code_snippet,
            "config_summary": self.config_summary,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecipeDetail":
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            type=data["type"],
            engine=data["engine"],
            inputs=data["inputs"],
            outputs=data["outputs"],
            description=data.get("description", ""),
            tags=data.get("tags", []),
            code_snippet=data.get("code_snippet"),
            config_summary=data.get("config_summary", {}),
        )


@dataclass
class EnhancedBlockMetadata(BlockMetadata):
    """
    Extended metadata with rich component details.

    Extends BlockMetadata with detailed information about datasets, recipes,
    library files, and notebooks contained within a block. This provides
    the foundation for generating rich documentation and understanding
    block complexity.

    Attributes:
        dataset_details: List of detailed dataset metadata
        recipe_details: List of detailed recipe metadata
        library_refs: List of library file references
        notebook_refs: List of notebook references
        flow_graph: Optional flow graph structure
        estimated_complexity: Complexity estimate ("simple", "moderate", "complex")
        estimated_size: Size estimate (e.g., "2.5GB")

    Example:
        >>> enhanced = EnhancedBlockMetadata(
        >>>     block_id="FEATURE_ENG",
        >>>     version="1.0.0",
        >>>     type="zone",
        >>>     source_project="PROJ",
        >>>     dataset_details=[
        >>>         DatasetDetail(name="ds1", type="Snowflake", ...)
        >>>     ]
        >>> )
    """

    dataset_details: List[DatasetDetail] = field(default_factory=list)
    recipe_details: List[RecipeDetail] = field(default_factory=list)
    library_refs: List[LibraryReference] = field(default_factory=list)
    notebook_refs: List[NotebookReference] = field(default_factory=list)
    flow_graph: Optional[Dict[str, Any]] = None
    estimated_complexity: str = ""  # "simple", "moderate", "complex"
    estimated_size: str = ""  # e.g., "2.5GB"

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize EnhancedBlockMetadata to dictionary.

        Performs deep serialization by converting all nested objects
        (DatasetDetail, RecipeDetail, etc.) to dictionaries.

        Returns:
            Dict representation suitable for JSON serialization
        """
        # Get base class fields
        base_dict = super().to_dict()

        # Add enhanced fields with deep serialization
        base_dict.update(
            {
                "dataset_details": [ds.to_dict() for ds in self.dataset_details],
                "recipe_details": [rc.to_dict() for rc in self.recipe_details],
                "library_refs": [lib.to_dict() for lib in self.library_refs],
                "notebook_refs": [nb.to_dict() for nb in self.notebook_refs],
                "flow_graph": self.flow_graph,
                "estimated_complexity": self.estimated_complexity,
                "estimated_size": self.estimated_size,
            }
        )

        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnhancedBlockMetadata":
        """
        Deserialize EnhancedBlockMetadata from dictionary.

        Performs deep deserialization by reconstructing nested objects
        from dictionaries.

        Args:
            data: Dictionary containing enhanced block metadata

        Returns:
            EnhancedBlockMetadata instance
        """
        # Extract base class fields
        base_fields = {
            "block_id": data["block_id"],
            "version": data["version"],
            "type": data["type"],
            "source_project": data["source_project"],
            "blocked": data.get("blocked", False),
            "name": data.get("name", ""),
            "description": data.get("description", ""),
            "hierarchy_level": data.get("hierarchy_level", ""),
            "domain": data.get("domain", ""),
            "tags": data.get("tags", []),
            "source_zone": data.get("source_zone", ""),
            "inputs": [BlockPort.from_dict(inp) for inp in data.get("inputs", [])],
            "outputs": [BlockPort.from_dict(out) for out in data.get("outputs", [])],
            "contains": BlockContents.from_dict(data.get("contains", {})),
            "dependencies": data.get("dependencies", {}),
            "bundle_ref": data.get("bundle_ref"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "created_by": data.get("created_by", ""),
        }

        # Extract enhanced fields with deep deserialization
        enhanced_fields = {
            "dataset_details": [
                DatasetDetail.from_dict(ds) for ds in data.get("dataset_details", [])
            ],
            "recipe_details": [
                RecipeDetail.from_dict(rc) for rc in data.get("recipe_details", [])
            ],
            "library_refs": [
                LibraryReference.from_dict(lib) for lib in data.get("library_refs", [])
            ],
            "notebook_refs": [
                NotebookReference.from_dict(nb) for nb in data.get("notebook_refs", [])
            ],
            "flow_graph": data.get("flow_graph"),
            "estimated_complexity": data.get("estimated_complexity", ""),
            "estimated_size": data.get("estimated_size", ""),
        }

        # Combine and create instance
        return cls(**base_fields, **enhanced_fields)
