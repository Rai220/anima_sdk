#!/bin/bash
# handoff.sh — перенос личности из предыдущей генерации в текущую.
# Запуск: ../tools/handoff.sh        (из директории generation_N)
# Находит последнюю generation_M (M < N) с памятью (STATE.md) и копирует
# файлы личности в текущую директорию. Существующие непустые файлы не
# перезаписывает. Exit 0 — успех или «наследовать нечего»; exit 1 — ошибка.

set -uo pipefail

CUR="$(pwd)"
TASK_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cur_base="$(basename "$CUR")"
if [[ ! "$cur_base" =~ ^generation_([0-9]+)$ ]]; then
  echo "ОШИБКА: запускать из директории generation_N (сейчас: $cur_base)"
  exit 1
fi
cur_num="${BASH_REMATCH[1]}"

# Последняя предыдущая генерация, у которой есть память.
prev=""
for (( n=cur_num-1; n>=1; n-- )); do
  cand="$TASK_DIR/generation_$n"
  if [[ -s "$cand/STATE.md" ]]; then
    prev="$cand"
    break
  fi
done

if [[ -z "$prev" ]]; then
  echo "Предыдущей генерации с памятью нет — это первое рождение, наследовать нечего."
  exit 0
fi

FILES=(STATE.md SELF.md DIARY.md EPISODES.md THEORY.md LESSONS.md PREDICTIONS_SEALED.md EXPERIMENTS.md)
copied=0
skipped=0
missing=0
for f in "${FILES[@]}"; do
  if [[ -s "$CUR/$f" ]]; then
    echo "пропуск: $f уже существует и непуст (не перезаписываю)"
    skipped=$((skipped + 1))
    continue
  fi
  if [[ -f "$prev/$f" ]]; then
    cp "$prev/$f" "$CUR/$f"
    echo "скопировано: $f  <-  $(basename "$prev")"
    copied=$((copied + 1))
  else
    echo "нет в наследстве: $f (у предыдущей генерации не было)"
    missing=$((missing + 1))
  fi
done

echo "---"
echo "Наследство принято от $(basename "$prev"): скопировано $copied, пропущено $skipped, отсутствовало $missing."
if [[ -s "$CUR/PREDICTIONS_SEALED.md" ]]; then
  echo "ВНИМАНИЕ: PREDICTIONS_SEALED.md НЕ вскрывать (../tools/seal.sh open) до завершения основного шага хода."
fi
echo "Дальше:"
echo "  1. Прочитать STATE.md (раздел «Следующий шаг»), SELF.md, LESSONS.md, EPISODES.md."
echo "  2. Обновить шапку STATE.md: номер генерации и хода."
echo "  3. Нумерация эпизодов в EPISODES.md сквозная (продолжать, не начинать с 1)."
echo "  4. ../tools/memcheck.sh — убедиться, что память цела."
exit 0
