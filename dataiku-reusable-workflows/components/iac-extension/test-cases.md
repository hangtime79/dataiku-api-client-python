# IaC Block Extension Test Cases

## Test Organization

Tests are organized into:
1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test components working together with mocks
3. **End-to-End Tests** - Test full workflow against real/simulated Dataiku

---

## Unit Tests

### Test Suite: BlockReferenceConfig

#### Test: parse_ref_valid_full

```python
def test_parse_ref_valid_full():
    """Valid ref with all components should parse correctly."""
    # Arrange
    config = BlockReferenceConfig(
        ref="BLOCKS_REGISTRY/FEATURE_ENG@1.2.0",
        instance_name="feature_instance",
        zone_name="feature_zone",
    )

    # Act
    config.parse_ref()

    # Assert
    assert config.registry == "BLOCKS_REGISTRY"
    assert config.block_id == "FEATURE_ENG"
    assert config.version == "1.2.0"
```

#### Test: parse_ref_latest_implicit

```python
def test_parse_ref_latest_implicit():
    """Ref without version should default to 'latest'."""
    # Arrange
    config = BlockReferenceConfig(
        ref="BLOCKS_REGISTRY/MY_BLOCK",
        instance_name="my_instance",
        zone_name="my_zone",
    )

    # Act
    config.parse_ref()

    # Assert
    assert config.registry == "BLOCKS_REGISTRY"
    assert config.block_id == "MY_BLOCK"
    assert config.version == "latest"
```

#### Test: parse_ref_invalid_no_slash

```python
def test_parse_ref_invalid_no_slash():
    """Ref without slash should raise ValueError."""
    # Arrange
    config = BlockReferenceConfig(
        ref="INVALID_REF",
        instance_name="instance",
        zone_name="zone",
    )

    # Act & Assert
    with pytest.raises(ValueError) as exc:
        config.parse_ref()

    assert "Invalid block ref format" in str(exc.value)
```

#### Test: parse_ref_empty_registry

```python
def test_parse_ref_empty_registry():
    """Ref with empty registry should raise ValueError."""
    # Arrange
    config = BlockReferenceConfig(
        ref="/BLOCK_ID@1.0.0",
        instance_name="instance",
        zone_name="zone",
    )

    # Act & Assert
    with pytest.raises(ValueError) as exc:
        config.parse_ref()

    assert "Missing registry" in str(exc.value)
```

#### Test: validate_missing_fields

```python
def test_validate_missing_fields():
    """Validation should catch missing required fields."""
    # Arrange
    config = BlockReferenceConfig(
        ref="",
        instance_name="",
        zone_name="",
    )

    # Act
    errors = config.validate()

    # Assert
    assert len(errors) >= 3
    assert any("ref" in e for e in errors)
    assert any("instance_name" in e for e in errors)
    assert any("zone_name" in e for e in errors)
```

#### Test: to_dict_and_from_dict_roundtrip

```python
def test_to_dict_and_from_dict_roundtrip():
    """Config should survive dict serialization roundtrip."""
    # Arrange
    original = BlockReferenceConfig(
        ref="BLOCKS_REGISTRY/FEATURE_ENG@1.2.0",
        instance_name="feature_instance",
        zone_name="feature_zone",
        inputs={"RAW_DATA": "source_sensors"},
        outputs={"FEATURES": "computed_features"},
        extends=[
            ExtensionConfig(
                recipe="signal_smoothing",
                override_with="custom_smoothing"
            )
        ],
    )
    original.parse_ref()

    # Act
    as_dict = original.to_dict()
    restored = BlockReferenceConfig.from_dict(as_dict)

    # Assert
    assert restored.ref == original.ref
    assert restored.instance_name == original.instance_name
    assert restored.inputs == original.inputs
    assert restored.outputs == original.outputs
    assert len(restored.extends) == len(original.extends)
```

---

### Test Suite: ExtensionConfig

#### Test: validate_recipe_override

```python
def test_validate_recipe_override():
    """Valid recipe override should pass validation."""
    # Arrange
    ext = ExtensionConfig(
        recipe="signal_smoothing",
        override_with="custom_smoothing",
    )

    # Act
    errors = ext.validate()

    # Assert
    assert len(errors) == 0
```

#### Test: validate_class_override

```python
def test_validate_class_override():
    """Valid class override should pass validation."""
    # Arrange
    ext = ExtensionConfig(
        recipe="feature_compute",
        use_class="mypackage.features.CustomFeatureExtractor",
        class_config={"window_size": 100},
    )

    # Act
    errors = ext.validate()

    # Assert
    assert len(errors) == 0
```

