#!/usr/bin/env python3
"""
Configuration Monitor CLI

Command-line interface for configuration monitoring and health checks.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.shared.infrastructure.config.config_monitor import get_config_monitor


def show_monitoring_dashboard():
    """Show the main monitoring dashboard."""
    print("📊 Configuration System Monitoring")
    print("=" * 50)

    monitor = get_config_monitor()

    # System Health
    print("System Health:")
    health = monitor.get_service_health_report()
    print(f"  Total Services: {health.get('total_services', 0)}")
    print(f"  Healthy Services: {health.get('healthy_services', 0)}")
    print(".1%")

    # Performance
    print("\nPerformance (last hour):")
    perf = monitor.get_performance_report()
    if 'error' not in perf:
        print(f"  Total Loads: {perf.get('total_loads', 0)}")
        print(".1%")
        print(".3f")
        print(f"  Pydantic Loads: {perf.get('pydantic_loads', 0)}")
        print(f"  Dataclass Loads: {perf.get('dataclass_loads', 0)}")
    else:
        print("  Performance: No recent data")

    # Recent Alerts
    print("\nRecent Alerts:")
    alerts = monitor.alerts[-3:] if hasattr(monitor, 'alerts') else []
    if alerts:
        for alert in alerts:
            severity = alert.get('severity', 'info')
            severity_icon = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}.get(severity, '❓')
            print(f"  {severity_icon} {alert.get('service', 'unknown')}: {alert.get('message', '')}")
    else:
        print("  Recent Alerts: None")

    print("\n✅ Monitoring check completed")


def show_health_status():
    """Show detailed health status for all services."""
    print("🏥 Configuration Health Check")
    print("=" * 40)

    monitor = get_config_monitor()
    health = monitor.get_service_health_report()

    print("Service Health Status:")
    for service_name, service_health in health.get('services', {}).items():
        status = service_health.get('status', 'unknown')
        status_icon = {
            'healthy': '✅',
            'warning': '⚠️',
            'error': '❌',
            'stale': '⏰'
        }.get(status, '❓')

        pydantic_icon = '🔧' if service_health.get('pydantic_enabled') else '📋'
        load_count = service_health.get('load_count', 0)
        avg_time = service_health.get('avg_load_time', 0)

        print("6")

    print("\n✅ Health check completed")


def show_service_details(service_name: str):
    """Show detailed information for a specific service."""
    print(f"🔍 Service Details: {service_name}")
    print("=" * 40)

    monitor = get_config_monitor()
    health = monitor.get_service_health_report(service_name)

    if 'error' in health:
        print(f"❌ Service not found: {service_name}")
        return

    print(f"Status: {health.get('status', 'unknown')}")
    print(f"Last Check: {health.get('last_check', 'never')}")
    print(".1f")
    print(f"Validation Issues: {health.get('validation_issues', 0)}")
    print(f"Load Count: {health.get('load_count', 0)}")
    print(".3f")
    print(f"Pydantic Enabled: {health.get('pydantic_enabled', False)}")

    print("\n✅ Service details displayed")


def export_metrics(format_type: str = 'json'):
    """Export metrics in specified format."""
    monitor = get_config_monitor()
    metrics_json = monitor.export_metrics(format_type)

    if format_type == 'json':
        print(metrics_json)
    else:
        print("JSON format:")
        print(metrics_json)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Configuration Monitor CLI")
    parser.add_argument('command', choices=['dashboard', 'health', 'service', 'export'],
                       help='Command to execute')
    parser.add_argument('--service', '-s', help='Service name for service command')
    parser.add_argument('--format', '-f', choices=['json', 'text'], default='json',
                       help='Export format')

    args = parser.parse_args()

    try:
        if args.command == 'dashboard':
            show_monitoring_dashboard()
        elif args.command == 'health':
            show_health_status()
        elif args.command == 'service':
            if not args.service:
                print("❌ Error: --service required for service command")
                sys.exit(1)
            show_service_details(args.service)
        elif args.command == 'export':
            export_metrics(args.format)

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
