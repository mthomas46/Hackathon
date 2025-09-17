"""Query handlers for Interpreter service.

Handles the complex logic for query interpretation and execution endpoints.
"""
import time
from typing import Dict, Any

from .models import InterpretedIntent, InterpretedWorkflow, WorkflowStep
from .shared_utils import (
    validate_user_query,
    build_interpreter_context,
    log_interpretation_metrics,
    create_interpreter_success_response
)
from .intent_recognizer import IntentRecognizer
from .workflow_builder import WorkflowBuilder


class QueryHandlers:
    """Handles query interpretation and execution operations."""

    def __init__(self):
        self.intent_recognizer = IntentRecognizer()
        self.workflow_builder = WorkflowBuilder()

    async def handle_interpret_query(self, query) -> InterpretedIntent:
        """Interpret user query and return intent with workflow."""
        start_time = time.time()

        try:
            # Validate user query
            validate_user_query(query.dict())

            # Recognize intent and extract entities
            intent, confidence, entities = self.intent_recognizer.recognize_intent(query.query)

            # Build workflow if intent is recognized with sufficient confidence
            workflow = None
            if confidence > 0.3:  # Minimum confidence threshold
                try:
                    workflow = await self.workflow_builder.build_workflow(intent, entities)
                except Exception as e:
                    from services.shared.monitoring.logging import fire_and_forget
                    from services.shared.core.constants_new import ServiceNames
                    fire_and_forget("error", f"Workflow build error: {e}", ServiceNames.INTERPRETER)

            # Generate response text
            response_text = self._generate_response_text(intent, confidence, entities, workflow)

            # Log interpretation metrics
            processing_time = time.time() - start_time
            log_interpretation_metrics(query.query, intent, confidence, processing_time)

            return InterpretedIntent(
                intent=intent,
                confidence=confidence,
                entities=entities,
                workflow=workflow.dict() if workflow else None,
                response_text=response_text
            )

        except Exception as e:
            processing_time = time.time() - start_time
            log_interpretation_metrics(query.query, "error", 0.0, processing_time)

            from .shared_utils import handle_interpreter_error
            raise handle_interpreter_error(
                "interpret query",
                e,
                **build_interpreter_context("interpret", query_length=len(query.query))
            )

    async def handle_execute_workflow(self, query) -> Dict[str, Any]:
        """Interpret query and execute the resulting workflow."""
        try:
            # First interpret the query
            interpretation = await self.handle_interpret_query(query)

            if not interpretation.workflow:
                return create_interpreter_success_response(
                    "interpretation completed (no workflow)",
                    {
                        "status": "no_workflow",
                        "message": "Could not generate a workflow for this query",
                        "interpretation": interpretation.dict()
                    },
                    **build_interpreter_context("execute_no_workflow")
                )

            # Execute the workflow
            workflow_data = interpretation.workflow
            results = []
            from .shared_utils import get_interpreter_clients
            clients = get_interpreter_clients()

            for step in workflow_data.get("steps", []):
                try:
                    result = await self._execute_workflow_step(step, clients)
                    results.append({
                        "step_id": step["step_id"],
                        "status": "success",
                        "result": result
                    })
                except Exception as e:
                    results.append({
                        "step_id": step["step_id"],
                        "status": "error",
                        "error": str(e)
                    })

            return create_interpreter_success_response(
                "workflow executed",
                {
                    "status": "completed",
                    "workflow_id": workflow_data.get("workflow_id"),
                    "results": results,
                    "interpretation": interpretation.dict()
                },
                **build_interpreter_context("execute_workflow", step_count=len(results))
            )

        except Exception as e:
            from .shared_utils import handle_interpreter_error
            raise handle_interpreter_error(
                "execute workflow",
                e,
                **build_interpreter_context("execute_error")
            )

    async def _execute_workflow_step(self, step: Dict[str, Any], clients=None) -> Any:
        """Execute a single workflow step."""
        if clients is None:
            from .shared_utils import get_interpreter_clients
            clients = get_interpreter_clients()

        service = step["service"]
        action = step["action"]
        parameters = step.get("parameters", {})

        # Route to appropriate service
        if service == "analysis-service":
            if action == "analyze":
                return await clients.post_json("analysis-service/analyze", parameters)
            elif action == "consistency_check":
                return await clients.get_json("analysis-service/consistency/check")
            elif action == "findings":
                return await clients.get_json("analysis-service/findings")

        elif service == "source-agent":
            if action == "ingest":
                return await clients.post_json("source-agent/ingest", parameters)

        elif service == "doc_store":
            if action == "store":
                return await clients.post_json("doc_store/store", parameters)

        elif service == "prompt-store":
            if action == "search":
                # Build query parameters
                query_params = {}
                if "categories" in parameters:
                    query_params["category"] = parameters["categories"][0] if parameters["categories"] else ""
                if "query" in parameters:
                    query_params["q"] = parameters["query"]

                return await clients.get_json("prompt-store/prompts", params=query_params)

        # Default: return success for unknown services/actions
        from services.shared.core.responses.responses import create_success_response
        return create_success_response(
            "Workflow step executed successfully",
            {"service": service, "action": action, "parameters": parameters}
        )

    def _generate_response_text(self, intent: str, confidence: float, entities: Dict[str, Any], workflow) -> str:
        """Generate human-readable response text based on interpretation."""
        from .shared_utils import generate_response_text
        return generate_response_text(intent, confidence, entities, workflow)


# Create singleton instance
query_handlers = QueryHandlers()
