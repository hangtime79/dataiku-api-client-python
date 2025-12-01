# Feature Specification: Enhanced Metadata Model

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P0-F003` |
| **Feature Name** | EnhancedBlockMetadata Model |
| **Parent Phase** | Phase 0: Foundation (Data Models) |
| **Estimated LOC** | ~25 lines |
| **Complexity** | Medium |
| **Parallel Safe** | **NO** (Depends on F001/F002 types) |

---

## Context

The existing `BlockMetadata` class captures high-level block info. We need to extend this to hold the detailed component lists (datasets, recipes, etc.) defined in previous features, creating a comprehensive container for all block information.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Import `DatasetDetail`, `RecipeDetail`, `LibraryReference`, `NotebookReference` in `models.py`
- [ ] Define `EnhancedBlockMetadata` dataclass inheriting from `BlockMetadata`
- [ ] Override `to_dict` and `from_dict` to handle nested objects
- [ ] Add flow graph and complexity estimation fields

### OUT OF SCOPE (Do NOT do these things)

- ❌ DO NOT: Modify the base `BlockMetadata` class
- ❌ DO NOT: Remove any existing fields

---

## Dependencies

### Requires Complete (must be merged before starting)

| Feature ID | What it provides |
|------------|------------------|
| `P0-F001` | DatasetDetail and RecipeDetail types |
| `P0-F002` | LibraryReference and NotebookReference types |

### Requires Readable

| File | What you need from it |
|------|----------------------|
| `dataikuapi/iac/workflows/discovery/models.py` | BlockMetadata base class |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/models.py
           └─ Add class EnhancedBlockMetadata(BlockMetadata)

DO NOT TOUCH:
           - BlockMetadata definition (must remain compatible)
```

---

## Input/Output Contract

### Class Signature

```python
@dataclass
class EnhancedBlockMetadata(BlockMetadata):
    """
    Extended metadata with rich component details.
    """
    dataset_details: List[DatasetDetail] = field(default_factory=list)
    recipe_details: List[RecipeDetail] = field(default_factory=list)
    library_refs: List[LibraryReference] = field(default_factory=list)
    notebook_refs: List[NotebookReference] = field(default_factory=list)
    flow_graph: Optional[Dict[str, Any]] = None
    estimated_complexity: str = ""  # "simple", "moderate", "complex"
    estimated_size: str = ""        # e.g., "2.5GB"

    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnhancedBlockMetadata": ...
```

---

## Implementation Guidance

1.  Ensure all component types (`DatasetDetail` etc.) are imported.
2.  Define `EnhancedBlockMetadata` inheriting from `BlockMetadata`.
3.  **Crucial:** Dataclass inheritance with default values can be tricky. Ensure `BlockMetadata` fields are respected.
4.  Implement `to_dict`:
    - Call `super().to_dict()` (or manually serialize base fields).
    - Add the new list fields, calling `.to_dict()` on each item in the lists.
5.  Implement `from_dict`:
    - Extract base fields and create base object (or pass to constructor).
    - deserialise the lists: `[DatasetDetail.from_dict(x) for x in data.get("dataset_details", [])]`.

### Key Logic Notes

- When deserializing, if a field is missing in the input dict, use the default factory (empty list).

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_models.py` (To be created in P0-F004)

**Manual Verification Script:**

```python
from dataikuapi.iac.workflows.discovery.models import EnhancedBlockMetadata, DatasetDetail, BlockMetadata

# Create minimal base
base_args = {
    "block_id": "TEST_BLOCK",
    "version": "1.0",
    "type": "zone",
    "source_project": "PROJ"
}

# Create enhanced
enhanced = EnhancedBlockMetadata(
    **base_args,
    dataset_details=[DatasetDetail(name="d1", type="s3", connection="c", format_type="csv", schema_summary={})]
)

# Test Serialize
data = enhanced.to_dict()
print(f"Serialized keys: {data.keys()}")
assert "dataset_details" in data
assert "block_id" in data

# Test Deserialize
restored = EnhancedBlockMetadata.from_dict(data)
assert restored.block_id == "TEST_BLOCK"
assert len(restored.dataset_details) == 1
assert restored.dataset_details[0].name == "d1"
print("EnhancedBlockMetadata: Pass")
```

---

## Verification

### Quick Sanity Check

```python
# Run manual verification script
# Expected Output:
# Serialized keys: dict_keys(['block_id', ..., 'dataset_details', ...])
# EnhancedBlockMetadata: Pass
```

---

## Acceptance Criteria

- [ ] `EnhancedBlockMetadata` inherits from `BlockMetadata`
- [ ] All new fields are present
- [ ] `to_dict()` serializes deeply (converts children to dicts)
- [ ] `from_dict()` deserializes deeply (converts dicts to children objects)
- [ ] Backward compatibility (can load from dict without new fields)

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
   git checkout -b feature/p0-f003
   ```

### After Implementation

4. **Push feature branch:**
   ```bash
   git push -u origin feature/p0-f003
   ```

5. **Create PR to master:**
   ```bash
   gh pr create --base master --title "feat(p0-f003): <description>"
   ```

**Never use Reusable_Workflows branch!**

---