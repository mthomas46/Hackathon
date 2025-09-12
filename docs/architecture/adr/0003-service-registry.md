# ADR 0003: Orchestrator Service Registry

## Status
Accepted

## Context
Services need to discover each other with minimal configuration and support peer replication.

## Decision
Orchestrator provides a registry with self-registration endpoints and peer replication.

## Consequences
- Simplifies service discovery in dev/test
- Supports eventual consistency via peer sync
- Requires health checks to prune stale entries
