# Feature Specification: Generate Technical Details Section

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P9-F001` |
| **Feature Name** | Generate Technical Details Section |
| **Parent Phase** | Phase 9: Wiki Technical Details Section |
| **Estimated LOC** | ~35 lines |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

Provides a deep dive into schemas for input/output datasets, linked to the raw JSON schema files.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_generate_technical_details(self, metadata)` to `CatalogWriter`
- [ ] Iterate through Input and Output datasets (found in `dataset_details`)
- [ ] Create a table for each showing schema sample
- [ ] Add link to full schema file in Library
- [ ] Wrap in `<details>`

---

## Dependencies

### Requires Readable

| File | What you need from it |
|------|----------------------|
| `dataikuapi/iac/workflows/discovery/models.py` | EnhancedBlockMetadata |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/catalog_writer.py
           └─ Add method _generate_technical_details() and call in generate_wiki_article()
```

---

## Implementation Guidance

```python
def _generate_technical_details(self, metadata: EnhancedBlockMetadata) -> str:
    md = "## Technical Details\n\n"
    
    # Filter for inputs/outputs only (not internals)
    # Note: Requires logic to match dataset names against metadata.inputs/outputs list
    # For now, just listing all datasets with schema info is acceptable for V1
    
    md += "### Dataset Schemas\n\n"
    
    for ds in metadata.dataset_details:
        md += f"<details>\n<summary>Schema: {ds.name}</summary>\n\n"
        md += "| Column | Type |\n|---|---|\n"
        
        # In reality, schema_summary.sample is a list of names. 
        # Ideally we'd have types too, but let's just list names for now.
        for col in ds.schema_summary.get("sample", []):
            md += f"| {col} | - |\n"
            
        md += f"\n[Download Full Schema (JSON)](schemas/{metadata.block_id}_{ds.name}.schema.json)\n"
        md += "</details>\n\n"
        
    return md
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_catalog_writer_tech.py` (New file)

```python
def test_generate_technical_details():
    writer = CatalogWriter()
    ds = DatasetDetail(name="DS1", type="S3", connection="", format_type="", schema_summary={"sample": ["col1", "col2"]})
    meta = EnhancedBlockMetadata(block_id="BLK", dataset_details=[ds])
    
    section = writer._generate_technical_details(meta)
    
    assert "Schema: DS1" in section
    assert "| col1 |" in section
    assert ".schema.json" in section
```

---

## Acceptance Criteria

- [ ] Generates technical details section
- [ ] Includes schema tables
- [ ] Includes links to schema files

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
   git checkout -b feature/p9-f001
   ```

### After Implementation

4. **Push feature branch:**
   ```bash
   git push -u origin feature/p9-f001
   ```

5. **Create PR to master:**
   ```bash
   gh pr create --base master --title "feat(p9-f001): <description>"
   ```

**Never use Reusable_Workflows branch!**

---