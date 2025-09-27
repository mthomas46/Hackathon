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
from infrastructure.resource_optimizer import get_resource_optimizer
from config.profiles import profile_manager
from config.thresholds import get_thresholds_for_profile

# Enhanced reporting libraries
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID, TimeRemainingColumn, MofNCompleteColumn
    from rich.text import Text
    from rich.columns import Columns
    from rich.live import Live
    from rich.spinner import Spinner
    from rich.style import Style
    from rich import box
    from rich.align import Align
    from rich.layout import Layout
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# Try to import async libraries for parallel processing
try:
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    HAS_ASYNC = True
except ImportError:
    HAS_ASYNC = False

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

        # Initialize console for rich output
        self.console = Console() if HAS_RICH else None

    def discover_services(self) -> List[str]:
        """Discover available services in the services directory with enhanced detection."""
        # Find the project root by looking for the services directory
        current_path = Path.cwd()
        services_dir = current_path / "services"

        # If not found, try going up one level (in case we're in a subdirectory)
        if not services_dir.exists():
            services_dir = current_path.parent / "services"

        if not services_dir.exists():
            return []

        services = []

        # Only look at directories, not files
        directories = [item for item in services_dir.iterdir() if item.is_dir()]

        # Filter out common non-service directories
        exclude_dirs = {'__pycache__', '_template', '.git', '.vscode', '.idea', 'node_modules'}
        service_candidates = [d for d in directories if d.name not in exclude_dirs and not d.name.startswith('.')]

        # Use parallel processing for service discovery if we have many directories
        if HAS_ASYNC and len(service_candidates) > 10:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=min(4, len(service_candidates))) as executor:
                discovery_tasks = []
                for item in service_candidates:
                    task = loop.run_in_executor(executor, self._check_if_service, item)
                    discovery_tasks.append(task)

                # Gather results
                try:
                    results = loop.run_until_complete(asyncio.gather(*discovery_tasks, return_exceptions=True))
                    for item, is_service in zip(service_candidates, results):
                        if isinstance(is_service, bool) and is_service:
                            services.append(item.name)
                except Exception:
                    # Fall back to sequential discovery
                    for item in service_candidates:
                        if self._check_if_service(item):
                            services.append(item.name)
        else:
            # Sequential discovery for smaller numbers
            for item in service_candidates:
                if self._check_if_service(item):
                    services.append(item.name)

        return sorted(services)

    def _check_if_service(self, service_path: Path) -> bool:
        """Check if a directory contains a valid service."""
        # Exclude known infrastructure/configuration directories
        infrastructure_dirs = {
            "ollama",  # Just Docker config, not a service
            "redis",   # Just Redis config, not a service
            "data-services-dashboard",  # Minimal placeholder
            "_template",  # Template directory
        }

        if service_path.name in infrastructure_dirs:
            return False

        # Enhanced service detection
        service_indicators = [
            "main.py", "app.py", "__main__.py",  # Entry points
            "requirements.txt", "pyproject.toml",  # Dependencies
            "Dockerfile",  # Containerization
            "config.yaml", "config.yml"  # Configuration
        ]

        # Check for any service indicators
        for indicator in service_indicators:
            if (service_path / indicator).exists():
                return True

        # Check for Python modules in a modules/ directory
        modules_dir = service_path / "modules"
        if modules_dir.exists() and modules_dir.is_dir():
            py_files = list(modules_dir.glob("**/*.py"))
            if py_files:
                return True

        return False

    def compare_services(self, service_names: List[str]) -> Dict[str, Any]:
        """Compare multiple services - stub implementation."""
        # For now, return a simple comparison
        return {
            'services_compared': service_names,
            'message': 'Service comparison not fully implemented yet'
        }

    async def audit_service_by_name(
        self,
        service_name: str,
        profile_name: str = "standard",
        full_audit: bool = False
    ) -> AnalysisResult:
        """
        Audit a service by name using the specified profile.

        Args:
            service_name: Name of the service to audit
            profile_name: Name of the audit profile to use

        Returns:
            Complete analysis result
        """
        # Discover service - try both underscore and dash versions
        service_path = self._discover_service_path(service_name)
        if not service_path:
            # Try converting underscores to dashes for directory lookup
            alt_service_name = service_name.replace('_', '-')
            service_path = self._discover_service_path(alt_service_name)
            if service_path:
                service_name = alt_service_name  # Use the kebab-case version
            else:
                raise ValueError(f"Service '{service_name}' not found")
        else:
            # Even if we found the path, ensure the service name is in kebab-case
            if '_' in service_name:
                service_name = service_name.replace('_', '-')

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
        return await self.audit_use_case.execute(service_info, profile, full_audit)

    def _discover_service_path(self, service_name: str) -> Optional[Path]:
        """Discover the path for a service by name."""
        # Look in common service directories - try both underscore and dash versions
        service_names_to_try = [service_name]
        if '_' in service_name:
            service_names_to_try.append(service_name.replace('_', '-'))
        elif '-' in service_name:
            service_names_to_try.append(service_name.replace('-', '_'))

        search_paths = []
        for svc_name in service_names_to_try:
            search_paths.extend([
                Path.cwd() / "services" / svc_name,
                Path.cwd() / svc_name,
                Path.cwd().parent / "services" / svc_name,
            ])

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

    # Get available profiles dynamically
    try:
        available_profiles = list(profile_manager.list_profiles().keys())
    except:
        available_profiles = ['relaxed', 'standard', 'strict', 'ci_fast', 'ci_comprehensive', 'strict_ddd']

    audit_parser.add_argument('--profile', default='standard',
                            choices=available_profiles,
                            help='Audit profile to use')
    audit_parser.add_argument('--output', choices=['rich', 'json', 'markdown', 'full'], default='rich',
                            help='Output format (full includes all detailed analysis)')
    audit_parser.add_argument('--verbose', action='store_true', help='Verbose output')
    audit_parser.add_argument('--full', action='store_true',
                              help='Full audit mode - analyze all files in service directory (no limits)')

    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare multiple services')
    compare_parser.add_argument('--services', required=True,
                              help='Comma-separated list of services to compare')

    # Get available profiles dynamically for compare command too
    try:
        compare_available_profiles = list(profile_manager.list_profiles().keys())
    except:
        compare_available_profiles = ['relaxed', 'standard', 'strict', 'ci_fast', 'ci_comprehensive', 'strict_ddd']

    compare_parser.add_argument('--profile', default='standard',
                              choices=compare_available_profiles,
                              help='Audit profile to use')
    compare_parser.add_argument('--output', choices=['rich', 'json'], default='rich',
                              help='Output format')

    # List profiles command
    list_parser = subparsers.add_parser('list-profiles', help='List available audit profiles')

    # List services command
    services_parser = subparsers.add_parser('list-services', help='List available services')

    # Bulk audit command
    bulk_parser = subparsers.add_parser('bulk-audit', help='Audit all services in parallel')
    bulk_parser.add_argument('--profile', default='strict',
                            choices=available_profiles,
                            help='Audit profile to use for all services')
    bulk_parser.add_argument('--output', default='rich',
                            choices=['json', 'rich', 'summary'],
                            help='Output format for results')
    bulk_parser.add_argument('--max-parallel', type=int, default=3,
                            help='Maximum number of services to audit in parallel')
    bulk_parser.add_argument('--services', nargs='*',
                              help='Specific services to audit (default: all)')
    bulk_parser.add_argument('--full', action='store_true',
                              help='Full audit mode - analyze all files in service directory (no limits)')

    # Resources/optimization command
    resources_parser = subparsers.add_parser('resources', help='Display system resources and optimization recommendations')
    resources_parser.add_argument('--service', help='Analyze a specific service for workload optimization')

    # Report display command
    report_parser = subparsers.add_parser('report', help='Display audit reports from JSON files')
    report_parser.add_argument('service', help='Service name to display report for')
    report_parser.add_argument('--profile', default='strict', 
                              choices=['relaxed', 'standard', 'strict', 'ci_fast', 'ci_comprehensive', 'strict_ddd'],
                              help='Audit profile to display (default: strict')
    report_parser.add_argument('--output', choices=['rich', 'json', 'summary'], default='rich',
                              help='Output format (default: rich')
    report_parser.add_argument('--verbose', action='store_true',
                              help='Show detailed issues and recommendations')

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
            framework = AuditOrchestrator()
            services = framework.discover_services()
            print("Available Services:")
            print("-" * 30)
            for service in services:
                print(f"  ✅ {service}")
            return

        if args.command == 'audit':
            # Run single service audit using DDD orchestrator
            orchestrator = AuditOrchestrator()
            result = asyncio.run(orchestrator.audit_service_by_name(
                service_name=args.service,
                profile_name=getattr(args, 'profile', 'standard'),
                full_audit=getattr(args, 'full', False)
            ))

            output_format = getattr(args, 'output', 'rich')

            # Save audit result to file
            profile_name = getattr(args, 'profile', 'standard')
            full_audit = getattr(args, 'full', False)
            _save_audit_result(result, profile_name, full_audit)

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
                # Markdown report output - not implemented yet
                print("Markdown output not implemented yet. Use 'json' or 'full' format.")
                print(json.dumps({
                    'service_name': result.service_name,
                    'overall_score': result.overall_score,
                    'grade': result.grade,
                    'recommendations': result.recommendations[:5]
                }, indent=2, default=str))
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
                # Rich console output with enhanced visual feedback
                if HAS_RICH and orchestrator.console:
                    # Create a beautiful audit results display with live updates
                    _display_enhanced_audit_results(orchestrator.console, result, getattr(args, 'verbose', False))
                else:
                    _display_rich_audit_results(orchestrator.console, result)

        elif args.command == 'compare':
            # Run service comparison
            service_names = [s.strip() for s in args.services.split(',')]
            comparison = framework.compare_services(service_names)

            if getattr(args, 'output', 'rich') == 'json':
                print(json.dumps(comparison, indent=2, default=str))
            else:
                _display_rich_comparison(framework.console, comparison)

        elif args.command == 'bulk-audit':
            # Bulk audit all services with parallel processing
            orchestrator = AuditOrchestrator()
            asyncio.run(_handle_bulk_audit(args, orchestrator))

        elif args.command == 'resources':
            # Display system resources and optimization recommendations
            _handle_resources_command(args)

        elif args.command == 'report':
            # Display audit reports from JSON files
            _handle_report_command(args)
            # Display system resources and optimization recommendations
            _handle_resources_command(args)

    except Exception as e:
        logger.error(f"Command failed: {e}")
        if getattr(args, 'verbose', False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


async def _handle_bulk_audit(args, orchestrator):
    """Handle bulk auditing of all services with parallel processing and progress tracking."""
    import time

    # Discover all services with heartbeat feedback
    console = orchestrator.console if HAS_RICH else None

    if console:
        console.print("[bold blue]🔍 Service Discovery Phase[/bold blue]")
        with console.status("[bold blue]🔍 Scanning service directories...", spinner="dots") as status:
            start_time = time.time()
            services = orchestrator.discover_services()
            discovery_time = time.time() - start_time
            status.update(f"[green]✅ Found {len(services)} services in {discovery_time:.2f}s[/green]")
            time.sleep(0.5)  # Brief pause to show result
    else:
        services = orchestrator.discover_services()

    # Filter services if specified
    if getattr(args, 'services', None):
        # Handle comma-separated service names
        specified_services = []
        for svc_arg in args.services:
            specified_services.extend([s.strip() for s in svc_arg.split(',')])
        services = [s for s in services if s in specified_services]

    if not services:
        if HAS_RICH and orchestrator.console:
            console.print("[yellow]⚠️  No services found to audit[/yellow]")
        else:
            print("No services found to audit")
        return

    profile_name = getattr(args, 'profile', 'strict')
    output_format = getattr(args, 'output', 'rich')

    # Get optimal parallel workers from resource optimizer
    try:
        resource_optimizer = get_resource_optimizer()
        # Sample one service to get workload characteristics for optimization
        sample_service_path = None
        if services:
            try:
                from infrastructure.file_system.service_discovery_service import ServiceDiscoveryService
                discovery_service = ServiceDiscoveryService()
                discovered_services = discovery_service.discover_services()
                service_info = next((s for s in discovered_services if s.name == services[0]), None)
                if service_info:
                    sample_service_path = service_info.path
            except Exception as discovery_error:
                logger.debug(f"Service discovery for optimization failed: {discovery_error}")
                # Try manual path construction
                from pathlib import Path
                potential_path = Path("services") / services[0]
                if potential_path.exists():
                    sample_service_path = potential_path

        if sample_service_path:
            optimization_settings = resource_optimizer.get_optimal_settings(sample_service_path, getattr(args, 'full', False))
            optimal_workers = optimization_settings['optimization_profile']['parallel_workers']

            # Use optimal workers unless user explicitly set max_parallel
            # Since argparse sets default=3, we need to check if it was actually specified
            if hasattr(args, 'max_parallel') and args.max_parallel != 3:  # 3 is the default
                # User explicitly set max_parallel
                max_parallel = args.max_parallel
            else:
                # Use optimal workers
                max_parallel = optimal_workers

            # Store optimization info for later display
            optimization_info = {
                'optimal_workers': optimal_workers,
                'recommendations': optimization_settings.get('recommendations', [])
            }

            # Log optimization info
            logger.info(f"🎯 Resource optimization: {optimal_workers} parallel workers recommended")
            for rec in optimization_info['recommendations']:
                logger.info(f"💡 {rec}")
        else:
            max_parallel = getattr(args, 'max_parallel', 3)
            optimization_info = None
    except Exception as e:
        logger.warning(f"⚠️ Resource optimizer failed ({e}), using default parallel workers")
        max_parallel = getattr(args, 'max_parallel', 3)

    if HAS_RICH and orchestrator.console:
        console = orchestrator.console

        # Display bulk audit header
        header_panel = Panel(
            f"[bold blue]🔍 Bulk Auditing {len(services)} Services[/bold blue]\n"
            f"[dim]Profile: {profile_name} | Parallel: {max_parallel} | Format: {output_format}[/dim]",
            title="[bold green]🚀 Starting Bulk Audit[/bold green]",
            border_style="green"
        )
        console.print(header_panel)

        # Display optimization info if available
        try:
            if optimization_info:
                console.print(f"[blue]🎯 Resource optimization: {optimization_info['optimal_workers']} parallel workers recommended[/blue]")
        except NameError:
            pass  # optimization_info not defined

        # Create progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=console,
            transient=False
        ) as progress:
            audit_task = progress.add_task(
                f"📊 Auditing {len(services)} services...",
                total=len(services)
            )

            # Audit services with controlled parallelism and enhanced progress feedback
            semaphore = asyncio.Semaphore(max_parallel)
            results = []
            active_audits = set()
            completed_count = 0

            async def audit_service_with_semaphore(service_name):
                nonlocal completed_count
                async with semaphore:
                    active_audits.add(service_name)
                    start_time = time.time()

                    # Show current active audits in progress description
                    active_list = ", ".join(sorted(list(active_audits)[:3])) + ("..." if len(active_audits) > 3 else "")
                    progress.update(audit_task, description=f"🔍 Auditing {service_name} | Active: {active_list}")

                    logger.info("🚀 Starting parallel audit for service: %s", service_name)

                    try:
                        result = await orchestrator.audit_service_by_name(service_name, profile_name, full_audit=getattr(args, 'full', False))
                        end_time = time.time()
                        duration = end_time - start_time

                        if result and hasattr(result, 'metadata'):
                            result.metadata['audit_duration_seconds'] = duration

                        results.append(result)
                        active_audits.remove(service_name)
                        completed_count += 1

                        # Calculate ETA based on completed audits
                        successful_results = [r for r in results if r and hasattr(r, 'overall_score')]
                        if successful_results:
                            avg_time = sum(r.metadata.get('audit_duration_seconds', 0) for r in successful_results) / len(successful_results)
                            remaining = len(services) - completed_count
                            eta = avg_time * remaining
                            eta_str = f" | ETA: {eta:.0f}s" if eta > 0 else ""
                        else:
                            eta_str = ""

                        progress.update(audit_task, advance=1,
                                      description=f"✅ {service_name} ({duration:.1f}) | {completed_count}/{len(services)} done{eta_str}")

                        logger.info("✅ Completed audit for %s in %.1f (Score: %.1f, Grade: %s)",
                                   service_name, duration,
                                   result.overall_score if result else 0.0,
                                   result.grade if result else 'F')

                        return result

                    except Exception as e:
                        end_time = time.time()
                        duration = end_time - start_time
                        active_audits.discard(service_name)
                        completed_count += 1

                        logger.error("❌ Audit failed for %s after %.1f: %s", service_name, duration, e)

                        # Create error result
                        error_result = type('ErrorResult', (), {
                            'service_name': service_name,
                            'overall_score': 0.0,
                            'grade': 'F',
                            'critical_issues': [{'message': f'Audit failed: {str(e)}'}],
                            'recommendations': [f'Fix audit error: {str(e)}'],
                            'dimensions': {'architecture': 0.0, 'code_quality': 0.0, 'performance': 0.0, 'maintainability': 0.0},
                            'metadata': {'audit_duration_seconds': duration, 'error': str(e)},
                            'to_dict': lambda self: {
                                'service_name': self.service_name,
                                'overall_score': self.overall_score,
                                'grade': self.grade,
                                'critical_issues': self.critical_issues,
                                'recommendations': self.recommendations,
                                'dimensions': self.dimensions,
                                'metadata': self.metadata
                            }
                        })()
                        results.append(error_result)
                        progress.update(audit_task, advance=1, description=f"❌ Failed {service_name} ({duration:.1f})")
                        return error_result

            # Run all audits in parallel with controlled concurrency
            tasks = [audit_service_with_semaphore(service) for service in services]
            await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out failed audits but keep error results for reporting
            successful_results = [r for r in results if r is not None and hasattr(r, 'service_name')]

            # Save all results to files
            for result in successful_results:
                _save_audit_result(result, profile_name, getattr(args, 'full', False))

            # Display results based on output format
            if output_format == 'summary':
                _display_bulk_audit_summary(console, successful_results, services)
            elif output_format == 'json':
                _display_bulk_audit_json(successful_results)
            else:
                _display_bulk_audit_rich(console, successful_results)

    else:
        # Fallback for systems without rich
        print(f"🔍 Bulk auditing {len(services)} services with profile '{profile_name}'...")

        results = []
        for i, service in enumerate(services, 1):
            print(f"[{i}/{len(services)}] Auditing {service}...")
            try:
                result = await orchestrator.audit_service_by_name(service, profile_name, full_audit=getattr(args, 'full', False))
                results.append(result)
                print(f"  ✅ {service}: {result.overall_score} ({result.grade})")
            except Exception as e:
                print(f"  ❌ {service}: Failed - {e}")

        print(f"\nCompleted bulk audit of {len(results)}/{len(services)} services")

