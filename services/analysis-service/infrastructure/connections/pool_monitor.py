"""Connection Pool Monitor - Monitoring and alerting for connection pool health."""

import asyncio
import threading
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class PoolHealthMetrics:
    """Health metrics for connection pools."""
    pool_name: str
    status: HealthStatus
    timestamp: datetime
    active_connections: int
    idle_connections: int
    total_connections: int
    connection_utilization: float
    acquire_time_p95: Optional[float] = None
    error_rate: float = 0.0
    last_error: Optional[str] = None
    issues: List[str] = None

    def __post_init__(self):
        """Initialize metrics."""
        if self.issues is None:
            self.issues = []


@dataclass
class PoolHealthCheck:
    """Health check configuration for connection pools."""
    pool_name: str
    enabled: bool = True
    check_interval: int = 30  # seconds
    warning_threshold: float = 0.8  # 80% utilization
    critical_threshold: float = 0.95  # 95% utilization
    max_error_rate: float = 0.1  # 10% error rate
    max_acquire_time: float = 5.0  # 5 seconds
    min_idle_connections: int = 1

    def evaluate_health(self, metrics: PoolHealthMetrics) -> HealthStatus:
        """Evaluate health status based on metrics."""
        if not self.enabled:
            return HealthStatus.UNKNOWN

        # Critical conditions
        if (metrics.connection_utilization >= self.critical_threshold or
            metrics.error_rate >= self.max_error_rate * 2 or
            metrics.idle_connections < 1 or
            (metrics.acquire_time_p95 and metrics.acquire_time_p95 > self.max_acquire_time * 2)):
            return HealthStatus.CRITICAL

        # Warning conditions
        if (metrics.connection_utilization >= self.warning_threshold or
            metrics.error_rate >= self.max_error_rate or
            (metrics.acquire_time_p95 and metrics.acquire_time_p95 > self.max_acquire_time)):
            return HealthStatus.WARNING

        return HealthStatus.HEALTHY


class ConnectionPoolMonitor:
    """Monitor for connection pool health and performance."""

    def __init__(self):
        """Initialize connection pool monitor."""
        self.health_checks: Dict[str, PoolHealthCheck] = {}
        self.last_metrics: Dict[str, PoolHealthMetrics] = {}
        self.alert_callbacks: List[Callable] = []
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False

        # Statistics
        self.total_checks = 0
        self.alerts_sent = 0
        self.healthy_pools = 0
        self.warning_pools = 0
        self.critical_pools = 0

    def register_pool(
        self,
        pool_name: str,
        check_config: Optional[PoolHealthCheck] = None
    ) -> None:
        """Register a connection pool for monitoring."""
        if check_config is None:
            check_config = PoolHealthCheck(pool_name=pool_name)

        self.health_checks[pool_name] = check_config

    def unregister_pool(self, pool_name: str) -> None:
        """Unregister a connection pool from monitoring."""
        self.health_checks.pop(pool_name, None)
        self.last_metrics.pop(pool_name, None)

    def add_alert_callback(self, callback: Callable) -> None:
        """Add callback for health alerts."""
        self.alert_callbacks.append(callback)

    def remove_alert_callback(self, callback: Callable) -> None:
        """Remove alert callback."""
        try:
            self.alert_callbacks.remove(callback)
        except ValueError:
            pass

    async def start_monitoring(self) -> None:
        """Start monitoring all registered pools."""
        if self._running:
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self) -> None:
        """Stop monitoring."""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                # Use the minimum check interval
                min_interval = min(
                    (check.check_interval for check in self.health_checks.values() if check.enabled),
                    default=30
                )

                await asyncio.sleep(min_interval)

                # Check all pools
                for pool_name, check_config in self.health_checks.items():
                    if check_config.enabled:
                        await self._check_pool_health(pool_name, check_config)

                self.total_checks += 1

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")

    async def _check_pool_health(
        self,
        pool_name: str,
        check_config: PoolHealthCheck
    ) -> None:
        """Check health of a specific pool."""
        try:
            # Get pool metrics (this would need to be implemented per pool type)
            metrics = await self._collect_pool_metrics(pool_name)

            if metrics:
                # Evaluate health
                health_status = check_config.evaluate_health(metrics)

                # Update statistics
                self._update_health_stats(health_status)

                # Store metrics
                self.last_metrics[pool_name] = metrics

                # Check for status changes and send alerts
                await self._check_for_alerts(pool_name, metrics, health_status)

        except Exception as e:
            print(f"Error checking pool {pool_name}: {e}")

    async def _collect_pool_metrics(self, pool_name: str) -> Optional[PoolHealthMetrics]:
        """Collect metrics for a pool."""
        # This is a placeholder - actual implementation would depend on pool type
        # In a real implementation, this would query the actual pool for metrics

        # For now, return mock metrics
        return PoolHealthMetrics(
            pool_name=pool_name,
            status=HealthStatus.UNKNOWN,
            timestamp=datetime.utcnow(),
            active_connections=5,
            idle_connections=3,
            total_connections=8,
            connection_utilization=0.625,  # 62.5%
            acquire_time_p95=0.5,
            error_rate=0.02,
            issues=[]
        )

    def _update_health_stats(self, status: HealthStatus) -> None:
        """Update health statistics."""
        # Reset counters
        self.healthy_pools = 0
        self.warning_pools = 0
        self.critical_pools = 0

        # Count current status
        for metrics in self.last_metrics.values():
            if metrics.status == HealthStatus.HEALTHY:
                self.healthy_pools += 1
            elif metrics.status == HealthStatus.WARNING:
                self.warning_pools += 1
            elif metrics.status == HealthStatus.CRITICAL:
                self.critical_pools += 1

    async def _check_for_alerts(
        self,
        pool_name: str,
        metrics: PoolHealthMetrics,
        new_status: HealthStatus
    ) -> None:
        """Check for status changes and send alerts."""
        previous_metrics = self.last_metrics.get(pool_name)

        if previous_metrics and previous_metrics.status != new_status:
            # Status changed - send alert
            alert_data = {
                'pool_name': pool_name,
                'previous_status': previous_metrics.status.value,
                'new_status': new_status.value,
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': {
                    'active_connections': metrics.active_connections,
                    'idle_connections': metrics.idle_connections,
                    'connection_utilization': metrics.connection_utilization,
                    'error_rate': metrics.error_rate
                },
                'issues': metrics.issues
            }

            # Send alerts to all callbacks
            for callback in self.alert_callbacks:
                try:
                    await callback(alert_data)
                except Exception as e:
                    print(f"Error in alert callback: {e}")

            self.alerts_sent += 1

    def get_pool_health(self, pool_name: str) -> Optional[PoolHealthMetrics]:
        """Get current health metrics for a pool."""
        return self.last_metrics.get(pool_name)

    def get_all_pool_health(self) -> Dict[str, PoolHealthMetrics]:
        """Get health metrics for all pools."""
        return self.last_metrics.copy()

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        return {
            'total_checks': self.total_checks,
            'alerts_sent': self.alerts_sent,
            'healthy_pools': self.healthy_pools,
            'warning_pools': self.warning_pools,
            'critical_pools': self.critical_pools,
            'total_monitored_pools': len(self.health_checks),
            'enabled_checks': sum(1 for check in self.health_checks.values() if check.enabled)
        }

    def reset_stats(self) -> None:
        """Reset monitoring statistics."""
        self.total_checks = 0
        self.alerts_sent = 0
        self.healthy_pools = 0
        self.warning_pools = 0
        self.critical_pools = 0


