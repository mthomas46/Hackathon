"""Code Analyzer monitoring infrastructure for Frontend service.

Provides visualization and monitoring capabilities for code analyzer
service analysis results, security scans, and style checking.
"""
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta

from services.shared.utilities import utc_now
from .shared_utils import get_code_analyzer_url, get_frontend_clients


class CodeAnalyzerMonitor:
    """Monitor for code analyzer service operations."""

    def __init__(self):
        self._analyses = []
        self._security_scans = []
        self._style_checks = []
        self._cache_ttl = 60  # Cache for 60 seconds

    def is_cache_fresh(self, cache_key: str) -> bool:
        """Check if cache is still fresh."""
        cache_time = self._activity_cache.get(f"{cache_key}_updated")
        if not cache_time:
            return False
        return (utc_now() - cache_time).total_seconds() < self._cache_ttl

    async def get_analyzer_status(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get comprehensive code analyzer service status."""
        if not force_refresh and self.is_cache_fresh("status"):
            return self._activity_cache.get("status", {})

        try:
            clients = get_frontend_clients()
            analyzer_url = get_code_analyzer_url()

            # Get health status
            health_response = await clients.get_json(f"{analyzer_url}/health")

            # Get style examples (to see available styles)
            style_response = await clients.get_json(f"{analyzer_url}/style/examples")

            status_data = {
                "health": health_response,
                "available_styles": style_response.get("examples", []),
                "analysis_stats": self._calculate_analysis_stats(),
                "recent_analyses": self._analyses[-10:] if self._analyses else [],
                "recent_security_scans": self._security_scans[-10:] if self._security_scans else [],
                "recent_style_checks": self._style_checks[-10:] if self._style_checks else [],
                "last_updated": utc_now().isoformat()
            }

            self._activity_cache["status"] = status_data
            self._activity_cache["status_updated"] = utc_now()

            return status_data

        except Exception as e:
            return {
                "error": str(e),
                "health": {},
                "available_styles": [],
                "analysis_stats": {},
                "recent_analyses": [],
                "recent_security_scans": [],
                "recent_style_checks": [],
                "last_updated": utc_now().isoformat()
            }

    async def analyze_text(self, text: str, analysis_type: str = "general") -> Dict[str, Any]:
        """Analyze text content and cache the result."""
        try:
            clients = get_frontend_clients()
            analyzer_url = get_code_analyzer_url()

            payload = {
                "text": text,
                "analysis_type": analysis_type
            }

            response = await clients.post_json(f"{analyzer_url}/analyze/text", payload)

            # Cache the analysis
            analysis_result = {
                "id": f"analysis_{utc_now().isoformat()}",
                "timestamp": utc_now().isoformat(),
                "type": "text_analysis",
                "analysis_type": analysis_type,
                "text_length": len(text),
                "result": response
            }

            self._analyses.insert(0, analysis_result)
            if len(self._analyses) > 50:
                self._analyses = self._analyses[:50]

            return {
                "success": True,
                "analysis_id": analysis_result["id"],
                "result": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }

    async def analyze_files(self, files: List[str], analysis_type: str = "general") -> Dict[str, Any]:
        """Analyze files and cache the result."""
        try:
            clients = get_frontend_clients()
            analyzer_url = get_code_analyzer_url()

            payload = {
                "files": files,
                "analysis_type": analysis_type
            }

            response = await clients.post_json(f"{analyzer_url}/analyze/files", payload)

            # Cache the analysis
            analysis_result = {
                "id": f"analysis_{utc_now().isoformat()}",
                "timestamp": utc_now().isoformat(),
                "type": "file_analysis",
                "analysis_type": analysis_type,
                "file_count": len(files),
                "files": files,
                "result": response
            }

            self._analyses.insert(0, analysis_result)
            if len(self._analyses) > 50:
                self._analyses = self._analyses[:50]

            return {
                "success": True,
                "analysis_id": analysis_result["id"],
                "result": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }

    async def scan_security(self, code: str) -> Dict[str, Any]:
        """Perform security scan and cache the result."""
        try:
            clients = get_frontend_clients()
            analyzer_url = get_code_analyzer_url()

            payload = {"code": code}

            response = await clients.post_json(f"{analyzer_url}/scan/secure", payload)

            # Cache the security scan
            scan_result = {
                "id": f"security_scan_{utc_now().isoformat()}",
                "timestamp": utc_now().isoformat(),
                "code_length": len(code),
                "result": response
            }

            self._security_scans.insert(0, scan_result)
            if len(self._security_scans) > 50:
                self._security_scans = self._security_scans[:50]

            return {
                "success": True,
                "scan_id": scan_result["id"],
                "result": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }

    async def check_style(self, code: str, style: str = "google") -> Dict[str, Any]:
        """Check code style and cache the result."""
        try:
            clients = get_frontend_clients()
            analyzer_url = get_code_analyzer_url()

            payload = {"code": code, "style": style}

            response = await clients.post_json(f"{analyzer_url}/style/examples", payload)

            # Cache the style check
            style_result = {
                "id": f"style_check_{utc_now().isoformat()}",
                "timestamp": utc_now().isoformat(),
                "style": style,
                "code_length": len(code),
                "result": response
            }

            self._style_checks.insert(0, style_result)
            if len(self._style_checks) > 50:
                self._style_checks = self._style_checks[:50]

            return {
                "success": True,
                "check_id": style_result["id"],
                "result": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }

    def _calculate_analysis_stats(self) -> Dict[str, Any]:
        """Calculate statistics from cached analyses."""
        total_analyses = len(self._analyses)
        total_security_scans = len(self._security_scans)
        total_style_checks = len(self._style_checks)

        # Analysis types breakdown
        analysis_types = {}
        for analysis in self._analyses:
            atype = analysis.get("analysis_type", "unknown")
            analysis_types[atype] = analysis_types.get(atype, 0) + 1

        # Style breakdown
        styles = {}
        for check in self._style_checks:
            style = check.get("style", "unknown")
            styles[style] = styles.get(style, 0) + 1

        return {
            "total_analyses": total_analyses,
            "total_security_scans": total_security_scans,
            "total_style_checks": total_style_checks,
            "analysis_types": analysis_types,
            "style_breakdown": styles
        }

    def get_analysis_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent analysis history."""
        return self._analyses[:limit]

    def get_security_scan_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent security scan history."""
        return self._security_scans[:limit]

    def get_style_check_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent style check history."""
        return self._style_checks[:limit]


# Global instance
code_analyzer_monitor = CodeAnalyzerMonitor()

# Initialize activity cache
code_analyzer_monitor._activity_cache = {}
