# Feature Specification: Integration Test Setup

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P11-F001` |
| **Feature Name** | Setup Integration Test Fixtures |
| **Parent Phase** | Phase 11: Integration Testing |
| **Estimated LOC** | ~30 lines |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

We need to validate the full flow against a real Dataiku instance. This feature sets up the test file and fixtures to connect to the `COALSHIPPINGSIMULATIONGSC` project.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Create `tests/iac/workflows/discovery/integration/test_enhanced_discovery.py`
- [ ] Add `real_client` fixture (if not already in conftest)
- [ ] Add test skeleton `test_full_discovery_flow`
- [ ] Verify environment variables `DSS_HOST`, `DSS_API_KEY`

---

## Dependencies

### Requires Complete

_None (Tests can be written anytime, but run last)_

---

## File Operations

```
CREATE:    tests/iac/workflows/discovery/integration/test_enhanced_discovery.py
```

---

## Implementation Guidance

```python
import os
import pytest
from dataikuapi.iac.workflows.discovery.agent import DiscoveryAgent

@pytest.mark.integration
@pytest.mark.skipif(os.environ.get("USE_REAL_DATAIKU") != "true", reason="Requires real instance")
def test_full_discovery_flow(real_client):
    """
    Runs the full discovery agent against COALSHIPPINGSIMULATIONGSC
    and verifies the output structure.
    """
    project_key = "COALSHIPPINGSIMULATIONGSC"
    
    # 1. Init Agent
    agent = DiscoveryAgent(client=real_client)
    
    # 2. Run Discovery
    # (Implementation in next feature)
    pass
```

---

## Test Specification

### Quick Sanity Check

```bash
# Run with env vars
export USE_REAL_DATAIKU=true
pytest tests/iac/workflows/discovery/integration/test_enhanced_discovery.py -v
```

---

## Acceptance Criteria

- [ ] Test file created
- [ ] Fixtures work
- [ ] Test is skipped if env var missing

---

## Merge Instructions

### Branch

```bash
git checkout Reusable_Workflows
git pull origin Reusable_Workflows
git checkout -b feature/P11-F001-integration-setup
```