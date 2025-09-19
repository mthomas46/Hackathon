"""
Document Recommendation Service for high-level document analysis and recommendations.
Following DDD application layer patterns with clean separation of concerns.
"""

from typing import List, Dict, Any, Optional
import asyncio

from simulation.domain.recommendations.recommendation_engine import RecommendationEngine
from simulation.domain.recommendations.recommendation import Recommendation, RecommendationType
from simulation.infrastructure.recommendations.summarizer_hub_client import SummarizerHubClient


class DocumentRecommendationService:
    """High-level service for document analysis and recommendation generation."""

    def __init__(self):
        """Initialize the document recommendation service."""
        self.recommendation_engine = RecommendationEngine()
        self.summarizer_client = SummarizerHubClient()

    async def analyze_document_quality(self, document: Dict[str, Any]) -> float:
        """Analyze the quality of a single document."""
        try:
            # Use summarizer service for quality analysis
            analysis_result = await self.summarizer_client.analyze_document(document)
            return analysis_result.get("quality_score", 0.5)
        except Exception:
            # Fallback quality analysis
            content = document.get("content", "")
            word_count = len(content.split()) if content else 0

            quality_score = 0.5

            # Basic quality heuristics
            if word_count > 100:
                quality_score += 0.2
            if document.get("title"):
                quality_score += 0.1
            if "example" in content.lower() or "usage" in content.lower():
                quality_score += 0.1
            if len(content) > 500:
                quality_score += 0.1

            return max(0.0, min(1.0, quality_score))

    async def detect_similar_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect similar documents in a collection."""
        similar_pairs = []

        # Use recommendation engine for duplicate detection
        duplicate_recommendations = await self.recommendation_engine.generate_duplicate_recommendations(documents)

        for rec in duplicate_recommendations:
            if rec.affected_documents and len(rec.affected_documents) >= 2:
                similar_pairs.append({
                    "document1_id": rec.affected_documents[0],
                    "document2_id": rec.affected_documents[1],
                    "similarity_score": rec.confidence_score,
                    "recommendation": rec.description
                })

        return similar_pairs

    async def identify_content_gaps(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify gaps in documentation content."""
        gaps = []

        # Analyze document types and coverage
        doc_types = {}
        for doc in documents:
            doc_type = doc.get("type", "unknown")
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

        # Check for common documentation types that might be missing
        essential_types = {
            "api_documentation": "API documentation",
            "user_guide": "User guides and tutorials",
            "installation": "Installation and setup guides",
            "troubleshooting": "Troubleshooting and FAQ",
            "architecture": "System architecture documentation"
        }

        for doc_type, description in essential_types.items():
            if doc_type not in doc_types or doc_types[doc_type] == 0:
                gaps.append({
                    "topic": description,
                    "importance": "high",
                    "missing_content_type": doc_type,
                    "rationale": f"No {description.lower()} found in documentation set"
                })

        # Check for content depth issues
        total_docs = len(documents)
        if total_docs > 0:
            avg_word_count = sum(len(doc.get("content", "").split()) for doc in documents) / total_docs

            if avg_word_count < 200:
                gaps.append({
                    "topic": "Content depth and completeness",
                    "importance": "medium",
                    "missing_content_type": "detailed_content",
                    "rationale": f"Average document length ({avg_word_count:.0f} words) suggests superficial coverage"
                })

        return gaps

    async def generate_actionable_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on comprehensive analysis."""
        recommendations = []

        # Process quality scores
        quality_scores = analysis_results.get("quality_scores", {})
        low_quality_docs = [doc_id for doc_id, score in quality_scores.items() if score < 0.6]

        if low_quality_docs:
            recommendations.append({
                "action": f"Improve quality of {len(low_quality_docs)} low-quality documents",
                "rationale": "Low-quality documentation reduces user satisfaction and increases support burden",
                "expected_impact": "Enhanced user experience and reduced support tickets",
                "effort_level": "medium" if len(low_quality_docs) <= 3 else "high",
                "affected_documents": low_quality_docs,
                "priority": "high" if len(low_quality_docs) > 5 else "medium"
            })

        # Process similar documents
        similar_documents = analysis_results.get("similar_documents", [])
        if similar_documents:
            # Handle different possible formats for similar documents
            doc_ids = set()
            for pair in similar_documents:
                if "document1_id" in pair and "document2_id" in pair:
                    doc_ids.add(pair["document1_id"])
                    doc_ids.add(pair["document2_id"])
                elif "doc1" in pair and "doc2" in pair:
                    doc_ids.add(pair["doc1"])
                    doc_ids.add(pair["doc2"])

            consolidation_count = len(doc_ids)
            recommendations.append({
                "action": f"Consolidate {consolidation_count} redundant documents",
                "rationale": "Duplicate content increases maintenance overhead and confuses users",
                "expected_impact": "Simplified documentation structure and reduced maintenance costs",
                "effort_level": "medium",
                "affected_documents": list(doc_ids),
                "priority": "medium"
            })

        # Process content gaps
        content_gaps = analysis_results.get("content_gaps", [])
        for gap in content_gaps:
            if isinstance(gap, dict):
                # Gap is already a dictionary with detailed information
                recommendations.append({
                    "action": f"Create {gap.get('topic', str(gap))}",
                    "rationale": gap.get("rationale", "Fill documentation gap"),
                    "expected_impact": "Complete documentation coverage for better user experience",
                    "effort_level": "medium",
                    "priority": gap.get("importance", "medium"),
                    "content_type": gap.get("missing_content_type", "documentation")
                })
            else:
                # Gap is just a string identifier
                recommendations.append({
                    "action": f"Create documentation for {str(gap)}",
                    "rationale": f"Missing {str(gap)} documentation",
                    "expected_impact": "Complete documentation coverage for better user experience",
                    "effort_level": "medium",
                    "priority": "medium",
                    "content_type": str(gap)
                })

        return recommendations

    async def perform_comprehensive_analysis(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform comprehensive analysis of a document collection."""
        # Run multiple analysis tasks concurrently
        tasks = [
            self._analyze_quality_scores(documents),
            self.detect_similar_documents(documents),
            self.identify_content_gaps(documents),
            self.recommendation_engine.generate_comprehensive_recommendations(documents)
        ]

        results = await asyncio.gather(*tasks)

        quality_scores = results[0]
        similar_documents = results[1]
        content_gaps = results[2]
        recommendations = results[3]

        return {
            "quality_scores": quality_scores,
            "similar_documents": similar_documents,
            "content_gaps": content_gaps,
            "recommendations": [rec.to_dict() for rec in recommendations],
            "summary": {
                "total_documents": len(documents),
                "average_quality": sum(quality_scores.values()) / len(quality_scores) if quality_scores else 0,
                "duplicate_pairs": len(similar_documents),
                "content_gaps": len(content_gaps),
                "total_recommendations": len(recommendations)
            },
            "analyzed_at": asyncio.get_event_loop().time()
        }

    async def _analyze_quality_scores(self, documents: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze quality scores for all documents."""
        quality_scores = {}

        # Analyze documents in batches to avoid overwhelming the service
        batch_size = 5
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            # Analyze batch concurrently
            tasks = [self.analyze_document_quality(doc) for doc in batch]
            batch_scores = await asyncio.gather(*tasks)

            # Store results
            for doc, score in zip(batch, batch_scores):
                quality_scores[doc["id"]] = score

        return quality_scores
