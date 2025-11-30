# Feature Specification: Generate Datasets Subsection

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P7-F001` |
| **Feature Name** | Generate Datasets Subsection |
| **Parent Phase** | Phase 7: Wiki Components Section Generation |
| **Estimated LOC** | ~30 lines |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

We need to generate a detailed list of internal datasets using HTML `<details>` tags for collapsibility. This keeps the wiki clean while providing depth when needed.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_generate_datasets_section(self, datasets: List[DatasetDetail])` to `CatalogWriter`
- [ ] Iterate through datasets
- [ ] Generate HTML `<details>` block for each
- [ ] Include: Name, Type, Schema Summary, Description, Tags
- [ ] Return formatted Markdown string

---

## Dependencies

### Requires Readable

| File | What you need from it |
|------|----------------------|
| `dataikuapi/iac/workflows/discovery/models.py` | DatasetDetail |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/catalog_writer.py
           └─ Add method _generate_datasets_section()
```

---

## Implementation Guidance

```python
def _generate_datasets_section(self, datasets: List[DatasetDetail]) -> str:
    if not datasets:
        return ""

    md = f"### Datasets\n\n<details>\n<summary><b>{len(datasets)} internal datasets</b> - Click to expand</summary>\n\n"
    
    for ds in datasets:
        cols = ds.schema_summary.get("columns", "?")
        md += f"#### `{ds.name}` ({ds.type})\n"
        md += f"- **Purpose**: {ds.description or 'No description'}\n"
        md += f"- **Schema**: {cols} columns\n"
        if ds.tags:
            md += f"- **Tags**: `{', '.join(ds.tags)}`\n"
        md += "\n"
        
    md += "</details>\n\n"
    return md
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_catalog_writer_components.py` (New file)

```python
def test_generate_datasets_section():
    writer = CatalogWriter()
    ds = DatasetDetail(name="DS1", type="S3", connection="", format_type="", schema_summary={"columns": 5})
    
    section = writer._generate_datasets_section([ds])
    
    assert "<details>" in section
    assert "DS1" in section
    assert "5 columns" in section
```

---

## Acceptance Criteria

- [ ] Generates collapsible HTML section
- [ ] Includes key details
- [ ] Handles empty list gracefully

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P7-F001-generate-datasets-section
```