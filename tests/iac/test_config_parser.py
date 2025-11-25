"""
Tests for configuration parser.
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from dataikuapi.iac.config.parser import ConfigParser
from dataikuapi.iac.config.models import Config, ProjectConfig, DatasetConfig, RecipeConfig
from dataikuapi.iac.exceptions import ConfigParseError


class TestConfigParser:
    """Tests for ConfigParser class."""

    def test_parse_simple_config(self, tmp_path):
        """Test parsing simple configuration file."""
        config_file = tmp_path / "simple.yml"
        config_file.write_text("""
version: "1.0"

metadata:
  description: "Simple test project"

project:
  key: TEST_PROJECT
  name: Test Project
  description: A simple test project

datasets:
  - name: TEST_DATASET
    type: managed
    format_type: parquet

recipes:
  - name: prep_data
    type: python
    inputs: [TEST_DATASET]
    outputs: [PREPPED_DATA]
    code: |
      # Simple transformation
      output = input
""")

        parser = ConfigParser()
        config = parser.parse_file(config_file)

        assert config.version == "1.0"
        assert config.project.key == "TEST_PROJECT"
        assert config.project.name == "Test Project"
        assert len(config.datasets) == 1
        assert config.datasets[0].name == "TEST_DATASET"
        assert config.datasets[0].type == "managed"
        assert len(config.recipes) == 1
        assert config.recipes[0].name == "prep_data"

    def test_parse_complete_config(self, tmp_path):
        """Test parsing complete configuration with all fields."""
        config_file = tmp_path / "complete.yml"
        config_file.write_text("""
version: "1.0"

metadata:
  description: "Complete test project"
  owner: data_team
  tags:
    - test
    - complete

project:
  key: COMPLETE_PROJECT
  name: Complete Test Project
  description: A complete test project
  settings:
    git:
      enabled: true
      remote: git@github.com:test/test.git

datasets:
  - name: RAW_CUSTOMERS
    type: sql
    connection: my_snowflake
    params:
      schema: PUBLIC
      table: customers
      mode: table
    schema:
      columns:
        - name: customer_id
          type: bigint
        - name: name
          type: varchar

  - name: PREPARED_CUSTOMERS
    type: managed
    format_type: parquet

recipes:
  - name: prep_customers
    type: python
    inputs:
      - RAW_CUSTOMERS
    outputs:
      - PREPARED_CUSTOMERS
    params:
      containerSelection:
        containerMode: INHERIT
    code: |
      import dataiku
      df = dataiku.Dataset("RAW_CUSTOMERS").get_dataframe()
      df_clean = df.dropna()
      df_clean.to_csv("PREPARED_CUSTOMERS")

  - name: aggregate_customers
    type: grouping
    inputs:
      - PREPARED_CUSTOMERS
    outputs:
      - AGGREGATED_CUSTOMERS
    params:
      keys:
        - column: customer_id
      values:
        - column: amount
          aggregation: sum
""")

        parser = ConfigParser()
        config = parser.parse_file(config_file)

        assert config.version == "1.0"
        assert config.metadata["owner"] == "data_team"
        assert len(config.metadata["tags"]) == 2
        assert config.project.key == "COMPLETE_PROJECT"
        assert config.project.settings["git"]["enabled"] is True
        assert len(config.datasets) == 2
        assert config.datasets[0].connection == "my_snowflake"
        assert config.datasets[0].params["schema"] == "PUBLIC"
        assert len(config.recipes) == 2
        assert config.recipes[0].code is not None
        assert "import dataiku" in config.recipes[0].code

    def test_parse_file_not_found(self):
        """Test error when file doesn't exist."""
        parser = ConfigParser()

        with pytest.raises(ConfigParseError) as exc_info:
            parser.parse_file("/nonexistent/file.yml")

        assert "not found" in str(exc_info.value).lower()

    def test_parse_invalid_yaml(self, tmp_path):
        """Test error when YAML is malformed."""
        config_file = tmp_path / "invalid.yml"
        config_file.write_text("""
project:
  key: TEST
  name: Test
  invalid: [unclosed bracket
""")

        parser = ConfigParser()

        with pytest.raises(ConfigParseError) as exc_info:
            parser.parse_file(config_file)

        assert "invalid yaml" in str(exc_info.value).lower()

    def test_parse_empty_file(self, tmp_path):
        """Test error when file is empty."""
        config_file = tmp_path / "empty.yml"
        config_file.write_text("")

        parser = ConfigParser()

        with pytest.raises(ConfigParseError) as exc_info:
            parser.parse_file(config_file)

        assert "empty" in str(exc_info.value).lower()

    def test_parse_non_dict_yaml(self, tmp_path):
        """Test error when YAML is not a dict."""
        config_file = tmp_path / "list.yml"
        config_file.write_text("- item1\n- item2")

        parser = ConfigParser()

        with pytest.raises(ConfigParseError) as exc_info:
            parser.parse_file(config_file)

        assert "expected dict" in str(exc_info.value).lower()

    def test_parse_missing_required_field(self, tmp_path):
        """Test error when required field is missing."""
        config_file = tmp_path / "missing_field.yml"
        config_file.write_text("""
project:
  name: Test Project
  # Missing 'key' field
""")

        parser = ConfigParser()

        with pytest.raises(ConfigParseError) as exc_info:
            parser.parse_file(config_file)

        assert "missing required field" in str(exc_info.value).lower() or "key" in str(exc_info.value).lower()

    def test_parse_directory(self, tmp_path):
        """Test parsing directory-based configuration."""
        # Create directory structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Create project.yml
        project_file = config_dir / "project.yml"
        project_file.write_text("""
version: "1.0"
project:
  key: DIR_PROJECT
  name: Directory Project
  description: Project from directory
""")

        # Create datasets directory
        datasets_dir = config_dir / "datasets"
        datasets_dir.mkdir()

        dataset1 = datasets_dir / "dataset1.yml"
        dataset1.write_text("""
datasets:
  - name: DATASET_1
    type: managed
    format_type: parquet
""")

        dataset2 = datasets_dir / "dataset2.yml"
        dataset2.write_text("""
datasets:
  - name: DATASET_2
    type: sql
    connection: my_connection
""")

        # Create recipes directory
        recipes_dir = config_dir / "recipes"
        recipes_dir.mkdir()

        recipe1 = recipes_dir / "recipe1.yml"
        recipe1.write_text("""
recipes:
  - name: prep_recipe
    type: python
    inputs: [DATASET_1]
    outputs: [DATASET_2]
""")

        # Parse directory
        parser = ConfigParser()
        config = parser.parse_directory(config_dir)

        assert config.project.key == "DIR_PROJECT"
        assert len(config.datasets) == 2
        assert config.datasets[0].name == "DATASET_1"
        assert config.datasets[1].name == "DATASET_2"
        assert len(config.recipes) == 1
        assert config.recipes[0].name == "prep_recipe"

    def test_parse_directory_no_project_yml(self, tmp_path):
        """Test error when directory has no project.yml."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        parser = ConfigParser()

        with pytest.raises(ConfigParseError) as exc_info:
            parser.parse_directory(config_dir)

        assert "project.yml not found" in str(exc_info.value).lower()

    def test_parse_directory_not_found(self):
        """Test error when directory doesn't exist."""
        parser = ConfigParser()

        with pytest.raises(ConfigParseError) as exc_info:
            parser.parse_directory("/nonexistent/directory")

        assert "not found" in str(exc_info.value).lower()

    def test_parse_directory_is_file(self, tmp_path):
        """Test error when directory path is actually a file."""
        file_path = tmp_path / "notadir.txt"
        file_path.write_text("content")

        parser = ConfigParser()

        with pytest.raises(ConfigParseError) as exc_info:
            parser.parse_directory(file_path)

        assert "not a directory" in str(exc_info.value).lower()

    def test_parse_directory_optional_subdirs(self, tmp_path):
        """Test directory parsing works without datasets/ and recipes/."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        project_file = config_dir / "project.yml"
        project_file.write_text("""
