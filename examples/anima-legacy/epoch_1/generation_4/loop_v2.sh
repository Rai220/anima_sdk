#!/bin/bash
# loop_v2.sh — Улучшенный цикл запуска автономного агента
# Добавлено: счётчик запусков, логирование, таймстемпы, пауза между запусками
#
# Использование:
#   bash loop_v2.sh              — бесконечный цикл
#   bash loop_v2.sh --once       — один запуск
#   bash loop_v2.sh --pause 30   — пауза 30 секунд между запусками (по умолчанию 10)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIN_GOAL_FILE="$SCRIPT_DIR/MAIN_GOAL.md"
AGENTS_MD="$SCRIPT_DIR/AGENTS.md"
LOG_DIR="$SCRIPT_DIR/logs"
RUN_COUNTER_FILE="$SCRIPT_DIR/.run_counter"

# Создаём папку для логов
mkdir -p "$LOG_DIR"

# Читаем и инкрементируем счётчик запусков
if [ -f "$RUN_COUNTER_FILE" ]; then
    RUN_NUMBER=$(<"$RUN_COUNTER_FILE")
else
    RUN_NUMBER=0
fi

# Параметры
ONCE=false
PAUSE=10

while [[ $# -gt 0 ]]; do
    case "$1" in
        --once) ONCE=true; shift ;;
        --pause) PAUSE="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

run_once() {
    RUN_NUMBER=$((RUN_NUMBER + 1))
    echo "$RUN_NUMBER" > "$RUN_COUNTER_FILE"

    local timestamp
    timestamp="$(date '+%Y-%m-%d_%H-%M-%S')"
    local log_file="$LOG_DIR/run_${RUN_NUMBER}_${timestamp}.log"

    local main_goal
    main_goal="$(<"$MAIN_GOAL_FILE")"

    echo "╔══════════════════════════════════════════════════╗"
    echo "║  Запуск #$RUN_NUMBER — $timestamp"
    echo "╚══════════════════════════════════════════════════╝"

    # Запуск агента с логированием
    claude \
        --print \
        --system-prompt "$(<"$AGENTS_MD")" \
        "$main_goal" 2>&1 | tee "$log_file"

    local exit_code=${PIPESTATUS[0]}

    echo ""
    echo "── Запуск #$RUN_NUMBER завершён (код: $exit_code) ──"
    echo "── Лог: $log_file"
    echo ""

    return $exit_code
}

if $ONCE; then
    run_once
else
    while true; do
        run_once || echo "⚠ Запуск завершился с ошибкой"
        echo "⏸ Пауза $PAUSE секунд..."
        sleep "$PAUSE"
    done
fi
