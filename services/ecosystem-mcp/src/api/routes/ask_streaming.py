"""
Streaming RAG API Routes

Provides streaming responses for better UX with long-running LLM generations.

Features:
- Token-by-token streaming
- Server-Sent Events (SSE) format
- Sources included in final chunk
- Progress updates
"""

import logging
import json
from typing import AsyncGenerator, Optional, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ...services.rag import get_rag_service
from ...services.ollama import get_ollama_service

logger = logging.getLogger(__name__)

router = APIRouter()


class StreamingAskRequest(BaseModel):
    """Streaming ask request."""
    question: str = Field(..., description="Question to ask", min_length=3, max_length=500)
    n_results: int = Field(10, description="Number of documents to retrieve", ge=1, le=50)
    use_enhancements: bool = Field(True, description="Use enhancement pipeline")
    temperature: float = Field(0.7, description="LLM temperature", ge=0.0, le=1.0)


@router.post(
    "/ask/stream",
    summary="Ask a question with streaming response",
    description="Stream RAG answer token-by-token using Server-Sent Events"
)
async def ask_question_streaming(request: StreamingAskRequest):
    """
    Answer a question using RAG with streaming response.
    
    This endpoint:
    1. Retrieves relevant documents (same as /ask)
    2. Streams the LLM answer token-by-token
    3. Returns sources and metadata in final chunk
    
    **Response Format: Server-Sent Events (SSE)**
    
    ```
    data: {"type": "progress", "message": "Retrieving documents..."}
    
    data: {"type": "progress", "message": "Found 8 sources"}
    
    data: {"type": "token", "content": "Ecosystem"}
    data: {"type": "token", "content": "-MCP"}
    data: {"type": "token", "content": " is"}
    
    data: {"type": "done", "sources": [...], "metadata": {...}}
    ```
    
    **Client Example (JavaScript):**
    ```javascript
    const eventSource = new EventSource('/api/v1/ask/stream', {
        method: 'POST',
        body: JSON.stringify({question: "What is MCP?"})
    });
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "token") {
            console.log(data.content);  // Stream tokens
        } else if (data.type === "done") {
            console.log("Sources:", data.sources);
            eventSource.close();
        }
    };
    ```
    
    **Benefits:**
    - Perceived latency: ~1-2s (vs 10-15s for full response)
    - Better UX for long answers
    - Real-time progress feedback
    """
    try:
        logger.info(f"🌊 Streaming RAG query: {request.question[:60]}...")
        
        async def generate_stream() -> AsyncGenerator[str, None]:
            try:
                # Step 1: Send progress - retrieving documents
                yield _sse_message({
                    "type": "progress",
                    "message": "Retrieving relevant documents..."
                })
                
                # Get RAG service
                rag_service = get_rag_service()
                
                # Retrieve documents (non-streaming part)
                if request.use_enhancements:
                    # Use enhancement pipeline for retrieval
                    from ...services.rag.enhancements import EnhancementPipeline, EnhancementConfig
                    
                    pipeline = EnhancementPipeline(
                        chroma_collection=rag_service.chroma_collection,
                        ollama_service=rag_service.ollama,
                        document_store=rag_service.document_store
                    )
                    
                    config = EnhancementConfig.default()
                    result = await pipeline.execute(
                        query=request.question,
                        n_results=request.n_results,
                        config=config
                    )
                    documents = result.get("documents", [])
                else:
                    # Standard retrieval
                    search_result = rag_service.chroma_collection.query(
                        query_texts=[request.question],
                        n_results=request.n_results
                    )
                    documents = rag_service._format_search_results(search_result)
                
                # Step 2: Send progress - found sources
                yield _sse_message({
                    "type": "progress",
                    "message": f"Found {len(documents)} relevant sources"
                })
                
                # Step 3: Build prompt
                context = rag_service._build_context(documents)
                prompt = f"""Based on the following context, answer the question concisely and accurately.

Context:
{context}

Question: {request.question}

Answer:"""
                
                # Step 4: Stream LLM generation
                ollama = get_ollama_service()
                answer_tokens = []
                
                async for token in ollama.generate_streaming(
                    prompt=prompt,
                    temperature=request.temperature
                ):
                    answer_tokens.append(token)
                    yield _sse_message({
                        "type": "token",
                        "content": token
                    })
                
                # Step 5: Send final chunk with metadata
                answer = "".join(answer_tokens)
                sources = rag_service._format_sources(documents)
                confidence = rag_service._calculate_confidence(answer, documents, request.question)
                
                yield _sse_message({
                    "type": "done",
                    "answer": answer,
                    "sources": sources,
                    "confidence": confidence,
                    "metadata": {
                        "n_sources": len(sources),
                        "n_tokens": len(answer_tokens),
                        "enhanced": request.use_enhancements
                    }
                })
                
                logger.info(f"✅ Streamed {len(answer_tokens)} tokens, {len(sources)} sources")
                
            except Exception as e:
                logger.error(f"Streaming generation failed: {e}", exc_info=True)
                yield _sse_message({
                    "type": "error",
                    "message": str(e)
                })
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
    
    except Exception as e:
        logger.error(f"Streaming ask failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _sse_message(data: dict) -> str:
    """Format data as Server-Sent Event message."""
    return f"data: {json.dumps(data)}\n\n"


@router.get(
    "/ask/stream/info",
    summary="Streaming endpoint information"
)
async def streaming_info():
    """Get information about the streaming RAG endpoint."""
    return {
        "endpoint": "/ask/stream",
        "method": "POST",
        "format": "Server-Sent Events (SSE)",
        "features": [
            "Token-by-token streaming",
            "Progress updates",
            "Sources in final chunk",
            "Enhancement pipeline support"
        ],
        "benefits": {
            "perceived_latency": "1-2s (vs 10-15s full response)",
            "ux": "Better for long answers",
            "feedback": "Real-time progress"
        },
        "client_example": {
            "javascript": "const es = new EventSource('/api/v1/ask/stream'); es.onmessage = ...",
            "python": "import requests; response = requests.post(..., stream=True); for line in response.iter_lines(): ..."
        }
    }

