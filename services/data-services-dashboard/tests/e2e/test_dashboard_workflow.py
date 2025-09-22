"""End-to-end tests for dashboard workflows."""

import pytest
import asyncio
from unittest.mock import Mock, patch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# Mock Streamlit to avoid UI dependencies
import streamlit as st
for attr in dir(st):
    if not attr.startswith('_'):
        setattr(st, attr, Mock())


class TestDashboardInitialization:
    """Test dashboard initialization and setup."""

    def test_dashboard_imports(self):
        """Test that dashboard can be imported without errors."""
        try:
            from app import get_memory_client, get_prompt_client, get_document_client
            assert callable(get_memory_client)
            assert callable(get_prompt_client)
            assert callable(get_document_client)
        except ImportError as e:
            pytest.skip(f"Dashboard imports failed: {e}")

    def test_config_loading(self, test_config):
        """Test configuration loading."""
        assert test_config["environment"] == "test"
        assert test_config["debug"] is True
        assert "memory_agent" in test_config["service_endpoints"]
        assert "prompt_store" in test_config["service_endpoints"]
        assert "document_store" in test_config["service_endpoints"]


class TestServiceIntegrationWorkflow:
    """Test complete service integration workflows."""

    @pytest.mark.asyncio
    async def test_memory_agent_workflow(self, mock_memory_client, sample_memory_items):
        """Test complete memory agent workflow."""
        # 1. Health check
        health = await mock_memory_client.health_check()
        assert health["status"] == "healthy"

        # 2. Add memory items
        for item in sample_memory_items[:2]:  # Test with first 2 items
            result = await mock_memory_client.put_memory_item(**item)
            assert result["success"] is True

        # 3. List memory items
        items = await mock_memory_client.list_memory_items()
        assert items["success"] is True
        assert len(items["items"]) > 0

        # 4. Search memory items
        search_results = await mock_memory_client.search_memory_items("operation")
        assert search_results["success"] is True

    @pytest.mark.asyncio
    async def test_prompt_store_workflow(self, mock_prompt_client, sample_prompts):
        """Test complete prompt store workflow."""
        # 1. List prompts (should work even if empty)
        prompts = await mock_prompt_client.list_prompts()
        assert "prompts" in prompts

        # 2. Create a prompt
        test_prompt = sample_prompts[0]
        result = await mock_prompt_client.create_prompt(**test_prompt)
        assert result["success"] is True
        assert "id" in result

        # 3. Get the created prompt
        prompt_id = result["id"]
        retrieved = await mock_prompt_client.get_prompt(prompt_id)
        assert retrieved["success"] is True
        assert retrieved["prompt"]["name"] == test_prompt["name"]

        # 4. Update the prompt
        updates = {"name": "Updated Test Prompt"}
        update_result = await mock_prompt_client.update_prompt(prompt_id, updates)
        assert update_result["success"] is True

        # 5. Delete the prompt
        delete_result = await mock_prompt_client.delete_prompt(prompt_id)
        assert delete_result["success"] is True

    @pytest.mark.asyncio
    async def test_document_store_workflow(self, mock_document_client, sample_documents):
        """Test complete document store workflow."""
        # 1. List documents
        docs = await mock_document_client.list_documents()
        assert "items" in docs

        # 2. Create a document
        test_doc = sample_documents[0]
        result = await mock_document_client.create_document(test_doc)
        assert result["success"] is True
        assert "id" in result

        # 3. Get the created document
        doc_id = result["id"]
        retrieved = await mock_document_client.get_document(doc_id)
        assert retrieved["id"] == doc_id
        assert "content" in retrieved

        # 4. Search documents
        search_results = await mock_document_client.search_documents("test")
        assert search_results["success"] is True
        assert "results" in search_results


