"""Application layer for memory agent.

This module contains the application logic for memory management operations.
It implements use cases, commands, and queries following CQRS patterns.

Components:
- Commands: Operations that modify memory state
- Queries: Read operations for memory analytics
- DTOs: Data transfer objects for API communication
- Events: Domain events for memory-related activities
- Handlers: Command and event handlers

The application layer orchestrates domain services and enforces business rules
while maintaining clean separation from infrastructure concerns.
"""
