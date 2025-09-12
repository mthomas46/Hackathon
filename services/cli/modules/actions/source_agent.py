from typing import Any, Dict, List, Tuple, Callable
from rich.prompt import Prompt
import base64
import httpx

from services.shared.clients import ServiceClients
from ..helpers import print_kv, print_list, save_data
from services.shared.credentials import get_secret
import os


def build_actions(console, clients: ServiceClients) -> List[Tuple[str, Callable[[], Any]]]:
    async def fetch_doc():
        source = Prompt.ask("Source", default="github")
        ident = Prompt.ask("Identifier (e.g., owner:repo or JIRA key)")
        url = f"{clients.source_agent_url()}/docs/fetch"
        rx = await clients.post_json(url, {"source": source, "identifier": ident})
        print_kv(console, "Result", rx)

    async def normalize():
        source = Prompt.ask("Source", default="github")
        data_raw = Prompt.ask("Source data JSON")
        import json
        try:
            data = json.loads(data_raw)
        except Exception:
            data = {}
        url = f"{clients.source_agent_url()}/normalize"
        rx = await clients.post_json(url, {"source": source, "data": data})
        print_kv(console, "Result", rx)

    async def analyze_code():
        text = Prompt.ask("Code/Text to analyze")
        url = f"{clients.source_agent_url()}/code/analyze"
        rx = await clients.post_json(url, {"text": text})
        print_kv(console, "Result", rx)

    async def download_fetched_document():
        source = Prompt.ask("Source", default="github")
        ident = Prompt.ask("Identifier (e.g., owner:repo or JIRA key)")
        fmt = Prompt.ask("Format (json|txt|md)", default="json")
        path = Prompt.ask("Output path", default=f"./{source}_{ident.replace(':','_')}.{fmt}")
        url = f"{clients.source_agent_url()}/docs/fetch"
        rx = await clients.post_json(url, {"source": source, "identifier": ident})
        data = rx.get("data") or rx
        doc = (data.get("document") if isinstance(data, dict) else None) or data
        await save_data(console, doc, fmt, path, content_key="content")

    async def test_github_credentials():
        env_token = get_secret("GITHUB_TOKEN")
        token: str = ""
        if env_token:
            use_env = Prompt.ask("Use existing GITHUB_TOKEN from environment? (y/n)", default="y")
            if use_env.lower().startswith("y"):
                token = env_token
        if not token:
            token = Prompt.ask("GitHub token (or leave blank)", default="")
        api_default = os.environ.get("GITHUB_API_BASE", "https://api.github.com")
        api = Prompt.ask("API base", default=api_default)
        owner_default = os.environ.get("GITHUB_OWNER", "")
        owner = Prompt.ask("Owner (user or org)", default=owner_default)
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
        print_kv(console, "GitHub Credentials", {"github_ok": ok, "owner": owner or "self"})

    async def browse_github():
        env_token = get_secret("GITHUB_TOKEN")
        token: str = ""
        if env_token:
            use_env = Prompt.ask("Use existing GITHUB_TOKEN from environment? (y/n)", default="y")
            if use_env.lower().startswith("y"):
                token = env_token
        if not token:
            token = Prompt.ask("GitHub token (or leave blank)", default="")
        api_default = os.environ.get("GITHUB_API_BASE", "https://api.github.com")
        api = Prompt.ask("API base", default=api_default)
        owner_default = os.environ.get("GITHUB_OWNER", "")
        owner = Prompt.ask("Owner (user or org)", default=owner_default)
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
                print_list(console, "GitHub Repos", items)
            except Exception as e:
                print_kv(console, "Error", {"error": str(e)})
            choice = Prompt.ask("Enter full_name to view README, or 'b' to back", default="b")
            if choice.lower() == "b":
                break
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    r = await client.get(f"{api}/repos/{choice}/readme", headers=headers)
                    if r.status_code >= 400:
                        print_kv(console, "Error", {"error": f"readme fetch failed {r.status_code}"})
                    else:
                        content_b64 = r.json().get("content", "")
                        text = base64.b64decode(content_b64).decode("utf-8", errors="ignore")
                        path = Prompt.ask("Save path", default=f"./{choice.replace('/', '_')}_README.md")
                        await save_data(console, {"content": text}, "md", path, content_key="content")
            except Exception as e:
                print_kv(console, "Error", {"error": str(e)})

    async def test_jira_credentials():
        base_default = os.environ.get("JIRA_BASE_URL", "https://example.atlassian.net")
        base = Prompt.ask("Jira base URL", default=base_default)
        email_env = get_secret("JIRA_EMAIL") or os.environ.get("JIRA_EMAIL", "")
        email = Prompt.ask("Email", default=email_env if email_env else "")
        tok_env = get_secret("JIRA_API_TOKEN")
        token: str = ""
        if tok_env:
            use_env = Prompt.ask("Use existing JIRA_API_TOKEN from environment? (y/n)", default="y")
            if use_env.lower().startswith("y"):
                token = tok_env
        if not token:
            token = Prompt.ask("API token")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{base}/rest/api/3/project/search", auth=(email, token), params={"maxResults": 1})
                ok = r.status_code < 400
        except Exception:
            ok = False
        print_kv(console, "Jira Credentials", {"jira_ok": ok, "base": base})

    async def browse_jira():
        base_default = os.environ.get("JIRA_BASE_URL", "https://example.atlassian.net")
        base = Prompt.ask("Jira base URL", default=base_default)
        email_env = get_secret("JIRA_EMAIL") or os.environ.get("JIRA_EMAIL", "")
        email = Prompt.ask("Email", default=email_env if email_env else "")
        tok_env = get_secret("JIRA_API_TOKEN")
        token: str = ""
        if tok_env:
            use_env = Prompt.ask("Use existing JIRA_API_TOKEN from environment? (y/n)", default="y")
            if use_env.lower().startswith("y"):
                token = tok_env
        if not token:
            token = Prompt.ask("API token")
        while True:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    r = await client.get(f"{base}/rest/api/3/project/search", auth=(email, token), params={"maxResults": 25})
                    projects = r.json().get("values", []) if r.status_code < 400 else []
                items = [{"key": it.get("key"), "name": it.get("name") } for it in projects]
                print_list(console, "Jira Projects", items)
            except Exception as e:
                print_kv(console, "Error", {"error": str(e)})
            pkey = Prompt.ask("Enter project key to list issues, or 'b' to back", default="b")
            if pkey.lower() == "b":
                break
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    r = await client.get(f"{base}/rest/api/3/search", auth=(email, token), params={"jql": f"project={pkey}", "maxResults": 25})
                    issues = r.json().get("issues", []) if r.status_code < 400 else []
                items = [{"key": it.get("key"), "summary": (it.get("fields", {}).get("summary") if isinstance(it.get("fields"), dict) else "")} for it in issues]
                print_list(console, f"Jira Issues ({pkey})", items)
                ikey = Prompt.ask("Enter issue key to save JSON, or 'b' to back", default="b")
                if ikey.lower() == "b":
                    continue
                async with httpx.AsyncClient(timeout=15) as client:
                    r = await client.get(f"{base}/rest/api/3/issue/{ikey}", auth=(email, token))
                    data = r.json() if r.status_code < 400 else {"error": r.text}
                path = Prompt.ask("Save path", default=f"./jira_{ikey}.json")
                await save_data(console, data, "json", path)
            except Exception as e:
                print_kv(console, "Error", {"error": str(e)})

    async def test_confluence_credentials():
        base_default = os.environ.get("CONFLUENCE_BASE_URL", "https://example.atlassian.net/wiki")
        base = Prompt.ask("Confluence base URL", default=base_default)
        email_env = get_secret("CONFLUENCE_EMAIL") or os.environ.get("CONFLUENCE_EMAIL", "")
        email = Prompt.ask("Email", default=email_env if email_env else "")
        tok_env = get_secret("CONFLUENCE_API_TOKEN")
        token: str = ""
        if tok_env:
            use_env = Prompt.ask("Use existing CONFLUENCE_API_TOKEN from environment? (y/n)", default="y")
            if use_env.lower().startswith("y"):
                token = tok_env
        if not token:
            token = Prompt.ask("API token")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{base}/rest/api/space", auth=(email, token), params={"limit": 1})
                ok = r.status_code < 400
        except Exception:
            ok = False
        print_kv(console, "Confluence Credentials", {"confluence_ok": ok, "base": base})

    async def browse_confluence():
        base_default = os.environ.get("CONFLUENCE_BASE_URL", "https://example.atlassian.net/wiki")
        base = Prompt.ask("Confluence base URL", default=base_default)
        email_env = get_secret("CONFLUENCE_EMAIL") or os.environ.get("CONFLUENCE_EMAIL", "")
        email = Prompt.ask("Email", default=email_env if email_env else "")
        tok_env = get_secret("CONFLUENCE_API_TOKEN")
        token: str = ""
        if tok_env:
            use_env = Prompt.ask("Use existing CONFLUENCE_API_TOKEN from environment? (y/n)", default="y")
            if use_env.lower().startswith("y"):
                token = tok_env
        if not token:
            token = Prompt.ask("API token")
        while True:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    r = await client.get(f"{base}/rest/api/space", auth=(email, token), params={"limit": 25})
                    spaces = r.json().get("results", []) if r.status_code < 400 else []
                items = [{"key": it.get("key"), "name": it.get("name") } for it in spaces]
                print_list(console, "Confluence Spaces", items)
            except Exception as e:
                print_kv(console, "Error", {"error": str(e)})
            skey = Prompt.ask("Enter space key to list pages, or 'b' to back", default="b")
            if skey.lower() == "b":
                break
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    r = await client.get(f"{base}/rest/api/content", auth=(email, token), params={"spaceKey": skey, "limit": 25, "expand": "body.storage"})
                    pages = r.json().get("results", []) if r.status_code < 400 else []
                items = [{"id": it.get("id"), "title": it.get("title") } for it in pages]
                print_list(console, f"Confluence Pages ({skey})", items)
                pid = Prompt.ask("Enter page id to save, or 'b' to back", default="b")
                if pid.lower() == "b":
                    continue
                page = next((p for p in pages if str(p.get("id")) == pid), None)
                body = (((page or {}).get("body") or {}).get("storage") or {}).get("value") if isinstance(page, dict) else ""
                path = Prompt.ask("Save path", default=f"./confluence_{pid}.md")
                await save_data(console, {"content": body}, "md", path, content_key="content")
            except Exception as e:
                print_kv(console, "Error", {"error": str(e)})

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


