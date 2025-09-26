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


class AuditOrchestrator:
    """Orchestrates the audit process using DDD principles.

    This class coordinates between domain services, application use cases,
    and infrastructure components to execute audits.
    """

    def __init__(self, profile: Optional[AuditProfile] = None):
        """Initialize the audit orchestrator with all dependencies."""
        self.profile = profile or profile_manager.get_profile('standard')
        thresholds_dict = get_thresholds_for_profile(self.profile)

        # Initialize domain service
        self.audit_service = AuditService(ThresholdConfig.from_dict(thresholds_dict))

        # Initialize infrastructure services
        self.file_system = FileSystemService()

        # Initialize analyzers (infrastructure implementations)
        self.analyzers = {
            'architecture': ArchitectureAnalyzer(self.profile),
            'code_quality': CodeQualityAnalyzer(self.profile),
            'performance': PerformanceAnalyzer(self.profile),
            'maintainability': MaintainabilityAnalyzer(self.profile),
        }

        # Initialize application use case
        self.audit_use_case = AuditServiceUseCase(self.audit_service, self.analyzers)

    async def audit_service_by_name(
        self,
        service_name: str,
        profile_name: str = "standard"
    ) -> AnalysisResult:
        """
        Audit a service by name using the specified profile.

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

        # Use the profile from the orchestrator, or get a new one if profile_name is different
        if profile_name != self.profile.name:
            try:
                profile = profile_manager.get_profile(profile_name)
            except ValueError as e:
                raise ValueError(f"Profile '{profile_name}' not found") from e
        else:
            profile = self.profile

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
                    'estimated_effort_days': result.get_estimated_effort_days(),
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
                    'estimated_effort_days': result.get_estimated_effort_days(),
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


def _display_rich_audit_results(console: Console, results: AnalysisResult):
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
        'A+': 'green',
        'B': 'yellow',
        'B+': 'yellow',
        'C': 'orange',
        'C+': 'orange',
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
