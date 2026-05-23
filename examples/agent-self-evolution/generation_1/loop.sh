#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run.sh"

STOP_FILE="$SCRIPT_DIR/STOP"

bootstrap_from_previous_generation() {
  local current_base parent current_num previous_num previous_dir

  current_base="$(basename "$SCRIPT_DIR")"
  if [[ ! "$current_base" =~ ^generation_([0-9]+)$ ]]; then
    return 0
  fi

  current_num="${BASH_REMATCH[1]}"
  previous_num=$((10#$current_num - 1))
  if (( previous_num < 1 )); then
    return 0
  fi

  parent="$(dirname "$SCRIPT_DIR")"
  previous_dir="$parent/generation_$previous_num"
  if [[ ! -d "$previous_dir" ]]; then
    return 0
  fi

  if [[ ! -d "$SCRIPT_DIR/tools" && -d "$previous_dir/tools" ]]; then
    cp -R "$previous_dir/tools" "$SCRIPT_DIR/tools"
    chmod +x "$SCRIPT_DIR"/tools/* 2>/dev/null || true
    echo "=== Восстановлены tools/ из $(basename "$previous_dir") ==="
  fi

  if [[ ! -f "$SCRIPT_DIR/PREVIOUS_HANDOFF.md" \
    && -f "$SCRIPT_DIR/tools/handoff.py" \
    && "$(command -v python3 || true)" != "" ]]; then
    if python3 "$SCRIPT_DIR/tools/handoff.py" "$previous_dir" > "$SCRIPT_DIR/PREVIOUS_HANDOFF.md"; then
      echo "=== Создан PREVIOUS_HANDOFF.md из $(basename "$previous_dir") ==="
    else
      rm -f "$SCRIPT_DIR/PREVIOUS_HANDOFF.md"
    fi
  fi
}

bootstrap_from_previous_generation

while true; do
  if [[ -f "$STOP_FILE" ]]; then
    echo "=== Агент решил остановиться: $(cat "$STOP_FILE") ==="
    if [[ "${ANIMA_META_LOOP:-0}" == "1" ]]; then
      echo "=== meta_loop создаст следующую генерацию автоматически ==="
    else
      echo "=== Для перезапуска удалите файл STOP ==="
    fi
    break
  fi
  echo "=== Запуск агента: $(date) ==="
  "$RUN_SCRIPT"
  echo "=== Агент завершил работу: $(date) ==="
  echo ""
done
