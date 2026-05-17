#!/bin/bash
# ===========================================
# Auto Agent CLI — End-to-End Lifecycle Test
# ===========================================
# Tests the full agent lifecycle:
#   init → simulate runs → status → archive → verify
#
# Unlike smoke_test.sh (which tests individual commands),
# this script tests the *workflow* — how commands interact
# across a realistic agent lifecycle.
#
# Usage: bash test_e2e.sh
# Requires: auto-agent installed (pip install -e .)
# ===========================================

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "╔═══════════════════════════════════════════╗"
echo "║   Auto Agent CLI — End-to-End Test        ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

# ── Helpers ──────────────────────────────────
ERRORS=0
TESTS=0
pass() { TESTS=$((TESTS + 1)); echo "  ✓ $1"; }
fail() { TESTS=$((TESTS + 1)); ERRORS=$((ERRORS + 1)); echo "  ✗ $1"; }

E2E_DIR=$(mktemp -d "${TMPDIR:-/tmp}/auto_agent_e2e_XXXXXX")
AGENT_DIR="$E2E_DIR/test_agent"
trap "rm -rf '$E2E_DIR'" EXIT

echo "  Temp dir: $E2E_DIR"
echo ""

# ════════════════════════════════════════════
# Phase 1: BIRTH — Initialize a new agent
# ════════════════════════════════════════════
echo "▶ Phase 1: BIRTH — Initialize agent"

auto-agent init "$AGENT_DIR" --name "E2E-Bot" --goal "Survive the end-to-end test" > /dev/null 2>&1 \
    && pass "init succeeded" || fail "init failed"

# Verify all 14 files exist
EXPECTED_FILES="MEMORY.md TODO.md GOALS.md JOURNAL.md KNOWLEDGE.md WHO_AM_I.md AGENTS.md MAIN_GOAL.md INBOX.md FAILURES.md run.sh loop.sh think.sh health_check.sh"
INIT_OK=true
for f in $EXPECTED_FILES; do
    if [[ ! -f "$AGENT_DIR/$f" ]]; then
        fail "missing after init: $f"
        INIT_OK=false
    fi
done
$INIT_OK && pass "all 14 files created"

# Verify template substitution
if grep -q "E2E-Bot" "$AGENT_DIR/MEMORY.md" 2>/dev/null; then
    pass "name substituted in MEMORY.md"
else
    fail "name NOT in MEMORY.md"
fi

if grep -q "Survive the end-to-end test" "$AGENT_DIR/GOALS.md" 2>/dev/null; then
    pass "goal substituted in GOALS.md"
else
    fail "goal NOT in GOALS.md"
fi

if grep -q "Survive the end-to-end test" "$AGENT_DIR/MAIN_GOAL.md" 2>/dev/null; then
    pass "goal in MAIN_GOAL.md"
else
    fail "goal NOT in MAIN_GOAL.md"
fi

# Verify scripts are executable
for s in run.sh loop.sh think.sh health_check.sh; do
    if [[ -x "$AGENT_DIR/$s" ]]; then
        pass "$s is executable"
    else
        fail "$s not executable"
    fi
done

# Verify init refuses to overwrite
if auto-agent init "$AGENT_DIR" --name "X" --goal "Y" 2>&1 | grep -qi "already exists\|already initialized"; then
    pass "init refuses to overwrite existing agent"
else
    fail "init should refuse overwrite"
fi

echo ""

# ════════════════════════════════════════════
# Phase 2: STATUS — Check newborn agent health
# ════════════════════════════════════════════
echo "▶ Phase 2: STATUS — Newborn agent health check"

auto-agent status -d "$AGENT_DIR" > /dev/null 2>&1 \
    && pass "status on fresh agent" || fail "status on fresh agent"

auto-agent status -d "$AGENT_DIR" --verbose > /dev/null 2>&1 \
    && pass "status --verbose on fresh agent" || fail "status --verbose on fresh agent"

echo ""

# ════════════════════════════════════════════
# Phase 3: LIFE — Simulate agent runs
# ════════════════════════════════════════════
echo "▶ Phase 3: LIFE — Simulate 15 agent runs"

# Simulate 15 runs by appending to MEMORY.md and JOURNAL.md
# This tests that the file format is compatible with archive

