#!/bin/bash

anima_split_args() {
  local var_name="$1"
  local value="${!var_name:-}"
  if [[ -n "$value" ]]; then
    # Intentional shell-style splitting for simple extra arguments.
    # Use ANIMA_HARNESS_CMD when arguments require complex quoting.
    # shellcheck disable=SC2206
    ANIMA_SPLIT_ARGS=($value)
  else
    ANIMA_SPLIT_ARGS=()
  fi
}

anima_render_stream_json() {
  local trim="${ANIMA_TOOL_INPUT_TRIM:-80}"

  if ! command -v jq >/dev/null 2>&1; then
    cat
    return 0
  fi

  local line top_type evt block_type delta_type tool_name content
  local tool_input_buf=""
  local tool_input_printed=0

  while IFS= read -r line; do
    top_type=$(printf '%s' "$line" | jq -r '.type // empty' 2>/dev/null) || continue
    case "$top_type" in
      stream_event)
        evt=$(printf '%s' "$line" | jq -r '.event.type // empty' 2>/dev/null)
        case "$evt" in
          content_block_start)
            block_type=$(printf '%s' "$line" | jq -r '.event.content_block.type // empty' 2>/dev/null)
            case "$block_type" in
              tool_use)
                tool_name=$(printf '%s' "$line" | jq -r '.event.content_block.name // "tool"' 2>/dev/null)
                tool_input_buf=""
                tool_input_printed=0
                printf '\n\033[36m>>> TOOL: %s\033[0m ' "$tool_name"
                ;;
              thinking)
                printf '\033[2m'
                ;;
            esac
            ;;
          content_block_delta)
            delta_type=$(printf '%s' "$line" | jq -r '.event.delta.type // empty' 2>/dev/null)
            case "$delta_type" in
              text_delta)
                printf '%s' "$(printf '%s' "$line" | jq -r '.event.delta.text // empty' 2>/dev/null)"
                ;;
              thinking_delta)
                printf '%s' "$(printf '%s' "$line" | jq -r '.event.delta.thinking // empty' 2>/dev/null)"
                ;;
              input_json_delta)
                if [[ "$tool_input_printed" -eq 0 ]]; then
                  chunk=$(printf '%s' "$line" | jq -r '.event.delta.partial_json // empty' 2>/dev/null)
                  tool_input_buf="${tool_input_buf}${chunk}"
                  if [[ ${#tool_input_buf} -ge $trim ]]; then
                    printf '%s...' "$(printf '%s' "$tool_input_buf" | head -c "$trim")"
                    tool_input_printed=1
                  fi
                fi
                ;;
            esac
            ;;
          content_block_stop)
            if [[ -n "${tool_input_buf:-}" && "${tool_input_printed:-0}" -eq 0 ]]; then
              printf '%s' "$tool_input_buf"
            fi
            tool_input_buf=""
            tool_input_printed=0
            printf '\033[0m\n'
            ;;
        esac
        ;;
      tool_result)
        content=$(printf '%s' "$line" | jq -r '.content // empty' 2>/dev/null | head -c 500)
        printf '\033[33m<<< RESULT: %s\033[0m\n\n' "$content"
        ;;
      result)
        printf '\n'
        ;;
      *)
        printf '%s\n' "$line"
        ;;
    esac
  done
}
