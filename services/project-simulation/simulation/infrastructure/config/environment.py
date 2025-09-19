"""Environment Configuration - Environment-Specific Settings.

Handles environment-specific configuration with automatic detection,
validation, and environment-aware defaults for the Project Simulation Service.
"""

import os
import platform
from typing import Dict, Any, Optional, List
from pathlib import Path

from .config_manager import ConfigManager, get_config
from ..logging import get_simulation_logger


class EnvironmentDetector:
    """Environment detection and configuration."""

    @staticmethod
    def detect_environment() -> str:
        """Detect the current environment."""
        # Check explicit environment variable
        env = os.getenv("ENVIRONMENT")
        if env:
            return env.lower()

        # Check for development indicators
        if EnvironmentDetector._is_development_environment():
            return "development"

        # Check for testing indicators
        if EnvironmentDetector._is_testing_environment():
            return "testing"

        # Check for staging indicators
        if EnvironmentDetector._is_staging_environment():
            return "staging"

        # Default to production
        return "production"

    @staticmethod
    def _is_development_environment() -> bool:
        """Check if running in development environment."""
        indicators = [
            # Development tools and files
            Path(".git").exists(),
            Path("requirements-dev.txt").exists(),
            Path("pyproject.toml").exists(),

            # Environment variables
            os.getenv("DEBUG", "").lower() == "true",
            os.getenv("RELOAD", "").lower() == "true",
            os.getenv("PYDEVD_ENABLE", "").lower() == "true",

            # Host information
            platform.node().startswith(("localhost", "desktop", "laptop")),
            os.getenv("USER", "").startswith(("dev", "user")),

            # Development ports
            os.getenv("PORT", "").startswith(("3000", "5000", "8000", "8080"))
        ]

        return any(indicators)

    @staticmethod
    def _is_testing_environment() -> bool:
        """Check if running in testing environment."""
        indicators = [
            # Test files and directories
            Path("tests").exists(),
            Path("pytest.ini").exists(),
            Path(".coverage").exists(),

            # Test environment variables
            os.getenv("PYTEST_CURRENT_TEST"),
            os.getenv("TESTING", "").lower() == "true",
            os.getenv("CI", "").lower() == "true",

            # Test database
            "test" in os.getenv("DATABASE_URL", "").lower()
        ]

        return any(indicators)

    @staticmethod
    def _is_staging_environment() -> bool:
        """Check if running in staging environment."""
        indicators = [
            # Staging-specific variables
            os.getenv("STAGING", "").lower() == "true",
            "staging" in os.getenv("DATABASE_URL", "").lower(),
            "staging" in platform.node().lower()
        ]

        return any(indicators)


