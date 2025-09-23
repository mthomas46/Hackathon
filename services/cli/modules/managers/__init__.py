"""CLI managers for different service operations."""

# Import specialized manager modules
from .analysis.analysis_service_manager import AnalysisServiceManager
from .config.config_manager import ConfigManager
from .monitoring.advanced_monitoring_manager import AdvancedMonitoringManager
from .prompt_manager import PromptManager

# Import service-specific managers
from .services import (
    AnalysisManager,
    ArchitectureDigitizerManager,
    BedrockProxyManager,
    BulkOperationsManager,
    CodeAnalyzerManager,
    DeploymentManager,
    DiscoveryAgentManager,
    DocStoreManager,
    InfrastructureManager,
    InterpreterManager,
    LogCollectorManager,
    MemoryAgentManager,
    NotificationServiceManager,
    OrchestratorManager,
    SecureAnalyzerManager,
    SourceAgentManager,
    SummarizerHubManager,
)

# Import workflow and prompt managers
from .workflow_manager import WorkflowManager

__all__ = [
    "ConfigManager",
    "OrchestratorManager",
    "AnalysisManager",
    "DocStoreManager",
    "SourceAgentManager",
    "InfrastructureManager",
    "BulkOperationsManager",
    "InterpreterManager",
    "DiscoveryAgentManager",
    "MemoryAgentManager",
    "SecureAnalyzerManager",
    "SummarizerHubManager",
    "CodeAnalyzerManager",
    "NotificationServiceManager",
    "LogCollectorManager",
    "BedrockProxyManager",
    "AnalysisServiceManager",
    "DeploymentManager",
    "AdvancedMonitoringManager",
    "ArchitectureDigitizerManager",
    "WorkflowManager",
    "PromptManager",
]
