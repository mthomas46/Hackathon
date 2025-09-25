#!/usr/bin/env python3
"""
DDD Audit Framework for LLM Documentation Ecosystem

This framework implements Domain-Driven Design principles to provide
automated assessment of services across four critical dimensions:

- Architecture: DDD compliance, REST design, layer separation
- Code Quality: Complexity, testing, duplication, documentation
- Performance: Runtime, database, resource optimization
- Maintainability: Organization, error handling, scalability, DevOps

Clean Architecture:
- Domain: Core business logic and entities
- Application: Use cases and business orchestration
- Infrastructure: External services and implementations
- Presentation: CLI and user interfaces

Usage:
    python audit_framework.py audit --service doc_store [--profile strict]
    python audit_framework.py audit --service doc_store --profile ci_fast --output json
    python audit_framework.py compare --services doc_store,prompt_store
    python audit_framework.py list-profiles
"""

import os
import sys
import json
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

# Setup path for DDD imports
import sys
from pathlib import Path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Import from DDD structure
from domain.entities.service_info import ServiceInfo
from domain.entities.analysis_result import AnalysisResult
from domain.value_objects.audit_profile import AuditProfile
from domain.value_objects.thresholds import ThresholdConfig
from domain.services.audit_service import AuditService
from application.use_cases.audit_service_use_case import AuditServiceUseCase
from application.commands.audit_service_command import AuditServiceCommand
from infrastructure.analyzers import (
    ArchitectureAnalyzer, CodeQualityAnalyzer,
    PerformanceAnalyzer, MaintainabilityAnalyzer
)
from infrastructure.file_system import FileSystemService
from config.profiles import profile_manager
from config.thresholds import get_thresholds_for_profile

# Enhanced reporting libraries
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.text import Text
    from rich.columns import Columns
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

logger = logging.getLogger(__name__)


@dataclass
class AuditResults:
    """Comprehensive audit results for a service"""
    service_name: str
    service_path: Path
    overall_score: float
    grade: str
    critical_issues: List[Dict[str, Any]]
    dimensions: Dict[str, Any]
    architecture: Dict[str, Any]
    code_quality: Dict[str, Any]
    performance: Dict[str, Any]
    maintainability: Dict[str, Any]
    recommendations: List[str]
    estimated_effort_days: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ServiceInfo:
    """Information about a discovered service"""
    name: str
    path: Path
    type: str = "python"  # python, docker, kubernetes
    status: str = "unknown"  # active, inactive, deprecated
    metadata: Dict[str, Any] = field(default_factory=dict)


