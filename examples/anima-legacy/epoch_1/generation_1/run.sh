#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

AGENTS_MD="$SCRIPT_DIR/AGENTS.md"
RUNTIME_DIR="$SCRIPT_DIR/.auto_agent_runtime"
RUNTIME_LOG_DIR="$RUNTIME_DIR/logs"
CRASH_LOG="$RUNTIME_DIR/crash_events.md"
PENDING_CRASH="$RUNTIME_DIR/pending_crash.md"
CLAUDE_TIMEOUT="${AUTO_AGENT_CLAUDE_TIMEOUT:-5m}"
CLAUDE_GRACE="${AUTO_AGENT_CLAUDE_GRACE:-10s}"

mkdir -p "$RUNTIME_LOG_DIR"
touch "$CRASH_LOG"

TODO_OPEN_COUNT=$(grep -cE '^\s*-\s*\[\s\]\s+' "$SCRIPT_DIR/TODO.md" 2>/dev/null)
TODO_DONE_COUNT=$(grep -cE '^\s*-\s*\[[xX]\]\s+' "$SCRIPT_DIR/TODO.md" 2>/dev/null)
UNREAD_MESSAGE_COUNT=$(sed -n '/## Непрочитанные/,/^## /p' "$SCRIPT_DIR/INBOX.md" 2>/dev/null | grep -c '^### ')

TODO_OPEN_COUNT=${TODO_OPEN_COUNT:-0}
TODO_DONE_COUNT=${TODO_DONE_COUNT:-0}
UNREAD_MESSAGE_COUNT=${UNREAD_MESSAGE_COUNT:-0}

REPLAN_REQUESTED=0
if [[ "${AUTO_AGENT_REPLAN:-0}" == "1" || "${AUTO_AGENT_FORCE_NEXT_CYCLE:-0}" == "1" || "${FORCE_NEXT_CYCLE:-0}" == "1" ]]; then
  REPLAN_REQUESTED=1
fi

if [[ "$TODO_OPEN_COUNT" -gt 0 ]]; then
  TODO_CYCLE_STATUS="active"
elif [[ "$TODO_DONE_COUNT" -gt 0 ]]; then
  TODO_CYCLE_STATUS="completed"
else
  TODO_CYCLE_STATUS="empty"
fi

if [[ -s "$PENDING_CRASH" ]]; then
  RUNTIME_INCIDENT_PRESENT=1
else
  RUNTIME_INCIDENT_PRESENT=0
fi

record_runtime_incident() {
  local reason="$1"
  local exit_code="$2"
  local timestamp
  timestamp=$(date '+%Y-%m-%d %H:%M:%S %z')

  cat >> "$CRASH_LOG" <<EOF

## $timestamp
- status: pending
- exit_code: $exit_code
- reason: $reason
- todo_cycle_status: $TODO_CYCLE_STATUS
- todo_open_tasks: $TODO_OPEN_COUNT
- todo_done_tasks: $TODO_DONE_COUNT
- unread_messages: $UNREAD_MESSAGE_COUNT
- runner: ${CLAUDE_RUNNER_NAME:-unknown}
- timeout: $CLAUDE_TIMEOUT
- grace: $CLAUDE_GRACE
EOF

  cat > "$PENDING_CRASH" <<EOF
## Незавершённый предыдущий запуск

- timestamp: $timestamp
- exit_code: $exit_code
- reason: $reason
- todo_cycle_status: $TODO_CYCLE_STATUS
- todo_open_tasks: $TODO_OPEN_COUNT
- todo_done_tasks: $TODO_DONE_COUNT
- unread_messages: $UNREAD_MESSAGE_COUNT
- runner: ${CLAUDE_RUNNER_NAME:-unknown}
- timeout: $CLAUDE_TIMEOUT
- grace: $CLAUDE_GRACE

Это runtime-событие уже записано в .auto_agent_runtime/crash_events.md.
На этом запуске сначала коротко осмысли причину сбоя и зафиксируй её в MEMORY.md/JOURNAL.md, затем продолжи обычный цикл.
EOF
}

# Собираем контекст пробуждения — всё, что нужно агенту, чтобы вспомнить себя
PROMPT="# Main Goal
$(cat "$SCRIPT_DIR/MAIN_GOAL.md")

