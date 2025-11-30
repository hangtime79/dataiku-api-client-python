# Feature Specification: Orchestrate Recipe Extraction

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P2-F003` |
| **Feature Name** | Orchestrate Recipe Detail Extraction |
| **Parent Phase** | Phase 2: Recipe Metadata Extraction |
| **Estimated LOC** | ~40 lines |
| **Complexity** | Medium |
| **Parallel Safe** | **NO** (Depends on F001, F002) |

---

## Context

Orchestrates the extraction of recipe details by iterating through recipe names and calling the helpers.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_extract_recipe_details(self, project, recipe_names)`
- [ ] Iterate recipe names
- [ ] Call `project.get_recipe()`
- [ ] Call helpers F001, F002
- [ ] Extract description/tags (inline, simple enough)
- [ ] Create `RecipeDetail` objects

### OUT OF SCOPE (Do NOT do these things)

- ❌ DO NOT: Modify helpers

---

## Dependencies

### Requires Complete

| Feature ID | What it provides |
|------------|------------------|
| `P2-F001` | Config helper |
| `P2-F002` | Snippet helper |
| `P0-F001` | RecipeDetail model |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/identifier.py
           └─ Add method _extract_recipe_details()
```

---

## Implementation Guidance

```python
def _extract_recipe_details(self, project: Any, recipe_names: List[str]) -> List[RecipeDetail]:
    details = []
    
    for name in recipe_names:
        try:
            rc = project.get_recipe(name)
            settings = rc.get_settings()
            raw = settings.get_raw()
            
            config = self._get_recipe_config(rc)
            snippet = self._extract_code_snippet(raw)
            
            detail = RecipeDetail(
                name=name,
                type=config["type"],
                engine=config["engine"],
                inputs=config["inputs"],
                outputs=config["outputs"],
                description=raw.get("description", ""),
                tags=raw.get("tags", []),
                code_snippet=snippet,
                config_summary={} # Can leave empty for now
            )
            details.append(detail)
        except Exception:
            # Log and continue
            continue
            
    return details
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_identifier_orchestration.py`

```python
def test_extract_recipe_details_success(self, mock_project):
    identifier = BlockIdentifier(...)
    details = identifier._extract_recipe_details(mock_project, ["rc1"])
    assert len(details) == 1
    assert isinstance(details[0], RecipeDetail)
```

---

## Acceptance Criteria

- [ ] Method exists
- [ ] Iterates all inputs
- [ ] Returns list of `RecipeDetail` objects
- [ ] Handles errors gracefully

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P2-F003-orchestrate-recipe-extraction
```