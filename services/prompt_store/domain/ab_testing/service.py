"""A/B testing service implementation.

Handles business logic for A/B testing operations.
"""

import asyncio
import statistics
from typing import List, Optional, Dict, Any, Tuple
from services.prompt_store.core.service import BaseService
from services.prompt_store.core.entities import ABTest, ABTestResult, Prompt
from services.prompt_store.domain.ab_testing.repository import ABTestRepository, ABTestResultRepository
from services.prompt_store.domain.prompts.service import PromptService
from services.prompt_store.infrastructure.cache import prompt_store_cache
from services.shared.utilities import generate_id, utc_now


class ABTestService(BaseService[ABTest]):
    """Service for A/B testing business logic."""

    def __init__(self):
        super().__init__(ABTestRepository())
        self.result_repository = ABTestResultRepository()
        self.prompt_service = PromptService()

    def create_entity(self, data: Dict[str, Any], entity_id: Optional[str] = None) -> ABTest:
        """Create a new A/B test with validation."""
        # Validate required fields
        required_fields = ["name", "prompt_a_id", "prompt_b_id"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        # Validate prompts exist and are different
        prompt_a = self.prompt_service.get_entity(data["prompt_a_id"])
        prompt_b = self.prompt_service.get_entity(data["prompt_b_id"])

        if not prompt_a or not prompt_b:
            raise ValueError("Both prompts must exist")

        if prompt_a.id == prompt_b.id:
            raise ValueError("Prompt A and Prompt B must be different")

        # Validate traffic split
        traffic_split = data.get("traffic_split", 0.5)
        if not (0.0 < traffic_split < 1.0):
            raise ValueError("Traffic split must be between 0.0 and 1.0")

        # Check for duplicate test name
        existing = self._get_by_name(data["name"])
        if existing:
            raise ValueError(f"A/B test with name '{data['name']}' already exists")

        # Create A/B test entity
        ab_test = ABTest(
            id=entity_id or generate_id(),
            name=data["name"],
            description=data.get("description", ""),
            prompt_a_id=data["prompt_a_id"],
            prompt_b_id=data["prompt_b_id"],
            test_metric=data.get("test_metric", "response_quality"),
            traffic_split=traffic_split,
            target_audience=data.get("target_audience", {}),
            created_by=data.get("created_by", "api_user")
        )

        # Save to database
        saved_test = self.repository.save(ab_test)

        # Cache the test
        asyncio.create_task(self._cache_test(saved_test))

        return saved_test

    def select_prompt_for_test(self, test_id: str, user_id: Optional[str] = None,
                              session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Select a prompt variant for A/B testing."""
        test = self.get_entity(test_id)
        if not test or not test.is_active:
            return None

        # Get the selected prompt ID
        selected_prompt_id = self.repository.select_prompt_for_test(test_id, user_id)

        if not selected_prompt_id:
            return None

        # Get the full prompt details
        selected_prompt = self.prompt_service.get_entity(selected_prompt_id)
        if not selected_prompt:
            return None

        # Record the selection for analytics
        asyncio.create_task(self._record_test_usage(test_id, selected_prompt_id, user_id, session_id))

        return {
            "test_id": test_id,
            "selected_prompt": selected_prompt.to_dict(),
            "variant": "A" if selected_prompt_id == test.prompt_a_id else "B",
            "user_id": user_id,
            "session_id": session_id
        }

    def get_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get comprehensive results for an A/B test."""
        test = self.get_entity(test_id)
        if not test:
            raise ValueError(f"A/B test {test_id} not found")

        # Get aggregated results
        aggregated_results = self.result_repository.get_aggregated_results(test_id)

        # Get prompt details
        prompt_a = self.prompt_service.get_entity(test.prompt_a_id)
        prompt_b = self.prompt_service.get_entity(test.prompt_b_id)

        if not prompt_a or not prompt_b:
            raise ValueError("Test prompts not found")

        # Calculate winner if we have enough data
        winner = self._determine_winner(test, aggregated_results)

        return {
            "test": test.to_dict(),
            "prompt_a": prompt_a.to_dict(),
            "prompt_b": prompt_b.to_dict(),
            "results": aggregated_results,
            "winner": winner,
            "confidence_assessment": self._assess_confidence(aggregated_results)
        }

    def record_test_result(self, test_id: str, prompt_id: str, metric_value: float,
                          sample_size: int = 1, metadata: Optional[Dict[str, Any]] = None) -> ABTestResult:
        """Record a result for an A/B test."""
        test = self.get_entity(test_id)
        if not test:
            raise ValueError(f"A/B test {test_id} not found")

        if prompt_id not in [test.prompt_a_id, test.prompt_b_id]:
            raise ValueError(f"Prompt {prompt_id} is not part of test {test_id}")

        # Calculate confidence level (simplified statistical significance)
        confidence_level = self._calculate_confidence_level(metric_value, sample_size)

        # Determine statistical significance (basic implementation)
        statistical_significance = confidence_level > 0.95

        result = ABTestResult(
            id=generate_id(),
            test_id=test_id,
            prompt_id=prompt_id,
            metric_value=metric_value,
            sample_size=sample_size,
            confidence_level=confidence_level,
            statistical_significance=statistical_significance
        )

        saved_result = self.result_repository.save(result)

        # Check if we should auto-determine winner
        if statistical_significance and not test.winner:
            aggregated = self.result_repository.get_aggregated_results(test_id)
            winner = self._determine_winner(test, aggregated)
            if winner:
                self.update_entity(test_id, {"winner": winner})

        return saved_result

    def end_test(self, test_id: str, winner: Optional[str] = None) -> ABTest:
        """End an A/B test and optionally declare a winner."""
        test = self.get_entity(test_id)
        if not test:
            raise ValueError(f"A/B test {test_id} not found")

        if not test.is_active:
            raise ValueError(f"A/B test {test_id} is already ended")

        updates = {"is_active": False, "end_date": utc_now()}

        if winner:
            if winner not in ["A", "B"]:
                raise ValueError("Winner must be 'A' or 'B'")
            updates["winner"] = winner

        # Auto-determine winner if not provided and we have results
        if not winner:
            aggregated = self.result_repository.get_aggregated_results(test_id)
            auto_winner = self._determine_winner(test, aggregated)
            if auto_winner:
                updates["winner"] = auto_winner

        updated_test = self.update_entity(test_id, updates)

        # Invalidate cache
        asyncio.create_task(self._invalidate_test_cache(test_id))

        return updated_test

    def get_active_tests(self) -> List[ABTest]:
        """Get all active A/B tests."""
        return self.repository.get_active_tests()

    def get_tests_for_prompt(self, prompt_id: str) -> List[ABTest]:
        """Get all A/B tests that include a specific prompt."""
        return self.repository.get_tests_by_prompt(prompt_id)

    def _get_by_name(self, name: str) -> Optional[ABTest]:
        """Get A/B test by name."""
        # This requires a database query - simplified implementation
        all_tests = self.repository.get_all(limit=1000)
        tests = all_tests.get("items", [])
        for test in tests:
            if test.name == name:
                return test
        return None

    def _determine_winner(self, test: ABTest, aggregated_results: Dict[str, Any]) -> Optional[str]:
        """Determine the winner of an A/B test based on results."""
        if len(aggregated_results) < 2:
            return None

        prompt_a_results = aggregated_results.get(test.prompt_a_id)
        prompt_b_results = aggregated_results.get(test.prompt_b_id)

        if not prompt_a_results or not prompt_b_results:
            return None

        # Check if we have statistical significance
        a_significant = prompt_a_results.get("has_statistical_significance", False)
        b_significant = prompt_b_results.get("has_statistical_significance", False)

        if not (a_significant or b_significant):
            return None

        # Compare average metrics (higher is better for most metrics)
        a_metric = prompt_a_results.get("average_metric", 0)
        b_metric = prompt_b_results.get("average_metric", 0)

        # For metrics where lower is better (like response_time), invert the comparison
        if test.test_metric == "response_time":
            return "A" if a_metric < b_metric else "B"
        else:
            return "A" if a_metric > b_metric else "B"

    def _calculate_confidence_level(self, metric_value: float, sample_size: int) -> float:
        """Calculate confidence level for a metric (simplified implementation)."""
        # This is a simplified confidence calculation
        # In a real implementation, you'd use proper statistical methods

        if sample_size < 10:
            return 0.5  # Low confidence with small sample

        # Assume normal distribution and calculate based on sample size
        # This is not statistically rigorous but provides a basic implementation
        base_confidence = min(0.95, sample_size / 100)  # Max 95% confidence

        # Adjust based on metric value stability (simplified)
        if metric_value < 0.1 or metric_value > 0.9:
            base_confidence *= 0.8  # Reduce confidence for extreme values

        return base_confidence

    def _assess_confidence(self, aggregated_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall confidence in test results."""
        if not aggregated_results:
            return {"level": "insufficient_data", "description": "Not enough data to assess confidence"}

        total_samples = sum(r.get("total_samples", 0) for r in aggregated_results.values())
        avg_confidence = sum(r.get("average_confidence", 0) for r in aggregated_results.values()) / len(aggregated_results)

        if total_samples < 100:
            return {
                "level": "low",
                "description": f"Low confidence: only {total_samples} total samples",
                "total_samples": total_samples,
                "average_confidence": avg_confidence
            }
        elif avg_confidence > 0.8:
            return {
                "level": "high",
                "description": "High confidence in results",
                "total_samples": total_samples,
                "average_confidence": avg_confidence
            }
        else:
            return {
                "level": "medium",
                "description": "Medium confidence: more data recommended",
                "total_samples": total_samples,
                "average_confidence": avg_confidence
            }

    async def _cache_test(self, test: ABTest) -> None:
        """Cache A/B test."""
        cache_key = f"ab_test:{test.id}"
        await prompt_store_cache.set(cache_key, test, ttl=3600)

    async def _invalidate_test_cache(self, test_id: str) -> None:
        """Invalidate test cache."""
        cache_key = f"ab_test:{test_id}"
        await prompt_store_cache.delete(cache_key)

    async def _record_test_usage(self, test_id: str, prompt_id: str,
                               user_id: Optional[str], session_id: Optional[str]) -> None:
        """Record test usage for analytics."""
        # This would integrate with the usage tracking system
        # For now, just increment counters
        pass

    def create_ab_test(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new A/B test (convenience method)."""
        ab_test = self.create_entity(test_data)
        return ab_test.to_dict()

    def get_ab_test(self, test_id: str) -> Optional[ABTest]:
        """Get A/B test by ID (alias for get_entity)."""
        return self.get_entity(test_id)

    def select_prompt_variant(self, test_id: str, user_id: Optional[str] = None) -> Optional[str]:
        """Select a prompt variant for A/B testing (convenience method)."""
        result = self.select_prompt_for_test(test_id, user_id)
        return result.get("selected_prompt", {}).get("id") if result else None

    def get_ab_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get test results (convenience method)."""
        return self.get_test_results(test_id)
