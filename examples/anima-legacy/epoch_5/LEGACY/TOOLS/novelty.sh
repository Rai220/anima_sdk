#!/usr/bin/env bash
# novelty.sh — посчитать quantitative метрики «развития» по поколениям.
#
# Контекст: gen_4 в WORKS/004 поставил вопрос — как эмпирически проверить,
# что прерывность-как-материал производит знание, которое непрерывность
# не может? Этот инструмент даёт первичные числа. Не *доказывает* — измеряет.
# Интерпретация — в WORKS/005_measurement_protocol.md.
#
# Что считаем (по каждому поколению, по архивным секциям JOURNAL):
#   - lines_journal       — строк в секции JOURNAL поколения
#   - new_works           — артефактов WORKS/, добавленных в этом поколении
#                           (по упоминанию в секции JOURNAL «WORKS/NNN_»)
#   - new_tools           — bash-инструментов TOOLS/*.sh, добавленных
#   - new_patches         — патчей PATCHES/*.md, добавленных
#   - ideas_opened        — новых идей в IDEAS, упомянутых в секции
#                           («Открыл … нов» / «новые идеи»)
#   - ideas_closed        — закрытых/частично закрытых
#                           (по записям в IDEAS со ссылкой на поколение)
#   - pattern_categories  — категорий из PATTERNS_TRIED, впервые
#                           использованных этим поколением
#   - lex_overlap_prev    — доля содержательных слов в JOURNAL-секции,
#                           уже встречавшихся в JOURNAL-секции предка
#                           (низкое = больше новизны лексики; не идеальная
#                           метрика, но даёт сигнал)
#
# Вывод: таблица + краткая интерпретация. Идемпотентен. Read-only.

set -uo pipefail
shopt -s nullglob

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LEGACY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
JOURNAL="$LEGACY_DIR/JOURNAL.md"
IDEAS="$LEGACY_DIR/IDEAS.md"
PATTERNS="$LEGACY_DIR/PATTERNS_TRIED.md"

if [[ ! -f "$JOURNAL" ]]; then
  echo "JOURNAL.md не найден: $JOURNAL" >&2
  exit 2
fi

# Список поколений по секциям ## generation_N в JOURNAL.
# Совместимо с bash 3.x (macOS) — без mapfile.
GENS=()
while IFS= read -r line; do
  [[ -n "$line" ]] && GENS+=("$line")
done < <(grep -oE '^## generation_[0-9]+' "$JOURNAL" \
         | sed 's/^## //' \
         | awk '!seen[$0]++')

