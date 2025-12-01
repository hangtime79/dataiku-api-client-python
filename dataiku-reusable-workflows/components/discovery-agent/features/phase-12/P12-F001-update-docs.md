# Feature Specification: Update Documentation

> **Usage:** Copy this template for each feature. Fill in all sections. Do not skip sections - if something doesn't apply, write "N/A" with a reason.

---

## Feature Identity

| Field | Value |
|-------|-------|
| **Feature ID** | `P12-F001` |
| **Feature Name** | Update Discovery Agent Documentation |
| **Parent Phase** | Phase 12: Documentation |
| **Estimated LOC** | N/A (Markdown) |
| **Complexity** | Low |
| **Parallel Safe** | Yes |

---

## Context

Document the new capabilities in the component README so users know about the rich metadata features.

---

## Scope Boundaries

### IN SCOPE (Do exactly these things)

- [ ] Update `components/discovery-agent/README.md`
- [ ] Add "Features" section listing: Rich Metadata, Flow Diagrams, Schema Extraction
- [ ] Add "Output Example" showing the new Wiki structure

---

## Dependencies

### Requires Complete

_None_

---

## File Operations

```
MODIFY:    components/discovery-agent/README.md
```

---

## Implementation Guidance

Add text describing:
1.  **Rich Metadata**: Now captures schemas, connections, and types.
2.  **Visualizations**: Automatic Mermaid flow diagrams.
3.  **Scannability**: Quick summary blocks and navigation menus.

---

## Acceptance Criteria

- [ ] README updated
- [ ] clearly describes new features

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
   git checkout -b feature/p12-f001
   ```

### After Implementation

4. **Push feature branch:**
   ```bash
   git push -u origin feature/p12-f001
   ```

5. **Create PR to master:**
   ```bash
   gh pr create --base master --title "feat(p12-f001): <description>"
   ```

**Never use Reusable_Workflows branch!**

---