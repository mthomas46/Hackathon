"""
Multi-File Analysis Services (Phase 3)

Cross-file dependency analysis, architecture detection, and API extraction.
"""

from .dependency_analyzer import (
    DependencyAnalyzer,
    Dependency,
    DependencyGraph,
    get_dependency_analyzer
)
from .stack_detector import (
    TechnologyStackDetector,
    TechnologyStack,
    get_stack_detector
)
from .architecture_detector import (
    ArchitectureDetector,
    ArchitecturePattern,
    ArchitectureAnalysis,
    get_architecture_detector
)
from .service_detector import (
    ServiceBoundaryDetector,
    Service,
    ServiceMap,
    get_service_detector
)
from .analysis_engine import (
    AnalysisEngine,
    AnalysisReport,
    get_analysis_engine
)
from .context_generator import (
    ContextGenerator,
    RepositoryContext,
    get_context_generator
)

__all__ = [
    # Dependency Analysis
    "DependencyAnalyzer",
    "Dependency",
    "DependencyGraph",
    "get_dependency_analyzer",
    
    # Technology Stack
    "TechnologyStackDetector",
    "TechnologyStack",
    "get_stack_detector",
    
    # Architecture Detection
    "ArchitectureDetector",
    "ArchitecturePattern",
    "ArchitectureAnalysis",
    "get_architecture_detector",
    
    # Service Detection
    "ServiceBoundaryDetector",
    "Service",
    "ServiceMap",
    "get_service_detector",
    
    # Analysis Engine (Orchestration)
    "AnalysisEngine",
    "AnalysisReport",
    "get_analysis_engine",
    
    # Context Generator (RAG)
    "ContextGenerator",
    "RepositoryContext",
    "get_context_generator",
]
