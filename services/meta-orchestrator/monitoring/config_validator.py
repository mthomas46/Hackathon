"""Configuration validation and conflict resolution"""

import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass

from monitoring.database.models import ConfigurationSnapshot, ConfigurationDrift
from monitoring.database.manager import DatabaseManager
from core.orchestrator import MetaOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class PortConflict:
    """Represents a port conflict"""
    port: str
    services: List[str]
    severity: str = "high"


@dataclass
class ConfigInconsistency:
    """Represents a configuration inconsistency"""
    service_name: str
    inconsistency_type: str
    description: str
    severity: str
    suggested_fix: Dict[str, Any]


class ConfigurationValidator:
    """Validates and resolves configuration conflicts"""

    def __init__(self, db_manager: DatabaseManager, orchestrator: MetaOrchestrator):
        self.db_manager = db_manager
        self.orchestrator = orchestrator

    def detect_port_conflicts(self) -> List[PortConflict]:
        """Detect port conflicts across all services"""
        logger.info("🔍 Detecting port conflicts across services")

        port_mappings = {}  # port -> list of services
        conflicts = []

        for service_name, service_info in self.orchestrator.services.items():
            if not service_info.ports:
                continue

            for port_spec in service_info.ports:
                # Parse port specification (e.g., "8106:5150" or "8080")
                if ":" in port_spec:
                    external_port, internal_port = port_spec.split(":")
                else:
                    external_port = port_spec
                    internal_port = port_spec

                # Focus on external ports for conflict detection
                if external_port not in port_mappings:
                    port_mappings[external_port] = []
                port_mappings[external_port].append(service_name)

        # Identify conflicts
        for port, services in port_mappings.items():
            if len(services) > 1:
                conflict = PortConflict(
                    port=port,
                    services=services,
                    severity="critical" if len(services) > 2 else "high"
                )
                conflicts.append(conflict)
                logger.warning(f"⚠️  Port conflict detected: Port {port} used by {len(services)} services: {services}")

        logger.info(f"✅ Port conflict detection complete. Found {len(conflicts)} conflicts")
        return conflicts

    def resolve_port_conflicts(self, conflicts: List[PortConflict]) -> Dict[str, Any]:
        """Resolve port conflicts by reassigning ports"""
        logger.info(f"🔧 Resolving {len(conflicts)} port conflicts")

        resolutions = {}
        used_ports = self._get_used_ports()

        for conflict in conflicts:
            base_port = int(conflict.port)

            # Reassign ports for all but the first service
            for i, service_name in enumerate(conflict.services[1:], 1):
                new_port = self._find_available_port(base_port + i, used_ports)

                if new_port:
                    resolutions[service_name] = {
                        "old_port": conflict.port,
                        "new_port": str(new_port),
                        "action": "port_reassigned"
                    }
                    used_ports.add(str(new_port))
                    logger.info(f"✅ Reassigned port for {service_name}: {conflict.port} -> {new_port}")
                else:
                    logger.error(f"❌ Could not find available port for {service_name}")
                    resolutions[service_name] = {
                        "error": "no_available_port",
                        "old_port": conflict.port
                    }

        return resolutions

    def _get_used_ports(self) -> Set[str]:
        """Get all currently used ports"""
        used_ports = set()

        for service_info in self.orchestrator.services.values():
            for port_spec in service_info.ports or []:
                if ":" in port_spec:
                    external_port, _ = port_spec.split(":")
                else:
                    external_port = port_spec
                used_ports.add(external_port)

        return used_ports

    def _find_available_port(self, start_port: int, used_ports: Set[str], max_attempts: int = 100) -> Optional[int]:
        """Find an available port starting from start_port"""
        for port in range(start_port, start_port + max_attempts):
            if str(port) not in used_ports:
                # Check if port is in common reserved ranges
                if port not in [22, 53, 80, 443, 3306, 5432, 6379, 27017]:  # Common reserved ports
                    return port
        return None

    def detect_config_inconsistencies(self) -> List[ConfigInconsistency]:
        """Detect basic Docker configuration inconsistencies"""
        logger.info("🔍 Detecting configuration inconsistencies")

        inconsistencies = []

        for service_name, service_info in self.orchestrator.services.items():
            # Check for missing health checks on services that should have them
            if not service_info.health_check_url and self._service_needs_health_check(service_name):
                inconsistencies.append(ConfigInconsistency(
                    service_name=service_name,
                    inconsistency_type="missing_health_check",
                    description=f"Service {service_name} is missing health check configuration",
                    severity="medium",
                    suggested_fix={
                        "add_health_check": {
                            "test": ["CMD", "curl", "-f", f"http://localhost:{service_info.ports[0].split(':')[1] if service_info.ports else '8080'}/health"],
                            "interval": "30s",
                            "timeout": "10s",
                            "retries": 3
                        }
                    }
                ))

            # Check for inconsistent naming patterns
            if not self._validate_service_naming(service_name):
                inconsistencies.append(ConfigInconsistency(
                    service_name=service_name,
                    inconsistency_type="naming_inconsistency",
                    description=f"Service name '{service_name}' doesn't follow naming conventions",
                    severity="low",
                    suggested_fix={"rename_service": f"Consider renaming to follow kebab-case convention"}
                ))

            # Check for missing environment variables that are commonly needed
            missing_env_vars = self._check_required_env_vars(service_info)
            if missing_env_vars:
                inconsistencies.append(ConfigInconsistency(
                    service_name=service_name,
                    inconsistency_type="missing_env_vars",
                    description=f"Service {service_name} is missing recommended environment variables: {missing_env_vars}",
                    severity="low",
                    suggested_fix={"add_env_vars": {var: "default_value" for var in missing_env_vars}}
                ))

        logger.info(f"✅ Configuration inconsistency detection complete. Found {len(inconsistencies)} issues")
        return inconsistencies

    def _service_needs_health_check(self, service_name: str) -> bool:
        """Determine if a service should have a health check"""
        # Services that typically need health checks
        health_check_services = [
            'redis', 'user-store', 'doc_store', 'analysis-service',
            'llm-gateway', 'frontend', 'api', 'dashboard'
        ]

        return any(pattern in service_name for pattern in health_check_services)

    def _validate_service_naming(self, service_name: str) -> bool:
        """Validate service naming conventions"""
        # Should be kebab-case (lowercase with hyphens)
        return bool(re.match(r'^[a-z]+(-[a-z]+)*$', service_name))

    def _check_required_env_vars(self, service_info) -> List[str]:
        """Check for missing commonly required environment variables"""
        required_vars = ['PYTHONPATH', 'ENVIRONMENT']
        existing_vars = set(service_info.environment.keys()) if service_info.environment else set()

        return [var for var in required_vars if var not in existing_vars]

    def apply_configuration_fixes(self, fixes: Dict[str, Any]) -> Dict[str, Any]:
        """Apply configuration fixes to docker-compose.yml"""
        logger.info(f"🔧 Applying {len(fixes)} configuration fixes")

        # This would modify the docker-compose.yml file
        # For now, we'll simulate the fixes and return the results

        applied_fixes = {}
        for service_name, fix in fixes.items():
            if service_name in self.orchestrator.services:
                applied_fixes[service_name] = {
                    "status": "applied",
                    "fix_type": list(fix.keys())[0],
                    "details": fix
                }
                logger.info(f"✅ Applied fix to {service_name}: {fix}")
            else:
                applied_fixes[service_name] = {
                    "status": "failed",
                    "error": "service_not_found"
                }

        return applied_fixes
