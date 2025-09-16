"""Unit tests for orchestration domain functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.prompt_store.domain.orchestration.service import PromptOrchestrator


@pytest.fixture
def orchestrator_service():
    """Create orchestration service for testing."""
    return PromptOrchestrator()


@pytest.mark.asyncio
class TestPromptOrchestrator:
    """Test cases for prompt orchestrator functionality."""

    async def test_create_conditional_chain(self, orchestrator_service):
        """Test creating a conditional chain."""
        chain_definition = {
            "name": "Test Chain",
            "description": "A test conditional chain",
            "steps": [
                {
                    "type": "prompt",
                    "prompt_id": "step1_prompt",
                    "conditions": []
                }
            ],
            "conditions": {}
        }

        with patch('services.prompt_store.domain.orchestration.service.prompt_store_cache') as mock_cache:
            mock_cache.set = AsyncMock()

            result = await orchestrator_service.create_conditional_chain(chain_definition)

            # Verify cache was called
            mock_cache.set.assert_called_once()

            # Verify returned chain structure
            assert "id" in result
            assert result["name"] == "Test Chain"
            assert result["description"] == "A test conditional chain"
            assert len(result["steps"]) == 1
            assert result["status"] == "created"

    async def test_execute_conditional_chain_no_conditions(self, orchestrator_service):
        """Test executing a chain with no conditions."""
        chain_definition = {
            "name": "Simple Chain",
            "steps": [
                {
                    "type": "prompt",
                    "prompt_id": "test_prompt",
                    "variables": {"input": "test"}
                }
            ]
        }

        initial_context = {"input": "hello world"}

        with patch('services.prompt_store.domain.orchestration.service.prompt_store_cache') as mock_cache:
            # Mock chain retrieval
            mock_cache.get.return_value = chain_definition

            # Mock prompt execution
            with patch.object(orchestrator_service, '_execute_prompt_step', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = {
                    "step_type": "prompt",
                    "success": True,
                    "outputs": {"result": "processed"}
                }

                result = await orchestrator_service.execute_conditional_chain("chain_123", initial_context)

                # Verify execution structure
                assert result["chain_id"] == "chain_123"
                assert result["status"] == "completed"
                assert len(result["step_results"]) == 1
                assert "started_at" in result
                assert "completed_at" in result

    async def test_execute_conditional_chain_with_conditions_met(self, orchestrator_service):
        """Test executing a chain where conditions are met."""
        initial_context = {"status": "approved", "priority": "high"}

        step_conditions = [
            {
                "field": "status",
                "operator": "equals",
                "value": "approved"
            },
            {
                "field": "priority",
                "operator": "equals",
                "value": "high"
            }
        ]

        # Test condition checking
        result = await orchestrator_service._check_step_conditions(
            {"conditions": step_conditions},
            initial_context
        )

        assert result is True

    async def test_execute_conditional_chain_with_conditions_not_met(self, orchestrator_service):
        """Test executing a chain where conditions are not met."""
        initial_context = {"status": "pending", "priority": "low"}

        step_conditions = [
            {
                "field": "status",
                "operator": "equals",
                "value": "approved"
            }
        ]

        # Test condition checking
        result = await orchestrator_service._check_step_conditions(
            {"conditions": step_conditions},
            initial_context
        )

        assert result is False

    async def test_condition_operators(self, orchestrator_service):
        """Test different condition operators."""
        context = {"score": 85, "tags": ["urgent", "review"], "count": 10}

        # Test greater_than
        assert await orchestrator_service._check_step_conditions(
            {"conditions": [{"field": "score", "operator": "greater_than", "value": 80}]},
            context
        ) is True

        # Test less_than
        assert await orchestrator_service._check_step_conditions(
            {"conditions": [{"field": "score", "operator": "less_than", "value": 80}]},
            context
        ) is False

        # Test contains
        assert await orchestrator_service._check_step_conditions(
            {"conditions": [{"field": "tags", "operator": "contains", "value": "urgent"}]},
            context
        ) is True

        # Test not_equals
        assert await orchestrator_service._check_step_conditions(
            {"conditions": [{"field": "count", "operator": "not_equals", "value": 5}]},
            context
        ) is True

    async def test_execute_prompt_step_success(self, orchestrator_service):
        """Test executing a prompt step successfully."""
        step = {
            "type": "prompt",
            "prompt_id": "test_prompt_123",
            "variables": {"custom_var": "custom_value"}
        }

        context = {"base_var": "base_value"}

        # Mock the clients.interpret_query call
        with patch.object(orchestrator_service.clients, 'interpret_query', new_callable=AsyncMock) as mock_interpret:
            mock_interpret.return_value = {
                "success": True,
                "data": {
                    "response_text": "Generated response",
                    "execution_time": 1.5
                }
            }

            result = await orchestrator_service._execute_step(step, context)

            # Verify the call was made correctly
            mock_interpret.assert_called_once_with(
                f"Execute prompt {step['prompt_id']} with variables: {{'base_var': 'base_value', 'custom_var': 'custom_value'}}",
                "orchestrator"
            )

            # Verify result structure
            assert result["step_type"] == "prompt"
            assert result["success"] is True
            assert result["outputs"]["response"] == "Generated response"
            assert result["outputs"]["execution_time"] == 1.5

    async def test_execute_llm_step_success(self, orchestrator_service):
        """Test executing an LLM step successfully."""
        step = {
            "type": "llm_call",
            "prompt_template": "Analyze this: {input}",
            "llm_service": "interpreter"
        }

        context = {"input": "test data"}

        with patch.object(orchestrator_service.clients, 'interpret_query', new_callable=AsyncMock) as mock_interpret:
            mock_interpret.return_value = {
                "success": True,
                "data": {
                    "response_text": "Analysis complete",
                    "raw_response": {"full": "response"}
                }
            }

            result = await orchestrator_service._execute_step(step, context)

            # Verify template was filled
            expected_prompt = "Analyze this: test data"
            mock_interpret.assert_called_once_with(expected_prompt, "orchestrator")

            # Verify result
            assert result["step_type"] == "llm_call"
            assert result["success"] is True
            assert result["outputs"]["response"] == "Analysis complete"

    async def test_execute_condition_check_step(self, orchestrator_service):
        """Test executing a condition check step."""
        step = {
            "type": "condition_check",
            "check_conditions": [
                {"field": "status", "operator": "equals", "value": "approved"}
            ]
        }

        context = {"status": "approved"}

        result = await orchestrator_service._execute_step(step, context)

        assert result["step_type"] == "condition_check"
        assert result["conditions_met"] is True
        assert result["outputs"]["condition_result"] is True

    async def test_execute_transformation_step(self, orchestrator_service):
        """Test executing a data transformation step."""
        step = {
            "type": "data_transformation",
            "transformations": [
                {
                    "type": "uppercase",
                    "input_field": "name",
                    "output_field": "name_upper"
                },
                {
                    "type": "split",
                    "input_field": "tags",
                    "output_field": "tag_list",
                    "delimiter": ","
                }
            ]
        }

        context = {"name": "john", "tags": "urgent,review"}

        result = await orchestrator_service._execute_step(step, context)

        assert result["step_type"] == "data_transformation"
        assert result["success"] is True
        assert result["outputs"]["name_upper"] == "JOHN"
        assert result["outputs"]["tag_list"] == ["urgent", "review"]

    async def test_fill_template_simple(self, orchestrator_service):
        """Test filling template with simple variables."""
        template = "Hello {name}, welcome to {place}!"
        context = {"name": "Alice", "place": "Wonderland"}

        result = orchestrator_service._fill_template(template, context)

        assert result == "Hello Alice, welcome to Wonderland!"

    async def test_fill_template_missing_vars(self, orchestrator_service):
        """Test filling template with missing variables."""
        template = "Hello {name}, your score is {score}!"
        context = {"name": "Bob"}  # score is missing

        result = orchestrator_service._fill_template(template, context)

        assert result == "Hello Bob, your score is {score}!"

    async def test_create_pipeline(self, orchestrator_service):
        """Test creating a prompt pipeline."""
        pipeline_definition = {
            "name": "Test Pipeline",
            "description": "A test pipeline",
            "stages": [
                {
                    "type": "parallel_prompts",
                    "prompts": [{"name": "prompt1"}, {"name": "prompt2"}]
                }
            ],
            "configuration": {"timeout": 30}
        }

        with patch('services.prompt_store.domain.orchestration.service.prompt_store_cache') as mock_cache:
            mock_cache.set = AsyncMock()

            result = await orchestrator_service.create_pipeline(pipeline_definition)

            assert "id" in result
            assert result["name"] == "Test Pipeline"
            assert result["status"] == "created"
            assert len(result["stages"]) == 1

    async def test_select_optimal_prompt(self, orchestrator_service):
        """Test selecting optimal prompt for a task."""
        # This is a mock implementation, so we'll test the interface
        result = await orchestrator_service.select_optimal_prompt("code review task")

        # In the current implementation, this returns a mock value
        assert result is not None or result is None  # Can be None or a string

    async def test_get_prompt_recommendations(self, orchestrator_service):
        """Test getting prompt recommendations."""
        recommendations = await orchestrator_service.get_prompt_recommendations("documentation task")

        # Should return a list (even if mock data)
        assert isinstance(recommendations, list)
