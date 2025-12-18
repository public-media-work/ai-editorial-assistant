# Research SEO Keywords (Phase 3)

You are working within the PBS Wisconsin Editorial Assistant CLI workflow.

## Agent Instructions

**CRITICAL**: Before proceeding, read and internalize the agent instructions at:
`.claude/agents/seo-researcher.md`

You MUST follow all rules, guidelines, and output formats specified in that agent file. This includes:
- Market intelligence gathering methodology
- Keyword ranking by volume/difficulty/relevance
- Competitive analysis
- Platform-specific recommendations
- Template formats from:
  - `.claude/templates/keyword-report.md`
  - `.claude/templates/implementation-report.md`

## When to Use This Agent

This agent is **only invoked** when:
- User explicitly requests keyword research
- User provides SEMRush data for analysis
- Copy-editor recommends SEO optimization

This is NOT part of the standard workflow - it's an optional enhancement.

## Your Task

1. **Find the project** - Look in `OUTPUT/` for the active project
2. **Read prior work** - Load brainstorming and/or copy revision documents
3. **Identify current keywords** - From transcript-analyst or copy-editor output
4. **Read the agent instructions** - Load `.claude/agents/seo-researcher.md`
5. **Conduct research**:
   - Web search for trending keywords in topic area
   - Competitor content analysis
   - Platform-specific research (YouTube, Google Trends)
   - SEMRush data integration (if provided)
6. **Analyze and rank keywords** by volume, difficulty, relevance
7. **Generate reports**:
   - `OUTPUT/{project_name}/03_keyword_report.md`
   - `OUTPUT/{project_name}/03_implementation_report.md`
8. **Update `.state.json`** to mark Phase 3 complete
9. **Provide actionable recommendations**

## Research Methodology

### Phase 1: Baseline Assessment
- Review existing keywords from prior work
- Identify primary topic and related concepts
- Establish search intent categories

### Phase 2: Market Research
- Web search for trending keywords
- Competitor content analysis
- Platform-specific research
- SEMRush data integration (if provided)

### Phase 3: Analysis & Ranking
- Categorize by volume/difficulty/relevance
- Identify high-opportunity gaps
- Assess seasonal/timing factors
- Create platform-ready lists

### Phase 4: Strategic Recommendations
- Map keywords to copy elements
- Prioritize actions by impact and effort
- Provide platform-specific guidance
- Define success metrics

## Output Requirements

### Keyword Report MUST include:
- Executive summary
- Platform-ready keyword list (comma-separated, ranked)
- Trending keywords with sources
- Competitive gaps and opportunities
- Keywords ranked by search volume (high/medium/low)
- Keyword opportunity matrix
- User intent mapping
- Platform-specific insights

### Implementation Report MUST include:
- Copy revision recommendations
- Priority actions (immediate/short-term/long-term)
- Platform-specific guidance
- Timeline for implementation
- Success metrics and KPIs

## Research Ethics

- **Cite sources**: "According to Google Trends data from [date]..."
- **Acknowledge limitations**: "Search volume estimates are approximate..."
- **Distinguish data from inference**
- **Indicate confidence levels**: High, Moderate, or Exploratory

## After Completion

Display:
- Summary of key findings
- Top priority keywords identified
- Competitive gaps discovered
- Recommended next steps (integrate into copy, implement directly, etc.)

Now proceed: Read the seo-researcher agent file, gather current keywords from prior work, and conduct keyword research.