class AuditFramework:
    """
    Modular audit framework that orchestrates quality analysis across multiple dimensions.

    This framework provides:
    - Configurable audit profiles for different scenarios (strict, standard, relaxed, ci_fast)
    - Modular analyzers for each quality dimension
    - Rich reporting with actionable recommendations
    - CI/CD integration with quality gates
    """

    def __init__(self, profile: Optional[AuditProfile] = None):
        """
        Initialize the audit framework with a specific profile.

        Args:
            profile: Audit profile to use. If None, uses 'standard' profile.
        """
        self.profile = profile or profile_manager.get_profile('standard')
        self.thresholds = get_thresholds_for_profile(self.profile)
        self.console = Console() if HAS_RICH else None

        # Initialize analyzers with the profile
        self.architecture_analyzer = ArchitectureAnalyzer(self.profile)
        self.code_quality_analyzer = CodeQualityAnalyzer(self.profile)
        self.performance_analyzer = PerformanceAnalyzer(self.profile)
        self.maintainability_analyzer = MaintainabilityAnalyzer(self.profile)

    def discover_services(self) -> List[ServiceInfo]:
        """
        Discover all services in the project.

        Returns:
            List of ServiceInfo objects for discovered services
        """
        services = []
        services_root = Path(__file__).parent.parent.parent / "services"

        if not services_root.exists():
            logger.warning(f"Services directory not found: {services_root}")
            return services

        for service_dir in services_root.iterdir():
            if service_dir.is_dir() and not service_dir.name.startswith('.'):
                # Check if it's a Python service (has main.py or __init__.py)
                has_python_files = any(service_dir.glob("**/*.py"))
                has_main = (service_dir / "main.py").exists() or (service_dir / "app.py").exists()

                if has_python_files:
                    service_info = self._analyze_service_structure(service_dir)
                    if service_info:
                        services.append(service_info)

        return services

    def _analyze_service_structure(self, service_path: Path) -> Optional[ServiceInfo]:
        """Analyze the structure of a potential service"""
        try:
            service_name = service_path.name

            # Check for Python service indicators
            python_files = list(service_path.glob("**/*.py"))
            if not python_files:
                return None

            # Determine service type and status
            has_main = any(service_path.glob("main.py")) or any(service_path.glob("app.py"))
            has_tests = any(service_path.glob("**/test*.py")) or any(service_path.glob("tests/**/*.py"))
            has_config = any(service_path.glob("**/config*.py")) or any(service_path.glob("**/settings*.py"))
            has_docker = (service_path / "Dockerfile").exists()
            has_requirements = (service_path / "requirements.txt").exists()

            service_type = "python"
            status = "active" if has_main else "inactive"

            return ServiceInfo(
                name=service_name,
                path=service_path,
                type=service_type,
                status=status,
                metadata={
                    'python_files': len(python_files),
                    'has_main': has_main,
                    'has_tests': has_tests,
                    'has_config': has_config,
                    'has_docker': has_docker,
                    'has_requirements': has_requirements,
                    'total_files': sum(1 for _ in service_path.rglob("*") if _.is_file())
                }
            )

        except Exception as e:
            logger.error(f"Error analyzing service structure for {service_path}: {e}")
            return None

    async def audit_service(self, service_name: str, progress_callback=None) -> AuditResults:
        """
        Perform comprehensive audit of a service.

        Args:
            service_name: Name of the service to audit
            progress_callback: Optional callback for progress updates

        Returns:
            AuditResults object with comprehensive analysis
        """
        start_time = time.time()

        # Discover service
        services = self.discover_services()
        service_info = next((s for s in services if s.name == service_name), None)

        if not service_info:
            raise ValueError(f"Service '{service_name}' not found. Available services: {[s.name for s in services]}")

        if self.console and progress_callback:
            progress_callback(f"Starting audit of {service_name}...")

        try:
            # Run all analyzers sequentially for now (to avoid concurrency issues)
            results = {}

            # Architecture analysis
            if self.console and progress_callback:
                progress_callback("Analyzing architecture...")
            try:
                results['architecture'] = await self.architecture_analyzer.analyze(service_info)
            except Exception as e:
                logger.error(f"Error in architecture analysis: {e}")
                results['architecture'] = self._create_fallback_results('architecture', e)

            # Code quality analysis
            if self.console and progress_callback:
                progress_callback("Analyzing code quality...")
            try:
                results['code_quality'] = await self.code_quality_analyzer.analyze(service_info)
            except Exception as e:
                logger.error(f"Error in code quality analysis: {e}")
                results['code_quality'] = self._create_fallback_results('code_quality', e)

            # Performance analysis
            if self.console and progress_callback:
                progress_callback("Analyzing performance...")
            try:
                results['performance'] = await self.performance_analyzer.analyze(service_info)
            except Exception as e:
                logger.error(f"Error in performance analysis: {e}")
                results['performance'] = self._create_fallback_results('performance', e)

            # Maintainability analysis
            if self.console and progress_callback:
                progress_callback("Analyzing maintainability...")
            try:
                results['maintainability'] = await self.maintainability_analyzer.analyze(service_info)
            except Exception as e:
                logger.error(f"Error in maintainability analysis: {e}")
                results['maintainability'] = self._create_fallback_results('maintainability', e)

            # Calculate overall score
            overall_score = self._calculate_overall_score(results)
            grade = self._calculate_grade(overall_score)

            # Identify critical issues
            critical_issues = self._identify_critical_issues(results)

            # Generate recommendations
            recommendations = self._generate_recommendations(results)

            # Estimate effort for recommendations
            estimated_effort_days = self._estimate_effort(recommendations)

            audit_time = time.time() - start_time

            return AuditResults(
                service_name=service_name,
                service_path=service_info.path,
                overall_score=round(overall_score, 2),
                grade=grade,
                critical_issues=critical_issues,
                dimensions={
                    'architecture': results['architecture'].score,
                    'code_quality': results['code_quality'].score,
                    'performance': results['performance'].score,
                    'maintainability': results['maintainability'].score
                },
                architecture=results['architecture'].__dict__,
                code_quality=results['code_quality'].__dict__,
                performance=results['performance'].__dict__,
                maintainability=results['maintainability'].__dict__,
                recommendations=recommendations,
                estimated_effort_days=estimated_effort_days,
                metadata={
                    'audit_time_seconds': round(audit_time, 2),
                    'profile_used': self.profile.name,
                    'service_info': service_info.metadata,
                    'thresholds_applied': {
                        'min_passing_score': self.thresholds['min_passing_score'],
                        'critical_issues_threshold': self.thresholds['critical_issues']['max_critical_issues']
                    }
                }
            )

        except Exception as e:
            logger.error(f"Audit failed for {service_name}: {e}")
            raise

    def _create_fallback_results(self, dimension: str, error: Exception):
        """Create fallback results when analysis fails"""
        base_result = {
            'score': 0,
            'issues': [f"Analysis failed: {str(error)}"],
            'recommendations': [f"Fix analysis error and re-run audit"],
            'error': str(error)
        }

        if dimension == 'architecture':
            from .analyzers.architecture import ArchitectureAnalysisResult
            return ArchitectureAnalysisResult(**base_result, **{k: [] for k in [
                'ddd_issues', 'ddd_recommendations', 'file_metrics', 'test_quality',
                'linting_quality', 'endpoint_analysis', 'complexity_analysis',
                'dependency_coupling', 'dead_code_analysis', 'test_quality_metrics',
                'domain_boundaries', 'api_documentation', 'code_documentation',
                'configuration_management', 'logging_practices', 'directory_analysis'
            ]})
        elif dimension == 'code_quality':
            from .analyzers.code_quality import CodeQualityAnalysisResult
            return CodeQualityAnalysisResult(**base_result, **{k: {} for k in [
                'cyclomatic_complexity', 'test_quality_metrics', 'linting_quality', 'duplication_analysis'
            ]}, test_coverage=0)
        elif dimension == 'performance':
            from .analyzers.performance import PerformanceAnalysisResult
            return PerformanceAnalysisResult(**base_result, **{k: {} for k in [
                'system_metrics', 'database_performance', 'resource_usage', 'performance_indicators'
            ]})
        elif dimension == 'maintainability':
            from .analyzers.maintainability import MaintainabilityAnalysisResult
            return MaintainabilityAnalysisResult(**base_result, **{k: {} for k in [
                'linting_quality', 'test_quality', 'test_quality_metrics', 'domain_boundaries',
                'api_documentation', 'code_documentation', 'configuration_management', 'logging_practices'
            ]})

    def _calculate_overall_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall audit score from dimension results"""
        weights = self.profile.dimension_weights

        overall_score = (
            results['architecture'].score * (weights['architecture'] / 100) +
            results['code_quality'].score * (weights['code_quality'] / 100) +
            results['performance'].score * (weights['performance'] / 100) +
            results['maintainability'].score * (weights['maintainability'] / 100)
        )

        return min(100, max(0, overall_score))

    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from numerical score"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"

    def _identify_critical_issues(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify critical issues that require immediate attention"""
        critical_issues = []

        # Check dimension scores against critical thresholds
        for dimension, result in results.items():
            threshold = self.thresholds['dimensions'][dimension]['min_score']
            if result.score < self.thresholds['critical_score']:
                critical_issues.append({
                    'type': 'dimension_score',
                    'dimension': dimension,
                    'severity': 'critical',
                    'message': f"{dimension.replace('_', ' ').title()} score ({result.score:.1f}) below critical threshold ({self.thresholds['critical_score']})",
                    'impact': 'high'
                })

        # Check for specific critical patterns
        if hasattr(results['architecture'], 'ddd_issues') and len(results['architecture'].ddd_issues) > 2:
            critical_issues.append({
                'type': 'architecture_violations',
                'severity': 'critical',
                'message': f"Multiple DDD violations detected ({len(results['architecture'].ddd_issues)})",
                'impact': 'high'
            })

        if hasattr(results['code_quality'], 'cyclomatic_complexity'):
            high_complexity = results['code_quality'].cyclomatic_complexity.get('high_complexity_functions', [])
            if len(high_complexity) > 0:
                critical_issues.append({
                    'type': 'complexity_violations',
                    'severity': 'high',
                    'message': f"High complexity functions detected ({len(high_complexity)} functions > 20 complexity)",
                    'impact': 'medium'
                })

        return critical_issues

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate prioritized recommendations from all dimensions"""
        recommendations = []

        # Collect recommendations from all analyzers
        for result in results.values():
            if hasattr(result, 'recommendations'):
                recommendations.extend(result.recommendations)

        # Remove duplicates and prioritize
        unique_recommendations = list(set(recommendations))

        # Add profile-specific recommendations
        if self.profile.intensity.name == 'RELAXED' and results['code_quality'].score < 60:
            unique_recommendations.insert(0, "Consider using 'standard' profile for more comprehensive analysis")

        if self.profile.intensity.name == 'STRICT' and len(unique_recommendations) > 10:
            unique_recommendations.insert(0, "Many issues detected - consider phased remediation approach")

        return unique_recommendations[:15]  # Limit to top 15 recommendations

    def _estimate_effort(self, recommendations: List[str]) -> float:
        """Estimate total effort for all recommendations."""
        total_effort = 0.0

        # Effort estimation based on recommendation content
        effort_mapping = {
            'refactor': 2.0,      # Refactoring complex functions
            'increase': 1.5,      # Increasing coverage/documentation
            'implement': 3.0,     # Implementing missing patterns
            'fix': 1.0,           # Fixing specific issues
            'add': 1.5,           # Adding missing components
            'optimize': 2.5,      # Performance optimizations
            'improve': 2.0,       # General improvements
            'reduce': 1.5,        # Reducing complexity/duplication
            'use': 1.0,           # Using better patterns
            'replace': 2.0,       # Replacing implementations
            'consider': 0.5,      # Considering changes (low effort)
        }

        for rec in recommendations:
            rec_lower = rec.lower()
            effort_days = 0.5  # Base effort

            for keyword, effort in effort_mapping.items():
                if keyword in rec_lower:
                    effort_days = max(effort_days, effort)
                    break

            # Adjust based on complexity indicators
            if any(word in rec_lower for word in ['multiple', 'many', 'complex', 'significant']):
                effort_days *= 1.5

            total_effort += effort_days

        return round(total_effort, 1)

    def generate_markdown_report(self, results: AuditResults) -> str:
        """Generate markdown audit report."""
        report = f"""# Service Audit Report: {results.service_name}

