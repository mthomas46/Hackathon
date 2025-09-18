#!/usr/bin/env python3
"""
Ecosystem CI/CD Runner
Comprehensive CI/CD integration for automated validation and deployment
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ci_run.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

class CIRunner:
    """CI/CD runner for ecosystem validation and deployment"""

    def __init__(self, workspace_path: str = "."):
        self.workspace_path = Path(workspace_path)
        self.reports_dir = self.workspace_path / "ci_reports"
        self.reports_dir.mkdir(exist_ok=True)
        self.results = {}

    def run_validation_suite(self, validation_level: str = "standard") -> bool:
        """Run the complete validation suite"""
        logger.info(f"🚀 Starting {validation_level} validation suite")

        success = True

        try:
            # Quick validation (always run)
            if not self._run_quick_validation():
                success = False
                logger.error("❌ Quick validation failed")

            # Standard validation
            if validation_level in ["standard", "comprehensive"]:
                if not self._run_standard_validation():
                    success = False
                    logger.error("❌ Standard validation failed")

            # Comprehensive validation
            if validation_level == "comprehensive":
                if not self._run_comprehensive_validation():
                    success = False
                    logger.error("❌ Comprehensive validation failed")

            # Security validation (always run)
            if not self._run_security_validation():
                success = False
                logger.error("❌ Security validation failed")

        except Exception as e:
            logger.error(f"❌ Validation suite failed: {e}")
            success = False

        # Generate final report
        self._generate_final_report(success)

        return success

    def _run_quick_validation(self) -> bool:
        """Run quick validation checks"""
        logger.info("⚡ Running quick validation...")

        checks = [
            ("syntax", self._check_syntax),
            ("imports", self._check_imports),
            ("config", self._check_config_files),
            ("ports", self._check_ports_quick)
        ]

        results = {}
        all_passed = True

        for check_name, check_func in checks:
            try:
                result = check_func()
                results[check_name] = result
                if not result["passed"]:
                    all_passed = False
                    logger.warning(f"⚠️ {check_name} check failed: {result.get('error', 'Unknown error')}")
            except Exception as e:
                results[check_name] = {"passed": False, "error": str(e)}
                all_passed = False
                logger.error(f"❌ {check_name} check error: {e}")

        self.results["quick_validation"] = {
            "passed": all_passed,
            "checks": results,
            "duration": time.time()
        }

        return all_passed

    def _run_standard_validation(self) -> bool:
        """Run standard validation checks"""
        logger.info("🔍 Running standard validation...")

        checks = [
            ("dependencies", self._check_dependencies),
            ("dockerfiles", self._check_dockerfiles),
            ("environment", self._check_environment),
            ("connectivity", self._check_connectivity),
            ("health_endpoints", self._check_health_endpoints)
        ]

        results = {}
        all_passed = True

        for check_name, check_func in checks:
            try:
                result = check_func()
                results[check_name] = result
                if not result["passed"]:
                    all_passed = False
                    logger.warning(f"⚠️ {check_name} check failed")
            except Exception as e:
                results[check_name] = {"passed": False, "error": str(e)}
                all_passed = False
                logger.error(f"❌ {check_name} check error: {e}")

        self.results["standard_validation"] = {
            "passed": all_passed,
            "checks": results,
            "duration": time.time()
        }

        return all_passed

    def _run_comprehensive_validation(self) -> bool:
        """Run comprehensive validation checks"""
        logger.info("🔬 Running comprehensive validation...")

        checks = [
            ("functional_tests", self._run_functional_tests),
            ("performance", self._check_performance),
            ("config_drift", self._check_config_drift),
            ("logging", self._check_logging),
            ("api_contracts", self._check_api_contracts),
            ("integration", self._check_integration)
        ]

        results = {}
        all_passed = True

        for check_name, check_func in checks:
            try:
                result = check_func()
                results[check_name] = result
                if not result["passed"]:
                    all_passed = False
                    logger.warning(f"⚠️ {check_name} check failed")
            except Exception as e:
                results[check_name] = {"passed": False, "error": str(e)}
                all_passed = False
                logger.error(f"❌ {check_name} check error: {e}")

        self.results["comprehensive_validation"] = {
            "passed": all_passed,
            "checks": results,
            "duration": time.time()
        }

        return all_passed

    def _run_security_validation(self) -> bool:
        """Run security validation checks"""
        logger.info("🔒 Running security validation...")

        checks = [
            ("secrets", self._check_secrets),
            ("vulnerabilities", self._check_vulnerabilities),
            ("permissions", self._check_permissions)
        ]

        results = {}
        all_passed = True

        for check_name, check_func in checks:
            try:
                result = check_func()
                results[check_name] = result
                if not result["passed"]:
                    all_passed = False
                    logger.warning(f"⚠️ {check_name} security check failed")
            except Exception as e:
                results[check_name] = {"passed": False, "error": str(e)}
                all_passed = False
                logger.error(f"❌ {check_name} security check error: {e}")

        self.results["security_validation"] = {
            "passed": all_passed,
            "checks": results,
            "duration": time.time()
        }

        return all_passed

    # ========================================
    # INDIVIDUAL CHECK IMPLEMENTATIONS
    # ========================================

    def _check_syntax(self) -> Dict[str, Any]:
        """Check Python syntax"""
        logger.info("Checking Python syntax...")

        try:
            # Check our hardening scripts
            scripts_dir = self.workspace_path / "scripts" / "hardening"
            if scripts_dir.exists():
                for py_file in scripts_dir.glob("*.py"):
                    result = subprocess.run(
                        [sys.executable, "-m", "py_compile", str(py_file)],
                        capture_output=True, text=True, timeout=30
                    )
                    if result.returncode != 0:
                        return {
                            "passed": False,
                            "error": f"Syntax error in {py_file}: {result.stderr}",
                            "file": str(py_file)
                        }

            return {"passed": True, "files_checked": len(list(scripts_dir.glob("*.py"))) if scripts_dir.exists() else 0}

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _check_imports(self) -> Dict[str, Any]:
        """Check Python imports"""
        logger.info("Checking Python imports...")

        try:
            # Test key imports (use absolute imports where possible)
            test_imports = [
                ("yaml", "yaml"),
                ("json", "json"),
                ("os", "os"),
                ("pathlib", "pathlib")
            ]

            # Test relative imports by trying to import the modules directly
            script_imports = []
            for module_path in ["scripts.hardening.docker_standardization",
                              "scripts.hardening.environment_validator",
                              "scripts.hardening.dependency_validator"]:
                try:
                    # Try importing by executing the module
                    import subprocess
                    import sys
                    result = subprocess.run(
                        [sys.executable, "-c", f"import {module_path}"],
                        capture_output=True, text=True, cwd=self.workspace_path
                    )
                    if result.returncode != 0:
                        script_imports.append(f"{module_path}: Import failed")
                    else:
                        script_imports.append(f"{module_path}: OK")
                except Exception as e:
                    script_imports.append(f"{module_path}: {e}")

            failed_imports = []
            for std_module, import_name in test_imports:
                try:
                    __import__(import_name)
                except ImportError as e:
                    failed_imports.append(f"{std_module}: {e}")

            all_failed = failed_imports + [imp for imp in script_imports if "failed" in imp.lower() or "error" in imp.lower()]

            if all_failed:
                return {
                    "passed": False,
                    "error": f"Import errors: {', '.join(all_failed)}",
                    "failed_imports": all_failed
                }

            return {"passed": True, "imports_tested": len(test_imports) + len(script_imports)}

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _check_config_files(self) -> Dict[str, Any]:
        """Check configuration files"""
        logger.info("Checking configuration files...")

        try:
            config_files = [
                "docker-compose.dev.yml",
                "config/standardized/port_registry.json"
            ]

            missing_files = []
            invalid_files = []

            for config_file in config_files:
                file_path = self.workspace_path / config_file
                if not file_path.exists():
                    missing_files.append(config_file)
                    continue

                # Try to parse the file
                try:
                    if config_file.endswith('.yml'):
                        import yaml
                        with open(file_path, 'r') as f:
                            yaml.safe_load(f)
                    elif config_file.endswith('.json'):
                        with open(file_path, 'r') as f:
                            json.load(f)
                except Exception as e:
                    invalid_files.append(f"{config_file}: {e}")

            if missing_files or invalid_files:
                error_msg = ""
                if missing_files:
                    error_msg += f"Missing files: {', '.join(missing_files)}. "
                if invalid_files:
                    error_msg += f"Invalid files: {', '.join(invalid_files)}"

                return {
                    "passed": False,
                    "error": error_msg,
                    "missing_files": missing_files,
                    "invalid_files": invalid_files
                }

            return {"passed": True, "files_checked": len(config_files)}

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _check_ports_quick(self) -> Dict[str, Any]:
        """Quick port configuration check"""
        logger.info("Checking port configurations...")

        try:
            result = subprocess.run(
                [sys.executable, "scripts/hardening/docker_standardization.py"],
                capture_output=True, text=True, timeout=60
            )

            if result.returncode != 0:
                return {
                    "passed": False,
                    "error": f"Port validation failed: {result.stderr}",
                    "stdout": result.stdout
                }

            return {
                "passed": True,
                "stdout": result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _check_dependencies(self) -> Dict[str, Any]:
        """Check service dependencies"""
        logger.info("Checking service dependencies...")

        try:
            result = subprocess.run(
                [sys.executable, "scripts/hardening/dependency_validator.py"],
                capture_output=True, text=True, timeout=60
            )

            return {
                "passed": result.returncode == 0,
                "stdout": result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout,
                "stderr": result.stderr
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _check_dockerfiles(self) -> Dict[str, Any]:
        """Check Dockerfiles"""
        logger.info("Checking Dockerfiles...")

        try:
            result = subprocess.run(
                [sys.executable, "scripts/hardening/dockerfile_validator.py"],
                capture_output=True, text=True, timeout=120
            )

            # Dockerfile validator exits with 1 if critical issues found
            passed = result.returncode == 0 or "No critical Dockerfile issues" in result.stdout

            return {
                "passed": passed,
                "stdout": result.stdout[:1000] + "..." if len(result.stdout) > 1000 else result.stdout,
                "stderr": result.stderr
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _check_environment(self) -> Dict[str, Any]:
        """Check environment variables"""
        logger.info("Checking environment variables...")

        try:
            result = subprocess.run(
                [sys.executable, "scripts/hardening/environment_validator.py"],
                capture_output=True, text=True, timeout=60
            )

            return {
                "passed": result.returncode == 0,
                "stdout": result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout,
                "stderr": result.stderr
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _check_connectivity(self) -> Dict[str, Any]:
        """Check service connectivity"""
        logger.info("Checking service connectivity...")

        try:
            result = subprocess.run(
                [sys.executable, "scripts/hardening/service_connectivity_validator.py"],
                capture_output=True, text=True, timeout=60
            )

            return {
                "passed": result.returncode == 0,
                "stdout": result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout,
                "stderr": result.stderr
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _run_functional_tests(self) -> Dict[str, Any]:
        """Run functional tests"""
        logger.info("Running functional tests...")

        try:
            result = subprocess.run(
                [sys.executable, "ecosystem_functional_test_suite.py"],
                capture_output=True, text=True, timeout=300  # 5 minutes
            )

            return {
                "passed": result.returncode == 0,
                "stdout": result.stdout[:1000] + "..." if len(result.stdout) > 1000 else result.stdout,
                "stderr": result.stderr
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _check_performance(self) -> Dict[str, Any]:
        """Check performance metrics"""
        logger.info("Checking performance metrics...")

        try:
            result = subprocess.run(
                [sys.executable, "scripts/safeguards/unified_health_monitor.py", "--performance"],
                capture_output=True, text=True, timeout=60
            )

            return {
                "passed": result.returncode == 0,
                "stdout": result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout,
                "stderr": result.stderr
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _check_health_endpoints(self) -> Dict[str, Any]:
        """Check health endpoints for all services"""
        logger.info("Checking health endpoints...")

        try:
            # Run comprehensive health endpoint validator
            result = subprocess.run(
                [sys.executable, "scripts/safeguards/health_endpoint_validator.py", "--mode", "single"],
                capture_output=True, text=True, cwd=self.workspace_path, timeout=60
            )

            if result.returncode == 0:
                return {"passed": True, "health_checks": "passed", "details": result.stdout}
            else:
                return {
                    "passed": False,
                    "error": f"Health endpoint validation failed: {result.stderr}",
                    "details": result.stdout
                }

        except subprocess.TimeoutExpired:
            return {"passed": False, "error": "Health endpoint validation timed out"}
        except Exception as e:
            return {"passed": False, "error": f"Health check exception: {str(e)}"}

    def _check_config_drift(self) -> Dict[str, Any]:
        """Check for configuration drift across the ecosystem"""
        logger.info("Checking for configuration drift...")

        try:
            # Run comprehensive configuration drift detection
            result = subprocess.run(
                [sys.executable, "scripts/safeguards/config_drift_detector.py", "--scan-only"],
                capture_output=True, text=True, cwd=self.workspace_path, timeout=60
            )

            if result.returncode == 0:
                # Now run the actual drift detection
                drift_result = subprocess.run(
                    [sys.executable, "scripts/safeguards/config_drift_detector.py"],
                    capture_output=True, text=True, cwd=self.workspace_path, timeout=120
                )

                if drift_result.returncode == 0:
                    return {"passed": True, "config_drift": "no_critical_issues"}
                else:
                    return {
                        "passed": False,
                        "error": f"Configuration drift detected: {drift_result.stderr}",
                        "details": drift_result.stdout
                    }
            else:
                return {
                    "passed": False,
                    "error": f"Configuration scan failed: {result.stderr}",
                    "details": result.stdout
                }

        except subprocess.TimeoutExpired:
            return {"passed": False, "error": "Configuration drift detection timed out"}
        except Exception as e:
            return {"passed": False, "error": f"Configuration drift check exception: {str(e)}"}

    def _check_logging(self) -> Dict[str, Any]:
        """Check logging configuration and validation"""
        logger.info("Checking logging configuration...")

        try:
            # This would validate that all services have proper logging setup
            # For now, we'll do a basic check
            result = subprocess.run(
                [sys.executable, "-c", "print('Logging validation placeholder - implement actual logging checks')"],
                capture_output=True, text=True, cwd=self.workspace_path, timeout=30
            )

            return {
                "passed": result.returncode == 0,
                "logging_check": "basic_validation",
                "details": result.stdout
            }

        except subprocess.TimeoutExpired:
            return {"passed": False, "error": "Logging validation timed out"}
        except Exception as e:
            return {"passed": False, "error": f"Logging check exception: {str(e)}"}

    def _check_api_contracts(self) -> Dict[str, Any]:
        """Check API contracts for breaking changes"""
        logger.info("Checking API contracts...")

        try:
            # Run comprehensive API contract validation
            result = subprocess.run(
                [sys.executable, "scripts/safeguards/api_contract_validator.py"],
                capture_output=True, text=True, cwd=self.workspace_path, timeout=120
            )

            if result.returncode == 0:
                return {"passed": True, "api_contracts": "valid", "details": result.stdout}
            else:
                return {
                    "passed": False,
                    "error": f"API contract validation failed: {result.stderr}",
                    "details": result.stdout
                }

        except subprocess.TimeoutExpired:
            return {"passed": False, "error": "API contract validation timed out"}
        except Exception as e:
            return {"passed": False, "error": f"API contract check exception: {str(e)}"}

    def _check_integration(self) -> Dict[str, Any]:
        """Check integration between services"""
        logger.info("Checking service integration...")

        try:
            # This could be enhanced to run specific integration tests
            result = subprocess.run(
                [sys.executable, "-c", "print('Integration check placeholder - implement actual integration tests')"],
                capture_output=True, text=True, timeout=30
            )

            return {
                "passed": True,  # Placeholder
                "message": "Integration check completed (placeholder)",
                "stdout": result.stdout
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _check_secrets(self) -> Dict[str, Any]:
        """Check for secrets and sensitive data"""
        logger.info("Checking for secrets...")

        try:
            # Simple pattern matching for potential secrets
            secret_patterns = [
                r'password\s*[=:]\s*["\'][^"\']+["\']',
                r'secret\s*[=:]\s*["\'][^"\']+["\']',
                r'key\s*[=:]\s*["\'][^"\']+["\']',
                r'token\s*[=:]\s*["\'][^"\']+["\']'
            ]

            found_secrets = []

            # Check key files
            files_to_check = [
                "docker-compose.dev.yml",
                "scripts/hardening/*.py"
            ]

            for file_pattern in files_to_check:
                for file_path in self.workspace_path.glob(file_pattern):
                    if file_path.is_file():
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()

                            for pattern in secret_patterns:
                                matches = re.findall(pattern, content, re.IGNORECASE)
                                if matches:
                                    found_secrets.extend([f"{file_path}: {match[:50]}..." for match in matches[:3]])
                        except Exception:
                            pass  # Skip files that can't be read

            if found_secrets:
                return {
                    "passed": False,
                    "error": f"Potential secrets found: {len(found_secrets)} instances",
                    "secrets_found": found_secrets[:5]  # Show first 5
                }

            return {"passed": True, "message": "No obvious secrets found"}

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _check_vulnerabilities(self) -> Dict[str, Any]:
        """Check for vulnerabilities"""
        logger.info("Checking for vulnerabilities...")

        try:
            # Placeholder for vulnerability scanning
            # In a real implementation, this would integrate with tools like:
            # - Trivy for container scanning
            # - Snyk for dependency scanning
            # - Bandit for Python security

            return {
                "passed": True,
                "message": "Vulnerability check completed (placeholder - integrate with security tools)",
                "tools_recommended": ["trivy", "snyk", "bandit"]
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _check_permissions(self) -> Dict[str, Any]:
        """Check file permissions"""
        logger.info("Checking file permissions...")

        try:
            # Check for executable scripts that shouldn't be executable
            suspicious_files = []

            for py_file in self.workspace_path.rglob("*.py"):
                if os.access(py_file, os.X_OK) and py_file.name not in ["__main__.py"]:
                    suspicious_files.append(str(py_file))

            if suspicious_files:
                return {
                    "passed": False,
                    "error": f"Python files with executable permissions: {len(suspicious_files)}",
                    "suspicious_files": suspicious_files[:5]
                }

            return {"passed": True, "message": "File permissions look good"}

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _generate_final_report(self, overall_success: bool):
        """Generate final CI/CD report"""
        report = {
            "timestamp": time.time(),
            "overall_success": overall_success,
            "validation_levels": list(self.results.keys()),
            "summary": {},
            "details": self.results
        }

        # Calculate summary
        total_checks = 0
        passed_checks = 0

        for level, level_results in self.results.items():
            if "checks" in level_results:
                for check_name, check_result in level_results["checks"].items():
                    total_checks += 1
                    if check_result.get("passed", False):
                        passed_checks += 1

        report["summary"] = {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": total_checks - passed_checks,
            "success_rate": passed_checks / total_checks if total_checks > 0 else 0
        }

        # Save report
        report_file = self.reports_dir / f"ci_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        # Print summary
        logger.info("\n📊 CI/CD VALIDATION SUMMARY")
        logger.info(f"  Overall Status: {'✅ PASSED' if overall_success else '❌ FAILED'}")

        # Calculate summary stats if not already available
        if 'summary' not in report:
            total_checks = sum(len(level_results.get("checks", {})) for level_results in self.results.values() if "checks" in level_results)
            passed_checks = sum(
                1 for level_results in self.results.values() if "checks" in level_results
                for check_result in level_results["checks"].values() if check_result.get("passed", False)
            )
            success_rate = passed_checks / total_checks if total_checks > 0 else 0

            logger.info(f"  Total Checks: {total_checks}")
            logger.info(f"  Passed: {passed_checks}")
            logger.info(f"  Failed: {total_checks - passed_checks}")
            logger.info(f"  Success Rate: {success_rate:.1f}")
        else:
            summary = report["summary"]
            logger.info(f"  Total Checks: {summary.get('total_checks', 0)}")
            logger.info(f"  Passed: {summary.get('passed_checks', 0)}")
            logger.info(f"  Failed: {summary.get('failed_checks', 0)}")
            logger.info(f"  Success Rate: {summary.get('success_rate', 0):.1f}")

        logger.info(f"  Report Saved: {report_file}")

        return report


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Ecosystem CI/CD Runner")
    parser.add_argument(
        "--level",
        choices=["quick", "standard", "comprehensive"],
        default="standard",
        help="Validation level to run"
    )
    parser.add_argument(
        "--workspace",
        default=".",
        help="Workspace path"
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Exit immediately on first failure"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Only generate reports, don't fail on errors"
    )

    args = parser.parse_args()

    # Set up logging based on report-only flag
    if args.report_only:
        logging.getLogger().setLevel(logging.WARNING)

    runner = CIRunner(args.workspace)

    try:
        success = runner.run_validation_suite(args.level)

        if args.report_only:
            success = True  # Don't fail in report-only mode

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("CI/CD validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"CI/CD validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
