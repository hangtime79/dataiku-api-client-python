# Feature Specification: Integrate References Extraction

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P3-F003` |
| **Feature Name** | Integrate Libs & Notebooks into Metadata |
| **Parent Phase** | Phase 3: Libraries & Notebooks |
| **Estimated LOC** | ~10 lines |
| **Complexity** | Low |
| **Parallel Safe** | **NO** (Depends on F001, F002) |

---

## Context

Wire up the library and notebook extraction to the main `extract_block_metadata` method.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Modify `extract_block_metadata` in `identifier.py`
- [ ] Call `_extract_library_refs`
- [ ] Call `_extract_notebook_refs`
- [ ] Populate `library_refs` and `notebook_refs` fields

---

## Dependencies

### Requires Complete

| Feature ID | What it provides |
|------------|------------------|
| `P3-F001` | Library extraction |
| `P3-F002` | Notebook extraction |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/identifier.py
           └─ Update method extract_block_metadata()
```

---

## Implementation Guidance

1.  Locate `extract_block_metadata`.
2.  Add calls to new methods.
3.  Pass results to `EnhancedBlockMetadata`.

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_identifier.py`

```python
def test_extract_block_metadata_includes_refs(self, mock_project):
    identifier = BlockIdentifier(...)
    meta = identifier.extract_block_metadata("PROJ", "ZONE", boundary)
    assert isinstance(meta.library_refs, list)
    assert isinstance(meta.notebook_refs, list)
```

---

## Acceptance Criteria

- [ ] Metadata includes library refs
- [ ] Metadata includes notebook refs

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P3-F003-integrate-refs-extraction
```