# Feature Specification: Basic Dataset Properties

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P1-F001` |
| **Feature Name** | Extract Basic Dataset Properties |
| **Parent Phase** | Phase 1: Dataset Metadata Extraction |
| **Estimated LOC** | ~20 lines |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

We need to extract technical details about datasets (type, connection, format) to populate the `DatasetDetail` model. This helper method isolates the logic for reading dataset settings.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_get_dataset_config(self, dataset)` helper method to `BlockIdentifier`
- [ ] Extract `type` (e.g., Snowflake, S3)
- [ ] Extract `connection` (if available in params)
- [ ] Extract `formatType` (if available)
- [ ] Extract `partitioning` info (if available)

### OUT OF SCOPE (Do NOT do these things)

- ❌ DO NOT: Extract schema (handled in F002)
- ❌ DO NOT: Extract documentation (handled in F003)
- ❌ DO NOT: Modify any other class

---

## Dependencies

### Requires Complete

| Feature ID | What it provides |
|------------|------------------|
| `P0-F001` | DatasetDetail model (for reference, though this method returns dict/tuple) |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/identifier.py
           └─ Add method _get_dataset_config() to BlockIdentifier class

READ ONLY: dataikuapi/iac/workflows/discovery/models.py
```

---

## Input/Output Contract

### Method Signature

```python
def _get_dataset_config(self, dataset: Any) -> Dict[str, Any]:
    """
    Extracts technical configuration from a dataset.

    Args:
        dataset: Dataiku dataset object

    Returns:
        Dict with keys: type, connection, format_type, partitioning
    """
```

---

## Implementation Guidance

```python
def _get_dataset_config(self, dataset: Any) -> Dict[str, Any]:
    # Step 1: Get settings
    settings = dataset.get_settings()
    raw = settings.get_raw()
    
    # Step 2: Extract basic fields
    ds_type = raw.get("type", "unknown")
    params = raw.get("params", {})
    connection = params.get("connection", "")
    
    # Step 3: Extract format
    format_params = raw.get("formatParams", {})
    format_type = raw.get("formatType", "")
    
    # Step 4: Extract partitioning
    partitioning = raw.get("partitioning", {}).get("dimensions", [])
    part_info = f"{len(partitioning)} dims" if partitioning else None

    return {
        "type": ds_type,
        "connection": connection,
        "format_type": format_type,
        "partitioning": part_info
    }
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_identifier_helpers.py` (New file for helpers)

```python
def test_get_dataset_config(self, mock_dataset):
    """Test extraction of basic properties."""
    identifier = BlockIdentifier(...)
    config = identifier._get_dataset_config(mock_dataset)
    assert config["type"] == "Snowflake"
    assert config["connection"] == "DW_CONNECTION"
```

---

## Verification

### Quick Sanity Check

```python
# Helper to run in python shell
from dataikuapi.iac.workflows.discovery.identifier import BlockIdentifier
# Mock a dataset object with .get_settings().get_raw() returning dict
# Call _get_dataset_config
```

---

## Acceptance Criteria

- [ ] Helper method added to `BlockIdentifier`
- [ ] Extracts Type, Connection, Format correctly
- [ ] Handles missing params gracefully (defaults to empty strings)
- [ ] Unit test passes

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P1-F001-basic-dataset-props
```