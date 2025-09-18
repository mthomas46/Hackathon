"""LLM Gateway Integration Module for Interpreter Service.

Provides integration between the Interpreter service and LLM Gateway for:
- Enhanced natural language understanding using LLM capabilities
- Query preprocessing and optimization
- Entity extraction with LLM assistance
- Intent classification with LLM-powered analysis
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.shared.clients import ServiceClients
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget
from services.shared.config import get_config_value


class LLMGatewayIntegration:
    """Integration layer between Interpreter and LLM Gateway."""

    def __init__(self):
        self.clients = ServiceClients()
        self.llm_gateway_url = get_config_value("LLM_GATEWAY_URL", "http://llm-gateway:5055", section="services")

    async def enhance_query_understanding(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Use LLM Gateway to enhance query understanding."""
        try:
            enhanced_prompt = f"""
You are an expert at understanding user queries in the context of a documentation ecosystem.

Analyze the following query and provide:
1. The primary intent of the query
2. Key entities mentioned
3. Suggested categories for the query
4. Potential follow-up questions
5. Recommended services that could help

Query: {query}
Context: {context or 'No additional context provided'}

Provide your analysis in JSON format with keys: intent, entities, categories, follow_ups, services
            """.strip()

            llm_request = {
                "prompt": enhanced_prompt,
                "provider": "ollama",  # Use local for cost efficiency
                "max_tokens": 500,
                "temperature": 0.3
            }

            response = await self.clients.post_json(f"{self.llm_gateway_url}/query", llm_request)

            if response.get("success"):
                # Parse LLM response as JSON
                llm_response = response["data"]["response"]
                try:
                    import json
                    analysis = json.loads(llm_response)
                    return {
                        "enhanced_understanding": analysis,
                        "original_query": query,
                        "llm_used": response["data"]["provider"],
                        "confidence_score": 0.8  # Could be calculated based on response quality
                    }
                except json.JSONDecodeError:
                    return {
                        "enhanced_understanding": {"intent": "unknown", "entities": [], "categories": []},
                        "original_query": query,
                        "llm_used": response["data"]["provider"],
                        "error": "Failed to parse LLM response as JSON"
                    }
            else:
                return {
                    "enhanced_understanding": {"intent": "unknown", "entities": [], "categories": []},
                    "original_query": query,
                    "error": response.get("message", "LLM Gateway request failed")
                }

        except Exception as e:
            fire_and_forget(
                "interpreter_llm_gateway_integration_error",
                f"LLM Gateway integration error: {str(e)}",
                ServiceNames.INTERPRETER,
                {"query": query[:100], "error": str(e)}
            )
            return {
                "enhanced_understanding": {"intent": "unknown", "entities": [], "categories": []},
                "original_query": query,
                "error": str(e)
            }

    async def optimize_prompt_for_llm(self, original_prompt: str, task_type: str) -> str:
        """Use LLM Gateway to optimize prompts for better LLM performance."""
        try:
            optimization_prompt = f"""
You are an expert prompt engineer. Optimize the following prompt for a {task_type} task.

Original prompt: {original_prompt}

Provide an optimized version that:
1. Is clear and specific
2. Includes relevant context
3. Uses effective prompting techniques
4. Is concise but comprehensive
5. Includes examples if helpful

Return only the optimized prompt, no explanation.
            """.strip()

            llm_request = {
                "prompt": optimization_prompt,
                "provider": "ollama",
                "max_tokens": 1000,
                "temperature": 0.7
            }

            response = await self.clients.post_json(f"{self.llm_gateway_url}/query", llm_request)

            if response.get("success"):
                return response["data"]["response"].strip()
            else:
                return original_prompt

        except Exception as e:
            fire_and_forget(
                "interpreter_prompt_optimization_error",
                f"Prompt optimization error: {str(e)}",
                ServiceNames.INTERPRETER,
                {"original_prompt_length": len(original_prompt), "error": str(e)}
            )
            return original_prompt

    async def extract_entities_with_llm(self, text: str, entity_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Use LLM Gateway for advanced entity extraction."""
        try:
            entity_types_str = ", ".join(entity_types) if entity_types else "any relevant entities"

            extraction_prompt = f"""
Extract {entity_types_str} from the following text. Return the results as a JSON object with entity types as keys and lists of extracted entities as values.

Text: {text}

Example format:
{{
    "persons": ["John Doe", "Jane Smith"],
    "organizations": ["Acme Corp"],
    "locations": ["New York"],
    "dates": ["2024-01-15"],
    "technologies": ["Python", "Docker"]
}}
            """.strip()

            llm_request = {
                "prompt": extraction_prompt,
                "provider": "ollama",
                "max_tokens": 1000,
                "temperature": 0.2
            }

            response = await self.clients.post_json(f"{self.llm_gateway_url}/query", llm_request)

            if response.get("success"):
                llm_response = response["data"]["response"]
                try:
                    import json
                    entities = json.loads(llm_response)
                    return {
                        "entities": entities,
                        "extraction_method": "llm_enhanced",
                        "confidence": 0.85,
                        "llm_provider": response["data"]["provider"]
                    }
                except json.JSONDecodeError:
                    return {
                        "entities": {},
                        "extraction_method": "llm_enhanced",
                        "error": "Failed to parse LLM response as JSON",
                        "raw_response": llm_response[:500]
                    }
            else:
                return {
                    "entities": {},
                    "extraction_method": "llm_enhanced",
                    "error": response.get("message", "LLM Gateway request failed")
                }

        except Exception as e:
            fire_and_forget(
                "interpreter_entity_extraction_error",
                f"LLM-enhanced entity extraction error: {str(e)}",
                ServiceNames.INTERPRETER,
                {"text_length": len(text), "error": str(e)}
            )
            return {
                "entities": {},
                "extraction_method": "llm_enhanced",
                "error": str(e)
            }

    async def classify_intent_with_llm(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Use LLM Gateway for advanced intent classification."""
        try:
            context_str = f"\nContext: {context}" if context else ""

            classification_prompt = f"""
Classify the intent of the following query in the context of a documentation ecosystem.

Query: {query}{context_str}

Possible intents:
- search_documentation: Looking for specific documentation or information
- create_content: Requesting to generate new documentation or content
- analyze_code: Requesting code analysis or review
- workflow_execution: Requesting to execute a multi-step process
- system_status: Checking system or service status
- configuration_change: Requesting configuration modifications
- troubleshooting: Seeking help with problems or issues
- learning_education: Requesting educational content or explanations

Return a JSON object with:
- primary_intent: The main intent category
- confidence: Confidence score (0.0-1.0)
- secondary_intents: List of secondary intents (if any)
- reasoning: Brief explanation of the classification
- suggested_actions: List of recommended next steps
            """.strip()

            llm_request = {
                "prompt": classification_prompt,
                "provider": "ollama",
                "max_tokens": 800,
                "temperature": 0.3
            }

            response = await self.clients.post_json(f"{self.llm_gateway_url}/query", llm_request)

            if response.get("success"):
                llm_response = response["data"]["response"]
                try:
                    import json
                    classification = json.loads(llm_response)
                    return {
                        "classification": classification,
                        "method": "llm_enhanced",
                        "llm_provider": response["data"]["provider"],
                        "processing_time": response["data"]["processing_time"]
                    }
                except json.JSONDecodeError:
                    return {
                        "classification": {
                            "primary_intent": "unknown",
                            "confidence": 0.0,
                            "reasoning": "Failed to parse LLM response"
                        },
                        "method": "llm_enhanced",
                        "error": "JSON parsing failed",
                        "raw_response": llm_response[:500]
                    }
            else:
                return {
                    "classification": {
                        "primary_intent": "unknown",
                        "confidence": 0.0,
                        "reasoning": "LLM Gateway request failed"
                    },
                    "method": "llm_enhanced",
                    "error": response.get("message", "LLM Gateway request failed")
                }

        except Exception as e:
            fire_and_forget(
                "interpreter_intent_classification_error",
                f"LLM-enhanced intent classification error: {str(e)}",
                ServiceNames.INTERPRETER,
                {"query": query[:100], "error": str(e)}
            )
            return {
                "classification": {
                    "primary_intent": "unknown",
                    "confidence": 0.0,
                    "reasoning": str(e)
                },
                "method": "llm_enhanced",
                "error": str(e)
            }

    async def generate_workflow_suggestions(self, query: str, available_services: List[str]) -> Dict[str, Any]:
        """Use LLM Gateway to generate workflow suggestions based on query and available services."""
        try:
            services_str = ", ".join(available_services)

            workflow_prompt = f"""
Based on the following query, suggest a workflow that utilizes the available services.

Query: {query}

Available services: {services_str}

Consider:
1. Which services are most relevant to the query
2. The logical sequence of operations
3. Data flow between services
4. Potential parallel processing opportunities
5. Error handling and fallback strategies

Return a JSON object with:
- workflow_steps: Array of workflow steps with service, operation, and parameters
- estimated_duration: Estimated execution time
- success_probability: Estimated success probability (0.0-1.0)
- resource_requirements: Services and resources needed
- alternative_workflows: Array of alternative approaches (if applicable)
            """.strip()

            llm_request = {
                "prompt": workflow_prompt,
                "provider": "ollama",
                "max_tokens": 1200,
                "temperature": 0.4
            }

            response = await self.clients.post_json(f"{self.llm_gateway_url}/query", llm_request)

            if response.get("success"):
                llm_response = response["data"]["response"]
                try:
                    import json
                    workflow_suggestion = json.loads(llm_response)
                    return {
                        "workflow_suggestion": workflow_suggestion,
                        "generated_by": "llm_gateway",
                        "llm_provider": response["data"]["provider"]
                    }
                except json.JSONDecodeError:
                    return {
                        "workflow_suggestion": {
                            "workflow_steps": [],
                            "estimated_duration": "unknown",
                            "success_probability": 0.0
                        },
                        "generated_by": "llm_gateway",
                        "error": "Failed to parse LLM response as JSON",
                        "raw_response": llm_response[:500]
                    }
            else:
                return {
                    "workflow_suggestion": {
                        "workflow_steps": [],
                        "estimated_duration": "unknown",
                        "success_probability": 0.0
                    },
                    "generated_by": "llm_gateway",
                    "error": response.get("message", "LLM Gateway request failed")
                }

        except Exception as e:
            fire_and_forget(
                "interpreter_workflow_suggestion_error",
                f"Workflow suggestion error: {str(e)}",
                ServiceNames.INTERPRETER,
                {"query": query[:100], "available_services": available_services, "error": str(e)}
            )
            return {
                "workflow_suggestion": {
                    "workflow_steps": [],
                    "estimated_duration": "unknown",
                    "success_probability": 0.0
                },
                "generated_by": "llm_gateway",
                "error": str(e)
            }


# Global instance
llm_gateway_integration = LLMGatewayIntegration()
