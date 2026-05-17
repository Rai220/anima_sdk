"""Tests for auto-agent learn command."""

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from auto_agent.cli import main
from auto_agent.commands.learn import _build_learn_prompt


# --- Fixtures ---

@pytest.fixture
def agent_dir(tmp_path: Path) -> Path:
    """Create a minimal agent directory with knowledge files."""
    (tmp_path / "MEMORY.md").write_text("# Memory\n## Facts\n- I am a test agent\n")
    (tmp_path / "KNOWLEDGE.md").write_text(
        "# Knowledge\n## About myself\n- I use markdown files\n"
    )
    (tmp_path / "JOURNAL.md").write_text(
        "# Journal\n## Run 1\nI did something interesting.\n"
    )
    (tmp_path / "AGENTS.md").write_text("# AGENTS\nYou are a test agent.\n")
    return tmp_path


@pytest.fixture
def agent_dir_minimal(tmp_path: Path) -> Path:
    """Create agent directory with only MEMORY.md."""
    (tmp_path / "MEMORY.md").write_text("# Memory\n- Minimal agent\n")
    return tmp_path


# --- CLI tests ---

class TestLearnCLI:
    """Test CLI integration for learn command."""

    def test_learn_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["learn", "--help"])
        assert result.exit_code == 0
        assert "TOPIC" in result.output
        assert "--save" in result.output
        assert "--dry-run" in result.output
        assert "--directory" in result.output

    def test_learn_requires_topic(self):
        runner = CliRunner()
        result = runner.invoke(main, ["learn"])
        assert result.exit_code != 0  # Missing required argument

    def test_learn_in_help_list(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert "learn" in result.output


# --- Prompt building tests ---

class TestBuildLearnPrompt:
    """Test prompt assembly for learn mode."""

    def test_includes_topic(self, agent_dir: Path):
        prompt = _build_learn_prompt(agent_dir, "autonomous agents", save=True)
        assert "autonomous agents" in prompt

    def test_includes_knowledge(self, agent_dir: Path):
        prompt = _build_learn_prompt(agent_dir, "test topic", save=True)
        assert "I use markdown files" in prompt

    def test_includes_memory(self, agent_dir: Path):
        prompt = _build_learn_prompt(agent_dir, "test topic", save=True)
        assert "I am a test agent" in prompt

    def test_includes_journal_tail(self, agent_dir: Path):
        prompt = _build_learn_prompt(agent_dir, "test topic", save=True)
        assert "something interesting" in prompt

    def test_save_mode_mentions_knowledge_update(self, agent_dir: Path):
        prompt = _build_learn_prompt(agent_dir, "test topic", save=True)
        assert "KNOWLEDGE.md" in prompt
        assert "Обнови" in prompt

    def test_no_save_mode_mentions_display_only(self, agent_dir: Path):
        prompt = _build_learn_prompt(agent_dir, "test topic", save=False)
        assert "НЕ изменяй файлы" in prompt

    def test_mentions_websearch(self, agent_dir: Path):
        prompt = _build_learn_prompt(agent_dir, "test topic", save=True)
        assert "WebSearch" in prompt

    def test_minimal_dir_still_works(self, agent_dir_minimal: Path):
        prompt = _build_learn_prompt(agent_dir_minimal, "test", save=True)
        assert "test" in prompt
        assert "Minimal agent" in prompt

    def test_missing_knowledge_no_crash(self, agent_dir_minimal: Path):
        """Should work even without KNOWLEDGE.md."""
        prompt = _build_learn_prompt(agent_dir_minimal, "test", save=True)
        assert "ИССЛЕДОВАНИЕ" in prompt


# --- Execution tests ---

class TestRunLearn:
    """Test learn execution (mocked)."""

    def test_no_agent_dir_fails(self, tmp_path: Path):
        """Should fail if MEMORY.md doesn't exist."""
        runner = CliRunner()
        result = runner.invoke(main, ["learn", "test", "-d", str(tmp_path)])
        assert result.exit_code != 0

    def test_dry_run_shows_context(self, agent_dir: Path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["learn", "quantum computing", "-d", str(agent_dir), "--dry-run"]
        )
        assert result.exit_code == 0
        assert "quantum computing" in result.output
        assert "dry-run" in result.output

    def test_dry_run_no_save(self, agent_dir: Path):
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["learn", "test topic", "-d", str(agent_dir), "--dry-run", "--no-save"],
        )
        assert result.exit_code == 0
        assert "НЕ изменяй файлы" in result.output
