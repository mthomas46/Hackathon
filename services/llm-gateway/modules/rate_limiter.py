"""Rate Limiter Module for LLM Gateway Service.

Implements intelligent rate limiting to prevent abuse, manage costs, and ensure
fair usage across different users and providers. Supports multiple rate limiting
strategies including token bucket, sliding window, and provider-specific limits.
"""

import time
from collections import defaultdict, deque
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from services.shared.config import get_config_value
from services.shared.logging import fire_and_forget
from services.shared.constants_new import ServiceNames


@dataclass
class RateLimitRule:
    """Represents a rate limiting rule."""
    requests_per_minute: int
    requests_per_hour: int
    tokens_per_minute: int
    burst_limit: int
    cooldown_seconds: int


@dataclass
class UserRateLimit:
    """Rate limit state for a user."""
    user_id: str
    rule: RateLimitRule
    request_times: deque = None  # Sliding window of request timestamps
    token_usage: deque = None    # Sliding window of token usage
    burst_count: int = 0
    last_request_time: float = 0.0
    cooldown_until: float = 0.0

    def __post_init__(self):
        if self.request_times is None:
            self.request_times = deque(maxlen=100)
        if self.token_usage is None:
            self.token_usage = deque(maxlen=100)


class RateLimiter:
    """Intelligent rate limiter for LLM requests."""

    def __init__(self):
        # User-specific rate limits
        self.user_limits: Dict[str, UserRateLimit] = {}

        # Global rate limits
        self.global_requests: deque = deque(maxlen=1000)
        self.global_tokens: deque = deque(maxlen=10000)

        # Default rate limit rules
        self.default_rule = RateLimitRule(
            requests_per_minute=int(get_config_value("RATE_LIMIT_REQUESTS_PER_MINUTE", "60", section="rate_limiting")),
            requests_per_hour=int(get_config_value("RATE_LIMIT_REQUESTS_PER_HOUR", "1000", section="rate_limiting")),
            tokens_per_minute=int(get_config_value("RATE_LIMIT_TOKENS_PER_MINUTE", "50000", section="rate_limiting")),
            burst_limit=int(get_config_value("RATE_LIMIT_BURST_LIMIT", "10", section="rate_limiting")),
            cooldown_seconds=int(get_config_value("RATE_LIMIT_COOLDOWN_SECONDS", "60", section="rate_limiting"))
        )

        # Provider-specific rate limits
        self.provider_limits: Dict[str, RateLimitRule] = self._load_provider_limits()

        # Special user rules (premium users, etc.)
        self.special_rules: Dict[str, RateLimitRule] = {}

    def _load_provider_limits(self) -> Dict[str, RateLimitRule]:
        """Load provider-specific rate limits."""
        return {
            "ollama": RateLimitRule(
                requests_per_minute=120,
                requests_per_hour=2000,
                tokens_per_minute=100000,
                burst_limit=20,
                cooldown_seconds=30
            ),
            "openai": RateLimitRule(
                requests_per_minute=50,
                requests_per_hour=500,
                tokens_per_minute=40000,
                burst_limit=5,
                cooldown_seconds=60
            ),
            "anthropic": RateLimitRule(
                requests_per_minute=50,
                requests_per_hour=500,
                tokens_per_minute=40000,
                burst_limit=5,
                cooldown_seconds=60
            ),
            "bedrock": RateLimitRule(
                requests_per_minute=30,
                requests_per_hour=300,
                tokens_per_minute=20000,
                burst_limit=3,
                cooldown_seconds=120
            ),
            "grok": RateLimitRule(
                requests_per_minute=60,
                requests_per_hour=1000,
                tokens_per_minute=50000,
                burst_limit=10,
                cooldown_seconds=45
            )
        }

    async def check_rate_limit(self, user_id: str, provider: str = "default",
                              tokens_requested: int = 0) -> bool:
        """Check if a request should be allowed based on rate limits."""
        try:
            # Get applicable rule
            rule = self._get_applicable_rule(user_id, provider)

            # Initialize user limit if not exists
            if user_id not in self.user_limits:
                self.user_limits[user_id] = UserRateLimit(user_id, rule)

            user_limit = self.user_limits[user_id]

            current_time = time.time()

            # Check cooldown period
            if current_time < user_limit.cooldown_until:
                remaining_cooldown = int(user_limit.cooldown_until - current_time)
                fire_and_forget(
                    "llm_gateway_rate_limit_cooldown",
                    f"User {user_id} in cooldown for {remaining_cooldown} seconds",
                    ServiceNames.LLM_GATEWAY,
                    {
                        "user_id": user_id,
                        "remaining_cooldown": remaining_cooldown,
                        "provider": provider
                    }
                )
                return False

            # Clean old entries from sliding windows
            self._clean_old_entries(user_limit, current_time)

            # Check burst limit
            time_since_last_request = current_time - user_limit.last_request_time
            if time_since_last_request < 1.0:  # Within 1 second
                user_limit.burst_count += 1
                if user_limit.burst_count > rule.burst_limit:
                    # Enter cooldown
                    user_limit.cooldown_until = current_time + rule.cooldown_seconds
                    user_limit.burst_count = 0

                    fire_and_forget(
                        "llm_gateway_burst_limit_exceeded",
                        f"User {user_id} exceeded burst limit, cooldown activated",
                        ServiceNames.LLM_GATEWAY,
                        {
                            "user_id": user_id,
                            "burst_count": user_limit.burst_count,
                            "cooldown_seconds": rule.cooldown_seconds
                        }
                    )
                    return False
            else:
                user_limit.burst_count = 1

            # Check per-minute request limit
            recent_requests = [t for t in user_limit.request_times if current_time - t < 60]
            if len(recent_requests) >= rule.requests_per_minute:
                return False

            # Check per-hour request limit
            hourly_requests = [t for t in user_limit.request_times if current_time - t < 3600]
            if len(hourly_requests) >= rule.requests_per_hour:
                return False

            # Check token limits
            if tokens_requested > 0:
                recent_tokens = sum(tokens for _, tokens in user_limit.token_usage
                                  if current_time - _ < 60)
                if recent_tokens + tokens_requested > rule.tokens_per_minute:
                    return False

            # Check global limits
            if not self._check_global_limits(current_time):
                return False

            # Update tracking
            user_limit.request_times.append(current_time)
            user_limit.last_request_time = current_time

            if tokens_requested > 0:
                user_limit.token_usage.append((current_time, tokens_requested))

            return True

        except Exception as e:
            # On error, allow the request but log the issue
            fire_and_forget(
                "llm_gateway_rate_limit_error",
                f"Rate limit check error for user {user_id}: {str(e)}",
                ServiceNames.LLM_GATEWAY,
                {
                    "user_id": user_id,
                    "provider": provider,
                    "error": str(e)
                }
            )
            return True

    def _get_applicable_rule(self, user_id: str, provider: str) -> RateLimitRule:
        """Get the applicable rate limit rule for a user and provider."""
        # Check for special user rules first
        if user_id in self.special_rules:
            return self.special_rules[user_id]

        # Check for provider-specific rules
        if provider in self.provider_limits:
            return self.provider_limits[provider]

        # Default rule
        return self.default_rule

    def _clean_old_entries(self, user_limit: UserRateLimit, current_time: float):
        """Clean old entries from sliding windows."""
        # Clean request times (keep only last hour)
        while user_limit.request_times and current_time - user_limit.request_times[0] > 3600:
            user_limit.request_times.popleft()

        # Clean token usage (keep only last hour)
        while user_limit.token_usage and current_time - user_limit.token_usage[0][0] > 3600:
            user_limit.token_usage.popleft()

    def _check_global_limits(self, current_time: float) -> bool:
        """Check global rate limits."""
        try:
            # Clean old global entries
            while self.global_requests and current_time - self.global_requests[0] > 60:
                self.global_requests.popleft()

            while self.global_tokens and current_time - self.global_tokens[0][0] > 60:
                self.global_tokens.popleft()

            # Check global request limit (1000 per minute)
            if len(self.global_requests) >= 1000:
                return False

            return True

        except Exception:
            # On global limit check error, allow the request
            return True

    def record_request(self, user_id: str, provider: str, tokens_used: int = 0):
        """Record a successful request for global tracking."""
        try:
            current_time = time.time()

            # Record global request
            self.global_requests.append(current_time)

            # Record global tokens
            if tokens_used > 0:
                self.global_tokens.append((current_time, tokens_used))

            # Clean global tracking
            self._check_global_limits(current_time)

        except Exception as e:
            fire_and_forget(
                "llm_gateway_global_tracking_error",
                f"Global tracking error: {str(e)}",
                ServiceNames.LLM_GATEWAY,
                {"error": str(e)}
            )

    def set_special_rule(self, user_id: str, rule: RateLimitRule):
        """Set a special rate limit rule for a user."""
        self.special_rules[user_id] = rule

        fire_and_forget(
            "llm_gateway_special_rule_set",
            f"Special rate limit rule set for user {user_id}",
            ServiceNames.LLM_GATEWAY,
            {
                "user_id": user_id,
                "rule": {
                    "requests_per_minute": rule.requests_per_minute,
                    "requests_per_hour": rule.requests_per_hour,
                    "tokens_per_minute": rule.tokens_per_minute
                }
            }
        )

    def remove_special_rule(self, user_id: str):
        """Remove special rate limit rule for a user."""
        if user_id in self.special_rules:
            del self.special_rules[user_id]

            fire_and_forget(
                "llm_gateway_special_rule_removed",
                f"Special rate limit rule removed for user {user_id}",
                ServiceNames.LLM_GATEWAY,
                {"user_id": user_id}
            )

    def get_user_status(self, user_id: str) -> Dict[str, Any]:
        """Get rate limit status for a user."""
        if user_id not in self.user_limits:
            return {
                "user_id": user_id,
                "status": "no_activity",
                "requests_this_minute": 0,
                "requests_this_hour": 0,
                "tokens_this_minute": 0,
                "burst_count": 0,
                "cooldown_remaining": 0
            }

        user_limit = self.user_limits[user_id]
        current_time = time.time()

        # Calculate current usage
        requests_this_minute = sum(1 for t in user_limit.request_times
                                 if current_time - t < 60)
        requests_this_hour = len(user_limit.request_times)  # Already limited to 1 hour

        tokens_this_minute = sum(tokens for _, tokens in user_limit.token_usage
                               if current_time - _ < 60)

        cooldown_remaining = max(0, int(user_limit.cooldown_until - current_time))

        # Determine status
        rule = user_limit.rule
        status = "normal"

        if cooldown_remaining > 0:
            status = "cooldown"
        elif requests_this_minute >= rule.requests_per_minute * 0.9:  # 90% of limit
            status = "approaching_limit"
        elif requests_this_hour >= rule.requests_per_hour * 0.9:
            status = "approaching_hourly_limit"
        elif tokens_this_minute >= rule.tokens_per_minute * 0.9:
            status = "approaching_token_limit"

        return {
            "user_id": user_id,
            "status": status,
            "rule": {
                "requests_per_minute": rule.requests_per_minute,
                "requests_per_hour": rule.requests_per_hour,
                "tokens_per_minute": rule.tokens_per_minute,
                "burst_limit": rule.burst_limit
            },
            "current_usage": {
                "requests_this_minute": requests_this_minute,
                "requests_this_hour": requests_this_hour,
                "tokens_this_minute": tokens_this_minute,
                "burst_count": user_limit.burst_count
            },
            "limits": {
                "cooldown_remaining": cooldown_remaining,
                "next_request_allowed": user_limit.cooldown_until if cooldown_remaining > 0 else 0
            }
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get overall rate limiter status."""
        try:
            current_time = time.time()

            # Clean global tracking
            self._check_global_limits(current_time)

            return {
                "global_requests_last_minute": len(self.global_requests),
                "global_tokens_last_minute": sum(tokens for _, tokens in self.global_tokens),
                "active_users": len(self.user_limits),
                "special_rules_count": len(self.special_rules),
                "timestamp": current_time
            }

        except Exception as e:
            return {
                "error": f"Failed to get status: {str(e)}",
                "timestamp": time.time()
            }

    def reset_user_limits(self, user_id: Optional[str] = None):
        """Reset rate limits for a user or all users."""
        if user_id:
            if user_id in self.user_limits:
                del self.user_limits[user_id]
                fire_and_forget(
                    "llm_gateway_user_limits_reset",
                    f"Rate limits reset for user {user_id}",
                    ServiceNames.LLM_GATEWAY,
                    {"user_id": user_id}
                )
        else:
            self.user_limits.clear()
            self.special_rules.clear()
            fire_and_forget(
                "llm_gateway_all_limits_reset",
                "All user rate limits reset",
                ServiceNames.LLM_GATEWAY
            )

    def get_rate_limit_violations(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get rate limit violations from the last N hours."""
        current_time = time.time()
        cutoff_time = current_time - (hours * 3600)

        violations = []

        # Check user violations
        for user_id, user_limit in self.user_limits.items():
            # Check for cooldowns in the time period
            if user_limit.cooldown_until > cutoff_time:
                violations.append({
                    "type": "user_cooldown",
                    "user_id": user_id,
                    "timestamp": user_limit.cooldown_until,
                    "reason": "Exceeded burst limit"
                })

        # Could also check for other violation patterns
        # (high request rates, unusual patterns, etc.)

        return violations
