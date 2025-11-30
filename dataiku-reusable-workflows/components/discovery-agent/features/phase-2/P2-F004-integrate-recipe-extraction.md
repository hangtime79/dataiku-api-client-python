# Feature Specification: Integrate Recipe Extraction

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P2-F004` |
| **Feature Name** | Integrate Recipe Details into Metadata |
| **Parent Phase** | Phase 2: Recipe Metadata Extraction |
| **Estimated LOC** | ~10 lines |
| **Complexity** | Low |
| **Parallel Safe** | **NO** (Depends on F003) |

---

## Context

Wire up the recipe extraction to the main `extract_block_metadata` method.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Modify `extract_block_metadata` in `identifier.py`
- [ ] Call `_extract_recipe_details` using the list of internal recipes
- [ ] Populate the `recipe_details` field of `EnhancedBlockMetadata`

---

## Dependencies

### Requires Complete

| Feature ID | What it provides |
|------------|------------------|
| `P2-F003` | `_extract_recipe_details` |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/identifier.py
           └─ Update method extract_block_metadata()
```

---

## Implementation Guidance

1.  Locate `extract_block_metadata`.
2.  Add call: `rc_details = self._extract_recipe_details(project, contents.recipes)`.
3.  Pass `recipe_details=rc_details` to `EnhancedBlockMetadata` constructor.

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_identifier.py`

```python
def test_extract_block_metadata_includes_recipes(self, mock_project):
    identifier = BlockIdentifier(...)
    meta = identifier.extract_block_metadata("PROJ", "ZONE", boundary)
    assert len(meta.recipe_details) > 0
```

---

## Acceptance Criteria

- [ ] `extract_block_metadata` calls recipe extraction
- [ ] Resulting object has populated `recipe_details`

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P2-F004-integrate-recipe-extraction
```