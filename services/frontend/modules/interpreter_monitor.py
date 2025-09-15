"""Interpreter monitoring infrastructure for Frontend service.

Provides visualization and monitoring capabilities for interpreter
service natural language processing and workflow generation.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from services.shared.utilities import utc_now
from .shared_utils import get_interpreter_url, get_frontend_clients


class InterpreterMonitor:
    """Monitor for interpreter service natural language processing and workflow operations."""

    def __init__(self):
        self._interpretations = []
        self._executions = []
        self._cache_ttl = 30  # Cache for 30 seconds

    def is_cache_fresh(self, cache_key: str) -> bool:
        """Check if cache is still fresh."""
        cache_time = getattr(self, f"_{cache_key}_updated", None)
        if not cache_time:
            return False
        return (utc_now() - cache_time).total_seconds() < self._cache_ttl

    async def get_interpreter_status(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get comprehensive interpreter service status."""
        if not force_refresh and self.is_cache_fresh("status"):
            return getattr(self, "_status_cache", {})

        try:
            clients = get_frontend_clients()
            interpreter_url = get_interpreter_url()

            # Get health and intents
            health_response = await clients.get_json(f"{interpreter_url}/health")
            intents_response = await clients.get_json(f"{interpreter_url}/intents")

            status_data = {
                "health": health_response,
                "intents": intents_response,
                "interpretation_stats": self._calculate_interpretation_stats(),
                "execution_stats": self._calculate_execution_stats(),
                "recent_interpretations": self._interpretations[-10:] if self._interpretations else [],  # Last 10 interpretations
                "recent_executions": self._executions[-10:] if self._executions else [],  # Last 10 executions
                "last_updated": utc_now().isoformat()
            }

            self._status_cache = status_data
            self._status_updated = utc_now()

            return status_data

        except Exception as e:
            return {
                "error": str(e),
                "health": {},
                "intents": {},
                "interpretation_stats": {},
                "execution_stats": {},
                "recent_interpretations": [],
                "recent_executions": [],
                "last_updated": utc_now().isoformat()
            }

    async def get_supported_intents(self) -> List[Dict[str, Any]]:
        """Get list of supported intents and their examples."""
        try:
            clients = get_frontend_clients()
            interpreter_url = get_interpreter_url()

            intents_response = await clients.get_json(f"{interpreter_url}/intents")
            return intents_response if isinstance(intents_response, list) else []

        except Exception as e:
            return []

    async def interpret_query(self, query: str, session_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Interpret a natural language query and cache the result."""
        try:
            clients = get_frontend_clients()
            interpreter_url = get_interpreter_url()

            payload = {"query": query}
            if session_id:
                payload["session_id"] = session_id
            if user_id:
                payload["user_id"] = user_id

            response = await clients.post_json(f"{interpreter_url}/interpret", payload)

            if response.get("intent") or "intent" in response:
                # Cache the interpretation
                interpretation_result = {
                    "id": f"interpretation_{utc_now().isoformat()}",
                    "timestamp": utc_now().isoformat(),
                    "query": query[:200] + "..." if len(query) > 200 else query,
                    "session_id": session_id,
                    "user_id": user_id,
                    "intent": response.get("intent", {}),
                    "entities": response.get("entities", []),
                    "confidence": response.get("confidence", 0),
                    "workflow": response.get("workflow", {}),
                    "response": response
                }

                self._interpretations.insert(0, interpretation_result)  # Add to front

                # Keep only last 50 interpretations
                if len(self._interpretations) > 50:
                    self._interpretations = self._interpretations[:50]

                return {
                    "success": True,
                    "interpretation_id": interpretation_result["id"],
                    "intent": interpretation_result["intent"],
                    "confidence": interpretation_result["confidence"],
                    "workflow": interpretation_result["workflow"],
                    "response": response
                }

            return {
                "success": False,
                "error": "Interpretation failed",
                "response": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": None
            }

    async def execute_workflow(self, query: str, session_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a workflow from a natural language query and cache the result."""
        try:
            clients = get_frontend_clients()
            interpreter_url = get_interpreter_url()

            payload = {"query": query}
            if session_id:
                payload["session_id"] = session_id
            if user_id:
                payload["user_id"] = user_id

            response = await clients.post_json(f"{interpreter_url}/execute", payload)

            # Cache the execution
            execution_result = {
                "id": f"execution_{utc_now().isoformat()}",
                "timestamp": utc_now().isoformat(),
                "query": query[:200] + "..." if len(query) > 200 else query,
                "session_id": session_id,
                "user_id": user_id,
                "success": response.get("success", False),
                "results": response.get("results", {}),
                "execution_time": response.get("execution_time"),
                "steps_completed": len(response.get("results", {}).get("steps", [])),
                "response": response
            }

            self._executions.insert(0, execution_result)  # Add to front

            # Keep only last 50 executions
            if len(self._executions) > 50:
                self._executions = self._executions[:50]

            return {
                "success": True,
                "execution_id": execution_result["id"],
                "results": execution_result["results"],
                "execution_time": execution_result["execution_time"],
                "response": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": None
            }

    def _calculate_interpretation_stats(self) -> Dict[str, Any]:
        """Calculate statistics from cached interpretations."""
        if not self._interpretations:
            return {
                "total_interpretations": 0,
                "average_confidence": 0,
                "unique_intents": 0,
                "intents_detected": []
            }

        total = len(self._interpretations)
        avg_confidence = sum(interp.get("confidence", 0) for interp in self._interpretations) / total

        # Unique intents
        intents = set()
        for interp in self._interpretations:
            if interp.get("intent", {}).get("name"):
                intents.add(interp["intent"]["name"])

        return {
            "total_interpretations": total,
            "average_confidence": round(avg_confidence, 2),
            "unique_intents": len(intents),
            "intents_detected": list(intents)
        }

    def _calculate_execution_stats(self) -> Dict[str, Any]:
        """Calculate statistics from cached executions."""
        if not self._executions:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "average_execution_time": 0,
                "average_steps_completed": 0
            }

        total = len(self._executions)
        successful = sum(1 for exec in self._executions if exec.get("success"))
        failed = total - successful

        # Calculate averages
        execution_times = [exec.get("execution_time", 0) for exec in self._executions if exec.get("execution_time")]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0

        avg_steps = sum(exec.get("steps_completed", 0) for exec in self._executions) / total

        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": round((successful / total) * 100, 1) if total > 0 else 0,
            "average_execution_time": round(avg_execution_time, 2),
            "average_steps_completed": round(avg_steps, 1)
        }

    def get_interpretation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent interpretation history."""
        return self._interpretations[:limit]

    def get_execution_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent execution history."""
        return self._executions[:limit]


# Global instance
interpreter_monitor = InterpreterMonitor()
