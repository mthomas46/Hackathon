"""Service Integration Module for LLM Gateway Service.

Handles comprehensive integration with all ecosystem services including:
- doc_store: Document storage and retrieval
- prompt_store: Prompt management and optimization
- memory-agent: Conversation memory and context
- interpreter: Natural language processing and workflow translation
- orchestrator: Workflow orchestration and coordination
- summarizer-hub: LLM summarization operations
- secure-analyzer: Security analysis and policy enforcement
- code-analyzer: Code analysis and documentation
- architecture-digitizer: Architecture analysis and digitization
- analysis-service: Document analysis and consistency checking
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from services.shared.clients import ServiceClients
from services.shared.constants_new import ServiceNames, ErrorCodes
from services.shared.logging import fire_and_forget
from services.shared.config import get_config_value
from services.shared.utilities import utc_now

from .models import LLMQuery, GatewayResponse


class ServiceIntegrations:
    """Manages integrations with all ecosystem services."""

    def __init__(self):
        self.clients = ServiceClients()
        self.service_endpoints = self._initialize_service_endpoints()
        self.integration_cache = {}  # Cache for service capabilities and metadata

    def _initialize_service_endpoints(self) -> Dict[str, str]:
        """Initialize service endpoint mappings."""
        return {
            ServiceNames.DOC_STORE: get_config_value("DOC_STORE_URL", "http://doc_store:5087", section="services"),
            ServiceNames.PROMPT_STORE: get_config_value("PROMPT_STORE_URL", "http://prompt-store:5110", section="services"),
            ServiceNames.MEMORY_AGENT: get_config_value("MEMORY_AGENT_URL", "http://memory-agent:5040", section="services"),
            ServiceNames.INTERPRETER: get_config_value("INTERPRETER_URL", "http://interpreter:5120", section="services"),
            ServiceNames.ORCHESTRATOR: get_config_value("ORCHESTRATOR_URL", "http://orchestrator:5099", section="services"),
            ServiceNames.SUMMARIZER_HUB: get_config_value("SUMMARIZER_HUB_URL", "http://summarizer-hub:5060", section="services"),
            ServiceNames.SECURE_ANALYZER: get_config_value("SECURE_ANALYZER_URL", "http://secure-analyzer:5070", section="services"),
            ServiceNames.CODE_ANALYZER: get_config_value("CODE_ANALYZER_URL", "http://code-analyzer:5085", section="services"),
            ServiceNames.ARCHITECTURE_DIGITIZER: get_config_value("ARCHITECTURE_DIGITIZER_URL", "http://architecture-digitizer:5105", section="services"),
            ServiceNames.ANALYSIS_SERVICE: get_config_value("ANALYSIS_SERVICE_URL", "http://analysis-service:5020", section="services"),
        }

    async def initialize_integrations(self):
        """Initialize all service integrations."""
        try:
            # Test connectivity to all services
            connectivity_results = await self._test_service_connectivity()

            # Register with orchestrator
            await self._register_with_orchestrator()

            # Cache service capabilities
            await self._cache_service_capabilities()

            fire_and_forget(
                "llm_gateway_integrations_initialized",
                f"LLM Gateway integrations initialized: {len(connectivity_results)} services connected",
                ServiceNames.LLM_GATEWAY,
                {"connectivity_results": connectivity_results}
            )

            return connectivity_results

        except Exception as e:
            fire_and_forget(
                "llm_gateway_integration_error",
                f"Failed to initialize integrations: {str(e)}",
                ServiceNames.LLM_GATEWAY,
                {"error": str(e)}
            )
            raise

    async def _test_service_connectivity(self) -> Dict[str, bool]:
        """Test connectivity to all integrated services."""
        connectivity_results = {}

        for service_name, endpoint in self.service_endpoints.items():
            try:
                # Test health endpoint
                health_url = f"{endpoint}/health"
                response = await self.clients.get_json(health_url)
                connectivity_results[service_name] = response.get("status") == "healthy"
            except Exception as e:
                connectivity_results[service_name] = False
                fire_and_forget(
                    "llm_gateway_connectivity_test_failed",
                    f"Connectivity test failed for {service_name}: {str(e)}",
                    ServiceNames.LLM_GATEWAY,
                    {"service": service_name, "endpoint": endpoint, "error": str(e)}
                )

        return connectivity_results

    async def _register_with_orchestrator(self):
        """Register LLM Gateway capabilities with the orchestrator."""
        try:
            orchestrator_url = self.service_endpoints[ServiceNames.ORCHESTRATOR]

            # Register LLM capabilities
            capabilities = {
                "service_name": ServiceNames.LLM_GATEWAY,
                "capabilities": [
                    "llm_query",
                    "llm_chat",
                    "llm_embeddings",
                    "llm_streaming",
                    "content_analysis",
                    "provider_routing",
                    "security_filtering",
                    "response_caching",
                    "rate_limiting",
                    "metrics_collection"
                ],
                "endpoints": {
                    "query": "/query",
                    "chat": "/chat",
                    "embeddings": "/embeddings",
                    "stream": "/stream",
                    "providers": "/providers",
                    "metrics": "/metrics"
                },
                "supported_providers": ["ollama", "openai", "anthropic", "bedrock", "grok"],
                "security_features": ["content_filtering", "provider_routing", "audit_logging"],
                "performance_features": ["response_caching", "load_balancing", "rate_limiting"],
                "registered_at": utc_now().isoformat()
            }

            registration_url = f"{orchestrator_url}/services/register"
            response = await self.clients.post_json(registration_url, capabilities)

            if response.get("success"):
                fire_and_forget(
                    "llm_gateway_registered_with_orchestrator",
                    "LLM Gateway successfully registered with orchestrator",
                    ServiceNames.LLM_GATEWAY,
                    {"capabilities_count": len(capabilities["capabilities"])}
                )
            else:
                fire_and_forget(
                    "llm_gateway_orchestrator_registration_failed",
                    "Failed to register with orchestrator",
                    ServiceNames.LLM_GATEWAY,
                    {"response": response}
                )

        except Exception as e:
            fire_and_forget(
                "llm_gateway_orchestrator_registration_error",
                f"Error registering with orchestrator: {str(e)}",
                ServiceNames.LLM_GATEWAY,
                {"error": str(e)}
            )

    async def _cache_service_capabilities(self):
        """Cache service capabilities for optimized integration."""
        try:
            for service_name, endpoint in self.service_endpoints.items():
                try:
                    # Try to get service capabilities
                    capabilities_url = f"{endpoint}/capabilities"
                    capabilities = await self.clients.get_json(capabilities_url)
                    self.integration_cache[service_name] = capabilities

                except Exception:
                    # Fallback: cache basic service info
                    self.integration_cache[service_name] = {
                        "name": service_name,
                        "endpoint": endpoint,
                        "capabilities": ["basic"],
                        "last_updated": utc_now().isoformat()
                    }

            fire_and_forget(
                "llm_gateway_capabilities_cached",
                f"Cached capabilities for {len(self.integration_cache)} services",
                ServiceNames.LLM_GATEWAY,
                {"cached_services": list(self.integration_cache.keys())}
            )

        except Exception as e:
            fire_and_forget(
                "llm_gateway_capabilities_cache_error",
                f"Error caching service capabilities: {str(e)}",
                ServiceNames.LLM_GATEWAY,
                {"error": str(e)}
            )

    # ============================================================================
    # INTEGRATION METHODS - Core Services
    # ============================================================================

    async def integrate_with_doc_store(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Integrate with Document Store service."""
        try:
            endpoint = self.service_endpoints[ServiceNames.DOC_STORE]

            if operation == "store":
                # Store LLM interaction results
                url = f"{endpoint}/documents"
                data = {
                    "title": kwargs.get("title", "LLM Interaction"),
                    "content": kwargs.get("content", ""),
                    "metadata": {
                        "llm_provider": kwargs.get("provider"),
                        "tokens_used": kwargs.get("tokens_used"),
                        "processing_time": kwargs.get("processing_time"),
                        "timestamp": utc_now().isoformat()
                    }
                }
                response = await self.clients.post_json(url, data)
                return response

            elif operation == "retrieve":
                # Retrieve documents for context
                doc_id = kwargs.get("doc_id")
                url = f"{endpoint}/documents/{doc_id}"
                response = await self.clients.get_json(url)
                return response

            elif operation == "search":
                # Search documents for relevant context
                url = f"{endpoint}/documents/search"
                data = {"query": kwargs.get("query", "")}
                response = await self.clients.post_json(url, data)
                return response

        except Exception as e:
            fire_and_forget(
                "llm_gateway_doc_store_integration_error",
                f"Doc Store integration error: {str(e)}",
                ServiceNames.LLM_GATEWAY,
                {"operation": operation, "error": str(e)}
            )
            return {"error": str(e)}

    async def integrate_with_prompt_store(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Integrate with Prompt Store service."""
        try:
            endpoint = self.service_endpoints[ServiceNames.PROMPT_STORE]

            if operation == "get_optimized":
                # Get optimized prompt for task
                url = f"{endpoint}/prompts/optimized"
                data = {
                    "task_type": kwargs.get("task_type"),
                    "context": kwargs.get("context", {})
                }
                response = await self.clients.post_json(url, data)
                return response

            elif operation == "store_prompt":
                # Store new prompt
                url = f"{endpoint}/prompts"
                data = {
                    "content": kwargs.get("content"),
                    "category": kwargs.get("category", "llm_gateway"),
                    "variables": kwargs.get("variables", [])
                }
                response = await self.clients.post_json(url, data)
                return response

            elif operation == "get_prompts":
                # Get prompts by category
                category = kwargs.get("category", "general")
                url = f"{endpoint}/prompts/category/{category}"
                response = await self.clients.get_json(url)
                return response

        except Exception as e:
            fire_and_forget(
                "llm_gateway_prompt_store_integration_error",
                f"Prompt Store integration error: {str(e)}",
                ServiceNames.LLM_GATEWAY,
                {"operation": operation, "error": str(e)}
            )
            return {"error": str(e)}

    async def integrate_with_memory_agent(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Integrate with Memory Agent service."""
        try:
            endpoint = self.service_endpoints[ServiceNames.MEMORY_AGENT]

            if operation == "store_interaction":
                # Store LLM interaction in memory
                url = f"{endpoint}/memory"
                data = {
                    "user_id": kwargs.get("user_id"),
                    "interaction_type": "llm_query",
                    "content": {
                        "prompt": kwargs.get("prompt"),
                        "response": kwargs.get("response"),
                        "provider": kwargs.get("provider"),
                        "context": kwargs.get("context", {})
                    },
                    "metadata": {
                        "tokens_used": kwargs.get("tokens_used"),
                        "processing_time": kwargs.get("processing_time"),
                        "timestamp": utc_now().isoformat()
                    }
                }
                response = await self.clients.post_json(url, data)
                return response

            elif operation == "retrieve_context":
                # Retrieve conversation context
                user_id = kwargs.get("user_id")
                url = f"{endpoint}/memory/{user_id}/context"
                response = await self.clients.get_json(url)
                return response

            elif operation == "get_conversation_history":
                # Get conversation history
                user_id = kwargs.get("user_id")
                limit = kwargs.get("limit", 10)
                url = f"{endpoint}/memory/{user_id}/history?limit={limit}"
                response = await self.clients.get_json(url)
                return response

        except Exception as e:
            fire_and_forget(
                "llm_gateway_memory_agent_integration_error",
                f"Memory Agent integration error: {str(e)}",
                ServiceNames.LLM_GATEWAY,
                {"operation": operation, "error": str(e)}
            )
            return {"error": str(e)}

    async def integrate_with_interpreter(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Integrate with Interpreter service."""
        try:
            endpoint = self.service_endpoints[ServiceNames.INTERPRETER]

            if operation == "interpret_query":
                # Interpret natural language query
                url = f"{endpoint}/interpret"
                data = {
                    "query": kwargs.get("query"),
                    "context": kwargs.get("context", {}),
                    "user_id": kwargs.get("user_id")
                }
                response = await self.clients.post_json(url, data)
                return response

            elif operation == "translate_to_workflow":
                # Translate query to workflow
                url = f"{endpoint}/translate/workflow"
                data = {
                    "query": kwargs.get("query"),
                    "available_services": kwargs.get("available_services", []),
                    "context": kwargs.get("context", {})
                }
                response = await self.clients.post_json(url, data)
                return response

            elif operation == "extract_entities":
                # Extract entities from text
                url = f"{endpoint}/extract/entities"
                data = {
                    "text": kwargs.get("text"),
                    "entity_types": kwargs.get("entity_types", [])
                }
                response = await self.clients.post_json(url, data)
                return response

        except Exception as e:
            fire_and_forget(
                "llm_gateway_interpreter_integration_error",
                f"Interpreter integration error: {str(e)}",
                ServiceNames.LLM_GATEWAY,
                {"operation": operation, "error": str(e)}
            )
            return {"error": str(e)}

    async def integrate_with_orchestrator(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Integrate with Orchestrator service."""
        try:
            endpoint = self.service_endpoints[ServiceNames.ORCHESTRATOR]

            if operation == "execute_workflow":
                # Execute LLM-related workflow
                url = f"{endpoint}/workflows/execute"
                data = {
                    "workflow_type": kwargs.get("workflow_type", "llm_processing"),
                    "parameters": kwargs.get("parameters", {}),
                    "context": kwargs.get("context", {})
                }
                response = await self.clients.post_json(url, data)
                return response

            elif operation == "register_workflow":
                # Register LLM workflow
                url = f"{endpoint}/workflows/register"
                data = {
                    "workflow_name": kwargs.get("workflow_name"),
                    "workflow_definition": kwargs.get("workflow_definition"),
                    "required_services": ["llm-gateway"]
                }
                response = await self.clients.post_json(url, data)
                return response

            elif operation == "get_service_status":
                # Get orchestrator service status
                url = f"{endpoint}/services/status"
                response = await self.clients.get_json(url)
                return response

        except Exception as e:
            fire_and_forget(
                "llm_gateway_orchestrator_integration_error",
                f"Orchestrator integration error: {str(e)}",
                ServiceNames.LLM_GATEWAY,
                {"operation": operation, "error": str(e)}
            )
            return {"error": str(e)}

    # ============================================================================
    # INTEGRATION METHODS - AI/ML Services
    # ============================================================================

    async def integrate_with_summarizer_hub(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Integrate with Summarizer Hub service."""
        try:
            endpoint = self.service_endpoints[ServiceNames.SUMMARIZER_HUB]

            if operation == "summarize":
                # Use summarizer hub for specialized summarization
                url = f"{endpoint}/summarize/ensemble"
                data = {
                    "text": kwargs.get("text"),
                    "providers": kwargs.get("providers", ["ollama"]),
                    "prompt": kwargs.get("prompt")
                }
                response = await self.clients.post_json(url, data)
                return response

            elif operation == "get_providers":
                # Get available summarization providers
                url = f"{endpoint}/providers"
                response = await self.clients.get_json(url)
                return response

        except Exception as e:
            fire_and_forget(
                "llm_gateway_summarizer_hub_integration_error",
                f"Summarizer Hub integration error: {str(e)}",
                ServiceNames.LLM_GATEWAY,
                {"operation": operation, "error": str(e)}
            )
            return {"error": str(e)}

    async def integrate_with_secure_analyzer(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Integrate with Secure Analyzer service."""
        try:
            endpoint = self.service_endpoints[ServiceNames.SECURE_ANALYZER]

            if operation == "analyze_security":
                # Analyze content for security issues
                url = f"{endpoint}/detect"
                data = {
                    "content": kwargs.get("content"),
                    "keywords": kwargs.get("keywords", [])
                }
                response = await self.clients.post_json(url, data)
                return response

            elif operation == "get_secure_providers":
                # Get security recommendations for providers
                url = f"{endpoint}/suggest"
                data = {
                    "content": kwargs.get("content"),
                    "providers": kwargs.get("providers", [])
                }
                response = await self.clients.post_json(url, data)
                return response

        except Exception as e:
            fire_and_forget(
                "llm_gateway_secure_analyzer_integration_error",
                f"Secure Analyzer integration error: {str(e)}",
                ServiceNames.LLM_GATEWAY,
                {"operation": operation, "error": str(e)}
            )
            return {"error": str(e)}

    async def integrate_with_code_analyzer(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Integrate with Code Analyzer service."""
        try:
            endpoint = self.service_endpoints[ServiceNames.CODE_ANALYZER]

            if operation == "analyze_code":
                # Analyze code for LLM processing
                url = f"{endpoint}/analyze"
                data = {
                    "code": kwargs.get("code"),
                    "language": kwargs.get("language"),
                    "analysis_type": kwargs.get("analysis_type", "comprehensive")
                }
                response = await self.clients.post_json(url, data)
                return response

            elif operation == "extract_endpoints":
                # Extract API endpoints from code
                url = f"{endpoint}/endpoints"
                data = {"code": kwargs.get("code")}
                response = await self.clients.post_json(url, data)
                return response

        except Exception as e:
            fire_and_forget(
                "llm_gateway_code_analyzer_integration_error",
                f"Code Analyzer integration error: {str(e)}",
                ServiceNames.LLM_GATEWAY,
                {"operation": operation, "error": str(e)}
            )
            return {"error": str(e)}

    async def integrate_with_architecture_digitizer(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Integrate with Architecture Digitizer service."""
        try:
            endpoint = self.service_endpoints[ServiceNames.ARCHITECTURE_DIGITIZER]

            if operation == "digitize_architecture":
                # Digitize architecture diagrams/documents
                url = f"{endpoint}/digitize"
                data = {
                    "content": kwargs.get("content"),
                    "format": kwargs.get("format", "text"),
                    "extract_relationships": kwargs.get("extract_relationships", True)
                }
                response = await self.clients.post_json(url, data)
                return response

            elif operation == "analyze_dependencies":
                # Analyze system dependencies
                url = f"{endpoint}/dependencies"
                data = {"architecture_data": kwargs.get("architecture_data")}
                response = await self.clients.post_json(url, data)
                return response

        except Exception as e:
            fire_and_forget(
                "llm_gateway_architecture_digitizer_integration_error",
                f"Architecture Digitizer integration error: {str(e)}",
                ServiceNames.LLM_GATEWAY,
                {"operation": operation, "error": str(e)}
            )
            return {"error": str(e)}

    async def integrate_with_analysis_service(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Integrate with Analysis Service."""
        try:
            endpoint = self.service_endpoints[ServiceNames.ANALYSIS_SERVICE]

            if operation == "analyze_consistency":
                # Analyze document consistency
                url = f"{endpoint}/analyze"
                data = {
                    "content": kwargs.get("content"),
                    "analysis_type": "consistency",
                    "thresholds": kwargs.get("thresholds", {})
                }
                response = await self.clients.post_json(url, data)
                return response

            elif operation == "analyze_quality":
                # Analyze document quality
                url = f"{endpoint}/quality"
                data = {"content": kwargs.get("content")}
                response = await self.clients.post_json(url, data)
                return response

        except Exception as e:
            fire_and_forget(
                "llm_gateway_analysis_service_integration_error",
                f"Analysis Service integration error: {str(e)}",
                ServiceNames.LLM_GATEWAY,
                {"operation": operation, "error": str(e)}
            )
            return {"error": str(e)}

    # ============================================================================
    # ENHANCED LLM PROCESSING WITH SERVICE INTEGRATION
    # ============================================================================

    async def enhanced_llm_processing(self, query: LLMQuery) -> GatewayResponse:
        """Enhanced LLM processing with full service integration."""

        # Step 1: Interpret query with Interpreter service
        interpretation = await self.integrate_with_interpreter(
            "interpret_query",
            query=query.prompt,
            context=query.context,
            user_id=query.user_id
        )

        # Step 2: Get optimized prompt from Prompt Store
        optimized_prompt = await self.integrate_with_prompt_store(
            "get_optimized",
            task_type=interpretation.get("intent", "general"),
            context=query.context
        )

        # Step 3: Retrieve relevant context from Memory Agent
        conversation_context = await self.integrate_with_memory_agent(
            "retrieve_context",
            user_id=query.user_id
        )

        # Step 4: Analyze security with Secure Analyzer
        security_analysis = await self.integrate_with_secure_analyzer(
            "analyze_security",
            content=query.prompt + (query.context or "")
        )

        # Step 5: Execute LLM query with enhanced context
        enhanced_query = LLMQuery(
            prompt=optimized_prompt.get("content", query.prompt),
            provider=query.provider,
            model=query.model,
            context={
                **(query.context or {}),
                "conversation_history": conversation_context.get("history", []),
                "security_analysis": security_analysis,
                "interpretation": interpretation
            },
            user_id=query.user_id,
            temperature=query.temperature,
            max_tokens=query.max_tokens
        )

        # This would return the actual LLM response
        # For now, return a placeholder
        return GatewayResponse(
            response="Enhanced LLM processing with full service integration",
            provider="integrated",
            tokens_used=150,
            processing_time=2.5,
            correlation_id=f"enhanced-{int(utc_now().timestamp())}"
        )

    async def get_service_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of all integrated services."""
        health_status = {}

        for service_name, endpoint in self.service_endpoints.items():
            try:
                health_url = f"{endpoint}/health"
                response = await self.clients.get_json(health_url)
                health_status[service_name] = {
                    "status": "healthy" if response.get("status") == "healthy" else "unhealthy",
                    "endpoint": endpoint,
                    "response_time": response.get("response_time", 0),
                    "last_checked": utc_now().isoformat()
                }
            except Exception as e:
                health_status[service_name] = {
                    "status": "error",
                    "endpoint": endpoint,
                    "error": str(e),
                    "last_checked": utc_now().isoformat()
                }

        return {
            "overall_status": "healthy" if all(s["status"] == "healthy" for s in health_status.values()) else "degraded",
            "services": health_status,
            "total_services": len(health_status),
            "healthy_services": sum(1 for s in health_status.values() if s["status"] == "healthy"),
            "timestamp": utc_now().isoformat()
        }
