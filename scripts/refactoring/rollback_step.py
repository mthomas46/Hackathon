#!/usr/bin/env python3
"""
Rollback Step Script

Rolls back to a previous checkpoint when step goes wrong.
PRIORITY 1 FIX #5

Usage:
    python3 scripts/refactoring/rollback_step.py --to-checkpoint <checkpoint_id>
    python3 scripts/refactoring/rollback_step.py --steps-back <N>

Examples:
    # Rollback to specific checkpoint
    python3 scripts/refactoring/rollback_step.py \
      --to-checkpoint checkpoint_phase3_domain_20251009_120000

    # Rollback N steps
    python3 scripts/refactoring/rollback_step.py --steps-back 2

Author: Hackathon Team
Version: 1.0.0
"""

import argparse
import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional


class StepRollback:
    """Handles rollback to previous checkpoints"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.ai_execution_dir = project_root / ".ai_execution"
        self.checkpoints_dir = self.ai_execution_dir / "checkpoints"
        self.context_file = self.ai_execution_dir / "context.json"
        
    def rollback_to_checkpoint(self, checkpoint_id: str) -> dict:
        """Rollback to specific checkpoint"""
        
        checkpoint_file = self.checkpoints_dir / f"{checkpoint_id}.json"
        
        if not checkpoint_file.exists():
            return {
                "success": False,
                "error": f"Checkpoint not found: {checkpoint_id}"
            }
        
        print(f"🔄 Rolling back to checkpoint: {checkpoint_id}")
        print("=" * 70)
        print()
        
        # Load checkpoint
        checkpoint = json.loads(checkpoint_file.read_text())
        
        # Show what will be rolled back
        print("📊 Checkpoint State:")
        print(f"   Created: {checkpoint['created_at']}")
        print(f"   Phase: {checkpoint['context_snapshot']['current_state']['phase']}")
        print(f"   Step: {checkpoint['context_snapshot']['current_state']['step']}")
        print()
        
        # Get current state for comparison
        if self.context_file.exists():
            current_context = json.loads(self.context_file.read_text())
            print("📊 Current State (will be lost):")
            print(f"   Phase: {current_context['current_state']['phase']}")
            print(f"   Step: {current_context['current_state']['step']}")
            print()
        
        # Confirm rollback
        print("⚠️  WARNING: This will:")
        print("   1. Restore context to checkpoint state")
        print("   2. Revert code changes (git reset)")
        print("   3. Lose any uncommitted work after checkpoint")
        print()
        
        response = input("Continue with rollback? [y/N]: ")
        if response.lower() != 'y':
            print("❌ Rollback cancelled")
            return {"success": False, "error": "User cancelled"}
        
        print()
        
        # Step 1: Restore context
        print("1️⃣  Restoring execution context...")
        self.context_file.write_text(json.dumps(checkpoint['context_snapshot'], indent=2))
        print("   ✅ Context restored")
        
        # Step 2: Revert code changes (SAFELY)
        if "git_commit" in checkpoint.get("code_state", {}):
            git_commit = checkpoint["code_state"]["git_commit"]
            print(f"2️⃣  Reverting code to commit: {git_commit[:8]}")
            
            try:
                # SAFETY: Create backup branch first
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                backup_branch = f"backup_before_rollback_{timestamp}"
                
                print(f"   🛡️  Creating safety backup branch: {backup_branch}")
                result = subprocess.run(
                    ["git", "branch", backup_branch],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print(f"   ✅ Backup branch created (can recover from here if needed)")
                else:
                    print(f"   ⚠️ Could not create backup branch: {result.stderr}")
                    print(f"   ⚠️ Proceeding anyway (use with caution)")
                
                # Ask if should hard reset or soft reset
                print("   Options:")
                print("     [h] Hard reset (discard all changes)")
                print("     [s] Soft reset (keep changes uncommitted)")
                reset_type = input("   Choose reset type [h/s]: ").lower()
                
                if reset_type == 'h':
                    result = subprocess.run(
                        ["git", "reset", "--hard", git_commit],
                        cwd=self.project_root,
                        capture_output=True,
                        text=True
                    )
                else:
                    result = subprocess.run(
                        ["git", "reset", "--soft", git_commit],
                        cwd=self.project_root,
                        capture_output=True,
                        text=True
                    )
                
                if result.returncode == 0:
                    print(f"   ✅ Code reverted to {git_commit[:8]}")
                    print(f"   💡 If needed, recover from: git checkout {backup_branch}")
                else:
                    print(f"   ⚠️ Git reset failed: {result.stderr}")
            except Exception as e:
                print(f"   ⚠️ Could not revert code: {e}")
        
        # Step 3: Log rollback
        print("3️⃣  Logging rollback...")
        rollback_log = self.ai_execution_dir / "rollback_log.md"
        log_entry = f"""
