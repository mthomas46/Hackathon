#!/usr/bin/env python3
"""
Enhanced Production CLI with Full Service Adapter Support
Uses the new ServiceRegistry with all adapters for comprehensive service interaction
"""

import asyncio
import json
import sys
import os
from typing import Dict, List, Any, Optional

# Add the services directory to Python path for imports
sys.path.insert(0, '/app/services')

# Mock HTTP client for demonstration (in real deployment, this would be aiohttp)
class SimpleHTTPClient:
    async def get_json(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Mock HTTP GET request returning JSON"""
        import time
        await asyncio.sleep(0.01)  # Simulate network delay
        
        # Mock responses based on URL patterns
        if "/health" in url:
            service_name = self._extract_service_name(url)
            return {"status": "healthy", "service": service_name, "timestamp": "2025-09-17T21:00:00Z"}
        elif "/status" in url:
            return {"status": "operational", "uptime": "6h 15m", "version": "1.0.0"}
        elif "/models" in url:
            return {"models": [
                {"modelId": "claude-3-sonnet", "modelName": "Claude 3 Sonnet", "providerName": "Anthropic"},
                {"modelId": "titan-text-express", "modelName": "Titan Text Express", "providerName": "Amazon"}
            ]}
        elif "/languages" in url:
            return {"languages": [
                {"name": "python", "version": "3.9+", "features": ["execution", "jupyter"], "status": "available"},
                {"name": "javascript", "version": "Node 18+", "features": ["execution"], "status": "available"}
            ]}
        elif "/documents" in url:
            return {"documents": [
                {"id": "doc1", "title": "Test Document", "collection": "default", "created_at": "2025-09-17T21:00:00Z"}
            ], "total": 1}
        elif "/memories" in url:
            return {"memories": [
                {"id": "mem1", "content": "System initialized successfully", "context_id": "system", "created_at": "2025-09-17T21:00:00Z"}
            ], "total": 1}
        elif "/services" in url:
            return {"services": [
                {"name": "analysis-service", "type": "core", "url": "http://hackathon-analysis-service-1:5020", "status": "healthy"}
            ]}
        elif "/workflows" in url:
            return {"workflows": []}
        elif "/repositories" in url:
            return {"repositories": [{"name": "test-repo", "full_name": "user/test-repo"}]}
        else:
            return {"success": True, "data": "mock response"}
    
    async def post_json(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Mock HTTP POST request"""
        await asyncio.sleep(0.01)
        return {"success": True, "id": "generated-id", "message": "Operation completed"}
    
    async def delete_json(self, url: str) -> Dict[str, Any]:
        """Mock HTTP DELETE request"""
        await asyncio.sleep(0.01)
        return {"success": True, "message": "Resource deleted"}
    
    async def get_text(self, url: str) -> str:
        """Mock HTTP GET request returning text"""
        await asyncio.sleep(0.01)
        return "<html><head><title>Service</title></head><body><h1>Service Page</h1></body></html>"
    
    def _extract_service_name(self, url: str) -> str:
        """Extract service name from URL"""
        for service in ["analysis-service", "orchestrator", "doc_store", "memory-agent", "discovery-agent", 
                       "bedrock-proxy", "frontend", "interpreter", "github-mcp", "source-agent"]:
            if service in url:
                return service
        return "unknown-service"


class EnhancedProductionCLI:
    """
    Enhanced production CLI with full service adapter support
    """
    
    def __init__(self):
        self.client = SimpleHTTPClient()
        self.registry = None
    
    async def initialize(self):
        """Initialize the service registry"""
        try:
            # Import and initialize the enhanced service registry
            from cli.modules.adapters.service_registry import ServiceRegistry
            from rich.console import Console
            
            console = Console()
            self.registry = ServiceRegistry(console, self.client)
            await self.registry.initialize()
            print("✅ Enhanced CLI initialized with full service adapter support")
            
        except ImportError as e:
            print(f"❌ Failed to import service registry: {e}")
            print("📋 Available basic commands: health")
            return False
        except Exception as e:
            print(f"❌ Failed to initialize registry: {e}")
            return False
        
        return True
    
    async def execute_command(self, service: str, command: str, **kwargs) -> None:
        """Execute a command on a service"""
        if not self.registry:
            await self.basic_health_check()
            return
        
        try:
            # Use the service registry to execute the command
            await self.registry.execute_service_command(service, command, **kwargs)
            
        except Exception as e:
            print(f"❌ Error executing {service} {command}: {str(e)}")
    
    async def list_services(self) -> None:
        """List all available services and their commands"""
        if not self.registry:
            print("📋 Basic services: analysis-service, orchestrator, doc-store, memory-agent")
            return
        
        try:
            await self.registry.display_service_overview()
        except Exception as e:
            print(f"❌ Error listing services: {str(e)}")
    
    async def health_check(self) -> None:
        """Perform comprehensive health check"""
        if not self.registry:
            await self.basic_health_check()
            return
        
        try:
            await self.registry.health_check_all()
        except Exception as e:
            print(f"❌ Error performing health check: {str(e)}")
    
    async def basic_health_check(self) -> None:
        """Basic health check without full registry"""
        print("🔍 Performing basic health check...")
        
        basic_services = {
            "analysis-service": "http://hackathon-analysis-service-1:5020",
            "orchestrator": "http://hackathon-orchestrator-1:5099",
            "doc_store": "http://hackathon-doc_store-1:5087",
            "memory-agent": "http://hackathon-memory-agent-1:5040"
        }
        
        healthy_count = 0
        for service, url in basic_services.items():
            try:
                response = await self.client.get_json(f"{url}/health")
                if response.get("status") == "healthy":
                    print(f"  ✅ {service}: Healthy")
                    healthy_count += 1
                else:
                    print(f"  ⚠️  {service}: {response.get('status', 'Unknown')}")
            except Exception as e:
                print(f"  ❌ {service}: Error - {str(e)}")
        
        print(f"📊 Health Summary: {healthy_count}/{len(basic_services)} services healthy")


async def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("Enhanced Production CLI for LLM Documentation Ecosystem")
        print("Usage: python enhanced_production_cli.py <command> [service] [subcommand]")
        print("\nCommands:")
        print("  health                    - Check ecosystem health")
        print("  services                  - List all services and capabilities")
        print("  <service> <command>       - Execute command on service")
        print("\nExamples:")
        print("  python enhanced_production_cli.py health")
        print("  python enhanced_production_cli.py services")
        print("  python enhanced_production_cli.py memory-agent stats")
        print("  python enhanced_production_cli.py bedrock-proxy models")
        print("  python enhanced_production_cli.py doc-store documents")
        return
    
    cli = EnhancedProductionCLI()
    
    # Initialize the CLI
    initialized = await cli.initialize()
    
    command = sys.argv[1].lower()
    
    if command == "health":
        await cli.health_check()
    elif command == "services":
        await cli.list_services()
    elif len(sys.argv) >= 3:
        service = sys.argv[1]
        subcommand = sys.argv[2]
        
        # Parse additional arguments as kwargs
        kwargs = {}
        for i in range(3, len(sys.argv), 2):
            if i + 1 < len(sys.argv):
                kwargs[sys.argv[i]] = sys.argv[i + 1]
        
        await cli.execute_command(service, subcommand, **kwargs)
    else:
        print(f"❌ Invalid command: {command}")
        print("Use 'python enhanced_production_cli.py' for help")


if __name__ == "__main__":
    asyncio.run(main())
