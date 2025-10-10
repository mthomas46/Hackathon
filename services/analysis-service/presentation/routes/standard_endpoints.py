"""Standard Endpoints.

Standard service endpoints required by the ecosystem: about-me, endpoints, provider-consumer.
These endpoints provide service metadata, API discovery, and relationship information.
"""
from typing import Any, Dict, List
from fastapi import APIRouter, Request

# Service metadata
SERVICE_NAME = "analysis-service"
SERVICE_VERSION = "1.0.0"
SERVICE_DESCRIPTION = "Comprehensive document analysis service for consistency checking, quality assessment, and trend analysis"

router = APIRouter(tags=["Standard Endpoints"])


@router.get("/about-me")
async def about_me():
    """Service descriptor with capabilities and features.

    Provides comprehensive information about the analysis service including
    its capabilities, features, architecture, and integration points for
    service discovery and ecosystem integration.

    Returns:
        Detailed service information and capabilities
    """
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": SERVICE_DESCRIPTION,
        "capabilities": [
            "Document consistency analysis",
            "Semantic similarity detection",
            "Sentiment and tone analysis",
            "Content quality assessment",
            "Trend analysis and forecasting",
            "Risk assessment",
            "Maintenance forecasting",
            "Quality degradation detection",
            "Change impact analysis",
            "PR confidence scoring",
            "Automated remediation",
            "Workflow integration",
            "Cross-repository analysis",
            "Distributed processing",
            "Report generation"
        ],
        "features": {
            "analysis_types": [
                "semantic_similarity",
                "sentiment",
                "tone",
                "quality",
                "trends",
                "risk",
                "maintenance_forecast",
                "quality_degradation",
                "change_impact"
            ],
            "processing": {
                "synchronous": True,
                "asynchronous": True,
                "distributed": True,
                "batch": True
            },
            "integrations": {
                "doc_store": True,
                "prompt_store": True,
                "interpreter": True,
                "source_agent": True,
                "orchestrator": True,
                "log_collector": True
            },
            "automation": {
                "automated_remediation": True,
                "workflow_triggers": True,
                "webhook_support": True,
                "scheduled_analysis": True
            }
        },
        "ecosystem_role": "Core Analysis Engine",
        "tier": 1,
        "dependencies": {
            "providers": [
                {"service": "doc-store", "purpose": "Document storage and retrieval", "critical": True},
                {"service": "prompt-store", "purpose": "Analysis prompt templates", "critical": False},
                {"service": "interpreter", "purpose": "Natural language query processing", "critical": False}
            ],
            "consumers": [
                {"service": "orchestrator", "purpose": "Workflow coordination", "critical": True},
                {"service": "dashboard", "purpose": "Results visualization", "critical": False},
                {"service": "report-generator", "purpose": "Report compilation", "critical": False}
            ]
        },
        "architecture": {
            "pattern": "Domain-Driven Design",
            "principles": ["DDD", "Clean Architecture", "CQRS", "Event-Driven"],
            "style": "Microservice"
        },
        "quality_metrics": {
            "test_coverage": "65%+",
            "code_style": "Black, Pylint",
            "type_checking": "MyPy",
            "complexity": "Moderate (enterprise-scale)"
        },
        "api": {
            "version": "v1",
            "base_path": "/",
            "documentation": "/docs",
            "openapi_spec": "/openapi.json",
            "authentication": "Optional",
            "rate_limiting": "Configurable"
        },
        "scale": {
            "endpoints": 62,
            "analysis_types": 15,
            "workers": "Dynamic",
            "throughput": "High",
            "latency": "Low to Moderate (depends on analysis type)"
        }
    }


