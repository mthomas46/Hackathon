"""Tests for A/B testing domain.

Tests covering repository, service, and handler layers for A/B testing functionality.
"""

import pytest
from unittest.mock import Mock, patch

from services.prompt_store.domain.ab_testing.repository import ABTestRepository
from services.prompt_store.domain.ab_testing.service import ABTestService
from services.prompt_store.domain.ab_testing.handlers import ABTestHandlers
from services.prompt_store.core.models import ABTestCreate


@pytest.mark.unit
class TestABTestRepository:
    """Test ABTestRepository operations."""

    def test_create_ab_test_success(self, prompt_store_db, clean_db):
        """Test successful A/B test creation."""
        from services.prompt_store.domain.prompts.service import PromptService
        import uuid

        prompt_service = PromptService()

        # Create test prompts with unique names
        unique_id = str(uuid.uuid4())[:8]
        prompt_a = prompt_service.create_entity({
            "name": f"ab_test_prompt_a_{unique_id}",
            "category": "test",
            "content": "Version A content",
            "created_by": "test_user"
        })
        prompt_b = prompt_service.create_entity({
            "name": f"ab_test_prompt_b_{unique_id}",
            "category": "test",
            "content": "Version B content",
            "created_by": "test_user"
        })

        repo = ABTestRepository()
        test_data = {
            "name": f"test_ab_experiment_{unique_id}",
            "description": "A/B test for prompt effectiveness",
            "prompt_a_id": prompt_a.id,
            "prompt_b_id": prompt_b.id,
            "traffic_percentage": 50,
            "created_by": "test_user"
        }

        ab_test = repo.create_ab_test(test_data)
        assert ab_test.name == f"test_ab_experiment_{unique_id}"
        assert ab_test.prompt_a_id == prompt_a.id
        assert ab_test.prompt_b_id == prompt_b.id
        assert ab_test.traffic_percentage == 50
        assert ab_test.status == "active"

    def test_get_ab_test_found(self, prompt_store_db):
        """Test getting existing A/B test."""
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()

        prompt_a = prompt_service.create_entity({
            "name": "get_test_a",
            "category": "test",
            "content": "Version A",
            "created_by": "test_user"
        })
        prompt_b = prompt_service.create_entity({
            "name": "get_test_b",
            "category": "test",
            "content": "Version B",
            "created_by": "test_user"
        })

        repo = ABTestRepository()
        test_data = {
            "name": "get_test_experiment",
            "prompt_a_id": prompt_a.id,
            "prompt_b_id": prompt_b.id,
            "traffic_percentage": 30,
            "created_by": "test_user"
        }

        created = repo.create_ab_test(test_data)
        retrieved = repo.get_ab_test(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "get_test_experiment"

    def test_record_test_result_success(self, prompt_store_db):
        """Test recording A/B test results."""
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()

        prompt_a = prompt_service.create_entity({
            "name": "result_test_a",
            "category": "test",
            "content": "Version A",
            "created_by": "test_user"
        })

        repo = ABTestRepository()
        test_data = {
            "name": "result_test_experiment",
            "prompt_a_id": prompt_a.id,
            "prompt_b_id": prompt_a.id,  # Same prompt for simplicity
            "traffic_percentage": 50,
            "created_by": "test_user"
        }

        ab_test = repo.create_ab_test(test_data)

        # Record test result
        result = repo.record_test_result(ab_test.id, prompt_a.id, 0.85, 100, "test_session")
        assert result is not None
        assert result.metric_value == 0.85
        assert result.sample_size == 100


@pytest.mark.unit
class TestABTestService:
    """Test ABTestService business logic."""

    def test_create_ab_test_success(self, prompt_store_db):
        """Test successful A/B test creation through service."""
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()

        prompt_a = prompt_service.create_entity({
            "name": "service_test_a",
            "category": "test",
            "content": "Version A",
            "created_by": "test_user"
        })
        prompt_b = prompt_service.create_entity({
            "name": "service_test_b",
            "category": "test",
            "content": "Version B",
            "created_by": "test_user"
        })

        service = ABTestService()
        result = service.create_ab_test({
            "name": "service_test_experiment",
            "description": "Service layer test",
            "prompt_a_id": prompt_a.id,
            "prompt_b_id": prompt_b.id,
            "traffic_percentage": 75,
            "created_by": "test_user"
        })

        assert result["name"] == "service_test_experiment"
        assert result["traffic_percentage"] == 75
        assert result["status"] == "active"

    def test_get_ab_test_results(self, prompt_store_db):
        """Test getting A/B test results."""
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()

        prompt_a = prompt_service.create_entity({
            "name": "results_test_a",
            "category": "test",
            "content": "Version A",
            "created_by": "test_user"
        })

        service = ABTestService()
        ab_test = service.create_ab_test({
            "name": "results_test_experiment",
            "prompt_a_id": prompt_a.id,
            "prompt_b_id": prompt_a.id,
            "traffic_percentage": 50,
            "created_by": "test_user"
        })

        # Record some results
        service.record_test_result(ab_test["id"], prompt_a.id, 0.9, 50, "session_1")
        service.record_test_result(ab_test["id"], prompt_a.id, 0.85, 75, "session_2")

        # Get results
        results = service.get_test_results(ab_test["id"])
        assert len(results) >= 2
        assert all(r["metric_value"] >= 0.8 for r in results)

    def test_select_prompt_variant(self, prompt_store_db):
        """Test prompt variant selection for A/B test."""
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()

        prompt_a = prompt_service.create_entity({
            "name": "variant_test_a",
            "category": "test",
            "content": "Version A",
            "created_by": "test_user"
        })
        prompt_b = prompt_service.create_entity({
            "name": "variant_test_b",
            "category": "test",
            "content": "Version B",
            "created_by": "test_user"
        })

        service = ABTestService()
        ab_test = service.create_ab_test({
            "name": "variant_test_experiment",
            "prompt_a_id": prompt_a.id,
            "prompt_b_id": prompt_b.id,
            "traffic_percentage": 50,
            "created_by": "test_user"
        })

        # Select variant multiple times
        variants = []
        for _ in range(20):
            variant = service.select_prompt_variant(ab_test["id"], f"user_{_}")
            variants.append(variant)

        # Should get both variants (approximately 50/50)
        a_count = sum(1 for v in variants if v == prompt_a.id)
        b_count = sum(1 for v in variants if v == prompt_b.id)
        assert a_count > 0 and b_count > 0


@pytest.mark.unit
class TestABTestHandlers:
    """Test ABTestHandlers HTTP operations."""

    @pytest.mark.asyncio
    async def test_handle_create_ab_test_success(self):
        """Test successful A/B test creation handler."""
        handlers = ABTestHandlers()

        with patch.object(handlers.service, 'create_ab_test') as mock_create:
            mock_create.return_value = {
                "id": "test_ab_test_id",
                "name": "test_experiment",
                "status": "active",
                "traffic_percentage": 50
            }

            test_data = ABTestCreate(
                name="test_experiment",
                prompt_a_id="prompt_a_id",
                prompt_b_id="prompt_b_id",
                traffic_percentage=50
            )

            result = await handlers.handle_create_ab_test(test_data)

            assert result.success is True
            assert result.data["name"] == "test_experiment"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_get_ab_test_success(self):
        """Test successful A/B test retrieval handler."""
        handlers = ABTestHandlers()

        with patch.object(handlers.service, 'get_ab_test') as mock_get:
            mock_get.return_value = {
                "id": "test_id",
                "name": "test_experiment",
                "status": "active",
                "traffic_percentage": 50
            }

            result = await handlers.handle_get_ab_test("test_id")

            assert result.success is True
            assert result.data["status"] == "active"
            mock_get.assert_called_once_with("test_id")

    @pytest.mark.asyncio
    async def test_handle_select_variant_success(self):
        """Test successful variant selection handler."""
        handlers = ABTestHandlers()

        with patch.object(handlers.service, 'select_prompt_variant') as mock_select:
            mock_select.return_value = "prompt_a_id"

            result = await handlers.handle_select_variant("test_id", "user_123")

            assert result.success is True
            assert result.data["selected_prompt_id"] == "prompt_a_id"
            mock_select.assert_called_once_with("test_id", "user_123")

    @pytest.mark.asyncio
    async def test_handle_get_test_results_success(self):
        """Test successful test results retrieval handler."""
        handlers = ABTestHandlers()

        with patch.object(handlers.service, 'get_ab_test_results') as mock_results:
            mock_results.return_value = [
                {"metric_value": 0.85, "sample_size": 100},
                {"metric_value": 0.90, "sample_size": 150}
            ]

            result = await handlers.handle_get_test_results("test_id")

            assert result.success is True
            assert len(result.data["results"]) == 2
            mock_results.assert_called_once_with("test_id")
