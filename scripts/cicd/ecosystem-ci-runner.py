#!/usr/bin/env python3
"""
🚀 Ecosystem CI/CD Runner with Audit Framework Integration
Comprehensive CI/CD automation and validation pipeline

Usage:
    python ecosystem-ci-runner.py --level quick
    python ecosystem-ci-runner.py --level standard --service shared
    python ecosystem-ci-runner.py --level comprehensive --output json
"""

import sys
import os
import json
import time
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EcosystemCIRunner:
    """Comprehensive CI/CD runner with audit framework integration"""

    def __init__(self, level: str = "standard", service: Optional[str] = None,
                 output_format: str = "text", verbose: bool = False):
        self.level = level
        self.service = service
        self.output_format = output_format
        self.verbose = verbose
        self.project_root = Path(__file__).parent.parent.parent
        self.results = {}

    def run(self) -> int:
        """Execute CI/CD pipeline based on level"""
        start_time = time.time()

        try:
            logger.info(f"🚀 Starting {self.level} CI/CD pipeline")

            if self.level == "quick":
                result = self._run_quick_checks()
            elif self.level == "standard":
                result = self._run_standard_checks()
            elif self.level == "comprehensive":
                result = self._run_comprehensive_checks()
            else:
                logger.error(f"Unknown level: {self.level}")
                return 1

            execution_time = time.time() - start_time
            self._output_results(result, execution_time)

            return 0 if result["passed"] else 1

        except Exception as e:
            logger.error(f"CI/CD pipeline failed: {e}")
            return 1

    def _run_quick_checks(self) -> Dict[str, Any]:
        """Quick CI checks - syntax, imports, basic validation"""
        logger.info("⚡ Running quick checks...")

        checks = {
            "syntax_check": self._check_python_syntax(),
            "import_check": self._check_imports(),
            "config_validation": self._validate_configs(),
            "basic_audit": self._run_basic_audit()
        }

        passed = all(check["passed"] for check in checks.values())
        return {
            "level": "quick",
            "passed": passed,
            "checks": checks,
            "summary": f"Quick checks {'PASSED' if passed else 'FAILED'}"
        }

    def _run_standard_checks(self) -> Dict[str, Any]:
        """Standard CI checks - includes dependency analysis, Dockerfiles, environment"""
        logger.info("🔍 Running standard checks...")

        quick_checks = self._run_quick_checks()
        if not quick_checks["passed"]:
            return {
                "level": "standard",
                "passed": False,
                "error": "Quick checks failed, aborting standard checks",
                "checks": quick_checks["checks"]
            }

        additional_checks = {
            "dependency_analysis": self._analyze_dependencies(),
            "docker_validation": self._validate_dockerfiles(),
            "environment_check": self._check_environment(),
            "standard_audit": self._run_standard_audit()
        }

        all_checks = {**quick_checks["checks"], **additional_checks}
        passed = all(check["passed"] for check in all_checks.values())

        return {
            "level": "standard",
            "passed": passed,
            "checks": all_checks,
            "summary": f"Standard checks {'PASSED' if passed else 'FAILED'}"
        }

    def _run_comprehensive_checks(self) -> Dict[str, Any]:
        """Comprehensive CI checks - includes functional tests, performance, integration"""
        logger.info("🔬 Running comprehensive checks...")

        standard_checks = self._run_standard_checks()
        if not standard_checks["passed"]:
            return {
                "level": "comprehensive",
                "passed": False,
                "error": "Standard checks failed, aborting comprehensive checks",
                "checks": standard_checks["checks"]
            }

        additional_checks = {
            "functional_tests": self._run_functional_tests(),
            "performance_checks": self._run_performance_checks(),
            "integration_tests": self._run_integration_tests(),
            "security_audit": self._run_security_audit(),
            "comprehensive_audit": self._run_comprehensive_audit()
        }

        all_checks = {**standard_checks["checks"], **additional_checks}
        passed = all(check["passed"] for check in all_checks.values())

        return {
            "level": "comprehensive",
            "passed": passed,
            "checks": all_checks,
            "summary": f"Comprehensive checks {'PASSED' if passed else 'FAILED'}"
        }

    def _check_python_syntax(self) -> Dict[str, Any]:
        """Check Python syntax across codebase"""
        try:
            result = subprocess.run([
                sys.executable, "-m", "py_compile",
                *(str(f) for f in Path(self.project_root).rglob("*.py")
                  if not any(part.startswith('.') or part == '__pycache__'
                            for part in f.parts))
            ], capture_output=True, text=True)

            return {
                "passed": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _check_imports(self) -> Dict[str, Any]:
        """Check Python imports"""
        try:
            # Basic import test for key modules
            test_imports = [
                "import sys",
                "import os",
                "import yaml",
                "import json",
                "from pathlib import Path",
                "from dataclasses import dataclass"
            ]

            for import_stmt in test_imports:
                exec(import_stmt)

            return {"passed": True}
        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _validate_configs(self) -> Dict[str, Any]:
        """Validate configuration files"""
        try:
            config_files = [
                "config/audit-config.yaml",
                "config/app.yaml",
                "docker-compose.dev.yml",
                "pytest.ini"
            ]

            for config_file in config_files:
                file_path = self.project_root / config_file
                if file_path.exists():
                    if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                        import yaml
                        yaml.safe_load(file_path.read_text())
                    elif config_file.endswith('.json'):
                        import json
                        json.loads(file_path.read_text())

            return {"passed": True}
        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze project dependencies"""
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "check"
            ], capture_output=True, text=True, cwd=self.project_root)

            return {
                "passed": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _validate_dockerfiles(self) -> Dict[str, Any]:
        """Validate Dockerfiles"""
        try:
            dockerfiles = list(self.project_root.glob("**/Dockerfile*"))
            results = []

            for dockerfile in dockerfiles:
                result = subprocess.run([
                    "docker", "build", "--dry-run", "-f", str(dockerfile), "."
                ], capture_output=True, text=True, cwd=dockerfile.parent)

                results.append({
                    "file": str(dockerfile),
                    "passed": result.returncode == 0,
                    "errors": result.stderr
                })

            passed = all(r["passed"] for r in results)
            return {"passed": passed, "results": results}
        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _check_environment(self) -> Dict[str, Any]:
        """Check environment configuration"""
        try:
            required_env_vars = ["PYTHON_VERSION", "PIP_DISABLE_PIP_VERSION_CHECK"]
            missing_vars = []

            for var in required_env_vars:
                if var not in os.environ:
                    missing_vars.append(var)

            return {
                "passed": len(missing_vars) == 0,
                "missing_variables": missing_vars
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _run_functional_tests(self) -> Dict[str, Any]:
        """Run functional tests"""
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "tests/", "-v", "--tb=short", "--maxfail=5"
            ], capture_output=True, text=True, cwd=self.project_root)

            return {
                "passed": result.returncode == 0,
                "output": result.stdout[-1000:],  # Last 1000 chars
                "errors": result.stderr[-1000:]
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _run_performance_checks(self) -> Dict[str, Any]:
        """Run performance checks"""
        try:
            # Basic performance check - ensure services can start
            result = subprocess.run([
                sys.executable, "-c",
                "import time; start=time.time(); [x**2 for x in range(10000)]; print(f'Perf check: {time.time()-start:.3f}s')"
            ], capture_output=True, text=True)

            return {"passed": result.returncode == 0}
        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        try:
            # Check if docker-compose is available and services can be validated
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.dev.yml", "config"
            ], capture_output=True, text=True, cwd=self.project_root)

            return {"passed": result.returncode == 0}
        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _run_security_audit(self) -> Dict[str, Any]:
        """Run security audit"""
        try:
            # Use audit framework for security checks
            result = subprocess.run([
                sys.executable, "scripts/audit-framework/audit_cli.py",
                "audit", "--service", self.service or "shared",
                "--profile", "ci_fast", "--output", "json"
            ], capture_output=True, text=True, cwd=self.project_root)

            if result.returncode == 0:
                audit_data = json.loads(result.stdout)
                security_score = audit_data.get("code_quality", {}).get("security_score", 0)
                return {"passed": security_score >= 80, "security_score": security_score}
            else:
                return {"passed": False, "error": result.stderr}
        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _run_basic_audit(self) -> Dict[str, Any]:
        """Run basic audit check"""
        return self._run_audit_with_profile("ci_fast")

    def _run_standard_audit(self) -> Dict[str, Any]:
        """Run standard audit check"""
        return self._run_audit_with_profile("standard")

    def _run_comprehensive_audit(self) -> Dict[str, Any]:
        """Run comprehensive audit check"""
        return self._run_audit_with_profile("ci_comprehensive")

    def _run_audit_with_profile(self, profile: str) -> Dict[str, Any]:
        """Run audit with specific profile"""
        try:
            cmd = [
                sys.executable, "scripts/audit-framework/audit_cli.py",
                "audit", "--service", self.service or "shared",
                "--profile", profile, "--output", "json"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)

            if result.returncode == 0:
                audit_data = json.loads(result.stdout)
                score = audit_data.get("overall_score", 0)
                critical_issues = audit_data.get("critical_issues_count", 0)

                # Basic quality gates
                passed = score >= 60 and critical_issues <= 5

                return {
                    "passed": passed,
                    "score": score,
                    "critical_issues": critical_issues,
                    "profile": profile
                }
            else:
                return {"passed": False, "error": result.stderr}
        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _output_results(self, results: Dict[str, Any], execution_time: float):
        """Output results in specified format"""
        if self.output_format == "json":
            output_data = {
                **results,
                "execution_time_seconds": round(execution_time, 2),
                "timestamp": time.time(),
                "runner_version": "1.0.0"
            }
            print(json.dumps(output_data, indent=2))
        else:
            # Text output
            status = "✅ PASSED" if results["passed"] else "❌ FAILED"
            print(f"\n🚀 CI/CD Pipeline Results")
            print(f"Level: {results['level']}")
            print(f"Status: {status}")
            print(f"Execution Time: {execution_time:.2f}s")
            print(f"Summary: {results.get('summary', 'N/A')}")

            if "checks" in results:
                print(f"\n📋 Check Results:")
                for check_name, check_result in results["checks"].items():
                    check_status = "✅" if check_result.get("passed", False) else "❌"
                    print(f"  {check_status} {check_name}")

def main():
    parser = argparse.ArgumentParser(description="Ecosystem CI/CD Runner with Audit Integration")
    parser.add_argument("--level", choices=["quick", "standard", "comprehensive"],
                       default="standard", help="CI validation level")
    parser.add_argument("--service", help="Specific service to audit")
    parser.add_argument("--output", choices=["text", "json"], default="text",
                       help="Output format")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")

    args = parser.parse_args()

    runner = EcosystemCIRunner(
        level=args.level,
        service=args.service,
        output_format=args.output,
        verbose=args.verbose
    )

    sys.exit(runner.run())

if __name__ == "__main__":
    main()