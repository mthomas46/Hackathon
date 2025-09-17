# Demo Scripts

This directory contains demonstration scripts for showcasing LLM Documentation Ecosystem capabilities.

## Demo Categories

### System Architecture Demos
- `demo_refactored_architecture.py` - Demonstrates the DDD architecture and clean code principles
- `demo_complete_system.py` - Full system demonstration with all services

### Interactive Demos
- `demo_interactive_cli.py` - Interactive CLI demonstration
- `demo_phase3_interactive.py` - Phase 3 feature demonstration
- `demo_phase4_phase5_enhancements.py` - Advanced feature demonstrations

### Workflow Demos
- `demo_workflow_management.py` - Workflow orchestration demonstrations
- `demo_service_health.py` - Service health monitoring demonstrations

## Demo Scope

Demo scripts focus on:
- ✅ Showcasing system capabilities and features
- ✅ Demonstrating user workflows and interactions
- ✅ Illustrating system architecture and design
- ✅ Providing examples for new users
- ✅ Validating end-to-end functionality

## What Demos DON'T Cover

Demo scripts do NOT test:
- ❌ Unit testing (belongs in service tests)
- ❌ Integration testing (belongs in integration tests)
- ❌ CLI testing (belongs in CLI tests)
- ❌ Validation (belongs in validation tests)

## Usage

```bash
# Demonstrate complete system
python scripts/demo/demo_complete_system.py

# Interactive CLI demo
python scripts/demo/demo_interactive_cli.py

# Workflow management demo
python scripts/demo/demo_workflow_management.py

# Architecture demonstration
python scripts/demo/demo_refactored_architecture.py
```

## Demo Best Practices

- Demos should be self-contained and runnable
- Include clear instructions and explanations
- Demonstrate real-world use cases
- Show both success and error scenarios
- Provide cleanup procedures
- Include timing and performance notes
