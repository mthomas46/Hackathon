"""LangGraph Tool Discovery Module for Discovery Agent service.

This module handles automatic discovery and registration of LangGraph tools
from service OpenAPI specifications. It analyzes endpoint definitions and
generates appropriate tool wrappers for integration with LangGraph workflows.
"""

import re
from typing import Dict, Any, List, Optional
try:
    from services.shared.clients import ServiceClients
except ImportError:
    # Fallback for when running in Docker or different environment
    ServiceClients = None
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class ToolDiscoveryService:
    """Service for discovering and generating LangGraph tools from OpenAPI specs."""

    def __init__(self):
        self.service_client = ServiceClients()
        self.discovered_tools = {}
        self.security_scanner = None
        self.monitoring_service = None
        self.registry_storage = None

    def set_security_scanner(self, scanner):
        """Set the security scanner for tool validation"""
        self.security_scanner = scanner

    def set_monitoring_service(self, monitoring):
        """Set the monitoring service for observability"""
        self.monitoring_service = monitoring

    def set_registry_storage(self, storage):
        """Set the persistent storage for tool registry"""
        self.registry_storage = storage

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

    # ============================================================================
    # PHASE 2: COMPREHENSIVE SERVICE DISCOVERY
    # ============================================================================

    async def discover_ecosystem_tools(self, service_configs: Dict[str, Dict]) -> Dict[str, Any]:
        """PHASE 2: Run comprehensive tool discovery across entire ecosystem

        Args:
            service_configs: Dictionary mapping service names to their configurations

        Returns:
            Comprehensive discovery results with tools, metrics, and validation
        """
        discovery_results = {
            "timestamp": "2025-01-17T21:30:00Z",  # Would use datetime.now() in real implementation
            "services_tested": len(service_configs),
            "healthy_services": 0,
            "total_tools_discovered": 0,
            "services": {},
            "summary": {},
            "performance_metrics": [],
            "validation_results": []
        }

        print(f"🔍 Starting comprehensive ecosystem discovery for {len(service_configs)} services...")

        for service_name, config in service_configs.items():
            print(f"\n🔍 Discovering tools for {service_name}...")

            # Health check
            health_result = await self._check_service_health(service_name, config)
            service_result = {
                "config": config,
                "health": health_result,
                "tools": [],
                "validation": {},
                "performance": {}
            }

            if health_result["status"] == "healthy":
                discovery_results["healthy_services"] += 1

                # Discover OpenAPI and tools
                openapi_result = await self._discover_service_openapi(service_name, config)
                service_result["openapi"] = openapi_result

                if openapi_result.get("success"):
                    # Extract tools
                    tools = await self._extract_tools_from_openapi(service_name, openapi_result["data"])
                    service_result["tools"] = tools
                    discovery_results["total_tools_discovered"] += len(tools)

                    # Validate tools
                    if self.security_scanner:
                        validation = await self._validate_tools_security(service_name, tools)
                        service_result["validation"] = validation

                    print(f"   ✅ Discovered {len(tools)} tools, {len([t for t in tools if t.get('langraph_ready', False)])} LangGraph-ready")

                    # Performance tracking
                    service_result["performance"] = {
                        "discovery_time": health_result.get("response_time", 0),
                        "tool_count": len(tools),
                        "endpoint_count": openapi_result["data"].get("endpoints_count", 0)
                    }

                    discovery_results["performance_metrics"].append({
                        "service": service_name,
                        "response_time": health_result.get("response_time", 0),
                        "tools_found": len(tools),
                        "endpoints_found": openapi_result["data"].get("endpoints_count", 0)
                    })

                else:
                    print(f"   ❌ OpenAPI discovery failed: {openapi_result.get('error')}")

            else:
                print(f"   ❌ Service unhealthy: {health_result.get('error')}")

            discovery_results["services"][service_name] = service_result

            # Log to monitoring if available
            if self.monitoring_service:
                await self.monitoring_service.log_discovery_event(
                    "service_discovery",
                    {
                        "service_name": service_name,
                        "health_status": health_result["status"],
                        "tools_discovered": len(service_result["tools"]),
                        "response_time": health_result.get("response_time", 0)
                    }
                )

        # Generate summary
        discovery_results["summary"] = {
            "services_healthy": discovery_results["healthy_services"],
            "services_total": discovery_results["services_tested"],
            "health_percentage": (discovery_results["healthy_services"] / discovery_results["services_tested"]) * 100,
            "tools_discovered": discovery_results["total_tools_discovered"],
            "avg_tools_per_service": discovery_results["total_tools_discovered"] / max(discovery_results["healthy_services"], 1)
        }

        # Persist to registry if available
        if self.registry_storage:
            await self.registry_storage.save_discovery_results(discovery_results)

        return discovery_results

    async def _check_service_health(self, service_name: str, config: Dict) -> Dict[str, Any]:
        """Check service health status"""
        try:
            async with self.service_client.session() as session:
                health_url = f"{config['url']}/health"
                start_time = 0  # Would use time.time() in real implementation

                async with session.get(health_url, timeout=5) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "response_time": 0.1,  # Placeholder
                            "service_url": config['url']
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"Health check returned {response.status}",
                            "response_time": 0.1
                        }
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e),
                "response_time": 0.1
            }

    async def _discover_service_openapi(self, service_name: str, config: Dict) -> Dict[str, Any]:
        """Discover OpenAPI specification for a service"""
        try:
            spec_url = f"{config['url']}{config['openapi_path']}"

            async with self.service_client.session() as session:
                async with session.get(spec_url, timeout=10) as response:
                    if response.status == 200:
                        spec = await response.json()

                        # Extract key information
                        info = {
                            "title": spec.get("info", {}).get("title", service_name),
                            "version": spec.get("info", {}).get("version", "unknown"),
                            "description": spec.get("info", {}).get("description", ""),
                            "paths": list(spec.get("paths", {}).keys()),
                            "endpoints_count": len(spec.get("paths", {})),
                            "full_spec": spec
                        }

                        return {"success": True, "data": info}
                    else:
                        return {"success": False, "error": f"OpenAPI returned {response.status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _extract_tools_from_openapi(self, service_name: str, openapi_data: Dict) -> List[Dict[str, Any]]:
        """Extract tool definitions from OpenAPI specification"""
        spec = openapi_data["full_spec"]
        paths = spec.get("paths", {})
        tools = []

        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE"]:
                    tool = {
                        "name": f"{service_name}_{path.replace('/', '_').replace('-', '_')}_{method}",
                        "service": service_name,
                        "path": path,
                        "method": method.upper(),
                        "category": self._categorize_endpoint(path, method, details),
                        "summary": details.get("summary", ""),
                        "description": details.get("description", ""),
                        "parameters": self._extract_parameters(details),
                        "responses": list(details.get("responses", {}).keys()),
                        "langraph_ready": self._assess_langraph_readiness(details)
                    }
                    tools.append(tool)

        return tools

    # ============================================================================
    # PHASE 4: SECURITY SCANNING INTEGRATION
    # ============================================================================

    async def _validate_tools_security(self, service_name: str, tools: List[Dict]) -> Dict[str, Any]:
        """PHASE 4: Validate tools using security scanner"""
        if not self.security_scanner:
            return {"scanned": False, "error": "Security scanner not configured"}

        validation_results = {
            "scanned": True,
            "tools_scanned": len(tools),
            "vulnerabilities_found": 0,
            "high_risk_tools": 0,
            "tool_validations": []
        }

        print(f"🔒 Security scanning {len(tools)} tools for {service_name}...")

        for tool in tools:
            # Use the security scanner to validate this tool
            security_result = await self.security_scanner.scan_tool_security(tool)
            validation_results["tool_validations"].append(security_result)

            # Count vulnerabilities
            vulnerabilities = len(security_result.get("vulnerabilities", []))
            validation_results["vulnerabilities_found"] += vulnerabilities

            # Count high-risk tools
            if security_result.get("risk_level") == "high":
                validation_results["high_risk_tools"] += 1

            # Log security scan
            if self.monitoring_service:
                await self.monitoring_service.monitor_security_scan(
                    tool["name"],
                    security_result
                )

        validation_results["overall_risk"] = "high" if validation_results["high_risk_tools"] > 0 else \
                                           "medium" if validation_results["vulnerabilities_found"] > 0 else "low"

        return validation_results

    # ============================================================================
    # PHASE 5: MONITORING AND OBSERVABILITY
    # ============================================================================

    async def monitor_discovery_performance(self, discovery_results: Dict[str, Any]):
        """PHASE 5: Monitor discovery performance and log metrics"""
        if not self.monitoring_service:
            return

        # Log overall discovery metrics
        await self.monitoring_service.log_discovery_event("discovery_batch_complete", {
            "services_tested": discovery_results["services_tested"],
            "healthy_services": discovery_results["healthy_services"],
            "total_tools_discovered": discovery_results["total_tools_discovered"],
            "discovery_duration": len(discovery_results["performance_metrics"]) * 0.5  # Estimate
        })

        # Log performance metrics for each service
        for metric in discovery_results["performance_metrics"]:
            await self.monitoring_service.log_discovery_event("service_performance", metric)


# Create singleton instance
tool_discovery_service = ToolDiscoveryService()
