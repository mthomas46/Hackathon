from typing import Dict, List
from services.shared.clients import ServiceClients  # type: ignore


def parse_openapi_to_endpoints(spec: Dict) -> List[dict]:
    endpoints: List[dict] = []
    for path, methods in (spec.get("paths") or {}).items():
        for method, meta in (methods or {}).items():
            endpoints.append({
                "path": path,
                "method": method.upper(),
                "summary": (meta or {}).get("summary"),
                "description": (meta or {}).get("description"),
            })
    return endpoints


async def self_register(name: str, base_url: str, orchestrator_url: str) -> None:
    """Best-effort self-registration helper for services on startup."""
    try:
        svc = ServiceClients(timeout=5)
        await svc.post_json(f"{orchestrator_url}/registry/register", {
            "name": name,
            "base_url": base_url,
        })
    except Exception:
        return

