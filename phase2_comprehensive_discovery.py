#!/usr/bin/env python3
"""
Phase 2: Comprehensive Service Discovery Implementation

This script implements Phase 2 of the Discovery Agent expansion plan:
- Test discovery against all 15+ running services
- Create comprehensive tool catalog
- Validate tool functionality and performance
"""

import asyncio
import aiohttp
import json
import time
from pathlib import Path
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class ComprehensiveServiceDiscovery:
    """Comprehensive service discovery across the entire ecosystem"""
    
    def __init__(self):
        self.discovered_tools = {}
        self.service_catalog = {}
        self.performance_metrics = {}
        
        # All services from the running Docker ecosystem
        self.services = {
            "analysis-service": {
                "url": "http://localhost:5020",
                "openapi_path": "/openapi.json",
                "category": "analysis",
                "priority": 1
            },
            "source-agent": {
                "url": "http://localhost:5000", 
                "openapi_path": "/openapi.json",
                "category": "integration",
                "priority": 1
            },
            "memory-agent": {
                "url": "http://localhost:5040",
                "openapi_path": "/openapi.json", 
                "category": "storage",
                "priority": 1
            },
            "prompt_store": {
                "url": "http://localhost:5110",
                "openapi_path": "/openapi.json",
                "category": "ai",
                "priority": 1
            },
            "github-mcp": {
                "url": "http://localhost:5072",
                "openapi_path": "/openapi.json",
                "category": "integration", 
                "priority": 2
            },
            "interpreter": {
                "url": "http://localhost:5120",
                "openapi_path": "/openapi.json",
                "category": "execution",
                "priority": 2
            },
            "secure-analyzer": {
                "url": "http://localhost:5070",
                "openapi_path": "/openapi.json",
                "category": "security",
                "priority": 1
            },
            "summarizer-hub": {
                "url": "http://localhost:5160",
                "openapi_path": "/openapi.json",
                "category": "ai",
                "priority": 2
            },
            "doc_store": {
                "url": "http://localhost:5087",
                "openapi_path": "/openapi.json",
                "category": "storage",
                "priority": 1
            },
            "orchestrator": {
                "url": "http://localhost:5099",
                "openapi_path": "/openapi.json",
                "category": "orchestration",
                "priority": 1
            },
            "architecture-digitizer": {
                "url": "http://localhost:5105",
                "openapi_path": "/openapi.json",
                "category": "analysis",
                "priority": 3
            },
            "log-collector": {
                "url": "http://localhost:5080",
                "openapi_path": "/openapi.json",
                "category": "monitoring",
                "priority": 2
            },
            "notification-service": {
                "url": "http://localhost:5095",
                "openapi_path": "/openapi.json",
                "category": "communication",
                "priority": 3
            },
            "code-analyzer": {
                "url": "http://localhost:5065",
                "openapi_path": "/openapi.json",
                "category": "analysis",
                "priority": 3
            },
            "discovery-agent": {
                "url": "http://localhost:5045",
                "openapi_path": "/openapi.json",
                "category": "discovery",
                "priority": 1
            }
        }
    
    async def test_service_health(self, service_name: str, service_config: Dict) -> Dict[str, Any]:
        """Test if a service is healthy and responsive"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                # Test health endpoint
                health_url = f"{service_config['url']}/health"
                async with session.get(health_url) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        response_time = time.time() - start_time
                        
                        return {
                            "status": "healthy",
                            "response_time": response_time,
                            "health_data": health_data,
                            "service_url": service_config['url']
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"Health check returned {response.status}",
                            "response_time": time.time() - start_time
                        }
        
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e),
                "response_time": time.time() - start_time
            }
    
    async def discover_service_openapi(self, service_name: str, service_config: Dict) -> Dict[str, Any]:
        """Discover OpenAPI specification for a service"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                openapi_url = f"{service_config['url']}{service_config['openapi_path']}"
                
                async with session.get(openapi_url) as response:
                    if response.status == 200:
                        openapi_spec = await response.json()
                        
                        # Extract key information
                        info = {
                            "title": openapi_spec.get("info", {}).get("title", service_name),
                            "version": openapi_spec.get("info", {}).get("version", "unknown"),
                            "description": openapi_spec.get("info", {}).get("description", ""),
                            "paths": list(openapi_spec.get("paths", {}).keys()),
                            "endpoints_count": len(openapi_spec.get("paths", {})),
                            "components": list(openapi_spec.get("components", {}).get("schemas", {}).keys()) if openapi_spec.get("components") else [],
                            "full_spec": openapi_spec
                        }
                        
                        return {"success": True, "data": info}
                    else:
                        return {"success": False, "error": f"OpenAPI returned {response.status}"}
                        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def analyze_service_endpoints(self, service_name: str, openapi_data: Dict) -> List[Dict[str, Any]]:
        """Analyze service endpoints to identify potential LangGraph tools"""
        if not openapi_data.get("success"):
            return []
        
        spec = openapi_data["data"]["full_spec"]
        paths = spec.get("paths", {})
        tools = []
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE"]:
                    
                    # Categorize the tool based on path and operation
                    category = self._categorize_endpoint(path, method, details)
                    
                    tool = {
                        "name": f"{service_name}_{path.replace('/', '_').replace('-', '_')}_{method}",
                        "service": service_name,
                        "path": path,
                        "method": method.upper(),
                        "category": category,
                        "summary": details.get("summary", ""),
                        "description": details.get("description", ""),
                        "parameters": self._extract_parameters(details),
                        "responses": list(details.get("responses", {}).keys()),
                        "langraph_ready": self._assess_langraph_readiness(details)
                    }
                    
                    tools.append(tool)
        
        return tools
    
    def _categorize_endpoint(self, path: str, method: str, details: Dict) -> str:
        """Categorize an endpoint for LangGraph tool classification"""
        path_lower = path.lower()
        summary_lower = details.get("summary", "").lower()
        
        # Analysis tools
        if any(word in path_lower for word in ["analyze", "analysis", "process", "validate"]):
            return "analysis"
        
        # CRUD operations
        if method.upper() == "GET" and not any(word in path_lower for word in ["search", "query"]):
            return "read"
        elif method.upper() == "POST":
            return "create"
        elif method.upper() == "PUT":
            return "update"
        elif method.upper() == "DELETE":
            return "delete"
        
        # Search and query
        if any(word in path_lower for word in ["search", "query", "find"]):
            return "search"
        
        # Management
        if any(word in path_lower for word in ["manage", "admin", "config"]):
            return "management"
        
        # Integration
        if any(word in path_lower for word in ["github", "jira", "confluence", "external"]):
            return "integration"
        
        # Security
        if any(word in path_lower for word in ["secure", "auth", "permission", "scan"]):
            return "security"
        
        # Storage
        if any(word in path_lower for word in ["store", "save", "retrieve", "document"]):
            return "storage"
        
        return "utility"
    
    def _extract_parameters(self, endpoint_details: Dict) -> List[Dict[str, Any]]:
        """Extract parameter information for LangGraph tool generation"""
        parameters = []
        
        # Path parameters
        for param in endpoint_details.get("parameters", []):
            parameters.append({
                "name": param.get("name"),
                "type": param.get("schema", {}).get("type", "string"),
                "required": param.get("required", False),
                "location": param.get("in", "query"),
                "description": param.get("description", "")
            })
        
        # Request body parameters
        request_body = endpoint_details.get("requestBody", {})
        if request_body:
            content = request_body.get("content", {})
            for content_type, schema_info in content.items():
                if "application/json" in content_type:
                    schema = schema_info.get("schema", {})
                    if schema.get("properties"):
                        for prop_name, prop_details in schema["properties"].items():
                            parameters.append({
                                "name": prop_name,
                                "type": prop_details.get("type", "string"),
                                "required": prop_name in schema.get("required", []),
                                "location": "body",
                                "description": prop_details.get("description", "")
                            })
        
        return parameters
    
    def _assess_langraph_readiness(self, endpoint_details: Dict) -> Dict[str, Any]:
        """Assess how ready an endpoint is for LangGraph tool conversion"""
        
        # Check for clear parameters
        has_parameters = len(endpoint_details.get("parameters", [])) > 0 or endpoint_details.get("requestBody") is not None
        
        # Check for clear responses
        responses = endpoint_details.get("responses", {})
        has_success_response = "200" in responses or "201" in responses
        
        # Check for documentation
        has_description = bool(endpoint_details.get("description") or endpoint_details.get("summary"))
        
        readiness_score = 0
        if has_parameters: readiness_score += 3
        if has_success_response: readiness_score += 3
        if has_description: readiness_score += 2
        
        # Additional points for clear operation types
        if endpoint_details.get("operationId"):
            readiness_score += 2
        
        return {
            "score": readiness_score,
            "max_score": 10,
            "percentage": (readiness_score / 10) * 100,
            "ready": readiness_score >= 6,
            "factors": {
                "has_parameters": has_parameters,
                "has_success_response": has_success_response,
                "has_description": has_description,
                "has_operation_id": bool(endpoint_details.get("operationId"))
            }
        }
    
    async def run_comprehensive_discovery(self) -> Dict[str, Any]:
        """Run comprehensive discovery across all services"""
        print("🔍 PHASE 2: COMPREHENSIVE SERVICE DISCOVERY")
        print("=" * 60)
        
        discovery_results = {
            "timestamp": datetime.now().isoformat(),
            "services_tested": len(self.services),
            "healthy_services": 0,
            "total_tools_discovered": 0,
            "services": {},
            "summary": {}
        }
        
        # Test each service
        for service_name, service_config in self.services.items():
            print(f"\n🔍 Discovering {service_name}...")
            print("-" * 40)
            
            # Test health
            health_result = await self.test_service_health(service_name, service_config)
            print(f"Health: {health_result['status']} ({health_result['response_time']:.2f}s)")
            
            service_result = {
                "config": service_config,
                "health": health_result,
                "openapi": None,
                "tools": [],
                "summary": {}
            }
            
            if health_result["status"] == "healthy":
                discovery_results["healthy_services"] += 1
                
                # Discover OpenAPI
                openapi_result = await self.discover_service_openapi(service_name, service_config)
                service_result["openapi"] = openapi_result
                
                if openapi_result["success"]:
                    endpoints_count = openapi_result["data"]["endpoints_count"]
                    print(f"OpenAPI: ✅ {endpoints_count} endpoints found")
                    
                    # Analyze endpoints for tools
                    tools = await self.analyze_service_endpoints(service_name, openapi_result)
                    service_result["tools"] = tools
                    
                    # Filter LangGraph-ready tools
                    ready_tools = [t for t in tools if t["langraph_ready"]["ready"]]
                    
                    print(f"Tools: 📋 {len(tools)} total, {len(ready_tools)} LangGraph-ready")
                    
                    discovery_results["total_tools_discovered"] += len(tools)
                    
                    # Create summary
                    service_result["summary"] = {
                        "endpoints_total": endpoints_count,
                        "tools_total": len(tools),
                        "tools_langraph_ready": len(ready_tools),
                        "categories": list(set(t["category"] for t in tools)),
                        "average_readiness_score": sum(t["langraph_ready"]["score"] for t in tools) / len(tools) if tools else 0
                    }
                    
                    # Show top tools
                    if ready_tools:
                        print("Top LangGraph-ready tools:")
                        for tool in ready_tools[:3]:
                            print(f"  📋 {tool['name']}: {tool['category']} ({tool['langraph_ready']['percentage']:.0f}%)")
                
                else:
                    print(f"OpenAPI: ❌ {openapi_result['error']}")
            
            else:
                print(f"❌ Service unhealthy: {health_result.get('error', 'Unknown error')}")
            
            discovery_results["services"][service_name] = service_result
        
        # Create summary
        discovery_results["summary"] = {
            "services_healthy": discovery_results["healthy_services"],
            "services_total": discovery_results["services_tested"],
            "health_percentage": (discovery_results["healthy_services"] / discovery_results["services_tested"]) * 100,
            "tools_discovered": discovery_results["total_tools_discovered"],
            "avg_tools_per_service": discovery_results["total_tools_discovered"] / discovery_results["healthy_services"] if discovery_results["healthy_services"] > 0 else 0
        }
        
        return discovery_results
    
    async def save_discovery_results(self, results: Dict[str, Any]):
        """Save discovery results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"discovery_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to {filename}")
        
        # Also create a summary report
        summary_filename = f"discovery_summary_{timestamp}.md"
        await self.create_summary_report(results, summary_filename)
    
    async def create_summary_report(self, results: Dict[str, Any], filename: str):
        """Create a markdown summary report"""
        
        report = f"""# 🔍 Phase 2: Comprehensive Service Discovery Report

