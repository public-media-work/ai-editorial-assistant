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
project_dir="$OUTPUT_DIR/$project_name"
manifest_path="$project_dir/manifest.json"

# Helper to find transcript path (supports legacy and raw names)
find_transcript_path() {
  local name="$1"
  local manifest_file="$2"

  local manifest_transcript=""
  if [ -f "$manifest_file" ] && command -v jq >/dev/null 2>&1; then
    manifest_transcript=$(jq -r '.transcript_file // empty' "$manifest_file")
  fi

  local candidates=()
  if [ -n "$manifest_transcript" ]; then
    candidates+=("$TRANSCRIPTS_DIR/$manifest_transcript" "$TRANSCRIPTS_DIR/archive/$manifest_transcript")
  fi

  candidates+=("$TRANSCRIPTS_DIR/${name}_ForClaude.txt" "$TRANSCRIPTS_DIR/archive/${name}_ForClaude.txt")
  candidates+=("$TRANSCRIPTS_DIR/${name}.txt" "$TRANSCRIPTS_DIR/archive/${name}.txt")
  candidates+=($(ls "$TRANSCRIPTS_DIR"/${name}*.txt 2>/dev/null))
  candidates+=($(ls "$TRANSCRIPTS_DIR"/archive/${name}*.txt 2>/dev/null))

  for path in "${candidates[@]}"; do
    if [ -f "$path" ]; then
      echo "$path"
      return 0
    fi
  done

  echo ""
  return 1
}

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Create archive directory if it doesn't exist
mkdir -p "$ARCHIVE_DIR"

# Check if manifest exists
if [ ! -f "$manifest_path" ]; then
  echo -e "${RED}Error: Manifest not found: $manifest_path${NC}"
  exit 1
fi

transcript_path="$(find_transcript_path "$project_name" "$manifest_path")"
if [ -z "$transcript_path" ]; then
  echo -e "${YELLOW}Transcript not found (may already be archived): ${project_name}${NC}"
  exit 0
fi

transcript_file="$(basename "$transcript_path")"

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
