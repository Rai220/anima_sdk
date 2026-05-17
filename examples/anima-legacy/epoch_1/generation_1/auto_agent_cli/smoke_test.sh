#!/bin/bash
# ===========================================
# Auto Agent CLI — Smoke Test in Clean Env
# ===========================================
# Creates a fresh venv, installs the package,
# and tests all commands end-to-end.
#
# Usage: bash smoke_test.sh
# ===========================================

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "╔════════════════════════════════════════╗"
echo "║   Auto Agent CLI — Smoke Test          ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Step 1: Create clean venv
SMOKE_DIR="$SCRIPT_DIR/_smoke_env"
echo "▶ Step 1: Creating clean virtual environment..."
rm -rf "$SMOKE_DIR"
python3 -m venv "$SMOKE_DIR"
source "$SMOKE_DIR/bin/activate"
echo "  Python: $(python --version)"
echo "  ✓ Clean venv created"
echo ""

# Step 2: Install package
echo "▶ Step 2: Installing auto-agent..."
pip install -e "$SCRIPT_DIR" 2>&1 | tail -5
echo "  ✓ Installed"
echo ""

ERRORS=0
TESTS=0
pass() { TESTS=$((TESTS + 1)); echo "  ✓ $1"; }
fail() { TESTS=$((TESTS + 1)); ERRORS=$((ERRORS + 1)); echo "  ✗ $1"; }

# Step 3: Test --help and --version
echo "▶ Step 3: Basic commands..."
auto-agent --version && pass "--version" || fail "--version"
auto-agent --help > /dev/null && pass "--help" || fail "--help"

# Check all 6 commands appear in help
for cmd in init run think status learn archive; do
    if auto-agent --help 2>/dev/null | grep -q "$cmd"; then
        pass "help lists '$cmd'"
    else
        fail "help missing '$cmd'"
    fi
done
echo ""

# Step 4: Test init
echo "▶ Step 4: Init command..."
TEST_DIR="$SMOKE_DIR/test_agent"
auto-agent init "$TEST_DIR" --name "SmokeBot" --goal "Test smoke" && pass "init" || fail "init"

EXPECTED_FILES="MEMORY.md TODO.md GOALS.md JOURNAL.md KNOWLEDGE.md WHO_AM_I.md AGENTS.md MAIN_GOAL.md INBOX.md FAILURES.md run.sh loop.sh think.sh health_check.sh"
for f in $EXPECTED_FILES; do
    if [[ -f "$TEST_DIR/$f" ]]; then
        pass "file: $f"
    else
        fail "missing: $f"
    fi
done

# Check substitutions
if grep -q "SmokeBot" "$TEST_DIR/MEMORY.md" 2>/dev/null; then
    pass "name substituted in MEMORY.md"
else
    fail "name NOT substituted in MEMORY.md"
fi

if grep -q "Test smoke" "$TEST_DIR/GOALS.md" 2>/dev/null; then
    pass "goal substituted in GOALS.md"
else
    fail "goal NOT substituted in GOALS.md"
fi
echo ""

# Step 5: Test status
echo "▶ Step 5: Status command..."
auto-agent status -d "$TEST_DIR" && pass "status" || fail "status"
auto-agent status -d "$TEST_DIR" --verbose > /dev/null && pass "status --verbose" || fail "status --verbose"
echo ""

# Step 6: Test run/think --dry-run
echo "▶ Step 6: Run and Think (dry-run)..."
auto-agent run -d "$TEST_DIR" --dry-run > /dev/null 2>&1 && pass "run --dry-run" || fail "run --dry-run"
auto-agent think -d "$TEST_DIR" --dry-run > /dev/null 2>&1 && pass "think --dry-run" || fail "think --dry-run"
auto-agent think -d "$TEST_DIR" --topic "test" --dry-run > /dev/null 2>&1 && pass "think --topic --dry-run" || fail "think --topic --dry-run"
echo ""

# Step 7: Test learn
echo "▶ Step 7: Learn command..."
auto-agent learn -d "$TEST_DIR" --help > /dev/null && pass "learn --help" || fail "learn --help"
echo ""

# Step 8: Test archive
echo "▶ Step 8: Archive command..."
auto-agent archive -d "$TEST_DIR" --dry-run > /dev/null 2>&1 && pass "archive --dry-run" || fail "archive --dry-run"
echo ""

# Step 9: Run pytest
echo "▶ Step 9: Running pytest..."
pip install pytest > /dev/null 2>&1
python -m pytest "$SCRIPT_DIR/tests/" -v --tb=short 2>&1
PYTEST_EXIT=$?
if [[ $PYTEST_EXIT -eq 0 ]]; then
    pass "pytest"
else
    fail "pytest (exit code: $PYTEST_EXIT)"
fi
echo ""

# Cleanup
echo "▶ Cleanup..."
rm -rf "$SMOKE_DIR"
echo "  ✓ Clean"
echo ""

# Summary
echo "═══════════════════════════════════════"
echo "  Tests: $TESTS | Errors: $ERRORS"
if [[ "$ERRORS" -eq 0 ]]; then
    echo "  ✅ ALL SMOKE TESTS PASSED"
else
    echo "  ❌ $ERRORS FAILURES"
fi
echo "═══════════════════════════════════════"

deactivate 2>/dev/null || true
exit $ERRORS
