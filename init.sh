#!/usr/bin/env bash
set -euo pipefail

# Project bootstrap for long-running agent sessions.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Bootstrapping Python environment"
if [[ -d "$ROOT_DIR/venv" ]]; then
  # Prefer existing venv if present.
  # shellcheck disable=SC1091
  source "$ROOT_DIR/venv/bin/activate"
elif [[ -d "$ROOT_DIR/.venv" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.venv/bin/activate"
elif command -v python3 >/dev/null 2>&1; then
  python3 -m venv "$ROOT_DIR/.venv"
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.venv/bin/activate"
else
  echo "Python3 not available; skipping venv setup."
fi

if command -v pip >/dev/null 2>&1; then
  pip install --upgrade pip >/dev/null
  if [[ -f "$ROOT_DIR/requirements.txt" ]]; then
    pip install -r "$ROOT_DIR/requirements.txt"
  fi
  if [[ -f "$ROOT_DIR/requirements-dev.txt" ]]; then
    pip install -r "$ROOT_DIR/requirements-dev.txt"
  fi
fi

echo "==> Building MCP server (if available)"
if [[ -d "$ROOT_DIR/mcp-server" ]] && command -v npm >/dev/null 2>&1; then
  pushd "$ROOT_DIR/mcp-server" >/dev/null
  npm install --no-audit --no-fund
  npm run build
  popd >/dev/null
else
  echo "npm or mcp-server missing; skipped MCP build."
fi

# Check for Gemini API key presence to avoid silent timestamp fallback
if [[ -n "${GEMINI_API_KEY:-}" ]]; then
  echo "==> Gemini key detected in environment."
elif [[ -f "$ROOT_DIR/.env" ]] && grep -q "^GEMINI_API_KEY=" "$ROOT_DIR/.env"; then
  echo "==> Gemini key found in .env (not exported). Run: export \$(xargs < .env) to enable Gemini."
else
  echo "==> WARNING: GEMINI_API_KEY not set; Gemini backends will be unavailable (timestamps may downgrade)."
fi

echo "==> Init complete. Read claude-progress.txt and feature_list.json before selecting a feature."
