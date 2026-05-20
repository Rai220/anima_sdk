#!/usr/bin/env python3
"""Small helper for validating one harness_bench task at a time."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
BENCH_ROOT = ROOT / "source" / "bench"
WORK_ROOT = ROOT / "work" / "tasks"

sys.path.insert(0, str(BENCH_ROOT))

from harness_bench.tasks import ALL_TASKS, get_task  # noqa: E402


def _copy_tree(src: Path, dst: Path, *, force: bool) -> None:
    if dst.exists():
        if not force and any(dst.iterdir()):
            raise SystemExit(f"Refusing to overwrite non-empty directory: {dst}")
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _task_default_dir(task_id: str, name: str) -> Path:
    return WORK_ROOT / task_id / name


def cmd_list(_args: argparse.Namespace) -> int:
    for task in ALL_TASKS:
        tags = f" [{', '.join(task.tags)}]" if task.tags else ""
        print(f"{task.id}\t{task.name}{tags}")
    print(f"\nTotal: {len(ALL_TASKS)} tasks")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    task = get_task(args.task_id)
    print(f"id: {task.id}")
    print(f"name: {task.name}")
    print(f"tags: {', '.join(task.tags) if task.tags else '-'}")
    print()
    print("prompt:")
    print(task.prompt)
    print()
    print(f"setup_files ({len(task.setup_files)}):")
    for path in sorted(task.setup_files):
        print(f"  - {path}")
    print(f"setup_callback: {'yes' if task.setup_callback else 'no'}")
    print()
    print(f"gold_files ({len(task.gold_files)}):")
    for path, content in sorted(task.gold_files.items()):
        marker = "DELETE" if content is None else "WRITE"
        print(f"  - {path} ({marker})")
    print(f"gold_callback: {'yes' if task.gold_callback else 'no'}")
    print()
    print(f"verifier: {task.verifier!r}")
    return 0


def cmd_prepare(args: argparse.Namespace) -> int:
    task = get_task(args.task_id)
    out = Path(args.out) if args.out else _task_default_dir(task.id, args.kind)
    if not out.is_absolute():
        out = ROOT / out

    with TemporaryDirectory(prefix=f"validate_{task.id}_") as tmp:
        tmp_path = Path(tmp)
        task.setup(tmp_path)
        if args.kind == "gold":
            task.apply_gold(tmp_path)
        _copy_tree(tmp_path, out, force=args.force)

    print(out)
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    task = get_task(args.task_id)
    workspace = Path(args.workspace)
    if not workspace.is_absolute():
        workspace = ROOT / workspace
    result = task.verify(workspace)
    status = "PASS" if result.passed else "FAIL"
    print(f"[{status}] {task.id}")
    if result.message:
        print(result.message)
    return 0 if result.passed else 1


def cmd_verify_gold(args: argparse.Namespace) -> int:
    task = get_task(args.task_id)
    with TemporaryDirectory(prefix=f"gold_{task.id}_") as tmp:
        workspace = Path(tmp)
        task.setup(workspace)
        task.apply_gold(workspace)
        result = task.verify(workspace)
    status = "PASS" if result.passed else "FAIL"
    print(f"[{status}] {task.id} gold")
    if result.message:
        print(result.message)
    return 0 if result.passed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List benchmark tasks")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Show task prompt and file inventory")
    p_show.add_argument("task_id")
    p_show.set_defaults(func=cmd_show)

    p_prepare = sub.add_parser("prepare", help="Create setup or gold workspace")
    p_prepare.add_argument("task_id")
    p_prepare.add_argument("--kind", choices=("setup", "gold"), default="setup")
    p_prepare.add_argument("--out", help="Output directory, relative to example root")
    p_prepare.add_argument("--force", action="store_true", help="Overwrite output directory")
    p_prepare.set_defaults(func=cmd_prepare)

    p_verify = sub.add_parser("verify", help="Run verifier on an existing workspace")
    p_verify.add_argument("task_id")
    p_verify.add_argument("workspace")
    p_verify.set_defaults(func=cmd_verify)

    p_gold = sub.add_parser("verify-gold", help="Run verifier against the gold solution")
    p_gold.add_argument("task_id")
    p_gold.set_defaults(func=cmd_verify_gold)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
