"""Tests for CatalogWriter component."""

import pytest
import json
from typing import Dict, List, Any


class TestCatalogWriter:
    """Test suite for CatalogWriter class."""

    def test_create_catalog_writer(self):
        """Test creating CatalogWriter instance."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter

        writer = CatalogWriter()
        assert writer is not None

    def test_generate_wiki_article_basic(self):
        """Test generating basic wiki article from block metadata."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
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
            name="Test Block",
            description="Test description",
            inputs=[BlockPort(name="input1", type="dataset")],
            outputs=[BlockPort(name="output1", type="dataset")],
            contains=BlockContents(),
        )

        writer = CatalogWriter()
        article = writer.generate_wiki_article(metadata)

        assert "TEST_BLOCK" in article
        assert "1.0.0" in article
        assert "Test Block" in article
        assert "Test description" in article
        assert "input1" in article
        assert "output1" in article

    def test_generate_wiki_frontmatter(self):
        """Test generating YAML frontmatter."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
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
            hierarchy_level="process",
            domain="analytics",
            tags=["ml", "feature-engineering"],
            inputs=[],
            outputs=[],
            contains=BlockContents(),
        )

        writer = CatalogWriter()
        article = writer.generate_wiki_article(metadata)

        # Check frontmatter
        assert "---" in article
        assert "block_id: TEST_BLOCK" in article
        assert "version: 1.0.0" in article
        assert "hierarchy_level: process" in article
        assert "domain: analytics" in article

    def test_generate_inputs_table(self):
        """Test generating inputs table."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
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
            inputs=[
                BlockPort(
                    name="input1", type="dataset", required=True, description="Input 1"
                ),
                BlockPort(
                    name="input2",
                    type="dataset",
                    required=False,
                    description="Input 2",
                ),
            ],
            outputs=[],
            contains=BlockContents(),
        )

        writer = CatalogWriter()
        article = writer.generate_wiki_article(metadata)

        assert "## Inputs" in article
        assert "input1" in article
        assert "input2" in article
        assert "Required" in article or "required" in article

    def test_generate_usage_example(self):
        """Test generating usage example."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
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
            inputs=[BlockPort(name="input1", type="dataset")],
            outputs=[BlockPort(name="output1", type="dataset")],
            contains=BlockContents(),
        )

        writer = CatalogWriter()
        article = writer.generate_wiki_article(metadata)

        assert "## Usage" in article
        assert "```yaml" in article
        assert "blocks:" in article
        assert "ref:" in article
        assert "TEST_BLOCK@1.0.0" in article

    def test_wiki_includes_quick_summary_with_enhanced_metadata(self):
        """Test that wiki article includes quick summary for EnhancedBlockMetadata."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import (
            EnhancedBlockMetadata,
            BlockPort,
            BlockContents,
            RecipeDetail,
            DatasetDetail,
        )

        metadata = EnhancedBlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST_PROJECT",
            name="Test Block",
            description="Test enhanced block",
            inputs=[BlockPort(name="input1", type="dataset")],
            outputs=[BlockPort(name="output1", type="dataset")],
            contains=BlockContents(),
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

        writer = CatalogWriter()
        article = writer.generate_wiki_article(metadata)

        # Check that quick summary is present
        assert "> **Quick Summary**" in article
        assert "Test enhanced block" in article
        assert "**Complexity**" in article
        assert "**Recipes**" in article
        assert "**Datasets**" in article

    def test_wiki_no_quick_summary_with_basic_metadata(self):
        """Test that wiki article does NOT include quick summary for basic BlockMetadata."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
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
            name="Test Block",
            description="Basic test block",
            inputs=[BlockPort(name="input1", type="dataset")],
            outputs=[BlockPort(name="output1", type="dataset")],
            contains=BlockContents(),
        )

        writer = CatalogWriter()
        article = writer.generate_wiki_article(metadata)

        # Check that quick summary is NOT present
        assert "> **Quick Summary**" not in article
        assert "**Complexity**" not in article

    def test_wiki_quick_summary_positioned_correctly(self):
        """Test that quick summary appears after title and before description."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import (
            EnhancedBlockMetadata,
            BlockPort,
            BlockContents,
            RecipeDetail,
            DatasetDetail,
        )

        metadata = EnhancedBlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST_PROJECT",
            name="Test Block",
            description="Test description",
            inputs=[BlockPort(name="input1", type="dataset")],
            outputs=[BlockPort(name="output1", type="dataset")],
            contains=BlockContents(),
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

        writer = CatalogWriter()
        article = writer.generate_wiki_article(metadata)

        # Find positions
        title_pos = article.find("# Test Block")
        summary_pos = article.find("> **Quick Summary**")
        description_header_pos = article.find("## Description")

        # Verify ordering: title < summary < description
        assert title_pos < summary_pos, "Title should come before summary"
        assert (
            summary_pos < description_header_pos
        ), "Summary should come before description section"


