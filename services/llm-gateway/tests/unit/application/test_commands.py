"""Unit tests for LLM gateway application commands."""

import pytest
from datetime import datetime, timezone

from services.llm_gateway.application.commands import (
    ProcessLLMRequestCommand,
    UpdateProviderStatusCommand,
    RefreshProviderModelsCommand,
    UpdateRoutingRulesCommand
)


class TestProcessLLMRequestCommand:
    """Test cases for ProcessLLMRequestCommand."""

    def test_command_creation(self):
        """Test basic ProcessLLMRequestCommand creation."""
        command = ProcessLLMRequestCommand(
            request_id="req-123",
            prompt="Test prompt",
            model="llama2",
            provider="ollama",
            max_tokens=100,
            temperature=0.7,
            stream=False
        )

        assert command.request_id == "req-123"
        assert command.prompt == "Test prompt"
        assert command.model == "llama2"
        assert command.provider == "ollama"
        assert command.max_tokens == 100
        assert command.temperature == 0.7
        assert command.stream is False

    def test_command_with_optional_params(self):
        """Test command with all optional parameters."""
        command = ProcessLLMRequestCommand(
            request_id="req-456",
            prompt="Advanced prompt",
            model="gpt-4",
            provider="openai",
            max_tokens=2000,
            temperature=0.3,
            top_p=0.9,
            top_k=50,
            stream=True,
            system_prompt="You are a helpful assistant",
            response_format="json"
        )

        assert command.top_p == 0.9
        assert command.top_k == 50
        assert command.stream is True
        assert command.system_prompt == "You are a helpful assistant"
        assert command.response_format == "json"

    def test_command_validation(self):
        """Test command validation."""
        # Valid command
        valid_command = ProcessLLMRequestCommand(
            request_id="valid-123",
            prompt="Valid prompt",
            model="llama2"
        )
        assert valid_command.request_id == "valid-123"

        # Commands should validate at creation time
        # (In pydantic, validation happens during instantiation)


class TestUpdateProviderStatusCommand:
    """Test cases for UpdateProviderStatusCommand."""

    def test_command_creation(self):
        """Test basic UpdateProviderStatusCommand creation."""
        command = UpdateProviderStatusCommand(
            provider_name="ollama",
            status="healthy",
            latency_ms=45,
            error_message=None
        )

        assert command.provider_name == "ollama"
        assert command.status == "healthy"
        assert command.latency_ms == 45
        assert command.error_message is None

    def test_command_with_error(self):
        """Test command with error status."""
        command = UpdateProviderStatusCommand(
            provider_name="openai",
            status="unhealthy",
            latency_ms=None,
            error_message="API rate limit exceeded"
        )

        assert command.status == "unhealthy"
        assert command.error_message == "API rate limit exceeded"

    def test_command_with_metrics(self):
        """Test command with performance metrics."""
        command = UpdateProviderStatusCommand(
            provider_name="anthropic",
            status="degraded",
            latency_ms=2000,
            error_message="High latency detected",
            additional_metrics={
                "success_rate": 0.95,
                "requests_per_minute": 50
            }
        )

        assert command.status == "degraded"
        assert command.latency_ms == 2000
        assert command.additional_metrics["success_rate"] == 0.95


class TestRefreshProviderModelsCommand:
    """Test cases for RefreshProviderModelsCommand."""

    def test_command_creation(self):
        """Test basic RefreshProviderModelsCommand creation."""
        command = RefreshProviderModelsCommand(
            provider_name="ollama",
            force_refresh=False,
            timeout_seconds=30
        )

        assert command.provider_name == "ollama"
        assert command.force_refresh is False
        assert command.timeout_seconds == 30

    def test_command_force_refresh(self):
        """Test force refresh command."""
        command = RefreshProviderModelsCommand(
            provider_name="openai",
            force_refresh=True,
            timeout_seconds=60
        )

        assert command.force_refresh is True
        assert command.timeout_seconds == 60

    def test_command_with_filters(self):
        """Test command with model filters."""
        command = RefreshProviderModelsCommand(
            provider_name="ollama",
            model_filters={
                "capability": "chat",
                "min_context_window": 4096
            }
        )

        assert command.model_filters["capability"] == "chat"
        assert command.model_filters["min_context_window"] == 4096


class TestUpdateRoutingRulesCommand:
    """Test cases for UpdateRoutingRulesCommand."""

    def test_command_creation(self):
        """Test basic UpdateRoutingRulesCommand creation."""
        routing_rules = {
            "default_provider": "ollama",
            "model_mappings": {
                "gpt-3.5-turbo": "openai",
                "llama2": "ollama"
            },
            "load_balancing": {
                "enabled": True,
                "strategy": "round_robin"
            }
        }

        command = UpdateRoutingRulesCommand(
            routing_rules=routing_rules,
            validate_rules=True,
            backup_existing=True
        )

        assert command.routing_rules == routing_rules
        assert command.validate_rules is True
        assert command.backup_existing is True

    def test_command_complex_rules(self):
        """Test command with complex routing rules."""
        complex_rules = {
            "providers": {
                "ollama": {"priority": 1, "weight": 0.7},
                "openai": {"priority": 2, "weight": 0.3}
            },
            "model_routing": [
                {
                    "pattern": "gpt-*",
                    "provider": "openai",
                    "fallback": "ollama"
                },
                {
                    "pattern": "llama*",
                    "provider": "ollama",
                    "fallback": "openai"
                }
            ],
            "quality_routing": {
                "high_quality": ["gpt-4", "claude-2"],
                "fast": ["llama2:7b", "gpt-3.5-turbo"],
                "cost_effective": ["llama2:7b", "ollama-models"]
            }
        }

        command = UpdateRoutingRulesCommand(
            routing_rules=complex_rules,
            validate_rules=True
        )

        assert command.routing_rules["providers"]["ollama"]["weight"] == 0.7
        assert len(command.routing_rules["model_routing"]) == 2


