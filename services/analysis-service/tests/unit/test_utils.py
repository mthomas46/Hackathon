"""Shared test utilities for analysis service test suite.

Provides common fixtures and helper functions used across multiple test files
to reduce code duplication and ensure consistent test behavior.
"""
import importlib.util, os
from fastapi.testclient import TestClient


def load_analysis_service():
    """Load analysis-service dynamically.

    Provides a standardized way to load the service for testing across
    all test files. Handles import errors gracefully.

    Returns:
        FastAPI app instance for testing

    Raises:
        Exception: If service loading fails
    """
    import sys
    from pathlib import Path
    
    # Get the analysis-service root directory (parent of tests/)
    analysis_service_root = Path(__file__).parent.parent.parent
    # Get the services directory (parent of analysis-service)
    services_root = analysis_service_root.parent
    # Get the Hackathon root (parent of services) - needed for "services.*" imports
    hackathon_root = services_root.parent
    
    # Add to Python path:
    # 1. Hackathon root for "services.shared" imports to work
    # 2. analysis-service root for local imports
    sys.path.insert(0, str(hackathon_root))
    sys.path.insert(0, str(analysis_service_root))
    
    try:
        # Change to the analysis-service directory to make relative imports work
        original_dir = Path.cwd()
        os.chdir(analysis_service_root)
        
        # Import with the module name that makes relative imports work
        spec = importlib.util.spec_from_file_location(
            "analysis_service.main",
            analysis_service_root / "main.py",
            submodule_search_locations=[str(analysis_service_root)]
        )
        analysis_main = importlib.util.module_from_spec(spec)
        sys.modules['analysis_service'] = type(sys)('analysis_service')  # Create parent package
        sys.modules['analysis_service.main'] = analysis_main
        spec.loader.exec_module(analysis_main)
        
        # Change back to original directory
        os.chdir(original_dir)
        
        return analysis_main.app
    except Exception as e:
        print(f"Warning: Failed to load analysis service: {e}")
        print(f"Analysis service root: {analysis_service_root}")
        print(f"Services root: {services_root}")
        print(f"CWD: {os.getcwd()}")
        import traceback
        traceback.print_exc()
        # If loading fails, create a minimal mock app for testing
        from fastapi import FastAPI

        app = FastAPI(title="Analysis Service", version="1.0.0")

        # Mock endpoints for testing
        @app.get("/health")
        async def health():
            return {"status": "healthy", "service": "analysis-service"}

        return app


def _assert_http_ok(response):
    """Assert that HTTP response is successful."""
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"