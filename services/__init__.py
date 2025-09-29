"""Services package for Hackathon Platform."""

# Import mapping for services with dashes in directory names
import importlib

# Map service names to their actual module paths
_service_mappings = {
    "doc_store": "doc_store",
    "analysis_service": "analysis-service",
    "architecture_digitizer": "architecture-digitizer",
    "bedrock_proxy": "bedrock-proxy",
    "code-analyzer": "code-analyzer",
    "discovery_agent": "discovery-agent",
    "github_mcp": "github-mcp",
    "log_collector": "log-collector",
    "memory_agent": "memory-agent",
    "notification-service": "notification-service",
    "prompt_store": "prompt-store",
    "project_simulation": "project-simulation",
    "secure-analyzer": "secure-analyzer",
    "source-agent": "source-agent",
    "summarizer-hub": "summarizer-hub",
}


def __getattr__(name):
    """Dynamic import for services with special naming."""
    if name in _service_mappings:
        actual_name = _service_mappings[name]
        try:
            return importlib.import_module(f".{actual_name}", package=__name__)
        except ImportError:
            # Fallback to direct import if the module structure allows
            pass
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
