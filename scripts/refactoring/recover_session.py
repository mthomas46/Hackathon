#!/usr/bin/env python3
"""
Session Recovery Script

Universal recovery from any interruption (IDE crash, session timeout, context loss).

Usage:
    python3 scripts/refactoring/recover_session.py [--service NAME]

Examples:
    # Auto-detect and recover
    python3 scripts/refactoring/recover_session.py
    
    # Recover specific service
    python3 scripts/refactoring/recover_session.py --service doc-store

Author: Hackathon Team
Version: 1.0.0
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import subprocess
from typing import Optional, Dict, Any


class SessionRecovery:
    """Session recovery system"""
    
    def __init__(self, project_root: Path, service_name: Optional[str] = None):
        self.project_root = project_root
        self.service_name = service_name
        self.ai_execution_dir = project_root / ".ai_execution"
        self.context_file = self.ai_execution_dir / "context.json"
        self.checkpoints_dir = self.ai_execution_dir / "checkpoints"
        
    def recover(self) -> dict:
        """Main recovery process"""
        
        print("🔄 Session Recovery Protocol")
        print("="*60)
        print()
        
        # Step 1: Assess situation
        print("📊 Step 1: Assessing situation...")
        recovery_sources = self._assess_recovery_sources()
        
        # Step 2: Choose recovery method
        print("🎯 Step 2: Choosing recovery method...")
        method = self._choose_recovery_method(recovery_sources)
        print(f"   Method: {method}")
        print()
        
        # Step 3: Execute recovery
        print(f"⚙️  Step 3: Executing recovery ({method})...")
        if method == "DIRECT_RESUME":
            context = self._direct_resume()
        elif method == "CHECKPOINT_RESTORE":
            context = self._checkpoint_restore()
        elif method == "LOG_RECONSTRUCTION":
            context = self._log_reconstruction()
        elif method == "GIT_RECONSTRUCTION":
            context = self._git_reconstruction()
        else:
            context = None
        
        if not context:
            print("❌ Recovery failed - manual restart required")
            return {
                "success": False,
                "method": method,
                "message": "Could not recover context"
            }
        
        # Step 4: Validate recovered state
        print("✅ Step 4: Validating recovered state...")
        is_valid, issues = self._validate_context(context)
        
        if not is_valid:
            print(f"⚠️  Warning: Recovered context has issues:")
            for issue in issues:
                print(f"   - {issue}")
            print()
        
        # Step 5: Display summary
        self._display_recovery_summary(context, method)
        
        return {
            "success": True,
            "method": method,
            "context": context,
            "issues": issues
        }
    
    def _assess_recovery_sources(self) -> dict:
        """Assess what recovery sources are available"""
        
        sources = {
            "context_file": False,
            "context_valid": False,
            "checkpoints": [],
            "session_log": False,
            "git_history": False
        }
        
        # Check context file
        if self.context_file.exists():
            sources["context_file"] = True
            print("   ✓ Context file exists")
            
            # Check if valid
            try:
                context = json.loads(self.context_file.read_text())
                if self._is_valid_context(context):
                    sources["context_valid"] = True
                    print("   ✓ Context file is valid")
                else:
                    print("   ⚠️  Context file is invalid")
            except Exception:
                print("   ⚠️  Context file is corrupted")
        else:
            print("   ✗ No context file")
        
        # Check checkpoints
        if self.checkpoints_dir.exists():
            checkpoints = sorted(
                self.checkpoints_dir.glob("*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            sources["checkpoints"] = [str(p) for p in checkpoints]
            if checkpoints:
                print(f"   ✓ {len(checkpoints)} checkpoint(s) available")
        else:
            print("   ✗ No checkpoints")
        
        # Check session log
        session_log = self.ai_execution_dir / "session_log.md"
        if session_log.exists():
            sources["session_log"] = True
            print("   ✓ Session log exists")
        else:
            print("   ✗ No session log")
        
        # Check git history
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.project_root,
                capture_output=True
            )
            if result.returncode == 0:
                sources["git_history"] = True
                print("   ✓ Git history available")
        except Exception:
            print("   ✗ No git history")
        
        print()
        return sources
    
    def _choose_recovery_method(self, sources: dict) -> str:
        """Choose best recovery method based on available sources"""
        
        if sources["context_valid"]:
            return "DIRECT_RESUME"
        elif sources["checkpoints"]:
            return "CHECKPOINT_RESTORE"
        elif sources["session_log"]:
            return "LOG_RECONSTRUCTION"
        elif sources["git_history"]:
            return "GIT_RECONSTRUCTION"
        else:
            return "MANUAL_RESTART"
    
    def _direct_resume(self) -> Optional[dict]:
        """Direct resume from valid context file"""
        
        try:
            context = json.loads(self.context_file.read_text())
            print("   ✓ Loaded context directly")
            return context
        except Exception as e:
            print(f"   ✗ Failed to load context: {e}")
            return None
    
    def _checkpoint_restore(self) -> Optional[dict]:
        """Restore from most recent checkpoint"""
        
        checkpoints = sorted(
            self.checkpoints_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for checkpoint in checkpoints:
            try:
                print(f"   Trying checkpoint: {checkpoint.name}")
                context = json.loads(checkpoint.read_text())
                
                # Extract context from checkpoint
                if "context_snapshot" in context:
                    recovered_context = context["context_snapshot"]
                else:
                    recovered_context = context
                
                # Restore to context file
                self.context_file.write_text(json.dumps(recovered_context, indent=2))
                
                print(f"   ✓ Restored from {checkpoint.name}")
                
                # Calculate time loss
                checkpoint_time = datetime.fromisoformat(context.get("created_at", ""))
                time_loss = datetime.utcnow() - checkpoint_time
                print(f"   ⚠️  Lost ~{time_loss.seconds // 60} minutes of work (acceptable)")
                
                return recovered_context
            except Exception as e:
                print(f"   ✗ Checkpoint failed: {e}")
                continue
        
        print("   ✗ No valid checkpoints found")
        return None
    
    def _log_reconstruction(self) -> Optional[dict]:
        """Reconstruct from session log"""
        
        session_log = self.ai_execution_dir / "session_log.md"
        
        try:
            log_content = session_log.read_text()
            
            # Parse log to extract last known state
            # Look for patterns like "Phase X: ..." and "Step: ..."
            import re
            
            phases = re.findall(r"Phase (\d+):", log_content)
            steps = re.findall(r"Step: ([\d.]+)", log_content)
            services = re.findall(r"Service: ([\w-]+)", log_content)
            
            if not phases or not services:
                print("   ✗ Log doesn't contain enough information")
                return None
            
            # Reconstruct basic context
            reconstructed = {
                "execution_id": f"recovered_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "service": services[-1] if services else self.service_name,
                "current_state": {
                    "phase": f"Phase {phases[-1]}" if phases else "Phase 1",
                    "step": steps[-1] if steps else "1.1",
                    "status": "in_progress"
                },
                "completed_work": [],
                "session_memory": {
                    "note": "Reconstructed from session log",
                    "confidence": "medium"
                }
            }
            
            # Save reconstructed context
            self.context_file.write_text(json.dumps(reconstructed, indent=2))
            
            print("   ✓ Reconstructed from session log")
            print("   ⚠️  Confidence: MEDIUM (validate before continuing)")
            
            return reconstructed
        except Exception as e:
            print(f"   ✗ Log reconstruction failed: {e}")
            return None
    
    def _git_reconstruction(self) -> Optional[dict]:
        """Reconstruct from git history"""
        
        if not self.service_name:
            # Try to detect service from recent commits
            try:
                result = subprocess.run(
                    ["git", "log", "-1", "--pretty=%s"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True
                )
                commit_msg = result.stdout.strip()
                
                # Extract service name from commit message
                import re
                match = re.search(r"\(([^)]+)\)", commit_msg)
                if match:
                    self.service_name = match.group(1)
                    print(f"   Detected service: {self.service_name}")
            except Exception:
                pass
        
        if not self.service_name:
            print("   ✗ Cannot reconstruct without service name")
            return None
        
        service_path = self.project_root / "services" / self.service_name
        
        # Analyze codebase state
        print(f"   Analyzing codebase for {self.service_name}...")
        
        phase = self._infer_phase_from_codebase(service_path)
        
        reconstructed = {
            "execution_id": f"git_recovered_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "service": self.service_name,
            "current_state": {
                "phase": f"Phase {phase}",
                "step": f"{phase}.1",
                "status": "in_progress"
            },
            "completed_work": [],
            "session_memory": {
                "note": "Reconstructed from git/codebase analysis",
                "confidence": "low"
            }
        }
        
        # Save reconstructed context
        self.ai_execution_dir.mkdir(exist_ok=True)
        self.context_file.write_text(json.dumps(reconstructed, indent=2))
        
        print(f"   ✓ Reconstructed from git (Phase {phase})")
        print("   ⚠️  Confidence: LOW (validate thoroughly)")
        
        return reconstructed
    
    def _infer_phase_from_codebase(self, service_path: Path) -> int:
        """Infer current phase from codebase state"""
        
        if not service_path.exists():
            return 1
        
        # Check for Phase 5 markers (documentation)
        readme = service_path / "README.md"
        if readme.exists() and readme.stat().st_size > 5000:
            return 5
        
        # Check for Phase 4 markers (integration tests)
        workflow_tests = service_path / "tests" / "workflows"
        if workflow_tests.exists():
            return 4
        
        # Check for Phase 3 markers (implementation)
        domain = service_path / "domain"
        tests = service_path / "tests"
        if domain.exists() and tests.exists():
            return 3
        
        # Check for Phase 2 markers (design)
        design = service_path / "design"
        if design.exists():
            return 2
        
        return 1
    
    def _is_valid_context(self, context: dict) -> bool:
        """Check if context is valid"""
        
        required_fields = ["execution_id", "service", "current_state"]
        return all(field in context for field in required_fields)
    
    def _validate_context(self, context: dict) -> tuple[bool, list]:
        """Validate recovered context"""
        
        issues = []
        
        if not context.get("execution_id"):
            issues.append("Missing execution_id")
        
        if not context.get("service"):
            issues.append("Missing service name")
        
        current_state = context.get("current_state", {})
        if not current_state.get("phase"):
            issues.append("Missing current phase")
        
        if not current_state.get("step"):
            issues.append("Missing current step")
        
        return len(issues) == 0, issues
    
    def _display_recovery_summary(self, context: dict, method: str):
        """Display recovery summary"""
        
        print()
        print("="*60)
        print("✅ RECOVERY SUCCESSFUL")
        print("="*60)
        print()
        
        print(f"📌 Recovery Method: {method}")
        print(f"🔧 Service: {context.get('service', 'N/A')}")
        print(f"📍 Phase: {context.get('current_state', {}).get('phase', 'N/A')}")
        print(f"📌 Step: {context.get('current_state', {}).get('step', 'N/A')}")
        print()
        
        if context.get("completed_work"):
            print("✅ Completed Work:")
            for work in context["completed_work"][:5]:
                print(f"  ✓ {work}")
            if len(context["completed_work"]) > 5:
                print(f"  ... and {len(context['completed_work']) - 5} more")
            print()
        
        print("🎯 Next Steps:")
        print(f"  1. Review current phase instructions")
        print(f"  2. Validate current state")
        print(f"  3. Continue from step: {context.get('current_state', {}).get('step')}")
        print()
        
        # Recommendations based on method
        if method == "CHECKPOINT_RESTORE":
            print("⚠️  Note: Some recent work may have been lost (check git diff)")
        elif method == "LOG_RECONSTRUCTION":
            print("⚠️  Note: Context reconstructed - validate thoroughly")
        elif method == "GIT_RECONSTRUCTION":
            print("⚠️  Note: Context inferred from code - verify phase/step is correct")
        print()


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Universal session recovery from any interruption"
    )
    parser.add_argument(
        "--service",
        help="Service name (will auto-detect if not provided)"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # Create recovery system
    recovery = SessionRecovery(args.project_root, args.service)
    
    # Execute recovery
    try:
        result = recovery.recover()
        
        if result["success"]:
            print("✅ Ready to continue!")
            sys.exit(0)
        else:
            print("❌ Recovery failed - manual intervention required")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error during recovery: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

