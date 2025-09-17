"""Service Actions module for the CLI service.

Provides an interactive, API-driven menu that lets users enact common actions
across services. Menus are populated by querying the appropriate APIs and
collecting user input for required parameters.
"""

from typing import Dict, Any, List, Optional, Tuple, Callable
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from services.shared.integrations.clients.clients import ServiceClients
from services.shared.core.constants_new import ServiceNames

from ..shared_utils import (
    create_menu_table,
    add_menu_rows,
    print_panel,
)
from ..utils.display_helpers import print_kv as _print_kv, print_list as _print_list, save_data as _save_data


class ServiceActions:
    """Interactive, API-backed actions for each service."""

    def __init__(self, console: Console, clients: ServiceClients):
        self.console = console
        self.clients = clients
        self._cache: Dict[str, Any] = {}

        # Curated action registry per service name → (display, handler)
        self._actions: Dict[str, List[Tuple[str, Callable[[], Any]]]] = {}

    async def run(self) -> None:
        """Top-level menu: choose a service, then an action."""
        while True:
            service = await self._select_service()
            if service is None:
                break
            await self._service_menu(service)

    async def _select_service(self) -> Optional[str]:
        """Build service list from orchestrator registry if available; fallback to known set."""
        services: List[str] = []
        # Try orchestrator registry
        try:
            reg = await self._get_or_cache(
                "orchestrator.registry",
                lambda: self.clients.get_json(f"{self.clients.orchestrator_url()}/registry")
            )
            for entry in reg.get("services", []):
                name = entry.get("name")
                if isinstance(name, str) and name:
                    services.append(name)
        except Exception:
            pass

        # Fallback curated list
        if not services:
            services = [
                ServiceNames.ORCHESTRATOR,
                ServiceNames.DOC_STORE,
                ServiceNames.ANALYSIS_SERVICE,
                ServiceNames.SOURCE_AGENT,
                ServiceNames.SUMMARIZER_HUB,
                ServiceNames.FRONTEND,
            ]

        # Display menu
        self.console.print("\n[bold cyan]Service Actions[/bold cyan]")
        menu = create_menu_table("", ["Option", "Service"])
        options: Dict[str, str] = {"0": "Global Tools"}
        menu.add_row("0", "Global Tools")
        for idx, svc in enumerate(services, start=1):
            key = str(idx)
            options[key] = svc
            menu.add_row(key, svc)
        menu.add_row("b", "Back to main menu")
        self.console.print(menu)

        choice = Prompt.ask("[bold green]Select service[/bold green]")
        if choice.lower() == "b":
            return None
        if choice == "0":
            await self._global_menu()
            return None
        return options.get(choice)

    async def _global_menu(self) -> None:
        """Global tools not tied to a single service."""
        while True:
            menu = create_menu_table("Global Tools", ["Option", "Action"])
            options: Dict[str, Callable[[], Any]] = {}

            async def config_overview():
                items: List[Dict[str, Any]] = []
                svc_getters = [
                    ("orchestrator", self.clients.orchestrator_url),
                    ("doc_store", self.clients.doc_store_url),
                    ("analysis-service", self.clients.analysis_service_url),
                    ("source-agent", self.clients.source_agent_url),
                ]
                # Optional if available
                for name, getter in svc_getters:
                    try:
                        base = getter()
                        rx = await self.clients.get_json(f"{base}/config/effective")
                        items.append({"service": name, **{str(k): str(v) for k, v in (rx or {}).items()}})
                    except Exception:
                        items.append({"service": name, "config": "n/a"})
                _print_list(self.console, "Config Overview", items)

            async def view_cache():
                keys = list(self._cache.keys())
                _print_list(self.console, "Cache Keys", [{"key": k} for k in keys])

            async def clear_cache():
                self._cache.clear()
                _print_kv(self.console, "Cache", {"cache_cleared": True})

            actions: List[Tuple[str, Callable[[], Any]]] = [
                ("View config overview", config_overview),
                ("View cache keys", view_cache),
                ("Clear cache", clear_cache),
            ]
            for idx, (label, handler) in enumerate(actions, start=1):
                key = str(idx)
                options[key] = handler
                menu.add_row(key, label)
            menu.add_row("b", "Back")
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select action[/bold green]")
            if choice.lower() == "b":
                break
            selected = options.get(choice)
            if not selected:
                self.console.print("[red]Invalid option.[/red]")
                continue
            await selected()

    async def _service_menu(self, service_name: str) -> None:
        """Show actions for a selected service."""
        actions = self._build_actions_for(service_name)
        # Always append bulk ops and cache ops for convenience
        actions.extend(self.bulk_actions())
        actions.extend(self.cache_actions())
        if not actions:
            self.console.print(f"[yellow]No actions available for {service_name} yet.[/yellow]")
            return

        while True:
            menu = create_menu_table(f"{service_name} Actions", ["Option", "Action"])
            options: Dict[str, Callable[[], Any]] = {}
            for idx, (label, handler) in enumerate(actions, start=1):
                key = str(idx)
                options[key] = handler
                menu.add_row(key, label)
            menu.add_row("b", "Back")
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select action[/bold green]")
            if choice.lower() == "b":
                break
            selected = options.get(choice)
            if not selected:
                self.console.print("[red]Invalid option.[/red]")
                continue
            try:
                await selected()
            except Exception as e:
                self.console.print(f"[red]Action failed: {e}[/red]")

    # ------------------------
    # Action registry builders
    # ------------------------
    def _build_actions_for(self, service_name: str) -> List[Tuple[str, Callable[[], Any]]]:
        service_name = service_name.lower()
        mapping: Dict[str, Callable[[], List[Tuple[str, Callable[[], Any]]]]] = {
            ServiceNames.DOC_STORE.lower(): lambda: build_doc_store_actions(self.console, self.clients),
            ServiceNames.ANALYSIS_SERVICE.lower(): lambda: build_analysis_actions(self.console, self.clients),
            ServiceNames.SOURCE_AGENT.lower(): lambda: build_source_agent_actions(self.console, self.clients),
            ServiceNames.ORCHESTRATOR.lower(): lambda: build_orchestrator_actions(self.console, self.clients),
            ServiceNames.SUMMARIZER_HUB.lower(): lambda: build_summarizer_hub_actions(self.console, self.clients),
            ServiceNames.PROMPT_STORE.lower(): lambda: build_prompt_store_actions(self.console, self.clients),
            ServiceNames.INTERPRETER.lower(): lambda: build_interpreter_actions(self.console, self.clients),
            ServiceNames.FRONTEND.lower(): lambda: build_frontend_actions(self.console, self.clients),
        }
        builder = mapping.get(service_name)
        return builder() if builder else []

    # -----------
    # Doc Store
    # -----------
    def _doc_store_actions(self) -> List[Tuple[str, Callable[[], Any]]]:
        async def list_documents():
            q = Prompt.ask("Query (fts)", default="")
            url = f"{self.clients.doc_store_url()}/search"
            rx = await self._get_or_cache(
                f"docstore.search:{q}",
                lambda: self.clients.get_json(url, params={"q": q} if q else None)
            )
            _print_list(self.console, "Documents", rx.get("items", []))

        async def get_document():
            doc_id = Prompt.ask("Document ID")
            url = f"{self.clients.doc_store_url()}/documents/{doc_id}"
            rx = await self._get_or_cache(f"docstore.get:{doc_id}", lambda: self.clients.get_json(url))
            _print_kv(self.console, "Result", rx)

        async def put_document():
            content = Prompt.ask("Content")
            metadata_raw = Prompt.ask("Metadata JSON (optional)", default="{}")
            import json
            try:
                metadata = json.loads(metadata_raw) if metadata_raw else {}
            except Exception:
                metadata = {}
            url = f"{self.clients.doc_store_url()}/documents"
            rx = await self.clients.post_json(url, {"content": content, "metadata": metadata})
            _print_kv(self.console, "Result", rx)

        async def quality():
            url = f"{self.clients.doc_store_url()}/documents/quality"
            rx = await self._get_or_cache("docstore.quality", lambda: self.clients.get_json(url))
            _print_list(self.console, "Quality", rx.get("items", []))

        async def config_effective():
            url = f"{self.clients.doc_store_url()}/config/effective"
            rx = await self.clients.get_json(url)
            _print_kv(self.console, "Config", rx)

        async def db_probe():
            import time as _t
            temp_id = f"cli:{int(_t.time())}"
            create_url = f"{self.clients.doc_store_url()}/documents"
            created = await self.clients.post_json(create_url, {"id": temp_id, "content": "cli-db-probe", "metadata": {"source": "cli"}})
            get_url = f"{self.clients.doc_store_url()}/documents/{created.get('id', temp_id)}"
            fetched = await self.clients.get_json(get_url)
            _print_kv(self.console, "DB Probe", {"created": created.get("id"), "fetched": bool(fetched)})

        async def download_document():
            doc_id = Prompt.ask("Document ID")
            fmt = Prompt.ask("Format (json|txt|md)", default="json")
            path = Prompt.ask("Output path", default=f"./{doc_id.replace(':','_')}.{fmt}")
            url = f"{self.clients.doc_store_url()}/documents/{doc_id}"
            data = await self.clients.get_json(url)
            await _save_data(self.console, data, fmt, path, content_key="content")

        return [
            ("Search documents", list_documents),
            ("Get document by ID", get_document),
            ("Create document", put_document),
            ("List quality signals", quality),
            ("View config (effective)", config_effective),
            ("DB probe (write/read)", db_probe),
            ("Download document", download_document),
        ]

    # ----------------
    # Analysis Service
    # ----------------
    def _analysis_actions(self) -> List[Tuple[str, Callable[[], Any]]]:
        async def analyze():
            target = Prompt.ask("Target ID (doc:... or api:...)")
            atype = Prompt.ask("Analysis type", default="consistency")
            url = f"{self.clients.analysis_service_url()}/analyze"
            rx = await self.clients.post_json(url, {"targets": [target], "analysis_type": atype})
            _print_kv(self.console, "Result", rx)

        async def report():
            kind = Prompt.ask("Report kind", default="summary")
            url = f"{self.clients.analysis_service_url()}/reports/generate"
            rx = await self.clients.post_json(url, {"kind": kind})
            _print_kv(self.console, "Result", rx)

        return [
            ("Analyze targets", analyze),
            ("Generate report", report),
        ]

    # -------------
    # Source Agent
    # -------------
    def _source_agent_actions(self) -> List[Tuple[str, Callable[[], Any]]]:
        async def fetch_doc():
            source = Prompt.ask("Source", default="github")
            ident = Prompt.ask("Identifier (e.g., owner:repo or JIRA key)")
            url = f"{self.clients.source_agent_url()}/docs/fetch"
            rx = await self.clients.post_json(url, {"source": source, "identifier": ident})
            _print_kv(self.console, "Result", rx)

        async def normalize():
            source = Prompt.ask("Source", default="github")
            data_raw = Prompt.ask("Source data JSON")
            import json
            try:
                data = json.loads(data_raw)
            except Exception:
                data = {}
            url = f"{self.clients.source_agent_url()}/normalize"
            rx = await self.clients.post_json(url, {"source": source, "data": data})
            _print_kv(self.console, "Result", rx)

        async def analyze_code():
            text = Prompt.ask("Code/Text to analyze")
            url = f"{self.clients.source_agent_url()}/code/analyze"
            rx = await self.clients.post_json(url, {"text": text})
            _print_kv(self.console, "Result", rx)

        async def download_fetched_document():
            source = Prompt.ask("Source", default="github")
            ident = Prompt.ask("Identifier (e.g., owner:repo or JIRA key)")
            fmt = Prompt.ask("Format (json|txt|md)", default="json")
            path = Prompt.ask("Output path", default=f"./{source}_{ident.replace(':','_')}.{fmt}")
            url = f"{self.clients.source_agent_url()}/docs/fetch"
            rx = await self.clients.post_json(url, {"source": source, "identifier": ident})
            data = rx.get("data") or rx
            doc = (data.get("document") if isinstance(data, dict) else None) or data
            await _save_data(self.console, doc, fmt, path, content_key="content")

        async def test_github_credentials():
            import httpx
            token = Prompt.ask("GitHub token (or leave blank)", default="")
            owner = Prompt.ask("Owner (user or org)")
            api = Prompt.ask("API base", default="https://api.github.com")
            headers = {"Accept": "application/vnd.github+json"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            url = f"{api}/orgs/{owner}/repos" if owner else f"{api}/user/repos"
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    r = await client.get(url, headers=headers, params={"per_page": 5})
                    ok = r.status_code < 400
            except Exception:
                ok = False
            _print_kv(self.console, "GitHub Credentials", {"github_ok": ok, "owner": owner or "self"})

        async def browse_github():
            import httpx, base64
            token = Prompt.ask("GitHub token (or leave blank)", default="")
            owner = Prompt.ask("Owner (user or org)")
            api = Prompt.ask("API base", default="https://api.github.com")
            headers = {"Accept": "application/vnd.github+json"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            while True:
                try:
                    async with httpx.AsyncClient(timeout=15) as client:
                        url = f"{api}/orgs/{owner}/repos"
                        r = await client.get(url, headers=headers, params={"per_page": 25})
                        repos = r.json() if r.status_code < 400 else []
                    items = [{"name": it.get("name"), "full_name": it.get("full_name"), "private": it.get("private")} for it in repos]
                    _print_list(self.console, "GitHub Repos", items)
                except Exception as e:
                    _print_kv(self.console, "Error", {"error": str(e)})
                choice = Prompt.ask("Enter full_name to view README, or 'b' to back", default="b")
                if choice.lower() == "b":
                    break
                try:
                    async with httpx.AsyncClient(timeout=15) as client:
                        r = await client.get(f"{api}/repos/{choice}/readme", headers=headers)
                        if r.status_code >= 400:
                            _print_kv(self.console, "Error", {"error": f"readme fetch failed {r.status_code}"})
                        else:
                            content_b64 = r.json().get("content", "")
                            text = base64.b64decode(content_b64).decode("utf-8", errors="ignore")
                            path = Prompt.ask("Save path", default=f"./{choice.replace('/', '_')}_README.md")
                            await _save_data(self.console, {"content": text}, "md", path, content_key="content")
                except Exception as e:
                    _print_kv(self.console, "Error", {"error": str(e)})

        async def test_jira_credentials():
            import httpx
            base = Prompt.ask("Jira base URL", default="https://example.atlassian.net")
            email = Prompt.ask("Email")
            token = Prompt.ask("API token")
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    r = await client.get(f"{base}/rest/api/3/project/search", auth=(email, token), params={"maxResults": 1})
                    ok = r.status_code < 400
            except Exception:
                ok = False
            _print_kv(self.console, "Jira Credentials", {"jira_ok": ok, "base": base})

        async def browse_jira():
            import httpx
            base = Prompt.ask("Jira base URL", default="https://example.atlassian.net")
            email = Prompt.ask("Email")
            token = Prompt.ask("API token")
            while True:
                try:
                    async with httpx.AsyncClient(timeout=15) as client:
                        r = await client.get(f"{base}/rest/api/3/project/search", auth=(email, token), params={"maxResults": 25})
                        projects = r.json().get("values", []) if r.status_code < 400 else []
                    items = [{"key": it.get("key"), "name": it.get("name") } for it in projects]
                    _print_list(self.console, "Jira Projects", items)
                except Exception as e:
                    _print_kv(self.console, "Error", {"error": str(e)})
                pkey = Prompt.ask("Enter project key to list issues, or 'b' to back", default="b")
                if pkey.lower() == "b":
                    break
                try:
                    async with httpx.AsyncClient(timeout=15) as client:
                        r = await client.get(f"{base}/rest/api/3/search", auth=(email, token), params={"jql": f"project={pkey}", "maxResults": 25})
                        issues = r.json().get("issues", []) if r.status_code < 400 else []
                    items = [{"key": it.get("key"), "summary": (it.get("fields", {}).get("summary") if isinstance(it.get("fields"), dict) else "")} for it in issues]
                    _print_list(self.console, f"Jira Issues ({pkey})", items)
                    ikey = Prompt.ask("Enter issue key to save JSON, or 'b' to back", default="b")
                    if ikey.lower() == "b":
                        continue
                    async with httpx.AsyncClient(timeout=15) as client:
                        r = await client.get(f"{base}/rest/api/3/issue/{ikey}", auth=(email, token))
                        data = r.json() if r.status_code < 400 else {"error": r.text}
                    path = Prompt.ask("Save path", default=f"./jira_{ikey}.json")
                    await _save_data(self.console, data, "json", path)
                except Exception as e:
                    _print_kv(self.console, "Error", {"error": str(e)})

        async def test_confluence_credentials():
            import httpx
            base = Prompt.ask("Confluence base URL", default="https://example.atlassian.net/wiki")
            email = Prompt.ask("Email")
            token = Prompt.ask("API token")
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    r = await client.get(f"{base}/rest/api/space", auth=(email, token), params={"limit": 1})
                    ok = r.status_code < 400
            except Exception:
                ok = False
            _print_kv(self.console, "Confluence Credentials", {"confluence_ok": ok, "base": base})

        async def browse_confluence():
            import httpx
            base = Prompt.ask("Confluence base URL", default="https://example.atlassian.net/wiki")
            email = Prompt.ask("Email")
            token = Prompt.ask("API token")
            while True:
                try:
                    async with httpx.AsyncClient(timeout=15) as client:
                        r = await client.get(f"{base}/rest/api/space", auth=(email, token), params={"limit": 25})
                        spaces = r.json().get("results", []) if r.status_code < 400 else []
                    items = [{"key": it.get("key"), "name": it.get("name") } for it in spaces]
                    _print_list(self.console, "Confluence Spaces", items)
                except Exception as e:
                    _print_kv(self.console, "Error", {"error": str(e)})
                skey = Prompt.ask("Enter space key to list pages, or 'b' to back", default="b")
                if skey.lower() == "b":
                    break
                try:
                    async with httpx.AsyncClient(timeout=15) as client:
                        r = await client.get(f"{base}/rest/api/content", auth=(email, token), params={"spaceKey": skey, "limit": 25, "expand": "body.storage"})
                        pages = r.json().get("results", []) if r.status_code < 400 else []
                    items = [{"id": it.get("id"), "title": it.get("title") } for it in pages]
                    _print_list(self.console, f"Confluence Pages ({skey})", items)
                    pid = Prompt.ask("Enter page id to save, or 'b' to back", default="b")
                    if pid.lower() == "b":
                        continue
                    page = next((p for p in pages if str(p.get("id")) == pid), None)
                    body = (((page or {}).get("body") or {}).get("storage") or {}).get("value") if isinstance(page, dict) else ""
                    path = Prompt.ask("Save path", default=f"./confluence_{pid}.md")
                    await _save_data(self.console, {"content": body}, "md", path, content_key="content")
                except Exception as e:
                    _print_kv(self.console, "Error", {"error": str(e)})

        return [
            ("Fetch document", fetch_doc),
            ("Normalize data", normalize),
            ("Analyze code for endpoints", analyze_code),
            ("Download fetched document", download_fetched_document),
            ("Test GitHub credentials", test_github_credentials),
            ("Browse GitHub", browse_github),
            ("Test Jira credentials", test_jira_credentials),
            ("Browse Jira", browse_jira),
            ("Test Confluence credentials", test_confluence_credentials),
            ("Browse Confluence", browse_confluence),
        ]

    # -------------
    # Orchestrator
    # -------------
    def _orchestrator_actions(self) -> List[Tuple[str, Callable[[], Any]]]:
        async def peers():
            url = f"{self.clients.orchestrator_url()}/peers"
            rx = await self._get_or_cache("orch.peers", lambda: self.clients.get_json(url))
            _print_kv(self.console, "Result", rx)

        async def sync_peers():
            url = f"{self.clients.orchestrator_url()}/registry/sync-peers"
            rx = await self.clients.post_json(url, {})
            _print_kv(self.console, "Result", rx)

        async def poll_openapi():
            url = f"{self.clients.orchestrator_url()}/registry/poll-openapi"
            rx = await self.clients.post_json(url, {})
            _print_list(self.console, "OpenAPI Drift Candidates", rx.get("results", []))

        async def demo_e2e():
            fmt = Prompt.ask("Report format", default="json")
            url = f"{self.clients.orchestrator_url()}/demo/e2e"
            rx = await self.clients.post_json(url, {"format": fmt})
            _print_kv(self.console, "Result", rx)

        async def config_effective():
            url = f"{self.clients.orchestrator_url()}/config/effective"
            rx = await self.clients.get_json(url)
            _print_kv(self.console, "Config", rx)

        async def redis_connectivity():
            import socket
            from services.shared.core.config.config import get_config_value as _cfg
            host = str(_cfg("REDIS_HOST", "redis", section="redis", env_key="REDIS_HOST")).strip()
            port = 6379
            ok = False
            try:
                with socket.create_connection((host, port), timeout=2):
                    ok = True
            except Exception:
                ok = False
            _print_kv(self.console, "Redis Probe", {"redis_host": host, "port": port, "connect_ok": ok})

        return [
            ("List peers", peers),
            ("Sync registry to peers", sync_peers),
            ("Poll OpenAPI & detect drift", poll_openapi),
            ("Run demo e2e", demo_e2e),
            ("View config (effective)", config_effective),
            ("Probe Redis connectivity", redis_connectivity),
        ]

    # ----------------
    # Summarizer Hub
    # ----------------
    def _summarizer_hub_actions(self) -> List[Tuple[str, Callable[[], Any]]]:
        async def summarize():
            text = Prompt.ask("Text to summarize")
            provider = Prompt.ask("Provider (ollama|bedrock)", default="ollama")
            model = Prompt.ask("Model (optional)", default="")
            providers = [{"name": provider, **({"model": model} if model else {})}]
            url = f"{self.clients.summarizer_hub_url()}/summarize/ensemble"
            rx = await self.clients.post_json(url, {"text": text, "providers": providers, "use_hub_config": True})
            _print_kv(self.console, "Result", rx)

        async def test_providers():
            url = f"{self.clients.summarizer_hub_url()}/summarize/ensemble"
            try:
                _ = await self.clients.post_json(url, {"text": "ping", "providers": [{"name": "ollama"}], "use_hub_config": True})
                ok = True
            except Exception:
                ok = False
            _print_kv(self.console, "Providers", {"providers_ok": ok})

        return [
            ("Summarize text (ensemble)", summarize),
            ("Test providers (hub)", test_providers),
        ]

    # ---------
    # Frontend
    # ---------
    def _frontend_actions(self) -> List[Tuple[str, Callable[[], Any]]]:
        async def metrics():
            url = f"{self.clients.frontend_url()}/metrics"
            rx = await self._get_or_cache("frontend.metrics", lambda: self.clients.get_json(url))
            _print_kv(self.console, "Result", rx)

        async def config_effective():
            url = f"{self.clients.frontend_url()}/config/effective"
            rx = await self.clients.get_json(url)
            _print_kv(self.console, "Config", rx)

        return [
            ("Show metrics", metrics),
            ("View config (effective)", config_effective),
        ]

    # -----------------
    # Bulk operations
    # -----------------
    def bulk_actions(self) -> List[Tuple[str, Callable[[], Any]]]:
        async def bulk_analyze():
            targets = Prompt.ask("Targets (comma-separated, doc:... or api:...)")
            atype = Prompt.ask("Analysis type", default="consistency")
            arr = [t.strip() for t in targets.split(",") if t.strip()]
            url = f"{self.clients.analysis_service_url()}/analyze"
            rx = await self.clients.post_json(url, {"targets": arr, "analysis_type": atype})
            _print_kv(self.console, "Result", rx)

        async def bulk_search():
            queries = Prompt.ask("Search queries (comma-separated)")
            arr = [q.strip() for q in queries.split(",") if q.strip()]
            all_items: List[Dict[str, Any]] = []
            for q in arr:
                url = f"{self.clients.doc_store_url()}/search"
                rx = await self._get_or_cache(f"docstore.search:{q}", lambda: self.clients.get_json(url, params={"q": q}))
                all_items.extend(rx.get("items", []))
            _print_list(self.console, "Aggregated Search Results", all_items)

        return [
            ("Bulk analyze targets", bulk_analyze),
            ("Bulk search documents", bulk_search),
        ]

    

    # -----------------
    # Cache management
    # -----------------
    def cache_actions(self) -> List[Tuple[str, Callable[[], Any]]]:
        async def view_cache():
            keys = list(self._cache.keys())
            _print_list(self.console, "Cache Keys", [{"key": k} for k in keys])

        async def clear_cache():
            self._cache.clear()
            _print_kv(self.console, "Cache", {"cache_cleared": True})

        return [
            ("View cache keys", view_cache),
            ("Clear cache", clear_cache),
        ]

    # -----------------
    # Display utilities
    # -----------------
    def _print_list(self, title: str, items: List[Dict[str, Any]]) -> None:
        if not items:
            self.console.print("[yellow]No items found.[/yellow]")
            return
        table = Table(title=title)
        # Build columns from union of keys
        cols: List[str] = []
        for it in items:
            for k in it.keys():
                if k not in cols:
                    cols.append(k)
        for c in cols:
            table.add_column(str(c))
        for it in items:
            row = [str(it.get(c, "")) for c in cols]
            table.add_row(*row)
        self.console.print(table)

    def _print_kv(self, title: str, data: Dict[str, Any]) -> None:
        table = Table(title=title)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")
        for k, v in (data or {}).items():
            table.add_row(str(k), str(v))
        self.console.print(table)

    async def _get_or_cache(self, key: str, fn):
        if key in self._cache:
            return self._cache[key]
        value = await fn()
        self._cache[key] = value
        return value

    async def _save_data(self, console: Console, data: Dict[str, Any], fmt: str, path: str, content_key: Optional[str] = None) -> None:
        import json, os
        fmt = (fmt or "json").lower()
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            if fmt == "json":
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif fmt in ("txt", "md"):
                text = ""
                if content_key and isinstance(data, dict) and content_key in data:
                    text = str(data.get(content_key) or "")
                else:
                    text = json.dumps(data, indent=2, ensure_ascii=False)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(str(data))
            _print_kv(console, "Saved", {"saved": True, "path": path, "format": fmt})
        except Exception as e:
            _print_kv(console, "Saved", {"saved": False, "path": path, "error": str(e)})


