#!/usr/bin/env python3
"""
Lightweight web monitor for the visual dashboard.

Serves a minimal HTML page and JSON state for queue/session/logs so operators can
view dashboard data in a browser. Intended as a spike; not a full replacement
for the Rich dashboard UI.

Usage:
    python3 scripts/dashboard_web_monitor.py [--port 8000]
"""

import argparse
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
QUEUE_FILE = PROJECT_ROOT / ".processing-requests.json"
SESSION_FILE = PROJECT_ROOT / "OUTPUT" / ".dashboard_session.json"
LOG_FILE = PROJECT_ROOT / "logs" / "dashboard_session.log"


def load_json(path: Path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default


def read_tail(path: Path, limit: int = 200) -> list[str]:
    try:
        lines = path.read_text().splitlines()
        return lines[-limit:]
    except Exception:
        return []


def format_timestamp(ts: str | None) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ts


HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Editorial Assistant Monitor</title>
  <style>
    body { font-family: Arial, sans-serif; background: #0b0d11; color: #e7edf5; margin: 0; padding: 16px; }
    h1 { margin-top: 0; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .card { background: #141821; border: 1px solid #1f2733; border-radius: 8px; padding: 12px; }
    .card h2 { margin: 0 0 8px 0; font-size: 16px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 6px 8px; border-bottom: 1px solid #1f2733; font-size: 14px; }
    th { text-align: left; color: #9fb0c7; }
    .status-processing { color: #4fd1c5; }
    .status-failed { color: #f87171; }
    .status-completed { color: #a3e635; }
    .log { font-family: monospace; font-size: 12px; white-space: pre; }
  </style>
</head>
<body>
  <h1>Editorial Assistant Monitor</h1>
  <div class="grid">
    <div class="card">
      <h2>Queue</h2>
      <table id="queue-table">
        <thead><tr><th>Project</th><th>Status</th><th>Cost</th><th>Started</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
    <div class="card">
      <h2>Session</h2>
      <div id="session-stats"></div>
    </div>
    <div class="card">
      <h2>Recent Errors</h2>
      <div id="errors"></div>
    </div>
    <div class="card">
      <h2>Logs</h2>
      <div class="log" id="logs"></div>
    </div>
  </div>
  <script>
    async function fetchState() {
      const res = await fetch('/api/state');
      if (!res.ok) return;
      const data = await res.json();
      renderQueue(data.queue);
      renderSession(data.session);
      renderErrors(data.errors);
      renderLogs(data.logs);
    }

    function renderQueue(queue) {
      const tbody = document.querySelector('#queue-table tbody');
      tbody.innerHTML = '';
      queue.forEach(item => {
        const tr = document.createElement('tr');
        const statusClass = item.status === 'processing' ? 'status-processing'
                          : item.status === 'failed' ? 'status-failed'
                          : item.status === 'completed' ? 'status-completed' : '';
        tr.innerHTML = `
          <td>${item.project}</td>
          <td class="${statusClass}">${item.status || ''}</td>
          <td>${item.cost !== undefined ? '$' + item.cost.toFixed(2) : ''}</td>
          <td>${item.started_at ? item.started_at.slice(11,19) : ''}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    function renderSession(session) {
      const el = document.querySelector('#session-stats');
      if (!session) { el.textContent = 'No session data'; return; }
      const stats = session.stats || {};
      el.innerHTML = `
        <div>Projects: ${stats.projects_processed || 0} ✓ / ${stats.projects_failed || 0} ✗</div>
        <div>Total cost: $${(stats.total_cost || 0).toFixed(4)}</div>
        <div>Total minutes: ${(stats.total_processing_minutes || 0).toFixed(1)}</div>
        <div>Last updated: ${session.last_updated || ''}</div>
      `;
    }

    function renderErrors(errors) {
      const el = document.querySelector('#errors');
      if (!errors || errors.length === 0) { el.textContent = 'No errors'; return; }
      el.innerHTML = errors.map(e => {
        const time = e.timestamp ? e.timestamp.slice(11,19) : '';
        return `<div><strong>${time}</strong> [${e.backend || 'n/a'}] ${e.project || ''}: ${e.error || ''}</div>`;
      }).join('');
    }

    function renderLogs(logs) {
      const el = document.querySelector('#logs');
      if (!logs || logs.length === 0) { el.textContent = 'No logs'; return; }
      el.textContent = logs.slice(-200).join('\\n');
    }

    fetchState();
    setInterval(fetchState, 5000);
  </script>
</body>
</html>
"""


class MonitorHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, body: str):
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            self._send_html(HTML_TEMPLATE)
            return

        if self.path.startswith("/api/state"):
            queue = load_json(QUEUE_FILE, [])
            session_data = load_json(SESSION_FILE, {})

            errors = session_data.get("errors", [])
            # If errors are nested in stats (older schema), merge them
            stats = session_data.get("stats", {})
            stats_errors = stats.get("errors", [])
            if stats_errors and not errors:
                errors = stats_errors

            payload = {
                "queue": queue,
                "session": session_data,
                "errors": errors[-20:],
                "logs": read_tail(LOG_FILE, limit=200),
            }
            self._send_json(payload)
            return

        self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        # Suppress stdio logging to keep output clean
        return


def main():
    parser = argparse.ArgumentParser(description="Run lightweight web monitor for the dashboard.")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    args = parser.parse_args()

    server = HTTPServer(("0.0.0.0", args.port), MonitorHandler)
    print(f"Serving web monitor on http://localhost:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
