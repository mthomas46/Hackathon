from __future__ import annotations
from typing import Any, Dict, List
from services.shared.html import render_table, render_list  # type: ignore
from services.shared.core.config.config import get_config_value
from services.shared.core.constants_new import EnvVars


def render_index() -> str:
    return (
        """
    <html>
      <head><title>Doc Consistency Portal</title></head>
      <body>
        <h1>Documentation Consistency Portal</h1>
        <ul>
          <li><a href="/findings">View Findings (Consistency Engine)</a></li>
          <li><a href="/report">Generate Report</a></li>
          <li><a href="/findings/by-severity">Findings by Severity</a></li>
          <li><a href="/findings/by-type">Findings by Type</a></li>
          <li><a href="/search">Search Confluence/Docs</a></li>
          <li><a href="/docs/quality">Docs Quality Signals</a></li>
          <li><a href="/confluence/consolidation">Confluence Consolidation Report</a></li>
          <li><a href="/reports/jira/staleness">Jira Staleness</a></li>
          <li><a href="/duplicates/clusters">Duplicate Clusters</a></li>
          <li><a href="/topics">Topic Collections</a></li>
          <li><a href="/owner-coverage">Owner Coverage</a></li>
        </ul>
      </body>
    </html>
    """
    ).strip()


def render_owner_coverage_table(coverage: Dict[str, Dict[str, Any]]) -> str:
    headers = ["Team", "% Missing Owner", "% Low Views", "Total"]
    rows = [
        [team, stats.get("missing_owner_pct", 0), stats.get("low_views_pct", 0), stats.get("total", 0)]
        for team, stats in coverage.items()
    ]
    return "<h2>Owner Coverage</h2>" + render_table(headers, rows)


def render_topics_html(topics: Dict[str, List[tuple[str, str]]]) -> str:
    html = "<h2>Topic Collections</h2>"
    for t, arr in topics.items():
        html += f"<h3>{t.title()}</h3><ul>" + "".join([f"<li>{i} <span>({f})</span></li>" for i, f in arr]) + "</ul>"
    return html


def render_consolidation_list(items: List[Dict[str, Any]]) -> str:
    formatted = [
        f"{i.get('id')} - confidence {i.get('confidence'):.2f} - flags: {','.join(i.get('flags', []))}"
        for i in items
    ]
    return render_list(formatted, title="Confluence Consolidation Candidates")


def render_search_results(query: str, items: List[Dict[str, Any]]) -> str:
    import html
    # Sanitize the query parameter to prevent XSS attacks
    safe_query = html.escape(query)
    return render_list([str(i.get("id")) for i in items], title=f"Search results for '{safe_query}'")


def render_docs_quality(items: List[Dict[str, Any]]) -> str:
    formatted = []
    for i in items:
        flags = ",".join(i.get("flags", []))
        badges = ",".join(i.get("badges", [])) if isinstance(i.get("badges"), list) else ""
        if badges:
            formatted.append(f"{i.get('id')} - badges:[{badges}] flags:[{flags}]")
        else:
            formatted.append(f"{i.get('id')} - flags:[{flags}]")
    return render_list(formatted, title="Docs Quality Signals")


def render_findings(items: List[Dict[str, Any]]) -> str:
    return render_list([str(f) for f in items], title="Findings")


def render_counts(title: str, items: Dict[str, int]) -> str:
    formatted = [f"{k}: {v}" for k, v in items.items()]
    return render_list(formatted, title=title)


def render_report_page(data: Dict[str, Any]) -> str:
    return (
        f"""
      <h2>Report</h2>
      <p>Total findings: {data.get('total')}</p>
      <h3>By Severity</h3>
      <pre>{data.get('by_severity')}</pre>
      <h3>By Type</h3>
      <pre>{data.get('by_type')}</pre>
      <h3>Top Endpoints with Drift</h3>
      <ul>{''.join([f"<li>{{ep}} ({{cnt}})</li>" for ep, cnt in (data.get('top_endpoints_with_drift') or [])])}</ul>
      <h3>Suggestions</h3>
      <ul>{''.join([f"<li>{{it['id']}}: {{it['suggestion']}}</li>" for it in (data.get('suggestions') or [])])}</ul>
    """
    ).strip()


def render_clusters(clusters: List[Dict[str, Any]]) -> str:
    formatted: List[str] = []
    for c in clusters:
        cid = c.get("cluster_id")
        conf = c.get("confidence")
        members = ", ".join([str(it.get("id")) for it in c.get("items", [])])
        formatted.append(f"{cid} - confidence {conf:.2f} - members: {members}")
    return render_list(formatted, title="Duplicate Clusters")


