# Feature Specification: Extract Notebook References

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P3-F002` |
| **Feature Name** | Extract Notebook References |
| **Parent Phase** | Phase 3: Libraries & Notebooks |
| **Estimated LOC** | ~25 lines |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

Notebooks are often used for exploration. We want to list them in the documentation.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_extract_notebook_refs(self, project)` to `BlockIdentifier`
- [ ] List notebooks using `project.list_jupyter_notebooks()` (check API exact name)
- [ ] Return list of `NotebookReference` objects

---

## Dependencies

### Requires Complete

| Feature ID | What it provides |
|------------|------------------|
| `P0-F002` | NotebookReference model |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/identifier.py
           └─ Add method _extract_notebook_refs()
```

---

## Implementation Guidance

```python
def _extract_notebook_refs(self, project: Any) -> List[NotebookReference]:
    refs = []
    try:
        # Note: API might vary, verify project.list_jupyter_notebooks()
        notebooks = project.list_jupyter_notebooks() 
        for nb in notebooks:
            refs.append(NotebookReference(
                name=nb["name"],
                type="jupyter",
                description="Jupyter Notebook"
            ))
    except Exception:
        pass
    return refs
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_identifier_refs.py`

```python
def test_extract_notebook_refs(self, mock_project):
    identifier = BlockIdentifier(...)
    refs = identifier._extract_notebook_refs(mock_project)
    assert len(refs) > 0
    assert refs[0].type == "jupyter"
```

---

## Acceptance Criteria

- [ ] Method exists
- [ ] Lists notebooks
- [ ] Returns `NotebookReference` objects

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P3-F002-extract-notebook-refs
```