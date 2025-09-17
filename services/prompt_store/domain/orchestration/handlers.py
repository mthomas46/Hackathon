"""Orchestration handlers for dynamic prompt chains and pipelines."""

from typing import Dict, Any
from ...core.handler import BaseHandler
from .service import PromptOrchestrator
from services.shared.responses import create_success_response, create_error_response


class OrchestrationHandlers(BaseHandler):
    """Handlers for orchestration operations."""

    def __init__(self):
        super().__init__(PromptOrchestrator())

    async def handle_create_conditional_chain(self, chain_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Create a conditional prompt chain."""
        try:
            chain = await self.service.create_conditional_chain(chain_definition)
            return create_success_response(
                message="Conditional chain created successfully",
                data=chain
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to create conditional chain: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_execute_chain(self, chain_id: str, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a conditional chain."""
        try:
            execution = await self.service.execute_conditional_chain(chain_id, initial_context)
            return create_success_response(
                message="Chain execution completed",
                data=execution
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to execute chain: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_create_pipeline(self, pipeline_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Create a prompt pipeline."""
        try:
            pipeline = await self.service.create_pipeline(pipeline_definition)
            return create_success_response(
                message="Pipeline created successfully",
                data=pipeline
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to create pipeline: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_execute_pipeline(self, pipeline_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a pipeline."""
        try:
            execution = await self.service.execute_pipeline(pipeline_id, input_data)
            return create_success_response(
                message="Pipeline execution completed",
                data=execution
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to execute pipeline: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_select_optimal_prompt(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Select optimal prompt for a task."""
        try:
            prompt_id = await self.service.select_optimal_prompt(task_description, context)
            return create_success_response(
                message="Optimal prompt selected",
                data={"prompt_id": prompt_id, "task_description": task_description}
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to select optimal prompt: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_get_recommendations(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get prompt recommendations for a task."""
        try:
            recommendations = await self.service.get_prompt_recommendations(task_description, context)
            return create_success_response(
                message="Prompt recommendations retrieved",
                data={"recommendations": recommendations, "task_description": task_description}
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to get recommendations: {str(e)}", "INTERNAL_ERROR").model_dump()
