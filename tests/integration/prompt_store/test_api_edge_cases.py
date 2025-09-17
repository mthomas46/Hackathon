"""API edge cases and error condition tests for prompt_store service.

Tests boundary conditions, error handling, and security scenarios.
"""

import pytest
from fastapi.testclient import TestClient
import uuid
import json
from unittest.mock import patch, AsyncMock


@pytest.mark.integration
class TestAPIEdgeCases:
    """Test edge cases and error conditions in API endpoints."""

    def test_extremely_long_prompt_content(self, prompt_store_service: TestClient):
        """Test handling of extremely long prompt content."""
        # Create content that's very large (1MB)
        large_content = "x" * (1024 * 1024)  # 1MB string

        prompt_data = {
            "name": f"large_content_test_{uuid.uuid4().hex[:8]}",
            "category": "edge_case_testing",
            "content": large_content,
            "created_by": "edge_case_test"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)

        # Should either succeed or fail with appropriate error
        if response.status_code == 201:
            # If it succeeds, verify the content was stored
            prompt = response.json()["data"]
            assert len(prompt["content"]) == len(large_content)
        elif response.status_code in [413, 422]:
            # Payload too large or validation error - acceptable
            data = response.json()
            assert "success" in data
            assert data["success"] is False
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")

    def test_special_characters_in_content(self, prompt_store_service: TestClient):
        """Test handling of special characters and Unicode in prompt content."""
        special_content = """
        Special characters test:
        - Emojis: 😀🚀🔥
        - Unicode: ñáéíóú 中文 العربية
        - Symbols: ©®™€£¥
        - Math: ∫∑√∂∆∞
        - SQL injection attempt: '; DROP TABLE prompts; --
        - XSS attempt: <script>alert('xss')</script>
        - Path traversal: ../../../etc/passwd
        """

        prompt_data = {
            "name": f"special_chars_test_{uuid.uuid4().hex[:8]}",
            "category": "edge_case_testing",
            "content": special_content,
            "created_by": "edge_case_test"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
        assert response.status_code == 201

        prompt = response.json()["data"]
        assert prompt["content"] == special_content  # Should preserve all characters

    def test_concurrent_prompt_creation_same_name(self, prompt_store_service: TestClient):
        """Test concurrent creation of prompts with same name."""
        prompt_name = f"concurrent_name_test_{uuid.uuid4().hex[:8]}"

        # Create multiple prompts with same name rapidly
        responses = []
        for i in range(5):
            prompt_data = {
                "name": prompt_name,
                "category": "concurrency_testing",
                "content": f"Content for concurrent prompt {i}",
                "created_by": "concurrency_test"
            }

            response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
            responses.append(response)

        # At least one should succeed, others should fail appropriately
        success_count = sum(1 for r in responses if r.status_code == 201)
        failure_count = sum(1 for r in responses if r.status_code != 201)

        assert success_count >= 1, "At least one prompt creation should succeed"
        assert failure_count >= 1, "Some prompt creations should fail due to name conflict"

        # Failed requests should have appropriate error responses
        for response in responses:
            if response.status_code != 201:
                data = response.json()
                assert "success" in data
                assert data["success"] is False

    def test_empty_and_whitespace_content(self, prompt_store_service: TestClient):
        """Test handling of empty and whitespace-only content."""
        test_cases = [
            ("", "empty content"),
            ("   ", "whitespace only"),
            ("\n\n\t  \n", "newlines and tabs only"),
            (" \n \t \r ", "mixed whitespace"),
        ]

        for content, description in test_cases:
            prompt_data = {
                "name": f"whitespace_test_{uuid.uuid4().hex[:8]}",
                "category": "edge_case_testing",
                "content": content,
                "created_by": "edge_case_test"
            }

            response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)

            # Should either succeed or fail with validation error
            if response.status_code == 201:
                # If it succeeds, content should be preserved
                prompt = response.json()["data"]
                assert prompt["content"] == content
            elif response.status_code == 422:
                # Validation error is acceptable
                data = response.json()
                assert "success" in data
                assert data["success"] is False
            else:
                pytest.fail(f"Unexpected status for {description}: {response.status_code}")

    def test_extremely_long_names(self, prompt_store_service: TestClient):
        """Test handling of extremely long prompt names."""
        long_name = "a" * 1000  # 1000 character name

        prompt_data = {
            "name": long_name,
            "category": "edge_case_testing",
            "content": "Test content for long name",
            "created_by": "edge_case_test"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)

        if response.status_code == 201:
            prompt = response.json()["data"]
            assert prompt["name"] == long_name
        elif response.status_code == 422:
            # Validation error for too long name is acceptable
            data = response.json()
            assert "success" in data
            assert data["success"] is False
        else:
            pytest.fail(f"Unexpected status for long name: {response.status_code}")

    def test_invalid_uuid_formats(self, prompt_store_service: TestClient):
        """Test handling of invalid UUID formats in URL parameters."""
        invalid_ids = [
            "not-a-uuid",
            "123",
            "invalid-uuid-format",
            "00000000-0000-0000-0000-00000000000Z",  # Invalid character
            "",  # Empty
            "null",
            "undefined"
        ]

        for invalid_id in invalid_ids:
            response = prompt_store_service.get(f"/api/v1/prompts/{invalid_id}")

            # Should return 404 or 422, but not crash
            assert response.status_code in [404, 422]

            data = response.json()
            assert "success" in data
            assert data["success"] is False

    def test_malformed_json_payloads(self, prompt_store_service: TestClient):
        """Test handling of malformed JSON payloads."""
        malformed_payloads = [
            '{"name": "test", "category": "test"',  # Missing closing brace
            '{"name": "test", "category": "test",}',  # Trailing comma
            '{"name": "test", "category": "test", "content": }',  # Invalid value
            'null',  # Null payload
            '"string"',  # String instead of object
            '[]',  # Array instead of object
        ]

        for payload in malformed_payloads:
            response = prompt_store_service.post(
                "/api/v1/prompts",
                data=payload,
                headers={"Content-Type": "application/json"}
            )

            # Should return 422 for JSON parsing/validation errors
            assert response.status_code == 422

            data = response.json()
            assert "success" in data
            assert data["success"] is False

    def test_extreme_pagination_values(self, prompt_store_service: TestClient):
        """Test handling of extreme pagination values."""
        # Create some test prompts first
        for i in range(5):
            prompt_data = {
                "name": f"pagination_test_{i}_{uuid.uuid4().hex[:4]}",
                "category": "pagination_testing",
                "content": f"Content {i}",
                "created_by": "pagination_test"
            }
            response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
            assert response.status_code == 201

        # Test extreme limit values
        extreme_limits = [0, 1, 1000, 10000, -1, -100]

        for limit in extreme_limits:
            response = prompt_store_service.get(f"/api/v1/prompts?limit={limit}")

            if limit > 0 and limit <= 1000:  # Reasonable limits
                assert response.status_code == 200
                data = response.json()
                assert "success" in data
                assert data["success"] is True
                assert "data" in data
                prompts = data["data"]
                assert isinstance(prompts, list)
                if limit < len(prompts):
                    assert len(prompts) <= limit
            elif limit <= 0 or limit > 1000:  # Unreasonable limits
                # Should either work with default/sane limits or return error
                assert response.status_code in [200, 422]

        # Test extreme offset values
        extreme_offsets = [0, 1000, 10000, -1, -100]

        for offset in extreme_offsets:
            response = prompt_store_service.get(f"/api/v1/prompts?offset={offset}")

            if offset >= 0:  # Valid offsets
                assert response.status_code == 200
                data = response.json()
                assert "success" in data
                assert data["success"] is True
            else:  # Invalid negative offsets
                assert response.status_code in [200, 422]  # May default to 0

    def test_sql_injection_attempts(self, prompt_store_service: TestClient):
        """Test handling of SQL injection attempts."""
        injection_attempts = [
            "'; DROP TABLE prompts; --",
            "' OR '1'='1",
            "'; SELECT * FROM prompts; --",
            "admin'--",
            "1' OR '1' = '1",
            "'; UPDATE prompts SET content='hacked' WHERE 1=1; --"
        ]

        for injection in injection_attempts:
            # Test in search queries
            response = prompt_store_service.get(f"/api/v1/prompts/search?q={injection}")
            assert response.status_code in [200, 422, 404]  # Should not crash or expose data

            # Test in prompt content
            prompt_data = {
                "name": f"sql_test_{uuid.uuid4().hex[:8]}",
                "category": "security_testing",
                "content": f"Content with injection: {injection}",
                "created_by": "security_test"
            }

            response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
            if response.status_code == 201:
                # If it succeeds, verify the content is stored as-is (no execution)
                prompt = response.json()["data"]
                assert injection in prompt["content"]
            else:
                # Validation error is acceptable
                assert response.status_code == 422

    def test_xss_prevention(self, prompt_store_service: TestClient):
        """Test prevention of XSS attacks."""
        xss_payloads = [
            '<script>alert("xss")</script>',
            '<img src=x onerror=alert("xss")>',
            'javascript:alert("xss")',
            '<iframe src="javascript:alert(\'xss\')"></iframe>',
            '<svg onload=alert("xss")>',
            '"><script>alert("xss")</script><"'
        ]

        for xss in xss_payloads:
            prompt_data = {
                "name": f"xss_test_{uuid.uuid4().hex[:8]}",
                "category": "security_testing",
                "content": f"Content with XSS: {xss}",
                "created_by": "security_test"
            }

            response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
            if response.status_code == 201:
                # Content should be stored as-is, not executed
                prompt = response.json()["data"]
                assert xss in prompt["content"]
            else:
                # Validation error is acceptable
                assert response.status_code == 422

    def test_directory_traversal_attempts(self, prompt_store_service: TestClient):
        """Test prevention of directory traversal attacks."""
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows\\System32",
            "../../../../etc/shadow",
            "....//....//....//etc/passwd"
        ]

        for traversal in traversal_attempts:
            # Test in search parameters
            response = prompt_store_service.get(f"/api/v1/prompts/search?q={traversal}")
            assert response.status_code in [200, 404, 422]  # Should not crash

            # Test in content
            prompt_data = {
                "name": f"traversal_test_{uuid.uuid4().hex[:8]}",
                "category": "security_testing",
                "content": f"Content with traversal: {traversal}",
                "created_by": "security_test"
            }

            response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
            if response.status_code == 201:
                prompt = response.json()["data"]
                assert traversal in prompt["content"]
            else:
                assert response.status_code == 422

    def test_extreme_json_nesting(self, prompt_store_service: TestClient):
        """Test handling of extremely nested JSON structures."""
        # Create deeply nested metadata
        def create_nested_dict(depth=10):
            if depth == 0:
                return {"value": "deep"}
            return {"nested": create_nested_dict(depth - 1)}

        nested_metadata = create_nested_dict()

        prompt_data = {
            "name": f"nested_test_{uuid.uuid4().hex[:8]}",
            "category": "edge_case_testing",
            "content": "Test content for nested JSON",
            "metadata": nested_metadata,
            "created_by": "edge_case_test"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)

        if response.status_code == 201:
            prompt = response.json()["data"]
            assert prompt["metadata"] == nested_metadata
        elif response.status_code == 422:
            # Validation error for too deep nesting is acceptable
            data = response.json()
            assert "success" in data
            assert data["success"] is False
        else:
            pytest.fail(f"Unexpected status for nested JSON: {response.status_code}")

    def test_rapid_successive_updates(self, prompt_store_service: TestClient):
        """Test rapid successive updates to the same prompt."""
        # Create initial prompt
        prompt_data = {
            "name": f"rapid_update_test_{uuid.uuid4().hex[:8]}",
            "category": "performance_testing",
            "content": "Initial content",
            "created_by": "performance_test"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
        assert response.status_code == 201
        prompt_id = response.json()["data"]["id"]

        # Perform rapid successive updates
        for i in range(10):
            update_data = {
                "content": f"Updated content version {i+1}",
                "updated_by": "performance_test"
            }

            response = prompt_store_service.put(f"/api/v1/prompts/{prompt_id}", json=update_data)
            assert response.status_code == 200

            updated_prompt = response.json()["data"]
            assert updated_prompt["version"] == i + 2  # Initial + updates
            assert f"version {i+1}" in updated_prompt["content"]

        # Verify final version
        response = prompt_store_service.get(f"/api/v1/prompts/{prompt_id}")
        assert response.status_code == 200
        final_prompt = response.json()["data"]
        assert final_prompt["version"] == 11  # Initial + 10 updates

    def test_memory_exhaustion_prevention(self, prompt_store_service: TestClient):
        """Test prevention of memory exhaustion attacks."""
        # Test with very large arrays in metadata
        large_array = ["x"] * 100000  # 100k element array

        prompt_data = {
            "name": f"memory_test_{uuid.uuid4().hex[:8]}",
            "category": "security_testing",
            "content": "Test content for memory exhaustion",
            "metadata": {"large_array": large_array},
            "created_by": "security_test"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)

        # Should either succeed or fail gracefully
        if response.status_code == 201:
            prompt = response.json()["data"]
            assert len(prompt["metadata"]["large_array"]) == 100000
        elif response.status_code in [413, 422]:
            # Payload too large or validation error - acceptable
            data = response.json()
            assert "success" in data
            assert data["success"] is False
        else:
            pytest.fail(f"Unexpected status for memory test: {response.status_code}")

    def test_unicode_edge_cases(self, prompt_store_service: TestClient):
        """Test handling of Unicode edge cases."""
        unicode_content = "".join([
            "Basic ASCII",
            "Àáâãäå",  # Latin-1 Supplement
            "αβγδε",  # Greek
            "абвгде",  # Cyrillic
            "中文",  # Chinese
            "العربية",  # Arabic
            "🚀🔥💯",  # Emojis
            "𝄞🎵🎶",  # Musical symbols and emojis
            "\u0000",  # Null byte
            "\uFFFF",  # Non-character
            "𝒜𝒷𝒸𝒹ℰ",  # Mathematical alphanumeric symbols
        ])

        prompt_data = {
            "name": f"unicode_test_{uuid.uuid4().hex[:8]}",
            "category": "edge_case_testing",
            "content": unicode_content,
            "created_by": "edge_case_test"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)

        if response.status_code == 201:
            prompt = response.json()["data"]
            assert prompt["content"] == unicode_content
        elif response.status_code == 422:
            # Unicode validation error is acceptable
            data = response.json()
            assert "success" in data
            assert data["success"] is False
        else:
            pytest.fail(f"Unexpected status for Unicode test: {response.status_code}")

    def test_concurrent_mixed_operations(self, prompt_store_service: TestClient):
        """Test concurrent mixed operations (create, read, update, delete)."""
        # This test would require running operations in parallel threads
        # For now, we'll test sequential mixed operations rapidly

        created_prompts = []

        # Rapid create operations
        for i in range(5):
            prompt_data = {
                "name": f"mixed_op_test_{i}_{uuid.uuid4().hex[:4]}",
                "category": "concurrency_testing",
                "content": f"Content for mixed operation {i}",
                "created_by": "concurrency_test"
            }

            response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
            assert response.status_code == 201
            created_prompts.append(response.json()["data"]["id"])

        # Rapid read operations
        for prompt_id in created_prompts:
            response = prompt_store_service.get(f"/api/v1/prompts/{prompt_id}")
            assert response.status_code == 200

        # Rapid update operations
        for i, prompt_id in enumerate(created_prompts):
            update_data = {
                "content": f"Updated content for mixed operation {i}",
                "updated_by": "concurrency_test"
            }

            response = prompt_store_service.put(f"/api/v1/prompts/{prompt_id}", json=update_data)
            assert response.status_code == 200

        # Verify all operations succeeded
        for prompt_id in created_prompts:
            response = prompt_store_service.get(f"/api/v1/prompts/{prompt_id}")
            assert response.status_code == 200
            prompt = response.json()["data"]
            assert "Updated content" in prompt["content"]
            assert prompt["version"] == 2
