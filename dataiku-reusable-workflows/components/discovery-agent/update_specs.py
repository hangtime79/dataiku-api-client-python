#!/usr/bin/env python3
"""
Update all feature specification files to use correct git workflow.

Replaces old Reusable_Workflows branch references with correct master-based workflow.
"""

import os
import re
from pathlib import Path

# Correct merge instructions template
CORRECT_MERGE_INSTRUCTIONS = """## Merge Instructions

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
   git checkout -b feature/{FEATURE_ID}
   ```

### After Implementation

4. **Push feature branch:**
   ```bash
   git push -u origin feature/{FEATURE_ID}
   ```

5. **Create PR to master:**
   ```bash
   gh pr create --base master --title "feat({FEATURE_ID}): <description>"
   ```

**Never use Reusable_Workflows branch!**

---
"""


def update_file(filepath):
    """Update a single feature spec file."""
    with open(filepath, "r") as f:
        content = f.read()

    # Pattern to match old merge instructions section (more flexible)
    old_pattern = r"## Merge Instructions\s+###\s+Branch\s+```bash\s+git checkout Reusable_Workflows\s+git pull origin Reusable_Workflows\s+git checkout -b feature/[^\n]+\s+```"

    # Extract feature ID from filename or content
    feature_id = None
    # Try to extract from filename (e.g., P7-F001-name.md -> P7-F001)
    filename = os.path.basename(filepath)
    match = re.match(r"(P\d+-F\d+)", filename)
    if match:
        feature_id = match.group(1)

    # If not in filename, try to extract from content
    if not feature_id:
        id_match = re.search(r"\|\s*\*\*Feature ID\*\*\s*\|\s*`(P\d+-F\d+)`", content)
        if id_match:
            feature_id = id_match.group(1)

    if not feature_id:
        print(f"⚠️  Could not determine feature ID for {filepath}")
        feature_id = "PX-FXXX-feature-name"

    # Replace with correct instructions
    replacement = CORRECT_MERGE_INSTRUCTIONS.replace("{FEATURE_ID}", feature_id.lower())

    # Try to replace
    new_content, count = re.subn(
        old_pattern, replacement.rstrip(), content, flags=re.DOTALL
    )

    if count > 0:
        with open(filepath, "w") as f:
            f.write(new_content)
        return True, feature_id

    return False, feature_id


def main():
    """Update all feature spec files."""
    base_dir = Path(__file__).parent / "features"

    if not base_dir.exists():
        print(f"❌ Features directory not found: {base_dir}")
        return

    # Find all .md files in features directory
    spec_files = list(base_dir.rglob("*.md"))

    print(f"Found {len(spec_files)} specification files\n")

    updated_count = 0
    skipped_count = 0

    for spec_file in sorted(spec_files):
        updated, feature_id = update_file(spec_file)
        if updated:
            print(
                f"✅ Updated: {spec_file.relative_to(base_dir.parent)} ({feature_id})"
            )
            updated_count += 1
        else:
            print(
                f"⏭️  Skipped: {spec_file.relative_to(base_dir.parent)} (no old pattern found)"
            )
            skipped_count += 1

    print(f"\n{'='*60}")
    print("Summary:")
    print(f"  Updated: {updated_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Total:   {len(spec_files)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
