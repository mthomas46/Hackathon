# ✅ Reality Validation Protocol - Preventing Hallucination & Context Drift

**Version**: 1.0.0  
**Created**: October 9, 2025  
**Status**: Active  
**Purpose**: Ensure AI agent's believed state matches actual reality

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [The Hallucination Problem](#the-hallucination-problem)
3. [Validation Triggers](#validation-triggers)
4. [Reality Checks](#reality-checks)
5. [Incomplete Thought Detection](#incomplete-thought-detection)
6. [Drift Detection](#drift-detection)
7. [Remediation](#remediation)

---

## 🎯 Overview

### The Problem

**AI agents can believe they've completed work they haven't**:

❌ Think a step is done when it's not  
❌ Believe files exist that don't  
❌ Remember tests passing that failed  
❌ Think code was committed when it wasn't  
❌ Skip critical sub-steps without realizing  

### The Solution

**Continuous reality validation**:

✅ Verify filesystem matches expectations  
✅ Verify tests actually pass  
✅ Verify deliverables actually exist  
✅ Verify git commits match believed state  
✅ Verify step completion criteria met  

---

## 🚨 The Hallucination Problem

### Common Hallucinations

**Type 1: File Existence Hallucination**
```python
# AI believes:
"I created services/doc-store/domain/entities/document.py"

# Reality:
$ ls services/doc-store/domain/entities/document.py
No such file or directory

# Why: AI thought about creating it but didn't actually write it
```

**Type 2: Test Pass Hallucination**
```python
# AI believes:
"All 25 tests passing"

# Reality:
$ pytest
FAILED tests/unit/domain/test_document.py::test_create - AssertionError
20 passed, 5 failed

# Why: AI saw passing tests earlier, doesn't realize code changes broke them
```

**Type 3: Step Completion Hallucination**
```python
# AI believes:
"Phase 3.2 Domain Layer complete"

# Reality:
$ ls services/doc-store/domain/entities/
Only 8 entities (expected 15)

# Why: AI updated context but didn't finish implementing all entities
```

**Type 4: Git Commit Hallucination**
```python
# AI believes:
"Committed Phase 3 work"

# Reality:
$ git log -1
Last commit: Phase 2 complete (2 hours ago)

# Why: AI planned to commit but didn't execute git command
```

**Type 5: Completeness Hallucination**
```python
# AI believes:
"Application layer implemented"

# Reality:
$ ls services/doc-store/application/
Empty directory

# Why: AI moved on to next step before finishing current step
```

### Why Hallucinations Happen

1. **Interrupted Execution**: AI starts a step but gets interrupted
2. **Context Confusion**: Long conversation, AI confuses intent with action
3. **Optimistic Updating**: Updates context before validating work done
4. **Lack of Verification**: Doesn't check that action succeeded
5. **Step Drift**: Gradually drifts from actual state

---

## ⏰ Validation Triggers

### Mandatory Validation Points

**After Every Step** (Non-negotiable):
```bash
python3 scripts/refactoring/validate_step_reality.py \
  --service doc-store \
  --step "3.2.1"
```

**Before Updating Context** (Prevent false state):
```bash
# WRONG:
update_execution_context(step="3.2.1", status="completed")  # Optimistic
validate_step()  # Too late

# RIGHT:
validate_step("3.2.1")  # Check reality first
if validation_passed:
    update_execution_context(step="3.2.1", status="completed")  # Then update
```

**Before Phase Transition** (Critical gate):
```bash
python3 scripts/refactoring/self_review.py doc-store --phase 3
# Only proceed if PASSED
```

**Before Git Commit** (Verify work exists):
```bash
python3 scripts/refactoring/pre_commit_validation.py
# Only commit if all checks pass
```

**After Context Recovery** (Validate continuity):
```bash
python3 scripts/refactoring/recover_session.py
python3 scripts/refactoring/validate_context_reality.py  # Verify recovered state
```

**Every 30 Minutes** (Continuous drift detection):
```bash
# Automated check
python3 scripts/refactoring/check_context_drift.py
```

---

## ✅ Reality Checks

### Level 1: Filesystem Reality Check

**Purpose**: Verify files exist as expected

```bash
#!/bin/bash
# validate_filesystem.sh

SERVICE=$1
PHASE=$2

echo "🔍 Filesystem Reality Check for $SERVICE (Phase $PHASE)"

# Phase 1: Audit deliverables
if [ "$PHASE" = "1" ]; then
  [ -f "reports/${SERVICE}_audit.json" ] || echo "❌ Missing: audit report"
  [ -f "services/${SERVICE}/gap_analysis.md" ] || echo "❌ Missing: gap analysis"
fi

# Phase 2: Design deliverables
if [ "$PHASE" = "2" ]; then
  [ -d "services/${SERVICE}/design" ] || echo "❌ Missing: design directory"
  [ -f "services/${SERVICE}/design/domain_model.md" ] || echo "❌ Missing: domain model"
  [ -f "services/${SERVICE}/design/openapi_v2.yaml" ] || echo "❌ Missing: OpenAPI spec"
fi

# Phase 3: Implementation deliverables
if [ "$PHASE" = "3" ]; then
  [ -d "services/${SERVICE}/domain" ] || echo "❌ Missing: domain layer"
  [ -d "services/${SERVICE}/application" ] || echo "❌ Missing: application layer"
  [ -d "services/${SERVICE}/infrastructure" ] || echo "❌ Missing: infrastructure layer"
  [ -d "services/${SERVICE}/presentation" ] || echo "❌ Missing: presentation layer"
  
  ENTITY_COUNT=$(find "services/${SERVICE}/domain/entities" -name "*.py" 2>/dev/null | wc -l)
  [ $ENTITY_COUNT -ge 2 ] || echo "❌ Too few entities: $ENTITY_COUNT"
fi

# Phase 5: Documentation deliverables
if [ "$PHASE" = "5" ]; then
  README="services/${SERVICE}/README.md"
  [ -f "$README" ] || echo "❌ Missing: README"
  
  if [ -f "$README" ]; then
    SIZE=$(wc -c < "$README")
    [ $SIZE -ge 5000 ] || echo "⚠️ README too small: $SIZE bytes (need 5KB+)"
  fi
fi

echo "✅ Filesystem check complete"
```

### Level 2: Test Reality Check

**Purpose**: Verify tests actually pass

```bash
#!/bin/bash
# validate_tests.sh

SERVICE=$1

echo "🔍 Test Reality Check for $SERVICE"

cd "services/$SERVICE" || exit 1

# Run tests
echo "Running pytest..."
pytest --tb=short --quiet

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ All tests passing"
  
  # Check coverage
  pytest --cov --cov-report=term --quiet | grep "TOTAL"
  
else
  echo "❌ Tests FAILING (exit code: $EXIT_CODE)"
  echo "⚠️ Do NOT mark step complete until tests pass"
  exit 1
fi
```

### Level 3: Coverage Reality Check

**Purpose**: Verify coverage meets target

```python
#!/usr/bin/env python3
# validate_coverage.py

import subprocess
import json
import sys

def check_coverage(service: str, target: float = 80.0):
    """Verify test coverage meets target"""
    
    # Run coverage
    result = subprocess.run(
        ["pytest", "--cov", "--cov-report=json", "--quiet"],
        cwd=f"services/{service}",
        capture_output=True
    )
    
    # Read coverage report
    coverage_file = f"services/{service}/coverage.json"
    try:
        with open(coverage_file) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Coverage report not found: {coverage_file}")
        return False
    
    total_coverage = data["totals"]["percent_covered"]
    
    print(f"📊 Coverage: {total_coverage:.1f}%")
    
    if total_coverage >= target:
        print(f"✅ Meets target ({target}%)")
        return True
    else:
        print(f"❌ Below target ({target}%)")
        print(f"⚠️ Need {target - total_coverage:.1f}% more coverage")
        return False

if __name__ == "__main__":
    service = sys.argv[1]
    passed = check_coverage(service)
    sys.exit(0 if passed else 1)
```

### Level 4: Git Reality Check

**Purpose**: Verify git state matches expectations

```bash
#!/bin/bash
# validate_git.sh

SERVICE=$1

echo "🔍 Git Reality Check for $SERVICE"

# Check for uncommitted changes
if ! git diff --quiet; then
  echo "⚠️ Uncommitted changes exist"
  git status --short
  echo ""
fi

# Check last commit
LAST_COMMIT=$(git log -1 --oneline -- "services/$SERVICE")
echo "📝 Last commit affecting $SERVICE:"
echo "   $LAST_COMMIT"
echo ""

# Check if current work is committed
UNCOMMITTED=$(git diff --name-only -- "services/$SERVICE" | wc -l)
if [ $UNCOMMITTED -gt 0 ]; then
  echo "⚠️ $UNCOMMITTED uncommitted file(s) in services/$SERVICE/"
  echo "💡 Consider committing before marking step complete"
fi

echo "✅ Git check complete"
```

### Level 5: Deliverable Completeness Check

**Purpose**: Verify deliverables are not just present but COMPLETE

```python
#!/usr/bin/env python3
# validate_deliverable_completeness.py

from pathlib import Path
import sys

def check_file_completeness(filepath: Path) -> tuple[bool, str]:
    """Check if file is actually complete (not skeleton/TODO)"""
    
    if not filepath.exists():
        return False, "File doesn't exist"
    
    content = filepath.read_text()
    
    # Check for skeleton markers
    skeleton_markers = [
        "TODO: Implement",
        "pass  # TODO",
        "raise NotImplementedError",
        "# Placeholder",
        "...  # To be implemented"
    ]
    
    for marker in skeleton_markers:
        if marker in content:
            return False, f"Contains skeleton code: '{marker}'"
    
    # Check minimum content
    lines = [l for l in content.split("\n") if l.strip() and not l.strip().startswith("#")]
    if len(lines) < 10:
        return False, f"Too few lines: {len(lines)} (seems like skeleton)"
    
    return True, "Complete"

def check_domain_layer(service_path: Path) -> bool:
    """Check domain layer is complete, not skeleton"""
    
    domain_path = service_path / "domain"
    if not domain_path.exists():
        print("❌ Domain layer missing")
        return False
    
    entity_files = list((domain_path / "entities").glob("*.py"))
    if len(entity_files) < 2:
        print(f"❌ Too few entities: {len(entity_files)}")
        return False
    
    print(f"📁 Checking {len(entity_files)} entity files...")
    
    incomplete = []
    for entity_file in entity_files:
        is_complete, reason = check_file_completeness(entity_file)
        if not is_complete:
            incomplete.append(f"{entity_file.name}: {reason}")
    
    if incomplete:
        print("❌ Incomplete entities found:")
        for item in incomplete:
            print(f"   - {item}")
        return False
    
    print("✅ All entities complete")
    return True
```

---

## 🔍 Incomplete Thought Detection

### The Incomplete Thought Problem

**Scenario**: AI starts a task but doesn't finish

```python
# AI Agent's Plan:
"I will implement the Document entity with 5 methods"

# AI's Actual Work:
# 1. Creates file ✅
# 2. Writes class definition ✅
# 3. Implements 2 methods ✅
# 4. Gets interrupted ❌
# 5. Never implements other 3 methods ❌

# AI's Belief:
"Document entity implemented" ✅  # WRONG

# Reality:
"Document entity partially implemented" ⚠️  # TRUE
```

### Detection Mechanism

**Pre-Completion Checklist**:

```yaml
before_marking_complete:
  - check: "All planned files created?"
    validate: "ls -la expected/files/"
  
  - check: "All tests pass?"
    validate: "pytest"
  
  - check: "Coverage meets target?"
    validate: "pytest --cov"
  
  - check: "No TODOs in code?"
    validate: "grep -r 'TODO' services/<service>/"
  
  - check: "Linting passes?"
    validate: "flake8 services/<service>/"
  
  - check: "All step deliverables exist?"
    validate: "check_deliverables_list()"
```

**Automated Detection**:

```python
def detect_incomplete_thought(step_id: str, service: str) -> tuple[bool, list]:
    """Detect if step is truly complete or just thought to be"""
    
    issues = []
    
    # 1. Check required deliverables exist
    required = get_step_deliverables(step_id)
    for deliverable in required:
        if not exists(deliverable):
            issues.append(f"Missing deliverable: {deliverable}")
    
    # 2. Check tests pass
    test_result = run_tests(service)
    if not test_result.passed:
        issues.append(f"Tests failing: {test_result.failures}")
    
    # 3. Check no skeleton code
    has_skeletons = check_for_skeletons(service)
    if has_skeletons:
        issues.append("Skeleton code found (not implemented)")
    
    # 4. Check coverage
    coverage = get_coverage(service)
    target_coverage = get_target_coverage(step_id)
    if coverage < target_coverage:
        issues.append(f"Coverage {coverage}% < target {target_coverage}%")
    
    is_complete = len(issues) == 0
    return is_complete, issues
```

### Enforced Validation

**Rule**: **Cannot mark step complete without validation**

```python
# WRONG PATTERN:
def complete_step(step_id):
    # Do work...
    update_context(step_id, "completed")  # No validation!

# RIGHT PATTERN:
def complete_step(step_id):
    # Do work...
    
    # Validate BEFORE updating
    is_complete, issues = detect_incomplete_thought(step_id, service)
    
    if not is_complete:
        print(f"❌ Cannot mark complete - issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print("⚠️ Fix issues before proceeding")
        return False
    
    # Only update after validation passes
    update_context(step_id, "completed")
    return True
```

---

## 🌊 Drift Detection

### Context Drift Problem

**Drift**: Gradual divergence between believed state and actual state

```
Hour 0: Context = Reality (aligned)
Hour 1: Context = Reality (aligned)
Hour 2: Context slightly ahead of Reality (5% drift)
Hour 3: Context moderately ahead (15% drift)
Hour 4: Context significantly ahead (30% drift) ⚠️
Hour 5: Context completely wrong (50% drift) ❌
```

### Drift Causes

1. **Optimistic Context Updates**: Updating context before validating work
2. **Interrupted Execution**: Starting work, updating context, then getting interrupted
3. **Forgotten Validation**: Forgetting to run tests/checks
4. **Accumulated Small Errors**: Many tiny mistakes compound
5. **Context Overflow**: Old incorrect state persists

### Drift Detection Script

```python
#!/usr/bin/env python3
# check_context_drift.py

import json
from pathlib import Path

def calculate_drift_score(service: str) -> tuple[float, list]:
    """Calculate how much context has drifted from reality"""
    
    # Load context
    context_file = Path(f".ai_execution/context.json")
    context = json.loads(context_file.read_text())
    
    service_path = Path(f"services/{service}")
    
    discrepancies = []
    checks = 0
    failures = 0
    
    # Check 1: Phase matches reality
    checks += 1
    claimed_phase = context["current_state"]["phase"]
    actual_phase = infer_phase_from_codebase(service_path)
    if claimed_phase != actual_phase:
        failures += 1
        discrepancies.append(f"Phase mismatch: context='{claimed_phase}' reality='{actual_phase}'")
    
    # Check 2: Completed work actually exists
    checks += 1
    for work in context.get("completed_work", []):
        if "Phase" in work:
            phase_num = extract_phase_num(work)
            if not phase_completed(service_path, phase_num):
                failures += 1
                discrepancies.append(f"Claims completed but isn't: '{work}'")
    
    # Check 3: Tests actually pass
    checks += 1
    test_result = run_tests(service)
    if not test_result.passed and "tests passing" in str(context):
        failures += 1
        discrepancies.append(f"Context claims tests pass, but {test_result.failures} failing")
    
    # Check 4: Files exist that context claims
    checks += 1
    # Parse context for file mentions
    mentioned_files = extract_file_mentions(context)
    for filepath in mentioned_files:
        if not Path(filepath).exists():
            failures += 1
            discrepancies.append(f"Context mentions file that doesn't exist: {filepath}")
    
    # Calculate drift score (0 = perfect, 100 = completely wrong)
    drift_score = (failures / checks) * 100 if checks > 0 else 0
    
    return drift_score, discrepancies

def assess_drift(drift_score: float) -> str:
    """Assess severity of drift"""
    if drift_score == 0:
        return "✅ NO_DRIFT (perfect alignment)"
    elif drift_score < 10:
        return "🟢 MINIMAL_DRIFT (acceptable)"
    elif drift_score < 25:
        return "🟡 MODERATE_DRIFT (caution)"
    elif drift_score < 50:
        return "🟠 SIGNIFICANT_DRIFT (action needed)"
    else:
        return "🔴 CRITICAL_DRIFT (stop and reconcile)"
```

### Drift Remediation

**When drift detected**:

```bash
# 1. Stop immediately
echo "⚠️ Context drift detected - stopping work"

# 2. Run comprehensive reality check
python3 scripts/refactoring/validate_context_reality.py doc-store

# 3. Reconcile context with reality
python3 scripts/refactoring/reconcile_context.py doc-store

# 4. Verify reconciliation worked
python3 scripts/refactoring/check_context_drift.py doc-store
# Should show: "✅ NO_DRIFT"

# 5. Resume work
echo "✅ Context reconciled - safe to continue"
```

---

## 🔧 Remediation Procedures

### Procedure 1: Fix Hallucinated Completion

**Problem**: Step marked complete but isn't

```bash
# 1. Identify what's actually missing
python3 scripts/refactoring/validate_step_reality.py \
  --service doc-store \
  --step "3.2.1"

# Output:
# ❌ Missing: services/doc-store/domain/entities/audit.py
# ❌ Tests failing: 5 failures
# ❌ Coverage: 72% (target: 80%)

# 2. Update context to reflect reality
python3 scripts/refactoring/update_execution_context.py \
  --step "3.2.1" \
  --status "in_progress" \  # NOT completed
  --notes "Actually incomplete: need 3 more entities, fix 5 tests, increase coverage"

# 3. Complete the missing work
# ... implement missing entities ...
# ... fix tests ...
# ... add more tests for coverage ...

# 4. Validate AGAIN
python3 scripts/refactoring/validate_step_reality.py \
  --service doc-store \
  --step "3.2.1"

# Output should be:
# ✅ All deliverables present
# ✅ All tests passing
# ✅ Coverage: 85% (meets target)

# 5. NOW mark complete
python3 scripts/refactoring/update_execution_context.py \
  --step "3.2.1" \
  --status "completed"
```

### Procedure 2: Reconcile Context After Drift

**Problem**: Context significantly drifted from reality

```python
#!/usr/bin/env python3
# reconcile_context.py

def reconcile_context(service: str):
    """Forcibly reconcile context with reality"""
    
    print("🔄 Reconciling context with reality...")
    
    service_path = Path(f"services/{service}")
    
    # Determine actual phase from codebase
    actual_phase = infer_phase_from_codebase(service_path)
    actual_step = infer_step_from_codebase(service_path, actual_phase)
    
    # Determine actual progress
    actual_completed_work = []
    for phase in range(1, 7):
        if phase_completed(service_path, phase):
            actual_completed_work.append(f"Phase {phase}: Complete")
    
    # Update context to match reality
    context = load_context()
    context["current_state"]["phase"] = actual_phase
    context["current_state"]["step"] = actual_step
    context["completed_work"] = actual_completed_work
    context["session_memory"]["reconciliation"] = {
        "timestamp": datetime.utcnow().isoformat(),
        "reason": "Context drift detected and reconciled",
        "confidence": "high"  # Based on reality, not memory
    }
    
    save_context(context)
    
    print(f"✅ Context reconciled:")
    print(f"   Phase: {actual_phase}")
    print(f"   Step: {actual_step}")
    print(f"   Completed: {len(actual_completed_work)} phases")
```

---

## ⚠️ Critical Rules

### Never Trust, Always Verify

```python
# WRONG:
"I implemented X"
update_context("X completed")  # Trust without verification

# RIGHT:
"I implemented X"
verify_X_exists()  # Verify
verify_X_works()   # Validate
verify_tests_pass()  # Ensure quality
update_context("X completed")  # Then trust
```

### Reality > Memory

```python
if context.says("completed") and reality.says("incomplete"):
    # Trust reality, not memory
    context.update("incomplete")
```

### Validate Before Transition

```python
# Before moving to next step
validate_current_step_complete()  # REQUIRED

# Before changing phase
validate_all_phase_steps_complete()  # REQUIRED

# Before marking service done
validate_all_phases_complete()  # REQUIRED
```

---

**Document Control**  
**Version**: 1.0.0  
**Last Updated**: October 9, 2025  
**For AI Agents**: Use this to prevent hallucination and drift  
**Owner**: Hackathon Team