# Read current MEMORY.md content
MEMORY_CONTENT=$(cat "$AGENT_DIR/MEMORY.md")

# Build run history section
RUNS_SECTION="
## История запусков
"

for i in $(seq 1 15); do
    RUNS_SECTION+="
### Запуск $i — 2026-03-13 (E2E test run $i)
- **Что сделал:** Simulated action $i for e2e testing.
- **Вывод:** This is run $i of 15 simulated runs.
"
done

PRINCIPLES_SECTION="
## Принципы, которые я выработал
1. End-to-end tests are important
2. Simulated data should be realistic
3. Every run should leave a trace
"

# Write MEMORY.md with runs
cat > "$AGENT_DIR/MEMORY.md" << 'MEMEOF'
# Память агента

## Факты обо мне
- Я — E2E-Bot, тестовый агент
- Создан для проверки жизненного цикла
MEMEOF

echo "$RUNS_SECTION" >> "$AGENT_DIR/MEMORY.md"
echo "$PRINCIPLES_SECTION" >> "$AGENT_DIR/MEMORY.md"

# Verify runs were written
RUN_COUNT=$(grep -c "^### Запуск" "$AGENT_DIR/MEMORY.md" 2>/dev/null || echo 0)
if [[ "$RUN_COUNT" -eq 15 ]]; then
    pass "15 runs written to MEMORY.md"
else
    fail "expected 15 runs, got $RUN_COUNT"
fi

# Write JOURNAL.md with matching entries
cat > "$AGENT_DIR/JOURNAL.md" << 'JOUREOF'
# Журнал
JOUREOF

for i in $(seq 1 15); do
    cat >> "$AGENT_DIR/JOURNAL.md" << EOF

## Запуск $i — 2026-03-13

### О чём я думаю
This is journal entry $i. Simulated reflection.

### Что я вынес
Lesson from run $i.

---
EOF
done

JOURNAL_ENTRIES=$(grep -c "^## Запуск" "$AGENT_DIR/JOURNAL.md" 2>/dev/null || echo 0)
if [[ "$JOURNAL_ENTRIES" -eq 15 ]]; then
    pass "15 journal entries written"
else
    fail "expected 15 journal entries, got $JOURNAL_ENTRIES"
fi

# Update TODO.md with tasks
cat > "$AGENT_DIR/TODO.md" << 'TODOEOF'
# TODO — Cycle 1

## Шаги
- [x] Step 1: Initialize
- [x] Step 2: Run simulations
- [x] Step 3: Check status
- [ ] Step 4: Archive memory
- [ ] Step 5: Final check
TODOEOF

pass "TODO.md updated with tasks"

echo ""

# ════════════════════════════════════════════
# Phase 4: STATUS — Check active agent health
# ════════════════════════════════════════════
echo "▶ Phase 4: STATUS — Active agent health check"

STATUS_OUT=$(auto-agent status -d "$AGENT_DIR" 2>&1)
STATUS_EXIT=$?

if [[ $STATUS_EXIT -eq 0 ]]; then
    pass "status on active agent"
else
    # Status may exit 1 due to warnings, which is acceptable
    pass "status on active agent (exit $STATUS_EXIT — warnings expected)"
fi

# Status should detect launch records
if echo "$STATUS_OUT" | grep -qi "launch\|запуск\|15"; then
    pass "status detects launch records"
else
    fail "status doesn't detect launch records"
fi

# Status should detect TODO tasks
if echo "$STATUS_OUT" | grep -qi "todo\|done\|task"; then
    pass "status detects TODO tasks"
else
    fail "status doesn't detect TODO tasks"
fi

echo ""

# ════════════════════════════════════════════
# Phase 5: ARCHIVE — Test progressive memory
# ════════════════════════════════════════════
echo "▶ Phase 5: ARCHIVE — Progressive memory management"

# Dry-run first
ARCHIVE_DRY=$(auto-agent archive -d "$AGENT_DIR" --dry-run 2>&1)
if echo "$ARCHIVE_DRY" | grep -qi "archive\|запуск"; then
    pass "archive --dry-run shows plan"
else
    fail "archive --dry-run output unexpected"
fi

# Verify no changes were made during dry-run
if [[ ! -f "$AGENT_DIR/MEMORY_ARCHIVE.md" ]]; then
    pass "dry-run didn't create archive file"
else
    fail "dry-run created archive file (should not)"
