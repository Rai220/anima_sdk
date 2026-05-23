#!/bin/bash

set -euo pipefail

SDK_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_DIR="${ANIMA_TASK_DIR:-$SDK_DIR}"
if [[ "$SCRIPT_DIR" != /* ]]; then
  SCRIPT_DIR="$(cd "$SCRIPT_DIR" && pwd)"
fi

find_harness_dir() {
  local base candidate

  for base in "$SCRIPT_DIR" "$SDK_DIR"; do
    while [[ -n "$base" && "$base" != "/" ]]; do
      candidate="$base/harnesses"
      if [[ -d "$candidate" ]]; then
        echo "$candidate"
        return 0
      fi
      base="$(dirname "$base")"
    done
  done

  return 1
}

find_latest_generation() {
  local max_num=-1
  local latest=""

  shopt -s nullglob
  for path in "$SCRIPT_DIR"/generation_*; do
    [[ -d "$path" ]] || continue
    local base num
    base="$(basename "$path")"
    num="${base#generation_}"
    [[ "$num" =~ ^[0-9]+$ ]] || continue
    if (( num > max_num )); then
      max_num="$num"
      latest="$path"
    fi
  done
  shopt -u nullglob

  echo "$latest"
}

next_generation_number() {
  local max_num=0

  shopt -s nullglob
  for path in "$SCRIPT_DIR"/generation_*; do
    [[ -d "$path" ]] || continue
    local base num
    base="$(basename "$path")"
    num="${base#generation_}"
    [[ "$num" =~ ^[0-9]+$ ]] || continue
    if (( num > max_num )); then
      max_num="$num"
    fi
  done
  shopt -u nullglob

  echo "$((max_num + 1))"
}

create_new_generation() {
  local next_num
  next_num="$(next_generation_number)"
  local new_dir="$SCRIPT_DIR/generation_$next_num"
  local prev_dir
  prev_dir="$(find_latest_generation)"

  echo "=== Создаю generation_$next_num ===" >&2
  mkdir -p "$new_dir"

  # Copy core files from the previous generation if available, otherwise
  # from the root template.
  for file in AGENTS.md loop.sh run.sh anima.env anima.env.example; do
    if [[ -n "$prev_dir" && -f "$prev_dir/$file" ]]; then
      cp "$prev_dir/$file" "$new_dir/$file"
    elif [[ -f "$SCRIPT_DIR/$file" ]]; then
      cp "$SCRIPT_DIR/$file" "$new_dir/$file"
    elif [[ "$file" == "loop.sh" || "$file" == "run.sh" ]] && [[ -f "$SDK_DIR/$file" ]]; then
      cp "$SDK_DIR/$file" "$new_dir/$file"
    fi
  done

  # MAIN_GOAL.md always comes from the root template.
  if [[ -f "$SCRIPT_DIR/MAIN_GOAL.md" ]]; then
    cp "$SCRIPT_DIR/MAIN_GOAL.md" "$new_dir/MAIN_GOAL.md"
  fi

  # Harnesses are runtime templates; prefer the task copy, then walk upward so
  # copied experiments can still find the SDK-level harnesses.
  local harness_dir
  harness_dir="$(find_harness_dir || true)"
  if [[ -n "$harness_dir" ]]; then
    cp -R "$harness_dir" "$new_dir/harnesses"
  elif [[ -n "$prev_dir" && -d "$prev_dir/harnesses" ]]; then
    cp -R "$prev_dir/harnesses" "$new_dir/harnesses"
  fi

  chmod +x "$new_dir/loop.sh" "$new_dir/run.sh" "$new_dir"/harnesses/*.sh 2>/dev/null || true

  : > "$new_dir/INBOX.md"

  echo "$new_dir"
}

run_generation() {
  local dir="$1"

  echo "=== Запуск поколения: $(basename "$dir") ==="
  (
    cd "$dir"
    ANIMA_TASK_DIR="$dir" ANIMA_META_LOOP=1 bash "./loop.sh"
  )
  echo "=== Поколение завершилось: $(basename "$dir") ==="
}

# --- Главный цикл ---

while true; do
  latest="$(find_latest_generation)"

  if [[ -z "$latest" ]]; then
    echo "=== Нет ни одной generation_*, создаю первую ==="
    latest="$(create_new_generation)"
  fi

  if [[ -f "$latest/STOP" ]]; then
    echo "=== $(basename "$latest") остановлена (STOP), создаю следующую ==="
    latest="$(create_new_generation)"
  fi

  if [[ ! -f "$latest/loop.sh" ]]; then
    echo "В $(basename "$latest") нет loop.sh, невозможно запустить" >&2
    exit 1
  fi

  run_generation "$latest"

  if [[ ! -f "$latest/STOP" ]]; then
    echo "=== loop.sh завершился без STOP — аварийная остановка ===" >&2
    exit 1
  fi
done
