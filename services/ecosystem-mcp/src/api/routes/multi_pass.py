"""
Multi-Pass Query API Endpoints.

Provides complex query decomposition and synthesis with progress tracking.
"""

import logging
import asyncio
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json

from ...services.rag.multi_pass_query import get_multi_pass_service

logger = logging.getLogger(__name__)

router = APIRouter()


class MultiPassRequest(BaseModel):
    """Request for multi-pass query processing."""
    query: str = Field(
        ...,
        description="Main query to analyze",
        min_length=10,
        max_length=2000
    )
    num_passes: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of major concepts/sections to decompose into"
    )
    num_secondary_questions: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of secondary questions per section"
    )
    n_results: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Documents to retrieve per question"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="LLM temperature"
    )
    stream: bool = Field(
        default=False,
        description="Stream progress updates (SSE)"
    )


class ProgressUpdate(BaseModel):
    """Progress update for streaming."""
    status: str
    progress: int  # 0-100
    message: str
    timestamp: str


class SectionSummary(BaseModel):
    """Summary of a processed section."""
    section_index: int
    section_name: str
    section_description: str
    questions_count: int
    synthesis_length: int
    duration_seconds: float


class MultiPassResponse(BaseModel):
    """Response from multi-pass query processing."""
    original_query: str
    num_passes: int
    num_secondary_questions: int
    sections: list  # Full section results
    section_summaries: list  # Quick overview
    final_synthesis: str
    total_duration_seconds: float
    total_questions_asked: int
    total_sources_used: int
    timestamp: str
    metadata: dict


@router.post(
    "/query/multi-pass",
    response_model=MultiPassResponse,
    summary="Multi-pass complex query processing",
    description="Decompose complex queries into sections with secondary questions for comprehensive analysis"
)
async def multi_pass_query(request: MultiPassRequest):
    """
    Process a complex query using multi-pass decomposition.
    
    **Workflow:**
    1. Decompose query into N major concepts/sections
    2. Generate M secondary questions per section
    3. Execute RAG for each question (N×M total questions)
    4. Synthesize section-level answers
    5. Create final comprehensive synthesis
    
    **Use Cases:**
    - Complex technical questions requiring deep analysis
    - Research queries needing multiple perspectives
    - Documentation generation
    - Comprehensive system understanding
    
    **Example:**
    ```json
    {
        "query": "How does the caching system work and what are the best practices?",
        "num_passes": 3,
        "num_secondary_questions": 4,
        "n_results": 10
    }
    ```
    
    This would:
    - Decompose into 3 sections (e.g., Core Concepts, Implementation, Best Practices)
    - Generate 4 questions per section (12 total)
    - Execute 12 RAG queries
    - Synthesize 3 section answers
    - Create 1 final comprehensive answer
    """
    if request.stream:
        # Return streaming response
        return StreamingResponse(
            _stream_multi_pass(request),
            media_type="text/event-stream"
        )
    
    # Standard response
    try:
        multi_pass_service = get_multi_pass_service()
        
        result = await multi_pass_service.process_query(
            query=request.query,
            num_passes=request.num_passes,
            num_secondary_questions=request.num_secondary_questions,
            n_results=request.n_results,
            temperature=request.temperature
        )
        
        # Create section summaries
        section_summaries = [
            SectionSummary(
                section_index=section.section_index,
                section_name=section.section_name,
                section_description=section.section_description,
                questions_count=len(section.questions),
                synthesis_length=len(section.synthesis),
                duration_seconds=section.duration_seconds
            )
            for section in result.sections
        ]
        
        # Convert sections to dicts
        sections_dict = []
        for section in result.sections:
            section_dict = {
                "section_index": section.section_index,
                "section_name": section.section_name,
                "section_description": section.section_description,
                "synthesis": section.synthesis,
                "duration_seconds": section.duration_seconds,
                "timestamp": section.timestamp,
                "questions": [
                    {
                        "question": q.question,
                        "answer": q.answer,
                        "sources": q.sources,
                        "confidence": q.confidence,
                        "duration_seconds": q.duration_seconds,
                        "timestamp": q.timestamp,
                        "metadata": q.metadata
                    }
                    for q in section.questions
                ]
            }
            sections_dict.append(section_dict)
        
        return MultiPassResponse(
            original_query=result.original_query,
            num_passes=result.num_passes,
            num_secondary_questions=result.num_secondary_questions,
            sections=sections_dict,
            section_summaries=[s.dict() for s in section_summaries],
            final_synthesis=result.final_synthesis,
            total_duration_seconds=result.total_duration_seconds,
            total_questions_asked=result.total_questions_asked,
            total_sources_used=result.total_sources_used,
            timestamp=result.timestamp,
            metadata=result.metadata
        )
    
    except Exception as e:
        logger.error(f"Multi-pass query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Multi-pass query processing failed: {str(e)}"
        )


