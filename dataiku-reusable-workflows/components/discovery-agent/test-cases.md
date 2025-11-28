# Discovery Agent Test Cases

## Test Organization

Tests are organized into:
1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test components working together
3. **End-to-End Tests** - Test full discovery workflow against real/mock Dataiku

---

## Unit Tests

### Test Suite: BlockIdentifier

#### Test: identify_blocks_empty_project

```python
def test_identify_blocks_empty_project():
    """Empty project should return no block candidates."""
    # Arrange
    project_data = ProjectData(
        project_key="EMPTY_PROJECT",
        name="Empty",
        description="",
        tags=[],
        datasets={},
        recipes={},
        zones={},
        saved_models=[]
    )

    # Act
    identifier = BlockIdentifier()
    candidates = identifier.identify_blocks(project_data)

    # Assert
    assert len(candidates) == 0
```

#### Test: identify_blocks_single_valid_zone

```python
def test_identify_blocks_single_valid_zone():
    """Zone with clear inputs/outputs should be valid candidate."""
    # Arrange
    project_data = ProjectData(
        project_key="TEST_PROJECT",
        name="Test",
        description="",
        tags=[],
        datasets={
            "INPUT_DS": DatasetInfo(
                name="INPUT_DS",
                type="PostgreSQL",
                zone="zone1",
                schema=None,
                settings={},
                upstream_recipes=[],
                downstream_recipes=["recipe1"]
            ),
            "OUTPUT_DS": DatasetInfo(
                name="OUTPUT_DS",
                type="Filesystem",
                zone="zone1",
                schema=None,
                settings={},
                upstream_recipes=["recipe1"],
                downstream_recipes=[]
            )
        },
        recipes={
            "recipe1": RecipeInfo(
                name="recipe1",
                type="python",
                zone="zone1",
                inputs=["INPUT_DS"],
                outputs=["OUTPUT_DS"],
                settings={},
                code=None
            )
        },
        zones={
            "zone1": ZoneInfo(
                id="zone1",
                name="Data Preparation",
                datasets=["INPUT_DS", "OUTPUT_DS"],
                recipes=["recipe1"],
                color="#2ab1ac"
            )
        },
        saved_models=[]
    )

    # Act
    identifier = BlockIdentifier()
    candidates = identifier.identify_blocks(project_data)

    # Assert
    assert len(candidates) == 1
    assert candidates[0].zone.name == "Data Preparation"
    assert candidates[0].boundary.is_valid == True
    assert "INPUT_DS" in candidates[0].boundary.inputs
    assert "OUTPUT_DS" in candidates[0].boundary.outputs
```

#### Test: identify_blocks_zone_no_outputs

```python
def test_identify_blocks_zone_no_outputs():
    """Zone with no outputs should be invalid candidate."""
    # Arrange
    project_data = ProjectData(
        project_key="TEST_PROJECT",
        name="Test",
        description="",
        tags=[],
        datasets={
            "INPUT_DS": DatasetInfo(
                name="INPUT_DS",
                type="PostgreSQL",
                zone="zone1",
                schema=None,
                settings={},
                upstream_recipes=[],
                downstream_recipes=["recipe1"]
            ),
            "INTERNAL_DS": DatasetInfo(
                name="INTERNAL_DS",
                type="Filesystem",
                zone="zone1",
                schema=None,
                settings={},
                upstream_recipes=["recipe1"],
                downstream_recipes=["recipe2"]
            )
        },
        recipes={
            "recipe1": RecipeInfo(
                name="recipe1",
                type="python",
                zone="zone1",
                inputs=["INPUT_DS"],
                outputs=["INTERNAL_DS"],
                settings={},
                code=None
            ),
            "recipe2": RecipeInfo(
                name="recipe2",
                type="python",
                zone="zone1",
                inputs=["INTERNAL_DS"],
                outputs=[],  # No outputs
                settings={},
                code=None
            )
        },
        zones={
            "zone1": ZoneInfo(
                id="zone1",
                name="Dead End Zone",
                datasets=["INPUT_DS", "INTERNAL_DS"],
                recipes=["recipe1", "recipe2"],
                color="#2ab1ac"
            )
        },
        saved_models=[]
    )

    # Act
    identifier = BlockIdentifier()
    candidates = identifier.identify_blocks(project_data)

    # Assert
    assert len(candidates) == 1
    assert candidates[0].boundary.is_valid == False
    assert "must have at least one" in candidates[0].boundary.validation_error.lower()
```

#### Test: identify_blocks_multiple_zones