class EnvironmentConfig:
    """Environment-specific configuration handler."""

    def __init__(self, environment: Optional[str] = None):
        """Initialize environment configuration."""
        self.logger = get_simulation_logger()
        self.environment = environment or EnvironmentDetector.detect_environment()
        self.config_manager = ConfigManager()
        self._config_overrides: Dict[str, Any] = {}

    def load_environment_config(self) -> Dict[str, Any]:
        """Load environment-specific configuration."""
        config = self.config_manager.load_config(self.environment)

        # Apply environment-specific overrides
        self._apply_environment_overrides(config)

        # Apply runtime overrides
        self._apply_runtime_overrides(config)

        self.logger.info("Environment configuration loaded",
                        environment=self.environment,
                        overrides=len(self._config_overrides))

        return config

    def _apply_environment_overrides(self, config):
        """Apply environment-specific configuration overrides."""
        overrides = self._get_environment_overrides()
        self._apply_overrides(config, overrides)

    def _apply_runtime_overrides(self, config):
        """Apply runtime configuration overrides."""
        overrides = self._get_runtime_overrides()
        self._apply_overrides(config, overrides)

    def _get_environment_overrides(self) -> Dict[str, Any]:
        """Get environment-specific overrides."""
        if self.environment == "development":
            return self._get_development_overrides()
        elif self.environment == "testing":
            return self._get_testing_overrides()
        elif self.environment == "staging":
            return self._get_staging_overrides()
        elif self.environment == "production":
            return self._get_production_overrides()
        else:
            return {}

    def _get_development_overrides(self) -> Dict[str, Any]:
        """Get development environment overrides."""
        return {
            "service": {
                "debug": True,
                "reload": True,
                "log_level": "DEBUG"
            },
            "development": {
                "enable_swagger": True,
                "enable_redoc": True,
                "enable_cors": True,
                "cors_origins": ["http://localhost:3000", "http://localhost:8080"],
                "auto_reload": True,
                "debug_mode": True
            },
            "security": {
                "rate_limit_enabled": False,
                "circuit_breaker_failure_threshold": 10
            },
            "monitoring": {
                "enable_profiling": False
            },
            "features": {
                "enable_advanced_analytics": True,
                "enable_real_time_updates": True,
                "enable_extended_logging": True,
                "enable_detailed_metrics": True
            },
            "database": {
                "url": "sqlite:///./data/project_simulation_dev.db"
            }
        }

    def _get_testing_overrides(self) -> Dict[str, Any]:
        """Get testing environment overrides."""
        return {
            "service": {
                "debug": False,
                "reload": False,
                "log_level": "WARNING"
            },
            "database": {
                "url": "sqlite:///:memory:"  # In-memory database for tests
            },
            "testing": {
                "use_mock_services": True,
                "mock_data_enabled": True
            },
            "security": {
                "rate_limit_enabled": False
            },
            "monitoring": {
                "enable_metrics": False,
                "enable_profiling": False
            },
            "features": {
                "enable_advanced_analytics": False,
                "enable_real_time_updates": False,
                "enable_extended_logging": False,
                "enable_detailed_metrics": False
            }
        }

    def _get_staging_overrides(self) -> Dict[str, Any]:
        """Get staging environment overrides."""
        return {
            "service": {
                "debug": False,
                "reload": False,
                "log_level": "INFO"
            },
            "monitoring": {
                "enable_metrics": True,
                "enable_profiling": True
            },
            "security": {
                "rate_limit_enabled": True,
                "circuit_breaker_failure_threshold": 5
            }
        }

    def _get_production_overrides(self) -> Dict[str, Any]:
        """Get production environment overrides."""
        return {
            "service": {
                "debug": False,
                "reload": False,
                "log_level": "WARNING"
            },
            "monitoring": {
                "enable_metrics": True,
                "enable_profiling": False
            },
            "security": {
                "rate_limit_enabled": True,
                "circuit_breaker_failure_threshold": 3
            },
            "development": {
                "enable_swagger": False,
                "enable_redoc": False,
                "auto_reload": False,
                "debug_mode": False
            }
        }

    def _get_runtime_overrides(self) -> Dict[str, Any]:
        """Get runtime configuration overrides."""
        overrides = {}

        # Check for runtime flags
        if os.getenv("DEBUG_MODE", "").lower() == "true":
            overrides.setdefault("service", {})["debug"] = True
            overrides.setdefault("development", {})["debug_mode"] = True

        if os.getenv("ENABLE_PROFILING", "").lower() == "true":
            overrides.setdefault("monitoring", {})["enable_profiling"] = True

        if os.getenv("DISABLE_RATE_LIMITS", "").lower() == "true":
            overrides.setdefault("security", {})["rate_limit_enabled"] = False

        return overrides

    def _apply_overrides(self, config, overrides: Dict[str, Any]):
        """Apply configuration overrides."""
        for section_name, section_overrides in overrides.items():
            if hasattr(config, section_name):
                section = getattr(config, section_name)
                for key, value in section_overrides.items():
                    if hasattr(section, key):
                        setattr(section, key, value)
                        self._config_overrides[f"{section_name}.{key}"] = value

    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment information."""
        return {
            "environment": self.environment,
            "detected": EnvironmentDetector.detect_environment(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "user": os.getenv("USER", "unknown"),
            "overrides_applied": len(self._config_overrides),
            "config_overrides": self._config_overrides
        }

    def validate_environment(self) -> List[str]:
        """Validate environment configuration."""
        issues = []

        # Check required directories
        required_dirs = ["./data", "./logs", "./cache"]
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                issues.append(f"Required directory missing: {dir_path}")

        # Check required environment variables for production
        if self.environment == "production":
            required_vars = ["DATABASE_URL", "REDIS_URL", "JWT_SECRET"]
            for var in required_vars:
                if not os.getenv(var):
                    issues.append(f"Required environment variable missing: {var}")

        # Check service URLs
        service_urls = self.config_manager.get_service_urls()
        for service_name, url in service_urls.items():
            if not url or url == "http://localhost:0":
                issues.append(f"Service URL not configured: {service_name}")

        return issues

    def setup_environment(self):
        """Setup environment-specific configuration."""
        # Create required directories
        dirs_to_create = ["./data", "./logs", "./cache", "./profiling"]
        for dir_path in dirs_to_create:
            Path(dir_path).mkdir(exist_ok=True)

        # Setup logging
        self._setup_logging()

        # Setup database
        self._setup_database()

        # Setup monitoring
        self._setup_monitoring()

        self.logger.info("Environment setup completed", environment=self.environment)

    def _setup_logging(self):
        """Setup environment-specific logging."""
        config = get_config()

        # Create log directory if file logging is enabled
        if config.logging.enable_file and config.logging.log_file:
            log_dir = Path(config.logging.log_file).parent
            log_dir.mkdir(exist_ok=True)

    def _setup_database(self):
        """Setup environment-specific database."""
        config = get_config()

        if "sqlite" in config.database.url:
            # Ensure SQLite database directory exists
            db_path = Path(config.database.url.replace("sqlite:///", ""))
            db_path.parent.mkdir(exist_ok=True)

    def _setup_monitoring(self):
        """Setup environment-specific monitoring."""
        config = get_config()

        if config.monitoring.enable_profiling:
            # Ensure profiling directory exists
            Path(config.monitoring.profiling_output_dir).mkdir(exist_ok=True)

    def print_environment_info(self):
        """Print environment information."""
        info = self.get_environment_info()
        issues = self.validate_environment()

        print("=== Environment Configuration ===")
        print(f"Environment: {info['environment']}")
        print(f"Detected: {info['detected']}")
        print(f"Platform: {info['platform']}")
        print(f"Python: {info['python_version']}")
        print(f"Hostname: {info['hostname']}")
        print(f"User: {info['user']}")
        print(f"Overrides Applied: {info['overrides_applied']}")

        if issues:
            print("⚠️  Configuration Issues:")
            for issue in issues:
                print(f"  - {issue}")

        if info['config_overrides']:
            print("🔧 Applied Overrides:")
            for key, value in info['config_overrides'].items():
                print(f"  - {key}: {value}")

        print("✅ Environment setup complete\n")


def get_environment_config() -> EnvironmentConfig:
    """Get the current environment configuration."""
    return EnvironmentConfig()


def setup_environment():
    """Setup the current environment."""
    env_config = get_environment_config()
    env_config.setup_environment()
    return env_config


def print_env_info():
    """Print environment information."""
    env_config = get_environment_config()
    env_config.print_environment_info()


def validate_environment() -> List[str]:
    """Validate the current environment configuration."""
    env_config = get_environment_config()
    return env_config.validate_environment()


# Convenience functions
def is_development() -> bool:
    """Check if running in development environment."""
    return EnvironmentDetector.detect_environment() == "development"


def is_testing() -> bool:
    """Check if running in testing environment."""
    return EnvironmentDetector.detect_environment() == "testing"


def is_production() -> bool:
    """Check if running in production environment."""
    return EnvironmentDetector.detect_environment() == "production"


__all__ = [
    'EnvironmentDetector',
    'EnvironmentConfig',
    'get_environment_config',
    'setup_environment',
    'print_env_info',
    'validate_environment',
    'is_development',
    'is_testing',
    'is_production'
]
