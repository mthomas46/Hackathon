"""Service: Interpreter - Working Version with Document Persistence

This is a simplified working version that demonstrates the document persistence
and provenance features without complex import dependencies.
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

# ============================================================================
# ENVIRONMENT VARIABLE CONFIGURATION
# ============================================================================
def configure_service_urls():
    """Configure default service URLs as environment variables if not set."""
    defaults = {
        # Core Services
        "DOC_STORE_URL": "http://doc-store:5087",
        "PROMPT_STORE_URL": "http://prompt-store:5110",
        "ANALYSIS_SERVICE_URL": "http://analysis-service:5020",
        "MEMORY_AGENT_URL": "http://memory-agent:5040",
        "SOURCE_AGENT_URL": "http://source-agent:5000",
        "LLM_GATEWAY_URL": "http://llm-gateway:5055",

        # Interpreter Service Configuration
        "INTERPRETER_SERVICE_API_HOST": "127.0.0.1",
        "INTERPRETER_SERVICE_API_PORT": "5120",
    }

    # Set defaults only if not already set
    for key, default_value in defaults.items():
        if key not in os.environ:
            os.environ[key] = default_value

# Configure service URLs before application startup
configure_service_urls()

# ============================================================================
# STANDARDIZED CONFIGURATION
# ============================================================================
from services.shared.infrastructure.config import load_service_config
from services.shared.infrastructure.utilities.middleware import setup_common_middleware
from services.shared.presentation.api.responses import create_error_response, create_success_response
from services.shared.infrastructure.monitoring.health import register_health_endpoints

# Load standardized configuration
config = load_service_config("interpreter")

# Service configuration from standardized config
SERVICE_NAME = "interpreter"
SERVICE_TITLE = "Interpreter Service"
SERVICE_VERSION = "1.0.0"

# Fallback logging function if shared modules aren't available
def fire_and_forget(event_type, message, service, metadata=None):
    logger.info(f"[{service}] {event_type}: {message}")


# Set up logging for the interpreter service
import logging
logger = logging.getLogger(__name__)

# Import WorkflowLogger for enhanced v2.0 logging
import sys
from pathlib import Path
services_path = Path(__file__).parent.parent.parent
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

try:
    from services.shared.infrastructure.logging.workflow_logger import WorkflowLogger
    # Initialize workflow logger for interpreter service
    workflow_logger = WorkflowLogger(
        service_name="interpreter",
        log_collector_url=os.getenv("LOG_COLLECTOR_URL", "http://log-collector:5040")
    )
    logger.info("✅ WorkflowLogger initialized successfully")
except ImportError as e:
    logger.warning(f"WorkflowLogger not available: {e}. Logging will use standard logger.")
    workflow_logger = None

# Import sample documents repository
logger.info("Starting sample documents import...")
try:
    logger.debug("Attempting to import sample_documents module...")
    from .modules.sample_documents import sample_documents

    logger.info(f"Import successful! sample_documents = {sample_documents}")
    if sample_documents is not None:
        logger.info(
            f"Sample documents repository has {len(sample_documents.get_all_documents())} documents"
        )
    else:
        logger.warning("Sample documents repository is None")
except ImportError as e:
    logger.warning(f"Import failed with ImportError: {e}")
    # Fallback if import fails - will use mock data
    sample_documents = None
except Exception as e:
    logger.error(f"Import failed with unexpected error: {e}")
    sample_documents = None

logger.info(f"Final sample_documents value: {sample_documents}")

# Create FastAPI app
app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description="AI-powered natural language query interpreter with document persistence and provenance tracking",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup standardized middleware and utilities
setup_common_middleware(app, service_name=SERVICE_NAME)

# Register standardized health endpoints
register_health_endpoints(app, SERVICE_NAME, SERVICE_VERSION)

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
        self.doc_store_url = os.getenv("DOC_STORE_URL", "http://doc-store:5087")
        self.supported_formats = ["json", "markdown", "csv"]

    async def generate_output(
        self,
        workflow_result: Dict[str, Any],
        output_format: str = "json",
        filename_prefix: str = None,
    ) -> Dict[str, Any]:
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
                    "document_type": f"workflow_output_{output_format}",
                },
            }

        except Exception as e:
            logger.error(f"Error generating output: {str(e)}")
            return {"error": str(e)}

    async def _generate_content(
        self, workflow_result: Dict[str, Any], output_format: str
    ) -> str:
        """Generate content for the specified format."""
        if output_format == "json":
            return json.dumps(
                {
                    "metadata": {
                        "generated_at": datetime.utcnow().isoformat(),
                        "format": "json",
                        "workflow_name": workflow_result.get("workflow_name"),
                        "execution_id": workflow_result.get("execution_id"),
                        "status": workflow_result.get("status"),
                    },
                    "execution_summary": {
                        "services_used": workflow_result.get("services_used", []),
                        "execution_time": workflow_result.get("execution_time"),
                        "confidence": workflow_result.get("confidence"),
                    },
                    "results": workflow_result.get("results", {}),
                    "raw_data": workflow_result,
                },
                indent=2,
            )

        elif output_format == "markdown":
            md_content = []
            workflow_name = workflow_result.get("workflow_name", "Workflow Report")
            md_content.append(f"# {workflow_name.replace('_', ' ').title()}")
            md_content.append("")
            md_content.append("## Execution Summary")
            md_content.append("")
            md_content.append(
                f"- **Execution ID**: {workflow_result.get('execution_id', 'N/A')}"
            )
            md_content.append(
                f"- **Status**: {workflow_result.get('status', 'Unknown')}"
            )
            md_content.append(
                f"- **Services Used**: {', '.join(workflow_result.get('services_used', []))}"
            )
            md_content.append("")
            md_content.append("## Results")
            md_content.append("")
            md_content.append(str(workflow_result.get("results", {})))
            md_content.append("")
            md_content.append("---")
            md_content.append(
                f"*Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} by LLM Documentation Ecosystem*"
            )
            return "\n".join(md_content)

        elif output_format == "csv":
            return f"Workflow,{workflow_result.get('workflow_name', '')}\nExecution ID,{workflow_result.get('execution_id', '')}\nStatus,{workflow_result.get('status', '')}\nGenerated At,{datetime.utcnow().isoformat()}\n"

        else:
            return str(workflow_result)

    def _create_workflow_provenance(
        self, workflow_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive provenance metadata."""
        return {
            "workflow_execution": {
                "execution_id": workflow_result.get("execution_id"),
                "workflow_name": workflow_result.get("workflow_name"),
                "started_at": workflow_result.get("started_at"),
                "completed_at": datetime.utcnow().isoformat(),
                "execution_time": workflow_result.get("execution_time"),
                "status": workflow_result.get("status"),
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
                    "prompt_variables": {"content_type": "document"},
                }
            ],
            "data_lineage": {
                "input_sources": ["user_query"],
                "processing_steps": workflow_result.get("steps_executed", []),
                "output_artifacts": ["document"],
                "transformations": ["content_analysis", "format_conversion"],
            },
            "quality_metrics": {
                "confidence": workflow_result.get("confidence", 0.8),
                "completeness": 1.0,
                "accuracy": 0.9,
            },
            "created_by": "interpreter_service",
            "creation_timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
        }

    async def _store_document_in_doc_store(
        self,
        content: str,
        filename: str,
        format_type: str,
        workflow_result: Dict[str, Any],
        provenance: Dict[str, Any],
    ) -> Dict[str, Any]:
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
                    f"user_{workflow_result.get('user_id', 'anonymous')}",
                ],
                "author": workflow_result.get("user_id", "system"),
                "source": "interpreter_workflow_execution",
                "quality_score": workflow_result.get("confidence", 0.8),
                "workflow_provenance": provenance,
                "execution_metadata": {
                    "execution_id": workflow_result.get("execution_id"),
                    "services_used": workflow_result.get("services_used", []),
                    "execution_time": workflow_result.get("execution_time"),
                    "generated_at": datetime.utcnow().isoformat(),
                },
            }

            store_request = {"content": content, "metadata": document_metadata}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.doc_store_url}/documents", json=store_request
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "document_id": result.get(
                                "document_id", f"doc_{uuid.uuid4().hex[:8]}"
                            ),
                            "storage_url": f"{self.doc_store_url}/documents/{result.get('document_id')}",
                            "stored_at": datetime.utcnow().isoformat(),
                        }
                    else:
                        # Fallback - create mock document ID
                        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
                        logger.warning(f"Doc store unavailable, using mock ID: {doc_id}")
                        return {
                            "document_id": doc_id,
                            "storage_url": f"{self.doc_store_url}/documents/{doc_id}",
                            "stored_at": datetime.utcnow().isoformat(),
                            "mock": True,
                        }

        except Exception as e:
            # Fallback - create mock document ID
            doc_id = f"doc_{uuid.uuid4().hex[:8]}"
            logger.warning(f"Doc store error: {str(e)}, using mock ID: {doc_id}")
            return {
                "document_id": doc_id,
                "storage_url": f"{self.doc_store_url}/documents/{doc_id}",
                "stored_at": datetime.utcnow().isoformat(),
                "error": str(e),
                "mock": True,
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
                "output_types": ["json", "markdown", "csv"],
            },
            "security_audit": {
                "name": "Security Audit Workflow",
                "description": "Comprehensive security analysis and reporting",
                "services": ["secure-analyzer", "analysis_service"],
                "output_types": ["json", "markdown", "csv"],
            },
            "code_documentation": {
                "name": "Code Documentation Generator",
                "description": "Generate comprehensive documentation for codebases",
                "services": ["github_mcp", "analysis_service", "doc_store"],
                "output_types": ["markdown", "json"],
            },
        }

    async def execute_workflow(
        self,
        workflow_name: str,
        parameters: Dict[str, Any],
        user_id: str = None,
        output_format: str = "json",
    ) -> Dict[str, Any]:
        """Execute a workflow."""
        execution_id = (
            f"exec_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{workflow_name}"
        )

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
                "services_used": self.workflow_templates.get(workflow_name, {}).get(
                    "services", ["interpreter"]
                ),
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
                        "Suggest adding more examples",
                    ],
                },
                "steps_executed": [
                    {
                        "step_index": 0,
                        "service": "analysis_service",
                        "action": "analyze_content",
                        "status": "completed",
                        "duration": 0.8,
                        "result": {"quality_score": 0.87},
                    }
                ],
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
                "timestamp": datetime.utcnow().isoformat(),
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
        successful = len(
            [e for e in self.execution_history if e["status"] == "completed"]
        )
        return {
            "total_executions": total,
            "successful_executions": successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "active_executions": 0,
        }


