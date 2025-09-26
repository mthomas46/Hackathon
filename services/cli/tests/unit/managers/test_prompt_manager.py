"""Comprehensive tests for CLI PromptManager."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add service path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from cli.modules.managers.prompt_manager import PromptManager


class TestPromptManager:
    """Test PromptManager functionality."""

    @pytest.fixture
    def mock_console(self):
        """Create mock console."""
        return Mock(spec=['print', 'input'])

    @pytest.fixture
    def mock_clients(self):
        """Create mock service clients."""
        return Mock(spec=['post_json', 'get_json'])

    @pytest.fixture
    def prompt_manager(self, mock_console, mock_clients):
        """Create PromptManager instance."""
        return PromptManager(mock_console, mock_clients)

    def test_prompt_manager_initialization(self, prompt_manager, mock_console, mock_clients):
        """Test PromptManager initialization."""
        assert prompt_manager.console == mock_console
        assert prompt_manager.clients == mock_clients
        assert prompt_manager.cache == {}

    @pytest.mark.asyncio
    async def test_get_main_menu(self, prompt_manager):
        """Test main menu retrieval."""
        menu = await prompt_manager.get_main_menu()

        assert isinstance(menu, list)
        assert len(menu) == 6  # 6 menu items

        # Check menu structure
        for item in menu:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], str)  # Choice number
            assert isinstance(item[1], str)  # Description

    @pytest.mark.asyncio
    async def test_handle_choice_list_prompts(self, prompt_manager):
        """Test handling list prompts choice."""
        with patch.object(prompt_manager, 'list_prompts', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = True

            result = await prompt_manager.handle_choice("1")
            assert result is True
            mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_choice_search_prompts(self, prompt_manager):
        """Test handling search prompts choice."""
        with patch.object(prompt_manager, 'search_prompts', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = True

            result = await prompt_manager.handle_choice("2")
            assert result is True
            mock_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_choice_create_prompt(self, prompt_manager):
        """Test handling create prompt choice."""
        with patch.object(prompt_manager, 'create_prompt', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = True

            result = await prompt_manager.handle_choice("3")
            assert result is True
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_choice_update_prompt(self, prompt_manager):
        """Test handling update prompt choice."""
        with patch.object(prompt_manager, 'update_prompt', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = True

            result = await prompt_manager.handle_choice("4")
            assert result is True
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_choice_delete_prompt(self, prompt_manager):
        """Test handling delete prompt choice."""
        with patch.object(prompt_manager, 'delete_prompt', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True

            result = await prompt_manager.handle_choice("5")
            assert result is True
            mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_choice_view_details(self, prompt_manager):
        """Test handling view prompt details choice."""
        with patch.object(prompt_manager, 'view_prompt_details', new_callable=AsyncMock) as mock_view:
            mock_view.return_value = True

            result = await prompt_manager.handle_choice("6")
            assert result is True
            mock_view.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_choice_invalid(self, prompt_manager):
        """Test handling invalid choice."""
        result = await prompt_manager.handle_choice("invalid")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_prompts_success(self, prompt_manager, mock_clients):
        """Test successful prompt listing."""
        mock_response = Mock()
        mock_response.get.return_value = [
            {"id": "prompt1", "name": "Test Prompt 1"},
            {"id": "prompt2", "name": "Test Prompt 2"}
        ]
        mock_clients.get_json = AsyncMock(return_value=mock_response)

        with patch.object(prompt_manager.console, 'print') as mock_print:
            result = await prompt_manager.list_prompts()
            assert result is True

            # Verify API call
            mock_clients.get_json.assert_called_once()

            # Verify console output
            mock_print.assert_called()

    @pytest.mark.asyncio
    async def test_list_prompts_api_error(self, prompt_manager, mock_clients):
        """Test prompt listing with API error."""
        mock_clients.get_json = AsyncMock(side_effect=Exception("API Error"))

        with patch.object(prompt_manager.console, 'print') as mock_print:
            result = await prompt_manager.list_prompts()
            assert result is False

            # Verify error message printed
            mock_print.assert_called()

    @pytest.mark.asyncio
    async def test_search_prompts_with_query(self, prompt_manager, mock_clients):
        """Test prompt search with user query."""
        mock_response = Mock()
        mock_response.get.return_value = [{"id": "prompt1", "name": "Found Prompt"}]
        mock_clients.post_json = AsyncMock(return_value=mock_response)

        with patch('rich.prompt.Prompt.ask', return_value="test query") as mock_prompt, \
             patch.object(prompt_manager.console, 'print') as mock_print:

            result = await prompt_manager.search_prompts()
            assert result is True

            # Verify API call with search query
            mock_clients.post_json.assert_called_once()
            mock_print.assert_called()

    @pytest.mark.asyncio
    async def test_create_prompt_success(self, prompt_manager, mock_clients):
        """Test successful prompt creation."""
        mock_response = Mock()
        mock_response.get.return_value = {"id": "new_prompt", "name": "New Prompt"}
        mock_clients.post_json = AsyncMock(return_value=mock_response)

        with patch('rich.prompt.Prompt.ask') as mock_prompt, \
             patch.object(prompt_manager.console, 'print') as mock_print:

            # Mock user inputs
            mock_prompt.side_effect = ["New Prompt", "This is a test prompt", "test-category"]

            result = await prompt_manager.create_prompt()
            assert result is True

            # Verify API call
            mock_clients.post_json.assert_called_once()
            mock_print.assert_called()

    @pytest.mark.asyncio
    async def test_create_prompt_validation_error(self, prompt_manager):
        """Test prompt creation with validation error."""
        with patch('rich.prompt.Prompt.ask', return_value="") as mock_prompt, \
             patch.object(prompt_manager.console, 'print') as mock_print:

            result = await prompt_manager.create_prompt()
            assert result is False

            # Verify error message
            mock_print.assert_called()

    @pytest.mark.asyncio
    async def test_update_prompt_success(self, prompt_manager, mock_clients):
        """Test successful prompt update."""
        # Mock finding existing prompt
        with patch.object(prompt_manager, 'select_prompt', return_value="prompt1") as mock_select, \
             patch('rich.prompt.Prompt.ask') as mock_prompt, \
             patch.object(prompt_manager.console, 'print') as mock_print:

            mock_prompt.side_effect = ["Updated Name", "Updated content"]
            mock_clients.post_json = AsyncMock(return_value=Mock())

            result = await prompt_manager.update_prompt()
            assert result is True

            mock_select.assert_called_once()
            mock_clients.post_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_prompt_with_confirmation(self, prompt_manager, mock_clients):
        """Test prompt deletion with user confirmation."""
        with patch.object(prompt_manager, 'select_prompt', return_value="prompt1") as mock_select, \
             patch('rich.prompt.Confirm.ask', return_value=True) as mock_confirm, \
             patch.object(prompt_manager.console, 'print') as mock_print:

            mock_clients.post_json = AsyncMock(return_value=Mock())

            result = await prompt_manager.delete_prompt()
            assert result is True

            mock_select.assert_called_once()
            mock_confirm.assert_called_once()
            mock_clients.post_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_prompt_cancelled(self, prompt_manager):
        """Test prompt deletion when user cancels."""
        with patch.object(prompt_manager, 'select_prompt', return_value="prompt1"), \
             patch('rich.prompt.Confirm.ask', return_value=False) as mock_confirm:

            result = await prompt_manager.delete_prompt()
            assert result is False

            mock_confirm.assert_called_once()

    @pytest.mark.asyncio
    async def test_view_prompt_details(self, prompt_manager, mock_clients):
        """Test viewing prompt details."""
        mock_response = Mock()
        mock_response.get.return_value = {
            "id": "prompt1",
            "name": "Test Prompt",
            "content": "Test content",
            "category": "test"
        }
        mock_clients.get_json = AsyncMock(return_value=mock_response)

        with patch.object(prompt_manager, 'select_prompt', return_value="prompt1"), \
             patch.object(prompt_manager.console, 'print') as mock_print:

            result = await prompt_manager.view_prompt_details()
            assert result is True

            mock_clients.get_json.assert_called_once()
            mock_print.assert_called()

    def test_select_prompt_from_list(self, prompt_manager):
        """Test prompt selection from list."""
        prompts = [
            {"id": "prompt1", "name": "First Prompt"},
            {"id": "prompt2", "name": "Second Prompt"}
        ]

        with patch('rich.prompt.Prompt.ask', return_value="1") as mock_prompt:
            result = prompt_manager.select_prompt(prompts)
            assert result == "prompt1"

    def test_select_prompt_invalid_choice(self, prompt_manager):
        """Test prompt selection with invalid choice."""
        prompts = [{"id": "prompt1", "name": "Test Prompt"}]

        with patch('rich.prompt.Prompt.ask', side_effect=["invalid", "1"]) as mock_prompt:
            result = prompt_manager.select_prompt(prompts)
            assert result == "prompt1"

    @pytest.mark.asyncio
    async def test_refresh_cache(self, prompt_manager, mock_clients):
        """Test cache refresh functionality."""
        mock_response = Mock()
        mock_response.get.return_value = [{"id": "prompt1", "name": "Cached Prompt"}]
        mock_clients.get_json = AsyncMock(return_value=mock_response)

        result = await prompt_manager.refresh_cache()
        assert result is True

        # Verify cache was updated
        assert "prompts" in prompt_manager.cache
        assert len(prompt_manager.cache["prompts"]) == 1

    def test_clear_cache(self, prompt_manager):
        """Test cache clearing."""
        # Set up cache
        prompt_manager.cache = {"prompts": [{"id": "test"}]}

        result = prompt_manager.clear_cache()
        assert result is True
        assert prompt_manager.cache == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
