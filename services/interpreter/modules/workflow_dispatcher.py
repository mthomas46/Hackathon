"""Intelligent Workflow Dispatcher for Interpreter Service.

This module handles the intelligent routing of user queries to appropriate ecosystem workflows,
with deep orchestrator integration and context-aware workflow selection. It understands the
main workflows available in the ecosystem and maps user intents to optimal execution paths.
"""

import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from services.shared.clients import ServiceClients
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget

try:
    from .ecosystem_context import ecosystem_context
    from .orchestrator_integration import orchestrator_integration
    from .conversation_memory import conversation_memory
except ImportError:
    # Handle relative imports for direct execution
    from ecosystem_context import ecosystem_context
    from orchestrator_integration import orchestrator_integration
    from conversation_memory import conversation_memory


class WorkflowDispatcher:
    """Intelligent dispatcher for ecosystem workflows with orchestrator integration."""

    def __init__(self):
        self.client = ServiceClients()
        self.orchestrator_url = "http://orchestrator:5099"
        
        # Define main ecosystem workflows with detailed mapping
        self.main_workflows = {
            "document_analysis": {
                "description": "Comprehensive document analysis and quality assessment",
                "services": ["doc_store", "analysis_service", "summarizer_hub"],
                "capabilities": ["retrieve_documents", "analyze_quality", "generate_summary"],
                "orchestrator_endpoint": "/workflows/document-analysis",
                "langgraph_workflow": "document-analysis",
                "triggers": [
                    "analyze document", "check document quality", "review document",
                    "document analysis", "assess document", "evaluate content"
                ],
                "parameters": {
                    "doc_id": {"type": "string", "required": True},
                    "analysis_types": {"type": "array", "default": ["quality", "consistency", "security"]},
                    "include_summary": {"type": "boolean", "default": True},
                    "generate_report": {"type": "boolean", "default": True}
                },
                "confidence_threshold": 0.8
            },
            
            "code_documentation": {
                "description": "Automated code documentation generation and analysis",
                "services": ["source_agent", "code_analyzer", "doc_store", "summarizer_hub"],
                "capabilities": ["ingest_repository", "analyze_code", "generate_docs", "store_documents"],
                "orchestrator_endpoint": "/workflows/code-documentation",
                "langgraph_workflow": "code-documentation",
                "triggers": [
                    "document code", "generate code docs", "analyze repository", 
                    "code documentation", "repo analysis", "generate docs from code"
                ],
                "parameters": {
                    "repo_url": {"type": "string", "required": True},
                    "doc_types": {"type": "array", "default": ["api", "readme", "architecture"]},
                    "include_examples": {"type": "boolean", "default": True},
                    "auto_commit": {"type": "boolean", "default": False}
                },
                "confidence_threshold": 0.85
            },
            
            "security_audit": {
                "description": "Comprehensive security vulnerability assessment",
                "services": ["secure_analyzer", "code_analyzer", "analysis_service", "notification_service"],
                "capabilities": ["scan_vulnerabilities", "analyze_security", "generate_alerts"],
                "orchestrator_endpoint": "/workflows/security-audit",
                "langgraph_workflow": "security-audit",
                "triggers": [
                    "security scan", "vulnerability check", "security audit",
                    "scan for vulnerabilities", "security assessment", "check security"
                ],
                "parameters": {
                    "target_type": {"type": "string", "default": "full_system"},
                    "scan_types": {"type": "array", "default": ["vulnerabilities", "compliance", "data_safety"]},
                    "severity_threshold": {"type": "string", "default": "medium"},
                    "send_notifications": {"type": "boolean", "default": True}
                },
                "confidence_threshold": 0.9
            },
            
            "content_processing": {
                "description": "Advanced content processing and summarization",
                "services": ["doc_store", "summarizer_hub", "analysis_service"],
                "capabilities": ["retrieve_content", "summarize_content", "analyze_sentiment"],
                "orchestrator_endpoint": "/workflows/content-processing",
                "langgraph_workflow": "content-processing",
                "triggers": [
                    "summarize content", "process content", "content summary",
                    "generate summary", "content processing", "text processing"
                ],
                "parameters": {
                    "content_source": {"type": "string", "required": True},
                    "summary_length": {"type": "string", "default": "medium"},
                    "include_sentiment": {"type": "boolean", "default": True},
                    "format": {"type": "string", "default": "structured"}
                },
                "confidence_threshold": 0.75
            },
            
            "data_ingestion": {
                "description": "Multi-source data ingestion and processing",
                "services": ["source_agent", "github_mcp", "doc_store"],
                "capabilities": ["ingest_github", "ingest_confluence", "store_documents"],
                "orchestrator_endpoint": "/workflows/data-ingestion",
                "langgraph_workflow": "data-ingestion",
                "triggers": [
                    "ingest data", "import from github", "pull from confluence",
                    "data ingestion", "import documents", "sync repository"
                ],
                "parameters": {
                    "source_type": {"type": "string", "required": True},
                    "source_url": {"type": "string", "required": True},
                    "auto_process": {"type": "boolean", "default": True},
                    "notification_on_complete": {"type": "boolean", "default": True}
                },
                "confidence_threshold": 0.8
            },
            
            "prompt_optimization": {
                "description": "AI prompt optimization and management",
                "services": ["prompt_store", "analysis_service", "bedrock_proxy"],
                "capabilities": ["manage_prompts", "optimize_prompts", "test_prompts"],
                "orchestrator_endpoint": "/workflows/prompt-optimization",
                "langgraph_workflow": "prompt-optimization",
                "triggers": [
                    "optimize prompt", "improve prompt", "prompt optimization",
                    "enhance prompt", "prompt tuning", "refine prompt"
                ],
                "parameters": {
                    "prompt_id": {"type": "string", "required": True},
                    "optimization_goals": {"type": "array", "default": ["performance", "clarity", "effectiveness"]},
                    "test_scenarios": {"type": "array", "default": ["default"]},
                    "auto_save": {"type": "boolean", "default": True}
                },
                "confidence_threshold": 0.8
            },
            
            "quality_assurance": {
                "description": "Comprehensive quality assurance workflow",
                "services": ["analysis_service", "secure_analyzer", "code_analyzer", "doc_store"],
                "capabilities": ["quality_analysis", "security_check", "code_review", "compliance_check"],
                "orchestrator_endpoint": "/workflows/quality-assurance",
                "langgraph_workflow": "quality-assurance",
                "triggers": [
                    "quality check", "qa workflow", "quality assurance",
                    "comprehensive review", "quality assessment", "full analysis"
                ],
                "parameters": {
                    "target_type": {"type": "string", "required": True},
                    "qa_checks": {"type": "array", "default": ["quality", "security", "compliance"]},
                    "generate_report": {"type": "boolean", "default": True},
                    "severity_threshold": {"type": "string", "default": "low"}
                },
                "confidence_threshold": 0.85
            },
            
            "research_assistance": {
                "description": "AI-powered research and information gathering",
                "services": ["doc_store", "analysis_service", "summarizer_hub", "memory_agent"],
                "capabilities": ["search_documents", "analyze_content", "synthesize_information"],
                "orchestrator_endpoint": "/workflows/research-assistance",
                "langgraph_workflow": "research-assistance",
                "triggers": [
                    "research topic", "find information", "research assistance",
                    "gather information", "research help", "information synthesis"
                ],
                "parameters": {
                    "research_topic": {"type": "string", "required": True},
                    "search_depth": {"type": "string", "default": "comprehensive"},
                    "include_synthesis": {"type": "boolean", "default": True},
                    "format": {"type": "string", "default": "report"}
                },
                "confidence_threshold": 0.75
            }
        }
        
        # Workflow execution history for learning
        self.execution_history = []
        self.workflow_performance = {}

    async def dispatch_query(self, query: str, intent: str, entities: Dict[str, Any], 
                           user_id: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main dispatch method - routes query to appropriate workflow."""
        try:
            # Get conversation context
            conversation_context = await conversation_memory.get_conversation_context(user_id) if user_id else {}
            
            # Preprocess query for better matching
            processed_query = await self._preprocess_query(query, conversation_context)
            
            # Find best matching workflow
            workflow_match = await self._find_best_workflow_match(
                processed_query, intent, entities, conversation_context
            )
            
            if not workflow_match:
                return await self._handle_no_workflow_match(query, intent, entities, user_id)
            
            # Prepare workflow execution
            execution_plan = await self._prepare_workflow_execution(
                workflow_match, entities, context or {}, user_id
            )
            
            # Execute workflow through orchestrator
            execution_result = await self._execute_workflow_with_orchestrator(
                execution_plan, user_id
            )
            
            # Update conversation memory and learning
            if user_id:
                await conversation_memory.update_conversation(
                    user_id, query, workflow_match["workflow_name"], execution_result
                )
            
            await self._update_workflow_performance(workflow_match, execution_result)
            
            fire_and_forget(
                "interpreter_workflow_dispatched",
                f"Successfully dispatched workflow: {workflow_match['workflow_name']}",
                ServiceNames.INTERPRETER,
                {
                    "workflow": workflow_match["workflow_name"],
                    "confidence": workflow_match["confidence"],
                    "user_id": user_id,
                    "execution_status": execution_result.get("status", "unknown")
                }
            )
            
            return {
                "status": "success",
                "workflow_dispatched": workflow_match["workflow_name"],
                "confidence": workflow_match["confidence"],
                "execution_plan": execution_plan,
                "execution_result": execution_result,
                "conversation_context": conversation_context
            }
            
        except Exception as e:
            error_msg = f"Failed to dispatch workflow for query: {str(e)}"
            fire_and_forget(
                "interpreter_dispatch_error",
                error_msg,
                ServiceNames.INTERPRETER,
                {"query": query, "intent": intent, "error": str(e)}
            )
            
            return {
                "status": "error",
                "error": str(e),
                "fallback_suggestion": await self._generate_fallback_suggestion(query, intent)
            }

    async def _find_best_workflow_match(self, query: str, intent: str, entities: Dict[str, Any],
                                      conversation_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find the best matching workflow for the query."""
        best_match = None
        best_score = 0.0
        
        query_lower = query.lower()
        
        for workflow_name, workflow_info in self.main_workflows.items():
            score = await self._calculate_workflow_score(
                query_lower, intent, entities, workflow_name, workflow_info, conversation_context
            )
            
            if score > best_score and score >= workflow_info["confidence_threshold"]:
                best_score = score
                best_match = {
                    "workflow_name": workflow_name,
                    "workflow_info": workflow_info,
                    "confidence": score,
                    "match_reasons": await self._get_match_reasons(query_lower, intent, workflow_name, workflow_info)
                }
        
        return best_match

    async def _calculate_workflow_score(self, query: str, intent: str, entities: Dict[str, Any],
                                      workflow_name: str, workflow_info: Dict[str, Any],
                                      conversation_context: Dict[str, Any]) -> float:
        """Calculate confidence score for workflow match."""
        score = 0.0
        
        # 1. Direct trigger phrase matching (40% weight)
        trigger_score = 0.0
        for trigger in workflow_info["triggers"]:
            if trigger.lower() in query:
                trigger_score = max(trigger_score, 0.9)
            elif any(word in query for word in trigger.lower().split()):
                trigger_score = max(trigger_score, 0.6)
        score += trigger_score * 0.4
        
        # 2. Intent-based matching (25% weight)
        intent_score = 0.0
        workflow_keywords = workflow_name.replace("_", " ").split()
        if intent in workflow_name or any(keyword in intent for keyword in workflow_keywords):
            intent_score = 0.9
        elif any(keyword in query for keyword in workflow_keywords):
            intent_score = 0.7
        score += intent_score * 0.25
        
        # 3. Service capability matching (20% weight)
        capability_score = 0.0
        mentioned_services = await self._extract_service_mentions(query)
        workflow_services = set(workflow_info["services"])
        if mentioned_services.intersection(workflow_services):
            capability_score = 0.8
        score += capability_score * 0.2
        
        # 4. Entity compatibility (10% weight)
        entity_score = await self._calculate_entity_compatibility(entities, workflow_info)
        score += entity_score * 0.1
        
        # 5. Conversation context boost (5% weight)
        context_score = await self._calculate_context_boost(workflow_name, conversation_context)
        score += context_score * 0.05
        
        return min(score, 1.0)

    async def _extract_service_mentions(self, query: str) -> set:
        """Extract mentioned services from query."""
        mentioned = set()
        service_aliases = await ecosystem_context.get_all_service_aliases()
        
        for service_name, aliases in service_aliases.items():
            all_names = [service_name.replace("_", " ")] + aliases
            for name in all_names:
                if name.lower() in query.lower():
                    mentioned.add(service_name)
                    break
        
        return mentioned

    async def _calculate_entity_compatibility(self, entities: Dict[str, Any], 
                                            workflow_info: Dict[str, Any]) -> float:
        """Calculate how well entities match workflow parameters."""
        if not entities:
            return 0.5  # Neutral score for no entities
        
        workflow_params = workflow_info.get("parameters", {})
        required_params = [k for k, v in workflow_params.items() if v.get("required", False)]
        
        if not required_params:
            return 0.7  # Good score if no required params
        
        # Check if we have entity data that could satisfy required params
        entity_types = set(entities.keys())
        param_types = set(required_params)
        
        # Basic compatibility mapping
        compatibility_map = {
            "url": ["repo_url", "source_url", "content_source"],
            "file_path": ["doc_id", "target_type"],
            "repo": ["repo_url"],
            "search_terms": ["research_topic", "prompt_id"]
        }
        
        satisfied_params = 0
        for entity_type, entity_values in entities.items():
            if entity_values:  # Has actual values
                if entity_type in param_types:
                    satisfied_params += 1
                else:
                    # Check compatibility mapping
                    for param in compatibility_map.get(entity_type, []):
                        if param in param_types:
                            satisfied_params += 1
                            break
        
        return min(satisfied_params / len(required_params), 1.0) if required_params else 0.7

    async def _calculate_context_boost(self, workflow_name: str, 
                                     conversation_context: Dict[str, Any]) -> float:
        """Calculate boost based on conversation context."""
        if not conversation_context:
            return 0.0
        
        # Recent workflow preferences
        recent_workflows = conversation_context.get("recent_workflows", [])
        if workflow_name in recent_workflows[-3:]:  # Last 3 workflows
            return 0.8
        
        # Domain context
        domain_context = conversation_context.get("domain_context", {})
        workflow_domain = self._get_workflow_domain(workflow_name)
        if domain_context.get("primary_domain") == workflow_domain:
            return 0.6
        
        return 0.0

    def _get_workflow_domain(self, workflow_name: str) -> str:
        """Get the domain category for a workflow."""
        domain_mapping = {
            "document_analysis": "content",
            "code_documentation": "development",
            "security_audit": "security",
            "content_processing": "content",
            "data_ingestion": "data",
            "prompt_optimization": "ai",
            "quality_assurance": "quality",
            "research_assistance": "research"
        }
        return domain_mapping.get(workflow_name, "general")

    async def _get_match_reasons(self, query: str, intent: str, workflow_name: str,
                               workflow_info: Dict[str, Any]) -> List[str]:
        """Get human-readable reasons for workflow match."""
        reasons = []
        
        # Check trigger matches
        for trigger in workflow_info["triggers"]:
            if trigger.lower() in query:
                reasons.append(f"Direct match for '{trigger}'")
                break
        
        # Check intent match
        if intent in workflow_name:
            reasons.append(f"Intent '{intent}' matches workflow")
        
        # Check service mentions
        mentioned_services = await self._extract_service_mentions(query)
        workflow_services = set(workflow_info["services"])
        common_services = mentioned_services.intersection(workflow_services)
        if common_services:
            reasons.append(f"Mentioned services: {', '.join(common_services)}")
        
        # Add capability match
        reasons.append(f"Workflow capabilities: {', '.join(workflow_info['capabilities'][:3])}")
        
        return reasons

    async def _prepare_workflow_execution(self, workflow_match: Dict[str, Any], 
                                        entities: Dict[str, Any], context: Dict[str, Any],
                                        user_id: str = None) -> Dict[str, Any]:
        """Prepare workflow execution plan with parameters."""
        workflow_info = workflow_match["workflow_info"]
        workflow_name = workflow_match["workflow_name"]
        
        # Build execution parameters
        execution_params = {}
        
        # Map entities to workflow parameters
        param_mapping = await self._map_entities_to_parameters(entities, workflow_info["parameters"])
        execution_params.update(param_mapping)
        
        # Add default parameters
        for param_name, param_config in workflow_info["parameters"].items():
            if param_name not in execution_params and "default" in param_config:
                execution_params[param_name] = param_config["default"]
        
        # Add context-based parameters
        if user_id:
            execution_params["user_id"] = user_id
        execution_params["execution_timestamp"] = datetime.utcnow().isoformat()
        execution_params["interpreter_confidence"] = workflow_match["confidence"]
        
        return {
            "workflow_name": workflow_name,
            "workflow_type": workflow_info.get("langgraph_workflow", workflow_name),
            "orchestrator_endpoint": workflow_info["orchestrator_endpoint"],
            "execution_method": "orchestrator_langgraph" if "langgraph_workflow" in workflow_info else "orchestrator_standard",
            "parameters": execution_params,
            "services_involved": workflow_info["services"],
            "estimated_duration": await self._estimate_workflow_duration(workflow_name),
            "execution_plan": {
                "preparation": "Parameters mapped and validated",
                "execution": "Route through orchestrator service",
                "monitoring": "Track execution progress",
                "completion": "Return results and update context"
            }
        }

    async def _map_entities_to_parameters(self, entities: Dict[str, Any], 
                                        workflow_params: Dict[str, Any]) -> Dict[str, Any]:
        """Map extracted entities to workflow parameters."""
        mapped_params = {}
        
        # Direct mapping for common entity types
        entity_to_param_map = {
            "url": ["repo_url", "source_url", "content_source"],
            "file_path": ["doc_id", "target_type"],
            "repo": ["repo_url"],
            "search_terms": ["research_topic", "prompt_id", "query"]
        }
        
        for entity_type, entity_values in entities.items():
            if not entity_values:
                continue
                
            # Take first value for single-value parameters
            entity_value = entity_values[0] if isinstance(entity_values, list) else entity_values
            
            # Direct parameter match
            if entity_type in workflow_params:
                mapped_params[entity_type] = entity_value
                continue
            
            # Use mapping
            for param_name in entity_to_param_map.get(entity_type, []):
                if param_name in workflow_params:
                    mapped_params[param_name] = entity_value
                    break
        
        return mapped_params

    async def _execute_workflow_with_orchestrator(self, execution_plan: Dict[str, Any],
                                                user_id: str = None) -> Dict[str, Any]:
        """Execute workflow through orchestrator integration."""
        try:
            workflow_name = execution_plan["workflow_name"]
            execution_method = execution_plan["execution_method"]
            parameters = execution_plan["parameters"]
            
            if execution_method == "orchestrator_langgraph":
                # Execute through LangGraph workflow
                result = await orchestrator_integration.execute_langgraph_workflow(
                    execution_plan["workflow_type"],
                    parameters,
                    user_id
                )
            else:
                # Execute through standard orchestrator workflow
                result = await orchestrator_integration.execute_workflow(
                    workflow_name,
                    parameters,
                    user_id
                )
            
            # Enhanced result processing
            enhanced_result = await self._enhance_execution_result(result, execution_plan)
            
            return enhanced_result
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "execution_plan": execution_plan,
                "fallback_available": True,
                "suggested_action": "Retry with simplified parameters or manual execution"
            }

    async def _enhance_execution_result(self, result: Dict[str, Any], 
                                      execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance execution result with additional context and suggestions."""
        enhanced_result = result.copy()
        
        # Add execution metadata
        enhanced_result["execution_metadata"] = {
            "workflow_name": execution_plan["workflow_name"],
            "services_used": execution_plan["services_involved"],
            "execution_time": datetime.utcnow().isoformat(),
            "interpreter_confidence": execution_plan["parameters"].get("interpreter_confidence", 0.0)
        }
        
        # Add follow-up suggestions based on workflow type
        if result.get("status") == "success":
            enhanced_result["follow_up_suggestions"] = await self._generate_follow_up_suggestions(
                execution_plan["workflow_name"], result
            )
        
        # Add related workflows
        enhanced_result["related_workflows"] = await self._get_related_workflows(
            execution_plan["workflow_name"]
        )
        
        return enhanced_result

    async def _generate_follow_up_suggestions(self, workflow_name: str, 
                                            result: Dict[str, Any]) -> List[str]:
        """Generate follow-up action suggestions based on workflow execution."""
        suggestions = []
        
        if workflow_name == "document_analysis":
            suggestions.extend([
                "Generate a detailed report from the analysis",
                "Compare with similar documents",
                "Schedule regular quality checks"
            ])
        elif workflow_name == "code_documentation":
            suggestions.extend([
                "Review generated documentation for accuracy",
                "Set up automated documentation updates",
                "Analyze code quality metrics"
            ])
        elif workflow_name == "security_audit":
            suggestions.extend([
                "Review security recommendations",
                "Schedule follow-up scans",
                "Implement suggested security improvements"
            ])
        elif workflow_name == "content_processing":
            suggestions.extend([
                "Share summary with relevant stakeholders",
                "Archive processed content",
                "Set up content monitoring"
            ])
        
        return suggestions

    async def _get_related_workflows(self, workflow_name: str) -> List[str]:
        """Get workflows related to the current one."""
        workflow_relationships = {
            "document_analysis": ["content_processing", "quality_assurance"],
            "code_documentation": ["security_audit", "quality_assurance"],
            "security_audit": ["quality_assurance", "code_documentation"],
            "content_processing": ["document_analysis", "research_assistance"],
            "data_ingestion": ["document_analysis", "content_processing"],
            "prompt_optimization": ["quality_assurance"],
            "quality_assurance": ["security_audit", "document_analysis"],
            "research_assistance": ["content_processing", "document_analysis"]
        }
        
        return workflow_relationships.get(workflow_name, [])

    async def _estimate_workflow_duration(self, workflow_name: str) -> str:
        """Estimate workflow execution duration."""
        duration_estimates = {
            "document_analysis": "2-5 minutes",
            "code_documentation": "5-15 minutes",
            "security_audit": "10-30 minutes",
            "content_processing": "1-3 minutes",
            "data_ingestion": "3-10 minutes",
            "prompt_optimization": "1-2 minutes",
            "quality_assurance": "15-45 minutes",
            "research_assistance": "3-8 minutes"
        }
        
        return duration_estimates.get(workflow_name, "5-10 minutes")

    async def _handle_no_workflow_match(self, query: str, intent: str, entities: Dict[str, Any],
                                      user_id: str = None) -> Dict[str, Any]:
        """Handle cases where no workflow matches the query."""
        # Try to provide helpful suggestions
        suggestions = await self._generate_workflow_suggestions(query, intent, entities)
        
        # Check if we can provide partial assistance
        partial_assistance = await self._check_partial_assistance(query, intent, entities)
        
        return {
            "status": "no_match",
            "message": "No specific workflow found for your query",
            "suggestions": suggestions,
            "partial_assistance": partial_assistance,
            "available_workflows": list(self.main_workflows.keys()),
            "help_message": "Try rephrasing your query or specify what you'd like to accomplish"
        }

    async def _generate_workflow_suggestions(self, query: str, intent: str, 
                                           entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate workflow suggestions for unmatched queries."""
        suggestions = []
        
        query_lower = query.lower()
        
        # Analyze query for potential workflow matches
        for workflow_name, workflow_info in self.main_workflows.items():
            score = await self._calculate_workflow_score(
                query_lower, intent, entities, workflow_name, workflow_info, {}
            )
            
            if score > 0.3:  # Lower threshold for suggestions
                suggestions.append({
                    "workflow_name": workflow_name,
                    "description": workflow_info["description"],
                    "confidence": score,
                    "example_query": f"Try: '{workflow_info['triggers'][0]}'"
                })
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        
        return suggestions[:3]  # Top 3 suggestions

    async def _check_partial_assistance(self, query: str, intent: str, 
                                      entities: Dict[str, Any]) -> Dict[str, Any]:
        """Check if we can provide partial assistance without full workflow."""
        assistance = {
            "available": False,
            "actions": []
        }
        
        # Check if we can help with service discovery
        mentioned_services = await self._extract_service_mentions(query)
        if mentioned_services:
            assistance["available"] = True
            assistance["actions"].append({
                "type": "service_info",
                "description": f"Get information about {', '.join(mentioned_services)} services",
                "services": list(mentioned_services)
            })
        
        # Check if we can help with capability exploration
        if "help" in query.lower() or "what can" in query.lower():
            assistance["available"] = True
            assistance["actions"].append({
                "type": "capability_exploration",
                "description": "Explore available ecosystem capabilities",
                "endpoint": "/ecosystem/capabilities"
            })
        
        return assistance

    async def _update_workflow_performance(self, workflow_match: Dict[str, Any], 
                                         execution_result: Dict[str, Any]):
        """Update workflow performance metrics for learning."""
        workflow_name = workflow_match["workflow_name"]
        
        if workflow_name not in self.workflow_performance:
            self.workflow_performance[workflow_name] = {
                "total_executions": 0,
                "successful_executions": 0,
                "average_confidence": 0.0,
                "last_executed": None
            }
        
        perf = self.workflow_performance[workflow_name]
        perf["total_executions"] += 1
        
        if execution_result.get("status") == "success":
            perf["successful_executions"] += 1
        
        # Update average confidence
        current_confidence = workflow_match["confidence"]
        perf["average_confidence"] = (
            (perf["average_confidence"] * (perf["total_executions"] - 1) + current_confidence) /
            perf["total_executions"]
        )
        
        perf["last_executed"] = datetime.utcnow().isoformat()

    async def _generate_fallback_suggestion(self, query: str, intent: str) -> Dict[str, Any]:
        """Generate fallback suggestion when dispatch fails."""
        return {
            "suggestion": "Try using more specific terms or mention the service you want to use",
            "examples": [
                "analyze document quality",
                "scan code for security issues", 
                "generate documentation from repository",
                "find prompts about analysis"
            ],
            "help_available": True,
            "contact_support": "For complex requests, contact system administrator"
        }

    async def _preprocess_query(self, query: str, conversation_context: Dict[str, Any]) -> str:
        """Preprocess query for better workflow matching."""
        # Basic normalization
        processed = query.lower().strip()
        
        # Expand abbreviations
        abbreviations = {
            "docs": "documents",
            "repo": "repository",
            "sec": "security",
            "qa": "quality assurance",
            "ai": "artificial intelligence"
        }
        
        for abbrev, expansion in abbreviations.items():
            processed = processed.replace(abbrev, expansion)
        
        # Add context from conversation
        if conversation_context.get("implied_context"):
            processed = f"{conversation_context['implied_context']} {processed}"
        
        return processed

    def get_workflow_info(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific workflow."""
        return self.main_workflows.get(workflow_name)

    def get_all_workflows(self) -> Dict[str, Any]:
        """Get information about all available workflows."""
        return {
            "workflows": self.main_workflows,
            "total_count": len(self.main_workflows),
            "categories": list(set(self._get_workflow_domain(name) for name in self.main_workflows.keys())),
            "performance_metrics": self.workflow_performance
        }

    async def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """Get status of a workflow execution."""
        try:
            return await orchestrator_integration.get_workflow_status(execution_id)
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to get workflow status: {str(e)}"
            }


# Create singleton instance
workflow_dispatcher = WorkflowDispatcher()
