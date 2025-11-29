"""Tests for Discovery Agent data models."""

import pytest
from datetime import datetime


class TestBlockPort:
    """Test suite for BlockPort model."""

    def test_create_block_port_minimal(self):
        """Test creating BlockPort with minimal required fields."""
        from dataikuapi.iac.workflows.discovery.models import BlockPort

        port = BlockPort(
            name="INPUT_DATA",
            type="dataset",
        )

        assert port.name == "INPUT_DATA"
        assert port.type == "dataset"
        assert port.required is True  # Default
        assert port.description == ""

    def test_create_block_port_complete(self):
        """Test creating BlockPort with all fields."""
        from dataikuapi.iac.workflows.discovery.models import BlockPort

        port = BlockPort(
            name="OUTPUT_DATA",
            type="dataset",
            required=False,
            description="Output dataset for results",
        )

        assert port.name == "OUTPUT_DATA"
        assert port.type == "dataset"
        assert port.required is False
        assert port.description == "Output dataset for results"

    def test_block_port_to_dict(self):
        """Test BlockPort serialization to dict."""
        from dataikuapi.iac.workflows.discovery.models import BlockPort

        port = BlockPort(
            name="INPUT_DATA",
            type="dataset",
            required=True,
            description="Test input",
        )

        result = port.to_dict()

        assert result == {
            "name": "INPUT_DATA",
            "type": "dataset",
            "required": True,
            "description": "Test input",
        }

    def test_block_port_from_dict(self):
        """Test BlockPort deserialization from dict."""
        from dataikuapi.iac.workflows.discovery.models import BlockPort

        data = {
            "name": "OUTPUT_DATA",
            "type": "dataset",
            "required": False,
            "description": "Output data",
        }

        port = BlockPort.from_dict(data)

        assert port.name == "OUTPUT_DATA"
        assert port.type == "dataset"
        assert port.required is False
        assert port.description == "Output data"


class TestBlockContents:
    """Test suite for BlockContents model."""

    def test_create_block_contents_empty(self):
        """Test creating empty BlockContents."""
        from dataikuapi.iac.workflows.discovery.models import BlockContents

        contents = BlockContents()

        assert contents.datasets == []
        assert contents.recipes == []
        assert contents.models == []

    def test_create_block_contents_with_items(self):
        """Test creating BlockContents with items."""
        from dataikuapi.iac.workflows.discovery.models import BlockContents

        contents = BlockContents(
            datasets=["ds1", "ds2"],
            recipes=["recipe1"],
            models=["model1"],
        )

        assert contents.datasets == ["ds1", "ds2"]
        assert contents.recipes == ["recipe1"]
        assert contents.models == ["model1"]

    def test_block_contents_to_dict(self):
        """Test BlockContents serialization."""
        from dataikuapi.iac.workflows.discovery.models import BlockContents

        contents = BlockContents(
            datasets=["ds1"],
            recipes=["recipe1"],
            models=[],
        )

        result = contents.to_dict()

        assert result == {
            "datasets": ["ds1"],
            "recipes": ["recipe1"],
            "models": [],
        }

    def test_block_contents_from_dict(self):
        """Test BlockContents deserialization."""
        from dataikuapi.iac.workflows.discovery.models import BlockContents

        data = {
            "datasets": ["ds1", "ds2"],
            "recipes": ["recipe1"],
            "models": [],
        }

        contents = BlockContents.from_dict(data)

        assert contents.datasets == ["ds1", "ds2"]
        assert contents.recipes == ["recipe1"]
        assert contents.models == []