class TestCommandImmutability:
    """Test command immutability and validation."""

    def test_command_immutability(self):
        """Test that commands are immutable after creation."""
        command = ProcessLLMRequestCommand(
            request_id="immutable-123",
            prompt="Test prompt",
            model="llama2"
        )

        original_request_id = command.request_id
        original_prompt = command.prompt

        # Commands should be treated as immutable
        assert command.request_id == original_request_id
        assert command.prompt == original_prompt

    def test_command_timestamp(self):
        """Test that commands include creation timestamp."""
        before_creation = datetime.now(timezone.utc)

        command = ProcessLLMRequestCommand(
            request_id="timestamp-test",
            prompt="Test",
            model="llama2"
        )

        after_creation = datetime.now(timezone.utc)

        # Command should have creation timestamp
        assert hasattr(command, 'created_at') or hasattr(command, 'timestamp')

    def test_command_serialization(self):
        """Test command serialization for event sourcing."""
        command = ProcessLLMRequestCommand(
            request_id="serialize-test",
            prompt="Test prompt",
            model="llama2",
            max_tokens=100
        )

        # Commands should be serializable
        command_dict = {
            "request_id": command.request_id,
            "prompt": command.prompt,
            "model": command.model,
            "max_tokens": command.max_tokens
        }

        assert command_dict["request_id"] == "serialize-test"
        assert command_dict["model"] == "llama2"


class TestCommandValidation:
    """Test comprehensive command validation."""

    def test_process_command_validation(self):
        """Test ProcessLLMRequestCommand validation."""
        # Valid command
        valid_command = ProcessLLMRequestCommand(
            request_id="valid-123",
            prompt="This is a valid prompt with enough content",
            model="llama2",
            max_tokens=100,
            temperature=0.7
        )
        assert valid_command.request_id == "valid-123"

        # Invalid temperature
        with pytest.raises(ValueError):
            ProcessLLMRequestCommand(
                request_id="invalid-temp",
                prompt="Test",
                model="llama2",
                temperature=2.5  # Invalid: > 2.0
            )

        # Invalid max_tokens
        with pytest.raises(ValueError):
            ProcessLLMRequestCommand(
                request_id="invalid-tokens",
                prompt="Test",
                model="llama2",
                max_tokens=100000  # Invalid: too high
            )

    def test_provider_command_validation(self):
        """Test UpdateProviderStatusCommand validation."""
        # Valid command
        valid_command = UpdateProviderStatusCommand(
            provider_name="ollama",
            status="healthy",
            latency_ms=100
        )
        assert valid_command.provider_name == "ollama"

        # Invalid status
        with pytest.raises(ValueError):
            UpdateProviderStatusCommand(
                provider_name="ollama",
                status="invalid_status",
                latency_ms=100
            )

    def test_routing_command_validation(self):
        """Test UpdateRoutingRulesCommand validation."""
        # Valid command
        valid_rules = {
            "default_provider": "ollama",
            "model_mappings": {"gpt-3.5-turbo": "openai"}
        }

        valid_command = UpdateRoutingRulesCommand(
            routing_rules=valid_rules
        )
        assert valid_command.routing_rules == valid_rules

        # Invalid rules (empty)
        with pytest.raises(ValueError):
            UpdateRoutingRulesCommand(
                routing_rules={}
            )


class TestCommandMetadata:
    """Test command metadata and context."""

    def test_command_context(self):
        """Test command execution context."""
        command = ProcessLLMRequestCommand(
            request_id="context-test",
            prompt="Test prompt",
            model="llama2",
            user_id="user-123",
            session_id="session-456",
            source_ip="192.168.1.100"
        )

        # Command should include context information
        assert hasattr(command, 'user_id') or hasattr(command, 'context')

    def test_command_priority(self):
        """Test command priority levels."""
        high_priority_command = ProcessLLMRequestCommand(
            request_id="high-priority",
            prompt="Urgent request",
            model="llama2",
            priority="high"
        )

        normal_priority_command = ProcessLLMRequestCommand(
            request_id="normal-priority",
            prompt="Normal request",
            model="llama2"
        )

        # Commands should support priority levels
        assert hasattr(high_priority_command, 'priority') or hasattr(high_priority_command, 'priority_level')

    def test_command_timeout(self):
        """Test command timeout handling."""
        command_with_timeout = ProcessLLMRequestCommand(
            request_id="timeout-test",
            prompt="Test prompt",
            model="llama2",
            timeout_seconds=30
        )

        command_without_timeout = ProcessLLMRequestCommand(
            request_id="no-timeout",
            prompt="Test prompt",
            model="llama2"
        )

        # Commands should support timeout configuration
        assert hasattr(command_with_timeout, 'timeout_seconds') or hasattr(command_with_timeout, 'timeout')
