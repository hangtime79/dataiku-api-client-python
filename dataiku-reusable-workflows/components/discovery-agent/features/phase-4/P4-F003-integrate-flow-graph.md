# Feature Specification: Integrate Flow Graph

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P4-F003` |
| **Feature Name** | Integrate Flow Graph into Metadata |
| **Parent Phase** | Phase 4: Flow Graph Extraction |
| **Estimated LOC** | ~15 lines |
| **Complexity** | Low |
| **Parallel Safe** | **NO** (Depends on F001, F002) |

---

## Context

Combine nodes and edges into a graph structure and store it in `EnhancedBlockMetadata`.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Modify `extract_block_metadata` in `identifier.py`
- [ ] Call `_extract_graph_nodes`
- [ ] Call `_extract_graph_edges`
- [ ] Construct `flow_graph` dictionary
- [ ] Populate `EnhancedBlockMetadata`

---

## Dependencies

### Requires Complete

| Feature ID | What it provides |
|------------|------------------|
| `P4-F001` | Node extraction |
| `P4-F002` | Edge extraction |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/identifier.py
           └─ Update method extract_block_metadata()
```

---

## Implementation Guidance

```python
# In extract_block_metadata...

# ... existing code ...

nodes = self._extract_graph_nodes(boundary, contents)
edges = self._extract_graph_edges(project, contents.recipes)

flow_graph = {
    "nodes": nodes,
    "edges": edges
}

# Pass to constructor
return EnhancedBlockMetadata(
    # ...
    flow_graph=flow_graph
)
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_identifier.py`

```python
def test_extract_block_metadata_includes_graph(self, mock_project):
    identifier = BlockIdentifier(...)
    meta = identifier.extract_block_metadata("PROJ", "ZONE", boundary)
    assert meta.flow_graph is not None
    assert "nodes" in meta.flow_graph
    assert "edges" in meta.flow_graph
```

---

## Acceptance Criteria

- [ ] Metadata includes populated `flow_graph`

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
   git checkout -b feature/p4-f003
   ```

### After Implementation

4. **Push feature branch:**
   ```bash
   git push -u origin feature/p4-f003
   ```

5. **Create PR to master:**
   ```bash
   gh pr create --base master --title "feat(p4-f003): <description>"
   ```

**Never use Reusable_Workflows branch!**

---