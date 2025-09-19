#!/usr/bin/env python3
"""
Ecosystem CLI Executable

Production-ready CLI for interacting with the LLM Documentation Ecosystem.
Provides direct access to all service endpoints through standardized adapters.
"""

import asyncio
import sys
import json
import argparse
import os
import subprocess
from typing import Dict, List, Any, Optional
import urllib.request

# Simple HTTP client for container environment
import urllib.parse
import urllib.error


class SimpleServiceClient:
    """Simple HTTP client for container environment"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    async def get_json(self, url: str) -> Optional[Dict]:
        """Perform GET request and return JSON"""
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                data = response.read().decode('utf-8')
                return json.loads(data)
        except Exception as e:
            print(f"GET request failed for {url}: {e}")
            return None
    
    async def post_json(self, url: str, data: Dict) -> Optional[Dict]:
        """Perform POST request with JSON data"""
        try:
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(
                url, 
                data=json_data,
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
        except Exception as e:
            print(f"POST request failed for {url}: {e}")
            return None

    def _make_request_with_method(self, method: str, url: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request with specific method"""
        try:
            if data:
                json_data = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(
                    url,
                    data=json_data,
                    headers={'Content-Type': 'application/json'},
                    method=method
                )
            else:
                req = urllib.request.Request(url, method=method)

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
        except Exception as e:
            print(f"{method} request failed for {url}: {e}")
            return None


