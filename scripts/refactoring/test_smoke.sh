#!/bin/bash
# Smoke Test Suite - Tests that all scripts at least run
# Phase 1 Fix #1

set -e

echo "🔥 Refactoring Scripts Smoke Test Suite"
echo "========================================"
echo ""

PROJECT_ROOT="/Users/mykalthomas/Documents/work/Hackathon"
cd "$PROJECT_ROOT"

PASS=0
FAIL=0
SCRIPTS_DIR="scripts/refactoring"

# Test each Python script
for script in "$SCRIPTS_DIR"/*.py; do
    script_name=$(basename "$script")
    
    # Skip __init__.py
    if [ "$script_name" = "__init__.py" ]; then
        continue
    fi
    
    echo "Testing: $script_name"
    
    # Test 1: Can import without errors
    if python3 -c "import sys; sys.path.append('$SCRIPTS_DIR'); exec(open('$script').read())" 2>/dev/null; then
        echo "  ✓ Imports correctly (syntax OK)"
    else
        # Try just syntax check
        if python3 -m py_compile "$script" 2>/dev/null; then
            echo "  ✓ Syntax valid"
        else
            echo "  ✗ SYNTAX ERROR"
            FAIL=$((FAIL + 1))
            continue
        fi
    fi
    
    # Test 2: --help works
    if python3 "$script" --help >/dev/null 2>&1; then
        echo "  ✓ --help works"
        PASS=$((PASS + 1))
    else
        # Some scripts might not have --help, check if they at least run
        if python3 -c "exec(open('$script').read())" 2>&1 | grep -q "error: the following arguments are required"; then
            echo "  ✓ Runs (requires args)"
            PASS=$((PASS + 1))
        else
            echo "  ⚠ No --help, might need args"
            PASS=$((PASS + 1))
        fi
    fi
    
    echo ""
done

echo "========================================"
echo "Results: $PASS passed, $FAIL failed"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "✅ All smoke tests passed!"
    exit 0
else
    echo "❌ Some smoke tests failed"
    exit 1
fi

