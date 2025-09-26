"""
Architecture Analyzer
Handles all architecture-related quality assessments including DDD compliance,
REST API design, layer separation, and structural analysis.
"""

import os
import ast
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Handle imports for both module and script execution
try:
    from ..config import AuditProfile, get_thresholds_for_profile
    from domain.entities.service_info import ServiceInfo
except ImportError:
    import sys
    from pathlib import Path
    current_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(current_dir))

    from config import AuditProfile
    from config.thresholds import get_thresholds_for_profile

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


class ArchitectureAnalyzer:
    """Analyzer for architectural quality and compliance"""

    def __init__(self, profile: AuditProfile):
        self.profile = profile
        self.thresholds = get_thresholds_for_profile(profile)
        self._ddd_issues: List[str] = []
        self._ddd_recommendations: List[str] = []
        self._file_metrics: Dict[str, Any] = {}
        self._directory_analysis: Dict[str, Any] = {}

    async def analyze(self, service: ServiceInfo) -> ArchitectureAnalysisResult:
        """Perform complete architecture analysis"""
        # Initialize analysis storage
        self._ddd_issues = []
        self._ddd_recommendations = []
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
            'layer_separation': await self._check_layer_separation(service)
        }

        # Calculate weighted architecture score
        architecture_score = (
            scores['ddd_compliance'] * self.profile.architecture.get('ddd_compliance_weight', 0.4) +
            scores['rest_compliance'] * self.profile.architecture.get('rest_compliance_weight', 0.35) +
            scores['layer_separation'] * self.profile.architecture.get('layer_separation_weight', 0.25)
        )

        return ArchitectureAnalysisResult(
            score=round(architecture_score, 2),
            ddd_compliance=scores['ddd_compliance'],
            rest_compliance=scores['rest_compliance'],
            layer_separation=scores['layer_separation'],
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
            recommendations=self._generate_recommendations(scores)
        )

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
        return issues

    def _generate_recommendations(self, scores: Dict[str, float]) -> List[str]:
        """Generate architecture recommendations"""
        recommendations = []
        if scores.get('ddd_compliance', 0) < 70:
            recommendations.append("Adopt DDD patterns: entities, value objects, domain services")
        if scores.get('layer_separation', 0) < 70:
            recommendations.append("Improve layer separation: presentation, application, domain, infrastructure")
        return recommendations