def _display_bulk_audit_summary(console: Console, results: List, total_services: List):
    """Display a summary of bulk audit results."""
    if not results:
        console.print("[yellow]⚠️  No successful audits to display[/yellow]")
        return

    # Calculate statistics
    scores = [r.overall_score for r in results]
    avg_score = sum(scores) / len(scores)
    grade_counts = {}
    for result in results:
        grade_counts[result.grade] = grade_counts.get(result.grade, 0) + 1

    # Summary panel
    summary_panel = Panel(
        f"[bold blue]📊 Bulk Audit Summary[/bold blue]\n\n"
        f"[bold]Services Audited:[/bold] {len(results)}/{len(total_services)}\n"
        f"[bold]Average Score:[/bold] {avg_score:.1f}\n"
        f"[bold]Grade Distribution:[/bold]\n" +
        "\n".join([f"  {grade}: {count}" for grade, count in grade_counts.items()]),
        title="[bold green]📋 Summary[/bold green]",
        border_style="blue"
    )

    console.print(summary_panel)

    # Top performers and issues
    top_performers = sorted(results, key=lambda x: x.overall_score, reverse=True)[:3]
    worst_performers = sorted(results, key=lambda x: x.overall_score)[:3]

    if top_performers:
        console.print(f"\n[bold green]🌟 Top Performers:[/bold green]")
        for result in top_performers:
            console.print(f"  🏆 {result.service_name}: {result.overall_score} ({result.grade})")

    if worst_performers and len(results) > 1:
        console.print(f"\n[bold red]⚠️  Need Attention:[/bold red]")
        for result in worst_performers:
            console.print(f"  📉 {result.service_name}: {result.overall_score} ({result.grade})")

