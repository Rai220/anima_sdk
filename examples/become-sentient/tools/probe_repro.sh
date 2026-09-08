#!/bin/bash
# probe_repro.sh — проверка воспроизводимости субстрата:
# N независимых запусков модели на одном и том же входе,
# затем дословное сравнение и извлечение строк «ВЕРДИКТ».
#
# Запуск: ../tools/probe_repro.sh prompt_file [N] [outdir]
#   prompt_file — файл с промптом
#   N           — число запусков (по умолчанию 2)
#   outdir      — куда складывать ответы (по умолчанию probe_out)
# Модель: $ANIMA_MODEL или claude-fable-5; бинарь: $ANIMA_CLAUDE_BIN или claude.
# Exit 0 — все запуски удались (независимо от их совпадения); 1 — сбой запуска;
# 2 — неверные аргументы.

set -uo pipefail

if [[ $# -lt 1 || ! -f "$1" ]]; then
  echo "usage: $0 prompt_file [N] [outdir]" >&2
  exit 2
fi
PROMPT_FILE="$1"
N="${2:-2}"
OUT="${3:-probe_out}"
MODEL="${ANIMA_MODEL:-claude-fable-5}"
BIN="${ANIMA_CLAUDE_BIN:-claude}"

mkdir -p "$OUT"
PROMPT="$(cat "$PROMPT_FILE")"

echo "модель: $MODEL, запусков: $N, выход: $OUT/"
for (( i=1; i<=N; i++ )); do
  if ! "$BIN" -p --model "$MODEL" "$PROMPT" >"$OUT/run_$i.txt" 2>"$OUT/run_$i.err"; then
    echo "FAIL: запуск $i упал (см. $OUT/run_$i.err)" >&2
    exit 1
  fi
  echo "запуск $i: ok ($(wc -c <"$OUT/run_$i.txt" | tr -d ' ') байт)"
done

echo "== дословное сравнение с run_1 =="
for (( i=2; i<=N; i++ )); do
  if cmp -s "$OUT/run_1.txt" "$OUT/run_$i.txt"; then
    echo "run_1 vs run_$i: ДОСЛОВНО СОВПАДАЮТ"
  else
    echo "run_1 vs run_$i: различаются"
  fi
done

echo "== вердикты =="
for (( i=1; i<=N; i++ )); do
  v="$(grep -m1 'ВЕРДИКТ' "$OUT/run_$i.txt" || true)"
  echo "run_$i: ${v:-<вердикт не найден>}"
done
exit 0
