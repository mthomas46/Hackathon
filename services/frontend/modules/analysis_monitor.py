"""Analysis Service monitoring infrastructure for Frontend service.

Provides caching and visualization capabilities for analysis service results,
linking findings with documents and enabling deep-dive exploration.
"""
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict

from services.shared.utilities import utc_now
from .shared_utils import get_analysis_service_url, get_frontend_clients


class AnalysisMonitor:
    """Monitor for analysis service results and findings."""

    def __init__(self):
        self._analysis_results = []
        self._findings_cache = []
        self._detectors_cache = {}
        self._reports_cache = {}
        self._integration_health = {}
        self._cache_ttl = 60  # Cache for 60 seconds

    def is_cache_fresh(self, cache_key: str) -> bool:
        """Check if cache is still fresh."""
        cache_time = self._activity_cache.get(f"{cache_key}_updated")
        if not cache_time:
            return False
        return (utc_now() - cache_time).total_seconds() < self._cache_ttl

    async def get_analysis_status(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get comprehensive analysis service status."""
        if not force_refresh and self.is_cache_fresh("status"):
            return self._activity_cache.get("status", {})

        try:
            clients = get_frontend_clients()
            analysis_url = get_analysis_service_url()

            # Get basic info
            detectors = await clients.get_json(f"{analysis_url}/detectors")
            integration_health = await clients.get_json(f"{analysis_url}/integration/health")

            status_data = {
                "detectors": detectors.get("detectors", []),
                "integration_health": integration_health,
                "analysis_stats": self._calculate_analysis_stats(),
                "recent_findings": self._findings_cache[-10:] if self._findings_cache else [],  # Last 10 findings
                "last_updated": utc_now().isoformat()
            }

            self._activity_cache["status"] = status_data
            self._activity_cache["status_updated"] = utc_now()

            return status_data

        except Exception as e:
            return {
                "error": str(e),
                "detectors": [],
                "integration_health": {},
                "analysis_stats": {},
                "recent_findings": [],
                "last_updated": utc_now().isoformat()
            }

    async def get_findings(
        self,
        severity: Optional[str] = None,
        finding_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Get findings from analysis service with filtering."""
        if not force_refresh and self.is_cache_fresh("findings"):
            findings = self._findings_cache
        else:
            try:
                clients = get_frontend_clients()
                analysis_url = get_analysis_service_url()

                params = {}
                if severity:
                    params["severity"] = severity
                if finding_type:
                    params["type"] = finding_type
                if limit:
                    params["limit"] = limit

                response = await clients.get_json(f"{analysis_url}/findings", params)
                findings = response.get("findings", [])

                self._findings_cache = findings
                self._activity_cache["findings_updated"] = utc_now()

            except Exception as e:
                findings = []

        # Apply pagination
        start_idx = offset
        end_idx = offset + limit
        paginated_findings = findings[start_idx:end_idx] if start_idx < len(findings) else []

        return {
            "findings": paginated_findings,
            "total": len(findings),
            "limit": limit,
            "offset": offset,
            "filtered_by": {
                "severity": severity,
                "type": finding_type
            }
        }

    async def get_analysis_result(self, analysis_id: str) -> Dict[str, Any]:
        """Get a specific analysis result with linked documents."""
        # Look for the analysis in our cache first
        analysis = None
        for result in self._analysis_results:
            if result.get("id") == analysis_id:
                analysis = result
                break

        if not analysis:
            return {"error": "Analysis result not found", "analysis": None}

        # Enhance with document information
        enhanced_analysis = await self._enhance_analysis_with_documents(analysis)

        return {
            "analysis": enhanced_analysis,
            "linked_documents": enhanced_analysis.get("linked_documents", []),
            "findings_count": len(enhanced_analysis.get("findings", []))
        }

    async def run_analysis(
        self,
        targets: List[str],
        analysis_type: str = "consistency",
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run a new analysis and cache the results."""
        try:
            clients = get_frontend_clients()
            analysis_url = get_analysis_service_url()

            payload = {
                "targets": targets,
                "analysis_type": analysis_type,
                "options": options or {}
            }

            response = await clients.post_json(f"{analysis_url}/analyze", payload)

            if response.get("success"):
                # Cache the analysis result
                analysis_result = {
                    "id": f"analysis_{utc_now().isoformat()}",
                    "timestamp": utc_now().isoformat(),
                    "targets": targets,
                    "analysis_type": analysis_type,
                    "options": options,
                    "results": response.get("data", {}),
                    "findings": response.get("data", {}).get("findings", [])
                }

                self._analysis_results.insert(0, analysis_result)  # Add to front

                # Keep only last 50 analyses
                if len(self._analysis_results) > 50:
                    self._analysis_results = self._analysis_results[:50]

                # Update findings cache
                new_findings = analysis_result["findings"]
                self._findings_cache.extend(new_findings)

                # Keep only last 200 findings
                if len(self._findings_cache) > 200:
                    self._findings_cache = self._findings_cache[-200:]

                return {
                    "success": True,
                    "analysis_id": analysis_result["id"],
                    "findings_count": len(new_findings),
                    "results": analysis_result
                }

            return {
                "success": False,
                "error": response.get("message", "Analysis failed"),
                "results": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": None
            }

    async def get_reports(self, report_type: str = "summary") -> Dict[str, Any]:
        """Get analysis reports."""
        cache_key = f"report_{report_type}"
        if self.is_cache_fresh(cache_key):
            return self._activity_cache.get(cache_key, {})

        try:
            clients = get_frontend_clients()
            analysis_url = get_analysis_service_url()

            if report_type == "confluence_consolidation":
                response = await clients.get_json(f"{analysis_url}/reports/confluence/consolidation")
            elif report_type == "jira_staleness":
                response = await clients.get_json(f"{analysis_url}/reports/jira/staleness")
            else:
                # Generate general report
                report_payload = {"kind": report_type, "format": "json"}
                response = await clients.post_json(f"{analysis_url}/reports/generate", report_payload)

            report_data = {
                "type": report_type,
                "data": response.get("data", response),
                "generated_at": utc_now().isoformat()
            }

            self._activity_cache[cache_key] = report_data
            self._activity_cache[f"{cache_key}_updated"] = utc_now()

            return report_data

        except Exception as e:
            return {
                "type": report_type,
                "error": str(e),
                "data": {},
                "generated_at": utc_now().isoformat()
            }

    async def _enhance_analysis_with_documents(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance analysis results with document information."""
        enhanced_analysis = analysis.copy()
        linked_documents = []

        try:
            from .data_browser import data_browser

            # Get document information for each target
            for target_id in analysis.get("targets", []):
                doc_info = await data_browser.get_doc_store_document(target_id)
                if doc_info.get("document"):
                    linked_documents.append(doc_info["document"])

            enhanced_analysis["linked_documents"] = linked_documents

        except Exception as e:
            enhanced_analysis["linked_documents_error"] = str(e)

        return enhanced_analysis

    def _calculate_analysis_stats(self) -> Dict[str, Any]:
        """Calculate statistics from cached analysis data."""
        if not self._analysis_results:
            return {
                "total_analyses": 0,
                "total_findings": 0,
                "analysis_types": {},
                "severity_breakdown": {},
                "type_breakdown": {}
            }

        total_findings = sum(len(result.get("findings", [])) for result in self._analysis_results)

        # Analysis types
        analysis_types = defaultdict(int)
        for result in self._analysis_results:
            analysis_types[result.get("analysis_type", "unknown")] += 1

        # Findings breakdown
        severity_breakdown = defaultdict(int)
        type_breakdown = defaultdict(int)

        for result in self._analysis_results:
            for finding in result.get("findings", []):
                severity_breakdown[finding.get("severity", "unknown")] += 1
                type_breakdown[finding.get("type", "unknown")] += 1

        return {
            "total_analyses": len(self._analysis_results),
            "total_findings": total_findings,
            "analysis_types": dict(analysis_types),
            "severity_breakdown": dict(severity_breakdown),
            "type_breakdown": dict(type_breakdown),
            "average_findings_per_analysis": total_findings / len(self._analysis_results) if self._analysis_results else 0
        }

    def get_analysis_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent analysis history."""
        return self._analysis_results[:limit]

    def get_finding_details(self, finding_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific finding."""
        for result in self._analysis_results:
            for finding in result.get("findings", []):
                if finding.get("id") == finding_id:
                    return {
                        "finding": finding,
                        "analysis_id": result.get("id"),
                        "analysis_timestamp": result.get("timestamp"),
                        "targets": result.get("targets", [])
                    }
        return None


# Global instance
analysis_monitor = AnalysisMonitor()

# Initialize activity cache
analysis_monitor._activity_cache = {}
