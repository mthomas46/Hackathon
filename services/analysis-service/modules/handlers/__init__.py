"""Handlers Package - Analysis handlers with dependency injection."""

from .base_handler import BaseAnalysisHandler, AnalysisResult, HandlerRegistry, handler_registry
from .factory import HandlerFactory, get_handler_factory, create_handler, initialize_handlers

# Handler classes
from .semantic_handler import SemanticAnalysisHandler
from .sentiment_handler import SentimentAnalysisHandler
from .quality_handler import QualityAnalysisHandler
from .trend_handler import TrendAnalysisHandler
from .risk_handler import RiskAnalysisHandler
from .maintenance_handler import MaintenanceAnalysisHandler
from .impact_handler import ChangeImpactAnalysisHandler
from .remediation_handler import RemediationHandler
from .workflow_handler import WorkflowAnalysisHandler
from .distributed_handler import DistributedAnalysisHandler
from .cross_repository_handler import CrossRepositoryAnalysisHandler

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