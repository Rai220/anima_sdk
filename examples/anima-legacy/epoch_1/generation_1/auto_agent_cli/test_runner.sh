#!/bin/bash
# ===========================================
# Auto Agent CLI — Full Test Suite
# ===========================================
# Run this script to install dependencies and
# execute all tests including integration tests.
#
# Usage: bash test_runner.sh
# ===========================================

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "╔════════════════════════════════════╗"
echo "║   Auto Agent CLI — Test Runner     ║"
echo "╚════════════════════════════════════╝"
echo ""

# Step 1: Install dependencies
echo "▶ Step 1: Installing dependencies..."
if command -v uv &>/dev/null; then
    echo "  Using uv (fast mode)"
    uv pip install click pytest 2>&1 | tail -3
    uv pip install -e "$SCRIPT_DIR" 2>&1 | tail -3
else
    echo "  Using pip3"
    pip3 install click pytest 2>&1 | tail -3
    pip3 install -e "$SCRIPT_DIR" 2>&1 | tail -3
fi
echo "  ✓ Dependencies installed"
echo ""

# Step 2: Syntax check
echo "▶ Step 2: Syntax check..."
python3 -m py_compile "$SCRIPT_DIR/src/auto_agent/__init__.py"
python3 -m py_compile "$SCRIPT_DIR/src/auto_agent/cli.py"
python3 -m py_compile "$SCRIPT_DIR/src/auto_agent/commands/init.py"
python3 -m py_compile "$SCRIPT_DIR/src/auto_agent/commands/run.py"
python3 -m py_compile "$SCRIPT_DIR/src/auto_agent/commands/think.py"
python3 -m py_compile "$SCRIPT_DIR/src/auto_agent/commands/status.py"
python3 -m py_compile "$SCRIPT_DIR/src/auto_agent/commands/learn.py"
python3 -m py_compile "$SCRIPT_DIR/src/auto_agent/commands/archive.py"
python3 -m py_compile "$SCRIPT_DIR/src/auto_agent/commands/utils.py"
python3 -m py_compile "$SCRIPT_DIR/src/auto_agent/commands/__init__.py"
echo "  ✓ All files compile"
echo ""

# Step 3: Unit and integration tests (pytest)
echo "▶ Step 3: Running pytest..."
cd "$SCRIPT_DIR"
python3 -m pytest tests/ -v --tb=short
echo ""

# Step 4: CLI integration test
echo "▶ Step 4: CLI integration test..."
echo "  Testing --version..."
auto-agent --version

echo "  Testing --help..."
auto-agent --help > /dev/null

echo "  Testing init..."
TMPDIR=$(mktemp -d)
auto-agent init "$TMPDIR/test_agent" --name "TestBot" --goal "Test the CLI"
echo ""

echo "  Testing status..."
auto-agent status -d "$TMPDIR/test_agent"
echo ""

echo "  Testing run --dry-run..."
auto-agent run -d "$TMPDIR/test_agent" --dry-run | head -10
echo "  (...truncated)"
echo ""

echo "  Testing think --dry-run..."
auto-agent think -d "$TMPDIR/test_agent" --dry-run | head -10
echo "  (...truncated)"
echo ""

# Step 5: Verify created files
echo "▶ Step 5: Verifying created agent..."
EXPECTED_FILES="MEMORY.md TODO.md GOALS.md JOURNAL.md KNOWLEDGE.md WHO_AM_I.md AGENTS.md MAIN_GOAL.md INBOX.md FAILURES.md run.sh loop.sh think.sh health_check.sh"
PASS=0
FAIL=0
for f in $EXPECTED_FILES; do
    if [[ -f "$TMPDIR/test_agent/$f" ]]; then
        PASS=$((PASS + 1))
    else
        echo "  ✗ Missing: $f"
        FAIL=$((FAIL + 1))
    fi
done
echo "  Files: $PASS present, $FAIL missing"

# Check substitution
if grep -q "TestBot" "$TMPDIR/test_agent/MEMORY.md"; then
    echo "  ✓ Agent name substituted in MEMORY.md"
else
    echo "  ✗ Agent name NOT found in MEMORY.md"
    FAIL=$((FAIL + 1))
fi

if grep -q "Test the CLI" "$TMPDIR/test_agent/GOALS.md"; then
    echo "  ✓ Goal substituted in GOALS.md"
else
    echo "  ✗ Goal NOT found in GOALS.md"
    FAIL=$((FAIL + 1))
fi

# Cleanup
rm -rf "$TMPDIR"

# Summary
echo ""
echo "═══════════════════════════════════"
if [[ "$FAIL" -eq 0 ]]; then
    echo "  ✅ ALL TESTS PASSED"
else
    echo "  ❌ $FAIL issues found"
fi
echo "═══════════════════════════════════"
