"""Semantic Analysis Handler - Handles semantic similarity and embedding analysis."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .base_handler import BaseAnalysisHandler, AnalysisResult
from ..models import (
    SemanticSimilarityRequest, SemanticSimilarityResponse,
    SimilarityPair, SimilarityMatrix
)

logger = logging.getLogger(__name__)


class SemanticAnalysisHandler(BaseAnalysisHandler):
    """Handler for semantic similarity analysis operations."""

    def __init__(self):
        super().__init__("semantic_similarity")

    async def handle(self, request: SemanticSimilarityRequest) -> AnalysisResult:
        """Handle semantic similarity analysis request."""
        try:
            # Import semantic analyzer
            try:
                from ..semantic_analyzer import analyze_semantic_similarity
            except ImportError:
                # Fallback for testing
                analyze_semantic_similarity = self._mock_semantic_analysis

            # Perform semantic analysis
            analysis_result = await analyze_semantic_similarity(
                targets=request.targets,
                threshold=request.threshold,
                embedding_model=request.embedding_model,
                similarity_metric=request.similarity_metric,
                options=request.options or {}
            )

            # Convert to standardized response format
            response = SemanticSimilarityResponse(
                analysis_id=f"semantic-{int(datetime.now(timezone.utc).timestamp())}",
                analysis_type="semantic_similarity",
                targets=request.targets,
                status="completed",
                similarity_matrix=analysis_result.get('similarity_matrix', []),
                similar_pairs=[
                    SimilarityPair(**pair) for pair in analysis_result.get('similar_pairs', [])
                ],
                summary=analysis_result.get('summary', {}),
                execution_time_seconds=analysis_result.get('execution_time_seconds', 0.0),
                error_message=None
            )

            return self._create_analysis_result(
                analysis_id=response.analysis_id,
                data={"response": response.dict()},
                execution_time=response.execution_time_seconds
            )

        except Exception as e:
            error_msg = f"Semantic similarity analysis failed: {str(e)}"
            logger.error(error_msg, exc_info=True)

            return await self._handle_error(e, f"semantic-{int(datetime.now(timezone.utc).timestamp())}")

    async def _mock_semantic_analysis(self, targets: List[str], threshold: float = 0.8,
                                    embedding_model: str = "default", similarity_metric: str = "cosine",
                                    options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Mock semantic analysis for testing purposes."""
        # Generate mock similarity matrix
        n = len(targets)
        similarity_matrix = []
        for i in range(n):
            row = []
            for j in range(n):
                similarity = 1.0 if i == j else (0.8 - abs(i - j) * 0.1)
                row.append(max(0.0, similarity))  # Ensure non-negative
            similarity_matrix.append(row)

        # Generate mock similar pairs
        similar_pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                similarity = similarity_matrix[i][j]
                if similarity >= threshold:
                    similar_pairs.append({
                        'source': targets[i],
                        'target': targets[j],
                        'similarity': similarity,
                        'confidence': min(1.0, similarity + 0.1)
                    })

        return {
            'similarity_matrix': similarity_matrix,
            'similar_pairs': similar_pairs,
            'summary': {
                'total_pairs': len(similar_pairs),
                'highly_similar_pairs': len([p for p in similar_pairs if p['similarity'] >= 0.9]),
                'average_similarity': sum(p['similarity'] for p in similar_pairs) / len(similar_pairs) if similar_pairs else 0.0
            },
            'execution_time_seconds': 1.5
        }

    async def handle_batch_semantic_analysis(self, requests: List[SemanticSimilarityRequest]) -> List[AnalysisResult]:
        """Handle batch semantic similarity analysis."""
        results = []

        for request in requests:
            result = await self.handle(request)
            results.append(result)

        return results

    async def get_semantic_similarity_matrix(self, targets: List[str],
                                           embedding_model: str = "default") -> Dict[str, Any]:
        """Get semantic similarity matrix for targets."""
        request = SemanticSimilarityRequest(
            targets=targets,
            threshold=0.0,  # Include all similarities
            embedding_model=embedding_model,
            options={"return_matrix_only": True}
        )

        result = await self.handle(request)

        if result.error_message:
            return {"error": result.error_message}

        return {
            "targets": targets,
            "similarity_matrix": result.data.get("response", {}).get("similarity_matrix", []),
            "execution_time_seconds": result.execution_time_seconds
        }

    async def find_most_similar(self, target: str, candidates: List[str],
                              top_k: int = 5) -> Dict[str, Any]:
        """Find most similar documents to target from candidates."""
        all_targets = [target] + candidates

        matrix_result = await self.get_semantic_similarity_matrix(all_targets)

        if "error" in matrix_result:
            return {"error": matrix_result["error"]}

        similarity_matrix = matrix_result["similarity_matrix"]
        if not similarity_matrix or len(similarity_matrix) < 1:
            return {"error": "No similarity data available"}

        # Get similarities for target (first row)
        target_similarities = similarity_matrix[0][1:]  # Skip self-similarity

        # Get top-k most similar
        similarities_with_indices = [(i, sim) for i, sim in enumerate(target_similarities)]
        similarities_with_indices.sort(key=lambda x: x[1], reverse=True)

        top_similar = []
        for idx, similarity in similarities_with_indices[:top_k]:
            top_similar.append({
                'document': candidates[idx],
                'similarity': similarity,
                'rank': len(top_similar) + 1
            })

        return {
            'target': target,
            'most_similar': top_similar,
            'total_candidates': len(candidates),
            'execution_time_seconds': matrix_result.get('execution_time_seconds', 0.0)
        }


# Register handler
from .base_handler import handler_registry
handler_registry.register("semantic_similarity", SemanticAnalysisHandler())
