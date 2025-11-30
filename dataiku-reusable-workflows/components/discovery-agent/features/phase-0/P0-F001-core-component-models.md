# Feature Specification: Core Component Models

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P0-F001` |
| **Feature Name** | DatasetDetail and RecipeDetail Models |
| **Parent Phase** | Phase 0: Foundation (Data Models) |
| **Estimated LOC** | ~30 lines |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

To generate rich documentation, we need structured data models to hold detailed metadata about datasets and recipes. This feature establishes the `DatasetDetail` and `RecipeDetail` dataclasses which will later be populated by the extraction logic.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Define `DatasetDetail` dataclass in `models.py`
- [ ] Define `RecipeDetail` dataclass in `models.py`
- [ ] Implement `to_dict()` and `from_dict()` serialization for both
- [ ] Add strict type hints

### OUT OF SCOPE (Do NOT do these things)

- ❌ DO NOT: Modify existing classes (`BlockMetadata`, `BlockPort`, etc.)
- ❌ DO NOT: Implement extraction logic (that is Phase 1 & 2)
- ❌ DO NOT: Add tests (covered in P0-F004)

---

## Dependencies

### Requires Complete (must be merged before starting)

_None - this feature can start immediately_

### Requires Readable (must exist, will not modify)

_None_

### Independent Of (can run in parallel with)

- `P0-F002` (Reference Models)
- `P0-F003` (Enhanced Metadata - though F003 will eventually need this)

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/models.py
           └─ Add classes DatasetDetail and RecipeDetail

DO NOT TOUCH:
           - Existing classes in models.py (BlockMetadata, BlockPort, etc.)
           - Any other files
```

---

## Input/Output Contract

### Class Signatures

```python
@dataclass
class DatasetDetail:
    """
    Rich metadata for a dataset.
    """
    name: str
    type: str
    connection: str
    format_type: str
    schema_summary: Dict[str, Any]  # e.g. {"columns": 10, "sample": ["id", "val"]}
    partitioning: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    description: str = ""
    estimated_size: Optional[str] = None
    last_built: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetDetail": ...

@dataclass
class RecipeDetail:
    """
    Rich metadata for a recipe.
    """
    name: str
    type: str
    engine: str
    inputs: List[str]
    outputs: List[str]
    description: str = ""
    tags: List[str] = field(default_factory=list)
    code_snippet: Optional[str] = None
    config_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecipeDetail": ...
```

---

## Implementation Guidance

1.  Open `dataikuapi/iac/workflows/discovery/models.py`.
2.  Import `Optional`, `Dict`, `List`, `Any`, `field` from `typing` and `dataclasses`.
3.  Add `DatasetDetail` class definition with the fields specified above.
4.  Implement `to_dict` returning a dictionary of all fields.
5.  Implement `from_dict` creating a class instance from a dictionary (handle optional fields using `.get()`).
6.  Add `RecipeDetail` class definition.
7.  Implement serialization for `RecipeDetail`.

### Key Logic Notes

- Ensure `default_factory=list` or `default_factory=dict` is used for mutable defaults.
- Docstrings must follow Google style.

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_models.py` (To be created in P0-F004, but manual verification allowed here)

**Manual Verification Script:**

```python
from dataikuapi.iac.workflows.discovery.models import DatasetDetail, RecipeDetail

# Test DatasetDetail
ds = DatasetDetail(
    name="test_ds",
    type="Snowflake",
    connection="DB",
    format_type="table",
    schema_summary={"cols": 5}
)
ds_dict = ds.to_dict()
ds_restored = DatasetDetail.from_dict(ds_dict)
print(f"Dataset Match: {ds == ds_restored}")

# Test RecipeDetail
rc = RecipeDetail(
    name="compute_X",
    type="python",
    engine="k8s",
    inputs=["ds_in"],
    outputs=["ds_out"]
)
rc_dict = rc.to_dict()
rc_restored = RecipeDetail.from_dict(rc_dict)
print(f"Recipe Match: {rc == rc_restored}")
```

---

## Verification

### Quick Sanity Check

```python
# Run the manual verification script above in a Python shell
# Expected Output:
# Dataset Match: True
# Recipe Match: True
```

---

## Acceptance Criteria

- [ ] `DatasetDetail` class exists with all 10 fields
- [ ] `RecipeDetail` class exists with all 9 fields
- [ ] `to_dict()` returns correct JSON-serializable dict
- [ ] `from_dict()` correctly reconstructs objects
- [ ] No changes to existing `Block*` classes
- [ ] Code formatted with `black`

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P0-F001-core-component-models
```