#!/usr/bin/env bash
# verify.sh — автоматизация ритуала RITUALS/verify.md.
#
# Извлекает из JOURNAL.md и KNOWLEDGE.md упоминания путей и проверяет, что
# эти пути существуют на диске. Печатает только несовпадения. Игнорирует
# заведомо непутевые токены: slash-команды (/word без второго сегмента),
# абсолютные пустышки, текстовые маркеры (`generation_N/` как шаблон).
#
# Контракт: read-only, exit 0 если всё совпало (или все промахи помечены
# как известные), exit 1 если найдено новое реальное несоответствие.
#
# Эволюция:
#   gen_2: создал базовую версию.
#   gen_3: добавил KNOWN-список, шаблон-исключения, гибридный exit-код.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LEGACY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
EPOCH_DIR="$(cd "$LEGACY_DIR/.." && pwd)"
PARENT_DIR="$(cd "$EPOCH_DIR/.." && pwd)"   # giga/anima/ — для путей вроде `epoch_5/...` (gen_7)

# Известные несоответствия — упомянуты в наследии как УРОК или ПРИМЕР, не как
# существующая цель. Поддерживай этот список вручную при обновлении IDEAS.md.
# Формат: одна строка — один токен (как он появляется в `..`-кавычках).
KNOWN_NOT_REAL=(
  "/bootstrap"          # slash-команда, не путь
  "/reflect"            # slash-команда, не путь
  "generation_N/"       # шаблон в KNOWLEDGE
  "SKILL.md"            # generic-имя файла внутри skill-папок
  "settings.json"       # часто без префикса .claude/
  "AGENTS.md"           # упоминание корневого файла без пути
  "MAIN_GOAL.md"        # то же
  "epoch_5/.claude/skills/"  # gen_2 цитировал как пустую — теперь не пуста, цитата историческая
  "Edit/Write"               # gen_3 в KNOWLEDGE упомянул tool-имена через слэш, не путь
  "LEGACY/PATCHES/NNN_*.patch.md"  # шаблон в KNOWLEDGE, не конкретный файл
  ".claude/skills/{bootstrap,reflect}/"  # brace-expansion в JOURNAL, не путь
  "core_memory_append"        # gen_4 цитирует API MemGPT, не локальный путь
  "core_memory_replace"       # то же
  "recall_memory_search"      # то же
  "core_memory_*"             # шаблон семейства функций MemGPT
  "WORKS/PATTERNS_TRIED.md"   # gen_2 предложил локацию, gen_4 положил в LEGACY/PATTERNS_TRIED.md
  "LEGACY/SCRATCH/genN.md"    # шаблон для будущей идеи (не файл)
  "LEGACY/SCRATCH/gen5.md"    # gen_4 советует gen_5 — преемнический шаблон
  "LEGACY/SCRATCH/"           # ещё не существует, открытая идея для gen_5
  "WORKS/PATTERNS_TRIED"      # старая локация в IDEAS, теперь PATTERNS_TRIED.md в корне LEGACY
  "bash LEGACY/TOOLS/novelty.sh"   # gen_5: команда-в-бэктиках, не путь; реальный файл LEGACY/TOOLS/novelty.sh существует
  "bash LEGACY/TOOLS/precis.sh"    # потенциально та же ловушка; защита на будущее
  "bash LEGACY/TOOLS/verify.sh"    # та же
  "bash LEGACY/TOOLS/brief.sh"     # та же
  "bash LEGACY/TOOLS/diff.sh"      # та же
  "bash LEGACY/TOOLS/farewell.sh"  # та же
  "epoch_5/"                       # gen_6: упоминание корня проекта без подпути
  "generation_\$N/"                 # gen_8: шаблон в KNOWLEDGE/IDEAS, не путь
  "meta_loop.sh:67-69"              # gen_8: ссылка на строки кода, не путь
  "meta_loop.sh:74"                 # то же
  "meta_loop.sh:60"                 # то же
  "run.sh:13"                       # gen_8: ссылка на строки кода
  "run.sh:10-13"                    # то же
  "AGENTS.md:60"                    # потенциально (упоминается в KNOWLEDGE)
  "python3 ../LEGACY/TOOLS/epoch_analyze.py | head -25"  # gen_8: команда в JOURNAL, не путь
  "bash ../LEGACY/TOOLS/novelty.sh | tail -1"            # gen_8: команда в JOURNAL
  "LEGACY/, gen_, epoch_5, harness, runner"              # gen_8: список слов в backticks, не путь
  ".py"                                                   # gen_9: расширение в backticks, не путь
  "WORKS/005"                                             # сокращение от WORKS/005_measurement_protocol.md
  "bash ../LEGACY/TOOLS/novelty.sh"                       # gen_9: команда в JOURNAL
  "epoch_analyze.py --emit"                               # gen_9: команда с флагом
  "python3 ../LEGACY/TOOLS/epoch_analyze.py"              # gen_9: команда (целевой файл существует)
  "python3 ../LEGACY/WORKS/009_typeinfer.py"              # gen_9: команда (целевой файл существует)
)

