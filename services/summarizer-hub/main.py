"""Summarizer Hub Service

Advanced document summarization and categorization service with ML-based classification
capabilities for the LLM Documentation Ecosystem.
"""

from fastapi import FastAPI
from pydantic import BaseModel, field_validator
from typing import Dict, Any, List, Optional
import time

# Import modules
try:
    from modules.categorizer import categorize_document, categorize_documents_batch
    from modules.peer_review_enhancer import review_documentation, compare_document_versions
    from modules.models import PeerReviewRequest, PeerReviewResponse, DocumentComparisonRequest, DocumentComparisonResponse
except ImportError:
    # Fallback for when running as script
    from services.summarizer_hub.modules.categorizer import categorize_document, categorize_documents_batch
    from services.summarizer_hub.modules.peer_review_enhancer import review_documentation, compare_document_versions
    from services.summarizer_hub.modules.models import PeerReviewRequest, PeerReviewResponse, DocumentComparisonRequest, DocumentComparisonResponse

app = FastAPI(
    title="Summarizer Hub Service",
    version="1.0.0",
    description="Advanced document summarization, categorization, and AI-assisted peer review service"
)

class SummarizeRequest(BaseModel):
    """Request model for document summarization."""
    content: str
    format: str = "markdown"
    max_length: int = 500

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
        if not v:
            raise ValueError('Document cannot be empty')
        if 'id' not in v:
            raise ValueError('Document must have an id field')
        return v


class BatchCategorizeRequest(BaseModel):
    """Request model for batch document categorization."""
    documents: List[Dict[str, Any]]
    candidate_categories: Optional[List[str]] = None
    use_zero_shot: bool = True

    @field_validator('documents')
    @classmethod
    def validate_documents(cls, v):
        if not v:
            raise ValueError('Documents list cannot be empty')
        if len(v) > 100:
            raise ValueError('Too many documents (max 100)')
        for doc in v:
            if 'id' not in v:
                raise ValueError('Each document must have an id field')
        return v


class CategorizationResponse(BaseModel):
    """Response model for document categorization."""
    document_id: str
    category: str
    confidence: float
    tags: List[str]
    method: str
    all_scores: Optional[Dict[str, float]] = None


class BatchCategorizationResponse(BaseModel):
    """Response model for batch document categorization."""
    total_documents: int
    successful_categorizations: int
    results: List[Dict[str, Any]]
    summary: Dict[str, Any]
    processing_time: float

@app.post("/summarize")
async def summarize_document(request: SummarizeRequest) -> Dict[str, Any]:
    """Summarize document content and extract key concepts."""
    try:
        # Basic scaffolding - return mock summary
        summary = {
            "summary": f"Summary of {len(request.content)} characters of content",
            "key_concepts": [
                "artificial intelligence",
                "machine learning",
                "natural language processing",
                "prompt engineering"
            ],
            "main_topics": [
                "AI Fundamentals",
                "Language Models",
                "Prompt Design",
                "Best Practices"
            ],
            "sentiment": "neutral",
            "complexity": "intermediate",
            "estimated_reading_time": 5,
            "word_count": len(request.content.split()) if request.content else 0
        }

        return SummarizeResponse(
            success=True,
            data=summary
        ).dict()

    except Exception as e:
        return SummarizeResponse(
            success=False,
            error=str(e)
        ).dict()

