from typing import Dict, Any, Optional, List
import os
import re
from ..integrations.clients import ServiceClients  # type: ignore


def extract_owner_from_metadata(meta: Dict[str, Any] | None) -> Dict[str, Optional[str]]:
    """Extract owner hints from a document metadata dictionary.

    Looks for keys like owner, code_owner, repo_owner, jira_assignee, jira_reporter,
    confluence_last_updated_by.
    """
    meta = meta or {}
    sl = (meta.get("source_link") or {}) if isinstance(meta, dict) else {}
    return {
        "owner": (meta.get("owner") if isinstance(meta, dict) else None),
        "code_owner": (meta.get("code_owner") if isinstance(meta, dict) else None),
        "repo_owner": (sl.get("repo_owner") if isinstance(sl, dict) else None),
        "jira_assignee": (meta.get("jira_assignee") if isinstance(meta, dict) else None),
        "jira_reporter": (meta.get("jira_reporter") if isinstance(meta, dict) else None),
        "confluence_last_updated_by": (meta.get("updated_by") or meta.get("last_updated_by")),
        "confluence_created_by": (meta.get("created_by") if isinstance(meta, dict) else None),
        "confluence_space_owner": (meta.get("space_owner") if isinstance(meta, dict) else None),
    }


def merge_owner_hints(*hint_maps: Dict[str, Optional[str]]) -> List[str]:
    """Merge multiple owner hint maps into a unique ordered list of targets.

    Priority: owner -> code_owner -> repo_owner -> jira_assignee -> jira_reporter -> confluence_last_updated_by
    """
    ordered_keys = [
        "owner",
        "code_owner",
        "repo_owner",
        "jira_assignee",
        "jira_reporter",
        "confluence_last_updated_by",
        "confluence_created_by",
        "confluence_space_owner",
    ]
    seen = set()
    out: List[str] = []
    for k in ordered_keys:
        for hm in hint_maps:
            v = (hm or {}).get(k)
            if v and v not in seen:
                seen.add(v)
                out.append(v)
    return out[:20]


def parse_codeowners(text: str) -> Dict[str, List[str]]:
    """Parse a CODEOWNERS file into a mapping of glob -> owners.

    Lines: "path pattern" then one or more owners (@user or team).
    Comments and blanks ignored. Very small subset parser sufficient for heuristics.
    """
    mapping: Dict[str, List[str]] = {}
    for line in (text or "").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        if len(parts) < 2:
            continue
        pattern, owners = parts[0], [p.lstrip("@") for p in parts[1:]]
        mapping[pattern] = owners
    return mapping


def owners_for_path_from_codeowners(mapping: Dict[str, List[str]], path: str) -> List[str]:
    """Naive glob matching: supports '*' simple wildcard.
    Picks the last matching pattern (CODEOWNERS precedence)."""
    selected: List[str] = []
    for pat, owners in mapping.items():
        # Convert simple '*' to regex
        regex = re.escape(pat).replace(r"\*", ".*") + r"$"
        if re.match(regex, path):
            selected = owners
    return selected


async def try_fetch_codeowners(owner: str, repo: str, branch: str = "main") -> Optional[str]:
    """Try to fetch CODEOWNERS via raw URL if configured.

    Environment overrides:
    - GITHUB_RAW_BASE (default https://raw.githubusercontent.com)
    - GITHUB_CODEOWNERS_PATH candidates: .github/CODEOWNERS, CODEOWNERS
    """
    raw = os.environ.get("GITHUB_RAW_BASE", "https://raw.githubusercontent.com")
    candidates = [f".github/CODEOWNERS", f"CODEOWNERS"]
    import httpx  # fallback path for raw text when ServiceClients returns JSON
    async with httpx.AsyncClient(timeout=10) as client:
        for p in candidates:
            url = f"{raw}/{owner}/{repo}/{branch}/{p}"
            try:
                r = await client.get(url)
                if r.status_code == 200 and r.text:
                    return r.text
            except Exception:
                continue
    return None


async def derive_github_owners(owner: str, repo: str, path: str) -> List[str]:
    """Best-effort CODEOWNERS lookup for a path.
    Returns list of owners without '@'."""
    try:
        text = await try_fetch_codeowners(owner, repo)
        if not text:
            return []
        mapping = parse_codeowners(text)
        return owners_for_path_from_codeowners(mapping, path)
    except Exception:
        return []



def merge_codeowners_with_blame(
    codeowners_mapping: Dict[str, List[str]],
    file_path: str,
    blame_authors: List[str],
) -> List[str]:
    """Merge CODEOWNERS owners for a path with git blame authors.

    Priority: CODEOWNERS pattern owners first (latest match), then blame authors.
    Dedupe while preserving order.
    """
    owners = owners_for_path_from_codeowners(codeowners_mapping, file_path)
    out: List[str] = []
    seen = set()
    for o in owners + (blame_authors or []):
        if o and o not in seen:
            seen.add(o)
            out.append(o)
    return out[:20]