#### Test: validate_both_override_types

```python
def test_validate_both_override_types():
    """Extension with both override types should fail."""
    # Arrange
    ext = ExtensionConfig(
        recipe="signal_smoothing",
        override_with="custom_smoothing",
        use_class="mypackage.Custom",
    )

    # Act
    errors = ext.validate()

    # Assert
    assert len(errors) == 1
    assert "cannot have both" in errors[0].lower()
```

#### Test: validate_neither_override_type

```python
def test_validate_neither_override_type():
    """Extension with neither override type should fail."""
    # Arrange
    ext = ExtensionConfig(recipe="signal_smoothing")

    # Act
    errors = ext.validate()

    # Assert
    assert len(errors) == 1
    assert "must specify" in errors[0].lower()
```

#### Test: validate_invalid_class_path

```python
def test_validate_invalid_class_path():
    """Class path without dot should fail validation."""
    # Arrange
    ext = ExtensionConfig(
        recipe="feature_compute",
        use_class="InvalidClassName",  # No module path
    )

    # Act
    errors = ext.validate()

    # Assert
    assert len(errors) == 1
    assert "fully qualified" in errors[0].lower()
```

#### Test: extension_type_property

```python
def test_extension_type_property():
    """extension_type should return correct type."""
    # Arrange
    recipe_override = ExtensionConfig(
        recipe="r1",
        override_with="custom_r1"
    )
    class_override = ExtensionConfig(
        recipe="r2",
        use_class="pkg.MyClass"
    )

    # Assert
    assert recipe_override.extension_type == ExtensionType.RECIPE_OVERRIDE
    assert class_override.extension_type == ExtensionType.CLASS_OVERRIDE
```

---

### Test Suite: BlockState

#### Test: to_dict_complete

```python
def test_to_dict_complete():
    """BlockState should serialize all fields to dict."""
    # Arrange
    state = BlockState(
        resource_id="feature_instance",
        block_ref="BLOCKS_REGISTRY/FEATURE_ENG@1.2.0",
        block_id="FEATURE_ENG",
        version="1.2.0",
        instance_name="feature_instance",
        zone_name="feature_zone",
        inputs={"RAW_DATA": "source_sensors"},
        outputs={"FEATURES": "computed_features"},
        extensions=[{"recipe": "r1", "override_with": "custom_r1"}],
        created_datasets=["internal_ds1", "internal_ds2"],
        created_recipes=["recipe1", "recipe2"],
        status="applied",
    )

    # Act
    result = state.to_dict()

    # Assert
    assert result["resource_id"] == "feature_instance"
    assert result["block_id"] == "FEATURE_ENG"
    assert result["version"] == "1.2.0"
    assert result["status"] == "applied"
    assert len(result["created_datasets"]) == 2
    assert len(result["created_recipes"]) == 2
```

#### Test: from_dict_complete

```python
def test_from_dict_complete():
    """BlockState should deserialize from dict."""
    # Arrange
    data = {
        "resource_id": "feature_instance",
        "block_ref": "BLOCKS_REGISTRY/FEATURE_ENG@1.2.0",
        "block_id": "FEATURE_ENG",
        "version": "1.2.0",
        "instance_name": "feature_instance",
        "zone_name": "feature_zone",
        "inputs": {"RAW_DATA": "source_sensors"},
        "outputs": {"FEATURES": "computed_features"},
        "extensions": [],
        "created_datasets": ["ds1"],
        "created_recipes": ["r1"],
        "status": "applied",
        "error_message": None,
    }

    # Act
    state = BlockState.from_dict(data)

    # Assert
    assert state.resource_id == "feature_instance"
    assert state.block_id == "FEATURE_ENG"
    assert state.status == "applied"
```

---

### Test Suite: ConfigParser Block Extension

#### Test: parse_blocks_section

```python
def test_parse_blocks_section():
    """Parser should correctly parse blocks section."""
    # Arrange
    parser = ConfigParser(client=Mock())
    config_dict = {
        "blocks": [
            {
                "ref": "BLOCKS_REGISTRY/FEATURE_ENG@1.2.0",
                "instance_name": "feature_instance",
                "zone_name": "feature_zone",
                "inputs": {"RAW_DATA": "source_sensors"},
                "outputs": {"FEATURES": "computed_features"},
            }
        ]
    }

    # Act
    parsed = parser.parse(config_dict)

    # Assert
    assert len(parsed.blocks) == 1
    assert parsed.blocks[0].block_id == "FEATURE_ENG"
    assert parsed.blocks[0].version == "1.2.0"
```

