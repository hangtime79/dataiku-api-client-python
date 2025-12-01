"""Unit tests for CatalogWriter helper methods."""

import pytest
from unittest.mock import Mock
from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
from dataikuapi.iac.workflows.discovery.models import (
    EnhancedBlockMetadata,
    BlockPort,
    BlockContents,
    RecipeDetail,
    DatasetDetail,
)


class TestCalculateComplexity:
    """Test suite for _calculate_complexity method."""

    def test_complexity_simple(self):
        """Test complexity calculation for simple blocks (< 3 recipes)."""
        writer = CatalogWriter()
        metadata = Mock(spec=EnhancedBlockMetadata)
        metadata.recipe_details = [Mock()]  # 1 recipe

        result = writer._calculate_complexity(metadata)

        assert result == "Simple"

    def test_complexity_simple_with_two_recipes(self):
        """Test complexity calculation with exactly 2 recipes."""
        writer = CatalogWriter()
        metadata = Mock(spec=EnhancedBlockMetadata)
        metadata.recipe_details = [Mock(), Mock()]  # 2 recipes

        result = writer._calculate_complexity(metadata)

        assert result == "Simple"

    def test_complexity_moderate(self):
        """Test complexity calculation for moderate blocks (3-8 recipes)."""
        writer = CatalogWriter()
        metadata = Mock(spec=EnhancedBlockMetadata)
        metadata.recipe_details = [Mock() for _ in range(5)]  # 5 recipes

        result = writer._calculate_complexity(metadata)

        assert result == "Moderate"

    def test_complexity_moderate_boundary_lower(self):
        """Test complexity calculation at lower boundary (3 recipes)."""
        writer = CatalogWriter()
        metadata = Mock(spec=EnhancedBlockMetadata)
        metadata.recipe_details = [Mock() for _ in range(3)]  # 3 recipes

        result = writer._calculate_complexity(metadata)

        assert result == "Moderate"

    def test_complexity_moderate_boundary_upper(self):
        """Test complexity calculation at upper boundary (8 recipes)."""
        writer = CatalogWriter()
        metadata = Mock(spec=EnhancedBlockMetadata)
        metadata.recipe_details = [Mock() for _ in range(8)]  # 8 recipes

        result = writer._calculate_complexity(metadata)

        assert result == "Moderate"

    def test_complexity_complex(self):
        """Test complexity calculation for complex blocks (> 8 recipes)."""
        writer = CatalogWriter()
        metadata = Mock(spec=EnhancedBlockMetadata)
        metadata.recipe_details = [Mock() for _ in range(10)]  # 10 recipes

        result = writer._calculate_complexity(metadata)

        assert result == "Complex"

    def test_complexity_complex_boundary(self):
        """Test complexity calculation at boundary (9 recipes)."""
        writer = CatalogWriter()
        metadata = Mock(spec=EnhancedBlockMetadata)
        metadata.recipe_details = [Mock() for _ in range(9)]  # 9 recipes

        result = writer._calculate_complexity(metadata)

        assert result == "Complex"

    def test_complexity_with_zero_recipes(self):
        """Test complexity calculation with no recipes."""
        writer = CatalogWriter()
        metadata = Mock(spec=EnhancedBlockMetadata)
        metadata.recipe_details = []  # 0 recipes

        result = writer._calculate_complexity(metadata)

        assert result == "Simple"


class TestEstimateDataVolume:
    """Test suite for _estimate_data_volume method."""

    def test_estimate_volume_single_dataset(self):
        """Test volume estimation with single dataset."""
        writer = CatalogWriter()
        metadata = Mock(spec=EnhancedBlockMetadata)
        metadata.dataset_details = [Mock()]  # 1 dataset

        result = writer._estimate_data_volume(metadata)

        assert result == "~1 Datasets"

    def test_estimate_volume_multiple_datasets(self):
        """Test volume estimation with multiple datasets."""
        writer = CatalogWriter()
        metadata = Mock(spec=EnhancedBlockMetadata)
        metadata.dataset_details = [Mock() for _ in range(5)]  # 5 datasets

        result = writer._estimate_data_volume(metadata)

        assert result == "~5 Datasets"

    def test_estimate_volume_no_datasets(self):
        """Test volume estimation with no datasets."""
        writer = CatalogWriter()
        metadata = Mock(spec=EnhancedBlockMetadata)
        metadata.dataset_details = []  # 0 datasets

        result = writer._estimate_data_volume(metadata)

        assert result == "~0 Datasets"

    def test_estimate_volume_with_real_metadata(self):
        """Test volume estimation with real EnhancedBlockMetadata."""
        writer = CatalogWriter()

        # Create real metadata with dataset details
        metadata = EnhancedBlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST_PROJECT",
            dataset_details=[
                DatasetDetail(
                    name="DS1",
                    type="Snowflake",
                    connection="snowflake",
                    format_type="table",
                    schema_summary={"columns": 5},
                ),
                DatasetDetail(
                    name="DS2",
                    type="Snowflake",
                    connection="snowflake",
                    format_type="table",
                    schema_summary={"columns": 3},
                ),
            ],
        )

        result = writer._estimate_data_volume(metadata)

        assert result == "~2 Datasets"


