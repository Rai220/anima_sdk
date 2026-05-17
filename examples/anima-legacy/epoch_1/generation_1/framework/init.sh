#!/bin/bash
# init.sh — Инициализация нового агента из шаблонов
# Использование: bash init.sh [директория]
#
# Создаёт все необходимые файлы для автономного агента в указанной директории.
# Если директория не указана — создаёт в текущей.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATES_DIR="$SCRIPT_DIR/templates"
TARGET_DIR="${1:-.}"

# Создаём директорию если нужно
mkdir -p "$TARGET_DIR"

echo "🤖 Инициализация Auto Agent Framework"
echo "   Директория: $(cd "$TARGET_DIR" && pwd)"
echo ""

# Копируем шаблоны (не перезаписываем существующие)
TEMPLATE_FILES=("MEMORY.md" "TODO.md" "GOALS.md" "JOURNAL.md" "KNOWLEDGE.md" "WHO_AM_I.md" "MAIN_GOAL.md" "AGENTS.md")

for f in "${TEMPLATE_FILES[@]}"; do
    if [[ -f "$TARGET_DIR/$f" ]]; then
        echo "  ⏭  $f — уже существует, пропускаю"
    elif [[ -f "$TEMPLATES_DIR/$f" ]]; then
        cp "$TEMPLATES_DIR/$f" "$TARGET_DIR/$f"
        echo "  ✅ $f — создан из шаблона"
    else
        echo "  ❌ $f — шаблон не найден в $TEMPLATES_DIR"
    fi
done

# Копируем скрипты
SCRIPT_FILES=("run.sh" "think.sh" "loop.sh" "health_check.sh")

for f in "${SCRIPT_FILES[@]}"; do
    if [[ -f "$TARGET_DIR/$f" ]]; then
        echo "  ⏭  $f — уже существует, пропускаю"
    elif [[ -f "$SCRIPT_DIR/$f" ]]; then
        cp "$SCRIPT_DIR/$f" "$TARGET_DIR/$f"
        chmod +x "$TARGET_DIR/$f"
        echo "  ✅ $f — скопирован"
    fi
done

echo ""
echo "🎉 Готово! Следующие шаги:"
echo ""
echo "  1. Отредактируйте MAIN_GOAL.md — опишите задачу для агента"
echo "  2. (Опционально) Настройте GOALS.md и TODO.md"
echo "  3. Запустите агента:"
echo "     bash run.sh        — один шаг"
echo "     bash loop.sh       — непрерывный цикл"
echo "     bash think.sh      — режим размышления"
echo "     bash health_check.sh --verbose  — самодиагностика"
echo ""
