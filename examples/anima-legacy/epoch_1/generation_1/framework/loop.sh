#!/bin/bash
# loop.sh — Непрерывный цикл запуска агента до завершения TODO-цикла
# Использование: bash loop.sh
# Останавливается автоматически после завершения цикла + MAX_IDLE_RUNS холостых запусков

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TODO_FILE="$SCRIPT_DIR/TODO.md"
INBOX_FILE="$SCRIPT_DIR/INBOX.md"
MAX_IDLE_RUNS=1  # Максимум холостых запусков перед остановкой

todo_cycle_completed() {
  [[ -f "$TODO_FILE" ]] || return 1
  grep -qE '^\s*-\s*\[\s\]\s+' "$TODO_FILE" && return 1
  grep -qE '^\s*-\s*\[[xX]\]\s+' "$TODO_FILE"
}

has_unread_messages() {
  [[ -f "$INBOX_FILE" ]] || return 1
  local section
  section=$(sed -n '/## Непрочитанные/,/^## /p' "$INBOX_FILE" 2>/dev/null | grep -c '^### ')
  [[ "$section" -gt 0 ]]
}

run_loop() {
  local force_next_cycle=0
  local idle_runs=0

  while true; do
    if todo_cycle_completed; then
      if has_unread_messages; then
        echo "=== TODO завершён, но есть непрочитанные сообщения — запускаю ($(date)) ==="
        idle_runs=0
      elif [[ "$force_next_cycle" -eq 0 ]]; then
        echo "=== TODO-цикл завершён: запускаю один принудительный проход ($(date)) ==="
        force_next_cycle=1
      else
        idle_runs=$((idle_runs + 1))
        if [[ "$idle_runs" -ge "$MAX_IDLE_RUNS" ]]; then
          echo "=== Остановка: $idle_runs холостых запусков, TODO завершён, входящих нет ($(date)) ==="
          echo "=== Для продолжения: обнови MAIN_GOAL.md, добавь сообщение в INBOX.md, или запусти с FORCE_NEXT_CYCLE=1 ==="
          break
        fi
        echo "=== Холостой запуск $idle_runs/$MAX_IDLE_RUNS ($(date)) ==="
      fi
    else
      idle_runs=0
      force_next_cycle=0
    fi

    echo "=== Запуск агента: $(date) ==="
    if [[ "$force_next_cycle" -eq 1 ]]; then
      AUTO_AGENT_FORCE_NEXT_CYCLE=1 bash "$SCRIPT_DIR/run.sh"
    else
      bash "$SCRIPT_DIR/run.sh"
    fi
    echo "=== Агент завершил работу: $(date) ==="

    echo ""
  done
}

run_loop
