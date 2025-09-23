"""Pytest configuration and fixtures for Data Services Dashboard testing."""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, Mock

import pytest

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import client classes (mock them if they don't exist)
try:
    from services.clients.memory_client import MemoryAgentClient
except ImportError:
    MemoryAgentClient = Mock

try:
    from services.clients.prompt_client import PromptStoreClient
except ImportError:
    PromptStoreClient = Mock

try:
    from services.clients.document_client import DocumentStoreClient
except ImportError:
    DocumentStoreClient = Mock


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_memory_client():
    """Create a mock Memory Agent client."""
    client = Mock(spec=MemoryAgentClient)

    # Store for created memory items to simulate state
    stored_memory_items = []

    async def mock_put_memory_item(**kwargs):
        memory_item = {
            "type": kwargs.get("type") or kwargs.get("item_type"),
            "key": kwargs.get("key"),
            "summary": kwargs.get("summary"),
            "data": kwargs.get("data", {}),
        }
        stored_memory_items.append(memory_item)
        return {"success": True, "message": "Memory item stored successfully"}

    async def mock_list_memory_items(type_filter=None, key_filter=None, limit=50, offset=0):
        items = stored_memory_items
        if type_filter:
            items = [item for item in items if item["type"] == type_filter]
        return {"success": True, "items": items[offset : offset + limit]}

    client.health_check = AsyncMock(return_value={"status": "healthy", "service": "memory-agent", "version": "1.0.0"})
    client.list_memory_items = AsyncMock(side_effect=mock_list_memory_items)
    client.put_memory_item = AsyncMock(side_effect=mock_put_memory_item)
    client.search_memory_items = AsyncMock(return_value={"success": True, "items": []})
    return client


@pytest.fixture
def mock_prompt_client():
    """Create a mock Prompt Store client."""
    client = Mock(spec=PromptStoreClient)

    # Store for created prompts to simulate state
    created_prompts = {}

    async def mock_create_prompt(name, category, content, **kwargs):
        prompt_id = f"prompt_{len(created_prompts) + 1}"
        created_prompts[prompt_id] = {"id": prompt_id, "name": name, "category": category, "content": content, **kwargs}
        return {"success": True, "id": prompt_id}

    async def mock_get_prompt(prompt_id):
        if prompt_id in created_prompts:
            return {"success": True, "prompt": created_prompts[prompt_id]}
        else:
            # Return default test prompt
            return {
                "success": True,
                "prompt": {"id": "test_prompt_1", "name": "Test Prompt", "content": "You are a helpful assistant."},
            }

    client.list_prompts = AsyncMock(
        return_value={
            "success": True,
            "prompts": [
                {
                    "id": "test_prompt_1",
                    "name": "Test Prompt",
                    "category": "chat",
                    "content": "You are a helpful assistant.",
                    "version": 1,
                    "variables": [],
                    "tags": ["test"],
                }
            ],
        }
    )
    client.create_prompt = AsyncMock(side_effect=mock_create_prompt)
    client.get_prompt = AsyncMock(side_effect=mock_get_prompt)
    client.update_prompt = AsyncMock(return_value={"success": True, "message": "Prompt updated successfully"})
    client.delete_prompt = AsyncMock(return_value={"success": True, "message": "Prompt deleted successfully"})
    return client


@pytest.fixture
def mock_document_client():
    """Create a mock Document Store client."""
    client = Mock(spec=DocumentStoreClient)

    # Store for created documents to simulate state
    created_documents = {}

    async def mock_create_document(request_data):
        doc_id = f"doc_{len(created_documents) + 1}"
        created_documents[doc_id] = {"id": doc_id, **request_data}
        return {"success": True, "id": doc_id}

    async def mock_get_document(document_id):
        if document_id in created_documents:
            return created_documents[document_id]
        else:
            # Return default test document
            return {"id": "test_doc_1", "content": "Test document content", "content_type": "text"}

    client.list_documents = AsyncMock(
        return_value={
            "items": [
                {
                    "id": "test_doc_1",
                    "content": "Test document content",
                    "content_type": "text",
                    "created_at": "2024-01-01T00:00:00Z",
                }
            ],
            "total": 1,
        }
    )
    client.create_document = AsyncMock(side_effect=mock_create_document)
    client.get_document = AsyncMock(side_effect=mock_get_document)
    client.search_documents = AsyncMock(return_value={"success": True, "results": []})
    return client


@pytest.fixture
def sample_memory_items():
    """Sample memory items for testing."""
    return [
        {
            "type": "operation",
            "key": "op_123",
            "summary": "Data import operation completed",
            "data": {"operation_type": "import", "records_processed": 1500, "success_rate": 0.98},
        },
        {
            "type": "llm_summary",
            "key": "llm_session_456",
            "summary": "LLM processed user query about Python functions",
            "data": {"session_id": "session_456", "tokens_used": 245, "processing_time": 1.2},
        },
        {
            "type": "doc_summary",
            "key": "doc_analysis_789",
            "summary": "Analyzed API documentation",
            "data": {"document_id": "api_docs.pdf", "issues_found": 3, "quality_score": 8.5},
        },
    ]


@pytest.fixture
def sample_prompts():
    """Sample prompts for testing."""
    return [
        {
            "id": "prompt_1",
            "name": "Customer Support Assistant",
            "category": "chat",
            "content": "You are a helpful customer support assistant for {{company_name}}. Be polite, professional, and solve customer issues efficiently.",
            "description": "General customer support prompt",
            "variables": ["company_name"],
            "tags": ["support", "customer", "chat"],
            "version": 2,
            "is_active": True,
        },
        {
            "id": "prompt_2",
            "name": "Code Reviewer",
            "category": "analysis",
            "content": "Review the following {{language}} code for best practices, security issues, and performance optimizations. Provide specific recommendations.",
            "description": "Code review and analysis prompt",
            "variables": ["language"],
            "tags": ["code", "review", "security"],
            "version": 1,
            "is_active": True,
        },
    ]


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        {
            "id": "doc_1",
            "content": "# API Documentation\n\nThis document describes the REST API endpoints.\n\n## Authentication\n\nUse Bearer tokens for authentication.",
            "content_type": "markdown",
            "metadata": {"author": "Dev Team", "version": "1.0", "tags": ["api", "documentation"]},
            "created_at": "2024-01-01T10:00:00Z",
        },
        {
            "id": "doc_2",
            "content": "function processData(data) {\n    return data.map(item => item.value * 2);\n}",
            "content_type": "javascript",
            "metadata": {"language": "javascript", "purpose": "data processing"},
            "created_at": "2024-01-02T14:30:00Z",
        },
    ]


