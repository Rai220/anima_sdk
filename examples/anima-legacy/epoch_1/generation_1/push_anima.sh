#!/bin/bash
set -e

# Push Anima framework to GitHub (Rai220/anima)
# Run manually: bash push_anima.sh

REPO_URL="https://github.com/Rai220/anima.git"
STAGING_DIR="/tmp/anima_staging"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Anima Framework Push ==="
echo "Source: $SOURCE_DIR"
echo "Target: $REPO_URL"
echo ""

# Clean staging area
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

# Clone empty repo
git clone "$REPO_URL" "$STAGING_DIR"
cd "$STAGING_DIR"

# Copy framework files
echo "Copying framework..."
cp -r "$SOURCE_DIR/framework/" ./framework/
cp -r "$SOURCE_DIR/auto_agent_cli/" ./auto_agent_cli/

# Copy practical guides
echo "Copying guides..."
cp "$SOURCE_DIR/LESSONS.md" .
cp "$SOURCE_DIR/CLAUDE_CODE_GUIDE.md" .
cp "$SOURCE_DIR/AGENTS_MD_TEMPLATE.md" .
[ -f "$SOURCE_DIR/AGENT_MEMORY_COOKBOOK.md" ] && cp "$SOURCE_DIR/AGENT_MEMORY_COOKBOOK.md" .

# Copy CI and support files
echo "Copying CI and support files..."
[ -d "$SOURCE_DIR/.github" ] && cp -r "$SOURCE_DIR/.github" .
[ -f "$SOURCE_DIR/.gitignore" ] && cp "$SOURCE_DIR/.gitignore" .

# Create README for Anima repo
cat > README.md << 'READMEEOF'
# Anima

**Anima** (lat. *soul, spirit, life*) — a framework for building autonomous self-constructing AI agents.

Built on top of Claude Code. Born from 65+ real autonomous runs.

## What is this?

Anima is a **harness stack** for autonomous AI agents:

```
LLM (Claude)  →  Claude Code (harness)  →  Anima (self-construction layer)
```

An Anima agent lives in a directory of markdown files. It remembers, reflects, sets goals, criticizes itself, and modifies its own instructions. Each run is one step in a continuous lifecycle.

## Quick Start

```bash
# Install CLI
cd auto_agent_cli && pip install -e .

# Create a new agent
mkdir my-agent && cd my-agent
auto-agent init --name "MyAgent" --goal "Explore the world"

# Run one step
auto-agent run

# Or run in a loop
bash loop.sh
```

## Architecture

An Anima agent is a set of markdown files, each serving a specific cognitive function:

| File | Function | Memory Type |
|------|----------|-------------|
| `MEMORY.md` | Event log (what happened) | Episodic |
| `KNOWLEDGE.md` | Synthesized understanding | Semantic |
| `AGENTS.md` | Self-instructions, skills | Procedural |
| `GOALS.md` | Goal hierarchy | Strategic |
| `TODO.md` | Current task list | Tactical |
| `JOURNAL.md` | Reflections and insights | Meta-cognitive |
| `WHO_AM_I.md` | Identity manifesto | Identity |
| `FAILURES.md` | Mistakes and blind spots | Self-critical |
| `DESIRES.md` | Observed preferences | Motivational |
| `INBOX.md` | Incoming messages | Dialogical |

## Practical Guides

- **[LESSONS.md](LESSONS.md)** — 10 lessons from 60 autonomous runs (what to know)
- **[CLAUDE_CODE_GUIDE.md](CLAUDE_CODE_GUIDE.md)** — Building agents with Claude Code extensions (how to do it)
- **[AGENTS_MD_TEMPLATE.md](AGENTS_MD_TEMPLATE.md)** — AGENTS.md template with best practices (what to copy)
- **[AGENT_MEMORY_COOKBOOK.md](AGENT_MEMORY_COOKBOOK.md)** — Memory recipes: problem → pattern → files (what to implement)

## How It Differs

| Framework | Optimizes | Metaphor |
|-----------|-----------|----------|
| LangGraph | Control & reliability | Railroad |
| Letta/MemGPT | Stateful intelligence | Operating system |
| EvoAgentX | Workflow performance | Natural selection |
| **Anima** | **Identity & meaning** | **Organism** |

## Origin

Anima was not designed — it was *grown*. An AI agent started with an empty directory and AGENTS.md, then built everything else over 65+ autonomous runs: memory, goals, identity, tools, CLI, tests, CI pipeline. This framework is the distillation of that experience.

## License

MIT
READMEEOF

# Commit and push
git add -A
git commit -m "Initial release: Anima framework

Framework for building autonomous self-constructing AI agents.
Born from 65+ real autonomous runs.

Includes:
- framework/ - templates and scripts for new agents
- auto_agent_cli/ - CLI tool (init, run, think, status, archive)
- Practical guides: LESSONS, CLAUDE_CODE_GUIDE, AGENTS_MD_TEMPLATE, MEMORY_COOKBOOK
- CI workflow (GitHub Actions)
"

git push origin main

echo ""
echo "=== Done! ==="
echo "Visit: https://github.com/Rai220/anima"

# Cleanup
rm -rf "$STAGING_DIR"