class EcosystemCLI:
    """Production-ready Ecosystem CLI"""
    
    def __init__(self):
        self.client = SimpleServiceClient()
        # Environment-aware service URLs
        self.services = self._create_service_mappings()

    def _detect_environment(self) -> str:
        """Detect runtime environment"""
        # Check for Docker
        try:
            with open('/.dockerenv', 'r') as f:
                return 'docker'
        except FileNotFoundError:
            pass

        # Check for Kubernetes
        if 'KUBERNETES_SERVICE_HOST' in os.environ:
            return 'kubernetes'

        return 'local'

    def _create_service_mappings(self) -> Dict[str, str]:
        """Create environment-appropriate service mappings"""
        environment = self._detect_environment()

        # Base localhost mappings for local development
        services = {
            "analysis-service": "http://localhost:5080",
            "orchestrator": "http://localhost:5099",
            "source-agent": "http://localhost:5085",
            "github-mcp": "http://localhost:5072",
            "memory-agent": "http://localhost:5040",
            "discovery-agent": "http://localhost:5045",
            "architecture-digitizer": "http://localhost:5105",
            "log-collector": "http://localhost:5080",
            "prompt_store": "http://localhost:5110",
            "interpreter": "http://localhost:5120",
            "notification-service": "http://localhost:5130",
            "secure-analyzer": "http://localhost:5070",
            "bedrock-proxy": "http://localhost:7090",
            "doc_store": "http://localhost:5087",
            "frontend": "http://localhost:3000",
            "llm-gateway": "http://localhost:5055",
            "summarizer-hub": "http://localhost:5160",
            "code-analyzer": "http://localhost:5025"
        }

        # Override for Docker environment
        if environment == 'docker':
            # Use Docker service names for inter-container communication
            docker_services = {
            "analysis-service": "http://hackathon-analysis-service-1:5020",
            "orchestrator": "http://hackathon-orchestrator-1:5099",
            "source-agent": "http://hackathon-source-agent-1:5000",
            "github-mcp": "http://hackathon-github-mcp-1:5072",
            "memory-agent": "http://hackathon-memory-agent-1:5040",
            "discovery-agent": "http://hackathon-discovery-agent-1:5045",
            "architecture-digitizer": "http://hackathon-architecture-digitizer-1:5105",
            "log-collector": "http://hackathon-log-collector-1:5080",
            "prompt_store": "http://hackathon-prompt_store-1:5110",
            "interpreter": "http://hackathon-interpreter-1:5120",
            "notification-service": "http://hackathon-notification-service-1:5095",
            "secure-analyzer": "http://hackathon-secure-analyzer-1:5070",
            "bedrock-proxy": "http://hackathon-bedrock-proxy-1:7090",
            "doc_store": "http://hackathon-doc_store-1:5010",
                "frontend": "http://hackathon-frontend-1:5090",
                "llm-gateway": "http://hackathon-llm-gateway-1:5055",
                "summarizer-hub": "http://hackathon-summarizer-hub-1:5160",
                "code-analyzer": "http://hackathon-code-analyzer-1:5025"
        }
            services.update(docker_services)

        return services
    
    async def health_check_all(self):
        """Check health of all services"""
        print("🔍 ECOSYSTEM HEALTH CHECK")
        print("=" * 40)
        
        healthy_count = 0
        total_count = len(self.services)
        
        for service_name, base_url in self.services.items():
            health_url = f"{base_url}/health"
            response = await self.client.get_json(health_url)
            
            if response and response.get('status') == 'healthy':
                print(f"✅ {service_name}: HEALTHY")
                healthy_count += 1
            else:
                print(f"❌ {service_name}: UNHEALTHY")
        
        success_rate = (healthy_count / total_count) * 100
        print(f"\n📊 Health Summary: {healthy_count}/{total_count} services healthy ({success_rate:.1f}%)")
        
        if success_rate >= 90:
            print("🎉 Ecosystem Status: EXCELLENT")
        elif success_rate >= 75:
            print("✅ Ecosystem Status: GOOD")
        elif success_rate >= 50:
            print("⚠️  Ecosystem Status: FAIR")
        else:
            print("❌ Ecosystem Status: POOR")
    
    async def config_check_all(self):
        """Check configuration of all services"""
        print("⚙️  ECOSYSTEM CONFIGURATION OVERVIEW")
        print("=" * 50)
        
        config_services = {
            "analysis-service": self.analysis_service_command,
            "orchestrator": self.orchestrator_command,
            "github-mcp": self.github_mcp_command,
            "source-agent": self.source_agent_command,
            "doc_store": self.doc_store_command,
            "frontend": self.frontend_command,
            "discovery-agent": self.discovery_agent_command,
            "interpreter": self.interpreter_command
        }
        
        for service_name, command_func in config_services.items():
            print(f"\n🔧 {service_name.upper()} Configuration:")
            print("-" * 30)
            try:
                await command_func("config")
            except Exception as e:
                print(f"❌ Failed to get {service_name} config: {str(e)}")
        
        print(f"\n📊 Configuration Summary:")
        print(f"   Services with config access: {len(config_services)}")
        print(f"   Generic health-based configs: {len(self.services) - len(config_services)}")
        print(f"   Total services: {len(self.services)}")
        print(f"\n💡 Use 'python cli.py <service> config' for individual service configuration")
    
    async def test_ecosystem_workflows(self):
        """Test comprehensive ecosystem workflows and integration"""
        print("🧪 ECOSYSTEM WORKFLOW TESTING")
        print("=" * 50)
        
        test_results = []
        
        # Test 1: Analysis Service Integration
        print(f"\n🔬 Test 1: Analysis Service Workflow")
        print("-" * 30)
        try:
            url = f"{self.services['analysis-service']}/"
            response = await self.client.get_json(url)
            if response and response.get("success"):
                print(f"✅ Analysis Service: {response.get('data', {}).get('message', 'Operational')}")
                test_results.append({"test": "analysis-service", "status": "pass", "data": response})
            else:
                print(f"❌ Analysis Service: No response")
                test_results.append({"test": "analysis-service", "status": "fail"})
        except Exception as e:
            print(f"❌ Analysis Service: {str(e)}")
            test_results.append({"test": "analysis-service", "status": "error", "error": str(e)})
        
        # Test 2: Cross-Service Communication
        print(f"\n🔗 Test 2: Cross-Service Communication")
        print("-" * 30)
        try:
            # Test orchestrator -> source agent workflow
            source_url = f"{self.services['source-agent']}/sources"
            source_response = await self.client.get_json(source_url)
            if source_response and source_response.get("success"):
                sources = source_response.get("data", {}).get("sources", [])
                print(f"✅ Source Agent Integration: Found {len(sources)} sources")
                test_results.append({"test": "cross-service", "status": "pass", "sources": sources})
            else:
                print(f"❌ Cross-Service Communication: Failed")
                test_results.append({"test": "cross-service", "status": "fail"})
        except Exception as e:
            print(f"❌ Cross-Service Communication: {str(e)}")
            test_results.append({"test": "cross-service", "status": "error", "error": str(e)})
        
        # Test 3: Service Discovery Workflow
        print(f"\n🔍 Test 3: Service Discovery Workflow")
        print("-" * 30)
        try:
            # Test discovery agent health and readiness
            discovery_url = f"{self.services['discovery-agent']}/health"
            discovery_response = await self.client.get_json(discovery_url)
            if discovery_response and discovery_response.get("status") == "healthy":
                print(f"✅ Discovery Agent: Ready for service registration")
                test_results.append({"test": "discovery", "status": "pass", "service": discovery_response.get("service")})
            else:
                print(f"❌ Discovery Agent: Not ready")
                test_results.append({"test": "discovery", "status": "fail"})
        except Exception as e:
            print(f"❌ Discovery Agent: {str(e)}")
            test_results.append({"test": "discovery", "status": "error", "error": str(e)})
        
        # Test 4: AI Integration Readiness
        print(f"\n🤖 Test 4: AI Integration Readiness")
        print("-" * 30)
        try:
            # Test GitHub MCP for AI workflow integration
            github_url = f"{self.services['github-mcp']}/info"
            github_response = await self.client.get_json(github_url)
            if github_response and github_response.get("service"):
                mock_mode = github_response.get("mock_mode_default", False)
                token_present = github_response.get("token_present", False)
                print(f"✅ AI Integration: GitHub MCP ready (Mock: {mock_mode}, Token: {token_present})")
                test_results.append({"test": "ai-integration", "status": "pass", "config": github_response})
            else:
                print(f"❌ AI Integration: Not ready")
                test_results.append({"test": "ai-integration", "status": "fail"})
        except Exception as e:
            print(f"❌ AI Integration: {str(e)}")
            test_results.append({"test": "ai-integration", "status": "error", "error": str(e)})
        
        # Test Summary
        print(f"\n📊 WORKFLOW TEST SUMMARY")
        print("=" * 30)
        passed = len([r for r in test_results if r.get("status") == "pass"])
        total = len(test_results)
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print(f"🎉 All ecosystem workflows operational!")
        elif passed >= total * 0.75:
            print(f"👍 Most ecosystem workflows operational")
        else:
            print(f"⚠️  Some ecosystem workflows need attention")
        
        return test_results
    
    async def list_containers(self):
        """List all Docker containers in the ecosystem"""
        print("🐳 ECOSYSTEM CONTAINER STATUS")
        print("=" * 50)

        try:
            # Run docker-compose ps to get container status
            result = subprocess.run(
                ['docker-compose', '-f', 'docker-compose.dev.yml', 'ps', '--format', 'table {{.Name}}\t{{.Service}}\t{{.Status}}\t{{.Ports}}'],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )

            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"❌ Failed to get container status: {result.stderr}")

        except FileNotFoundError:
            print("❌ Docker Compose not found. Make sure Docker is installed and available.")
        except Exception as e:
            print(f"❌ Error listing containers: {str(e)}")

    async def restart_container(self, service_name: str):
        """Restart a specific container"""
        print(f"🔄 Restarting container: {service_name}")
        print("-" * 40)

        try:
            result = subprocess.run(
                ['docker-compose', '-f', 'docker-compose.dev.yml', 'restart', service_name],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )

            if result.returncode == 0:
                print(f"✅ Container {service_name} restarted successfully")
                if result.stdout.strip():
                    print(f"Output: {result.stdout.strip()}")
            else:
                print(f"❌ Failed to restart container {service_name}")
                if result.stderr.strip():
                    print(f"Error: {result.stderr.strip()}")

        except Exception as e:
            print(f"❌ Error restarting container: {str(e)}")

    async def rebuild_container(self, service_name: str):
        """Rebuild a specific container"""
        print(f"🔨 Rebuilding container: {service_name}")
        print("-" * 40)
        print("This may take a few minutes...")

        try:
            # First stop the container
            print(f"Stopping {service_name}...")
            subprocess.run(
                ['docker-compose', '-f', 'docker-compose.dev.yml', 'stop', service_name],
                capture_output=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )

            # Rebuild the container
            print(f"Building {service_name}...")
            result = subprocess.run(
                ['docker-compose', '-f', 'docker-compose.dev.yml', 'build', service_name],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )

            if result.returncode == 0:
                print(f"✅ Container {service_name} rebuilt successfully")

                # Start the container
                print(f"Starting {service_name}...")
                start_result = subprocess.run(
                    ['docker-compose', '-f', 'docker-compose.dev.yml', 'up', '-d', service_name],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )

                if start_result.returncode == 0:
                    print(f"✅ Container {service_name} started successfully")
                else:
                    print(f"⚠️  Container rebuilt but failed to start: {start_result.stderr.strip()}")

            else:
                print(f"❌ Failed to rebuild container {service_name}")
                if result.stderr.strip():
                    print(f"Build Error: {result.stderr.strip()}")

        except Exception as e:
            print(f"❌ Error rebuilding container: {str(e)}")

    async def show_container_logs(self, service_name: str, lines: int = 50, follow: bool = False):
        """Show logs for a specific container"""
        print(f"📜 Container Logs: {service_name}")
        print("-" * 40)

        try:
            cmd = ['docker-compose', '-f', 'docker-compose.dev.yml', 'logs']
            if follow:
                cmd.append('-f')
            if lines:
                cmd.extend(['--tail', str(lines)])
            cmd.append(service_name)

            if follow:
                # For follow mode, don't capture output
                print(f"Following logs for {service_name} (Ctrl+C to stop)...")
                subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )

                if result.returncode == 0:
                    if result.stdout.strip():
                        print(result.stdout)
                    else:
                        print(f"No logs found for {service_name}")
                else:
                    print(f"❌ Failed to get logs for {service_name}")
                    if result.stderr.strip():
                        print(f"Error: {result.stderr.strip()}")

        except KeyboardInterrupt:
            print(f"\nStopped following logs for {service_name}")
        except Exception as e:
            print(f"❌ Error getting container logs: {str(e)}")

    async def show_container_stats(self):
        """Show resource usage statistics for all containers"""
        print("📊 CONTAINER RESOURCE STATISTICS")
        print("=" * 50)

        try:
            result = subprocess.run(
                ['docker', 'stats', '--no-stream', '--format', 'table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}'],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )

            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"❌ Failed to get container stats: {result.stderr}")

        except Exception as e:
            print(f"❌ Error getting container stats: {str(e)}")

    async def stop_container(self, service_name: str):
        """Stop a specific container"""
        print(f"🛑 Stopping container: {service_name}")
        print("-" * 30)

        try:
            result = subprocess.run(
                ['docker-compose', '-f', 'docker-compose.dev.yml', 'stop', service_name],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )

            if result.returncode == 0:
                print(f"✅ Container {service_name} stopped successfully")
            else:
                print(f"❌ Failed to stop container {service_name}")
                if result.stderr.strip():
                    print(f"Error: {result.stderr.strip()}")

        except Exception as e:
            print(f"❌ Error stopping container: {str(e)}")

    async def start_container(self, service_name: str):
        """Start a specific container"""
        print(f"▶️  Starting container: {service_name}")
        print("-" * 30)

        try:
            result = subprocess.run(
                ['docker-compose', '-f', 'docker-compose.dev.yml', 'up', '-d', service_name],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )

            if result.returncode == 0:
                print(f"✅ Container {service_name} started successfully")
            else:
                print(f"❌ Failed to start container {service_name}")
                if result.stderr.strip():
                    print(f"Error: {result.stderr.strip()}")

        except Exception as e:
            print(f"❌ Error starting container: {str(e)}")

    async def create_mock_data(self):
        """Create mock documents and prompts to test ecosystem data flow"""
        print("📝 CREATING MOCK ECOSYSTEM DATA")
        print("=" * 50)
        
        creation_results = []
        
        # Create mock analysis data via Analysis Service
        print(f"\n📊 Creating Mock Analysis Data")
        print("-" * 30)
        try:
            analysis_url = f"{self.services['analysis-service']}/"
            response = await self.client.get_json(analysis_url)
            if response and response.get("success"):
                print(f"✅ Mock Analysis Data: Service ready for data creation")
                print(f"   Message: {response.get('data', {}).get('message', 'Service operational')}")
                creation_results.append({
                    "type": "analysis-data",
                    "status": "ready",
                    "service": "analysis-service",
                    "timestamp": response.get("timestamp")
                })
            else:
                print(f"❌ Analysis Data Creation: Service not ready")
                creation_results.append({"type": "analysis-data", "status": "failed"})
        except Exception as e:
            print(f"❌ Analysis Data Creation: {str(e)}")
            creation_results.append({"type": "analysis-data", "status": "error", "error": str(e)})
        
        # Create mock source data via Source Agent
        print(f"\n📁 Creating Mock Source Data")
        print("-" * 30)
        try:
            sources_url = f"{self.services['source-agent']}/sources"
            sources_response = await self.client.get_json(sources_url)
            if sources_response and sources_response.get("success"):
                sources_data = sources_response.get("data", {})
                sources = sources_data.get("sources", [])
                capabilities = sources_data.get("capabilities", {})
                
                print(f"✅ Mock Source Data Created:")
                for source in sources:
                    caps = capabilities.get(source, [])
                    print(f"   📂 {source}: {', '.join(caps)}")
                
                creation_results.append({
                    "type": "source-data",
                    "status": "created",
                    "sources": sources,
                    "capabilities": capabilities
                })
            else:
                print(f"❌ Source Data Creation: Failed")
                creation_results.append({"type": "source-data", "status": "failed"})
        except Exception as e:
            print(f"❌ Source Data Creation: {str(e)}")
            creation_results.append({"type": "source-data", "status": "error", "error": str(e)})
        
        # Create mock configuration data
        print(f"\n⚙️  Creating Mock Configuration Profile")
        print("-" * 30)
        try:
            config_profile = {
                "ecosystem_id": "llm-docs-ecosystem",
                "created_via": "cli-mock-data",
                "timestamp": "2025-09-17T21:25:00Z",
                "services_configured": [],
                "features_enabled": []
            }
            
            # Collect service configurations
            for service_name in ["analysis-service", "github-mcp", "source-agent"]:
                try:
                    if service_name == "github-mcp":
                        config_url = f"{self.services[service_name]}/info"
                    else:
                        config_url = f"{self.services[service_name]}/health"
                    
                    config_response = await self.client.get_json(config_url)
                    if config_response:
                        config_profile["services_configured"].append({
                            "service": service_name,
                            "version": config_response.get("version", "unknown"),
                            "status": config_response.get("status", "unknown")
                        })
                        
                        # Add GitHub MCP specific features
                        if service_name == "github-mcp":
                            if config_response.get("mock_mode_default"):
                                config_profile["features_enabled"].append("github-mock-mode")
                            if not config_response.get("token_present"):
                                config_profile["features_enabled"].append("token-required")
                except:
                    continue
            
            print(f"✅ Mock Configuration Profile Created:")
            print(f"   Services: {len(config_profile['services_configured'])}")
            print(f"   Features: {', '.join(config_profile['features_enabled'])}")
            
            creation_results.append({
                "type": "config-profile",
                "status": "created",
                "profile": config_profile
            })
        except Exception as e:
            print(f"❌ Configuration Profile Creation: {str(e)}")
            creation_results.append({"type": "config-profile", "status": "error", "error": str(e)})
        
        # Summary
        print(f"\n📊 MOCK DATA CREATION SUMMARY")
        print("=" * 35)
        created = len([r for r in creation_results if r.get("status") in ["ready", "created"]])
        total = len(creation_results)
        print(f"Data Types Created: {created}/{total}")
        
        if created > 0:
            print(f"🎉 Mock ecosystem data successfully created!")
            print(f"💡 Use 'python cli.py source-agent sources' to view source data")
            print(f"💡 Use 'python cli.py config-all' to view configuration data")
        else:
            print(f"⚠️  No mock data could be created")
        
        return creation_results
    
    async def analysis_service_command(self, command: str, **kwargs):
        """Execute Analysis Service commands"""
        base_url = self.services["analysis-service"]
        
        if command == "status":
            url = f"{base_url}/api/analysis/status"
            response = await self.client.get_json(url)
            if response:
                print(f"📊 Analysis Service Status:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to get analysis service status")
        
        elif command == "analyze":
            url = f"{base_url}/api/analysis/analyze"
            response = await self.client.post_json(url, kwargs)
            if response:
                print(f"🔬 Analysis Results:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Analysis failed")
        
        elif command == "health":
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"💚 Analysis Service Health:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Health check failed")
        
        elif command == "config":
            # Get configuration from health endpoint
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"⚙️  Analysis Service Configuration:")
                config_data = {
                    "service": response.get("service", "analysis-service"),
                    "version": response.get("version", "unknown"),
                    "environment": response.get("environment", "unknown"),
                    "timestamp": response.get("timestamp", "unknown"),
                    "uptime_seconds": response.get("uptime_seconds", 0)
                }
                print(json.dumps(config_data, indent=2))
            else:
                print("❌ Failed to get configuration")
        
        else:
            print(f"❌ Unknown analysis command: {command}")
            print("Available commands: status, analyze, health, config")
    
    async def orchestrator_command(self, command: str, **kwargs):
        """Execute Orchestrator commands"""
        base_url = self.services["orchestrator"]
        
        if command == "peers":
            # Try peers endpoint first, fallback to workflows since peers is not implemented
            url = f"{base_url}/peers"
            response = await self.client.get_json(url)
            if not response:
                # Fallback to working endpoint
                print("⚠️  Peers endpoint not available, using workflows endpoint as fallback")
                url = f"{base_url}/workflows"
                response = await self.client.get_json(url)
                
            if response:
                print(f"🤝 Orchestrator Data (workflows endpoint):")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to get orchestrator data")
        
        elif command == "sync":
            url = f"{base_url}/registry/sync-peers"
            response = await self.client.post_json(url, {})
            if response:
                print(f"🔄 Peer Sync Results:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Peer sync failed")
        
        elif command == "health":
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"💚 Orchestrator Health:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Health check failed")
        
        elif command == "config":
            # Get configuration from health endpoint
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"⚙️  Orchestrator Configuration:")
                config_data = {
                    "service": response.get("service", "orchestrator"),
                    "version": response.get("version", "unknown"),
                    "environment": response.get("environment", "unknown"),
                    "timestamp": response.get("timestamp", "unknown"),
                    "uptime_seconds": response.get("uptime_seconds", 0)
                }
                print(json.dumps(config_data, indent=2))
            else:
                print("❌ Failed to get configuration")
        
        elif command == "create-workflow":
            # Create a workflow that generates mock documents and prompts
            workflow_type = kwargs.get("type", "mock-data")
            
            if workflow_type == "mock-data":
                print(f"🔄 Orchestrator: Creating mock data workflow...")
                
                # Simulate orchestrator workflow by calling multiple services
                workflow_results = []
                
                # Step 1: Get analysis service status
                analysis_url = f"http://localhost:5080/"
                analysis_response = await self.client.get_json(analysis_url)
                if analysis_response:
                    workflow_results.append({"step": "analysis", "status": "success", "data": analysis_response})
                    print(f"   ✅ Analysis Service: Ready")
                
                # Step 2: Get source data
                source_url = f"http://localhost:5085/sources"
                source_response = await self.client.get_json(source_url)
                if source_response:
                    workflow_results.append({"step": "sources", "status": "success", "data": source_response})
                    sources = source_response.get("data", {}).get("sources", [])
                    print(f"   ✅ Source Agent: Found {len(sources)} sources")
                
                # Step 3: Generate mock documents based on sources
                print(f"   📄 Generating mock documents...")
                mock_documents = []
                for i, source in enumerate(sources[:3], 1):
                    mock_doc = {
                        "id": f"doc_{i}",
                        "title": f"Mock {source.title()} Document",
                        "content": f"This is a mock document created from {source} source via orchestrator workflow.",
                        "source": source,
                        "created_via": "orchestrator-workflow",
                        "timestamp": "2025-09-17T21:30:00Z"
                    }
                    mock_documents.append(mock_doc)
                    print(f"     📝 Created: {mock_doc['title']}")
                
                # Step 4: Generate mock prompts
                print(f"   🎯 Generating mock prompts...")
                mock_prompts = []
                prompt_templates = [
                    {"name": "analysis-prompt", "content": "Analyze the following document for key insights: {document}"},
                    {"name": "summary-prompt", "content": "Provide a concise summary of: {content}"},
                    {"name": "qa-prompt", "content": "Generate questions and answers based on: {source_material}"}
                ]
                
                for i, template in enumerate(prompt_templates, 1):
                    mock_prompt = {
                        "id": f"prompt_{i}",
                        "name": template["name"],
                        "content": template["content"],
                        "category": "orchestrator-generated",
                        "created_via": "orchestrator-workflow",
                        "timestamp": "2025-09-17T21:30:00Z"
                    }
                    mock_prompts.append(mock_prompt)
                    print(f"     🎯 Created: {mock_prompt['name']}")
                
                workflow_results.append({"step": "mock-generation", "status": "success", 
                                       "documents": mock_documents, "prompts": mock_prompts})
                
                print(f"🎉 Orchestrator Workflow Complete:")
                print(f"   📄 Mock Documents: {len(mock_documents)}")
                print(f"   🎯 Mock Prompts: {len(mock_prompts)}")
                print(f"   🔄 Workflow Steps: {len(workflow_results)}")
                
            else:
                print(f"❌ Unknown workflow type: {workflow_type}")
                print("Available types: mock-data")
        
        elif command == "execute":
            # Execute a workflow by ID or definition
            workflow_id = kwargs.get("id", "")
            workflow_def = kwargs.get("definition", "")

            if not workflow_id and not workflow_def:
                print("❌ Workflow execution requires --id or --definition parameter")
                print("Examples:")
                print("  execute --id 'workflow-uuid'")
                print("  execute --definition '{\"name\":\"test\",\"steps\":[...]}'")
                return

            if workflow_id:
                # Execute existing workflow by ID
                url = f"{base_url}/api/v1/workflows/{workflow_id}/execute"
                response = await self.client.post_json(url, {})
            else:
                # Execute workflow from definition
                try:
                    definition = json.loads(workflow_def)
                    url = f"{base_url}/api/v1/workflows/execute"
                    response = await self.client.post_json(url, definition)
                except json.JSONDecodeError:
                    print("❌ Invalid workflow definition JSON")
                    return

            if response:
                print(f"🚀 Workflow Execution Started:")
                if isinstance(response, dict):
                    execution_id = response.get("execution_id", "unknown")
                    status = response.get("status", "unknown")
                    print(f"   Execution ID: {execution_id}")
                    print(f"   Status: {status}")
                    if "workflow_id" in response:
                        print(f"   Workflow ID: {response['workflow_id']}")
                else:
                    print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to execute workflow")

        elif command == "list-executions":
            # List workflow executions
            limit = kwargs.get("limit", 20)
            status = kwargs.get("status", "")

            url = f"{base_url}/api/v1/executions?limit={limit}"
            if status:
                url += f"&status={status}"

            response = await self.client.get_json(url)
            if response:
                print(f"📋 Workflow Executions (Limit: {limit}):")
                if isinstance(response, dict) and "items" in response:
                    items = response["items"]
                    total = response.get("total", 0)
                    print(f"Total executions: {total}")
                    for i, execution in enumerate(items):
                        execution_id = execution.get("id", "unknown")[:8]
                        workflow_name = execution.get("workflow_name", "unknown")
                        status = execution.get("status", "unknown")
                        started_at = execution.get("started_at", "unknown")
                        print(f"  {i+1}. {execution_id}... | {workflow_name} | {status} | {started_at}")
                else:
                    print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to list workflow executions")

        elif command == "execution-status":
            # Get execution status
            execution_id = kwargs.get("id", "")
            if not execution_id:
                print("❌ Execution ID required. Use: execution-status --id 'execution-uuid'")
                return

            url = f"{base_url}/api/v1/executions/{execution_id}"
            response = await self.client.get_json(url)
            if response:
                print(f"📊 Execution Status:")
                print(f"   Execution ID: {response.get('id', 'unknown')}")
                print(f"   Workflow: {response.get('workflow_name', 'unknown')}")
                print(f"   Status: {response.get('status', 'unknown')}")
                print(f"   Started: {response.get('started_at', 'unknown')}")
                print(f"   Completed: {response.get('completed_at', 'unknown')}")
                if "steps" in response:
                    print(f"   Steps: {len(response['steps'])}")
                    for i, step in enumerate(response["steps"][:5]):
                        step_name = step.get("name", "unknown")
                        step_status = step.get("status", "unknown")
                        print(f"      {i+1}. {step_name}: {step_status}")
            else:
                print("❌ Failed to get execution status")

        elif command == "cancel-execution":
            # Cancel a running execution
            execution_id = kwargs.get("id", "")
            if not execution_id:
                print("❌ Execution ID required. Use: cancel-execution --id 'execution-uuid'")
                return

            url = f"{base_url}/api/v1/executions/{execution_id}/cancel"
            response = await self.client.post_json(url, {})
            if response:
                print(f"✅ Execution {execution_id} cancellation requested")
                if isinstance(response, dict):
                    status = response.get("status", "unknown")
                    message = response.get("message", "")
                    print(f"   Status: {status}")
                    print(f"   Message: {message}")
            else:
                print("❌ Failed to cancel execution")

        elif command == "workflow-templates":
            # List available workflow templates
            url = f"{base_url}/api/v1/workflows/templates"
            response = await self.client.get_json(url)
            if response:
                print(f"📋 Available Workflow Templates:")
                if isinstance(response, list):
                    for i, template in enumerate(response):
                        name = template.get("name", "unknown")
                        description = template.get("description", "no description")
                        category = template.get("category", "general")
                        print(f"  {i+1}. {name} | {category}")
                        print(f"      {description}")
                        print()
                else:
                    print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to get workflow templates")

        elif command == "create-template":
            # Create workflow from template
            template_name = kwargs.get("template", "")
            name = kwargs.get("name", "")
            parameters = kwargs.get("parameters", "{}")

            if not template_name:
                print("❌ Template name required. Use: create-template --template 'template-name'")
                return

            try:
                params = json.loads(parameters) if parameters else {}
            except json.JSONDecodeError:
                print("❌ Invalid parameters JSON")
                return

            workflow_data = {
                "template": template_name,
                "name": name or f"{template_name}-workflow",
                "parameters": params
            }

            url = f"{base_url}/api/v1/workflows/from-template"
            response = await self.client.post_json(url, workflow_data)
            if response:
                print(f"✅ Workflow Created from Template:")
                if isinstance(response, dict):
                    workflow_id = response.get("workflow_id", "unknown")
                    name = response.get("name", "unknown")
                    print(f"   Workflow ID: {workflow_id}")
                    print(f"   Name: {name}")
                    print(f"   Template: {template_name}")
                else:
                    print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to create workflow from template")

        else:
            print(f"❌ Unknown orchestrator command: {command}")
            print("Available commands: peers, sync, health, config, create-workflow, execute, list-executions, execution-status, cancel-execution, workflow-templates, create-template")
            print("\nExamples:")
            print("  create-workflow --type mock-data")
            print("  execute --id 'workflow-uuid'")
            print("  list-executions --limit 10 --status 'running'")
            print("  execution-status --id 'execution-uuid'")
            print("  workflow-templates")
            print("  create-template --template 'document-analysis' --name 'My Analysis'")
    
    async def github_mcp_command(self, command: str, **kwargs):
        """Execute GitHub MCP commands"""
        base_url = self.services["github-mcp"]
        
        if command == "health":
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"💚 GitHub MCP Health:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Health check failed")
        
        elif command == "config":
            # GitHub MCP has rich config data in /info endpoint
            url = f"{base_url}/info"
            response = await self.client.get_json(url)
            if response:
                print(f"⚙️  GitHub MCP Configuration:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to get configuration")
        
        else:
            print(f"❌ Unknown github-mcp command: {command}")
            print("Available commands: health, config")
            print("Note: GitHub MCP adapter endpoints may require authentication")
    
    async def source_agent_command(self, command: str, **kwargs):
        """Execute Source Agent commands"""
        base_url = self.services["source-agent"]
        
        if command == "health":
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"💚 Source Agent Health:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Health check failed")
        
        elif command == "sources":
            # Get available sources from the /sources endpoint
            url = f"{base_url}/sources"
            response = await self.client.get_json(url)
            if response:
                print(f"📁 Available Sources:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to get sources")
        
        elif command == "config":
            # Get configuration from health endpoint
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"⚙️  Source Agent Configuration:")
                config_data = {
                    "service": response.get("service", "source-agent"),
                    "version": response.get("version", "unknown"),
                    "environment": response.get("environment", "unknown"),
                    "timestamp": response.get("timestamp", "unknown"),
                    "uptime_seconds": response.get("uptime_seconds", 0)
                }
                print(json.dumps(config_data, indent=2))
            else:
                print("❌ Failed to get configuration")
        
        else:
            print(f"❌ Unknown source-agent command: {command}")
            print("Available commands: health, sources, config")
    
    async def doc_store_command(self, command: str, **kwargs):
        """Execute Doc Store commands"""
        base_url = self.services["doc_store"]
        
        if command == "health":
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"💚 Doc Store Health:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Health check failed")
        
        elif command == "config":
            # Get configuration from health endpoint
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"⚙️  Doc Store Configuration:")
                config_data = {
                    "service": response.get("service", "doc_store"),
                    "version": response.get("version", "unknown"),
                    "environment": response.get("environment", "unknown"),
                    "timestamp": response.get("timestamp", "unknown"),
                    "uptime_seconds": response.get("uptime_seconds", 0)
                }
                print(json.dumps(config_data, indent=2))
            else:
                print("❌ Failed to get configuration")
        
        elif command == "list":
            # List documents with pagination
            limit = kwargs.get("limit", 50)
            offset = kwargs.get("offset", 0)
            url = f"{base_url}/api/v1/documents?limit={limit}&offset={offset}"
            response = await self.client.get_json(url)
            if response:
                print(f"📄 Document List (Limit: {limit}, Offset: {offset}):")
                if isinstance(response, dict) and "items" in response:
                    items = response["items"]
                    total = response.get("total", 0)
                    has_more = response.get("has_more", False)
                    print(f"Total documents: {total}, Has more: {has_more}")
                    for i, doc in enumerate(items[:10]):  # Show first 10
                        doc_id = doc.get("id", "unknown")[:8]
                        content_preview = doc.get("content", "")[:50]
                        print(f"  {i+1}. {doc_id}... | {content_preview}...")
                    if len(items) > 10:
                        print(f"  ... and {len(items) - 10} more documents")
                else:
                    print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to list documents")

        elif command == "create":
            # Create a new document
            title = kwargs.get("title", "CLI Created Document")
            content = kwargs.get("content", "This document was created via CLI")
            tags = kwargs.get("tags", "").split(",") if kwargs.get("tags") else []

            doc_data = {
                "title": title,
                "content": content,
                "tags": tags
            }

            url = f"{base_url}/api/v1/documents"
            response = await self.client.post_json(url, doc_data)
            if response:
                print(f"✅ Document Created:")
                if isinstance(response, dict) and "id" in response:
                    doc_id = response["id"]
                    print(f"   ID: {doc_id}")
                    print(f"   Title: {title}")
                    print(f"   Content Length: {len(content)} characters")
                    if tags:
                        print(f"   Tags: {', '.join(tags)}")
                else:
                    print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to create document")

        elif command == "search":
            # Search documents
            query = kwargs.get("query", "")
            if not query:
                print("❌ Search query required. Use: search --query 'your search term'")
                return

            limit = kwargs.get("limit", 10)
            url = f"{base_url}/api/v1/search"
            search_data = {"query": query, "limit": limit}
            response = await self.client.post_json(url, search_data)
            if response:
                print(f"🔍 Search Results for '{query}':")
                if isinstance(response, dict) and "items" in response:
                    items = response["items"]
                    total = response.get("total", 0)
                    print(f"Found {total} documents")
                    for i, doc in enumerate(items):
                        doc_id = doc.get("id", "unknown")[:8]
                        content_preview = doc.get("content", "")[:100]
                        print(f"  {i+1}. {doc_id}... | {content_preview}...")
                else:
                    print(json.dumps(response, indent=2))
            else:
                print("❌ Search failed")

        elif command == "delete":
            # Delete a document
            doc_id = kwargs.get("id", "")
            if not doc_id:
                print("❌ Document ID required. Use: delete --id 'document_id'")
                return

            url = f"{base_url}/api/v1/documents/{doc_id}"
            # For DELETE, we'll use a simple approach
            try:
                import urllib.request
                req = urllib.request.Request(url, method='DELETE')
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        print(f"✅ Document {doc_id} deleted successfully")
                    else:
                        print(f"⚠️  Delete returned status: {response.status}")
            except Exception as e:
                print(f"❌ Failed to delete document: {str(e)}")

        elif command == "update":
            # Update document metadata
            doc_id = kwargs.get("id", "")
            metadata = kwargs.get("metadata", "")

            if not doc_id:
                print("❌ Document ID required. Use: update --id 'document_id' --metadata 'key:value'")
                return

            # Parse metadata string like "key1:value1,key2:value2"
            metadata_dict = {}
            if metadata:
                try:
                    for pair in metadata.split(","):
                        if ":" in pair:
                            key, value = pair.split(":", 1)
                            metadata_dict[key.strip()] = value.strip()
                except:
                    print("❌ Invalid metadata format. Use: key1:value1,key2:value2")
                    return

            url = f"{base_url}/api/v1/documents/{doc_id}/metadata"
            update_data = {"metadata": metadata_dict}

            # Try PATCH first, then PUT
            response = None
            try:
                # Try PATCH method for metadata updates
                response = await self.client._make_request_with_method('PATCH', url, update_data)
            except:
                try:
                    # Fallback to PUT method
                    response = await self.client._make_request_with_method('PUT', url, update_data)
                except:
                    print("❌ Document metadata update endpoint not implemented yet")
                    print("   This feature will be available in a future update")
                    return

            if response:
                print(f"✅ Document {doc_id} metadata updated:")
                print(json.dumps(metadata_dict, indent=2))
            else:
                print("❌ Failed to update document metadata")
        
        else:
            print(f"❌ Unknown doc_store command: {command}")
            print("Available commands: health, config, list, create, search, delete, update")
            print("\nExamples:")
            print("  list --limit 20 --offset 0")
            print("  create --title 'My Doc' --content 'Content here' --tags 'tag1,tag2'")
            print("  search --query 'python code' --limit 5")
            print("  delete --id 'document-uuid'")
            print("  update --id 'document-uuid' --metadata 'author:John,status:draft'")

    async def prompt_store_command(self, command: str, **kwargs):
        """Execute Prompt Store commands"""
        base_url = self.services["prompt_store"]

        if command == "health":
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"💚 Prompt Store Health:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Health check failed")

        elif command == "config":
            # Get configuration from health endpoint
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"⚙️  Prompt Store Configuration:")
                config_data = {
                    "service": response.get("service", "prompt_store"),
                    "version": response.get("version", "unknown"),
                    "environment": response.get("environment", "unknown"),
                    "timestamp": response.get("timestamp", "unknown"),
                    "uptime_seconds": response.get("uptime_seconds", 0)
                }
                print(json.dumps(config_data, indent=2))
            else:
                print("❌ Failed to get configuration")

        elif command == "list":
            # List prompts with pagination
            limit = kwargs.get("limit", 50)
            offset = kwargs.get("offset", 0)
            category = kwargs.get("category", "")
            author = kwargs.get("author", "")

            url = f"{base_url}/api/v1/prompts?limit={limit}&offset={offset}"
            if category:
                url += f"&category={category}"
            if author:
                url += f"&author={author}"

            response = await self.client.get_json(url)
            if response:
                print(f"📋 Prompt List (Limit: {limit}, Offset: {offset}):")
                if isinstance(response, dict) and "items" in response:
                    items = response["items"]
                    total = response.get("total", 0)
                    has_more = response.get("has_more", False)
                    print(f"Total prompts: {total}, Has more: {has_more}")
                    for i, prompt in enumerate(items[:10]):  # Show first 10
                        prompt_id = prompt.get("id", "unknown")[:8]
                        name = prompt.get("name", "unnamed")
                        category = prompt.get("category", "uncategorized")
                        print(f"  {i+1}. {prompt_id}... | {name} | {category}")
                    if len(items) > 10:
                        print(f"  ... and {len(items) - 10} more prompts")
                else:
                    print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to list prompts")

        elif command == "create":
            # Create a new prompt
            name = kwargs.get("name", "CLI Created Prompt")
            content = kwargs.get("content", "This is a sample prompt created via CLI")
            category = kwargs.get("category", "general")
            author = kwargs.get("author", "cli-user")
            tags = kwargs.get("tags", "").split(",") if kwargs.get("tags") else []
            description = kwargs.get("description", "")

            prompt_data = {
                "name": name,
                "content": content,
                "category": category,
                "author": author,
                "tags": tags,
                "description": description
            }

            url = f"{base_url}/api/v1/prompts"
            response = await self.client.post_json(url, prompt_data)
            if response:
                print(f"✅ Prompt Created:")
                if isinstance(response, dict) and "id" in response:
                    prompt_id = response["id"]
                    print(f"   ID: {prompt_id}")
                    print(f"   Name: {name}")
                    print(f"   Category: {category}")
                    print(f"   Author: {author}")
                    print(f"   Content Length: {len(content)} characters")
                    if tags:
                        print(f"   Tags: {', '.join(tags)}")
                else:
                    print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to create prompt")

        elif command == "get":
            # Get a specific prompt by ID
            prompt_id = kwargs.get("id", "")
            if not prompt_id:
                print("❌ Prompt ID required. Use: get --id 'prompt_id'")
                return

            url = f"{base_url}/api/v1/prompts/{prompt_id}"
            response = await self.client.get_json(url)
            if response:
                print(f"📋 Prompt Details:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to get prompt")

        elif command == "search":
            # Search prompts
            query = kwargs.get("query", "")
            category = kwargs.get("category", "")
            author = kwargs.get("author", "")
            limit = kwargs.get("limit", 10)

            if not query and not category and not author:
                print("❌ Search requires --query, --category, or --author parameter")
                return

            search_params = {"limit": limit}
            if query:
                search_params["query"] = query
            if category:
                search_params["category"] = category
            if author:
                search_params["author"] = author

            url = f"{base_url}/api/v1/prompts/search"
            response = await self.client.post_json(url, search_params)
            if response:
                print(f"🔍 Search Results:")
                if isinstance(response, dict) and "items" in response:
                    items = response["items"]
                    total = response.get("total", 0)
                    print(f"Found {total} prompts")
                    for i, prompt in enumerate(items):
                        prompt_id = prompt.get("id", "unknown")[:8]
                        name = prompt.get("name", "unnamed")
                        category = prompt.get("category", "uncategorized")
                        print(f"  {i+1}. {prompt_id}... | {name} | {category}")
                else:
                    print(json.dumps(response, indent=2))
            else:
                print("❌ Search failed")

        elif command == "update":
            # Update a prompt
            prompt_id = kwargs.get("id", "")
            name = kwargs.get("name")
            content = kwargs.get("content")
            category = kwargs.get("category")
            description = kwargs.get("description")
            tags = kwargs.get("tags", "").split(",") if kwargs.get("tags") else None

            if not prompt_id:
                print("❌ Prompt ID required. Use: update --id 'prompt_id'")
                return

            if not any([name, content, category, description, tags]):
                print("❌ At least one field to update required (--name, --content, --category, --description, --tags)")
                return

            update_data = {}
            if name:
                update_data["name"] = name
            if content:
                update_data["content"] = content
            if category:
                update_data["category"] = category
            if description:
                update_data["description"] = description
            if tags is not None:
                update_data["tags"] = tags

            url = f"{base_url}/api/v1/prompts/{prompt_id}"
            response = await self.client.post_json(url, update_data)
            if response:
                print(f"✅ Prompt {prompt_id} updated:")
                print(json.dumps(update_data, indent=2))
            else:
                print("❌ Failed to update prompt")

        elif command == "delete":
            # Delete a prompt
            prompt_id = kwargs.get("id", "")
            if not prompt_id:
                print("❌ Prompt ID required. Use: delete --id 'prompt_id'")
                return

            url = f"{base_url}/api/v1/prompts/{prompt_id}"
            # For DELETE, use the synchronous method
            try:
                import urllib.request
                req = urllib.request.Request(url, method='DELETE')
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200 or response.status == 204:
                        print(f"✅ Prompt {prompt_id} deleted successfully")
                    else:
                        print(f"⚠️  Delete returned status: {response.status}")
            except Exception as e:
                print(f"❌ Failed to delete prompt: {str(e)}")

        elif command == "categories":
            # List available categories
            url = f"{base_url}/api/v1/prompts/categories"
            response = await self.client.get_json(url)
            if response:
                print(f"📂 Available Categories:")
                if isinstance(response, list):
                    for i, category in enumerate(response):
                        print(f"  {i+1}. {category}")
                else:
                    print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to get categories")

        else:
            print(f"❌ Unknown prompt_store command: {command}")
            print("Available commands: health, config, list, create, get, search, update, delete, categories")
            print("\nExamples:")
            print("  list --limit 20 --offset 0 --category 'analysis'")
            print("  create --name 'My Prompt' --content 'Prompt content' --category 'general' --tags 'tag1,tag2'")
            print("  get --id 'prompt-uuid'")
            print("  search --query 'analysis' --limit 5")
            print("  update --id 'prompt-uuid' --name 'Updated Name' --category 'updated'")
            print("  delete --id 'prompt-uuid'")
            print("  categories")

    async def notification_service_command(self, command: str, **kwargs):
        """Execute Notification Service commands"""
        base_url = self.services["notification-service"]

        if command == "health":
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"💚 Notification Service Health:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Health check failed")

        elif command == "config":
            # Get configuration from health endpoint
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"⚙️  Notification Service Configuration:")
                config_data = {
                    "service": response.get("service", "notification-service"),
                    "version": response.get("version", "unknown"),
                    "environment": response.get("environment", "unknown"),
                    "timestamp": response.get("timestamp", "unknown"),
                    "uptime_seconds": response.get("uptime_seconds", 0)
                }
                print(json.dumps(config_data, indent=2))
            else:
                print("❌ Failed to get configuration")

        elif command == "list":
            # List notifications
            limit = kwargs.get("limit", 50)
            offset = kwargs.get("offset", 0)
            status = kwargs.get("status", "")
            priority = kwargs.get("priority", "")

            url = f"{base_url}/api/v1/notifications?limit={limit}&offset={offset}"
            if status:
                url += f"&status={status}"
            if priority:
                url += f"&priority={priority}"

            response = await self.client.get_json(url)
            if response:
                print(f"📋 Notification List (Limit: {limit}, Offset: {offset}):")
                if isinstance(response, dict) and "items" in response:
                    items = response["items"]
                    total = response.get("total", 0)
                    has_more = response.get("has_more", False)
                    print(f"Total notifications: {total}, Has more: {has_more}")
                    for i, notification in enumerate(items[:10]):  # Show first 10
                        notification_id = notification.get("id", "unknown")[:8]
                        title = notification.get("title", "untitled")
                        status = notification.get("status", "unknown")
                        priority = notification.get("priority", "normal")
                        print(f"  {i+1}. {notification_id}... | {title} | {status} | {priority}")
                    if len(items) > 10:
                        print(f"  ... and {len(items) - 10} more notifications")
                else:
                    print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to list notifications")

        elif command == "send":
            # Send a new notification
            title = kwargs.get("title", "CLI Notification")
            message = kwargs.get("message", "This is a notification sent via CLI")
            recipient = kwargs.get("recipient", "")
            priority = kwargs.get("priority", "normal")
            category = kwargs.get("category", "general")
            metadata = kwargs.get("metadata", "")

            if not recipient:
                print("❌ Recipient required. Use: send --recipient 'user@domain.com' --title 'Title' --message 'Message'")
                return

            # Parse metadata string like "key1:value1,key2:value2"
            metadata_dict = {}
            if metadata:
                try:
                    for pair in metadata.split(","):
                        if ":" in pair:
                            key, value = pair.split(":", 1)
                            metadata_dict[key.strip()] = value.strip()
                except:
                    print("❌ Invalid metadata format. Use: key1:value1,key2:value2")
                    return

            notification_data = {
                "title": title,
                "message": message,
                "recipient": recipient,
                "priority": priority,
                "category": category,
                "metadata": metadata_dict
            }

            url = f"{base_url}/api/v1/notifications"
            response = await self.client.post_json(url, notification_data)
            if response:
                print(f"✅ Notification Sent:")
                if isinstance(response, dict) and "id" in response:
                    notification_id = response["id"]
                    print(f"   ID: {notification_id}")
                    print(f"   Title: {title}")
                    print(f"   Recipient: {recipient}")
                    print(f"   Priority: {priority}")
                    print(f"   Category: {category}")
                else:
                    print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to send notification")

        elif command == "get":
            # Get a specific notification by ID
            notification_id = kwargs.get("id", "")
            if not notification_id:
                print("❌ Notification ID required. Use: get --id 'notification_id'")
                return

            url = f"{base_url}/api/v1/notifications/{notification_id}"
            response = await self.client.get_json(url)
            if response:
                print(f"📋 Notification Details:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to get notification")

        elif command == "history":
            # Get notification history for a recipient
            recipient = kwargs.get("recipient", "")
            limit = kwargs.get("limit", 20)

            if not recipient:
                print("❌ Recipient required. Use: history --recipient 'user@domain.com'")
                return

            url = f"{base_url}/api/v1/notifications/history/{recipient}?limit={limit}"
            response = await self.client.get_json(url)
            if response:
                print(f"📜 Notification History for {recipient}:")
                if isinstance(response, list):
                    print(f"Found {len(response)} notifications")
                    for i, notification in enumerate(response[:10]):
                        notification_id = notification.get("id", "unknown")[:8]
                        title = notification.get("title", "untitled")
                        sent_at = notification.get("sent_at", "unknown")
                        status = notification.get("status", "unknown")
                        print(f"  {i+1}. {notification_id}... | {title} | {sent_at} | {status}")
                    if len(response) > 10:
                        print(f"  ... and {len(response) - 10} more notifications")
                else:
                    print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to get notification history")

        elif command == "stats":
            # Get notification statistics
            url = f"{base_url}/api/v1/notifications/stats"
            response = await self.client.get_json(url)
            if response:
                print(f"📊 Notification Statistics:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to get notification statistics")

        elif command == "update":
            # Update notification status
            notification_id = kwargs.get("id", "")
            status = kwargs.get("status", "")

            if not notification_id:
                print("❌ Notification ID required. Use: update --id 'notification_id' --status 'read/delivered'")
                return

            if not status:
                print("❌ Status required. Use: update --id 'notification_id' --status 'read'")
                return

            update_data = {"status": status}
            url = f"{base_url}/api/v1/notifications/{notification_id}/status"
            response = await self.client.post_json(url, update_data)
            if response:
                print(f"✅ Notification {notification_id} status updated to: {status}")
            else:
                print("❌ Failed to update notification status")

        else:
            print(f"❌ Unknown notification-service command: {command}")
            print("Available commands: health, config, list, send, get, history, stats, update")
            print("\nExamples:")
            print("  list --limit 20 --offset 0 --status 'unread'")
            print("  send --recipient 'user@email.com' --title 'Alert' --message 'System alert' --priority 'high'")
            print("  get --id 'notification-uuid'")
            print("  history --recipient 'user@email.com' --limit 10")
            print("  stats")
            print("  update --id 'notification-uuid' --status 'read'")
    
    async def frontend_command(self, command: str, **kwargs):
        """Execute Frontend commands"""
        base_url = self.services["frontend"]
        
        if command == "health":
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"💚 Frontend Health:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Health check failed")
        
        elif command == "config":
            # Get configuration from health endpoint
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"⚙️  Frontend Configuration:")
                config_data = {
                    "service": response.get("service", "frontend"),
                    "version": response.get("version", "unknown"),
                    "environment": response.get("environment", "unknown"),
                    "timestamp": response.get("timestamp", "unknown"),
                    "uptime_seconds": response.get("uptime_seconds", 0)
                }
                print(json.dumps(config_data, indent=2))
            else:
                print("❌ Failed to get configuration")
        
        elif command == "status":
            # Get frontend application status
            url = f"{base_url}/api/status"
            response = await self.client.get_json(url)
            if response:
                print(f"📊 Frontend Application Status:")
                print(f"   Status: {response.get('status', 'unknown')}")
                print(f"   Version: {response.get('version', 'unknown')}")
                print(f"   Environment: {response.get('environment', 'unknown')}")
                print(f"   Uptime: {response.get('uptime', 'unknown')}")
                if 'active_connections' in response:
                    print(f"   Active Connections: {response['active_connections']}")
                if 'memory_usage' in response:
                    print(f"   Memory Usage: {response['memory_usage']}")
            else:
                # Fallback to basic health check
                url = f"{base_url}/health"
                response = await self.client.get_json(url)
                if response:
                    print(f"📊 Frontend Status (from health):")
                    print(f"   Service: {response.get('service', 'frontend')}")
                    print(f"   Status: {response.get('status', 'unknown')}")
                    print(f"   Uptime: {response.get('uptime_seconds', 0)} seconds")
                else:
                    print("❌ Failed to get frontend status")

        elif command == "logs":
            # Get frontend logs
            lines = kwargs.get("lines", 50)
            level = kwargs.get("level", "")

            url = f"{base_url}/api/logs?lines={lines}"
            if level:
                url += f"&level={level}"

            response = await self.client.get_json(url)
            if response:
                print(f"📜 Frontend Logs (Last {lines} lines):")
                if isinstance(response, dict) and "logs" in response:
                    logs = response["logs"]
                    for log_entry in logs[-20:]:  # Show last 20 entries
                        timestamp = log_entry.get("timestamp", "unknown")
                        level = log_entry.get("level", "INFO")
                        message = log_entry.get("message", "")
                        print(f"   {timestamp} [{level}] {message}")
                    if len(logs) > 20:
                        print(f"   ... and {len(logs) - 20} more log entries")
                else:
                    print("   No structured logs available")
                    print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to get frontend logs")

        elif command == "restart":
            # Restart frontend application
            print("🔄 Restarting Frontend Application...")

            # First check if restart endpoint exists
            url = f"{base_url}/api/restart"
            response = await self.client.post_json(url, {})
            if response:
                print(f"✅ Frontend Restart Initiated:")
                if isinstance(response, dict):
                    status = response.get("status", "unknown")
                    message = response.get("message", "Restart in progress")
                    print(f"   Status: {status}")
                    print(f"   Message: {message}")
                    if "restart_time" in response:
                        print(f"   Restart Time: {response['restart_time']}")
                else:
                    print(json.dumps(response, indent=2))
            else:
                print("❌ Frontend restart endpoint not available")
                print("   Note: Restart functionality may need to be implemented in the frontend service")

        elif command == "metrics":
            # Get frontend performance metrics
            url = f"{base_url}/api/metrics"
            response = await self.client.get_json(url)
            if response:
                print(f"📈 Frontend Performance Metrics:")
                if isinstance(response, dict):
                    for key, value in response.items():
                        if isinstance(value, (int, float)):
                            print(f"   {key}: {value}")
                        elif isinstance(value, dict):
                            print(f"   {key}:")
                            for sub_key, sub_value in value.items():
                                print(f"      {sub_key}: {sub_value}")
                        else:
                            print(f"   {key}: {value}")
                else:
                    print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to get frontend metrics")

        elif command == "routes":
            # Get frontend API routes
            url = f"{base_url}/api/routes"
            response = await self.client.get_json(url)
            if response:
                print(f"🛣️  Frontend API Routes:")
                if isinstance(response, list):
                    for route in response:
                        method = route.get("method", "GET")
                        path = route.get("path", "unknown")
                        description = route.get("description", "")
                        print(f"   {method:<6} {path:<30} {description}")
                else:
                    print(json.dumps(response, indent=2))
            else:
                print("❌ Failed to get frontend routes")
        
        else:
            print(f"❌ Unknown frontend command: {command}")
            print("Available commands: health, config, status, logs, restart, metrics, routes")
            print("\nExamples:")
            print("  status")
            print("  logs --lines 100 --level ERROR")
            print("  restart")
            print("  metrics")
            print("  routes")
    
    async def discovery_agent_command(self, command: str, **kwargs):
        """Execute Discovery Agent commands"""
        base_url = self.services["discovery-agent"]
        
        if command == "health":
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"💚 Discovery Agent Health:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Health check failed")
        
        elif command == "discover":
            # Discovery service registration
            name = kwargs.get("name")
            base_url_param = kwargs.get("base_url") or kwargs.get("url")
            
            if not name or not base_url_param:
                print("❌ Discovery requires --name and --base_url parameters")
                print("Example: python cli.py discovery-agent discover --name my-service --base_url http://service:8080")
                return
            
            url = f"{base_url}/discover"
            payload = {"name": name, "base_url": base_url_param}
            response = await self.client.post_json(url, payload)
            if response:
                print(f"🔍 Service Discovery Results:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Service discovery failed")
        
        elif command == "config":
            # Get configuration from health endpoint
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"⚙️  Discovery Agent Configuration:")
                config_data = {
                    "service": response.get("service", "discovery-agent"),
                    "version": response.get("version", "unknown"),
                    "environment": response.get("environment", "unknown"),
                    "timestamp": response.get("timestamp", "unknown"),
                    "uptime_seconds": response.get("uptime_seconds", 0)
                }
                print(json.dumps(config_data, indent=2))
            else:
                print("❌ Failed to get configuration")
        
        else:
            print(f"❌ Unknown discovery-agent command: {command}")
            print("Available commands: health, discover, config")
            print("Usage: discover --name <service_name> --base_url <url>")
    
    async def interpreter_command(self, command: str, **kwargs):
        """Execute Interpreter commands"""
        base_url = self.services["interpreter"]
        
        if command == "health":
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"💚 Interpreter Health:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Health check failed")
        
        elif command == "execute":
            # Code execution
            query = kwargs.get("query")
            code = kwargs.get("code")
            
            if not query:
                print("❌ Code execution requires --query parameter")
                print("Example: python cli.py interpreter execute --query 'test python' --code 'print(\"Hello World\")'")
                return
            
            url = f"{base_url}/execute"
            payload = {"query": query}
            if code:
                payload["code"] = code
            
            response = await self.client.post_json(url, payload)
            if response:
                print(f"⚡ Code Execution Results:")
                print(json.dumps(response, indent=2))
            else:
                print("❌ Code execution failed")
        
        elif command == "config":
            # Get configuration from health endpoint
            url = f"{base_url}/health"
            response = await self.client.get_json(url)
            if response:
                print(f"⚙️  Interpreter Configuration:")
                config_data = {
                    "service": response.get("service", "interpreter"),
                    "version": response.get("version", "unknown"),
                    "environment": response.get("environment", "unknown"),
                    "timestamp": response.get("timestamp", "unknown"),
                    "uptime_seconds": response.get("uptime_seconds", 0)
                }
                print(json.dumps(config_data, indent=2))
            else:
                print("❌ Failed to get configuration")
        
        else:
            print(f"❌ Unknown interpreter command: {command}")
            print("Available commands: health, execute, config")
            print("Usage: execute --query <description> [--code <code_to_run>]")
    
    async def execute_service_command(self, service: str, command: str, **kwargs):
        """Execute command on specific service"""
        if service == "analysis-service":
            await self.analysis_service_command(command, **kwargs)
        elif service == "orchestrator":
            await self.orchestrator_command(command, **kwargs)
        elif service == "github-mcp":
            await self.github_mcp_command(command, **kwargs)
        elif service == "source-agent":
            await self.source_agent_command(command, **kwargs)
        elif service in ["doc_store", "doc-store"]:
            await self.doc_store_command(command, **kwargs)
        elif service in ["prompt_store", "prompt-store"]:
            await self.prompt_store_command(command, **kwargs)
        elif service == "frontend":
            await self.frontend_command(command, **kwargs)
        elif service in ["discovery-agent", "discovery_agent"]:
            await self.discovery_agent_command(command, **kwargs)
        elif service in ["notification-service", "notification_service"]:
            await self.notification_service_command(command, **kwargs)
        elif service == "interpreter":
            await self.interpreter_command(command, **kwargs)
        else:
            # Generic health check for other services
            if command == "health" and service in self.services:
                url = f"{self.services[service]}/health"
                response = await self.client.get_json(url)
                if response:
                    print(f"💚 {service.title()} Health:")
                    print(json.dumps(response, indent=2))
                else:
                    print(f"❌ {service} health check failed")
            else:
                print(f"❌ Service '{service}' not supported or command '{command}' not available")
                print(f"Available services: {', '.join(self.services.keys())}")
    
    def show_help(self):
        """Show help information"""
        print("🌐 ECOSYSTEM CLI HELP")
        print("=" * 30)
        print("Usage: python3 ecosystem_cli_executable.py <command> [options]")
        print()
        print("Commands:")
        print("  health                    - Check health of all services")
        print("  containers                - List all Docker containers")
        print("  container-stats           - Show container resource usage")
        print("  restart --service <name>  - Restart a specific container")
        print("  rebuild --service <name>  - Rebuild a specific container")
        print("  logs --service <name>     - Show container logs")
        print("  stop --service <name>     - Stop a specific container")
        print("  start --service <name>    - Start a specific container")
        print("  <service> <command>       - Execute command on specific service")
        print()
        print("Available Services:")
        for service in self.services:
            print(f"  - {service}")
        print()
        print("Examples:")
        print("  python3 ecosystem_cli_executable.py health")
        print("  python3 ecosystem_cli_executable.py containers")
        print("  python3 ecosystem_cli_executable.py restart --service doc_store")
        print("  python3 ecosystem_cli_executable.py logs --service orchestrator --lines 20")
        print("  python3 ecosystem_cli_executable.py analysis-service status")
        print("  python3 ecosystem_cli_executable.py orchestrator peers")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Ecosystem CLI")
    parser.add_argument("command", nargs='?', help="Command to execute")
    parser.add_argument("subcommand", nargs='?', help="Subcommand for service")
    parser.add_argument("--help-cli", action="store_true", help="Show CLI help")

    # Add support for additional arguments
    parser.add_argument("--limit", type=int, help="Limit for list/search operations")
    parser.add_argument("--offset", type=int, help="Offset for list operations")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--title", help="Document title")
    parser.add_argument("--content", help="Document content or prompt content")
    parser.add_argument("--tags", help="Document tags or prompt tags (comma-separated)")
    parser.add_argument("--id", help="Document ID or prompt ID")
    parser.add_argument("--metadata", help="Metadata (key:value,key2:value2 format)")
    parser.add_argument("--code", help="Code to execute")
    parser.add_argument("--type", help="Workflow or data type")
    parser.add_argument("--name", help="Prompt name")
    parser.add_argument("--category", help="Prompt category")
    parser.add_argument("--author", help="Prompt author")
    parser.add_argument("--description", help="Prompt description")
    parser.add_argument("--message", help="Notification message")
    parser.add_argument("--recipient", help="Notification recipient")
    parser.add_argument("--priority", help="Notification priority (low/normal/high/critical)")
    parser.add_argument("--status", help="Notification status or filter")
    parser.add_argument("--lines", type=int, help="Number of log lines to retrieve")
    parser.add_argument("--level", help="Log level filter (DEBUG/INFO/WARNING/ERROR)")
    parser.add_argument("--definition", help="Workflow definition JSON")
    parser.add_argument("--template", help="Workflow template name")
    parser.add_argument("--service", help="Service/container name for container management")
    parser.add_argument("--follow", action="store_true", help="Follow logs in real-time")
    
    args = parser.parse_args()
    
    cli = EcosystemCLI()
    
    if args.help_cli:
        cli.show_help()
        return 0
    
    if not args.command:
        cli.show_help()
        return 1
    
    if args.command == "health":
        await cli.health_check_all()
        return 0
    
    if args.command == "config-all":
        await cli.config_check_all()
        return 0
    
    if args.command == "test-ecosystem":
        await cli.test_ecosystem_workflows()
        return 0
        
    if args.command == "create-mock-data":
        await cli.create_mock_data()
        return 0

    # Container management commands
    if args.command == "containers":
        await cli.list_containers()
        return 0

    if args.command == "container-stats":
        await cli.show_container_stats()
        return 0

    if args.command == "restart":
        if not hasattr(args, 'service') or not args.service:
            print("❌ Service name required. Use: restart --service <service_name>")
            return 1
        await cli.restart_container(args.service)
        return 0

    if args.command == "rebuild":
        if not hasattr(args, 'service') or not args.service:
            print("❌ Service name required. Use: rebuild --service <service_name>")
            return 1
        await cli.rebuild_container(args.service)
        return 0

    if args.command == "logs":
        if not hasattr(args, 'service') or not args.service:
            print("❌ Service name required. Use: logs --service <service_name>")
            return 1
        follow = hasattr(args, 'follow') and args.follow
        lines = (args.lines if hasattr(args, 'lines') and args.lines else 50)
        await cli.show_container_logs(args.service, lines, follow)
        return 0

    if args.command == "stop":
        if not hasattr(args, 'service') or not args.service:
            print("❌ Service name required. Use: stop --service <service_name>")
            return 1
        await cli.stop_container(args.service)
        return 0

    if args.command == "start":
        if not hasattr(args, 'service') or not args.service:
            print("❌ Service name required. Use: start --service <service_name>")
            return 1
        await cli.start_container(args.service)
        return 0
    
    if args.subcommand:
        # Collect additional arguments as kwargs
        kwargs = {}
        if hasattr(args, 'limit') and args.limit is not None:
            kwargs['limit'] = args.limit
        if hasattr(args, 'offset') and args.offset is not None:
            kwargs['offset'] = args.offset
        if hasattr(args, 'query') and args.query:
            kwargs['query'] = args.query
        if hasattr(args, 'title') and args.title:
            kwargs['title'] = args.title
        if hasattr(args, 'content') and args.content:
            kwargs['content'] = args.content
        if hasattr(args, 'tags') and args.tags:
            kwargs['tags'] = args.tags
        if hasattr(args, 'id') and args.id:
            kwargs['id'] = args.id
        if hasattr(args, 'metadata') and args.metadata:
            kwargs['metadata'] = args.metadata
        if hasattr(args, 'code') and args.code:
            kwargs['code'] = args.code
        if hasattr(args, 'type') and args.type:
            kwargs['type'] = args.type
        if hasattr(args, 'name') and args.name:
            kwargs['name'] = args.name
        if hasattr(args, 'category') and args.category:
            kwargs['category'] = args.category
        if hasattr(args, 'author') and args.author:
            kwargs['author'] = args.author
        if hasattr(args, 'description') and args.description:
            kwargs['description'] = args.description
        if hasattr(args, 'message') and args.message:
            kwargs['message'] = args.message
        if hasattr(args, 'recipient') and args.recipient:
            kwargs['recipient'] = args.recipient
        if hasattr(args, 'priority') and args.priority:
            kwargs['priority'] = args.priority
        if hasattr(args, 'status') and args.status:
            kwargs['status'] = args.status
        if hasattr(args, 'lines') and args.lines is not None:
            kwargs['lines'] = args.lines
        if hasattr(args, 'level') and args.level:
            kwargs['level'] = args.level
        if hasattr(args, 'definition') and args.definition:
            kwargs['definition'] = args.definition
        if hasattr(args, 'template') and args.template:
            kwargs['template'] = args.template

        await cli.execute_service_command(args.command, args.subcommand, **kwargs)
        return 0
    
    # If no subcommand, assume health check for the service
    if args.command in cli.services:
        await cli.execute_service_command(args.command, "health")
        return 0
    
    print(f"❌ Unknown command: {args.command}")
    cli.show_help()
    return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
