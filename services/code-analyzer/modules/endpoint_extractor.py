"""Endpoint extraction logic for code analyzer service."""

import re
from typing import List


def extract_endpoints_from_text(text: str) -> List[str]:
    """Extract API endpoints from code text.

    Supports FastAPI, Flask, and Express.js patterns.
    """
    if not text:
        return []

    endpoints: List[str] = []
    seen = set()

    # Look for decorators and common route patterns (FastAPI/Flask/Express)
    for line in text.splitlines():
        s = line.strip()

        # FastAPI: @app.get("/path")
        if s.startswith("@app.") and "(" in s:
            m = re.search(r"\(\s*['\"]([^'\"]+)['\"]", s)
            if m:
                ep = m.group(1)
                if ep not in seen:
                    seen.add(ep)
                    endpoints.append(ep)

        # Flask: @app.route('/path') optionally with methods
        elif s.startswith("@app.route") and "(" in s:
            m = re.search(r"\(\s*['\"]([^'\"]+)['\"]", s)
            if m:
                ep = m.group(1)
                if ep not in seen:
                    seen.add(ep)
                    endpoints.append(ep)

        # Express: app.get('/path', ...) or router.post("/path", ...)
        elif ("app." in s or "router." in s) and "(" in s:
            m = re.search(r"\b(?:app|router)\.(get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]", s, flags=re.IGNORECASE)
            if m:
                ep = m.group(2)
                if ep not in seen:
                    seen.add(ep)
                    endpoints.append(ep)

        # Fallback: Look for URL patterns
        else:
            for m in re.findall(r"/(?:[a-zA-Z0-9_\-]+(?:/[a-zA-Z0-9_\-]+)*)", s):
                if m not in seen:
                    seen.add(m)
                    endpoints.append(m)

    return endpoints[:200]  # Limit results


def extract_endpoints_from_patch(patch: str) -> List[str]:
    """Extract endpoints from a git patch by analyzing added lines only."""
    added_lines = []

    for line in patch.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:])  # Remove the + prefix

    text = "\n".join(added_lines)
    return extract_endpoints_from_text(text)
