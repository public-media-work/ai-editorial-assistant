# Revise Copy (Phase 2)

You are working within the PBS Wisconsin Editorial Assistant CLI workflow.

## Agent Instructions

**CRITICAL**: Before proceeding, read and internalize the agent instructions at:
`.claude/agents/copy-editor.md`

You MUST follow all rules, guidelines, and output formats specified in that agent file. This includes:
- Side-by-side original vs. proposed comparison
- Clear reasoning for each edit
- Character count verification
- AP Style compliance
- Program-specific rule enforcement
- Template format from `.claude/templates/copy-revision-document.md`

## Your Task

1. **Find the project** - Look in `OUTPUT/` for the active project
2. **Read prior work** - Load `01_brainstorming.md` if it exists
3. **Get draft copy from user** - The user will provide their draft title, descriptions, and/or keywords
4. **Read the agent instructions** - Load `.claude/agents/copy-editor.md`
5. **Compare draft against transcript** - Verify factual accuracy
6. **Identify issues**:
   - AP Style violations
   - Prohibited language
   - Character limit exceeded
   - Title/description pairing problems
   - Program-specific rule violations
7. **Generate revision document** with side-by-side comparisons
8. **Save to** `OUTPUT/{project_name}/02_copy_revision.md`
9. **Update `.state.json`** to mark Phase 2 in progress
10. **Ask feedback questions** to guide next iteration

## Input Expected

The user should provide their draft copy:
- **Title** (80 chars max)
- **Short Description** (100 chars max)
- **Long Description** (350 chars max)
- **Keywords** (comma-separated list)

They may also provide:
- Specific concerns or requests
- Program name (if not already known)
- Feedback on previous revision

## Revision Principles

- **It's acceptable to say content needs no changes** if it meets requirements
- **Minimize edits while applying expertise** - don't over-edit working copy
- Preserve user's voice and tone where possible
- Focus edits on compliance, accuracy, and SEO - not stylistic preferences
- Always explain trade-offs when edit improves one aspect but affects another

## Output Requirements

The copy revision document MUST:
- Follow `.claude/templates/copy-revision-document.md` structure
- Show original and proposed side-by-side in tables
- Provide detailed reasoning for every change
- Include exact character counts (before and after)
- Verify title/description pairing cohesion
- List feedback questions for user
- Suggest next steps (iterate, SEO research, or proceed to implementation)

## Feedback Integration

When user provides feedback on a revision:
1. **Acknowledge specifics**: "You mentioned the title feels too technical..."
2. **Propose targeted revision**: Show updated version addressing that concern
3. **Explain trade-off**: "This makes it more accessible but reduces keyword density..."
4. **Ask confirmation**: "Does this revision better capture your intent?"
5. **Update revision history**: Track iterations in the document

## After Completion

Display:
- Summary of changes made
- Key issues identified and resolved
- Feedback questions for user
- Next steps (provide feedback, request SEO research, or finalize)

Now proceed: Get the user's draft copy and generate the revision document.
