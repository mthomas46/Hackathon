"""
Main MCP server entry point.

Provides both MCP protocol (stdio) and REST API (HTTP) interfaces.
"""

import asyncio
import logging
import sys

import uvicorn

from .utils.preflight import run_preflight_checks

logger = logging.getLogger(__name__)


async def main():
    """Main server entry point."""
    logger.info("=" * 80)
    logger.info("ECOSYSTEM MCP SERVER")
    logger.info("=" * 80)
    
    # Run preflight checks
    logger.info("\n🔍 Running preflight checks...")
    await run_preflight_checks(fail_fast=True)
    
    # Start REST API server
    logger.info("\n🚀 Starting REST API server...")
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
        await server.serve()
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down...")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Run server
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Shutdown complete")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}", exc_info=True)
        sys.exit(1)

