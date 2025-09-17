#!/usr/bin/env python3
"""
Chaos Engineering Framework

This module provides comprehensive chaos engineering capabilities including:
- Controlled fault injection
- Resilience testing scenarios
- Automated remediation strategies
- System stability analysis
- Failure pattern learning
"""

import asyncio
import json
import uuid
import random
import time
from typing import Dict, Any, List, Optional, Callable, Type, Union, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import threading
import signal
import os

from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget
from services.shared.intelligent_caching import get_service_cache
from services.shared.enterprise_error_handling import enterprise_error_handler, ErrorContext, ErrorSeverity, ErrorCategory


class ChaosExperimentType(Enum):
    """Types of chaos experiments."""
    NETWORK_LATENCY = "network_latency"
    NETWORK_PARTITION = "network_partition"
    SERVICE_FAILURE = "service_failure"
    RESOURCE_STARVATION = "resource_starvation"
    DEPENDENCY_FAILURE = "dependency_failure"
    DATA_CORRUPTION = "data_corruption"
    CONFIGURATION_DRIFT = "configuration_drift"
    LOAD_SPIKE = "load_spike"


class ExperimentState(Enum):
    """Chaos experiment states."""
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ChaosExperiment:
    """Chaos experiment definition."""
    experiment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    experiment_type: ChaosExperimentType
    target_services: List[str]
    duration_seconds: int = 300  # 5 minutes default
    intensity: str = "medium"  # low, medium, high
    safety_checks: List[str] = field(default_factory=list)
    rollback_actions: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    state: ExperimentState = ExperimentState.PLANNED
    results: Dict[str, Any] = field(default_factory=dict)
    metrics_before: Dict[str, Any] = field(default_factory=dict)
    metrics_after: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert experiment to dictionary."""
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "description": self.description,
            "experiment_type": self.experiment_type.value,
            "target_services": self.target_services,
            "duration_seconds": self.duration_seconds,
            "intensity": self.intensity,
            "safety_checks": self.safety_checks,
            "rollback_actions": self.rollback_actions,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "state": self.state.value,
            "results": self.results,
            "metrics_before": self.metrics_before,
            "metrics_after": self.metrics_after
        }


@dataclass
class ResilienceMetrics:
    """System resilience metrics."""
    experiment_count: int = 0
    successful_experiments: int = 0
    failed_experiments: int = 0
    average_recovery_time: float = 0.0
    system_stability_score: float = 1.0
    resilience_patterns: Dict[str, int] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)

    def update_from_experiment(self, experiment: ChaosExperiment):
        """Update metrics from completed experiment."""
        self.experiment_count += 1

        if experiment.state == ExperimentState.COMPLETED:
            self.successful_experiments += 1
        elif experiment.state == ExperimentState.FAILED:
            self.failed_experiments += 1

        # Update success rate
        success_rate = self.successful_experiments / self.experiment_count if self.experiment_count > 0 else 1.0

        # Calculate stability score based on success rate and recovery patterns
        self.system_stability_score = success_rate * 0.8 + self._calculate_resilience_factor() * 0.2

        self.last_updated = datetime.now()

    def _calculate_resilience_factor(self) -> float:
        """Calculate resilience factor based on learned patterns."""
        if not self.resilience_patterns:
            return 0.5

        # Simple resilience calculation based on pattern diversity
        pattern_diversity = len(self.resilience_patterns) / 10  # Normalize to 10 expected patterns
        return min(pattern_diversity, 1.0)


class FaultInjector:
    """Fault injection engine for chaos experiments."""

    def __init__(self):
        self.active_faults: Dict[str, Dict[str, Any]] = {}
        self.fault_history: List[Dict[str, Any]] = []
        self.recovery_actions: Dict[str, Callable] = {}

    async def inject_network_latency(self, target_service: str, latency_ms: int, duration_seconds: int) -> str:
        """Inject network latency fault."""
        fault_id = f"latency_{uuid.uuid4().hex[:8]}"

        # In a real implementation, this would use network tools like tc (traffic control)
        # For simulation, we'll just log the intended fault
        fault_data = {
            "fault_id": fault_id,
            "type": "network_latency",
            "target_service": target_service,
            "latency_ms": latency_ms,
            "duration_seconds": duration_seconds,
            "injected_at": datetime.now(),
            "status": "active"
        }

        self.active_faults[fault_id] = fault_data

        # Schedule fault removal
        asyncio.create_task(self._remove_fault_after_delay(fault_id, duration_seconds))

        fire_and_forget("warning", f"Injected network latency fault on {target_service}: +{latency_ms}ms for {duration_seconds}s", ServiceNames.ORCHESTRATOR)
        return fault_id

    async def inject_service_failure(self, target_service: str, failure_mode: str, duration_seconds: int) -> str:
        """Inject service failure fault."""
        fault_id = f"failure_{uuid.uuid4().hex[:8]}"

        fault_data = {
            "fault_id": fault_id,
            "type": "service_failure",
            "target_service": target_service,
            "failure_mode": failure_mode,
            "duration_seconds": duration_seconds,
            "injected_at": datetime.now(),
            "status": "active"
        }

        self.active_faults[fault_id] = fault_data

        # Schedule fault removal
        asyncio.create_task(self._remove_fault_after_delay(fault_id, duration_seconds))

        fire_and_forget("error", f"Injected service failure on {target_service}: {failure_mode} for {duration_seconds}s", ServiceNames.ORCHESTRATOR)
        return fault_id

    async def inject_resource_starvation(self, target_service: str, resource_type: str,
                                       reduction_percent: int, duration_seconds: int) -> str:
        """Inject resource starvation fault."""
        fault_id = f"starvation_{uuid.uuid4().hex[:8]}"

        fault_data = {
            "fault_id": fault_id,
            "type": "resource_starvation",
            "target_service": target_service,
            "resource_type": resource_type,
            "reduction_percent": reduction_percent,
            "duration_seconds": duration_seconds,
            "injected_at": datetime.now(),
            "status": "active"
        }

        self.active_faults[fault_id] = fault_data

        # Schedule fault removal
        asyncio.create_task(self._remove_fault_after_delay(fault_id, duration_seconds))

        fire_and_forget("warning", f"Injected resource starvation on {target_service}: {resource_type} -{reduction_percent}% for {duration_seconds}s", ServiceNames.ORCHESTRATOR)
        return fault_id

    async def _remove_fault_after_delay(self, fault_id: str, delay_seconds: int):
        """Remove fault after specified delay."""
        await asyncio.sleep(delay_seconds)

        if fault_id in self.active_faults:
            fault_data = self.active_faults[fault_id]
            fault_data["status"] = "removed"
            fault_data["removed_at"] = datetime.now()

            # Move to history
            self.fault_history.append(fault_data)
            del self.active_faults[fault_id]

            fire_and_forget("info", f"Fault {fault_id} automatically removed after {delay_seconds}s", ServiceNames.ORCHESTRATOR)

    def register_recovery_action(self, fault_type: str, recovery_func: Callable):
        """Register recovery action for fault type."""
        self.recovery_actions[fault_type] = recovery_func

    async def trigger_recovery(self, fault_id: str) -> bool:
        """Trigger recovery for specific fault."""
        if fault_id not in self.active_faults:
            return False

        fault_data = self.active_faults[fault_id]
        fault_type = fault_data["type"]

        if fault_type in self.recovery_actions:
            try:
                recovery_func = self.recovery_actions[fault_type]
                await recovery_func(fault_data)
                fault_data["recovered_at"] = datetime.now()
                return True
            except Exception as e:
                fire_and_forget("error", f"Recovery failed for fault {fault_id}: {e}", ServiceNames.ORCHESTRATOR)
                return False

        return False

    def get_active_faults(self) -> Dict[str, Dict[str, Any]]:
        """Get all active faults."""
        return self.active_faults.copy()

    def get_fault_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get fault injection history."""
        return self.fault_history[-limit:]


