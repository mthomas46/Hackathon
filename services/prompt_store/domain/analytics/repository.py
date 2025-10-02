"""Analytics repository for data access operations."""

import json
from typing import Any, Dict, List, Optional

from services.shared.domain.repositories.base_repository import SqlRepository
from services.shared.infrastructure.utilities.utilities import validate_sql_identifier
from .entities import PromptPerformanceMetrics


class AnalyticsRepository(SqlRepository[PromptPerformanceMetrics]):
    """Repository for analytics data access."""

    def __init__(self, connection_string: str):
        from ...db.connection import get_prompt_store_connection_string

        super().__init__(
            PromptPerformanceMetrics,
            connection_string or get_prompt_store_connection_string(),
        )

        # Validate table name to prevent SQL injection
        if not validate_sql_identifier(self.table_name):
            raise ValueError(f"Invalid table name: {self.table_name}")

    def _dict_to_entity(self, data: Dict[str, Any]) -> PromptPerformanceMetrics:
        """Convert database row to PromptPerformanceMetrics entity."""
        return PromptPerformanceMetrics.from_dict(data)

    def get_all(self, limit: int = 50, offset: int = 0, **filters) -> Dict[str, Any]:
        """Get all entities with pagination and filters."""
        where_clause = ""
        params = []

        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            where_clause = f"WHERE {' AND '.join(conditions)}"

        rows = execute_query(
            f"SELECT * FROM {self.table_name} {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
            fetch_all=True,
        )

        entities = [self._row_to_entity(row) for row in rows]

        # Get total count
        count_result = execute_query(
            f"SELECT COUNT(*) as count FROM {self.table_name} {where_clause}",
            params,
            fetch_one=True,
        )
        total_count = count_result["count"] if count_result else 0

        return {
            "items": entities,
            "total": total_count,
            "limit": limit,
            "offset": offset,
        }

    def count(self, **filters) -> int:
        """Count entities with filters."""
        where_clause = ""
        params = []

        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            where_clause = f"WHERE {' AND '.join(conditions)}"

        result = execute_query(
            f"SELECT COUNT(*) as count FROM {self.table_name} {where_clause}",
            params,
            fetch_one=True,
        )
        return result["count"] if result else 0

    def _row_to_entity(self, row: Dict[str, Any]) -> PromptPerformanceMetrics:
        """Convert database row to entity."""
        from datetime import datetime

        return PromptPerformanceMetrics(
            id=row["id"],
            prompt_id=row["prompt_id"],
            version=row["version"],
            total_requests=row["total_requests"],
            successful_requests=row["successful_requests"],
            failed_requests=row["failed_requests"],
            average_response_time_ms=row["average_response_time_ms"],
            median_response_time_ms=row["median_response_time_ms"],
            p95_response_time_ms=row["p95_response_time_ms"],
            p99_response_time_ms=row["p99_response_time_ms"],
            total_tokens_used=row["total_tokens_used"],
            average_tokens_per_request=row["average_tokens_per_request"],
            cost_estimate_usd=row["cost_estimate_usd"],
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
            updated_at=(
                datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00"))
                if row.get("updated_at")
                else None
            ),
        )

    def _entity_to_row(self, entity: PromptPerformanceMetrics) -> Dict[str, Any]:
        """Convert entity to database row."""
        return {
            "id": entity.id,
            "prompt_id": entity.prompt_id,
            "version": entity.version,
            "total_requests": entity.total_requests,
            "successful_requests": entity.successful_requests,
            "failed_requests": entity.failed_requests,
            "average_response_time_ms": entity.average_response_time_ms,
            "median_response_time_ms": entity.median_response_time_ms,
            "p95_response_time_ms": entity.p95_response_time_ms,
            "p99_response_time_ms": entity.p99_response_time_ms,
            "total_tokens_used": entity.total_tokens_used,
            "average_tokens_per_request": entity.average_tokens_per_request,
            "cost_estimate_usd": entity.cost_estimate_usd,
            "created_at": entity.created_at.isoformat(),
            "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
        }

    def get_metrics_by_prompt_version(
        self, prompt_id: str, version: int
    ) -> Optional[PromptPerformanceMetrics]:
        """Get metrics for a specific prompt version."""
        row = execute_query(
            "SELECT * FROM prompt_performance_metrics WHERE prompt_id = ? AND version = ?",
            (prompt_id, version),
            fetch_one=True,
        )
        return self._row_to_entity(row) if row else None

    def get_all_prompts(self) -> List[Dict[str, Any]]:
        """Get all prompts (for summary stats)."""
        # This would typically query the prompts table
        # For now, return mock data
        return []

    def get_total_requests(self, days: int) -> int:
        """Get total requests in the last N days."""
        # Simplified implementation
        return 0

    def get_active_prompts_count(self) -> int:
        """Get count of active prompts."""
        return 0

    def get_top_performing_prompts(self, days: int, limit: int) -> List[Dict[str, Any]]:
        """Get top performing prompts by success rate."""
        return []

    def get_average_response_time(self, days: int) -> float:
        """Get average response time."""
        return 0.0

    def get_usage_by_day(self, days: int) -> List[Dict[str, Any]]:
        """Get usage statistics by day."""
        return []

    def get_most_used_prompts(self, days: int, limit: int) -> List[Dict[str, Any]]:
        """Get most used prompts."""
        return []

    # User satisfaction methods
    def create_satisfaction_score(self, score_data: Dict[str, Any]) -> None:
        """Create a user satisfaction score record."""
        execute_query(
            """
            INSERT INTO user_satisfaction_scores
            (id, prompt_id, user_id, session_id, rating, feedback_text, context_tags, use_case_category, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                score_data["id"],
                score_data["prompt_id"],
                score_data["user_id"],
                score_data["session_id"],
                score_data["rating"],
                score_data["feedback_text"],
                json.dumps(score_data["context_tags"]),
                score_data["use_case_category"],
                score_data["created_at"],
            ),
        )

    def get_recent_satisfaction_scores(self, days: int) -> List[Dict[str, Any]]:
        """Get recent satisfaction scores."""
        return execute_query(
            """
            SELECT * FROM user_satisfaction_scores
            WHERE created_at >= datetime('now', '-{} days')
            ORDER BY created_at DESC
        """.format(
                days
            ),
            fetch_all=True,
        )
