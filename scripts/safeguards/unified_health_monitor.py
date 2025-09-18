#!/usr/bin/env python3
"""
Unified Health Monitoring System
Standardized health checks with multiple validation methods
"""

import urllib.request
import urllib.error
import subprocess
import socket
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import redis


class HealthStatus(Enum):
    """Standardized health status values"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNREACHABLE = "unreachable"
    UNKNOWN = "unknown"


class HealthCheckMethod(Enum):
    """Types of health check methods"""
    HTTP_ENDPOINT = "http_endpoint"
    DOCKER_HEALTH = "docker_health"
    TCP_CONNECTION = "tcp_connection"
    REDIS_PING = "redis_ping"
    OLLAMA_API = "ollama_api"
    PROCESS_CHECK = "process_check"


@dataclass
class HealthCheckConfig:
    """Configuration for a service health check"""
    service_name: str
    primary_method: HealthCheckMethod
    fallback_methods: List[HealthCheckMethod]
    host_port: int
    docker_port: Optional[int] = None
    container_name: Optional[str] = None
    health_endpoint: str = "/health"
    timeout: int = 10
    expected_response_keys: List[str] = None


@dataclass
class HealthResult:
    """Result of a health check"""
    service_name: str
    status: HealthStatus
    method_used: HealthCheckMethod
    response_time_ms: float
    details: Dict[str, Any]
    error_message: Optional[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class UnifiedHealthMonitor:
    """Centralized health monitoring with multiple validation methods"""
    
    def __init__(self):
        self.service_configs = self._load_service_configs()
        self.health_history = {}
        
    def _load_service_configs(self) -> Dict[str, HealthCheckConfig]:
        """Load health check configurations for all services"""
        return {
            "redis": HealthCheckConfig(
                service_name="redis",
                primary_method=HealthCheckMethod.REDIS_PING,
                fallback_methods=[HealthCheckMethod.TCP_CONNECTION],
                host_port=6379,
                container_name="hackathon-redis-1"
            ),
            "doc_store": HealthCheckConfig(
                service_name="doc_store",
                primary_method=HealthCheckMethod.HTTP_ENDPOINT,
                fallback_methods=[HealthCheckMethod.DOCKER_HEALTH, HealthCheckMethod.TCP_CONNECTION],
                host_port=5087,
                docker_port=5010,
                container_name="hackathon-doc_store-1",
                expected_response_keys=["status", "service", "version"]
            ),
            "orchestrator": HealthCheckConfig(
                service_name="orchestrator",
                primary_method=HealthCheckMethod.HTTP_ENDPOINT,
                fallback_methods=[HealthCheckMethod.DOCKER_HEALTH],
                host_port=5099,
                container_name="hackathon-orchestrator-1",
                expected_response_keys=["status", "service"]
            ),
            "llm-gateway": HealthCheckConfig(
                service_name="llm-gateway",
                primary_method=HealthCheckMethod.HTTP_ENDPOINT,
                fallback_methods=[HealthCheckMethod.DOCKER_HEALTH],
                host_port=5055,
                container_name="hackathon-llm-gateway-1"
            ),
            "analysis-service": HealthCheckConfig(
                service_name="analysis-service",
                primary_method=HealthCheckMethod.HTTP_ENDPOINT,
                fallback_methods=[HealthCheckMethod.DOCKER_HEALTH],
                host_port=5080,
                docker_port=5020,
                container_name="hackathon-analysis-service-1"
            ),
            "discovery-agent": HealthCheckConfig(
                service_name="discovery-agent",
                primary_method=HealthCheckMethod.HTTP_ENDPOINT,
                fallback_methods=[HealthCheckMethod.DOCKER_HEALTH],
                host_port=5045,
                container_name="hackathon-discovery-agent-1"
            ),
            "frontend": HealthCheckConfig(
                service_name="frontend",
                primary_method=HealthCheckMethod.DOCKER_HEALTH,
                fallback_methods=[HealthCheckMethod.TCP_CONNECTION],
                host_port=3000,
                container_name="hackathon-frontend-1",
                health_endpoint="/"
            ),
            "ollama": HealthCheckConfig(
                service_name="ollama",
                primary_method=HealthCheckMethod.OLLAMA_API,
                fallback_methods=[HealthCheckMethod.TCP_CONNECTION],
                host_port=11434,
                container_name="hackathon-ollama-1",
                health_endpoint="/api/tags"
            ),
            "notification-service": HealthCheckConfig(
                service_name="notification-service",
                primary_method=HealthCheckMethod.HTTP_ENDPOINT,
                fallback_methods=[HealthCheckMethod.DOCKER_HEALTH],
                host_port=5130,
                container_name="hackathon-notification-service-1"
            ),
            "code-analyzer": HealthCheckConfig(
                service_name="code-analyzer",
                primary_method=HealthCheckMethod.HTTP_ENDPOINT,
                fallback_methods=[HealthCheckMethod.DOCKER_HEALTH],
                host_port=5025,
                container_name="hackathon-code-analyzer-1"
            ),
            "source-agent": HealthCheckConfig(
                service_name="source-agent",
                primary_method=HealthCheckMethod.HTTP_ENDPOINT,
                fallback_methods=[HealthCheckMethod.DOCKER_HEALTH],
                host_port=5085,
                container_name="hackathon-source-agent-1"
            )
        }
    
    def check_service_health(self, service_name: str) -> HealthResult:
        """Perform comprehensive health check for a service"""
        if service_name not in self.service_configs:
            return HealthResult(
                service_name=service_name,
                status=HealthStatus.UNKNOWN,
                method_used=HealthCheckMethod.HTTP_ENDPOINT,
                response_time_ms=0,
                details={},
                error_message=f"No configuration found for service: {service_name}"
            )
        
        config = self.service_configs[service_name]
        start_time = time.time()
        
        # Try primary method first
        result = self._execute_health_check(config, config.primary_method)
        if result.status == HealthStatus.HEALTHY:
            return result
        
        # Try fallback methods
        for fallback_method in config.fallback_methods:
            fallback_result = self._execute_health_check(config, fallback_method)
            if fallback_result.status == HealthStatus.HEALTHY:
                return fallback_result
        
        # All methods failed, return the primary method result
        return result
    
    def _execute_health_check(self, config: HealthCheckConfig, 
                             method: HealthCheckMethod) -> HealthResult:
        """Execute a specific health check method"""
        start_time = time.time()
        
        try:
            if method == HealthCheckMethod.HTTP_ENDPOINT:
                return self._check_http_endpoint(config, start_time)
            elif method == HealthCheckMethod.DOCKER_HEALTH:
                return self._check_docker_health(config, start_time)
            elif method == HealthCheckMethod.TCP_CONNECTION:
                return self._check_tcp_connection(config, start_time)
            elif method == HealthCheckMethod.REDIS_PING:
                return self._check_redis_ping(config, start_time)
            elif method == HealthCheckMethod.OLLAMA_API:
                return self._check_ollama_api(config, start_time)
            else:
                return HealthResult(
                    service_name=config.service_name,
                    status=HealthStatus.UNKNOWN,
                    method_used=method,
                    response_time_ms=(time.time() - start_time) * 1000,
                    details={},
                    error_message=f"Unsupported health check method: {method}"
                )
        except Exception as e:
            return HealthResult(
                service_name=config.service_name,
                status=HealthStatus.UNREACHABLE,
                method_used=method,
                response_time_ms=(time.time() - start_time) * 1000,
                details={},
                error_message=str(e)
            )
    
    def _check_http_endpoint(self, config: HealthCheckConfig, start_time: float) -> HealthResult:
        """Check HTTP health endpoint"""
        url = f"http://localhost:{config.host_port}{config.health_endpoint}"
        
        try:
            with urllib.request.urlopen(url, timeout=config.timeout) as response:
                response_time = (time.time() - start_time) * 1000
                
                if response.getcode() == 200:
                    content = response.read().decode('utf-8')
                    details = {"url": url, "response_preview": content[:200]}
                    
                    # Try to parse JSON and validate expected keys
                    try:
                        json_data = json.loads(content)
                        details["response_data"] = json_data
                        
                        if config.expected_response_keys:
                            missing_keys = [key for key in config.expected_response_keys 
                                          if key not in json_data]
                            if missing_keys:
                                details["missing_keys"] = missing_keys
                                return HealthResult(
                                    service_name=config.service_name,
                                    status=HealthStatus.DEGRADED,
                                    method_used=HealthCheckMethod.HTTP_ENDPOINT,
                                    response_time_ms=response_time,
                                    details=details,
                                    error_message=f"Missing expected keys: {missing_keys}"
                                )
                    except json.JSONDecodeError:
                        details["response_type"] = "non_json"
                    
                    return HealthResult(
                        service_name=config.service_name,
                        status=HealthStatus.HEALTHY,
                        method_used=HealthCheckMethod.HTTP_ENDPOINT,
                        response_time_ms=response_time,
                        details=details
                    )
                else:
                    return HealthResult(
                        service_name=config.service_name,
                        status=HealthStatus.UNHEALTHY,
                        method_used=HealthCheckMethod.HTTP_ENDPOINT,
                        response_time_ms=response_time,
                        details={"url": url},
                        error_message=f"HTTP {response.getcode()}"
                    )
        except urllib.error.URLError as e:
            return HealthResult(
                service_name=config.service_name,
                status=HealthStatus.UNREACHABLE,
                method_used=HealthCheckMethod.HTTP_ENDPOINT,
                response_time_ms=(time.time() - start_time) * 1000,
                details={"url": url},
                error_message=str(e)
            )
    
    def _check_docker_health(self, config: HealthCheckConfig, start_time: float) -> HealthResult:
        """Check Docker container health status"""
        if not config.container_name:
            return HealthResult(
                service_name=config.service_name,
                status=HealthStatus.UNKNOWN,
                method_used=HealthCheckMethod.DOCKER_HEALTH,
                response_time_ms=(time.time() - start_time) * 1000,
                details={},
                error_message="No container name configured"
            )
        
        try:
            result = subprocess.run(
                ["docker", "inspect", config.container_name, "--format", "{{.State.Health.Status}}"],
                capture_output=True,
                text=True,
                timeout=config.timeout
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if result.returncode == 0:
                docker_status = result.stdout.strip()
                
                if docker_status == "healthy":
                    status = HealthStatus.HEALTHY
                elif docker_status == "unhealthy":
                    status = HealthStatus.UNHEALTHY
                elif docker_status == "starting":
                    status = HealthStatus.DEGRADED
                else:
                    status = HealthStatus.UNKNOWN
                
                return HealthResult(
                    service_name=config.service_name,
                    status=status,
                    method_used=HealthCheckMethod.DOCKER_HEALTH,
                    response_time_ms=response_time,
                    details={"docker_status": docker_status, "container": config.container_name}
                )
            else:
                return HealthResult(
                    service_name=config.service_name,
                    status=HealthStatus.UNREACHABLE,
                    method_used=HealthCheckMethod.DOCKER_HEALTH,
                    response_time_ms=response_time,
                    details={"container": config.container_name},
                    error_message=result.stderr.strip()
                )
        except subprocess.TimeoutExpired:
            return HealthResult(
                service_name=config.service_name,
                status=HealthStatus.UNREACHABLE,
                method_used=HealthCheckMethod.DOCKER_HEALTH,
                response_time_ms=(time.time() - start_time) * 1000,
                details={},
                error_message="Docker command timeout"
            )
    
    def _check_tcp_connection(self, config: HealthCheckConfig, start_time: float) -> HealthResult:
        """Check TCP connection to service port"""
        try:
            with socket.create_connection(("localhost", config.host_port), timeout=config.timeout):
                response_time = (time.time() - start_time) * 1000
                return HealthResult(
                    service_name=config.service_name,
                    status=HealthStatus.HEALTHY,
                    method_used=HealthCheckMethod.TCP_CONNECTION,
                    response_time_ms=response_time,
                    details={"port": config.host_port}
                )
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            return HealthResult(
                service_name=config.service_name,
                status=HealthStatus.UNREACHABLE,
                method_used=HealthCheckMethod.TCP_CONNECTION,
                response_time_ms=(time.time() - start_time) * 1000,
                details={"port": config.host_port},
                error_message=str(e)
            )
    
    def _check_redis_ping(self, config: HealthCheckConfig, start_time: float) -> HealthResult:
        """Check Redis with PING command"""
        try:
            r = redis.Redis(host='localhost', port=config.host_port, 
                          decode_responses=True, socket_timeout=config.timeout)
            ping_result = r.ping()
            response_time = (time.time() - start_time) * 1000
            
            if ping_result:
                return HealthResult(
                    service_name=config.service_name,
                    status=HealthStatus.HEALTHY,
                    method_used=HealthCheckMethod.REDIS_PING,
                    response_time_ms=response_time,
                    details={"ping_result": "PONG", "port": config.host_port}
                )
            else:
                return HealthResult(
                    service_name=config.service_name,
                    status=HealthStatus.UNHEALTHY,
                    method_used=HealthCheckMethod.REDIS_PING,
                    response_time_ms=response_time,
                    details={"port": config.host_port},
                    error_message="Redis PING failed"
                )
        except Exception as e:
            return HealthResult(
                service_name=config.service_name,
                status=HealthStatus.UNREACHABLE,
                method_used=HealthCheckMethod.REDIS_PING,
                response_time_ms=(time.time() - start_time) * 1000,
                details={"port": config.host_port},
                error_message=str(e)
            )
    
    def _check_ollama_api(self, config: HealthCheckConfig, start_time: float) -> HealthResult:
        """Check Ollama API endpoint"""
        url = f"http://localhost:{config.host_port}{config.health_endpoint}"
        
        try:
            with urllib.request.urlopen(url, timeout=config.timeout) as response:
                response_time = (time.time() - start_time) * 1000
                
                if response.getcode() == 200:
                    content = response.read().decode('utf-8')
                    
                    try:
                        json_data = json.loads(content)
                        models_count = len(json_data.get('models', []))
                        
                        return HealthResult(
                            service_name=config.service_name,
                            status=HealthStatus.HEALTHY,
                            method_used=HealthCheckMethod.OLLAMA_API,
                            response_time_ms=response_time,
                            details={"models_available": models_count, "url": url}
                        )
                    except json.JSONDecodeError:
                        return HealthResult(
                            service_name=config.service_name,
                            status=HealthStatus.DEGRADED,
                            method_used=HealthCheckMethod.OLLAMA_API,
                            response_time_ms=response_time,
                            details={"url": url},
                            error_message="Invalid JSON response"
                        )
                else:
                    return HealthResult(
                        service_name=config.service_name,
                        status=HealthStatus.UNHEALTHY,
                        method_used=HealthCheckMethod.OLLAMA_API,
                        response_time_ms=response_time,
                        details={"url": url},
                        error_message=f"HTTP {response.getcode()}"
                    )
        except Exception as e:
            return HealthResult(
                service_name=config.service_name,
                status=HealthStatus.UNREACHABLE,
                method_used=HealthCheckMethod.OLLAMA_API,
                response_time_ms=(time.time() - start_time) * 1000,
                details={"url": url},
                error_message=str(e)
            )
    
    def check_all_services(self, parallel: bool = True) -> Dict[str, HealthResult]:
        """Check health of all configured services"""
        if parallel:
            return self._check_all_parallel()
        else:
            return self._check_all_sequential()
    
    def _check_all_parallel(self) -> Dict[str, HealthResult]:
        """Check all services in parallel for faster execution"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_service = {
                executor.submit(self.check_service_health, service_name): service_name 
                for service_name in self.service_configs.keys()
            }
            
            for future in as_completed(future_to_service):
                service_name = future_to_service[future]
                try:
                    result = future.result()
                    results[service_name] = result
                except Exception as e:
                    results[service_name] = HealthResult(
                        service_name=service_name,
                        status=HealthStatus.UNKNOWN,
                        method_used=HealthCheckMethod.HTTP_ENDPOINT,
                        response_time_ms=0,
                        details={},
                        error_message=f"Health check exception: {str(e)}"
                    )
        
        return results
    
    def _check_all_sequential(self) -> Dict[str, HealthResult]:
        """Check all services sequentially"""
        results = {}
        for service_name in self.service_configs.keys():
            results[service_name] = self.check_service_health(service_name)
        return results
    
    def generate_health_report(self, results: Dict[str, HealthResult]) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        total_services = len(results)
        healthy_services = sum(1 for r in results.values() if r.status == HealthStatus.HEALTHY)
        unhealthy_services = sum(1 for r in results.values() if r.status == HealthStatus.UNHEALTHY)
        degraded_services = sum(1 for r in results.values() if r.status == HealthStatus.DEGRADED)
        unreachable_services = sum(1 for r in results.values() if r.status == HealthStatus.UNREACHABLE)
        
        health_percentage = (healthy_services / total_services) * 100 if total_services > 0 else 0
        
        return {
            "timestamp": time.time(),
            "total_services": total_services,
            "healthy_services": healthy_services,
            "unhealthy_services": unhealthy_services,
            "degraded_services": degraded_services,
            "unreachable_services": unreachable_services,
            "health_percentage": health_percentage,
            "overall_status": self._determine_overall_status(health_percentage, unreachable_services),
            "service_details": {name: {
                "status": result.status.value,
                "method_used": result.method_used.value,
                "response_time_ms": result.response_time_ms,
                "error_message": result.error_message
            } for name, result in results.items()}
        }
    
    def _determine_overall_status(self, health_percentage: float, unreachable_count: int) -> str:
        """Determine overall ecosystem status"""
        if unreachable_count > 3:
            return "CRITICAL"
        elif health_percentage >= 90:
            return "EXCELLENT"
        elif health_percentage >= 75:
            return "GOOD"
        elif health_percentage >= 50:
            return "DEGRADED"
        else:
            return "POOR"
    
    def print_health_report(self, results: Dict[str, HealthResult]):
        """Print formatted health report"""
        report = self.generate_health_report(results)
        
        print("🏥 UNIFIED HEALTH MONITORING REPORT")
        print("=" * 50)
        print(f"Overall Status: {report['overall_status']}")
        print(f"Health Percentage: {report['health_percentage']:.1f}%")
        print(f"Total Services: {report['total_services']}")
        print(f"Healthy: {report['healthy_services']} | Unhealthy: {report['unhealthy_services']} | Degraded: {report['degraded_services']} | Unreachable: {report['unreachable_services']}")
        
        print("\n📊 SERVICE DETAILS")
        for service_name, result in results.items():
            status_emoji = {
                HealthStatus.HEALTHY: "✅",
                HealthStatus.UNHEALTHY: "❌", 
                HealthStatus.DEGRADED: "⚠️",
                HealthStatus.UNREACHABLE: "🔌",
                HealthStatus.UNKNOWN: "❓"
            }[result.status]
            
            print(f"  {status_emoji} {service_name:20} | {result.status.value:12} | {result.method_used.value:15} | {result.response_time_ms:6.1f}ms")
            if result.error_message:
                print(f"    Error: {result.error_message}")


def main():
    """Main health monitoring execution"""
    monitor = UnifiedHealthMonitor()
    
    print("🚀 Starting Unified Health Monitoring...")
    results = monitor.check_all_services(parallel=True)
    monitor.print_health_report(results)
    
    # Save results
    report = monitor.generate_health_report(results)
    with open("/Users/mykalthomas/Documents/work/Hackathon/unified_health_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print("\n💾 Health report saved to: unified_health_report.json")


if __name__ == "__main__":
    main()
