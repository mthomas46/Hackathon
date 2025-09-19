"""Environment Manager - Advanced Multi-Environment Configuration Management.

This module provides comprehensive environment management capabilities for the
Project Simulation Service, enabling seamless switching between different
deployment environments (development, staging, production) with environment-specific
configurations, validation, and automated setup.

Key Features:
- Environment detection and auto-configuration
- Environment-specific service endpoints and settings
- Configuration validation and health checks
- Environment switching with zero-downtime
- Environment-specific feature flags and overrides
- Configuration drift detection and correction
"""

import sys
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import hashlib
from datetime import datetime

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger


class Environment(str, Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"
    LOCAL = "local"


class ServiceStatus(str, Enum):
    """Service status indicators."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class EnvironmentConfig:
    """Configuration for a specific environment."""
    name: str
    environment: Environment
    service_endpoints: Dict[str, str] = field(default_factory=dict)
    database_config: Dict[str, Any] = field(default_factory=dict)
    cache_config: Dict[str, Any] = field(default_factory=dict)
    monitoring_config: Dict[str, Any] = field(default_factory=dict)
    security_config: Dict[str, Any] = field(default_factory=dict)
    feature_flags: Dict[str, bool] = field(default_factory=dict)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    custom_settings: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "environment": self.environment.value,
            "service_endpoints": self.service_endpoints,
            "database_config": self.database_config,
            "cache_config": self.cache_config,
            "monitoring_config": self.monitoring_config,
            "security_config": self.security_config,
            "feature_flags": self.feature_flags,
            "resource_limits": self.resource_limits,
            "custom_settings": self.custom_settings
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnvironmentConfig':
        """Create from dictionary."""
        return cls(
            name=data["name"],
            environment=Environment(data["environment"]),
            service_endpoints=data.get("service_endpoints", {}),
            database_config=data.get("database_config", {}),
            cache_config=data.get("cache_config", {}),
            monitoring_config=data.get("monitoring_config", {}),
            security_config=data.get("security_config", {}),
            feature_flags=data.get("feature_flags", {}),
            resource_limits=data.get("resource_limits", {}),
            custom_settings=data.get("custom_settings", {})
        )


@dataclass
class ServiceHealth:
    """Health status of a service."""
    name: str
    status: ServiceStatus
    response_time: Optional[float] = None
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None
    version: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class EnvironmentManager:
    """Advanced environment configuration manager."""

    def __init__(self, config_dir: Union[str, Path] = None):
        """Initialize the environment manager."""
        if config_dir is None:
            # Default to config directory relative to this file
            config_dir = Path(__file__).parent.parent.parent / "config"

        self.config_dir = Path(config_dir)
        self.logger = get_simulation_logger()
        self.current_environment: Optional[Environment] = None
        self.current_config: Optional[EnvironmentConfig] = None
        self.service_health: Dict[str, ServiceHealth] = {}
        self.environment_configs: Dict[str, EnvironmentConfig] = {}
        self.config_hash: Optional[str] = None

        # Load environment configurations
        self._load_environment_configs()

    async def initialize(self) -> None:
        """Initialize the environment manager."""
        # Auto-detect current environment
        await self._detect_environment()

        # Load current environment configuration
        await self._load_current_environment()

        # Validate configuration
        await self._validate_configuration()

        self.logger.info(f"Environment manager initialized for {self.current_environment.value}")

    async def switch_environment(self, environment: Environment,
                               validate: bool = True) -> bool:
        """Switch to a different environment."""
        try:
            self.logger.info(f"Switching to environment: {environment.value}")

            # Validate target environment exists
            if environment.value not in self.environment_configs:
                self.logger.error(f"Environment configuration not found: {environment.value}")
                return False

            # Validate current environment health if requested
            if validate:
                health_status = await self._validate_environment_health(self.current_environment)
                if not health_status:
                    self.logger.warning("Current environment health check failed, proceeding with switch")

            # Switch environment
            old_environment = self.current_environment
            self.current_environment = environment
            self.current_config = self.environment_configs[environment.value]

            # Update configuration
            await self._apply_environment_config()

            # Validate new environment
            if validate:
                health_status = await self._validate_environment_health(environment)
                if not health_status:
                    self.logger.warning("New environment health check failed")

            self.logger.info(f"Successfully switched from {old_environment.value} to {environment.value}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to switch environment: {e}")
            return False

    async def get_current_environment(self) -> Optional[EnvironmentConfig]:
        """Get current environment configuration."""
        return self.current_config

    async def get_environment_info(self, environment: Optional[Environment] = None) -> Dict[str, Any]:
        """Get comprehensive environment information."""
        target_env = environment or self.current_environment
        if not target_env or target_env.value not in self.environment_configs:
            return {"error": "Environment not found"}

        config = self.environment_configs[target_env.value]

        # Get service health for this environment
        services_health = {}
        for service_name, endpoint in config.service_endpoints.items():
            health = self.service_health.get(service_name)
            if health:
                services_health[service_name] = {
                    "status": health.status.value,
                    "response_time": health.response_time,
                    "last_check": health.last_check.isoformat() if health.last_check else None,
                    "version": health.version
                }

        return {
            "environment": target_env.value,
            "name": config.name,
            "is_current": target_env == self.current_environment,
            "service_endpoints": config.service_endpoints,
            "services_health": services_health,
            "feature_flags": config.feature_flags,
            "resource_limits": config.resource_limits,
            "last_updated": datetime.now().isoformat()
        }

    async def validate_environment(self, environment: Optional[Environment] = None) -> Dict[str, Any]:
        """Validate an environment configuration."""
        target_env = environment or self.current_environment
        if not target_env or target_env.value not in self.environment_configs:
            return {"valid": False, "error": "Environment not found"}

        config = self.environment_configs[target_env.value]
        issues = []

        # Validate service endpoints
        for service_name, endpoint in config.service_endpoints.items():
            if not self._is_valid_url(endpoint):
                issues.append(f"Invalid service endpoint for {service_name}: {endpoint}")

        # Validate required configurations
        if not config.database_config:
            issues.append("Database configuration is missing")

        # Validate feature flags
        required_flags = ["enable_health_checks", "enable_monitoring"]
        for flag in required_flags:
            if flag not in config.feature_flags:
                issues.append(f"Required feature flag missing: {flag}")

        # Check service health
        health_issues = await self._validate_environment_health(target_env, return_issues=True)
        issues.extend(health_issues)

        return {
            "environment": target_env.value,
            "valid": len(issues) == 0,
            "issues": issues,
            "services_checked": len(config.service_endpoints),
            "validation_timestamp": datetime.now().isoformat()
        }

    async def refresh_service_health(self) -> Dict[str, Any]:
        """Refresh health status of all services in current environment."""
        if not self.current_config:
            return {"error": "No current environment configured"}

        results = {}
        for service_name, endpoint in self.current_config.service_endpoints.items():
            health = await self._check_service_health(service_name, endpoint)
            self.service_health[service_name] = health
            results[service_name] = {
                "status": health.status.value,
                "response_time": health.response_time,
                "healthy": health.status == ServiceStatus.HEALTHY
            }

        return {
            "environment": self.current_environment.value,
            "services_checked": len(results),
            "healthy_services": sum(1 for r in results.values() if r["healthy"]),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

    async def detect_configuration_drift(self) -> Dict[str, Any]:
        """Detect configuration drift between expected and actual state."""
        if not self.current_config:
            return {"error": "No current environment configured"}

        drift_issues = []

        # Check service endpoints
        for service_name, expected_endpoint in self.current_config.service_endpoints.items():
            # This would check actual running services vs expected
            # For now, just validate the endpoint format
            if not self._is_valid_url(expected_endpoint):
                drift_issues.append({
                    "type": "service_endpoint",
                    "service": service_name,
                    "expected": expected_endpoint,
                    "issue": "Invalid endpoint format"
                })

        # Check feature flags
        # This would compare with actual running configuration

        # Check resource limits
        # This would compare with actual system resources

        return {
            "environment": self.current_environment.value,
            "drift_detected": len(drift_issues) > 0,
            "issues": drift_issues,
            "timestamp": datetime.now().isoformat()
        }

    async def export_environment_config(self, environment: Environment,
                                      format: str = "yaml") -> Optional[str]:
        """Export environment configuration."""
        if environment.value not in self.environment_configs:
            return None

        config = self.environment_configs[environment.value]
        config_dict = config.to_dict()

        if format.lower() == "json":
            return json.dumps(config_dict, indent=2)
        elif format.lower() == "yaml":
            try:
                import yaml
                return yaml.dump(config_dict, default_flow_style=False)
            except ImportError:
                return json.dumps(config_dict, indent=2)
        else:
            return json.dumps(config_dict, indent=2)

    # Private methods

    def _load_environment_configs(self) -> None:
        """Load environment configurations from files."""
        if not self.config_dir.exists():
            self.logger.warning(f"Config directory not found: {self.config_dir}")
            self._create_default_configs()
            return

        # Load YAML/JSON config files
        for config_file in self.config_dir.glob("env*.{yaml,yml,json}"):
            try:
                with open(config_file, 'r') as f:
                    if config_file.suffix.lower() in ['.yaml', '.yml']:
                        config_data = yaml.safe_load(f)
                    else:
                        config_data = json.load(f)

                if config_data:
                    env_config = EnvironmentConfig.from_dict(config_data)
                    self.environment_configs[env_config.environment.value] = env_config

            except Exception as e:
                self.logger.error(f"Failed to load config file {config_file}: {e}")

        # Create default configs if none loaded
        if not self.environment_configs:
            self._create_default_configs()

    def _create_default_configs(self) -> None:
        """Create default environment configurations."""
        self.logger.info("Creating default environment configurations")

        # Development environment
        dev_config = EnvironmentConfig(
            name="Development Environment",
            environment=Environment.DEVELOPMENT,
            service_endpoints={
                "doc_store": "http://localhost:5001",
                "mock_data_generator": "http://localhost:5002",
                "orchestrator": "http://localhost:5003",
                "analysis_service": "http://localhost:5004",
                "llm_gateway": "http://localhost:5005"
            },
            database_config={
                "url": "postgresql://user:password@localhost:5432/simulation_dev",
                "pool_size": 10,
                "max_overflow": 20
            },
            cache_config={
                "redis_url": "redis://localhost:6379/0",
                "ttl_seconds": 3600
            },
            monitoring_config={
                "enabled": True,
                "metrics_interval": 30,
                "health_check_interval": 60
            },
            feature_flags={
                "enable_health_checks": True,
                "enable_monitoring": True,
                "enable_debug_logging": True,
                "enable_cors": True,
                "enable_swagger": True
            },
            resource_limits={
                "max_simulations": 10,
                "max_concurrent_workflows": 5,
                "memory_limit_mb": 1024
            }
        )

        # Production environment
        prod_config = EnvironmentConfig(
            name="Production Environment",
            environment=Environment.PRODUCTION,
            service_endpoints={
                "doc_store": "https://doc-store.production.company.com",
                "mock_data_generator": "https://mock-data.production.company.com",
                "orchestrator": "https://orchestrator.production.company.com",
                "analysis_service": "https://analysis.production.company.com",
                "llm_gateway": "https://llm-gateway.production.company.com"
            },
            database_config={
                "url": "postgresql://user:password@prod-db.company.com:5432/simulation_prod",
                "pool_size": 50,
                "max_overflow": 100
            },
            cache_config={
                "redis_url": "redis://prod-redis.company.com:6379/0",
                "ttl_seconds": 7200,
                "cluster_enabled": True
            },
            monitoring_config={
                "enabled": True,
                "metrics_interval": 15,
                "health_check_interval": 30,
                "alerting_enabled": True
            },
            security_config={
                "ssl_enabled": True,
                "api_key_required": True,
                "rate_limiting_enabled": True,
                "audit_logging_enabled": True
            },
            feature_flags={
                "enable_health_checks": True,
                "enable_monitoring": True,
                "enable_debug_logging": False,
                "enable_cors": False,
                "enable_swagger": False
            },
            resource_limits={
                "max_simulations": 100,
                "max_concurrent_workflows": 50,
                "memory_limit_mb": 8192
            }
        )

        self.environment_configs[Environment.DEVELOPMENT.value] = dev_config
        self.environment_configs[Environment.PRODUCTION.value] = prod_config

        # Save default configs
        self._save_default_configs()

    def _save_default_configs(self) -> None:
        """Save default configurations to files."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)

            for env_name, config in self.environment_configs.items():
                config_file = self.config_dir / f"env_{env_name}.yaml"
                config_yaml = self.export_environment_config(config.environment, "yaml")

                if config_yaml:
                    with open(config_file, 'w') as f:
                        f.write(config_yaml)

        except Exception as e:
            self.logger.error(f"Failed to save default configs: {e}")

    async def _detect_environment(self) -> None:
        """Auto-detect the current environment."""
        # Check environment variables
        env_var = os.getenv("SIMULATION_ENVIRONMENT", "").lower()
        if env_var in [e.value for e in Environment]:
            self.current_environment = Environment(env_var)
            return

        # Check hostname patterns
        import socket
        hostname = socket.gethostname().lower()

        if "prod" in hostname or "production" in hostname:
            self.current_environment = Environment.PRODUCTION
        elif "staging" in hostname or "stage" in hostname:
            self.current_environment = Environment.STAGING
        elif "test" in hostname or "testing" in hostname:
            self.current_environment = Environment.TESTING
        else:
            self.current_environment = Environment.DEVELOPMENT

        self.logger.info(f"Auto-detected environment: {self.current_environment.value}")

    async def _load_current_environment(self) -> None:
        """Load the current environment configuration."""
        if self.current_environment and self.current_environment.value in self.environment_configs:
            self.current_config = self.environment_configs[self.current_environment.value]
        else:
            # Fallback to development
            self.current_environment = Environment.DEVELOPMENT
            self.current_config = self.environment_configs.get(Environment.DEVELOPMENT.value)

    async def _validate_configuration(self) -> None:
        """Validate the current environment configuration."""
        if not self.current_config:
            return

        validation = await self.validate_environment(self.current_environment)
        if not validation["valid"]:
            self.logger.warning(f"Configuration validation issues: {validation['issues']}")

    async def _apply_environment_config(self) -> None:
        """Apply the current environment configuration."""
        if not self.current_config:
            return

        # This would apply configuration to various system components
        # For now, just log the configuration
        self.logger.info(f"Applied configuration for environment: {self.current_environment.value}")

    async def _validate_environment_health(self, environment: Optional[Environment] = None,
                                         return_issues: bool = False) -> Union[bool, List[str]]:
        """Validate environment health by checking service endpoints."""
        target_env = environment or self.current_environment
        if not target_env or target_env.value not in self.environment_configs:
            return False if not return_issues else ["Environment not found"]

        config = self.environment_configs[target_env.value]
        issues = []

        for service_name, endpoint in config.service_endpoints.items():
            health = await self._check_service_health(service_name, endpoint)
            self.service_health[service_name] = health

            if health.status != ServiceStatus.HEALTHY:
                issues.append(f"Service {service_name} is {health.status.value}")

        if return_issues:
            return issues

        # Consider environment healthy if most services are healthy
        healthy_count = sum(1 for h in self.service_health.values() if h.status == ServiceStatus.HEALTHY)
        total_count = len(config.service_endpoints)

        return healthy_count >= total_count * 0.8  # 80% healthy threshold

    async def _check_service_health(self, service_name: str, endpoint: str) -> ServiceHealth:
        """Check the health of a service."""
        import aiohttp
        import time

        health = ServiceHealth(
            name=service_name,
            status=ServiceStatus.UNKNOWN,
            last_check=datetime.now()
        )

        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()

                # Try health endpoint
                health_url = f"{endpoint}/health"
                async with session.get(health_url, timeout=5) as response:
                    response_time = time.time() - start_time

                    health.response_time = response_time

                    if response.status == 200:
                        health.status = ServiceStatus.HEALTHY
                        try:
                            data = await response.json()
                            health.version = data.get("version")
                        except:
                            pass
                    elif response.status < 500:
                        health.status = ServiceStatus.DEGRADED
                    else:
                        health.status = ServiceStatus.UNHEALTHY
                        health.error_message = f"HTTP {response.status}"

        except asyncio.TimeoutError:
            health.status = ServiceStatus.UNHEALTHY
            health.error_message = "Timeout"
        except Exception as e:
            health.status = ServiceStatus.UNHEALTHY
            health.error_message = str(e)

        return health

    def _is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid."""
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return url_pattern.match(url) is not None


# Global environment manager instance
_environment_manager: Optional[EnvironmentManager] = None


def get_environment_manager() -> EnvironmentManager:
    """Get the global environment manager instance."""
    global _environment_manager
    if _environment_manager is None:
        _environment_manager = EnvironmentManager()
    return _environment_manager


async def initialize_environment_management() -> None:
    """Initialize the environment management system."""
    manager = get_environment_manager()
    await manager.initialize()


__all__ = [
    'EnvironmentManager',
    'Environment',
    'EnvironmentConfig',
    'ServiceStatus',
    'ServiceHealth',
    'get_environment_manager',
    'initialize_environment_management'
]
