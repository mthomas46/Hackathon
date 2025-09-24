#!/usr/bin/env python3
"""
Comprehensive Audit Framework for LLM Documentation Ecosystem

This script provides automated assessment of services across four critical dimensions:
- Architecture: DDD compliance, REST design, layer separation
- Code Quality: Complexity, testing, duplication, documentation
- Performance: Runtime, database, resource optimization
- Maintainability: Organization, error handling, scalability, DevOps

Usage:
    python audit_framework.py audit --service doc_store
    python audit_framework.py compare --services doc_store,prompt_store
    python audit_framework.py trend --service shared --period 6months
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AuditResults:
    """Container for audit results across all dimensions."""
    service_name: str
    audit_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Overall scores
    overall_score: float = 0.0
    grade: str = ""

    # Dimension results
    architecture: Dict[str, Any] = field(default_factory=dict)
    code_quality: Dict[str, Any] = field(default_factory=dict)
    performance: Dict[str, Any] = field(default_factory=dict)
    maintainability: Dict[str, Any] = field(default_factory=dict)

    # Issues and recommendations
    critical_issues: List[Dict[str, Any]] = field(default_factory=list)
    priority_improvements: List[Dict[str, Any]] = field(default_factory=list)
    estimated_effort_days: float = 0.0

@dataclass
class ServiceInfo:
    """Service metadata for auditing."""
    name: str
    path: Path
    files: int = 0
    lines: int = 0
    tests: int = 0

class AuditFramework:
    """Main audit framework class."""

    DIMENSION_WEIGHTS = {
        'architecture': 0.30,
        'code_quality': 0.25,
        'performance': 0.20,
        'maintainability': 0.25
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.services_dir = project_root / "services"

    def discover_services(self) -> List[ServiceInfo]:
        """Discover all services in the ecosystem."""
        services = []

        if not self.services_dir.exists():
            logger.error(f"Services directory not found: {self.services_dir}")
            return services

        for service_dir in self.services_dir.iterdir():
            if service_dir.is_dir() and not service_dir.name.startswith('.'):
                service_info = self._analyze_service_structure(service_dir)
                if service_info:
                    services.append(service_info)

        return services

    def _analyze_service_structure(self, service_path: Path) -> Optional[ServiceInfo]:
        """Analyze basic service structure."""
        try:
            # Count Python files and lines
            python_files = list(service_path.rglob("*.py"))
            total_lines = 0
            test_files = 0

            for py_file in python_files:
                if py_file.name.startswith('test_') or 'test' in str(py_file):
                    test_files += 1
                try:
                    with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                        total_lines += len(f.readlines())
                except:
                    pass

            return ServiceInfo(
                name=service_path.name,
                path=service_path,
                files=len(python_files),
                lines=total_lines,
                tests=test_files
            )
        except Exception as e:
            logger.warning(f"Failed to analyze service {service_path.name}: {e}")
            return None

    async def audit_service(self, service_name: str) -> AuditResults:
        """Run comprehensive audit on a specific service."""
        services = self.discover_services()
        service_info = next((s for s in services if s.name == service_name), None)

        if not service_info:
            raise ValueError(f"Service '{service_name}' not found")

        logger.info(f"Starting comprehensive audit for service: {service_name}")

        results = AuditResults(service_name=service_name)

        # Run all audit dimensions
        results.architecture = await self._audit_architecture(service_info)
        results.code_quality = await self._audit_code_quality(service_info)
        results.performance = await self._audit_performance(service_info)
        results.maintainability = await self._audit_maintainability(service_info)

        # Calculate overall score
        results.overall_score = self._calculate_overall_score(results)
        results.grade = self._calculate_grade(results.overall_score)

        # Generate issues and recommendations
        results.critical_issues = self._identify_critical_issues(results)
        results.priority_improvements = self._generate_recommendations(results)
        results.estimated_effort_days = self._estimate_effort(results)

        logger.info(".2f"
        return results

    async def _audit_architecture(self, service: ServiceInfo) -> Dict[str, Any]:
        """Audit architectural compliance."""
        logger.info(f"Auditing architecture for {service.name}")

        scores = {
            'ddd_compliance': await self._check_ddd_compliance(service),
            'rest_compliance': await self._check_rest_compliance(service),
            'layer_separation': await self._check_layer_separation(service)
        }

        # Calculate weighted architecture score
        architecture_score = (
            scores['ddd_compliance'] * 0.40 +
            scores['rest_compliance'] * 0.35 +
            scores['layer_separation'] * 0.25
        )

        return {
            'score': round(architecture_score, 2),
            'ddd_compliance': scores['ddd_compliance'],
            'rest_compliance': scores['rest_compliance'],
            'layer_separation': scores['layer_separation'],
            'issues': self._identify_architecture_issues(scores),
            'recommendations': self._generate_architecture_recommendations(scores)
        }

    async def _check_ddd_compliance(self, service: ServiceInfo) -> float:
        """Check Domain-Driven Design compliance."""
        score = 0.0
        total_checks = 0

        # Check for domain layer structure
        domain_patterns = ['domain', 'entities', 'value_objects', 'services']
        domain_files = list(service.path.rglob("**/domain/**/*.py"))

        if domain_files:
            score += 30
        total_checks += 30

        # Check for repository pattern
        repo_files = list(service.path.rglob("**/repository.py")) + list(service.path.rglob("**/repositories/**/*.py"))
        if repo_files:
            score += 25
        total_checks += 25

        # Check for service layer
        service_files = list(service.path.rglob("**/service.py")) + list(service.path.rglob("**/services/**/*.py"))
        if service_files:
            score += 20
        total_checks += 20

        # Check for proper imports (basic heuristic)
        try:
            main_file = service.path / "main.py"
            if main_file.exists():
                with open(main_file, 'r') as f:
                    content = f.read()
                    if 'BaseEntity' in content or 'BaseService' in content:
                        score += 15
                    total_checks += 15
        except:
            pass

        # Check for entity definitions
        entity_files = list(service.path.rglob("**/entities.py")) + list(service.path.rglob("**/entity.py"))
        if entity_files:
            score += 10
        total_checks += 10

        return min(100, (score / total_checks) * 100) if total_checks > 0 else 0

    async def _check_rest_compliance(self, service: ServiceInfo) -> float:
        """Check REST API design compliance."""
        score = 0.0
        total_checks = 0

        try:
            main_file = service.path / "main.py"
            if main_file.exists():
                with open(main_file, 'r') as f:
                    content = f.read()

                    # Check for FastAPI usage
                    if 'FastAPI' in content:
                        score += 25
                    total_checks += 25

                    # Check for proper HTTP methods
                    http_methods = ['@app.get', '@app.post', '@app.put', '@app.patch', '@app.delete']
                    methods_found = sum(1 for method in http_methods if method in content)
                    score += min(25, methods_found * 5)
                    total_checks += 25

                    # Check for response models
                    if 'response_model' in content:
                        score += 20
                    total_checks += 20

                    # Check for API documentation
                    if 'docs_url' in content or 'redoc_url' in content:
                        score += 15
                    total_checks += 15

                    # Check for error handling
                    if 'HTTPException' in content:
                        score += 15
                    total_checks += 15
        except:
            pass

        return min(100, (score / total_checks) * 100) if total_checks > 0 else 0

    async def _check_layer_separation(self, service: ServiceInfo) -> float:
        """Check layer separation quality."""
        score = 0.0
        total_checks = 0

        # Check directory structure
        dirs = [d.name for d in service.path.iterdir() if d.is_dir()]

        # Presentation layer (API)
        if any(d in ['api', 'routes', 'controllers'] for d in dirs):
            score += 25
        total_checks += 25

        # Application layer (services, use cases)
        if any(d in ['application', 'use_cases', 'handlers'] for d in dirs):
            score += 25
        total_checks += 25

        # Domain layer
        if 'domain' in dirs:
            score += 25
        total_checks += 25

        # Infrastructure layer
        if any(d in ['infrastructure', 'db', 'config', 'external'] for d in dirs):
            score += 25
        total_checks += 25

        return min(100, (score / total_checks) * 100) if total_checks > 0 else 0

    async def _audit_code_quality(self, service: ServiceInfo) -> Dict[str, Any]:
        """Audit code quality metrics."""
        logger.info(f"Auditing code quality for {service.name}")

        scores = {
            'complexity': await self._check_complexity(service),
            'testing': await self._check_testing(service),
            'duplication': await self._check_duplication(service),
            'documentation': await self._check_documentation(service)
        }

        # Calculate weighted code quality score
        code_quality_score = (
            scores['complexity'] * 0.30 +
            scores['testing'] * 0.35 +
            scores['duplication'] * 0.20 +
            scores['documentation'] * 0.15
        )

        return {
            'score': round(code_quality_score, 2),
            'complexity': scores['complexity'],
            'testing': scores['testing'],
            'duplication': scores['duplication'],
            'documentation': scores['documentation'],
            'issues': self._identify_code_quality_issues(scores),
            'recommendations': self._generate_code_quality_recommendations(scores)
        }

    async def _check_complexity(self, service: ServiceInfo) -> float:
        """Check code complexity metrics."""
        score = 100.0  # Start with perfect score, deduct for issues

        try:
            # Run flake8 for basic complexity checks
            result = subprocess.run(
                ['flake8', '--select=C901,E501', '--max-line-length=88', str(service.path)],
                capture_output=True, text=True, timeout=30
            )

            # Count complexity violations
            complexity_violations = len([line for line in result.stdout.split('\n') if 'C901' in line])
            line_length_violations = len([line for line in result.stdout.split('\n') if 'E501' in line])

            # Deduct points for violations
            score -= min(30, complexity_violations * 5)  # Max 30 points for complexity
            score -= min(20, line_length_violations * 0.5)  # Max 20 points for line length

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # If flake8 not available, use basic heuristics
            score -= 10  # Penalty for not being able to check

        # Check file sizes as complexity indicator
        large_files = [f for f in service.path.rglob("*.py") if f.stat().st_size > 100000]  # >100KB
        score -= min(20, len(large_files) * 5)  # Max 20 points for large files

        return max(0, score)

    async def _check_testing(self, service: ServiceInfo) -> float:
        """Check testing coverage and quality."""
        score = 0.0

        # Test file coverage
        test_ratio = service.tests / max(1, service.files)  # Avoid division by zero
        if test_ratio > 0.5:  # Good test coverage
            score += 40
        elif test_ratio > 0.2:  # Moderate coverage
            score += 20
        elif test_ratio > 0:
            score += 10

        # Check for test directories
        test_dirs = list(service.path.glob("**/test*")) + list(service.path.glob("**/tests"))
        if test_dirs:
            score += 20

        # Check for CI/CD testing
        ci_files = list(service.path.glob(".github/workflows/*.yml")) + list(service.path.glob(".gitlab-ci.yml"))
        if ci_files:
            score += 20

        # Check for test configuration
        pytest_files = list(service.path.glob("**/pytest.ini")) + list(service.path.glob("**/setup.cfg"))
        if pytest_files:
            score += 20

        return min(100, score)

    async def _check_duplication(self, service: ServiceInfo) -> float:
        """Check for code duplication."""
        score = 100.0  # Start with perfect score

        # Basic duplication check - look for repeated patterns
        try:
            python_files = list(service.path.rglob("*.py"))
            file_contents = []

            for py_file in python_files[:10]:  # Check first 10 files for performance
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                        file_contents.append(content)
                except:
                    continue

            # Simple duplication detection
            duplicate_lines = 0
            total_lines = 0

            for content in file_contents:
                lines = content.split('\n')
                total_lines += len(lines)

                # Check for repeated import blocks, function signatures, etc.
                import_blocks = [line for line in lines if line.startswith('from ') or line.startswith('import ')]
                if len(import_blocks) > 20:  # Too many imports in one file
                    duplicate_lines += len(import_blocks) - 10

            if total_lines > 0:
                duplication_ratio = duplicate_lines / total_lines
                score -= min(50, duplication_ratio * 200)  # Scale deduction

        except:
            score -= 10  # Penalty for analysis failure

        return max(0, score)

    async def _check_documentation(self, service: ServiceInfo) -> float:
        """Check documentation quality."""
        score = 0.0

        try:
            python_files = list(service.path.rglob("*.py"))
            total_functions = 0
            documented_functions = 0

            for py_file in python_files[:5]:  # Check first 5 files
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()

                        # Count functions/methods
                        functions = len([line for line in content.split('\n') if line.strip().startswith('def ')])
                        total_functions += functions

                        # Count docstrings (triple quotes)
                        docstrings = content.count('"""') + content.count("'''")
                        documented_functions += min(functions, docstrings // 2)  # Each docstring covers ~2 quotes

                except:
                    continue

            if total_functions > 0:
                documentation_ratio = documented_functions / total_functions
                score += min(50, documentation_ratio * 100)

            # Check for README
            readme_files = list(service.path.glob("README*"))
            if readme_files:
                score += 30

            # Check for API documentation setup
            main_file = service.path / "main.py"
            if main_file.exists():
                with open(main_file, 'r') as f:
                    if 'docs_url' in f.read():
                        score += 20

        except:
            pass

        return min(100, score)

    async def _audit_performance(self, service: ServiceInfo) -> Dict[str, Any]:
        """Audit performance characteristics."""
        logger.info(f"Auditing performance for {service.name}")

        scores = {
            'runtime': await self._check_runtime_performance(service),
            'database': await self._check_database_performance(service),
            'resources': await self._check_resource_usage(service)
        }

        # Calculate weighted performance score
        performance_score = (
            scores['runtime'] * 0.40 +
            scores['database'] * 0.30 +
            scores['resources'] * 0.30
        )

        return {
            'score': round(performance_score, 2),
            'runtime': scores['runtime'],
            'database': scores['database'],
            'resources': scores['resources'],
            'issues': self._identify_performance_issues(scores),
            'recommendations': self._generate_performance_recommendations(scores)
        }

    async def _check_runtime_performance(self, service: ServiceInfo) -> float:
        """Check runtime performance indicators."""
        score = 100.0

        # Check for async/await usage (good for performance)
        async_usage = 0
        total_functions = 0

        try:
            python_files = list(service.path.rglob("*.py"))
            for py_file in python_files[:3]:  # Check first 3 files
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                        functions = [line for line in content.split('\n') if line.strip().startswith('def ') or line.strip().startswith('async def ')]
                        total_functions += len(functions)

                        async_functions = [line for line in content.split('\n') if line.strip().startswith('async def ')]
                        async_usage += len(async_functions)
                except:
                    continue

            if total_functions > 0:
                async_ratio = async_usage / total_functions
                score += min(20, async_ratio * 50)  # Bonus for async usage

        except:
            pass

        # Check for obvious performance anti-patterns
        try:
            main_file = service.path / "main.py"
            if main_file.exists():
                with open(main_file, 'r') as f:
                    content = f.read()

                    # Check for synchronous database calls in async functions
                    if 'await' in content and 'sqlite3.connect' in content:
                        score -= 15  # Using sync DB in async context

                    # Check for proper error handling
                    if 'try:' in content and 'except:' in content:
                        score += 10

        except:
            pass

        return max(0, min(100, score))

    async def _check_database_performance(self, service: ServiceInfo) -> float:
        """Check database performance indicators."""
        score = 100.0

        # Check for database-related files
        db_files = list(service.path.glob("**/db/**/*.py")) + list(service.path.glob("**/database/**/*.py"))

        if db_files:
            score += 20  # Has database layer
        else:
            score -= 30  # No database layer found

        # Check for connection pooling
        try:
            for db_file in db_files[:2]:  # Check first 2 files
                with open(db_file, 'r') as f:
                    content = f.read()
                    if 'pool' in content.lower() or 'aiosqlite' in content:
                        score += 25  # Good async database usage
                        break
        except:
            pass

        # Check for SQL injection prevention
        try:
            python_files = list(service.path.rglob("*.py"))
            for py_file in python_files[:3]:
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                        if '%' in content and 'execute' in content:
                            score -= 20  # Potential SQL injection
                        if 'validate_sql_identifier' in content:
                            score += 15  # SQL injection prevention
                except:
                    continue
        except:
            pass

        return max(0, min(100, score))

    async def _check_resource_usage(self, service: ServiceInfo) -> float:
        """Check resource usage patterns."""
        score = 100.0

        # Check for proper resource management
        try:
            python_files = list(service.path.rglob("*.py"))
            resource_management = 0
            total_files = 0

            for py_file in python_files[:5]:  # Check first 5 files
                try:
                    total_files += 1
                    with open(py_file, 'r') as f:
                        content = f.read()

                        # Check for context managers
                        if 'with ' in content:
                            resource_management += 1

                        # Check for proper cleanup
                        if 'close()' in content or 'cleanup' in content:
                            resource_management += 1

                        # Check for async resource management
                        if 'async with' in content:
                            resource_management += 1

                except:
                    continue

            if total_files > 0:
                resource_score = (resource_management / total_files) * 30
                score += min(30, resource_score)

        except:
            pass

        # Check for memory management
        try:
            main_file = service.path / "main.py"
            if main_file.exists():
                with open(main_file, 'r') as f:
                    content = f.read()
                    if 'ThreadPoolExecutor' in content or 'ProcessPoolExecutor' in content:
                        score += 15  # Good resource pooling
        except:
            pass

        return max(0, min(100, score))

    async def _audit_maintainability(self, service: ServiceInfo) -> Dict[str, Any]:
        """Audit maintainability factors."""
        logger.info(f"Auditing maintainability for {service.name}")

        scores = {
            'organization': await self._check_organization(service),
            'error_handling': await self._check_error_handling(service),
            'scalability': await self._check_scalability(service),
            'devops': await self._check_devops_readiness(service)
        }

        # Calculate weighted maintainability score
        maintainability_score = (
            scores['organization'] * 0.30 +
            scores['error_handling'] * 0.25 +
            scores['scalability'] * 0.25 +
            scores['devops'] * 0.20
        )

        return {
            'score': round(maintainability_score, 2),
            'organization': scores['organization'],
            'error_handling': scores['error_handling'],
            'scalability': scores['scalability'],
            'devops': scores['devops'],
            'issues': self._identify_maintainability_issues(scores),
            'recommendations': self._generate_maintainability_recommendations(scores)
        }

    async def _check_organization(self, service: ServiceInfo) -> float:
        """Check code organization quality."""
        score = 100.0

        # Check directory structure
        dirs = [d.name for d in service.path.iterdir() if d.is_dir()]

        # Penalize for too many directories at root level
        if len(dirs) > 10:
            score -= min(20, (len(dirs) - 10) * 2)

        # Reward for proper separation
        if 'domain' in dirs:
            score += 10
        if any(d in ['infrastructure', 'config'] for d in dirs):
            score += 10
        if any(d in ['api', 'routes'] for d in dirs):
            score += 10

        # Check for circular imports (basic check)
        try:
            python_files = list(service.path.rglob("*.py"))
            import_statements = []

            for py_file in python_files[:3]:
                try:
                    with open(py_file, 'r') as f:
                        lines = f.readlines()
                        for line in lines:
                            if line.strip().startswith('from ') and 'import' in line:
                                import_statements.append(line.strip())
                except:
                    continue

            # Simple circular import detection
            local_imports = [imp for imp in import_statements if 'services.' in imp]
            if len(local_imports) > 5:
                score -= min(15, len(local_imports) - 5)

        except:
            pass

        return max(0, min(100, score))

    async def _check_error_handling(self, service: ServiceInfo) -> float:
        """Check error handling quality."""
        score = 0.0

        try:
            python_files = list(service.path.rglob("*.py"))
            error_handling_score = 0
            total_files = 0

            for py_file in python_files[:5]:  # Check first 5 files
                try:
                    total_files += 1
                    with open(py_file, 'r') as f:
                        content = f.read()

                        # Check for try/except blocks
                        if 'try:' in content and 'except' in content:
                            error_handling_score += 1

                        # Check for specific exception types
                        if 'ValueError' in content or 'HTTPException' in content:
                            error_handling_score += 1

                        # Check for logging in error handling
                        if 'logger.' in content and 'except' in content:
                            error_handling_score += 1

                        # Check for custom exceptions
                        if 'class' in content and 'Exception' in content:
                            error_handling_score += 1

                except:
                    continue

            if total_files > 0:
                avg_error_handling = error_handling_score / total_files
                score += min(60, avg_error_handling * 20)

            # Check for global error handling
            main_file = service.path / "main.py"
            if main_file.exists():
                with open(main_file, 'r') as f:
                    content = f.read()
                    if '@app.exception_handler' in content:
                        score += 40  # Good global error handling

        except:
            pass

        return min(100, score)

    async def _check_scalability(self, service: ServiceInfo) -> float:
        """Check scalability readiness."""
        score = 100.0

        # Check for stateless design indicators
        try:
            python_files = list(service.path.rglob("*.py"))
            stateless_indicators = 0
            total_checks = 0

            for py_file in python_files[:3]:
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                        total_checks += 1

                        # Check for async/await (good for scalability)
                        if 'async def' in content:
                            stateless_indicators += 1

                        # Check for database connection pooling
                        if 'pool' in content.lower():
                            stateless_indicators += 1

                        # Check for caching
                        if 'cache' in content.lower() or 'redis' in content.lower():
                            stateless_indicators += 1

                        # Check for proper resource cleanup
                        if 'async with' in content or 'with ' in content:
                            stateless_indicators += 1

                except:
                    continue

            if total_checks > 0:
                scalability_ratio = stateless_indicators / total_checks
                score += min(20, scalability_ratio * 40)

        except:
            pass

        # Check for Docker configuration
        docker_files = list(service.path.glob("Dockerfile*")) + list(service.path.glob("docker-compose*.yml"))
        if docker_files:
            score += 15

        # Check for Kubernetes manifests
        k8s_files = list(service.path.glob("**/*.yaml")) + list(service.path.glob("**/*.yml"))
        k8s_indicators = ['kind: Deployment', 'kind: Service', 'apiVersion: v1']
        has_k8s = any(
            any(indicator in (open(f).read() if f.exists() else '') for indicator in k8s_indicators)
            for f in k8s_files[:2]
        )
        if has_k8s:
            score += 15

        return max(0, min(100, score))

    async def _check_devops_readiness(self, service: ServiceInfo) -> float:
        """Check DevOps and deployment readiness."""
        score = 0.0

        # Check for CI/CD
        ci_files = list(service.path.glob(".github/workflows/*.yml")) + list(service.path.glob(".gitlab-ci.yml"))
        if ci_files:
            score += 25

        # Check for Docker
        docker_files = list(service.path.glob("Dockerfile*"))
        if docker_files:
            score += 20

        # Check for configuration management
        config_files = list(service.path.glob("config*")) + list(service.path.glob("*.yaml")) + list(service.path.glob("*.yml"))
        if config_files:
            score += 15

        # Check for health checks
        try:
            main_file = service.path / "main.py"
            if main_file.exists():
                with open(main_file, 'r') as f:
                    content = f.read()
                    if '/health' in content:
                        score += 15
        except:
            pass

        # Check for logging configuration
        try:
            python_files = list(service.path.rglob("*.py"))
            for py_file in python_files[:2]:
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                        if 'logging' in content and 'basicConfig' in content:
                            score += 15
                            break
                except:
                    continue
        except:
            pass

        # Check for monitoring
        try:
            python_files = list(service.path.rglob("*.py"))
            for py_file in python_files[:2]:
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                        if 'metrics' in content or 'prometheus' in content.lower():
                            score += 10
                            break
                except:
                    continue
        except:
            pass

        return min(100, score)

    def _calculate_overall_score(self, results: AuditResults) -> float:
        """Calculate overall service score."""
        architecture_score = results.architecture.get('score', 0)
        code_quality_score = results.code_quality.get('score', 0)
        performance_score = results.performance.get('score', 0)
        maintainability_score = results.maintainability.get('score', 0)

        overall_score = (
            architecture_score * self.DIMENSION_WEIGHTS['architecture'] +
            code_quality_score * self.DIMENSION_WEIGHTS['code_quality'] +
            performance_score * self.DIMENSION_WEIGHTS['performance'] +
            maintainability_score * self.DIMENSION_WEIGHTS['maintainability']
        )

        return round(overall_score, 2)

    def _calculate_grade(self, score: float) -> str:
        """Calculate grade based on score."""
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "A-"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 65:
            return "B-"
        elif score >= 60:
            return "C+"
        elif score >= 55:
            return "C"
        elif score >= 50:
            return "C-"
        else:
            return "D"

    def _identify_critical_issues(self, results: AuditResults) -> List[Dict[str, Any]]:
        """Identify critical issues requiring immediate attention."""
        critical_issues = []

        # Check for very low scores
        if results.architecture.get('score', 0) < 50:
            critical_issues.append({
                'dimension': 'architecture',
                'issue': 'Critical architecture violations',
                'severity': 'critical',
                'description': 'Architecture score below 50 - fundamental design issues'
            })

        if results.code_quality.get('testing', 0) < 30:
            critical_issues.append({
                'dimension': 'testing',
                'issue': 'Inadequate test coverage',
                'severity': 'critical',
                'description': 'Testing score below 30 - high risk of undetected bugs'
            })

        if results.maintainability.get('error_handling', 0) < 40:
            critical_issues.append({
                'dimension': 'error_handling',
                'issue': 'Poor error handling',
                'severity': 'critical',
                'description': 'Error handling score below 40 - unreliable service'
            })

        return critical_issues

    def _generate_recommendations(self, results: AuditResults) -> List[Dict[str, Any]]:
        """Generate prioritized improvement recommendations."""
        recommendations = []

        # Architecture recommendations
        if results.architecture.get('ddd_compliance', 0) < 70:
            recommendations.append({
                'dimension': 'architecture',
                'priority': 'high',
                'title': 'Implement Domain-Driven Design patterns',
                'description': 'Adopt DDD principles with proper entity, value object, and service separation',
                'effort_days': 8,
                'impact': 'high'
            })

        if results.architecture.get('rest_compliance', 0) < 70:
            recommendations.append({
                'dimension': 'architecture',
                'priority': 'high',
                'title': 'Standardize REST API design',
                'description': 'Implement proper HTTP methods, status codes, and resource naming',
                'effort_days': 5,
                'impact': 'high'
            })

        # Code quality recommendations
        if results.code_quality.get('testing', 0) < 60:
            recommendations.append({
                'dimension': 'code_quality',
                'priority': 'high',
                'title': 'Increase test coverage',
                'description': 'Add comprehensive unit and integration tests',
                'effort_days': 10,
                'impact': 'high'
            })

        if results.code_quality.get('complexity', 0) < 70:
            recommendations.append({
                'dimension': 'code_quality',
                'priority': 'medium',
                'title': 'Reduce code complexity',
                'description': 'Refactor complex functions and improve code organization',
                'effort_days': 6,
                'impact': 'medium'
            })

        # Performance recommendations
        if results.performance.get('database', 0) < 70:
            recommendations.append({
                'dimension': 'performance',
                'priority': 'medium',
                'title': 'Optimize database performance',
                'description': 'Implement connection pooling and query optimization',
                'effort_days': 4,
                'impact': 'high'
            })

        # Maintainability recommendations
        if results.maintainability.get('error_handling', 0) < 60:
            recommendations.append({
                'dimension': 'maintainability',
                'priority': 'high',
                'title': 'Improve error handling',
                'description': 'Implement comprehensive exception handling and logging',
                'effort_days': 3,
                'impact': 'high'
            })

        if results.maintainability.get('devops', 0) < 60:
            recommendations.append({
                'dimension': 'maintainability',
                'priority': 'medium',
                'title': 'Enhance DevOps readiness',
                'description': 'Add Docker, CI/CD, and monitoring configuration',
                'effort_days': 7,
                'impact': 'medium'
            })

        return recommendations

    def _estimate_effort(self, results: AuditResults) -> float:
        """Estimate total effort for all recommendations."""
        recommendations = results.priority_improvements
        total_effort = sum(rec.get('effort_days', 0) for rec in recommendations)
        return round(total_effort, 1)

    # Placeholder methods for issue identification (would be more comprehensive in real implementation)
    def _identify_architecture_issues(self, scores: Dict[str, float]) -> List[str]:
        issues = []
        if scores.get('ddd_compliance', 0) < 60:
            issues.append("Low DDD compliance - consider implementing domain patterns")
        if scores.get('rest_compliance', 0) < 60:
            issues.append("REST API design issues - review HTTP methods and status codes")
        return issues

    def _generate_architecture_recommendations(self, scores: Dict[str, float]) -> List[str]:
        recommendations = []
        if scores.get('ddd_compliance', 0) < 70:
            recommendations.append("Adopt DDD patterns: entities, value objects, domain services")
        if scores.get('layer_separation', 0) < 70:
            recommendations.append("Improve layer separation: presentation, application, domain, infrastructure")
        return recommendations

    def _identify_code_quality_issues(self, scores: Dict[str, float]) -> List[str]:
        issues = []
        if scores.get('testing', 0) < 50:
            issues.append("Insufficient test coverage - aim for >90% coverage")
        if scores.get('complexity', 0) < 60:
            issues.append("High code complexity - refactor large functions")
        return issues

    def _generate_code_quality_recommendations(self, scores: Dict[str, float]) -> List[str]:
        recommendations = []
        if scores.get('testing', 0) < 70:
            recommendations.append("Add comprehensive test suite with unit and integration tests")
        if scores.get('documentation', 0) < 60:
            recommendations.append("Improve documentation with docstrings and API docs")
        return recommendations

    def _identify_performance_issues(self, scores: Dict[str, float]) -> List[str]:
        issues = []
        if scores.get('database', 0) < 60:
            issues.append("Database performance issues - implement connection pooling")
        if scores.get('runtime', 0) < 70:
            issues.append("Runtime performance concerns - review async patterns")
        return issues

    def _generate_performance_recommendations(self, scores: Dict[str, float]) -> List[str]:
        recommendations = []
        if scores.get('database', 0) < 70:
            recommendations.append("Optimize database queries and implement connection pooling")
        if scores.get('resources', 0) < 70:
            recommendations.append("Improve resource management with proper cleanup")
        return recommendations

    def _identify_maintainability_issues(self, scores: Dict[str, float]) -> List[str]:
        issues = []
        if scores.get('error_handling', 0) < 50:
            issues.append("Poor error handling - implement comprehensive exception management")
        if scores.get('scalability', 0) < 60:
            issues.append("Scalability concerns - review async patterns and resource management")
        return issues

    def _generate_maintainability_recommendations(self, scores: Dict[str, float]) -> List[str]:
        recommendations = []
        if scores.get('organization', 0) < 70:
            recommendations.append("Improve code organization with clear module boundaries")
        if scores.get('devops', 0) < 70:
            recommendations.append("Enhance DevOps readiness with Docker and CI/CD")
        return recommendations

    def generate_report(self, results: AuditResults, output_format: str = 'json') -> str:
        """Generate audit report in specified format."""
        if output_format == 'json':
            return json.dumps({
                'service_name': results.service_name,
                'audit_date': results.audit_date,
                'overall_score': results.overall_score,
                'grade': results.grade,
                'dimensions': {
                    'architecture': results.architecture,
                    'code_quality': results.code_quality,
                    'performance': results.performance,
                    'maintainability': results.maintainability
                },
                'critical_issues': results.critical_issues,
                'priority_improvements': results.priority_improvements,
                'estimated_effort_days': results.estimated_effort_days
            }, indent=2)

        elif output_format == 'markdown':
            return self._generate_markdown_report(results)

        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _generate_markdown_report(self, results: AuditResults) -> str:
        """Generate markdown audit report."""
        report = f"""# Service Audit Report: {results.service_name}

**Audit Date:** {results.audit_date}
**Overall Score:** {results.overall_score}/100 ({results.grade})

## 📊 Score Breakdown

| Dimension | Score | Weight | Contribution |
|-----------|-------|--------|--------------|
| Architecture | {results.architecture.get('score', 0)} | 30% | {(results.architecture.get('score', 0) * 0.3):.1f} |
| Code Quality | {results.code_quality.get('score', 0)} | 25% | {(results.code_quality.get('score', 0) * 0.25):.1f} |
| Performance | {results.performance.get('score', 0)} | 20% | {(results.performance.get('score', 0) * 0.2):.1f} |
| Maintainability | {results.maintainability.get('score', 0)} | 25% | {(results.maintainability.get('score', 0) * 0.25):.1f} |

## 🚨 Critical Issues

"""

        if results.critical_issues:
            for issue in results.critical_issues:
                report += f"- **{issue['issue']}**: {issue['description']}\n"
        else:
            report += "No critical issues identified.\n"

        report += f"""

## 🎯 Priority Improvements

**Estimated Total Effort: {results.estimated_effort_days} days**

"""

        for rec in results.priority_improvements:
            report += f"### {rec['priority'].title()}: {rec['title']}\n"
            report += f"- **Effort:** {rec['effort_days']} days\n"
            report += f"- **Impact:** {rec['impact']}\n"
            report += f"- **Description:** {rec['description']}\n\n"

        return report


async def main():
    """Main entry point for audit framework."""
    import argparse

    parser = argparse.ArgumentParser(description='Comprehensive Service Audit Framework')
    parser.add_argument('command', choices=['audit', 'compare', 'trend'], help='Audit command')
    parser.add_argument('--service', help='Service name to audit')
    parser.add_argument('--services', help='Comma-separated service names for comparison')
    parser.add_argument('--output', choices=['json', 'markdown'], default='json', help='Output format')
    parser.add_argument('--period', default='6months', help='Trend analysis period')

    args = parser.parse_args()

    # Initialize framework
    project_root = Path(__file__).parent.parent.parent
    framework = AuditFramework(project_root)

    try:
        if args.command == 'audit':
            if not args.service:
                logger.error("Service name required for audit command")
                return 1

            logger.info(f"Starting audit for service: {args.service}")
            results = await framework.audit_service(args.service)
            report = framework.generate_report(results, args.output)

            if args.output == 'json':
                print(report)
            else:
                print(report)

        elif args.command == 'compare':
            if not args.services:
                logger.error("Service names required for compare command")
                return 1

            services = [s.strip() for s in args.services.split(',')]
            logger.info(f"Comparing services: {services}")

            # Audit all services
            all_results = []
            for service in services:
                try:
                    results = await framework.audit_service(service)
                    all_results.append(results)
                except Exception as e:
                    logger.error(f"Failed to audit {service}: {e}")

            # Generate comparison report
            comparison = {
                'audit_date': datetime.utcnow().isoformat(),
                'services_compared': len(all_results),
                'results': [
                    {
                        'service': r.service_name,
                        'overall_score': r.overall_score,
                        'grade': r.grade,
                        'critical_issues': len(r.critical_issues)
                    } for r in all_results
                ]
            }

            print(json.dumps(comparison, indent=2))

        elif args.command == 'trend':
            logger.info("Trend analysis not yet implemented")
            print("Trend analysis feature coming soon")

    except Exception as e:
        logger.error(f"Audit failed: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
