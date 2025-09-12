"""Persistence logic for code analyzer service."""

import os
from typing import Dict, Any


async def persist_analysis_result(result: Dict[str, Any]) -> None:
    """Persist analysis result to external services (Redis and doc-store)."""

    # Publish to Redis if available
    if "aioredis" in globals() or _try_import_redis():
        try:
            import aioredis
            host = os.environ.get("REDIS_HOST")
            if host:
                client = await aioredis.from_url(f"redis://{host}")
                await client.publish("docs.ingested.code", str(result))
                await client.aclose()
        except Exception:
            pass  # Redis publishing is optional

    # Store in doc-store if configured
    ds = os.environ.get("DOC_STORE_URL")
    if ds:
        try:
            from services.shared.clients import ServiceClients  # type: ignore
            svc = ServiceClients(timeout=10)
            await svc.post_json(f"{ds}/documents/enveloped", result)
        except Exception:
            pass  # Doc-store persistence is optional


def _try_import_redis():
    """Try to import aioredis."""
    try:
        import aioredis
        globals()["aioredis"] = aioredis
        return True
    except ImportError:
        return False
