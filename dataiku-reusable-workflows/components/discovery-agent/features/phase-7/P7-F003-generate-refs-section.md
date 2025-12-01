# Feature Specification: Generate References Subsection

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P7-F003` |
| **Feature Name** | Generate Libraries & Notebooks Subsections |
| **Parent Phase** | Phase 7: Wiki Components Section Generation |
| **Estimated LOC** | ~30 lines |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

List referenced libraries and notebooks.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_generate_libraries_section(self, libs)`
- [ ] Add `_generate_notebooks_section(self, notebooks)`
- [ ] Simple bulleted lists (collapsible optional, but let's keep simple for now)

---

## Dependencies

### Requires Readable

| File | What you need from it |
|------|----------------------|
| `dataikuapi/iac/workflows/discovery/models.py` | LibraryReference, NotebookReference |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/catalog_writer.py
           └─ Add methods _generate_libraries_section() and _generate_notebooks_section()
```

---

## Implementation Guidance

```python
def _generate_libraries_section(self, libs: List[LibraryReference]) -> str:
    if not libs:
        return ""
    
    md = "### Project Libraries\n\n"
    for lib in libs:
        md += f"- `{lib.name}` ({lib.type})\n"
    return md + "\n"

def _generate_notebooks_section(self, nbs: List[NotebookReference]) -> str:
    if not nbs:
        return ""
        
    md = "### Notebooks\n\n"
    for nb in nbs:
        md += f"- `{nb.name}` ({nb.type})\n"
    return md + "\n"
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_catalog_writer_components.py`

```python
def test_generate_refs_sections():
    writer = CatalogWriter()
    libs = [LibraryReference(name="utils.py", type="python")]
    nbs = [NotebookReference(name="EDA", type="jupyter")]
    
    assert "utils.py" in writer._generate_libraries_section(libs)
    assert "EDA" in writer._generate_notebooks_section(nbs)
```

---

## Acceptance Criteria

- [ ] Methods exist
- [ ] Formatted correctly

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
   git checkout -b feature/p7-f003
   ```

### After Implementation

4. **Push feature branch:**
   ```bash
   git push -u origin feature/p7-f003
   ```

5. **Create PR to master:**
   ```bash
   gh pr create --base master --title "feat(p7-f003): <description>"
   ```

**Never use Reusable_Workflows branch!**

---