## Rollback - {datetime.utcnow().isoformat()}

**From State**:
- Phase: {current_context['current_state']['phase'] if 'current_context' in locals() else 'Unknown'}
- Step: {current_context['current_state']['step'] if 'current_context' in locals() else 'Unknown'}

**To Checkpoint**: {checkpoint_id}
- Phase: {checkpoint['context_snapshot']['current_state']['phase']}
- Step: {checkpoint['context_snapshot']['current_state']['step']}

**Reason**: Manual rollback requested

---
"""
        with open(rollback_log, 'a') as f:
            f.write(log_entry)
        
        print("   ✅ Rollback logged")
        print()
        
        print("✅ ROLLBACK COMPLETE")
        print()
        print("📊 Current State (after rollback):")
        restored_context = json.loads(self.context_file.read_text())
        print(f"   Phase: {restored_context['current_state']['phase']}")
        print(f"   Step: {restored_context['current_state']['step']}")
        print()
        print("💡 Next Steps:")
        print("   1. Review checkpoint recovery instructions")
        print("   2. Validate current state")
        print("   3. Try different approach for failed step")
        print()
        
        return {
            "success": True,
            "checkpoint_id": checkpoint_id,
            "restored_state": restored_context["current_state"]
        }
    
    def rollback_n_steps(self, n: int) -> dict:
        """Rollback N steps by finding appropriate checkpoint"""
        
        if not self.checkpoints_dir.exists():
            return {
                "success": False,
                "error": "No checkpoints directory found"
            }
        
        checkpoints = sorted(
            self.checkpoints_dir.glob("checkpoint_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if not checkpoints:
            return {
                "success": False,
                "error": "No checkpoints available"
            }
        
        # Try to find checkpoint N steps back
        if n > len(checkpoints):
            print(f"⚠️ Only {len(checkpoints)} checkpoints available, using oldest")
            n = len(checkpoints)
        
        target_checkpoint = checkpoints[n - 1]
        checkpoint_id = target_checkpoint.stem
        
        print(f"🔍 Rolling back {n} step(s)...")
        print(f"   Target checkpoint: {checkpoint_id}")
        print()
        
        return self.rollback_to_checkpoint(checkpoint_id)
    
    def list_checkpoints(self):
        """List available checkpoints"""
        
        if not self.checkpoints_dir.exists():
            print("❌ No checkpoints directory found")
            return
        
        checkpoints = sorted(
            self.checkpoints_dir.glob("checkpoint_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if not checkpoints:
            print("❌ No checkpoints available")
            return
        
        print(f"📋 Available Checkpoints ({len(checkpoints)}):")
        print("=" * 70)
        print()
        
        for i, checkpoint_file in enumerate(checkpoints, 1):
            try:
                checkpoint = json.loads(checkpoint_file.read_text())
                created = datetime.fromisoformat(checkpoint['created_at'].replace('Z', ''))
                
                print(f"{i}. {checkpoint_file.stem}")
                print(f"   Created: {created.strftime('%Y-%m-%d %H:%M UTC')}")
                print(f"   Phase: {checkpoint['context_snapshot']['current_state']['phase']}")
                print(f"   Step: {checkpoint['context_snapshot']['current_state']['step']}")
                if 'notes' in checkpoint:
                    print(f"   Notes: {checkpoint['notes']}")
                print()
            except Exception as e:
                print(f"{i}. {checkpoint_file.stem} (error reading: {e})")
                print()


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Rollback to previous checkpoint"
    )
    parser.add_argument(
        "--to-checkpoint",
        help="Specific checkpoint ID to rollback to"
    )
    parser.add_argument(
        "--steps-back",
        type=int,
        help="Number of steps to rollback"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available checkpoints"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory"
    )
    
    args = parser.parse_args()
    
    rollback = StepRollback(args.project_root)
    
    if args.list:
        rollback.list_checkpoints()
        sys.exit(0)
    
    if not args.to_checkpoint and not args.steps_back:
        print("❌ Error: Must specify --to-checkpoint or --steps-back")
        print()
        print("Examples:")
        print("  # List checkpoints")
        print("  python3 rollback_step.py --list")
        print()
        print("  # Rollback to specific checkpoint")
        print("  python3 rollback_step.py --to-checkpoint checkpoint_phase3_domain_20251009_120000")
        print()
        print("  # Rollback 2 steps")
        print("  python3 rollback_step.py --steps-back 2")
        sys.exit(1)
    
    try:
        if args.to_checkpoint:
            result = rollback.rollback_to_checkpoint(args.to_checkpoint)
        else:
            result = rollback.rollback_n_steps(args.steps_back)
        
        if result["success"]:
            sys.exit(0)
        else:
            print(f"❌ Rollback failed: {result['error']}")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error during rollback: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