```python
def test_identify_blocks_multiple_zones():
    """Multiple valid zones should all become candidates."""
    # Arrange
    # ... setup project_data with 3 zones, 2 valid, 1 invalid

    # Act
    identifier = BlockIdentifier()
    candidates = identifier.identify_blocks(project_data)

    # Assert
    assert len(candidates) == 3
    valid_count = sum(1 for c in candidates if c.boundary.is_valid)
    assert valid_count == 2
```

---

### Test Suite: MetadataExtractor

#### Test: generate_block_id_simple

```python
def test_generate_block_id_simple():
    """Simple zone name should convert to uppercase with underscores."""
    # Arrange
    extractor = MetadataExtractor(DiscoveryConfig(
        hierarchy_level="equipment",
        domain="general"
    ))

    # Act
    block_id = extractor._generate_block_id("feature engineering")

    # Assert
    assert block_id == "FEATURE_ENGINEERING"
```

#### Test: generate_block_id_special_chars

```python
def test_generate_block_id_special_chars():
    """Special characters should be removed."""
    # Arrange
    extractor = MetadataExtractor(DiscoveryConfig(
        hierarchy_level="equipment",
        domain="general"
    ))

    # Act
    block_id = extractor._generate_block_id("Feature-Eng (v2.0)")

    # Assert
    assert block_id == "FEATURE_ENG_V20"
```

#### Test: generate_block_id_truncation

```python
def test_generate_block_id_truncation():
    """Long names should be truncated to 64 chars."""
    # Arrange
    extractor = MetadataExtractor(DiscoveryConfig(
        hierarchy_level="equipment",
        domain="general"
    ))
    long_name = "a" * 100

    # Act
    block_id = extractor._generate_block_id(long_name)

    # Assert
    assert len(block_id) == 64
```

#### Test: extract_port_metadata_with_schema

```python
def test_extract_port_metadata_with_schema():
    """Port metadata should include normalized schema."""
    # Arrange
    config = DiscoveryConfig(
        hierarchy_level="equipment",
        domain="general",
        extract_schemas=True
    )
    extractor = MetadataExtractor(config)

    dataset_info = DatasetInfo(
        name="MY_DATASET",
        type="PostgreSQL",
        zone="zone1",
        schema={
            "columns": [
                {"name": "id", "type": "bigint", "notNull": True},
                {"name": "value", "type": "double"},
                {"name": "label", "type": "string", "comment": "Category label"}
            ]
        },
        settings={"description": "Test dataset"},
        upstream_recipes=[],
        downstream_recipes=[]
    )

    # Act
    port = extractor._extract_port_metadata(dataset_info, required=True)

    # Assert
    assert port.name == "MY_DATASET"
    assert port.type == PortType.DATASET
    assert port.required == True
    assert port.schema is not None
    assert len(port.schema["columns"]) == 3
    assert port.schema["columns"][0]["type"] == "integer"  # Mapped from bigint
    assert port.schema["columns"][0]["nullable"] == False
    assert port.schema["columns"][2]["description"] == "Category label"
```

#### Test: parse_python_imports

```python
def test_parse_python_imports():
    """Should extract non-stdlib imports from Python code."""
    # Arrange
    extractor = MetadataExtractor(DiscoveryConfig(
        hierarchy_level="equipment",
        domain="general"
    ))

    code = '''
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
import os
import custom_module
from mypackage.submodule import helper
'''

    # Act
    imports = extractor._parse_python_imports(code)

    # Assert
    assert "pandas" in imports
    assert "numpy" in imports
    assert "sklearn" in imports
    assert "custom_module" in imports
    assert "mypackage" in imports
    # Standard library should be excluded
    assert "datetime" not in imports
    assert "os" not in imports
```

#### Test: extract_metadata_full

