"""
Model router for intelligent AI model selection.

Routes tasks to optimal models based on complexity, cost, and availability.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

from ..models import TaskType, ModelType
from .models.ollama_client import get_ollama_client
from .models.claude_client import get_claude_client
from .models.cursor_client import get_cursor_client

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Represents a task to be routed to a model."""
    
    type: TaskType
    prompt: str
    system: Optional[str] = None
    input_tokens: int = 0
    requires_reasoning: bool = False
    complexity: float = 0.5  # 0.0 (simple) to 1.0 (complex)


@dataclass
class ModelResponse:
    """Response from a model."""
    
    content: str
    model: ModelType
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    success: bool
    error_message: Optional[str] = None


class ModelRouter:
    """
    Intelligent model router.
    
    Routes tasks to optimal models based on:
    - Task complexity
    - Cost constraints
    - Model availability
    - Performance requirements
    """
    
    def __init__(self):
        """Initialize model router."""
        self.ollama = get_ollama_client()
        self.claude = get_claude_client()
        self.cursor = get_cursor_client()
        
        logger.info("Model router initialized")
    
    async def route_task(self, task: Task) -> ModelResponse:
        """
        Route task to optimal model.
        
        Args:
            task: Task to process
        
        Returns:
            Model response
        """
        # Select optimal model
        model = self._select_model(task)
        
        logger.info(
            f"Routing task (type={task.type}, complexity={task.complexity}) "
            f"to model={model}"
        )
        
        # Execute task
        start_time = datetime.utcnow()
        
        try:
            response = await self._execute_task(model, task)
            response.success = True
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            
            # Try fallback
            fallback_model = self._get_fallback(model)
            if fallback_model:
                logger.info(f"Trying fallback model: {fallback_model}")
                try:
                    response = await self._execute_task(fallback_model, task)
                    response.success = True
                except Exception as e2:
                    logger.error(f"Fallback also failed: {e2}")
                    response = ModelResponse(
                        content="",
                        model=model,
                        input_tokens=task.input_tokens,
                        output_tokens=0,
                        cost_usd=0.0,
                        latency_ms=0,
                        success=False,
                        error_message=str(e2)
                    )
            else:
                response = ModelResponse(
                    content="",
                    model=model,
                    input_tokens=task.input_tokens,
                    output_tokens=0,
                    cost_usd=0.0,
                    latency_ms=0,
                    success=False,
                    error_message=str(e)
                )
        
        # Calculate latency
        latency = (datetime.utcnow() - start_time).total_seconds() * 1000
        response.latency_ms = int(latency)
        
        return response
    
    def _select_model(self, task: Task) -> ModelType:
        """
        Select optimal model based on task characteristics.
        
        Decision tree:
        1. Metadata extraction → Ollama (local, fast, free)
        2. Simple summarization → Ollama (local, fast, free)
        3. Code analysis → Cursor or Claude Haiku
        4. Pattern recognition → Claude Sonnet
        5. Complex refactoring → Claude Opus
        """
        complexity = self._calculate_complexity(task)
        
        # Simple tasks → Local Ollama (if available)
        if complexity < 0.3:
            if self.ollama.is_available():
                return ModelType.OLLAMA_LLAMA3_8B
        
        # Medium tasks → Cursor (if available) or Claude Haiku
        if complexity < 0.5:
            if self.cursor.is_available():
                return ModelType.CURSOR_FREE_SMART
            elif self.claude.is_available():
                return ModelType.CLAUDE_HAIKU
            elif self.ollama.is_available():
                return ModelType.OLLAMA_MISTRAL_7B
        
        # High complexity → Claude Sonnet
        if complexity < 0.8:
            if self.claude.is_available():
                return ModelType.CLAUDE_SONNET
            elif self.ollama.is_available():
                return ModelType.OLLAMA_LLAMA3_8B
        
        # Highest complexity → Claude Opus
        if self.claude.is_available():
            return ModelType.CLAUDE_OPUS
        
        # Fallback to whatever is available
        if self.ollama.is_available():
            return ModelType.OLLAMA_LLAMA3_8B
        elif self.claude.is_available():
            return ModelType.CLAUDE_SONNET
        
        raise RuntimeError("No AI models available")
    
    def _calculate_complexity(self, task: Task) -> float:
        """
        Calculate task complexity score (0.0 to 1.0).
        
        Factors:
        - Task type
        - Input size
        - Reasoning requirement
        """
        score = 0.0
        
        # Base score by task type
        task_complexity = {
            TaskType.METADATA_EXTRACTION: 0.1,
            TaskType.SUMMARIZATION: 0.2,
            TaskType.CODE_ANALYSIS: 0.5,
            TaskType.PATTERN_RECOGNITION: 0.7,
            TaskType.REFACTORING_SUGGESTION: 0.9,
            TaskType.EMBEDDING_GENERATION: 0.1,
            TaskType.SEARCH_QUERY: 0.3,
            TaskType.COMPARISON: 0.6,
        }
        score += task_complexity.get(task.type, 0.5)
        
        # Adjust for input size
        if task.input_tokens > 8000:
            score += 0.3
        elif task.input_tokens > 4000:
            score += 0.2
        elif task.input_tokens > 2000:
            score += 0.1
        
        # Adjust for reasoning requirement
        if task.requires_reasoning:
            score += 0.2
        
        # Use explicit complexity if provided
        if task.complexity > 0:
            score = (score + task.complexity) / 2
        
        return min(score, 1.0)
    
    async def _execute_task(
        self,
        model: ModelType,
        task: Task
    ) -> ModelResponse:
        """Execute task with specific model."""
        
        # Ollama models
        if model in [ModelType.OLLAMA_LLAMA3_8B, ModelType.OLLAMA_MISTRAL_7B]:
            model_name = (
                "llama3.1:8b-instruct-q8_0"
                if model == ModelType.OLLAMA_LLAMA3_8B
                else "mistral:7b-instruct-q8_0"
            )
            
            result = await self.ollama.generate(
                prompt=task.prompt,
                model=model_name,
                system=task.system
            )
            
            return ModelResponse(
                content=result.get("response", ""),
                model=model,
                input_tokens=task.input_tokens,
                output_tokens=result.get("eval_count", 0),
                cost_usd=0.0,  # Local inference is free
                latency_ms=0,  # Will be set by caller
                success=True
            )
        
        # Claude models
        elif model in [ModelType.CLAUDE_HAIKU, ModelType.CLAUDE_SONNET, ModelType.CLAUDE_OPUS]:
            model_name = {
                ModelType.CLAUDE_HAIKU: "claude-3-haiku-20240307",
                ModelType.CLAUDE_SONNET: "claude-3-5-sonnet-20241022",
                ModelType.CLAUDE_OPUS: "claude-3-opus-20240229",
            }[model]
            
            result = await self.claude.generate(
                prompt=task.prompt,
                model=model_name,
                system=task.system
            )
            
            usage = result["usage"]
            cost = self.claude.calculate_cost(
                input_tokens=usage["input_tokens"],
                output_tokens=usage["output_tokens"],
                model=model_name
            )
            
            return ModelResponse(
                content=result["content"],
                model=model,
                input_tokens=usage["input_tokens"],
                output_tokens=usage["output_tokens"],
                cost_usd=cost,
                latency_ms=0,  # Will be set by caller
                success=True
            )
        
        # Cursor models
        elif model in [ModelType.CURSOR_FREE_FAST, ModelType.CURSOR_FREE_SMART]:
            result = await self.cursor.generate(
                prompt=task.prompt,
                model=str(model.value),
                system=task.system
            )
            
            return ModelResponse(
                content=result.get("content", ""),
                model=model,
                input_tokens=task.input_tokens,
                output_tokens=result.get("output_tokens", 0),
                cost_usd=0.0,  # Cursor free models
                latency_ms=0,
                success=True
            )
        
        else:
            raise ValueError(f"Unknown model type: {model}")
    
    def _get_fallback(self, model: ModelType) -> Optional[ModelType]:
        """Get fallback model if primary fails."""
        
        # Claude → Ollama
        if model in [ModelType.CLAUDE_OPUS, ModelType.CLAUDE_SONNET]:
            if self.ollama.is_available():
                return ModelType.OLLAMA_LLAMA3_8B
        
        # Ollama → Claude
        if model in [ModelType.OLLAMA_LLAMA3_8B, ModelType.OLLAMA_MISTRAL_7B]:
            if self.claude.is_available():
                return ModelType.CLAUDE_SONNET
        
        # Cursor → Claude or Ollama
        if model in [ModelType.CURSOR_FREE_FAST, ModelType.CURSOR_FREE_SMART]:
            if self.claude.is_available():
                return ModelType.CLAUDE_HAIKU
            elif self.ollama.is_available():
                return ModelType.OLLAMA_LLAMA3_8B
        
        return None


# Global instance
_model_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """Get global model router instance."""
    global _model_router
    if _model_router is None:
        _model_router = ModelRouter()
    return _model_router

