# Executing Agent Test Cases

## Test Organization

Tests are organized into:
1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test components working together
3. **End-to-End Tests** - Test full composition workflow

---

## Unit Tests

### Test Suite: BlockMatcher

#### Test: match_empty_query_returns_all

```python
def test_match_empty_query_returns_all():
    """Empty query should return all blocks (up to limit)."""
    # Arrange
    catalog = create_test_catalog(num_blocks=20)
    matcher = BlockMatcher(catalog)
    query = BlockQuery()  # Empty query

    # Act
    results = matcher.match(query)

    # Assert
    assert len(results) == 10  # Default limit
    assert all(r.score == 1.0 for r in results)  # No criteria = perfect match
```

#### Test: match_by_hierarchy_level

```python
def test_match_by_hierarchy_level():
    """Query with hierarchy filter should only return matching blocks."""
    # Arrange
    catalog = BlockCatalog()
    catalog.add_block(BlockSummary(
        block_id="BLOCK_A",
        version="1.0.0",
        type="zone",
        blocked=False,
        hierarchy_level="equipment",
        domain="general",
        tags=[],
        name="Block A",
        description=None,
        inputs=[],
        outputs=[],
        source_project="TEST"
    ))
    catalog.add_block(BlockSummary(
        block_id="BLOCK_B",
        version="1.0.0",
        type="zone",
        blocked=False,
        hierarchy_level="process",
        domain="general",
        tags=[],
        name="Block B",
        description=None,
        inputs=[],
        outputs=[],
        source_project="TEST"
    ))
    catalog.build_indexes()

    matcher = BlockMatcher(catalog)
    query = BlockQuery(hierarchy_level="equipment")

    # Act
    results = matcher.match(query)

    # Assert
    assert len(results) == 1
    assert results[0].block_id == "BLOCK_A"
```

#### Test: match_by_domain

```python
def test_match_by_domain():
    """Query with domain filter should only return matching blocks."""
    # Arrange
    catalog = create_catalog_with_domains(
        [("BLOCK_A", "rotating_equipment"), ("BLOCK_B", "process_control")]
    )
    matcher = BlockMatcher(catalog)
    query = BlockQuery(domain="rotating_equipment")

    # Act
    results = matcher.match(query)

    # Assert
    assert len(results) == 1
    assert results[0].block_id == "BLOCK_A"
```

#### Test: match_blocked_only

```python
def test_match_blocked_only():
    """blocked_only filter should exclude non-blocked blocks."""
    # Arrange
    catalog = BlockCatalog()
    catalog.add_block(create_block_summary("BLOCK_A", blocked=True))
    catalog.add_block(create_block_summary("BLOCK_B", blocked=False))
    catalog.build_indexes()

    matcher = BlockMatcher(catalog)
    query = BlockQuery(blocked_only=True)

    # Act
    results = matcher.match(query)

    # Assert
    assert len(results) == 1
    assert results[0].block_id == "BLOCK_A"
```

#### Test: match_by_tags_partial

```python
def test_match_by_tags_partial():
    """Tag matching should score based on partial matches."""
    # Arrange
    catalog = BlockCatalog()
    catalog.add_block(create_block_summary(
        "BLOCK_A", tags=["compressor", "vibration", "monitoring"]
    ))
    catalog.add_block(create_block_summary(
        "BLOCK_B", tags=["pump", "monitoring"]
    ))
    catalog.build_indexes()

    matcher = BlockMatcher(catalog)
    query = BlockQuery(tags=["compressor", "vibration"])

    # Act
    results = matcher.match(query)

    # Assert
    assert len(results) == 2
    assert results[0].block_id == "BLOCK_A"  # Higher score (2/2 matches)
    assert results[0].score > results[1].score
```

#### Test: match_by_capabilities

