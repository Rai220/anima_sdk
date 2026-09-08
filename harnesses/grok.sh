#!/bin/bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/lib.sh"

BIN="${ANIMA_GROK_BIN:-grok}"

cmd=("$BIN" --prompt-file "$ANIMA_PROMPT_FILE")

if [[ -n "${ANIMA_TASK_DIR:-}" ]]; then
  cmd+=(--cwd "$ANIMA_TASK_DIR")
fi

if [[ -n "${ANIMA_MODEL:-}" ]]; then
  cmd+=(--model "$ANIMA_MODEL")
fi

# --yolo auto-approves tool executions (alias of --always-approve).
if [[ "${ANIMA_GROK_YOLO:-${ANIMA_SKIP_PERMISSIONS:-1}}" != "0" ]]; then
  cmd+=(--yolo)
fi

anima_split_args ANIMA_GROK_ARGS
if ((${#ANIMA_SPLIT_ARGS[@]})); then
  cmd+=("${ANIMA_SPLIT_ARGS[@]}")
fi

"${cmd[@]}"
