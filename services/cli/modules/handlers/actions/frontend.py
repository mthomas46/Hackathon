from typing import Any, Dict, List, Tuple, Callable

from services.shared.integrations.clients.clients import ServiceClients
from ...utils.display_helpers import print_kv


def build_actions(console, clients: ServiceClients) -> List[Tuple[str, Callable[[], Any]]]:
    async def metrics():
        url = f"{clients.frontend_url()}/metrics"
        rx = await clients.get_json(url)
        print_kv(console, "Metrics", rx)

    async def config_effective():
        url = f"{clients.frontend_url()}/config/effective"
        rx = await clients.get_json(url)
        print_kv(console, "Config", rx)

    return [
        ("Show metrics", metrics),
        ("View config (effective)", config_effective),
    ]


