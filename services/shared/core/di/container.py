"""Dependency Injection Container - Enterprise-grade DI framework."""

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
    """Service lifetime scopes."""
    SINGLETON = "singleton"      # Single instance for entire application
    TRANSIENT = "transient"      # New instance each time requested
    SCOPED = "scoped"            # Single instance per scope/context


class ServiceDescriptor(Generic[T]):
    """Service descriptor for DI container registration."""

    def __init__(self,
                 service_type: Type[T],
                 implementation_type: Optional[Type[T]] = None,
                 factory: Optional[Callable[..., T]] = None,
                 lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
                 instance: Optional[T] = None) -> None:
        self.service_type = service_type
        self.implementation_type = implementation_type or service_type
        self.factory = factory
        self.lifetime = lifetime
        self.instance: Optional[T] = instance
        self._lock = threading.RLock()

    def create_instance(self, container: 'DependencyContainer', *args: Any, **kwargs: Any) -> T:
        """Create a new instance of the service."""
        with self._lock:
            if self.instance is not None and self.lifetime == ServiceLifetime.SINGLETON:
                return self.instance

            if self.factory:
                instance = self.factory(container, *args, **kwargs)
            else:
                # Auto-inject dependencies from constructor
                instance = self._create_with_injection(container, *args, **kwargs)

            if self.lifetime == ServiceLifetime.SINGLETON:
                self.instance = instance

            return instance

    def _create_with_injection(self, container: 'DependencyContainer', *args: Any, **kwargs: Any) -> T:
        """Create instance with automatic dependency injection."""
        try:
            signature = inspect.signature(self.implementation_type.__init__)
            parameters = {}

            for param_name, param in signature.parameters.items():
                if param_name == 'self':
                    continue
                if param_name in kwargs:
                    parameters[param_name] = kwargs[param_name]
                elif param.default != inspect.Parameter.empty:
                    parameters[param_name] = param.default
                else:
                    # Try to resolve from container
                    try:
                        parameters[param_name] = container.resolve(param.annotation)
                    except Exception:
                        if param.default == inspect.Parameter.empty:
                            raise ValueError(f"Cannot resolve dependency '{param_name}' of type '{param.annotation}' for {self.implementation_type}")

            return self.implementation_type(*args, **parameters)
        except Exception as e:
            raise RuntimeError(f"Failed to create instance of {self.implementation_type}: {e}")


class IServiceProvider(Protocol):
    """Service provider protocol."""

    def get_service(self, service_type: Type[T]) -> T:
        """Get service instance."""
        ...

    def get_services(self, service_type: Type[T]) -> List[T]:
        """Get all service instances of type."""
        ...


class IServiceScope(Protocol):
    """Service scope protocol."""

    def get_service(self, service_type: Type[T]) -> T:
        """Get scoped service instance."""
        ...

    def dispose(self) -> None:
        """Dispose of scoped services."""
        ...


class DependencyContainer(IServiceProvider):
    """Enterprise-grade dependency injection container."""

    def __init__(self, parent: Optional['DependencyContainer'] = None) -> None:
        self._parent = parent
        self._services: Dict[Type[Any], ServiceDescriptor[Any]] = {}
        self._scoped_services: WeakValueDictionary[Type[Any], Any] = WeakValueDictionary()
        self._current_scope: ContextVar[Optional['ServiceScope']] = ContextVar('current_scope', default=None)
        self._lock = threading.RLock()

    def register_singleton(self, service_type: Type[T], implementation_type: Optional[Type[T]] = None, instance: Optional[T] = None) -> 'DependencyContainer':
        """Register a singleton service."""
        return self._register(service_type, implementation_type, ServiceLifetime.SINGLETON, instance=instance)

    def register_transient(self, service_type: Type[T], implementation_type: Optional[Type[T]] = None) -> 'DependencyContainer':
        """Register a transient service."""
        return self._register(service_type, implementation_type, ServiceLifetime.TRANSIENT)

    def register_scoped(self, service_type: Type[T], implementation_type: Optional[Type[T]] = None) -> 'DependencyContainer':
        """Register a scoped service."""
        return self._register(service_type, implementation_type, ServiceLifetime.SCOPED)

    def register_factory(self, service_type: Type[T], factory: Callable[..., T], lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> 'DependencyContainer':
        """Register a service with a factory function."""
        descriptor = ServiceDescriptor(service_type, factory=factory, lifetime=lifetime)
        self._services[service_type] = descriptor
        return self

    def register_instance(self, service_type: Type[T], instance: T) -> 'DependencyContainer':
        """Register a pre-created instance as singleton."""
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
        """Resolve a service instance."""
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
        """Get service instance (IServiceProvider implementation)."""
        return self.resolve(service_type)

    def get_services(self, service_type: Type[T]) -> List[T]:
        """Get all service instances of type."""
        services = []

        # Check if service is registered
        if service_type in self._services:
            services.append(self.resolve(service_type))

        # Check parent
        if self._parent:
            parent_services = self._parent.get_services(service_type)
            services.extend(parent_services)

        return services

    def create_scope(self) -> 'ServiceScope':
        """Create a new service scope."""
        return ServiceScope(self)

    def dispose(self) -> None:
        """Dispose of container resources."""
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
    """Service scope for scoped services."""

    def __init__(self, container: DependencyContainer) -> None:
        self._container = container
        self._scoped_instances: Dict[Type[Any], Any] = {}
        self._disposed = False
        self._lock = threading.RLock()

    def get_service(self, service_type: Type[T]) -> T:
        """Get scoped service instance."""
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

            # Fall back to container resolution
            return self._container.resolve(service_type)

    def dispose(self) -> None:
        """Dispose of scoped services."""
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


# Global container instance
_global_container: Optional[DependencyContainer] = None
_container_lock = threading.RLock()


def get_global_container() -> DependencyContainer:
    """Get the global dependency injection container."""
    global _global_container
    with _container_lock:
        if _global_container is None:
            _global_container = DependencyContainer()
        return _global_container


def set_global_container(container: DependencyContainer) -> None:
    """Set the global dependency injection container."""
    global _global_container
    with _container_lock:
        _global_container = container


@contextmanager
def service_scope():
    """Context manager for creating a service scope."""
    container = get_global_container()
    scope = container.create_scope()
    token = container._current_scope.set(scope)

    try:
        yield scope
    finally:
        container._current_scope.reset(token)
        scope.dispose()


def inject(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to inject dependencies into a function."""
    container = get_global_container()
    signature = inspect.signature(func)

    def wrapper(*args: Any, **kwargs: Any) -> T:
        # Resolve missing dependencies
        resolved_kwargs = {}

        for param_name, param in signature.parameters.items():
            if param_name in kwargs:
                continue
            if param.default != inspect.Parameter.empty:
                continue

            try:
                resolved_kwargs[param_name] = container.resolve(param.annotation)
            except Exception:
                if param.default == inspect.Parameter.empty:
                    raise ValueError(f"Cannot resolve dependency '{param_name}' of type '{param.annotation}' for function {func.__name__}")

        kwargs.update(resolved_kwargs)
        return func(*args, **kwargs)

    return wrapper
