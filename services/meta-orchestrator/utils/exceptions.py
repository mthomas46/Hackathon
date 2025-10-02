"""Custom exceptions for the Meta-Orchestration Service"""


class OrchestrationError(Exception):
    """Base exception for orchestration errors"""
    pass


class DockerError(OrchestrationError):
    """Docker-related errors"""
    pass


class ServiceNotFoundError(OrchestrationError):
    """Service not found error"""
    pass


class DependencyError(OrchestrationError):
    """Service dependency error"""
    pass


class ConfigurationError(OrchestrationError):
    """Configuration-related error"""
    pass


class SecurityError(OrchestrationError):
    """Security-related error"""
    pass
