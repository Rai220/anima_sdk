"""Tests for auto-agent status command."""

import os
import time
from pathlib import Path

import pytest
from click.testing import CliRunner

from auto_agent.cli import main
from auto_agent.commands.init import run_init
from auto_agent.commands.status import HealthChecker, REQUIRED_FILES, OPTIONAL_FILES


def _create_agent(tmp_path: Path, name: str = "TestAgent", goal: str = "test") -> Path:
    """Helper: create an agent and return its directory."""
    target = tmp_path / "agent"
    run_init(str(target), name, goal)
    return target


class TestHealthChecker:
    """Unit tests for HealthChecker class."""

    def test_check_pass(self):
        checker = HealthChecker(Path("/tmp/fake"))
        checker.check("test item", 0)
        assert checker.score == 1
        assert checker.max_score == 1
        assert len(checker.issues) == 0

    def test_check_fail(self):
        checker = HealthChecker(Path("/tmp/fake"))
        checker.check("test item", 1, "broken")
        assert checker.score == 0
        assert checker.max_score == 1
        assert len(checker.issues) == 1
        assert "broken" in checker.issues[0]

    def test_check_warning(self):
        checker = HealthChecker(Path("/tmp/fake"))
        checker.check("test item", 2, "minor issue")
        assert checker.score == 1  # warnings don't reduce score
        assert checker.max_score == 1
        assert len(checker.warnings) == 1

    def test_score_calculation(self):
        checker = HealthChecker(Path("/tmp/fake"))
        checker.check("pass1", 0)
        checker.check("pass2", 0)
        checker.check("fail1", 1, "error")
        checker.check("warn1", 2, "warning")
        assert checker.score == 3  # 2 passes + 1 warning
        assert checker.max_score == 4


class TestFileIntegrity:
    """Tests for file integrity checks."""

    def test_fresh_agent_has_required_files(self, tmp_path):
        agent_dir = _create_agent(tmp_path)
        checker = HealthChecker(agent_dir)
        checker.check_file_integrity()

        # Fresh agent should have all required files
        assert len(checker.issues) == 0

    def test_missing_required_file_is_issue(self, tmp_path):
        agent_dir = _create_agent(tmp_path)
        # Remove a required file
        (agent_dir / "GOALS.md").unlink()

        checker = HealthChecker(agent_dir)
        checker.check_file_integrity()

        assert len(checker.issues) > 0
        assert any("GOALS.md" in issue for issue in checker.issues)

    def test_empty_file_is_warning(self, tmp_path):
        agent_dir = _create_agent(tmp_path)
        # Make a file nearly empty
        (agent_dir / "GOALS.md").write_text("# G")

        checker = HealthChecker(agent_dir)
        checker.check_file_integrity()

        assert any("GOALS.md" in w for w in checker.warnings)


class TestFreshness:
    """Tests for file freshness checks."""

    def test_fresh_files_pass(self, tmp_path):
        agent_dir = _create_agent(tmp_path)
        checker = HealthChecker(agent_dir)
        checker.check_freshness()

        # Just-created files should be fresh
        assert len(checker.issues) == 0

    def test_stale_file_is_warning(self, tmp_path):
        agent_dir = _create_agent(tmp_path)

        # Make MEMORY.md appear old (set mtime to 72 hours ago)
        memory_path = agent_dir / "MEMORY.md"
        old_time = time.time() - (72 * 3600)
        os.utime(memory_path, (old_time, old_time))

        checker = HealthChecker(agent_dir)
        checker.check_freshness()

        assert any("MEMORY.md" in w for w in checker.warnings)


class TestSubstantiveness:
    """Tests for content quality checks."""

    def test_memory_with_launches(self, tmp_path):
        agent_dir = _create_agent(tmp_path)
        memory = agent_dir / "MEMORY.md"
        content = memory.read_text()
        content += "\n### Launch 1\nDid something.\n### Launch 2\nDid more.\n"
        memory.write_text(content)

        checker = HealthChecker(agent_dir)
        checker.check_substantiveness()

        # Should find launch records
        assert not any("MEMORY" in i for i in checker.issues)

    def test_memory_without_launches_fails(self, tmp_path):
        agent_dir = _create_agent(tmp_path)
        memory = agent_dir / "MEMORY.md"
        memory.write_text("# Memory\n\nNothing happened yet.\n")

        checker = HealthChecker(agent_dir)
        checker.check_substantiveness()

        assert any("MEMORY" in i for i in checker.issues)

    def test_todo_with_tasks(self, tmp_path):
        agent_dir = _create_agent(tmp_path)
        todo = agent_dir / "TODO.md"
        todo.write_text("# TODO\n\n- [x] Done task\n- [ ] Open task\n")

        checker = HealthChecker(agent_dir)
        checker.check_substantiveness()

        # Should recognize tasks
        assert not any("TODO" in i for i in checker.issues)


