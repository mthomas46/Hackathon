#!/usr/bin/env python3
"""
Execution Health Monitor

Monitors AI agent execution health to detect problems early.
PRIORITY 1 FIX #6 (stuck detection) and #7 (context overflow monitoring)

Usage:
    python3 scripts/refactoring/monitor_execution_health.py [--service NAME]

Author: Hackathon Team
Version: 1.0.0
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List


class ExecutionHealthMonitor:
    """Monitors execution health and detects problems"""
    
    # Thresholds
    STUCK_THRESHOLD_HOURS = 4
    TOKEN_WARNING_THRESHOLD = 200_000
    TOKEN_CRITICAL_THRESHOLD = 250_000
    
    def __init__(self, project_root: Path, service_name: str = None):
        self.project_root = project_root
        self.service_name = service_name
        self.context_file = project_root / ".ai_execution" / "context.json"
        self.issues = []
        self.warnings = []
        
    def monitor(self) -> dict:
        """Comprehensive health monitoring"""
        
        print("🏥 Execution Health Monitor")
        print("=" * 70)
        print()
        
        results = {
            "healthy": True,
            "issues": [],
            "warnings": [],
            "recommendations": [],
            "metrics": {}
        }
        
        # Check 1: Stuck detection
        print("🔍 Checking for stuck state...")
        stuck_check = self._check_stuck_state()
        if stuck_check["stuck"]:
            results["healthy"] = False
            results["issues"].append(stuck_check)
        elif stuck_check.get("warning"):
            results["warnings"].append(stuck_check)
        
        # Check 2: Context/token overflow (estimated)
        print("📊 Checking context size...")
        token_check = self._check_token_usage()
        if token_check["status"] == "critical":
            results["healthy"] = False
            results["issues"].append(token_check)
        elif token_check["status"] == "warning":
            results["warnings"].append(token_check)
        
        # Check 3: Progress rate
        print("📈 Checking progress rate...")
        progress_check = self._check_progress_rate()
        if progress_check.get("slow"):
            results["warnings"].append(progress_check)
        
        # Check 4: Context freshness
        print("🕐 Checking context freshness...")
        freshness_check = self._check_context_freshness()
        if freshness_check.get("stale"):
            results["warnings"].append(freshness_check)
        
        results["metrics"] = self._gather_metrics()
        
        return results
    
    def _check_stuck_state(self) -> dict:
        """Detect if execution is stuck (no progress for 4+ hours)"""
        
        if not self.context_file.exists():
            return {"stuck": False, "reason": "No context file"}
        
        context = json.loads(self.context_file.read_text())
        
        # Check last updated time
        last_updated_str = context.get("last_updated")
        if not last_updated_str:
            return {"stuck": False, "reason": "No timestamp"}
        
        last_updated = datetime.fromisoformat(last_updated_str.replace('Z', ''))
        time_since = datetime.utcnow() - last_updated
        hours_since = time_since.total_seconds() / 3600
        
        current_step = context["current_state"]["step"]
        
        # Check if step has changed recently
        completed_steps = context.get("completed_work", {}).get("steps", [])
        
        if completed_steps:
            last_completed = completed_steps[-1]
            last_step_time = datetime.fromisoformat(last_completed["completed_at"].replace('Z', ''))
            time_since_progress = datetime.utcnow() - last_step_time
            hours_since_progress = time_since_progress.total_seconds() / 3600
            
            if hours_since_progress >= self.STUCK_THRESHOLD_HOURS:
                return {
                    "stuck": True,
                    "severity": "high",
                    "hours_stuck": round(hours_since_progress, 1),
                    "current_step": current_step,
                    "last_completed_step": last_completed["step"],
                    "recommendation": "Consider different approach, rollback, or escalate to human"
                }
            elif hours_since_progress >= 2:
                return {
                    "stuck": False,
                    "warning": True,
                    "hours_since_progress": round(hours_since_progress, 1),
                    "message": "Progress slowing down",
                    "recommendation": "Monitor closely, may be stuck soon"
                }
        
        return {"stuck": False}
    
    def _check_token_usage(self) -> dict:
        """Estimate token usage and warn before overflow"""
        
        # Estimate based on context file size and conversation
        if not self.context_file.exists():
            return {"status": "unknown"}
        
        context_size = self.context_file.stat().st_size
        
        # Rough estimation: context JSON + conversation history
        # This is very approximate - in reality, need actual token counter
        estimated_tokens = context_size * 4  # Very rough multiplier
        
        # Check session log size if exists
        session_log = self.context_file.parent / "session_log.md"
        if session_log.exists():
            log_size = session_log.stat().st_size
            estimated_tokens += log_size * 2
        
        # Add estimate for conversation (harder to measure)
        context = json.loads(self.context_file.read_text())
        completed_steps = len(context.get("completed_work", {}).get("steps", []))
        estimated_conversation_tokens = completed_steps * 5000  # ~5K tokens per step
        
        total_estimate = estimated_tokens + estimated_conversation_tokens
        
        if total_estimate >= self.TOKEN_CRITICAL_THRESHOLD:
            return {
                "status": "critical",
                "severity": "high",
                "estimated_tokens": total_estimate,
                "threshold": self.TOKEN_CRITICAL_THRESHOLD,
                "message": "Context size critical - must create checkpoint and start fresh session",
                "recommendation": "IMMEDIATE: Run create_checkpoint.py, write summary, start new session"
            }
        elif total_estimate >= self.TOKEN_WARNING_THRESHOLD:
            return {
                "status": "warning",
                "severity": "medium",
                "estimated_tokens": total_estimate,
                "threshold": self.TOKEN_WARNING_THRESHOLD,
                "percent_used": round((total_estimate / self.TOKEN_CRITICAL_THRESHOLD) * 100, 1),
                "message": "Context size approaching limit",
                "recommendation": "Create checkpoint soon, plan for session refresh"
            }
        else:
            return {
                "status": "healthy",
                "estimated_tokens": total_estimate,
                "percent_used": round((total_estimate / self.TOKEN_CRITICAL_THRESHOLD) * 100, 1)
            }
    
    def _check_progress_rate(self) -> dict:
        """Check if progress rate is acceptable"""
        
        if not self.context_file.exists():
            return {}
        
        context = json.loads(self.context_file.read_text())
        
        completed_steps = context.get("completed_work", {}).get("steps", [])
        if len(completed_steps) < 2:
            return {"slow": False, "reason": "Too early to assess"}
        
        # Calculate average time per step
        first_step = datetime.fromisoformat(completed_steps[0]["completed_at"].replace('Z', ''))
        last_step = datetime.fromisoformat(completed_steps[-1]["completed_at"].replace('Z', ''))
        
        time_span = last_step - first_step
        hours_span = time_span.total_seconds() / 3600
        steps_per_hour = len(completed_steps) / hours_span if hours_span > 0 else 0
        
        if steps_per_hour < 0.25:  # Less than 1 step per 4 hours
            return {
                "slow": True,
                "severity": "low",
                "steps_per_hour": round(steps_per_hour, 2),
                "message": "Progress rate is slow",
                "recommendation": "Review if steps are too complex or if AI is struggling"
            }
        
        return {"slow": False, "steps_per_hour": round(steps_per_hour, 2)}
    
    def _check_context_freshness(self) -> dict:
        """Check if context was updated recently"""
        
        if not self.context_file.exists():
            return {"stale": False}
        
        context = json.loads(self.context_file.read_text())
        
        last_updated_str = context.get("last_updated")
        if not last_updated_str:
            return {"stale": True, "reason": "No timestamp"}
        
        last_updated = datetime.fromisoformat(last_updated_str.replace('Z', ''))
        time_since = datetime.utcnow() - last_updated
        minutes_since = time_since.total_seconds() / 60
        
        if minutes_since > 60:  # Over 1 hour
            return {
                "stale": True,
                "severity": "low",
                "minutes_since_update": round(minutes_since, 1),
                "message": "Context not updated in over an hour",
                "recommendation": "Ensure context is being updated regularly (every 30 min)"
            }
        
        return {"stale": False, "minutes_since_update": round(minutes_since, 1)}
    
    def _gather_metrics(self) -> dict:
        """Gather current metrics"""
        
        if not self.context_file.exists():
            return {}
        
        context = json.loads(self.context_file.read_text())
        
        return {
            "current_phase": context["current_state"]["phase"],
            "current_step": context["current_state"]["step"],
            "progress_percent": context["current_state"]["progress_percent"],
            "completed_steps": len(context.get("completed_work", {}).get("steps", [])),
            "completed_phases": len(context.get("completed_work", {}).get("phases", [])),
            "active_blockers": len(context.get("session_memory", {}).get("blockers", []))
        }


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Monitor AI execution health"
    )
    parser.add_argument(
        "--service",
        help="Service name (optional)"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory"
    )
    
    args = parser.parse_args()
    
    monitor = ExecutionHealthMonitor(args.project_root, args.service)
    
    try:
        results = monitor.monitor()
        
        print()
        print("=" * 70)
        print("📊 HEALTH CHECK RESULTS")
        print("=" * 70)
        print()
        
        # Overall health
        if results["healthy"]:
            print("✅ HEALTHY - No critical issues detected")
        else:
            print("❌ UNHEALTHY - Critical issues found")
        print()
        
        # Issues
        if results["issues"]:
            print(f"🚨 CRITICAL ISSUES ({len(results['issues'])}):")
            for i, issue in enumerate(results["issues"], 1):
                print(f"{i}. {issue.get('message', 'Issue detected')}")
                if "recommendation" in issue:
                    print(f"   → {issue['recommendation']}")
                if "hours_stuck" in issue:
                    print(f"   ⏰ Stuck for: {issue['hours_stuck']} hours")
                if "estimated_tokens" in issue:
                    print(f"   📊 Estimated tokens: {issue['estimated_tokens']:,}")
                print()
        
        # Warnings
        if results["warnings"]:
            print(f"⚠️  WARNINGS ({len(results['warnings'])}):")
            for i, warning in enumerate(results["warnings"], 1):
                print(f"{i}. {warning.get('message', 'Warning')}")
                if "recommendation" in warning:
                    print(f"   → {warning['recommendation']}")
                print()
        
        # Metrics
        if results["metrics"]:
            print("📈 CURRENT METRICS:")
            metrics = results["metrics"]
            print(f"   Phase: {metrics.get('current_phase', 'Unknown')}")
            print(f"   Step: {metrics.get('current_step', 'Unknown')}")
            print(f"   Progress: {metrics.get('progress_percent', 0)}%")
            print(f"   Completed Steps: {metrics.get('completed_steps', 0)}")
            print(f"   Completed Phases: {metrics.get('completed_phases', 0)}")
            if metrics.get('active_blockers', 0) > 0:
                print(f"   ⚠️  Active Blockers: {metrics['active_blockers']}")
            print()
        
        # Recommendations
        if not results["healthy"] or results["warnings"]:
            print("💡 RECOMMENDATIONS:")
            if any(i.get("stuck") for i in results["issues"]):
                print("  1. STUCK DETECTED - Try different approach or rollback")
                print("  2. Consider: python3 scripts/refactoring/rollback_step.py --steps-back 1")
                print("  3. Or escalate to human if truly blocked")
            if any(i.get("status") == "critical" for i in results["issues"]):
                print("  1. CONTEXT CRITICAL - Must create checkpoint NOW")
                print("  2. Run: python3 scripts/refactoring/create_checkpoint.py")
                print("  3. Write summary and start fresh session")
            print()
        
        # Output JSON
        print(json.dumps(results, indent=2))
        
        sys.exit(0 if results["healthy"] else 1)
    
    except Exception as e:
        print(f"❌ Error during monitoring: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

