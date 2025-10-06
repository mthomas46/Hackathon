"""Provision MCP Use Case - Application Layer.

This use case handles the creation and initial setup of new MCP instances.
"""

import logging
from typing import Optional
import uuid

from services.mcp_provisioner.domain.entities.mcp_instance import MCPInstance
from services.mcp_provisioner.domain.value_objects.mcp_state import MCPState
from services.mcp_provisioner.domain.value_objects.mcp_config import MCPConfig
from services.mcp_provisioner.domain.value_objects.resource_limits import ResourceLimits
from services.mcp_provisioner.domain.repositories.mcp_repository import MCPRepository
from services.mcp_provisioner.application.dto.provision_request_dto import ProvisionRequestDTO
from services.mcp_provisioner.application.dto.operation_result_dto import OperationResultDTO
from services.mcp_provisioner.application.dto.mcp_status_dto import MCPStatusDTO


logger = logging.getLogger(__name__)


class ProvisionMCPUseCase:
    """
    Use case for provisioning a new MCP instance.
    
    This use case:
    1. Validates the provision request
    2. Creates an MCPInstance entity (in COLD state)
    3. Persists the instance via repository
    4. Returns status DTO
    
    Note: This creates the MCP record but doesn't start the container.
    Use StartMCPUseCase to actually start the container.
    """
    
    def __init__(self, repository: MCPRepository):
        """
        Initialize the use case.
        
        Args:
            repository: MCP repository for persistence
        """
        self.repository = repository
    
    async def execute(self, request: ProvisionRequestDTO) -> OperationResultDTO:
        """
        Execute the provision use case.
        
        Args:
            request: Provision request DTO
        
        Returns:
            OperationResultDTO with MCPStatusDTO data on success
        """
        try:
            logger.info(f"Provisioning MCP for client: {request.client_id}, tier: {request.tier}")
            
            # Create MCPConfig value object
            resource_limits = ResourceLimits(
                memory=request.memory_limit,
                cpu_shares=request.cpu_shares,
            )
            
            mcp_config = MCPConfig(
                client_id=request.client_id,
                image_name=request.image_name,
                network_name=request.network_name,
                chromadb_path=request.chromadb_path,
                neo4j_uri=request.neo4j_uri,
                api_port=request.api_port,
                environment_vars=request.environment_vars,
                resource_limits=resource_limits.to_docker_kwargs(),
            )
            
            # Create MCPInstance entity
            mcp_instance = MCPInstance(
                id=str(uuid.uuid4()),
                client_id=request.client_id,
                name=f"mcp-{request.client_id}-tier{request.tier}",
                mcp_config=mcp_config,
                state=MCPState.COLD,
                metadata={
                    "tier": request.tier,
                    **request.metadata,
                },
            )
            
            # Persist the instance
            await self.repository.save(mcp_instance)
            
            logger.info(f"Successfully provisioned MCP: {mcp_instance.id}")
            
            # Convert to status DTO
            status_dto = MCPStatusDTO.from_entity(mcp_instance)
            status_dto.tier = request.tier  # Ensure tier is set
            
            return OperationResultDTO.success(
                message=f"MCP instance provisioned successfully: {mcp_instance.id}",
                data=status_dto,
                mcp_id=mcp_instance.id,
            )
            
        except ValueError as e:
            logger.error(f"Validation error during provisioning: {e}")
            return OperationResultDTO.failure(
                message="Validation error",
                errors=[str(e)],
            )
        
        except Exception as e:
            logger.error(f"Unexpected error during provisioning: {e}", exc_info=True)
            return OperationResultDTO.failure(
                message="Failed to provision MCP instance",
                errors=[str(e)],
            )