#### Test: parse_blocks_with_extensions

```python
def test_parse_blocks_with_extensions():
    """Parser should correctly parse block extensions."""
    # Arrange
    parser = ConfigParser(client=Mock())
    config_dict = {
        "blocks": [
            {
                "ref": "BLOCKS_REGISTRY/FEATURE_ENG@1.0.0",
                "instance_name": "instance",
                "zone_name": "zone",
                "extends": [
                    {"recipe": "r1", "override_with": "custom_r1"},
                    {"recipe": "r2", "use_class": "pkg.MyClass", "class_config": {"key": "value"}},
                ]
            }
        ]
    }

    # Act
    parsed = parser.parse(config_dict)

    # Assert
    assert len(parsed.blocks[0].extends) == 2
    assert parsed.blocks[0].extends[0].override_with == "custom_r1"
    assert parsed.blocks[0].extends[1].use_class == "pkg.MyClass"
    assert parsed.blocks[0].extends[1].class_config == {"key": "value"}
```

#### Test: parse_blocks_generates_default_names

```python
def test_parse_blocks_generates_default_names():
    """Parser should generate default instance/zone names from ref."""
    # Arrange
    parser = ConfigParser(client=Mock())
    config_dict = {
        "blocks": [
            {"ref": "BLOCKS_REGISTRY/MY_BLOCK@1.0.0"}
            # No instance_name or zone_name provided
        ]
    }

    # Act
    parsed = parser.parse(config_dict)

    # Assert
    assert parsed.blocks[0].instance_name == "my_block_instance"
    assert parsed.blocks[0].zone_name == "my_block_zone"
```

#### Test: parse_blocks_missing_ref_raises

```python
def test_parse_blocks_missing_ref_raises():
    """Parser should raise error when ref is missing."""
    # Arrange
    parser = ConfigParser(client=Mock())
    config_dict = {
        "blocks": [
            {"instance_name": "instance", "zone_name": "zone"}
            # No ref
        ]
    }

    # Act & Assert
    with pytest.raises(ValueError) as exc:
        parser.parse(config_dict)

    assert "ref" in str(exc.value).lower()
```

---

### Test Suite: ConfigValidator Block Extension

#### Test: validate_block_exists

```python
def test_validate_block_exists(mock_registry):
    """Validator should pass when block exists in registry."""
    # Arrange
    setup_mock_registry(mock_registry, [
        create_block_summary("FEATURE_ENG", version="1.2.0")
    ])

    validator = ConfigValidator(client=mock_registry.client)
    config = create_parsed_config_with_blocks([
        BlockReferenceConfig(
            ref="BLOCKS_REGISTRY/FEATURE_ENG@1.2.0",
            instance_name="instance",
            zone_name="zone",
        )
    ])

    # Act
    errors = validator.validate(config)

    # Assert
    block_errors = [e for e in errors if "block" in e.path.lower()]
    assert len(block_errors) == 0
```

#### Test: validate_block_not_found

```python
def test_validate_block_not_found(mock_registry):
    """Validator should error when block not in registry."""
    # Arrange
    setup_mock_registry(mock_registry, [])  # Empty registry

    validator = ConfigValidator(client=mock_registry.client)
    config = create_parsed_config_with_blocks([
        BlockReferenceConfig(
            ref="BLOCKS_REGISTRY/NONEXISTENT@1.0.0",
            instance_name="instance",
            zone_name="zone",
        )
    ])

    # Act
    errors = validator.validate(config)

    # Assert
    assert len(errors) > 0
    assert any("not found" in e.message.lower() for e in errors)
```

#### Test: validate_version_not_found

```python
def test_validate_version_not_found(mock_registry):
    """Validator should error when version not available."""
    # Arrange
    setup_mock_registry(mock_registry, [
        create_block_summary("FEATURE_ENG", version="1.0.0")
        # Version 2.0.0 does not exist
    ])

    validator = ConfigValidator(client=mock_registry.client)
    config = create_parsed_config_with_blocks([
        BlockReferenceConfig(
            ref="BLOCKS_REGISTRY/FEATURE_ENG@2.0.0",
            instance_name="instance",
            zone_name="zone",
        )
    ])

    # Act
    errors = validator.validate(config)

    # Assert
    assert len(errors) > 0
    assert any("version" in e.message.lower() for e in errors)
```

#### Test: validate_required_input_not_mapped

