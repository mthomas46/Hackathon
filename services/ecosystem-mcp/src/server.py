"""
Main MCP server entry point.

Provides both MCP protocol (stdio) and REST API (HTTP) interfaces.
"""

import asyncio
import logging
import sys

# MCP will be implemented in a separate module
# For now, this is the entry point placeholder

logger = logging.getLogger(__name__)


async def main():
    """Main server entry point."""
    logger.info("Ecosystem MCP Server starting...")
    
    # TODO: Initialize services
    # TODO: Start MCP server (stdio)
    # TODO: Start REST API server (HTTP)
    
    logger.info("Server ready")
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run server
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete")
        sys.exit(0)