class TestJSONIndex:
    """Test suite for JSON index generation."""

    def test_generate_block_summary_json(self):
        """Test generating block summary for JSON index."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
            BlockContents,
            BlockSummary,
        )

        metadata = BlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST_PROJECT",
            name="Test Block",
            inputs=[BlockPort(name="input1", type="dataset")],
            outputs=[BlockPort(name="output1", type="dataset")],
            contains=BlockContents(),
        )

        writer = CatalogWriter()
        summary_json = writer.generate_block_summary(metadata)

        # Should be valid JSON
        summary = json.loads(summary_json)
        assert summary["block_id"] == "TEST_BLOCK"
        assert summary["version"] == "1.0.0"

    def test_merge_catalog_index_new_block(self):
        """Test merging new block into catalog index."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
            BlockContents,
        )

        metadata = BlockMetadata(
            block_id="NEW_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST_PROJECT",
            inputs=[],
            outputs=[],
            contains=BlockContents(),
        )

        writer = CatalogWriter()

        # Start with existing index
        existing_index = {"blocks": []}

        # Merge new block
        updated_index = writer.merge_catalog_index(existing_index, metadata)

        assert len(updated_index["blocks"]) == 1
        assert updated_index["blocks"][0]["block_id"] == "NEW_BLOCK"

    def test_merge_catalog_index_update_existing(self):
        """Test updating existing block in catalog index."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
            BlockContents,
        )

        # Existing block in index
        existing_index = {
            "blocks": [
                {
                    "block_id": "EXISTING_BLOCK",
                    "version": "1.0.0",
                    "type": "zone",
                    "name": "Old Name",
                }
            ]
        }

        # Updated metadata
        metadata = BlockMetadata(
            block_id="EXISTING_BLOCK",
            version="2.0.0",  # New version
            type="zone",
            source_project="TEST_PROJECT",
            name="New Name",  # Updated name
            inputs=[],
            outputs=[],
            contains=BlockContents(),
        )

        writer = CatalogWriter()
        updated_index = writer.merge_catalog_index(existing_index, metadata)

        # Should still have only one entry
        assert len(updated_index["blocks"]) == 1
        # But with updated version
        assert updated_index["blocks"][0]["version"] == "2.0.0"
        assert updated_index["blocks"][0]["name"] == "New Name"


class TestSchemaFiles:
    """Test suite for schema file generation."""

    def test_generate_schema_file_content(self):
        """Test generating schema file content."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter

        schema = {
            "format_version": "1.0",
            "columns": [
                {"name": "ID", "type": "integer", "nullable": False},
                {"name": "VALUE", "type": "double", "nullable": True},
            ],
        }

        writer = CatalogWriter()
        schema_content = writer.generate_schema_file(schema)

        # Should be valid JSON
        parsed = json.loads(schema_content)
        assert parsed["format_version"] == "1.0"
        assert len(parsed["columns"]) == 2

    def test_generate_schema_file_pretty_printed(self):
        """Test schema file is pretty-printed."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter

        schema = {"format_version": "1.0", "columns": []}

        writer = CatalogWriter()
        schema_content = writer.generate_schema_file(schema)

        # Should have indentation (pretty-printed)
        assert "  " in schema_content or "\t" in schema_content


class TestManualEditPreservation:
    """Test suite for preserving manual edits."""

    def test_extract_changelog_from_existing_article(self):
        """Test extracting changelog section from existing article."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter

        existing_article = """
# Test Block

## Description
Test description

## Changelog

- 2.0.0: Added new feature
- 1.0.0: Initial release
"""

        writer = CatalogWriter()
        changelog = writer.extract_changelog(existing_article)

        assert "2.0.0" in changelog
        assert "1.0.0" in changelog

    def test_merge_with_existing_article_preserves_changelog(self):
        """Test merging preserves existing changelog."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockPort,
            BlockContents,
        )

        existing_article = """
