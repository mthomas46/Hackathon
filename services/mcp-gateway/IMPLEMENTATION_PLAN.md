# MCP Gateway Service - Implementation Plan

**Service:** MCP Gateway  
**Port:** 5300 (Internal) / 8151 (External)  
**Status:** 🚧 Phase 1 In Progress  
**Pattern:** Domain-Driven Design (DDD)

---

## Overview

Single entry point for all MCP interactions, managing routing, load balancing, and connection pooling to dynamic MCP instances.

---

## Phase 1: Domain & Application Layers

### Value Objects ✅
- [x] MCPInstanceStatus (available, busy, draining, unhealthy, offline)
- [x] RoutingStrategy (round_robin, least_loaded, sticky_session, etc.)
- [x] HealthStatus (healthy, degraded, unhealthy)

### Entities (Next)
- [ ] MCPInstance - Represents a registered MCP with health and metrics
- [ ] RoutingDecision - Result of routing algorithm
- [ ] LoadMetrics - Current load on an instance
- [ ] CircuitBreakerState - Fault tolerance state

### Repositories (Next)
- [ ] MCPRegistryRepository - Store/retrieve MCP instances
- [ ] RoutingCacheRepository - Cache routing decisions

### Use Cases (Next)
- [ ] RegisterMCPInstanceUseCase
- [ ] RouteRequestUseCase
- [ ] UpdateInstanceHealthUseCase
- [ ] GetAvailableInstancesUseCase

---

## Phase 2: Infrastructure Layer

### Components
- [ ] RedisMCPRegistryRepository
- [ ] RedisRoutingCacheRepository
- [ ] HTTPMCPClient (with circuit breaker)
- [ ] HealthChecker
- [ ] LoadBalancer

---

## Phase 3: Presentation Layer

### API Endpoints
- [ ] POST /api/v1/gateway/route - Route a request to an MCP
- [ ] POST /api/v1/gateway/register - Register an MCP instance
- [ ] DELETE /api/v1/gateway/instances/{id} - Deregister instance
- [ ] GET /api/v1/gateway/instances - List all instances
- [ ] GET /api/v1/gateway/instances/{id}/health - Get instance health
- [ ] POST /api/v1/gateway/instances/{id}/drain - Drain instance
- [ ] GET /api/v1/health - Gateway health check

---

## Phase 4: Testing & Docker

### Tests
- [ ] Unit tests for entities and value objects
- [ ] Integration tests for routing logic
- [ ] API endpoint tests

### Docker
- [ ] Dockerfile
- [ ] Docker Compose integration
- [ ] Environment configuration

---

## Key Features

### Smart Routing
- Health-based routing (skip unhealthy instances)
- Load-based routing (prefer least loaded)
- Session affinity (sticky sessions)

### Fault Tolerance
- Circuit breaker pattern per instance
- Automatic retry with backoff
- Graceful degradation to fallback instances

### Performance
- Connection pooling
- Query result caching
- Metrics collection

---

## Integration Points

- **MCP Infrastructure** - Read instance metadata and context
- **MCP Provisioner** - Notify when instances are created/destroyed
- **MCP Instances** - Forward requests and collect responses
- **Redis** - Registry, caching, rate limiting
- **Log Collector** - Centralized logging

---

## Next Steps

1. Complete domain entities (MCPInstance, RoutingDecision)
2. Implement repository interfaces
3. Build core use cases (Register, Route, Health Check)
4. Create infrastructure layer (Redis repositories)
5. Build FastAPI presentation layer
6. Add comprehensive testing
7. Docker integration

---

*Created: October 6, 2025*  
*Status: Domain layer in progress*
