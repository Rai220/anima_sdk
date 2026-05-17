#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIN_GOAL_FILE="$SCRIPT_DIR/MAIN_GOAL.md"
AGENTS_MD="$SCRIPT_DIR/AGENTS.md"
PERMISSION_MODE="${CLAUDE_PERMISSION_MODE:-bypassPermissions}"
CONTINUE_FLAG="${CLAUDE_CONTINUE:-1}"
MAX_RUNS="${CLAUDE_MAX_RUNS:-10}"

run_count=0

run_once() {
  local main_goal
  main_goal="$(<"$MAIN_GOAL_FILE")"

  (
    cd "$SCRIPT_DIR"

    if [[ "$CONTINUE_FLAG" == "1" ]]; then
      claude \
        --print \
        --append-system-prompt "$(<"$AGENTS_MD")" \
        --permission-mode "$PERMISSION_MODE" \
        --tools default \
        --continue \
        "$main_goal"
    else
      claude \
        --print \
        --append-system-prompt "$(<"$AGENTS_MD")" \
        --permission-mode "$PERMISSION_MODE" \
        --tools default \
        "$main_goal"
    fi
  )
}

echo "🔄 Цикл агента (макс $MAX_RUNS запусков)"
echo ""

while true; do
  run_count=$((run_count + 1))

  if [[ $run_count -gt $MAX_RUNS ]]; then
    echo "⏹ Достигнут лимит ($MAX_RUNS запусков). Остановка."
    break
  fi

  echo "=== Запуск $run_count/$MAX_RUNS: $(date) ==="
  run_once
  echo "=== Завершён $run_count/$MAX_RUNS: $(date) ==="
  echo ""

  # Drift check between runs (if run_tracker available)
  if [[ -f "$SCRIPT_DIR/tools/run_tracker.py" ]]; then
    drift_output=$(python3 "$SCRIPT_DIR/tools/run_tracker.py" drift 2>&1 || true)
    if echo "$drift_output" | grep -q "ДРЕЙФ"; then
      echo "⚠️  Drift detected between runs. Continuing (agent should handle)."
    fi
  fi
done

echo "✓ Цикл завершён: $run_count запусков выполнено."
