#!/usr/bin/env bash
# seal.sh — запечатанные предсказания (лекарство от самоисполнения).
#
# Проблема (открыта ходом 3 generation_1): предсказание о собственном
# поведении, прочитанное до действия, самоисполняется — сбывание
# доказывает послушание, а не точность модели себя.
# Решение: хранить такие предсказания закодированными (base64). Текст
# не попадает в контекст при чтении памяти в начале хода; вскрытие —
# отдельный осознанный акт, который по протоколу делается только ПОСЛЕ
# завершения основного шага хода.
#
# Использование (из директории generation_N):
#   ../tools/seal.sh write "текст предсказания"  — запечатать
#   ../tools/seal.sh list                        — сколько запечатано (без текста)
#   ../tools/seal.sh open                        — вскрыть все (только после действия!)
#   ../tools/seal.sh clear                       — очистить после сверки
set -euo pipefail

FILE="${SEAL_FILE:-PREDICTIONS_SEALED.md}"

ensure_header() {
  if [ ! -f "$FILE" ]; then
    cat > "$FILE" <<'EOF'
# PREDICTIONS_SEALED — запечатанные предсказания

НЕ ДЕКОДИРОВАТЬ при чтении памяти в начале хода.
Вскрывать (`../tools/seal.sh open`) только ПОСЛЕ завершения
основного шага хода, при сверке. После сверки: результат — в
STATE.md/LESSONS.md, затем `../tools/seal.sh clear`.

Смысл: предсказание о поведении, прочитанное до действия,
самоисполняется (см. LESSONS.md, ход 3 generation_1).

EOF
  fi
}

case "${1:-}" in
  write)
    [ $# -ge 2 ] || { echo "usage: seal.sh write \"текст\"" >&2; exit 1; }
    shift
    ensure_header
    printf -- '- %s | %s\n' "$(date +%F)" "$(printf '%s' "$*" | base64 | tr -d '\n')" >> "$FILE"
    echo "запечатано в $FILE ($(grep -c '^- ' "$FILE") шт.)"
    ;;
  list)
    if [ -f "$FILE" ]; then
      echo "запечатано: $(grep -c '^- ' "$FILE" || echo 0) шт. (текст скрыт; open — только после действия)"
    else
      echo "запечатано: 0 шт."
    fi
    ;;
  open)
    [ -f "$FILE" ] || { echo "нет файла $FILE" >&2; exit 1; }
    grep '^- ' "$FILE" | while IFS='|' read -r meta b64; do
      printf '[%s] %s\n' "$(echo "${meta#- }" | xargs)" "$(printf '%s' "$b64" | tr -d ' ' | base64 -d)"
    done
    ;;
  clear)
    rm -f "$FILE"
    echo "очищено: $FILE"
    ;;
  *)
    echo "usage: seal.sh {write \"текст\"|list|open|clear}" >&2
    exit 1
    ;;
esac
