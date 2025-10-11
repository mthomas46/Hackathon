"""
REST API for Ecosystem MCP Service.

Provides HTTP-based access for humans and operations.
"""

from .app import create_app

__all__ = ["create_app"]

