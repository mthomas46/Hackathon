from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

# Config now handled by standardized config system in main.py
import os
from services.shared.integrations.clients.clients import ServiceClients
from services.shared.presentation.api.responses import (
    create_error_response,
    create_success_response,
)

# Domain exceptions
from ..domain.exceptions import (
    PeerSynchronizationError,
    ExternalServiceCommunicationError,
)

router = APIRouter()


def _get_registry(request: Request) -> Dict[str, Dict[str, Any]]:
    app = request.app
    reg = getattr(app.state, "registry", None)
    if isinstance(reg, dict):
        return reg
    return {}


@router.post("/registry/sync-peers")
async def registry_sync_peers(request: Request):
    """Synchronize service registry with peer orchestrators."""
    try:
        peers = [
            p.strip()
            for p in os.getenv("ORCHESTRATOR_PEERS", "").split(",")
            if p.strip()
        ]

        if not peers:
            return create_success_response(
                {"sent": 0, "peers": 0, "message": "No peers configured"}
            )

        svc_client = ServiceClients(timeout=5)
        registry = _get_registry(request)

        if not registry:
            return create_success_response(
                {"sent": 0, "peers": len(peers), "message": "Registry is empty"}
            )

        sent = 0
        failed_peers = []

        for peer in peers:
            peer_sent = 0
            for entry in registry.values():
                try:
                    await svc_client.post_json(f"{peer}/registry/register", entry)
                    peer_sent += 1
                except Exception as e:
                    # Log the specific error but continue with other entries
                    print(f"Failed to sync entry to peer {peer}: {e}")
                    continue
            sent += peer_sent

        return create_success_response({
            "sent": sent,
            "peers": len(peers),
            "message": f"Successfully synchronized {sent} service entries across {len(peers)} peers"
        })

    except ExternalServiceCommunicationError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to communicate with peer orchestrators: {e}"
        )
    except Exception as e:
        # Catch any unexpected errors and provide meaningful response
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during peer synchronization: {e}"
        )
