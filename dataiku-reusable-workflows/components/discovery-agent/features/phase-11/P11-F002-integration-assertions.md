# Feature Specification: Integration Test Assertions

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P11-F002` |
| **Feature Name** | Verify Discovery Output Content |
| **Parent Phase** | Phase 11: Integration Testing |
| **Estimated LOC** | ~40 lines |
| **Complexity** | Medium |
| **Parallel Safe** | **NO** (Depends on F001) |

---

## Context

Verify that the generated Wiki article actually contains the new sections we built (Summary, Nav, Components, Graph).

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Implement logic in `test_full_discovery_flow`
- [ ] Run `agent.scan_project(project_key)`
- [ ] Fetch the generated Wiki article
- [ ] Assert presence of: "Quick Summary", "Internal Components", "Flow Diagram", "mermaid", "Schema:"

---

## Dependencies

### Requires Complete

| Feature ID | What it provides |
|------------|------------------|
| `P11-F001` | Test setup |
| `P0` - `P10` | All features |

---

## File Operations

```
MODIFY:    tests/iac/workflows/discovery/integration/test_enhanced_discovery.py
```

---

## Implementation Guidance

```python
    # ... inside test function ...
    
    # 2. Run Discovery
    agent.scan_project(project_key)
    
    # 3. Verify Wiki Output
    project = real_client.get_project(project_key)
    wiki = project.get_wiki()
    
    # Assuming we know at least one block ID will be found, e.g. "DEFAULT_ZONE"
    # In reality, we might list articles to find one.
    articles = wiki.list_articles()
    assert len(articles) > 0, "No articles generated"
    
    # Inspect content of first article
    article = wiki.get_article(articles[0]["id"])
    content = article.get_body()
    
    # Assertions for Enhancements
    assert "> **Quick Summary**" in content
    assert "## 🗺️ Quick Navigation" in content
    assert "## Internal Components" in content
    assert "```mermaid" in content
    assert "## Technical Details" in content
```

---

## Acceptance Criteria

- [ ] Test passes against real project
- [ ] All 5 key sections are verified present

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
   git checkout -b feature/p11-f002
   ```

### After Implementation

4. **Push feature branch:**
   ```bash
   git push -u origin feature/p11-f002
   ```

5. **Create PR to master:**
   ```bash
   gh pr create --base master --title "feat(p11-f002): <description>"
   ```

**Never use Reusable_Workflows branch!**

---