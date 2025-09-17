"""Tool Registry Storage Module for Discovery Agent.

This module provides persistent storage capabilities for discovered tools
using a simple file-based registry that can be extended to database storage.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional


class ToolRegistryStorage:
    """Persistent storage for discovered tools and discovery results"""

    def __init__(self, storage_path: str = "./data/tool_registry"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Registry files
        self.tools_file = self.storage_path / "discovered_tools.json"
        self.discovery_results_file = self.storage_path / "discovery_results.json"
        self.security_reports_file = self.storage_path / "security_reports.json"

    async def save_discovery_results(self, discovery_results: Dict[str, Any]):
        """Save comprehensive discovery results to persistent storage"""

        try:
            # Load existing results
            existing_results = await self.load_discovery_results()

            # Add new results with timestamp as key
            timestamp = discovery_results.get("timestamp", "unknown")
            existing_results[timestamp] = discovery_results

            # Keep only last 10 discovery runs to prevent file bloat
            if len(existing_results) > 10:
                # Sort by timestamp and keep newest 10
                sorted_keys = sorted(existing_results.keys(), reverse=True)
                existing_results = {k: existing_results[k] for k in sorted_keys[:10]}

            # Save to file
            with open(self.discovery_results_file, 'w') as f:
                json.dump(existing_results, f, indent=2)

            print(f"💾 Saved discovery results to {self.discovery_results_file}")

        except Exception as e:
            print(f"⚠️ Failed to save discovery results: {e}")

    async def save_tools(self, service_name: str, tools: List[Dict[str, Any]]):
        """Save discovered tools for a specific service"""

        try:
            # Load existing tools registry
            registry = await self.load_tools_registry()

            # Update with new tools
            registry[service_name] = {
                "last_updated": "2025-01-17T21:30:00Z",
                "tool_count": len(tools),
                "tools": tools
            }

            # Save to file
            with open(self.tools_file, 'w') as f:
                json.dump(registry, f, indent=2)

            print(f"💾 Saved {len(tools)} tools for {service_name}")

        except Exception as e:
            print(f"⚠️ Failed to save tools for {service_name}: {e}")

    async def save_security_report(self, service_name: str, security_report: Dict[str, Any]):
        """Save security scan results for a service"""

        try:
            # Load existing security reports
            reports = await self.load_security_reports()

            # Add new report
            timestamp = security_report.get("timestamp", "unknown")
            reports[f"{service_name}_{timestamp}"] = security_report

            # Keep only last 20 reports
            if len(reports) > 20:
                sorted_keys = sorted(reports.keys(), reverse=True)
                reports = {k: reports[k] for k in sorted_keys[:20]}

            # Save to file
            with open(self.security_reports_file, 'w') as f:
                json.dump(reports, f, indent=2)

            print(f"🔒 Saved security report for {service_name}")

        except Exception as e:
            print(f"⚠️ Failed to save security report for {service_name}: {e}")

    async def load_discovery_results(self) -> Dict[str, Any]:
        """Load discovery results from persistent storage"""
        try:
            if self.discovery_results_file.exists():
                with open(self.discovery_results_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"⚠️ Failed to load discovery results: {e}")
            return {}

    async def load_tools_registry(self) -> Dict[str, Any]:
        """Load tools registry from persistent storage"""
        try:
            if self.tools_file.exists():
                with open(self.tools_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"⚠️ Failed to load tools registry: {e}")
            return {}

    async def load_security_reports(self) -> Dict[str, Any]:
        """Load security reports from persistent storage"""
        try:
            if self.security_reports_file.exists():
                with open(self.security_reports_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"⚠️ Failed to load security reports: {e}")
            return {}

    async def get_tools_for_service(self, service_name: str) -> List[Dict[str, Any]]:
        """Retrieve tools for a specific service"""
        registry = await self.load_tools_registry()
        service_data = registry.get(service_name, {})
        return service_data.get("tools", [])

    async def get_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve all tools from registry"""
        registry = await self.load_tools_registry()
        return {service: data.get("tools", []) for service, data in registry.items()}

    async def search_tools(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search tools based on criteria"""
        all_tools = await self.get_all_tools()
        matching_tools = []

        for service, tools in all_tools.items():
            for tool in tools:
                matches = True

                # Check category filter
                if "category" in criteria:
                    if tool.get("category") != criteria["category"]:
                        matches = False

                # Check service filter
                if "service" in criteria:
                    if tool.get("service") != criteria["service"]:
                        matches = False

                # Check method filter
                if "method" in criteria:
                    if tool.get("method") != criteria["method"]:
                        matches = False

                # Check readiness filter
                if "langraph_ready" in criteria:
                    if tool.get("langraph_ready", {}).get("ready") != criteria["langraph_ready"]:
                        matches = False

                if matches:
                    matching_tools.append(tool)

        return matching_tools

    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the tool registry"""
        registry = await self.load_tools_registry()
        discovery_results = await self.load_discovery_results()
        security_reports = await self.load_security_reports()

        stats = {
            "services_registered": len(registry),
            "total_tools": sum(data.get("tool_count", 0) for data in registry.values()),
            "discovery_runs": len(discovery_results),
            "security_reports": len(security_reports),
            "categories": set(),
            "service_breakdown": {}
        }

        # Calculate category breakdown and service stats
        for service, data in registry.items():
            tools = data.get("tools", [])
            stats["service_breakdown"][service] = {
                "tools_count": len(tools),
                "categories": set(),
                "methods": set(),
                "langraph_ready": 0
            }

            for tool in tools:
                if tool.get("category"):
                    stats["categories"].add(tool["category"])
                    stats["service_breakdown"][service]["categories"].add(tool["category"])

                if tool.get("method"):
                    stats["service_breakdown"][service]["methods"].add(tool["method"])

                if tool.get("langraph_ready", {}).get("ready"):
                    stats["service_breakdown"][service]["langraph_ready"] += 1

        # Convert sets to lists for JSON serialization
        stats["categories"] = list(stats["categories"])
        for service in stats["service_breakdown"]:
            service_stats = stats["service_breakdown"][service]
            service_stats["categories"] = list(service_stats["categories"])
            service_stats["methods"] = list(service_stats["methods"])

        return stats

    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old discovery results and reports"""
        # This would implement cleanup logic based on timestamps
        # For now, just maintain the size limits we already have
        print(f"🧹 Cleanup completed (maintaining size limits)")


# Create singleton instance
tool_registry_storage = ToolRegistryStorage()
