# Feature Specification: Model Serialization Tests

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P0-F004` |
| **Feature Name** | Model Serialization Unit Tests |
| **Parent Phase** | Phase 0: Foundation (Data Models) |
| **Estimated LOC** | ~50 lines |
| **Complexity** | Low |
| **Parallel Safe** | **NO** (Depends on all models) |

---

## Context

We have created the data structures, but they need formal verification. This feature creates the permanent unit test suite to ensure all models serialize and deserialize correctly, including edge cases like missing optional fields.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Create `tests/iac/workflows/discovery/unit/test_models.py`
- [ ] Test `DatasetDetail` serialization/deserialization
- [ ] Test `RecipeDetail` serialization/deserialization
- [ ] Test `LibraryReference` & `NotebookReference`
- [ ] Test `EnhancedBlockMetadata` (deep serialization)

### OUT OF SCOPE (Do NOT do these things)

- ❌ DO NOT: Modify any model code
- ❌ DO NOT: Add integration tests

---

## Dependencies

### Requires Complete (must be merged before starting)

| Feature ID | What it provides |
|------------|------------------|
| `P0-F001` | Core models |
| `P0-F002` | Reference models |
| `P0-F003` | Enhanced metadata model |

---

## File Operations

```
CREATE:    tests/iac/workflows/discovery/unit/test_models.py
READ ONLY: dataikuapi/iac/workflows/discovery/models.py
```

---

## Input/Output Contract

### Test Functions

```python
def test_dataset_detail_serialization(): ...
def test_recipe_detail_serialization(): ...
def test_reference_models_serialization(): ...
def test_enhanced_metadata_deep_serialization(): ...
def test_enhanced_metadata_empty_lists(): ...
```

---

## Implementation Guidance

1.  Create the test file.
2.  Import `pytest` and all models from `dataikuapi.iac.workflows.discovery.models`.
3.  Implement `test_dataset_detail_serialization`:
    - Create instance with all fields.
    - Assert `to_dict` output matches input.
    - Assert `from_dict` creates equal object.
4.  Implement `test_enhanced_metadata_deep_serialization`:
    - Create `EnhancedBlockMetadata` containing a list of `DatasetDetail`.
    - Serialize to dict.
    - Verify the `dataset_details` field in the dict is a list of dicts, NOT a list of objects.
    - Deserialize.
    - Verify nested objects are restored to correct classes.

### Key Logic Notes

- Use `assert` statements freely.
- Test that optional fields default to `None` or empty lists when missing from input dicts.

---

## Test Specification

**File:** `tests/iac/workflows/discovery/unit/test_models.py`

```python
def test_enhanced_metadata_defaults():
    """Test that missing lists become empty lists, not None."""
    data = {
        "block_id": "B1",
        "version": "1",
        "type": "zone",
        "source_project": "P"
    }
    obj = EnhancedBlockMetadata.from_dict(data)
    assert isinstance(obj.dataset_details, list)
    assert len(obj.dataset_details) == 0
```

---

## Verification

### Quick Sanity Check

```bash
# Run pytest on the new file
pytest tests/iac/workflows/discovery/unit/test_models.py -v
```

### Expected Console Output

```
test_models.py::test_dataset_detail_serialization PASSED
test_models.py::test_recipe_detail_serialization PASSED
test_models.py::test_reference_models_serialization PASSED
test_models.py::test_enhanced_metadata_deep_serialization PASSED
test_models.py::test_enhanced_metadata_defaults PASSED
```

---

## Acceptance Criteria

- [ ] New test file created
- [ ] At least 5 test cases covering all new models
- [ ] All tests pass
- [ ] Tests verify that nested objects are serialized to dicts (not left as objects)
- [ ] Tests verify behavior when optional fields are missing

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P0-F004-model-serialization-tests
```