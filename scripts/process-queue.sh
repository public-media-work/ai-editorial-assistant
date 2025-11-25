#!/bin/bash
# Process all items in the .processing-requests.json queue
# This is a helper script for the Claude Code workflow
# Usage: Called by Claude Code agent with Task tool

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
QUEUE_FILE="$PROJECT_ROOT/.processing-requests.json"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Processing Queue ===${NC}"
echo ""

# Check if queue file exists
if [ ! -f "$QUEUE_FILE" ]; then
  echo -e "${YELLOW}No processing queue found${NC}"
  exit 0
fi

# Read queue
queue=$(cat "$QUEUE_FILE")
queue_count=$(echo "$queue" | jq 'length')

if [ "$queue_count" -eq 0 ]; then
  echo -e "${YELLOW}Queue is empty${NC}"
  exit 0
fi

echo -e "${BLUE}Found $queue_count project(s) in queue${NC}"
echo ""

# Extract project names
projects=$(echo "$queue" | jq -r '.[].project')

# Display queue
echo -e "${BLUE}Projects to process:${NC}"
for project in $projects; do
  echo -e "  • $project"
done
echo ""

echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}IMPORTANT: This script prepares the queue for processing${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}To complete processing, run in Claude Code:${NC}"
echo ""
echo -e "${GREEN}For each project above:${NC}"
echo -e "  1. Run transcript-analyst agent"
echo -e "  2. Run formatter agent"
echo -e "  3. Auto-archive will happen automatically"
echo ""
echo -e "${BLUE}Example Claude Code prompt:${NC}"
echo -e '  "Process these projects from the queue:'
for project in $projects; do
  echo -e "   - $project"
done
echo -e '   "'
echo ""
echo -e "${YELLOW}After agents complete, run:${NC}"
echo -e "  ./scripts/finalize-queue.sh"
echo ""