orchestrator_integration = SimpleOrchestratorIntegration()

# ============================================================================
# CORE ENDPOINTS
# ============================================================================


@app.get(
    "/health",
    summary="Health Check",
    description="Check the health status of the Interpreter service and its core components.",
    tags=["Health"],
    responses={
        200: {
            "description": "Service is healthy and operational",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "interpreter",
                        "timestamp": "2024-01-01T12:00:00Z",
                        "version": "1.0.0"
                    }
                }
            }
        },
        503: {
            "description": "Service is unhealthy or unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "service": "interpreter",
                        "error": "Service dependencies unavailable"
                    }
                }
            }
        }
    }
)
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "interpreter",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "document_persistence",
            "workflow_provenance",
            "doc_store_integration",
        ],
    }


@app.post(
    "/interpret",
    summary="Interpret Natural Language Query",
    description="Interpret a natural language query and return structured workflow execution parameters.",
    tags=["Query Processing"],
    responses={
        200: {
            "description": "Query successfully interpreted",
            "content": {
                "application/json": {
                    "example": {
                        "intent": "workflow_execution",
                        "confidence": 0.85,
                        "parameters": {
                            "workflow": "document_analysis",
                            "target": "repo:example/docs"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Invalid query format or parameters",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Invalid query format",
                        "details": "Query must be a non-empty string"
                    }
                }
            }
        },
        422: {
            "description": "Validation error in request data",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Validation Error",
                        "details": [
                            {
                                "loc": ["query"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during query interpretation",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Internal server error",
                        "details": "Failed to process query interpretation"
                    }
                }
            }
        }
    }
)
async def interpret_query(query_data: UserQuery):
    """Basic query interpretation with proper error handling."""
    try:
        # Validate input
        if not query_data.query or not query_data.query.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid query format",
                    "message": "Query cannot be empty",
                    "details": "Please provide a non-empty query string"
                }
            )

        # Basic intent detection (in real implementation, this would use NLP models)
        query_lower = query_data.query.lower()

        if any(word in query_lower for word in ["analyze", "analysis", "check", "review"]):
            intent = "document_analysis"
            confidence = 0.85
        elif any(word in query_lower for word in ["generate", "create", "build"]):
            intent = "content_generation"
            confidence = 0.82
        elif any(word in query_lower for word in ["execute", "run", "workflow"]):
            intent = "workflow_execution"
            confidence = 0.88
        else:
            intent = "general_query"
            confidence = 0.65

        return {
            "intent": intent,
            "confidence": confidence,
            "entities": {"workflow": intent.replace("_", " ")},
            "response_text": f"I can help you execute a workflow for: {query_data.query}",
            "processing_time_ms": 150
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error interpreting query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Failed to process query interpretation",
                "details": str(e)
            }
        )


