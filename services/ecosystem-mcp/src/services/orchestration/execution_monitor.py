"""
Execution Monitor

Real-time monitoring of execution performance, resource usage, and anomaly detection.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import psutil
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot."""
    timestamp: str
    
    # CPU metrics
    cpu_percent: float
    cpu_count: int
    
    # Memory metrics
    memory_used_mb: float
    memory_available_mb: float
    memory_percent: float
    
    # Execution metrics
    active_sub_jobs: int
    completed_sub_jobs: int
    failed_sub_jobs: int
    
    # Throughput metrics
    files_per_second: float
    sub_jobs_per_minute: float
    
    # Processing metrics
    avg_processing_time_per_file: Optional[float] = None
    avg_processing_time_per_sub_job: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AnomalyAlert:
    """Anomaly detection alert."""
    timestamp: str
    severity: str  # 'warning', 'critical'
    category: str  # 'memory', 'cpu', 'throughput', 'errors'
    message: str
    metric_value: float
    threshold_value: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class ExecutionMonitor:
    """
    Monitors execution performance and detects anomalies.
    
    Features:
    - Real-time performance metrics collection
    - Resource usage tracking (CPU, memory)
    - Throughput monitoring
    - Anomaly detection
    - Alert generation
    - Historical metrics storage
    """
    
    def __init__(
        self,
        collection_interval: float = 5.0,
        history_size: int = 100,
        enable_anomaly_detection: bool = True
    ):
        """
        Initialize execution monitor.
        
        Args:
            collection_interval: Metrics collection interval in seconds
            history_size: Number of historical metrics to keep
            enable_anomaly_detection: Enable anomaly detection
        """
        self.collection_interval = collection_interval
        self.history_size = history_size
        self.enable_anomaly_detection = enable_anomaly_detection
        
        # Metrics history
        self.metrics_history: deque = deque(maxlen=history_size)
        self.alerts_history: deque = deque(maxlen=100)
        
        # Monitoring state
        self.monitoring_active: Dict[str, bool] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        
        # Execution tracking
        self.plan_start_times: Dict[str, datetime] = {}
        self.plan_file_counts: Dict[str, Dict[str, int]] = {}
        self.plan_sub_job_counts: Dict[str, Dict[str, int]] = {}
        
        # Anomaly thresholds
        self.thresholds = {
            "cpu_percent": 90.0,
            "memory_percent": 85.0,
            "error_rate": 0.2,  # 20% error rate
            "throughput_drop": 0.5  # 50% drop in throughput
        }
        
        logger.info(f"ExecutionMonitor initialized (interval={collection_interval}s)")
    
    async def start_monitoring(self, plan_id: str) -> None:
        """
        Start monitoring a plan execution.
        
        Args:
            plan_id: Processing plan ID
        """
        if plan_id in self.monitoring_active and self.monitoring_active[plan_id]:
            logger.warning(f"Monitoring already active for plan {plan_id}")
            return
        
        logger.info(f"📊 Starting monitoring for plan {plan_id}")
        
        self.monitoring_active[plan_id] = True
        self.plan_start_times[plan_id] = datetime.utcnow()
        self.plan_file_counts[plan_id] = {
            "processed": 0,
            "failed": 0,
            "skipped": 0
        }
        self.plan_sub_job_counts[plan_id] = {
            "active": 0,
            "completed": 0,
            "failed": 0
        }
        
        # Start monitoring task
        task = asyncio.create_task(self._monitor_loop(plan_id))
        self.monitoring_tasks[plan_id] = task
    
    async def stop_monitoring(self, plan_id: str) -> None:
        """
        Stop monitoring a plan execution.
        
        Args:
            plan_id: Processing plan ID
        """
        if plan_id not in self.monitoring_active:
            return
        
        logger.info(f"🛑 Stopping monitoring for plan {plan_id}")
        
        self.monitoring_active[plan_id] = False
        
        # Cancel monitoring task
        if plan_id in self.monitoring_tasks:
            self.monitoring_tasks[plan_id].cancel()
            try:
                await self.monitoring_tasks[plan_id]
            except asyncio.CancelledError:
                pass
            del self.monitoring_tasks[plan_id]
        
        # Cleanup
        if plan_id in self.plan_start_times:
            del self.plan_start_times[plan_id]
        if plan_id in self.plan_file_counts:
            del self.plan_file_counts[plan_id]
        if plan_id in self.plan_sub_job_counts:
            del self.plan_sub_job_counts[plan_id]
    
    async def update_execution_stats(
        self,
        plan_id: str,
        files_processed: int = 0,
        files_failed: int = 0,
        files_skipped: int = 0,
        sub_jobs_active: int = 0,
        sub_jobs_completed: int = 0,
        sub_jobs_failed: int = 0
    ) -> None:
        """
        Update execution statistics.
        
        Args:
            plan_id: Processing plan ID
            files_processed: Files processed delta
            files_failed: Files failed delta
            files_skipped: Files skipped delta
            sub_jobs_active: Current active sub-jobs
            sub_jobs_completed: Sub-jobs completed delta
            sub_jobs_failed: Sub-jobs failed delta
        """
        if plan_id not in self.plan_file_counts:
            return
        
        # Update file counts
        self.plan_file_counts[plan_id]["processed"] += files_processed
        self.plan_file_counts[plan_id]["failed"] += files_failed
        self.plan_file_counts[plan_id]["skipped"] += files_skipped
        
        # Update sub-job counts
        self.plan_sub_job_counts[plan_id]["active"] = sub_jobs_active
        self.plan_sub_job_counts[plan_id]["completed"] += sub_jobs_completed
        self.plan_sub_job_counts[plan_id]["failed"] += sub_jobs_failed
    
    async def get_current_metrics(self, plan_id: str) -> Optional[PerformanceMetrics]:
        """
        Get current performance metrics.
        
        Args:
            plan_id: Processing plan ID
        
        Returns:
            PerformanceMetrics or None
        """
        if plan_id not in self.plan_file_counts:
            return None
        
        return await self._collect_metrics(plan_id)
    
    async def get_metrics_history(self, plan_id: str, limit: int = 50) -> List[PerformanceMetrics]:
        """
        Get metrics history.
        
        Args:
            plan_id: Processing plan ID
            limit: Maximum number of metrics to return
        
        Returns:
            List of PerformanceMetrics
        """
        # Filter metrics for this plan
        plan_metrics = [
            m for m in self.metrics_history
            if m.get("plan_id") == plan_id
        ]
        
        return plan_metrics[-limit:]
    
    async def get_alerts(self, plan_id: Optional[str] = None, limit: int = 50) -> List[AnomalyAlert]:
        """
        Get anomaly alerts.
        
        Args:
            plan_id: Optional plan ID to filter by
            limit: Maximum number of alerts to return
        
        Returns:
            List of AnomalyAlert
        """
        alerts = list(self.alerts_history)
        
        if plan_id:
            alerts = [a for a in alerts if a.get("plan_id") == plan_id]
        
        return alerts[-limit:]
    
    async def _monitor_loop(self, plan_id: str) -> None:
        """
        Main monitoring loop.
        
        Args:
            plan_id: Processing plan ID
        """
        try:
            while self.monitoring_active.get(plan_id, False):
                # Collect metrics
                metrics = await self._collect_metrics(plan_id)
                
                if metrics:
                    # Store metrics
                    metrics_dict = metrics.to_dict()
                    metrics_dict["plan_id"] = plan_id
                    self.metrics_history.append(metrics_dict)
                    
                    # Detect anomalies
                    if self.enable_anomaly_detection:
                        alerts = await self._detect_anomalies(plan_id, metrics)
                        for alert in alerts:
                            alert_dict = alert.to_dict()
                            alert_dict["plan_id"] = plan_id
                            self.alerts_history.append(alert_dict)
                            logger.warning(f"⚠️  Anomaly detected: {alert.message}")
                
                # Wait for next collection
                await asyncio.sleep(self.collection_interval)
                
        except asyncio.CancelledError:
            logger.debug(f"Monitoring loop cancelled for plan {plan_id}")
        except Exception as e:
            logger.error(f"Monitoring loop error for plan {plan_id}: {e}", exc_info=True)
    
    async def _collect_metrics(self, plan_id: str) -> Optional[PerformanceMetrics]:
        """
        Collect current performance metrics.
        
        Args:
            plan_id: Processing plan ID
        
        Returns:
            PerformanceMetrics or None
        """
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            
            memory = psutil.virtual_memory()
            memory_used_mb = (memory.total - memory.available) / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            memory_percent = memory.percent
            
            # Execution metrics
            file_counts = self.plan_file_counts.get(plan_id, {})
            sub_job_counts = self.plan_sub_job_counts.get(plan_id, {})
            
            # Calculate throughput
            elapsed = (datetime.utcnow() - self.plan_start_times[plan_id]).total_seconds()
            
            files_processed = file_counts.get("processed", 0)
            files_per_second = files_processed / elapsed if elapsed > 0 else 0.0
            
            sub_jobs_completed = sub_job_counts.get("completed", 0)
            sub_jobs_per_minute = (sub_jobs_completed / elapsed * 60) if elapsed > 0 else 0.0
            
            # Calculate averages
            avg_time_per_file = elapsed / files_processed if files_processed > 0 else None
            avg_time_per_sub_job = elapsed / sub_jobs_completed if sub_jobs_completed > 0 else None
            
            return PerformanceMetrics(
                timestamp=datetime.utcnow().isoformat(),
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                memory_percent=memory_percent,
                active_sub_jobs=sub_job_counts.get("active", 0),
                completed_sub_jobs=sub_job_counts.get("completed", 0),
                failed_sub_jobs=sub_job_counts.get("failed", 0),
                files_per_second=files_per_second,
                sub_jobs_per_minute=sub_jobs_per_minute,
                avg_processing_time_per_file=avg_time_per_file,
                avg_processing_time_per_sub_job=avg_time_per_sub_job
            )
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return None
    
    async def _detect_anomalies(
        self,
        plan_id: str,
        metrics: PerformanceMetrics
    ) -> List[AnomalyAlert]:
        """
        Detect anomalies in metrics.
        
        Args:
            plan_id: Processing plan ID
            metrics: Current metrics
        
        Returns:
            List of AnomalyAlert
        """
        alerts = []
        
        # CPU usage anomaly
        if metrics.cpu_percent > self.thresholds["cpu_percent"]:
            alerts.append(AnomalyAlert(
                timestamp=datetime.utcnow().isoformat(),
                severity="warning",
                category="cpu",
                message=f"High CPU usage: {metrics.cpu_percent:.1f}%",
                metric_value=metrics.cpu_percent,
                threshold_value=self.thresholds["cpu_percent"]
            ))
        
        # Memory usage anomaly
        if metrics.memory_percent > self.thresholds["memory_percent"]:
            alerts.append(AnomalyAlert(
                timestamp=datetime.utcnow().isoformat(),
                severity="warning",
                category="memory",
                message=f"High memory usage: {metrics.memory_percent:.1f}%",
                metric_value=metrics.memory_percent,
                threshold_value=self.thresholds["memory_percent"]
            ))
        
        # Error rate anomaly
        total_sub_jobs = metrics.completed_sub_jobs + metrics.failed_sub_jobs
        if total_sub_jobs > 0:
            error_rate = metrics.failed_sub_jobs / total_sub_jobs
            if error_rate > self.thresholds["error_rate"]:
                alerts.append(AnomalyAlert(
                    timestamp=datetime.utcnow().isoformat(),
                    severity="critical",
                    category="errors",
                    message=f"High error rate: {error_rate*100:.1f}%",
                    metric_value=error_rate,
                    threshold_value=self.thresholds["error_rate"]
                ))
        
        # Throughput drop anomaly (compare with recent history)
        if len(self.metrics_history) > 10:
            recent_metrics = [
                m for m in list(self.metrics_history)[-10:]
                if m.get("plan_id") == plan_id
            ]
            
            if recent_metrics:
                avg_throughput = sum(m.get("files_per_second", 0) for m in recent_metrics) / len(recent_metrics)
                
                if avg_throughput > 0 and metrics.files_per_second < avg_throughput * self.thresholds["throughput_drop"]:
                    alerts.append(AnomalyAlert(
                        timestamp=datetime.utcnow().isoformat(),
                        severity="warning",
                        category="throughput",
                        message=f"Throughput drop: {metrics.files_per_second:.2f} files/s (avg: {avg_throughput:.2f})",
                        metric_value=metrics.files_per_second,
                        threshold_value=avg_throughput * self.thresholds["throughput_drop"]
                    ))
        
        return alerts


# Singleton instance
_execution_monitor_instance = None

def get_execution_monitor() -> ExecutionMonitor:
    """Get singleton execution monitor instance."""
    global _execution_monitor_instance
    if _execution_monitor_instance is None:
        _execution_monitor_instance = ExecutionMonitor()
    return _execution_monitor_instance

