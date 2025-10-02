"""Run Profile Manager for Ecosystem Optimization

This module provides a centralized run profile system that optimizes HTTP requests,
service discovery, and performance based on the detected environment.

Features:
- Environment-aware HTTP client configuration
- Optimized service discovery patterns
- Performance tuning based on run profile
- Automatic profile switching
- Profile validation and monitoring
"""

import os
import asyncio
import aiohttp
import time
from typing import Dict, Any, Optional, List, Callable
from contextlib import asynccontextmanager

from .environment_detector import (
    EnvironmentDetector,
    Environment,
    RunProfile,
    HTTPConfig,
    ServiceDiscoveryConfig,
    get_current_environment
)


class HTTPClientManager:
    """Environment-aware HTTP client manager."""

    def __init__(self):
        self.detector = EnvironmentDetector()
        self._clients: Dict[str, aiohttp.ClientSession] = {}
        self._client_configs: Dict[str, HTTPConfig] = {}

    def get_client_config(self, profile_name: str = 'default') -> HTTPConfig:
        """Get HTTP configuration for a profile."""
        if profile_name not in self._client_configs:
            profile = self.detector.detect_environment()
            self._client_configs[profile_name] = profile.http_config

        return self._client_configs[profile_name]

    def create_client_session(self, profile_name: str = 'default') -> aiohttp.ClientSession:
        """Create an optimized HTTP client session."""
        config = self.get_client_config(profile_name)

        connector = aiohttp.TCPConnector(
            limit=config.pool_connections,
            limit_per_host=config.pool_maxsize,
            ttl_dns_cache=30,
            use_dns_cache=True,
            keepalive_timeout=config.max_keepalive,
            enable_cleanup_closed=True,
            force_close=False
        )

        timeout = aiohttp.ClientTimeout(
            total=config.timeout,
            connect=config.timeout / 3,
            sock_read=config.timeout / 2
        )

        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': config.user_agent}
        )

        return session

    @asynccontextmanager
    async def get_client(self, profile_name: str = 'default'):
        """Context manager for HTTP client sessions."""
        session_key = f"{profile_name}_{id(asyncio.current_task())}"

        if session_key not in self._clients:
            self._clients[session_key] = self.create_client_session(profile_name)

        session = self._clients[session_key]

        try:
            yield session
        finally:
            # Clean up session after use
            if session_key in self._clients:
                await self._clients[session_key].close()
                del self._clients[session_key]

    async def make_request(self, method: str, url: str,
                          profile_name: str = 'default',
                          **kwargs) -> aiohttp.ClientResponse:
        """Make an HTTP request with optimized configuration."""
        config = self.get_client_config(profile_name)

        async with self.get_client(profile_name) as session:
            for attempt in range(config.retries + 1):
                try:
                    async with session.request(method, url, **kwargs) as response:
                        return response
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt == config.retries:
                        raise e
                    await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff


class ServiceDiscoveryManager:
    """Environment-aware service discovery manager."""

    def __init__(self):
        self.detector = EnvironmentDetector()
        self._service_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._health_checks: Dict[str, bool] = {}

    def get_discovery_config(self) -> ServiceDiscoveryConfig:
        """Get service discovery configuration."""
        profile = self.detector.detect_environment()
        return profile.discovery_config

    def get_service_url(self, service_name: str) -> Optional[str]:
        """Get service URL for current environment."""
        return self.detector.get_service_url(service_name)

    async def discover_services(self, service_names: List[str] = None) -> Dict[str, str]:
        """Discover available services."""
        profile = self.detector.detect_environment()
        config = profile.discovery_config

        discovered = {}

        if service_names is None:
            service_names = list(profile.service_mappings.keys())

        for service_name in service_names:
            url = profile.service_mappings.get(service_name)
            if url:
                discovered[service_name] = url

        return discovered

    async def check_service_health(self, service_name: str) -> bool:
        """Check if a service is healthy."""
        config = self.get_discovery_config()
        url = self.get_service_url(service_name)

        if not url or not config.use_health_checks:
            return True  # Assume healthy if no health checks

        cache_key = f"health_{service_name}"
        current_time = time.time()

        # Check cache
        if (cache_key in self._health_checks and
            current_time - self._cache_timestamps.get(cache_key, 0) < config.health_check_interval):
            return self._health_checks[cache_key]

        # Perform health check
        try:
            http_manager = HTTPClientManager()
            response = await http_manager.make_request('GET', f"{url}/health")
            healthy = response.status == 200
        except:
            healthy = False

        # Cache result
        self._health_checks[cache_key] = healthy
        self._cache_timestamps[cache_key] = current_time

        return healthy

    async def get_healthy_services(self, service_names: List[str] = None) -> Dict[str, str]:
        """Get only healthy services."""
        all_services = await self.discover_services(service_names)
        healthy_services = {}

        for name, url in all_services.items():
            if await self.check_service_health(name):
                healthy_services[name] = url

        return healthy_services


