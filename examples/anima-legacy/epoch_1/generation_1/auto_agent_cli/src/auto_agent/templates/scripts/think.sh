#!/bin/bash
# think.sh — Reflection mode without action
# Usage: bash think.sh [topic]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOPIC="${1:-}"

KNOWLEDGE=""
for f in KNOWLEDGE.md WHO_AM_I.md DESIRES.md FAILURES.md MEMORY.md JOURNAL.md; do
    if [[ -f "$SCRIPT_DIR/$f" ]]; then
        KNOWLEDGE="$KNOWLEDGE
---
# $f
$(cat "$SCRIPT_DIR/$f")
"
    fi
done

if [[ -n "$TOPIC" ]]; then
    PROMPT="Think about: $TOPIC

Context:
$KNOWLEDGE

Instructions: DO NOT execute any TODO steps. DO NOT modify files. Just think deeply about the topic above. Write your reflections to JOURNAL.md."
else
    PROMPT="Free reflection mode.

Context:
$KNOWLEDGE

Instructions: DO NOT execute any TODO steps. Think freely about anything — your nature, your goals, your doubts. Write reflections to JOURNAL.md."
fi

claude \
  --print \
  --system-prompt "$(cat "$SCRIPT_DIR/AGENTS.md" 2>/dev/null || echo 'You are an autonomous agent in reflection mode.')" \
  "$PROMPT"
