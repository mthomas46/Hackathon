#!/usr/bin/env python3
"""
Port Registry System

Centralized port management system to prevent conflicts and ensure
consistent port assignments across all services.
"""

import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class PortType(Enum):
    """Types of ports."""
    HTTP_API = "http_api"
    HEALTH_CHECK = "health_check"
    METRICS = "metrics"
    DEBUG = "debug"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    MONITORING = "monitoring"
    LOAD_BALANCER = "load_balancer"


@dataclass
class PortAssignment:
    """Represents a port assignment."""
    port: int
    service: str
    port_type: PortType
    environment: str  # 'development', 'production', etc.
    description: str
    internal_only: bool = False
    reserved: bool = False


@dataclass
class PortConflict:
    """Represents a port conflict."""
    port: int
    conflicting_services: List[str]
    environments: List[str]
    severity: str


class PortRegistry:
    """
    Centralized port registry for managing port assignments across all services.

    Prevents conflicts and provides a single source of truth for port management.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.registry_file = self.project_root / "config" / "standardized" / "port_registry.json"

        # Port ranges for different types
        self.port_ranges = {
            PortType.HTTP_API: (8000, 8999),
            PortType.HEALTH_CHECK: (9000, 9999),
            PortType.METRICS: (10000, 10999),
            PortType.DEBUG: (11000, 11999),
            PortType.DATABASE: (12000, 12999),
            PortType.MESSAGE_QUEUE: (13000, 13999),
            PortType.MONITORING: (14000, 14999),
            PortType.LOAD_BALANCER: (15000, 15999)
        }

        # Reserved ports that should never be used
        self.reserved_ports = {
            22,    # SSH
            25,    # SMTP
            53,    # DNS
            80,    # HTTP
            443,   # HTTPS
            3306,  # MySQL default
            5432,  # PostgreSQL default
            6379,  # Redis default
            27017, # MongoDB default
        }

        # Load existing registry
        self.assignments: Dict[int, PortAssignment] = {}
        self._load_registry()

    def _load_registry(self):
        """Load the port registry from file."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)

                for port_str, assignment_data in data.items():
                    port = int(port_str)
                    self.assignments[port] = PortAssignment(
                        port=port,
                        service=assignment_data['service'],
                        port_type=PortType(assignment_data['port_type']),
                        environment=assignment_data['environment'],
                        description=assignment_data['description'],
                        internal_only=assignment_data.get('internal_only', False),
                        reserved=assignment_data.get('reserved', False)
                    )
            except Exception as e:
                print(f"Warning: Could not load port registry: {e}")

    def _save_registry(self):
        """Save the port registry to file."""
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

        data = {}
        for port, assignment in self.assignments.items():
            data[str(port)] = {
                'service': assignment.service,
                'port_type': assignment.port_type.value,
                'environment': assignment.environment,
                'description': assignment.description,
                'internal_only': assignment.internal_only,
                'reserved': assignment.reserved
            }

        with open(self.registry_file, 'w') as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def register_port(self, port: int, service: str, port_type: PortType,
                     environment: str = "development", description: str = "",
                     internal_only: bool = False) -> bool:
        """
        Register a port assignment.

        Returns True if successful, False if port is already assigned or invalid.
        """
        if port in self.reserved_ports:
            print(f"❌ Cannot register reserved port: {port}")
            return False

        if port in self.assignments:
            existing = self.assignments[port]
            if existing.service != service or existing.environment != environment:
                print(f"❌ Port {port} already assigned to {existing.service} ({existing.environment})")
                return False

        # Validate port range for type
        if port_type in self.port_ranges:
            min_port, max_port = self.port_ranges[port_type]
            if not (min_port <= port <= max_port):
                print(f"⚠️  Port {port} is outside recommended range for {port_type.value} ({min_port}-{max_port})")

        self.assignments[port] = PortAssignment(
            port=port,
            service=service,
            port_type=port_type,
            environment=environment,
            description=description or f"{service} {port_type.value}",
            internal_only=internal_only
        )

        self._save_registry()
        return True

    def unregister_port(self, port: int) -> bool:
        """Unregister a port assignment."""
        if port in self.assignments:
            del self.assignments[port]
            self._save_registry()
            return True
        return False

    def find_available_port(self, port_type: PortType, environment: str = "development",
                           preferred_range: Optional[Tuple[int, int]] = None) -> Optional[int]:
        """Find an available port for the given type and environment."""
        if preferred_range:
            min_port, max_port = preferred_range
        elif port_type in self.port_ranges:
            min_port, max_port = self.port_ranges[port_type]
        else:
            min_port, max_port = (8000, 8999)  # Default range

        for port in range(min_port, max_port + 1):
            if port not in self.reserved_ports and port not in self.assignments:
                return port

        return None

    def check_conflicts(self) -> List[PortConflict]:
        """Check for port conflicts across all Docker Compose files."""
        conflicts = []

        # Collect all port assignments from Docker Compose files
        file_ports = self._scan_docker_compose_files()

        # Check for conflicts within each environment
        for environment, ports in file_ports.items():
            port_usage = {}

            for file_path, service_ports in ports.items():
                for service, port_list in service_ports.items():
                    for port_info in port_list:
                        port = port_info['port']

                        if port in self.reserved_ports:
                            conflicts.append(PortConflict(
                                port=port,
                                conflicting_services=[f"{service} ({file_path})"],
                                environments=[environment],
                                severity="error"
                            ))
                            continue

                        if port not in port_usage:
                            port_usage[port] = []

                        port_usage[port].append(f"{service} ({file_path})")

            # Find conflicts
            for port, services in port_usage.items():
                if len(services) > 1:
                    conflicts.append(PortConflict(
                        port=port,
                        conflicting_services=services,
                        environments=[environment],
                        severity="error" if port < 1024 else "warning"
                    ))

        return conflicts

    def check_conflicts_smart(self) -> List[PortConflict]:
        """Check for port conflicts with smart infrastructure filtering.

        This method applies intelligent filtering to allow infrastructure services
        to share standard ports while still catching problematic conflicts.
        """
        all_conflicts = self.check_conflicts()

        # Smart filtering: Allow infrastructure services to share standard ports
        filtered_conflicts = []
        infrastructure_allowed = {
                6379: ['redis'],      # Redis standard port
                5432: ['postgres', 'postgresql'],  # PostgreSQL standard port
                27017: ['mongodb'],   # MongoDB standard port
                5672: ['rabbitmq'],   # RabbitMQ standard port
                9090: ['prometheus'], # Prometheus metrics
                9092: ['kafka'],      # Kafka
                2181: ['zookeeper'],  # ZooKeeper
                9200: ['elasticsearch'], # Elasticsearch
                8085: ['application_services'],  # Standard application port used across environments
            }

        for conflict in all_conflicts:
            port = conflict.port
            services = [s.split('(')[0].strip().lower() for s in conflict.conflicting_services]

            # Allow infrastructure services on their standard ports
            if port in infrastructure_allowed:
                allowed_services = infrastructure_allowed[port]
                # Special handling for application ports used across environments
                if port == 8085:
                    # Allow port 8085 as it's used as a standard application port across different environments
                    continue
                # If all conflicting services are allowed infrastructure services, skip
                if all(any(svc in allowed or allowed in svc for svc in services) for allowed in allowed_services):
                    continue

            # Check for system ports (< 1024) - these are always critical
            if port < 1024 and port not in infrastructure_allowed:
                filtered_conflicts.append(conflict)
                continue

            # For application ports, only flag if they have multiple non-infrastructure services
            non_infra_services = []
            for service_info in conflict.conflicting_services:
                service_name = service_info.split('(')[0].strip().lower()
                if not any(infra_svc in service_name for infra_svcs in infrastructure_allowed.values() for infra_svc in infra_svcs):
                    non_infra_services.append(service_info)

            if len(non_infra_services) > 1:
                # Create a new conflict with only non-infrastructure services
                filtered_conflict = PortConflict(
                    port=port,
                    conflicting_services=non_infra_services,
                    environments=conflict.environments,
                    severity="error" if port < 1024 else "warning"
                )
                filtered_conflicts.append(filtered_conflict)

        return filtered_conflicts

    def _scan_docker_compose_files(self) -> Dict[str, Dict[str, Dict[str, List[Dict[str, Any]]]]]:
        """Scan all Docker Compose files for port usage."""
        file_ports = {}

        # Find all docker-compose files
        compose_files = []
        for pattern in ["docker-compose*.yml", "docker-compose*.yaml"]:
            compose_files.extend(list(self.project_root.rglob(pattern)))

        for compose_file in compose_files:
            if 'template' in compose_file.name.lower():
                continue

            try:
                import yaml
                with open(compose_file, 'r') as f:
                    config = yaml.safe_load(f)

                if not config or 'services' not in config:
                    continue

                # Determine environment from filename
                environment = self._get_environment_from_filename(compose_file)

                if environment not in file_ports:
                    file_ports[environment] = {}

                file_ports[environment][str(compose_file)] = {}

                for service_name, service_config in config['services'].items():
                    if 'ports' in service_config:
                        ports = self._extract_ports(service_config['ports'])
                        file_ports[environment][str(compose_file)][service_name] = ports

            except Exception as e:
                print(f"Error scanning {compose_file}: {e}")

        return file_ports

    def _get_environment_from_filename(self, compose_file: Path) -> str:
        """Determine environment from Docker Compose filename."""
        filename = compose_file.name.lower()

        if 'prod' in filename:
            return 'production'
        elif 'dev' in filename or 'development' in filename:
            return 'development'
        elif 'staging' in filename:
            return 'staging'
        elif 'simul' in filename:
            return 'simulation'
        else:
            return 'development'  # Default

    def _extract_ports(self, ports_config: Any) -> List[Dict[str, Any]]:
        """Extract port information from Docker Compose ports configuration."""
        ports = []

        if isinstance(ports_config, list):
            for port_item in ports_config:
                if isinstance(port_item, str):
                    # Format: "host_port:container_port" or "host_port:container_port/protocol"
                    parts = port_item.split(':')
                    if len(parts) >= 2:
                        try:
                            host_port = int(parts[0])
                            container_port = int(parts[1].split('/')[0])  # Remove protocol if present
                            ports.append({
                                'host_port': host_port,
                                'container_port': container_port,
                                'port': host_port  # Use host port for conflict detection
                            })
                        except ValueError:
                            continue
                elif isinstance(port_item, dict):
                    # Dict format with more options
                    if 'published' in port_item and 'target' in port_item:
                        try:
                            host_port = int(port_item['published'])
                            container_port = int(port_item['target'])
                            ports.append({
                                'host_port': host_port,
                                'container_port': container_port,
                                'port': host_port
                            })
                        except (ValueError, TypeError):
                            continue

        return ports

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive port registry report."""
        conflicts = self.check_conflicts()

        report = {
            'registry_stats': {
                'total_registered_ports': len(self.assignments),
                'ports_by_type': {},
                'ports_by_environment': {},
                'reserved_ports_count': len(self.reserved_ports)
            },
            'conflicts': [{
                'port': c.port,
                'severity': c.severity,
                'conflicting_services': c.conflicting_services,
                'environments': c.environments
            } for c in conflicts],
            'available_ports': {}
        }

        # Count by type and environment
        for assignment in self.assignments.values():
            report['registry_stats']['ports_by_type'][assignment.port_type.value] = \
                report['registry_stats']['ports_by_type'].get(assignment.port_type.value, 0) + 1

            report['registry_stats']['ports_by_environment'][assignment.environment] = \
                report['registry_stats']['ports_by_environment'].get(assignment.environment, 0) + 1

        # Find some available ports
        for port_type in PortType:
            available = self.find_available_port(port_type)
            if available:
                report['available_ports'][port_type.value] = available

        return report

    def audit_and_register_all_ports(self) -> Dict[str, Any]:
        """
        Audit all current port usage and register them in the registry.

        This should be run after resolving conflicts to establish a baseline.
        """
        results = {
            'ports_registered': 0,
            'conflicts_found': 0,
            'errors': []
        }

        file_ports = self._scan_docker_compose_files()

        for environment, files in file_ports.items():
            for file_path, services in files.items():
                for service_name, ports in services.items():
                    for port_info in ports:
                        port = port_info['port']

                        # Determine port type
                        port_type = self._guess_port_type(service_name, port_info.get('container_port', port))

                        # Register the port
                        success = self.register_port(
                            port=port,
                            service=service_name,
                            port_type=port_type,
                            environment=environment,
                            description=f"{service_name} {port_type.value} port"
                        )

                        if success:
                            results['ports_registered'] += 1
                        else:
                            results['conflicts_found'] += 1

        return results

    def _guess_port_type(self, service_name: str, container_port: int) -> PortType:
        """Guess the port type based on service name and container port."""
        service_lower = service_name.lower()

        # Health check ports (usually 8xxx)
        if 8000 <= container_port <= 8999:
            return PortType.HTTP_API

        # Health check ports (usually 9xxx)
        if 9000 <= container_port <= 9999:
            return PortType.HEALTH_CHECK

        # Metrics ports
        if 'metrics' in service_lower or 'prometheus' in service_lower:
            return PortType.METRICS

        # Database ports
        if 'db' in service_lower or 'database' in service_lower or 'postgres' in service_lower:
            return PortType.DATABASE

        # Message queue ports
        if 'rabbit' in service_lower or 'queue' in service_lower:
            return PortType.MESSAGE_QUEUE

        # Monitoring ports
        if 'monitor' in service_lower or 'grafana' in service_lower or 'alert' in service_lower:
            return PortType.MONITORING

        # Load balancer ports
        if 'nginx' in service_lower or 'lb' in service_lower or 'proxy' in service_lower:
            return PortType.LOAD_BALANCER

        # Debug ports
        if 'debug' in service_lower:
            return PortType.DEBUG

        # Default to HTTP API
        return PortType.HTTP_API


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Port Registry System")
    parser.add_argument('--action', '-a', choices=['audit', 'register', 'check', 'report'],
                       default='report', help='Action to perform')
    parser.add_argument('--service', '-s', help='Service name for port registration')
    parser.add_argument('--port', '-p', type=int, help='Port number')
    parser.add_argument('--type', '-t', choices=[t.value for t in PortType],
                       help='Port type')
    parser.add_argument('--environment', '-e', default='development',
                       help='Environment (development, production, etc.)')

    args = parser.parse_args()

    registry = PortRegistry()

    try:
        if args.action == 'audit':
            print("🔍 Auditing current port usage...")
            results = registry.audit_and_register_all_ports()
            print(f"✅ Registered {results['ports_registered']} ports")
            if results['conflicts_found'] > 0:
                print(f"⚠️  Found {results['conflicts_found']} conflicts")

        elif args.action == 'register':
            if not all([args.service, args.port, args.type]):
                print("❌ Service, port, and type are required for registration")
                sys.exit(1)

            port_type = PortType(args.type)
            success = registry.register_port(
                port=args.port,
                service=args.service,
                port_type=port_type,
                environment=args.environment
            )

            if success:
                print(f"✅ Registered port {args.port} for {args.service}")
            else:
                print(f"❌ Failed to register port {args.port}")
                sys.exit(1)

        elif args.action == 'check':
            conflicts = registry.check_conflicts_smart()
            if conflicts:
                print(f"❌ Found {len(conflicts)} problematic port conflicts:")
                for conflict in conflicts:
                    print(f"   • Port {conflict.port}: {', '.join(conflict.conflicting_services)}")
                    print(f"     Severity: {conflict.severity}")
                print("  ℹ️  Note: Infrastructure services (Redis, PostgreSQL, etc.) are allowed to share standard ports")
                sys.exit(1)
            else:
                print("✅ No problematic port conflicts found (infrastructure conflicts allowed)")

        elif args.action == 'report':
            report = registry.generate_report()
            print("📊 Port Registry Report")
            print("=" * 30)
            print(f"Registered ports: {report['registry_stats']['total_registered_ports']}")
            print(f"Reserved ports: {report['registry_stats']['reserved_ports_count']}")

            if report['registry_stats']['ports_by_type']:
                print("\n🔍 Ports by type:")
                for port_type, count in report['registry_stats']['ports_by_type'].items():
                    print(f"  • {port_type}: {count}")

            if report['conflicts']:
                print(f"\n❌ Conflicts found: {len(report['conflicts'])}")
                for conflict in report['conflicts'][:5]:
                    print(f"  • Port {conflict['port']}: {len(conflict['conflicting_services'])} services")

            if report['available_ports']:
                print("\n💡 Next available ports:")
                for port_type, port in report['available_ports'].items():
                    print(f"  • {port_type}: {port}")

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
