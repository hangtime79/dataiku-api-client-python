# Feature Specification: Schema Summary Helper

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P1-F002` |
| **Feature Name** | Summarize Dataset Schema |
| **Parent Phase** | Phase 1: Dataset Metadata Extraction |
| **Estimated LOC** | ~20 lines |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

Full schemas are too large for the main documentation view. We need a helper to create a "schema summary" (column count + list of first 5 columns) to give users a quick idea of the data structure.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_summarize_schema(self, dataset)` helper method to `BlockIdentifier`
- [ ] Extract column count
- [ ] Extract names of first 5 columns
- [ ] Handle potential API errors when fetching schema

### OUT OF SCOPE (Do NOT do these things)

- ❌ DO NOT: Persist full schema (handled by SchemaExtractor)
- ❌ DO NOT: Modify existing schema extraction logic

---

## Dependencies

### Requires Complete

_None_

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/identifier.py
           └─ Add method _summarize_schema() to BlockIdentifier class
```

---

## Input/Output Contract

### Method Signature

```python
def _summarize_schema(self, dataset: Any) -> Dict[str, Any]:
    """
    Creates a lightweight summary of the dataset schema.

    Args:
        dataset: Dataiku dataset object

    Returns:
        Dict with keys: columns (int), sample (List[str])
    """
```

---

## Implementation Guidance

```python
def _summarize_schema(self, dataset: Any) -> Dict[str, Any]:
    try:
        # Step 1: Get schema
        schema = dataset.get_schema()
        columns = schema.get("columns", [])
        
        # Step 2: Summarize
        count = len(columns)
        sample = [c["name"] for c in columns[:5]]
        
        return {
            "columns": count,
            "sample": sample
        }
    except Exception:
        # Step 3: Graceful fallback
        return {"columns": 0, "sample": []}
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_identifier_helpers.py`

```python
def test_summarize_schema(self, mock_dataset):
    """Test schema summarization."""
    mock_dataset.get_schema.return_value = {
        "columns": [{"name": f"col_{i}"} for i in range(10)]
    }
    identifier = BlockIdentifier(...)
    summary = identifier._summarize_schema(mock_dataset)
    
    assert summary["columns"] == 10
    assert len(summary["sample"]) == 5
    assert summary["sample"][0] == "col_0"
```

---

## Acceptance Criteria

- [ ] Helper method exists
- [ ] Returns correct column count
- [ ] Returns first 5 columns only
- [ ] Returns empty dict/zeros on error (doesn't crash)

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P1-F002-schema-summary
```