class AlertManager:
    """Manager for handling and routing alerts."""

    def __init__(self):
        """Initialize alert manager."""
        self.alert_handlers: Dict[str, List[Callable]] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000

    def register_handler(self, alert_type: str, handler: Callable) -> None:
        """Register alert handler."""
        if alert_type not in self.alert_handlers:
            self.alert_handlers[alert_type] = []
        self.alert_handlers[alert_type].append(handler)

    def unregister_handler(self, alert_type: str, handler: Callable) -> None:
        """Unregister alert handler."""
        if alert_type in self.alert_handlers:
            try:
                self.alert_handlers[alert_type].remove(handler)
            except ValueError:
                pass

    async def handle_alert(self, alert_data: Dict[str, Any]) -> None:
        """Handle incoming alert."""
        alert_type = alert_data.get('alert_type', 'pool_health')

        # Store in history
        self.alert_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'type': alert_type,
            'data': alert_data
        })

        # Maintain history size
        if len(self.alert_history) > self.max_history_size:
            self.alert_history.pop(0)

        # Route to handlers
        if alert_type in self.alert_handlers:
            for handler in self.alert_handlers[alert_type]:
                try:
                    await handler(alert_data)
                except Exception as e:
                    print(f"Error in alert handler: {e}")

    def get_alert_history(
        self,
        alert_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get alert history."""
        history = self.alert_history

        if alert_type:
            history = [alert for alert in history if alert['type'] == alert_type]

        return history[-limit:]

    def clear_history(self) -> None:
        """Clear alert history."""
        self.alert_history.clear()


# Global instances
pool_monitor = ConnectionPoolMonitor()
alert_manager = AlertManager()


class PoolMonitorService:
    """Service for monitoring connection pools with alert integration."""

    def __init__(
        self,
        pool_monitor: ConnectionPoolMonitor,
        alert_manager: AlertManager
    ):
        """Initialize pool monitor service."""
        self.pool_monitor = pool_monitor
        self.alert_manager = alert_manager
        self._started = False

    async def start(self) -> None:
        """Start the pool monitor service."""
        if not self._started:
            # Register alert handler
            await self.alert_manager.register_handler(
                'pool_health',
                self._handle_pool_alert
            )

            await self.pool_monitor.start_monitoring()
            self._started = True
            print("Connection Pool Monitor Service started")

    async def stop(self) -> None:
        """Stop the pool monitor service."""
        if self._started:
            await self.pool_monitor.stop_monitoring()
            self._started = False
            print("Connection Pool Monitor Service stopped")

    async def _handle_pool_alert(self, alert_data: Dict[str, Any]) -> None:
        """Handle pool health alerts."""
        print(f"Pool Alert: {alert_data['pool_name']} - {alert_data['new_status']}")

        # Here you could integrate with notification systems
        # For example, send email, Slack message, etc.

    def register_pool_for_monitoring(
        self,
        pool_name: str,
        warning_threshold: float = 0.8,
        critical_threshold: float = 0.95
    ) -> None:
        """Register a pool for monitoring."""
        health_check = PoolHealthCheck(
            pool_name=pool_name,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold
        )

        self.pool_monitor.register_pool(pool_name, health_check)

    async def get_service_status(self) -> Dict[str, Any]:
        """Get service status and metrics."""
        return {
            'service_started': self._started,
            'monitoring_stats': self.pool_monitor.get_monitoring_stats(),
            'pool_health': {
                name: {
                    'status': metrics.status.value,
                    'utilization': metrics.connection_utilization,
                    'active': metrics.active_connections,
                    'idle': metrics.idle_connections
                }
                for name, metrics in self.pool_monitor.get_all_pool_health().items()
            },
            'recent_alerts': self.alert_manager.get_alert_history(limit=10)
        }


# Global pool monitor service instance
pool_monitor_service = PoolMonitorService(pool_monitor, alert_manager)