```python
def test_match_by_capabilities():
    """Capability matching should search name, description, tags."""
    # Arrange
    catalog = BlockCatalog()
    catalog.add_block(BlockSummary(
        block_id="FEATURE_ENG",
        version="1.0.0",
        type="zone",
        blocked=False,
        hierarchy_level="equipment",
        domain="general",
        tags=["feature", "engineering"],
        name="Feature Engineering Block",
        description="Extracts features from sensor data",
        inputs=[],
        outputs=[],
        source_project="TEST"
    ))
    catalog.add_block(BlockSummary(
        block_id="ANOMALY_DET",
        version="1.0.0",
        type="zone",
        blocked=False,
        hierarchy_level="equipment",
        domain="general",
        tags=["anomaly", "detection"],
        name="Anomaly Detection",
        description="Detects anomalies using ML",
        inputs=[],
        outputs=[],
        source_project="TEST"
    ))
    catalog.build_indexes()

    matcher = BlockMatcher(catalog)
    query = BlockQuery(capabilities=["feature", "engineering"])

    # Act
    results = matcher.match(query)

    # Assert
    assert results[0].block_id == "FEATURE_ENG"
    assert results[0].score > results[1].score
```

#### Test: match_min_version

```python
def test_match_min_version():
    """min_version filter should exclude older versions."""
    # Arrange
    catalog = BlockCatalog()
    catalog.add_block(create_block_summary("BLOCK_A", version="1.0.0"))
    catalog.add_block(create_block_summary("BLOCK_A", version="2.0.0"))
    catalog.add_block(create_block_summary("BLOCK_A", version="1.5.0"))
    catalog.build_indexes()

    matcher = BlockMatcher(catalog)
    query = BlockQuery(min_version="1.5.0")

    # Act
    results = matcher.match(query)

    # Assert
    versions = [r.version for r in results]
    assert "1.0.0" not in versions
    assert "1.5.0" in versions
    assert "2.0.0" in versions
```

---

### Test Suite: DependencyResolver

#### Test: resolve_linear_dependency

```python
def test_resolve_linear_dependency():
    """Linear A -> B -> C should resolve to [A, B, C]."""
    # Arrange
    blocks = [
        {
            "block_id": "A",
            "inputs": [],
            "outputs": [{"name": "OUT_A", "type": "dataset"}]
        },
        {
            "block_id": "B",
            "inputs": [{"name": "IN_B", "type": "dataset"}],
            "outputs": [{"name": "OUT_B", "type": "dataset"}]
        },
        {
            "block_id": "C",
            "inputs": [{"name": "IN_C", "type": "dataset"}],
            "outputs": []
        }
    ]

    resolver = DependencyResolver()

    # Act
    plan = resolver.resolve(blocks)

    # Assert
    assert plan.execution_order == ["A", "B", "C"]
    assert len(plan.wiring) == 2
```

#### Test: resolve_parallel_branches

```python
def test_resolve_parallel_branches():
    """A -> B, A -> C should have B and C in same stage."""
    # Arrange
    blocks = [
        {
            "block_id": "A",
            "inputs": [],
            "outputs": [{"name": "OUT", "type": "dataset"}]
        },
        {
            "block_id": "B",
            "inputs": [{"name": "IN", "type": "dataset"}],
            "outputs": []
        },
        {
            "block_id": "C",
            "inputs": [{"name": "IN", "type": "dataset"}],
            "outputs": []
        }
    ]

    resolver = DependencyResolver()

    # Act
    plan = resolver.resolve(blocks)

    # Assert
    assert plan.stages[0] == ["A"]
    assert set(plan.stages[1]) == {"B", "C"}  # Parallel
```

#### Test: resolve_fan_in

```python
def test_resolve_fan_in():
    """A -> C, B -> C should resolve C after both A and B."""
    # Arrange
    blocks = [
        {
            "block_id": "A",
            "inputs": [],
            "outputs": [{"name": "OUT_A", "type": "dataset"}]
        },
        {
            "block_id": "B",
            "inputs": [],
            "outputs": [{"name": "OUT_B", "type": "dataset"}]
        },
        {
            "block_id": "C",
            "inputs": [
                {"name": "IN_1", "type": "dataset"},
                {"name": "IN_2", "type": "dataset"}
            ],
            "outputs": []
        }
    ]

    resolver = DependencyResolver()

    # Act
    plan = resolver.resolve(blocks)

    # Assert
    assert set(plan.stages[0]) == {"A", "B"}  # Parallel first
    assert plan.stages[1] == ["C"]  # C depends on both
```

#### Test: resolve_circular_dependency_error

