#!/usr/bin/env python3
"""
AI Agent Self-Review Script

Comprehensive validation of AI agent's refactoring work to catch missed steps,
incomplete deliverables, and quality issues.

Usage:
    python3 scripts/refactoring/self_review.py <service-name> [--phase N]

Examples:
    # Review current phase
    python3 scripts/refactoring/self_review.py doc-store
    
    # Review specific phase
    python3 scripts/refactoring/self_review.py doc-store --phase 3
    
    # Review all phases
    python3 scripts/refactoring/self_review.py doc-store --phase all

Author: Hackathon Team
Version: 1.0.0
"""

import argparse
import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class SelfReviewer:
    """AI Agent self-review system"""
    
    def __init__(self, service_name: str, project_root: Path):
        self.service_name = service_name
        self.project_root = project_root
        self.service_path = project_root / "services" / service_name
        self.issues = []
        self.recommendations = []
        self.passed_checks = []
        
    def review(self, phase: str = None) -> dict:
        """Perform comprehensive self-review"""
        
        results = {
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "phase_reviewed": phase or "current",
            "issues": [],
            "recommendations": [],
            "passed_checks": [],
            "summary": {}
        }
        
        # Determine which phase to review
        if phase == "all":
            phases = [1, 2, 3, 4, 5, 6]
        elif phase:
            phases = [int(phase)]
        else:
            # Detect current phase from context
            phases = [self._detect_current_phase()]
        
        print(f"🔍 Reviewing Phase(s): {phases}")
        print()
        
        # Run phase-specific reviews
        for p in phases:
            print(f"📋 Phase {p} Review...")
            if p == 1:
                self._review_phase1()
            elif p == 2:
                self._review_phase2()
            elif p == 3:
                self._review_phase3()
            elif p == 4:
                self._review_phase4()
            elif p == 5:
                self._review_phase5()
            elif p == 6:
                self._review_phase6()
        
        # Holistic checks
        print("🎯 Holistic Validation...")
        self._review_holistic()
        
        # Compile results
        results["issues"] = self.issues
        results["recommendations"] = self.recommendations
        results["passed_checks"] = self.passed_checks
        results["summary"] = self._generate_summary()
        
        return results
    
    def _detect_current_phase(self) -> int:
        """Detect current phase from service state"""
        
        # Check what exists to infer phase
        if not self.service_path.exists():
            return 1  # Hasn't started yet
        
        # Check for Phase 6 markers (complete)
        progress_tracker = self.project_root / "docs" / "refactoring" / "LIVING_PROGRESS_TRACKER.md"
        if progress_tracker.exists():
            content = progress_tracker.read_text()
            if f"{self.service_name}.*Completed" in content or \
               f"{self.service_name}.*100%" in content:
                return 6
        
        # Check for Phase 5 markers (documentation)
        readme = self.service_path / "README.md"
        if readme.exists() and readme.stat().st_size > 5000:
            return 5
        
        # Check for Phase 4 markers (integration tests)
        workflow_tests = self.service_path / "tests" / "workflows"
        if workflow_tests.exists():
            return 4
        
        # Check for Phase 3 markers (implementation)
        test_dir = self.service_path / "tests"
        if test_dir.exists() and len(list(test_dir.glob("**/*.py"))) > 5:
            return 3
        
        # Check for Phase 2 markers (design)
        design_dir = self.service_path / "design"
        if design_dir.exists():
            return 2
        
        return 1  # Phase 1 by default
    
    def _review_phase1(self):
        """Review Phase 1: Audit & Analysis"""
        
        print("  Checking Phase 1 deliverables...")
        
        # Check audit report
        audit_report = self.project_root / "reports" / f"{self.service_name}_audit.json"
        if not audit_report.exists():
            self.issues.append({
                "phase": 1,
                "severity": "critical",
                "issue": "Audit report missing",
                "expected": str(audit_report),
                "fix": f"Run: python3 scripts/refactoring/audit_service.py {self.service_name}"
            })
        else:
            # Validate audit report content
            try:
                audit_data = json.loads(audit_report.read_text())
                if "metrics" not in audit_data:
                    self.issues.append({
                        "phase": 1,
                        "severity": "high",
                        "issue": "Audit report incomplete (missing metrics)",
                        "fix": "Re-run audit script"
                    })
                else:
                    self.passed_checks.append("Phase 1: Audit report exists and valid")
            except json.JSONDecodeError:
                self.issues.append({
                    "phase": 1,
                    "severity": "high",
                    "issue": "Audit report is invalid JSON",
                    "fix": "Re-run audit script"
                })
        
        # Check gap analysis
        gap_analysis = self.service_path / "gap_analysis.md"
        if not gap_analysis.exists():
            self.issues.append({
                "phase": 1,
                "severity": "medium",
                "issue": "Gap analysis missing",
                "expected": str(gap_analysis),
                "fix": "Create gap analysis document"
            })
        else:
            self.passed_checks.append("Phase 1: Gap analysis exists")
    
    def _review_phase2(self):
        """Review Phase 2: Design & Planning"""
        
        print("  Checking Phase 2 deliverables...")
        
        design_dir = self.service_path / "design"
        
        # Check domain model
        domain_model = design_dir / "domain_model.md"
        if not domain_model.exists():
            self.issues.append({
                "phase": 2,
                "severity": "critical",
                "issue": "Domain model missing",
                "expected": str(domain_model),
                "fix": "Create domain model document"
            })
        else:
            self.passed_checks.append("Phase 2: Domain model exists")
        
        # Check OpenAPI spec
        openapi_spec = design_dir / "openapi_v2.yaml"
        if not openapi_spec.exists():
            self.issues.append({
                "phase": 2,
                "severity": "critical",
                "issue": "OpenAPI specification missing",
                "expected": str(openapi_spec),
                "fix": "Create OpenAPI v2 specification"
            })
        else:
            self.passed_checks.append("Phase 2: OpenAPI spec exists")
        
        # Check test plan
        test_plan = design_dir / "test_plan.md"
        if not test_plan.exists():
            self.issues.append({
                "phase": 2,
                "severity": "high",
                "issue": "Test plan missing",
                "expected": str(test_plan),
                "fix": "Create test plan document"
            })
        else:
            self.passed_checks.append("Phase 2: Test plan exists")
    
    def _review_phase3(self):
        """Review Phase 3: TDD Implementation"""
        
        print("  Checking Phase 3 deliverables...")
        
        # Check DDD layers
        layers = ["domain", "application", "infrastructure", "presentation"]
        for layer in layers:
            layer_path = self.service_path / layer
            if not layer_path.exists():
                self.issues.append({
                    "phase": 3,
                    "severity": "critical",
                    "issue": f"{layer.capitalize()} layer missing",
                    "expected": str(layer_path),
                    "fix": f"Implement {layer} layer following DDD"
                })
            else:
                self.passed_checks.append(f"Phase 3: {layer.capitalize()} layer exists")
        
        # Check tests exist
        test_dir = self.service_path / "tests"
        if not test_dir.exists():
            self.issues.append({
                "phase": 3,
                "severity": "critical",
                "issue": "Tests directory missing",
                "expected": str(test_dir),
                "fix": f"Run: python3 scripts/refactoring/setup_testing_infrastructure.py {self.service_name}"
            })
        else:
            # Count tests
            test_files = list(test_dir.glob("**/test_*.py"))
            test_count = len(test_files)
            
            if test_count < 10:
                self.issues.append({
                    "phase": 3,
                    "severity": "high",
                    "issue": f"Insufficient tests ({test_count} tests, expect 30+)",
                    "fix": "Add more unit and integration tests"
                })
            else:
                self.passed_checks.append(f"Phase 3: {test_count} tests exist")
        
        # Check test coverage
        try:
            result = subprocess.run(
                ["pytest", "--cov", "--cov-report=json", "--quiet"],
                cwd=self.service_path,
                capture_output=True,
                timeout=60
            )
            
            if result.returncode == 0:
                coverage_file = self.service_path / "coverage.json"
                if coverage_file.exists():
                    coverage_data = json.loads(coverage_file.read_text())
                    total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
                    
                    if total_coverage < 80:
                        self.issues.append({
                            "phase": 3,
                            "severity": "high",
                            "issue": f"Coverage below target ({total_coverage:.1f}%, need 80%+)",
                            "fix": "Add tests to increase coverage"
                        })
                    else:
                        self.passed_checks.append(f"Phase 3: Coverage {total_coverage:.1f}% (meets 80% target)")
        except Exception as e:
            self.recommendations.append({
                "phase": 3,
                "recommendation": "Run pytest --cov to check test coverage",
                "reason": f"Could not auto-check coverage: {str(e)}"
            })
        
        # Check logging
        try:
            result = subprocess.run(
                ["python3", "scripts/refactoring/validate_logging.py", self.service_name],
                cwd=self.project_root,
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.issues.append({
                    "phase": 3,
                    "severity": "medium",
                    "issue": "Logging validation failed",
                    "fix": "Implement standardized logging per STANDARDIZED_LOGGING_STRATEGY.md"
                })
            else:
                self.passed_checks.append("Phase 3: Logging implemented correctly")
        except Exception:
            self.recommendations.append({
                "phase": 3,
                "recommendation": "Manually validate logging implementation"
            })
    
    def _review_phase4(self):
        """Review Phase 4: Integration Testing"""
        
        print("  Checking Phase 4 deliverables...")
        
        # Check integration tests
        integration_dir = self.service_path / "tests" / "integration"
        if not integration_dir.exists():
            self.issues.append({
                "phase": 4,
                "severity": "high",
                "issue": "Integration tests missing",
                "expected": str(integration_dir),
                "fix": "Create integration tests"
            })
        else:
            integration_tests = list(integration_dir.glob("**/test_*.py"))
            if len(integration_tests) < 5:
                self.issues.append({
                    "phase": 4,
                    "severity": "medium",
                    "issue": f"Insufficient integration tests ({len(integration_tests)})",
                    "fix": "Add more integration tests"
                })
            else:
                self.passed_checks.append(f"Phase 4: {len(integration_tests)} integration tests exist")
        
        # Check workflow tests
        workflow_dir = self.service_path / "tests" / "workflows"
        if not workflow_dir.exists():
            self.recommendations.append({
                "phase": 4,
                "recommendation": "Add workflow tests to validate end-to-end scenarios",
                "fix": f"Run: python3 scripts/refactoring/generate_workflow_tests.py {self.service_name}"
            })
        else:
            self.passed_checks.append("Phase 4: Workflow tests exist")
        
        # Check Docker build
        dockerfile = self.service_path / "Dockerfile"
        if not dockerfile.exists():
            self.issues.append({
                "phase": 4,
                "severity": "medium",
                "issue": "Dockerfile missing",
                "fix": "Create Dockerfile for service"
            })
        else:
            self.passed_checks.append("Phase 4: Dockerfile exists")
    
    def _review_phase5(self):
        """Review Phase 5: Documentation"""
        
        print("  Checking Phase 5 deliverables...")
        
        # Check README
        readme = self.service_path / "README.md"
        if not readme.exists():
            self.issues.append({
                "phase": 5,
                "severity": "critical",
                "issue": "README missing",
                "expected": str(readme),
                "fix": f"Run: python3 scripts/refactoring/generate_service_readme.py {self.service_name}"
            })
        else:
            readme_size = readme.stat().st_size
            if readme_size < 3000:
                self.issues.append({
                    "phase": 5,
                    "severity": "high",
                    "issue": f"README too short ({readme_size} bytes, expect 5KB+)",
                    "fix": "Expand README with comprehensive documentation"
                })
            else:
                self.passed_checks.append(f"Phase 5: README exists ({readme_size} bytes)")
        
        # Check for diagrams
        readme_content = readme.read_text() if readme.exists() else ""
        diagram_count = readme_content.count("```mermaid") + readme_content.count("![")
        if diagram_count < 2:
            self.issues.append({
                "phase": 5,
                "severity": "medium",
                "issue": f"Insufficient diagrams ({diagram_count}, need 2+)",
                "fix": "Add architecture and data flow diagrams"
            })
        else:
            self.passed_checks.append(f"Phase 5: {diagram_count} diagrams in README")
        
        # Check standard endpoints (if presentation layer exists)
        presentation_path = self.service_path / "presentation"
        if presentation_path.exists():
            standard_endpoints = ["/health", "/about-me", "/endpoints", "/provider-consumer"]
            # This is a heuristic check - would need actual API testing for accuracy
            self.recommendations.append({
                "phase": 5,
                "recommendation": "Manually verify standard endpoints are implemented",
                "endpoints": standard_endpoints
            })
        
        # Check documentation validation
        try:
            result = subprocess.run(
                ["python3", "scripts/refactoring/validate_service_documentation.py", self.service_name],
                cwd=self.project_root,
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.issues.append({
                    "phase": 5,
                    "severity": "high",
                    "issue": "Documentation validation failed",
                    "fix": "Address documentation validation issues"
                })
            else:
                self.passed_checks.append("Phase 5: Documentation validation passed")
        except Exception:
            self.recommendations.append({
                "phase": 5,
                "recommendation": "Manually validate documentation completeness"
            })
        
        # Check AI enrichment
        ai_index = self.service_path / ".ai-index.json"
        if not ai_index.exists():
            self.recommendations.append({
                "phase": 5,
                "recommendation": "Enrich documentation with AI metadata",
                "fix": f"Run: python3 scripts/refactoring/enrich_service_documentation.py {self.service_name}"
            })
        else:
            self.passed_checks.append("Phase 5: Documentation AI-enriched")
    
    def _review_phase6(self):
        """Review Phase 6: Deployment & Monitoring"""
        
        print("  Checking Phase 6 deliverables...")
        
        # Check quality gates
        try:
            result = subprocess.run(
                ["python3", "scripts/refactoring/check_quality_gates.py", self.service_name],
                cwd=self.project_root,
                capture_output=True,
                timeout=60
            )
            
            if result.returncode != 0:
                self.issues.append({
                    "phase": 6,
                    "severity": "critical",
                    "issue": "Quality gates not passing",
                    "fix": "Address quality gate failures before marking complete"
                })
            else:
                self.passed_checks.append("Phase 6: All quality gates passed")
        except Exception as e:
            self.issues.append({
                "phase": 6,
                "severity": "high",
                "issue": "Could not validate quality gates",
                "reason": str(e),
                "fix": f"Run: python3 scripts/refactoring/check_quality_gates.py {self.service_name}"
            })
        
        # Check progress tracker updated
        progress_tracker = self.project_root / "docs" / "refactoring" / "LIVING_PROGRESS_TRACKER.md"
        if progress_tracker.exists():
            content = progress_tracker.read_text()
            if self.service_name in content:
                self.passed_checks.append("Phase 6: Progress tracker updated")
            else:
                self.issues.append({
                    "phase": 6,
                    "severity": "medium",
                    "issue": "Service not in progress tracker",
                    "fix": "Update LIVING_PROGRESS_TRACKER.md with service status"
                })
    
    def _review_holistic(self):
        """Holistic validation across all phases"""
        
        print("  Checking holistic requirements...")
        
        # Check for circular dependencies
        self.recommendations.append({
            "holistic": True,
            "recommendation": "Manually verify no circular dependencies between DDD layers"
        })
        
        # Check naming consistency
        self.recommendations.append({
            "holistic": True,
            "recommendation": "Verify naming follows NAMING_CONVENTIONS_STANDARDS.md"
        })
        
        # Check git commits
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "--", f"services/{self.service_name}"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            commit_count = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
            
            if commit_count == 0:
                self.issues.append({
                    "holistic": True,
                    "severity": "high",
                    "issue": "No git commits for this service",
                    "fix": "Commit work following GIT_COMMIT_STRATEGY.md"
                })
            elif commit_count > 20:
                self.recommendations.append({
                    "holistic": True,
                    "recommendation": f"Many commits ({commit_count}) - consider if commits are too granular"
                })
            else:
                self.passed_checks.append(f"Holistic: {commit_count} commits (reasonable)")
        except Exception:
            pass
    
    def _generate_summary(self) -> dict:
        """Generate review summary"""
        
        critical_issues = len([i for i in self.issues if i.get("severity") == "critical"])
        high_issues = len([i for i in self.issues if i.get("severity") == "high"])
        medium_issues = len([i for i in self.issues if i.get("severity") == "medium"])
        
        total_issues = len(self.issues)
        total_passed = len(self.passed_checks)
        
        # Determine overall status
        if critical_issues > 0:
            status = "CRITICAL_ISSUES"
            ready = False
        elif high_issues > 0:
            status = "HIGH_ISSUES"
            ready = False
        elif medium_issues > 0:
            status = "MEDIUM_ISSUES"
            ready = True  # Can proceed with caution
        else:
            status = "PASSED"
            ready = True
        
        return {
            "status": status,
            "ready_to_proceed": ready,
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "high_issues": high_issues,
            "medium_issues": medium_issues,
            "passed_checks": total_passed,
            "recommendations_count": len(self.recommendations)
        }


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="AI Agent self-review for comprehensive work validation"
    )
    parser.add_argument(
        "service",
        help="Service name (e.g., doc-store)"
    )
    parser.add_argument(
        "--phase",
        help="Phase to review (1-6, or 'all')",
        default=None
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)"
    )
    
    args = parser.parse_args()
    
    print(f"🔍 Self-Review: {args.service}")
    print(f"{'='*60}")
    print()
    
    # Create reviewer
    reviewer = SelfReviewer(args.service, args.project_root)
    
    # Perform review
    try:
        results = reviewer.review(args.phase)
        
        # Display results
        print()
        print(f"{'='*60}")
        print("📊 REVIEW RESULTS")
        print(f"{'='*60}")
        print()
        
        summary = results["summary"]
        
        # Status
        status_emoji = "❌" if summary["critical_issues"] > 0 else \
                      "⚠️" if summary["high_issues"] > 0 else \
                      "⚡" if summary["medium_issues"] > 0 else "✅"
        
        print(f"{status_emoji} Status: {summary['status']}")
        print(f"{'✅' if summary['ready_to_proceed'] else '❌'} Ready to Proceed: {summary['ready_to_proceed']}")
        print()
        
        # Issues
        if results["issues"]:
            print("🚨 ISSUES FOUND:")
            for i, issue in enumerate(results["issues"], 1):
                phase = issue.get("phase", "N/A")
                severity = issue.get("severity", "unknown")
                severity_icon = "🔴" if severity == "critical" else \
                               "🟠" if severity == "high" else "🟡"
                
                print(f"{i}. {severity_icon} Phase {phase} ({severity.upper()})")
                print(f"   Issue: {issue['issue']}")
                if "fix" in issue:
                    print(f"   Fix: {issue['fix']}")
                print()
        else:
            print("✅ No issues found!")
            print()
        
        # Passed checks
        if results["passed_checks"]:
            print(f"✅ PASSED CHECKS ({len(results['passed_checks'])}):")
            for check in results["passed_checks"][:10]:  # Show first 10
                print(f"  ✓ {check}")
            if len(results["passed_checks"]) > 10:
                print(f"  ... and {len(results['passed_checks']) - 10} more")
            print()
        
        # Recommendations
        if results["recommendations"]:
            print(f"💡 RECOMMENDATIONS ({len(results['recommendations'])}):")
            for i, rec in enumerate(results["recommendations"], 1):
                print(f"{i}. {rec['recommendation']}")
                if "fix" in rec:
                    print(f"   → {rec['fix']}")
            print()
        
        # Summary
        print("📈 SUMMARY:")
        print(f"  Issues: {summary['total_issues']} ({summary['critical_issues']} critical, {summary['high_issues']} high, {summary['medium_issues']} medium)")
        print(f"  Passed: {summary['passed_checks']} checks")
        print(f"  Recommendations: {summary['recommendations_count']}")
        print()
        
        # Next steps
        if summary["critical_issues"] > 0:
            print("⚠️  NEXT STEPS: Fix critical issues before proceeding!")
        elif summary["high_issues"] > 0:
            print("⚠️  NEXT STEPS: Fix high-priority issues before proceeding.")
        elif summary["medium_issues"] > 0:
            print("✅ NEXT STEPS: Can proceed, but address medium issues soon.")
        else:
            print("🎉 NEXT STEPS: All checks passed! Ready to proceed.")
        print()
        
        # Output JSON for automation
        print(json.dumps(results, indent=2))
        
        # Exit code based on status
        if summary["critical_issues"] > 0:
            sys.exit(2)  # Critical issues
        elif summary["high_issues"] > 0:
            sys.exit(1)  # High issues
        else:
            sys.exit(0)  # Success
    
    except Exception as e:
        print(f"❌ Error during self-review: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

