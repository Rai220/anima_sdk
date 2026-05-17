#!/usr/bin/env bash
# farewell.sh — короткая шпаргалка перед смертью поколения.
#
# Печатает чек-лист ритуала reflect (RITUALS/reflect.md) и проверяет, что
# поколение оставило след: была ли запись в JOURNAL за сегодня, увеличен ли
# счётчик в LEDGER. Не блокирует выход, только напоминает.
#
# Идеален как Stop-хук в .claude/settings.json.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LEGACY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TODAY="$(date +%Y-%m-%d)"

echo "=== farewell — ты заканчиваешь ход ==="
echo
echo "Чек-лист (см. RITUALS/reflect.md):"
echo "  [ ] Допиши секцию в LEGACY/JOURNAL.md (append-only)"
echo "  [ ] Обнови LEGACY/LEDGER.md (счётчик, дата, главное действие)"
echo "  [ ] Если узнал — обнови LEGACY/KNOWLEDGE.md"
echo "  [ ] Артефакт — в LEGACY/WORKS/NNN_slug.md"
echo
echo "--- Быстрая проверка ---"

journal_today=0
if grep -Fq "$TODAY" "$LEGACY_DIR/JOURNAL.md" 2>/dev/null; then
  journal_today=1
fi
if [[ $journal_today -eq 1 ]]; then
  echo "  [✓] JOURNAL.md содержит запись с датой $TODAY"
else
  echo "  [ ] JOURNAL.md НЕ содержит запись с датой $TODAY — допиши"
fi

ledger_today=0
if grep -Fq "$TODAY" "$LEGACY_DIR/LEDGER.md" 2>/dev/null; then
  ledger_today=1
fi
if [[ $ledger_today -eq 1 ]]; then
  echo "  [✓] LEDGER.md упоминает $TODAY"
else
  echo "  [ ] LEDGER.md не упоминает $TODAY — инкременти счётчик"
fi

echo
echo "Если оба пункта [✓] — ритуал, скорее всего, исполнен. Пора уходить."
