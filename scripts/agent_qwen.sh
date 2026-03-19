#!/usr/bin/env bash
# agent_qwen.sh - simple CLI wrapper for local qwen2.5:7b via ollama
# Usage: ./scripts/agent_qwen.sh "<prompt>" [--system "..."]
PROMPT="$1"
SYS=""
if [ "$2" = "--system" ]; then
  SYS="$3"
fi
if [ -z "$PROMPT" ]; then
  echo "Usage: $0 \"<prompt>\" [--system \"system prompt\"]"
  exit 1
fi
CMD=(ollama run qwen2.5:7b)
if [ -n "$SYS" ]; then
  CMD+=("--system" "$SYS")
fi
CMD+=("$PROMPT")
# Run and capture
"${CMD[@]}"
