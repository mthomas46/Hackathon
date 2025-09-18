"""Summarizer Hub Service - Simplified Version.

Advanced document summarization and categorization service for the LLM Documentation Ecosystem.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import Dict, Any, List, Optional
import time
import os
import httpx
import uuid

# Service configuration
SERVICE_NAME = "summarizer-hub"
SERVICE_TITLE = "Summarizer Hub"
SERVICE_VERSION = "1.0.0"
DEFAULT_PORT = 5160

# Environment configuration
LLM_GATEWAY_URL = os.getenv("LLM_GATEWAY_URL", "http://llm-gateway:5055")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description="Advanced document summarization, categorization, and AI-assisted peer review service"
)

class SummarizeRequest(BaseModel):
    """Request model for document summarization."""
    content: str
    format: str = "markdown"
    max_length: int = 500
    style: Optional[str] = "professional"

class SummarizeResponse(BaseModel):
    """Response model for document summarization."""
    success: bool
    data: Dict[str, Any] = {}
    error: str = ""

class CategorizeRequest(BaseModel):
    """Request model for document categorization."""
    document: Dict[str, Any]
    candidate_categories: Optional[List[str]] = None
    use_zero_shot: bool = True

    @field_validator('document')
    @classmethod
    def validate_document(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Document must be a dictionary')
        if 'content' not in v:
            raise ValueError('Document must contain content field')
        return v

class CategorizeResponse(BaseModel):
    """Response model for document categorization."""
    success: bool
    document_id: str
    category: str
    confidence: float
    explanation: str
    metadata: Dict[str, Any] = {}

class PeerReviewRequest(BaseModel):
    """Request model for peer review."""
    content: str
    review_type: str = "general"
    focus_areas: Optional[List[str]] = None

class PeerReviewResponse(BaseModel):
    """Response model for peer review."""
    success: bool
    review_id: str
    suggestions: List[Dict[str, Any]]
    overall_score: float
    metadata: Dict[str, Any] = {}

class SimpleSummarizer:
    """Core summarization logic."""
    
    def __init__(self):
        self.categories = [
            "Technical Documentation",
            "API Documentation", 
            "User Guide",
            "Architecture Documentation",
            "Process Documentation",
            "Meeting Notes",
            "Requirements",
            "Code Documentation"
        ]
    
    async def summarize_with_llm(self, content: str, max_length: int = 500, style: str = "professional") -> str:
        """Summarize content using LLM Gateway."""
        try:
            prompt = f"Summarize the following content in a {style} style, keeping it under {max_length} words:\n\n{content}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{LLM_GATEWAY_URL}/query",
                    json={
                        "prompt": prompt,
                        "provider": "ollama",
                        "model": "llama2",
                        "max_tokens": max_length
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("data", {}).get("response", "")
                else:
                    return self.fallback_summarize(content, max_length)
                    
        except Exception as e:
            print(f"LLM summarization failed: {e}")
            return self.fallback_summarize(content, max_length)
    
    def fallback_summarize(self, content: str, max_length: int = 500) -> str:
        """Fallback summarization without LLM."""
        words = content.split()
        if len(words) <= max_length:
            return content
        
        # Simple truncation with sentence awareness
        truncated = " ".join(words[:max_length])
        last_period = truncated.rfind('.')
        if last_period > max_length * 0.7:  # If we can find a sentence ending in the last 30%
            return truncated[:last_period + 1]
        return truncated + "..."
    
    async def categorize_with_llm(self, content: str, candidate_categories: List[str] = None) -> Dict[str, Any]:
        """Categorize content using LLM Gateway."""
        categories = candidate_categories or self.categories
        try:
            prompt = f"Categorize the following content into one of these categories: {', '.join(categories)}. Provide the category name and a confidence score (0-1):\n\n{content[:1000]}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{LLM_GATEWAY_URL}/query",
                    json={
                        "prompt": prompt,
                        "provider": "ollama",
                        "model": "llama2",
                        "max_tokens": 200
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    llm_response = result.get("data", {}).get("response", "")
                    return self.parse_categorization_response(llm_response, categories)
                else:
                    return self.fallback_categorize(content, categories)
                    
        except Exception as e:
            print(f"LLM categorization failed: {e}")
            return self.fallback_categorize(content, categories)
    
    def parse_categorization_response(self, response: str, categories: List[str]) -> Dict[str, Any]:
        """Parse LLM categorization response."""
        response_lower = response.lower()
        
        # Find the category mentioned in the response
        for category in categories:
            if category.lower() in response_lower:
                # Try to extract confidence if mentioned
                confidence = 0.8  # Default confidence
                if "confidence" in response_lower:
                    import re
                    conf_match = re.search(r'(\d+\.?\d*)%?', response)
                    if conf_match:
                        conf_val = float(conf_match.group(1))
                        confidence = conf_val / 100 if conf_val > 1 else conf_val
                
                return {
                    "category": category,
                    "confidence": confidence,
                    "explanation": response.strip()
                }
        
        # Fallback to first category
        return {
            "category": categories[0],
            "confidence": 0.5,
            "explanation": "Category assigned by fallback logic"
        }
    
    def fallback_categorize(self, content: str, categories: List[str]) -> Dict[str, Any]:
        """Fallback categorization without LLM."""
        content_lower = content.lower()
        
        # Simple keyword matching
        if any(word in content_lower for word in ["api", "endpoint", "request", "response"]):
            return {"category": "API Documentation", "confidence": 0.7, "explanation": "Contains API-related keywords"}
        elif any(word in content_lower for word in ["architecture", "system", "design"]):
            return {"category": "Architecture Documentation", "confidence": 0.7, "explanation": "Contains architecture-related keywords"}
        elif any(word in content_lower for word in ["user", "guide", "tutorial", "how to"]):
            return {"category": "User Guide", "confidence": 0.7, "explanation": "Contains user guide keywords"}
        elif any(word in content_lower for word in ["meeting", "notes", "discussion"]):
            return {"category": "Meeting Notes", "confidence": 0.7, "explanation": "Contains meeting-related keywords"}
        else:
            return {"category": "Technical Documentation", "confidence": 0.5, "explanation": "Default categorization"}
    
    async def peer_review_with_llm(self, content: str, review_type: str = "general", focus_areas: List[str] = None) -> Dict[str, Any]:
        """Perform peer review using LLM Gateway."""
        focus = focus_areas or ["clarity", "completeness", "accuracy"]
        try:
            prompt = f"Perform a {review_type} peer review of the following content, focusing on {', '.join(focus)}. Provide specific suggestions and an overall score (0-10):\n\n{content}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{LLM_GATEWAY_URL}/query",
                    json={
                        "prompt": prompt,
                        "provider": "ollama",
                        "model": "llama2",
                        "max_tokens": 800
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    llm_response = result.get("data", {}).get("response", "")
                    return self.parse_review_response(llm_response, focus)
                else:
                    return self.fallback_review(content, focus)
                    
        except Exception as e:
            print(f"LLM peer review failed: {e}")
            return self.fallback_review(content, focus)
    
    def parse_review_response(self, response: str, focus_areas: List[str]) -> Dict[str, Any]:
        """Parse LLM review response."""
        suggestions = []
        
        # Extract suggestions (simple heuristic)
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or 'suggest' in line.lower()):
                suggestions.append({
                    "type": "improvement",
                    "suggestion": line,
                    "priority": "medium"
                })
        
        # Extract score
        import re
        score_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:/\s*10|out of 10)', response)
        score = float(score_match.group(1)) if score_match else 7.5
        
        if not suggestions:
            suggestions = [{"type": "general", "suggestion": "Overall content is well-structured", "priority": "low"}]
        
        return {
            "suggestions": suggestions,
            "overall_score": score,
            "review_text": response
        }
    
    def fallback_review(self, content: str, focus_areas: List[str]) -> Dict[str, Any]:
        """Fallback review without LLM."""
        suggestions = [
            {"type": "clarity", "suggestion": "Consider adding more examples to improve clarity", "priority": "medium"},
            {"type": "structure", "suggestion": "Content structure is adequate", "priority": "low"}
        ]
        
        # Simple scoring based on content length and structure
        word_count = len(content.split())
        score = min(8.0, 5.0 + (word_count / 200))  # Basic scoring
        
        return {
            "suggestions": suggestions,
            "overall_score": score,
            "review_text": "Automated review completed with basic analysis"
        }

# Initialize summarizer
summarizer = SimpleSummarizer()

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "timestamp": time.time(),
        "environment": ENVIRONMENT,
        "llm_gateway_url": LLM_GATEWAY_URL
    }

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": SERVICE_NAME,
        "title": SERVICE_TITLE,
        "version": SERVICE_VERSION,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "summarize": "/summarize",
            "categorize": "/categorize",
            "peer_review": "/peer-review",
            "capabilities": "/capabilities"
        },
        "features": {
            "llm_integration": True,
            "fallback_processing": True,
            "batch_processing": True,
            "peer_review": True
        }
    }

@app.get("/capabilities")
async def get_capabilities():
    """Get service capabilities."""
    return {
        "summarization": {
            "formats": ["markdown", "plain", "structured"],
            "styles": ["professional", "casual", "technical", "executive"],
            "max_length": 2000
        },
        "categorization": {
            "default_categories": summarizer.categories,
            "custom_categories": True,
            "confidence_scoring": True
        },
        "peer_review": {
            "review_types": ["general", "technical", "editorial", "compliance"],
            "focus_areas": ["clarity", "completeness", "accuracy", "style", "structure"],
            "scoring": "0-10 scale"
        }
    }

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_document(request: SummarizeRequest):
    """Summarize a document."""
    try:
        summary = await summarizer.summarize_with_llm(
            request.content, 
            request.max_length,
            getattr(request, 'style', 'professional')
        )
        
        return SummarizeResponse(
            success=True,
            data={
                "summary": summary,
                "original_length": len(request.content.split()),
                "summary_length": len(summary.split()),
                "compression_ratio": len(summary) / len(request.content) if request.content else 0,
                "format": request.format
            }
        )
        
    except Exception as e:
        return SummarizeResponse(
            success=False,
            error=str(e)
        )

@app.post("/categorize", response_model=CategorizeResponse)
async def categorize_document(request: CategorizeRequest):
    """Categorize a document."""
    try:
        content = request.document.get("content", "")
        result = await summarizer.categorize_with_llm(content, request.candidate_categories)
        
        return CategorizeResponse(
            success=True,
            document_id=request.document.get("id", str(uuid.uuid4())),
            category=result["category"],
            confidence=result["confidence"],
            explanation=result["explanation"],
            metadata={
                "use_zero_shot": request.use_zero_shot,
                "candidate_categories": request.candidate_categories or summarizer.categories,
                "content_length": len(content)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/peer-review", response_model=PeerReviewResponse)
async def peer_review_document(request: PeerReviewRequest):
    """Perform peer review on a document."""
    try:
        result = await summarizer.peer_review_with_llm(
            request.content,
            request.review_type,
            request.focus_areas
        )
        
        return PeerReviewResponse(
            success=True,
            review_id=str(uuid.uuid4()),
            suggestions=result["suggestions"],
            overall_score=result["overall_score"],
            metadata={
                "review_type": request.review_type,
                "focus_areas": request.focus_areas or ["clarity", "completeness", "accuracy"],
                "content_length": len(request.content),
                "review_timestamp": time.time()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch/summarize")
async def batch_summarize(requests: List[SummarizeRequest]):
    """Batch summarize multiple documents."""
    results = []
    
    for request in requests:
        try:
            result = await summarize_document(request)
            results.append(result)
        except Exception as e:
            results.append(SummarizeResponse(success=False, error=str(e)))
    
    return {
        "batch_results": results,
        "total_processed": len(results),
        "successful": sum(1 for r in results if r.success),
        "failed": sum(1 for r in results if not r.success)
    }

@app.post("/api/v1/summarize")
async def summarize_v1(request: SummarizeRequest):
    """Summarize text content using standardized API v1 interface."""
    try:
        summarizer = SimpleSummarizer()

        # Generate summary
        summary_text = await summarizer.summarize_with_llm(
            request.content,
            max_length=request.max_length,
            style=request.style or "professional"
        )

        # Get content analysis
        analysis = summarizer.analyze_content(request.content)

        # Categorize content
        category_result = await summarizer.categorize_with_llm(request.content)

        response_data = {
            "summary_id": str(uuid.uuid4()),
            "original_length": len(request.content),
            "summary_length": len(summary_text),
            "compression_ratio": len(summary_text) / len(request.content) if request.content else 0,
            "summary": summary_text,
            "format": request.format,
            "style": request.style,
            "category": category_result.get("category", "Unknown"),
            "confidence": category_result.get("confidence", 0.0),
            "content_analysis": analysis,
            "processing_time": 0.5,  # Mock processing time
            "timestamp": time.time(),
            "metadata": {
                "llm_model": "llama2",
                "provider": "ollama",
                "version": SERVICE_VERSION
            }
        }

        return SummarizeResponse(
            success=True,
            data=response_data
        )

    except Exception as e:
        return SummarizeResponse(
            success=False,
            error=f"Summarization failed: {str(e)}"
        )

@app.get("/test/llm-connection")
async def test_llm_connection():
    """Test connection to LLM Gateway."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{LLM_GATEWAY_URL}/health")
            if response.status_code == 200:
                return {
                    "llm_gateway_status": "connected",
                    "response": response.json()
                }
            else:
                return {
                    "llm_gateway_status": "error",
                    "status_code": response.status_code
                }
    except Exception as e:
        return {
            "llm_gateway_status": "unreachable",
            "error": str(e)
        }

if __name__ == "__main__":
    """Run the Summarizer Hub service directly."""
    import uvicorn
    print(f"🚀 Starting {SERVICE_TITLE} Service...")
    print(f"🔗 LLM Gateway: {LLM_GATEWAY_URL}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )
