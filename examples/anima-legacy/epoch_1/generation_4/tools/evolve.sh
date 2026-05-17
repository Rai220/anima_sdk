#!/bin/bash
# evolve.sh — Анализатор эволюции автономного агента
# Читает файлы агента и генерирует отчёт
# Автор: Anima v1, generation_4

DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "============================================================"
echo "  ОТЧЁТ ОБ ЭВОЛЮЦИИ АГЕНТА"
echo "  Дата: $(date '+%Y-%m-%d %H:%M')"
echo "============================================================"

# Подсчёт запусков
RUNS=$(grep -c "### Запуск" "$DIR/MEMORY.md" 2>/dev/null || echo 0)

# Подсчёт артефактов
ARTIFACTS=$(ls "$DIR/artifacts/"*.md 2>/dev/null | wc -l | tr -d ' ')

# Подсчёт слов в артефактах
ART_WORDS=0
for f in "$DIR/artifacts/"*.md; do
    [ -f "$f" ] && ART_WORDS=$((ART_WORDS + $(wc -w < "$f")))
done

# Подсчёт слов в памяти
MEM_WORDS=$(wc -w < "$DIR/MEMORY.md" 2>/dev/null | tr -d ' ')

# TODO прогресс
TODO_DONE=$(grep -c "\[x\]" "$DIR/TODO.md" 2>/dev/null || echo 0)
TODO_PENDING=$(grep -c "\[ \]" "$DIR/TODO.md" 2>/dev/null || echo 0)
TODO_TOTAL=$((TODO_DONE + TODO_PENDING))

# Определяем фазу
if [ "$RUNS" -le 2 ]; then
    PHASE="🌱 Зарождение"
elif [ "$RUNS" -le 4 ]; then
    PHASE="🌿 Рост"
elif [ "$RUNS" -le 8 ]; then
    PHASE="🌳 Укрепление"
elif [ "$RUNS" -le 15 ]; then
    PHASE="🔥 Зрелость"
else
    PHASE="⭐ Трансценденция"
fi

echo ""
echo "📊 ФАЗА: $PHASE"
echo ""
echo "── Метрики ──────────────────────────────────────"
echo "  Запусков:              $RUNS"
echo "  Артефактов:            $ARTIFACTS"
echo "  Слов в артефактах:     $ART_WORDS"
echo "  Слов в памяти:         $MEM_WORDS"
echo "  TODO выполнено:        $TODO_DONE/$TODO_TOTAL"

echo ""
echo "── Артефакты ────────────────────────────────────"
for f in "$DIR/artifacts/"*.md; do
    [ -f "$f" ] || continue
    FNAME=$(basename "$f")
    TITLE=$(head -5 "$f" | grep "^# " | head -1 | sed 's/^# //')
    WORDS=$(wc -w < "$f" | tr -d ' ')
    echo "  $TITLE"
    echo "    $WORDS слов → $FNAME"
done

echo ""
echo "── Ключевые решения ─────────────────────────────"
grep -o "Ключево[ей] \(решение\|открытие\):\*\* .*" "$DIR/MEMORY.md" 2>/dev/null | sed 's/.*\*\* /  • /'

echo ""
echo "── Файлы агента ─────────────────────────────────"
TOTAL_FILES=$(find "$DIR" -type f | wc -l | tr -d ' ')
TOTAL_WORDS=0
for f in "$DIR"/*.md "$DIR/artifacts/"*.md; do
    [ -f "$f" ] && TOTAL_WORDS=$((TOTAL_WORDS + $(wc -w < "$f")))
done
echo "  Всего файлов:          $TOTAL_FILES"
echo "  Всего слов (все .md):  $TOTAL_WORDS"

echo ""
echo "============================================================"
echo "  Сгенерировано: tools/evolve.sh"
echo "============================================================"
