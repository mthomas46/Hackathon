"""
Model Router Integration (Week 3, Day 1, Task 1.2)

Integrates the enhanced model router with existing services:
- Documentation generation
- File analysis
- RAG queries
- General LLM tasks

Provides backward compatibility with existing code while enabling
smart model selection.
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from .enhanced_model_router import (
    get_enhanced_model_router,
    EnhancedModelRouter,
    TaskType
)

logger = logging.getLogger(__name__)


class ModelRouterIntegration:
    """
    Integration layer for enhanced model routing.
    
    Provides convenience methods for common use cases:
    - analyze_file: Analyze a file with optimal model
    - generate_docs: Generate documentation with optimal model
    - query_rag: Query RAG with optimal model
    - general_task: Execute general task with optimal model
    """
    
    def __init__(self):
        self.router = get_enhanced_model_router()
        logger.info("ModelRouterIntegration initialized")
    
    def select_model_for_file(
        self,
        file_path: str,
        content: Optional[str] = None
    ) -> str:
        """
        Select optimal model for file analysis.
        
        Args:
            file_path: Path to file
            content: Optional file content for detection
        
        Returns:
            Model name
        """
        if content:
            return self.router.select_model(
                content=content,
                file_path=file_path,
                task_type=TaskType.CODE_ANALYSIS
            )
        else:
            # No content, use file extension only
            if self.router.code_detector.is_code_file(file_path):
                return self.router._select_available_model(
                    self.router.model_priorities[TaskType.CODE_ANALYSIS]
                )
            else:
                return self.router._select_available_model(
                    self.router.model_priorities[TaskType.GENERAL_QUERY]
                )
    
    def select_model_for_documentation(
        self,
        content: str,
        file_path: Optional[str] = None,
        is_code: Optional[bool] = None
    ) -> str:
        """
        Select optimal model for documentation generation.
        
        Args:
            content: Content to document
            file_path: Optional file path
            is_code: Optional flag indicating if content is code
        
        Returns:
            Model name
        """
        # If explicitly told it's code, route to code model
        if is_code:
            return self.router._select_available_model(
                self.router.model_priorities[TaskType.CODE_ANALYSIS]
            )
        
        # Otherwise, use documentation model
        return self.router.select_model(
            content=content,
            file_path=file_path,
            task_type=TaskType.DOCUMENTATION
        )
    
    def select_model_for_rag(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Select optimal model for RAG query.
        
        Args:
            query: Query text
            context: Optional context info
        
        Returns:
            Model name
        """
        return self.router.select_model(
            content=query,
            task_type=TaskType.RAG_QUERY,
            is_rag_query=True,
            **(context or {})
        )
    
    def select_model_for_general_task(
        self,
        content: str,
        **context
    ) -> str:
        """
        Select optimal model for general task.
        
        Args:
            content: Content to process
            **context: Additional context
        
        Returns:
            Model name
        """
        return self.router.select_model(
            content=content,
            **context
        )
    
    def is_code_file(self, file_path: str) -> bool:
        """Check if file is a code file."""
        return self.router.code_detector.is_code_file(file_path)
    
    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file."""
        return self.router.code_detector.detect_language(file_path)
    
    def get_task_type(
        self,
        content: str,
        file_path: Optional[str] = None
    ) -> TaskType:
        """Get task type for content."""
        return self.router.get_task_type_for_content(content, file_path)


# Singleton
_integration_instance: Optional[ModelRouterIntegration] = None


def get_model_router_integration() -> ModelRouterIntegration:
    """Get singleton integration instance."""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = ModelRouterIntegration()
    return _integration_instance


# ============================================================================
# Backward Compatibility Wrappers
# ============================================================================

def select_model_for_analysis(
    file_path: str,
    content: Optional[str] = None
) -> str:
    """
    Backward compatible function for model selection.
    
    Can be used as drop-in replacement for existing code.
    """
    integration = get_model_router_integration()
    return integration.select_model_for_file(file_path, content)


def should_use_codellama(file_path: str) -> bool:
    """
    Check if CodeLlama should be used for file.
    
    Helper function for quick checks.
    """
    integration = get_model_router_integration()
    return integration.is_code_file(file_path)

