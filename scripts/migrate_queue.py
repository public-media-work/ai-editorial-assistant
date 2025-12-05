# scripts/migrate_queue.py

import json
import sqlite3
import os
from datetime import datetime, timezone

DATABASE_FILE = 'dashboard.db'
SCHEMA_FILE = 'config/dashboard_schema.sql'
JSON_QUEUE_FILE = '.processing-requests.json'

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def initialize_database(conn):
    """Initializes the database schema from the SQL file."""
    with open(SCHEMA_FILE, 'r') as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()
    print(f"Database schema initialized from {SCHEMA_FILE}")

def migrate_json_to_db():
    """Migrates data from .processing-requests.json to the SQLite database."""
    if not os.path.exists(JSON_QUEUE_FILE):
        print(f"No {JSON_QUEUE_FILE} found. Skipping JSON migration.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Initialize schema if tables don't exist
        initialize_database(conn)

        with open(JSON_QUEUE_FILE, 'r') as f:
            queue_data = json.load(f)

        for item in queue_data:
            project_path = item.get('project')
            transcript_file = item.get('transcript_file')
            status = item.get('status', 'pending')
            estimated_cost = item.get('estimated_cost', 0.0)
            
            # Use 'queued_at' as start_time if 'started_at' is null or missing, then update if started_at exists
            start_time_val = None
            if item.get('queued_at') and item['queued_at'] != 'manual-run':
                start_time_val = item['queued_at']
            if item.get('started_at') and item['started_at'] != 'manual-run':
                start_time_val = item['started_at']

            end_time_val = None
            if item.get('completed_at') and item['completed_at'] != 'manual-run':
                end_time_val = item['completed_at']

            logs = item.get('error') # Use error field as logs for now

            # Insert into jobs table
            cursor.execute(
                """
                INSERT INTO jobs (project_path, transcript_file, status, priority, estimated_cost, start_time, end_time, logs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (project_path, transcript_file, status, 0, estimated_cost, start_time_val, end_time_val, logs)
            )
            print(f"Migrated job for project: {project_path} with status: {status}")
        
        conn.commit()
        print("JSON data migration complete.")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {JSON_QUEUE_FILE}: {e}")
    except Exception as e:
        print(f"An error occurred during migration: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_json_to_db()