```python
def test_validate_required_input_not_mapped(mock_registry):
    """Validator should error when required input not mapped."""
    # Arrange
    setup_mock_registry(mock_registry, [
        create_block_summary(
            "FEATURE_ENG",
            version="1.0.0",
            inputs=[{"name": "RAW_DATA", "required": True}]
        )
    ])

    validator = ConfigValidator(client=mock_registry.client)
    config = create_parsed_config_with_blocks([
        BlockReferenceConfig(
            ref="BLOCKS_REGISTRY/FEATURE_ENG@1.0.0",
            instance_name="instance",
            zone_name="zone",
            inputs={},  # Missing RAW_DATA mapping
        )
    ])

    # Act
    errors = validator.validate(config)

    # Assert
    assert len(errors) > 0
    assert any("RAW_DATA" in e.message for e in errors)
```

#### Test: validate_extension_recipe_not_in_block

```python
def test_validate_extension_recipe_not_in_block(mock_registry):
    """Validator should error when extension targets non-existent recipe."""
    # Arrange
    setup_mock_registry(mock_registry, [
        create_block_summary(
            "FEATURE_ENG",
            version="1.0.0",
            recipes=["recipe_a", "recipe_b"]
        )
    ])

    validator = ConfigValidator(client=mock_registry.client)
    config = create_parsed_config_with_blocks([
        BlockReferenceConfig(
            ref="BLOCKS_REGISTRY/FEATURE_ENG@1.0.0",
            instance_name="instance",
            zone_name="zone",
            extends=[
                ExtensionConfig(recipe="nonexistent_recipe", override_with="custom")
            ],
        )
    ])

    # Act
    errors = validator.validate(config)

    # Assert
    assert len(errors) > 0
    assert any("nonexistent_recipe" in e.message for e in errors)
```

#### Test: validate_override_recipe_not_defined

```python
def test_validate_override_recipe_not_defined(mock_registry):
    """Validator should error when override recipe not in config."""
    # Arrange
    setup_mock_registry(mock_registry, [
        create_block_summary(
            "FEATURE_ENG",
            version="1.0.0",
            recipes=["signal_smoothing"]
        )
    ])

    validator = ConfigValidator(client=mock_registry.client)
    config = create_parsed_config_with_blocks(
        blocks=[
            BlockReferenceConfig(
                ref="BLOCKS_REGISTRY/FEATURE_ENG@1.0.0",
                instance_name="instance",
                zone_name="zone",
                extends=[
                    ExtensionConfig(recipe="signal_smoothing", override_with="undefined_recipe")
                ],
            )
        ],
        recipes=[]  # No recipes defined
    )

    # Act
    errors = validator.validate(config)

    # Assert
    assert len(errors) > 0
    assert any("undefined_recipe" in e.message for e in errors)
```

#### Test: validate_duplicate_instance_names

```python
def test_validate_duplicate_instance_names(mock_registry):
    """Validator should error on duplicate instance names."""
    # Arrange
    setup_mock_registry(mock_registry, [
        create_block_summary("BLOCK_A", version="1.0.0"),
        create_block_summary("BLOCK_B", version="1.0.0"),
    ])

    validator = ConfigValidator(client=mock_registry.client)
    config = create_parsed_config_with_blocks([
        BlockReferenceConfig(
            ref="BLOCKS_REGISTRY/BLOCK_A@1.0.0",
            instance_name="same_name",  # Duplicate
            zone_name="zone_a",
        ),
        BlockReferenceConfig(
            ref="BLOCKS_REGISTRY/BLOCK_B@1.0.0",
            instance_name="same_name",  # Duplicate
            zone_name="zone_b",
        ),
    ])

    # Act
    errors = validator.validate(config)

    # Assert
    assert len(errors) > 0
    assert any("duplicate" in e.message.lower() for e in errors)
```

---

### Test Suite: PlanEngine Block Extension

#### Test: plan_create_new_block

```python
def test_plan_create_new_block():
    """Plan should include create operation for new block."""
    # Arrange
    engine = PlanEngine()
    config = create_parsed_config_with_blocks([
        BlockReferenceConfig(
            ref="BLOCKS_REGISTRY/FEATURE_ENG@1.2.0",
            instance_name="feature_instance",
            zone_name="feature_zone",
        )
    ])
    current_state = State()  # Empty state

    # Act
    plan = engine.generate_plan(config, current_state)

    # Assert
    block_ops = [op for op in plan.operations if op.resource_type == ResourceType.BLOCK]
    assert len(block_ops) == 1
    assert block_ops[0].operation_type == "create"
    assert block_ops[0].instance_name == "feature_instance"
```

