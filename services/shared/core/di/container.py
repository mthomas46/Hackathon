"""Dependency Injection Container - Enterprise-grade DI framework.

This module provides a comprehensive dependency injection framework that supports:

- Service registration and resolution
- Multiple service lifetimes (singleton, transient, scoped)
- Automatic constructor dependency injection
- Service scoping and lifecycle management
- Thread-safe operations
- Type-safe service resolution
- Graceful error handling and fallbacks

## Architecture

The DI container follows enterprise patterns:

- **Constructor Injection**: Services are injected through constructor parameters
- **Service Locator**: Fallback resolution through global registry
- **Factory Pattern**: Automatic service instantiation with dependency resolution
- **Registry Pattern**: Centralized service registration and discovery
- **Singleton/Scoped/Transient**: Multiple service lifetime management

## Usage Examples

### Basic Service Registration

```python
from services.shared.core.di.container import DependencyContainer, ServiceLifetime

container = DependencyContainer()

# Register a singleton service
container.register_singleton(IMyService, MyServiceImplementation)

# Register a transient service
container.register_transient(IOtherService, OtherServiceImplementation)

# Resolve services
my_service = container.resolve(IMyService)
```

### Constructor Injection

```python
class MyService:
    def __init__(self, logger: ILoggerService, cache: ICacheService):
        self.logger = logger
        self.cache = cache

# Container automatically injects dependencies
service = container.resolve(MyService)
```

### Scoped Services

```python
# Create a service scope
with container.create_scope() as scope:
    # Services in this scope are isolated
    scoped_service = scope.get_service(IScopedService)
    # Scope is automatically disposed
```

## Service Lifetimes

- **Singleton**: Single instance shared across entire application
- **Transient**: New instance created each time requested
- **Scoped**: Single instance per scope/context, disposed when scope ends

## Thread Safety

All container operations are thread-safe and can be used in concurrent environments.
The container uses proper locking mechanisms to ensure data consistency.

## Error Handling

The container provides graceful error handling:
- Missing services return None instead of crashing
- Constructor injection failures are logged with details
- Fallback mechanisms ensure system stability

## Integration

This container integrates with the broader service ecosystem:
- Service Registry for centralized configuration
- Handler Factory for automated handler creation
- Base services for common functionality injection
"""

import asyncio
import inspect
import threading
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Dict, Any, Type, TypeVar, Optional, Union, Callable, Generic, Protocol, List
from enum import Enum
from dataclasses import dataclass, field
from weakref import WeakValueDictionary

T = TypeVar('T')
TService = TypeVar('TService')
TImplementation = TypeVar('TImplementation')


class ServiceLifetime(Enum):
    """Enumeration of service lifetime scopes.

    This enum defines the different lifetime management strategies for services
    registered in the dependency injection container.

    Attributes:
        SINGLETON: Single instance shared across entire application lifetime.
                  Most efficient for stateless services and shared resources.
        TRANSIENT: New instance created each time the service is requested.
                  Best for stateful services or when isolation is required.
        SCOPED: Single instance per scope/context, disposed when scope ends.
               Useful for request-scoped services and per-operation state.
    """
    SINGLETON = "singleton"      # Single instance for entire application
    TRANSIENT = "transient"      # New instance each time requested
    SCOPED = "scoped"            # Single instance per scope/context


