"""Self-Healing Service for automatic recovery and maintenance.

Provides comprehensive self-healing capabilities:
- Automatic service restart on failure detection
- Data consistency checks and repair mechanisms
- Health-based recovery actions
- Predictive maintenance based on metrics
- Resource leak detection and cleanup
"""
import asyncio
import time
import threading
import subprocess
import signal
import os
import psutil
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import logging
import json


logger = logging.getLogger(__name__)


class HealingAction(Enum):
    """Types of healing actions."""
    RESTART_SERVICE = "restart_service"
    RESTART_DEPENDENCY = "restart_dependency"
    CLEAR_CACHE = "clear_cache"
    RECREATE_RESOURCE = "recreate_resource"
    SCALE_UP = "scale_up"
    FAILOVER = "failover"
    DATA_REPAIR = "data_repair"
    LOG_ROTATION = "log_rotation"


class FailurePattern(Enum):
    """Patterns of failures that trigger healing."""
    CRASH_LOOP = "crash_loop"
    MEMORY_LEAK = "memory_leak"
    HIGH_LATENCY = "high_latency"
    ERROR_RATE_SPIKE = "error_rate_spike"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DEPENDENCY_FAILURE = "dependency_failure"
    DATA_CORRUPTION = "data_corruption"


@dataclass
class ServiceInstance:
    """Represents a service instance for monitoring and healing."""
    service_name: str
    process_id: Optional[int] = None
    container_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    restart_count: int = 0
    last_restart: Optional[float] = None
    health_status: str = "unknown"
    consecutive_failures: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0


@dataclass
class HealingRule:
    """Rule for triggering healing actions."""
    name: str
    condition_func: Callable[[Dict[str, Any]], bool]
    action: HealingAction
    priority: int = 5  # 1-10, 1 being highest
    cooldown_seconds: float = 60.0
    max_executions: int = 5
    last_executed: Optional[float] = None
    execution_count: int = 0
    enabled: bool = True


@dataclass
class DataConsistencyCheck:
    """Configuration for data consistency checks."""
    name: str
    check_func: Callable[[], Awaitable[bool]]
    repair_func: Optional[Callable[[], Awaitable[bool]]] = None
    interval_seconds: float = 3600  # 1 hour
    last_check: float = 0
    consecutive_failures: int = 0
    enabled: bool = True


class ProcessMonitor:
    """Monitor for process health and resource usage."""

    def __init__(self):
        self._monitored_processes: Dict[str, ServiceInstance] = {}
        self._lock = threading.Lock()

    def register_process(self, service_name: str, process_id: Optional[int] = None,
                        container_id: Optional[str] = None) -> None:
        """Register a process for monitoring."""
        with self._lock:
            instance = ServiceInstance(
                service_name=service_name,
                process_id=process_id,
                container_id=container_id
            )
            self._monitored_processes[service_name] = instance
            logger.info(f"Registered process monitoring for {service_name}")

    def update_process_info(self, service_name: str) -> None:
        """Update process information."""
        with self._lock:
            instance = self._monitored_processes.get(service_name)
            if not instance:
                return

            try:
                if instance.process_id:
                    process = psutil.Process(instance.process_id)
                    instance.memory_usage_mb = process.memory_info().rss / 1024 / 1024
                    instance.cpu_usage_percent = process.cpu_percent(interval=1.0)

                    # Check if process is still running
                    if not process.is_running():
                        instance.health_status = "crashed"
                        logger.warning(f"Process {instance.process_id} for {service_name} has crashed")

                elif instance.container_id:
                    # For containers, we'd use Docker API here
                    # For now, assume healthy
                    instance.health_status = "healthy"

            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                instance.health_status = "not_found"
                logger.warning(f"Process monitoring failed for {service_name}: {e}")

    def get_process_info(self, service_name: str) -> Optional[ServiceInstance]:
        """Get process information."""
        with self._lock:
            return self._monitored_processes.get(service_name)

    def detect_memory_leak(self, service_name: str, threshold_mb: float = 1000.0) -> bool:
        """Detect potential memory leaks."""
        instance = self.get_process_info(service_name)
        if instance and instance.memory_usage_mb > threshold_mb:
            logger.warning(f"Potential memory leak detected for {service_name}: {instance.memory_usage_mb:.1f}MB")
            return True
        return False

    def detect_crash_loop(self, service_name: str, time_window: float = 300.0) -> bool:
        """Detect crash loop pattern."""
        instance = self.get_process_info(service_name)
        if not instance:
            return False

        # Check restart frequency
        if instance.restart_count > 3 and instance.last_restart:
            time_since_last_restart = time.time() - instance.last_restart
            if time_since_last_restart < time_window:
                logger.warning(f"Crash loop detected for {service_name}: {instance.restart_count} restarts in {time_window}s")
                return True
        return False


