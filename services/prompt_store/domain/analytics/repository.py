"""Analytics repository implementation.

Handles database operations for analytics and usage tracking entities.
"""

from typing import List, Optional, Dict, Any, Tuple
from services.prompt_store.core.entities import PromptUsage
from services.prompt_store.db.queries import execute_query, serialize_json, deserialize_json
from datetime import datetime, timezone, timedelta


class AnalyticsRepository:
    """Repository for analytics and usage tracking entities."""

    def __init__(self):
        self.usage_table = "prompt_usage"

    def _row_to_usage_entity(self, row: Dict[str, Any]) -> PromptUsage:
        """Convert database row to PromptUsage entity."""
        return PromptUsage(
            id=row["id"],
            prompt_id=row["prompt_id"],
            session_id=row["session_id"],
            user_id=row["user_id"],
            service_name=row["service_name"],
            operation=row["operation"],
            input_tokens=row["input_tokens"],
            output_tokens=row["output_tokens"],
            response_time_ms=row["response_time_ms"],
            success=row["success"],
            error_message=row["error_message"],
            metadata=deserialize_json(row["metadata"]),
            created_at=row["created_at"]
        )

    def save_usage(self, usage: PromptUsage) -> PromptUsage:
        """Save usage record to database."""
        row = {
            "id": usage.id,
            "prompt_id": usage.prompt_id,
            "session_id": usage.session_id,
            "user_id": usage.user_id,
            "service_name": usage.service_name,
            "operation": usage.operation,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "response_time_ms": usage.response_time_ms,
            "success": usage.success,
            "error_message": usage.error_message,
            "metadata": serialize_json(usage.metadata),
            "created_at": usage.created_at.isoformat()
        }

        columns = list(row.keys())
        placeholders = ",".join("?" * len(columns))
        values = [row[col] for col in columns]

        query = f"""
            INSERT INTO {self.usage_table}
            ({','.join(columns)})
            VALUES ({placeholders})
        """

        execute_query(query, values)
        return usage

    def get_usage_for_prompt(self, prompt_id: str, limit: int = 100) -> List[PromptUsage]:
        """Get usage records for a specific prompt."""
        query = f"SELECT * FROM {self.usage_table} WHERE prompt_id = ? ORDER BY created_at DESC LIMIT ?"
        rows = execute_query(query, (prompt_id, limit), fetch_all=True)
        return [self._row_to_usage_entity(row) for row in rows]

    def get_usage_in_date_range(self, start_date: datetime, end_date: datetime,
                               prompt_id: Optional[str] = None) -> List[PromptUsage]:
        """Get usage records within a date range."""
        params = [start_date.isoformat(), end_date.isoformat()]
        where_clause = "created_at BETWEEN ? AND ?"

        if prompt_id:
            where_clause += " AND prompt_id = ?"
            params.append(prompt_id)

        query = f"SELECT * FROM {self.usage_table} WHERE {where_clause} ORDER BY created_at DESC"
        rows = execute_query(query, tuple(params), fetch_all=True)
        return [self._row_to_usage_entity(row) for row in rows]

    def get_usage_stats(self, prompt_id: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get comprehensive usage statistics."""
        params = []
        where_conditions = []

        if prompt_id:
            where_conditions.append("prompt_id = ?")
            params.append(prompt_id)

        if start_date:
            where_conditions.append("created_at >= ?")
            params.append(start_date.isoformat())

        if end_date:
            where_conditions.append("created_at <= ?")
            params.append(end_date.isoformat())

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Basic counts
        count_query = f"SELECT COUNT(*) as total_requests FROM {self.usage_table} WHERE {where_clause}"
        count_result = execute_query(count_query, tuple(params), fetch_one=True)
        total_requests = count_result["total_requests"] if count_result else 0

        # Success rate
        success_query = f"SELECT COUNT(*) as success_count FROM {self.usage_table} WHERE {where_clause} AND success = 1"
        success_result = execute_query(success_query, tuple(params), fetch_one=True)
        success_count = success_result["success_count"] if success_result else 0
        success_rate = success_count / total_requests if total_requests > 0 else 0

        # Performance metrics
        perf_query = f"""
            SELECT
                AVG(response_time_ms) as avg_response_time,
                MIN(response_time_ms) as min_response_time,
                MAX(response_time_ms) as max_response_time,
                AVG(input_tokens) as avg_input_tokens,
                AVG(output_tokens) as avg_output_tokens,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens
            FROM {self.usage_table}
            WHERE {where_clause} AND response_time_ms IS NOT NULL
        """
        perf_result = execute_query(perf_query, tuple(params), fetch_one=True)

        # Error breakdown
        error_query = f"""
            SELECT error_message, COUNT(*) as count
            FROM {self.usage_table}
            WHERE {where_clause} AND success = 0 AND error_message IS NOT NULL
            GROUP BY error_message
            ORDER BY count DESC
            LIMIT 10
        """
        error_results = execute_query(error_query, tuple(params), fetch_all=True)

        # Service breakdown
        service_query = f"""
            SELECT service_name, COUNT(*) as count
            FROM {self.usage_table}
            WHERE {where_clause}
            GROUP BY service_name
            ORDER BY count DESC
        """
        service_results = execute_query(service_query, tuple(params), fetch_all=True)

        return {
            "total_requests": total_requests,
            "success_rate": success_rate,
            "success_count": success_count,
            "failure_count": total_requests - success_count,
            "performance": {
                "avg_response_time_ms": perf_result["avg_response_time"] if perf_result else None,
                "min_response_time_ms": perf_result["min_response_time"] if perf_result else None,
                "max_response_time_ms": perf_result["max_response_time"] if perf_result else None,
                "avg_input_tokens": perf_result["avg_input_tokens"] if perf_result else None,
                "avg_output_tokens": perf_result["avg_output_tokens"] if perf_result else None,
                "total_input_tokens": perf_result["total_input_tokens"] if perf_result else None,
                "total_output_tokens": perf_result["total_output_tokens"] if perf_result else None,
            },
            "errors": [{"error": row["error_message"], "count": row["count"]} for row in (error_results or [])],
            "services": [{"service": row["service_name"], "count": row["count"]} for row in (service_results or [])]
        }

    def get_prompt_performance_ranking(self, limit: int = 20,
                                      start_date: Optional[datetime] = None,
                                      end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get prompts ranked by performance metrics."""
        params = []
        date_conditions = []

        if start_date:
            date_conditions.append("u.created_at >= ?")
            params.append(start_date.isoformat())

        if end_date:
            date_conditions.append("u.created_at <= ?")
            params.append(end_date.isoformat())

        date_where = " AND ".join(date_conditions) if date_conditions else "1=1"

        query = f"""
            SELECT
                p.id,
                p.name,
                p.category,
                COUNT(u.id) as usage_count,
                AVG(u.response_time_ms) as avg_response_time,
                AVG(u.success) as success_rate,
                AVG(u.input_tokens + COALESCE(u.output_tokens, 0)) as avg_total_tokens,
                MAX(u.created_at) as last_used
            FROM prompts p
            LEFT JOIN prompt_usage u ON p.id = u.prompt_id AND {date_where}
            WHERE p.is_active = 1
            GROUP BY p.id, p.name, p.category
            HAVING usage_count > 0
            ORDER BY success_rate DESC, avg_response_time ASC
            LIMIT ?
        """
        params.append(limit)

        rows = execute_query(query, tuple(params), fetch_all=True)
        return [dict(row) for row in rows] if rows else []

    def get_usage_trends(self, days: int = 30, group_by: str = "day") -> List[Dict[str, Any]]:
        """Get usage trends over time."""
        interval_format = "%Y-%m-%d" if group_by == "day" else "%Y-%m"

        query = f"""
            SELECT
                strftime('{interval_format}', created_at) as period,
                COUNT(*) as total_requests,
                AVG(success) as success_rate,
                AVG(response_time_ms) as avg_response_time
            FROM {self.usage_table}
            WHERE created_at >= datetime('now', '-{days} days')
            GROUP BY period
            ORDER BY period ASC
        """

        rows = execute_query(query, fetch_all=True)
        return [dict(row) for row in rows] if rows else []

    def get_category_usage_stats(self) -> List[Dict[str, Any]]:
        """Get usage statistics by prompt category."""
        query = """
            SELECT
                p.category,
                COUNT(u.id) as usage_count,
                AVG(u.response_time_ms) as avg_response_time,
                AVG(u.success) as success_rate,
                COUNT(DISTINCT p.id) as unique_prompts
            FROM prompts p
            LEFT JOIN prompt_usage u ON p.id = u.prompt_id
            WHERE p.is_active = 1
            GROUP BY p.category
            ORDER BY usage_count DESC
        """

        rows = execute_query(query, fetch_all=True)
        return [dict(row) for row in rows] if rows else []

    def get_user_activity_stats(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most active users."""
        query = f"""
            SELECT
                user_id,
                COUNT(*) as total_requests,
                AVG(success) as success_rate,
                COUNT(DISTINCT prompt_id) as unique_prompts_used,
                MAX(created_at) as last_activity
            FROM {self.usage_table}
            WHERE user_id IS NOT NULL
            GROUP BY user_id
            ORDER BY total_requests DESC
            LIMIT ?
        """

        rows = execute_query(query, (limit,), fetch_all=True)
        return [dict(row) for row in rows] if rows else []

    def get_system_health_metrics(self) -> Dict[str, Any]:
        """Get system health metrics from usage data."""
        # Recent error rate (last hour)
        hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

        error_query = f"""
            SELECT
                COUNT(*) as total_recent,
                AVG(success) as recent_success_rate
            FROM {self.usage_table}
            WHERE created_at >= ?
        """

        error_result = execute_query(error_query, (hour_ago,), fetch_one=True)

        # Peak usage times
        peak_query = """
            SELECT
                strftime('%H', created_at) as hour,
                COUNT(*) as requests
            FROM prompt_usage
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY hour
            ORDER BY requests DESC
            LIMIT 5
        """

        peak_results = execute_query(peak_query, fetch_all=True)

        return {
            "recent_health": {
                "total_requests_last_hour": error_result["total_recent"] if error_result else 0,
                "success_rate_last_hour": error_result["recent_success_rate"] if error_result else 1.0
            },
            "peak_usage_hours": [{"hour": row["hour"], "requests": row["requests"]} for row in (peak_results or [])]
        }
