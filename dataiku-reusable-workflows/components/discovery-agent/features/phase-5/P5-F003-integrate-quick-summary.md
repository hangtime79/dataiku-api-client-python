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

**IMPORTANT:** Before starting, read `DEVELOPMENT_PROCESS.md` for complete workflow.

### Pre-Development Checklist

1. **Check for outstanding PRs:**
   ```bash
   gh pr list --repo hangtime79/dataiku-api-client-python --state open
   ```
   - If ANY open PRs exist: **STOP!** Wait for them to be merged first.
   - If NO open PRs: Proceed to step 2.

2. **Sync local master:**
   ```bash
   git checkout master
   git pull origin master
   ```

3. **Create feature branch from master:**
   ```bash
   git checkout -b feature/p5-f003
   ```

### After Implementation

4. **Push feature branch:**
   ```bash
   git push -u origin feature/p5-f003
   ```

5. **Create PR to master:**
   ```bash
   gh pr create --base master --title "feat(p5-f003): <description>"
   ```

**Never use Reusable_Workflows branch!**

---