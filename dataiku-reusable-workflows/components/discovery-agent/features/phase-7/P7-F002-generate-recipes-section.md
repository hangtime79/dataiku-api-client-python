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

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P7-F002-generate-recipes-section
```