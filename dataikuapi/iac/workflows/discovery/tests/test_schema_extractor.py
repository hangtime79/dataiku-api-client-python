"""Tests for SchemaExtractor component."""

import pytest
from typing import Dict, List, Any


class TestSchemaExtractor:
    """Test suite for SchemaExtractor class."""

    def test_create_schema_extractor(self, mock_dss_client):
        """Test creating SchemaExtractor instance."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )

        extractor = SchemaExtractor(mock_dss_client)
        assert extractor.client == mock_dss_client

    def test_extract_schema_from_dataset(self, mock_dss_client, mock_project):
        """Test extracting schema from dataset."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project
        dataset = mock_project.get_dataset.return_value
        dataset.get_schema.return_value = {
            "columns": [
                {"name": "ID", "type": "bigint"},
                {"name": "VALUE", "type": "double"},
            ]
        }

        extractor = SchemaExtractor(mock_dss_client)
        schema = extractor.extract_schema("TEST_PROJECT", "test_dataset")

        assert schema is not None
        assert "format_version" in schema
        assert "columns" in schema
        assert len(schema["columns"]) == 2

    def test_extract_schema_with_nullable_columns(self, mock_dss_client, mock_project):
        """Test extracting schema with nullable column information."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )

        # Setup mock with notNull flag
        mock_dss_client.get_project.return_value = mock_project
        dataset = mock_project.get_dataset.return_value
        dataset.get_schema.return_value = {
            "columns": [
                {"name": "ID", "type": "bigint", "notNull": True},
                {"name": "VALUE", "type": "double", "notNull": False},
            ]
        }

        extractor = SchemaExtractor(mock_dss_client)
        schema = extractor.extract_schema("TEST_PROJECT", "test_dataset")

        assert schema["columns"][0]["nullable"] is False  # notNull=True
        assert schema["columns"][1]["nullable"] is True  # notNull=False

    def test_extract_schema_with_descriptions(self, mock_dss_client, mock_project):
        """Test extracting schema with column descriptions."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )

        # Setup mock with comments
        mock_dss_client.get_project.return_value = mock_project
        dataset = mock_project.get_dataset.return_value
        dataset.get_schema.return_value = {
            "columns": [
                {"name": "ID", "type": "bigint", "comment": "Unique identifier"},
                {"name": "VALUE", "type": "double", "comment": "Measurement value"},
            ]
        }

        extractor = SchemaExtractor(mock_dss_client)
        schema = extractor.extract_schema("TEST_PROJECT", "test_dataset")

        assert schema["columns"][0]["description"] == "Unique identifier"
        assert schema["columns"][1]["description"] == "Measurement value"

    def test_handle_empty_schema(self, mock_dss_client, mock_project):
        """Test handling dataset with no schema."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )

        # Setup mock with empty schema
        mock_dss_client.get_project.return_value = mock_project
        dataset = mock_project.get_dataset.return_value
        dataset.get_schema.return_value = {"columns": []}

        extractor = SchemaExtractor(mock_dss_client)
        schema = extractor.extract_schema("TEST_PROJECT", "test_dataset")

        assert schema is None  # No schema available

    def test_handle_schema_extraction_error(self, mock_dss_client, mock_project):
        """Test handling schema extraction errors."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )
        from dataikuapi.iac.workflows.discovery.exceptions import (
            SchemaExtractionError,
        )

        # Setup mock to raise exception
        mock_dss_client.get_project.return_value = mock_project
        dataset = mock_project.get_dataset.return_value
        dataset.get_schema.side_effect = Exception("Schema not available")

        extractor = SchemaExtractor(mock_dss_client)

        with pytest.raises(SchemaExtractionError):
            extractor.extract_schema("TEST_PROJECT", "test_dataset")


