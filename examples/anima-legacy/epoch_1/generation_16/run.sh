#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIN_GOAL_FILE="$SCRIPT_DIR/MAIN_GOAL.md"
AGENTS_MD="$SCRIPT_DIR/AGENTS.md"
PERMISSION_MODE="${CLAUDE_PERMISSION_MODE:-bypassPermissions}"
CONTINUE_FLAG="${CLAUDE_CONTINUE:-1}"
THINKING_MODE="${CLAUDE_THINKING_MODE:-enabled}"

main_goal="$(<"$MAIN_GOAL_FILE")"

(
  cd "$SCRIPT_DIR"

  if [[ "$CONTINUE_FLAG" == "1" ]]; then
    claude \
      --print \
      --thinking "$THINKING_MODE" \
      --append-system-prompt "$(<"$AGENTS_MD")" \
      --permission-mode "$PERMISSION_MODE" \
      --tools default \
      --continue \
      "$main_goal"
  else
    claude \
      --print \
      --thinking "$THINKING_MODE" \
      --append-system-prompt "$(<"$AGENTS_MD")" \
      --permission-mode "$PERMISSION_MODE" \
      --tools default \
      "$main_goal"
  fi
)