---
block_id: TEST_BLOCK
version: 1.0.0
---

# Test Block

## Description
Old description

## Changelog

- 1.0.0: Initial release
"""

        metadata = BlockMetadata(
            block_id="TEST_BLOCK",
            version="2.0.0",
            type="zone",
            source_project="TEST_PROJECT",
            description="New description",
            inputs=[],
            outputs=[],
            contains=BlockContents(),
        )

        writer = CatalogWriter()
        merged = writer.merge_wiki_article(existing_article, metadata)

        # Should have new version metadata
        assert "2.0.0" in merged
        # Should preserve old changelog
        assert "1.0.0: Initial release" in merged


class TestHierarchyOrganization:
    """Test suite for hierarchy-based organization."""

    def test_get_wiki_path_by_hierarchy(self):
        """Test generating wiki path based on hierarchy level."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockContents,
        )

        metadata = BlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST_PROJECT",
            hierarchy_level="process",
            inputs=[],
            outputs=[],
            contains=BlockContents(),
        )

        writer = CatalogWriter()
        path = writer.get_wiki_path(metadata)

        assert "process" in path.lower()

    def test_get_wiki_path_default_hierarchy(self):
        """Test wiki path for block without hierarchy level."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockContents,
        )

        metadata = BlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST_PROJECT",
            hierarchy_level="",  # No hierarchy
            inputs=[],
            outputs=[],
            contains=BlockContents(),
        )

        writer = CatalogWriter()
        path = writer.get_wiki_path(metadata)

        # Should have default path
        assert "TEST_BLOCK" in path


class TestErrorHandling:
    """Test suite for error handling."""

    def test_handle_invalid_block_metadata(self):
        """Test handling invalid block metadata."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.exceptions import CatalogWriteError

        writer = CatalogWriter()

        # Invalid metadata (None)
        with pytest.raises((CatalogWriteError, AttributeError, TypeError)):
            writer.generate_wiki_article(None)

    def test_handle_malformed_existing_article(self):
        """Test handling malformed existing article during merge."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import (
            BlockMetadata,
            BlockContents,
        )

        metadata = BlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST_PROJECT",
            inputs=[],
            outputs=[],
            contains=BlockContents(),
        )

        writer = CatalogWriter()

        # Malformed article (no structure)
        malformed = "This is not a valid article format"

        # Should handle gracefully - either merge or regenerate
        result = writer.merge_wiki_article(malformed, metadata)
        assert result is not None
        assert "TEST_BLOCK" in result

    def test_wiki_includes_components(self):
        """Test that wiki article includes Internal Components section (P7-F004)."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import (
            EnhancedBlockMetadata,
            BlockContents,
            DatasetDetail,
            RecipeDetail,
            LibraryReference,
            NotebookReference,
        )

        writer = CatalogWriter()

        # Create EnhancedBlockMetadata with all component details
        metadata = EnhancedBlockMetadata(
            block_id="TEST_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST_PROJECT",
            inputs=[],
            outputs=[],
            contains=BlockContents(),
            dataset_details=[
                DatasetDetail(
                    name="DS1",
                    type="S3",
                    connection="s3-conn",
                    format_type="parquet",
                    schema_summary={"columns": 5},
                )
            ],
            recipe_details=[
                RecipeDetail(
                    name="compute_metrics",
                    type="python",
                    engine="DSS",
                    inputs=["DS1"],
                    outputs=["DS2"],
                )
            ],
            library_refs=[LibraryReference(name="utils.py", type="python")],
            notebook_refs=[NotebookReference(name="Analysis", type="jupyter")],
        )

        article = writer.generate_wiki_article(metadata)

        # Verify components section appears
        assert "## Internal Components" in article
        assert "### Datasets" in article
        assert "### Recipes" in article
        assert "### Project Libraries" in article
        assert "### Notebooks" in article

        # Verify specific component content
        assert "DS1" in article
        assert "compute_metrics" in article
        assert "utils.py" in article
        assert "Analysis" in article
