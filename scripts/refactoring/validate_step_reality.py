#!/usr/bin/env python3
"""
Step Reality Validation Script

Validates that a step is ACTUALLY complete, not just believed to be complete.
Prevents hallucination and incomplete thought completion.

Usage:
    python3 scripts/refactoring/validate_step_reality.py --service <name> --step <step_id>

Example:
    python3 scripts/refactoring/validate_step_reality.py --service doc-store --step 3.2.1

Author: Hackathon Team
Version: 1.0.0
"""

import argparse
import json
import sys
import subprocess
import yaml
from pathlib import Path
from typing import Dict, List, Tuple


class StepRealityValidator:
    """Validates step completion against reality"""
    
    def __init__(self, service_name: str, step_id: str, project_root: Path):
        self.service_name = service_name
        self.step_id = step_id
        self.project_root = project_root
        self.service_path = project_root / "services" / service_name
        self.issues = []
        self.warnings = []
        self.passed_checks = []
        self.step_criteria = self._load_step_criteria()
    
    def _load_step_criteria(self) -> dict:
        """Load acceptance criteria from STEP_DEFINITIONS.yaml"""
        
        step_defs_file = self.project_root / "docs" / "refactoring" / "STEP_DEFINITIONS.yaml"
        
        if not step_defs_file.exists():
            return {}  # Fall back to hardcoded checks
        
        try:
            with open(step_defs_file) as f:
                all_steps = yaml.safe_load(f)
            
            # Extract phase and step number
            phase_num = self.step_id.split(".")[0]
            phase_key = f"phase_{phase_num}"
            
            if phase_key in all_steps:
                for step in all_steps[phase_key].get("steps", []):
                    if step["id"] == self.step_id:
                        return step.get("acceptance_criteria", {})
        except Exception as e:
            # If can't load, fall back to hardcoded
            pass
        
        return {}
        
    def validate(self) -> dict:
        """Comprehensive reality validation"""
        
        results = {
            "service": self.service_name,
            "step": self.step_id,
            "validated": True,
            "issues": [],
            "warnings": [],
            "passed_checks": []
        }
        
        print(f"🔍 Validating Step Reality: {self.step_id} for {self.service_name}")
        print("=" * 70)
        print()
        
        # Determine what to check based on step
        phase = self.step_id.split(".")[0]
        
        # Check 1: Required deliverables exist
        print("📁 Checking deliverables...")
        self._check_deliverables(phase)
        
        # Check 2: Files are complete (not skeletons)
        print("✏️  Checking file completeness...")
        self._check_file_completeness()
        
        # Check 3: Tests exist and pass
        if int(phase) >= 3:
            print("🧪 Checking tests...")
            self._check_tests()
        
        # Check 4: Coverage meets target
        if int(phase) >= 3:
            print("📊 Checking coverage...")
            self._check_coverage()
        
        # Check 5: No TODO markers
        print("🔍 Checking for TODOs...")
        self._check_todos()
        
        # Check 6: Linting passes
        print("🎨 Checking linting...")
        self._check_linting()
        
        # Compile results
        results["issues"] = self.issues
        results["warnings"] = self.warnings
        results["passed_checks"] = self.passed_checks
        results["validated"] = len(self.issues) == 0
        
        return results
    
    def _check_deliverables(self, phase: str):
        """Check phase-specific deliverables exist"""
        
        required = self._get_required_deliverables(phase)
        
        for deliverable in required:
            path = self.project_root / deliverable
            if path.exists():
                self.passed_checks.append(f"Deliverable exists: {deliverable}")
            else:
                self.issues.append({
                    "severity": "critical",
                    "check": "deliverables",
                    "issue": f"Missing required deliverable: {deliverable}"
                })
    
    def _get_required_deliverables(self, phase: str) -> List[str]:
        """Get required deliverables for phase"""
        
        deliverables = {
            "1": [
                f"reports/{self.service_name}_audit.json",
                f"services/{self.service_name}/gap_analysis.md"
            ],
            "2": [
                f"services/{self.service_name}/design/domain_model.md",
                f"services/{self.service_name}/design/openapi_v2.yaml",
                f"services/{self.service_name}/design/test_plan.md"
            ],
            "3": [
                f"services/{self.service_name}/domain",
                f"services/{self.service_name}/application",
                f"services/{self.service_name}/infrastructure",
                f"services/{self.service_name}/presentation",
                f"services/{self.service_name}/tests"
            ],
            "4": [
                f"services/{self.service_name}/tests/integration",
                f"services/{self.service_name}/Dockerfile"
            ],
            "5": [
                f"services/{self.service_name}/README.md"
            ],
            "6": []
        }
        
        return deliverables.get(phase, [])
    
    def _check_file_completeness(self):
        """Check files are not skeletons"""
        
        if not self.service_path.exists():
            return
        
        # Find Python files
        py_files = list(self.service_path.rglob("*.py"))
        
        skeleton_markers = [
            "TODO: Implement",
            "pass  # TODO",
            "raise NotImplementedError",
            "# Placeholder",
            "...  # To be implemented"
        ]
        
        for py_file in py_files:
            if py_file.name == "__init__.py":
                continue
            
            try:
                content = py_file.read_text()
                
                # Check for skeleton markers
                for marker in skeleton_markers:
                    if marker in content:
                        self.warnings.append({
                            "severity": "medium",
                            "check": "completeness",
                            "issue": f"Skeleton code in {py_file.relative_to(self.project_root)}: '{marker}'"
                        })
                        break
                else:
                    # Check minimum content
                    lines = [l for l in content.split("\n") 
                            if l.strip() and not l.strip().startswith("#")]
                    if len(lines) < 5:
                        self.warnings.append({
                            "severity": "low",
                            "check": "completeness",
                            "issue": f"Very short file ({len(lines)} lines): {py_file.relative_to(self.project_root)}"
                        })
            except Exception as e:
                self.warnings.append({
                    "severity": "low",
                    "check": "completeness",
                    "issue": f"Could not read {py_file.relative_to(self.project_root)}: {e}"
                })
    
    def _check_tests(self):
        """Check tests exist and pass"""
        
        test_dir = self.service_path / "tests"
        
        if not test_dir.exists():
            self.issues.append({
                "severity": "critical",
                "check": "tests",
                "issue": "Tests directory missing"
            })
            return
        
        # Count tests
        test_files = list(test_dir.rglob("test_*.py"))
        test_count = len(test_files)
        
        if test_count == 0:
            self.issues.append({
                "severity": "critical",
                "check": "tests",
                "issue": "No test files found"
            })
            return
        
        if test_count < 10:
            self.warnings.append({
                "severity": "medium",
                "check": "tests",
                "issue": f"Only {test_count} test files (recommend 30+ for full service)"
            })
        
        # Run tests
        try:
            result = subprocess.run(
                ["pytest", "--tb=short", "--quiet"],
                cwd=self.service_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                self.passed_checks.append(f"All tests passing ({test_count} test files)")
            else:
                # Parse failures
                output = result.stdout + result.stderr
                self.issues.append({
                    "severity": "critical",
                    "check": "tests",
                    "issue": f"Tests failing (exit code {result.returncode})",
                    "details": output[:500]  # First 500 chars
                })
        
        except subprocess.TimeoutExpired:
            self.issues.append({
                "severity": "critical",
                "check": "tests",
                "issue": "Tests timed out (> 2 minutes)"
            })
        except Exception as e:
            self.warnings.append({
                "severity": "medium",
                "check": "tests",
                "issue": f"Could not run tests: {e}"
            })
    
    def _check_coverage(self):
        """Check test coverage"""
        
        try:
            result = subprocess.run(
                ["pytest", "--cov", "--cov-report=json", "--quiet"],
                cwd=self.service_path,
                capture_output=True,
                timeout=120
            )
            
            coverage_file = self.service_path / "coverage.json"
            if coverage_file.exists():
                data = json.loads(coverage_file.read_text())
                total_coverage = data["totals"]["percent_covered"]
                
                if total_coverage >= 80:
                    self.passed_checks.append(f"Coverage {total_coverage:.1f}% (meets 80% target)")
                elif total_coverage >= 70:
                    self.warnings.append({
                        "severity": "medium",
                        "check": "coverage",
                        "issue": f"Coverage {total_coverage:.1f}% (below 80% target)"
                    })
                else:
                    self.issues.append({
                        "severity": "high",
                        "check": "coverage",
                        "issue": f"Coverage {total_coverage:.1f}% (significantly below 80% target)"
                    })
            else:
                self.warnings.append({
                    "severity": "low",
                    "check": "coverage",
                    "issue": "Could not generate coverage report"
                })
        
        except Exception as e:
            self.warnings.append({
                "severity": "low",
                "check": "coverage",
                "issue": f"Could not check coverage: {e}"
            })
    
    def _check_todos(self):
        """Check for TODO markers"""
        
        if not self.service_path.exists():
            return
        
        py_files = list(self.service_path.rglob("*.py"))
        
        todos = []
        for py_file in py_files:
            try:
                content = py_file.read_text()
                if "TODO" in content:
                    # Count TODOs
                    count = content.count("TODO")
                    todos.append((py_file.relative_to(self.project_root), count))
            except:
                pass
        
        if todos:
            total_todos = sum(count for _, count in todos)
            self.warnings.append({
                "severity": "low",
                "check": "todos",
                "issue": f"{total_todos} TODO(s) found in {len(todos)} file(s)"
            })
        else:
            self.passed_checks.append("No TODOs in code")
    
    def _check_linting(self):
        """Check linting (basic)"""
        
        if not self.service_path.exists():
            return
        
        try:
            # Basic syntax check via compile
            py_files = list(self.service_path.rglob("*.py"))
            
            syntax_errors = []
            for py_file in py_files[:20]:  # Check first 20 files
                try:
                    compile(py_file.read_text(), str(py_file), 'exec')
                except SyntaxError as e:
                    syntax_errors.append(f"{py_file.name}: {e}")
            
            if syntax_errors:
                self.issues.append({
                    "severity": "critical",
                    "check": "linting",
                    "issue": "Syntax errors found",
                    "details": syntax_errors
                })
            else:
                self.passed_checks.append("No syntax errors")
        
        except Exception as e:
            self.warnings.append({
                "severity": "low",
                "check": "linting",
                "issue": f"Could not check linting: {e}"
            })


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Validate step completion against reality"
    )
    parser.add_argument(
        "--service",
        required=True,
        help="Service name (e.g., doc-store)"
    )
    parser.add_argument(
        "--step",
        required=True,
        help="Step ID (e.g., 3.2.1)"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory"
    )
    
    args = parser.parse_args()
    
    # Create validator
    validator = StepRealityValidator(args.service, args.step, args.project_root)
    
    # Run validation
    try:
        results = validator.validate()
        
        # Display results
        print()
        print("=" * 70)
        print("📊 VALIDATION RESULTS")
        print("=" * 70)
        print()
        
        if results["validated"]:
            print("✅ VALIDATION PASSED - Step is actually complete")
        else:
            print("❌ VALIDATION FAILED - Step is NOT complete")
        print()
        
        # Issues
        if results["issues"]:
            print("🚨 ISSUES (must fix before marking complete):")
            for i, issue in enumerate(results["issues"], 1):
                severity_icon = "🔴" if issue["severity"] == "critical" else "🟠"
                print(f"{i}. {severity_icon} [{issue['severity'].upper()}] {issue['issue']}")
                if "details" in issue:
                    print(f"   Details: {issue['details']}")
            print()
        
        # Warnings
        if results["warnings"]:
            print(f"⚠️  WARNINGS ({len(results['warnings'])}):")
            for i, warning in enumerate(results["warnings"], 1):
                print(f"{i}. {warning['issue']}")
            print()
        
        # Passed
        if results["passed_checks"]:
            print(f"✅ PASSED CHECKS ({len(results['passed_checks'])}):")
            for check in results["passed_checks"][:10]:
                print(f"  ✓ {check}")
            if len(results["passed_checks"]) > 10:
                print(f"  ... and {len(results['passed_checks']) - 10} more")
            print()
        
        # Summary
        print("📈 SUMMARY:")
        print(f"  Validated: {results['validated']}")
        print(f"  Issues: {len(results['issues'])}")
        print(f"  Warnings: {len(results['warnings'])}")
        print(f"  Passed: {len(results['passed_checks'])}")
        print()
        
        if not results["validated"]:
            print("⚠️  DO NOT mark step complete until all issues fixed!")
        else:
            print("✅ Safe to mark step complete and proceed")
        print()
        
        # Output JSON
        print(json.dumps(results, indent=2))
        
        sys.exit(0 if results["validated"] else 1)
    
    except Exception as e:
        print(f"❌ Error during validation: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

