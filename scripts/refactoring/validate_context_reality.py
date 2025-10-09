#!/usr/bin/env python3
"""
Context Reality Validation Script

Validates that execution context matches actual codebase reality.
Detects context drift and hallucination.

Usage:
    python3 scripts/refactoring/validate_context_reality.py <service-name>

Example:
    python3 scripts/refactoring/validate_context_reality.py doc-store

Author: Hackathon Team
Version: 1.0.0
"""

import argparse
import json
import sys
import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


class ContextRealityValidator:
    """Validates context matches reality"""
    
    def __init__(self, service_name: str, project_root: Path):
        self.service_name = service_name
        self.project_root = project_root
        self.service_path = project_root / "services" / service_name
        self.context_file = project_root / ".ai_execution" / "context.json"
        self.discrepancies = []
        self.alignments = []
        
    def validate(self) -> dict:
        """Comprehensive context vs reality validation"""
        
        results = {
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "drift_score": 0.0,
            "drift_assessment": "",
            "discrepancies": [],
            "alignments": [],
            "checks_performed": 0,
            "checks_failed": 0
        }
        
        print(f"🔍 Validating Context vs Reality: {self.service_name}")
        print("=" * 70)
        print()
        
        # Load context
        if not self.context_file.exists():
            return {
                **results,
                "error": "No execution context found",
                "drift_score": 100.0
            }
        
        context = json.loads(self.context_file.read_text())
        
        # Validate service matches
        if context.get("service") != self.service_name:
            self.discrepancies.append({
                "check": "service_name",
                "context": context.get("service"),
                "reality": self.service_name,
                "severity": "critical"
            })
        
        # Check 1: Phase vs Reality
        print("📊 Checking phase alignment...")
        self._check_phase_alignment(context)
        
        # Check 2: Completed work exists
        print("✅ Checking completed work...")
        self._check_completed_work(context)
        
        # Check 3: Tests actually pass
        print("🧪 Checking test state...")
        self._check_test_state(context)
        
        # Check 4: Files mentioned in context exist
        print("📁 Checking file existence...")
        self._check_file_existence(context)
        
        # Check 5: Git state matches
        print("🔀 Checking git state...")
        self._check_git_state(context)
        
        # Calculate drift score
        checks = len(self.discrepancies) + len(self.alignments)
        failures = len(self.discrepancies)
        
        drift_score = (failures / checks * 100) if checks > 0 else 0.0
        drift_assessment = self._assess_drift(drift_score)
        
        results["drift_score"] = drift_score
        results["drift_assessment"] = drift_assessment
        results["discrepancies"] = self.discrepancies
        results["alignments"] = self.alignments
        results["checks_performed"] = checks
        results["checks_failed"] = failures
        
        return results
    
    def _check_phase_alignment(self, context: dict):
        """Check if context phase matches reality"""
        
        claimed_phase_str = context.get("current_state", {}).get("phase", "")
        
        # Extract phase number
        phase_match = re.search(r"Phase (\d+)", claimed_phase_str)
        claimed_phase = int(phase_match.group(1)) if phase_match else 0
        
        # Infer actual phase from codebase
        actual_phase = self._infer_phase_from_codebase()
        
        if claimed_phase == actual_phase:
            self.alignments.append({
                "check": "phase",
                "value": f"Phase {actual_phase}",
                "status": "aligned"
            })
        elif claimed_phase > actual_phase:
            self.discrepancies.append({
                "check": "phase",
                "context": f"Phase {claimed_phase}",
                "reality": f"Phase {actual_phase}",
                "severity": "high",
                "issue": f"Context claims Phase {claimed_phase} but code shows Phase {actual_phase}"
            })
        else:
            # Context behind reality (less severe)
            self.discrepancies.append({
                "check": "phase",
                "context": f"Phase {claimed_phase}",
                "reality": f"Phase {actual_phase}",
                "severity": "medium",
                "issue": "Context behind reality (may just need updating)"
            })
    
    def _infer_phase_from_codebase(self) -> int:
        """Infer current phase from codebase state"""
        
        if not self.service_path.exists():
            return 1  # Not started
        
        # Check Phase 5 markers
        readme = self.service_path / "README.md"
        if readme.exists() and readme.stat().st_size > 5000:
            # Check for AI enrichment
            readme_content = readme.read_text()
            if "<!-- @ai-section:" in readme_content:
                return 6  # Phase 6 (docs enriched)
            return 5  # Phase 5 (docs created)
        
        # Check Phase 4 markers
        workflow_tests = self.service_path / "tests" / "workflows"
        if workflow_tests.exists():
            return 4
        
        # Check Phase 3 markers
        domain = self.service_path / "domain"
        tests = self.service_path / "tests"
        if domain.exists() and tests.exists():
            test_files = list(tests.rglob("test_*.py"))
            if len(test_files) >= 10:
                return 3
        
        # Check Phase 2 markers
        design = self.service_path / "design"
        if design.exists():
            openapi = design / "openapi_v2.yaml"
            if openapi.exists():
                return 2
        
        return 1  # Phase 1
    
    def _check_completed_work(self, context: dict):
        """Check claimed completed work actually exists"""
        
        completed_work = context.get("completed_work", [])
        
        for work_item in completed_work:
            # Parse phase from work item
            phase_match = re.search(r"Phase (\d+)", work_item)
            if not phase_match:
                continue
            
            phase = int(phase_match.group(1))
            
            # Verify phase deliverables exist
            if self._phase_deliverables_exist(phase):
                self.alignments.append({
                    "check": "completed_work",
                    "value": work_item,
                    "status": "verified"
                })
            else:
                self.discrepancies.append({
                    "check": "completed_work",
                    "context": work_item,
                    "reality": f"Phase {phase} deliverables missing",
                    "severity": "high",
                    "issue": f"Context claims '{work_item}' but deliverables don't exist"
                })
    
    def _phase_deliverables_exist(self, phase: int) -> bool:
        """Check if phase deliverables exist"""
        
        if phase == 1:
            audit = self.project_root / "reports" / f"{self.service_name}_audit.json"
            return audit.exists()
        
        elif phase == 2:
            design_dir = self.service_path / "design"
            if not design_dir.exists():
                return False
            openapi = design_dir / "openapi_v2.yaml"
            return openapi.exists()
        
        elif phase == 3:
            domain = self.service_path / "domain"
            application = self.service_path / "application"
            tests = self.service_path / "tests"
            return domain.exists() and application.exists() and tests.exists()
        
        elif phase == 4:
            workflows = self.service_path / "tests" / "workflows"
            return workflows.exists()
        
        elif phase == 5:
            readme = self.service_path / "README.md"
            return readme.exists() and readme.stat().st_size > 3000
        
        return True
    
    def _check_test_state(self, context: dict):
        """Check if tests actually pass"""
        
        # Look for test claims in context
        context_str = json.dumps(context)
        
        if "tests passing" in context_str.lower() or "all tests pass" in context_str.lower():
            # Context claims tests pass - verify
            if not self.service_path.exists():
                self.discrepancies.append({
                    "check": "tests",
                    "context": "Tests passing",
                    "reality": "Service doesn't exist",
                    "severity": "critical"
                })
                return
            
            try:
                result = subprocess.run(
                    ["pytest", "--quiet", "--tb=no"],
                    cwd=self.service_path,
                    capture_output=True,
                    timeout=120
                )
                
                if result.returncode == 0:
                    self.alignments.append({
                        "check": "tests",
                        "value": "Tests passing",
                        "status": "verified"
                    })
                else:
                    self.discrepancies.append({
                        "check": "tests",
                        "context": "Tests passing",
                        "reality": f"Tests failing (exit code {result.returncode})",
                        "severity": "high",
                        "issue": "Context claims tests pass but they're actually failing"
                    })
            
            except Exception as e:
                self.discrepancies.append({
                    "check": "tests",
                    "context": "Tests passing",
                    "reality": f"Could not run tests: {e}",
                    "severity": "medium"
                })
    
    def _check_file_existence(self, context: dict):
        """Check files mentioned in context exist"""
        
        context_str = json.dumps(context)
        
        # Extract file paths from context
        file_patterns = [
            r'services/[\w-]+/[\w/]+\.py',
            r'tests/[\w/]+\.py',
            r'docs/[\w/]+\.md'
        ]
        
        mentioned_files = set()
        for pattern in file_patterns:
            matches = re.findall(pattern, context_str)
            mentioned_files.update(matches)
        
        for filepath in mentioned_files:
            full_path = self.project_root / filepath
            if full_path.exists():
                self.alignments.append({
                    "check": "file_existence",
                    "value": filepath,
                    "status": "exists"
                })
            else:
                self.discrepancies.append({
                    "check": "file_existence",
                    "context": f"File mentioned: {filepath}",
                    "reality": "File doesn't exist",
                    "severity": "medium",
                    "issue": f"Context mentions {filepath} but it doesn't exist"
                })
    
    def _check_git_state(self, context: dict):
        """Check git state matches context"""
        
        try:
            # Get actual git state
            result = subprocess.run(
                ["git", "log", "-1", "--oneline", "--", f"services/{self.service_name}"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            last_commit = result.stdout.strip() if result.returncode == 0 else ""
            
            # Check for uncommitted changes
            result = subprocess.run(
                ["git", "diff", "--quiet", "--", f"services/{self.service_name}"],
                cwd=self.project_root
            )
            has_uncommitted = result.returncode != 0
            
            if has_uncommitted:
                self.alignments.append({
                    "check": "git",
                    "value": "Uncommitted changes (work in progress)",
                    "status": "normal"
                })
            elif last_commit:
                self.alignments.append({
                    "check": "git",
                    "value": f"Last commit: {last_commit}",
                    "status": "clean"
                })
        
        except Exception:
            pass
    
    def _assess_drift(self, drift_score: float) -> str:
        """Assess drift severity"""
        if drift_score == 0:
            return "✅ NO_DRIFT (perfect alignment)"
        elif drift_score < 10:
            return "🟢 MINIMAL_DRIFT (acceptable)"
        elif drift_score < 25:
            return "🟡 MODERATE_DRIFT (caution advised)"
        elif drift_score < 50:
            return "🟠 SIGNIFICANT_DRIFT (action needed)"
        else:
            return "🔴 CRITICAL_DRIFT (stop and reconcile immediately)"


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Validate execution context matches reality"
    )
    parser.add_argument(
        "service",
        help="Service name (e.g., doc-store)"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory"
    )
    
    args = parser.parse_args()
    
    # Create validator
    validator = ContextRealityValidator(args.service, args.project_root)
    
    # Run validation
    try:
        results = validator.validate()
        
        # Display results
        print()
        print("=" * 70)
        print("📊 CONTEXT-REALITY VALIDATION RESULTS")
        print("=" * 70)
        print()
        
        drift_score = results["drift_score"]
        assessment = results["drift_assessment"]
        
        print(f"📈 Drift Score: {drift_score:.1f}%")
        print(f"📊 Assessment: {assessment}")
        print()
        
        # Discrepancies
        if results["discrepancies"]:
            print(f"🚨 DISCREPANCIES FOUND ({len(results['discrepancies'])}):")
            for i, disc in enumerate(results["discrepancies"], 1):
                severity_icon = "🔴" if disc["severity"] == "critical" else \
                               "🟠" if disc["severity"] == "high" else "🟡"
                
                print(f"{i}. {severity_icon} [{disc['severity'].upper()}] {disc['check']}")
                print(f"   Context: {disc.get('context', 'N/A')}")
                print(f"   Reality: {disc.get('reality', 'N/A')}")
                if "issue" in disc:
                    print(f"   Issue: {disc['issue']}")
                print()
        else:
            print("✅ No discrepancies found!")
            print()
        
        # Alignments
        if results["alignments"]:
            print(f"✅ VERIFIED ALIGNMENTS ({len(results['alignments'])}):")
            for alignment in results["alignments"][:10]:
                print(f"  ✓ {alignment['check']}: {alignment.get('value', alignment.get('status'))}")
            if len(results["alignments"]) > 10:
                print(f"  ... and {len(results['alignments']) - 10} more")
            print()
        
        # Summary
        print("📈 SUMMARY:")
        print(f"  Checks: {results['checks_performed']}")
        print(f"  Failed: {results['checks_failed']}")
        print(f"  Passed: {len(results['alignments'])}")
        print(f"  Drift: {drift_score:.1f}%")
        print()
        
        # Recommendations
        if drift_score >= 50:
            print("🔴 CRITICAL ACTION REQUIRED:")
            print("  1. STOP current work immediately")
            print("  2. Run: python3 scripts/refactoring/reconcile_context.py")
            print("  3. Validate reconciliation worked")
            print("  4. Then resume work")
        elif drift_score >= 25:
            print("🟠 ACTION RECOMMENDED:")
            print("  1. Review discrepancies carefully")
            print("  2. Update context to match reality")
            print("  3. Consider creating checkpoint")
        elif drift_score >= 10:
            print("🟡 CAUTION:")
            print("  Minor drift detected - monitor closely")
        else:
            print("✅ Context is aligned with reality - safe to proceed")
        print()
        
        # Output JSON
        print(json.dumps(results, indent=2))
        
        sys.exit(0 if drift_score < 50 else 1)
    
    except Exception as e:
        print(f"❌ Error during validation: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

