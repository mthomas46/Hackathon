from typing import Dict, List

from .shared_utils import safe_service_clients_call, TIMEOUT_HEALTH_CHECK


def parse_openapi_to_endpoints(spec: Dict) -> List[dict]:
    endpoints: List[dict] = []
    for path, methods in (spec.get("paths") or {}).items():
        for method, meta in (methods or {}).items():
            endpoints.append(
                {
                    "path": path,
                    "method": method.upper(),
                    "summary": (meta or {}).get("summary"),
                    "description": (meta or {}).get("description"),
                }
            )
    return endpoints


async def self_register(name: str, base_url: str, orchestrator_url: str) -> None:
    """Best-effort self-registration helper for services on startup."""
    try:
        svc = safe_service_clients_call(timeout=TIMEOUT_HEALTH_CHECK)
        await svc.post_json(
            f"{orchestrator_url}/registry/register",
            {
                "name": name,
                "base_url": base_url,
            },
        )
    except Exception:
        return
