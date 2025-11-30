# Feature Specification: Generate Mermaid Diagram

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P8-F001` |
| **Feature Name** | Generate Mermaid Syntax |
| **Parent Phase** | Phase 8: Wiki Flow Diagram Generation |
| **Estimated LOC** | ~40 lines |
| **Complexity** | Medium |
| **Parallel Safe** | Yes |

---

## Context

Convert the generic flow graph structure (nodes/edges) into Mermaid JS Markdown syntax supported by Dataiku Wiki.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_generate_flow_diagram(self, flow_graph)` to `CatalogWriter`
- [ ] Generate `graph LR` header
- [ ] Iterate nodes: sanitize IDs, format based on type (Square for Recipe, Cylinder for Dataset)
- [ ] Iterate edges: `A --> B`
- [ ] Wrap in mermaid code block

---

## Dependencies

### Requires Readable

| File | What you need from it |
|------|----------------------|
| `dataikuapi/iac/workflows/discovery/models.py` | EnhancedBlockMetadata |

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/catalog_writer.py
           └─ Add method _generate_flow_diagram()
```

---

## Implementation Guidance

```python
def _generate_flow_diagram(self, flow_graph: Dict[str, Any]) -> str:
    if not flow_graph:
        return ""
        
    nodes = flow_graph.get("nodes", [])
    edges = flow_graph.get("edges", [])
    
    mermaid = "```mermaid\ngraph LR\n"
    
    # Define Nodes
    for node in nodes:
        nid = node["id"].replace(" ", "_") # Sanitize
        label = node["id"]
        if node["type"] == "DATASET":
            # Cylinder shape for datasets: [Label] or [ (Label) ] syntax depends on mermaid version
            # Using simple box for robustness first: [Label]
            mermaid += f"    {nid}[{label}]\n"
        else:
            # Rounded rect for recipes
            mermaid += f"    {nid}({label})\n"
            
    # Define Edges
    for edge in edges:
        src = edge["source"].replace(" ", "_")
        tgt = edge["target"].replace(" ", "_")
        mermaid += f"    {src} --> {tgt}\n"
        
    mermaid += "```\n"
    return mermaid
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_catalog_writer_graph.py` (New file)

```python
def test_generate_flow_diagram():
    writer = CatalogWriter()
    graph = {
        "nodes": [{"id": "DS1", "type": "DATASET"}, {"id": "RC1", "type": "RECIPE"}],
        "edges": [{"source": "DS1", "target": "RC1"}]
    }
    diagram = writer._generate_flow_diagram(graph)
    
    assert "graph LR" in diagram
    assert "DS1 --> RC1" in diagram
    assert "DS1[DS1]" in diagram
```

---

## Acceptance Criteria

- [ ] Generates valid Mermaid syntax
- [ ] Sanitizes IDs (spaces to underscores)
- [ ] Handles empty graph

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P8-F001-generate-mermaid-diagram
```