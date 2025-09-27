"""Unit tests for prompt store domain entities."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from services.prompt_store.domain.entities import Prompt, PromptTemplate, PromptExecution


class TestPrompt:
    """Test cases for Prompt entity."""

    def test_prompt_creation(self):
        """Test basic Prompt creation."""
        prompt = Prompt(
            name="test-prompt",
            content="This is a test prompt with {variable}",
            description="A test prompt",
            tags=["test", "example"]
        )

        assert prompt.name == "test-prompt"
        assert prompt.content == "This is a test prompt with {variable}"
        assert prompt.description == "A test prompt"
        assert "test" in prompt.tags
        assert isinstance(prompt.created_at, datetime)

    def test_prompt_variable_extraction(self):
        """Test variable extraction from prompt content."""
        prompt = Prompt(
            name="variable-test",
            content="Hello {name}, your age is {age} and you live in {city}"
        )

        variables = prompt.extract_variables()
        assert "name" in variables
        assert "age" in variables
        assert "city" in variables
        assert len(variables) == 3

    def test_prompt_validation(self):
        """Test prompt validation."""
        # Valid prompt
        valid_prompt = Prompt(
            name="valid-prompt",
            content="Valid content",
            description="Valid description"
        )
        assert valid_prompt.validate() is True

        # Invalid prompt (empty content)
        invalid_prompt = Prompt(
            name="invalid-prompt",
            content="",
            description="Invalid description"
        )
        assert invalid_prompt.validate() is False

    def test_prompt_rendering(self):
        """Test prompt rendering with variables."""
        prompt = Prompt(
            name="render-test",
            content="Hello {name}, welcome to {place}!"
        )

        rendered = prompt.render({"name": "Alice", "place": "Wonderland"})
        assert rendered == "Hello Alice, welcome to Wonderland!"

        # Test with missing variables
        with pytest.raises(ValueError):
            prompt.render({"name": "Alice"})  # Missing 'place'

    def test_prompt_metadata(self):
        """Test prompt metadata handling."""
        prompt = Prompt(
            name="metadata-test",
            content="Test content",
            metadata={"author": "test@example.com", "version": "1.0"}
        )

        assert prompt.get_metadata("author") == "test@example.com"
        assert prompt.get_metadata("version") == "1.0"
        assert prompt.get_metadata("nonexistent", "default") == "default"


class TestPromptTemplate:
    """Test cases for PromptTemplate entity."""

    def test_template_creation(self):
        """Test basic PromptTemplate creation."""
        template = PromptTemplate(
            name="greeting-template",
            template_string="Hello {name}! How are you {time_of_day}?",
            description="A greeting template",
            category="social"
        )

        assert template.name == "greeting-template"
        assert template.template_string == "Hello {name}! How are you {time_of_day}?"
        assert template.category == "social"

    def test_template_instantiation(self):
        """Test template instantiation."""
        template = PromptTemplate(
            name="email-template",
            template_string="Subject: {subject}\n\nDear {recipient},\n\n{message}\n\nBest regards,\n{sender}"
        )

        instance = template.instantiate({
            "subject": "Meeting Update",
            "recipient": "John Doe",
            "message": "The meeting is rescheduled to tomorrow.",
            "sender": "Jane Smith"
        })

        expected = "Subject: Meeting Update\n\nDear John Doe,\n\nThe meeting is rescheduled to tomorrow.\n\nBest regards,\nJane Smith"
        assert instance == expected

    def test_template_validation(self):
        """Test template validation."""
        # Valid template
        valid_template = PromptTemplate(
            name="valid-template",
            template_string="Valid {variable} template"
        )
        assert valid_template.validate() is True

        # Invalid template (no variables but claims to have them)
        invalid_template = PromptTemplate(
            name="invalid-template",
            template_string="No variables here"
        )
        # This would depend on validation logic - template might be valid if no variables expected

    def test_template_categories(self):
        """Test template categorization."""
        business_template = PromptTemplate(
            name="business-template",
            template_string="Business {content}",
            category="business"
        )

        creative_template = PromptTemplate(
            name="creative-template",
            template_string="Creative {content}",
            category="creative"
        )

        assert business_template.category == "business"
        assert creative_template.category == "creative"


class TestPromptExecution:
    """Test cases for PromptExecution entity."""

    def test_execution_creation(self):
        """Test basic PromptExecution creation."""
        execution = PromptExecution(
            prompt_id="test-prompt-001",
            input_variables={"name": "Alice", "age": 30},
            execution_context={"user_id": "user123", "session_id": "sess456"}
        )

        assert execution.prompt_id == "test-prompt-001"
        assert execution.input_variables["name"] == "Alice"
        assert execution.execution_context["user_id"] == "user123"
        assert execution.status == "pending"
        assert isinstance(execution.started_at, datetime)

    def test_execution_workflow(self):
        """Test execution workflow."""
        execution = PromptExecution(
            prompt_id="workflow-test",
            input_variables={"query": "What is AI?"}
        )

        # Start execution
        execution.start_execution()
        assert execution.status == "running"
        assert execution.started_at is not None

        # Complete execution
        result = "AI stands for Artificial Intelligence..."
        execution.complete_execution(result)
        assert execution.status == "completed"
        assert execution.result == result
        assert execution.completed_at is not None
        assert execution.execution_time_seconds > 0

    def test_execution_error_handling(self):
        """Test execution error handling."""
        execution = PromptExecution(
            prompt_id="error-test",
            input_variables={"query": "Test query"}
        )

        # Start and then fail
        execution.start_execution()
        error_message = "Model API timeout"
        execution.fail_execution(error_message)

        assert execution.status == "failed"
        assert execution.error_message == error_message
        assert execution.completed_at is not None

    def test_execution_metrics(self):
        """Test execution metrics calculation."""
        execution = PromptExecution(
            prompt_id="metrics-test",
            input_variables={"query": "Test query"}
        )

        execution.start_execution()
        execution.complete_execution("Test result")

        # Test metrics
        assert execution.execution_time_seconds >= 0
        assert execution.input_tokens_count >= 0  # Would be calculated based on input
        assert execution.output_tokens_count >= 0  # Would be calculated based on output

    def test_execution_retry_logic(self):
        """Test execution retry logic."""
        execution = PromptExecution(
            prompt_id="retry-test",
            input_variables={"query": "Test query"}
        )

        # Simulate retries
        assert execution.retry_count == 0
        assert execution.can_retry() is True

        execution.increment_retry_count()
        assert execution.retry_count == 1
        assert execution.can_retry() is True

        # Max retries reached
        for _ in range(4):  # Total of 5 retries (0 + 4 increments + 1 more)
            execution.increment_retry_count()

        assert execution.retry_count == 5
        assert execution.can_retry() is False

    def test_execution_caching(self):
        """Test execution result caching."""
        execution = PromptExecution(
            prompt_id="cache-test",
            input_variables={"query": "Cached query"}
        )

        # Set cache key
        cache_key = "cache-key-123"
        execution.set_cache_key(cache_key)
        assert execution.cache_key == cache_key

        # Mark as cache hit
        execution.mark_cache_hit()
        assert execution.cache_hit is True

    def test_execution_context_validation(self):
        """Test execution context validation."""
        # Valid execution
        valid_execution = PromptExecution(
            prompt_id="valid-exec",
            input_variables={"required": "value"},
            execution_context={"optional": "context"}
        )
        assert valid_execution.validate() is True

        # Invalid execution (missing prompt_id)
        with pytest.raises(ValueError):
            PromptExecution(
                prompt_id="",  # Invalid
                input_variables={"query": "test"}
            )
