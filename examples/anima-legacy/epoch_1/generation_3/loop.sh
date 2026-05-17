#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIN_GOAL_FILE="$SCRIPT_DIR/MAIN_GOAL.md"
AGENTS_MD="$SCRIPT_DIR/AGENTS.md"
RUN_COUNTER_FILE="$SCRIPT_DIR/.run_counter"
LOG_DIR="$SCRIPT_DIR/logs"

# Создать директорию логов, если её нет
mkdir -p "$LOG_DIR"

# Инициализировать счётчик запусков
if [[ -f "$RUN_COUNTER_FILE" ]]; then
  RUN_NUMBER=$(<"$RUN_COUNTER_FILE")
else
  RUN_NUMBER=0
fi

# Graceful shutdown: ловим SIGINT и SIGTERM
RUNNING=true
trap 'echo ""; echo "=== Anima: Ctrl+C получен. Завершаю после текущего запуска... ==="; RUNNING=false' INT TERM

run_once() {
  local run_num="$1"
  local main_goal
  main_goal="$(<"$MAIN_GOAL_FILE")"

  # Формируем промпт с контекстом о номере запуска
  local prompt="# Запуск #${run_num}
Дата: $(date '+%Y-%m-%d %H:%M:%S')

${main_goal}"

  claude \
    --print \
    --dangerously-skip-permissions \
    --system-prompt "$(<"$AGENTS_MD")" \
    "$prompt"
}

while $RUNNING; do
  RUN_NUMBER=$((RUN_NUMBER + 1))
  echo "$RUN_NUMBER" > "$RUN_COUNTER_FILE"

  LOG_FILE="$LOG_DIR/run_$(printf '%03d' "$RUN_NUMBER")_$(date '+%Y%m%d_%H%M%S').log"

  echo "=== Anima: Запуск #${RUN_NUMBER} — $(date) ==="

  # Запуск с логированием (tee сохраняет и в файл, и на экран)
  if run_once "$RUN_NUMBER" 2>&1 | tee "$LOG_FILE"; then
    echo "=== Anima: Запуск #${RUN_NUMBER} завершён успешно — $(date) ==="
  else
    echo "=== Anima: Запуск #${RUN_NUMBER} завершён с ошибкой (код $?) — $(date) ==="
  fi

  echo ""

  # Пауза между запусками (2 сек — дать системе отдохнуть)
  if $RUNNING; then
    sleep 2
  fi
done

echo "=== Anima: Процесс остановлен. Всего запусков: ${RUN_NUMBER} ==="
