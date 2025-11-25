# Clean Development Documentation

Audit and archive stale development documentation from the project root.

## Your Task

Identify development notes, coordination files, and stale documentation in the project root that can be safely moved to `docs/archive/`.

## How This Works

### Step 1: Audit

First, scan all `.md` files in the project root and identify candidates for archival based on:

**Pattern Matching** (always candidates):
- `DEV_`, `WIP_`, `DRAFT_`, `TODO_`, `TEMP_` prefixes
- `_COMPLETE.md`, `_SETUP.md`, `_SPEC.md`, `_PLAN.md` suffixes
- Files containing `WORKFLOW`, `COORDINATION`, `ARCHITECTURE`, `CODE_REVIEW`

**Age-Based** (default: >14 days old):
- Non-protected files older than the threshold

**Protected Files** (never archive):
- `README.md`, `CLAUDE.md`, `CHANGELOG.md`, `CONTRIBUTING.md`
- `LICENSE.md`, `HOW_TO_USE.md`, `QUICK_REFERENCE.md`

### Step 2: Report

Display a summary showing:
- Total markdown files in root
- Candidates for archival (with reason: pattern or age)
- Protected files that will be kept

### Step 3: Confirm and Archive

After reviewing the candidates, move selected files to `docs/archive/`.

## Arguments (Optional)

- `/clean-dev-docs` - Audit with default 14-day age threshold
- `/clean-dev-docs 30` - Use 30-day age threshold

## Expected Output

```
Development Docs Audit

Threshold: 14 days
Total docs in root: 12

Archive Candidates (5):
- DEV_NOTES.md (pattern: DEV_ prefix, 3 days old)
- WORKFLOW_UPDATE.md (pattern: WORKFLOW, 8 days old)
- OLD_SPEC.md (age: 45 days old)
- BUILD_STATUS.md (pattern: _STATUS suffix, 20 days old)
- DRAFT_API.md (pattern: DRAFT_ prefix, 2 days old)

Protected (will keep):
- README.md
- CLAUDE.md
- HOW_TO_USE.md

Would you like me to archive these 5 files to docs/archive/?
```

## Protocol for Ongoing Development

When creating new development documentation:
1. Use prefixes like `DEV_`, `WIP_`, `DRAFT_` for work-in-progress
2. Use `_COMPLETE.md` suffix for milestone markers (auto-cleaned)
3. Coordination files will be auto-detected by pattern
4. Run `/clean-dev-docs` periodically to keep root clean

## Notes

- Files are moved, not deleted (recoverable from docs/archive/)
- Protected files cannot be archived even if explicitly requested
- The archive is tracked in git for history
