"""
API Catalog Manager

Manages the centralized catalog of all ecosystem APIs including:
- OpenAPI specification parsing and storage
- API search and filtering capabilities
- API documentation generation
- API versioning and lifecycle management
- API relationship and dependency mapping
"""

import asyncio
import json
import re
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict

from ...modules.discovery.client import DiscoveryClient
from ...config import Config


class APICatalogEntry:
    """Represents a single API endpoint in the catalog."""

    def __init__(self, service_name: str, endpoint_data: Dict[str, Any]):
        self.service_name = service_name
        self.path = endpoint_data.get("path", "")
        self.method = endpoint_data.get("method", "").upper()
        self.summary = endpoint_data.get("summary", "")
        self.description = endpoint_data.get("description", "")
        self.tags = endpoint_data.get("tags", [])
        self.parameters = endpoint_data.get("parameters", [])
        self.responses = endpoint_data.get("responses", {})
        self.deprecated = endpoint_data.get("deprecated", False)
        self.security = endpoint_data.get("security", [])
        self.last_updated = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "service_name": self.service_name,
            "path": self.path,
            "method": self.method,
            "summary": self.summary,
            "description": self.description,
            "tags": self.tags,
            "parameters": self.parameters,
            "responses": self.responses,
            "deprecated": self.deprecated,
            "security": self.security,
            "last_updated": self.last_updated.isoformat()
        }

    def matches_search(self, query: str) -> bool:
        """Check if this entry matches a search query."""
        search_text = f"{self.summary} {self.description} {self.path} {' '.join(self.tags)}".lower()
        return query.lower() in search_text

    def matches_filters(self, service: str = "", method: str = "", tags: List[str] = None) -> bool:
        """Check if this entry matches the given filters."""
        if service and service.lower() not in self.service_name.lower():
            return False
        if method and self.method != method.upper():
            return False
        if tags and not any(tag in self.tags for tag in tags):
            return False
        return True


