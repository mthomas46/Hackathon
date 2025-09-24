"""Unified Configuration System.

This module provides a standardized configuration management system
for all services in the LLM Documentation Ecosystem. Consolidates
46+ individual config files into a unified, type-safe configuration framework.
"""

from .base_config import BaseConfig, ConfigValidationError, ConfigLoader
from .service_config import (
    ServiceConfig,
    load_service_config,
    create_service_config,
    DocStoreConfig,
    AnalysisServiceConfig,
    OrchestratorConfig,
    PromptStoreConfig,
    DiscoveryAgentConfig,
    FrontendConfig,
    CLIConfig,
    SummarizerHubConfig,
)

__all__ = [
    "BaseConfig",
    "ConfigValidationError",
    "ConfigLoader",
    "EnvironmentConfig",
    "FileConfig",
    "ServiceConfig",
    "load_service_config",
    "create_service_config",
    "DocStoreConfig",
    "AnalysisServiceConfig",
    "OrchestratorConfig",
    "PromptStoreConfig",
    "DiscoveryAgentConfig",
    "FrontendConfig",
    "CLIConfig",
    "SummarizerHubConfig",
]
