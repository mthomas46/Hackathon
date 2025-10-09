# ✅ AI Agent Self-Review Checklist - Holistic Work Validation

**Version**: 1.0.0  
**Created**: October 9, 2025  
**Status**: Active  
**Purpose**: Enable AI agents to review their own work holistically and catch missed steps

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [When to Self-Review](#when-to-self-review)
3. [Review Levels](#review-levels)
4. [Phase-by-Phase Review](#phase-by-phase-review)
5. [Common Mistakes](#common-mistakes)
6. [Remediation](#remediation)

---

## 🎯 Overview

### Purpose

AI agents MUST perform **self-reviews** to:
- Verify no steps were skipped
- Ensure all deliverables exist
- Validate work quality
- Catch mistakes before moving forward
- Prevent accumulation of technical debt

### Self-Review Philosophy

**"Trust, but verify"**

- Assume mistakes were made
- Check everything systematically
- Fix issues before proceeding
- Better to catch now than later

---

## ⏰ When to Self-Review

### Mandatory Self-Review Points

```yaml
review_point_1:
  trigger: "After completing each phase"
  type: "Phase Review"
  duration: "5-10 minutes"
  scope: "All phase deliverables and steps"
  
review_point_2:
  trigger: "Before passing quality gate"
  type: "Gate Review"
  duration: "10-15 minutes"
  scope: "All gate requirements"
  
review_point_3:
  trigger: "Before committing to git"
  type: "Commit Review"
  duration: "2-5 minutes"
  scope: "Changes being committed"
  
review_point_4:
  trigger: "After 4+ hours of work"
  type: "Progress Review"
  duration: "5 minutes"
  scope: "Recent work for consistency"
  
review_point_5:
  trigger: "When recovering from interruption"
  type: "Recovery Review"
  duration: "10 minutes"
  scope: "State consistency and completeness"
  
review_point_6:
  trigger: "Before ending session"
  type: "Session Review"
  duration: "5 minutes"
  scope: "Context update and state preservation"
```

---

## 📊 Review Levels

### Level 1: Quick Sanity Check (2 minutes)

**Purpose**: Verify nothing is obviously broken

**Checklist**:
- [ ] All tests pass (`pytest`)
- [ ] Code runs without errors
- [ ] No syntax errors
- [ ] Context file is valid JSON
- [ ] Current step makes sense

**Command**:
```bash
python3 scripts/refactoring/quick_sanity_check.py
```

---

### Level 2: Step Review (5 minutes)

**Purpose**: Verify current step completed correctly

**Checklist**:
- [ ] Step deliverables exist
- [ ] Deliverables are complete (not empty/skeleton)
- [ ] Tests for this step pass
- [ ] Step documented in context
- [ ] Next step is correct

**Example for Step 3.2.1 (Implement Application Layer)**:
```yaml
step_review:
  step: "3.2.1 Implement Application Layer"
  
  required_deliverables:
    - "services/{service}/application/commands/"
    - "services/{service}/application/queries/"
    - "tests/unit/application/"
  
  validation:
    - "At least 3 command handlers implemented"
    - "At least 2 query handlers implemented"
    - "At least 10 tests for application layer"
    - "Tests pass: pytest tests/unit/application/"
    - "Coverage >= 80% for application layer"
```

---

### Level 3: Phase Review (10-15 minutes)

**Purpose**: Verify entire phase completed correctly

**Checklist**:
- [ ] All phase steps completed
- [ ] All phase deliverables exist
- [ ] Phase quality gate passed
- [ ] Phase documented in context
- [ ] Ready for next phase

**Use Phase-by-Phase Review section below**

---

### Level 4: Comprehensive Review (30 minutes)

**Purpose**: Verify entire refactoring is correct

**Checklist**:
- [ ] All 6 phases completed
- [ ] All 10 quality gates passed
- [ ] All deliverables exist
- [ ] Service works end-to-end
- [ ] Documentation complete
- [ ] Ready for production

**Use Quality Gates section below**

---

## 🔍 Phase-by-Phase Review

### Phase 1: Audit & Analysis Review

**When**: After completing Phase 1, before starting Phase 2

**Self-Review Checklist**:

```yaml
phase_1_review:
  phase: "Phase 1: Audit & Analysis"
  
  step_1_1_audit:
    deliverable: "services/{service}/audit_report.json"
    checks:
      - "File exists"
      - "File size > 1KB (not empty)"
      - "Contains metrics: LOC, complexity, dependencies"
      - "Contains service name and version"
    
  step_1_2_dependencies:
    deliverable: "services/{service}/dependency_map.json"
    checks:
      - "File exists"
      - "Lists provider services"
      - "Lists consumer services"
      - "Identifies critical dependencies"
    
  step_1_3_gap_analysis:
    deliverable: "services/{service}/gap_analysis.md"
    checks:
      - "File exists"
      - "Identifies test coverage gap"
      - "Identifies missing documentation"
      - "Identifies missing logging"
      - "Prioritizes gaps"
  
  holistic_checks:
    - "Understand service purpose and capabilities"
    - "Know all dependencies"
    - "Understand current state vs target state"
    - "Ready to design new architecture"
```

**Validation Command**:
```bash
python3 scripts/refactoring/review_phase1.py {service}
```

**Common Mistakes**:
- ❌ Audit report missing metrics
- ❌ Dependency map incomplete (missing consumers)
- ❌ Gap analysis too vague ("needs improvement" vs "missing 45% test coverage")

**Remediation**:
```bash
# Re-run audit
python3 scripts/refactoring/audit_service.py {service}

# Verify all deliverables
ls -lh services/{service}/audit_report.json
ls -lh services/{service}/dependency_map.json
ls -lh services/{service}/gap_analysis.md
```

---

### Phase 2: Design & Planning Review

**When**: After completing Phase 2, before starting Phase 3

**Self-Review Checklist**:

```yaml
phase_2_review:
  phase: "Phase 2: Design & Planning"
  
  step_2_1_domain_modeling:
    deliverable: "services/{service}/design/domain_model.md"
    checks:
      - "File exists"
      - "Identifies at least 2 entities"
      - "Identifies at least 1 value object"
      - "Defines aggregates"
      - "Contains domain model diagram (Mermaid or ASCII)"
    
  step_2_2_api_design:
    deliverable: "services/{service}/design/openapi_v2.yaml"
    checks:
      - "File exists"
      - "Valid OpenAPI 3.0 spec"
      - "Defines /api/v2/ endpoints"
      - "Includes standard endpoints"
      - "All endpoints have request/response schemas"
    
  step_2_3_test_planning:
    deliverable: "services/{service}/design/test_plan.md"
    checks:
      - "File exists"
      - "Lists all core features to test"
      - "Plans for 60% unit, 30% integration, 10% E2E"
      - "Target: 80%+ coverage"
      - "Identifies test scenarios"
  
  holistic_checks:
    - "Design follows DDD principles"
    - "API is RESTful"
    - "Test plan covers all features"
    - "Design is implementable"
    - "Ready to start TDD"
```

**Validation Command**:
```bash
python3 scripts/refactoring/review_phase2.py {service}

# Validate OpenAPI spec
python3 -c "import yaml; yaml.safe_load(open('services/{service}/design/openapi_v2.yaml'))"
```

**Common Mistakes**:
- ❌ Domain model too vague (no clear entities)
- ❌ OpenAPI spec invalid YAML
- ❌ Test plan doesn't specify coverage targets
- ❌ Missing standard endpoints in API design

---

### Phase 3: TDD Implementation Review

**When**: After completing Phase 3, before starting Phase 4

**Self-Review Checklist**:

```yaml
phase_3_review:
  phase: "Phase 3: TDD Implementation"
  
  ddd_layers:
    domain:
      location: "services/{service}/domain/"
      checks:
        - "Directory exists"
        - "Contains entities/"
        - "Contains value_objects/"
        - "At least 2 entities implemented"
        - "Tests: tests/unit/domain/"
    
    application:
      location: "services/{service}/application/"
      checks:
        - "Directory exists"
        - "Contains commands/"
        - "Contains queries/"
        - "At least 3 commands implemented"
        - "At least 2 queries implemented"
        - "Tests: tests/unit/application/"
    
    infrastructure:
      location: "services/{service}/infrastructure/"
      checks:
        - "Directory exists"
        - "Contains repositories/"
        - "Repository implementations exist"
        - "Tests: tests/integration/"
    
    presentation:
      location: "services/{service}/presentation/"
      checks:
        - "Directory exists"
        - "Contains api/"
        - "API controllers implemented"
        - "Tests: tests/integration/api/"
  
  testing:
    unit_tests:
      checks:
        - "tests/unit/ exists"
        - "At least 30 unit tests"
        - "All unit tests pass"
        - "Unit tests cover domain and application"
    
    integration_tests:
      checks:
        - "tests/integration/ exists"
        - "At least 15 integration tests"
        - "All integration tests pass"
    
    coverage:
      checks:
        - "Overall coverage >= 80%"
        - "Domain coverage >= 90%"
        - "Application coverage >= 80%"
        - "Infrastructure coverage >= 70%"
        - "Presentation coverage >= 80%"
  
  logging:
    checks:
      - "StructuredLogger imported and used"
      - "All core features have INFO logging"
      - "All errors have ERROR logging"
      - "Correlation IDs tracked"
      - "Performance metrics (duration_ms) included"
      - "Log-collector integration configured"
  
  holistic_checks:
    - "All 4 DDD layers implemented"
    - "Clear layer separation (no circular dependencies)"
    - "80%+ test coverage achieved"
    - "All tests pass"
    - "Logging comprehensive"
    - "Ready for integration testing"
```

**Validation Command**:
```bash
# Validate structure
python3 scripts/refactoring/review_phase3.py {service}

# Validate tests
cd services/{service}
pytest --cov --cov-report=term

# Validate logging
python3 scripts/refactoring/validate_logging.py {service}
```

**Common Mistakes**:
- ❌ Skipped domain layer (went straight to database)
- ❌ Test coverage below 80%
- ❌ Missing logging in core features
- ❌ Circular dependencies between layers
- ❌ Tests don't follow AAA pattern
- ❌ No integration tests
- ❌ Correlation IDs not implemented

**Remediation**:
```bash
# Check coverage gaps
pytest --cov --cov-report=html
open htmlcov/index.html

# Find files with low coverage
pytest --cov --cov-report=term-missing

# Add tests for low-coverage areas
# Add logging to core features
```

---

### Phase 4: Integration Testing Review

**When**: After completing Phase 4, before starting Phase 5

**Self-Review Checklist**:

```yaml
phase_4_review:
  phase: "Phase 4: Integration Testing"
  
  integration_tests:
    checks:
      - "tests/integration/services/ exists"
      - "Tests for each service dependency"
      - "All integration tests pass"
  
  workflow_tests:
    checks:
      - "tests/workflows/ exists"
      - "At least 3 workflow tests"
      - "Workflows test end-to-end scenarios"
      - "All workflow tests pass"
  
  docker:
    checks:
      - "Service runs standalone: docker build ."
      - "Service runs in compose: docker-compose up {service}"
      - "Health check responds: curl localhost:{port}/health"
  
  holistic_checks:
    - "Service integrates with dependencies"
    - "Workflows work end-to-end"
    - "Service deployable"
    - "Ready for documentation"
```

**Validation Command**:
```bash
python3 scripts/refactoring/review_phase4.py {service}

# Test Docker
docker build -t {service} services/{service}
docker run -p {port}:{port} {service}
curl http://localhost:{port}/health
```

**Common Mistakes**:
- ❌ No integration tests (only unit tests)
- ❌ Workflow tests don't test actual workflows
- ❌ Docker build fails
- ❌ Health check not implemented

---

### Phase 5: Documentation Review

**When**: After completing Phase 5, before starting Phase 6

**Self-Review Checklist**:

```yaml
phase_5_review:
  phase: "Phase 5: Documentation"
  
  readme:
    location: "services/{service}/README.md"
    checks:
      - "File exists and > 5KB"
      - "Has Overview section (solo + ecosystem)"
      - "Has Architecture diagrams (at least 2)"
      - "Has Dependencies section"
      - "Has Endpoints section"
      - "Has Service Relationships section"
      - "Has Quick Start section"
  
  diagrams:
    checks:
      - "At least 2 visual diagrams"
      - "Ecosystem architecture diagram"
      - "Data flow diagram"
  
  standard_endpoints:
    checks:
      - "GET /health implemented"
      - "GET /about-me implemented"
      - "GET /endpoints implemented"
      - "GET /provider-consumer implemented"
      - "All return valid JSON"
      - "All work (curl test)"
  
  openapi:
    checks:
      - "Swagger UI at /docs"
      - "OpenAPI spec at /openapi.json"
      - "All endpoints documented"
      - "Request/response schemas defined"
  
  holistic_checks:
    - "Documentation complete and accurate"
    - "Standard endpoints working"
    - "OpenAPI/Swagger available"
    - "Service is self-documenting"
    - "Ready for deployment"
```

**Validation Command**:
```bash
python3 scripts/refactoring/review_phase5.py {service}
python3 scripts/refactoring/validate_service_documentation.py {service}

# Test standard endpoints
curl http://localhost:{port}/health
curl http://localhost:{port}/about-me
curl http://localhost:{port}/endpoints
curl http://localhost:{port}/provider-consumer
```

**Common Mistakes**:
- ❌ README too short (< 1KB)
- ❌ No diagrams
- ❌ Standard endpoints not implemented
- ❌ Swagger UI not available
- ❌ README doesn't describe ecosystem contribution

---

### Phase 6: Deployment & Monitoring Review

**When**: After completing Phase 6 (final phase)

**Self-Review Checklist**:

```yaml
phase_6_review:
  phase: "Phase 6: Deployment & Monitoring"
  
  quality_gates:
    checks:
      - "All 10 quality gates pass"
      - "Gate results documented"
  
  progress_tracker:
    checks:
      - "LIVING_PROGRESS_TRACKER.md updated"
      - "Service marked as 'Completed'"
      - "Progress: 100%"
      - "Completion date recorded"
  
  final_validation:
    checks:
      - "Service builds: docker build"
      - "Service runs: docker run"
      - "All tests pass: pytest"
      - "Coverage >= 80%: pytest --cov"
      - "Logging validated: validate_logging.py"
      - "Docs validated: validate_service_documentation.py"
      - "Quality gates: check_quality_gates.py"
  
  holistic_checks:
    - "Service is production-ready"
    - "All phases complete"
    - "All deliverables exist"
    - "Everything validated"
    - "Ready to move to next service"
```

**Validation Command**:
```bash
python3 scripts/refactoring/review_phase6.py {service}
python3 scripts/refactoring/check_quality_gates.py {service}
```

---

## ⚠️ Common Mistakes

### Top 10 AI Agent Mistakes

1. **Skipping tests**
   - ❌ Implementing code without tests
   - ✅ Always follow TDD: Red → Green → Refactor

2. **Incomplete logging**
   - ❌ Only logging errors
   - ✅ Log all core features at INFO level

3. **Missing documentation**
   - ❌ No README or minimal README
   - ✅ Comprehensive README with diagrams

4. **Not validating after each step**
   - ❌ Moving to next step without validation
   - ✅ Validate deliverables before proceeding

5. **Forgetting standard endpoints**
   - ❌ Only implementing business endpoints
   - ✅ Implement all 4 standard endpoints

6. **Low test coverage**
   - ❌ 50-60% coverage
   - ✅ 80%+ coverage required

7. **Skipping integration tests**
   - ❌ Only unit tests
   - ✅ Unit + integration + E2E tests

8. **Not updating context**
   - ❌ Context not updated for 2+ hours
   - ✅ Update context every 30 minutes

9. **Circular dependencies**
   - ❌ Infrastructure depends on Presentation
   - ✅ Clear layer separation (DDD)

10. **Not creating checkpoints**
    - ❌ No checkpoints, can't recover
    - ✅ Checkpoint after each phase

---

## 🔧 Remediation

### If Self-Review Finds Issues

**Protocol**:

```yaml
remediation_protocol:
  1_identify:
    action: "List all issues found"
    priority: "Critical issues first"
  
  2_prioritize:
    critical:
      - "Tests failing"
      - "Coverage < 80%"
      - "Missing entire layer"
    high:
      - "Missing logging"
      - "Missing documentation"
      - "Standard endpoints not implemented"
    medium:
      - "README incomplete"
      - "Missing diagrams"
  
  3_fix:
    action: "Fix issues in priority order"
    note: "Don't proceed until critical issues fixed"
  
  4_validate:
    action: "Re-run validation"
    note: "Ensure issue actually fixed"
  
  5_update_context:
    action: "Record remediation in context"
    field: "session_memory.issues_found_and_fixed"
```

### Remediation Script

```bash
# Run comprehensive validation
python3 scripts/refactoring/validate_all.py {service}

# Output shows all issues
# Fix each issue
# Re-run validation
```

---

## 📊 Self-Review Metrics

### Track Review Effectiveness

```python
review_metrics = {
    "issues_found_per_review": "2-3 (average)",
    "critical_issues_found": "< 1 (target)",
    "time_spent_reviewing": "10-15 minutes per phase",
    "issues_fixed_before_next_phase": "100% (required)"
}
```

---

## ✅ Quick Self-Review Command

```bash
# One command to review everything
python3 scripts/refactoring/self_review.py {service}

# This checks:
# - All phases completed
# - All deliverables exist
# - Tests pass
# - Coverage >= 80%
# - Logging validated
# - Documentation validated
# - Quality gates pass
# 
# Outputs:
# ✅ or ❌ for each check
# List of issues found
# Recommendations for fixes
```

---

**Document Control**  
**Version**: 1.0.0  
**Last Updated**: October 9, 2025  
**For AI Agents**: Use this to review your work holistically  
**Owner**: Hackathon Team

