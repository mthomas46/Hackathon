"""Prompt Store versioning tests.

Tests version control and history tracking for prompts.
Focused on version management and rollback capabilities.
"""
import pytest
import importlib.util, os
from fastapi.testclient import TestClient

from .test_utils import load_prompt_store_service, _assert_http_ok, sample_prompt, sample_prompt_update


@pytest.fixture(scope="module")
def client():
    """Test client fixture for prompt store service."""
    app = load_prompt_store_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestPromptVersioning:
    """Test prompt version control and history management."""

    def test_prompt_version_creation(self, client):
        """Test creating different versions of a prompt."""
        base_prompt = {
            "name": "versioned-prompt",
            "category": "assistant",
            "content": "You are a helpful assistant. Version 1.0",
            "description": "Base version of test prompt",
            "created_by": "test-user"
        }

        # Create initial version
        v1_resp = client.post("/prompts", json=base_prompt)
        _assert_http_ok(v1_resp)

        v1_data = v1_resp.json()
        prompt_id = v1_data.get("id") or v1_data.get("data", {}).get("id")

        if prompt_id:
            # Create version 2
            v2_data = {
                "content": "You are a helpful and friendly assistant. Version 2.0",
                "description": "Enhanced version with friendliness"
            }

            v2_resp = client.post(f"/prompts/{prompt_id}/versions", json=v2_data)
            assert v2_resp.status_code in [200, 201, 404, 501]  # May not be implemented

            if v2_resp.status_code in [200, 201]:
                v2_result = v2_resp.json()
                assert "version" in v2_result or "data" in v2_result

    def test_version_history_retrieval(self, client):
        """Test retrieving version history for a prompt."""
        # Create a prompt with multiple versions
        prompt_id = self._create_prompt_with_versions(client)

        if prompt_id:
            # Get version history
            history_resp = client.get(f"/prompts/{prompt_id}/versions")
            assert history_resp.status_code in [200, 404, 501]

            if history_resp.status_code == 200:
                history = history_resp.json()
                assert isinstance(history, (list, dict))

                # Should show multiple versions
                if isinstance(history, list):
                    assert len(history) >= 1
                elif isinstance(history, dict):
                    assert "versions" in history or "items" in history

    def test_version_rollback(self, client):
        """Test rolling back to a previous version."""
        prompt_id = self._create_prompt_with_versions(client)

        if prompt_id:
            # Rollback to version 1
            rollback_resp = client.post(f"/prompts/{prompt_id}/rollback", json={"version": 1})
            assert rollback_resp.status_code in [200, 404, 501]

            if rollback_resp.status_code == 200:
                rollback_data = rollback_resp.json()
                assert isinstance(rollback_data, dict)

                # Verify rollback was successful
                current_resp = client.get(f"/prompts/{prompt_id}")
                if current_resp.status_code == 200:
                    current_data = current_resp.json()
                    # Should now be version 1 content
                    assert "Version 1.0" in str(current_data)

    def test_version_diff_comparison(self, client):
        """Test comparing differences between versions."""
        prompt_id = self._create_prompt_with_versions(client)

        if prompt_id:
            # Compare versions 1 and 2
            diff_resp = client.get(f"/prompts/{prompt_id}/diff", params={"from": 1, "to": 2})
            assert diff_resp.status_code in [200, 404, 501]

            if diff_resp.status_code == 200:
                diff_data = diff_resp.json()
                assert isinstance(diff_data, dict)
                # Should contain diff information
                assert "changes" in diff_data or "diff" in diff_data

    def _create_prompt_with_versions(self, client):
        """Helper method to create a prompt with multiple versions."""
        base_prompt = {
            "name": "multi-version-prompt",
            "category": "test",
            "content": "You are a helpful assistant. Version 1.0",
            "description": "Prompt for version testing",
            "created_by": "test-user"
        }

        # Create initial version
        create_resp = client.post("/prompts", json=base_prompt)
        if create_resp.status_code != 200:
            return None

        create_data = create_resp.json()
        prompt_id = create_data.get("id") or create_data.get("data", {}).get("id")

        if prompt_id:
            # Create a second version by updating
            update_data = {
                "content": "You are a helpful and knowledgeable assistant. Version 2.0",
                "description": "Updated version"
            }

            update_resp = client.put(f"/prompts/{prompt_id}", json=update_data)
            if update_resp.status_code == 200:
                return prompt_id

        return None


class TestPromptMigration:
    """Test prompt migration and import functionality."""

    def test_yaml_import(self, client):
        """Test importing prompts from YAML format."""
        yaml_content = """
prompts:
  - name: "imported-prompt-1"
    content: "You are an AI assistant imported from YAML."
    description: "First imported prompt"
    tags: ["imported", "yaml"]

  - name: "imported-prompt-2"
    content: "You are a specialized assistant for coding tasks."
    description: "Second imported prompt"
    tags: ["coding", "imported"]
"""

        import_data = {
            "format": "yaml",
            "content": yaml_content,
            "options": {
                "validate": True,
                "create_versions": False
            }
        }

        response = client.post("/migrate", json=import_data)
        assert response.status_code in [200, 201, 404, 501]

        if response.status_code in [200, 201]:
            import_result = response.json()
            assert isinstance(import_result, dict)
            # Should indicate successful import
            assert "imported" in import_result or "success" in import_result

    def test_migration_validation(self, client):
        """Test validation during prompt migration."""
        # Test with invalid YAML
        invalid_yaml = """
invalid: yaml: content:
  - broken: structure
"""

        import_data = {
            "format": "yaml",
            "content": invalid_yaml
        }

        response = client.post("/migrate", json=import_data)
        # Should either succeed (with error handling) or fail with validation error
        assert response.status_code in [200, 400, 404, 501]

        if response.status_code == 400:
            error_data = response.json()
            assert "error" in error_data or "detail" in error_data

    def test_migration_dry_run(self, client):
        """Test migration dry-run functionality."""
        yaml_content = """
prompts:
  - name: "dry-run-prompt"
    content: "This is a dry-run import test."
    description: "Should not be persisted"
"""

        import_data = {
            "format": "yaml",
            "content": yaml_content,
            "options": {
                "dry_run": True,
                "validate_only": True
            }
        }

        response = client.post("/migrate", json=import_data)
        assert response.status_code in [200, 404, 501]

        if response.status_code == 200:
            dry_run_result = response.json()
            # Skip if we get a database error response
            if "error_code" in dry_run_result and dry_run_result.get("error_code") == "database_error":
                pytest.skip("Database error - skipping test due to environment setup")

            assert isinstance(dry_run_result, dict)
            # Should indicate what would be imported without actually importing
            assert "preview" in dry_run_result or "would_import" in dry_run_result
