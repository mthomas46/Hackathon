"""
RAG Enhancement System

Provides modular enhancement pipeline for all RAG types.

Components:
- EnhancementConfig: Configuration with presets
- EnhancementHooks: Custom hooks for specialization
- QueryContext: Query state management
- EnhancementPipeline: Main orchestrator

Usage:
    from .enhancement_config import EnhancementConfig
    from .enhancement_pipeline import EnhancementPipeline
    
    # Create pipeline
    pipeline = EnhancementPipeline()
    
    # Execute with config
    result = await pipeline.execute(
        query="How does authentication work?",
        n_results=10,
        config=EnhancementConfig.default()
    )
"""

from .enhancement_config import EnhancementConfig
from .enhancement_hooks import EnhancementHooks
from .query_context import QueryContext
from .enhancement_pipeline import EnhancementPipeline

__all__ = [
    "EnhancementConfig",
    "EnhancementHooks",
    "QueryContext",
    "EnhancementPipeline",
]

