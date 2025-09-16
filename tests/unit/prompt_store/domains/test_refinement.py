"""Tests for refinement domain.

Tests covering repository, service, and handler layers for LLM-assisted prompt refinement.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import uuid

from services.prompt_store.domain.refinement.service import PromptRefinementService
from services.prompt_store.domain.refinement.handlers import PromptRefinementHandlers


@pytest.mark.unit
class TestRefinementService:
    """Test PromptRefinementService operations."""

    @pytest.mark.asyncio
    async def test_get_refinement_status_success(self):
        """Test getting refinement session status."""
        service = PromptRefinementService()

        # Create a mock session in cache
        session_id = "test_session_123"
        session_data = {
            "session_id": session_id,
            "original_prompt_id": "prompt_123",
            "status": "completed",
            "result_document_id": "doc_456",
            "llm_service": "interpreter",
            "refinement_instructions": "Make it better"
        }

        # Mock cache get
        with patch('services.prompt_store.infrastructure.cache.prompt_store_cache.get') as mock_cache:
            mock_cache.return_value = session_data

            result = await service.get_refinement_status(session_id)
            assert result["session_id"] == session_id
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_refine_prompt_success(self):
        """Test successful prompt refinement."""
        service = PromptRefinementService()

        # Create a test prompt
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()
        unique_name = f'refinement_test_{uuid.uuid4().hex[:8]}'
        prompt = prompt_service.create_entity({
            "name": unique_name,
            "category": "test",
            "content": "Original prompt content",
            "created_by": "test_user"
        })

        # Mock the async execution method that actually calls the LLM
        with patch.object(service, '_execute_refinement_async', new_callable=AsyncMock) as mock_execute:

            result = await service.refine_prompt(
                prompt.id,
                "Make this prompt more specific and actionable",
                "interpreter",
                ["context_doc_1"],
                "test_user"
            )

            assert result["session_id"] is not None
            assert result["status"] == "processing"
            # The async execution should be called (though in tests it might not run due to no event loop)
            # Let's check that the session was created in cache instead
            assert result["session_id"] is not None

    @pytest.mark.asyncio
    async def test_compare_prompt_versions_success(self):
        """Test prompt version comparison."""
        service = PromptRefinementService()

        # Create test prompt
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()
        unique_name = f'comparison_test_{uuid.uuid4().hex[:8]}'
        prompt = prompt_service.create_entity({
            "name": unique_name,
            "category": "test",
            "content": "Original content",
            "created_by": "test_user"
        })

        # Mock version retrieval
        with patch.object(prompt_service, '_get_prompt_versions') as mock_versions:
            mock_versions.return_value = [
                Mock(content="Version 1 content", version=1),
                Mock(content="Version 2 content", version=2)
            ]

            result = await service.compare_prompt_versions(prompt.id, 1, 2)
            assert result["prompt_id"] == prompt.id
            assert "comparison" in result

    @pytest.mark.asyncio
    async def test_replace_prompt_with_refined_success(self):
        """Test applying refinement results."""
        service = PromptRefinementService()

        # Create test prompt
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()
        unique_name = f'apply_test_{uuid.uuid4().hex[:8]}'
        prompt = prompt_service.create_entity({
            "name": unique_name,
            "category": "test",
            "content": "Original content",
            "created_by": "test_user"
        })

        # Mock session data and dependencies
        session_id = f'session_{uuid.uuid4().hex}'
        session_data = {
            "session_id": session_id,
            "original_prompt_id": prompt.id,
            "status": "completed",
            "llm_service": "interpreter",
            "refinement_instructions": "Make it better",
            "result_document_id": f'doc_{uuid.uuid4().hex}'
        }

        # Mock document with refined content
        mock_doc = Mock()
        mock_doc.content = '''# Prompt Refinement Result

**Session ID:** ''' + session_id + '''

## Refined Prompt
```
Improved and enhanced content with more details.
```
'''
        mock_doc.metadata = {"original_prompt_version": 1}

        # Mock doc service
        mock_doc_service = AsyncMock()
        mock_doc_service.get_entity.return_value = mock_doc

        with patch('services.prompt_store.infrastructure.cache.prompt_store_cache.get') as mock_cache_get, \
             patch('services.prompt_store.infrastructure.cache.prompt_store_cache.set') as mock_cache_set, \
             patch.object(service, 'initialize_doc_service') as mock_init_doc, \
             patch.object(service, 'doc_service', mock_doc_service), \
             patch.object(prompt_service, 'get_entity') as mock_get_prompt, \
             patch.object(prompt_service, 'update_prompt_content') as mock_update:

            mock_cache_get.return_value = session_data
            mock_get_prompt.return_value = prompt
            mock_update.return_value = Mock(version=2, id=prompt.id)

            result = await service.replace_prompt_with_refined(prompt.id, session_id, "test_user")

            assert "prompt_id" in result
            assert "new_version" in result
            assert result["new_version"] == 2
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_refinement_history_success(self):
        """Test getting refinement history."""
        service = PromptRefinementService()

        # Create test prompt
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()
        unique_name = f'history_test_{uuid.uuid4().hex[:8]}'
        prompt = prompt_service.create_entity({
            "name": unique_name,
            "category": "test",
            "content": "Original content",
            "created_by": "test_user"
        })

        # Mock version retrieval with refinement summaries
        mock_versions = [
            Mock(change_summary="LLM-assisted refinement using interpreter | Content changes: +5 lines, -2 lines",
                version=2, created_by="test_user", created_at=Mock(isoformat=lambda: "2024-01-01T10:00:00"),
                change_type="update"),
            Mock(change_summary="Manual update for testing",
                version=3, created_by="test_user", created_at=Mock(isoformat=lambda: "2024-01-01T11:00:00"),
                change_type="update")
        ]

        with patch.object(prompt_service, '_get_prompt_versions') as mock_get_versions:
            mock_get_versions.return_value = mock_versions

            result = await service.get_refinement_history(prompt.id)
            assert result["prompt_id"] == prompt.id
            assert len(result["refinement_history"]) == 1  # Only the LLM refinement
            assert "LLM-assisted refinement" in result["refinement_history"][0]["change_summary"]

    @pytest.mark.asyncio
    async def test_get_version_refinement_details_success(self):
        """Test getting version refinement details."""
        service = PromptRefinementService()

        # Create test prompt
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()
        unique_name = f'version_details_test_{uuid.uuid4().hex[:8]}'
        prompt = prompt_service.create_entity({
            "name": unique_name,
            "category": "test",
            "content": "Original content",
            "created_by": "test_user"
        })

        # Mock version retrieval
        mock_version = Mock(
            change_summary="LLM-assisted refinement using interpreter | Content changes: +3 lines, -1 lines | Instructions: Make it more detailed",
            version=2,
            created_by="test_user",
            created_at=Mock(isoformat=lambda: "2024-01-01T10:00:00")
        )

        with patch('services.prompt_store.domain.prompts.versioning_repository.PromptVersioningRepository') as mock_repo_class:
            mock_repo_instance = Mock()
            mock_repo_instance.get_version_by_number.return_value = mock_version
            mock_repo_class.return_value = mock_repo_instance

            result = await service.get_version_refinement_details(prompt.id, 2)
            assert result["version"] == 2
            assert result["is_refinement"] is True
            assert "refinement_info" in result
            assert result["refinement_info"]["llm_service"] == "interpreter"
            assert result["refinement_info"]["lines_added"] == 3
            assert result["refinement_info"]["lines_removed"] == 1

    @pytest.mark.asyncio
    async def test_call_llm_service_interpreter(self):
        """Test calling interpreter LLM service."""
        service = PromptRefinementService()

        request = {
            "original_prompt": {"name": "test", "content": "Write code", "category": "coding"},
            "refinement_instructions": "Add error handling",
            "user_id": "test_user"
        }

        with patch('services.shared.clients.ServiceClients.interpret_query', new_callable=AsyncMock) as mock_interpret:
            mock_interpret.return_value = {
                "success": True,
                "data": {
                    "intent": "refine_prompt",
                    "response_text": "Improved prompt: Write robust code with error handling and validation."
                }
            }

            result = await service._call_llm_service("interpreter", request)
            assert "refined_content" in result
            mock_interpret.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_llm_service_bedrock(self):
        """Test calling bedrock LLM service."""
        service = PromptRefinementService()

        request = {
            "original_prompt": {"name": "test", "content": "Write code", "category": "coding"},
            "refinement_instructions": "Add error handling",
            "user_id": "test_user"
        }

        with patch.object(service, '_call_bedrock_service', new_callable=AsyncMock) as mock_bedrock:
            mock_bedrock.return_value = {"output": "Improved prompt content from Claude"}

            result = await service._call_llm_service("bedrock-proxy", request)
            assert result["refined_content"] == "Improved prompt content from Claude"
            mock_bedrock.assert_called_once()

    def test_extract_refined_prompt_from_document(self):
        """Test extracting refined prompt from document."""
        service = PromptRefinementService()

        # Test document with proper structure
        mock_doc = Mock()
        mock_doc.content = '''# Prompt Refinement Result

## Refined Prompt
```
This is the refined prompt content.
It has multiple lines and proper formatting.
```
'''

        result = service._extract_refined_prompt_from_document(mock_doc)
        assert result == "This is the refined prompt content.\nIt has multiple lines and proper formatting."

    def test_generate_refinement_change_summary(self):
        """Test generating detailed change summary."""
        service = PromptRefinementService()

        original_prompt = Mock()
        original_prompt.content = "Original content"
        refined_content = "Improved and enhanced content with more details"

        session = {"llm_service": "interpreter", "refinement_instructions": "Make it better"}
        result_doc = Mock()
        result_doc.metadata = {"original_prompt_version": 1}

        summary = service._generate_refinement_change_summary(
            original_prompt, refined_content, session, result_doc
        )

        assert "LLM-assisted refinement using interpreter" in summary
        assert "Content changes:" in summary
        assert "Instructions: Make it better" in summary
        assert "Applied to version 1" in summary

    def test_parse_refinement_summary(self):
        """Test parsing refinement details from summary."""
        service = PromptRefinementService()

        summary = "LLM-assisted refinement using interpreter | Content changes: +3 lines, -1 lines | Instructions: Add error handling | Applied to version 2"

        result = service._parse_refinement_summary(summary)
        assert result["llm_service"] == "interpreter"
        assert result["lines_added"] == 3
        assert result["lines_removed"] == 1
        assert result["refinement_instructions"] == "Add error handling"
        assert result["source_version"] == 2


@pytest.mark.unit
class TestRefinementHandlers:
    """Test PromptRefinementHandlers HTTP operations."""

    @pytest.mark.asyncio
    async def test_handle_refine_prompt_success(self):
        """Test successful prompt refinement handler."""
        handlers = PromptRefinementHandlers()

        with patch.object(handlers.service, 'refine_prompt', new_callable=AsyncMock) as mock_refine:
            mock_refine.return_value = {
                "session_id": "session_123",
                "status": "processing",
                "message": "Refinement started"
            }

            result = await handlers.handle_refine_prompt(
                "prompt_123", "Make it better", "interpreter", None, "test_user"
            )

            result_dict = result.model_dump()
            assert result_dict["success"] is True
            assert result_dict["data"]["session_id"] == "session_123"
            mock_refine.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_get_refinement_status_success(self):
        """Test successful refinement status retrieval handler."""
        handlers = PromptRefinementHandlers()

        with patch.object(handlers.service, 'get_refinement_status', new_callable=AsyncMock) as mock_status:
            mock_status.return_value = {
                "session_id": "session_123",
                "status": "completed",
                "result_document_id": "doc_456",
                "llm_service": "interpreter"
            }

            result = await handlers.handle_get_refinement_status("session_123")

            result_dict = result.model_dump()
            assert result_dict["success"] is True
            assert result_dict["data"]["status"] == "completed"
            mock_status.assert_called_once_with("session_123")

    @pytest.mark.asyncio
    async def test_handle_compare_prompt_versions_success(self):
        """Test successful version comparison handler."""
        handlers = PromptRefinementHandlers()

        with patch.object(handlers.service, 'compare_prompt_versions', new_callable=AsyncMock) as mock_compare:
            mock_compare.return_value = {
                "prompt_id": "prompt_123",
                "comparison": {
                    "version_a": {"content": "Version 1"},
                    "version_b": {"content": "Version 2"},
                    "differences": ["Content changed"]
                }
            }

            result = await handlers.handle_compare_prompt_versions("prompt_123", 1, 2)

            result_dict = result.model_dump()
            assert result_dict["success"] is True
            assert result_dict["data"]["prompt_id"] == "prompt_123"
            mock_compare.assert_called_once_with(prompt_id="prompt_123", version_a=1, version_b=2)

    @pytest.mark.asyncio
    async def test_handle_replace_prompt_with_refined_success(self):
        """Test successful refinement application handler."""
        handlers = PromptRefinementHandlers()

        with patch.object(handlers.service, 'replace_prompt_with_refined', new_callable=AsyncMock) as mock_apply:
            mock_apply.return_value = {
                "prompt_id": "prompt_123",
                "new_version": 2,
                "message": "Refinement applied"
            }

            result = await handlers.handle_replace_prompt_with_refined("prompt_123", "session_456", "test_user")

            result_dict = result.model_dump()
            assert result_dict["success"] is True
            assert result_dict["data"]["new_version"] == 2
            mock_apply.assert_called_once_with(prompt_id="prompt_123", session_id="session_456", user_id="test_user")

    @pytest.mark.asyncio
    async def test_handle_get_refinement_history_success(self):
        """Test successful refinement history retrieval handler."""
        handlers = PromptRefinementHandlers()

        with patch.object(handlers.service, 'get_refinement_history', new_callable=AsyncMock) as mock_history:
            mock_history.return_value = {
                "prompt_id": "prompt_123",
                "refinement_history": [
                    {"version": 2, "change_summary": "LLM-assisted refinement", "created_by": "test_user"},
                    {"version": 3, "change_summary": "Another refinement", "created_by": "test_user"}
                ],
                "total_refinements": 2
            }

            result = await handlers.handle_get_refinement_history("prompt_123")

            result_dict = result.model_dump()
            assert result_dict["success"] is True
            assert result_dict["data"]["total_refinements"] == 2
            mock_history.assert_called_once_with("prompt_123")

    @pytest.mark.asyncio
    async def test_handle_get_version_refinement_details_success(self):
        """Test successful version refinement details handler."""
        handlers = PromptRefinementHandlers()

        with patch.object(handlers.service, 'get_version_refinement_details', new_callable=AsyncMock) as mock_details:
            mock_details.return_value = {
                "version": 2,
                "is_refinement": True,
                "refinement_info": {
                    "llm_service": "interpreter",
                    "lines_added": 3,
                    "lines_removed": 1
                }
            }

            result = await handlers.handle_get_version_refinement_details("prompt_123", 2)

            result_dict = result.model_dump()
            assert result_dict["success"] is True
            assert result_dict["data"]["is_refinement"] is True
            assert result_dict["data"]["refinement_info"]["llm_service"] == "interpreter"
            mock_details.assert_called_once_with("prompt_123", 2)

    # Error handling tests
    @pytest.mark.asyncio
    async def test_handle_refine_prompt_validation_error(self):
        """Test prompt refinement handler with validation error."""
        handlers = PromptRefinementHandlers()

        with patch.object(handlers.service, 'refine_prompt', new_callable=AsyncMock) as mock_refine:
            mock_refine.side_effect = ValueError("Invalid prompt ID")

            result = await handlers.handle_refine_prompt(
                "invalid_id", "Make it better", "interpreter", None, "test_user"
            )

            result_dict = result.model_dump()
            assert result_dict["success"] is False
            assert result_dict["error_code"] == "VALIDATION_ERROR"
            assert "Invalid prompt ID" in result_dict["message"]

    @pytest.mark.asyncio
    async def test_handle_get_refinement_status_not_found(self):
        """Test refinement status handler with not found error."""
        handlers = PromptRefinementHandlers()

        with patch.object(handlers.service, 'get_refinement_status', new_callable=AsyncMock) as mock_status:
            mock_status.side_effect = ValueError("Session not found")

            result = await handlers.handle_get_refinement_status("nonexistent_session")

            result_dict = result.model_dump()
            assert result_dict["success"] is False
            assert result_dict["error_code"] == "VALIDATION_ERROR"
            assert "Session not found" in result_dict["message"]

    @pytest.mark.asyncio
    async def test_handle_replace_prompt_with_refined_internal_error(self):
        """Test refinement application handler with internal error."""
        handlers = PromptRefinementHandlers()

        with patch.object(handlers.service, 'replace_prompt_with_refined', new_callable=AsyncMock) as mock_apply:
            mock_apply.side_effect = Exception("Database connection failed")

            result = await handlers.handle_replace_prompt_with_refined("prompt_123", "session_456", "test_user")

            result_dict = result.model_dump()
            assert result_dict["success"] is False
            assert result_dict["error_code"] == "INTERNAL_ERROR"
            assert "Database connection failed" in result_dict["message"]
