"""Data Services Dashboard - Unified Interface for Memory Agent, Prompt Store, and Document Store.

This dashboard provides a comprehensive interface for browsing, managing, and interacting with
three key data services in the LLM Documentation Ecosystem: Memory Agent, Prompt Store, and Document Store.

Features:
- Memory Agent: View conversation memory, manage operational context, search memory items
- Prompt Store: Browse prompts by category, create/edit prompts, manage versions and tags
- Document Store: Upload/manage documents, search with filters, view analytics and relationships
- Cross-service integration: Link documents to prompts, memory context to prompts
- Advanced search and filtering across all services
- Bulk operations and export/import capabilities
- Real-time updates and health monitoring

Technology Stack (inspired by simulation-dashboard):
- Streamlit for web interface
- httpx for async HTTP clients
- Plotly for data visualizations
- Domain-driven architecture
- Real-time updates and caching
"""

import streamlit as st
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
import logging

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Import local modules
from infrastructure.config.config import get_config, DashboardSettings
from infrastructure.logging.logger import setup_logging, get_logger
from services.clients.memory_client import MemoryAgentClient
from services.clients.prompt_client import PromptStoreClient
from services.clients.document_client import DocumentStoreClient
from components.sidebar import render_sidebar
from components.header import render_header
from components.footer import render_footer
from pages.overview import render_overview_page
from pages.memory_browser import render_memory_browser_page
from pages.prompt_browser import render_prompt_browser_page
from pages.document_browser import render_document_browser_page
from pages.cross_service import render_cross_service_page
from pages.search import render_search_page
from pages.bulk_operations import render_bulk_operations_page

# Configure page
st.set_page_config(
    page_title="Data Services Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-org/data-services-dashboard',
        'Report a bug': 'https://github.com/your-org/data-services-dashboard/issues',
        'About': '''
        ## Data Services Dashboard

        A unified interface for managing Memory Agent, Prompt Store,
        and Document Store services in the LLM Documentation Ecosystem.

        **Version:** 1.0.0
        **Environment:** Development
        '''
    }
)

# Load configuration
config: DashboardSettings = get_config()

# Setup logging
setup_logging(config.logging)
logger = get_logger(__name__)

# Initialize service clients
@st.cache_resource
def get_memory_client() -> MemoryAgentClient:
    """Get cached memory agent client instance."""
    return MemoryAgentClient(config.memory_service.base_url)

@st.cache_resource
def get_prompt_client() -> PromptStoreClient:
    """Get cached prompt store client instance."""
    return PromptStoreClient(config.prompt_service.base_url)

@st.cache_resource
def get_document_client() -> DocumentStoreClient:
    """Get cached document store client instance."""
    return DocumentStoreClient(config.document_service.base_url)

# Initialize session state
def initialize_session_state():
    """Initialize Streamlit session state."""
    if 'memory_client' not in st.session_state:
        st.session_state.memory_client = get_memory_client()

    if 'prompt_client' not in st.session_state:
        st.session_state.prompt_client = get_prompt_client()

    if 'document_client' not in st.session_state:
        st.session_state.document_client = get_document_client()

    if 'current_page' not in st.session_state:
        st.session_state.current_page = "overview"

    if 'selected_service' not in st.session_state:
        st.session_state.selected_service = None

    if 'theme' not in st.session_state:
        st.session_state.theme = config.dashboard.theme

    if 'search_cache' not in st.session_state:
        st.session_state.search_cache = {}

    if 'bulk_operations' not in st.session_state:
        st.session_state.bulk_operations = []

