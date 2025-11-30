# Feature Specification: Generate Navigation Menu

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P6-F001` |
| **Feature Name** | Generate Wiki Navigation Menu |
| **Parent Phase** | Phase 6: Wiki Navigation Menu Generation |
| **Estimated LOC** | ~35 lines |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

To make long articles scannable, we add a "Quick Navigation" section with anchor links to major sections.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_generate_navigation_menu(self, metadata)` to `CatalogWriter`
- [ ] Generate Markdown list with links:
    - Overview
    - Inputs & Outputs
    - Internal Components (with counts)
    - Flow Diagram
    - Technical Details
- [ ] Integrate into `generate_wiki_article` (after Quick Summary)

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
           └─ Add method _generate_navigation_menu() and call it in generate_wiki_article()
```

---

## Implementation Guidance

```python
def _generate_navigation_menu(self, metadata: EnhancedBlockMetadata) -> str:
    ds_count = len(metadata.dataset_details)
    rc_count = len(metadata.recipe_details)
    
    return f"""
## 🗺️ Quick Navigation

- [Overview](#overview)
- [Inputs & Outputs](#inputs--outputs)
- [Internal Components](#internal-components)
  - [Datasets ({ds_count})](#datasets)
  - [Recipes ({rc_count})](#recipes)
- [Flow Diagram](#flow-diagram)
- [Technical Details](#technical-details)
"""
```

**Integration:**
Call this method inside `generate_wiki_article` immediately after the Quick Summary block.

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_catalog_writer_helpers.py`

```python
def test_generate_navigation_menu():
    writer = CatalogWriter()
    meta = Mock(dataset_details=[1,2], recipe_details=[1])
    nav = writer._generate_navigation_menu(meta)
    
    assert "Datasets (2)" in nav
    assert "[Flow Diagram](#flow-diagram)" in nav
```

---

## Acceptance Criteria

- [ ] Navigation menu generated
- [ ] Counts are dynamic
- [ ] Integrated into main article generation

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P6-F001-generate-nav-menu
```