#!/usr/bin/env python3
"""
Checkpoint Creation Script

Creates a snapshot of current execution state for recovery purposes.
Should be called frequently (every 2 hours, before risky operations, after phases).

Usage:
    python3 scripts/refactoring/create_checkpoint.py [--name NAME] [--notes NOTES]

Example:
    python3 scripts/refactoring/create_checkpoint.py --name "phase3_domain_complete" --notes "Domain layer done"

Author: Hackathon Team
Version: 1.0.0
"""

import argparse
import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


class CheckpointCreator:
    """Creates execution checkpoints"""
    
    def __init__(self, project_root: Path, name: Optional[str] = None, notes: Optional[str] = None):
        self.project_root = project_root
        self.ai_execution_dir = project_root / ".ai_execution"
        self.checkpoints_dir = self.ai_execution_dir / "checkpoints"
        self.context_file = self.ai_execution_dir / "context.json"
        self.checkpoint_name = name
        self.checkpoint_notes = notes
        
    def create(self) -> dict:
        """Create checkpoint"""
        
        # Ensure checkpoints directory exists
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        
        # Load current context
        if not self.context_file.exists():
            return {
                "success": False,
                "error": "No execution context found. Run init_ai_execution.py first."
            }
        
        context = json.loads(self.context_file.read_text())
        
        # Generate checkpoint metadata
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        if self.checkpoint_name:
            checkpoint_id = f"checkpoint_{self.checkpoint_name}_{timestamp}"
        else:
            phase = context.get("current_state", {}).get("phase", "unknown")
            step = context.get("current_state", {}).get("step", "unknown")
            checkpoint_id = f"checkpoint_phase{phase}_step{step}_{timestamp}"
        
        checkpoint_file = self.checkpoints_dir / f"{checkpoint_id}.json"
        
        # Get git state
        git_state = self._get_git_state()
        
        # Get test state
        service = context.get("service")
        test_state = self._get_test_state(service) if service else {}
        
        # Build checkpoint
        checkpoint = {
            "checkpoint_id": checkpoint_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "execution_id": context.get("execution_id"),
            
            "context_snapshot": context,
            
            "code_state": {
                "git_commit": git_state.get("commit_sha"),
                "git_branch": git_state.get("branch"),
                "uncommitted_changes": git_state.get("uncommitted_changes", False),
                "uncommitted_files": git_state.get("uncommitted_files", [])
            },
            
            "test_state": test_state,
            
            "validation": {
                "context_valid": True,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            
            "notes": self.checkpoint_notes or "Automatic checkpoint",
            
            "recovery_instructions": self._generate_recovery_instructions(context)
        }
        
        # Write checkpoint
        checkpoint_file.write_text(json.dumps(checkpoint, indent=2))
        
        # Clean up old checkpoints (keep last 20)
        self._cleanup_old_checkpoints(keep=20)
        
        return {
            "success": True,
            "checkpoint_id": checkpoint_id,
            "checkpoint_file": str(checkpoint_file),
            "created_at": checkpoint["created_at"],
            "service": service,
            "phase": context.get("current_state", {}).get("phase"),
            "step": context.get("current_state", {}).get("step")
        }
    
    def _get_git_state(self) -> dict:
        """Get current git state"""
        
        try:
            # Get current commit
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            commit_sha = result.stdout.strip() if result.returncode == 0 else None
            
            # Get current branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            branch = result.stdout.strip() if result.returncode == 0 else None
            
            # Check for uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            uncommitted_files = []
            if result.returncode == 0 and result.stdout:
                uncommitted_files = [
                    line.strip() for line in result.stdout.split("\n") 
                    if line.strip()
                ]
            
            return {
                "commit_sha": commit_sha,
                "branch": branch,
                "uncommitted_changes": len(uncommitted_files) > 0,
                "uncommitted_files": uncommitted_files[:50]  # Limit to 50
            }
        
        except Exception as e:
            return {
                "error": f"Could not get git state: {e}"
            }
    
    def _get_test_state(self, service: str) -> dict:
        """Get test state for service"""
        
        service_path = self.project_root / "services" / service
        
        if not service_path.exists():
            return {"error": "Service not found"}
        
        try:
            # Run tests quickly
            result = subprocess.run(
                ["pytest", "--collect-only", "--quiet"],
                cwd=service_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Count tests
            test_count = result.stdout.count("test_") if result.returncode == 0 else 0
            
            # Check if tests pass
            result = subprocess.run(
                ["pytest", "--quiet", "--tb=no"],
                cwd=service_path,
                capture_output=True,
                timeout=120
            )
            
            all_tests_passing = result.returncode == 0
            
            return {
                "test_count": test_count,
                "all_tests_passing": all_tests_passing
            }
        
        except Exception as e:
            return {
                "error": f"Could not get test state: {e}"
            }
    
    def _generate_recovery_instructions(self, context: dict) -> str:
        """Generate recovery instructions"""
        
        service = context.get("service", "unknown")
        phase = context.get("current_state", {}).get("phase", "unknown")
        step = context.get("current_state", {}).get("step", "unknown")
        
        instructions = f"""To recover from this checkpoint:

1. Run recovery script:
   python3 scripts/refactoring/recover_session.py --service {service}

2. Validate restored state:
   python3 scripts/refactoring/validate_context_reality.py {service}

3. Check current step:
   Current Phase: {phase}
   Current Step: {step}

4. Continue from:
   Read: docs/refactoring/AI_AGENT_EXECUTION_GUIDE.md (Phase instructions)
   Continue implementing: {step}

5. Next steps:
   {', '.join(context.get('next_steps', ['See context for details'])[:3])}
"""
        
        return instructions
    
    def _cleanup_old_checkpoints(self, keep: int = 20):
        """Remove old checkpoints, keeping most recent N"""
        
        checkpoints = sorted(
            self.checkpoints_dir.glob("checkpoint_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # Remove old ones
        for old_checkpoint in checkpoints[keep:]:
            try:
                old_checkpoint.unlink()
            except Exception:
                pass


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Create execution checkpoint for recovery"
    )
    parser.add_argument(
        "--name",
        help="Checkpoint name (e.g., 'phase3_domain_complete')"
    )
    parser.add_argument(
        "--notes",
        help="Notes about this checkpoint"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory"
    )
    
    args = parser.parse_args()
    
    print(f"💾 Creating checkpoint...")
    print()
    
    # Create checkpoint
    creator = CheckpointCreator(args.project_root, args.name, args.notes)
    
    try:
        result = creator.create()
        
        if result["success"]:
            print("✅ Checkpoint created successfully!")
            print()
            print(f"📌 Checkpoint ID: {result['checkpoint_id']}")
            print(f"📁 File: {result['checkpoint_file']}")
            print(f"🕐 Created: {result['created_at']}")
            print()
            print(f"📊 State:")
            print(f"   Service: {result['service']}")
            print(f"   Phase: {result['phase']}")
            print(f"   Step: {result['step']}")
            print()
            print("💡 To recover from this checkpoint:")
            print(f"   python3 scripts/refactoring/recover_session.py --service {result['service']}")
            print()
            
            sys.exit(0)
        else:
            print(f"❌ Failed to create checkpoint: {result['error']}")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error creating checkpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

