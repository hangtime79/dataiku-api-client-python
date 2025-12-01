# Feature Specification: Extract Flow Graph Nodes

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P4-F001` |
| **Feature Name** | Extract Flow Graph Nodes |
| **Parent Phase** | Phase 4: Flow Graph Extraction |
| **Estimated LOC** | ~25 lines |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

To visualize the block's internal logic, we first need to identify all "nodes" in the graph. Nodes are either Datasets or Recipes. This helper prepares a clean list of nodes for Mermaid visualization.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_extract_graph_nodes(self, boundary, contents)` to `BlockIdentifier`
- [ ] Identify all input datasets (from boundary)
- [ ] Identify all output datasets (from boundary)
- [ ] Identify all internal datasets (from contents)
- [ ] Identify all internal recipes (from contents)
- [ ] Return a list of node dictionaries `{"id": "name", "type": "DATASET/RECIPE"}`

### OUT OF SCOPE (Do NOT do these things)

- ❌ DO NOT: Determine connections (Edges)
- ❌ DO NOT: Generate Mermaid syntax

---

## Dependencies

### Requires Complete

_None_

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/identifier.py
           └─ Add method _extract_graph_nodes()
```

---

## Implementation Guidance

```python
def _extract_graph_nodes(self, boundary: Dict, contents: BlockContents) -> List[Dict[str, str]]:
    nodes = []
    
    # 1. Add Input Datasets
    for item in boundary.get("inputs", []):
        nodes.append({"id": item["name"], "type": "DATASET", "role": "input"})
        
    # 2. Add Output Datasets
    for item in boundary.get("outputs", []):
        nodes.append({"id": item["name"], "type": "DATASET", "role": "output"})
        
    # 3. Add Internal Datasets
    for name in contents.datasets:
        nodes.append({"id": name, "type": "DATASET", "role": "internal"})
        
    # 4. Add Recipes
    for name in contents.recipes:
        nodes.append({"id": name, "type": "RECIPE", "role": "internal"})
        
    return nodes
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_identifier_graph.py` (New file)

```python
def test_extract_graph_nodes():
    identifier = BlockIdentifier(...)
    boundary = {
        "inputs": [{"name": "IN_DS"}],
        "outputs": [{"name": "OUT_DS"}]
    }
    contents = BlockContents(datasets=["INT_DS"], recipes=["compute_X"])
    
    nodes = identifier._extract_graph_nodes(boundary, contents)
    
    ids = [n["id"] for n in nodes]
    assert "IN_DS" in ids
    assert "compute_X" in ids
    assert len(nodes) == 4
```

---

## Acceptance Criteria

- [ ] Method returns all 4 types of items
- [ ] Nodes have `id` and `type`
- [ ] Duplicates are handled (or don't matter for now)

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
   git checkout -b feature/p4-f001
   ```

### After Implementation

4. **Push feature branch:**
   ```bash
   git push -u origin feature/p4-f001
   ```

5. **Create PR to master:**
   ```bash
   gh pr create --base master --title "feat(p4-f001): <description>"
   ```

**Never use Reusable_Workflows branch!**

---