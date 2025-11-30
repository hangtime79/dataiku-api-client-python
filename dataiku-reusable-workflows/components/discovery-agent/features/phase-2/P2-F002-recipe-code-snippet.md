# Feature Specification: Recipe Code Snippet

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P2-F002` |
| **Feature Name** | Extract Recipe Code Snippet |
| **Parent Phase** | Phase 2: Recipe Metadata Extraction |
| **Estimated LOC** | ~20 lines |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

For code-based recipes (Python, SQL, R), we want to show the first 10 lines of code in the documentation to give context on what the recipe does.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Add `_extract_code_snippet(self, recipe_settings)` helper
- [ ] Check if recipe has payload (code)
- [ ] Extract first 10 lines
- [ ] Return `None` if no code found

### OUT OF SCOPE (Do NOT do these things)

- ❌ DO NOT: Extract full code (too large)

---

## Dependencies

### Requires Complete

_None_

---

## File Operations

```
MODIFY:    dataikuapi/iac/workflows/discovery/identifier.py
           └─ Add method _extract_code_snippet()
```

---

## Implementation Guidance

```python
def _extract_code_snippet(self, raw_settings: Dict) -> Optional[str]:
    # Step 1: Check payload
    payload = raw_settings.get("payload")
    if not payload:
        return None
        
    # Step 2: Split and slice
    lines = payload.strip().split('\n')
    snippet = '\n'.join(lines[:10])
    
    # Step 3: Add indicator if truncated
    if len(lines) > 10:
        snippet += "\n... (truncated)"
        
    return snippet
```

---

## Test Specification

### Unit Test

**File:** `tests/iac/workflows/discovery/unit/test_identifier_helpers.py`

```python
def test_extract_code_snippet():
    identifier = BlockIdentifier(...)
    settings = {"payload": "line1\nline2\n" + ("line\n"*20)}
    snippet = identifier._extract_code_snippet(settings)
    assert "truncated" in snippet
    assert snippet.count("\n") <= 11 # 10 lines + truncation msg
```

---

## Acceptance Criteria

- [ ] Helper method exists
- [ ] Returns first 10 lines
- [ ] Handles missing payload (returns None)

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P2-F002-recipe-code-snippet
```