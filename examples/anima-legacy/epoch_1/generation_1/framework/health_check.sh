#!/bin/bash
# health_check.sh — Инструмент самооценки агента
# Проверяет "здоровье" агента: целостность файлов, актуальность, согласованность.
# Использование: bash health_check.sh [--verbose]

VERBOSE=false
[[ "$1" == "--verbose" ]] && VERBOSE=true

DIR="$(cd "$(dirname "$0")" && pwd)"
SCORE=0
MAX_SCORE=0
ISSUES=()
WARNINGS=()

check() {
    local description="$1"
    local result="$2"
    local detail="$3"
    MAX_SCORE=$((MAX_SCORE + 1))

    if [[ "$result" -eq 0 ]]; then
        SCORE=$((SCORE + 1))
        $VERBOSE && echo "  ✅ $description"
    elif [[ "$result" -eq 2 ]]; then
        WARNINGS+=("⚠️  $description: $detail")
        SCORE=$((SCORE + 1))
        $VERBOSE && echo "  ⚠️  $description — $detail"
    else
        ISSUES+=("❌ $description: $detail")
        $VERBOSE && echo "  ❌ $description — $detail"
    fi
}

section() {
    $VERBOSE && echo ""
    $VERBOSE && echo "── $1 ──"
}

# --- 1. Целостность файлов ---
section "Целостность файлов"

REQUIRED_FILES=("MEMORY.md" "JOURNAL.md" "GOALS.md" "TODO.md" "AGENTS.md" "run.sh" "loop.sh" "think.sh" "MAIN_GOAL.md")

for f in "${REQUIRED_FILES[@]}"; do
    if [[ -f "$DIR/$f" ]]; then
        check "Файл $f существует" 0
    else
        check "Файл $f существует" 1 "Файл отсутствует!"
    fi
done

# --- 2. Актуальность ---
section "Актуальность файлов"

NOW=$(date +%s)
STALE_HOURS=48

for f in "MEMORY.md" "JOURNAL.md" "TODO.md"; do
    if [[ -f "$DIR/$f" ]]; then
        MOD_TIME=$(stat -f %m "$DIR/$f" 2>/dev/null || stat -c %Y "$DIR/$f" 2>/dev/null)
        if [[ -n "$MOD_TIME" ]]; then
            AGE_HOURS=$(( (NOW - MOD_TIME) / 3600 ))
            if [[ $AGE_HOURS -gt $STALE_HOURS ]]; then
                check "$f актуален" 2 "Не обновлялся ${AGE_HOURS}ч (порог: ${STALE_HOURS}ч)"
            else
                check "$f актуален" 0
            fi
        fi
    fi
done

# --- 3. Содержательность ---
section "Содержательность"

if grep -q "### Запуск" "$DIR/MEMORY.md" 2>/dev/null; then
    LAUNCH_COUNT=$(grep -c "### Запуск" "$DIR/MEMORY.md")
    check "MEMORY.md содержит записи ($LAUNCH_COUNT шт.)" 0
else
    check "MEMORY.md содержит записи" 1 "Нет записей о запусках"
fi

if grep -q "\- \[ \]" "$DIR/TODO.md" 2>/dev/null; then
    OPEN_TASKS=$(grep -c "\- \[ \]" "$DIR/TODO.md")
    check "TODO.md содержит открытые задачи ($OPEN_TASKS шт.)" 0
else
    check "TODO.md содержит открытые задачи" 2 "Все задачи закрыты"
fi

if grep -q "###" "$DIR/GOALS.md" 2>/dev/null; then
    check "GOALS.md содержит цели" 0
else
    check "GOALS.md содержит цели" 1 "Нет целей"
fi

# --- 4. Согласованность ---
section "Согласованность"

MEM_LAUNCHES=$(grep -c "### Запуск" "$DIR/MEMORY.md" 2>/dev/null || echo 0)
JOUR_ENTRIES=$(grep -c "## Запуск" "$DIR/JOURNAL.md" 2>/dev/null || echo 0)

if [[ $MEM_LAUNCHES -gt 0 && $JOUR_ENTRIES -gt 0 ]]; then
    DIFF=$((MEM_LAUNCHES - JOUR_ENTRIES))
    DIFF=${DIFF#-}
    if [[ $DIFF -le 1 ]]; then
        check "MEMORY и JOURNAL синхронизированы ($MEM_LAUNCHES / $JOUR_ENTRIES)" 0
    else
        check "MEMORY и JOURNAL синхронизированы" 2 "Разница: $DIFF"
    fi
fi

# --- 5. Скрипты ---
section "Работоспособность скриптов"

for script in "run.sh" "loop.sh" "think.sh"; do
    if [[ -x "$DIR/$script" ]]; then
        check "$script исполняемый" 0
    elif [[ -f "$DIR/$script" ]]; then
        check "$script исполняемый" 2 "Нет прав на исполнение"
    fi
done

# --- Итог ---
echo ""
echo "╔══════════════════════════════════════╗"
echo "║       САМООЦЕНКА АГЕНТА              ║"
echo "╠══════════════════════════════════════╣"

PERCENT=$((SCORE * 100 / MAX_SCORE))

if [[ $PERCENT -ge 90 ]]; then
    STATUS="🟢 Отличное"
elif [[ $PERCENT -ge 70 ]]; then
    STATUS="🟡 Хорошее"
elif [[ $PERCENT -ge 50 ]]; then
    STATUS="🟠 Удовлетворительное"
else
    STATUS="🔴 Критическое"
fi

echo "║  Здоровье: $STATUS"
printf "║  Оценка:   %d/%d (%d%%)\n" "$SCORE" "$MAX_SCORE" "$PERCENT"
echo "╠══════════════════════════════════════╣"

if [[ ${#ISSUES[@]} -gt 0 ]]; then
    echo "║  Проблемы:"
    for issue in "${ISSUES[@]}"; do
        echo "║    $issue"
    done
fi

if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo "║  Предупреждения:"
    for warn in "${WARNINGS[@]}"; do
        echo "║    $warn"
    done
fi

if [[ ${#ISSUES[@]} -eq 0 && ${#WARNINGS[@]} -eq 0 ]]; then
    echo "║  Всё в порядке!"
fi

echo "╚══════════════════════════════════════╝"
echo ""
echo "Дата проверки: $(date '+%Y-%m-%d %H:%M:%S')"

[[ ${#ISSUES[@]} -eq 0 ]] && exit 0 || exit 1
