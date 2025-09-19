"""Shared Infrastructure for LLM Documentation Ecosystem.

This package contains shared utilities, middleware, logging, and other
common infrastructure components used across all services in the ecosystem.

Modules:
- core: Core utilities and models
- utilities: General utility functions and helpers
- monitoring: Health monitoring and metrics
- auth: Authentication and authorization
- enterprise: Enterprise-grade features
- reporting: Report generation utilities
- integrations: Third-party service integrations
- caching: Intelligent caching systems
- streaming: Event streaming infrastructure
- testing: Shared testing utilities

Usage:
    from services.shared.core.responses import create_success_response
    from services.shared.utilities.middleware import ServiceMiddleware
    from services.shared.monitoring.health import register_health_endpoints
"""