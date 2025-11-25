# Agent Coordination

**Video Editorial Workflow for PBS Wisconsin Content**

**Last Updated**: 2025-11-18

---

## Overview

This project uses a specialized agent workflow to transform video transcripts into discoverable, SEO-optimized metadata for streaming platforms and websites. The workflow follows ethical AI collaboration principles and PBS Wisconsin editorial standards.

### Purpose

Agent coordination enables:
- **Phased workflow**: Research → Edit → Analyze → Format
- **Specialized expertise**: Each agent focuses on specific deliverables
- **Quality assurance**: Clear handoffs and validation points
- **Ethical collaboration**: Human oversight at every phase
- **Composable tasks**: Agents work sequentially or in parallel as needed

---

## Workflow Phases

### Phase 1: Research & Brainstorming
**Agent**: transcript-analyst
**Trigger**: User provides transcript(s)
**Output**: Brainstorming Document or Digital Shorts Report

### Phase 2: Editing
**Agent**: copy-editor
**Trigger**: User provides draft copy for review
**Output**: Copy Revision Document with side-by-side comparisons

### Phase 3: Analysis (Optional)
**Agent**: seo-researcher
**Trigger**: User requests keyword research OR provides SEMRush data
**Output**: Keyword Report + Implementation Report

### Phase 4: Project Conclusion
**Agent**: formatter
**Trigger**: User requests formatted transcript or timestamps (after copy approved)
**Output**: Formatted Transcript and/or Timestamp Report

---

## Agent Registry

### transcript-analyst
- **Phase**: Research & Brainstorming (Phase 1)
- **Color**: Yellow
- **Purpose**: Analyze transcripts and generate initial metadata options
- **Capabilities**:
  - Content type assessment (standard vs. shortform)
  - Keyword extraction (direct + logical/implied)
  - Title/description option generation with pairing validation
  - Program-specific rule enforcement
- **Deliverables**:
  - `OUTPUT/{project}/brainstorming.md`
  - `OUTPUT/{project}/digital_shorts_report.md`
- **Template**: `.claude/templates/brainstorming-document.md` or `digital-shorts-report.md`
- **Agent Definition**: `.claude/agents/transcript-analyst.md`

### copy-editor
- **Phase**: Editing (Phase 2)
- **Color**: Blue
- **Purpose**: Review and refine draft metadata against transcript and standards
- **Capabilities**:
  - Draft analysis vs. transcript verification
  - AP Style compliance checking
  - Prohibited language detection
  - Side-by-side revision with reasoning
  - Feedback integration loops
- **Deliverables**:
  - `OUTPUT/{project}/copy_revision.md`
- **Template**: `.claude/templates/copy-revision-document.md`
- **Agent Definition**: `.claude/agents/copy-editor.md`

### seo-researcher
- **Phase**: Analysis (Phase 3 - Optional)
- **Color**: Green
- **Purpose**: Conduct market intelligence and keyword research for optimization
- **Capabilities**:
  - Trending keyword research
  - Competitive gap analysis
  - Search volume and difficulty ranking
  - Platform-specific recommendations
  - Strategic implementation guidance
- **Deliverables**:
  - `OUTPUT/{project}/keyword_report.md`
  - `OUTPUT/{project}/implementation_report.md`
- **Templates**:
  - `.claude/templates/keyword-report.md`
  - `.claude/templates/implementation-report.md`
- **Agent Definition**: `.claude/agents/seo-researcher.md`

### formatter
- **Phase**: Project Conclusion (Phase 4)
- **Color**: Cyan
- **Purpose**: Generate final formatted deliverables after content approval
- **Capabilities**:
  - AP Style transcript formatting
  - Speaker identification (full names, every instance)
  - Timestamp/chapter generation (15+ min videos)
  - Platform-specific format outputs
- **Deliverables**:
  - `OUTPUT/{project}/formatted_transcript.md`
  - `OUTPUT/{project}/timestamp_report.md` (if applicable)
- **Templates**:
  - `.claude/templates/formatted-transcript.md`
  - `.claude/templates/timestamp-report.md`
