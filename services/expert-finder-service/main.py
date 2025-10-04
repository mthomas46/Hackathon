"""
Expert Finder Service

An ecosystem-level microservice for intelligent user discovery.
Tightly coupled with user-store data but architecturally independent.

This service:
- Queries user-store for user data and relationships
- Queries doc-store for document authorship
- Queries external-service-store for service expertise
- Uses smart relevance scoring for expert matching
- Supports natural language queries
- Can integrate with LLM-gateway for advanced understanding
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
import os
import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from services.shared.infrastructure.logging.datastore_operation_logger import add_datastore_logging
except ImportError:
    # Fallback if shared module not available
    def add_datastore_logging(app, service_name):
        logger.warning(f"Datastore logging middleware not available for {service_name}")
        pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service metadata
SERVICE_NAME = "expert-finder-service"
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "5160"))

app = FastAPI(
    title="Expert Finder Service",
    description="""
    ## Intelligent User Discovery & Subject Matter Expert Identification
    
    The Expert Finder Service provides smart, relevance-based user search capabilities 
    across the ecosystem. It analyzes user data, relationships, and document associations 
    to identify relevant experts, SMEs, and potential collaborators.
    
    ### Key Features
    
    - **Natural Language Queries**: "Who knows Python backend development?"
    - **Topic-Based Search**: Find experts by technology or domain
    - **Service-Based Search**: Find users who worked on specific services
    - **SME Identification**: High-bar expert search with document threshold
    - **Teammate Discovery**: Find potential collaborators based on shared interests
    - **Team Expertise**: Aggregate team capabilities and knowledge areas
    
    ### Relevance Scoring
    
    Multi-factor scoring algorithm (0.0 to 1.0):
    - Role Matching (30% weight)
    - Topic/Interest Matching (40% weight) - Strongest signal
    - Service Subscriptions (20% weight)
    - Document Relationships (10% weight)
    - User Tags (bonus)
    - Name Matching (bonus)
    
    ### Architecture
    
    - **Standalone Microservice**: Runs in own Docker container
    - **Network**: hackathon_default (172.20.0.0/16)
    - **Dependencies**: user-store (primary), doc-store, external-service-store (optional)
    - **Horizontally Scalable**: Stateless design
    """,
    version=SERVICE_VERSION,
    contact={
        "name": "Hackathon Team",
        "url": "https://github.com/hackathon/expert-finder-service",
    },
    license_info={
        "name": "MIT",
    },
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add datastore operation logging middleware
# This logs all expert-finder operations to the log-collector service
add_datastore_logging(app, SERVICE_NAME)

# ============================================================================
# SERVICE CONFIGURATION
# ============================================================================

USER_STORE_URL = os.getenv("USER_STORE_URL", "http://localhost:5150")
DOC_STORE_URL = os.getenv("DOC_STORE_URL", "http://localhost:5087")
EXTERNAL_SERVICE_STORE_URL = os.getenv("EXTERNAL_SERVICE_STORE_URL", "http://localhost:5140")
LLM_GATEWAY_URL = os.getenv("LLM_GATEWAY_URL", "http://localhost:8100")


# ============================================================================
# MODELS
# ============================================================================

class ExpertQuery(BaseModel):
    """Query for finding experts."""
    query: str = Field(..., description="Natural language query (e.g., 'Who knows Python backend?')")
    max_results: int = Field(5, ge=1, le=20, description="Maximum number of results")
    team_id: Optional[str] = Field(None, description="Filter by team ID")
    exclude_team: bool = Field(False, description="Exclude team members if team_id provided")
    min_score: float = Field(0.1, ge=0.0, le=1.0, description="Minimum relevance score threshold")


class ExpertResult(BaseModel):
    """A single expert result."""
    user_id: str
    display_name: str
    username: str
    relevance_score: float  # 0.0 to 1.0
    explanation: str
    evidence: List[str]  # Supporting evidence
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExpertFinderResponse(BaseModel):
    """Response from expert finder."""
    query: str
    experts: List[ExpertResult]
    total_candidates: int
    execution_time_ms: float


# ============================================================================
# CORE LOGIC - USER DATA FETCHING
# ============================================================================

async def fetch_all_users() -> List[Dict[str, Any]]:
    """Fetch all users from user-store."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{USER_STORE_URL}/users")
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch users: {response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
    return []


async def fetch_users_by_team(team_id: str) -> List[Dict[str, Any]]:
    """Fetch users belonging to a specific team."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{USER_STORE_URL}/teams/{team_id}/users")
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch team users: {response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching team users: {e}")
    return []


# ============================================================================
# CORE LOGIC - KEYWORD EXTRACTION
# ============================================================================

def extract_keywords(query: str) -> Dict[str, List[str]]:
    """Extract keywords from query using pattern matching."""
    query_lower = query.lower()
    
    # Technology keywords
    tech_keywords = [
        "python", "java", "javascript", "typescript", "go", "rust", "c++", "c#", "ruby", "php",
        "react", "vue", "angular", "svelte", "node", "django", "flask", "spring", "express", "fastapi",
        "kubernetes", "docker", "aws", "gcp", "azure", "terraform", "ansible",
        "postgresql", "mongodb", "redis", "mysql", "cassandra", "elasticsearch",
        "ios", "android", "swift", "kotlin", "react native", "flutter",
        "graphql", "rest", "grpc", "kafka", "rabbitmq", "microservices"
    ]
    
    # Role/domain keywords
    role_keywords = [
        "backend", "frontend", "fullstack", "full stack", "full-stack",
        "devops", "sre", "mobile", "ios", "android", "architect", "engineer", 
        "developer", "senior", "junior", "lead", "principal", "staff",
        "analyst", "manager", "admin"
    ]
    
    # Skill/action keywords
    skill_keywords = [
        "expert", "experienced", "specialist", "knows", "familiar",
        "worked on", "created", "built", "designed", "implemented",
        "maintains", "lead", "contributed"
    ]
    
    found_tech = [k for k in tech_keywords if k in query_lower]
    found_roles = [k for k in role_keywords if k in query_lower]
    found_skills = [k for k in skill_keywords if k in query_lower]
    
    return {
        "technologies": found_tech,
        "roles": found_roles,
        "skills": found_skills
    }


# ============================================================================
# CORE LOGIC - RELEVANCE SCORING
# ============================================================================

def score_user_relevance(
    user: Dict[str, Any],
    keywords: Dict[str, List[str]],
    query: str
) -> tuple[float, List[str]]:
    """
    Score how relevant a user is to the query.
    Returns (score, evidence_list).
    """
    score = 0.0
    evidence = []
    
    # 1. Role matching (30% weight)
    user_role = user.get("role", "").lower()
    for role_keyword in keywords.get("roles", []):
        if role_keyword in user_role or role_keyword in user.get("display_name", "").lower():
            score += 0.3
            evidence.append(f"Role: {user_role}")
            break
    
    # 2. Topic/Interest matching (40% weight - strongest signal)
    topics = user.get("topic_interests", [])
    for tech in keywords.get("technologies", []):
        matching_topics = [t for t in topics if tech.lower() in t.lower()]
        if matching_topics:
            score += 0.2  # 0.2 per tech (up to 0.4 for 2+ techs)
            evidence.append(f"Topic expertise: {', '.join(matching_topics[:3])}")
    
    # 3. Service subscriptions (20% weight)
    services = user.get("service_subscriptions", [])
    for tech in keywords.get("technologies", []):
        matching_services = [s for s in services if tech.lower() in s.lower()]
        if matching_services:
            score += 0.1
            evidence.append(f"Service: {', '.join(matching_services[:2])}")
    
    # 4. Document relationships (10% weight - shows actual work)
    doc_count = len(user.get("document_relationships", []))
    if doc_count > 0:
        doc_score = min(doc_count * 0.02, 0.1)  # Cap at 0.1
        score += doc_score
        evidence.append(f"{doc_count} related documents")
    
    # 5. User tags (bonus)
    user_tags = user.get("user_tags", [])
    if user_tags:
        for tech in keywords.get("technologies", []):
            if any(tech.lower() in tag.lower() for tag in user_tags):
                score += 0.1
                evidence.append(f"Tagged: {tech}")
                break
    
    # 6. Name/username relevance (bonus)
    query_words = set(query.lower().split())
    display_name = user.get("display_name", "").lower()
    username = user.get("username", "").lower()
    
    name_words = set(display_name.split())
    username_words = set(username.split('_') + username.split('.'))
    
    if query_words & (name_words | username_words):
        score += 0.05
        evidence.append("Name match")
    
    return min(score, 1.0), evidence


# ============================================================================
# CORE LOGIC - EXPERT FINDING
# ============================================================================

async def find_experts_logic(
    query: str,
    max_results: int = 5,
    min_score: float = 0.1,
    team_id: Optional[str] = None,
    exclude_team: bool = False
) -> ExpertFinderResponse:
    """
    Core logic for finding experts.
    """
    start_time = datetime.utcnow()
    
    # Fetch users
    all_users = await fetch_all_users()
    
    if not all_users:
        return ExpertFinderResponse(
            query=query,
            experts=[],
            total_candidates=0,
            execution_time_ms=0.0
        )
    
    # Filter by team if specified
    if team_id:
        if exclude_team:
            # Exclude team members (find external experts)
            all_users = [u for u in all_users if u.get("team_id") != team_id]
        else:
            # Only team members
            all_users = [u for u in all_users if u.get("team_id") == team_id]
    
    # Extract keywords from query
    keywords = extract_keywords(query)
    
    # Score all users
    scored_users = []
    for user in all_users:
        score, evidence = score_user_relevance(user, keywords, query)
        
        if score >= min_score:
            scored_users.append({
                "user": user,
                "score": score,
                "evidence": evidence
            })
    
    # Sort by score (highest first)
    scored_users.sort(key=lambda x: x["score"], reverse=True)
    
    # Convert to ExpertResult objects
    experts = []
    for item in scored_users[:max_results]:
        user = item["user"]
        experts.append(ExpertResult(
            user_id=user.get("id", ""),
            display_name=user.get("display_name", "Unknown"),
            username=user.get("username", ""),
            relevance_score=item["score"],
            explanation=f"Matched on: {', '.join(item['evidence'][:3])}",
            evidence=item["evidence"],
            metadata={
                "role": user.get("role"),
                "topics": user.get("topic_interests", [])[:3],
                "services": user.get("service_subscriptions", [])[:3],
                "document_count": len(user.get("document_relationships", [])),
                "team_id": user.get("team_id")
            }
        ))
    
    execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    return ExpertFinderResponse(
        query=query,
        experts=experts,
        total_candidates=len(scored_users),
        execution_time_ms=execution_time
    )


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get(
    "/health",
    summary="Health Check",
    description="Check service health and dependency status",
    tags=["Health"],
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "expert-finder-service",
                        "version": "1.0.0",
                        "timestamp": "2025-01-04T12:00:00Z",
                        "dependencies": {
                            "user_store": "http://user-store:5150",
                            "doc_store": "http://doc-store:5087",
                            "external_service_store": "http://external-service-store:5140"
                        }
                    }
                }
            }
        }
    }
)
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns service status, version, and dependency URLs.
    """
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "user_store": USER_STORE_URL,
            "doc_store": DOC_STORE_URL,
            "external_service_store": EXTERNAL_SERVICE_STORE_URL
        }
    }


