"""Intelligence handlers for cross-service prompt generation."""

from typing import Dict, Any, Optional, List
from ...core.handler import BaseHandler
from .service import IntelligenceService
from services.shared.core.responses.responses import create_success_response, create_error_response


class IntelligenceHandlers(BaseHandler):
    """Handlers for intelligence operations."""

    def __init__(self):
        super().__init__(IntelligenceService())

    async def handle_generate_from_code(self, code_content: str, language: str = "python") -> Dict[str, Any]:
        """Generate prompts from code analysis."""
        try:
            result = await self.service.generate_prompts_from_code(code_content, language)
            if "error" in result:
                return create_error_response(result["error"], "ANALYSIS_FAILED").model_dump()

            return create_success_response(
                message="Prompts generated from code analysis",
                data=result
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to generate prompts from code: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_generate_from_document(self, document_content: str, doc_type: str = "markdown") -> Dict[str, Any]:
        """Generate prompts from document analysis."""
        try:
            result = await self.service.generate_prompts_from_document(document_content, doc_type)
            if "error" in result:
                return create_error_response(result["error"], "ANALYSIS_FAILED").model_dump()

            return create_success_response(
                message="Prompts generated from document analysis",
                data=result
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to generate prompts from document: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_generate_service_prompts(self, service_name: str, service_description: str = "") -> Dict[str, Any]:
        """Generate prompts for service integration."""
        try:
            prompts = await self.service.generate_service_integration_prompts(service_name, service_description)
            return create_success_response(
                message="Service integration prompts generated",
                data={"service": service_name, "prompts": prompts, "count": len(prompts)}
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to generate service prompts: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_analyze_effectiveness(self, prompt_id: str, usage_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Analyze prompt effectiveness."""
        try:
            # If no usage history provided, get it from analytics
            if usage_history is None:
                # This would integrate with analytics service
                usage_history = []

            analysis = await self.service.analyze_prompt_effectiveness(prompt_id, usage_history)
            if "error" in analysis:
                return create_error_response(analysis["error"], "ANALYSIS_FAILED").model_dump()

            return create_success_response(
                message="Prompt effectiveness analyzed",
                data=analysis
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to analyze effectiveness: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_generate_api_endpoints(self, service_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API endpoint documentation prompts."""
        try:
            # This would analyze service structure and generate API docs
            api_prompts = []

            endpoints = service_analysis.get("endpoints", [])
            for endpoint in endpoints:
                prompt = {
                    "id": f"api_doc_{endpoint.get('path', 'unknown')}",
                    "name": f"API Documentation: {endpoint.get('method', 'GET')} {endpoint.get('path', '')}",
                    "category": "api_documentation",
                    "content": f"""Document the API endpoint: {endpoint.get('method', 'GET')} {endpoint.get('path', '')}

Include:
1. Endpoint purpose and functionality
2. Request/response formats
3. Authentication requirements
4. Error codes and handling
5. Usage examples
6. Rate limiting information
7. Versioning details""",
                    "variables": [],
                    "tags": ["api", "documentation", "endpoint", "auto_generated"],
                    "source_type": "service_analysis",
                    "confidence_score": 0.8
                }
                api_prompts.append(prompt)

            return create_success_response(
                message="API endpoint prompts generated",
                data={"endpoints_analyzed": len(endpoints), "prompts": api_prompts}
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to generate API prompts: {str(e)}", "INTERNAL_ERROR").model_dump()
