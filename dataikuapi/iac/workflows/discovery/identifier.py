"""Block Identifier for Discovery Agent.

This module implements the BlockIdentifier class which analyzes zones to
determine if they are valid reusable blocks and extracts their metadata.
"""

from typing import Dict, List, Any, Optional
import re
from dataikuapi.iac.workflows.discovery.crawler import FlowCrawler
from dataikuapi.iac.workflows.discovery.models import (
    BlockMetadata,
    BlockPort,
    BlockContents,
    DatasetDetail,
)


class BlockIdentifier:
    """
    Identifies valid blocks from Dataiku zones and extracts metadata.

    The BlockIdentifier uses zone boundary analysis from FlowCrawler to
    determine if a zone qualifies as a reusable block (must have inputs
    and outputs) and extracts complete block metadata.

    Attributes:
        crawler: FlowCrawler instance for zone analysis

    Example:
        >>> client = DSSClient(host, api_key)
        >>> crawler = FlowCrawler(client)
        >>> identifier = BlockIdentifier(crawler)
        >>> blocks = identifier.identify_blocks("MY_PROJECT")
        >>> for block in blocks:
        >>>     print(f"{block.block_id} v{block.version}")
    """

    def __init__(self, crawler: FlowCrawler):
        """
        Initialize BlockIdentifier with FlowCrawler.

        Args:
            crawler: FlowCrawler instance for zone traversal
        """
        self.crawler = crawler

    def identify_blocks(self, project_key: str) -> List[BlockMetadata]:
        """
        Identify all valid blocks in a project.

        Implements Algorithm 2 from the specification:
        - Get all zones from project
        - Analyze each zone boundary
        - Filter to valid blocks (inputs + outputs)
        - Extract complete metadata

        Args:
            project_key: Project identifier

        Returns:
            List of BlockMetadata objects for valid blocks

        Example:
            >>> blocks = identifier.identify_blocks("MY_PROJECT")
            >>> print(f"Found {len(blocks)} blocks")
        """
        blocks = []

        # Get all zones in project
        zone_names = self.crawler.list_zones(project_key)

        for zone_name in zone_names:
            # Skip default zones without explicit names
            if self.should_skip_zone(zone_name):
                continue

            # Analyze zone boundary
            boundary = self.crawler.analyze_zone_boundary(project_key, zone_name)

            # Check if zone is a valid block
            if self.is_valid_block(boundary):
                # Extract complete block metadata
                metadata = self.extract_block_metadata(project_key, zone_name, boundary)
                blocks.append(metadata)

        return blocks

    def is_valid_block(self, boundary: Dict[str, Any]) -> bool:
        """
        Determine if a zone boundary represents a valid block.

        A valid block must have:
        - At least one input
        - At least one output
        - Valid containment (all recipe I/O within boundary)

        Args:
            boundary: Zone boundary dict from FlowCrawler.analyze_zone_boundary()

        Returns:
            True if zone is a valid block, False otherwise

        Example:
            >>> boundary = crawler.analyze_zone_boundary("PROJECT", "zone1")
            >>> if identifier.is_valid_block(boundary):
            >>>     print("Valid block!")
        """
        # Must pass containment validation
        if not boundary.get("is_valid", False):
            return False

        # Must have at least one input
        inputs = boundary.get("inputs", [])
        if not inputs:
            return False

        # Must have at least one output
        outputs = boundary.get("outputs", [])
        if not outputs:
            return False

        return True

    def should_skip_zone(self, zone_name: str) -> bool:
        """
        Determine if a zone should be skipped during block identification.

        Skips:
        - Empty zone names
        - Default zones (named "default" or "Default")

        Args:
            zone_name: Zone name to check

        Returns:
            True if zone should be skipped, False otherwise
        """
        if not zone_name or zone_name.strip() == "":
            return True

        if zone_name.lower() == "default":
            return True

        return False

    def extract_block_metadata(
        self, project_key: str, zone_name: str, boundary: Dict[str, Any]
    ) -> BlockMetadata:
        """
        Extract complete block metadata from a zone.

        Args:
            project_key: Project identifier
            zone_name: Zone name
            boundary: Zone boundary analysis

        Returns:
            BlockMetadata object with complete block information

        Example:
            >>> metadata = identifier.extract_block_metadata("PROJECT", "zone1", boundary)
            >>> print(metadata.block_id)
        """
        # Generate block ID from zone name
        block_id = self.generate_block_id(zone_name)

        # Get zone items
        zone_items = self.crawler.get_zone_items(project_key, zone_name)

        # Create input/output ports
        inputs = self.create_block_ports(boundary["inputs"], "dataset")
        outputs = self.create_block_ports(boundary["outputs"], "dataset")

        # Extract block contents (internals + all recipes)
        contents = self.extract_block_contents(boundary, zone_items)

        # Get zone metadata (tags, etc.)
        zone_metadata = self._get_zone_metadata(project_key, zone_name)

        # Extract classification metadata
        hierarchy_level = self.classify_hierarchy(zone_metadata)
        domain = self.extract_domain(zone_metadata)
        tags = self.extract_tags(zone_metadata)

        # Generate version
        version = self.generate_version(block_id)

        # Create BlockMetadata
        metadata = BlockMetadata(
            block_id=block_id,
            version=version,
            type="zone",
            source_project=project_key,
            source_zone=zone_name,
            name=self._format_block_name(zone_name),
            description=f"Block extracted from zone '{zone_name}'",
            hierarchy_level=hierarchy_level,
            domain=domain,
            tags=tags,
            inputs=inputs,
            outputs=outputs,
            contains=contents,
        )

        return metadata

    def generate_block_id(self, zone_name: str) -> str:
        """
        Generate a block ID from zone name.

        Converts zone name to UPPERCASE_WITH_UNDERSCORES format.

        Args:
            zone_name: Zone name

        Returns:
            Block ID in UPPERCASE_WITH_UNDERSCORES format

        Example:
            >>> identifier.generate_block_id("Feature Engineering")
            'FEATURE_ENGINEERING'
            >>> identifier.generate_block_id("data-ingestion")
            'DATA_INGESTION'
        """
        # Replace spaces and hyphens with underscores
        block_id = zone_name.replace(" ", "_").replace("-", "_")

        # Convert to uppercase
        block_id = block_id.upper()

        # Remove any non-alphanumeric characters except underscores
        block_id = re.sub(r"[^A-Z0-9_]", "", block_id)

        # Ensure it starts with a letter
        if block_id and not block_id[0].isalpha():
            block_id = "BLOCK_" + block_id

        return block_id

    def create_block_ports(
        self, dataset_names: List[str], port_type: str
    ) -> List[BlockPort]:
        """
        Create BlockPort objects from dataset names.

        Args:
            dataset_names: List of dataset names
            port_type: Port type ("dataset", "model", or "folder")

        Returns:
            List of BlockPort objects

        Example:
            >>> ports = identifier.create_block_ports(["input1", "input2"], "dataset")
            >>> print(len(ports))  # 2
        """
        ports = []
        for name in dataset_names:
            port = BlockPort(
                name=name, type=port_type, required=True, description=f"{name} port"
            )
            ports.append(port)
        return ports

    def extract_block_contents(
        self, boundary: Dict[str, Any], zone_items: Dict[str, List[str]]
    ) -> BlockContents:
        """
        Extract block contents (internal datasets and recipes).

        Args:
            boundary: Zone boundary with inputs, outputs, internals
            zone_items: Zone items with datasets and recipes

        Returns:
            BlockContents object

        Example:
            >>> contents = identifier.extract_block_contents(boundary, zone_items)
            >>> print(f"Internals: {contents.datasets}")
            >>> print(f"Recipes: {contents.recipes}")
        """
        # Internal datasets are those in boundary.internals
        internal_datasets = boundary.get("internals", [])

        # All recipes in the zone are part of the block
        recipes = zone_items.get("recipes", [])

        contents = BlockContents(datasets=internal_datasets, recipes=recipes, models=[])

        return contents

    def classify_hierarchy(self, zone_metadata: Dict[str, Any]) -> str:
        """
        Classify hierarchy level from zone metadata.

        Looks for tags like "level:process", "level:equipment", etc.

        Args:
            zone_metadata: Zone metadata dict

        Returns:
            Hierarchy level string or empty string if not found

        Example:
            >>> hierarchy = identifier.classify_hierarchy({"tags": ["level:process"]})
            >>> print(hierarchy)  # "process"
        """
        tags = zone_metadata.get("tags", [])

        for tag in tags:
            if tag.startswith("level:"):
                return tag.split(":", 1)[1]

        return ""

    def extract_domain(self, zone_metadata: Dict[str, Any]) -> str:
        """
        Extract domain from zone metadata.

        Looks for tags like "domain:analytics", "domain:ml", etc.

        Args:
            zone_metadata: Zone metadata dict

        Returns:
            Domain string or empty string if not found

        Example:
            >>> domain = identifier.extract_domain({"tags": ["domain:analytics"]})
            >>> print(domain)  # "analytics"
        """
        tags = zone_metadata.get("tags", [])

        for tag in tags:
            if tag.startswith("domain:"):
                return tag.split(":", 1)[1]

        return ""

    def extract_tags(self, zone_metadata: Dict[str, Any]) -> List[str]:
        """
        Extract tags from zone metadata.

        Filters out special tags (domain:, level:) and returns regular tags.

        Args:
            zone_metadata: Zone metadata dict

        Returns:
            List of tag strings

        Example:
            >>> tags = identifier.extract_tags({"tags": ["ml", "domain:analytics"]})
            >>> print(tags)  # ["ml"]
        """
        all_tags = zone_metadata.get("tags", [])

        # Filter out special tags
        regular_tags = []
        for tag in all_tags:
            if not tag.startswith("domain:") and not tag.startswith("level:"):
                regular_tags.append(tag)

        return regular_tags

    def generate_version(self, block_id: str) -> str:
        """
        Generate version for a block.

        For new blocks, returns "1.0.0".
        In future, this could check existing versions and increment.

        Args:
            block_id: Block identifier

        Returns:
            Semantic version string

        Example:
            >>> version = identifier.generate_version("NEW_BLOCK")
            >>> print(version)  # "1.0.0"
        """
        # For now, always return initial version
        # TODO: Check catalog for existing versions and increment
        return "1.0.0"

    def get_validation_message(self, boundary: Dict[str, Any]) -> str:
        """
        Get validation error message for invalid block.

        Args:
            boundary: Zone boundary dict

        Returns:
            Error message describing why block is invalid

        Example:
            >>> boundary = {"inputs": [], "outputs": ["out1"], "is_valid": True}
            >>> msg = identifier.get_validation_message(boundary)
            >>> print(msg)  # "Block has no inputs"
        """
        if not boundary.get("is_valid", False):
            return "Block has containment violation"

        inputs = boundary.get("inputs", [])
        if not inputs:
            return "Block has no inputs"

        outputs = boundary.get("outputs", [])
        if not outputs:
            return "Block has no outputs"

        return "Valid block"

    def _get_zone_metadata(self, project_key: str, zone_name: str) -> Dict[str, Any]:
        """
        Get zone metadata including tags.

        Args:
            project_key: Project identifier
            zone_name: Zone name

        Returns:
            Dictionary with zone metadata

        Note:
            This is a placeholder. In real implementation, would fetch from
            Dataiku API. For now, returns empty metadata.
        """
        # TODO: Fetch actual zone metadata from Dataiku API
        # For now, return empty metadata
        return {"tags": []}

    def _format_block_name(self, zone_name: str) -> str:
        """
        Format zone name into human-readable block name.

        Args:
            zone_name: Zone name

        Returns:
            Formatted block name

        Example:
            >>> identifier._format_block_name("feature_engineering")
            'Feature Engineering'
        """
        # Replace underscores and hyphens with spaces
        name = zone_name.replace("_", " ").replace("-", " ")

        # Title case
        name = name.title()

        return name

    def _get_dataset_config(self, dataset: Any) -> Dict[str, Any]:
        """
        Extracts technical configuration from a dataset.

        Args:
            dataset: Dataiku dataset object

        Returns:
            Dict with keys: type, connection, format_type, partitioning
        """
        # Step 1: Get settings
        settings = dataset.get_settings()
        raw = settings.get_raw()

        # Step 2: Extract basic fields
        ds_type = raw.get("type", "unknown")
        params = raw.get("params", {})
        connection = params.get("connection", "")

        # Step 3: Extract format
        format_type = raw.get("formatType", "")

        # Step 4: Extract partitioning
        partitioning = raw.get("partitioning", {}).get("dimensions", [])
        part_info = f"{len(partitioning)} dims" if partitioning else None

        return {
            "type": ds_type,
            "connection": connection,
            "format_type": format_type,
            "partitioning": part_info,
        }

    def _summarize_schema(self, dataset: Any) -> Dict[str, Any]:
        """
        Creates a lightweight summary of the dataset schema.

        Args:
            dataset: Dataiku dataset object

        Returns:
            Dict with keys: columns (int), sample (List[str])
        """
        try:
            # Step 1: Get schema
            schema = dataset.get_schema()
            columns = schema.get("columns", [])

            # Step 2: Summarize
            count = len(columns)
            sample = [c["name"] for c in columns[:5]]

            return {"columns": count, "sample": sample}
        except Exception:
            # Step 3: Graceful fallback
            return {"columns": 0, "sample": []}

    def _get_dataset_docs(self, dataset: Any) -> Dict[str, Any]:
        """
        Extracts documentation metadata from a dataset.

        Args:
            dataset: Dataiku dataset object

        Returns:
            Dict with keys: description, tags
        """
        # Step 1: Get settings
        settings = dataset.get_settings()
        raw = settings.get_raw()

        # Step 2: Extract info
        description = raw.get("description", "")
        tags = raw.get("tags", [])

        return {"description": description, "tags": tags}

    def _extract_dataset_details(
        self, project: Any, dataset_names: List[str]
    ) -> List[DatasetDetail]:
        """
        Extract detailed metadata for multiple datasets.

        Orchestrates the extraction of dataset details by calling helper methods
        for configuration, schema, and documentation.

        Args:
            project: Dataiku project object
            dataset_names: List of dataset names to extract

        Returns:
            List of DatasetDetail objects

        Example:
            >>> details = identifier._extract_dataset_details(project, ["ds1", "ds2"])
            >>> print(f"Extracted {len(details)} dataset details")
        """
        details = []

        for name in dataset_names:
            try:
                # Step 1: Get object
                ds = project.get_dataset(name)

                # Step 2: Call helpers
                config = self._get_dataset_config(ds)
                schema_sum = self._summarize_schema(ds)
                docs = self._get_dataset_docs(ds)

                # Step 3: Create Model
                detail = DatasetDetail(
                    name=name,
                    type=config["type"],
                    connection=config["connection"],
                    format_type=config["format_type"],
                    schema_summary=schema_sum,
                    partitioning=config["partitioning"],
                    tags=docs["tags"],
                    description=docs["description"],
                )
                details.append(detail)

            except Exception as e:
                # Step 4: Log error but continue
                print(f"Warning: Failed to extract details for {name}: {e}")
                continue

        return details
