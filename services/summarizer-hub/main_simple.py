"""
Simplified Summarizer Hub Service - Working Version
This version focuses on core functionality without complex NLP dependencies
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time
import uuid
import os
import httpx
import uvicorn

# Shared modules (these work with absolute imports)
from services.shared.monitoring.health import register_health_endpoints
from services.shared.core.responses import create_success_response, create_error_response

# Create FastAPI app
app = FastAPI(
    title="Summarizer Hub",
    description="Simplified document summarization service",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register health endpoints
register_health_endpoints(app, "summarizer-hub")

# Request/Response Models
class SummarizeRequest(BaseModel):
    content: str
    max_length: Optional[int] = 150
    summary_type: Optional[str] = "extractive"

class SummarizeResponse(BaseModel):
    success: bool
    summary: str
    summary_id: str
    word_count: int
    original_length: int
    metadata: Dict[str, Any] = {}

class CategorizeRequest(BaseModel):
    content: str
    categories: Optional[List[str]] = None

class CategorizeResponse(BaseModel):
    success: bool
    category: str
    confidence: float
    explanation: str
    metadata: Dict[str, Any] = {}

# Simple Summarizer Class
class SimplifiedSummarizer:
    """Simplified summarizer without complex NLP dependencies."""
    
    def __init__(self):
        self.llm_gateway_url = os.environ.get('LLM_GATEWAY_URL', 'http://llm-gateway:5055')
        
    async def summarize_with_llm(self, content: str, max_length: int = 150, summary_type: str = "extractive") -> Dict[str, Any]:
        """Summarize content using LLM Gateway."""
        try:
            prompt = f"Summarize the following content in approximately {max_length} words using {summary_type} summarization:\n\n{content}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.llm_gateway_url}/query",
                    json={
                        "prompt": prompt,
                        "max_tokens": max_length * 2,  # Rough estimate
                        "model": "tinyllama:latest",
                        "provider": "ollama"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        summary_text = result["data"]["response"].strip()
                        return {
                            "summary": summary_text,
                            "word_count": len(summary_text.split()),
                            "method": "llm_based",
                            "model_used": "tinyllama"
                        }
                
                # If LLM fails, use fallback
                return self.fallback_summarize(content, max_length)
                    
        except Exception as e:
            print(f"LLM summarization failed: {e}")
            return self.fallback_summarize(content, max_length)
    
    def fallback_summarize(self, content: str, max_length: int = 150) -> Dict[str, Any]:
        """Simple extractive summarization fallback."""
        sentences = content.split('. ')
        
        # Simple scoring: prefer longer sentences and those with common keywords
        scored_sentences = []
        for i, sentence in enumerate(sentences[:10]):  # Limit to first 10 sentences
            score = len(sentence) * 0.1  # Length factor
            score += sentence.lower().count('important') * 2
            score += sentence.lower().count('key') * 2
            score += sentence.lower().count('main') * 2
            scored_sentences.append((score, i, sentence))
        
        # Sort by score and take top sentences
        scored_sentences.sort(reverse=True)
        summary_sentences = []
        word_count = 0
        
        for score, idx, sentence in scored_sentences:
            sentence_words = len(sentence.split())
            if word_count + sentence_words <= max_length:
                summary_sentences.append((idx, sentence))
                word_count += sentence_words
            if word_count >= max_length * 0.8:  # Stop at 80% of max
                break
        
        # Sort by original order and join
        summary_sentences.sort(key=lambda x: x[0])
        summary = '. '.join([s[1] for s in summary_sentences])
        
        return {
            "summary": summary,
            "word_count": word_count,
            "method": "extractive_fallback",
            "model_used": "rule_based"
        }
    
    async def categorize_content(self, content: str, categories: List[str] = None) -> Dict[str, Any]:
        """Simple content categorization."""
        default_categories = ["Technical Documentation", "API Reference", "Tutorial", "Guide", "Other"]
        categories = categories or default_categories
        
        content_lower = content.lower()
        
        # Simple keyword-based categorization
        if any(word in content_lower for word in ['api', 'endpoint', 'request', 'response']):
            return {"category": "API Reference", "confidence": 0.8, "explanation": "Contains API-related keywords"}
        elif any(word in content_lower for word in ['tutorial', 'step', 'how to', 'guide']):
            return {"category": "Tutorial", "confidence": 0.8, "explanation": "Contains tutorial-style language"}
        elif any(word in content_lower for word in ['class', 'function', 'method', 'variable']):
            return {"category": "Technical Documentation", "confidence": 0.7, "explanation": "Contains code-related terms"}
        else:
            return {"category": "Other", "confidence": 0.5, "explanation": "No specific category indicators found"}

# Initialize summarizer
summarizer = SimplifiedSummarizer()

# API Endpoints
@app.get("/")
async def root():
    return create_success_response(
        data={"message": "Simplified Summarizer Hub is running"},
        message="Service operational"
    )

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_content(request: SummarizeRequest):
    """Summarize the provided content."""
    try:
        result = await summarizer.summarize_with_llm(
            request.content,
            request.max_length,
            request.summary_type
        )
        
        return SummarizeResponse(
            success=True,
            summary=result["summary"],
            summary_id=str(uuid.uuid4()),
            word_count=result["word_count"],
            original_length=len(request.content.split()),
            metadata={
                "method": result["method"],
                "model_used": result["model_used"],
                "timestamp": time.time()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/categorize", response_model=CategorizeResponse)
async def categorize_content(request: CategorizeRequest):
    """Categorize the provided content."""
    try:
        result = await summarizer.categorize_content(request.content, request.categories)
        
        return CategorizeResponse(
            success=True,
            category=result["category"],
            confidence=result["confidence"],
            explanation=result["explanation"],
            metadata={
                "timestamp": time.time(),
                "available_categories": request.categories or ["Technical Documentation", "API Reference", "Tutorial", "Guide", "Other"]
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/capabilities")
async def get_capabilities():
    """Get service capabilities."""
    return {
        "service": "summarizer-hub",
        "version": "1.0.0",
        "capabilities": {
            "summarization": {
                "types": ["extractive", "abstractive"],
                "max_length": 500,
                "llm_integration": True
            },
            "categorization": {
                "default_categories": ["Technical Documentation", "API Reference", "Tutorial", "Guide", "Other"],
                "custom_categories": True,
                "confidence_scoring": True
            }
        },
        "endpoints": {
            "health": "/health",
            "summarize": "/summarize",
            "categorize": "/categorize",
            "capabilities": "/capabilities"
        },
        "features": {
            "llm_integration": True,
            "fallback_processing": True,
            "simple_mode": True
        }
    }

if __name__ == "__main__":
    port = int(os.environ.get('SERVICE_PORT', 5160))
    print(f"Starting simplified Summarizer Hub on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
