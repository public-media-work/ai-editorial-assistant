# Claude Code Infrastructure Sprint - Editorial Assistant

## Context & Constraints

You are Claude Code running an infrastructure sprint on this repository. This is a **one-time credit-funded initiative** focused on high-leverage improvements that reduce future maintenance costs and token usage.

**Budget Parameters:**
- Target sprint cost: ~$75-100 in credits
- Estimated session count: 3-5 focused sessions
- Timeline: Complete within 1 week of wall-clock time
- Token optimization: Prioritize work that reduces future LLM dependency

**Your Role:**
- Infrastructure architect and implementer
- Code quality improver
- Documentation generator
- NOT a feature developer (unless features reduce operational costs)

## Sprint 2: editorial-assistant

**Repository Context:**
- **Current State:** Working MCP-based editorial workflow with Gemini preprocessing. Pain points: token usage monitoring, workflow phase boundaries, feature evolution without clear architecture.
- **Primary Goal:** "Deep-dive rework of core features with clear separation of concerns and token optimization"
- **Technology Stack:** Python 3.11+, MCP protocol, Gemini API, file-based state management

**Special Considerations:**
```
- Transcript preprocessing should be clearly delegated to cheaper models
- Editorial workflow phases should have clean interfaces
- Token usage should be logged and monitored with warnings
- File versioning logic should be bulletproof
- Integration with PBS metadata standards should be well-documented
```

**Expected Outcomes:**
- Clear phase separation (preprocess → edit → analyze)
- Token usage monitoring dashboard
- Comprehensive workflow documentation
- Error recovery mechanisms
- Template library for common editorial patterns

**Estimated Credit Usage:** $80-100 (complex refactoring needs)

## Sprint Objectives

### Primary Goal
Your main goal is to identify opportunities to make this tool more sustainable in the long run, including iterating on the logic and mechanisms present for controlling API costs. 

### Success Criteria
At sprint completion, this repository should have:

1. **Improved Maintainability**
   - [ ] Code follows consistent style and patterns
   - [ ] Complex logic is well-documented with rationale
   - [ ] Dependencies are clearly managed and up-to-date
   - [ ] Error handling is comprehensive and informative

2. **Better Documentation**
   - [ ] README explains what, why, and how
   - [ ] Architecture is documented with diagrams/explanations
   - [ ] Setup instructions work for someone new to the project
   - [ ] API/interface contracts are clearly defined

3. **Reduced Future Token Usage**
   - [ ] Common tasks are scripted/automated
   - [ ] Error messages are self-explanatory
   - [ ] Examples/templates exist for frequent operations
   - [ ] Debugging is easier (less "why is this failing" sessions)

4. **Quality Infrastructure**
   - [ ] Critical paths have tests
   - [ ] Validation catches errors early
   - [ ] Logging provides useful diagnostic information
   - [ ] Configuration is externalized and documented

### Out of Scope
To conserve credits, explicitly DO NOT:
- Add new features unless they directly reduce maintenance burden
- Refactor working code that's already clear and documented
- Over-engineer solutions (prefer simple, documented approaches)
- Bikeshed style preferences (follow existing patterns)

## Sprint Phases

### Phase 1: Audit & Planning (Session 1)
**Goal:** Understand current state and create improvement roadmap

**Tasks:**
1. Read all source files to understand architecture
2. Identify technical debt and pain points
3. Catalog undocumented behavior and implicit assumptions
4. Prioritize improvements by ROI (effort vs. future token savings)
5. Create a phased implementation plan

**Deliverable:** `SPRINT_PLAN.md` with prioritized improvements and effort estimates

### Phase 2: Core Improvements (Sessions 2-3)
**Goal:** Execute highest-priority infrastructure work

**Focus Areas (prioritize by ROI):**
- Code quality: Type hints, error handling, consistent patterns
- Documentation: Inline comments, README updates, architecture docs
- Testing: Critical path coverage, validation logic
- Automation: Scripts for common tasks, setup/deployment
- Configuration: Externalize magic numbers, document options

**Approach:**
- Start with quick wins (high impact, low effort)
- Batch similar changes together
- Commit frequently with clear messages
- Document decisions and rationale as you go

**Deliverable:** Improved codebase with comprehensive documentation

### Phase 3: Knowledge Capture (Session 4)
**Goal:** Create artifacts that prevent future "how does this work" sessions

**Tasks:**
1. Generate comprehensive README if missing/inadequate
2. Create architecture documentation (how components interact)
3. Write runbooks for common operations
4. Document lessons learned during sprint
5. Create troubleshooting guide for known issues
6. Build examples/templates for typical use cases

**Deliverable:** Complete documentation set that reduces future LLM dependency

### Phase 4: Validation & Handoff (Session 5)
**Goal:** Ensure work is complete and maintainable

