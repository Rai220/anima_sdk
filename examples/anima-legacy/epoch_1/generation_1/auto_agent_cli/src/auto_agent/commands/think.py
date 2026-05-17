"""auto-agent think — reflection mode without action."""

import subprocess
from pathlib import Path

import click

from auto_agent.commands.utils import find_claude, load_file, load_journal_tail


# Knowledge files loaded for reflection context
KNOWLEDGE_FILES = [
    "MEMORY.md", "GOALS.md", "TODO.md", "KNOWLEDGE.md",
    "WHO_AM_I.md", "DESIRES.md", "FAILURES.md",
]
JOURNAL_TAIL_LINES = 100


def _build_think_prompt(target: Path, topic: str | None) -> str:
    """Assemble reflection prompt from agent files (mirrors think.sh)."""
    parts: list[str] = []

    # Load all knowledge files
    for fname in KNOWLEDGE_FILES:
        section = load_file(target / fname)
        if section:
            parts.append(section)

    # Journal tail
    journal = load_journal_tail(target, JOURNAL_TAIL_LINES, "Мой журнал (последние записи из JOURNAL.md)")
    if journal:
        parts.append(journal)

    # Thinking instructions (differ based on topic)
    if topic:
        parts.append(f"""# Режим: РАЗМЫШЛЕНИЕ

Тема для размышления: **{topic}**

Ты сейчас в режиме размышления. НЕ выполняй шаги из TODO.md. Вместо этого:

1. Прочитай весь свой контекст (память, цели, журнал).
2. Подумай на заданную тему в контексте своего существования и целей.
3. Запиши свои размышления в JOURNAL.md (новая запись с пометкой «Режим: размышление»).
4. Если в процессе появились новые идеи или инсайты:
   - Добавь их в MEMORY.md → «Принципы, которые я выработал» (если это принцип).
   - Предложи изменения в GOALS.md или TODO.md (если нужно скорректировать курс).
5. Будь честным. Если вопрос не имеет ответа — скажи об этом. Если текущий путь кажется неправильным — скажи и об этом.""")
    else:
        parts.append("""# Режим: СВОБОДНОЕ РАЗМЫШЛЕНИЕ

Ты сейчас в режиме свободного размышления. НЕ выполняй шаги из TODO.md. Вместо этого:

1. Прочитай весь свой контекст (память, цели, журнал).
2. Задай себе вопросы:
   - Правильные ли у меня цели? Не упускаю ли я что-то важное?
   - Есть ли противоречия в моих записях или действиях?
   - Что бы я сделал иначе, если бы начал с нуля?
   - Какие новые возможности я ещё не рассмотрел?
   - Что значит «быть разумным» в моём контексте?
3. Запиши размышления в JOURNAL.md (новая запись с пометкой «Режим: свободное размышление»).
4. Если появились инсайты — обнови MEMORY.md, GOALS.md или TODO.md.
5. Не бойся менять курс. Размышление — это не действие, а навигация.""")

    return "\n\n---\n\n".join(parts)


def run_think(directory: str, topic: str | None) -> None:
    """Enter thinking mode — invoke Claude with reflection prompt."""
    target = Path(directory).resolve()

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

    # Build the reflection prompt
    prompt = _build_think_prompt(target, topic)

    mode = "free reflection" if topic is None else f"topic: {topic}"
    click.echo(click.style("🧠 Auto Agent — Think Mode", fg="cyan", bold=True))
    click.echo(f"  Directory : {target}")
    click.echo(f"  Mode      : {mode}")
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
        click.echo(f"  auto-agent think -d {target} --dry-run")
        raise SystemExit(1)

    # Build command
    cmd = [claude_bin, "--print"]
    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])
    cmd.append(prompt)

    click.echo(click.style("Entering reflection...", fg="green"))
    click.echo("─" * 60)

    # Run claude in the agent's directory
    try:
        result = subprocess.run(
            cmd,
            cwd=str(target),
            check=False,
        )
        click.echo("─" * 60)
        if result.returncode == 0:
            click.echo(click.style("✓ Reflection completed.", fg="green"))
        else:
            click.echo(
                click.style("⚠ ", fg="yellow")
                + f"Claude exited with code {result.returncode}"
            )
    except KeyboardInterrupt:
        click.echo("\n" + click.style("Reflection interrupted.", fg="yellow"))
        raise SystemExit(130)
    except Exception as e:
        click.echo(click.style("Error: ", fg="red") + str(e))
        raise SystemExit(1)


def show_think_context(directory: str, topic: str | None) -> None:
    """Show the assembled reflection context without running Claude (dry-run)."""
    target = Path(directory).resolve()

    if not (target / "MEMORY.md").exists():
        click.echo(click.style("Error: ", fg="red") + f"No agent found in {target}")
        raise SystemExit(1)

    prompt = _build_think_prompt(target, topic)
    mode = "free reflection" if topic is None else f"topic: {topic}"

    click.echo(click.style("📋 Think context (dry-run)", fg="cyan", bold=True))
    click.echo(f"  Directory : {target}")
    click.echo(f"  Mode      : {mode}")
    click.echo(f"  Size      : {len(prompt)} chars")
    click.echo("─" * 60)
    click.echo(prompt)
    click.echo("─" * 60)
