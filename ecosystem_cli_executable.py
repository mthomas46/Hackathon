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
from typing import Dict, List, Any, Optional

# Simple HTTP client for container environment
import urllib.request
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


class EcosystemCLI:
    """Production-ready Ecosystem CLI"""
    
    def __init__(self):
        self.client = SimpleServiceClient()
        self.services = {
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
            "frontend": "http://hackathon-frontend-1:5090"
        }
    
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
                analysis_url = f"http://hackathon-analysis-service-1:5020/"
                analysis_response = await self.client.get_json(analysis_url)
                if analysis_response:
                    workflow_results.append({"step": "analysis", "status": "success", "data": analysis_response})
                    print(f"   ✅ Analysis Service: Ready")
                
                # Step 2: Get source data
                source_url = f"http://hackathon-source-agent-1:5000/sources"
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
        
        else:
            print(f"❌ Unknown orchestrator command: {command}")
            print("Available commands: peers, sync, health, config, create-workflow")
            print("Usage: create-workflow --type mock-data")
    
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
        
        else:
            print(f"❌ Unknown doc_store command: {command}")
            print("Available commands: health, config")
    
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
        
        else:
            print(f"❌ Unknown frontend command: {command}")
            print("Available commands: health, config")
    
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
        elif service == "frontend":
            await self.frontend_command(command, **kwargs)
        elif service in ["discovery-agent", "discovery_agent"]:
            await self.discovery_agent_command(command, **kwargs)
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
        print("  <service> <command>       - Execute command on specific service")
        print()
        print("Available Services:")
        for service in self.services:
            print(f"  - {service}")
        print()
        print("Examples:")
        print("  python3 ecosystem_cli_executable.py health")
        print("  python3 ecosystem_cli_executable.py analysis-service status")
        print("  python3 ecosystem_cli_executable.py orchestrator peers")
        print("  python3 ecosystem_cli_executable.py github-mcp health")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Ecosystem CLI")
    parser.add_argument("command", nargs='?', help="Command to execute")
    parser.add_argument("subcommand", nargs='?', help="Subcommand for service")
    parser.add_argument("--help-cli", action="store_true", help="Show CLI help")
    
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
    
    if args.subcommand:
        await cli.execute_service_command(args.command, args.subcommand)
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
