#!/usr/bin/env python3
"""
Service Audit Helper Script

This script helps audit a service by gathering metrics and information
to populate the Service Audit Template.

Usage:
    python scripts/refactoring/audit_service.py <service-name>
    
Example:
    python scripts/refactoring/audit_service.py redis
    python scripts/refactoring/audit_service.py doc_store
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class ServiceAuditor:
    """Audit a service and gather metrics"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.service_path = project_root / "services" / service_name
        self.results: Dict = {}
        
    def audit(self) -> Dict:
        """Run complete audit and return results"""
        print(f"🔍 Auditing service: {self.service_name}")
        print("=" * 60)
        
        self.results = {
            "service_name": self.service_name,
            "audit_date": datetime.now().isoformat(),
            "basic_info": self._get_basic_info(),
            "structure": self._analyze_structure(),
            "dependencies": self._analyze_dependencies(),
            "api_endpoints": self._analyze_api(),
            "code_metrics": self._analyze_code_metrics(),
            "test_coverage": self._analyze_tests(),
            "documentation": self._analyze_documentation(),
            "docker": self._analyze_docker(),
        }
        
        return self.results
    
    def _get_basic_info(self) -> Dict:
        """Get basic service information"""
        print("\n📋 Gathering basic information...")
        
        info = {
            "exists": self.service_path.exists(),
            "path": str(self.service_path),
            "primary_language": "Python",  # Assumed for this ecosystem
        }
        
        if self.service_path.exists():
            # Count lines of code
            try:
                result = subprocess.run(
                    ["find", str(self.service_path), "-name", "*.py", "-exec", "wc", "-l", "{}", "+"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if lines:
                        total_line = lines[-1]
                        info["lines_of_code"] = int(total_line.split()[0])
            except Exception as e:
                print(f"   ⚠️  Could not count lines of code: {e}")
                info["lines_of_code"] = "N/A"
            
            # Check for main.py
            main_file = self.service_path / "main.py"
            info["has_main"] = main_file.exists()
            
            # Check for README
            readme = self.service_path / "README.md"
            info["has_readme"] = readme.exists()
            
            # Get last modified
            try:
                result = subprocess.run(
                    ["git", "log", "-1", "--format=%ai", str(self.service_path)],
                    capture_output=True,
                    text=True,
                    cwd=str(project_root)
                )
                if result.returncode == 0:
                    info["last_updated"] = result.stdout.strip()
            except Exception as e:
                print(f"   ⚠️  Could not get last update date: {e}")
                info["last_updated"] = "N/A"
        
        print(f"   ✓ Service exists: {info['exists']}")
        print(f"   ✓ Lines of code: {info.get('lines_of_code', 'N/A')}")
        
        return info
    
    def _analyze_structure(self) -> Dict:
        """Analyze directory structure for DDD compliance"""
        print("\n🏗️  Analyzing structure...")
        
        structure = {
            "ddd_layers": {},
            "has_tests": False,
            "has_config": False,
            "has_docs": False,
        }
        
        if not self.service_path.exists():
            return structure
        
        # Check for DDD layers
        ddd_layers = ["domain", "application", "infrastructure", "presentation"]
        for layer in ddd_layers:
            layer_path = self.service_path / layer
            exists = layer_path.exists()
            structure["ddd_layers"][layer] = {
                "exists": exists,
                "files": len(list(layer_path.glob("**/*.py"))) if exists else 0
            }
            print(f"   {'✓' if exists else '✗'} {layer}: {structure['ddd_layers'][layer]['files']} files")
        
        # Check for other directories
        structure["has_tests"] = (self.service_path / "tests").exists()
        structure["has_config"] = (self.service_path / "config").exists() or \
                                  (self.service_path / "config.yaml").exists()
        structure["has_docs"] = (self.service_path / "docs").exists()
        
        print(f"   {'✓' if structure['has_tests'] else '✗'} tests/")
        print(f"   {'✓' if structure['has_config'] else '✗'} config/")
        print(f"   {'✓' if structure['has_docs'] else '✗'} docs/")
        
        return structure
    
    def _analyze_dependencies(self) -> Dict:
        """Analyze service dependencies"""
        print("\n🔗 Analyzing dependencies...")
        
        deps = {
            "requirements_file": False,
            "total_dependencies": 0,
            "dependencies": []
        }
        
        requirements_file = self.service_path / "requirements.txt"
        if requirements_file.exists():
            deps["requirements_file"] = True
            try:
                with open(requirements_file) as f:
                    lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    deps["total_dependencies"] = len(lines)
                    deps["dependencies"] = lines[:10]  # First 10
                print(f"   ✓ Found {deps['total_dependencies']} dependencies")
            except Exception as e:
                print(f"   ⚠️  Could not read requirements.txt: {e}")
        else:
            print(f"   ✗ No requirements.txt found")
        
        return deps
    
    def _analyze_api(self) -> Dict:
        """Analyze API endpoints"""
        print("\n🌐 Analyzing API...")
        
        api = {
            "total_endpoints": 0,
            "has_openapi": False,
            "endpoints": []
        }
        
        # Look for route definitions
        if self.service_path.exists():
            try:
                # Search for @router or @app decorators
                result = subprocess.run(
                    ["grep", "-r", "-E", "@(router|app)\\.(get|post|put|patch|delete)", 
                     str(self.service_path), "--include=*.py"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    endpoints = result.stdout.strip().split('\n')
                    api["total_endpoints"] = len(endpoints)
                    api["endpoints"] = endpoints[:5]  # First 5
                    print(f"   ✓ Found {api['total_endpoints']} endpoints")
            except Exception as e:
                print(f"   ⚠️  Could not analyze endpoints: {e}")
        
        # Check for OpenAPI/Swagger
        if self.service_path.exists():
            try:
                result = subprocess.run(
                    ["grep", "-r", "openapi", str(self.service_path), "--include=*.py"],
                    capture_output=True,
                    text=True
                )
                api["has_openapi"] = result.returncode == 0
                print(f"   {'✓' if api['has_openapi'] else '✗'} OpenAPI documentation")
            except Exception:
                pass
        
        return api
    
    def _analyze_code_metrics(self) -> Dict:
        """Analyze code quality metrics"""
        print("\n📊 Analyzing code metrics...")
        
        metrics = {
            "complexity": "N/A",
            "duplication": "N/A",
            "type_hints": "N/A"
        }
        
        # These would require additional tools like radon, pylint, mypy
        # For now, just indicate they need to be measured
        print("   ℹ️  Detailed metrics require: radon, pylint, mypy")
        print("   ℹ️  Run manually: radon cc services/<service> -a")
        
        return metrics
    
    def _analyze_tests(self) -> Dict:
        """Analyze test coverage"""
        print("\n🧪 Analyzing tests...")
        
        tests = {
            "has_tests": False,
            "test_files": 0,
            "coverage": "N/A"
        }
        
        tests_dir = self.service_path / "tests"
        if tests_dir.exists():
            tests["has_tests"] = True
            test_files = list(tests_dir.glob("**/*.py"))
            tests["test_files"] = len(test_files)
            print(f"   ✓ Found {tests['test_files']} test files")
        else:
            print(f"   ✗ No tests directory found")
        
        return tests
    
    def _analyze_documentation(self) -> Dict:
        """Analyze documentation"""
        print("\n📖 Analyzing documentation...")
        
        docs = {
            "has_readme": False,
            "readme_sections": [],
            "has_architecture": False,
            "has_api_docs": False,
        }
        
        # Check README
        readme = self.service_path / "README.md"
        if readme.exists():
            docs["has_readme"] = True
            try:
                with open(readme) as f:
                    content = f.read()
                    # Find headers
                    import re
                    headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
                    docs["readme_sections"] = headers[:10]  # First 10 sections
                print(f"   ✓ README.md exists with {len(headers)} sections")
            except Exception as e:
                print(f"   ⚠️  Could not read README: {e}")
        else:
            print(f"   ✗ No README.md found")
        
        # Check for other docs
        docs["has_architecture"] = (self.service_path / "docs" / "architecture.md").exists() or \
                                   (self.service_path / "ARCHITECTURE.md").exists()
        docs["has_api_docs"] = (self.service_path / "docs" / "api.md").exists() or \
                              (self.service_path / "API.md").exists()
        
        print(f"   {'✓' if docs['has_architecture'] else '✗'} Architecture documentation")
        print(f"   {'✓' if docs['has_api_docs'] else '✗'} API documentation")
        
        return docs
    
    def _analyze_docker(self) -> Dict:
        """Analyze Docker configuration"""
        print("\n🐳 Analyzing Docker...")
        
        docker = {
            "has_dockerfile": False,
            "has_compose": False,
            "has_health_check": False,
        }
        
        # Check for Dockerfile
        dockerfile = self.service_path / "Dockerfile"
        docker["has_dockerfile"] = dockerfile.exists()
        
        if docker["has_dockerfile"]:
            try:
                with open(dockerfile) as f:
                    content = f.read()
                    docker["has_health_check"] = "HEALTHCHECK" in content
                print(f"   ✓ Dockerfile exists")
                print(f"   {'✓' if docker['has_health_check'] else '✗'} Health check defined")
            except Exception as e:
                print(f"   ⚠️  Could not read Dockerfile: {e}")
        else:
            print(f"   ✗ No Dockerfile found")
        
        # Check for docker-compose
        compose = self.service_path / "docker-compose.yml"
        docker["has_compose"] = compose.exists()
        print(f"   {'✓' if docker['has_compose'] else '✗'} docker-compose.yml")
        
        return docker
    
    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """Generate audit report"""
        if not output_path:
            output_path = project_root / "docs" / "refactoring" / "audits" / f"{self.service_name}_audit.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n✅ Audit report saved to: {output_path}")
        return str(output_path)
    
    def print_summary(self):
        """Print summary of audit"""
        print("\n" + "=" * 60)
        print("📊 AUDIT SUMMARY")
        print("=" * 60)
        
        # DDD Compliance Score
        ddd_layers = self.results.get("structure", {}).get("ddd_layers", {})
        ddd_score = sum(1 for layer in ddd_layers.values() if layer.get("exists", False))
        ddd_total = len(ddd_layers)
        
        print(f"\n🏗️  DDD Compliance: {ddd_score}/{ddd_total} layers")
        print(f"   Domain: {'✓' if ddd_layers.get('domain', {}).get('exists') else '✗'}")
        print(f"   Application: {'✓' if ddd_layers.get('application', {}).get('exists') else '✗'}")
        print(f"   Infrastructure: {'✓' if ddd_layers.get('infrastructure', {}).get('exists') else '✗'}")
        print(f"   Presentation: {'✓' if ddd_layers.get('presentation', {}).get('exists') else '✗'}")
        
        # Testing
        tests = self.results.get("test_coverage", {})
        print(f"\n🧪 Testing: {tests.get('test_files', 0)} test files")
        
        # Documentation
        docs = self.results.get("documentation", {})
        doc_score = sum([
            docs.get("has_readme", False),
            docs.get("has_architecture", False),
            docs.get("has_api_docs", False)
        ])
        print(f"\n📖 Documentation: {doc_score}/3 essential docs")
        
        # Docker
        docker = self.results.get("docker", {})
        print(f"\n🐳 Docker: {'✓' if docker.get('has_dockerfile') else '✗'} Dockerfile, {'✓' if docker.get('has_compose') else '✗'} Compose")
        
        # Overall recommendation
        total_score = ddd_score * 25 + doc_score * 10 + (10 if tests.get('has_tests') else 0)
        print(f"\n🎯 Estimated Score: {total_score}/110")
        
        if total_score >= 90:
            print("   ✅ Recommendation: Minor refactor needed")
        elif total_score >= 60:
            print("   ⚠️  Recommendation: Major refactor needed")
        else:
            print("   ❌ Recommendation: Complete rewrite recommended")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python audit_service.py <service-name>")
        print("\nExamples:")
        print("  python audit_service.py redis")
        print("  python audit_service.py doc_store")
        sys.exit(1)
    
    service_name = sys.argv[1]
    
    auditor = ServiceAuditor(service_name)
    auditor.audit()
    auditor.print_summary()
    auditor.generate_report()
    
    print("\n" + "=" * 60)
    print("Next steps:")
    print("1. Review the generated JSON report")
    print("2. Fill out the Service Audit Template manually")
    print("3. Create a refactoring plan")
    print("=" * 60)


if __name__ == "__main__":
    main()

