"""
Architecture Analyzer
Handles all architecture-related quality assessments including DDD compliance,
REST API design, layer separation, and structural analysis.
"""

import os
import ast
import re
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import progress libraries for enhanced feedback
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

try:
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID, TimeRemainingColumn, MofNCompleteColumn
    from rich.console import Console
    HAS_RICH_PROGRESS = True
except ImportError:
    HAS_RICH_PROGRESS = False

# Try to import async libraries for parallel processing
try:
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    HAS_ASYNC = True
except ImportError:
    HAS_ASYNC = False

# Handle imports for both module and script execution
try:
    from config import AuditProfile, get_thresholds_for_profile
    from domain.entities.service_info import ServiceInfo
    from .base_analyzer import BaseAnalyzer
except ImportError:
    import sys
    from pathlib import Path
    current_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(current_dir))

    from config import AuditProfile
    from config.thresholds import get_thresholds_for_profile
    from infrastructure.analyzers.base_analyzer import BaseAnalyzer

    # Create a simple ServiceInfo if models doesn't exist
    from dataclasses import dataclass
    from pathlib import Path
    from typing import Dict, Any

    @dataclass
    class ServiceInfo:
        name: str
        path: Path
        type: str = "python"
        status: str = "unknown"
        metadata: Dict[str, Any] = None

        def __post_init__(self):
            if self.metadata is None:
                self.metadata = {}


@dataclass
class ArchitectureAnalysisResult:
    """Results from architecture analysis"""
    score: float
    ddd_compliance: float
    rest_compliance: float
    layer_separation: float
    ddd_issues: List[str]
    ddd_recommendations: List[str]
    file_metrics: Dict[str, Any]
    test_quality: Dict[str, Any]
    linting_quality: Dict[str, Any]
    endpoint_analysis: Dict[str, Any]
    complexity_analysis: Dict[str, Any]
    dependency_coupling: Dict[str, Any]
    dead_code_analysis: Dict[str, Any]
    test_quality_metrics: Dict[str, Any]
    domain_boundaries: Dict[str, Any]
    api_documentation: Dict[str, Any]
    code_documentation: Dict[str, Any]
    configuration_management: Dict[str, Any]
    logging_practices: Dict[str, Any]
    directory_analysis: Dict[str, Any]
    issues: List[str]
    recommendations: List[str]
    detailed_issues: List[Dict[str, Any]]
    # New fields with defaults
    empty_directories: float = 100.0  # New: Empty directories check
    requirements_file: float = 100.0  # New: Requirements file check
    docker_infrastructure: float = 100.0  # New: Docker/infrastructure config check
    dry_principles: float = 100.0  # New: DRY principles check
    kiss_principles: float = 100.0  # New: KISS principles check
    ddd_patterns: float = 100.0  # New: DDD patterns check
    rest_best_practices: float = 100.0  # New: REST best practices check
    documentation_quality: float = 100.0  # New: Documentation quality check


