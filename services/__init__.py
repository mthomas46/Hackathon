"""Service module imports for the documentation ecosystem.

This module provides convenient access to all services, handling the
hyphenated directory names by creating dotted module names.
"""

import sys
import importlib.util
import os
from pathlib import Path

# Service directory mapping
SERVICE_MAPPING = {
    'source_agent': 'source-agent',
    'doc_store': 'doc-store',
    'analysis_service': 'analysis-service',
    'code_analyzer': 'code-analyzer',
    'secure_analyzer': 'secure-analyzer',
    'summarizer_hub': 'summarizer-hub',
    'prompt_store': 'prompt-store',
    'memory_agent': 'memory-agent',
    'discovery_agent': 'discovery-agent',
    'orchestrator': 'orchestrator',
    'frontend': 'frontend',
    'interpreter': 'interpreter',
    'log_collector': 'log-collector',
    'notification_service': 'notification-service',
    'bedrock_proxy': 'bedrock-proxy',
}

# Dynamic module creation
def _load_service_module(service_name: str):
    """Load a service module dynamically."""
    if service_name in SERVICE_MAPPING:
        actual_dir = SERVICE_MAPPING[service_name]
        service_dir = Path(__file__).parent / actual_dir
        main_file = service_dir / 'main.py'

        if main_file.exists():
            try:
                spec = importlib.util.spec_from_file_location(
                    f'services.{service_name}',
                    str(main_file)
                )
                module = importlib.util.module_from_spec(spec)
                sys.modules[f'services.{service_name}'] = module
                spec.loader.exec_module(module)
                return module
            except Exception as e:
                print(f"Warning: Could not load {service_name}: {e}")
                return None
    return None

# Load all services
for service_name in SERVICE_MAPPING.keys():
    _load_service_module(service_name)