```python
def test_resolve_circular_dependency_error():
    """Circular A -> B -> A should raise error."""
    # Arrange
    blocks = [
        {
            "block_id": "A",
            "inputs": [{"name": "FROM_B", "type": "dataset"}],
            "outputs": [{"name": "TO_B", "type": "dataset"}]
        },
        {
            "block_id": "B",
            "inputs": [{"name": "FROM_A", "type": "dataset"}],
            "outputs": [{"name": "TO_A", "type": "dataset"}]
        }
    ]

    # Also add explicit hints to create cycle
    hints = [
        WiringHint("A", "TO_B", "B", "FROM_A"),
        WiringHint("B", "TO_A", "A", "FROM_B"),
    ]

    resolver = DependencyResolver()

    # Act & Assert
    with pytest.raises(CircularDependencyError) as exc:
        resolver.resolve(blocks, hints)

    assert "A" in str(exc.value) or "B" in str(exc.value)
```

#### Test: resolve_with_wiring_hints

```python
def test_resolve_with_wiring_hints():
    """Explicit wiring hints should override inference."""
    # Arrange
    blocks = [
        {"block_id": "A", "inputs": [], "outputs": [{"name": "OUT", "type": "dataset"}]},
        {"block_id": "B", "inputs": [], "outputs": [{"name": "OUT", "type": "dataset"}]},
        {"block_id": "C", "inputs": [{"name": "IN", "type": "dataset"}], "outputs": []},
    ]

    # Explicitly wire B -> C (not A -> C)
    hints = [WiringHint("B", "OUT", "C", "IN")]

    resolver = DependencyResolver()

    # Act
    plan = resolver.resolve(blocks, hints)

    # Assert
    # Find wire to C
    wire_to_c = [w for w in plan.wiring if w.target_block == "C"][0]
    assert wire_to_c.source_block == "B"
```

---

### Test Suite: ConfigGenerator

#### Test: generate_basic_config

```python
def test_generate_basic_config():
    """Basic config generation should include all sections."""
    # Arrange
    plan = ResolvedPlan(
        execution_order=["BLOCK_A"],
        wiring=[],
        stages=[["BLOCK_A"]]
    )

    blocks_metadata = {
        "BLOCK_A": MatchResult(
            block_id="BLOCK_A",
            version="1.0.0",
            score=1.0,
            block_summary={
                "block_id": "BLOCK_A",
                "version": "1.0.0",
                "inputs": [{"name": "INPUT", "type": "dataset"}],
                "outputs": [{"name": "OUTPUT", "type": "dataset"}],
            }
        )
    }

    generator = ConfigGenerator()

    # Act
    config = generator.generate(
        plan=plan,
        target_project_key="TEST_PROJECT",
        external_inputs={},
        external_outputs={},
        extensions=[],
        blocks_metadata=blocks_metadata
    )

    # Assert
    assert config.version == "1.0"
    assert config.project.key == "TEST_PROJECT"
    assert len(config.blocks) == 1
    assert config.blocks[0].ref == "BLOCKS_REGISTRY/BLOCK_A@1.0.0"
```

#### Test: generate_with_external_mappings

```python
def test_generate_with_external_mappings():
    """External mappings should be used in block references."""
    # Arrange
    plan = ResolvedPlan(
        execution_order=["BLOCK_A"],
        wiring=[],
        stages=[["BLOCK_A"]]
    )

    blocks_metadata = {
        "BLOCK_A": MatchResult(
            block_id="BLOCK_A",
            version="1.0.0",
            score=1.0,
            block_summary={
                "block_id": "BLOCK_A",
                "version": "1.0.0",
                "inputs": [{"name": "RAW_DATA", "type": "dataset"}],
                "outputs": [{"name": "FEATURES", "type": "dataset"}],
            }
        )
    }

    generator = ConfigGenerator()

    # Act
    config = generator.generate(
        plan=plan,
        target_project_key="TEST_PROJECT",
        external_inputs={"RAW_DATA": "MY_SOURCE_DATA"},
        external_outputs={"FEATURES": "MY_OUTPUT_FEATURES"},
        extensions=[],
        blocks_metadata=blocks_metadata
    )

    # Assert
    block_ref = config.blocks[0]
    assert block_ref.inputs["RAW_DATA"] == "MY_SOURCE_DATA"
    assert block_ref.outputs["FEATURES"] == "MY_OUTPUT_FEATURES"
```

#### Test: generate_with_wiring