@router.get("/endpoints")
async def list_endpoints(request: Request):
    """Returns a JSON list of all endpoints provided by the service.

    Discovers and lists all registered API endpoints with their HTTP methods,
    paths, summaries, and tags for API discovery and documentation purposes.

    Args:
        request: FastAPI request object to access app routes

    Returns:
        Comprehensive list of all service endpoints
    """
    endpoints_list = []
    
    # Get all routes from the FastAPI app
    for route in request.app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            methods = list(route.methods) if route.methods else []
            # Filter out HEAD and OPTIONS which are auto-generated
            methods = [m for m in methods if m not in ["HEAD", "OPTIONS"]]
            
            if methods:
                endpoint_info = {
                    "path": route.path,
                    "methods": methods,
                    "name": route.name if hasattr(route, "name") else "unnamed",
                    "summary": getattr(route, "summary", None) or "No summary available",
                }
                
                # Add tags if available
                if hasattr(route, "tags") and route.tags:
                    endpoint_info["tags"] = list(route.tags)
                
                # Add description if available
                if hasattr(route, "description") and route.description:
                    endpoint_info["description"] = route.description
                
                endpoints_list.append(endpoint_info)
    
    # Sort by path for easier reading
    endpoints_list.sort(key=lambda x: x["path"])
    
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "total_endpoints": len(endpoints_list),
        "endpoints": endpoints_list,
        "categories": {
            "status": "Status and health endpoints",
            "analysis": "Core document analysis endpoints",
            "findings": "Analysis findings and detectors",
            "remediation": "Automated remediation",
            "workflows": "Workflow integration",
            "repositories": "Cross-repository analysis",
            "pr_confidence": "PR confidence scoring",
            "integration": "Service integrations",
            "reports": "Report generation",
            "distributed": "Distributed processing"
        }
    }


