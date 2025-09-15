from typing import Any, Dict, List, Tuple, Callable
from rich.prompt import Prompt

from services.shared.clients import ServiceClients
from ..helpers import print_kv


def build_actions(console, clients: ServiceClients) -> List[Tuple[str, Callable[[], Any]]]:
    async def summarize():
        text = Prompt.ask("Text to summarize")
        provider = Prompt.ask("Provider (ollama|bedrock)", default="ollama")
        model = Prompt.ask("Model (optional)", default="")
        providers = [{"name": provider, **({"model": model} if model else {})}]
        url = f"{clients.summarizer_hub_url()}/summarize/ensemble"
        rx = await clients.post_json(url, {"text": text, "providers": providers, "use_hub_config": True})
        print_kv(console, "Result", rx)

    async def test_providers():
        url = f"{clients.summarizer_hub_url()}/summarize/ensemble"
        try:
            _ = await clients.post_json(url, {"text": "ping", "providers": [{"name": "ollama"}], "use_hub_config": True})
            ok = True
        except Exception:
            ok = False
        print_kv(console, "Providers", {"providers_ok": ok})

    return [
        ("Summarize text (ensemble)", summarize),
        ("Test providers (hub)", test_providers),
    ]


