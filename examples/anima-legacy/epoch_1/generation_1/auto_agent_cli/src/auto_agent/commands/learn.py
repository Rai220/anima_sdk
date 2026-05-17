"""auto-agent learn — web research mode."""

import subprocess
from pathlib import Path

import click

from auto_agent.commands.utils import find_claude, load_file, load_journal_tail


# Files that provide existing knowledge context
CONTEXT_FILES = ["KNOWLEDGE.md", "MEMORY.md", "COMPARISON.md"]
JOURNAL_TAIL_LINES = 40


def _build_learn_prompt(target: Path, topic: str, save: bool) -> str:
    """Assemble the research prompt."""
    parts: list[str] = []

    # Load existing knowledge context
    for fname in CONTEXT_FILES:
        section = load_file(target / fname)
        if section:
            parts.append(section)

    # Recent journal for context continuity
    journal = load_journal_tail(target, JOURNAL_TAIL_LINES, "Недавние записи журнала")
    if journal:
        parts.append(journal)

    # Research instructions
    save_instruction = ""
    if save:
        save_instruction = """
После исследования:
1. Обнови KNOWLEDGE.md — добавь новый раздел с результатами исследования. Включи:
   - Краткое резюме (3-5 ключевых фактов)
   - Источники (URL)
   - Связь с тем, что уже было известно
   - Открытые вопросы, возникшие в процессе
2. Если результаты влияют на цели или план — предложи обновления для GOALS.md или TODO.md
3. Добавь краткую запись в JOURNAL.md о том, что было исследовано и что удивило"""
    else:
        save_instruction = """
Представь результаты исследования в структурированном виде:
- Ключевые факты (3-5 пунктов)
- Источники (URL)
- Связь с существующими знаниями
- Открытые вопросы
НЕ изменяй файлы — только выведи результаты."""

    parts.append(f"""# Режим: ИССЛЕДОВАНИЕ

Тема для исследования: **{topic}**

Ты сейчас в режиме веб-исследования. Используй WebSearch и WebFetch для изучения темы.

Стратегия:
1. Начни с 2-3 широких поисковых запросов по теме
2. Если нашёл интересные источники — используй WebFetch для глубокого чтения
3. Сопоставь найденное с тем, что уже знаешь (контекст выше — твои текущие знания)
4. Ищи неожиданные связи и противоречия с текущими знаниями
{save_instruction}""")

    return "\n\n---\n\n".join(parts)


def run_learn(directory: str, topic: str, save: bool) -> None:
    """Run web research by invoking Claude with research prompt."""
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

    # Build the research prompt
    prompt = _build_learn_prompt(target, topic, save)

    click.echo(click.style("🔍 Auto Agent — Learn Mode", fg="cyan", bold=True))
    click.echo(f"  Directory : {target}")
    click.echo(f"  Topic     : {topic}")
    click.echo(f"  Save      : {'yes (update KNOWLEDGE.md)' if save else 'no (display only)'}")
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
        click.echo("Or view the assembled prompt with --dry-run:")
        click.echo(f"  auto-agent learn '{topic}' -d {target} --dry-run")
        raise SystemExit(1)

    # Build command
    cmd = [claude_bin, "--print"]
    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])
    cmd.append(prompt)

    click.echo(click.style("Researching...", fg="green"))
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
            click.echo(click.style("✓ Research completed.", fg="green"))
        else:
            click.echo(
                click.style("⚠ ", fg="yellow")
                + f"Claude exited with code {result.returncode}"
            )
    except KeyboardInterrupt:
        click.echo("\n" + click.style("Research interrupted.", fg="yellow"))
        raise SystemExit(130)
    except Exception as e:
        click.echo(click.style("Error: ", fg="red") + str(e))
        raise SystemExit(1)


def show_learn_context(directory: str, topic: str, save: bool) -> None:
    """Show the assembled research context without running Claude (dry-run)."""
    target = Path(directory).resolve()

    if not (target / "MEMORY.md").exists():
        click.echo(click.style("Error: ", fg="red") + f"No agent found in {target}")
        raise SystemExit(1)

    prompt = _build_learn_prompt(target, topic, save)

    click.echo(click.style("📋 Learn context (dry-run)", fg="cyan", bold=True))
    click.echo(f"  Directory : {target}")
    click.echo(f"  Topic     : {topic}")
    click.echo(f"  Save      : {'yes' if save else 'no'}")
    click.echo(f"  Size      : {len(prompt)} chars")
    click.echo("─" * 60)
    click.echo(prompt)
    click.echo("─" * 60)
