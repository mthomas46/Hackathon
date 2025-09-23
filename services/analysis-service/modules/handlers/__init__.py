"""Handlers Package - Analysis handlers with dependency injection."""

from .base_handler import AnalysisResult, BaseAnalysisHandler, HandlerRegistry, handler_registry
from .cross_repository_handler import CrossRepositoryAnalysisHandler
from .distributed_handler import DistributedAnalysisHandler
from .factory import HandlerFactory, create_handler, get_handler_factory, initialize_handlers
from .impact_handler import ChangeImpactAnalysisHandler
from .maintenance_handler import MaintenanceAnalysisHandler
from .quality_handler import QualityAnalysisHandler
from .remediation_handler import RemediationHandler
from .risk_handler import RiskAnalysisHandler

# Handler classes
from .semantic_handler import SemanticAnalysisHandler
from .sentiment_handler import SentimentAnalysisHandler
from .trend_handler import TrendAnalysisHandler
from .workflow_handler import WorkflowAnalysisHandler

__all__ = [
    # Base components
    "BaseAnalysisHandler",
    "AnalysisResult",
    "HandlerRegistry",
    "handler_registry",
    # Factory components
    "HandlerFactory",
    "get_handler_factory",
    "create_handler",
    "initialize_handlers",
    # Handler classes
    "SemanticAnalysisHandler",
    "SentimentAnalysisHandler",
    "QualityAnalysisHandler",
    "TrendAnalysisHandler",
    "RiskAnalysisHandler",
    "MaintenanceAnalysisHandler",
    "ChangeImpactAnalysisHandler",
    "RemediationHandler",
    "WorkflowAnalysisHandler",
    "DistributedAnalysisHandler",
    "CrossRepositoryAnalysisHandler",
]