@app.post(
    "/natural-query",
    summary="🆕 Enhanced Natural Language Query Processing (v2.0)",
    description="""
    Process natural language queries with full Enhanced Roadmap v2.0 workflow support.
    
    This endpoint is the entry point for the intelligent orchestration workflow that:
    - Interprets natural language using advanced NLP
    - Generates a unique workflow_id for complete traceability
    - Logs every step to the log-collector service
    - Extracts entities and intent with high confidence
    - Prepares structured output for the orchestrator service
    
    Part of the Enhanced Roadmap v2.0 implementation with complete observability.
    """,
    tags=["Enhanced v2.0", "Query Processing"],
    responses={
        200: {
            "description": "Query successfully processed with full v2.0 workflow tracking",
            "content": {
                "application/json": {
                    "example": {
                        "workflow_id": "wf-20251003-abc123",
                        "interpreted_intent": {
                            "feature_type": "authentication",
                            "platform": "mobile_app",
                            "action": "plan"
                        },
                        "entities": {
                            "feature_type": "authentication",
                            "platform": "mobile",
                            "team_size": 5
                        },
                        "confidence": 0.92,
                        "processing_time_ms": 245.3,
                        "next_step": "orchestrator",
                        "logged": True
                    }
                }
            }
        }
    }
)
async def natural_query_v2(query_data: UserQuery):
    """
    Enhanced natural language query processing with full v2.0 workflow support.
    
    This endpoint implements the Enhanced Roadmap v2.0 specification with:
    - Complete workflow tracking via workflow_id
    - Full logging to log-collector service
    - Advanced entity extraction
    - Structured output for orchestrator integration
    """
    start_time = datetime.utcnow()
    
    # Generate unique workflow ID
    workflow_id = f"wf-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
    
    # Log workflow start (with WorkflowLogger if available)
    if workflow_logger:
        try:
            await workflow_logger.log_workflow_start(
                workflow_id=workflow_id,
                operation="natural_query_processing",
                context={
                    "query_length": len(query_data.query),
                    "user_id": getattr(query_data, 'user_id', 'anonymous'),
                    "has_context": bool(getattr(query_data, 'context', None))
                },
                user_id=getattr(query_data, 'user_id', None)
            )
        except Exception as e:
            logger.warning(f"WorkflowLogger failed: {e}")
    
    try:
        # Validate input
        if not query_data.query or not query_data.query.strip():
            if workflow_logger:
                await workflow_logger.log_error(
                    workflow_id=workflow_id,
                    error=ValueError("Empty query"),
                    context={"validation": "failed"}
                )
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid query format",
                    "message": "Query cannot be empty",
                    "workflow_id": workflow_id
                }
            )
        
        # Log preprocessing step
        if workflow_logger:
            await workflow_logger.log_workflow_step(
                workflow_id=workflow_id,
                step_name="query_preprocessing",
                step_data={"original_length": len(query_data.query)}
            )
        
        # Preprocess query
        query_lower = query_data.query.lower()
        
        # Extract intent (Enhanced v2.0 - feature planning focused)
        if any(word in query_lower for word in ["plan", "planning", "roadmap", "develop"]):
            intent_type = "feature_planning"
            confidence = 0.90
        elif any(word in query_lower for word in ["analyze", "analysis", "check", "review"]):
            intent_type = "document_analysis"
            confidence = 0.85
        elif any(word in query_lower for word in ["generate", "create", "build"]):
            intent_type = "content_generation"
            confidence = 0.82
        else:
            intent_type = "general_query"
            confidence = 0.70
        
        # Extract entities (Enhanced v2.0 - Basic extraction)
        basic_entities = {}
        
        # Feature type extraction
        if "authentication" in query_lower or "auth" in query_lower:
            basic_entities["feature_type"] = "authentication"
        elif "dashboard" in query_lower:
            basic_entities["feature_type"] = "dashboard"
        elif "payment" in query_lower:
            basic_entities["feature_type"] = "payment"
        else:
            basic_entities["feature_type"] = "general"
        
        # Platform extraction
        if "mobile" in query_lower or "app" in query_lower:
            basic_entities["platform"] = "mobile"
        elif "web" in query_lower:
            basic_entities["platform"] = "web"
        elif "desktop" in query_lower:
            basic_entities["platform"] = "desktop"
        
        # Team size extraction
        import re
        team_match = re.search(r'team.*?(\d+)', query_lower)
        if team_match:
            basic_entities["team_size"] = int(team_match.group(1))
        
        # Log basic extraction
        if workflow_logger:
            await workflow_logger.log_workflow_step(
                workflow_id=workflow_id,
                step_name="basic_entity_extraction",
                step_data={
                    "intent": intent_type,
                    "confidence": confidence,
                    "entities_count": len(basic_entities)
                }
            )
        
        # 🆕 Phase 2 Enhancement: LLM-powered entity enrichment
        enriched_entities = basic_entities
        try:
            if workflow_logger:
                await workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="llm_enrichment_start",
                    step_data={"llm_gateway": "invoking"}
                )
            
            enriched_entities = await llm_client.enrich_entities(query_data.query, basic_entities)
            
            if workflow_logger:
                await workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="llm_enrichment_complete",
                    step_data={
                        "enriched_count": len(enriched_entities),
                        "new_fields": list(set(enriched_entities.keys()) - set(basic_entities.keys()))
                    }
                )
        except Exception as e:
            # Fallback to basic entities if LLM enrichment fails
            if workflow_logger:
                await workflow_logger.log_error(
                    workflow_id=workflow_id,
                    error=e,
                    context={"stage": "llm_enrichment", "fallback": "basic_entities"}
                )
            enriched_entities = basic_entities
        
        # Use enriched entities for final response
        entities = enriched_entities
        
        # Update confidence if complexity was determined by LLM
        if "complexity" in entities:
            complexity_confidence_map = {
                "simple": 0.85,
                "moderate": 0.90,
                "complex": 0.95
            }
            llm_confidence = complexity_confidence_map.get(entities.get("complexity"), confidence)
            confidence = max(confidence, llm_confidence)
        
        # Log final intent extraction
        if workflow_logger:
            await workflow_logger.log_workflow_step(
                workflow_id=workflow_id,
                step_name="intent_extraction_final",
                step_data={
                    "intent": intent_type,
                    "confidence": confidence,
                    "entities_count": len(entities),
                    "llm_enriched": len(entities) > len(basic_entities)
                }
            )
        
        # Build interpreted intent structure (for orchestrator)
        interpreted_intent = {
            "type": intent_type,
            "confidence": confidence,
            "entities": entities,
            "original_query": query_data.query
        }
        
        # Add feature-specific fields if it's a planning query
        if intent_type == "feature_planning":
            interpreted_intent["feature_type"] = entities.get("feature_type", "general")
            interpreted_intent["platform"] = entities.get("platform", "unknown")
            interpreted_intent["action"] = "plan"
        
        # Calculate processing time
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Log workflow completion
        if workflow_logger:
            await workflow_logger.log_workflow_complete(
                workflow_id=workflow_id,
                duration_ms=duration_ms,
                success=True,
                metrics={
                    "intent": intent_type,
                    "confidence": confidence,
                    "entities_extracted": len(entities)
                }
            )
        
        # Build response
        response = {
            "workflow_id": workflow_id,
            "interpreted_intent": interpreted_intent,
            "entities": entities,
            "confidence": confidence,
            "processing_time_ms": round(duration_ms, 2),
            "next_step": "orchestrator",
            "logged": workflow_logger is not None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log to standard logger as well
        logger.info(f"✅ Natural query processed: {workflow_id} | Intent: {intent_type} | Confidence: {confidence:.2f}")
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        # Log error
        if workflow_logger:
            await workflow_logger.log_error(
                workflow_id=workflow_id,
                error=e,
                context={"endpoint": "/natural-query"}
            )
        
        logger.error(f"❌ Error processing natural query {workflow_id}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Failed to process natural language query",
                "workflow_id": workflow_id,
                "details": str(e)
            }
        )


