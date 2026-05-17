"""auto-agent archive — progressive memory management.

Implements Letta/MemGPT-inspired memory hierarchy:
- Core memory (MEMORY.md): always in context — facts, principles, recent N runs
- Archive memory (MEMORY_ARCHIVE.md): older runs, accessible on demand

This prevents context overflow as the agent accumulates more run entries.
"""

import re
from datetime import datetime
from pathlib import Path

import click


# Default: keep last N run entries in core memory
DEFAULT_KEEP_RUNS = 10

# Section markers in MEMORY.md
FACTS_HEADER = "## Факты обо мне"
RUNS_HEADER = "## История запусков"
PRINCIPLES_HEADER = "## Принципы, которые я выработал"
RUN_PATTERN = re.compile(r"^### Запуск (\d+)")


def _parse_memory(content: str) -> dict:
    """Parse MEMORY.md into structured sections.

    Handles the case where Principles section may appear between runs
    (e.g., between run 24 and run 25), not just at the end.

    Returns dict with keys:
      - 'preamble': text before runs section (title, facts)
      - 'runs': list of (run_number: int, run_text: str)
      - 'principles': principles section text (wherever it appears)
      - 'raw': original text
    """
    lines = content.split("\n")
    preamble_lines: list[str] = []
    runs: list[tuple[int, str]] = []
    principles_lines: list[str] = []

    # States: preamble -> body (runs + principles interleaved)
    state = "preamble"
    in_principles = False
    current_run_num = 0
    current_run_lines: list[str] = []

    for line in lines:
        if state == "preamble":
            preamble_lines.append(line)
            if line.strip() == RUNS_HEADER:
                state = "body"
            continue

        # In body: detect run headers, principles header, or content
        run_match = RUN_PATTERN.match(line)

        if run_match:
            # Save previous run if any
            if current_run_lines:
                runs.append((current_run_num, "\n".join(current_run_lines)))
            in_principles = False
            current_run_num = int(run_match.group(1))
            current_run_lines = [line]

        elif line.strip().startswith(PRINCIPLES_HEADER):
            # Save current run if any
            if current_run_lines:
                runs.append((current_run_num, "\n".join(current_run_lines)))
                current_run_lines = []
            in_principles = True
            principles_lines.append(line)

        elif in_principles:
            # Check if we're still in principles or a new run started
            principles_lines.append(line)

        elif current_run_lines:
            current_run_lines.append(line)
        # else: blank lines between sections — skip

    # Save last run
    if current_run_lines:
        runs.append((current_run_num, "\n".join(current_run_lines)))

    return {
        "preamble": "\n".join(preamble_lines),
        "runs": runs,
        "principles": "\n".join(principles_lines),
        "raw": content,
    }


def _build_core_memory(parsed: dict, keep_runs: int) -> str:
    """Rebuild MEMORY.md with only the last N runs."""
    parts = [parsed["preamble"]]

    # Add only recent runs
    recent_runs = parsed["runs"][-keep_runs:] if len(parsed["runs"]) > keep_runs else parsed["runs"]
    archived_count = len(parsed["runs"]) - len(recent_runs)

    # Add archive notice if runs were archived
    if archived_count > 0:
        first_archived = parsed["runs"][0][0]
        last_archived = parsed["runs"][-keep_runs - 1][0] if len(parsed["runs"]) > keep_runs else 0
        parts.append("")
        parts.append(f"> 📦 Запуски {first_archived}–{last_archived} перенесены в MEMORY_ARCHIVE.md ({archived_count} записей)")
        parts.append("")

    for _, run_text in recent_runs:
        parts.append("")
        parts.append(run_text)

    # Add principles
    if parsed["principles"].strip():
        parts.append("")
        parts.append(parsed["principles"])

    return "\n".join(parts)


def _build_archive(parsed: dict, keep_runs: int, existing_archive: str | None = None) -> str:
    """Build or update MEMORY_ARCHIVE.md with older runs.

    If existing_archive is provided, new runs are appended to it
    (preserving previously archived entries).
    """
    archived_runs = parsed["runs"][:-keep_runs] if len(parsed["runs"]) > keep_runs else []

    if not archived_runs:
        return existing_archive or ""

    # New run entries to add
    new_run_texts = []
    for _, run_text in archived_runs:
        new_run_texts.append(f"\n{run_text}")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_footer = (
        f"\n\n---\n\n"
        f"*Архивировано: {now}. "
        f"Записей: {len(archived_runs)} "
        f"(запуски {archived_runs[0][0]}–{archived_runs[-1][0]})*\n"
    )

    if existing_archive and existing_archive.strip():
        # Append new runs to existing archive
        return existing_archive.rstrip() + "\n" + "\n".join(new_run_texts) + new_footer

    # Create fresh archive
    header = (
        "# Архив памяти (MEMORY_ARCHIVE.md)\n\n"
        "Старые записи, перенесённые из MEMORY.md для экономии контекста.\n"
        "Эти записи не загружаются автоматически, но доступны для чтения.\n\n"
        "---\n"
    )

    return header + "\n".join(new_run_texts) + new_footer


