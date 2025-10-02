"""Configuration drift detection and monitoring"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass

from monitoring.database.models import ConfigurationSnapshot, ConfigurationDrift, DriftPattern
from monitoring.database.manager import DatabaseManager
from core.orchestrator import MetaOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class DriftDetectionResult:
    """Result of drift detection"""
    service_name: str
    has_drift: bool
    drifts: List[ConfigurationDrift]
    snapshot_taken: bool
    new_snapshot: Optional[ConfigurationSnapshot] = None


class ConfigurationDriftDetector:
    """Detects and monitors configuration drift"""

    def __init__(self, db_manager: DatabaseManager, orchestrator: MetaOrchestrator):
        self.db_manager = db_manager
        self.orchestrator = orchestrator

    def _calculate_config_hash(self, config: Dict[str, Any]) -> str:
        """Calculate hash of configuration for comparison"""
        # Create a normalized JSON string for consistent hashing
        normalized_config = json.dumps(config, sort_keys=True)
        return hashlib.sha256(normalized_config.encode()).hexdigest()[:16]

    def _compare_configs(self, old_config: Dict[str, Any],
                        new_config: Dict[str, Any]) -> List[ConfigurationDrift]:
        """Compare two configurations and identify drifts"""
        drifts = []

        # Compare environment variables
        old_env = old_config.get('environment', {})
        new_env = new_config.get('environment', {})

        # Handle both list and dict formats for environment variables
        if isinstance(old_env, list):
            old_env = self._parse_env_list(old_env)
        if isinstance(new_env, list):
            new_env = self._parse_env_list(new_env)

        # Check for added environment variables
        for key, value in new_env.items():
            if key not in old_env:
                drifts.append(ConfigurationDrift(
                    service_name="",  # Will be set by caller
                    drift_type="environment",
                    severity="info",
                    description=f"Environment variable '{key}' was added",
                    expected_value=None,
                    actual_value=value
                ))

        # Check for removed environment variables
        for key, value in old_env.items():
            if key not in new_env:
                drifts.append(ConfigurationDrift(
                    service_name="",  # Will be set by caller
                    drift_type="environment",
                    severity="warning",
                    description=f"Environment variable '{key}' was removed",
                    expected_value=value,
                    actual_value=None
                ))

        # Check for modified environment variables
        for key in set(old_env.keys()) & set(new_env.keys()):
            if old_env[key] != new_env[key]:
                drifts.append(ConfigurationDrift(
                    service_name="",  # Will be set by caller
                    drift_type="environment",
                    severity="warning",
                    description=f"Environment variable '{key}' was modified",
                    expected_value=old_env[key],
                    actual_value=new_env[key]
                ))

        # Compare ports
        old_ports = set(old_config.get('ports', []))
        new_ports = set(new_config.get('ports', []))

        added_ports = new_ports - old_ports
        removed_ports = old_ports - new_ports

        for port in added_ports:
            drifts.append(ConfigurationDrift(
                service_name="",  # Will be set by caller
                drift_type="ports",
                severity="info",
                description=f"Port '{port}' was added",
                expected_value=None,
                actual_value=port
            ))

        for port in removed_ports:
            drifts.append(ConfigurationDrift(
                service_name="",  # Will be set by caller
                drift_type="ports",
                severity="warning",
                description=f"Port '{port}' was removed",
                expected_value=port,
                actual_value=None
            ))

        # Compare volumes
        old_volumes = set(old_config.get('volumes', []))
        new_volumes = set(new_config.get('volumes', []))

        added_volumes = new_volumes - old_volumes
        removed_volumes = old_volumes - new_volumes

        for volume in added_volumes:
            drifts.append(ConfigurationDrift(
                service_name="",  # Will be set by caller
                drift_type="volumes",
                severity="info",
                description=f"Volume '{volume}' was added",
                expected_value=None,
                actual_value=volume
            ))

        for volume in removed_volumes:
            drifts.append(ConfigurationDrift(
                service_name="",  # Will be set by caller
                drift_type="volumes",
                severity="warning",
                description=f"Volume '{volume}' was removed",
                expected_value=volume,
                actual_value=None
            ))

        return drifts

    def _parse_env_list(self, env_list: List[str]) -> Dict[str, str]:
        """Parse environment variable list format"""
        env_dict = {}
        for env_item in env_list:
            if isinstance(env_item, str) and '=' in env_item:
                key, value = env_item.split('=', 1)
                env_dict[key] = value
        return env_dict

    async def detect_drift_for_service(self, service_name: str) -> DriftDetectionResult:
        """Detect configuration drift for a specific service"""
        try:
            # Get current service configuration
            services = await self.orchestrator.get_service_status(service_name)
            if not services:
                return DriftDetectionResult(
                    service_name=service_name,
                    has_drift=False,
                    drifts=[],
                    snapshot_taken=False
                )

            current_service = services[0]
            current_config = current_service.config
            config_hash = self._calculate_config_hash(current_config)

            # Get latest snapshot from database
            latest_snapshot = self.db_manager.get_latest_snapshot(service_name)

            # Create new snapshot
            new_snapshot = ConfigurationSnapshot(
                service_name=service_name,
                config_hash=config_hash,
                config_data=current_config,
                source="runtime"
            )

            # Save snapshot
            self.db_manager.save_configuration_snapshot(new_snapshot)

            # Check for drift
            drifts = []
            if latest_snapshot:
                if latest_snapshot.config_hash != config_hash:
                    drifts = self._compare_configs(
                        latest_snapshot.config_data,
                        current_config
                    )

                    # Set service name on drifts
                    for drift in drifts:
                        drift.service_name = service_name

                    # Save drift records
                    for drift in drifts:
                        self.db_manager.save_configuration_drift(drift)

            return DriftDetectionResult(
                service_name=service_name,
                has_drift=len(drifts) > 0,
                drifts=drifts,
                snapshot_taken=True,
                new_snapshot=new_snapshot
            )

        except Exception as e:
            logger.error(f"❌ Failed to detect drift for {service_name}: {e}")
            return DriftDetectionResult(
                service_name=service_name,
                has_drift=False,
                drifts=[],
                snapshot_taken=False
            )

    async def detect_drift_all_services(self) -> Dict[str, DriftDetectionResult]:
        """Detect configuration drift for all services"""
        logger.info("🔍 Starting configuration drift detection for all services")

        results = {}
        for service_name in self.orchestrator.services.keys():
            result = await self.detect_drift_for_service(service_name)
            results[service_name] = result

            if result.has_drift:
                logger.warning(f"⚠️  Configuration drift detected for {service_name}: {len(result.drifts)} changes")
            else:
                logger.info(f"✅ No configuration drift for {service_name}")

        total_drift = sum(len(result.drifts) for result in results.values())
        logger.info(f"🔍 Drift detection complete. Found {total_drift} total configuration changes across {len(results)} services")

        return results

    async def analyze_drift_patterns(self) -> Dict[str, DriftPattern]:
        """Analyze configuration drift patterns over time"""
        logger.info("📊 Analyzing configuration drift patterns")

        patterns = {}
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        # Get all drift records from the last 30 days
        drifts = self.db_manager.get_configuration_drift(resolved=False, limit=1000)

        # Group drifts by service and type
        service_patterns = {}
        for drift in drifts:
            if drift.timestamp < thirty_days_ago:
                continue

            key = (drift.service_name, drift.drift_type)
            if key not in service_patterns:
                service_patterns[key] = []
            service_patterns[key].append(drift)

        # Analyze patterns
        for (service_name, drift_type), drift_list in service_patterns.items():
            if len(drift_list) < 3:  # Need at least 3 occurrences for pattern
                continue

            # Calculate frequency
            timestamps = [d.timestamp for d in drift_list]
            timestamps.sort()

            # Simple frequency analysis
            if len(drift_list) >= 10:
                frequency = "high"
            elif len(drift_list) >= 5:
                frequency = "medium"
            else:
                frequency = "low"

            # Determine impact
            severities = [d.severity for d in drift_list]
            if "critical" in severities:
                impact = "high"
            elif "high" in severities or "error" in severities:
                impact = "medium"
            else:
                impact = "low"

            # Generate description and recommendations
            description = f"Frequent {drift_type} changes detected ({len(drift_list)} occurrences in 30 days)"
            recommendations = []

            if drift_type == "environment":
                recommendations.append("Consider using centralized configuration management")
                recommendations.append("Implement environment variable validation")
            elif drift_type == "ports":
                recommendations.append("Review port allocation strategy")
                recommendations.append("Implement port conflict detection")
            elif drift_type == "volumes":
                recommendations.append("Standardize volume mounting patterns")
                recommendations.append("Implement volume validation")

            pattern = DriftPattern(
                service_name=service_name,
                pattern_type=f"frequent_{drift_type}_changes",
                frequency=frequency,
                impact=impact,
                description=description,
                first_seen=min(timestamps),
                last_seen=max(timestamps),
                occurrence_count=len(drift_list),
                affected_configs=[drift_type],
                recommendations=recommendations
            )

            # Save pattern
            self.db_manager.save_drift_pattern(pattern)
            patterns[f"{service_name}_{drift_type}"] = pattern

        logger.info(f"📊 Pattern analysis complete. Found {len(patterns)} drift patterns")
        return patterns

    def get_drift_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get drift statistics for reporting"""
        return self.db_manager.get_drift_statistics(days)

    def get_unresolved_drifts(self, service_name: Optional[str] = None) -> List[ConfigurationDrift]:
        """Get unresolved configuration drifts"""
        return self.db_manager.get_configuration_drift(
            service_name=service_name,
            resolved=False,
            limit=100
        )

    async def resolve_drift(self, drift_id: int, resolution_action: str) -> bool:
        """Resolve a configuration drift"""
        return self.db_manager.resolve_drift(drift_id, resolution_action)
