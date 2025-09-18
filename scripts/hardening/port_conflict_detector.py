#!/usr/bin/env python3
"""
Automated Port Conflict Detection and Validation System
Comprehensive port management and conflict resolution
"""

import json
import yaml
import subprocess
import socket
import re
from typing import Dict, List, Any, Set, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PortInfo:
    """Port information container"""
    service_name: str
    external_port: int
    internal_port: int
    protocol: str = "tcp"
    interface: str = "0.0.0.0"

@dataclass
class PortConflict:
    """Port conflict information"""
    port: int
    conflicting_services: List[str]
    severity: str
    resolution_suggestion: str

class PortConflictDetector:
    """Comprehensive port conflict detection and validation system"""

    def __init__(self, docker_compose_file: str = "docker-compose.dev.yml",
                 port_registry_file: str = "config/standardized/port_registry.json"):
        self.docker_compose_file = Path(docker_compose_file)
        self.port_registry_file = Path(port_registry_file)
        self.ports_in_use: Set[int] = set()
        self.service_ports: Dict[str, PortInfo] = {}
        self.conflicts: List[PortConflict] = []
        self.warnings: List[str] = []
        self.recommendations: List[str] = []

    def load_docker_compose_config(self) -> Dict[str, Any]:
        """Load and parse docker-compose configuration"""
        try:
            with open(self.docker_compose_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load docker-compose file: {e}")
            return {}

    def load_port_registry(self) -> Dict[str, Any]:
        """Load port registry configuration"""
        try:
            with open(self.port_registry_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load port registry: {e}")
            return {}

    def extract_ports_from_compose(self, compose_config: Dict[str, Any]) -> Dict[str, PortInfo]:
        """Extract port mappings from docker-compose configuration"""
        service_ports = {}

        if 'services' not in compose_config:
            return service_ports

        for service_name, service_config in compose_config['services'].items():
            if 'ports' in service_config:
                ports = service_config['ports']
                if isinstance(ports, list):
                    for port_mapping in ports:
                        port_info = self._parse_port_mapping(port_mapping, service_name)
                        if port_info:
                            service_ports[service_name] = port_info
                            break  # Take first port mapping for simplicity

        return service_ports

    def _parse_port_mapping(self, port_mapping: str, service_name: str) -> Optional[PortInfo]:
        """Parse docker-compose port mapping string"""
        # Handle formats like "5087:5010", "5087:5010/tcp", "127.0.0.1:5087:5010"
        parts = port_mapping.split('/')

        if len(parts) > 1:
            protocol = parts[1]
        else:
            protocol = "tcp"

        port_part = parts[0]

        # Handle IP:external:internal format
        if port_part.count(':') == 2:
            _, external_port, internal_port = port_part.split(':')
        elif port_part.count(':') == 1:
            external_port, internal_port = port_part.split(':')
        else:
            # Single port (usually internal only)
            internal_port = port_part
            external_port = internal_port

        try:
            return PortInfo(
                service_name=service_name,
                external_port=int(external_port),
                internal_port=int(internal_port),
                protocol=protocol
            )
        except ValueError:
            logger.warning(f"Invalid port mapping for {service_name}: {port_mapping}")
            return None

    def check_system_ports_in_use(self) -> Set[int]:
        """Check which ports are currently in use on the system"""
        ports_in_use = set()

        try:
            # Use netstat to check listening ports
            result = subprocess.run(
                ['netstat', '-tlnp'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines[2:]:  # Skip header lines
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            local_address = parts[3]
                            if ':' in local_address:
                                try:
                                    port = int(local_address.split(':')[-1])
                                    ports_in_use.add(port)
                                except ValueError:
                                    continue

        except Exception as e:
            logger.warning(f"Failed to check system ports: {e}")

        return ports_in_use

    def check_docker_ports_in_use(self) -> Set[int]:
        """Check which ports are currently used by Docker containers"""
        ports_in_use = set()

        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Ports}}'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.strip():
                        # Extract port numbers from Docker port mappings
                        port_matches = re.findall(r':(\d+)->', line)
                        for match in port_matches:
                            try:
                                ports_in_use.add(int(match))
                            except ValueError:
                                continue

        except Exception as e:
            logger.warning(f"Failed to check Docker ports: {e}")

        return ports_in_use

    def detect_port_conflicts(self) -> List[PortConflict]:
        """Detect port conflicts between services and system"""
        conflicts = []

        # Check for conflicts between services
        port_to_services = {}
        for service_name, port_info in self.service_ports.items():
            if port_info.external_port not in port_to_services:
                port_to_services[port_info.external_port] = []
            port_to_services[port_info.external_port].append(service_name)

        # Find service-to-service conflicts
        for port, services in port_to_services.items():
            if len(services) > 1:
                conflicts.append(PortConflict(
                    port=port,
                    conflicting_services=services,
                    severity="high",
                    resolution_suggestion=f"Reassign one service to use a different external port. Suggested ports: {self._suggest_available_ports(port)}"
                ))

        # Check for conflicts with system ports
        system_ports = self.check_system_ports_in_use()
        docker_ports = self.check_docker_ports_in_use()

        for service_name, port_info in self.service_ports.items():
            if port_info.external_port in system_ports:
                conflicts.append(PortConflict(
                    port=port_info.external_port,
                    conflicting_services=[service_name, "system_process"],
                    severity="critical",
                    resolution_suggestion=f"Port {port_info.external_port} is in use by system. Use: {self._suggest_available_ports(port_info.external_port)}"
                ))
            elif port_info.external_port in docker_ports:
                conflicts.append(PortConflict(
                    port=port_info.external_port,
                    conflicting_services=[service_name, "docker_container"],
                    severity="high",
                    resolution_suggestion=f"Port {port_info.external_port} is used by another container. Use: {self._suggest_available_ports(port_info.external_port)}"
                ))

        return conflicts

    def _suggest_available_ports(self, conflicting_port: int) -> List[int]:
        """Suggest available ports around a conflicting port"""
        suggestions = []
        used_ports = self.check_system_ports_in_use() | self.check_docker_ports_in_use()

        # Add current service ports to used set
        for port_info in self.service_ports.values():
            used_ports.add(port_info.external_port)

        # Suggest ports in range ±10 of conflicting port
        for offset in range(-10, 11):
            if offset == 0:
                continue
            suggested_port = conflicting_port + offset
            if 1024 <= suggested_port <= 65535 and suggested_port not in used_ports:
                suggestions.append(suggested_port)
                if len(suggestions) >= 3:
                    break

        return suggestions[:3] if suggestions else [conflicting_port + 10, conflicting_port + 20, conflicting_port + 30]

    def validate_port_registry_consistency(self) -> List[str]:
        """Validate consistency between docker-compose and port registry"""
        warnings = []
        port_registry = self.load_port_registry()

        if not port_registry:
            warnings.append("Port registry not found - cannot validate consistency")
            return warnings

        for service_name, port_info in self.service_ports.items():
            if service_name in port_registry:
                registry_info = port_registry[service_name]
                registry_external = registry_info.get('external_port')
                registry_internal = registry_info.get('internal_port')

                if port_info.external_port != registry_external:
                    warnings.append(
                        f"{service_name}: External port mismatch - compose: {port_info.external_port}, "
                        f"registry: {registry_external}"
                    )

                if port_info.internal_port != registry_internal:
                    warnings.append(
                        f"{service_name}: Internal port mismatch - compose: {port_info.internal_port}, "
                        f"registry: {registry_internal}"
                    )

        return warnings

    def analyze_port_usage_efficiency(self) -> List[str]:
        """Analyze port usage for optimization opportunities"""
        recommendations = []

        # Find services using default ports
        default_ports = {80, 443, 8080, 3000, 5000, 8000, 9000}
        for service_name, port_info in self.service_ports.items():
            if port_info.external_port in default_ports:
                recommendations.append(
                    f"{service_name} uses default port {port_info.external_port}. "
                    "Consider using a service-specific port range (5xxx-8xxx)"
                )

        # Check for port ranges that could be optimized
        service_ports = sorted([p.external_port for p in self.service_ports.values()])
        if service_ports:
            port_range = max(service_ports) - min(service_ports)
            if port_range > 1000:
                recommendations.append(
                    f"Large port range detected ({min(service_ports)}-{max(service_ports)}). "
                    "Consider consolidating to a smaller range for easier management"
                )

        return recommendations

    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run complete port conflict detection and validation"""
        logger.info("Starting comprehensive port analysis...")

        # Load configurations
        compose_config = self.load_docker_compose_config()
        self.service_ports = self.extract_ports_from_compose(compose_config)

        # Detect conflicts
        self.conflicts = self.detect_port_conflicts()

        # Validate registry consistency
        self.warnings = self.validate_port_registry_consistency()

        # Analyze efficiency
        self.recommendations = self.analyze_port_usage_efficiency()

        # Generate report
        report = {
            "summary": {
                "total_services_analyzed": len(self.service_ports),
                "total_conflicts": len(self.conflicts),
                "critical_conflicts": len([c for c in self.conflicts if c.severity == "critical"]),
                "high_conflicts": len([c for c in self.conflicts if c.severity == "high"]),
                "warnings": len(self.warnings),
                "recommendations": len(self.recommendations)
            },
            "conflicts": [
                {
                    "port": c.port,
                    "severity": c.severity,
                    "services": c.conflicting_services,
                    "suggestion": c.resolution_suggestion
                }
                for c in self.conflicts
            ],
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "service_ports": {
                name: {
                    "external": info.external_port,
                    "internal": info.internal_port,
                    "protocol": info.protocol
                }
                for name, info in self.service_ports.items()
            }
        }

        return report

    def print_report(self, report: Dict[str, Any]):
        """Print comprehensive analysis report"""
        print("\n" + "="*80)
        print("🔍 PORT CONFLICT DETECTION AND VALIDATION REPORT")
        print("="*80)

        summary = report["summary"]
        print(f"\n📊 SUMMARY")
        print(f"  Services Analyzed: {summary['total_services_analyzed']}")
        print(f"  Port Conflicts: {summary['total_conflicts']}")
        print(f"  Critical Issues: {summary['critical_conflicts']}")
        print(f"  High Priority: {summary['high_conflicts']}")
        print(f"  Warnings: {summary['warnings']}")
        print(f"  Recommendations: {summary['recommendations']}")

        if report["conflicts"]:
            print(f"\n🚨 PORT CONFLICTS")
            for conflict in report["conflicts"]:
                severity_icon = "🔴" if conflict["severity"] == "critical" else "🟠"
                print(f"  {severity_icon} Port {conflict['port']}: {', '.join(conflict['services'])}")
                print(f"    💡 {conflict['suggestion']}")

        if report["warnings"]:
            print(f"\n⚠️  CONFIGURATION WARNINGS")
            for warning in report["warnings"]:
                print(f"  • {warning}")

        if report["recommendations"]:
            print(f"\n💡 OPTIMIZATION RECOMMENDATIONS")
            for rec in report["recommendations"]:
                print(f"  • {rec}")

        print(f"\n📋 SERVICE PORT MAPPINGS")
        for service, ports in report["service_ports"].items():
            print(f"  {service}: {ports['external']} → {ports['internal']} ({ports['protocol']})")

        print("\n" + "="*80)

    def export_conflict_resolution_script(self, conflicts: List[PortConflict]) -> str:
        """Generate a script to resolve detected conflicts"""
        script_lines = [
            "#!/bin/bash",
            "# Port Conflict Resolution Script",
            "# Generated by Port Conflict Detector",
            "",
            "echo '🔧 Resolving port conflicts...'",
            ""
        ]

        for conflict in conflicts:
            if conflict.severity in ["critical", "high"]:
                script_lines.extend([
                    f"# Resolving conflict on port {conflict.port}",
                    f"echo 'Resolving port {conflict.port} conflict...'",
                    "# Add your resolution commands here",
                    ""
                ])

        script_lines.extend([
            "echo '✅ Port conflict resolution complete'",
            "echo 'Remember to update port_registry.json if you change ports'"
        ])

        return "\n".join(script_lines)


def main():
    """Main entry point for port conflict detection"""
    detector = PortConflictDetector()

    try:
        # Run comprehensive analysis
        report = detector.run_comprehensive_analysis()

        # Print report
        detector.print_report(report)

        # Export conflict resolution script if conflicts found
        if report["summary"]["total_conflicts"] > 0:
            script = detector.export_conflict_resolution_script(detector.conflicts)
            with open("port_conflict_resolution.sh", "w") as f:
                f.write(script)

            print(f"\n📝 Resolution script saved to: port_conflict_resolution.sh")
            print("Run 'chmod +x port_conflict_resolution.sh' to make it executable")

        # Save detailed results
        with open("port_analysis_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Detailed results saved to: port_analysis_report.json")

        # Exit with error code if critical conflicts found
        if report["summary"]["critical_conflicts"] > 0:
            print("\n❌ Critical port conflicts detected!")
            exit(1)

    except Exception as e:
        logger.error(f"Port analysis failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()