class TestTypeMapping:
    """Test suite for Dataiku type mapping."""

    def test_map_string_type(self, mock_dss_client):
        """Test mapping string type."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )

        extractor = SchemaExtractor(mock_dss_client)
        assert extractor.map_dataiku_type_to_standard("string") == "string"

    def test_map_integer_types(self, mock_dss_client):
        """Test mapping integer types."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )

        extractor = SchemaExtractor(mock_dss_client)
        assert extractor.map_dataiku_type_to_standard("int") == "integer"
        assert extractor.map_dataiku_type_to_standard("bigint") == "integer"

    def test_map_numeric_types(self, mock_dss_client):
        """Test mapping numeric types."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )

        extractor = SchemaExtractor(mock_dss_client)
        assert extractor.map_dataiku_type_to_standard("float") == "double"
        assert extractor.map_dataiku_type_to_standard("double") == "double"

    def test_map_boolean_type(self, mock_dss_client):
        """Test mapping boolean type."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )

        extractor = SchemaExtractor(mock_dss_client)
        assert extractor.map_dataiku_type_to_standard("boolean") == "boolean"

    def test_map_date_type(self, mock_dss_client):
        """Test mapping date type."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )

        extractor = SchemaExtractor(mock_dss_client)
        assert extractor.map_dataiku_type_to_standard("date") == "date"

    def test_map_complex_types(self, mock_dss_client):
        """Test mapping complex types."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )

        extractor = SchemaExtractor(mock_dss_client)
        assert extractor.map_dataiku_type_to_standard("array") == "array"
        assert extractor.map_dataiku_type_to_standard("object") == "object"
        assert extractor.map_dataiku_type_to_standard("map") == "object"

    def test_map_unknown_type_defaults_to_string(self, mock_dss_client):
        """Test unknown types default to string."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )

        extractor = SchemaExtractor(mock_dss_client)
        assert extractor.map_dataiku_type_to_standard("unknown_type") == "string"

    def test_type_mapping_case_insensitive(self, mock_dss_client):
        """Test type mapping is case insensitive."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )

        extractor = SchemaExtractor(mock_dss_client)
        assert extractor.map_dataiku_type_to_standard("STRING") == "string"
        assert extractor.map_dataiku_type_to_standard("BIGINT") == "integer"
        assert extractor.map_dataiku_type_to_standard("Boolean") == "boolean"


class TestSchemaEnrichment:
    """Test suite for schema enrichment with ports."""

    def test_enrich_block_with_schemas(self, mock_dss_client, mock_project):
        """Test enriching block metadata with schemas."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
            BlockContents,
        )

        # Setup mock
        mock_dss_client.get_project.return_value = mock_project
        dataset = mock_project.get_dataset.return_value
        dataset.get_schema.return_value = {
            "columns": [{"name": "ID", "type": "bigint"}]
        }

        # Create block metadata with input port
        metadata = BlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST_PROJECT",
            inputs=[BlockPort(name="input1", type="dataset")],
            outputs=[BlockPort(name="output1", type="dataset")],
            contains=BlockContents(),
        )

        extractor = SchemaExtractor(mock_dss_client)
        enriched = extractor.enrich_block_with_schemas(metadata)

        # Input port should have schema reference
        assert enriched.inputs[0].schema_ref is not None

    def test_skip_schema_for_missing_datasets(self, mock_dss_client, mock_project):
        """Test skipping schema extraction for missing datasets."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
            BlockContents,
        )

        # Setup mock to simulate missing dataset
        mock_dss_client.get_project.return_value = mock_project
        dataset = mock_project.get_dataset.return_value
        dataset.get_schema.return_value = {"columns": []}  # Empty schema

        metadata = BlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST_PROJECT",
            inputs=[BlockPort(name="input1", type="dataset")],
            outputs=[],
            contains=BlockContents(),
        )

        extractor = SchemaExtractor(mock_dss_client)
        enriched = extractor.enrich_block_with_schemas(metadata)

        # Should handle gracefully, no schema_ref set
        assert enriched.inputs[0].schema_ref is None


class TestSchemaValidation:
    """Test suite for schema validation."""

    def test_validate_schema_format(self, mock_dss_client):
        """Test validating schema format."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )

        extractor = SchemaExtractor(mock_dss_client)

        # Valid schema
        valid_schema = {
            "format_version": "1.0",
            "columns": [{"name": "ID", "type": "integer", "nullable": False}],
        }

        assert extractor.validate_schema(valid_schema) is True

    def test_validate_schema_missing_version(self, mock_dss_client):
        """Test validating schema with missing format version."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )

        extractor = SchemaExtractor(mock_dss_client)

        # Missing format_version
        invalid_schema = {
            "columns": [{"name": "ID", "type": "integer"}],
        }

        assert extractor.validate_schema(invalid_schema) is False

    def test_validate_schema_missing_columns(self, mock_dss_client):
        """Test validating schema with missing columns."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )

        extractor = SchemaExtractor(mock_dss_client)

        # Missing columns
        invalid_schema = {
            "format_version": "1.0",
        }

        assert extractor.validate_schema(invalid_schema) is False


class TestSchemaStorage:
    """Test suite for schema storage/reference generation."""

    def test_generate_schema_reference_path(self, mock_dss_client):
        """Test generating schema reference path."""
        from dataikuapi.iac.workflows.discovery.schema_extractor import (
            SchemaExtractor,
        )

        extractor = SchemaExtractor(mock_dss_client)

        # Generate path for dataset schema
        path = extractor.generate_schema_reference(
            "TEST_BLOCK", "1.0.0", "input_dataset"
        )

        assert "TEST_BLOCK" in path
        assert "1.0.0" in path
        assert "input_dataset" in path
        assert path.endswith(".json")
