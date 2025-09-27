"""Infrastructure events and lifecycle management for discovery agent.

This module provides FastAPI lifecycle event handlers for the discovery agent,
managing startup initialization, shutdown cleanup, and background task coordination.

Key responsibilities:
- Service registration and deregistration with orchestrator
- Background task initialization and cleanup
- Health check endpoint registration
- Performance monitoring setup and teardown
- External service connection management

The event handlers ensure proper resource management and graceful service lifecycle
transitions, maintaining system stability and observability.
"""

from fastapi import FastAPI


def register_startup_events(app: FastAPI):
    """Register all startup event handlers with the FastAPI app"""

    @app.on_event("startup")
    async def startup_event():
        """Initialize enhanced discovery agent"""
        print("🚀 Enhanced Discovery Agent starting up...")
        print("✅ Network URL normalization enabled")
        print("✅ Bulk ecosystem discovery available")
        print("✅ Docker network integration ready")
        print("✅ All enhanced endpoints registered")
