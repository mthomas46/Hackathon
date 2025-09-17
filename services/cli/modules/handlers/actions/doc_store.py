from typing import Any, Dict, List, Tuple, Callable
from rich.prompt import Prompt
import json

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

    async def view_relationships():
        doc_id = Prompt.ask("Document ID")
        direction = Prompt.ask("Direction (incoming/outgoing/both)", default="both")
        rel_type = Prompt.ask("Relationship type filter (optional)", default="")
        url = f"{clients.doc_store_url()}/documents/{doc_id}/relationships"
        params = {"direction": direction}
        if rel_type:
            params["relationship_type"] = rel_type
        data = await clients.get_json(url, params=params)
        print_kv(console, f"Relationships for {doc_id}", data)

    async def find_paths():
        start_id = Prompt.ask("Start document ID")
        end_id = Prompt.ask("End document ID")
        max_depth = Prompt.ask("Max depth", default="3")
        url = f"{clients.doc_store_url()}/graph/paths/{start_id}/{end_id}"
        data = await clients.get_json(url, params={"max_depth": max_depth})
        print_kv(console, f"Paths from {start_id} to {end_id}", data)

    async def graph_stats():
        url = f"{clients.doc_store_url()}/graph/statistics"
        data = await clients.get_json(url)
        print_kv(console, "Graph Statistics", data)

    async def view_document_tags():
        doc_id = Prompt.ask("Document ID")
        category = Prompt.ask("Category filter (optional)", default="")
        url = f"{clients.doc_store_url()}/documents/{doc_id}/tags"
        params = {}
        if category:
            params["category"] = category
        data = await clients.get_json(url, params=params)
        print_kv(console, f"Tags for {doc_id}", data)

    async def tag_document_cli():
        doc_id = Prompt.ask("Document ID")
        url = f"{clients.doc_store_url()}/documents/{doc_id}/tags"
        data = await clients.post_json(url, {})
        print_kv(console, f"Tagging result for {doc_id}", data)

    async def search_by_tags():
        tags_input = Prompt.ask("Tags (comma-separated)")
        tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
        categories_input = Prompt.ask("Categories (optional, comma-separated)", default="")
        categories = [cat.strip() for cat in categories_input.split(",") if cat.strip()] if categories_input else None

        payload = {"tags": tags}
        if categories:
            payload["categories"] = categories

        url = f"{clients.doc_store_url()}/search/tags"
        data = await clients.post_json(url, payload)
        print_kv(console, "Tag Search Results", data)

    async def tag_statistics():
        url = f"{clients.doc_store_url()}/tags/statistics"
        data = await clients.get_json(url)
        print_kv(console, "Tag Statistics", data)

    async def bulk_create_documents():
        count = Prompt.ask("Number of documents to create", default="5")
        count = int(count)

        documents = []
        for i in range(count):
            console.print(f"\n[bold cyan]Document {i+1}/{count}[/bold cyan]")
            content = Prompt.ask(f"Content for document {i+1}")
            metadata_input = Prompt.ask(f"Metadata JSON (optional)", default="{}")

            try:
                metadata = json.loads(metadata_input) if metadata_input.strip() else {}
            except:
                metadata = {}

            documents.append({
                "content": content,
                "metadata": metadata
            })

        payload = {"documents": documents}
        url = f"{clients.doc_store_url()}/bulk/documents"
        data = await clients.post_json(url, payload)
        operation_id = data.get("operation_id")
        console.print(f"[green]Bulk operation started: {operation_id}[/green]")
        console.print("Use 'Monitor bulk operation' to check progress.")

    async def monitor_bulk_operation():
        operation_id = Prompt.ask("Bulk operation ID")
        url = f"{clients.doc_store_url()}/bulk/operations/{operation_id}"
        data = await clients.get_json(url)
        print_kv(console, f"Bulk Operation Status: {operation_id}", data)

    async def list_bulk_operations():
        status_filter = Prompt.ask("Status filter (optional)", default="")
        params = {}
        if status_filter:
            params["status"] = status_filter
        url = f"{clients.doc_store_url()}/bulk/operations"
        data = await clients.get_json(url, params=params)
        print_kv(console, "Bulk Operations", data)

    async def register_webhook():
        name = Prompt.ask("Webhook name")
        url_input = Prompt.ask("Webhook URL")
        events_input = Prompt.ask("Events (comma-separated)")
        events = [event.strip() for event in events_input.split(",") if event.strip()]
        secret = Prompt.ask("Secret (optional)", default="")
        secret = secret if secret else None

        payload = {
            "name": name,
            "url": url_input,
            "events": events
        }
        if secret:
            payload["secret"] = secret

        url = f"{clients.doc_store_url()}/webhooks"
        data = await clients.post_json(url, payload)
        print_kv(console, f"Webhook Registration: {name}", data)

    async def list_webhooks():
        url = f"{clients.doc_store_url()}/webhooks"
        data = await clients.get_json(url)
        print_kv(console, "Webhooks", data)

    async def emit_test_event():
        event_type = Prompt.ask("Event type", default="document.created")
        entity_type = Prompt.ask("Entity type", default="document")
        entity_id = Prompt.ask("Entity ID")
        user_id = Prompt.ask("User ID (optional)", default="")
        user_id = user_id if user_id else None

        payload = {
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id
        }
        if user_id:
            payload["user_id"] = user_id

        url = f"{clients.doc_store_url()}/events"
        data = await clients.post_json(url, payload)
        print_kv(console, f"Event Emission: {event_type}", data)

    async def view_event_history():
        event_type = Prompt.ask("Event type filter (optional)", default="")
        entity_type = Prompt.ask("Entity type filter (optional)", default="")
        entity_id = Prompt.ask("Entity ID filter (optional)", default="")
        limit = Prompt.ask("Limit", default="50")

        params = {"limit": int(limit)}
        if event_type:
            params["event_type"] = event_type
        if entity_type:
            params["entity_type"] = entity_type
        if entity_id:
            params["entity_id"] = entity_id

        url = f"{clients.doc_store_url()}/events"
        data = await clients.get_json(url, params=params)
        print_kv(console, "Event History", data)

    async def view_notification_stats():
        days = Prompt.ask("Days back", default="7")
        url = f"{clients.doc_store_url()}/notifications/stats"
        params = {"days_back": int(days)}
        data = await clients.get_json(url, params=params)
        print_kv(console, "Notification Statistics", data)

    async def test_webhook():
        webhook_id = Prompt.ask("Webhook ID")
        url = f"{clients.doc_store_url()}/webhooks/{webhook_id}/test"
        data = await clients.post_json(url, {})
        print_kv(console, f"Webhook Test: {webhook_id}", data)

    async def send_notification():
        channel = Prompt.ask("Channel (webhook/email/slack)", default="webhook")
        target = Prompt.ask("Target (URL/email/channel)")
        title = Prompt.ask("Title")
        message = Prompt.ask("Message")
        metadata_input = Prompt.ask("Metadata JSON (optional)", default="{}")
        labels_input = Prompt.ask("Labels (comma-separated, optional)", default="")

        try:
            metadata = json.loads(metadata_input) if metadata_input.strip() else {}
        except:
            metadata = {}

        labels = [label.strip() for label in labels_input.split(",") if label.strip()] if labels_input else []

        # Send via notification service
        try:
            result = await clients.notify_via_service(channel, target, title, message, metadata, labels)
            print_kv(console, "Notification Sent", result)
        except Exception as e:
            console.print(f"[red]Failed to send notification: {e}[/red]")

    async def resolve_owners():
        owners_input = Prompt.ask("Owners (comma-separated)")
        owners = [owner.strip() for owner in owners_input.split(",") if owner.strip()]

        try:
            result = await clients.resolve_owners_via_service(owners)
            print_kv(console, "Owner Resolution", result)
        except Exception as e:
            console.print(f"[red]Failed to resolve owners: {e}[/red]")

    return [
        ("Search documents", list_documents),
        ("Advanced search with filters", advanced_search),
        ("Get document by ID", get_document),
        ("Create document", put_document),
        ("Bulk create documents", bulk_create_documents),
        ("Monitor bulk operation", monitor_bulk_operation),
        ("List bulk operations", list_bulk_operations),
        ("List quality signals", quality),
        ("View document tags", view_document_tags),
        ("Tag document", tag_document_cli),
        ("Search by tags", search_by_tags),
        ("View tag statistics", tag_statistics),
        ("View document relationships", view_relationships),
        ("Find relationship paths", find_paths),
        ("View graph statistics", graph_stats),
        ("View document versions", view_document_versions),
        ("Compare document versions", compare_versions),
        ("Rollback document to version", rollback_document),
        ("Register webhook", register_webhook),
        ("List webhooks", list_webhooks),
        ("Emit test event", emit_test_event),
        ("View event history", view_event_history),
        ("View notification stats", view_notification_stats),
        ("Test webhook", test_webhook),
        ("Send notification", send_notification),
        ("Resolve owners", resolve_owners),
        ("View analytics (detailed)", view_analytics),
        ("View analytics summary", view_analytics_summary),
        ("View config (effective)", config_effective),
        ("DB probe (write/read)", db_probe),
        ("Download document", download_document),
    ]


