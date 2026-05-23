#!/bin/bash
set -euo pipefail

if [[ -z "${ANIMA_HARNESS_CMD:-}" ]]; then
  echo "ANIMA_HARNESS_CMD is required for the custom harness." >&2
  exit 2
fi

bash -lc "$ANIMA_HARNESS_CMD" < "$ANIMA_PROMPT_FILE"