```python
def test_generate_with_wiring():
    """Wiring should map outputs to inputs between blocks."""
    # Arrange
    plan = ResolvedPlan(
        execution_order=["BLOCK_A", "BLOCK_B"],
        wiring=[
            Wire(
                source_block="BLOCK_A",
                source_port="OUTPUT",
                target_block="BLOCK_B",
                target_port="INPUT",
                dataset_name="BLOCK_A_OUTPUT"
            )
        ],
        stages=[["BLOCK_A"], ["BLOCK_B"]]
    )

    blocks_metadata = {
        "BLOCK_A": MatchResult(
            block_id="BLOCK_A",
            version="1.0.0",
            score=1.0,
            block_summary={
                "block_id": "BLOCK_A",
                "version": "1.0.0",
                "inputs": [],
                "outputs": [{"name": "OUTPUT", "type": "dataset"}],
            }
        ),
        "BLOCK_B": MatchResult(
            block_id="BLOCK_B",
            version="1.0.0",
            score=1.0,
            block_summary={
                "block_id": "BLOCK_B",
                "version": "1.0.0",
                "inputs": [{"name": "INPUT", "type": "dataset"}],
                "outputs": [],
            }
        )
    }

    generator = ConfigGenerator()

    # Act
    config = generator.generate(
        plan=plan,
        target_project_key="TEST",
        external_inputs={},
        external_outputs={},
        extensions=[],
        blocks_metadata=blocks_metadata
    )

    # Assert
    block_b = config.blocks[1]
    assert block_b.inputs["INPUT"] == "BLOCK_A_OUTPUT"
```

#### Test: generate_placeholder_datasets

```python
def test_generate_placeholder_datasets():
    """Unmapped inputs should generate placeholder datasets."""
    # Arrange
    plan = ResolvedPlan(
        execution_order=["BLOCK_A"],
        wiring=[],
        stages=[["BLOCK_A"]]
    )

    blocks_metadata = {
        "BLOCK_A": MatchResult(
            block_id="BLOCK_A",
            version="1.0.0",
            score=1.0,
            block_summary={
                "block_id": "BLOCK_A",
                "version": "1.0.0",
                "inputs": [{"name": "UNMAPPED_INPUT", "type": "dataset"}],
                "outputs": [],
            }
        )
    }

    config_settings = ExecutingAgentConfig(generate_placeholders=True)
    generator = ConfigGenerator(config_settings)

    # Act
    config = generator.generate(
        plan=plan,
        target_project_key="TEST",
        external_inputs={},  # No mapping provided
        external_outputs={},
        extensions=[],
        blocks_metadata=blocks_metadata
    )

    # Assert
    assert len(config.datasets) == 1
    assert config.datasets[0].name == "INPUT_UNMAPPED_INPUT"
    assert "TODO" in config.datasets[0].type
```

#### Test: generate_with_extensions

```python
def test_generate_with_extensions():
    """Extensions should be included in block references."""
    # Arrange
    plan = ResolvedPlan(execution_order=["BLOCK_A"], wiring=[], stages=[["BLOCK_A"]])

    blocks_metadata = {
        "BLOCK_A": MatchResult(
            block_id="BLOCK_A",
            version="1.0.0",
            score=1.0,
            block_summary={
                "block_id": "BLOCK_A",
                "version": "1.0.0",
                "inputs": [],
                "outputs": [],
            }
        )
    }

    extensions = [
        ExtensionConfig(
            block_id="BLOCK_A",
            recipe_overrides=[
                RecipeOverride(recipe="original_recipe", override_with="my_custom_recipe")
            ]
        )
    ]

    generator = ConfigGenerator()

    # Act
    config = generator.generate(
        plan=plan,
        target_project_key="TEST",
        external_inputs={},
        external_outputs={},
        extensions=extensions,
        blocks_metadata=blocks_metadata
    )

    # Assert
    block_ref = config.blocks[0]
    assert len(block_ref.extends) == 1
    assert block_ref.extends[0]["recipe"] == "original_recipe"
    assert block_ref.extends[0]["override_with"] == "my_custom_recipe"
```

---

### Test Suite: IntentParser

#### Test: parse_hierarchy_keywords