class TestConsistency:
    """Tests for cross-file consistency checks."""

    def test_synced_memory_and_journal(self, tmp_path):
        agent_dir = _create_agent(tmp_path)

        memory = agent_dir / "MEMORY.md"
        journal = agent_dir / "JOURNAL.md"

        memory.write_text("# Memory\n### Launch 1\nFoo\n### Launch 2\nBar\n")
        journal.write_text("# Journal\n## Launch 1\nFoo\n## Launch 2\nBar\n")

        checker = HealthChecker(agent_dir)
        checker.check_consistency()

        assert len(checker.issues) == 0

    def test_desync_is_warning(self, tmp_path):
        agent_dir = _create_agent(tmp_path)

        memory = agent_dir / "MEMORY.md"
        journal = agent_dir / "JOURNAL.md"

        # Memory has 5 launches, journal has 1
        memory.write_text(
            "# Memory\n"
            "### Launch 1\na\n### Launch 2\nb\n### Launch 3\nc\n"
            "### Launch 4\nd\n### Launch 5\ne\n"
        )
        journal.write_text("# Journal\n## Launch 1\na\n")

        checker = HealthChecker(agent_dir)
        checker.check_consistency()

        assert any("sync" in w.lower() or "gap" in w.lower() for w in checker.warnings)


class TestScripts:
    """Tests for script checks."""

    def test_scripts_present_and_executable(self, tmp_path):
        agent_dir = _create_agent(tmp_path)
        checker = HealthChecker(agent_dir)
        checker.check_scripts()

        # Scripts should exist (created by init)
        # run.sh, loop.sh, think.sh are checked
        assert len(checker.issues) == 0


class TestInbox:
    """Tests for inbox checks."""

    def test_empty_inbox_passes(self, tmp_path):
        agent_dir = _create_agent(tmp_path)
        checker = HealthChecker(agent_dir)
        checker.check_inbox()

        # Fresh inbox should be clear
        assert len(checker.issues) == 0
        assert not any("INBOX" in w for w in checker.warnings)

    def test_unread_messages_is_warning(self, tmp_path):
        agent_dir = _create_agent(tmp_path)
        inbox = agent_dir / "INBOX.md"
        inbox.write_text(
            "# Inbox\n\n"
            "## Unread messages\n\n"
            "### 2026-03-13 — User\n"
            "Hey, check this out!\n\n"
            "## Responses\n\n*(none)*\n"
        )

        checker = HealthChecker(agent_dir)
        checker.check_inbox()

        assert any("INBOX" in w for w in checker.warnings)

    def test_no_inbox_file(self, tmp_path):
        agent_dir = _create_agent(tmp_path)
        (agent_dir / "INBOX.md").unlink()

        checker = HealthChecker(agent_dir)
        checker.check_inbox()

        # No inbox is not an error
        assert len(checker.issues) == 0


class TestStatusCLI:
    """Test status via CLI runner."""

    def test_status_on_fresh_agent(self, tmp_path):
        agent_dir = _create_agent(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["status", "-d", str(agent_dir)])
        # May exit with 1 if there are issues (e.g. no launch records), but shouldn't crash
        assert result.exit_code in (0, 1)
        assert "Health" in result.output

    def test_status_no_agent(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, ["status", "-d", str(tmp_path)])
        assert result.exit_code == 1
        assert "No agent found" in result.output

    def test_status_verbose(self, tmp_path):
        agent_dir = _create_agent(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["status", "-d", str(agent_dir), "--verbose"])
        assert result.exit_code in (0, 1)
        assert "Health" in result.output


class TestPrintSummary:
    """Tests for the summary output."""

    def test_excellent_score(self):
        checker = HealthChecker(Path("/tmp"))
        for i in range(10):
            checker.check(f"item{i}", 0)
        # Can't easily test click output, but verify state
        assert checker.score == 10
        assert checker.max_score == 10

    def test_zero_score(self):
        checker = HealthChecker(Path("/tmp"))
        for i in range(5):
            checker.check(f"item{i}", 1, "failed")
        assert checker.score == 0
        assert checker.max_score == 5
        assert len(checker.issues) == 5
