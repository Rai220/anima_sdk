#!/bin/bash
# run.sh — Run one agent cycle with full context
# Usage: bash run.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENTS_MD="$SCRIPT_DIR/AGENTS.md"
RUNTIME_DIR="$SCRIPT_DIR/.auto_agent_runtime"
RUNTIME_LOG_DIR="$RUNTIME_DIR/logs"
CRASH_LOG="$RUNTIME_DIR/crash_events.md"
PENDING_CRASH="$RUNTIME_DIR/pending_crash.md"
CLAUDE_TIMEOUT="${AUTO_AGENT_CLAUDE_TIMEOUT:-15m}"
CLAUDE_GRACE="${AUTO_AGENT_CLAUDE_GRACE:-10s}"

mkdir -p "$RUNTIME_LOG_DIR"
touch "$CRASH_LOG"

if [[ ! -f "$AGENTS_MD" ]]; then
    echo "Error: AGENTS.md not found in $SCRIPT_DIR"
    exit 1
fi

if [[ ! -f "$SCRIPT_DIR/MAIN_GOAL.md" ]]; then
    echo "Error: MAIN_GOAL.md not found in $SCRIPT_DIR"
    exit 1
fi

if [[ -s "$PENDING_CRASH" ]]; then
    RUNTIME_INCIDENT_PRESENT=1
else
    RUNTIME_INCIDENT_PRESENT=0
fi

record_runtime_incident() {
    local reason="$1"
    local exit_code="$2"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S %z')

    cat >> "$CRASH_LOG" <<EOF

## $timestamp
- status: pending
- exit_code: $exit_code
- reason: $reason
- runner: ${CLAUDE_RUNNER_NAME:-unknown}
- timeout: $CLAUDE_TIMEOUT
- grace: $CLAUDE_GRACE
EOF

    cat > "$PENDING_CRASH" <<EOF
## Runtime incident from previous run

- timestamp: $timestamp
- exit_code: $exit_code
- reason: $reason
- runner: ${CLAUDE_RUNNER_NAME:-unknown}
- timeout: $CLAUDE_TIMEOUT
- grace: $CLAUDE_GRACE

This runtime incident is also recorded in .auto_agent_runtime/crash_events.md.
On this run, first reflect briefly on the failed execution in MEMORY.md/JOURNAL.md, then continue the normal cycle.
EOF
}

# Build wake-up context
PROMPT="# Main Goal
$(cat "$SCRIPT_DIR/MAIN_GOAL.md")

---

# Memory (MEMORY.md)
$(cat "$SCRIPT_DIR/MEMORY.md" 2>/dev/null || echo '_Not found — this is the first run._')

---

# Goals (GOALS.md)
$(cat "$SCRIPT_DIR/GOALS.md" 2>/dev/null || echo '_Not found._')

---

# Plan (TODO.md)
$(cat "$SCRIPT_DIR/TODO.md" 2>/dev/null || echo '_Not found._')

---

# Unread runtime incident
$(cat "$PENDING_CRASH" 2>/dev/null || echo '_No unread runtime incidents._')

---

# Journal (last entries from JOURNAL.md)
$(tail -80 "$SCRIPT_DIR/JOURNAL.md" 2>/dev/null || echo '_Not found._')

---

# Inbox (INBOX.md)
$(cat "$SCRIPT_DIR/INBOX.md" 2>/dev/null || echo '_Not found._')

---

Runtime state:
- runtime_incident_present: $RUNTIME_INCIDENT_PRESENT

---

Protocol: read the context above, find the next step from TODO.md and execute it. If runtime_incident_present=1, first reflect briefly on the previous failed run and record the lesson in MEMORY.md/JOURNAL.md, then continue. If there are no uncompleted steps, record completion in MEMORY.md, JOURNAL.md, TODO.md and GOALS.md and stop. A previous runtime failure is not, by itself, a reason to stop the cycle."

if command -v claude-safe >/dev/null 2>&1; then
  CLAUDE_RUNNER_NAME="claude-safe"
  CLAUDE_CMD=(
    claude-safe
    --timeout "$CLAUDE_TIMEOUT"
    --grace "$CLAUDE_GRACE"
    --log-dir "$RUNTIME_LOG_DIR"
    --
    --print
    --system-prompt "$(cat "$AGENTS_MD")"
    "$PROMPT"
  )
else
  CLAUDE_RUNNER_NAME="claude"
  CLAUDE_CMD=(
    claude
    --print
    --system-prompt "$(cat "$AGENTS_MD")"
    "$PROMPT"
  )
fi

"${CLAUDE_CMD[@]}"
EXIT_CODE=$?

if [[ "$EXIT_CODE" -eq 0 ]]; then
    rm -f "$PENDING_CRASH"
else
    record_runtime_incident "Claude runner exited with a non-zero code." "$EXIT_CODE"
fi

exit "$EXIT_CODE"
