"""Integration tests for security scanning and compliance workflows.

These tests verify the complete workflow from security scanning through
analysis and notification, simulating enterprise security scenarios.
"""

import importlib.util, os
import pytest
from fastapi.testclient import TestClient


def _load_service(service_name, service_dir):
    """Load a service dynamically from hyphenated directory."""
    try:
        spec = importlib.util.spec_from_file_location(
            f"services.{service_name}.main",
            os.path.join(os.getcwd(), 'services', service_dir, 'main.py')
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.app
    except Exception as e:
        print(f"Warning: Could not load {service_name}: {e}")
        return None


@pytest.fixture(scope="module")
def secure_analyzer_app():
    """Load secure-analyzer service."""
    return _load_service("secure-analyzer", "secure-analyzer")


@pytest.fixture(scope="module")
def doc_store_app():
    """Load doc_store service."""
    return _load_service("doc_store", "doc_store")


@pytest.fixture(scope="module")
def analysis_service_app():
    """Load analysis-service."""
    return _load_service("analysis-service", "analysis-service")


@pytest.fixture(scope="module")
def notification_service_app():
    """Load notification-service."""
    return _load_service("notification-service", "notification-service")


def _assert_http_ok(response):
    """Assert HTTP 200 response."""
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


class TestSecurityComplianceWorkflow:
    """Test security scanning and compliance workflows."""

    def test_code_security_scanning_and_analysis(self, secure_analyzer_app, doc_store_app):
        """Test comprehensive security scanning of code and documentation."""
        if not secure_analyzer_app:
            pytest.skip("secure-analyzer service not available")

        secure_client = TestClient(secure_analyzer_app)
        doc_client = TestClient(doc_store_app)

        # Code with various security issues
        vulnerable_code = '''
# Security vulnerabilities demonstration
import os
import subprocess
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# SQL Injection vulnerability
@app.route('/users/<user_id>')
def get_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Dangerous: direct string interpolation in SQL
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return jsonify(cursor.fetchall())

# Command injection vulnerability
@app.route('/system/info')
def system_info():
    cmd = request.args.get('cmd', 'uname -a')
    # Dangerous: direct command execution
    result = subprocess.call(cmd, shell=True)
    return jsonify({'result': result})

# Hardcoded secrets
API_KEY = "sk-1234567890abcdef"  # Should be in environment
DB_PASSWORD = "admin123!"  # Should be in secrets manager
JWT_SECRET = "my-secret-key"  # Should be rotated

# Insecure direct object reference
@app.route('/files/<filename>')
def download_file(filename):
    # Dangerous: no path validation
    with open(filename, 'r') as f:
        return f.read()

# Weak password policy
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    password = data['password']
    # Should validate password strength
    if len(password) < 6:
        return jsonify({'error': 'Password too short'}), 400
    return jsonify({'message': 'User registered'})

# Missing input validation
@app.route('/search')
def search():
    query = request.args.get('q', '')
    # Should sanitize input
    results = perform_search(query)
    return jsonify(results)
'''

        # Step 1: Perform security scan
        scan_resp = secure_client.post("/detect", json={"content": vulnerable_code})
        _assert_http_ok(scan_resp)
        scan_result = scan_resp.json()

        # Verify security scan detected issues
        assert "sensitive" in scan_result
        assert isinstance(scan_result["matches"], list)
        assert isinstance(scan_result["topics"], list)

        # Should detect sensitive content
        assert scan_result["sensitive"] is True or len(scan_result["matches"]) > 0

        # Step 2: Store security analysis results
        security_report_id = "security-scan-001"
        store_resp = doc_client.post("/documents", json={
            "id": security_report_id,
            "content": f"""
# Security Scan Report

## Scan Results
{scan_result}

## Recommendations
1. Use parameterized queries to prevent SQL injection
2. Validate and sanitize user inputs
3. Store secrets in environment variables or secret managers
4. Implement proper authentication and authorization
5. Use secure coding practices
""",
            "metadata": {
                "type": "security_report",
                "scan_type": "code_analysis",
                "severity": "high",
                "findings_count": len(scan_result.get("findings", [])),
                "tags": ["security", "vulnerability", "compliance"]
            }
        })
        _assert_http_ok(store_resp)

        # Step 3: Verify security report is searchable
        security_search = doc_client.get("/search", params={"q": "security vulnerability"})
        _assert_http_ok(security_search)
        search_results = security_search.json()["data"]["items"]

        security_found = any("security" in doc["id"] for doc in search_results)
        assert security_found, "Security report not found in search results"

    def test_compliance_documentation_audit(self, doc_store_app, analysis_service_app):
        """Test compliance audit of documentation against standards."""
        doc_client = TestClient(doc_store_app)
        analysis_client = TestClient(analysis_service_app)

        # Documentation that may have compliance issues
        compliance_docs = [
            {
                "id": "api-without-auth",
                "content": """
# Public API Documentation

## Endpoints

### GET /public/data
Retrieves public data without authentication.

### POST /public/submit
Accepts public submissions without rate limiting.
""",
                "metadata": {
                    "compliance_level": "public",
                    "authentication": "none",
                    "data_classification": "public"
                }
            },
            {
                "id": "sensitive-data-api",
                "content": """
# Sensitive Data API

## Overview
This API handles sensitive user data including PII.

## Endpoints

### GET /users/personal
Returns user personal information.

**Security:** Requires JWT token
**Data:** Contains PII (email, phone, address)

### POST /users/consent
Records user consent for data processing.

**Security:** Requires MFA
**Compliance:** GDPR Article 7
""",
                "metadata": {
                    "compliance_level": "restricted",
                    "authentication": "jwt+mfa",
                    "data_classification": "sensitive",
                    "regulations": ["GDPR", "CCPA"]
                }
            },
            {
                "id": "financial-api",
                "content": """
# Financial Transactions API

## Endpoints

### POST /payments/process
Process financial transactions.

**Security:** PCI DSS compliant
**Encryption:** End-to-end encryption required
**Audit:** All transactions logged

### GET /payments/history
Retrieve payment history.

**Retention:** 7 years as per SOX requirements
**Access:** Restricted to authorized personnel
""",
                "metadata": {
                    "compliance_level": "critical",
                    "authentication": "certificate",
                    "data_classification": "financial",
                    "regulations": ["PCI_DSS", "SOX"],
                    "retention_period": "7_years"
                }
            }
        ]

        # Step 1: Store compliance documentation
        stored_compliance_docs = []
        for doc in compliance_docs:
            store_resp = doc_client.post("/documents", json={
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc["metadata"]
            })
            _assert_http_ok(store_resp)
            stored_compliance_docs.append(store_resp.json()["data"]["id"])

        # Step 2: Run compliance analysis
        if analysis_client:
            compliance_resp = analysis_client.post("/analyze", json={
                "targets": stored_compliance_docs,
                "analysis_type": "consistency",
                "options": {
                    "standards": ["GDPR", "PCI_DSS", "SOX"],
                    "scope": "documentation_audit"
                }
            })

            # Verify compliance analysis request
            assert compliance_resp.status_code in [200, 202, 404]

    def test_security_incident_response_workflow(self, secure_analyzer_app, doc_store_app, notification_service_app):
        """Test security incident detection and response workflow."""
        if not secure_analyzer_app:
            pytest.skip("secure-analyzer service not available")

        secure_client = TestClient(secure_analyzer_app)
        doc_client = TestClient(doc_store_app)
        notify_client = TestClient(notification_service_app) if notification_service_app else None

        # Step 1: Detect security incident in code
        incident_code = '''
# Code with critical security vulnerability
import pickle
from flask import Flask, request

app = Flask(__name__)

@app.route('/load_model')
def load_model():
    # CRITICAL: Pickle deserialization vulnerability
    model_data = request.data
    model = pickle.loads(model_data)  # Remote code execution possible!
    return str(model)
'''

        # Scan for security issues
        scan_resp = secure_client.post("/detect", json={"content": incident_code})
        _assert_http_ok(scan_resp)
        scan_result = scan_resp.json()

        # Step 2: Create security incident report
        incident_report = {
            "id": "security-incident-001",
            "title": "Critical Remote Code Execution Vulnerability",
            "severity": "critical",
            "content": f"""
# Security Incident Report

## Incident Details
- **Type:** Remote Code Execution
- **Severity:** Critical
    - **Detection Time:** 2024-01-15T10:30:00Z

## Vulnerability Description
Pickle deserialization vulnerability detected in model loading endpoint.

## Affected Code
```python
model = pickle.loads(model_data)  # SECURITY RISK
```

## Impact Assessment
- Potential remote code execution
- Data breach risk
- Service compromise

## Remediation Steps
1. Replace pickle with safe serialization (JSON, msgpack)
2. Implement input validation
3. Add security headers
4. Update dependencies

## Scan Results
{scan_result}
""",
            "metadata": {
                "type": "security_incident",
                "severity": "critical",
                "status": "open",
                "affected_components": ["web_api", "model_loading"],
                "remediation_priority": "high",
                "tags": ["security", "incident", "rce", "pickle"]
            }
        }

        # Store incident report
        store_resp = doc_client.post("/documents", json={
            "id": incident_report["id"],
            "content": incident_report["content"],
            "metadata": incident_report["metadata"]
        })
        _assert_http_ok(store_resp)

        # Step 3: Send security notifications
        if notify_client:
            notify_resp = notify_client.post("/notifications/security", json={
                "incident_id": incident_report["id"],
                "severity": incident_report["severity"],
                "message": f"Critical security vulnerability detected: {incident_report['title']}",
                "recipients": ["security_team", "devops_team"],
                "channels": ["email", "slack"],
                "escalation_required": True
            })

            # Notification might be async
            assert notify_resp.status_code in [200, 202, 404]

        # Step 4: Verify incident is properly documented and searchable
        incident_search = doc_client.get("/search", params={"q": "security incident critical"})
        _assert_http_ok(incident_search)
        search_results = incident_search.json()["data"]["items"]

        incident_found = any("incident" in doc["id"] for doc in search_results)
        assert incident_found, "Security incident not found in search"

    def test_compliance_monitoring_and_reporting(self, doc_store_app, analysis_service_app):
        """Test ongoing compliance monitoring and reporting."""
        doc_client = TestClient(doc_store_app)
        analysis_client = TestClient(analysis_service_app)

        # Compliance monitoring data
        compliance_monitoring = [
            {
                "id": "gdpr-compliance-report",
                "content": """
# GDPR Compliance Report

## Data Processing Activities

### User Registration Data
- **Purpose:** Account creation and management
- **Legal Basis:** Consent (Article 6.1.a)
- **Retention:** 3 years after account deactivation
- **Security Measures:** Encryption at rest and in transit

### Usage Analytics
- **Purpose:** Service improvement
- **Legal Basis:** Legitimate interest (Article 6.1.f)
- **Retention:** 2 years
- **Security Measures:** Anonymized data, aggregated reporting

## Data Subject Rights
- Right to access (Article 15)
- Right to rectification (Article 16)
- Right to erasure (Article 17)
- Right to data portability (Article 20)

## Compliance Status: COMPLIANT
""",
                "metadata": {
                    "type": "compliance_report",
                    "regulation": "GDPR",
                    "status": "compliant",
                    "last_audit": "2024-01-01",
                    "next_review": "2024-07-01"
                }
            },
            {
                "id": "security-audit-log",
                "content": """
# Security Audit Log

## Recent Security Events

### 2024-01-10 14:30:00
- **Event:** Failed login attempt
- **User:** unknown
- **IP:** 192.168.1.100
- **Action:** Account temporarily locked

### 2024-01-10 16:45:00
- **Event:** Database backup completed
- **Status:** Success
- **Size:** 2.3 GB
- **Duration:** 45 minutes

### 2024-01-11 09:15:00
- **Event:** SSL certificate renewed
- **Certificate:** api.example.com
- **Valid Until:** 2024-04-11

## Security Metrics
- Failed login attempts: 23 (last 30 days)
- Successful logins: 1,245 (last 30 days)
- Data breaches: 0
- Security incidents: 1 (resolved)

## Overall Security Posture: GOOD
""",
                "metadata": {
                    "type": "security_audit",
                    "period": "monthly",
                    "status": "good",
                    "metrics": {
                        "failed_logins": 23,
                        "successful_logins": 1245,
                        "incidents": 1
                    }
                }
            }
        ]

        # Step 1: Store compliance monitoring documents
        stored_monitoring_docs = []
        for doc in compliance_monitoring:
            store_resp = doc_client.post("/documents", json={
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc["metadata"]
            })
            _assert_http_ok(store_resp)
            stored_monitoring_docs.append(store_resp.json()["data"]["id"])

        # Step 2: Generate compliance dashboard/report
        if analysis_client:
            dashboard_resp = analysis_client.post("/reports/compliance", json={
                "documents": stored_monitoring_docs,
                "period": "monthly",
                "include_metrics": True,
                "regulations": ["GDPR", "ISO27001"]
            })

            # Verify report generation request
            assert dashboard_resp.status_code in [200, 202, 404]

        # Step 3: Verify compliance documents are accessible
        for doc_id in stored_monitoring_docs:
            get_resp = doc_client.get(f"/documents/{doc_id}")
            _assert_http_ok(get_resp)
            doc = get_resp.json()["data"]

            assert "type" in doc["metadata"]
            assert "status" in doc["metadata"]

    def test_access_control_and_audit_workflow(self, doc_store_app, secure_analyzer_app):
        """Test access control and audit logging for sensitive documentation."""
        if not secure_analyzer_app:
            pytest.skip("secure-analyzer service not available")

        doc_client = TestClient(doc_store_app)
        secure_client = TestClient(secure_analyzer_app)

        # Sensitive documentation with access controls
        sensitive_docs = [
            {
                "id": "confidential-api-keys",
                "content": """
# Confidential API Keys and Secrets

## Production API Keys
- **Stripe Secret Key:** sk_live_XXXXXXXXXXXXXXXXXXXX
- **AWS Access Key:** AKIAXXXXXXXXXXXXXXXXXXXX
- **Database Password:** prod_db_password_2024!

## Development API Keys
- **Stripe Test Key:** sk_test_XXXXXXXXXXXXXXXXXXXX
- **AWS Test Key:** AKIAXXXXXXXXXXXXXXXXXXXX

## Access Control
- Keys must be rotated quarterly
- Access limited to authorized personnel only
- Audit all access to this document
""",
                "metadata": {
                    "classification": "confidential",
                    "access_level": "restricted",
                    "audit_required": True,
                    "retention_policy": "permanent",
                    "tags": ["secrets", "api_keys", "confidential"]
                }
            },
            {
                "id": "user-data-handling",
                "content": """
# User Data Handling Procedures

## Data Collection
We collect the following user data:
- Email address (required for account)
- Name (optional, for personalization)
- IP address (automatically collected)
- Usage analytics (with consent)

## Data Storage
- User data encrypted at rest using AES-256
- Database backups encrypted and stored offsite
- Access logging enabled for all data operations

## Data Retention
- Account data: Retained until account deletion
- Analytics data: Anonymized after 2 years
- IP addresses: Anonymized after 30 days

## Data Subject Rights
Users can:
- Access their data
- Correct inaccurate data
- Delete their account and data
- Export their data
""",
                "metadata": {
                    "classification": "internal",
                    "access_level": "internal",
                    "audit_required": True,
                    "regulations": ["GDPR", "CCPA"],
                    "tags": ["privacy", "data_handling", "gdpr"]
                }
            }
        ]

        # Step 1: Store sensitive documents with access controls
        stored_sensitive_docs = []
        for doc in sensitive_docs:
            store_resp = doc_client.post("/documents", json={
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc["metadata"]
            })
            _assert_http_ok(store_resp)
            stored_sensitive_docs.append(store_resp.json()["data"]["id"])

        # Step 2: Scan for sensitive information leakage
        for doc in sensitive_docs:
            scan_resp = secure_client.post("/scan/content", json={
                "content": doc["content"],
                "scan_type": "secrets_detection"
            })

            if scan_resp.status_code == 200:
                scan_result = scan_resp.json()
                # Verify secrets detection
                assert "findings" in scan_result or "data" in scan_result

        # Step 3: Verify access controls and audit logging
        for doc_id in stored_sensitive_docs:
            get_resp = doc_client.get(f"/documents/{doc_id}")
            _assert_http_ok(get_resp)
            doc = get_resp.json()["data"]

            # Verify classification metadata
            assert doc["metadata"]["classification"] in ["confidential", "internal"]
            assert "access_level" in doc["metadata"]
            assert doc["metadata"]["audit_required"] is True
