"""
Environment configuration and safety checks.

This module provides environment-based configuration and
critical safety checks to prevent test data from contaminating
production environments.
"""

import os
from enum import Enum
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Application environment types."""
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TEST = "test"


class EnvironmentConfig:
    """Environment configuration manager."""
    
    @staticmethod
    def get_current_environment() -> Environment:
        """
        Get the current application environment.
        
        Returns:
            Environment: Current environment
        """
        env_str = os.getenv("APP_ENV", "development").lower()
        
        try:
            return Environment(env_str)
        except ValueError:
            logger.warning(
                f"Invalid APP_ENV '{env_str}', defaulting to development"
            )
            return Environment.DEVELOPMENT
    
    @staticmethod
    def is_test_environment() -> bool:
        """Check if running in test environment."""
        return (
            EnvironmentConfig.get_current_environment() == Environment.TEST
            or os.getenv("PYTEST_CURRENT_TEST") is not None
        )
    
    @staticmethod
    def is_production_environment() -> bool:
        """Check if running in production environment."""
        return EnvironmentConfig.get_current_environment() == Environment.PRODUCTION
    
    @staticmethod
    def validate_test_safety():
        """
        Validate that tests are not running in production.
        
        Raises:
            RuntimeError: If tests are attempted in production
        """
        if EnvironmentConfig.is_production_environment() and os.getenv("PYTEST_CURRENT_TEST"):
            raise RuntimeError(
                "🚨 CRITICAL SAFETY VIOLATION 🚨\n"
                "Tests cannot run in production environment!\n"
                "Set APP_ENV=test or APP_ENV=development\n"
                f"Current: APP_ENV={os.getenv('APP_ENV')}\n"
                f"Test: {os.getenv('PYTEST_CURRENT_TEST')}"
            )


def get_database_config() -> Dict[str, Any]:
    """
    Get database configuration based on environment.
    
    Returns:
        Dict[str, Any]: Database configuration
        
    Raises:
        RuntimeError: If attempting to run tests in production
    """
    # CRITICAL: Prevent tests from running in production
    EnvironmentConfig.validate_test_safety()
    
    env = EnvironmentConfig.get_current_environment()
    
    configs = {
        Environment.PRODUCTION: {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "ecosystem_mcp"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", ""),
            "allow_test_data": False,  # CRITICAL: No test data in production
            "auto_rollback": False,
        },
        Environment.STAGING: {
            "host": os.getenv("STAGING_DB_HOST", "localhost"),
            "port": int(os.getenv("STAGING_DB_PORT", "5432")),
            "database": os.getenv("STAGING_DB_NAME", "staging_ecosystem_mcp"),
            "user": os.getenv("STAGING_DB_USER", "postgres"),
            "password": os.getenv("STAGING_DB_PASSWORD", ""),
            "allow_test_data": False,  # No test data in staging
            "auto_rollback": False,
        },
        Environment.DEVELOPMENT: {
            "host": os.getenv("DEV_DB_HOST", "localhost"),
            "port": int(os.getenv("DEV_DB_PORT", "5432")),
            "database": os.getenv("DEV_DB_NAME", "dev_ecosystem_mcp"),
            "user": os.getenv("DEV_DB_USER", "postgres"),
            "password": os.getenv("DEV_DB_PASSWORD", "postgres"),
            "allow_test_data": True,  # Development can have test data
            "auto_rollback": False,
        },
        Environment.TEST: {
            "host": os.getenv("TEST_DB_HOST", "localhost"),
            "port": int(os.getenv("TEST_DB_PORT", "5433")),
            "database": os.getenv("TEST_DB_NAME", "test_ecosystem_mcp"),
            "user": os.getenv("TEST_DB_USER", "test_user"),
            "password": os.getenv("TEST_DB_PASSWORD", "test_pass"),
            "allow_test_data": True,  # Test environment requires test data
            "auto_rollback": True,  # Always rollback in tests
        }
    }
    
    config = configs.get(env, configs[Environment.DEVELOPMENT])
    config["environment"] = env.value
    
    logger.info(f"Database config for environment: {env.value}")
    logger.debug(f"Database: {config['database']} on {config['host']}:{config['port']}")
    
    return config


def get_redis_config() -> Dict[str, Any]:
    """
    Get Redis configuration based on environment.
    
    Returns:
        Dict[str, Any]: Redis configuration
    """
    env = EnvironmentConfig.get_current_environment()
    
    configs = {
        Environment.PRODUCTION: {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "db": int(os.getenv("REDIS_DB", "0")),
            "password": os.getenv("REDIS_PASSWORD"),
            "auto_flush": False,
        },
        Environment.STAGING: {
            "host": os.getenv("STAGING_REDIS_HOST", "localhost"),
            "port": int(os.getenv("STAGING_REDIS_PORT", "6379")),
            "db": int(os.getenv("STAGING_REDIS_DB", "1")),
            "password": os.getenv("STAGING_REDIS_PASSWORD"),
            "auto_flush": False,
        },
        Environment.DEVELOPMENT: {
            "host": os.getenv("DEV_REDIS_HOST", "localhost"),
            "port": int(os.getenv("DEV_REDIS_PORT", "6379")),
            "db": int(os.getenv("DEV_REDIS_DB", "0")),
            "password": None,
            "auto_flush": False,
        },
        Environment.TEST: {
            "host": os.getenv("TEST_REDIS_HOST", "localhost"),
            "port": int(os.getenv("TEST_REDIS_PORT", "6380")),
            "db": int(os.getenv("TEST_REDIS_DB", "0")),
            "password": None,
            "auto_flush": True,  # Always flush after tests
        }
    }
    
    config = configs.get(env, configs[Environment.DEVELOPMENT])
    config["environment"] = env.value
    
    return config


def get_chroma_config() -> Dict[str, Any]:
    """
    Get ChromaDB configuration based on environment.
    
    Returns:
        Dict[str, Any]: ChromaDB configuration
    """
    env = EnvironmentConfig.get_current_environment()
    
    configs = {
        Environment.PRODUCTION: {
            "host": os.getenv("CHROMA_HOST", "localhost"),
            "port": int(os.getenv("CHROMA_PORT", "8000")),
            "collection_prefix": "prod",
        },
        Environment.STAGING: {
            "host": os.getenv("STAGING_CHROMA_HOST", "localhost"),
            "port": int(os.getenv("STAGING_CHROMA_PORT", "8000")),
            "collection_prefix": "staging",
        },
        Environment.DEVELOPMENT: {
            "host": os.getenv("DEV_CHROMA_HOST", "localhost"),
            "port": int(os.getenv("DEV_CHROMA_PORT", "8000")),
            "collection_prefix": "dev",
        },
        Environment.TEST: {
            "host": os.getenv("TEST_CHROMA_HOST", "localhost"),
            "port": int(os.getenv("TEST_CHROMA_PORT", "8001")),
            "collection_prefix": "test",
        }
    }
    
    config = configs.get(env, configs[Environment.DEVELOPMENT])
    config["environment"] = env.value
    
    return config

