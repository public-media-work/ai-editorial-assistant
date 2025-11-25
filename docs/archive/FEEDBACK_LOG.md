# Stakeholder Feedback Log

## 2025-11-06 – CLI MVP Review

**Context**  
Codex agent review of the ADHD-friendly CLI reset to capture issues before stakeholder sync.

**Key Findings**
- `editorial_assistant.py:183` and `editorial_assistant.py:202` reference `editorial-assistant transcript` / `editorial-assistant continue`, but those commands are not implemented yet, so the onboarding flow immediately dead-ends after project creation.
- `editorial_assistant.py:191-200` instantiates `ProjectState` even when the provided path does not exist; the CLI surfaces a fresh “0 % progress” state instead of warning about the typo, hiding real user mistakes.
- `editorial_assistant.py:63-66` loads `.state.json` without error handling. Any partial write or manual edit causes a crash instead of guiding the user to recover.
- `editorial_assistant.py:27-50` leans on raw ANSI color codes and emoji. Windows consoles or accessibility tooling that cannot render them will show noisy escape sequences, undermining the calming UX goal.

**Questions for the Team**
- What is the timeline for shipping the Phase 1 transcript workflow? If it is not imminent, should we adjust onboarding copy to match the commands that actually exist today?
- Do we have explicit compatibility requirements (Windows terminals, screen readers)? That answer determines whether we keep the emoji-rich UI, auto-detect capabilities, or provide a “plain” fallback.

**Recommended Next Actions**
1. Either implement the promised `transcript`/`continue` commands or revise the start flow messaging so new users do not hit a broken path.
2. Add path validation and graceful `.state.json` error handling in `status` to prevent silent failure modes.
3. Decide on terminal/accessibility targets and add a low-color or ASCII-only mode if broader support is required.

