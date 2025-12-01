# Feature Specification: Integrate Components Section

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P7-F004` |
| **Feature Name** | Integrate Components Section into Wiki |
| **Parent Phase** | Phase 7: Wiki Components Section Generation |
| **Estimated LOC** | ~20 lines |
| **Complexity** | Low |
| **Parallel Safe** | **NO** (Depends on F001, F002, F003) |

---

## Context

Combine all subsections into a main "Internal Components" section in the wiki article.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_generate_components_section(self, metadata)` to `CatalogWriter`
- [ ] Orchestrate calls to datasets, recipes, libs, notebooks generators
- [ ] Integrate into `generate_wiki_article`

---

## Dependencies

### Requires Complete

| Feature ID | What it provides |
|------------|------------------|
| `P7-F001` | Datasets generator |
| `P7-F002` | Recipes generator |
| `P7-F003` | Refs generator |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/catalog_writer.py
           └─ Add method _generate_components_section() and update generate_wiki_article()
```

---

## Implementation Guidance

```python
def _generate_components_section(self, metadata: EnhancedBlockMetadata) -> str:
    md = "## Internal Components\n\n"
    md += self._generate_datasets_section(metadata.dataset_details)
    md += self._generate_recipes_section(metadata.recipe_details)
    md += self._generate_libraries_section(metadata.library_refs)
    md += self._generate_notebooks_section(metadata.notebook_refs)
    return md

# In generate_wiki_article:
# ... after nav menu ...
md += self._generate_components_section(metadata)
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_catalog_writer.py`

```python
def test_wiki_includes_components():
    writer = CatalogWriter()
    meta = EnhancedBlockMetadata(dataset_details=[...], recipe_details=[...])
    article = writer.generate_wiki_article(meta)
    assert "## Internal Components" in article
    assert "### Datasets" in article
```

---

## Acceptance Criteria

- [ ] Components section appears in Wiki
- [ ] Includes all 4 subsections if data exists

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
   git checkout -b feature/p7-f004
   ```

### After Implementation

4. **Push feature branch:**
   ```bash
   git push -u origin feature/p7-f004
   ```

5. **Create PR to master:**
   ```bash
   gh pr create --base master --title "feat(p7-f004): <description>"
   ```

**Never use Reusable_Workflows branch!**

---