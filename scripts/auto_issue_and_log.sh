#!/usr/bin/env bash
# Create an issue on the configured repo with a sample log
TITLE="$1"
BODY_FILE="$2"
if [ -z "$TITLE" ] || [ -z "$BODY_FILE" ]; then
  echo "Usage: $0 "title" path/to/logfile"
  exit 1
fi
if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not found"
  exit 1
fi
gh issue create --title "$TITLE" --body-file "$BODY_FILE"
