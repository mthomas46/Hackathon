# AI Agent Navigation Index

This file helps AI agents quickly find the right document for their current task.

## Quick Navigation by Task

### Starting Refactoring
1. Read: [AI_AGENT_EXECUTION_GUIDE.md](./AI_AGENT_EXECUTION_GUIDE.md) (Priority 1)
2. Read: [MASTER_REFACTORING_PLAN.md](./MASTER_REFACTORING_PLAN.md) (Priority 1)
3. Check: [LIVING_PROGRESS_TRACKER.md](./LIVING_PROGRESS_TRACKER.md) (Priority 2)

### During Phase 1 (Audit & Analysis)
- [SERVICE_AUDIT_TEMPLATE.md](./SERVICE_AUDIT_TEMPLATE.md)
- [MASTER_REFACTORING_PLAN.md](./MASTER_REFACTORING_PLAN.md) → "Phase 1: Audit & Analysis"

### During Phase 2 (Design & Planning)
- [NAMING_CONVENTIONS_STANDARDS.md](./NAMING_CONVENTIONS_STANDARDS.md)
- [MASTER_REFACTORING_PLAN.md](./MASTER_REFACTORING_PLAN.md) → "Phase 2: Design & Planning"

### During Phase 3 (TDD Implementation)
- [TDD_CHECKLIST.md](./TDD_CHECKLIST.md)
- [COMPREHENSIVE_TESTING_STRATEGY.md](./COMPREHENSIVE_TESTING_STRATEGY.md)
- [STANDARDIZED_LOGGING_STRATEGY.md](./STANDARDIZED_LOGGING_STRATEGY.md)
- [NAMING_CONVENTIONS_STANDARDS.md](./NAMING_CONVENTIONS_STANDARDS.md)

### During Phase 4 (Integration Testing)
- [WORKFLOW_TESTING_STRATEGY.md](./WORKFLOW_TESTING_STRATEGY.md)
- [API_VERSIONING_STRATEGY.md](./API_VERSIONING_STRATEGY.md)

### During Phase 5 (Documentation)
- [SERVICE_DOCUMENTATION_STRATEGY.md](./SERVICE_DOCUMENTATION_STRATEGY.md)
- [API_STANDARDIZATION_STRATEGY.md](./API_STANDARDIZATION_STRATEGY.md)

### During Phase 6 (Deployment)
- [MASTER_REFACTORING_PLAN.md](./MASTER_REFACTORING_PLAN.md) → "Quality Gates"

## Documents by Priority

### Priority 1 (Read First)
- AI_AGENT_EXECUTION_GUIDE.md
- MASTER_REFACTORING_PLAN.md

### Priority 2 (Read Early)
- LIVING_PROGRESS_TRACKER.md
- NAMING_CONVENTIONS_STANDARDS.md

### Priority 3 (Phase-Specific)
- COMPREHENSIVE_TESTING_STRATEGY.md (Phase 3)
- STANDARDIZED_LOGGING_STRATEGY.md (Phase 3)
- SERVICE_DOCUMENTATION_STRATEGY.md (Phase 5)
- API_STANDARDIZATION_STRATEGY.md (Phase 5)

### Priority 4 (Reference)
- SERVICE_AUDIT_TEMPLATE.md
- TDD_CHECKLIST.md
- WORKFLOW_TESTING_STRATEGY.md

## AI Agent Tips

1. **Always start** with AI_AGENT_EXECUTION_GUIDE.md
2. **Load context** from .ai_execution/context.json
3. **Check current phase** and read phase-specific docs
4. **Update context** every 30 minutes
5. **Stay in scope** - don't modify other services
6. **Follow TDD** - Red → Green → Refactor
7. **Validate often** - run checks after each step

## Metadata Explanation

Each document has AI metadata in YAML frontmatter:

```yaml
ai_metadata:
  purpose: "what this document is for"
  read_priority: 1-5 (1 = highest priority)
  context_level: strategic|tactical|operational|reference
  tags: [list, of, relevant, tags]
  when_to_read: "when AI agent should read this"
  key_sections: [list, of, important, sections]
  execution_relevance: critical|high|phase-specific|reference
```

Use these metadata to:
- Determine reading order
- Understand document purpose
- Navigate to relevant sections
- Know when to reference

---

**For AI Agents**: This index is your starting point for navigation.
