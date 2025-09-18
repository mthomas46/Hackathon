"""CLI Integration - Simulation Commands for Ecosystem CLI.

This module provides CLI commands for the project-simulation service,
integrating with the existing ecosystem CLI framework.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import asyncio
import argparse
from datetime import datetime

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.di_container import get_simulation_container
from simulation.infrastructure.logging import get_simulation_logger
from simulation.presentation.websockets.simulation_websocket import (
    notify_simulation_progress,
    notify_ecosystem_status
)


class SimulationCLI:
    """CLI interface for project-simulation service."""

    def __init__(self):
        """Initialize simulation CLI."""
        self.logger = get_simulation_logger()
        self.container = get_simulation_container()
        self.application_service = self.container.simulation_application_service

    async def create_simulation(self, args: argparse.Namespace) -> None:
        """Create a new simulation."""
        try:
            # Build simulation configuration
            simulation_config = {
                "name": args.name,
                "description": getattr(args, 'description', ''),
                "type": getattr(args, 'type', 'web_application'),
                "team_size": getattr(args, 'team_size', 5),
                "complexity": getattr(args, 'complexity', 'medium'),
                "duration_weeks": getattr(args, 'duration_weeks', 8)
            }

            # Add optional team members if provided
            if hasattr(args, 'team_members') and args.team_members:
                simulation_config["team_members"] = args.team_members

            self.logger.info(
                "Creating simulation via CLI",
                simulation_name=args.name,
                project_type=getattr(args, 'type', 'web_application')
            )

            result = await self.application_service.create_simulation(simulation_config)

            if result["success"]:
                simulation_id = result["simulation_id"]
                print(f"✅ Simulation created successfully!")
                print(f"📋 Simulation ID: {simulation_id}")
                print(f"🏷️  Name: {args.name}")
                print(f"📅 Created: {result.get('created_at', 'Unknown')}")

                # Offer to start the simulation immediately
                if getattr(args, 'start_immediately', False):
                    print(f"\n🚀 Starting simulation execution...")
                    await self.execute_simulation_by_id(simulation_id, args)
                else:
                    print(f"\n💡 Use 'simulation execute {simulation_id}' to start execution")
                    print(f"💡 Use 'simulation status {simulation_id}' to check progress")
            else:
                print(f"❌ Failed to create simulation: {result.get('message', 'Unknown error')}")
                sys.exit(1)

        except Exception as e:
            self.logger.error("CLI simulation creation failed", error=str(e))
            print(f"❌ Error creating simulation: {str(e)}")
            sys.exit(1)

    async def execute_simulation(self, args: argparse.Namespace) -> None:
        """Execute a simulation."""
        simulation_id = args.simulation_id

        try:
            self.logger.info(
                "Executing simulation via CLI",
                simulation_id=simulation_id
            )

            result = await self.application_service.execute_simulation(simulation_id)

            if result["success"]:
                print(f"✅ Simulation execution started!")
                print(f"📋 Simulation ID: {simulation_id}")
                print(f"⚡ Status: Running")

                # Show progress monitoring options
                print(f"\n📊 Monitor progress:")
                print(f"   simulation status {simulation_id}")
                print(f"   simulation results {simulation_id}")
                print(f"   simulation logs {simulation_id}")

                # WebSocket monitoring hint
                print(f"\n🌐 Real-time updates available via WebSocket:")
                print(f"   ws://localhost:5075/ws/simulations/{simulation_id}")

            else:
                print(f"❌ Failed to execute simulation: {result.get('message', 'Unknown error')}")
                sys.exit(1)

        except Exception as e:
            self.logger.error("CLI simulation execution failed", error=str(e), simulation_id=simulation_id)
            print(f"❌ Error executing simulation: {str(e)}")
            sys.exit(1)

    async def execute_simulation_by_id(self, simulation_id: str, args: Optional[argparse.Namespace] = None) -> None:
        """Execute simulation by ID (internal method)."""
        # Create a minimal args object if not provided
        if args is None:
            args = argparse.Namespace()
            args.simulation_id = simulation_id

        await self.execute_simulation(args)

    async def get_simulation_status(self, args: argparse.Namespace) -> None:
        """Get simulation status."""
        simulation_id = args.simulation_id

        try:
            self.logger.debug(
                "Getting simulation status via CLI",
                simulation_id=simulation_id
            )

            result = await self.application_service.get_simulation_status(simulation_id)

            if result["success"]:
                print(f"📊 Simulation Status: {simulation_id}")
                print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print(f"🏷️  Name: {result.get('project_name', 'Unknown')}")
                print(f"📊 Status: {result.get('status', 'Unknown')}")
                print(f"📈 Progress: {result.get('progress', 0)}%")
                print(f"🎯 Current Phase: {result.get('current_phase', 'Unknown')}")
                print(f"⏰ Created: {result.get('created_at', 'Unknown')}")
                print(f"🔄 Updated: {result.get('last_updated', 'Unknown')}")

                if result.get("started_at"):
                    print(f"▶️  Started: {result.get('started_at')}")

                if result.get("completed_at"):
                    print(f"✅ Completed: {result.get('completed_at')}")

                if result.get("error"):
                    print(f"❌ Error: {result.get('error')}")

            else:
                print(f"❌ Simulation not found: {simulation_id}")
                print(f"💡 Use 'simulation list' to see available simulations")
                sys.exit(1)

        except Exception as e:
            self.logger.error("CLI simulation status check failed", error=str(e), simulation_id=simulation_id)
            print(f"❌ Error getting simulation status: {str(e)}")
            sys.exit(1)

    async def get_simulation_results(self, args: argparse.Namespace) -> None:
        """Get simulation results."""
        simulation_id = args.simulation_id

        try:
            self.logger.debug(
                "Getting simulation results via CLI",
                simulation_id=simulation_id
            )

            result = await self.application_service.get_simulation_results(simulation_id)

            if result["success"]:
                print(f"📋 Simulation Results: {simulation_id}")
                print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

                # Display results in a structured format
                results_data = result.get("results", {})

                if results_data:
                    print(f"📊 Documents Generated: {results_data.get('total_documents', 0)}")
                    print(f"🔄 Workflows Executed: {results_data.get('total_workflows', 0)}")
                    print(f"⏱️  Execution Time: {results_data.get('execution_time_seconds', 0):.2f}s")
                    print(f"🎯 Success Rate: {results_data.get('success_rate', 0):.1f}%")
                    print(f"🔍 Inconsistencies Found: {results_data.get('inconsistencies_detected', 0)}")
                    print(f"💡 Insights Generated: {len(results_data.get('insights', []))}")

                    # Show insights if available
                    insights = results_data.get("insights", [])
                    if insights:
                        print(f"\n💡 Key Insights:")
                        for i, insight in enumerate(insights[:5], 1):  # Show top 5
                            print(f"   {i}. {insight}")
                        if len(insights) > 5:
                            print(f"   ... and {len(insights) - 5} more")
                else:
                    print("⏳ Results not yet available - simulation may still be running")
                    print("💡 Use 'simulation status {simulation_id}' to check progress")

            else:
                print(f"❌ Failed to get simulation results: {result.get('error', 'Unknown error')}")
                sys.exit(1)

        except Exception as e:
            self.logger.error("CLI simulation results retrieval failed", error=str(e), simulation_id=simulation_id)
            print(f"❌ Error getting simulation results: {str(e)}")
            sys.exit(1)

    async def list_simulations(self, args: argparse.Namespace) -> None:
        """List all simulations."""
        try:
            status_filter = getattr(args, 'status', None)
            limit = getattr(args, 'limit', 50)

            self.logger.debug(
                "Listing simulations via CLI",
                status_filter=status_filter,
                limit=limit
            )

            result = await self.application_service.list_simulations(status_filter, limit)

            if result["success"]:
                simulations = result.get("simulations", [])
                total = result.get("total", 0)

                print(f"📋 Simulations ({total} total)")
                print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

                if not simulations:
                    print("📭 No simulations found")
                    if status_filter:
                        print(f"💡 Try removing the status filter or use 'simulation list --all'")
                    return

                # Display simulations in a table format
                print(f"{'ID':<36} {'Name':<20} {'Status':<12} {'Progress':<10} {'Created':<19}")
                print("-" * 100)

                for sim in simulations:
                    sim_id = sim.get("id", "")[:35]  # Truncate long IDs
                    name = sim.get("name", "")[:19]
                    status = sim.get("status", "")[:11]
                    progress = f"{sim.get('progress', 0):>3.0f}%"
                    created = sim.get("created_at", "")[:19] if sim.get("created_at") else ""

                    print(f"{sim_id:<36} {name:<20} {status:<12} {progress:<10} {created:<19}")

                print(f"\n📊 Showing {len(simulations)} of {total} simulations")

                if status_filter:
                    print(f"🔍 Filtered by status: {status_filter}")

                # Show command hints
                print(f"\n💡 Commands:")
                print(f"   simulation status <id>    - Check specific simulation")
                print(f"   simulation execute <id>   - Start simulation")
                print(f"   simulation results <id>   - View results")

            else:
                print(f"❌ Failed to list simulations: {result.get('error', 'Unknown error')}")
                sys.exit(1)

        except Exception as e:
            self.logger.error("CLI simulation listing failed", error=str(e))
            print(f"❌ Error listing simulations: {str(e)}")
            sys.exit(1)

    async def cancel_simulation(self, args: argparse.Namespace) -> None:
        """Cancel a simulation."""
        simulation_id = args.simulation_id

        try:
            self.logger.info(
                "Cancelling simulation via CLI",
                simulation_id=simulation_id
            )

            result = await self.application_service.cancel_simulation(simulation_id)

            if result["success"]:
                print(f"✅ Simulation cancelled successfully!")
                print(f"📋 Simulation ID: {simulation_id}")
                print(f"🛑 Status: Cancelled")
                print(f"📅 Cancelled at: {result.get('cancelled_at', datetime.now().isoformat())}")
            else:
                print(f"❌ Failed to cancel simulation: {result.get('error', 'Unknown error')}")
                sys.exit(1)

        except Exception as e:
            self.logger.error("CLI simulation cancellation failed", error=str(e), simulation_id=simulation_id)
            print(f"❌ Error cancelling simulation: {str(e)}")
            sys.exit(1)

    async def get_health_status(self, args: argparse.Namespace) -> None:
        """Get system health status."""
        try:
            self.logger.debug("Getting health status via CLI")

            result = await self.application_service.get_health_status()

            if result["success"]:
                health = result.get("health", {})

                print("🏥 System Health Status")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

                # Overall health
                service_health = health.get("service_health", {})
                print(f"📊 Overall Status: {'✅ Healthy' if service_health.get('status') == 'healthy' else '❌ Unhealthy'}")
                print(f"🏷️  Service: {service_health.get('service', 'Unknown')}")
                print(f"🏷️  Version: {service_health.get('version', 'Unknown')}")
                print(f"⏰ Uptime: {service_health.get('uptime_seconds', 0):.0f} seconds")

                # Simulation-specific health
                sim_specific = health.get("simulation_specific", {})
                if sim_specific:
                    print(f"\n🎯 Simulation Health:")
                    print(f"   Domain Models: {'✅ Loaded' if sim_specific.get('domain_models_loaded') else '❌ Not loaded'}")
                    print(f"   Infrastructure: {'✅ Ready' if sim_specific.get('infrastructure_ready') else '❌ Not ready'}")
                    print(f"   Ecosystem: {'✅ Connected' if sim_specific.get('ecosystem_integration') else '❌ Disconnected'}")

                # Ecosystem services
                critical_services = sim_specific.get("critical_services", {})
                if critical_services:
                    print(f"\n🔗 Critical Ecosystem Services:")
                    for service_name, service_info in critical_services.items():
                        status = service_info.get("status", "unknown")
                        status_icon = "✅" if status == "healthy" else "❌" if status == "unhealthy" else "⚠️"
                        response_time = service_info.get("response_time_ms", "N/A")
                        print(f"   {service_name}: {status_icon} {status} ({response_time}ms)")

                print(f"\n💡 Health check completed at: {datetime.now().isoformat()}")

            else:
                print(f"❌ Failed to get health status: {result.get('error', 'Unknown error')}")
                sys.exit(1)

        except Exception as e:
            self.logger.error("CLI health check failed", error=str(e))
            print(f"❌ Error getting health status: {str(e)}")
            sys.exit(1)

    async def watch_simulation(self, args: argparse.Namespace) -> None:
        """Watch simulation progress in real-time."""
        simulation_id = args.simulation_id

        try:
            self.logger.info(
                "Starting simulation watch via CLI",
                simulation_id=simulation_id
            )

            print(f"👀 Watching simulation: {simulation_id}")
            print("Press Ctrl+C to stop watching")
            print("-" * 50)

            last_status = None

            while True:
                try:
                    # Get current status
                    status_args = argparse.Namespace()
                    status_args.simulation_id = simulation_id

                    # Temporarily redirect stdout to capture status output
                    import io
                    from contextlib import redirect_stdout

                    status_output = io.StringIO()
                    with redirect_stdout(status_output):
                        await self.get_simulation_status(status_args)

                    current_output = status_output.getvalue()

                    # Only print if status changed
                    if current_output != last_status:
                        # Clear screen and print new status
                        print("\033[2J\033[H", end="")  # Clear screen
                        print(current_output)
                        print(f"\n🔄 Last updated: {datetime.now().strftime('%H:%M:%S')}")
                        print("💡 Press Ctrl+C to stop watching")
                        last_status = current_output

                    # Wait before next check
                    await asyncio.sleep(2)

                except KeyboardInterrupt:
                    print(f"\n👋 Stopped watching simulation: {simulation_id}")
                    break
                except Exception as e:
                    print(f"❌ Error during watch: {str(e)}")
                    await asyncio.sleep(5)  # Wait longer on error

        except Exception as e:
            self.logger.error("CLI simulation watch failed", error=str(e), simulation_id=simulation_id)
            print(f"❌ Error watching simulation: {str(e)}")
            sys.exit(1)


# Global CLI instance
_simulation_cli: Optional[SimulationCLI] = None


def get_simulation_cli() -> SimulationCLI:
    """Get the global simulation CLI instance."""
    global _simulation_cli
    if _simulation_cli is None:
        _simulation_cli = SimulationCLI()
    return _simulation_cli


def create_simulation_parser(subparsers) -> None:
    """Create argument parser for simulation commands."""
    simulation_parser = subparsers.add_parser(
        'simulation',
        help='Manage project simulations',
        description='Create, execute, and monitor project simulations'
    )

    simulation_subparsers = simulation_parser.add_subparsers(
        dest='simulation_command',
        help='Simulation commands'
    )

    # Create simulation command
    create_parser = simulation_subparsers.add_parser(
        'create',
        help='Create a new simulation'
    )
    create_parser.add_argument('name', help='Simulation name')
    create_parser.add_argument('--description', help='Simulation description')
    create_parser.add_argument('--type', choices=['web_application', 'api_service', 'mobile_application', 'data_science', 'devops_tool'],
                              default='web_application', help='Project type')
    create_parser.add_argument('--team-size', type=int, default=5, help='Team size')
    create_parser.add_argument('--complexity', choices=['simple', 'medium', 'complex'],
                              default='medium', help='Project complexity')
    create_parser.add_argument('--duration-weeks', type=int, default=8, help='Project duration in weeks')
    create_parser.add_argument('--start-immediately', action='store_true',
                              help='Start simulation immediately after creation')

    # Execute simulation command
    execute_parser = simulation_subparsers.add_parser(
        'execute',
        help='Execute a simulation'
    )
    execute_parser.add_argument('simulation_id', help='Simulation ID to execute')

    # Status command
    status_parser = simulation_subparsers.add_parser(
        'status',
        help='Get simulation status'
    )
    status_parser.add_argument('simulation_id', help='Simulation ID')

    # Results command
    results_parser = simulation_subparsers.add_parser(
        'results',
        help='Get simulation results'
    )
    results_parser.add_argument('simulation_id', help='Simulation ID')

    # List command
    list_parser = simulation_subparsers.add_parser(
        'list',
        help='List simulations'
    )
    list_parser.add_argument('--status', help='Filter by status')
    list_parser.add_argument('--limit', type=int, default=50, help='Maximum number of results')

    # Cancel command
    cancel_parser = simulation_subparsers.add_parser(
        'cancel',
        help='Cancel a simulation'
    )
    cancel_parser.add_argument('simulation_id', help='Simulation ID to cancel')

    # Health command
    health_parser = simulation_subparsers.add_parser(
        'health',
        help='Get system health status'
    )

    # Watch command
    watch_parser = simulation_subparsers.add_parser(
        'watch',
        help='Watch simulation progress in real-time'
    )
    watch_parser.add_argument('simulation_id', help='Simulation ID to watch')


async def handle_simulation_command(args: argparse.Namespace) -> None:
    """Handle simulation CLI commands."""
    cli = get_simulation_cli()

    command = args.simulation_command

    if command == 'create':
        await cli.create_simulation(args)
    elif command == 'execute':
        await cli.execute_simulation(args)
    elif command == 'status':
        await cli.get_simulation_status(args)
    elif command == 'results':
        await cli.get_simulation_results(args)
    elif command == 'list':
        await cli.list_simulations(args)
    elif command == 'cancel':
        await cli.cancel_simulation(args)
    elif command == 'health':
        await cli.get_health_status(args)
    elif command == 'watch':
        await cli.watch_simulation(args)
    else:
        print(f"❌ Unknown simulation command: {command}")
        print("💡 Use 'simulation --help' to see available commands")
        sys.exit(1)


__all__ = [
    'SimulationCLI',
    'get_simulation_cli',
    'create_simulation_parser',
    'handle_simulation_command'
]
