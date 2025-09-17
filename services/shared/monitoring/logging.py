from __future__ import annotations

import os
import asyncio
from typing import Any, Dict, Optional
import httpx
from ..core.config.config import get_config_value


async def post_log(level: str, message: str, service: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Asynchronously send a log item to log-collector. Never raises.

    Honors LOG_COLLECTOR_URL; when set to http://testserver, uses in-process ASGI transport.
    """
    url = str(get_config_value("LOG_COLLECTOR_URL", "", section=None, env_key="LOG_COLLECTOR_URL")).strip()
    if not url:
        return
    payload = {
        "service": service,
        "level": level,
        "message": message,
        "context": context or {},
    }
    client: httpx.AsyncClient
    try:
        if url == "http://testserver":
            try:
                from services.log_collector.main import app as lc_app  # type: ignore
            except Exception:
                return
            transport = httpx.ASGITransport(app=lc_app)
            client = httpx.AsyncClient(transport=transport, base_url=url, timeout=2)
        else:
            client = httpx.AsyncClient(timeout=2)
        try:
            await client.post(f"{url}/logs", json=payload)
        finally:
            await client.aclose()
    except Exception:
        # swallow any logging errors
        return


def fire_and_forget(level: str, message: str, service: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Schedule non-blocking log emission; safe to call from sync/async contexts."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(post_log(level, message, service, context))
    except RuntimeError:
        try:
            asyncio.run(post_log(level, message, service, context))
        except Exception:
            return