```python
def test_extract_metadata_full():
    """Full metadata extraction should populate all fields."""
    # Arrange
    config = DiscoveryConfig(
        hierarchy_level="equipment",
        domain="rotating_equipment",
        version="1.0.0",
        blocked=True,
        tags=["compressor", "vibration"]
    )
    extractor = MetadataExtractor(config)

    candidate = BlockCandidate(
        zone=ZoneInfo(
            id="zone1",
            name="Feature Engineering",
            datasets=["INPUT_DATA", "FEATURES"],
            recipes=["compute_features"],
            color="#2ab1ac"
        ),
        boundary=ZoneBoundary(
            inputs=["INPUT_DATA"],
            outputs=["FEATURES"],
            internals=[],
            is_valid=True
        )
    )

    project_data = ProjectData(
        project_key="COMPRESSOR_PROJECT",
        name="Compressor Analytics",
        description="",
        tags=[],
        datasets={
            "INPUT_DATA": DatasetInfo(
                name="INPUT_DATA",
                type="PostgreSQL",
                zone="zone1",
                schema={"columns": [{"name": "sensor_id", "type": "string"}]},
                settings={},
                upstream_recipes=[],
                downstream_recipes=["compute_features"]
            ),
            "FEATURES": DatasetInfo(
                name="FEATURES",
                type="Filesystem",
                zone="zone1",
                schema={"columns": [{"name": "feature_1", "type": "double"}]},
                settings={},
                upstream_recipes=["compute_features"],
                downstream_recipes=[]
            )
        },
        recipes={
            "compute_features": RecipeInfo(
                name="compute_features",
                type="python",
                zone="zone1",
                inputs=["INPUT_DATA"],
                outputs=["FEATURES"],
                settings={},
                code="import pandas as pd\nimport numpy as np"
            )
        },
        zones={
            "zone1": ZoneInfo(
                id="zone1",
                name="Feature Engineering",
                datasets=["INPUT_DATA", "FEATURES"],
                recipes=["compute_features"],
                color="#2ab1ac"
            )
        },
        saved_models=[]
    )

    # Act
    metadata = extractor.extract_metadata(candidate, project_data)

    # Assert
    assert metadata.block_id == "FEATURE_ENGINEERING"
    assert metadata.version == "1.0.0"
    assert metadata.type == BlockType.ZONE
    assert metadata.blocked == True
    assert metadata.source_project == "COMPRESSOR_PROJECT"
    assert metadata.source_zone == "Feature Engineering"
    assert metadata.hierarchy_level == "equipment"
    assert metadata.domain == "rotating_equipment"
    assert "compressor" in metadata.tags

    assert len(metadata.inputs) == 1
    assert metadata.inputs[0].name == "INPUT_DATA"

    assert len(metadata.outputs) == 1
    assert metadata.outputs[0].name == "FEATURES"

    assert "compute_features" in metadata.contains.recipes
    assert "pandas" in metadata.dependencies.python
    assert "numpy" in metadata.dependencies.python
```

---

### Test Suite: CatalogWriter

#### Test: generate_wiki_content

```python
def test_generate_wiki_content():
    """Wiki content should have all required sections."""
    # Arrange
    writer = CatalogWriter.__new__(CatalogWriter)  # Skip __init__

    block = BlockMetadata(
        block_id="TEST_BLOCK",
        version="1.0.0",
        type=BlockType.ZONE,
        blocked=False,
        source_project="SOURCE_PROJECT",
        source_zone="Test Zone",
        hierarchy_level="equipment",
        domain="general",
        tags=["test"],
        name="Test Block",
        description="A test block",
        inputs=[
            BlockPort(name="INPUT1", type=PortType.DATASET, required=True)
        ],
        outputs=[
            BlockPort(name="OUTPUT1", type=PortType.DATASET)
        ],
        contains=BlockContents(datasets=["INTERNAL"], recipes=["recipe1"]),
        dependencies=Dependencies(python=["pandas"])
    )

    # Act
    content = writer._generate_wiki_content(block)

    # Assert
    assert "---" in content  # Has frontmatter
    assert "block_id: TEST_BLOCK" in content
    assert "version: 1.0.0" in content
    assert "# Test Block" in content
    assert "## Description" in content
    assert "A test block" in content
    assert "## Inputs" in content
    assert "| INPUT1 |" in content
    assert "## Outputs" in content
    assert "| OUTPUT1 |" in content
    assert "## Contains" in content
    assert "**Recipes:** recipe1" in content
    assert "## Dependencies" in content
    assert "pandas" in content
    assert "## Usage" in content
    assert "BLOCKS_REGISTRY/TEST_BLOCK@1.0.0" in content
    assert "## Changelog" in content
```

#### Test: merge_index_new_block

```python
def test_merge_index_new_block():
    """New block should be added to index."""
    # Arrange
    writer = CatalogWriter.__new__(CatalogWriter)

    existing = {
        "format_version": "1.0",
        "updated_at": "2024-01-01T00:00:00Z",
        "block_count": 1,
        "blocks": [
            {"block_id": "EXISTING_BLOCK", "version": "1.0.0"}
        ]
    }

    new_summaries = [
        {"block_id": "NEW_BLOCK", "version": "1.0.0"}
    ]

    # Act
    merged = writer._merge_index(existing, new_summaries)

    # Assert
    assert merged["block_count"] == 2
    assert len(merged["blocks"]) == 2
    block_ids = [b["block_id"] for b in merged["blocks"]]
    assert "EXISTING_BLOCK" in block_ids
    assert "NEW_BLOCK" in block_ids
```