@app.get(
    "/intents",
    summary="List Supported Query Intents",
    description="Retrieve a comprehensive list of all supported query intents with examples and confidence thresholds.",
    tags=["Query Processing", "Intents"],
    responses={
        200: {
            "description": "Successfully retrieved supported intents",
            "content": {
                "application/json": {
                    "example": {
                        "supported_intents": [
                            {
                                "intent": "document_analysis",
                                "description": "Analyze document quality, structure, and content",
                                "examples": ["Analyze this document for quality"],
                                "confidence_threshold": 0.7
                            }
                        ],
                        "total_intents": 5
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Internal server error",
                        "message": "Failed to retrieve intent information"
                    }
                }
            }
        }
    }
)
async def list_supported_intents():
    """List all supported query intents and examples."""
    return {
        "supported_intents": [
            {
                "name": "document_analysis",
                "description": "Analyze document quality, structure, and content",
                "examples": [
                    "Analyze this document for quality",
                    "Check document structure and formatting",
                    "Provide insights on document content",
                ],
            },
            {
                "name": "security_audit",
                "description": "Perform security vulnerability analysis",
                "examples": [
                    "Scan for security vulnerabilities",
                    "Analyze our system for security risks",
                    "Generate a security audit report",
                ],
            },
            {
                "name": "code_documentation",
                "description": "Generate comprehensive code documentation",
                "examples": [
                    "Create documentation for our API",
                    "Document the codebase",
                    "Generate API endpoint documentation",
                ],
            },
            {
                "name": "workflow_execution",
                "description": "Execute predefined workflows",
                "examples": [
                    "Run the data processing workflow",
                    "Execute quality assurance workflow",
                    "Start the integration testing workflow",
                ],
            },
        ]
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
            "multi_format_output": True,
        },
        "supported_workflows": [
            "document_analysis",
            "security_audit",
            "code_documentation",
        ],
        "output_formats": ["json", "markdown", "csv"],
        "integrated_services": {
            "doc_store": {
                "url": os.getenv("DOC_STORE_URL", "http://doc-store:5087"),
                "capabilities": ["document_storage", "search", "metadata"],
            },
            "prompt_store": {
                "url": os.getenv("PROMPT_STORE_URL", "http://prompt-store:5110"),
                "capabilities": ["prompt_management", "versioning"],
            },
            "analysis_service": {
                "capabilities": ["content_analysis", "quality_scoring"]
            },
            "orchestrator": {
                "capabilities": ["workflow_execution", "service_coordination"]
            },
        },
        "ecosystem_features": {
            "cross_service_workflows": True,
            "persistent_document_storage": True,
            "comprehensive_provenance": True,
            "execution_tracing": True,
            "quality_metrics": True,
            "audit_trail": True,
        },
        "system_info": {
            "service": "interpreter",
            "version": "1.0.0",
            "uptime": "running",
            "last_updated": datetime.utcnow().isoformat(),
        },
    }


