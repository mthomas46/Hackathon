"""Main monitoring service that orchestrates all monitoring components"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from monitoring.database.manager import DatabaseManager
from monitoring.health.checker import HealthChecker, HealthCheckConfig
from monitoring.drift_detector import ConfigurationDriftDetector
from monitoring.alerts.manager import AlertManager
from monitoring.analytics.analyzer import DriftAnalytics
from monitoring.config_validator import ConfigurationValidator
from monitoring.config_manager import ServiceConfigManager
from monitoring.audit.docker_compose_validator import DockerComposeValidator, DockerComposeValidationResult
from monitoring.audit.config_drift_detector import ConfigurationDriftDetector as AuditDriftDetector, DriftDetectionResult
from monitoring.audit.production_readiness import ProductionReadinessValidator, ProductionReadinessReport, ReadinessLevel
from monitoring.audit.config_standardizer import ConfigurationStandardizer, StandardizationResult, ConfigStandardizationReport
from monitoring.audit.docker_standardizer import UnifiedDockerStandardizer, StandardizationMode, DockerStandardizationReport
from core.orchestrator import MetaOrchestrator

logger = logging.getLogger(__name__)


class MonitoringService:
    """Main monitoring service for configuration drift detection and health monitoring"""

    def __init__(self, orchestrator: MetaOrchestrator, db_path: str = "/tmp/monitoring.db"):
        self.orchestrator = orchestrator
        self.db_manager = DatabaseManager(db_path)
        self.health_checker = HealthChecker(self.db_manager)
        self.drift_detector = ConfigurationDriftDetector(self.db_manager, orchestrator)
        self.alert_manager = AlertManager(self.db_manager)
        self.analytics = DriftAnalytics(self.db_manager)
        self.config_validator = ConfigurationValidator(self.db_manager, orchestrator)
        self.config_manager = ServiceConfigManager(self.db_manager, orchestrator)

        # Audit validators
        self.docker_compose_validator = DockerComposeValidator(orchestrator.settings.workspace_path)
        self.audit_drift_detector = AuditDriftDetector(orchestrator.settings.workspace_path)
        self.production_readiness_validator = ProductionReadinessValidator(orchestrator.settings.workspace_path)
        self.config_standardizer = ConfigurationStandardizer(orchestrator.settings.workspace_path)
        self.docker_standardizer = UnifiedDockerStandardizer(orchestrator.settings.workspace_path)

        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_running = False

    async def initialize(self):
        """Initialize the monitoring service"""
        logger.info("🚀 Initializing Monitoring Service")

        # Initialize components
        await self.health_checker.initialize()
        await self.config_manager.initialize()

        # Configure health checks for services
        await self._configure_health_checks()

        logger.info("✅ Monitoring Service initialized")

    async def _configure_health_checks(self):
        """Configure health checks for all services"""
        logger.info("🏥 Configuring health checks for services")

        # Services that don't have HTTP health endpoints (infrastructure services)
        non_http_services = {'redis', 'ollama'}

        # Get all services from orchestrator
        services = await self.orchestrator.get_service_status()

        for service in services:
            # Skip infrastructure services that don't have HTTP health endpoints
            if service.name in non_http_services:
                logger.info(f"⏭️ Skipping health check for {service.name} (infrastructure service)")
                continue

            # Extract health endpoint from service config
            health_endpoint = self._extract_health_endpoint(service)

            if health_endpoint:
                config = HealthCheckConfig(
                    service_name=service.name,
                    health_endpoint=health_endpoint,
                    timeout=15.0  # Longer timeout for monitoring
                )
                self.health_checker.add_service_config(config)

        logger.info(f"✅ Configured health checks for {len(self.health_checker.health_configs)} services")

    def _extract_health_endpoint(self, service_info) -> Optional[str]:
        """Extract health endpoint from service configuration"""
        # Try to construct health endpoint from service config
        ports = service_info.ports
        if ports:
            # Assume first port is the main service port
            port_spec = ports[0]  # e.g., "8106:5150"
            if ":" in port_spec:
                # This is a mapped port, extract the external port
                external_port = port_spec.split(":")[0]
                return f"http://localhost:{external_port}/health"

        return None

    async def start_monitoring(self, drift_interval: int = 300,
                              health_interval: int = 60,
                              analytics_interval: int = 3600):
        """Start the monitoring service with background tasks"""
        if self.is_running:
            logger.warning("⚠️  Monitoring service is already running")
            return

        self.is_running = True
        logger.info("🔄 Starting monitoring service")

        # Create monitoring tasks
        self.monitoring_task = asyncio.create_task(
            self._run_monitoring_loop(drift_interval, health_interval, analytics_interval)
        )

        logger.info("✅ Monitoring service started")

    async def stop_monitoring(self):
        """Stop the monitoring service"""
        if not self.is_running:
            logger.info("⚠️  Monitoring service is not running")
            return

        self.is_running = False
        logger.info("🛑 Stopping monitoring service")

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        # Cleanup components
        await self.health_checker.cleanup()
        await self.config_manager.cleanup()

        logger.info("✅ Monitoring service stopped")

    async def _run_monitoring_loop(self, drift_interval: int,
                                  health_interval: int,
                                  analytics_interval: int):
        """Main monitoring loop"""
        drift_next = datetime.utcnow().timestamp()
        health_next = datetime.utcnow().timestamp()
        analytics_next = datetime.utcnow().timestamp()

        while self.is_running:
            try:
                current_time = datetime.utcnow().timestamp()

                # Run health checks
                if current_time >= health_next:
                    await self._perform_health_checks()
                    health_next = current_time + health_interval

                # Run drift detection
                if current_time >= drift_next:
                    await self._perform_drift_detection()
                    drift_next = current_time + drift_interval

                # Run analytics
                if current_time >= analytics_next:
                    await self._perform_analytics()
                    analytics_next = current_time + analytics_interval

                # Sleep for a short interval
                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(30)  # Back off on errors

    async def _perform_health_checks(self):
        """Perform health checks for all services"""
        logger.info("🏥 Running health checks")

        try:
            health_results = await self.health_checker.check_all_services_health()
            summary = self.health_checker.get_health_summary(health_results)

            # Check for alerts
            health_percentage = summary.get('overall_health_percentage', 100)
            total_services = summary.get('total_services', 0)
            healthy_services = summary.get('healthy_services', 0)

            # Alert on low overall health
            overall_alert = self.alert_manager.create_overall_health_alert(
                health_percentage, total_services, healthy_services
            )
            if overall_alert:
                self.alert_manager.send_alert(overall_alert)

            # Alert on individual unhealthy services
            for service_name, health in health_results.items():
                if health.health_status == "unhealthy":
                    # Check for consecutive failures
                    consecutive_failures = await self._get_consecutive_failures(service_name)
                    if consecutive_failures >= 3:
                        alert = self.alert_manager.create_health_alert(service_name, consecutive_failures)
                        if alert:
                            self.alert_manager.send_alert(alert)

            logger.info(f"✅ Health checks completed: {healthy_services}/{total_services} services healthy")

        except Exception as e:
            logger.error(f"❌ Error performing health checks: {e}")

    async def _perform_drift_detection(self):
        """Perform configuration drift detection"""
        logger.info("🔍 Running configuration drift detection")

        try:
            drift_results = await self.drift_detector.detect_drift_all_services()

            total_drifts = 0
            services_with_drift = 0

            for service_name, result in drift_results.items():
                if result.has_drift:
                    services_with_drift += 1
                    total_drifts += len(result.drifts)

                    # Create alerts for critical drifts
                    for drift in result.drifts:
                        if drift.severity in ["critical", "high"]:
                            alert = self.alert_manager.create_critical_drift_alert(
                                service_name, drift.description, drift.severity
                            )
                            if alert:
                                self.alert_manager.send_alert(alert)

            # Check for high drift frequency alerts
            for service_name in self.orchestrator.services.keys():
                recent_drifts = self.db_manager.get_configuration_drift(
                    service_name=service_name,
                    limit=20
                )

                # Count drifts in last 24 hours
                cutoff = datetime.utcnow().timestamp() - (24 * 3600)
                recent_count = sum(1 for d in recent_drifts if d.timestamp.timestamp() >= cutoff)

                if recent_count >= 5:
                    alert = self.alert_manager.create_drift_alert(service_name, recent_count, 24)
                    if alert:
                        self.alert_manager.send_alert(alert)

            logger.info(f"✅ Drift detection completed: {total_drifts} changes in {services_with_drift} services")

        except Exception as e:
            logger.error(f"❌ Error performing drift detection: {e}")

    async def _perform_analytics(self):
        """Perform analytics and pattern analysis"""
        logger.info("📊 Running analytics and pattern analysis")

        try:
            # Analyze drift patterns
            patterns = await self.drift_detector.analyze_drift_patterns()

            # Generate analytics report
            report = self.analytics.get_comprehensive_report()

            # Log key insights
            risk_level = report.get("risk_level", "unknown")
            if risk_level in ["high", "critical"]:
                logger.warning(f"⚠️  System risk level: {risk_level.upper()} - Review recommendations")

            recommendations = report.get("recommendations", [])
            if recommendations:
                logger.info(f"💡 Generated {len(recommendations)} recommendations for system improvement")

            logger.info("✅ Analytics completed")

        except Exception as e:
            logger.error(f"❌ Error performing analytics: {e}")

    async def _get_consecutive_failures(self, service_name: str) -> int:
        """Get count of consecutive health check failures"""
        try:
            health_history = self.db_manager.get_service_health_history(service_name, hours=1)

            # Get recent health checks (last 10)
            recent_checks = sorted(health_history, key=lambda h: h.timestamp, reverse=True)[:10]

            consecutive_failures = 0
            for health in recent_checks:
                if health.health_status in ["unhealthy", "error"]:
                    consecutive_failures += 1
                else:
                    break  # Stop at first healthy check

            return consecutive_failures

        except Exception:
            return 0

    # Public API methods
    async def get_health_status(self) -> Dict[str, Any]:
        """Get current health status of all services"""
        health_status = self.db_manager.get_current_health_status()
        health_data = {}

        for service_name, health in health_status.items():
            health_data[service_name] = {
                "status": health.health_status,
                "response_time": health.response_time,
                "last_check": health.timestamp.isoformat(),
                "endpoint": health.endpoint,
                "error": health.error_message
            }

        return health_data

    async def get_drift_status(self) -> Dict[str, Any]:
        """Get current drift status"""
        unresolved_drifts = self.db_manager.get_configuration_drift(resolved=False, limit=100)

        # Group by service
        drift_by_service = {}
        for drift in unresolved_drifts:
            if drift.service_name not in drift_by_service:
                drift_by_service[drift.service_name] = []
            drift_by_service[drift.service_name].append({
                "type": drift.drift_type,
                "severity": drift.severity,
                "description": drift.description,
                "timestamp": drift.timestamp.isoformat()
            })

        return {
            "total_unresolved": len(unresolved_drifts),
            "by_service": drift_by_service
        }

    async def get_alerts(self, service_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active alerts"""
        alerts = self.alert_manager.get_active_alerts(service_name)

        return [{
            "id": alert.id,
            "type": alert.alert_type,
            "severity": alert.severity,
            "service": alert.service_name,
            "title": alert.title,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "acknowledged": alert.acknowledged
        } for alert in alerts]

    async def get_analytics_report(self) -> Dict[str, Any]:
        """Get comprehensive analytics report"""
        return self.analytics.get_comprehensive_report()

    async def acknowledge_alert(self, alert_id: int, user: str) -> bool:
        """Acknowledge an alert"""
        return self.alert_manager.acknowledge_alert(alert_id, user)

    async def resolve_drift(self, drift_id: int, action: str) -> bool:
        """Resolve a configuration drift"""
        return await self.drift_detector.resolve_drift(drift_id, action)

    def cleanup_old_data(self, days: int = 90):
        """Clean up old monitoring data"""
        return self.db_manager.cleanup_old_data(days)

    # Configuration Validation and Healing Methods
    async def detect_port_conflicts(self) -> List[Dict[str, Any]]:
        """Detect port conflicts in the ecosystem"""
        conflicts = self.config_validator.detect_port_conflicts()
        return [{
            "port": c.port,
            "services": c.services,
            "severity": c.severity
        } for c in conflicts]

    async def resolve_port_conflicts(self) -> Dict[str, Any]:
        """Automatically resolve port conflicts"""
        logger.info("🔧 Starting automatic port conflict resolution")

        # Detect conflicts
        conflicts = self.config_validator.detect_port_conflicts()

        if not conflicts:
            return {"status": "no_conflicts", "message": "No port conflicts detected"}

        # Resolve conflicts
        resolutions = self.config_validator.resolve_port_conflicts(conflicts)

        # Apply fixes (would modify docker-compose.yml in production)
        applied_fixes = self.config_validator.apply_configuration_fixes(resolutions)

        return {
            "status": "resolved",
            "conflicts_found": len(conflicts),
            "resolutions_applied": len(applied_fixes),
            "details": applied_fixes
        }

    # Audit and Validation Methods
    async def validate_docker_compose(self, compose_file: str = "docker-compose.dev.yml") -> Dict[str, Any]:
        """Validate Docker Compose configuration for startup"""
        logger.info(f"🔍 Validating Docker Compose file: {compose_file}")

        try:
            result = self.docker_compose_validator.validate_for_startup(compose_file)
            return {
                "success": result.success,
                "services_count": result.services_count,
                "port_conflicts": len(result.port_conflicts),
                "issues": [
                    {
                        "service": issue.service_name,
                        "type": issue.issue_type,
                        "severity": issue.severity,
                        "description": issue.description,
                        "can_auto_fix": issue.can_auto_fix
                    } for issue in result.issues
                ],
                "warnings": result.warnings,
                "errors": result.errors,
                "validation_errors": result.validation_errors,
                "port_conflicts_detail": [
                    {
                        "port": pc.port,
                        "services": pc.services,
                        "severity": pc.severity
                    } for pc in result.port_conflicts
                ]
            }
        except Exception as e:
            logger.error(f"❌ Docker Compose validation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "issues": [],
                "warnings": 0,
                "errors": 1
            }

    async def detect_configuration_drift(self, dev_only: bool = True) -> Dict[str, Any]:
        """Detect configuration drift across all sources"""
        logger.info("🔍 Detecting configuration drift")

        try:
            result = self.audit_drift_detector.detect_all_drift(dev_only=dev_only)
            return {
                "success": result.success,
                "total_issues": result.total_issues,
                "high_severity": result.high_severity,
                "medium_severity": result.medium_severity,
                "low_severity": result.low_severity,
                "schema_validation_passed": result.schema_validation_passed,
                "scanned_files": result.scanned_files,
                "scanned_containers": result.scanned_containers,
                "issues": [
                    {
                        "type": issue.issue_type,
                        "severity": issue.severity,
                        "description": issue.description,
                        "field_path": issue.field_path,
                        "can_auto_fix": issue.can_auto_fix
                    } for issue in result.issues
                ],
                "validation_errors": result.validation_errors
            }
        except Exception as e:
            logger.error(f"❌ Configuration drift detection failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_issues": 0,
                "issues": []
            }

    async def validate_production_readiness(self, target_level: str = "development_ready") -> Dict[str, Any]:
        """Validate production readiness of the ecosystem"""
        logger.info(f"🎯 Validating production readiness (target: {target_level})")

        try:
            # Convert string to enum
            level_map = {
                "production_ready": ReadinessLevel.PRODUCTION_READY,
                "development_ready": ReadinessLevel.DEVELOPMENT_READY,
                "testing_ready": ReadinessLevel.TESTING_READY,
                "not_ready": ReadinessLevel.NOT_READY
            }
            target = level_map.get(target_level, ReadinessLevel.DEVELOPMENT_READY)

            report = self.production_readiness_validator.validate_readiness(target)

            return {
                "success": True,
                "overall_readiness": report.overall_readiness.value,
                "overall_score": report.overall_score,
                "total_checks": report.total_checks,
                "passed_checks": report.passed_checks,
                "failed_checks": report.failed_checks,
                "critical_failures": report.critical_failures,
                "results": [
                    {
                        "check_name": result.check_name,
                        "success": result.success,
                        "score": result.score,
                        "message": result.message,
                        "issues": result.issues or [],
                        "recommendations": result.recommendations or []
                    } for result in (report.results or [])
                ],
                "summary": report.summary or {},
                "recommendations": report.recommendations or []
            }
        except Exception as e:
            logger.error(f"❌ Production readiness validation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "overall_readiness": "not_ready",
                "overall_score": 0.0,
                "results": []
            }

    # Configuration Standardization Methods
    async def standardize_service_config(self, service_name: str, mode: str = "validate") -> Dict[str, Any]:
            """Standardize configuration for a specific service."""
            logger.info(f"🔧 Standardizing configuration for service: {service_name}")

            try:
                # Convert string mode to enum
                mode_map = {
                    "validate": StandardizationMode.VALIDATE_ONLY,
                    "dry_run": StandardizationMode.DRY_RUN,
                    "apply": StandardizationMode.APPLY_CHANGES
                }
                standardization_mode = mode_map.get(mode, StandardizationMode.VALIDATE_ONLY)

                result = self.config_standardizer.standardize_service(service_name, standardization_mode)

                return {
                    "success": result.success,
                    "service_name": result.service_name,
                    "changes_made": result.changes_made,
                    "warnings": result.warnings,
                    "errors": result.errors,
                    "issues": [
                        {
                            "service": issue.service_name,
                            "type": issue.issue_type,
                            "severity": issue.severity,
                            "description": issue.description,
                            "can_auto_fix": issue.can_auto_fix
                        } for issue in result.issues
                    ]
                }
            except Exception as e:
                logger.error(f"❌ Configuration standardization failed for {service_name}: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "service_name": service_name,
                    "issues": []
                }

    async def standardize_all_configs(self, mode: str = "validate") -> Dict[str, Any]:
        """Standardize configurations for all services."""
        logger.info(f"🔧 Standardizing configurations for all services (mode: {mode})")

        try:
            # Convert string mode to enum
            mode_map = {
                "validate": StandardizationMode.VALIDATE_ONLY,
                "dry_run": StandardizationMode.DRY_RUN,
                "apply": StandardizationMode.APPLY_CHANGES
            }
            standardization_mode = mode_map.get(mode, StandardizationMode.VALIDATE_ONLY)

            report = self.config_standardizer.standardize_all_services(standardization_mode)

            return {
                "success": True,
                "services_processed": report.services_processed,
                "services_standardized": report.services_standardized,
                "total_issues": report.total_issues,
                "fixes_applied": report.total_fixes_applied,
                "standardization_rate": report.summary.get("standardization_rate", 0),
                "issue_breakdown": report.summary.get("issue_breakdown", {}),
                "results": [
                    {
                        "service_name": result.service_name,
                        "success": result.success,
                        "changes_made": result.changes_made,
                        "warnings": result.warnings,
                        "errors": result.errors
                    } for result in report.results
                ]
            }
        except Exception as e:
            logger.error(f"❌ Configuration standardization failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "services_processed": 0,
                "results": []
            }

    async def standardize_docker_configs(self, mode: str = "validate") -> Dict[str, Any]:
        """Standardize all Docker configurations."""
        logger.info(f"🐳 Standardizing Docker configurations (mode: {mode})")

        try:
            # Convert string mode to enum
            mode_map = {
                "validate": StandardizationMode.VALIDATE_ONLY,
                "dry_run": StandardizationMode.DRY_RUN,
                "apply": StandardizationMode.APPLY_CHANGES
            }
            standardization_mode = mode_map.get(mode, StandardizationMode.VALIDATE_ONLY)

            report = self.docker_standardizer.standardize_docker_configs(standardization_mode)

            return {
                "success": True,
                "files_processed": report.files_processed,
                "files_modified": report.files_modified,
                "issues_found": report.issues_found,
                "issues_fixed": report.issues_fixed,
                "validation_errors": report.validation_errors,
                "pydantic_validation_passed": report.pydantic_validation_passed,
                "issues": [
                    {
                        "service": issue.service_name,
                        "type": issue.issue_type,
                        "severity": issue.severity,
                        "description": issue.description,
                        "can_auto_fix": issue.can_auto_fix
                    } for issue in report.issues
                ]
            }
        except Exception as e:
            logger.error(f"❌ Docker standardization failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "files_processed": 0,
                "issues": []
            }

    async def detect_config_inconsistencies(self) -> List[Dict[str, Any]]:
        """Detect Docker configuration inconsistencies"""
        inconsistencies = self.config_validator.detect_config_inconsistencies()
        return [{
            "service_name": i.service_name,
            "inconsistency_type": i.inconsistency_type,
            "description": i.description,
            "severity": i.severity,
            "suggested_fix": i.suggested_fix
        } for i in inconsistencies]

    async def resolve_config_inconsistencies(self) -> Dict[str, Any]:
        """Automatically resolve configuration inconsistencies"""
        logger.info("🔧 Starting automatic configuration inconsistency resolution")

        # Detect inconsistencies
        inconsistencies = self.config_validator.detect_config_inconsistencies()

        if not inconsistencies:
            return {"status": "no_inconsistencies", "message": "No configuration inconsistencies detected"}

        # Group fixes by service
        fixes_by_service = {}
        for inconsistency in inconsistencies:
            if inconsistency.service_name not in fixes_by_service:
                fixes_by_service[inconsistency.service_name] = {}
            fixes_by_service[inconsistency.service_name][inconsistency.inconsistency_type] = inconsistency.suggested_fix

        # Apply fixes
        applied_fixes = self.config_validator.apply_configuration_fixes(fixes_by_service)

        return {
            "status": "resolved",
            "inconsistencies_found": len(inconsistencies),
            "fixes_applied": len(applied_fixes),
            "details": applied_fixes
        }

    # Service Configuration Management Methods
    async def sync_service_configs(self) -> Dict[str, Any]:
        """Sync configurations from all service endpoints"""
        return await self.config_manager.sync_all_service_configs()

    async def get_service_config(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get current configuration for a service"""
        config_snapshot = self.config_manager.get_latest_service_config(service_name)
        if config_snapshot:
            return {
                "service_name": config_snapshot.service_name,
                "config_hash": config_snapshot.config_hash,
                "config_data": config_snapshot.config_data,
                "timestamp": config_snapshot.timestamp.isoformat(),
                "source": config_snapshot.source
            }
        return None

    async def export_service_config(self, service_name: str, format: str = "json") -> Optional[str]:
        """Export a service's configuration"""
        return self.config_manager.export_service_config(service_name, format)

    async def export_all_configs(self, format: str = "json") -> Dict[str, str]:
        """Export all service configurations"""
        return self.config_manager.export_all_configs(format)

    async def compare_service_configs(self, service_name: str) -> Dict[str, Any]:
        """Compare current and previous configurations for a service"""
        return self.config_manager.compare_service_configs(service_name)

    async def get_service_config_history(self, service_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get configuration history for a service"""
        snapshots = self.config_manager.get_service_config_history(service_name, limit)
        return [{
            "id": s.id,
            "service_name": s.service_name,
            "config_hash": s.config_hash,
            "timestamp": s.timestamp.isoformat(),
            "source": s.source,
            "config_data": s.config_data
        } for s in snapshots]
