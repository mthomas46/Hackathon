"""A/B testing repository implementation.

Handles database operations for A/B testing entities.
"""

from typing import List, Optional, Dict, Any, Tuple
from services.prompt_store.core.repository import BaseRepository
from services.prompt_store.core.entities import ABTest, ABTestResult
from services.prompt_store.db.queries import execute_query, serialize_json, deserialize_json


class ABTestRepository(BaseRepository[ABTest]):
    """Repository for A/B test entities."""

    def __init__(self):
        super().__init__("ab_tests")

    def _row_to_entity(self, row: Dict[str, Any]) -> ABTest:
        """Convert database row to ABTest entity."""
        return ABTest.from_dict({
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "prompt_a_id": row["prompt_a_id"],
            "prompt_b_id": row["prompt_b_id"],
            "test_metric": row["test_metric"],
            "is_active": row["is_active"],
            "traffic_split": row["traffic_split"],
            "start_date": row["start_date"],
            "end_date": row["end_date"],
            "target_audience": deserialize_json(row["target_audience"]),
            "created_by": row["created_by"],
            "winner": row["winner"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        })

    def _entity_to_row(self, entity: ABTest) -> Dict[str, Any]:
        """Convert ABTest entity to database row."""
        return {
            "id": entity.id,
            "name": entity.name,
            "description": entity.description,
            "prompt_a_id": entity.prompt_a_id,
            "prompt_b_id": entity.prompt_b_id,
            "test_metric": entity.test_metric,
            "is_active": entity.is_active,
            "traffic_split": entity.traffic_split,
            "start_date": entity.start_date.isoformat(),
            "end_date": entity.end_date.isoformat() if entity.end_date else None,
            "target_audience": serialize_json(entity.target_audience),
            "created_by": entity.created_by,
            "winner": entity.winner,
            "created_at": entity.created_at.isoformat(),
            "updated_at": entity.updated_at.isoformat()
        }

    def save(self, entity: ABTest) -> ABTest:
        """Save A/B test to database."""
        row = self._entity_to_row(entity)
        columns = list(row.keys())
        placeholders = ",".join("?" * len(columns))
        values = [row[col] for col in columns]

        query = f"""
            INSERT OR REPLACE INTO {self.table_name}
            ({','.join(columns)})
            VALUES ({placeholders})
        """

        execute_query(query, values)
        return entity

    def get_by_id(self, entity_id: str) -> Optional[ABTest]:
        """Get A/B test by ID."""
        query = f"SELECT * FROM {self.table_name} WHERE id = ?"
        row = execute_query(query, (entity_id,), fetch_one=True)
        return self._row_to_entity(row) if row else None

    def get_all(self, limit: int = 50, offset: int = 0, **filters) -> Dict[str, Any]:
        """Get all A/B tests with pagination and filtering."""
        from services.prompt_store.db.queries import execute_paged_query
        return execute_paged_query(self.table_name, filters, limit=limit, offset=offset)

    def update(self, entity_id: str, updates: Dict[str, Any]) -> Optional[ABTest]:
        """Update A/B test."""
        if not updates:
            return self.get_by_id(entity_id)

        # Build update query
        set_parts = []
        values = []
        for key, value in updates.items():
            if key in ["target_audience"]:  # JSON fields
                set_parts.append(f"{key} = ?")
                values.append(serialize_json(value))
            else:
                set_parts.append(f"{key} = ?")
                values.append(value)

        values.append(entity_id)  # For WHERE clause

        query = f"""
            UPDATE {self.table_name}
            SET {', '.join(set_parts)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        execute_query(query, values)
        return self.get_by_id(entity_id)

    def delete(self, entity_id: str) -> bool:
        """Delete A/B test."""
        query = f"DELETE FROM {self.table_name} WHERE id = ?"
        execute_query(query, (entity_id,))
        return True

    def exists(self, entity_id: str) -> bool:
        """Check if A/B test exists."""
        query = f"SELECT 1 FROM {self.table_name} WHERE id = ?"
        row = execute_query(query, (entity_id,), fetch_one=True)
        return row is not None

    def count(self, **filters) -> int:
        """Count A/B tests matching filters."""
        where_clause = ""
        params = []

        if filters:
            conditions = []
            for key, value in filters.items():
                if key == "is_active":
                    conditions.append("is_active = ?")
                    params.append(value)
                elif key == "created_by":
                    conditions.append("created_by = ?")
                    params.append(value)

            if conditions:
                where_clause = f"WHERE {' AND '.join(conditions)}"

        query = f"SELECT COUNT(*) as count FROM {self.table_name} {where_clause}"
        result = execute_query(query, tuple(params), fetch_one=True)
        return result["count"] if result else 0

    def get_active_tests(self) -> List[ABTest]:
        """Get all active A/B tests."""
        query = f"SELECT * FROM {self.table_name} WHERE is_active = 1 ORDER BY created_at DESC"
        rows = execute_query(query, fetch_all=True)
        return [self._row_to_entity(row) for row in rows]

    def get_tests_by_prompt(self, prompt_id: str) -> List[ABTest]:
        """Get A/B tests that include a specific prompt."""
        query = f"SELECT * FROM {self.table_name} WHERE prompt_a_id = ? OR prompt_b_id = ? ORDER BY created_at DESC"
        rows = execute_query(query, (prompt_id, prompt_id), fetch_all=True)
        return [self._row_to_entity(row) for row in rows]

    def select_prompt_for_test(self, test_id: str, user_id: Optional[str] = None) -> Optional[str]:
        """Select a prompt variant for A/B testing using consistent hashing."""
        test = self.get_by_id(test_id)
        if not test or not test.is_active:
            return None

        # Use user_id for consistent assignment, fallback to random
        import hashlib
        import random

        if user_id:
            # Consistent hashing based on user_id
            hash_value = int(hashlib.md5(f"{test_id}:{user_id}".encode()).hexdigest(), 16)
            # Normalize to 0-1 range
            normalized = (hash_value % 1000) / 1000.0
            selected = "A" if normalized < test.traffic_split else "B"
        else:
            # Random selection
            selected = "A" if random.random() < test.traffic_split else "B"

        return test.prompt_a_id if selected == "A" else test.prompt_b_id

    def create_ab_test(self, test_data: Dict[str, Any]) -> ABTest:
        """Create a new A/B test."""
        from services.prompt_store.core.entities import ABTest
        import uuid

        # Create ABTest entity
        ab_test = ABTest(
            name=test_data["name"],
            description=test_data.get("description", ""),
            prompt_a_id=test_data["prompt_a_id"],
            prompt_b_id=test_data["prompt_b_id"],
            test_metric=test_data.get("test_metric", "response_quality"),
            is_active=test_data.get("is_active", True),
            traffic_split=test_data.get("traffic_percentage", 50) / 100.0,  # Convert percentage to decimal
            target_audience=test_data.get("target_audience", {}),
            created_by=test_data["created_by"],
            status=test_data.get("status", "active"),
            traffic_percentage=test_data.get("traffic_percentage", 50)
        )

        # Set ID if not provided
        if not ab_test.id:
            ab_test.id = str(uuid.uuid4())

        # Save to database
        return self.save(ab_test)

    def get_ab_test(self, test_id: str) -> Optional[ABTest]:
        """Get A/B test by ID (alias for get_by_id)."""
        return self.get_by_id(test_id)

    def record_test_result(self, test_id: str, prompt_id: str, metric_value: float,
                          sample_size: int = 1, session_id: Optional[str] = None) -> ABTestResult:
        """Record a test result for an A/B test."""
        from services.prompt_store.core.entities import ABTestResult
        import uuid

        result = ABTestResult(
            test_id=test_id,
            prompt_id=prompt_id,
            metric_value=metric_value,
            sample_size=sample_size,
            confidence_level=0.0,  # Will be calculated later
            statistical_significance=False  # Will be calculated later
        )

        # Set ID if not provided
        if not result.id:
            result.id = str(uuid.uuid4())

        # Save to database
        result_repo = ABTestResultRepository()
        return result_repo.save(result)


class ABTestResultRepository:
    """Repository for A/B test result entities."""

    def __init__(self):
        self.table_name = "ab_test_results"

    def _row_to_entity(self, row: Dict[str, Any]) -> ABTestResult:
        """Convert database row to ABTestResult entity."""
        return ABTestResult(
            id=row["id"],
            test_id=row["test_id"],
            prompt_id=row["prompt_id"],
            metric_value=row["metric_value"],
            sample_size=row["sample_size"],
            confidence_level=row["confidence_level"],
            statistical_significance=row["statistical_significance"],
            recorded_at=row["recorded_at"]
        )

    def save(self, entity: ABTestResult) -> ABTestResult:
        """Save A/B test result to database."""
        row = {
            "id": entity.id,
            "test_id": entity.test_id,
            "prompt_id": entity.prompt_id,
            "metric_value": entity.metric_value,
            "sample_size": entity.sample_size,
            "confidence_level": entity.confidence_level,
            "statistical_significance": entity.statistical_significance,
            "recorded_at": entity.recorded_at.isoformat()
        }

        columns = list(row.keys())
        placeholders = ",".join("?" * len(columns))
        values = [row[col] for col in columns]

        query = f"""
            INSERT OR REPLACE INTO {self.table_name}
            ({','.join(columns)})
            VALUES ({placeholders})
        """

        execute_query(query, values)
        return entity

    def get_results_for_test(self, test_id: str) -> List[ABTestResult]:
        """Get all results for a specific test."""
        query = f"SELECT * FROM {self.table_name} WHERE test_id = ? ORDER BY recorded_at DESC"
        rows = execute_query(query, (test_id,), fetch_all=True)
        return [self._row_to_entity(row) for row in rows]

    def get_latest_results(self, test_id: str, limit: int = 10) -> List[ABTestResult]:
        """Get latest results for a test."""
        query = f"SELECT * FROM {self.table_name} WHERE test_id = ? ORDER BY recorded_at DESC LIMIT ?"
        rows = execute_query(query, (test_id, limit), fetch_all=True)
        return [self._row_to_entity(row) for row in rows]

    def get_aggregated_results(self, test_id: str) -> Dict[str, Any]:
        """Get aggregated results for a test."""
        query = f"""
            SELECT
                prompt_id,
                AVG(metric_value) as avg_metric,
                SUM(sample_size) as total_samples,
                COUNT(*) as result_count,
                AVG(confidence_level) as avg_confidence,
                MAX(statistical_significance) as has_significance
            FROM {self.table_name}
            WHERE test_id = ?
            GROUP BY prompt_id
        """
        rows = execute_query(query, (test_id,), fetch_all=True)

        results = {}
        for row in rows:
            results[row["prompt_id"]] = {
                "average_metric": row["avg_metric"],
                "total_samples": row["total_samples"],
                "result_count": row["result_count"],
                "average_confidence": row["avg_confidence"],
                "has_statistical_significance": bool(row["has_significance"])
            }

        return results
