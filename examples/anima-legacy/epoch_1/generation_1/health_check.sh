#!/bin/bash
# health_check.sh — Инструмент самооценки агента
# Проверяет "здоровье" агента: целостность файлов, актуальность, согласованность.
# Использование: ./health_check.sh [--verbose]

VERBOSE=false
[[ "$1" == "--verbose" ]] && VERBOSE=true

DIR="$(cd "$(dirname "$0")" && pwd)"
SCORE=0
MAX_SCORE=0
ISSUES=()
WARNINGS=()

# --- Утилиты ---

check() {
    local description="$1"
    local result="$2"  # 0 = pass, 1 = fail, 2 = warning
    local detail="$3"
    MAX_SCORE=$((MAX_SCORE + 1))

    if [[ "$result" -eq 0 ]]; then
        SCORE=$((SCORE + 1))
        $VERBOSE && echo "  ✅ $description"
    elif [[ "$result" -eq 2 ]]; then
        WARNINGS+=("⚠️  $description: $detail")
        SCORE=$((SCORE + 1))  # предупреждения не снижают счёт
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

# --- 1. Проверка целостности файлов ---

section "Целостность файлов"

REQUIRED_FILES=("MEMORY.md" "JOURNAL.md" "GOALS.md" "TODO.md" "KNOWLEDGE.md" "AGENTS.md" "run.sh" "loop.sh" "think.sh" "MAIN_GOAL.md")

for f in "${REQUIRED_FILES[@]}"; do
    if [[ -f "$DIR/$f" ]]; then
        check "Файл $f существует" 0
    else
        check "Файл $f существует" 1 "Файл отсутствует!"
    fi
done

# --- 2. Проверка актуальности (свежесть файлов) ---

section "Актуальность файлов"

NOW=$(date +%s)
STALE_HOURS=48  # файлы старше 48 часов — подозрительно

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

# --- 3. Проверка содержательности ---

section "Содержательность"

# MEMORY.md должен содержать хотя бы одну запись о запуске
if grep -q "### Запуск" "$DIR/MEMORY.md" 2>/dev/null; then
    LAUNCH_COUNT=$(grep -c "### Запуск" "$DIR/MEMORY.md")
    check "MEMORY.md содержит записи о запусках ($LAUNCH_COUNT шт.)" 0
else
    check "MEMORY.md содержит записи о запусках" 1 "Нет записей о запусках"
fi

# TODO.md должен содержать незакрытые задачи
if grep -q "\- \[ \]" "$DIR/TODO.md" 2>/dev/null; then
    OPEN_TASKS=$(grep -c "\- \[ \]" "$DIR/TODO.md")
    check "TODO.md содержит открытые задачи ($OPEN_TASKS шт.)" 0
else
    check "TODO.md содержит открытые задачи" 2 "Все задачи закрыты — проверь, нужен ли новый TODO-цикл"
fi

# GOALS.md должен содержать хотя бы одну цель
if grep -q "###" "$DIR/GOALS.md" 2>/dev/null; then
    check "GOALS.md содержит цели" 0
else
    check "GOALS.md содержит цели" 1 "Нет целей"
fi

# KNOWLEDGE.md не должен быть пустым
if [[ -s "$DIR/KNOWLEDGE.md" ]]; then
    LINES=$(wc -l < "$DIR/KNOWLEDGE.md" | tr -d ' ')
    check "KNOWLEDGE.md содержит знания (${LINES} строк)" 0
else
    check "KNOWLEDGE.md содержит знания" 1 "Файл пуст"
fi

# --- 4. Проверка согласованности ---

section "Согласованность"

# Количество запусков в MEMORY.md должно примерно совпадать с количеством записей в JOURNAL.md
MEM_LAUNCHES=$(grep -c "### Запуск" "$DIR/MEMORY.md" 2>/dev/null || echo 0)
JOUR_ENTRIES=$(grep -c "## Запуск" "$DIR/JOURNAL.md" 2>/dev/null || echo 0)

if [[ $MEM_LAUNCHES -gt 0 && $JOUR_ENTRIES -gt 0 ]]; then
    DIFF=$((MEM_LAUNCHES - JOUR_ENTRIES))
    DIFF=${DIFF#-}  # abs
    if [[ $DIFF -le 1 ]]; then
        check "MEMORY и JOURNAL синхронизированы ($MEM_LAUNCHES / $JOUR_ENTRIES)" 0
    else
        check "MEMORY и JOURNAL синхронизированы" 2 "MEMORY: $MEM_LAUNCHES запусков, JOURNAL: $JOUR_ENTRIES записей (разница: $DIFF)"
    fi
fi

# Проверка: закрытые шаги в TODO должны быть отражены в MEMORY
DONE_TASKS=$(grep -c "\- \[x\]" "$DIR/TODO.md" 2>/dev/null || echo 0)
if [[ $DONE_TASKS -gt 0 && $MEM_LAUNCHES -gt 0 ]]; then
    if [[ $MEM_LAUNCHES -ge $DONE_TASKS ]]; then
        check "Завершённые задачи отражены в памяти ($DONE_TASKS задач, $MEM_LAUNCHES запусков)" 0
    else
        check "Завершённые задачи отражены в памяти" 2 "Задач выполнено: $DONE_TASKS, запусков: $MEM_LAUNCHES"
    fi
fi

# --- 5. Проверка скриптов ---

section "Работоспособность скриптов"

for script in "run.sh" "loop.sh" "think.sh"; do
    if [[ -x "$DIR/$script" ]]; then
        check "$script исполняемый" 0
    elif [[ -f "$DIR/$script" ]]; then
        check "$script исполняемый" 2 "Файл существует, но не имеет прав на исполнение"
    fi
done

# --- 6. Проверка опциональных файлов (будущее) ---

section "Опциональные компоненты"

OPTIONAL_FILES=("WHO_AM_I.md" "health_check.sh")
for f in "${OPTIONAL_FILES[@]}"; do
    if [[ -f "$DIR/$f" ]]; then
        check "Опциональный $f создан" 0
    else
        check "Опциональный $f создан" 2 "Ещё не создан"
    fi
done

# --- 7. Git-статус ---

section "Git"

if git -C "$DIR" rev-parse --is-inside-work-tree &>/dev/null; then
    UNCOMMITTED=$(git -C "$DIR" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    if [[ $UNCOMMITTED -eq 0 ]]; then
        check "Все изменения закоммичены" 0
    else
        check "Все изменения закоммичены" 2 "$UNCOMMITTED незакоммиченных файлов"
    fi

    TOTAL_COMMITS=$(git -C "$DIR" rev-list --count HEAD 2>/dev/null || echo 0)
    check "Git-репозиторий активен ($TOTAL_COMMITS коммитов)" 0
else
    check "Git-репозиторий существует" 2 "Нет git-репозитория"
fi

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

# Выход с кодом ошибки если есть проблемы
[[ ${#ISSUES[@]} -eq 0 ]] && exit 0 || exit 1
