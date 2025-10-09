#!/usr/bin/env python3
"""
Human Escalation Script
PRIORITY 2 FIX #10 - AI can ask for human help when stuck

Usage:
    python3 scripts/refactoring/escalate_to_human.py --reason "Description of issue"

Author: Hackathon Team
Version: 1.0.0
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime


def escalate_to_human(reason: str, project_root: Path):
    """Create help request for human review"""
    
    # Load current context
    context_file = project_root / ".ai_execution" / "context.json"
    
    if context_file.exists():
        context = json.loads(context_file.read_text())
    else:
        context = {"error": "No context available"}
    
    # Create escalation
    escalation = {
        "type": "ai_escalation",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "reason": reason,
        "service": context.get("service", "unknown"),
        "current_state": context.get("current_state", {}),
        "completed_work": context.get("completed_work", {}),
        "blockers": context.get("session_memory", {}).get("blockers", []),
        "question": "I need human guidance on how to proceed",
        "context_snapshot": context
    }
    
    # Save escalation
    escalations_dir = project_root / ".ai_execution" / "escalations"
    escalations_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    escalation_file = escalations_dir / f"escalation_{timestamp}.json"
    
    escalation_file.write_text(json.dumps(escalation, indent=2))
    
    # Print instructions
    print()
    print("🆘 ESCALATED TO HUMAN")
    print("=" * 70)
    print()
    print(f"📝 Escalation file: {escalation_file}")
    print(f"🔍 Reason: {reason}")
    print()
    print("📊 Current State:")
    print(f"   Service: {escalation['service']}")
    print(f"   Phase: {escalation['current_state'].get('phase', 'Unknown')}")
    print(f"   Step: {escalation['current_state'].get('step', 'Unknown')}")
    print()
    print("💡 Next Steps:")
    print("   1. Human reviews escalation file")
    print("   2. Human provides guidance or fixes issue")
    print("   3. AI resumes work with new approach")
    print()
    print("⏸️  Execution paused - waiting for human input")
    print()
    
    return escalation_file


def main():
    parser = argparse.ArgumentParser(description="Escalate to human for help")
    parser.add_argument("--reason", required=True, help="Reason for escalation")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    
    escalation_file = escalate_to_human(args.reason, args.project_root)
    
    sys.exit(2)  # Special exit code for "needs human"


if __name__ == "__main__":
    main()

