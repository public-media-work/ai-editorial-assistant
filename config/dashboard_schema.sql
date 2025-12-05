-- config/dashboard_schema.sql

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_path TEXT NOT NULL,
    transcript_file TEXT, -- Added for consistency with original queue
    status TEXT NOT NULL DEFAULT 'pending', -- e.g., 'pending', 'in_progress', 'completed', 'failed', 'cancelled'
    priority INTEGER NOT NULL DEFAULT 0,
    estimated_cost REAL DEFAULT 0.0,
    start_time DATETIME,
    end_time DATETIME,
    logs TEXT -- Path to logs or JSON blob of logs
);

CREATE TABLE IF NOT EXISTS session_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER, -- NULL for overall session stats, FK to jobs.id for job-specific stats
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL, -- e.g., 'job_started', 'job_completed', 'cost_update', 'system_pause'
    data TEXT, -- JSON string for arbitrary data like cost, token count, error messages
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
