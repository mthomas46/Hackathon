"""
Example: Integrating Discovery Agent and Service Mesh

This example shows how services can use both the Discovery Agent
for registration and the Service Mesh for intelligent routing.
"""

import asyncio
from services.shared.utilities import (
    # Discovery integration
    attach_self_register,

    # Service mesh integration
    get_service_mesh_service, register_mesh_service,

    # Health and resilience
    get_health_check_service, register_health_checks,
    get_circuit_breaker_service,

    # Logging
    get_logging_service, with_correlation_id
)

# Example service that integrates both discovery and service mesh
class ExampleService:
    def __init__(self, service_name: str, host: str = "localhost", port: int = 8080):
        self.service_name = service_name
        self.host = host
        self.port = port

        # Initialize components
        self.logger = get_logging_service().get_logger(service_name)
        self.mesh = get_service_mesh_service()
        self.health_service = get_health_check_service()
        self.circuit_breaker = get_circuit_breaker_service()

    async def initialize(self):
        """Initialize service with discovery and mesh integration."""

        # 1. Register with Discovery Agent
        await attach_self_register(
            app=None,  # Your FastAPI app
            service_name=self.service_name,
            service_port=self.port
        )

        # 2. Register with Service Mesh
        register_mesh_service(
            service_name=self.service_name,
            host=self.host,
            port=self.port
        )

        # 3. Setup health checks
        register_health_checks(
            self.service_name,
            [
                # Add your health checks here
            ]
        )

        # 4. Initialize service mesh
        await self.mesh.initialize()

        # 5. Sync mesh with discovery agent
        await self.mesh.sync_with_discovery_agent()

        self.logger.info(f"{self.service_name} initialized with discovery and mesh integration")

    async def call_other_service(self, target_service: str, path: str, **kwargs):
        """Call another service through the service mesh."""

        with with_correlation_id() as correlation_id:
            self.logger.info_with_context(
                f"Calling {target_service}",
                operation="service_call",
                target_service=target_service,
                path=path
            )

            try:
                # Use service mesh for routing (includes load balancing, circuit breaker, etc.)
                result = await self.mesh.route_request(
                    target_service,
                    path,
                    request_context={"correlation_id": correlation_id},
                    **kwargs
                )

                self.logger.info_with_context(
                    f"Call to {target_service} successful",
                    operation="service_call_success",
                    status_code=result.get("status_code", "unknown")
                )

                return result

            except Exception as e:
                self.logger.error_with_context(
                    f"Call to {target_service} failed: {e}",
                    operation="service_call_failed",
                    error=str(e)
                )
                raise

    async def handle_incoming_request(self, request_data: dict):
        """Handle incoming request with proper correlation."""

        # Extract or generate correlation ID
        correlation_id = request_data.get("correlation_id")
        if not correlation_id:
            correlation_id = None  # Will generate new one

        with with_correlation_id(correlation_id) as corr_id:
            self.logger.info_with_context(
                "Processing incoming request",
                operation="request_processing",
                request_data=request_data
            )

            # Your request processing logic here
            result = {"correlation_id": corr_id, "processed": True}

            self.logger.info_with_context(
                "Request processing complete",
                operation="request_complete",
                result=result
            )

            return result

# Example usage
async def main():
    """Example of how to use the integrated services."""

    # Create service instance
    service = ExampleService("example-service", port=8080)

    # Initialize with discovery and mesh
    await service.initialize()

    # Example: Call another service through mesh
    try:
        result = await service.call_other_service(
            "user-service",
            "/api/users/123",
            method="GET"
        )
        print(f"User service response: {result}")
    except Exception as e:
        print(f"Service call failed: {e}")

    # Example: Handle incoming request
    incoming_request = {"action": "get_data", "id": "123"}
    response = await service.handle_incoming_request(incoming_request)
    print(f"Response: {response}")

    # Check mesh status
    mesh_status = service.mesh.get_mesh_status()
    print(f"Service mesh status: {mesh_status}")

if __name__ == "__main__":
    asyncio.run(main())
