"""Analysis result repository infrastructure."""

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from ...domain.entities.analysis_result import AnalysisResult


class AnalysisResultRepository(ABC):
    """Abstract base class for analysis result repositories.

    Defines the interface for analysis result persistence operations.
    """

    @abstractmethod
    async def save(self, analysis_result: AnalysisResult) -> None:
        """Save an analysis result."""
        pass

    @abstractmethod
    async def find_by_id(self, analysis_id: str) -> Optional[AnalysisResult]:
        """Find an analysis result by ID."""
        pass

    @abstractmethod
    async def find_by_source(self, source_type: str, source_id: str) -> List[AnalysisResult]:
        """Find analysis results by source."""
        pass

    @abstractmethod
    async def find_by_correlation_id(self, correlation_id: str) -> Optional[AnalysisResult]:
        """Find analysis result by correlation ID."""
        pass

    @abstractmethod
    async def find_recent(self, limit: int = 10) -> List[AnalysisResult]:
        """Find recent analysis results."""
        pass

    @abstractmethod
    async def search_by_quality_score(self, min_score: float, max_score: float) -> List[AnalysisResult]:
        """Search analysis results by quality score range."""
        pass

    @abstractmethod
    async def get_statistics_summary(self) -> Dict[str, Any]:
        """Get overall statistics summary."""
        pass

    @abstractmethod
    async def delete_old_results(self, days_old: int) -> int:
        """Delete analysis results older than specified days."""
        pass


class InMemoryAnalysisResultRepository(AnalysisResultRepository):
    """In-memory implementation of analysis result repository."""

    def __init__(self):
        """Initialize the in-memory repository."""
        self._results: Dict[str, AnalysisResult] = {}
        self._source_index: Dict[str, List[str]] = {}  # source_key -> [result_ids]
        self._correlation_index: Dict[str, str] = {}   # correlation_id -> result_id

    async def save(self, analysis_result: AnalysisResult) -> None:
        """Save an analysis result to memory."""
        self._results[analysis_result.id] = analysis_result

        # Update source index
        source_key = f"{analysis_result.source_type}:{analysis_result.title}"
        if source_key not in self._source_index:
            self._source_index[source_key] = []
        if analysis_result.id not in self._source_index[source_key]:
            self._source_index[source_key].append(analysis_result.id)

        # Update correlation index
        if analysis_result.correlation_id:
            self._correlation_index[analysis_result.correlation_id] = analysis_result.id

    async def find_by_id(self, analysis_id: str) -> Optional[AnalysisResult]:
        """Find an analysis result by ID."""
        return self._results.get(analysis_id)

    async def find_by_source(self, source_type: str, source_id: str) -> List[AnalysisResult]:
        """Find analysis results by source."""
        source_key = f"{source_type}:{source_id}"
        result_ids = self._source_index.get(source_key, [])
        return [self._results[result_id] for result_id in result_ids if result_id in self._results]

    async def find_by_correlation_id(self, correlation_id: str) -> Optional[AnalysisResult]:
        """Find analysis result by correlation ID."""
        result_id = self._correlation_index.get(correlation_id)
        if result_id:
            return self._results.get(result_id)
        return None

    async def find_recent(self, limit: int = 10) -> List[AnalysisResult]:
        """Find recent analysis results."""
        sorted_results = sorted(
            self._results.values(),
            key=lambda r: r.analysis_timestamp,
            reverse=True
        )
        return sorted_results[:limit]

    async def search_by_quality_score(self, min_score: float, max_score: float) -> List[AnalysisResult]:
        """Search analysis results by quality score range."""
        matching_results = [
            result for result in self._results.values()
            if min_score <= result.quality_score <= max_score
        ]
        return matching_results

    async def get_statistics_summary(self) -> Dict[str, Any]:
        """Get overall statistics summary."""
        if not self._results:
            return {
                "total_analyses": 0,
                "average_quality_score": 0.0,
                "total_security_issues": 0,
                "total_endpoints_found": 0
            }

        results_list = list(self._results.values())
        total_analyses = len(results_list)
        avg_quality_score = sum(r.quality_score for r in results_list) / total_analyses
        total_security_issues = sum(len(r.security_issues) for r in results_list)
        total_endpoints = sum(len(r.endpoints_found) for r in results_list)

        return {
            "total_analyses": total_analyses,
            "average_quality_score": round(avg_quality_score, 2),
            "total_security_issues": total_security_issues,
            "total_endpoints_found": total_endpoints,
            "sources_analyzed": len(set(f"{r.source_type}:{r.title}" for r in results_list))
        }

    async def delete_old_results(self, days_old: int) -> int:
        """Delete analysis results older than specified days."""
        from datetime import datetime, timezone, timedelta

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
        to_delete = [
            result_id for result_id, result in self._results.items()
            if result.analysis_timestamp < cutoff_date
        ]

        for result_id in to_delete:
            result = self._results[result_id]

            # Remove from indexes
            source_key = f"{result.source_type}:{result.title}"
            if source_key in self._source_index:
                self._source_index[source_key] = [
                    rid for rid in self._source_index[source_key] if rid != result_id
                ]

            if result.correlation_id in self._correlation_index:
                del self._correlation_index[result.correlation_id]

            del self._results[result_id]

        return len(to_delete)
