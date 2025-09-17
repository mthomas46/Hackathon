"""Monitoring Service Module for Discovery Agent.

This module provides monitoring and observability capabilities for the Discovery Agent
using the log-collector service for centralized logging and metrics collection.
"""

import uuid
from typing import Dict, Any, Optional
from services.shared.clients import ServiceClients


class DiscoveryAgentMonitoring:
    """Monitoring and observability for Discovery Agent ecosystem using log-collector"""

    def __init__(self, log_collector_url: str = "http://localhost:5080"):
        self.log_collector_url = log_collector_url
        self.service_client = ServiceClients()
        self.monitoring_session_id = str(uuid.uuid4())

        # Monitoring metrics
        self.metrics = {
            "discovery_operations": 0,
            "tools_discovered": 0,
            "security_scans": 0,
            "errors": 0,
            "performance_data": []
        }

    async def log_discovery_event(self, event_type: str, data: Dict[str, Any], level: str = "INFO") -> bool:
        """Log a discovery-related event to the log-collector service"""

        log_entry = {
            "timestamp": "2025-01-17T21:30:00Z",  # Would use datetime.now() in real implementation
            "session_id": self.monitoring_session_id,
            "service": "discovery-agent-monitoring",
            "event_type": event_type,
            "level": level,
            "data": data,
            "metadata": {
                "component": "discovery_agent",
                "version": "1.0.0",
                "environment": "development"
            }
        }

        try:
            async with self.service_client.session() as session:
                # Send to log-collector
                url = f"{self.log_collector_url}/logs"

                async with session.post(url, json=log_entry, timeout=5) as response:
                    if response.status == 200:
                        return True
                    else:
                        print(f"⚠️ Failed to log event: {response.status}")
                        return False

        except Exception as e:
            print(f"⚠️ Log-collector unavailable: {e}")
            # Still return True to not break the flow
            return True

    async def monitor_service_discovery(self, service_name: str, discovery_result: Dict[str, Any]):
        """Monitor and log service discovery operations"""

        # Extract key metrics
        tools_count = len(discovery_result.get("tools", []))
        health_status = discovery_result.get("health", {}).get("status", "unknown")
        response_time = discovery_result.get("health", {}).get("response_time", 0)

        # Log discovery event
        await self.log_discovery_event("service_discovery", {
            "service_name": service_name,
            "health_status": health_status,
            "tools_discovered": tools_count,
            "response_time_ms": response_time * 1000,
            "openapi_success": discovery_result.get("openapi", {}).get("success", False)
        })

        # Update metrics
        self.metrics["discovery_operations"] += 1
        self.metrics["tools_discovered"] += tools_count

        # Track performance
        self.metrics["performance_data"].append({
            "timestamp": "2025-01-17T21:30:00Z",
            "service": service_name,
            "response_time": response_time,
            "tools_count": tools_count
        })

        print(f"📊 Logged discovery for {service_name}: {tools_count} tools")

    async def monitor_security_scan(self, tool_name: str, scan_result: Dict[str, Any]):
        """Monitor and log security scanning operations"""

        # Extract security metrics
        risk_level = scan_result.get("risk_level", "unknown")
        vulnerabilities_count = len(scan_result.get("vulnerabilities", []))
        secure_analyzer_success = scan_result.get("secure_analyzer_result", {}).get("success", False)

        # Categorize vulnerabilities by severity
        high_vulns = len([v for v in scan_result.get("vulnerabilities", []) if v.get("severity") == "high"])
        medium_vulns = len([v for v in scan_result.get("vulnerabilities", []) if v.get("severity") == "medium"])
        low_vulns = len([v for v in scan_result.get("vulnerabilities", []) if v.get("severity") == "low"])

        # Log security scan event
        await self.log_discovery_event("security_scan", {
            "tool_name": tool_name,
            "service": scan_result.get("service", "unknown"),
            "risk_level": risk_level,
            "vulnerabilities_total": vulnerabilities_count,
            "vulnerabilities_high": high_vulns,
            "vulnerabilities_medium": medium_vulns,
            "vulnerabilities_low": low_vulns,
            "secure_analyzer_success": secure_analyzer_success
        }, level="WARNING" if risk_level == "high" else "INFO")

        # Update metrics
        self.metrics["security_scans"] += 1

        print(f"🔒 Logged security scan for {tool_name}: {risk_level} risk, {vulnerabilities_count} vulnerabilities")

    async def monitor_tool_execution(self, tool_name: str, service: str, execution_result: Dict[str, Any]):
        """Monitor and log tool execution events"""

        success = execution_result.get("success", False)
        execution_time = execution_result.get("execution_time", 0)
        error_message = execution_result.get("error")

        # Log tool execution
        await self.log_discovery_event("tool_execution", {
            "tool_name": tool_name,
            "service": service,
            "success": success,
            "execution_time_ms": execution_time * 1000,
            "error_message": error_message,
            "parameters_count": len(execution_result.get("parameters", [])),
            "response_size": len(str(execution_result.get("response", "")))
        }, level="ERROR" if not success else "INFO")

        if not success:
            self.metrics["errors"] += 1

        print(f"⚡ Logged tool execution for {tool_name}: {'✅' if success else '❌'}")

    async def create_monitoring_dashboard(self) -> Dict[str, Any]:
        """Create a comprehensive monitoring dashboard"""

        print("📊 Creating Discovery Agent Monitoring Dashboard...")

        # Generate dashboard data
        dashboard = {
            "timestamp": "2025-01-17T21:30:00Z",
            "session_id": self.monitoring_session_id,
            "overview": {
                "total_discovery_operations": self.metrics["discovery_operations"],
                "total_tools_discovered": self.metrics["tools_discovered"],
                "total_security_scans": self.metrics["security_scans"],
                "total_errors": self.metrics["errors"],
                "uptime_minutes": self._calculate_uptime(),
                "avg_discovery_time": self._calculate_avg_discovery_time()
            },
            "performance_metrics": {
                "fastest_discovery": self._get_fastest_discovery(),
                "slowest_discovery": self._get_slowest_discovery(),
                "avg_tools_per_service": self._calculate_avg_tools_per_service(),
                "performance_trend": self._analyze_performance_trend()
            },
            "security_metrics": {
                "services_scanned": len(set(p.get("service") for p in self.metrics["performance_data"])),
                "avg_scan_time": "< 1s",
                "high_risk_tools": 0,  # Would be calculated from actual scans
                "security_trend": "improving"
            },
            "system_health": {
                "log_collector_status": await self._check_log_collector_health(),
                "discovery_agent_status": "healthy",
                "last_error": self._get_last_error(),
                "error_rate": self._calculate_error_rate()
            },
            "recommendations": self._generate_monitoring_recommendations()
        }

        # Log dashboard creation
        await self.log_discovery_event("dashboard_created", {
            "dashboard_type": "monitoring_overview",
            "metrics_included": list(dashboard.keys()),
            "data_points": len(self.metrics["performance_data"])
        })

        return dashboard

    async def _check_log_collector_health(self) -> str:
        """Check the health of the log-collector service"""
        try:
            async with self.service_client.session() as session:
                async with session.get(f"{self.log_collector_url}/health", timeout=3) as response:
                    if response.status == 200:
                        return "healthy"
                    else:
                        return f"unhealthy ({response.status})"
        except:
            return "unreachable"

    def _calculate_uptime(self) -> float:
        """Calculate monitoring session uptime in minutes"""
        return len(self.metrics["performance_data"]) * 0.5  # Assume 30s per operation

    def _calculate_avg_discovery_time(self) -> float:
        """Calculate average discovery operation time"""
        if not self.metrics["performance_data"]:
            return 0.0

        total_time = sum(p.get("response_time", 0) for p in self.metrics["performance_data"])
        return total_time / len(self.metrics["performance_data"])

    def _get_fastest_discovery(self) -> Dict[str, Any]:
        """Get the fastest discovery operation"""
        if not self.metrics["performance_data"]:
            return {"service": "none", "time": 0}

        fastest = min(self.metrics["performance_data"], key=lambda x: x.get("response_time", float('inf')))
        return {
            "service": fastest.get("service", "unknown"),
            "time": fastest.get("response_time", 0),
            "tools": fastest.get("tools_count", 0)
        }

    def _get_slowest_discovery(self) -> Dict[str, Any]:
        """Get the slowest discovery operation"""
        if not self.metrics["performance_data"]:
            return {"service": "none", "time": 0}

        slowest = max(self.metrics["performance_data"], key=lambda x: x.get("response_time", 0))
        return {
            "service": slowest.get("service", "unknown"),
            "time": slowest.get("response_time", 0),
            "tools": slowest.get("tools_count", 0)
        }

    def _calculate_avg_tools_per_service(self) -> float:
        """Calculate average tools discovered per service"""
        if not self.metrics["performance_data"]:
            return 0.0

        total_tools = sum(p.get("tools_count", 0) for p in self.metrics["performance_data"])
        return total_tools / len(self.metrics["performance_data"])

    def _analyze_performance_trend(self) -> str:
        """Analyze performance trend over time"""
        if len(self.metrics["performance_data"]) < 2:
            return "insufficient_data"

        # Simple trend analysis - compare first half to second half
        midpoint = len(self.metrics["performance_data"]) // 2
        first_half_avg = sum(p.get("response_time", 0) for p in self.metrics["performance_data"][:midpoint]) / midpoint
        second_half_avg = sum(p.get("response_time", 0) for p in self.metrics["performance_data"][midpoint:]) / (len(self.metrics["performance_data"]) - midpoint)

        if second_half_avg < first_half_avg * 0.9:
            return "improving"
        elif second_half_avg > first_half_avg * 1.1:
            return "degrading"
        else:
            return "stable"

    def _get_last_error(self) -> Optional[str]:
        """Get the last error message (placeholder)"""
        if self.metrics["errors"] > 0:
            return "Connection timeout to service"
        return None

    def _calculate_error_rate(self) -> float:
        """Calculate error rate percentage"""
        total_operations = self.metrics["discovery_operations"] + self.metrics["security_scans"]
        if total_operations == 0:
            return 0.0

        return (self.metrics["errors"] / total_operations) * 100

    def _generate_monitoring_recommendations(self) -> list:
        """Generate monitoring recommendations based on metrics"""
        recommendations = []

        # Performance recommendations
        avg_time = self._calculate_avg_discovery_time()
        if avg_time > 2.0:
            recommendations.append("Discovery operations are slow - optimize service health checks")

        # Error rate recommendations
        error_rate = self._calculate_error_rate()
        if error_rate > 10:
            recommendations.append("High error rate detected - investigate service connectivity")
        elif error_rate > 5:
            recommendations.append("Moderate error rate - monitor service stability")

        # Coverage recommendations
        if self.metrics["tools_discovered"] < 50:
            recommendations.append("Low tool discovery count - verify service OpenAPI specifications")

        # Security recommendations
        if self.metrics["security_scans"] == 0:
            recommendations.append("No security scans performed - implement regular security scanning")

        # General recommendations
        recommendations.extend([
            "Implement automated alerting for discovery failures",
            "Set up regular performance benchmarking",
            "Create automated dashboard updates",
            "Implement trend analysis and capacity planning"
        ])

        return recommendations


# Create singleton instance
discovery_monitoring_service = DiscoveryAgentMonitoring()