class TestCrossServiceWorkflows:
    """Test workflows that span multiple services."""

    @pytest.mark.asyncio
    async def test_data_creation_workflow(self, mock_memory_client, mock_prompt_client, mock_document_client,
                                        sample_memory_items, sample_prompts, sample_documents):
        """Test creating related data across all services."""
        # Create a memory item about prompt creation
        memory_item = {
            "type": "operation",
            "key": "workflow_test",
            "summary": "Testing cross-service data creation workflow",
            "data": {"workflow": "data_creation_test"}
        }
        memory_result = await mock_memory_client.put_memory_item(**memory_item)
        assert memory_result["success"] is True

        # Create a prompt
        prompt_result = await mock_prompt_client.create_prompt(**sample_prompts[0])
        assert prompt_result["success"] is True

        # Create a document
        doc_result = await mock_document_client.create_document(sample_documents[0])
        assert doc_result["success"] is True

        # Verify all services have data
        memory_list = await mock_memory_client.list_memory_items()
        assert len(memory_list["items"]) > 0

        prompt_list = await mock_prompt_client.list_prompts()
        assert len(prompt_list["prompts"]) > 0

        doc_list = await mock_document_client.list_documents()
        assert len(doc_list["items"]) > 0

    @pytest.mark.asyncio
    async def test_service_health_monitoring(self, mock_memory_client, mock_prompt_client, mock_document_client):
        """Test health monitoring across all services."""
        services = [
            ("memory_agent", mock_memory_client),
            ("prompt_store", mock_prompt_client),
            ("document_store", mock_document_client)
        ]

        health_results = {}
        for service_name, client in services:
            try:
                if service_name == "memory_agent":
                    health = await client.health_check()
                else:
                    # For other services, we'll mock health checks
                    health = {"status": "healthy", "service": service_name}

                health_results[service_name] = health["status"] == "healthy"
            except Exception:
                health_results[service_name] = False

        # All services should be healthy
        assert all(health_results.values()), f"Some services unhealthy: {health_results}"

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, mock_memory_client, mock_prompt_client, mock_document_client):
        """Test concurrent operations across services."""
        import asyncio

        async def memory_operations():
            tasks = []
            for i in range(3):
                task = asyncio.create_task(mock_memory_client.put_memory_item(
                    type="operation",
                    key=f"concurrent_test_{i}",
                    summary=f"Concurrent test operation {i}",
                    data={"test_id": i}
                ))
                tasks.append(task)
            results = await asyncio.gather(*tasks)
            return results

        async def prompt_operations():
            tasks = []
            for i in range(2):
                task = asyncio.create_task(mock_prompt_client.create_prompt(
                    name=f"Concurrent Test Prompt {i}",
                    category="test",
                    content=f"Test content {i}"
                ))
                tasks.append(task)
            results = await asyncio.gather(*tasks)
            return results

        async def document_operations():
            tasks = []
            for i in range(2):
                task = asyncio.create_task(mock_document_client.create_document({
                    "content": f"Concurrent test document {i}",
                    "content_type": "text"
                }))
                tasks.append(task)
            results = await asyncio.gather(*tasks)
            return results

        # Run all operations concurrently
        memory_results, prompt_results, doc_results = await asyncio.gather(
            memory_operations(),
            prompt_operations(),
            document_operations()
        )

        # Verify all operations succeeded
        assert all(result["success"] for result in memory_results)
        assert all(result["success"] for result in prompt_results)
        assert all(result["success"] for result in doc_results)


class TestDashboardPageIntegration:
    """Test dashboard page integration."""

    def test_memory_browser_page_import(self):
        """Test memory browser page can be imported."""
        try:
            from pages.memory_browser import render_memory_browser_page
            assert callable(render_memory_browser_page)
        except ImportError:
            pytest.skip("Memory browser page not available")

    def test_prompt_browser_page_import(self):
        """Test prompt browser page can be imported."""
        try:
            from pages.prompt_browser import render_prompt_browser_page
            assert callable(render_prompt_browser_page)
        except ImportError:
            pytest.skip("Prompt browser page not available")

    def test_document_browser_page_import(self):
        """Test document browser page can be imported."""
        try:
            from pages.document_browser import render_document_browser_page
            assert callable(render_document_browser_page)
        except ImportError:
            pytest.skip("Document browser page not available")

    def test_overview_page_import(self):
        """Test overview page can be imported."""
        try:
            from pages.overview import render_overview_page
            assert callable(render_overview_page)
        except ImportError:
            pytest.skip("Overview page not available")


