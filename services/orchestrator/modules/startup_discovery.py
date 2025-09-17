"""Ecosystem Startup Tool Discovery Module for Orchestrator Service.

This module provides automatic tool discovery and registration functionality
that runs when the ecosystem starts up. It ensures that all services are
discovered and their LangGraph tools are registered with the orchestrator.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from services.shared.clients import ServiceClients
from services.shared.logging import fire_and_forget
from services.shared.constants_new import ServiceNames

logger = logging.getLogger(__name__)


class StartupToolDiscovery:
    """Handles automatic tool discovery during ecosystem startup."""

    def __init__(self):
        self.client = ServiceClients()
        self.discovery_agent_url = "http://llm-discovery-agent:5045"
        self.discovered_tools = {}

    async def discover_all_tools(self, dry_run: bool = False) -> Dict[str, Any]:
        """Discover tools for all ecosystem services during startup.

        Args:
            dry_run: If True, only simulate discovery without registration

        Returns:
            Dictionary containing discovery results and summary
        """
        logger.info("🚀 Starting ecosystem tool discovery...")

        try:
            # Define all ecosystem services to discover
            ecosystem_services = [
                "prompt_store", "document_store", "code_analyzer",
                "summarizer_hub", "analysis_service", "notification_service",
                "source_agent", "secure_analyzer"
            ]

            # Service URL mappings for Docker network
            service_url_map = {
                "prompt_store": "http://llm-prompt-store:5110",
                "document_store": "http://llm-document-store:5140",
                "code_analyzer": "http://llm-code-analyzer:5150",
                "summarizer_hub": "http://llm-summarizer-hub:5160",
                "analysis_service": "http://llm-analysis-service:5020",
                "notification_service": "http://llm-notification-service:5210",
                "source_agent": "http://llm-source-agent:5000",
                "secure_analyzer": "http://llm-secure-analyzer:5070"
            }

            results = []
            total_tools = 0
            successful_services = 0

            # Discover tools for each service
            for service_name in ecosystem_services:
                try:
                    service_url = service_url_map.get(service_name)
                    if not service_url:
                        logger.warning(f"⚠️ No URL mapping found for service: {service_name}")
                        continue

                    logger.info(f"🔍 Discovering tools for {service_name}...")

                    # Call discovery-agent to discover tools
                    discovery_result = await self._discover_service_tools(
                        service_name, service_url, dry_run
                    )

                    if discovery_result["status"] == "success":
                        tools_count = discovery_result["tools_discovered"]
                        total_tools += tools_count
                        successful_services += 1

                        # Store discovered tools for later use
                        self.discovered_tools[service_name] = discovery_result

                        logger.info(f"✅ {service_name}: {tools_count} tools discovered")

                    results.append(discovery_result)

                except Exception as e:
                    error_msg = f"Failed to discover tools for {service_name}: {str(e)}"
                    logger.error(f"❌ {error_msg}")

                    results.append({
                        "service_name": service_name,
                        "status": "error",
                        "error": str(e)
                    })

            # Create summary
            summary = {
                "total_services": len(ecosystem_services),
                "successful_discoveries": successful_services,
                "failed_discoveries": len(ecosystem_services) - successful_services,
                "total_tools_discovered": total_tools,
                "dry_run": dry_run,
                "timestamp": "2024-01-01T00:00:00Z"  # Will be updated with actual timestamp
            }

            # Log final results
            if dry_run:
                logger.info(f"🔍 DRY RUN: Would discover {total_tools} tools from {successful_services} services")
            else:
                logger.info(f"🎉 Tool discovery completed: {total_tools} tools registered from {successful_services} services")

            # Fire and forget logging event
            fire_and_forget(
                "startup_tool_discovery_completed",
                f"Ecosystem tool discovery completed: {total_tools} tools from {successful_services} services",
                ServiceNames.ORCHESTRATOR,
                {
                    "summary": summary,
                    "results": results
                }
            )

            return {
                "summary": summary,
                "results": results,
                "discovered_tools": self.discovered_tools
            }

        except Exception as e:
            error_msg = f"Ecosystem tool discovery failed: {str(e)}"
            logger.error(f"💥 {error_msg}")

            fire_and_forget(
                "startup_tool_discovery_failed",
                error_msg,
                ServiceNames.ORCHESTRATOR,
                {"error": str(e)}
            )
            raise

    async def _discover_service_tools(self, service_name: str, service_url: str,
                                    dry_run: bool) -> Dict[str, Any]:
        """Discover tools for a specific service."""
        try:
            # Prepare discovery request
            discovery_payload = {
                "service_name": service_name,
                "service_url": service_url,
                "tool_categories": None,  # Discover all categories
                "dry_run": dry_run
            }

            # Call discovery-agent
            response = await self.client.post_json(
                f"{self.discovery_agent_url}/discover/tools",
                discovery_payload
            )

            if response.get("success"):
                data = response["data"]
                return {
                    "service_name": service_name,
                    "status": "success",
                    "tools_discovered": data["tools_discovered"],
                    "categories": data.get("categories", []),
                    "registration_status": data.get("registration_status", "pending"),
                    "tools": data.get("tools", [])
                }
            else:
                return {
                    "service_name": service_name,
                    "status": "error",
                    "error": response.get("message", "Discovery failed")
                }

        except Exception as e:
            return {
                "service_name": service_name,
                "status": "error",
                "error": str(e)
            }

    async def get_discovered_tools(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get discovered tools for a service or all services."""
        if service_name:
            return self.discovered_tools.get(service_name, {})
        return self.discovered_tools

    async def refresh_tools(self, service_name: Optional[str] = None,
                           dry_run: bool = False) -> Dict[str, Any]:
        """Refresh tool discovery for specific service or all services."""
        if service_name:
            # Refresh tools for specific service
            service_url_map = {
                "prompt_store": "http://llm-prompt-store:5110",
                "document_store": "http://llm-document-store:5140",
                "code_analyzer": "http://llm-code-analyzer:5150",
                "summarizer_hub": "http://llm-summarizer-hub:5160",
                "analysis_service": "http://llm-analysis-service:5020",
                "notification_service": "http://llm-notification-service:5210",
                "source_agent": "http://llm-source-agent:5000",
                "secure_analyzer": "http://llm-secure-analyzer:5070"
            }

            service_url = service_url_map.get(service_name)
            if not service_url:
                raise ValueError(f"Unknown service: {service_name}")

            result = await self._discover_service_tools(service_name, service_url, dry_run)
            if result["status"] == "success":
                self.discovered_tools[service_name] = result
            return result
        else:
            # Refresh all tools
            return await self.discover_all_tools(dry_run)


