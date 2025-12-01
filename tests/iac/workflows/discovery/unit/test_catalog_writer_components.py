"""Unit tests for CatalogWriter component generation methods (Phase 7)."""


class TestDatasetSection:
    """Tests for _generate_datasets_section method (P7-F001)."""

    def test_generate_datasets_section(self):
        """Test basic datasets section generation."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import DatasetDetail

        writer = CatalogWriter()
        ds = DatasetDetail(
            name="DS1",
            type="S3",
            connection="my-s3",
            format_type="parquet",
            schema_summary={"columns": 5},
        )

        section = writer._generate_datasets_section([ds])

        assert "<details>" in section
        assert "DS1" in section
        assert "5 columns" in section
        assert "S3" in section

    def test_generate_datasets_section_empty(self):
        """Test datasets section with empty list."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter

        writer = CatalogWriter()
        section = writer._generate_datasets_section([])

        assert section == ""

    def test_generate_datasets_section_with_description(self):
        """Test datasets section includes description."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import DatasetDetail

        writer = CatalogWriter()
        ds = DatasetDetail(
            name="CUSTOMERS",
            type="PostgreSQL",
            connection="pg-conn",
            format_type="table",
            schema_summary={"columns": 10},
            description="Customer master data",
        )

        section = writer._generate_datasets_section([ds])

        assert "CUSTOMERS" in section
        assert "Customer master data" in section
        assert "10 columns" in section

    def test_generate_datasets_section_with_tags(self):
        """Test datasets section includes tags."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import DatasetDetail

        writer = CatalogWriter()
        ds = DatasetDetail(
            name="SALES",
            type="Snowflake",
            connection="snowflake",
            format_type="table",
            schema_summary={"columns": 15},
            tags=["pii", "financial"],
        )

        section = writer._generate_datasets_section([ds])

        assert "SALES" in section
        assert "pii" in section
        assert "financial" in section
        assert "**Tags**" in section

    def test_generate_datasets_section_multiple_datasets(self):
        """Test datasets section with multiple datasets."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import DatasetDetail

        writer = CatalogWriter()
        datasets = [
            DatasetDetail(
                name="DS1",
                type="S3",
                connection="s3",
                format_type="csv",
                schema_summary={"columns": 5},
            ),
            DatasetDetail(
                name="DS2",
                type="PostgreSQL",
                connection="pg",
                format_type="table",
                schema_summary={"columns": 8},
            ),
        ]

        section = writer._generate_datasets_section(datasets)

        assert "2 internal datasets" in section
        assert "DS1" in section
        assert "DS2" in section
        assert "5 columns" in section
        assert "8 columns" in section

    def test_generate_datasets_section_no_description(self):
        """Test datasets section handles missing description."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import DatasetDetail

        writer = CatalogWriter()
        ds = DatasetDetail(
            name="DS_NO_DESC",
            type="S3",
            connection="s3",
            format_type="parquet",
            schema_summary={"columns": 3},
            description=None,
        )

        section = writer._generate_datasets_section([ds])

        assert "DS_NO_DESC" in section
        assert "No description" in section


