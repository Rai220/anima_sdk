#!/bin/bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/lib.sh"

BIN="${ANIMA_CODEX_BIN:-codex}"

cmd=("$BIN" exec)

if [[ "${ANIMA_CODEX_SKIP_GIT_REPO_CHECK:-1}" != "0" ]]; then
  cmd+=(--skip-git-repo-check)
fi

if [[ "${ANIMA_CODEX_FULL_AUTO:-1}" != "0" ]]; then
  cmd+=(--full-auto)
fi

if [[ -n "${ANIMA_MODEL:-}" ]]; then
  cmd+=(--model "$ANIMA_MODEL")
fi

anima_split_args ANIMA_CODEX_ARGS
if ((${#ANIMA_SPLIT_ARGS[@]})); then
  cmd+=("${ANIMA_SPLIT_ARGS[@]}")
fi

prompt="$(cat "$ANIMA_PROMPT_FILE")"
cmd+=("$prompt")

"${cmd[@]}"