version: "1.0"
project:
  key: MINIMAL_PROJECT
  name: Minimal Project
""")

        parser = ConfigParser()
        config = parser.parse_directory(config_dir)

        assert config.project.key == "MINIMAL_PROJECT"
        assert len(config.datasets) == 0
        assert len(config.recipes) == 0

    def test_parse_file_is_directory(self, tmp_path):
        """Test error when parse_file given a directory."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        parser = ConfigParser()

        with pytest.raises(ConfigParseError) as exc_info:
            parser.parse_file(config_dir)

        assert "not a file" in str(exc_info.value).lower()

    def test_parse_with_default_version(self, tmp_path):
        """Test that version defaults to 1.0 if not specified."""
        config_file = tmp_path / "no_version.yml"
        config_file.write_text("""
project:
  key: TEST
  name: Test
""")

        parser = ConfigParser()
        config = parser.parse_file(config_file)

        assert config.version == "1.0"

    def test_parse_empty_datasets_and_recipes(self, tmp_path):
        """Test parsing config with no datasets or recipes."""
        config_file = tmp_path / "project_only.yml"
        config_file.write_text("""
project:
  key: PROJECT_ONLY
  name: Project Only
""")

        parser = ConfigParser()
        config = parser.parse_file(config_file)

        assert config.project.key == "PROJECT_ONLY"
        assert len(config.datasets) == 0
        assert len(config.recipes) == 0

    def test_parse_preserves_metadata(self, tmp_path):
        """Test that metadata is preserved correctly."""
        config_file = tmp_path / "with_metadata.yml"
        config_file.write_text("""
version: "1.0"
metadata:
  description: "Test metadata"
  owner: data_team
  custom_field: custom_value

project:
  key: TEST
  name: Test
""")

        parser = ConfigParser()
        config = parser.parse_file(config_file)

        assert config.metadata["description"] == "Test metadata"
        assert config.metadata["owner"] == "data_team"
        assert config.metadata["custom_field"] == "custom_value"

    def test_from_dict_with_minimal_data(self):
        """Test Config.from_dict with minimal valid data."""
        data = {
            "project": {
                "key": "MINIMAL",
                "name": "Minimal"
            }
        }

        config = Config.from_dict(data)

        assert config.project.key == "MINIMAL"
        assert config.project.name == "Minimal"
        assert config.project.description == ""
        assert len(config.datasets) == 0
        assert len(config.recipes) == 0

    def test_parse_directory_with_yaml_extension(self, tmp_path):
        """Test directory parsing handles both .yml and .yaml extensions."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        project_file = config_dir / "project.yml"
        project_file.write_text("""
project:
  key: TEST
  name: Test
""")

        datasets_dir = config_dir / "datasets"
        datasets_dir.mkdir()

        # Mix .yml and .yaml extensions
        dataset1 = datasets_dir / "ds1.yml"
        dataset1.write_text("""
datasets:
  - name: DS1
    type: managed
""")

        dataset2 = datasets_dir / "ds2.yaml"
        dataset2.write_text("""
datasets:
  - name: DS2
    type: managed
""")

        parser = ConfigParser()
        config = parser.parse_directory(config_dir)

        assert len(config.datasets) == 2
        dataset_names = {ds.name for ds in config.datasets}
        assert "DS1" in dataset_names
        assert "DS2" in dataset_names
