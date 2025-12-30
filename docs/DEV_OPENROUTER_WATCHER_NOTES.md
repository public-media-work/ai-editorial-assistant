# DEV_OPENROUTER_WATCHER_NOTES

Context: December 2024 fixes to the v2 watcher/auto-processor while testing OpenRouter presets and model routing.

## What we changed
- Routing: Use `@preset/ai-editorial-assistant` on OpenRouter with `openrouter/auto` as fallback (see `config/llm-config.json`).
- Model selection: Local preferences simplified to `["openrouter"]` so OpenRouter dashboard controls model choice; we removed Gemini-first overrides that caused 400s.
- Cost visibility: `process_queue_auto.py` now logs per-run totals and emits a `worker: completed` event with `total_cost` and `total_tokens`.
- Timestamp fixes: Replaced `datetime.utcnow()` with timezone-aware helper `utc_now_iso()` across scripts to avoid deprecation warnings.

## Observations / lessons
- OpenRouter strictness: Sending a `models` array with unavailable IDs returned 400s. Keeping a single `model` and letting OpenRouter auto/fallback handle it avoids churn.
- Presets first: Pointing the backend at a preset is the cleanest way to enforce organization-wide routing rules without touching code.
- Key loading: Worker loads `.env`; ensure `OPENROUTER_API_KEY` is present. Lack of network or DNS will surface as repeated backend retries.
- Logging: Startup events land in `OUTPUT/system/processing.log.jsonl`; main session detail in `logs/dashboard_session.log`; `process_queue.log` captures worker stdout/stderr.

## Follow-ups for v3.0
- Add per-run cost cap/alert hook (read from env/preset) to avoid expensive auto-upgrades.
- Surface active model/preset in the dashboard UI and manifest for auditing.
- Provide a health endpoint that returns queue size, active model, and last cost totals.
- Consider a hard allowlist of models (or max $/token) in code as a safety guard even when using presets.
