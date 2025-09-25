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
import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

# Enhanced analysis libraries
try:
    import radon.complexity as radon_complexity
    import radon.metrics as radon_metrics
    HAS_RADON = True
except ImportError:
    HAS_RADON = False

try:
    import bandit
    HAS_BANDIT = True
except ImportError:
    HAS_BANDIT = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Enhanced reporting libraries
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    Console = None
    Progress = None

# Coverage and testing libraries
try:
    import coverage
    HAS_COVERAGE = True
except ImportError:
    HAS_COVERAGE = False

try:
    import interrogate
    HAS_INTERROGATE = True
except ImportError:
    HAS_INTERROGATE = False

try:
    import mypy.api
    HAS_MYPY = True
except ImportError:
    HAS_MYPY = False

try:
    import pylint.lint
    HAS_PYLINt = True
except ImportError:
    HAS_PYLINt = False

try:
    import safety.cli
    HAS_SAFETY = True
except ImportError:
    HAS_SAFETY = False

try:
    import pydeps
    HAS_PYDEPS = True
except ImportError:
    HAS_PYDEPS = False

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

    async def audit_service(self, service_name: str, progress_callback=None) -> AuditResults:
        """Run comprehensive audit on a specific service with progress tracking."""
        services = self.discover_services()
        service_info = next((s for s in services if s.name == service_name), None)

        if not service_info:
            raise ValueError(f"Service '{service_name}' not found")

        logger.info(f"Starting comprehensive audit for service: {service_name}")

        results = AuditResults(service_name=service_name)

        # Run all audit dimensions with progress updates
        audit_steps = [
            ("architecture", "Analyzing architecture patterns"),
            ("code_quality", "Assessing code quality metrics"),
            ("performance", "Evaluating performance characteristics"),
            ("maintainability", "Checking maintainability factors")
        ]

        for dimension, description in audit_steps:
            if progress_callback:
                progress_callback(description)

            if dimension == "architecture":
                results.architecture = await self._audit_architecture(service_info)
            elif dimension == "code_quality":
                results.code_quality = await self._audit_code_quality(service_info)
            elif dimension == "performance":
                results.performance = await self._audit_performance(service_info)
            elif dimension == "maintainability":
                results.maintainability = await self._audit_maintainability(service_info)

        # Calculate overall score
        results.overall_score = self._calculate_overall_score(results)
        results.grade = self._calculate_grade(results.overall_score)

        # Generate issues and recommendations
        results.critical_issues = self._identify_critical_issues(results)
        results.priority_improvements = self._generate_recommendations(results)
        results.estimated_effort_days = self._estimate_effort(results)

        logger.info(f"Audit completed for service {service_name}: Score {results.overall_score:.2f} ({results.grade})")
        return results

    async def _audit_architecture(self, service: ServiceInfo) -> Dict[str, Any]:
        """Audit architectural compliance with DDD structure analysis."""
        logger.info(f"Auditing architecture for {service.name}")

        # Initialize analysis storage
        self._ddd_issues = []
        self._ddd_recommendations = []
        self._file_metrics = {}

        # Analyze test quality
        test_quality_results = await self._analyze_test_quality(service)

        # Analyze linting quality
        linting_results = await self._analyze_linting_quality(service)

        # Analyze endpoints for REST compliance
        endpoint_results = self._analyze_endpoints_for_rest_compliance(service)

        # New enhanced analyses
        complexity_results = self._analyze_cyclomatic_complexity(service)
        coupling_results = self._analyze_dependency_coupling(service)
        dead_code_results = self._analyze_dead_code(service)
        test_quality_metrics = self._analyze_test_quality_metrics(service)
        domain_boundaries = self._analyze_domain_boundaries(service)
        api_docs_quality = self._analyze_api_documentation_quality(service)
        code_documentation = self._analyze_code_documentation(service)
        config_management = self._analyze_configuration_management(service)
        logging_practices = self._analyze_logging_practices(service)

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
            'ddd_issues': getattr(self, '_ddd_issues', []),
            'ddd_recommendations': getattr(self, '_ddd_recommendations', []),
            'file_metrics': getattr(self, '_file_metrics', {}),
            'test_quality': test_quality_results,
            'linting_quality': linting_results,
            'endpoint_analysis': endpoint_results,
            'complexity_analysis': complexity_results,
            'dependency_coupling': coupling_results,
            'dead_code_analysis': dead_code_results,
            'test_quality_metrics': test_quality_metrics,
            'domain_boundaries': domain_boundaries,
            'api_documentation': api_docs_quality,
            'code_documentation': code_documentation,
            'configuration_management': config_management,
            'logging_practices': logging_practices,
            'issues': self._identify_architecture_issues(scores),
            'recommendations': self._generate_architecture_recommendations(scores)
        }

    async def _check_ddd_compliance(self, service: ServiceInfo) -> float:
        """Check Domain-Driven Design compliance with comprehensive analysis."""
        score = 0.0
        total_checks = 0

        # 1. Directory Structure Analysis (30 points)
        structure_score = await self._analyze_directory_structure(service)
        score += structure_score
        total_checks += 30

        # 2. Domain Layer Structure & Quality (25 points)
        domain_score = await self._analyze_domain_layer_quality(service)
        score += domain_score
        total_checks += 25

        # 3. Application Layer Architecture (20 points)
        app_score = await self._analyze_application_layer_architecture(service)
        score += app_score
        total_checks += 20

        # 4. Clean Architecture Compliance (25 points)
        architecture_score = await self._analyze_clean_architecture_compliance(service)
        score += architecture_score
        total_checks += 25

        return min(100, (score / max(1, total_checks)) * 100)

    async def _analyze_directory_structure(self, service: ServiceInfo) -> float:
        """Analyze directory structure for DDD compliance and identify refactoring needs."""
        score = 0.0
        issues_found = []
        recommendations = []

        # Count files and analyze structure
        total_files = 0
        monolithic_files = []
        directory_file_counts = {}
        large_directories = []

        # Get all directories and count files
        all_dirs = []
        for root, dirs, files in os.walk(str(service.path)):
            for dir_name in dirs:
                if not dir_name.startswith('.') and dir_name not in ['__pycache__', 'tests', '.git']:
                    full_path = Path(root) / dir_name
                    rel_path = full_path.relative_to(service.path)
                    all_dirs.append(str(rel_path))

            # Count files in this directory
            dir_path = Path(root).relative_to(service.path)
            dir_files = [f for f in files if not f.startswith('.') and f.endswith('.py')]
            if dir_files:
                directory_file_counts[str(dir_path)] = len(dir_files)
                total_files += len(dir_files)

                # Check for large directories (too many files in one directory)
                if len(dir_files) > 15:  # More than 15 files in one directory
                    large_directories.append(f"{dir_path} ({len(dir_files)} files)")
                elif len(dir_files) > 10:  # More than 10 files in one directory
                    score -= 0.2  # Minor penalty

            # Check for monolithic files
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = len(f.readlines())
                            if lines > 500:  # Files over 500 lines may need refactoring
                                monolithic_files.append(f"{file_path.relative_to(service.path)} ({lines} lines)")
                                score -= 0.5  # Penalty for each monolithic file
                    except:
                        continue

        # Define comprehensive DDD+REST directory structure standards
        ddd_rest_standards = {
            'domain': {
                'description': 'Business logic layer - REST-agnostic core business rules',
                'required': ['entities', 'services', 'repositories'],
                'recommended': ['value_objects', 'exceptions', 'events', 'factories', 'validation'],
                'optional': ['aggregates', 'domain_services', 'specifications', 'commands', 'queries'],
                'forbidden': ['controllers', 'routes', 'middleware', 'models', 'config', 'cache',
                            'external_services', 'migrations', 'api', 'handlers', 'dto'],
                'forbidden_reason': 'HTTP/API concerns belong in presentation layer'
            },
            'application': {
                'description': 'Use case orchestration layer - coordinates domain logic',
                'required': ['handlers'],
                'recommended': ['services', 'dto', 'commands', 'queries', 'events', 'validators'],
                'optional': ['use_cases', 'cqrs', 'command_handlers', 'query_handlers'],
                'forbidden': ['entities', 'repositories', 'controllers', 'routes', 'config', 'cache',
                            'external_services', 'middleware', 'models'],
                'forbidden_reason': 'Infrastructure in infrastructure layer, HTTP concerns in presentation'
            },
            'infrastructure': {
                'description': 'External concerns layer - databases, external APIs, frameworks',
                'required': ['repositories'],
                'recommended': ['config', 'external_services', 'cache', 'events', 'connections'],
                'optional': ['migrations', 'logging', 'monitoring', 'database', 'clients'],
                'forbidden': ['entities', 'domain_services', 'controllers', 'handlers', 'dto',
                            'routes', 'middleware', 'models'],
                'forbidden_reason': 'Business logic in domain, HTTP concerns in presentation'
            },
            'presentation': {
                'description': 'HTTP/API layer - REST endpoints, request/response handling',
                'required': ['controllers'],
                'recommended': ['models', 'middleware', 'routes', 'api'],
                'optional': ['web', 'templates', 'responses', 'requests', 'schemas'],
                'forbidden': ['entities', 'repositories', 'domain_services', 'config', 'cache',
                            'external_services', 'migrations', 'handlers', 'dto'],
                'forbidden_reason': 'Business logic in domain/application, infrastructure concerns elsewhere'
            }
        }

        # Check for common anti-patterns in DDD+REST
        rest_antipatterns = {
            'api_at_root': {
                'pattern': lambda dirs: any('api' in d and len(d.split('/')) == 1 for d in dirs),
                'message': 'API directory at root level violates DDD - move to presentation layer',
                'penalty': 3
            },
            'routes_at_root': {
                'pattern': lambda dirs: any('routes' in d and len(d.split('/')) == 1 for d in dirs),
                'message': 'Routes directory at root level violates DDD - move to presentation/routes/',
                'penalty': 3
            },
            'controllers_mixed': {
                'pattern': lambda dirs: any('controllers' in d and not d.startswith('presentation/') for d in dirs),
                'message': 'Controllers outside presentation layer violate DDD separation',
                'penalty': 2
            },
            'business_logic_in_presentation': {
                'pattern': lambda dirs: any(layer in d for d in dirs
                                          for layer in ['domain/', 'application/']
                                          if any(http in d.lower() for http in ['api', 'routes', 'controllers'])),
                'message': 'Business logic mixed with HTTP concerns violates DDD',
                'penalty': 4
            }
        }

        # Check for layer separation (10 points)
        layer_score = 0
        layers_found = []
        for layer in ddd_rest_standards.keys():
            if any(layer in dir_path for dir_path in all_dirs):
                layers_found.append(layer)
                layer_score += 2.5  # 2.5 points per layer found

        if len(layers_found) >= 3:
            layer_score += 5  # Bonus for having at least 3 layers

        score += min(10, layer_score)

        # Check for DDD+REST anti-patterns
        antipattern_penalty = 0
        for antipattern_name, antipattern_config in rest_antipatterns.items():
            if antipattern_config['pattern'](all_dirs):
                issues_found.append(f"DDD+REST Anti-pattern: {antipattern_config['message']}")
                recommendations.append(f"Fix {antipattern_name}: {antipattern_config['message']}")
                antipattern_penalty += antipattern_config['penalty']
                score -= antipattern_config['penalty']

        if antipattern_penalty > 0:
            issues_found.append(f"Total DDD+REST anti-pattern penalties: -{antipattern_penalty} points")

        # Check domain layer structure (8 points)
        domain_dirs = [d for d in all_dirs if 'domain' in d.split('/')]
        domain_score = 0

        if domain_dirs:
            domain_score += 2  # Basic domain layer exists

            # Check for domain organization patterns
            # Pattern 1: Archetype-based (domain/entities, domain/services, domain/repositories)
            archetype_components = []
            for dir_path in domain_dirs:
                parts = dir_path.split('/')
                if len(parts) >= 2 and parts[0] == 'domain':
                    archetype_components.append(parts[1])

            # Pattern 2: Feature-based (domain/documents, domain/bulk, domain/lifecycle)
            feature_based = len([d for d in domain_dirs if len(d.split('/')) >= 2 and d.split('/')[1] not in ['entities', 'services', 'repositories', 'value_objects', 'exceptions', 'events', 'factories', 'validation', 'aggregates', 'domain_services', 'specifications']])

            # Score based on organization pattern
            if feature_based > 0:
                # Feature-based organization (DDD bounded contexts)
                domain_score += 3
                if len(domain_dirs) >= 3:
                    domain_score += 2  # Multiple bounded contexts
            else:
                # Traditional archetype-based organization
                required_found = sum(1 for required in ddd_rest_standards['domain']['required']
                                   if any(required in comp for comp in archetype_components))
                if required_found >= 2:
                    domain_score += 3
                elif required_found >= 1:
                    domain_score += 2

                # Check for missing required components only if using archetype pattern
                if required_found < 3:
                    for required in ddd_rest_standards['domain']['required']:
                        if not any(required in comp for comp in archetype_components):
                            issues_found.append(f"Missing required domain component: {required}")
                            recommendations.append(f"Create domain/{required}/ directory for domain logic")
                            score -= 1  # Penalty for missing required DDD component

            # Check for domain exceptions (always required)
            if not any('exception' in d.lower() for d in domain_dirs):
                issues_found.append("Missing domain exceptions")
                recommendations.append("Create domain/exceptions/ directory for domain-specific exceptions")
            else:
                domain_score += 1  # Has domain exceptions

        score += min(8, domain_score)

        # Check for anti-patterns and refactoring needs (7 points)
        anti_pattern_score = 7  # Start with perfect score, deduct for issues

        # Apply penalties for monolithic files (already counted above)
        if monolithic_files:
            issues_found.append(f"Large monolithic files detected: {', '.join([f.split(' ')[0] + ' (' + f.split('(')[1] for f in monolithic_files[:3]])}")
            recommendations.append("Break down large files (>500 lines) into smaller, focused modules")
            anti_pattern_score -= min(len(monolithic_files), 3)  # Max 3 point deduction

        # Apply penalties for large directories
        if large_directories:
            issues_found.append(f"Large directories detected: {', '.join(large_directories[:2])}")
            recommendations.append("Break down large directories (>15 files) into smaller subdirectories")
            anti_pattern_score -= min(len(large_directories), 2)  # Max 2 point deduction

        # Penalize for too many total files (service complexity)
        if total_files > 100:
            issues_found.append(f"High file count: {total_files} Python files (service may be too complex)")
            recommendations.append("Consider splitting large services into smaller microservices")
            score -= 2
        elif total_files > 50:
            score -= 1  # Minor penalty for moderately large services

        # Check for mixed concerns (business logic in infrastructure/presentation)
        mixed_concerns = []
        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(service.path)

                    # Check if infrastructure files contain domain logic
                    if 'infrastructure' in str(rel_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                domain_keywords = ['entity', 'aggregate', 'domain', 'business']
                                if any(keyword in content.lower() for keyword in domain_keywords):
                                    mixed_concerns.append(str(rel_path))
                                    anti_pattern_score -= 0.5
                        except:
                            continue

        if mixed_concerns:
            issues_found.append(f"Mixed concerns detected in infrastructure: {', '.join(mixed_concerns[:2])}")
            recommendations.append("Move domain logic out of infrastructure layer into domain layer")

        # Check for DDD architecture violations (8 points)
        ddd_violation_score = 8  # Start with perfect score, deduct for violations

        # Analyze Python modules that need DDD conversion
        modules_needing_ddd_conversion = []
        ddd_conversion_suggestions = []

        # Analyze file quality issues (large files, imports, linting)
        file_quality_issues = []
        large_files = []
        import_issues = []

        # Analyze each Python file for DDD conversion needs and quality issues
        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_') and not file.startswith('__'):
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(service.path)

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            lines = content.split('\n')

                            # Analyze file size
                            file_size = len(lines)
                            if file_size > 1000:
                                large_files.append(f"{rel_path} ({file_size} lines)")
                                score -= 2  # Major penalty for very large files
                            elif file_size > 500:
                                large_files.append(f"{rel_path} ({file_size} lines)")
                                score -= 1  # Penalty for large files

                            # Skip very small files for other analysis
                            if len(lines) < 10:
                                continue

                            # Analyze file for DDD conversion needs
                            conversion_needed, reasons = self._analyze_module_for_ddd_conversion(content, str(rel_path))

                            if conversion_needed:
                                modules_needing_ddd_conversion.append(str(rel_path))
                                ddd_conversion_suggestions.extend(reasons)

                            # Analyze import structure
                            import_problems = self._analyze_import_structure(content, str(rel_path))
                            if import_problems:
                                import_issues.extend(import_problems)
                                score -= min(len(import_problems) * 0.5, 2)  # Penalty for import issues

                    except Exception as e:
                        logger.debug(f"Error analyzing file {file_path}: {e}")
                        continue

        # Analyze test directories for DDD compliance
        test_directories_to_analyze = [
            Path("/Users/mykalthomas/Documents/work/Hackathon/tests"),
            Path("/Users/mykalthomas/Documents/work/Hackathon/tests/unit")
        ]

        tests_needing_ddd_reorganization = []
        test_ddd_suggestions = []

        for test_dir in test_directories_to_analyze:
            if test_dir.exists():
                for root, dirs, files in os.walk(str(test_dir)):
                    for file in files:
                        if file.startswith('test_') and file.endswith('.py'):
                            file_path = Path(root) / file
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()

                                # Analyze test file for DDD reorganization needs
                                reorganization_needed, reasons = self._analyze_test_for_ddd_reorganization(content, str(file_path), service.name)

                                if reorganization_needed:
                                    tests_needing_ddd_reorganization.append(str(file_path.relative_to(Path("/Users/mykalthomas/Documents/work/Hackathon"))))
                                    test_ddd_suggestions.extend(reasons)

                            except Exception as e:
                                logger.debug(f"Error analyzing test file {file_path}: {e}")
                                continue

        # Apply penalties for modules needing DDD conversion
        if modules_needing_ddd_conversion:
            # Penalty scales with number of modules needing conversion
            conversion_penalty = min(len(modules_needing_ddd_conversion) * 0.3, 4)  # Max 4 points
            ddd_violation_score -= conversion_penalty
            score -= conversion_penalty

            issues_found.append(f"Modules requiring DDD conversion: {len(modules_needing_ddd_conversion)} files need architectural refactoring")
            recommendations.extend(ddd_conversion_suggestions[:3])  # Limit to top 3 suggestions

        # Apply penalties for tests needing DDD reorganization
        if tests_needing_ddd_reorganization:
            # Penalty scales with number of test files needing reorganization
            test_reorg_penalty = min(len(tests_needing_ddd_reorganization) * 0.2, 3)  # Max 3 points
            ddd_violation_score -= test_reorg_penalty
            score -= test_reorg_penalty

            issues_found.append(f"Test files requiring DDD reorganization: {len(tests_needing_ddd_reorganization)} test files need structural changes")
            recommendations.extend(test_ddd_suggestions[:2])  # Limit to top 2 test suggestions

        # Report file quality issues
        if large_files:
            issues_found.append(f"Large files detected: {len(large_files)} files exceed recommended size")
            recommendations.extend([f"Break down {file} - too large for maintainability" for file in large_files[:2]])

        if import_issues:
            issues_found.append(f"Import structure issues: {len(import_issues)} files have problematic imports")
            recommendations.extend(import_issues[:2])

        # Analyze each directory for DDD violations
        directories_to_refactor = []
        refactoring_suggestions = []

        for root, dirs, files in os.walk(str(service.path)):
            for dir_name in dirs:
                if not dir_name.startswith('.') and dir_name not in ['__pycache__', 'tests', '.git']:
                    full_path = Path(root) / dir_name
                    rel_path = full_path.relative_to(service.path)
                    dir_parts = str(rel_path).split('/')

                    # Determine which layer this directory belongs to
                    layer = None
                    if 'domain' in dir_parts:
                        layer = 'domain'
                    elif 'application' in dir_parts:
                        layer = 'application'
                    elif 'infrastructure' in dir_parts:
                        layer = 'infrastructure'
                    elif 'presentation' in dir_parts or 'api' in dir_parts or 'controllers' in dir_parts:
                        layer = 'presentation'

                    if layer and layer in ddd_rest_standards:
                        standards = ddd_rest_standards[layer]

                        # Check for forbidden components in this layer
                        for forbidden in standards['forbidden']:
                            if forbidden in dir_parts[-1].lower():
                                directories_to_refactor.append(str(rel_path))
                                forbidden_reason = standards.get('forbidden_reason', f'forbidden in {layer} layer')
                                refactoring_suggestions.append(
                                    f"Move {rel_path} - {forbidden_reason}"
                                )
                                ddd_violation_score -= 1
                                score -= 1  # Overall penalty for DDD violation

                        # Check for missing required components
                        if dir_parts[-1] == layer:  # Root layer directory
                            missing_required = []
                            for required in standards['required']:
                                if not any(required in d for d in dir_parts):
                                    # Check if required subdirectories exist
                                    layer_root = Path(root) / dir_name
                                    if layer_root.exists():
                                        subdirs = [d.name.lower() for d in layer_root.iterdir() if d.is_dir()]
                                        if not any(required in subdir for subdir in subdirs):
                                            missing_required.append(required)

                            if missing_required:
                                for missing in missing_required:
                                    refactoring_suggestions.append(
                                        f"Create {layer}/{missing}/ directory - required for {standards['description']}"
                                    )
                                ddd_violation_score -= 0.5 * len(missing_required)

        # Add DDD violation findings
        if directories_to_refactor:
            issues_found.append(f"DDD architecture violations in directories: {', '.join(directories_to_refactor[:3])}")
            if len(directories_to_refactor) > 3:
                issues_found.append(f"... and {len(directories_to_refactor) - 3} more directories")

        # Add specific refactoring suggestions
        if refactoring_suggestions:
            recommendations.extend(refactoring_suggestions[:5])  # Limit to top 5 suggestions
            if len(refactoring_suggestions) > 5:
                recommendations.append(f"... and {len(refactoring_suggestions) - 5} more refactoring suggestions")

        score += min(8, ddd_violation_score)

        # Check for proper module organization (5 points)
        module_score = 0

        # Check for __init__.py files in directories
        init_files_missing = []
        for dir_path in all_dirs:
            full_dir = service.path / dir_path
            if not (full_dir / '__init__.py').exists():
                # Only flag missing __init__.py for non-trivial directories
                py_files = list(full_dir.glob('*.py'))
                if len(py_files) > 2:  # More than 2 Python files
                    init_files_missing.append(dir_path)
                    module_score -= 0.5

        if init_files_missing:
            issues_found.append(f"Missing __init__.py files in: {', '.join(init_files_missing[:3])}")
            recommendations.append("Add __init__.py files to Python packages for proper module structure")

        module_score = max(0, 5 + module_score)  # Convert negative deductions to positive score
        score += module_score

        # Store issues and recommendations for reporting
        if hasattr(self, '_ddd_issues'):
            self._ddd_issues.extend(issues_found)
        else:
            self._ddd_issues = issues_found

        if hasattr(self, '_ddd_recommendations'):
            self._ddd_recommendations.extend(recommendations)
        else:
            self._ddd_recommendations = recommendations

        # Store file metrics for overall scoring
        if hasattr(self, '_file_metrics'):
            self._file_metrics.update({
                'total_files': total_files,
                'monolithic_files_count': len(monolithic_files),
                'large_directories_count': len(large_directories),
                'directory_file_counts': directory_file_counts
            })
        else:
            self._file_metrics = {
                'total_files': total_files,
                'monolithic_files_count': len(monolithic_files),
                'large_directories_count': len(large_directories),
                'directory_file_counts': directory_file_counts
            }

        return min(30, score)

    def _analyze_module_for_ddd_conversion(self, content: str, file_path: str) -> tuple[bool, List[str]]:
        """Analyze a Python module to determine if it needs DDD conversion."""
        conversion_needed = False
        reasons = []

        lines = content.split('\n')
        file_size = len(lines)

        # Define patterns that indicate mixed concerns
        patterns = {
            'business_logic': [
                r'class.*Entity|class.*Model|class.*Aggregate',
                r'def.*business|def.*domain|def.*logic',
                r'def.*validate.*business|def.*check.*rule',
                r'@property|@staticmethod|@classmethod',
                r'def.*calculate|def.*compute|def.*process'
            ],
            'data_access': [
                r'import.*sqlite|from.*sqlite',
                r'import.*sqlalchemy|from.*sqlalchemy',
                r'import.*redis|from.*redis',
                r'def.*save|def.*update|def.*delete|def.*insert',
                r'def.*query|def.*select|def.*fetch',
                r'def.*connect|def.*session|def.*cursor'
            ],
            'external_services': [
                r'import.*requests|from.*requests',
                r'import.*httpx|from.*httpx',
                r'import.*aiohttp|from.*aiohttp',
                r'def.*api|def.*http|def.*call.*service',
                r'def.*send.*request|def.*get.*response'
            ],
            'presentation': [
                r'import.*fastapi|from.*fastapi',
                r'import.*flask|from.*flask',
                r'@app\.|@router\.|@get|@post|@put|@delete',
                r'def.*endpoint|def.*handler|def.*route',
                r'class.*Controller|class.*View'
            ],
            'infrastructure': [
                r'import.*logging|from.*logging',
                r'import.*config|from.*config',
                r'import.*os\.environ|getenv',
                r'def.*setup|def.*initialize|def.*configure',
                r'class.*Service|class.*Client|class.*Manager'
            ]
        }

        # Count concerns in the file
        concerns_found = {}
        for concern_type, patterns_list in patterns.items():
            concern_count = 0
            for pattern in patterns_list:
                if re.search(pattern, content, re.IGNORECASE):
                    concern_count += 1
            if concern_count > 0:
                concerns_found[concern_type] = concern_count

        # Determine if conversion is needed
        concern_types = list(concerns_found.keys())

        # Rule 1: Files with multiple concerns (3+ different types)
        if len(concern_types) >= 3:
            conversion_needed = True
            mixed_concerns = ', '.join(concern_types)
            reasons.append(f"Split {file_path} - contains {len(concern_types)} concerns ({mixed_concerns}) into separate layers")

        # Rule 2: Very large files (should be split regardless of concerns)
        if file_size > 800:
            conversion_needed = True
            reasons.append(f"Break down {file_path} ({file_size} lines) into smaller, focused modules following DDD")

        # Rule 3: Files mixing domain logic with infrastructure
        if ('business_logic' in concerns_found and
            ('data_access' in concerns_found or 'external_services' in concerns_found)):
            conversion_needed = True
            reasons.append(f"Separate domain logic from infrastructure in {file_path} - move business logic to domain layer")

        # Rule 4: Files mixing presentation with business logic
        if ('business_logic' in concerns_found and 'presentation' in concerns_found):
            conversion_needed = True
            reasons.append(f"Separate presentation from domain logic in {file_path} - create dedicated controllers")

        # Rule 5: Monolithic service classes that should be split
        if ('business_logic' in concerns_found and file_size > 400 and
            re.search(r'class.*Service.*:', content, re.IGNORECASE)):
            conversion_needed = True
            reasons.append(f"Split monolithic service class in {file_path} into domain services and application handlers")

        # Rule 6: Files with too many responsibilities (multiple large functions/classes)
        class_count = len(re.findall(r'^class\s+\w+', content, re.MULTILINE))
        function_count = len(re.findall(r'^def\s+\w+', content, re.MULTILINE))

        if class_count > 5 or function_count > 15:
            conversion_needed = True
            reasons.append(f"Reduce complexity in {file_path} - {class_count} classes, {function_count} functions should be split into focused modules")

        # Rule 7: Files that should be repositories but contain business logic
        if ('data_access' in concerns_found and 'business_logic' in concerns_found and
            'Repository' in content):
            conversion_needed = True
            reasons.append(f"Extract business logic from repository in {file_path} - repositories should only handle data access")

        return conversion_needed, reasons

    def _analyze_test_for_ddd_reorganization(self, content: str, file_path: str, service_name: str) -> tuple[bool, List[str]]:
        """Analyze a test file to determine if it needs DDD reorganization."""
        reorganization_needed = False
        reasons = []

        lines = content.split('\n')

        # Check if test file is in wrong location (should be in service-specific tests)
        expected_test_path = f"services/{service_name}/tests"
        if expected_test_path not in file_path:
            reorganization_needed = True
            reasons.append(f"Move {file_path} to {expected_test_path}/ to follow DDD service boundaries")

        # Analyze test structure for DDD compliance
        imports = []
        test_classes = []
        test_functions = []

        for line in lines:
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)
            elif line.startswith('class Test') or line.startswith('def test_'):
                if line.startswith('class '):
                    test_classes.append(line)
                elif line.startswith('def '):
                    test_functions.append(line)

        # Rule 1: Tests should be organized by layer (unit/integration/e2e)
        if 'unit' not in file_path and 'integration' not in file_path and 'e2e' not in file_path:
            reorganization_needed = True
            reasons.append(f"Organize {file_path} into unit/integration/e2e test categories following DDD testing structure")

        # Rule 2: Test files should follow naming conventions
        if not any(keyword in file_path.lower() for keyword in ['unit', 'integration', 'e2e', 'test_']):
            reorganization_needed = True
            reasons.append(f"Rename test file to follow DDD naming: test_[layer]_[component].py")

        # Rule 3: Large test files should be split by domain/component
        if len(test_functions) > 20 or len(lines) > 300:
            reorganization_needed = True
            reasons.append(f"Split large test file {file_path} by domain components or test types")

        # Rule 4: Tests should be co-located with the code they test
        if f"services/{service_name}" not in file_path:
            reorganization_needed = True
            reasons.append(f"Move tests to services/{service_name}/tests/ to follow DDD service boundaries")

        return reorganization_needed, reasons

    def _analyze_import_structure(self, content: str, file_path: str) -> List[str]:
        """Analyze import structure for quality issues."""
        issues = []
        lines = content.split('\n')

        # Track import patterns
        imports = []
        from_imports = []
        wildcard_imports = []
        relative_imports = []
        unused_likely = []

        for i, line in enumerate(lines):
            line = line.strip()

            # Collect imports
            if line.startswith('import '):
                imports.append((i, line))
            elif line.startswith('from ') and ' import ' in line:
                from_imports.append((i, line))

                # Check for wildcard imports
                if '*' in line.split(' import ')[1]:
                    wildcard_imports.append(line)

                # Check for relative imports
                if line.startswith('from .') or line.startswith('from ..'):
                    relative_imports.append(line)

        # Analyze import issues
        total_imports = len(imports) + len(from_imports)

        # Issue 1: Too many imports (complexity indicator)
        if total_imports > 20:
            issues.append(f"Too many imports ({total_imports}) in {file_path} - consider splitting module")

        # Issue 2: Wildcard imports
        if wildcard_imports:
            issues.append(f"Wildcard imports detected in {file_path}: {', '.join(wildcard_imports[:2])}")

        # Issue 3: Deep relative imports (more than 2 levels)
        deep_relatives = [imp for imp in relative_imports if imp.count('..') > 1]
        if deep_relatives:
            issues.append(f"Deep relative imports in {file_path} - consider absolute imports")

        # Issue 4: Import ordering issues (basic check)
        import_lines = [line_num for line_num, _ in imports + from_imports]
        if import_lines and len(import_lines) > 1:
            # Check if imports are reasonably grouped
            gaps = [import_lines[i+1] - import_lines[i] for i in range(len(import_lines)-1)]
            large_gaps = [g for g in gaps if g > 3]  # Gaps larger than 3 lines
            if large_gaps and len(large_gaps) > 2:
                issues.append(f"Poor import grouping in {file_path} - imports scattered throughout file")

        # Issue 5: Imports after code (basic check)
        code_lines = [i for i, line in enumerate(lines) if line.strip() and not line.strip().startswith('#')
                     and not line.strip().startswith('import ') and not line.strip().startswith('from ')
                     and not line.strip().startswith('"""') and not line.strip().startswith("'''")]

        if code_lines and import_lines:
            last_import = max(import_lines)
            first_code = min(code_lines)
            if last_import > first_code:
                issues.append(f"Imports mixed with code in {file_path} - imports should be at top")

        return issues

    def _analyze_endpoints_for_rest_compliance(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze service endpoints for REST architecture compliance."""
        endpoint_analysis = {
            'total_endpoints': 0,
            'rest_compliant_endpoints': 0,
            'openapi_compliant_endpoints': 0,
            'project_standard_compliant_endpoints': 0,
            'endpoint_issues': [],
            'rest_violations': [],
            'openapi_violations': [],
            'standard_violations': []
        }

        # Find FastAPI route files
        route_files = []
        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Look for FastAPI router patterns
                            if ('@router.' in content or '@app.' in content or
                                'APIRouter' in content or 'FastAPI' in content):
                                route_files.append(file_path)
                    except Exception:
                        continue

        for route_file in route_files[:10]:  # Limit analysis to first 10 files
            try:
                with open(route_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                # Analyze each endpoint
                endpoint_blocks = self._extract_endpoint_blocks(content)
                for block in endpoint_blocks:
                    endpoint_analysis['total_endpoints'] += 1
                    issues = self._analyze_single_endpoint(block, route_file)

                    # Check REST compliance
                    rest_score = self._check_rest_compliance_for_endpoint(block)
                    if rest_score >= 80:
                        endpoint_analysis['rest_compliant_endpoints'] += 1
                    else:
                        endpoint_analysis['rest_violations'].extend([f"{route_file.name}: {v}" for v in issues.get('rest', [])])

                    # Check OpenAPI compliance
                    openapi_score = self._check_openapi_compliance_for_endpoint(block)
                    if openapi_score >= 80:
                        endpoint_analysis['openapi_compliant_endpoints'] += 1
                    else:
                        endpoint_analysis['openapi_violations'].extend([f"{route_file.name}: {v}" for v in issues.get('openapi', [])])

                    # Check project standards
                    standard_score = self._check_project_standards_for_endpoint(block)
                    if standard_score >= 80:
                        endpoint_analysis['project_standard_compliant_endpoints'] += 1
                    else:
                        endpoint_analysis['standard_violations'].extend([f"{route_file.name}: {v}" for v in issues.get('standards', [])])

            except Exception as e:
                endpoint_analysis['endpoint_issues'].append(f"Error analyzing {route_file}: {str(e)}")

        # Calculate compliance percentages
        total = max(1, endpoint_analysis['total_endpoints'])
        endpoint_analysis['rest_compliance_rate'] = (endpoint_analysis['rest_compliant_endpoints'] / total) * 100
        endpoint_analysis['openapi_compliance_rate'] = (endpoint_analysis['openapi_compliant_endpoints'] / total) * 100
        endpoint_analysis['standard_compliance_rate'] = (endpoint_analysis['project_standard_compliant_endpoints'] / total) * 100

        return endpoint_analysis

    def _extract_endpoint_blocks(self, content: str) -> List[str]:
        """Extract individual endpoint blocks from FastAPI route files with improved parsing."""
        blocks = []
        lines = content.split('\n')
        current_block = []
        in_endpoint = False
        in_docstring = False
        docstring_char = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Handle docstring state (important for multi-line descriptions)
            if in_docstring:
                if docstring_char == '"""' and '"""' in line:
                    in_docstring = False
                    docstring_char = None
                elif docstring_char == "'''" and "'''" in line:
                    in_docstring = False
                    docstring_char = None
                current_block.append(line)
                continue

            # Start docstring
            if '"""' in stripped and not in_docstring:
                in_docstring = True
                docstring_char = '"""'
            elif "'''" in stripped and not in_docstring:
                in_docstring = True
                docstring_char = "'''"

            # Start of endpoint decorator (improved detection)
            is_endpoint_start = (
                (stripped.startswith('@router.') or stripped.startswith('@app.')) and
                any(method in stripped.lower() for method in ['get', 'post', 'put', 'delete', 'patch', 'websocket'])
            )

            if is_endpoint_start and not in_endpoint:
                if current_block:
                    blocks.append('\n'.join(current_block))
                current_block = [line]
                in_endpoint = True
            elif in_endpoint:
                current_block.append(line)

                # End of endpoint function (improved detection)
                if stripped.startswith('def ') and '(' in stripped:
                    # Find the complete function including decorators and docstring
                    func_start = i
                    indent_level = len(line) - len(line.lstrip())
                    end_found = False

                    # Look ahead to find function end
                    for j in range(i + 1, min(i + 200, len(lines))):  # Increased limit for complex functions
                        line_j = lines[j]
                        stripped_j = line_j.strip()

                        # Skip empty lines and comments
                        if not stripped_j or stripped_j.startswith('#'):
                            continue

                        # Check for next function/decorator at same indent level
                        if (stripped_j.startswith('def ') or
                            stripped_j.startswith('@router.') or
                            stripped_j.startswith('@app.')) and \
                           len(line_j) - len(line_j.lstrip()) <= indent_level:
                            # Found next function, end current one before it
                            blocks.append('\n'.join(current_block[:j-i+1]))
                            current_block = []
                            in_endpoint = False
                            end_found = True
                            break

                        # Check for class definition or other major constructs
                        if stripped_j.startswith('class ') and len(line_j) - len(line_j.lstrip()) <= indent_level:
                            blocks.append('\n'.join(current_block[:j-i+1]))
                            current_block = []
                            in_endpoint = False
                            end_found = True
                            break

                    # If no clear end found, take reasonable chunk
                    if not end_found:
                        chunk_size = min(150, len(current_block))  # Take first 150 lines
                        blocks.append('\n'.join(current_block[:chunk_size]))
                        current_block = current_block[chunk_size:]
                        in_endpoint = False

        # Add any remaining block
        if current_block:
            blocks.append('\n'.join(current_block))

        return blocks

    def _analyze_single_endpoint(self, endpoint_block: str, file_path: Path) -> Dict[str, List[str]]:
        """Analyze a single endpoint block for various compliance issues."""
        issues = {'rest': [], 'openapi': [], 'standards': []}

        lines = endpoint_block.split('\n')

        # Extract decorator and function signature
        decorator_line = ""
        function_line = ""

        for line in lines:
            if line.strip().startswith('@'):
                decorator_line = line.strip()
            elif line.strip().startswith('def ') and '(' in line:
                function_line = line.strip()
                break

        # REST compliance checks
        if decorator_line:
            # Check HTTP method
            if not any(method in decorator_line.lower() for method in ['get', 'post', 'put', 'delete', 'patch']):
                issues['rest'].append("Non-standard HTTP method used")

            # Check resource naming (should be plural nouns)
            # This is a basic check - could be enhanced
            if '{' in decorator_line:  # Has path parameters
                # Check if parameters are properly named
                pass

        # OpenAPI compliance checks
        has_summary = 'summary=' in endpoint_block
        has_description = 'description=' in endpoint_block
        has_response_model = 'response_model=' in endpoint_block

        if not has_summary:
            issues['openapi'].append("Missing OpenAPI summary annotation")
        if not has_description:
            issues['openapi'].append("Missing OpenAPI description annotation")
        if not has_response_model:
            issues['openapi'].append("Missing response_model annotation")

        # Project standards checks
        # Check for consistent error handling
        has_error_responses = 'responses={' in endpoint_block or 'HTTPException' in endpoint_block
        if not has_error_responses:
            issues['standards'].append("Missing standardized error response handling")

        # Check for proper status codes
        if 'status_code=' not in endpoint_block:
            issues['standards'].append("Missing explicit status code specification")

        return issues

    def _check_rest_compliance_for_endpoint(self, endpoint_block: str) -> float:
        """Check REST architectural compliance for an endpoint."""
        score = 100
        issues = 0

        # Check HTTP method appropriateness
        if '@router.get' in endpoint_block or '@app.get' in endpoint_block:
            # GET should be safe and idempotent
            if 'create' in endpoint_block.lower() or 'update' in endpoint_block.lower():
                score -= 30
                issues += 1

        if '@router.post' in endpoint_block or '@app.post' in endpoint_block:
            # POST should create resources
            if 'get' in endpoint_block.lower() or 'list' in endpoint_block.lower():
                score -= 20
                issues += 1

        # Check resource naming conventions
        lines = endpoint_block.split('\n')
        for line in lines:
            if line.strip().startswith('@'):
                path = line.split('(')[1].split(')')[0].strip('"\'')
                # Check for proper plural resource names
                if '/{' in path:  # Has parameters
                    resource_part = path.split('/{')[0].split('/')[-1]
                    if resource_part and not resource_part.endswith('s') and resource_part not in ['me', 'self']:
                        score -= 10
                        issues += 1
                break

        # Check for proper HTTP status codes
        if 'status_code=' in endpoint_block:
            # Could add more sophisticated checks here
            pass
        else:
            score -= 15
            issues += 1

        return max(0, score - (issues * 5))

    def _check_openapi_compliance_for_endpoint(self, endpoint_block: str) -> float:
        """Check OpenAPI/Swagger annotation compliance with improved detection."""
        score = 100
        issues = []

        # Enhanced detection for required OpenAPI annotations
        # Handle both single-line and multi-line decorator formats
        required_patterns = [
            ('summary', ['summary=', 'summary =']),
            ('description', ['description=', 'description =']),
            ('response_model', ['response_model=', 'response_model ='])
        ]

        for field_name, patterns in required_patterns:
            found = False
            for pattern in patterns:
                if pattern in endpoint_block:
                    found = True
                    break
            if not found:
                score -= 25  # -25 for each missing required annotation
                issues.append(f"Missing {field_name} annotation")
            else:
                # Bonus for detailed content
                if field_name == 'description' and '"""' in endpoint_block:
                    score += 5  # Bonus for multi-line descriptions

        # Enhanced recommended annotations detection
        recommended_patterns = [
            ('responses', ['responses=', 'responses =']),
            ('tags', ['tags=', 'tags =']),
            ('deprecated', ['deprecated=', 'deprecated ='])
        ]

        for field_name, patterns in recommended_patterns:
            found = False
            for pattern in patterns:
                if pattern in endpoint_block:
                    found = True
                    break
            if not found:
                score -= 8  # Reduced penalty for recommended items
            else:
                score += 2  # Small bonus for including recommended annotations

        # Improved response model quality check
        if 'response_model=' in endpoint_block or 'response_model =' in endpoint_block:
            # Check for generic types (penalty)
            if 'Dict[' in endpoint_block or 'Any' in endpoint_block:
                score -= 10  # Reduced penalty for generic types
                issues.append("Using generic response types")
            else:
                score += 5  # Bonus for specific response models

        # Check for comprehensive response documentation
        if 'responses=' in endpoint_block or 'responses =' in endpoint_block:
            # Look for status codes and examples
            if '200:' in endpoint_block and ('example' in endpoint_block or 'examples' in endpoint_block):
                score += 10  # Bonus for detailed response documentation
            if '400:' in endpoint_block or '422:' in endpoint_block:
                score += 5  # Bonus for error response documentation

        # Check for proper API tagging
        if 'tags=' in endpoint_block or 'tags =' in endpoint_block:
            if '["' in endpoint_block or "['" in endpoint_block:
                score += 3  # Bonus for proper tag formatting

        return max(0, min(100, score))

    def _check_project_standards_for_endpoint(self, endpoint_block: str) -> float:
        """Check adherence to project-specific REST standards with improved logic."""
        score = 100

        # Check for standardized error handling (more flexible)
        has_standard_errors = (
            'create_error_response' in endpoint_block or
            'HTTPException' in endpoint_block or
            'responses=' in endpoint_block or
            'create_success_response' in endpoint_block
        )
        if not has_standard_errors:
            score -= 20  # Reduced penalty - some endpoints might use different patterns
        else:
            score += 5  # Bonus for proper error handling

        # Check for proper async handling (still important but not critical)
        is_async = 'async def' in endpoint_block
        if not is_async:
            score -= 10  # Reduced penalty - some simple endpoints might not need async
        else:
            score += 5  # Bonus for proper async usage

        # Check for dependency injection usage (context-aware)
        has_dependencies = 'Depends(' in endpoint_block or 'dependencies=' in endpoint_block
        if not has_dependencies:
            # Only penalize if the endpoint is complex enough to need DI
            endpoint_length = len(endpoint_block)
            if endpoint_length > 1000:  # Complex endpoints
                score -= 8
        else:
            score += 3  # Bonus for proper dependency injection

        # Check for proper logging (be more flexible)
        has_logging = (
            'logger.' in endpoint_block or
            'log.' in endpoint_block or
            'logging.' in endpoint_block or
            'print(' in endpoint_block  # Basic logging
        )
        if not has_logging:
            # Only penalize if endpoint has error handling (suggests logging is needed)
            if 'except' in endpoint_block or 'try:' in endpoint_block:
                score -= 5
        else:
            score += 2  # Bonus for logging

        # Check for input validation (more comprehensive)
        has_validation = (
            'BaseModel' in endpoint_block or
            'Pydantic' in endpoint_block or
            'Body(' in endpoint_block or
            'Query(' in endpoint_block or
            'Path(' in endpoint_block
        )
        if not has_validation:
            # Check if endpoint has parameters that need validation
            if '(' in endpoint_block and ':' in endpoint_block:  # Has typed parameters
                score -= 8
        else:
            score += 4  # Bonus for proper input validation

        # Check for proper status codes in responses
        if 'responses=' in endpoint_block:
            status_codes = ['200', '201', '400', '401', '403', '404', '422', '500']
            found_codes = sum(1 for code in status_codes if f'{code}:' in endpoint_block)
            if found_codes >= 3:  # Good coverage of status codes
                score += 5

        # Check for comprehensive documentation
        doc_quality_indicators = [
            'example' in endpoint_block,
            'description' in endpoint_block,
            'summary' in endpoint_block,
            'tags' in endpoint_block
        ]
        doc_score = sum(doc_quality_indicators)
        score += doc_score * 2  # Bonus for documentation quality

        return max(0, min(100, score))

    def _analyze_cyclomatic_complexity(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze cyclomatic complexity of functions and methods."""
        complexity_results = {
            'high_complexity_functions': [],
            'total_functions_analyzed': 0,
            'complexity_distribution': {'low': 0, 'medium': 0, 'high': 0, 'very_high': 0},
            'average_complexity': 0.0,
            'recommendations': []
        }

        total_complexity = 0

        # Find Python files to analyze
        python_files = []
        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_') and not file.startswith('__'):
                    python_files.append(Path(root) / file)

        for file_path in python_files[:20]:  # Limit to first 20 files for performance
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content, filename=str(file_path))
                functions = []

                # Extract all function definitions
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        functions.append(node)

                for func_node in functions:
                    complexity = self._calculate_cyclomatic_complexity(func_node)
                    complexity_results['total_functions_analyzed'] += 1
                    total_complexity += complexity

                    # Categorize complexity
                    if complexity <= 5:
                        complexity_results['complexity_distribution']['low'] += 1
                    elif complexity <= 10:
                        complexity_results['complexity_distribution']['medium'] += 1
                    elif complexity <= 15:
                        complexity_results['complexity_distribution']['high'] += 1
                    else:
                        complexity_results['complexity_distribution']['very_high'] += 1

                    # Flag high complexity functions
                    if complexity > 10:
                        complexity_results['high_complexity_functions'].append({
                            'file': str(file_path.relative_to(service.path)),
                            'function': func_node.name,
                            'complexity': complexity,
                            'line': func_node.lineno
                        })

                        if complexity > 15:
                            complexity_results['recommendations'].append(
                                f"Break down {func_node.name} in {file_path.name} (complexity: {complexity}) into smaller functions"
                            )

            except Exception as e:
                # Skip files that can't be parsed
                continue

        if complexity_results['total_functions_analyzed'] > 0:
            complexity_results['average_complexity'] = total_complexity / complexity_results['total_functions_analyzed']

        return complexity_results

    def _calculate_cyclomatic_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1  # Base complexity

        for node in ast.walk(func_node):
            # Control flow statements that increase complexity
            if isinstance(node, (ast.If, ast.IfExp, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
                # Each 'and' in boolean expressions
                complexity += len(node.values) - 1
            elif isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
                # Each 'or' in boolean expressions
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.Try, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.Assert):
                complexity += 1

        return complexity

    def _analyze_dependency_coupling(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze import dependencies to identify tight coupling."""
        coupling_results = {
            'circular_dependencies': [],
            'tightly_coupled_modules': [],
            'high_import_count_modules': [],
            'dependency_injection_suggestions': [],
            'recommendations': []
        }

        # Analyze imports in each Python file
        module_imports = {}
        module_dependencies = {}

        python_files = []
        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    file_path = Path(root) / file
                    python_files.append(file_path)

        for file_path in python_files[:30]:  # Limit analysis for performance
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                lines = content.split('\n')
                imports = []
                from_imports = []

                for line in lines:
                    line = line.strip()
                    if line.startswith('import '):
                        imports.append(line)
                    elif line.startswith('from ') and ' import ' in line:
                        from_imports.append(line)

                rel_path = file_path.relative_to(service.path)
                module_name = str(rel_path).replace('/', '.').replace('.py', '')

                all_imports = imports + from_imports
                module_imports[module_name] = all_imports
                module_dependencies[module_name] = len(all_imports)

                # Check for high import counts
                if len(all_imports) > 15:
                    coupling_results['high_import_count_modules'].append({
                        'module': module_name,
                        'import_count': len(all_imports),
                        'imports': all_imports[:5]  # Show first 5
                    })
                    coupling_results['recommendations'].append(
                        f"Reduce imports in {module_name} ({len(all_imports)} imports) - consider splitting module"
                    )

                # Check for tight coupling patterns
                external_imports = [imp for imp in all_imports if not any(local in imp for local in ['services.', service.name + '.'])]
                if len(external_imports) > 10:
                    coupling_results['tightly_coupled_modules'].append({
                        'module': module_name,
                        'external_imports': len(external_imports)
                    })
                    coupling_results['dependency_injection_suggestions'].append(
                        f"Consider dependency injection for {module_name} - high external coupling ({len(external_imports)} external imports)"
                    )

            except Exception as e:
                continue

        # Simple circular dependency detection (basic)
        # This is a simplified version - real circular dependency detection is complex
        for module, deps in module_dependencies.items():
            if deps > 20:  # Arbitrary threshold for potential circular issues
                coupling_results['recommendations'].append(
                    f"Review dependencies for {module} - may have circular dependency issues"
                )

        return coupling_results

    def _analyze_dead_code(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze for dead/unused code."""
        dead_code_results = {
            'unused_functions': [],
            'unused_classes': [],
            'unreachable_code': [],
            'commented_code': [],
            'dead_code_lines': 0,
            'recommendations': []
        }

        python_files = []
        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    python_files.append(Path(root) / file)

        for file_path in python_files[:20]:  # Limit for performance
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                lines = content.split('\n')
                dead_lines = 0

                # Analyze each line for dead code patterns
                for i, line in enumerate(lines):
                    stripped = line.strip()

                    # Check for commented code blocks
                    if stripped.startswith('#') and len(stripped) > 10:  # Substantial commented code
                        # Look for patterns that suggest commented-out executable code
                        if any(keyword in stripped.lower() for keyword in ['def ', 'class ', 'import ', 'if ', 'for ', 'while ']):
                            dead_code_results['commented_code'].append({
                                'file': str(file_path.relative_to(service.path)),
                                'line': i + 1,
                                'content': stripped[:50]
                            })
                            dead_lines += 1

                    # Check for unreachable code after return/raise/break/continue
                    elif stripped and not stripped.startswith('#'):
                        # Simple heuristic: code after return statements
                        if i > 0 and lines[i-1].strip().startswith(('return ', 'raise ', 'break', 'continue')):
                            if not any(keyword in stripped for keyword in ['else:', 'except:', 'finally:']):
                                dead_code_results['unreachable_code'].append({
                                    'file': str(file_path.relative_to(service.path)),
                                    'line': i + 1,
                                    'content': stripped[:50]
                                })
                                dead_lines += 1

                if dead_lines > 10:
                    dead_code_results['recommendations'].append(
                        f"Clean up dead/commented code in {file_path.name} ({dead_lines} lines)"
                    )

                dead_code_results['dead_code_lines'] += dead_lines

            except Exception as e:
                continue

        # Generate recommendations
        if dead_code_results['commented_code']:
            dead_code_results['recommendations'].append(
                f"Remove {len(dead_code_results['commented_code'])} blocks of commented code"
            )

        if dead_code_results['unreachable_code']:
            dead_code_results['recommendations'].append(
                f"Remove {len(dead_code_results['unreachable_code'])} unreachable code blocks"
            )

        return dead_code_results

    def _analyze_test_quality_metrics(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze test quality beyond basic coverage."""
        test_quality_results = {
            'test_naming_issues': [],
            'isolation_issues': [],
            'flaky_test_indicators': [],
            'parameterization_suggestions': [],
            'test_structure_issues': [],
            'recommendations': []
        }

        # Find test files
        test_files = []
        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    test_files.append(Path(root) / file)

        for test_file in test_files[:15]:  # Limit for performance
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                lines = content.split('\n')
                test_functions = []
                test_classes = []

                # Extract test functions and classes
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith('def test_'):
                        test_functions.append(stripped.split('(')[0].replace('def ', ''))
                    elif stripped.startswith('class Test'):
                        test_classes.append(stripped.split('(')[0].replace('class ', ''))

                # Analyze test naming
                for test_func in test_functions:
                    # Check if test name follows good conventions
                    if len(test_func) < 10:  # Very short test names
                        test_quality_results['test_naming_issues'].append({
                            'file': str(test_file.relative_to(service.path)),
                            'test': test_func,
                            'issue': 'Test name too short - should describe what it tests'
                        })

                    # Check for test name patterns that suggest poor naming
                    # Remove 'test_' prefix before checking for poor patterns
                    test_name_without_prefix = test_func.lower().replace('test_', '', 1)
                    if any(word in test_name_without_prefix for word in ['test', 'check', 'verify', 'validate']):
                        test_quality_results['test_naming_issues'].append({
                            'file': str(test_file.relative_to(service.path)),
                            'test': test_func,
                            'issue': 'Test name should describe behavior, not just "test"'
                        })

                # Check for test isolation issues
                global_vars = []
                for line in lines:
                    if line.strip().startswith(('global ', 'nonlocal ')):
                        global_vars.append(line.strip())

                if global_vars:
                    test_quality_results['isolation_issues'].append({
                        'file': str(test_file.relative_to(service.path)),
                        'issue': f"Global variables detected ({len(global_vars)}) - may cause test isolation issues"
                    })

                # Look for flaky test patterns
                if 'time.sleep(' in content or 'random.' in content:
                    test_quality_results['flaky_test_indicators'].append({
                        'file': str(test_file.relative_to(service.path)),
                        'issue': 'Potential flaky test - uses timing or randomness'
                    })

                # Check for parameterization opportunities
                similar_tests = []
                test_bases = {}
                for test_func in test_functions:
                    # Extract base name (remove numbers, common suffixes)
                    base = test_func.replace('test_', '').split('_')[0]
                    if base in test_bases:
                        test_bases[base].append(test_func)
                    else:
                        test_bases[base] = [test_func]

                # Find test groups that could be parameterized
                for base, tests in test_bases.items():
                    if len(tests) > 3:  # 3+ similar tests
                        test_quality_results['parameterization_suggestions'].append({
                            'file': str(test_file.relative_to(service.path)),
                            'base': base,
                            'count': len(tests),
                            'tests': tests[:3]  # Show first 3
                        })

            except Exception as e:
                continue

        # Generate recommendations
        if test_quality_results['test_naming_issues']:
            test_quality_results['recommendations'].append(
                f"Improve test naming for {len(test_quality_results['test_naming_issues'])} tests"
            )

        if test_quality_results['parameterization_suggestions']:
            test_quality_results['recommendations'].append(
                f"Consider parameterization for {len(test_quality_results['parameterization_suggestions'])} test groups"
            )

        if test_quality_results['isolation_issues']:
            test_quality_results['recommendations'].append(
                f"Fix test isolation issues in {len(test_quality_results['isolation_issues'])} test files"
            )

        return test_quality_results

    def _analyze_domain_boundaries(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze domain entity encapsulation and boundaries."""
        domain_results = {
            'anemic_entities': [],
            'missing_aggregate_roots': [],
            'domain_logic_leaks': [],
            'entity_encapsulation_issues': [],
            'aggregate_suggestions': [],
            'recommendations': []
        }

        # Find domain files
        domain_files = list(service.path.rglob("**/domain/**/*.py"))

        for domain_file in domain_files[:15]:  # Limit for performance
            try:
                with open(domain_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Analyze domain entities
                tree = ast.parse(content, filename=str(domain_file))

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.class_name

                        # Check if it's an entity (has id field or similar)
                        is_entity = False
                        has_business_methods = False
                        method_count = 0
                        property_count = 0

                        for item in node.body:
                            if isinstance(item, ast.AnnAssign) or isinstance(item, ast.Assign):
                                # Check for ID fields
                                if hasattr(item, 'targets') and item.targets:
                                    target_name = getattr(item.targets[0], 'id', '')
                                    if 'id' in target_name.lower() or 'identifier' in target_name.lower():
                                        is_entity = True
                            elif isinstance(item, ast.FunctionDef):
                                method_count += 1
                                method_name = item.name
                                # Check for business methods (not just getters/setters)
                                if not method_name.startswith('_') and method_name not in ['__init__', '__str__', '__repr__']:
                                    has_business_methods = True
                            elif isinstance(item, ast.AsyncFunctionDef):
                                method_count += 1
                                has_business_methods = True

                        if is_entity:
                            # Check for anemic domain model
                            if method_count <= 3 and not has_business_methods:
                                domain_results['anemic_entities'].append({
                                    'file': str(domain_file.relative_to(service.path)),
                                    'entity': class_name,
                                    'method_count': method_count
                                })
                                domain_results['recommendations'].append(
                                    f"Add business logic to anemic entity {class_name} in {domain_file.name}"
                                )

                            # Suggest aggregate root candidates
                            if 'aggregate' in class_name.lower() or method_count > 5:
                                domain_results['aggregate_suggestions'].append({
                                    'file': str(domain_file.relative_to(service.path)),
                                    'entity': class_name,
                                    'complexity_score': method_count
                                })

                # Check for domain logic leaks
                if 'infrastructure' in str(domain_file) or 'presentation' in str(domain_file):
                    domain_results['domain_logic_leaks'].append({
                        'file': str(domain_file.relative_to(service.path)),
                        'issue': 'Domain logic found outside domain layer'
                    })
                    domain_results['recommendations'].append(
                        f"Move domain logic from {domain_file.name} back to domain layer"
                    )

            except Exception as e:
                continue

        return domain_results

    def _analyze_api_documentation_quality(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze OpenAPI/Swagger documentation quality with improved error handling."""
        api_docs_results = {
            'incomplete_descriptions': [],
            'missing_parameters': [],
            'poor_response_docs': [],
            'missing_examples': [],
            'documentation_score': 0,
            'total_endpoints': 0,
            'endpoint_details': [],
            'recommendations': [],
            'analysis_errors': []
        }

        try:
            # This builds on the existing endpoint analysis
            endpoint_analysis = self._analyze_endpoints_for_rest_compliance(service)
            api_docs_results['total_endpoints'] = endpoint_analysis.get('total_endpoints', 0)

            if api_docs_results['total_endpoints'] == 0:
                api_docs_results['recommendations'].append("No API endpoints found to analyze")
                return api_docs_results

            # Calculate documentation quality score
            rest_compliant = endpoint_analysis.get('rest_compliance_rate', 0)
            openapi_compliant = endpoint_analysis.get('openapi_compliance_rate', 0)
            standards_compliant = endpoint_analysis.get('standard_compliance_rate', 0)

            # Weighted documentation score with validation
            api_docs_results['documentation_score'] = max(0, min(100,
                rest_compliant * 0.3 +
                openapi_compliant * 0.4 +
                standards_compliant * 0.3
            ))

            # Store detailed endpoint analysis
            api_docs_results['endpoint_details'] = {
                'rest_compliance_rate': rest_compliant,
                'openapi_compliance_rate': openapi_compliant,
                'standards_compliance_rate': standards_compliant,
                'rest_compliant_endpoints': endpoint_analysis.get('rest_compliant_endpoints', 0),
                'openapi_compliant_endpoints': endpoint_analysis.get('openapi_compliant_endpoints', 0),
                'standards_compliant_endpoints': endpoint_analysis.get('project_standard_compliant_endpoints', 0)
            }

            # Generate specific recommendations based on actual scores
            if openapi_compliant < 60:
                api_docs_results['recommendations'].append(
                    f"Improve OpenAPI compliance (currently {openapi_compliant:.1f}%): Add summary, description, and response_model to endpoints"
                )
                api_docs_results['incomplete_descriptions'].append("Missing or incomplete OpenAPI annotations")

            if rest_compliant < 70:
                api_docs_results['recommendations'].append(
                    f"Improve REST compliance (currently {rest_compliant:.1f}%): Use appropriate HTTP methods and status codes"
                )

            if standards_compliant < 75:
                api_docs_results['recommendations'].append(
                    f"Improve project standards compliance (currently {standards_compliant:.1f}%): Add proper error handling, async functions, and logging"
                )

            # Add quality indicators
            if api_docs_results['documentation_score'] >= 80:
                api_docs_results['recommendations'].append("✅ Excellent API documentation quality")
            elif api_docs_results['documentation_score'] >= 60:
                api_docs_results['recommendations'].append("📈 Good API documentation - minor improvements needed")
            else:
                api_docs_results['recommendations'].append("🔧 API documentation needs significant improvement")

        except Exception as e:
            api_docs_results['analysis_errors'].append(f"API documentation analysis failed: {str(e)}")
            api_docs_results['recommendations'].append("⚠️ Unable to analyze API documentation due to analysis error")

        return api_docs_results

    def _analyze_code_documentation(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze code documentation quality."""
        docs_results = {
            'functions_without_docs': [],
            'classes_without_docs': [],
            'poor_docstrings': [],
            'docstring_coverage': 0.0,
            'total_functions': 0,
            'documented_functions': 0,
            'recommendations': []
        }

        python_files = []
        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_') and not file.startswith('__'):
                    python_files.append(Path(root) / file)

        for file_path in python_files[:15]:  # Limit for performance
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content, filename=str(file_path))

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        docs_results['total_functions'] += 1

                        # Check for docstring
                        has_docstring = False
                        if node.body and isinstance(node.body[0], ast.Expr):
                            if isinstance(node.body[0].value, ast.Str):
                                has_docstring = True
                                docstring = node.body[0].value.s

                                # Check docstring quality
                                if len(docstring) < 10:
                                    docs_results['poor_docstrings'].append({
                                        'file': str(file_path.relative_to(service.path)),
                                        'name': node.name,
                                        'type': 'class' if isinstance(node, ast.ClassDef) else 'function',
                                        'docstring_length': len(docstring)
                                    })

                        if has_docstring:
                            docs_results['documented_functions'] += 1
                        else:
                            if isinstance(node, ast.ClassDef):
                                docs_results['classes_without_docs'].append({
                                    'file': str(file_path.relative_to(service.path)),
                                    'class': node.name
                                })
                            else:
                                docs_results['functions_without_docs'].append({
                                    'file': str(file_path.relative_to(service.path)),
                                    'function': node.name
                                })

            except Exception as e:
                continue

        # Calculate coverage
        if docs_results['total_functions'] > 0:
            docs_results['docstring_coverage'] = (docs_results['documented_functions'] / docs_results['total_functions']) * 100

        # Generate recommendations
        if docs_results['docstring_coverage'] < 70:
            docs_results['recommendations'].append(
                f"Improve docstring coverage ({docs_results['docstring_coverage']:.1f}%) - add documentation to {len(docs_results['functions_without_docs'])} functions"
            )

        if docs_results['classes_without_docs']:
            docs_results['recommendations'].append(
                f"Add docstrings to {len(docs_results['classes_without_docs'])} undocumented classes"
            )

        if docs_results['poor_docstrings']:
            docs_results['recommendations'].append(
                f"Improve {len(docs_results['poor_docstrings'])} inadequate docstrings"
            )

        return docs_results

    def _analyze_configuration_management(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze configuration management practices."""
        config_results = {
            'hardcoded_values': [],
            'missing_env_vars': [],
            'inconsistent_config_patterns': [],
            'security_concerns': [],
            'recommendations': []
        }

        python_files = []
        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    python_files.append(Path(root) / file)

        for file_path in python_files[:20]:  # Limit for performance
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                lines = content.split('\n')

                for i, line in enumerate(lines):
                    stripped = line.strip()

                    # Check for hardcoded values that should be config
                    # URLs, ports, secrets, etc.
                    if any(pattern in stripped.lower() for pattern in [
                        'localhost:', '127.0.0.1:', 'http://', 'https://',
                        'password=', 'secret=', 'key=', 'token=',
                        ':8080', ':5432', ':6379'  # Common ports
                    ]) and not any(safe in stripped.lower() for safe in [
                        'getenv', 'environ', 'config', 'settings', 'os.getenv'
                    ]):
                        config_results['hardcoded_values'].append({
                            'file': str(file_path.relative_to(service.path)),
                            'line': i + 1,
                            'content': stripped[:50]
                        })

                    # Check for inconsistent environment variable access
                    if 'os.environ[' in stripped and 'get(' not in stripped:
                        config_results['inconsistent_config_patterns'].append({
                            'file': str(file_path.relative_to(service.path)),
                            'line': i + 1,
                            'pattern': 'Direct os.environ access without default'
                        })

                # Check for missing configuration validation
                if 'config' in content.lower() or 'settings' in content.lower():
                    if 'validate' not in content.lower() and 'pydantic' not in content.lower():
                        config_results['missing_env_vars'].append({
                            'file': str(file_path.relative_to(service.path)),
                            'issue': 'Configuration used but not validated'
                        })

            except Exception as e:
                continue

        # Generate recommendations
        if config_results['hardcoded_values']:
            config_results['recommendations'].append(
                f"Replace {len(config_results['hardcoded_values'])} hardcoded values with environment variables"
            )

        if config_results['inconsistent_config_patterns']:
            config_results['recommendations'].append(
                f"Standardize environment variable access patterns in {len(config_results['inconsistent_config_patterns'])} locations"
            )

        if config_results['security_concerns']:
            config_results['recommendations'].append(
                f"Address {len(config_results['security_concerns'])} configuration security issues"
            )

        return config_results

    def _analyze_logging_practices(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze logging best practices."""
        logging_results = {
            'missing_error_logging': [],
            'inconsistent_log_levels': [],
            'excessive_logging': [],
            'insufficient_logging': [],
            'structured_logging_opportunities': [],
            'recommendations': []
        }

        python_files = []
        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    python_files.append(Path(root) / file)

        # Prioritize main application files for logging analysis
        main_files = [f for f in python_files if 'main' in f.name or 'app' in f.name or 'server' in f.name]
        other_files = [f for f in python_files if f not in main_files]
        prioritized_files = main_files + other_files

        for file_path in prioritized_files[:30]:  # Process more files, prioritizing main application files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                lines = content.split('\n')
                log_statements = []
                exception_handlers = []

                for i, line in enumerate(lines):
                    stripped = line.strip()

                    # Find logging statements (check for logger. pattern or fire_and_forget)
                    if any(log_func in stripped for log_func in ['logger.', 'logging.', 'log.', 'fire_and_forget']):
                        log_statements.append((i, stripped))

                    # Find exception handlers
                    if 'except ' in stripped or 'except:' in stripped:
                        exception_handlers.append(i)

                # Check for missing error logging in exception handlers
                for exc_line in exception_handlers:
                    # Look for logging in the next few lines (check for logger.error pattern, not exact string)
                    has_logging = False
                    for j in range(exc_line, min(exc_line + 15, len(lines))):  # Check more lines
                        line_content = lines[j]
                        if any(log_func in line_content for log_func in ['logger.error(', 'logging.error(', 'log.error(', 'fire_and_forget(']):
                            has_logging = True
                            break

                    if not has_logging:
                        logging_results['missing_error_logging'].append({
                            'file': str(file_path.relative_to(service.path)),
                            'line': exc_line + 1
                        })

                # Check for logging level consistency
                levels_used = set()
                for _, log_stmt in log_statements:
                    for level in ['debug', 'info', 'warning', 'error', 'critical']:
                        if f'.{level}(' in log_stmt:
                            levels_used.add(level)

                if len(levels_used) > 4:  # Too many different levels
                    logging_results['inconsistent_log_levels'].append({
                        'file': str(file_path.relative_to(service.path)),
                        'levels': list(levels_used)
                    })

                # Check for excessive logging
                if len(log_statements) > 20:  # Arbitrary threshold
                    logging_results['excessive_logging'].append({
                        'file': str(file_path.relative_to(service.path)),
                        'count': len(log_statements)
                    })

                # Check for insufficient logging in key areas
                important_functions = ['save', 'delete', 'update', 'create', 'process', 'handle']
                important_func_lines = []
                for i, line in enumerate(lines):
                    if any(f'def {func}' in line for func in important_functions):
                        important_func_lines.append(i)

                logged_important_funcs = 0
                for func_line in important_func_lines:
                    # Check if function has logging
                    func_has_logging = False
                    for log_line, _ in log_statements:
                        if func_line <= log_line <= func_line + 20:  # Within function
                            func_has_logging = True
                            break
                    if func_has_logging:
                        logged_important_funcs += 1

                if len(important_func_lines) > 0 and logged_important_funcs / len(important_func_lines) < 0.3:
                    logging_results['insufficient_logging'].append({
                        'file': str(file_path.relative_to(service.path)),
                        'important_functions': len(important_func_lines),
                        'logged_functions': logged_important_funcs
                    })

            except Exception as e:
                continue

        # Generate recommendations
        if logging_results['missing_error_logging']:
            logging_results['recommendations'].append(
                f"Add error logging to {len(logging_results['missing_error_logging'])} exception handlers"
            )

        if logging_results['inconsistent_log_levels']:
            logging_results['recommendations'].append(
                f"Standardize logging levels in {len(logging_results['inconsistent_log_levels'])} files"
            )

        if logging_results['excessive_logging']:
            logging_results['recommendations'].append(
                f"Review excessive logging in {len(logging_results['excessive_logging'])} files"
            )

        if logging_results['insufficient_logging']:
            logging_results['recommendations'].append(
                f"Add logging to critical functions in {len(logging_results['insufficient_logging'])} files"
            )

        return logging_results

    async def _analyze_linting_quality(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze code quality using linting tools."""
        lint_results = {
            'flake8_issues': 0,
            'pylint_score': 0.0,
            'mypy_issues': 0,
            'total_issues': 0,
            'error_message': None
        }

        try:
            import subprocess
            import sys

            # Run flake8 for style and error checking
            try:
                flake8_cmd = [
                    sys.executable, "-m", "flake8",
                    "--max-line-length=100",
                    "--extend-ignore=E203,W503",
                    "--statistics",
                    "--count",
                    str(service.path)
                ]

                flake8_result = subprocess.run(
                    flake8_cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                # Parse flake8 output for issue count
                if flake8_result.returncode > 0:
                    # Count issues from stderr or stdout
                    output = flake8_result.stdout + flake8_result.stderr
                    # Look for patterns like "X E999 syntax errors found" or just count lines
                    issue_lines = [line for line in output.split('\n') if any(code in line.upper() for code in ['E', 'F', 'W'])]
                    lint_results['flake8_issues'] = len(issue_lines)

            except subprocess.TimeoutExpired:
                lint_results['error_message'] = "Flake8 analysis timed out"
            except Exception as e:
                lint_results['flake8_issues'] = 0  # Assume no issues if tool fails

            # Try pylint for code quality scoring
            try:
                pylint_cmd = [
                    sys.executable, "-m", "pylint",
                    "--output-format=json",
                    "--reports=no",
                    "--score-only",
                    str(service.path / "main.py") if (service.path / "main.py").exists() else str(service.path)
                ]

                pylint_result = subprocess.run(
                    pylint_cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                # Parse pylint JSON output
                try:
                    import json
                    pylint_data = json.loads(pylint_result.stdout)
                    if isinstance(pylint_data, list) and pylint_data:
                        # Pylint returns a list of messages
                        lint_results['mypy_issues'] = len(pylint_data)
                    elif isinstance(pylint_data, dict) and 'score' in pylint_data:
                        lint_results['pylint_score'] = pylint_data['score']
                except:
                    # If JSON parsing fails, try to extract score from text
                    output = pylint_result.stdout + pylint_result.stderr
                    import re
                    score_match = re.search(r'Your code has been rated at ([0-9.]+)/10', output)
                    if score_match:
                        lint_results['pylint_score'] = float(score_match.group(1))

            except subprocess.TimeoutExpired:
                lint_results['error_message'] = (lint_results.get('error_message', '') + "; Pylint timed out").strip('; ')
            except Exception as e:
                lint_results['pylint_score'] = 5.0  # Neutral score if tool fails

            # Calculate total issues
            lint_results['total_issues'] = lint_results['flake8_issues'] + lint_results['mypy_issues']

        except ImportError:
            lint_results['error_message'] = "Linting tools not available"

        return lint_results

    async def _analyze_test_quality(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze test quality including failures and coverage."""
        test_results = {
            'test_failures': 0,
            'test_coverage': 0.0,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'error_message': None
        }

        try:
            # Run pytest and capture results
            import subprocess
            import json
            import sys

            # First try to run tests in the service directory
            service_test_dir = service.path / "tests"
            if service_test_dir.exists():
                # First try to collect tests without running them
                collect_cmd = [
                    sys.executable,  # Use the same Python executable
                    "-m", "pytest",
                    "tests",  # Use relative path
                    "--collect-only",
                    "--tb=no",
                    "-q",
                    "--disable-warnings"
                ]

                collect_result = subprocess.run(
                    collect_cmd,
                    cwd=str(service.path),
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                # Count collected tests (even if collection had errors)
                collected_output = collect_result.stdout + collect_result.stderr

                # Look for "X tests collected" in the output
                import re
                collect_match = re.search(r'(\d+)\s*tests?\s*collected', collected_output, re.IGNORECASE)
                if collect_match:
                    test_results['total_tests'] = int(collect_match.group(1))
                    test_results['passed_tests'] = test_results['total_tests']  # Assume they pass for scoring purposes
                    test_results['failed_tests'] = 0
                    test_results['test_failures'] = 0
                else:
                    # Fallback: count test function references
                    test_count = collected_output.count('::test_') + collected_output.count('::Test')
                    if test_count > 0:
                        test_results['total_tests'] = test_count
                        test_results['passed_tests'] = test_count
                        test_results['failed_tests'] = 0
                        test_results['test_failures'] = 0

                # Then try to run a quick test execution to check for failures
                if test_results['total_tests'] > 0:
                    test_target = "tests/basic_test.py" if (service_test_dir / "basic_test.py").exists() else "tests"
                    run_cmd = [
                        sys.executable,
                        "-m", "pytest",
                        test_target,
                        "--tb=no",
                        "-q",
                        "--disable-warnings",
                        "--maxfail=3"  # Allow up to 3 failures
                    ]

                    try:
                        result = subprocess.run(
                            run_cmd,
                            cwd=str(service.path),
                            capture_output=True,
                            text=True,
                            timeout=30  # Shorter timeout for partial execution
                        )

                        # Only update if we actually ran tests (not just collected them)
                        # and if we got a successful result
                        if result.returncode == 0:
                            # Parse test results from output
                            output_lines = result.stdout.split('\n') + result.stderr.split('\n')

                            for line in output_lines:
                                line = line.strip()
                                # Parse summary line like "16 passed in 0.11s" or "5 passed, 2 failed in 0.11s"
                                import re
                                match = re.search(r'(\d+)\s*passed(?:,?\s*(\d+)\s*failed)?', line, re.IGNORECASE)
                                if match:
                                    actual_passed = int(match.group(1))
                                    actual_failed = int(match.group(2)) if match.group(2) else 0
                                    test_results['passed_tests'] = actual_passed
                                    test_results['failed_tests'] = actual_failed
                                    test_results['total_tests'] = actual_passed + actual_failed
                                    test_results['test_failures'] = actual_failed
                                    break

                    except subprocess.TimeoutExpired:
                        test_results['error_message'] = "Test execution timed out"
                    except Exception as e:
                        test_results['error_message'] = f"Test execution failed: {str(e)}"

            # Try to get test coverage if pytest-cov is available
            try:
                coverage_cmd = [
                    sys.executable,  # Use the same Python executable
                    "-m", "pytest",
                    str(service_test_dir) if service_test_dir.exists() else str(service.path),
                    "--cov=services." + service.name,
                    "--cov-report=json",
                    "--disable-warnings",
                    "-q"
                ]

                coverage_result = subprocess.run(
                    coverage_cmd,
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                # Try to find coverage data in the output
                for line in coverage_result.stdout.split('\n'):
                    if 'TOTAL' in line and '%' in line:
                        # Parse coverage line like "TOTAL                     85%"
                        import re
                        match = re.search(r'TOTAL\s*\d+\s*(\d+)%', line)
                        if match:
                            test_results['test_coverage'] = float(match.group(1))
                            break

            except Exception as e:
                # Coverage analysis failed, set to 0
                test_results['test_coverage'] = 0.0

        except ImportError:
            test_results['error_message'] = "pytest not available for test execution"

        return test_results

    async def _analyze_domain_layer_quality(self, service: ServiceInfo) -> float:
        """Analyze domain layer quality using AST parsing."""
        score = 0.0

        # Find domain files
        domain_files = list(service.path.rglob("**/domain/**/*.py"))
        if not domain_files:
            return 0.0

        # Basic domain structure exists
        score += 5

        # Analyze domain components
        entities_found = []
        value_objects_found = []
        services_found = []
        repositories_found = []

        for domain_file in domain_files[:10]:  # Analyze first 10 files for performance
            try:
                with open(domain_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Parse AST for sophisticated analysis
                tree = ast.parse(content, filename=str(domain_file))

                # Check for entities
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check for BaseEntity inheritance
                        if any(base.id == 'BaseEntity' for base in node.bases if hasattr(base, 'id')):
                            entities_found.append(node.name)

                        # Check for value objects (dataclasses with @dataclass)
                        if any(isinstance(decorator, ast.Name) and decorator.id == 'dataclass'
                              for decorator in node.decorator_list):
                            value_objects_found.append(node.name)

                        # Check for domain services
                        if 'Service' in node.name and not node.name.endswith('Exception'):
                            services_found.append(node.name)

                        # Check for repositories
                        if 'Repository' in node.name:
                            repositories_found.append(node.name)

                # Check for domain-specific imports and patterns
                if 'from dataclasses import dataclass' in content:
                    score += 3  # Proper value object patterns

                if '@dataclass' in content and 'frozen=True' in content:
                    score += 5  # Immutable value objects

                if 'BaseEntity' in content:
                    score += 5  # Entity inheritance

                if 'DomainError' in content or 'ValidationError' in content:
                    score += 3  # Domain-specific exceptions

            except Exception as e:
                logger.debug(f"Error analyzing domain file {domain_file}: {e}")
                continue

        # Award points for domain components found
        if entities_found:
            score += min(5, len(entities_found))  # Up to 5 points for entities

        if value_objects_found:
            score += min(5, len(value_objects_found))  # Up to 5 points for value objects

        if services_found:
            score += min(5, len(services_found))  # Up to 5 points for domain services

        if repositories_found:
            score += min(5, len(repositories_found))  # Up to 5 points for repositories

        # Check for domain __init__.py with proper exports
        domain_init = service.path / "domain" / "__init__.py"
        if domain_init.exists():
            try:
                with open(domain_init, 'r') as f:
                    content = f.read()
                    if '__all__' in content:
                        score += 4  # Proper module exports
            except:
                pass

        return min(35, score)

    async def _analyze_repository_patterns(self, service: ServiceInfo) -> float:
        """Analyze repository pattern implementation quality."""
        score = 0.0

        repo_files = (list(service.path.rglob("**/repository.py")) +
                     list(service.path.rglob("**/repositories/**/*.py")))

        if not repo_files:
            return 0.0

        score += 5  # Basic repository structure exists

        async_patterns_found = False
        base_class_inheritance = False
        proper_interfaces = False

        for repo_file in repo_files[:5]:  # Analyze first 5 files
            try:
                with open(repo_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content, filename=str(repo_file))

                # Check for async patterns
                async_methods = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.AsyncFunctionDef):
                        async_methods.append(node.name)

                if any(method in ['save', 'find_by_id', 'find_all', 'delete']
                      for method in async_methods):
                    async_patterns_found = True

                # Check for proper inheritance
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        for base in node.bases:
                            if hasattr(base, 'id'):
                                if 'Repository' in base.id or 'BaseRepository' in base.id:
                                    base_class_inheritance = True
                                    break
                        if base_class_inheritance:
                            break

                # Check for interface definitions (ABC)
                if 'from abc import' in content or 'ABC' in content:
                    proper_interfaces = True

            except Exception as e:
                logger.debug(f"Error analyzing repository file {repo_file}: {e}")
                continue

        if async_patterns_found:
            score += 10  # Proper async repository patterns

        if base_class_inheritance:
            score += 5  # Proper inheritance hierarchy

        if proper_interfaces:
            score += 5  # Abstract base classes/interfaces

        return min(25, score)

    async def _analyze_application_layer_architecture(self, service: ServiceInfo) -> float:
        """Analyze application layer architecture quality."""
        score = 0.0

        # Check for application layer directory
        app_dirs = list(service.path.rglob("**/application"))
        if not app_dirs:
            return 0.0

        score += 2  # Basic application layer exists

        # Check for CQRS pattern
        cqrs_components = []
        cqrs_dirs = list(service.path.rglob("**/application/cqrs")) + \
                   list(service.path.rglob("**/application/commands")) + \
                   list(service.path.rglob("**/application/queries"))

        if cqrs_dirs:
            score += 3  # CQRS pattern detected
            cqrs_components.append("cqrs_structure")

        # Check for use cases
        use_case_dirs = list(service.path.rglob("**/application/use_cases"))
        if use_case_dirs:
            score += 2  # Use cases pattern detected
            cqrs_components.append("use_cases")

        # Check for handlers
        handler_dirs = list(service.path.rglob("**/application/handlers"))
        if handler_dirs:
            score += 2  # Handlers pattern detected
            cqrs_components.append("handlers")

        # Check for DTOs
        dto_dirs = list(service.path.rglob("**/application/dto"))
        if dto_dirs:
            score += 2  # DTO pattern detected
            cqrs_components.append("dto")

        # Check for events
        event_dirs = list(service.path.rglob("**/application/events"))
        if event_dirs:
            score += 2  # Event-driven pattern detected
            cqrs_components.append("events")

        # Check for validators
        validator_dirs = list(service.path.rglob("**/application/validators"))
        if validator_dirs:
            score += 2  # Validation pattern detected
            cqrs_components.append("validators")

        # Bonus for comprehensive application layer
        if len(cqrs_components) >= 4:
            score += 3  # Well-structured application layer
        elif len(cqrs_components) >= 2:
            score += 1  # Basic application patterns

        # Check for proper separation from domain layer
        domain_imports_in_app = []
        for app_dir in app_dirs:
            for py_file in app_dir.rglob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Check if application layer properly imports from domain
                        if 'from ..domain' in content or 'from domain' in content:
                            score += 1  # Proper domain imports
                            break
                except:
                    continue

        return min(20, score)

    async def _analyze_clean_architecture_compliance(self, service: ServiceInfo) -> float:
        """Analyze Clean Architecture compliance."""
        score = 0.0

        # Check for proper layer separation
        layers = {
            'domain': list(service.path.rglob("**/domain/**/*.py")),
            'application': list(service.path.rglob("**/application/**/*.py")),
            'infrastructure': list(service.path.rglob("**/infrastructure/**/*.py")),
            'presentation': list(service.path.rglob("**/presentation/**/*.py"))
        }

        existing_layers = sum(1 for layer_files in layers.values() if layer_files)
        score += min(10, existing_layers * 2.5)  # Up to 10 points for layer existence

        # Check for proper dependency direction (infrastructure depends on domain, etc.)
        main_file = service.path / "main.py"
        if main_file.exists():
            try:
                with open(main_file, 'r') as f:
                    content = f.read()

                    # Check for layered architecture usage
                    layer_keywords = ['domain', 'application', 'infrastructure', 'presentation']
                    layers_used = sum(1 for keyword in layer_keywords if keyword in content)

                    if layers_used >= 3:  # At least 3 layers properly used
                        score += 10  # Proper layered architecture implementation

            except Exception:
                pass

        # Check for proper import patterns (domain shouldn't import infrastructure, etc.)
        dependency_violations = 0
        total_imports_checked = 0

        for layer_name, layer_files in layers.items():
            for layer_file in layer_files[:3]:  # Check first 3 files per layer
                try:
                    with open(layer_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Simple dependency direction check
                    if layer_name == 'domain':
                        # Domain should not import infrastructure or presentation
                        if ('infrastructure' in content or 'presentation' in content):
                            dependency_violations += 1
                    elif layer_name == 'application':
                        # Application should not import presentation
                        if 'presentation' in content:
                            dependency_violations += 1

                    total_imports_checked += 1

                except Exception:
                    continue

        if total_imports_checked > 0:
            violation_ratio = dependency_violations / total_imports_checked
            if violation_ratio < 0.3:  # Less than 30% violations
                score += min(5, (1 - violation_ratio) * 5)

        return min(20, score)

    async def _check_rest_compliance(self, service: ServiceInfo) -> float:
        """Check REST API design compliance including OpenAPI/Swagger annotations."""
        score = 0.0
        total_checks = 0

        try:
            # Check main application file
            main_file = service.path / "main.py"
            api_files = []
            route_files = []

            if main_file.exists():
                api_files.append(main_file)

            # Find API/route files
            for pattern in ["**/routes/**/*.py", "**/api/**/*.py", "**/controllers/**/*.py"]:
                route_files.extend(service.path.glob(pattern))

            api_files.extend(route_files)

            if not api_files:
                return 0.0  # No API files found

            # Analyze all API files
            all_content = ""
            for api_file in api_files[:10]:  # Limit to 10 files
                try:
                    with open(api_file, 'r') as f:
                        content = f.read()
                        all_content += content + "\n"
                except:
                    continue

            if not all_content:
                return 0.0

            # 1. Framework Usage (25 points)
            if 'FastAPI' in all_content:
                score += 25
            elif 'flask' in all_content.lower():
                score += 15  # Flask is acceptable but FastAPI preferred
            total_checks += 25

            # 2. HTTP Methods Coverage (20 points)
            http_methods = ['@app.get', '@app.post', '@app.put', '@app.patch', '@app.delete']
            methods_found = sum(1 for method in http_methods if method in all_content)
            if methods_found >= 3:  # At least GET, POST, PUT
                score += 20
            elif methods_found >= 2:
                score += 15
            elif methods_found >= 1:
                score += 10
            total_checks += 20

            # 3. Response Models/Pydantic Schemas (15 points)
            response_indicators = [
                'response_model', 'BaseModel', 'pydantic', 'from pydantic',
                'Response[', 'List[', 'Dict['  # Type hints for responses
            ]
            response_score = 0
            for indicator in response_indicators:
                if indicator in all_content:
                    response_score += 3
            score += min(15, response_score)
            total_checks += 15

            # 4. Request Models/Validation (15 points)
            request_indicators = [
                'Body(', 'Query(', 'Path(', 'Form(', 'File(',
                'Depends(', 'Security(',  # FastAPI dependency injection
                'Request', 'Body'  # Request handling
            ]
            request_score = 0
            for indicator in request_indicators:
                if indicator in all_content:
                    request_score += 3
            score += min(15, request_score)
            total_checks += 15

            # 5. API Documentation/OpenAPI (10 points)
            docs_indicators = [
                'docs_url', 'redoc_url', 'openapi_url',
                'description=', 'summary=', 'tags=',
                'responses={', 'status_code='
            ]
            docs_score = 0
            for indicator in docs_indicators:
                if indicator in all_content:
                    docs_score += 2
            score += min(10, docs_score)
            total_checks += 10

            # 6. Error Handling (10 points)
            error_indicators = [
                'HTTPException', 'status.HTTP_', 'exception_handler',
                'ValidationError', 'RequestValidationError'
            ]
            error_score = 0
            for indicator in error_indicators:
                if indicator in all_content:
                    error_score += 2
            score += min(10, error_score)
            total_checks += 10

            # 7. RESTful Design Principles (5 points)
            rest_indicators = [
                'status_code=200', 'status_code=201', 'status_code=204',  # Proper status codes
                'status_code=400', 'status_code=401', 'status_code=403', 'status_code=404', 'status_code=500'  # Error codes
            ]
            rest_score = 0
            for indicator in rest_indicators:
                if indicator in all_content:
                    rest_score += 1
            score += min(5, rest_score)
            total_checks += 5

            # 8. Content-Type Headers (5 points)
            content_type_indicators = [
                'json()', 'JSONResponse', 'Response(content=',
                'media_type=', 'application/json'
            ]
            content_score = 0
            for indicator in content_type_indicators:
                if indicator in all_content:
                    content_score += 1
            score += min(5, content_score)
            total_checks += 5

            # 9. Authentication/Security (5 points)
            auth_indicators = [
                'Depends(', 'Security(', 'OAuth2PasswordBearer',
                'HTTPBearer', 'APIKey', 'HTTPBasic'
            ]
            auth_score = 0
            for indicator in auth_indicators:
                if indicator in all_content:
                    auth_score += 1
            score += min(5, auth_score)
            total_checks += 5

            # 10. CORS and Middleware (5 points)
            middleware_indicators = [
                'CORSMiddleware', 'add_middleware', 'middleware',
                'TrustedHost', 'GZip', 'SessionMiddleware'
            ]
            middleware_score = 0
            for indicator in middleware_indicators:
                if indicator in all_content:
                    middleware_score += 1
            score += min(5, middleware_score)
            total_checks += 5

        except Exception as e:
            logger.debug(f"REST compliance check failed: {e}")

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
            score += 20
        total_checks += 20

        # Check for dependency analysis capability
        if HAS_PYDEPS:
            try:
                # Check if we can analyze dependencies (basic check)
                python_files = list(service.path.rglob("*.py"))
                if len(python_files) > 5:  # Only for services with substantial code
                    score += 15  # Bonus for dependency analysis capability
            except Exception as e:
                logger.debug(f"Pydeps check failed: {e}")
        total_checks += 15

        # Check for proper import structure
        try:
            python_files = list(service.path.rglob("*.py"))[:5]
            circular_import_risk = 0

            for py_file in python_files:
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                        imports = re.findall(r'^from\s+services\.', content, re.MULTILINE)
                        if len(imports) > 10:  # Too many internal imports
                            circular_import_risk += 1
                except:
                    continue

            if circular_import_risk == 0:
                score += 10  # Clean import structure
            elif circular_import_risk < 3:
                score += 5   # Moderate import complexity
        except Exception as e:
            logger.debug(f"Import analysis failed: {e}")

        total_checks += 10

        return min(100, (score / total_checks) * 100) if total_checks > 0 else 0

    async def _audit_code_quality(self, service: ServiceInfo) -> Dict[str, Any]:
        """Audit code quality metrics."""
        logger.info(f"Auditing code quality for {service.name}")

        # Get testing details including coverage data
        testing_score, testing_details = await self._check_testing_with_details(service)

        scores = {
            'complexity': await self._check_complexity(service),
            'testing': testing_score,
            'duplication': await self._check_duplication(service),
            'documentation': await self._check_documentation(service),
            'security': await self._check_security(service),
            'dry_principle': await self._check_dry_principle(service),
            'kiss_principle': await self._check_kiss_principle(service)
        }

        # Calculate weighted code quality score (adjusted weights)
        code_quality_score = (
            scores['complexity'] * 0.20 +
            scores['testing'] * 0.25 +
            scores['duplication'] * 0.10 +
            scores['documentation'] * 0.10 +
            scores['security'] * 0.15 +
            scores['dry_principle'] * 0.10 +
            scores['kiss_principle'] * 0.10
        )

        return {
            'score': round(code_quality_score, 2),
            'complexity': scores['complexity'],
            'testing': scores['testing'],
            'duplication': scores['duplication'],
            'documentation': scores['documentation'],
            'security': scores['security'],
            'dry_principle': scores['dry_principle'],
            'kiss_principle': scores['kiss_principle'],
            'coverage_data': getattr(scores.get('testing_details', {}), 'coverage_data', {}),
            'issues': self._identify_code_quality_issues(scores),
            'recommendations': self._generate_code_quality_recommendations(scores)
        }

    async def _check_complexity(self, service: ServiceInfo) -> float:
        """Check code complexity metrics using advanced analysis."""
        score = 100.0  # Start with perfect score, deduct for issues
        total_complexity_score = 0
        total_lines = 0

        try:
            python_files = list(service.path.rglob("*.py"))

            if HAS_RADON:
                # Use radon for advanced complexity analysis
                for py_file in python_files[:10]:  # Analyze first 10 files for performance
                    try:
                        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            total_lines += len(content.split('\n'))

                        # Calculate cyclomatic complexity
                        complexity_results = radon_complexity.cc_visit(content)
                        file_complexity = sum(block.complexity for block in complexity_results)
                        total_complexity_score += file_complexity

                        # Calculate maintainability index
                        try:
                            mi = radon_metrics.mi_visit(content, False)
                            if mi < 50:  # Low maintainability
                                score -= 5
                        except:
                            pass

                    except Exception as e:
                        logger.debug(f"Failed to analyze {py_file}: {e}")
                        continue

                # Evaluate complexity score
                if total_lines > 0:
                    avg_complexity = total_complexity_score / max(1, len(python_files[:10]))
                    if avg_complexity > 15:  # High complexity threshold
                        score -= min(30, (avg_complexity - 15) * 2)
            else:
                # Fallback to basic flake8 analysis
                result = subprocess.run(
                    ['flake8', '--select=C901,E501', '--max-line-length=88', str(service.path)],
                    capture_output=True, text=True, timeout=30
                )

                complexity_violations = len([line for line in result.stdout.split('\n') if 'C901' in line])
                line_length_violations = len([line for line in result.stdout.split('\n') if 'E501' in line])

                score -= min(30, complexity_violations * 5)
                score -= min(20, line_length_violations * 0.5)

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            score -= 10  # Penalty for analysis failure

        # Check file sizes as complexity indicator
        large_files = [f for f in service.path.rglob("*.py") if f.stat().st_size > 100000]  # >100KB
        score -= min(20, len(large_files) * 5)

        return max(0, score)

    async def _check_testing_with_details(self, service: ServiceInfo) -> Tuple[float, Dict[str, Any]]:
        """Check testing coverage and quality with actual coverage measurement."""
        score = 0.0
        coverage_data = {}

        try:
            # Test file coverage (basic heuristic)
            test_ratio = service.tests / max(1, service.files)
            if test_ratio > 0.5:  # Good test coverage
                score += 20
            elif test_ratio > 0.2:  # Moderate coverage
                score += 10
            elif test_ratio > 0:
                score += 5

            # Check for test directories and structure
            test_dirs = list(service.path.glob("**/test*")) + list(service.path.glob("**/tests"))
            if test_dirs:
                score += 15

            # Check for CI/CD testing
            ci_files = list(service.path.glob(".github/workflows/*.yml")) + list(service.path.glob(".gitlab-ci.yml"))
            if ci_files:
                score += 15

            # Check for test configuration
            pytest_files = list(service.path.glob("**/pytest.ini")) + list(service.path.glob("**/setup.cfg"))
            if pytest_files:
                score += 10

            # Attempt actual test coverage measurement
            if HAS_COVERAGE:
                try:
                    logger.debug("Attempting coverage measurement")
                    coverage_data = await self._measure_test_coverage(service)
                    if coverage_data.get('overall_coverage', 0) > 80:
                        score += 25  # Excellent coverage
                    elif coverage_data.get('overall_coverage', 0) > 60:
                        score += 15  # Good coverage
                    elif coverage_data.get('overall_coverage', 0) > 40:
                        score += 10  # Moderate coverage
                    elif coverage_data.get('overall_coverage', 0) > 0:
                        score += 5   # Some coverage

                    # Bonus for coverage reporting
                    if coverage_data.get('has_coverage_report', False):
                        score += 10

                except Exception as e:
                    logger.debug(f"Coverage measurement failed: {e}")

            # Check for test quality indicators
            test_quality_indicators = [
                'pytest.mark.parametrize',  # Parameterized tests
                'pytest.fixture',          # Fixtures
                'mock', 'MagicMock',       # Mocking
                'assertRaises',            # Exception testing
            ]

            test_files = list(service.path.rglob("test_*.py")) + list(service.path.rglob("*_test.py"))
            quality_score = 0

            for test_file in test_files[:5]:  # Check first 5 test files
                try:
                    with open(test_file, 'r') as f:
                        content = f.read()
                        for indicator in test_quality_indicators:
                            if indicator in content:
                                quality_score += 2
                except:
                    continue

            score += min(15, quality_score)  # Max 15 points for test quality

        except Exception as e:
            logger.debug(f"Testing analysis failed: {e}")

        return min(100, score), {'coverage_data': coverage_data}

    async def _check_testing(self, service: ServiceInfo) -> float:
        """Legacy method for backward compatibility."""
        score, _ = await self._check_testing_with_details(service)
        return score

    async def _measure_test_coverage(self, service: ServiceInfo) -> Dict[str, Any]:
        """Measure actual test coverage using coverage.py."""
        coverage_result = {
            'overall_coverage': 0,
            'files_covered': 0,
            'total_files': 0,
            'has_coverage_report': False,
            'coverage_data': {}
        }

        try:
            # Look for existing coverage reports first
            coverage_files = list(service.path.glob("**/coverage.xml")) + \
                           list(service.path.glob("**/.coverage")) + \
                           list(service.path.glob("**/htmlcov/index.html"))

            if coverage_files:
                coverage_result['has_coverage_report'] = True
                # Try to parse coverage.xml if it exists
                coverage_xml = service.path / "coverage.xml"
                if coverage_xml.exists():
                    try:
                        import xml.etree.ElementTree as ET
                        tree = ET.parse(str(coverage_xml))
                        root = tree.getroot()
                        coverage_result['overall_coverage'] = float(root.get('line-rate', 0)) * 100
                    except:
                        pass

            # If no existing reports, try to run tests with coverage
            if coverage_result['overall_coverage'] == 0:
                try:
                    # Check if pytest is available and there are tests
                    test_files = list(service.path.glob("**/test_*.py")) + list(service.path.glob("**/*_test.py"))
                    if test_files:
                        # Try to run a quick coverage check (limit to avoid long runs)
                        import subprocess
                        import tempfile
                        import os

                        with tempfile.TemporaryDirectory() as temp_dir:
                            # Run pytest with coverage (limited to avoid hanging)
                            cmd = [
                                'python', '-m', 'coverage', 'run', '--source', str(service.path),
                                '-m', 'pytest', str(service.path), '--maxfail=1', '--tb=no', '-q',
                                '--disable-warnings'
                            ]

                            try:
                                result = subprocess.run(
                                    cmd,
                                    cwd=str(service.path),
                                    capture_output=True,
                                    text=True,
                                    timeout=30  # 30 second timeout
                                )

                                # Generate coverage report
                                report_cmd = ['python', '-m', 'coverage', 'report', '--include', f'{service.path}/**']
                                report_result = subprocess.run(
                                    report_cmd,
                                    cwd=str(service.path),
                                    capture_output=True,
                                    text=True,
                                    timeout=10
                                )

                                # Parse coverage output
                                if report_result.returncode == 0:
                                    lines = report_result.stdout.split('\n')
                                    for line in lines:
                                        if 'TOTAL' in line and '%' in line:
                                            # Extract percentage from TOTAL line
                                            parts = line.split()
                                            for part in parts:
                                                if '%' in part:
                                                    try:
                                                        coverage_result['overall_coverage'] = float(part.strip('%'))
                                                        break
                                                    except:
                                                        continue
                                            break

                            except subprocess.TimeoutExpired:
                                logger.debug("Coverage measurement timed out")
                            except FileNotFoundError:
                                logger.debug("Coverage or pytest not available")

                except Exception as e:
                    logger.debug(f"Coverage measurement failed: {e}")

        except Exception as e:
            logger.debug(f"Coverage analysis failed: {e}")

        return coverage_result

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
        """Check documentation quality using interrogate for actual docstring coverage."""
        score = 0.0

        try:
            # Use interrogate for accurate docstring coverage if available
            if HAS_INTERROGATE:
                try:
                    logger.debug("Using interrogate for documentation analysis")
                    from interrogate import coverage as interrogate_coverage

                    # Run interrogate on the service
                    interrogate_config = interrogate_coverage.InterrogateConfig(
                        paths=[str(service.path)],
                        ignore_module=True,
                        ignore_private=True,
                        ignore_magic=True,
                        ignore_init_method=True,
                        ignore_init_module=True
                    )

                    results = interrogate_coverage.InterrogateResults()
                    results.from_config(interrogate_config)

                    # Get overall coverage percentage
                    docstring_coverage = results.get_coverage()
                    score += min(60, docstring_coverage * 100)  # Max 60 points for docstring coverage

                    # Bonus for detailed results
                    detailed_results = results.get_detailed_results()
                    if detailed_results:
                        score += 10  # Bonus for having detailed documentation analysis

                except Exception as e:
                    logger.debug(f"Interrogate analysis failed: {e}")
                    # Fall back to basic analysis

            # Fallback to basic documentation analysis
            if score == 0:
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

            # Check for README and other documentation files
            readme_files = list(service.path.glob("README*")) + list(service.path.glob("*.md"))
            if readme_files:
                score += min(20, len(readme_files) * 10)  # Max 20 points for README files

            # Check for API documentation setup
            main_file = service.path / "main.py"
            if main_file.exists():
                try:
                    with open(main_file, 'r') as f:
                        content = f.read()
                        if 'docs_url' in content or 'redoc_url' in content:
                            score += 15  # API documentation configured
                        if 'description=' in content and 'FastAPI(' in content:
                            score += 5  # Detailed API description
                except:
                    pass

            # Check for type hints usage
            type_hints_score = 0
            python_files = list(service.path.rglob("*.py"))[:3]  # Check first 3 files
            for py_file in python_files:
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                        # Look for type hints
                        if '->' in content and 'def ' in content:
                            type_hints_score += 5
                        if ': ' in content and ('str' in content or 'int' in content or 'List' in content):
                            type_hints_score += 5
                except:
                    continue

            score += min(10, type_hints_score)  # Max 10 points for type hints

        except Exception as e:
            logger.debug(f"Documentation analysis failed: {e}")

        return min(100, score)

    async def _check_security(self, service: ServiceInfo) -> float:
        """Check security vulnerabilities and best practices using advanced analysis."""
        score = 100.0  # Start with perfect score
        security_findings = {
            'high_severity': 0,
            'medium_severity': 0,
            'low_severity': 0,
            'hardcoded_secrets': 0,
            'injection_vulnerabilities': 0,
            'unsafe_functions': 0,
            'weak_crypto': 0
        }

        try:
            logger.debug(f"Starting security analysis for {service.name}")
            python_files = list(service.path.rglob("*.py"))
            logger.debug(f"Found {len(python_files)} Python files")

            # Bandit-based comprehensive security analysis (skip for large services)
            if HAS_BANDIT and service.lines <= 50000:  # Only use bandit for smaller services
                logger.debug("Using bandit for security analysis")
                try:
                    from bandit.core import manager as bandit_manager
                    from bandit.core import config as bandit_config

                    # Configure bandit for comprehensive scanning
                    b_config = bandit_config.BanditConfig()
                    b_config.set_option('profiles', ['B101', 'B102', 'B103', 'B104', 'B105', 'B106', 'B107', 'B108', 'B201', 'B301', 'B302', 'B303', 'B304', 'B305', 'B306', 'B307', 'B308', 'B309', 'B310', 'B311', 'B312', 'B313', 'B314', 'B315', 'B316', 'B317', 'B318', 'B319', 'B320', 'B321', 'B322', 'B323', 'B324', 'B325', 'B401', 'B402', 'B403', 'B404', 'B405', 'B406', 'B407', 'B408', 'B409', 'B410', 'B411', 'B412', 'B413', 'B414', 'B415', 'B416', 'B417', 'B418', 'B419', 'B420', 'B421', 'B422', 'B423', 'B424', 'B425', 'B426', 'B501', 'B502', 'B503', 'B504', 'B505', 'B506', 'B507', 'B508', 'B509', 'B510', 'B511', 'B512', 'B513', 'B601', 'B602', 'B603', 'B604', 'B605', 'B606', 'B607', 'B608', 'B609', 'B610', 'B611', 'B612'])

                    b_manager = bandit_manager.BanditManager(b_config, 'file')

                    # Analyze files with bandit (with timeout protection)
                    import signal

                    def timeout_handler(signum, frame):
                        raise TimeoutError("Bandit analysis timed out")

                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(30)  # 30 second timeout

                    try:
                        logger.debug("Starting bandit file processing")
                        for i, py_file in enumerate(python_files[:3]):  # Reduced to 3 files for testing
                            logger.debug(f"Processing file {i+1}/3: {py_file.name}")
                            try:
                                # Skip very large files
                                file_size = py_file.stat().st_size
                                if file_size > 500000:  # >500KB
                                    logger.debug(f"Skipping large file {py_file.name} ({file_size} bytes)")
                                    continue
                                logger.debug(f"Running bandit on {py_file.name}")
                                b_manager.process_file(str(py_file))
                                logger.debug(f"Bandit completed on {py_file.name}")
                            except Exception as e:
                                logger.debug(f"Bandit failed on {py_file}: {e}")

                        logger.debug("Getting bandit results")
                        # Process bandit results
                        issues = b_manager.get_issue_list()
                        logger.debug(f"Bandit found {len(issues)} issues")
                    finally:
                        signal.alarm(0)  # Cancel the alarm
                    for issue in issues:
                        if issue.severity == 'HIGH':
                            security_findings['high_severity'] += 1
                        elif issue.severity == 'MEDIUM':
                            security_findings['medium_severity'] += 1
                        else:
                            security_findings['low_severity'] += 1

                        # Categorize by issue type
                        if 'secret' in issue.test_id.lower() or 'password' in str(issue.text).lower():
                            security_findings['hardcoded_secrets'] += 1
                        elif 'injection' in issue.test_id.lower() or 'sql' in str(issue.text).lower():
                            security_findings['injection_vulnerabilities'] += 1
                        elif issue.test_id in ['B304', 'B305', 'B306', 'B307', 'B602', 'B603', 'B604', 'B605', 'B606']:
                            security_findings['unsafe_functions'] += 1
                        elif 'crypto' in issue.test_id.lower() or 'hash' in str(issue.text).lower():
                            security_findings['weak_crypto'] += 1

                except Exception as e:
                    logger.debug(f"Bandit analysis failed: {e}")

            # Fallback pattern-based security checks (optimized for performance)
            logger.debug("Starting fallback security checks")
            max_files_to_check = min(3, len(python_files))  # Very aggressive limit
            if service.lines > 50000:  # Large codebase
                max_files_to_check = min(2, len(python_files))  # Even more aggressive for very large services
            nodes_processed = 0
            max_nodes_per_file = 300  # Further reduced AST nodes per file

            logger.debug(f"Processing {max_files_to_check} files for security analysis")
            for i, py_file in enumerate(python_files[:max_files_to_check]):
                logger.debug(f"Processing file {i+1}/{max_files_to_check}: {py_file.name}")
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()

                        # Skip very large files to avoid hanging
                        if len(content) > 200000:  # Reduced to 200KB
                            logger.debug(f"Skipping large file {py_file.name} ({len(content)} chars)")
                            continue

                        logger.debug(f"Analyzing {py_file.name} ({len(content)} chars)")

                        # Enhanced secret detection with AST (limited processing)
                        try:
                            logger.debug(f"Parsing AST for {py_file.name}")
                            tree = ast.parse(content)
                            file_nodes_processed = 0

                            for node in ast.walk(tree):
                                file_nodes_processed += 1
                                if file_nodes_processed > max_nodes_per_file:
                                    logger.debug(f"Reached node limit ({max_nodes_per_file}) for {py_file.name}")
                                    break  # Limit processing per file

                                if isinstance(node, ast.Assign):
                                    # Check for hardcoded secrets in assignments
                                    if isinstance(node.value, ast.Str) and len(node.value.s) > 10:
                                        var_name = None
                                        if isinstance(node.targets[0], ast.Name):
                                            var_name = node.targets[0].id.lower()
                                        elif isinstance(node.targets[0], ast.Attribute):
                                            var_name = node.targets[0].attr.lower()

                                        if var_name and any(keyword in var_name for keyword in ['password', 'secret', 'key', 'token', 'credential']):
                                            security_findings['hardcoded_secrets'] += 1

                            nodes_processed += file_nodes_processed
                            logger.debug(f"Processed {file_nodes_processed} AST nodes for {py_file.name}")

                        except SyntaxError:
                            logger.debug(f"Syntax error in {py_file.name}")
                        except Exception as e:
                            logger.debug(f"AST analysis failed for {py_file}: {e}")

                except Exception as e:
                    logger.debug(f"File analysis failed for {py_file}: {e}")
                    continue

            logger.debug(f"Security analysis completed. Processed {nodes_processed} total AST nodes")

            # Now do pattern-based security checks for all files (with timeout protection)
            logger.debug("Starting pattern-based security checks")
            import time
            start_time = time.time()

            for i, py_file in enumerate(python_files[:max_files_to_check]):
                # Check timeout every 10 files
                if i % 10 == 0 and time.time() - start_time > 30:  # 30 second timeout
                    logger.debug(f"Security pattern analysis timed out after {i} files")
                    break

                logger.debug(f"Pattern checking file {i+1}/{max_files_to_check}: {py_file.name}")
                try:
                    # Skip very large files to prevent regex hangs
                    file_size = py_file.stat().st_size
                    if file_size > 100000:  # >100KB
                        logger.debug(f"Skipping large file {py_file.name} ({file_size} bytes)")
                        continue

                    with open(py_file, 'r') as f:
                        content = f.read()

                    # Limit content size to prevent regex hangs
                    if len(content) > 50000:  # >50KB
                        logger.debug(f"Limiting content for {py_file.name} ({len(content)} chars)")
                        content = content[:50000]

                    # Enhanced SQL injection detection (simplified patterns)
                    if '%' in content and ('execute' in content.lower() or 'cursor' in content.lower()):
                        security_findings['injection_vulnerabilities'] += 1

                    # Enhanced unsafe function detection
                    unsafe_functions = ['eval(', 'exec(', 'pickle.loads(', 'yaml.load(', 'input(', 'raw_input(']
                    for func in unsafe_functions:
                        if func in content:
                            security_findings['unsafe_functions'] += 1

                    # Check for weak cryptography
                    weak_crypto = ['md5(', 'sha1(', 'des(', 'rc4(']
                    for crypto in weak_crypto:
                        if crypto in content.lower():
                            security_findings['weak_crypto'] += 1

                    # Check for insecure HTTPS patterns (simplified)
                    if 'http://' in content and ('urllib' in content or 'requests' in content or 'httpx' in content):
                        security_findings['high_severity'] += 1

                    logger.debug(f"Completed pattern check for {py_file.name}")

                except Exception as e:
                    logger.debug(f"Pattern analysis failed on {py_file}: {e}")
                    continue

            logger.debug("Pattern-based security checks completed")

            # Calculate security score based on findings
            total_issues = sum(security_findings.values())

            # Severity-based scoring
            score -= security_findings['high_severity'] * 10  # -10 per high severity
            score -= security_findings['medium_severity'] * 5  # -5 per medium severity
            score -= security_findings['low_severity'] * 2     # -2 per low severity

            # Category-based penalties
            score -= security_findings['hardcoded_secrets'] * 15    # Critical
            score -= security_findings['injection_vulnerabilities'] * 12  # Critical
            score -= security_findings['unsafe_functions'] * 8     # High
            score -= security_findings['weak_crypto'] * 6          # Medium

            # Bonuses for security best practices
            security_indicators = [
                'validate_sql_identifier',
                'bleach.clean',
                'html.escape',
                'secrets.token',
                'cryptography',
                'bcrypt',
                'argon2'
            ]

            found_indicators = 0
            for indicator in security_indicators:
                if any(indicator in str(service.path.glob("**/*.py")) for _ in [None]):
                    found_indicators += 1

            score += found_indicators * 5  # +5 per security best practice found

            # Additional bonus for comprehensive security setup
            if found_indicators >= 3:
                score += 10  # Bonus for security-conscious codebase

        except Exception as e:
            logger.error(f"Security analysis completely failed: {e}")
            score -= 20

        return max(0, min(100, score))

    async def _check_dry_principle(self, service: ServiceInfo) -> float:
        """Check DRY (Don't Repeat Yourself) principle compliance with performance safeguards."""
        score = 100.0  # Start with perfect score
        dry_violations = 0

        try:
            python_files = list(service.path.rglob("*.py"))
            logger.debug(f"DRY analysis: Found {len(python_files)} Python files")

            # Limit analysis based on codebase size to prevent hanging
            max_files_to_analyze = min(3, len(python_files))  # Very aggressive limit
            if service.lines > 50000:  # Large codebase
                max_files_to_analyze = min(2, len(python_files))  # Even more aggressive for very large services

            logger.debug(f"DRY analysis: Analyzing {max_files_to_analyze} files")
            import time
            dry_start_time = time.time()

            # Check for duplicate import blocks (simplified)
            import_blocks = []
            for py_file in python_files[:max_files_to_analyze]:
                # Timeout check
                if time.time() - dry_start_time > 20:  # 20 second timeout for DRY analysis
                    logger.debug("DRY analysis timed out")
                    break

                try:
                    with open(py_file, 'r') as f:
                        content = f.read()

                        if len(content) > 50000:  # Skip very large files
                            continue

                        lines = content.split('\n')

                        # Extract import blocks (consecutive import statements)
                        current_imports = []
                        for line in lines[:30]:  # Reduced from 50
                            line = line.strip()
                            if line.startswith('from ') or line.startswith('import '):
                                current_imports.append(line)
                            elif current_imports and line:  # End of import block
                                if len(current_imports) > 2:  # Significant import block
                                    import_blocks.append(tuple(sorted(current_imports)))
                                current_imports = []

                except Exception:
                    continue

            # Check for duplicate import blocks
            import_counts = {}
            for block in import_blocks:
                import_counts[block] = import_counts.get(block, 0) + 1

            duplicate_imports = sum(count - 1 for count in import_counts.values() if count > 1)
            dry_violations += duplicate_imports * 5

            # Simplified duplicate name checking
            function_signatures = []
            for py_file in python_files[:max_files_to_analyze]:
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                        if len(content) > 50000:
                            continue

                        # Extract function definitions (simplified)
                        functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', content)
                        function_signatures.extend(functions[:20])  # Limit per file

                except Exception:
                    continue

            # Check for duplicate names
            name_counts = {}
            for name in function_signatures:
                if len(name) > 3:  # Ignore very short names
                    name_counts[name] = name_counts.get(name, 0) + 1

            duplicate_names = sum(count - 1 for count in name_counts.values() if count > 1)
            dry_violations += duplicate_names * 3

            # Skip complex AST analysis for large codebases to prevent hanging
            if service.lines <= 50000:
                # Check for repeated string literals (simplified)
                string_literals = []
                for py_file in python_files[:max_files_to_analyze]:
                    try:
                        with open(py_file, 'r') as f:
                            content = f.read()
                            if len(content) > 50000:
                                continue

                            # Extract string literals (simplified)
                            strings = re.findall(r'["\']([^"\']{15,})["\']', content)  # Longer strings only
                            string_literals.extend(strings[:10])  # Limit per file

                    except Exception:
                        continue

                # Count repeated strings
                string_counts = {}
                for string in string_literals:
                    string_counts[string] = string_counts.get(string, 0) + 1

                repeated_strings = sum(count - 1 for count in string_counts.values() if count > 1)
                dry_violations += repeated_strings * 3

            # Calculate DRY score based on violations
            score -= min(60, dry_violations * 2)

            # Bonus for good DRY practices
            dry_indicators = [
                'BaseService', 'BaseRepository', 'BaseEntity',
                'create_success_response', 'create_error_response',
                'validate_sql_identifier', 'sanitize_sql_identifier'
            ]

            found_indicators = 0
            for indicator in dry_indicators:
                if any(indicator in str(service.path.glob("**/*.py")) for _ in [None]):
                    found_indicators += 1

            score += found_indicators * 3

            logger.debug(f"DRY analysis completed: score={score}, violations={dry_violations}")

        except Exception as e:
            logger.debug(f"DRY analysis failed: {e}")
            score -= 10

        return max(0, min(100, score))

    async def _check_kiss_principle(self, service: ServiceInfo) -> float:
        """Check KISS (Keep It Simple Stupid) principle compliance with performance safeguards."""
        score = 100.0  # Start with perfect score
        complexity_violations = 0

        try:
            python_files = list(service.path.rglob("*.py"))
            logger.debug(f"KISS analysis: Found {len(python_files)} Python files")

            # Limit analysis based on codebase size
            max_files_to_analyze = min(3, len(python_files))  # Very aggressive limit
            if service.lines > 50000:  # Large codebase
                max_files_to_analyze = min(2, len(python_files))  # Even more aggressive for very large services

            logger.debug(f"KISS analysis: Analyzing {max_files_to_analyze} files")
            import time
            kiss_start_time = time.time()

            for py_file in python_files[:max_files_to_analyze]:
                # Timeout check
                if time.time() - kiss_start_time > 20:  # 20 second timeout for KISS analysis
                    logger.debug("KISS analysis timed out")
                    break

                try:
                    with open(py_file, 'r') as f:
                        content = f.read()

                        if len(content) > 50000:  # Skip very large files
                            continue

                        # Use regex for basic complexity checks (faster than AST for large files)
                        lines = content.split('\n')

                        # Check function complexity via regex
                        functions = re.findall(r'def\s+\w+\s*\([^)]*\):', content)
                        for func_match in functions[:20]:  # Limit per file
                            # Extract function body (simplified)
                            func_start = content.find(func_match)
                            if func_start != -1:
                                func_body = content[func_start:func_start + 1000]  # First 1000 chars of function
                                body_lines = len(func_body.split('\n'))

                                if body_lines > 50:  # Very long function
                                    complexity_violations += (body_lines - 50) // 10

                                # Count parameters in function signature
                                param_match = re.search(r'def\s+\w+\s*\(([^)]*)\)', func_match)
                                if param_match:
                                    params = param_match.group(1)
                                    param_count = len([p for p in params.split(',') if p.strip() and not p.strip().startswith('*')])
                                    if param_count > 5:
                                        complexity_violations += (param_count - 5) * 2

                        # Check class complexity
                        classes = re.findall(r'class\s+(\w+)', content)
                        for class_name in classes[:10]:  # Limit per file
                            # Count methods in class (simplified)
                            class_pattern = rf'class\s+{re.escape(class_name)}\b.*?(?=class|\Z)'
                            class_match = re.search(class_pattern, content, re.DOTALL)
                            if class_match:
                                class_content = class_match.group(0)
                                methods = len(re.findall(r'def\s+\w+\s*\(', class_content))
                                if methods > 15:
                                    complexity_violations += (methods - 15) * 2

                        # Check for complex patterns (simplified)
                        # Count nested if statements
                        nested_ifs = re.findall(r'if.*:\s*if', content, re.IGNORECASE)
                        complexity_violations += len(nested_ifs) * 2

                        # Count very long lines
                        long_lines = [line for line in lines if len(line) > 120]
                        complexity_violations += len(long_lines) // 5

                        # Check for complex comprehensions
                        complex_comprehensions = re.findall(r'\[.*\[.*\].*\]', content)  # Nested list comprehensions
                        complexity_violations += len(complex_comprehensions) * 3

                except Exception as e:
                    logger.debug(f"KISS analysis failed for {py_file}: {e}")
                    continue

            # Check for over-engineering patterns (simplified)
            for py_file in python_files[:max_files_to_analyze]:
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()

                        if len(content) > 50000:  # Skip large files
                            continue

                        # Check for excessive use of advanced Python features (simplified)
                        advanced_features = [
                            '__slots__', '@property', 'metaclass', '__new__'
                        ]

                        for feature in advanced_features:
                            if feature in content:
                                complexity_violations += 1  # Simplified penalty

                        # Check for too many decorators
                        decorators = re.findall(r'@\w+', content)
                        if len(decorators) > 15:  # Too many decorators
                            complexity_violations += (len(decorators) - 15) // 3

                except Exception:
                    continue

            # Calculate KISS score
            score -= min(70, complexity_violations)  # Max 70 points deduction

            # Bonus for simplicity
            simple_indicators = [
                'SimpleNamespace',  # Simple data structures
                '# TODO', '# FIXME',  # Acknowledged technical debt
                'NotImplementedError',  # Explicitly marking incomplete features
            ]

            simple_violations = 0
            for indicator in simple_indicators:
                if any(indicator in str(service.path.glob("**/*.py")) for _ in [None]):
                    simple_violations += 1

            score -= simple_violations * 2  # Penalty for technical debt indicators

            # Bonus for clean, simple code patterns
            clean_patterns = [
                'if __name__ == "__main__":',  # Proper script structure
                'def main():',  # Clear entry points
                'logger = logging.getLogger(__name__)',  # Proper logging
            ]

            found_patterns = 0
            for pattern in clean_patterns:
                if any(pattern in str(service.path.glob("**/*.py")) for _ in [None]):
                    found_patterns += 1

            score += found_patterns * 5  # Bonus for good practices

        except Exception as e:
            logger.debug(f"KISS analysis failed: {e}")
            score -= 10

        return max(0, min(100, score))


    async def _audit_performance(self, service: ServiceInfo) -> Dict[str, Any]:
        """Audit performance characteristics with real-time monitoring."""
        logger.info(f"Auditing performance for {service.name}")

        # Collect system resource metrics during analysis
        system_metrics = await self._collect_system_metrics()

        scores = {
            'runtime': await self._check_runtime_performance(service),
            'database': await self._check_database_performance(service),
            'resources': await self._check_resource_usage(service)
        }

        # Adjust scores based on system resource usage
        if system_metrics:
            scores = self._adjust_scores_for_system_load(scores, system_metrics)

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
            'system_metrics': system_metrics,
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

                    # Check for resource monitoring with psutil
                    if HAS_PSUTIL and 'psutil' in content:
                        score += 10  # Good resource monitoring

        except:
            pass

        # AST-based analysis for performance patterns
        try:
            for py_file in python_files[:2]:
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()

                    tree = ast.parse(content)

                    # Check for inefficient patterns
                    inefficient_patterns = 0

                    for node in ast.walk(tree):
                        # Check for nested loops (potential N^2 complexity)
                        if isinstance(node, ast.For) and any(isinstance(child, ast.For) for child in ast.walk(node)):
                            inefficient_patterns += 1

                        # Check for string concatenation in loops
                        if isinstance(node, ast.For):
                            for child in ast.walk(node):
                                if isinstance(child, ast.BinOp) and isinstance(child.op, ast.Add):
                                    inefficient_patterns += 0.5

                        # Check for large list comprehensions
                        if isinstance(node, ast.ListComp):
                            comprehension_size = len(ast.dump(node))
                            if comprehension_size > 1000:  # Large comprehension
                                inefficient_patterns += 1

                    score -= min(15, inefficient_patterns * 3)

                except (SyntaxError, UnicodeDecodeError):
                    continue

        except Exception as e:
            logger.debug(f"AST analysis failed: {e}")

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

    async def _collect_system_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect real-time system resource metrics."""
        if not HAS_PSUTIL:
            return None

        try:
            import psutil
            import time

            # Collect metrics over a short interval for accuracy
            cpu_before = psutil.cpu_percent(interval=0.1)
            mem_before = psutil.virtual_memory()

            # Brief pause to get more accurate readings
            await asyncio.sleep(0.2)

            cpu_after = psutil.cpu_percent(interval=0.1)
            mem_after = psutil.virtual_memory()

            # Disk I/O
            disk_io = psutil.disk_io_counters()
            net_io = psutil.net_io_counters()

            return {
                'cpu_percent': round((cpu_before + cpu_after) / 2, 1),
                'memory_percent': round(mem_after.percent, 1),
                'memory_used_gb': round(mem_after.used / (1024**3), 2),
                'memory_available_gb': round(mem_after.available / (1024**3), 2),
                'disk_read_mb': round(disk_io.read_bytes / (1024**2), 2) if disk_io else 0,
                'disk_write_mb': round(disk_io.write_bytes / (1024**2), 2) if disk_io else 0,
                'network_sent_mb': round(net_io.bytes_sent / (1024**2), 2) if net_io else 0,
                'network_recv_mb': round(net_io.bytes_recv / (1024**2), 2) if net_io else 0,
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.debug(f"System metrics collection failed: {e}")
            return None

    def _adjust_scores_for_system_load(self, scores: Dict[str, float], system_metrics: Dict[str, Any]) -> Dict[str, float]:
        """Adjust performance scores based on current system load."""
        adjusted_scores = scores.copy()

        # Reduce scores if system is heavily loaded (could indicate performance issues)
        if system_metrics.get('cpu_percent', 0) > 80:
            adjusted_scores['runtime'] = max(0, adjusted_scores['runtime'] - 10)
            adjusted_scores['resources'] = max(0, adjusted_scores['resources'] - 10)

        if system_metrics.get('memory_percent', 0) > 85:
            adjusted_scores['resources'] = max(0, adjusted_scores['resources'] - 15)
            adjusted_scores['database'] = max(0, adjusted_scores['database'] - 5)

        # Bonus for good resource availability
        if system_metrics.get('memory_percent', 0) < 50:
            adjusted_scores['resources'] = min(100, adjusted_scores['resources'] + 5)

        if system_metrics.get('cpu_percent', 0) < 30:
            adjusted_scores['runtime'] = min(100, adjusted_scores['runtime'] + 5)

        return adjusted_scores

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
        """Check error handling quality with enterprise pattern detection."""
        score = 0.0

        try:
            python_files = list(service.path.rglob("*.py"))

            # 1. Domain Exception Analysis (40 points)
            domain_exceptions = await self._analyze_domain_exceptions(service)
            score += domain_exceptions

            # 2. Error Handling Patterns (35 points)
            patterns_score = await self._analyze_error_patterns(service)
            score += patterns_score

            # 3. Resilience Patterns (25 points)
            resilience_score = await self._analyze_resilience_patterns(service)
            score += resilience_score

        except Exception as e:
            logger.debug(f"Error handling analysis failed: {e}")

        return min(100, score)

    async def _analyze_domain_exceptions(self, service: ServiceInfo) -> float:
        """Analyze domain-specific exception implementation."""
        score = 0.0

        exception_files = list(service.path.rglob("**/exceptions.py")) + \
                         list(service.path.rglob("**/exception.py"))

        if not exception_files:
            return 0.0

        score += 5  # Basic exception module exists

        # Analyze exception definitions
        domain_exceptions_found = []
        enterprise_patterns_found = []

        for exc_file in exception_files[:3]:  # Analyze first 3 exception files
            try:
                with open(exc_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content, filename=str(exc_file))

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check for domain-specific exceptions
                        base_names = []
                        for base in node.bases:
                            if hasattr(base, 'id'):
                                base_names.append(base.id)
                            elif hasattr(base, 'attr'):
                                base_names.append(base.attr)

                        # Domain exceptions inheriting from DomainError
                        if 'DomainError' in base_names or 'ValidationError' in base_names:
                            domain_exceptions_found.append(node.name)

                        # Enterprise patterns (circuit breaker, saga, etc.)
                        enterprise_keywords = ['Circuit', 'Saga', 'Event', 'Stream', 'Tracing']
                        if any(keyword in node.name for keyword in enterprise_keywords):
                            enterprise_patterns_found.append(node.name)

            except Exception as e:
                logger.debug(f"Error analyzing exception file {exc_file}: {e}")
                continue

        # Award points for domain exceptions
        if domain_exceptions_found:
            score += min(15, len(domain_exceptions_found) * 3)  # Up to 15 points

        # Award points for enterprise patterns
        if enterprise_patterns_found:
            score += min(10, len(enterprise_patterns_found) * 2)  # Up to 10 points

        # Check for exception hierarchy imports
        for exc_file in exception_files[:3]:
            try:
                with open(exc_file, 'r') as f:
                    content = f.read()
                    if 'from services.shared.domain.exceptions import' in content:
                        score += 10  # Proper exception hierarchy
                        break
            except:
                continue

        return min(40, score)

    async def _analyze_error_patterns(self, service: ServiceInfo) -> float:
        """Analyze error handling patterns and best practices."""
        score = 0.0

        python_files = list(service.path.rglob("*.py"))
        if not python_files:
            return 0.0

        files_analyzed = 0
        pattern_scores = {
            'try_except_blocks': 0,
            'specific_exceptions': 0,
            'logging_integration': 0,
            'error_context': 0,
            'graceful_degradation': 0
        }

        for py_file in python_files[:10]:  # Analyze first 10 files
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content, filename=str(py_file))

                # Analyze error patterns using AST
                for node in ast.walk(tree):
                    # Check for try/except blocks
                    if isinstance(node, ast.Try):
                        pattern_scores['try_except_blocks'] += 1

                        # Check for specific exception handling
                        for handler in node.handlers:
                            if handler.type:
                                if hasattr(handler.type, 'id'):
                                    # Specific exceptions (not bare except)
                                    if handler.type.id not in ['Exception', 'BaseException']:
                                        pattern_scores['specific_exceptions'] += 1

                    # Check for logging in exception context
                    elif isinstance(node, ast.Call):
                        if hasattr(node.func, 'attr'):
                            if node.func.attr in ['error', 'exception', 'critical']:
                                # Check if in exception context
                                parent = getattr(node, '_parent', None)
                                if parent and isinstance(parent, ast.ExceptHandler):
                                    pattern_scores['logging_integration'] += 1

                # Check for error context patterns
                if 'error_context' in content or 'ErrorContext' in content:
                    pattern_scores['error_context'] += 1

                # Check for graceful degradation patterns
                graceful_indicators = ['fallback', 'degrade', 'circuit', 'timeout']
                if any(indicator in content.lower() for indicator in graceful_indicators):
                    pattern_scores['graceful_degradation'] += 1

                files_analyzed += 1

            except Exception as e:
                logger.debug(f"Error analyzing file {py_file}: {e}")
                continue

        # Calculate pattern scores
        if files_analyzed > 0:
            # Try/except blocks (up to 10 points)
            try_except_ratio = min(1.0, pattern_scores['try_except_blocks'] / (files_analyzed * 2))
            score += try_except_ratio * 10

            # Specific exceptions (up to 8 points)
            specific_ratio = min(1.0, pattern_scores['specific_exceptions'] / files_analyzed)
            score += specific_ratio * 8

            # Logging integration (up to 7 points)
            logging_ratio = min(1.0, pattern_scores['logging_integration'] / files_analyzed)
            score += logging_ratio * 7

            # Error context (up to 5 points)
            context_ratio = min(1.0, pattern_scores['error_context'] / files_analyzed)
            score += context_ratio * 5

            # Graceful degradation (up to 5 points)
            graceful_ratio = min(1.0, pattern_scores['graceful_degradation'] / files_analyzed)
            score += graceful_ratio * 5

        return min(35, score)

    async def _analyze_resilience_patterns(self, service: ServiceInfo) -> float:
        """Analyze resilience and fault tolerance patterns."""
        score = 0.0

        python_files = list(service.path.rglob("*.py"))
        resilience_indicators = {
            'circuit_breaker': ['CircuitBreaker', 'circuit', 'breaker'],
            'retry_logic': ['retry', 'Retry', 'backoff', 'exponential'],
            'timeout_handling': ['timeout', 'Timeout', 'deadline'],
            'fallback_mechanisms': ['fallback', 'Fallback', 'degrade'],
            'bulkhead_pattern': ['bulkhead', 'isolation', 'resource'],
            'health_checks': ['health', 'Health', 'liveness', 'readiness']
        }

        pattern_found = {pattern: False for pattern in resilience_indicators}

        for py_file in python_files[:15]:  # Analyze first 15 files
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                for pattern, keywords in resilience_indicators.items():
                    if any(keyword in content for keyword in keywords):
                        pattern_found[pattern] = True

            except Exception as e:
                logger.debug(f"Error analyzing file {py_file}: {e}")
                continue

        # Award points for each resilience pattern found
        pattern_points = {
            'circuit_breaker': 6,
            'retry_logic': 5,
            'timeout_handling': 4,
            'fallback_mechanisms': 4,
            'bulkhead_pattern': 3,
            'health_checks': 3
        }

        for pattern, found in pattern_found.items():
            if found:
                score += pattern_points[pattern]

        return min(25, score)

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
        """Check DevOps and deployment readiness including type checking and dependency security."""
        score = 0.0

        # Check for CI/CD
        ci_files = list(service.path.glob(".github/workflows/*.yml")) + list(service.path.glob(".gitlab-ci.yml"))
        if ci_files:
            score += 20

        # Check for Docker
        docker_files = list(service.path.glob("Dockerfile*"))
        if docker_files:
            score += 15

        # Check for configuration management
        config_files = list(service.path.glob("config*")) + list(service.path.glob("*.yaml")) + list(service.path.glob("*.yml"))
        if config_files:
            score += 10

        # Check for health checks
        try:
            main_file = service.path / "main.py"
            if main_file.exists():
                with open(main_file, 'r') as f:
                    content = f.read()
                    if '/health' in content:
                        score += 10
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
                            score += 10
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
                            score += 8
                            break
                except:
                    continue
        except:
            pass

        # Check for type checking with mypy
        if HAS_MYPY:
            try:
                requirements_file = service.path / "requirements.txt"
                setup_file = service.path / "setup.py"
                pyproject_file = service.path / "pyproject.toml"

                if requirements_file.exists() or setup_file.exists() or pyproject_file.exists():
                    # Mypy configuration indicates type checking awareness
                    mypy_config = service.path / "mypy.ini"
                    setup_cfg = service.path / "setup.cfg"
                    pyproject = service.path / "pyproject.toml"

                    if mypy_config.exists() or setup_cfg.exists() or pyproject.exists():
                        score += 12  # Type checking configured
                    else:
                        score += 6   # Dependencies suggest type checking possible
            except Exception as e:
                logger.debug(f"Mypy check failed: {e}")

        # Check for dependency security with safety
        if HAS_SAFETY:
            try:
                requirements_file = service.path / "requirements.txt"
                if requirements_file.exists():
                    score += 8  # Dependency vulnerability checking possible
                    # Could run safety check here but it's slow, so just check for setup
            except Exception as e:
                logger.debug(f"Safety check failed: {e}")

        # Check for linting configuration
        lint_configs = [
            "flake8", ".flake8", "setup.cfg", "pyproject.toml", "tox.ini",
            ".pylintrc", "pylint.rc", ".bandit"
        ]
        lint_config_found = False
        for config in lint_configs:
            if list(service.path.glob(f"**/{config}")) or list(service.path.glob(config)):
                lint_config_found = True
                break

        if lint_config_found:
            score += 7  # Code quality tooling configured

        return min(100, score)

    def _calculate_overall_score(self, results: AuditResults) -> float:
        """Calculate overall service score with structural and complexity penalties."""
        architecture_score = results.architecture.get('score', 0)
        code_quality_score = results.code_quality.get('score', 0)
        performance_score = results.performance.get('score', 0)
        maintainability_score = results.maintainability.get('score', 0)

        # Base weighted score
        overall_score = (
            architecture_score * self.DIMENSION_WEIGHTS['architecture'] +
            code_quality_score * self.DIMENSION_WEIGHTS['code_quality'] +
            performance_score * self.DIMENSION_WEIGHTS['performance'] +
            maintainability_score * self.DIMENSION_WEIGHTS['maintainability']
        )

        # Additional penalties based on structural patterns and file metrics
        file_metrics = results.architecture.get('file_metrics', {})
        ddd_compliance = results.architecture.get('ddd_compliance', 0)
        ddd_issues = results.architecture.get('ddd_issues', [])
        test_quality = results.architecture.get('test_quality', {})
        linting_quality = results.architecture.get('linting_quality', {})
        endpoint_analysis = results.architecture.get('endpoint_analysis', {})

        # Factor in DDD compliance more heavily (additional 10% weight)
        ddd_bonus = (ddd_compliance - 50) * 0.1  # Bonus/penalty based on DDD score vs 50 baseline
        overall_score += ddd_bonus

        # Additional penalties for DDD architecture violations
        ddd_violation_penalty = len(ddd_issues) * 0.5  # 0.5 points per DDD violation
        overall_score -= min(ddd_violation_penalty, 5)  # Max 5 point penalty

        # Test quality penalties and bonuses
        test_failures = test_quality.get('test_failures', 0)
        test_coverage = test_quality.get('test_coverage', 0.0)

        # Penalties for test failures (up to -8 points)
        if test_failures > 0:
            test_failure_penalty = min(test_failures * 0.5, 8)  # 0.5 points per failure
            overall_score -= test_failure_penalty

        # Bonuses/penalties for test coverage
        if test_coverage >= 80:
            overall_score += 3  # Bonus for excellent coverage
        elif test_coverage >= 70:
            overall_score += 2  # Bonus for good coverage
        elif test_coverage >= 60:
            overall_score += 1  # Bonus for adequate coverage
        elif test_coverage >= 40:
            overall_score -= 1  # Minor penalty for low coverage
        elif test_coverage >= 20:
            overall_score -= 2  # Moderate penalty for very low coverage
        else:
            overall_score -= 3  # Major penalty for critically low coverage

        # Penalties for monolithic files (up to -5 points)
        monolithic_penalty = min(file_metrics.get('monolithic_files_count', 0) * 0.8, 5)
        overall_score -= monolithic_penalty

        # Penalties for large directories (up to -3 points)
        large_dir_penalty = min(file_metrics.get('large_directories_count', 0) * 0.5, 3)
        overall_score -= large_dir_penalty

        # Penalties for service complexity (high file count)
        total_files = file_metrics.get('total_files', 0)
        if total_files > 100:
            complexity_penalty = min((total_files - 100) * 0.02, 5)  # 2% penalty per file over 100
            overall_score -= complexity_penalty
        elif total_files > 50:
            complexity_penalty = min((total_files - 50) * 0.01, 2)  # 1% penalty per file over 50
            overall_score -= complexity_penalty

        # Penalties for linting issues
        total_lint_issues = linting_quality.get('total_issues', 0)
        pylint_score = linting_quality.get('pylint_score', 5.0)

        # Penalty for excessive linting issues
        if total_lint_issues > 50:
            lint_penalty = min((total_lint_issues - 50) * 0.05, 5)  # 5% penalty per 10 issues over 50
            overall_score -= lint_penalty
        elif total_lint_issues > 20:
            lint_penalty = min((total_lint_issues - 20) * 0.02, 2)  # 2% penalty per issue over 20
            overall_score -= lint_penalty

        # Bonus/penalty based on pylint score (0-10 scale)
        if pylint_score >= 8.0:
            overall_score += 2  # Excellent code quality
        elif pylint_score >= 6.0:
            overall_score += 1  # Good code quality
        elif pylint_score < 4.0:
            overall_score -= 2  # Poor code quality
        elif pylint_score < 3.0:
            overall_score -= 3  # Very poor code quality

        # Endpoint compliance penalties
        rest_compliance_rate = endpoint_analysis.get('rest_compliance_rate', 100)
        openapi_compliance_rate = endpoint_analysis.get('openapi_compliance_rate', 100)
        standard_compliance_rate = endpoint_analysis.get('standard_compliance_rate', 100)

        # Penalties for poor REST compliance
        if rest_compliance_rate < 80:
            rest_penalty = min((80 - rest_compliance_rate) * 0.1, 8)  # Up to 8 points penalty
            overall_score -= rest_penalty

        # Penalties for poor OpenAPI compliance
        if openapi_compliance_rate < 70:
            openapi_penalty = min((70 - openapi_compliance_rate) * 0.15, 10)  # Up to 10 points penalty
            overall_score -= openapi_penalty

        # New enhanced analysis penalties and bonuses
        complexity_analysis = results.architecture.get('complexity_analysis', {})
        dependency_coupling = results.architecture.get('dependency_coupling', {})
        dead_code_analysis = results.architecture.get('dead_code_analysis', {})
        test_quality_metrics = results.architecture.get('test_quality_metrics', {})
        domain_boundaries = results.architecture.get('domain_boundaries', {})
        api_documentation = results.architecture.get('api_documentation', {})
        code_documentation = results.architecture.get('code_documentation', {})
        configuration_management = results.architecture.get('configuration_management', {})
        logging_practices = results.architecture.get('logging_practices', {})

        # Cyclomatic complexity penalties
        high_complexity_count = len(complexity_analysis.get('high_complexity_functions', []))
        if high_complexity_count > 0:
            complexity_penalty = min(high_complexity_count * 0.5, 5)  # 0.5 points per high complexity function
            overall_score -= complexity_penalty

        # Dependency coupling penalties
        high_import_modules = len(dependency_coupling.get('high_import_count_modules', []))
        if high_import_modules > 0:
            coupling_penalty = min(high_import_modules * 1.0, 5)  # 1 point per module with high imports
            overall_score -= coupling_penalty

        # Dead code penalties
        dead_code_lines = dead_code_analysis.get('dead_code_lines', 0)
        if dead_code_lines > 50:
            dead_code_penalty = min((dead_code_lines - 50) * 0.02, 3)  # 2% penalty per line over 50
            overall_score -= dead_code_penalty

        # Test quality metrics penalties
        test_naming_issues = len(test_quality_metrics.get('test_naming_issues', []))
        isolation_issues = len(test_quality_metrics.get('isolation_issues', []))
        flaky_indicators = len(test_quality_metrics.get('flaky_test_indicators', []))

        test_quality_penalty = min((test_naming_issues + isolation_issues + flaky_indicators) * 0.3, 4)
        overall_score -= test_quality_penalty

        # Domain boundary penalties
        anemic_entities = len(domain_boundaries.get('anemic_entities', []))
        domain_leaks = len(domain_boundaries.get('domain_logic_leaks', []))

        domain_penalty = min((anemic_entities + domain_leaks) * 0.8, 4)
        overall_score -= domain_penalty

        # API documentation penalties
        api_docs_score = api_documentation.get('documentation_score', 0)
        if api_docs_score < 60:
            api_docs_penalty = min((60 - api_docs_score) * 0.1, 6)
            overall_score -= api_docs_penalty

        # Code documentation penalties
        docstring_coverage = code_documentation.get('docstring_coverage', 0)
        if docstring_coverage < 50:
            doc_penalty = min((50 - docstring_coverage) * 0.05, 3)
            overall_score -= doc_penalty

        # Configuration management penalties
        hardcoded_values = len(configuration_management.get('hardcoded_values', []))
        inconsistent_patterns = len(configuration_management.get('inconsistent_config_patterns', []))

        config_penalty = min((hardcoded_values + inconsistent_patterns) * 0.5, 5)
        overall_score -= config_penalty

        # Logging practices penalties
        missing_error_logging = len(logging_practices.get('missing_error_logging', []))
        excessive_logging = len(logging_practices.get('excessive_logging', []))
        insufficient_logging = len(logging_practices.get('insufficient_logging', []))

        logging_penalty = min((missing_error_logging + excessive_logging + insufficient_logging) * 0.4, 4)
        overall_score -= logging_penalty

        # Enhanced bonuses for excellent performance across all new analysis areas
        bonuses_applied = 0

        # Code quality bonuses
        if complexity_analysis.get('average_complexity', 10) <= 8:
            overall_score += 2  # Bonus for low average complexity
            bonuses_applied += 2

        # Documentation bonuses
        if docstring_coverage >= 80:
            overall_score += 2  # Bonus for excellent code documentation
            bonuses_applied += 2

        if api_docs_score >= 80:
            overall_score += 1  # Bonus for excellent API documentation
            bonuses_applied += 1

        # Test quality bonuses
        parameterization_suggestions = len(test_quality_metrics.get('parameterization_suggestions', []))
        if parameterization_suggestions == 0:
            overall_score += 1  # Bonus for well-structured tests
            bonuses_applied += 1

        test_naming_issues = len(test_quality_metrics.get('test_naming_issues', []))
        if test_naming_issues == 0:
            overall_score += 1  # Bonus for excellent test naming
            bonuses_applied += 1

        # Architecture and design bonuses
        anemic_entities = len(domain_boundaries.get('anemic_entities', []))
        domain_leaks = len(domain_boundaries.get('domain_logic_leaks', []))
        if anemic_entities == 0 and domain_leaks == 0:
            overall_score += 2  # Bonus for proper domain boundaries
            bonuses_applied += 2

        # Dependency management bonuses
        high_import_modules = len(dependency_coupling.get('high_import_count_modules', []))
        tightly_coupled_modules = len(dependency_coupling.get('tightly_coupled_modules', []))
        if high_import_modules == 0 and tightly_coupled_modules == 0:
            overall_score += 1  # Bonus for clean dependency management
            bonuses_applied += 1

        # Code cleanliness bonuses
        dead_code_lines = dead_code_analysis.get('dead_code_lines', 0)
        if dead_code_lines <= 10:
            overall_score += 1  # Bonus for clean codebase
            bonuses_applied += 1

        # Configuration management bonuses
        hardcoded_values = len(configuration_management.get('hardcoded_values', []))
        inconsistent_patterns = len(configuration_management.get('inconsistent_config_patterns', []))
        if hardcoded_values == 0 and inconsistent_patterns == 0:
            overall_score += 1  # Bonus for excellent configuration management
            bonuses_applied += 1

        # Logging excellence bonuses
        missing_error_logging = len(logging_practices.get('missing_error_logging', []))
        excessive_logging = len(logging_practices.get('excessive_logging', []))
        insufficient_logging = len(logging_practices.get('insufficient_logging', []))
        inconsistent_log_levels = len(logging_practices.get('inconsistent_log_levels', []))
        if all(count == 0 for count in [missing_error_logging, excessive_logging, insufficient_logging, inconsistent_log_levels]):
            overall_score += 1  # Bonus for excellent logging practices
            bonuses_applied += 1

        # Major excellence bonus for outstanding performance across multiple areas
        if bonuses_applied >= 8:  # If 8+ bonuses applied
            overall_score += 3  # Major bonus for comprehensive excellence

        # Critical issue penalties - severe penalties for major problems
        critical_issues_count = 0

        # Critical complexity issues
        very_high_complexity = len([f for f in complexity_analysis.get('high_complexity_functions', [])
                                   if f.get('complexity', 0) >= 20])
        if very_high_complexity > 0:
            critical_penalty = min(very_high_complexity * 2, 8)  # 2 points per very high complexity function
            overall_score -= critical_penalty
            critical_issues_count += very_high_complexity

        # Critical dead code issues
        if dead_code_lines > 200:
            critical_penalty = min((dead_code_lines - 200) * 0.05, 10)  # Major penalty for excessive dead code
            overall_score -= critical_penalty
            critical_issues_count += 1

        # Critical test quality issues
        total_test_issues = (test_naming_issues + isolation_issues + flaky_indicators +
                           len(test_quality_metrics.get('isolation_issues', [])))
        if total_test_issues > 50:
            critical_penalty = min((total_test_issues - 50) * 0.1, 5)  # Penalty for poor test quality
            overall_score -= critical_penalty
            critical_issues_count += 1

        # Critical documentation issues
        if docstring_coverage < 20:
            overall_score -= 5  # Major penalty for critically low documentation
            critical_issues_count += 1

        if api_docs_score < 20:
            overall_score -= 5  # Major penalty for undocumented APIs
            critical_issues_count += 1

        # Critical configuration issues
        if hardcoded_values > 10:
            overall_score -= 5  # Major penalty for extensive hardcoded values
            critical_issues_count += 1

        # Critical logging issues
        if missing_error_logging > 30:
            overall_score -= 4  # Major penalty for missing error logging
            critical_issues_count += 1

        # Overall critical issues penalty
        if critical_issues_count > 3:
            overall_score -= min(critical_issues_count - 3, 5)  # Additional penalty for multiple critical issues

        # Penalties for poor project standards compliance
        if standard_compliance_rate < 75:
            standard_penalty = min((75 - standard_compliance_rate) * 0.12, 6)  # Up to 6 points penalty
            overall_score -= standard_penalty

        # Bonus for well-structured services (good DDD + low complexity + good linting + good endpoints)
        if (ddd_compliance >= 70 and total_files <= 30 and
            total_lint_issues <= 10 and pylint_score >= 6.0 and
            rest_compliance_rate >= 80 and openapi_compliance_rate >= 80):
            overall_score += 4  # Major bonus for excellent overall quality including endpoints

        return round(max(0, min(100, overall_score)), 2)

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

        # New critical issues from enhanced analysis methods
        architecture_data = results.architecture

        # Critical complexity issues
        complexity_analysis = architecture_data.get('complexity_analysis', {})
        very_high_complexity = len([f for f in complexity_analysis.get('high_complexity_functions', [])
                                   if f.get('complexity', 0) >= 25])
        if very_high_complexity > 0:
            critical_issues.append({
                'dimension': 'complexity',
                'issue': f'Extremely high complexity functions ({very_high_complexity} functions ≥ 25 complexity)',
                'severity': 'critical',
                'description': 'Functions with complexity ≥ 25 are extremely difficult to maintain and test'
            })

        # Critical dead code issues
        dead_code_analysis = architecture_data.get('dead_code_analysis', {})
        dead_code_lines = dead_code_analysis.get('dead_code_lines', 0)
        if dead_code_lines > 300:
            critical_issues.append({
                'dimension': 'code_quality',
                'issue': f'Excessive dead code ({dead_code_lines} lines)',
                'severity': 'critical',
                'description': 'Over 300 lines of dead/commented code indicates severe maintenance issues'
            })

        # Critical test quality issues
        test_quality_metrics = architecture_data.get('test_quality_metrics', {})
        test_issues = len(test_quality_metrics.get('test_naming_issues', []))
        isolation_issues = len(test_quality_metrics.get('isolation_issues', []))
        flaky_tests = len(test_quality_metrics.get('flaky_test_indicators', []))
        total_test_issues = test_issues + isolation_issues + flaky_tests

        if total_test_issues > 100:
            critical_issues.append({
                'dimension': 'testing',
                'issue': f'Severe test quality issues ({total_test_issues} issues)',
                'severity': 'critical',
                'description': 'Over 100 test quality issues indicate unreliable testing infrastructure'
            })

        # Critical documentation issues
        code_documentation = architecture_data.get('code_documentation', {})
        docstring_coverage = code_documentation.get('docstring_coverage', 0)
        if docstring_coverage < 10:
            critical_issues.append({
                'dimension': 'documentation',
                'issue': f'Critically low documentation ({docstring_coverage:.1f}% coverage)',
                'severity': 'critical',
                'description': 'Less than 10% docstring coverage makes code extremely difficult to maintain'
            })

        api_documentation = architecture_data.get('api_documentation', {})
        api_docs_score = api_documentation.get('documentation_score', 0)
        if api_docs_score < 10:
            critical_issues.append({
                'dimension': 'api_documentation',
                'issue': f'Undocumented APIs ({api_docs_score:.1f} score)',
                'severity': 'critical',
                'description': 'APIs with less than 10 documentation score are unusable for integration'
            })

        # Critical configuration issues
        configuration_management = architecture_data.get('configuration_management', {})
        hardcoded_values = len(configuration_management.get('hardcoded_values', []))
        if hardcoded_values > 20:
            critical_issues.append({
                'dimension': 'configuration',
                'issue': f'Extensive hardcoded configuration ({hardcoded_values} instances)',
                'severity': 'critical',
                'description': 'Over 20 hardcoded configuration values create deployment and security risks'
            })

        # Critical logging issues
        logging_practices = architecture_data.get('logging_practices', {})
        missing_error_logging = len(logging_practices.get('missing_error_logging', []))
        if missing_error_logging > 50:
            critical_issues.append({
                'dimension': 'logging',
                'issue': f'Missing error logging ({missing_error_logging} locations)',
                'severity': 'critical',
                'description': 'Over 50 missing error logging locations make debugging impossible'
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

        # New recommendations from enhanced analysis methods
        architecture_data = results.architecture

        # Complexity recommendations
        complexity_analysis = architecture_data.get('complexity_analysis', {})
        high_complexity_count = len(complexity_analysis.get('high_complexity_functions', []))
        if high_complexity_count > 0:
            recommendations.append({
                'dimension': 'code_quality',
                'priority': 'high',
                'title': f'Refactor {high_complexity_count} high-complexity functions',
                'description': 'Break down functions with complexity >10 into smaller, focused methods',
                'effort_days': max(2, high_complexity_count * 1),  # 1 day per function
                'impact': 'high'
            })

        # Dependency coupling recommendations
        dependency_coupling = architecture_data.get('dependency_coupling', {})
        high_import_modules = len(dependency_coupling.get('high_import_count_modules', []))
        if high_import_modules > 0:
            recommendations.append({
                'dimension': 'architecture',
                'priority': 'medium',
                'title': f'Reduce coupling in {high_import_modules} modules',
                'description': 'Refactor modules with excessive imports and consider dependency injection',
                'effort_days': max(3, high_import_modules * 2),
                'impact': 'medium'
            })

        # Dead code recommendations
        dead_code_analysis = architecture_data.get('dead_code_analysis', {})
        dead_code_lines = dead_code_analysis.get('dead_code_lines', 0)
        if dead_code_lines > 50:
            recommendations.append({
                'dimension': 'maintainability',
                'priority': 'low',
                'title': f'Remove {dead_code_lines} lines of dead code',
                'description': 'Clean up commented and unreachable code to improve maintainability',
                'effort_days': max(1, dead_code_lines // 100),  # 1 day per 100 lines
                'impact': 'low'
            })

        # Test quality recommendations
        test_quality_metrics = architecture_data.get('test_quality_metrics', {})
        test_issues = len(test_quality_metrics.get('test_naming_issues', []))
        parameterization_needed = len(test_quality_metrics.get('parameterization_suggestions', []))
        if test_issues > 10 or parameterization_needed > 0:
            recommendations.append({
                'dimension': 'testing',
                'priority': 'medium',
                'title': f'Improve test quality ({test_issues} naming issues)',
                'description': 'Fix test naming conventions and implement parameterization where appropriate',
                'effort_days': max(2, (test_issues // 20) + parameterization_needed),
                'impact': 'medium'
            })

        # Domain boundary recommendations
        domain_boundaries = architecture_data.get('domain_boundaries', {})
        anemic_entities = len(domain_boundaries.get('anemic_entities', []))
        domain_leaks = len(domain_boundaries.get('domain_logic_leaks', []))
        if anemic_entities > 0 or domain_leaks > 0:
            recommendations.append({
                'dimension': 'architecture',
                'priority': 'high',
                'title': f'Fix domain boundaries ({anemic_entities} anemic entities, {domain_leaks} leaks)',
                'description': 'Add business logic to anemic entities and move leaked domain logic back to domain layer',
                'effort_days': max(3, (anemic_entities + domain_leaks) * 1),
                'impact': 'high'
            })

        # API documentation recommendations
        api_documentation = architecture_data.get('api_documentation', {})
        api_docs_score = api_documentation.get('documentation_score', 0)
        if api_docs_score < 70:
            recommendations.append({
                'dimension': 'documentation',
                'priority': 'high',
                'title': f'Improve API documentation (score: {api_docs_score:.1f})',
                'description': 'Add comprehensive OpenAPI/Swagger documentation to API endpoints',
                'effort_days': 4,
                'impact': 'high'
            })

        # Code documentation recommendations
        code_documentation = architecture_data.get('code_documentation', {})
        docstring_coverage = code_documentation.get('docstring_coverage', 0)
        if docstring_coverage < 70:
            recommendations.append({
                'dimension': 'documentation',
                'priority': 'medium',
                'title': f'Improve code documentation ({docstring_coverage:.1f}% coverage)',
                'description': 'Add docstrings to functions and classes for better maintainability',
                'effort_days': 3,
                'impact': 'medium'
            })

        # Configuration management recommendations
        configuration_management = architecture_data.get('configuration_management', {})
        hardcoded_values = len(configuration_management.get('hardcoded_values', []))
        if hardcoded_values > 5:
            recommendations.append({
                'dimension': 'security',
                'priority': 'high',
                'title': f'Fix {hardcoded_values} hardcoded configuration values',
                'description': 'Replace hardcoded values with environment variables for security and flexibility',
                'effort_days': max(1, hardcoded_values // 5),
                'impact': 'high'
            })

        # Logging recommendations
        logging_practices = architecture_data.get('logging_practices', {})
        missing_error_logging = len(logging_practices.get('missing_error_logging', []))
        if missing_error_logging > 10:
            recommendations.append({
                'dimension': 'maintainability',
                'priority': 'medium',
                'title': f'Add error logging to {missing_error_logging} locations',
                'description': 'Implement proper error logging in exception handlers for better debugging',
                'effort_days': max(2, missing_error_logging // 10),
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
    """Main entry point for audit framework with enhanced reporting."""
    import argparse

    parser = argparse.ArgumentParser(description='🚀 Comprehensive Service Audit Framework')
    parser.add_argument('command', choices=['audit', 'compare', 'trend'], help='Audit command')
    parser.add_argument('--service', help='Service name to audit')
    parser.add_argument('--services', help='Comma-separated service names for comparison')
    parser.add_argument('--output', choices=['json', 'markdown', 'rich'], default='rich', help='Output format')
    parser.add_argument('--period', default='6months', help='Trend analysis period')
    parser.add_argument('--quiet', action='store_true', help='Suppress progress output')

    args = parser.parse_args()

    # Initialize framework
    project_root = Path(__file__).parent.parent.parent
    framework = AuditFramework(project_root)

    # Setup rich console if available
    console = Console() if HAS_RICH else None

    try:
        if args.command == 'audit':
            if not args.service:
                logger.error("Service name required for audit command")
                return 1

            # Enhanced audit with progress tracking
            if console and not args.quiet:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeElapsedColumn(),
                    console=console,
                    transient=True
                ) as progress:
                    task = progress.add_task("Initializing audit...", total=4)

                    def progress_callback(description):
                        progress.update(task, description=description, advance=1)

                    results = await framework.audit_service(args.service, progress_callback)
            else:
                logger.info(f"Starting audit for service: {args.service}")
                results = await framework.audit_service(args.service)

            # Enhanced output formatting
            if args.output == 'rich' and console:
                # Temporarily suppress logging to avoid interference with Rich output
                import logging
                original_level = logging.getLogger().level
                logging.getLogger().setLevel(logging.WARNING)

                try:
                    _display_rich_audit_results(console, results)
                finally:
                    # Restore original logging level
                    logging.getLogger().setLevel(original_level)
            else:
                report = framework.generate_report(results, args.output)
                print(report)  # Always print plain text for JSON/Markdown

        elif args.command == 'compare':
            if not args.services:
                logger.error("Service names required for compare command")
                return 1

            services = [s.strip() for s in args.services.split(',')]

            if console and not args.quiet:
                console.print(f"🔍 Comparing {len(services)} services: {', '.join(services)}")
                with Progress(console=console) as progress:
                    task = progress.add_task("Auditing services...", total=len(services))

                    all_results = []
                    for service in services:
                        try:
                            results = await framework.audit_service(service)
                            all_results.append(results)
                            progress.update(task, advance=1)
                        except Exception as e:
                            logger.error(f"Failed to audit {service}: {e}")
                            if console:
                                console.print(f"[red]❌ Failed to audit {service}: {e}[/red]")
            else:
                logger.info(f"Comparing services: {services}")
                all_results = []
                for service in services:
                    try:
                        results = await framework.audit_service(service)
                        all_results.append(results)
                    except Exception as e:
                        logger.error(f"Failed to audit {service}: {e}")

            # Generate comparison report
            if args.output == 'rich' and console:
                # Temporarily suppress logging to avoid interference with Rich output
                import logging
                original_level = logging.getLogger().level
                logging.getLogger().setLevel(logging.WARNING)

                try:
                    _display_rich_comparison(console, all_results)
                finally:
                    # Restore original logging level
                    logging.getLogger().setLevel(original_level)
            elif args.output == 'json':
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
            else:  # markdown or default
                report = "# Service Comparison Report\n\n"
                report += f"**Audit Date:** {datetime.utcnow().isoformat()}\n"
                report += f"**Services Compared:** {len(all_results)}\n\n"

                report += "| Service | Score | Grade | Critical Issues |\n"
                report += "|---------|-------|-------|----------------|\n"
                for r in all_results:
                    report += f"| {r.service_name} | {r.overall_score:.1f} | {r.grade} | {len(r.critical_issues)} |\n"

                print(report)

        elif args.command == 'trend':
            if console:
                console.print("[yellow]📈 Trend analysis feature coming soon![/yellow]")
            else:
                logger.info("Trend analysis not yet implemented")
                print("Trend analysis feature coming soon")

    except Exception as e:
        if console:
            console.print(f"[red]❌ Audit failed: {e}[/red]")
        logger.error(f"Audit failed: {e}")
        return 1

    return 0


def _display_rich_audit_results(console: Console, results: AuditResults):
    """Display audit results using rich formatting with comprehensive score breakdown."""
    # Header with final grade prominently displayed
    grade_color = {
        'A': 'green', 'B': 'blue', 'C': 'yellow', 'D': 'red', 'F': 'red'
    }.get(results.grade, 'white')

    title = f"🎯 Service Audit: {results.service_name}"
    console.print(Panel.fit(
        f"[bold {grade_color}]FINAL GRADE: {results.grade}[/bold {grade_color}]\n"
        f"[bold green]Overall Score: {results.overall_score:.1f}/100[/bold green]\n"
        f"[dim]Audit Date: {results.audit_date}[/dim]",
        title=title
    ))

    # Critical Issues Alert
    if results.critical_issues:
        console.print(f"\n🚨 [bold red]CRITICAL ISSUES: {len(results.critical_issues)}[/bold red]")
        for issue in results.critical_issues[:3]:  # Show top 3
            console.print(f"  • {issue['issue']}")
        if len(results.critical_issues) > 3:
            console.print(f"  • ... and {len(results.critical_issues) - 3} more")

    # Score Calculation Overview
    console.print(f"\n[bold cyan]📊 SCORE CALCULATION BREAKDOWN[/bold cyan]")

    # Base dimension scores table
    dim_table = Table(title="Base Dimension Scores")
    dim_table.add_column("Dimension", style="cyan", min_width=15)
    dim_table.add_column("Raw Score", style="green", justify="right")
    dim_table.add_column("Weight", style="yellow", justify="right")
    dim_table.add_column("Weighted", style="magenta", justify="right")

    base_score = 0
    dimensions = [
        ("Architecture", results.architecture.get('score', 0), 30),
        ("Code Quality", results.code_quality.get('score', 0), 25),
        ("Performance", results.performance.get('score', 0), 20),
        ("Maintainability", results.maintainability.get('score', 0), 25)
    ]

    for dim_name, score, weight in dimensions:
        contribution = score * weight / 100
        base_score += contribution
        dim_table.add_row(
            dim_name,
            f"{score:.1f}",
            f"{weight}%",
            f"{contribution:.1f}"
        )

    console.print(dim_table)
    console.print(f"[dim]Base Score (weighted dimensions): {base_score:.1f}[/dim]")

    # Score Adjustments Table - showing all penalties and bonuses
    console.print(f"\n[bold cyan]⚖️ SCORE ADJUSTMENTS[/bold cyan]")

    adjustments_table = Table(title="Penalties & Bonuses Applied")
    adjustments_table.add_column("Category", style="cyan", min_width=25)
    adjustments_table.add_column("Factor", style="white", min_width=30)
    adjustments_table.add_column("Impact", style="red", justify="right", min_width=10)
    adjustments_table.add_column("Details", style="yellow", min_width=40)

    total_adjustments = 0
    architecture_data = results.architecture

    # Architecture-specific adjustments
    ddd_compliance = architecture_data.get('ddd_compliance', 0)
    ddd_bonus = (ddd_compliance - 50) * 0.1
    if ddd_bonus != 0:
        adjustments_table.add_row(
            "Architecture", "DDD Compliance Bonus", f"{ddd_bonus:+.1f}",
            f"DDD score: {ddd_compliance:.1f} ({'+' if ddd_bonus > 0 else ''}{ddd_bonus:.1f} adjustment)"
        )
        total_adjustments += ddd_bonus

    ddd_issues = architecture_data.get('ddd_issues', [])
    ddd_penalty = min(len(ddd_issues) * 0.5, 5)
    if ddd_penalty > 0:
        adjustments_table.add_row(
            "Architecture", "DDD Violations", f"-{ddd_penalty:.1f}",
            f"{len(ddd_issues)} DDD architecture violations"
        )
        total_adjustments -= ddd_penalty

    # Test quality adjustments
    test_quality = architecture_data.get('test_quality', {})
    test_failures = test_quality.get('test_failures', 0)
    test_coverage = test_quality.get('test_coverage', 0.0)

    if test_failures > 0:
        test_failure_penalty = min(test_failures * 0.5, 8)
        adjustments_table.add_row(
            "Testing", "Test Failures", f"-{test_failure_penalty:.1f}",
            f"{test_failures} failing tests"
        )
        total_adjustments -= test_failure_penalty

    coverage_bonus = 0
    if test_coverage >= 80:
        coverage_bonus = 3
    elif test_coverage >= 70:
        coverage_bonus = 2
    elif test_coverage >= 60:
        coverage_bonus = 1
    elif test_coverage >= 40:
        coverage_bonus = -1
    elif test_coverage >= 20:
        coverage_bonus = -2
    else:
        coverage_bonus = -3

    if coverage_bonus != 0:
        adjustments_table.add_row(
            "Testing", "Test Coverage", f"{coverage_bonus:+.1f}",
            f"Coverage: {test_coverage:.1f}%"
        )
        total_adjustments += coverage_bonus

    # Linting adjustments
    linting_quality = architecture_data.get('linting_quality', {})
    total_lint_issues = linting_quality.get('total_issues', 0)
    pylint_score = linting_quality.get('pylint_score', 5.0)

    lint_penalty = 0
    if total_lint_issues > 50:
        lint_penalty = min((total_lint_issues - 50) * 0.05, 5)
    elif total_lint_issues > 20:
        lint_penalty = min((total_lint_issues - 20) * 0.02, 2)

    if lint_penalty > 0:
        adjustments_table.add_row(
            "Code Quality", "Linting Issues", f"-{lint_penalty:.1f}",
            f"{total_lint_issues} linting issues"
        )
        total_adjustments -= lint_penalty

    pylint_bonus = 0
    if pylint_score >= 8.0:
        pylint_bonus = 2
    elif pylint_score >= 6.0:
        pylint_bonus = 1
    elif pylint_score < 4.0:
        pylint_bonus = -2
    elif pylint_score < 3.0:
        pylint_bonus = -3

    if pylint_bonus != 0:
        adjustments_table.add_row(
            "Code Quality", "Pylint Score", f"{pylint_bonus:+.1f}",
            f"Score: {pylint_score:.1f}/10"
        )
        total_adjustments += pylint_bonus

    # Endpoint compliance adjustments
    endpoint_analysis = architecture_data.get('endpoint_analysis', {})
    rest_rate = endpoint_analysis.get('rest_compliance_rate', 100)
    openapi_rate = endpoint_analysis.get('openapi_compliance_rate', 100)

    if rest_rate < 80:
        rest_penalty = min((80 - rest_rate) * 0.1, 8)
        adjustments_table.add_row(
            "API", "REST Compliance", f"-{rest_penalty:.1f}",
            f"REST compliance: {rest_rate:.1f}%"
        )
        total_adjustments -= rest_penalty

    if openapi_rate < 70:
        openapi_penalty = min((70 - openapi_rate) * 0.15, 10)
        adjustments_table.add_row(
            "API", "OpenAPI Compliance", f"-{openapi_penalty:.1f}",
            f"OpenAPI compliance: {openapi_rate:.1f}%"
        )
        total_adjustments -= openapi_penalty

    # Enhanced analysis method adjustments
    # Complexity
    complexity_analysis = architecture_data.get('complexity_analysis', {})
    high_complexity_count = len(complexity_analysis.get('high_complexity_functions', []))
    avg_complexity = complexity_analysis.get('average_complexity', 10)

    if high_complexity_count > 0:
        complexity_penalty = min(high_complexity_count * 0.5, 5)
        adjustments_table.add_row(
            "Complexity", "High Complexity Functions", f"-{complexity_penalty:.1f}",
            f"{high_complexity_count} functions with complexity >10"
        )
        total_adjustments -= complexity_penalty

    if avg_complexity <= 8:
        adjustments_table.add_row(
            "Complexity", "Low Average Complexity", "+2.0",
            f"Average complexity: {avg_complexity:.1f} ≤ 8"
        )
        total_adjustments += 2

    # Dependency coupling
    dependency_coupling = architecture_data.get('dependency_coupling', {})
    high_import_modules = len(dependency_coupling.get('high_import_count_modules', []))
    if high_import_modules > 0:
        coupling_penalty = min(high_import_modules * 1.0, 5)
        adjustments_table.add_row(
            "Architecture", "High Import Modules", f"-{coupling_penalty:.1f}",
            f"{high_import_modules} modules with excessive imports"
        )
        total_adjustments -= coupling_penalty

    # Dead code
    dead_code_analysis = architecture_data.get('dead_code_analysis', {})
    dead_code_lines = dead_code_analysis.get('dead_code_lines', 0)
    if dead_code_lines > 50:
        dead_penalty = min((dead_code_lines - 50) * 0.02, 3)
        adjustments_table.add_row(
            "Maintainability", "Dead Code", f"-{dead_penalty:.1f}",
            f"{dead_code_lines} lines of dead/commented code"
        )
        total_adjustments -= dead_penalty

    # Test quality metrics
    test_quality_metrics = architecture_data.get('test_quality_metrics', {})
    test_issues = len(test_quality_metrics.get('test_naming_issues', []))
    isolation_issues = len(test_quality_metrics.get('isolation_issues', []))
    flaky_indicators = len(test_quality_metrics.get('flaky_test_indicators', []))
    total_test_issues = test_issues + isolation_issues + flaky_indicators

    if total_test_issues > 0:
        test_quality_penalty = min(total_test_issues * 0.3, 4)
        adjustments_table.add_row(
            "Testing", "Test Quality Issues", f"-{test_quality_penalty:.1f}",
            f"{total_test_issues} test quality issues (naming, isolation, flaky)"
        )
        total_adjustments -= test_quality_penalty

    # Domain boundaries
    domain_boundaries = architecture_data.get('domain_boundaries', {})
    anemic_entities = len(domain_boundaries.get('anemic_entities', []))
    domain_leaks = len(domain_boundaries.get('domain_logic_leaks', []))
    domain_penalty = min((anemic_entities + domain_leaks) * 0.8, 4)

    if domain_penalty > 0:
        adjustments_table.add_row(
            "Architecture", "Domain Boundary Issues", f"-{domain_penalty:.1f}",
            f"{anemic_entities} anemic entities, {domain_leaks} domain leaks"
        )
        total_adjustments -= domain_penalty

    # API Documentation
    api_documentation = architecture_data.get('api_documentation', {})
    api_docs_score = api_documentation.get('documentation_score', 0)
    if api_docs_score < 60:
        api_docs_penalty = min((60 - api_docs_score) * 0.1, 6)
        adjustments_table.add_row(
            "Documentation", "API Documentation", f"-{api_docs_penalty:.1f}",
            f"API docs score: {api_docs_score:.1f}/100"
        )
        total_adjustments -= api_docs_penalty

    # Code Documentation
    code_documentation = architecture_data.get('code_documentation', {})
    docstring_coverage = code_documentation.get('docstring_coverage', 0)
    if docstring_coverage < 50:
        doc_penalty = min((50 - docstring_coverage) * 0.05, 3)
        adjustments_table.add_row(
            "Documentation", "Code Documentation", f"-{doc_penalty:.1f}",
            f"Docstring coverage: {docstring_coverage:.1f}%"
        )
        total_adjustments -= doc_penalty

    if docstring_coverage >= 80:
        adjustments_table.add_row(
            "Documentation", "Excellent Documentation", "+2.0",
            f"Docstring coverage: {docstring_coverage:.1f}% ≥ 80%"
        )
        total_adjustments += 2

    if api_docs_score >= 80:
        adjustments_table.add_row(
            "Documentation", "Excellent API Docs", "+1.0",
            f"API docs score: {api_docs_score:.1f} ≥ 80"
        )
        total_adjustments += 1

    # Configuration management
    configuration_management = architecture_data.get('configuration_management', {})
    hardcoded_values = len(configuration_management.get('hardcoded_values', []))
    if hardcoded_values > 0:
        config_penalty = min(hardcoded_values * 0.5, 5)
        adjustments_table.add_row(
            "Security", "Hardcoded Values", f"-{config_penalty:.1f}",
            f"{hardcoded_values} hardcoded configuration values"
        )
        total_adjustments -= config_penalty

    # Logging practices
    logging_practices = architecture_data.get('logging_practices', {})
    missing_error_logging = len(logging_practices.get('missing_error_logging', []))
    excessive_logging = len(logging_practices.get('excessive_logging', []))
    insufficient_logging = len(logging_practices.get('insufficient_logging', []))
    logging_penalty = min((missing_error_logging + excessive_logging + insufficient_logging) * 0.4, 4)

    if logging_penalty > 0:
        adjustments_table.add_row(
            "Logging", "Logging Issues", f"-{logging_penalty:.1f}",
            f"{missing_error_logging} missing, {excessive_logging} excessive, {insufficient_logging} insufficient"
        )
        total_adjustments -= logging_penalty

    # Excellence bonuses
    bonuses_applied = 0
    if avg_complexity <= 8:
        bonuses_applied += 2
    if docstring_coverage >= 80:
        bonuses_applied += 2
    if api_docs_score >= 80:
        bonuses_applied += 1

    parameterization_suggestions = len(test_quality_metrics.get('parameterization_suggestions', []))
    if parameterization_suggestions == 0:
        bonuses_applied += 1

    anemic_entities = len(domain_boundaries.get('anemic_entities', []))
    domain_leaks = len(domain_boundaries.get('domain_logic_leaks', []))
    if anemic_entities == 0 and domain_leaks == 0:
        bonuses_applied += 2

    high_import_modules = len(dependency_coupling.get('high_import_count_modules', []))
    tightly_coupled_modules = len(dependency_coupling.get('tightly_coupled_modules', []))
    if high_import_modules == 0 and tightly_coupled_modules == 0:
        bonuses_applied += 1

    if dead_code_lines <= 10:
        bonuses_applied += 1

    hardcoded_values = len(configuration_management.get('hardcoded_values', []))
    inconsistent_patterns = len(configuration_management.get('inconsistent_config_patterns', []))
    if hardcoded_values == 0 and inconsistent_patterns == 0:
        bonuses_applied += 1

    missing_error_logging = len(logging_practices.get('missing_error_logging', []))
    excessive_logging = len(logging_practices.get('excessive_logging', []))
    insufficient_logging = len(logging_practices.get('insufficient_logging', []))
    inconsistent_log_levels = len(logging_practices.get('inconsistent_log_levels', []))
    if all(count == 0 for count in [missing_error_logging, excessive_logging, insufficient_logging, inconsistent_log_levels]):
        bonuses_applied += 1

    if bonuses_applied >= 8:
        adjustments_table.add_row(
            "Excellence", "Comprehensive Excellence", "+3.0",
            f"8+ excellence criteria met across all categories"
        )
        total_adjustments += 3

    # Critical issue penalties
    critical_issues_count = len(results.critical_issues)
    if critical_issues_count > 3:
        critical_penalty = min(critical_issues_count - 3, 5)
        adjustments_table.add_row(
            "Critical", "Multiple Critical Issues", f"-{critical_penalty:.1f}",
            f"{critical_issues_count} critical issues (additional penalty)"
        )
        total_adjustments -= critical_penalty

    # Standards compliance penalty
    standard_compliance_rate = endpoint_analysis.get('standard_compliance_rate', 100)
    if standard_compliance_rate < 75:
        standard_penalty = min((75 - standard_compliance_rate) * 0.12, 6)
        adjustments_table.add_row(
            "Standards", "Project Standards", f"-{standard_penalty:.1f}",
            f"Project standards compliance: {standard_compliance_rate:.1f}%"
        )
        total_adjustments -= standard_penalty

    console.print(adjustments_table)

    # Final calculation summary
    final_score = base_score + total_adjustments
    console.print(f"\n[bold]SCORE SUMMARY:[/bold]")
    console.print(f"  Base Score: {base_score:.1f}")
    console.print(f"  Total Adjustments: {total_adjustments:+.1f}")
    console.print(f"  [bold green]Final Score: {final_score:.1f} → Grade {results.grade}[/bold green]")

    # 📋 DETAILED ANALYSIS SECTIONS
    console.print(f"\n[bold cyan]📋 DETAILED ANALYSIS BREAKDOWN[/bold cyan]")

    # Code Quality Section
    if results.code_quality:
        console.print(f"\n[bold blue]🔧 CODE QUALITY METRICS[/bold blue]")
        cq_table = Table(show_header=False, box=None)
        cq_table.add_column("Metric", style="cyan", width=20)
        cq_table.add_column("Score", style="green", width=10)
        cq_table.add_column("Status", style="white", width=15)

        cq_metrics = [
            ("Complexity Score", results.code_quality.get('complexity', 0)),
            ("Testing Score", results.code_quality.get('testing', 0)),
            ("Documentation Score", results.code_quality.get('documentation', 0)),
            ("Security Score", results.code_quality.get('security', 0)),
            ("DRY Principle", results.code_quality.get('dry_principle', 0)),
            ("KISS Principle", results.code_quality.get('kiss_principle', 0)),
        ]

        # Add coverage information if available
        coverage_data = results.code_quality.get('coverage_data', {})
        if coverage_data.get('overall_coverage', 0) > 0:
            cq_metrics.append(("Test Coverage %", coverage_data.get('overall_coverage', 0)))

        for metric, score in cq_metrics:
            status = "✅ Good" if score >= 70 else "⚠️  Needs Work" if score >= 50 else "❌ Poor"
            cq_table.add_row(metric, f"{score:.1f}", status)

        console.print(cq_table)

    # Architecture & Structure Analysis
    console.print(f"\n[bold blue]🏗️ ARCHITECTURE & STRUCTURE ANALYSIS[/bold blue]")

    # Service Complexity Overview
    file_metrics = architecture_data.get('file_metrics', {})
    if file_metrics:
        complexity_table = Table(show_header=False, box=None)
        complexity_table.add_column("Metric", style="cyan", width=25)
        complexity_table.add_column("Value", style="green", width=10)
        complexity_table.add_column("Impact", style="red", width=15)

        total_files = file_metrics.get('total_files', 0)
        monolithic_count = file_metrics.get('monolithic_files_count', 0)
        large_dirs_count = file_metrics.get('large_directories_count', 0)

        complexity_impact = 0
        if monolithic_count > 0:
            complexity_impact -= min(monolithic_count * 0.8, 5)
        if large_dirs_count > 0:
            complexity_impact -= min(large_dirs_count * 0.5, 3)
        if total_files > 100:
            complexity_impact -= min((total_files - 100) * 0.02, 5)
        elif total_files > 50:
            complexity_impact -= min((total_files - 50) * 0.01, 2)

        complexity_table.add_row("Total Files", str(total_files),
                                f"{'❌ High' if total_files > 100 else '⚠️  Medium' if total_files > 50 else '✅ Good'}")
        complexity_table.add_row("Monolithic Files", str(monolithic_count),
                                f"-{min(monolithic_count * 0.8, 5):.1f} pts" if monolithic_count > 0 else "✅ None")
        complexity_table.add_row("Large Directories", str(large_dirs_count),
                                f"-{min(large_dirs_count * 0.5, 3):.1f} pts" if large_dirs_count > 0 else "✅ None")

        console.print(complexity_table)

    # DDD Compliance Summary
    ddd_compliance = architecture_data.get('ddd_compliance', 0)
    ddd_issues = architecture_data.get('ddd_issues', [])
    console.print(f"\n[cyan]DDD Compliance: {ddd_compliance:.1f}/100[/cyan] ({len(ddd_issues)} issues)")
    if ddd_issues:
        console.print("  [red]Key Issues:[/red]")
        for issue in ddd_issues[:3]:
            console.print(f"  • {issue}")
        if len(ddd_issues) > 3:
            console.print(f"  • ... and {len(ddd_issues) - 3} more")

    # Enhanced Analysis Sections - New Methods
    console.print(f"\n[bold blue]🔍 ENHANCED ANALYSIS RESULTS[/bold blue]")

    # 1. Cyclomatic Complexity Analysis
    complexity_analysis = architecture_data.get('complexity_analysis', {})
    if complexity_analysis:
        console.print(f"\n[cyan]🌀 Cyclomatic Complexity:[/cyan]")
        total_funcs = complexity_analysis.get('total_functions_analyzed', 0)
        high_complexity = len(complexity_analysis.get('high_complexity_functions', []))
        avg_complexity = complexity_analysis.get('average_complexity', 0)

        console.print(f"  • Analyzed {total_funcs} functions")
        console.print(f"  • {high_complexity} high-complexity functions (>10)")
        console.print(f"  • Average complexity: {avg_complexity:.1f}")
        if high_complexity > 0:
            console.print(f"  • [red]Impact: -{min(high_complexity * 0.5, 5):.1f} points[/red]")
        else:
            console.print("  • [green]✅ Good complexity management[/green]")

    # 2. Dependency Coupling Analysis
    dependency_coupling = architecture_data.get('dependency_coupling', {})
    if dependency_coupling:
        console.print(f"\n[cyan]🔗 Dependency Coupling:[/cyan]")
        high_imports = len(dependency_coupling.get('high_import_count_modules', []))
        tight_coupling = len(dependency_coupling.get('tightly_coupled_modules', []))

        console.print(f"  • {high_imports} modules with excessive imports")
        console.print(f"  • {tight_coupling} tightly coupled modules")
        if high_imports > 0 or tight_coupling > 0:
            penalty = min(high_imports * 1.0 + tight_coupling * 0.5, 5)
            console.print(f"  • [red]Impact: -{penalty:.1f} points[/red]")
        else:
            console.print("  • [green]✅ Clean dependency management[/green]")

    # 3. Dead Code Analysis
    dead_code_analysis = architecture_data.get('dead_code_analysis', {})
    if dead_code_analysis:
        console.print(f"\n[cyan]💀 Dead Code Analysis:[/cyan]")
        dead_lines = dead_code_analysis.get('dead_code_lines', 0)
        commented_code = len(dead_code_analysis.get('commented_code', []))
        unreachable_code = len(dead_code_analysis.get('unreachable_code', []))

        console.print(f"  • {dead_lines} lines of dead/commented code")
        console.print(f"  • {commented_code} commented code blocks")
        console.print(f"  • {unreachable_code} unreachable code blocks")
        if dead_lines > 50:
            penalty = min((dead_lines - 50) * 0.02, 3)
            console.print(f"  • [red]Impact: -{penalty:.1f} points[/red]")
        else:
            console.print("  • [green]✅ Clean codebase[/green]")

    # 4. Test Quality Metrics
    test_quality_metrics = architecture_data.get('test_quality_metrics', {})
    if test_quality_metrics:
        console.print(f"\n[cyan]🧪 Test Quality Metrics:[/cyan]")
        naming_issues = len(test_quality_metrics.get('test_naming_issues', []))
        isolation_issues = len(test_quality_metrics.get('isolation_issues', []))
        flaky_tests = len(test_quality_metrics.get('flaky_test_indicators', []))
        parameterization = len(test_quality_metrics.get('parameterization_suggestions', []))

        console.print(f"  • {naming_issues} test naming issues")
        console.print(f"  • {isolation_issues} isolation issues")
        console.print(f"  • {flaky_tests} flaky test indicators")
        console.print(f"  • {parameterization} parameterization opportunities")

        total_issues = naming_issues + isolation_issues + flaky_tests
        if total_issues > 0:
            penalty = min(total_issues * 0.3, 4)
            console.print(f"  • [red]Impact: -{penalty:.1f} points[/red]")
        else:
            console.print("  • [green]✅ Good test quality standards[/green]")

    # 5. Domain Boundary Analysis
    domain_boundaries = architecture_data.get('domain_boundaries', {})
    if domain_boundaries:
        console.print(f"\n[cyan]🏛️ Domain Boundaries:[/cyan]")
        anemic_entities = len(domain_boundaries.get('anemic_entities', []))
        domain_leaks = len(domain_boundaries.get('domain_logic_leaks', []))

        console.print(f"  • {anemic_entities} anemic entities")
        console.print(f"  • {domain_leaks} domain logic leaks")
        if anemic_entities > 0 or domain_leaks > 0:
            penalty = min((anemic_entities + domain_leaks) * 0.8, 4)
            console.print(f"  • [red]Impact: -{penalty:.1f} points[/red]")
        else:
            console.print("  • [green]✅ Proper domain encapsulation[/green]")

    # 6. API Documentation Quality
    api_documentation = architecture_data.get('api_documentation', {})
    if api_documentation:
        console.print(f"\n[cyan]📚 API Documentation:[/cyan]")
        docs_score = api_documentation.get('documentation_score', 0)
        total_endpoints = api_documentation.get('total_endpoints', 0)

        console.print(f"  • {total_endpoints} endpoints analyzed")
        console.print(f"  • Documentation score: {docs_score:.1f}/100")
        if docs_score < 60:
            penalty = min((60 - docs_score) * 0.1, 6)
            console.print(f"  • [red]Impact: -{penalty:.1f} points[/red]")
        else:
            console.print("  • [green]✅ Good API documentation[/green]")

    # 7. Code Documentation Analysis
    code_documentation = architecture_data.get('code_documentation', {})
    if code_documentation:
        console.print(f"\n[cyan]📖 Code Documentation:[/cyan]")
        coverage = code_documentation.get('docstring_coverage', 0)
        undocumented_functions = len(code_documentation.get('functions_without_docs', []))
        undocumented_classes = len(code_documentation.get('classes_without_docs', []))

        console.print(f"  • Docstring coverage: {coverage:.1f}%")
        console.print(f"  • {undocumented_functions} undocumented functions")
        console.print(f"  • {undocumented_classes} undocumented classes")
        if coverage < 50:
            penalty = min((50 - coverage) * 0.05, 3)
            console.print(f"  • [red]Impact: -{penalty:.1f} points[/red]")
        elif coverage >= 80:
            console.print("  • [green]Bonus: +2.0 points (excellent)[/green]")
        else:
            console.print("  • [yellow]⚠️  Needs improvement[/yellow]")

    # 8. Configuration Management
    configuration_management = architecture_data.get('configuration_management', {})
    if configuration_management:
        console.print(f"\n[cyan]⚙️ Configuration Management:[/cyan]")
        hardcoded_values = len(configuration_management.get('hardcoded_values', []))
        inconsistent_patterns = len(configuration_management.get('inconsistent_config_patterns', []))

        console.print(f"  • {hardcoded_values} hardcoded values")
        console.print(f"  • {inconsistent_patterns} inconsistent patterns")
        if hardcoded_values > 0:
            penalty = min(hardcoded_values * 0.5, 5)
            console.print(f"  • [red]Impact: -{penalty:.1f} points[/red]")
        else:
            console.print("  • [green]✅ Good configuration practices[/green]")

    # 9. Logging Practices
    logging_practices = architecture_data.get('logging_practices', {})
    if logging_practices:
        console.print(f"\n[cyan]📝 Logging Practices:[/cyan]")
        missing_error_logging = len(logging_practices.get('missing_error_logging', []))
        excessive_logging = len(logging_practices.get('excessive_logging', []))
        insufficient_logging = len(logging_practices.get('insufficient_logging', []))

        console.print(f"  • {missing_error_logging} missing error logs")
        console.print(f"  • {excessive_logging} excessive logging locations")
        console.print(f"  • {insufficient_logging} insufficient logging locations")
        if missing_error_logging > 0 or excessive_logging > 0 or insufficient_logging > 0:
            penalty = min((missing_error_logging + excessive_logging + insufficient_logging) * 0.4, 4)
            console.print(f"  • [red]Impact: -{penalty:.1f} points[/red]")
        else:
            console.print("  • [green]✅ Good logging practices[/green]")

    # Test Quality Analysis
    test_quality = architecture_data.get('test_quality', {})
    if test_quality and (test_quality.get('total_tests', 0) > 0 or test_quality.get('test_coverage', 0) > 0):
        console.print(f"\n[bold blue]🧪 TESTING ANALYSIS[/bold blue]")

        total_tests = test_quality.get('total_tests', 0)
        passed_tests = test_quality.get('passed_tests', 0)
        failed_tests = test_quality.get('failed_tests', 0)
        test_coverage = test_quality.get('test_coverage', 0.0)
        error_message = test_quality.get('error_message')

        test_status_table = Table(show_header=False, box=None)
        test_status_table.add_column("Metric", style="cyan", width=20)
        test_status_table.add_column("Value", style="green", width=15)
        test_status_table.add_column("Status", style="white", width=20)

        test_status_table.add_row("Total Tests", str(total_tests), "✅ Good" if total_tests > 0 else "❌ None")
        test_status_table.add_row("Passed/Failed", f"{passed_tests}/{failed_tests}",
                                 "✅ All Passing" if failed_tests == 0 and total_tests > 0 else f"❌ {failed_tests} Failed")
        test_status_table.add_row("Coverage", f"{test_coverage:.1f}%" if test_coverage > 0 else "N/A",
                                 "✅ Excellent" if test_coverage >= 80 else "⚠️  Needs Work" if test_coverage >= 50 else "❌ Poor")

        console.print(test_status_table)

        if error_message:
            console.print(f"  [yellow]Note: {error_message}[/yellow]")

    # REST API Endpoint Analysis
    endpoint_analysis = architecture_data.get('endpoint_analysis', {})
    if endpoint_analysis and endpoint_analysis.get('total_endpoints', 0) > 0:
        console.print(f"\n[bold blue]🌐 API ENDPOINT ANALYSIS[/bold blue]")

        total_endpoints = endpoint_analysis.get('total_endpoints', 0)
        rest_rate = endpoint_analysis.get('rest_compliance_rate', 0)
        openapi_rate = endpoint_analysis.get('openapi_compliance_rate', 0)
        standard_rate = endpoint_analysis.get('standard_compliance_rate', 0)

        api_table = Table(show_header=False, box=None)
        api_table.add_column("Metric", style="cyan", width=20)
        api_table.add_column("Score", style="green", width=10)
        api_table.add_column("Status", style="white", width=15)

        api_table.add_row("Total Endpoints", str(total_endpoints), "✅ Good")
        api_table.add_row("REST Compliance", f"{rest_rate:.1f}%",
                         "✅ Good" if rest_rate >= 80 else "⚠️  Needs Work" if rest_rate >= 60 else "❌ Poor")
        api_table.add_row("OpenAPI Compliance", f"{openapi_rate:.1f}%",
                         "✅ Good" if openapi_rate >= 80 else "⚠️  Needs Work" if openapi_rate >= 60 else "❌ Poor")
        api_table.add_row("Standards Compliance", f"{standard_rate:.1f}%",
                         "✅ Good" if standard_rate >= 80 else "⚠️  Needs Work" if standard_rate >= 60 else "❌ Poor")

        console.print(api_table)

    # Linting Quality Analysis
    linting_quality = architecture_data.get('linting_quality', {})
    if linting_quality:
        console.print(f"\n[bold blue]🔍 LINTING & CODE QUALITY[/bold blue]")

        flake8_issues = linting_quality.get('flake8_issues', 0)
        pylint_score = linting_quality.get('pylint_score', 5.0)
        total_issues = linting_quality.get('total_issues', 0)

        lint_table = Table(show_header=False, box=None)
        lint_table.add_column("Metric", style="cyan", width=20)
        lint_table.add_column("Value", style="green", width=15)
        lint_table.add_column("Status", style="white", width=20)

        lint_table.add_row("Flake8 Issues", str(flake8_issues),
                          "✅ Clean" if flake8_issues == 0 else "⚠️  Some Issues" if flake8_issues < 50 else "❌ Many Issues")
        lint_table.add_row("Pylint Score", f"{pylint_score:.1f}/10",
                          "✅ Excellent" if pylint_score >= 8.0 else "⚠️  Good" if pylint_score >= 6.0 else "❌ Poor")

        console.print(lint_table)

    # Priority improvements and recommendations
    if results.priority_improvements:
        console.print(f"\n[bold blue]🎯 PRIORITY IMPROVEMENTS ({results.estimated_effort_days} days total)[/bold blue]")
        for rec in results.priority_improvements[:5]:  # Show top 5
            priority_color = {"high": "red", "medium": "yellow", "low": "green"}.get(rec.get('priority', 'medium'), 'white')
            console.print(f"  [{priority_color}]{rec['priority'].upper()}[/{priority_color}] {rec['title']} ({rec['effort_days']} days)")

    # System metrics if available
    if results.performance.get('system_metrics'):
        metrics = results.performance['system_metrics']
        console.print(f"\n[bold blue]💻 SYSTEM METRICS[/bold blue]")
        console.print(f"  • CPU Usage: {metrics.get('cpu_percent', 'N/A')}%")
        console.print(f"  • Memory: {metrics.get('memory_percent', 'N/A')}% ({metrics.get('memory_used_gb', 'N/A')}GB used)")
        console.print(f"  • Disk I/O: {metrics.get('disk_read_mb', 'N/A')}MB read, {metrics.get('disk_write_mb', 'N/A')}MB write")
        console.print(f"  • Network: {metrics.get('network_sent_mb', 'N/A')}MB sent, {metrics.get('network_recv_mb', 'N/A')}MB received")

    # Comprehensive Action Plan Summary
    console.print(f"\n[bold cyan]📋 ACTION PLAN SUMMARY[/bold cyan]")
    console.print("Specific strategies to address identified issues:")

    architecture_data = results.architecture

    # 1. Complexity Issues
    complexity_analysis = architecture_data.get('complexity_analysis', {})
    high_complexity_count = len(complexity_analysis.get('high_complexity_functions', []))
    if high_complexity_count > 0:
        console.print(f"\n[cyan]🌀 Complexity Reduction:[/cyan]")
        console.print(f"  • Break down {high_complexity_count} high-complexity functions (>10)")
        console.print("  • Strategy: Extract smaller functions, use early returns, simplify conditionals")
        console.print("  • Tools: Use radon cc <file> to identify complex functions")
        console.print("  • Goal: Reduce complexity score by 20-40 points")

    # 2. Architecture & DDD Issues
    ddd_compliance = architecture_data.get('ddd_compliance', 100)
    if ddd_compliance < 80:
        console.print(f"\n[cyan]🏗️ Architecture Refactoring:[/cyan]")
        console.print("  • Implement Domain-Driven Design principles")
        console.print("  • Create domain/entities/, domain/services/, domain/repositories/")
        console.print("  • Move business logic from infrastructure to domain layer")
        console.print("  • Break down monolithic files (>500 lines) into smaller modules")
        console.print("  • Expected Impact: +15-25 points to architecture score")

    # 3. Dependency Coupling Issues
    dependency_coupling = architecture_data.get('dependency_coupling', {})
    high_import_modules = len(dependency_coupling.get('high_import_count_modules', []))
    if high_import_modules > 0:
        console.print(f"\n[cyan]🔗 Dependency Injection:[/cyan]")
        console.print(f"  • Refactor {high_import_modules} tightly coupled modules")
        console.print("  • Implement dependency injection pattern")
        console.print("  • Create interfaces/abstractions between layers")
        console.print("  • Use factories or service locators for dependencies")
        console.print("  • Result: Improved testability and maintainability")

    # 4. Dead Code Cleanup
    dead_code_analysis = architecture_data.get('dead_code_analysis', {})
    dead_lines = dead_code_analysis.get('dead_code_lines', 0)
    if dead_lines > 50:
        console.print(f"\n[cyan]💀 Code Cleanup:[/cyan]")
        console.print(f"  • Remove {dead_lines} lines of dead/commented code")
        console.print("  • Use tools: coverage.py, vulture for unused code detection")
        console.print("  • Remove unreachable code after return/raise statements")
        console.print("  • Clean up old commented code blocks")
        console.print("  • Benefit: Improved code readability and reduced maintenance burden")

    # 5. Test Quality Improvements
    test_quality_metrics = architecture_data.get('test_quality_metrics', {})
    test_issues = len(test_quality_metrics.get('test_naming_issues', []))
    if test_issues > 0:
        console.print(f"\n[cyan]🧪 Test Quality Enhancement:[/cyan]")
        console.print(f"  • Fix {test_issues} poorly named test functions")
        console.print("  • Naming convention: test_<behavior>_<condition>_<expected_result>")
        console.print("  • Implement parameterized tests using @pytest.mark.parametrize")
        console.print("  • Add test isolation with proper fixtures and mocking")
        console.print("  • Target: 80%+ test coverage with meaningful test names")

    # 6. Domain Boundary Fixes
    domain_boundaries = architecture_data.get('domain_boundaries', {})
    anemic_entities = len(domain_boundaries.get('anemic_entities', []))
    if anemic_entities > 0:
        console.print(f"\n[cyan]🏛️ Domain Logic Enhancement:[/cyan]")
        console.print(f"  • Add business logic to {anemic_entities} anemic entities")
        console.print("  • Move validation, business rules to entity methods")
        console.print("  • Implement value objects for complex data structures")
        console.print("  • Create domain services for cross-entity business logic")
        console.print("  • Outcome: Rich domain model with proper encapsulation")

    # 7. API Documentation Improvements
    api_documentation = architecture_data.get('api_documentation', {})
    api_docs_score = api_documentation.get('documentation_score', 100)
    if api_docs_score < 80:
        console.print(f"\n[cyan]📚 API Documentation:[/cyan]")
        console.print(f"  • Improve API documentation score from {api_docs_score:.1f} to 90+")
        console.print("  • Add comprehensive OpenAPI/Swagger annotations")
        console.print("  • Include response examples and error schemas")
        console.print("  • Document all parameters, request/response models")
        console.print("  • Generate API docs: /docs endpoint for interactive documentation")

    # 8. Code Documentation Strategy
    code_documentation = architecture_data.get('code_documentation', {})
    docstring_coverage = code_documentation.get('docstring_coverage', 100)
    if docstring_coverage < 70:
        console.print(f"\n[cyan]📖 Code Documentation:[/cyan]")
        console.print(f"  • Increase docstring coverage from {docstring_coverage:.1f}% to 90%")
        console.print("  • Add Google/NumPy style docstrings to all functions/classes")
        console.print("  • Document parameters, return types, exceptions, examples")
        console.print("  • Use type hints (mypy) for better IDE support")
        console.print("  • Tools: interrogate for coverage, sphinx for documentation generation")

    # 9. Configuration Management Fixes
    configuration_management = architecture_data.get('configuration_management', {})
    hardcoded_values = len(configuration_management.get('hardcoded_values', []))
    if hardcoded_values > 0:
        console.print(f"\n[cyan]⚙️ Configuration Security:[/cyan]")
        console.print(f"  • Replace {hardcoded_values} hardcoded configuration values")
        console.print("  • Use environment variables with pydantic-settings")
        console.print("  • Implement configuration validation")
        console.print("  • Create .env.example file for required variables")
        console.print("  • Security benefit: No sensitive data in code repository")

    # 10. Logging Best Practices
    logging_practices = architecture_data.get('logging_practices', {})
    missing_error_logging = len(logging_practices.get('missing_error_logging', []))
    if missing_error_logging > 0:
        console.print(f"\n[cyan]📝 Logging Excellence:[/cyan]")
        console.print(f"  • Add error logging to {missing_error_logging} exception handlers")
        console.print("  • Implement structured logging with correlation IDs")
        console.print("  • Use appropriate log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        console.print("  • Add contextual information to log messages")
        console.print("  • Centralize logging configuration for consistency")

    # 11. REST API Compliance
    endpoint_analysis = architecture_data.get('endpoint_analysis', {})
    rest_rate = endpoint_analysis.get('rest_compliance_rate', 100)
    if rest_rate < 80:
        console.print(f"\n[cyan]🌐 REST API Standards:[/cyan]")
        console.print(f"  • Improve REST compliance from {rest_rate:.1f}% to 90%+")
        console.print("  • Use proper HTTP methods: GET, POST, PUT, DELETE")
        console.print("  • Implement standard status codes (200, 201, 400, 404, 500)")
        console.print("  • Use consistent resource naming (/users, /users/{id})")
        console.print("  • Add proper error response formats")

    # 12. Code Quality Tools
    linting_quality = architecture_data.get('linting_quality', {})
    total_lint_issues = linting_quality.get('total_issues', 0)
    if total_lint_issues > 50:
        console.print(f"\n[cyan]🔍 Code Quality Tools:[/cyan]")
        console.print(f"  • Fix {total_lint_issues} linting issues")
        console.print("  • Run: black . && isort . && flake8 . && pylint .")
        console.print("  • Set up pre-commit hooks for automated quality checks")
        console.print("  • Configure CI/CD pipeline with quality gates")
        console.print("  • Maintain code quality standards consistently")

    # Implementation Timeline
    console.print(f"\n[bold yellow]⏰ IMPLEMENTATION TIMELINE[/bold yellow]")
    console.print(f"Estimated total effort: {results.estimated_effort_days} days")

    # Group recommendations by timeline
    high_priority = [r for r in results.priority_improvements if r.get('priority') == 'high']
    medium_priority = [r for r in results.priority_improvements if r.get('priority') == 'medium']
    low_priority = [r for r in results.priority_improvements if r.get('priority') == 'low']

    if high_priority:
        high_effort = sum(r.get('effort_days', 0) for r in high_priority)
        console.print(f"  • Week 1-2 (High Priority): {len(high_priority)} items, {high_effort} days")
        for rec in high_priority[:3]:
            console.print(f"    - {rec['title']}")

    if medium_priority:
        medium_effort = sum(r.get('effort_days', 0) for r in medium_priority)
        console.print(f"  • Week 3-4 (Medium Priority): {len(medium_priority)} items, {medium_effort} days")
        for rec in medium_priority[:2]:
            console.print(f"    - {rec['title']}")

    if low_priority:
        low_effort = sum(r.get('effort_days', 0) for r in low_priority)
        console.print(f"  • Ongoing (Low Priority): {len(low_priority)} items, {low_effort} days")
        for rec in low_priority[:2]:
            console.print(f"    - {rec['title']}")

    # Success Metrics
    console.print(f"\n[bold green]🎯 SUCCESS METRICS[/bold green]")
    console.print("Track improvement with these targets:")
    console.print(f"  • Score Improvement: {results.overall_score:.1f} → 80+ (target grade: B or A)")
    console.print("  • Critical Issues: {len(results.critical_issues)} → 0 (zero tolerance)")
    console.print("  • Test Coverage: → 80%+ with meaningful tests")
    console.print("  • Documentation: → 90%+ coverage with quality docstrings")
    console.print("  • Complexity: → Average <8, no functions >15")
    console.print("  • Architecture: → DDD compliance 80%+")

    # LLM-Friendly Summary
    console.print(f"\n[bold cyan]🤖 LLM SUMMARY[/bold cyan]")
    console.print(f"Service: {results.service_name}")
    console.print(f"Grade: {results.grade} (Score: {results.overall_score:.1f}/100)")
    console.print(f"Critical Issues: {len(results.critical_issues)}")
    console.print(f"Priority Actions: {len(results.priority_improvements)}")
    console.print(f"Estimated Effort: {results.estimated_effort_days} days")

    if results.critical_issues:
        console.print("Critical Issues:")
        for issue in results.critical_issues[:3]:
            console.print(f"  - {issue['issue']}")

    console.print("Top Recommendations:")
    for rec in results.priority_improvements[:3]:
        console.print(f"  - {rec['title']} ({rec['priority']} priority, {rec['effort_days']} days)")


def _display_rich_comparison(console: Console, results_list: List[AuditResults]):
    """Display comparison results using rich formatting."""
    if not results_list:
        console.print("[red]No results to compare[/red]")
        return

    table = Table(title="🔍 Service Comparison")
    table.add_column("Service", style="cyan")
    table.add_column("Score", style="green")
    table.add_column("Grade", style="yellow")
    table.add_column("Critical Issues", style="red")
    table.add_column("Priority Actions", style="blue")

    for results in sorted(results_list, key=lambda x: x.overall_score, reverse=True):
        table.add_row(
            results.service_name,
            f"{results.overall_score:.1f}",
            results.grade,
            str(len(results.critical_issues)),
            str(len(results.priority_improvements))
        )

    console.print(table)

    # Summary stats
    avg_score = sum(r.overall_score for r in results_list) / len(results_list)
    total_critical = sum(len(r.critical_issues) for r in results_list)

    console.print(f"\n📈 Summary: {len(results_list)} services audited")
    console.print(f"   Average Score: {avg_score:.1f}")
    console.print(f"   Total Critical Issues: {total_critical}")


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
