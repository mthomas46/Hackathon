"""Base pattern engine for all LLM patterns."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from pydantic import BaseModel


logger = logging.getLogger(__name__)


class PatternStep(BaseModel):
    """Single step in pattern execution."""
    step_id: str
    step_type: str
    description: str
    prompt: str
    response: Optional[str] = None
    metadata: Dict[str, Any] = {}
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None


class PatternResult(BaseModel):
    """Result from pattern execution."""
    pattern_type: str
    success: bool
    steps: List[PatternStep]
    final_answer: Optional[str] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = {}
    total_duration_ms: int = 0
    error: Optional[str] = None


class BasePatternEngine(ABC):
    """Base class for all pattern engines."""
    
    def __init__(self, pattern_type: str):
        """Initialize pattern engine."""
        self.pattern_type = pattern_type
        self.logger = logging.getLogger(f"{__name__}.{pattern_type}")
    
    @abstractmethod
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """
        Execute the pattern.
        
        Args:
            query: User query to process
            context: Context information (MCP data, etc.)
            config: Pattern-specific configuration
        
        Returns:
            PatternResult with execution details
        """
        pass
    
    async def call_llm(
        self,
        prompt: str,
        config: Dict[str, Any]
    ) -> str:
        """
        Call LLM via llm-gateway.
        
        Args:
            prompt: Prompt to send to LLM
            config: LLM configuration
        
        Returns:
            LLM response text
        """
        import httpx
        
        try:
            llm_gateway_url = config.get("llm_gateway_url", "http://llm-gateway:5055")
            model = config.get("model", "llama3.2")
            temperature = config.get("temperature", 0.7)
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{llm_gateway_url}/api/v1/chat",
                    json={
                        "model": model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": temperature,
                        "stream": False
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"LLM Gateway error: {response.status_code}")
                
                data = response.json()
                return data.get("message", {}).get("content", "")
        
        except Exception as e:
            self.logger.error(f"Error calling LLM: {e}")
            raise
    
    def create_step(
        self,
        step_id: str,
        step_type: str,
        description: str,
        prompt: str
    ) -> PatternStep:
        """Create a new pattern step."""
        return PatternStep(
            step_id=step_id,
            step_type=step_type,
            description=description,
            prompt=prompt,
            started_at=datetime.utcnow().isoformat()
        )
    
    def complete_step(
        self,
        step: PatternStep,
        response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PatternStep:
        """Mark step as complete."""
        step.response = response
        step.completed_at = datetime.utcnow().isoformat()
        
        if step.started_at and step.completed_at:
            start = datetime.fromisoformat(step.started_at)
            end = datetime.fromisoformat(step.completed_at)
            step.duration_ms = int((end - start).total_seconds() * 1000)
        
        if metadata:
            step.metadata.update(metadata)
        
        return step
    
    def calculate_confidence(
        self,
        steps: List[PatternStep],
        config: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score based on execution.
        
        Default implementation - can be overridden.
        """
        # Simple heuristic: all steps completed = high confidence
        if not steps:
            return 0.0
        
        completed = sum(1 for s in steps if s.response is not None)
        base_confidence = completed / len(steps)
        
        # Adjust based on response quality indicators
        avg_response_length = sum(len(s.response or "") for s in steps) / len(steps)
        length_factor = min(avg_response_length / 100, 1.0)  # Normalize to 0-1
        
        return min(base_confidence * 0.7 + length_factor * 0.3, 1.0)

