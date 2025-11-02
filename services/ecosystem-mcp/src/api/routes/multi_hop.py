"""
Multi-Hop RAG API Routes

Endpoints for complex questions requiring multi-hop reasoning.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...services.rag.multi_hop_rag import get_multi_hop_service

logger = logging.getLogger(__name__)

router = APIRouter()


class MultiHopRequest(BaseModel):
    """Multi-hop query request."""
    question: str = Field(..., description="Complex question requiring multi-hop reasoning", min_length=10, max_length=500)
    max_hops: int = Field(3, description="Maximum reasoning hops", ge=1, le=5)
    n_results_per_hop: int = Field(5, description="Documents per sub-question", ge=1, le=20)


class MultiHopResponse(BaseModel):
    """Multi-hop query response."""
    answer: str
    reasoning_chain: list
    sources: list
    confidence: float
    metadata: dict


@router.post(
    "/multi-hop",
    response_model=MultiHopResponse,
    summary="Answer complex question with multi-hop reasoning",
    description="Break down complex questions into sub-questions and synthesize comprehensive answers"
)
async def multi_hop_query(request: MultiHopRequest):
    """
    Answer complex question using multi-hop reasoning.
    
    **How it works:**
    1. Decompose complex question into 2-3 simpler sub-questions
    2. Answer each sub-question independently using RAG
    3. Synthesize final comprehensive answer
    
    **Best for:**
    - Cause-and-effect questions ("How did X affect Y?")
    - Relationship questions ("What is the connection between A and B?")
    - Evolution questions ("How did Z change over time?")
    - Complex multi-part questions
    
    **Example:**
    ```json
    {
        "question": "How did the authentication refactor affect API performance and what were the main trade-offs?",
        "max_hops": 3
    }
    ```
    
    **Response includes:**
    - Final synthesized answer
    - Reasoning chain (all sub-questions and sub-answers)
    - All unique sources used
    - Overall confidence score
    
    **Performance:**
    - Slower than single-pass RAG (3x sub-questions)
    - Higher accuracy for complex questions
    - Better context coverage
    """
    try:
        logger.info(f"🔗 Multi-hop query: {request.question[:60]}...")
        
        # Get multi-hop service
        service = get_multi_hop_service(max_hops=request.max_hops)
        
        # Execute multi-hop reasoning
        result = await service.answer_multi_hop(
            question=request.question,
            max_hops=request.max_hops,
            n_results_per_hop=request.n_results_per_hop
        )
        
        return MultiHopResponse(**result)
    
    except Exception as e:
        logger.error(f"Multi-hop query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/multi-hop/info",
    summary="Multi-hop endpoint information"
)
async def multi_hop_info():
    """Get information about the multi-hop RAG endpoint."""
    return {
        "endpoint": "/multi-hop",
        "method": "POST",
        "description": "Answer complex questions using multi-hop reasoning",
        "process": [
            "1. Decompose question into sub-questions",
            "2. Answer each sub-question with RAG",
            "3. Synthesize comprehensive final answer"
        ],
        "best_for": [
            "Cause-and-effect questions",
            "Relationship questions",
            "Evolution/history questions",
            "Complex multi-part questions"
        ],
        "performance": {
            "speed": "3x slower than single-pass (due to multiple sub-queries)",
            "accuracy": "Higher for complex questions",
            "coverage": "Better context from multiple sources"
        },
        "examples": [
            "How did the authentication refactor affect API performance?",
            "What is the relationship between caching and response times?",
            "Trace the evolution of the ingestion pipeline"
        ]
    }

