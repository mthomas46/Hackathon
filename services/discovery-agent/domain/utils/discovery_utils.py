"""Utility functions for service discovery operations

This module contains utility functions used across the discovery agent
for URL normalization, OpenAPI spec extraction, and other common operations.
"""

import re
from typing import Any, Dict, List, Optional

import httpx

from services.shared.infrastructure.config import load_service_config

# Load configuration using standardized system
config = load_service_config(
    service_type="discovery-agent",
    config_file="./config.yaml",  # Optional config file override
)


def normalize_service_url(url: str, service_name: str = None) -> str:
    """Normalize service URL to use Docker internal networking when appropriate"""
    if not url:
        return url

    # If it's a localhost URL and we have a service name, try Docker internal URL
    if "localhost" in url or "127.0.0.1" in url:
        if service_name:
            # Extract port from URL
            port_match = re.search(r":(\d+)", url)
            if port_match:
                port = port_match.group(1)
                return f"http://{service_name}:{port}"

    return url


def extract_endpoints_from_spec(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract endpoints from OpenAPI specification"""
    endpoints = []
    paths = spec.get("paths", {})

    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                endpoint = {
                    "path": path,
                    "method": method.upper(),
                    "operation_id": details.get("operationId"),
                    "summary": details.get("summary"),
                    "description": details.get("description"),
                    "tags": details.get("tags", []),
                    "parameters": details.get("parameters", []),
                    "request_body": details.get("requestBody"),
                    "responses": details.get("responses", {}),
                }
                endpoints.append(endpoint)

    return endpoints


async def fetch_openapi_spec_with_fallback(
    base_url: str, openapi_url: str = None
) -> Optional[Dict[str, Any]]:
    """Fetch OpenAPI spec with fallback to common endpoints"""
    urls_to_try = []

    if openapi_url:
        urls_to_try.append(openapi_url)

    # Common OpenAPI spec locations
    common_paths = ["/openapi.json", "/docs/openapi.json", "/api/openapi.json"]
    for path in common_paths:
        urls_to_try.append(f"{base_url}{path}")

    async with httpx.AsyncClient(timeout=config.timeouts.service_discovery) as client:
        for url in urls_to_try:
            try:
                print(f"🔍 Trying to fetch OpenAPI spec from: {url}")
                response = await client.get(url)
                if response.status_code == 200:
                    spec = response.json()
                    print(f"✅ Successfully fetched OpenAPI spec from: {url}")
                    return spec
                else:
                    print(f"❌ Failed to fetch from {url}: HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ Error fetching from {url}: {e}")
                continue

    return None
