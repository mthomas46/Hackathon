# Meta-Orchestrator Core

The core business logic layer of the Meta-Orchestration Service, handling service lifecycle management, Docker operations, and orchestration workflows.

## 📋 Overview

The core module contains the primary business logic for managing the Hackathon ecosystem, providing high-level abstractions over Docker operations and service coordination.

## 📁 Structure

```
core/
├── __init__.py          # Core package initialization
└── orchestrator.py      # Main orchestration logic
```

## 🔧 Core Components

### Meta-Orchestrator (`orchestrator.py`)

The central orchestrator class that coordinates all service operations:

```python
class MetaOrchestrator:
    """Main orchestrator for service lifecycle management"""

    def __init__(self, workspace_path: Path = None):
        self.workspace_path = workspace_path or Path("/app")
        self.docker_manager = DockerManager()
        self.config_manager = ConfigurationManager()
        self.settings = Settings()

    async def initialize(self):
        """Initialize the orchestrator"""
        await self.docker_manager.initialize()
        await self.config_manager.initialize()
        logger.info("🎯 Meta-Orchestrator initialized")

    async def get_services(self) -> List[ServiceInfo]:
        """Get all services from docker-compose configuration"""
        compose_file = self.workspace_path / "docker-compose.dev.yml"

        if not compose_file.exists():
            raise FileNotFoundError(f"Docker Compose file not found: {compose_file}")

        # Parse docker-compose file
        with open(compose_file) as f:
            compose_data = yaml.safe_load(f)

        services = []
        for service_name, service_config in compose_data.get("services", {}).items():
            service_info = ServiceInfo(
                name=service_name,
                image=service_config.get("image", ""),
                ports=service_config.get("ports", []),
                environment=service_config.get("environment", {}),
                volumes=service_config.get("volumes", []),
                depends_on=service_config.get("depends_on", []),
                restart_policy=service_config.get("restart", "no")
            )
            services.append(service_info)

        return services

    async def get_service_info(self, service_name: str) -> Optional[ServiceInfo]:
        """Get detailed information about a specific service"""
        services = await self.get_services()
        return next((s for s in services if s.name == service_name), None)

    async def start_service(self, service_name: str, profile: str = "all") -> bool:
        """Start a specific service"""
        try:
            logger.info(f"🚀 Starting service: {service_name}")

            # Check if service exists
            service_info = await self.get_service_info(service_name)
            if not service_info:
                raise ValueError(f"Service '{service_name}' not found")

            # Check dependencies
            await self._ensure_dependencies_started(service_name, service_info)

            # Start the service
            success = await self.docker_manager.start_service(service_name, profile)

            if success:
                logger.info(f"✅ Service started successfully: {service_name}")

                # Wait for health check
                await self._wait_for_service_healthy(service_name)
            else:
                logger.error(f"❌ Failed to start service: {service_name}")

            return success

        except Exception as e:
            logger.error(f"❌ Error starting service {service_name}: {e}")
            raise

    async def stop_service(self, service_name: str) -> bool:
        """Stop a specific service"""
        try:
            logger.info(f"🛑 Stopping service: {service_name}")

            # Check if service is running
            status = await self.get_service_status(service_name)
            if status != "running":
                logger.warning(f"Service {service_name} is not running (status: {status})")
                return True

            # Stop dependent services first
            await self._stop_dependent_services(service_name)

            # Stop the service
            success = await self.docker_manager.stop_service(service_name)

            if success:
                logger.info(f"✅ Service stopped successfully: {service_name}")
            else:
                logger.error(f"❌ Failed to stop service: {service_name}")

            return success

        except Exception as e:
            logger.error(f"❌ Error stopping service {service_name}: {e}")
            raise

    async def restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        logger.info(f"🔄 Restarting service: {service_name}")

        # Stop the service
        stopped = await self.stop_service(service_name)
        if not stopped:
            return False

        # Brief pause to ensure clean shutdown
        await asyncio.sleep(2)

        # Start the service
        started = await self.start_service(service_name)
        return started

    async def get_service_status(self, service_name: str = None) -> Union[str, Dict[str, str]]:
        """Get status of service(s)"""
        try:
            if service_name:
                # Get status for specific service
                container = await self.docker_manager.get_container(service_name)
                if container:
                    return container.status
                else:
                    return "not_found"
            else:
                # Get status for all services
                services = await self.get_services()
                status_map = {}

                for service in services:
                    container = await self.docker_manager.get_container(service.name)
                    if container:
                        status_map[service.name] = container.status
                    else:
                        status_map[service.name] = "not_deployed"

                return status_map

        except Exception as e:
            logger.error(f"❌ Error getting service status: {e}")
            raise

    async def start_all_services(self, profile: str = "all") -> Dict[str, bool]:
        """Start all services in the ecosystem"""
        logger.info(f"🚀 Starting all services (profile: {profile})")

        services = await self.get_services()
        results = {}

        # Start services in dependency order
        dependency_graph = self._build_dependency_graph(services)

        for service_name in self._topological_sort(dependency_graph):
            try:
                success = await self.start_service(service_name, profile)
                results[service_name] = success
            except Exception as e:
                logger.error(f"❌ Failed to start {service_name}: {e}")
                results[service_name] = False

        successful = sum(1 for success in results.values() if success)
        total = len(results)

        logger.info(f"✅ Started {successful}/{total} services")

        return results

    async def stop_all_services(self) -> Dict[str, bool]:
        """Stop all services in the ecosystem"""
        logger.info("🛑 Stopping all services")

        services = await self.get_services()
        results = {}

        # Stop services in reverse dependency order
        dependency_graph = self._build_dependency_graph(services)

        for service_name in reversed(self._topological_sort(dependency_graph)):
            try:
                success = await self.stop_service(service_name)
                results[service_name] = success
            except Exception as e:
                logger.error(f"❌ Failed to stop {service_name}: {e}")
                results[service_name] = False

        successful = sum(1 for success in results.values() if success)
        total = len(results)

        logger.info(f"✅ Stopped {successful}/{total} services")

        return results

    # Private helper methods
    async def _ensure_dependencies_started(self, service_name: str, service_info: ServiceInfo):
        """Ensure all dependencies are started"""
        for dependency in service_info.depends_on:
            status = await self.get_service_status(dependency)
            if status != "running":
                logger.info(f"📋 Starting dependency: {dependency}")
                await self.start_service(dependency)

    async def _stop_dependent_services(self, service_name: str):
        """Stop services that depend on the given service"""
        services = await self.get_services()

        for service in services:
            if service_name in service.depends_on:
                status = await self.get_service_status(service.name)
                if status == "running":
                    logger.info(f"📋 Stopping dependent service: {service.name}")
                    await self.stop_service(service.name)

    async def _wait_for_service_healthy(self, service_name: str, timeout: int = 60):
        """Wait for service to become healthy"""
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check if service has health endpoint
                service_info = await self.get_service_info(service_name)
                if service_info and hasattr(service_info, 'health_endpoint'):
                    # Perform health check
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(service_info.health_endpoint)
                        if response.status_code == 200:
                            logger.info(f"🏥 Service healthy: {service_name}")
                            return
            except Exception:
                pass  # Health check failed, continue waiting

            await asyncio.sleep(5)

        logger.warning(f"⏰ Service health check timeout: {service_name}")

    def _build_dependency_graph(self, services: List[ServiceInfo]) -> Dict[str, List[str]]:
        """Build dependency graph from services"""
        graph = {}

        for service in services:
            graph[service.name] = service.depends_on or []

        return graph

    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """Topological sort of dependency graph"""
        # Kahn's algorithm
        in_degree = {node: 0 for node in graph}

        for node in graph:
            for dependency in graph[node]:
                if dependency in in_degree:
                    in_degree[dependency] += 1

        queue = [node for node in in_degree if in_degree[node] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for dependent in [n for n in graph if node in graph[n]]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check for cycles
        if len(result) != len(graph):
            raise ValueError("Circular dependency detected in services")

        return result
```

