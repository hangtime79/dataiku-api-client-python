# Feature Specification: Integrate Flow Diagram

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P8-F002` |
| **Feature Name** | Integrate Flow Diagram into Wiki |
| **Parent Phase** | Phase 8: Wiki Flow Diagram Generation |
| **Estimated LOC** | ~10 lines |
| **Complexity** | Low |
| **Parallel Safe** | **NO** (Depends on F001) |

---

## Context

Place the diagram in the wiki article.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Modify `generate_wiki_article`
- [ ] Add "## Flow Diagram" section
- [ ] Call `_generate_flow_diagram`

---

## Dependencies

### Requires Complete

| Feature ID | What it provides |
|------------|------------------|
| `P8-F001` | Mermaid generator |

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
md += "## Flow Diagram\n\n"
md += self._generate_flow_diagram(metadata.flow_graph)
md += "\n\n"
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_catalog_writer.py`

```python
def test_wiki_includes_diagram():
    writer = CatalogWriter()
    meta = EnhancedBlockMetadata(flow_graph={"nodes": [], "edges": []})
    article = writer.generate_wiki_article(meta)
    assert "## Flow Diagram" in article
    assert "```mermaid" in article
```

---

## Acceptance Criteria

- [ ] Diagram section present

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
   git checkout -b feature/p8-f002
   ```

### After Implementation

4. **Push feature branch:**
   ```bash
   git push -u origin feature/p8-f002
   ```

5. **Create PR to master:**
   ```bash
   gh pr create --base master --title "feat(p8-f002): <description>"
   ```

**Never use Reusable_Workflows branch!**

---