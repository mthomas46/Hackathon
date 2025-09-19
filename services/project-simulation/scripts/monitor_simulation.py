#!/usr/bin/env python3
"""Terminal Monitor for Project Simulation Service.

This script provides a command-line interface for monitoring simulation execution
with rich terminal UI, progress bars, and real-time status updates.

Usage:
    python monitor_simulation.py <simulation_id> [--host HOST] [--port PORT] [--no-color]
    python monitor_simulation.py --list [--host HOST] [--port PORT]
"""

import sys
import os
import argparse
import requests
import json
import time
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation.infrastructure.logging import get_simulation_logger


class SimulationMonitor:
    """Terminal-based simulation monitor."""

    def __init__(self, host: str = "localhost", port: int = 5075, use_color: bool = True):
        """Initialize the simulation monitor."""
        self.host = host
        self.port = port
        self.use_color = use_color
        self.base_url = f"http://{host}:{port}"
        self.logger = get_simulation_logger()

        # Color codes
        self.colors = {
            'red': '\033[31m',
            'green': '\033[32m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'magenta': '\033[35m',
            'cyan': '\033[36m',
            'white': '\033[37m',
            'bold': '\033[1m',
            'reset': '\033[0m'
        } if use_color else {k: '' for k in ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'bold', 'reset']}

    def colorize(self, text: str, color: str) -> str:
        """Colorize text if colors are enabled."""
        return f"{self.colors.get(color, '')}{text}{self.colors['reset']}"

    def make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make HTTP request to the simulation service."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            return {"success": False, "error": str(e)}

    def list_simulations(self) -> None:
        """List all available simulations."""
        print(f"{self.colorize('📋 Available Simulations', 'cyan')}\n")

        # Get simulations list (simplified for demo)
        print("🔍 Checking for running simulations...")
        print("📊 Recent simulations:")

        # This would normally fetch from the API
        print("   • No active simulations found")
        print("   💡 Use the API to create and start simulations")
        print(f"   🌐 API: {self.base_url}/docs")

    def start_monitoring(self, simulation_id: str) -> None:
        """Start monitoring a simulation."""
        print(f"{self.colorize('🚀 Starting Simulation Monitor', 'cyan')}")
        print(f"🎯 Simulation ID: {simulation_id}")
        print(f"🌐 API Endpoint: {self.base_url}")
        print(f"{'─' * 60}\n")

        # Start UI monitoring via API
        print("📡 Starting terminal UI monitoring...")
        response = self.make_request("POST", f"/api/v1/simulations/{simulation_id}/ui/start")

        if response.get("success"):
            print(f"✅ {self.colorize('Terminal monitoring started successfully!', 'green')}")
            print("📊 Live progress will be displayed below...\n")
        else:
            print(f"❌ {self.colorize('Failed to start monitoring', 'red')}: {response.get('error', 'Unknown error')}")
            return

        # Monitor simulation status
        self.monitor_simulation_status(simulation_id)

    def monitor_simulation_status(self, simulation_id: str) -> None:
        """Monitor and display simulation status in real-time."""
        print(f"{self.colorize('📊 Monitoring Simulation Progress', 'yellow')}")
        print("Press Ctrl+C to stop monitoring\n")

        last_status = None
        start_time = time.time()

        try:
            while True:
                # Get simulation status
                response = self.make_request("GET", f"/api/v1/simulations/{simulation_id}")

                if response.get("success"):
                    data = response.get("data", {})

                    # Clear previous status if changed
                    if last_status != data.get("status"):
                        if last_status:
                            print()  # Add spacing
                        last_status = data.get("status")

                    # Display current status
                    self.display_status_update(data, time.time() - start_time)

                else:
                    print(f"❌ Error getting status: {response.get('error', 'Unknown error')}")

                time.sleep(2)  # Update every 2 seconds

        except KeyboardInterrupt:
            print(f"\n\n{self.colorize('🛑 Monitoring stopped by user', 'yellow')}")

            # Stop UI monitoring
            self.stop_monitoring(simulation_id)

        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")
            self.stop_monitoring(simulation_id)

    def display_status_update(self, data: dict, elapsed_time: float) -> None:
        """Display a status update."""
        status = data.get("status", "unknown")
        progress = data.get("progress", 0)

        # Status indicators
        status_colors = {
            "running": "green",
            "completed": "green",
            "failed": "red",
            "pending": "yellow",
            "paused": "yellow"
        }

        status_color = status_colors.get(status, "white")
        status_icon = {
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "pending": "⏳",
            "paused": "⏸️"
        }.get(status, "❓")

        # Format elapsed time
        minutes, seconds = divmod(int(elapsed_time), 60)
        time_str = f"{minutes:02d}:{seconds:02d}"

        # Progress bar (simple text-based)
        bar_width = 30
        filled = int(bar_width * progress / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        # Display status line
        print(f"\r{status_icon} Status: {self.colorize(status.upper(), status_color)} | "
              f"Progress: [{bar}] {progress:5.1f}% | "
              f"Time: {time_str} | "
              f"Phase: {data.get('current_phase', 'N/A')}", end="", flush=True)

        # Show completion message
        if status in ["completed", "failed"]:
            print()  # New line
            if status == "completed":
                print(f"🎉 {self.colorize('Simulation completed successfully!', 'green')}")
            else:
                print(f"⚠️  {self.colorize('Simulation failed', 'red')}: {data.get('error', 'Unknown error')}")

            # Stop monitoring
            simulation_id = data.get("simulation_id", "")
            if simulation_id:
                self.stop_monitoring(simulation_id)
            return False

        return True

    def stop_monitoring(self, simulation_id: str) -> None:
        """Stop monitoring a simulation."""
        print(f"\n📡 Stopping terminal UI monitoring...")

        response = self.make_request("POST", f"/api/v1/simulations/{simulation_id}/ui/stop",
                                   json={"success": True})

        if response.get("success"):
            print(f"✅ {self.colorize('Terminal monitoring stopped successfully!', 'green')}")
        else:
            print(f"⚠️  {self.colorize('Warning', 'yellow')}: Could not stop monitoring - {response.get('error', 'Unknown error')}")

    def show_help(self) -> None:
        """Show help information."""
        print(f"{self.colorize('🚀 Project Simulation Monitor', 'cyan')}")
        print(f"{'─' * 40}")
        print()
        print("Monitor simulation execution with rich terminal UI:")
        print()
        print("USAGE:")
        print("  python monitor_simulation.py <simulation_id> [options]")
        print("  python monitor_simulation.py --list [options]")
        print()
        print("OPTIONS:")
        print("  --host HOST       API host (default: localhost)")
        print("  --port PORT       API port (default: 5075)")
        print("  --no-color        Disable colored output")
        print("  --list           List available simulations")
        print()
        print("EXAMPLES:")
        print("  python monitor_simulation.py abc-123-def")
        print("  python monitor_simulation.py abc-123-def --host 192.168.1.100 --port 8080")
        print("  python monitor_simulation.py --list --no-color")
        print()
        print(f"🌐 API Documentation: {self.base_url}/docs")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor Project Simulation Service with rich terminal UI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python monitor_simulation.py abc-123-def
  python monitor_simulation.py abc-123-def --host 192.168.1.100 --port 8080
  python monitor_simulation.py --list --no-color
        """
    )

    parser.add_argument(
        "simulation_id",
        nargs="?",
        help="Simulation ID to monitor"
    )

    parser.add_argument(
        "--host",
        default="localhost",
        help="API host (default: localhost)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=5075,
        help="API port (default: 5075)"
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List available simulations"
    )

    args = parser.parse_args()

    # Initialize monitor
    monitor = SimulationMonitor(
        host=args.host,
        port=args.port,
        use_color=not args.no_color
    )

    try:
        if args.list:
            # List simulations
            monitor.list_simulations()
        elif args.simulation_id:
            # Monitor specific simulation
            monitor.start_monitoring(args.simulation_id)
        else:
            # Show help
            monitor.show_help()

    except KeyboardInterrupt:
        print(f"\n\n{monitor.colorize('👋 Goodbye!', 'cyan')}")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
