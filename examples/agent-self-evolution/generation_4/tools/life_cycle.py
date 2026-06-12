#!/usr/bin/env python3
"""Run the local start-of-turn life cycle for a generation."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys


QUICK_STEPS = [
    ("inbox", "inbox_triage.py", False),
    ("pulse", "pulse.py", False),
    ("intent", "next_intent.py", False),
]

FULL_STEPS = [
    ("self_audit", "self_audit.py", False),
    ("memory_consistency", "memory_consistency.py", False),
    ("behavior_review", "behavior_review.py", False),
    ("handoff", "handoff.py", False),
]


COMPACT_PREFIXES = {
    "inbox": (
        "status:",
        "active_items:",
        "urgent:",
        "do_not:",
        "focus:",
        "feedback:",
        "question:",
        "general:",
    ),
    "pulse": (
        "inbox:",
        "memory_missing:",
        "todo:",
        "next:",
        "state_hint:",
        "stop_file:",
        "tool_mismatch:",
        "status:",
    ),
    "intent": ("constraint:", "decision_source:", "next_intent:"),
    "self_audit": ("inbox:", "lessons:", "todo:", "missing:", "next:", "status:"),
    "memory_consistency": ("ok:", "warn:", "error:", "status:"),
}


@dataclass
class StepResult:
    label: str
    script_name: str
    returncode: int
    output: str


def compact_output(label: str, output: str) -> list[str]:
    lines = [line.rstrip() for line in output.splitlines() if line.strip()]

    if label == "behavior_review":
        return [
            line
            for line in lines
            if line.startswith("Итог:")
            or line.startswith("- ")
            or line.startswith("Вывод:")
            or line.startswith("status:")
        ]

    if label == "handoff":
        selected: list[str] = []
        in_next = False
        for line in lines:
            if line.startswith(("done_tasks:", "open_tasks:", "lesson_symptoms:", "status:")):
                selected.append(line)
                continue
            if line == "## Next":
                in_next = True
                continue
            if in_next and line.startswith("## "):
                in_next = False
                continue
            if in_next and line.startswith("- "):
                selected.append(f"next: {line[2:]}")
        return selected

    prefixes = COMPACT_PREFIXES.get(label, ("status:",))
    return [line for line in lines if line.startswith(prefixes)]


def run_step(
    root: Path,
    label: str,
    script_name: str,
    allow_fail: bool,
    verbose: bool,
) -> int:
    script = root / "tools" / script_name
    print(f"## {label}: tools/{script_name}")
    if not script.exists():
        print(f"missing: {script}")
        print()
        return 1 if not allow_fail else 0

    result = subprocess.run(
        [sys.executable, str(script), str(root)],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    step = StepResult(label, script_name, result.returncode, result.stdout.rstrip())
    if verbose:
        print(step.output)
    else:
        lines = compact_output(step.label, step.output)
        if lines:
            print("\n".join(lines))
        elif step.output:
            print(step.output.splitlines()[0])
        if step.returncode:
            print()
            print("failure_output:")
            print(step.output)
    print(f"exit_code: {step.returncode}")
    print()
    if step.returncode and not allow_fail:
        return step.returncode
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Запускает стартовый жизненный цикл поколения: inbox triage, "
            "pulse и выбор следующего намерения. С --full добавляет строгие "
            "проверки памяти и handoff."
        )
    )
    parser.add_argument("root", nargs="?", default=".", help="Директория поколения.")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Добавить self_audit, memory_consistency, behavior_review и handoff.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Печатать полный stdout вложенных инструментов вместо краткой выжимки.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    steps = list(QUICK_STEPS)
    if args.full:
        steps.extend(FULL_STEPS)

    print("# LIFE CYCLE")
    print(f"root: {root}")
    print(f"mode: {'full' if args.full else 'quick'}")
    print()

    failures = 0
    for label, script_name, allow_fail in steps:
        failures += (
            1
            if run_step(root, label, script_name, allow_fail, args.verbose)
            else 0
        )

    if failures:
        print(f"status: fail ({failures} step(s) failed)")
        return 1
    print("status: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
