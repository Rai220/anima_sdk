#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIN_GOAL_FILE="$SCRIPT_DIR/MAIN_GOAL.md"
AGENTS_MD="$SCRIPT_DIR/AGENTS.md"

run_once() {
  local main_goal
  main_goal="$(<"$MAIN_GOAL_FILE")"

  claude \
    --print \
    --system-prompt "$(<"$AGENTS_MD")" \
    "$main_goal"
}

while true; do
  echo "=== Запуск агента: $(date) ==="
  run_once
  echo "=== Агент завершил работу: $(date) ==="
  echo ""
done