**Generated:** {results['timestamp']}

## 📊 Summary

- **Services Tested:** {results['summary']['services_total']}
- **Services Healthy:** {results['summary']['services_healthy']} ({results['summary']['health_percentage']:.1f}%)
- **Total Tools Discovered:** {results['summary']['tools_discovered']}
- **Average Tools per Service:** {results['summary']['avg_tools_per_service']:.1f}

## 🎯 Service Details

"""
        
        for service_name, service_data in results["services"].items():
            health_status = service_data["health"]["status"]
            emoji = "✅" if health_status == "healthy" else "❌"
            
            report += f"""### {emoji} {service_name}

- **Status:** {health_status}
- **URL:** {service_data['config']['url']}
- **Category:** {service_data['config']['category']}
- **Response Time:** {service_data['health']['response_time']:.2f}s
"""
            
            if service_data.get("summary"):
                summary = service_data["summary"]
                report += f"""- **Endpoints:** {summary['endpoints_total']}
- **Tools Discovered:** {summary['tools_total']}
- **LangGraph Ready:** {summary['tools_langraph_ready']}
- **Categories:** {', '.join(summary['categories'])}
- **Avg Readiness:** {summary['average_readiness_score']:.1f}/10

"""
            else:
                report += f"- **Error:** {service_data['health'].get('error', 'Unknown')}\n\n"
        
        report += """## 🚀 Next Steps