class APICatalogManager:
    """Manages the centralized API catalog for the ecosystem."""

    def __init__(self, discovery_client: DiscoveryClient, config: Config):
        self.discovery_client = discovery_client
        self.config = config
        self.catalog: Dict[str, List[APICatalogEntry]] = {}
        self.service_metadata: Dict[str, Dict[str, Any]] = {}
        self.last_refresh = None
        self.refresh_interval = config.api_polling_interval

    async def refresh_catalog(self, force: bool = False) -> Dict[str, Any]:
        """Refresh the API catalog from all services."""
        now = datetime.now()

        # Check if refresh is needed
        if not force and self.last_refresh and \
           (now - self.last_refresh).seconds < self.refresh_interval:
            return {
                "refreshed": False,
                "reason": "Refresh interval not elapsed",
                "last_refresh": self.last_refresh.isoformat(),
                "catalog_size": sum(len(entries) for entries in self.catalog.values())
            }

        try:
            # Get all services
            services = await self.discovery_client.get_all_services()

            new_catalog = {}
            new_metadata = {}
            total_endpoints = 0
            processed_services = 0

            for service in services:
                service_name = service.get("name")
                if not service_name:
                    continue

                try:
                    # Get OpenAPI spec for the service
                    openapi_spec = await self.discovery_client.get_openapi_spec(service_name)

                    if openapi_spec:
                        # Parse the spec into catalog entries
                        entries = self._parse_openapi_spec(service_name, openapi_spec)
                        new_catalog[service_name] = entries
                        total_endpoints += len(entries)

                        # Store service metadata
                        new_metadata[service_name] = {
                            "service_info": service,
                            "openapi_version": openapi_spec.get("openapi", "unknown"),
                            "endpoints_count": len(entries),
                            "last_updated": now.isoformat()
                        }

                        processed_services += 1
                    else:
                        # Service without OpenAPI spec
                        new_catalog[service_name] = []
                        new_metadata[service_name] = {
                            "service_info": service,
                            "openapi_version": None,
                            "endpoints_count": 0,
                            "last_updated": now.isoformat(),
                            "warning": "No OpenAPI specification available"
                        }

                except Exception as e:
                    print(f"Error processing service {service_name}: {e}")
                    new_catalog[service_name] = []
                    new_metadata[service_name] = {
                        "service_info": service,
                        "error": str(e),
                        "last_updated": now.isoformat()
                    }

            # Update catalog
            self.catalog = new_catalog
            self.service_metadata = new_metadata
            self.last_refresh = now

            return {
                "refreshed": True,
                "services_processed": processed_services,
                "total_endpoints": total_endpoints,
                "catalog_size": len(new_catalog),
                "timestamp": now.isoformat()
            }

        except Exception as e:
            return {
                "refreshed": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _parse_openapi_spec(self, service_name: str, spec: Dict[str, Any]) -> List[APICatalogEntry]:
        """Parse OpenAPI specification into catalog entries."""
        entries = []
        paths = spec.get("paths", {})

        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue

            for method, details in methods.items():
                if not isinstance(details, dict):
                    continue

                endpoint_data = {
                    "path": path,
                    "method": method,
                    "summary": details.get("summary", ""),
                    "description": details.get("description", ""),
                    "tags": details.get("tags", []),
                    "parameters": details.get("parameters", []),
                    "responses": details.get("responses", {}),
                    "deprecated": details.get("deprecated", False),
                    "security": details.get("security", [])
                }

                entry = APICatalogEntry(service_name, endpoint_data)
                entries.append(entry)

        return entries

    def search_catalog(self, query: str = "", service: str = "", method: str = "",
                      tags: List[str] = None, deprecated: bool = None) -> List[Dict[str, Any]]:
        """Search the API catalog with various filters."""
        results = []

        for service_name, entries in self.catalog.items():
            for entry in entries:
                # Apply filters
                if not entry.matches_filters(service, method, tags or []):
                    continue

                if deprecated is not None and entry.deprecated != deprecated:
                    continue

                if query and not entry.matches_search(query):
                    continue

                # Add to results
                result = entry.to_dict()
                result["relevance_score"] = self._calculate_relevance_score(entry, query, tags or [])
                results.append(result)

        # Sort by relevance score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        return results

    def _calculate_relevance_score(self, entry: APICatalogEntry, query: str, tags: List[str]) -> float:
        """Calculate relevance score for search results."""
        score = 0.0

        if query:
            # Exact matches in summary get highest score
            if query.lower() in entry.summary.lower():
                score += 10.0
            # Matches in description
            elif query.lower() in entry.description.lower():
                score += 5.0
            # Matches in path
            elif query.lower() in entry.path.lower():
                score += 3.0
            # Fuzzy matches
            else:
                score += 1.0

        # Tag matches
        if tags:
            matching_tags = sum(1 for tag in tags if tag in entry.tags)
            score += matching_tags * 2.0

        # Deprecation penalty
        if entry.deprecated:
            score -= 1.0

        return score

    def get_service_catalog(self, service_name: str) -> Dict[str, Any]:
        """Get the complete catalog for a specific service."""
        if service_name not in self.catalog:
            return {"error": f"Service {service_name} not found in catalog"}

        entries = [entry.to_dict() for entry in self.catalog[service_name]]
        metadata = self.service_metadata.get(service_name, {})

        # Group by tags for better organization
        by_tags = defaultdict(list)
        for entry in entries:
            for tag in entry.get("tags", ["untagged"]):
                by_tags[tag].append(entry)

        return {
            "service_name": service_name,
            "metadata": metadata,
            "total_endpoints": len(entries),
            "endpoints": entries,
            "endpoints_by_tag": dict(by_tags),
            "last_updated": self.last_refresh.isoformat() if self.last_refresh else None
        }

    def get_catalog_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the API catalog."""
        total_services = len(self.catalog)
        total_endpoints = sum(len(entries) for entries in self.catalog.values())

        # Count by HTTP methods
        method_counts = defaultdict(int)
        tag_counts = defaultdict(int)
        deprecated_count = 0

        for service_entries in self.catalog.values():
            for entry in service_entries:
                method_counts[entry.method] += 1

                for tag in entry.tags:
                    tag_counts[tag] += 1

                if entry.deprecated:
                    deprecated_count += 1

        # Services with most endpoints
        service_stats = []
        for service_name, entries in self.catalog.items():
            metadata = self.service_metadata.get(service_name, {})
            service_stats.append({
                "service_name": service_name,
                "endpoints_count": len(entries),
                "has_openapi": metadata.get("openapi_version") is not None,
                "last_updated": metadata.get("last_updated")
            })

        service_stats.sort(key=lambda x: x["endpoints_count"], reverse=True)

        return {
            "total_services": total_services,
            "total_endpoints": total_endpoints,
            "method_distribution": dict(method_counts),
            "tag_distribution": dict(tag_counts),
            "deprecated_endpoints": deprecated_count,
            "services_by_size": service_stats[:10],  # Top 10
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
            "catalog_health": self._assess_catalog_health()
        }

    def _assess_catalog_health(self) -> Dict[str, Any]:
        """Assess the overall health of the API catalog."""
        if not self.catalog:
            return {"status": "empty", "score": 0}

        total_services = len(self.catalog)
        services_with_openapi = sum(
            1 for metadata in self.service_metadata.values()
            if metadata.get("openapi_version") is not None
        )

        total_endpoints = sum(len(entries) for entries in self.catalog.values())
        deprecated_endpoints = sum(
            1 for entries in self.catalog.values()
            for entry in entries if entry.deprecated
        )

        # Calculate health score (0-100)
        openapi_coverage = services_with_openapi / total_services if total_services > 0 else 0
        deprecation_rate = deprecated_endpoints / total_endpoints if total_endpoints > 0 else 0

        health_score = (openapi_coverage * 70) + ((1 - deprecation_rate) * 30)

        # Determine status
        if health_score >= 80:
            status = "excellent"
        elif health_score >= 60:
            status = "good"
        elif health_score >= 40:
            status = "fair"
        else:
            status = "poor"

        return {
            "status": status,
            "score": round(health_score, 1),
            "openapi_coverage": round(openapi_coverage * 100, 1),
            "deprecation_rate": round(deprecation_rate * 100, 1),
            "recommendations": self._generate_health_recommendations(
                openapi_coverage, deprecation_rate
            )
        }

    def _generate_health_recommendations(self, openapi_coverage: float,
                                       deprecation_rate: float) -> List[str]:
        """Generate health improvement recommendations."""
        recommendations = []

        if openapi_coverage < 0.8:
            recommendations.append("Increase OpenAPI specification coverage across services")

        if deprecation_rate > 0.1:
            recommendations.append("Review and update deprecated API endpoints")

        if openapi_coverage < 0.9:
            recommendations.append("Standardize OpenAPI documentation practices")

        if not recommendations:
            recommendations.append("Catalog health is excellent - maintain current standards")

        return recommendations

    def get_api_relationships(self) -> Dict[str, Any]:
        """Analyze and return API relationships and dependencies."""
        relationships = {
            "service_dependencies": {},
            "api_patterns": {},
            "common_endpoints": defaultdict(list)
        }

        # Analyze service dependencies based on API calls
        for service_name, entries in self.catalog.items():
            dependencies = set()

            for entry in entries:
                # Look for service-to-service API calls in responses/examples
                # This is a simplified analysis - in practice would need more sophisticated parsing
                if "responses" in entry.responses:
                    for response_data in entry.responses.values():
                        if isinstance(response_data, dict):
                            # Check for service references in examples or descriptions
                            example = response_data.get("example", "")
                            if any(svc in example for svc in self.catalog.keys() if svc != service_name):
                                for svc in self.catalog.keys():
                                    if svc != service_name and svc in example:
                                        dependencies.add(svc)

            relationships["service_dependencies"][service_name] = list(dependencies)

            # Find common endpoint patterns
            for entry in entries:
                pattern = self._extract_endpoint_pattern(entry.path)
                if pattern:
                    relationships["api_patterns"].setdefault(pattern, []).append({
                        "service": service_name,
                        "method": entry.method,
                        "path": entry.path
                    })

                # Group by common endpoint types
                if "/health" in entry.path:
                    relationships["common_endpoints"]["health"].append(f"{service_name}:{entry.method}")
                elif "/metrics" in entry.path:
                    relationships["common_endpoints"]["metrics"].append(f"{service_name}:{entry.method}")
                elif "/docs" in entry.path or "/openapi" in entry.path:
                    relationships["common_endpoints"]["documentation"].append(f"{service_name}:{entry.method}")

        return relationships

    def _extract_endpoint_pattern(self, path: str) -> Optional[str]:
        """Extract common endpoint patterns from paths."""
        # Remove parameter placeholders
        pattern = re.sub(r'\{[^}]+\}', '{}', path)

        # Common patterns
        if pattern.startswith("/api/v") and "/{" in pattern:
            return "versioned_resource"
        elif "/health" in pattern:
            return "health_check"
        elif "/metrics" in pattern:
            return "metrics"
        elif pattern.count("/") == 2 and not "{" in pattern:
            return "simple_endpoint"
        elif "/search" in pattern or "/query" in pattern:
            return "search_query"
        elif "/batch" in pattern or "/bulk" in pattern:
            return "batch_operation"

        return None

    def export_catalog(self, format: str = "json") -> str:
        """Export the API catalog in various formats."""
        catalog_data = {
            "metadata": {
                "export_time": datetime.now().isoformat(),
                "total_services": len(self.catalog),
                "total_endpoints": sum(len(entries) for entries in self.catalog.values()),
                "format": format
            },
            "services": {}
        }

        for service_name, entries in self.catalog.items():
            catalog_data["services"][service_name] = {
                "metadata": self.service_metadata.get(service_name, {}),
                "endpoints": [entry.to_dict() for entry in entries]
            }

        if format == "json":
            return json.dumps(catalog_data, indent=2, default=str)
        elif format == "yaml":
            try:
                import yaml
                return yaml.dump(catalog_data, default_flow_style=False)
            except ImportError:
                return json.dumps(catalog_data, indent=2, default=str)
        else:
            return json.dumps(catalog_data, indent=2, default=str)
