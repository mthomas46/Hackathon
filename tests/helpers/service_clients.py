"""Shared service client helpers for FastAPI TestClient spins.

Consolidates lazy loading and caching of service clients.
"""

from typing import Dict, Optional, Tuple
from fastapi.testclient import TestClient
import importlib.util
import sys
from pathlib import Path


SERVICE_REGISTRY: Dict[str, Tuple[str, str]] = {
    "orchestrator": ("services.orchestrator.main", "app"),
    "source_agent": ("services.source-agent.main", "app"),
    "analysis_service": ("services.analysis-service.main", "app"),
    "doc_store": ("services.doc-store.main", "app"),
    "frontend": ("services.frontend.main", "app"),
    "memory_agent": ("services.memory-agent.main", "app"),
    "discovery_agent": ("services.discovery-agent.main", "app"),
    "secure_analyzer": ("services.secure-analyzer.main", "app"),
    "summarizer_hub": ("services.summarizer-hub.main", "app"),
    "prompt_store": ("services.prompt-store.main", "app"),
    "interpreter": ("services.interpreter.main", "app"),
    "code_analyzer": ("services.code-analyzer.main", "app"),
    "bedrock_proxy": ("services.bedrock-proxy.main", "app"),
    "notification_service": ("services.notification-service.main", "app"),
    "log_collector": ("services.log-collector.main", "app"),
}


_SERVICE_CACHE: Dict[str, Optional[TestClient]] = {}


def get_service_client(name: str) -> Optional[TestClient]:
    if name not in _SERVICE_CACHE:
        try:
            module_path, attr = SERVICE_REGISTRY[name]
            # Convert module path to file path
            file_path = module_path.replace('.', '/') + '.py'
            project_root = Path(__file__).parent.parent.parent
            full_path = project_root / file_path

            # Load the module directly from file
            spec = importlib.util.spec_from_file_location(module_path, full_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_path] = module
                spec.loader.exec_module(module)
                app = getattr(module, attr)
                _SERVICE_CACHE[name] = TestClient(app)
            else:
                raise ImportError(f"Could not load module {module_path}")
        except Exception as e:
            print(f"Warning: Could not import service {name}: {e}")
            _SERVICE_CACHE[name] = None
    return _SERVICE_CACHE[name]