## 🔄 Service Lifecycle Management

### Service States

The orchestrator manages services through several states:

```
not_deployed → stopped → starting → running → stopping → stopped
     ↓             ↓         ↓         ↓         ↓         ↓
   removed     starting   healthy   unhealthy stopping  crashed
```

### Dependency Resolution

The orchestrator automatically handles service dependencies:

```python
# Example docker-compose.yml with dependencies
services:
  database:
    image: postgres:15
    # No dependencies

  redis:
    image: redis:7
    # No dependencies

  api:
    image: myapi:latest
    depends_on:
      - database
      - redis

  web:
    image: nginx:alpine
    depends_on:
      - api
```

**Dependency Resolution Logic:**
1. Parse `depends_on` declarations from docker-compose
2. Build dependency graph
3. Use topological sort for startup order
4. Reverse topological sort for shutdown order
5. Detect and prevent circular dependencies

## 🐳 Docker Integration

### Container Operations

The orchestrator provides high-level abstractions over Docker operations:

```python
class DockerManager:
    """Docker container management"""

    def __init__(self):
        self.docker_client = aiodocker.Docker()

    async def start_service(self, service_name: str, profile: str = "all") -> bool:
        """Start a service using docker-compose"""
        try:
            # Run docker-compose up
            cmd = ["docker-compose", "-f", "docker-compose.dev.yml"]

            if profile != "all":
                cmd.extend(["--profile", profile])

            cmd.extend(["up", "-d", service_name])

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            return process.returncode == 0

        except Exception as e:
            logger.error(f"Docker start failed: {e}")
            return False

    async def stop_service(self, service_name: str) -> bool:
        """Stop a service using docker-compose"""
        try:
            cmd = ["docker-compose", "-f", "docker-compose.dev.yml", "stop", service_name]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            return process.returncode == 0

        except Exception as e:
            logger.error(f"Docker stop failed: {e}")
            return False

    async def get_container(self, service_name: str):
        """Get container information"""
        try:
            containers = await self.docker_client.containers.list(
                filters={"name": f".*{service_name}.*"}
            )

            return containers[0] if containers else None

        except Exception as e:
            logger.error(f"Failed to get container info: {e}")
            return None
```

