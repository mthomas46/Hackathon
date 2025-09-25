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

        # Define expected DDD directory structure with strict standards
        ddd_standards = {
            'domain': {
                'required': ['entities', 'services', 'repositories'],
                'recommended': ['value_objects', 'exceptions', 'events', 'factories', 'validation'],
                'optional': ['aggregates', 'domain_services', 'specifications'],
                'forbidden': ['controllers', 'routes', 'config', 'cache', 'external_services', 'migrations']
            },
            'application': {
                'required': ['handlers'],
                'recommended': ['services', 'events', 'dto', 'use_cases', 'validators'],
                'optional': ['commands', 'queries', 'cqrs'],
                'forbidden': ['entities', 'repositories', 'config', 'cache', 'external_services']
            },
            'infrastructure': {
                'required': [],
                'recommended': ['config', 'repositories', 'external_services', 'cache', 'events'],
                'optional': ['migrations', 'connections', 'logging', 'monitoring'],
                'forbidden': ['entities', 'domain_services', 'controllers', 'handlers']
            },
            'presentation': {
                'required': ['controllers'],
                'recommended': ['middleware', 'models', 'routes'],
                'optional': ['api', 'web', 'templates'],
                'forbidden': ['entities', 'repositories', 'domain_services', 'config']
            }
        }

        # Check for layer separation (10 points)
        layer_score = 0
        layers_found = []
        for layer in ddd_standards.keys():
            if any(layer in dir_path for dir_path in all_dirs):
                layers_found.append(layer)
                layer_score += 2.5  # 2.5 points per layer found

        if len(layers_found) >= 3:
            layer_score += 5  # Bonus for having at least 3 layers

        score += min(10, layer_score)

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
                required_found = sum(1 for required in ddd_standards['domain']['required']
                                   if any(required in comp for comp in archetype_components))
                if required_found >= 2:
                    domain_score += 3
                elif required_found >= 1:
                    domain_score += 2

                # Check for missing required components only if using archetype pattern
                if required_found < 3:
                    for required in ddd_standards['domain']['required']:
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

        # Analyze each Python file for DDD conversion needs
        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_') and not file.startswith('__'):
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(service.path)

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            lines = content.split('\n')

                            # Skip very small files
                            if len(lines) < 50:
                                continue

                            # Analyze file for DDD conversion needs
                            conversion_needed, reasons = self._analyze_module_for_ddd_conversion(content, str(rel_path))

                            if conversion_needed:
                                modules_needing_ddd_conversion.append(str(rel_path))
                                ddd_conversion_suggestions.extend(reasons)

                    except Exception as e:
                        logger.debug(f"Error analyzing file {file_path}: {e}")
                        continue

        # Apply penalties for modules needing DDD conversion
        if modules_needing_ddd_conversion:
            # Penalty scales with number of modules needing conversion
            conversion_penalty = min(len(modules_needing_ddd_conversion) * 0.3, 4)  # Max 4 points
            ddd_violation_score -= conversion_penalty
            score -= conversion_penalty

            issues_found.append(f"Modules requiring DDD conversion: {len(modules_needing_ddd_conversion)} files need architectural refactoring")
            recommendations.extend(ddd_conversion_suggestions[:3])  # Limit to top 3 suggestions

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

                    if layer and layer in ddd_standards:
                        standards = ddd_standards[layer]

                        # Check for forbidden components in this layer
                        for forbidden in standards['forbidden']:
                            if forbidden in dir_parts[-1].lower():
                                directories_to_refactor.append(str(rel_path))
                                refactoring_suggestions.append(
                                    f"Move {rel_path} from {layer} layer to appropriate layer (forbidden in {layer})"
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
                                        f"Create {layer}/{missing}/ directory for required {layer} component"
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

        # Factor in DDD compliance more heavily (additional 10% weight)
        ddd_bonus = (ddd_compliance - 50) * 0.1  # Bonus/penalty based on DDD score vs 50 baseline
        overall_score += ddd_bonus

        # Additional penalties for DDD architecture violations
        ddd_violation_penalty = len(ddd_issues) * 0.5  # 0.5 points per DDD violation
        overall_score -= min(ddd_violation_penalty, 5)  # Max 5 point penalty

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

        # Bonus for well-structured services (good DDD + low complexity)
        if ddd_compliance >= 70 and total_files <= 30:
            overall_score += 2  # Bonus for clean, well-structured services

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
    """Display audit results using rich formatting."""
    # Header
    title = f"🎯 Service Audit: {results.service_name}"
    console.print(Panel.fit(
        f"[bold green]Score: {results.overall_score:.1f}/100[/bold green]\n"
        f"[bold blue]Grade: {results.grade}[/bold blue]\n"
        f"[dim]Audit Date: {results.audit_date}[/dim]",
        title=title
    ))

    # Score breakdown table
    table = Table(title="📊 Dimension Scores")
    table.add_column("Dimension", style="cyan")
    table.add_column("Score", style="green")
    table.add_column("Weight", style="yellow")
    table.add_column("Contribution", style="magenta")

    dimensions = [
        ("Architecture", results.architecture.get('score', 0), 30),
        ("Code Quality", results.code_quality.get('score', 0), 25),
        ("Performance", results.performance.get('score', 0), 20),
        ("Maintainability", results.maintainability.get('score', 0), 25)
    ]

    for dim_name, score, weight in dimensions:
        contribution = score * weight / 100
        table.add_row(
            dim_name,
            f"{score:.1f}",
            f"{weight}%",
            f"{contribution:.1f}"
        )

    console.print(table)

    # Detailed Code Quality Breakdown
    if results.code_quality:
        cq_table = Table(title="🔧 Code Quality Details")
        cq_table.add_column("Metric", style="cyan")
        cq_table.add_column("Score", style="green")

        cq_metrics = [
            ("Complexity", results.code_quality.get('complexity', 0)),
            ("Testing", results.code_quality.get('testing', 0)),
            ("Documentation", results.code_quality.get('documentation', 0)),
            ("Security", results.code_quality.get('security', 0)),
            ("DRY Principle", results.code_quality.get('dry_principle', 0)),
            ("KISS Principle", results.code_quality.get('kiss_principle', 0)),
        ]

        # Add coverage information if available
        coverage_data = results.code_quality.get('coverage_data', {})
        if coverage_data.get('overall_coverage', 0) > 0:
            cq_metrics.append(("Test Coverage", coverage_data.get('overall_coverage', 0)))

        for metric, score in cq_metrics:
            cq_table.add_row(metric, f"{score:.1f}")

        console.print()
        console.print(cq_table)

    # DDD Structure Analysis
    architecture_data = results.architecture
    if architecture_data.get('ddd_issues') or architecture_data.get('ddd_recommendations') or architecture_data.get('file_metrics'):
        console.print("\n🏗️ [bold cyan]DDD Structure & Complexity Analysis[/bold cyan]")

        # File metrics and complexity impact
        file_metrics = architecture_data.get('file_metrics', {})
        if file_metrics:
            console.print("[blue]📊 Service Complexity:[/blue]")
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

            console.print(f"  • Total Files: {total_files}")
            console.print(f"  • Monolithic Files: {monolithic_count}")
            console.print(f"  • Large Directories: {large_dirs_count}")

            # Calculate DDD violation impact
            ddd_issues = architecture_data.get('ddd_issues', [])
            ddd_violation_penalty = min(len(ddd_issues) * 0.5, 5)

            # Calculate DDD conversion penalty (modules needing conversion)
            ddd_conversion_modules = sum(1 for issue in ddd_issues
                                       if "Modules requiring DDD conversion:" in issue)
            ddd_conversion_penalty = min(ddd_conversion_modules * 0.3, 4) if ddd_conversion_modules > 0 else 0

            total_ddd_penalty = ddd_violation_penalty + ddd_conversion_penalty
            total_impact = complexity_impact - total_ddd_penalty

            if total_impact != 0:
                impact_color = "red" if total_impact < 0 else "green"
                console.print(f"  • [bold {impact_color}]Complexity Impact: {complexity_impact:+.1f}[/bold {impact_color}]")
                if ddd_violation_penalty > 0:
                    console.print(f"  • [bold red]DDD Violation Impact: -{ddd_violation_penalty:.1f}[/bold red]")
                if ddd_conversion_penalty > 0:
                    console.print(f"  • [bold red]DDD Conversion Impact: -{ddd_conversion_penalty:.1f} ({ddd_conversion_modules} modules)[/bold red]")
                console.print(f"  • [bold {impact_color}]Total Score Impact: {total_impact:+.1f}[/bold {impact_color}]")

        if architecture_data.get('ddd_issues'):
            # Separate DDD architecture violations from general structural issues
            ddd_violations = [issue for issue in architecture_data['ddd_issues']
                            if 'DDD architecture violations' in issue or
                               'Missing required domain component' in issue or
                               'forbidden in' in issue.lower()]
            other_issues = [issue for issue in architecture_data['ddd_issues']
                          if issue not in ddd_violations]

            if ddd_violations:
                console.print("\n[red]🚫 DDD Architecture Violations:[/red]")
                for issue in ddd_violations[:3]:  # Show top 3 DDD violations
                    console.print(f"  • {issue}")

            if other_issues:
                console.print("\n[yellow]⚠️  Other Structural Issues:[/yellow]")
                for issue in other_issues[:3]:  # Show top 3 other issues
                    console.print(f"  • {issue}")

        if architecture_data.get('ddd_recommendations'):
            # Separate DDD conversion recommendations from general recommendations
            conversion_recs = [rec for rec in architecture_data['ddd_recommendations']
                             if any(keyword in rec.lower() for keyword in
                                   ['split', 'break down', 'separate', 'extract', 'reduce complexity', 'move to'])]
            other_recs = [rec for rec in architecture_data['ddd_recommendations']
                         if rec not in conversion_recs]

            if conversion_recs:
                console.print("\n[orange]🔄 DDD Module Conversion Recommendations:[/orange]")
                for rec in conversion_recs[:3]:  # Show top 3 conversion recommendations
                    console.print(f"  • {rec}")

            if other_recs:
                console.print("\n[green]💡 DDD Structure Recommendations:[/green]")
                for rec in other_recs[:3]:  # Show top 3 structure recommendations
                    console.print(f"  • {rec}")

    # Critical issues
    if results.critical_issues:
        console.print("\n[red]🚨 Critical Issues:[/red]")
        for issue in results.critical_issues:
            console.print(f"  • {issue['issue']}")
    else:
        console.print("\n[green]✅ No critical issues found![/green]")

    # Priority improvements
    if results.priority_improvements:
        console.print(f"\n[blue]🎯 Priority Improvements ({results.estimated_effort_days} days):[/blue]")
        for rec in results.priority_improvements[:5]:  # Show top 5
            console.print(f"  • [{rec['priority'].upper()}] {rec['title']} ({rec['effort_days']} days)")

    # System metrics if available
    if results.performance.get('system_metrics'):
        metrics = results.performance['system_metrics']
        console.print("\n[purple]💻 System Metrics:[/purple]")
        console.print(f"  • CPU: {metrics.get('cpu_percent', 'N/A')}%")
        console.print(f"  • Memory: {metrics.get('memory_percent', 'N/A')}% ({metrics.get('memory_used_gb', 'N/A')}GB used)")


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
