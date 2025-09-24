from typing import Any, Dict

from fastapi import APIRouter, Request

# Config now handled by standardized config system in main.py
import os
from services.shared.integrations.clients.clients import ServiceClients

router = APIRouter()


def _get_registry(request: Request) -> Dict[str, Dict[str, Any]]:
    app = request.app
    reg = getattr(app.state, "registry", None)
    if isinstance(reg, dict):
        return reg
    return {}


@router.post("/registry/sync-peers")
async def registry_sync_peers(request: Request):
    peers = [
        p.strip()
        for p in (
            os.getenv("ORCHESTRATOR_PEERS", "").split(
                ","
            )
        )
        if p.strip()
    ]
    sent = 0
    try:
        svc_client = ServiceClients(timeout=5)
        registry = _get_registry(request)
        for peer in peers:
            for entry in registry.values():
                try:
                    await svc_client.post_json(f"{peer}/registry/register", entry)
                    sent += 1
                except Exception:
                    continue
    except Exception:
        pass
    return {"sent": sent, "peers": len(peers)}
