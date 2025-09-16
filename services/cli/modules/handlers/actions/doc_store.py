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

    async def view_analytics():
        days = Prompt.ask("Analysis period (days)", default="30")
        url = f"{clients.doc_store_url()}/analytics"
        data = await clients.get_json(url, params={"days_back": days})
        print_kv(console, "Analytics", data)

    async def view_analytics_summary():
        url = f"{clients.doc_store_url()}/analytics/summary"
        data = await clients.get_json(url)
        print_kv(console, "Analytics Summary", data)

    async def advanced_search():
        # Build search query interactively
        q = Prompt.ask("Search query (optional)", default="")
        content_type = Prompt.ask("Content type filter (optional)", default="")
        source_type = Prompt.ask("Source type filter (optional)", default="")
        language = Prompt.ask("Language filter (optional)", default="")
        has_analysis_input = Prompt.ask("Analysis filter (analyzed/unanalyzed/both)", default="both")

        # Convert analysis filter
        has_analysis = None
        if has_analysis_input == "analyzed":
            has_analysis = True
        elif has_analysis_input == "unanalyzed":
            has_analysis = False

        # Build request payload
        payload = {}
        if q:
            payload["q"] = q
        if content_type:
            payload["content_type"] = content_type
        if source_type:
            payload["source_type"] = source_type
        if language:
            payload["language"] = language
        if has_analysis is not None:
            payload["has_analysis"] = has_analysis

        if not payload:
            console.print("[yellow]No search criteria specified, showing recent documents...[/yellow]")
            payload["limit"] = 10

        url = f"{clients.doc_store_url()}/search/advanced"
        data = await clients.post_json(url, payload)
        print_kv(console, "Advanced Search Results", data)

    async def view_document_versions():
        doc_id = Prompt.ask("Document ID")
        limit = Prompt.ask("Limit (default 10)", default="10")
        url = f"{clients.doc_store_url()}/documents/{doc_id}/versions"
        data = await clients.get_json(url, params={"limit": limit})
        print_kv(console, f"Versions for {doc_id}", data)

    async def rollback_document():
        doc_id = Prompt.ask("Document ID")
        version = Prompt.ask("Version number to rollback to")
        changed_by = Prompt.ask("Changed by (optional)", default="cli_user")

        url = f"{clients.doc_store_url()}/documents/{doc_id}/rollback"
        data = await clients.post_json(url, {"version_number": int(version), "changed_by": changed_by})
        print_kv(console, f"Rollback Result for {doc_id}", data)

    async def compare_versions():
        doc_id = Prompt.ask("Document ID")
        version_a = Prompt.ask("First version number")
        version_b = Prompt.ask("Second version number")

        url = f"{clients.doc_store_url()}/documents/{doc_id}/versions/{version_a}/compare/{version_b}"
        data = await clients.get_json(url)
        print_kv(console, f"Comparison {version_a} vs {version_b}", data)

    return [
        ("Search documents", list_documents),
        ("Advanced search with filters", advanced_search),
        ("Get document by ID", get_document),
        ("Create document", put_document),
        ("List quality signals", quality),
        ("View document versions", view_document_versions),
        ("Compare document versions", compare_versions),
        ("Rollback document to version", rollback_document),
        ("View analytics (detailed)", view_analytics),
        ("View analytics summary", view_analytics_summary),
        ("View config (effective)", config_effective),
        ("DB probe (write/read)", db_probe),
        ("Download document", download_document),
    ]


