#!/bin/bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/lib.sh"

BIN="${ANIMA_FREE_CODE_BIN:-free-code}"

cmd=(
  "$BIN"
  --debug
  --print
  --verbose
  --output-format stream-json
  --include-partial-messages
  --think-tool
)

if [[ -n "${ANIMA_MODEL:-}" ]]; then
  cmd+=(--model "$ANIMA_MODEL")
fi

if [[ "${ANIMA_SKIP_PERMISSIONS:-1}" != "0" ]]; then
  cmd+=(--dangerously-skip-permissions)
fi

anima_split_args ANIMA_FREE_CODE_ARGS
if ((${#ANIMA_SPLIT_ARGS[@]})); then
  cmd+=("${ANIMA_SPLIT_ARGS[@]}")
fi

"${cmd[@]}" < "$ANIMA_PROMPT_FILE" | anima_render_stream_json
