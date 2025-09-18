#!/usr/bin/env python3
"""
Service Connectivity Validation Pipeline
Automated testing and validation of service connectivity and integration
"""

import asyncio
import json
import time
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import subprocess
import yaml


@dataclass
class ServiceDependency:
    """Represents a service dependency relationship"""
    service: str
    depends_on: List[str]
    critical: bool = True  # Whether this dependency is critical for service function


@dataclass
class IntegrationTest:
    """Represents an integration test between services"""
    test_name: str
    source_service: str
    target_service: str
    test_endpoint: str
    test_data: Optional[Dict] = None
    expected_status: int = 200
    timeout: int = 30


class ServiceConnectivityValidator:
    """Comprehensive service connectivity and integration validation"""
    
    def __init__(self):
        self.service_dependencies = self._load_service_dependencies()
        self.integration_tests = self._load_integration_tests()
        self.validation_results = {}
        
    def _load_service_dependencies(self) -> Dict[str, ServiceDependency]:
        """Load service dependency mappings"""
        return {
            "doc_store": ServiceDependency(
                service="doc_store",
                depends_on=["redis"],  # Uses Redis for caching
                critical=True
            ),
            "orchestrator": ServiceDependency(
                service="orchestrator",
                depends_on=["redis"],  # Uses Redis for coordination
                critical=True
            ),
            "llm-gateway": ServiceDependency(
                service="llm-gateway", 
                depends_on=["ollama"],  # Routes to Ollama
                critical=False  # Can function without Ollama if other providers available
            ),
            "analysis-service": ServiceDependency(
                service="analysis-service",
                depends_on=["doc_store", "llm-gateway"],  # Reads docs, uses LLM
                critical=True
            ),
            "discovery-agent": ServiceDependency(
                service="discovery-agent",
                depends_on=["orchestrator"],  # Registers with orchestrator
                critical=True
            ),
            "mock-data-generator": ServiceDependency(
                service="mock-data-generator",
                depends_on=["llm-gateway", "doc_store"],  # Uses LLM, stores in doc_store
                critical=True
            ),
            "summarizer-hub": ServiceDependency(
                service="summarizer-hub",
                depends_on=["llm-gateway"],  # Uses LLM for summarization
                critical=True
            ),
            "notification-service": ServiceDependency(
                service="notification-service",
                depends_on=[],  # Standalone service
                critical=False
            ),
            "prompt_store": ServiceDependency(
                service="prompt_store",
                depends_on=["doc_store"],  # May store results in doc_store
                critical=False
            )
        }
    
    def _load_integration_tests(self) -> List[IntegrationTest]:
        """Load integration test scenarios"""
        return [
            # Document workflow tests
            IntegrationTest(
                test_name="document_creation_workflow",
                source_service="doc_store",
                target_service="doc_store",
                test_endpoint="/api/v1/documents",
                test_data={
                    "title": "Connectivity Test Document",
                    "content": "Testing service connectivity validation",
                    "content_type": "text",
                    "source_type": "connectivity_test"
                },
                expected_status=201
            ),
            IntegrationTest(
                test_name="document_analysis_workflow",
                source_service="analysis-service",
                target_service="analysis-service", 
                test_endpoint="/api/v1/analysis/analyze",
                test_data={
                    "document_id": "test_doc_id",
                    "analysis_types": ["basic_analysis"]
                },
                expected_status=200
            ),
            IntegrationTest(
                test_name="llm_provider_check",
                source_service="llm-gateway",
                target_service="llm-gateway",
                test_endpoint="/api/v1/providers",
                expected_status=200
            ),
            IntegrationTest(
                test_name="service_discovery_check",
                source_service="discovery-agent",
                target_service="discovery-agent",
                test_endpoint="/api/v1/discovery/services",
                expected_status=200
            ),
            IntegrationTest(
                test_name="orchestrator_services_check",
                source_service="orchestrator",
                target_service="orchestrator",
                test_endpoint="/api/v1/services",
                expected_status=200
            ),
            # Cross-service integration tests
            IntegrationTest(
                test_name="doc_store_to_analysis_integration",
                source_service="doc_store",
                target_service="analysis-service",
                test_endpoint="/api/v1/analysis/capabilities",
                expected_status=200
            )
        ]
    
    async def validate_service_dependencies(self) -> Dict[str, Any]:
        """Validate all service dependencies are met"""
        dependency_results = {}
        
        for service_name, dependency in self.service_dependencies.items():
            dependency_results[service_name] = await self._validate_single_dependency(dependency)
        
        return {
            "dependency_validation": dependency_results,
            "critical_failures": [
                service for service, result in dependency_results.items()
                if not result["dependencies_met"] and self.service_dependencies[service].critical
            ],
            "total_dependencies": len(dependency_results),
            "healthy_dependencies": sum(1 for r in dependency_results.values() if r["dependencies_met"])
        }
    
    async def _validate_single_dependency(self, dependency: ServiceDependency) -> Dict[str, Any]:
        """Validate dependencies for a single service"""
        missing_dependencies = []
        dependency_status = {}
        
        for dep_service in dependency.depends_on:
            # Check if dependency service is reachable
            is_reachable = await self._check_service_reachability(dep_service)
            dependency_status[dep_service] = is_reachable
            
            if not is_reachable:
                missing_dependencies.append(dep_service)
        
        return {
            "service": dependency.service,
            "required_dependencies": dependency.depends_on,
            "dependency_status": dependency_status,
            "missing_dependencies": missing_dependencies,
            "dependencies_met": len(missing_dependencies) == 0,
            "critical": dependency.critical
        }
    
    async def _check_service_reachability(self, service_name: str) -> bool:
        """Check if a service is reachable"""
        service_ports = {
            "redis": 6379,
            "doc_store": 5087,
            "orchestrator": 5099,
            "llm-gateway": 5055,
            "analysis-service": 5080,
            "discovery-agent": 5045,
            "ollama": 11434,
            "notification-service": 5130,
            "prompt_store": 5110
        }
        
        if service_name not in service_ports:
            return False
        
        port = service_ports[service_name]
        
        try:
            # For Redis, try a simple TCP connection
            if service_name == "redis":
                import socket
                with socket.create_connection(("localhost", port), timeout=5):
                    return True
            
            # For Ollama, check the API endpoint
            elif service_name == "ollama":
                with urllib.request.urlopen(f"http://localhost:{port}/api/tags", timeout=5) as response:
                    return response.getcode() == 200
            
            # For other services, check health endpoint
            else:
                with urllib.request.urlopen(f"http://localhost:{port}/health", timeout=5) as response:
                    return response.getcode() == 200
                    
        except Exception:
            return False
    
    async def run_integration_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        test_results = {}
        
        for test in self.integration_tests:
            test_results[test.test_name] = await self._run_single_integration_test(test)
        
        return {
            "integration_tests": test_results,
            "total_tests": len(test_results),
            "passed_tests": sum(1 for r in test_results.values() if r["passed"]),
            "failed_tests": [name for name, result in test_results.items() if not result["passed"]]
        }
    
    async def _run_single_integration_test(self, test: IntegrationTest) -> Dict[str, Any]:
        """Run a single integration test"""
        start_time = time.time()
        
        # Determine service URL
        service_ports = {
            "doc_store": 5087,
            "orchestrator": 5099,
            "llm-gateway": 5055,
            "analysis-service": 5080,
            "discovery-agent": 5045
        }
        
        if test.target_service not in service_ports:
            return {
                "test_name": test.test_name,
                "passed": False,
                "error": f"Unknown target service: {test.target_service}",
                "execution_time": 0
            }
        
        port = service_ports[test.target_service]
        url = f"http://localhost:{port}{test.test_endpoint}"
        
        try:
            if test.test_data:
                # POST request with data
                json_data = json.dumps(test.test_data).encode('utf-8')
                req = urllib.request.Request(
                    url,
                    data=json_data,
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=test.timeout) as response:
                    status_code = response.getcode()
                    response_data = response.read().decode('utf-8')
            else:
                # GET request
                with urllib.request.urlopen(url, timeout=test.timeout) as response:
                    status_code = response.getcode()
                    response_data = response.read().decode('utf-8')
            
            execution_time = time.time() - start_time
            passed = status_code == test.expected_status
            
            result = {
                "test_name": test.test_name,
                "passed": passed,
                "status_code": status_code,
                "expected_status": test.expected_status,
                "execution_time": execution_time,
                "url": url
            }
            
            if not passed:
                result["error"] = f"Expected status {test.expected_status}, got {status_code}"
            
            # Try to parse response for additional validation
            try:
                json_response = json.loads(response_data)
                result["response_valid_json"] = True
                
                # Check for common error indicators
                if "error" in json_response or "message" in json_response:
                    result["response_preview"] = json_response
            except json.JSONDecodeError:
                result["response_valid_json"] = False
                result["response_preview"] = response_data[:200]
            
            return result
            
        except Exception as e:
            return {
                "test_name": test.test_name,
                "passed": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "url": url
            }
    
    async def validate_docker_port_mappings(self) -> Dict[str, Any]:
        """Validate Docker port mappings match expectations"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    "port_validation": {},
                    "error": "Could not query Docker containers"
                }
            
            port_mappings = {}
            port_conflicts = []
            
            for line in result.stdout.split('\n'):
                if line.strip():
                    try:
                        container_info = json.loads(line)
                        container_name = container_info.get('Names', '')
                        ports = container_info.get('Ports', '')
                        
                        if 'hackathon-' in container_name:
                            service_name = container_name.replace('hackathon-', '').replace('-1', '')
                            port_mappings[service_name] = ports
                            
                            # Check for common port mapping issues
                            if service_name == 'analysis-service' and '5080:5020' in ports:
                                port_conflicts.append({
                                    "service": service_name,
                                    "issue": "Internal/external port mismatch",
                                    "details": "Mapped 5080:5020 but health checks expect 5080:5080"
                                })
                    except json.JSONDecodeError:
                        continue
            
            return {
                "port_validation": port_mappings,
                "port_conflicts": port_conflicts,
                "total_containers": len(port_mappings),
                "conflicts_found": len(port_conflicts)
            }
            
        except Exception as e:
            return {
                "port_validation": {},
                "error": str(e)
            }
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run complete connectivity validation suite"""
        print("🔍 Starting Comprehensive Service Connectivity Validation...")
        
        # Run all validation components
        dependency_results = await self.validate_service_dependencies()
        integration_results = await self.run_integration_tests()
        port_validation = await self.validate_docker_port_mappings()
        
        # Calculate overall connectivity score
        total_checks = (
            dependency_results["total_dependencies"] +
            integration_results["total_tests"] +
            1  # Port validation
        )
        
        passed_checks = (
            dependency_results["healthy_dependencies"] +
            integration_results["passed_tests"] +
            (1 if port_validation.get("conflicts_found", 1) == 0 else 0)
        )
        
        connectivity_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        return {
            "validation_timestamp": time.time(),
            "connectivity_score": connectivity_score,
            "overall_status": self._determine_connectivity_status(connectivity_score, dependency_results),
            "dependency_validation": dependency_results,
            "integration_testing": integration_results,
            "port_validation": port_validation,
            "critical_issues": self._identify_critical_connectivity_issues(
                dependency_results, integration_results, port_validation
            ),
            "recommendations": self._generate_connectivity_recommendations(
                dependency_results, integration_results, port_validation
            )
        }
    
    def _determine_connectivity_status(self, score: float, dependency_results: Dict) -> str:
        """Determine overall connectivity status"""
        critical_failures = len(dependency_results.get("critical_failures", []))
        
        if critical_failures > 0:
            return "CRITICAL"
        elif score >= 90:
            return "EXCELLENT"
        elif score >= 75:
            return "GOOD"
        elif score >= 50:
            return "DEGRADED"
        else:
            return "POOR"
    
    def _identify_critical_connectivity_issues(self, dependency_results: Dict, 
                                             integration_results: Dict, 
                                             port_validation: Dict) -> List[str]:
        """Identify critical connectivity issues"""
        issues = []
        
        # Critical dependency failures
        critical_failures = dependency_results.get("critical_failures", [])
        if critical_failures:
            issues.append(f"Critical service dependencies missing: {', '.join(critical_failures)}")
        
        # Failed integration tests
        failed_tests = integration_results.get("failed_tests", [])
        if failed_tests:
            issues.append(f"Integration tests failing: {', '.join(failed_tests)}")
        
        # Port conflicts
        port_conflicts = port_validation.get("port_conflicts", [])
        if port_conflicts:
            issues.append(f"Port mapping conflicts detected: {len(port_conflicts)} services affected")
        
        return issues
    
    def _generate_connectivity_recommendations(self, dependency_results: Dict,
                                             integration_results: Dict,
                                             port_validation: Dict) -> List[str]:
        """Generate actionable recommendations for connectivity issues"""
        recommendations = []
        
        # Dependency recommendations
        critical_failures = dependency_results.get("critical_failures", [])
        if critical_failures:
            recommendations.append("Start missing critical dependencies before dependent services")
        
        # Integration test recommendations
        failed_tests = integration_results.get("failed_tests", [])
        if failed_tests:
            recommendations.append("Fix API endpoints and response formats for failing integration tests")
        
        # Port mapping recommendations
        port_conflicts = port_validation.get("port_conflicts", [])
        if port_conflicts:
            recommendations.append("Update Docker Compose port mappings to match service expectations")
        
        if not recommendations:
            recommendations.append("All connectivity validations passed - ecosystem ready for integration")
        
        return recommendations
    
    def print_validation_report(self, results: Dict[str, Any]):
        """Print comprehensive validation report"""
        print("\n" + "="*80)
        print("🔗 SERVICE CONNECTIVITY VALIDATION REPORT")
        print("="*80)
        
        print(f"\n📊 OVERALL ASSESSMENT")
        print(f"  Connectivity Score: {results['connectivity_score']:.1f}/100")
        print(f"  Overall Status: {results['overall_status']}")
        
        # Dependency validation
        dep_results = results['dependency_validation']
        print(f"\n🔄 DEPENDENCY VALIDATION")
        print(f"  Total Services: {dep_results['total_dependencies']}")
        print(f"  Dependencies Met: {dep_results['healthy_dependencies']}")
        print(f"  Critical Failures: {len(dep_results['critical_failures'])}")
        
        if dep_results['critical_failures']:
            print(f"  Failed Services: {', '.join(dep_results['critical_failures'])}")
        
        # Integration testing
        int_results = results['integration_testing']
        print(f"\n🧪 INTEGRATION TESTING")
        print(f"  Total Tests: {int_results['total_tests']}")
        print(f"  Passed Tests: {int_results['passed_tests']}")
        print(f"  Failed Tests: {len(int_results['failed_tests'])}")
        
        if int_results['failed_tests']:
            print(f"  Failed: {', '.join(int_results['failed_tests'])}")
        
        # Port validation
        port_results = results['port_validation']
        print(f"\n🔌 PORT VALIDATION")
        print(f"  Containers Checked: {port_results.get('total_containers', 0)}")
        print(f"  Port Conflicts: {port_results.get('conflicts_found', 0)}")
        
        # Critical issues
        if results['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES")
            for i, issue in enumerate(results['critical_issues'], 1):
                print(f"  {i}. {issue}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print("\n" + "="*80)


async def main():
    """Main validation execution"""
    validator = ServiceConnectivityValidator()
    results = await validator.run_comprehensive_validation()
    validator.print_validation_report(results)
    
    # Save detailed results
    with open("/Users/mykalthomas/Documents/work/Hackathon/connectivity_validation_report.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed connectivity validation saved to: connectivity_validation_report.json")


if __name__ == "__main__":
    asyncio.run(main())
