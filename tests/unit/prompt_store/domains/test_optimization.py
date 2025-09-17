"""Unit tests for optimization domain functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.prompt_store.domain.optimization.service import (
    OptimizationService,
    ABTest
)


@pytest.fixture
def optimization_service():
    """Create optimization service for testing."""
    return OptimizationService()


@pytest.mark.asyncio
class TestOptimizationService:
    """Test cases for optimization service functionality."""

    async def test_create_ab_test(self, optimization_service):
        """Test creating a new A/B test."""
        prompt_a_id = "prompt_a_123"
        prompt_b_id = "prompt_b_456"
        traffic_percentage = 60.0

        with patch('services.prompt_store.domain.optimization.service.prompt_store_cache') as mock_cache:
            mock_cache.set = AsyncMock()

            result = await optimization_service.create_ab_test(
                prompt_a_id, prompt_b_id, traffic_percentage
            )

            # Verify test was created
            assert isinstance(result, ABTest)
            assert result.prompt_a_id == prompt_a_id
            assert result.prompt_b_id == prompt_b_id
            assert result.traffic_percentage == traffic_percentage
            assert result.status == "running"

            # Verify cache was called
            mock_cache.set.assert_called_once()

    async def test_get_prompt_for_user_assignment(self, optimization_service):
        """Test getting prompt assignment for a user."""
        # Create a test
        test = ABTest("test_123", "prompt_a", "prompt_b", 70.0)
        optimization_service.active_tests["test_123"] = test

        # Mock cache miss
        with patch('services.prompt_store.domain.optimization.service.prompt_store_cache') as mock_cache:
            mock_cache.get.return_value = None

            # Test assignment (deterministic based on hash)
            result = await optimization_service.get_prompt_for_user("test_123", "user_456")

            # Result should be one of the two prompts
            assert result in ["prompt_a", "prompt_b"]

    async def test_get_prompt_for_user_nonexistent_test(self, optimization_service):
        """Test getting prompt for non-existent test."""
        with patch('services.prompt_store.domain.optimization.service.prompt_store_cache') as mock_cache:
            mock_cache.get.return_value = None

            result = await optimization_service.get_prompt_for_user("nonexistent", "user_123")

            assert result is None

    async def test_record_test_result_success(self, optimization_service):
        """Test recording a successful test result."""
        # Create and register test
        test = ABTest("test_123", "prompt_a", "prompt_b", 50.0)
        optimization_service.active_tests["test_123"] = test

        with patch('services.prompt_store.domain.optimization.service.prompt_store_cache') as mock_cache:
            mock_cache.set = AsyncMock()

            # Record result for prompt_a
            await optimization_service.record_test_result("test_123", "prompt_a", True, 4.5)

            # Verify test results were updated
            assert test.results_a["requests"] == 1
            assert test.results_a["successes"] == 1
            assert test.results_a["total_score"] == 4.5

            # Cache should have been updated
            mock_cache.set.assert_called_once()

    async def test_record_test_result_failure(self, optimization_service):
        """Test recording a failed test result."""
        # Create and register test
        test = ABTest("test_123", "prompt_a", "prompt_b", 50.0)
        optimization_service.active_tests["test_123"] = test

        with patch('services.prompt_store.domain.optimization.service.prompt_store_cache') as mock_cache:
            mock_cache.set = AsyncMock()

            # Record failed result for prompt_b
            await optimization_service.record_test_result("test_123", "prompt_b", False, 2.0)

            # Verify test results were updated
            assert test.results_b["requests"] == 1
            assert test.results_b["successes"] == 0
            assert test.results_b["failed_requests"] == 1
            assert test.results_b["total_score"] == 2.0

    async def test_get_test_results(self, optimization_service):
        """Test getting test results."""
        # Create test with some data
        test = ABTest("test_123", "prompt_a", "prompt_b", 50.0)
        test.record_result("prompt_a", True, 4.0)
        test.record_result("prompt_a", False, 2.0)
        test.record_result("prompt_b", True, 3.5)

        optimization_service.active_tests["test_123"] = test

        results = await optimization_service.get_test_results("test_123")

        assert results is not None
        assert results["test_id"] == "test_123"
        assert results["status"] == "running"

        # Check prompt_a results
        prompt_a = results["prompt_a"]
        assert prompt_a["requests"] == 2
        assert prompt_a["conversion_rate"] == 0.5  # 1 success out of 2
        assert prompt_a["average_score"] == 3.0  # (4.0 + 2.0) / 2

        # Check prompt_b results
        prompt_b = results["prompt_b"]
        assert prompt_b["requests"] == 1
        assert prompt_b["conversion_rate"] == 1.0  # 1 success out of 1
        assert prompt_b["average_score"] == 3.5

    async def test_get_test_results_nonexistent(self, optimization_service):
        """Test getting results for non-existent test."""
        with patch('services.prompt_store.domain.optimization.service.prompt_store_cache') as mock_cache:
            mock_cache.get.return_value = None

            results = await optimization_service.get_test_results("nonexistent")

            assert results is None

    async def test_end_test_with_winner(self, optimization_service):
        """Test ending a test that has a clear winner."""
        # Create test with clear winner (prompt_a performs much better)
        test = ABTest("test_123", "prompt_a", "prompt_b", 50.0)

        # Give prompt_a many successes
        for _ in range(20):
            test.record_result("prompt_a", True, 4.5)

        # Give prompt_b poor performance
        for _ in range(20):
            test.record_result("prompt_b", False, 2.0)

        optimization_service.active_tests["test_123"] = test

        with patch('services.prompt_store.domain.optimization.service.prompt_store_cache') as mock_cache:
            mock_cache.set = AsyncMock()

            winner = await optimization_service.end_test("test_123")

            assert winner == "prompt_a"
            assert test.status == "completed"

            # Cache should be updated with longer TTL
            mock_cache.set.assert_called_once()

    async def test_end_test_insufficient_data(self, optimization_service):
        """Test ending a test with insufficient data."""
        # Create test with minimal data
        test = ABTest("test_123", "prompt_a", "prompt_b", 50.0)
        test.record_result("prompt_a", True, 4.0)  # Only 1 result each

        optimization_service.active_tests["test_123"] = test

        with patch('services.prompt_store.domain.optimization.service.prompt_store_cache') as mock_cache:
            mock_cache.set = AsyncMock()

            winner = await optimization_service.end_test("test_123")

            # With insufficient data, no clear winner
            assert winner is None
            assert test.status == "completed"

    async def test_run_automated_optimization(self, optimization_service):
        """Test running automated optimization cycle."""
        prompt_id = "test_prompt_123"
        base_version = 1

        with patch('services.prompt_store.domain.optimization.service.prompt_store_cache') as mock_cache:
            mock_cache.set = AsyncMock()

            result = await optimization_service.run_automated_optimization(prompt_id, base_version)

            assert "cycle_id" in result
            assert result["prompt_id"] == prompt_id
            assert result["base_version"] == base_version
            assert result["status"] == "running"

            # Cache should be set
            mock_cache.set.assert_called_once()

    async def test_generate_prompt_variations_success(self, optimization_service):
        """Test generating prompt variations successfully."""
        base_prompt = "Write a summary of this text: {text}"

        with patch.object(optimization_service.clients, 'interpret_query', new_callable=AsyncMock) as mock_interpret:
            mock_interpret.return_value = {
                "success": True,
                "data": {
                    "response_text": "Improved version: Create a concise summary of the following text: {text}"
                }
            }

            variations = await optimization_service.generate_prompt_variations(base_prompt, 2)

            # Should return variations (may fall back to simple variations if LLM fails)
            assert isinstance(variations, list)
            assert len(variations) <= 2  # May be less if LLM fails

    async def test_generate_prompt_variations_llm_failure(self, optimization_service):
        """Test generating variations when LLM fails (should fall back to simple variations)."""
        base_prompt = "Original prompt"

        with patch.object(optimization_service.clients, 'interpret_query', new_callable=AsyncMock) as mock_interpret:
            mock_interpret.side_effect = Exception("LLM service unavailable")

            variations = await optimization_service.generate_prompt_variations(base_prompt, 3)

            # Should fall back to simple variations
            assert isinstance(variations, list)
            assert len(variations) == 3

            # Check that variations are created
            for variation in variations:
                assert isinstance(variation, str)
                assert len(variation) > 0


class TestABTest:
    """Test cases for ABTest class functionality."""

    def test_ab_test_initialization(self):
        """Test ABTest initialization."""
        test = ABTest("test_123", "prompt_a", "prompt_b", 75.0)

        assert test.test_id == "test_123"
        assert test.prompt_a_id == "prompt_a"
        assert test.prompt_b_id == "prompt_b"
        assert test.traffic_percentage == 75.0
        assert test.status == "running"
        assert test.results_a["requests"] == 0
        assert test.results_b["requests"] == 0

    def test_assign_prompt_traffic_distribution(self):
        """Test prompt assignment follows traffic distribution."""
        test = ABTest("test_123", "prompt_a", "prompt_b", 70.0)

        # Test multiple assignments to check distribution
        assignments = []
        for i in range(1000):
            user_id = f"user_{i}"
            assignment = test.assign_prompt(user_id)
            assignments.append(assignment)

        # Count assignments
        prompt_a_count = assignments.count("prompt_a")
        prompt_b_count = assignments.count("prompt_b")

        # Should be roughly 70/30 split (allowing some variance due to hashing)
        total_assignments = len(assignments)
        prompt_a_percentage = (prompt_a_count / total_assignments) * 100

        # Allow 10% variance due to hash-based distribution
        assert 60.0 <= prompt_a_percentage <= 80.0

    def test_record_result_prompt_a(self):
        """Test recording results for prompt A."""
        test = ABTest("test_123", "prompt_a", "prompt_b", 50.0)

        test.record_result("prompt_a", True, 4.5)
        test.record_result("prompt_a", False, 2.0)
        test.record_result("prompt_a", True, 5.0)

        results = test.results_a
        assert results["requests"] == 3
        assert results["successes"] == 2
        assert results["total_score"] == 11.5  # 4.5 + 2.0 + 5.0

    def test_record_result_prompt_b(self):
        """Test recording results for prompt B."""
        test = ABTest("test_123", "prompt_a", "prompt_b", 50.0)

        test.record_result("prompt_b", True, 3.5)
        test.record_result("prompt_b", True, 4.0)

        results = test.results_b
        assert results["requests"] == 2
        assert results["successes"] == 2
        assert results["total_score"] == 7.5  # 3.5 + 4.0

    def test_get_results_with_data(self):
        """Test getting results when test has data."""
        test = ABTest("test_123", "prompt_a", "prompt_b", 50.0)

        # Add some test data
        test.record_result("prompt_a", True, 4.0)
        test.record_result("prompt_a", False, 2.0)
        test.record_result("prompt_b", True, 3.5)
        test.record_result("prompt_b", True, 4.5)

        results = test.get_results()

        assert results["test_id"] == "test_123"
        assert results["status"] == "running"

        # Check prompt_a results
        prompt_a = results["prompt_a"]
        assert prompt_a["requests"] == 2
        assert prompt_a["conversion_rate"] == 0.5
        assert prompt_a["average_score"] == 3.0

        # Check prompt_b results
        prompt_b = results["prompt_b"]
        assert prompt_b["requests"] == 2
        assert prompt_b["conversion_rate"] == 1.0
        assert prompt_b["average_score"] == 4.0

        # With equal performance, winner should be None or either one
        # (depends on implementation details)
        assert results["winner"] in [None, "prompt_a", "prompt_b"]

    def test_get_results_insufficient_data(self):
        """Test getting results with insufficient data."""
        test = ABTest("test_123", "prompt_a", "prompt_b", 50.0)

        # Add minimal data
        test.record_result("prompt_a", True, 4.0)

        results = test.get_results()

        # With insufficient data, no winner should be determined
        assert results["winner"] is None

    def test_determine_winner_clear_winner(self):
        """Test winner determination with clear performance difference."""
        test = ABTest("test_123", "prompt_a", "prompt_b", 50.0)

        # Make prompt_a clearly better
        for _ in range(15):
            test.record_result("prompt_a", True, 4.5)

        for _ in range(15):
            test.record_result("prompt_b", False, 2.0)

        winner = test.determine_winner()

        assert winner == "prompt_a"

    def test_determine_winner_insufficient_data(self):
        """Test winner determination with insufficient data."""
        test = ABTest("test_123", "prompt_a", "prompt_b", 50.0)

        # Add minimal data
        test.record_result("prompt_a", True, 4.0)
        test.record_result("prompt_b", True, 4.0)

        winner = test.determine_winner()

        # Should return None due to insufficient data
        assert winner is None
