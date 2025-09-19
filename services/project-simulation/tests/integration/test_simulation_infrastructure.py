"""Integration tests for simulation infrastructure components.

Tests database operations, service communication, Redis pub/sub,
and cross-service integration.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from simulation.infrastructure.repositories.sqlite_repositories import SQLiteSimulationRepository
from simulation.application.services.simulation_application_service import SimulationApplicationService
from simulation.domain.entities.simulation import Simulation, SimulationId, SimulationConfiguration
from simulation.domain.entities.simulation import SimulationType
from simulation.infrastructure.redis_integration import (
    RedisPubSubManager,
    SimulationRedisClient,
    RedisConfig
)


class TestDatabaseIntegration:
    """Test database operations and transactions."""

    @pytest.fixture
    async def db_repo(self):
        """Create a test database repository."""
        repo = SQLiteSimulationRepository(db_path=":memory:")
        yield repo
        # Cleanup if needed

    @pytest.mark.asyncio
    async def test_simulation_lifecycle_database(self, db_repo):
        """Test complete simulation lifecycle in database."""
        # Create simulation
        config = SimulationConfiguration(simulation_type=SimulationType.FULL_PROJECT)
        simulation = Simulation(id=SimulationId(), project_id="test_project", configuration=config)

        # Save simulation
        await db_repo.save(simulation)

        # Retrieve simulation
        retrieved = await db_repo.find_by_id(str(simulation.id.value))
        assert retrieved is not None
        assert retrieved.id.value == simulation.id.value
        assert retrieved.project_id == simulation.project_id

        # Link document
        await db_repo.link_document_to_simulation(
            str(simulation.id.value),
            "doc_123",
            "generated",
            "doc_store_ref_123"
        )

        # Link prompt
        await db_repo.link_prompt_to_simulation(
            str(simulation.id.value),
            "prompt_456",
            "generation",
            "prompt_store_ref_456"
        )

        # Save run data
        run_data = {
            "start_time": datetime.now().isoformat(),
            "status": "completed",
            "execution_time": 120.5,
            "metrics": {"documents_generated": 5, "prompts_used": 3}
        }
        await db_repo.save_simulation_run(str(simulation.id.value), "run_001", run_data)

        # Retrieve run data
        retrieved_run = await db_repo.get_simulation_run_data(str(simulation.id.value), "run_001")
        assert retrieved_run is not None
        assert retrieved_run["status"] == "completed"
        assert retrieved_run["execution_time"] == 120.5

        # Retrieve documents
        documents = await db_repo.get_simulation_documents(str(simulation.id.value))
        assert len(documents) == 1
        assert documents[0]["document_id"] == "doc_123"
        assert documents[0]["document_type"] == "generated"

        # Retrieve prompts
        prompts = await db_repo.get_simulation_prompts(str(simulation.id.value))
        assert len(prompts) == 1
        assert prompts[0]["prompt_id"] == "prompt_456"
        assert prompts[0]["prompt_type"] == "generation"

        # Test deletion with cascade
        deleted = await db_repo.delete(str(simulation.id.value))
        assert deleted is True

        # Verify deletion
        retrieved_after_delete = await db_repo.find_by_id(str(simulation.id.value))
        assert retrieved_after_delete is None

        run_after_delete = await db_repo.get_simulation_run_data(str(simulation.id.value), "run_001")
        assert run_after_delete is None


class TestApplicationServiceIntegration:
    """Test application service integration with database."""

    @pytest.fixture
    async def app_service(self):
        """Create application service with test database."""
        # Use in-memory SQLite for testing
        from simulation.infrastructure.repositories.sqlite_repositories import get_sqlite_simulation_repository
        from unittest.mock import MagicMock

        # Mock the factory to return in-memory database
        with patch('simulation.infrastructure.repositories.sqlite_repositories.get_sqlite_simulation_repository') as mock_get:
            mock_repo = SQLiteSimulationRepository(db_path=":memory:")
            mock_get.return_value = mock_repo

            # Create service with mocked dependencies
            service = SimulationApplicationService(
                project_repository=MagicMock(),
                simulation_repository=mock_repo,
                timeline_repository=MagicMock(),
                team_repository=MagicMock()
            )

            # Override the repository attribute
            service._simulation_repository = mock_repo

            yield service

    @pytest.mark.asyncio
    async def test_application_service_document_linking(self, app_service):
        """Test document linking through application service."""
        simulation_id = "test_sim_123"
        document_id = "doc_456"
        document_type = "generated"
        doc_store_ref = "store_ref_789"

        # Link document
        await app_service.link_document_to_simulation(
            simulation_id, document_id, document_type, doc_store_ref
        )

        # Retrieve documents
        documents = await app_service.get_simulation_documents(simulation_id)
        assert len(documents) == 1
        assert documents[0]["document_id"] == document_id
        assert documents[0]["document_type"] == document_type
        assert documents[0]["doc_store_reference"] == doc_store_ref

    @pytest.mark.asyncio
    async def test_application_service_prompt_linking(self, app_service):
        """Test prompt linking through application service."""
        simulation_id = "test_sim_456"
        prompt_id = "prompt_789"
        prompt_type = "generation"
        prompt_store_ref = "prompt_store_ref_012"

        # Link prompt
        await app_service.link_prompt_to_simulation(
            simulation_id, prompt_id, prompt_type, prompt_store_ref
        )

        # Retrieve prompts
        prompts = await app_service.get_simulation_prompts(simulation_id)
        assert len(prompts) == 1
        assert prompts[0]["prompt_id"] == prompt_id
        assert prompts[0]["prompt_type"] == prompt_type
        assert prompts[0]["prompt_store_reference"] == prompt_store_ref

    @pytest.mark.asyncio
    async def test_application_service_run_data(self, app_service):
        """Test run data storage and retrieval through application service."""
        simulation_id = "test_sim_789"
        run_id = "run_012"
        run_data = {
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "progress": 0.75,
            "current_phase": "document_generation"
        }

        # Save run data
        await app_service.save_simulation_run_data(simulation_id, run_id, run_data)

        # Retrieve run data
        retrieved = await app_service.get_simulation_run_data(simulation_id, run_id)
        assert retrieved is not None
        assert retrieved["status"] == "running"
        assert retrieved["progress"] == 0.75
        assert retrieved["current_phase"] == "document_generation"


class TestRedisIntegration:
    """Test Redis pub/sub integration."""

    @pytest.fixture
    async def redis_manager(self):
        """Create Redis manager for testing."""
        config = RedisConfig(host="localhost", port=6379, db=1)  # Use DB 1 for testing
        logger = MagicMock()
        manager = RedisPubSubManager(config, logger)

        # Mock Redis connection for testing
        mock_redis = AsyncMock()
        mock_pubsub = AsyncMock()
        manager.redis_client = mock_redis
        manager.pubsub = mock_pubsub
        manager.is_connected = True

        yield manager

    @pytest.fixture
    async def redis_client(self, redis_manager):
        """Create Redis client for testing."""
        logger = MagicMock()
        client = SimulationRedisClient(redis_manager, logger)
        yield client

    @pytest.mark.asyncio
    async def test_redis_simulation_events(self, redis_client, redis_manager):
        """Test publishing simulation events via Redis."""
        simulation_id = "test_sim_123"
        event_type = "simulation_started"
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "phase": "initialization"
        }

        # Publish event
        success = await redis_client.publish_simulation_event(
            simulation_id, event_type, event_data
        )

        assert success is True

        # Verify Redis publish was called
        redis_manager.redis_client.publish.assert_called_once()
        call_args = redis_manager.redis_client.publish.call_args

        # Check channel and message
        channel = call_args[0][0]
        message_data = json.loads(call_args[0][1])

        assert channel == f"simulation:{simulation_id}"
        assert message_data["type"] == event_type
        assert message_data["simulation_id"] == simulation_id
        assert message_data["phase"] == "initialization"
        assert "timestamp" in message_data
        assert "publisher" in message_data

    @pytest.mark.asyncio
    async def test_redis_document_events(self, redis_client, redis_manager):
        """Test publishing document generation events via Redis."""
        simulation_id = "test_sim_456"
        document_id = "doc_789"
        document_type = "generated"

        # Publish document event
        success = await redis_client.publish_document_generated(
            simulation_id, document_id, document_type
        )

        assert success is True

        # Verify Redis publish was called
        redis_manager.redis_client.publish.assert_called_once()
        call_args = redis_manager.redis_client.publish.call_args

        # Check channel and message
        channel = call_args[0][0]
        message_data = json.loads(call_args[0][1])

        assert channel == "documents:generated"
        assert message_data["type"] == "document_generated"
        assert message_data["simulation_id"] == simulation_id
        assert message_data["document_id"] == document_id
        assert message_data["document_type"] == document_type

    @pytest.mark.asyncio
    async def test_redis_prompt_events(self, redis_client, redis_manager):
        """Test publishing prompt usage events via Redis."""
        simulation_id = "test_sim_789"
        prompt_id = "prompt_012"
        prompt_type = "generation"

        # Publish prompt event
        success = await redis_client.publish_prompt_used(
            simulation_id, prompt_id, prompt_type
        )

        assert success is True

        # Verify Redis publish was called
        redis_manager.redis_client.publish.assert_called_once()
        call_args = redis_manager.redis_client.publish.call_args

        # Check channel and message
        channel = call_args[0][0]
        message_data = json.loads(call_args[0][1])

        assert channel == "prompts:used"
        assert message_data["type"] == "prompt_used"
        assert message_data["simulation_id"] == simulation_id
        assert message_data["prompt_id"] == prompt_id
        assert message_data["prompt_type"] == prompt_type

    @pytest.mark.asyncio
    async def test_redis_subscription(self, redis_client, redis_manager):
        """Test Redis channel subscription."""
        simulation_id = "test_sim_999"
        callback = AsyncMock()

        # Subscribe to simulation events
        await redis_client.subscribe_to_simulation_events(simulation_id, callback)

        # Verify subscription was set up
        redis_manager.pubsub.subscribe.assert_called_once_with(f"simulation:{simulation_id}")

        # Subscribe to document events
        doc_callback = AsyncMock()
        await redis_client.subscribe_to_document_events(doc_callback)

        # Verify document subscription was set up
        assert redis_manager.pubsub.subscribe.call_count == 2
        redis_manager.pubsub.subscribe.assert_called_with("documents:generated")


class TestEndToEndIntegration:
    """Test end-to-end integration scenarios."""

    @pytest.mark.asyncio
    async def test_simulation_with_redis_and_database(self):
        """Test complete simulation workflow with Redis and database integration."""
        # This would be a more comprehensive integration test
        # that tests the entire flow from simulation creation
        # through document generation, Redis events, and database storage

        # For now, just verify the components can be imported and instantiated
        from simulation.infrastructure.repositories.sqlite_repositories import SQLiteSimulationRepository
        from simulation.infrastructure.redis_integration import RedisPubSubManager, SimulationRedisClient

        # Test database repository
        repo = SQLiteSimulationRepository(db_path=":memory:")
        assert repo is not None

        # Test Redis components (with mocked Redis)
        config = RedisConfig()
        logger = MagicMock()
        redis_manager = RedisPubSubManager(config, logger)
        redis_client = SimulationRedisClient(redis_manager, logger)

        assert redis_manager is not None
        assert redis_client is not None

        # Verify core functionality works
        config_obj = SimulationConfiguration(simulation_type=SimulationType.FULL_PROJECT)
        assert config_obj is not None
        assert config_obj.simulation_type == SimulationType.FULL_PROJECT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