```python
def test_parse_hierarchy_keywords():
    """Parser should extract hierarchy level from keywords."""
    # Arrange
    parser = IntentParser()

    test_cases = [
        ("I need equipment level blocks", "equipment"),
        ("Find sensor processing components", "sensor"),
        ("Get plant-wide analytics", "plant"),
        ("Business metrics blocks", "business"),
    ]

    # Act & Assert
    for text, expected_hierarchy in test_cases:
        query = parser.parse(text)
        assert query.hierarchy_level == expected_hierarchy, f"Failed for: {text}"
```

#### Test: parse_domain_keywords

```python
def test_parse_domain_keywords():
    """Parser should extract domain from keywords."""
    # Arrange
    parser = IntentParser()

    test_cases = [
        ("compressor monitoring", "rotating_equipment"),
        ("pump analytics", "rotating_equipment"),
        ("process control blocks", "process_control"),
        ("predictive maintenance solution", "predictive_maintenance"),
    ]

    # Act & Assert
    for text, expected_domain in test_cases:
        query = parser.parse(text)
        assert query.domain == expected_domain, f"Failed for: {text}"
```

#### Test: parse_capability_keywords

```python
def test_parse_capability_keywords():
    """Parser should extract capability keywords."""
    # Arrange
    parser = IntentParser()

    # Act
    query = parser.parse("feature engineering and anomaly detection")

    # Assert
    assert "feature" in query.capabilities or "engineering" in query.capabilities
    assert "anomaly" in query.capabilities or "detection" in query.capabilities
```

#### Test: parse_blocked_modifiers

```python
def test_parse_blocked_modifiers():
    """Parser should detect blocked/protected modifiers."""
    # Arrange
    parser = IntentParser()

    # Act & Assert
    query1 = parser.parse("Find protected blocks for monitoring")
    assert query1.blocked_only == True

    query2 = parser.parse("Get stable published components")
    assert query2.blocked_only == True

    query3 = parser.parse("Find editable blocks I can modify")
    assert query3.exclude_blocked == True
```

#### Test: parse_with_catalog_tags

```python
def test_parse_with_catalog_tags():
    """Parser should use catalog tags for better matching."""
    # Arrange
    catalog = BlockCatalog()
    catalog.add_block(create_block_summary("B1", tags=["vibration", "fft", "spectral"]))
    catalog.build_indexes()

    parser = IntentParser(catalog)

    # Act
    query = parser.parse("I need vibration analysis with fft")

    # Assert
    assert "vibration" in query.tags
    assert "fft" in query.tags
```

---

## Integration Tests

### Test: full_composition_workflow

```python
def test_full_composition_workflow(mock_client, mock_registry):
    """Full workflow from query to config generation."""
    # Arrange
    # Setup mock registry with blocks
    setup_mock_registry(mock_registry, [
        create_block_summary("FEATURE_ENG", hierarchy_level="equipment", domain="rotating_equipment"),
        create_block_summary("ANOMALY_DET", hierarchy_level="equipment", domain="rotating_equipment"),
    ])

    agent = ExecutingAgent(mock_client)

    query = BlockQuery(
        hierarchy_level="equipment",
        domain="rotating_equipment"
    )

    # Act
    result = agent.compose(
        query=query,
        target_project_key="NEW_PROJECT",
        external_inputs={"RAW_DATA": "SOURCE_SENSORS"}
    )

    # Assert
    assert result.success == True
    assert len(result.matches) == 2
    assert result.config is not None

    yaml_output = result.config.to_yaml()
    assert "NEW_PROJECT" in yaml_output
    assert "FEATURE_ENG" in yaml_output
```

### Test: compose_from_intent

```python
def test_compose_from_intent(mock_client, mock_registry):
    """Natural language intent should produce valid config."""
    # Arrange
    setup_mock_registry(mock_registry, [
        create_block_summary(
            "COMPRESSOR_FEATURES",
            hierarchy_level="equipment",
            domain="rotating_equipment",
            tags=["compressor", "feature"]
        ),
    ])

    agent = ExecutingAgent(mock_client)

    # Act
    result = agent.compose_from_intent(
        intent="I need compressor feature engineering",
        target_project_key="COMPRESSOR_PROJECT"
    )

    # Assert
    assert result.success == True
    assert len(result.matches) > 0
    assert "COMPRESSOR_FEATURES" in result.matches[0].block_id
```

### Test: no_matches_returns_suggestions

