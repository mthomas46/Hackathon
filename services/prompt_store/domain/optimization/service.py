"""Optimization service for A/B testing and automated prompt improvement."""

import asyncio
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from ...core.service import BaseService
from ...shared.clients import ServiceClients
from ...shared.utilities import generate_id, utc_now
from ...infrastructure.cache import prompt_store_cache


class ABTest(BaseService):
    """A/B testing entity for prompt optimization."""

    def __init__(self, test_id: str, prompt_a_id: str, prompt_b_id: str,
                 traffic_percentage: float = 50.0):
        self.test_id = test_id
        self.prompt_a_id = prompt_a_id
        self.prompt_b_id = prompt_b_id
        self.traffic_percentage = traffic_percentage
        self.results_a = {"requests": 0, "successes": 0, "total_score": 0}
        self.results_b = {"requests": 0, "successes": 0, "total_score": 0}
        self.start_time = utc_now()
        self.status = "running"

    def assign_prompt(self, user_id: str) -> str:
        """Assign a prompt variant to a user."""
        # Simple A/B assignment based on user ID hash
        user_hash = hash(user_id) % 100
        if user_hash < self.traffic_percentage:
            return self.prompt_a_id
        else:
            return self.prompt_b_id

    def record_result(self, prompt_id: str, success: bool, score: float = 0.0):
        """Record the result of using a prompt variant."""
        if prompt_id == self.prompt_a_id:
            self.results_a["requests"] += 1
            if success:
                self.results_a["successes"] += 1
            self.results_a["total_score"] += score
        elif prompt_id == self.prompt_b_id:
            self.results_b["requests"] += 1
            if success:
                self.results_b["successes"] += 1
            self.results_b["total_score"] += score

    def get_results(self) -> Dict[str, Any]:
        """Get current test results."""
        def calculate_metrics(results):
            requests = results["requests"]
            if requests == 0:
                return {"conversion_rate": 0, "average_score": 0, "requests": 0}
            return {
                "conversion_rate": results["successes"] / requests,
                "average_score": results["total_score"] / requests,
                "requests": requests
            }

        return {
            "test_id": self.test_id,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "prompt_a": {
                "id": self.prompt_a_id,
                **calculate_metrics(self.results_a)
            },
            "prompt_b": {
                "id": self.prompt_b_id,
                **calculate_metrics(self.results_b)
            },
            "winner": self.determine_winner()
        }

    def determine_winner(self) -> Optional[str]:
        """Determine which prompt is performing better."""
        if self.results_a["requests"] < 10 or self.results_b["requests"] < 10:
            return None  # Need more data

        rate_a = self.results_a["successes"] / self.results_a["requests"]
        rate_b = self.results_b["successes"] / self.results_b["requests"]

        if rate_a > rate_b:
            return self.prompt_a_id
        elif rate_b > rate_a:
            return self.prompt_b_id
        else:
            return None  # Tie


class OptimizationService:
    """Service for automated prompt optimization and A/B testing."""

    def __init__(self):
        self.clients = ServiceClients()
        self.active_tests: Dict[str, ABTest] = {}

    async def create_ab_test(self, prompt_a_id: str, prompt_b_id: str,
                           traffic_percentage: float = 50.0) -> ABTest:
        """Create a new A/B test between two prompt variants."""
        test_id = generate_id()
        test = ABTest(test_id, prompt_a_id, prompt_b_id, traffic_percentage)
        self.active_tests[test_id] = test

        # Cache the test
        await prompt_store_cache.set(f"ab_test:{test_id}", test.get_results(), ttl=3600)

        return test

    async def get_prompt_for_user(self, test_id: str, user_id: str) -> Optional[str]:
        """Get the assigned prompt for a user in an A/B test."""
        test = self.active_tests.get(test_id)
        if not test:
            # Try to load from cache
            cached = await prompt_store_cache.get(f"ab_test:{test_id}")
            if cached:
                # Recreate test from cached data (simplified)
                test = ABTest(cached["test_id"],
                            cached["prompt_a"]["id"],
                            cached["prompt_b"]["id"])
                self.active_tests[test_id] = test

        if test and test.status == "running":
            return test.assign_prompt(user_id)

        return None

    async def record_test_result(self, test_id: str, prompt_id: str,
                               success: bool, score: float = 0.0):
        """Record the result of using a prompt in an A/B test."""
        test = self.active_tests.get(test_id)
        if test:
            test.record_result(prompt_id, success, score)
            # Update cache
            await prompt_store_cache.set(f"ab_test:{test_id}", test.get_results(), ttl=3600)

    async def get_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get results for an A/B test."""
        test = self.active_tests.get(test_id)
        if test:
            return test.get_results()

        # Try cache
        cached = await prompt_store_cache.get(f"ab_test:{test_id}")
        return cached

    async def end_test(self, test_id: str) -> Optional[str]:
        """End an A/B test and return the winning prompt."""
        test = self.active_tests.get(test_id)
        if test:
            test.status = "completed"
            winner = test.determine_winner()
            # Update cache
            results = test.get_results()
            await prompt_store_cache.set(f"ab_test:{test_id}", results, ttl=86400)  # Keep for 24 hours
            return winner

        return None

    async def run_automated_optimization(self, prompt_id: str, base_version: int) -> Dict[str, Any]:
        """Run automated optimization cycle for a prompt."""
        # This would create variations, run A/B tests, and implement improvements
        # For now, return a basic structure

        optimization_cycle = {
            "prompt_id": prompt_id,
            "base_version": base_version,
            "status": "running",
            "variations_created": 0,
            "tests_started": 0,
            "improvements_applied": 0,
            "cycle_id": generate_id()
        }

        # Cache the optimization cycle
        await prompt_store_cache.set(f"optimization:{optimization_cycle['cycle_id']}",
                                   optimization_cycle, ttl=3600)

        return optimization_cycle

    async def generate_prompt_variations(self, prompt_content: str, count: int = 3) -> List[str]:
        """Generate variations of a prompt using LLM."""
        variations = []

        for i in range(count):
            try:
                variation_prompt = f"""
                Create a variation of this prompt. Make it more effective by:
                1. Improving clarity
                2. Adding specific instructions
                3. Optimizing structure

                Original prompt:
                {prompt_content}

                Provide only the improved prompt, no explanation:
                """

                response = await self.clients.interpret_query(variation_prompt, "system")
                if response.get("success"):
                    variation = response["data"].get("response_text", "").strip()
                    if variation and len(variation) > 10:  # Basic quality check
                        variations.append(variation)

            except Exception as e:
                print(f"Error generating variation {i}: {e}")

        # If LLM fails, create simple variations
        if not variations:
            variations = [
                f"Improved version 1: {prompt_content}",
                f"Enhanced version 2: {prompt_content}",
                f"Optimized version 3: {prompt_content}"
            ]

        return variations[:count]