## ⚙️ Configuration Management

### Service Configuration

The orchestrator manages service configurations from multiple sources:

```python
class ConfigurationManager:
    """Service configuration management"""

    async def load_service_config(self, service_name: str) -> Dict[str, Any]:
        """Load service configuration from all sources"""
        config = {}

        # 1. Load from docker-compose.yml
        compose_config = await self._load_compose_config(service_name)
        config.update(compose_config)

        # 2. Load from service-specific config files
        file_config = await self._load_config_file(service_name)
        config.update(file_config)

        # 3. Load from environment variables
        env_config = self._load_env_config(service_name)
        config.update(env_config)

        # 4. Apply runtime overrides
        runtime_config = await self._load_runtime_config(service_name)
        config.update(runtime_config)

        return config

    async def update_service_config(self, service_name: str, updates: Dict[str, Any]) -> bool:
        """Update service configuration"""
        try:
            # Validate configuration
            validated_config = await self._validate_config(updates)

            # Backup current configuration
            await self._backup_config(service_name)

            # Apply updates
            success = await self._apply_config_updates(service_name, validated_config)

            if success:
                # Restart service if necessary
                if self._requires_restart(validated_config):
                    await self.orchestrator.restart_service(service_name)

            return success

        except Exception as e:
            logger.error(f"Configuration update failed: {e}")
            # Attempt rollback
            await self._rollback_config(service_name)
            return False
```

## 🔄 Orchestration Workflows

### Startup Workflow

```
1. Parse docker-compose.yml
2. Build dependency graph
3. Validate environment
4. Start services in dependency order
5. Wait for health checks
6. Verify startup completion
7. Log results
```

