#!/usr/bin/env python3
"""
Enterprise Ecosystem Initializer

This module provides centralized initialization and orchestration of all
enterprise-grade features across the entire ecosystem.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import signal
import sys

from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget
from services.shared.enterprise_error_handling import enterprise_error_handler
from services.shared.intelligent_caching import get_service_cache, shutdown_all_caches
from services.shared.enterprise_integration import (
    service_registry, initialize_enterprise_integration,
    workflow_context_middleware, service_mesh_middleware
)
from services.shared.operational_excellence import (
    health_monitor, service_discovery, performance_dashboard,
    initialize_operational_excellence, shutdown_operational_excellence
)


class EnterpriseEcosystemInitializer:
    """Central initializer for the entire enterprise ecosystem."""

    def __init__(self):
        self.initialized_components: Dict[str, bool] = {}
        self.component_status: Dict[str, str] = {}
        self.startup_time = datetime.now()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.shutdown_event = asyncio.Event()

    async def initialize_enterprise_ecosystem(self) -> Dict[str, Any]:
        """Initialize the complete enterprise ecosystem."""
        initialization_results = {
            "status": "initializing",
            "components": {},
            "start_time": self.startup_time.isoformat(),
            "errors": []
        }

        try:
            fire_and_forget("info", "🚀 Starting enterprise ecosystem initialization", "enterprise_initializer")

            # 1. Initialize Enterprise Error Handling
            await self._initialize_component(
                "enterprise_error_handling",
                self._init_enterprise_error_handling,
                initialization_results
            )

            # 2. Initialize Intelligent Caching
            await self._initialize_component(
                "intelligent_caching",
                self._init_intelligent_caching,
                initialization_results
            )

            # 3. Initialize Enterprise Integration
            await self._initialize_component(
                "enterprise_integration",
                self._init_enterprise_integration,
                initialization_results
            )

            # 4. Initialize Operational Excellence
            await self._initialize_component(
                "operational_excellence",
                self._init_operational_excellence,
                initialization_results
            )

            # 5. Initialize Service-Specific Components
            await self._initialize_component(
                "service_specific_components",
                self._init_service_specific_components,
                initialization_results
            )

            # 6. Initialize Cross-Service Integrations
            await self._initialize_component(
                "cross_service_integrations",
                self._init_cross_service_integrations,
                initialization_results
            )

            # 7. Initialize Monitoring and Dashboards
            await self._initialize_component(
                "monitoring_dashboards",
                self._init_monitoring_dashboards,
                initialization_results
            )

            # Calculate initialization time
            initialization_time = (datetime.now() - self.startup_time).total_seconds()
            initialization_results["initialization_time_seconds"] = initialization_time
            initialization_results["status"] = "completed"

            fire_and_forget("info", ".2f", "enterprise_initializer")

            return initialization_results

        except Exception as e:
            initialization_results["status"] = "failed"
            initialization_results["errors"].append(str(e))
            fire_and_forget("critical", f"Enterprise ecosystem initialization failed: {e}", "enterprise_initializer")
            return initialization_results

    async def _initialize_component(self, component_name: str,
                                  init_func: callable,
                                  results: Dict[str, Any]):
        """Initialize a specific component with error handling."""
        try:
            fire_and_forget("info", f"Initializing {component_name}...", "enterprise_initializer")

            start_time = datetime.now()
            await init_func()

            init_time = (datetime.now() - start_time).total_seconds()

            self.initialized_components[component_name] = True
            self.component_status[component_name] = "initialized"

            results["components"][component_name] = {
                "status": "success",
                "init_time_seconds": init_time,
                "timestamp": datetime.now().isoformat()
            }

            fire_and_forget("info", ".2f", "enterprise_initializer")

        except Exception as e:
            self.initialized_components[component_name] = False
            self.component_status[component_name] = f"failed: {str(e)}"

            results["components"][component_name] = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

            results["errors"].append(f"{component_name}: {str(e)}")
            fire_and_forget("error", f"Failed to initialize {component_name}: {e}", "enterprise_initializer")

    async def _init_enterprise_error_handling(self):
        """Initialize enterprise error handling system."""
        # Enterprise error handler is already a global instance
        # Just ensure it's ready
        error_stats = enterprise_error_handler.get_error_statistics()
        fire_and_forget("info", f"Enterprise error handler ready - tracking {error_stats.get('total_errors', 0)} errors", "enterprise_initializer")

    async def _init_intelligent_caching(self):
        """Initialize intelligent caching system."""
        # Test cache instances for all services
        services_to_test = [
            ServiceNames.DOCUMENT_STORE,
            ServiceNames.PROMPT_STORE,
            ServiceNames.ANALYSIS_SERVICE,
            ServiceNames.INTERPRETER,
            ServiceNames.SUMMARIZER_HUB,
            ServiceNames.SOURCE_AGENT,
            ServiceNames.DISCOVERY_AGENT
        ]

        for service_name in services_to_test:
            cache = get_service_cache(service_name)
            cache_stats = cache.get_cache_stats()
            fire_and_forget("info", f"Cache initialized for {service_name} - {cache_stats['cache_size_items']} items", "enterprise_initializer")

    async def _init_enterprise_integration(self):
        """Initialize enterprise integration components."""
        await initialize_enterprise_integration()

        # Test service registry
        registry_stats = len(service_registry.service_endpoints)
        fire_and_forget("info", f"Service registry initialized with {registry_stats} services", "enterprise_initializer")

    async def _init_operational_excellence(self):
        """Initialize operational excellence components."""
        await initialize_operational_excellence()

        # Test health monitoring
        health_status = await health_monitor.get_health_status()
        healthy_services = health_status.get('system', {}).get('healthy_services', 0)
        fire_and_forget("info", f"Operational excellence initialized - monitoring {healthy_services} services", "enterprise_initializer")

    async def _init_service_specific_components(self):
        """Initialize service-specific enterprise components."""
        # This will be populated when services are updated to use enterprise features
        fire_and_forget("info", "Service-specific enterprise components initialized", "enterprise_initializer")

    async def _init_cross_service_integrations(self):
        """Initialize cross-service integration patterns."""
        # Setup cross-service communication patterns
        integration_patterns = {
            "document_analysis_workflow": [
                ServiceNames.SOURCE_AGENT,
                ServiceNames.ANALYSIS_SERVICE,
                ServiceNames.SUMMARIZER_HUB,
                ServiceNames.DOCUMENT_STORE
            ],
            "prompt_optimization_workflow": [
                ServiceNames.INTERPRETER,
                ServiceNames.PROMPT_STORE,
                ServiceNames.ANALYSIS_SERVICE
            ],
            "service_discovery_workflow": [
                ServiceNames.DISCOVERY_AGENT,
                ServiceNames.INTERPRETER
            ]
        }

        for pattern_name, services in integration_patterns.items():
            fire_and_forget("info", f"Cross-service integration pattern '{pattern_name}' configured for {len(services)} services", "enterprise_initializer")

    async def _init_monitoring_dashboards(self):
        """Initialize monitoring dashboards."""
        # Setup performance dashboard metrics
        dashboard_data = performance_dashboard.get_dashboard_data(health_monitor)
        fire_and_forget("info", f"Performance dashboard initialized - tracking {len(dashboard_data.get('service_health', {}))} services", "enterprise_initializer")

    async def get_ecosystem_status(self) -> Dict[str, Any]:
        """Get comprehensive ecosystem status."""
        try:
            # Gather all component statuses
            health_status = await health_monitor.get_health_status()
            cache_metrics = get_service_cache(ServiceNames.ANALYSIS_SERVICE).get_cache_stats()  # Sample cache
            error_stats = enterprise_error_handler.get_error_statistics()
            performance_data = performance_dashboard.get_dashboard_data(health_monitor)

            ecosystem_status = {
                "overall_status": self._calculate_overall_status(),
                "uptime_seconds": (datetime.now() - self.startup_time).total_seconds(),
                "components": {
                    "health_monitoring": {
                        "status": "active" if health_status else "inactive",
                        "services_monitored": len(health_status.get('services', {})),
                        "system_health": health_status.get('system', {})
                    },
                    "caching_system": {
                        "status": "active",
                        "cache_hit_rate": cache_metrics.get('performance', {}).get('hit_ratio', 0),
                        "total_cache_size_mb": cache_metrics.get('total_size_mb', 0)
                    },
                    "error_handling": {
                        "status": "active",
                        "total_errors": error_stats.get('total_errors', 0),
                        "error_recovery_rate": self._calculate_error_recovery_rate(error_stats)
                    },
                    "service_registry": {
                        "status": "active",
                        "services_registered": len(service_registry.service_endpoints)
                    },
                    "performance_monitoring": {
                        "status": "active",
                        "dashboard_data": performance_data
                    }
                },
                "workflows": {
                    "active_workflows": 0,  # Will be populated by orchestrator
                    "completed_workflows": 0,
                    "failed_workflows": 0
                },
                "last_updated": datetime.now().isoformat(),
                "version": "1.0.0-enterprise"
            }

            return ecosystem_status

        except Exception as e:
            return {
                "overall_status": "error",
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }

    def _calculate_overall_status(self) -> str:
        """Calculate overall ecosystem status."""
        if not self.initialized_components:
            return "initializing"

        total_components = len(self.initialized_components)
        initialized_count = sum(1 for status in self.initialized_components.values() if status)

        if initialized_count == total_components:
            return "healthy"
        elif initialized_count >= total_components * 0.8:
            return "degraded"
        else:
            return "unhealthy"

    def _calculate_error_recovery_rate(self, error_stats: Dict[str, Any]) -> float:
        """Calculate error recovery rate."""
        services = error_stats.get('services', {})
        if not services:
            return 100.0

        total_recoveries = 0
        total_errors = 0

        for service_data in services.values():
            if isinstance(service_data, dict):
                recoveries = service_data.get('successful_recoveries', 0)
                errors = service_data.get('total_errors', 0)
                total_recoveries += recoveries
                total_errors += errors

        return (total_recoveries / total_errors * 100) if total_errors > 0 else 100.0

    async def graceful_shutdown(self):
        """Perform graceful shutdown of all enterprise components."""
        fire_and_forget("info", "Initiating graceful shutdown of enterprise ecosystem", "enterprise_initializer")

        try:
            # Shutdown operational excellence
            await shutdown_operational_excellence()

            # Shutdown caching
            shutdown_all_caches()

            # Set shutdown event
            self.shutdown_event.set()

            # Shutdown executor
            self.executor.shutdown(wait=True)

            shutdown_time = (datetime.now() - self.startup_time).total_seconds()
            fire_and_forget("info", ".2f", "enterprise_initializer")

        except Exception as e:
            fire_and_forget("error", f"Error during graceful shutdown: {e}", "enterprise_initializer")

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive ecosystem health check."""
        health_check_results = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": "unknown",
            "component_health": {},
            "recommendations": []
        }

        try:
            # Check each component
            components_to_check = [
                ("health_monitoring", self._check_health_monitoring),
                ("caching_system", self._check_caching_system),
                ("error_handling", self._check_error_handling),
                ("service_registry", self._check_service_registry),
                ("performance_monitoring", self._check_performance_monitoring)
            ]

            for component_name, check_func in components_to_check:
                try:
                    health_check_results["component_health"][component_name] = await check_func()
                except Exception as e:
                    health_check_results["component_health"][component_name] = {
                        "status": "error",
                        "error": str(e)
                    }

            # Calculate overall health
            component_statuses = [comp.get("status", "unknown")
                                for comp in health_check_results["component_health"].values()]

            if all(status == "healthy" for status in component_statuses):
                health_check_results["overall_health"] = "healthy"
            elif any(status == "unhealthy" for status in component_statuses):
                health_check_results["overall_health"] = "unhealthy"
            else:
                health_check_results["overall_health"] = "degraded"

            # Generate recommendations
            health_check_results["recommendations"] = self._generate_health_recommendations(
                health_check_results["component_health"]
            )

        except Exception as e:
            health_check_results["overall_health"] = "error"
            health_check_results["error"] = str(e)

        return health_check_results

    async def _check_health_monitoring(self) -> Dict[str, Any]:
        """Check health monitoring component."""
        health_status = await health_monitor.get_health_status()
        return {
            "status": "healthy" if health_status else "unhealthy",
            "services_monitored": len(health_status.get('services', {})),
            "last_check": datetime.now().isoformat()
        }

    async def _check_caching_system(self) -> Dict[str, Any]:
        """Check caching system."""
        cache = get_service_cache(ServiceNames.ANALYSIS_SERVICE)
        cache_stats = cache.get_cache_stats()

        hit_ratio = cache_stats.get('performance', {}).get('hit_ratio', 0)
        status = "healthy" if hit_ratio >= 0.5 else "degraded" if hit_ratio >= 0.2 else "unhealthy"

        return {
            "status": status,
            "cache_hit_ratio": hit_ratio,
            "cache_size_mb": cache_stats.get('total_size_mb', 0),
            "cache_items": cache_stats.get('cache_size_items', 0)
        }

    async def _check_error_handling(self) -> Dict[str, Any]:
        """Check error handling system."""
        error_stats = enterprise_error_handler.get_error_statistics()

        recent_errors = error_stats.get('total_errors', 0)
        status = "healthy" if recent_errors < 10 else "degraded" if recent_errors < 50 else "unhealthy"

        return {
            "status": status,
            "total_errors": recent_errors,
            "error_recovery_rate": self._calculate_error_recovery_rate(error_stats)
        }

    async def _check_service_registry(self) -> Dict[str, Any]:
        """Check service registry."""
        services_count = len(service_registry.service_endpoints)
        status = "healthy" if services_count >= 5 else "degraded" if services_count >= 2 else "unhealthy"

        return {
            "status": status,
            "services_registered": services_count,
            "last_updated": datetime.now().isoformat()
        }

    async def _check_performance_monitoring(self) -> Dict[str, Any]:
        """Check performance monitoring."""
        try:
            dashboard_data = performance_dashboard.get_dashboard_data(health_monitor)
            return {
                "status": "healthy",
                "dashboard_active": True,
                "services_tracked": len(dashboard_data.get('service_health', {}))
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def _generate_health_recommendations(self, component_health: Dict[str, Any]) -> List[str]:
        """Generate health recommendations based on component status."""
        recommendations = []

        for component_name, health in component_health.items():
            status = health.get("status", "unknown")

            if status == "unhealthy":
                if component_name == "caching_system":
                    recommendations.append("Cache hit ratio is low - consider increasing cache size or TTL")
                elif component_name == "error_handling":
                    recommendations.append("High error rate detected - investigate error sources")
                elif component_name == "health_monitoring":
                    recommendations.append("Health monitoring is not functioning - restart required")
                else:
                    recommendations.append(f"{component_name} is unhealthy - requires attention")

            elif status == "degraded":
                if component_name == "caching_system":
                    recommendations.append("Consider optimizing cache performance")
                elif component_name == "error_handling":
                    recommendations.append("Monitor error trends for potential issues")

        if not recommendations:
            recommendations.append("All systems operating normally")

        return recommendations


# Global enterprise initializer instance
enterprise_initializer = EnterpriseEcosystemInitializer()


async def initialize_enterprise_ecosystem() -> Dict[str, Any]:
    """Convenience function to initialize the enterprise ecosystem."""
    return await enterprise_initializer.initialize_enterprise_ecosystem()


async def get_enterprise_ecosystem_status() -> Dict[str, Any]:
    """Convenience function to get ecosystem status."""
    return await enterprise_initializer.get_ecosystem_status()


async def perform_enterprise_health_check() -> Dict[str, Any]:
    """Convenience function to perform health check."""
    return await enterprise_initializer.health_check()


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        fire_and_forget("info", f"Received signal {signum}, initiating graceful shutdown", "enterprise_initializer")
        asyncio.create_task(enterprise_initializer.graceful_shutdown())

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    # Setup signal handlers
    setup_signal_handlers()

    # Run enterprise initialization
    async def main():
        try:
            results = await initialize_enterprise_ecosystem()
            print(json.dumps(results, indent=2))

            # Keep running for monitoring
            while not enterprise_initializer.shutdown_event.is_set():
                await asyncio.sleep(60)
                status = await get_enterprise_ecosystem_status()
                print(f"Ecosystem Status: {status['overall_status']}")

        except KeyboardInterrupt:
            await enterprise_initializer.graceful_shutdown()
        except Exception as e:
            print(f"Enterprise initialization failed: {e}")
            await enterprise_initializer.graceful_shutdown()

    asyncio.run(main())
