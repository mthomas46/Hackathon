"""LLM Gateway Integration Module for Orchestrator Service.

Provides integration between the Orchestrator service and LLM Gateway for:
- LLM-powered workflow orchestration
- Dynamic workflow generation based on natural language requests
- Intelligent service coordination with LLM assistance
- Workflow optimization using LLM analysis
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.shared.clients import ServiceClients
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget
from services.shared.config import get_config_value


class LLMGatewayIntegration:
    """Integration layer between Orchestrator and LLM Gateway."""

    def __init__(self):
        self.clients = ServiceClients()
        self.llm_gateway_url = get_config_value("LLM_GATEWAY_URL", "http://llm-gateway:5055", section="services")
        self.interpreter_url = get_config_value("INTERPRETER_URL", "http://interpreter:5120", section="services")

    async def generate_workflow_from_nlp(self, natural_language_request: str,
                                       available_services: List[str],
                                       user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a complete workflow from a natural language request using LLM Gateway."""
        try:
            # First, interpret the request using the interpreter service
            interpretation = await self.clients.post_json(
                f"{self.interpreter_url}/interpret",
                {
                    "query": natural_language_request,
                    "context": user_context or {},
                    "user_id": user_context.get("user_id") if user_context else None
                }
            )

            if not interpretation.get("success"):
                return {
                    "error": "Failed to interpret natural language request",
                    "interpretation_error": interpretation.get("message")
                }

            intent_data = interpretation["data"]

            # Use LLM Gateway to generate detailed workflow
            workflow_prompt = f"""
You are an expert workflow orchestrator. Create a detailed workflow specification based on the following interpreted request.

Interpreted Request:
- Query: {natural_language_request}
- Primary Intent: {intent_data.get('intent', 'unknown')}
- Entities: {intent_data.get('entities', [])}
- Categories: {intent_data.get('categories', [])}
- Suggested Services: {intent_data.get('suggested_services', [])}

Available Services: {', '.join(available_services)}

Create a workflow specification that includes:
1. Workflow name and description
2. Sequence of steps with service assignments
3. Data flow between steps
4. Error handling strategies
5. Success criteria
6. Estimated execution time
7. Resource requirements

Return the workflow specification as a JSON object with keys: name, description, steps, data_flow, error_handling, success_criteria, estimated_duration, resource_requirements
            """.strip()

            llm_request = {
                "prompt": workflow_prompt,
                "provider": "ollama",
                "max_tokens": 1500,
                "temperature": 0.4
            }

            response = await self.clients.post_json(f"{self.llm_gateway_url}/query", llm_request)

            if response.get("success"):
                llm_response = response["data"]["response"]
                try:
                    import json
                    workflow_spec = json.loads(llm_response)

                    # Enhance with additional metadata
                    workflow_spec["generated_from"] = {
                        "original_request": natural_language_request,
                        "interpretation": intent_data,
                        "llm_provider": response["data"]["provider"],
                        "generation_timestamp": datetime.now().isoformat()
                    }

                    return {
                        "workflow_specification": workflow_spec,
                        "generation_method": "llm_enhanced",
                        "confidence_score": 0.85,
                        "available_services": available_services
                    }

                except json.JSONDecodeError:
                    return {
                        "error": "Failed to parse LLM-generated workflow specification",
                        "raw_response": llm_response[:1000],
                        "llm_provider": response["data"]["provider"]
                    }
            else:
                return {
                    "error": "LLM Gateway request failed",
                    "llm_error": response.get("message")
                }

        except Exception as e:
            fire_and_forget(
                "orchestrator_llm_workflow_generation_error",
                f"LLM workflow generation error: {str(e)}",
                ServiceNames.ORCHESTRATOR,
                {
                    "request": natural_language_request[:100],
                    "available_services_count": len(available_services),
                    "error": str(e)
                }
            )
            return {
                "error": f"Workflow generation failed: {str(e)}",
                "request": natural_language_request,
                "available_services": available_services
            }

    async def optimize_workflow_execution(self, workflow_spec: Dict[str, Any],
                                       execution_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Use LLM Gateway to optimize workflow execution based on historical performance."""
        try:
            history_summary = "No execution history available"
            if execution_history:
                successful_executions = [h for h in execution_history if h.get("success", False)]
                failed_executions = [h for h in execution_history if not h.get("success", False)]

                history_summary = f"""
                Execution History Summary:
                - Total executions: {len(execution_history)}
                - Successful: {len(successful_executions)}
                - Failed: {len(failed_executions)}
                - Success rate: {len(successful_executions)/len(execution_history)*100:.1f}%

                Common failure patterns: {[h.get('error', 'unknown') for h in failed_executions[:3]]}
                Average execution time: {sum(h.get('duration', 0) for h in execution_history)/len(execution_history):.2f}s
                """

            optimization_prompt = f"""
You are an expert workflow optimizer. Analyze the following workflow specification and execution history to provide optimization recommendations.

Workflow Specification:
{workflow_spec}

{history_summary}

Provide optimization recommendations including:
1. Step reordering for better performance
2. Parallel execution opportunities
3. Resource allocation improvements
4. Error handling enhancements
5. Caching strategies
6. Alternative service selections

Return your analysis as a JSON object with keys: optimizations, performance_improvements, risk_reductions, implementation_priority
            """.strip()

            llm_request = {
                "prompt": optimization_prompt,
                "provider": "ollama",
                "max_tokens": 1200,
                "temperature": 0.3
            }

            response = await self.clients.post_json(f"{self.llm_gateway_url}/query", llm_request)

            if response.get("success"):
                llm_response = response["data"]["response"]
                try:
                    import json
                    optimization_recommendations = json.loads(llm_response)
                    return {
                        "optimization_recommendations": optimization_recommendations,
                        "original_workflow": workflow_spec,
                        "analysis_method": "llm_enhanced",
                        "llm_provider": response["data"]["provider"]
                    }
                except json.JSONDecodeError:
                    return {
                        "optimization_recommendations": {
                            "optimizations": [],
                            "performance_improvements": [],
                            "risk_reductions": []
                        },
                        "error": "Failed to parse optimization recommendations",
                        "raw_response": llm_response[:500]
                    }
            else:
                return {
                    "optimization_recommendations": {
                        "optimizations": [],
                        "performance_improvements": [],
                        "risk_reductions": []
                    },
                    "error": response.get("message", "LLM Gateway request failed")
                }

        except Exception as e:
            fire_and_forget(
                "orchestrator_workflow_optimization_error",
                f"Workflow optimization error: {str(e)}",
                ServiceNames.ORCHESTRATOR,
                {
                    "workflow_steps": len(workflow_spec.get("steps", [])),
                    "execution_history_count": len(execution_history) if execution_history else 0,
                    "error": str(e)
                }
            )
            return {
                "optimization_recommendations": {
                    "optimizations": [],
                    "performance_improvements": [],
                    "risk_reductions": []
                },
                "error": str(e)
            }

    async def intelligent_service_selection(self, task_description: str,
                                         available_services: List[Dict[str, Any]],
                                         constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Use LLM Gateway to intelligently select the best services for a task."""
        try:
            services_description = "\n".join([
                f"- {service.get('name', 'Unknown')}: {service.get('description', 'No description')} "
                f"(Capabilities: {', '.join(service.get('capabilities', []))})"
                for service in available_services
            ])

            constraints_str = ""
            if constraints:
                constraints_str = f"\nConstraints: {constraints}"

            selection_prompt = f"""
You are an expert service selection advisor. For the following task, recommend the most appropriate services from the available options.

Task: {task_description}

Available Services:
{services_description}
{constraints_str}

Consider:
1. Service capabilities match with task requirements
2. Service reliability and performance
3. Cost-effectiveness
4. Integration complexity
5. Scalability and resource requirements
6. Security and compliance requirements

Return your recommendation as a JSON object with keys: primary_service, supporting_services, reasoning, confidence_score, alternative_options
            """.strip()

            llm_request = {
                "prompt": selection_prompt,
                "provider": "ollama",
                "max_tokens": 1000,
                "temperature": 0.3
            }

            response = await self.clients.post_json(f"{self.llm_gateway_url}/query", llm_request)

            if response.get("success"):
                llm_response = response["data"]["response"]
                try:
                    import json
                    service_recommendation = json.loads(llm_response)
                    return {
                        "service_recommendation": service_recommendation,
                        "selection_method": "llm_intelligent",
                        "available_services_count": len(available_services),
                        "llm_provider": response["data"]["provider"]
                    }
                except json.JSONDecodeError:
                    return {
                        "service_recommendation": {
                            "primary_service": available_services[0].get("name") if available_services else "none",
                            "supporting_services": [],
                            "reasoning": "Failed to parse LLM response",
                            "confidence_score": 0.0
                        },
                        "error": "JSON parsing failed",
                        "raw_response": llm_response[:500]
                    }
            else:
                return {
                    "service_recommendation": {
                        "primary_service": available_services[0].get("name") if available_services else "none",
                        "supporting_services": [],
                        "reasoning": "LLM Gateway request failed",
                        "confidence_score": 0.0
                    },
                    "error": response.get("message", "LLM Gateway request failed")
                }

        except Exception as e:
            fire_and_forget(
                "orchestrator_service_selection_error",
                f"Intelligent service selection error: {str(e)}",
                ServiceNames.ORCHESTRATOR,
                {
                    "task_description": task_description[:100],
                    "available_services_count": len(available_services),
                    "error": str(e)
                }
            )
            return {
                "service_recommendation": {
                    "primary_service": available_services[0].get("name") if available_services else "none",
                    "supporting_services": [],
                    "reasoning": str(e),
                    "confidence_score": 0.0
                },
                "error": str(e)
            }

    async def analyze_workflow_performance(self, workflow_execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM Gateway to analyze workflow performance and provide insights."""
        try:
            analysis_prompt = f"""
You are a workflow performance analyst. Analyze the following workflow execution data and provide insights.

Workflow Execution Data:
{workflow_execution_data}

Provide analysis including:
1. Performance bottlenecks and their causes
2. Resource utilization efficiency
3. Service interaction patterns
4. Potential optimization opportunities
5. Reliability and error pattern analysis
6. Scalability recommendations

Return your analysis as a JSON object with keys: bottlenecks, efficiency_analysis, optimization_opportunities, reliability_insights, scalability_recommendations, actionable_insights
            """.strip()

            llm_request = {
                "prompt": analysis_prompt,
                "provider": "ollama",
                "max_tokens": 1200,
                "temperature": 0.2
            }

            response = await self.clients.post_json(f"{self.llm_gateway_url}/query", llm_request)

            if response.get("success"):
                llm_response = response["data"]["response"]
                try:
                    import json
                    performance_analysis = json.loads(llm_response)
                    return {
                        "performance_analysis": performance_analysis,
                        "analysis_method": "llm_enhanced",
                        "workflow_data": workflow_execution_data,
                        "llm_provider": response["data"]["provider"]
                    }
                except json.JSONDecodeError:
                    return {
                        "performance_analysis": {
                            "bottlenecks": [],
                            "efficiency_analysis": {},
                            "optimization_opportunities": []
                        },
                        "error": "Failed to parse performance analysis",
                        "raw_response": llm_response[:500]
                    }
            else:
                return {
                    "performance_analysis": {
                        "bottlenecks": [],
                        "efficiency_analysis": {},
                        "optimization_opportunities": []
                    },
                    "error": response.get("message", "LLM Gateway request failed")
                }

        except Exception as e:
            fire_and_forget(
                "orchestrator_performance_analysis_error",
                f"Performance analysis error: {str(e)}",
                ServiceNames.ORCHESTRATOR,
                {
                    "workflow_steps": len(workflow_execution_data.get("steps", [])),
                    "error": str(e)
                }
            )
            return {
                "performance_analysis": {
                    "bottlenecks": [],
                    "efficiency_analysis": {},
                    "optimization_opportunities": []
                },
                "error": str(e)
            }


# Global instance
llm_gateway_integration = LLMGatewayIntegration()
