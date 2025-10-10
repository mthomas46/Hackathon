"""
REST API router with standard endpoints.

Provides standard endpoints for ecosystem integration:
- GET /health - Health check
- GET /about-me - Service descriptor
- GET /endpoints - Endpoint listing
- GET /provider-consumer - Service relationships
- GET /openapi.json - OpenAPI specification
"""

from fastapi import APIRouter, FastAPI
from datetime import datetime, timezone
from typing import Dict, List, Any
import time
import httpx

# Track service start time
SERVICE_START_TIME = time.time()

# Create router
api_router = APIRouter(tags=["standard"])


def get_uptime() -> int:
    """Get service uptime in seconds."""
    return int(time.time() - SERVICE_START_TIME)


def check_log_collector_health() -> str:
    """
    Check if log-collector is reachable.
    
    Returns:
        "connected" if reachable, "unavailable" otherwise
    """
    try:
        response = httpx.get("http://localhost:8104/health", timeout=2.0)
        if response.status_code == 200:
            return "connected"
    except Exception:
        pass
    return "unavailable"


@api_router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns health status, uptime, and dependency status.
    
    Returns:
        {
            "status": "healthy",
            "service": "data-services-dashboard",
            "version": "1.0.0",
            "timestamp": "2025-10-09T12:00:00Z",
            "uptime_seconds": 3600,
            "dependencies": {
                "log_collector": "connected",
                "ui": "running"
            }
        }
    """
    return {
        "status": "healthy",
        "service": "data-services-dashboard",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": get_uptime(),
        "dependencies": {
            "log_collector": check_log_collector_health(),
            "ui": "running"
        }
    }


@api_router.get("/about-me")
async def about_me() -> Dict[str, Any]:
    """
    Service descriptor endpoint.
    
    Returns comprehensive information about the dashboard service.
    
    Returns:
        Detailed service information including interfaces, capabilities,
        architecture, and dependencies
    """
    return {
        "service": "data-services-dashboard",
        "version": "1.0.0",
        "type": "dashboard",
        "architecture": "hybrid",
        
        "description": """
        Real-time monitoring dashboard for datastore operations across the ecosystem.
        
        Provides both a Streamlit web UI for human operators and a REST API
        for programmatic access and ecosystem integration.
        """,
        
        "interfaces": {
            "web_ui": {
                "type": "streamlit",
                "url": "http://localhost:8501",
                "port": 8501,
                "consumers": "human-operators",
                "description": "Interactive web dashboard with real-time visualizations"
            },
            "rest_api": {
                "type": "rest",
                "base_path": "/api/v1",
                "port": 8080,
                "consumers": "monitoring-systems",
                "description": "REST API for programmatic access",
                "documentation": "/docs"
            }
        },
        
        "capabilities": [
            "Real-time operation monitoring across datastore services",
            "Performance visualization and trend analysis",
            "Error analysis and alerting",
            "Workflow tracing across services",
            "Interactive filtering and drill-down",
            "Data export (CSV)",
            "Auto-refresh with configurable intervals",
            "Health check and status monitoring"
        ],
        
        "features": {
            "overview_tab": "Service health and operation distribution",
            "performance_tab": "Response times, duration analysis, statistics",
            "operations_tab": "Detailed operation log with search and filtering",
            "workflows_tab": "Cross-service workflow tracing and timelines",
            "errors_tab": "Error analysis by service and status code"
        },
        
        "architecture": {
            "pattern": "Modular by Feature",
            "organization": {
                "data": "Fetching, parsing, validation",
                "metrics": "Calculation and aggregation",
                "visualization": "Tab rendering (Streamlit)",
                "api": "REST endpoints (FastAPI)",
                "utils": "Retry logic, logging, formatting"
            },
            "principles": ["KISS", "DRY", "Testable modules"],
            "testing": "70% unit, 20% integration, 10% functional"
        },
        
        "technologies": {
            "ui_framework": "Streamlit",
            "api_framework": "FastAPI",
            "visualization": "Plotly",
            "data_processing": "Pandas",
            "http_client": "httpx",
            "validation": "Pydantic"
        },
        
        "quality_metrics": {
            "test_coverage": "80%+",
            "test_count": "235+ tests",
            "architecture": "Modular by Feature",
            "code_quality": "Type hints, docstrings, validation"
        },
        
        "dependencies": {
            "providers": [
                {
                    "service": "log-collector",
                    "port": 8104,
                    "purpose": "Provides operation logs and metrics",
                    "endpoints_used": ["GET /logs"],
                    "criticality": "critical",
                    "retry_logic": "3 attempts with exponential backoff"
                }
            ],
            "consumers": [
                {
                    "service": "human-operators",
                    "interface": "web-ui",
                    "purpose": "View dashboard visualizations"
                },
                {
                    "service": "monitoring-systems",
                    "interface": "rest-api",
                    "purpose": "Query health and status"
                }
            ]
        },
        
        "monitored_services": [
            {"service": "doc_store", "port": 5087},
            {"service": "prompt_store", "port": 5110},
            {"service": "external-service-store", "port": 5140},
            {"service": "memory-agent", "port": 5090}
        ],
        
        "configuration": {
            "ports": {
                "ui": 8501,
                "api": 8080
            },
            "environment_variables": [
                "DASHBOARD_LOG_COLLECTOR_URL",
                "DASHBOARD_CACHE_TTL",
                "DASHBOARD_DEFAULT_SERVICES"
            ]
        }
    }


@api_router.get("/endpoints")
async def list_endpoints() -> Dict[str, Any]:
    """
    List all API endpoints.
    
    Returns a JSON list of all available API endpoints.
    
    Returns:
        {
            "service": "data-services-dashboard",
            "version": "1.0.0",
            "base_url": "http://localhost:8080",
            "endpoints": [...]
        }
    """
    endpoints_data = [
        {
            "path": "/health",
            "method": "GET",
            "summary": "Health check",
            "category": "monitoring",
            "description": "Returns health status, uptime, and dependencies"
        },
        {
            "path": "/about-me",
            "method": "GET",
            "summary": "Service descriptor",
            "category": "metadata",
            "description": "Comprehensive service information"
        },
        {
            "path": "/endpoints",
            "method": "GET",
            "summary": "Endpoint listing",
            "category": "metadata",
            "description": "Lists all available API endpoints"
        },
        {
            "path": "/provider-consumer",
            "method": "GET",
            "summary": "Service relationships",
            "category": "metadata",
            "description": "Provider and consumer relationships"
        },
        {
            "path": "/openapi.json",
            "method": "GET",
            "summary": "OpenAPI specification",
            "category": "documentation",
            "description": "OpenAPI 3.0 specification"
        },
        {
            "path": "/docs",
            "method": "GET",
            "summary": "Interactive API documentation",
            "category": "documentation",
            "description": "Swagger UI interactive documentation"
        }
    ]
    
    # Count by category
    categories = {}
    for endpoint in endpoints_data:
        category = endpoint["category"]
        categories[category] = categories.get(category, 0) + 1
    
    return {
        "service": "data-services-dashboard",
        "version": "1.0.0",
        "base_url": "http://localhost:8080",
        "endpoints": endpoints_data,
        "total_endpoints": len(endpoints_data),
        "categories": categories,
        "documentation": {
            "swagger_ui": "http://localhost:8080/docs",
            "redoc": "http://localhost:8080/redoc",
            "openapi_spec": "http://localhost:8080/openapi.json"
        }
    }


@api_router.get("/provider-consumer")
async def provider_consumer_relationships() -> Dict[str, Any]:
    """
    Service relationship matrix.
    
    Returns detailed information about provider and consumer relationships.
    
    Returns:
        {
            "service": "data-services-dashboard",
            "version": "1.0.0",
            "relationships": {...}
        }
    """
    return {
        "service": "data-services-dashboard",
        "version": "1.0.0",
        "type": "dashboard",
        "self_contained": False,
        
        "relationships": {
            "providers": [
                {
                    "service": "log-collector",
                    "relationship": "provider",
                    "criticality": "critical",
                    "purpose": "Provides operation logs and metrics for visualization",
                    "endpoints_used": ["GET /logs"],
                    "data_flow": "Dashboard pulls logs from log-collector via HTTP GET requests",
                    "retry_logic": "3 attempts with exponential backoff (1s, 2s, 4s)",
                    "fallback": "Display cached data or empty state"
                }
            ],
            "consumers": [
                {
                    "service": "human-operators",
                    "relationship": "consumer",
                    "interface": "web-ui",
                    "port": 8501,
                    "purpose": "View real-time dashboard visualizations",
                    "data_flow": "Users access Streamlit web UI in browser"
                },
                {
                    "service": "monitoring-systems",
                    "relationship": "consumer",
                    "interface": "rest-api",
                    "port": 8080,
                    "purpose": "Query dashboard health and status",
                    "endpoints_consumed": [
                        "/health",
                        "/about-me",
                        "/endpoints",
                        "/provider-consumer"
                    ],
                    "data_flow": "Monitoring systems query REST API for health status"
                }
            ],
            "provide_consume": []
        },
        
        "data_flow_summary": """
        Dashboard pulls operation logs from log-collector service via HTTP GET requests
        with retry logic (3 attempts, exponential backoff). Data is cached (5s TTL) and
        transformed into visualizations. Human operators access via Streamlit web UI (8501),
        while monitoring systems query via REST API (8080).
        """,
        
        "network_resilience": {
            "retry_attempts": 3,
            "initial_delay": 1.0,
            "backoff_multiplier": 2.0,
            "connection_pooling": True,
            "timeout": 5.0,
            "fallback_behavior": "Display cached data or empty state"
        }
    }

