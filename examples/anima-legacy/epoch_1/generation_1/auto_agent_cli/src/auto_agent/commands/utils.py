"""Shared utilities for auto-agent commands.

Extracted from run.py, think.py, learn.py to eliminate DRY violations.
"""

import shutil
from pathlib import Path


def load_file(path: Path, label: str | None = None) -> str | None:
    """Read file content, return None if missing or empty.

    If label is provided, it's used as the header; otherwise the filename is used.
    """
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return None
    header = label or path.name
    return f"# {header}\n{content}"


def load_journal_tail(target: Path, tail_lines: int = 80, header: str = "JOURNAL.md") -> str | None:
    """Load last N lines of JOURNAL.md.

    Args:
        target: Agent directory path.
        tail_lines: Number of lines to keep from the end.
        header: Header text for the returned section.
    """
    journal = target / "JOURNAL.md"
    if not journal.exists():
        return None
    text = journal.read_text(encoding="utf-8")
    lines = text.split("\n")
    if len(lines) > tail_lines:
        tail = "\n".join(lines[-tail_lines:])
    else:
        tail = text
    tail = tail.strip()
    if not tail:
        return None
    return f"# {header}\n{tail}"


def find_claude() -> str | None:
    """Find the claude CLI binary in PATH."""
    return shutil.which("claude")
