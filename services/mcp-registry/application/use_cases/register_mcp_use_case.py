"""Register MCP Use Case."""

import logging

from services.mcp_registry.domain.entities.registry_entry import RegistryEntry
from services.mcp_registry.domain.repositories.registry_repository import RegistryRepository
from services.mcp_registry.domain.repositories.package_storage_repository import PackageStorageRepository
from services.mcp_registry.application.dto.register_mcp_request import RegisterMCPRequest
from services.mcp_registry.application.dto.registry_entry_response import RegistryEntryResponse
from services.mcp_registry.domain.value_objects.registry_status import RegistryStatus

logger = logging.getLogger(__name__)


class RegisterMCPUseCase:
    """Use case for registering an MCP in the registry."""
    
    def __init__(
        self,
        registry_repository: RegistryRepository,
        storage_repository: PackageStorageRepository,
    ):
        self.registry_repo = registry_repository
        self.storage_repo = storage_repository
    
    async def execute(self, request: RegisterMCPRequest) -> RegistryEntryResponse:
        """Register MCP in registry."""
        logger.info(f"Registering MCP: {request.mcp_id}")
        
        # Verify storage exists
        if not await self.storage_repo.exists(request.storage_location):
            raise ValueError(f"Storage location not found: {request.storage_location}")
        
        # Get package data to create entry
        # TODO: Load full package and create entry
        # For now, create placeholder entry
        
        raise NotImplementedError("RegisterMCPUseCase not yet fully implemented")