async def _stream_multi_pass(request: MultiPassRequest):
    """Stream multi-pass query processing with progress updates."""
    
    async def progress_callback(status: str, progress: int, message: str):
        """Callback to send progress updates."""
        update = ProgressUpdate(
            status=status,
            progress=progress,
            message=message,
            timestamp=datetime.now().isoformat()
        )
        
        # Send Server-Sent Event
        yield f"data: {update.json()}\n\n"
    
    try:
        multi_pass_service = get_multi_pass_service()
        
        # Start progress stream
        async for progress_event in _generate_progress_events(
            multi_pass_service,
            request
        ):
            yield progress_event
    
    except Exception as e:
        logger.error(f"Streaming multi-pass query failed: {e}", exc_info=True)
        error_update = ProgressUpdate(
            status="error",
            progress=0,
            message=f"Error: {str(e)}",
            timestamp=datetime.now().isoformat()
        )
        yield f"data: {error_update.json()}\n\n"


async def _generate_progress_events(service, request):
    """Generate progress events during multi-pass processing."""
    
    progress_queue = asyncio.Queue()
    
    async def callback(status: str, progress: int, message: str):
        """Queue progress updates."""
        await progress_queue.put((status, progress, message))
    
    # Start processing in background
    async def process():
        try:
            result = await service.process_query(
                query=request.query,
                num_passes=request.num_passes,
                num_secondary_questions=request.num_secondary_questions,
                n_results=request.n_results,
                temperature=request.temperature,
                progress_callback=callback
            )
            
            # Signal completion
            await progress_queue.put(("done", result))
        
        except Exception as e:
            await progress_queue.put(("error", str(e)))
    
    # Start background task
    task = asyncio.create_task(process())
    
    # Stream progress updates
    while True:
        item = await progress_queue.get()
        
        if isinstance(item, tuple) and len(item) == 2:
            status, data = item
            
            if status == "done":
                # Send final result
                result = data
                
                # Create section summaries
                section_summaries = [
                    {
                        "section_index": section.section_index,
                        "section_name": section.section_name,
                        "section_description": section.section_description,
                        "questions_count": len(section.questions),
                        "synthesis_length": len(section.synthesis),
                        "duration_seconds": section.duration_seconds
                    }
                    for section in result.sections
                ]
                
                # Convert to dict
                sections_dict = []
                for section in result.sections:
                    section_dict = {
                        "section_index": section.section_index,
                        "section_name": section.section_name,
                        "section_description": section.section_description,
                        "synthesis": section.synthesis,
                        "duration_seconds": section.duration_seconds,
                        "timestamp": section.timestamp,
                        "questions": [
                            {
                                "question": q.question,
                                "answer": q.answer,
                                "sources": q.sources,
                                "confidence": q.confidence,
                                "duration_seconds": q.duration_seconds,
                                "timestamp": q.timestamp,
                                "metadata": q.metadata
                            }
                            for q in section.questions
                        ]
                    }
                    sections_dict.append(section_dict)
                
                final_data = {
                    "status": "complete",
                    "result": {
                        "original_query": result.original_query,
                        "num_passes": result.num_passes,
                        "num_secondary_questions": result.num_secondary_questions,
                        "sections": sections_dict,
                        "section_summaries": section_summaries,
                        "final_synthesis": result.final_synthesis,
                        "total_duration_seconds": result.total_duration_seconds,
                        "total_questions_asked": result.total_questions_asked,
                        "total_sources_used": result.total_sources_used,
                        "timestamp": result.timestamp,
                        "metadata": result.metadata
                    }
                }
                
                yield f"data: {json.dumps(final_data)}\n\n"
                break
            
            elif status == "error":
                error_data = {
                    "status": "error",
                    "message": data,
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                break
        
        elif isinstance(item, tuple) and len(item) == 3:
            # Progress update
            status, progress, message = item
            update = {
                "status": status,
                "progress": progress,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(update)}\n\n"
    
    # Wait for task completion
    await task


@router.get(
    "/query/multi-pass/info",
    summary="Get multi-pass query information",
    description="Get information about multi-pass query processing"
)
async def multi_pass_info():
    """Get information about multi-pass query processing."""
    return {
        "description": "Multi-pass query processing for complex analysis",
        "workflow": {
            "step_1": "Decompose query into N major concepts/sections",
            "step_2": "Generate M secondary questions per section",
            "step_3": "Execute RAG for each question (N×M total)",
            "step_4": "Synthesize section-level answers",
            "step_5": "Create final comprehensive synthesis"
        },
        "parameters": {
            "query": {
                "type": "string",
                "min_length": 10,
                "max_length": 2000,
                "description": "Main query to analyze"
            },
            "num_passes": {
                "type": "integer",
                "min": 1,
                "max": 10,
                "default": 3,
                "description": "Number of major concepts/sections"
            },
            "num_secondary_questions": {
                "type": "integer",
                "min": 1,
                "max": 10,
                "default": 3,
                "description": "Number of questions per section"
            },
            "n_results": {
                "type": "integer",
                "min": 1,
                "max": 50,
                "default": 10,
                "description": "Documents to retrieve per question"
            },
            "temperature": {
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.7,
                "description": "LLM temperature"
            },
            "stream": {
                "type": "boolean",
                "default": False,
                "description": "Stream progress updates (SSE)"
            }
        },
        "example_usage": {
            "query": "How does the caching system work and what are best practices?",
            "num_passes": 3,
            "num_secondary_questions": 4,
            "explanation": "This creates 3 sections with 4 questions each (12 total queries)"
        },
        "performance": {
            "time_estimate": "~5-30 seconds depending on configuration",
            "formula": "Time ≈ (num_passes × num_secondary_questions × 2-3s) + synthesis time"
        }
    }