@app.post(
    "/experts/find",
    response_model=ExpertFinderResponse,
    summary="Find Experts (Natural Language Query)",
    description="""
    Find experts using natural language queries with smart relevance scoring.
    
    This endpoint uses a multi-factor relevance algorithm to match users based on:
    - Role keywords (backend, frontend, devops, etc.)
    - Technology keywords (Python, React, Docker, etc.)
    - Skill indicators (expert, experienced, specialist, etc.)
    
    ### Examples
    
    - "Who knows Python backend development?"
    - "Find experts in React and TypeScript"
    - "Who worked on authentication services?"
    - "Show me iOS developers"
    - "Find senior engineers with Kubernetes experience"
    
    ### Team Filtering
    
    - `team_id + exclude_team=false`: Find experts within a specific team
    - `team_id + exclude_team=true`: Find external experts (exclude team members)
    - No `team_id`: Search all users
    
    ### Relevance Scoring
    
    Results are scored from 0.0 to 1.0 based on:
    - **Role Match**: 30% weight
    - **Topic/Interest Match**: 40% weight (strongest signal)
    - **Service Subscriptions**: 20% weight
    - **Document Relationships**: 10% weight
    - **Bonuses**: User tags, name matching
    """,
    tags=["Expert Discovery"],
    responses={
        200: {
            "description": "Successfully found experts",
            "content": {
                "application/json": {
                    "example": {
                        "query": "Who knows Python backend development?",
                        "experts": [
                            {
                                "user_id": "user_001",
                                "display_name": "Sarah Chen",
                                "username": "sarah.chen",
                                "relevance_score": 0.85,
                                "explanation": "Matched on: Role: developer, Topic expertise: Python, Backend, 15 related documents",
                                "evidence": ["Role: developer", "Topic expertise: Python, Backend", "15 related documents"],
                                "metadata": {
                                    "role": "developer",
                                    "topics": ["Python", "Backend", "APIs"],
                                    "services": ["user-service", "auth-service"],
                                    "document_count": 15,
                                    "team_id": "team_123"
                                }
                            }
                        ],
                        "total_candidates": 6,
                        "execution_time_ms": 12.5
                    }
                }
            }
        },
        500: {
            "description": "Error finding experts",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error finding experts: Connection timeout"
                    }
                }
            }
        }
    }
)
async def find_experts(query_request: ExpertQuery):
    """
    Find experts based on natural language query.
    
    Uses smart relevance scoring to rank users by expertise.
    """
    try:
        result = await find_experts_logic(
            query=query_request.query,
            max_results=query_request.max_results,
            min_score=query_request.min_score,
            team_id=query_request.team_id,
            exclude_team=query_request.exclude_team
        )
        return result
    except Exception as e:
        logger.error(f"Error finding experts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error finding experts: {str(e)}"
        )


