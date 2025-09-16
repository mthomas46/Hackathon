"""Services package for Hackathon Platform."""

# Import mapping for services with dashes in directory names
import importlib
import sys
from pathlib import Path

# Map service names to their actual module paths
_service_mappings = {
    'doc_store': 'doc_store',
    'analysis_service': 'analysis-service',
    'architecture_digitizer': 'architecture-digitizer',
    'bedrock_proxy': 'bedrock-proxy',
    'code_analyzer': 'code-analyzer',
    'discovery_agent': 'discovery-agent',
    'github_mcp': 'github-mcp',
    'log_collector': 'log-collector',
    'memory_agent': 'memory-agent',
    'notification_service': 'notification-service',
    'prompt_store': 'prompt-store',
    'secure_analyzer': 'secure-analyzer',
    'source_agent': 'source-agent',
    'summarizer_hub': 'summarizer-hub',
}

def __getattr__(name):
    """Dynamic import for services with special naming."""
    if name in _service_mappings:
        actual_name = _service_mappings[name]
        try:
            return importlib.import_module(f'.{actual_name}', package=__name__)
        except ImportError:
            # Fallback to direct import if the module structure allows
            pass
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")