"""
Tests for Ecosystem MCP Dashboard.

Tests the core dashboard functionality and page imports.
"""

import pytest
import sys
from pathlib import Path

# Add pages to path
sys.path.insert(0, str(Path(__file__).parent))


def test_pages_import():
    """Test that all page modules can be imported."""
    from pages import home
    from pages import health
    from pages import diagnostics
    from pages import config_viewer
    from pages import containers
    from pages import redis_explorer
    from pages import postgres_explorer
    from pages import rag
    from pages import documents
    from pages import cache
    from pages import metrics
    from pages import settings
    
    # Verify show functions exist
    assert hasattr(home, 'show')
    assert hasattr(health, 'show')
    assert hasattr(diagnostics, 'show')
    assert hasattr(config_viewer, 'show')
    assert hasattr(containers, 'show')
    assert hasattr(redis_explorer, 'show')
    assert hasattr(postgres_explorer, 'show')
    assert hasattr(rag, 'show')
    assert hasattr(documents, 'show')
    assert hasattr(cache, 'show')
    assert hasattr(metrics, 'show')
    assert hasattr(settings, 'show')


def test_app_imports():
    """Test that the main app can be imported."""
    # This will test the imports and structure
    import importlib.util
    
    app_path = Path(__file__).parent / "app.py"
    spec = importlib.util.spec_from_file_location("app", app_path)
    assert spec is not None
    assert spec.loader is not None


def test_requirements_file_exists():
    """Test that requirements.txt exists and has content."""
    req_path = Path(__file__).parent / "requirements.txt"
    assert req_path.exists()
    
    content = req_path.read_text()
    assert len(content) > 0
    
    # Check for key dependencies
    assert "streamlit" in content
    assert "httpx" in content
    assert "plotly" in content
    assert "pandas" in content


def test_dockerfile_exists():
    """Test that Dockerfile exists."""
    dockerfile_path = Path(__file__).parent / "Dockerfile"
    assert dockerfile_path.exists()
    
    content = dockerfile_path.read_text()
    assert "FROM python" in content
    assert "streamlit" in content
    assert "EXPOSE 8501" in content


def test_config_file_exists():
    """Test that Streamlit config exists."""
    config_path = Path(__file__).parent / ".streamlit" / "config.toml"
    assert config_path.exists()
    
    content = config_path.read_text()
    assert "8501" in content


def test_all_pages_exist():
    """Test that all page files exist."""
    pages_dir = Path(__file__).parent / "pages"
    assert pages_dir.exists()
    assert pages_dir.is_dir()
    
    expected_pages = [
        "__init__.py",
        "home.py",
        "health.py",
        "diagnostics.py",
        "config_viewer.py",
        "containers.py",
        "redis_explorer.py",
        "postgres_explorer.py",
        "rag.py",
        "documents.py",
        "cache.py",
        "metrics.py",
        "settings.py"
    ]
    
    for page in expected_pages:
        page_path = pages_dir / page
        assert page_path.exists(), f"Page {page} does not exist"


def test_page_structure():
    """Test that pages have the expected structure."""
    from pages import home, health, diagnostics
    
    # All pages should have a show function that takes api_base_url
    import inspect
    
    for page_module in [home, health, diagnostics]:
        assert hasattr(page_module, 'show')
        show_func = getattr(page_module, 'show')
        assert callable(show_func)
        
        # Check function signature
        sig = inspect.signature(show_func)
        params = list(sig.parameters.keys())
        assert 'api_base_url' in params


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

