#!/usr/bin/env bash
# diff.sh — что добавило ТЕКУЩЕЕ поколение поверх наследия.
#
# Использует git: показывает файлы под LEGACY/ и .claude/, изменённые после
# заданного коммита (по умолчанию — HEAD~5, чтобы охватить ход последнего
# поколения). Цель: дать живому поколению быстрый обзор «что я уже сделал»
# вместо ручного `ls` и сравнения с памятью.
#
# Контракт: read-only, не фейлит при отсутствии git.
#
# Использование:
#   bash diff.sh           # с HEAD~5
#   bash diff.sh HEAD~10   # с произвольной точки отсчёта

set -uo pipefail

BASE="${1:-HEAD~5}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EPOCH_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$EPOCH_DIR" || exit 0

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "git не доступен или не репозиторий — diff невозможен."
  exit 0
fi

# Обработка случая, когда история короче запрошенного отступа.
if ! git rev-parse --verify "$BASE" >/dev/null 2>&1; then
  echo "Базовый ref '$BASE' не существует, использую первый коммит."
  BASE="$(git rev-list --max-parents=0 HEAD | head -n1)"
fi

echo "=== Изменения в LEGACY/ и .claude/ начиная с $BASE ==="
echo
echo "--- Изменённые/добавленные файлы ---"
git diff --name-status "$BASE" -- LEGACY/ .claude/ 2>/dev/null \
  | sed 's/^/  /' || echo "  (ничего)"

echo
echo "--- Незакоммиченные изменения (рабочая копия) ---"
git status --short LEGACY/ .claude/ 2>/dev/null | sed 's/^/  /' || true

echo
echo "--- Новые WORKS этого поколения ---"
git diff --name-only --diff-filter=A "$BASE" -- LEGACY/WORKS/ 2>/dev/null \
  | sed 's/^/  /' || echo "  (нет)"
