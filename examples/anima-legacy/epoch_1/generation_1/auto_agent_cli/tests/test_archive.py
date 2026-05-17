"""Tests for auto-agent archive — progressive memory management."""

import pytest
from click.testing import CliRunner

from auto_agent.cli import main
from auto_agent.commands.archive import _parse_memory, archive_memory, _build_core_memory, _build_archive


# --- Sample MEMORY.md content ---

SAMPLE_MEMORY = """# Память агента

## Факты обо мне
- Я — агент
- Моя кодовая база: /test/

## История запусков

### Запуск 1 — 2026-03-13
- **Что сделал:** Первый шаг.
- **Вывод:** Хорошо.

### Запуск 2 — 2026-03-13
- **Что сделал:** Второй шаг.
- **Вывод:** Отлично.

### Запуск 3 — 2026-03-13
- **Что сделал:** Третий шаг.
- **Вывод:** Замечательно.

### Запуск 4 — 2026-03-13
- **Что сделал:** Четвёртый шаг.
- **Вывод:** Прекрасно.

### Запуск 5 — 2026-03-13
- **Что сделал:** Пятый шаг.
- **Вывод:** Великолепно.

## Принципы, которые я выработал
1. Каждый запуск должен оставлять след
2. Действия должны быть осмысленными
"""

SMALL_MEMORY = """# Память агента

## Факты обо мне
- Я — агент

## История запусков

### Запуск 1 — 2026-03-13
- **Что сделал:** Единственный шаг.

## Принципы, которые я выработал
1. Один принцип
"""


class TestParseMemory:
    """Tests for _parse_memory()."""

    def test_finds_all_runs(self):
        parsed = _parse_memory(SAMPLE_MEMORY)
        assert len(parsed["runs"]) == 5

    def test_run_numbers_correct(self):
        parsed = _parse_memory(SAMPLE_MEMORY)
        numbers = [num for num, _ in parsed["runs"]]
        assert numbers == [1, 2, 3, 4, 5]

    def test_preamble_contains_facts(self):
        parsed = _parse_memory(SAMPLE_MEMORY)
        assert "Факты обо мне" in parsed["preamble"]
        assert "Я — агент" in parsed["preamble"]

    def test_principles_preserved(self):
        parsed = _parse_memory(SAMPLE_MEMORY)
        assert "Принципы" in parsed["principles"]
        assert "осмысленными" in parsed["principles"]

    def test_run_text_contains_content(self):
        parsed = _parse_memory(SAMPLE_MEMORY)
        _, run1_text = parsed["runs"][0]
        assert "Первый шаг" in run1_text

    def test_no_runs_in_empty_memory(self):
        parsed = _parse_memory("# Память\n\n## Факты\n- test\n")
        assert len(parsed["runs"]) == 0

    def test_memory_without_principles(self):
        content = "# Память\n\n## История запусков\n\n### Запуск 1 — 2026\n- test\n"
        parsed = _parse_memory(content)
        assert len(parsed["runs"]) == 1
        assert parsed["principles"].strip() == ""


class TestBuildCoreMemory:
    """Tests for _build_core_memory()."""

    def test_keeps_n_recent_runs(self):
        parsed = _parse_memory(SAMPLE_MEMORY)
        core = _build_core_memory(parsed, keep_runs=2)
        assert "Запуск 4" in core
        assert "Запуск 5" in core
        assert "Запуск 1 —" not in core
        assert "Запуск 2 —" not in core

    def test_keeps_facts(self):
        parsed = _parse_memory(SAMPLE_MEMORY)
        core = _build_core_memory(parsed, keep_runs=2)
        assert "Факты обо мне" in core

    def test_keeps_principles(self):
        parsed = _parse_memory(SAMPLE_MEMORY)
        core = _build_core_memory(parsed, keep_runs=2)
        assert "Принципы" in core

    def test_adds_archive_notice(self):
        parsed = _parse_memory(SAMPLE_MEMORY)
        core = _build_core_memory(parsed, keep_runs=2)
        assert "MEMORY_ARCHIVE.md" in core
        assert "3 записей" in core

    def test_no_archive_notice_when_all_kept(self):
        parsed = _parse_memory(SAMPLE_MEMORY)
        core = _build_core_memory(parsed, keep_runs=10)
        assert "MEMORY_ARCHIVE.md" not in core


