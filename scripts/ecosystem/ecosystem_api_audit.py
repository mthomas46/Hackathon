#!/usr/bin/env python3
"""
Ecosystem API Audit - Identify gaps between available endpoints and CLI capabilities
Also tests configuration viewing across all services
"""

import subprocess
import json
import sys
import time
from typing import Dict, List, Any, Tuple, Optional


class EcosystemAPIAuditor:
    """
    Comprehensive auditor for ecosystem APIs vs CLI capabilities
    """
    
    def __init__(self):
        self.services = {
            "analysis-service": {"port": "5020", "container": "hackathon-analysis-service-1"},
            "orchestrator": {"port": "5099", "container": "hackathon-orchestrator-1"},
            "doc_store": {"port": "5087", "container": "hackathon-doc_store-1"},
            "memory-agent": {"port": "5040", "container": "hackathon-memory-agent-1"},
            "discovery-agent": {"port": "5045", "container": "hackathon-discovery-agent-1"},
            "bedrock-proxy": {"port": "7090", "container": "hackathon-bedrock-proxy-1"},
            "frontend": {"port": "3000", "container": "hackathon-frontend-1"},
            "interpreter": {"port": "5120", "container": "hackathon-interpreter-1"},
            "github-mcp": {"port": "5072", "container": "hackathon-github-mcp-1"},
            "source-agent": {"port": "5000", "container": "hackathon-source-agent-1"},
            "prompt_store": {"port": "5110", "container": "hackathon-prompt_store-1"},
            "architecture-digitizer": {"port": "5030", "container": "hackathon-architecture-digitizer-1"},
            "secure-analyzer": {"port": "5060", "container": "hackathon-secure-analyzer-1"}
        }
        self.audit_results = {}
        self.cli_capabilities = {}
        self.gaps = {}
    
    def test_endpoint(self, service: str, endpoint: str, method: str = "GET") -> Tuple[bool, str, Optional[Dict]]:
        """Test a specific API endpoint"""
        container = self.services[service]["container"]
        port = self.services[service]["port"]
        url = f"http://{container}:{port}{endpoint}"
        
        try:
            if method == "GET":
                result = subprocess.run(
                    ["curl", "-s", "-w", "%{http_code}", url],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            elif method == "POST":
                result = subprocess.run(
                    ["curl", "-s", "-w", "%{http_code}", "-X", "POST", 
                     "-H", "Content-Type: application/json", "-d", "{}", url],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            else:
                return False, f"Unsupported method: {method}", None
            
            # Extract HTTP status code (last 3 characters)
            if len(result.stdout) >= 3:
                status_code = result.stdout[-3:]
                response_body = result.stdout[:-3]
            else:
                status_code = "000"
                response_body = result.stdout
            
            success = status_code.startswith("2")  # 2xx status codes
            
            # Try to parse JSON response
            parsed_response = None
            if response_body.strip():
                try:
                    parsed_response = json.loads(response_body)
                except json.JSONDecodeError:
                    pass
            
            return success, status_code, parsed_response
            
        except subprocess.TimeoutExpired:
            return False, "timeout", None
        except Exception as e:
            return False, f"error: {str(e)}", None
    
    def discover_endpoints(self, service: str) -> List[str]:
        """Discover available endpoints for a service"""
        print(f"\n🔍 Discovering endpoints for {service}")
        
        # Common endpoints to test
        common_endpoints = [
            "/",
            "/health",
            "/status", 
            "/config",
            "/api/config",
            "/info",
            "/docs",
            "/openapi.json",
            "/metrics",
            "/ready",
            "/version"
        ]
        
        # Service-specific endpoints
        service_specific = {
            "analysis-service": ["/analyze", "/analysis", "/api/analyze", "/reports", "/models"],
            "orchestrator": ["/workflows", "/peers", "/registry", "/sync", "/api/workflows"],
            "doc_store": ["/documents", "/collections", "/search", "/api/documents", "/stats"],
            "memory-agent": ["/memories", "/contexts", "/api/memories", "/store", "/recall"],
            "discovery-agent": ["/services", "/discover", "/topology", "/register", "/api/services"],
            "bedrock-proxy": ["/models", "/chat/completions", "/completions", "/embeddings", "/test"],
            "frontend": ["/api/status", "/api/services", "/static", "/assets"],
            "interpreter": ["/execute", "/languages", "/sessions", "/api/execute", "/run"],
            "github-mcp": ["/repositories", "/repos", "/api/repos", "/github", "/webhook"],
            "source-agent": ["/sources", "/files", "/process", "/api/sources", "/upload"],
            "prompt_store": ["/prompts", "/categories", "/templates", "/api/prompts", "/search"],
            "architecture-digitizer": ["/digitize", "/analyze", "/api/digitize", "/models"],
            "secure-analyzer": ["/scan", "/analyze", "/vulnerabilities", "/api/scan", "/report"]
        }
        
        all_endpoints = common_endpoints + service_specific.get(service, [])
        discovered = []
        
        for endpoint in all_endpoints:
            success, status, response = self.test_endpoint(service, endpoint)
            
            result = {
                "endpoint": endpoint,
                "success": success,
                "status": status,
                "has_data": response is not None,
                "response_type": type(response).__name__ if response else "none"
            }
            
            if success:
                print(f"  ✅ {endpoint} ({status})")
                discovered.append(result)
            elif status == "404":
                print(f"  ❌ {endpoint} (404)")
            elif status.startswith("4") or status.startswith("5"):
                print(f"  ⚠️  {endpoint} ({status})")
                discovered.append(result)  # Include error responses for analysis
            else:
                print(f"  💔 {endpoint} ({status})")
        
        return discovered
    
    def test_cli_capabilities(self, service: str) -> List[str]:
        """Test what CLI commands are available for a service"""
        print(f"\n🔧 Testing CLI capabilities for {service}")
        
        # Map service names to CLI names
        cli_service_map = {
            "analysis-service": "analysis-service",
            "orchestrator": "orchestrator", 
            "doc_store": ["doc-store", "doc_store"],  # Try both variants
            "memory-agent": "memory-agent",
            "discovery-agent": "discovery-agent",
            "bedrock-proxy": "bedrock-proxy",
            "frontend": "frontend",
            "interpreter": "interpreter",
            "github-mcp": "github-mcp",
            "source-agent": "source-agent",
            "prompt_store": "prompt_store",
            "architecture-digitizer": "architecture-digitizer",
            "secure-analyzer": "secure-analyzer"
        }
        
        # Commands to test
        test_commands = ["health", "status", "config", "info", "help", "stats", "version"]
        
        cli_names = cli_service_map.get(service, [service])
        if isinstance(cli_names, str):
            cli_names = [cli_names]
        
        available_commands = []
        
        for cli_name in cli_names:
            for command in test_commands:
                try:
                    result = subprocess.run(
                        [sys.executable, "/tmp/ecosystem-cli-fixed.py", cli_name, command],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        print(f"  ✅ {cli_name} {command}")
                        available_commands.append(f"{cli_name} {command}")
                    else:
                        # Check if it's a "not supported" vs actual error
                        if "not supported" in result.stdout.lower():
                            print(f"  ❌ {cli_name} {command} (not supported)")
                        else:
                            print(f"  ⚠️  {cli_name} {command} (error)")
                            
                except Exception as e:
                    print(f"  💔 {cli_name} {command} (exception: {str(e)})")
        
        return available_commands
    
    def analyze_config_endpoints(self, service: str) -> Dict[str, Any]:
        """Specifically analyze configuration viewing capabilities"""
        print(f"\n⚙️  Analyzing config capabilities for {service}")
        
        config_endpoints = [
            "/config",
            "/api/config", 
            "/configuration",
            "/settings",
            "/api/settings",
            "/info",
            "/version",
            "/status"
        ]
        
        config_results = {
            "service": service,
            "config_endpoints": [],
            "cli_config_access": False,
            "config_data_available": False
        }
        
        # Test API endpoints
        for endpoint in config_endpoints:
            success, status, response = self.test_endpoint(service, endpoint)
            
            if success and response:
                config_results["config_endpoints"].append({
                    "endpoint": endpoint,
                    "status": status,
                    "has_config_data": self._contains_config_data(response)
                })
                
                if self._contains_config_data(response):
                    config_results["config_data_available"] = True
                    print(f"  ✅ {endpoint} has config data")
        
        # Test CLI config access
        cli_service_map = {
            "analysis-service": "analysis-service",
            "orchestrator": "orchestrator",
            "doc_store": "doc-store",
            "memory-agent": "memory-agent", 
            "discovery-agent": "discovery-agent",
            "bedrock-proxy": "bedrock-proxy",
            "frontend": "frontend",
            "interpreter": "interpreter",
            "github-mcp": "github-mcp",
            "source-agent": "source-agent",
            "prompt_store": "prompt_store",
            "architecture-digitizer": "architecture-digitizer",
            "secure-analyzer": "secure-analyzer"
        }
        
        cli_name = cli_service_map.get(service, service)
        
        try:
            result = subprocess.run(
                [sys.executable, "/tmp/ecosystem-cli-fixed.py", cli_name, "config"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                config_results["cli_config_access"] = True
                print(f"  ✅ CLI config access available")
            else:
                print(f"  ❌ CLI config access not available")
                
        except Exception as e:
            print(f"  💔 CLI config test failed: {str(e)}")
        
        return config_results
    
    def _contains_config_data(self, response: Dict[str, Any]) -> bool:
        """Check if response contains configuration data"""
        if not isinstance(response, dict):
            return False
        
        config_indicators = [
            "config", "configuration", "settings", "environment", 
            "debug", "log_level", "database", "redis", "port",
            "host", "timeout", "max_", "min_", "enable", "disable"
        ]
        
        response_str = json.dumps(response).lower()
        return any(indicator in response_str for indicator in config_indicators)
    
    def identify_gaps(self) -> Dict[str, Any]:
        """Identify gaps between API capabilities and CLI access"""
        print("\n📊 IDENTIFYING GAPS BETWEEN API AND CLI")
        print("=" * 60)
        
        gaps_summary = {
            "services_with_gaps": [],
            "missing_config_access": [],
            "available_but_not_cli": [],
            "total_api_endpoints": 0,
            "total_cli_commands": 0
        }
        
        for service in self.services.keys():
            service_gaps = {
                "service": service,
                "api_endpoints": len(self.audit_results.get(service, {}).get("discovered_endpoints", [])),
                "cli_commands": len(self.cli_capabilities.get(service, [])),
                "config_gap": False,
                "functional_gaps": []
            }
            
            # Check config access gap
            config_analysis = self.audit_results.get(service, {}).get("config_analysis", {})
            if config_analysis.get("config_data_available") and not config_analysis.get("cli_config_access"):
                service_gaps["config_gap"] = True
                gaps_summary["missing_config_access"].append(service)
            
            # Check functional gaps (API endpoints without CLI equivalent)
            api_endpoints = self.audit_results.get(service, {}).get("discovered_endpoints", [])
            functional_endpoints = [ep for ep in api_endpoints if ep["success"] and ep["endpoint"] not in ["/health", "/", "/docs"]]
            
            if functional_endpoints and service_gaps["cli_commands"] <= 2:  # Only health/status
                service_gaps["functional_gaps"] = [ep["endpoint"] for ep in functional_endpoints]
                gaps_summary["available_but_not_cli"].append({
                    "service": service,
                    "endpoints": service_gaps["functional_gaps"]
                })
            
            if service_gaps["config_gap"] or service_gaps["functional_gaps"]:
                gaps_summary["services_with_gaps"].append(service_gaps)
            
            gaps_summary["total_api_endpoints"] += service_gaps["api_endpoints"]
            gaps_summary["total_cli_commands"] += service_gaps["cli_commands"]
        
        return gaps_summary
    
    def run_comprehensive_audit(self) -> None:
        """Run complete audit of ecosystem APIs vs CLI capabilities"""
        print("🚀 COMPREHENSIVE ECOSYSTEM API vs CLI AUDIT")
        print("Testing all services for API endpoints, CLI capabilities, and configuration access")
        print("=" * 80)
        
        # Audit each service
        for service in self.services.keys():
            print(f"\n🔬 AUDITING {service.upper()}")
            print("-" * 50)
            
            # Discover API endpoints
            discovered_endpoints = self.discover_endpoints(service)
            
            # Test CLI capabilities  
            cli_commands = self.test_cli_capabilities(service)
            
            # Analyze configuration access
            config_analysis = self.analyze_config_endpoints(service)
            
            # Store results
            self.audit_results[service] = {
                "discovered_endpoints": discovered_endpoints,
                "config_analysis": config_analysis
            }
            self.cli_capabilities[service] = cli_commands
        
        # Identify and report gaps
        gaps = self.identify_gaps()
        self.generate_audit_report(gaps)
    
    def generate_audit_report(self, gaps: Dict[str, Any]) -> None:
        """Generate comprehensive audit report"""
        print("\n" + "=" * 80)
        print("📋 ECOSYSTEM API vs CLI AUDIT REPORT")
        print("=" * 80)
        
        # Overall statistics
        print(f"\n📊 OVERALL STATISTICS:")
        print(f"   Total Services Audited: {len(self.services)}")
        print(f"   Total API Endpoints Found: {gaps['total_api_endpoints']}")
        print(f"   Total CLI Commands Available: {gaps['total_cli_commands']}")
        print(f"   Services with Gaps: {len(gaps['services_with_gaps'])}")
        
        # Configuration access gaps
        print(f"\n⚙️  CONFIGURATION ACCESS GAPS:")
        if gaps["missing_config_access"]:
            print(f"   Services with config data but no CLI access:")
            for service in gaps["missing_config_access"]:
                print(f"     ❌ {service}")
        else:
            print(f"   ✅ No configuration access gaps identified")
        
        # Functional gaps
        print(f"\n🔧 FUNCTIONAL CAPABILITY GAPS:")
        if gaps["available_but_not_cli"]:
            for gap in gaps["available_but_not_cli"]:
                service = gap["service"]
                endpoints = gap["endpoints"]
                print(f"\n   📍 {service}:")
                print(f"      API Endpoints Available: {len(endpoints)}")
                print(f"      CLI Commands Available: {len(self.cli_capabilities.get(service, []))}")
                print(f"      Missing CLI Access to:")
                for endpoint in endpoints[:5]:  # Show first 5
                    print(f"        • {endpoint}")
                if len(endpoints) > 5:
                    print(f"        • ... and {len(endpoints) - 5} more")
        else:
            print(f"   ✅ No major functional gaps identified")
        
        # Service-by-service breakdown
        print(f"\n📋 SERVICE-BY-SERVICE AUDIT RESULTS:")
        for service in self.services.keys():
            api_count = len(self.audit_results.get(service, {}).get("discovered_endpoints", []))
            cli_count = len(self.cli_capabilities.get(service, []))
            config_analysis = self.audit_results.get(service, {}).get("config_analysis", {})
            
            # Status indicators
            config_status = "✅" if config_analysis.get("cli_config_access") else "❌" if config_analysis.get("config_data_available") else "➖"
            gap_status = "⚠️" if api_count > cli_count + 2 else "✅"  # Allow health + status
            
            print(f"   {gap_status} {service:25} | API: {api_count:2} | CLI: {cli_count:2} | Config: {config_status}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if gaps["missing_config_access"]:
            print(f"   1. 🔧 Add config viewing commands to CLI for:")
            for service in gaps["missing_config_access"]:
                print(f"      • {service}")
        
        if gaps["available_but_not_cli"]:
            print(f"   2. 🚀 Enhance CLI adapters with additional commands for:")
            for gap in gaps["available_but_not_cli"][:3]:  # Top 3
                print(f"      • {gap['service']} ({len(gap['endpoints'])} endpoints)")
        
        print(f"   3. 📊 Consider implementing unified config viewing across all services")
        print(f"   4. 🔗 Add batch operations for common workflows")
        
        print("\n" + "=" * 80)


def main():
    """Main audit runner"""
    auditor = EcosystemAPIAuditor()
    auditor.run_comprehensive_audit()


if __name__ == "__main__":
    main()
