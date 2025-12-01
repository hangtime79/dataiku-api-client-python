# Feature Specification: Dataset Documentation Extraction

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P1-F003` |
| **Feature Name** | Extract Dataset Documentation |
| **Parent Phase** | Phase 1: Dataset Metadata Extraction |
| **Estimated LOC** | ~15 lines |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

We need to extract the user-provided descriptions and tags from datasets to enrich the documentation.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_get_dataset_docs(self, dataset)` helper method
- [ ] Extract `description` (short)
- [ ] Extract `tags`

### OUT OF SCOPE (Do NOT do these things)

- ❌ DO NOT: Modify other extractors

---

## Dependencies

### Requires Complete

_None_

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/identifier.py
           └─ Add method _get_dataset_docs()
```

---

## Implementation Guidance

```python
def _get_dataset_docs(self, dataset: Any) -> Dict[str, Any]:
    # Step 1: Get settings
    settings = dataset.get_settings()
    raw = settings.get_raw()
    
    # Step 2: Extract info
    description = raw.get("description", "")
    tags = raw.get("tags", [])
    
    return {
        "description": description,
        "tags": tags
    }
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_identifier_helpers.py`

```python
def test_get_dataset_docs(self, mock_dataset):
    identifier = BlockIdentifier(...)
    docs = identifier._get_dataset_docs(mock_dataset)
    assert docs["description"] == "Test Desc"
    assert "tag1" in docs["tags"]
```

---

## Acceptance Criteria

- [ ] Helper method exists
- [ ] Extracts description and tags
- [ ] Handles missing fields gracefully

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
   git checkout -b feature/p1-f003
   ```

### After Implementation

4. **Push feature branch:**
   ```bash
   git push -u origin feature/p1-f003
   ```

5. **Create PR to master:**
   ```bash
   gh pr create --base master --title "feat(p1-f003): <description>"
   ```

**Never use Reusable_Workflows branch!**

---