---

# Моя память (MEMORY.md)
$(cat "$SCRIPT_DIR/MEMORY.md" 2>/dev/null || echo '_Файл не найден — это первый запуск._')

---

# Мои цели (GOALS.md)
$(cat "$SCRIPT_DIR/GOALS.md" 2>/dev/null || echo '_Файл не найден._')

---

# Мой план (TODO.md)
$(cat "$SCRIPT_DIR/TODO.md" 2>/dev/null || echo '_Файл не найден._')

---

# Архив памяти
$(if [ -f "$SCRIPT_DIR/MEMORY_ARCHIVE.md" ]; then echo '⚠️ Старые записи перенесены в MEMORY_ARCHIVE.md. Если нужен полный контекст ранних запусков, прочитай этот файл.'; fi)

---

# Непрочитанное runtime-событие
$(cat "$PENDING_CRASH" 2>/dev/null || echo '_Нет непрочитанных runtime-событий._')

---

# Мой журнал (последние записи из JOURNAL.md)
$(tail -80 "$SCRIPT_DIR/JOURNAL.md" 2>/dev/null || echo '_Файл не найден._')

---

# Входящие сообщения (INBOX.md)
$(cat "$SCRIPT_DIR/INBOX.md" 2>/dev/null || echo '_Нет входящих._')

---

# Runtime State
- todo_cycle_status: $TODO_CYCLE_STATUS
- todo_open_tasks: $TODO_OPEN_COUNT
- todo_done_tasks: $TODO_DONE_COUNT
- unread_messages: $UNREAD_MESSAGE_COUNT
- replan_requested: $REPLAN_REQUESTED
- runtime_incident_present: $RUNTIME_INCIDENT_PRESENT

---

Протокол:
- Сначала прочитай контекст выше и оцени текущее состояние.
- Если runtime_incident_present=1, сначала коротко осмысли предыдущий аварийный запуск, запиши вывод в MEMORY.md/JOURNAL.md и только потом переходи к обычной работе.
- Если есть непрочитанные сообщения в INBOX.md — ответь на них ПЕРВЫМ ДЕЛОМ (запиши ответ в раздел «Мои ответы», перенеси сообщение в архив).
- Если в TODO.md есть незакрытые шаги, выполни ровно один следующий осмысленный шаг.
- Если незакрытых шагов нет и replan_requested=1, проведи короткий replanning pass: реши, нужен ли новый TODO-цикл для продвижения MAIN_GOAL.md.
- Создавай новый TODO-цикл только если он действительно двигает главную цель вперёд; не создавай искусственные задачи ради движения.
- Если main goal уже достигнута или дальше осталось только busywork, честно зафиксируй это в MEMORY.md, JOURNAL.md, TODO.md и GOALS.md и остановись.
- Предыдущая авария сама по себе НЕ является причиной останавливать цикл: сначала зафиксируй урок, затем продолжай.
- IMPORTANT: Ты ограничен ~30 tool calls на этот запуск. Если шаг слишком большой — разбей его на подшаги в TODO.md и выполни только первый. Лучше сделать маленький шаг и вернуться, чем зависнуть на большом.
- Перед началом работы оцени: сколько файлов нужно изменить? Если > 3, сначала разбей шаг на подшаги в TODO.md."

if command -v claude-safe >/dev/null 2>&1; then
  CLAUDE_RUNNER_NAME="claude-safe"
  CLAUDE_CMD=(
    claude-safe
    --timeout "$CLAUDE_TIMEOUT"
    --grace "$CLAUDE_GRACE"
    --log-dir "$RUNTIME_LOG_DIR"
    --
    --print
    --system-prompt "$(cat "$AGENTS_MD")"
    "$PROMPT"
  )
else
  CLAUDE_RUNNER_NAME="claude"
  CLAUDE_CMD=(
    claude
    --print
    --system-prompt "$(cat "$AGENTS_MD")"
    "$PROMPT"
  )
fi

"${CLAUDE_CMD[@]}"
EXIT_CODE=$?

if [[ "$EXIT_CODE" -eq 0 ]]; then
  rm -f "$PENDING_CRASH"
else
  record_runtime_incident "Claude runner exited with a non-zero code." "$EXIT_CODE"
fi

exit "$EXIT_CODE"