def archive_memory(directory: str, keep_runs: int = DEFAULT_KEEP_RUNS, dry_run: bool = False) -> dict:
    """Archive old MEMORY.md entries.

    Returns dict with:
      - 'archived_count': number of runs moved to archive
      - 'kept_count': number of runs remaining in core
      - 'total_runs': total runs found
      - 'already_optimal': True if nothing to archive
    """
    target = Path(directory).resolve()
    memory_path = target / "MEMORY.md"
    archive_path = target / "MEMORY_ARCHIVE.md"

    if not memory_path.exists():
        return {"error": "MEMORY.md not found", "archived_count": 0, "kept_count": 0, "total_runs": 0}

    content = memory_path.read_text(encoding="utf-8")
    parsed = _parse_memory(content)
    total_runs = len(parsed["runs"])

    if total_runs <= keep_runs:
        return {
            "archived_count": 0,
            "kept_count": total_runs,
            "total_runs": total_runs,
            "already_optimal": True,
        }

    archived_count = total_runs - keep_runs

    # Build new files
    core = _build_core_memory(parsed, keep_runs)
    existing_archive = archive_path.read_text(encoding="utf-8") if archive_path.exists() else None
    archive = _build_archive(parsed, keep_runs, existing_archive)

    if not dry_run:
        memory_path.write_text(core, encoding="utf-8")
        archive_path.write_text(archive, encoding="utf-8")

    return {
        "archived_count": archived_count,
        "kept_count": keep_runs,
        "total_runs": total_runs,
        "already_optimal": False,
        "core_size": len(core),
        "archive_size": len(archive),
    }


def show_archive_plan(directory: str, keep_runs: int = DEFAULT_KEEP_RUNS) -> None:
    """Show what would be archived without making changes."""
    target = Path(directory).resolve()
    memory_path = target / "MEMORY.md"

    if not memory_path.exists():
        click.echo(click.style("Error: ", fg="red") + f"No MEMORY.md in {target}")
        raise SystemExit(1)

    content = memory_path.read_text(encoding="utf-8")
    parsed = _parse_memory(content)
    total = len(parsed["runs"])

    click.echo(click.style("📋 Archive plan (dry-run)", fg="cyan", bold=True))
    click.echo(f"  Directory : {target}")
    click.echo(f"  Total runs: {total}")
    click.echo(f"  Keep last : {keep_runs}")
    click.echo()

    if total <= keep_runs:
        click.echo(click.style("  ✓ Nothing to archive", fg="green") + f" — only {total} runs, threshold is {keep_runs}")
        return

    to_archive = total - keep_runs
    archived_runs = parsed["runs"][:to_archive]
    kept_runs = parsed["runs"][to_archive:]

    click.echo(f"  {click.style('Archive:', fg='yellow')} {to_archive} runs → MEMORY_ARCHIVE.md")
    for num, _ in archived_runs:
        click.echo(f"    → Запуск {num}")

    click.echo(f"\n  {click.style('Keep:', fg='green')} {keep_runs} runs in MEMORY.md")
    for num, _ in kept_runs:
        click.echo(f"    ✓ Запуск {num}")

    click.echo()
    click.echo("  Run without --dry-run to execute.")


def run_archive(directory: str, keep_runs: int = DEFAULT_KEEP_RUNS) -> None:
    """Archive old memory entries."""
    target = Path(directory).resolve()

    click.echo(click.style("📦 Auto Agent — Archive Memory", fg="cyan", bold=True))
    click.echo(f"  Directory : {target}")
    click.echo(f"  Keep last : {keep_runs} runs")
    click.echo()

    result = archive_memory(directory, keep_runs)

    if result.get("error"):
        click.echo(click.style("Error: ", fg="red") + result["error"])
        raise SystemExit(1)

    if result.get("already_optimal"):
        click.echo(
            click.style("✓ ", fg="green")
            + f"Nothing to archive — only {result['total_runs']} runs "
            + f"(threshold: {keep_runs})"
        )
        return

    click.echo(click.style("✓ ", fg="green", bold=True) + "Memory archived!")
    click.echo(f"  Archived  : {result['archived_count']} runs → MEMORY_ARCHIVE.md")
    click.echo(f"  Kept      : {result['kept_count']} runs in MEMORY.md")
    click.echo(f"  Core size : {result['core_size']:,} chars")
    click.echo(f"  Archive   : {result['archive_size']:,} chars")
