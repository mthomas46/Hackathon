"""LLM Gateway Client - Client for LLM Gateway Service.

This module provides a client for interacting with the LLM Gateway service,
enabling AI-powered insights and intelligent analysis in the dashboard.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from infrastructure.config.config import get_config


class LLMGatewayClient:
    """Client for interacting with the LLM Gateway service."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize the LLM Gateway client.

        Args:
            base_url: Base URL of the LLM Gateway service
            timeout: Request timeout in seconds
        """
        self.config = get_config()
        self.base_url = base_url or "http://localhost:5055"
        self.timeout = timeout

        # HTTP client setup
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={"Content-Type": "application/json", "User-Agent": "SimulationDashboard/1.0"},
        )

        # Logging
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def health_check(self) -> Dict[str, Any]:
        """Check LLM Gateway health."""
        try:
            response = await self.client.get("/health")
            return response.json()
        except Exception as e:
            self.logger.error(f"LLM Gateway health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def get_providers(self) -> Dict[str, Any]:
        """Get available LLM providers and their status."""
        try:
            response = await self.client.get("/providers")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get providers: {e}")
            return {"providers": [], "error": str(e)}

    async def query_llm(
        self,
        prompt: str,
        model: str = "llama2",
        provider: str = "ollama",
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Send a query to the LLM Gateway."""
        try:
            request_data = {
                "prompt": prompt,
                "model": model,
                "provider": provider,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False,
            }

            response = await self.client.post("/query", json=request_data)
            return response.json()
        except Exception as e:
            self.logger.error(f"LLM query failed: {e}")
            return {"success": False, "error": str(e)}

    async def chat_llm(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama2",
        provider: str = "ollama",
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Send a chat request to the LLM Gateway."""
        try:
            request_data = {
                "messages": messages,
                "model": model,
                "provider": provider,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False,
            }

            response = await self.client.post("/chat", json=request_data)
            return response.json()
        except Exception as e:
            self.logger.error(f"LLM chat failed: {e}")
            return {"success": False, "error": str(e)}

    async def generate_insights(self, context: Dict[str, Any]) -> List[str]:
        """Generate intelligent insights using LLM based on context."""
        try:
            # Create a comprehensive prompt based on context
            prompt = self._build_insights_prompt(context)

            # Query the LLM
            result = await self.query_llm(
                prompt=prompt,
                model="llama2",
                max_tokens=500,
                temperature=0.3,  # Lower temperature for more focused insights
            )

            if result.get("success"):
                # Parse and clean the response
                response_text = result.get("data", {}).get("response", "")
                insights = self._parse_insights_response(response_text)
                return insights
            else:
                return ["LLM analysis unavailable - using fallback insights"]

        except Exception as e:
            self.logger.error(f"Failed to generate insights: {e}")
            return ["Error generating AI insights - using basic analysis"]

    def _build_insights_prompt(self, context: Dict[str, Any]) -> str:
        """Build a comprehensive insights prompt from context data."""
        health_data = context.get("health_data", {})
        simulation_data = context.get("simulation_data", {})
        timestamp = context.get("timestamp", datetime.now())

        prompt = f"""Analyze the following system health and simulation data to provide intelligent insights:

SYSTEM HEALTH SUMMARY:
- Overall Health: {health_data.get('overall_health', 'unknown')}
- Total Services: {len(health_data.get('services', {}))}
- Healthy Services: {sum(1 for s in health_data.get('services', {}).values() if s.get('status') == 'healthy')}

SERVICE DETAILS:
"""

        for service_name, service_data in health_data.get("services", {}).items():
            status = service_data.get("status", "unknown")
            response_time = service_data.get("response_time", "N/A")
            prompt += f"- {service_name}: {status} (response time: {response_time})\n"

        prompt += f"""

SIMULATION METRICS:
- Active Simulations: {simulation_data.get('active_count', 0)}
- Success Rate: {simulation_data.get('success_rate', 0)}%
- Average Duration: {simulation_data.get('avg_duration', 0)} minutes
- Performance Score: {simulation_data.get('performance_score', 0)}%

CURRENT TIMESTAMP: {timestamp}

Please provide 3-5 intelligent insights about:
1. System performance and health trends
2. Potential optimization opportunities
3. Risk assessment and recommendations
4. Predictive analysis for the next 2-4 hours

Format your response as a numbered list of insights, each starting with an emoji and being concise but informative."""

        return prompt

    def _parse_insights_response(self, response_text: str) -> List[str]:
        """Parse the LLM response into clean insights."""
        insights = []

        # Split by numbered items or bullet points
        lines = response_text.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for numbered insights or insights starting with emojis
            if (line[0].isdigit() and line[1:3] in [". ", ") "]) or any(
                line.startswith(emoji) for emoji in ["🔍", "📈", "⚠️", "💡", "🎯", "🚀", "🔮"]
            ):
                # Clean up the line
                if line[0].isdigit():
                    # Remove numbering
                    if ". " in line:
                        insight = line.split(". ", 1)[1]
                    elif ") " in line:
                        insight = line.split(") ", 1)[1]
                    else:
                        insight = line[2:]  # Remove number
                else:
                    insight = line

                # Clean and add if meaningful
                insight = insight.strip()
                if len(insight) > 10:  # Only add substantial insights
                    insights.append(insight)

        # If no structured insights found, create some from the text
        if not insights:
            # Split by sentences and take first few meaningful ones
            sentences = [s.strip() for s in response_text.split(".") if s.strip()]
            insights = sentences[:4]  # Take up to 4 insights

        return insights[:5]  # Limit to 5 insights max
