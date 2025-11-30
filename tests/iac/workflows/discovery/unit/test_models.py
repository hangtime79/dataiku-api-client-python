"""Unit tests for Discovery Agent data models."""

import pytest
from dataikuapi.iac.workflows.discovery.models import (
    DatasetDetail,
    RecipeDetail,
    LibraryReference,
    NotebookReference,
    EnhancedBlockMetadata,
    BlockMetadata,
)


class TestDatasetDetail:
    """Tests for DatasetDetail model."""

    def test_dataset_detail_serialization(self):
        """Test DatasetDetail serialization with all fields."""
        dataset = DatasetDetail(
            name="CUSTOMER_DATA",
            type="Snowflake",
            connection="PROD_DB",
            format_type="table",
            schema_summary={"columns": 10, "sample": ["id", "name", "email"]},
            partitioning="date",
            tags=["pii", "critical"],
            description="Customer master data",
            estimated_size="2.5GB",
            last_built="2025-12-01T00:00:00Z",
        )

        # Serialize
        data = dataset.to_dict()
        assert data["name"] == "CUSTOMER_DATA"
        assert data["type"] == "Snowflake"
        assert data["connection"] == "PROD_DB"
        assert data["format_type"] == "table"
        assert data["schema_summary"]["columns"] == 10
        assert data["partitioning"] == "date"
        assert "pii" in data["tags"]
        assert data["description"] == "Customer master data"
        assert data["estimated_size"] == "2.5GB"
        assert data["last_built"] == "2025-12-01T00:00:00Z"

        # Deserialize
        restored = DatasetDetail.from_dict(data)
        assert restored == dataset
        assert restored.name == "CUSTOMER_DATA"
        assert len(restored.tags) == 2

    def test_dataset_detail_minimal(self):
        """Test DatasetDetail with only required fields."""
        dataset = DatasetDetail(
            name="RAW_DATA",
            type="S3",
            connection="data-lake",
            format_type="parquet",
            schema_summary={},
        )

        data = dataset.to_dict()
        restored = DatasetDetail.from_dict(data)

        assert restored == dataset
        assert restored.partitioning is None
        assert restored.tags == []
        assert restored.description == ""
        assert restored.estimated_size is None
        assert restored.last_built is None

    def test_dataset_detail_from_dict_missing_optionals(self):
        """Test DatasetDetail deserialization handles missing optional fields."""
        data = {
            "name": "TEST_DS",
            "type": "PostgreSQL",
            "connection": "db",
            "format_type": "table",
            "schema_summary": {"columns": 5},
        }

        dataset = DatasetDetail.from_dict(data)
        assert dataset.name == "TEST_DS"
        assert dataset.partitioning is None
        assert dataset.tags == []
        assert dataset.description == ""


class TestRecipeDetail:
    """Tests for RecipeDetail model."""

    def test_recipe_detail_serialization(self):
        """Test RecipeDetail serialization with all fields."""
        recipe = RecipeDetail(
            name="feature_engineering",
            type="python",
            engine="spark",
            inputs=["raw_data", "lookup_table"],
            outputs=["features"],
            description="Generate ML features",
            tags=["ml", "preprocessing"],
            code_snippet="def transform(df):\n    return df",
            config_summary={"memory": "8GB", "cores": 4},
        )

        # Serialize
        data = recipe.to_dict()
        assert data["name"] == "feature_engineering"
        assert data["type"] == "python"
        assert data["engine"] == "spark"
        assert len(data["inputs"]) == 2
        assert "raw_data" in data["inputs"]
        assert data["outputs"] == ["features"]
        assert "ml" in data["tags"]
        assert data["code_snippet"] is not None
        assert data["config_summary"]["memory"] == "8GB"

        # Deserialize
        restored = RecipeDetail.from_dict(data)
        assert restored == recipe
        assert restored.inputs == ["raw_data", "lookup_table"]
        assert restored.config_summary["cores"] == 4

    def test_recipe_detail_minimal(self):
        """Test RecipeDetail with only required fields."""
        recipe = RecipeDetail(
            name="simple_join",
            type="sql",
            engine="indb",
            inputs=["table_a"],
            outputs=["result"],
        )

        data = recipe.to_dict()
        restored = RecipeDetail.from_dict(data)

        assert restored == recipe
        assert restored.description == ""
        assert restored.tags == []
        assert restored.code_snippet is None
        assert restored.config_summary == {}

    def test_recipe_detail_from_dict_missing_optionals(self):
        """Test RecipeDetail deserialization handles missing optional fields."""
        data = {
            "name": "compute",
            "type": "python",
            "engine": "containerized",
            "inputs": ["in1", "in2"],
            "outputs": ["out1"],
        }

        recipe = RecipeDetail.from_dict(data)
        assert recipe.name == "compute"
        assert recipe.description == ""
        assert recipe.tags == []
        assert recipe.code_snippet is None
        assert recipe.config_summary == {}