#### Test: merge_index_update_existing

```python
def test_merge_index_update_existing():
    """Existing block should be updated."""
    # Arrange
    writer = CatalogWriter.__new__(CatalogWriter)

    existing = {
        "format_version": "1.0",
        "updated_at": "2024-01-01T00:00:00Z",
        "block_count": 1,
        "blocks": [
            {"block_id": "BLOCK_A", "version": "1.0.0", "name": "Old Name"}
        ]
    }

    new_summaries = [
        {"block_id": "BLOCK_A", "version": "1.0.0", "name": "New Name"}
    ]

    # Act
    merged = writer._merge_index(existing, new_summaries)

    # Assert
    assert merged["block_count"] == 1
    assert len(merged["blocks"]) == 1
    assert merged["blocks"][0]["name"] == "New Name"
```

#### Test: merge_index_preserve_manual

```python
def test_merge_index_preserve_manual():
    """Manually added blocks should be preserved."""
    # Arrange
    writer = CatalogWriter.__new__(CatalogWriter)

    existing = {
        "format_version": "1.0",
        "updated_at": "2024-01-01T00:00:00Z",
        "block_count": 2,
        "blocks": [
            {"block_id": "AUTO_BLOCK", "version": "1.0.0"},
            {"block_id": "MANUAL_BLOCK", "version": "1.0.0"}  # Added manually
        ]
    }

    # Re-discover only AUTO_BLOCK
    new_summaries = [
        {"block_id": "AUTO_BLOCK", "version": "1.1.0"}  # Updated version
    ]

    # Act
    merged = writer._merge_index(existing, new_summaries)

    # Assert
    assert merged["block_count"] == 2
    block_lookup = {b["block_id"]: b for b in merged["blocks"]}
    assert "MANUAL_BLOCK" in block_lookup  # Preserved
    assert block_lookup["AUTO_BLOCK"]["version"] == "1.1.0"  # Updated
```

---

## Integration Tests

### Test: full_discovery_workflow

```python
def test_full_discovery_workflow(mock_client, mock_project):
    """Full workflow from crawl to catalog write."""
    # Arrange
    client = mock_client
    # Setup mock project with zones

    agent = DiscoveryAgent(client)
    config = DiscoveryConfig(
        hierarchy_level="equipment",
        domain="rotating_equipment",
        version="1.0.0"
    )

    # Act
    result = agent.discover_project("TEST_PROJECT", config)

    # Assert
    assert result.success == True
    assert result.blocks_written > 0
    assert result.blocks_failed == 0
```

### Test: discovery_with_filters

```python
def test_discovery_with_filters(mock_client, mock_project):
    """Zone filters should limit discovered blocks."""
    # Arrange
    # Setup project with zones: zone1, zone2, zone3

    agent = DiscoveryAgent(mock_client)
    config = DiscoveryConfig(
        hierarchy_level="equipment",
        domain="general",
        zone_filter=["zone1", "zone2"]  # Exclude zone3
    )

    # Act
    result = agent.discover_project("TEST_PROJECT", config)

    # Assert
    assert result.blocks_written == 2
    assert "ZONE3" not in [b.upper().replace(" ", "_") for b in result.written_blocks]
```

### Test: rediscovery_preserves_manual

```python
def test_rediscovery_preserves_manual(mock_client, mock_registry):
    """Re-discovery should preserve manually added wiki content."""
    # Arrange
    # 1. Run initial discovery
    # 2. Manually add "## Manual Notes" section to wiki article
    # 3. Run discovery again

    agent = DiscoveryAgent(mock_client)
    config = DiscoveryConfig(
        hierarchy_level="equipment",
        domain="general"
    )

    # Act
    result1 = agent.discover_project("TEST_PROJECT", config)
    # Add manual notes to wiki article
    # ...
    result2 = agent.discover_project("TEST_PROJECT", config)

    # Assert
    # Check that manual notes section is preserved
    registry = mock_client.get_project("BLOCKS_REGISTRY")
    wiki = registry.get_wiki()
    article = wiki.get_article(result2.written_blocks[0])
    content = article.get_data().get_body()
    assert "## Manual Notes" in content
```

---

## End-to-End Tests

### Test: discovery_creates_registry