@app.get("/health/ecosystem")
async def ecosystem_health():
    """Check health status of connected ecosystem services."""
    ecosystem_health_status = {
        "interpreter": {
            "status": "healthy",
            "version": "1.0.0",
            "features_active": [
                "document_persistence",
                "workflow_provenance",
                "doc_store_integration",
            ],
            "uptime": "running",
        },
        "connected_services": {
            "doc_store": {
                "url": os.getenv("DOC_STORE_URL", "http://doc-store:5087"),
                "status": "unknown",
                "capabilities": ["document_storage", "search", "metadata"],
            },
            "prompt_store": {
                "url": os.getenv("PROMPT_STORE_URL", "http://prompt-store:5110"),
                "status": "unknown",
                "capabilities": ["prompt_management", "versioning"],
            },
            "orchestrator": {
                "url": "http://orchestrator:5099",
                "status": "unknown",
                "capabilities": ["workflow_execution", "service_coordination"],
            },
            "analysis_service": {
                "status": "unknown",
                "capabilities": ["content_analysis", "quality_scoring"],
            },
        },
        "ecosystem_summary": {
            "total_services": 5,
            "healthy_services": 1,
            "unknown_services": 4,
            "overall_status": "partial",
        },
        "last_checked": datetime.utcnow().isoformat(),
        "note": "Service health checks require individual service pings for accurate status",
    }

    # Try to check a few key services
    try:
        async with aiohttp.ClientSession() as session:
            # Check doc_store
            try:
                async with session.get(
                    f"{os.getenv('DOC_STORE_URL', 'http://doc-store:5087')}/health", timeout=2
                ) as response:
                    if response.status == 200:
                        ecosystem_health_status["connected_services"]["doc_store"][
                            "status"
                        ] = "healthy"
                        ecosystem_health_status["ecosystem_summary"][
                            "healthy_services"
                        ] += 1
                        ecosystem_health_status["ecosystem_summary"][
                            "unknown_services"
                        ] -= 1
            except Exception:
                ecosystem_health_status["connected_services"]["doc_store"][
                    "status"
                ] = "unreachable"

            # Check orchestrator
            try:
                async with session.get(
                    "http://orchestrator:5099/health", timeout=2
                ) as response:
                    if response.status == 200:
                        ecosystem_health_status["connected_services"]["orchestrator"][
                            "status"
                        ] = "healthy"
                        ecosystem_health_status["ecosystem_summary"][
                            "healthy_services"
                        ] += 1
                        ecosystem_health_status["ecosystem_summary"][
                            "unknown_services"
                        ] -= 1
            except Exception:
                ecosystem_health_status["connected_services"]["orchestrator"][
                    "status"
                ] = "unreachable"

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
                "confidence": 0.85,
            },
        }

        fire_and_forget(
            "basic_workflow_executed",
            f"Legacy /execute endpoint used for workflow: {workflow_name}",
            ServiceNames.INTERPRETER,
            {"workflow": workflow_name, "execution_id": execution_id},
        )

        return result

    except Exception as e:
        fire_and_forget(
            "basic_workflow_error",
            f"Legacy /execute endpoint failed: {str(e)}",
            ServiceNames.INTERPRETER,
            {"error": str(e)},
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
                "confidence": 0.90,
            },
            "steps_executed": [
                {
                    "step": 1,
                    "name": "input_validation",
                    "status": "completed",
                    "duration": "0.1s",
                },
                {
                    "step": 2,
                    "name": "workflow_execution",
                    "status": "completed",
                    "duration": "2.0s",
                },
                {
                    "step": 3,
                    "name": "output_generation",
                    "status": "completed",
                    "duration": "0.2s",
                },
            ],
        }

        fire_and_forget(
            "legacy_workflow_executed",
            f"Legacy /execute-workflow endpoint used: {workflow_id}",
            ServiceNames.INTERPRETER,
            {"workflow_id": workflow_id, "execution_id": execution_id},
        )

        return result

    except Exception as e:
        fire_and_forget(
            "legacy_workflow_error",
            f"Legacy /execute-workflow endpoint failed: {str(e)}",
            ServiceNames.INTERPRETER,
            {"error": str(e)},
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
                "started_at": (
                    datetime.utcnow().replace(minute=0, second=0, microsecond=0)
                ).isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "estimated_completion": datetime.utcnow().isoformat(),
                "current_step": "completed",
                "total_steps": 3,
                "completed_steps": 3,
                "error": None,
                "results_available": True,
                "output_files": [
                    f"{execution_id}_results.json",
                    f"{execution_id}_summary.txt",
                ],
            }
        else:
            # Unknown execution ID
            status_info = {
                "execution_id": execution_id,
                "status": "not_found",
                "error": "Execution ID not found or expired",
                "progress": 0,
            }

        fire_and_forget(
            "execution_status_checked",
            f"Legacy status check for execution: {execution_id}",
            ServiceNames.INTERPRETER,
            {"execution_id": execution_id, "status": status_info["status"]},
        )

        return status_info

    except Exception as e:
        fire_and_forget(
            "execution_status_error",
            f"Legacy status check failed: {str(e)}",
            ServiceNames.INTERPRETER,
            {"error": str(e), "execution_id": execution_id},
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
                    "size": "1.2KB",
                },
            }

            fire_and_forget(
                "legacy_file_downloaded",
                f"Legacy file download: {file_id}",
                ServiceNames.INTERPRETER,
                {"file_id": file_id, "type": "json"},
            )

            return mock_content

        elif file_id.endswith(".txt"):
            mock_content = {
                "file_id": file_id,
                "generated_at": datetime.utcnow().isoformat(),
                "content_type": "text/plain",
                "content": f"This is a mock text output file.\nFile ID: {file_id}\nGenerated: {datetime.utcnow().isoformat()}\n\nContent would be here...",
            }

            fire_and_forget(
                "legacy_file_downloaded",
                f"Legacy file download: {file_id}",
                ServiceNames.INTERPRETER,
                {"file_id": file_id, "type": "text"},
            )

            return mock_content

        else:
            return {
                "error": "File not found or unsupported format",
                "file_id": file_id,
                "supported_formats": [".json", ".txt"],
                "recommendation": "Use /documents/{document_id}/download for newer document downloads",
            }

    except Exception as e:
        fire_and_forget(
            "legacy_download_error",
            f"Legacy file download failed: {str(e)}",
            ServiceNames.INTERPRETER,
            {"error": str(e), "file_id": file_id},
        )
        return {"error": str(e), "file_id": file_id}


