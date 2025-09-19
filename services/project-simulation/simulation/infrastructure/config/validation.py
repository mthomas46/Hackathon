"""Configuration Validation - Validate Configuration Settings.

Provides comprehensive validation for configuration settings with
detailed error reporting and suggestions for the Project Simulation Service.
"""

import re
import socket
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse
from pathlib import Path

from .config_manager import ConfigManager, get_config
from ..logging import get_simulation_logger


class ValidationError(Exception):
    """Configuration validation error."""

    def __init__(self, field: str, message: str, suggestion: Optional[str] = None):
        """Initialize validation error."""
        self.field = field
        self.message = message
        self.suggestion = suggestion
        super().__init__(f"{field}: {message}")


class ConfigValidator:
    """Configuration validator with comprehensive validation rules."""

    def __init__(self):
        """Initialize configuration validator."""
        self.logger = get_simulation_logger()
        self.errors: List[ValidationError] = []
        self.warnings: List[str] = []

    def validate_config(self, config) -> bool:
        """Validate the entire configuration."""
        self.errors.clear()
        self.warnings.clear()

        try:
            # Validate service configuration
            self._validate_service_config(config.service)

            # Validate database configuration
            self._validate_database_config(config.database)

            # Validate Redis configuration
            self._validate_redis_config(config.redis)

            # Validate ecosystem configuration
            self._validate_ecosystem_config(config.ecosystem)

            # Validate external services
            self._validate_external_services_config(config.external)

            # Validate security configuration
            self._validate_security_config(config.security)

            # Validate logging configuration
            self._validate_logging_config(config.logging)

            # Validate monitoring configuration
            self._validate_monitoring_config(config.monitoring)

            # Validate paths and directories
            self._validate_paths()

            # Cross-validation
            self._validate_cross_dependencies(config)

        except Exception as e:
            self.errors.append(ValidationError("general", f"Validation failed: {str(e)}"))

        return len(self.errors) == 0

    def _validate_service_config(self, service_config):
        """Validate service configuration."""
        # Service name
        if not service_config.name or not service_config.name.strip():
            self.errors.append(ValidationError(
                "service.name",
                "Service name is required",
                "Set SERVICE_NAME environment variable"
            ))

        # Version format
        if not re.match(r'^\d+\.\d+\.\d+', service_config.version):
            self.errors.append(ValidationError(
                "service.version",
                "Service version must be in format x.y.z",
                "Use semantic versioning (e.g., 1.0.0)"
            ))

        # Port range
        if not (1024 <= service_config.port <= 65535):
            self.errors.append(ValidationError(
                "service.port",
                "Port must be between 1024 and 65535",
                "Choose a port in the valid range"
            ))

        # Log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if service_config.log_level.upper() not in valid_log_levels:
            self.errors.append(ValidationError(
                "service.log_level",
                f"Log level must be one of: {', '.join(valid_log_levels)}",
                "Use a valid Python logging level"
            ))

    def _validate_database_config(self, db_config):
        """Validate database configuration."""
        # Database URL format
        if not db_config.url:
            self.errors.append(ValidationError(
                "database.url",
                "Database URL is required",
                "Set DATABASE_URL environment variable"
            ))
        else:
            parsed = urlparse(db_config.url)
            if not parsed.scheme:
                self.errors.append(ValidationError(
                    "database.url",
                    "Database URL must include scheme (e.g., postgresql://, sqlite:///)",
                    "Use proper database URL format"
                ))

            # SQLite path validation
            if parsed.scheme == "sqlite":
                db_path = parsed.path.lstrip("/")
                if db_path and db_path != ":memory:":
                    db_file = Path(db_path)
                    if not db_file.parent.exists():
                        self.warnings.append(f"SQLite database directory does not exist: {db_file.parent}")

        # Connection pool settings
        if db_config.pool_size < 1:
            self.errors.append(ValidationError(
                "database.pool_size",
                "Database pool size must be at least 1",
                "Set DATABASE_POOL_SIZE to a positive integer"
            ))

        if db_config.max_overflow < 0:
            self.errors.append(ValidationError(
                "database.max_overflow",
                "Database max overflow cannot be negative",
                "Set DATABASE_MAX_OVERFLOW to a non-negative integer"
            ))

    def _validate_redis_config(self, redis_config):
        """Validate Redis configuration."""
        if not redis_config.url:
            self.errors.append(ValidationError(
                "redis.url",
                "Redis URL is required",
                "Set REDIS_URL environment variable"
            ))
        else:
            parsed = urlparse(redis_config.url)
            if parsed.scheme not in ["redis", "rediss"]:
                self.errors.append(ValidationError(
                    "redis.url",
                    "Redis URL must use redis:// or rediss:// scheme",
                    "Use proper Redis URL format"
                ))

        # Connection settings
        if redis_config.max_connections < 1:
            self.errors.append(ValidationError(
                "redis.max_connections",
                "Redis max connections must be at least 1",
                "Set REDIS_MAX_CONNECTIONS to a positive integer"
            ))

        if redis_config.socket_timeout < 1:
            self.errors.append(ValidationError(
                "redis.socket_timeout",
                "Redis socket timeout must be at least 1 second",
                "Set REDIS_SOCKET_TIMEOUT to a positive integer"
            ))

    def _validate_ecosystem_config(self, ecosystem_config):
        """Validate ecosystem service configuration."""
        services = {
            "mock_data_generator": ecosystem_config.mock_data_generator_url,
            "analysis_service": ecosystem_config.analysis_service_url,
            "interpreter": ecosystem_config.interpreter_url,
            "doc_store": ecosystem_config.doc_store_url,
            "llm_gateway": ecosystem_config.llm_gateway_url,
            "notification_service": ecosystem_config.notification_service_url,
            "log_collector": ecosystem_config.log_collector_url,
            "discovery_agent": ecosystem_config.discovery_agent_url,
            "orchestrator": ecosystem_config.orchestrator_url,
            "frontend": ecosystem_config.frontend_url
        }

        for service_name, url in services.items():
            self._validate_service_url(f"ecosystem.{service_name}", url)

    def _validate_external_services_config(self, external_config):
        """Validate external services configuration."""
        # Ollama URL
        self._validate_service_url("external.ollama_base_url", external_config.ollama_base_url)

        # Ollama model
        if not external_config.ollama_model:
            self.errors.append(ValidationError(
                "external.ollama_model",
                "Ollama model name is required",
                "Set OLLAMA_MODEL environment variable"
            ))

    def _validate_security_config(self, security_config):
        """Validate security configuration."""
        # JWT secret for production
        if get_config().service.environment == "production":
            if not security_config.jwt_secret:
                self.errors.append(ValidationError(
                    "security.jwt_secret",
                    "JWT secret is required in production",
                    "Set JWT_SECRET environment variable with a secure random string"
                ))
            elif len(security_config.jwt_secret) < 32:
                self.errors.append(ValidationError(
                    "security.jwt_secret",
                    "JWT secret must be at least 32 characters long",
                    "Use a cryptographically secure random string of at least 32 characters"
                ))

        # API key for production
        if get_config().service.environment == "production":
            if not security_config.api_key:
                self.errors.append(ValidationError(
                    "security.api_key",
                    "API key is required in production",
                    "Set API_KEY environment variable with a secure key"
                ))

        # Circuit breaker settings
        if security_config.circuit_breaker_failure_threshold < 1:
            self.errors.append(ValidationError(
                "security.circuit_breaker_failure_threshold",
                "Circuit breaker failure threshold must be at least 1",
                "Set CIRCUIT_BREAKER_FAILURE_THRESHOLD to a positive integer"
            ))

        if security_config.circuit_breaker_recovery_timeout < 1:
            self.errors.append(ValidationError(
                "security.circuit_breaker_recovery_timeout",
                "Circuit breaker recovery timeout must be at least 1 second",
                "Set CIRCUIT_BREAKER_RECOVERY_TIMEOUT to a positive integer"
            ))

    def _validate_logging_config(self, logging_config):
        """Validate logging configuration."""
        # Log format
        valid_formats = ["json", "text", "structured"]
        if logging_config.format.lower() not in valid_formats:
            self.errors.append(ValidationError(
                "logging.format",
                f"Log format must be one of: {', '.join(valid_formats)}",
                "Choose a valid log format"
            ))

        # Log file validation
        if logging_config.enable_file and logging_config.log_file:
            log_file = Path(logging_config.log_file)
            if not log_file.parent.exists():
                self.warnings.append(f"Log file directory does not exist: {log_file.parent}")

    def _validate_monitoring_config(self, monitoring_config):
        """Validate monitoring configuration."""
        # Metrics port
        if not (1024 <= monitoring_config.metrics_port <= 65535):
            self.errors.append(ValidationError(
                "monitoring.metrics_port",
                "Metrics port must be between 1024 and 65535",
                "Choose a port in the valid range"
            ))

        # Profiling directory
        if monitoring_config.enable_profiling:
            profile_dir = Path(monitoring_config.profiling_output_dir)
            if not profile_dir.exists():
                self.warnings.append(f"Profiling directory does not exist: {profile_dir}")

    def _validate_service_url(self, field_name: str, url: str):
        """Validate a service URL."""
        if not url:
            self.errors.append(ValidationError(
                field_name,
                "Service URL is required",
                f"Set {field_name.upper().replace('.', '_')} environment variable"
            ))
            return

        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                self.errors.append(ValidationError(
                    field_name,
                    "Service URL must be a valid HTTP/HTTPS URL",
                    "Use format: http://hostname:port or https://hostname:port"
                ))
        except Exception as e:
            self.errors.append(ValidationError(
                field_name,
                f"Invalid URL format: {str(e)}",
                "Use a properly formatted URL"
            ))

    def _validate_paths(self):
        """Validate file paths and directories."""
        config = get_config()

        # Database path for SQLite
        if "sqlite" in config.database.url and ":memory:" not in config.database.url:
            db_path = Path(config.database.url.replace("sqlite:///", ""))
            if not db_path.parent.exists():
                self.warnings.append(f"SQLite database directory does not exist: {db_path.parent}")

        # Log file directory
        if config.logging.enable_file and config.logging.log_file:
            log_dir = Path(config.logging.log_file).parent
            if not log_dir.exists():
                self.warnings.append(f"Log directory does not exist: {log_dir}")

        # Profiling directory
        if config.monitoring.enable_profiling:
            profile_dir = Path(config.monitoring.profiling_output_dir)
            if not profile_dir.exists():
                self.warnings.append(f"Profiling directory does not exist: {profile_dir}")

    def _validate_cross_dependencies(self, config):
        """Validate cross-configuration dependencies."""
        # Development features in production
        if config.service.environment == "production":
            if config.development.enable_swagger:
                self.warnings.append("Swagger UI is enabled in production")

            if config.development.debug_mode:
                self.errors.append(ValidationError(
                    "development.debug_mode",
                    "Debug mode should not be enabled in production",
                    "Set DEBUG_MODE=false in production"
                ))

            if not config.security.rate_limit_enabled:
                self.errors.append(ValidationError(
                    "security.rate_limit_enabled",
                    "Rate limiting should be enabled in production",
                    "Set RATE_LIMIT_ENABLED=true in production"
                ))

        # Test database in production
        if config.service.environment == "production" and "test" in config.database.url.lower():
            self.errors.append(ValidationError(
                "database.url",
                "Test database should not be used in production",
                "Use production database URL"
            ))

    def get_validation_report(self) -> Dict[str, Any]:
        """Get validation report."""
        return {
            "valid": len(self.errors) == 0,
            "errors": [{"field": e.field, "message": e.message, "suggestion": e.suggestion} for e in self.errors],
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings)
        }

    def print_validation_report(self):
        """Print validation report."""
        report = self.get_validation_report()

        print("=== Configuration Validation Report ===")
        print(f"Valid: {'✅' if report['valid'] else '❌'}")
        print(f"Errors: {report['error_count']}")
        print(f"Warnings: {report['warning_count']}")

        if report['errors']:
            print("❌ Errors:")
            for error in report['errors']:
                print(f"  • {error['field']}: {error['message']}")
                if error['suggestion']:
                    print(f"    💡 {error['suggestion']}")

        if report['warnings']:
            print("⚠️  Warnings:")
            for warning in report['warnings']:
                print(f"  • {warning}")

        if report['valid']:
            print("✅ Configuration is valid!\n")


def validate_configuration() -> bool:
    """Validate the current configuration."""
    config = get_config()
    validator = ConfigValidator()
    return validator.validate_config(config)


def get_validation_report() -> Dict[str, Any]:
    """Get configuration validation report."""
    config = get_config()
    validator = ConfigValidator()
    validator.validate_config(config)
    return validator.get_validation_report()


def print_validation_report():
    """Print configuration validation report."""
    config = get_config()
    validator = ConfigValidator()
    validator.validate_config(config)
    validator.print_validation_report()


__all__ = [
    'ValidationError',
    'ConfigValidator',
    'validate_configuration',
    'get_validation_report',
    'print_validation_report'
]