class RunProfileManager:
    """Central run profile manager for the ecosystem."""

    def __init__(self):
        self.detector = EnvironmentDetector()
        self.http_manager = HTTPClientManager()
        self.discovery_manager = ServiceDiscoveryManager()
        self._profile_hooks: List[Callable] = []

    def add_profile_hook(self, hook: Callable):
        """Add a hook that gets called when profile changes."""
        self._profile_hooks.append(hook)

    def get_current_profile(self) -> Dict[str, Any]:
        """Get current environment and run profile information."""
        profile = self.detector.detect_environment()

        return {
            'environment': profile.environment.value,
            'run_profile': profile.run_profile.value,
            'http_config': {
                'timeout': profile.http_config.timeout,
                'retries': profile.http_config.retries,
                'pool_connections': profile.http_config.pool_connections
            },
            'discovery_config': {
                'use_dns': profile.discovery_config.use_dns,
                'use_health_checks': profile.discovery_config.use_health_checks,
                'health_check_interval': profile.discovery_config.health_check_interval
            },
            'service_count': len(profile.service_mappings),
            'network_info': profile.network_info
        }

    async def make_service_request(self, service_name: str, endpoint: str,
                                  method: str = 'GET', **kwargs) -> aiohttp.ClientResponse:
        """Make a request to a service using optimized configuration."""
        url = self.discovery_manager.get_service_url(service_name)
        if not url:
            raise ValueError(f"Service {service_name} not found")

        full_url = f"{url}{endpoint}"
        return await self.http_manager.make_request(method, full_url, **kwargs)

    async def call_service_method(self, service_name: str, method_name: str,
                                 parameters: Dict[str, Any] = None) -> Any:
        """Call a service method with automatic discovery and optimization."""
        if parameters is None:
            parameters = {}

        # Construct endpoint
        endpoint = f"/api/v1/{method_name}"

        # Make request
        response = await self.make_service_request(
            service_name,
            endpoint,
            method='POST',
            json=parameters
        )

        if response.status == 200:
            return await response.json()
        else:
            error_text = await response.text()
            raise Exception(f"Service call failed: {response.status} - {error_text}")

    async def validate_ecosystem(self) -> Dict[str, Any]:
        """Validate the entire ecosystem configuration."""
        print("🔍 Validating Ecosystem Configuration")
        print("=" * 50)

        results = {
            'environment': {},
            'services': {},
            'connectivity': {},
            'performance': {},
            'recommendations': []
        }

        # Environment validation
        profile = self.detector.detect_environment()
        results['environment'] = {
            'type': profile.environment.value,
            'run_profile': profile.run_profile.value,
            'detected_services': len(profile.service_mappings)
        }

        print(f"📋 Environment: {profile.environment.value}")
        print(f"📋 Run Profile: {profile.run_profile.value}")

        # Service validation
        print("\n🔍 Checking Services...")
        healthy_services = await self.discovery_manager.get_healthy_services()
        all_services = await self.discovery_manager.discover_services()

        results['services'] = {
            'total': len(all_services),
            'healthy': len(healthy_services),
            'unhealthy': len(all_services) - len(healthy_services)
        }

        for name, url in all_services.items():
            is_healthy = name in healthy_services
            status = "✅" if is_healthy else "❌"
            print(f"   {status} {name}: {url}")

        # Connectivity validation
        print("\n🌐 Testing Connectivity...")
        connectivity_results = []
        for name, url in all_services.items():
            try:
                start_time = time.time()
                response = await self.http_manager.make_request('GET', f"{url}/health")
                response_time = time.time() - start_time
                connectivity_results.append({
                    'service': name,
                    'status': 'success',
                    'response_time': round(response_time, 3)
                })
                print(f"   ✅ {name}: {response_time:.3f}s")
            except Exception as e:
                connectivity_results.append({
                    'service': name,
                    'status': 'failed',
                    'error': str(e)
                })
                print(f"   ❌ {name}: Failed")

        results['connectivity'] = connectivity_results

        # Performance analysis
        response_times = [r['response_time'] for r in connectivity_results
                         if r['status'] == 'success' and 'response_time' in r]

        if response_times:
            results['performance'] = {
                'avg_response_time': round(sum(response_times) / len(response_times), 3),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'total_tests': len(connectivity_results)
            }

        # Generate recommendations
        if results['services']['healthy'] < results['services']['total']:
            results['recommendations'].append(
                f"Improve service health: {results['services']['healthy']}/{results['services']['total']} services healthy"
            )

        if results['performance'].get('avg_response_time', 0) > 1.0:
            results['recommendations'].append(
                f"Optimize response times: average {results['performance']['avg_response_time']}s"
            )

        # Summary
        print("\n📊 VALIDATION SUMMARY")
        print(f"🏥 Services: {results['services']['healthy']}/{results['services']['total']} healthy")

        if results['performance']:
            perf = results['performance']
            print(f"⚡ Performance: {perf['avg_response_time']}s avg")

        if results['recommendations']:
            print("\n💡 RECOMMENDATIONS:")
            for rec in results['recommendations']:
                print(f"   • {rec}")

        return results


# Global instance
profile_manager = RunProfileManager()


async def get_profile_manager() -> RunProfileManager:
    """Get the global profile manager instance."""
    return profile_manager


# Utility functions for easy access
async def call_service(service_name: str, method_name: str, parameters: Dict[str, Any] = None):
    """Convenience function to call a service method."""
    return await profile_manager.call_service_method(service_name, method_name, parameters)


async def get_service_url(service_name: str) -> Optional[str]:
    """Get service URL for current environment."""
    return profile_manager.discovery_manager.get_service_url(service_name)


if __name__ == '__main__':
    # Test the profile manager
    async def test_profile_manager():
        print("🧪 Run Profile Manager Test")
        print("=" * 40)

        # Get current profile
        profile = profile_manager.get_current_profile()
        print(f"Environment: {profile['environment']}")
        print(f"Run Profile: {profile['run_profile']}")
        print(f"Services: {profile['service_count']}")

        # Validate ecosystem
        validation = await profile_manager.validate_ecosystem()

        print("\n✅ Profile Manager Test Complete")
        return validation

    # Run test
    asyncio.run(test_profile_manager())
