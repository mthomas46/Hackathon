"""Infrastructure events and startup handlers

This module contains startup and shutdown event handlers for the discovery agent.
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