```python
def test_discovery_creates_registry():
    """Discovery should create registry if missing."""
    # Arrange
    # Ensure BLOCKS_REGISTRY doesn't exist
    # ...

    agent = DiscoveryAgent(client)
    config = DiscoveryConfig(
        hierarchy_level="equipment",
        domain="general",
        create_registry_if_missing=True
    )

    # Act
    result = agent.discover_project("SOURCE_PROJECT", config)

    # Assert
    assert result.success == True
    # Registry should now exist
    registry = client.get_project("BLOCKS_REGISTRY")
    assert registry is not None
```

### Test: discovery_real_project

```python
@pytest.mark.integration
@pytest.mark.slow
def test_discovery_real_project():
    """Test discovery against real Dataiku instance."""
    # Arrange
    client = DSSClient(os.environ["DSS_HOST"], os.environ["DSS_API_KEY"])

    agent = DiscoveryAgent(client)
    config = DiscoveryConfig(
        hierarchy_level="equipment",
        domain="test",
        version="0.0.1-test"
    )

    # Act
    result = agent.discover_project("TEST_PROJECT", config)

    # Assert
    assert result.success == True
    # Cleanup test blocks from registry
    # ...
```

---

## Test Fixtures

### Mock Client Fixture

```python
@pytest.fixture
def mock_client():
    """Create mock DSSClient."""
    client = Mock(spec=DSSClient)

    # Setup mock project
    mock_project = Mock()
    mock_project.get_summary.return_value = {"name": "Test Project"}
    mock_project.get_metadata.return_value = {"description": "", "tags": []}
    mock_project.list_datasets.return_value = []
    mock_project.list_recipes.return_value = []
    mock_project.list_saved_models.return_value = []

    mock_flow = Mock()
    mock_flow.list_zones.return_value = []
    mock_project.get_flow.return_value = mock_flow

    client.get_project.return_value = mock_project

    return client
```

### Sample Project Data Fixture

```python
@pytest.fixture
def sample_project_data():
    """Create sample ProjectData for testing."""
    return ProjectData(
        project_key="SAMPLE_PROJECT",
        name="Sample Project",
        description="A sample project for testing",
        tags=["test"],
        datasets={
            "RAW_DATA": DatasetInfo(
                name="RAW_DATA",
                type="PostgreSQL",
                zone="zone_prep",
                schema={"columns": [{"name": "id", "type": "string"}]},
                settings={},
                upstream_recipes=[],
                downstream_recipes=["clean_data"]
            ),
            "CLEAN_DATA": DatasetInfo(
                name="CLEAN_DATA",
                type="Filesystem",
                zone="zone_prep",
                schema={"columns": [{"name": "id", "type": "string"}]},
                settings={},
                upstream_recipes=["clean_data"],
                downstream_recipes=["compute_features"]
            ),
            "FEATURES": DatasetInfo(
                name="FEATURES",
                type="Filesystem",
                zone="zone_features",
                schema={"columns": [{"name": "feature_1", "type": "double"}]},
                settings={},
                upstream_recipes=["compute_features"],
                downstream_recipes=[]
            )
        },
        recipes={
            "clean_data": RecipeInfo(
                name="clean_data",
                type="python",
                zone="zone_prep",
                inputs=["RAW_DATA"],
                outputs=["CLEAN_DATA"],
                settings={},
                code="import pandas as pd"
            ),
            "compute_features": RecipeInfo(
                name="compute_features",
                type="python",
                zone="zone_features",
                inputs=["CLEAN_DATA"],
                outputs=["FEATURES"],
                settings={},
                code="import numpy as np"
            )
        },
        zones={
            "zone_prep": ZoneInfo(
                id="zone_prep",
                name="Data Preparation",
                datasets=["RAW_DATA", "CLEAN_DATA"],
                recipes=["clean_data"],
                color="#2ab1ac"
            ),
            "zone_features": ZoneInfo(
                id="zone_features",
                name="Feature Engineering",
                datasets=["FEATURES"],
                recipes=["compute_features"],
                color="#ff5733"
            )
        },
        saved_models=[]
    )
```

---

## Test Coverage Requirements

| Component | Minimum Coverage |
|-----------|------------------|
| BlockIdentifier | 90% |
| MetadataExtractor | 90% |
| CatalogWriter | 85% |
| ProjectCrawler | 80% |
| DiscoveryAgent | 85% |
| Models | 95% |

---

## Running Tests

```bash
# Run all discovery agent tests
pytest tests/iac/workflows/discovery/ -v

# Run only unit tests
pytest tests/iac/workflows/discovery/ -v -m "not integration"

# Run with coverage
pytest tests/iac/workflows/discovery/ --cov=dataikuapi.iac.workflows.discovery --cov-report=html

# Run integration tests (requires real Dataiku)
pytest tests/iac/workflows/discovery/ -v -m integration
```