# Page routing
PAGES = {
    "overview": {
        "name": "🏠 Overview",
        "function": render_overview_page,
        "description": "Dashboard overview with service health and key metrics"
    },
    "memory_browser": {
        "name": "🧠 Memory Agent",
        "function": render_memory_browser_page,
        "description": "Browse and manage conversation memory and operational context"
    },
    "prompt_browser": {
        "name": "📝 Prompt Store",
        "function": render_prompt_browser_page,
        "description": "Browse, create, and manage prompts by category and tags"
    },
    "document_browser": {
        "name": "📄 Document Store",
        "function": render_document_browser_page,
        "description": "Upload, manage, and search documents with advanced filters"
    },
    "cross_service": {
        "name": "🔗 Cross-Service",
        "function": render_cross_service_page,
        "description": "Link documents to prompts, memory to prompts, and view relationships"
    },
    "search": {
        "name": "🔍 Advanced Search",
        "function": render_search_page,
        "description": "Unified search across all services with advanced filters"
    },
    "bulk_operations": {
        "name": "⚡ Bulk Operations",
        "function": render_bulk_operations_page,
        "description": "Bulk import/export, batch operations, and data management"
    }
}

def render_page_content(page_key: str):
    """Render the content for the selected page."""
    try:
        page_info = PAGES.get(page_key)
        if page_info:
            page_info["function"]()
        else:
            st.error(f"Page '{page_key}' not found")
            render_overview_page()
    except Exception as e:
        logger.error(f"Error rendering page {page_key}: {str(e)}")
        st.error(f"Error loading page: {str(e)}")
        with st.expander("Error Details"):
            st.code(str(e))

def main():
    """Main application entry point."""
    try:
        # Initialize session state
        initialize_session_state()

        # Render header
        render_header()

        # Create two-column layout
        col1, col2 = st.columns([1, 4])

        with col1:
            # Render sidebar navigation
            selected_page = render_sidebar(PAGES)

        with col2:
            # Render main content area
            st.markdown("---")

            # Page title and description
            if selected_page in PAGES:
                page_info = PAGES[selected_page]
                st.title(page_info["name"])
                st.markdown(f"*{page_info['description']}*")
                st.markdown("---")

            # Render page content
            render_page_content(selected_page)

        # Render footer
        st.markdown("---")
        render_footer()

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An unexpected error occurred. Please refresh the page.")
        with st.expander("Error Details"):
            st.code(str(e))

        # Show basic navigation as fallback
        st.sidebar.title("Navigation")
        if st.sidebar.button("🏠 Overview", key="fallback_overview"):
            st.rerun()

if __name__ == "__main__":
    # Log startup
    logger.info(
        "Starting Data Services Dashboard Service",
        version=config.service_version,
        environment=config.environment,
        port=config.port
    )

    # Print startup information
    print("🚀 Starting Data Services Dashboard Service...")
    print("=" * 60)
    print(f"📊 Service: {config.service_name} v{config.service_version}")
    print(f"🌐 Dashboard: http://localhost:{config.port}")
    print(f"🧠 Memory Agent: {config.memory_service.base_url}")
    print(f"📝 Prompt Store: {config.prompt_service.base_url}")
    print(f"📄 Document Store: {config.document_service.base_url}")
    print(f"⚙️  Environment: {config.environment}")
    print(f"🔧 Debug Mode: {config.debug}")
    print("\n📋 Available Pages:")
    for key, page in PAGES.items():
        print(f"  • {page['name']}: {page['description']}")
    print("\n✨ Features:")
    print("  🧠 Memory Agent Browser - View conversation memory and operational context")
    print("  📝 Prompt Store Browser - Create, edit, and manage prompts")
    print("  📄 Document Store Browser - Upload, search, and manage documents")
    print("  🔗 Cross-Service Integration - Link data across services")
    print("  🔍 Advanced Search - Unified search with filters")
    print("  ⚡ Bulk Operations - Import/export and batch operations")
    print("  📊 Real-Time Analytics - Live service monitoring")
    print("\n🏗️ Built with:")
    print("  🐍 Python & Streamlit")
    print("  🔄 Async HTTP Clients")
    print("  📊 Interactive Charts & Visualizations")
    print("  🏗️ Domain-Driven Architecture")

    # Run the application
    main()
