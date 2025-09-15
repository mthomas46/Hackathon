"""Secure Analyzer monitoring infrastructure for Frontend service.

Provides visualization and monitoring capabilities for secure analyzer
service content detection, policy enforcement, and secure summarization.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from services.shared.utilities import utc_now
from .shared_utils import get_secure_analyzer_url, get_frontend_clients


class SecureAnalyzerMonitor:
    """Monitor for secure analyzer service content detection and policy enforcement."""

    def __init__(self):
        self._detections = []
        self._suggestions = []
        self._summaries = []
        self._cache_ttl = 30  # Cache for 30 seconds

    def is_cache_fresh(self, cache_key: str) -> bool:
        """Check if cache is still fresh."""
        cache_time = getattr(self, f"_{cache_key}_updated", None)
        if not cache_time:
            return False
        return (utc_now() - cache_time).total_seconds() < self._cache_ttl

    async def get_secure_status(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get comprehensive secure analyzer service status."""
        if not force_refresh and self.is_cache_fresh("status"):
            return getattr(self, "_status_cache", {})

        try:
            clients = get_frontend_clients()
            secure_url = get_secure_analyzer_url()

            # Get health status
            health_response = await clients.get_json(f"{secure_url}/health")

            status_data = {
                "health": health_response,
                "analysis_stats": self._calculate_analysis_stats(),
                "recent_detections": self._detections[-10:] if self._detections else [],  # Last 10 detections
                "recent_suggestions": self._suggestions[-10:] if self._suggestions else [],  # Last 10 suggestions
                "recent_summaries": self._summaries[-10:] if self._summaries else [],  # Last 10 summaries
                "last_updated": utc_now().isoformat()
            }

            self._status_cache = status_data
            self._status_updated = utc_now()

            return status_data

        except Exception as e:
            return {
                "error": str(e),
                "health": {},
                "analysis_stats": {},
                "recent_detections": [],
                "recent_suggestions": [],
                "recent_summaries": [],
                "last_updated": utc_now().isoformat()
            }

    async def detect_content(self, content: str, keywords: Optional[List[str]] = None, keyword_document: Optional[str] = None) -> Dict[str, Any]:
        """Detect sensitive content in provided text."""
        try:
            clients = get_frontend_clients()
            secure_url = get_secure_analyzer_url()

            payload = {
                "content": content,
                "keywords": keywords or [],
                "keyword_document": keyword_document
            }

            response = await clients.post_json(f"{secure_url}/detect", payload)

            # Cache the detection result
            detection_result = {
                "id": f"detection_{utc_now().isoformat()}",
                "timestamp": utc_now().isoformat(),
                "content_length": len(content),
                "has_keywords": bool(keywords),
                "has_keyword_doc": bool(keyword_document),
                "sensitive": response.get("sensitive", False),
                "matches": response.get("matches", []),
                "topics": response.get("topics", []),
                "response": response
            }

            self._detections.insert(0, detection_result)  # Add to front
            # Keep only last 50 detections
            if len(self._detections) > 50:
                self._detections = self._detections[:50]

            return {
                "success": True,
                "detection_id": detection_result["id"],
                "sensitive": detection_result["sensitive"],
                "matches": detection_result["matches"],
                "topics": detection_result["topics"],
                "response": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": None
            }

    async def suggest_models(self, content: str, keywords: Optional[List[str]] = None, keyword_document: Optional[str] = None) -> Dict[str, Any]:
        """Get model suggestions based on content sensitivity."""
        try:
            clients = get_frontend_clients()
            secure_url = get_secure_analyzer_url()

            payload = {
                "content": content,
                "keywords": keywords or [],
                "keyword_document": keyword_document
            }

            response = await clients.post_json(f"{secure_url}/suggest", payload)

            # Cache the suggestion result
            suggestion_result = {
                "id": f"suggestion_{utc_now().isoformat()}",
                "timestamp": utc_now().isoformat(),
                "content_length": len(content),
                "has_keywords": bool(keywords),
                "has_keyword_doc": bool(keyword_document),
                "sensitive": response.get("sensitive", False),
                "allowed_models": response.get("allowed_models", []),
                "suggestion": response.get("suggestion", ""),
                "response": response
            }

            self._suggestions.insert(0, suggestion_result)  # Add to front
            # Keep only last 50 suggestions
            if len(self._suggestions) > 50:
                self._suggestions = self._suggestions[:50]

            return {
                "success": True,
                "suggestion_id": suggestion_result["id"],
                "sensitive": suggestion_result["sensitive"],
                "allowed_models": suggestion_result["allowed_models"],
                "suggestion": suggestion_result["suggestion"],
                "response": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": None
            }

    async def secure_summarize(self, content: str, providers: Optional[List[Dict[str, Any]]] = None, override_policy: bool = False, keywords: Optional[List[str]] = None, keyword_document: Optional[str] = None, prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate secure summary with policy enforcement."""
        try:
            clients = get_frontend_clients()
            secure_url = get_secure_analyzer_url()

            payload = {
                "content": content,
                "providers": providers or [],
                "override_policy": override_policy,
                "keywords": keywords or [],
                "keyword_document": keyword_document,
                "prompt": prompt
            }

            response = await clients.post_json(f"{secure_url}/summarize", payload)

            # Cache the summary result
            summary_result = {
                "id": f"summary_{utc_now().isoformat()}",
                "timestamp": utc_now().isoformat(),
                "content_length": len(content),
                "override_policy": override_policy,
                "has_keywords": bool(keywords),
                "has_keyword_doc": bool(keyword_document),
                "has_custom_prompt": bool(prompt),
                "provider_used": response.get("provider_used", ""),
                "confidence": response.get("confidence", 0),
                "policy_enforced": response.get("policy_enforced", False),
                "topics_detected": response.get("topics_detected", []),
                "summary_length": len(response.get("summary", "")),
                "response": response
            }

            self._summaries.insert(0, summary_result)  # Add to front
            # Keep only last 50 summaries
            if len(self._summaries) > 50:
                self._summaries = self._summaries[:50]

            return {
                "success": True,
                "summary_id": summary_result["id"],
                "summary": response.get("summary", ""),
                "provider_used": summary_result["provider_used"],
                "confidence": summary_result["confidence"],
                "policy_enforced": summary_result["policy_enforced"],
                "topics_detected": summary_result["topics_detected"],
                "response": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": None
            }

    def _calculate_analysis_stats(self) -> Dict[str, Any]:
        """Calculate statistics from cached analysis results."""
        if not self._detections:
            return {
                "total_detections": 0,
                "sensitive_content_detected": 0,
                "detection_accuracy": 0,
                "total_suggestions": 0,
                "total_summaries": 0
            }

        total_detections = len(self._detections)
        sensitive_detections = sum(1 for d in self._detections if d.get("sensitive"))

        total_suggestions = len(self._suggestions)
        total_summaries = len(self._summaries)

        # Calculate detection accuracy (if we had ground truth)
        detection_accuracy = (sensitive_detections / total_detections) * 100 if total_detections > 0 else 0

        return {
            "total_detections": total_detections,
            "sensitive_content_detected": sensitive_detections,
            "detection_accuracy": round(detection_accuracy, 1),
            "total_suggestions": total_suggestions,
            "total_summaries": total_summaries
        }

    def get_detection_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent detection history."""
        return self._detections[:limit]

    def get_suggestion_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent suggestion history."""
        return self._suggestions[:limit]

    def get_summary_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent summary history."""
        return self._summaries[:limit]


# Global instance
secure_analyzer_monitor = SecureAnalyzerMonitor()