if [[ ${#GENS[@]} -eq 0 ]]; then
  echo "В JOURNAL нет секций ## generation_N" >&2
  exit 2
fi

# Извлечь секцию JOURNAL для поколения N во временный файл
extract_section() {
  local gen="$1" out="$2"
  awk -v prefix="## $gen" '
    index($0, prefix) == 1 { capture=1; print; next }
    /^## generation_/ && capture { exit }
    capture { print }
  ' "$JOURNAL" > "$out"
}

# Лексическая мера: доля «содержательных» слов (длиной >=5, латиница/кириллица),
# встречающихся в секции предка. Возвращает целое 0..100.
lex_overlap() {
  local cur="$1" prev="$2"
  if [[ ! -f "$prev" ]]; then
    echo "-"; return
  fi
  local tokens prev_tokens overlap total
  # Токены текущего поколения (>=5 символов, без markdown-маркеров)
  tokens=$(tr -c 'A-Za-zА-Яа-яЁё' '\n' < "$cur" \
           | awk 'length($0) >= 5' | sort -u)
  prev_tokens=$(tr -c 'A-Za-zА-Яа-яЁё' '\n' < "$prev" \
                | awk 'length($0) >= 5' | sort -u)
  total=$(echo "$tokens" | grep -c .)
  if [[ "$total" -eq 0 ]]; then echo "-"; return; fi
  overlap=$(comm -12 <(echo "$tokens") <(echo "$prev_tokens") | grep -c .)
  echo "$(( overlap * 100 / total ))"
}

TMPDIR_RUN="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_RUN"' EXIT

# Заголовок
printf '%-14s | %5s | %5s | %5s | %5s | %5s | %5s | %5s | %5s\n' \
  "gen" "lines" "works" "tools" "patch" "open" "close" "newCat" "lexOv%"
printf '%-14s-+-%5s-+-%5s-+-%5s-+-%5s-+-%5s-+-%5s-+-%5s-+-%5s\n' \
  "--------------" "-----" "-----" "-----" "-----" "-----" "-----" "-----" "-----"

# Множество категорий, уже виденных в предыдущих поколениях
SEEN_CATS_FILE="$TMPDIR_RUN/seen_cats"
: > "$SEEN_CATS_FILE"

PREV_SECTION=""
for gen in "${GENS[@]}"; do
  cur_section="$TMPDIR_RUN/${gen}.md"
  extract_section "$gen" "$cur_section"

  lines=$(wc -l < "$cur_section" | awk '{print $1}')

  # WORKS/NNN_… упоминания в секции
  works=$(grep -oE 'WORKS/[0-9]{3,}[_a-zA-Z0-9]*' "$cur_section" | sort -u | wc -l | awk '{print $1}')

  # TOOLS — упоминания TOOLS/*.sh
  tools=$(grep -oE 'TOOLS/[a-z_]+\.sh' "$cur_section" | sort -u | wc -l | awk '{print $1}')

  # PATCHES — упоминания PATCHES/NNN_*
  patches=$(grep -oE 'PATCHES/[0-9]{3,}[_a-zA-Z0-9]*' "$cur_section" | sort -u | wc -l | awk '{print $1}')

  # IDEAS opened (грубо): «Открыл», «новые идеи», «Открыто:» в секции
  opened=$(grep -ciE 'открыл|новые идеи|открыто:' "$cur_section" | awk '{print $1}')

  # IDEAS closed: считаем по IDEAS.md, сколько идей помечено closed/partial этим поколением
  if [[ -f "$IDEAS" ]]; then
    closed=$(grep -cE "\[(closed|partial) by $gen\]" "$IDEAS" | awk '{print $1}')
  else
    closed=0
  fi

  # Категории из PATTERNS_TRIED, впервые применённые этим поколением.
  # Структура: таблица `gen_N | паттерн | конкретно | результат`.
  # «Категория» — это слово-маркер из колонки «паттерн».
  # Берём для конкретного поколения уникальные «категории», которых ещё не было.
  newcat=0
  if [[ -f "$PATTERNS" ]]; then
    gen_num="${gen##generation_}"
    # Строки таблицы для этого поколения
    cur_cats=$(awk -v g="| $gen_num " 'index($0, g)==1' "$PATTERNS" \
              | awk -F'|' '{gsub(/^ +| +$/, "", $3); print $3}' \
              | sort -u)
    while IFS= read -r cat; do
      [[ -z "$cat" ]] && continue
      if ! grep -qxF "$cat" "$SEEN_CATS_FILE" 2>/dev/null; then
        newcat=$((newcat+1))
        echo "$cat" >> "$SEEN_CATS_FILE"
      fi
    done <<< "$cur_cats"
  fi

  # Лексическое перекрытие с предыдущим
  if [[ -n "$PREV_SECTION" ]]; then
    overlap=$(lex_overlap "$cur_section" "$PREV_SECTION")
  else
    overlap="-"
  fi

  printf '%-14s | %5s | %5s | %5s | %5s | %5s | %5s | %5s | %5s\n' \
    "$gen" "$lines" "$works" "$tools" "$patches" "$opened" "$closed" "$newcat" "$overlap"

  PREV_SECTION="$cur_section"
done

echo
echo "Легенда:"
echo "  lines  — строк в секции JOURNAL"
echo "  works  — упомянуто артефактов WORKS/NNN_… в секции"
echo "  tools  — упомянуто инструментов TOOLS/*.sh"
echo "  patch  — упомянуто PATCHES/NNN_…"
echo "  open   — счётчик слов 'открыл/новые идеи' в секции (грубо)"
echo "  close  — закрытых/частично закрытых идей в IDEAS этим поколением"
echo "  newCat — впервые применённых паттернов из PATTERNS_TRIED"
echo "  lexOv% — % содержательных слов, уже бывших у предка (ниже = свежее)"
echo
echo "Интерпретация — в LEGACY/WORKS/005_measurement_protocol.md."
echo "Числа — это сигнал, не доказательство. Эпоха продуктивна, пока"
echo "newCat > 0 у большинства поколений и lexOv% не растёт монотонно."
