from typing import Any, Dict, List, Tuple, Callable
from rich.prompt import Prompt
import socket

from services.shared.clients import ServiceClients
from ..helpers import print_kv, print_list
from services.shared.config import get_config_value


def build_actions(console, clients: ServiceClients) -> List[Tuple[str, Callable[[], Any]]]:
    async def peers():
        url = f"{clients.orchestrator_url()}/peers"
        rx = await clients.get_json(url)
        print_kv(console, "Result", rx)

    async def sync_peers():
        url = f"{clients.orchestrator_url()}/registry/sync-peers"
        rx = await clients.post_json(url, {})
        print_kv(console, "Result", rx)

    async def poll_openapi():
        url = f"{clients.orchestrator_url()}/registry/poll-openapi"
        rx = await clients.post_json(url, {})
        print_list(console, "OpenAPI Drift Candidates", rx.get("results", []))

    async def demo_e2e():
        fmt = Prompt.ask("Report format", default="json")
        url = f"{clients.orchestrator_url()}/demo/e2e"
        rx = await clients.post_json(url, {"format": fmt})
        print_kv(console, "Result", rx)

    async def config_effective():
        url = f"{clients.orchestrator_url()}/config/effective"
        rx = await clients.get_json(url)
        print_kv(console, "Config", rx)

    async def redis_connectivity():
        host = str(get_config_value("REDIS_HOST", "redis", section="redis", env_key="REDIS_HOST")).strip()
        port = 6379
        ok = False
        try:
            with socket.create_connection((host, port), timeout=2):
                ok = True
        except Exception:
            ok = False
        print_kv(console, "Redis Probe", {"redis_host": host, "port": port, "connect_ok": ok})

    return [
        ("List peers", peers),
        ("Sync registry to peers", sync_peers),
        ("Poll OpenAPI & detect drift", poll_openapi),
        ("Run demo e2e", demo_e2e),
        ("View config (effective)", config_effective),
        ("Probe Redis connectivity", redis_connectivity),
    ]


