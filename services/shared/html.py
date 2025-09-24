"""Simple HTML rendering utilities for the frontend."""

from typing import Any, List


def render_list(items: List[str], title: str = "") -> str:
    """Render a list of items as HTML."""
    html = f"<h3>{title}</h3>" if title else ""
    html += "<ul>"
    for item in items:
        html += f"<li>{item}</li>"
    html += "</ul>"
    return html


def render_table(headers: List[str], rows: List[List[Any]]) -> str:
    """Render tabular data as HTML table."""
    html = "<table border='1' style='border-collapse: collapse;'>"

    # Add headers
    if headers:
        html += "<thead><tr>"
        for header in headers:
            html += f"<th style='padding: 8px;'>{header}</th>"
        html += "</tr></thead>"

    # Add rows
    html += "<tbody>"
    for row in rows:
        html += "<tr>"
        for cell in row:
            html += f"<td style='padding: 8px;'>{cell}</td>"
        html += "</tr>"
    html += "</tbody></table>"

    return html