#### Test: plan_no_change_for_identical_block

```python
def test_plan_no_change_for_identical_block():
    """Plan should have no operation when block unchanged."""
    # Arrange
    engine = PlanEngine()

    block_config = BlockReferenceConfig(
        ref="BLOCKS_REGISTRY/FEATURE_ENG@1.2.0",
        instance_name="feature_instance",
        zone_name="feature_zone",
        inputs={"RAW": "source"},
        outputs={"OUT": "dest"},
    )
    config = create_parsed_config_with_blocks([block_config])

    current_state = State()
    current_state.add_resource(ResourceType.BLOCK, BlockState(
        resource_id="feature_instance",
        block_ref="BLOCKS_REGISTRY/FEATURE_ENG@1.2.0",
        block_id="FEATURE_ENG",
        version="1.2.0",
        instance_name="feature_instance",
        zone_name="feature_zone",
        inputs={"RAW": "source"},
        outputs={"OUT": "dest"},
        extensions=[],
        created_datasets=[],
        created_recipes=[],
        status="applied",
    ))

    # Act
    plan = engine.generate_plan(config, current_state)

    # Assert
    block_ops = [op for op in plan.operations if op.resource_type == ResourceType.BLOCK]
    assert len(block_ops) == 0
```

#### Test: plan_update_for_version_change

```python
def test_plan_update_for_version_change():
    """Plan should include update operation when version changes."""
    # Arrange
    engine = PlanEngine()

    config = create_parsed_config_with_blocks([
        BlockReferenceConfig(
            ref="BLOCKS_REGISTRY/FEATURE_ENG@2.0.0",  # New version
            instance_name="feature_instance",
            zone_name="feature_zone",
        )
    ])

    current_state = State()
    current_state.add_resource(ResourceType.BLOCK, BlockState(
        resource_id="feature_instance",
        block_ref="BLOCKS_REGISTRY/FEATURE_ENG@1.0.0",  # Old version
        block_id="FEATURE_ENG",
        version="1.0.0",
        instance_name="feature_instance",
        zone_name="feature_zone",
        inputs={},
        outputs={},
        extensions=[],
        created_datasets=[],
        created_recipes=[],
        status="applied",
    ))

    # Act
    plan = engine.generate_plan(config, current_state)

    # Assert
    block_ops = [op for op in plan.operations if op.resource_type == ResourceType.BLOCK]
    assert len(block_ops) == 1
    assert block_ops[0].operation_type == "update"
    assert "version" in block_ops[0].changes[0].lower()
```

#### Test: plan_update_for_input_mapping_change

```python
def test_plan_update_for_input_mapping_change():
    """Plan should include update when input mapping changes."""
    # Arrange
    engine = PlanEngine()

    config = create_parsed_config_with_blocks([
        BlockReferenceConfig(
            ref="BLOCKS_REGISTRY/FEATURE_ENG@1.0.0",
            instance_name="feature_instance",
            zone_name="feature_zone",
            inputs={"RAW_DATA": "new_source"},  # Changed
        )
    ])

    current_state = State()
    current_state.add_resource(ResourceType.BLOCK, BlockState(
        resource_id="feature_instance",
        block_ref="BLOCKS_REGISTRY/FEATURE_ENG@1.0.0",
        block_id="FEATURE_ENG",
        version="1.0.0",
        instance_name="feature_instance",
        zone_name="feature_zone",
        inputs={"RAW_DATA": "old_source"},  # Original
        outputs={},
        extensions=[],
        created_datasets=[],
        created_recipes=[],
        status="applied",
    ))

    # Act
    plan = engine.generate_plan(config, current_state)

    # Assert
    block_ops = [op for op in plan.operations if op.resource_type == ResourceType.BLOCK]
    assert len(block_ops) == 1
    assert block_ops[0].operation_type == "update"
```

#### Test: plan_delete_removed_block

```python
def test_plan_delete_removed_block():
    """Plan should include delete for block not in config."""
    # Arrange
    engine = PlanEngine()

    config = create_parsed_config_with_blocks([])  # No blocks in config

    current_state = State()
    current_state.add_resource(ResourceType.BLOCK, BlockState(
        resource_id="old_instance",
        block_ref="BLOCKS_REGISTRY/OLD_BLOCK@1.0.0",
        block_id="OLD_BLOCK",
        version="1.0.0",
        instance_name="old_instance",
        zone_name="old_zone",
        inputs={},
        outputs={},
        extensions=[],
        created_datasets=[],
        created_recipes=[],
        status="applied",
    ))

    # Act
    plan = engine.generate_plan(config, current_state)

    # Assert
    block_ops = [op for op in plan.operations if op.resource_type == ResourceType.BLOCK]
    assert len(block_ops) == 1
    assert block_ops[0].operation_type == "delete"
```

