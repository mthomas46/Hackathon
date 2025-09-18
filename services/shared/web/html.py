from __future__ import annotations
from typing import Any, Iterable, List, Sequence


def render_table(headers: Sequence[str], rows: Iterable[Sequence[Any]], border: int = 1) -> str:
    head_html = "".join(f"<th>{h}</th>" for h in headers)
    body_html_parts: List[str] = []
    for row in rows:
        body_html_parts.append("<tr>" + "".join(f"<td>{(cell if cell is not None else '')}</td>" for cell in row) + "</tr>")
    return f"<table border={border}><tr>{head_html}</tr>{''.join(body_html_parts)}</table>"


def render_list(items: Iterable[str], title: str | None = None) -> str:
    import html
    # Escape the title to prevent XSS attacks
    safe_title = html.escape(title) if title else None
    prefix = f"<h2>{safe_title}</h2>" if safe_title else ""
    return prefix + "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


