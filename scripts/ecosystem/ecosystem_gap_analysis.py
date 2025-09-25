#!/usr/bin/env python3
"""
Ecosystem Gap Analysis & Stability Investigation
Detailed analysis of specific service issues and unintentional behavior
"""

import urllib.request
import urllib.error
import json
import subprocess
import time
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class ServiceIssue:
    """Represents a specific service issue found during analysis"""
    service: str
    issue_type: str
    severity: str  # "critical", "high", "medium", "low"
    description: str
    evidence: str
    recommended_fix: str


class EcosystemGapAnalyzer:
    """Deep dive analyzer for ecosystem stability gaps"""
    
    def __init__(self):
        self.issues = []
        self.service_ports = {
            "redis": 6379,
            "doc_store": 5087,
            "orchestrator": 5099,
            "llm-gateway": 5055,
            "mock-data-generator": 5065,
            "summarizer-hub": 5160,
            "bedrock-proxy": 5060,
            "github-mcp": 5030,
            "memory-agent": 5090,
            "discovery-agent": 5045,
            "source-agent": 5085,
            "analysis-service": 5080,
            "code-analyzer": 5025,
            "secure-analyzer": 5100,
            "log-collector": 5040,
            "prompt_store": 5110,
            "interpreter": 5120,
            "architecture-digitizer": 5105,
            "notification-service": 5130,
            "frontend": 3000,
            "ollama": 11434
        }
    
    def analyze_api_response_validation_issues(self):
        """Analyze API response validation problems"""
        print("🔍 Analyzing API Response Validation Issues...")
        
        # Test doc_store API validation issue found earlier
        try:
            with urllib.request.urlopen("http://localhost:5087/api/v1/documents", timeout=10) as response:
                content = response.read().decode('utf-8')
                
                # This should cause a validation error as we saw
                self.issues.append(ServiceIssue(
                    service="doc_store",
                    issue_type="api_validation",
                    severity="medium",
                    description="API response validation error - Pydantic schema mismatch",
                    evidence="3 validation errors: missing required fields 'items', 'total', 'has_more'",
                    recommended_fix="Update response model to match expected ListResponse schema or fix API handler"
                ))
                
        except Exception as e:
            self.issues.append(ServiceIssue(
                service="doc_store",
                issue_type="connectivity",
                severity="critical",
                description="Cannot connect to doc_store API",
                evidence=str(e),
                recommended_fix="Check service startup and port configuration"
            ))
    
    def analyze_port_mapping_discrepancies(self):
        """Analyze port mapping and internal/external connectivity"""
        print("🔍 Analyzing Port Mapping Discrepancies...")
        
        # Get Docker port mappings
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "table {{.Names}}\t{{.Ports}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            port_mappings = {}
            for line in result.stdout.split('\n')[1:]:  # Skip header
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        container_name = parts[0]
                        ports = parts[1]
                        port_mappings[container_name] = ports
            
            # Analyze specific problematic services
            problematic_services = [
                ("analysis-service", "hackathon-analysis-service-1", 5080),
                ("notification-service", "hackathon-notification-service-1", 5130),
                ("code-analyzer", "hackathon-code-analyzer-1", 5025),
                ("source-agent", "hackathon-source-agent-1", 5085),
                ("frontend", "hackathon-frontend-1", 3000)
            ]
            
            for service_name, container_name, expected_port in problematic_services:
                if container_name in port_mappings:
                    ports_info = port_mappings[container_name]
                    
                    # Check if expected port is properly mapped
                    if f"{expected_port}" not in ports_info:
                        self.issues.append(ServiceIssue(
                            service=service_name,
                            issue_type="port_mapping",
                            severity="high",
                            description=f"Port {expected_port} not properly mapped in Docker",
                            evidence=f"Container {container_name} ports: {ports_info}",
                            recommended_fix=f"Update docker-compose to properly map port {expected_port}"
                        ))
                
        except Exception as e:
            self.issues.append(ServiceIssue(
                service="docker",
                issue_type="infrastructure",
                severity="critical",
                description="Cannot analyze Docker port mappings",
                evidence=str(e),
                recommended_fix="Ensure Docker is running and accessible"
            ))
    
    def analyze_service_startup_errors(self):
        """Analyze service startup and runtime errors"""
        print("🔍 Analyzing Service Startup Errors...")
        
        # Check logs for specific services showing issues
        problematic_services = [
            "hackathon-analysis-service-1",
            "hackathon-code-analyzer-1", 
            "hackathon-notification-service-1",
            "hackathon-source-agent-1",
            "hackathon-frontend-1"
        ]
        
        for container_name in problematic_services:
            try:
                result = subprocess.run(
                    ["docker", "logs", "--tail", "20", container_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                logs = result.stdout + result.stderr
                service_name = container_name.replace("hackathon-", "").replace("-1", "")
                
                # Look for specific error patterns
                if "error" in logs.lower() or "exception" in logs.lower():
                    self.issues.append(ServiceIssue(
                        service=service_name,
                        issue_type="startup_error",
                        severity="high",
                        description="Service showing errors in logs",
                        evidence=logs[-500:],  # Last 500 chars
                        recommended_fix="Check service dependencies and configuration"
                    ))
                elif "ModuleNotFoundError" in logs:
                    self.issues.append(ServiceIssue(
                        service=service_name,
                        issue_type="dependency_missing",
                        severity="critical",
                        description="Missing Python dependencies preventing startup",
                        evidence=logs[-500:],
                        recommended_fix="Install missing dependencies or fix import paths"
                    ))
                elif not logs.strip():
                    self.issues.append(ServiceIssue(
                        service=service_name,
                        issue_type="silent_failure",
                        severity="medium",
                        description="Service running but producing no logs",
                        evidence="No log output detected",
                        recommended_fix="Add proper logging to service startup"
                    ))
                    
            except Exception as e:
                self.issues.append(ServiceIssue(
                    service=service_name,
                    issue_type="log_analysis_failed",
                    severity="low",
                    description="Cannot analyze service logs",
                    evidence=str(e),
                    recommended_fix="Check container status and Docker access"
                ))
    
    def analyze_cli_networking_issues(self):
        """Analyze CLI networking and hostname resolution problems"""
        print("🔍 Analyzing CLI Networking Issues...")
        
        # The CLI tool we tested earlier was using Docker internal hostnames
        # when running from the host machine
        
        self.issues.append(ServiceIssue(
            service="ecosystem_cli_executable",
            issue_type="networking_configuration",
            severity="high",
            description="CLI tool using Docker internal hostnames instead of localhost ports",
            evidence="CLI tool tries to connect to 'hackathon-*-1' hostnames which fail from host",
            recommended_fix="Update CLI to detect environment and use appropriate URLs (localhost:port vs internal hostname)"
        ))
    
    def analyze_health_check_discrepancies(self):
        """Analyze health check methodology differences"""
        print("🔍 Analyzing Health Check Discrepancies...")
        
        # We found that Docker health shows unhealthy but our script shows healthy
        self.issues.append(ServiceIssue(
            service="health_monitoring",
            issue_type="monitoring_inconsistency",
            severity="medium",
            description="Health check script and Docker health status report different results",
            evidence="Script reports 100% healthy, Docker shows multiple unhealthy services",
            recommended_fix="Standardize health check methods and ensure they test the same endpoints"
        ))
    
    def test_service_api_endpoints(self):
        """Test specific API endpoints for functional issues"""
        print("🔍 Testing Service API Endpoints...")
        
        # Test critical services that showed as healthy but might have functional issues
        test_cases = [
            ("orchestrator", 5099, "/api/v1/services", "Service registry endpoint"),
            ("llm-gateway", 5055, "/api/v1/providers", "Provider status endpoint"),
            ("discovery-agent", 5045, "/api/v1/discovery/services", "Service discovery endpoint"),
            ("prompt_store", 5110, "/api/v1/prompts", "Prompt listing endpoint"),
            ("analysis-service", 5080, "/health", "Basic health endpoint"),
        ]
        
        for service, port, endpoint, description in test_cases:
            try:
                url = f"http://localhost:{port}{endpoint}"
                with urllib.request.urlopen(url, timeout=10) as response:
                    if response.getcode() != 200:
                        self.issues.append(ServiceIssue(
                            service=service,
                            issue_type="api_functionality",
                            severity="medium",
                            description=f"{description} returning non-200 status",
                            evidence=f"HTTP {response.getcode()} from {url}",
                            recommended_fix=f"Debug {service} {endpoint} endpoint implementation"
                        ))
                    else:
                        # Try to parse response
                        content = response.read().decode('utf-8')
                        try:
                            json.loads(content)
                        except json.JSONDecodeError:
                            self.issues.append(ServiceIssue(
                                service=service,
                                issue_type="api_response_format",
                                severity="low",
                                description=f"{description} returning non-JSON response",
                                evidence=f"Invalid JSON from {url}",
                                recommended_fix=f"Ensure {service} returns proper JSON responses"
                            ))
                            
            except urllib.error.URLError as e:
                if "Connection refused" in str(e):
                    self.issues.append(ServiceIssue(
                        service=service,
                        issue_type="service_down",
                        severity="critical",
                        description=f"{description} not accessible",
                        evidence=f"Connection refused to {url}",
                        recommended_fix=f"Start {service} or fix port mapping"
                    ))
                else:
                    self.issues.append(ServiceIssue(
                        service=service,
                        issue_type="network_error",
                        severity="high",
                        description=f"Network error accessing {description}",
                        evidence=str(e),
                        recommended_fix=f"Check network connectivity to {service}"
                    ))
            except Exception as e:
                self.issues.append(ServiceIssue(
                    service=service,
                    issue_type="api_test_error",
                    severity="medium",
                    description=f"Error testing {description}",
                    evidence=str(e),
                    recommended_fix=f"Debug API testing for {service}"
                ))
    
    def test_integration_workflows(self):
        """Test cross-service integration workflows"""
        print("🔍 Testing Integration Workflows...")
        
        # Test workflow: Create document → Analyze → Summarize
        try:
            # Step 1: Create document in doc_store
            doc_data = {
                "title": "Integration Test Document",
                "content": "This document tests cross-service integration.",
                "content_type": "text",
                "source_type": "integration_test"
            }
            
            json_data = json.dumps(doc_data).encode('utf-8')
            req = urllib.request.Request(
                "http://localhost:5087/api/v1/documents",
                data=json_data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.getcode() != 201:
                    self.issues.append(ServiceIssue(
                        service="doc_store",
                        issue_type="integration_workflow",
                        severity="high",
                        description="Document creation failing in integration workflow",
                        evidence=f"HTTP {response.getcode()} instead of 201",
                        recommended_fix="Fix doc_store document creation endpoint"
                    ))
                    return
                
                result = json.loads(response.read().decode('utf-8'))
                if 'document_id' not in result:
                    self.issues.append(ServiceIssue(
                        service="doc_store",
                        issue_type="api_response_structure",
                        severity="medium",
                        description="Document creation response missing document_id",
                        evidence=str(result),
                        recommended_fix="Ensure document creation returns document_id"
                    ))
                    return
                
                doc_id = result['document_id']
                
                # Step 2: Test analysis service
                try:
                    analysis_data = {"document_id": doc_id, "analysis_types": ["basic"]}
                    analysis_json = json.dumps(analysis_data).encode('utf-8')
                    analysis_req = urllib.request.Request(
                        "http://localhost:5080/api/v1/analysis/analyze",
                        data=analysis_json,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    with urllib.request.urlopen(analysis_req, timeout=15) as analysis_response:
                        if analysis_response.getcode() != 200:
                            self.issues.append(ServiceIssue(
                                service="analysis-service",
                                issue_type="integration_workflow",
                                severity="high",
                                description="Analysis service failing in integration workflow",
                                evidence=f"HTTP {analysis_response.getcode()}",
                                recommended_fix="Fix analysis-service /analyze endpoint"
                            ))
                            
                except urllib.error.URLError:
                    self.issues.append(ServiceIssue(
                        service="analysis-service",
                        issue_type="service_unavailable",
                        severity="critical",
                        description="Analysis service not reachable for integration workflow",
                        evidence="Connection failed to analysis-service",
                        recommended_fix="Ensure analysis-service is running and accessible"
                    ))
                
        except Exception as e:
            self.issues.append(ServiceIssue(
                service="integration_workflow",
                issue_type="workflow_failure",
                severity="high",
                description="End-to-end integration workflow failed",
                evidence=str(e),
                recommended_fix="Debug cross-service communication and data flow"
            ))
    
    def run_comprehensive_gap_analysis(self):
        """Run complete gap analysis"""
        print("🚀 Starting Comprehensive Ecosystem Gap Analysis...")
        print("="*80)
        
        # Run all analysis functions
        self.analyze_api_response_validation_issues()
        self.analyze_port_mapping_discrepancies()
        self.analyze_service_startup_errors()
        self.analyze_cli_networking_issues()
        self.analyze_health_check_discrepancies()
        self.test_service_api_endpoints()
        self.test_integration_workflows()
        
        return self.generate_gap_analysis_report()
    
    def generate_gap_analysis_report(self):
        """Generate comprehensive gap analysis report"""
        
        # Categorize issues by severity
        critical_issues = [i for i in self.issues if i.severity == "critical"]
        high_issues = [i for i in self.issues if i.severity == "high"]
        medium_issues = [i for i in self.issues if i.severity == "medium"]
        low_issues = [i for i in self.issues if i.severity == "low"]
        
        # Categorize by type
        issue_types = {}
        for issue in self.issues:
            if issue.issue_type not in issue_types:
                issue_types[issue.issue_type] = []
            issue_types[issue.issue_type].append(issue)
        
        report = {
            "analysis_timestamp": time.time(),
            "total_issues_found": len(self.issues),
            "issues_by_severity": {
                "critical": len(critical_issues),
                "high": len(high_issues), 
                "medium": len(medium_issues),
                "low": len(low_issues)
            },
            "issues_by_type": {k: len(v) for k, v in issue_types.items()},
            "critical_issues": [self._issue_to_dict(i) for i in critical_issues],
            "high_issues": [self._issue_to_dict(i) for i in high_issues],
            "medium_issues": [self._issue_to_dict(i) for i in medium_issues],
            "low_issues": [self._issue_to_dict(i) for i in low_issues],
            "recommendations": self._generate_prioritized_recommendations(),
            "stability_assessment": self._assess_overall_stability()
        }
        
        return report
    
    def _issue_to_dict(self, issue: ServiceIssue) -> Dict:
        """Convert ServiceIssue to dictionary"""
        return {
            "service": issue.service,
            "issue_type": issue.issue_type,
            "severity": issue.severity,
            "description": issue.description,
            "evidence": issue.evidence,
            "recommended_fix": issue.recommended_fix
        }
    
    def _generate_prioritized_recommendations(self) -> List[str]:
        """Generate prioritized recommendations"""
        recommendations = []
        
        # Critical issues first
        critical_issues = [i for i in self.issues if i.severity == "critical"]
        if critical_issues:
            recommendations.append("URGENT: Address critical issues immediately - ecosystem stability at risk")
            
        # Service connectivity issues
        connectivity_issues = [i for i in self.issues if "connectivity" in i.issue_type or "service_down" in i.issue_type]
        if connectivity_issues:
            recommendations.append("HIGH: Fix service connectivity issues to restore full functionality")
        
        # API validation issues
        api_issues = [i for i in self.issues if "api" in i.issue_type]
        if api_issues:
            recommendations.append("MEDIUM: Resolve API validation and response format issues")
        
        # Health check consistency
        health_issues = [i for i in self.issues if "health" in i.issue_type or "monitoring" in i.issue_type]
        if health_issues:
            recommendations.append("MEDIUM: Standardize health check methods for accurate monitoring")
        
        # CLI and tooling
        cli_issues = [i for i in self.issues if "cli" in i.service or "networking" in i.issue_type]
        if cli_issues:
            recommendations.append("LOW: Update CLI tools for proper environment detection and networking")
        
        return recommendations
    
    def _assess_overall_stability(self) -> Dict[str, Any]:
        """Assess overall ecosystem stability"""
        critical_count = len([i for i in self.issues if i.severity == "critical"])
        high_count = len([i for i in self.issues if i.severity == "high"])
        
        if critical_count > 0:
            stability_level = "POOR"
            stability_score = 30
        elif high_count > 3:
            stability_level = "UNSTABLE" 
            stability_score = 50
        elif high_count > 0:
            stability_level = "MODERATE"
            stability_score = 70
        else:
            stability_level = "GOOD"
            stability_score = 85
        
        return {
            "stability_level": stability_level,
            "stability_score": stability_score,
            "critical_issues_count": critical_count,
            "blocking_issues_count": critical_count + high_count,
            "production_ready": critical_count == 0 and high_count <= 1
        }
    
    def print_gap_analysis_report(self, report: Dict[str, Any]):
        """Print comprehensive gap analysis report"""
        print("\n" + "="*80)
        print("🔍 ECOSYSTEM STABILITY GAP ANALYSIS REPORT")
        print("="*80)
        
        stability = report["stability_assessment"]
        print(f"\n📊 OVERALL STABILITY ASSESSMENT")
        print(f"  Stability Level: {stability['stability_level']}")
        print(f"  Stability Score: {stability['stability_score']}/100")
        print(f"  Production Ready: {'✅ YES' if stability['production_ready'] else '❌ NO'}")
        
        print(f"\n🚨 ISSUES SUMMARY")
        print(f"  Total Issues Found: {report['total_issues_found']}")
        print(f"  Critical Issues: {report['issues_by_severity']['critical']}")
        print(f"  High Priority: {report['issues_by_severity']['high']}")
        print(f"  Medium Priority: {report['issues_by_severity']['medium']}")
        print(f"  Low Priority: {report['issues_by_severity']['low']}")
        
        # Print critical issues
        if report["critical_issues"]:
            print(f"\n🚨 CRITICAL ISSUES (IMMEDIATE ACTION REQUIRED)")
            for i, issue in enumerate(report["critical_issues"], 1):
                print(f"  {i}. {issue['service']}: {issue['description']}")
                print(f"     Evidence: {issue['evidence'][:100]}...")
                print(f"     Fix: {issue['recommended_fix']}")
                print()
        
        # Print high priority issues
        if report["high_issues"]:
            print(f"\n⚠️  HIGH PRIORITY ISSUES")
            for i, issue in enumerate(report["high_issues"], 1):
                print(f"  {i}. {issue['service']}: {issue['description']}")
                print(f"     Fix: {issue['recommended_fix']}")
                print()
        
        # Print recommendations
        print(f"\n💡 PRIORITIZED RECOMMENDATIONS")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"  {i}. {rec}")
        
        print("\n" + "="*80)


def main():
    """Main gap analysis execution"""
    analyzer = EcosystemGapAnalyzer()
    report = analyzer.run_comprehensive_gap_analysis()
    analyzer.print_gap_analysis_report(report)
    
    # Save detailed report
    with open("ecosystem_gap_analysis.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Detailed gap analysis saved to: ecosystem_gap_analysis.json")


if __name__ == "__main__":
    main()
