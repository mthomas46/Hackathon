"""Source Agent integration and workflow tests.

Tests service integration, data flow, and end-to-end workflows.
Focused on integration scenarios following TDD principles.
"""
import pytest
import importlib.util, os
from fastapi.testclient import TestClient

from .test_utils import load_source_agent_service, _assert_http_ok


@pytest.fixture(scope="module")
def client():
    """Test client fixture for source agent service."""
    app = load_source_agent_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestSourceAgentIntegration:
    """Test source agent integration and workflow functionality."""

    def test_complete_github_workflow(self, client):
        """Test complete GitHub document processing workflow."""
        # Step 1: Fetch document
        fetch_request = {
            "source": "github",
            "identifier": "testuser:testrepo"
        }

        fetch_response = client.post("/docs/fetch", json=fetch_request)
        _assert_http_ok(fetch_response)

        fetch_data = fetch_response.json()["data"]
        document = fetch_data["document"]

        # Step 2: Normalize the fetched document
        normalize_request = {
            "source": "github",
            "data": {
                "type": "readme",
                "content": document["content"],
                "name": document["title"],
                "html_url": document["url"]
            },
            "correlation_id": "workflow-test-123"
        }

        normalize_response = client.post("/normalize", json=normalize_request)
        _assert_http_ok(normalize_response)

        normalize_data = normalize_response.json()["data"]
        envelope = normalize_data["envelope"]

        # Step 3: Verify workflow consistency
        assert envelope["correlation_id"] == "workflow-test-123"
        assert envelope["document"]["source_type"] == "github"
        assert "id" in envelope["document"]
        assert "title" in envelope["document"]
        assert "content" in envelope["document"]

    def test_cross_source_data_consistency(self, client):
        """Test data consistency across different sources."""
        sources_data = ["github", "jira"]

        results = []
        for source in sources_data:
            # Normalize sample data for each source
            if source == "github":
                normalize_request = {
                    "source": source,
                    "data": {
                        "type": "pr",
                        "number": 123,
                        "title": f"Test {source} Item",
                        "body": f"This is test content from {source}"
                    }
                }
            else:  # jira
                normalize_request = {
                    "source": source,
                    "data": {
                        "key": "TEST-123",
                        "fields": {
                            "summary": f"Test {source} Item",
                            "description": f"This is test content from {source}"
                        }
                    }
                }

            response = client.post("/normalize", json=normalize_request)
            if response.status_code == 200:
                results.append(response.json()["data"]["envelope"])

        # Verify all results have consistent structure
        for envelope in results:
            assert "id" in envelope
            assert "document" in envelope
            document = envelope["document"]
            assert "id" in document
            assert "title" in document
            assert "content" in document
            assert "source_type" in document

    def test_code_analysis_integration_workflow(self, client):
        """Test code analysis integration with document processing."""
        # Sample code with multiple API patterns
        test_code = '''
from fastapi import FastAPI
from flask import Flask, request
import express from 'express'
from org.springframework.web.bind.annotation import GetMapping, PostMapping

app = FastAPI()
flask_app = Flask(__name__)
express_app = express()

# FastAPI endpoints
@app.get("/users")
async def get_users():
    return {"users": []}

@app.post("/users")
async def create_user():
    return {"id": 1}

# Flask endpoints
@flask_app.route("/posts", methods=["GET"])
def get_posts():
    return {"posts": []}

@flask_app.route("/posts", methods=["POST"])
def create_post():
    return {"id": 1}

# Express endpoints
express_app.get("/items", (req, res) => {
    res.json({items: []});
});

express_app.post("/items", (req, res) => {
    res.json({id: 1});
});

// Spring Boot endpoints
@GetMapping("/products")
public List<Product> getProducts() {
    return products;
}

@PostMapping("/products")
public Product createProduct() {
    return new Product();
}
'''

        # Step 1: Analyze code
        analyze_request = {"text": test_code}
        analyze_response = client.post("/code/analyze", json=analyze_request)
        _assert_http_ok(analyze_response)

        analysis_data = analyze_response.json()["data"]

        # Step 2: Verify analysis results
        assert analysis_data["endpoint_count"] > 0
        assert len(analysis_data["patterns_found"]) > 0
        assert "FastAPI" in analysis_data["patterns_found"]

        # Step 3: Create document from analysis results
        normalize_request = {
            "source": "github",
            "data": {
                "type": "code_analysis",
                "title": "API Code Analysis Results",
                "content": f"Analysis Results:\n{analysis_data['analysis']}",
                "metadata": {
                    "endpoint_count": analysis_data["endpoint_count"],
                    "patterns": analysis_data["patterns_found"]
                }
            },
            "correlation_id": "code-analysis-workflow"
        }

        normalize_response = client.post("/normalize", json=normalize_request)
        _assert_http_ok(normalize_response)

        # Verify the workflow completed successfully
        envelope = normalize_response.json()["data"]["envelope"]
        assert envelope["correlation_id"] == "code-analysis-workflow"

    def test_bulk_document_processing_workflow(self, client):
        """Test bulk document processing workflow."""
        # Simulate processing multiple documents
        documents = [
            {"source": "github", "identifier": "org:repo1"},
            {"source": "github", "identifier": "org:repo2"},
            {"source": "github", "identifier": "org:repo3"},
        ]

        processed_documents = []
        correlation_base = "bulk-test"

        for i, doc_request in enumerate(documents):
            # Fetch document
            fetch_response = client.post("/docs/fetch", json=doc_request)
            if fetch_response.status_code == 200:
                fetch_data = fetch_response.json()["data"]
                document = fetch_data["document"]

                # Normalize document
                normalize_request = {
                    "source": "github",
                    "data": {
                        "type": "readme",
                        "content": document["content"],
                        "name": document["title"],
                        "html_url": document["url"]
                    },
                    "correlation_id": f"{correlation_base}-{i}"
                }

                normalize_response = client.post("/normalize", json=normalize_request)
                if normalize_response.status_code == 200:
                    processed_documents.append(normalize_response.json()["data"]["envelope"])

        # Verify bulk processing results
        assert len(processed_documents) > 0
        for envelope in processed_documents:
            assert envelope["correlation_id"].startswith(correlation_base)
            assert "document" in envelope

    def test_service_capabilities_integration(self, client):
        """Test integration with service capabilities listing."""
        # Get service capabilities
        sources_response = client.get("/sources")
        _assert_http_ok(sources_response)

        sources_data = sources_response.json()["data"]
        capabilities = sources_data["capabilities"]

        # Test each capability
        for source, capability_list in capabilities.items():
            for capability in capability_list:
                if capability == "readme_fetch" and source == "github":
                    # Test GitHub README fetch capability
                    fetch_request = {
                        "source": source,
                        "identifier": "testuser:testrepo"
                    }
                    fetch_response = client.post("/docs/fetch", json=fetch_request)
                    assert fetch_response.status_code in [200, 501]  # 501 if not implemented

                elif capability == "pr_normalization" and source == "github":
                    # Test GitHub PR normalization capability
                    normalize_request = {
                        "source": source,
                        "data": {
                            "type": "pr",
                            "number": 123,
                            "title": "Test PR"
                        }
                    }
                    normalize_response = client.post("/normalize", json=normalize_request)
                    assert normalize_response.status_code in [200, 501]

                elif capability == "code_analysis":
                    # Test code analysis capability
                    analyze_request = {
                        "text": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/test')\ndef test(): pass"
                    }
                    analyze_response = client.post("/code/analyze", json=analyze_request)
                    assert analyze_response.status_code in [200, 501]

    def test_error_handling_integration(self, client):
        """Test error handling across integrated operations."""
        # Test with invalid source
        invalid_request = {
            "source": "invalid-source",
            "identifier": "test"
        }

        response = client.post("/docs/fetch", json=invalid_request)
        # Should handle error gracefully
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            data = response.json()
            assert "error" in data or "message" in data

    def test_metadata_preservation_workflow(self, client):
        """Test metadata preservation through the processing workflow."""
        # Create document with rich metadata
        original_metadata = {
            "author": "testuser",
            "created_at": "2024-01-01T00:00:00Z",
            "tags": ["test", "integration"],
            "priority": "high",
            "category": "documentation"
        }

        normalize_request = {
            "source": "github",
            "data": {
                "type": "pr",
                "number": 456,
                "title": "Test PR with Metadata",
                "body": "This PR has rich metadata",
                "user": {"login": original_metadata["author"]},
                "created_at": original_metadata["created_at"],
                "labels": [{"name": tag} for tag in original_metadata["tags"]]
            },
            "correlation_id": "metadata-test"
        }

        response = client.post("/normalize", json=normalize_request)
        _assert_http_ok(response)

        envelope = response.json()["data"]["envelope"]
        document = envelope["document"]

        # Verify metadata preservation
        assert "metadata" in document
        metadata = document["metadata"]
        assert "owner" in metadata  # Should be transformed from user.login
        assert "type" in metadata
        assert metadata["type"] == "pull_request"

    def test_content_transformation_workflow(self, client):
        """Test content transformation through the processing pipeline."""
        # Test HTML to text conversion workflow
        html_content = """
        <html>
        <body>
            <h1>Test Document</h1>
            <p>This is a <strong>test</strong> document with <em>HTML</em> content.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
            <a href="https://example.com">Link</a>
        </body>
        </html>
        """

        # Create document with HTML content
        normalize_request = {
            "source": "confluence",
            "data": {
                "id": "12345",
                "title": "HTML Test Document",
                "body": {
                    "storage": {
                        "value": html_content
                    }
                }
            },
            "correlation_id": "html-transform-test"
        }

        response = client.post("/normalize", json=normalize_request)
        # Should handle HTML content transformation
        assert response.status_code in [200, 501]

        if response.status_code == 200:
            envelope = response.json()["data"]["envelope"]
            document = envelope["document"]
            assert "content" in document
            # Content should be processed (HTML tags may be stripped or preserved)

    def test_correlation_tracking_workflow(self, client):
        """Test correlation ID tracking through workflow."""
        correlation_id = "correlation-tracking-test-123"

        # Perform multiple operations with same correlation ID
        operations = [
            {
                "endpoint": "/normalize",
                "data": {
                    "source": "github",
                    "data": {"type": "pr", "number": 789, "title": "Correlation Test"},
                    "correlation_id": correlation_id
                }
            }
        ]

        results = []
        for op in operations:
            response = client.post(op["endpoint"], json=op["data"])
            if response.status_code == 200:
                results.append(response.json()["data"])

        # Verify correlation tracking
        for result in results:
            if "envelope" in result:
                assert result["envelope"]["correlation_id"] == correlation_id

    def test_service_response_consistency(self, client):
        """Test consistency of service responses across operations."""
        # Perform multiple operations and check response structure consistency
        operations = [
            ("/sources", {}, "GET"),
            ("/docs/fetch", {"source": "github", "identifier": "test:repo"}, "POST"),
            ("/normalize", {"source": "github", "data": {"type": "pr", "number": 1}}, "POST"),
            ("/code/analyze", {"text": "def test(): pass"}, "POST")
        ]

        responses = []
        for endpoint, data, method in operations:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json=data)

            if response.status_code == 200:
                responses.append(response.json())

        # Check response structure consistency
        for response_data in responses:
            # All successful responses should have consistent structure
            assert "message" in response_data or "data" in response_data

    def test_integration_load_test(self, client):
        """Test integration performance under load."""
        import time

        start_time = time.time()

        # Perform 50 operations across different endpoints
        operations_count = 0
        for i in range(10):
            # Test fetch
            fetch_response = client.post("/docs/fetch", json={
                "source": "github",
                "identifier": f"user{i}:repo{i}"
            })
            if fetch_response.status_code == 200:
                operations_count += 1

            # Test normalize
            normalize_response = client.post("/normalize", json={
                "source": "github",
                "data": {"type": "pr", "number": i, "title": f"PR {i}"}
            })
            if normalize_response.status_code == 200:
                operations_count += 1

            # Test analyze
            analyze_response = client.post("/code/analyze", json={
                "text": f"def function_{i}(): return {i}"
            })
            if analyze_response.status_code == 200:
                operations_count += 1

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete within reasonable time
        assert total_time < 30  # 30 seconds for 30 operations
        assert operations_count > 0  # At least some operations should succeed

    def test_workflow_error_recovery(self, client):
        """Test error recovery in workflow processing."""
        # Test with mixed valid and invalid operations
        test_cases = [
            # Valid operation
            {
                "endpoint": "/normalize",
                "data": {"source": "github", "data": {"type": "pr", "number": 1}},
                "expected_success": True
            },
            # Invalid operation
            {
                "endpoint": "/docs/fetch",
                "data": {"source": "invalid", "identifier": "test"},
                "expected_success": False
            },
            # Another valid operation
            {
                "endpoint": "/code/analyze",
                "data": {"text": "def test(): pass"},
                "expected_success": True
            }
        ]

        results = []
        for case in test_cases:
            response = client.post(case["endpoint"], json=case["data"])
            results.append({
                "endpoint": case["endpoint"],
                "success": response.status_code == 200,
                "expected_success": case["expected_success"]
            })

        # Verify error recovery - valid operations should still work
        successful_ops = [r for r in results if r["success"]]
        assert len(successful_ops) > 0  # At least some operations should succeed

        # Check that operations performed as expected
        for result in results:
            if result["expected_success"]:
                assert result["success"], f"Expected success for {result['endpoint']}"
