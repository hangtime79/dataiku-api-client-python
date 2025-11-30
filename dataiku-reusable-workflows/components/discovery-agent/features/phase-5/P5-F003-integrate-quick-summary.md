# Feature Specification: Integrate Quick Summary

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P5-F003` |
| **Feature Name** | Integrate Summary into Wiki Article |
| **Parent Phase** | Phase 5: Wiki Quick Summary Generation |
| **Estimated LOC** | ~10 lines |
| **Complexity** | Low |
| **Parallel Safe** | **NO** (Depends on F002) |

---

## Context

Insert the generated summary block into the main `generate_wiki_article` flow, right after the title.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Modify `generate_wiki_article` in `catalog_writer.py`
- [ ] Call `_generate_quick_summary`
- [ ] Insert result after the title (`# Name`) and before the next section

---

## Dependencies

### Requires Complete

| Feature ID | What it provides |
|------------|------------------|
| `P5-F002` | `_generate_quick_summary` |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/catalog_writer.py
           └─ Update method generate_wiki_article()
```

---

## Implementation Guidance

```python
# In generate_wiki_article...

md = self._generate_frontmatter(metadata)
md += f"\n# {metadata.name}\n\n"

# Add Summary
md += self._generate_quick_summary(metadata)
md += "\n\n"

# ... rest of article ...
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_catalog_writer.py`

```python
def test_wiki_includes_summary():
    writer = CatalogWriter()
    meta = EnhancedBlockMetadata(...)
    article = writer.generate_wiki_article(meta)
    assert "> **Quick Summary**" in article
```

---

## Acceptance Criteria

- [ ] Summary appears in generated article
- [ ] Positioned correctly (top)

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P5-F003-integrate-quick-summary
```