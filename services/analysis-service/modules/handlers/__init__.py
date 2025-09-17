"""Refactored Analysis Handlers - Focused handler modules for different analysis types.

This package contains the refactored analysis handlers that were extracted from the
original monolithic analysis_handlers.py file (1969+ lines) to improve maintainability,
testability, and separation of concerns.
"""

from .base_handler import BaseAnalysisHandler
from .semantic_handler import SemanticAnalysisHandler
from .sentiment_handler import SentimentAnalysisHandler
from .quality_handler import QualityAnalysisHandler
from .trend_handler import TrendAnalysisHandler
from .risk_handler import RiskAnalysisHandler
from .maintenance_handler import MaintenanceAnalysisHandler
from .impact_handler import ImpactAnalysisHandler
from .remediation_handler import RemediationHandler
from .workflow_handler import WorkflowAnalysisHandler
from .distributed_handler import DistributedAnalysisHandler
from .cross_repository_handler import CrossRepositoryAnalysisHandler

__all__ = [
    'BaseAnalysisHandler',
    'SemanticAnalysisHandler',
    'SentimentAnalysisHandler',
    'QualityAnalysisHandler',
    'TrendAnalysisHandler',
    'RiskAnalysisHandler',
    'MaintenanceAnalysisHandler',
    'ImpactAnalysisHandler',
    'RemediationHandler',
    'WorkflowAnalysisHandler',
    'DistributedAnalysisHandler',
    'CrossRepositoryAnalysisHandler'
]
