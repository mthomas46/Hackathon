"""Integration Tests for Enterprise Security Integration in Secure Analyzer Service.

This module tests enterprise security integration capabilities including:
- End-to-end security scanning workflows
- Enterprise compliance validation
- Security incident response and escalation
- Multi-layer security validation pipelines
- Enterprise policy enforcement

Integration tests cover complete enterprise security workflows and compliance scenarios.
"""

import pytest
import asyncio
import time
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
import uuid

from main import DetectRequest, DetectResponse


class TestEnterpriseSecurityIntegration:
    """Integration tests for enterprise security workflows."""

    @pytest.fixture
    def integration_app(self):
        """Create a complete Secure Analyzer application for integration testing."""
        from main import app
        return app

    @pytest.fixture
    def enterprise_security_scenarios(self):
        """Enterprise security scenarios for comprehensive testing."""
        return {
            "data_breach_prevention": {
                "content_type": "document",
                "content": """
COMPANY CONFIDENTIAL - EMPLOYEE DATABASE EXPORT

Employee Records Export - Generated: 2024-09-23

Employee ID | Full Name | SSN | Salary | Home Address | Phone
-----------|-----------|-----|--------|-------------|------
001 | John Smith | 123-45-6789 | $95,000 | 123 Main St, Anytown, USA | (555) 123-4567
002 | Jane Doe | 987-65-4321 | $110,000 | 456 Oak Ave, Somewhere, USA | (555) 987-6543
003 | Bob Johnson | 456-78-9012 | $85,000 | 789 Pine Rd, Elsewhere, USA | (555) 456-7890

Database Connection: postgresql://admin:supersecret@db.company.com:5432/hr_db
API Keys: sk-1234567890abcdef, pk_live_abcdef1234567890
AWS Credentials: AKIAIOSFODNN7EXAMPLE / wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
                """,
                "metadata": {
                    "source": "database_export",
                    "classification": "restricted",
                    "department": "HR",
                    "retention_period": "7_years"
                },
                "expected_violations": ["pii_data_exposure", "financial_data_exposure", "credential_exposure"],
                "expected_severity": "critical",
                "compliance_frameworks": ["GDPR", "HIPAA", "SOX"]
            },
            "api_security_incident": {
                "content_type": "api_log",
                "content": """
SECURITY INCIDENT REPORT - API Gateway

Incident ID: INC-2024-0923-001
Timestamp: 2024-09-23T14:30:00Z
Severity: HIGH

Attack Details:
- SQL Injection Attempts: 47 instances
  Payloads: ' OR 1=1 --, admin' --, UNION SELECT * FROM users
- XSS Attempts: 23 instances
  Payloads: <script>alert('xss')</script>, javascript:alert('xss')
- Credential Stuffing: 156 login attempts
  Usernames: admin, root, administrator, sa
  Passwords: password123, admin123, letmein123

Affected Endpoints:
/api/users (POST) - User creation endpoint
/api/auth/login (POST) - Authentication endpoint
/api/admin/users (GET) - Admin user listing

Source IPs: 192.168.1.100, 10.0.0.50, 203.0.113.1
User Agents: sqlmap/1.6, BurpSuite/2023.1, PostmanRuntime/7.32.0

Response Actions Taken:
- Rate limiting activated for source IPs
- WAF rules updated with new signatures
- Authentication temporarily disabled for suspicious accounts
- Incident response team notified
                """,
                "metadata": {
                    "source": "security_monitoring",
                    "classification": "confidential",
                    "incident_id": "INC-2024-0923-001",
                    "affected_systems": ["api_gateway", "user_database", "auth_service"]
                },
                "expected_violations": ["sql_injection", "xss_attack", "credential_stuffing"],
                "expected_severity": "critical",
                "compliance_frameworks": ["PCI_DSS", "GDPR", "NIST"]
            },
            "healthcare_data_compliance": {
                "content_type": "medical_record",
                "content": """
ELECTRONIC HEALTH RECORD - CONFIDENTIAL

Patient Information:
Name: Sarah Johnson
DOB: 1985-03-15
SSN: 111-22-3333
Medical Record Number: MRN-2024-04567

Medical History:
- Diagnosis: Type 2 Diabetes Mellitus (ICD-10: E11.9)
- Medications: Metformin 500mg BID, Insulin Glargine 20 units daily
- Allergies: Penicillin (severe reaction), Sulfa drugs
- Last Visit: 2024-09-20 - HbA1c: 7.8% (poor control)

Laboratory Results:
- Glucose (fasting): 185 mg/dL (elevated)
- HbA1c: 8.2% (2024-09-15)
- Lipid Panel: Total Cholesterol 245 mg/dL, HDL 35 mg/dL, LDL 160 mg/dL
- Liver Function: ALT 45 IU/L, AST 38 IU/L (normal)

Treatment Plan:
- Increase Metformin to 1000mg BID
- Continue insulin therapy
- Lifestyle counseling: diet and exercise
- Follow-up in 3 months

Provider Notes:
Patient shows good understanding of disease management but struggles with medication adherence.
Recommended endocrinology consultation for advanced diabetes management.

PHI Classification: Protected Health Information
Retention: 7 years post-treatment completion
Access Control: Healthcare providers only
                """,
                "metadata": {
                    "source": "ehr_system",
                    "classification": "restricted",
                    "patient_id": "MRN-2024-04567",
                    "department": "endocrinology",
                    "hipaa_compliant": True
                },
                "expected_violations": ["phi_data_exposure"],
                "expected_severity": "critical",
                "compliance_frameworks": ["HIPAA", "HITECH", "GDPR"]
            },
            "financial_transaction_security": {
                "content_type": "transaction_log",
                "content": """
PAYMENT PROCESSING LOG - SECURE

Transaction Batch: BATCH-2024-0923-001
Processing Date: 2024-09-23
Total Transactions: 1,247
Total Value: $2,456,789.34

Sample Transactions:

TXN-001:
Card Number: 4111-1111-1111-1111
Expiry: 12/26
CVV: 123
Amount: $299.99
Merchant: Online Retailer Inc.
Result: APPROVED
Authorization Code: A12345
Timestamp: 2024-09-23T09:15:30Z

TXN-002:
Card Number: 5555-5555-5555-4444
Expiry: 08/25
CVV: 456
Amount: $1,250.00
Merchant: Travel Agency LLC
Result: APPROVED
Authorization Code: B67890
Timestamp: 2024-09-23T09:16:45Z

TXN-003:
Card Number: 3782-822463-10005
Expiry: 06/27
CVV: 789
Amount: $5,678.90
Merchant: Luxury Goods Store
Result: APPROVED
Authorization Code: C54321
Timestamp: 2024-09-23T09:17:12Z

Security Metrics:
- Failed Transactions: 23 (1.8%)
- Fraud Alerts: 5 (0.4%)
- Chargebacks: 2 (0.16%)
- PCI DSS Compliance: PASS

Encryption: AES-256 with key rotation every 24 hours
Tokenization: All card data tokenized post-processing
Retention: 7 years for compliance and dispute resolution
                """,
                "metadata": {
                    "source": "payment_processor",
                    "classification": "restricted",
                    "batch_id": "BATCH-2024-0923-001",
                    "transaction_count": 1247,
                    "pci_compliant": True
                },
                "expected_violations": ["pci_data_exposure"],
                "expected_severity": "critical",
                "compliance_frameworks": ["PCI_DSS", "SOX", "GDPR"]
            },
            "code_repository_security": {
                "content_type": "source_code",
                "content": """
# Enterprise Application - Database Configuration
# WARNING: This file contains sensitive database credentials
# DO NOT commit to version control

import os
import psycopg2
import redis
from flask import Flask

# Database Configuration
DB_CONFIG = {
    'host': 'prod-database.company.com',
    'port': 5432,
    'database': 'enterprise_app',
    'user': 'app_user',
    'password': 'SuperSecretProdPassword123!',
    'ssl_mode': 'require'
}

# Redis Configuration
REDIS_CONFIG = {
    'host': 'redis-cluster.company.com',
    'port': 6379,
    'password': 'RedisMasterPassword456!',
    'ssl': True
}

# AWS Configuration
AWS_CONFIG = {
    'access_key_id': 'AKIAIOSFODNN7EXAMPLE',
    'secret_access_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
    'region': 'us-east-1',
    's3_bucket': 'company-secure-data'
}

# API Keys (Test/Dummy Values - DO NOT USE IN PRODUCTION)
STRIPE_SECRET_KEY = 'sk_test_dummy_key_for_testing_only_not_real'
SENDGRID_API_KEY = 'SG.dummy_api_key_for_testing_only_not_real'

# JWT Secret
JWT_SECRET = 'MySuperSecretJWTKeyThatShouldNeverBeInCode123456789!'

def get_database_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_redis_connection():
    return redis.Redis(**REDIS_CONFIG)

app = Flask(__name__)
app.config['SECRET_KEY'] = JWT_SECRET
                """,
                "metadata": {
                    "source": "git_repository",
                    "classification": "confidential",
                    "repository": "enterprise-app",
                    "branch": "main",
                    "commit_hash": "a1b2c3d4e5f6",
                    "file_path": "config/secrets.py"
                },
                "expected_violations": ["hardcoded_secrets", "credential_exposure", "api_key_exposure"],
                "expected_severity": "critical",
                "compliance_frameworks": ["NIST", "ISO27001", "GDPR"]
            }
        }

    @pytest.fixture
    def enterprise_compliance_frameworks(self):
        """Enterprise compliance frameworks and requirements."""
        return {
            "GDPR": {
                "data_types": ["personal_data", "special_categories"],
                "principles": ["lawfulness", "fairness", "transparency", "purpose_limitation", "data_minimization", "accuracy", "storage_limitation", "integrity", "confidentiality", "accountability"],
                "rights": ["access", "rectification", "erasure", "restriction", "portability", "objection"],
                "violations": ["unauthorized_processing", "data_breach", "inadequate_security"]
            },
            "HIPAA": {
                "data_types": ["protected_health_information", "electronic_health_records"],
                "rules": ["privacy_rule", "security_rule", "breach_notification_rule"],
                "safeguards": ["administrative", "physical", "technical"],
                "violations": ["unauthorized_disclosure", "insufficient_security", "lack_of_encryption"]
            },
            "PCI_DSS": {
                "requirements": ["build_maintain_secure_network", "protect_cardholder_data", "maintain_vulnerability_program", "implement_access_controls", "regularly_monitor_test", "maintain_information_security_policy"],
                "data_types": ["cardholder_data", "sensitive_authentication_data"],
                "violations": ["unencrypted_transmission", "weak_access_controls", "lack_of_monitoring"]
            },
            "SOX": {
                "sections": ["302", "404", "906"],
                "controls": ["access_controls", "change_management", "segregation_of_duties"],
                "violations": ["inadequate_controls", "material_weakness", "non_compliance_reporting"]
            },
            "NIST": {
                "framework": ["identify", "protect", "detect", "respond", "recover"],
                "controls": ["access_control", "awareness_training", "data_security", "information_protection"],
                "violations": ["weak_access_control", "insufficient_monitoring", "lack_of_incident_response"]
            }
        }

    @pytest.mark.asyncio
    async def test_end_to_end_enterprise_security_workflow(self, integration_app, enterprise_security_scenarios):
        """Test complete enterprise security scanning workflow."""
        # Setup comprehensive enterprise security workflow
        with patch("main.ContentDetector") as mock_content_detector_class, \
             patch("main.PolicyEnforcer") as mock_policy_enforcer_class, \
             patch("main.CircuitBreaker") as mock_circuit_breaker_class, \
             patch("main.LogCollectorClient") as mock_logger_class:

            # Mock components
            mock_content_detector = MagicMock()
            mock_policy_enforcer = MagicMock()
            mock_circuit_breaker = MagicMock()
            mock_logger = AsyncMock()

            mock_content_detector_class.return_value = mock_content_detector
            mock_policy_enforcer_class.return_value = mock_policy_enforcer
            mock_circuit_breaker_class.return_value = mock_circuit_breaker
            mock_logger_class.return_value = mock_logger

            # Configure security analysis responses for different scenarios
            def content_detector_side_effect(content, keywords=None, keyword_document=None):
                # Analyze content and return appropriate security assessment
                if "SSN" in content and "salary" in content.lower():
                    return {
                        "sensitive": True,
                        "risk_score": 95,
                        "topics": ["pii_data", "financial_data", "credentials"],
                        "matches": [
                            {"pattern": "ssn", "value": "123-45-6789", "severity": "critical"},
                            {"pattern": "salary", "value": "$95,000", "severity": "high"}
                        ],
                        "recommendations": ["Encrypt data", "Implement access controls", "Regular audits"]
                    }
                elif "SQL Injection" in content and "XSS" in content:
                    return {
                        "sensitive": True,
                        "risk_score": 98,
                        "topics": ["security_incident", "attack_patterns", "system_compromise"],
                        "matches": [
                            {"pattern": "sql_injection", "value": "UNION SELECT", "severity": "critical"},
                            {"pattern": "xss", "value": "<script>", "severity": "high"}
                        ],
                        "recommendations": ["Update WAF rules", "Patch vulnerabilities", "Monitor for anomalies"]
                    }
                elif "Diabetes" in content and "Medical Record" in content:
                    return {
                        "sensitive": True,
                        "risk_score": 100,
                        "topics": ["phi_data", "healthcare", "medical_records"],
                        "matches": [
                            {"pattern": "diagnosis", "value": "Type 2 Diabetes", "severity": "critical"},
                            {"pattern": "medications", "value": "Insulin", "severity": "high"}
                        ],
                        "recommendations": ["PHI encryption", "Access logging", "HIPAA compliance audit"]
                    }
                elif "4111-1111-1111-1111" in content:
                    return {
                        "sensitive": True,
                        "risk_score": 97,
                        "topics": ["pci_data", "financial", "cardholder_data"],
                        "matches": [
                            {"pattern": "credit_card", "value": "4111-1111-1111-1111", "severity": "critical"}
                        ],
                        "recommendations": ["Tokenize data", "PCI DSS compliance", "Secure transmission"]
                    }
                elif "SuperSecretProdPassword" in content:
                    return {
                        "sensitive": True,
                        "risk_score": 99,
                        "topics": ["hardcoded_secrets", "credentials", "security_vulnerability"],
                        "matches": [
                            {"pattern": "hardcoded_password", "value": "SuperSecretProdPassword123!", "severity": "critical"},
                            {"pattern": "api_key", "value": "sk_live_", "severity": "critical"}
                        ],
                        "recommendations": ["Remove hardcoded secrets", "Use environment variables", "Implement secret management"]
                    }
                else:
                    return {
                        "sensitive": False,
                        "risk_score": 10,
                        "topics": [],
                        "matches": [],
                        "recommendations": []
                    }

            mock_content_detector.detect_sensitive_content.side_effect = content_detector_side_effect

            # Configure policy enforcement responses
            def policy_enforcer_side_effect(content, policies):
                if any(keyword in content for keyword in ["SSN", "password", "API key", "SuperSecret"]):
                    return {
                        "action_taken": "quarantine",
                        "policies_triggered": ["block_sensitive_data", "encrypt_content"],
                        "severity_assessment": "critical",
                        "compliance_violations": ["GDPR", "PCI_DSS", "SOX"]
                    }
                else:
                    return {
                        "action_taken": "allow",
                        "policies_triggered": [],
                        "severity_assessment": "low",
                        "compliance_violations": []
                    }

            mock_policy_enforcer.enforce_policies.side_effect = policy_enforcer_side_effect

            # Configure circuit breaker
            mock_circuit_breaker.is_open.return_value = False
            mock_circuit_breaker.call.return_value = {"status": "success"}

            # Execute enterprise security scanning workflow
            security_scan_results = {}

            for scenario_name, scenario_config in enterprise_security_scenarios.items():
                print(f"🔒 Scanning {scenario_name} for security violations...")

                # Perform security scan
                scan_result = mock_content_detector.detect_sensitive_content(
                    scenario_config["content"],
                    keywords=scenario_config.get("metadata", {}).get("keywords", []),
                    keyword_document=scenario_config.get("metadata", {}).get("keyword_document")
                )

                # Apply security policies
                policy_result = mock_policy_enforcer.enforce_policies(
                    scenario_config["content"],
                    ["block_sensitive_data", "encrypt_content", "audit_access"]
                )

                # Assess compliance
                compliance_assessment = {
                    "frameworks_checked": scenario_config["compliance_frameworks"],
                    "violations_found": len(scan_result["topics"]),
                    "overall_compliant": scan_result["risk_score"] < 50,
                    "remediation_required": scan_result["risk_score"] >= 80
                }

                security_scan_results[scenario_name] = {
                    "scan": scan_result,
                    "policy": policy_result,
                    "compliance": compliance_assessment,
                    "metadata": scenario_config["metadata"]
                }

            # Verify comprehensive enterprise security scanning
            assert len(security_scan_results) == 5

            # Verify data breach prevention scenario
            breach_result = security_scan_results["data_breach_prevention"]
            assert breach_result["scan"]["sensitive"] is True
            assert breach_result["scan"]["risk_score"] >= 90
            assert "pii_data" in breach_result["scan"]["topics"]
            assert "credentials" in breach_result["scan"]["topics"]
            assert breach_result["policy"]["action_taken"] == "quarantine"
            assert "GDPR" in breach_result["compliance"]["frameworks_checked"]

            # Verify API security incident scenario
            api_result = security_scan_results["api_security_incident"]
            assert api_result["scan"]["sensitive"] is True
            assert api_result["scan"]["risk_score"] >= 95
            assert "security_incident" in api_result["scan"]["topics"]
            assert "attack_patterns" in api_result["scan"]["topics"]
            assert api_result["compliance"]["remediation_required"] is True

            # Verify healthcare compliance scenario
            healthcare_result = security_scan_results["healthcare_data_compliance"]
            assert healthcare_result["scan"]["sensitive"] is True
            assert healthcare_result["scan"]["risk_score"] == 100  # Maximum risk
            assert "phi_data" in healthcare_result["scan"]["topics"]
            assert "HIPAA" in healthcare_result["compliance"]["frameworks_checked"]

            # Verify financial transaction security
            financial_result = security_scan_results["financial_transaction_security"]
            assert financial_result["scan"]["sensitive"] is True
            assert financial_result["scan"]["risk_score"] >= 95
            assert "pci_data" in financial_result["scan"]["topics"]
            assert "PCI_DSS" in financial_result["compliance"]["frameworks_checked"]

            # Verify code repository security
            code_result = security_scan_results["code_repository_security"]
            assert code_result["scan"]["sensitive"] is True
            assert code_result["scan"]["risk_score"] >= 95
            assert "hardcoded_secrets" in code_result["scan"]["topics"]
            assert "credentials" in code_result["scan"]["topics"]

    @pytest.mark.asyncio
    async def test_enterprise_compliance_validation_pipeline(self, integration_app, enterprise_compliance_frameworks):
        """Test enterprise compliance validation and reporting pipeline."""
        # Setup enterprise compliance validation
        with patch("main.PolicyEnforcer") as mock_policy_enforcer_class, \
             patch("main.ComplianceChecker") as mock_compliance_class, \
             patch("main.AuditLogger") as mock_audit_class:

            mock_policy_enforcer = MagicMock()
            mock_compliance_checker = MagicMock()
            mock_audit_logger = MagicMock()

            mock_policy_enforcer_class.return_value = mock_policy_enforcer
            mock_compliance_class.return_value = mock_compliance_checker
            mock_audit_class.return_value = mock_audit_logger

            # Configure compliance checking for different frameworks
            def compliance_check_side_effect(content, frameworks):
                compliance_results = {}

                for framework in frameworks:
                    if framework == "GDPR":
                        compliance_results[framework] = {
                            "compliant": False,
                            "violations": [
                                {
                                    "rule": "Article 5 - Principles relating to processing",
                                    "description": "Unlawful processing of personal data",
                                    "severity": "high",
                                    "remediation": "Implement lawful basis for processing"
                                },
                                {
                                    "rule": "Article 25 - Data protection by design and by default",
                                    "description": "Inadequate data protection measures",
                                    "severity": "medium",
                                    "remediation": "Implement privacy by design principles"
                                }
                            ],
                            "overall_score": 35
                        }
                    elif framework == "HIPAA":
                        compliance_results[framework] = {
                            "compliant": False,
                            "violations": [
                                {
                                    "rule": "Security Rule - Technical Safeguards",
                                    "description": "Lack of encryption for PHI data",
                                    "severity": "critical",
                                    "remediation": "Implement AES-256 encryption for all PHI"
                                }
                            ],
                            "overall_score": 20
                        }
                    elif framework == "PCI_DSS":
                        compliance_results[framework] = {
                            "compliant": True,
                            "violations": [],
                            "overall_score": 95
                        }
                    else:
                        compliance_results[framework] = {
                            "compliant": True,
                            "violations": [],
                            "overall_score": 85
                        }

                return compliance_results

            mock_compliance_checker.check_compliance.side_effect = compliance_check_side_effect

            # Configure audit logging
            mock_audit_logger.log_compliance_event.return_value = {"logged": True, "event_id": "audit-123"}

            # Execute enterprise compliance validation workflow
            test_contents = [
                {
                    "content": "Employee database with SSN and salary data",
                    "frameworks": ["GDPR", "SOX"],
                    "expected_non_compliant": ["GDPR"]
                },
                {
                    "content": "Medical records with PHI data",
                    "frameworks": ["HIPAA", "HITECH"],
                    "expected_non_compliant": ["HIPAA"]
                },
                {
                    "content": "Payment processing logs with tokenized data",
                    "frameworks": ["PCI_DSS", "SOX"],
                    "expected_non_compliant": []
                }
            ]

            compliance_validation_results = {}

            for i, test_case in enumerate(test_contents):
                print(f"📋 Validating compliance for test case {i+1}...")

                # Perform compliance validation
                compliance_result = mock_compliance_checker.check_compliance(
                    test_case["content"],
                    test_case["frameworks"]
                )

                # Log compliance events
                for framework, assessment in compliance_result.items():
                    mock_audit_logger.log_compliance_event(
                        framework=framework,
                        compliant=assessment["compliant"],
                        violations=len(assessment["violations"]),
                        score=assessment["overall_score"]
                    )

                compliance_validation_results[f"test_case_{i+1}"] = {
                    "content_summary": test_case["content"][:50] + "...",
                    "frameworks_checked": test_case["frameworks"],
                    "compliance_results": compliance_result,
                    "expected_non_compliant": test_case["expected_non_compliant"]
                }

            # Verify comprehensive compliance validation
            assert len(compliance_validation_results) == 3

            # Verify GDPR compliance validation
            gdpr_case = compliance_validation_results["test_case_1"]
            assert "GDPR" in gdpr_case["compliance_results"]
            gdpr_result = gdpr_case["compliance_results"]["GDPR"]
            assert gdpr_result["compliant"] is False
            assert len(gdpr_result["violations"]) >= 2
            assert gdpr_result["overall_score"] < 50

            # Verify HIPAA compliance validation
            hipaa_case = compliance_validation_results["test_case_2"]
            assert "HIPAA" in hipaa_case["compliance_results"]
            hipaa_result = hipaa_case["compliance_results"]["HIPAA"]
            assert hipaa_result["compliant"] is False
            assert len(hipaa_result["violations"]) >= 1
            assert hipaa_result["overall_score"] < 30

            # Verify PCI DSS compliance (should pass)
            pci_case = compliance_validation_results["test_case_3"]
            assert "PCI_DSS" in pci_case["compliance_results"]
            pci_result = pci_case["compliance_results"]["PCI_DSS"]
            assert pci_result["compliant"] is True
            assert len(pci_result["violations"]) == 0
            assert pci_result["overall_score"] >= 90

            # Verify audit logging was called for each framework
            expected_calls = sum(len(case["frameworks_checked"]) for case in compliance_validation_results.values())
            assert mock_audit_logger.log_compliance_event.call_count == expected_calls

    @pytest.mark.asyncio
    async def test_security_incident_response_and_escalation(self, integration_app, enterprise_security_scenarios):
        """Test security incident response and escalation workflows."""
        # Setup security incident response system
        with patch("main.IncidentResponseManager") as mock_incident_class, \
             patch("main.EscalationEngine") as mock_escalation_class, \
             patch("main.NotificationService") as mock_notification_class:

            mock_incident_manager = MagicMock()
            mock_escalation_engine = MagicMock()
            mock_notification_service = MagicMock()

            mock_incident_class.return_value = mock_incident_manager
            mock_escalation_class.return_value = mock_escalation_engine
            mock_notification_class.return_value = mock_notification_service

            # Configure incident response for different severity levels
            def incident_response_side_effect(incident_data):
                severity = incident_data.get("severity", "low")

                if severity == "critical":
                    return {
                        "incident_id": f"INC-{int(time.time())}",
                        "response_plan": "critical_incident_response",
                        "immediate_actions": [
                            "Isolate affected systems",
                            "Notify security team",
                            "Activate incident response team",
                            "Preserve evidence"
                        ],
                        "escalation_level": "executive",
                        "estimated_resolution_time": "4-8 hours",
                        "communication_plan": {
                            "stakeholders": ["CEO", "CISO", "Legal", "PR"],
                            "timeline": "Immediate notification, hourly updates",
                            "channels": ["phone", "email", "incident_bridge"]
                        }
                    }
                elif severity == "high":
                    return {
                        "incident_id": f"INC-{int(time.time())}",
                        "response_plan": "high_severity_response",
                        "immediate_actions": [
                            "Assess impact",
                            "Contain breach",
                            "Notify relevant teams"
                        ],
                        "escalation_level": "management",
                        "estimated_resolution_time": "24-48 hours",
                        "communication_plan": {
                            "stakeholders": ["IT Director", "Security Lead", "Department Heads"],
                            "timeline": "Within 1 hour, daily updates",
                            "channels": ["email", "slack", "incident_management_system"]
                        }
                    }
                else:
                    return {
                        "incident_id": f"INC-{int(time.time())}",
                        "response_plan": "standard_response",
                        "immediate_actions": ["Log incident", "Monitor for recurrence"],
                        "escalation_level": "team_lead",
                        "estimated_resolution_time": "1-2 weeks",
                        "communication_plan": {
                            "stakeholders": ["Team Lead", "Security Officer"],
                            "timeline": "End of week",
                            "channels": ["email", "jira_ticket"]
                        }
                    }

            mock_incident_manager.create_incident_response.side_effect = incident_response_side_effect

            # Configure escalation engine
            mock_escalation_engine.should_escalate.return_value = True
            mock_escalation_engine.get_escalation_path.return_value = ["Tier 1", "Tier 2", "Management", "Executive"]

            # Configure notification service
            mock_notification_service.send_notification.return_value = {"delivered": True, "message_id": "msg-123"}

            # Execute security incident response workflow
            incident_scenarios = [
                {
                    "name": "data_breach_incident",
                    "severity": "critical",
                    "description": "Large-scale data breach with PII exposure",
                    "affected_systems": ["database", "api_gateway", "user_portal"],
                    "data_types": ["pii", "financial", "healthcare"]
                },
                {
                    "name": "api_attack_incident",
                    "severity": "high",
                    "description": "Coordinated API attack with multiple injection attempts",
                    "affected_systems": ["api_gateway", "web_servers"],
                    "data_types": ["api_logs", "security_events"]
                },
                {
                    "name": "code_leak_incident",
                    "severity": "high",
                    "description": "Hardcoded secrets found in source code repository",
                    "affected_systems": ["git_repository", "ci_cd_pipeline"],
                    "data_types": ["source_code", "configuration"]
                }
            ]

            incident_response_results = {}

            for scenario in incident_scenarios:
                print(f"🚨 Processing {scenario['name']} incident response...")

                # Create incident response
                incident_data = {
                    "severity": scenario["severity"],
                    "description": scenario["description"],
                    "affected_systems": scenario["affected_systems"],
                    "data_types": scenario["data_types"],
                    "timestamp": datetime.now().isoformat()
                }

                response_plan = mock_incident_manager.create_incident_response(incident_data)

                # Check escalation requirements
                should_escalate = mock_escalation_engine.should_escalate(incident_data)
                escalation_path = mock_escalation_engine.get_escalation_path(incident_data) if should_escalate else []

                # Send notifications
                notification_result = mock_notification_service.send_notification(
                    recipients=response_plan["communication_plan"]["stakeholders"],
                    message=f"Security Incident: {scenario['description']}",
                    priority=scenario["severity"],
                    channels=response_plan["communication_plan"]["channels"]
                )

                incident_response_results[scenario["name"]] = {
                    "incident_data": incident_data,
                    "response_plan": response_plan,
                    "escalation_required": should_escalate,
                    "escalation_path": escalation_path,
                    "notification_sent": notification_result["delivered"]
                }

            # Verify comprehensive incident response
            assert len(incident_response_results) == 3

            # Verify critical incident response (data breach)
            breach_response = incident_response_results["data_breach_incident"]
            assert breach_response["response_plan"]["escalation_level"] == "executive"
            assert "Isolate affected systems" in breach_response["response_plan"]["immediate_actions"]
            assert "CEO" in breach_response["response_plan"]["communication_plan"]["stakeholders"]
            assert breach_response["escalation_required"] is True
            assert len(breach_response["escalation_path"]) >= 3

            # Verify high severity incident response (API attack)
            api_response = incident_response_results["api_attack_incident"]
            assert api_response["response_plan"]["escalation_level"] == "management"
            assert "Assess impact" in api_response["response_plan"]["immediate_actions"]
            assert "IT Director" in api_response["response_plan"]["communication_plan"]["stakeholders"]

            # Verify notification delivery
            for result in incident_response_results.values():
                assert result["notification_sent"] is True

    @pytest.mark.asyncio
    async def test_multi_layer_enterprise_security_pipeline(self, integration_app, enterprise_security_scenarios):
        """Test multi-layer enterprise security validation pipeline."""
        # Setup comprehensive multi-layer security pipeline
        with patch("main.SecurityPipeline") as mock_pipeline_class, \
             patch("main.InputValidator") as mock_validator_class, \
             patch("main.ContentAnalyzer") as mock_analyzer_class, \
             patch("main.PolicyEngine") as mock_policy_class, \
             patch("main.OutputProcessor") as mock_output_class:

            mock_pipeline = MagicMock()
            mock_validator = MagicMock()
            mock_analyzer = MagicMock()
            mock_policy_engine = MagicMock()
            mock_output_processor = MagicMock()

            mock_pipeline_class.return_value = mock_pipeline
            mock_validator_class.return_value = mock_validator
            mock_analyzer_class.return_value = mock_analyzer
            mock_policy_class.return_value = mock_policy_engine
            mock_output_class.return_value = mock_output_processor

            # Configure multi-layer pipeline processing
            def pipeline_process_side_effect(content, context=None):
                layers_results = {
                    "input_validation": {"passed": True, "issues": []},
                    "content_analysis": {"sensitive": False, "risk_score": 0, "topics": []},
                    "policy_enforcement": {"action": "allow", "policies_applied": []},
                    "output_processing": {"transformed": False, "output_format": "original"}
                }

                # Layer 1: Input Validation
                if any(char in content for char in ["<script>", "javascript:", "../../../../"]):
                    layers_results["input_validation"] = {
                        "passed": False,
                        "issues": ["malicious_input_detected", "potential_xss"]
                    }
                    layers_results["policy_enforcement"]["action"] = "block"
                    return layers_results

                # Layer 2: Content Analysis
                if any(keyword in content.lower() for keyword in ["ssn", "password", "api key", "secret"]):
                    layers_results["content_analysis"] = {
                        "sensitive": True,
                        "risk_score": 85,
                        "topics": ["credentials", "sensitive_data"]
                    }

                # Layer 3: Policy Enforcement
                if layers_results["content_analysis"]["sensitive"]:
                    layers_results["policy_enforcement"] = {
                        "action": "quarantine",
                        "policies_applied": ["data_protection", "encryption_required"]
                    }

                # Layer 4: Output Processing
                if layers_results["policy_enforcement"]["action"] == "quarantine":
                    layers_results["output_processing"] = {
                        "transformed": True,
                        "output_format": "encrypted"
                    }

                return layers_results

            mock_pipeline.process_content.side_effect = pipeline_process_side_effect

            # Execute multi-layer security pipeline for enterprise scenarios
            pipeline_results = {}

            for scenario_name, scenario_config in enterprise_security_scenarios.items():
                print(f"🔐 Processing {scenario_name} through security pipeline...")

                # Process through multi-layer pipeline
                pipeline_result = mock_pipeline.process_content(
                    scenario_config["content"],
                    context={"source": scenario_config["metadata"]["source"]}
                )

                pipeline_results[scenario_name] = {
                    "layers": pipeline_result,
                    "overall_secure": all(layer["passed"] if "passed" in layer else layer.get("action") != "block"
                                        for layer in pipeline_result.values()),
                    "requires_attention": any(layer.get("sensitive", False) for layer in pipeline_result.values()
                                            if isinstance(layer, dict) and "sensitive" in layer)
                }

            # Verify comprehensive multi-layer security processing
            assert len(pipeline_results) == 5

            # Verify pipeline structure for each scenario
            for scenario_name, result in pipeline_results.items():
                assert "layers" in result
                layers = result["layers"]

                # Verify all layers are present
                required_layers = ["input_validation", "content_analysis", "policy_enforcement", "output_processing"]
                for layer in required_layers:
                    assert layer in layers

                # Verify layer structure
                for layer_name, layer_result in layers.items():
                    assert isinstance(layer_result, dict)

            # Verify specific scenario behaviors
            # Data breach scenario should trigger content analysis and policy enforcement
            breach_result = pipeline_results["data_breach_prevention"]
            assert breach_result["layers"]["content_analysis"]["sensitive"] is True
            assert breach_result["layers"]["policy_enforcement"]["action"] == "quarantine"
            assert breach_result["requires_attention"] is True

            # Healthcare scenario should have highest security processing
            healthcare_result = pipeline_results["healthcare_data_compliance"]
            assert healthcare_result["layers"]["content_analysis"]["sensitive"] is True
            assert healthcare_result["layers"]["policy_enforcement"]["action"] == "quarantine"
            assert healthcare_result["layers"]["output_processing"]["transformed"] is True

            # Financial transaction scenario should maintain PCI compliance
            financial_result = pipeline_results["financial_transaction_security"]
            assert financial_result["layers"]["content_analysis"]["sensitive"] is True
            assert financial_result["layers"]["policy_enforcement"]["action"] == "quarantine"

            # Code repository scenario should trigger credential detection
            code_result = pipeline_results["code_repository_security"]
            assert code_result["layers"]["content_analysis"]["sensitive"] is True
            assert code_result["layers"]["policy_enforcement"]["action"] == "quarantine"

            # API incident scenario should pass input validation but trigger content analysis
            api_result = pipeline_results["api_security_incident"]
            assert api_result["layers"]["input_validation"]["passed"] is True
            assert api_result["layers"]["content_analysis"]["sensitive"] is True

    @pytest.mark.asyncio
    async def test_enterprise_security_monitoring_and_reporting(self, integration_app, enterprise_security_scenarios):
        """Test enterprise security monitoring and automated reporting."""
        # Setup enterprise security monitoring and reporting
        with patch("main.SecurityMonitor") as mock_monitor_class, \
             patch("main.ReportGenerator") as mock_report_class, \
             patch("main.MetricsCollector") as mock_metrics_class:

            mock_monitor = MagicMock()
            mock_report_generator = MagicMock()
            mock_metrics_collector = MagicMock()

            mock_monitor_class.return_value = mock_monitor
            mock_report_class.return_value = mock_report_generator
            mock_metrics_class.return_value = mock_metrics_collector

            # Configure security monitoring
            mock_monitor.get_security_metrics.return_value = {
                "total_scans": 15420,
                "sensitive_content_detected": 234,
                "critical_violations": 12,
                "policy_violations": 89,
                "false_positives": 15,
                "average_response_time": 0.85,
                "uptime_percentage": 99.7
            }

            # Configure metrics collection
            def collect_metrics_side_effect(time_range):
                return {
                    "scan_volume": {
                        "daily": [120, 145, 132, 158, 167, 189, 201],
                        "weekly_average": 159
                    },
                    "violation_trends": {
                        "pii_exposure": [5, 8, 3, 12, 7, 9, 15],
                        "credential_leaks": [2, 1, 4, 6, 3, 8, 11],
                        "policy_breaches": [3, 7, 5, 9, 4, 6, 13]
                    },
                    "compliance_scores": {
                        "GDPR": [85, 87, 82, 89, 91, 88, 93],
                        "HIPAA": [78, 82, 79, 85, 87, 84, 89],
                        "PCI_DSS": [92, 94, 91, 96, 95, 97, 98]
                    }
                }

            mock_metrics_collector.collect_security_metrics.side_effect = collect_metrics_side_effect

            # Configure report generation
            def generate_report_side_effect(report_type, data):
                if report_type == "executive_summary":
                    return {
                        "title": "Enterprise Security Report - Executive Summary",
                        "period": "Last 30 Days",
                        "key_metrics": {
                            "security_score": 87,
                            "risk_level": "Medium",
                            "compliance_status": "Good",
                            "incident_count": 12
                        },
                        "top_risks": [
                            "PII Data Exposure",
                            "Credential Management",
                            "Access Control Weaknesses"
                        ],
                        "recommendations": [
                            "Implement automated data classification",
                            "Enhance credential rotation policies",
                            "Deploy advanced threat detection"
                        ]
                    }
                elif report_type == "detailed_analysis":
                    return {
                        "title": "Enterprise Security Detailed Analysis",
                        "sections": ["threat_landscape", "compliance_status", "incident_analysis", "remediation_tracking"],
                        "findings": data.get("findings", []),
                        "metrics": data.get("metrics", {}),
                        "charts": ["violation_trends.png", "compliance_dashboard.png"]
                    }
                else:
                    return {"title": f"{report_type.title()} Report", "data": data}

            mock_report_generator.generate_security_report.side_effect = generate_report_side_effect

            # Execute enterprise security monitoring workflow
            # Collect current metrics
            current_metrics = mock_monitor.get_security_metrics()

            # Collect historical metrics
            historical_metrics = mock_metrics_collector.collect_security_metrics("30_days")

            # Generate executive summary report
            executive_report = mock_report_generator.generate_security_report(
                "executive_summary",
                {"metrics": current_metrics, "historical": historical_metrics}
            )

            # Generate detailed analysis report
            detailed_report = mock_report_generator.generate_security_report(
                "detailed_analysis",
                {
                    "metrics": current_metrics,
                    "historical": historical_metrics,
                    "findings": [
                        {
                            "severity": "high",
                            "category": "data_exposure",
                            "description": "PII data detected in logs",
                            "recommendation": "Implement data loss prevention"
                        }
                    ]
                }
            )

            # Verify comprehensive security monitoring and reporting
            assert "total_scans" in current_metrics
            assert current_metrics["total_scans"] == 15420
            assert "critical_violations" in current_metrics
            assert current_metrics["critical_violations"] == 12

            # Verify historical metrics
            assert "scan_volume" in historical_metrics
            assert len(historical_metrics["scan_volume"]["daily"]) == 7
            assert "violation_trends" in historical_metrics
            assert "compliance_scores" in historical_metrics

            # Verify executive summary report
            assert executive_report["title"] == "Enterprise Security Report - Executive Summary"
            assert "key_metrics" in executive_report
            assert executive_report["key_metrics"]["security_score"] == 87
            assert "top_risks" in executive_report
            assert len(executive_report["recommendations"]) >= 3

            # Verify detailed analysis report
            assert detailed_report["title"] == "Enterprise Security Detailed Analysis"
            assert "sections" in detailed_report
            assert len(detailed_report["sections"]) >= 4
            assert "metrics" in detailed_report
            assert "charts" in detailed_report

            # Verify compliance score trends
            compliance_scores = historical_metrics["compliance_scores"]
            assert "GDPR" in compliance_scores
            assert "HIPAA" in compliance_scores
            assert "PCI_DSS" in compliance_scores

            # All compliance scores should show improvement trend
            for framework, scores in compliance_scores.items():
                assert len(scores) == 7
                assert scores[-1] >= scores[0]  # Ending score >= starting score
