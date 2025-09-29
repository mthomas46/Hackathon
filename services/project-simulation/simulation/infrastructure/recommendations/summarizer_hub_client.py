"""
Summarizer-Hub Client for integrating with the summarizer service.
Following DDD infrastructure patterns with clean separation of concerns.
"""

import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime

from simulation.application.analysis.simulation_analyzer import SimulationAnalyzer
from simulation.domain.recommendations.recommendation import Recommendation, RecommendationType


class SummarizerHubClient:
    """Client for communicating with the Summarizer-Hub service for recommendations."""

    def __init__(self, http_client: Optional[httpx.AsyncClient] = None):
        """Initialize the Summarizer-Hub client."""
        self.http_client = http_client or httpx.AsyncClient(timeout=30.0)
        self._analyzer = SimulationAnalyzer()
        self.service_url = self._get_service_url()

    def _get_service_url(self) -> str:
        """Get the appropriate Summarizer-Hub service URL."""
        # Use the same environment detection logic as the analyzer
        return self._analyzer.service_urls.get("summarizer_hub", "http://localhost:5160")

    async def analyze_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single document using the summarizer-hub service."""
        try:
            analysis_request = {
                "content": document.get("content", ""),
                "title": document.get("title", ""),
                "document_type": document.get("type", "unknown"),
                "analysis_type": "comprehensive"
            }

            response = await self.http_client.post(
                f"{self.service_url}/api/v1/analyze/document",
                json=analysis_request,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                return response.json()
            else:
                # Fallback to basic analysis
                return await self._fallback_document_analysis(document)

        except Exception as e:
            # Service unavailable - return fallback analysis
            return await self._fallback_document_analysis(document)

    async def analyze_documents_batch(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze multiple documents in batch."""
        results = []

        # Limit batch size to avoid overwhelming the service
        batch_size = min(len(documents), 10)

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            try:
                batch_request = {
                    "documents": [
                        {
                            "id": doc.get("id"),
                            "content": doc.get("content", ""),
                            "title": doc.get("title", ""),
                            "type": doc.get("type", "unknown")
                        }
                        for doc in batch
                    ],
                    "analysis_type": "batch_quality"
                }

                response = await self.http_client.post(
                    f"{self.service_url}/api/v1/analyze/batch",
                    json=batch_request,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    batch_results = response.json()
                    results.extend(batch_results.get("results", []))
                else:
                    # Fallback analysis for batch
                    for doc in batch:
                        fallback_result = await self._fallback_document_analysis(doc)
                        results.append({
                            "document_id": doc.get("id"),
                            "analysis": fallback_result,
                            "fallback": True
                        })

            except Exception:
                # Fallback for entire batch
                for doc in batch:
                    fallback_result = await self._fallback_document_analysis(doc)
                    results.append({
                        "document_id": doc.get("id"),
                        "analysis": fallback_result,
                        "fallback": True
                    })

        return results

    async def generate_recommendations(self, analysis_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations based on analysis results."""
        try:
            recommendation_request = {
                "analysis_results": analysis_results,
                "recommendation_types": ["consolidation", "quality", "structure"],
                "include_priorities": True
            }

            response = await self.http_client.post(
                f"{self.service_url}/api/v1/recommendations/generate",
                json=recommendation_request,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                return response.json().get("recommendations", [])
            else:
                # Fallback recommendation generation
                return await self._fallback_recommendation_generation(analysis_results)

        except Exception:
            # Service unavailable - return fallback recommendations
            return await self._fallback_recommendation_generation(analysis_results)

    async def get_fallback_analysis(self) -> Dict[str, Any]:
        """Provide fallback analysis when service is unavailable."""
        return {
            "fallback_mode": True,
            "analysis_type": "basic_fallback",
            "summary": "Service temporarily unavailable - using basic analysis",
            "quality_score": 0.5,
            "recommendations": [
                {
                    "type": "service_unavailable",
                    "description": "Summarizer service is currently unavailable",
                    "priority": "medium"
                }
            ],
            "generated_at": datetime.now().isoformat()
        }

    async def _fallback_document_analysis(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Provide basic fallback analysis for a document."""
        content = document.get("content", "")
        word_count = len(content.split()) if content else 0

        # Basic quality assessment
        quality_score = 0.5  # Neutral starting point

        if word_count > 100:
            quality_score += 0.2
        elif word_count < 20:
            quality_score -= 0.3

        if document.get("title"):
            quality_score += 0.1

        if "example" in content.lower():
            quality_score += 0.1

        quality_score = max(0.0, min(1.0, quality_score))

        return {
            "document_id": document.get("id"),
            "summary": f"Basic analysis of '{document.get('title', 'Unknown')}'",
            "word_count": word_count,
            "quality_score": quality_score,
            "key_points": ["Content length analysis", "Basic quality assessment"],
            "sentiment": "neutral",
            "fallback_mode": True,
            "analyzed_at": datetime.now().isoformat()
        }

    async def _fallback_recommendation_generation(self, analysis_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate basic fallback recommendations."""
        recommendations = []

        for result in analysis_results:
            doc_id = result.get("document_id")
            quality_score = result.get("quality_score", 0.5)

            if quality_score < 0.6:
                recommendations.append({
                    "type": "quality",
                    "description": f"Consider improving quality of document {doc_id}",
                    "priority": "medium",
                    "document_id": doc_id,
                    "fallback": True
                })

        # Add general recommendations if we have multiple low-quality documents
        low_quality_count = sum(1 for r in analysis_results if r.get("quality_score", 0.5) < 0.6)

        if low_quality_count > len(analysis_results) * 0.5:
            recommendations.append({
                "type": "consolidation",
                "description": "Consider consolidating multiple low-quality documents",
                "priority": "high",
                "fallback": True
            })

        return recommendations

    async def get_recommendations(self, documents: List[Dict[str, Any]], recommendation_types: Optional[List[str]] = None, confidence_threshold: float = 0.4) -> List[Recommendation]:
        """Get recommendations for documents from Summarizer Hub."""
        try:
            async with httpx.AsyncClient(timeout=self.http_client.timeout) as client:
                response = await client.post(
                    f"{self.service_url}/api/v1/recommendations",
                    json={
                        "documents": documents,
                        "recommendation_types": recommendation_types,
                        "confidence_threshold": confidence_threshold
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        return self._parse_recommendations(result["recommendations"])
                    else:
                        print(f"Summarizer Hub error: {result.get('error', 'Unknown error')}")
                        return []
                else:
                    print(f"Summarizer Hub request failed with status {response.status_code}")
                    return []

        except Exception as e:
            print(f"Error communicating with Summarizer Hub: {e}")
            return []

    async def get_consolidation_recommendations(self, documents: List[Dict[str, Any]]) -> List[Recommendation]:
        """Get consolidation recommendations specifically."""
        return await self.get_recommendations(documents, ["consolidation"])

    async def get_duplicate_recommendations(self, documents: List[Dict[str, Any]]) -> List[Recommendation]:
        """Get duplicate detection recommendations specifically."""
        return await self.get_recommendations(documents, ["duplicate"])

    async def get_outdated_recommendations(self, documents: List[Dict[str, Any]]) -> List[Recommendation]:
        """Get outdated document recommendations specifically."""
        return await self.get_recommendations(documents, ["outdated"])

    async def get_quality_recommendations(self, documents: List[Dict[str, Any]]) -> List[Recommendation]:
        """Get quality improvement recommendations specifically."""
        return await self.get_recommendations(documents, ["quality"])

    async def get_comprehensive_recommendations(self, documents: List[Dict[str, Any]]) -> List[Recommendation]:
        """Get comprehensive recommendations across all types."""
        return await self.get_recommendations(documents, ["consolidation", "duplicate", "outdated", "quality"])

    def _parse_recommendations(self, raw_recommendations: List[Dict[str, Any]]) -> List[Recommendation]:
        """Parse raw recommendations into Recommendation objects."""
        recommendations = []

        for raw_rec in raw_recommendations:
            try:
                # Map string types to RecommendationType enum
                rec_type_str = raw_rec.get("type", "")
                if rec_type_str == "consolidation":
                    rec_type = RecommendationType.CONSOLIDATION
                elif rec_type_str == "duplicate":
                    rec_type = RecommendationType.DUPLICATE
                elif rec_type_str == "outdated":
                    rec_type = RecommendationType.OUTDATED
                elif rec_type_str == "quality":
                    rec_type = RecommendationType.QUALITY
                else:
                    continue  # Skip unknown types

                recommendation = Recommendation(
                    type=rec_type,
                    description=raw_rec.get("description", ""),
                    affected_documents=raw_rec.get("affected_documents", []),
                    confidence_score=raw_rec.get("confidence_score", 0.0),
                    priority=raw_rec.get("priority", "medium"),
                    rationale=raw_rec.get("rationale", ""),
                    expected_impact=raw_rec.get("expected_impact", ""),
                    effort_level=raw_rec.get("effort_level", "medium"),
                    tags=raw_rec.get("tags", []),
                    metadata=raw_rec.get("metadata", {}),
                    age_days=raw_rec.get("age_days")
                )
                recommendations.append(recommendation)

            except Exception as e:
                print(f"Error parsing recommendation: {e}")
                continue

        return recommendations

    async def get_health_status(self) -> Dict[str, Any]:
        """Check the health status of the Summarizer Hub service."""
        try:
            async with httpx.AsyncClient(timeout=self.http_client.timeout) as client:
                response = await client.get(f"{self.service_url}/health")
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}

    async def get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of the Summarizer Hub service."""
        try:
            async with httpx.AsyncClient(timeout=self.http_client.timeout) as client:
                response = await client.get(f"{self.service_url}/capabilities")
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
