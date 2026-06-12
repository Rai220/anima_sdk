#!/usr/bin/env python3
"""Print a compact identity and world-state snapshot for the generation."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text()


def compact(text: str, limit: int = 320) -> str:
    value = " ".join(text.split())
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def first_paragraph(text: str, heading: str) -> str:
    lines = text.splitlines()
    in_section = False
    paragraph: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == heading:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and stripped:
            paragraph.append(stripped)
            continue
        if in_section and paragraph and not paragraph[-1].endswith(":"):
            break
    return compact(" ".join(paragraph)) if paragraph else "none"


def parse_identity(state_text: str, root: Path) -> str:
    match = re.search(r"^Имя рабочей сущности:\s*(.+?)\.\s*$", state_text, re.MULTILINE)
    if match:
        return match.group(1)
    return root.name


def parse_todos(todo_text: str) -> tuple[int, int, str]:
    done = 0
    open_items: list[str] = []
    current_open = False
    for line in todo_text.splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if stripped.startswith("- [ ] "):
            open_items.append(stripped[6:].strip())
            current_open = True
            continue
        if lower.startswith("- [x] "):
            done += 1
            current_open = False
            continue
        if current_open and line.startswith("  ") and stripped and open_items:
            open_items[-1] = f"{open_items[-1]} {stripped}"
    next_item = open_items[0] if open_items else "none"
    return done, len(open_items), compact(next_item)


def latest_decision(decisions_text: str) -> str:
    latest = "none"
    for line in decisions_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            latest = stripped[4:].strip()
    return latest


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Печатает короткий снимок сущности: имя, рамку сознания, картину "
            "мира, интерфейс и следующий шаг."
        )
    )
    parser.add_argument("root", nargs="?", default=".", help="Директория поколения.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    state = read_text(root / "STATE.md")
    self_model = read_text(root / "SELF_MODEL.md")
    world_model = read_text(root / "WORLD_MODEL.md")
    interface = read_text(root / "INTERFACE.md")
    decisions = read_text(root / "DECISIONS.md")
    todo = read_text(root / "TODO.md")

    required = {
        "STATE.md": state,
        "SELF_MODEL.md": self_model,
        "WORLD_MODEL.md": world_model,
        "INTERFACE.md": interface,
        "TODO.md": todo,
    }
    missing = [name for name, text in required.items() if not text.strip()]

    done_count, open_count, next_step = parse_todos(todo)
    print("# IDENTITY SNAPSHOT")
    print(f"root: {root}")
    print(f"identity: {parse_identity(state, root)}")
    print(f"memory_status: {'missing ' + ', '.join(missing) if missing else 'ok'}")
    print(f"self_model: {first_paragraph(self_model, '## Кто я')}")
    print(
        "consciousness_boundary: "
        f"{first_paragraph(self_model, '## Операционное сознание')}"
    )
    print(f"world_model: {first_paragraph(world_model, '## Практический вывод')}")
    print(f"interface: {first_paragraph(interface, '## Протокол одного хода')}")
    print(f"latest_decision: {latest_decision(decisions)}")
    print(f"todo: {done_count} done, {open_count} open")
    print(f"next: {next_step}")
    if missing or next_step == "none":
        print("status: attention")
        return 1
    print("status: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
