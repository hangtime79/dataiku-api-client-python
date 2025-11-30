# Feature Specification: Basic Recipe Properties

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P2-F001` |
| **Feature Name** | Extract Basic Recipe Properties |
| **Parent Phase** | Phase 2: Recipe Metadata Extraction |
| **Estimated LOC** | ~20 lines |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

Extract technical details about recipes (type, engine, inputs/outputs) to populate `RecipeDetail`.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_get_recipe_config(self, recipe)` helper to `BlockIdentifier`
- [ ] Extract `type` (e.g., python, sync)
- [ ] Extract `engine` (if available in params)
- [ ] Extract `inputs` and `outputs` (names of datasets)

### OUT OF SCOPE (Do NOT do these things)

- ❌ DO NOT: Extract code (F002)
- ❌ DO NOT: Extract docs

---

## Dependencies

### Requires Complete

| Feature ID | What it provides |
|------------|------------------|
| `P0-F001` | RecipeDetail model |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/identifier.py
           └─ Add method _get_recipe_config()
```

---

## Implementation Guidance

```python
def _get_recipe_config(self, recipe: Any) -> Dict[str, Any]:
    # Step 1: Get settings
    settings = recipe.get_settings()
    raw = settings.get_raw()
    
    # Step 2: Extract basic
    r_type = raw.get("type", "unknown")
    params = raw.get("params", {})
    engine = params.get("engineType", "DSS")
    
    # Step 3: Extract I/O (Flatten to list of names)
    inputs = [i["ref"] for i in raw.get("inputs", {}).values()]
    outputs = [o["ref"] for o in raw.get("outputs", {}).values()]
    
    return {
        "type": r_type,
        "engine": engine,
        "inputs": inputs,
        "outputs": outputs
    }
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_identifier_helpers.py`

```python
def test_get_recipe_config(self, mock_recipe):
    identifier = BlockIdentifier(...)
    config = identifier._get_recipe_config(mock_recipe)
    assert config["type"] == "python"
    assert "input_ds" in config["inputs"]
```

---

## Acceptance Criteria

- [ ] Helper method added
- [ ] Extracts Type, Engine
- [ ] Extracts Inputs/Outputs as lists of strings

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P2-F001-basic-recipe-props
```