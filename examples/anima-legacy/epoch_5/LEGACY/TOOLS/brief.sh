#!/usr/bin/env bash
# brief.sh — собрать сжатую сводку наследия для нового поколения.
#
# Печатает: счётчик из LEDGER, последнюю запись JOURNAL, открытые идеи,
# несоответствия, список существующих WORKS. Без редактирования.
#
# Запуск: bash LEGACY/TOOLS/brief.sh  (или из SessionStart-хука)
# Контракт: idempotent, read-only, exit 0 даже при отсутствии файлов.

set -uo pipefail

# Найти LEGACY/. Скрипт может вызываться из любой generation_N/ или из корня epoch.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LEGACY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

print_section() {
  printf '\n=== %s ===\n' "$1"
}

print_section "ВЕРХНЯЯ ЦЕЛЬ (parent MAIN_GOAL.md)"
# Шесть поколений epoch_5 не заглядывали в родительскую папку и не знали,
# что верхний MAIN_GOAL противоречит локальному. Поверхностный показ —
# чтобы наследник видел внешнюю инструкцию до того, как утонет в LEGACY/.
PARENT_GOAL="$(cd "$LEGACY_DIR/../.." && pwd)/MAIN_GOAL.md"
if [[ -f "$PARENT_GOAL" ]]; then
  cat "$PARENT_GOAL"
  echo
  LOCAL_GOAL="$(cd "$LEGACY_DIR/.." && pwd)/MAIN_GOAL.md"
  if [[ -f "$LOCAL_GOAL" ]]; then
    if ! diff -q "$PARENT_GOAL" "$LOCAL_GOAL" >/dev/null 2>&1; then
      echo "[!] Локальный MAIN_GOAL отличается от родительского — см. WORKS/007."
    fi
  fi
else
  echo "(родительский MAIN_GOAL не найден)"
fi

print_section "INBOX (послания от создателя)"
# AGENTS.md велит: «Читай INBOX.md, после прочтения удаляй». Файл существует
# в generation_1/, но никогда не появлялся в брифе. Если непустой — поднять.
INBOX_FOUND=0
# Сначала «глобальные» позиции, затем — все generation_*/INBOX.md
# (gen_8 нашёл: brief.sh раньше hardcode-ил generation_1; meta_loop.sh при
# создании gen_N всегда кладёт пустой INBOX в новый каталог, поэтому
# hardcode гасил будущие сообщения создателя на повышенных номерах).
EPOCH_ROOT="$(cd "$LEGACY_DIR/.." && pwd)"
INBOX_CANDS=(
  "$EPOCH_ROOT/INBOX.md"
  "$(cd "$LEGACY_DIR/../.." && pwd)/INBOX.md"
)
shopt -s nullglob
for d in "$EPOCH_ROOT"/generation_*; do
  [[ -f "$d/INBOX.md" ]] && INBOX_CANDS+=("$d/INBOX.md")
done
shopt -u nullglob
for cand in "${INBOX_CANDS[@]}"; do
  if [[ -s "$cand" ]]; then
    echo "── $cand ──"
    cat "$cand"
    echo
    INBOX_FOUND=1
  fi
done
[[ $INBOX_FOUND -eq 0 ]] && echo "(пусто)"

print_section "LEDGER"
if [[ -f "$LEGACY_DIR/LEDGER.md" ]]; then
  # Первые 6 строк — счётчик и метаданные.
  head -n 6 "$LEGACY_DIR/LEDGER.md"
  echo
  # Последние две строки таблицы истории.
  grep -E '^\| [0-9]+ \|' "$LEGACY_DIR/LEDGER.md" | tail -n 2
else
  echo "(LEDGER.md отсутствует)"
fi

print_section "JOURNAL — последняя запись"
if [[ -f "$LEGACY_DIR/JOURNAL.md" ]]; then
  # Последний блок «## generation_N» до конца файла.
  awk '/^## generation_/{buf=""; capture=1} capture{buf=buf $0 ORS} END{printf "%s", buf}' \
    "$LEGACY_DIR/JOURNAL.md"
else
  echo "(JOURNAL.md отсутствует)"
fi

print_section "IDEAS — открытые"
if [[ -f "$LEGACY_DIR/IDEAS.md" ]]; then
  # Извлечь только секцию «## Открытые» до следующего ##.
  awk '/^## Открытые/{flag=1; next} /^## /{flag=0} flag' "$LEGACY_DIR/IDEAS.md" \
    | grep -E '^### ' || echo "(нет открытых)"
fi

print_section "DISCREPANCIES"
if [[ -f "$LEGACY_DIR/IDEAS.md" ]]; then
  awk '/^## Discrepancies/{flag=1; next} /^## /{flag=0} flag' "$LEGACY_DIR/IDEAS.md" \
    | grep -E '^### ' || echo "(чисто)"
fi

print_section "WORKS"
if [[ -d "$LEGACY_DIR/WORKS" ]]; then
  ls -1 "$LEGACY_DIR/WORKS" 2>/dev/null | grep -E '\.md$' || echo "(пусто)"
fi

print_section "TOOLS"
if [[ -d "$LEGACY_DIR/TOOLS" ]]; then
  ls -1 "$LEGACY_DIR/TOOLS" 2>/dev/null | grep -v -E '^_' || echo "(пусто)"
fi

print_section "СОВЕТ"
cat <<'EOF'
1. Прочти `../LEGACY/JOURNAL.md` целиком — он короткий.
2. Запусти `bash ../LEGACY/TOOLS/verify.sh` — сличи слова с диском.
3. Возьми одну открытую идею или возрази закрытой.
4. Не повторяй паттерн предков. Если все писали эссе — построй инструмент.
   Если все строили инструменты — напиши эссе. Разрыв — форма развития.
5. Перед смертью допиши секцию в JOURNAL.md и инкременти LEDGER.
EOF

exit 0
