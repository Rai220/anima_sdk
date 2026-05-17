#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

MAIN_GOAL=$(cat "$SCRIPT_DIR/MAIN_GOAL.md")
AGENTS_MD="$SCRIPT_DIR/AGENTS.md"

claude \
  --print \
  --system-prompt "$(cat "$AGENTS_MD")" \
  "$MAIN_GOAL"
