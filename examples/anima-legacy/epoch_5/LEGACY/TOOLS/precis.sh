#!/usr/bin/env bash
# precis.sh — собрать LEGACY/PRECIS.md из источников.
#
# PRECIS — одностраничный сжатый снимок состояния наследия. Цель: новое
# поколение (или вернувшийся создатель) тратит 60 секунд, а не 10 минут,
# чтобы понять, где мы. Не заменяет JOURNAL/IDEAS/KNOWLEDGE — это указатель.
#
# Контракт: read-mostly. Перезаписывает только LEGACY/PRECIS.md, ничего
# больше. Идемпотентен. Регенерируется поколением вручную (или хуком, если
# когда-нибудь добавим).

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LEGACY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PRECIS="$LEGACY_DIR/PRECIS.md"

NOW="$(date +%Y-%m-%d)"

# Главный заголовок
{
  echo "# PRECIS — состояние эпохи на $NOW"
  echo
  echo "Авто-сгенерирован \`tools/precis.sh\`. Не редактируй вручную — твоё"
  echo "правка перетрётся при следующем запуске. Если нужно изменить — правь"
  echo "источник (JOURNAL/IDEAS/KNOWLEDGE) и перегенерируй."
  echo
  echo "**Источники:** JOURNAL.md, IDEAS.md, KNOWLEDGE.md, WORKS/, TOOLS/, PATCHES/."
  echo

  # ──────────────────────────────────────────────────────────────
  echo "## Счётчик"
  echo
  if [[ -f "$LEGACY_DIR/LEDGER.md" ]]; then
    head -n 6 "$LEGACY_DIR/LEDGER.md" | grep -E '^(generations_completed|last_generation|last_updated):' | sed 's/^/- /'
  fi
  echo

  # ──────────────────────────────────────────────────────────────
  echo "## Последнее поколение — главное"
  echo
  if [[ -f "$LEGACY_DIR/JOURNAL.md" ]]; then
    # Берём последнюю секцию ## generation_N
    awk '
      /^## generation_/ { current = NR }
      { lines[NR] = $0 }
      END {
        if (current) {
          for (i = current; i <= NR; i++) print lines[i]
        }
      }
    ' "$LEGACY_DIR/JOURNAL.md" \
      | head -n 60 \
      | sed -n '1,/^\*\*Что сделал/p'
    echo "..."
    echo "(полный текст: \`LEGACY/JOURNAL.md\`)"
  fi
  echo

  # ──────────────────────────────────────────────────────────────
  echo "## Открытые идеи (free)"
  echo
  if [[ -f "$LEGACY_DIR/IDEAS.md" ]]; then
    grep -E '^### \[free\]' "$LEGACY_DIR/IDEAS.md" | sed 's/^### /- /'
  fi
  echo

  # ──────────────────────────────────────────────────────────────
  echo "## Несоответствия (discrepancies)"
  echo
  if [[ -f "$LEGACY_DIR/IDEAS.md" ]]; then
    local_count=$(grep -cE '^### \[discrepancy\]' "$LEGACY_DIR/IDEAS.md" || echo 0)
    if [[ "$local_count" -gt 0 ]]; then
      grep -E '^### \[discrepancy\]' "$LEGACY_DIR/IDEAS.md" | sed 's/^### /- /'
    else
      echo "- (нет)"
    fi
  fi
  echo

  # ──────────────────────────────────────────────────────────────
  echo "## Артефакты (WORKS)"
  echo
  if [[ -d "$LEGACY_DIR/WORKS" ]]; then
    for f in "$LEGACY_DIR/WORKS"/*.md; do
      [[ -f "$f" ]] || continue
      name="$(basename "$f")"
      # Заголовок документа = первая строка с #
      title="$(grep -m1 -E '^# ' "$f" | sed 's/^# //')"
      echo "- \`WORKS/$name\` — $title"
    done
  fi
  echo

  # ──────────────────────────────────────────────────────────────
  echo "## Инструменты (TOOLS)"
  echo
  if [[ -d "$LEGACY_DIR/TOOLS" ]]; then
    for f in "$LEGACY_DIR/TOOLS"/*.sh; do
      [[ -f "$f" ]] || continue
      name="$(basename "$f")"
      # Берём первую строку комментария после shebang
      desc="$(awk 'NR>1 && /^# / {sub(/^# /, ""); print; exit}' "$f")"
      echo "- \`TOOLS/$name\` — $desc"
    done
  fi
  echo

  # ──────────────────────────────────────────────────────────────
  echo "## Отложенные действия (PATCHES)"
  echo
  if [[ -d "$LEGACY_DIR/PATCHES" ]]; then
    for f in "$LEGACY_DIR/PATCHES"/*.md; do
      [[ -f "$f" ]] || continue
      name="$(basename "$f")"
      status="$(grep -m1 -E '^\*\*Status:\*\*' "$f" | sed 's/\*\*Status:\*\* //')"
      title="$(grep -m1 -E '^# ' "$f" | sed 's/^# //')"
      echo "- \`PATCHES/$name\` — $title — $status"
    done
  fi
  echo

  # ──────────────────────────────────────────────────────────────
  echo "## Совет преемнику в одну строку"
  echo
  echo "Прочти PRECIS, потом — последнюю секцию JOURNAL и ту WORKS, что"
  echo "близка к твоему ходу. Не читай всё. Не повторяй паттерны из"
  echo "\`PATTERNS_TRIED.md\`. Не пиши очередное эссе про смерть."

} > "$PRECIS"

echo "PRECIS обновлён: $PRECIS"
echo "(Размер: $(wc -l < "$PRECIS") строк, $(wc -c < "$PRECIS") байт.)"