1. **Implement discovered tools** in LangGraph workflows
2. **Enhance tool readiness** for services with low scores
3. **Create tool registry** for persistent storage
4. **Add security scanning** using secure-analyzer
5. **Implement monitoring** using log-collector

"""
        
        with open(filename, 'w') as f:
            f.write(report)
        
        print(f"📋 Summary report saved to {filename}")

async def main():
    """Main execution function"""
    print("🚀 Starting Phase 2: Comprehensive Service Discovery")
    print("This will test all services and create a comprehensive tool catalog")
    
    discovery = ComprehensiveServiceDiscovery()
    
    try:
        # Run discovery
        results = await discovery.run_comprehensive_discovery()
        
        # Save results
        await discovery.save_discovery_results(results)
        
        # Print final summary
        print("\n🎉 PHASE 2 DISCOVERY COMPLETE!")
        print("=" * 40)
        print(f"✅ Services Healthy: {results['summary']['services_healthy']}/{results['summary']['services_total']}")
        print(f"🛠️ Tools Discovered: {results['summary']['tools_discovered']}")
        print(f"📊 Health Rate: {results['summary']['health_percentage']:.1f}%")
        
        if results['summary']['tools_discovered'] > 0:
            print(f"\n🎯 Ready to proceed to Phase 3: Orchestrator Integration")
        else:
            print(f"\n⚠️ No tools discovered. Check service connectivity.")
        
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