class TestRecipeSection:
    """Tests for _generate_recipes_section method (P7-F002)."""

    def test_generate_recipes_section(self):
        """Test basic recipes section generation."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import RecipeDetail

        writer = CatalogWriter()
        rc = RecipeDetail(
            name="compute_X",
            type="python",
            engine="DSS",
            inputs=["A"],
            outputs=["B"],
            code_snippet="print('hi')",
        )

        section = writer._generate_recipes_section([rc])

        assert "compute_X" in section
        assert "print('hi')" in section
        assert "```python" in section

    def test_generate_recipes_section_empty(self):
        """Test recipes section with empty list."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter

        writer = CatalogWriter()
        section = writer._generate_recipes_section([])

        assert section == ""

    def test_generate_recipes_section_no_code(self):
        """Test recipes section without code snippet."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import RecipeDetail

        writer = CatalogWriter()
        rc = RecipeDetail(
            name="join_recipe",
            type="join",
            engine="DSS",
            inputs=["customers", "orders"],
            outputs=["customer_orders"],
            code_snippet=None,
        )

        section = writer._generate_recipes_section([rc])

        assert "join_recipe" in section
        assert "customers, orders" in section
        assert "customer_orders" in section
        assert "```python" not in section

    def test_generate_recipes_section_multiple_inputs_outputs(self):
        """Test recipes section with multiple inputs and outputs."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import RecipeDetail

        writer = CatalogWriter()
        rc = RecipeDetail(
            name="aggregate",
            type="python",
            engine="DSS",
            inputs=["sales", "products", "stores"],
            outputs=["sales_summary", "product_summary"],
        )

        section = writer._generate_recipes_section([rc])

        assert "aggregate" in section
        assert "sales, products, stores" in section
        assert "sales_summary, product_summary" in section
        assert "**Inputs**" in section
        assert "**Outputs**" in section

    def test_generate_recipes_section_multiple_recipes(self):
        """Test recipes section with multiple recipes."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import RecipeDetail

        writer = CatalogWriter()
        recipes = [
            RecipeDetail(
                name="recipe1",
                type="python",
                engine="DSS",
                inputs=["A"],
                outputs=["B"],
            ),
            RecipeDetail(
                name="recipe2",
                type="sql",
                engine="PostgreSQL",
                inputs=["C"],
                outputs=["D"],
            ),
        ]

        section = writer._generate_recipes_section(recipes)

        assert "2 recipes" in section
        assert "recipe1" in section
        assert "recipe2" in section
        assert "python" in section
        assert "sql" in section

    def test_generate_recipes_section_with_code_snippet(self):
        """Test recipes section includes code snippet with proper formatting."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import RecipeDetail

        writer = CatalogWriter()
        rc = RecipeDetail(
            name="transform",
            type="python",
            engine="DSS",
            inputs=["raw_data"],
            outputs=["clean_data"],
            code_snippet="df['clean'] = df['raw'].str.strip()",
        )

        section = writer._generate_recipes_section([rc])

        assert "transform" in section
        assert "**Logic Preview**" in section
        assert "```python" in section
        assert "df['clean'] = df['raw'].str.strip()" in section


class TestRefSections:
    """Tests for _generate_libraries_section and _generate_notebooks_section methods (P7-F003)."""

    def test_generate_refs_sections(self):
        """Test basic libraries and notebooks section generation."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import (
            LibraryReference,
            NotebookReference,
        )

        writer = CatalogWriter()
        libs = [LibraryReference(name="utils.py", type="python")]
        nbs = [NotebookReference(name="EDA", type="jupyter")]

        lib_section = writer._generate_libraries_section(libs)
        nb_section = writer._generate_notebooks_section(nbs)

        assert "utils.py" in lib_section
        assert "EDA" in nb_section

    def test_generate_libraries_section_empty(self):
        """Test libraries section with empty list."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter

        writer = CatalogWriter()
        section = writer._generate_libraries_section([])

        assert section == ""

    def test_generate_notebooks_section_empty(self):
        """Test notebooks section with empty list."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter

        writer = CatalogWriter()
        section = writer._generate_notebooks_section([])

        assert section == ""

    def test_generate_libraries_section_multiple(self):
        """Test libraries section with multiple libraries."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import LibraryReference

        writer = CatalogWriter()
        libs = [
            LibraryReference(name="utils.py", type="python"),
            LibraryReference(name="helpers.R", type="R"),
            LibraryReference(name="config.json", type="resource"),
        ]

        section = writer._generate_libraries_section(libs)

        assert "### Project Libraries" in section
        assert "utils.py" in section
        assert "helpers.R" in section
        assert "config.json" in section
        assert "python" in section
        assert "R" in section
        assert "resource" in section

    def test_generate_notebooks_section_multiple(self):
        """Test notebooks section with multiple notebooks."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import NotebookReference

        writer = CatalogWriter()
        nbs = [
            NotebookReference(name="EDA", type="jupyter"),
            NotebookReference(name="Analysis", type="sql"),
        ]

        section = writer._generate_notebooks_section(nbs)

        assert "### Notebooks" in section
        assert "EDA" in section
        assert "Analysis" in section
        assert "jupyter" in section
        assert "sql" in section

    def test_generate_libraries_section_formatting(self):
        """Test libraries section has proper markdown formatting."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import LibraryReference

        writer = CatalogWriter()
        libs = [LibraryReference(name="script.py", type="python")]

        section = writer._generate_libraries_section(libs)

        assert section.startswith("### Project Libraries")
        assert "`script.py`" in section
        assert "- " in section

    def test_generate_notebooks_section_formatting(self):
        """Test notebooks section has proper markdown formatting."""
        from dataikuapi.iac.workflows.discovery.catalog_writer import CatalogWriter
        from dataikuapi.iac.workflows.discovery.models import NotebookReference

        writer = CatalogWriter()
        nbs = [NotebookReference(name="notebook.ipynb", type="jupyter")]

        section = writer._generate_notebooks_section(nbs)

        assert section.startswith("### Notebooks")
        assert "`notebook.ipynb`" in section
        assert "- " in section
