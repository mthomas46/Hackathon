"""Unit Tests for AWS Integration in Bedrock Proxy Service.

This module tests AWS integration capabilities including:
- AWS Bedrock API client interactions
- Model routing and selection logic
- AWS credential management and security
- Region-based service routing
- Cost optimization and usage tracking

Tests cover the complete AWS integration infrastructure within the Bedrock Proxy service.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any, List

from main import InvokeRequest, InvokeResponse


class TestAWSIntegration:
    """Test AWS Integration functionality."""

    @pytest.fixture
    def bedrock_client(self):
        """Create Bedrock client instance with test configuration."""
        from main import BedrockClient
        return BedrockClient()

    @pytest.fixture
    def model_router(self):
        """Create model router instance with test configuration."""
        from main import ModelRouter
        return ModelRouter()

    @pytest.fixture
    def sample_invoke_request(self):
        """Sample invoke request for testing."""
        return InvokeRequest(
            prompt="Explain the concept of machine learning in simple terms.",
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            template="explanation",
            format="md",
            max_tokens=1000,
            temperature=0.7,
            title="ML Explanation"
        )

    @pytest.fixture
    def mock_bedrock_response(self):
        """Mock AWS Bedrock API response."""
        return {
            "response": {
                "completion": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
                "usage": {
                    "input_tokens": 15,
                    "output_tokens": 28,
                    "total_tokens": 43
                },
                "finish_reason": "end_turn"
            },
            "model": "anthropic.claude-3-sonnet-20240229-v1:0",
            "region": "us-east-1",
            "timestamp": datetime.now().isoformat(),
            "request_id": "test-request-123"
        }

    def test_aws_bedrock_client_initialization(self, bedrock_client):
        """Test AWS Bedrock client initialization."""
        assert bedrock_client is not None
        assert hasattr(bedrock_client, 'client')
        assert hasattr(bedrock_client, 'region')

    def test_model_routing_basic_selection(self, model_router):
        """Test basic model routing and selection."""
        # Test Claude 3 Sonnet selection
        model = model_router.select_model("claude-3-sonnet", "us-east-1")
        assert model == "anthropic.claude-3-sonnet-20240229-v1:0"

        # Test Titan Text selection
        model = model_router.select_model("titan-text", "us-west-2")
        assert model == "amazon.titan-text-express-v1"

        # Test invalid model fallback
        model = model_router.select_model("invalid-model", "us-east-1")
        assert model == "anthropic.claude-3-sonnet-20240229-v1:0"  # Default fallback

    def test_model_routing_region_optimization(self, model_router):
        """Test model routing with region optimization."""
        # Test region-specific model availability
        models_east = model_router.get_available_models("us-east-1")
        models_west = model_router.get_available_models("us-west-2")

        assert len(models_east) > 0
        assert len(models_west) > 0

        # Test latency-based routing
        optimal_model = model_router.select_optimal_model("us-east-1", "text-generation")
        assert optimal_model in models_east

    def test_aws_credential_management(self, bedrock_client):
        """Test AWS credential management and security."""
        with patch.dict('os.environ', {
            'AWS_ACCESS_KEY_ID': 'test-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            # Test credential loading
            creds = bedrock_client._get_credentials()
            assert creds is not None
            assert 'access_key' in creds
            assert 'secret_key' in creds

            # Test secure credential handling (no logging)
            import logging
            with patch('logging.Logger.info') as mock_log:
                bedrock_client._log_credentials_safe()
                # Should not log actual credentials
                assert not any('test-key' in str(call) for call in mock_log.call_args_list)

    def test_cost_optimization_routing(self, model_router):
        """Test cost optimization in model routing."""
        # Test cost-based model selection
        cost_optimized = model_router.select_cost_optimized("text-generation", budget_limit=0.01)
        assert cost_optimized is not None

        # Test cost estimation
        cost_estimate = model_router.estimate_cost("anthropic.claude-3-sonnet-20240229-v1:0", 1000, 500)
        assert cost_estimate > 0
        assert cost_estimate < 1.0  # Reasonable cost estimate

    def test_region_failover_handling(self, bedrock_client):
        """Test region failover and error handling."""
        # Test primary region failure
        with patch.object(bedrock_client, '_call_bedrock_api') as mock_call:
            mock_call.side_effect = [
                Exception("Region us-east-1 unavailable"),
                {"response": {"completion": "Success from failover region"}}
            ]

            # Should automatically failover to secondary region
            result = bedrock_client.invoke_model("test-model", "test prompt", "us-west-2")
            assert result is not None
            assert mock_call.call_count == 2  # Called twice: primary failed, secondary succeeded

    def test_model_performance_tracking(self, bedrock_client):
        """Test model performance tracking and metrics."""
        # Simulate multiple model calls
        performance_data = []

        for i in range(5):
            start_time = datetime.now()
            # Simulate API call
            with patch.object(bedrock_client, '_call_bedrock_api') as mock_call:
                mock_call.return_value = {
                    "response": {"completion": f"Response {i}"},
                    "usage": {"total_tokens": 100 + i * 10}
                }

                result = bedrock_client.invoke_model("test-model", f"Prompt {i}", "us-east-1")

                end_time = datetime.now()
                latency = (end_time - start_time).total_seconds()

                performance_data.append({
                    "latency": latency,
                    "tokens": 100 + i * 10,
                    "success": True
                })

        # Verify performance metrics
        avg_latency = sum(d["latency"] for d in performance_data) / len(performance_data)
        avg_tokens = sum(d["tokens"] for d in performance_data) / len(performance_data)

        assert avg_latency < 1.0  # Reasonable latency
        assert avg_tokens > 0

    def test_security_compliance_validation(self, bedrock_client):
        """Test security compliance validation for AWS integration."""
        # Test input sanitization
        malicious_prompt = "<script>alert('xss')</script> normal prompt"
        sanitized = bedrock_client._sanitize_input(malicious_prompt)
        assert "<script>" not in sanitized
        assert "alert" not in sanitized
        assert "normal prompt" in sanitized

        # Test content filtering
        inappropriate_content = "This contains inappropriate content for testing"
        is_allowed = bedrock_client._validate_content(inappropriate_content)
        # Should either filter or flag the content
        assert isinstance(is_allowed, bool)

    def test_rate_limiting_integration(self, bedrock_client):
        """Test rate limiting integration with AWS services."""
        # Test rate limit handling
        call_count = 0

        def rate_limited_response(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count <= 10:  # First 10 calls succeed
                return {"response": {"completion": f"Response {call_count}"}}
            else:  # Subsequent calls rate limited
                raise Exception("Rate limit exceeded")

        with patch.object(bedrock_client, '_call_bedrock_api', side_effect=rate_limited_response):
            # Make multiple calls
            results = []
            for i in range(15):
                try:
                    result = bedrock_client.invoke_model("test-model", f"Prompt {i}", "us-east-1")
                    results.append(result)
                except Exception as e:
                    if "Rate limit exceeded" in str(e):
                        break  # Stop when rate limited

            # Verify rate limiting behavior
            assert len(results) >= 10  # At least 10 successful calls
            assert call_count > len(results)  # Some calls were rate limited

    def test_model_fallback_strategies(self, model_router):
        """Test model fallback strategies for reliability."""
        # Test primary model failure with fallback
        fallback_sequence = [
            "anthropic.claude-3-sonnet-20240229-v1:0",  # Primary
            "amazon.titan-text-express-v1",            # First fallback
            "anthropic.claude-3-haiku-20240307-v1:0"   # Second fallback
        ]

        call_count = 0
        def failing_model_call(model, *args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                raise Exception("Primary model unavailable")
            elif call_count == 2:
                raise Exception("First fallback unavailable")
            else:
                return {"response": {"completion": "Success from final fallback"}}

        with patch.object(model_router, '_invoke_model', side_effect=failing_model_call):
            result = model_router.invoke_with_fallback("test prompt", fallback_sequence, "us-east-1")

            assert result is not None
            assert "Success from final fallback" in result["response"]["completion"]
            assert call_count == 3  # All three models attempted

    def test_usage_tracking_and_analytics(self, bedrock_client):
        """Test usage tracking and analytics for AWS integration."""
        usage_tracker = bedrock_client.usage_tracker

        # Simulate various API calls
        test_calls = [
            {"model": "claude-3-sonnet", "tokens": 1000, "region": "us-east-1", "cost": 0.015},
            {"model": "claude-3-sonnet", "tokens": 500, "region": "us-east-1", "cost": 0.0075},
            {"model": "titan-text", "tokens": 800, "region": "us-west-2", "cost": 0.0008},
        ]

        for call in test_calls:
            usage_tracker.record_usage(
                model=call["model"],
                tokens=call["tokens"],
                region=call["region"],
                cost=call["cost"]
            )

        # Verify usage analytics
        analytics = usage_tracker.get_analytics()

        assert "total_calls" in analytics
        assert analytics["total_calls"] == 3

        assert "total_tokens" in analytics
        assert analytics["total_tokens"] == 2300

        assert "total_cost" in analytics
        assert abs(analytics["total_cost"] - 0.0233) < 0.001  # Approximate cost

        assert "model_usage" in analytics
        assert analytics["model_usage"]["claude-3-sonnet"] == 2
        assert analytics["model_usage"]["titan-text"] == 1

    def test_multi_region_load_balancing(self, model_router):
        """Test multi-region load balancing for high availability."""
        regions = ["us-east-1", "us-west-2", "eu-west-1"]
        region_calls = {region: 0 for region in regions}

        # Simulate load balancing across regions
        for i in range(30):
            selected_region = model_router.select_region_for_model("claude-3-sonnet", regions)
            region_calls[selected_region] += 1

        # Verify load distribution (should be roughly even)
        for region, calls in region_calls.items():
            assert 8 <= calls <= 12  # Roughly 10 calls per region (30/3)

        # Test region health checking
        unhealthy_regions = ["us-west-2"]  # Simulate unhealthy region

        for i in range(10):
            healthy_region = model_router.select_healthy_region(regions, unhealthy_regions)
            assert healthy_region != "us-west-2"
            assert healthy_region in ["us-east-1", "eu-west-1"]

    def test_enterprise_compliance_features(self, bedrock_client):
        """Test enterprise compliance features for AWS integration."""
        # Test data residency compliance
        eu_regions = ["eu-west-1", "eu-central-1"]

        for region in eu_regions:
            is_compliant = bedrock_client._check_data_residency_compliance("EU_GDPR", region)
            assert is_compliant is True

        # Test audit logging
        audit_log = bedrock_client.audit_log

        # Simulate audited operations
        bedrock_client._log_audit_event("model_invocation", {
            "model": "claude-3-sonnet",
            "user": "enterprise-user@company.com",
            "purpose": "content_generation",
            "data_classification": "internal"
        })

        bedrock_client._log_audit_event("model_invocation", {
            "model": "titan-text",
            "user": "contractor@external.com",
            "purpose": "research",
            "data_classification": "confidential"
        })

        # Verify audit trail
        audit_entries = audit_log.get_entries()
        assert len(audit_entries) >= 2

        # Check compliance reporting
        compliance_report = bedrock_client.generate_compliance_report("GDPR")
        assert "compliant" in compliance_report
        assert "violations" in compliance_report
        assert compliance_report["compliant"] is True  # Should be compliant

    @pytest.mark.parametrize("model_name,expected_family", [
        ("claude-3-sonnet", "claude"),
        ("titan-text-express", "titan"),
        ("claude-3-haiku", "claude"),
        ("amazon.qwen2-72b-instruct", "amazon"),
        ("meta.llama3-70b-instruct", "meta"),
    ])
    def test_model_family_detection(self, model_router, model_name, expected_family):
        """Test model family detection for routing optimization."""
        family = model_router.get_model_family(model_name)
        assert family == expected_family

    def test_cost_monitoring_and_alerts(self, bedrock_client):
        """Test cost monitoring and alerting for AWS usage."""
        cost_monitor = bedrock_client.cost_monitor

        # Set budget thresholds
        cost_monitor.set_budget_threshold("monthly", 100.0)
        cost_monitor.set_budget_threshold("daily", 5.0)

        # Simulate usage that triggers alerts
        test_usage = [
            {"cost": 3.0, "should_alert": False},  # Under daily limit
            {"cost": 4.0, "should_alert": True},   # Exceeds daily limit (7.0 > 5.0)
            {"cost": 2.0, "should_alert": True},   # Still over daily limit (9.0 > 5.0)
        ]

        alerts_triggered = []

        for usage in test_usage:
            cost_monitor.record_cost(usage["cost"])

            if cost_monitor.check_budget_alerts():
                alerts_triggered.append(True)
                # Reset for next test
                cost_monitor.current_daily_cost = 0
            else:
                alerts_triggered.append(False)

        # Verify alert triggering
        assert alerts_triggered[0] is False  # Under limit
        assert alerts_triggered[1] is True   # Over limit
        assert alerts_triggered[2] is True   # Still over limit

    def test_template_engine_aws_integration(self, bedrock_client):
        """Test template engine integration with AWS Bedrock."""
        template_engine = bedrock_client.template_engine

        # Test template processing with AWS-specific optimizations
        test_templates = {
            "code_review": {
                "template": "Review this {language} code for {issues}: {code}",
                "variables": ["language", "issues", "code"]
            },
            "documentation": {
                "template": "Generate documentation for {component} in {format} format",
                "variables": ["component", "format"]
            }
        }

        for template_name, template_config in test_templates.items():
            # Register template
            template_engine.register_template(template_name, template_config)

            # Test template rendering
            variables = {var: f"test_{var}" for var in template_config["variables"]}
            rendered = template_engine.render_template(template_name, variables)

            # Verify all variables replaced
            for var in template_config["variables"]:
                assert f"test_{var}" in rendered
                assert f"{{{var}}}" not in rendered

        # Test AWS token optimization
        long_prompt = "x" * 5000  # Very long prompt
        optimized = template_engine.optimize_for_tokens(long_prompt, "claude-3-sonnet")

        # Should be truncated or optimized for token limits
        assert len(optimized) <= len(long_prompt)

    def test_error_recovery_and_circuit_breaker(self, bedrock_client):
        """Test error recovery and circuit breaker patterns."""
        circuit_breaker = bedrock_client.circuit_breaker

        # Test successful calls
        for i in range(5):
            success = circuit_breaker.call(lambda: {"success": True})
            assert success["success"] is True

        # Test failure threshold
        failure_count = 0
        def failing_operation():
            nonlocal failure_count
            failure_count += 1
            raise Exception(f"Operation failed {failure_count}")

        # Trigger circuit breaker
        for i in range(circuit_breaker.failure_threshold + 1):
            try:
                circuit_breaker.call(failing_operation)
            except Exception:
                pass  # Expected failures

        # Circuit should now be open
        assert circuit_breaker.state == "open"

        # Test circuit breaker recovery
        import time
        time.sleep(circuit_breaker.recovery_timeout_seconds + 0.1)

        # Should attempt recovery
        def successful_operation():
            return {"recovered": True}

        result = circuit_breaker.call(successful_operation)
        assert result["recovered"] is True
        assert circuit_breaker.state == "closed"

    def test_model_version_compatibility(self, model_router):
        """Test model version compatibility and migration."""
        # Test version compatibility matrix
        compatibility = model_router.check_model_compatibility("claude-3-sonnet", "claude-3-haiku")
        assert compatibility["compatible"] is True
        assert "migration_path" in compatibility

        # Test deprecated model handling
        deprecated_models = model_router.get_deprecated_models()
        assert isinstance(deprecated_models, list)

        # Test version upgrade suggestions
        upgrade_suggestion = model_router.suggest_model_upgrade("claude-2", "text-generation")
        assert upgrade_suggestion is not None
        assert "claude-3" in upgrade_suggestion or "claude-2" in upgrade_suggestion
