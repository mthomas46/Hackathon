"""Services Overview monitoring infrastructure for Frontend service.

Provides comprehensive system-wide monitoring and health dashboard
for all services in the LLM Documentation Ecosystem.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from services.shared.utilities import utc_now
from .shared_utils import (
    get_orchestrator_url,
    get_doc_store_url,
    get_prompt_store_url,
    get_analysis_service_url,
    get_summarizer_hub_url,
    get_log_collector_url,
    get_bedrock_proxy_url,
    get_code_analyzer_url,
    get_discovery_agent_url,
    get_github_mcp_url,
    get_interpreter_url,
    get_memory_agent_url,
    get_notification_service_url,
    get_secure_analyzer_url,
    get_source_agent_url,
    get_frontend_clients
)


class ServicesOverviewMonitor:
    """Comprehensive monitor for all services in the ecosystem."""

    def __init__(self):
        self._service_status = {}
        self._system_metrics = {}
        self._cache_ttl = 15  # Cache for 15 seconds for real-time overview

    def is_cache_fresh(self, cache_key: str) -> bool:
        """Check if cache is still fresh."""
        cache_time = getattr(self, f"_{cache_key}_updated", None)
        if not cache_time:
            return False
        return (utc_now() - cache_time).total_seconds() < self._cache_ttl

    async def get_services_overview(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get comprehensive overview of all services in the ecosystem."""
        if not force_refresh and self.is_cache_fresh("overview"):
            return getattr(self, "_overview_cache", {})

        try:
            clients = get_frontend_clients()

            # Define all services and their health endpoints
            services = {
                "orchestrator": {"url_func": get_orchestrator_url, "endpoint": "/health"},
                "doc_store": {"url_func": get_doc_store_url, "endpoint": "/health"},
                "prompt-store": {"url_func": get_prompt_store_url, "endpoint": "/health"},
                "analysis-service": {"url_func": get_analysis_service_url, "endpoint": "/health"},
                "summarizer-hub": {"url_func": get_summarizer_hub_url, "endpoint": "/health"},
                "log-collector": {"url_func": get_log_collector_url, "endpoint": "/health"},
                "bedrock-proxy": {"url_func": get_bedrock_proxy_url, "endpoint": "/health"},
                "code-analyzer": {"url_func": get_code_analyzer_url, "endpoint": "/health"},
                "discovery-agent": {"url_func": get_discovery_agent_url, "endpoint": "/health"},
                "github-mcp": {"url_func": get_github_mcp_url, "endpoint": "/health"},
                "interpreter": {"url_func": get_interpreter_url, "endpoint": "/health"},
                "memory-agent": {"url_func": get_memory_agent_url, "endpoint": "/health"},
                "notification-service": {"url_func": get_notification_service_url, "endpoint": "/health"},
                "secure-analyzer": {"url_func": get_secure_analyzer_url, "endpoint": "/health"},
                "source-agent": {"url_func": get_source_agent_url, "endpoint": "/health"},
                "frontend": {"status": "healthy", "version": "2.0.0", "description": "Frontend service is operational"}
            }

            # Collect status from all services
            service_statuses = {}
            healthy_count = 0
            unhealthy_count = 0

            for service_name, config in services.items():
                try:
                    if service_name == "frontend":
                        status_data = config
                    else:
                        url_func = config["url_func"]
                        endpoint = config["endpoint"]
                        base_url = url_func()

                        response = await clients.get_json(f"{base_url}{endpoint}")
                        status_data = response

                    service_statuses[service_name] = {
                        "name": service_name,
                        "status": status_data.get("status", "unknown"),
                        "version": status_data.get("version", "unknown"),
                        "description": status_data.get("description", f"{service_name} service status"),
                        "last_checked": utc_now().isoformat(),
                        "response": status_data
                    }

                    if status_data.get("status") == "healthy":
                        healthy_count += 1
                    else:
                        unhealthy_count += 1

                except Exception as e:
                    service_statuses[service_name] = {
                        "name": service_name,
                        "status": "unhealthy",
                        "version": "unknown",
                        "description": f"Failed to check {service_name}: {str(e)}",
                        "last_checked": utc_now().isoformat(),
                        "error": str(e)
                    }
                    unhealthy_count += 1

            # Calculate system metrics
            total_services = len(services)
            system_health = "healthy" if unhealthy_count == 0 else ("degraded" if unhealthy_count < total_services * 0.5 else "critical")

            system_metrics = {
                "total_services": total_services,
                "healthy_services": healthy_count,
                "unhealthy_services": unhealthy_count,
                "system_health": system_health,
                "uptime_percentage": round((healthy_count / total_services) * 100, 1) if total_services > 0 else 0,
                "last_updated": utc_now().isoformat()
            }

            # Group services by category
            service_categories = {
                "core_infrastructure": ["orchestrator", "doc_store", "prompt-store", "frontend"],
                "analysis_services": ["analysis-service", "code-analyzer", "secure-analyzer"],
                "ai_ml_services": ["summarizer-hub", "bedrock-proxy", "interpreter"],
                "integration_services": ["discovery-agent", "github-mcp", "source-agent"],
                "operational_services": ["log-collector", "memory-agent", "notification-service"]
            }

            categorized_services = {}
            for category, service_list in service_categories.items():
                categorized_services[category] = {
                    "services": [service_statuses.get(s, {}) for s in service_list if s in service_statuses],
                    "healthy_count": sum(1 for s in service_list if service_statuses.get(s, {}).get("status") == "healthy"),
                    "total_count": len(service_list),
                    "health_percentage": round((sum(1 for s in service_list if service_statuses.get(s, {}).get("status") == "healthy") / len(service_list)) * 100, 1) if service_list else 0
                }

            overview_data = {
                "system_metrics": system_metrics,
                "service_statuses": service_statuses,
                "categorized_services": categorized_services,
                "service_categories": service_categories,
                "last_updated": utc_now().isoformat()
            }

            self._overview_cache = overview_data
            self._overview_updated = utc_now()

            return overview_data

        except Exception as e:
            return {
                "error": str(e),
                "system_metrics": {"system_health": "unknown", "total_services": 0},
                "service_statuses": {},
                "categorized_services": {},
                "last_updated": utc_now().isoformat()
            }

    async def get_service_health_details(self, service_name: str) -> Dict[str, Any]:
        """Get detailed health information for a specific service."""
        try:
            clients = get_frontend_clients()

            # Map service names to their URL functions and detailed endpoints
            service_configs = {
                "orchestrator": (get_orchestrator_url, "/health"),
                "doc_store": (get_doc_store_url, "/health"),
                "prompt-store": (get_prompt_store_url, "/health"),
                "analysis-service": (get_analysis_service_url, "/health"),
                "summarizer-hub": (get_summarizer_hub_url, "/health"),
                "log-collector": (get_log_collector_url, "/health"),
                "bedrock-proxy": (get_bedrock_proxy_url, "/health"),
                "code-analyzer": (get_code_analyzer_url, "/health"),
                "discovery-agent": (get_discovery_agent_url, "/health"),
                "github-mcp": (get_github_mcp_url, "/health"),
                "interpreter": (get_interpreter_url, "/health"),
                "memory-agent": (get_memory_agent_url, "/health"),
                "notification-service": (get_notification_service_url, "/health"),
                "secure-analyzer": (get_secure_analyzer_url, "/health"),
                "source-agent": (get_source_agent_url, "/health")
            }

            if service_name not in service_configs:
                return {"error": f"Unknown service: {service_name}"}

            url_func, endpoint = service_configs[service_name]
            base_url = url_func()

            response = await clients.get_json(f"{base_url}{endpoint}")

            return {
                "service_name": service_name,
                "health_data": response,
                "url": base_url,
                "endpoint": endpoint,
                "last_checked": utc_now().isoformat()
            }

        except Exception as e:
            return {
                "service_name": service_name,
                "error": str(e),
                "last_checked": utc_now().isoformat()
            }


# Global instance
services_overview_monitor = ServicesOverviewMonitor()