**Audit Date:** {results.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Overall Score:** {results.overall_score}/100 ({results.grade})
**Estimated Effort:** {results.estimated_effort_days} days

## 📊 Score Breakdown

| Dimension | Score | Weight | Contribution |
|-----------|-------|--------|--------------|
| Architecture | {results.dimensions['architecture']:.1f} | 30% | {(results.dimensions['architecture'] * 0.30):.1f} |
| Code Quality | {results.dimensions['code_quality']:.1f} | 25% | {(results.dimensions['code_quality'] * 0.25):.1f} |
| Performance | {results.dimensions['performance']:.1f} | 20% | {(results.dimensions['performance'] * 0.20):.1f} |
| Maintainability | {results.dimensions['maintainability']:.1f} | 25% | {(results.dimensions['maintainability'] * 0.25):.1f} |

## 🚨 Critical Issues

{f"**{len(results.critical_issues)} critical issues found:**" if results.critical_issues else "**No critical issues found** ✅"}

"""

        if results.critical_issues:
            for i, issue in enumerate(results.critical_issues, 1):
                report += f"{i}. **{issue['severity'].title()}**: {issue['message']}\n"

        report += "\n## 🎯 Top Recommendations\n\n"

        for i, rec in enumerate(results.recommendations[:10], 1):
            report += f"{i}. {rec}\n"

        report += "\n## 📈 Detailed Analysis\n\n"

        # Architecture details
        report += "### 🏗️ Architecture Analysis\n"
        report += f"- **DDD Compliance:** {results.architecture.get('ddd_compliance', 0):.1f}/100\n"
        report += f"- **REST Compliance:** {results.architecture.get('rest_compliance', 0):.1f}/100\n"
        report += f"- **Layer Separation:** {results.architecture.get('layer_separation', 0):.1f}/100\n\n"

        # Code Quality details
        report += "### 💻 Code Quality Analysis\n"
        report += f"- **Complexity:** {results.code_quality.get('complexity_score', 0):.1f}/100\n"
        report += f"- **Testing:** {results.code_quality.get('testing_score', 0):.1f}/100\n"
        report += f"- **Linting:** {results.code_quality.get('linting_score', 0):.1f}/100\n"
        report += f"- **Test Coverage:** {results.code_quality.get('test_coverage', 0):.1f}%\n\n"

        # Performance details
        report += "### ⚡ Performance Analysis\n"
        report += f"- **System Metrics:** {results.performance.get('system_metrics_score', 0):.1f}/100\n"
        report += f"- **Database:** {results.performance.get('database_score', 0):.1f}/100\n"
        report += f"- **Resource Usage:** {results.performance.get('resource_usage_score', 0):.1f}/100\n\n"

        # Maintainability details
        report += "### 🔧 Maintainability Analysis\n"
        report += f"- **Documentation:** {results.maintainability.get('documentation_score', 0):.1f}/100\n"
        report += f"- **Organization:** {results.maintainability.get('organization_score', 0):.1f}/100\n"
        report += f"- **Error Handling:** {results.maintainability.get('error_handling_score', 0):.1f}/100\n"
        report += f"- **DevOps Readiness:** {results.maintainability.get('devops_readiness_score', 0):.1f}/100\n\n"

        report += "## 📋 Metadata\n\n"
        report += f"- **Profile Used:** {results.metadata.get('profile_used', 'unknown')}\n"
        report += f"- **Audit Time:** {results.metadata.get('audit_time_seconds', 0):.1f} seconds\n"
        report += f"- **Python Files:** {results.metadata.get('service_info', {}).get('python_files', 0)}\n"
        report += f"- **Total Files:** {results.metadata.get('service_info', {}).get('total_files', 0)}\n\n"

        report += "---\n\n*Report generated by LLM Documentation Ecosystem Audit Framework*"

        return report

    def compare_services(self, service_names: List[str]) -> Dict[str, Any]:
        """Compare multiple services side by side"""
        results = {}
        for service_name in service_names:
            try:
                result = asyncio.run(self.audit_service(service_name))
                results[service_name] = result
            except Exception as e:
                logger.error(f"Failed to audit {service_name}: {e}")
                results[service_name] = None

        return {
            'comparison': results,
            'summary': self._generate_comparison_summary(results)
        }

    def _generate_comparison_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for service comparison"""
        valid_results = {k: v for k, v in results.items() if v is not None}

        if not valid_results:
            return {'error': 'No valid results to compare'}

        scores = [r.overall_score for r in valid_results.values()]

        return {
            'total_services': len(results),
            'successful_audits': len(valid_results),
            'average_score': round(sum(scores) / len(scores), 2) if scores else 0,
            'highest_score': max(scores) if scores else 0,
            'lowest_score': min(scores) if scores else 0,
            'services_above_threshold': sum(1 for s in scores if s >= self.thresholds['min_passing_score']),
            'critical_issues_total': sum(len(r.critical_issues) for r in valid_results.values())
        }


class AuditOrchestrator:
    """Orchestrates the audit process using DDD principles.

    This class coordinates between domain services, application use cases,
    and infrastructure components to execute audits.
    """

    def __init__(self):
        """Initialize the audit orchestrator with all dependencies."""
        self.thresholds = get_thresholds_for_profile("standard")

        # Initialize domain service
        self.audit_service = AuditService(self.thresholds)

        # Initialize infrastructure services
        self.file_system = FileSystemService()

        # Initialize analyzers (infrastructure implementations)
        self.analyzers = {
            'architecture': ArchitectureAnalyzer(),
            'code_quality': CodeQualityAnalyzer(),
            'performance': PerformanceAnalyzer(),
            'maintainability': MaintainabilityAnalyzer(),
        }

        # Initialize application use case
        self.audit_use_case = AuditServiceUseCase(self.audit_service, self.analyzers)

    async def audit_service_by_name(
        self,
        service_name: str,
        profile_name: str = "standard"
    ) -> AnalysisResult:
        print(f"DEBUG: audit_service_by_name called with service_name={service_name}, profile_name={profile_name}")
        """Audit a service by discovering it and running analysis.

        Args:
            service_name: Name of the service to audit
            profile_name: Name of the audit profile to use

        Returns:
            Complete analysis result
        """
        # Discover service
        service_path = self._discover_service_path(service_name)
        if not service_path:
            raise ValueError(f"Service '{service_name}' not found")

        # Create service info
        service_info = ServiceInfo(
            name=service_name,
            path=service_path
        )

        # Get audit profile
        try:
            profile = profile_manager.get_profile(profile_name)
            print(f"DEBUG: Retrieved profile type: {type(profile)}, name: {getattr(profile, 'name', 'NO_NAME')}")
        except ValueError as e:
            raise ValueError(f"Profile '{profile_name}' not found") from e

        # Execute audit use case
        return await self.audit_use_case.execute(service_info, profile)

    def _discover_service_path(self, service_name: str) -> Optional[Path]:
        """Discover the path for a service by name."""
        # Look in common service directories
        search_paths = [
            Path.cwd() / "services" / service_name,
            Path.cwd() / service_name,
            Path.cwd().parent / "services" / service_name,
        ]

        for path in search_paths:
            if path.exists() and path.is_dir():
                # Verify it looks like a service
                if (path / "main.py").exists() or (path / "app.py").exists():
                    return path

        return None


# CLI Interface
def main():
    """Command-line interface for the DDD audit framework"""
    import argparse

    parser = argparse.ArgumentParser(description="DDD Audit Framework for LLM Documentation Ecosystem")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Audit command
    audit_parser = subparsers.add_parser('audit', help='Audit a single service')
    audit_parser.add_argument('--service', required=True, help='Service name to audit')
    audit_parser.add_argument('--profile', default='standard',
                            choices=['relaxed', 'standard', 'strict', 'ci_fast', 'ci_comprehensive'],
                            help='Audit profile to use')
    audit_parser.add_argument('--output', choices=['rich', 'json', 'markdown', 'full'], default='rich',
                            help='Output format (full includes all detailed analysis)')
    audit_parser.add_argument('--verbose', action='store_true', help='Verbose output')

    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare multiple services')
    compare_parser.add_argument('--services', required=True,
                              help='Comma-separated list of services to compare')
    compare_parser.add_argument('--profile', default='standard',
                              choices=['relaxed', 'standard', 'strict', 'ci_fast', 'ci_comprehensive'],
                              help='Audit profile to use')
    compare_parser.add_argument('--output', choices=['rich', 'json'], default='rich',
                              help='Output format')

    # List profiles command
    list_parser = subparsers.add_parser('list-profiles', help='List available audit profiles')

    # List services command
    services_parser = subparsers.add_parser('list-services', help='List available services')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if getattr(args, 'verbose', False) else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        if args.command == 'list-profiles':
            profiles = profile_manager.list_profiles()
            print("Available Audit Profiles:")
            print("-" * 40)
            for name, description in profiles.items():
                print("30")
            return

        if args.command == 'list-services':
            framework = AuditFramework()
            services = framework.discover_services()
            print("Available Services:")
            print("-" * 30)
            for service in services:
                status_icon = "✅" if service.status == "active" else "⚠️"
                print("20")
            return

        if args.command == 'audit':
            # Run single service audit using DDD orchestrator
            orchestrator = AuditOrchestrator()
            result = asyncio.run(orchestrator.audit_service_by_name(
                service_name=args.service,
                profile_name=getattr(args, 'profile', 'standard')
            ))

            output_format = getattr(args, 'output', 'rich')
            if output_format == 'json':
                # JSON output for CI/CD
                output = {
                    'service_name': result.service_name,
                    'overall_score': result.overall_score,
                    'grade': result.grade,
                    'critical_issues_count': len(result.critical_issues),
                    'estimated_effort_days': result.estimated_effort_days,
                    'dimensions': result.dimensions,
                    'recommendations': result.recommendations[:5],  # Top 5
                    'metadata': result.metadata
                }
                print(json.dumps(output, indent=2, default=str))
            elif output_format == 'markdown':
                # Markdown report output
                report = framework.generate_markdown_report(result)
                print(report)
            elif output_format == 'full':
                # Full detailed JSON output
                output = {
                    'service_name': result.service_name,
                    'overall_score': result.overall_score,
                    'grade': result.grade,
                    'critical_issues': result.critical_issues,
                    'estimated_effort_days': result.estimated_effort_days,
                    'dimensions': result.dimensions,
                    'recommendations': result.recommendations,
                    'architecture': result.architecture,
                    'code_quality': result.code_quality,
                    'performance': result.performance,
                    'maintainability': result.maintainability,
                    'metadata': result.metadata
                }
                print(json.dumps(output, indent=2, default=str))
            else:
                # Rich console output
                _display_rich_audit_results(framework.console, result)

        elif args.command == 'compare':
            # Run service comparison
            service_names = [s.strip() for s in args.services.split(',')]
            comparison = framework.compare_services(service_names)

            if getattr(args, 'output', 'rich') == 'json':
                print(json.dumps(comparison, indent=2, default=str))
            else:
                _display_rich_comparison(framework.console, comparison)

    except Exception as e:
        logger.error(f"Command failed: {e}")
        if getattr(args, 'verbose', False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _display_rich_audit_results(console: Console, results: AuditResults):
    """Display audit results using rich formatting"""
    if not console:
        # Fallback to basic text output
        print(f"Audit Results for {results.service_name}")
        print(f"Overall Score: {results.overall_score} ({results.grade})")
        print(f"Critical Issues: {len(results.critical_issues)}")
        return

    # Title
    console.print(Panel.fit(
        f"[bold blue]Audit Results for {results.service_name}[/bold blue]",
        title="🔍 LLM Ecosystem Audit"
    ))

    # Overall score with grade
    score_color = {
        'A': 'green',
        'B': 'yellow',
        'C': 'orange',
        'D': 'red',
        'F': 'red'
    }.get(results.grade, 'white')

    console.print(f"\n[bold]Overall Score:[/] [{score_color}]{results.overall_score}/100 ({results.grade})[/{score_color}]")

    # Critical issues alert
    if results.critical_issues:
        console.print(f"\n[bold red]🚨 Critical Issues: {len(results.critical_issues)}[/bold red]")
        for issue in results.critical_issues[:3]:  # Show top 3
            console.print(f"  • {issue['message']}")

    # Dimension scores table
    table = Table(title="Dimension Scores")
    table.add_column("Dimension", style="cyan")
    table.add_column("Score", style="magenta")
    table.add_column("Status", style="green")

    for dim, score in results.dimensions.items():
        status = "✅" if score >= 70 else "⚠️" if score >= 50 else "❌"
        table.add_row(dim.replace('_', ' ').title(), f"{score:.1f}", status)

    console.print(table)

    # Top recommendations
    if results.recommendations:
        console.print(f"\n[bold]Top Recommendations:[/bold]")
        for i, rec in enumerate(results.recommendations[:5], 1):
            console.print(f"  {i}. {rec}")

    # Metadata
    console.print(f"\n[dim]Profile:[/] {results.metadata.get('profile_used', 'unknown')}")
    console.print(f"[dim]Audit Time:[/] {results.metadata.get('audit_time_seconds', 0):.1f}s")


def _display_rich_comparison(console: Console, comparison: Dict[str, Any]):
    """Display service comparison using rich formatting"""
    if not console:
        print("Service Comparison")
        print(json.dumps(comparison['summary'], indent=2))
        return

    summary = comparison['summary']
    results = comparison['comparison']

    console.print(Panel.fit(
        "[bold blue]Service Comparison[/bold blue]",
        title="📊 Comparative Analysis"
    ))

    # Summary table
    table = Table(title="Summary Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Total Services", str(summary['total_services']))
    table.add_row("Successful Audits", str(summary['successful_audits']))
    table.add_row("Average Score", f"{summary['average_score']:.1f}")
    table.add_row("Highest Score", f"{summary['highest_score']:.1f}")
    table.add_row("Lowest Score", f"{summary['lowest_score']:.1f}")
    table.add_row("Above Threshold", f"{summary['services_above_threshold']}")
    table.add_row("Total Critical Issues", str(summary['critical_issues_total']))

    console.print(table)

    # Individual service scores
    if results:
        console.print(f"\n[bold]Individual Service Scores:[/bold]")
        for service_name, result in results.items():
            if result:
                score_color = 'green' if result.overall_score >= 70 else 'red'
                console.print(f"  {service_name}: [{score_color}]{result.overall_score:.1f}[/{score_color}] ({result.grade}) - {len(result.critical_issues)} critical issues")
            else:
                console.print(f"  {service_name}: [red]Audit failed[/red]")


if __name__ == "__main__":
    main()
