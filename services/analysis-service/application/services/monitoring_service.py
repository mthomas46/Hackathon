"""Application Monitoring Service - Metrics collection and performance monitoring."""

import asyncio
import psutil
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque

from .application_service import ApplicationService, ServiceContext


class ApplicationMetrics:
    """Application metrics collector."""

    def __init__(self, max_samples: int = 1000):
        """Initialize metrics collector."""
        self.max_samples = max_samples
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_samples))
        self.timers: Dict[str, List[float]] = defaultdict(list)

        # Start time for uptime calculation
        self.start_time = time.time()

    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter."""
        self.counters[name] += value

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge value."""
        self.gauges[name] = value

    def record_histogram(self, name: str, value: float) -> None:
        """Record a histogram value."""
        self.histograms[name].append(value)

    def start_timer(self, name: str) -> str:
        """Start a timer and return timer ID."""
        timer_id = f"{name}_{int(time.time() * 1000000)}"
        self.timers[timer_id] = [time.time()]
        return timer_id

    def stop_timer(self, timer_id: str) -> float:
        """Stop a timer and return duration."""
        if timer_id in self.timers:
            start_time = self.timers[timer_id][0]
            duration = time.time() - start_time
            self.record_histogram(timer_id.split('_')[0], duration)
            del self.timers[timer_id]
            return duration
        return 0.0

    def time_execution(self, name: str):
        """Decorator to time function execution."""
        def decorator(func):
            async def async_wrapper(*args, **kwargs):
                timer_id = self.start_timer(name)
                try:
                    return await func(*args, **kwargs)
                finally:
                    self.stop_timer(timer_id)

            def sync_wrapper(*args, **kwargs):
                timer_id = self.start_timer(name)
                try:
                    return func(*args, **kwargs)
                finally:
                    self.stop_timer(timer_id)

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def get_counter(self, name: str) -> int:
        """Get counter value."""
        return self.counters.get(name, 0)

    def get_gauge(self, name: str) -> float:
        """Get gauge value."""
        return self.gauges.get(name, 0.0)

    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics."""
        values = list(self.histograms.get(name, []))
        if not values:
            return {'count': 0, 'mean': 0.0, 'min': 0.0, 'max': 0.0}

        return {
            'count': len(values),
            'mean': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'p50': self._percentile(values, 50),
            'p95': self._percentile(values, 95),
            'p99': self._percentile(values, 99)
        }

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile from values."""
        if not values:
            return 0.0

        values_sorted = sorted(values)
        k = (len(values_sorted) - 1) * (percentile / 100)
        f = int(k)
        c = k - f

        if f + 1 < len(values_sorted):
            return values_sorted[f] + c * (values_sorted[f + 1] - values_sorted[f])
        else:
            return values_sorted[f]

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        return {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'histograms': {name: self.get_histogram_stats(name) for name in self.histograms},
            'uptime_seconds': time.time() - self.start_time
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.timers.clear()
        self.start_time = time.time()


class MonitoringService(ApplicationService):
    """Application monitoring service with metrics collection."""

    def __init__(self, metrics: Optional[ApplicationMetrics] = None, collection_interval: int = 30):
        """Initialize monitoring service."""
        super().__init__("monitoring_service")
        self.metrics = metrics or ApplicationMetrics()
        self.collection_interval = collection_interval
        self._collection_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start monitoring service."""
        await super().start()

        # Start metrics collection task
        self._collection_task = asyncio.create_task(self._collect_system_metrics())

    async def stop(self) -> None:
        """Stop monitoring service."""
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass

        await super().stop()

    async def _collect_system_metrics(self) -> None:
        """Collect system metrics periodically."""
        while self._running:
            try:
                await asyncio.sleep(self.collection_interval)

                # CPU metrics
                self.metrics.set_gauge('system_cpu_percent', psutil.cpu_percent(interval=1))

                # Memory metrics
                memory = psutil.virtual_memory()
                self.metrics.set_gauge('system_memory_percent', memory.percent)
                self.metrics.set_gauge('system_memory_used_mb', memory.used / 1024 / 1024)
                self.metrics.set_gauge('system_memory_available_mb', memory.available / 1024 / 1024)

                # Disk metrics
                disk = psutil.disk_usage('/')
                self.metrics.set_gauge('system_disk_percent', disk.percent)
                self.metrics.set_gauge('system_disk_used_gb', disk.used / 1024 / 1024 / 1024)
                self.metrics.set_gauge('system_disk_free_gb', disk.free / 1024 / 1024 / 1024)

                # Network metrics (basic)
                net = psutil.net_io_counters()
                if net:
                    self.metrics.set_gauge('system_network_bytes_sent', net.bytes_sent)
                    self.metrics.set_gauge('system_network_bytes_recv', net.bytes_recv)

                # Process metrics
                process = psutil.Process()
                self.metrics.set_gauge('process_cpu_percent', process.cpu_percent())
                self.metrics.set_gauge('process_memory_mb', process.memory_info().rss / 1024 / 1024)
                self.metrics.set_gauge('process_threads', process.num_threads())

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error collecting system metrics: {e}")

    async def record_operation_start(self, operation: str, context: Optional[ServiceContext] = None) -> str:
        """Record operation start."""
        timer_id = self.metrics.start_timer(operation)

        self.metrics.increment_counter(f"operation_{operation}_started")

        async with self.operation_context("record_operation_start", context):
            self.logger.debug(f"Operation started: {operation}", extra={
                'operation': operation,
                'correlation_id': context.correlation_id if context else None
            })

        return timer_id

    async def record_operation_end(
        self,
        operation: str,
        timer_id: str,
        success: bool = True,
        context: Optional[ServiceContext] = None
    ) -> None:
        """Record operation end."""
        duration = self.metrics.stop_timer(timer_id)

        if success:
            self.metrics.increment_counter(f"operation_{operation}_completed")
        else:
            self.metrics.increment_counter(f"operation_{operation}_failed")

        async with self.operation_context("record_operation_end", context):
            log_level = "info" if success else "warning"
            getattr(self.logger, log_level)(
                f"Operation {'completed' if success else 'failed'}: {operation}",
                extra={
                    'operation': operation,
                    'duration': duration,
                    'success': success,
                    'correlation_id': context.correlation_id if context else None
                }
            )

    async def record_business_metric(
        self,
        metric_name: str,
        value: Any,
        metric_type: str = "counter",
        context: Optional[ServiceContext] = None
    ) -> None:
        """Record business metric."""
        async with self.operation_context("record_business_metric", context):
            if metric_type == "counter" and isinstance(value, (int, float)):
                self.metrics.increment_counter(f"business_{metric_name}", int(value))
            elif metric_type == "gauge" and isinstance(value, (int, float)):
                self.metrics.set_gauge(f"business_{metric_name}", float(value))
            elif metric_type == "histogram" and isinstance(value, (int, float)):
                self.metrics.record_histogram(f"business_{metric_name}", float(value))

            self.logger.debug(f"Business metric recorded: {metric_name} = {value}")

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        all_metrics = self.metrics.get_all_metrics()

        # Calculate derived metrics
        summary = {
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': all_metrics['uptime_seconds'],
            'total_operations': sum(
                count for name, count in all_metrics['counters'].items()
                if name.startswith('operation_') and name.endswith('_started')
            ),
            'successful_operations': sum(
                count for name, count in all_metrics['counters'].items()
                if name.startswith('operation_') and name.endswith('_completed')
            ),
            'failed_operations': sum(
                count for name, count in all_metrics['counters'].items()
                if name.startswith('operation_') and name.endswith('_failed')
            )
        }

        # Calculate success rate
        total_ops = summary['total_operations']
        if total_ops > 0:
            summary['operation_success_rate'] = summary['successful_operations'] / total_ops
        else:
            summary['operation_success_rate'] = 1.0

        # Add system metrics
        summary['system'] = {
            'cpu_percent': self.metrics.get_gauge('system_cpu_percent'),
            'memory_percent': self.metrics.get_gauge('system_memory_percent'),
            'disk_percent': self.metrics.get_gauge('system_disk_percent')
        }

        # Add key histogram stats
        summary['performance'] = {}
        for name in self.metrics.histograms.keys():
            if name.startswith('operation_'):
                summary['performance'][name] = self.metrics.get_histogram_stats(name)

        return summary

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        summary = await self.get_metrics_summary()

        # Determine health status based on metrics
        health_status = "healthy"
        issues = []

        # Check operation success rate
        success_rate = summary['operation_success_rate']
        if success_rate < 0.95:  # Less than 95% success rate
            health_status = "degraded"
            issues.append(f"Low operation success rate: {success_rate:.2%}")

        # Check system resource usage
        if summary['system']['cpu_percent'] > 90:
            health_status = "critical"
            issues.append(f"High CPU usage: {summary['system']['cpu_percent']}%")

        if summary['system']['memory_percent'] > 90:
            health_status = "critical"
            issues.append(f"High memory usage: {summary['system']['memory_percent']}%")

        if summary['system']['disk_percent'] > 95:
            health_status = "critical"
            issues.append(f"Low disk space: {100 - summary['system']['disk_percent']}% free")

        return {
            'status': health_status,
            'issues': issues,
            'metrics': summary,
            'timestamp': datetime.utcnow().isoformat()
        }

    async def reset_metrics(self, context: Optional[ServiceContext] = None) -> None:
        """Reset all metrics."""
        async with self.operation_context("reset_metrics", context):
            self.metrics.reset()
            self.logger.info("All metrics reset")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health = await super().health_check()

        # Add monitoring-specific health info
        try:
            health_status = await self.get_health_status()
            health['monitoring'] = {
                'metrics_collected': len(self.metrics.counters) + len(self.metrics.gauges) + len(self.metrics.histograms),
                'system_metrics_enabled': True,
                'collection_interval_seconds': self.collection_interval,
                'health_status': health_status['status']
            }

        except Exception as e:
            health['monitoring'] = {'error': str(e)}

        return health


# Global monitoring service instance
monitoring_service = MonitoringService()

# Create application metrics instance
app_metrics = monitoring_service.metrics
