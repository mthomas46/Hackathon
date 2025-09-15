from typing import Any, Dict, List, Tuple, Callable
from rich.prompt import Prompt

from services.shared.clients import ServiceClients
from ..helpers import print_kv


def build_actions(console, clients: ServiceClients) -> List[Tuple[str, Callable[[], Any]]]:
    async def analyze():
        target = Prompt.ask("Target ID (doc:... or api:...)")
        atype = Prompt.ask("Analysis type", default="consistency")
        url = f"{clients.analysis_service_url()}/analyze"
        rx = await clients.post_json(url, {"targets": [target], "analysis_type": atype})
        print_kv(console, "Result", rx)

    async def report():
        kind = Prompt.ask("Report kind", default="summary")
        url = f"{clients.analysis_service_url()}/reports/generate"
        rx = await clients.post_json(url, {"kind": kind})
        print_kv(console, "Result", rx)

    return [
        ("Analyze targets", analyze),
        ("Generate report", report),
    ]