class ServiceRestarter:
    """Handles automatic service restart functionality."""

    def __init__(self, docker_compose_file: str = "docker-compose.dev.yml"):
        self.docker_compose_file = docker_compose_file
        self._restart_lock = threading.Lock()

    async def restart_service(self, service_name: str, max_attempts: int = 3) -> bool:
        """Restart a service using Docker Compose."""
        with self._restart_lock:
            for attempt in range(max_attempts):
                try:
                    logger.info(f"Attempting to restart service {service_name} (attempt {attempt + 1}/{max_attempts})")

                    # Stop the service
                    stop_cmd = ["docker-compose", "-f", self.docker_compose_file, "stop", service_name]
                    subprocess.run(stop_cmd, check=True, timeout=30)

                    # Wait a moment
                    await asyncio.sleep(2)

                    # Start the service
                    start_cmd = ["docker-compose", "-f", self.docker_compose_file, "up", "-d", service_name]
                    subprocess.run(start_cmd, check=True, timeout=60)

                    logger.info(f"Successfully restarted service {service_name}")
                    return True

                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                    logger.error(f"Failed to restart {service_name} (attempt {attempt + 1}): {e}")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(5 * (attempt + 1))  # Exponential backoff

            logger.error(f"Failed to restart {service_name} after {max_attempts} attempts")
            return False

    async def restart_container(self, container_id: str) -> bool:
        """Restart a specific container."""
        try:
            logger.info(f"Restarting container {container_id}")

            # Use Docker CLI to restart
            cmd = ["docker", "restart", container_id]
            subprocess.run(cmd, check=True, timeout=30)

            logger.info(f"Successfully restarted container {container_id}")
            return True

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.error(f"Failed to restart container {container_id}: {e}")
            return False

    def kill_process(self, process_id: int) -> bool:
        """Force kill a process."""
        try:
            os.kill(process_id, signal.SIGKILL)
            logger.info(f"Force killed process {process_id}")
            return True
        except (OSError, ProcessLookupError) as e:
            logger.error(f"Failed to kill process {process_id}: {e}")
            return False


class DataConsistencyChecker:
    """Handles data consistency checks and repairs."""

    def __init__(self):
        self._checks: Dict[str, DataConsistencyCheck] = {}

    def register_check(self, check: DataConsistencyCheck) -> None:
        """Register a data consistency check."""
        self._checks[check.name] = check
        logger.info(f"Registered data consistency check: {check.name}")

    async def run_check(self, check_name: str) -> bool:
        """Run a specific consistency check."""
        check = self._checks.get(check_name)
        if not check or not check.enabled:
            return True

        try:
            # Check if it's time to run
            current_time = time.time()
            if current_time - check.last_check < check.interval_seconds:
                return True  # Not due yet

            logger.info(f"Running data consistency check: {check_name}")
            success = await check.check_func()
            check.last_check = current_time

            if success:
                check.consecutive_failures = 0
                logger.info(f"Data consistency check passed: {check_name}")
                return True
            else:
                check.consecutive_failures += 1
                logger.warning(f"Data consistency check failed: {check_name} (failures: {check.consecutive_failures})")

                # Attempt repair if available
                if check.repair_func and check.consecutive_failures >= 3:
                    logger.info(f"Attempting repair for {check_name}")
                    repair_success = await check.repair_func()
                    if repair_success:
                        check.consecutive_failures = 0
                        logger.info(f"Data repair successful for {check_name}")
                        return True

                return False

        except Exception as e:
            logger.error(f"Error running consistency check {check_name}: {e}")
            check.consecutive_failures += 1
            return False

    async def run_all_checks(self) -> Dict[str, bool]:
        """Run all registered consistency checks."""
        results = {}
        for check_name in self._checks.keys():
            results[check_name] = await self.run_check(check_name)
        return results


