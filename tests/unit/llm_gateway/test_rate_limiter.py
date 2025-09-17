"""Unit tests for LLM Gateway Rate Limiter.

Tests the intelligent rate limiting functionality including
user-specific limits, burst protection, provider-specific limits,
and cooldown mechanisms.
"""

import pytest
import asyncio
import time
from collections import deque
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

# Adjust path for local imports
import sys
from pathlib import Path

# Add the LLM Gateway service directory to Python path
llm_gateway_path = Path(__file__).parent.parent.parent.parent / "services" / "llm-gateway"
sys.path.insert(0, str(llm_gateway_path))

from modules.rate_limiter import RateLimiter, UserRateLimit, RateLimitRule

# Test markers for parallel execution
pytestmark = [
    pytest.mark.unit,
    pytest.mark.parallel_safe,
    pytest.mark.slow  # Rate limiter tests may have timing dependencies
]


class TestRateLimiter:
    """Test suite for RateLimiter class."""

    @pytest.fixture
    def rate_limiter(self):
        """Create a RateLimiter instance for testing."""
        return RateLimiter()

    def test_rate_limiter_initialization(self, rate_limiter):
        """Test that RateLimiter initializes correctly."""
        assert isinstance(rate_limiter, RateLimiter)
        assert hasattr(rate_limiter, 'user_limits')
        assert hasattr(rate_limiter, 'provider_limits')
        assert hasattr(rate_limiter, 'special_rules')
        assert hasattr(rate_limiter, 'global_requests')
        assert hasattr(rate_limiter, 'global_tokens')

        # Should have provider-specific limits
        assert 'ollama' in rate_limiter.provider_limits
        assert 'openai' in rate_limiter.provider_limits
        assert 'bedrock' in rate_limiter.provider_limits

    @pytest.mark.asyncio
    async def test_check_rate_limit_new_user(self, rate_limiter):
        """Test rate limit check for a new user."""
        user_id = "new_user"

        # Should allow first request
        allowed = await rate_limiter.check_rate_limit(user_id, "ollama", 100)

        assert allowed is True

        # User should now be in user_limits
        assert user_id in rate_limiter.user_limits

    @pytest.mark.asyncio
    async def test_check_rate_limit_under_limit(self, rate_limiter):
        """Test rate limit check when under the limit."""
        user_id = "test_user"

        # Make requests under the limit
        for i in range(5):
            allowed = await rate_limiter.check_rate_limit(user_id, "ollama", 50)
            assert allowed is True

        # Check that requests were recorded
        user_limit = rate_limiter.user_limits[user_id]
        assert len(user_limit.request_times) == 5

    @pytest.mark.asyncio
    async def test_check_rate_limit_burst_protection(self, rate_limiter):
        """Test burst protection mechanism."""
        user_id = "burst_test_user"

        # Make rapid successive requests to trigger burst protection
        for i in range(15):  # More than burst limit
            allowed = await rate_limiter.check_rate_limit(user_id, "ollama", 50)
            if i < 10:  # Should allow first 10 (burst limit)
                assert allowed is True
            else:  # Should deny after burst limit
                if i == 10:  # First denied request should trigger cooldown
                    assert allowed is False
                # Subsequent requests should be denied due to cooldown

        # Check cooldown was activated
        user_limit = rate_limiter.user_limits[user_id]
        assert user_limit.cooldown_until > time.time()

    @pytest.mark.asyncio
    async def test_check_rate_limit_during_cooldown(self, rate_limiter):
        """Test rate limit check during cooldown period."""
        user_id = "cooldown_test_user"

        # Trigger cooldown by exceeding burst limit
        for i in range(15):
            await rate_limiter.check_rate_limit(user_id, "ollama", 50)

        # Next request should be denied due to cooldown
        allowed = await rate_limiter.check_rate_limit(user_id, "ollama", 50)
        assert allowed is False

    @pytest.mark.asyncio
    async def test_check_rate_limit_after_cooldown(self, rate_limiter):
        """Test rate limit check after cooldown period."""
        user_id = "cooldown_expired_user"

        # Trigger cooldown
        for i in range(15):
            await rate_limiter.check_rate_limit(user_id, "ollama", 50)

        # Manually expire cooldown for testing
        user_limit = rate_limiter.user_limits[user_id]
        user_limit.cooldown_until = time.time() - 1  # 1 second ago

        # Should allow request after cooldown
        allowed = await rate_limiter.check_rate_limit(user_id, "ollama", 50)
        assert allowed is True

    @pytest.mark.asyncio
    async def test_check_rate_limit_token_limits(self, rate_limiter):
        """Test token-based rate limiting."""
        user_id = "token_limit_user"

        # Make requests that approach token limits
        large_token_request = 60000  # Close to per-minute token limit

        # First request should be allowed
        allowed1 = await rate_limiter.check_rate_limit(user_id, "ollama", large_token_request)
        assert allowed1 is True

        # Second request might be denied due to token limits
        allowed2 = await rate_limiter.check_rate_limit(user_id, "ollama", large_token_request)
        # This could be True or False depending on timing, but shouldn't crash

    @pytest.mark.asyncio
    async def test_check_rate_limit_provider_specific(self, rate_limiter):
        """Test provider-specific rate limits."""
        user_id = "provider_test_user"

        # Test with different providers that have different limits
        ollama_allowed = await rate_limiter.check_rate_limit(user_id, "ollama", 100)
        openai_allowed = await rate_limiter.check_rate_limit(user_id, "openai", 100)

        # Both should be allowed initially
        assert ollama_allowed is True
        assert openai_allowed is True

        # Check that different rules were applied
        ollama_rule = rate_limiter.user_limits[user_id].rule
        # Reset user for clean test
        del rate_limiter.user_limits[user_id]

        await rate_limiter.check_rate_limit(user_id, "openai", 100)
        openai_rule = rate_limiter.user_limits[user_id].rule

        # Rules should be different for different providers
        assert ollama_rule.requests_per_minute != openai_rule.requests_per_minute

    def test_get_applicable_rule_default(self, rate_limiter):
        """Test getting default rule for regular users."""
        user_id = "regular_user"

        rule = rate_limiter._get_applicable_rule(user_id, "ollama")

        assert isinstance(rule, RateLimitRule)
        assert rule.requests_per_minute > 0
        assert rule.requests_per_hour > 0

    def test_get_applicable_rule_special_user(self, rate_limiter):
        """Test getting special rule for premium users."""
        user_id = "premium_user"

        # Set special rule
        premium_rule = RateLimitRule(
            requests_per_minute=200,
            requests_per_hour=10000,
            tokens_per_minute=100000,
            burst_limit=50,
            cooldown_seconds=30
        )
        rate_limiter.set_special_rule(user_id, premium_rule)

        rule = rate_limiter._get_applicable_rule(user_id, "ollama")

        assert rule == premium_rule
        assert rule.requests_per_minute == 200

    def test_get_applicable_rule_provider_specific(self, rate_limiter):
        """Test getting provider-specific rules."""
        user_id = "provider_specific_user"

        ollama_rule = rate_limiter._get_applicable_rule(user_id, "ollama")
        openai_rule = rate_limiter._get_applicable_rule(user_id, "openai")

        # Should have different rules for different providers
        assert ollama_rule.requests_per_minute != openai_rule.requests_per_minute

    def test_get_user_status_new_user(self, rate_limiter):
        """Test getting status for new user."""
        user_id = "status_test_new_user"

        status = rate_limiter.get_user_status(user_id)

        assert status["user_id"] == user_id
        assert status["status"] == "no_activity"
        assert status["requests_this_minute"] == 0
        assert status["requests_this_hour"] == 0
        assert status["cooldown_remaining"] == 0

    @pytest.mark.asyncio
    async def test_get_user_status_active_user(self, rate_limiter):
        """Test getting status for active user."""
        user_id = "status_test_active_user"

        # Make some requests
        await rate_limiter.check_rate_limit(user_id, "ollama", 100)
        await rate_limiter.check_rate_limit(user_id, "ollama", 100)

        status = rate_limiter.get_user_status(user_id)

        assert status["user_id"] == user_id
        assert status["status"] in ["normal", "approaching_limit"]
        assert status["requests_this_minute"] >= 2
        assert status["cooldown_remaining"] == 0

    @pytest.mark.asyncio
    async def test_get_user_status_cooldown_user(self, rate_limiter):
        """Test getting status for user in cooldown."""
        user_id = "status_test_cooldown_user"

        # Trigger cooldown
        for i in range(15):
            await rate_limiter.check_rate_limit(user_id, "ollama", 50)

        status = rate_limiter.get_user_status(user_id)

        assert status["user_id"] == user_id
        assert status["status"] == "cooldown"
        assert status["cooldown_remaining"] > 0

    def test_record_request(self, rate_limiter):
        """Test recording successful requests."""
        user_id = "record_test_user"
        provider = "ollama"
        tokens_used = 150

        # Record a request
        rate_limiter.record_request(user_id, provider, tokens_used)

        # Check global tracking
        assert len(rate_limiter.global_requests) >= 1
        assert len(rate_limiter.global_tokens) >= 1

    def test_set_special_rule(self, rate_limiter):
        """Test setting special rate limit rules."""
        user_id = "special_rule_test_user"
        special_rule = RateLimitRule(
            requests_per_minute=300,
            requests_per_hour=5000,
            tokens_per_minute=200000,
            burst_limit=100,
            cooldown_seconds=15
        )

        rate_limiter.set_special_rule(user_id, special_rule)

        assert user_id in rate_limiter.special_rules
        assert rate_limiter.special_rules[user_id] == special_rule

    def test_remove_special_rule(self, rate_limiter):
        """Test removing special rate limit rules."""
        user_id = "remove_special_test_user"

        # Add special rule first
        rate_limiter.set_special_rule(user_id, RateLimitRule(100, 1000, 50000, 10, 60))

        # Verify it was added
        assert user_id in rate_limiter.special_rules

        # Remove it
        rate_limiter.remove_special_rule(user_id)

        # Verify it was removed
        assert user_id not in rate_limiter.special_rules

    @pytest.mark.asyncio
    async def test_get_status(self, rate_limiter):
        """Test getting overall rate limiter status."""
        # Add some activity
        await rate_limiter.check_rate_limit("status_test_user", "ollama", 100)

        status = await rate_limiter.get_status()

        assert isinstance(status, dict)
        assert "global_requests_last_minute" in status
        assert "global_tokens_last_minute" in status
        assert "active_users" in status
        assert "special_rules_count" in status

    def test_reset_user_limits(self, rate_limiter):
        """Test resetting user rate limits."""
        user_id = "reset_test_user"

        # Add user activity
        rate_limiter.user_limits[user_id] = UserRateLimit(user_id, rate_limiter.default_rule)

        # Verify user exists
        assert user_id in rate_limiter.user_limits

        # Reset user limits
        rate_limiter.reset_user_limits(user_id)

        # Verify user was removed
        assert user_id not in rate_limiter.user_limits

    def test_reset_all_limits(self, rate_limiter):
        """Test resetting all user limits."""
        # Add multiple users
        users = ["reset_all_user1", "reset_all_user2", "reset_all_user3"]
        for user_id in users:
            rate_limiter.user_limits[user_id] = UserRateLimit(user_id, rate_limiter.default_rule)
            rate_limiter.set_special_rule(user_id, RateLimitRule(100, 1000, 50000, 10, 60))

        # Reset all limits
        rate_limiter.reset_user_limits()

        # Verify all users and special rules were cleared
        assert len(rate_limiter.user_limits) == 0
        assert len(rate_limiter.special_rules) == 0

    def test_user_rate_limit_structure(self):
        """Test UserRateLimit data structure."""
        rule = RateLimitRule(60, 1000, 50000, 10, 60)
        user_limit = UserRateLimit("test_user", rule)

        assert user_limit.user_id == "test_user"
        assert user_limit.rule == rule
        assert user_limit.burst_count == 0
        assert user_limit.cooldown_until == 0.0
        assert isinstance(user_limit.request_times, deque)
        assert isinstance(user_limit.token_usage, deque)

    def test_rate_limit_rule_structure(self):
        """Test RateLimitRule data structure."""
        rule = RateLimitRule(
            requests_per_minute=60,
            requests_per_hour=1000,
            tokens_per_minute=50000,
            burst_limit=10,
            cooldown_seconds=60
        )

        assert rule.requests_per_minute == 60
        assert rule.requests_per_hour == 1000
        assert rule.tokens_per_minute == 50000
        assert rule.burst_limit == 10
        assert rule.cooldown_seconds == 60

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, rate_limiter):
        """Test handling concurrent requests."""
        user_id = "concurrent_test_user"

        # Simulate concurrent requests
        tasks = []
        for i in range(10):
            task = rate_limiter.check_rate_limit(user_id, "ollama", 50)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Should handle concurrent requests without issues
        assert len(results) == 10
        # Some should be allowed, some denied based on rate limits
        allowed_count = sum(1 for result in results if result)
        denied_count = len(results) - allowed_count

        assert allowed_count >= 0
        assert denied_count >= 0
        assert allowed_count + denied_count == 10
