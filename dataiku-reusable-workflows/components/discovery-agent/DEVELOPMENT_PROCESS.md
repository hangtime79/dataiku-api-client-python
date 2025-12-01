# Development Process for Discovery Agent Features

## Critical Pre-Development Checklist

### STEP 1: Check for Outstanding Pull Requests

**BEFORE starting ANY development work:**

```bash
gh pr list --repo hangtime79/dataiku-api-client-python --state open
```

**Decision:**
- ✅ **If NO open PRs:** Proceed to Step 2
- ❌ **If ANY open PRs exist:** STOP! Do not start development until all PRs are merged or closed

**Rationale:** We maintain a single-PR workflow to avoid merge conflicts and ensure clean integration.

---

### STEP 2: Sync Local Master with Remote

```bash
# Ensure you're on master
git checkout master

# Pull latest changes from remote
git pull origin master

# Verify you're up to date
git log --oneline -5
```

**Verify:** Your local master should match `origin/master` exactly.

---

### STEP 3: Create Feature Branch from Master

```bash
# Create and checkout new feature branch
git checkout -b feature/PX-FYYY-feature-name

# Example:
# git checkout -b feature/P7-F001-generate-datasets-section
```

**Branch Naming Convention:**
- Pattern: `feature/PX-FYYY-short-description`
- `X` = Phase number
- `YYY` = Feature number (001, 002, etc.)
- Use lowercase with hyphens for description

---

## Development Workflow

### STEP 4: Implement Feature

1. **Read the feature spec completely** before implementing
2. **Follow scope boundaries exactly:**
   - Do ONLY what's in "IN SCOPE"
   - Do NOT do anything in "OUT OF SCOPE"
3. **Create tests as you implement** (don't defer testing)
4. **Run tests frequently** to catch issues early

### STEP 5: Verify Tests Pass

```bash
# Run feature-specific tests
pytest path/to/your/tests -v

# Run broader test suite to ensure no regressions
pytest path/to/related/tests -v
```

**All tests MUST pass before proceeding.**

---

## Commit and Push Workflow

### STEP 6: Commit Changes

```bash
# Stage your changes
git add <modified-files>

# Commit with descriptive message
git commit -m "feat(PX-FYYY): <concise description>

<Detailed description of changes>

Tests:
- X/X tests passing (100%)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Commit Message Format:**
- First line: `feat(PX-FYYY): <50 char summary>`
- Blank line
- Detailed description (what, why, how)
- Test results
- Claude Code attribution

### STEP 7: Push Feature Branch to Remote

```bash
# Push feature branch to hangtime79 remote
git push -u origin feature/PX-FYYY-feature-name
```

---

## Pull Request Workflow

### STEP 8: Create Pull Request

```bash
# Create PR using GitHub CLI
gh pr create --title "feat(PX-FYYY): <title>" --body "$(cat <<'EOF'
## Summary

<Concise summary of changes>

### Changes
- Change 1
- Change 2

### Tests
- X/X tests passing (100%)

### Related
- Implements feature PX-FYYY from Discovery Agent Enhancement Plan

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)" --base master
```

**PR Requirements:**
- **Base branch:** Always `master` (NOT Reusable_Workflows!)
- **Title:** Clear, concise, includes feature ID
- **Description:** Summarizes changes, test results, context
- **State:** Should be mergeable (no conflicts)

### STEP 9: Verify PR Status

```bash
# Check PR status
gh pr view <PR-number> --json state,mergeable,url

# Expected output:
# {
#   "mergeable": "MERGEABLE",
#   "state": "OPEN",
#   "url": "https://github.com/..."
# }
```

**If conflicts exist:** The PR was not created from an up-to-date master. See troubleshooting.

---

## Important Notes

### ❌ NEVER Use "Reusable_Workflows" Branch

**Old (incorrect) process:**
```bash
git checkout Reusable_Workflows  # ❌ NEVER DO THIS
git pull origin Reusable_Workflows  # ❌ NEVER DO THIS
```

**Correct process:**
```bash
git checkout master  # ✅ Always work from master
git pull origin master  # ✅ Always sync with master
```

### Why Single-PR Workflow?

1. **Prevents conflicts:** Only one person/feature changes master at a time
2. **Clean integration:** Each PR builds on latest stable master
3. **Clear history:** Linear commit history, easy to track
4. **Faster reviews:** Focused PRs get reviewed and merged quickly

### What If PRs Are Blocked?

**If PRs are open when you want to start:**
1. Check with team if PRs can be merged soon
2. Help review/test open PRs to unblock them
3. Wait for merge before starting new work

**Do NOT:**
- Create PRs that stack on unmerged branches
- Work in parallel on separate features
- Force push to master

---

## Troubleshooting

### PR Has Conflicts

**Cause:** Local master was not synced before creating feature branch.

**Fix:**
```bash
# 1. Ensure local master is updated
git checkout master
git pull origin master

# 2. Rebase your feature branch
git checkout feature/PX-FYYY-name
git rebase master

# 3. Force push (rewrites history)
git push -f origin feature/PX-FYYY-name

# 4. Verify PR shows MERGEABLE
gh pr view <PR-number> --json mergeable
```

### Tests Failing

**Before creating PR:**
1. Run full test suite locally
2. Fix all failures
3. Commit fixes
4. Re-run tests
5. Only create PR when 100% passing

### Accidentally Worked on Wrong Branch

**If you committed to master:**
```bash
# 1. Create feature branch from current state
git checkout -b feature/PX-FYYY-name

# 2. Reset master to remote
git checkout master
git reset --hard origin/master

# 3. Push feature branch
git checkout feature/PX-FYYY-name
git push -u origin feature/PX-FYYY-name
```

---

## Quick Reference

**Pre-Development:**
1. ✅ Check for open PRs (`gh pr list`)
2. ✅ Sync master (`git pull origin master`)
3. ✅ Create feature branch (`git checkout -b feature/PX-FYYY-name`)

**Development:**
4. ✅ Implement feature
5. ✅ Write/run tests
6. ✅ All tests pass

**Post-Development:**
7. ✅ Commit changes
8. ✅ Push to remote (`git push -u origin feature/PX-FYYY-name`)
9. ✅ Create PR to master (`gh pr create --base master`)
10. ✅ Verify PR is mergeable

**Never:**
- ❌ Use Reusable_Workflows branch
- ❌ Start development with open PRs
- ❌ Skip syncing master
- ❌ Create PRs with conflicts

---

**Last Updated:** 2025-12-01
**Version:** 1.0