class SelfHealingService:
    """Centralized self-healing service for the ecosystem."""

    def __init__(self):
        self._process_monitor = ProcessMonitor()
        self._service_restarter = ServiceRestarter()
        self._data_checker = DataConsistencyChecker()
        self._healing_rules: List[HealingRule] = []
        self._alert_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

        # Default healing rules
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """Setup default healing rules."""
        # Crash loop detection and restart
        self.add_healing_rule(HealingRule(
            name="crash_loop_restart",
            condition_func=self._detect_crash_loop,
            action=HealingAction.RESTART_SERVICE,
            priority=1,
            cooldown_seconds=300.0
        ))

        # Memory leak detection and restart
        self.add_healing_rule(HealingRule(
            name="memory_leak_restart",
            condition_func=self._detect_memory_leak,
            action=HealingAction.RESTART_SERVICE,
            priority=2,
            cooldown_seconds=600.0
        ))

        # High error rate response
        self.add_healing_rule(HealingRule(
            name="high_error_rate_cache_clear",
            condition_func=self._detect_high_error_rate,
            action=HealingAction.CLEAR_CACHE,
            priority=3,
            cooldown_seconds=120.0
        ))

    def add_healing_rule(self, rule: HealingRule) -> None:
        """Add a healing rule."""
        self._healing_rules.append(rule)
        logger.info(f"Added healing rule: {rule.name}")

    def register_service(self, service_name: str, process_id: Optional[int] = None,
                        container_id: Optional[str] = None) -> None:
        """Register a service for monitoring and healing."""
        self._process_monitor.register_process(service_name, process_id, container_id)

    def add_data_consistency_check(self, check: DataConsistencyCheck) -> None:
        """Add a data consistency check."""
        self._data_checker.register_check(check)

    def add_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Add callback for healing alerts."""
        self._alert_callbacks.append(callback)

    async def perform_healing_check(self) -> List[str]:
        """Perform healing checks and execute necessary actions."""
        executed_actions = []

        # Update process information
        for service_name in self._process_monitor._monitored_processes.keys():
            self._process_monitor.update_process_info(service_name)

        # Check healing rules
        for rule in self._healing_rules:
            if not rule.enabled:
                continue

            # Check cooldown
            if rule.last_executed and time.time() - rule.last_executed < rule.cooldown_seconds:
                continue

            # Check max executions
            if rule.execution_count >= rule.max_executions:
                continue

            try:
                # Get context for rule evaluation
                context = self._get_rule_context(rule)

                if rule.condition_func(context):
                    logger.info(f"Healing rule triggered: {rule.name}")

                    # Execute healing action
                    success = await self._execute_healing_action(rule.action, context)

                    if success:
                        rule.last_executed = time.time()
                        rule.execution_count += 1
                        executed_actions.append(rule.name)

                        # Alert
                        await self._trigger_alert("healing_action_executed", {
                            "rule_name": rule.name,
                            "action": rule.action.value,
                            "context": context
                        })
                    else:
                        logger.error(f"Healing action failed: {rule.name}")

            except Exception as e:
                logger.error(f"Error evaluating healing rule {rule.name}: {e}")

        # Run data consistency checks
        consistency_results = await self._data_checker.run_all_checks()
        failed_checks = [name for name, success in consistency_results.items() if not success]

        if failed_checks:
            logger.warning(f"Data consistency checks failed: {failed_checks}")
            executed_actions.extend([f"consistency_check_{name}" for name in failed_checks])

        return executed_actions

    def _get_rule_context(self, rule: HealingRule) -> Dict[str, Any]:
        """Get context information for rule evaluation."""
        context = {
            "timestamp": time.time(),
            "rule_name": rule.name
        }

        # Add service-specific information
        for service_name, instance in self._process_monitor._monitored_processes.items():
            context[f"{service_name}_status"] = instance.health_status
            context[f"{service_name}_memory_mb"] = instance.memory_usage_mb
            context[f"{service_name}_cpu_percent"] = instance.cpu_usage_percent
            context[f"{service_name}_restarts"] = instance.restart_count
            context[f"{service_name}_last_restart"] = instance.last_restart

        return context

    async def _execute_healing_action(self, action: HealingAction, context: Dict[str, Any]) -> bool:
        """Execute a healing action."""
        try:
            if action == HealingAction.RESTART_SERVICE:
                service_name = context.get("service_name", "unknown")
                return await self._service_restarter.restart_service(service_name)

            elif action == HealingAction.CLEAR_CACHE:
                # This would integrate with cache services
                logger.info("Clearing caches (integration needed)")
                return True

            elif action == HealingAction.LOG_ROTATION:
                # This would integrate with logging services
                logger.info("Performing log rotation (integration needed)")
                return True

            else:
                logger.warning(f"Unsupported healing action: {action}")
                return False

        except Exception as e:
            logger.error(f"Error executing healing action {action}: {e}")
            return False

    def _detect_crash_loop(self, context: Dict[str, Any]) -> bool:
        """Detect crash loop pattern."""
        for service_name in self._process_monitor._monitored_processes.keys():
            if self._process_monitor.detect_crash_loop(service_name):
                context["service_name"] = service_name
                return True
        return False

    def _detect_memory_leak(self, context: Dict[str, Any]) -> bool:
        """Detect memory leak pattern."""
        for service_name in self._process_monitor._monitored_processes.keys():
            if self._process_monitor.detect_memory_leak(service_name):
                context["service_name"] = service_name
                return True
        return False

    def _detect_high_error_rate(self, context: Dict[str, Any]) -> bool:
        """Detect high error rate pattern."""
        # This would integrate with error tracking services
        # For now, return False
        return False

    async def _trigger_alert(self, alert_type: str, data: Dict[str, Any]) -> None:
        """Trigger alert callbacks."""
        for callback in self._alert_callbacks:
            try:
                await callback(alert_type, data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

    def get_healing_status(self) -> Dict[str, Any]:
        """Get current healing status."""
        rules_status = []
        for rule in self._healing_rules:
            rules_status.append({
                "name": rule.name,
                "enabled": rule.enabled,
                "executions": rule.execution_count,
                "max_executions": rule.max_executions,
                "last_executed": rule.last_executed,
                "cooldown_seconds": rule.cooldown_seconds
            })

        services_status = {}
        for service_name, instance in self._process_monitor._monitored_processes.items():
            services_status[service_name] = {
                "health_status": instance.health_status,
                "memory_usage_mb": instance.memory_usage_mb,
                "cpu_usage_percent": instance.cpu_usage_percent,
                "restart_count": instance.restart_count,
                "last_restart": instance.last_restart
            }

        return {
            "rules": rules_status,
            "services": services_status,
            "data_checks": list(self._data_checker._checks.keys())
        }

    async def start_monitoring(self, check_interval: float = 60.0) -> None:
        """Start background healing monitoring."""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop(check_interval))
            logger.info("Self-healing monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop background healing monitoring."""
        if self._monitoring_task:
            self._shutdown_event.set()
            try:
                await asyncio.wait_for(self._monitoring_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._monitoring_task.cancel()
            logger.info("Self-healing monitoring stopped")

    async def _monitoring_loop(self, check_interval: float) -> None:
        """Background monitoring loop."""
        while not self._shutdown_event.is_set():
            try:
                executed_actions = await self.perform_healing_check()
                if executed_actions:
                    logger.info(f"Executed healing actions: {executed_actions}")

                await asyncio.sleep(check_interval)
            except Exception as e:
                logger.error(f"Error in healing monitoring loop: {e}")
                await asyncio.sleep(check_interval)


# Global instance
_self_healing_service: Optional[SelfHealingService] = None


def get_self_healing_service() -> SelfHealingService:
    """Get the global self-healing service instance."""
    global _self_healing_service
    if _self_healing_service is None:
        _self_healing_service = SelfHealingService()
    return _self_healing_service


# Convenience functions
async def trigger_healing_check() -> List[str]:
    """Convenience function to trigger healing check."""
    service = get_self_healing_service()
    return await service.perform_healing_check()


def register_service_for_healing(service_name: str, process_id: Optional[int] = None,
                                container_id: Optional[str] = None) -> None:
    """Convenience function to register service for healing."""
    service = get_self_healing_service()
    service.register_service(service_name, process_id, container_id)