```python
def test_no_matches_returns_suggestions(mock_client, mock_registry):
    """No matches should return helpful suggestions."""
    # Arrange
    setup_mock_registry(mock_registry, [
        create_block_summary("UNRELATED_BLOCK", domain="other_domain"),
    ])

    agent = ExecutingAgent(mock_client)

    query = BlockQuery(
        domain="nonexistent_domain"
    )

    # Act
    result = agent.compose(query, "PROJECT")

    # Assert
    assert result.success == False
    assert len(result.errors) > 0
    assert len(result.warnings) > 0  # Should have suggestions
```

---

## End-to-End Tests

### Test: compose_and_validate_yaml

```python
def test_compose_and_validate_yaml():
    """Generated YAML should be valid and parseable."""
    # Arrange
    # ... setup real or comprehensive mock

    agent = ExecutingAgent(client)
    result = agent.compose(
        query=BlockQuery(capabilities=["feature"]),
        target_project_key="TEST"
    )

    # Act
    yaml_str = result.config.to_yaml()

    # Assert
    # Should be valid YAML
    parsed = yaml.safe_load(yaml_str)
    assert "version" in parsed
    assert "project" in parsed
    assert "blocks" in parsed

    # Should have expected structure
    assert parsed["project"]["key"] == "TEST"
```

### Test: compose_real_registry

```python
@pytest.mark.integration
@pytest.mark.slow
def test_compose_real_registry():
    """Test against real Dataiku instance."""
    # Arrange
    client = DSSClient(os.environ["DSS_HOST"], os.environ["DSS_API_KEY"])

    agent = ExecutingAgent(client)

    # Act
    result = agent.search(BlockQuery(max_results=5))

    # Assert
    # Should return blocks if registry exists
    # (May be empty if registry not setup)
    assert isinstance(result, list)
```

---

## Test Fixtures

### Mock Registry Fixture

```python
@pytest.fixture
def mock_registry():
    """Create mock BLOCKS_REGISTRY project."""
    registry = Mock()

    # Mock library
    library = Mock()
    index_data = {
        "format_version": "1.0",
        "updated_at": "2024-01-01T00:00:00Z",
        "blocks": []
    }

    index_file = Mock()
    index_file.read.return_value = json.dumps(index_data)
    library.get_file.return_value = index_file

    registry.get_library.return_value = library

    return registry


def setup_mock_registry(registry, blocks):
    """Setup mock registry with given blocks."""
    index_data = {
        "format_version": "1.0",
        "updated_at": "2024-01-01T00:00:00Z",
        "blocks": [block_summary_to_dict(b) for b in blocks]
    }

    library = registry.get_library()
    index_file = library.get_file()
    index_file.read.return_value = json.dumps(index_data)
```

### Block Summary Helper

```python
def create_block_summary(
    block_id: str,
    version: str = "1.0.0",
    blocked: bool = False,
    hierarchy_level: str = "equipment",
    domain: str = "general",
    tags: List[str] = None,
    inputs: List[dict] = None,
    outputs: List[dict] = None
) -> BlockSummary:
    """Create a BlockSummary for testing."""
    return BlockSummary(
        block_id=block_id,
        version=version,
        type="zone",
        blocked=blocked,
        hierarchy_level=hierarchy_level,
        domain=domain,
        tags=tags or [],
        name=block_id.replace("_", " ").title(),
        description=f"Test block {block_id}",
        inputs=inputs or [{"name": "INPUT", "type": "dataset"}],
        outputs=outputs or [{"name": "OUTPUT", "type": "dataset"}],
        source_project="TEST_PROJECT",
    )
```

---

## Test Coverage Requirements

| Component | Minimum Coverage |
|-----------|------------------|
| BlockMatcher | 90% |
| DependencyResolver | 95% |
| ConfigGenerator | 90% |
| IntentParser | 85% |
| CatalogReader | 85% |
| ExecutingAgent | 85% |
| Models | 95% |

---

## Running Tests

```bash
# Run all executing agent tests
pytest tests/iac/workflows/executing/ -v

# Run only unit tests
pytest tests/iac/workflows/executing/ -v -m "not integration"

# Run with coverage
pytest tests/iac/workflows/executing/ --cov=dataikuapi.iac.workflows.executing --cov-report=html

# Run integration tests
pytest tests/iac/workflows/executing/ -v -m integration
```
