"""Provision MCP Use Case - Application Layer.

This use case handles the business logic for provisioning new MCP instances.
"""

import logging
import uuid
import asyncio
import subprocess
from typing import Optional

import docker
from docker.errors import DockerException, APIError

from services.mcp_provisioner.domain.entities.mcp_instance import MCPInstance
from services.mcp_provisioner.domain.repositories.mcp_repository import MCPRepository
from services.mcp_provisioner.domain.value_objects.mcp_config import MCPConfig
from services.mcp_provisioner.domain.value_objects.mcp_state import cold_state, hot_state
from services.mcp_provisioner.domain.value_objects.resource_limits import ResourceLimits
from services.mcp_provisioner.application.dto.provision_request_dto import ProvisionRequestDTO
from services.mcp_provisioner.application.dto.mcp_status_dto import MCPStatusDTO
from services.mcp_provisioner.application.dto.operation_result_dto import OperationResultDTO
from services.mcp_provisioner.infrastructure.external_services.gateway_client import GatewayClient


logger = logging.getLogger(__name__)


class ProvisionMCPUseCase:
    """
    Use case for provisioning a new MCP instance.
    
    Handles:
    1. Validation of provision request
    2. Creation of MCP configuration
    3. Creation of MCP entity
    4. Docker container deployment
    5. Gateway registration
    6. Persistence via repository
    """
    
    def __init__(self, repository: MCPRepository, gateway_client: Optional[GatewayClient] = None):
        self.repository = repository
        self.gateway_client = gateway_client or GatewayClient()
    
    async def execute(self, request: ProvisionRequestDTO) -> OperationResultDTO:
        """
        Execute the provision MCP use case.
        
        Args:
            request: Provision request DTO
        
        Returns:
            OperationResultDTO with MCPStatusDTO data on success
        """
        try:
            logger.info(f"Provisioning MCP for client: {request.client_id}, tier: {request.tier}")
            
            # Step 1: Parse and validate resource limits
            resource_limits = self._parse_resource_limits(request)
            logger.debug(f"Resource limits: {resource_limits}")
            
            # Step 2: Create MCP configuration
            mcp_config = self._create_mcp_config(request)
            logger.debug(f"MCP config created for tier {mcp_config.tier}")
            
            # Step 3: Generate MCP ID
            mcp_id = f"mcp-{request.client_id}-{uuid.uuid4().hex[:8]}"
            mcp_name = f"mcp-{request.client_id}-tier{request.tier}"
            
            # Step 4: Create MCP instance entity with enriched metadata
            mcp_instance = MCPInstance(
                mcp_id=mcp_id,
                config=mcp_config,
                resource_limits=resource_limits,
                state=cold_state(),
                metadata={
                    "client_id": request.client_id,
                    "name": mcp_name,
                    "tier": request.tier,
                    "provisioned_by": "provision_mcp_use_case",
                    "request_metadata": request.metadata,
                    "environment": request.environment_vars,
                    "resource_config": {
                        "memory_limit": request.memory_limit,
                        "cpu_shares": request.cpu_shares,
                    }
                }
            )
            
            # Add client_id and name as attributes for DTO compatibility
            if not hasattr(mcp_instance, 'client_id'):
                object.__setattr__(mcp_instance, 'client_id', request.client_id)
            if not hasattr(mcp_instance, 'name'):
                object.__setattr__(mcp_instance, 'name', mcp_name)
            
            logger.info(f"Created MCP entity: {mcp_id}")
            
            # Step 4.5: Deploy Docker container
            container_id = await self._deploy_docker_container(mcp_instance)
            if container_id:
                logger.info(f"Successfully deployed container {container_id[:12]} for MCP {mcp_id}")
                # Update entity with container info (IMPORTANT: Set on entity, not just metadata!)
                mcp_instance.container_id = container_id
                mcp_instance.metadata["container_id"] = container_id
                mcp_instance.metadata["status"] = "deployed"
                mcp_instance.metadata["deployment_time"] = asyncio.get_event_loop().time()
                
                # Step 4.6: Get container port for gateway registration
                mcp_port = await self._get_container_port(container_id)
                if mcp_port:
                    logger.info(f"Container {container_id[:12]} mapped to host port {mcp_port}")
                    
                    # Step 4.7: Register with Gateway
                    gateway_success = await self.gateway_client.register_mcp(
                        mcp_id=mcp_id,
                        host="localhost",  # TODO: Make this configurable for multi-host deployments
                        port=mcp_port,
                        name=f"{request.client_id} MCP (Tier {request.tier})",
                        tier=request.tier,
                        health_check_url=f"http://localhost:{mcp_port}/health",
                        tags=[request.client_id, f"tier-{request.tier}", "auto-provisioned"],
                        metadata=mcp_instance.metadata
                    )
                    
                    if gateway_success:
                        logger.info(f"✅ MCP {mcp_id} registered with gateway")
                        mcp_instance.metadata["gateway_registered"] = True
                        mcp_instance.metadata["gateway_port"] = mcp_port
                    else:
                        logger.warning(f"⚠️ Failed to register MCP {mcp_id} with gateway")
                        mcp_instance.metadata["gateway_registered"] = False
                else:
                    logger.warning(f"Could not determine host port for container {container_id[:12]}")
                    mcp_instance.metadata["gateway_registered"] = False
                
                # Transition to HOT state since container is running
                object.__setattr__(mcp_instance, 'state', hot_state())
                logger.info(f"MCP {mcp_id} transitioned to HOT state")
            else:
                logger.warning(f"Failed to deploy container for MCP {mcp_id}, keeping in COLD state")
                mcp_instance.metadata["status"] = "deployment_failed"
                mcp_instance.metadata["gateway_registered"] = False
            
            # Step 5: Persist the instance
            await self.repository.save(mcp_instance)
            logger.info(f"Successfully persisted MCP: {mcp_id}")
            
            # Step 6: Convert to status DTO for response
            status_dto = self._entity_to_dto(mcp_instance, request)
            
            return OperationResultDTO.success(
                message=f"MCP instance provisioned successfully: {mcp_id}",
                data=status_dto,
                mcp_id=mcp_id,
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
    
    async def _deploy_docker_container(
        self,
        mcp_instance: MCPInstance
    ) -> Optional[str]:
        """
        Deploy MCP instance as Docker container.
        
        This method:
        1. Connects to Docker daemon
        2. Creates container with proper configuration
        3. Waits for container to become healthy
        4. Returns container ID
        
        Args:
            mcp_instance: MCP instance entity to deploy
        
        Returns:
            Container ID if successful, None otherwise
        """
        try:
            client = docker.from_env()
            logger.info(f"Connected to Docker daemon for MCP {mcp_instance.mcp_id}")
            
            # Build container configuration
            container_name = f"mcp-{mcp_instance.mcp_id}"
            environment = mcp_instance.metadata.get("environment", {})
            
            # Add MCP-specific environment variables
            environment.update({
                "MCP_ID": mcp_instance.mcp_id,
                "MCP_TIER": str(mcp_instance.config.tier),
                "MCP_PORT": str(mcp_instance.config.port),
                "CHROMADB_PATH": mcp_instance.config.chromadb_path,
                "NEO4J_URI": mcp_instance.config.neo4j_uri,
                "DOC_STORE_URL": "http://doc_store:5010",  # Enable MCP to query doc_store for training documents
            })
            
            container_config = {
                "image": mcp_instance.config.docker_image,
                "name": container_name,
                "environment": environment,
                "mem_limit": f"{mcp_instance.resource_limits.memory_limit_mb}m",
                "cpu_shares": int(mcp_instance.resource_limits.cpu_limit * 1024),
                "ports": {
                    f'{mcp_instance.config.port}/tcp': None  # Auto-assign external port
                },
                "network": "ams",  # Same network as other services
                "detach": True,
                "labels": {
                    "mcp.id": mcp_instance.mcp_id,
                    "mcp.tier": str(mcp_instance.config.tier),
                    "mcp.client_id": mcp_instance.metadata.get("client_id", "unknown"),
                    "mcp.provisioner": "mcp-provisioner"
                },
                "healthcheck": {
                    "test": ["CMD", "curl", "-f", f"http://localhost:{mcp_instance.config.port}/health"],
                    "interval": 10_000_000_000,  # 10 seconds in nanoseconds
                    "timeout": 5_000_000_000,    # 5 seconds
                    "retries": 3,
                    "start_period": 30_000_000_000  # 30 seconds start period
                }
            }
            
            logger.info(f"Deploying container {container_name} with image {mcp_instance.config.docker_image}")
            logger.debug(f"Container config: {container_config}")
            
            # Create and start container
            container = client.containers.run(**container_config)
            logger.info(f"Container {container.id[:12]} created and starting...")
            
            # Wait for container to be healthy (up to 60 seconds)
            max_wait_seconds = 60
            for i in range(max_wait_seconds):
                try:
                    container.reload()
                    
                    # Check if container is still running
                    if container.status != "running":
                        logger.warning(f"Container {container.id[:12]} status: {container.status}")
                        if container.status in ["exited", "dead"]:
                            # Get container logs for debugging
                            logs = container.logs(tail=50).decode('utf-8', errors='ignore')
                            logger.error(f"Container {container.id[:12]} failed. Logs:\n{logs}")
                            return None
                        continue
                    
                    # Check health status
                    health = container.attrs.get("State", {}).get("Health", {})
                    health_status = health.get("Status", "unknown")
                    
                    if health_status == "healthy":
                        logger.info(f"✅ Container {container.id[:12]} is healthy after {i+1}s")
                        return container.id
                    elif health_status == "unhealthy":
                        logger.warning(f"Container {container.id[:12]} is unhealthy, waiting...")
                    
                    # Log progress every 10 seconds
                    if (i + 1) % 10 == 0:
                        logger.info(f"Waiting for container {container.id[:12]} to be healthy... ({i+1}/{max_wait_seconds}s)")
                
                except APIError as e:
                    logger.error(f"Docker API error while checking container: {e}")
                    return None
                
                await asyncio.sleep(1)
            
            # Timeout reached
            logger.warning(f"⚠️  Container {container.id[:12]} did not become healthy within {max_wait_seconds}s")
            logger.warning(f"Returning container ID anyway - gateway will handle unhealthy instances")
            
            # Get logs for debugging
            try:
                logs = container.logs(tail=100).decode('utf-8', errors='ignore')
                logger.debug(f"Container logs:\n{logs}")
            except:
                pass
            
            return container.id
            
        except DockerException as e:
            logger.error(f"❌ Docker error deploying MCP {mcp_instance.mcp_id}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error deploying MCP {mcp_instance.mcp_id}: {e}", exc_info=True)
            return None
    
    async def _get_container_port(self, container_id: str) -> Optional[int]:
        """
        Get the dynamically assigned host port for an MCP container.
        
        Uses `docker port` command to retrieve the host port mapping for the container's
        exposed MCP_PORT (default 8080 or 3000).
        
        Args:
            container_id: Docker container ID
        
        Returns:
            Host port number if found, None otherwise
        """
        try:
            # Use docker port command to get port mapping
            result = subprocess.run(
                ['docker', 'port', container_id],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse output for port mappings
                # Example output:
                # 3000/tcp -> 0.0.0.0:54321
                # 8080/tcp -> 0.0.0.0:54322
                for line in result.stdout.split('\n'):
                    if '3000/tcp' in line or '8080/tcp' in line:
                        # Extract port from "0.0.0.0:PORT" or ":::PORT"
                        port_str = line.split(':')[-1].strip()
                        if port_str and port_str.isdigit():
                            port = int(port_str)
                            logger.debug(f"Found port mapping: {port} for container {container_id[:12]}")
                            return port
                
                logger.warning(f"No port mapping found in output: {result.stdout}")
                return None
            else:
                logger.error(f"docker port command failed: {result.stderr}")
                return None
        
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout while getting port for container {container_id[:12]}")
            return None
        except FileNotFoundError:
            logger.error("docker command not found in PATH")
            return None
        except Exception as e:
            logger.error(f"Error getting container port: {e}")
            return None
    
    def _parse_resource_limits(self, request: ProvisionRequestDTO) -> ResourceLimits:
        """
        Parse resource limits from request.
        
        Args:
            request: Provision request DTO
        
        Returns:
            ResourceLimits value object
        """
        # Parse memory limit (e.g., "512m" -> 512 MB, "2g" -> 2048 MB)
        memory_limit_str = request.memory_limit.lower()
        if memory_limit_str.endswith('m'):
            memory_mb = int(memory_limit_str[:-1])
        elif memory_limit_str.endswith('g'):
            memory_mb = int(memory_limit_str[:-1]) * 1024
        else:
            memory_mb = 512  # Default to 512 MB
        
        # Convert CPU shares to CPU limit (1024 shares ≈ 1 CPU core)
        cpu_limit = max(0.5, request.cpu_shares / 1024.0)
        
        # Create resource limits value object
        return ResourceLimits(
            cpu_limit=cpu_limit,
            memory_limit_mb=memory_mb,
            disk_limit_mb=10240  # Default 10 GB
        )
    
    def _create_mcp_config(self, request: ProvisionRequestDTO) -> MCPConfig:
        """
        Create MCP configuration from request.
        
        Args:
            request: Provision request DTO
        
        Returns:
            MCPConfig value object
        """
        # Determine port based on tier (3000-3004)
        port = request.api_port if request.api_port else (3000 + request.tier)
        
        # Set Neo4j URI with defaults
        neo4j_uri = request.neo4j_uri or f"bolt://neo4j:7687"
        
        # Set ChromaDB path with defaults
        chromadb_path = request.chromadb_path or f"/data/chromadb/tier{request.tier}"
        
        # Set Docker image with defaults
        docker_image = request.image_name or f"mcp-server:tier-{request.tier}"
        
        # Merge environment variables with defaults
        env_vars = {
            "TIER": str(request.tier),
            "LOG_LEVEL": "INFO",
            **request.environment_vars
        }
        
        return MCPConfig(
            tier=request.tier,
            docker_image=docker_image,
            port=port,
            chromadb_path=chromadb_path,
            neo4j_uri=neo4j_uri,
            environment_vars=env_vars
        )
    
    def _entity_to_dto(self, instance: MCPInstance, request: ProvisionRequestDTO) -> MCPStatusDTO:
        """
        Convert MCPInstance entity to MCPStatusDTO.
        
        This is a custom mapper since the generic from_entity method may not work
        with our specific entity structure.
        
        Args:
            instance: MCP instance entity
            request: Original provision request (for additional context)
        
        Returns:
            MCPStatusDTO
        """
        return MCPStatusDTO(
            mcp_id=instance.mcp_id,
            client_id=request.client_id,
            name=f"mcp-{request.client_id}-tier{request.tier}",
            state=str(instance.state),  # MCPState has __str__ method
            container_id=instance.container_id,
            ip_address=None,  # Will be set when container is started
            external_port=instance.host_port,
            tier=request.tier,
            image_name=instance.config.docker_image,
            created_at=instance.created_at.isoformat() if instance.created_at else None,
            updated_at=instance.updated_at.isoformat() if instance.updated_at else None,
            last_accessed_at=instance.last_query_time.isoformat() if instance.last_query_time else None,
            metadata={
                "tier": request.tier,
                "resource_limits": {
                    "cpu": instance.resource_limits.cpu_limit,
                    "memory_mb": instance.resource_limits.memory_limit_mb,
                    "disk_mb": instance.resource_limits.disk_limit_mb
                },
                **request.metadata
            },
            health_status="healthy" if instance.is_healthy else "unhealthy"
        )