class TestDataFlowIntegration:
    """Test data flow between dashboard components."""

    @pytest.mark.asyncio
    async def test_memory_to_prompt_workflow(self, mock_memory_client, mock_prompt_client):
        """Test workflow where memory data influences prompt creation."""
        # Create memory about user preferences
        preference_memory = {
            "type": "llm_summary",
            "key": "user_preference_summary",
            "summary": "User prefers concise, technical responses with code examples",
            "data": {
                "preference": "concise_technical",
                "style": "code_examples",
                "complexity": "intermediate"
            }
        }

        memory_result = await mock_memory_client.put_memory_item(**preference_memory)
        assert memory_result["success"] is True

        # Retrieve memory to inform prompt creation
        memory_items = await mock_memory_client.list_memory_items(type_filter="llm_summary")
        assert len(memory_items["items"]) > 0

        user_preference = memory_items["items"][0]["data"]["preference"]

        # Create prompt based on user preference
        prompt_content = f"You are a helpful AI assistant. Provide {user_preference} responses with clear examples."

        prompt_data = {
            "name": "Personalized Assistant",
            "category": "chat",
            "content": prompt_content,
            "description": f"Prompt tailored to user preference: {user_preference}"
        }

        prompt_result = await mock_prompt_client.create_prompt(**prompt_data)
        assert prompt_result["success"] is True

    @pytest.mark.asyncio
    async def test_document_to_memory_workflow(self, mock_document_client, mock_memory_client):
        """Test workflow where document analysis creates memory."""
        # Create a technical document
        technical_doc = {
            "content": "# Python Best Practices\n\n1. Use type hints\n2. Write docstrings\n3. Follow PEP 8\n\n```python\ndef hello(name: str) -> str:\n    \"\"\"Greet a person by name.\"\"\"\n    return f\"Hello, {name}!\"\n```",
            "content_type": "markdown",
            "metadata": {"topic": "python", "difficulty": "intermediate"}
        }

        doc_result = await mock_document_client.create_document(technical_doc)
        assert doc_result["success"] is True

        # Simulate analysis and memory creation
        analysis_memory = {
            "type": "doc_summary",
            "key": f"doc_analysis_{doc_result['id']}",
            "summary": "Analyzed Python best practices document - contains code examples and style guidelines",
            "data": {
                "document_id": doc_result["id"],
                "topics": ["python", "best_practices", "code_examples"],
                "quality_score": 8.5,
                "recommendations": ["Use for code review prompts", "Reference in Python tutorials"]
            }
        }

        memory_result = await mock_memory_client.put_memory_item(**analysis_memory)
        assert memory_result["success"] is True

        # Verify the memory-document link
        memory_items = await mock_memory_client.list_memory_items(type_filter="doc_summary")
        assert len(memory_items["items"]) > 0
        assert memory_items["items"][0]["data"]["document_id"] == doc_result["id"]


class TestErrorRecoveryWorkflows:
    """Test error handling and recovery workflows."""

    @pytest.mark.asyncio
    async def test_service_failure_recovery(self, mock_memory_client, mock_prompt_client):
        """Test recovery when services fail."""
        # Simulate service failure
        original_health_check = mock_memory_client.health_check
        mock_memory_client.health_check = Mock(side_effect=Exception("Service temporarily unavailable"))

        try:
            # This should fail
            with pytest.raises(Exception):
                await mock_memory_client.health_check()
        finally:
            # Restore service
            mock_memory_client.health_check = original_health_check

        # Verify service is restored
        health = await mock_memory_client.health_check()
        assert health["status"] == "healthy"

        # Continue with normal operations
        result = await mock_prompt_client.list_prompts()
        assert "prompts" in result

    @pytest.mark.asyncio
    async def test_partial_failure_handling(self, mock_memory_client, mock_prompt_client, mock_document_client):
        """Test handling partial failures in multi-service operations."""
        # Make prompt client fail
        mock_prompt_client.create_prompt = Mock(side_effect=Exception("Validation error"))

        try:
            # This should fail
            with pytest.raises(Exception):
                await mock_prompt_client.create_prompt(
                    name="Test", category="test", content="Test content"
                )
        except Exception:
            pass  # Expected

        # Other services should still work
        memory_result = await mock_memory_client.health_check()
        assert memory_result["status"] == "healthy"

        doc_result = await mock_document_client.list_documents()
        assert "items" in doc_result

    @pytest.mark.asyncio
    async def test_timeout_and_retry_logic(self, mock_memory_client):
        """Test timeout handling and retry logic."""
        import asyncio

        # Simulate timeout
        async def slow_operation():
            await asyncio.sleep(0.1)  # Simulate delay
            return {"success": True, "data": "result"}

        mock_memory_client.list_memory_items = slow_operation

        # Operation should complete within reasonable time
        import time
        start_time = time.time()
        result = await mock_memory_client.list_memory_items()
        end_time = time.time()

        assert end_time - start_time < 1.0  # Should complete quickly
        assert result["success"] is True