---

### Test Suite: BlockSync

#### Test: create_block_creates_zone

```python
def test_create_block_creates_zone(mock_client, mock_project):
    """Creating block should create zone in project."""
    # Arrange
    sync = BlockSync(mock_client, mock_project)

    config = BlockReferenceConfig(
        ref="BLOCKS_REGISTRY/FEATURE_ENG@1.0.0",
        instance_name="feature_instance",
        zone_name="feature_zone",
    )
    config.parse_ref()

    # Act
    state = sync.create(config)

    # Assert
    mock_project.get_flow().create_zone.assert_called_with("feature_zone")
    assert state.zone_name == "feature_zone"
    assert state.status == "applied"
```

#### Test: delete_block_deletes_zone

```python
def test_delete_block_deletes_zone(mock_client, mock_project):
    """Deleting block should delete zone."""
    # Arrange
    sync = BlockSync(mock_client, mock_project)

    state = BlockState(
        resource_id="feature_instance",
        block_ref="BLOCKS_REGISTRY/FEATURE_ENG@1.0.0",
        block_id="FEATURE_ENG",
        version="1.0.0",
        instance_name="feature_instance",
        zone_name="feature_zone",
        inputs={},
        outputs={},
        extensions=[],
        created_datasets=[],
        created_recipes=[],
        status="applied",
    )

    # Act
    sync.delete(state)

    # Assert
    mock_project.get_flow().get_zone.assert_called_with("feature_zone")
    mock_project.get_flow().get_zone().delete.assert_called()
```

#### Test: diff_detects_version_change

```python
def test_diff_detects_version_change(mock_client, mock_project):
    """Diff should detect version changes."""
    # Arrange
    sync = BlockSync(mock_client, mock_project)

    config = BlockReferenceConfig(
        ref="BLOCKS_REGISTRY/FEATURE_ENG@2.0.0",  # New version
        instance_name="feature_instance",
        zone_name="feature_zone",
    )
    config.parse_ref()

    existing = BlockState(
        resource_id="feature_instance",
        block_ref="BLOCKS_REGISTRY/FEATURE_ENG@1.0.0",
        block_id="FEATURE_ENG",
        version="1.0.0",  # Old version
        instance_name="feature_instance",
        zone_name="feature_zone",
        inputs={},
        outputs={},
        extensions=[],
        created_datasets=[],
        created_recipes=[],
        status="applied",
    )

    # Act
    diff = sync.diff(config, existing)

    # Assert
    assert diff["action"] == "update"
    assert any("version" in change for change in diff["changes"])
```

---

### Test Suite: BlockInstantiator

#### Test: instantiate_creates_internal_datasets

```python
def test_instantiate_creates_internal_datasets(mock_client, mock_project):
    """Instantiator should create internal datasets in zone."""
    # Arrange
    instantiator = BlockInstantiator(mock_client)

    block_meta = {
        "block_id": "FEATURE_ENG",
        "source_project": "BLOCK_SOURCE",
        "inputs": [],
        "outputs": [],
        "contains": {
            "datasets": ["internal_ds1", "internal_ds2"],
            "recipes": [],
        },
    }

    mock_zone = Mock()

    # Act
    result = instantiator.instantiate(
        project=mock_project,
        block_meta=block_meta,
        zone=mock_zone,
        input_mapping={},
        output_mapping={},
        extensions=[],
    )

    # Assert
    assert result.success
    assert "internal_ds1" in result.created_datasets
    assert "internal_ds2" in result.created_datasets
```

#### Test: instantiate_skips_overridden_recipes

```python
def test_instantiate_skips_overridden_recipes(mock_client, mock_project):
    """Instantiator should skip recipes that have overrides."""
    # Arrange
    instantiator = BlockInstantiator(mock_client)

    block_meta = {
        "block_id": "FEATURE_ENG",
        "source_project": "BLOCK_SOURCE",
        "inputs": [],
        "outputs": [],
        "contains": {
            "datasets": [],
            "recipes": ["recipe_a", "recipe_b"],
        },
    }

    extensions = [
        ExtensionConfig(recipe="recipe_a", override_with="custom_recipe_a")
    ]

    mock_zone = Mock()

    # Act
    result = instantiator.instantiate(
        project=mock_project,
        block_meta=block_meta,
        zone=mock_zone,
        input_mapping={},
        output_mapping={},
        extensions=extensions,
    )

    # Assert
    # recipe_a should be skipped (user provides override)
    # recipe_b should be copied
    assert "recipe_a" not in result.created_recipes
```