- **Agent Definition**: `.claude/agents/formatter.md`

---

## Cooperation Patterns

### Pattern 1: Sequential (Standard Workflow)

**Most common path for full-length content:**

```
User provides transcript
    ↓
[transcript-analyst] → Brainstorming Document
    ↓
User reviews options
    ↓
User provides draft copy for revision
    ↓
[copy-editor] → Copy Revision Document
    ↓
User reviews revisions
    ↓
(Optional) User requests SEO research
    ↓
[seo-researcher] → Keyword Report + Implementation Report
    ↓
[copy-editor] → Updated revision with SEO integration
    ↓
User approves final copy
    ↓
(Optional) User requests formatted deliverables
    ↓
[formatter] → Formatted Transcript + Timestamps
    ↓
User implements across platforms
```

**Agent Handoffs:**
- transcript-analyst → User (for review)
- User → copy-editor (with draft copy + feedback)
- copy-editor → User (for approval)
- User → seo-researcher (if research requested)
- seo-researcher → copy-editor (keyword integration)
- User → formatter (after copy approved)
- formatter → User (final deliverables)

### Pattern 2: Direct to Editing

**When user already has draft copy:**

```
User provides transcript + draft copy
    ↓
[copy-editor] → Copy Revision Document
    ↓
User reviews and provides feedback
    ↓
[copy-editor] → Updated revision (Rev 2)
    ↓
Continue iteration until user satisfaction
```

### Pattern 3: SEO-First Analysis

**When user has SEMRush data or explicit research request:**

```
User provides transcript + SEMRush data
    ↓
[transcript-analyst] → Initial keywords (from transcript)
    ↓
[seo-researcher] → Keyword Report + Implementation Report
    ↓
[copy-editor] → Keyword-optimized copy revisions
    ↓
User reviews and approves
```

### Pattern 4: Shortform/Digital Shorts

**For multiple short clips:**

```
User provides multiple short transcripts
    ↓
[transcript-analyst] → Digital Shorts Brainstorming Report
    (One comprehensive report covering all clips)
    ↓
User reviews platform-specific metadata
    ↓
(Optional) User requests revisions for specific clips
    ↓
[copy-editor] → Targeted revisions per clip
    ↓
User implements across social platforms
```

---

## Agent Contracts

### Input/Output Standards

Each agent follows workspace_ops agent contract conventions:

**Input Contract Structure:**
```typescript
{
  // Required fields
  "task_description": string,
  "agent_role": string,

  // Context (as applicable)
  "prior_work": {
    "agent": string,
    "summary": string,
    "artifacts": string[],
    "decisions": object,
    "open_questions": string[]
  },

  // Constraints
  "requirements": string[],
  "success_criteria": string[]
}
```

**Output Contract Structure:**
```typescript
{
  "completed": boolean,
  "summary": string,

  "artifacts": {
    "files_created": string[],
    "files_modified": string[]
  },

  "next_steps": string[],
  "validation": object
}
```

See individual agent definitions in `.claude/agents/` for detailed contracts.

---

## Quality Assurance Gates

### Phase 1: Brainstorming
✅ Character counts exact
✅ Title/description pairs cohesive
✅ Keywords based on transcript only
✅ No prohibited language
✅ Program rules applied
✅ Ethical AI disclaimer included

### Phase 2: Editing
✅ All revisions have clear reasoning
✅ Original vs. proposed shown side-by-side
✅ AP Style compliance
✅ Transcript accuracy verified
✅ Feedback questions included

### Phase 3: Analysis (if invoked)
✅ Data sources cited with dates
✅ Search volumes provided
✅ Competitive analysis complete
✅ Implementation timeline realistic
✅ Success metrics measurable

### Phase 4: Formatting (if invoked)
✅ Speaker names full and consistent
✅ AP Style throughout
✅ Timestamps logical (if applicable)
✅ Both platform formats provided
✅ Implementation instructions clear

---

## Invocation Examples

### Example 1: Standard Full-Length Content

