"""
Architecture Analyzer
Handles all architecture-related quality assessments including DDD compliance,
REST API design, layer separation, and structural analysis.
"""

import os
import ast
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from ..config import AuditProfile, get_thresholds_for_profile
from ..models import ServiceInfo


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

    # Additional architecture analysis methods would go here...
    # (Truncated for brevity - would include all the DDD analysis methods)

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
