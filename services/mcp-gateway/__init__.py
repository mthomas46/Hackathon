"""MCP Gateway Service.

Single entry point for all MCP interactions, managing routing, load balancing,
and connection pooling to dynamic MCP instances.

Architecture: Domain-Driven Design (DDD)
Port: 5300 (Internal) / 8151 (External)

Key Features:
- Smart routing to healthy MCP instances
- Load balancing across instances
- Health monitoring and auto-recovery
- Connection pooling and retry logic
- Rate limiting and quotas
- Query caching
"""

__version__ = "1.0.0"
__service_name__ = "mcp-gateway"

