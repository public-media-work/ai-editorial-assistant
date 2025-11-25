#!/bin/bash
# Launcher script to open the Visual Dashboard in a new Terminal window

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT_ROOT' && ./venv/bin/python3 scripts/process_queue_visual.py\""
