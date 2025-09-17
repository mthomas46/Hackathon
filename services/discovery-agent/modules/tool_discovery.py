"""LangGraph Tool Discovery Module for Discovery Agent service.

This module handles automatic discovery and registration of LangGraph tools
from service OpenAPI specifications. It analyzes endpoint definitions and
generates appropriate tool wrappers for integration with LangGraph workflows.
"""

import re
from typing import Dict, Any, List, Optional
from services.shared.clients import ServiceClients
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class ToolDiscoveryService:
    """Service for discovering and generating LangGraph tools from OpenAPI specs."""

    def __init__(self):
        self.service_client = ServiceClients()
        self.discovered_tools = {}

    async def discover_tools(self, service_name: str, service_url: str, openapi_url: Optional[str] = None,
                           tool_categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Discover LangGraph tools for a service from its OpenAPI specification.

        Args:
            service_name: Name of the service to discover tools for
            service_url: Base URL of the service
            openapi_url: OpenAPI spec URL (if different from service_url)
            tool_categories: Optional categories to filter tools by

        Returns:
            Dictionary containing discovered tools and metadata
        """
        try:
            # Get OpenAPI spec
            spec_url = openapi_url or f"{service_url}/openapi.json"
            spec = await self._fetch_openapi_spec(spec_url)

            # Extract endpoints and analyze for tool potential
            endpoints = self._extract_endpoints(spec)
            tools = self._analyze_endpoints_for_tools(service_name, service_url, endpoints, tool_categories)

            # Store discovered tools
            self.discovered_tools[service_name] = {
                "tools": tools,
                "spec_url": spec_url,
                "endpoint_count": len(endpoints),
                "tool_count": len(tools)
            }

            return {
                "service_name": service_name,
                "service_url": service_url,
                "spec_url": spec_url,
                "endpoints_discovered": len(endpoints),
                "tools_discovered": len(tools),
                "tools": tools,
                "categories": tool_categories or []
            }

        except Exception as e:
            error_msg = f"Failed to discover tools for {service_name}: {str(e)}"
            fire_and_forget("error", error_msg, ServiceNames.DISCOVERY_AGENT, {
                "service_name": service_name,
                "service_url": service_url,
                "openapi_url": openapi_url
            })
            raise Exception(error_msg)

    async def _fetch_openapi_spec(self, spec_url: str) -> Dict[str, Any]:
        """Fetch OpenAPI specification from URL."""
        try:
            response = await self.service_client.get_json(spec_url)
            return response
        except Exception as e:
            raise Exception(f"Failed to fetch OpenAPI spec from {spec_url}: {str(e)}")

    def _extract_endpoints(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract endpoints from OpenAPI specification."""
        endpoints = []
        paths = spec.get("paths", {})

        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue

            for method, details in methods.items():
                if not isinstance(details, dict):
                    continue

                endpoint = {
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", ""),
                    "description": details.get("description", ""),
                    "operation_id": details.get("operationId", ""),
                    "tags": details.get("tags", []),
                    "parameters": details.get("parameters", []),
                    "request_body": details.get("requestBody", {}),
                    "responses": details.get("responses", {})
                }
                endpoints.append(endpoint)

        return endpoints

    def _analyze_endpoints_for_tools(self, service_name: str, service_url: str,
                                   endpoints: List[Dict[str, Any]],
                                   tool_categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Analyze endpoints and generate LangGraph tool definitions."""
        tools = []

        for endpoint in endpoints:
            tool = self._generate_tool_for_endpoint(service_name, service_url, endpoint)
            if tool:
                # Filter by categories if specified
                if tool_categories is None or any(cat in tool.get("categories", []) for cat in tool_categories):
                    tools.append(tool)

        return tools

    def _generate_tool_for_endpoint(self, service_name: str, service_url: str,
                                  endpoint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate a LangGraph tool definition for an endpoint."""
        operation_id = endpoint.get("operation_id", "")
        if not operation_id:
            return None

        # Categorize the tool based on operation patterns
        categories = self._categorize_operation(endpoint)

        # Generate tool definition
        tool_name = self._generate_tool_name(service_name, operation_id)
        tool_description = self._generate_tool_description(endpoint, categories)

        # Create parameter schema
        parameters = self._extract_tool_parameters(endpoint)

        return {
            "name": tool_name,
            "description": tool_description,
            "service_name": service_name,
            "service_url": service_url,
            "operation_id": operation_id,
            "http_method": endpoint["method"],
            "path": endpoint["path"],
            "categories": categories,
            "parameters": parameters,
            "endpoint_info": {
                "summary": endpoint.get("summary", ""),
                "tags": endpoint.get("tags", [])
            }
        }

    def _categorize_operation(self, endpoint: Dict[str, Any]) -> List[str]:
        """Categorize an operation based on its characteristics."""
        categories = []
        operation_id = endpoint.get("operation_id", "").lower()
        method = endpoint.get("method", "").lower()
        path = endpoint.get("path", "").lower()
        summary = endpoint.get("summary", "").lower()

        # CRUD operations
        if operation_id.startswith("create") or method == "post":
            categories.append("create")
        if operation_id.startswith("get") or operation_id.startswith("list") or method == "get":
            categories.append("read")
        if operation_id.startswith("update") or method in ["put", "patch"]:
            categories.append("update")
        if operation_id.startswith("delete") or method == "delete":
            categories.append("delete")

        # Business operations
        if any(word in operation_id for word in ["analyze", "analysis", "check", "validate"]):
            categories.append("analysis")
        if any(word in operation_id for word in ["search", "find", "query"]):
            categories.append("search")
        if any(word in operation_id for word in ["notify", "alert", "send"]):
            categories.append("notification")
        if any(word in operation_id for word in ["store", "save", "persist"]):
            categories.append("storage")
        if any(word in operation_id for word in ["process", "execute", "run"]):
            categories.append("processing")

        # Service-specific categories
        if "document" in operation_id or "doc" in operation_id:
            categories.append("document")
        if "prompt" in operation_id:
            categories.append("prompt")
        if "code" in operation_id or "repo" in operation_id:
            categories.append("code")
        if "workflow" in operation_id:
            categories.append("workflow")

        return categories or ["general"]

    def _generate_tool_name(self, service_name: str, operation_id: str) -> str:
        """Generate a standardized tool name."""
        # Convert camelCase/PascalCase to snake_case
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', operation_id).lower()
        return f"{service_name}_{name}"

    def _generate_tool_description(self, endpoint: Dict[str, Any], categories: List[str]) -> str:
        """Generate a descriptive tool description."""
        summary = endpoint.get("summary", "")
        operation_id = endpoint.get("operation_id", "")
        method = endpoint.get("method", "")

        description = f"{method} {operation_id}"
        if summary:
            description += f": {summary}"

        if categories:
            description += f" (Categories: {', '.join(categories)})"

        return description

    def _extract_tool_parameters(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameter schema for tool definition."""
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }

        # Extract path parameters
        for param in endpoint.get("parameters", []):
            if isinstance(param, dict):
                param_name = param.get("name", "")
                param_type = param.get("schema", {}).get("type", "string")
                param_required = param.get("required", False)

                if param_name:
                    parameters["properties"][param_name] = {
                        "type": param_type,
                        "description": param.get("description", "")
                    }
                    if param_required:
                        parameters["required"].append(param_name)

        # Extract body parameters if present
        request_body = endpoint.get("requestBody", {})
        if request_body and "content" in request_body:
            for content_type, schema_info in request_body["content"].items():
                if "schema" in schema_info:
                    schema = schema_info["schema"]
                    if schema.get("type") == "object" and "properties" in schema:
                        for prop_name, prop_info in schema["properties"].items():
                            parameters["properties"][prop_name] = {
                                "type": prop_info.get("type", "string"),
                                "description": prop_info.get("description", "")
                            }
                            if prop_name in schema.get("required", []):
                                parameters["required"].append(prop_name)

        return parameters

    def get_discovered_tools(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get discovered tools for a service or all services."""
        if service_name:
            return self.discovered_tools.get(service_name, {})
        return self.discovered_tools

    def clear_discovered_tools(self, service_name: Optional[str] = None):
        """Clear discovered tools cache."""
        if service_name:
            self.discovered_tools.pop(service_name, None)
        else:
            self.discovered_tools.clear()


# Create singleton instance
tool_discovery_service = ToolDiscoveryService()
