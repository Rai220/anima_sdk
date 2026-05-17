"""auto-agent status — comprehensive agent health check.

Python equivalent of health_check.sh with 7 check categories:
1. File integrity (required + optional)
2. File freshness (stale file detection)
3. Content substantiveness (launches, tasks, goals, knowledge)
4. Consistency (MEMORY vs JOURNAL sync, tasks vs launches)
5. Script checks (existence and permissions)
6. Git status
7. INBOX check
"""

import os
import re
import subprocess
import time
from pathlib import Path

import click


# Core files every agent should have
REQUIRED_FILES = [
    "MEMORY.md",
    "TODO.md",
    "GOALS.md",
    "JOURNAL.md",
    "MAIN_GOAL.md",
    "AGENTS.md",
]

# Optional but valuable files
OPTIONAL_FILES = [
    "KNOWLEDGE.md",
    "WHO_AM_I.md",
    "INBOX.md",
    "DESIRES.md",
    "FAILURES.md",
    "DIALOGUE.md",
]

# Scripts the agent should have
SCRIPTS = ["run.sh", "loop.sh", "think.sh"]

# Files that should be updated regularly (stale threshold: 48 hours)
FRESHNESS_FILES = ["MEMORY.md", "JOURNAL.md", "TODO.md"]
STALE_HOURS = 48


