# Feature Specification: Extract Flow Graph Edges

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P4-F002` |
| **Feature Name** | Extract Flow Graph Edges |
| **Parent Phase** | Phase 4: Flow Graph Extraction |
| **Estimated LOC** | ~30 lines |
| **Complexity** | Medium |
| **Parallel Safe** | Yes |

---

## Context

Edges represent the flow of data. We need to iterate through the block's recipes and define connections: `Input Dataset -> Recipe -> Output Dataset`.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_extract_graph_edges(self, project, recipes)` to `BlockIdentifier`
- [ ] Iterate through recipes
- [ ] For each recipe, get inputs and outputs
- [ ] Create edges `DATASET -> RECIPE`
- [ ] Create edges `RECIPE -> DATASET`
- [ ] Return list of edges `{"source": "A", "target": "B"}`

### OUT OF SCOPE (Do NOT do these things)

- ❌ DO NOT: Generate Mermaid syntax

---

## Dependencies

### Requires Complete

| Feature ID | What it provides |
|------------|------------------|
| `P2-F001` | `_get_recipe_config` (to easily get inputs/outputs) |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/identifier.py
           └─ Add method _extract_graph_edges()
```

---

## Implementation Guidance

```python
def _extract_graph_edges(self, project: Any, recipe_names: List[str]) -> List[Dict[str, str]]:
    edges = []
    
    for r_name in recipe_names:
        try:
            rc = project.get_recipe(r_name)
            # Reuse P2 helper for robust config extraction
            config = self._get_recipe_config(rc) 
            
            # Input -> Recipe
            for i_name in config["inputs"]:
                edges.append({"source": i_name, "target": r_name})
                
            # Recipe -> Output
            for o_name in config["outputs"]:
                edges.append({"source": r_name, "target": o_name})
                
        except Exception:
            continue
            
    return edges
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_identifier_graph.py`

```python
def test_extract_graph_edges(mock_project):
    identifier = BlockIdentifier(...)
    # Mock project.get_recipe to return object with inputs=["A"], outputs=["B"]
    edges = identifier._extract_graph_edges(mock_project, ["compute_B"])
    
    assert {"source": "A", "target": "compute_B"} in edges
    assert {"source": "compute_B", "target": "B"} in edges
```

---

## Acceptance Criteria

- [ ] Returns list of edges
- [ ] Captures both sides of the recipe (inputs and outputs)
- [ ] Handles API errors gracefully

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
   git checkout -b feature/p4-f002
   ```

### After Implementation

4. **Push feature branch:**
   ```bash
   git push -u origin feature/p4-f002
   ```

5. **Create PR to master:**
   ```bash
   gh pr create --base master --title "feat(p4-f002): <description>"
   ```

**Never use Reusable_Workflows branch!**

---