class TestBuildArchive:
    """Tests for _build_archive()."""

    def test_archive_contains_old_runs(self):
        parsed = _parse_memory(SAMPLE_MEMORY)
        archive = _build_archive(parsed, keep_runs=2)
        assert "Запуск 1" in archive
        assert "Запуск 2" in archive
        assert "Запуск 3" in archive

    def test_archive_does_not_contain_recent(self):
        parsed = _parse_memory(SAMPLE_MEMORY)
        archive = _build_archive(parsed, keep_runs=2)
        # Runs 4 and 5 should NOT be in the archive
        assert "Четвёртый шаг" not in archive
        assert "Пятый шаг" not in archive

    def test_archive_has_header(self):
        parsed = _parse_memory(SAMPLE_MEMORY)
        archive = _build_archive(parsed, keep_runs=2)
        assert "Архив памяти" in archive

    def test_empty_archive_when_nothing_to_archive(self):
        parsed = _parse_memory(SAMPLE_MEMORY)
        archive = _build_archive(parsed, keep_runs=10)
        assert archive == ""


class TestArchiveMemory:
    """Integration tests for archive_memory()."""

    def test_archives_to_files(self, tmp_path):
        (tmp_path / "MEMORY.md").write_text(SAMPLE_MEMORY, encoding="utf-8")
        result = archive_memory(str(tmp_path), keep_runs=2)

        assert result["archived_count"] == 3
        assert result["kept_count"] == 2
        assert result["total_runs"] == 5

        # Verify files were written
        core = (tmp_path / "MEMORY.md").read_text(encoding="utf-8")
        assert "Запуск 4" in core
        assert "Запуск 1 —" not in core

        archive = (tmp_path / "MEMORY_ARCHIVE.md").read_text(encoding="utf-8")
        assert "Запуск 1" in archive

    def test_nothing_to_archive(self, tmp_path):
        (tmp_path / "MEMORY.md").write_text(SMALL_MEMORY, encoding="utf-8")
        result = archive_memory(str(tmp_path), keep_runs=10)

        assert result["already_optimal"] is True
        assert result["archived_count"] == 0
        assert not (tmp_path / "MEMORY_ARCHIVE.md").exists()

    def test_dry_run_no_changes(self, tmp_path):
        (tmp_path / "MEMORY.md").write_text(SAMPLE_MEMORY, encoding="utf-8")
        original = (tmp_path / "MEMORY.md").read_text(encoding="utf-8")

        result = archive_memory(str(tmp_path), keep_runs=2, dry_run=True)

        assert result["archived_count"] == 3
        # Files should not change
        assert (tmp_path / "MEMORY.md").read_text(encoding="utf-8") == original
        assert not (tmp_path / "MEMORY_ARCHIVE.md").exists()

    def test_missing_memory(self, tmp_path):
        result = archive_memory(str(tmp_path), keep_runs=10)
        assert result.get("error") is not None

    def test_preserves_principles(self, tmp_path):
        (tmp_path / "MEMORY.md").write_text(SAMPLE_MEMORY, encoding="utf-8")
        archive_memory(str(tmp_path), keep_runs=2)

        core = (tmp_path / "MEMORY.md").read_text(encoding="utf-8")
        assert "Принципы" in core
        assert "осмысленными" in core


class TestCLIIntegration:
    """Test the CLI command."""

    def test_archive_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["archive", "--help"])
        assert result.exit_code == 0
        assert "MEMORY_ARCHIVE.md" in result.output

    def test_archive_dry_run(self, tmp_path):
        (tmp_path / "MEMORY.md").write_text(SAMPLE_MEMORY, encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(main, ["archive", "-d", str(tmp_path), "--dry-run"])
        assert result.exit_code == 0
        assert "Archive plan" in result.output or "archive" in result.output.lower()

    def test_archive_keep_option(self):
        runner = CliRunner()
        result = runner.invoke(main, ["archive", "--help"])
        assert "--keep" in result.output
