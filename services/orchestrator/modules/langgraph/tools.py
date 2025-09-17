"""Service tool wrappers for LangGraph integration.

This module provides LangGraph tool wrappers for all orchestrator services,
enabling them to be used as tools within LangGraph workflows.
"""

from typing import Dict, Any, List, Optional, Type
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from services.shared.utilities import get_service_client
from services.shared.constants_new import ServiceNames


class ServiceTool(BaseTool):
    """Base class for service-based LangGraph tools."""

    service_name: str
    service_client: Any

    def __init__(self, service_name: str, service_client: Any):
        super().__init__()
        self.service_name = service_name
        self.service_client = service_client

    @property
    def name(self) -> str:
        return f"{self.service_name}_{self.__class__.__name__.lower()}"

    @property
    def description(self) -> str:
        return f"Tool for interacting with {self.service_name} service"


# Prompt Store Tools
@tool
def create_prompt_tool(name: str, category: str, content: str, variables: List[str]) -> Dict[str, Any]:
    """Create a new prompt in the Prompt Store."""
    service_client = get_service_client()

    prompt_data = {
        "name": name,
        "category": category,
        "content": content,
        "variables": variables
    }

    try:
        result = service_client.post_json("prompt-store/api/v1/prompts", prompt_data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_prompt_tool(name: str, category: str) -> Dict[str, Any]:
    """Retrieve a prompt from the Prompt Store."""
    service_client = get_service_client()

    try:
        result = service_client.get_json(f"prompt-store/api/v1/prompts/search/{category}/{name}")
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_optimal_prompt_tool(task_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Get the optimal prompt for a task from the Prompt Store."""
    service_client = get_service_client()

    try:
        result = service_client.post_json("prompt-store/api/v1/orchestration/prompts/select", {
            "task_type": task_type,
            "context": context
        })
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Document Store Tools
@tool
def store_document_tool(content: str, metadata: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Store a document in the Document Store."""
    service_client = get_service_client()

    doc_data = {
        "content": content,
        "metadata": metadata,
        "source": source
    }

    try:
        result = service_client.post_json("doc-store/api/v1/documents", doc_data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def search_documents_tool(query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Search documents in the Document Store."""
    service_client = get_service_client()

    search_params = {"q": query}
    if filters:
        search_params.update(filters)

    try:
        result = service_client.get_json("doc-store/api/v1/search", params=search_params)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_document_tool(doc_id: str) -> Dict[str, Any]:
    """Retrieve a specific document from the Document Store."""
    service_client = get_service_client()

    try:
        result = service_client.get_json(f"doc-store/api/v1/documents/{doc_id}")
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Code Analyzer Tools
@tool
def analyze_codebase_tool(repo_url: str, languages: List[str]) -> Dict[str, Any]:
    """Analyze a codebase using the Code Analyzer service."""
    service_client = get_service_client()

    analysis_data = {
        "repo_url": repo_url,
        "languages": languages
    }

    try:
        result = service_client.post_json("code-analyzer/analyze", analysis_data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def extract_functions_tool(code: str) -> Dict[str, Any]:
    """Extract functions from code using the Code Analyzer."""
    service_client = get_service_client()

    try:
        result = service_client.post_json("code-analyzer/analyze", {"code": code})
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Summarizer Hub Tools
@tool
def summarize_document_tool(content: str, style: str = "concise") -> Dict[str, Any]:
    """Summarize a document using the Summarizer Hub."""
    service_client = get_service_client()

    summary_data = {
        "content": content,
        "format": "markdown",
        "max_length": 500
    }

    try:
        result = service_client.post_json("summarizer-hub/summarize", summary_data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def extract_key_concepts_tool(content: str) -> Dict[str, Any]:
    """Extract key concepts from content using the Summarizer Hub."""
    service_client = get_service_client()

    try:
        result = service_client.post_json("summarizer-hub/summarize", {"content": content})
        return {"success": True, "data": result.get("key_concepts", [])}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Interpreter Tools
@tool
def interpret_query_tool(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Interpret a natural language query using the Interpreter service."""
    service_client = get_service_client()

    interpret_data = {
        "query": query,
        "context": context or {}
    }

    try:
        result = service_client.post_json("interpreter/interpret", interpret_data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def execute_workflow_tool(query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute a workflow from a natural language query."""
    service_client = get_service_client()

    execute_data = {
        "query": query,
        "user_id": user_id
    }

    try:
        result = service_client.post_json("interpreter/execute", execute_data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Analysis Service Tools
@tool
def analyze_document_consistency_tool(doc_ids: List[str], criteria: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze document consistency using the Analysis Service."""
    service_client = get_service_client()

    analysis_data = {
        "targets": doc_ids,
        "analysis_type": "consistency",
        "criteria": criteria
    }

    try:
        result = service_client.post_json("analysis-service/analyze", analysis_data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def generate_quality_report_tool(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a quality report from analysis results."""
    service_client = get_service_client()

    try:
        result = service_client.post_json("analysis-service/reports/generate", {
            "type": "quality_summary",
            "data": analysis_results
        })
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Notification Service Tools
@tool
def send_notification_tool(message: str, channels: List[str], priority: str) -> Dict[str, Any]:
    """Send a notification using the Notification Service."""
    service_client = get_service_client()

    notification_data = {
        "message": message,
        "channels": channels,
        "priority": priority
    }

    try:
        result = service_client.post_json("notification-service/notify", notification_data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def create_notification_template_tool(name: str, template: str) -> Dict[str, Any]:
    """Create a notification template."""
    service_client = get_service_client()

    template_data = {
        "name": name,
        "template": template
    }

    try:
        result = service_client.post_json("notification-service/templates", template_data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Source Agent Tools
@tool
def ingest_github_repo_tool(repo_url: str, filters: Dict[str, Any]) -> Dict[str, Any]:
    """Ingest content from a GitHub repository."""
    service_client = get_service_client()

    ingest_data = {
        "source_url": repo_url,
        "source_type": "github",
        "filters": filters
    }

    try:
        result = service_client.post_json("source-agent/docs/fetch", ingest_data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def ingest_jira_issues_tool(project_key: str, query: str) -> Dict[str, Any]:
    """Ingest Jira issues and tickets."""
    service_client = get_service_client()

    ingest_data = {
        "source_url": f"jira/{project_key}",
        "source_type": "jira",
        "query": query
    }

    try:
        result = service_client.post_json("source-agent/docs/fetch", ingest_data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Secure Analyzer Tools
@tool
def analyze_content_security_tool(content: str) -> Dict[str, Any]:
    """Analyze content for security risks."""
    service_client = get_service_client()

    analysis_data = {
        "content": content
    }

    try:
        result = service_client.post_json("secure-analyzer/detect", analysis_data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def sanitize_content_tool(content: str, policies: List[str]) -> Dict[str, Any]:
    """Sanitize content based on security policies."""
    service_client = get_service_client()

    sanitize_data = {
        "content": content,
        "policies": policies
    }

    try:
        result = service_client.post_json("secure-analyzer/sanitize", sanitize_data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def create_service_tools(service_name: str, service_client: Any) -> Dict[str, BaseTool]:
    """Create LangGraph tools for a specific service."""

    tools = {}

    # Map services to their tool functions
    service_tool_map = {
        "prompt_store": [
            create_prompt_tool,
            get_prompt_tool,
            get_optimal_prompt_tool
        ],
        "document_store": [
            store_document_tool,
            search_documents_tool,
            get_document_tool
        ],
        "code_analyzer": [
            analyze_codebase_tool,
            extract_functions_tool
        ],
        "summarizer_hub": [
            summarize_document_tool,
            extract_key_concepts_tool
        ],
        "interpreter": [
            interpret_query_tool,
            execute_workflow_tool
        ],
        "analysis_service": [
            analyze_document_consistency_tool,
            generate_quality_report_tool
        ],
        "notification_service": [
            send_notification_tool,
            create_notification_template_tool
        ],
        "source_agent": [
            ingest_github_repo_tool,
            ingest_jira_issues_tool
        ],
        "secure_analyzer": [
            analyze_content_security_tool,
            sanitize_content_tool
        ]
    }

    if service_name in service_tool_map:
        for tool_func in service_tool_map[service_name]:
            tools[tool_func.name] = tool_func

    return tools