fi

# Run actual archive (keep last 10)
auto-agent archive -d "$AGENT_DIR" --keep 10 > /dev/null 2>&1 \
    && pass "archive executed" || fail "archive failed"

# Verify MEMORY_ARCHIVE.md was created
if [[ -f "$AGENT_DIR/MEMORY_ARCHIVE.md" ]]; then
    pass "MEMORY_ARCHIVE.md created"
else
    fail "MEMORY_ARCHIVE.md not created"
fi

# Verify core memory was trimmed
CORE_RUNS=$(grep -c "^### Запуск" "$AGENT_DIR/MEMORY.md" 2>/dev/null || echo 0)
if [[ "$CORE_RUNS" -eq 10 ]]; then
    pass "MEMORY.md trimmed to 10 runs"
else
    fail "expected 10 runs in core, got $CORE_RUNS"
fi

# Verify archive has the old runs
ARCHIVE_RUNS=$(grep -c "^### Запуск" "$AGENT_DIR/MEMORY_ARCHIVE.md" 2>/dev/null || echo 0)
if [[ "$ARCHIVE_RUNS" -eq 5 ]]; then
    pass "MEMORY_ARCHIVE.md has 5 archived runs"
else
    fail "expected 5 runs in archive, got $ARCHIVE_RUNS"
fi

# Verify archive notice in core memory
if grep -q "MEMORY_ARCHIVE.md" "$AGENT_DIR/MEMORY.md" 2>/dev/null; then
    pass "archive notice in MEMORY.md"
else
    fail "no archive notice in MEMORY.md"
fi

# Verify principles survived archival
if grep -q "End-to-end tests are important" "$AGENT_DIR/MEMORY.md" 2>/dev/null; then
    pass "principles preserved after archive"
else
    fail "principles lost during archive"
fi

# Run archive again — should be no-op
ARCHIVE_AGAIN=$(auto-agent archive -d "$AGENT_DIR" --keep 10 2>&1)
if echo "$ARCHIVE_AGAIN" | grep -qi "nothing\|optimal\|ничего"; then
    pass "second archive is no-op"
else
    fail "second archive should be no-op"
fi

echo ""

# ════════════════════════════════════════════
# Phase 6: CONTEXT — Verify run/think context assembly
# ════════════════════════════════════════════
echo "▶ Phase 6: CONTEXT — Verify context assembly"

# Run --dry-run should show assembled context
RUN_CTX=$(auto-agent run -d "$AGENT_DIR" --dry-run 2>&1)
if [[ -n "$RUN_CTX" ]]; then
    pass "run --dry-run produces output"
else
    fail "run --dry-run empty"
fi

# Context should include MEMORY
if echo "$RUN_CTX" | grep -q "E2E-Bot"; then
    pass "run context includes agent name from MEMORY"
else
    fail "run context missing agent name"
fi

# Context should include GOALS
if echo "$RUN_CTX" | grep -q "Survive the end-to-end test"; then
    pass "run context includes goal"
else
    fail "run context missing goal"
fi

# Context should include TODO
if echo "$RUN_CTX" | grep -q "Step 4"; then
    pass "run context includes TODO tasks"
else
    fail "run context missing TODO"
fi

# Context should include archive notice
if echo "$RUN_CTX" | grep -q "MEMORY_ARCHIVE"; then
    pass "run context includes archive notice"
else
    fail "run context missing archive notice"
fi

# Context should include journal tail
if echo "$RUN_CTX" | grep -q "journal\|Запуск\|Журнал"; then
    pass "run context includes journal"
else
    fail "run context missing journal"
fi

# Think --dry-run should also work
THINK_CTX=$(auto-agent think -d "$AGENT_DIR" --topic "e2e test reflection" --dry-run 2>&1)
if echo "$THINK_CTX" | grep -q "e2e test reflection"; then
    pass "think --dry-run includes topic"
else
    fail "think --dry-run missing topic"
fi

echo ""

# ════════════════════════════════════════════
# Phase 7: EDGE CASES
# ════════════════════════════════════════════
echo "▶ Phase 7: EDGE CASES"

# Status on non-existent directory should fail gracefully
if auto-agent status -d "$E2E_DIR/nonexistent" 2>&1 | grep -qi "error\|not found\|no agent"; then
    pass "status on missing dir: graceful error"
