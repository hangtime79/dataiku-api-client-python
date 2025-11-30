# Feature Specification: Reference Models

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P0-F002` |
| **Feature Name** | LibraryReference and NotebookReference Models |
| **Parent Phase** | Phase 0: Foundation (Data Models) |
| **Estimated LOC** | ~25 lines |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

Blocks often contain supporting code that isn't a recipe, such as project libraries or Jupyter notebooks. We need data structures to inventory these references so they can be included in the documentation.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Define `LibraryReference` dataclass in `models.py`
- [ ] Define `NotebookReference` dataclass in `models.py`
- [ ] Implement `to_dict()` and `from_dict()` serialization for both

### OUT OF SCOPE (Do NOT do these things)

- ❌ DO NOT: Modify existing classes
- ❌ DO NOT: Implement extraction logic
- ❌ DO NOT: Add tests (covered in P0-F004)

---

## Dependencies

### Requires Complete

_None_

### Independent Of

- `P0-F001`
- `P0-F003`

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/models.py
           └─ Add classes LibraryReference and NotebookReference

DO NOT TOUCH:
           - Existing classes in models.py
```

---

## Input/Output Contract

### Class Signatures

```python
@dataclass
class LibraryReference:
    """
    Reference to a file or module in the project library.
    """
    name: str
    type: str  # "python", "R", "resource"
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LibraryReference": ...

@dataclass
class NotebookReference:
    """
    Reference to a Jupyter or SQL notebook.
    """
    name: str
    type: str  # "jupyter", "sql"
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotebookReference": ...
```

---

## Implementation Guidance

1.  Open `dataikuapi/iac/workflows/discovery/models.py`.
2.  Add `LibraryReference` class definition.
3.  Implement simple serialization (these are flat structures, so it's straightforward).
4.  Add `NotebookReference` class definition.
5.  Implement serialization.

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_models.py` (To be created in P0-F004)

**Manual Verification Script:**

```python
from dataikuapi.iac.workflows.discovery.models import LibraryReference, NotebookReference

# Test LibraryReference
lib = LibraryReference(name="utils.py", type="python", description="Helpers")
lib_dict = lib.to_dict()
assert lib_dict["name"] == "utils.py"
assert LibraryReference.from_dict(lib_dict) == lib
print("LibraryReference: Pass")

# Test NotebookReference
nb = NotebookReference(name="EDA", type="jupyter", tags=["wip"])
nb_dict = nb.to_dict()
assert "wip" in nb_dict["tags"]
assert NotebookReference.from_dict(nb_dict) == nb
print("NotebookReference: Pass")
```

---

## Verification

### Quick Sanity Check

```python
# Run the manual verification script above
# Expected Output:
# LibraryReference: Pass
# NotebookReference: Pass
```

---

## Acceptance Criteria

- [ ] `LibraryReference` class exists
- [ ] `NotebookReference` class exists
- [ ] Serialization works for both
- [ ] Code formatted with `black`

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P0-F002-reference-models
```