### Shutdown Workflow

```
1. Identify dependent services
2. Stop services in reverse dependency order
3. Wait for graceful shutdown
4. Clean up resources
5. Log results
```

### Configuration Update Workflow

```
1. Validate new configuration
2. Create configuration backup
3. Apply configuration changes
4. Restart service if required
5. Verify service health
6. Log operation results
7. Clean up old backups
```

## 🚨 Error Handling

### Service Operation Errors

```python
class ServiceOperationError(Exception):
    """Base exception for service operation failures"""
    pass

class ServiceNotFoundError(ServiceOperationError):
    """Service not found in configuration"""
    pass

class DependencyError(ServiceOperationError):
    """Service dependency resolution failed"""
    pass

class DockerOperationError(ServiceOperationError):
    """Docker operation failed"""
    pass
```

### Error Recovery

The orchestrator implements comprehensive error recovery:

```python
async def _handle_operation_error(self, operation: str, service_name: str, error: Exception):
    """Handle operation errors with appropriate recovery actions"""
    logger.error(f"Operation '{operation}' failed for {service_name}: {error}")

    # Log error details
    await self._log_operation_error(operation, service_name, error)

    # Attempt recovery based on operation type
    if operation == "start":
        # Retry with exponential backoff
        await self._retry_operation(operation, service_name)
    elif operation == "stop":
        # Force stop if graceful stop fails
        await self._force_stop_service(service_name)
    elif operation == "restart":
        # Reset service state and retry
        await self._reset_service_state(service_name)

    # Notify monitoring system
    await self._notify_monitoring_system(operation, service_name, error)
```

## 📊 Performance Optimization

### Caching

```python
class OrchestratorCache:
    """Cache for expensive operations"""

    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds

    async def get_service_info(self, service_name: str) -> Optional[ServiceInfo]:
        """Get cached service information"""
        cache_key = f"service_info:{service_name}"

        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.ttl:
                return cached_data

        # Cache miss - fetch from source
        service_info = await self._fetch_service_info(service_name)

        if service_info:
            self.cache[cache_key] = (service_info, time.time())

        return service_info
```

### Concurrent Operations

```python
async def start_multiple_services(self, service_names: List[str]) -> Dict[str, bool]:
    """Start multiple services concurrently"""
    # Limit concurrency to prevent resource exhaustion
    semaphore = asyncio.Semaphore(5)

    async def start_with_semaphore(service_name: str):
        async with semaphore:
            return await self.start_service(service_name)

    # Start all services concurrently with limited parallelism
    tasks = [start_with_semaphore(name) for name in service_names]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    return dict(zip(service_names, results))
```

## 🔒 Security Considerations

### Access Control

```python
class AccessController:
    """Control access to orchestration operations"""

    def __init__(self):
        self.permissions = {
            "start_service": ["admin", "operator"],
            "stop_service": ["admin", "operator"],
            "restart_service": ["admin"],
            "update_config": ["admin"],
            "view_logs": ["admin", "operator", "viewer"]
        }

    def check_permission(self, user: str, operation: str, resource: str = None) -> bool:
        """Check if user has permission for operation"""
        user_roles = self._get_user_roles(user)

        allowed_roles = self.permissions.get(operation, [])
        return any(role in allowed_roles for role in user_roles)
```

### Audit Logging

```python
class AuditLogger:
    """Log all orchestration operations for audit purposes"""

    async def log_operation(self, operation: str, service_name: str,
                          user: str, success: bool, details: Dict[str, Any]):
        """Log orchestration operation"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "service_name": service_name,
            "user": user,
            "success": success,
            "details": details,
            "ip_address": self._get_client_ip(),
            "user_agent": self._get_user_agent()
        }

        await self._store_audit_entry(audit_entry)

        # Alert on suspicious operations
        if self._is_suspicious_operation(audit_entry):
            await self._send_security_alert(audit_entry)
```

This core orchestration layer provides the foundation for managing complex microservices ecosystems with reliability, performance, and security in mind.
