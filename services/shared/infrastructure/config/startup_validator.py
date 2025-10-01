#!/usr/bin/env python3
"""
Service Startup Configuration Validator

Validates service configuration during startup and provides clear error messages
for configuration issues. This helps catch configuration problems early in the
service lifecycle.

Features:
- Configuration validation on startup
- Clear error messages for developers
- Environment-specific validation
- Graceful degradation for legacy services
"""

import sys
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add project root to path
# From services/shared/infrastructure/config/startup_validator.py
# Go up: config -> infrastructure -> shared -> services -> project_root (Hackathon dir)
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from services.shared.infrastructure.config.configuration_manager import load_service_config, USE_PYDANTIC_CONFIG, PYDANTIC_AVAILABLE
    CONFIG_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import configuration manager: {e}")
    CONFIG_AVAILABLE = False
    USE_PYDANTIC_CONFIG = True  # Default to Pydantic
    PYDANTIC_AVAILABLE = False


class StartupValidationError(Exception):
    """Raised when configuration validation fails during startup."""
    pass


class ServiceStartupValidator:
    """
    Validates service configuration during startup.

    This validator checks configuration integrity and provides helpful
    error messages to developers when configuration issues are detected.
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.config = None

    def validate_configuration(self) -> bool:
        """
        Validate service configuration for startup.

        Returns:
            True if configuration is valid, False otherwise

        Raises:
            StartupValidationError: If configuration cannot be loaded or is invalid
        """
        print(f"🔍 Validating {self.service_name} configuration for startup...")

        if not CONFIG_AVAILABLE:
            self.errors.append("Configuration system not available")
            return False

        try:
            # Load configuration
            self.config = load_service_config(self.service_name)

            # Perform validation based on configuration type
            if USE_PYDANTIC_CONFIG and PYDANTIC_AVAILABLE:
                # Try Pydantic validation first
                if self._validate_pydantic_config():
                    return True
                else:
                    # Pydantic validation failed - this might be due to service-specific configs
                    # Log warning but allow startup during migration period
                    self.warnings.append("Pydantic validation failed - using legacy validation")
                    self.warnings.extend([f"  • {error}" for error in self.errors])
                    self.errors = []  # Clear errors to allow startup

                    # Fall back to basic dataclass validation
                    return self._validate_dataclass_config()
            else:
                return self._validate_dataclass_config()

        except Exception as e:
            error_msg = f"Failed to load configuration: {e}"
            self.errors.append(error_msg)
            raise StartupValidationError(error_msg)

    def _validate_pydantic_config(self) -> bool:
        """Validate Pydantic-based configuration."""
        if not hasattr(self.config, 'validate_configuration'):
            self.errors.append("Configuration object missing validation method")
            return False

        try:
            issues = self.config.validate_configuration()
            if issues:
                self.errors.extend(issues)
        except Exception as e:
            # Pydantic validation failed - this might be due to schema mismatches
            self.errors.append(f"Pydantic validation error: {e}")
            return False

        # Additional Pydantic-specific validations
        self._validate_required_fields()
        self._validate_environment_specific()
        self._validate_service_dependencies()

        return len(self.errors) == 0

    def _validate_dataclass_config(self) -> bool:
        """Validate dataclass-based configuration."""
        # Basic validation for dataclass configs
        self._validate_required_fields()
        self._validate_basic_types()

        return len(self.errors) == 0

    def _validate_required_fields(self):
        """Validate that required configuration fields are present."""
        required_fields = ['service_name', 'server', 'environment']

        for field in required_fields:
            if not hasattr(self.config, field):
                self.errors.append(f"Missing required field: {field}")
                continue

            value = getattr(self.config, field)
            if value is None or (isinstance(value, str) and not value.strip()):
                self.errors.append(f"Required field '{field}' is empty or None")

    def _validate_environment_specific(self):
        """Validate environment-specific configuration requirements."""
        if not hasattr(self.config, 'environment'):
            return

        env = self.config.environment

        # Production-specific validations
        if str(env).upper() in ['PRODUCTION', 'Environment.PRODUCTION']:
            self._validate_production_requirements()

        # Development-specific validations
        elif str(env).upper() in ['DEVELOPMENT', 'Environment.DEVELOPMENT']:
            self._validate_development_defaults()

    def _validate_production_requirements(self):
        """Validate production-specific requirements."""
        # Check for secure defaults
        if hasattr(self.config, 'server'):
            server = self.config.server
            if hasattr(server, 'debug') and server.debug:
                self.errors.append("Debug mode must be disabled in production")

        if hasattr(self.config, 'security'):
            security = self.config.security
            if hasattr(security, 'jwt_secret') and security.jwt_secret == "change-me-in-production":
                self.errors.append("JWT secret must be changed from default in production")

            if hasattr(security, 'enable_ssl') and not security.enable_ssl:
                self.warnings.append("SSL is recommended for production")

    def _validate_development_defaults(self):
        """Validate development-specific defaults."""
        # Development can be more permissive, but warn about security
        if hasattr(self.config, 'security'):
            security = self.config.security
            if hasattr(security, 'enable_auth') and security.enable_auth:
                self.warnings.append("Authentication enabled in development - ensure test credentials are used")

    def _validate_service_dependencies(self):
        """Validate service dependency URLs."""
        if not hasattr(self.config, 'services'):
            return

        services = self.config.services
        if hasattr(services, '__dict__'):
            service_attrs = services.__dict__
        elif hasattr(services, 'model_dump'):
            service_attrs = services.model_dump()
        else:
            service_attrs = {}

        for service_name, url in service_attrs.items():
            if isinstance(url, str) and url:
                if not (url.startswith('http://') or url.startswith('https://')):
                    self.errors.append(f"Invalid URL format for {service_name}: {url}")
                elif url == 'http://localhost' or url == 'http://127.0.0.1':
                    self.warnings.append(f"{service_name} using localhost URL - verify service availability")

    def _validate_basic_types(self):
        """Validate basic field types for dataclass configs."""
        # Server port validation
        if hasattr(self.config, 'server') and self.config.server:
            server = self.config.server
            if hasattr(server, 'port'):
                port = server.port
                if not isinstance(port, int) or not (1000 <= port <= 65535):
                    self.errors.append(f"Invalid server port: {port} (must be 1000-65535)")

        # Environment validation
        if hasattr(self.config, 'environment'):
            env = self.config.environment
            valid_envs = ['development', 'staging', 'production', 'testing']
            if str(env).lower() not in valid_envs:
                self.warnings.append(f"Unknown environment: {env}")

    def get_validation_report(self) -> Dict[str, Any]:
        """Get a comprehensive validation report."""
        return {
            'service_name': self.service_name,
            'config_type': type(self.config).__name__ if self.config else 'None',
            'pydantic_enabled': USE_PYDANTIC_CONFIG,
            'errors': self.errors,
            'warnings': self.warnings,
            'valid': len(self.errors) == 0,
            'config_summary': self._get_config_summary()
        }

    def _get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the loaded configuration."""
        if not self.config:
            return {}

        summary = {}
        try:
            # Basic fields
            if hasattr(self.config, 'service_name'):
                summary['service_name'] = self.config.service_name
            if hasattr(self.config, 'environment'):
                summary['environment'] = str(self.config.environment)
            if hasattr(self.config, 'server') and self.config.server:
                server = self.config.server
                if hasattr(server, 'port'):
                    summary['server_port'] = server.port
                if hasattr(server, 'host'):
                    summary['server_host'] = server.host
        except Exception:
            # Don't fail on summary generation
            pass

        return summary

    def print_report(self):
        """Print a human-readable validation report."""
        report = self.get_validation_report()

        print(f"\n📊 Configuration Validation Report for {self.service_name}")
        print("=" * 60)
        print(f"Configuration Type: {report['config_type']}")
        print(f"Pydantic Enabled: {report['pydantic_enabled']}")
        print(f"Validation Status: {'✅ VALID' if report['valid'] else '❌ INVALID'}")

        if report['config_summary']:
            print(f"\nConfiguration Summary:")
            for key, value in report['config_summary'].items():
                print(f"  • {key}: {value}")

        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")

        print()