class ArchitectureAnalyzer(BaseAnalyzer):
    """Analyzer for architectural quality and compliance"""

    def __init__(self, profile: AuditProfile):
        super().__init__(profile)
        self._ddd_issues: List[str] = []
        self._ddd_recommendations: List[str] = []
        self._file_metrics: Dict[str, Any] = {}
        self._directory_analysis: Dict[str, Any] = {}

    async def analyze(self, service: ServiceInfo, full_audit: bool = False) -> ArchitectureAnalysisResult:
        """Perform complete architecture analysis"""
        # Set full audit mode in base class
        self.set_full_audit_mode(full_audit)

        # Initialize analysis storage
        self._ddd_issues = []
        self._ddd_recommendations = []
        self._detailed_issues = []
        self._file_metrics = {}


        # Note: Test quality and linting are now handled by separate analyzers
        # Initialize with basic results for backward compatibility
        test_quality_results = {
            'coverage_score': 0,
            'quality_score': 0,
            'structure_score': 0,
            'total_score': 0,
            'recommendations': []
        }
        linting_results = {
            'pylint_score': 0,
            'flake8_issues': 0,
            'total_issues': 0,
            'issues_by_type': {},
            'recommendations': []
        }

        # Analyze endpoints for REST compliance
        endpoint_results = self._analyze_endpoints_for_rest_compliance(service)

        # Basic complexity, coupling, dead code results for architecture focus
        complexity_results = {
            'high_complexity_functions': [],
            'total_functions_analyzed': 0,
            'complexity_distribution': {'low': 0, 'medium': 0, 'high': 0, 'very_high': 0},
            'average_complexity': 0.0,
            'recommendations': []
        }
        coupling_results = {
            'import_dependencies': {},
            'coupling_score': 0,
            'recommendations': []
        }
        dead_code_results = {
            'dead_code_lines': 0,
            'unused_functions': [],
            'recommendations': []
        }
        test_quality_metrics = {
            'total_test_files': 0,
            'test_naming_issues': 0,
            'recommendations': []
        }
        domain_boundaries = {
            'leaks_detected': 0,
            'boundary_violations': [],
            'layer_integrity': True,
            'recommendations': []
        }
        api_docs_quality = {
            'endpoints_documented': 0,
            'documentation_score': 0,
            'recommendations': []
        }
        code_documentation = {
            'docstring_coverage': 0.0,
            'undocumented_functions': 0,
            'recommendations': []
        }
        config_management = {
            'hardcoded_values': 0,
            'security_issues': 0,
            'recommendations': []
        }
        logging_practices = {
            'logging_usage': 0,
            'error_logging': 0,
            'recommendations': []
        }

        scores = {
            'ddd_compliance': await self._check_ddd_compliance(service),
            'rest_compliance': await self._check_rest_compliance(service),
            'layer_separation': await self._check_layer_separation(service),
            'empty_directories': await self._check_empty_directories(service),
            'requirements_file': await self._check_requirements_file(service),
            'docker_infrastructure': await self._check_docker_infrastructure_config(service),
            'dry_principles': await self._check_dry_principles(service),
            'kiss_principles': await self._check_kiss_principles(service),
            'ddd_patterns': await self._check_ddd_patterns(service),
            'rest_best_practices': await self._check_rest_best_practices(service),
            'documentation_quality': await self._check_documentation_quality(service)
        }

        # Calculate weighted architecture score using profile-specific weights
        # Get weights from profile settings, fallback to defaults
        arch_settings = getattr(self.profile, 'architecture', {}) if self.profile else {}

        ddd_weight = arch_settings.get('ddd_compliance_weight', 0.23)
        rest_weight = arch_settings.get('rest_compliance_weight', 0.18)
        layer_weight = arch_settings.get('layer_separation_weight', 0.09)
        empty_dirs_weight = arch_settings.get('empty_directories_weight', 0.04)
        req_file_weight = arch_settings.get('requirements_file_weight', 0.04)
        docker_weight = arch_settings.get('docker_infrastructure_weight', 0.04)
        dry_weight = arch_settings.get('dry_principles_weight', 0.14)
        kiss_weight = arch_settings.get('kiss_principles_weight', 0.09)
        ddd_patterns_weight = arch_settings.get('ddd_patterns_weight', 0.02)
        rest_bp_weight = arch_settings.get('rest_best_practices_weight', 0.02)
        docs_weight = arch_settings.get('documentation_quality_weight', 0.13)

        # Ensure weights sum to 1.0 (normalize if needed)
        total_weight = (ddd_weight + rest_weight + layer_weight + empty_dirs_weight +
                       req_file_weight + docker_weight + dry_weight + kiss_weight +
                       ddd_patterns_weight + rest_bp_weight + docs_weight)

        if total_weight > 0:
            # Normalize weights to sum to 1.0
            ddd_weight /= total_weight
            rest_weight /= total_weight
            layer_weight /= total_weight
            empty_dirs_weight /= total_weight
            req_file_weight /= total_weight
            docker_weight /= total_weight
            dry_weight /= total_weight
            kiss_weight /= total_weight
            ddd_patterns_weight /= total_weight
            rest_bp_weight /= total_weight
            docs_weight /= total_weight

        architecture_score = (
            scores['ddd_compliance'] * ddd_weight +
            scores['rest_compliance'] * rest_weight +
            scores['layer_separation'] * layer_weight +
            scores['empty_directories'] * empty_dirs_weight +
            scores['requirements_file'] * req_file_weight +
            scores['docker_infrastructure'] * docker_weight +
            scores['dry_principles'] * dry_weight +
            scores['kiss_principles'] * kiss_weight +
            scores['ddd_patterns'] * ddd_patterns_weight +
            scores['rest_best_practices'] * rest_bp_weight +
            scores['documentation_quality'] * docs_weight
        )

        return ArchitectureAnalysisResult(
            score=round(architecture_score, 2),
            ddd_compliance=scores['ddd_compliance'],
            rest_compliance=scores['rest_compliance'],
            layer_separation=scores['layer_separation'],
            empty_directories=scores['empty_directories'],
            requirements_file=scores['requirements_file'],
            docker_infrastructure=scores['docker_infrastructure'],
            dry_principles=scores['dry_principles'],
            kiss_principles=scores['kiss_principles'],
            ddd_patterns=scores['ddd_patterns'],
            rest_best_practices=scores['rest_best_practices'],
            documentation_quality=scores['documentation_quality'],
            ddd_issues=self._ddd_issues,
            ddd_recommendations=self._ddd_recommendations,
            file_metrics=self._file_metrics,
            test_quality=test_quality_results,
            linting_quality=linting_results,
            endpoint_analysis=endpoint_results,
            complexity_analysis=complexity_results,
            dependency_coupling=coupling_results,
            dead_code_analysis=dead_code_results,
            test_quality_metrics=test_quality_metrics,
            domain_boundaries=domain_boundaries,
            api_documentation=api_docs_quality,
            code_documentation=code_documentation,
            configuration_management=config_management,
            logging_practices=logging_practices,
            directory_analysis=self._directory_analysis,
            issues=self._identify_issues(scores),
            recommendations=self._generate_recommendations(scores),
            detailed_issues=self._detailed_issues
        )

    async def _check_ddd_compliance(self, service: ServiceInfo) -> float:
        """Check Domain-Driven Design compliance with STRICT enforcement."""
        logger.info(f"🚀 Starting DDD compliance analysis for {service.name} using STRICT profile")

        # Show overall progress with rich progress bar if available
        if HAS_RICH_PROGRESS:
            console = Console()
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=console,
                transient=True
            ) as progress:
                ddd_task = progress.add_task("🏗️ DDD Compliance Analysis", total=4)

                score = 0.0
                total_checks = 0

                # 1. STRICT Directory Structure Analysis (35 points)
                progress.update(ddd_task, description="📁 Phase 1/4: Directory Structure")
                structure_score = await self._analyze_strict_directory_structure(service)
                score += structure_score
                total_checks += 35
                progress.update(ddd_task, advance=1, description="📁 Phase 1/4: Directory Structure ✓")

                # 2. STRICT Domain Layer Completeness (25 points)
                progress.update(ddd_task, description="🏛️ Phase 2/4: Domain Layer")
                domain_score = await self._analyze_strict_domain_layer_completeness(service)
                score += domain_score
                total_checks += 25
                progress.update(ddd_task, advance=1, description="🏛️ Phase 2/4: Domain Layer ✓")

                # 3. STRICT Application Layer Patterns (20 points)
                progress.update(ddd_task, description="⚙️ Phase 3/4: Application Layer")
                app_score = await self._analyze_strict_application_layer_patterns(service)
                score += app_score
                total_checks += 20
                progress.update(ddd_task, advance=1, description="⚙️ Phase 3/4: Application Layer ✓")

                # 4. STRICT Clean Architecture & Layer Separation (20 points)
                progress.update(ddd_task, description="🏗️ Phase 4/4: Clean Architecture")
                architecture_score = await self._analyze_strict_clean_architecture_compliance(service)
                score += architecture_score
                total_checks += 20
                progress.update(ddd_task, advance=1, description="🏗️ Phase 4/4: Clean Architecture ✓")
        else:
            # Fallback without progress bar
            score = 0.0
            total_checks = 0

            # 1. STRICT Directory Structure Analysis (35 points)
            logger.info(f"📁 Phase 1/4: Directory structure analysis for {service.name}")
            structure_score = await self._analyze_strict_directory_structure(service)
            score += structure_score
            total_checks += 35
            logger.info(f"📁 Phase 1 completed: {structure_score:.1f}/35 points")

            # 2. STRICT Domain Layer Completeness (25 points)
            logger.info(f"🏛️  Phase 2/4: Domain layer analysis for {service.name}")
            domain_score = await self._analyze_strict_domain_layer_completeness(service)
            score += domain_score
            total_checks += 25
            logger.info(f"🏛️  Phase 2 completed: {domain_score:.1f}/25 points")

            # 3. STRICT Application Layer Patterns (20 points)
            logger.info(f"⚙️  Phase 3/4: Application layer analysis for {service.name}")
            app_score = await self._analyze_strict_application_layer_patterns(service)
            score += app_score
            total_checks += 20
            logger.info(f"⚙️  Phase 3 completed: {app_score:.1f}/20 points")

            # 4. STRICT Clean Architecture & Layer Separation (20 points)
            logger.info(f"🏗️  Phase 4/4: Clean architecture analysis for {service.name}")
            architecture_score = await self._analyze_strict_clean_architecture_compliance(service)
            score += architecture_score
            total_checks += 20
            logger.info(f"🏗️  Phase 4 completed: {architecture_score:.1f}/20 points")

        final_score = min(100, (score / max(1, total_checks)) * 100)
        logger.info(f"🎯 DDD compliance analysis completed for {service.name}: {final_score:.1f}/100 final score")

        return final_score

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
                            if lines > self.thresholds['file_limits']['max_lines_per_file']:  # Files over threshold
                                monolithic_files.append(f"{file_path.relative_to(service.path)} ({lines} lines)")
                                score -= 0.5  # Penalty for each monolithic file
                    except:
                        continue

        # Store metrics
        self._file_metrics = {
            'total_files': total_files,
            'monolithic_files': len(monolithic_files),
            'large_directories': len(large_directories),
            'directory_file_counts': directory_file_counts
        }

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
                'required': ['controllers', 'routes'],
                'recommended': ['models', 'middleware', 'api', 'schemas', 'responses'],
                'optional': ['web', 'templates', 'requests', 'dto', 'serializers'],
                'forbidden': ['entities', 'repositories', 'domain_services', 'config', 'cache',
                            'external_services', 'migrations', 'handlers', 'business_logic'],
                'forbidden_reason': 'Business logic in domain/application, infrastructure concerns elsewhere'
            },
            'presentation/routes': {
                'description': 'Route definitions organized by domain/feature',
                'required': ['__init__.py'],
                'recommended': ['analysis', 'documents', 'workflows', 'reports', 'health'],
                'optional': ['auth', 'users', 'admin', 'monitoring', 'metrics'],
                'forbidden': ['entities', 'repositories', 'services', 'config', 'cache'],
                'forbidden_reason': 'Routes should only contain endpoint definitions and imports'
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

        # Check routes directory structure (8 points)
        routes_score = 0
        routes_dirs = [d for d in all_dirs if 'presentation/routes' in d or 'routes' in d.split('/')]

        if routes_dirs:
            routes_score += 3  # Routes directory exists

            # Check for proper routes organization
            routes_subdirs = []
            for dir_path in routes_dirs:
                parts = dir_path.split('/')
                if len(parts) >= 3 and parts[-2] == 'routes':
                    routes_subdirs.append(parts[-1])

            # Check for domain/feature-based organization
            domain_features = ['analysis', 'documents', 'workflows', 'reports', 'health', 'auth', 'admin']
            feature_routes = sum(1 for subdir in routes_subdirs if subdir in domain_features)

            if feature_routes > 0:
                routes_score += 3  # Feature-based routes organization
                if len(routes_subdirs) >= 3:
                    routes_score += 2  # Multiple feature areas

            # Check for __init__.py in routes directory
            routes_init_found = False
            for root, dirs, files in os.walk(str(service.path)):
                if 'routes' in Path(root).relative_to(service.path).parts:
                    if '__init__.py' in files:
                        routes_init_found = True
                        break

            if routes_init_found:
                routes_score += 2  # Proper Python package structure
            else:
                issues_found.append("Missing __init__.py in routes directory")
                recommendations.append("Add __init__.py to routes directory for proper Python package")

            # Check for oversized route files
            large_route_files = []
            for root, dirs, files in os.walk(str(service.path)):
                if 'routes' in Path(root).relative_to(service.path).parts:
                    for file in files:
                        if file.endswith('.py') and not file.startswith('__'):
                            file_path = Path(root) / file
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    line_count = len(f.readlines())
                                    if line_count > 300:  # Routes files shouldn't be too large
                                        large_route_files.append(f"{file_path.relative_to(service.path)} ({line_count} lines)")
                                        routes_score -= 0.5
                            except:
                                continue

            if large_route_files:
                issues_found.append(f"Large route files detected: {', '.join(large_route_files[:2])}")
                recommendations.append("Split large route files into smaller domain-specific files")

        else:
            issues_found.append("Missing routes directory - required for DDD+REST architecture")
            recommendations.append("Create presentation/routes/ directory with domain-organized route files")
            routes_score -= 8  # Major penalty for missing routes

        score += max(0, routes_score)

        # Store directory analysis results for reporting
        self._directory_analysis = {
            'routes_score': routes_score,
            'total_files': total_files,
            'monolithic_files': len(monolithic_files),
            'large_directories': len(large_directories),
            'issues': issues_found,
            'recommendations': recommendations
        }

        return max(0, score)

    # Basic implementations for DDD analysis methods
    async def _analyze_domain_layer_quality(self, service: ServiceInfo) -> float:
        """Analyze domain layer quality"""
        # Basic domain analysis - check for domain directory and entities
        domain_score = 0.0

        if (service.path / "domain").exists():
            domain_score += 20  # Domain directory exists

            domain_files = list(service.path.glob("domain/**/*.py"))
            if domain_files:
                domain_score += 30  # Domain files exist

                # Check for basic DDD patterns
                has_entities = any("entity" in str(f).lower() or "model" in str(f).lower() for f in domain_files)
                has_services = any("service" in str(f).lower() for f in domain_files)

                if has_entities:
                    domain_score += 25
                if has_services:
                    domain_score += 25

        return min(100, domain_score)

    async def _analyze_application_layer_architecture(self, service: ServiceInfo) -> float:
        """Analyze application layer architecture"""
        app_score = 0.0

        if (service.path / "application").exists():
            app_score += 20  # Application directory exists

            app_files = list(service.path.glob("application/**/*.py"))
            if app_files:
                app_score += 30  # Application files exist

                # Check for CQRS/command patterns
                has_handlers = any("handler" in str(f).lower() for f in app_files)
                has_commands = any("command" in str(f).lower() or "query" in str(f).lower() for f in app_files)

                if has_handlers:
                    app_score += 25
                if has_commands:
                    app_score += 25

        return min(100, app_score)

    async def _analyze_clean_architecture_compliance(self, service: ServiceInfo) -> float:
        """Analyze clean architecture compliance"""
        arch_score = 100.0

        # Check for proper layer separation
        layers = ['domain', 'application', 'infrastructure', 'presentation']
        existing_layers = sum(1 for layer in layers if (service.path / layer).exists())

        if existing_layers >= 3:
            arch_score += 20  # Multiple layers exist
        elif existing_layers >= 2:
            arch_score += 10

        # Penalize if infrastructure depends on domain
        infra_files = list(service.path.glob("infrastructure/**/*.py"))
        domain_imports = 0

        for infra_file in infra_files[:5]:  # Check first 5 files
            try:
                with open(infra_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'from domain' in content or 'import domain' in content:
                        domain_imports += 1
            except Exception:
                continue

        if domain_imports > 0:
            arch_score -= min(30, domain_imports * 10)  # Penalty for layer violations

        return max(0, arch_score)

    async def _analyze_strict_directory_structure(self, service: ServiceInfo) -> float:
        """STRICT DDD directory structure enforcement with migration requirements."""
        score = 0.0
        critical_violations = 0
        files_analyzed = 0
        if self._full_audit:
            max_files_to_analyze = float('inf')  # No limit in full audit mode
            logger.info(f"🔍 Starting FULL DDD directory analysis for {service.name} (no file limit)")
        else:
            max_files_to_analyze = min(50, self.thresholds.get('architecture', {}).get('max_files_to_analyze', 50))
            logger.info(f"🔍 Starting STRICT DDD directory analysis for {service.name} (max files: {max_files_to_analyze})")

        # Get all Python files and analyze their locations
        python_files = []
        legacy_module_files = []
        mislocated_business_logic = []

        # Use enhanced progress bar with batch processing
        if HAS_RICH_PROGRESS:
            console = Console()
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TextColumn("•"),
                TimeRemainingColumn(),
                console=console,
                transient=True
            ) as progress:
                analysis_task = progress.add_task(f"🔍 Discovering Python files in {service.name}...", total=None)

                # First pass: collect all files
                all_python_files = []
                for root, dirs, files in os.walk(str(service.path)):
                    for file in files:
                        if file.endswith('.py') and not file.startswith('.') and not file.startswith('test_'):
                            file_path = Path(root) / file
                            all_python_files.append(file_path)

                # Limit to max files (handle infinity case)
                if max_files_to_analyze == float('inf'):
                    python_files_to_analyze = all_python_files
                else:
                    python_files_to_analyze = all_python_files[:int(max_files_to_analyze)]
                progress.update(analysis_task, total=len(python_files_to_analyze),
                              description=f"📊 Analyzing {len(python_files_to_analyze)} Python files in {service.name}")

                # Process files in batches for better performance with detailed progress
                batch_size = min(20, len(python_files_to_analyze))  # Process in batches of 20
                total_batches = (len(python_files_to_analyze) + batch_size - 1) // batch_size

                logger.info("🔄 Processing %d files in %d batches (batch size: %d)",
                           len(python_files_to_analyze), total_batches, batch_size)

                batch_start_time = time.time()

                for batch_idx, i in enumerate(range(0, len(python_files_to_analyze), batch_size)):
                    batch = python_files_to_analyze[i:i + batch_size]
                    batch_desc = f"🔍 Batch {batch_idx + 1}/{total_batches}: {len(batch)} files"

                    # Update progress bar with current batch
                    progress.update(analysis_task, description=batch_desc)

                    try:
                        batch_start = time.time()
                        batch_results = await self._process_file_batch(batch, service)
                        batch_time = time.time() - batch_start

                        # Log batch completion with timing
                        logger.debug("✅ Batch %d/%d complete (%.2fs): %d files, %d violations",
                                   batch_idx + 1, total_batches, batch_time,
                                   len(batch_results.get('files', [])),
                                   batch_results.get('critical_violations', 0))

                    except Exception as e:
                        logger.error("❌ Batch %d/%d failed: %s", batch_idx + 1, total_batches, e)
                        batch_results = {'files': [], 'legacy_modules': [], 'mislocated_logic': [], 'critical_violations': 0, 'errors': [str(e)]}

                    # Update results
                    python_files.extend(batch_results['files'])
                    legacy_module_files.extend(batch_results['legacy_modules'])
                    mislocated_business_logic.extend(batch_results['mislocated_logic'])
                    critical_violations += batch_results['critical_violations']

                    # Update progress
                    files_analyzed += len(batch)
                    progress.update(analysis_task, advance=len(batch),
                                  description=f"📊 Processed {files_analyzed}/{len(python_files_to_analyze)} files • {critical_violations} violations found")

                    # Safety check (only applies when not in full audit mode)
                    if not self._full_audit and files_analyzed >= max_files_to_analyze:
                        progress.update(analysis_task, description="⚠️ Analysis limited - timeout prevention")
                        logger.warning(f"⚠️ ANALYSIS LIMITED: Only analyzed first {max_files_to_analyze} Python files to prevent timeout")
                        self._ddd_issues.append(f"⚠️ ANALYSIS LIMITED: Only analyzed first {max_files_to_analyze} Python files to prevent timeout")
                        break
        else:
            # Fallback to simple logging without progress bar
            for root, dirs, files in os.walk(str(service.path)):
                for file in files:
                    if file.endswith('.py') and not file.startswith('.') and not file.startswith('test_'):
                        file_path = Path(root) / file
                        rel_path = file_path.relative_to(service.path)

                        python_files.append(file_path)
                        files_analyzed += 1

                        # Check for STRICT DDD violations
                        path_parts = rel_path.parts

                        # Progress feedback every 10 files
                        if files_analyzed % 10 == 0:
                            logger.info(f"📊 Analyzed {files_analyzed}/{max_files_to_analyze} files in {service.name}")

                        # Safety limit to prevent hanging on large codebases (only in non-full audit mode)
                        if not self._full_audit and files_analyzed > max_files_to_analyze:
                            logger.warning(f"⚠️ ANALYSIS LIMITED: Only analyzed first {max_files_to_analyze} Python files to prevent timeout")
                            self._ddd_issues.append(f"⚠️ ANALYSIS LIMITED: Only analyzed first {max_files_to_analyze} Python files to prevent timeout")
                            break

                        # CRITICAL: Files in modules/ directory with business logic
                        if 'modules' in path_parts and len(path_parts) >= 2:
                            try:
                                # Limit file size to prevent reading massive files
                                file_size = file_path.stat().st_size
                                if file_size > 100000:  # Skip files larger than 100KB
                                    continue

                                with open(file_path, 'r', encoding='utf-8') as f:
                                    # Read only first 1000 lines to avoid massive files
                                    content = ''.join(f.readline() for _ in range(1000))

                                # Check for business logic patterns (optimized search)
                                business_logic_patterns = [
                                    'class.*Entity', 'class.*Service', 'class.*Repository',
                                    'def.*handle', 'def.*execute', 'def.*process',
                                    'from domain', 'from application', 'import domain', 'import application'
                                ]

                                has_business_logic = any(pattern in content for pattern in business_logic_patterns)

                                if has_business_logic:
                                    legacy_module_files.append(str(rel_path))
                                    critical_violations += 1
                                    self._ddd_issues.append(f"🚨 CRITICAL: Business logic in legacy modules/ directory: {rel_path}")
                                    self._ddd_recommendations.append(f"🔄 MIGRATE: Move {rel_path} to appropriate DDD layer (domain/, application/, infrastructure/)")

                            except Exception:
                                continue

                        # Check for presentation layer violations (business logic in controllers/routes)
                        if any(layer in path_parts for layer in ['presentation', 'routes', 'controllers']):
                            try:
                                # Limit file size to prevent reading massive files
                                file_size = file_path.stat().st_size
                                if file_size > 50000:  # Skip files larger than 50KB for presentation checks
                                    continue

                                with open(file_path, 'r', encoding='utf-8') as f:
                                    # Read only first 500 lines for presentation layer checks
                                    content = ''.join(f.readline() for _ in range(500))

                                # Check for forbidden business logic in presentation layer
                                forbidden_patterns = [
                                    'class.*Entity', 'class.*Service', 'class.*Repository',
                                    'def.*calculate', 'def.*validate', 'def.*process',
                                    'from domain', 'from application', 'import domain', 'import application'
                                ]

                                has_business_logic = any(pattern in content for pattern in forbidden_patterns)

                                if has_business_logic and self.thresholds['architecture'].get('forbid_presentation_business_logic', False):
                                    mislocated_business_logic.append(str(rel_path))
                                    critical_violations += 1
                                    self._ddd_issues.append(f"🚨 CRITICAL: Business logic in presentation layer: {rel_path}")
                                    self._ddd_recommendations.append(f"🔄 REFACTOR: Move business logic from {rel_path} to domain/ or application/ layers")

                            except Exception:
                                continue

                if not self._full_audit and files_analyzed > max_files_to_analyze:
                    break

        # Apply STRICT scoring penalties
        if critical_violations > 0:
            # Zero tolerance for legacy module files with business logic
            if legacy_module_files:
                score -= 50  # Major penalty for each legacy file
                self._ddd_issues.append(f"🚨 ZERO TOLERANCE: {len(legacy_module_files)} files with business logic in modules/ directory must be migrated")

            if mislocated_business_logic:
                score -= 30  # Major penalty for presentation layer violations
                self._ddd_issues.append(f"🚨 STRICT VIOLATION: {len(mislocated_business_logic)} presentation files contain business logic")

        # Check for required DDD layer presence
        required_layers = ['domain', 'application', 'infrastructure', 'presentation']
        existing_layers = sum(1 for layer in required_layers if (service.path / layer).exists())

        if existing_layers < 4:
            missing_layers = [layer for layer in required_layers if not (service.path / layer).exists()]
            score -= 20 * len(missing_layers)
            self._ddd_issues.append(f"🚨 MISSING DDD LAYERS: {missing_layers} - all four layers required")
            self._ddd_recommendations.append(f"📁 CREATE: Missing DDD layers: {', '.join(missing_layers)}")

        # Routes directory enforcement
        if not any('routes' in str(p) for p in python_files):
            score -= 25
            self._ddd_issues.append("🚨 MISSING ROUTES: presentation/routes/ directory required for DDD+REST")
            self._ddd_recommendations.append("📁 CREATE: presentation/routes/ directory with domain-organized route files")

        # Check for oversized files (maintainability issue)
        oversized_files = []
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
                    max_lines = self.thresholds['file_limits']['max_lines_per_file']
                    if lines > max_lines:
                        oversized_files.append(f"{file_path.relative_to(service.path)} ({lines} lines)")
                        self._add_oversized_file_issue(
                            file_path=file_path,
                            line_count=lines,
                            threshold=max_lines
                        )
            except Exception:
                continue

        if oversized_files:
            score -= 5 * len(oversized_files)
            self._ddd_issues.append(f"📏 OVERSIZED FILES: {len(oversized_files)} files exceed {self.thresholds['file_limits']['max_lines_per_file']} lines")
            self._ddd_recommendations.append(f"🔨 REFACTOR: Split oversized files: {', '.join(oversized_files[:3])}")

        logger.info(f"✅ Completed STRICT DDD directory analysis for {service.name}: {files_analyzed} files analyzed, {critical_violations} critical violations found")

        return max(0, score)

    async def _process_file_batch(self, file_batch: List[Path], service: ServiceInfo) -> Dict[str, Any]:
        """Process a batch of files for STRICT DDD violations with optimized parallel processing."""
        batch_files = []
        batch_legacy_modules = []
        batch_mislocated_logic = []
        batch_critical_violations = 0
        batch_errors = []

        # Adaptive batch processing based on system resources and batch size
        batch_size = len(file_batch)

        if HAS_ASYNC and batch_size > 3:
            # Dynamic worker count based on batch size and system capabilities
            max_workers = min(
                batch_size,  # Don't exceed batch size
                8 if batch_size > 20 else 4,  # Scale up for larger batches
                os.cpu_count() or 4  # Respect system CPU count
            )

            try:
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="file-analyzer") as executor:
                    # Create tasks with error handling
                    tasks = []
                    for file_path in file_batch:
                        task = loop.run_in_executor(
                            executor,
                            self._analyze_single_file_safe,
                            file_path,
                            service
                        )
                        tasks.append(task)

                    # Process results with progress tracking for large batches
                    if batch_size > 10:
                        logger.debug(f"🔄 Processing {batch_size} files in parallel with {max_workers} workers")

                    # Gather results with timeout protection
                    try:
                        results = await asyncio.wait_for(
                            asyncio.gather(*tasks, return_exceptions=True),
                            timeout=30.0  # 30 second timeout per batch
                        )
                    except asyncio.TimeoutError:
                        logger.warning(f"⏰ Batch processing timeout after 30s for {batch_size} files")
                        # Fall back to sequential processing for remaining files
                        results = []
                        for file_path in file_batch:
                            try:
                                result = self._analyze_single_file_safe(file_path, service)
                                results.append(result)
                            except Exception as e:
                                batch_errors.append(f"File {file_path}: {e}")
                                results.append(None)

                    # Process results
                    for i, result in enumerate(results):
                        if result is None:
                            continue
                        elif isinstance(result, Exception):
                            batch_errors.append(f"File {file_batch[i]}: {result}")
                            continue
                        elif isinstance(result, dict):
                            batch_files.append(result.get('file'))
                            if result.get('legacy_module'):
                                batch_legacy_modules.append(result['legacy_module'])
                                batch_critical_violations += 1
                            if result.get('mislocated_logic'):
                                batch_mislocated_logic.append(result['mislocated_logic'])
                                batch_critical_violations += 1

            except Exception as e:
                logger.warning(f"Parallel processing failed, falling back to sequential: {e}")
                # Fall back to sequential processing
                for file_path in file_batch:
                    result = self._analyze_single_file_safe(file_path, service)
                    batch_files.append(result.get('file', file_path))
                    if result.get('legacy_module'):
                        batch_legacy_modules.append(result['legacy_module'])
                        batch_critical_violations += 1
                    if result.get('mislocated_logic'):
                        batch_mislocated_logic.append(result['mislocated_logic'])
                        batch_critical_violations += 1
        else:
            # Sequential processing for small batches
            for file_path in file_batch:
                result = self._analyze_single_file_safe(file_path, service)
                batch_files.append(result.get('file', file_path))
                if result.get('legacy_module'):
                    batch_legacy_modules.append(result['legacy_module'])
                    batch_critical_violations += 1
                if result.get('mislocated_logic'):
                    batch_mislocated_logic.append(result['mislocated_logic'])
                    batch_critical_violations += 1

        # Log batch summary if there were errors
        if batch_errors:
            logger.warning(f"⚠️  {len(batch_errors)} errors in batch processing: {batch_errors[:3]}...")

        return {
            'files': batch_files,
            'legacy_modules': batch_legacy_modules,
            'mislocated_logic': batch_mislocated_logic,
            'critical_violations': batch_critical_violations,
            'errors': batch_errors
        }

    def _analyze_single_file_safe(self, file_path: Path, service: ServiceInfo) -> Dict[str, Any]:
        """Safely analyze a single file with comprehensive error handling."""
        try:
            return self._analyze_single_file(file_path, service)
        except Exception as e:
            logger.debug(f"Error analyzing file {file_path}: {e}")
            # Return safe default result
            return {
                'file': file_path,
                'legacy_module': None,
                'mislocated_logic': None,
                'error': str(e)
            }

    def _analyze_single_file(self, file_path: Path, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze a single file for STRICT DDD violations."""
        try:
            rel_path = file_path.relative_to(service.path)
        except ValueError:
            # File is not within service path
            return {
                'file': file_path,
                'legacy_module': None,
                'mislocated_logic': None
            }

        path_parts = rel_path.parts

        result = {
            'file': file_path,
            'legacy_module': None,
            'mislocated_logic': None
        }

        # CRITICAL: Files in modules/ directory with business logic
        if 'modules' in path_parts and len(path_parts) >= 2:
            try:
                # Limit file size to prevent reading massive files
                file_size = file_path.stat().st_size
                if file_size > 100000:  # Skip files larger than 100KB
                    return result

                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # Read only first 1000 lines to avoid massive files
                    content = ''.join(f.readline() for _ in range(1000))

                # Check for business logic patterns (optimized search)
                business_logic_patterns = [
                    'class.*Entity', 'class.*Service', 'class.*Repository',
                    'def.*handle', 'def.*execute', 'def.*process',
                    'from domain', 'from application', 'import domain', 'import application'
                ]

                has_business_logic = any(pattern in content for pattern in business_logic_patterns)

                if has_business_logic:
                    result['legacy_module'] = str(rel_path)
                    self._ddd_issues.append(f"🚨 CRITICAL: Business logic in legacy modules/ directory: {rel_path}")
                    self._ddd_recommendations.append(f"🔄 MIGRATE: Move {rel_path} to appropriate DDD layer (domain/, application/, infrastructure/)")

            except (OSError, UnicodeDecodeError) as e:
                # Skip files that can't be read or have encoding issues
                logger.debug(f"Skipping file {file_path} due to read error: {e}")
                return result

        # Check for presentation layer violations (business logic in controllers/routes)
        if any(layer in path_parts for layer in ['presentation', 'routes', 'controllers']):
            try:
                # Limit file size to prevent reading massive files
                file_size = file_path.stat().st_size
                if file_size > 50000:  # Skip files larger than 50KB for presentation checks
                    return result

                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # Read only first 500 lines for presentation layer checks
                    content = ''.join(f.readline() for _ in range(500))

                # Check for forbidden business logic in presentation layer
                forbidden_patterns = [
                    'class.*Entity', 'class.*Service', 'class.*Repository',
                    'def.*calculate', 'def.*validate', 'def.*process',
                    'from domain', 'from application', 'import domain', 'import application'
                ]

                has_business_logic = any(pattern in content for pattern in forbidden_patterns)

                if has_business_logic and self.thresholds['architecture'].get('forbid_presentation_business_logic', False):
                    result['mislocated_logic'] = str(rel_path)
                    self._ddd_issues.append(f"🚨 CRITICAL: Business logic in presentation layer: {rel_path}")
                    self._ddd_recommendations.append(f"🔄 REFACTOR: Move business logic from {rel_path} to domain/ or application/ layers")

            except (OSError, UnicodeDecodeError) as e:
                # Skip files that can't be read or have encoding issues
                logger.debug(f"Skipping presentation file {file_path} due to read error: {e}")
                return result

        return result

    def _check_domain_import_violations(self, domain_file: Path, service: ServiceInfo) -> int:
        """Check a single domain file for import violations. Returns number of violations found."""
        violations = 0
        try:
            with open(domain_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Domain layer should NOT import from infrastructure or presentation
            forbidden_imports = ['from infrastructure', 'from presentation', 'import infrastructure', 'import presentation']
            if any(forbidden in content for forbidden in forbidden_imports):
                violations += 1
                self._ddd_issues.append(f"🚨 DOMAIN VIOLATION: {domain_file.relative_to(service.path)} imports from infrastructure/presentation")
                self._ddd_recommendations.append(f"🔄 REFACTOR: Remove infrastructure/presentation imports from domain layer")

        except Exception:
            # Skip files that can't be read
            pass

        return violations

    async def _check_empty_directories(self, service: ServiceInfo) -> float:
        """Check for empty directories that should be removed or populated."""
        score = 100.0
        empty_dirs = []

        try:
            # Walk through service directory
            for root, dirs, files in os.walk(str(service.path)):
                # Skip common directories that should be empty
                skip_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules',
                           '.DS_Store', 'Thumbs.db', '.vscode', '.idea'}

                for dir_name in dirs:
                    dir_path = Path(root) / dir_name

                    # Skip if it's in our skip list or starts with dot
                    if dir_name in skip_dirs or dir_name.startswith('.'):
                        continue

                    try:
                        # Check if directory is empty (no files, no subdirs)
                        contents = list(dir_path.iterdir())
                        if not contents:
                            empty_dirs.append(str(dir_path.relative_to(service.path)))
                            score -= 5  # Penalty for each empty directory
                            self._add_empty_directory_issue(directory_path=dir_path)
                    except (OSError, PermissionError):
                        # Skip directories we can't access
                        continue

        except Exception as e:
            logger.warning(f"Error checking empty directories for {service.name}: {e}")
            return 80.0  # Partial credit if we can't check

        if empty_dirs:
            self._ddd_issues.append(f"🗂️ EMPTY DIRECTORIES: {len(empty_dirs)} empty directories found")
            self._ddd_recommendations.append(f"🧹 CLEANUP: Remove or populate empty directories: {', '.join(empty_dirs[:3])}")

        return max(0, score)

    async def _check_requirements_file(self, service: ServiceInfo) -> float:
        """Check if requirements.txt or similar files are up to date."""
        score = 100.0
        issues = []

        try:
            service_path = Path(service.path)

            # Check for requirements files
            requirements_files = [
                'requirements.txt',
                'requirements-dev.txt',
                'pyproject.toml',
                'setup.py',
                'Pipfile',
                'poetry.lock'
            ]

            found_req_files = []
            for req_file in requirements_files:
                if (service_path / req_file).exists():
                    found_req_files.append(req_file)

            if not found_req_files:
                score -= 30
                issues.append("No requirements/dependency files found")
            else:
                # Check if requirements.txt exists and is not empty
                req_txt = service_path / 'requirements.txt'
                if req_txt.exists():
                    try:
                        content = req_txt.read_text()
                        if not content.strip():
                            score -= 20
                            issues.append("requirements.txt is empty")
                        elif len(content.strip().split('\n')) < 3:
                            score -= 10
                            issues.append("requirements.txt has very few dependencies")
                    except Exception:
                        score -= 15
                        issues.append("Cannot read requirements.txt")

                # Check for outdated dependency management
                if 'setup.py' in found_req_files and 'pyproject.toml' not in found_req_files:
                    score -= 5
                    issues.append("Consider migrating from setup.py to pyproject.toml")

                # Check for lock files
                has_lock = any(file.endswith('.lock') or 'poetry.lock' in found_req_files for file in found_req_files)
                if not has_lock and len(found_req_files) > 1:
                    score -= 5
                    issues.append("Consider using lock files for reproducible builds")

        except Exception as e:
            logger.warning(f"Error checking requirements files for {service.name}: {e}")
            return 70.0  # Partial credit if we can't check

        if issues:
            self._ddd_issues.extend([f"📦 REQUIREMENTS: {issue}" for issue in issues])
            if score < 80:
                self._ddd_recommendations.append("📦 DEPENDENCIES: Review and update dependency management files")

        return max(0, score)

    async def _check_docker_infrastructure_config(self, service: ServiceInfo) -> float:
        """Check Docker and infrastructure configuration compliance."""
        score = 100.0
        issues = []

        try:
            service_path = Path(service.path)
            project_root = service_path.parent.parent  # Go up to hackathon root

            # 1. Check if service has Dockerfile
            dockerfile = service_path / 'Dockerfile'
            if not dockerfile.exists():
                score -= 25
                issues.append("Missing Dockerfile")
            else:
                # Basic Dockerfile checks
                try:
                    content = dockerfile.read_text()
                    if 'FROM ' not in content:
                        score -= 10
                        issues.append("Dockerfile missing FROM instruction")
                    if 'EXPOSE ' not in content:
                        score -= 5
                        issues.append("Dockerfile missing EXPOSE instruction")
                except Exception:
                    score -= 5
                    issues.append("Cannot read Dockerfile")

            # 2. Check if service is in docker-compose.dev.yml
            compose_file = project_root / 'docker-compose.dev.yml'
            if compose_file.exists():
                try:
                    import yaml
                    with open(compose_file, 'r') as f:
                        compose_config = yaml.safe_load(f)

                    if 'services' in compose_config and service.name not in compose_config['services']:
                        score -= 20
                        issues.append(f"Service not found in docker-compose.dev.yml")
                    else:
                        # Check service configuration
                        service_config = compose_config['services'].get(service.name, {})
                        if 'build' not in service_config and 'image' not in service_config:
                            score -= 10
                            issues.append("Service missing build or image configuration")
                        if 'ports' not in service_config:
                            score -= 5
                            issues.append("Service missing port configuration")
                except Exception as e:
                    logger.warning(f"Error reading docker-compose file: {e}")
                    score -= 5
                    issues.append("Cannot validate docker-compose configuration")

            # 3. Check for port conflicts using existing script
            port_conflicts = await self._check_port_conflicts(service)
            if port_conflicts > 0:
                score -= min(30, port_conflicts * 10)  # Up to 30 points penalty
                issues.append(f"Port conflicts detected: {port_conflicts} issues")

            # 4. Check Makefile integration
            makefile = project_root / 'Makefile'
            if makefile.exists():
                try:
                    content = makefile.read_text()
                    service_in_makefile = service.name in content
                    if not service_in_makefile:
                        score -= 5
                        issues.append("Service not referenced in Makefile")
                except Exception:
                    score -= 2
                    issues.append("Cannot validate Makefile integration")

            # 5. Check for health checks
            if dockerfile.exists():
                try:
                    dockerfile_content = dockerfile.read_text()
                    if 'HEALTHCHECK' not in dockerfile_content:
                        score -= 5
                        issues.append("Dockerfile missing HEALTHCHECK instruction")
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"Error checking Docker/infrastructure config for {service.name}: {e}")
            return 60.0  # Partial credit if we can't check

        if issues:
            self._ddd_issues.extend([f"🐳 DOCKER/INFRA: {issue}" for issue in issues])
            if score < 70:
                self._ddd_recommendations.append("🐳 INFRASTRUCTURE: Review Docker and CI/CD configuration compliance")

        return max(0, score)

    async def _check_port_conflicts(self, service: ServiceInfo) -> int:
        """Check for port conflicts using the existing port conflict detector."""
        conflicts = 0

        try:
            # Use the existing port conflict detector
            from scripts.hardening.port_conflict_detector import PortConflictDetector

            detector = PortConflictDetector()
            compose_config = detector.load_docker_compose_config()
            service_ports = detector.extract_ports_from_compose(compose_config)

            # Check conflicts for this specific service
            if service.name in service_ports:
                port_conflicts = detector.detect_port_conflicts()

                # Count conflicts involving this service
                for conflict in port_conflicts:
                    if service.name in conflict.conflicting_services:
                        conflicts += 1

        except Exception as e:
            logger.debug(f"Error checking port conflicts for {service.name}: {e}")
            # Return 0 conflicts if we can't check (don't penalize)
            return 0

        return conflicts

    async def _check_dry_principles(self, service: ServiceInfo) -> float:
        """Check adherence to DRY (Don't Repeat Yourself) principles"""
        logger.info("🔄 Checking DRY principles compliance...")

        dry_score = 100.0
        dry_issues = []
        dry_recommendations = []

        try:
            # Analyze code duplication patterns
            duplicate_patterns = await self._analyze_code_duplication(service)
            if duplicate_patterns > 0:
                dry_score -= min(duplicate_patterns * 5, 40)  # Max 40 point penalty
                dry_issues.append(f"Found {duplicate_patterns} code duplication patterns")
                dry_recommendations.append("🔄 Extract common code into shared utilities or base classes")

            # Check for repeated configuration patterns
            config_duplication = await self._analyze_config_duplication(service)
            if config_duplication > 0:
                dry_score -= min(config_duplication * 3, 20)  # Max 20 point penalty
                dry_issues.append(f"Configuration duplication detected in {config_duplication} areas")
                dry_recommendations.append("⚙️ Centralize configuration management and eliminate duplicates")

            # Analyze utility function reuse
            utility_reuse_score = await self._analyze_utility_reuse(service)
            dry_score = min(dry_score, utility_reuse_score)

            # Check for repeated error handling patterns
            error_pattern_duplication = await self._analyze_error_pattern_duplication(service)
            if error_pattern_duplication > 0:
                dry_score -= min(error_pattern_duplication * 2, 15)  # Max 15 point penalty
                dry_recommendations.append("🚨 Standardize error handling patterns across the service")

        except Exception as e:
            logger.warning(f"DRY principles check failed: {e}")
            dry_score = 30.0  # Harsh penalty for analysis failure

        # Apply stricter penalties based on profile name
        if self.profile and hasattr(self.profile, 'name') and self.profile.name == 'strict':
            logger.debug("Applying strict mode penalties to DRY principles")
            # In strict mode, penalize poor DRY compliance more heavily
            if dry_score < 70:
                logger.debug(f"DRY score {dry_score} < 70, applying -20 penalty")
                dry_score -= 20  # Additional 20 point penalty for poor DRY in strict mode
            elif dry_score < 85:
                logger.debug(f"DRY score {dry_score} < 85, applying -10 penalty")
                dry_score -= 10  # Additional 10 point penalty for mediocre DRY in strict mode

        if dry_issues:
            self._ddd_issues.extend([f"🔄 DRY: {issue}" for issue in dry_issues])
        if dry_recommendations:
            self._ddd_recommendations.extend(dry_recommendations)

        logger.info(f"✅ DRY principles analysis complete: {dry_score:.1f}/100")
        return max(0.0, dry_score)

    async def _check_kiss_principles(self, service: ServiceInfo) -> float:
        """Check adherence to KISS (Keep It Simple, Stupid) principles"""
        logger.info("🎯 Checking KISS principles compliance...")

        kiss_score = 100.0
        kiss_issues = []
        kiss_recommendations = []

        try:
            # Analyze method complexity
            method_complexity_issues = await self._analyze_method_complexity(service)
            if method_complexity_issues > 0:
                kiss_score -= min(method_complexity_issues * 4, 35)  # Max 35 point penalty
                kiss_issues.append(f"Found {method_complexity_issues} overly complex methods (>15 cyclomatic complexity)")
                kiss_recommendations.append("🧩 Refactor complex methods into smaller, focused functions")

            # Check class responsibility (Single Responsibility Principle)
            class_responsibility_issues = await self._analyze_class_responsibility(service)
            if class_responsibility_issues > 0:
                kiss_score -= min(class_responsibility_issues * 3, 25)  # Max 25 point penalty
                kiss_issues.append(f"Found {class_responsibility_issues} classes violating Single Responsibility Principle")
                kiss_recommendations.append("📦 Split multi-responsibility classes into focused components")

            # Analyze unnecessary abstraction layers
            abstraction_overkill = await self._analyze_abstraction_layers(service)
            if abstraction_overkill > 0:
                kiss_score -= min(abstraction_overkill * 5, 20)  # Max 20 point penalty
                kiss_issues.append(f"Detected {abstraction_overkill} unnecessary abstraction layers")
                kiss_recommendations.append("🏗️ Simplify architecture by removing over-engineered abstractions")

            # Check for over-engineering patterns
            over_engineering_score = await self._analyze_over_engineering(service)
            kiss_score = min(kiss_score, over_engineering_score)

        except Exception as e:
            logger.warning(f"KISS principles check failed: {e}")
            kiss_score = 40.0  # Harsh penalty for analysis failure

        # Apply stricter penalties based on profile name
        if self.profile and hasattr(self.profile, 'name') and self.profile.name == 'strict':
            # In strict mode, penalize poor KISS compliance more heavily
            if kiss_score < 80:
                kiss_score -= 15  # Additional 15 point penalty for poor KISS in strict mode
            elif kiss_score < 90:
                kiss_score -= 8   # Additional 8 point penalty for mediocre KISS in strict mode

        if kiss_issues:
            self._ddd_issues.extend([f"🎯 KISS: {issue}" for issue in kiss_issues])
        if kiss_recommendations:
            self._ddd_recommendations.extend(kiss_recommendations)

        logger.info(f"✅ KISS principles analysis complete: {kiss_score:.1f}/100")
        return max(0.0, kiss_score)

    async def _check_ddd_patterns(self, service: ServiceInfo) -> float:
        """Check implementation of advanced DDD patterns"""
        logger.info("🏛️ Checking DDD patterns implementation...")

        ddd_pattern_score = 100.0
        pattern_issues = []
        pattern_recommendations = []

        try:
            # Check for proper entity validation
            entity_validation_score = await self._analyze_entity_validation(service)
            ddd_pattern_score = min(ddd_pattern_score, entity_validation_score)

            # Analyze repository pattern implementation
            repository_pattern_score = await self._analyze_repository_patterns(service)
            ddd_pattern_score = min(ddd_pattern_score, repository_pattern_score)

            # Check for value object immutability
            value_object_score = await self._analyze_value_objects(service)
            ddd_pattern_score = min(ddd_pattern_score, value_object_score)

            # Analyze aggregate root identification
            aggregate_root_score = await self._analyze_aggregate_roots(service)
            ddd_pattern_score = min(ddd_pattern_score, aggregate_root_score)

            # Check domain event implementation
            domain_events_score = await self._analyze_domain_events(service)
            ddd_pattern_score = min(ddd_pattern_score, domain_events_score)

            if ddd_pattern_score < 80:
                pattern_issues.append("DDD patterns implementation could be improved")
                pattern_recommendations.append("🎯 Implement proper DDD patterns: entities, value objects, aggregates, domain events")

        except Exception as e:
            logger.warning(f"DDD patterns check failed: {e}")
            ddd_pattern_score = 50.0

        if pattern_issues:
            self._ddd_issues.extend(pattern_issues)
        if pattern_recommendations:
            self._ddd_recommendations.extend(pattern_recommendations)

        logger.info(f"✅ DDD patterns analysis complete: {ddd_pattern_score:.1f}/100")
        return max(0.0, ddd_pattern_score)

    async def _check_rest_best_practices(self, service: ServiceInfo) -> float:
        """Check REST API best practices implementation"""
        logger.info("🌐 Checking REST best practices...")

        rest_bp_score = 100.0
        rest_issues = []
        rest_recommendations = []

        try:
            # Analyze HTTP method usage
            http_method_score = await self._analyze_http_methods(service)
            rest_bp_score = min(rest_bp_score, http_method_score)

            # Check status code usage patterns
            status_code_score = await self._analyze_status_codes(service)
            rest_bp_score = min(rest_bp_score, status_code_score)

            # Analyze resource naming conventions
            naming_convention_score = await self._analyze_resource_naming(service)
            rest_bp_score = min(rest_bp_score, naming_convention_score)

            # Check for HATEOAS implementation
            hateoas_score = await self._analyze_hateoas(service)
            rest_bp_score = min(rest_bp_score, hateoas_score)

            # Analyze content negotiation
            content_negotiation_score = await self._analyze_content_negotiation(service)
            rest_bp_score = min(rest_bp_score, content_negotiation_score)

            if rest_bp_score < 80:
                rest_issues.append("REST API could follow more best practices")
                rest_recommendations.append("📡 Implement REST best practices: proper HTTP methods, status codes, HATEOAS, content negotiation")

        except Exception as e:
            logger.warning(f"REST best practices check failed: {e}")
            rest_bp_score = 50.0

        if rest_issues:
            self._ddd_issues.extend(rest_issues)
        if rest_recommendations:
            self._ddd_recommendations.extend(rest_recommendations)

        logger.info(f"✅ REST best practices analysis complete: {rest_bp_score:.1f}/100")
        return max(0.0, rest_bp_score)

    async def _check_documentation_quality(self, service: ServiceInfo) -> float:
        """Analyze documentation quality including README and other docs"""
        logger.info("📚 Checking documentation quality...")

        doc_score = 100.0
        doc_issues = []
        doc_recommendations = []

        try:
            # Look for README files
            logger.debug("🔍 Scanning for documentation files...")
            readme_files = []
            for pattern in ['README.md', 'README.txt', 'README.rst', 'readme.md', 'readme.txt']:
                readme_path = service.path / pattern
                if readme_path.exists():
                    readme_files.append(readme_path)
                    logger.debug(f"📄 Found documentation file: {readme_path.name}")

            # Also check for docs directory
            docs_dir = service.path / 'docs'
            if docs_dir.exists():
                logger.debug("📁 Scanning docs/ directory...")
                doc_files = list(docs_dir.rglob('*.md'))
                readme_files.extend(doc_files)
                logger.debug(f"📄 Found {len(doc_files)} additional documentation files in docs/")

            if not readme_files:
                logger.warning("❌ No documentation files found")
                doc_score = 20.0  # Heavy penalty for no documentation
                doc_issues.append("No README or documentation files found")
                doc_recommendations.append("📚 Create a comprehensive README.md file with all required sections")
            else:
                logger.info(f"📊 Analyzing {len(readme_files)} documentation files...")

                # Analyze each documentation file with progress feedback
                total_files_score = 0
                files_analyzed = 0

                for i, doc_file in enumerate(readme_files[:3]):  # Limit to first 3 files
                    logger.debug(f"🔍 Analyzing file {i+1}/{min(3, len(readme_files))}: {doc_file.name}")
                    try:
                        # Add timeout protection for file reading
                        import asyncio
                        content = await asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(None, doc_file.read_text),
                            timeout=5.0  # 5 second timeout for file reading
                        )

                        logger.debug(f"📝 Processing {len(content)} characters in {doc_file.name}")
                        file_score = await self._analyze_documentation_file(content, doc_file.name)
                        total_files_score += file_score
                        files_analyzed += 1
                        logger.debug(f"✅ File {doc_file.name} scored: {file_score:.1f}/100")

                    except asyncio.TimeoutError:
                        logger.warning(f"⏰ Timeout reading documentation file {doc_file}")
                        continue
                    except Exception as e:
                        logger.warning(f"❌ Error analyzing documentation file {doc_file}: {e}")
                        continue

                if files_analyzed > 0:
                    avg_file_score = total_files_score / files_analyzed
                    doc_score = min(doc_score, avg_file_score)
                    logger.debug(f"📊 Average documentation score: {avg_file_score:.1f}/100")

                # Check for documentation consistency across multiple files
                if len(readme_files) > 1:
                    logger.debug("🔄 Checking documentation consistency...")
                    consistency_score = await self._analyze_documentation_consistency(readme_files)
                    doc_score = min(doc_score, consistency_score)
                    logger.debug(f"📋 Documentation consistency score: {consistency_score:.1f}/100")

                    if consistency_score < 80:
                        doc_issues.append("Inconsistent documentation across multiple files")
                        doc_recommendations.append("📋 Standardize documentation format and content across all doc files")

                # Check for links to other documents
                logger.debug("🔗 Analyzing documentation links...")
                links_score = await self._analyze_documentation_links(readme_files)
                doc_score = min(doc_score, links_score)
                logger.debug(f"🔗 Documentation links score: {links_score:.1f}/100")

                if links_score < 70:
                    doc_issues.append("Missing or broken links to related documentation")
                    doc_recommendations.append("🔗 Add proper cross-references and links to related docs")

        except Exception as e:
            logger.warning(f"❌ Documentation quality check failed: {e}")
            doc_score = 20.0  # Harsh penalty for analysis failure

        # Apply stricter penalties based on profile name
        if self.profile and hasattr(self.profile, 'name') and self.profile.name == 'strict':
            # In strict mode, penalize poor documentation more heavily
            if doc_score < 60:
                doc_score -= 25  # Additional 25 point penalty for poor docs in strict mode
            elif doc_score < 75:
                doc_score -= 15  # Additional 15 point penalty for mediocre docs in strict mode
            elif doc_score < 85:
                doc_score -= 5   # Additional 5 point penalty for decent docs in strict mode

        if doc_issues:
            self._ddd_issues.extend([f"📚 DOC: {issue}" for issue in doc_issues])
        if doc_recommendations:
            self._ddd_recommendations.extend(doc_recommendations)

        logger.info(f"✅ Documentation quality analysis complete: {doc_score:.1f}/100")
        return max(0.0, doc_score)

    async def _analyze_strict_domain_layer_completeness(self, service: ServiceInfo) -> float:
        """STRICT domain layer completeness enforcement with parallel file processing."""
        logger.info(f"🏛️  Analyzing STRICT domain layer completeness for {service.name}")
        score = 0.0

        domain_path = service.path / "domain"
        if not domain_path.exists():
            self._ddd_issues.append("🚨 CRITICAL: domain/ layer missing - required for DDD")
            self._ddd_recommendations.append("📁 CREATE: domain/ layer with entities, services, repositories")
            logger.warning(f"❌ Domain layer missing for {service.name}")
            return 0.0

        # Collect all domain files for parallel processing
        domain_files = []
        for root, dirs, files in os.walk(str(domain_path)):
            for file in files:
                if file.endswith('.py') and not file.startswith('.') and not file.startswith('__'):
                    domain_files.append(Path(root) / file)

        if not domain_files:
            self._ddd_issues.append("🚨 CRITICAL: domain/ layer is empty - no domain entities, services, or repositories")
            self._ddd_recommendations.append("📝 CREATE: domain entities, services, and repositories in domain/ layer")
            return 0.0

        # Required domain subdirectories
        required_domain_dirs = {
            'entities': 25,
            'services': 25,
            'repositories': 25,
            'exceptions': 10,
            'value_objects': 10,
            'events': 5
        }

        existing_score = 0
        missing_dirs = []

        for dir_name, points in required_domain_dirs.items():
            if (domain_path / dir_name).exists():
                existing_score += points
            else:
                missing_dirs.append(dir_name)

        score += existing_score

        # Check for actual content in required directories
        critical_dirs = ['entities', 'services', 'repositories']
        for dir_name in critical_dirs:
            dir_path = domain_path / dir_name
            if dir_path.exists():
                py_files = list(dir_path.glob("**/*.py"))
                if not py_files:
                    score -= 15
                    self._ddd_issues.append(f"📭 EMPTY DOMAIN DIR: domain/{dir_name}/ exists but contains no Python files")
                    self._ddd_recommendations.append(f"📝 IMPLEMENT: Add domain logic to domain/{dir_name}/ directory")

        # Check for domain layer violations (imports from infrastructure/presentation)
        violations = 0

        # Use parallel processing for import checking if we have enough files
        if HAS_ASYNC and len(domain_files) > 3:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=min(4, len(domain_files))) as executor:
                import_check_tasks = []
                for domain_file in domain_files[:20]:  # Check up to 20 files
                    task = loop.run_in_executor(executor, self._check_domain_import_violations, domain_file, service)
                    import_check_tasks.append(task)

                try:
                    import_results = await asyncio.wait_for(
                        asyncio.gather(*import_check_tasks, return_exceptions=True),
                        timeout=10.0
                    )

                    for result in import_results:
                        if isinstance(result, int):
                            violations += result

                except asyncio.TimeoutError:
                    logger.warning("Domain import checking timed out, falling back to sequential")
                    # Fall back to sequential processing
                    for domain_file in domain_files[:5]:
                        violations += self._check_domain_import_violations(domain_file, service)
        else:
            # Sequential processing for small file counts
            for domain_file in domain_files[:5]:
                violations += self._check_domain_import_violations(domain_file, service)

        if violations > 0:
            score -= violations * 10

        logger.info(f"✅ Completed STRICT domain layer analysis for {service.name}: score {score:.1f}/100")
        return max(0, score)

    async def _analyze_strict_application_layer_patterns(self, service: ServiceInfo) -> float:
        """STRICT application layer pattern enforcement (CQRS, handlers, etc.)."""
        logger.info(f"⚙️  Analyzing STRICT application layer patterns for {service.name}")
        score = 0.0

        app_path = service.path / "application"
        if not app_path.exists():
            self._ddd_issues.append("🚨 CRITICAL: application/ layer missing - required for DDD use case orchestration")
            self._ddd_recommendations.append("📁 CREATE: application/ layer with handlers, commands, queries")
            logger.warning(f"❌ Application layer missing for {service.name}")
            return 0.0

        # Required application patterns
        required_patterns = {
            'handlers': ['*handler*.py', '*_handler.py'],
            'commands': ['*command*.py', 'commands.py'],
            'queries': ['*query*.py', 'queries.py'],
            'dto': ['*dto*.py', 'dto/'],
            'events': ['*event*.py', 'events.py']
        }

        pattern_score = 0
        missing_patterns = []

        for pattern_name, patterns in required_patterns.items():
            found = False
            for pattern in patterns:
                if list(app_path.glob(f"**/{pattern}")):
                    found = True
                    break

            if found:
                if pattern_name in ['handlers', 'commands', 'queries']:
                    pattern_score += 20  # Core patterns worth more
                else:
                    pattern_score += 10  # Supporting patterns
            else:
                missing_patterns.append(pattern_name)

        score += pattern_score

        # Check for CQRS pattern implementation
        cqrs_indicators = ['Command', 'Query', 'CommandHandler', 'QueryHandler']
        cqrs_found = 0

        app_files = list(app_path.glob("**/*.py"))
        for app_file in app_files[:5]:  # Check first 5 files
            try:
                with open(app_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for indicator in cqrs_indicators:
                        if indicator in content:
                            cqrs_found += 1
                            break
            except Exception:
                continue

        if cqrs_found > 0:
            score += 20  # Bonus for CQRS implementation
        else:
            self._ddd_issues.append("📋 MISSING CQRS: Application layer should implement Command/Query patterns")
            self._ddd_recommendations.append("🔄 IMPLEMENT: Add CQRS patterns (Command, Query, CommandHandler, QueryHandler) to application layer")

        # Check for proper application layer imports
        for app_file in app_files[:3]:  # Check first 3 files
            try:
                with open(app_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Application can import from domain but NOT from infrastructure
                if 'from infrastructure' in content or 'import infrastructure' in content:
                    score -= 15
                    self._ddd_issues.append(f"🚨 APP LAYER VIOLATION: {app_file.relative_to(service.path)} imports from infrastructure")
                    self._ddd_recommendations.append(f"🔄 REFACTOR: Remove infrastructure imports from application layer")

            except Exception:
                continue

        logger.info(f"✅ Completed STRICT application layer analysis for {service.name}: score {score:.1f}/100")
        return max(0, score)

    async def _analyze_strict_clean_architecture_compliance(self, service: ServiceInfo) -> float:
        """STRICT clean architecture compliance with layer separation enforcement."""
        logger.info(f"🏗️  Analyzing STRICT clean architecture compliance for {service.name}")
        score = 100.0

        # Define STRICT layer boundaries
        layer_rules = {
            'domain': {
                'can_import': [],
                'cannot_import': ['application', 'infrastructure', 'presentation'],
                'purpose': 'Business logic only'
            },
            'application': {
                'can_import': ['domain'],
                'cannot_import': ['infrastructure', 'presentation'],
                'purpose': 'Use case orchestration'
            },
            'infrastructure': {
                'can_import': ['domain', 'application'],
                'cannot_import': ['presentation'],
                'purpose': 'External concerns'
            },
            'presentation': {
                'can_import': ['application', 'infrastructure'],
                'cannot_import': ['domain'],
                'purpose': 'HTTP/API layer'
            }
        }

        violations_found = 0
        total_checks = 0

        # Check each layer's import compliance
        for layer, rules in layer_rules.items():
            layer_path = service.path / layer
            if not layer_path.exists():
                continue

            layer_files = list(layer_path.glob("**/*.py"))

            for layer_file in layer_files[:3]:  # Check first 3 files per layer
                total_checks += 1

                try:
                    with open(layer_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Check forbidden imports
                    for forbidden_layer in rules['cannot_import']:
                        forbidden_patterns = [
                            f'from {forbidden_layer}',
                            f'import {forbidden_layer}',
                            f'from services.shared.{forbidden_layer}',
                            f'import services.shared.{forbidden_layer}'
                        ]

                        for pattern in forbidden_patterns:
                            if pattern in content:
                                violations_found += 1
                                score -= 10
                                self._ddd_issues.append(f"🚨 STRICT LAYER VIOLATION: {layer_file.relative_to(service.path)} illegally imports from {forbidden_layer} layer")
                                self._ddd_recommendations.append(f"🔄 FIX: Remove {forbidden_layer} imports from {layer} layer - violates clean architecture")

                except Exception:
                    continue

        # Check for dependency injection/inversion (infrastructure should depend on abstractions)
        infra_files = list((service.path / "infrastructure").glob("**/*.py")) if (service.path / "infrastructure").exists() else []

        abstraction_violations = 0
        for infra_file in infra_files[:3]:
            try:
                with open(infra_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Infrastructure should NOT directly instantiate domain objects
                # Should use dependency injection instead
                direct_instantiation = [
                    'domain.', 'Domain', 'Entity(', 'Service('
                ]

                if any(pattern in content for pattern in direct_instantiation):
                    abstraction_violations += 1
                    self._ddd_issues.append(f"🚨 ABSTRACTION VIOLATION: {infra_file.relative_to(service.path)} directly instantiates domain objects")
                    self._ddd_recommendations.append(f"🔄 REFACTOR: Use dependency injection in infrastructure layer instead of direct domain instantiation")

            except Exception:
                continue

        if abstraction_violations > 0:
            score -= abstraction_violations * 8

        # Overall architecture score
        if violations_found > self.thresholds['architecture'].get('max_architecture_violations', 5):
            score -= 20  # Major penalty for excessive violations

        logger.info(f"✅ Completed STRICT clean architecture analysis for {service.name}: score {score:.1f}/100, {violations_found} violations found")
        return max(0, score)

    async def _check_rest_compliance(self, service: ServiceInfo) -> float:
        """Check REST API compliance"""
        rest_score = 50.0  # Base score for having an API

        # Check for FastAPI/Flask patterns
        api_files = []
        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if '@app.' in content or '@router.' in content:
                                api_files.append(file_path)
                    except Exception:
                        continue

        if api_files:
            rest_score += 30  # API endpoints detected

            # Check for HTTP methods
            http_methods = ['get', 'post', 'put', 'delete', 'patch']
            method_usage = 0

            for api_file in api_files[:5]:  # Check first 5 files
                try:
                    with open(api_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for method in http_methods:
                            if f'@{method}' in content.lower():
                                method_usage += 1
                except Exception:
                    continue

            if method_usage > 0:
                rest_score += min(20, method_usage * 4)

        return min(100, rest_score)

    async def _check_layer_separation(self, service: ServiceInfo) -> float:
        """Check layer separation quality"""
        separation_score = 100.0

        # Check for proper imports between layers
        layers = {
            'domain': ['domain'],
            'application': ['domain', 'application'],
            'infrastructure': ['domain', 'application', 'infrastructure'],
            'presentation': ['application', 'infrastructure', 'presentation']
        }

        violations = 0
        total_checks = 0

        for layer, allowed_imports in layers.items():
            layer_path = service.path / layer
            if layer_path.exists():
                layer_files = list(layer_path.glob("**/*.py"))

                for layer_file in layer_files[:3]:  # Check first 3 files per layer
                    try:
                        with open(layer_file, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Check imports
                        for other_layer in layers.keys():
                            if other_layer != layer and other_layer not in allowed_imports:
                                if f'from {other_layer}' in content or f'import {other_layer}' in content:
                                    violations += 1

                        total_checks += 1

                    except Exception:
                        continue

        if total_checks > 0:
            violation_rate = violations / total_checks
            separation_score -= min(50, violation_rate * 100)

        return max(0, separation_score)

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
            'standard_violations': [],
            'endpoint_details': [],  # Detailed endpoint information
            'compliant_endpoints': [],  # List of compliant endpoints
            'non_compliant_endpoints': []  # List of non-compliant endpoints
        }

        # Find FastAPI route files with comprehensive detection
        route_files = []
        all_python_files = []
        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    all_python_files.append(file_path)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Look for FastAPI router patterns - expanded detection
                            has_fastapi_patterns = (
                                '@router.' in content or '@app.' in content or
                                'APIRouter' in content or 'FastAPI' in content or
                                'fastapi' in content.lower() or
                                'from fastapi' in content or
                                'import fastapi' in content
                            )

                            # Prioritize routes directory files (DDD+REST structure)
                            is_in_routes_dir = 'presentation/routes' in str(file_path.relative_to(service.path)) or 'routes' in str(file_path.relative_to(service.path)).split('/')

                            if has_fastapi_patterns:
                                # Routes directory files get priority (add to front of list)
                                if is_in_routes_dir:
                                    route_files.insert(0, file_path)
                                else:
                                    route_files.append(file_path)
                    except Exception:
                        continue

        # Validate endpoint detection completeness
        endpoint_detection_validation = self._validate_endpoint_detection_completeness(service, route_files, all_python_files)

        # Analyze each route file for endpoints
        for route_file in route_files:
            try:
                with open(route_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract endpoint blocks using improved parsing
                endpoint_blocks = self._extract_endpoint_blocks(content)

                for block in endpoint_blocks:
                    endpoint_info = self._extract_endpoint_info(block, route_file)
                    if endpoint_info:
                        endpoint_analysis['total_endpoints'] += 1
                        endpoint_analysis['endpoint_details'].append(endpoint_info)

                        # Analyze compliance for this endpoint
                        compliance_results = self._analyze_single_endpoint(block, route_file)

                        # Check REST compliance
                        rest_compliant = compliance_results.get('rest_compliance', 0) >= 80
                        openapi_compliant = compliance_results.get('openapi_compliance', 0) >= 80
                        standard_compliant = compliance_results.get('project_standards', 0) >= 80

                        if rest_compliant:
                            endpoint_analysis['rest_compliant_endpoints'] += 1
                        if openapi_compliant:
                            endpoint_analysis['openapi_compliant_endpoints'] += 1
                        if standard_compliant:
                            endpoint_analysis['project_standard_compliant_endpoints'] += 1

                        # Overall compliance check
                        overall_compliant = rest_compliant and openapi_compliant and standard_compliant
                        if overall_compliant:
                            endpoint_analysis['compliant_endpoints'].append(endpoint_info)
                        else:
                            endpoint_analysis['non_compliant_endpoints'].append({
                                **endpoint_info,
                                'issues': compliance_results.get('issues', [])
                            })

                        # Collect violations
                        endpoint_analysis['rest_violations'].extend(compliance_results.get('rest_violations', []))
                        endpoint_analysis['openapi_violations'].extend(compliance_results.get('openapi_violations', []))
                        endpoint_analysis['standard_violations'].extend(compliance_results.get('standard_violations', []))

            except Exception as e:
                logger.error(f"Error analyzing route file {route_file}: {e}")
                continue

        # Calculate compliance scores
        total_endpoints = endpoint_analysis['total_endpoints']
        if total_endpoints > 0:
            endpoint_analysis['rest_compliance_score'] = round((endpoint_analysis['rest_compliant_endpoints'] / total_endpoints) * 100, 2)
            endpoint_analysis['openapi_compliance_score'] = round((endpoint_analysis['openapi_compliant_endpoints'] / total_endpoints) * 100, 2)
            endpoint_analysis['project_standards_compliance_score'] = round((endpoint_analysis['project_standard_compliant_endpoints'] / total_endpoints) * 100, 2)
        else:
            endpoint_analysis['rest_compliance_score'] = 0
            endpoint_analysis['openapi_compliance_score'] = 0
            endpoint_analysis['project_standards_compliance_score'] = 0

        endpoint_analysis['endpoint_detection_validation'] = endpoint_detection_validation

        return endpoint_analysis

    def _extract_endpoint_blocks(self, content: str) -> List[str]:
        """Extract endpoint blocks from FastAPI route files."""
        blocks = []
        lines = content.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Look for FastAPI decorators
            if line.startswith('@app.') or line.startswith('@router.'):
                # Collect the decorator and function
                block_lines = [line]

                # Look for additional decorators (responses, tags, etc.)
                j = i + 1
                while j < len(lines) and (lines[j].strip().startswith('@') or lines[j].strip() == ''):
                    if lines[j].strip().startswith('@'):
                        block_lines.append(lines[j].strip())
                    j += 1

                # Find the function definition
                while j < len(lines):
                    if lines[j].strip().startswith('def ') or lines[j].strip().startswith('async def '):
                        # Collect function lines until next function or class
                        func_start = j
                        j += 1
                        brace_count = 0
                        in_function = True

                        while j < len(lines) and in_function:
                            line_content = lines[j]
                            brace_count += line_content.count('{') - line_content.count('}')

                            # Check for next function/class/decorator at same indentation level
                            stripped = line_content.strip()
                            if (stripped.startswith('def ') or stripped.startswith('async def ') or
                                stripped.startswith('class ') or stripped.startswith('@')) and brace_count <= 0:
                                in_function = False
                                j -= 1  # Don't include the next function
                            else:
                                j += 1

                        # Add function to block
                        block_lines.extend(lines[func_start:j])
                        blocks.append('\n'.join(block_lines))
                        break
                    j += 1

                i = j
            else:
                i += 1

        return blocks

    def _extract_endpoint_info(self, endpoint_block: str, file_path: Path) -> Optional[Dict[str, Any]]:
        """Extract endpoint information from a FastAPI endpoint block."""
        try:
            lines = endpoint_block.split('\n')

            # Find the main decorator
            main_decorator = None
            for line in lines:
                if line.strip().startswith('@app.') or line.strip().startswith('@router.'):
                    main_decorator = line.strip()
                    break

            if not main_decorator:
                return None

            # Extract HTTP method and path
            method_match = re.search(r'@(?:app|router)\.(\w+)\s*\(\s*["\']([^"\']+)["\']', main_decorator)
            if method_match:
                method = method_match.group(1).upper()
                path = method_match.group(2)
            else:
                return None

            # Find function name
            func_match = re.search(r'def\s+(\w+)|async def\s+(\w+)', endpoint_block)
            func_name = func_match.group(1) or func_match.group(2) if func_match else 'unknown'

            return {
                'method': method,
                'path': path,
                'function': func_name,
                'file': str(file_path.relative_to(file_path.parent.parent.parent)),  # Relative to service root
                'line_number': self._get_endpoint_line_number(endpoint_block, file_path)
            }

        except Exception:
            return None

    def _get_endpoint_line_number(self, endpoint_block: str, file_path: Path) -> int:
        """Get the line number where the endpoint is defined."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find the position of the endpoint block in the file
            lines = content.split('\n')
            block_lines = endpoint_block.split('\n')

            # Look for the main decorator
            for i, line in enumerate(lines):
                if block_lines and block_lines[0] in line:
                    return i + 1

        except Exception:
            pass

        return 0

    def _validate_endpoint_detection_completeness(self, service: ServiceInfo, route_files: List[Path], all_python_files: List[Path]) -> Dict[str, Any]:
        """Validate that endpoint detection is comprehensive."""
        validation = {
            'total_fastapi_files_found': len(route_files),
            'detection_gaps': [],
            'recommendations': []
        }

        # Check for missed FastAPI files
        missed_files = []
        for py_file in all_python_files:
            if py_file not in route_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if any(pattern in content for pattern in ['@app.', '@router.', 'FastAPI(', 'APIRouter(']):
                            missed_files.append(str(py_file.relative_to(service.path)))
                except Exception:
                    continue

        if missed_files:
            validation['detection_gaps'].extend(missed_files)
            validation['recommendations'].append(f"Consider analyzing additional FastAPI files: {', '.join(missed_files[:3])}")

        return validation

    def _analyze_single_endpoint(self, endpoint_block: str, file_path: Path) -> Dict[str, Any]:
        """Analyze a single endpoint for compliance."""
        results = {
            'rest_compliance': 0,
            'openapi_compliance': 0,
            'project_standards': 0,
            'issues': [],
            'rest_violations': [],
            'openapi_violations': [],
            'standard_violations': []
        }

        # Check REST compliance
        rest_score = self._check_rest_compliance_for_endpoint(endpoint_block)
        results['rest_compliance'] = rest_score

        # Check OpenAPI compliance
        openapi_score = self._check_openapi_compliance_for_endpoint(endpoint_block)
        results['openapi_compliance'] = openapi_score

        # Check project standards
        standards_score = self._check_project_standards_for_endpoint(endpoint_block)
        results['project_standards'] = standards_score

        # Collect issues
        results['issues'] = []
        if rest_score < 80:
            results['issues'].append("REST compliance issues")
            results['rest_violations'].append("Low REST compliance score")
        if openapi_score < 80:
            results['issues'].append("OpenAPI documentation issues")
            results['openapi_violations'].append("Low OpenAPI compliance score")
        if standards_score < 80:
            results['issues'].append("Project standard violations")
            results['standard_violations'].append("Low project standards compliance")

        return results

    def _check_rest_compliance_for_endpoint(self, endpoint_block: str) -> float:
        """Check REST compliance for a single endpoint."""
        score = 100.0

        # Check for proper HTTP methods
        if not any(method in endpoint_block for method in ['get(', 'post(', 'put(', 'delete(', 'patch(']):
            score -= 30

        # Check for status code specification
        if 'status_code=' not in endpoint_block:
            score -= 20

        # Check for proper response modeling
        if 'response_model=' not in endpoint_block:
            score -= 15

        return max(0, score)

    def _check_openapi_compliance_for_endpoint(self, endpoint_block: str) -> float:
        """Check OpenAPI compliance for a single endpoint."""
        score = 100.0

        # Required OpenAPI annotations
        required_annotations = ['summary=', 'description=', 'response_model=']
        for annotation in required_annotations:
            if annotation not in endpoint_block:
                score -= 25

        # Recommended annotations
        recommended_annotations = ['responses=', 'tags=']
        for annotation in recommended_annotations:
            if annotation not in endpoint_block:
                score -= 10

        return max(0, score)

    def _check_project_standards_for_endpoint(self, endpoint_block: str) -> float:
        """Check project standards compliance for a single endpoint."""
        score = 100.0

        # Check for async functions
        if 'async def' not in endpoint_block and 'def ' in endpoint_block:
            score -= 15

        # Check for proper error handling
        if 'try:' not in endpoint_block or 'except' not in endpoint_block:
            score -= 20

        # Check for logging
        if 'logger.' not in endpoint_block and 'logging.' not in endpoint_block:
            score -= 15

        return max(0, score)

    def _identify_issues(self, scores: Dict[str, float]) -> List[str]:
        """Identify architecture issues based on scores"""
        issues = []
        if scores.get('ddd_compliance', 0) < self.thresholds['dimensions']['architecture']['min_score']:
            issues.append("Low DDD compliance - consider implementing domain patterns")
        if scores.get('rest_compliance', 0) < self.thresholds['dimensions']['architecture']['rest_compliance_required']:
            issues.append("REST API design issues - review HTTP methods and status codes")
        if scores.get('empty_directories', 100) < 95:
            issues.append("Empty directories detected - clean up unnecessary directories")
        if scores.get('requirements_file', 100) < 80:
            issues.append("Requirements/dependency files need review or updates")
        if scores.get('docker_infrastructure', 100) < 80:
            issues.append("Docker/infrastructure configuration issues detected")
        return issues

    def _generate_recommendations(self, scores: Dict[str, float]) -> List[str]:
        """Generate STRICT DDD architecture recommendations"""
        recommendations = []

        if scores.get('ddd_compliance', 0) < 85:  # STRICT threshold
            recommendations.append("🚨 STRICT DDD REQUIRED: Implement complete DDD architecture with domain/, application/, infrastructure/, presentation/ layers")
            recommendations.append("📁 MIGRATE IMMEDIATELY: Move all business logic from modules/ to appropriate DDD layers")
            recommendations.append("🔄 ZERO TOLERANCE: Remove business logic from presentation layer (controllers, routes)")
            recommendations.append("🏗️ LAYER SEPARATION: Enforce strict import boundaries - domain→application→infrastructure→presentation")

        if scores.get('ddd_compliance', 0) < 70:
            recommendations.append("📝 DOMAIN LAYER: Implement entities, services, repositories, value_objects, exceptions")
            recommendations.append("⚡ APPLICATION LAYER: Add CQRS patterns (Command, Query, CommandHandler, QueryHandler)")
            recommendations.append("🔌 INFRASTRUCTURE LAYER: Use dependency injection, avoid direct domain instantiation")
            recommendations.append("🌐 PRESENTATION LAYER: Keep only HTTP concerns, delegate business logic to application layer")

        if scores.get('layer_separation', 0) < 80:  # STRICT threshold
            recommendations.append("🚫 IMPORT VIOLATIONS: Fix all cross-layer import violations immediately")
            recommendations.append("🔀 DEPENDENCY INVERSION: Infrastructure should depend on domain abstractions, not concretions")

        # Add recommendations for new checks
        if scores.get('empty_directories', 100) < 95:
            recommendations.append("🗂️ CLEANUP: Remove empty directories or add necessary files")

        if scores.get('requirements_file', 100) < 80:
            recommendations.append("📦 DEPENDENCIES: Add/update requirements.txt and consider pyproject.toml")
            recommendations.append("🔒 LOCK FILES: Use poetry.lock or requirements-lock.txt for reproducible builds")

        if scores.get('docker_infrastructure', 100) < 80:
            recommendations.append("🐳 DOCKER: Ensure Dockerfile exists with FROM, EXPOSE, and HEALTHCHECK")
            recommendations.append("🔌 PORTS: Check for port conflicts using port validation script")
            recommendations.append("📋 MAKEFILE: Ensure service is integrated in CI/CD Makefile targets")

        # Documentation quality recommendations
        if scores.get('documentation_quality', 100) < 80:
            recommendations.append("📚 DOCUMENTATION: Create comprehensive README.md with required sections")
            recommendations.append("📖 SECTIONS: Add title, description, requirements, config, infrastructure, ecosystem, features")
            recommendations.append("🔗 LINKS: Add cross-references to related documentation and services")
            recommendations.append("📝 FORMATTING: Use proper markdown formatting with headers, lists, and code blocks")
            recommendations.append("🤖 LLM: Structure content for AI consumption with clear sections and semantic markup")

        return recommendations

    # ===== DRY PRINCIPLES ANALYSIS METHODS =====

    async def _analyze_code_duplication(self, service: ServiceInfo) -> int:
        """Analyze code duplication patterns across the service"""
        duplication_count = 0

        try:
            # Get all Python files
            python_files = []
            for root, dirs, files in os.walk(str(service.path)):
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        python_files.append(Path(root) / file)

            # Simple duplication detection - look for repeated code blocks
            code_blocks = {}
            for file_path in python_files[:20]:  # Limit to first 20 files for performance
                try:
                    content = file_path.read_text()
                    lines = content.split('\n')

                    # Look for repeated 4-line blocks
                    for i in range(len(lines) - 4):
                        block = '\n'.join(lines[i:i+4]).strip()
                        if len(block) > 20:  # Ignore very short blocks
                            if block in code_blocks:
                                code_blocks[block] += 1
                            else:
                                code_blocks[block] = 1
                except:
                    continue

            # Count blocks that appear more than once
            for block, count in code_blocks.items():
                if count > 1:
                    duplication_count += 1

        except Exception:
            pass

        return duplication_count

    async def _analyze_config_duplication(self, service: ServiceInfo) -> int:
        """Analyze configuration duplication patterns"""
        config_duplication = 0

        try:
            # Look for repeated configuration patterns
            config_patterns = [
                r'host\s*=\s*["\'][^"\']+["\']',
                r'port\s*=\s*\d+',
                r'database\s*=\s*["\'][^"\']+["\']',
                r'user\s*=\s*["\'][^"\']+["\']',
                r'password\s*=\s*["\'][^"\']+["\']'
            ]

            python_files = []
            for root, dirs, files in os.walk(str(service.path)):
                for file in files:
                    if file.endswith('.py'):
                        python_files.append(Path(root) / file)

            pattern_counts = {}
            for file_path in python_files[:15]:  # Limit for performance
                try:
                    content = file_path.read_text()
                    for pattern in config_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            if match in pattern_counts:
                                pattern_counts[match] += 1
                            else:
                                pattern_counts[match] = 1
                except:
                    continue

            # Count patterns that appear in multiple files
            for pattern, count in pattern_counts.items():
                if count > 1:
                    config_duplication += 1

        except Exception:
            pass

        return config_duplication

    async def _analyze_utility_reuse(self, service: ServiceInfo) -> float:
        """Analyze utility function reuse across the service"""
        score = 100.0

        try:
            # Look for utility functions that are defined but not used elsewhere
            python_files = []
            for root, dirs, files in os.walk(str(service.path)):
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        python_files.append(Path(root) / file)

            utility_functions = {}
            function_usage = {}

            for file_path in python_files[:20]:
                try:
                    content = file_path.read_text()

                    # Find function definitions
                    func_defs = re.findall(r'def\s+(\w+)\s*\(', content)
                    for func in func_defs:
                        if func.startswith('_'):  # Private functions
                            utility_functions[func] = str(file_path)

                    # Find function calls
                    for func in func_defs:
                        usage_count = content.count(f'{func}(')
                        if usage_count > 1:  # Function is called somewhere
                            function_usage[func] = usage_count

                except:
                    continue

            # Check for unused utility functions
            unused_count = 0
            for func in utility_functions:
                if func not in function_usage:
                    unused_count += 1

            if unused_count > 0:
                score -= min(unused_count * 5, 30)  # Max 30 point penalty

        except Exception:
            score = 80.0

        return score

    async def _analyze_error_pattern_duplication(self, service: ServiceInfo) -> int:
        """Analyze repeated error handling patterns"""
        error_patterns = 0

        try:
            python_files = []
            for root, dirs, files in os.walk(str(service.path)):
                for file in files:
                    if file.endswith('.py'):
                        python_files.append(Path(root) / file)

            error_handlers = {}
            for file_path in python_files[:15]:
                try:
                    content = file_path.read_text()

                    # Look for try-except blocks
                    try_blocks = re.findall(r'try\s*:.*?(except\s+\w+\s+as\s+\w+\s*:.*?)(?=try|\Z)', content, re.DOTALL)
                    for block in try_blocks:
                        # Simplify the block for comparison
                        simplified = re.sub(r'\s+', ' ', block.strip())
                        if len(simplified) > 20:  # Ignore very short blocks
                            if simplified in error_handlers:
                                error_handlers[simplified] += 1
                            else:
                                error_handlers[simplified] = 1

                except:
                    continue

            # Count repeated error patterns
            for pattern, count in error_handlers.items():
                if count > 1:
                    error_patterns += 1

        except Exception:
            pass

        return error_patterns

    # ===== KISS PRINCIPLES ANALYSIS METHODS =====

    async def _analyze_method_complexity(self, service: ServiceInfo) -> int:
        """Analyze method complexity using cyclomatic complexity"""
        complex_methods = 0

        try:
            python_files = []
            for root, dirs, files in os.walk(str(service.path)):
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        python_files.append(Path(root) / file)

            if self._full_audit:
                files_to_process = python_files  # Process all files
            else:
                files_to_process = python_files[:25]  # Limit for performance

            for file_path in files_to_process:
                try:
                    content = file_path.read_text()

                    # Simple complexity analysis based on control flow
                    functions = re.findall(r'def\s+\w+\s*\([^)]*\)\s*:(.*?)(?=\n\s*def|\n\s*@|\nclass|\Z)', content, re.DOTALL)

                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if line.strip().startswith('def '):
                            # Extract function name
                            func_match = re.match(r'def\s+(\w+)\s*\(', line.strip())
                            if func_match:
                                func_name = func_match.group(1)

                                # Find function end
                                func_start = i
                                func_end = i
                                indent_level = len(line) - len(line.lstrip())

                                # Simple function body extraction
                                func_lines = []
                                j = i + 1
                                while j < len(lines):
                                    line_j = lines[j]
                                    if line_j.strip() and not line_j.startswith(' ' * (indent_level + 1)) and not line_j.startswith('\t' * (indent_level + 1)):
                                        break
                                    func_lines.append(line_j)
                                    j += 1
                                func_end = j

                                func_content = '\n'.join(func_lines)
                                complexity = 1  # Base complexity

                                # Count control flow statements
                                complexity += func_content.count('if ')
                                complexity += func_content.count('elif ')
                                complexity += func_content.count('for ')
                                complexity += func_content.count('while ')
                                complexity += func_content.count('try:')
                                complexity += func_content.count('except ')
                                complexity += func_content.count('and ')
                                complexity += func_content.count('or ')

                                # Track detailed issues for high complexity
                                profile_threshold = 15  # Default
                                if self.profile and hasattr(self.profile, 'code_quality'):
                                    profile_threshold = self.profile.code_quality.get('complexity_threshold', 15)

                                if complexity >= profile_threshold:
                                    self._add_complexity_issue(
                                        file_path=file_path,
                                        function_name=func_name,
                                        complexity=complexity,
                                        line_number=func_start + 1,
                                        threshold=profile_threshold
                                    )
                                    complex_methods += 1

                except:
                    continue

        except Exception:
            pass

        return complex_methods

    async def _analyze_class_responsibility(self, service: ServiceInfo) -> int:
        """Analyze classes for Single Responsibility Principle violations"""
        responsibility_violations = 0

        try:
            python_files = []
            for root, dirs, files in os.walk(str(service.path)):
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        python_files.append(Path(root) / file)

            for file_path in python_files[:20]:
                try:
                    content = file_path.read_text()

                    # Find classes
                    classes = re.findall(r'class\s+(\w+)', content)
                    for class_match in classes:
                        # Extract class content
                        class_pattern = rf'class\s+{re.escape(class_match)}\b.*?:(.*?)(?=\nclass|\Z)'
                        class_content_match = re.search(class_pattern, content, re.DOTALL)

                        if class_content_match:
                            class_content = class_content_match.group(1)

                            # Count different types of methods
                            method_types = set()

                            # Business logic methods
                            if re.search(r'def\s+(create|update|delete|process|handle|validate|calculate)', class_content):
                                method_types.add('business')

                            # Data access methods
                            if re.search(r'def\s+(save|find|get|query|insert|update_record)', class_content):
                                method_types.add('data')

                            # HTTP/communication methods
                            if re.search(r'def\s+(send|receive|post|get|put|delete|request)', class_content):
                                method_types.add('communication')

                            # Utility methods
                            if re.search(r'def\s+(format|parse|convert|encode|decode)', class_content):
                                method_types.add('utility')

                            # If class has more than 2 different types of methods, it's doing too much
                            if len(method_types) > 2:
                                responsibility_violations += 1

                except:
                    continue

        except Exception:
            pass

        return responsibility_violations

    async def _analyze_abstraction_layers(self, service: ServiceInfo) -> int:
        """Analyze unnecessary abstraction layers"""
        abstraction_issues = 0

        try:
            # Check for over-abstraction patterns
            python_files = []
            for root, dirs, files in os.walk(str(service.path)):
                for file in files:
                    if file.endswith('.py'):
                        python_files.append(Path(root) / file)

            for file_path in python_files[:15]:
                try:
                    content = file_path.read_text()

                    # Look for interface/abstract base classes that add no value
                    abc_imports = content.count('from abc import')
                    abstract_classes = len(re.findall(r'class\s+\w+\(ABC\)', content))
                    concrete_implementations = len(re.findall(r'class\s+\w+\([^)]*\):\s*(?!.*pass\s*$)', content))

                    # If we have many abstract classes but few implementations, might be over-abstracted
                    if abstract_classes > concrete_implementations and abstract_classes > 2:
                        abstraction_issues += 1

                    # Look for wrapper classes that just delegate
                    wrapper_patterns = re.findall(r'class\s+\w+.*:\s*def\s+\w+.*:\s*return\s+self\.\w+\.\w+', content, re.DOTALL)
                    abstraction_issues += len(wrapper_patterns)

                except:
                    continue

        except Exception:
            pass

        return abstraction_issues

    async def _analyze_over_engineering(self, service: ServiceInfo) -> float:
        """Analyze for over-engineering patterns"""
        score = 100.0

        try:
            python_files = []
            for root, dirs, files in os.walk(str(service.path)):
                for file in files:
                    if file.endswith('.py'):
                        python_files.append(Path(root) / file)

            over_engineering_indicators = 0

            for file_path in python_files[:20]:
                try:
                    content = file_path.read_text()

                    # Count over-engineering indicators
                    over_engineering_indicators += content.count('Factory') * 2  # Factories can be overkill
                    over_engineering_indicators += content.count('Strategy') * 2  # Strategy pattern overuse
                    over_engineering_indicators += content.count('Observer') * 3  # Observer pattern is complex
                    over_engineering_indicators += content.count('Singleton') * 3  # Singleton is often overkill

                    # Check for overly complex inheritance hierarchies
                    inheritance_depth = content.count('class') - content.count('class.*:.*pass')
                    if inheritance_depth > 5:
                        over_engineering_indicators += 2

                    # Check for excessive use of metaclasses or descriptors
                    if 'metaclass' in content or '__getattribute__' in content:
                        over_engineering_indicators += 3

                except:
                    continue

            # Penalize based on over-engineering indicators
            if over_engineering_indicators > 0:
                score -= min(over_engineering_indicators * 3, 40)

        except Exception:
            score = 80.0

        return score

    # ===== DDD PATTERNS ANALYSIS METHODS =====

    async def _analyze_entity_validation(self, service: ServiceInfo) -> float:
        """Analyze entity validation implementation"""
        score = 100.0

        try:
            domain_path = service.path / "domain"
            if not domain_path.exists():
                return 50.0

            entity_files = []
            for root, dirs, files in os.walk(str(domain_path)):
                for file in files:
                    if file.endswith('.py') and 'entity' in file.lower():
                        entity_files.append(Path(root) / file)

            validation_methods = 0
            total_entities = len(entity_files)

            for file_path in entity_files:
                try:
                    content = file_path.read_text()

                    # Look for validation methods
                    if re.search(r'def\s+(validate|is_valid|check_|ensure_)', content):
                        validation_methods += 1

                    # Look for property validation
                    if re.search(r'@property\s+.*\n.*def.*validate', content, re.DOTALL):
                        validation_methods += 1

                except:
                    continue

            if total_entities > 0:
                validation_coverage = (validation_methods / total_entities) * 100
                score = min(100, validation_coverage + 50)  # Base 50 points + coverage bonus

        except Exception:
            score = 60.0

        return score

    async def _analyze_repository_patterns(self, service: ServiceInfo) -> float:
        """Analyze repository pattern implementation"""
        score = 100.0

        try:
            domain_path = service.path / "domain"
            infrastructure_path = service.path / "infrastructure"

            repository_interfaces = 0
            repository_implementations = 0

            # Check domain layer for repository interfaces
            if domain_path.exists():
                for root, dirs, files in os.walk(str(domain_path)):
                    for file in files:
                        if file.endswith('.py') and 'repository' in file.lower():
                            try:
                                content = Path(root) / file.read_text()
                                if re.search(r'class.*Repository.*:', content) and 'ABC' in content:
                                    repository_interfaces += 1
                            except:
                                continue

            # Check infrastructure layer for implementations
            if infrastructure_path.exists():
                for root, dirs, files in os.walk(str(infrastructure_path)):
                    for file in files:
                        if file.endswith('.py') and 'repository' in file.lower():
                            try:
                                content = Path(root) / file.read_text()
                                if re.search(r'class.*Repository.*:', content) and 'Repository' in content:
                                    repository_implementations += 1
                            except:
                                continue

            # Score based on interface/implementation balance
            if repository_interfaces == 0:
                score = 30.0  # No repository pattern
            elif repository_interfaces > repository_implementations:
                score = 70.0  # Interfaces without implementations
            elif repository_implementations >= repository_interfaces:
                score = 100.0  # Good implementation

        except Exception:
            score = 50.0

        return score

    async def _analyze_value_objects(self, service: ServiceInfo) -> float:
        """Analyze value object immutability"""
        score = 100.0

        try:
            domain_path = service.path / "domain"
            if not domain_path.exists():
                return 50.0

            value_objects = []
            for root, dirs, files in os.walk(str(domain_path)):
                for file in files:
                    if file.endswith('.py') and ('value' in file.lower() or 'vo' in file.lower()):
                        value_objects.append(Path(root) / file)

            immutable_objects = 0

            for file_path in value_objects:
                try:
                    content = file_path.read_text()

                    # Check for immutability indicators
                    has_frozen = '@dataclass(frozen=True)' in content or 'frozen=True' in content
                    has_slots = '__slots__' in content
                    no_setters = len(re.findall(r'def\s+set\w+', content)) == 0

                    if has_frozen or (has_slots and no_setters):
                        immutable_objects += 1

                except:
                    continue

            if len(value_objects) > 0:
                immutability_ratio = (immutable_objects / len(value_objects)) * 100
                score = immutability_ratio
            else:
                score = 50.0  # No value objects found

        except Exception:
            score = 60.0

        return score

    async def _analyze_aggregate_roots(self, service: ServiceInfo) -> float:
        """Analyze aggregate root identification and implementation"""
        score = 100.0

        try:
            domain_path = service.path / "domain"
            if not domain_path.exists():
                return 50.0

            entities = []
            for root, dirs, files in os.walk(str(domain_path)):
                for file in files:
                    if file.endswith('.py') and ('entity' in file.lower() or 'aggregate' in file.lower()):
                        entities.append(Path(root) / file)

            aggregates_with_business_logic = 0

            for file_path in entities:
                try:
                    content = file_path.read_text()

                    # Look for aggregate root indicators
                    has_business_methods = len(re.findall(r'def\s+(create|update|delete|process|validate)', content)) > 2
                    has_encapsulation = '__init__' in content and len(re.findall(r'def\s+_\w+', content)) > 0
                    has_invariants = 'raise' in content and ('ValueError' in content or 'DomainError' in content)

                    if has_business_methods and (has_encapsulation or has_invariants):
                        aggregates_with_business_logic += 1

                except:
                    continue

            if len(entities) > 0:
                aggregate_ratio = (aggregates_with_business_logic / len(entities)) * 100
                score = min(100, aggregate_ratio + 40)  # Base 40 points + ratio bonus

        except Exception:
            score = 50.0

        return score

    async def _analyze_domain_events(self, service: ServiceInfo) -> float:
        """Analyze domain event implementation"""
        score = 100.0

        try:
            domain_path = service.path / "domain"
            if not domain_path.exists():
                return 50.0

            event_files = []
            for root, dirs, files in os.walk(str(domain_path)):
                for file in files:
                    if file.endswith('.py') and ('event' in file.lower()):
                        event_files.append(Path(root) / file)

            event_classes = len(event_files)

            # Check for event publishing in domain logic
            domain_files = []
            for root, dirs, files in os.walk(str(domain_path)):
                for file in files:
                    if file.endswith('.py'):
                        domain_files.append(Path(root) / file)

            event_usage = 0
            for file_path in domain_files[:10]:
                try:
                    content = file_path.read_text()
                    if 'Event' in content and ('publish' in content or 'emit' in content):
                        event_usage += 1
                except:
                    continue

            # Score based on event implementation and usage
            if event_classes == 0:
                score = 40.0  # No domain events
            elif event_classes > 0 and event_usage == 0:
                score = 60.0  # Events defined but not used
            elif event_usage > 0:
                score = min(100, 70 + (event_classes * 5))  # Good event usage

        except Exception:
            score = 50.0

        return score

    # ===== REST BEST PRACTICES ANALYSIS METHODS =====

    async def _analyze_http_methods(self, service: ServiceInfo) -> float:
        """Analyze HTTP method usage patterns"""
        score = 100.0

        try:
            presentation_path = service.path / "presentation"
            api_path = service.path / "api"

            api_files = []
            if presentation_path.exists():
                for root, dirs, files in os.walk(str(presentation_path)):
                    for file in files:
                        if file.endswith('.py') and ('route' in file.lower() or 'api' in file.lower()):
                            api_files.append(Path(root) / file)

            if api_path.exists():
                for root, dirs, files in os.walk(str(api_path)):
                    for file in files:
                        if file.endswith('.py'):
                            api_files.append(Path(root) / file)

            method_counts = {'GET': 0, 'POST': 0, 'PUT': 0, 'DELETE': 0, 'PATCH': 0}
            total_endpoints = 0

            for file_path in api_files[:15]:
                try:
                    content = file_path.read_text()

                    # Count HTTP method decorators
                    for method in method_counts.keys():
                        method_counts[method] += len(re.findall(rf'@(?:app|router)\.{method.lower()}\s*\(', content))
                        total_endpoints += method_counts[method]

                except:
                    continue

            # Score based on RESTful method distribution
            if total_endpoints == 0:
                score = 50.0
            else:
                # Prefer GET operations, penalize over-reliance on POST for everything
                get_ratio = method_counts['GET'] / total_endpoints
                post_ratio = method_counts['POST'] / total_endpoints

                if get_ratio > 0.6:  # Too many GETs, might be missing proper REST design
                    score -= 20
                if post_ratio > 0.7:  # Too many POSTs, not following REST properly
                    score -= 30

                # Bonus for having all main HTTP methods
                methods_used = sum(1 for count in method_counts.values() if count > 0)
                if methods_used >= 4:  # GET, POST, PUT, DELETE
                    score += 10

        except Exception:
            score = 60.0

        return max(0, score)

    async def _analyze_status_codes(self, service: ServiceInfo) -> float:
        """Analyze HTTP status code usage patterns"""
        score = 100.0

        try:
            api_files = []
            for path_name in ['presentation', 'api', 'routes']:
                api_path = service.path / path_name
                if api_path.exists():
                    for root, dirs, files in os.walk(str(api_path)):
                        for file in files:
                            if file.endswith('.py'):
                                api_files.append(Path(root) / file)

            status_codes_found = set()
            inappropriate_codes = 0

            for file_path in api_files[:15]:
                try:
                    content = file_path.read_text()

                    # Look for HTTP status codes
                    status_matches = re.findall(r'\b\d{3}\b', content)
                    for match in status_matches:
                        code = int(match)
                        status_codes_found.add(code)

                        # Check for inappropriate status codes
                        if code in [200, 201, 204, 400, 401, 403, 404, 409, 422, 500]:
                            pass  # Appropriate codes
                        elif code >= 100 and code < 600:
                            inappropriate_codes += 1

                except:
                    continue

            # Penalize inappropriate status codes
            score -= min(inappropriate_codes * 5, 40)

            # Bonus for using proper status codes
            proper_codes = len([c for c in status_codes_found if c in [200, 201, 204, 400, 401, 403, 404, 409, 422, 500]])
            score += min(proper_codes * 2, 20)

        except Exception:
            score = 60.0

        return max(0, score)

    async def _analyze_resource_naming(self, service: ServiceInfo) -> float:
        """Analyze REST resource naming conventions"""
        score = 100.0

        try:
            api_files = []
            for path_name in ['presentation', 'api', 'routes']:
                api_path = service.path / path_name
                if api_path.exists():
                    for root, dirs, files in os.walk(str(api_path)):
                        for file in files:
                            if file.endswith('.py'):
                                api_files.append(Path(root) / file)

            restful_paths = 0
            non_restful_paths = 0

            for file_path in api_files[:15]:
                try:
                    content = file_path.read_text()

                    # Extract route paths
                    path_matches = re.findall(r'@(?:app|router)\.\w+\s*\(\s*["\']([^"\']+)["\']', content)
                    for path in path_matches:
                        # Check RESTful naming conventions
                        if re.match(r'^/?(?:[a-z-]+(?:/[a-z-]+)*/?(?:\?[^/]*)?)?/?$', path):
                            restful_paths += 1
                        else:
                            non_restful_paths += 1

                except:
                    continue

            total_paths = restful_paths + non_restful_paths
            if total_paths > 0:
                restful_ratio = restful_paths / total_paths
                score = restful_ratio * 100

                # Bonus for consistent kebab-case naming
                if restful_ratio > 0.8:
                    score += 10

        except Exception:
            score = 60.0

        return max(0, score)

    async def _analyze_hateoas(self, service: ServiceInfo) -> float:
        """Analyze HATEOAS (Hypermedia as the Engine of Application State) implementation"""
        score = 100.0

        try:
            api_files = []
            for path_name in ['presentation', 'api', 'routes']:
                api_path = service.path / path_name
                if api_path.exists():
                    for root, dirs, files in os.walk(str(api_path)):
                        for file in files:
                            if file.endswith('.py'):
                                api_files.append(Path(root) / file)

            hateoas_indicators = 0
            total_responses = 0

            for file_path in api_files[:10]:
                try:
                    content = file_path.read_text()

                    # Look for HATEOAS indicators
                    hateoas_indicators += content.count('_links') * 2
                    hateoas_indicators += content.count('self')  # self links
                    hateoas_indicators += content.count('href')
                    hateoas_indicators += content.count('rel')  # relationship links

                    # Count response objects
                    total_responses += len(re.findall(r'return\s+.*Response|JSONResponse|dict', content))

                except:
                    continue

            # Score based on HATEOAS implementation
            if total_responses == 0:
                score = 50.0
            else:
                hateoas_ratio = hateoas_indicators / total_responses
                if hateoas_ratio > 0.5:  # Good HATEOAS implementation
                    score = 100.0
                elif hateoas_ratio > 0.2:  # Basic HATEOAS
                    score = 80.0
                else:  # Poor HATEOAS
                    score = 60.0

        except Exception:
            score = 50.0

        return score

    async def _analyze_content_negotiation(self, service: ServiceInfo) -> float:
        """Analyze content negotiation implementation"""
        score = 100.0

        try:
            api_files = []
            for path_name in ['presentation', 'api', 'routes']:
                api_path = service.path / path_name
                if api_path.exists():
                    for root, dirs, files in os.walk(str(api_path)):
                        for file in files:
                            if file.endswith('.py'):
                                api_files.append(Path(root) / file)

            content_negotiation_features = 0
            total_endpoints = 0

            for file_path in api_files[:15]:
                try:
                    content = file_path.read_text()

                    # Look for content negotiation features
                    content_negotiation_features += content.count('Accept') * 2
                    content_negotiation_features += content.count('Content-Type') * 2
                    content_negotiation_features += content.count('application/json')
                    content_negotiation_features += content.count('application/xml')
                    content_negotiation_features += content.count('text/html')

                    # Count endpoints
                    total_endpoints += len(re.findall(r'@(?:app|router)\.\w+\s*\(', content))

                except:
                    continue

            # Score based on content negotiation implementation
            if total_endpoints == 0:
                score = 50.0
            else:
                negotiation_ratio = content_negotiation_features / total_endpoints
                if negotiation_ratio > 1.0:  # Good content negotiation
                    score = 100.0
                elif negotiation_ratio > 0.5:  # Basic content negotiation
                    score = 80.0
                else:  # Poor content negotiation
                    score = 60.0

        except Exception:
            score = 50.0

        return score

    # ===== DOCUMENTATION QUALITY ANALYSIS METHODS =====

    async def _analyze_documentation_file(self, content: str, filename: str) -> float:
        """Analyze a single documentation file for quality metrics"""
        score = 100.0
        content_lower = content.lower()

        # Check for required sections (organization)
        required_sections = {
            'title': ['# ', 'title', filename.replace('.md', '').replace('_', ' ')],
            'description': ['description', 'overview', 'about', 'summary'],
            'requirements': ['requirements', 'dependencies', 'prerequisites', 'install'],
            'config': ['config', 'configuration', 'setup', 'environment'],
            'infrastructure': ['infrastructure', 'docker', 'deployment', 'makefile', 'ci/cd'],
            'ecosystem': ['ecosystem', 'integration', 'api', 'endpoints', 'interaction'],
            'features': ['features', 'functionality', 'capabilities', 'key features']
        }

        sections_found = 0
        total_sections = len(required_sections)

        for section_name, keywords in required_sections.items():
            section_present = any(keyword in content_lower for keyword in keywords)
            if section_present:
                sections_found += 1
            else:
                score -= 5  # Small penalty per missing section

        # Bonus for having an index/table of contents
        if any(keyword in content_lower for keyword in ['table of contents', 'index', 'contents', '##']):
            score += 5

        # Analyze section detail and readability
        lines = content.split('\n')
        total_lines = len(lines)

        if total_lines < 20:
            score -= 20  # Too short
        elif total_lines < 50:
            score -= 10  # Could be more detailed

        # Check for code blocks (good for technical docs)
        code_blocks = len(re.findall(r'```', content))
        if code_blocks == 0:
            score -= 10  # Technical docs should have code examples

        # Check markdown formatting usage
        formatting_score = await self._analyze_markdown_formatting(content)
        score = min(score, formatting_score)

        # LLM embeddings consideration - check for structured content
        llm_score = await self._analyze_llm_readability(content)
        score = min(score, llm_score)

        return max(0, score)

    async def _analyze_markdown_formatting(self, content: str) -> float:
        """Analyze markdown formatting quality"""
        score = 100.0

        # Check for various markdown elements
        formatting_elements = {
            'headers': len(re.findall(r'^#{1,6}\s+', content, re.MULTILINE)),
            'bold': len(re.findall(r'\*\*.*?\*\*', content)),
            'italic': len(re.findall(r'\*.*?\*', content)),
            'lists': len(re.findall(r'^[\s]*[-\*\+]\s+', content, re.MULTILINE)),
            'links': len(re.findall(r'\[.*?\]\(.*?\)', content)),
            'code_inline': len(re.findall(r'`.*?`', content)),
            'code_blocks': len(re.findall(r'```', content))
        }

        # Penalize poor formatting usage
        total_elements = sum(formatting_elements.values())
        if total_elements < 10:
            score -= 30  # Poor formatting usage
        elif total_elements < 20:
            score -= 15  # Could use more formatting

        # Check for proper header hierarchy
        headers = re.findall(r'^#{1,6}\s+', content, re.MULTILINE)
        if len(headers) > 0:
            # Check if headers follow proper hierarchy (no skipping levels)
            header_levels = [len(h.strip()) for h in headers]
            for i in range(1, len(header_levels)):
                if header_levels[i] > header_levels[i-1] + 1:
                    score -= 5  # Skipping header levels

        return max(0, score)

    async def _analyze_llm_readability(self, content: str) -> float:
        """Analyze content structure for LLM embeddings and AI consumption"""
        score = 100.0

        # Check for semantic structure
        semantic_indicators = [
            len(re.findall(r'^#{1,3}\s+', content, re.MULTILINE)),  # Clear section headers
            len(re.findall(r'\n\n', content)),  # Paragraph breaks
            len(re.findall(r'\[.*?\]\(.*?\)', content)),  # Descriptive links
            len(re.findall(r'`.*?`', content)),  # Code snippets
            len(re.findall(r'\*\*.*?\*\*', content))  # Emphasized text
        ]

        # Penalize poor semantic structure
        if sum(semantic_indicators) < 15:
            score -= 25

        # Check for consistent formatting patterns
        lines = content.split('\n')
        inconsistent_formatting = 0

        for line in lines[:50]:  # Check first 50 lines
            # Look for mixed formatting styles
            if ('*' in line and '_' in line) or ('**' in line and '__' in line):
                inconsistent_formatting += 1

        if inconsistent_formatting > 3:
            score -= 15

        return max(0, score)

    async def _analyze_documentation_consistency(self, doc_files: List[Path]) -> float:
        """Analyze consistency across multiple documentation files"""
        score = 100.0

        if len(doc_files) < 2:
            return score

        try:
            # Compare formatting styles across files
            formatting_patterns = []
            header_styles = []
            link_styles = []

            for doc_file in doc_files[:3]:
                try:
                    content = doc_file.read_text()

                    # Collect formatting patterns
                    formatting_patterns.append({
                        'code_blocks': len(re.findall(r'```', content)),
                        'headers': len(re.findall(r'^#{1,6}\s+', content, re.MULTILINE)),
                        'links': len(re.findall(r'\[.*?\]\(.*?\)', content)),
                        'lists': len(re.findall(r'^[\s]*[-\*\+]\s+', content, re.MULTILINE))
                    })

                    # Check header styles
                    headers = re.findall(r'^#{1,6}\s+', content, re.MULTILINE)
                    header_styles.append(len(headers) > 0 and headers[0].startswith('# ') if headers else False)

                    # Check link styles
                    links = re.findall(r'\[.*?\]\(.*?\)', content)
                    link_styles.append(len(links) > 0)

                except:
                    continue

            # Analyze consistency
            if len(formatting_patterns) > 1:
                # Check if formatting patterns are similar
                avg_code_blocks = sum(p['code_blocks'] for p in formatting_patterns) / len(formatting_patterns)
                consistency_deviation = sum(abs(p['code_blocks'] - avg_code_blocks) for p in formatting_patterns) / len(formatting_patterns)

                if consistency_deviation > 3:
                    score -= 20  # Inconsistent code block usage

                # Check header style consistency
                header_consistency = sum(header_styles) / len(header_styles)
                if header_consistency < 0.7:
                    score -= 15  # Inconsistent header styles

        except Exception:
            score = 70.0

        return max(0, score)

    async def _analyze_documentation_links(self, doc_files: List[Path]) -> float:
        """Analyze links and cross-references in documentation"""
        score = 100.0

        try:
            total_links = 0
            broken_links = 0
            cross_references = 0

            for doc_file in doc_files[:3]:
                try:
                    content = doc_file.read_text()
                    base_path = doc_file.parent

                    # Count total links
                    links = re.findall(r'\[.*?\]\((.*?)\)', content)
                    total_links += len(links)

                    # Check for cross-references (links to other docs)
                    for link in links:
                        if link.startswith(('../', './', 'docs/', 'README', '.md')):
                            cross_references += 1

                            # Check if linked file exists (basic check)
                            if '../' in link or './' in link:
                                # Try to resolve relative path
                                try:
                                    resolved_path = (base_path / link).resolve()
                                    if not resolved_path.exists() and not link.startswith('http'):
                                        broken_links += 1
                                except:
                                    broken_links += 1

                except:
                    continue

            # Scoring based on links
            if total_links == 0:
                score -= 40  # No links at all
            elif total_links < 5:
                score -= 20  # Very few links

            if cross_references == 0:
                score -= 25  # No cross-references to other docs

            if broken_links > 0:
                score -= min(broken_links * 10, 30)  # Broken links penalty

        except Exception:
            score = 60.0

        return max(0, score)

    def _add_detailed_issue(self, issue_type: str, file_path: str, line_number: Optional[int] = None,
                           line_block: Optional[str] = None, description: str = "",
                           severity: str = "warning", dimension: str = "architecture"):
        """Add a detailed issue with location information."""
        issue = {
            "issue_type": issue_type,
            "file_path": str(file_path),
            "description": description,
            "severity": severity,
            "dimension": dimension
        }

        if line_number is not None:
            issue["line_number"] = line_number
        if line_block is not None:
            issue["line_block"] = line_block

        self._detailed_issues.append(issue)

    def _add_complexity_issue(self, file_path: str, function_name: str, complexity: int,
                             line_number: int, threshold: int = 10):
        """Add a detailed complexity issue."""
        self._add_detailed_issue(
            issue_type="high_cyclomatic_complexity",
            file_path=file_path,
            line_number=line_number,
            description=f"Function '{function_name}' has cyclomatic complexity {complexity} (threshold: {threshold})",
            severity="warning" if complexity < 15 else "critical",
            dimension="code_quality"
        )

    def _add_duplication_issue(self, file_path: str, duplicate_lines: List[str],
                              line_start: int, line_end: int, similarity_score: float = 0.0):
        """Add a detailed code duplication issue."""
        self._add_detailed_issue(
            issue_type="code_duplication",
            file_path=file_path,
            line_number=line_start,
            line_block=f"{line_start}-{line_end}",
            description=f"Code duplication detected: {len(duplicate_lines)} lines, similarity: {similarity_score:.1f}%",
            severity="warning",
            dimension="maintainability"
        )

    def _add_import_violation_issue(self, file_path: str, violation_type: str,
                                   import_statement: str, line_number: int):
        """Add a detailed import layer violation issue."""
        self._add_detailed_issue(
            issue_type="layer_separation_violation",
            file_path=file_path,
            line_number=line_number,
            description=f"Layer separation violation ({violation_type}): {import_statement}",
            severity="critical",
            dimension="architecture"
        )

    def _add_oversized_file_issue(self, file_path: str, line_count: int, threshold: int = 800):
        """Add a detailed oversized file issue."""
        self._add_detailed_issue(
            issue_type="oversized_file",
            file_path=file_path,
            description=f"File exceeds line limit: {line_count} lines (threshold: {threshold})",
            severity="warning",
            dimension="maintainability"
        )

    def _add_empty_directory_issue(self, directory_path: str):
        """Add a detailed empty directory issue."""
        self._add_detailed_issue(
            issue_type="empty_directory",
            file_path=directory_path,
            description="Empty directory found",
            severity="info",
            dimension="maintainability"
        )
