"""Health Checker for MCP instances."""

import asyncio
import logging
from typing import Optional

import httpx

from services.mcp_gateway.application.use_cases.update_health_use_case import UpdateHealthUseCase
from services.mcp_gateway.domain.repositories.mcp_registry_repository import MCPRegistryRepository
from services.mcp_gateway.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


class HealthChecker:
    """
    Background health checker for MCP instances.
    
    Periodically checks instance health and updates their status.
    """
    
    def __init__(
        self,
        registry: MCPRegistryRepository,
        update_health_use_case: UpdateHealthUseCase,
        settings: Settings
    ):
        """
        Initialize the health checker.
        
        Args:
            registry: Registry repository for finding instances
            update_health_use_case: Use case for updating health
            settings: Application settings
        """
        self.registry = registry
        self.update_health_use_case = update_health_use_case
        self.settings = settings
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the health checker background task."""
        if self._running:
            logger.warning("Health checker is already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._health_check_loop())
        logger.info(
            f"Health checker started (interval={self.settings.health_check_interval_seconds}s)"
        )
    
    async def stop(self) -> None:
        """Stop the health checker background task."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Health checker stopped")
    
    async def _health_check_loop(self) -> None:
        """Main loop for health checking."""
        while self._running:
            try:
                await self._check_all_instances()
            except Exception as e:
                logger.error(f"Error in health check loop: {e}", exc_info=True)
            
            # Wait for next interval
            await asyncio.sleep(self.settings.health_check_interval_seconds)
    
    async def _check_all_instances(self) -> None:
        """Check health of all registered instances."""
        try:
            # Get all instances
            instances = await self.registry.find_all()
            
            if not instances:
                logger.debug("No instances to health check")
                return
            
            logger.debug(f"Checking health of {len(instances)} instances")
            
            # Check health concurrently
            tasks = [
                self._check_instance_health(instance.id, instance.health_check_url)
                for instance in instances
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error checking all instances: {e}", exc_info=True)
    
    async def _check_instance_health(
        self,
        instance_id: str,
        health_check_url: str
    ) -> None:
        """
        Check health of a single instance.
        
        Args:
            instance_id: Instance ID
            health_check_url: Health check endpoint URL
        """
        is_healthy = False
        
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.health_check_timeout_seconds
            ) as client:
                response = await client.get(health_check_url)
                is_healthy = response.status_code == 200
                
                if is_healthy:
                    logger.debug(f"Instance {instance_id} is healthy")
                else:
                    logger.warning(
                        f"Instance {instance_id} unhealthy: status={response.status_code}"
                    )
        
        except httpx.TimeoutException:
            logger.warning(f"Health check timeout for instance {instance_id}")
        except httpx.RequestError as e:
            logger.warning(f"Health check request error for instance {instance_id}: {e}")
        except Exception as e:
            logger.error(
                f"Unexpected error checking instance {instance_id}: {e}",
                exc_info=True
            )
        
        # Update instance health
        try:
            await self.update_health_use_case.execute(instance_id, is_healthy)
        except Exception as e:
            logger.error(
                f"Error updating health for instance {instance_id}: {e}",
                exc_info=True
            )

