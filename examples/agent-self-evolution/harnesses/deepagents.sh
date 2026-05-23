#!/bin/bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/lib.sh"

BIN="${ANIMA_DEEPAGENTS_BIN:-deepagents}"

prompt="$(cat "$ANIMA_PROMPT_FILE")"

cmd=("$BIN" --non-interactive "$prompt")

if [[ -n "${ANIMA_MODEL:-}" ]]; then
  cmd+=(--model "$ANIMA_MODEL")
fi

if [[ -n "${ANIMA_DEEPAGENTS_AGENT:-}" ]]; then
  cmd+=(--agent "$ANIMA_DEEPAGENTS_AGENT")
fi

if [[ "${ANIMA_DEEPAGENTS_AUTO_APPROVE:-${ANIMA_SKIP_PERMISSIONS:-1}}" != "0" ]]; then
  cmd+=(--auto-approve)
fi

shell_allow="${ANIMA_DEEPAGENTS_SHELL_ALLOW-all}"
if [[ -n "$shell_allow" ]]; then
  cmd+=(--shell-allow-list "$shell_allow")
fi

if [[ -n "${ANIMA_DEEPAGENTS_MAX_TURNS:-}" ]]; then
  cmd+=(--max-turns "$ANIMA_DEEPAGENTS_MAX_TURNS")
fi

if [[ "${ANIMA_DEEPAGENTS_QUIET:-0}" != "0" ]]; then
  cmd+=(--quiet)
fi

anima_split_args ANIMA_DEEPAGENTS_ARGS
if ((${#ANIMA_SPLIT_ARGS[@]})); then
  cmd+=("${ANIMA_SPLIT_ARGS[@]}")
fi

"${cmd[@]}"