class TestReferenceModels:
    """Tests for LibraryReference and NotebookReference models."""

    def test_library_reference_serialization(self):
        """Test LibraryReference serialization."""
        lib = LibraryReference(
            name="utils.py",
            type="python",
            description="Utility functions",
        )

        data = lib.to_dict()
        assert data["name"] == "utils.py"
        assert data["type"] == "python"
        assert data["description"] == "Utility functions"

        restored = LibraryReference.from_dict(data)
        assert restored == lib

    def test_library_reference_minimal(self):
        """Test LibraryReference with minimal fields."""
        lib = LibraryReference(name="helpers.R", type="R")

        data = lib.to_dict()
        restored = LibraryReference.from_dict(data)

        assert restored == lib
        assert restored.description == ""

    def test_notebook_reference_serialization(self):
        """Test NotebookReference serialization."""
        nb = NotebookReference(
            name="exploratory_analysis",
            type="jupyter",
            description="EDA for customer data",
            tags=["analysis", "wip"],
        )

        data = nb.to_dict()
        assert data["name"] == "exploratory_analysis"
        assert data["type"] == "jupyter"
        assert "wip" in data["tags"]
        assert len(data["tags"]) == 2

        restored = NotebookReference.from_dict(data)
        assert restored == nb

    def test_notebook_reference_minimal(self):
        """Test NotebookReference with minimal fields."""
        nb = NotebookReference(name="query", type="sql")

        data = nb.to_dict()
        restored = NotebookReference.from_dict(data)

        assert restored == nb
        assert restored.description == ""
        assert restored.tags == []


