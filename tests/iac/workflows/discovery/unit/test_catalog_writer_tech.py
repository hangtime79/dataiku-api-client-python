"""Unit tests for CatalogWriter technical details generation (Phase 9)."""


class TestGenerateTechnicalDetailsSection:
    """Tests for _generate_technical_details method (P9-F001)."""

    def test_generate_technical_details_basic(self):
        """Test basic technical details section generation."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import (
            DatasetDetail,
            EnhancedBlockMetadata,
        )

        writer = CatalogWriter()
        ds = DatasetDetail(
            name="DS1",
            type="S3",
            connection="",
            format_type="",
            schema_summary={"sample": ["col1", "col2"]},
        )
        meta = EnhancedBlockMetadata(
            block_id="BLK",
            version="1.0.0",
            type="zone",
            source_project="TEST",
            dataset_details=[ds],
        )

        section = writer._generate_technical_details(meta)

        assert "## Technical Details" in section
        assert "### Dataset Schemas" in section
        assert "Schema: DS1" in section
        assert "| col1 |" in section
        assert "| col2 |" in section
        assert "BLK_DS1.schema.json" in section
        assert "<details>" in section
        assert "</details>" in section

    def test_generate_technical_details_empty(self):
        """Test technical details with no datasets."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import EnhancedBlockMetadata

        writer = CatalogWriter()
        meta = EnhancedBlockMetadata(
            block_id="BLK",
            version="1.0.0",
            type="zone",
            source_project="TEST",
            dataset_details=[],
        )

        section = writer._generate_technical_details(meta)

        assert section == ""

    def test_generate_technical_details_no_sample(self):
        """Test technical details when schema has no sample columns."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import (
            DatasetDetail,
            EnhancedBlockMetadata,
        )

        writer = CatalogWriter()
        ds = DatasetDetail(
            name="DS_NO_SAMPLE",
            type="PostgreSQL",
            connection="",
            format_type="",
            schema_summary={},  # No "sample" key
        )
        meta = EnhancedBlockMetadata(
            block_id="BLK",
            version="1.0.0",
            type="zone",
            source_project="TEST",
            dataset_details=[ds],
        )

        section = writer._generate_technical_details(meta)

        assert "Schema: DS_NO_SAMPLE" in section
        assert "BLK_DS_NO_SAMPLE.schema.json" in section
        assert "| Column | Type |" in section

    def test_generate_technical_details_multiple_datasets(self):
        """Test technical details with multiple datasets."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import (
            DatasetDetail,
            EnhancedBlockMetadata,
        )

        writer = CatalogWriter()
        datasets = [
            DatasetDetail(
                name="INPUTS",
                type="S3",
                connection="",
                format_type="",
                schema_summary={"sample": ["id", "name"]},
            ),
            DatasetDetail(
                name="OUTPUTS",
                type="Snowflake",
                connection="",
                format_type="",
                schema_summary={"sample": ["id", "prediction"]},
            ),
        ]
        meta = EnhancedBlockMetadata(
            block_id="ML_BLOCK",
            version="1.0.0",
            type="zone",
            source_project="TEST",
            dataset_details=datasets,
        )

        section = writer._generate_technical_details(meta)

        assert "Schema: INPUTS" in section
        assert "Schema: OUTPUTS" in section
        assert "| id |" in section
        assert "| name |" in section
        assert "| prediction |" in section
        assert "ML_BLOCK_INPUTS.schema.json" in section
        assert "ML_BLOCK_OUTPUTS.schema.json" in section

    def test_generate_technical_details_special_characters(self):
        """Test handling of special characters in column names."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import (
            DatasetDetail,
            EnhancedBlockMetadata,
        )

        writer = CatalogWriter()
        ds = DatasetDetail(
            name="SPECIAL",
            type="S3",
            connection="",
            format_type="",
            schema_summary={"sample": ["col_with_underscore", "col-with-dash"]},
        )
        meta = EnhancedBlockMetadata(
            block_id="BLK",
            version="1.0.0",
            type="zone",
            source_project="TEST",
            dataset_details=[ds],
        )

        section = writer._generate_technical_details(meta)

        assert "col_with_underscore" in section
        assert "col-with-dash" in section

    def test_generate_technical_details_formatting(self):
        """Test markdown formatting is correct."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import (
            DatasetDetail,
            EnhancedBlockMetadata,
        )

        writer = CatalogWriter()
        ds = DatasetDetail(
            name="FMT_TEST",
            type="S3",
            connection="",
            format_type="",
            schema_summary={"sample": ["col1"]},
        )
        meta = EnhancedBlockMetadata(
            block_id="BLK",
            version="1.0.0",
            type="zone",
            source_project="TEST",
            dataset_details=[ds],
        )

        section = writer._generate_technical_details(meta)

        # Verify markdown structure
        assert section.startswith("## Technical Details\n")
        assert "<details>\n<summary>" in section
        assert "</summary>\n" in section
        assert "| Column | Type |" in section
        assert "[Download Full Schema (JSON)]" in section
        assert section.endswith("</details>\n\n")
