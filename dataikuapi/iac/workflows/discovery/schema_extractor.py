"""Schema Extractor for Discovery Agent.

This module implements the SchemaExtractor class which extracts dataset schemas
and enriches block metadata with schema information.
"""

from typing import Dict, List, Any, Optional
from dataikuapi import DSSClient
from dataikuapi.iac.workflows.discovery.models import BlockMetadata
from dataikuapi.iac.workflows.discovery.exceptions import SchemaExtractionError


class SchemaExtractor:
    """
    Extracts dataset schemas and enriches block metadata.

    The SchemaExtractor implements Algorithm 3 from the specification,
    extracting dataset schemas from Dataiku and converting them to a
    standardized format for the block catalog.

    Attributes:
        client: DSSClient instance for API access

    Example:
        >>> client = DSSClient(host, api_key)
        >>> extractor = SchemaExtractor(client)
        >>> schema = extractor.extract_schema("MY_PROJECT", "my_dataset")
        >>> print(schema)
        {
            'format_version': '1.0',
            'columns': [
                {'name': 'ID', 'type': 'integer', 'nullable': False},
                {'name': 'VALUE', 'type': 'double', 'nullable': True}
            ]
        }
    """

    def __init__(self, client: DSSClient):
        """
        Initialize SchemaExtractor with DSSClient.

        Args:
            client: Authenticated DSSClient instance
        """
        self.client = client

    def extract_schema(
        self, project_key: str, dataset_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract schema from a dataset.

        Implements Algorithm 3 from the specification:
        - Get raw schema from dataset
        - Convert column types to standard format
        - Extract nullable and description metadata
        - Return standardized schema dict

        Args:
            project_key: Project identifier
            dataset_name: Dataset name

        Returns:
            Schema dict with format_version and columns, or None if no schema

        Raises:
            SchemaExtractionError: If schema extraction fails

        Example:
            >>> schema = extractor.extract_schema("PROJECT", "dataset1")
            >>> print(len(schema['columns']))
        """
        try:
            # Get dataset
            project = self.client.get_project(project_key)
            dataset = project.get_dataset(dataset_name)

            # Get raw schema
            schema_raw = dataset.get_schema()

            # Check if schema exists and has columns
            if not schema_raw or not schema_raw.get("columns"):
                return None

            # Convert to standard format
            columns = []
            for col in schema_raw["columns"]:
                column_def = {
                    "name": col["name"],
                    "type": self.map_dataiku_type_to_standard(col["type"]),
                    "description": col.get("comment", ""),
                    "nullable": not col.get("notNull", False),
                }
                columns.append(column_def)

            # Return standardized schema
            return {"format_version": "1.0", "columns": columns}

        except Exception as e:
            raise SchemaExtractionError(
                f"Failed to extract schema from {dataset_name}: {e}"
            ) from e

    def map_dataiku_type_to_standard(self, dataiku_type: str) -> str:
        """
        Map Dataiku data type to standard type.

        Converts Dataiku-specific type names to standardized type names
        for consistency across the catalog.

        Args:
            dataiku_type: Dataiku type name (e.g., "bigint", "string")

        Returns:
            Standard type name (e.g., "integer", "string")

        Example:
            >>> extractor.map_dataiku_type_to_standard("bigint")
            'integer'
            >>> extractor.map_dataiku_type_to_standard("float")
            'double'
        """
        mapping = {
            "string": "string",
            "int": "integer",
            "bigint": "integer",
            "float": "double",
            "double": "double",
            "boolean": "boolean",
            "date": "date",
            "array": "array",
            "object": "object",
            "map": "object",
        }

        # Case insensitive lookup with default to string
        return mapping.get(dataiku_type.lower(), "string")

    def enrich_block_with_schemas(self, metadata: BlockMetadata) -> BlockMetadata:
        """
        Enrich block metadata with schema information.

        Extracts schemas for all input and output datasets and adds
        schema references to the block ports.

        Args:
            metadata: BlockMetadata to enrich

        Returns:
            Enriched BlockMetadata with schema references

        Example:
            >>> enriched = extractor.enrich_block_with_schemas(block_metadata)
            >>> print(enriched.inputs[0].schema_ref)
            'schemas/MY_BLOCK_v1.0.0/input1.json'
        """
        project_key = metadata.source_project

        # Enrich input ports with schemas
        for port in metadata.inputs:
            if port.type == "dataset":
                try:
                    schema = self.extract_schema(project_key, port.name)
                    if schema:
                        # Generate schema reference path
                        schema_ref = self.generate_schema_reference(
                            metadata.block_id, metadata.version, port.name
                        )
                        port.schema_ref = schema_ref
                except SchemaExtractionError:
                    # If schema extraction fails, leave schema_ref as None
                    pass

        # Enrich output ports with schemas
        for port in metadata.outputs:
            if port.type == "dataset":
                try:
                    schema = self.extract_schema(project_key, port.name)
                    if schema:
                        # Generate schema reference path
                        schema_ref = self.generate_schema_reference(
                            metadata.block_id, metadata.version, port.name
                        )
                        port.schema_ref = schema_ref
                except SchemaExtractionError:
                    # If schema extraction fails, leave schema_ref as None
                    pass

        return metadata

    def validate_schema(self, schema: Dict[str, Any]) -> bool:
        """
        Validate schema format.

        Checks that schema has required fields:
        - format_version
        - columns (list)

        Args:
            schema: Schema dict to validate

        Returns:
            True if valid, False otherwise

        Example:
            >>> schema = {'format_version': '1.0', 'columns': [...]}
            >>> extractor.validate_schema(schema)
            True
        """
        if not isinstance(schema, dict):
            return False

        # Must have format_version
        if "format_version" not in schema:
            return False

        # Must have columns
        if "columns" not in schema:
            return False

        # Columns must be a list
        if not isinstance(schema["columns"], list):
            return False

        return True

    def generate_schema_reference(
        self, block_id: str, version: str, dataset_name: str
    ) -> str:
        """
        Generate schema reference path for storage.

        Creates a path in the format:
        schemas/{BLOCK_ID}_v{VERSION}/{dataset_name}.json

        Args:
            block_id: Block identifier
            version: Block version
            dataset_name: Dataset name

        Returns:
            Schema reference path

        Example:
            >>> path = extractor.generate_schema_reference("MY_BLOCK", "1.0.0", "input1")
            >>> print(path)
            'schemas/MY_BLOCK_v1.0.0/input1.json'
        """
        # Format: schemas/{BLOCK_ID}_v{VERSION}/{dataset_name}.json
        return f"schemas/{block_id}_v{version}/{dataset_name}.json"
