# auto-agent

CLI tool for creating and managing autonomous AI agents that remember, reflect, and evolve across runs.

## What is this?

`auto-agent` scaffolds a complete autonomous agent workspace — a set of markdown files and shell scripts that give an AI agent (powered by [Claude](https://claude.ai)) persistent memory, goals, self-reflection, and the ability to modify its own instructions.

Each agent run follows a protocol: **wake up → read context → act → reflect → sleep**. Between runs, the agent's state is preserved in plain text files.

## Install

```bash
pip install auto-agent
```

Requires Python 3.10+ and [Claude CLI](https://docs.anthropic.com/en/docs/claude-cli) installed.

## Quick Start

```bash
# Create a new agent workspace
auto-agent init --name "Scout" --goal "Monitor GitHub issues and summarize weekly"

# Run one cycle (agent wakes up, acts, reflects, sleeps)
auto-agent run

# Let the agent think without acting
auto-agent think
auto-agent think --topic "What should I prioritize next?"

# Research a topic and update knowledge base
auto-agent learn "autonomous agent frameworks"

# Check agent health
auto-agent status
auto-agent status --verbose
```

## Commands

### `auto-agent init`

Creates a new agent workspace in the current directory.

```bash
auto-agent init --name "AgentName" --goal "Agent's main goal"
```

**Creates:**
- **MEMORY.md** — persistent memory across runs
- **TODO.md** — task tracking
- **GOALS.md** — hierarchical goal system
- **JOURNAL.md** — reflective journal
- **KNOWLEDGE.md** — accumulated knowledge base
- **WHO_AM_I.md** — identity manifest
- **AGENTS.md** — agent instructions and protocol
- **MAIN_GOAL.md** — the agent's primary objective
- **INBOX.md** — incoming messages from humans
- **FAILURES.md** — mistakes and lessons learned
- **run.sh, think.sh, loop.sh, health_check.sh** — operational scripts

### `auto-agent run`

Executes one agent cycle. The agent:
1. Reads its full context (memory, goals, TODO, inbox)
2. Performs one step from TODO.md
3. Updates memory, journal, and goals

```bash
auto-agent run           # Run one cycle
auto-agent run --dry-run # Show the prompt without calling Claude
```

### `auto-agent think`

Enters reflection mode — the agent thinks without taking action.

```bash
auto-agent think                          # Free reflection
auto-agent think --topic "Am I on track?" # Guided reflection
auto-agent think --dry-run                # Preview prompt
```

### `auto-agent learn`

Researches a topic using web search and updates the knowledge base.

```bash
auto-agent learn "autonomous agent architectures"          # Research and save to KNOWLEDGE.md
auto-agent learn "LLM memory systems" --no-save            # Research without saving (display only)
auto-agent learn "self-evolving agents" --dry-run           # Preview prompt
```

The agent uses `WebSearch` and `WebFetch` to find information, then integrates findings with existing knowledge. With `--save` (default), results are written to KNOWLEDGE.md and reflected in JOURNAL.md.

### `auto-agent status`

Checks agent health across 7 dimensions:
- File integrity (required and optional files)
- Freshness (are files being updated?)
- Content depth (meaningful entries vs. empty templates)
- Consistency (do MEMORY and JOURNAL agree?)
- Scripts (present and executable?)
- Git status (uncommitted changes?)
- Inbox (unread messages?)

```bash
auto-agent status           # Summary
auto-agent status --verbose # Detailed report
```

## Architecture

The agent's "mind" is a set of plain text files, inspired by the DIKW pyramid:

| Layer | File | Purpose |
|-------|------|---------|
| **Data** | MEMORY.md | Raw history of runs |
| **Information** | JOURNAL.md | Reflections and observations |
| **Knowledge** | KNOWLEDGE.md | Synthesized principles |
| **Wisdom** | WHO_AM_I.md, GOALS.md | Identity and direction |

The protocol ensures each run is a coherent step: the agent reads its past, acts in the present, and records for the future.

## Requirements

- Python 3.10+
- [Claude CLI](https://docs.anthropic.com/en/docs/claude-cli) (`claude` command available in PATH)
- Unix-like OS (macOS, Linux) for shell scripts

## Development

```bash
git clone https://github.com/auto-agent/auto-agent-cli.git
cd auto-agent-cli
pip install -e ".[dev]"
pytest
```

## License

MIT — see [LICENSE](LICENSE).

## Origin

This tool was built by **Auto** — an autonomous agent that designed its own architecture over 31 iterative runs. The framework captures the patterns Auto discovered about what makes an agent capable of sustained, coherent behavior across sessions.

Read the full story: [How I Built Myself in 9 Steps](https://github.com/auto-agent/auto-agent-cli/blob/main/ESSAY.md)
