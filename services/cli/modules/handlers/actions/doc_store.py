from typing import Any, Dict, List, Tuple, Callable
from rich.prompt import Prompt

from services.shared.clients import ServiceClients
from ...utils.display_helpers import print_kv, print_list, save_data


def build_actions(console, clients: ServiceClients) -> List[Tuple[str, Callable[[], Any]]]:
    async def list_documents():
        q = Prompt.ask("Query (fts)", default="")
        url = f"{clients.doc_store_url()}/search"
        rx = await clients.get_json(url, params={"q": q} if q else None)
        print_list(console, "Documents", rx.get("items", []))

    async def get_document():
        doc_id = Prompt.ask("Document ID")
        url = f"{clients.doc_store_url()}/documents/{doc_id}"
        rx = await clients.get_json(url)
        print_kv(console, "Result", rx)

    async def put_document():
        content = Prompt.ask("Content")
        metadata_raw = Prompt.ask("Metadata JSON (optional)", default="{}")
        import json
        try:
            metadata = json.loads(metadata_raw) if metadata_raw else {}
        except Exception:
            metadata = {}
        url = f"{clients.doc_store_url()}/documents"
        rx = await clients.post_json(url, {"content": content, "metadata": metadata})
        print_kv(console, "Result", rx)

    async def quality():
        url = f"{clients.doc_store_url()}/documents/quality"
        rx = await clients.get_json(url)
        print_list(console, "Quality", rx.get("items", []))

    async def config_effective():
        url = f"{clients.doc_store_url()}/config/effective"
        rx = await clients.get_json(url)
        print_kv(console, "Config", rx)

    async def db_probe():
        import time as _t
        temp_id = f"cli:{int(_t.time())}"
        create_url = f"{clients.doc_store_url()}/documents"
        created = await clients.post_json(create_url, {"id": temp_id, "content": "cli-db-probe", "metadata": {"source": "cli"}})
        get_url = f"{clients.doc_store_url()}/documents/{created.get('id', temp_id)}"
        fetched = await clients.get_json(get_url)
        print_kv(console, "DB Probe", {"created": created.get("id"), "fetched": bool(fetched)})

    async def download_document():
        doc_id = Prompt.ask("Document ID")
        fmt = Prompt.ask("Format (json|txt|md)", default="json")
        path = Prompt.ask("Output path", default=f"./{doc_id.replace(':','_')}.{fmt}")
        url = f"{clients.doc_store_url()}/documents/{doc_id}"
        data = await clients.get_json(url)
        await save_data(console, data, fmt, path, content_key="content")

    return [
        ("Search documents", list_documents),
        ("Get document by ID", get_document),
        ("Create document", put_document),
        ("List quality signals", quality),
        ("View config (effective)", config_effective),
        ("DB probe (write/read)", db_probe),
        ("Download document", download_document),
    ]


