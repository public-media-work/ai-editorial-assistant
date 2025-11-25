#!/bin/bash
# Automatically archive a single transcript after processing completes
# Usage: ./scripts/auto-archive-transcript.sh <project_name>

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <project_name>"
  exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TRANSCRIPTS_DIR="$PROJECT_ROOT/transcripts"
OUTPUT_DIR="$PROJECT_ROOT/OUTPUT"
ARCHIVE_DIR="$TRANSCRIPTS_DIR/archive"

project_name="$1"
transcript_file="${project_name}_ForClaude.txt"
transcript_path="$TRANSCRIPTS_DIR/$transcript_file"
project_dir="$OUTPUT_DIR/$project_name"
manifest_path="$project_dir/manifest.json"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Create archive directory if it doesn't exist
mkdir -p "$ARCHIVE_DIR"

# Check if transcript exists
if [ ! -f "$transcript_path" ]; then
  echo -e "${YELLOW}Transcript not found (may already be archived): $transcript_file${NC}"
  exit 0
fi

# Check if manifest exists
if [ ! -f "$manifest_path" ]; then
  echo -e "${RED}Error: Manifest not found: $manifest_path${NC}"
  exit 1
fi

# Check if processing is complete
has_brainstorming=$(grep '"brainstorming"' "$manifest_path" | grep -v 'null' || echo "")
has_formatted=$(grep '"formatted_transcript"' "$manifest_path" | grep -v 'null' || echo "")

if [[ -z "$has_brainstorming" ]] || [[ -z "$has_formatted" ]]; then
  echo -e "${YELLOW}Processing not complete, skipping archive${NC}"
  echo -e "  Brainstorming: $([ -n "$has_brainstorming" ] && echo "✓" || echo "✗")"
  echo -e "  Formatted transcript: $([ -n "$has_formatted" ] && echo "✓" || echo "✗")"
  exit 0
fi

# Check if file already exists in archive
archive_destination="$ARCHIVE_DIR/$transcript_file"

if [ -f "$archive_destination" ]; then
  # File exists, create versioned backup
  version=1
  while [ -f "$ARCHIVE_DIR/${transcript_file%.txt}_v${version}.txt" ]; do
    version=$((version + 1))
  done

  # Move existing to versioned name
  versioned_name="${transcript_file%.txt}_v${version}.txt"
  mv "$archive_destination" "$ARCHIVE_DIR/$versioned_name"
  echo -e "${YELLOW}⚠ Duplicate detected - existing archived as: $versioned_name${NC}"
fi

# Archive the transcript
mv "$transcript_path" "$ARCHIVE_DIR/"

echo -e "${GREEN}✓ Archived: $transcript_file → archive/${NC}"
echo -e "${BLUE}  Output remains in: OUTPUT/$project_name/${NC}"

# Update manifest with archive info
if command -v jq &> /dev/null; then
  tmp_manifest=$(mktemp)
  jq ". += {\"transcript_archived\": true, \"archived_at\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}" "$manifest_path" > "$tmp_manifest"
  mv "$tmp_manifest" "$manifest_path"
fi

exit 0
