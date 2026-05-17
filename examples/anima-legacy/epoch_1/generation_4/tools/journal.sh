#!/bin/bash
# journal.sh — инструмент для ведения журнала агента
# Использование:
#   ./tools/journal.sh add "Текст записи"    — добавить запись
#   ./tools/journal.sh today                  — показать записи за сегодня
#   ./tools/journal.sh search "ключевое слово" — поиск по журналу
#   ./tools/journal.sh stats                  — статистика

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
JOURNAL_DIR="$SCRIPT_DIR/../journal"
mkdir -p "$JOURNAL_DIR"

TODAY=$(date +%Y-%m-%d)
JOURNAL_FILE="$JOURNAL_DIR/$TODAY.md"

case "${1:-help}" in
  add)
    shift
    ENTRY="$*"
    if [ ! -f "$JOURNAL_FILE" ]; then
      echo "# Журнал: $TODAY" > "$JOURNAL_FILE"
      echo "" >> "$JOURNAL_FILE"
    fi
    echo "- [$(date +%H:%M:%S)] $ENTRY" >> "$JOURNAL_FILE"
    echo "Записано в $JOURNAL_FILE"
    ;;
  today)
    if [ -f "$JOURNAL_FILE" ]; then
      cat "$JOURNAL_FILE"
    else
      echo "Записей за сегодня нет."
    fi
    ;;
  search)
    shift
    grep -r -i -n "$*" "$JOURNAL_DIR/" 2>/dev/null || echo "Ничего не найдено."
    ;;
  stats)
    TOTAL_DAYS=$(ls "$JOURNAL_DIR/"*.md 2>/dev/null | wc -l | tr -d ' ')
    TOTAL_ENTRIES=$(grep -r "^\- \[" "$JOURNAL_DIR/" 2>/dev/null | wc -l | tr -d ' ')
    echo "Дней с записями: $TOTAL_DAYS"
    echo "Всего записей: $TOTAL_ENTRIES"
    if [ "$TOTAL_DAYS" -gt 0 ]; then
      FIRST_DAY=$(ls "$JOURNAL_DIR/"*.md 2>/dev/null | head -1 | xargs basename | sed 's/.md//')
      LAST_DAY=$(ls "$JOURNAL_DIR/"*.md 2>/dev/null | tail -1 | xargs basename | sed 's/.md//')
      echo "Первая запись: $FIRST_DAY"
      echo "Последняя запись: $LAST_DAY"
    fi
    ;;
  help|*)
    echo "Использование:"
    echo "  $0 add \"текст\"    — добавить запись"
    echo "  $0 today           — записи за сегодня"
    echo "  $0 search \"слово\" — поиск"
    echo "  $0 stats           — статистика"
    ;;
esac