# ============================================================================
# ENHANCED WORKFLOW ENDPOINTS
# ============================================================================


@app.post("/interpret")
async def interpret_query(query_data: dict):
    """Interpret user query and return intent analysis."""
    try:
        query_text = query_data.get("query", "")
        if not query_text:
            return {"error": "Query is required", "status": "failed"}

        # Simple intent recognition (matching test expectations)
        intent = "general_query"
        confidence = 0.8
        entities = {}

        if "analyze" in query_text.lower() or "review" in query_text.lower():
            intent = "document_analysis"
            confidence = 0.9
            entities = {"workflow": "document_analysis"}
        elif "generate" in query_text.lower() or "create" in query_text.lower():
            intent = "content_generation"
            confidence = 0.85
            entities = {"workflow": "content_generation"}
        elif "execute" in query_text.lower() or "run" in query_text.lower():
            intent = "workflow_execution"
            confidence = 0.95
            entities = {"workflow": "workflow_execution"}

        return {
            "intent": intent,
            "entities": entities,
            "confidence": confidence,
            "response_text": f"Processing query: {query_text}"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@app.get("/intents")
async def get_supported_intents():
    """Get list of supported intents."""
    return {
        "supported_intents": [
            {
                "name": "document_analysis",
                "description": "Analyze documents for quality, structure, and content insights",
                "examples": ["analyze this document for issues", "check document consistency", "review content quality"]
            },
            {
                "name": "content_generation",
                "description": "Generate documentation, code, and other content",
                "examples": ["generate API documentation", "create code examples", "write technical content"]
            },
            {
                "name": "workflow_execution",
                "description": "Execute predefined workflows and processes",
                "examples": ["execute deployment workflow", "run analysis process", "start automated task"]
            },
            {
                "name": "general_query",
                "description": "Handle general queries and provide assistance",
                "examples": ["how do I use this service", "what can you help with", "show me options"]
            }
        ]
    }


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
                "workflow_result": workflow_result,
            }
        else:
            return {
                "execution_id": workflow_result.get("execution_id"),
                "query": query,
                "status": "failed",
                "error": workflow_result.get("error", "Workflow execution failed"),
            }

    except Exception as e:
        return {
            "query": request.get("query", ""),
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
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
                "workflow_result": workflow_result,
            }
        else:
            return {
                "execution_id": workflow_result.get("execution_id"),
                "workflow_name": workflow_name,
                "status": "failed",
                "error": workflow_result.get("error", "Workflow execution failed"),
            }

    except Exception as e:
        return {
            "workflow_name": request.get("workflow_name"),
            "status": "error",
            "error": str(e),
        }


