"""
Quality Assurance Module

Provides quality validation, scoring, and review workflow management
for generated documentation.

Components:
- CompletenessChecker: Validates documentation completeness
- AccuracyValidator: Validates technical accuracy
- ConfidenceScorer: Calculates confidence scores
- ReviewWorkflowManager: Manages review queue
- QualityReporter: Generates quality metrics
"""

from .completeness_checker import (
    CompletenessChecker,
    CompletenessResult,
    SectionType,
    get_completeness_checker
)
from .accuracy_validator import (
    AccuracyValidator,
    AccuracyResult,
    get_accuracy_validator
)
from .confidence_scorer import (
    ConfidenceScorer,
    ConfidenceScore,
    get_confidence_scorer
)
from .review_workflow import (
    ReviewWorkflowManager,
    ReviewItem,
    ReviewStatus,
    get_review_workflow_manager
)
from .quality_reporter import (
    QualityReporter,
    QualityReport,
    get_quality_reporter
)

__all__ = [
    # Completeness
    'CompletenessChecker',
    'CompletenessResult',
    'SectionType',
    'get_completeness_checker',
    
    # Accuracy
    'AccuracyValidator',
    'AccuracyResult',
    'get_accuracy_validator',
    
    # Confidence
    'ConfidenceScorer',
    'ConfidenceScore',
    'get_confidence_scorer',
    
    # Review Workflow
    'ReviewWorkflowManager',
    'ReviewItem',
    'ReviewStatus',
    'get_review_workflow_manager',
    
    # Reporting
    'QualityReporter',
    'QualityReport',
    'get_quality_reporter',
]

