"""Service Discovery Domain Service

Implements the core business logic for discovering services and their APIs.
"""

import httpx
import time
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin

from ..entities import Service, Endpoint, DiscoveryResult


async def fetch_openapi_spec(url: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Fetch OpenAPI specification from a URL.
    
    Tries common OpenAPI spec locations:
    - /openapi.json
    - /docs/openapi.json
    - /api/openapi.json
    - The provided URL directly
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        # Try the provided URL first
        urls_to_try = [
            url,
            urljoin(url, "/openapi.json"),
            urljoin(url, "/docs/openapi.json"),
            urljoin(url, "/api/openapi.json"),
            urljoin(url, "/api/v1/openapi.json"),
        ]
        
        last_error = None
        for spec_url in urls_to_try:
            try:
                response = await client.get(spec_url)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                last_error = e
                continue
        
        # If we got here, all attempts failed
        raise Exception(f"Failed to fetch OpenAPI spec from {url}: {last_error}")


def parse_openapi_spec(spec: Dict[str, Any]) -> List[Endpoint]:
    """
    Parse OpenAPI specification and extract endpoints.
    
    Returns:
        List of Endpoint entities
    """
    endpoints = []
    paths = spec.get("paths", {})
    
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
            
        for method, operation in methods.items():
            # Skip non-HTTP methods (like $ref, parameters, etc.)
            if method.startswith("$") or method in ["parameters", "servers"]:
                continue
                
            if not isinstance(operation, dict):
                continue
            
            # Extract parameters
            parameters = []
            for param in operation.get("parameters", []):
                if isinstance(param, dict):
                    parameters.append({
                        "name": param.get("name"),
                        "in": param.get("in"),
                        "required": param.get("required", False),
                        "schema": param.get("schema", {}),
                        "description": param.get("description"),
                    })
            
            # Extract responses
            responses = {}
            for status_code, response_data in operation.get("responses", {}).items():
                if isinstance(response_data, dict):
                    responses[status_code] = {
                        "description": response_data.get("description", ""),
                        "content": response_data.get("content", {}),
                    }
            
            # Create endpoint entity
            endpoint = Endpoint(
                path=path,
                method=method.upper(),
                summary=operation.get("summary"),
                description=operation.get("description"),
                parameters=parameters,
                responses=responses,
                tags=operation.get("tags", []),
            )
            endpoints.append(endpoint)
    
    return endpoints


async def discover_service(
    service_name: str,
    base_url: str,
    openapi_url: Optional[str] = None,
    openapi_content: Optional[Dict[str, Any]] = None
) -> DiscoveryResult:
    """
    Discover a service by fetching and parsing its OpenAPI specification.
    
    Args:
        service_name: Name of the service to discover
        base_url: Base URL of the service
        openapi_url: Optional explicit OpenAPI spec URL
        openapi_content: Optional inline OpenAPI content
        
    Returns:
        DiscoveryResult with discovered service information
    """
    start_time = time.time()
    
    try:
        # Get OpenAPI spec
        if openapi_content:
            spec = openapi_content
        elif openapi_url:
            spec = await fetch_openapi_spec(openapi_url)
        else:
            # Try to fetch from base URL
            spec = await fetch_openapi_spec(base_url)
        
        # Parse endpoints
        endpoints = parse_openapi_spec(spec)
        
        # Extract service metadata from spec
        info = spec.get("info", {})
        version = info.get("version", "unknown")
        description = info.get("description", "")
        
        # Create service entity
        service = Service(
            name=service_name,
            base_url=base_url,
            openapi_url=openapi_url or base_url + "/openapi.json",
            version=version,
            description=description,
            endpoints=endpoints,
            metadata={
                "openapi_version": spec.get("openapi", "3.0.0"),
                "title": info.get("title", service_name),
                "servers": spec.get("servers", []),
            },
            status="discovered",
        )
        
        # Calculate discovery duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Return successful result
        return DiscoveryResult(
            service=service,
            success=True,
            discovery_duration_ms=duration_ms,
            metadata={
                "endpoint_count": len(endpoints),
                "openapi_version": spec.get("openapi", "3.0.0"),
            }
        )
        
    except Exception as e:
        # Return failure result
        duration_ms = (time.time() - start_time) * 1000
        
        # Create a minimal service entity for the failed result
        service = Service(
            name=service_name,
            base_url=base_url,
            status="error",
        )
        
        return DiscoveryResult(
            service=service,
            success=False,
            error_message=str(e),
            discovery_duration_ms=duration_ms,
        )


async def discover_multiple_services(
    services: List[Dict[str, str]]
) -> List[DiscoveryResult]:
    """
    Discover multiple services concurrently.
    
    Args:
        services: List of service definitions with 'name' and 'base_url'
        
    Returns:
        List of DiscoveryResult objects
    """
    import asyncio
    
    tasks = []
    for service_def in services:
        task = discover_service(
            service_name=service_def.get("name", "unknown"),
            base_url=service_def.get("base_url", ""),
            openapi_url=service_def.get("openapi_url"),
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Convert exceptions to failed DiscoveryResults
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            service_def = services[i]
            service = Service(
                name=service_def.get("name", "unknown"),
                base_url=service_def.get("base_url", ""),
                status="error",
            )
            processed_results.append(DiscoveryResult(
                service=service,
                success=False,
                error_message=str(result),
            ))
        else:
            processed_results.append(result)
    
    return processed_results

