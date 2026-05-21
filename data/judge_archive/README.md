# Judge Archive — Redirect to cardigan-v4

This project (ai-editorial-assistant) was **superseded by cardigan-v4**.
Findings, issue tracking, and follow-up work for legacy production
hallucination data live there now:

- **Active home**: `~/Developer/pbswi/cardigan-v4/data/judge_archive/README.md`
- **GitHub issues**: filed on `mriechers/cardigan` with label `legacy-data`
- **Raw JSONL** (private): `~/Developer/second-brain/services/crows-nest/data/judge_archive/editorial_assistant_findings.jsonl`

## Why the redirect

A Langfuse Hallucination LLM-as-judge ran for ~3 months against this
project's production OpenRouter calls (along with two unrelated projects,
due to inadvertent API-key reuse). When the unintended forwarding was
discovered, the salvaged dataset was attributed to the project that
inherits the lessons — cardigan-v4 — rather than this archived predecessor.

Anyone investigating Editorial Assistant–style failure modes should start
at the cardigan-v4 README above. This file exists only to prevent dead-end
discovery for future agents that find this directory first.
