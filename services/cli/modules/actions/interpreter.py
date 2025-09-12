from typing import Any, Dict, List, Tuple, Callable
from rich.prompt import Prompt

from services.shared.clients import ServiceClients
from ..helpers import print_kv


def build_actions(console, clients: ServiceClients) -> List[Tuple[str, Callable[[], Any]]]:
    async def interpret():
        query = Prompt.ask("Query")
        url = f"{clients.interpreter_url()}/interpret"
        rx = await clients.post_json(url, {"query": query})
        print_kv(console, "Result", rx)

    async def execute():
        query = Prompt.ask("Query to execute")
        url = f"{clients.interpreter_url()}/execute"
        rx = await clients.post_json(url, {"query": query})
        print_kv(console, "Result", rx)

    return [
        ("Interpret query", interpret),
        ("Execute workflow", execute),
    ]


