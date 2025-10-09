<!-- AI_READ_PRIORITY: 1 -->
<!-- AI_TAGS: ai-execution, step-by-step, context-management, scope-control -->
<!-- AI_KEY_SECTIONS: Execution Context Management, Step-by-Step Execution Protocol, Scope Control, Context Maintenance -->

---
ai_metadata:
  purpose: execution_instructions
  read_priority: 1
  context_level: tactical
  tags:
  - ai-execution
  - step-by-step
  - context-management
  - scope-control
  when_to_read: At start of every session
  key_sections:
  - Execution Context Management
  - Step-by-Step Execution Protocol
  - Scope Control
  - Context Maintenance
  execution_relevance: critical
---

# 🤖 AI Agent Execution Guide - Automated Refactoring

**Version**: 1.0.0  
**Created**: October 9, 2025  
**Status**: Active  
**Purpose**: Enable AI/LLM agents to execute the refactoring plan autonomously

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [AI Agent Prerequisites](#ai-agent-prerequisites)
3. [Execution Context Management](#execution-context-management)
4. [Step-by-Step Execution Protocol](#step-by-step-execution-protocol)
5. [Context Maintenance](#context-maintenance)
6. [Scope Control](#scope-control)
7. [Navigation Guide](#navigation-guide)
8. [Living Documents](#living-documents)
9. [Error Recovery](#error-recovery)

---

## 🎯 Overview

### Purpose

This guide provides **explicit instructions for AI agents** to execute the service refactoring plan autonomously while maintaining context, tracking progress, and preventing scope drift.

### AI Agent Capabilities Required

**Minimum Requirements**:
- Code reading and writing
- File system operations
- Command execution
- Pattern recognition
- Context maintenance across sessions
- JSON/YAML parsing
- Markdown generation

### Execution Model

**Mode**: Iterative, single-service execution  
**Context**: Maintained through living documents  
**Validation**: Automatic validation after each phase  
**Recovery**: Checkpoint-based recovery on failure

---

## 🔧 AI Agent Prerequisites

### Before Starting Execution

**AI Agent MUST**:

1. **Read Master Documents** (in this order):
   ```
   PRIORITY 1 (Critical - Read First):
   - AI_AGENT_EXECUTION_GUIDE.md (this file)
   - MASTER_REFACTORING_PLAN.md
   - LIVING_PROGRESS_TRACKER.md
   
   PRIORITY 2 (Phase-Specific):
   - NAMING_CONVENTIONS_STANDARDS.md
   - COMPREHENSIVE_TESTING_STRATEGY.md
   - STANDARDIZED_LOGGING_STRATEGY.md
   - SERVICE_DOCUMENTATION_STRATEGY.md
   - API_STANDARDIZATION_STRATEGY.md
   ```

2. **Initialize Execution Context**:
   ```bash
   # Create execution context file
   python3 scripts/refactoring/init_ai_execution.py
   ```

3. **Validate Environment**:
   ```bash
   # Check prerequisites
   python3 scripts/refactoring/validate_environment.py
   ```

---

## 📊 Execution Context Management

### Context File Structure

**Location**: `.ai_execution/context.json`

**Format**:
```json
{
  "execution_id": "exec_20251009_103045_abc123",
  "started_at": "2025-10-09T10:30:45.123Z",
  "last_updated": "2025-10-09T11:15:22.456Z",
  "current_state": {
    "phase": "Phase 3: TDD Implementation",
    "step": "3.2.1 Implement Application Layer",
    "service": "doc-store",
    "progress_percent": 45
  },
  "completed_work": {
    "phases": [
      {
        "phase": "Phase 1: Audit & Analysis",
        "completed_at": "2025-10-09T10:45:00.000Z",
        "deliverables": [
          "services/doc-store/audit_report.json",
          "services/doc-store/dependency_map.json"
        ]
      }
    ],
    "checkpoints": [
      "checkpoint_phase1_complete",
      "checkpoint_phase2_complete"
    ]
  },
  "next_work": [
    {
      "step": "3.2.2 Implement Infrastructure Layer",
      "estimated_duration_minutes": 120,
      "dependencies": ["3.2.1 Implement Application Layer"]
    }
  ],
  "scope": {
    "service": "doc-store",
    "tier": "Tier 1: Foundation Services",
    "bounded_context": "Document Management",
    "out_of_scope": [
      "Modifying other services",
      "Changing database schema globally",
      "Altering authentication system"
    ]
  },
  "session_memory": {
    "key_decisions": [
      "Using PostgreSQL for document storage",
      "Redis for caching with 5-minute TTL"
    ],
    "patterns_identified": [
      "Document entity uses UUID for IDs",
      "All timestamps in UTC ISO 8601"
    ],
    "blockers": []
  }
}
```

### Context Update Protocol

**MUST update context after**:
- Completing any step
- Before starting new step
- Every 30 minutes during long tasks
- When making key decisions
- When encountering blockers

**Update Command**:
```bash
python3 scripts/refactoring/update_execution_context.py \
  --step "3.2.1 Implement Application Layer" \
  --status "completed" \
  --notes "Implemented 5 commands, 3 queries"
```

---

## 🔄 Step-by-Step Execution Protocol

### Execution Loop (Per Service)

```
┌─────────────────────────────────────────────────────────┐
│ START: Service Refactoring                              │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ 1. READ CONTEXT                                         │
│    - Load .ai_execution/context.json                    │
│    - Determine current service and phase                │
│    - Review completed work                              │
│    - Identify next step                                 │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ 2. VALIDATE PREREQUISITES                               │
│    - All previous steps completed                       │
│    - Required tools available                           │
│    - Environment ready                                  │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ 3. EXECUTE CURRENT STEP                                 │
│    - Follow phase-specific instructions                 │
│    - Use automation tools where available               │
│    - Document decisions in context                      │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ 4. VALIDATE STEP COMPLETION                             │
│    - Run validation scripts                             │
│    - Check quality gates                                │
│    - Verify deliverables                                │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ 5. UPDATE CONTEXT                                       │
│    - Mark step complete                                 │
│    - Record deliverables                                │
│    - Update progress                                    │
│    - Save checkpoint                                    │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ 6. CHECK PHASE COMPLETION                               │
│    - All steps in phase done?                           │
│    - Quality gate passed?                               │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
              ┌─────────┴─────────┐
              │                   │
         YES  │                   │  NO
              │                   │
              ▼                   ▼
    ┌────────────────┐   ┌────────────────┐
    │ Next Phase     │   │ Next Step      │
    │ or Service     │   │ in Phase       │
    └────────────────┘   └────────────────┘
              │                   │
              └─────────┬─────────┘
                        │
                        ▼
                   LOOP BACK
```

---

## 📝 Phase-Specific Execution Instructions

### Phase 1: Audit & Analysis

**AI Agent Instructions**:

```yaml
phase: "Phase 1: Audit & Analysis"
duration: "1-2 days"
objective: "Understand current state and dependencies"

steps:
  - step_id: "1.1"
    name: "Service Audit"
    ai_instructions: |
      EXECUTE:
      1. Run: python3 scripts/refactoring/audit_service.py {service_name}
      2. READ: Generated audit report at reports/{service_name}_audit.json
      3. EXTRACT: Key metrics (LOC, complexity, dependencies)
      4. RECORD in context: Audit findings
      
      DELIVERABLE: services/{service_name}/audit_report.json
    
    validation:
      - "Audit report exists"
      - "LOC > 0"
      - "Dependencies listed"
    
    context_tags:
      - "audit"
      - "metrics"
      - "analysis"
  
  - step_id: "1.2"
    name: "Dependency Analysis"
    ai_instructions: |
      EXECUTE:
      1. READ: docker-compose.dev.yml
      2. IDENTIFY: All services this service depends on
      3. IDENTIFY: All services that depend on this service
      4. CREATE: Dependency map JSON
      5. RECORD in context: Critical dependencies
      
      DELIVERABLE: services/{service_name}/dependency_map.json
    
    validation:
      - "Dependency map exists"
      - "Providers listed"
      - "Consumers listed"
  
  - step_id: "1.3"
    name: "Gap Analysis"
    ai_instructions: |
      EXECUTE:
      1. COMPARE: Current state vs. DDD standards
      2. IDENTIFY: Missing tests (target: 80%)
      3. IDENTIFY: Missing documentation
      4. IDENTIFY: Missing logging
      5. CREATE: Gap analysis document
      6. RECORD in context: Major gaps
      
      DELIVERABLE: services/{service_name}/gap_analysis.md

completion_criteria:
  - "All 3 deliverables created"
  - "Context updated with findings"
  - "Ready for Phase 2"
```

### Phase 2: Design & Planning

**AI Agent Instructions**:

```yaml
phase: "Phase 2: Design & Planning"
duration: "1 day"
objective: "Create detailed refactoring plan"

steps:
  - step_id: "2.1"
    name: "Domain Modeling"
    ai_instructions: |
      EXECUTE:
      1. READ: Current service code
      2. IDENTIFY: Domain entities (classes that represent business concepts)
      3. IDENTIFY: Value objects (immutable data holders)
      4. IDENTIFY: Aggregates (clusters of related entities)
      5. CREATE: Domain model diagram (use Mermaid)
      6. RECORD in context: Domain entities identified
      
      PATTERN TO FOLLOW:
      - Entities: Have identity, mutable
      - Value Objects: No identity, immutable
      - Aggregates: Root entity + related entities
      
      DELIVERABLE: services/{service_name}/design/domain_model.md
    
    validation:
      - "At least 2 entities identified"
      - "At least 1 value object identified"
      - "Domain model diagram present"
  
  - step_id: "2.2"
    name: "API Design"
    ai_instructions: |
      EXECUTE:
      1. LIST: All current endpoints
      2. DESIGN: New /api/v2/ endpoints
      3. DESIGN: Standard endpoints (health, about-me, endpoints, provider-consumer)
      4. CREATE: OpenAPI spec (use OpenAPI 3.0)
      5. RECORD in context: API changes
      
      DELIVERABLE: services/{service_name}/design/openapi_v2.yaml

  - step_id: "2.3"
    name: "Test Planning"
    ai_instructions: |
      EXECUTE:
      1. LIST: All core features (from audit)
      2. PLAN: Unit tests (60% of total tests)
      3. PLAN: Integration tests (30% of total tests)
      4. PLAN: E2E tests (10% of total tests)
      5. CREATE: Test plan document
      6. TARGET: 80%+ coverage
      
      DELIVERABLE: services/{service_name}/design/test_plan.md

completion_criteria:
  - "All 3 deliverables created"
  - "Design reviewed and validated"
  - "Ready for Phase 3"
```

### Phase 3: TDD Implementation

**AI Agent Instructions**:

```yaml
phase: "Phase 3: TDD Implementation"
duration: "3-5 days"
objective: "Implement refactored service following TDD"

important_notes: |
  THIS IS THE LONGEST PHASE
  MAINTAIN CONTEXT CAREFULLY
  UPDATE CONTEXT EVERY 30 MINUTES
  FOLLOW TDD: RED → GREEN → REFACTOR

steps:
  - step_id: "3.1"
    name: "Set Up Testing Infrastructure"
    ai_instructions: |
      EXECUTE:
      1. RUN: python3 scripts/refactoring/setup_testing_infrastructure.py {service_name}
      2. VERIFY: pytest.ini created
      3. VERIFY: Test directories created
      4. VERIFY: conftest.py created
      5. RECORD in context: Testing infrastructure ready
      
      DELIVERABLE: Complete test structure
  
  - step_id: "3.2"
    name: "Red Phase - Write Failing Tests"
    ai_instructions: |
      FOR EACH LAYER (domain, application, infrastructure, presentation):
        1. IDENTIFY: Components to test in this layer
        2. WRITE: Test for component (it will FAIL - that's expected)
        3. RUN: pytest -m unit
        4. VERIFY: Test fails as expected
        5. MOVE TO: Green Phase for this component
      
      PATTERN:
      def test_component_behavior_expected_result():
          # Arrange - set up test data
          # Act - execute code
          # Assert - verify result
      
      TARGET: 80%+ coverage
      
      RECORD in context: Tests written per layer
  
  - step_id: "3.3"
    name: "Green Phase - Implement Features"
    ai_instructions: |
      FOR EACH FAILING TEST:
        1. IMPLEMENT: Minimal code to make test pass
        2. RUN: pytest
        3. VERIFY: Test passes
        4. IMPLEMENT: Logging for this feature (if core feature)
        5. MOVE TO: Next failing test
      
      LOGGING REQUIRED:
      - Use StructuredLogger
      - Log at INFO level for core features
      - Include correlation_id and duration_ms
      - Follow STANDARDIZED_LOGGING_STRATEGY.md
      
      RECORD in context: Features implemented
  
  - step_id: "3.4"
    name: "Refactor Phase - Optimize Code"
    ai_instructions: |
      WITH TESTS PASSING:
        1. IDENTIFY: Code duplication
        2. EXTRACT: Common patterns
        3. IMPROVE: Naming
        4. OPTIMIZE: Performance
        5. RUN: pytest (ensure still passing)
        6. REPEAT until no more improvements
      
      DO NOT:
      - Change behavior
      - Break tests
      - Add new features
      
      RECORD in context: Refactorings applied
  
  - step_id: "3.5"
    name: "Validate Testing & Logging"
    ai_instructions: |
      EXECUTE:
      1. RUN: pytest --cov --cov-fail-under=80
      2. VERIFY: Coverage ≥ 80%
      3. RUN: python3 scripts/refactoring/validate_logging.py {service_name}
      4. VERIFY: Logging score ≥ 80
      5. GENERATE: Coverage report
      6. GENERATE: Logging report
      
      DELIVERABLE: Test coverage report + Logging validation report

completion_criteria:
  - "All tests pass"
  - "Coverage ≥ 80%"
  - "Logging score ≥ 80"
  - "All core features implemented"
  - "Ready for Phase 4"
```

### Phase 4: Integration Testing

**AI Agent Instructions**:

```yaml
phase: "Phase 4: Integration Testing"
duration: "1-2 days"
objective: "Ensure service integrates with ecosystem"

steps:
  - step_id: "4.1"
    name: "Service Integration Tests"
    ai_instructions: |
      EXECUTE:
      1. IDENTIFY: Services this service calls
      2. WRITE: Integration tests for each dependency
      3. RUN: pytest -m integration
      4. VERIFY: All integration tests pass
      
      DELIVERABLE: Integration test results
  
  - step_id: "4.2"
    name: "Workflow Tests"
    ai_instructions: |
      EXECUTE:
      1. RUN: python3 scripts/refactoring/generate_workflow_tests.py {service_name}
      2. REVIEW: Generated workflow tests
      3. CUSTOMIZE: Tests for specific workflows
      4. RUN: pytest -m workflow
      5. VERIFY: All workflow tests pass
      
      DELIVERABLE: Workflow test results

completion_criteria:
  - "Integration tests pass"
  - "Workflow tests pass"
  - "Service integrates correctly"
  - "Ready for Phase 5"
```

### Phase 5: Documentation

**AI Agent Instructions**:

```yaml
phase: "Phase 5: Documentation"
duration: "1 day"
objective: "Complete comprehensive documentation"

steps:
  - step_id: "5.1"
    name: "Generate Service README"
    ai_instructions: |
      EXECUTE:
      1. RUN: python3 scripts/refactoring/generate_service_readme.py {service_name}
      2. REVIEW: Generated README
      3. ADD: Ecosystem architecture diagram (use Mermaid or ASCII art)
      4. ADD: Data flow diagram
      5. ADD: Workflow diagrams
      6. CUSTOMIZE: Service-specific details
      7. VERIFY: All sections complete
      
      DELIVERABLE: Comprehensive README.md
  
  - step_id: "5.2"
    name: "Implement Standard Endpoints"
    ai_instructions: |
      EXECUTE:
      1. IMPLEMENT: GET /health
      2. IMPLEMENT: GET /about-me
      3. IMPLEMENT: GET /endpoints
      4. IMPLEMENT: GET /provider-consumer
      5. VERIFY: All endpoints return correct JSON
      6. ADD: OpenAPI annotations
      
      FOLLOW: API_STANDARDIZATION_STRATEGY.md
      
      DELIVERABLE: Standard endpoints implemented
  
  - step_id: "5.3"
    name: "Validate Documentation"
    ai_instructions: |
      EXECUTE:
      1. RUN: python3 scripts/refactoring/validate_service_documentation.py {service_name}
      2. REVIEW: Validation report
      3. FIX: Any issues identified
      4. RE-RUN: Until score ≥ 80
      
      DELIVERABLE: Documentation validation report

completion_criteria:
  - "README complete"
  - "Standard endpoints working"
  - "Documentation score ≥ 80"
  - "OpenAPI/Swagger available"
  - "Ready for Phase 6"
```

### Phase 6: Deployment & Monitoring

**AI Agent Instructions**:

```yaml
phase: "Phase 6: Deployment & Monitoring"
duration: "1 day"
objective: "Deploy and validate in target environment"

steps:
  - step_id: "6.1"
    name: "Quality Gates Check"
    ai_instructions: |
      EXECUTE:
      1. RUN: python3 scripts/refactoring/check_quality_gates.py {service_name}
      2. REVIEW: Quality gate results
      3. FIX: Any failing gates
      4. RE-RUN: Until all gates pass
      
      DELIVERABLE: Quality gates report (all passing)
  
  - step_id: "6.2"
    name: "Update Progress Tracker"
    ai_instructions: |
      EXECUTE:
      1. OPEN: docs/refactoring/LIVING_PROGRESS_TRACKER.md
      2. UPDATE: Service status to "Completed"
      3. UPDATE: Progress percentage to 100%
      4. ADD: Completion notes
      5. SAVE: Updated tracker
      
      DELIVERABLE: Updated LIVING_PROGRESS_TRACKER.md

completion_criteria:
  - "All quality gates pass"
  - "Service deployed"
  - "Progress tracker updated"
  - "Service refactoring COMPLETE"
```

---

## 🧭 Context Maintenance

### Session Context

**At Start of Each Session**:

```python
# AI Agent MUST execute this protocol

# 1. Load execution context
context = load_json(".ai_execution/context.json")

# 2. Review current state
print(f"Current Phase: {context['current_state']['phase']}")
print(f"Current Step: {context['current_state']['step']}")
print(f"Service: {context['current_state']['service']}")
print(f"Progress: {context['current_state']['progress_percent']}%")

# 3. Review completed work
for phase in context['completed_work']['phases']:
    print(f"✓ Completed: {phase['phase']}")

# 4. Identify next work
next_step = context['next_work'][0]
print(f"Next: {next_step['step']}")

# 5. Review key decisions
for decision in context['session_memory']['key_decisions']:
    print(f"Decision: {decision}")

# 6. Check for blockers
if context['session_memory']['blockers']:
    print("⚠️ BLOCKERS:")
    for blocker in context['session_memory']['blockers']:
        print(f"  - {blocker}")
```

### During Execution

**Every 30 minutes, AI Agent MUST**:

1. **Update context file** with current progress
2. **Record any decisions** made
3. **Note any patterns** identified
4. **Flag any blockers** encountered
5. **Save checkpoint** if significant progress made

### Between Sessions

**Before Ending Session**:

```python
# AI Agent MUST execute this protocol

# 1. Update context with latest state
update_context({
    "last_updated": current_timestamp(),
    "current_state": {
        "phase": current_phase,
        "step": current_step,
        "progress_percent": calculated_progress
    },
    "session_summary": {
        "duration_minutes": session_duration,
        "work_completed": list_of_completed_items,
        "decisions_made": list_of_decisions,
        "next_session_focus": what_to_do_next
    }
})

# 2. Create checkpoint
create_checkpoint(f"checkpoint_{current_phase}_{current_step}")

# 3. Generate session summary
generate_session_summary(".ai_execution/session_log.md")
```

---

## 🎯 Scope Control

### In-Scope

**AI Agent IS ALLOWED to**:

✅ Modify the current service being refactored  
✅ Create new tests for the current service  
✅ Update documentation for the current service  
✅ Add logging to the current service  
✅ Implement standard endpoints in the current service  
✅ Update execution context  
✅ Update progress tracker  
✅ Run validation scripts  
✅ Create diagrams for the current service  

### Out-of-Scope

**AI Agent MUST NOT**:

❌ Modify other services (except the one being refactored)  
❌ Change global configurations (unless explicitly required)  
❌ Alter database schemas globally  
❌ Modify authentication/authorization systems  
❌ Change common/shared libraries without approval  
❌ Skip quality gates  
❌ Reduce test coverage below 80%  
❌ Remove logging  
❌ Skip documentation  
❌ Change service dependencies without documenting  

### Scope Validation

**Before making ANY change, AI Agent MUST**:

```python
def validate_scope(change):
    """Validate if change is in scope"""
    
    # Check if modifying current service
    if not is_current_service(change.file_path):
        return False, "Out of scope: modifying other service"
    
    # Check if removing tests
    if is_removing_tests(change):
        return False, "Out of scope: cannot remove tests"
    
    # Check if reducing coverage
    if reduces_coverage(change):
        return False, "Out of scope: cannot reduce coverage"
    
    # Check if skipping quality gate
    if skips_quality_gate(change):
        return False, "Out of scope: cannot skip quality gates"
    
    return True, "In scope"
```

---

## 🗺️ Navigation Guide

### Document Navigation Map

```
START HERE:
├─ AI_AGENT_EXECUTION_GUIDE.md (THIS FILE)
│
├─ MASTER_REFACTORING_PLAN.md
│  ├─ Read: Goals and Objectives
│  ├─ Read: Guiding Principles
│  ├─ Read: Refactoring Methodology (6 phases)
│  ├─ Read: Quality Gates (10 gates)
│  └─ Read: Service Categories (which tier is current service?)
│
├─ LIVING_PROGRESS_TRACKER.md
│  ├─ Find: Current service
│  ├─ Check: Current status
│  ├─ Review: Completed work
│  └─ Identify: Next service
│
└─ Phase-Specific Guides (read when in that phase):
   ├─ NAMING_CONVENTIONS_STANDARDS.md (always reference)
   ├─ SERVICE_AUDIT_TEMPLATE.md (Phase 1)
   ├─ TDD_CHECKLIST.md (Phase 3)
   ├─ COMPREHENSIVE_TESTING_STRATEGY.md (Phase 3)
   ├─ STANDARDIZED_LOGGING_STRATEGY.md (Phase 3)
   ├─ WORKFLOW_TESTING_STRATEGY.md (Phase 4)
   ├─ SERVICE_DOCUMENTATION_STRATEGY.md (Phase 5)
   └─ API_STANDARDIZATION_STRATEGY.md (Phase 5)
```

### Quick Reference Cheat Sheet

**AI Agent: Use this for quick lookups**

| Need | Document | Section |
|------|----------|---------|
| Current service status | LIVING_PROGRESS_TRACKER.md | Service Progress Table |
| What to do next | .ai_execution/context.json | next_work[] |
| Naming conventions | NAMING_CONVENTIONS_STANDARDS.md | Quick Reference Tables |
| Test coverage target | COMPREHENSIVE_TESTING_STRATEGY.md | Coverage Requirements |
| Log format | STANDARDIZED_LOGGING_STRATEGY.md | Standard Log Format |
| Standard endpoints | API_STANDARDIZATION_STRATEGY.md | Standard Endpoints |
| DDD structure | MASTER_REFACTORING_PLAN.md | Architecture Standards |
| Quality gates | MASTER_REFACTORING_PLAN.md | Quality Gates |

---

## 📝 Living Documents

### Documents AI Agent MUST Update

#### 1. Execution Context (.ai_execution/context.json)

**Update Frequency**: Every step completion + every 30 minutes

**What to Update**:
- current_state.phase
- current_state.step
- current_state.progress_percent
- completed_work.phases[] (add completed phases)
- next_work[] (update with next steps)
- session_memory.key_decisions[] (add decisions)
- session_memory.patterns_identified[] (add patterns)

#### 2. Progress Tracker (docs/refactoring/LIVING_PROGRESS_TRACKER.md)

**Update Frequency**: After each phase completion + at service completion

**What to Update**:
- Service status (Not Started → In Progress → Completed)
- Progress percentage (0% → 100%)
- Current phase
- Phase completion dates
- Metrics (LOC, coverage, etc.)
- Notes and lessons learned

#### 3. Session Log (.ai_execution/session_log.md)

**Update Frequency**: End of each session

**What to Update**:
```markdown
## Session [SESSION_ID] - [DATE]

**Duration**: [MINUTES] minutes  
**Service**: [SERVICE_NAME]  
**Phase**: [PHASE_NAME]

### Work Completed
- [ITEM 1]
- [ITEM 2]

### Decisions Made
- [DECISION 1]: [RATIONALE]
- [DECISION 2]: [RATIONALE]

### Patterns Identified
- [PATTERN 1]
- [PATTERN 2]

### Blockers Encountered
- [BLOCKER 1]: [RESOLUTION or PENDING]

### Next Session Focus
- [WHAT TO DO NEXT]

### Context Checkpoints
- Checkpoint: [CHECKPOINT_ID]
- State: [SAVED STATE]
```

---

## ⚠️ Error Recovery

### If AI Agent Loses Context

**Recovery Protocol**:

```python
# 1. Load last checkpoint
context = load_checkpoint("latest")

# 2. Review session log
session_log = read_file(".ai_execution/session_log.md")
last_session = parse_last_session(session_log)

# 3. Verify current state
current_files = list_modified_files(since=last_session['timestamp'])

# 4. Determine next action
if last_session['phase_completed']:
    next_action = "Start next phase"
else:
    next_action = "Continue current phase from last step"

# 5. Resume execution
print(f"Resuming: {next_action}")
print(f"Last completed: {last_session['work_completed']}")
print(f"Next step: {context['next_work'][0]['step']}")
```

### If Tests Fail

**Recovery Protocol**:

```python
# DO NOT PROCEED if tests fail

# 1. Identify failure
test_results = run_tests()
failures = [t for t in test_results if t.failed]

# 2. Analyze failure
for failure in failures:
    print(f"Failed: {failure.test_name}")
    print(f"Error: {failure.error_message}")

# 3. Fix issue
# - Review code
# - Fix bug
# - Re-run test

# 4. Verify fix
assert run_tests().all_passed

# 5. Update context
record_issue_and_resolution(failures[0], resolution)
```

### If Quality Gate Fails

**DO NOT PROCEED**

```python
# 1. Identify failing gate
gate_results = check_quality_gates()
failing_gates = [g for g in gate_results if not g.passed]

# 2. Fix each failing gate
for gate in failing_gates:
    print(f"Failing gate: {gate.name}")
    print(f"Reason: {gate.reason}")
    
    # Follow remediation steps
    execute_remediation(gate)

# 3. Re-check
assert check_quality_gates().all_passed

# 4. Proceed to next phase
```

---

## 🚀 Execution Checklist

### Pre-Execution (AI Agent MUST Complete)

- [ ] Read AI_AGENT_EXECUTION_GUIDE.md (this file)
- [ ] Read MASTER_REFACTORING_PLAN.md
- [ ] Load execution context
- [ ] Identify current service
- [ ] Identify current phase
- [ ] Review completed work
- [ ] Understand next steps
- [ ] Validate environment
- [ ] Check for blockers

### During Execution (AI Agent MUST Maintain)

- [ ] Update context every 30 minutes
- [ ] Record decisions as they're made
- [ ] Note patterns identified
- [ ] Flag blockers immediately
- [ ] Run validations after each step
- [ ] Maintain scope boundaries
- [ ] Follow TDD process
- [ ] Keep tests passing

### Post-Execution (AI Agent MUST Complete)

- [ ] Update final context state
- [ ] Create checkpoint
- [ ] Generate session summary
- [ ] Update progress tracker
- [ ] Verify all deliverables created
- [ ] Run final validation
- [ ] Document lessons learned
- [ ] Prepare for next session

---

## 📊 Success Metrics

### AI Agent Performance Metrics

**Track These**:
- Time per phase
- Steps completed per session
- Test coverage achieved
- Quality gates passed first time
- Context maintenance accuracy
- Scope adherence (% of time)
- Recovery success rate

### Optimization Targets

- Phase 1: < 2 hours
- Phase 2: < 4 hours
- Phase 3: < 40 hours (longest phase)
- Phase 4: < 8 hours
- Phase 5: < 4 hours
- Phase 6: < 2 hours

**Total per service**: < 60 hours

---

**Document Control**  
**Version**: 1.0.0  
**Last Updated**: October 9, 2025  
**For AI Agents**: This is your primary execution guide  
**Owner**: Hackathon Team

