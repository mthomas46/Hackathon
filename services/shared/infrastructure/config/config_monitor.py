#!/usr/bin/env python3
"""
Configuration Monitoring and Metrics

Provides comprehensive monitoring, metrics, and analytics for the configuration system.
Tracks configuration loading, validation performance, and system health.
"""

import time
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import os

# Add project root to path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from services.shared.infrastructure.config.configuration_manager import USE_PYDANTIC_CONFIG, PYDANTIC_AVAILABLE


@dataclass
class ConfigMetric:
    """Individual configuration metric."""
    name: str
    value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class ConfigLoadEvent:
    """Configuration loading event."""
    service_name: str
    config_type: str  # 'pydantic' or 'dataclass'
    load_time: float
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    config_size: int = 0  # Number of configuration fields
    validation_errors: int = 0


@dataclass
class ServiceHealth:
    """Service configuration health status."""
    service_name: str
    last_check: datetime
    status: str  # 'healthy', 'warning', 'error'
    config_age: float  # Hours since last config change
    validation_issues: int
    load_count: int
    avg_load_time: float
    pydantic_enabled: bool


class ConfigurationMonitor:
    """
    Monitors configuration system performance and health.

    Provides metrics, alerts, and insights into configuration usage across the ecosystem.
    """

    def __init__(self, metrics_interval: int = 60):
        self.metrics_interval = metrics_interval  # seconds
        self.metrics: List[ConfigMetric] = []
        self.load_events: List[ConfigLoadEvent] = []
        self.service_health: Dict[str, ServiceHealth] = {}
        self.alerts: List[Dict[str, Any]] = []
        self.monitoring_enabled = True
        self._lock = threading.Lock()

        # Start background monitoring
        self._start_monitoring()

    def _start_monitoring(self):
        """Start background monitoring thread."""
        if not self.monitoring_enabled:
            return

        def monitor_loop():
            while self.monitoring_enabled:
                try:
                    self._collect_system_metrics()
                    self._check_service_health()
                    self._cleanup_old_data()
                except Exception as e:
                    print(f"Configuration monitoring error: {e}")

                time.sleep(self.metrics_interval)

        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()

    def record_config_load(self, service_name: str, config_type: str, load_time: float,
                          success: bool, error_message: Optional[str] = None,
                          config_size: int = 0, validation_errors: int = 0):
        """Record a configuration loading event."""
        with self._lock:
            event = ConfigLoadEvent(
                service_name=service_name,
                config_type=config_type,
                load_time=load_time,
                success=success,
                error_message=error_message,
                config_size=config_size,
                validation_errors=validation_errors
            )
            self.load_events.append(event)

            # Update service health
            self._update_service_health(service_name, event)

            # Check for alerts
            self._check_for_alerts(event)

    def _update_service_health(self, service_name: str, event: ConfigLoadEvent):
        """Update service health based on loading event."""
        if service_name not in self.service_health:
            self.service_health[service_name] = ServiceHealth(
                service_name=service_name,
                last_check=event.timestamp,
                status='unknown',
                config_age=0.0,
                validation_issues=0,
                load_count=0,
                avg_load_time=0.0,
                pydantic_enabled=(event.config_type == 'pydantic')
            )

        health = self.service_health[service_name]
        health.last_check = event.timestamp
        health.load_count += 1
        health.validation_issues = event.validation_errors

        # Update average load time
        if health.load_count == 1:
            health.avg_load_time = event.load_time
        else:
            health.avg_load_time = (health.avg_load_time * (health.load_count - 1) + event.load_time) / health.load_count

        # Determine status
        if not event.success:
            health.status = 'error'
        elif event.validation_errors > 0:
            health.status = 'warning'
        else:
            health.status = 'healthy'

    def _check_for_alerts(self, event: ConfigLoadEvent):
        """Check for alert conditions based on loading event."""
        alerts = []

        # Slow loading alert
        if event.load_time > 2.0:  # More than 2 seconds
            alerts.append({
                'type': 'slow_config_load',
                'service': event.service_name,
                'message': f'Slow configuration load: {event.load_time:.2f}s',
                'severity': 'warning',
                'timestamp': event.timestamp
            })

        # Failed loading alert
        if not event.success:
            alerts.append({
                'type': 'config_load_failure',
                'service': event.service_name,
                'message': f'Configuration load failed: {event.error_message}',
                'severity': 'error',
                'timestamp': event.timestamp
            })

        # Validation errors alert
        if event.validation_errors > 0:
            alerts.append({
                'type': 'config_validation_errors',
                'service': event.service_name,
                'message': f'Configuration validation errors: {event.validation_errors}',
                'severity': 'warning',
                'timestamp': event.timestamp
            })

        self.alerts.extend(alerts)

        # Keep only recent alerts (last 24 hours)
        cutoff = datetime.now() - timedelta(hours=24)
        self.alerts = [a for a in self.alerts if a['timestamp'] > cutoff]

    def _collect_system_metrics(self):
        """Collect system-wide configuration metrics."""
        with self._lock:
            now = datetime.now()

            # Pydantic adoption metrics
            pydantic_services = sum(1 for h in self.service_health.values() if h.pydantic_enabled)
            total_services = len(self.service_health)

            self.metrics.append(ConfigMetric(
                name='config_system_pydantic_adoption',
                value=pydantic_services / max(total_services, 1),
                timestamp=now,
                tags={'total_services': str(total_services), 'pydantic_services': str(pydantic_services)}
            ))

            # Load performance metrics
            if self.load_events:
                recent_events = [e for e in self.load_events if (now - e.timestamp).seconds < 3600]  # Last hour
                if recent_events:
                    avg_load_time = sum(e.load_time for e in recent_events) / len(recent_events)
                    success_rate = sum(1 for e in recent_events if e.success) / len(recent_events)

                    self.metrics.append(ConfigMetric(
                        name='config_system_avg_load_time',
                        value=avg_load_time,
                        timestamp=now,
                        tags={'events_count': str(len(recent_events))}
                    ))

                    self.metrics.append(ConfigMetric(
                        name='config_system_success_rate',
                        value=success_rate,
                        timestamp=now,
                        tags={'events_count': str(len(recent_events))}
                    ))

            # Service health metrics
            for service_name, health in self.service_health.items():
                self.metrics.append(ConfigMetric(
                    name='config_service_status',
                    value=1 if health.status == 'healthy' else 0,
                    timestamp=now,
                    tags={
                        'service': service_name,
                        'status': health.status,
                        'pydantic_enabled': str(health.pydantic_enabled)
                    }
                ))

    def _check_service_health(self):
        """Check overall service health and update status."""
        with self._lock:
            now = datetime.now()

            for service_name, health in self.service_health.items():
                # Check if service hasn't been seen recently (stale config)
                time_since_check = (now - health.last_check).total_seconds()
                if time_since_check > 3600:  # More than 1 hour
                    health.status = 'stale'

                # Update config age (would need file monitoring in real implementation)
                health.config_age = time_since_check / 3600  # hours

    def _cleanup_old_data(self):
        """Clean up old metrics and events."""
        with self._lock:
            cutoff = datetime.now() - timedelta(hours=24)

            # Keep only recent metrics (last 24 hours)
            self.metrics = [m for m in self.metrics if m.timestamp > cutoff]

            # Keep only recent events (last 24 hours)
            self.load_events = [e for e in self.load_events if e.timestamp > cutoff]

    def get_service_health_report(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive service health report."""
        with self._lock:
            if service_name:
                health = self.service_health.get(service_name)
                if not health:
                    return {'error': f'Service {service_name} not found'}

                return {
                    'service_name': health.service_name,
                    'status': health.status,
                    'last_check': health.last_check.isoformat(),
                    'config_age_hours': health.config_age,
                    'validation_issues': health.validation_issues,
                    'load_count': health.load_count,
                    'avg_load_time': health.avg_load_time,
                    'pydantic_enabled': health.pydantic_enabled
                }

            # System-wide report
            total_services = len(self.service_health)
            healthy_services = sum(1 for h in self.service_health.values() if h.status == 'healthy')
            pydantic_services = sum(1 for h in self.service_health.values() if h.pydantic_enabled)

            return {
                'total_services': total_services,
                'healthy_services': healthy_services,
                'pydantic_services': pydantic_services,
                'pydantic_adoption_rate': pydantic_services / max(total_services, 1),
                'services': {name: self.get_service_health_report(name) for name in self.service_health.keys()},
                'recent_alerts': self.alerts[-10:]  # Last 10 alerts
            }

    def get_performance_report(self) -> Dict[str, Any]:
        """Get configuration performance report."""
        with self._lock:
            if not self.load_events:
                return {'error': 'No load events recorded'}

            now = datetime.now()
            recent_events = [e for e in self.load_events if (now - e.timestamp).seconds < 3600]  # Last hour

            if not recent_events:
                return {'error': 'No recent load events'}

            total_loads = len(recent_events)
            successful_loads = sum(1 for e in recent_events if e.success)
            avg_load_time = sum(e.load_time for e in recent_events) / total_loads
            max_load_time = max(e.load_time for e in recent_events)
            min_load_time = min(e.load_time for e in recent_events)

            # Group by config type
            pydantic_events = [e for e in recent_events if e.config_type == 'pydantic']
            dataclass_events = [e for e in recent_events if e.config_type == 'dataclass']

            return {
                'time_period': 'last_hour',
                'total_loads': total_loads,
                'successful_loads': successful_loads,
                'success_rate': successful_loads / total_loads,
                'avg_load_time': avg_load_time,
                'max_load_time': max_load_time,
                'min_load_time': min_load_time,
                'pydantic_loads': len(pydantic_events),
                'dataclass_loads': len(dataclass_events),
                'pydantic_avg_time': sum(e.load_time for e in pydantic_events) / max(len(pydantic_events), 1),
                'dataclass_avg_time': sum(e.load_time for e in dataclass_events) / max(len(dataclass_events), 1)
            }

    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format."""
        with self._lock:
            data = {
                'timestamp': datetime.now().isoformat(),
                'system_health': self.get_service_health_report(),
                'performance': self.get_performance_report(),
                'recent_metrics': [
                    {
                        'name': m.name,
                        'value': m.value,
                        'timestamp': m.timestamp.isoformat(),
                        'tags': m.tags
                    } for m in self.metrics[-100:]  # Last 100 metrics
                ],
                'recent_alerts': self.alerts[-50:]  # Last 50 alerts
            }

            if format == 'json':
                return json.dumps(data, indent=2, default=str)
            else:
                return str(data)


# Global monitor instance
_config_monitor = None

def get_config_monitor() -> ConfigurationMonitor:
    """Get the global configuration monitor instance."""
    global _config_monitor
    if _config_monitor is None:
        _config_monitor = ConfigurationMonitor()
    return _config_monitor


def record_config_load(service_name: str, config_type: str, load_time: float,
                      success: bool, error_message: Optional[str] = None,
                      config_size: int = 0, validation_errors: int = 0):
    """Convenience function to record configuration loading."""
    monitor = get_config_monitor()
    monitor.record_config_load(
        service_name=service_name,
        config_type=config_type,
        load_time=load_time,
        success=success,
        error_message=error_message,
        config_size=config_size,
        validation_errors=validation_errors
    )


# Integration with existing configuration system
def patch_config_loading():
    """Patch the configuration loading to include monitoring."""
    from services.shared.infrastructure.config import configuration_manager

    original_load_service_config = configuration_manager.load_service_config

    def monitored_load_service_config(service_name: str, **kwargs):
        start_time = time.time()
        config_type = 'pydantic' if configuration_manager.USE_PYDANTIC_CONFIG else 'dataclass'

        try:
            config = original_load_service_config(service_name, **kwargs)
            load_time = time.time() - start_time

            # Count config fields (approximate)
            config_size = getattr(config, '__dict__', {})
            if hasattr(config_size, '__len__'):
                config_size = len(config_size)
            else:
                config_size = len(dir(config))

            # Count validation issues (if available)
            validation_errors = 0
            if hasattr(config, 'validate_configuration'):
                try:
                    issues = config.validate_configuration()
                    validation_errors = len(issues) if isinstance(issues, list) else 0
                except:
                    validation_errors = 0

            record_config_load(
                service_name=service_name,
                config_type=config_type,
                load_time=load_time,
                success=True,
                config_size=config_size,
                validation_errors=validation_errors
            )

            return config

        except Exception as e:
            load_time = time.time() - start_time
            record_config_load(
                service_name=service_name,
                config_type=config_type,
                load_time=load_time,
                success=False,
                error_message=str(e)
            )
            raise

    # Replace the function
    configuration_manager.load_service_config = monitored_load_service_config


if __name__ == "__main__":
    # Test the monitoring system
    print("🧪 Testing Configuration Monitoring System")
    print("=" * 50)

    # Initialize monitoring
    monitor = get_config_monitor()

    # Simulate some config loads
    record_config_load('test-service', 'pydantic', 0.1, True, config_size=15)
    record_config_load('orchestrator', 'pydantic', 0.2, True, config_size=25)
    record_config_load('analysis-service', 'pydantic', 0.15, True, config_size=20, validation_errors=0)
    record_config_load('doc_store', 'pydantic', 0.12, True, config_size=18)
    record_config_load('legacy-service', 'dataclass', 0.3, True, config_size=12)
    record_config_load('failing-service', 'pydantic', 2.5, False, error_message='Validation failed')

    # Give monitoring time to collect metrics
    time.sleep(2)

    # Print reports
    print("\n📊 Service Health Report:")
    health_report = monitor.get_service_health_report()
    print(json.dumps(health_report, indent=2, default=str))

    print("\n⚡ Performance Report:")
    perf_report = monitor.get_performance_report()
    print(json.dumps(perf_report, indent=2, default=str))

    print("\n🚨 Recent Alerts:")
    for alert in monitor.alerts[-5:]:
        print(f"  • {alert['type']}: {alert['message']} ({alert['severity']})")

    print("\n✅ Configuration monitoring system test completed!")
