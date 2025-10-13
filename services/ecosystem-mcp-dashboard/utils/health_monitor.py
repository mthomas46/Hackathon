"""Health monitoring utilities for dashboard data sources."""

import httpx
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Health status for a data source."""
    name: str
    status: str  # "healthy", "degraded", "unhealthy", "unknown"
    latency_ms: float
    last_check: datetime
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class HealthMonitor:
    """Monitor health of all dashboard data sources."""
    
    def __init__(self, api_base_url: str, timeout: float = 5.0):
        """
        Initialize health monitor.
        
        Args:
            api_base_url: Base URL for the ecosystem-mcp API
            timeout: Request timeout in seconds
        """
        self.api_base_url = api_base_url
        self.timeout = timeout
        self.health_history: List[Dict[str, HealthStatus]] = []
        self.max_history = 100  # Keep last 100 checks
    
    async def check_api_health(self) -> HealthStatus:
        """Check ecosystem-mcp API health."""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.api_base_url}/health")
                latency = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    return HealthStatus(
                        name="API",
                        status="healthy",
                        latency_ms=latency,
                        last_check=datetime.now(),
                        details=data
                    )
                else:
                    return HealthStatus(
                        name="API",
                        status="unhealthy",
                        latency_ms=latency,
                        last_check=datetime.now(),
                        error_message=f"HTTP {response.status_code}"
                    )
        
        except httpx.ConnectError as e:
            return HealthStatus(
                name="API",
                status="unhealthy",
                latency_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                error_message=f"Connection failed: {str(e)}"
            )
        except httpx.TimeoutException:
            return HealthStatus(
                name="API",
                status="unhealthy",
                latency_ms=self.timeout * 1000,
                last_check=datetime.now(),
                error_message="Request timeout"
            )
        except Exception as e:
            return HealthStatus(
                name="API",
                status="unknown",
                latency_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    def check_api_health_sync(self) -> HealthStatus:
        """Synchronous version of check_api_health."""
        start_time = time.time()
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.api_base_url}/health")
                latency = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    return HealthStatus(
                        name="API",
                        status="healthy",
                        latency_ms=latency,
                        last_check=datetime.now(),
                        details=data
                    )
                else:
                    return HealthStatus(
                        name="API",
                        status="unhealthy",
                        latency_ms=latency,
                        last_check=datetime.now(),
                        error_message=f"HTTP {response.status_code}"
                    )
        
        except httpx.ConnectError as e:
            return HealthStatus(
                name="API",
                status="unhealthy",
                latency_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                error_message=f"Connection failed: {str(e)}"
            )
        except httpx.TimeoutException:
            return HealthStatus(
                name="API",
                status="unhealthy",
                latency_ms=self.timeout * 1000,
                last_check=datetime.now(),
                error_message="Request timeout"
            )
        except Exception as e:
            return HealthStatus(
                name="API",
                status="unknown",
                latency_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    def check_datasource(self, name: str, endpoint: str) -> HealthStatus:
        """
        Check health of a specific data source.
        
        Args:
            name: Name of the data source (e.g., "PostgreSQL", "Redis")
            endpoint: API endpoint to check
        
        Returns:
            HealthStatus object
        """
        start_time = time.time()
        
        try:
            response = httpx.get(
                f"{self.api_base_url}{endpoint}",
                timeout=self.timeout
            )
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                return HealthStatus(
                    name=name,
                    status="healthy",
                    latency_ms=latency,
                    last_check=datetime.now(),
                    details=data
                )
            elif response.status_code == 503:
                return HealthStatus(
                    name=name,
                    status="unhealthy",
                    latency_ms=latency,
                    last_check=datetime.now(),
                    error_message="Service unavailable"
                )
            else:
                return HealthStatus(
                    name=name,
                    status="degraded",
                    latency_ms=latency,
                    last_check=datetime.now(),
                    error_message=f"HTTP {response.status_code}"
                )
        
        except httpx.ConnectError as e:
            return HealthStatus(
                name=name,
                status="unhealthy",
                latency_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                error_message=f"Connection failed: {str(e)}"
            )
        except httpx.TimeoutException:
            return HealthStatus(
                name=name,
                status="unhealthy",
                latency_ms=self.timeout * 1000,
                last_check=datetime.now(),
                error_message="Request timeout"
            )
        except Exception as e:
            return HealthStatus(
                name=name,
                status="unknown",
                latency_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    def check_all_datasources(self) -> Dict[str, HealthStatus]:
        """Check all data sources and return their health status."""
        results = {}
        
        # Check API first
        api_status = self.check_api_health_sync()
        results["API"] = api_status
        
        # If API is healthy, extract component status from health response
        if api_status.status == "healthy" and api_status.details:
            components = api_status.details.get("components", {})
            
            # Map components from health endpoint
            component_mapping = {
                "Database": "database",
                "Redis": "redis",
                "ChromaDB": "chromadb",
                "Ollama": "ollama"
            }
            
            for display_name, component_key in component_mapping.items():
                if component_key in components:
                    comp_data = components[component_key]
                    comp_status = comp_data.get("status", "unknown")
                    
                    # Map component status to our status format
                    if comp_status == "healthy":
                        status = "healthy"
                    elif comp_status == "degraded":
                        status = "degraded"
                    else:
                        status = "unhealthy"
                    
                    results[display_name] = HealthStatus(
                        name=display_name,
                        status=status,
                        latency_ms=comp_data.get("response_time_ms", 0),
                        last_check=datetime.now(),
                        error_message=comp_data.get("message") if status != "healthy" else None,
                        details=comp_data
                    )
        else:
            # If API is unhealthy, mark all components as unknown
            for name in ["Database", "Redis", "ChromaDB", "Ollama"]:
                results[name] = HealthStatus(
                    name=name,
                    status="unknown",
                    latency_ms=0,
                    last_check=datetime.now(),
                    error_message="API unavailable or unhealthy"
                )
        
        # Store in history
        self.health_history.append(results)
        if len(self.health_history) > self.max_history:
            self.health_history.pop(0)
        
        return results
    
    def get_overall_status(self, results: Dict[str, HealthStatus]) -> str:
        """
        Determine overall system status.
        
        Args:
            results: Dictionary of health statuses
        
        Returns:
            "healthy", "degraded", or "unhealthy"
        """
        statuses = [r.status for r in results.values()]
        
        if all(s == "healthy" for s in statuses):
            return "healthy"
        elif any(s == "unhealthy" for s in statuses):
            return "unhealthy"
        else:
            return "degraded"
    
    def get_status_color(self, status: str) -> str:
        """Get color emoji for status."""
        colors = {
            "healthy": "🟢",
            "degraded": "🟡",
            "unhealthy": "🔴",
            "unknown": "⚪"
        }
        return colors.get(status, "⚪")
    
    def get_average_latency(self) -> float:
        """Get average latency across all recent checks."""
        if not self.health_history:
            return 0.0
        
        total_latency = 0
        count = 0
        
        for check in self.health_history:
            for status in check.values():
                if status.status == "healthy":
                    total_latency += status.latency_ms
                    count += 1
        
        return total_latency / count if count > 0 else 0.0
    
    def get_uptime_percentage(self, datasource: str) -> float:
        """
        Get uptime percentage for a specific datasource.
        
        Args:
            datasource: Name of the datasource
        
        Returns:
            Uptime percentage (0-100)
        """
        if not self.health_history:
            return 0.0
        
        healthy_count = sum(
            1 for check in self.health_history
            if datasource in check and check[datasource].status == "healthy"
        )
        
        total_count = len(self.health_history)
        
        return (healthy_count / total_count * 100) if total_count > 0 else 0.0