@router.get("/provider-consumer")
async def provider_consumer_relationships():
    """Returns service relationships (provider/consumer).

    Lists all services this service connects to, marking each relationship
    as provider (provides data to us), consumer (consumes data from us),
    or provide-consume (bidirectional relationship).

    Returns:
        Comprehensive service relationship mapping
    """
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "relationships": {
            "providers": [
                {
                    "service": "doc-store",
                    "relationship": "provider",
                    "purpose": "Provides document content for analysis",
                    "endpoints_used": [
                        "GET /documents/{id}",
                        "GET /documents/_list",
                        "POST /documents/search"
                    ],
                    "data_consumed": ["Documents", "Metadata", "Content"],
                    "criticality": "high"
                },
                {
                    "service": "prompt-store",
                    "relationship": "provider",
                    "purpose": "Provides analysis prompt templates",
                    "endpoints_used": [
                        "GET /prompts/{category}/{name}",
                        "GET /prompts/categories"
                    ],
                    "data_consumed": ["Prompts", "Templates", "Variables"],
                    "criticality": "medium"
                },
                {
                    "service": "interpreter",
                    "relationship": "provider",
                    "purpose": "Provides natural language query interpretation",
                    "endpoints_used": [
                        "POST /interpret",
                        "POST /execute-workflow"
                    ],
                    "data_consumed": ["Query interpretations", "Workflow definitions"],
                    "criticality": "low"
                },
                {
                    "service": "source-agent",
                    "relationship": "provider",
                    "purpose": "Provides source code and repository data",
                    "endpoints_used": [
                        "GET /repositories/{repo_id}",
                        "GET /files/{file_id}"
                    ],
                    "data_consumed": ["Source code", "Repository metadata", "File content"],
                    "criticality": "medium"
                }
            ],
            "consumers": [
                {
                    "service": "orchestrator",
                    "relationship": "consumer",
                    "purpose": "Consumes analysis results for workflow coordination",
                    "data_provided": ["Analysis results", "Status updates", "Findings"],
                    "endpoints_provided": ["All analysis endpoints"],
                    "criticality": "high"
                },
                {
                    "service": "dashboard",
                    "relationship": "consumer",
                    "purpose": "Consumes analysis results for visualization",
                    "data_provided": ["Analysis results", "Trends", "Statistics"],
                    "endpoints_provided": [
                        "GET /findings",
                        "GET /distributed/stats",
                        "POST /analyze/*"
                    ],
                    "criticality": "medium"
                },
                {
                    "service": "report-generator",
                    "relationship": "consumer",
                    "purpose": "Consumes analysis results for report generation",
                    "data_provided": ["Analysis results", "Findings", "Recommendations"],
                    "endpoints_provided": [
                        "POST /reports/generate",
                        "GET /reports/*"
                    ],
                    "criticality": "medium"
                },
                {
                    "service": "log-collector",
                    "relationship": "consumer",
                    "purpose": "Consumes log data for centralized logging",
                    "data_provided": ["Logs", "Events", "Metrics"],
                    "endpoints_provided": ["N/A (push-based)"],
                    "criticality": "low"
                }
            ],
            "provide_consume": [
                {
                    "service": "architecture-digitizer",
                    "relationship": "provide-consume",
                    "purpose": "Bidirectional: provides architecture data, consumes analysis results",
                    "data_flow": {
                        "inbound": ["Architecture diagrams", "Component definitions", "Connections"],
                        "outbound": ["Architecture analysis results", "Consistency findings"]
                    },
                    "endpoints_used": [
                        "GET /architecture/{id}",
                        "POST /architecture/validate"
                    ],
                    "endpoints_provided": [
                        "POST /architecture/analyze"
                    ],
                    "criticality": "medium"
                }
            ]
        },
        "dependencies": {
            "external_services": [
                {
                    "name": "AWS Bedrock",
                    "purpose": "LLM processing for advanced analysis",
                    "type": "external_api",
                    "required": False,
                    "note": "Optional for AI-powered analysis features"
                }
            ],
            "databases": [
                {
                    "name": "Redis",
                    "purpose": "Caching and distributed task queue",
                    "type": "cache/queue",
                    "required": True
                }
            ],
            "message_queues": [],
            "infrastructure": [
                {
                    "name": "Docker",
                    "purpose": "Containerization",
                    "required": True
                }
            ]
        },
        "provides_data_to": [
            "orchestrator",
            "dashboard",
            "report-generator",
            "log-collector"
        ],
        "consumes_data_from": [
            "doc-store",
            "prompt-store",
            "interpreter",
            "source-agent"
        ],
        "self_contained": False,
        "reason_not_self_contained": "Requires doc-store for document access and Redis for distributed processing",
        "data_flow": {
            "inbound": [
                {"source": "orchestrator", "data_type": "Analysis requests", "frequency": "high"},
                {"source": "doc-store", "data_type": "Document content", "frequency": "high"},
                {"source": "prompt-store", "data_type": "Prompt templates", "frequency": "medium"},
                {"source": "interpreter", "data_type": "NL query interpretations", "frequency": "low"},
                {"source": "source-agent", "data_type": "Source code", "frequency": "medium"},
                {"source": "architecture-digitizer", "data_type": "Architecture data", "frequency": "low"}
            ],
            "outbound": [
                {"destination": "orchestrator", "data_type": "Analysis results", "frequency": "high"},
                {"destination": "dashboard", "data_type": "Analytics data", "frequency": "medium"},
                {"destination": "report-generator", "data_type": "Report data", "frequency": "medium"},
                {"destination": "log-collector", "data_type": "Logs and events", "frequency": "high"},
                {"destination": "architecture-digitizer", "data_type": "Architecture analysis", "frequency": "low"}
            ]
        },
        "integration_points": {
            "rest_apis": {
                "inbound": "All service endpoints",
                "outbound": ["doc-store", "prompt-store", "interpreter", "source-agent"]
            },
            "events": {
                "publishes": ["analysis.completed", "analysis.failed", "workflow.triggered"],
                "subscribes": ["document.updated", "repository.changed"]
            },
            "webhooks": {
                "receives": ["GitHub", "GitLab", "CI/CD systems"],
                "sends": ["Notifications to owners"]
            }
        },
        "service_mesh": {
            "tier": 1,
            "role": "Core Analysis Engine",
            "critical_path": True,
            "scaling_strategy": "Horizontal (workers) + Vertical (resources)"
        }
    }

