"""
Demo Service for Expert Finder.

Provides self-contained and ecosystem-based demos that showcase
the service's capabilities and generate tangible data/reports.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.document_repository import DocumentRepository
from infrastructure.repositories.service_repository import ServiceRepository
from application.use_cases.find_experts_use_case import FindExpertsUseCase
from domain.value_objects.expert_query import ExpertQuery
from domain.services.relevance_scoring_service import RelevanceScoringService


class DemoService:
    """
    Service for executing demonstrations of expert-finder capabilities.
    
    Provides both self-contained demos (with mock data) and ecosystem-based demos
    (requiring actual service dependencies).
    """
    
    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        doc_repo: Optional[DocumentRepository] = None,
        service_repo: Optional[ServiceRepository] = None
    ):
        """
        Initialize demo service.
        
        Args:
            user_repo: User repository (optional, for ecosystem demos)
            doc_repo: Document repository (optional, for ecosystem demos)
            service_repo: Service repository (optional, for ecosystem demos)
        """
        self.user_repo = user_repo
        self.doc_repo = doc_repo
        self.service_repo = service_repo
        self.scoring_service = RelevanceScoringService()
        
    def list_demos(self) -> List[Dict[str, Any]]:
        """
        List all available demos.
        
        Returns:
            List of demo metadata
        """
        return [
            {
                "id": "scoring-algorithm",
                "name": "Relevance Scoring Algorithm Demo",
                "description": "Demonstrates the multi-factor scoring algorithm with sample data",
                "type": "self-contained",
                "duration": "< 1 second",
                "requires_dependencies": False,
                "output": "Scoring breakdown with explanations"
            },
            {
                "id": "expert-matching",
                "name": "Expert Matching Demo",
                "description": "Shows how experts are matched based on various criteria",
                "type": "self-contained",
                "duration": "< 1 second",
                "requires_dependencies": False,
                "output": "List of matched experts with scores"
            },
            {
                "id": "sme-identification",
                "name": "SME Identification Demo",
                "description": "Identifies subject matter experts using contribution thresholds",
                "type": "self-contained",
                "duration": "< 1 second",
                "requires_dependencies": False,
                "output": "List of SMEs with evidence"
            },
            {
                "id": "ecosystem-expert-search",
                "name": "Ecosystem Expert Search",
                "description": "Live search for experts using actual ecosystem data",
                "type": "ecosystem",
                "duration": "1-3 seconds",
                "requires_dependencies": True,
                "dependencies": ["user-store"],
                "output": "Real expert matches from ecosystem"
            },
            {
                "id": "ecosystem-sme-discovery",
                "name": "Ecosystem SME Discovery",
                "description": "Live SME identification using ecosystem data",
                "type": "ecosystem",
                "duration": "2-5 seconds",
                "requires_dependencies": True,
                "dependencies": ["user-store", "doc-store"],
                "output": "Real SMEs from ecosystem with contribution metrics"
            },
            {
                "id": "performance-benchmark",
                "name": "Performance Benchmark",
                "description": "Benchmarks scoring performance with various dataset sizes",
                "type": "self-contained",
                "duration": "2-5 seconds",
                "requires_dependencies": False,
                "output": "Performance metrics and timing data"
            }
        ]
    
    async def run_demo(self, demo_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a specific demo.
        
        Args:
            demo_id: The ID of the demo to run
            params: Optional parameters for the demo
            
        Returns:
            Demo execution results with data and metadata
            
        Raises:
            ValueError: If demo_id is not found
        """
        start_time = datetime.utcnow()
        
        # Route to appropriate demo implementation
        demo_methods = {
            "scoring-algorithm": self._demo_scoring_algorithm,
            "expert-matching": self._demo_expert_matching,
            "sme-identification": self._demo_sme_identification,
            "ecosystem-expert-search": self._demo_ecosystem_expert_search,
            "ecosystem-sme-discovery": self._demo_ecosystem_sme_discovery,
            "performance-benchmark": self._demo_performance_benchmark
        }
        
        if demo_id not in demo_methods:
            raise ValueError(f"Unknown demo ID: {demo_id}")
        
        # Execute demo
        demo_method = demo_methods[demo_id]
        result = await demo_method(params or {})
        
        # Add execution metadata
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        return {
            "demo_id": demo_id,
            "demo_name": next((d["name"] for d in self.list_demos() if d["id"] == demo_id), demo_id),
            "executed_at": start_time.isoformat(),
            "execution_time_seconds": round(execution_time, 3),
            "status": "success",
            "data": result
        }
    
    async def _demo_scoring_algorithm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Demo: Relevance Scoring Algorithm"""
        from domain.entities.expert import Expert
        from domain.value_objects.expert_query import ExpertQuery
        
        # Create sample query
        query = ExpertQuery(
            query_text="Python backend developer with FastAPI experience",
            role="Backend Developer",
            topics=["Python", "FastAPI"],
            limit=5
        )
        
        # Create sample experts with different matching profiles
        experts = [
            Expert(
                user_id="user_001",
                name="Alice Smith",
                role="Backend Developer",
                topics=["Python", "FastAPI", "PostgreSQL", "Docker"],
                services=["api-gateway", "user-service"],
                document_count=25,
                service_count=5
            ),
            Expert(
                user_id="user_002",
                name="Bob Johnson",
                role="Frontend Developer",
                topics=["React", "TypeScript", "JavaScript"],
                services=["frontend-app"],
                document_count=15,
                service_count=2
            ),
            Expert(
                user_id="user_003",
                name="Carol Davis",
                role="Backend Developer",
                topics=["Python", "Django", "MySQL"],
                services=["legacy-api"],
                document_count=40,
                service_count=3
            ),
            Expert(
                user_id="user_004",
                name="David Wilson",
                role="Full Stack Developer",
                topics=["Python", "FastAPI", "React"],
                services=["api-gateway", "frontend-app", "data-service"],
                document_count=30,
                service_count=8
            ),
            Expert(
                user_id="user_005",
                name="Eve Martinez",
                role="DevOps Engineer",
                topics=["Python", "Kubernetes", "Docker"],
                services=["infrastructure"],
                document_count=10,
                service_count=1
            )
        ]
        
        # Score all experts
        matches = [self.scoring_service.calculate_score(expert, query) for expert in experts]
        
        # Sort by score
        matches.sort(key=lambda m: m.overall_score, reverse=True)
        
        return {
            "query": query.query_text,
            "scoring_weights": {
                "role": self.scoring_service.role_weight,
                "topic": self.scoring_service.topic_weight,
                "service": self.scoring_service.service_weight,
                "document": self.scoring_service.document_weight
            },
            "candidates_scored": len(experts),
            "results": [
                {
                    "rank": idx + 1,
                    "expert": {
                        "user_id": m.expert.user_id,
                        "name": m.expert.name,
                        "role": m.expert.role,
                        "topics": m.expert.topics[:3],  # Top 3 topics
                        "document_count": m.expert.document_count
                    },
                    "scores": {
                        "overall": round(m.overall_score, 3),
                        "role": round(m.role_score, 3),
                        "topic": round(m.topic_score, 3),
                        "service": round(m.service_score, 3),
                        "document": round(m.document_score, 3)
                    },
                    "match_quality": m.match_quality(),
                    "explanation": m.explanation
                }
                for idx, m in enumerate(matches[:3])  # Top 3 results
            ],
            "insights": {
                "best_match": matches[0].expert.name if matches else "None",
                "best_score": round(matches[0].overall_score, 3) if matches else 0.0,
                "scoring_breakdown": f"The scoring algorithm uses 4 factors: role ({self.scoring_service.role_weight*100}%), "
                                    f"topics ({self.scoring_service.topic_weight*100}%), "
                                    f"services ({self.scoring_service.service_weight*100}%), and "
                                    f"documents ({self.scoring_service.document_weight*100}%)"
            }
        }
    
    async def _demo_expert_matching(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Demo: Expert Matching Process"""
        return {
            "demo_type": "Expert Matching",
            "description": "This demo shows how different query parameters affect expert matching",
            "scenarios": [
                {
                    "scenario": "Role-based search",
                    "query": "Backend Developer",
                    "matching_strategy": "Primary match on role field with 30% weight",
                    "typical_results": "10-20 developers with backend role",
                    "use_case": "Finding developers for backend-focused projects"
                },
                {
                    "scenario": "Topic-based search",
                    "query": "Python",
                    "matching_strategy": "Primary match on topics field with 40% weight (highest)",
                    "typical_results": "15-30 users with Python expertise",
                    "use_case": "Finding experts in specific technology"
                },
                {
                    "scenario": "Natural language query",
                    "query": "Python backend developer with API experience",
                    "matching_strategy": "Combined matching across role, topics, and service experience",
                    "typical_results": "5-15 highly relevant matches",
                    "use_case": "Complex searches requiring multiple criteria"
                },
                {
                    "scenario": "Service-based search",
                    "query": {"services": ["api-gateway"]},
                    "matching_strategy": "Match on service experience with 20% weight",
                    "typical_results": "5-10 users who worked on api-gateway",
                    "use_case": "Finding team members familiar with specific services"
                }
            ],
            "algorithm_flow": [
                "1. Parse query and extract role, topics, services",
                "2. Fetch candidate users from user-store",
                "3. Enrich with document and service counts",
                "4. Calculate multi-factor relevance scores",
                "5. Filter by minimum score threshold",
                "6. Sort by overall score (descending)",
                "7. Limit results and return with explanations"
            ]
        }
    
    async def _demo_sme_identification(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Demo: SME Identification"""
        return {
            "demo_type": "Subject Matter Expert (SME) Identification",
            "description": "Shows how SMEs are identified using contribution thresholds",
            "criteria": {
                "min_documents": 10,
                "min_score": 0.7,
                "rationale": "SMEs must have both proven contributions (documents) and high expertise scores"
            },
            "sample_smes": [
                {
                    "name": "Alice Smith (Senior Backend Developer)",
                    "expertise": ["Python", "FastAPI", "PostgreSQL"],
                    "contributions": {
                        "documents_authored": 35,
                        "services_contributed": 7,
                        "years_experience": "5+ years"
                    },
                    "relevance_score": 0.92,
                    "sme_status": "✅ Qualified",
                    "reason": "High contribution count and excellent topic match"
                },
                {
                    "name": "Bob Johnson (Mid-level Frontend Developer)",
                    "expertise": ["React", "TypeScript"],
                    "contributions": {
                        "documents_authored": 8,
                        "services_contributed": 2,
                        "years_experience": "2-3 years"
                    },
                    "relevance_score": 0.78,
                    "sme_status": "❌ Not Qualified",
                    "reason": "Below minimum document threshold (8 < 10)"
                },
                {
                    "name": "Carol Davis (Senior Full Stack Developer)",
                    "expertise": ["Python", "React", "AWS"],
                    "contributions": {
                        "documents_authored": 45,
                        "services_contributed": 12,
                        "years_experience": "7+ years"
                    },
                    "relevance_score": 0.88,
                    "sme_status": "✅ Qualified",
                    "reason": "Exceptional contribution count and strong expertise"
                }
            ],
            "identification_process": [
                "1. Query users by topic or role",
                "2. Fetch document counts for each user",
                "3. Filter by min_documents threshold (default: 10)",
                "4. Calculate relevance scores",
                "5. Filter by min_score threshold (default: 0.7)",
                "6. Return qualified SMEs with evidence"
            ],
            "insights": {
                "key_metric": "Document count is the primary indicator of SME status",
                "score_threshold": "0.7+ ensures high relevance to the query",
                "typical_sme_profile": "20+ documents, 0.8+ relevance score"
            }
        }
    
    async def _demo_ecosystem_expert_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Demo: Live Ecosystem Expert Search"""
        if not self.user_repo:
            return {
                "error": "This demo requires ecosystem dependencies",
                "required_services": ["user-store"],
                "status": "unavailable",
                "message": "Please ensure user-store service is running and accessible"
            }
        
        try:
            # Use FindExpertsUseCase with real data
            use_case = FindExpertsUseCase(
                user_repo=self.user_repo,
                doc_repo=self.doc_repo,
                service_repo=self.service_repo,
                scoring_service=self.scoring_service
            )
            
            query = ExpertQuery(
                query_text=params.get("query", "Python developer"),
                limit=params.get("limit", 5)
            )
            
            matches = await use_case.execute(query)
            
            return {
                "query": query.query_text,
                "source": "Live ecosystem data",
                "matches_found": len(matches),
                "results": [
                    {
                        "expert": {
                            "user_id": m.expert.user_id,
                            "name": m.expert.name,
                            "role": m.expert.role,
                            "topics": m.expert.topics[:5]
                        },
                        "overall_score": round(m.overall_score, 3),
                        "match_quality": m.match_quality()
                    }
                    for m in matches[:5]
                ]
            }
        except Exception as e:
            return {
                "error": "Ecosystem demo failed",
                "message": str(e),
                "status": "error"
            }
    
    async def _demo_ecosystem_sme_discovery(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Demo: Live Ecosystem SME Discovery"""
        if not self.user_repo:
            return {
                "error": "This demo requires ecosystem dependencies",
                "required_services": ["user-store", "doc-store"],
                "status": "unavailable",
                "message": "Please ensure required services are running"
            }
        
        try:
            # Use FindExpertsUseCase with SME-like criteria
            use_case = FindExpertsUseCase(
                user_repo=self.user_repo,
                doc_repo=self.doc_repo,
                service_repo=self.service_repo,
                scoring_service=self.scoring_service
            )
            
            # Create query with high thresholds to simulate SME discovery
            topic = params.get("topic", "Python")
            query = ExpertQuery(
                query_text=topic,
                topics=[topic],
                min_score=params.get("min_score", 0.7),
                limit=params.get("limit", 3)
            )
            
            matches = await use_case.execute(query)
            
            # Filter by document count (SME criterion)
            min_docs = params.get("min_documents", 10)
            smes = [m for m in matches if m.expert.document_count >= min_docs]
            
            return {
                "topic": topic,
                "criteria": {
                    "min_documents": min_docs,
                    "min_score": query.min_score
                },
                "source": "Live ecosystem data",
                "smes_found": len(smes),
                "results": [
                    {
                        "expert": {
                            "user_id": sme.expert.user_id,
                            "name": sme.expert.name,
                            "role": sme.expert.role,
                            "document_count": sme.expert.document_count
                        },
                        "overall_score": round(sme.overall_score, 3),
                        "match_quality": sme.match_quality()
                    }
                    for sme in smes[:3]
                ]
            }
        except Exception as e:
            return {
                "error": "Ecosystem demo failed",
                "message": str(e),
                "status": "error"
            }
    
    async def _demo_performance_benchmark(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Demo: Performance Benchmark"""
        from domain.entities.expert import Expert
        from domain.value_objects.expert_query import ExpertQuery
        import time
        
        query = ExpertQuery(
            query_text="Python backend developer",
            role="Backend Developer",
            topics=["Python"],
            limit=10
        )
        
        # Create sample experts of varying sizes
        dataset_sizes = [10, 50, 100, 500]
        results = []
        
        for size in dataset_sizes:
            # Generate sample experts
            experts = [
                Expert(
                    user_id=f"user_{i:03d}",
                    name=f"Test User {i}",
                    role="Backend Developer" if i % 2 == 0 else "Frontend Developer",
                    topics=["Python", "FastAPI"] if i % 3 == 0 else ["React", "TypeScript"],
                    services=[f"service_{i % 5}"],
                    document_count=i * 2,
                    service_count=i % 10
                )
                for i in range(size)
            ]
            
            # Benchmark scoring
            start = time.perf_counter()
            matches = [self.scoring_service.calculate_score(expert, query) for expert in experts]
            end = time.perf_counter()
            
            duration_ms = (end - start) * 1000
            
            results.append({
                "dataset_size": size,
                "duration_ms": round(duration_ms, 3),
                "experts_per_second": round(size / (duration_ms / 1000), 2),
                "matches_found": len([m for m in matches if m.overall_score > 0.3])
            })
        
        return {
            "benchmark": "Scoring Performance",
            "algorithm": "Multi-factor relevance scoring",
            "results": results,
            "insights": {
                "scalability": "Linear time complexity O(n) where n = number of candidates",
                "typical_performance": "Can score 1000+ experts per second",
                "optimization": "Batch processing and efficient scoring algorithms"
            }
        }