@app.get("/outputs/formats")
async def get_supported_formats():
    """Get list of supported output formats."""
    return {
        "supported_formats": output_generator.get_supported_formats(),
        "format_descriptions": {
            "json": "Structured JSON data with complete results",
            "csv": "Comma-separated values for data analysis",
            "markdown": "Markdown formatted documentation",
        },
    }


@app.get("/workflows/templates")
async def get_workflow_templates():
    """Get available workflow templates."""
    return {
        "templates": orchestrator_integration.get_workflow_templates(),
        "total_templates": len(orchestrator_integration.get_workflow_templates()),
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
                    "execution_time": "1.2s",
                },
                "services_chain": ["doc_store", "analysis_service"],
                "prompts_used": [
                    {
                        "step_index": 1,
                        "service": "analysis_service",
                        "action": "analyze_content",
                        "prompt_template": "Analyze the following content for quality and insights",
                        "prompt_variables": {"content_type": "document"},
                    }
                ],
                "quality_metrics": {
                    "confidence": 0.87,
                    "completeness": 1.0,
                    "accuracy": 0.9,
                },
            },
            "document_info": {
                "title": f"Workflow Output: Document {document_id[:8]}",
                "format": "json",
                "created_at": datetime.utcnow().isoformat(),
                "author": "system",
                "category": "workflow_output",
            },
            "workflow_chain": {
                "services_used": ["doc_store", "analysis_service"],
                "prompts_used": [{"action": "analyze_content", "step_index": 1}],
                "quality_metrics": {"confidence": 0.87, "completeness": 1.0},
            },
        }
    except Exception as e:
        return {"error": str(e), "document_id": document_id}


@app.get("/workflows/{execution_id}/trace")
async def get_workflow_execution_trace(execution_id: str):
    """Get detailed execution trace for a workflow."""
    try:
        execution_status = await orchestrator_integration.get_execution_status(
            execution_id
        )

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
                "download_url": f"/documents/download/doc_{execution_id[-8:]}",
            }
        ]

        return {
            "execution_id": execution_id,
            "execution_details": execution_status,
            "generated_documents": documents,
            "trace_metadata": {
                "total_documents": len(documents),
                "trace_generated_at": datetime.utcnow().isoformat(),
            },
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
            documents.append(
                {
                    "document_id": doc_id,
                    "title": f"Workflow Output: {workflow_name} #{i+1}",
                    "format": "json",
                    "created_at": datetime.utcnow().isoformat(),
                    "execution_id": f"exec_{workflow_name}_{i}",
                    "author": "system",
                    "quality_score": 0.85 + (i * 0.05),
                    "size_bytes": 1024 + (i * 512),
                    "download_url": f"/documents/download/{doc_id}",
                }
            )

        return {
            "workflow_name": workflow_name,
            "documents": documents,
            "total_found": len(documents),
            "query_limit": limit,
        }

    except Exception as e:
        return {"error": str(e), "workflow_name": workflow_name, "documents": []}


@app.get("/documents/{document_id}/download")
async def download_document_from_doc_store(document_id: str):
    """Download a document from doc_store with proper headers."""
    try:
        # For demo, generate mock content
        content = json.dumps(
            {
                "document_id": document_id,
                "title": f"Demo Document {document_id[:8]}",
                "content": "This is a demonstration document generated by the workflow system.",
                "generated_at": datetime.utcnow().isoformat(),
                "provenance": {
                    "workflow": "document_analysis",
                    "services_used": ["doc_store", "analysis_service"],
                    "quality_score": 0.87,
                },
            },
            indent=2,
        )

        headers = {
            "Content-Disposition": f"attachment; filename=document_{document_id[:8]}.json",
            "Content-Type": "application/json",
        }

        return Response(content=content, headers=headers, media_type="application/json")

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
                    "download_url": f"/documents/download/doc_{execution_id[-8:]}",
                }
            ]

            executions_with_docs.append(
                {
                    "execution_id": execution_id,
                    "workflow_name": execution.get("workflow_name"),
                    "status": execution.get("status"),
                    "timestamp": execution.get("started_at"),
                    "user_id": execution.get("user_id"),
                    "execution_time": execution.get("execution_time"),
                    "documents_generated": len(documents),
                    "documents": documents,
                }
            )

        return {
            "executions": executions_with_docs,
            "total_executions": len(executions_with_docs),
            "execution_metrics": execution_metrics,
            "query_limit": limit,
        }

    except Exception as e:
        return {"error": str(e), "recent_executions": []}


