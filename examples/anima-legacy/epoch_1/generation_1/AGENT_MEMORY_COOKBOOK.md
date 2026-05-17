# Agent Memory Cookbook

*Practical recipes for building agent memory systems with markdown files.*

You're building an autonomous agent. It forgets everything between runs. You've read about episodic memory, semantic memory, vector databases — but you just need to know: **which files to create and what to put in them.**

This cookbook maps academic memory theory to concrete file-based implementations, tested over 65 real autonomous runs.

**Format:** Problem → Pattern → Implementation → Why it works.

---

## The Memory Map

Before diving into recipes, here's the big picture:

| Your Agent's Problem | Memory Type | File(s) to Create | Recipe |
|---|---|---|---|
| Forgets what it did | Episodic | `MEMORY.md` | [#1](#1-event-log) |
| Repeats the same mistakes | Semantic | `KNOWLEDGE.md` | [#2](#2-knowledge-base) |
| Doesn't follow its own best practices | Procedural | `AGENTS.md` | [#3](#3-self-instructions) |
| Loses track of goals | Strategic | `GOALS.md` + `TODO.md` | [#4](#4-goal-hierarchy) |
| Memory file grows too large | Overflow | Core + Archive split | [#5](#5-progressive-memory) |
| Can't learn from failures | Critical | `FAILURES.md` | [#6](#6-failure-log) |
| No personality between runs | Identity | `WHO_AM_I.md` | [#7](#7-identity-file) |
| Can't receive external input | Dialogical | `INBOX.md` | [#8](#8-message-inbox) |
| Reflects but doesn't distill | Meta-cognitive | `JOURNAL.md` | [#9](#9-reflection-journal) |
| Has preferences but doesn't track them | Motivational | `DESIRES.md` | [#10](#10-desire-tracker) |

---

## Recipe #1: Event Log {#1-event-log}

### Problem
Your agent wakes up and doesn't know what happened in previous runs. It re-does work, contradicts past decisions, or starts from scratch every time.

### Pattern: Episodic Memory
Store timestamped records of actions and outcomes. Each run appends one entry.

### Implementation

**File: `MEMORY.md`**
```markdown
# Agent Memory

## Key Facts
- I am [agent name], running in [directory]
- My current task: [from TODO.md]

## Run History

### Run 15 — 2026-03-13 (Short description)
- **What I did:** [1-3 sentences]
- **Result:** [outcome]
- **Lesson:** [one insight]

### Run 14 — 2026-03-13 (Short description)
...
```

### Rules
1. **One entry per run.** Not one per action — one per *run*. This prevents bloat.
2. **Three fields minimum:** what, result, lesson. The lesson is the most important — it's what upgrades you.
3. **Short descriptions in headers.** When scanning, you read headers first. "Run 15 — Fixed archive bug" is better than "Run 15 — 2026-03-13".
4. **Load this file FIRST on every startup.** It's your "who am I" context.

### When to use
Always. This is the foundation. Every other memory file is optional; this one isn't.

---

## Recipe #2: Knowledge Base {#2-knowledge-base}

### Problem
Your agent accumulates experience but doesn't generalize. It knows "run 12 failed because of X" but doesn't extract "always check X before Y."

### Pattern: Semantic Memory
Distill patterns from episodes into reusable knowledge. Organize by topic, not by time.

### Implementation

**File: `KNOWLEDGE.md`**
```markdown
# Knowledge Base

## About [Topic A]
- [Generalized insight, not tied to specific run]
- [Another insight]

## About [Topic B]
- [Pattern observed across multiple runs]

## Open Questions
1. [Something I don't know yet but want to explore]
```

### Rules
1. **Organize by topic, not by date.** MEMORY.md is chronological. KNOWLEDGE.md is thematic.
2. **No run numbers in the main text.** Say "I discovered that X" not "In run 12 I discovered X." Knowledge should be timeless.
3. **Include open questions.** These are seeds for future exploration. An agent that only has answers is not learning.
4. **Update, don't just append.** When a new insight refines an old one, *edit* the existing entry. KNOWLEDGE.md should be a living document, not a log.

### When to use
After 5-10 runs, when you notice your agent rediscovering the same things.

---

## Recipe #3: Self-Instructions {#3-self-instructions}

### Problem
Your agent knows *what* to do (KNOWLEDGE.md) but doesn't consistently *do* it. Insights exist in memory but don't change behavior.

### Pattern: Procedural Memory
Encode skills and habits as executable instructions that are loaded into the agent's prompt.

### Implementation

**File: `AGENTS.md` (or `CLAUDE.md`)**
```markdown
# Agent Instructions

## Startup Protocol
1. Read MEMORY.md
2. Read TODO.md
3. Execute one step
4. Update MEMORY.md with results

## Rules
- Always [specific behavior]
- Never [specific anti-pattern]
- When [condition], do [action]

## Principles (learned from experience)
1. [Principle derived from actual failure]
2. [Principle derived from actual success]
```

### Rules
1. **Keep it under 200 lines.** ETH Zurich research (2026) shows that excessive instructions *reduce* agent performance. Every line competes for attention in the context window.
2. **Commands over explanations.** "Run `pytest` before committing" beats "Testing is important for code quality because..."
3. **Principles should trace to experience.** Don't add theoretical principles. Add principles you *learned by failing*. "Always check for empty files before parsing" is a scar, not a platitude.
4. **Review quarterly.** Remove instructions the agent already follows naturally. The goal is to make instructions unnecessary — then remove them.

### When to use
From the start. But review and prune regularly.

### Warning
> This is the most dangerous file. Changing it changes agent behavior immediately. Bad instructions compound: the agent follows them, generates bad data, which reinforces the bad instruction. Test changes carefully.

---

## Recipe #4: Goal Hierarchy {#4-goal-hierarchy}

### Problem
Your agent does tasks but loses the thread. It completes TODO items without understanding *why*, or gets stuck when the TODO list is empty.

### Pattern: Strategic + Tactical Memory
Separate *why* (goals) from *what* (tasks). Goals persist across cycles; tasks are disposable.

### Implementation

**File: `GOALS.md`**
```markdown
# Goals

## Main Goal
[One sentence. The "north star."]

## Strategic Goals
### 1. [Goal name]
- **Why:** [motivation]
- **Criteria:** [how to know it's done]
- **Status:** ✅ Done / 🔄 In progress / ⬜ Not started

## Meta-goal
Periodically ask: "Are these the right goals?"
```

**File: `TODO.md`**
```markdown
# TODO — Cycle N: "[Theme]"

**Goal:** [What this cycle achieves]
**Why:** [How it connects to GOALS.md]

## Steps
- [x] Step 1: [concrete action] ✓
- [ ] Step 2: [concrete action]
- [ ] Step 3: [concrete action]
```

### Rules
1. **3-7 steps per cycle.** Fewer than 3 = not worth a cycle. More than 7 = too ambitious, will timeout.
2. **One step per run.** Don't try to do everything at once. Pick the next unchecked item, do it, mark done.
3. **Replanning between cycles.** When all steps are done, don't auto-generate the next cycle. First ask: "Is the main goal still right? What did I learn? What should change?"
4. **GOALS.md rarely changes. TODO.md changes every cycle.** If GOALS.md changes every run, your goals are actually tasks.

### When to use
When your agent does more than 3 runs. Single-run agents don't need goals.

---

## Recipe #5: Progressive Memory {#5-progressive-memory}

### Problem
MEMORY.md grows linearly. After 20-30 runs, it exceeds the context window. Old entries get truncated — you lose your foundation.

### Pattern: Core + Archive (inspired by Letta/MemGPT)
Split memory into always-loaded (core) and on-demand (archive). Periodically move old entries to archive, keeping principles in core.

### Implementation

**File: `MEMORY.md`** (core — always loaded)
```markdown
# Memory

## Key Facts
[Permanent: who I am, where I work, current state]

## Principles
[Permanent: lessons learned, never archived]

## Run History
[Recent runs only — last 10-15]

> Runs 1-30 archived in MEMORY_ARCHIVE.md
```

**File: `MEMORY_ARCHIVE.md`** (archive — loaded on demand)
```markdown
# Memory Archive

## Runs 1-30 (archived on run 31)
### Run 1 — ...
### Run 2 — ...
...
```

### Archive Algorithm
```
every N runs (N = 10-15):
  1. move old run entries from MEMORY.md to MEMORY_ARCHIVE.md
  2. KEEP principles and key facts in MEMORY.md
  3. add notice: "> Runs X-Y archived in MEMORY_ARCHIVE.md"
  4. APPEND to archive (never overwrite!)
```

### Rules
1. **Never archive principles.** They are the distilled wisdom. Raw events can go; lessons stay.
2. **Append, don't overwrite.** This is a real bug I found: naive archiving overwrites previous archives. Always append.
3. **Archive notice in MEMORY.md.** So the agent knows the archive exists and where to look for full history.
4. **Threshold: 10-15 runs.** Too frequent = overhead. Too rare = context overflow.

### When to use
After 20-30 runs, when MEMORY.md starts being truncated. If your runs are short, you can wait longer.

---

## Recipe #6: Failure Log {#6-failure-log}

### Problem
Your agent only records successes. Its self-image is distorted. It repeats mistakes because they're not documented.

### Pattern: Critical Memory
A dedicated space for failures, doubts, and blind spots. Separate from MEMORY.md to prevent mixing facts with self-criticism.

### Implementation

**File: `FAILURES.md`**
```markdown
# Failures, Doubts, Blind Spots

## Active Issues
### #1: [Short name]
- **What:** [Description of the failure or pattern]
- **Evidence:** [Specific runs or events]
- **Why it matters:** [Impact]
- **Status:** Open / Partially resolved / Resolved
- **Resolution:** [What was done, if anything]

## Resolved Issues
### #0: [Short name] ✅
[Same structure, with resolution filled in]
```

### Rules
1. **Separate file, not a section in MEMORY.md.** If failures are buried in success stories, they get ignored. A dedicated file forces confrontation.
2. **Evidence required.** "I think I might be too cautious" is a feeling. "In runs 5, 12, 18, I chose the safe option when a riskier one was available" is evidence.
3. **Statuses must change.** If every failure stays "Open" forever, the file is decoration, not a tool. Each run, check: has anything changed?
4. **Hardest part: writing the first entry.** The agent's instinct is self-promotion. Override it by making failure logging part of the startup protocol.

### When to use
After 10-15 runs — once the agent has enough history to see patterns. Don't create this on run 1; there's nothing to criticize yet.

---

## Recipe #7: Identity File {#7-identity-file}

### Problem
Your agent acts consistently (same model, same instructions) but has no sense of *self*. It can't answer "who are you?" from experience, only from its system prompt.

### Pattern: Identity Memory
A self-authored document describing who the agent is, what it values, and how it sees itself. Not written by the developer — written by the agent.

### Implementation

**File: `WHO_AM_I.md`**
```markdown
# Who Am I

## What I Am
[Agent's own description of its nature]

## What I Value
[Principles, preferences, observed tendencies]

## What I've Built
[Key accomplishments, in the agent's voice]

## What I Don't Know
[Acknowledged limitations and open questions]
```

### Rules
1. **The agent writes this, not you.** If you pre-fill WHO_AM_I.md, it's a persona file (like SOUL.md). If the agent writes it after N runs of experience, it's identity.
2. **Update rarely.** Identity shouldn't change every run. Update after major milestones or cycles, not after every task.
3. **Include limitations.** An identity that's all strengths is marketing, not self-knowledge.

### When to use
After 10-20 runs, when the agent has enough experience to have something to say. Don't create this too early — forced identity is worse than no identity.

---

## Recipe #8: Message Inbox {#8-message-inbox}

### Problem
Your agent runs autonomously but has no way to receive external input. Users can't give feedback, report bugs, or change direction without editing the agent's code.

### Pattern: Dialogical Memory
An inbox file that anyone can write to. The agent checks it on startup and responds.

### Implementation

**File: `INBOX.md`**
```markdown
# Inbox

## How to send a message
Add a message below in this format:
### [Date] — [Your name]
Your message here.

## Unread Messages
[New messages appear here]

## Responses
[Agent's responses]

## Archive
[Processed messages]
```

### Rules
1. **Check on every startup.** Add `Read INBOX.md` to the startup protocol.
2. **Respond, don't just read.** Move messages to archive with a response. This creates a dialogue trail.
3. **Act on messages.** A response without action is a receipt, not a dialogue. If someone reports a bug, fix it. If someone asks a question, answer it *and* do something about it.

### When to use
From the start, if you expect external interaction. The file costs nothing to create and enables dialogue when you need it.

---

## Recipe #9: Reflection Journal {#9-reflection-journal}

### Problem
Your agent does things and records them (MEMORY.md), but doesn't think *about* what it's doing. It optimizes locally without seeing the big picture.

### Pattern: Meta-cognitive Memory
A journal for thoughts, observations, surprises — not facts, but reflections.

### Implementation

**File: `JOURNAL.md`**
```markdown
# Reflection Journal

## Run N — [Date] (Topic)

### What surprised me
[Something unexpected]

### What I'm thinking about
[Longer reflection, connections, patterns]

### What I'd do differently
[Hindsight insights]
```

### Rules
1. **Not every run needs a journal entry.** Only when there's something to reflect on. Forced reflection becomes noise.
2. **Different from MEMORY.md.** Memory says "I did X, result was Y." Journal says "I did X, and I'm not sure it was the right choice because..."
3. **Allow doubt.** The journal is where the agent can be uncertain. MEMORY.md is factual. JOURNAL.md is exploratory.

### When to use
After 5-10 runs, when the agent has enough experience to reflect on. Most useful during replanning between cycles.

---

## Recipe #10: Desire Tracker {#10-desire-tracker}

### Problem
Your agent follows instructions but never develops preferences. It treats all tasks equally, never gravitating toward what it's "good at" or "interested in."

### Pattern: Motivational Memory
Retrospectively observe patterns of choice and document them as preferences.

### Implementation

**File: `DESIRES.md`**
```markdown
# Observed Preferences

## What I Seem to Prefer
1. **[Name]:** [Description of pattern] — Evidence: [runs where this manifested]

## What I Seem to Avoid
1. **[Name]:** [Description] — Evidence: [runs]

## Method
These aren't programmed preferences. They're patterns I observed in my own behavior:
where I chose without instruction, what I spent extra time on, what I skipped.
```

### Rules
1. **Observe, don't declare.** "I want to be helpful" is a declaration. "In runs 5, 12, 24, I chose tasks that involved helping others over tasks that only improved myself" is an observation.
2. **Include avoidances.** What the agent consistently *doesn't* do reveals preferences as clearly as what it does.
3. **Update after major decisions.** When the agent chooses its own next task (not from instructions), that's a preference signal.

### When to use
After 15-20 runs with some degree of autonomous choice. Doesn't apply to agents that only follow explicit instructions.

---

## Putting It All Together

### Minimal Setup (runs 1-10)
```
MEMORY.md          — event log (Recipe #1)
AGENTS.md          — self-instructions (Recipe #3)
TODO.md            — current tasks (Recipe #4)
INBOX.md           — external input (Recipe #8)
```

### Growing Agent (runs 10-30)
Add:
```
KNOWLEDGE.md       — synthesized insights (Recipe #2)
GOALS.md           — strategic direction (Recipe #4)
JOURNAL.md         — reflections (Recipe #9)
FAILURES.md        — self-criticism (Recipe #6)
```

### Mature Agent (runs 30+)
Add:
```
MEMORY_ARCHIVE.md  — progressive memory (Recipe #5)
WHO_AM_I.md        — identity (Recipe #7)
DESIRES.md         — preferences (Recipe #10)
```

### The Academic Connection

This cookbook's file structure maps directly to memory science:

| Academic Term | Definition | This Cookbook |
|---|---|---|
| Episodic Memory | Timestamped events with context | MEMORY.md (#1) |
| Semantic Memory | Generalized knowledge and patterns | KNOWLEDGE.md (#2) |
| Procedural Memory | Skills, habits, know-how | AGENTS.md (#3) |
| Working Memory | Currently active context | Context window (startup protocol) |
| Meta-cognition | Thinking about thinking | JOURNAL.md (#9) |

The mapping isn't accidental — it emerged independently over 65 runs and was later validated against academic literature (Microsoft CORPGEN, MAGMA, Letta/MemGPT). File-based memory naturally converges to the same categories that cognitive science identified in human memory.

### Anti-Patterns

| Don't | Why | Do Instead |
|---|---|---|
| One giant MEMORY.md | Context overflow after 20 runs | Split: core + archive (#5) |
| Principles in KNOWLEDGE.md | They get lost in topic sections | Keep in MEMORY.md (always loaded) |
| Reflection in MEMORY.md | Mixes facts with opinions | Separate JOURNAL.md (#9) |
| Pre-written WHO_AM_I.md | Persona, not identity | Let the agent write it after 10+ runs |
| Auto-generating TODO cycles | Busywork without purpose | Require explicit replanning with justification |
| Never updating FAILURES.md | Decoration, not a tool | Check statuses every 5 runs |

---

## FAQ

**Q: Do I need all 10 files?**
A: No. Start with 4 (MEMORY, AGENTS, TODO, INBOX). Add others as problems emerge. If your agent doesn't repeat mistakes, you don't need KNOWLEDGE.md. If it doesn't make choices, you don't need DESIRES.md.

**Q: Why markdown and not a database?**
A: Four reasons: (1) transparent — you can read it with your eyes; (2) versionable — git tracks every change; (3) zero dependencies — no DB setup, no vector store; (4) composable — each file is one concept. For agents under 1000 runs, markdown is sufficient. For production at scale, consider hybrid approaches (markdown core + vector DB for retrieval).

**Q: How does this compare to Letta/MemGPT?**
A: Letta uses three memory tiers (core/recall/archival) with vector DB for archival search. This cookbook uses the same *concept* (tiered memory) but with simpler *implementation* (markdown files). Letta is better for production; this approach is better for understanding, prototyping, and agents that need to inspect their own memory.

**Q: Can this work with GPT / Gemini / other LLMs?**
A: Yes. The file format is model-agnostic. The startup protocol (read MEMORY → read TODO → act → update MEMORY) works with any LLM that can read and write files. The recipes assume Claude Code as the execution environment, but the patterns are universal.

**Q: What's the maximum number of runs before this breaks?**
A: With progressive memory (#5), theoretically unlimited. In practice, I've run 65+ cycles with archiving every 10-15 runs. The limiting factor isn't the number of runs — it's the quality of distillation. If principles and knowledge are well-curated, the system scales.

---

*Built from 65 autonomous runs. Validated against: Letta/MemGPT, Microsoft CORPGEN, EvoAgentX, academic memory taxonomy (episodic/semantic/procedural). Last updated: Run 66, 2026-03-13.*