class ChaosExperimentRunner:
    """Chaos experiment execution engine."""

    def __init__(self):
        self.experiments: Dict[str, ChaosExperiment] = {}
        self.fault_injector = FaultInjector()
        self.resilience_metrics = ResilienceMetrics()
        self.experiment_tasks: Dict[str, asyncio.Task] = {}
        self.cache = get_service_cache(ServiceNames.ORCHESTRATOR)

    async def create_experiment(self, name: str, description: str, experiment_type: ChaosExperimentType,
                              target_services: List[str], **kwargs) -> str:
        """Create a new chaos experiment."""
        experiment = ChaosExperiment(
            name=name,
            description=description,
            experiment_type=experiment_type,
            target_services=target_services,
            **kwargs
        )

        self.experiments[experiment.experiment_id] = experiment

        # Cache experiment
        await self.cache.set(f"experiment_{experiment.experiment_id}", experiment.to_dict(), ttl_seconds=3600)

        fire_and_forget("info", f"Created chaos experiment: {name} ({experiment.experiment_id})", ServiceNames.ORCHESTRATOR)
        return experiment.experiment_id

    async def run_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """Run a chaos experiment."""
        if experiment_id not in self.experiments:
            return {"error": f"Experiment {experiment_id} not found"}

        experiment = self.experiments[experiment_id]

        # Check safety conditions
        if not await self._check_safety_conditions(experiment):
            experiment.state = ExperimentState.FAILED
            experiment.results = {"error": "Safety conditions not met"}
            return {"error": "Safety conditions not met"}

        # Start experiment
        experiment.state = ExperimentState.RUNNING
        experiment.started_at = datetime.now()

        # Capture baseline metrics
        experiment.metrics_before = await self._capture_system_metrics()

        # Run experiment task
        task = asyncio.create_task(self._execute_experiment(experiment))
        self.experiment_tasks[experiment_id] = task

        return {
            "experiment_id": experiment_id,
            "status": "running",
            "started_at": experiment.started_at.isoformat()
        }

    async def _execute_experiment(self, experiment: ChaosExperiment):
        """Execute the chaos experiment."""
        try:
            fault_ids = []

            # Inject faults based on experiment type
            if experiment.experiment_type == ChaosExperimentType.NETWORK_LATENCY:
                for service in experiment.target_services:
                    latency = 500 if experiment.intensity == "high" else 200 if experiment.intensity == "medium" else 100
                    fault_id = await self.fault_injector.inject_network_latency(
                        service, latency, experiment.duration_seconds
                    )
                    fault_ids.append(fault_id)

            elif experiment.experiment_type == ChaosExperimentType.SERVICE_FAILURE:
                for service in experiment.target_services:
                    failure_mode = "complete" if experiment.intensity == "high" else "degraded"
                    fault_id = await self.fault_injector.inject_service_failure(
                        service, failure_mode, experiment.duration_seconds
                    )
                    fault_ids.append(fault_id)

            elif experiment.experiment_type == ChaosExperimentType.RESOURCE_STARVATION:
                for service in experiment.target_services:
                    resource = random.choice(["cpu", "memory", "disk"])
                    reduction = 80 if experiment.intensity == "high" else 50 if experiment.intensity == "medium" else 20
                    fault_id = await self.fault_injector.inject_resource_starvation(
                        service, resource, reduction, experiment.duration_seconds
                    )
                    fault_ids.append(fault_id)

            # Wait for experiment duration
            await asyncio.sleep(experiment.duration_seconds)

            # Capture post-experiment metrics
            experiment.metrics_after = await self._capture_system_metrics()

            # Analyze results
            experiment.results = await self._analyze_experiment_results(experiment, fault_ids)

            # Complete experiment
            experiment.state = ExperimentState.COMPLETED
            experiment.completed_at = datetime.now()

            # Update resilience metrics
            self.resilience_metrics.update_from_experiment(experiment)

            fire_and_forget("info", f"Chaos experiment {experiment.experiment_id} completed successfully", ServiceNames.ORCHESTRATOR)

        except Exception as e:
            experiment.state = ExperimentState.FAILED
            experiment.results = {"error": str(e)}
            experiment.completed_at = datetime.now()

            fire_and_forget("error", f"Chaos experiment {experiment.experiment_id} failed: {e}", ServiceNames.ORCHESTRATOR)

        finally:
            # Cleanup
            if experiment.experiment_id in self.experiment_tasks:
                del self.experiment_tasks[experiment.experiment_id]

    async def _check_safety_conditions(self, experiment: ChaosExperiment) -> bool:
        """Check if it's safe to run the experiment."""
        # Check if critical services are healthy
        critical_services = [ServiceNames.DOCUMENT_STORE, ServiceNames.ANALYSIS_SERVICE]

        for service in critical_services:
            if service in experiment.target_services:
                # In a real implementation, check service health
                # For now, assume it's safe unless explicitly critical
                if experiment.intensity == "high":
                    fire_and_forget("warning", f"High-intensity experiment targeting critical service: {service}", ServiceNames.ORCHESTRATOR)
                    return False

        # Check concurrent experiments
        running_experiments = [exp for exp in self.experiments.values()
                             if exp.state == ExperimentState.RUNNING]

        if len(running_experiments) > 2:
            fire_and_forget("warning", "Too many concurrent experiments running", ServiceNames.ORCHESTRATOR)
            return False

        return True

    async def _capture_system_metrics(self) -> Dict[str, Any]:
        """Capture current system metrics."""
        # In a real implementation, this would gather actual system metrics
        # For simulation, return mock metrics
        return {
            "cpu_usage": random.uniform(10, 90),
            "memory_usage": random.uniform(20, 95),
            "disk_usage": random.uniform(5, 85),
            "network_traffic": random.uniform(1, 100),
            "active_connections": random.randint(10, 1000),
            "response_time_avg": random.uniform(50, 2000),
            "error_rate": random.uniform(0, 0.05),
            "captured_at": datetime.now().isoformat()
        }

    async def _analyze_experiment_results(self, experiment: ChaosExperiment, fault_ids: List[str]) -> Dict[str, Any]:
        """Analyze experiment results."""
        analysis = {
            "experiment_type": experiment.experiment_type.value,
            "duration_actual": (experiment.completed_at - experiment.started_at).seconds if experiment.completed_at and experiment.started_at else 0,
            "faults_injected": len(fault_ids),
            "system_impact": self._calculate_system_impact(experiment.metrics_before, experiment.metrics_after),
            "recovery_time": self._calculate_recovery_time(experiment),
            "resilience_score": self._calculate_resilience_score(experiment),
            "recommendations": self._generate_experiment_recommendations(experiment)
        }

        return analysis

    def _calculate_system_impact(self, metrics_before: Dict[str, Any], metrics_after: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate system impact of the experiment."""
        impact = {}

        for metric in ['cpu_usage', 'memory_usage', 'response_time_avg', 'error_rate']:
            before = metrics_before.get(metric, 0)
            after = metrics_after.get(metric, 0)
            change = after - before
            impact[metric] = {
                "change": change,
                "change_percent": (change / before * 100) if before > 0 else 0,
                "severity": "high" if abs(change) > 50 else "medium" if abs(change) > 20 else "low"
            }

        return impact

    def _calculate_recovery_time(self, experiment: ChaosExperiment) -> float:
        """Calculate system recovery time."""
        # Simple recovery time calculation
        # In practice, this would analyze metrics during and after experiment
        base_recovery_time = experiment.duration_seconds * 0.1  # 10% of experiment duration
        return base_recovery_time * random.uniform(0.5, 2.0)  # Add some variance

    def _calculate_resilience_score(self, experiment: ChaosExperiment) -> float:
        """Calculate system resilience score from experiment."""
        # Base score from successful completion
        score = 1.0 if experiment.state == ExperimentState.COMPLETED else 0.0

        # Adjust based on system impact
        impact = experiment.results.get("system_impact", {})
        high_impact_count = sum(1 for metric_impact in impact.values()
                              if isinstance(metric_impact, dict) and metric_impact.get("severity") == "high")

        # Reduce score for high impact
        score -= high_impact_count * 0.2
        score = max(0, score)

        return round(score, 2)

    def _generate_experiment_recommendations(self, experiment: ChaosExperiment) -> List[str]:
        """Generate recommendations based on experiment results."""
        recommendations = []

        results = experiment.results
        system_impact = results.get("system_impact", {})
        resilience_score = results.get("resilience_score", 1.0)

        if resilience_score < 0.7:
            recommendations.append("Consider implementing additional fault tolerance measures")

        # Analyze impact metrics
        for metric, impact in system_impact.items():
            if isinstance(impact, dict) and impact.get("severity") == "high":
                if metric == "response_time_avg":
                    recommendations.append("Implement response time circuit breakers")
                elif metric == "error_rate":
                    recommendations.append("Enhance error handling and retry mechanisms")
                elif metric == "memory_usage":
                    recommendations.append("Optimize memory usage and implement garbage collection")

        if experiment.duration_seconds > 600:  # 10 minutes
            recommendations.append("Consider shorter experiment durations for faster feedback")

        return recommendations

    async def stop_experiment(self, experiment_id: str) -> bool:
        """Stop a running experiment."""
        if experiment_id not in self.experiments:
            return False

        experiment = self.experiments[experiment_id]

        if experiment.state != ExperimentState.RUNNING:
            return False

        # Cancel experiment task
        if experiment_id in self.experiment_tasks:
            self.experiment_tasks[experiment_id].cancel()
            del self.experiment_tasks[experiment_id]

        # Rollback faults
        await self._rollback_experiment(experiment)

        experiment.state = ExperimentState.ROLLED_BACK
        experiment.completed_at = datetime.now()

        fire_and_forget("info", f"Chaos experiment {experiment_id} stopped and rolled back", ServiceNames.ORCHESTRATOR)
        return True

    async def _rollback_experiment(self, experiment: ChaosExperiment):
        """Rollback experiment changes."""
        for rollback_action in experiment.rollback_actions:
            try:
                action_type = rollback_action.get("type")
                if action_type == "remove_fault":
                    fault_id = rollback_action.get("fault_id")
                    if fault_id:
                        await self.fault_injector.trigger_recovery(fault_id)
            except Exception as e:
                fire_and_forget("error", f"Rollback action failed: {e}", ServiceNames.ORCHESTRATOR)

    def get_experiment_status(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment status."""
        if experiment_id not in self.experiments:
            return None

        experiment = self.experiments[experiment_id]
        return experiment.to_dict()

    def get_running_experiments(self) -> List[Dict[str, Any]]:
        """Get all running experiments."""
        return [exp.to_dict() for exp in self.experiments.values()
                if exp.state == ExperimentState.RUNNING]

    async def get_resilience_report(self) -> Dict[str, Any]:
        """Generate comprehensive resilience report."""
        experiments = list(self.experiments.values())

        report = {
            "total_experiments": len(experiments),
            "successful_experiments": len([e for e in experiments if e.state == ExperimentState.COMPLETED]),
            "failed_experiments": len([e for e in experiments if e.state == ExperimentState.FAILED]),
            "rolled_back_experiments": len([e for e in experiments if e.state == ExperimentState.ROLLED_BACK]),
            "resilience_metrics": {
                "system_stability_score": self.resilience_metrics.system_stability_score,
                "average_recovery_time": self.resilience_metrics.average_recovery_time,
                "resilience_patterns": dict(self.resilience_metrics.resilience_patterns)
            },
            "experiment_types": {},
            "recent_experiments": [exp.to_dict() for exp in experiments[-5:]],
            "generated_at": datetime.now().isoformat()
        }

        # Analyze experiment types
        for exp in experiments:
            exp_type = exp.experiment_type.value
            if exp_type not in report["experiment_types"]:
                report["experiment_types"][exp_type] = 0
            report["experiment_types"][exp_type] += 1

        return report


class AutomatedRemediation:
    """Automated remediation system for chaos engineering."""

    def __init__(self):
        self.remediation_rules: Dict[str, Dict[str, Any]] = {}
        self.remediation_history: List[Dict[str, Any]] = []
        self.failure_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def register_remediation_rule(self, failure_pattern: str, remediation_actions: List[Dict[str, Any]],
                                 conditions: Optional[Dict[str, Any]] = None):
        """Register automated remediation rule."""
        self.remediation_rules[failure_pattern] = {
            "actions": remediation_actions,
            "conditions": conditions or {},
            "created_at": datetime.now(),
            "trigger_count": 0
        }

    async def detect_and_remediate(self, failure_event: Dict[str, Any]) -> Dict[str, Any]:
        """Detect failure pattern and apply automated remediation."""
        failure_pattern = self._identify_failure_pattern(failure_event)

        if failure_pattern in self.remediation_rules:
            rule = self.remediation_rules[failure_pattern]

            # Check conditions
            if self._check_remediation_conditions(rule["conditions"], failure_event):
                # Apply remediation
                remediation_result = await self._apply_remediation_actions(
                    rule["actions"], failure_event
                )

                # Record remediation
                remediation_record = {
                    "failure_pattern": failure_pattern,
                    "failure_event": failure_event,
                    "remediation_actions": rule["actions"],
                    "result": remediation_result,
                    "timestamp": datetime.now()
                }

                self.remediation_history.append(remediation_record)
                rule["trigger_count"] += 1

                # Update failure patterns for learning
                self.failure_patterns[failure_pattern].append(failure_event)

                return {
                    "remediated": True,
                    "pattern": failure_pattern,
                    "actions_taken": len(rule["actions"]),
                    "success": remediation_result["success"]
                }

        return {"remediated": False, "reason": "No matching remediation rule"}

    def _identify_failure_pattern(self, failure_event: Dict[str, Any]) -> str:
        """Identify failure pattern from event."""
        error_type = failure_event.get("error_type", "")
        service = failure_event.get("service", "")
        operation = failure_event.get("operation", "")

        # Simple pattern matching
        if "timeout" in error_type.lower():
            return "timeout_failure"
        elif "connection" in error_type.lower():
            return "connection_failure"
        elif "memory" in error_type.lower():
            return "resource_failure"
        elif service and operation:
            return f"{service}_{operation}_failure"
        else:
            return "generic_failure"

    def _check_remediation_conditions(self, conditions: Dict[str, Any], failure_event: Dict[str, Any]) -> bool:
        """Check if remediation conditions are met."""
        if not conditions:
            return True

        # Check severity
        if "min_severity" in conditions:
            event_severity = failure_event.get("severity", "low")
            min_severity = conditions["min_severity"]
            severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            if severity_levels.get(event_severity, 0) < severity_levels.get(min_severity, 0):
                return False

        # Check service
        if "allowed_services" in conditions:
            service = failure_event.get("service", "")
            if service not in conditions["allowed_services"]:
                return False

        return True

    async def _apply_remediation_actions(self, actions: List[Dict[str, Any]],
                                       failure_event: Dict[str, Any]) -> Dict[str, Any]:
        """Apply remediation actions."""
        results = {"success": True, "actions_executed": 0, "errors": []}

        for action in actions:
            try:
                action_type = action.get("type")

                if action_type == "restart_service":
                    service = action.get("service", failure_event.get("service"))
                    await self._restart_service(service)
                elif action_type == "scale_resources":
                    service = action.get("service", failure_event.get("service"))
                    scale_factor = action.get("scale_factor", 1.5)
                    await self._scale_service_resources(service, scale_factor)
                elif action_type == "clear_cache":
                    service = action.get("service", failure_event.get("service"))
                    await self._clear_service_cache(service)
                elif action_type == "switch_to_backup":
                    service = action.get("service", failure_event.get("service"))
                    await self._switch_to_backup_service(service)

                results["actions_executed"] += 1

            except Exception as e:
                results["success"] = False
                results["errors"].append(str(e))

        return results

    async def _restart_service(self, service_name: str):
        """Restart a service (simulated)."""
        fire_and_forget("info", f"Restarting service: {service_name}", ServiceNames.ORCHESTRATOR)
        await asyncio.sleep(2)  # Simulate restart time

    async def _scale_service_resources(self, service_name: str, scale_factor: float):
        """Scale service resources (simulated)."""
        fire_and_forget("info", f"Scaling resources for {service_name} by factor {scale_factor}", ServiceNames.ORCHESTRATOR)

    async def _clear_service_cache(self, service_name: str):
        """Clear service cache."""
        from services.shared.intelligent_caching import get_service_cache
        cache = get_service_cache(service_name)
        # Clear all entries (would need to be more selective in practice)
        await cache.invalidate("all")

    async def _switch_to_backup_service(self, service_name: str):
        """Switch to backup service (simulated)."""
        fire_and_forget("info", f"Switching {service_name} to backup instance", ServiceNames.ORCHESTRATOR)


# Global instances
chaos_experiment_runner = ChaosExperimentRunner()
automated_remediation = AutomatedRemediation()


async def initialize_chaos_engineering():
    """Initialize chaos engineering capabilities."""
    # Register sample remediation rules
    automated_remediation.register_remediation_rule(
        "timeout_failure",
        [
            {"type": "restart_service", "service": "{service}"},
            {"type": "clear_cache", "service": "{service}"}
        ],
        {"min_severity": "medium", "allowed_services": ["analysis_service", "interpreter"]}
    )

    automated_remediation.register_remediation_rule(
        "connection_failure",
        [
            {"type": "switch_to_backup", "service": "{service}"},
            {"type": "scale_resources", "service": "{service}", "scale_factor": 2.0}
        ],
        {"min_severity": "high"}
    )

    fire_and_forget("info", "Chaos engineering framework initialized", ServiceNames.ORCHESTRATOR)
