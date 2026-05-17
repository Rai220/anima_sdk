#!/bin/bash
# health_check.sh — Agent self-assessment
# Usage: bash health_check.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ISSUES=0
WARNINGS=0
TOTAL=0
PASSED=0

check_file() {
    local file="$1"
    local required="$2"
    local min_size="${3:-20}"
    TOTAL=$((TOTAL + 1))

    if [[ -f "$SCRIPT_DIR/$file" ]]; then
        local size
        size=$(wc -c < "$SCRIPT_DIR/$file" | tr -d ' ')
        if [[ "$size" -gt "$min_size" ]]; then
            echo "  OK  $file ($size bytes)"
            PASSED=$((PASSED + 1))
        else
            echo "  WARN $file (only $size bytes)"
            WARNINGS=$((WARNINGS + 1))
            PASSED=$((PASSED + 1))
        fi
    elif [[ "$required" == "required" ]]; then
        echo "  FAIL $file (missing!)"
        ISSUES=$((ISSUES + 1))
    else
        echo "  SKIP $file (optional, not created yet)"
        PASSED=$((PASSED + 1))
    fi
}

echo "=== Agent Health Check ==="
echo "Directory: $SCRIPT_DIR"
echo ""

echo "Core files:"
check_file "MEMORY.md" required
check_file "TODO.md" required
check_file "GOALS.md" required
check_file "JOURNAL.md" required
check_file "MAIN_GOAL.md" required
check_file "AGENTS.md" required
echo ""

echo "Optional files:"
check_file "KNOWLEDGE.md" optional
check_file "WHO_AM_I.md" optional
check_file "INBOX.md" optional
check_file "DESIRES.md" optional
check_file "FAILURES.md" optional
echo ""

echo "Scripts:"
for script in run.sh think.sh loop.sh health_check.sh; do
    TOTAL=$((TOTAL + 1))
    if [[ -x "$SCRIPT_DIR/$script" ]]; then
        echo "  OK  $script (executable)"
        PASSED=$((PASSED + 1))
    elif [[ -f "$SCRIPT_DIR/$script" ]]; then
        echo "  WARN $script (exists but not executable)"
        WARNINGS=$((WARNINGS + 1))
        PASSED=$((PASSED + 1))
    else
        echo "  SKIP $script"
        PASSED=$((PASSED + 1))
    fi
done
echo ""

# Summary
PCT=$((PASSED * 100 / TOTAL))
echo "Score: $PASSED/$TOTAL ($PCT%)"
[[ "$ISSUES" -gt 0 ]] && echo "Issues: $ISSUES"
[[ "$WARNINGS" -gt 0 ]] && echo "Warnings: $WARNINGS"
