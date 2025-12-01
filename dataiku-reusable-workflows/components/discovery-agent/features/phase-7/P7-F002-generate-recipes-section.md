# Feature Specification: Generate Recipes Subsection

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P7-F002` |
| **Feature Name** | Generate Recipes Subsection |
| **Parent Phase** | Phase 7: Wiki Components Section Generation |
| **Estimated LOC** | ~35 lines |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

Generate detailed list of recipes, including code snippets for code-based recipes.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_generate_recipes_section(self, recipes: List[RecipeDetail])` to `CatalogWriter`
- [ ] Generate HTML `<details>` block
- [ ] Include: Name, Type, Inputs/Outputs
- [ ] Include code snippet in a markdown code block if available

---

## Dependencies

### Requires Readable

| File | What you need from it |
|------|----------------------|
| `dataikuapi/iac/workflows/discovery/models.py` | RecipeDetail |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/catalog_writer.py
           └─ Add method _generate_recipes_section()
```

---

## Implementation Guidance

```python
def _generate_recipes_section(self, recipes: List[RecipeDetail]) -> str:
    if not recipes:
        return ""

    md = f"### Recipes\n\n<details>\n<summary><b>{len(recipes)} recipes</b> - Click to expand</summary>\n\n"
    
    for rc in recipes:
        md += f"#### `{rc.name}` ({rc.type})\n"
        md += f"**Inputs**: {', '.join(rc.inputs)} → **Outputs**: {', '.join(rc.outputs)}\n\n"
        
        if rc.code_snippet:
            md += "**Logic Preview**:\n"
            md += f"```python\n{rc.code_snippet}\n```\n"
        
        md += "\n"
        
    md += "</details>\n\n"
    return md
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_catalog_writer_components.py`

```python
def test_generate_recipes_section():
    writer = CatalogWriter()
    rc = RecipeDetail(name="compute_X", type="python", engine="", inputs=["A"], outputs=["B"], code_snippet="print('hi')")
    
    section = writer._generate_recipes_section([rc])
    
    assert "compute_X" in section
    assert "print('hi')" in section
    assert "```python" in section
```

---

## Acceptance Criteria

- [ ] Generates collapsible section
- [ ] Displays code snippets correctly
- [ ] Handles empty list

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
   git checkout -b feature/p7-f002
   ```

### After Implementation

4. **Push feature branch:**
   ```bash
   git push -u origin feature/p7-f002
   ```

5. **Create PR to master:**
   ```bash
   gh pr create --base master --title "feat(p7-f002): <description>"
   ```

**Never use Reusable_Workflows branch!**

---