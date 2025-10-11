#!/usr/bin/env python3
"""
Simple server startup script that bypasses preflight checks.
"""

import asyncio
import uvicorn

print("🚀 Starting Ecosystem-MCP Server (simplified)")
print("=" * 80)

# Start the server directly
config = uvicorn.Config(
    "src.api.app:create_app",
    factory=True,
    host="0.0.0.0",
    port=8000,
    log_level="info",
    access_log=True
)
server = uvicorn.Server(config)

try:
    asyncio.run(server.serve())
except KeyboardInterrupt:
    print("\n✅ Shutdown complete")