@app.post("/categorize")
async def categorize_single_document(request: CategorizeRequest) -> Dict[str, Any]:
    """Categorize a single document using ML-based classification.

    Uses zero-shot classification or traditional ML approaches to automatically
    categorize documents and generate relevant tags for better organization and discovery.
    """
    try:
        start_time = time.time()

        result = await categorize_document(
            document=request.document,
            candidate_categories=request.candidate_categories,
            use_zero_shot=request.use_zero_shot
        )

        if 'error' in result:
            return {
                "success": False,
                "error": result['error'],
                "message": result.get('message', 'Categorization failed'),
                "processing_time": time.time() - start_time
            }

        return {
            "success": True,
            "data": {
                "document_id": result['document_id'],
                "category": result['category'],
                "confidence": result['confidence'],
                "tags": result['tags'],
                "method": result['method'],
                "all_scores": result.get('all_scores', {}),
                "processing_time": time.time() - start_time
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "processing_time": time.time() - start_time
        }


@app.post("/categorize/batch")
async def categorize_documents(request: BatchCategorizeRequest) -> Dict[str, Any]:
    """Categorize multiple documents in batch using ML-based classification.

    Processes multiple documents efficiently with automatic categorization
    and provides summary statistics for the batch operation.
    """
    try:
        result = await categorize_documents_batch(
            documents=request.documents,
            candidate_categories=request.candidate_categories,
            use_zero_shot=request.use_zero_shot
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "total_documents": len(request.documents) if request.documents else 0
        }


@app.get("/categorize/categories")
async def get_available_categories() -> Dict[str, Any]:
    """Get available document categories for classification."""
    return {
        "categories": [
            "api_documentation",
            "user_guide",
            "technical_specification",
            "troubleshooting",
            "configuration",
            "security",
            "performance",
            "integration",
            "general"
        ],
        "description": "Available document categories for automated classification",
        "custom_categories_supported": True
    }


@app.post("/review")
async def review_document_endpoint(request: PeerReviewRequest) -> Dict[str, Any]:
    """Perform AI-assisted peer review of documentation.

    Provides comprehensive feedback on documentation quality, including content
    completeness, technical accuracy, clarity, structure, and compliance with
    best practices. Offers actionable recommendations for improvement.
    """
    try:
        result = await review_documentation(
            content=request.content,
            doc_type=request.doc_type,
            title=request.title,
            metadata=request.metadata
        )

        if 'error' in result:
            return {
                "success": False,
                "error": result['message'],
                "document_title": request.title or 'Untitled Document'
            }

        return {
            "success": True,
            "data": {
                "document_title": result['document_title'],
                "document_type": result['document_type'],
                "overall_assessment": result['overall_assessment'],
                "criteria_analyses": result['criteria_analyses'],
                "criteria_scores": result['criteria_scores'],
                "feedback": result['feedback'],
                "review_summary": result['review_summary'],
                "processing_time": result['processing_time'],
                "review_timestamp": result['review_timestamp']
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "document_title": request.title or 'Untitled Document'
        }


@app.post("/review/compare")
async def compare_documents_endpoint(request: DocumentComparisonRequest) -> Dict[str, Any]:
    """Compare two versions of documentation to assess improvements.

    Analyzes changes between document versions and provides detailed comparison
    of quality improvements, regressions, and specific recommendations for further
    enhancements.
    """
    try:
        result = await compare_document_versions(
            old_content=request.old_content,
            new_content=request.new_content,
            doc_type=request.doc_type
        )

        if 'error' in result:
            return {
                "success": False,
                "error": result['message']
            }

        return {
            "success": True,
            "data": {
                "comparison": result['comparison'],
                "old_review": result['old_review'],
                "new_review": result['new_review'],
                "processing_time": result['processing_time'],
                "comparison_timestamp": result['comparison_timestamp']
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/review/types")
async def get_document_types() -> Dict[str, Any]:
    """Get supported document types for peer review."""
    return {
        "document_types": [
            "general",
            "api_reference",
            "user_guide",
            "tutorial",
            "architecture",
            "troubleshooting",
            "security",
            "technical_spec"
        ],
        "description": "Supported document types for peer review analysis",
        "custom_types_supported": True
    }


@app.get("/review/criteria")
async def get_review_criteria() -> Dict[str, Any]:
    """Get quality criteria used in peer review."""
    return {
        "criteria": [
            {
                "name": "completeness",
                "description": "Content completeness and coverage",
                "weight": 0.25
            },
            {
                "name": "accuracy",
                "description": "Technical accuracy and correctness",
                "weight": 0.20
            },
            {
                "name": "clarity",
                "description": "Clarity and readability",
                "weight": 0.18
            },
            {
                "name": "structure",
                "description": "Organization and structure",
                "weight": 0.15
            },
            {
                "name": "compliance",
                "description": "Standards and best practices compliance",
                "weight": 0.12
            },
            {
                "name": "engagement",
                "description": "User engagement and effectiveness",
                "weight": 0.10
            }
        ],
        "description": "Quality criteria evaluated during peer review",
        "grading_scale": {
            "A": "Excellent (≥90%)",
            "B": "Good (≥80%)",
            "C": "Average (≥70%)",
            "D": "Below Average (≥60%)",
            "F": "Poor (<60%)"
        }
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "summarizer-hub",
        "version": "1.0.0",
        "capabilities": [
            "document_summarization",
            "automated_categorization",
            "batch_processing",
            "zero_shot_classification",
            "ai_peer_review",
            "document_comparison",
            "quality_assessment",
            "best_practice_recommendations"
        ]
    }