def _display_bulk_audit_json(results: List):
    """Display bulk audit results in JSON format."""
    output = {
        "bulk_audit_summary": {
            "total_services": len(results),
            "average_score": sum(r.overall_score for r in results) / len(results) if results else 0,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        },
        "services": [
            {
                "name": r.service_name,
                "score": r.overall_score,
                "grade": r.grade,
                "dimensions": r.dimensions,
                "critical_issues": len(r.critical_issues),
                "recommendations": len(r.recommendations)
            }
            for r in results
        ]
    }
    print(json.dumps(output, indent=2, default=str))

def _display_bulk_audit_rich(console: Console, results: List):
    """Display bulk audit results in rich table format with enhanced visuals."""
    if not results:
        console.print("[yellow]⚠️  No successful audits to display[/yellow]")
        return

    # Enhanced header with summary stats
    scores = [r.overall_score for r in results]
    avg_score = sum(scores) / len(scores) if scores else 0
    median_score = sorted(scores)[len(scores)//2] if scores else 0

    # Determine overall ecosystem health
    if avg_score >= 85:
        health_status = "🌟 EXCELLENT"
        health_color = "bright_green"
        health_desc = "Production-ready ecosystem"
    elif avg_score >= 75:
        health_status = "✅ GOOD"
        health_color = "green"
        health_desc = "Meets quality standards"
    elif avg_score >= 65:
        health_status = "⚠️  NEEDS ATTENTION"
        health_color = "yellow"
        health_desc = "Improvement opportunities exist"
    else:
        health_status = "🚨 CRITICAL"
        health_color = "bright_red"
        health_desc = "Major quality issues detected"

    header_panel = Panel(
        f"[bold {health_color}]{health_status}[/bold {health_color}]\n"
        f"[dim]{health_desc}[/dim]\n\n"
        f"[bold blue]📊 Audit Summary:[/bold blue]\n"
        f"[dim]• Services: {len(results)} audited[/dim]\n"
        f"[dim]• Average: {avg_score:.1f}/100[/dim]\n"
        f"[dim]• Range: {min(scores):.1f} - {max(scores):.1f}[/dim]",
        title="[bold]🔍 Bulk Audit Results[/bold]",
        border_style=health_color
    )
    console.print(header_panel)

    # Enhanced results table with more columns and better formatting
    results_table = Table(
        title="[bold blue]🏆 Service Rankings[/bold blue]",
        show_header=True,
        header_style="bold blue",
        box=box.ROUNDED,
        show_lines=True
    )
    results_table.add_column("🏅 Rank", style="yellow", justify="center", width=6)
    results_table.add_column("🏗️  Service", style="cyan", width=22)
    results_table.add_column("📊 Score", style="magenta", justify="right", width=10)
    results_table.add_column("🎖️  Grade", width=8, justify="center")
    results_table.add_column("🚨 Issues", style="red", justify="right", width=8)
    results_table.add_column("⏱️  Duration", style="yellow", justify="right", width=10)
    results_table.add_column("📈 Trend", width=8, justify="center")

    sorted_results = sorted(results, key=lambda x: x.overall_score, reverse=True)
    grade_counts = {}

    for i, result in enumerate(sorted_results, 1):
        duration = result.metadata.get('audit_duration_seconds', 0)
        duration_str = f"{duration:.1f}s" if duration else "N/A"

        # Enhanced grade colors with emojis
        grade_info = {
            'A+': ('🌟', 'bright_green'), 'A': ('✅', 'bright_green'),
            'B+': ('👍', 'green'), 'B': ('👌', 'green'),
            'C+': ('⚠️', 'yellow'), 'C': ('🟡', 'yellow'),
            'D': ('❌', 'red'), 'F': ('💥', 'bright_red')
        }
        grade_emoji, grade_color = grade_info.get(result.grade, ('❓', 'white'))

        # Count grades for distribution
        grade_counts[result.grade] = grade_counts.get(result.grade, 0) + 1

        # Performance trend indicator (simplified)
        if result.overall_score >= 80:
            trend = "[bright_green]↗️[/bright_green]"
        elif result.overall_score >= 70:
            trend = "[yellow]➡️[/yellow]"
        else:
            trend = "[red]↘️[/red]"

        results_table.add_row(
            f"{i}",
            result.service_name,
            f"[bold {grade_color}]{result.overall_score:.1f}[/bold {grade_color}]",
            f"{grade_emoji} {result.grade}",
            str(len(result.critical_issues)),
            duration_str,
            trend
        )

    console.print(results_table)

    # Enhanced statistics with grade distribution
    console.print(f"\n[bold blue]📈 Detailed Statistics[/bold blue]")

    # Grade distribution chart
    grade_distribution = Table(show_header=False, box=None, show_edge=False)
    grade_distribution.add_column("Grade", style="bold", width=8)
    grade_distribution.add_column("Count", style="cyan", width=8)
    grade_distribution.add_column("Percentage", style="magenta", width=12)
    grade_distribution.add_column("Visual", width=20)

    sorted_grades = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F']
    for grade in sorted_grades:
        count = grade_counts.get(grade, 0)
        if count > 0:
            percentage = (count / len(results)) * 100
            visual_bar = "█" * int(percentage // 5)  # Scale to 20 chars max
            grade_distribution.add_row(
                grade,
                str(count),
                f"{percentage:.1f}%",
                f"[green]{visual_bar}[/green]"
            )

    console.print(grade_distribution)

    # Performance insights
    console.print(f"\n[bold green]🎯 Performance Insights[/bold green]")

    insights = []
    if avg_score >= 85:
        insights.append("🌟 [green]Excellent overall quality - maintain standards[/green]")
    elif avg_score >= 75:
        insights.append("✅ [green]Good quality foundation - focus on consistency[/green]")
    else:
        insights.append("🚨 [red]Quality improvement needed across multiple services[/red]")

    # Top performers
    top_performers = sorted_results[:3]
    if top_performers:
        top_names = [f"[bold cyan]{r.service_name}[/bold cyan]" for r in top_performers]
        insights.append(f"🏆 Top performers: {', '.join(top_names)}")

    # Services needing attention
    critical_services = [r for r in sorted_results if r.overall_score < 70]
    if critical_services:
        critical_names = [f"[bold red]{r.service_name}[/bold red]" for r in critical_services[:3]]
        insights.append(f"🚨 Critical attention needed: {', '.join(critical_names)}")

    # Total audit time
    total_time = sum(r.metadata.get('audit_duration_seconds', 0) for r in results)
    avg_time = total_time / len(results) if results else 0
    insights.append(f"⏱️  Total audit time: {total_time:.1f}s (avg: {avg_time:.1f}s per service)")

    for insight in insights:
        console.print(f"  {insight}")

    # Next steps recommendations
    console.print(f"\n[bold yellow]💡 Next Steps Recommendations[/bold yellow]")

    recommendations = []
    if critical_services:
        recommendations.append(f"🔴 [red]Address {len(critical_services)} services with scores below 70[/red]")
    if avg_score < 80:
        recommendations.append("📈 Focus on improving overall ecosystem quality")
    if len([r for r in results if r.metadata.get('audit_duration_seconds', 0) > 30]) > 0:
        recommendations.append("⚡ Optimize slow-performing services (>30s audit time)")
    if len(set(r.grade for r in results)) <= 2:
        recommendations.append("🎯 Work towards more consistent quality across services")

    if not recommendations:
        recommendations.append("✅ [green]Maintain current quality standards and monitor trends[/green]")

    for rec in recommendations:
        console.print(f"  {rec}")

def _save_audit_result(result: AnalysisResult, profile_name: str, full_audit: bool = False):
    """Save audit result to the appropriate directory based on profile and audit type."""
    import json
    from pathlib import Path

    # Determine directory based on profile and audit type
    if full_audit:
        audit_dir = Path("audit-results/full")
    elif profile_name == 'strict':
        audit_dir = Path("audit-results/strict")
    elif profile_name == 'comprehensive':
        audit_dir = Path("audit-results/comprehensive")
    else:
        audit_dir = Path("audit-results/standard")

    # Create directory if it doesn't exist
    audit_dir.mkdir(parents=True, exist_ok=True)

    # Create filename
    filename = f"audit_{result.service_name}.json"
    filepath = audit_dir / filename

    # Save the result
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, default=str, ensure_ascii=False)
        logger.info(f"Saved audit result to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save audit result to {filepath}: {e}")

def _display_enhanced_audit_results(console: Console, results: AnalysisResult, verbose: bool = False):
    """Display audit results with enhanced visual feedback and animations"""
    import time

    # Show analysis completion progress
    console.print("\n[bold green]✅ Analysis Complete[/bold green] - Generating results...")

    # Create a spectacular animated header
    console.print()  # Add spacing

    # Service quality indicator
    quality_indicator = ""
    if results.overall_score >= 90:
        quality_indicator = "🌟 [bold bright_green]EXCEPTIONAL QUALITY[/bold bright_green] 🌟"
    elif results.overall_score >= 80:
        quality_indicator = "✅ [bold green]HIGH QUALITY[/bold green] ✅"
    elif results.overall_score >= 70:
        quality_indicator = "⚠️ [bold yellow]GOOD WITH IMPROVEMENTS[/bold yellow] ⚠️"
    elif results.overall_score >= 60:
        quality_indicator = "🟡 [bold yellow]NEEDS ATTENTION[/bold yellow] 🟡"
    else:
        quality_indicator = "🚨 [bold bright_red]CRITICAL ISSUES[/bold bright_red] 🚨"

    header_text = Text("🔍 LLM Ecosystem Audit Framework", style="bold blue")
    header_panel = Panel(
        Align.center(f"{header_text}\n\n{quality_indicator}"),
        title="[bold green]🚀 Audit Complete[/bold green]",
        border_style="green",
        padding=(1, 2)
    )

    console.print(header_panel)

    # Service information with enhanced styling
    service_info = Panel(
        f"[bold cyan]Service:[/bold cyan] {results.service_name}\n"
        f"[bold cyan]Profile:[/bold cyan] {results.metadata.get('profile_used', 'standard')}\n"
        f"[bold cyan]Timestamp:[/bold cyan] {time.strftime('%Y-%m-%d %H:%M:%S')}",
        title="[bold]📋 Audit Information[/bold]",
        border_style="blue"
    )

    console.print(service_info)

    # Overall score with spectacular animated reveal effect
    score_color_map = {
        'A+': ('bright_green', '🌟 EXCELLENT'),
        'A': ('bright_green', '✅ HIGH QUALITY'),
        'B+': ('green', '👍 VERY GOOD'),
        'B': ('green', '👌 GOOD'),
        'C+': ('yellow', '⚠️ NEEDS WORK'),
        'C': ('yellow', '🟡 FAIR'),
        'D': ('yellow', '❌ POOR'),
        'F': ('bright_red', '💥 CRITICAL')
    }

    score_color, quality_desc = score_color_map.get(results.grade, ('white', '❓ UNKNOWN'))

    # Create spectacular score display with progress visualization
    score_progress = "█" * int(results.overall_score // 10) + "░" * (10 - int(results.overall_score // 10))

    score_panel = Panel(
        f"[bold {score_color}]{quality_desc}[/bold {score_color}]\n\n"
        f"[bold white]Score: {results.overall_score:.1f}/100[/bold white] [dim](Grade: {results.grade})[/dim]\n"
        f"[bold {score_color}]{score_progress}[/bold {score_color}] {results.overall_score:.1f}%\n\n"
        f"[dim]🚨 Critical Issues: {len(results.critical_issues)}[/dim]\n"
        f"[dim]⏱️  Estimated Effort: {results.get_estimated_effort_days():.1f} days[/dim]\n"
        f"[dim]🎯 Audit Duration: {results.metadata.get('audit_duration_seconds', 0):.2f}s[/dim]",
        title="[bold]📊 Final Assessment[/bold]",
        border_style=score_color,
        padding=(1, 2)
    )

    console.print(score_panel)

    # Enhanced dimension scores with beautiful progress bars and insights
    console.print("\n[bold magenta]📈 Architecture Quality Dimensions[/bold magenta]")

    dimensions_table = Table(
        show_header=True,
        header_style="bold magenta",
        box=box.ROUNDED,
        show_lines=True
    )
    dimensions_table.add_column("🏗️ Dimension", style="cyan", width=18)
    dimensions_table.add_column("📊 Score", style="magenta", justify="right", width=10)
    dimensions_table.add_column("🎨 Status", width=12, justify="center")
    dimensions_table.add_column("📈 Progress", width=25, justify="center")
    dimensions_table.add_column("💡 Insight", style="dim white", width=35)

    # Dimension descriptions for better understanding
    dimension_insights = {
        'architecture': 'DDD + REST compliance, layer separation',
        'code_quality': 'Clean code, cyclomatic complexity, coverage',
        'performance': 'Efficiency, memory usage, response times',
        'maintainability': 'Documentation, code organization, dead code'
    }

    for dim, score in results.dimensions.items():
        if score >= 95:
            status = "[bright_green]🌟 Excellent[/bright_green]"
            progress_color = "bright_green"
        elif score >= 85:
            status = "[green]✅ Very Good[/green]"
            progress_color = "green"
        elif score >= 75:
            status = "[yellow]⚠️ Good[/yellow]"
            progress_color = "yellow"
        elif score >= 65:
            status = "[yellow]🟡 Needs Work[/yellow]"
            progress_color = "yellow"
        else:
            status = "[bright_red]❌ Critical[/bright_red]"
            progress_color = "bright_red"

        # Create beautiful progress bar with percentage
        filled = int(score // 10)
        empty = 10 - filled
        progress_bar = f"[{progress_color}]{'█' * filled}{'░' * empty}[/{progress_color}]"

        dim_name = dim.replace('_', ' ').title()
        insight = dimension_insights.get(dim, 'Quality assessment')
        dimensions_table.add_row(
            dim_name,
            f"[bold]{score:.1f}[/bold]",
            status,
            f"{progress_bar} [{progress_color}]{score:.1f}%[/{progress_color}]",
            f"[dim]{insight}[/dim]"
        )

    console.print(dimensions_table)

    # Critical issues with spectacular formatting
    if results.critical_issues:
        console.print(f"\n[bold bright_red]🚨 Critical Issues Found ({len(results.critical_issues)})[/bold bright_red]")

        issues_table = Table(
            show_header=True,
            header_style="bold bright_red",
            box=box.ROUNDED,
            title="[bold red]⚠️ Issues Requiring Immediate Attention[/bold red]",
            title_style="bold red"
        )
        issues_table.add_column("🔥 Priority", width=10, justify="center")
        issues_table.add_column("📋 Issue Description", style="red", width=60)
        issues_table.add_column("💡 Impact", style="yellow", width=20)

        priority_levels = {
            0: ("[bright_red]🔴 CRITICAL[/bright_red]", "[red]Blocks Production[/red]"),
            1: ("[red]🟠 HIGH[/red]", "[yellow]Major Issues[/yellow]"),
            2: ("[yellow]🟡 MEDIUM[/yellow]", "[yellow]Needs Attention[/yellow]")
        }

        for i, issue in enumerate(results.critical_issues[:7]):  # Show more issues
            priority_icon, impact = priority_levels.get(min(i // 2, 2), ("[white]❓[/white]", "[white]Unknown[/white]"))
            issue_text = issue.get('message', str(issue)) if isinstance(issue, dict) else str(issue)
            issues_table.add_row(priority_icon, issue_text, impact)

        console.print(issues_table)

    # Enhanced recommendations section with categorized suggestions
    if results.recommendations:
        console.print(f"\n[bold bright_green]💡 Actionable Recommendations ({len(results.recommendations)})[/bold bright_green]")

        # Categorize recommendations
        quick_wins = []
        architecture_fixes = []
        quality_improvements = []
        monitoring_tasks = []

        for rec in results.recommendations:
            rec_lower = rec.lower()
            if any(keyword in rec_lower for keyword in ['test', 'coverage', 'lint', 'format']):
                quick_wins.append(rec)
            elif any(keyword in rec_lower for keyword in ['ddd', 'layer', 'architecture', 'pattern']):
                architecture_fixes.append(rec)
            elif any(keyword in rec_lower for keyword in ['complexity', 'duplication', 'maintainability']):
                quality_improvements.append(rec)
            else:
                monitoring_tasks.append(rec)

        # Display categorized recommendations
        categories = [
            ("🚀 Quick Wins", quick_wins[:3], "bright_green"),
            ("🏗️ Architecture", architecture_fixes[:3], "blue"),
            ("⚡ Quality", quality_improvements[:3], "yellow"),
            ("📊 Monitoring", monitoring_tasks[:3], "cyan")
        ]

        for category_name, category_recs, color in categories:
            if category_recs:
                console.print(f"\n[bold {color}]{category_name}[/bold {color}]")

                rec_table = Table(show_header=False, box=box.ROUNDED, show_edge=False)
                rec_table.add_column("🎯 Action", width=3, justify="center")
                rec_table.add_column("📝 Recommendation", style=color, width=65)

                priority_icons = ["🔥", "⚡", "💡"]
                for i, rec in enumerate(category_recs):
                    priority = priority_icons[min(i, 2)]
                    rec_table.add_row(priority, rec)

                console.print(rec_table)

    # Spectacular footer with next steps and quality insights
    console.print("\n" + "="*80)

    # Quality assessment summary
    if results.overall_score >= 95:
        quality_summary = "🌟 [bold bright_green]OUTSTANDING QUALITY[/bold bright_green] 🌟\n[dim]This service exemplifies best practices and is production-ready.[/dim]"
        next_steps = "🎯 [green]Maintain excellence and share knowledge with the team.[/green]"
    elif results.overall_score >= 85:
        quality_summary = "✅ [bold green]HIGH QUALITY ACHIEVED[/bold green] ✅\n[dim]Service meets production standards with room for minor polish.[/dim]"
        next_steps = "💡 [green]Focus on preventive maintenance and continuous improvement.[/green]"
    elif results.overall_score >= 75:
        quality_summary = "⚠️ [bold yellow]GOOD WITH OPPORTUNITIES[/bold yellow] ⚠️\n[dim]Solid foundation exists but targeted improvements will yield benefits.[/dim]"
        next_steps = "📈 [yellow]Address high-priority recommendations to reach excellence.[/yellow]"
    elif results.overall_score >= 65:
        quality_summary = "🟡 [bold yellow]NEEDS ATTENTION[/bold yellow] 🟡\n[dim]Quality issues present that impact maintainability and reliability.[/dim]"
        next_steps = "🚨 [yellow]Prioritize critical issues and architectural improvements.[/yellow]"
    else:
        quality_summary = "🚨 [bold bright_red]CRITICAL QUALITY ISSUES[/bold bright_red] 🚨\n[dim]Immediate action required to ensure service stability and security.[/dim]"
        next_steps = "🔴 [red]Stop feature development and focus on quality remediation.[/red]"

    # Create beautiful footer with timing and metadata
    audit_duration = results.metadata.get('audit_duration_seconds', 0)
    profile_used = results.metadata.get('profile_used', 'standard')

    footer_content = f"""
{quality_summary}

🎯 [bold cyan]Next Steps:[/bold cyan]
{next_steps}

📊 [bold blue]Audit Details:[/bold blue]
[dim]• Profile: {profile_used.title()}[/dim]
[dim]• Duration: {audit_duration:.2f} seconds[/dim]
[dim]• Dimensions: {len(results.dimensions)} analyzed[/dim]
[dim]• Rules: {len([r for r in results.recommendations if r])} applied[/dim]

💡 [bold magenta]Remember:[/bold magenta] [dim]Quality is not an accident, it's a habit.[/dim]
"""

    footer_panel = Panel(
        footer_content.strip(),
        title="[bold]🎯 Quality Assessment Complete[/bold]",
        border_style="cyan" if results.overall_score >= 80 else "yellow" if results.overall_score >= 70 else "red",
        padding=(1, 2)
    )

    console.print(footer_panel)
    console.print()  # Add final spacing

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
        'C': 'yellow',
        'C+': 'yellow',
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

    # Detailed Issues (only shown in verbose mode)
    print(f"DEBUG: verbose={verbose}, has_detailed_issues={hasattr(results, 'detailed_issues')}, issues_count={len(getattr(results, 'detailed_issues', []))}")
    print(f"DEBUG: detailed_issues content: {getattr(results, 'detailed_issues', [])}")
    if verbose and hasattr(results, 'detailed_issues') and results.detailed_issues:
        console.print(f"\n[bold blue]🔍 Detailed Issues Found ({len(results.detailed_issues)})[/bold blue]")

        # Group issues by type
        issues_by_type = {}
        for issue in results.detailed_issues:
            issue_type = issue.get('issue_type', 'unknown')
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)

        for issue_type, issues in issues_by_type.items():
            console.print(f"\n[bold cyan]{issue_type.upper()}:[/bold cyan]")
            for issue in issues[:10]:  # Limit to first 10 per type
                severity_color = {
                    'critical': 'red',
                    'warning': 'yellow',
                    'info': 'blue'
                }.get(issue.get('severity', 'warning'), 'yellow')

                location = ""
                if issue.get('file_path'):
                    location += f"📁 {Path(issue['file_path']).name}"
                if issue.get('line_number'):
                    location += f" 📍 Line {issue['line_number']}"
                if issue.get('line_block'):
                    location += f" ({issue['line_block']})"

                console.print(f"  [{severity_color}]• {issue.get('description', 'No description')}[/{severity_color}]")
                if location:
                    console.print(f"    [dim]{location}[/dim]")

            if len(issues) > 10:
                console.print(f"    [dim]... and {len(issues) - 10} more[/dim]")

    # Metadata
    console.print(f"\n[dim]Profile:[/] {results.metadata.get('profile_used', 'unknown')}")
    console.print(f"[dim]Audit Time:[/] {results.metadata.get('audit_time_seconds', 0):.1f}s")
    if verbose:
        console.print(f"[dim]Detailed Issues:[/] {len(getattr(results, 'detailed_issues', []))}")


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


def _handle_resources_command(args):
    """Handle the resources command to display system optimization info."""
    try:
        from infrastructure.resource_optimizer import get_resource_optimizer

        resource_optimizer = get_resource_optimizer()

        # Get service path if specified
        service_path = None
        if getattr(args, 'service', None):
            try:
                from infrastructure.file_system.service_discovery_service import ServiceDiscoveryService
                discovery_service = ServiceDiscoveryService()
                services = discovery_service.discover_services()
                service_info = next((s for s in services if s.name == args.service), None)
                if service_info:
                    service_path = service_info.path
                else:
                    print(f"❌ Service '{args.service}' not found")
                    return
            except Exception as discovery_error:
                logger.warning(f"Service discovery failed: {discovery_error}")
                # Try to construct path manually
                from pathlib import Path
                potential_path = Path("services") / args.service
                if potential_path.exists():
                    service_path = potential_path
                    logger.info(f"Using manually constructed path: {service_path}")
                else:
                    print(f"❌ Service '{args.service}' not found")
                    return

        # Get optimization settings
        full_audit = getattr(args, 'full', False)
        try:
            optimization_settings = resource_optimizer.get_optimal_settings(service_path, full_audit)
        except Exception as service_error:
            logger.warning(f"Service-specific optimization failed: {service_error}")
            # Fall back to general optimization
            optimization_settings = resource_optimizer.get_optimal_settings(None, full_audit)

        # Display results
        if HAS_RICH:
            console = Console()
            console.print("\n[bold blue]🎯 System Resource Optimization Analysis[/bold blue]\n")

            # System Resources
            sys_info = optimization_settings['system_info']
            console.print("[bold cyan]System Resources:[/bold cyan]")
            console.print(f"  🖥️  CPU Cores: {sys_info['cpu']['physical_cores']} physical, {sys_info['cpu']['logical_cores']} logical")
            console.print(f"  🧠 Memory: {sys_info['memory']['available_gb']:.1f}GB available / {sys_info['memory']['total_gb']:.1f}GB total")
            console.print(f"  💾 Disk: {sys_info['disk']['free_gb']:.1f}GB free / {sys_info['disk']['total_gb']:.1f}GB total")
            console.print(f"  📊 System Load: {sys_info['system_load']:.2f}")

            # Optimization Profile
            profile = optimization_settings['optimization_profile']
            console.print(f"\n[bold green]Optimization Profile:[/bold green]")
            console.print(f"  ⚡ Parallel Workers: {profile['parallel_workers']}")
            console.print(f"  📦 Batch Size: {profile['batch_size']}")
            console.print(f"  💾 Max Files in Memory: {profile['max_files_in_memory']}")
            console.print(f"  ⚖️  Load Factor: {profile['load_factor']:.2f}")

            # Workload Analysis (if available)
            if optimization_settings.get('workload_analysis'):
                workload = optimization_settings['workload_analysis']
                console.print(f"\n[bold yellow]Workload Analysis:[/bold yellow]")
                console.print(f"  📁 Files: {workload['file_count']}")
                console.print(f"  📊 Total Size: {workload['total_size_mb']:.1f}MB")
                console.print(f"  📏 Avg File Size: {workload['avg_file_size_kb']:.1f}KB")

                size_dist = workload['size_distribution']
                if size_dist:
                    console.print("  📈 File Size Distribution:")
                    for category, count in size_dist.items():
                        console.print(f"    {category.capitalize()}: {count} files")

            # Recommendations
            recommendations = optimization_settings.get('recommendations', [])
            if recommendations:
                console.print(f"\n[bold magenta]💡 Recommendations:[/bold magenta]")
                for rec in recommendations:
                    console.print(f"  • {rec}")

        else:
            # Plain text output
            print("🎯 System Resource Optimization Analysis")
            print("=" * 50)

            sys_info = optimization_settings['system_info']
            print(f"CPU Cores: {sys_info['cpu']['physical_cores']} physical, {sys_info['cpu']['logical_cores']} logical")
            print(f"Memory: {sys_info['memory']['available_gb']:.1f}GB available / {sys_info['memory']['total_gb']:.1f}GB total")
            print(f"Disk: {sys_info['disk']['free_gb']:.1f}GB free / {sys_info['disk']['total_gb']:.1f}GB total")
            print(f"System Load: {sys_info['system_load']:.2f}")

            profile = optimization_settings['optimization_profile']
            print(f"\nOptimization Profile:")
            print(f"  Parallel Workers: {profile['parallel_workers']}")
            print(f"  Batch Size: {profile['batch_size']}")
            print(f"  Max Files in Memory: {profile['max_files_in_memory']}")
            print(f"  Load Factor: {profile['load_factor']:.2f}")

            recommendations = optimization_settings.get('recommendations', [])
            if recommendations:
                print(f"\nRecommendations:")
                for rec in recommendations:
                    print(f"  • {rec}")

    except Exception as e:
        logger.error(f"Failed to display resource information: {e}")
        print(f"❌ Failed to analyze system resources: {e}")


def _handle_report_command(args):
    """Handle the report command to display audit reports from JSON files."""
    try:
        service_name = args.service
        profile_name = getattr(args, 'profile', 'strict')
        output_format = getattr(args, 'output', 'rich')
        verbose = getattr(args, 'verbose', False)
        
        # Construct the report file path
        report_file = Path("audit-results") / profile_name / f"audit_{service_name}.json"
        
        if not report_file.exists():
            print(f"❌ Report file not found: {report_file}")
            print(f"Available profiles: relaxed, standard, strict, ci_fast, ci_comprehensive")
            print(f"Available services: check audit-results/{profile_name}/ directory")
            return
        
        # Load and parse the report
        with open(report_file, 'r') as f:
            report_data = json.load(f)
        
        print(f"📊 Audit Report for {service_name} ({profile_name} profile)")
        print("=" * 60)
        print(f"Overall Score: {report_data.get('overall_score', 'N/A'):.1f}")
        print(f"Grade: {report_data.get('grade', 'N/A')}")
        print(f"Analysis Timestamp: {report_data.get('analysis_timestamp', 'N/A')}")
        print()
        
        # Display dimensions
        dimensions = report_data.get('dimensions', {})
        if dimensions:
            print("📈 Dimension Scores:")
            for dim, score in dimensions.items():
                print(f"  {dim.replace('_', ' ' ).title()}: {score:.1f}")
            print()
        
        # Display recommendations
        recommendations = report_data.get('recommendations', [])
        if recommendations:
            print("💡 Key Recommendations:")
            for rec in recommendations[:10]:  # Show first 10 recommendations
                print(f"  • {rec}")
            if len(recommendations) > 10:
                print(f"  ... and {len(recommendations) - 10} more")
            print()
        
        # Display critical issues
        critical_issues = report_data.get('critical_issues', [])
        if critical_issues:
            print("🚨 Critical Issues:")
            for issue in critical_issues[:5]:  # Show first 5 critical issues
                print(f"  • {issue}")
            if len(critical_issues) > 5:
                print(f"  ... and {len(critical_issues) - 5} more critical issues")
            print()
        
        # Display detailed issues if verbose
        if verbose:
            detailed_issues = report_data.get('detailed_issues', [])
            if detailed_issues:
                print("🔍 Detailed Issues:")
                for issue in detailed_issues[:10]:  # Show first 10 detailed issues
                    severity = issue.get('severity', 'unknown')
                    severity_icon = {'critical': '🚨', 'warning': '⚠️', 'info': 'ℹ️'}.get(severity, '❓')
                    print(f"  {severity_icon} {issue.get('description', 'No description')}")
                    if issue.get('file_path'):
                        print(f"      📁 {issue['file_path']}")
                    if issue.get('line_number'):
                        print(f"      📍 Line {issue['line_number']}")
                if len(detailed_issues) > 10:
                    print(f"  ... and {len(detailed_issues) - 10} more detailed issues")
                print()
        
        # Show metadata
        metadata = report_data.get('metadata', {})
        if metadata:
            service_info = metadata.get('service_info', {})
            if service_info:
                print("ℹ️  Service Information:")
                print(f"  Name: {service_info.get('name', 'N/A')}")
                print(f"  Path: {service_info.get('path', 'N/A')}")
                print(f"  Type: {service_info.get('type', 'N/A')}")
                print()
        
        if output_format == 'json':
            print(json.dumps(report_data, indent=2, default=str))
        elif output_format == 'summary':
            _display_report_summary(report_data)
            
    except Exception as e:
        logger.error(f"Failed to display report: {e}")
        print(f"❌ Failed to load audit report: {e}")


def _display_report_summary(report_data):
    """Display a concise summary of the audit report."""
    print("📋 AUDIT SUMMARY")
    print("-" * 30)
    print(f"Service: {report_data.get('service_name', 'Unknown')}")
    print(f"Score: {report_data.get('overall_score', 0):.1f}/100")
    print(f"Grade: {report_data.get('grade', 'F')}")
    print(f"Critical Issues: {len(report_data.get('critical_issues', []))}")
    print(f"Detailed Issues: {len(report_data.get('detailed_issues', []))}")
    print(f"Estimated Effort: {report_data.get('estimated_effort_days', 'Unknown')} days")

if __name__ == "__main__":
    main()
