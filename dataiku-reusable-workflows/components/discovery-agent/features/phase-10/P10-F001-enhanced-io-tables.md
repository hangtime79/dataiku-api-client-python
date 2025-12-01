# Feature Specification: Enhanced I/O Tables

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P10-F001` |
| **Feature Name** | Enhance I/O Tables with Schema Links |
| **Parent Phase** | Phase 10: Enhanced I/O Section |
| **Estimated LOC** | ~35 lines |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

The current Input/Output tables are basic. We want to add a "Type" column and a "Schema" column that links down to the "Technical Details" section we created in Phase 9, allowing users to jump straight to the field definitions.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Modify `_generate_io_section(self, metadata)` (or `_generate_inputs_outputs` depending on existing name) in `CatalogWriter`
- [ ] Add "Type" column to the markdown table (e.g., "Snowflake", "S3")
- [ ] Add "Schema" column with link: `[View Details](#schema-{dataset_name})`
- [ ] Ensure anchor links match those generated in Phase 9

---

## Dependencies

### Requires Complete

| Feature ID | What it provides |
|------------|------------------|
| `P9-F001` | Technical details section (targets for the links) |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/catalog_writer.py
           └─ Update method _generate_io_section()
```

---

## Implementation Guidance

```python
def _generate_io_section(self, metadata: EnhancedBlockMetadata) -> str:
    md = "## Inputs & Outputs\n\n"
    
    # 1. Inputs Table
    md += "### Inputs\n\n"
    md += "| Name | Type | Schema |\n|---|---|---|\n"
    
    # Note: metadata.inputs is a list of dicts from the boundary
    # We need to find the matching DatasetDetail to get the Type
    # For now, simplistic lookup or default to "Dataset"
    
    for input_item in metadata.inputs:
        name = input_item.name
        # Lookup type from details list (simplified logic here)
        ds_detail = next((d for d in metadata.dataset_details if d.name == name), None)
        ds_type = ds_detail.type if ds_detail else "Unknown"
        
        link = f"[View Details](#schema-{name})"
        md += f"| {name} | {ds_type} | {link} |\n"
        
    # 2. Outputs Table (Repeat logic)
    md += "\n### Outputs\n\n"
    md += "| Name | Type | Schema |\n|---|---|---|\n"
    for output_item in metadata.outputs:
        name = output_item.name
        ds_detail = next((d for d in metadata.dataset_details if d.name == name), None)
        ds_type = ds_detail.type if ds_detail else "Unknown"
        link = f"[View Details](#schema-{name})"
        md += f"| {name} | {ds_type} | {link} |\n"

    return md + "\n"
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_catalog_writer_io.py` (New file)

```python
def test_enhanced_io_tables():
    writer = CatalogWriter()
    # Mock details to ensure lookup works
    ds = DatasetDetail(name="IN_DS", type="Snowflake", ...)
    meta = EnhancedBlockMetadata(inputs=[BlockPort(name="IN_DS", type="dataset")], dataset_details=[ds])
    
    section = writer._generate_io_section(meta)
    
    assert "| Snowflake |" in section
    assert "[View Details](#schema-IN_DS)" in section
```

---

## Acceptance Criteria

- [ ] Tables include Type and Schema columns
- [ ] Links are formatted correctly
- [ ] Handles missing details gracefully

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
   git checkout -b feature/p10-f001
   ```

### After Implementation

4. **Push feature branch:**
   ```bash
   git push -u origin feature/p10-f001
   ```

5. **Create PR to master:**
   ```bash
   gh pr create --base master --title "feat(p10-f001): <description>"
   ```

**Never use Reusable_Workflows branch!**

---