class ServiceDescriptor(Generic[T]):
    """Service descriptor for DI container registration.

    This class encapsulates all the metadata and configuration needed to manage
    a service within the dependency injection container. It handles service
    instantiation, lifetime management, and dependency resolution.

    Attributes:
        service_type: The interface/contract type that clients will request
        implementation_type: The concrete class that implements the service
        factory: Optional factory function for custom instantiation logic
        lifetime: Service lifetime management strategy
        instance: Pre-created instance for singleton services
        _lock: Thread synchronization lock for thread-safe operations

    Args:
        service_type: The service interface type
        implementation_type: The concrete implementation type (defaults to service_type)
        factory: Custom factory function for service creation
        lifetime: Service lifetime scope (default: TRANSIENT)
        instance: Pre-created service instance for singletons
    """

    def __init__(self,
                 service_type: Type[T],
                 implementation_type: Optional[Type[T]] = None,
                 factory: Optional[Callable[..., T]] = None,
                 lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
                 instance: Optional[T] = None) -> None:
        """Initialize service descriptor.

        Args:
            service_type: The interface type clients will request
            implementation_type: Concrete implementation class
            factory: Custom factory function for instantiation
            lifetime: Service lifetime management strategy
            instance: Pre-created instance (for singletons)
        """
        self.service_type = service_type
        self.implementation_type = implementation_type or service_type
        self.factory = factory
        self.lifetime = lifetime
        self.instance: Optional[T] = instance
        self._lock = threading.RLock()

    def create_instance(self, container: 'DependencyContainer', *args: Any, **kwargs: Any) -> T:
        """Create a new instance of the service.

        This method handles the complete service instantiation process including:
        - Singleton instance reuse
        - Factory method execution
        - Automatic dependency injection
        - Lifetime management

        Args:
            container: The DI container for dependency resolution
            *args: Positional arguments to pass to constructor/factory
            **kwargs: Keyword arguments to pass to constructor/factory

        Returns:
            New service instance with all dependencies resolved

        Raises:
            RuntimeError: If service creation fails
            ValueError: If required dependencies cannot be resolved
        """
        with self._lock:
            # Return existing singleton instance if available
            if self.instance is not None and self.lifetime == ServiceLifetime.SINGLETON:
                return self.instance

            # Create new instance
            if self.factory:
                # Use custom factory function
                instance = self.factory(container, *args, **kwargs)
            else:
                # Auto-inject dependencies from constructor
                instance = self._create_with_injection(container, *args, **kwargs)

            # Cache singleton instances
            if self.lifetime == ServiceLifetime.SINGLETON:
                self.instance = instance

            return instance

    def _create_with_injection(self, container: 'DependencyContainer', *args: Any, **kwargs: Any) -> T:
        """Create instance with automatic dependency injection.

        This method performs automatic dependency injection by:
        1. Inspecting the constructor signature
        2. Resolving missing parameters from the DI container
        3. Instantiating the service with resolved dependencies

        Args:
            container: The DI container for dependency resolution
            *args: Positional arguments to pass to constructor
            **kwargs: Keyword arguments to pass to constructor

        Returns:
            Service instance with injected dependencies

        Raises:
            RuntimeError: If constructor inspection or instantiation fails
            ValueError: If required dependencies cannot be resolved
        """
        try:
            # Inspect constructor signature for dependency resolution
            signature = inspect.signature(self.implementation_type.__init__)
            parameters = {}

            # Process each constructor parameter
            for param_name, param in signature.parameters.items():
                if param_name == 'self':
                    continue

                if param_name in kwargs:
                    # Use explicitly provided parameter
                    parameters[param_name] = kwargs[param_name]
                elif param.default != inspect.Parameter.empty:
                    # Use default parameter value
                    parameters[param_name] = param.default
                else:
                    # Try to resolve dependency from container
                    try:
                        parameters[param_name] = container.resolve(param.annotation)
                    except Exception as e:
                        if param.default == inspect.Parameter.empty:
                            raise ValueError(
                                f"Cannot resolve dependency '{param_name}' of type '{param.annotation}' "
                                f"for {self.implementation_type}: {e}"
                            ) from e

            # Create instance with resolved dependencies
            return self.implementation_type(*args, **parameters)

        except Exception as e:
            raise RuntimeError(f"Failed to create instance of {self.implementation_type}: {e}") from e


class IServiceProvider(Protocol):
    """Service provider protocol.

    This protocol defines the standard interface for service providers
    in the dependency injection system. It allows for different service
    resolution strategies while maintaining a consistent API.

    The protocol supports both single service resolution and multiple
    service enumeration, enabling flexible service discovery patterns.
    """

    def get_service(self, service_type: Type[T]) -> T:
        """Get service instance.

        Retrieves a single instance of the requested service type.
        For services with multiple implementations, this typically
        returns the primary/default implementation.

        Args:
            service_type: The type of service to retrieve

        Returns:
            Service instance of the requested type

        Raises:
            ValueError: If service type is not registered
        """
        ...

    def get_services(self, service_type: Type[T]) -> List[T]:
        """Get all service instances of type.

        Retrieves all registered instances of the requested service type.
        This is useful when multiple implementations of the same interface
        are registered and all should be available.

        Args:
            service_type: The type of services to retrieve

        Returns:
            List of all service instances of the requested type
        """
        ...


