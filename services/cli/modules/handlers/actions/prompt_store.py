from typing import Any, Dict, List, Tuple, Callable
from rich.prompt import Prompt

from services.shared.integrations.clients.clients import ServiceClients
from ...utils.display_helpers import print_kv, print_list, save_data


def build_actions(console, clients: ServiceClients) -> List[Tuple[str, Callable[[], Any]]]:
    async def list_prompts():
        url = f"{clients.prompt_store_url()}/prompts?limit=50"
        rx = await clients.get_json(url)
        print_list(console, "Prompts", rx.get("prompts", []))

    async def get_prompt():
        category = Prompt.ask("Category")
        name = Prompt.ask("Name")
        params: Dict[str, Any] = {}
        content = Prompt.ask("Variable 'content' (optional)", default="")
        if content:
            params["content"] = content
        url = f"{clients.prompt_store_url()}/prompts/search/{category}/{name}"
        rx = await clients.get_json(url, params=params or None)
        print_kv(console, "Result", rx)

    async def create_prompt():
        category = Prompt.ask("Category")
        name = Prompt.ask("Name")
        content = Prompt.ask("Content")
        url = f"{clients.prompt_store_url()}/prompts"
        rx = await clients.post_json(url, {"category": category, "name": name, "content": content})
        print_kv(console, "Result", rx)

    return [
        ("List prompts", list_prompts),
        ("Get prompt", get_prompt),
        ("Create prompt", create_prompt),
    ]


