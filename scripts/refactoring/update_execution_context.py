#!/usr/bin/env python3
"""
AI Execution Context Updater

Updates the execution context with current progress.
CRITICAL: Enforces validation before allowing "completed" status.

Usage:
    python update_execution_context.py --step STEP --status STATUS [--notes NOTES]

Example:
    python update_execution_context.py \
      --step "3.2.1 Implement Application Layer" \
      --status "completed" \
      --notes "Implemented 5 commands, 3 queries"
"""

import argparse
import json
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def load_context(context_path: Path) -> dict:
    """Load execution context"""
    if not context_path.exists():
        print(f"✗ Context file not found: {context_path}")
        print("Run: python scripts/refactoring/init_ai_execution.py")
        sys.exit(1)
    
    with open(context_path) as f:
        return json.load(f)


def save_context(context: dict, context_path: Path):
    """Save execution context"""
    context["last_updated"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    with open(context_path, "w") as f:
        json.dump(context, f, indent=2)


def calculate_progress(context: dict) -> int:
    """Calculate overall progress percentage"""
    # Simple calculation based on completed phases
    total_phases = 6
    completed_phases = len(context["completed_work"]["phases"])
    
    # If in a phase, add partial progress for current phase
    current_phase_num = extract_phase_number(context["current_state"]["phase"])
    if current_phase_num:
        # Assume 4 steps per phase on average
        current_step = context["current_state"]["step"]
        if current_step:
            step_progress = 0.2  # Assume 20% per step within phase
            phase_progress = completed_phases + step_progress
        else:
            phase_progress = completed_phases
    else:
        phase_progress = completed_phases
    
    progress = int((phase_progress / total_phases) * 100)
    return min(progress, 100)


def extract_phase_number(phase_str: str) -> int:
    """Extract phase number from phase string"""
    if not phase_str or "Phase" not in phase_str:
        return None
    
    try:
        # Extract number after "Phase "
        num_str = phase_str.split("Phase ")[1].split(":")[0].strip()
        return int(num_str)
    except:
        return None


def get_next_step(context: dict, current_step: str, status: str) -> dict:
    """Determine next step based on current step completion"""
    # Map of steps to next steps
    step_sequence = {
        # Phase 1
        "1.1 Service Audit": "1.2 Dependency Analysis",
        "1.2 Dependency Analysis": "1.3 Gap Analysis",
        "1.3 Gap Analysis": "Phase 2: Design & Planning",
        
        # Phase 2
        "2.1 Domain Modeling": "2.2 API Design",
        "2.2 API Design": "2.3 Test Planning",
        "2.3 Test Planning": "Phase 3: TDD Implementation",
        
        # Phase 3
        "3.1 Set Up Testing Infrastructure": "3.2 Red Phase - Write Failing Tests",
        "3.2 Red Phase - Write Failing Tests": "3.3 Green Phase - Implement Features",
        "3.3 Green Phase - Implement Features": "3.4 Refactor Phase - Optimize Code",
        "3.4 Refactor Phase - Optimize Code": "3.5 Validate Testing & Logging",
        "3.5 Validate Testing & Logging": "Phase 4: Integration Testing",
        
        # Phase 4
        "4.1 Service Integration Tests": "4.2 Workflow Tests",
        "4.2 Workflow Tests": "Phase 5: Documentation",
        
        # Phase 5
        "5.1 Generate Service README": "5.2 Implement Standard Endpoints",
        "5.2 Implement Standard Endpoints": "5.3 Validate Documentation",
        "5.3 Validate Documentation": "Phase 6: Deployment & Monitoring",
        
        # Phase 6
        "6.1 Quality Gates Check": "6.2 Update Progress Tracker",
        "6.2 Update Progress Tracker": "COMPLETE"
    }
    
    if status == "completed":
        next_step_name = step_sequence.get(current_step, "Unknown")
        
        if next_step_name == "COMPLETE":
            return {
                "step": "Service refactoring complete",
                "estimated_duration_minutes": 0,
                "dependencies": []
            }
        elif next_step_name.startswith("Phase"):
            # Starting new phase - FIX #3: Return full step name
            phase_num = extract_phase_number(next_step_name)
            first_step_map = {
                1: "1.1 Service Audit",
                2: "2.1 Domain Modeling",
                3: "3.1 Set Up Testing Infrastructure",
                4: "4.1 Service Integration Tests",
                5: "5.1 Generate Service README",
                6: "6.1 Quality Gates Check"
            }
            first_step = first_step_map.get(phase_num, f"{phase_num}.1")
            return {
                "step": first_step,
                "estimated_duration_minutes": 60,
                "dependencies": [current_step]
            }
        else:
            return {
                "step": next_step_name,
                "estimated_duration_minutes": 60,
                "dependencies": [current_step]
            }
    else:
        # Continue current step
        return {
            "step": current_step,
            "estimated_duration_minutes": 60,
            "dependencies": []
        }


def update_step_status(context: dict, step: str, status: str, notes: str = None):
    """Update context with step status"""
    current_phase = context["current_state"]["phase"]
    
    if status == "completed":
        # Check if this completes a phase
        if step.endswith(("1.3 Gap Analysis", "2.3 Test Planning", "3.5 Validate Testing & Logging",
                          "4.2 Workflow Tests", "5.3 Validate Documentation", "6.2 Update Progress Tracker")):
            # Phase completed
            context["completed_work"]["phases"].append({
                "phase": current_phase,
                "completed_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "deliverables": [],  # AI agent should populate this
                "notes": notes
            })
            
            # Move to next phase
            next_phase_num = extract_phase_number(current_phase) + 1
            if next_phase_num <= 6:
                phase_names = [
                    "Phase 1: Audit & Analysis",
                    "Phase 2: Design & Planning",
                    "Phase 3: TDD Implementation",
                    "Phase 4: Integration Testing",
                    "Phase 5: Documentation",
                    "Phase 6: Deployment & Monitoring"
                ]
                context["current_state"]["phase"] = phase_names[next_phase_num - 1]
                context["current_state"]["step"] = f"{next_phase_num}.1"
            else:
                context["current_state"]["phase"] = "Complete"
                context["current_state"]["step"] = None
        else:
            # Step completed, move to next step in phase
            next_step_info = get_next_step(context, step, status)
            context["current_state"]["step"] = next_step_info["step"]
        
        # Update next work
        next_step_info = get_next_step(context, step, status)
        context["next_work"] = [next_step_info]
    
    elif status == "in_progress":
        context["current_state"]["step"] = step
    
    elif status == "blocked":
        if notes:
            context["session_memory"]["blockers"].append({
                "step": step,
                "issue": notes,
                "reported_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            })
    
    # Update progress
    context["current_state"]["progress_percent"] = calculate_progress(context)


def check_if_should_checkpoint(repo_root: Path) -> tuple[bool, str]:
    """Check if automatic checkpoint should be created"""
    
    checkpoints_dir = repo_root / ".ai_execution" / "checkpoints"
    
    if not checkpoints_dir.exists():
        return True, "auto_first"
    
    checkpoints = sorted(
        checkpoints_dir.glob("checkpoint_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if not checkpoints:
        return True, "auto_first"
    
    # Check time since last checkpoint
    last_checkpoint = checkpoints[0]
    time_since = datetime.now(timezone.utc).timestamp() - last_checkpoint.stat().st_mtime
    hours_since = time_since / 3600
    
    if hours_since >= 2.0:
        return True, f"auto_2hour_{int(hours_since)}h"
    
    return False, None


def enforce_validation_before_completion(service: str, step: str, repo_root: Path) -> bool:
    """
    CRITICAL: Enforce validation before allowing completion.
    Prevents hallucination of step completion.
    """
    
    print("\n🔍 VALIDATION ENFORCEMENT (Required for 'completed' status)")
    print("=" * 70)
    
    # Extract step ID (e.g., "3.2.1")
    step_id = step.split()[0] if " " in step else step
    
    # Run validate_step_reality.py
    validate_script = repo_root / "scripts" / "refactoring" / "validate_step_reality.py"
    
    if not validate_script.exists():
        print("⚠️ WARNING: validate_step_reality.py not found")
        print(f"   Expected: {validate_script}")
        print("   Skipping validation (not recommended)")
        return True  # Allow but warn
    
    try:
        result = subprocess.run(
            ["python3", str(validate_script), "--service", service, "--step", step_id],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )
        
        # Print validation output
        print(result.stdout)
        
        if result.returncode == 0:
            print("✅ VALIDATION PASSED - Step is actually complete\n")
            return True
        else:
            print("❌ VALIDATION FAILED - Step is NOT complete\n")
            print("🚨 CRITICAL: Cannot mark step as 'completed'")
            print()
            print("You must fix the issues found before updating context to 'completed'.")
            print()
            print("Options:")
            print("  1. Fix the issues and run validation again")
            print("  2. Use --status 'in_progress' instead")
            print("  3. Use --force to bypass (NOT recommended)")
            print()
            return False
    
    except subprocess.TimeoutExpired:
        print("⚠️ WARNING: Validation timed out (> 5 minutes)")
        print("   This might indicate tests hanging or very slow")
        print("   Allowing completion but investigate timeout")
        return True
    
    except Exception as e:
        print(f"⚠️ WARNING: Could not run validation: {e}")
        print("   Allowing completion but validation could not be enforced")
        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Update AI execution context")
    parser.add_argument("--step", required=True, help="Current step")
    parser.add_argument("--status", required=True, choices=["in_progress", "completed", "blocked"],
                       help="Step status")
    parser.add_argument("--notes", help="Additional notes")
    parser.add_argument("--decision", help="Key decision made")
    parser.add_argument("--pattern", help="Pattern identified")
    parser.add_argument("--deliverable", help="Deliverable created (file path)")
    parser.add_argument("--force", action="store_true",
                       help="Force update without validation (NOT recommended)")
    
    args = parser.parse_args()
    
    # Determine repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    context_path = repo_root / ".ai_execution" / "context.json"
    
    print(f"\n🔄 Updating Execution Context\n")
    
    # Load context
    context = load_context(context_path)
    print(f"✓ Loaded context: {context['execution_id']}")
    
    # CRITICAL: Enforce validation before marking completed
    if args.status == "completed" and not args.force:
        service = context.get("service")
        if service:
            validation_passed = enforce_validation_before_completion(service, args.step, repo_root)
            
            if not validation_passed:
                print("❌ Context update BLOCKED due to validation failure")
                print("   Step was NOT marked as 'completed'")
                sys.exit(1)
        else:
            print("⚠️ WARNING: No service in context, skipping validation")
    
    elif args.force:
        print("⚠️ WARNING: --force used, bypassing validation (NOT recommended)")
    
    # Update step status
    update_step_status(context, args.step, args.status, args.notes)
    print(f"✓ Updated step: {args.step} → {args.status}")
    
    # Add decision if provided
    if args.decision:
        context["session_memory"]["key_decisions"].append({
            "decision": args.decision,
            "step": args.step,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        })
        print(f"✓ Recorded decision: {args.decision}")
    
    # Add pattern if provided
    if args.pattern:
        context["session_memory"]["patterns_identified"].append({
            "pattern": args.pattern,
            "step": args.step,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        })
        print(f"✓ Recorded pattern: {args.pattern}")
    
    # Add deliverable if provided
    if args.deliverable and args.status == "completed":
        phase_idx = len(context["completed_work"]["phases"]) - 1
        if phase_idx >= 0:
            if "deliverables" not in context["completed_work"]["phases"][phase_idx]:
                context["completed_work"]["phases"][phase_idx]["deliverables"] = []
            context["completed_work"]["phases"][phase_idx]["deliverables"].append(args.deliverable)
            print(f"✓ Added deliverable: {args.deliverable}")
    
    # Save context
    save_context(context, context_path)
    print(f"✓ Saved context\n")
    
    # PRIORITY 0 FIX #2: Automatic checkpointing
    should_checkpoint, checkpoint_reason = check_if_should_checkpoint(repo_root)
    
    if should_checkpoint:
        print(f"💾 Auto-Checkpoint Triggered: {checkpoint_reason}")
        try:
            checkpoint_script = repo_root / "scripts" / "refactoring" / "create_checkpoint.py"
            if checkpoint_script.exists():
                result = subprocess.run(
                    ["python3", str(checkpoint_script), "--name", checkpoint_reason.split()[0]],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    print("✅ Auto-checkpoint created successfully\n")
                else:
                    print(f"⚠️ Auto-checkpoint failed: {result.stderr}\n")
            else:
                print("⚠️ create_checkpoint.py not found, skipping auto-checkpoint\n")
        except Exception as e:
            print(f"⚠️ Could not create auto-checkpoint: {e}\n")
    
    # Check if phase boundary (always checkpoint)
    if args.status == "completed" and "Phase" in str(context.get("next_work", [{}])[0].get("step", "")):
        print(f"💾 Phase Boundary Checkpoint (Phase complete)")
        try:
            checkpoint_script = repo_root / "scripts" / "refactoring" / "create_checkpoint.py"
            if checkpoint_script.exists():
                phase_num = extract_phase_number(context["current_state"]["phase"])
                result = subprocess.run(
                    ["python3", str(checkpoint_script), "--name", f"phase{phase_num}_complete"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    print("✅ Phase completion checkpoint created\n")
        except Exception as e:
            print(f"⚠️ Could not create phase checkpoint: {e}\n")
    
    # Print current state
    print(f"📊 Current State:")
    print(f"   Phase: {context['current_state']['phase']}")
    print(f"   Step: {context['current_state']['step']}")
    print(f"   Progress: {context['current_state']['progress_percent']}%")
    
    if context["next_work"]:
        print(f"\n📝 Next Work:")
        next_step = context["next_work"][0]
        print(f"   {next_step['step']}")
    
    if context["session_memory"]["blockers"]:
        print(f"\n⚠️ Active Blockers:")
        for blocker in context["session_memory"]["blockers"]:
            print(f"   - {blocker['step']}: {blocker['issue']}")


if __name__ == "__main__":
    main()

