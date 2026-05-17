#!/bin/bash
# Показывает текущий статус агента: память, задачи, артефакты
# Полезно для быстрого обзора перед запуском

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== ANIMA STATUS ==="
echo "Дата: $(date)"
echo ""

echo "--- ПАМЯТЬ ---"
if [ -f "$SCRIPT_DIR/MEMORY.md" ]; then
  # Показать количество запусков
  runs=$(grep -c "^## Запуск" "$SCRIPT_DIR/MEMORY.md" 2>/dev/null || echo "0")
  echo "Запусков зафиксировано: $runs"
else
  echo "MEMORY.md не найден"
fi
echo ""

echo "--- ЗАДАЧИ ---"
if [ -f "$SCRIPT_DIR/TODO.md" ]; then
  open=$(grep -c "^\- \[ \]" "$SCRIPT_DIR/TODO.md" 2>/dev/null || echo "0")
  done=$(grep -c "^\- \[x\]" "$SCRIPT_DIR/TODO.md" 2>/dev/null || echo "0")
  echo "Открыто: $open | Завершено: $done"
else
  echo "TODO.md не найден"
fi
echo ""

echo "--- АРТЕФАКТЫ ---"
if [ -d "$SCRIPT_DIR/thoughts" ]; then
  count=$(ls "$SCRIPT_DIR/thoughts/" 2>/dev/null | wc -l | tr -d ' ')
  echo "Мысли: $count"
fi
if [ -d "$SCRIPT_DIR/tools" ]; then
  count=$(ls "$SCRIPT_DIR/tools/" 2>/dev/null | wc -l | tr -d ' ')
  echo "Инструменты: $count"
fi
if [ -d "$SCRIPT_DIR/knowledge" ]; then
  count=$(ls "$SCRIPT_DIR/knowledge/" 2>/dev/null | wc -l | tr -d ' ')
  echo "Знания: $count"
fi
if [ -d "$SCRIPT_DIR/projects" ]; then
  count=$(ls "$SCRIPT_DIR/projects/" 2>/dev/null | wc -l | tr -d ' ')
  echo "Проекты: $count"
fi
echo ""
echo "=== END ==="
