from typing import Any, Dict, List, Tuple, Callable
from rich.prompt import Prompt
import json

from services.shared.integrations.clients.clients import ServiceClients
from ...utils.display_helpers import print_kv, print_list


def build_actions(console, clients: ServiceClients) -> List[Tuple[str, Callable[[], Any]]]:
    # ============================================================================
    # BASIC ANALYSIS ENDPOINTS
    # ============================================================================

    async def analyze():
        target = Prompt.ask("Target ID (doc:... or api:...)")
        atype = Prompt.ask("Analysis type", default="consistency")
        url = f"{clients.analysis_service_url()}/analyze"
        rx = await clients.post_json(url, {"targets": [target], "analysis_type": atype})
        print_kv(console, "Result", rx)

    async def semantic_similarity():
        """Analyze semantic similarity between documents."""
        targets = Prompt.ask("Target IDs (comma-separated)")
        threshold = Prompt.ask("Similarity threshold (0.0-1.0)", default="0.7")
        url = f"{clients.analysis_service_url()}/analyze/semantic-similarity"
        targets_list = [t.strip() for t in targets.split(",") if t.strip()]
        rx = await clients.post_json(url, {"targets": targets_list, "threshold": float(threshold)})
        print_kv(console, "Semantic Similarity Analysis", rx)

    async def sentiment_analysis():
        """Analyze sentiment of documents."""
        targets = Prompt.ask("Target IDs (comma-separated)")
        url = f"{clients.analysis_service_url()}/analyze/sentiment"
        targets_list = [t.strip() for t in targets.split(",") if t.strip()]
        rx = await clients.post_json(url, {"targets": targets_list})
        print_kv(console, "Sentiment Analysis", rx)

    async def tone_analysis():
        """Analyze tone of documents."""
        targets = Prompt.ask("Target IDs (comma-separated)")
        url = f"{clients.analysis_service_url()}/analyze/tone"
        targets_list = [t.strip() for t in targets.split(",") if t.strip()]
        rx = await clients.post_json(url, {"targets": targets_list})
        print_kv(console, "Tone Analysis", rx)

    async def quality_analysis():
        """Analyze content quality."""
        targets = Prompt.ask("Target IDs (comma-separated)")
        url = f"{clients.analysis_service_url()}/analyze/quality"
        targets_list = [t.strip() for t in targets.split(",") if t.strip()]
        rx = await clients.post_json(url, {"targets": targets_list})
        print_kv(console, "Quality Analysis", rx)

    # ============================================================================
    # TREND ANALYSIS ENDPOINTS
    # ============================================================================

    async def trend_analysis():
        """Analyze documentation trends."""
        targets = Prompt.ask("Target IDs (comma-separated)")
        timeframe = Prompt.ask("Timeframe (days)", default="30")
        url = f"{clients.analysis_service_url()}/analyze/trends"
        targets_list = [t.strip() for t in targets.split(",") if t.strip()]
        rx = await clients.post_json(url, {"targets": targets_list, "timeframe_days": int(timeframe)})
        print_kv(console, "Trend Analysis", rx)

    async def portfolio_trend_analysis():
        """Analyze trends across entire portfolio."""
        timeframe = Prompt.ask("Timeframe (days)", default="90")
        url = f"{clients.analysis_service_url()}/analyze/trends/portfolio"
        rx = await clients.post_json(url, {"timeframe_days": int(timeframe)})
        print_kv(console, "Portfolio Trend Analysis", rx)

    # ============================================================================
    # RISK ANALYSIS ENDPOINTS
    # ============================================================================

    async def risk_assessment():
        """Assess documentation risks."""
        targets = Prompt.ask("Target IDs (comma-separated)")
        url = f"{clients.analysis_service_url()}/analyze/risk"
        targets_list = [t.strip() for t in targets.split(",") if t.strip()]
        rx = await clients.post_json(url, {"targets": targets_list})
        print_kv(console, "Risk Assessment", rx)

    async def portfolio_risk_analysis():
        """Analyze risks across entire portfolio."""
        url = f"{clients.analysis_service_url()}/analyze/risk/portfolio"
        rx = await clients.post_json(url, {})
        print_kv(console, "Portfolio Risk Analysis", rx)

    # ============================================================================
    # REMEDIATION ENDPOINTS
    # ============================================================================

    async def remediate():
        """Generate remediation suggestions."""
        targets = Prompt.ask("Target IDs (comma-separated)")
        issue_type = Prompt.ask("Issue type (quality|consistency|completeness)", default="quality")
        url = f"{clients.analysis_service_url()}/remediate"
        targets_list = [t.strip() for t in targets.split(",") if t.strip()]
        rx = await clients.post_json(url, {"targets": targets_list, "issue_type": issue_type})
        print_kv(console, "Remediation Suggestions", rx)

    async def remediate_preview():
        """Preview remediation changes."""
        targets = Prompt.ask("Target IDs (comma-separated)")
        issue_type = Prompt.ask("Issue type (quality|consistency|completeness)", default="quality")
        url = f"{clients.analysis_service_url()}/remediate/preview"
        targets_list = [t.strip() for t in targets.split(",") if t.strip()]
        rx = await clients.post_json(url, {"targets": targets_list, "issue_type": issue_type})
        print_kv(console, "Remediation Preview", rx)

    # ============================================================================
    # WORKFLOW ENDPOINTS
    # ============================================================================

    async def workflow_events():
        """Send workflow event."""
        event_type = Prompt.ask("Event type (pr.created|commit.pushed|release.created)")
        entity_type = Prompt.ask("Entity type (pr|commit|release)")
        entity_id = Prompt.ask("Entity ID")
        metadata_input = Prompt.ask("Metadata JSON (optional)", default="{}")
        try:
            metadata = json.loads(metadata_input) if metadata_input.strip() else {}
        except:
            metadata = {}
        url = f"{clients.analysis_service_url()}/workflows/events"
        rx = await clients.post_json(url, {
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "metadata": metadata
        })
        print_kv(console, "Workflow Event", rx)

    async def workflow_status():
        """Get workflow status."""
        workflow_id = Prompt.ask("Workflow ID")
        url = f"{clients.analysis_service_url()}/workflows/{workflow_id}"
        rx = await clients.get_json(url)
        print_kv(console, f"Workflow {workflow_id} Status", rx)

    async def workflow_queue_status():
        """Get workflow queue status."""
        url = f"{clients.analysis_service_url()}/workflows/queue/status"
        rx = await clients.get_json(url)
        print_kv(console, "Workflow Queue Status", rx)

    # ============================================================================
    # DISTRIBUTED PROCESSING ENDPOINTS
    # ============================================================================

    async def distributed_task():
        """Submit distributed task."""
        task_type = Prompt.ask("Task type (analysis|indexing|cleanup)")
        targets_input = Prompt.ask("Targets (comma-separated)")
        targets = [t.strip() for t in targets_input.split(",") if t.strip()]
        priority = Prompt.ask("Priority (low|normal|high)", default="normal")
        url = f"{clients.analysis_service_url()}/distributed/tasks"
        rx = await clients.post_json(url, {
            "task_type": task_type,
            "targets": targets,
            "priority": priority
        })
        print_kv(console, "Distributed Task", rx)

    async def distributed_workers():
        """List distributed workers."""
        url = f"{clients.analysis_service_url()}/distributed/workers"
        rx = await clients.get_json(url)
        print_list(console, "Distributed Workers", rx.get("workers", []))

    async def distributed_stats():
        """Get distributed processing stats."""
        url = f"{clients.analysis_service_url()}/distributed/stats"
        rx = await clients.get_json(url)
        print_kv(console, "Distributed Stats", rx)

    # ============================================================================
    # REPORTING ENDPOINTS
    # ============================================================================

    async def generate_report():
        """Generate analysis report."""
        kind = Prompt.ask("Report kind", default="summary")
        format_type = Prompt.ask("Format (json|pdf|html)", default="json")
        filters_input = Prompt.ask("Filters JSON (optional)", default="{}")
        try:
            filters = json.loads(filters_input) if filters_input.strip() else {}
        except:
            filters = {}
        url = f"{clients.analysis_service_url()}/reports/generate"
        rx = await clients.post_json(url, {
            "kind": kind,
            "format": format_type,
            "filters": filters
        })
        print_kv(console, "Report Generation", rx)

    async def list_findings():
        """List analysis findings."""
        severity = Prompt.ask("Severity filter (optional)")
        category = Prompt.ask("Category filter (optional)")
        limit = Prompt.ask("Limit", default="50")
        params = {"limit": int(limit)}
        if severity:
            params["severity"] = severity
        if category:
            params["category"] = category
        url = f"{clients.analysis_service_url()}/findings"
        rx = await clients.get_json(url, params=params)
        print_list(console, "Findings", rx.get("findings", []))

    async def list_detectors():
        """List available detectors."""
        url = f"{clients.analysis_service_url()}/detectors"
        rx = await clients.get_json(url)
        print_list(console, "Detectors", rx.get("detectors", []))

    # ============================================================================
    # INTEGRATION ENDPOINTS
    # ============================================================================

    async def integration_health():
        """Check integration health."""
        url = f"{clients.analysis_service_url()}/integration/health"
        rx = await clients.get_json(url)
        print_kv(console, "Integration Health", rx)

    async def analyze_with_prompt():
        """Analyze with custom prompt."""
        targets_input = Prompt.ask("Target IDs (comma-separated)")
        prompt_id = Prompt.ask("Prompt ID")
        targets = [t.strip() for t in targets_input.split(",") if t.strip()]
        url = f"{clients.analysis_service_url()}/integration/analyze-with-prompt"
        rx = await clients.post_json(url, {
            "targets": targets,
            "prompt_id": prompt_id
        })
        print_kv(console, "Prompt-based Analysis", rx)

    async def natural_language_analysis():
        """Natural language analysis query."""
        query = Prompt.ask("Natural language query")
        context_input = Prompt.ask("Context JSON (optional)", default="{}")
        try:
            context = json.loads(context_input) if context_input.strip() else {}
        except:
            context = {}
        url = f"{clients.analysis_service_url()}/integration/natural-language-analysis"
        rx = await clients.post_json(url, {
            "query": query,
            "context": context
        })
        print_kv(console, "Natural Language Analysis", rx)

    # ============================================================================
    # PR CONFIDENCE ANALYSIS ENDPOINTS
    # ============================================================================

    async def pr_confidence_analysis():
        """Analyze PR confidence."""
        pr_id = Prompt.ask("Pull Request ID")
        analysis_type = Prompt.ask("Analysis type (comprehensive|quick)", default="comprehensive")
        url = f"{clients.analysis_service_url()}/pr-confidence/analyze"
        rx = await clients.post_json(url, {
            "pr_id": pr_id,
            "analysis_type": analysis_type
        })
        print_kv(console, "PR Confidence Analysis", rx)

    async def pr_confidence_history():
        """Get PR confidence history."""
        pr_id = Prompt.ask("Pull Request ID")
        url = f"{clients.analysis_service_url()}/pr-confidence/history/{pr_id}"
        rx = await clients.get_json(url)
        print_kv(console, f"PR {pr_id} Confidence History", rx)

    async def pr_confidence_statistics():
        """Get PR confidence statistics."""
        url = f"{clients.analysis_service_url()}/pr-confidence/statistics"
        rx = await clients.get_json(url)
        print_kv(console, "PR Confidence Statistics", rx)

    # ============================================================================
    # ORGANIZE ACTIONS BY CATEGORY
    # ============================================================================

    return [
        # Basic Analysis
        ("🔍 Analyze documents", analyze),
        ("🧠 Semantic similarity analysis", semantic_similarity),
        ("😊 Sentiment analysis", sentiment_analysis),
        ("🎭 Tone analysis", tone_analysis),
        ("⭐ Quality analysis", quality_analysis),

        # Trend Analysis
        ("📈 Trend analysis", trend_analysis),
        ("📊 Portfolio trend analysis", portfolio_trend_analysis),

        # Risk Analysis
        ("⚠️ Risk assessment", risk_assessment),
        ("📉 Portfolio risk analysis", portfolio_risk_analysis),

        # Remediation
        ("🔧 Generate remediation", remediate),
        ("👀 Preview remediation", remediate_preview),

        # Workflow Management
        ("📨 Send workflow event", workflow_events),
        ("📋 Get workflow status", workflow_status),
        ("📊 Workflow queue status", workflow_queue_status),

        # Distributed Processing
        ("⚡ Submit distributed task", distributed_task),
        ("👥 List distributed workers", distributed_workers),
        ("📈 Distributed processing stats", distributed_stats),

        # Reporting
        ("📄 Generate analysis report", generate_report),
        ("🔍 List findings", list_findings),
        ("🔧 List detectors", list_detectors),

        # Integration
        ("🩺 Integration health check", integration_health),
        ("💬 Analyze with custom prompt", analyze_with_prompt),
        ("🗣️ Natural language analysis", natural_language_analysis),

        # PR Confidence
        ("🔍 PR confidence analysis", pr_confidence_analysis),
        ("📚 PR confidence history", pr_confidence_history),
        ("📊 PR confidence statistics", pr_confidence_statistics),
    ]


