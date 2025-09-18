"""Metrics Collector Module for LLM Gateway Service.

Collects comprehensive metrics for LLM usage, performance, costs, and error tracking.
Provides insights into provider performance, cost optimization, and system health.
"""

import time
from collections import defaultdict, deque
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from services.shared.logging import fire_and_forget
from services.shared.constants_new import ServiceNames


@dataclass
class RequestMetrics:
    """Metrics for a single LLM request."""
    timestamp: float
    provider: str
    response_time: float
    tokens_used: int
    cost: float
    success: bool
    error_type: Optional[str] = None
    user_id: Optional[str] = None


@dataclass
class ProviderMetrics:
    """Aggregated metrics for a provider."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    total_response_time: float = 0.0
    error_counts: Dict[str, int] = field(default_factory=dict)
    response_times: List[float] = field(default_factory=list)

    def add_request(self, metrics: RequestMetrics):
        """Add a request to the provider metrics."""
        self.total_requests += 1

        if metrics.success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
            if metrics.error_type:
                self.error_counts[metrics.error_type] = self.error_counts.get(metrics.error_type, 0) + 1

        self.total_tokens += metrics.tokens_used
        self.total_cost += metrics.cost
        self.total_response_time += metrics.response_time

        # Keep last 100 response times for rolling averages
        self.response_times.append(metrics.response_time)
        if len(self.response_times) > 100:
            self.response_times.pop(0)

    def get_success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    def get_average_response_time(self) -> float:
        """Get average response time in seconds."""
        if self.total_requests == 0:
            return 0.0
        return self.total_response_time / self.total_requests

    def get_average_cost_per_request(self) -> float:
        """Get average cost per request."""
        if self.total_requests == 0:
            return 0.0
        return self.total_cost / self.total_requests

    def get_tokens_per_second(self) -> float:
        """Get tokens per second rate."""
        total_time = sum(self.response_times)
        if total_time == 0:
            return 0.0
        return sum(self.response_times[-10:]) / max(total_time, 0.001)  # Use last 10 for recency


class MetricsCollector:
    """Collects and analyzes LLM usage metrics."""

    def __init__(self):
        self.provider_metrics: Dict[str, ProviderMetrics] = defaultdict(ProviderMetrics)
        self.request_history: deque = deque(maxlen=1000)  # Keep last 1000 requests
        self.start_time = time.time()

        # Rolling metrics windows
        self.hourly_metrics: Dict[int, Dict[str, Any]] = {}
        self.daily_metrics: Dict[int, Dict[str, Any]] = {}

    async def record_request(self, request_type: str, provider: str,
                           response_time: float, tokens_used: int,
                           cost: float = 0.0, success: bool = True,
                           error_type: Optional[str] = None,
                           user_id: Optional[str] = None):
        """Record metrics for a single LLM request."""
        try:
            metrics = RequestMetrics(
                timestamp=time.time(),
                provider=provider,
                response_time=response_time,
                tokens_used=tokens_used,
                cost=cost,
                success=success,
                error_type=error_type,
                user_id=user_id
            )

            # Add to provider metrics
            self.provider_metrics[provider].add_request(metrics)

            # Add to request history
            self.request_history.append(metrics)

            # Update rolling metrics
            await self._update_rolling_metrics(metrics)

            # Log high-level metrics
            if not success or response_time > 30:  # Log slow or failed requests
                fire_and_forget(
                    f"llm_gateway_{'error' if not success else 'slow_request'}",
                    f"{'Failed' if not success else 'Slow'} request to {provider}: {response_time:.2f}s",
                    ServiceNames.LLM_GATEWAY,
                    {
                        "provider": provider,
                        "response_time": response_time,
                        "tokens_used": tokens_used,
                        "cost": cost,
                        "success": success,
                        "error_type": error_type,
                        "user_id": user_id
                    }
                )

        except Exception as e:
            fire_and_forget(
                "llm_gateway_metrics_error",
                f"Failed to record metrics: {str(e)}",
                ServiceNames.LLM_GATEWAY,
                {"error": str(e)}
            )

    async def record_error(self, request_type: str, error: str, response_time: float):
        """Record an error without full request details."""
        try:
            metrics = RequestMetrics(
                timestamp=time.time(),
                provider="unknown",
                response_time=response_time,
                tokens_used=0,
                cost=0.0,
                success=False,
                error_type=error
            )

            self.request_history.append(metrics)

            fire_and_forget(
                "llm_gateway_error_recorded",
                f"Error recorded: {error}",
                ServiceNames.LLM_GATEWAY,
                {
                    "error": error,
                    "response_time": response_time
                }
            )

        except Exception as e:
            # Avoid recursive error logging
            pass

    async def _update_rolling_metrics(self, metrics: RequestMetrics):
        """Update rolling metrics windows."""
        current_hour = int(metrics.timestamp // 3600)
        current_day = int(metrics.timestamp // 86400)

        # Hourly metrics
        if current_hour not in self.hourly_metrics:
            self.hourly_metrics[current_hour] = {
                "requests": 0,
                "tokens": 0,
                "cost": 0.0,
                "errors": 0,
                "start_time": metrics.timestamp
            }

        hour_data = self.hourly_metrics[current_hour]
        hour_data["requests"] += 1
        hour_data["tokens"] += metrics.tokens_used
        hour_data["cost"] += metrics.cost
        if not metrics.success:
            hour_data["errors"] += 1

        # Daily metrics
        if current_day not in self.daily_metrics:
            self.daily_metrics[current_day] = {
                "requests": 0,
                "tokens": 0,
                "cost": 0.0,
                "errors": 0,
                "start_time": metrics.timestamp
            }

        day_data = self.daily_metrics[current_day]
        day_data["requests"] += 1
        day_data["tokens"] += metrics.tokens_used
        day_data["cost"] += metrics.cost
        if not metrics.success:
            day_data["errors"] += 1

        # Clean old rolling metrics (keep last 24 hours and 7 days)
        current_time = time.time()
        cutoff_hour = int((current_time - 86400) // 3600)  # 24 hours ago
        cutoff_day = int((current_time - 604800) // 86400)  # 7 days ago

        self.hourly_metrics = {
            h: data for h, data in self.hourly_metrics.items() if h > cutoff_hour
        }
        self.daily_metrics = {
            d: data for d, data in self.daily_metrics.items() if d > cutoff_day
        }

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        try:
            total_requests = sum(pm.total_requests for pm in self.provider_metrics.values())
            total_tokens = sum(pm.total_tokens for pm in self.provider_metrics.values())
            total_cost = sum(pm.total_cost for pm in self.provider_metrics.values())

            # Provider breakdown
            requests_by_provider = {
                provider: pm.total_requests
                for provider, pm in self.provider_metrics.items()
            }

            # Performance metrics
            if self.request_history:
                response_times = [req.response_time for req in self.request_history]
                average_response_time = sum(response_times) / len(response_times)
                cache_hit_rate = 0.0  # Would need cache integration

                # Error rate
                error_count = sum(1 for req in self.request_history if not req.success)
                error_rate = (error_count / len(self.request_history)) * 100 if self.request_history else 0
            else:
                average_response_time = 0.0
                cache_hit_rate = 0.0
                error_rate = 0.0

            # Uptime calculation
            uptime_seconds = time.time() - self.start_time
            uptime_percentage = 99.9  # Placeholder - would need actual downtime tracking

            return {
                "total_requests": total_requests,
                "requests_by_provider": requests_by_provider,
                "total_tokens_used": total_tokens,
                "total_cost": round(total_cost, 4),
                "average_response_time": round(average_response_time, 3),
                "cache_hit_rate": round(cache_hit_rate, 3),
                "error_rate": round(error_rate, 2),
                "uptime_percentage": uptime_percentage,
                "collection_period_seconds": uptime_seconds
            }

        except Exception as e:
            return {
                "error": f"Failed to generate metrics summary: {str(e)}",
                "total_requests": 0,
                "total_cost": 0.0,
                "average_response_time": 0.0
            }

    def get_provider_metrics(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed metrics for a specific provider or all providers."""
        if provider:
            if provider not in self.provider_metrics:
                return {"error": f"Provider '{provider}' not found"}

            pm = self.provider_metrics[provider]
            return {
                "provider": provider,
                "total_requests": pm.total_requests,
                "successful_requests": pm.successful_requests,
                "failed_requests": pm.failed_requests,
                "success_rate": round(pm.get_success_rate(), 2),
                "total_tokens": pm.total_tokens,
                "total_cost": round(pm.total_cost, 4),
                "average_response_time": round(pm.get_average_response_time(), 3),
                "average_cost_per_request": round(pm.get_average_cost_per_request(), 4),
                "tokens_per_second": round(pm.get_tokens_per_second(), 2),
                "error_breakdown": pm.error_counts
            }

        # Return all providers
        return {
            provider: self.get_provider_metrics(provider)
            for provider in self.provider_metrics.keys()
        }

    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over the specified time period."""
        current_time = time.time()
        cutoff_time = current_time - (hours * 3600)

        # Filter recent requests
        recent_requests = [
            req for req in self.request_history
            if req.timestamp > cutoff_time
        ]

        if not recent_requests:
            return {"error": f"No requests found in the last {hours} hours"}

        # Calculate trends
        total_requests = len(recent_requests)
        successful_requests = sum(1 for req in recent_requests if req.success)
        failed_requests = total_requests - successful_requests

        avg_response_time = sum(req.response_time for req in recent_requests) / total_requests
        total_tokens = sum(req.tokens_used for req in recent_requests)
        total_cost = sum(req.cost for req in recent_requests)

        # Provider breakdown
        provider_stats = defaultdict(lambda: {"requests": 0, "tokens": 0, "cost": 0.0})
        for req in recent_requests:
            provider_stats[req.provider]["requests"] += 1
            provider_stats[req.provider]["tokens"] += req.tokens_used
            provider_stats[req.provider]["cost"] += req.cost

        return {
            "time_period_hours": hours,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": round((successful_requests / total_requests) * 100, 2),
            "average_response_time": round(avg_response_time, 3),
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 4),
            "requests_per_hour": round(total_requests / hours, 2),
            "tokens_per_hour": round(total_tokens / hours, 2),
            "cost_per_hour": round(total_cost / hours, 4),
            "provider_breakdown": dict(provider_stats)
        }

    def get_cost_analysis(self) -> Dict[str, Any]:
        """Get detailed cost analysis."""
        total_cost = sum(pm.total_cost for pm in self.provider_metrics.values())

        if total_cost == 0:
            return {"message": "No cost data available"}

        # Cost by provider
        cost_by_provider = {
            provider: round(pm.total_cost, 4)
            for provider, pm in self.provider_metrics.items()
        }

        # Cost efficiency (cost per token)
        cost_efficiency = {}
        for provider, pm in self.provider_metrics.items():
            if pm.total_tokens > 0:
                cost_efficiency[provider] = round(pm.total_cost / pm.total_tokens, 6)

        # Most expensive requests
        expensive_requests = sorted(
            self.request_history,
            key=lambda x: x.cost,
            reverse=True
        )[:10]

        expensive_list = [
            {
                "provider": req.provider,
                "cost": round(req.cost, 4),
                "tokens": req.tokens_used,
                "timestamp": req.timestamp
            }
            for req in expensive_requests
            if req.cost > 0
        ]

        return {
            "total_cost": round(total_cost, 4),
            "cost_by_provider": cost_by_provider,
            "cost_efficiency_per_token": cost_efficiency,
            "most_expensive_requests": expensive_list,
            "average_cost_per_request": round(total_cost / max(len(self.request_history), 1), 4)
        }

    def reset_metrics(self):
        """Reset all metrics (useful for testing)."""
        self.provider_metrics.clear()
        self.request_history.clear()
        self.hourly_metrics.clear()
        self.daily_metrics.clear()
        self.start_time = time.time()

        fire_and_forget(
            "llm_gateway_metrics_reset",
            "Metrics have been reset",
            ServiceNames.LLM_GATEWAY
        )
