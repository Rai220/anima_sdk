#!/bin/bash
# loop.sh — Continuous agent loop until TODO cycle completes
# Usage: bash loop.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TODO_FILE="$SCRIPT_DIR/TODO.md"
INBOX_FILE="$SCRIPT_DIR/INBOX.md"
MAX_IDLE_RUNS=1

# Built-in runtime defaults for Claude and recovery behavior.
# They can still be overridden via environment variables when needed.
export AUTO_AGENT_CLAUDE_TIMEOUT="${AUTO_AGENT_CLAUDE_TIMEOUT:-15m}"
export AUTO_AGENT_CLAUDE_GRACE="${AUTO_AGENT_CLAUDE_GRACE:-10s}"
export AUTO_AGENT_FAILURE_BACKOFF_SECONDS="${AUTO_AGENT_FAILURE_BACKOFF_SECONDS:-5}"
FAILURE_BACKOFF_SECONDS="$AUTO_AGENT_FAILURE_BACKOFF_SECONDS"

todo_cycle_completed() {
  [[ -f "$TODO_FILE" ]] || return 1
  grep -qE '^\s*-\s*\[\s\]\s+' "$TODO_FILE" && return 1
  grep -qE '^\s*-\s*\[[xX]\]\s+' "$TODO_FILE"
}

has_unread_messages() {
  [[ -f "$INBOX_FILE" ]] || return 1
  local section
  section=$(sed -n '/## Unread/,/^## /p' "$INBOX_FILE" 2>/dev/null | grep -c '^### ')
  [[ "$section" -gt 0 ]]
}

run_loop() {
  local force_next_cycle=0
  local idle_runs=0
  local consecutive_failures=0

  while true; do
    if todo_cycle_completed; then
      if has_unread_messages; then
        echo "=== TODO done, but inbox has messages — running ($(date)) ==="
        idle_runs=0
      elif [[ "$force_next_cycle" -eq 0 ]]; then
        echo "=== TODO cycle complete: one forced pass ($(date)) ==="
        force_next_cycle=1
      else
        idle_runs=$((idle_runs + 1))
        if [[ "$idle_runs" -ge "$MAX_IDLE_RUNS" ]]; then
          echo "=== Stopping: $idle_runs idle runs, TODO done, no inbox ($(date)) ==="
          echo "=== To continue: update MAIN_GOAL.md, add message to INBOX.md, or run with FORCE_NEXT_CYCLE=1 ==="
          break
        fi
        echo "=== Idle run $idle_runs/$MAX_IDLE_RUNS ($(date)) ==="
      fi
    else
      idle_runs=0
      force_next_cycle=0
    fi

    echo "=== Agent starting: $(date) ==="
    echo "=== Runtime config: timeout=$AUTO_AGENT_CLAUDE_TIMEOUT, grace=$AUTO_AGENT_CLAUDE_GRACE, backoff=${FAILURE_BACKOFF_SECONDS}s ==="
    if [[ "$force_next_cycle" -eq 1 ]]; then
      AUTO_AGENT_FORCE_NEXT_CYCLE=1 bash "$SCRIPT_DIR/run.sh"
      run_exit=$?
    else
      bash "$SCRIPT_DIR/run.sh"
      run_exit=$?
    fi

    if [[ "$run_exit" -ne 0 ]]; then
      consecutive_failures=$((consecutive_failures + 1))
      idle_runs=0
      echo "=== Agent exited abnormally with code $run_exit: $(date) ==="
      echo "=== Runtime incident recorded. Continuing loop after ${FAILURE_BACKOFF_SECONDS}s (consecutive failures: $consecutive_failures) ==="
      echo ""
      sleep "$FAILURE_BACKOFF_SECONDS"
      continue
    fi

    consecutive_failures=0
    echo "=== Agent finished: $(date) ==="
    echo ""
  done
}

run_loop
