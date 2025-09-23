# ADR 0001: Standardized Envelopes for Responses

## Status
Accepted

## Context
Services returned heterogeneous response shapes. We want consistent clients, errors, and observability.

## Decision
Adopt success and error envelopes across services.

## Consequences
- Easier client consumption and testing
- Centralized error code taxonomy
- Slight overhead for wrapping responses
