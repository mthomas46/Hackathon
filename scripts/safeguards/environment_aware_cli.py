#!/usr/bin/env python3
"""
Environment-Aware CLI Framework
Auto-detects environment and configures appropriate service URLs
"""

import os
import subprocess
import socket
import urllib.request
import urllib.error
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json


class EnvironmentType(Enum):
    """Types of execution environments"""
    HOST_MACHINE = "host_machine"  # Running on host, services in Docker
    DOCKER_INTERNAL = "docker_internal"  # Running inside Docker network
    KUBERNETES = "kubernetes"  # Running in Kubernetes cluster
    DEVELOPMENT = "development"  # Local development setup
    PRODUCTION = "production"  # Production deployment


@dataclass
class ServiceEndpoint:
    """Service endpoint configuration for different environments"""
    host_url: str  # URL when running from host machine
    docker_url: str  # URL when running inside Docker network
    k8s_url: str  # URL when running in Kubernetes
    port: int
    health_path: str = "/health"


class EnvironmentDetector:
    """Detects the current execution environment and configures service URLs"""
    
    def __init__(self):
        self.environment = self._detect_environment()
        self.service_endpoints = self._load_service_endpoints()
        
    def _detect_environment(self) -> EnvironmentType:
        """Auto-detect the current execution environment"""
        
        # Check if running inside Docker container
        if self._is_running_in_docker():
            return EnvironmentType.DOCKER_INTERNAL
            
        # Check if running in Kubernetes
        if self._is_running_in_kubernetes():
            return EnvironmentType.KUBERNETES
            
        # Check if Docker services are accessible from host
        if self._are_docker_services_accessible():
            return EnvironmentType.HOST_MACHINE
            
        # Default to development
        return EnvironmentType.DEVELOPMENT
    
    def _is_running_in_docker(self) -> bool:
        """Check if currently running inside a Docker container"""
        try:
            # Check for Docker-specific files
            if os.path.exists("/.dockerenv"):
                return True
                
            # Check cgroup for Docker indicators
            if os.path.exists("/proc/1/cgroup"):
                with open("/proc/1/cgroup", "r") as f:
                    content = f.read()
                    if "docker" in content or "containerd" in content:
                        return True
                        
            return False
        except Exception:
            return False
    
    def _is_running_in_kubernetes(self) -> bool:
        """Check if running in Kubernetes environment"""
        try:
            # Check for Kubernetes service account
            if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount"):
                return True
                
            # Check environment variables
            if "KUBERNETES_SERVICE_HOST" in os.environ:
                return True
                
            return False
        except Exception:
            return False
    
    def _are_docker_services_accessible(self) -> bool:
        """Check if Docker services are accessible from host machine"""
        try:
            # Test connection to a known Docker service port
            test_ports = [5087, 5099, 5055]  # doc_store, orchestrator, llm-gateway
            
            for port in test_ports:
                try:
                    with socket.create_connection(("localhost", port), timeout=2):
                        return True
                except (socket.timeout, ConnectionRefusedError, OSError):
                    continue
                    
            return False
        except Exception:
            return False
    
    def _load_service_endpoints(self) -> Dict[str, ServiceEndpoint]:
        """Load service endpoint configurations"""
        return {
            "doc_store": ServiceEndpoint(
                host_url="http://localhost:5087",
                docker_url="http://doc_store:5010",
                k8s_url="http://doc-store-service:5010",
                port=5087
            ),
            "orchestrator": ServiceEndpoint(
                host_url="http://localhost:5099",
                docker_url="http://orchestrator:5099",
                k8s_url="http://orchestrator-service:5099",
                port=5099
            ),
            "llm-gateway": ServiceEndpoint(
                host_url="http://localhost:5055",
                docker_url="http://llm-gateway:5055",
                k8s_url="http://llm-gateway-service:5055",
                port=5055
            ),
            "analysis-service": ServiceEndpoint(
                host_url="http://localhost:5080",
                docker_url="http://analysis-service:5020",
                k8s_url="http://analysis-service:5020",
                port=5080
            ),
            "discovery-agent": ServiceEndpoint(
                host_url="http://localhost:5045",
                docker_url="http://discovery-agent:5045",
                k8s_url="http://discovery-agent-service:5045",
                port=5045
            ),
            "prompt_store": ServiceEndpoint(
                host_url="http://localhost:5110",
                docker_url="http://prompt_store:5110",
                k8s_url="http://prompt-store-service:5110",
                port=5110
            ),
            "redis": ServiceEndpoint(
                host_url="http://localhost:6379",
                docker_url="http://redis:6379",
                k8s_url="http://redis-service:6379",
                port=6379,
                health_path="/"
            ),
            "ollama": ServiceEndpoint(
                host_url="http://localhost:11434",
                docker_url="http://ollama:11434",
                k8s_url="http://ollama-service:11434",
                port=11434,
                health_path="/api/tags"
            )
        }
    
    def get_service_url(self, service_name: str) -> Optional[str]:
        """Get the appropriate service URL for current environment"""
        if service_name not in self.service_endpoints:
            return None
            
        endpoint = self.service_endpoints[service_name]
        
        if self.environment == EnvironmentType.HOST_MACHINE:
            return endpoint.host_url
        elif self.environment == EnvironmentType.DOCKER_INTERNAL:
            return endpoint.docker_url
        elif self.environment == EnvironmentType.KUBERNETES:
            return endpoint.k8s_url
        else:
            # Development fallback - try host first
            return endpoint.host_url
    
    def get_health_url(self, service_name: str) -> Optional[str]:
        """Get health check URL for a service"""
        base_url = self.get_service_url(service_name)
        if not base_url:
            return None
            
        endpoint = self.service_endpoints[service_name]
        return f"{base_url}{endpoint.health_path}"
    
    def validate_environment_connectivity(self) -> Dict[str, bool]:
        """Validate connectivity to all services in current environment"""
        results = {}
        
        for service_name in self.service_endpoints.keys():
            health_url = self.get_health_url(service_name)
            if not health_url:
                results[service_name] = False
                continue
                
            try:
                with urllib.request.urlopen(health_url, timeout=5) as response:
                    results[service_name] = response.getcode() == 200
            except Exception:
                results[service_name] = False
        
        return results
    
    def get_environment_info(self) -> Dict[str, any]:
        """Get comprehensive environment information"""
        return {
            "detected_environment": self.environment.value,
            "total_services": len(self.service_endpoints),
            "service_endpoints": {
                name: self.get_service_url(name) 
                for name in self.service_endpoints.keys()
            },
            "connectivity_status": self.validate_environment_connectivity(),
            "docker_available": self._check_docker_availability(),
            "kubernetes_available": self._is_running_in_kubernetes()
        }
    
    def _check_docker_availability(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False


class EnvironmentAwareCLI:
    """CLI framework that adapts to different environments"""
    
    def __init__(self):
        self.detector = EnvironmentDetector()
        self.current_env = self.detector.environment
        
    def execute_service_command(self, service_name: str, endpoint: str, 
                               method: str = "GET", data: Optional[Dict] = None) -> Tuple[bool, str]:
        """Execute a command against a service with environment-aware URL resolution"""
        
        base_url = self.detector.get_service_url(service_name)
        if not base_url:
            return False, f"Unknown service: {service_name}"
        
        url = f"{base_url}{endpoint}"
        
        try:
            if method == "GET":
                with urllib.request.urlopen(url, timeout=10) as response:
                    content = response.read().decode('utf-8')
                    return True, content
            elif method == "POST" and data:
                json_data = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(
                    url,
                    data=json_data,
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    content = response.read().decode('utf-8')
                    return True, content
            else:
                return False, f"Unsupported method: {method}"
                
        except urllib.error.URLError as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Request error: {str(e)}"
    
    def health_check_all_services(self) -> Dict[str, Dict[str, any]]:
        """Perform health checks on all services"""
        results = {}
        
        for service_name in self.detector.service_endpoints.keys():
            health_url = self.detector.get_health_url(service_name)
            
            try:
                with urllib.request.urlopen(health_url, timeout=5) as response:
                    if response.getcode() == 200:
                        content = response.read().decode('utf-8')
                        try:
                            health_data = json.loads(content)
                            results[service_name] = {
                                "status": "healthy",
                                "response": health_data,
                                "url": health_url
                            }
                        except json.JSONDecodeError:
                            results[service_name] = {
                                "status": "healthy",
                                "response": content[:200],
                                "url": health_url
                            }
                    else:
                        results[service_name] = {
                            "status": "unhealthy",
                            "error": f"HTTP {response.getcode()}",
                            "url": health_url
                        }
            except Exception as e:
                results[service_name] = {
                    "status": "unreachable",
                    "error": str(e),
                    "url": health_url
                }
        
        return results
    
    def print_environment_status(self):
        """Print comprehensive environment status"""
        env_info = self.detector.get_environment_info()
        
        print("🌐 ENVIRONMENT-AWARE CLI STATUS")
        print("=" * 50)
        print(f"Detected Environment: {env_info['detected_environment']}")
        print(f"Total Services: {env_info['total_services']}")
        print(f"Docker Available: {env_info['docker_available']}")
        print(f"Kubernetes Available: {env_info['kubernetes_available']}")
        
        print("\n📊 SERVICE CONNECTIVITY")
        for service, connected in env_info['connectivity_status'].items():
            status = "✅ Connected" if connected else "❌ Unreachable"
            url = env_info['service_endpoints'][service]
            print(f"  {service:20} | {status:15} | {url}")


def main():
    """Main CLI execution with environment awareness"""
    cli = EnvironmentAwareCLI()
    
    print("🚀 Environment-Aware CLI Started")
    cli.print_environment_status()
    
    # Test service connectivity
    print("\n🧪 Testing Service Health Checks...")
    health_results = cli.health_check_all_services()
    
    healthy_count = sum(1 for result in health_results.values() if result['status'] == 'healthy')
    total_count = len(health_results)
    
    print(f"\n📈 Health Check Summary: {healthy_count}/{total_count} services healthy")
    
    for service, result in health_results.items():
        status_emoji = "✅" if result['status'] == 'healthy' else "❌"
        print(f"  {status_emoji} {service}: {result['status']}")


if __name__ == "__main__":
    main()
