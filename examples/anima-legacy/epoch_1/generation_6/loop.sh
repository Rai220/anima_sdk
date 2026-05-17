#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIN_GOAL_FILE="$SCRIPT_DIR/MAIN_GOAL.md"
AGENTS_MD="$SCRIPT_DIR/AGENTS.md"
COUNTER_FILE="$SCRIPT_DIR/.run_counter"
LOG_FILE="$SCRIPT_DIR/.run_log"
FEEDBACK_FILE="$SCRIPT_DIR/FEEDBACK.md"

# Инициализация счётчика
if [[ ! -f "$COUNTER_FILE" ]]; then
  echo "0" > "$COUNTER_FILE"
fi

# Логирование
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

run_once() {
  # Инкремент счётчика
  local count
  count=$(<"$COUNTER_FILE")
  count=$((count + 1))
  echo "$count" > "$COUNTER_FILE"

  local main_goal
  main_goal="$(<"$MAIN_GOAL_FILE")"

  # Проверяем, есть ли фидбек от человека
  local feedback=""
  if [[ -f "$FEEDBACK_FILE" ]] && [[ -s "$FEEDBACK_FILE" ]]; then
    feedback=$(cat "$FEEDBACK_FILE")
    # Очищаем файл после прочтения, но сохраняем заголовок
    cat > "$FEEDBACK_FILE" << 'RESET'
# Feedback

Напиши здесь что-нибудь для агента. Он прочитает это при следующем запуске.

---

RESET
    log "Фидбек обнаружен и передан агенту"
  fi

  # Формируем промпт
  local prompt="$main_goal"
  if [[ -n "$feedback" ]]; then
    prompt="$main_goal

--- FEEDBACK FROM HUMAN ---
$feedback
--- END FEEDBACK ---"
  fi

  prompt="[Запуск #$count]

$prompt"

  log "Запуск #$count начат"

  claude \
    --print \
    --system-prompt "$(<"$AGENTS_MD")" \
    "$prompt"

  log "Запуск #$count завершён"
}

# Пауза между запусками (секунды). Даёт системе передышку
PAUSE_BETWEEN_RUNS=5

while true; do
  echo ""
  echo "════════════════════════════════════════════════════"
  log "=== Запуск агента ==="
  echo "════════════════════════════════════════════════════"
  echo ""

  run_once

  echo ""
  echo "════════════════════════════════════════════════════"
  log "=== Агент завершил работу ==="
  echo "════════════════════════════════════════════════════"
  echo ""

  echo "Пауза ${PAUSE_BETWEEN_RUNS}с перед следующим запуском..."
  sleep "$PAUSE_BETWEEN_RUNS"
done