@pytest.fixture
def mock_session_state():
    """Mock Streamlit session state."""
    return {"memory_client": Mock(), "prompt_client": Mock(), "document_client": Mock()}


@pytest.fixture(autouse=True)
def mock_streamlit(monkeypatch):
    """Mock Streamlit functions to avoid UI dependencies in tests."""
    mock_functions = [
        "markdown",
        "header",
        "subheader",
        "text",
        "code",
        "json",
        "success",
        "error",
        "warning",
        "info",
        "button",
        "checkbox",
        "text_input",
        "text_area",
        "selectbox",
        "multiselect",
        "slider",
        "columns",
        "tabs",
        "sidebar",
        "expander",
        "dataframe",
        "table",
        "metric",
        "progress",
        "spinner",
        "empty",
        "container",
        "form",
        "form_submit_button",
        "file_uploader",
        "download_button",
        "session_state",
        "set_page_config",
        "sidebar",
        "cache_data",
        "cache_resource",
    ]

    for func_name in mock_functions:
        monkeypatch.setattr(f"streamlit.{func_name}", Mock(), raising=False)

    # Mock streamlit.session_state as a dict-like object
    mock_session_state = Mock()
    mock_session_state.__getitem__ = Mock(return_value=None)
    mock_session_state.__setitem__ = Mock()
    mock_session_state.__contains__ = Mock(return_value=False)
    monkeypatch.setattr("streamlit.session_state", mock_session_state, raising=False)


@pytest.fixture
def test_config():
    """Test configuration data."""
    return {
        "environment": "test",
        "debug": True,
        "service_endpoints": {
            "memory_agent": "http://localhost:5090",
            "prompt_store": "http://localhost:5110",
            "document_store": "http://localhost:5087",
        },
        "performance": {"max_concurrent_requests": 5, "request_timeout": 30},
    }
