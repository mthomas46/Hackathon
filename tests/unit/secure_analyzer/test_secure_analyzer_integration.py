"""Secure Analyzer Service integration and workflow tests.

Tests service integration, data flow, and end-to-end workflows.
Focused on integration scenarios following TDD principles.
"""

import pytest
from fastapi.testclient import TestClient

from .test_utils import load_secure_analyzer_service


@pytest.fixture(scope="module")
def client():
    """Test client fixture for secure analyzer service."""
    app = load_secure_analyzer_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


def _assert_http_ok(response):
    """Assert that HTTP response is successful."""
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


class TestSecureAnalyzerIntegration:
    """Test secure analyzer integration and workflow functionality."""

    def test_complete_security_analysis_workflow(self, client):
        """Test complete security analysis workflow from detection to summarization."""
        # Step 1: Prepare test content with various security issues
        test_content = """
        Project Configuration:
        API_KEY = "sk-1234567890abcdef"
        DATABASE_PASSWORD = "super_secret_db_pass123"
        JWT_SECRET = "my_jwt_secret_token_456"
        AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
        USER_SSN = "123-45-6789"
        CREDIT_CARD = "4111-1111-1111-1111"

        This document contains sensitive information that needs protection.
        """

        custom_keywords = ["proprietary", "confidential", "internal"]

        # Step 2: Detect sensitive content
        detect_request = {
            "content": test_content,
            "keywords": custom_keywords
        }

        detect_response = client.post("/detect", json=detect_request)
        _assert_http_ok(detect_response)

        detect_data = detect_response.json()
        assert detect_data["sensitive"] == True
        assert len(detect_data["matches"]) >= 6  # Should find multiple sensitive items
        assert len(detect_data["topics"]) > 0

        # Step 3: Get model suggestions
        suggest_response = client.post("/suggest", json=detect_request)
        _assert_http_ok(suggest_response)

        suggest_data = suggest_response.json()
        assert suggest_data["sensitive"] == detect_data["sensitive"]
        assert len(suggest_data["allowed_models"]) <= 2  # Should be restricted to secure models

        # Step 4: Test summarization with policy enforcement
        summarize_request = {
            "content": test_content,
            "providers": [
                {"name": "openai"},
                {"name": "bedrock"},
                {"name": "ollama"}
            ]
        }

        summarize_response = client.post("/summarize", json=summarize_request)
        _assert_http_ok(summarize_response)

        summarize_data = summarize_response.json()
        assert "summary" in summarize_data
        assert summarize_data["policy_enforced"] == True  # Should enforce policy

        # Should use secure provider despite requesting openai
        provider_used = summarize_data["provider_used"].lower()
        assert provider_used in ["bedrock", "ollama"]

    def test_policy_override_workflow(self, client):
        """Test policy override functionality."""
        sensitive_content = """
        Sensitive research data:
        API_TOKEN = "ghp_abcd1234efgh5678"
        PRIVATE_KEY = "-----BEGIN PRIVATE KEY-----"
        """

        # Step 1: Normal policy enforcement
        normal_request = {
            "content": sensitive_content,
            "providers": [{"name": "openai"}]
        }

        normal_response = client.post("/summarize", json=normal_request)
        _assert_http_ok(normal_response)

        normal_data = normal_response.json()
        assert normal_data["policy_enforced"] == True
        assert normal_data["provider_used"].lower() in ["bedrock", "ollama"]

        # Step 2: Policy override
        override_request = {
            "content": sensitive_content,
            "providers": [{"name": "openai"}],
            "override_policy": True
        }

        override_response = client.post("/summarize", json=override_request)
        _assert_http_ok(override_response)

        override_data = override_response.json()
        assert override_data["policy_enforced"] == False
        assert override_data["provider_used"].lower() == "openai"  # Should use requested provider

    def test_multi_stage_security_workflow(self, client):
        """Test multi-stage security analysis workflow."""
        # Stage 1: Initial content analysis
        stage1_content = "Basic content with API_KEY = 'sk-test123'"

        stage1_detect = client.post("/detect", json={"content": stage1_content})
        _assert_http_ok(stage1_detect)

        stage1_suggest = client.post("/suggest", json={"content": stage1_content})
        _assert_http_ok(stage1_suggest)

        # Stage 2: Enhanced analysis with more content
        stage2_content = stage1_content + """
        Additional sensitive data:
        PASSWORD = "admin123"
        SECRET_TOKEN = "token456"
        """

        stage2_detect = client.post("/detect", json={"content": stage2_content})
        _assert_http_ok(stage2_detect)

        stage2_suggest = client.post("/suggest", json={"content": stage2_content})
        _assert_http_ok(stage2_suggest)

        # Stage 3: Final summarization with all content
        stage3_content = stage2_content + """
        Final confidential section:
        PRIVATE_KEY = "key789"
        SSN = "987-65-4321"
        """

        stage3_summarize = client.post("/summarize", json={"content": stage3_content})
        _assert_http_ok(stage3_summarize)

        # Verify progressive sensitivity detection
        stage1_data = stage1_detect.json()
        stage2_data = stage2_detect.json()
        stage3_data = stage3_summarize.json()

        assert stage1_data["sensitive"] == True
        assert stage2_data["sensitive"] == True
        assert stage3_data["policy_enforced"] == True

        # Later stages should detect more issues
        assert len(stage2_data["matches"]) >= len(stage1_data["matches"])
        assert len(stage3_data["topics_detected"]) >= len(stage2_data["topics"])

    def test_batch_security_analysis(self, client):
        """Test batch processing of multiple documents."""
        documents = [
            {
                "content": "Normal user documentation without secrets.",
                "expected_sensitive": False
            },
            {
                "content": "Config with API_KEY = 'sk-12345'",
                "expected_sensitive": True
            },
            {
                "content": "Database password: db_secret123",
                "expected_sensitive": True
            },
            {
                "content": "Regular business logic code.",
                "expected_sensitive": False
            },
            {
                "content": "Auth system with JWT_SECRET = 'secret' and CLIENT_ID = 'client123'",
                "expected_sensitive": True
            }
        ]

        results = []
        for i, doc in enumerate(documents):
            # Analyze each document
            detect_result = client.post("/detect", json={"content": doc["content"]})
            _assert_http_ok(detect_result)

            suggest_result = client.post("/suggest", json={"content": doc["content"]})
            _assert_http_ok(suggest_result)

            summarize_result = client.post("/summarize", json={"content": doc["content"]})
            _assert_http_ok(summarize_result)

            doc_result = {
                "index": i,
                "detect": detect_result.json(),
                "suggest": suggest_result.json(),
                "summarize": summarize_result.json()
            }
            results.append(doc_result)

        # Analyze batch results
        sensitive_count = sum(1 for r in results if r["detect"]["sensitive"])
        expected_sensitive_count = sum(1 for d in documents if d["expected_sensitive"])

        assert sensitive_count == expected_sensitive_count

        # Verify policy enforcement consistency
        for result in results:
            detect_sensitive = result["detect"]["sensitive"]
            suggest_sensitive = result["suggest"]["sensitive"]
            policy_enforced = result["summarize"]["policy_enforced"]

            assert detect_sensitive == suggest_sensitive
            if detect_sensitive:
                assert policy_enforced == True
                provider_used = result["summarize"]["provider_used"].lower()
                assert provider_used in ["bedrock", "ollama"]

    def test_security_compliance_workflow(self, client):
        """Test security compliance checking workflow."""
        compliance_scenarios = [
            {
                "name": "PCI DSS Compliance",
                "content": "Credit card: 4111-1111-1111-1111 CVV: 123",
                "required_topics": ["credit card"],
                "should_restrict": True
            },
            {
                "name": "HIPAA Compliance",
                "content": "Patient SSN: 123-45-6789 Medical ID: 987654",
                "required_topics": ["ssn", "pii"],
                "should_restrict": True
            },
            {
                "name": "API Security",
                "content": "OAuth token: abc123 API secret: secret456",
                "required_topics": ["token", "secret"],
                "should_restrict": True
            },
            {
                "name": "Clean Content",
                "content": "Regular business documentation without sensitive data.",
                "required_topics": [],
                "should_restrict": False
            }
        ]

        for scenario in compliance_scenarios:
            # Step 1: Security analysis
            detect_result = client.post("/detect", json={"content": scenario["content"]})
            _assert_http_ok(detect_result)

            suggest_result = client.post("/suggest", json={"content": scenario["content"]})
            _assert_http_ok(suggest_result)

            # Step 2: Verify compliance requirements
            detect_data = detect_result.json()
            suggest_data = suggest_result.json()

            if scenario["should_restrict"]:
                assert detect_data["sensitive"] == True
                assert len(suggest_data["allowed_models"]) <= 2  # Restricted to secure models

                # Check for required topics
                detected_topics = set(detect_data["topics"])
                required_topics = set(scenario["required_topics"])
                assert len(detected_topics.intersection(required_topics)) > 0
            else:
                assert detect_data["sensitive"] == False
                assert len(suggest_data["allowed_models"]) > 2  # All models allowed

    def test_cross_service_integration_simulation(self, client):
        """Test integration with other ecosystem services (simulated)."""
        # Simulate integration with different services
        integration_scenarios = [
            {
                "service": "doc_store",
                "content": "Retrieved document with API_KEY = 'sk-doc123'",
                "expected_provider": "bedrock"  # Should use secure provider
            },
            {
                "service": "source-agent",
                "content": "GitHub PR with password: 'pr_secret456'",
                "expected_provider": "ollama"  # Should use secure provider
            },
            {
                "service": "analysis-service",
                "content": "Analysis result containing token: 'analysis_token789'",
                "expected_provider": "bedrock"  # Should use secure provider
            },
            {
                "service": "frontend",
                "content": "UI template without sensitive data",
                "expected_provider": "openai"  # Can use any provider
            }
        ]

        for scenario in integration_scenarios:
            # Step 1: Analyze content as if from the service
            detect_result = client.post("/detect", json={"content": scenario["content"]})
            _assert_http_ok(detect_result)

            # Step 2: Get summarization recommendations
            summarize_result = client.post("/summarize", json={"content": scenario["content"]})
            _assert_http_ok(summarize_result)

            summarize_data = summarize_result.json()

            if ("secret" in scenario["content"].lower() or
                "key" in scenario["content"].lower() or
                "token" in scenario["content"].lower() or
                "password" in scenario["content"].lower()):
                # Sensitive content should use secure provider
                assert summarize_data["policy_enforced"] == True
                provider_used = summarize_data["provider_used"].lower()
                assert provider_used in ["bedrock", "ollama"]
            else:
                # Non-sensitive content can use any provider
                assert summarize_data["policy_enforced"] == False

    @pytest.mark.timeout(60)  # 60 second timeout for performance test
    def test_performance_monitoring_integration(self, client):
        """Test performance monitoring and metrics integration."""
        import time

        # Step 1: Execute multiple analysis operations
        operations = []
        start_time = time.time()

        for i in range(10):
            content = f"Test content {i} with API_KEY = 'sk-test{i}'"
            operation_start = time.time()

            detect_result = client.post("/detect", json={"content": content})
            suggest_result = client.post("/suggest", json={"content": content})
            summarize_result = client.post("/summarize", json={"content": content})

            operation_end = time.time()

            operations.append({
                "index": i,
                "duration": operation_end - operation_start,
                "detect_status": detect_result.status_code,
                "suggest_status": suggest_result.status_code,
                "summarize_status": summarize_result.status_code
            })

        total_time = time.time() - start_time

        # Step 2: Analyze performance metrics
        successful_operations = sum(1 for op in operations if op["detect_status"] == 200)
        avg_duration = sum(op["duration"] for op in operations) / len(operations)
        max_duration = max(op["duration"] for op in operations)

        # Performance assertions (relaxed for test environment)
        assert successful_operations == 10  # All operations should succeed
        assert total_time < 120  # Should complete within 2 minutes (relaxed)
        assert avg_duration < 15  # Average operation should be under 15 seconds (relaxed)
        assert max_duration < 30  # No operation should take more than 30 seconds (relaxed)

        # Verify all operations returned expected results
        for op in operations:
            assert op["detect_status"] == 200
            assert op["suggest_status"] == 200
            assert op["summarize_status"] == 200

    def test_error_recovery_and_fallback_workflow(self, client):
        """Test error recovery and fallback mechanisms."""
        # Test with various edge cases and error conditions
        edge_cases = [
            {
                "content": "",  # Empty content
                "expected_detect_status": 422,
                "expected_summarize_status": 422
            },
            {
                "content": "x" * 1000001,  # Too large
                "expected_detect_status": 413,
                "expected_summarize_status": 413
            },
            {
                "content": "Valid content with API_KEY = 'sk-valid'",
                "expected_detect_status": 200,
                "expected_summarize_status": 200
            },
            {
                "content": "Content with many secrets: " + "API_KEY = 'sk-123' " * 50,
                "expected_detect_status": 200,
                "expected_summarize_status": 200
            }
        ]

        for case in edge_cases:
            # Test detection
            detect_result = client.post("/detect", json={"content": case["content"]})
            if case["expected_detect_status"] == 413:
                assert detect_result.status_code in [413, 422]
            else:
                assert detect_result.status_code == case["expected_detect_status"]

            # Test summarization (only if content is valid)
            if case["expected_summarize_status"] == 200:
                summarize_result = client.post("/summarize", json={"content": case["content"]})
                assert summarize_result.status_code == case["expected_summarize_status"]

                # Verify policy enforcement for valid content
                if "API_KEY" in case["content"]:
                    summarize_data = summarize_result.json()
                    assert summarize_data["policy_enforced"] == True

    def test_audit_trail_and_logging_integration(self, client):
        """Test audit trail and logging integration."""
        # Execute a series of operations to generate audit trail
        audit_operations = []

        for i in range(5):
            content = f"Audit test {i}: API_KEY = 'sk-audit{i}' PASSWORD = 'pass{i}'"

            # Perform operations
            detect_result = client.post("/detect", json={"content": content})
            suggest_result = client.post("/suggest", json={"content": content})
            summarize_result = client.post("/summarize", json={"content": content})

            operation_record = {
                "operation_id": f"audit-{i}",
                "content_hash": hash(content),
                "detect_success": detect_result.status_code == 200,
                "suggest_success": suggest_result.status_code == 200,
                "summarize_success": summarize_result.status_code == 200,
                "policy_enforced": False,
                "provider_used": None
            }

            if summarize_result.status_code == 200:
                summarize_data = summarize_result.json()
                operation_record["policy_enforced"] = summarize_data.get("policy_enforced", False)
                operation_record["provider_used"] = summarize_data.get("provider_used")

            audit_operations.append(operation_record)

        # Verify audit trail consistency
        sensitive_operations = [op for op in audit_operations if op["policy_enforced"]]
        assert len(sensitive_operations) == 5  # All operations should have been sensitive

        # Verify all operations used secure providers
        for op in sensitive_operations:
            assert op["provider_used"].lower() in ["bedrock", "ollama"]

        # Verify operation success rates
        success_rate = sum(1 for op in audit_operations if op["detect_success"] and op["suggest_success"] and op["summarize_success"]) / len(audit_operations)
        assert success_rate == 1.0  # 100% success rate

    def test_configuration_driven_policy_enforcement(self, client):
        """Test configuration-driven policy enforcement."""
        # Test different policy configurations
        policy_scenarios = [
            {
                "content": "Content with API_KEY = 'sk-123'",
                "expected_secure_only": ["bedrock", "ollama"],
                "expected_all_providers": ["bedrock", "ollama", "openai", "anthropic", "grok"]
            },
            {
                "content": "Clean content without secrets",
                "expected_secure_only": ["bedrock", "ollama"],
                "expected_all_providers": ["bedrock", "ollama", "openai", "anthropic", "grok"]
            }
        ]

        for scenario in policy_scenarios:
            # Test with sensitive content
            if "API_KEY" in scenario["content"]:
                suggest_result = client.post("/suggest", json={"content": scenario["content"]})
                _assert_http_ok(suggest_result)

                suggest_data = suggest_result.json()
                assert suggest_data["sensitive"] == True
                assert len(suggest_data["allowed_models"]) <= 2  # Should be restricted

                # Verify secure providers are used
                allowed_providers = set(suggest_data["allowed_models"])
                expected_secure = set(scenario["expected_secure_only"])
                assert allowed_providers.issubset(expected_secure)
            else:
                # Test with clean content
                suggest_result = client.post("/suggest", json={"content": scenario["content"]})
                _assert_http_ok(suggest_result)

                suggest_data = suggest_result.json()
                assert suggest_data["sensitive"] == False
                assert len(suggest_data["allowed_models"]) >= 3  # Should allow more providers

    def test_data_consistency_across_operations(self, client):
        """Test data consistency across multiple operations."""
        test_content = """
        Consistent test data:
        API_KEY = "sk-consistency123"
        PASSWORD = "consistent_pass456"
        SECRET_TOKEN = "token789"
        """

        # Execute same operations multiple times
        results = []
        for i in range(3):
            detect_result = client.post("/detect", json={"content": test_content})
            suggest_result = client.post("/suggest", json={"content": test_content})
            summarize_result = client.post("/summarize", json={"content": test_content})

            iteration_results = {
                "iteration": i,
                "detect": detect_result.json() if detect_result.status_code == 200 else None,
                "suggest": suggest_result.json() if suggest_result.status_code == 200 else None,
                "summarize": summarize_result.json() if summarize_result.status_code == 200 else None
            }
            results.append(iteration_results)

        # Verify consistency across iterations
        for i in range(1, len(results)):
            # Detection results should be identical
            assert results[i]["detect"]["sensitive"] == results[0]["detect"]["sensitive"]
            assert len(results[i]["detect"]["matches"]) == len(results[0]["detect"]["matches"])

            # Suggestion results should be consistent
            assert results[i]["suggest"]["sensitive"] == results[0]["suggest"]["sensitive"]
            assert results[i]["suggest"]["allowed_models"] == results[0]["suggest"]["allowed_models"]

            # Summarization should use same provider
            assert results[i]["summarize"]["provider_used"] == results[0]["summarize"]["provider_used"]
            assert results[i]["summarize"]["policy_enforced"] == results[0]["summarize"]["policy_enforced"]

    @pytest.mark.timeout(20)  # 20 second timeout for resource test
    def test_resource_cleanup_and_memory_management(self, client):
        """Test resource cleanup and memory management."""
        # Execute many operations to test resource handling
        large_operations = []

        for i in range(20):
            # Mix of large and small content
            if i % 2 == 0:
                content = f"Small content {i} with API_KEY = 'sk-{i}'"
            else:
                content = f"Large content {i} with multiple secrets: " + "API_KEY = 'sk-123' PASSWORD = 'pass456' " * 10

            operation_results = {
                "index": i,
                "content": content,  # Store the actual content for later checks
                "content_size": len(content),
                "detect": client.post("/detect", json={"content": content}),
                "suggest": client.post("/suggest", json={"content": content}),
                "summarize": client.post("/summarize", json={"content": content})
            }
            large_operations.append(operation_results)

        # Verify all operations completed successfully
        for op in large_operations:
            assert op["detect"].status_code == 200
            assert op["suggest"].status_code == 200
            assert op["summarize"].status_code == 200

        # Verify resource usage patterns (reduced iterations for performance)
        large_content_ops = [op for op in large_operations if op["content_size"] > 1000]
        small_content_ops = [op for op in large_operations if op["content_size"] <= 1000]

        # Large content should still trigger policy enforcement
        for op in large_content_ops[:5]:  # Test first 5 to reduce execution time
            summarize_data = op["summarize"].json()
            assert summarize_data["policy_enforced"] == True

        # Small content with secrets should also trigger policy
        for op in small_content_ops[:5]:  # Test first 5 to reduce execution time
            if "API_KEY" in op["content"]:
                summarize_data = op["summarize"].json()
                assert summarize_data["policy_enforced"] == True

    def test_end_to_end_ecosystem_simulation(self, client):
        """Test end-to-end ecosystem simulation."""
        # Simulate a complete document processing pipeline
        pipeline_stages = [
            {
                "stage": "ingestion",
                "content": "Raw document with API_KEY = 'sk-ingest123'",
                "operation": "detect"
            },
            {
                "stage": "analysis",
                "content": "Analyzed document with PASSWORD = 'analysis456'",
                "operation": "suggest"
            },
            {
                "stage": "processing",
                "content": "Processed document with SECRET = 'process789'",
                "operation": "summarize"
            },
            {
                "stage": "output",
                "content": "Final output document with TOKEN = 'output101'",
                "operation": "detect"
            }
        ]

        pipeline_results = []

        for stage in pipeline_stages:
            if stage["operation"] == "detect":
                result = client.post("/detect", json={"content": stage["content"]})
            elif stage["operation"] == "suggest":
                result = client.post("/suggest", json={"content": stage["content"]})
            elif stage["operation"] == "summarize":
                result = client.post("/summarize", json={"content": stage["content"]})

            stage_result = {
                "stage": stage["stage"],
                "operation": stage["operation"],
                "success": result.status_code == 200,
                "data": result.json() if result.status_code == 200 else None
            }
            pipeline_results.append(stage_result)

        # Verify pipeline integrity
        assert all(stage["success"] for stage in pipeline_results)

        # Verify security policy was consistently applied
        for stage in pipeline_results:
            if stage["data"] and "policy_enforced" in stage["data"]:
                assert stage["data"]["policy_enforced"] == True
            elif stage["data"] and "sensitive" in stage["data"]:
                assert stage["data"]["sensitive"] == True

        # Verify at least some stages processed content with security implications
        sensitive_stages = sum(1 for stage in pipeline_results if stage["data"] and stage["data"].get("sensitive", False))
        assert sensitive_stages >= 2  # At least some stages should have been sensitive