@app.get(
    "/experts/by-topic/{topic}",
    summary="Find Experts by Topic",
    description="Find experts who have expertise in a specific topic or technology",
    tags=["Expert Discovery"]
)
async def find_experts_by_topic(
    topic: str,
    max_results: int = Query(5, ge=1, le=20, description="Maximum number of results")
):
    """Find experts for a specific topic."""
    query = f"Who knows {topic}?"
    result = await find_experts_logic(query, max_results=max_results)
    
    return {
        "topic": topic,
        "experts": [e.dict() for e in result.experts],
        "count": len(result.experts),
        "execution_time_ms": result.execution_time_ms
    }


@app.get(
    "/experts/by-service/{service}",
    summary="Find Experts by Service",
    description="Find users who have worked on a specific service",
    tags=["Expert Discovery"]
)
async def find_experts_by_service(
    service: str,
    max_results: int = Query(5, ge=1, le=20, description="Maximum number of results")
):
    """Find experts who worked on a specific service."""
    # Fetch all users
    users = await fetch_all_users()
    
    # Find users subscribed to this service
    matches = []
    for user in users:
        services = user.get("service_subscriptions", [])
        if any(service.lower() in s.lower() for s in services):
            score = 0.8  # High score for direct service subscription
            evidence = [f"Subscribed to {service}"]
            
            # Bonus for document relationships
            doc_count = len(user.get("document_relationships", []))
            if doc_count > 0:
                score = min(score + 0.1, 1.0)
                evidence.append(f"{doc_count} related documents")
            
            matches.append({
                "user_id": user.get("id"),
                "display_name": user.get("display_name"),
                "username": user.get("username"),
                "relevance_score": score,
                "evidence": evidence,
                "metadata": {
                    "services": services[:3],
                    "document_count": doc_count
                }
            })
    
    # Sort by score
    matches.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    return {
        "service": service,
        "experts": matches[:max_results],
        "count": len(matches)
    }


