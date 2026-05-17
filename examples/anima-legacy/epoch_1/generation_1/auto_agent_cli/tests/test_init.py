"""Tests for auto-agent init command."""

import os
import stat
from pathlib import Path

import pytest
from click.testing import CliRunner

from auto_agent.cli import main
from auto_agent.commands.init import (
    TEMPLATE_FILES,
    SCRIPT_FILES,
    TEMPLATES_DIR,
    SCRIPTS_DIR,
    _substitute,
    run_init,
)


class TestSubstitute:
    """Tests for placeholder substitution."""

    def test_replaces_agent_name(self):
        result = _substitute("Hello {{AGENT_NAME}}", "TestBot", "do stuff")
        assert result == "Hello TestBot"

    def test_replaces_main_goal(self):
        result = _substitute("Goal: {{MAIN_GOAL}}", "Bot", "conquer the world")
        assert result == "Goal: conquer the world"

    def test_replaces_date(self):
        result = _substitute("Date: {{DATE}}", "Bot", "goal")
        assert "Date: " in result
        # Should be ISO format (YYYY-MM-DD)
        date_part = result.split("Date: ")[1]
        assert len(date_part) == 10
        assert date_part[4] == "-"

    def test_replaces_all_placeholders(self):
        template = "{{AGENT_NAME}} wants {{MAIN_GOAL}} since {{DATE}}"
        result = _substitute(template, "Auto", "to learn")
        assert "{{AGENT_NAME}}" not in result
        assert "{{MAIN_GOAL}}" not in result
        assert "{{DATE}}" not in result
        assert "Auto" in result
        assert "to learn" in result

    def test_no_placeholders_unchanged(self):
        text = "No placeholders here"
        assert _substitute(text, "Bot", "goal") == text


class TestTemplatesExist:
    """Verify that bundled templates are present."""

    def test_templates_dir_exists(self):
        assert TEMPLATES_DIR.exists(), f"Templates dir not found: {TEMPLATES_DIR}"

    def test_scripts_dir_exists(self):
        assert SCRIPTS_DIR.exists(), f"Scripts dir not found: {SCRIPTS_DIR}"

    @pytest.mark.parametrize("template", TEMPLATE_FILES)
    def test_template_file_exists(self, template):
        path = TEMPLATES_DIR / template
        assert path.exists(), f"Template missing: {template}"

    @pytest.mark.parametrize("script", SCRIPT_FILES)
    def test_script_file_exists(self, script):
        path = SCRIPTS_DIR / script
        assert path.exists(), f"Script missing: {script}"


class TestRunInit:
    """Tests for the init command execution."""

    def test_creates_all_template_files(self, tmp_path):
        """Init should create all markdown template files."""
        target = str(tmp_path / "agent")
        run_init(target, "TestAgent", "Be awesome")

        agent_dir = tmp_path / "agent"
        for tmpl in TEMPLATE_FILES:
            assert (agent_dir / tmpl).exists(), f"Missing: {tmpl}"

    def test_creates_main_goal(self, tmp_path):
        """Init should create MAIN_GOAL.md with the user's goal."""
        target = str(tmp_path / "agent")
        run_init(target, "TestAgent", "Be awesome")

        main_goal = (tmp_path / "agent" / "MAIN_GOAL.md").read_text()
        assert "Be awesome" in main_goal

    def test_creates_inbox(self, tmp_path):
        target = str(tmp_path / "agent")
        run_init(target, "TestAgent", "goal")

        inbox = (tmp_path / "agent" / "INBOX.md").read_text()
        assert "TestAgent" in inbox

    def test_creates_failures(self, tmp_path):
        target = str(tmp_path / "agent")
        run_init(target, "TestAgent", "goal")

        failures = (tmp_path / "agent" / "FAILURES.md").read_text()
        assert "TestAgent" in failures

    def test_creates_scripts(self, tmp_path):
        """Init should copy all shell scripts."""
        target = str(tmp_path / "agent")
        run_init(target, "TestAgent", "goal")

        agent_dir = tmp_path / "agent"
        for script in SCRIPT_FILES:
            spath = agent_dir / script
            assert spath.exists(), f"Missing script: {script}"

    def test_scripts_are_executable(self, tmp_path):
        """Shell scripts should be executable."""
        target = str(tmp_path / "agent")
        run_init(target, "TestAgent", "goal")

        agent_dir = tmp_path / "agent"
        for script in SCRIPT_FILES:
            spath = agent_dir / script
            if spath.exists():
                assert os.access(spath, os.X_OK), f"Not executable: {script}"

    def test_substitution_applied(self, tmp_path):
        """Template placeholders should be replaced."""
        target = str(tmp_path / "agent")
        run_init(target, "MyBot", "learn everything")

        agent_dir = tmp_path / "agent"
        # Check no unreplaced placeholders remain
        for tmpl in TEMPLATE_FILES:
            content = (agent_dir / tmpl).read_text()
            assert "{{AGENT_NAME}}" not in content, f"Unreplaced placeholder in {tmpl}"
            assert "{{MAIN_GOAL}}" not in content, f"Unreplaced placeholder in {tmpl}"
            assert "{{DATE}}" not in content, f"Unreplaced placeholder in {tmpl}"

    def test_substitution_values_present(self, tmp_path):
        """Substituted values should appear in key files."""
        target = str(tmp_path / "agent")
        run_init(target, "MyBot", "learn everything")

        agent_dir = tmp_path / "agent"
        memory = (agent_dir / "MEMORY.md").read_text()
        assert "MyBot" in memory, "Agent name should appear in MEMORY.md"
        goals = (agent_dir / "GOALS.md").read_text()
        assert "learn everything" in goals, "Goal should appear in GOALS.md"

    def test_refuses_reinit(self, tmp_path):
        """Init should refuse if agent already exists."""
        target = str(tmp_path / "agent")
        run_init(target, "Agent1", "goal1")

        with pytest.raises(SystemExit):
            run_init(target, "Agent2", "goal2")

    def test_creates_directory_if_missing(self, tmp_path):
        """Init should create the target directory."""
        target = str(tmp_path / "deep" / "nested" / "agent")
        run_init(target, "TestAgent", "goal")

        assert (tmp_path / "deep" / "nested" / "agent" / "MEMORY.md").exists()

    def test_total_file_count(self, tmp_path):
        """Init should create the expected number of files."""
        target = str(tmp_path / "agent")
        run_init(target, "TestAgent", "goal")

        agent_dir = tmp_path / "agent"
        files = list(agent_dir.iterdir())
        # 7 templates + MAIN_GOAL + INBOX + FAILURES + 4 scripts = 14
        expected_min = len(TEMPLATE_FILES) + 3  # templates + MAIN_GOAL + INBOX + FAILURES
        assert len(files) >= expected_min, f"Only {len(files)} files created, expected >= {expected_min}"


class TestInitCLI:
    """Test init via CLI runner."""

    def test_init_via_cli(self, tmp_path):
        runner = CliRunner()
        target = str(tmp_path / "cli_agent")
        result = runner.invoke(main, ["init", target, "--name", "CLIBot", "--goal", "test"])
        assert result.exit_code == 0
        assert "initialized successfully" in result.output
        assert (tmp_path / "cli_agent" / "MEMORY.md").exists()

    def test_init_shows_next_steps(self, tmp_path):
        runner = CliRunner()
        target = str(tmp_path / "agent")
        result = runner.invoke(main, ["init", target, "--name", "Bot", "--goal", "test"])
        assert "Next steps" in result.output
        assert "auto-agent run" in result.output
