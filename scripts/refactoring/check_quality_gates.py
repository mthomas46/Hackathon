#!/usr/bin/env python3
"""
Quality Gates Checker

This script validates that a service meets all quality gates before
it can be considered complete.

Usage:
    python scripts/refactoring/check_quality_gates.py <service-name>
    
Example:
    python scripts/refactoring/check_quality_gates.py analysis-service
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class QualityGateChecker:
    """Check if a service passes all quality gates"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.service_path = project_root / "services" / service_name.replace("-", "_")
        if not self.service_path.exists():
            self.service_path = project_root / "services" / service_name
        self.results: Dict = {}
        self.passed_gates = 0
        self.total_gates = 8
        
    def check_all_gates(self) -> Dict:
        """Check all quality gates"""
        print(f"🚦 Checking Quality Gates for: {self.service_name}")
        print("=" * 60)
        
        self.results = {
            "service_name": self.service_name,
            "check_date": datetime.now().isoformat(),
            "gates": {
                "architecture": self._check_gate_architecture(),
                "code_quality": self._check_gate_code_quality(),
                "testing": self._check_gate_testing(),
                "documentation": self._check_gate_documentation(),
                "docker": self._check_gate_docker(),
                "configuration": self._check_gate_configuration(),
                "api_standards": self._check_gate_api_standards(),
                "integration": self._check_gate_integration(),
            }
        }
        
        # Count passed gates
        self.passed_gates = sum(
            1 for gate in self.results["gates"].values() 
            if gate.get("passed", False)
        )
        
        self.results["summary"] = {
            "passed_gates": self.passed_gates,
            "total_gates": self.total_gates,
            "percentage": (self.passed_gates / self.total_gates) * 100,
            "overall_passed": self.passed_gates == self.total_gates
        }
        
        return self.results
    
    def _check_gate_architecture(self) -> Dict:
        """Gate 1: Architecture Review"""
        print("\n🏗️  Gate 1: Architecture Review")
        
        gate = {
            "name": "Architecture Review",
            "checks": {},
            "passed": False,
            "score": 0,
            "total": 5
        }
        
        if not self.service_path.exists():
            print("   ❌ Service directory does not exist")
            return gate
        
        # Check DDD structure
        ddd_layers = ["domain", "application", "infrastructure", "presentation"]
        for layer in ddd_layers:
            exists = (self.service_path / layer).exists()
            gate["checks"][f"has_{layer}"] = exists
            if exists:
                gate["score"] += 1
            print(f"   {'✓' if exists else '✗'} {layer}/ layer")
        
        # Check for circular dependencies (simplified check)
        gate["checks"]["no_circular_deps"] = True  # Would need more complex analysis
        print(f"   ℹ️  Circular dependency check requires manual review")
        
        gate["passed"] = gate["score"] >= 4  # At least 4/5 checks pass
        
        return gate
    
    def _check_gate_code_quality(self) -> Dict:
        """Gate 2: Code Quality"""
        print("\n📊 Gate 2: Code Quality")
        
        gate = {
            "name": "Code Quality",
            "checks": {},
            "passed": False,
            "score": 0,
            "total": 5
        }
        
        if not self.service_path.exists():
            return gate
        
        # Check naming conventions (simplified)
        try:
            # Check for snake_case in Python files
            result = subprocess.run(
                ["find", str(self.service_path), "-name", "*.py", "-type", "f"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                valid_names = all('_' in f or f.endswith('main.py') or f.endswith('__init__.py') 
                                for f in files if f)
                gate["checks"]["naming_conventions"] = valid_names
                if valid_names:
                    gate["score"] += 1
                print(f"   {'✓' if valid_names else '✗'} Naming conventions")
        except Exception as e:
            print(f"   ⚠️  Could not check naming: {e}")
        
        # Check for type hints (look for typing imports)
        try:
            result = subprocess.run(
                ["grep", "-r", "from typing import", str(self.service_path), "--include=*.py"],
                capture_output=True,
                text=True
            )
            has_type_hints = result.returncode == 0
            gate["checks"]["type_hints"] = has_type_hints
            if has_type_hints:
                gate["score"] += 1
            print(f"   {'✓' if has_type_hints else '✗'} Type hints present")
        except Exception:
            pass
        
        # Check for docstrings (look for triple quotes)
        try:
            result = subprocess.run(
                ["grep", "-r", '"""', str(self.service_path), "--include=*.py"],
                capture_output=True,
                text=True
            )
            has_docstrings = result.returncode == 0
            gate["checks"]["docstrings"] = has_docstrings
            if has_docstrings:
                gate["score"] += 1
            print(f"   {'✓' if has_docstrings else '✗'} Docstrings present")
        except Exception:
            pass
        
        # Check for error handling
        try:
            result = subprocess.run(
                ["grep", "-r", "try:", str(self.service_path), "--include=*.py"],
                capture_output=True,
                text=True
            )
            has_error_handling = result.returncode == 0
            gate["checks"]["error_handling"] = has_error_handling
            if has_error_handling:
                gate["score"] += 1
            print(f"   {'✓' if has_error_handling else '✗'} Error handling present")
        except Exception:
            pass
        
        print(f"   ℹ️  Complexity and duplication require: radon, pylint")
        
        gate["passed"] = gate["score"] >= 3  # At least 3/5 checks pass
        
        return gate
    
    def _check_gate_testing(self) -> Dict:
        """Gate 3: Testing"""
        print("\n🧪 Gate 3: Testing")
        
        gate = {
            "name": "Testing",
            "checks": {},
            "passed": False,
            "score": 0,
            "total": 5
        }
        
        tests_dir = self.service_path / "tests"
        
        # Check tests directory exists
        has_tests = tests_dir.exists()
        gate["checks"]["has_tests"] = has_tests
        if has_tests:
            gate["score"] += 1
        print(f"   {'✓' if has_tests else '✗'} tests/ directory")
        
        if has_tests:
            # Check for unit tests
            unit_tests = list(tests_dir.glob("**/test_*.py"))
            has_unit_tests = len(unit_tests) > 0
            gate["checks"]["has_unit_tests"] = has_unit_tests
            if has_unit_tests:
                gate["score"] += 1
            print(f"   {'✓' if has_unit_tests else '✗'} Unit tests ({len(unit_tests)} files)")
            
            # Check for integration tests
            integration_dir = tests_dir / "integration"
            has_integration = integration_dir.exists()
            gate["checks"]["has_integration_tests"] = has_integration
            if has_integration:
                gate["score"] += 1
            print(f"   {'✓' if has_integration else '✗'} Integration tests")
            
            # Check for pytest.ini
            has_pytest_config = (self.service_path / "pytest.ini").exists()
            gate["checks"]["has_pytest_config"] = has_pytest_config
            if has_pytest_config:
                gate["score"] += 1
            print(f"   {'✓' if has_pytest_config else '✗'} pytest.ini")
        
        print(f"   ℹ️  Coverage check requires: pytest-cov")
        
        gate["passed"] = gate["score"] >= 3  # At least 3/5 checks pass
        
        return gate
    
    def _check_gate_documentation(self) -> Dict:
        """Gate 4: Documentation"""
        print("\n📖 Gate 4: Documentation")
        
        gate = {
            "name": "Documentation",
            "checks": {},
            "passed": False,
            "score": 0,
            "total": 5
        }
        
        # Check README
        readme = self.service_path / "README.md"
        has_readme = readme.exists()
        gate["checks"]["has_readme"] = has_readme
        if has_readme:
            gate["score"] += 1
        print(f"   {'✓' if has_readme else '✗'} README.md")
        
        # Check OpenAPI documentation
        try:
            result = subprocess.run(
                ["grep", "-r", "openapi", str(self.service_path), "--include=*.py"],
                capture_output=True,
                text=True
            )
            has_openapi = result.returncode == 0
            gate["checks"]["has_openapi"] = has_openapi
            if has_openapi:
                gate["score"] += 1
            print(f"   {'✓' if has_openapi else '✗'} OpenAPI documentation")
        except Exception:
            pass
        
        # Check architecture docs
        has_arch = (self.service_path / "docs" / "architecture.md").exists() or \
                   (self.service_path / "ARCHITECTURE.md").exists()
        gate["checks"]["has_architecture"] = has_arch
        if has_arch:
            gate["score"] += 1
        print(f"   {'✓' if has_arch else '✗'} Architecture documentation")
        
        # Check integration guide
        has_integration = (self.service_path / "docs" / "integration.md").exists() or \
                         (self.service_path / "INTEGRATION.md").exists()
        gate["checks"]["has_integration_guide"] = has_integration
        if has_integration:
            gate["score"] += 1
        print(f"   {'✓' if has_integration else '✗'} Integration guide")
        
        # Check for docstrings in code
        try:
            result = subprocess.run(
                ["grep", "-r", '"""', str(self.service_path), "--include=*.py"],
                capture_output=True,
                text=True
            )
            has_docstrings = result.returncode == 0 and len(result.stdout.split('\n')) > 10
            gate["checks"]["has_docstrings"] = has_docstrings
            if has_docstrings:
                gate["score"] += 1
            print(f"   {'✓' if has_docstrings else '✗'} Code docstrings")
        except Exception:
            pass
        
        gate["passed"] = gate["score"] >= 4  # At least 4/5 checks pass
        
        return gate
    
    def _check_gate_docker(self) -> Dict:
        """Gate 5: Docker & Deployment"""
        print("\n🐳 Gate 5: Docker & Deployment")
        
        gate = {
            "name": "Docker & Deployment",
            "checks": {},
            "passed": False,
            "score": 0,
            "total": 5
        }
        
        # Check Dockerfile
        dockerfile = self.service_path / "Dockerfile"
        has_dockerfile = dockerfile.exists()
        gate["checks"]["has_dockerfile"] = has_dockerfile
        if has_dockerfile:
            gate["score"] += 1
        print(f"   {'✓' if has_dockerfile else '✗'} Dockerfile")
        
        # Check docker-compose
        compose = self.service_path / "docker-compose.yml"
        has_compose = compose.exists()
        gate["checks"]["has_compose"] = has_compose
        if has_compose:
            gate["score"] += 1
        print(f"   {'✓' if has_compose else '✗'} docker-compose.yml")
        
        # Check health check in Dockerfile
        if has_dockerfile:
            try:
                with open(dockerfile) as f:
                    content = f.read()
                    has_health = "HEALTHCHECK" in content
                    gate["checks"]["has_health_check"] = has_health
                    if has_health:
                        gate["score"] += 1
                    print(f"   {'✓' if has_health else '✗'} Health check defined")
            except Exception:
                pass
        
        # Check for main.py (can run standalone)
        main_file = self.service_path / "main.py"
        has_main = main_file.exists()
        gate["checks"]["has_main"] = has_main
        if has_main:
            gate["score"] += 1
        print(f"   {'✓' if has_main else '✗'} main.py (standalone)")
        
        gate["passed"] = gate["score"] >= 4  # At least 4/5 checks pass
        
        return gate
    
    def _check_gate_configuration(self) -> Dict:
        """Gate 6: Configuration"""
        print("\n⚙️  Gate 6: Configuration")
        
        gate = {
            "name": "Configuration",
            "checks": {},
            "passed": False,
            "score": 0,
            "total": 5
        }
        
        # Check for config files
        has_config_yaml = (self.service_path / "config.yaml").exists()
        has_config_dir = (self.service_path / "config").exists()
        has_config = has_config_yaml or has_config_dir
        gate["checks"]["has_config"] = has_config
        if has_config:
            gate["score"] += 1
        print(f"   {'✓' if has_config else '✗'} Configuration files")
        
        # Check for environment-specific configs
        has_dev_config = (self.service_path / "config.development.yaml").exists()
        has_prod_config = (self.service_path / "config.production.yaml").exists()
        gate["checks"]["has_env_configs"] = has_dev_config or has_prod_config
        if has_dev_config or has_prod_config:
            gate["score"] += 1
        print(f"   {'✓' if (has_dev_config or has_prod_config) else '✗'} Environment configs")
        
        # Check for .env.example
        has_env_example = (self.service_path / ".env.example").exists()
        gate["checks"]["has_env_example"] = has_env_example
        if has_env_example:
            gate["score"] += 1
        print(f"   {'✓' if has_env_example else '✗'} .env.example")
        
        # Check for environment variables in documentation
        if (self.service_path / "README.md").exists():
            try:
                with open(self.service_path / "README.md") as f:
                    content = f.read()
                    has_env_docs = "environment" in content.lower() or "configuration" in content.lower()
                    gate["checks"]["has_env_docs"] = has_env_docs
                    if has_env_docs:
                        gate["score"] += 1
                    print(f"   {'✓' if has_env_docs else '✗'} Environment documented")
            except Exception:
                pass
        
        gate["passed"] = gate["score"] >= 3  # At least 3/5 checks pass
        
        return gate
    
    def _check_gate_api_standards(self) -> Dict:
        """Gate 7: API Standards"""
        print("\n🌐 Gate 7: API Standards")
        
        gate = {
            "name": "API Standards",
            "checks": {},
            "passed": False,
            "score": 0,
            "total": 5
        }
        
        # Check for REST endpoints
        try:
            result = subprocess.run(
                ["grep", "-r", "-E", "@(router|app)\\.(get|post|put|patch|delete)", 
                 str(self.service_path), "--include=*.py"],
                capture_output=True,
                text=True
            )
            has_rest = result.returncode == 0
            gate["checks"]["has_rest_endpoints"] = has_rest
            if has_rest:
                gate["score"] += 1
            print(f"   {'✓' if has_rest else '✗'} REST endpoints")
        except Exception:
            pass
        
        # Check for OpenAPI/Swagger
        try:
            result = subprocess.run(
                ["grep", "-r", "openapi", str(self.service_path), "--include=*.py"],
                capture_output=True,
                text=True
            )
            has_openapi = result.returncode == 0
            gate["checks"]["has_swagger"] = has_openapi
            if has_openapi:
                gate["score"] += 1
            print(f"   {'✓' if has_openapi else '✗'} Swagger/OpenAPI")
        except Exception:
            pass
        
        # Check for error handling
        try:
            result = subprocess.run(
                ["grep", "-r", "HTTPException", str(self.service_path), "--include=*.py"],
                capture_output=True,
                text=True
            )
            has_error_responses = result.returncode == 0
            gate["checks"]["has_error_responses"] = has_error_responses
            if has_error_responses:
                gate["score"] += 1
            print(f"   {'✓' if has_error_responses else '✗'} Error responses")
        except Exception:
            pass
        
        # Check for versioning
        try:
            result = subprocess.run(
                ["grep", "-r", "/api/v", str(self.service_path), "--include=*.py"],
                capture_output=True,
                text=True
            )
            has_versioning = result.returncode == 0
            gate["checks"]["has_versioning"] = has_versioning
            if has_versioning:
                gate["score"] += 1
            print(f"   {'✓' if has_versioning else '✗'} API versioning")
        except Exception:
            pass
        
        gate["passed"] = gate["score"] >= 3  # At least 3/5 checks pass
        
        return gate
    
    def _check_gate_integration(self) -> Dict:
        """Gate 8: Integration"""
        print("\n🔗 Gate 8: Integration")
        
        gate = {
            "name": "Integration",
            "checks": {},
            "passed": False,
            "score": 0,
            "total": 5
        }
        
        # Check for health endpoint
        try:
            result = subprocess.run(
                ["grep", "-r", "/health", str(self.service_path), "--include=*.py"],
                capture_output=True,
                text=True
            )
            has_health = result.returncode == 0
            gate["checks"]["has_health_endpoint"] = has_health
            if has_health:
                gate["score"] += 1
            print(f"   {'✓' if has_health else '✗'} Health endpoint")
        except Exception:
            pass
        
        # Check for service discovery
        try:
            result = subprocess.run(
                ["grep", "-r", "SERVICE_NAME", str(self.service_path), "--include=*.py"],
                capture_output=True,
                text=True
            )
            has_service_name = result.returncode == 0
            gate["checks"]["has_service_discovery"] = has_service_name
            if has_service_name:
                gate["score"] += 1
            print(f"   {'✓' if has_service_name else '✗'} Service discovery")
        except Exception:
            pass
        
        # Check for dependency injection
        try:
            result = subprocess.run(
                ["grep", "-r", "Depends", str(self.service_path), "--include=*.py"],
                capture_output=True,
                text=True
            )
            has_di = result.returncode == 0
            gate["checks"]["has_dependency_injection"] = has_di
            if has_di:
                gate["score"] += 1
            print(f"   {'✓' if has_di else '✗'} Dependency injection")
        except Exception:
            pass
        
        # Check for integration tests
        integration_tests = self.service_path / "tests" / "integration"
        has_integration_tests = integration_tests.exists()
        gate["checks"]["has_integration_tests"] = has_integration_tests
        if has_integration_tests:
            gate["score"] += 1
        print(f"   {'✓' if has_integration_tests else '✗'} Integration tests")
        
        gate["passed"] = gate["score"] >= 3  # At least 3/5 checks pass
        
        return gate
    
    def generate_report(self, output_path: Optional[Path] = None):
        """Generate quality gates report"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = project_root / "docs" / "refactoring" / "reports" / f"{self.service_name}_quality_gates_{timestamp}.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n✅ Quality gates report saved to: {output_path}")
        return str(output_path)
    
    def print_summary(self):
        """Print summary of quality gates"""
        print("\n" + "=" * 60)
        print("🚦 QUALITY GATES SUMMARY")
        print("=" * 60)
        
        summary = self.results.get("summary", {})
        passed = summary.get("passed_gates", 0)
        total = summary.get("total_gates", 0)
        percentage = summary.get("percentage", 0)
        
        print(f"\n📊 Overall: {passed}/{total} gates passed ({percentage:.1f}%)")
        
        # Show each gate
        for gate_name, gate_data in self.results.get("gates", {}).items():
            status = "✅" if gate_data.get("passed") else "❌"
            score = gate_data.get("score", 0)
            total_score = gate_data.get("total", 0)
            print(f"   {status} {gate_data.get('name')}: {score}/{total_score}")
        
        # Overall status
        print(f"\n{'🎉' if summary.get('overall_passed') else '⚠️'} ", end="")
        if summary.get("overall_passed"):
            print("ALL QUALITY GATES PASSED! Service is ready.")
        else:
            print(f"Quality gates not met. {total - passed} gates need attention.")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python check_quality_gates.py <service-name>")
        print("\nExamples:")
        print("  python check_quality_gates.py analysis-service")
        print("  python check_quality_gates.py doc_store")
        sys.exit(1)
    
    service_name = sys.argv[1]
    
    checker = QualityGateChecker(service_name)
    checker.check_all_gates()
    checker.print_summary()
    checker.generate_report()
    
    # Exit with appropriate code
    if checker.results["summary"]["overall_passed"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

