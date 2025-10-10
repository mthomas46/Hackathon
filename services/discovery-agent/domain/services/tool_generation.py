"""Tool Generation Domain Service

Generates LangGraph-compatible tool definitions from discovered services.
"""

from typing import Dict, Any, List
from ..entities import Service, Endpoint


def generate_tool_name(endpoint: Endpoint, service_name: str) -> str:
    """
    Generate a tool name from endpoint information.
    
    Format: {service_name}_{method}_{path_simplified}
    Example: user_api_get_users, user_api_post_user
    """
    # Simplify path by removing slashes and parameters
    path_parts = [p for p in endpoint.path.split("/") if p and not p.startswith("{")]
    path_str = "_".join(path_parts) if path_parts else "root"
    
    # Create tool name
    tool_name = f"{service_name}_{endpoint.method.lower()}_{path_str}"
    
    # Clean up the name (remove special characters)
    tool_name = tool_name.replace("-", "_").replace(".", "_")
    
    return tool_name


def generate_tool_description(endpoint: Endpoint, service_name: str) -> str:
    """
    Generate a tool description from endpoint metadata.
    """
    # Use summary if available, otherwise construct from method and path
    if endpoint.summary:
        description = f"{endpoint.summary}"
    else:
        description = f"{endpoint.method} {endpoint.path}"
    
    # Add service name context
    description = f"[{service_name}] {description}"
    
    # Add full description if available
    if endpoint.description and endpoint.description != endpoint.summary:
        description += f". {endpoint.description}"
    
    return description


def generate_tool_parameters(endpoint: Endpoint) -> Dict[str, Any]:
    """
    Generate tool parameter schema from endpoint parameters.
    
    Returns a JSON Schema compatible parameter definition.
    """
    properties = {}
    required = []
    
    for param in endpoint.parameters:
        param_name = param.get("name")
        if not param_name:
            continue
        
        param_schema = param.get("schema", {})
        param_type = param_schema.get("type", "string")
        
        # Map OpenAPI types to JSON Schema types
        type_mapping = {
            "integer": "integer",
            "number": "number",
            "string": "string",
            "boolean": "boolean",
            "array": "array",
            "object": "object",
        }
        
        properties[param_name] = {
            "type": type_mapping.get(param_type, "string"),
            "description": param.get("description", f"Parameter: {param_name}"),
        }
        
        # Add enum if present
        if "enum" in param_schema:
            properties[param_name]["enum"] = param_schema["enum"]
        
        # Track required parameters
        if param.get("required", False):
            required.append(param_name)
    
    # If endpoint has request body, add a generic body parameter
    # (This is a simplification - in production you'd parse requestBody schema)
    if endpoint.method.upper() in ["POST", "PUT", "PATCH"]:
        if "body" not in properties:
            properties["body"] = {
                "type": "object",
                "description": "Request body data",
            }
    
    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def generate_tool_from_endpoint(
    endpoint: Endpoint,
    service: Service
) -> Dict[str, Any]:
    """
    Generate a single tool definition from an endpoint.
    
    Returns a LangGraph-compatible tool definition.
    """
    tool_name = generate_tool_name(endpoint, service.name)
    description = generate_tool_description(endpoint, service.name)
    parameters = generate_tool_parameters(endpoint)
    
    return {
        "name": tool_name,
        "description": description,
        "parameters": parameters,
        "metadata": {
            "service_name": service.name,
            "service_url": service.base_url,
            "endpoint_path": endpoint.path,
            "http_method": endpoint.method,
            "tags": endpoint.tags,
            "operation_id": endpoint.operation_id,
        }
    }


def generate_tools_from_service(service: Service) -> List[Dict[str, Any]]:
    """
    Generate all tool definitions from a discovered service.
    
    Args:
        service: The discovered Service entity
        
    Returns:
        List of LangGraph-compatible tool definitions
    """
    tools = []
    
    for endpoint in service.endpoints:
        try:
            tool = generate_tool_from_endpoint(endpoint, service)
            tools.append(tool)
        except Exception as e:
            # Log error but continue processing other endpoints
            print(f"Warning: Failed to generate tool for {endpoint.path}: {e}")
            continue
    
    return tools


def generate_tool_summary(tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a summary of generated tools.
    
    Returns statistics about the tools generated.
    """
    if not tools:
        return {
            "total_tools": 0,
            "by_method": {},
            "by_tag": {},
        }
    
    # Count by HTTP method
    by_method = {}
    for tool in tools:
        method = tool.get("metadata", {}).get("http_method", "UNKNOWN")
        by_method[method] = by_method.get(method, 0) + 1
    
    # Count by tag
    by_tag = {}
    for tool in tools:
        tags = tool.get("metadata", {}).get("tags", [])
        for tag in tags:
            by_tag[tag] = by_tag.get(tag, 0) + 1
    
    return {
        "total_tools": len(tools),
        "by_method": by_method,
        "by_tag": by_tag,
        "tool_names": [t["name"] for t in tools],
    }