# Global startup discovery instance
startup_discovery = StartupToolDiscovery()


async def initialize_ecosystem_tools(dry_run: bool = False) -> Dict[str, Any]:
    """Initialize tool discovery for the entire ecosystem.

    This function should be called during orchestrator startup to ensure
    all services are discovered and their tools are registered.

    Args:
        dry_run: If True, simulate discovery without actual registration

    Returns:
        Dictionary containing discovery results
    """
    logger.info("🌟 Initializing ecosystem tool discovery...")

    try:
        results = await startup_discovery.discover_all_tools(dry_run=dry_run)

        if not dry_run:
            logger.info("✅ Ecosystem tools initialized and registered")
        else:
            logger.info("🔍 DRY RUN: Ecosystem tools would be initialized")

        return results

    except Exception as e:
        logger.error(f"💥 Failed to initialize ecosystem tools: {str(e)}")
        raise


async def refresh_service_tools(service_name: str, dry_run: bool = False) -> Dict[str, Any]:
    """Refresh tools for a specific service.

    Args:
        service_name: Name of the service to refresh tools for
        dry_run: If True, simulate refresh without actual registration

    Returns:
        Dictionary containing refresh results
    """
    logger.info(f"🔄 Refreshing tools for service: {service_name}")

    try:
        results = await startup_discovery.refresh_tools(service_name, dry_run)

        if results["status"] == "success":
            logger.info(f"✅ Tools refreshed for {service_name}: {results['tools_discovered']} tools")
        else:
            logger.error(f"❌ Failed to refresh tools for {service_name}: {results.get('error', 'Unknown error')}")

        return results

    except Exception as e:
        logger.error(f"💥 Failed to refresh tools for {service_name}: {str(e)}")
        raise