class TestBlockMetadata:
    """Test suite for BlockMetadata model."""

    def test_create_block_metadata_minimal(self, sample_block_metadata):
        """Test creating BlockMetadata with minimal fields."""
        from dataikuapi.iac.workflows.discovery.models import BlockMetadata

        metadata = BlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST_PROJECT",
        )

        assert metadata.block_id == "TEST_BLOCK"
        assert metadata.version == "1.0.0"
        assert metadata.type == "zone"
        assert metadata.source_project == "TEST_PROJECT"
        assert metadata.blocked is False  # Default

    def test_create_block_metadata_complete(self):
        """Test creating BlockMetadata with all fields."""
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
            BlockContents,
        )

        metadata = BlockMetadata(
            block_id="COMPLETE_BLOCK",
            version="2.0.0",
            type="zone",
            blocked=True,
            name="Complete Test Block",
            description="Full description",
            hierarchy_level="process",
            domain="testing",
            tags=["test", "complete"],
            source_project="SOURCE_PROJECT",
            source_zone="source_zone",
            inputs=[BlockPort(name="INPUT", type="dataset", required=True)],
            outputs=[BlockPort(name="OUTPUT", type="dataset")],
            contains=BlockContents(
                datasets=["internal_ds"],
                recipes=["process_recipe"],
            ),
            created_by="test_user",
        )

        assert metadata.block_id == "COMPLETE_BLOCK"
        assert metadata.version == "2.0.0"
        assert metadata.blocked is True
        assert len(metadata.inputs) == 1
        assert len(metadata.outputs) == 1
        assert len(metadata.contains.datasets) == 1

    def test_block_metadata_to_dict(self):
        """Test BlockMetadata serialization to dict."""
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
            BlockContents,
        )

        metadata = BlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST_PROJECT",
            inputs=[BlockPort(name="INPUT", type="dataset")],
            outputs=[BlockPort(name="OUTPUT", type="dataset")],
            contains=BlockContents(datasets=["ds1"]),
        )

        result = metadata.to_dict()

        assert result["block_id"] == "TEST_BLOCK"
        assert result["version"] == "1.0.0"
        assert len(result["inputs"]) == 1
        assert result["inputs"][0]["name"] == "INPUT"
        assert result["contains"]["datasets"] == ["ds1"]

    def test_block_metadata_from_dict(self, sample_block_metadata):
        """Test BlockMetadata deserialization from dict."""
        from dataikuapi.iac.workflows.discovery.models import BlockMetadata

        metadata = BlockMetadata.from_dict(sample_block_metadata)

        assert metadata.block_id == "TEST_BLOCK"
        assert metadata.version == "1.0.0"
        assert len(metadata.inputs) == 1
        assert metadata.inputs[0].name == "INPUT_DATA"
        assert len(metadata.outputs) == 1
        assert len(metadata.contains.datasets) == 1

    def test_block_metadata_validate_valid(self):
        """Test validation of valid BlockMetadata."""
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
        )

        metadata = BlockMetadata(
            block_id="VALID_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="PROJECT",
            inputs=[BlockPort(name="INPUT", type="dataset")],
            outputs=[BlockPort(name="OUTPUT", type="dataset")],
        )

        errors = metadata.validate()
        assert len(errors) == 0

    def test_block_metadata_validate_missing_inputs(self):
        """Test validation catches missing inputs."""
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
        )

        metadata = BlockMetadata(
            block_id="INVALID_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="PROJECT",
            inputs=[],  # No inputs
            outputs=[BlockPort(name="OUTPUT", type="dataset")],
        )

        errors = metadata.validate()
        assert len(errors) > 0
        assert any("input" in err.lower() for err in errors)

    def test_block_metadata_validate_missing_outputs(self):
        """Test validation catches missing outputs."""
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
        )

        metadata = BlockMetadata(
            block_id="INVALID_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="PROJECT",
            inputs=[BlockPort(name="INPUT", type="dataset")],
            outputs=[],  # No outputs
        )

        errors = metadata.validate()
        assert len(errors) > 0
        assert any("output" in err.lower() for err in errors)

    def test_block_metadata_validate_invalid_version(self):
        """Test validation catches invalid semantic version."""
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
        )

        metadata = BlockMetadata(
            block_id="INVALID_BLOCK",
            version="1.0",  # Invalid - not X.Y.Z format
            type="zone",
            source_project="PROJECT",
            inputs=[BlockPort(name="INPUT", type="dataset")],
            outputs=[BlockPort(name="OUTPUT", type="dataset")],
        )

        errors = metadata.validate()
        assert len(errors) > 0
        assert any("version" in err.lower() for err in errors)

    def test_block_metadata_validate_invalid_block_id(self):
        """Test validation catches invalid block_id format."""
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
        )

        metadata = BlockMetadata(
            block_id="invalid_block",  # Invalid - lowercase
            version="1.0.0",
            type="zone",
            source_project="PROJECT",
            inputs=[BlockPort(name="INPUT", type="dataset")],
            outputs=[BlockPort(name="OUTPUT", type="dataset")],
        )

        errors = metadata.validate()
        assert len(errors) > 0
        assert any("block_id" in err.lower() for err in errors)

    def test_block_metadata_validate_invalid_type(self):
        """Test validation catches invalid type."""
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
        )

        metadata = BlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="invalid",  # Invalid type
            source_project="PROJECT",
            inputs=[BlockPort(name="INPUT", type="dataset")],
            outputs=[BlockPort(name="OUTPUT", type="dataset")],
        )

        errors = metadata.validate()
        assert len(errors) > 0
        assert any("type" in err.lower() for err in errors)

    def test_block_metadata_validate_missing_source_project(self):
        """Test validation catches missing source_project."""
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
        )

        metadata = BlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="",  # Empty source_project
            inputs=[BlockPort(name="INPUT", type="dataset")],
            outputs=[BlockPort(name="OUTPUT", type="dataset")],
        )

        errors = metadata.validate()
        assert len(errors) > 0
        assert any("source_project" in err.lower() for err in errors)

    def test_block_metadata_validate_empty_block_id(self):
        """Test validation catches empty block_id."""
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
        )

        metadata = BlockMetadata(
            block_id="",  # Empty
            version="1.0.0",
            type="zone",
            source_project="PROJECT",
            inputs=[BlockPort(name="INPUT", type="dataset")],
            outputs=[BlockPort(name="OUTPUT", type="dataset")],
        )

        errors = metadata.validate()
        assert len(errors) > 0
        assert any("block_id" in err.lower() for err in errors)

    def test_block_metadata_validate_empty_version(self):
        """Test validation catches empty version."""
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
        )

        metadata = BlockMetadata(
            block_id="TEST_BLOCK",
            version="",  # Empty
            type="zone",
            source_project="PROJECT",
            inputs=[BlockPort(name="INPUT", type="dataset")],
            outputs=[BlockPort(name="OUTPUT", type="dataset")],
        )

        errors = metadata.validate()
        assert len(errors) > 0
        assert any("version" in err.lower() for err in errors)


