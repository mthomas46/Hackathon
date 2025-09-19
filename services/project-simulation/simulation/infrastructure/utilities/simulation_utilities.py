"""Simulation Utilities - Leveraging Shared Ecosystem Utilities.

This module provides simulation-specific utilities that leverage and extend
the shared utilities from services/shared/utilities/ for consistency and reusability.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable, TypeVar, Generic
from datetime import datetime, timedelta
import json
import hashlib
import uuid
import re
from functools import wraps, lru_cache
import asyncio

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger

# Import shared utilities (with fallbacks)
try:
    from shared.utilities.validation import DataValidator, ValidationRule, ValidationResult
    from shared.utilities.formatting import DataFormatter, FormatTemplate
    from shared.utilities.caching import CacheManager, CacheConfig
    from shared.utilities.async_utils import AsyncTaskManager, TaskConfig
    from shared.utilities.error_handling import ErrorHandler, ErrorContext
    from shared.utilities.retry import RetryManager, RetryConfig
    from shared.utilities.metrics import PerformanceTracker, MetricConfig
except ImportError:
    # Fallback implementations for shared utilities
    from dataclasses import dataclass
    from enum import Enum

    class ValidationResult:
        def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
            self.is_valid = is_valid
            self.errors = errors or []
            self.warnings = warnings or []

    class DataValidator:
        def __init__(self):
            self.rules = []

        def validate(self, data: Dict[str, Any], rules: List[str] = None) -> ValidationResult:
            errors = []
            warnings = []
            # Simplified validation
            if not isinstance(data, dict):
                errors.append("Data must be a dictionary")
            return ValidationResult(len(errors) == 0, errors, warnings)

    class DataFormatter:
        def __init__(self):
            self.templates = {}

        def format_data(self, data: Dict[str, Any], template: str = None) -> str:
            return json.dumps(data, indent=2, default=str)

    @dataclass
    class CacheConfig:
        ttl_seconds: int = 300
        max_size: int = 1000
        strategy: str = "lru"

    class CacheManager:
        def __init__(self, config: CacheConfig):
            self.config = config
            self.cache = {}

        def get(self, key: str) -> Optional[Any]:
            return self.cache.get(key)

        def set(self, key: str, value: Any, ttl: int = None):
            self.cache[key] = value

        def delete(self, key: str):
            self.cache.pop(key, None)

    class AsyncTaskManager:
        def __init__(self):
            self.tasks = []

        async def run_task(self, coro):
            return await coro

    class ErrorHandler:
        def __init__(self):
            pass

        def handle_error(self, error: Exception, context: Dict[str, Any] = None):
            print(f"Error: {error}")

    @dataclass
    class RetryConfig:
        max_attempts: int = 3
        backoff_factor: float = 1.0
        max_delay: float = 60.0

    class RetryManager:
        def __init__(self, config: RetryConfig):
            self.config = config

        async def execute_with_retry(self, func, *args, **kwargs):
            return await func(*args, **kwargs)

    @dataclass
    class MetricConfig:
        name: str
        unit: str = "count"

    class PerformanceTracker:
        def __init__(self, config: MetricConfig):
            self.config = config

        def track_performance(self, operation: str, duration: float):
            print(f"Performance: {operation} took {duration:.2f}s")


class SimulationDataValidator(DataValidator):
    """Extended data validator for simulation-specific validation."""

    def __init__(self):
        super().__init__()
        self._setup_simulation_validation_rules()

    def _setup_simulation_validation_rules(self):
        """Set up simulation-specific validation rules."""
        self.simulation_rules = {
            "project_config": self._validate_project_config,
            "team_config": self._validate_team_config,
            "timeline_config": self._validate_timeline_config,
            "simulation_parameters": self._validate_simulation_parameters
        }

    def validate_simulation_data(self, data_type: str, data: Dict[str, Any]) -> ValidationResult:
        """Validate simulation-specific data."""
        if data_type not in self.simulation_rules:
            return ValidationResult(False, [f"Unknown data type: {data_type}"])

        validator_func = self.simulation_rules[data_type]
        return validator_func(data)

    def _validate_project_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate project configuration."""
        errors = []
        warnings = []

        required_fields = ["name", "type", "complexity", "duration_weeks"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")

        if "name" in config and len(config["name"]) < 3:
            errors.append("Project name must be at least 3 characters")

        if "type" in config and config["type"] not in ["web_application", "api_service", "mobile_application", "data_science", "devops_tool"]:
            errors.append("Invalid project type")

        if "complexity" in config and config["complexity"] not in ["simple", "medium", "complex"]:
            errors.append("Invalid complexity level")

        if "duration_weeks" in config and not (1 <= config["duration_weeks"] <= 52):
            errors.append("Duration must be between 1 and 52 weeks")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_team_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate team configuration."""
        errors = []
        warnings = []

        if "members" not in config:
            errors.append("Team configuration must include members")
            return ValidationResult(False, errors, warnings)

        members = config["members"]
        if not isinstance(members, list) or len(members) == 0:
            errors.append("Team must have at least one member")
        elif len(members) > 20:
            warnings.append("Large team size may impact simulation performance")

        for i, member in enumerate(members):
            if not isinstance(member, dict):
                errors.append(f"Team member {i} must be a dictionary")
                continue

            if "name" not in member:
                errors.append(f"Team member {i} missing name")
            if "role" not in member:
                errors.append(f"Team member {i} missing role")
            elif member["role"] not in ["developer", "qa_engineer", "devops_engineer", "architect", "product_owner", "scrum_master", "ux_designer"]:
                errors.append(f"Team member {i} has invalid role: {member['role']}")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_timeline_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate timeline configuration."""
        errors = []
        warnings = []

        if "phases" not in config:
            errors.append("Timeline configuration must include phases")
            return ValidationResult(False, errors, warnings)

        phases = config["phases"]
        if not isinstance(phases, list) or len(phases) == 0:
            errors.append("Timeline must have at least one phase")

        for i, phase in enumerate(phases):
            if not isinstance(phase, dict):
                errors.append(f"Phase {i} must be a dictionary")
                continue

            required_phase_fields = ["name", "duration_days", "start_date", "end_date"]
            for field in required_phase_fields:
                if field not in phase:
                    errors.append(f"Phase {i} missing required field: {field}")

            if "duration_days" in phase and phase["duration_days"] <= 0:
                errors.append(f"Phase {i} duration must be positive")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_simulation_parameters(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate simulation parameters."""
        errors = []
        warnings = []

        if "max_concurrent_simulations" in params and params["max_concurrent_simulations"] > 100:
            warnings.append("High concurrent simulation count may impact performance")

        if "timeout_seconds" in params and params["timeout_seconds"] > 3600:
            warnings.append("Very long timeout may cause resource issues")

        if "quality_threshold" in params:
            threshold = params["quality_threshold"]
            if not (0.0 <= threshold <= 1.0):
                errors.append("Quality threshold must be between 0.0 and 1.0")

        return ValidationResult(len(errors) == 0, errors, warnings)


class SimulationDataFormatter(DataFormatter):
    """Extended data formatter for simulation-specific formatting."""

    def __init__(self):
        super().__init__()
        self._setup_simulation_templates()

    def _setup_simulation_templates(self):
        """Set up simulation-specific formatting templates."""
        self.templates.update({
            "simulation_summary": self._format_simulation_summary,
            "project_report": self._format_project_report,
            "team_analysis": self._format_team_analysis,
            "timeline_progress": self._format_timeline_progress
        })

    def format_simulation_summary(self, simulation_data: Dict[str, Any]) -> str:
        """Format simulation summary."""
        return self.format_data(simulation_data, "simulation_summary")

    def format_project_report(self, project_data: Dict[str, Any]) -> str:
        """Format project report."""
        return self.format_data(project_data, "project_report")

    def _format_simulation_summary(self, data: Dict[str, Any]) -> str:
        """Format simulation summary with custom template."""
        lines = [
            "=" * 60,
            "SIMULATION SUMMARY",
            "=" * 60,
            f"Simulation ID: {data.get('id', 'N/A')}",
            f"Project: {data.get('project_name', 'N/A')}",
            f"Status: {data.get('status', 'N/A')}",
            f"Duration: {data.get('duration_seconds', 0)} seconds",
            f"Documents Generated: {data.get('documents_count', 0)}",
            f"Success Rate: {data.get('success_rate', 0):.1%}",
            "-" * 60,
            "Key Metrics:",
            f"  Total Events: {data.get('total_events', 0)}",
            f"  Quality Score: {data.get('quality_score', 0):.2f}",
            f"  Performance Score: {data.get('performance_score', 0):.2f}",
            "=" * 60
        ]
        return "\n".join(lines)

    def _format_project_report(self, data: Dict[str, Any]) -> str:
        """Format project report."""
        lines = [
            "=" * 60,
            f"PROJECT REPORT: {data.get('name', 'Unknown')}",
            "=" * 60,
            f"Type: {data.get('type', 'N/A')}",
            f"Complexity: {data.get('complexity', 'N/A')}",
            f"Team Size: {data.get('team_size', 0)}",
            f"Duration: {data.get('duration_weeks', 0)} weeks",
            "-" * 60,
            "Generated Documents:",
        ]

        documents = data.get('documents', [])
        for doc in documents[:10]:  # Limit to first 10
            lines.append(f"  • {doc.get('title', 'Untitled')} ({doc.get('type', 'unknown')})")

        if len(documents) > 10:
            lines.append(f"  ... and {len(documents) - 10} more documents")

        lines.append("=" * 60)
        return "\n".join(lines)

    def _format_team_analysis(self, data: Dict[str, Any]) -> str:
        """Format team analysis."""
        lines = [
            "=" * 60,
            "TEAM ANALYSIS",
            "=" * 60,
        ]

        members = data.get('members', [])
        for member in members:
            lines.extend([
                f"Member: {member.get('name', 'Unknown')}",
                f"  Role: {member.get('role', 'Unknown')}",
                f"  Experience: {member.get('experience_years', 0)} years",
                f"  Productivity: {member.get('productivity_factor', 1.0):.2f}",
                ""
            ])

        lines.append("=" * 60)
        return "\n".join(lines)

    def _format_timeline_progress(self, data: Dict[str, Any]) -> str:
        """Format timeline progress."""
        lines = [
            "=" * 60,
            "TIMELINE PROGRESS",
            "=" * 60,
        ]

        phases = data.get('phases', [])
        for phase in phases:
            progress = phase.get('progress_percentage', 0)
            status = phase.get('status', 'unknown')
            lines.extend([
                f"Phase: {phase.get('name', 'Unknown')}",
                f"  Progress: {progress:.1f}%",
                f"  Status: {status}",
                f"  Duration: {phase.get('duration_days', 0)} days",
                ""
            ])

        lines.append("=" * 60)
        return "\n".join(lines)


class SimulationCacheManager(CacheManager):
    """Extended cache manager for simulation-specific caching."""

    def __init__(self, config: CacheConfig = None):
        config = config or CacheConfig(ttl_seconds=600, max_size=500)
        super().__init__(config)
        self.logger = get_simulation_logger()

    def get_simulation_cache_key(self, simulation_id: str, data_type: str) -> str:
        """Generate cache key for simulation data."""
        return f"sim:{simulation_id}:{data_type}"

    def cache_simulation_result(self, simulation_id: str, result: Dict[str, Any], ttl: int = None):
        """Cache simulation result."""
        key = self.get_simulation_cache_key(simulation_id, "result")
        self.set(key, result, ttl or self.config.ttl_seconds)

    def get_simulation_result(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Get cached simulation result."""
        key = self.get_simulation_cache_key(simulation_id, "result")
        return self.get(key)

    def cache_document_metadata(self, document_id: str, metadata: Dict[str, Any]):
        """Cache document metadata."""
        key = f"doc:{document_id}:metadata"
        self.set(key, metadata, self.config.ttl_seconds * 2)  # Longer TTL for metadata

    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get cached document metadata."""
        key = f"doc:{document_id}:metadata"
        return self.get(key)

    def invalidate_simulation_cache(self, simulation_id: str):
        """Invalidate all cache entries for a simulation."""
        # In a real implementation, this would iterate through all keys
        # For now, we'll just clear specific known keys
        result_key = self.get_simulation_cache_key(simulation_id, "result")
        self.delete(result_key)
        self.logger.info("Invalidated simulation cache", simulation_id=simulation_id)


class SimulationAsyncTaskManager(AsyncTaskManager):
    """Extended async task manager for simulation tasks."""

    def __init__(self):
        super().__init__()
        self.logger = get_simulation_logger()
        self.active_tasks = {}
        self.completed_tasks = []

    async def run_simulation_task(self, task_name: str, coro) -> Any:
        """Run a simulation task with tracking."""
        task_id = f"{task_name}_{datetime.now().strftime('%H%M%S')}_{hash(coro) % 1000}"

        self.active_tasks[task_id] = {
            "name": task_name,
            "start_time": datetime.now(),
            "status": "running"
        }

        try:
            self.logger.info("Starting simulation task", task_id=task_id, task_name=task_name)
            result = await self.run_task(coro)

            self.active_tasks[task_id]["status"] = "completed"
            self.active_tasks[task_id]["end_time"] = datetime.now()
            self.active_tasks[task_id]["result"] = result

            self.completed_tasks.append(self.active_tasks.pop(task_id))

            self.logger.info("Simulation task completed", task_id=task_id, task_name=task_name)
            return result

        except Exception as e:
            self.active_tasks[task_id]["status"] = "failed"
            self.active_tasks[task_id]["end_time"] = datetime.now()
            self.active_tasks[task_id]["error"] = str(e)

            self.completed_tasks.append(self.active_tasks.pop(task_id))

            self.logger.error("Simulation task failed", task_id=task_id, task_name=task_name, error=str(e))
            raise

    async def run_parallel_simulations(self, simulations: List[Dict[str, Any]]) -> List[Any]:
        """Run multiple simulations in parallel."""
        tasks = []
        for i, sim_config in enumerate(simulations):
            task_name = f"simulation_{i+1}"
            # In a real implementation, this would create actual simulation coroutines
            tasks.append(self.run_simulation_task(task_name, self._mock_simulation_task(sim_config)))

        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _mock_simulation_task(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Mock simulation task for demonstration."""
        await asyncio.sleep(1)  # Simulate work
        return {"status": "completed", "config": config, "result": "mock_result"}

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        return None

    def get_completed_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get list of completed tasks."""
        return self.completed_tasks[-limit:]


class SimulationErrorHandler(ErrorHandler):
    """Extended error handler for simulation-specific errors."""

    def __init__(self):
        super().__init__()
        self.logger = get_simulation_logger()
        self.error_patterns = self._setup_error_patterns()

    def _setup_error_patterns(self) -> Dict[str, Callable]:
        """Set up error pattern handlers."""
        return {
            "validation_error": self._handle_validation_error,
            "service_unavailable": self._handle_service_unavailable,
            "timeout_error": self._handle_timeout_error,
            "resource_exhausted": self._handle_resource_exhausted,
            "configuration_error": self._handle_configuration_error
        }

    def handle_simulation_error(self, error: Exception, context: Dict[str, Any] = None):
        """Handle simulation-specific errors."""
        context = context or {}
        error_type = self._classify_error(error)

        if error_type in self.error_patterns:
            self.error_patterns[error_type](error, context)
        else:
            self.handle_error(error, context)

    def _classify_error(self, error: Exception) -> str:
        """Classify error type for appropriate handling."""
        error_message = str(error).lower()
        error_class = error.__class__.__name__.lower()

        if "validation" in error_message or "pydantic" in error_class:
            return "validation_error"
        elif "timeout" in error_message or "timeout" in error_class:
            return "timeout_error"
        elif "service" in error_message and "unavailable" in error_message:
            return "service_unavailable"
        elif "resource" in error_message or "memory" in error_message or "cpu" in error_message:
            return "resource_exhausted"
        elif "config" in error_message:
            return "configuration_error"
        else:
            return "unknown_error"

    def _handle_validation_error(self, error: Exception, context: Dict[str, Any]):
        """Handle validation errors."""
        self.logger.warning(
            "Validation error in simulation",
            error=str(error),
            context=context,
            recommendation="Check input data format and required fields"
        )

    def _handle_service_unavailable(self, error: Exception, context: Dict[str, Any]):
        """Handle service unavailable errors."""
        self.logger.error(
            "Ecosystem service unavailable",
            error=str(error),
            context=context,
            recommendation="Check service health and network connectivity"
        )

    def _handle_timeout_error(self, error: Exception, context: Dict[str, Any]):
        """Handle timeout errors."""
        self.logger.warning(
            "Operation timeout in simulation",
            error=str(error),
            context=context,
            recommendation="Consider increasing timeout or optimizing operation"
        )

    def _handle_resource_exhausted(self, error: Exception, context: Dict[str, Any]):
        """Handle resource exhaustion errors."""
        self.logger.error(
            "Resource exhaustion in simulation",
            error=str(error),
            context=context,
            recommendation="Scale resources or reduce concurrent operations"
        )

    def _handle_configuration_error(self, error: Exception, context: Dict[str, Any]):
        """Handle configuration errors."""
        self.logger.error(
            "Configuration error in simulation",
            error=str(error),
            context=context,
            recommendation="Validate configuration files and environment variables"
        )


class SimulationRetryManager(RetryManager):
    """Extended retry manager for simulation operations."""

    def __init__(self, config: RetryConfig = None):
        config = config or RetryConfig(max_attempts=5, backoff_factor=1.5, max_delay=120.0)
        super().__init__(config)
        self.logger = get_simulation_logger()

    async def execute_with_simulation_retry(self, operation_name: str, func, *args, **kwargs):
        """Execute with simulation-specific retry logic."""
        attempt = 0
        last_error = None

        while attempt < self.config.max_attempts:
            try:
                attempt += 1
                self.logger.debug(
                    "Attempting simulation operation",
                    operation=operation_name,
                    attempt=attempt,
                    max_attempts=self.config.max_attempts
                )

                result = await self.execute_with_retry(func, *args, **kwargs)
                return result

            except Exception as e:
                last_error = e

                if attempt < self.config.max_attempts:
                    delay = min(
                        self.config.backoff_factor ** attempt,
                        self.config.max_delay
                    )

                    # Add jitter to prevent thundering herd
                    import random
                    jitter = random.uniform(0.1, 1.0) * delay * 0.1
                    total_delay = delay + jitter

                    self.logger.warning(
                        "Simulation operation failed, retrying",
                        operation=operation_name,
                        attempt=attempt,
                        error=str(e),
                        delay_seconds=round(total_delay, 2)
                    )

                    await asyncio.sleep(total_delay)
                else:
                    self.logger.error(
                        "Simulation operation failed after all retries",
                        operation=operation_name,
                        total_attempts=attempt,
                        final_error=str(e)
                    )
                    raise last_error

        raise last_error


class SimulationPerformanceTracker(PerformanceTracker):
    """Extended performance tracker for simulation operations."""

    def __init__(self, config: MetricConfig = None):
        config = config or MetricConfig(name="simulation_performance", unit="seconds")
        super().__init__(config)
        self.logger = get_simulation_logger()
        self.performance_history = []

    def track_simulation_performance(self, operation: str, duration: float, metadata: Dict[str, Any] = None):
        """Track simulation-specific performance metrics."""
        self.track_performance(operation, duration)

        performance_record = {
            "operation": operation,
            "duration": duration,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }

        self.performance_history.append(performance_record)

        # Keep only last 1000 records
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]

        # Log performance insights
        if duration > 10.0:  # Log slow operations
            self.logger.warning(
                "Slow simulation operation detected",
                operation=operation,
                duration=duration,
                metadata=metadata
            )

    def get_performance_summary(self, operation_filter: str = None) -> Dict[str, Any]:
        """Get performance summary for operations."""
        records = self.performance_history

        if operation_filter:
            records = [r for r in records if operation_filter in r["operation"]]

        if not records:
            return {"total_operations": 0, "average_duration": 0, "slow_operations": 0}

        durations = [r["duration"] for r in records]
        slow_operations = len([r for r in records if r["duration"] > 5.0])

        return {
            "total_operations": len(records),
            "average_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "slow_operations": slow_operations,
            "slow_operation_percentage": (slow_operations / len(records)) * 100
        }


# Global utility instances
_simulation_validator: Optional[SimulationDataValidator] = None
_simulation_formatter: Optional[SimulationDataFormatter] = None
_simulation_cache: Optional[SimulationCacheManager] = None
_simulation_task_manager: Optional[SimulationAsyncTaskManager] = None
_simulation_error_handler: Optional[SimulationErrorHandler] = None
_simulation_retry_manager: Optional[SimulationRetryManager] = None
_simulation_performance_tracker: Optional[SimulationPerformanceTracker] = None


def get_simulation_validator() -> SimulationDataValidator:
    """Get the global simulation data validator instance."""
    global _simulation_validator
    if _simulation_validator is None:
        _simulation_validator = SimulationDataValidator()
    return _simulation_validator


def get_simulation_formatter() -> SimulationDataFormatter:
    """Get the global simulation data formatter instance."""
    global _simulation_formatter
    if _simulation_formatter is None:
        _simulation_formatter = SimulationDataFormatter()
    return _simulation_formatter


def get_simulation_cache() -> SimulationCacheManager:
    """Get the global simulation cache manager instance."""
    global _simulation_cache
    if _simulation_cache is None:
        _simulation_cache = SimulationCacheManager()
    return _simulation_cache


def get_simulation_task_manager() -> SimulationAsyncTaskManager:
    """Get the global simulation async task manager instance."""
    global _simulation_task_manager
    if _simulation_task_manager is None:
        _simulation_task_manager = SimulationAsyncTaskManager()
    return _simulation_task_manager


def get_simulation_error_handler() -> SimulationErrorHandler:
    """Get the global simulation error handler instance."""
    global _simulation_error_handler
    if _simulation_error_handler is None:
        _simulation_error_handler = SimulationErrorHandler()
    return _simulation_error_handler


def get_simulation_retry_manager() -> SimulationRetryManager:
    """Get the global simulation retry manager instance."""
    global _simulation_retry_manager
    if _simulation_retry_manager is None:
        _simulation_retry_manager = SimulationRetryManager()
    return _simulation_retry_manager


def get_simulation_performance_tracker() -> SimulationPerformanceTracker:
    """Get the global simulation performance tracker instance."""
    global _simulation_performance_tracker
    if _simulation_performance_tracker is None:
        _simulation_performance_tracker = SimulationPerformanceTracker()
    return _simulation_performance_tracker


__all__ = [
    # Core Classes
    'SimulationDataValidator',
    'SimulationDataFormatter',
    'SimulationCacheManager',
    'SimulationAsyncTaskManager',
    'SimulationErrorHandler',
    'SimulationRetryManager',
    'SimulationPerformanceTracker',

    # Global Instances
    'get_simulation_validator',
    'get_simulation_formatter',
    'get_simulation_cache',
    'get_simulation_task_manager',
    'get_simulation_error_handler',
    'get_simulation_retry_manager',
    'get_simulation_performance_tracker'
]
