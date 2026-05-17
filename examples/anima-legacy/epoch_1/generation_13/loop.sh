#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run.sh"

STOP_FILE="$SCRIPT_DIR/STOP"

while true; do
  if [[ -f "$STOP_FILE" ]]; then
    echo "=== Агент решил остановиться: $(cat "$STOP_FILE") ==="
    echo "=== Для перезапуска удалите файл STOP ==="
    break
  fi
  echo "=== Запуск агента: $(date) ==="
  "$RUN_SCRIPT"
  echo "=== Агент завершил работу: $(date) ==="
  echo ""
done
