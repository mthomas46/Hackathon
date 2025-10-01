#!/usr/bin/env python3
"""
Port Conflict Resolution System

Analyzes and resolves port conflicts across all Docker Compose files
with detailed reporting and automated conflict resolution suggestions.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class ConflictSeverity(Enum):
    """Severity levels for port conflicts."""
    CRITICAL = "critical"  # Ports < 1024 or system ports
    HIGH = "high"         # Application ports with multiple conflicts
    MEDIUM = "medium"     # Application ports with few conflicts
    LOW = "low"          # Minor conflicts


@dataclass
class PortConflictResolution:
    """Represents a port conflict resolution suggestion."""
    port: int
    conflicting_services: List[str]
    severity: ConflictSeverity
    suggested_resolutions: List[str]
    affected_files: List[str]
    resolution_priority: int  # 1 = highest priority


@dataclass
class ConflictAnalysis:
    """Analysis results for port conflicts."""
    total_conflicts: int = 0
    critical_conflicts: int = 0
    conflicts_by_port: Dict[int, PortConflictResolution] = field(default_factory=dict)
    conflicts_by_file: Dict[str, List[int]] = field(default_factory=dict)
    resolution_suggestions: List[str] = field(default_factory=list)


class PortConflictResolver:
    """
    Analyzes and resolves port conflicts across all Docker Compose files.

    Provides detailed conflict analysis and resolution suggestions.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent

        # Port ranges and their purposes
        self.port_ranges = {
            "infrastructure": (1, 1023),      # System/infrastructure ports
            "application": (8000, 8999),     # Main application ports
            "health": (9000, 9999),          # Health check ports
            "metrics": (10000, 10999),       # Metrics ports
            "debug": (11000, 11999),         # Debug ports
            "database": (12000, 12999),      # Database ports
            "queue": (13000, 13999),         # Message queue ports
            "monitoring": (14000, 14999),    # Monitoring ports
            "load_balancer": (15000, 15999)  # Load balancer ports
        }

        # Reserved ports that should never be changed
        self.reserved_ports = {
            22: "SSH",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            443: "HTTPS",
            3306: "MySQL",
            5432: "PostgreSQL",
            6379: "Redis",
            27017: "MongoDB"
        }

    def analyze_conflicts(self) -> ConflictAnalysis:
        """
        Analyze all port conflicts across Docker Compose files.

        Returns:
            Comprehensive conflict analysis with resolution suggestions
        """
        print("🔍 Analyzing Port Conflicts Across All Files")
        print("=" * 50)

        # Get conflicts from port registry
        sys.path.insert(0, str(self.project_root / "scripts" / "hardening"))
        from port_registry import PortRegistry

        registry = PortRegistry()
        raw_conflicts = registry.check_conflicts()

        analysis = ConflictAnalysis()

        # Process each conflict
        for conflict in raw_conflicts:
            port = conflict.port
            services = conflict.conflicting_services

            # Extract file information
            affected_files = []
            for service_info in services:
                if '(' in service_info and ')' in service_info:
                    file_path = service_info.split('(')[1].split(')')[0]
                    file_name = Path(file_path).name
                    affected_files.append(file_name)

            # Determine severity
            severity = self._calculate_severity(port, len(services))

            # Generate resolution suggestions
            suggestions = self._generate_resolution_suggestions(port, services, affected_files)

            # Create resolution object
            resolution = PortConflictResolution(
                port=port,
                conflicting_services=services,
                severity=severity,
                suggested_resolutions=suggestions,
                affected_files=affected_files,
                resolution_priority=self._calculate_priority(port, severity, len(services))
            )

            analysis.conflicts_by_port[port] = resolution
            analysis.total_conflicts += 1

            if severity == ConflictSeverity.CRITICAL:
                analysis.critical_conflicts += 1

            # Track conflicts by file
            for file_name in affected_files:
                if file_name not in analysis.conflicts_by_file:
                    analysis.conflicts_by_file[file_name] = []
                if port not in analysis.conflicts_by_file[file_name]:
                    analysis.conflicts_by_file[file_name].append(port)

        # Generate overall suggestions
        analysis.resolution_suggestions = self._generate_overall_suggestions(analysis)

        return analysis

    def _calculate_severity(self, port: int, conflict_count: int) -> ConflictSeverity:
        """Calculate the severity of a port conflict."""
        # Critical: System ports or heavily conflicted
        if port < 1024 or port in self.reserved_ports:
            return ConflictSeverity.CRITICAL

        # High: Multiple services conflicting
        if conflict_count > 3:
            return ConflictSeverity.HIGH

        # Medium: 2-3 services conflicting
        if conflict_count > 1:
            return ConflictSeverity.MEDIUM

        return ConflictSeverity.LOW

    def _calculate_priority(self, port: int, severity: ConflictSeverity, conflict_count: int) -> int:
        """Calculate resolution priority (1 = highest)."""
        priority = 10  # Base priority

        if severity == ConflictSeverity.CRITICAL:
            priority -= 5
        elif severity == ConflictSeverity.HIGH:
            priority -= 3
        elif severity == ConflictSeverity.MEDIUM:
            priority -= 1

        # More conflicts = higher priority
        priority -= min(conflict_count, 3)

        return max(1, priority)

    def _generate_resolution_suggestions(self, port: int, services: List[str], files: List[str]) -> List[str]:
        """Generate specific resolution suggestions for a conflict."""
        suggestions = []

        if port in self.reserved_ports:
            service_name = self.reserved_ports[port]
            suggestions.append(f"🚫 RESERVED PORT: Port {port} is reserved for {service_name}")
            suggestions.append("   • Remove all non-infrastructure services from this port")
            suggestions.append("   • Infrastructure services should coordinate port usage")
            return suggestions

        if port < 1024:
            suggestions.append(f"🔴 SYSTEM PORT: Port {port} is in system range (< 1024)")
            suggestions.append("   • Move services to application port range (8000-8999)")
            suggestions.append("   • Use port registry to assign new ports")

        # Suggest alternative ports based on service types
        alternative_ports = self._suggest_alternative_ports(services)

        if alternative_ports:
            suggestions.append("💡 Suggested alternative port assignments:")
            for service_info, alt_port in alternative_ports.items():
                service_name = service_info.split('(')[0].strip() if '(' in service_info else service_info
                suggestions.append(f"   • {service_name}: Change to port {alt_port}")

        return suggestions

    def _suggest_alternative_ports(self, services: List[str]) -> Dict[str, int]:
        """Suggest alternative ports for conflicting services."""
        alternatives = {}

        # Group services by type hints from names
        service_types = {}
        for service_info in services:
            service_name = service_info.split('(')[0].strip().lower()

            if any(word in service_name for word in ['api', 'backend', 'service', 'gateway']):
                service_types[service_info] = 'application'
            elif any(word in service_name for word in ['redis', 'postgres', 'database', 'db']):
                service_types[service_info] = 'infrastructure'
            elif any(word in service_name for word in ['monitor', 'metrics', 'prometheus']):
                service_types[service_info] = 'monitoring'
            elif any(word in service_name for word in ['health', 'check']):
                service_types[service_info] = 'health'
            else:
                service_types[service_info] = 'application'

        # Assign ports based on type
        port_assignments = {
            'infrastructure': [6379, 5432, 27017],  # Allow some infrastructure overlap
            'application': list(range(8000, 8100)),  # 8000-8099 range
            'monitoring': list(range(9090, 9100)),   # 9090-9099 range
            'health': list(range(9000, 9010))        # 9000-9009 range
        }

        for service_info, service_type in service_types.items():
            available_ports = port_assignments.get(service_type, [])
            if available_ports:
                # Find first unused port in the range
                for alt_port in available_ports:
                    # Check if this port is already assigned to another service in this conflict
                    if alt_port not in [p for s, p in alternatives.items()]:
                        alternatives[service_info] = alt_port
                        break

        return alternatives

    def _generate_overall_suggestions(self, analysis: ConflictAnalysis) -> List[str]:
        """Generate overall resolution suggestions."""
        suggestions = []

        if analysis.critical_conflicts > 0:
            suggestions.append(f"🚨 CRITICAL: {analysis.critical_conflicts} critical conflicts must be resolved immediately")
            suggestions.append("   • System ports (< 1024) cannot be shared")
            suggestions.append("   • Reserved ports must be used only by designated services")

        # Group conflicts by priority
        high_priority = [p for p, r in analysis.conflicts_by_port.items() if r.resolution_priority <= 3]
        medium_priority = [p for p, r in analysis.conflicts_by_port.items() if 3 < r.resolution_priority <= 6]
        low_priority = [p for p, r in analysis.conflicts_by_port.items() if r.resolution_priority > 6]

        if high_priority:
            suggestions.append(f"🔥 HIGH PRIORITY: Resolve {len(high_priority)} conflicts first")
            suggestions.append(f"   Ports: {', '.join(map(str, high_priority))}")

        if medium_priority:
            suggestions.append(f"⚠️  MEDIUM PRIORITY: Address {len(medium_priority)} conflicts next")
            suggestions.append(f"   Ports: {', '.join(map(str, medium_priority))}")

        if low_priority:
            suggestions.append(f"ℹ️  LOW PRIORITY: Consider fixing {len(low_priority)} remaining conflicts")
            suggestions.append(f"   Ports: {', '.join(map(str, low_priority))}")

        suggestions.extend([
            "",
            "🛠️  RESOLUTION STEPS:",
            "1. Review port registry assignments",
            "2. Update Docker Compose port mappings",
            "3. Test service accessibility after changes",
            "4. Update documentation and service discovery",
            "5. Run validation to confirm conflicts resolved"
        ])

        return suggestions

    def generate_conflict_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive port conflict report.

        Returns:
            Detailed conflict analysis and resolution guide
        """
        print("📊 Generating Port Conflict Resolution Report")
        print("=" * 50)

        analysis = self.analyze_conflicts()

        report = {
            'summary': {
                'total_conflicts': analysis.total_conflicts,
                'critical_conflicts': analysis.critical_conflicts,
                'affected_files': len(analysis.conflicts_by_file),
                'resolution_suggestions': len(analysis.resolution_suggestions)
            },
            'conflicts_by_severity': {},
            'conflicts_by_file': {},
            'detailed_conflicts': {},
            'resolution_guide': analysis.resolution_suggestions
        }

        # Group conflicts by severity
        severity_groups = {}
        for port, resolution in analysis.conflicts_by_port.items():
            severity = resolution.severity.value
            if severity not in severity_groups:
                severity_groups[severity] = []
            severity_groups[severity].append(port)

        report['conflicts_by_severity'] = severity_groups

        # Conflicts by file
        report['conflicts_by_file'] = {
            file: len(ports) for file, ports in analysis.conflicts_by_file.items()
        }

        # Detailed conflict information
        for port, resolution in sorted(analysis.conflicts_by_port.items(),
                                      key=lambda x: x[1].resolution_priority):
            report['detailed_conflicts'][str(port)] = {
                'severity': resolution.severity.value,
                'priority': resolution.resolution_priority,
                'service_count': len(resolution.conflicting_services),
                'affected_files': resolution.affected_files,
                'resolutions': resolution.suggested_resolutions
            }

        # Print summary
        print(f"📋 Conflict Summary:")
        print(f"   Total conflicts: {analysis.total_conflicts}")
        print(f"   Critical conflicts: {analysis.critical_conflicts}")
        print(f"   Files affected: {len(analysis.conflicts_by_file)}")

        if severity_groups:
            print(f"\n🔍 Conflicts by Severity:")
            for severity, ports in severity_groups.items():
                print(f"   • {severity.title()}: {len(ports)} conflicts")

        print(f"\n💡 Resolution Guide:")
        for suggestion in analysis.resolution_suggestions[:5]:
            print(f"   • {suggestion}")

        if len(analysis.resolution_suggestions) > 5:
            print(f"   • ... and {len(analysis.resolution_suggestions) - 5} more steps")

        return report

    def apply_resolutions(self, resolutions: Dict[int, int]) -> Dict[str, Any]:
        """
        Apply port conflict resolutions by updating Docker Compose files.

        Args:
            resolutions: Dict mapping old_port -> new_port

        Returns:
            Results of applied resolutions
        """
        results = {
            'files_modified': 0,
            'ports_changed': 0,
            'errors': []
        }

        print(f"🔧 Applying {len(resolutions)} Port Resolutions")
        print("=" * 45)

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

                modified = False

                # Update port mappings
                for service_name, service_config in config['services'].items():
                    if 'ports' in service_config:
                        original_ports = service_config['ports']
                        updated_ports = []

                        for port_mapping in original_ports:
                            if isinstance(port_mapping, str):
                                # Parse "host_port:container_port" format
                                parts = port_mapping.split(':')
                                if len(parts) >= 2:
                                    try:
                                        host_port = int(parts[0])
                                        if host_port in resolutions:
                                            new_port = resolutions[host_port]
                                            new_mapping = port_mapping.replace(str(host_port), str(new_port), 1)
                                            updated_ports.append(new_mapping)
                                            print(f"✅ Updated {service_name} in {compose_file.name}: {host_port} → {new_port}")
                                            results['ports_changed'] += 1
                                            modified = True
                                        else:
                                            updated_ports.append(port_mapping)
                                    except ValueError:
                                        updated_ports.append(port_mapping)
                                else:
                                    updated_ports.append(port_mapping)
                            else:
                                updated_ports.append(port_mapping)

                        if modified:
                            service_config['ports'] = updated_ports

                if modified:
                    with open(compose_file, 'w') as f:
                        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                    results['files_modified'] += 1

            except Exception as e:
                error_msg = f"Error processing {compose_file}: {e}"
                print(f"❌ {error_msg}")
                results['errors'].append(error_msg)

        print(f"\n📊 Resolution Results:")
        print(f"   Files modified: {results['files_modified']}")
        print(f"   Ports changed: {results['ports_changed']}")
        print(f"   Errors: {len(results['errors'])}")

        return results


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Port Conflict Resolution System")
    parser.add_argument('--action', '-a', choices=['analyze', 'report', 'resolve'],
                       default='report', help='Action to perform')
    parser.add_argument('--resolve-port', '-p', action='append',
                       help='Port resolution in format old_port:new_port (can be used multiple times)')
    parser.add_argument('--auto-resolve', action='store_true',
                       help='Automatically resolve conflicts using suggested ports')

    args = parser.parse_args()

    resolver = PortConflictResolver()

    try:
        if args.action == 'analyze':
            analysis = resolver.analyze_conflicts()
            print(f"Analysis complete: {analysis.total_conflicts} conflicts found")

        elif args.action == 'report':
            report = resolver.generate_conflict_report()

        elif args.action == 'resolve':
            if args.resolve_port:
                # Manual resolution
                resolutions = {}
                for resolution_str in args.resolve_port:
                    if ':' in resolution_str:
                        old_port, new_port = resolution_str.split(':', 1)
                        try:
                            resolutions[int(old_port)] = int(new_port)
                        except ValueError:
                            print(f"❌ Invalid resolution format: {resolution_str}")
                            continue

                if resolutions:
                    results = resolver.apply_resolutions(resolutions)
                    print(f"✅ Applied {len(resolutions)} port resolutions")

            elif args.auto_resolve:
                # Auto-resolve using suggestions
                analysis = resolver.analyze_conflicts()

                # Generate automatic resolutions for non-critical conflicts
                auto_resolutions = {}
                for port, resolution in analysis.conflicts_by_port.items():
                    if resolution.severity != ConflictSeverity.CRITICAL and resolution.suggested_resolutions:
                        # Look for suggested port in resolution suggestions
                        for suggestion in resolution.suggested_resolutions:
                            if "Change to port" in suggestion:
                                # Extract suggested port
                                import re
                                match = re.search(r'Change to port (\d+)', suggestion)
                                if match:
                                    suggested_port = int(match.group(1))
                                    auto_resolutions[port] = suggested_port
                                    break

                if auto_resolutions:
                    print(f"🔄 Auto-resolving {len(auto_resolutions)} non-critical conflicts...")
                    results = resolver.apply_resolutions(auto_resolutions)
                    print(f"✅ Auto-resolved {len(auto_resolutions)} conflicts")
                else:
                    print("ℹ️  No auto-resolvable conflicts found")

            else:
                print("❌ Specify --resolve-port or --auto-resolve to apply resolutions")
                sys.exit(1)

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
