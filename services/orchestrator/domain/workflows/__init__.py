"""
Workflow modules for Enhanced Roadmap v2.0
Phase 2: Natural Language Interface - 4 Parallel Workflows
"""

from .feature_decomposition_workflow import (
    FeatureDecompositionWorkflow,
    UserStory,
    TechnicalTask,
    FeatureBreakdown
)

from .historical_context_workflow import (
    HistoricalContextWorkflow,
    ContextSource,
    HistoricalContext
)

from .timeline_analysis_workflow import (
    TimelineAnalysisWorkflow,
    TimelineEstimate,
    HistoricalTrend,
    TimelineAnalysisResult
)

from .skills_matching_workflow import (
    SkillsMatchingWorkflow,
    TeamMember,
    SkillGap,
    ResourceAllocation,
    SkillsMatchingResult
)

__all__ = [
    # Workflow A
    "FeatureDecompositionWorkflow",
    "UserStory",
    "TechnicalTask",
    "FeatureBreakdown",
    # Workflow B
    "HistoricalContextWorkflow",
    "ContextSource",
    "HistoricalContext",
    # Workflow C
    "TimelineAnalysisWorkflow",
    "TimelineEstimate",
    "HistoricalTrend",
    "TimelineAnalysisResult",
    # Workflow D
    "SkillsMatchingWorkflow",
    "TeamMember",
    "SkillGap",
    "ResourceAllocation",
    "SkillsMatchingResult"
]