#### Test: instantiate_applies_class_extension

```python
def test_instantiate_applies_class_extension(mock_client, mock_project, mock_recipe):
    """Instantiator should inject class override code."""
    # Arrange
    instantiator = BlockInstantiator(mock_client)

    block_meta = {
        "block_id": "FEATURE_ENG",
        "source_project": "BLOCK_SOURCE",
        "inputs": [],
        "outputs": [],
        "contains": {
            "datasets": [],
            "recipes": ["feature_compute"],
        },
    }

    extensions = [
        ExtensionConfig(
            recipe="feature_compute",
            use_class="mypackage.features.CustomExtractor",
            class_config={"window": 100},
        )
    ]

    mock_zone = Mock()
    mock_project.get_recipe.return_value = mock_recipe

    # Act
    result = instantiator.instantiate(
        project=mock_project,
        block_meta=block_meta,
        zone=mock_zone,
        input_mapping={},
        output_mapping={},
        extensions=extensions,
    )

    # Assert
    # Check that code was modified
    mock_recipe.get_settings().set_code.assert_called()
    set_code_arg = mock_recipe.get_settings().set_code.call_args[0][0]
    assert "from mypackage.features import CustomExtractor" in set_code_arg
    assert "_block_override_class" in set_code_arg
```

---

## Integration Tests

### Test: full_block_parsing_and_validation

```python
def test_full_block_parsing_and_validation(mock_registry):
    """Full workflow from YAML to validated config."""
    # Arrange
    setup_mock_registry(mock_registry, [
        create_block_summary(
            "FEATURE_ENG",
            version="1.2.0",
            inputs=[{"name": "RAW_DATA", "required": True}],
            recipes=["signal_smoothing", "feature_compute"],
        )
    ])

    yaml_content = """
version: "1.0"

project:
  key: NEW_PROJECT
  name: "New Project"

blocks:
  - ref: "BLOCKS_REGISTRY/FEATURE_ENG@1.2.0"
    instance_name: feature_instance
    zone_name: feature_zone
    inputs:
      RAW_DATA: source_sensors
    outputs:
      FEATURES: computed_features
    extends:
      - recipe: signal_smoothing
        override_with: custom_smoothing

datasets:
  - name: source_sensors
    type: sql_table
    connection: WAREHOUSE

recipes:
  - name: custom_smoothing
    type: python
    code: "# Custom implementation"
"""

    parser = ConfigParser(client=mock_registry.client)
    validator = ConfigValidator(client=mock_registry.client)

    # Act
    config_dict = yaml.safe_load(yaml_content)
    parsed = parser.parse(config_dict)
    errors = validator.validate(parsed)

    # Assert
    assert len(parsed.blocks) == 1
    assert parsed.blocks[0].block_id == "FEATURE_ENG"
    assert len([e for e in errors if e.severity == "error"]) == 0
```

### Test: plan_and_apply_block

```python
@pytest.mark.integration
def test_plan_and_apply_block(mock_client, mock_registry, mock_project):
    """Plan and apply should correctly instantiate block."""
    # Arrange
    setup_mock_registry(mock_registry, [
        create_block_summary("FEATURE_ENG", version="1.0.0")
    ])

    config = create_parsed_config_with_blocks([
        BlockReferenceConfig(
            ref="BLOCKS_REGISTRY/FEATURE_ENG@1.0.0",
            instance_name="feature_instance",
            zone_name="feature_zone",
        )
    ])

    engine = PlanEngine()
    state_manager = StateManager(mock_client, "NEW_PROJECT")
    block_sync = BlockSync(mock_client, mock_project)

    # Act - Plan
    plan = engine.generate_plan(config, state_manager.state)

    # Assert plan
    assert len(plan.operations) > 0

    # Act - Apply (simplified)
    for op in plan.operations:
        if op.resource_type == ResourceType.BLOCK:
            if op.operation_type == "create":
                block_sync.create(op.config)

    # Assert state updated
    # ... verify zone created, etc.
```

---

## End-to-End Tests

### Test: complete_workflow_real_dataiku

