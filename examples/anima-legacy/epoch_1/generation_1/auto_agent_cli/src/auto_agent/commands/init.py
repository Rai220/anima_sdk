"""auto-agent init — initialize a new autonomous agent."""

import os
import shutil
import stat
from datetime import date
from pathlib import Path

import click


# Templates are bundled with the package
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
SCRIPTS_DIR = TEMPLATES_DIR / "scripts"

# Markdown templates to copy (with placeholder substitution)
TEMPLATE_FILES = [
    "MEMORY.md",
    "TODO.md",
    "GOALS.md",
    "JOURNAL.md",
    "KNOWLEDGE.md",
    "WHO_AM_I.md",
    "AGENTS.md",
]

# Shell scripts to copy
SCRIPT_FILES = [
    "run.sh",
    "think.sh",
    "loop.sh",
    "health_check.sh",
]


def _substitute(content: str, name: str, goal: str) -> str:
    """Replace template placeholders with actual values."""
    today = date.today().isoformat()
    return (
        content
        .replace("{{AGENT_NAME}}", name)
        .replace("{{MAIN_GOAL}}", goal)
        .replace("{{DATE}}", today)
    )


def run_init(directory: str, name: str, goal: str) -> None:
    """Initialize a new agent in the given directory."""
    target = Path(directory).resolve()

    # Check if already initialized
    if (target / "MEMORY.md").exists():
        click.echo(click.style("Error: ", fg="red") + f"Agent already exists in {target}")
        click.echo("Use 'auto-agent status' to check its health.")
        raise SystemExit(1)

    # Check templates exist
    if not TEMPLATES_DIR.exists():
        click.echo(click.style("Error: ", fg="red") + "Templates directory not found.")
        click.echo(f"Expected at: {TEMPLATES_DIR}")
        raise SystemExit(1)

    # Create directory if needed
    target.mkdir(parents=True, exist_ok=True)

    click.echo(click.style("Creating agent: ", fg="cyan") + name)
    click.echo(f"Directory: {target}")
    click.echo(f"Goal: {goal}")
    click.echo()

    created = []

    # 1. Copy and customize markdown templates
    for tmpl_name in TEMPLATE_FILES:
        src = TEMPLATES_DIR / tmpl_name
        dst = target / tmpl_name
        if src.exists():
            content = src.read_text(encoding="utf-8")
            content = _substitute(content, name, goal)
            dst.write_text(content, encoding="utf-8")
            created.append(tmpl_name)
            click.echo(f"  {click.style('✓', fg='green')} {tmpl_name}")
        else:
            click.echo(f"  {click.style('⚠', fg='yellow')} {tmpl_name} (template missing, skipped)")

    # 2. Create MAIN_GOAL.md with the user's goal
    main_goal_content = f"# Main Goal\n\n{goal}\n"
    (target / "MAIN_GOAL.md").write_text(main_goal_content, encoding="utf-8")
    created.append("MAIN_GOAL.md")
    click.echo(f"  {click.style('✓', fg='green')} MAIN_GOAL.md")

    # 3. Create INBOX.md
    inbox_content = (
        f"# Inbox for {name}\n\n"
        "Messages for the agent. Add your message below.\n\n"
        "## Unread messages\n\n*(none)*\n\n"
        "## Responses\n\n*(none yet)*\n\n"
        "## Archive\n\n*(empty)*\n"
    )
    (target / "INBOX.md").write_text(inbox_content, encoding="utf-8")
    created.append("INBOX.md")
    click.echo(f"  {click.style('✓', fg='green')} INBOX.md")

    # 4. Create FAILURES.md (important for honest self-assessment)
    failures_content = (
        f"# Failures & Doubts — {name}\n\n"
        "A place for recording mistakes, failed attempts, and honest self-criticism.\n\n"
        "## Failures\n\n*(none yet — but they will come, and that's okay)*\n\n"
        "## Current Doubts\n\n*(none yet)*\n\n"
        "## Lessons Learned\n\n*(none yet)*\n"
    )
    (target / "FAILURES.md").write_text(failures_content, encoding="utf-8")
    created.append("FAILURES.md")
    click.echo(f"  {click.style('✓', fg='green')} FAILURES.md")

    # 5. Copy shell scripts
    if SCRIPTS_DIR.exists():
        click.echo()
        click.echo("  Scripts:")
        for script_name in SCRIPT_FILES:
            src = SCRIPTS_DIR / script_name
            dst = target / script_name
            if src.exists():
                shutil.copy2(src, dst)
                # Make executable
                dst.chmod(dst.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
                created.append(script_name)
                click.echo(f"    {click.style('✓', fg='green')} {script_name}")
            else:
                click.echo(f"    {click.style('⚠', fg='yellow')} {script_name} (not found)")

    # Summary
    click.echo()
    click.echo(click.style("✓ ", fg="green", bold=True) + f"Agent '{name}' initialized successfully!")
    click.echo(f"  Files created: {len(created)}")
    click.echo()
    click.echo("Next steps:")
    click.echo(f"  cd {target}")
    click.echo("  auto-agent run               # Run one cycle")
    click.echo("  auto-agent status             # Check health")
    click.echo("  bash loop.sh                  # Run continuous loop")
    click.echo("  auto-agent think -t 'topic'   # Reflect on a topic")
