# Feature Specification: Orchestrate Dataset Extraction

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P1-F004` |
| **Feature Name** | Orchestrate Dataset Detail Extraction |
| **Parent Phase** | Phase 1: Dataset Metadata Extraction |
| **Estimated LOC** | ~40 lines |
| **Complexity** | Medium |
| **Parallel Safe** | **NO** (Depends on F001, F002, F003) |

---

## Context

This is the core logic that ties the previous helpers together. It iterates through a list of dataset names, retrieves the objects, calls the helpers, and constructs `DatasetDetail` objects.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_extract_dataset_details(self, project, dataset_names)` to `BlockIdentifier`
- [ ] Iterate through dataset names
- [ ] Call `project.get_dataset()`
- [ ] Call helpers from F001, F002, F003
- [ ] Instantiate `DatasetDetail` objects
- [ ] Handle errors for individual datasets (log and skip, don't crash)

### OUT OF SCOPE (Do NOT do these things)

- ❌ DO NOT: Modify existing helpers

---

## Dependencies

### Requires Complete

| Feature ID | What it provides |
|------------|------------------|
| `P1-F001` | `_get_dataset_config` |
| `P1-F002` | `_summarize_schema` |
| `P1-F003` | `_get_dataset_docs` |
| `P0-F001` | `DatasetDetail` class |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/identifier.py
           └─ Add method _extract_dataset_details()

READ ONLY: dataikuapi/iac/workflows/discovery/models.py
```

---

## Implementation Guidance

```python
def _extract_dataset_details(self, project: Any, dataset_names: List[str]) -> List[DatasetDetail]:
    details = []
    
    for name in dataset_names:
        try:
            # Step 1: Get object
            ds = project.get_dataset(name)
            
            # Step 2: Call helpers
            config = self._get_dataset_config(ds)
            schema_sum = self._summarize_schema(ds)
            docs = self._get_dataset_docs(ds)
            
            # Step 3: Create Model
            detail = DatasetDetail(
                name=name,
                type=config["type"],
                connection=config["connection"],
                format_type=config["format_type"],
                schema_summary=schema_sum,
                partitioning=config["partitioning"],
                tags=docs["tags"],
                description=docs["description"]
            )
            details.append(detail)
            
        except Exception as e:
            # Step 4: Log error but continue
            print(f"Warning: Failed to extract details for {name}: {e}")
            continue
            
    return details
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_identifier_orchestration.py`

```python
def test_extract_dataset_details_success(self, mock_project, mock_helpers):
    """Test successful orchestration."""
    identifier = BlockIdentifier(...)
    # Mock helpers to return valid dicts
    # ...
    details = identifier._extract_dataset_details(mock_project, ["ds1"])
    assert len(details) == 1
    assert isinstance(details[0], DatasetDetail)
    assert details[0].name == "ds1"
```

---

## Verification

### Quick Sanity Check

```python
# Run unit test
```

---

## Acceptance Criteria

- [ ] Method exists
- [ ] Iterates all inputs
- [ ] Returns list of `DatasetDetail` objects
- [ ] Skips failed datasets without crashing

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P1-F004-orchestrate-dataset-extraction
```