class TestBlockSummary:
    """Test suite for BlockSummary model."""

    def test_create_block_summary(self):
        """Test creating BlockSummary from BlockMetadata."""
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockSummary,
            BlockPort,
        )

        metadata = BlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            name="Test Block",
            description="A test block",
            hierarchy_level="equipment",
            domain="testing",
            tags=["test"],
            source_project="PROJECT",
            inputs=[BlockPort(name="INPUT", type="dataset")],
            outputs=[BlockPort(name="OUTPUT", type="dataset")],
        )

        summary = BlockSummary.from_metadata(metadata)

        assert summary.block_id == "TEST_BLOCK"
        assert summary.version == "1.0.0"
        assert summary.name == "Test Block"
        assert summary.hierarchy_level == "equipment"
        assert len(summary.inputs) == 1
        assert len(summary.outputs) == 1

    def test_block_summary_to_dict(self):
        """Test BlockSummary serialization."""
        from dataikuapi.iac.workflows.discovery.models import BlockSummary

        summary = BlockSummary(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            name="Test Block",
            hierarchy_level="equipment",
            domain="testing",
            tags=["test"],
            inputs=[{"name": "INPUT", "type": "dataset"}],
            outputs=[{"name": "OUTPUT", "type": "dataset"}],
        )

        result = summary.to_dict()

        assert result["block_id"] == "TEST_BLOCK"
        assert result["name"] == "Test Block"
        assert len(result["inputs"]) == 1