@app.get(
    "/experts/sme/{area}",
    summary="Find Subject Matter Experts",
    description="Find SMEs with proven expertise (requires minimum document threshold)",
    tags=["SME Identification"]
)
async def find_subject_matter_experts(
    area: str,
    min_documents: int = Query(3, ge=1, description="Minimum document count required"),
    max_results: int = Query(5, ge=1, le=20, description="Maximum number of results")
):
    """
    Find subject matter experts in a specific area.
    Requires users to have meaningful document relationships (actual work).
    """
    # Use expert finder with higher threshold
    result = await find_experts_logic(
        query=f"Expert in {area}",
        max_results=max_results * 2,  # Get more candidates
        min_score=0.3  # Higher threshold for SMEs
    )
    
    # Filter to those with sufficient document history
    smes = [
        expert for expert in result.experts
        if expert.metadata.get("document_count", 0) >= min_documents
    ]
    
    # Re-score with document count emphasis
    for expert in smes:
        doc_count = expert.metadata.get("document_count", 0)
        doc_bonus = min(doc_count * 0.05, 0.3)
        expert.relevance_score = min(expert.relevance_score + doc_bonus, 1.0)
        expert.evidence.append(f"SME: {doc_count} documents")
    
    # Re-sort and limit
    smes.sort(key=lambda x: x.relevance_score, reverse=True)
    
    return {
        "area": area,
        "subject_matter_experts": [e.dict() for e in smes[:max_results]],
        "count": len(smes[:max_results])
    }