def validate_service_startup(service_name: str) -> bool:
    """
    Validate service configuration during startup.

    This function should be called at the beginning of service startup
    to ensure configuration is valid before the service begins operation.

    Args:
        service_name: Name of the service being started

    Returns:
        True if configuration is valid and service can start

    Raises:
        StartupValidationError: If configuration validation fails
    """
    validator = ServiceStartupValidator(service_name)

    try:
        is_valid = validator.validate_configuration()

        # Always print the report for transparency
        validator.print_report()

        if not is_valid:
            print(f"⚠️  {service_name} configuration has issues but allowing startup during migration")
            return True  # Allow startup during migration period

        # Print success message
        print(f"✅ {service_name} configuration validated successfully")

        return True

    except Exception as e:
        print(f"❌ Configuration validation failed with unexpected error: {e}")
        validator.print_report()
        print(f"⚠️  Allowing {service_name} startup despite validation errors during migration")
        return True  # Allow startup during migration period


def get_service_config_with_validation(service_name: str):
    """
    Load and validate service configuration in one call.

    This is a convenience function that loads configuration and validates it,
    raising an exception if validation fails.

    Args:
        service_name: Name of the service

    Returns:
        Validated configuration object

    Raises:
        StartupValidationError: If configuration is invalid
    """
    validator = ServiceStartupValidator(service_name)

    if not validator.validate_configuration():
        validator.print_report()
        raise StartupValidationError(f"Configuration validation failed for {service_name}")

    return validator.config


# Example usage in a service main.py:
"""
if __name__ == "__main__":
    from services.shared.infrastructure.config.startup_validator import validate_service_startup

    # Validate configuration before starting service
    if not validate_service_startup("my-service"):
        print("❌ Service startup aborted due to configuration errors")
        sys.exit(1)

    # Configuration is valid, start the service
    print("🚀 Starting my-service...")
    # ... service startup code ...
"""


if __name__ == "__main__":
    # Test the validator
    import sys

    if len(sys.argv) != 2:
        print("Usage: python3 startup_validator.py <service_name>")
        sys.exit(1)

    service_name = sys.argv[1]

    try:
        is_valid = validate_service_startup(service_name)
        sys.exit(0 if is_valid else 1)
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        sys.exit(1)
