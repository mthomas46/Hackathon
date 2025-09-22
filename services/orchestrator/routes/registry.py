from fastapi import APIRouter, Request
from typing import Dict, Any, List, Optional
import time

from services.shared.core.responses.responses import create_error_response, create_success_response
from services.shared.core.constants_new import ErrorCodes, ServiceNames
from services.shared.core.config.config import get_config_value
from services.shared.integrations.clients.clients import ServiceClients
from services.shared.utilities.logging_client import get_log_collector_client

router = APIRouter()

# Global logger client instance
logger_client = None

async def get_logger_client():
    """Get or initialize the logger client."""
    global logger_client
    if logger_client is None:
        try:
            logger_client = await get_log_collector_client(ServiceNames.ORCHESTRATOR)
        except Exception:
            pass  # Fallback to no logging if client unavailable
    return logger_client


def _get_registry(request: Request) -> Dict[str, Dict[str, Any]]:
    app = request.app
    reg = getattr(app.state, "registry", None)
    if isinstance(reg, dict):
        return reg
    return {}


@router.post("/registry/sync-peers")
async def registry_sync_peers(request: Request):
    """Sync service registry with peer orchestrators."""
    start_time = time.time()
    request_id = f"sync_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        peers = [p.strip() for p in (get_config_value("ORCHESTRATOR_PEERS", "", section="orchestrator").split(",")) if p.strip()]
        registry = _get_registry(request)

        # Log sync operation start
        if logger:
            await logger.log_business_event("registry_sync_started", {
                "request_id": request_id,
                "peers_count": len(peers),
                "services_to_sync": len(registry),
                "peers": peers
            })

            await logger.log_info("Starting registry synchronization with peers", {
                "request_id": request_id,
                "peer_count": len(peers),
                "services_count": len(registry)
            })

        sent = 0
        failed = 0

        svc_client = ServiceClients(timeout=5)

        for peer in peers:
            peer_sent = 0
            peer_failed = 0

            for service_name, entry in registry.items():
                try:
                    await svc_client.post_json(f"{peer}/registry/register", entry)
                    sent += 1
                    peer_sent += 1
                except Exception as e:
                    failed += 1
                    peer_failed += 1

                    # Log individual sync failures
                    if logger:
                        await logger.log_warning("Registry sync failed for service", {
                            "request_id": request_id,
                            "peer": peer,
                            "service": service_name,
                            "error": str(e)
                        })

            # Log per-peer results
            if logger and peer_sent > 0:
                await logger.log_info("Registry sync completed for peer", {
                    "request_id": request_id,
                    "peer": peer,
                    "services_synced": peer_sent,
                    "services_failed": peer_failed
                })

        response_time = time.time() - start_time

        # Log overall sync completion
        if logger:
            await logger.log_business_event("registry_sync_completed", {
                "request_id": request_id,
                "peers_count": len(peers),
                "services_synced": sent,
                "services_failed": failed,
                "response_time_seconds": response_time,
                "success_rate": sent / (sent + failed) if (sent + failed) > 0 else 0
            })

            await logger.log_performance_metric(
                "registry_sync",
                response_time,
                {
                    "request_id": request_id,
                    "peers_processed": len(peers),
                    "services_synced": sent,
                    "sync_success": sent > 0
                }
            )

        return {
            "sent": sent,
            "failed": failed,
            "peers": len(peers),
            "success_rate": sent / (sent + failed) if (sent + failed) > 0 else 0
        }

    except Exception as e:
        error_time = time.time() - start_time

        # Log sync operation failure
        if logger:
            await logger.log_error(
                f"Registry synchronization failed: {str(e)}",
                {
                    "request_id": request_id,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time
                },
                error=e
            )

            await logger.log_business_event("registry_sync_failed", {
                "request_id": request_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "response_time_seconds": error_time
            })

        return {"sent": 0, "failed": 0, "peers": 0, "error": str(e)}
