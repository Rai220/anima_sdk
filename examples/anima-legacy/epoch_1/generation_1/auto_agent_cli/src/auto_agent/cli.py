"""CLI entry point for auto-agent."""

import click

from auto_agent import __version__


@click.group()
@click.version_option(version=__version__, prog_name="auto-agent")
def main():
    """Auto Agent — create and manage autonomous AI agents."""
    pass


@main.command()
@click.argument("directory", default=".")
@click.option("--name", "-n", prompt="Agent name", help="Name of the agent")
@click.option("--goal", "-g", prompt="Main goal", help="The agent's main goal")
def init(directory: str, name: str, goal: str):
    """Initialize a new autonomous agent in DIRECTORY."""
    from auto_agent.commands.init import run_init
    run_init(directory, name, goal)


@main.command()
@click.option("--directory", "-d", default=".", help="Agent directory")
@click.option("--dry-run", is_flag=True, help="Show context without running Claude")
def run(directory: str, dry_run: bool):
    """Run one cycle of the agent."""
    if dry_run:
        from auto_agent.commands.run import show_context
        show_context(directory)
    else:
        from auto_agent.commands.run import run_cycle
        run_cycle(directory)


@main.command()
@click.option("--directory", "-d", default=".", help="Agent directory")
@click.option("--topic", "-t", default=None, help="Topic to think about")
@click.option("--dry-run", is_flag=True, help="Show context without running Claude")
def think(directory: str, topic: str | None, dry_run: bool):
    """Enter thinking mode (reflection without action)."""
    if dry_run:
        from auto_agent.commands.think import show_think_context
        show_think_context(directory, topic)
    else:
        from auto_agent.commands.think import run_think
        run_think(directory, topic)


@main.command()
@click.option("--directory", "-d", default=".", help="Agent directory")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def status(directory: str, verbose: bool):
    """Check the health and status of the agent."""
    from auto_agent.commands.status import run_status
    run_status(directory, verbose=verbose)


@main.command()
@click.argument("topic")
@click.option("--directory", "-d", default=".", help="Agent directory")
@click.option("--save/--no-save", default=True, help="Save results to KNOWLEDGE.md (default: yes)")
@click.option("--dry-run", is_flag=True, help="Show context without running Claude")
def learn(topic: str, directory: str, save: bool, dry_run: bool):
    """Research a topic using web search and update knowledge base."""
    if dry_run:
        from auto_agent.commands.learn import show_learn_context
        show_learn_context(directory, topic, save)
    else:
        from auto_agent.commands.learn import run_learn
        run_learn(directory, topic, save)


@main.command()
@click.option("--directory", "-d", default=".", help="Agent directory")
@click.option("--keep", "-k", default=10, help="Number of recent runs to keep in core memory (default: 10)")
@click.option("--dry-run", is_flag=True, help="Show what would be archived without making changes")
def archive(directory: str, keep: int, dry_run: bool):
    """Archive old MEMORY.md entries to MEMORY_ARCHIVE.md.

    Implements progressive memory: keeps recent runs in core memory (always
    loaded), moves older runs to archive (accessible on demand). Inspired by
    Letta/MemGPT's core/archival memory split.
    """
    if dry_run:
        from auto_agent.commands.archive import show_archive_plan
        show_archive_plan(directory, keep)
    else:
        from auto_agent.commands.archive import run_archive
        run_archive(directory, keep)


if __name__ == "__main__":
    main()