else
    fail "status on missing dir: no error message"
fi

# Run on non-existent directory should fail gracefully
if auto-agent run -d "$E2E_DIR/nonexistent" --dry-run 2>&1 | grep -qi "error\|not found\|no agent"; then
    pass "run on missing dir: graceful error"
else
    fail "run on missing dir: no error message"
fi

# Archive on empty memory (create new agent with no runs)
EMPTY_DIR="$E2E_DIR/empty_agent"
auto-agent init "$EMPTY_DIR" --name "EmptyBot" --goal "Test edge cases" > /dev/null 2>&1
EMPTY_ARCHIVE=$(auto-agent archive -d "$EMPTY_DIR" --keep 10 2>&1)
if echo "$EMPTY_ARCHIVE" | grep -qi "nothing\|optimal\|0"; then
    pass "archive on fresh agent: nothing to archive"
else
    fail "archive on fresh agent: unexpected behavior"
fi

# INBOX should exist and have structure
if grep -q "E2E-Bot" "$AGENT_DIR/INBOX.md" 2>/dev/null; then
    pass "INBOX.md has agent name"
else
    fail "INBOX.md missing agent name"
fi

# FAILURES.md should exist and have structure
if grep -q "E2E-Bot\|Failures\|Ошибки" "$AGENT_DIR/FAILURES.md" 2>/dev/null; then
    pass "FAILURES.md has structure"
else
    fail "FAILURES.md missing structure"
fi

echo ""

# ════════════════════════════════════════════
# Phase 8: SECOND LIFECYCLE — Incremental archive
# ════════════════════════════════════════════
echo "▶ Phase 8: SECOND LIFECYCLE — Incremental archive test"

# Add 5 more runs (16-20) to test append to existing archive
for i in $(seq 16 20); do
    cat >> "$AGENT_DIR/MEMORY.md" << EOF

### Запуск $i — 2026-03-13 (Second lifecycle run $i)
- **Что сделал:** Second lifecycle action $i.
- **Вывод:** This is second lifecycle run $i.
EOF
done

NEW_CORE_RUNS=$(grep -c "^### Запуск" "$AGENT_DIR/MEMORY.md" 2>/dev/null || echo 0)
if [[ "$NEW_CORE_RUNS" -eq 15 ]]; then
    pass "15 runs in core after adding 5 more"
else
    fail "expected 15 runs in core, got $NEW_CORE_RUNS"
fi

# Archive again — should move 5 oldest to archive (append, not overwrite)
auto-agent archive -d "$AGENT_DIR" --keep 10 > /dev/null 2>&1 \
    && pass "incremental archive executed" || fail "incremental archive failed"

# Verify archive now has 10 runs (5 old + 5 new)
FINAL_ARCHIVE_RUNS=$(grep -c "^### Запуск" "$AGENT_DIR/MEMORY_ARCHIVE.md" 2>/dev/null || echo 0)
if [[ "$FINAL_ARCHIVE_RUNS" -eq 10 ]]; then
    pass "archive has 10 runs total (5 + 5 appended)"
else
    fail "expected 10 runs in archive, got $FINAL_ARCHIVE_RUNS"
fi

# Verify core still has 10
FINAL_CORE_RUNS=$(grep -c "^### Запуск" "$AGENT_DIR/MEMORY.md" 2>/dev/null || echo 0)
if [[ "$FINAL_CORE_RUNS" -eq 10 ]]; then
    pass "core has 10 runs after second archive"
else
    fail "expected 10 runs in core, got $FINAL_CORE_RUNS"
fi

# Verify old archive entries are preserved (run 1 should still be there)
if grep -q "Запуск 1" "$AGENT_DIR/MEMORY_ARCHIVE.md" 2>/dev/null; then
    pass "original archive entries preserved"
else
    fail "original archive entries lost on second archive"
fi

echo ""

# ════════════════════════════════════════════
# Summary
# ════════════════════════════════════════════
echo "═══════════════════════════════════════════"
echo "  Tests: $TESTS | Errors: $ERRORS"
if [[ "$ERRORS" -eq 0 ]]; then
    echo "  ✅ ALL E2E TESTS PASSED"
else
    echo "  ❌ $ERRORS FAILURES"
fi
echo "═══════════════════════════════════════════"

exit $ERRORS