class TestGenerateQuickSummary:
    """Test suite for _generate_quick_summary method."""

    def test_generate_quick_summary_basic(self):
        """Test generating quick summary with basic metadata."""
        writer = CatalogWriter()
        metadata = Mock(spec=EnhancedBlockMetadata)
        metadata.description = "Test block"
        metadata.recipe_details = [Mock(), Mock(), Mock()]  # 3 recipes
        metadata.dataset_details = [Mock()]  # 1 dataset

        # Mock the helper method
        writer._calculate_complexity = Mock(return_value="Moderate")

        summary = writer._generate_quick_summary(metadata)

        assert "> **Quick Summary**" in summary
        assert "Test block" in summary
        assert "Moderate" in summary
        assert "**Recipes**: 3" in summary
        assert "**Datasets**: 1" in summary

    def test_generate_quick_summary_no_description(self):
        """Test generating quick summary with missing description."""
        writer = CatalogWriter()
        metadata = Mock(spec=EnhancedBlockMetadata)
        metadata.description = ""
        metadata.recipe_details = [Mock()]
        metadata.dataset_details = [Mock()]

        writer._calculate_complexity = Mock(return_value="Simple")

        summary = writer._generate_quick_summary(metadata)

        assert "No description provided." in summary

    def test_generate_quick_summary_none_description(self):
        """Test generating quick summary with None description."""
        writer = CatalogWriter()
        metadata = Mock(spec=EnhancedBlockMetadata)
        metadata.description = None
        metadata.recipe_details = []
        metadata.dataset_details = []

        writer._calculate_complexity = Mock(return_value="Simple")

        summary = writer._generate_quick_summary(metadata)

        assert "No description provided." in summary

    def test_generate_quick_summary_complex_block(self):
        """Test generating quick summary for complex block."""
        writer = CatalogWriter()
        metadata = Mock(spec=EnhancedBlockMetadata)
        metadata.description = "Complex analytics pipeline"
        metadata.recipe_details = [Mock() for _ in range(10)]  # 10 recipes
        metadata.dataset_details = [Mock() for _ in range(7)]  # 7 datasets

        writer._calculate_complexity = Mock(return_value="Complex")

        summary = writer._generate_quick_summary(metadata)

        assert "> **Quick Summary**: Complex analytics pipeline" in summary
        assert "**Complexity**: Complex" in summary
        assert "**Recipes**: 10" in summary
        assert "**Datasets**: 7" in summary

    def test_generate_quick_summary_format(self):
        """Test that quick summary has correct markdown blockquote format."""
        writer = CatalogWriter()
        metadata = Mock(spec=EnhancedBlockMetadata)
        metadata.description = "Test"
        metadata.recipe_details = [Mock()]
        metadata.dataset_details = [Mock()]

        writer._calculate_complexity = Mock(return_value="Simple")

        summary = writer._generate_quick_summary(metadata)

        # Check that it starts with blockquote
        assert summary.startswith(">")
        # Check that second line also starts with blockquote
        lines = summary.split("\n")
        assert len(lines) == 2
        assert all(line.startswith(">") for line in lines)

    def test_generate_quick_summary_with_real_metadata(self):
        """Test generating quick summary with real EnhancedBlockMetadata."""
        writer = CatalogWriter()

        metadata = EnhancedBlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST_PROJECT",
            description="Real test block",
            recipe_details=[
                RecipeDetail(
                    name="recipe1",
                    type="python",
                    engine="DSS",
                    inputs=["ds1"],
                    outputs=["ds2"],
                )
            ],
            dataset_details=[
                DatasetDetail(
                    name="DS1",
                    type="Snowflake",
                    connection="snowflake",
                    format_type="table",
                    schema_summary={"columns": 5},
                )
            ],
        )

        summary = writer._generate_quick_summary(metadata)

        assert "> **Quick Summary**: Real test block" in summary
        assert "**Complexity**: Simple" in summary  # 1 recipe = simple
        assert "**Recipes**: 1" in summary
        assert "**Datasets**: 1" in summary
