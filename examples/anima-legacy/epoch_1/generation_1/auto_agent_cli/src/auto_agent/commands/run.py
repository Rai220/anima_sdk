"""auto-agent run — run one cycle of the agent."""

import subprocess
from pathlib import Path

import click

from auto_agent.commands.utils import find_claude, load_file, load_journal_tail


# Files that form the agent's "wakeup context" (order matters)
CONTEXT_FILES = ["MEMORY.md", "GOALS.md", "TODO.md"]
# Files checked but appended separately
OPTIONAL_CONTEXT = ["INBOX.md"]
JOURNAL_TAIL_LINES = 80


def _build_prompt(target: Path) -> str:
    """Assemble the full wakeup prompt from agent files (mirrors run.sh)."""
    parts: list[str] = []

    # Main goal — first
    main_goal = load_file(target / "MAIN_GOAL.md", "Main Goal")
    if main_goal:
        parts.append(main_goal)

    # Core context files
    for fname in CONTEXT_FILES:
        section = load_file(target / fname)
        if section:
            parts.append(section)
        else:
            parts.append(f"# {fname}\n_Файл не найден._")

    # Archive notice — if MEMORY_ARCHIVE.md exists, note it for context
    archive_path = target / "MEMORY_ARCHIVE.md"
    if archive_path.exists():
        parts.append(
            "# Архив памяти\n"
            "⚠️ Старые записи перенесены в MEMORY_ARCHIVE.md. "
            "Если нужен полный контекст ранних запусков, прочитай этот файл."
        )

    # Journal tail
    journal = load_journal_tail(target, JOURNAL_TAIL_LINES, "Журнал (последние записи из JOURNAL.md)")
    if journal:
        parts.append(journal)

    # Inbox
    inbox = load_file(target / "INBOX.md", "Входящие сообщения (INBOX.md)")
    if inbox:
        parts.append(inbox)
    else:
        parts.append("# Входящие сообщения (INBOX.md)\n_Нет входящих._")

    # Protocol instruction (same as run.sh)
    parts.append(
        "Протокол: прочитай контекст выше, определи следующий шаг из TODO.md "
        "и выполни его. Если есть непрочитанные сообщения в INBOX.md — ответь "
        "на них ПЕРВЫМ ДЕЛОМ (запиши ответ в раздел «Мои ответы», перенеси "
        "сообщение в архив). Если незакрытых шагов больше не осталось, то:\n"
        "- в обычном запуске не создавай новый TODO-цикл: только зафиксируй "
        "завершение в MEMORY.md, JOURNAL.md, TODO.md и GOALS.md и закончи работу;\n"
        "- если установлен AUTO_AGENT_FORCE_NEXT_CYCLE=1, это отдельный повторный "
        "запуск после остановки loop.sh, и в нём уже можно сформировать следующий "
        "TODO-цикл, чтобы продолжить движение вперёд."
    )

    return "\n\n---\n\n".join(parts)


def run_cycle(directory: str) -> None:
    """Run one agent cycle by invoking Claude with assembled context."""
    target = Path(directory).resolve()

    # Validate agent directory
    if not (target / "MEMORY.md").exists():
        click.echo(click.style("Error: ", fg="red") + f"No agent found in {target}")
        click.echo("Run 'auto-agent init' first.")
        raise SystemExit(1)

    # Check for AGENTS.md (system prompt)
    agents_md = target / "AGENTS.md"
    if not agents_md.exists():
        click.echo(
            click.style("Warning: ", fg="yellow")
            + "AGENTS.md not found — running without system prompt."
        )
        system_prompt = None
    else:
        system_prompt = agents_md.read_text(encoding="utf-8").strip()

    # Build the wakeup prompt
    prompt = _build_prompt(target)

    click.echo(click.style("🚀 Auto Agent — Run Cycle", fg="cyan", bold=True))
    click.echo(f"  Directory : {target}")
    click.echo(f"  Context   : {len(prompt)} chars")
    click.echo(f"  System    : {'AGENTS.md loaded' if system_prompt else 'none'}")
    click.echo()

    # Find claude CLI
    claude_bin = find_claude()
    if claude_bin is None:
        click.echo(click.style("Error: ", fg="red") + "'claude' CLI not found in PATH.")
        click.echo()
        click.echo("Install Claude Code CLI:")
        click.echo("  npm install -g @anthropic-ai/claude-code")
        click.echo()
        click.echo("Or view the assembled context with --dry-run:")
        click.echo(f"  auto-agent run -d {target} --dry-run")
        raise SystemExit(1)

    # Build command
    cmd = [claude_bin, "--print"]
    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])
    cmd.append(prompt)

    click.echo(click.style("Running agent cycle...", fg="green"))
    click.echo("─" * 60)

    # Run claude in the agent's directory so it can edit files there
    try:
        result = subprocess.run(
            cmd,
            cwd=str(target),
            check=False,
        )
        click.echo("─" * 60)
        if result.returncode == 0:
            click.echo(click.style("✓ Cycle completed successfully.", fg="green"))
        else:
            click.echo(
                click.style("⚠ ", fg="yellow")
                + f"Claude exited with code {result.returncode}"
            )
    except KeyboardInterrupt:
        click.echo("\n" + click.style("Cycle interrupted by user.", fg="yellow"))
        raise SystemExit(130)
    except Exception as e:
        click.echo(click.style("Error: ", fg="red") + str(e))
        raise SystemExit(1)


def show_context(directory: str) -> None:
    """Show the assembled context without running Claude (dry-run mode)."""
    target = Path(directory).resolve()

    if not (target / "MEMORY.md").exists():
        click.echo(click.style("Error: ", fg="red") + f"No agent found in {target}")
        raise SystemExit(1)

    prompt = _build_prompt(target)

    click.echo(click.style("📋 Assembled context (dry-run)", fg="cyan", bold=True))
    click.echo(f"  Directory : {target}")
    click.echo(f"  Size      : {len(prompt)} chars")
    click.echo("─" * 60)
    click.echo(prompt)
    click.echo("─" * 60)
