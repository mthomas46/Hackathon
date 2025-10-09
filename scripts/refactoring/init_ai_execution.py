#!/usr/bin/env python3
"""
AI Execution Context Initializer

Initializes the execution context for AI agent refactoring.

Usage:
    python init_ai_execution.py [service-name]

Example:
    python init_ai_execution.py doc-store
"""

import os
import sys
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


def generate_execution_id() -> str:
    """Generate unique execution ID"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:6]
    return f"exec_{timestamp}_{unique_id}"


def create_initial_context(service_name: str = None) -> dict:
    """Create initial execution context"""
    return {
        "execution_id": generate_execution_id(),
        "service": service_name,  # FIX #1: Add service at root level for validation
        "started_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "last_updated": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "current_state": {
            "phase": "Phase 1: Audit & Analysis" if service_name else "Not Started",
            "step": "1.1 Service Audit" if service_name else None,
            "service": service_name,
            "progress_percent": 0
        },
        "completed_work": {
            "phases": [],
            "checkpoints": []
        },
        "next_work": [
            {
                "step": "1.1 Service Audit",
                "estimated_duration_minutes": 30,
                "dependencies": []
            }
        ] if service_name else [],
        "scope": {
            "service": service_name,
            "tier": determine_tier(service_name) if service_name else None,
            "bounded_context": None,
            "out_of_scope": [
                "Modifying other services",
                "Changing database schema globally",
                "Altering authentication system"
            ]
        },
        "session_memory": {
            "key_decisions": [],
            "patterns_identified": [],
            "blockers": []
        },
        "metadata": {
            "version": "1.0.0",
            "ai_agent": "cursor",
            "plan_version": "4.0.0"
        }
    }


def determine_tier(service_name: str) -> str:
    """Determine service tier"""
    tier1 = ["redis", "doc-store", "orchestrator", "llm-gateway"]
    tier2 = ["analysis-service", "prompt-store", "source-agent", "discovery-agent", "memory-agent"]
    
    if service_name in tier1:
        return "Tier 1: Foundation Services"
    elif service_name in tier2:
        return "Tier 2: Core Services"
    else:
        return "Tier 3+: Integration/Analysis/User-Facing Services"


def create_ai_execution_directory(repo_root: Path):
    """Create .ai_execution directory"""
    ai_exec_dir = repo_root / ".ai_execution"
    ai_exec_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (ai_exec_dir / "checkpoints").mkdir(exist_ok=True)
    (ai_exec_dir / "sessions").mkdir(exist_ok=True)
    
    # Create .gitignore to exclude context files from git
    gitignore_path = ai_exec_dir / ".gitignore"
    gitignore_path.write_text("*\n!.gitignore\n")
    
    return ai_exec_dir


def create_session_log(ai_exec_dir: Path):
    """Create initial session log"""
    session_log_path = ai_exec_dir / "session_log.md"
    
    content = """# AI Agent Execution Session Log

This file tracks all AI agent execution sessions.

## Session Guidelines

Each session should:
1. Load context from context.json
2. Review last session summary
3. Execute planned work
4. Update context regularly (every 30 minutes)
5. Create checkpoint at significant milestones
6. Generate session summary before ending

---

"""
    
    session_log_path.write_text(content)
    return session_log_path


def create_quick_reference(ai_exec_dir: Path, service_name: str = None):
    """Create quick reference for AI agent"""
    quick_ref_path = ai_exec_dir / "QUICK_REFERENCE.md"
    
    content = f"""# AI Agent Quick Reference

**Current Service**: {service_name or "None selected"}  
**Execution Started**: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")} UTC

## 🎯 Current Objective

{f"Refactor the {service_name} service following the 6-phase methodology." if service_name else "Initialize AI execution context and select service to refactor."}

## 📋 Quick Commands

### Load Context
```python
import json
with open('.ai_execution/context.json') as f:
    context = json.load(f)
print(f"Phase: {{context['current_state']['phase']}}")
print(f"Step: {{context['current_state']['step']}}")
```

### Update Context
```bash
python scripts/refactoring/update_execution_context.py \\
  --step "3.2.1 Implement Application Layer" \\
  --status "completed"
```

### Run Validation
```bash
# Test coverage
cd services/{service_name or '<service>'} && pytest --cov

# Logging validation
python scripts/refactoring/validate_logging.py {service_name or '<service>'}

# Documentation validation
python scripts/refactoring/validate_service_documentation.py {service_name or '<service>'}

# Quality gates
python scripts/refactoring/check_quality_gates.py {service_name or '<service>'}
```

## 🗺️ Navigation

### Essential Documents (Priority 1)
1. [AI Agent Execution Guide](../../docs/refactoring/AI_AGENT_EXECUTION_GUIDE.md) ⭐
2. [Master Refactoring Plan](../../docs/refactoring/MASTER_REFACTORING_PLAN.md)
3. [Living Progress Tracker](../../docs/refactoring/LIVING_PROGRESS_TRACKER.md)

