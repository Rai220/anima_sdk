"""Basic tests for auto-agent CLI."""

from click.testing import CliRunner

from auto_agent.cli import main


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "run" in result.output
    assert "think" in result.output
    assert "status" in result.output
    assert "learn" in result.output
    assert "archive" in result.output


def test_archive_help():
    runner = CliRunner()
    result = runner.invoke(main, ["archive", "--help"])
    assert result.exit_code == 0
    assert "--dry-run" in result.output


def test_learn_help():
    runner = CliRunner()
    result = runner.invoke(main, ["learn", "--help"])
    assert result.exit_code == 0


def test_init_help():
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--help"])
    assert result.exit_code == 0
    assert "--name" in result.output
    assert "--goal" in result.output


def test_status_help():
    runner = CliRunner()
    result = runner.invoke(main, ["status", "--help"])
    assert result.exit_code == 0
    assert "--verbose" in result.output
    assert "--directory" in result.output


def test_run_help():
    runner = CliRunner()
    result = runner.invoke(main, ["run", "--help"])
    assert result.exit_code == 0
    assert "--dry-run" in result.output


def test_think_help():
    runner = CliRunner()
    result = runner.invoke(main, ["think", "--help"])
    assert result.exit_code == 0
    assert "--topic" in result.output
    assert "--dry-run" in result.output