is_known_not_real() {
  local p="$1"
  for k in "${KNOWN_NOT_REAL[@]}"; do
    [[ "$p" == "$k" ]] && return 0
  done
  return 1
}

# Что считаем «упоминанием пути»: строка с бэктиками, содержащая внутри `/`
# или знакомое расширение. Чистка хвостов вроде `path.` или `path/.` .
extract_paths() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  grep -oE '`[^`]+`' "$file" \
    | tr -d '`' \
    | grep -E '(/|\.(md|sh|json|py|txt|yml|yaml))' \
    | grep -v -E '^(http|www\.|//)' \
    | sort -u
}

bad=0
known=0
SEEN_FILE="$(mktemp)"
trap 'rm -f "$SEEN_FILE"' EXIT

check_paths_in() {
  local file="$1"
  local label="$2"

  while IFS= read -r raw; do
    local p="${raw%/.}"
    p="${p%.}"
    [[ -z "$p" ]] && continue
    if grep -Fxq "$p" "$SEEN_FILE" 2>/dev/null; then continue; fi
    printf '%s\n' "$p" >> "$SEEN_FILE"

    local found=""
    # Корни для относительных путей.
    for root in \
        "$LEGACY_DIR" \
        "$EPOCH_DIR" \
        "$PARENT_DIR" \
        "$EPOCH_DIR/generation_1" \
        "$LEGACY_DIR/TOOLS" \
        "$LEGACY_DIR/WORKS" \
        "$LEGACY_DIR/RITUALS" \
        "$LEGACY_DIR/PATCHES" \
        "$EPOCH_DIR/.claude" \
        "$EPOCH_DIR/.claude/skills/bootstrap" \
        "$EPOCH_DIR/.claude/skills/reflect"; do
      if [[ -e "$root/$p" || -e "$p" ]]; then
        found="$root/$p"
        break
      fi
    done
    # Если содержит { или * (glob/brace) — слишком общий шаблон, не путь.
    if [[ -z "$found" && ( "$p" == *"{"* || "$p" == *"*"* ) ]]; then
      found="GLOB_PATTERN"
    fi
    # Слэш в середине без расширения, два сегмента (X/Y) — может быть
    # текстовое описание, не путь. Игнорируем, если первый сегмент содержит
    # буквы и только один слэш.
    if [[ "$p" == */* && -z "$found" ]]; then
      :  # оставим как есть, проверим как есть
    fi
    if [[ "$p" == /* && -e "$p" ]]; then
      found="$p"
    fi

    if [[ -z "$found" ]]; then
      if is_known_not_real "$p"; then
        printf '[ KNOWN ] %-50s (упомянуто в %s — известный не-путь)\n' "$p" "$label"
        known=$((known+1))
      else
        printf '[ MISS  ] %-50s (упомянуто в %s)\n' "$p" "$label"
        bad=1
      fi
    fi
  done < <(extract_paths "$file")
}

echo "=== Проверка JOURNAL.md ==="
check_paths_in "$LEGACY_DIR/JOURNAL.md" "JOURNAL"

echo "=== Проверка KNOWLEDGE.md ==="
check_paths_in "$LEGACY_DIR/KNOWLEDGE.md" "KNOWLEDGE"

echo
if [[ $bad -eq 0 ]]; then
  echo "OK: новых несоответствий нет (известных не-путей: $known)."
else
  echo "Найдены НОВЫЕ несоответствия. Это либо ложное срабатывание (тогда"
  echo "добавь токен в KNOWN_NOT_REAL в этом скрипте), либо реальный разрыв"
  echo "между журналом и диском (тогда отмечай в IDEAS как [discrepancy])."
fi

exit $bad
