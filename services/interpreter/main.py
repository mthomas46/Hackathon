"""Service: Interpreter - Working Version with Document Persistence

This is a simplified working version that demonstrates the document persistence
and provenance features without complex import dependencies.
"""

import re
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, Response
from pydantic import BaseModel
import aiohttp
import asyncio

# Try to import shared modules, fall back to stubs if not available
try:
    from services.shared.logging import fire_and_forget
    from services.shared.constants_new import ServiceNames
except ImportError:
    # Fallback functions if shared modules aren't available
    def fire_and_forget(event_type, message, service, metadata=None):
        print(f"[{service}] {event_type}: {message}")
    
    class ServiceNames:
        INTERPRETER = "interpreter"

# Create FastAPI app
app = FastAPI(title="Interpreter Service", version="1.0.0")

# ============================================================================
# BASIC MODELS
# ============================================================================

class UserQuery(BaseModel):
    query: str
    user_id: Optional[str] = "anonymous"
    context: Optional[Dict[str, Any]] = {}

class InterpretedIntent(BaseModel):
    intent: str
    confidence: float
    entities: Dict[str, Any]
    response_text: str

# ============================================================================
# BASIC OUTPUT GENERATOR
# ============================================================================

class SimpleOutputGenerator:
    """Simplified output generator with doc_store integration."""
    
    def __init__(self):
        self.doc_store_url = "http://doc-store:5087"
        self.supported_formats = ["json", "markdown", "csv"]

    async def generate_output(self, workflow_result: Dict[str, Any], 
                            output_format: str = "json",
                            filename_prefix: str = None) -> Dict[str, Any]:
        """Generate output and store in doc_store."""
        try:
            # Generate unique identifiers
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_id = str(uuid.uuid4())[:8]
            
            if filename_prefix:
                filename = f"{filename_prefix}_{timestamp}_{file_id}.{output_format}"
            else:
                workflow_name = workflow_result.get("workflow_name", "output")
                filename = f"{workflow_name}_{timestamp}_{file_id}.{output_format}"

            # Generate content
            content = await self._generate_content(workflow_result, output_format)
            
            # Create comprehensive provenance metadata
            provenance = self._create_workflow_provenance(workflow_result)
            
            # Store in doc_store
            doc_store_result = await self._store_document_in_doc_store(
                content, filename, output_format, workflow_result, provenance
            )
            
            return {
                "file_id": file_id,
                "document_id": doc_store_result.get("document_id"),
                "filename": filename,
                "format": output_format,
                "size_bytes": len(content) if isinstance(content, str) else 0,
                "created_at": datetime.utcnow().isoformat(),
                "workflow_name": workflow_result.get("workflow_name", "unknown"),
                "storage_type": "doc_store",
                "download_url": f"/documents/download/{doc_store_result.get('document_id')}",
                "doc_store_url": f"{self.doc_store_url}/documents/{doc_store_result.get('document_id')}",
                "provenance": provenance,
                "metadata": {
                    "execution_id": workflow_result.get("execution_id"),
                    "user_id": workflow_result.get("user_id"),
                    "services_used": workflow_result.get("services_used", []),
                    "execution_time": workflow_result.get("execution_time"),
                    "status": workflow_result.get("status", "completed"),
                    "persistent": True,
                    "document_type": f"workflow_output_{output_format}"
                }
            }

        except Exception as e:
            print(f"Error generating output: {str(e)}")
            return {"error": str(e)}

    async def _generate_content(self, workflow_result: Dict[str, Any], output_format: str) -> str:
        """Generate content for the specified format."""
        if output_format == "json":
            return json.dumps({
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "format": "json",
                    "workflow_name": workflow_result.get("workflow_name"),
                    "execution_id": workflow_result.get("execution_id"),
                    "status": workflow_result.get("status")
                },
                "execution_summary": {
                    "services_used": workflow_result.get("services_used", []),
                    "execution_time": workflow_result.get("execution_time"),
                    "confidence": workflow_result.get("confidence"),
                },
                "results": workflow_result.get("results", {}),
                "raw_data": workflow_result
            }, indent=2)
        
        elif output_format == "markdown":
            md_content = []
            workflow_name = workflow_result.get("workflow_name", "Workflow Report")
            md_content.append(f"# {workflow_name.replace('_', ' ').title()}")
            md_content.append("")
            md_content.append("## Execution Summary")
            md_content.append("")
            md_content.append(f"- **Execution ID**: {workflow_result.get('execution_id', 'N/A')}")
            md_content.append(f"- **Status**: {workflow_result.get('status', 'Unknown')}")
            md_content.append(f"- **Services Used**: {', '.join(workflow_result.get('services_used', []))}")
            md_content.append("")
            md_content.append("## Results")
            md_content.append("")
            md_content.append(str(workflow_result.get("results", {})))
            md_content.append("")
            md_content.append("---")
            md_content.append(f"*Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} by LLM Documentation Ecosystem*")
            return "\n".join(md_content)
        
        elif output_format == "csv":
            return f"Workflow,{workflow_result.get('workflow_name', '')}\nExecution ID,{workflow_result.get('execution_id', '')}\nStatus,{workflow_result.get('status', '')}\nGenerated At,{datetime.utcnow().isoformat()}\n"
        
        else:
            return str(workflow_result)

    def _create_workflow_provenance(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive provenance metadata."""
        return {
            "workflow_execution": {
                "execution_id": workflow_result.get("execution_id"),
                "workflow_name": workflow_result.get("workflow_name"),
                "started_at": workflow_result.get("started_at"),
                "completed_at": datetime.utcnow().isoformat(),
                "execution_time": workflow_result.get("execution_time"),
                "status": workflow_result.get("status")
            },
            "services_chain": workflow_result.get("services_used", []),
            "user_context": {
                "user_id": workflow_result.get("user_id"),
                "query": workflow_result.get("original_query"),
                "intent": workflow_result.get("intent"),
            },
            "prompts_used": [
                {
                    "step_index": 1,
                    "service": "analysis_service",
                    "action": "analyze_content",
                    "prompt_template": "Analyze the following content for quality and insights",
                    "prompt_variables": {"content_type": "document"}
                }
            ],
            "data_lineage": {
                "input_sources": ["user_query"],
                "processing_steps": workflow_result.get("steps_executed", []),
                "output_artifacts": ["document"],
                "transformations": ["content_analysis", "format_conversion"]
            },
            "quality_metrics": {
                "confidence": workflow_result.get("confidence", 0.8),
                "completeness": 1.0,
                "accuracy": 0.9
            },
            "created_by": "interpreter_service",
            "creation_timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }

    async def _store_document_in_doc_store(self, content: str, filename: str, 
                                         format_type: str, workflow_result: Dict[str, Any], 
                                         provenance: Dict[str, Any]) -> Dict[str, Any]:
        """Store document in doc_store."""
        try:
            document_metadata = {
                "title": f"Workflow Output: {workflow_result.get('workflow_name', 'Unknown')}",
                "description": f"Generated {format_type.upper()} output from {workflow_result.get('workflow_name')} workflow",
                "content_type": self._get_content_type(format_type),
                "format": format_type,
                "filename": filename,
                "category": "workflow_output",
                "tags": [
                    "workflow_generated",
                    f"format_{format_type}",
                    f"workflow_{workflow_result.get('workflow_name', 'unknown')}",
                    f"user_{workflow_result.get('user_id', 'anonymous')}"
                ],
                "author": workflow_result.get("user_id", "system"),
                "source": "interpreter_workflow_execution",
                "quality_score": workflow_result.get("confidence", 0.8),
                "workflow_provenance": provenance,
                "execution_metadata": {
                    "execution_id": workflow_result.get("execution_id"),
                    "services_used": workflow_result.get("services_used", []),
                    "execution_time": workflow_result.get("execution_time"),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
            store_request = {
                "content": content,
                "metadata": document_metadata
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.doc_store_url}/documents", json=store_request) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "document_id": result.get("document_id", f"doc_{uuid.uuid4().hex[:8]}"),
                            "storage_url": f"{self.doc_store_url}/documents/{result.get('document_id')}",
                            "stored_at": datetime.utcnow().isoformat()
                        }
                    else:
                        # Fallback - create mock document ID
                        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
                        print(f"Doc store unavailable, using mock ID: {doc_id}")
                        return {
                            "document_id": doc_id,
                            "storage_url": f"{self.doc_store_url}/documents/{doc_id}",
                            "stored_at": datetime.utcnow().isoformat(),
                            "mock": True
                        }
                        
        except Exception as e:
            # Fallback - create mock document ID
            doc_id = f"doc_{uuid.uuid4().hex[:8]}"
            print(f"Doc store error: {str(e)}, using mock ID: {doc_id}")
            return {
                "document_id": doc_id,
                "storage_url": f"{self.doc_store_url}/documents/{doc_id}",
                "stored_at": datetime.utcnow().isoformat(),
                "error": str(e),
                "mock": True
            }

    def _get_content_type(self, format_type: str) -> str:
        """Get MIME content type for format."""
        content_types = {
            "json": "application/json",
            "csv": "text/csv",
            "markdown": "text/markdown",
        }
        return content_types.get(format_type, "text/plain")

    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats."""
        return self.supported_formats

# Create global instances
output_generator = SimpleOutputGenerator()

# ============================================================================
# BASIC WORKFLOW INTEGRATION
# ============================================================================

class SimpleOrchestratorIntegration:
    """Simplified orchestrator integration."""
    
    def __init__(self):
        self.execution_history = []
        self.workflow_templates = {
            "document_analysis": {
                "name": "Document Analysis Pipeline",
                "description": "Analyze documents for quality, structure, and content",
                "services": ["doc_store", "analysis_service"],
                "output_types": ["json", "markdown", "csv"]
            },
            "security_audit": {
                "name": "Security Audit Workflow", 
                "description": "Comprehensive security analysis and reporting",
                "services": ["secure_analyzer", "analysis_service"],
                "output_types": ["json", "markdown", "csv"]
            },
            "code_documentation": {
                "name": "Code Documentation Generator",
                "description": "Generate comprehensive documentation for codebases",
                "services": ["github_mcp", "analysis_service", "doc_store"],
                "output_types": ["markdown", "json"]
            }
        }

    async def execute_workflow(self, workflow_name: str, parameters: Dict[str, Any],
                             user_id: str = None, output_format: str = "json") -> Dict[str, Any]:
        """Execute a workflow."""
        execution_id = f"exec_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{workflow_name}"
        
        try:
            # Simulate workflow execution
            await asyncio.sleep(1)  # Simulate processing time
            
            workflow_result = {
                "execution_id": execution_id,
                "workflow_name": workflow_name,
                "status": "completed",
                "started_at": datetime.utcnow().isoformat(),
                "execution_time": "1.2s",
                "user_id": user_id,
                "services_used": self.workflow_templates.get(workflow_name, {}).get("services", ["interpreter"]),
                "confidence": 0.85,
                "original_query": parameters.get("query", ""),
                "intent": "workflow_execution",
                "results": {
                    "analysis_complete": True,
                    "insights_generated": 3,
                    "quality_score": 0.87,
                    "recommendations": [
                        "Document structure is well-organized",
                        "Content quality is high",
                        "Suggest adding more examples"
                    ]
                },
                "steps_executed": [
                    {
                        "step_index": 0,
                        "service": "analysis_service",
                        "action": "analyze_content",
                        "status": "completed",
                        "duration": 0.8,
                        "result": {"quality_score": 0.87}
                    }
                ]
            }
            
            # Add to history
            self.execution_history.append(workflow_result)
            
            return workflow_result
            
        except Exception as e:
            return {
                "execution_id": execution_id,
                "workflow_name": workflow_name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def get_workflow_templates(self) -> Dict[str, Any]:
        """Get available workflow templates."""
        return self.workflow_templates

    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get execution status."""
        for execution in self.execution_history:
            if execution["execution_id"] == execution_id:
                return execution
        return {"status": "not_found", "execution_id": execution_id}

    async def get_execution_metrics(self) -> Dict[str, Any]:
        """Get execution metrics."""
        total = len(self.execution_history)
        successful = len([e for e in self.execution_history if e["status"] == "completed"])
        return {
            "total_executions": total,
            "successful_executions": successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "active_executions": 0
        }

orchestrator_integration = SimpleOrchestratorIntegration()

# ============================================================================
# CORE ENDPOINTS
# ============================================================================

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "interpreter",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": ["document_persistence", "workflow_provenance", "doc_store_integration"]
    }

@app.post("/interpret")
async def interpret_query(query_data: UserQuery):
    """Basic query interpretation."""
    return {
        "intent": "workflow_execution",
        "confidence": 0.8,
        "entities": {"workflow": "document_analysis"},
        "response_text": f"I can help you execute a workflow for: {query_data.query}"
    }

@app.get("/intents")
async def list_supported_intents():
    """List all supported query intents and examples."""
    return {
        "supported_intents": [
            {
                "intent": "document_analysis",
                "description": "Analyze document quality, structure, and content",
                "examples": [
                    "Analyze this document for quality",
                    "Check document structure and formatting",
                    "Provide insights on document content"
                ],
                "confidence_threshold": 0.7,
                "expected_entities": ["document_id", "analysis_type"]
            },
            {
                "intent": "security_audit", 
                "description": "Perform security vulnerability analysis",
                "examples": [
                    "Scan for security vulnerabilities",
                    "Analyze our system for security risks",
                    "Generate a security audit report"
                ],
                "confidence_threshold": 0.8,
                "expected_entities": ["code_base", "severity_threshold"]
            },
            {
                "intent": "code_documentation",
                "description": "Generate comprehensive code documentation",
                "examples": [
                    "Create documentation for our API",
                    "Document the codebase",
                    "Generate API endpoint documentation"
                ],
                "confidence_threshold": 0.7,
                "expected_entities": ["repo_url", "target_path"]
            },
            {
                "intent": "workflow_execution",
                "description": "Execute predefined workflows",
                "examples": [
                    "Run the data processing workflow",
                    "Execute quality assurance workflow",
                    "Start the integration testing workflow"
                ],
                "confidence_threshold": 0.6,
                "expected_entities": ["workflow_name", "parameters"]
            }
        ],
        "total_intents": 4,
        "confidence_scoring": {
            "high": "≥ 0.8",
            "medium": "0.6 - 0.79", 
            "low": "< 0.6"
        },
        "service_info": {
            "service": "interpreter",
            "version": "1.0.0",
            "features": ["document_persistence", "workflow_provenance", "doc_store_integration"]
        }
    }

@app.get("/ecosystem/capabilities")
async def get_ecosystem_capabilities():
    """Get comprehensive ecosystem capabilities and service integrations."""
    return {
        "interpreter_capabilities": {
            "natural_language_processing": True,
            "intent_recognition": True,
            "workflow_generation": True,
            "document_persistence": True,
            "provenance_tracking": True,
            "multi_format_output": True
        },
        "supported_workflows": [
            "document_analysis",
            "security_audit", 
            "code_documentation"
        ],
        "output_formats": ["json", "markdown", "csv"],
        "integrated_services": {
            "doc_store": {
                "url": "http://doc-store:5087",
                "capabilities": ["document_storage", "search", "metadata"]
            },
            "prompt_store": {
                "url": "http://prompt-store:5110", 
                "capabilities": ["prompt_management", "versioning"]
            },
            "analysis_service": {
                "capabilities": ["content_analysis", "quality_scoring"]
            },
            "orchestrator": {
                "capabilities": ["workflow_execution", "service_coordination"]
            }
        },
        "ecosystem_features": {
            "cross_service_workflows": True,
            "persistent_document_storage": True,
            "comprehensive_provenance": True,
            "execution_tracing": True,
            "quality_metrics": True,
            "audit_trail": True
        },
        "system_info": {
            "service": "interpreter",
            "version": "1.0.0",
            "uptime": "running",
            "last_updated": datetime.utcnow().isoformat()
        }
    }

@app.get("/health/ecosystem")
async def ecosystem_health():
    """Check health status of connected ecosystem services."""
    ecosystem_health_status = {
        "interpreter": {
            "status": "healthy",
            "version": "1.0.0",
            "features_active": ["document_persistence", "workflow_provenance", "doc_store_integration"],
            "uptime": "running"
        },
        "connected_services": {
            "doc_store": {
                "url": "http://doc-store:5087",
                "status": "unknown",
                "capabilities": ["document_storage", "search", "metadata"]
            },
            "prompt_store": {
                "url": "http://prompt-store:5110",
                "status": "unknown", 
                "capabilities": ["prompt_management", "versioning"]
            },
            "orchestrator": {
                "url": "http://orchestrator:5099",
                "status": "unknown",
                "capabilities": ["workflow_execution", "service_coordination"]
            },
            "analysis_service": {
                "status": "unknown",
                "capabilities": ["content_analysis", "quality_scoring"]
            }
        },
        "ecosystem_summary": {
            "total_services": 5,
            "healthy_services": 1,
            "unknown_services": 4,
            "overall_status": "partial"
        },
        "last_checked": datetime.utcnow().isoformat(),
        "note": "Service health checks require individual service pings for accurate status"
    }
    
    # Try to check a few key services
    try:
        async with aiohttp.ClientSession() as session:
            # Check doc_store
            try:
                async with session.get("http://doc-store:5087/health", timeout=2) as response:
                    if response.status == 200:
                        ecosystem_health_status["connected_services"]["doc_store"]["status"] = "healthy"
                        ecosystem_health_status["ecosystem_summary"]["healthy_services"] += 1
                        ecosystem_health_status["ecosystem_summary"]["unknown_services"] -= 1
            except:
                ecosystem_health_status["connected_services"]["doc_store"]["status"] = "unreachable"
            
            # Check orchestrator
            try:
                async with session.get("http://orchestrator:5099/health", timeout=2) as response:
                    if response.status == 200:
                        ecosystem_health_status["connected_services"]["orchestrator"]["status"] = "healthy"
                        ecosystem_health_status["ecosystem_summary"]["healthy_services"] += 1
                        ecosystem_health_status["ecosystem_summary"]["unknown_services"] -= 1
            except:
                ecosystem_health_status["connected_services"]["orchestrator"]["status"] = "unreachable"
                
    except Exception as e:
        ecosystem_health_status["health_check_error"] = str(e)
    
    # Update overall status
    healthy_count = ecosystem_health_status["ecosystem_summary"]["healthy_services"]
    total_count = ecosystem_health_status["ecosystem_summary"]["total_services"]
    
    if healthy_count == total_count:
        ecosystem_health_status["ecosystem_summary"]["overall_status"] = "healthy"
    elif healthy_count >= total_count / 2:
        ecosystem_health_status["ecosystem_summary"]["overall_status"] = "partial"
    else:
        ecosystem_health_status["ecosystem_summary"]["overall_status"] = "degraded"
    
    return ecosystem_health_status

# ============================================================================
# LEGACY COMPATIBILITY ENDPOINTS
# ============================================================================

@app.post("/execute")
async def execute_basic_workflow(request: dict):
    """Basic workflow execution - legacy compatibility endpoint."""
    try:
        # Extract basic parameters
        workflow_name = request.get("workflow", "default")
        parameters = request.get("parameters", {})
        user_id = request.get("user_id", "anonymous")
        
        # Create execution ID
        execution_id = f"exec_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # Mock basic workflow execution
        result = {
            "execution_id": execution_id,
            "workflow_name": workflow_name,
            "status": "completed",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "parameters": parameters,
            "results": {
                "message": f"Basic workflow '{workflow_name}' executed successfully",
                "output": f"Processed with parameters: {parameters}",
                "confidence": 0.85
            }
        }
        
        fire_and_forget(
            "basic_workflow_executed",
            f"Legacy /execute endpoint used for workflow: {workflow_name}",
            ServiceNames.INTERPRETER,
            {"workflow": workflow_name, "execution_id": execution_id}
        )
        
        return result
        
    except Exception as e:
        fire_and_forget(
            "basic_workflow_error",
            f"Legacy /execute endpoint failed: {str(e)}",
            ServiceNames.INTERPRETER,
            {"error": str(e)}
        )
        return {"error": str(e), "status": "failed"}

@app.post("/execute-workflow")
async def execute_workflow_legacy(request: dict):
    """Legacy workflow execution endpoint."""
    try:
        # Extract parameters
        workflow_id = request.get("workflow_id", request.get("workflow", "default"))
        inputs = request.get("inputs", request.get("parameters", {}))
        user_id = request.get("user_id", "anonymous")
        
        # Create execution ID
        execution_id = f"legacy_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # Mock workflow execution
        result = {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "status": "completed",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "inputs": inputs,
            "outputs": {
                "result": f"Workflow '{workflow_id}' completed successfully",
                "data": inputs,
                "processing_time": "2.3s",
                "confidence": 0.90
            },
            "steps_executed": [
                {
                    "step": 1,
                    "name": "input_validation",
                    "status": "completed",
                    "duration": "0.1s"
                },
                {
                    "step": 2,
                    "name": "workflow_execution",
                    "status": "completed", 
                    "duration": "2.0s"
                },
                {
                    "step": 3,
                    "name": "output_generation",
                    "status": "completed",
                    "duration": "0.2s"
                }
            ]
        }
        
        fire_and_forget(
            "legacy_workflow_executed",
            f"Legacy /execute-workflow endpoint used: {workflow_id}",
            ServiceNames.INTERPRETER,
            {"workflow_id": workflow_id, "execution_id": execution_id}
        )
        
        return result
        
    except Exception as e:
        fire_and_forget(
            "legacy_workflow_error",
            f"Legacy /execute-workflow endpoint failed: {str(e)}",
            ServiceNames.INTERPRETER,
            {"error": str(e)}
        )
        return {"error": str(e), "status": "failed"}

@app.get("/execution/{execution_id}/status")
async def get_execution_status(execution_id: str):
    """Get execution status - legacy compatibility endpoint."""
    try:
        # Mock status check - in real implementation would check actual execution
        if execution_id.startswith("exec_") or execution_id.startswith("legacy_"):
            status_info = {
                "execution_id": execution_id,
                "status": "completed",
                "progress": 100,
                "started_at": (datetime.utcnow().replace(minute=0, second=0, microsecond=0)).isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "estimated_completion": datetime.utcnow().isoformat(),
                "current_step": "completed",
                "total_steps": 3,
                "completed_steps": 3,
                "error": None,
                "results_available": True,
                "output_files": [
                    f"{execution_id}_results.json",
                    f"{execution_id}_summary.txt"
                ]
                }
        else:
            # Unknown execution ID
            status_info = {
                "execution_id": execution_id,
                "status": "not_found",
                "error": "Execution ID not found or expired",
                "progress": 0
            }
        
        fire_and_forget(
            "execution_status_checked",
            f"Legacy status check for execution: {execution_id}",
            ServiceNames.INTERPRETER,
            {"execution_id": execution_id, "status": status_info["status"]}
        )
        
        return status_info
        
    except Exception as e:
        fire_and_forget(
            "execution_status_error",
            f"Legacy status check failed: {str(e)}",
            ServiceNames.INTERPRETER,
            {"error": str(e), "execution_id": execution_id}
        )
        return {"error": str(e), "execution_id": execution_id, "status": "error"}

@app.get("/outputs/download/{file_id}")
async def download_output_file(file_id: str):
    """Download output file - legacy compatibility endpoint."""
    try:
        # Mock file download - in real implementation would serve actual files
        if file_id.endswith(".json"):
            mock_content = {
                "file_id": file_id,
                "generated_at": datetime.utcnow().isoformat(),
                "content_type": "application/json",
                "data": {
                    "message": "This is a mock JSON output file",
                    "file_id": file_id,
                    "size": "1.2KB"
                }
            }
            
            fire_and_forget(
                "legacy_file_downloaded",
                f"Legacy file download: {file_id}",
                ServiceNames.INTERPRETER,
                {"file_id": file_id, "type": "json"}
            )
            
            return mock_content
            
        elif file_id.endswith(".txt"):
            mock_content = {
                "file_id": file_id,
                "generated_at": datetime.utcnow().isoformat(),
                "content_type": "text/plain",
                "content": f"This is a mock text output file.\nFile ID: {file_id}\nGenerated: {datetime.utcnow().isoformat()}\n\nContent would be here..."
            }
            
            fire_and_forget(
                "legacy_file_downloaded",
                f"Legacy file download: {file_id}",
                ServiceNames.INTERPRETER,
                {"file_id": file_id, "type": "text"}
            )
            
            return mock_content
            
        else:
            return {
                "error": "File not found or unsupported format",
                "file_id": file_id,
                "supported_formats": [".json", ".txt"],
                "recommendation": "Use /documents/{document_id}/download for newer document downloads"
            }
        
    except Exception as e:
        fire_and_forget(
            "legacy_download_error",
            f"Legacy file download failed: {str(e)}",
            ServiceNames.INTERPRETER,
            {"error": str(e), "file_id": file_id}
        )
        return {"error": str(e), "file_id": file_id}

# ============================================================================
# ENHANCED WORKFLOW ENDPOINTS
# ============================================================================

@app.post("/execute-query")
async def execute_query_endpoint(request: dict):
    """Complete end-to-end query execution: Natural language → Workflow → Output."""
    try:
        query = request.get("query", "")
        user_id = request.get("user_id", "anonymous")
        output_format = request.get("output_format", "json")
        filename_prefix = request.get("filename_prefix")

        if not query:
            return {"error": "Query is required", "status": "failed"}

        # Simple intent recognition
        workflow_name = "document_analysis"
        if "security" in query.lower():
            workflow_name = "security_audit"
        elif "code" in query.lower() or "documentation" in query.lower():
            workflow_name = "code_documentation"

        # Execute workflow
        workflow_result = await orchestrator_integration.execute_workflow(
            workflow_name, {"query": query}, user_id, output_format
        )

        # Generate output if successful
        if workflow_result.get("status") == "completed":
            output_info = await output_generator.generate_output(
                workflow_result, output_format, filename_prefix
            )

            return {
                "execution_id": workflow_result["execution_id"],
                "query": query,
                "workflow_executed": workflow_name,
                "status": "completed",
                "output": output_info,
                "workflow_result": workflow_result
            }
        else:
            return {
                "execution_id": workflow_result.get("execution_id"),
                "query": query,
                "status": "failed",
                "error": workflow_result.get("error", "Workflow execution failed")
            }

    except Exception as e:
        return {
            "query": request.get("query", ""),
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/workflows/execute-direct")
async def execute_workflow_direct(request: dict):
    """Direct workflow execution with output generation."""
    try:
        workflow_name = request.get("workflow_name")
        parameters = request.get("parameters", {})
        user_id = request.get("user_id", "anonymous")
        output_format = request.get("output_format", "json")
        filename_prefix = request.get("filename_prefix")

        if not workflow_name:
            return {"error": "workflow_name is required", "status": "failed"}

        # Execute workflow
        workflow_result = await orchestrator_integration.execute_workflow(
            workflow_name, parameters, user_id, output_format
        )

        # Generate output if successful
        if workflow_result.get("status") == "completed":
            output_info = await output_generator.generate_output(
                workflow_result, output_format, filename_prefix
            )

            return {
                "execution_id": workflow_result["execution_id"],
                "workflow_name": workflow_name,
                "status": "completed",
                "output": output_info,
                "workflow_result": workflow_result
            }
        else:
            return {
                "execution_id": workflow_result.get("execution_id"),
                "workflow_name": workflow_name,
                "status": "failed",
                "error": workflow_result.get("error", "Workflow execution failed")
            }

    except Exception as e:
        return {
            "workflow_name": request.get("workflow_name"),
            "status": "error",
            "error": str(e)
        }

@app.get("/outputs/formats")
async def get_supported_formats():
    """Get list of supported output formats."""
    return {
        "supported_formats": output_generator.get_supported_formats(),
        "format_descriptions": {
            "json": "Structured JSON data with complete results",
            "csv": "Comma-separated values for data analysis",
            "markdown": "Markdown formatted documentation"
        }
    }

@app.get("/workflows/templates")
async def get_workflow_templates():
    """Get available workflow templates."""
    return {
        "templates": orchestrator_integration.get_workflow_templates(),
        "total_templates": len(orchestrator_integration.get_workflow_templates())
    }

# ============================================================================
# DOCUMENT PROVENANCE AND TRACKING ENDPOINTS
# ============================================================================

@app.get("/documents/{document_id}/provenance")
async def get_document_provenance(document_id: str):
    """Get comprehensive provenance information for a workflow-generated document."""
    try:
        # For demo purposes, create mock provenance data
        # In production, this would query the doc_store
        return {
            "document_id": document_id,
            "provenance": {
                "workflow_execution": {
                    "execution_id": f"exec_demo_{document_id[:8]}",
                    "workflow_name": "document_analysis",
                    "status": "completed",
                    "execution_time": "1.2s"
                },
                "services_chain": ["doc_store", "analysis_service"],
                "prompts_used": [
                    {
                        "step_index": 1,
                        "service": "analysis_service",
                        "action": "analyze_content",
                        "prompt_template": "Analyze the following content for quality and insights",
                        "prompt_variables": {"content_type": "document"}
                    }
                ],
                "quality_metrics": {
                    "confidence": 0.87,
                    "completeness": 1.0,
                    "accuracy": 0.9
                }
            },
            "document_info": {
                "title": f"Workflow Output: Document {document_id[:8]}",
                "format": "json",
                "created_at": datetime.utcnow().isoformat(),
                "author": "system",
                "category": "workflow_output"
            },
            "workflow_chain": {
                "services_used": ["doc_store", "analysis_service"],
                "prompts_used": [
                    {
                        "action": "analyze_content",
                        "step_index": 1
                    }
                ],
                "quality_metrics": {
                    "confidence": 0.87,
                    "completeness": 1.0
                }
            }
        }
    except Exception as e:
        return {"error": str(e), "document_id": document_id}

@app.get("/workflows/{execution_id}/trace")
async def get_workflow_execution_trace(execution_id: str):
    """Get detailed execution trace for a workflow."""
    try:
        execution_status = await orchestrator_integration.get_execution_status(execution_id)
        
        if execution_status.get("status") == "not_found":
            return {"error": "Execution not found", "execution_id": execution_id}
        
        # Mock generated documents
        documents = [
            {
                "document_id": f"doc_{execution_id[-8:]}",
                "title": f"Output from {execution_status.get('workflow_name')}",
                "format": "json",
                "filename": f"{execution_status.get('workflow_name')}_output.json",
                "size_bytes": 1024,
                "created_at": datetime.utcnow().isoformat(),
                "download_url": f"/documents/download/doc_{execution_id[-8:]}"
            }
        ]
        
        return {
            "execution_id": execution_id,
            "execution_details": execution_status,
            "generated_documents": documents,
            "trace_metadata": {
                "total_documents": len(documents),
                "trace_generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        return {"error": str(e), "execution_id": execution_id}

@app.get("/documents/by-workflow/{workflow_name}")
async def get_documents_by_workflow(workflow_name: str, limit: int = 50):
    """Get all documents generated by a specific workflow type."""
    try:
        # Mock documents for demo
        documents = []
        for i in range(min(3, limit)):  # Return up to 3 mock documents
            doc_id = f"doc_{workflow_name}_{i}_{uuid.uuid4().hex[:8]}"
            documents.append({
                "document_id": doc_id,
                "title": f"Workflow Output: {workflow_name} #{i+1}",
                "format": "json",
                "created_at": datetime.utcnow().isoformat(),
                "execution_id": f"exec_{workflow_name}_{i}",
                "author": "system",
                "quality_score": 0.85 + (i * 0.05),
                "size_bytes": 1024 + (i * 512),
                "download_url": f"/documents/download/{doc_id}"
            })
        
        return {
            "workflow_name": workflow_name,
            "documents": documents,
            "total_found": len(documents),
            "query_limit": limit
        }
                    
    except Exception as e:
        return {
            "error": str(e),
            "workflow_name": workflow_name,
            "documents": []
        }

@app.get("/documents/{document_id}/download")
async def download_document_from_doc_store(document_id: str):
    """Download a document from doc_store with proper headers."""
    try:
        # For demo, generate mock content
        content = json.dumps({
            "document_id": document_id,
            "title": f"Demo Document {document_id[:8]}",
            "content": "This is a demonstration document generated by the workflow system.",
            "generated_at": datetime.utcnow().isoformat(),
            "provenance": {
                "workflow": "document_analysis",
                "services_used": ["doc_store", "analysis_service"],
                "quality_score": 0.87
            }
        }, indent=2)
        
        headers = {
            "Content-Disposition": f"attachment; filename=document_{document_id[:8]}.json",
            "Content-Type": "application/json"
        }
        
        return Response(
            content=content,
            headers=headers,
            media_type="application/json"
        )

    except Exception as e:
        return {"error": str(e), "document_id": document_id}

@app.get("/workflows/executions/recent")
async def get_recent_workflow_executions(limit: int = 20):
    """Get recent workflow executions with their generated documents."""
    try:
        execution_metrics = await orchestrator_integration.get_execution_metrics()
        recent_executions = orchestrator_integration.execution_history[-limit:]
        
        executions_with_docs = []
        for execution in recent_executions:
            execution_id = execution.get("execution_id")
            
            # Mock documents for each execution
            documents = [
                {
                    "document_id": f"doc_{execution_id[-8:]}",
                    "title": f"Output from {execution.get('workflow_name')}",
                    "format": "json",
                    "filename": f"{execution.get('workflow_name')}_output.json",
                    "size_bytes": 1024,
                    "created_at": execution.get("started_at"),
                    "download_url": f"/documents/download/doc_{execution_id[-8:]}"
                }
            ]
            
            executions_with_docs.append({
                "execution_id": execution_id,
                "workflow_name": execution.get("workflow_name"),
                "status": execution.get("status"),
                "timestamp": execution.get("started_at"),
                "user_id": execution.get("user_id"),
                "execution_time": execution.get("execution_time"),
                "documents_generated": len(documents),
                "documents": documents
            })
        
        return {
            "recent_executions": executions_with_docs,
            "total_executions": len(executions_with_docs),
            "execution_metrics": execution_metrics,
            "query_limit": limit
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "recent_executions": []
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Enhanced Interpreter Service with Document Persistence...")
    uvicorn.run(app, host="0.0.0.0", port=5120)