class HealthChecker:
    """Runs all health checks and collects results."""

    def __init__(self, target: Path, verbose: bool = False):
        self.target = target
        self.verbose = verbose
        self.score = 0
        self.max_score = 0
        self.issues: list[str] = []
        self.warnings: list[str] = []

    def check(self, description: str, result: int, detail: str = "") -> None:
        """Record a check result. 0=pass, 1=fail, 2=warning."""
        self.max_score += 1
        if result == 0:
            self.score += 1
        elif result == 2:
            self.warnings.append(f"{description}: {detail}" if detail else description)
            self.score += 1  # warnings don't reduce score
        else:
            self.issues.append(f"{description}: {detail}" if detail else description)

    def check_file_integrity(self) -> None:
        """Check that required and optional files exist and have content."""
        click.echo(click.style("1. File Integrity", fg="cyan", bold=True))

        for fname in REQUIRED_FILES:
            fpath = self.target / fname
            if fpath.exists():
                content = fpath.read_text().strip()
                if len(content) > 20:
                    click.echo(f"  {click.style('OK', fg='green')}  {fname} ({len(content)} chars)")
                    self.check(f"{fname} exists and has content", 0)
                else:
                    click.echo(f"  {click.style('!!', fg='yellow')}  {fname} (nearly empty: {len(content)} chars)")
                    self.check(f"{fname} has content", 2, "nearly empty")
            else:
                click.echo(f"  {click.style('XX', fg='red')}  {fname} (missing)")
                self.check(f"{fname} exists", 1, "missing")

        click.echo()
        optional_count = 0
        for fname in OPTIONAL_FILES:
            fpath = self.target / fname
            if fpath.exists():
                optional_count += 1
                if self.verbose:
                    content = fpath.read_text().strip()
                    click.echo(f"  {click.style('OK', fg='green')}  {fname} ({len(content)} chars)")
        click.echo(f"  Optional files: {optional_count}/{len(OPTIONAL_FILES)} created")

    def check_freshness(self) -> None:
        """Check that key files have been updated recently."""
        click.echo(click.style("2. File Freshness", fg="cyan", bold=True))

        now = time.time()
        for fname in FRESHNESS_FILES:
            fpath = self.target / fname
            if fpath.exists():
                mod_time = fpath.stat().st_mtime
                age_hours = int((now - mod_time) / 3600)
                if age_hours > STALE_HOURS:
                    click.echo(f"  {click.style('!!', fg='yellow')}  {fname} — stale ({age_hours}h since update)")
                    self.check(f"{fname} is fresh", 2, f"not updated in {age_hours}h")
                else:
                    if age_hours == 0:
                        age_str = "< 1h ago"
                    else:
                        age_str = f"{age_hours}h ago"
                    click.echo(f"  {click.style('OK', fg='green')}  {fname} — updated {age_str}")
                    self.check(f"{fname} is fresh", 0)
            else:
                self.check(f"{fname} freshness", 1, "file missing")

    def check_substantiveness(self) -> None:
        """Check that files contain meaningful content."""
        click.echo(click.style("3. Content Quality", fg="cyan", bold=True))

        # MEMORY.md should have launch records
        memory_path = self.target / "MEMORY.md"
        launch_count = 0
        if memory_path.exists():
            content = memory_path.read_text()
            launch_count = len(re.findall(r"###\s+Запуск|###\s+Launch|###\s+Run\s+\d", content))
            if launch_count > 0:
                click.echo(f"  {click.style('OK', fg='green')}  MEMORY: {launch_count} launch records")
                self.check("MEMORY has launch records", 0)
            else:
                click.echo(f"  {click.style('XX', fg='red')}  MEMORY: no launch records found")
                self.check("MEMORY has launch records", 1, "no records")

        # TODO.md — check open/closed tasks
        todo_path = self.target / "TODO.md"
        done_tasks = 0
        open_tasks = 0
        if todo_path.exists():
            content = todo_path.read_text()
            done_tasks = len(re.findall(r"- \[x\]|- \[X\]", content))
            open_tasks = len(re.findall(r"- \[ \]", content))
            total = done_tasks + open_tasks
            if total > 0:
                pct = done_tasks * 100 // total
                click.echo(f"  {click.style('OK', fg='green')}  TODO: {done_tasks}/{total} done ({pct}%)")
                if open_tasks > 0:
                    self.check("TODO has tasks", 0)
                else:
                    self.check("TODO has open tasks", 2, "all done — time for new goals?")
            else:
                click.echo(f"  {click.style('!!', fg='yellow')}  TODO: no tasks found")
                self.check("TODO has tasks", 2, "no tasks")

        # GOALS.md should have goals
        goals_path = self.target / "GOALS.md"
        if goals_path.exists():
            content = goals_path.read_text()
            goal_count = len(re.findall(r"###\s+\d+\.", content))
            if goal_count > 0:
                click.echo(f"  {click.style('OK', fg='green')}  GOALS: {goal_count} goals defined")
                self.check("GOALS has goals", 0)
            else:
                click.echo(f"  {click.style('!!', fg='yellow')}  GOALS: no structured goals found")
                self.check("GOALS has goals", 2, "no goals found")

        # KNOWLEDGE.md should not be empty
        knowledge_path = self.target / "KNOWLEDGE.md"
        if knowledge_path.exists():
            lines = len(knowledge_path.read_text().splitlines())
            if lines > 5:
                click.echo(f"  {click.style('OK', fg='green')}  KNOWLEDGE: {lines} lines")
                self.check("KNOWLEDGE has content", 0)
            else:
                click.echo(f"  {click.style('!!', fg='yellow')}  KNOWLEDGE: only {lines} lines")
                self.check("KNOWLEDGE has content", 2, "very short")

    def check_consistency(self) -> None:
        """Check that files are consistent with each other."""
        click.echo(click.style("4. Consistency", fg="cyan", bold=True))

        # MEMORY launches vs JOURNAL entries
        memory_path = self.target / "MEMORY.md"
        journal_path = self.target / "JOURNAL.md"

        mem_launches = 0
        jour_entries = 0

        if memory_path.exists():
            mem_launches = len(re.findall(r"###\s+Запуск|###\s+Launch|###\s+Run\s+\d", memory_path.read_text()))
        if journal_path.exists():
            jour_entries = len(re.findall(r"##\s+Запуск|##\s+Launch|##\s+Run\s+\d", journal_path.read_text()))

        if mem_launches > 0 and jour_entries > 0:
            diff = abs(mem_launches - jour_entries)
            if diff <= 2:
                click.echo(f"  {click.style('OK', fg='green')}  MEMORY ({mem_launches}) ~ JOURNAL ({jour_entries}) in sync")
                self.check("MEMORY and JOURNAL in sync", 0)
            else:
                click.echo(f"  {click.style('!!', fg='yellow')}  MEMORY ({mem_launches}) vs JOURNAL ({jour_entries}) — gap of {diff}")
                self.check("MEMORY and JOURNAL in sync", 2, f"gap of {diff}")
        elif mem_launches > 0 or jour_entries > 0:
            click.echo(f"  {click.style('!!', fg='yellow')}  Can't compare — MEMORY: {mem_launches}, JOURNAL: {jour_entries}")
            self.check("MEMORY and JOURNAL comparable", 2, "one file has no entries")
        else:
            click.echo(f"  {click.style('--', fg='white')}  No launch data to compare")

    def check_scripts(self) -> None:
        """Check that shell scripts exist and are executable."""
        click.echo(click.style("5. Scripts", fg="cyan", bold=True))

        for script in SCRIPTS:
            spath = self.target / script
            if spath.exists():
                if os.access(spath, os.X_OK):
                    click.echo(f"  {click.style('OK', fg='green')}  {script} (executable)")
                    self.check(f"{script} is executable", 0)
                else:
                    click.echo(f"  {click.style('!!', fg='yellow')}  {script} (exists but not executable)")
                    self.check(f"{script} is executable", 2, "missing +x permission")
            else:
                click.echo(f"  {click.style('--', fg='white')}  {script} (not found)")
                # Not a hard requirement for CLI-managed agents
                self.check(f"{script} exists", 2, "not created")

    def check_git(self) -> None:
        """Check git repository status."""
        click.echo(click.style("6. Git", fg="cyan", bold=True))

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=self.target,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                click.echo(f"  {click.style('--', fg='white')}  No git repository")
                self.check("Git repository", 2, "not initialized")
                return

            # Check uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.target,
                capture_output=True,
                text=True,
                timeout=5,
            )
            uncommitted = len([l for l in result.stdout.strip().splitlines() if l.strip()])
            if uncommitted == 0:
                click.echo(f"  {click.style('OK', fg='green')}  All changes committed")
                self.check("Changes committed", 0)
            else:
                click.echo(f"  {click.style('!!', fg='yellow')}  {uncommitted} uncommitted changes")
                self.check("Changes committed", 2, f"{uncommitted} uncommitted")

            # Commit count
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=self.target,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                commits = result.stdout.strip()
                click.echo(f"  {click.style('OK', fg='green')}  Repository active ({commits} commits)")
                self.check("Git active", 0)

        except FileNotFoundError:
            click.echo(f"  {click.style('--', fg='white')}  git not found in PATH")
        except subprocess.TimeoutExpired:
            click.echo(f"  {click.style('!!', fg='yellow')}  git command timed out")

    def check_inbox(self) -> None:
        """Check for unread messages."""
        click.echo(click.style("7. Communication", fg="cyan", bold=True))

        inbox_path = self.target / "INBOX.md"
        if not inbox_path.exists():
            click.echo(f"  {click.style('--', fg='white')}  No INBOX.md")
            return

        content = inbox_path.read_text()

        # Look for unread section
        has_unread = False
        for marker in ["## Непрочитанные", "## Unread"]:
            if marker in content:
                section = content.split(marker)[1].split("##")[0]
                # Check if section has actual messages (not just "нет" or empty)
                cleaned = section.strip().lower()
                if cleaned and "нет" not in cleaned and "(нет)" not in cleaned and "none" not in cleaned:
                    has_unread = True
                break

        if has_unread:
            click.echo(f"  {click.style('!!', fg='yellow', bold=True)}  INBOX has unread messages!")
            self.check("INBOX processed", 2, "unread messages waiting")
        else:
            click.echo(f"  {click.style('OK', fg='green')}  INBOX clear")
            self.check("INBOX processed", 0)

    def print_summary(self) -> None:
        """Print overall health summary."""
        click.echo()
        pct = self.score * 100 // self.max_score if self.max_score > 0 else 0

        # Status bar
        bar_width = 20
        filled = pct * bar_width // 100
        bar = click.style("█" * filled, fg="green") + click.style("░" * (bar_width - filled), fg="white")

        click.echo(click.style("═" * 40, fg="cyan"))

        if pct >= 90:
            label = click.style(f"Excellent ({pct}%)", fg="green", bold=True)
        elif pct >= 70:
            label = click.style(f"Good ({pct}%)", fg="yellow", bold=True)
        elif pct >= 50:
            label = click.style(f"Fair ({pct}%)", fg="yellow")
        else:
            label = click.style(f"Needs attention ({pct}%)", fg="red", bold=True)

        click.echo(f"  Health: {label}")
        click.echo(f"  Score:  {self.score}/{self.max_score}  [{bar}]")
        click.echo(click.style("═" * 40, fg="cyan"))

        if self.issues:
            click.echo(click.style("\nIssues:", fg="red", bold=True))
            for issue in self.issues:
                click.echo(f"  {click.style('!', fg='red')} {issue}")

        if self.warnings:
            click.echo(click.style("\nWarnings:", fg="yellow"))
            for warning in self.warnings:
                click.echo(f"  {click.style('~', fg='yellow')} {warning}")

        if not self.issues and not self.warnings:
            click.echo(click.style("\nAll clear!", fg="green"))

        click.echo()


def run_status(directory: str, verbose: bool = False) -> None:
    """Check agent health and report status."""
    target = Path(directory).resolve()

    if not (target / "MEMORY.md").exists():
        click.echo(click.style("Error: ", fg="red") + f"No agent found in {target}")
        click.echo("Run 'auto-agent init' first.")
        raise SystemExit(1)

    click.echo()
    click.echo(click.style("  Agent Health Check", fg="cyan", bold=True))
    click.echo(f"  Directory: {target}")
    click.echo()

    checker = HealthChecker(target, verbose=verbose)

    checker.check_file_integrity()
    click.echo()
    checker.check_freshness()
    click.echo()
    checker.check_substantiveness()
    click.echo()
    checker.check_consistency()
    click.echo()
    checker.check_scripts()
    click.echo()
    checker.check_git()
    click.echo()
    checker.check_inbox()
    click.echo()

    checker.print_summary()

    # Exit with error code if there are issues
    if checker.issues:
        raise SystemExit(1)
