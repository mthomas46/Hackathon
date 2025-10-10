"""
Business API routes for expert finding.

Provides endpoints for finding experts, identifying SMEs, and discovering teammates.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from domain.value_objects.expert_query import ExpertQuery
from application.use_cases.find_experts_use_case import FindExpertsUseCase
from infrastructure.config.settings import Settings, get_settings
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.document_repository import DocumentRepository
from infrastructure.repositories.service_repository import ServiceRepository
from domain.services.relevance_scoring_service import RelevanceScoringService
from utils.validators import validate_query_text, validate_limit, validate_id
from utils.constants import DEFAULT_RESULTS, MAX_RESULTS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Expert Finding"])


# ============================================================================
# Request/Response Models
# ============================================================================

class FindExpertsRequest(BaseModel):
    """Request model for finding experts."""
    query_text: str = Field(..., description="Natural language query or search text")
    role: Optional[str] = Field(None, description="Filter by specific role")
    topics: List[str] = Field(default_factory=list, description="Filter by topics")
    services: List[str] = Field(default_factory=list, description="Filter by services")
    tags: List[str] = Field(default_factory=list, description="Filter by tags")
    limit: int = Field(DEFAULT_RESULTS, ge=1, le=MAX_RESULTS, description="Maximum results")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum relevance score")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query_text": "Python backend developer",
                "role": "Backend Developer",
                "topics": ["Python", "FastAPI", "Docker"],
                "limit": 10,
                "min_score": 0.6
            }
        }


class IdentifySMEsRequest(BaseModel):
    """Request model for identifying subject matter experts."""
    query_text: str = Field(..., description="Topic or area of expertise")
    topics: List[str] = Field(default_factory=list, description="Filter by topics")
    min_documents: int = Field(10, ge=1, description="Minimum document count for SME status")
    min_score: float = Field(0.7, ge=0.0, le=1.0, description="Minimum relevance score")
    limit: int = Field(DEFAULT_RESULTS, ge=1, le=MAX_RESULTS, description="Maximum results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query_text": "FastAPI microservices",
                "topics": ["FastAPI", "Microservices"],
                "min_documents": 10,
                "min_score": 0.7,
                "limit": 5
            }
        }


class ExpertMatchResponse(BaseModel):
    """Response model for expert match."""
    user_id: str
    name: str
    role: Optional[str]
    seniority: str
    topics: List[str]
    tags: List[str]
    services: List[str]
    document_count: int
    service_count: int
    overall_score: float
    role_score: float
    topic_score: float
    service_score: float
    document_score: float
    match_quality: str
    explanation: str


class FindExpertsResponse(BaseModel):
    """Response model for find experts endpoint."""
    query: str
    total_matches: int
    matches: List[ExpertMatchResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Python backend developer",
                "total_matches": 5,
                "matches": [
                    {
                        "user_id": "user123",
                        "name": "Alice Smith",
                        "role": "Backend Developer",
                        "seniority": "senior",
                        "topics": ["Python", "FastAPI", "Docker"],
                        "tags": ["backend", "python"],
                        "services": ["user-store", "doc-store"],
                        "document_count": 25,
                        "service_count": 3,
                        "overall_score": 0.85,
                        "role_score": 0.90,
                        "topic_score": 0.80,
                        "service_score": 0.75,
                        "document_score": 0.85,
                        "match_quality": "excellent",
                        "explanation": "Strong role match: Backend Developer; Strong topic overlap (80%); Significant contributions (25 docs); SME status"
                    }
                ]
            }
        }


# ============================================================================
# Dependency Injection
# ============================================================================

def get_find_experts_use_case(settings: Settings = Depends(get_settings)) -> FindExpertsUseCase:
    """
    Create and configure FindExpertsUseCase with dependencies.
    
    This is a factory function that creates the use case with all its
    dependencies properly initialized.
    """
    # Create repositories
    user_repo = UserRepository(settings.user_store_url, settings.http_timeout)
    doc_repo = DocumentRepository(settings.doc_store_url, settings.http_timeout)
    service_repo = ServiceRepository(settings.service_store_url, settings.http_timeout)
    
    # Create scoring service
    scoring_service = RelevanceScoringService(
        role_weight=settings.role_weight,
        topic_weight=settings.topic_weight,
        service_weight=settings.service_weight,
        document_weight=settings.document_weight
    )
    
    # Create use case
    return FindExpertsUseCase(
        user_repo=user_repo,
        doc_repo=doc_repo,
        service_repo=service_repo,
        scoring_service=scoring_service
    )


# ============================================================================
# Business Endpoints
# ============================================================================

@router.post("/find-experts", response_model=FindExpertsResponse)
async def find_experts(
    request: FindExpertsRequest,
    use_case: FindExpertsUseCase = Depends(get_find_experts_use_case)
) -> FindExpertsResponse:
    """
    Find experts matching search criteria.
    
    Uses multi-factor relevance scoring to identify users with specific
    expertise based on role, topics, services, and document contributions.
    
    **Scoring Algorithm**:
    - Role Matching: 30% weight
    - Topic Matching: 40% weight (strongest signal)
    - Service Contributions: 20% weight
    - Document Authorship: 10% weight
    - Bonus: Name match, tag matching
    
    **Returns**: List of experts sorted by relevance score (highest first)
    """
    try:
        # Validate input
        validate_query_text(request.query_text)
        validate_limit(request.limit, MAX_RESULTS)
        
        # Create domain query
        query = ExpertQuery(
            query_text=request.query_text,
            role=request.role,
            topics=request.topics,
            services=request.services,
            tags=request.tags,
            limit=request.limit,
            min_score=request.min_score,
            sme_only=False
        )
        
        # Execute use case
        matches = await use_case.execute(query)
        
        # Convert to response model
        response_matches = [
            ExpertMatchResponse(
                user_id=match.expert.user_id,
                name=match.expert.name,
                role=match.expert.role,
                seniority=match.expert.seniority,
                topics=match.expert.topics,
                tags=match.expert.tags,
                services=match.expert.services,
                document_count=match.expert.document_count,
                service_count=match.expert.service_count,
                overall_score=match.overall_score,
                role_score=match.role_score,
                topic_score=match.topic_score,
                service_score=match.service_score,
                document_score=match.document_score,
                match_quality=match.match_quality(),
                explanation=match.explanation
            )
            for match in matches
        ]
        
        logger.info(
            f"Found {len(response_matches)} experts for query: '{request.query_text}'"
        )
        
        return FindExpertsResponse(
            query=request.query_text,
            total_matches=len(response_matches),
            matches=response_matches
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error finding experts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/identify-smes", response_model=FindExpertsResponse)
async def identify_smes(
    request: IdentifySMEsRequest,
    use_case: FindExpertsUseCase = Depends(get_find_experts_use_case)
) -> FindExpertsResponse:
    """
    Identify Subject Matter Experts (SMEs).
    
    Finds experts with significant contributions (documents) in specific areas.
    Higher bar than general expert search - requires minimum document count.
    
    **SME Criteria**:
    - Minimum document count (default: 10)
    - High relevance score (default: 0.7)
    - Strong topic match
    
    **Returns**: List of SMEs sorted by relevance score
    """
    try:
        # Validate input
        validate_query_text(request.query_text)
        validate_limit(request.limit, MAX_RESULTS)
        
        # Create domain query with SME filter
        query = ExpertQuery(
            query_text=request.query_text,
            topics=request.topics,
            limit=request.limit,
            min_score=request.min_score,
            sme_only=True,  # Filter for SMEs only
            min_documents=request.min_documents
        )
        
        # Execute use case
        matches = await use_case.execute(query)
        
        # Convert to response model
        response_matches = [
            ExpertMatchResponse(
                user_id=match.expert.user_id,
                name=match.expert.name,
                role=match.expert.role,
                seniority=match.expert.seniority,
                topics=match.expert.topics,
                tags=match.expert.tags,
                services=match.expert.services,
                document_count=match.expert.document_count,
                service_count=match.expert.service_count,
                overall_score=match.overall_score,
                role_score=match.role_score,
                topic_score=match.topic_score,
                service_score=match.service_score,
                document_score=match.document_score,
                match_quality=match.match_quality(),
                explanation=match.explanation
            )
            for match in matches
        ]
        
        logger.info(
            f"Identified {len(response_matches)} SMEs for query: '{request.query_text}'"
        )
        
        return FindExpertsResponse(
            query=request.query_text,
            total_matches=len(response_matches),
            matches=response_matches
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error identifying SMEs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