class TestEnhancedBlockMetadata:
    """Tests for EnhancedBlockMetadata model."""

    def test_enhanced_metadata_deep_serialization(self):
        """Test EnhancedBlockMetadata deep serialization of nested objects."""
        # Create enhanced metadata with nested objects
        enhanced = EnhancedBlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="PROJ",
            dataset_details=[
                DatasetDetail(
                    name="ds1",
                    type="Snowflake",
                    connection="db",
                    format_type="table",
                    schema_summary={"columns": 5},
                )
            ],
            recipe_details=[
                RecipeDetail(
                    name="r1",
                    type="python",
                    engine="spark",
                    inputs=["ds1"],
                    outputs=["ds2"],
                )
            ],
            library_refs=[LibraryReference(name="lib.py", type="python")],
            notebook_refs=[NotebookReference(name="nb1", type="jupyter")],
        )

        # Serialize
        data = enhanced.to_dict()

        # Verify base fields are present
        assert data["block_id"] == "TEST_BLOCK"
        assert data["version"] == "1.0.0"

        # Verify enhanced fields are present
        assert "dataset_details" in data
        assert "recipe_details" in data
        assert "library_refs" in data
        assert "notebook_refs" in data

        # CRITICAL: Verify nested objects are serialized to dicts, not left as objects
        assert isinstance(data["dataset_details"], list)
        assert isinstance(data["dataset_details"][0], dict)
        assert data["dataset_details"][0]["name"] == "ds1"

        assert isinstance(data["recipe_details"], list)
        assert isinstance(data["recipe_details"][0], dict)
        assert data["recipe_details"][0]["name"] == "r1"

        # Deserialize
        restored = EnhancedBlockMetadata.from_dict(data)

        # Verify base fields
        assert restored.block_id == "TEST_BLOCK"
        assert restored.version == "1.0.0"

        # CRITICAL: Verify nested dicts are restored to proper objects
        assert len(restored.dataset_details) == 1
        assert isinstance(restored.dataset_details[0], DatasetDetail)
        assert restored.dataset_details[0].name == "ds1"

        assert len(restored.recipe_details) == 1
        assert isinstance(restored.recipe_details[0], RecipeDetail)
        assert restored.recipe_details[0].name == "r1"

        assert len(restored.library_refs) == 1
        assert isinstance(restored.library_refs[0], LibraryReference)

        assert len(restored.notebook_refs) == 1
        assert isinstance(restored.notebook_refs[0], NotebookReference)

    def test_enhanced_metadata_empty_lists(self):
        """Test EnhancedBlockMetadata with no nested objects."""
        enhanced = EnhancedBlockMetadata(
            block_id="MINIMAL_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="PROJ",
        )

        data = enhanced.to_dict()
        restored = EnhancedBlockMetadata.from_dict(data)

        assert restored.block_id == "MINIMAL_BLOCK"
        assert isinstance(restored.dataset_details, list)
        assert len(restored.dataset_details) == 0
        assert isinstance(restored.recipe_details, list)
        assert len(restored.recipe_details) == 0
        assert isinstance(restored.library_refs, list)
        assert isinstance(restored.notebook_refs, list)

    def test_enhanced_metadata_defaults(self):
        """Test that missing lists become empty lists, not None."""
        # Simulate loading from old data without enhanced fields
        data = {
            "block_id": "OLD_BLOCK",
            "version": "1.0.0",
            "type": "zone",
            "source_project": "LEGACY_PROJ",
        }

        obj = EnhancedBlockMetadata.from_dict(data)

        # Verify backward compatibility
        assert obj.block_id == "OLD_BLOCK"
        assert isinstance(obj.dataset_details, list)
        assert len(obj.dataset_details) == 0
        assert isinstance(obj.recipe_details, list)
        assert len(obj.recipe_details) == 0
        assert isinstance(obj.library_refs, list)
        assert isinstance(obj.notebook_refs, list)
        assert obj.flow_graph is None
        assert obj.estimated_complexity == ""
        assert obj.estimated_size == ""

    def test_enhanced_metadata_with_complexity_and_size(self):
        """Test EnhancedBlockMetadata with complexity and size estimates."""
        enhanced = EnhancedBlockMetadata(
            block_id="COMPLEX_BLOCK",
            version="2.0.0",
            type="solution",
            source_project="PROJ",
            estimated_complexity="complex",
            estimated_size="15.2GB",
            flow_graph={"nodes": 10, "edges": 15},
        )

        data = enhanced.to_dict()
        restored = EnhancedBlockMetadata.from_dict(data)

        assert restored.estimated_complexity == "complex"
        assert restored.estimated_size == "15.2GB"
        assert restored.flow_graph["nodes"] == 10
        assert restored.flow_graph["edges"] == 15

    def test_enhanced_metadata_inherits_from_block_metadata(self):
        """Test that EnhancedBlockMetadata properly inherits from BlockMetadata."""
        # Verify inheritance
        assert issubclass(EnhancedBlockMetadata, BlockMetadata)

        # Create instance with base class methods
        enhanced = EnhancedBlockMetadata(
            block_id="INHERIT_TEST",
            version="1.0.0",
            type="zone",
            source_project="PROJ",
            name="Test Block",
            description="Testing inheritance",
            tags=["test"],
        )

        # Verify base class fields work
        assert enhanced.block_id == "INHERIT_TEST"
        assert enhanced.name == "Test Block"
        assert enhanced.description == "Testing inheritance"
        assert "test" in enhanced.tags

        # Verify base class methods work (validate)
        errors = enhanced.validate()
        # Should have errors because no inputs/outputs defined
        assert len(errors) > 0
        assert any("input" in err.lower() for err in errors)
