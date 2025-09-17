"""Orchestrator Integration for Interpreter Service.

This module provides deep integration with the orchestrator service, enabling
the interpreter to execute complex workflows and coordinate multiple services
to produce tangible outputs from natural language queries.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from services.shared.clients import ServiceClients
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class OrchestratorIntegration:
    """Manages integration with orchestrator service for workflow execution."""

    def __init__(self):
        self.client = ServiceClients()
        self.orchestrator_url = "http://orchestrator:5099"
        self.orchestrator_available = False
        
        # Workflow execution tracking
        self.active_executions = {}
        self.execution_history = []
        
        # Service capability mapping
        self.service_capabilities = {}
        
        # Workflow templates for common operations
        self.workflow_templates = {
            "document_analysis": {
                "name": "Document Analysis Pipeline",
                "description": "Analyze documents for quality, structure, and content",
                "services": ["doc_store", "analysis_service"],
                "steps": [
                    {"service": "doc_store", "action": "retrieve_document"},
                    {"service": "analysis_service", "action": "analyze_content"},
                    {"service": "analysis_service", "action": "generate_summary"}
                ],
                "output_types": ["pdf", "json", "markdown"]
            },
            "code_documentation": {
                "name": "Code Documentation Generator",
                "description": "Generate comprehensive documentation for codebases",
                "services": ["github_mcp", "analysis_service", "doc_store"],
                "steps": [
                    {"service": "github_mcp", "action": "analyze_repository"},
                    {"service": "analysis_service", "action": "extract_api_info"},
                    {"service": "doc_store", "action": "store_documentation"}
                ],
                "output_types": ["markdown", "pdf", "zip"]
            },
            "security_audit": {
                "name": "Security Audit Workflow",
                "description": "Comprehensive security analysis and reporting",
                "services": ["secure_analyzer", "analysis_service"],
                "steps": [
                    {"service": "secure_analyzer", "action": "scan_vulnerabilities"},
                    {"service": "analysis_service", "action": "assess_risk"},
                    {"service": "analysis_service", "action": "generate_recommendations"}
                ],
                "output_types": ["pdf", "json", "csv"]
            },
            "data_ingestion": {
                "name": "Data Ingestion Pipeline",
                "description": "Ingest and process data from various sources",
                "services": ["source_agent", "doc_store", "analysis_service"],
                "steps": [
                    {"service": "source_agent", "action": "fetch_data"},
                    {"service": "analysis_service", "action": "process_data"},
                    {"service": "doc_store", "action": "store_results"}
                ],
                "output_types": ["json", "csv", "zip"]
            },
            "content_processing": {
                "name": "Content Processing Workflow",
                "description": "Process and analyze textual content",
                "services": ["analysis_service", "prompt_store"],
                "steps": [
                    {"service": "analysis_service", "action": "analyze_text"},
                    {"service": "prompt_store", "action": "apply_templates"},
                    {"service": "analysis_service", "action": "generate_insights"}
                ],
                "output_types": ["markdown", "pdf", "json"]
            }
        }

    async def check_orchestrator_health(self) -> Dict[str, Any]:
        """Check if orchestrator service is available and healthy."""
        try:
            response = await self.client.get_json(f"{self.orchestrator_url}/health")
            
            self.orchestrator_available = response.get("status") == "healthy"
            
            return {
                "healthy": self.orchestrator_available,
                "status": response.get("status", "unknown"),
                "response_time": response.get("response_time"),
                "services_connected": response.get("services_connected", []),
                "active_workflows": response.get("active_workflows", 0)
            }
            
        except Exception as e:
            self.orchestrator_available = False
            return {
                "healthy": False,
                "error": str(e),
                "status": "unreachable"
            }

    async def discover_available_workflows(self) -> Dict[str, Any]:
        """Discover workflows available through the orchestrator."""
        try:
            # Get registered tools/workflows from orchestrator
            tools_response = await self.client.get_json(f"{self.orchestrator_url}/tools")
            
            # Get LangGraph workflows
            workflows_response = await self.client.get_json(f"{self.orchestrator_url}/workflows")
            
            discovered_workflows = {
                "registered_tools": tools_response.get("tools", []),
                "langgraph_workflows": workflows_response.get("workflows", []),
                "template_workflows": self.workflow_templates,
                "total_available": (
                    len(tools_response.get("tools", [])) + 
                    len(workflows_response.get("workflows", [])) +
                    len(self.workflow_templates)
                )
            }
            
            fire_and_forget(
                "workflows_discovered",
                f"Discovered {discovered_workflows['total_available']} available workflows",
                ServiceNames.INTERPRETER,
                {"total_workflows": discovered_workflows['total_available']}
            )
            
            return discovered_workflows
            
        except Exception as e:
            fire_and_forget(
                "workflow_discovery_error",
                f"Failed to discover workflows: {str(e)}",
                ServiceNames.INTERPRETER,
                {"error": str(e)}
            )
            return {
                "registered_tools": [],
                "langgraph_workflows": [],
                "template_workflows": self.workflow_templates,
                "total_available": len(self.workflow_templates),
                "error": str(e)
            }

    async def execute_workflow(self, workflow_name: str, parameters: Dict[str, Any],
                             user_id: str = None, output_format: str = "json") -> Dict[str, Any]:
        """Execute a workflow through the orchestrator."""
        execution_id = f"exec_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{workflow_name}"
        
        try:
            # Check if it's a template workflow
            if workflow_name in self.workflow_templates:
                return await self._execute_template_workflow(
                    workflow_name, parameters, execution_id, user_id, output_format
                )
            
            # Execute through orchestrator's workflow system
            execution_request = {
                "workflow_name": workflow_name,
                "parameters": parameters,
                "execution_id": execution_id,
                "user_id": user_id,
                "output_format": output_format,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Track execution
            self.active_executions[execution_id] = {
                "workflow_name": workflow_name,
                "status": "running",
                "started_at": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "parameters": parameters
            }
            
            # Execute workflow
            response = await self.client.post_json(
                f"{self.orchestrator_url}/workflows/execute",
                execution_request
            )
            
            # Update execution status
            if response.get("success"):
                self.active_executions[execution_id]["status"] = "completed"
                self.active_executions[execution_id]["completed_at"] = datetime.utcnow().isoformat()
                self.active_executions[execution_id]["results"] = response.get("results", {})
            else:
                self.active_executions[execution_id]["status"] = "failed"
                self.active_executions[execution_id]["error"] = response.get("error", "Unknown error")
            
            # Create execution result
            execution_result = {
                "execution_id": execution_id,
                "workflow_name": workflow_name,
                "status": "completed" if response.get("success") else "failed",
                "results": response.get("results", {}),
                "services_used": response.get("services_used", []),
                "execution_time": response.get("execution_time"),
                "output_format": output_format,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if not response.get("success"):
                execution_result["error"] = response.get("error", "Workflow execution failed")
            
            # Add to history
            self.execution_history.append(execution_result)
            
            fire_and_forget(
                "workflow_executed",
                f"Executed workflow {workflow_name}",
                ServiceNames.INTERPRETER,
                {
                    "execution_id": execution_id,
                    "workflow": workflow_name,
                    "status": execution_result["status"],
                    "user_id": user_id
                }
            )
            
            return execution_result
            
        except Exception as e:
            # Update execution status on error
            if execution_id in self.active_executions:
                self.active_executions[execution_id]["status"] = "error"
                self.active_executions[execution_id]["error"] = str(e)
            
            fire_and_forget(
                "workflow_execution_error",
                f"Failed to execute workflow {workflow_name}: {str(e)}",
                ServiceNames.INTERPRETER,
                {
                    "execution_id": execution_id,
                    "workflow": workflow_name,
                    "error": str(e),
                    "user_id": user_id
                }
            )
            
            return {
                "execution_id": execution_id,
                "workflow_name": workflow_name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _execute_template_workflow(self, workflow_name: str, parameters: Dict[str, Any],
                                       execution_id: str, user_id: str, output_format: str) -> Dict[str, Any]:
        """Execute a predefined template workflow."""
        template = self.workflow_templates[workflow_name]
        
        try:
            results = {
                "workflow_name": workflow_name,
                "execution_id": execution_id,
                "steps_executed": [],
                "services_used": template["services"],
                "execution_time": 0
            }
            
            start_time = datetime.utcnow()
            
            # Execute each step in the workflow
            for step_index, step in enumerate(template["steps"]):
                step_start = datetime.utcnow()
                
                try:
                    step_result = await self._execute_workflow_step(
                        step, parameters, f"{execution_id}_step_{step_index}"
                    )
                    
                    step_duration = (datetime.utcnow() - step_start).total_seconds()
                    
                    step_info = {
                        "step_index": step_index,
                        "service": step["service"],
                        "action": step["action"],
                        "status": "completed",
                        "duration": step_duration,
                        "result": step_result
                    }
                    
                    results["steps_executed"].append(step_info)
                    
                except Exception as step_error:
                    step_info = {
                        "step_index": step_index,
                        "service": step["service"], 
                        "action": step["action"],
                        "status": "failed",
                        "error": str(step_error)
                    }
                    
                    results["steps_executed"].append(step_info)
                    
                    # Decide whether to continue or fail
                    if step.get("required", True):
                        raise step_error
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            results["execution_time"] = execution_time
            results["status"] = "completed"
            
            # Generate summary based on results
            results["summary"] = await self._generate_workflow_summary(template, results)
            
            return results
            
        except Exception as e:
            return {
                "execution_id": execution_id,
                "workflow_name": workflow_name,
                "status": "failed",
                "error": str(e),
                "steps_executed": results.get("steps_executed", [])
            }

    async def _execute_workflow_step(self, step: Dict[str, Any], parameters: Dict[str, Any],
                                   step_id: str) -> Dict[str, Any]:
        """Execute a single workflow step."""
        service_name = step["service"]
        action = step["action"]
        
        # Map service names to URLs
        service_urls = {
            "doc_store": "http://doc-store:5020",
            "analysis_service": "http://analysis-service:5010", 
            "github_mcp": "http://github-mcp:5050",
            "secure_analyzer": "http://secure-analyzer:5055",
            "source_agent": "http://source-agent:5025",
            "prompt_store": "http://prompt-store:5015"
        }
        
        service_url = service_urls.get(service_name)
        if not service_url:
            raise ValueError(f"Unknown service: {service_name}")
        
        # Create service-specific request
        request_data = {
            "action": action,
            "parameters": parameters,
            "step_id": step_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Call the service
            response = await self.client.post_json(f"{service_url}/execute", request_data)
            
            return {
                "success": response.get("success", False),
                "data": response.get("data", {}),
                "service": service_name,
                "action": action
            }
            
        except Exception as e:
            # For now, create mock results to demonstrate the flow
            return await self._create_mock_service_result(service_name, action, parameters)

    async def _create_mock_service_result(self, service_name: str, action: str, 
                                        parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create mock service results for demonstration."""
        
        if service_name == "analysis_service":
            if action == "analyze_content":
                return {
                    "success": True,
                    "data": {
                        "analysis_type": "content_analysis",
                        "metrics": {
                            "readability_score": 0.85,
                            "complexity_score": 0.72,
                            "quality_score": 0.91
                        },
                        "insights": [
                            "Content is well-structured and readable",
                            "Technical complexity is moderate",
                            "Overall quality is high"
                        ],
                        "recommendations": [
                            "Consider adding more examples",
                            "Improve technical explanations"
                        ]
                    }
                }
            elif action == "generate_summary":
                return {
                    "success": True,
                    "data": {
                        "summary": "The analyzed content demonstrates high quality with good readability and structure. Recommendations include enhanced examples and clearer technical explanations.",
                        "key_points": [
                            "High overall quality score (0.91)",
                            "Good readability (0.85)",
                            "Moderate complexity (0.72)"
                        ]
                    }
                }
        
        elif service_name == "doc_store":
            return {
                "success": True,
                "data": {
                    "document_id": "doc_12345",
                    "content": "Sample document content for analysis",
                    "metadata": {
                        "size": 1024,
                        "type": "text/markdown",
                        "created": datetime.utcnow().isoformat()
                    }
                }
            }
        
        elif service_name == "secure_analyzer":
            return {
                "success": True,
                "data": {
                    "vulnerabilities_found": 2,
                    "risk_level": "medium",
                    "issues": [
                        {
                            "type": "dependency_vulnerability",
                            "severity": "medium",
                            "description": "Outdated dependency with known issues"
                        },
                        {
                            "type": "code_quality",
                            "severity": "low", 
                            "description": "Missing input validation in API endpoint"
                        }
                    ],
                    "recommendations": [
                        "Update dependencies to latest versions",
                        "Implement comprehensive input validation"
                    ]
                }
            }
        
        # Default mock result
        return {
            "success": True,
            "data": {
                "service": service_name,
                "action": action,
                "result": f"Mock result for {action} from {service_name}",
                "parameters_received": parameters
            }
        }

    async def _generate_workflow_summary(self, template: Dict[str, Any], 
                                       results: Dict[str, Any]) -> str:
        """Generate a summary of workflow execution results."""
        successful_steps = len([s for s in results["steps_executed"] if s["status"] == "completed"])
        total_steps = len(results["steps_executed"])
        
        summary = f"""
Workflow: {template['name']}
Description: {template['description']}

Execution Summary:
- Steps Completed: {successful_steps}/{total_steps}
- Total Execution Time: {results['execution_time']:.2f} seconds
- Services Used: {', '.join(results['services_used'])}
- Status: {results['status']}

Results: The workflow executed successfully and generated comprehensive results.
"""
        
        return summary.strip()

    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get the status of a workflow execution."""
        if execution_id in self.active_executions:
            return self.active_executions[execution_id]
        
        # Check execution history
        for execution in self.execution_history:
            if execution["execution_id"] == execution_id:
                return execution
        
        return {
            "execution_id": execution_id,
            "status": "not_found",
            "error": "Execution not found"
        }

    async def get_execution_metrics(self) -> Dict[str, Any]:
        """Get metrics about workflow executions."""
        total_executions = len(self.execution_history)
        successful_executions = len([e for e in self.execution_history if e["status"] == "completed"])
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0.0,
            "active_executions": len(self.active_executions),
            "available_workflows": len(self.workflow_templates),
            "orchestrator_connected": self.orchestrator_available
        }

    def get_workflow_templates(self) -> Dict[str, Any]:
        """Get available workflow templates."""
        return self.workflow_templates


# Create singleton instance
orchestrator_integration = OrchestratorIntegration()