```typescript
// Phase 1: Initial Analysis
Task({
  subagent_type: "transcript-analyst",
  prompt: `Analyze this University Place lecture transcript.

  Transcript: transcripts/9UNP2005HD_ForClaude.txt
  Program: University Place
  Content type: standard (56-minute lecture)

  Speaker: Dr. Sarah Johnson discussing Wisconsin labor history

  Generate brainstorming document with title options, descriptions,
  and keywords based on transcript content only.`
})

// Phase 2: User provides draft, requests revision
Task({
  subagent_type: "copy-editor",
  prompt: `Review this draft metadata against the transcript.

  Draft title: "Dr. Johnson Talks About Labor Unions"
  Draft short desc: "An expert discusses Wisconsin workers"
  Draft long desc: "Watch as Dr. Sarah Johnson explains..."

  Transcript: transcripts/9UNP2005HD_ForClaude.txt
  Program: University Place

  Issues I'm concerned about:
  - Title uses honorific and vague verb
  - Description has prohibited language ("watch as")
  - Not sure if it captures the content accurately

  Please provide side-by-side revisions with reasoning.`,

  prior_work: {
    agent: "transcript-analyst",
    summary: "Generated initial brainstorming with 20 keywords",
    artifacts: ["OUTPUT/labor_lecture/brainstorming.md"]
  }
})

// Phase 3: Optional SEO research
Task({
  subagent_type: "seo-researcher",
  prompt: `Research keywords for Wisconsin labor history content.

  Current keywords from transcript-analyst:
  [list of 20 keywords]

  Research goals:
  - Find trending Wisconsin history keywords
  - Identify competitive gaps
  - Optimize for YouTube and PBS.org

  Geographic focus: Wisconsin + regional Midwest`,

  prior_work: {
    agent: "copy-editor",
    summary: "Revised draft copy with AP Style compliance",
    artifacts: ["OUTPUT/labor_lecture/copy_revision.md"]
  }
})

// Phase 4: Final deliverables
Task({
  subagent_type: "formatter",
  prompt: `Generate formatted transcript and timestamps.

  Source: transcripts/9UNP2005HD_ForClaude.txt
  Subject: "Dr. Sarah Johnson - Wisconsin Labor History"
  Duration: 56:32

  Speakers:
  - Host: Michael Stevens
  - Guest: Dr. Sarah Johnson

  Deliverables: Both transcript and timestamp report
  Chapter style: Topical (educational lecture format)`,

  prior_work: {
    agent: "copy-editor",
    summary: "Final metadata approved by user",
    artifacts: ["OUTPUT/labor_lecture/copy_revision.md"],
    decisions: [{
      decision: "User approved final titles and descriptions",
      rationale: "Ready for implementation"
    }]
  }
})
```

### Example 2: Direct to Editing

```typescript
Task({
  subagent_type: "copy-editor",
  prompt: `Review this Here and Now interview metadata.

  Draft copy:
  - Title: "Speaker Vos Talks About Prison Reform"
  - Short: "Legislative leader discusses corrections"
  - Long: "Watch as Assembly Speaker Robin Vos..."

  Transcript: transcripts/here_and_now_vos_corrections.txt
  Program: Here and Now

  Please check against Here and Now format requirements and
  provide side-by-side revisions.`
})
```

### Example 3: Digital Shorts Batch

```typescript
Task({
  subagent_type: "transcript-analyst",
  prompt: `Analyze these 5 short clips from Wisconsin Life episode.

  Transcripts:
  - 2WLI_clip1_bear_researcher.txt
  - 2WLI_clip2_cave_crawling.txt
  - 2WLI_clip3_hmong_dance.txt
  - 2WLI_clip4_pigeon_racing.txt
  - 2WLI_clip5_typewriter_poet.txt

  Content type: shortform/digital shorts
  Target platforms: Instagram, Facebook, YouTube Shorts

  Generate Digital Shorts Brainstorming Report with metadata
  for each clip optimized for social media discovery.`
})
```

---

## Output Organization

### Directory Structure

