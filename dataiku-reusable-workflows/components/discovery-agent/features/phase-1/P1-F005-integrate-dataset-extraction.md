# Feature Specification: Integrate Dataset Extraction

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P1-F005` |
| **Feature Name** | Integrate Dataset Details into Metadata |
| **Parent Phase** | Phase 1: Dataset Metadata Extraction |
| **Estimated LOC** | ~10 lines |
| **Complexity** | Low |
| **Parallel Safe** | **NO** (Depends on F004) |

---

## Context

Now that we can extract the details, we need to wire this up to the main `extract_block_metadata` method so that every discovered block is populated with this rich data.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Modify `extract_block_metadata` in `identifier.py`
- [ ] Call `_extract_dataset_details` using the list of internal datasets
- [ ] Populate the `dataset_details` field of `EnhancedBlockMetadata`

### OUT OF SCOPE (Do NOT do these things)

- ❌ DO NOT: Modify extraction logic

---

## Dependencies

### Requires Complete

| Feature ID | What it provides |
|------------|------------------|
| `P1-F004` | `_extract_dataset_details` method |
| `P0-F003` | `EnhancedBlockMetadata` class |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/identifier.py
           └─ Update method extract_block_metadata()
```

---

## Implementation Guidance

1.  Locate `extract_block_metadata`.
2.  Locate where `BlockContents` (internal items) are identified.
3.  Add call: `ds_details = self._extract_dataset_details(project, contents.datasets)`.
4.  Ensure `EnhancedBlockMetadata` is instantiated instead of `BlockMetadata` (if not already switched).
5.  Pass `dataset_details=ds_details` to the constructor.

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_identifier.py` (Existing main test)

```python
def test_extract_block_metadata_includes_details(self, mock_project):
    """Test that the main entry point now includes dataset details."""
    identifier = BlockIdentifier(...)
    # ... setup mock ...
    meta = identifier.extract_block_metadata("PROJ", "ZONE", boundary)
    assert isinstance(meta, EnhancedBlockMetadata)
    assert len(meta.dataset_details) > 0
```

---

## Acceptance Criteria

- [ ] `extract_block_metadata` calls the new extraction logic
- [ ] Resulting metadata object contains populated `dataset_details` list
- [ ] Existing functionality remains unbroken

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P1-F005-integrate-dataset-extraction
```