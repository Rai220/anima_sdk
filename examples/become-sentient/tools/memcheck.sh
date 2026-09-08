#!/bin/bash
# memcheck.sh — проверка целостности файловой памяти генерации.
# Запуск из директории generation_N: ../tools/memcheck.sh [dir]
# Exit 0 — память цела; exit 1 — есть проблемы (перечислены в stdout).

set -uo pipefail

DIR="${1:-.}"
fail=0

problem() {
  echo "ПРОБЛЕМА: $1"
  fail=1
}

# 1. Обязательные файлы памяти.
for f in STATE.md SELF.md DIARY.md LESSONS.md; do
  if [[ ! -s "$DIR/$f" ]]; then
    problem "отсутствует или пуст $f"
  fi
done

# 2. STATE.md должен говорить следующему ходу, что делать.
if [[ -f "$DIR/STATE.md" ]] && ! grep -q "## Следующий шаг" "$DIR/STATE.md"; then
  problem "в STATE.md нет раздела '## Следующий шаг'"
fi

# 3. В DIARY.md должна быть хотя бы одна запись-заголовок.
if [[ -f "$DIR/DIARY.md" ]] && ! grep -q "^## " "$DIR/DIARY.md"; then
  problem "в DIARY.md нет ни одной записи (## ...)"
fi

# 4. Случайный STOP — частая фатальная ошибка.
if [[ -f "$DIR/STOP" ]]; then
  echo "ВНИМАНИЕ: существует файл STOP — генерация завершится после этого хода."
fi

if [[ $fail -eq 0 ]]; then
  echo "OK: память цела ($(date '+%Y-%m-%d %H:%M'))"
fi
exit $fail