```
editorial-assistant/
├── .claude/
│   ├── agents/
│   │   ├── transcript-analyst.md
│   │   ├── copy-editor.md
│   │   ├── seo-researcher.md
│   │   └── formatter.md
│   └── templates/
│       ├── brainstorming-document.md
│       ├── digital-shorts-report.md
│       ├── copy-revision-document.md
│       ├── keyword-report.md
│       ├── implementation-report.md
│       ├── formatted-transcript.md
│       └── timestamp-report.md
├── OUTPUT/
│   └── {project_name}/
│       ├── brainstorming.md (or digital_shorts_report.md)
│       ├── copy_revision.md
│       ├── keyword_report.md (if Phase 3)
│       ├── implementation_report.md (if Phase 3)
│       ├── formatted_transcript.md (if Phase 4)
│       └── timestamp_report.md (if Phase 4)
├── transcripts/
│   ├── {program_files}.txt
│   └── archive/
└── AGENT_COORDINATION.md (this file)
```

### File Naming Convention

```
OUTPUT/{project_identifier}/{deliverable_type}.md
```

**Examples:**
- `OUTPUT/9UNP2005_labor_history/brainstorming.md`
- `OUTPUT/here_and_now_vos/copy_revision.md`
- `OUTPUT/wisconsin_life_shorts_batch1/digital_shorts_report.md`
- `OUTPUT/bucky_documentary/keyword_report.md`

---

## Ethical AI Collaboration

**All agents include this disclaimer in deliverables:**

> **Note**: This is AI-generated brainstorming content. Ethical use of generative AI involves collaboration and coaching between the AI and human user. My duty is to provide advice rooted in best practices and the content itself. Your duty is to use this content to advise your own writing and editing, not to publish AI-generated content without review and revision.

**Human oversight required at:**
- ✅ Phase 1 completion (review brainstorming options)
- ✅ Phase 2 completion (approve copy revisions)
- ✅ Phase 3 completion (decide on SEO implementations)
- ✅ Phase 4 completion (verify formatted deliverables)
- ✅ Final publication (human implements and publishes)

---

## Getting Started

1. **Place transcript(s)** in `transcripts/` directory
2. **Invoke transcript-analyst** with transcript path and program context
3. **Review brainstorming output** in `OUTPUT/{project}/`
4. **Continue workflow** based on needs:
   - Have draft copy? → Invoke copy-editor
   - Need SEO research? → Invoke seo-researcher
   - Copy approved? → Invoke formatter for final deliverables

---

## Best Practices

### From workspace_ops/knowledge/agentic_dev_best_practices.md

**Anthropic Claude Code Best Practices:**
- Treat agent definitions as living prompts—refine based on usage
- Use structured workflows (research → edit → analyze → format)
- Test-first approach: validate deliverables match templates
- Clear course-correction: Use feedback loops in copy-editor phase

**Agentic AI Prompting (Ran Isenberg):**
- Six-step prompt pattern: persona → problem → context → plan → tailor → share
- Plan-first behavior before execution
- Keep humans in the loop at quality gates
- Chain prompts for complex workflows (our phase system)

**Reddit AI Agent Lessons:**
- Single-responsibility agents (each phase has one purpose)
- Transparent planning traces (all agents document reasoning)
- Narrow agent scopes (no "do everything" agents)
- Structured outputs (JSON-like agent contracts)

---

## Maintenance

**Monthly Review:**
- Audit OUTPUT/ directory for completed projects
- Archive processed transcripts to `transcripts/archive/`
- Update agent definitions based on user feedback
- Refresh program-specific rules as editorial standards evolve

**Template Updates:**
- When PBS Wisconsin updates style guidelines
- When new platforms added (e.g., new social media)
- When character limits change
- When new deliverable types requested

**Agent Registration:**
- Register new agents in workspace_ops/conventions/AGENT_REGISTRY.md
- Follow workspace-wide agent cooperation conventions
- Maintain agent contract documentation

---

**Last Updated**: 2025-11-18
**Version**: 1.0
**Maintainer**: Editorial Assistant Project
**Related Docs**:
- workspace_ops/conventions/AGENT_COOPERATION.md
- workspace_ops/conventions/AGENT_REGISTRY.md
- AGENT INSTRUCTIONS — Haiku 4.5 version.md
