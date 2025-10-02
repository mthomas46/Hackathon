"""Service configuration management and versioning"""

import asyncio
import logging
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from monitoring.database.models import ConfigurationSnapshot
from monitoring.database.manager import DatabaseManager
from core.orchestrator import MetaOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class ServiceConfigReport:
    """Configuration report from a service"""
    service_name: str
    config_data: Dict[str, Any]
    config_sources: Dict[str, Any]
    timestamp: datetime
    version: str = "1.0.0"


@dataclass
class ConfigVersion:
    """Configuration version information"""
    service_name: str
    version: str
    config_hash: str
    source: str
    timestamp: datetime
    changes: List[str]


class ServiceConfigManager:
    """Manages service configurations via endpoints"""

    def __init__(self, db_manager: DatabaseManager, orchestrator: MetaOrchestrator):
        self.db_manager = db_manager
        self.orchestrator = orchestrator
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        """Initialize the config manager"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        logger.info("📋 Service config manager initialized")

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

    async def query_service_config(self, service_name: str) -> Optional[ServiceConfigReport]:
        """Query a service's configuration endpoint"""
        try:
            service_info = self.orchestrator.services.get(service_name)
            if not service_info:
                logger.error(f"❌ Service {service_name} not found in orchestrator")
                return None

            # Construct config endpoint URL
            config_endpoint = self._get_config_endpoint(service_info)

            if not config_endpoint:
                logger.warning(f"⚠️  No config endpoint available for {service_name}")
                return None

            logger.info(f"📡 Querying config endpoint for {service_name}: {config_endpoint}")

            async with self.session.get(config_endpoint) as response:
                if response.status == 200:
                    config_data = await response.json()

                    report = ServiceConfigReport(
                        service_name=service_name,
                        config_data=config_data.get('config', {}),
                        config_sources=config_data.get('sources', {}),
                        timestamp=datetime.utcnow(),
                        version=config_data.get('version', '1.0.0')
                    )

                    logger.info(f"✅ Retrieved config for {service_name} (v{report.version})")
                    return report
                else:
                    logger.error(f"❌ Failed to query {service_name} config endpoint: HTTP {response.status}")
                    return None

        except Exception as e:
            logger.error(f"❌ Error querying config for {service_name}: {e}")
            return None

    def _get_config_endpoint(self, service_info) -> Optional[str]:
        """Get the configuration endpoint for a service"""
        # Extract port from service configuration
        if service_info.ports:
            port_spec = service_info.ports[0]
            if ":" in port_spec:
                external_port = port_spec.split(":")[0]
            else:
                external_port = port_spec

            # Assume config endpoint is at /config
            return f"http://localhost:{external_port}/config"

        return None

    async def query_all_service_configs(self) -> Dict[str, ServiceConfigReport]:
        """Query configuration endpoints for all services"""
        logger.info("📡 Querying configuration endpoints for all services")

        tasks = []
        service_names = []

        for service_name in self.orchestrator.services.keys():
            task = self.query_service_config(service_name)
            tasks.append(task)
            service_names.append(service_name)

        # Execute all queries concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        config_reports = {}
        successful_queries = 0

        for service_name, result in zip(service_names, results):
            if isinstance(result, Exception):
                logger.error(f"❌ Config query failed for {service_name}: {result}")
            elif result is not None:
                config_reports[service_name] = result
                successful_queries += 1
            else:
                logger.warning(f"⚠️  No config available for {service_name}")

        logger.info(f"✅ Config queries complete. Retrieved configs for {successful_queries}/{len(service_names)} services")
        return config_reports

    def save_service_config(self, config_report: ServiceConfigReport) -> int:
        """Save a service configuration to the database"""
        try:
            # Calculate config hash
            config_str = json.dumps(config_report.config_data, sort_keys=True)
            config_hash = str(hash(config_str))[:16]

            # Create snapshot
            snapshot = ConfigurationSnapshot(
                service_name=config_report.service_name,
                config_hash=config_hash,
                config_data={
                    'config': config_report.config_data,
                    'sources': config_report.config_sources,
                    'version': config_report.version
                },
                source="service_endpoint",
                timestamp=config_report.timestamp
            )

            # Save to database
            snapshot_id = self.db_manager.save_configuration_snapshot(snapshot)

            logger.info(f"💾 Saved config snapshot for {config_report.service_name} (ID: {snapshot_id})")
            return snapshot_id

        except Exception as e:
            logger.error(f"❌ Failed to save config for {config_report.service_name}: {e}")
            return -1

    def get_service_config_history(self, service_name: str, limit: int = 10) -> List[ConfigurationSnapshot]:
        """Get configuration history for a service"""
        return self.db_manager.get_configuration_snapshots(service_name, limit)

    def get_latest_service_config(self, service_name: str) -> Optional[ConfigurationSnapshot]:
        """Get the latest configuration for a service"""
        snapshots = self.get_service_config_history(service_name, limit=1)
        return snapshots[0] if snapshots else None

    def export_service_config(self, service_name: str, format: str = "json") -> Optional[str]:
        """Export a service's current configuration"""
        try:
            latest_config = self.get_latest_service_config(service_name)
            if not latest_config:
                logger.warning(f"⚠️  No configuration found for {service_name}")
                return None

            if format.lower() == "json":
                return json.dumps(latest_config.config_data, indent=2)
            elif format.lower() == "yaml":
                try:
                    import yaml
                    return yaml.dump(latest_config.config_data, default_flow_style=False)
                except ImportError:
                    logger.warning("⚠️  PyYAML not available, falling back to JSON")
                    return json.dumps(latest_config.config_data, indent=2)
            else:
                logger.error(f"❌ Unsupported export format: {format}")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to export config for {service_name}: {e}")
            return None

    def export_all_configs(self, format: str = "json", output_dir: str = "config_exports") -> Dict[str, str]:
        """Export configurations for all services"""
        import os
        from pathlib import Path

        exports = {}
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        for service_name in self.orchestrator.services.keys():
            config_content = self.export_service_config(service_name, format)
            if config_content:
                filename = f"{service_name}_config.{format.lower()}"
                filepath = output_path / filename

                try:
                    with open(filepath, 'w') as f:
                        f.write(config_content)

                    exports[service_name] = str(filepath)
                    logger.info(f"📄 Exported config for {service_name} to {filepath}")

                except Exception as e:
                    logger.error(f"❌ Failed to write config file for {service_name}: {e}")

        logger.info(f"✅ Exported configurations for {len(exports)} services to {output_dir}")
        return exports

    async def sync_all_service_configs(self) -> Dict[str, Any]:
        """Sync configurations from all service endpoints"""
        logger.info("🔄 Starting configuration sync from all services")

        # Query all service configurations
        config_reports = await self.query_all_service_configs()

        sync_results = {
            'total_services': len(self.orchestrator.services),
            'successful_syncs': 0,
            'failed_syncs': 0,
            'new_versions': 0,
            'service_results': {}
        }

        for service_name, config_report in config_reports.items():
            try:
                # Save the configuration
                snapshot_id = self.save_service_config(config_report)

                if snapshot_id > 0:
                    sync_results['successful_syncs'] += 1
                    sync_results['service_results'][service_name] = {
                        'status': 'success',
                        'snapshot_id': snapshot_id,
                        'version': config_report.version
                    }
                else:
                    sync_results['failed_syncs'] += 1
                    sync_results['service_results'][service_name] = {
                        'status': 'failed',
                        'error': 'save_failed'
                    }

            except Exception as e:
                sync_results['failed_syncs'] += 1
                sync_results['service_results'][service_name] = {
                    'status': 'failed',
                    'error': str(e)
                }
                logger.error(f"❌ Failed to sync config for {service_name}: {e}")

        # Check for new versions (services not in reports)
        for service_name in self.orchestrator.services.keys():
            if service_name not in sync_results['service_results']:
                sync_results['service_results'][service_name] = {
                    'status': 'no_endpoint',
                    'error': 'Service does not have config endpoint'
                }

        logger.info(f"✅ Configuration sync complete: {sync_results['successful_syncs']} successful, {sync_results['failed_syncs']} failed")
        return sync_results

    def compare_service_configs(self, service_name: str) -> Dict[str, Any]:
        """Compare a service's current config with stored versions"""
        try:
            latest_config = self.get_latest_service_config(service_name)
            if not latest_config:
                return {"status": "no_stored_config"}

            # Get previous configs for comparison
            history = self.get_service_config_history(service_name, limit=5)

            if len(history) < 2:
                return {
                    "status": "insufficient_history",
                    "latest_config": latest_config.config_data
                }

            # Compare with previous version
            current_config = latest_config.config_data
            previous_config = history[1].config_data  # Second most recent

            changes = self._compare_configs(previous_config, current_config)

            return {
                "status": "compared",
                "changes_detected": len(changes) > 0,
                "change_count": len(changes),
                "changes": changes,
                "current_version": current_config.get('version', 'unknown'),
                "previous_version": previous_config.get('version', 'unknown')
            }

        except Exception as e:
            logger.error(f"❌ Failed to compare configs for {service_name}: {e}")
            return {"status": "error", "error": str(e)}

    def _compare_configs(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare two configurations and return list of changes"""
        changes = []

        # Compare config sections
        for section in ['config', 'sources']:
            if section in old_config and section in new_config:
                old_section = old_config[section]
                new_section = new_config[section]

                # Simple comparison - could be made more sophisticated
                if old_section != new_section:
                    changes.append({
                        "section": section,
                        "change_type": "modified",
                        "old_value": old_section,
                        "new_value": new_section
                    })
            elif section in old_config and section not in new_config:
                changes.append({
                    "section": section,
                    "change_type": "removed",
                    "old_value": old_config[section]
                })
            elif section not in old_config and section in new_config:
                changes.append({
                    "section": section,
                    "change_type": "added",
                    "new_value": new_config[section]
                })

        return changes