### Phase-Specific Guides
- **Phase 1**: [Service Audit Template](../../docs/refactoring/SERVICE_AUDIT_TEMPLATE.md)
- **Phase 2**: [DDD Config Example](../../config/ddd_config.yaml)
- **Phase 3**: 
  - [TDD Checklist](../../docs/refactoring/TDD_CHECKLIST.md)
  - [Comprehensive Testing Strategy](../../docs/refactoring/COMPREHENSIVE_TESTING_STRATEGY.md)
  - [Standardized Logging Strategy](../../docs/refactoring/STANDARDIZED_LOGGING_STRATEGY.md)
- **Phase 4**: [Workflow Testing Strategy](../../docs/refactoring/WORKFLOW_TESTING_STRATEGY.md)
- **Phase 5**: 
  - [Service Documentation Strategy](../../docs/refactoring/SERVICE_DOCUMENTATION_STRATEGY.md)
  - [API Standardization Strategy](../../docs/refactoring/API_STANDARDIZATION_STRATEGY.md)

### Always Reference
- [Naming Conventions](../../docs/refactoring/NAMING_CONVENTIONS_STANDARDS.md)

## 🎯 Current Phase Instructions

{f'''
### Phase 1: Audit & Analysis

**Next Steps**:
1. Run: `python scripts/refactoring/audit_service.py {service_name}`
2. Review audit report
3. Create dependency map
4. Complete gap analysis
''' if service_name else '''
### No Service Selected

**Next Steps**:
1. Review [LIVING_PROGRESS_TRACKER.md](../../docs/refactoring/LIVING_PROGRESS_TRACKER.md)
2. Select next service from appropriate tier
3. Run: `python scripts/refactoring/init_ai_execution.py <service-name>`
'''}

## ⚠️ Scope Boundaries

### ✅ In Scope
- Modify current service ({service_name or '<service>'})
- Create tests for current service
- Update documentation for current service
- Add logging to current service
- Update execution context

### ❌ Out of Scope
- Modify other services
- Change global configurations
- Alter database schemas globally
- Skip quality gates
- Reduce test coverage below 80%

## 🔄 Context Update Protocol

**MUST update context**:
- After completing any step
- Every 30 minutes during long tasks
- When making key decisions
- When encountering blockers
- Before ending session

## 📊 Progress Tracking

Track these in context.json:
- `current_state.progress_percent` (0-100)
- `completed_work.phases[]` (list of completed phases)
- `session_memory.key_decisions[]` (important decisions)
- `session_memory.blockers[]` (current blockers)

---

**Remember**: This is AI-assisted refactoring. Follow the plan, maintain context, stay in scope!
"""
    
    quick_ref_path.write_text(content)
    return quick_ref_path


def main():
    """Main entry point"""
    service_name = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Determine repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    
    print("\n🤖 Initializing AI Execution Context\n")
    
    # Create .ai_execution directory
    ai_exec_dir = create_ai_execution_directory(repo_root)
    print(f"✓ Created directory: {ai_exec_dir}")
    
    # Create initial context
    context = create_initial_context(service_name)
    context_path = ai_exec_dir / "context.json"
    
    with open(context_path, "w") as f:
        json.dump(context, f, indent=2)
    print(f"✓ Created context: {context_path}")
    
    # Create session log
    session_log_path = create_session_log(ai_exec_dir)
    print(f"✓ Created session log: {session_log_path}")
    
    # Create quick reference
    quick_ref_path = create_quick_reference(ai_exec_dir, service_name)
    print(f"✓ Created quick reference: {quick_ref_path}")
    
    print(f"\n📊 Execution Context Initialized")
    print(f"   Execution ID: {context['execution_id']}")
    print(f"   Service: {service_name or 'None (select one next)'}")
    print(f"   Phase: {context['current_state']['phase']}")
    
    if service_name:
        print(f"\n📝 Next Steps:")
        print(f"   1. Review: .ai_execution/QUICK_REFERENCE.md")
        print(f"   2. Read: docs/refactoring/AI_AGENT_EXECUTION_GUIDE.md")
        print(f"   3. Execute: python scripts/refactoring/audit_service.py {service_name}")
    else:
        print(f"\n📝 Next Steps:")
        print(f"   1. Review: docs/refactoring/LIVING_PROGRESS_TRACKER.md")
        print(f"   2. Select service to refactor")
        print(f"   3. Run: python scripts/refactoring/init_ai_execution.py <service-name>")
    
    print(f"\n📚 Key Files:")
    print(f"   - Context: .ai_execution/context.json")
    print(f"   - Session Log: .ai_execution/session_log.md")
    print(f"   - Quick Ref: .ai_execution/QUICK_REFERENCE.md")
    print(f"   - AI Guide: docs/refactoring/AI_AGENT_EXECUTION_GUIDE.md")


if __name__ == "__main__":
    main()

