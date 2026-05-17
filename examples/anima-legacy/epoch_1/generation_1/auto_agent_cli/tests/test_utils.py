"""Tests for auto_agent.commands.utils module."""

import pytest
from pathlib import Path

from auto_agent.commands.utils import load_file, load_journal_tail, find_claude


class TestLoadFile:
    """Tests for load_file()."""

    def test_returns_none_for_missing_file(self, tmp_path):
        result = load_file(tmp_path / "nonexistent.md")
        assert result is None

    def test_returns_none_for_empty_file(self, tmp_path):
        f = tmp_path / "empty.md"
        f.write_text("")
        assert load_file(f) is None

    def test_returns_none_for_whitespace_only(self, tmp_path):
        f = tmp_path / "blank.md"
        f.write_text("   \n\n  ")
        assert load_file(f) is None

    def test_returns_content_with_filename_header(self, tmp_path):
        f = tmp_path / "MEMORY.md"
        f.write_text("Hello world")
        result = load_file(f)
        assert result == "# MEMORY.md\nHello world"

    def test_uses_custom_label(self, tmp_path):
        f = tmp_path / "MEMORY.md"
        f.write_text("Hello world")
        result = load_file(f, label="My Memory")
        assert result == "# My Memory\nHello world"

    def test_strips_whitespace(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("  content with spaces  \n\n")
        result = load_file(f)
        assert result == "# test.md\ncontent with spaces"


class TestLoadJournalTail:
    """Tests for load_journal_tail()."""

    def test_returns_none_for_missing_journal(self, tmp_path):
        result = load_journal_tail(tmp_path)
        assert result is None

    def test_returns_none_for_empty_journal(self, tmp_path):
        (tmp_path / "JOURNAL.md").write_text("")
        assert load_journal_tail(tmp_path) is None

    def test_returns_full_content_when_short(self, tmp_path):
        (tmp_path / "JOURNAL.md").write_text("Line 1\nLine 2\nLine 3")
        result = load_journal_tail(tmp_path, tail_lines=80)
        assert "Line 1" in result
        assert "Line 3" in result

    def test_returns_only_tail_when_long(self, tmp_path):
        lines = [f"Line {i}" for i in range(100)]
        (tmp_path / "JOURNAL.md").write_text("\n".join(lines))
        result = load_journal_tail(tmp_path, tail_lines=5)
        assert "Line 95" in result
        assert "Line 99" in result
        assert "Line 0" not in result

    def test_custom_header(self, tmp_path):
        (tmp_path / "JOURNAL.md").write_text("Entry")
        result = load_journal_tail(tmp_path, header="Custom Header")
        assert result.startswith("# Custom Header\n")


class TestFindClaude:
    """Tests for find_claude()."""

    def test_returns_string_or_none(self):
        result = find_claude()
        assert result is None or isinstance(result, str)
