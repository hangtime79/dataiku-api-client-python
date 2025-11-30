# Feature Specification: Calculate Complexity Metrics

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P5-F001` |
| **Feature Name** | Calculate Block Complexity Metrics |
| **Parent Phase** | Phase 5: Wiki Quick Summary Generation |
| **Estimated LOC** | ~25 lines |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

We want to show a "Complexity" and "Data Volume" rating at the top of the Wiki. This feature implements the logic to calculate these values based on the metadata.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_calculate_complexity(self, metadata)` to `CatalogWriter`
- [ ] Logic:
    - Simple: < 3 recipes
    - Moderate: 3-8 recipes
    - Complex: > 8 recipes
- [ ] Add `_estimate_data_volume(self, metadata)`
    - Sum up sizes (mock logic for now as sizes might be strings/missing)
    - Return a string (e.g., "Unknown" or "~5GB")

---

## Dependencies

### Requires Readable

| File | What you need from it |
|------|----------------------|
| `dataikuapi/iac/workflows/discovery/models.py` | EnhancedBlockMetadata |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/catalog_writer.py
           └─ Add methods _calculate_complexity() and _estimate_data_volume()
```

---

## Implementation Guidance

```python
def _calculate_complexity(self, metadata: EnhancedBlockMetadata) -> str:
    count = len(metadata.recipe_details)
    if count < 3:
        return "Simple"
    elif count < 9:
        return "Moderate"
    else:
        return "Complex"

def _estimate_data_volume(self, metadata: EnhancedBlockMetadata) -> str:
    # Future: Parse "1.2GB" strings from DatasetDetail
    # For now, return placeholder or simple count
    ds_count = len(metadata.dataset_details)
    return f"~{ds_count} Datasets" 
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_catalog_writer_helpers.py` (New file)

```python
def test_calculate_complexity():
    writer = CatalogWriter()
    # Mock metadata with list of 5 recipes
    meta = Mock(recipe_details=[1,2,3,4,5]) 
    assert writer._calculate_complexity(meta) == "Moderate"

def test_complexity_simple():
    writer = CatalogWriter()
    meta = Mock(recipe_details=[1])
    assert writer._calculate_complexity(meta) == "Simple"
```

---

## Acceptance Criteria

- [ ] Methods exist
- [ ] Logic follows rules (<3, 3-8, >8)
- [ ] Returns string values

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P5-F001-calculate-metrics
```