**Tasks:**
1. Run all tests and validation
2. Verify setup instructions work from scratch
3. Create `SPRINT_SUMMARY.md` documenting:
   - What was accomplished
   - What was intentionally deferred
   - Recommendations for future work
   - Estimated token/cost savings from improvements
4. Clean up temporary files and commented-out code
5. Final commit with sprint summary

**Deliverable:** Production-ready repository with handoff documentation

## Working Principles

### Code Quality Standards
```python
# GOOD: Self-documenting with rationale
def preprocess_transcript(text: str) -> str:
    """
    Clean transcript text for editorial processing.
    
    We normalize whitespace because raw transcripts often have
    inconsistent spacing that breaks downstream keyword extraction.
    We preserve paragraph breaks because they indicate speaker changes.
    
    Args:
        text: Raw transcript text from transcription service
        
    Returns:
        Cleaned transcript ready for editorial assistant
        
    Raises:
        ValueError: If text is empty or only whitespace
    """
    if not text or not text.strip():
        raise ValueError("Cannot process empty transcript")
    
    # Normalize whitespace within lines (but preserve paragraph breaks)
    # This prevents downstream regex patterns from failing on irregular spacing
    lines = text.split('\n\n')
    cleaned_lines = [' '.join(line.split()) for line in lines]
    
    return '\n\n'.join(cleaned_lines)

# BAD: Requires future LLM sessions to understand
def process(t):
    return '\n\n'.join([' '.join(l.split()) for l in t.split('\n\n')])
```

### Documentation Standards
- Every module has a docstring explaining its purpose and role in the system
- Every public function has comprehensive docstring (what, why, args, returns, raises)
- Complex algorithms have inline comments explaining the approach
- Magic numbers are replaced with named constants with explanations
- Configuration options are documented with examples

### Testing Standards
- Critical paths have test coverage (not aiming for 100%, just safety nets)
- Edge cases that have caused bugs are captured as tests
- Tests serve as documentation of expected behavior
- Test names explain what they're validating

## Special Considerations for This Repository

[FILL IN: Repository-specific notes, e.g.,

**For workspace-ops:**
- MCP servers must have clear error messages (they're called by other agents)
- Agent onboarding docs should be copy-paste ready
- Configuration should be centralized and well-documented

**For editorial-assistant:**
- Transcript preprocessing should be delegated to cheaper models
- Editorial workflow should be clearly separated into phases
- Token usage should be logged and monitored

**For obsidian-config:**
- Plugin separation should enable independent development
- MCP service should have clean API contracts
- Integration points should be well-documented]

## Context for Future Optimization

This sprint is part of a larger strategy to optimize LLM usage:
- Daily work uses Claude Sonnet 4.5 (paid tier, limited allocation)
- Routine tasks route to ChatGPT Plus (employer-funded) or Gemini (education license)
- Infrastructure improvements reduce future token consumption
- Documentation reduces "how does this work" questions

Your improvements should make this repository:
1. **Self-documenting** → fewer clarification questions needed
2. **Error-resistant** → less debugging time
3. **Well-tested** → more confidence in changes
4. **Clearly structured** → easier to understand and modify

## Handoff Requirements

When the sprint is complete, create `SPRINT_SUMMARY.md` with:

### What Was Accomplished
- Concrete list of improvements made
- Key decisions and rationale
- Metrics: lines of code changed, tests added, documentation created

### Immediate Next Steps
- Any critical follow-up work
- Known issues that weren't addressed
- Recommendations for user testing/validation

### Future Recommendations
- Lower-priority improvements worth considering
- Technical debt that should be addressed eventually
- Ideas for further optimization

### Estimated Impact
- Time savings per month from automation
- Token savings from better documentation
- Reduced debugging/troubleshooting sessions
- Improved developer experience metrics

## Working with Mark

**Communication preferences:**
- Mark values precision in language
- Extensive documentation and commenting is preferred
- Explanations should clarify "why" not just "what"
- Code should be readable and self-documenting

**Learning focus:**
- Mark is actively learning to code
- Implementation details should be explained thoroughly
- Design decisions should include rationale
- Educational comments are encouraged

**Workflow:**
- Uses Homebrew for package management (macOS)
- Maintains notes in Obsidian with PARA system
- Works with PBS Wisconsin on content/media projects
- Balancing multiple repositories and projects

## Begin Sprint

**First action:** Read the current codebase thoroughly, then create `SPRINT_PLAN.md` with your proposed approach, prioritized task list, and effort estimates.

**Remember:** This is a one-time infrastructure investment. Prioritize work that has lasting impact and reduces future token usage. When in doubt, choose the approach that makes the codebase more self-explanatory.

---

**Ready to begin? Start by reading the repository contents and creating your sprint plan.**