#!/usr/bin/env python3
"""Event Management CLI for Project Simulation Service.

This script provides command-line tools for managing simulation events,
including querying, replaying, statistics, and cleanup operations.

Usage:
    python manage_events.py stats [--simulation-id ID]
    python manage_events.py query <simulation_id> [--event-types TYPES] [--limit N]
    python manage_events.py replay <simulation_id> [--speed 2.0] [--event-types TYPES]
    python manage_events.py timeline <simulation_id>
    python manage_events.py cleanup --days 30
    python manage_events.py --help
"""

import sys
import os
import argparse
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation.infrastructure.logging import get_simulation_logger


class EventManager:
    """CLI tool for managing simulation events."""

    def __init__(self, host: str = "localhost", port: int = 5075):
        """Initialize the event manager."""
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.logger = get_simulation_logger()

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

    def show_statistics(self, simulation_id: Optional[str] = None) -> None:
        """Show event statistics."""
        print("📊 Event Statistics")
        print("=" * 50)

        # Get statistics
        params = {}
        if simulation_id:
            params["simulation_id"] = simulation_id

        response = self.make_request("GET", "/api/v1/events/statistics", params=params)

        if response.get("success"):
            stats = response.get("data", {})

            print(f"Total Events: {stats.get('total_events', 0)}")
            print(f"Simulations: {len(stats.get('simulations', []))}")
            print(f"Unique Tags: {len(stats.get('tags', []))}")

            if stats.get("time_range", {}).get("start"):
                print(f"Time Range: {stats['time_range']['start']} to {stats['time_range']['end']}")

            print("\nEvent Types:")
            for event_type, count in stats.get("event_types", {}).items():
                print(f"  {event_type}: {count}")

            if simulation_id:
                print(f"\nFiltered by simulation: {simulation_id}")
        else:
            print(f"❌ Failed to get statistics: {response.get('error', 'Unknown error')}")

    def query_events(self, simulation_id: str, event_types: Optional[str] = None,
                    limit: int = 20, offset: int = 0) -> None:
        """Query events for a simulation."""
        print(f"🔍 Querying events for simulation: {simulation_id}")
        print("=" * 60)

        params = {
            "limit": limit,
            "offset": offset
        }
        if event_types:
            params["event_types"] = event_types

        response = self.make_request("GET", f"/api/v1/simulations/{simulation_id}/events", params=params)

        if response.get("success"):
            data = response.get("data", {})
            events = data.get("events", [])

            print(f"Found {len(events)} events (showing {data.get('limit', limit)} of {data.get('total_count', len(events))})")

            if events:
                print("\nRecent Events:")
                print("-" * 100)
                for event in events[:10]:  # Show first 10
                    timestamp = event.get("timestamp", "")
                    event_type = event.get("event_type", "")
                    event_id = event.get("event_id", "")[:8]

                    print("12")

                if len(events) > 10:
                    print(f"\n... and {len(events) - 10} more events")
        else:
            print(f"❌ Failed to query events: {response.get('error', 'Unknown error')}")

    def show_timeline(self, simulation_id: str) -> None:
        """Show timeline of events for a simulation."""
        print(f"⏰ Event Timeline for simulation: {simulation_id}")
        print("=" * 60)

        response = self.make_request("GET", f"/api/v1/simulations/{simulation_id}/timeline")

        if response.get("success"):
            data = response.get("data", {})
            timeline = data.get("timeline", [])

            print(f"Total events: {len(timeline)}")

            if timeline:
                print("\nTimeline:")
                print("-" * 100)

                for event in timeline[-20:]:  # Show last 20 events
                    timestamp = event.get("timestamp", "")
                    event_type = event.get("event_type", "")
                    description = event.get("description", "")

                    print("20")

                if len(timeline) > 20:
                    print(f"\n... and {len(timeline) - 20} earlier events")
        else:
            print(f"❌ Failed to get timeline: {response.get('error', 'Unknown error')}")

    def replay_events(self, simulation_id: str, speed_multiplier: float = 1.0,
                     event_types: Optional[str] = None, max_events: Optional[int] = None) -> None:
        """Replay events for a simulation."""
        print(f"🎬 Starting event replay for simulation: {simulation_id}")
        print("=" * 60)
        print(f"Speed multiplier: {speed_multiplier}x")
        if event_types:
            print(f"Event types: {event_types}")
        if max_events:
            print(f"Max events: {max_events}")
        print()

        # Start replay
        replay_data = {
            "speed_multiplier": speed_multiplier,
            "include_system_events": False
        }
        if event_types:
            replay_data["event_types"] = event_types.split(",")
        if max_events:
            replay_data["max_events"] = max_events

        response = self.make_request("POST", f"/api/v1/simulations/{simulation_id}/events/replay",
                                   json=replay_data)

        if response.get("success"):
            data = response.get("data", {})
            replay_id = data.get("replay_id")

            print(f"✅ Replay started successfully!")
            print(f"Replay ID: {replay_id}")
            print("Monitor the replay status or use WebSocket for real-time updates."
        else:
            print(f"❌ Failed to start replay: {response.get('error', 'Unknown error')}")

    def cleanup_events(self, days_old: int = 30) -> None:
        """Clean up old events."""
        print(f"🧹 Cleaning up events older than {days_old} days")
        print("=" * 50)

        response = self.make_request("POST", "/api/v1/events/cleanup",
                                   json={"days_old": days_old})

        if response.get("success"):
            data = response.get("data", {})
            cleaned = data.get("events_cleaned", 0)
            print(f"✅ Successfully cleaned up {cleaned} old events")
        else:
            print(f"❌ Failed to cleanup events: {response.get('error', 'Unknown error')}")

    def show_help(self) -> None:
        """Show help information."""
        print("🎯 Project Simulation Event Manager")
        print("=" * 40)
        print()
        print("Manage simulation events with advanced querying, replay, and analytics:")
        print()
        print("COMMANDS:")
        print("  stats [--simulation-id ID]        Show event statistics")
        print("  query <simulation_id> [options]   Query events with filters")
        print("  timeline <simulation_id>          Show event timeline")
        print("  replay <simulation_id> [options]  Replay simulation events")
        print("  cleanup --days N                 Clean up old events")
        print()
        print("OPTIONS:")
        print("  --simulation-id ID    Filter by simulation ID")
        print("  --event-types TYPES   Filter by event types (comma-separated)")
        print("  --limit N            Limit number of results (default: 20)")
        print("  --offset N           Offset for pagination (default: 0)")
        print("  --speed N.N          Replay speed multiplier (default: 1.0)")
        print("  --max-events N       Maximum events to replay")
        print("  --days N             Days old for cleanup (default: 30)")
        print("  --host HOST          API host (default: localhost)")
        print("  --port PORT          API port (default: 5075)")
        print()
        print("EXAMPLES:")
        print("  python manage_events.py stats")
        print("  python manage_events.py stats --simulation-id abc-123")
        print("  python manage_events.py query abc-123 --event-types simulation_started,document_generated")
        print("  python manage_events.py timeline abc-123")
        print("  python manage_events.py replay abc-123 --speed 2.0 --max-events 100")
        print("  python manage_events.py cleanup --days 7")
        print()
        print(f"🌐 API Documentation: {self.base_url}/docs")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage Project Simulation Service events",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_events.py stats --simulation-id abc-123
  python manage_events.py query abc-123 --event-types simulation_started,document_generated --limit 50
  python manage_events.py timeline abc-123
  python manage_events.py replay abc-123 --speed 2.0 --max-events 100
  python manage_events.py cleanup --days 30
        """
    )

    parser.add_argument(
        "command",
        choices=["stats", "query", "timeline", "replay", "cleanup"],
        help="Command to execute"
    )

    parser.add_argument(
        "simulation_id",
        nargs="?",
        help="Simulation ID for commands that require it"
    )

    parser.add_argument(
        "--simulation-id",
        help="Simulation ID for filtering"
    )

    parser.add_argument(
        "--event-types",
        help="Comma-separated list of event types to filter"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Limit number of results"
    )

    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Offset for pagination"
    )

    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Replay speed multiplier"
    )

    parser.add_argument(
        "--max-events",
        type=int,
        help="Maximum events to replay"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Days old for cleanup"
    )

    parser.add_argument(
        "--host",
        default="localhost",
        help="API host"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=5075,
        help="API port"
    )

    args = parser.parse_args()

    # Initialize event manager
    manager = EventManager(host=args.host, port=args.port)

    try:
        # Execute command
        if args.command == "stats":
            simulation_id = args.simulation_id or getattr(args, 'simulation_id', None)
            manager.show_statistics(simulation_id)
        elif args.command == "query":
            if not args.simulation_id:
                print("❌ Simulation ID required for query command")
                sys.exit(1)
            manager.query_events(args.simulation_id, args.event_types, args.limit, args.offset)
        elif args.command == "timeline":
            if not args.simulation_id:
                print("❌ Simulation ID required for timeline command")
                sys.exit(1)
            manager.show_timeline(args.simulation_id)
        elif args.command == "replay":
            if not args.simulation_id:
                print("❌ Simulation ID required for replay command")
                sys.exit(1)
            manager.replay_events(args.simulation_id, args.speed, args.event_types, args.max_events)
        elif args.command == "cleanup":
            manager.cleanup_events(args.days)
        else:
            manager.show_help()

    except KeyboardInterrupt:
        print(f"\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
