"""
Tool Discovery Adapter - Simplified interface for test compatibility.

Provides a clean interface matching test expectations while delegating
to the full ToolDiscoveryService implementation.
"""

from typing import List, Dict, Any
import re


class ToolDiscovery:
    """
    Simplified tool discovery interface for generating LangGraph tools from services.
    
    This adapter provides a clean API matching test expectations.
    """
    
    def __init__(self):
        """Initialize the tool discovery service."""
        self.discovered_tools = {}
    
    async def generate_tools(self, service) -> List[Dict[str, Any]]:
        """
        Generate LangGraph tools from a discovered service.
        
        Args:
            service: Service entity with endpoints
            
        Returns:
            List of tool definitions
        """
        tools = []
        
        for endpoint in service.endpoints:
            tool = self._generate_tool_for_endpoint(service, endpoint)
            if tool:
                tools.append(tool)
        
        # Cache the generated tools
        self.discovered_tools[service.name] = tools
        
        return tools
    
    def _generate_tool_for_endpoint(self, service, endpoint) -> Dict[str, Any]:
        """
        Generate a tool definition for a single endpoint.
        
        Args:
            service: Service entity
            endpoint: Endpoint entity
            
        Returns:
            Tool definition dictionary
        """
        # Generate tool name from service and endpoint
        tool_name = self._generate_tool_name(service.name, endpoint.path, endpoint.method)
        
        # Categorize the endpoint
        categories = self._categorize_endpoint(endpoint)
        
        # Generate description
        description = endpoint.summary or endpoint.description or f"{endpoint.method} {endpoint.path}"
        if categories:
            description += f" (Categories: {', '.join(categories)})"
        
        # Extract parameters
        parameters = self._extract_parameters(endpoint)
        
        return {
            "name": tool_name,
            "description": description,
            "categories": categories,
            "service_name": service.name,
            "service_url": service.base_url,
            "http_method": endpoint.method,
            "path": endpoint.path,
            "parameters": parameters
        }
    
    def _generate_tool_name(self, service_name: str, path: str, method: str) -> str:
        """
        Generate a standardized tool name.
        
        Format: service_name_sanitized_path_method
        Example: code_analyzer_analyze_post
        
        Args:
            service_name: Name of the service
            path: API path
            method: HTTP method
            
        Returns:
            Sanitized tool name
        """
        # Sanitize service name (replace hyphens with underscores)
        service_part = service_name.replace("-", "_").replace(" ", "_")
        
        # Sanitize path (remove leading slash, replace special chars)
        path_part = path.lstrip("/").replace("/", "_").replace("-", "_").replace("{", "").replace("}", "")
        
        # Remove consecutive underscores
        path_part = re.sub(r"_+", "_", path_part)
        
        # Add method
        method_part = method.lower()
        
        # Combine parts
        tool_name = f"{service_part}_{path_part}_{method_part}"
        
        # Ensure it's a valid identifier
        tool_name = re.sub(r"[^a-z0-9_]", "", tool_name)
        
        return tool_name
    
    def _categorize_endpoint(self, endpoint) -> List[str]:
        """
        Categorize an endpoint based on its characteristics.
        
        Args:
            endpoint: Endpoint entity
            
        Returns:
            List of categories
        """
        categories = []
        path = endpoint.path.lower()
        method = endpoint.method.lower()
        summary = (endpoint.summary or "").lower()
        description = (endpoint.description or "").lower()
        
        # CRUD operations
        if method == "post" and "/create" not in path:
            categories.append("create")
        elif method == "get":
            categories.append("read")
        elif method in ["put", "patch"]:
            categories.append("update")
        elif method == "delete":
            categories.append("delete")
        
        # Search operations
        if any(keyword in path for keyword in ["search", "query", "find"]):
            categories.append("search")
        if any(keyword in summary for keyword in ["search", "query", "find"]):
            categories.append("search")
        
        # Health/monitoring
        if "health" in path or "health" in summary:
            categories.append("monitoring")
        if any(keyword in path for keyword in ["status", "ping", "readiness"]):
            categories.append("monitoring")
        
        # Analysis operations
        if any(keyword in path for keyword in ["analyze", "analysis", "check", "validate"]):
            categories.append("analysis")
        if any(keyword in summary for keyword in ["analyze", "analysis", "check", "validate"]):
            categories.append("analysis")
        
        # Code operations
        if any(keyword in path for keyword in ["code", "repository", "repo"]):
            categories.append("code")
        
        # Document operations
        if any(keyword in path for keyword in ["document", "doc", "file"]):
            categories.append("document")
        
        # Default category if none matched
        if not categories:
            categories.append("general")
        
        return categories
    
    def _extract_parameters(self, endpoint) -> Dict[str, Any]:
        """
        Extract parameters from an endpoint.
        
        Args:
            endpoint: Endpoint entity
            
        Returns:
            Parameters schema
        """
        parameters_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Process endpoint parameters
        for param in endpoint.parameters:
            if isinstance(param, dict):
                param_name = param.get("name", "")
                param_required = param.get("required", False)
                
                if param_name:
                    parameters_schema["properties"][param_name] = {
                        "type": param.get("type", "string"),
                        "description": param.get("description", "")
                    }
                    
                    if param_required:
                        parameters_schema["required"].append(param_name)
        
        return parameters_schema

