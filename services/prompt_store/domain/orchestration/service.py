"""Dynamic prompt orchestration service for conditional chains and pipelines."""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from ...shared.clients import ServiceClients
from ...shared.utilities import generate_id, utc_now
from ...infrastructure.cache import prompt_store_cache


class PromptOrchestrator:
    """Service for orchestrating complex prompt workflows."""

    def __init__(self):
        self.clients = ServiceClients()
        self.active_pipelines: Dict[str, Dict[str, Any]] = {}

    async def create_conditional_chain(self, chain_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Create a conditional prompt chain."""
        chain_id = generate_id()

        chain = {
            "id": chain_id,
            "name": chain_definition.get("name", "Conditional Chain"),
            "description": chain_definition.get("description", ""),
            "steps": chain_definition.get("steps", []),
            "conditions": chain_definition.get("conditions", {}),
            "created_at": utc_now().isoformat(),
            "status": "created"
        }

        # Cache the chain
        await prompt_store_cache.set(f"chain:{chain_id}", chain, ttl=3600)

        return chain

    async def execute_conditional_chain(self, chain_id: str, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a conditional prompt chain."""
        # Get chain definition
        chain = await prompt_store_cache.get(f"chain:{chain_id}")
        if not chain:
            return {"error": "Chain not found"}

        execution_id = generate_id()
        execution = {
            "id": execution_id,
            "chain_id": chain_id,
            "status": "running",
            "current_step": 0,
            "context": initial_context.copy(),
            "step_results": [],
            "started_at": utc_now().isoformat()
        }

        self.active_pipelines[execution_id] = execution

        try:
            # Execute chain steps
            for step_idx, step in enumerate(chain["steps"]):
                execution["current_step"] = step_idx

                # Check conditions for this step
                if not await self._check_step_conditions(step, execution["context"]):
                    continue  # Skip this step

                # Execute the step
                step_result = await self._execute_step(step, execution["context"])
                execution["step_results"].append(step_result)

                # Update context with step results
                execution["context"].update(step_result.get("outputs", {}))

                # Check for early termination conditions
                if step_result.get("terminate_chain", False):
                    break

            execution["status"] = "completed"
            execution["completed_at"] = utc_now().isoformat()

        except Exception as e:
            execution["status"] = "failed"
            execution["error"] = str(e)

        # Cache final execution state
        await prompt_store_cache.set(f"execution:{execution_id}", execution, ttl=3600)

        return execution

    async def _check_step_conditions(self, step: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if conditions are met for executing a step."""
        conditions = step.get("conditions", [])

        for condition in conditions:
            condition_type = condition.get("type")
            field = condition.get("field")
            operator = condition.get("operator", "equals")
            value = condition.get("value")

            if field not in context:
                return False

            actual_value = context[field]

            if operator == "equals" and actual_value != value:
                return False
            elif operator == "not_equals" and actual_value == value:
                return False
            elif operator == "contains" and value not in str(actual_value):
                return False
            elif operator == "greater_than" and actual_value <= value:
                return False
            elif operator == "less_than" and actual_value >= value:
                return False

        return True

    async def _execute_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step in the chain."""
        step_type = step.get("type", "prompt")

        if step_type == "prompt":
            return await self._execute_prompt_step(step, context)
        elif step_type == "llm_call":
            return await self._execute_llm_step(step, context)
        elif step_type == "condition_check":
            return await self._execute_condition_step(step, context)
        elif step_type == "data_transformation":
            return await self._execute_transformation_step(step, context)
        else:
            return {"error": f"Unknown step type: {step_type}"}

    async def _execute_prompt_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a prompt step using the prompt store."""
        prompt_id = step.get("prompt_id")
        variables = step.get("variables", {})

        # Merge context variables
        final_variables = context.copy()
        final_variables.update(variables)

        try:
            # Call interpreter service to execute the prompt
            prompt_data = {
                "prompt_id": prompt_id,
                "variables": final_variables,
                "context": context
            }

            # This would call the interpreter service
            response = await self.clients.interpret_query(
                f"Execute prompt {prompt_id} with variables: {final_variables}",
                "orchestrator"
            )

            return {
                "step_type": "prompt",
                "prompt_id": prompt_id,
                "success": True,
                "outputs": {
                    "response": response.get("data", {}).get("response_text", ""),
                    "execution_time": response.get("execution_time", 0)
                }
            }

        except Exception as e:
            return {
                "step_type": "prompt",
                "prompt_id": prompt_id,
                "success": False,
                "error": str(e)
            }

    async def _execute_llm_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a direct LLM call step."""
        prompt_template = step.get("prompt_template", "")
        service = step.get("llm_service", "interpreter")

        # Fill template with context
        filled_prompt = self._fill_template(prompt_template, context)

        try:
            response = await self.clients.interpret_query(filled_prompt, "orchestrator")

            return {
                "step_type": "llm_call",
                "service": service,
                "success": True,
                "outputs": {
                    "response": response.get("data", {}).get("response_text", ""),
                    "raw_response": response
                }
            }

        except Exception as e:
            return {
                "step_type": "llm_call",
                "service": service,
                "success": False,
                "error": str(e)
            }

    async def _execute_condition_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a condition checking step."""
        conditions = step.get("check_conditions", [])
        all_met = True

        for condition in conditions:
            if not await self._check_step_conditions({"conditions": [condition]}, context):
                all_met = False
                break

        return {
            "step_type": "condition_check",
            "conditions_met": all_met,
            "outputs": {
                "condition_result": all_met
            }
        }

    async def _execute_transformation_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a data transformation step."""
        transformations = step.get("transformations", [])

        transformed_data = context.copy()

        for transformation in transformations:
            transform_type = transformation.get("type")
            input_field = transformation.get("input_field")
            output_field = transformation.get("output_field", input_field)

            if input_field not in transformed_data:
                continue

            input_value = transformed_data[input_field]

            if transform_type == "uppercase":
                transformed_data[output_field] = str(input_value).upper()
            elif transform_type == "lowercase":
                transformed_data[output_field] = str(input_value).lower()
            elif transform_type == "split":
                delimiter = transformation.get("delimiter", " ")
                transformed_data[output_field] = str(input_value).split(delimiter)
            elif transform_type == "join":
                delimiter = transformation.get("delimiter", " ")
                if isinstance(input_value, list):
                    transformed_data[output_field] = delimiter.join(input_value)
            elif transform_type == "extract_json":
                # Simple JSON extraction (would need more robust parsing)
                import json
                try:
                    transformed_data[output_field] = json.loads(str(input_value))
                except:
                    transformed_data[output_field] = input_value

        return {
            "step_type": "data_transformation",
            "success": True,
            "outputs": transformed_data
        }

    def _fill_template(self, template: str, context: Dict[str, Any]) -> str:
        """Fill template variables with context values."""
        result = template
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))
        return result

    # Pipeline Management
    async def create_pipeline(self, pipeline_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Create a prompt pipeline."""
        pipeline_id = generate_id()

        pipeline = {
            "id": pipeline_id,
            "name": pipeline_definition.get("name", "Pipeline"),
            "description": pipeline_definition.get("description", ""),
            "stages": pipeline_definition.get("stages", []),
            "configuration": pipeline_definition.get("configuration", {}),
            "created_at": utc_now().isoformat(),
            "status": "created"
        }

        await prompt_store_cache.set(f"pipeline:{pipeline_id}", pipeline, ttl=3600)
        return pipeline

    async def execute_pipeline(self, pipeline_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a pipeline with input data."""
        pipeline = await prompt_store_cache.get(f"pipeline:{pipeline_id}")
        if not pipeline:
            return {"error": "Pipeline not found"}

        execution_id = generate_id()
        execution = {
            "id": execution_id,
            "pipeline_id": pipeline_id,
            "status": "running",
            "current_stage": 0,
            "data": input_data.copy(),
            "stage_results": [],
            "started_at": utc_now().isoformat()
        }

        try:
            # Execute pipeline stages
            for stage_idx, stage in enumerate(pipeline["stages"]):
                execution["current_stage"] = stage_idx

                # Execute stage
                stage_result = await self._execute_pipeline_stage(stage, execution["data"])
                execution["stage_results"].append(stage_result)

                # Update data with stage outputs
                if "outputs" in stage_result:
                    execution["data"].update(stage_result["outputs"])

            execution["status"] = "completed"
            execution["completed_at"] = utc_now().isoformat()

        except Exception as e:
            execution["status"] = "failed"
            execution["error"] = str(e)

        await prompt_store_cache.set(f"pipeline_execution:{execution_id}", execution, ttl=3600)
        return execution

    async def _execute_pipeline_stage(self, stage: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single pipeline stage."""
        stage_type = stage.get("type")

        if stage_type == "parallel_prompts":
            return await self._execute_parallel_stage(stage, data)
        elif stage_type == "sequential_prompts":
            return await self._execute_sequential_stage(stage, data)
        elif stage_type == "aggregation":
            return await self._execute_aggregation_stage(stage, data)
        else:
            return {"error": f"Unknown stage type: {stage_type}"}

    async def _execute_parallel_stage(self, stage: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute prompts in parallel."""
        prompts = stage.get("prompts", [])

        # Execute all prompts concurrently
        tasks = []
        for prompt_config in prompts:
            task = self._execute_prompt_config(prompt_config, data)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        outputs = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                outputs[f"prompt_{i}_error"] = str(result)
            else:
                outputs.update(result.get("outputs", {}))

        return {
            "stage_type": "parallel_prompts",
            "success": True,
            "outputs": outputs
        }

    async def _execute_sequential_stage(self, stage: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute prompts sequentially, passing results between them."""
        prompts = stage.get("prompts", [])
        current_data = data.copy()

        for prompt_config in prompts:
            result = await self._execute_prompt_config(prompt_config, current_data)
            if result.get("success"):
                current_data.update(result.get("outputs", {}))

        return {
            "stage_type": "sequential_prompts",
            "success": True,
            "outputs": current_data
        }

    async def _execute_aggregation_stage(self, stage: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from multiple sources."""
        aggregation_type = stage.get("aggregation_type", "concatenate")
        input_fields = stage.get("input_fields", [])
        output_field = stage.get("output_field", "aggregated_result")

        values = []
        for field in input_fields:
            if field in data:
                values.append(str(data[field]))

        if aggregation_type == "concatenate":
            result = " ".join(values)
        elif aggregation_type == "summarize":
            # Use LLM to summarize
            summary_prompt = f"Summarize the following information: {' '.join(values)}"
            llm_response = await self.clients.interpret_query(summary_prompt, "orchestrator")
            result = llm_response.get("data", {}).get("response_text", " ".join(values))
        else:
            result = values[0] if values else ""

        return {
            "stage_type": "aggregation",
            "success": True,
            "outputs": {output_field: result}
        }

    async def _execute_prompt_config(self, prompt_config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single prompt configuration."""
        # Simplified version - would call actual prompt execution
        return {
            "success": True,
            "outputs": {"result": f"Executed {prompt_config.get('name', 'prompt')}"}
        }

    # Context-Aware Prompt Selection
    async def select_optimal_prompt(self, task_description: str, context: Dict[str, Any] = None) -> Optional[str]:
        """Select the optimal prompt for a given task based on context."""
        context = context or {}

        # This would analyze available prompts and select the best one
        # For now, return a mock selection
        return "default_prompt_id"

    async def get_prompt_recommendations(self, task_description: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get prompt recommendations for a task."""
        # Analyze task and context to recommend prompts
        recommendations = [
            {
                "prompt_id": "code_generation_v1",
                "confidence": 0.85,
                "reason": "Best for code generation tasks"
            },
            {
                "prompt_id": "content_writing_v2",
                "confidence": 0.72,
                "reason": "Good alternative for structured content"
            }
        ]

        return recommendations
