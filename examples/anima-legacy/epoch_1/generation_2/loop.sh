#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

while true; do
  echo "=== Запуск агента: $(date) ==="
  bash "$SCRIPT_DIR/run.sh"
  echo "=== Агент завершил работу: $(date) ==="
  echo ""
done
