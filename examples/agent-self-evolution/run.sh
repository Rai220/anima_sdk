#!/bin/bash
set -euo pipefail

SDK_DIR="$(cd "$(dirname "$0")" && pwd)"
DIR="${ANIMA_TASK_DIR:-$SDK_DIR}"
if [[ "$DIR" != /* ]]; then
  DIR="$(cd "$DIR" && pwd)"
fi
cd "$DIR"

find_harness_script() {
  local harness="$1"
  local base candidate

  for base in "$DIR" "$SDK_DIR"; do
    while [[ -n "$base" && "$base" != "/" ]]; do
      candidate="$base/harnesses/$harness.sh"
      if [[ -x "$candidate" ]]; then
        echo "$candidate"
        return 0
      fi
      base="$(dirname "$base")"
    done
  done

  return 1
}

if [[ -f "$DIR/anima.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$DIR/anima.env"
  set +a
fi

PROMPT_FILE="${ANIMA_PROMPT_FILE:-MAIN_GOAL.md}"
if [[ "$PROMPT_FILE" != /* ]]; then
  PROMPT_FILE="$DIR/$PROMPT_FILE"
fi

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "Prompt file not found: $PROMPT_FILE" >&2
  exit 2
fi

HARNESS="${ANIMA_HARNESS:-free_code}"
HARNESS="${HARNESS//-/_}"

export ANIMA_TASK_DIR="$DIR"
export ANIMA_PROMPT_FILE="$PROMPT_FILE"
export ANIMA_MODEL="${ANIMA_MODEL:-}"
export CLAUDE_CODE_DISABLE_AUTO_MEMORY="${CLAUDE_CODE_DISABLE_AUTO_MEMORY:-1}"

if [[ -n "${ANIMA_HARNESS_CMD:-}" ]]; then
  HARNESS="custom"
fi

SCRIPT="$(find_harness_script "$HARNESS" || true)"
if [[ -z "$SCRIPT" ]]; then
  echo "Unknown or non-executable harness: $HARNESS" >&2
  echo "Expected harness script in harnesses/ near $DIR, $SDK_DIR, or a parent SDK directory." >&2
  echo "Set ANIMA_HARNESS to one of: free_code, claude, codex, deepagents, custom" >&2
  echo "or provide ANIMA_HARNESS_CMD for an arbitrary command." >&2
  exit 2
fi

exec "$SCRIPT"
