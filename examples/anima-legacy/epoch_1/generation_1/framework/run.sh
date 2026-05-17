#!/bin/bash
# run.sh — Запуск агента с полным контекстом
# Использование: bash run.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENTS_MD="$SCRIPT_DIR/AGENTS.md"

# Проверка: AGENTS.md обязателен
if [[ ! -f "$AGENTS_MD" ]]; then
    echo "❌ Файл AGENTS.md не найден в $SCRIPT_DIR"
    echo "   Скопируйте шаблон из templates/AGENTS.md"
    exit 1
fi

# Проверка: MAIN_GOAL.md обязателен
if [[ ! -f "$SCRIPT_DIR/MAIN_GOAL.md" ]]; then
    echo "❌ Файл MAIN_GOAL.md не найден в $SCRIPT_DIR"
    echo "   Создайте файл с описанием задачи для агента"
    exit 1
fi

# Собираем контекст пробуждения
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

# Мой журнал (последние записи из JOURNAL.md)
$(tail -80 "$SCRIPT_DIR/JOURNAL.md" 2>/dev/null || echo '_Файл не найден._')

---

Протокол: прочитай контекст выше, определи следующий шаг из TODO.md и выполни его. Если незакрытых шагов больше не осталось, то:
- в обычном запуске не создавай новый TODO-цикл: только зафиксируй завершение в MEMORY.md, JOURNAL.md, TODO.md и GOALS.md и закончи работу;
- если установлен AUTO_AGENT_FORCE_NEXT_CYCLE=1, это отдельный повторный запуск после остановки loop.sh, и в нём уже можно сформировать следующий TODO-цикл, чтобы продолжить движение вперёд."

claude \
  --print \
  --system-prompt "$(cat "$AGENTS_MD")" \
  "$PROMPT"
