# Feature Specification: Generate Summary Markdown

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P5-F002` |
| **Feature Name** | Generate Quick Summary Markdown |
| **Parent Phase** | Phase 5: Wiki Quick Summary Generation |
| **Estimated LOC** | ~20 lines |
| **Complexity** | Low |
| **Parallel Safe** | **NO** (Depends on F001) |

---

## Context

Format the calculated metrics into a Markdown blockquote that will sit at the top of the Wiki article.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_generate_quick_summary(self, metadata)` to `CatalogWriter`
- [ ] Call calculation helpers from F001
- [ ] Format output as a Markdown blockquote
- [ ] Include "Quick Summary", "Complexity", "Recipes", "Datasets"

---

## Dependencies

### Requires Complete

| Feature ID | What it provides |
|------------|------------------|
| `P5-F001` | Calculation helpers |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/catalog_writer.py
           └─ Add method _generate_quick_summary()
```

---

## Implementation Guidance

```python
def _generate_quick_summary(self, metadata: EnhancedBlockMetadata) -> str:
    complexity = self._calculate_complexity(metadata)
    # Use simple counts for now if volume is vague
    recipes = len(metadata.recipe_details)
    datasets = len(metadata.dataset_details)
    
    return f"""
> **Quick Summary**: {metadata.description or "No description provided."}
> **Complexity**: {complexity} | **Recipes**: {recipes} | **Datasets**: {datasets}
"""
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_catalog_writer_helpers.py`

```python
def test_generate_quick_summary():
    writer = CatalogWriter()
    meta = Mock(description="Test block", recipe_details=[1,2,3], dataset_details=[1])
    # Mock helpers
    writer._calculate_complexity = Mock(return_value="Moderate")
    
    summary = writer._generate_quick_summary(meta)
    
    assert "> **Quick Summary**" in summary
    assert "Test block" in summary
    assert "Moderate" in summary
```

---

## Acceptance Criteria

- [ ] Method returns formatted markdown string
- [ ] Includes description and metrics
- [ ] Handles missing description gracefully

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P5-F002-generate-summary-markdown
```