class IServiceScope(Protocol):
    """Service scope protocol.

    This protocol defines the interface for service scopes, which provide
    isolated service instances within a specific context or lifetime.
    Scopes are typically used for request-scoped services or per-operation
    state management.

    Service scopes ensure that services created within the scope are properly
    disposed when the scope ends, preventing resource leaks and ensuring
    proper cleanup of stateful services.
    """

    def get_service(self, service_type: Type[T]) -> T:
        """Get scoped service instance.

        Retrieves a service instance that is scoped to this specific context.
        If the service is scoped, a new instance will be created for this scope
        if one doesn't already exist.

        Args:
            service_type: The type of service to retrieve

        Returns:
            Service instance scoped to this context

        Raises:
            ValueError: If service type is not registered
            RuntimeError: If scope has been disposed
        """
        ...

    def dispose(self) -> None:
        """Dispose of scoped services.

        Cleans up all services that were created within this scope.
        This method should be called when the scope is no longer needed
        to ensure proper resource cleanup and prevent memory leaks.

        After disposal, the scope should not be used for further service
        resolution as it may result in undefined behavior.
        """
        ...


class DependencyContainer(IServiceProvider):
    """Enterprise-grade dependency injection container.

    This is the core class of the dependency injection framework, providing
    comprehensive service registration, resolution, and lifecycle management.
    It implements the IServiceProvider protocol and supports hierarchical
    container composition for complex application architectures.

    ## Key Features

    - **Service Registration**: Register services with different lifetimes
    - **Dependency Resolution**: Automatic constructor injection
    - **Hierarchical Containers**: Parent-child container relationships
    - **Scoped Services**: Request-scoped service management
    - **Thread Safety**: All operations are thread-safe
    - **Type Safety**: Full type checking and validation
    - **Error Resilience**: Graceful handling of missing dependencies

    ## Service Lifetimes

    - **Singleton**: Single shared instance across application
    - **Transient**: New instance each resolution
    - **Scoped**: Single instance per scope context

    ## Usage Patterns

    ```python
    # Create container
    container = DependencyContainer()

    # Register services
    container.register_singleton(ILogger, Logger)
    container.register_transient(IAnalyzer, SemanticAnalyzer)

    # Resolve services
    logger = container.resolve(ILogger)
    analyzer = container.resolve(IAnalyzer)
    ```

    Attributes:
        _parent: Optional parent container for hierarchical resolution
        _services: Dictionary mapping service types to descriptors
        _scoped_services: Weak reference cache for scoped services
        _current_scope: Context variable tracking current service scope
        _lock: Thread synchronization lock
    """

    def __init__(self, parent: Optional['DependencyContainer'] = None) -> None:
        """Initialize dependency injection container.

        Args:
            parent: Optional parent container for hierarchical resolution.
                  Child containers can resolve services from parent containers
                  if not found locally, enabling modular application composition.
        """
        self._parent = parent
        self._services: Dict[Type[Any], ServiceDescriptor[Any]] = {}
        self._scoped_services: WeakValueDictionary[Type[Any], Any] = WeakValueDictionary()
        self._current_scope: ContextVar[Optional['ServiceScope']] = ContextVar('current_scope', default=None)
        self._lock = threading.RLock()

    def register_singleton(self, service_type: Type[T], implementation_type: Optional[Type[T]] = None, instance: Optional[T] = None) -> 'DependencyContainer':
        """Register a singleton service.

        Singleton services share a single instance across the entire application.
        This is the most efficient option for stateless services and shared resources.

        Args:
            service_type: The interface/contract type clients will request
            implementation_type: The concrete class implementing the service
            instance: Optional pre-created instance to use

        Returns:
            Self for method chaining

        Example:
            container.register_singleton(ILogger, FileLogger)
        """
        return self._register(service_type, implementation_type, ServiceLifetime.SINGLETON, instance=instance)

    def register_transient(self, service_type: Type[T], implementation_type: Optional[Type[T]] = None) -> 'DependencyContainer':
        """Register a transient service.

        Transient services create a new instance each time they are requested.
        Use this for stateful services or when isolation between requests is needed.

        Args:
            service_type: The interface/contract type clients will request
            implementation_type: The concrete class implementing the service

        Returns:
            Self for method chaining

        Example:
            container.register_transient(IAnalyzer, SemanticAnalyzer)
        """
        return self._register(service_type, implementation_type, ServiceLifetime.TRANSIENT)

    def register_scoped(self, service_type: Type[T], implementation_type: Optional[Type[T]] = None) -> 'DependencyContainer':
        """Register a scoped service.

        Scoped services create one instance per service scope. Within a scope,
        the same instance is reused, but different scopes get different instances.

        Args:
            service_type: The interface/contract type clients will request
            implementation_type: The concrete class implementing the service

        Returns:
            Self for method chaining

        Example:
            container.register_scoped(IUnitOfWork, DatabaseContext)
        """
        return self._register(service_type, implementation_type, ServiceLifetime.SCOPED)

    def register_factory(self, service_type: Type[T], factory: Callable[..., T], lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> 'DependencyContainer':
        """Register a service with a custom factory function.

        Factory functions provide full control over service instantiation,
        useful for complex initialization logic or third-party libraries.

        Args:
            service_type: The interface/contract type clients will request
            factory: Function that creates service instances
            lifetime: Service lifetime management strategy

        Returns:
            Self for method chaining

        Example:
            def create_database_connection(container):
                config = container.resolve(IConfig)
                return DatabaseConnection(config.connection_string)

            container.register_factory(IDatabase, create_database_connection, ServiceLifetime.SINGLETON)
        """
        descriptor = ServiceDescriptor(service_type, factory=factory, lifetime=lifetime)
        self._services[service_type] = descriptor
        return self

    def register_instance(self, service_type: Type[T], instance: T) -> 'DependencyContainer':
        """Register a pre-created instance as singleton.

        This is useful for services that need special initialization or
        when integrating with existing singleton instances.

        Args:
            service_type: The interface/contract type clients will request
            instance: Pre-created service instance

        Returns:
            Self for method chaining

        Example:
            existing_logger = FileLogger("/var/log/app.log")
            container.register_instance(ILogger, existing_logger)
        """
        descriptor = ServiceDescriptor(service_type, instance=instance, lifetime=ServiceLifetime.SINGLETON)
        self._services[service_type] = descriptor
        return self

    def _register(self, service_type: Type[T], implementation_type: Optional[Type[T]], lifetime: ServiceLifetime, instance: Optional[T] = None) -> 'DependencyContainer':
        """Internal registration method."""
        with self._lock:
            if implementation_type is None:
                implementation_type = service_type

            descriptor = ServiceDescriptor(
                service_type=service_type,
                implementation_type=implementation_type,
                lifetime=lifetime,
                instance=instance
            )

            self._services[service_type] = descriptor
            return self

    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service instance.

        This is the core method for retrieving service instances from the container.
        It implements the service resolution algorithm:

        1. Check current service scope for scoped services
        2. Check local service registry
        3. Check parent container (if hierarchical)
        4. Create instance using registered descriptor

        Args:
            service_type: The type of service to resolve

        Returns:
            Service instance of the requested type

        Raises:
            ValueError: If service type is not registered in this or parent containers

        Example:
            logger = container.resolve(ILogger)
            analyzer = container.resolve(IAnalysisService)
        """
        # Check current scope first for scoped services
        current_scope = self._current_scope.get()
        if current_scope and service_type in current_scope._scoped_instances:
            return current_scope._scoped_instances[service_type]

        # Check local services
        if service_type in self._services:
            descriptor = self._services[service_type]
            return descriptor.create_instance(self)

        # Check parent container
        if self._parent:
            return self._parent.resolve(service_type)

        raise ValueError(f"Service of type '{service_type}' not registered")

    def get_service(self, service_type: Type[T]) -> T:
        """Get service instance (IServiceProvider implementation).

        This method implements the IServiceProvider protocol, providing
        a standard interface for service resolution.

        Args:
            service_type: The type of service to retrieve

        Returns:
            Service instance of the requested type

        Raises:
            ValueError: If service type is not registered
        """
        return self.resolve(service_type)

    def get_services(self, service_type: Type[T]) -> List[T]:
        """Get all service instances of type.

        Retrieves all registered instances of the requested service type.
        This is useful when multiple implementations of the same interface
        exist and all should be available to the consumer.

        The method searches both local and parent containers to provide
        a complete list of all available service instances.

        Args:
            service_type: The type of services to retrieve

        Returns:
            List of all service instances of the requested type

        Example:
            validators = container.get_services(IValidator)
            for validator in validators:
                validator.validate(data)
        """
        services = []

        # Check if service is registered locally
        if service_type in self._services:
            services.append(self.resolve(service_type))

        # Check parent container
        if self._parent:
            parent_services = self._parent.get_services(service_type)
            services.extend(parent_services)

        return services

    def create_scope(self) -> 'ServiceScope':
        """Create a new service scope.

        Service scopes provide isolated service instances within a specific
        context or lifetime. Scoped services will share instances within
        the scope but have separate instances across different scopes.

        This is particularly useful for:
        - Per-request services in web applications
        - Per-operation state management
        - Isolated service instances for testing

        Returns:
            New service scope instance

        Example:
            with container.create_scope() as scope:
                scoped_service = scope.get_service(IScopedService)
                # Service is automatically disposed when scope exits
        """
        return ServiceScope(self)

    def dispose(self) -> None:
        """Dispose of container resources.

        This method cleans up all resources managed by the container:
        - Disposes of singleton service instances
        - Clears service registry
        - Cleans up scoped service references

        Call this method when shutting down the application to ensure
        proper cleanup of resources and prevent memory leaks.

        Note: After disposal, the container should not be used for further
        service resolution as it may result in undefined behavior.
        """
        with self._lock:
            for descriptor in self._services.values():
                if hasattr(descriptor.instance, 'dispose'):
                    try:
                        descriptor.instance.dispose()
                    except Exception:
                        pass  # Ignore disposal errors

            self._services.clear()
            self._scoped_services.clear()


class ServiceScope(IServiceScope):
    """Service scope for managing scoped service instances.

    Service scopes provide isolated service instances within a specific context
    or lifetime. They ensure that scoped services share instances within the
    scope but have separate instances across different scopes.

    ## Key Features

    - **Instance Isolation**: Each scope gets its own service instances
    - **Automatic Cleanup**: Services are disposed when scope ends
    - **Thread Safety**: All operations are thread-safe
    - **Resource Management**: Prevents resource leaks through proper disposal

    ## Usage

    ```python
    # Manual scope management
    scope = container.create_scope()
    try:
        service = scope.get_service(IScopedService)
        # Use service...
    finally:
        scope.dispose()

    # Context manager (recommended)
    with container.create_scope() as scope:
        service = scope.get_service(IScopedService)
        # Scope automatically disposed
    ```

    Attributes:
        _container: Parent dependency injection container
        _scoped_instances: Dictionary of scoped service instances
        _disposed: Flag indicating if scope has been disposed
        _lock: Thread synchronization lock
    """

    def __init__(self, container: DependencyContainer) -> None:
        """Initialize service scope.

        Args:
            container: The parent dependency injection container that
                      manages the service registrations and resolution.
        """
        self._container = container
        self._scoped_instances: Dict[Type[Any], Any] = {}
        self._disposed = False
        self._lock = threading.RLock()

    def get_service(self, service_type: Type[T]) -> T:
        """Get scoped service instance.

        Retrieves a service instance that is scoped to this specific context.
        If the service is scoped, a new instance will be created for this scope
        if one doesn't already exist. The same instance will be reused for
        subsequent requests within this scope.

        Args:
            service_type: The type of service to retrieve

        Returns:
            Service instance scoped to this context

        Raises:
            RuntimeError: If the scope has been disposed
            ValueError: If service type is not registered

        Example:
            db_context = scope.get_service(IDatabaseContext)
            # Same instance returned for all requests in this scope
        """
        if self._disposed:
            raise RuntimeError("Service scope has been disposed")

        with self._lock:
            # Check if already created in this scope
            if service_type in self._scoped_instances:
                return self._scoped_instances[service_type]

            # Check if service is registered as scoped
            if service_type in self._container._services:
                descriptor = self._container._services[service_type]
                if descriptor.lifetime == ServiceLifetime.SCOPED:
                    instance = descriptor.create_instance(self._container)
                    self._scoped_instances[service_type] = instance
                    return instance

            # Fall back to container resolution for non-scoped services
            return self._container.resolve(service_type)

    def dispose(self) -> None:
        """Dispose of scoped services and clean up resources.

        This method disposes of all service instances that were created
        within this scope. It calls the dispose method on any services
        that support it, ensuring proper cleanup and preventing resource leaks.

        After disposal, the scope should not be used for further service
        resolution as it may result in undefined behavior.

        Note: This method is idempotent - calling it multiple times is safe.
        """
        if self._disposed:
            return

        with self._lock:
            for instance in self._scoped_instances.values():
                if hasattr(instance, 'dispose'):
                    try:
                        instance.dispose()
                    except Exception:
                        pass  # Ignore disposal errors

            self._scoped_instances.clear()
            self._disposed = True


# Global container instance and management
_global_container: Optional[DependencyContainer] = None
_container_lock = threading.RLock()


def get_global_container() -> DependencyContainer:
    """Get the global dependency injection container.

    Returns the singleton global container instance. If no global container
    exists, a new one is created automatically.

    This is the primary way to access the DI container throughout the
    application. The global container is thread-safe and can be used
    concurrently by multiple threads.

    Returns:
        Global dependency injection container instance

    Example:
        container = get_global_container()
        service = container.resolve(IService)
    """
    global _global_container
    with _container_lock:
        if _global_container is None:
            _global_container = DependencyContainer()
        return _global_container


def set_global_container(container: DependencyContainer) -> None:
    """Set the global dependency injection container.

    This function allows replacing the global container instance.
    This is useful for testing scenarios where you want to use
    a custom container configuration, or for advanced scenarios
    where you need multiple container hierarchies.

    Args:
        container: The new global container instance

    Example:
        # Create custom container for testing
        test_container = DependencyContainer()
        test_container.register_singleton(ITestService, MockTestService)
        set_global_container(test_container)
    """
    global _global_container
    with _container_lock:
        _global_container = container


@contextmanager
def service_scope():
    """Context manager for creating a service scope.

    This context manager provides a convenient way to create and manage
    service scopes. It automatically handles scope creation, context
    variable management, and proper disposal.

    The scope is set as the current scope for the duration of the context,
    allowing scoped services to be resolved correctly. When the context
    exits, the scope is automatically disposed.

    Yields:
        ServiceScope: The created service scope

    Example:
        with service_scope() as scope:
            scoped_service = scope.get_service(IScopedService)
            # Service automatically disposed when context exits
    """
    container = get_global_container()
    scope = container.create_scope()
    token = container._current_scope.set(scope)

    try:
        yield scope
    finally:
        container._current_scope.reset(token)
        scope.dispose()


def inject(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to inject dependencies into a function.

    This decorator automatically injects dependencies into function parameters
    based on their type annotations. It inspects the function signature and
    resolves any missing parameters from the global DI container.

    The decorator preserves the original function's behavior while adding
    automatic dependency resolution. It's particularly useful for:

    - Factory functions
    - Initialization functions
    - Functions that need access to services

    Args:
        func: The function to decorate

    Returns:
        Decorated function with automatic dependency injection

    Raises:
        ValueError: If required dependencies cannot be resolved

    Example:
        @inject
        def create_user_handler(logger: ILogger, db: IDatabase) -> UserHandler:
            return UserHandler(logger, db)

        # Dependencies automatically resolved when calling
        handler = create_user_handler()
    """
    container = get_global_container()
    signature = inspect.signature(func)

    def wrapper(*args: Any, **kwargs: Any) -> T:
        # Resolve missing dependencies from container
        resolved_kwargs = {}

        for param_name, param in signature.parameters.items():
            if param_name in kwargs:
                continue  # Already provided
            if param.default != inspect.Parameter.empty:
                continue  # Has default value

            try:
                # Resolve dependency from container
                resolved_kwargs[param_name] = container.resolve(param.annotation)
            except Exception as e:
                if param.default == inspect.Parameter.empty:
                    raise ValueError(
                        f"Cannot resolve dependency '{param_name}' of type '{param.annotation}' "
                        f"for function {func.__name__}: {e}"
                    ) from e

        kwargs.update(resolved_kwargs)
        return func(*args, **kwargs)

    return wrapper
