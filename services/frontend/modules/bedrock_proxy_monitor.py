"""Bedrock Proxy monitoring infrastructure for Frontend service.

Provides visualization and monitoring capabilities for bedrock proxy
service AI invocations and template-based responses.
"""
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta

from services.shared.utilities import utc_now
from .shared_utils import get_bedrock_proxy_url, get_frontend_clients


class BedrockProxyMonitor:
    """Monitor for bedrock proxy service invocations and responses."""

    def __init__(self):
        self._invocations = []
        self._cache_ttl = 60  # Cache for 60 seconds

    def is_cache_fresh(self, cache_key: str) -> bool:
        """Check if cache is still fresh."""
        cache_time = self._activity_cache.get(f"{cache_key}_updated")
        if not cache_time:
            return False
        return (utc_now() - cache_time).total_seconds() < self._cache_ttl

    async def get_proxy_status(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get comprehensive bedrock proxy service status."""
        if not force_refresh and self.is_cache_fresh("status"):
            return self._activity_cache.get("status", {})

        try:
            clients = get_frontend_clients()
            proxy_url = get_bedrock_proxy_url()

            # Get health status
            health_response = await clients.get_json(f"{proxy_url}/health")

            status_data = {
                "health": health_response,
                "invocation_stats": self._calculate_invocation_stats(),
                "recent_invocations": self._invocations[-10:] if self._invocations else [],  # Last 10 invocations
                "last_updated": utc_now().isoformat()
            }

            self._activity_cache["status"] = status_data
            self._activity_cache["status_updated"] = utc_now()

            return status_data

        except Exception as e:
            return {
                "error": str(e),
                "health": {},
                "invocation_stats": {},
                "recent_invocations": [],
                "last_updated": utc_now().isoformat()
            }

    async def invoke_ai(self, prompt: str, template: Optional[str] = None, format: Optional[str] = None, title: Optional[str] = None, model: Optional[str] = None, region: Optional[str] = None, **params) -> Dict[str, Any]:
        """Invoke AI through the bedrock proxy and cache the result."""
        try:
            clients = get_frontend_clients()
            proxy_url = get_bedrock_proxy_url()

            payload = {
                "prompt": prompt,
                "template": template,
                "format": format,
                "title": title,
                "model": model,
                "region": region,
                **params
            }

            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}

            response = await clients.post_json(f"{proxy_url}/invoke", payload)

            if response.get("success") or "response" in response:
                # Cache the invocation
                invocation_result = {
                    "id": f"invocation_{utc_now().isoformat()}",
                    "timestamp": utc_now().isoformat(),
                    "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    "template": template,
                    "format": format,
                    "title": title,
                    "model": model,
                    "region": region,
                    "response": response.get("response", response),
                    "params": params
                }

                self._invocations.insert(0, invocation_result)  # Add to front

                # Keep only last 50 invocations
                if len(self._invocations) > 50:
                    self._invocations = self._invocations[:50]

                return {
                    "success": True,
                    "invocation_id": invocation_result["id"],
                    "response": response
                }

            return {
                "success": False,
                "error": "Invocation failed",
                "response": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": None
            }

    def _calculate_invocation_stats(self) -> Dict[str, Any]:
        """Calculate statistics from cached invocations."""
        if not self._invocations:
            return {
                "total_invocations": 0,
                "unique_models": 0,
                "unique_templates": 0,
                "average_response_time": 0
            }

        total = len(self._invocations)

        # Models used
        models = set()
        templates = set()

        for inv in self._invocations:
            if inv.get("model"):
                models.add(inv["model"])
            if inv.get("template"):
                templates.add(inv["template"])

        return {
            "total_invocations": total,
            "unique_models": len(models),
            "unique_templates": len(templates),
            "models_used": list(models),
            "templates_used": list(templates)
        }

    def get_invocation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent invocation history."""
        return self._invocations[:limit]


# Global instance
bedrock_proxy_monitor = BedrockProxyMonitor()

# Initialize activity cache
bedrock_proxy_monitor._activity_cache = {}