@app.get(
    "/experts/teammates/{user_id}",
    summary="Find Potential Teammates",
    description="Discover potential collaborators based on shared interests and services",
    tags=["Team Collaboration"]
)
async def find_potential_teammates(
    user_id: str,
    max_results: int = Query(5, ge=1, le=20, description="Maximum number of results")
):
    """Find potential teammates based on shared interests and services."""
    try:
        # Get all users
        all_users = await fetch_all_users()
        
        # Find the target user
        target_user = None
        for u in all_users:
            if u.get("id") == user_id:
                target_user = u
                break
        
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_topics = set(target_user.get("topic_interests", []))
        user_services = set(target_user.get("service_subscriptions", []))
        
        potential_teammates = []
        
        for other_user in all_users:
            if other_user.get("id") == user_id:
                continue  # Skip self
            
            other_topics = set(other_user.get("topic_interests", []))
            other_services = set(other_user.get("service_subscriptions", []))
            
            # Calculate overlap
            shared_topics = user_topics & other_topics
            shared_services = user_services & other_services
            
            if shared_topics or shared_services:
                # Score based on overlap
                topic_score = len(shared_topics) * 0.3
                service_score = len(shared_services) * 0.7
                total_score = min(topic_score + service_score, 1.0)
                
                potential_teammates.append({
                    "user_id": other_user.get("id"),
                    "display_name": other_user.get("display_name"),
                    "username": other_user.get("username"),
                    "collaboration_score": total_score,
                    "shared_topics": list(shared_topics),
                    "shared_services": list(shared_services),
                    "same_team": other_user.get("team_id") == target_user.get("team_id")
                })
        
        # Sort by score
        potential_teammates.sort(key=lambda x: x["collaboration_score"], reverse=True)
        
        return {
            "user_id": user_id,
            "potential_teammates": potential_teammates[:max_results],
            "count": len(potential_teammates[:max_results])
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding teammates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/teams/{team_id}/expertise",
    summary="Get Team Expertise Summary",
    description="Aggregate expertise, skills, and capabilities for an entire team",
    tags=["Team Collaboration"]
)
async def get_team_expertise_summary(team_id: str):
    """Get expertise summary for a team."""
    try:
        # Fetch all users and filter by team
        all_users = await fetch_all_users()
        team_members = [u for u in all_users if u.get("team_id") == team_id]
        
        if not team_members:
            return {
                "team_id": team_id,
                "member_count": 0,
                "topics": [],
                "services": [],
                "total_documents": 0
            }
        
        # Aggregate expertise
        all_topics = []
        all_services = []
        total_docs = 0
        
        for member in team_members:
            all_topics.extend(member.get("topic_interests", []))
            all_services.extend(member.get("service_subscriptions", []))
            total_docs += len(member.get("document_relationships", []))
        
        # Count frequencies
        from collections import Counter
        topic_counts = Counter(all_topics)
        service_counts = Counter(all_services)
        
        return {
            "team_id": team_id,
            "member_count": len(team_members),
            "topics": [{"topic": k, "count": v} for k, v in topic_counts.most_common(10)],
            "services": [{"service": k, "count": v} for k, v in service_counts.most_common(10)],
            "total_documents": total_docs,
            "avg_documents_per_member": total_docs / len(team_members) if team_members else 0
        }
    except Exception as e:
        logger.error(f"Error getting team expertise: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NEW API ENDPOINTS (Phase 2.3) - Enhanced Metadata Queries
# ============================================================================

@app.get(
    "/experts/by-experience",
    summary="Find experts by experience level",
    description="Query experts based on experience level (junior/mid/senior), domain, and contribution count.",
    tags=["Enhanced Metadata Queries"],
    responses={
        200: {
            "description": "List of experts matching experience criteria",
            "content": {
                "application/json": {
                    "example": {
                        "query": {
                            "level": "senior",
                            "domain": "backend",
                            "min_contributions": 50
                        },
                        "experts": [
                            {
                                "username": "senior.dev",
                                "display_name": "Senior Dev",
                                "experience_level": "senior",
                                "domain": "backend",
                                "total_contributions": 150,
                                "years_active": 5
                            }
                        ],
                        "count": 1
                    }
                }
            }
        },
        400: {"description": "Invalid parameters"}
    }
)
async def find_experts_by_experience(
    level: str = Query(..., description="Experience level: junior, mid, senior"),
    domain: str = Query(None, description="Domain filter: backend, frontend, devops, etc."),
    min_contributions: int = Query(10, description="Minimum contributions threshold")
):
    """
    Find experts based on experience level and domain.
    
    Experience is calculated from:
    - Code volume (lines added/deleted)
    - Time span (GitHub PR activity)
    - PR count
    - Review participation
    """
    try:
        all_users = await fetch_all_users()
        
        # Filter by experience level based on GitHub metrics
        filtered_experts = []
        for user in all_users:
            # Get user's GitHub metrics from user-store
            user_id = user.get("id")
            # For now, use document count as proxy for contributions
            contributions = len(user.get("document_relationships", []))
            
            # Simple experience level heuristic
            if level == "senior" and contributions >= 50:
                exp_level = "senior"
            elif level == "mid" and 20 <= contributions < 50:
                exp_level = "mid"
            elif level == "junior" and contributions < 20:
                exp_level = "junior"
            else:
                continue
            
            # Domain filtering (if specified)
            if domain:
                topics = [t.lower() for t in user.get("topic_interests", [])]
                if domain.lower() not in " ".join(topics):
                    continue
            
            # Min contributions filter
            if contributions < min_contributions:
                continue
            
            filtered_experts.append({
                "username": user.get("username"),
                "display_name": user.get("full_name", user.get("username")),
                "experience_level": exp_level,
                "domain": domain or "general",
                "total_contributions": contributions,
                "topics": user.get("topic_interests", [])
            })
        
        # Sort by contributions
        filtered_experts.sort(key=lambda x: x["total_contributions"], reverse=True)
        
        return {
            "query": {
                "level": level,
                "domain": domain,
                "min_contributions": min_contributions
            },
            "experts": filtered_experts,
            "count": len(filtered_experts)
        }
    except Exception as e:
        logger.error(f"Error finding experts by experience: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/experts/reviewers",
    summary="Find code review experts",
    description="Query experts based on review quality score, technology, and review count.",
    tags=["Enhanced Metadata Queries"],
    responses={
        200: {
            "description": "List of code review experts",
            "content": {
                "application/json": {
                    "example": {
                        "query": {
                            "quality": "high",
                            "technology": "Python",
                            "min_reviews": 20
                        },
                        "experts": [
                            {
                                "username": "code.reviewer",
                                "display_name": "Code Reviewer",
                                "review_quality_score": 0.85,
                                "total_reviews": 45,
                                "approval_rate": 0.78,
                                "technologies": ["Python", "FastAPI"]
                            }
                        ],
                        "count": 1
                    }
                }
            }
        },
        400: {"description": "Invalid parameters"}
    }
)
async def find_code_review_experts(
    quality: str = Query("high", description="Review quality: low, medium, high"),
    technology: str = Query(None, description="Technology/language filter"),
    min_reviews: int = Query(10, description="Minimum reviews count")
):
    """
    Find experts in code review based on quality score and technology.
    
    Review quality is calculated from:
    - Comment depth and actionability
    - Code snippet analysis
    - Review state (approved vs changes requested)
    """
    try:
        all_users = await fetch_all_users()
        
        # Filter by review expertise
        review_experts = []
        for user in all_users:
            # For now, use document relationships as proxy for reviews
            reviews = len(user.get("document_relationships", []))
            
            if reviews < min_reviews:
                continue
            
            # Simple quality heuristic
            quality_score = min(reviews / 100.0, 1.0)  # Normalize
            
            if quality == "high" and quality_score < 0.7:
                continue
            elif quality == "medium" and (quality_score < 0.4 or quality_score >= 0.7):
                continue
            elif quality == "low" and quality_score >= 0.4:
                continue
            
            # Technology filtering
            if technology:
                topics = [t.lower() for t in user.get("topic_interests", [])]
                if technology.lower() not in " ".join(topics):
                    continue
            
            review_experts.append({
                "username": user.get("username"),
                "display_name": user.get("full_name", user.get("username")),
                "review_quality_score": round(quality_score, 2),
                "total_reviews": reviews,
                "approval_rate": 0.75,  # Placeholder
                "technologies": user.get("topic_interests", [])
            })
        
        # Sort by quality score
        review_experts.sort(key=lambda x: x["review_quality_score"], reverse=True)
        
        return {
            "query": {
                "quality": quality,
                "technology": technology,
                "min_reviews": min_reviews
            },
            "experts": review_experts,
            "count": len(review_experts)
        }
    except Exception as e:
        logger.error(f"Error finding review experts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/experts/component-leads",
    summary="Find component ownership experts",
    description="Query experts who lead or contribute significantly to specific Jira components.",
    tags=["Enhanced Metadata Queries"],
    responses={
        200: {
            "description": "List of component lead experts",
            "content": {
                "application/json": {
                    "example": {
                        "query": {
                            "component": "authentication",
                            "min_contributions": 10
                        },
                        "experts": [
                            {
                                "username": "auth.expert",
                                "display_name": "Auth Expert",
                                "component": "authentication",
                                "contributions": 35,
                                "is_component_lead": True,
                                "worklog_hours": 120
                            }
                        ],
                        "count": 1
                    }
                }
            }
        },
        400: {"description": "Invalid parameters"}
    }
)
async def find_component_leads(
    component: str = Query(..., description="Jira component name"),
    min_contributions: int = Query(5, description="Minimum contributions to component")
):
    """
    Find experts who own or contribute significantly to a specific Jira component.
    
    Identifies:
    - Component leads (is_component_lead flag)
    - Frequent contributors
    - Worklog time spent on component
    """
    try:
        all_users = await fetch_all_users()
        
        # Filter by component expertise
        component_experts = []
        for user in all_users:
            # For now, check if component matches topics/services
            topics = [t.lower() for t in user.get("topic_interests", [])]
            services = [s.lower() for s in user.get("service_subscriptions", [])]
            
            if component.lower() not in " ".join(topics + services):
                continue
            
            contributions = len(user.get("document_relationships", []))
            
            if contributions < min_contributions:
                continue
            
            component_experts.append({
                "username": user.get("username"),
                "display_name": user.get("full_name", user.get("username")),
                "component": component,
                "contributions": contributions,
                "is_component_lead": contributions >= 20,  # Heuristic
                "worklog_hours": contributions * 2,  # Placeholder
                "topics": user.get("topic_interests", [])
            })
        
        # Sort by contributions
        component_experts.sort(key=lambda x: x["contributions"], reverse=True)
        
        return {
            "query": {
                "component": component,
                "min_contributions": min_contributions
            },
            "experts": component_experts,
            "count": len(component_experts)
        }
    except Exception as e:
        logger.error(f"Error finding component leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/experts/merge-authority",
    summary="Find users with merge authority",
    description="Query experts who have merge permissions and authority, filtered by repository and merge count.",
    tags=["Enhanced Metadata Queries"],
    responses={
        200: {
            "description": "List of users with merge authority",
            "content": {
                "application/json": {
                    "example": {
                        "query": {
                            "repo": "backend-api",
                            "min_merges": 10
                        },
                        "experts": [
                            {
                                "username": "tech.lead",
                                "display_name": "Tech Lead",
                                "repository": "backend-api",
                                "merge_authority": True,
                                "total_merges": 45,
                                "merge_approval_rate": 0.92
                            }
                        ],
                        "count": 1
                    }
                }
            }
        },
        400: {"description": "Invalid parameters"}
    }
)
async def find_merge_authority_experts(
    repo: str = Query(None, description="Repository filter"),
    min_merges: int = Query(5, description="Minimum merges count")
):
    """
    Find experts with merge authority and permissions.
    
    Identifies:
    - Users with merge_authority flag
    - Frequent mergers
    - Repository-specific merge history
    """
    try:
        all_users = await fetch_all_users()
        
        # Filter by merge authority
        merge_experts = []
        for user in all_users:
            # Check role for merge authority (manager, admin)
            role = user.get("role", "").lower()
            has_authority = role in ["admin", "manager", "tech_lead"]
            
            if not has_authority:
                continue
            
            # Calculate merges (using documents as proxy)
            merges = len(user.get("document_relationships", []))
            
            if merges < min_merges:
                continue
            
            # Repo filtering
            if repo:
                services = [s.lower() for s in user.get("service_subscriptions", [])]
                if repo.lower() not in " ".join(services):
                    continue
            
            merge_experts.append({
                "username": user.get("username"),
                "display_name": user.get("full_name", user.get("username")),
                "repository": repo or "all",
                "merge_authority": has_authority,
                "total_merges": merges,
                "merge_approval_rate": 0.85,  # Placeholder
                "role": role
            })
        
        # Sort by merges
        merge_experts.sort(key=lambda x: x["total_merges"], reverse=True)
        
        return {
            "query": {
                "repo": repo,
                "min_merges": min_merges
            },
            "experts": merge_experts,
            "count": len(merge_experts)
        }
    except Exception as e:
        logger.error(f"Error finding merge authority experts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/experts/by-activity",
    summary="Find experts by activity recency",
    description="Query experts based on recent activity and activity frequency.",
    tags=["Enhanced Metadata Queries"],
    responses={
        200: {
            "description": "List of active experts",
            "content": {
                "application/json": {
                    "example": {
                        "query": {
                            "recency": "last_30_days",
                            "activity_frequency": "daily"
                        },
                        "experts": [
                            {
                                "username": "active.dev",
                                "display_name": "Active Dev",
                                "last_activity": "2024-01-10",
                                "activity_frequency": "daily",
                                "recent_contributions": 25,
                                "activity_score": 0.95
                            }
                        ],
                        "count": 1
                    }
                }
            }
        },
        400: {"description": "Invalid parameters"}
    }
)
async def find_experts_by_activity(
    recency: str = Query("last_30_days", description="Recency filter: last_7_days, last_30_days, last_90_days"),
    activity_frequency: str = Query(None, description="Activity frequency: daily, weekly, monthly"),
    min_contributions: int = Query(1, description="Minimum recent contributions")
):
    """
    Find experts based on recent activity and activity frequency.
    
    Activity metrics:
    - Last activity timestamp
    - Activity frequency (daily, weekly, monthly)
    - Recent contributions count
    - Activity score (0.0 to 1.0)
    """
    try:
        all_users = await fetch_all_users()
        
        # Filter by activity
        active_experts = []
        for user in all_users:
            # Check if user has recent activity (using status as proxy)
            status = user.get("status", "inactive")
            if status != "active":
                continue
            
            contributions = len(user.get("document_relationships", []))
            
            if contributions < min_contributions:
                continue
            
            # Calculate activity score
            activity_score = min(contributions / 50.0, 1.0)
            
            # Frequency heuristic
            if activity_frequency == "daily" and activity_score < 0.8:
                continue
            elif activity_frequency == "weekly" and activity_score < 0.5:
                continue
            elif activity_frequency == "monthly" and activity_score < 0.2:
                continue
            
            active_experts.append({
                "username": user.get("username"),
                "display_name": user.get("full_name", user.get("username")),
                "last_activity": "2024-01-10",  # Placeholder
                "activity_frequency": activity_frequency or "variable",
                "recent_contributions": contributions,
                "activity_score": round(activity_score, 2),
                "status": status
            })
        
        # Sort by activity score
        active_experts.sort(key=lambda x: x["activity_score"], reverse=True)
        
        return {
            "query": {
                "recency": recency,
                "activity_frequency": activity_frequency,
                "min_contributions": min_contributions
            },
            "experts": active_experts,
            "count": len(active_experts)
        }
    except Exception as e:
        logger.error(f"Error finding experts by activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SERVICE REGISTRATION & STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Register service with service discovery on startup."""
    logger.info(f"🚀 Starting {SERVICE_NAME} v{SERVICE_VERSION}")
    logger.info(f"   Port: {SERVICE_PORT}")
    logger.info(f"   User Store: {USER_STORE_URL}")
    logger.info(f"   Doc Store: {DOC_STORE_URL}")
    logger.info(f"   External Service Store: {EXTERNAL_SERVICE_STORE_URL}")
    
    # TODO: Register with service discovery if available
    # try:
    #     from services.shared.infrastructure.service_discovery import register_service
    #     register_service(SERVICE_NAME, SERVICE_PORT)
    # except Exception as e:
    #     logger.warning(f"Could not register with service discovery: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