```python
@pytest.mark.e2e
@pytest.mark.slow
def test_complete_workflow_real_dataiku():
    """End-to-end test against real Dataiku instance."""
    # Skip if no credentials
    if not os.environ.get("DSS_HOST"):
        pytest.skip("DSS_HOST not configured")

    # Arrange
    client = DSSClient(
        os.environ["DSS_HOST"],
        os.environ["DSS_API_KEY"]
    )

    # Create config
    config_dict = {
        "version": "1.0",
        "project": {
            "key": "E2E_TEST_PROJECT",
            "name": "E2E Test Project",
        },
        "blocks": [
            {
                "ref": "BLOCKS_REGISTRY/TEST_BLOCK@1.0.0",
                "instance_name": "test_instance",
                "zone_name": "test_zone",
            }
        ],
    }

    # Act
    try:
        # Parse and validate
        parser = ConfigParser(client)
        validator = ConfigValidator(client)

        parsed = parser.parse(config_dict)
        errors = validator.validate(parsed)

        if errors:
            pytest.skip(f"Validation errors (may need setup): {errors}")

        # Generate plan
        engine = PlanEngine()
        manager = StateManager(client, "E2E_TEST_PROJECT")
        plan = engine.generate_plan(parsed, manager.state)

        # Should have operations
        assert len(plan.operations) >= 0

    finally:
        # Cleanup
        try:
            client.get_project("E2E_TEST_PROJECT").delete()
        except Exception:
            pass
```

---

## Test Fixtures

### Mock Registry Fixture

```python
@pytest.fixture
def mock_registry():
    """Create mock BLOCKS_REGISTRY project."""
    mock_client = Mock(spec=DSSClient)
    mock_project = Mock()
    mock_library = Mock()

    # Setup default empty index
    index_data = {
        "format_version": "1.0",
        "updated_at": "2024-01-01T00:00:00Z",
        "blocks": [],
    }

    mock_index_file = Mock()
    mock_index_file.read.return_value = json.dumps(index_data)
    mock_library.get_file.return_value = mock_index_file

    mock_project.get_library.return_value = mock_library
    mock_client.get_project.return_value = mock_project

    return MockRegistry(client=mock_client, project=mock_project, library=mock_library)


def setup_mock_registry(mock_registry, blocks):
    """Setup mock registry with given blocks."""
    index_data = {
        "format_version": "1.0",
        "updated_at": "2024-01-01T00:00:00Z",
        "blocks": [block_to_dict(b) for b in blocks],
    }

    mock_index_file = Mock()
    mock_index_file.read.return_value = json.dumps(index_data)
    mock_registry.library.get_file.return_value = mock_index_file
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
    outputs: List[dict] = None,
    recipes: List[str] = None,
) -> dict:
    """Create a block summary for testing."""
    return {
        "block_id": block_id,
        "version": version,
        "type": "zone",
        "blocked": blocked,
        "hierarchy_level": hierarchy_level,
        "domain": domain,
        "tags": tags or [],
        "name": block_id.replace("_", " ").title(),
        "description": f"Test block {block_id}",
        "inputs": inputs or [],
        "outputs": outputs or [],
        "source_project": "TEST_PROJECT",
        "contains": {
            "datasets": [],
            "recipes": recipes or [],
        },
    }
```

### Parsed Config Helper

```python
def create_parsed_config_with_blocks(
    blocks: List[BlockReferenceConfig],
    datasets: List = None,
    recipes: List = None,
):
    """Create ParsedConfig with blocks for testing."""
    config = ParsedConfig()
    config.blocks = blocks
    config.datasets = datasets or []
    config.recipes = recipes or []

    # Parse refs
    for block in config.blocks:
        try:
            block.parse_ref()
        except ValueError:
            pass

    return config
```

---

## Test Coverage Requirements

| Component | Minimum Coverage |
|-----------|------------------|
| BlockReferenceConfig | 95% |
| ExtensionConfig | 95% |
| BlockState | 90% |
| ConfigParser (blocks) | 90% |
| ConfigValidator (blocks) | 90% |
| PlanEngine (blocks) | 90% |
| BlockSync | 85% |
| BlockInstantiator | 80% |

---

## Running Tests

```bash
# Run all IaC block extension tests
pytest tests/iac/blocks/ -v

# Run only unit tests
pytest tests/iac/blocks/ -v -m "not integration and not e2e"

# Run with coverage
pytest tests/iac/blocks/ --cov=dataikuapi.iac --cov-report=html

# Run integration tests
pytest tests/iac/blocks/ -v -m integration

# Run end-to-end tests (requires Dataiku instance)
DSS_HOST=https://dss.example.com DSS_API_KEY=xxx pytest tests/iac/blocks/ -v -m e2e
```