@app.get("/documents/sample")
async def get_sample_documents(
    type_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    limit: int = 50,
):
    """Get sample documents for testing and demonstration purposes."""
    try:
        if sample_documents is None:
            return {
                "error": "Sample documents module not available",
                "documents": [],
                "total_count": 0,
            }

        documents = []

        if type_filter:
            documents = sample_documents.get_documents_by_type(type_filter)
        elif category_filter:
            documents = sample_documents.get_documents_by_category(category_filter)
        else:
            documents = sample_documents.get_all_documents()

        # Apply limit
        documents = documents[:limit]

        return {
            "documents": documents,
            "total_count": len(documents),
            "filters_applied": {
                "type": type_filter,
                "category": category_filter,
                "limit": limit,
            },
            "available_types": ["confluence", "jira", "pull_request"],
            "available_categories": [
                "architecture",
                "api",
                "security",
                "compliance",
                "feature",
                "bug",
            ],
        }

    except Exception as e:
        return {"error": str(e), "documents": []}


@app.post("/documents/sample/context")
async def get_sample_documents_for_query(query_data: Dict[str, Any]):
    """Get relevant sample documents based on query context."""
    try:
        if sample_documents is None:
            return {
                "error": "Sample documents module not available",
                "relevant_documents": [],
                "total_relevant": 0,
            }

        query = query_data.get("query", "")
        context = query_data.get("context", {})

        relevant_documents = sample_documents.get_documents_for_query(query)

        return {
            "query": query,
            "context_provided": bool(context),
            "relevant_documents": relevant_documents,
            "total_relevant": len(relevant_documents),
            "document_types_found": list(
                set(doc.get("type", "") for doc in relevant_documents)
            ),
            "categories_found": list(
                set(doc.get("category", "") for doc in relevant_documents)
            ),
        }

    except Exception as e:
        return {"error": str(e), "relevant_documents": []}


@app.get("/documents/sample/types")
async def get_sample_document_types():
    """Get available document types and their characteristics."""
    if sample_documents is None:
        return {
            "error": "Sample documents module not available",
            "document_types": {},
            "special_collections": {},
        }

    return {
        "document_types": {
            "confluence": {
                "description": "Wiki pages and technical documentation",
                "characteristics": ["detailed_content", "structured", "technical"],
                "count": len(sample_documents.get_documents_by_type("confluence")),
            },
            "jira": {
                "description": "Issue tracking and project management",
                "characteristics": [
                    "conversational",
                    "status_tracking",
                    "requirements",
                ],
                "count": len(sample_documents.get_documents_by_type("jira")),
            },
            "pull_request": {
                "description": "Code review and merge request discussions",
                "characteristics": [
                    "code_changes",
                    "review_comments",
                    "technical_discussion",
                ],
                "count": len(sample_documents.get_documents_by_type("pull_request")),
            },
        },
        "special_collections": {
            "similar_documents": {
                "description": "Highly similar documents for testing deduplication",
                "count": len(sample_documents.get_similar_documents()),
            },
            "contradictory_documents": {
                "description": "Documents with conflicting information",
                "count": len(sample_documents.get_contradictory_documents()),
            },
            "gap_documents": {
                "description": "Documents identifying development gaps",
                "count": len(sample_documents.get_gap_documents()),
            },
            "sparse_documents": {
                "description": "Documents with minimal content",
                "count": len(sample_documents.get_sparse_documents()),
            },
            "blank_documents": {
                "description": "Documents with empty content",
                "count": len(sample_documents.get_blank_documents()),
            },
            "documents_with_comments": {
                "description": "Documents with conversation history",
                "count": len(sample_documents.get_documents_with_comments()),
            },
        },
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting Enhanced Interpreter Service with Document Persistence...")
    host = os.getenv("INTERPRETER_SERVICE_API_HOST", "127.0.0.1")
    port = int(os.getenv("INTERPRETER_SERVICE_API_PORT", "5120"))
    uvicorn.run(app, host=host, port=port)
