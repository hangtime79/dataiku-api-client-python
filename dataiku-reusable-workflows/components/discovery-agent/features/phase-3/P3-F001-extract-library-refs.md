# Feature Specification: Extract Library References

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P3-F001` |
| **Feature Name** | Extract Library References |
| **Parent Phase** | Phase 3: Libraries & Notebooks |
| **Estimated LOC** | ~25 lines |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

Projects often have code in the `lib/` folder. We need to identify these files to list them in the documentation.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_extract_library_refs(self, project)` to `BlockIdentifier`
- [ ] Access project library
- [ ] List files in `python/` and `R/` folders
- [ ] Return list of `LibraryReference` objects

### OUT OF SCOPE (Do NOT do these things)

- ❌ DO NOT: Read file contents
- ❌ DO NOT: Recursively scan deep folders (keep it top-level for now)

---

## Dependencies

### Requires Complete

| Feature ID | What it provides |
|------------|------------------|
| `P0-F002` | LibraryReference model |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/identifier.py
           └─ Add method _extract_library_refs()
```

---

## Implementation Guidance

```python
def _extract_library_refs(self, project: Any) -> List[LibraryReference]:
    refs = []
    try:
        lib = project.get_library()
        # Scan python lib
        for item in lib.list("python"):
            refs.append(LibraryReference(
                name=item["path"], 
                type="python", 
                description="Project Library"
            ))
    except Exception:
        pass # Library might not exist
        
    return refs
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_identifier_refs.py`

```python
def test_extract_library_refs(self, mock_project):
    identifier = BlockIdentifier(...)
    refs = identifier._extract_library_refs(mock_project)
    assert len(refs) > 0
    assert refs[0].type == "python"
```

---

## Acceptance Criteria

- [ ] Method exists
- [ ] Lists python library files
- [ ] Returns `LibraryReference` objects
- [ ] Does not crash if library is empty

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P3-F001-extract-library-refs
```