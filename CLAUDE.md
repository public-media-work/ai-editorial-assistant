# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

PBS Wisconsin Editorial Assistant - A system for processing video transcripts and generating SEO-optimized metadata (titles, descriptions, keywords) for streaming platforms.

## Key Commands

### Development
```bash
# Build the MCP server
cd mcp-server && npm run build

# Run queue processing
python3 scripts/process_queue_auto.py
```

### Custom Slash Commands
- `/brainstorm` - Process a transcript and generate brainstorming document
- `/process-transcript` - Full transcript processing workflow
- `/archive-transcripts` - Move processed transcripts to archive
- `/prioritize-transcript <name>` - Move transcript to front of queue
- `/archive-old-projects` - Archive output folders older than 30 days
- `/clean-dev-docs` - Audit and archive stale development documentation
- `/check-pricing` - Verify LLM pricing and re-evaluate model priority (run monthly)

## Architecture

```
editorial-assistant/
├── mcp-server/          # MCP server (TypeScript) for Claude Desktop integration
├── scripts/             # Python processing scripts
├── transcripts/         # Input transcripts (gitignored except examples/)
├── OUTPUT/              # Processed project outputs (gitignored except examples/)
├── .claude/
│   ├── agents/          # Agent instruction files
│   ├── commands/        # Slash command definitions
│   └── templates/       # Output templates
└── docs/archive/        # Archived development documentation
```

## Git Commit Convention

**IMPORTANT**: AI-generated commits should include agent attribution for tracking purposes.

**See**: `/Users/mriechers/Developer/workspace_ops/conventions/COMMIT_CONVENTIONS.md`

**Quick Reference**: AI commits should include `[Agent: <name>]` after the subject line. Human commits do not require this.

Example AI commit:
```
feat: Add new feature

[Agent: Main Assistant]

Detailed description of the change...
```

## Documentation Conventions

### File Naming for Development Docs

Use these prefixes/suffixes so the cleanup system can identify stale docs:

| Pattern | Purpose | Example |
|---------|---------|---------|
| `DEV_*.md` | Development notes | `DEV_API_NOTES.md` |
| `WIP_*.md` | Work in progress | `WIP_NEW_FEATURE.md` |
| `DRAFT_*.md` | Draft documents | `DRAFT_SPEC.md` |
| `TEMP_*.md` | Temporary notes | `TEMP_DEBUG_LOG.md` |
| `*_COMPLETE.md` | Milestone markers | `FEATURE_COMPLETE.md` |
| `*_SETUP.md` | Setup documentation | `LOCAL_LLM_SETUP.md` |
| `*_SPEC.md` | Specifications | `MCP_SERVER_SPEC.md` |
| `*_PLAN.md` | Planning documents | `AUTOMATION_PLAN.md` |
| `*_STATUS.md` | Status updates | `BUILD_STATUS.md` |

### Protected Files (Never Auto-Archived)

These files are protected from the `/clean-dev-docs` command:
- `README.md` - Project overview
- `CLAUDE.md` - This file (Claude Code instructions)
- `HOW_TO_USE.md` - User guide
- `QUICK_REFERENCE.md` - Quick reference
- `CHANGELOG.md` - Version history
- `CONTRIBUTING.md` - Contribution guidelines
- `LICENSE.md` - License information

### Cleanup Protocol

Run `/clean-dev-docs` periodically to audit and archive stale documentation:
1. Files matching the patterns above are flagged as candidates
2. Files older than 14 days (configurable) are also flagged
3. Review candidates before archiving
4. Archived files go to `docs/archive/` (preserved in git history)

## Long-Running Harness (Initializer + Coding Agent)

- Start every session with `./init.sh`, then read `claude-progress.txt` and `feature_list.json` to select a single feature (`pending` → `in_progress`).
- Initializer agent: ensure context is loaded (this file + DEV_LONG_RUNNING_AGENT_PLAN.md), refresh the queue, and set the next feature.
- Coding agent: work one feature end-to-end, verify results/tests, update `feature_list.json` and `claude-progress.txt`, and keep the tree clean with an attributed commit.
- Never mark `passes: true` without verification; do not remove features; prefer small, plan-first changes.
- New feedback belongs in `USER_FEEDBACK.md` (intake) and then in `feature_list.json` (queue).

## Directory Conventions

### Folders with Gitignored Contents

These folders are tracked but their contents (except examples) are gitignored:

| Folder | Purpose | Tracked |
|--------|---------|---------|
| `transcripts/` | Input transcript files | Only `examples/` and `.gitkeep` |
| `transcripts/archive/` | Processed transcripts | Only `.gitkeep` |
| `OUTPUT/` | Processed project outputs | Only `examples/` and `.gitkeep` |
| `OUTPUT/archive/` | Old projects (>30 days) | Only `.gitkeep` |

### Example Files

Example files in `transcripts/examples/` and `OUTPUT/examples/` are committed to demonstrate expected formats for new machine setup.

## Notes for Claude Code

1. **Include agent attribution** in commits for tracking purposes
2. **Use dev doc naming conventions** for temporary/planning documents
3. **Run cleanup periodically** via `/clean-dev-docs` to keep root clean
4. **Don't commit actual transcripts or outputs** - only examples
5. **Rebuild MCP server** after TypeScript changes: `cd mcp-server && npm run build`
