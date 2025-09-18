#!/usr/bin/env python3
"""
Phase 4: Security Scanning Implementation using Secure-Analyzer

This script implements security scanning for discovered tools using the secure-analyzer service:
- Scan discovered tools for security vulnerabilities
- Validate tool parameters for security risks
- Create security compliance reports
- Integrate with secure-analyzer service
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

class ToolSecurityScanner:
    """Security scanner for discovered LangGraph tools using secure-analyzer service"""
    
    def __init__(self):
        self.secure_analyzer_url = "http://localhost:5070"
        self.security_reports = {}
        
        # Security risk categories
        self.risk_categories = {
            "injection": ["sql", "command", "script", "code"],
            "authentication": ["auth", "token", "password", "credential"],
            "authorization": ["permission", "role", "access", "admin"],
            "data_exposure": ["sensitive", "private", "confidential", "personal"],
            "file_operations": ["file", "upload", "download", "path", "directory"],
            "network_operations": ["url", "external", "remote", "fetch", "request"]
        }
    
    async def scan_tool_security(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Scan a single tool for security vulnerabilities"""
        
        print(f"🔒 Scanning {tool['name']} for security risks...")
        
        security_analysis = {
            "tool_name": tool["name"],
            "service": tool["service"],
            "timestamp": datetime.now().isoformat(),
            "risk_level": "low",
            "vulnerabilities": [],
            "recommendations": [],
            "secure_analyzer_result": None
        }
        
        # Analyze tool for common security risks
        vulnerabilities = []
        
        # 1. Parameter injection risks
        injection_risks = self._analyze_injection_risks(tool)
        vulnerabilities.extend(injection_risks)
        
        # 2. Authentication/Authorization risks
        auth_risks = self._analyze_auth_risks(tool)
        vulnerabilities.extend(auth_risks)
        
        # 3. Data exposure risks
        data_risks = self._analyze_data_exposure_risks(tool)
        vulnerabilities.extend(data_risks)
        
        # 4. File operation risks
        file_risks = self._analyze_file_operation_risks(tool)
        vulnerabilities.extend(file_risks)
        
        # 5. Use secure-analyzer service for advanced scanning
        secure_analyzer_result = await self._scan_with_secure_analyzer(tool)
        security_analysis["secure_analyzer_result"] = secure_analyzer_result
        
        # Combine vulnerabilities
        security_analysis["vulnerabilities"] = vulnerabilities
        
        # Determine overall risk level
        security_analysis["risk_level"] = self._calculate_risk_level(vulnerabilities, secure_analyzer_result)
        
        # Generate recommendations
        security_analysis["recommendations"] = self._generate_security_recommendations(vulnerabilities, tool)
        
        return security_analysis
    
    def _analyze_injection_risks(self, tool: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze tool for injection vulnerabilities"""
        vulnerabilities = []
        
        # Check path for injection-prone patterns
        path = tool.get("path", "").lower()
        
        # SQL injection risks
        if any(word in path for word in ["query", "search", "filter", "where"]):
            vulnerabilities.append({
                "type": "sql_injection_risk",
                "severity": "medium",
                "description": f"Path '{tool['path']}' may be vulnerable to SQL injection",
                "location": "path",
                "mitigation": "Use parameterized queries and input validation"
            })
        
        # Command injection risks
        if any(word in path for word in ["execute", "run", "command", "script"]):
            vulnerabilities.append({
                "type": "command_injection_risk", 
                "severity": "high",
                "description": f"Path '{tool['path']}' may allow command injection",
                "location": "path",
                "mitigation": "Sanitize inputs and use allowlisted commands only"
            })
        
        # Check parameters for injection risks
        for param in tool.get("parameters", []):
            param_name = param.get("name", "").lower()
            
            if any(word in param_name for word in ["query", "command", "script", "code"]):
                vulnerabilities.append({
                    "type": "parameter_injection_risk",
                    "severity": "medium",
                    "description": f"Parameter '{param['name']}' may be vulnerable to injection",
                    "location": f"parameter:{param['name']}",
                    "mitigation": "Implement strict input validation and sanitization"
                })
        
        return vulnerabilities
    
    def _analyze_auth_risks(self, tool: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze tool for authentication/authorization risks"""
        vulnerabilities = []
        
        path = tool.get("path", "").lower()
        
        # Admin/management endpoints without auth
        if any(word in path for word in ["admin", "manage", "config", "delete"]):
            vulnerabilities.append({
                "type": "privileged_operation_risk",
                "severity": "high", 
                "description": f"Privileged operation '{tool['path']}' may lack proper authorization",
                "location": "path",
                "mitigation": "Implement role-based access control and authentication"
            })
        
        # Check for auth-related parameters
        for param in tool.get("parameters", []):
            param_name = param.get("name", "").lower()
            
            if any(word in param_name for word in ["token", "password", "key", "secret"]):
                if param.get("location") == "query":
                    vulnerabilities.append({
                        "type": "credential_exposure_risk",
                        "severity": "high",
                        "description": f"Sensitive parameter '{param['name']}' passed in URL/query",
                        "location": f"parameter:{param['name']}",
                        "mitigation": "Move sensitive parameters to request body or headers"
                    })
        
        return vulnerabilities
    
    def _analyze_data_exposure_risks(self, tool: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze tool for data exposure risks"""
        vulnerabilities = []
        
        # Check for endpoints that might expose sensitive data
        path = tool.get("path", "").lower()
        
        if any(word in path for word in ["dump", "export", "backup", "logs"]):
            vulnerabilities.append({
                "type": "data_exposure_risk",
                "severity": "medium",
                "description": f"Endpoint '{tool['path']}' may expose sensitive data",
                "location": "path", 
                "mitigation": "Implement access controls and data filtering"
            })
        
        # Check for parameters that might expose data
        for param in tool.get("parameters", []):
            param_name = param.get("name", "").lower()
            
            if any(word in param_name for word in ["user", "email", "private", "internal"]):
                vulnerabilities.append({
                    "type": "parameter_data_exposure",
                    "severity": "low",
                    "description": f"Parameter '{param['name']}' may expose sensitive information",
                    "location": f"parameter:{param['name']}",
                    "mitigation": "Review data access controls and implement field filtering"
                })
        
        return vulnerabilities
    
    def _analyze_file_operation_risks(self, tool: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze tool for file operation risks"""
        vulnerabilities = []
        
        path = tool.get("path", "").lower()
        
        # File upload/download risks
        if any(word in path for word in ["upload", "download", "file"]):
            vulnerabilities.append({
                "type": "file_operation_risk",
                "severity": "medium",
                "description": f"File operation '{tool['path']}' may be vulnerable to path traversal",
                "location": "path",
                "mitigation": "Validate file paths and implement file type restrictions"
            })
        
        # Check for path parameters
        for param in tool.get("parameters", []):
            param_name = param.get("name", "").lower()
            
            if any(word in param_name for word in ["path", "file", "directory", "folder"]):
                vulnerabilities.append({
                    "type": "path_traversal_risk",
                    "severity": "high",
                    "description": f"Path parameter '{param['name']}' vulnerable to traversal attacks",
                    "location": f"parameter:{param['name']}",
                    "mitigation": "Sanitize paths and restrict to allowed directories"
                })
        
        return vulnerabilities
    
    async def _scan_with_secure_analyzer(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Use the secure-analyzer service for advanced security scanning"""
        
        try:
            # Prepare tool data for secure-analyzer
            scan_data = {
                "content": json.dumps(tool),
                "type": "tool_definition",
                "service": tool.get("service"),
                "metadata": {
                    "tool_name": tool.get("name"),
                    "method": tool.get("method"),
                    "path": tool.get("path")
                }
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # Use secure-analyzer's detect-content endpoint
                url = f"{self.secure_analyzer_url}/detect-content"
                
                async with session.post(url, json=scan_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "analysis": result,
                            "response_time": response.headers.get("X-Response-Time", "unknown")
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Secure-analyzer returned {response.status}: {error_text}"
                        }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to connect to secure-analyzer: {str(e)}"
            }
    
    def _calculate_risk_level(self, vulnerabilities: List[Dict], secure_analyzer_result: Dict) -> str:
        """Calculate overall risk level for a tool"""
        
        # Count vulnerabilities by severity
        high_count = len([v for v in vulnerabilities if v.get("severity") == "high"])
        medium_count = len([v for v in vulnerabilities if v.get("severity") == "medium"])
        low_count = len([v for v in vulnerabilities if v.get("severity") == "low"])
        
        # Factor in secure-analyzer results
        if secure_analyzer_result.get("success"):
            analyzer_data = secure_analyzer_result.get("analysis", {})
            # This would depend on the actual secure-analyzer response format
            if analyzer_data.get("risk_level") == "high":
                high_count += 1
        
        # Determine overall risk
        if high_count > 0:
            return "high"
        elif medium_count > 2:
            return "high"
        elif medium_count > 0 or low_count > 3:
            return "medium"
        else:
            return "low"
    
    def _generate_security_recommendations(self, vulnerabilities: List[Dict], tool: Dict) -> List[str]:
        """Generate security recommendations based on vulnerabilities"""
        
        recommendations = []
        
        # Generic recommendations based on vulnerability types
        vuln_types = [v.get("type") for v in vulnerabilities]
        
        if any("injection" in vt for vt in vuln_types):
            recommendations.append("Implement comprehensive input validation and sanitization")
            recommendations.append("Use parameterized queries for database operations")
        
        if any("auth" in vt or "credential" in vt for vt in vuln_types):
            recommendations.append("Implement proper authentication and authorization controls")
            recommendations.append("Use secure credential storage and transmission")
        
        if any("file" in vt or "path" in vt for vt in vuln_types):
            recommendations.append("Restrict file operations to allowed directories")
            recommendations.append("Validate and sanitize all file paths")
        
        if any("exposure" in vt for vt in vuln_types):
            recommendations.append("Implement data access controls and field filtering")
            recommendations.append("Review and minimize data exposure in API responses")
        
        # Tool-specific recommendations
        if tool.get("method") == "DELETE":
            recommendations.append("Implement confirmation mechanisms for destructive operations")
        
        if tool.get("category") == "admin":
            recommendations.append("Require elevated privileges for administrative operations")
        
        # Default recommendations
        if not recommendations:
            recommendations.append("Review tool implementation for security best practices")
            recommendations.append("Implement logging and monitoring for tool usage")
        
        return list(set(recommendations))  # Remove duplicates
    
    async def scan_tool_catalog(self, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Scan an entire catalog of tools for security issues"""
        
        print("🔒 PHASE 4: SECURITY SCANNING WITH SECURE-ANALYZER")
        print("=" * 60)
        
        scan_results = {
            "timestamp": datetime.now().isoformat(),
            "tools_scanned": len(tools),
            "security_summary": {
                "high_risk": 0,
                "medium_risk": 0,
                "low_risk": 0,
                "secure_analyzer_success": 0,
                "secure_analyzer_failures": 0
            },
            "tool_results": [],
            "overall_assessment": "",
            "critical_findings": []
        }
        
        print(f"🔍 Scanning {len(tools)} tools for security vulnerabilities...")
        
        for i, tool in enumerate(tools, 1):
            print(f"\n[{i}/{len(tools)}] Scanning: {tool.get('name', 'Unknown')}")
            
            # Scan individual tool
            tool_security = await self.scan_tool_security(tool)
            scan_results["tool_results"].append(tool_security)
            
            # Update summary
            risk_level = tool_security["risk_level"]
            scan_results["security_summary"][f"{risk_level}_risk"] += 1
            
            if tool_security["secure_analyzer_result"].get("success"):
                scan_results["security_summary"]["secure_analyzer_success"] += 1
            else:
                scan_results["security_summary"]["secure_analyzer_failures"] += 1
            
            # Collect critical findings
            high_vulns = [v for v in tool_security["vulnerabilities"] if v.get("severity") == "high"]
            if high_vulns:
                for vuln in high_vulns:
                    scan_results["critical_findings"].append({
                        "tool": tool["name"],
                        "service": tool["service"],
                        "vulnerability": vuln
                    })
            
            print(f"  Risk Level: {risk_level.upper()}")
            print(f"  Vulnerabilities: {len(tool_security['vulnerabilities'])}")
            if tool_security["secure_analyzer_result"].get("success"):
                print(f"  Secure-Analyzer: ✅ Success")
            else:
                print(f"  Secure-Analyzer: ❌ {tool_security['secure_analyzer_result'].get('error', 'Failed')}")
        
        # Generate overall assessment
        total_tools = scan_results["tools_scanned"]
        high_risk = scan_results["security_summary"]["high_risk"]
        medium_risk = scan_results["security_summary"]["medium_risk"]
        
        if high_risk > total_tools * 0.3:
            scan_results["overall_assessment"] = "CRITICAL - Many high-risk tools detected"
        elif high_risk > 0 or medium_risk > total_tools * 0.5:
            scan_results["overall_assessment"] = "WARNING - Security issues require attention"
        else:
            scan_results["overall_assessment"] = "ACCEPTABLE - Low security risk overall"
        
        return scan_results
    
    async def create_security_report(self, scan_results: Dict[str, Any], filename: str):
        """Create a comprehensive security report"""
        
        summary = scan_results["security_summary"]
        total = scan_results["tools_scanned"]
        
        report = f"""# 🔒 Phase 4: Security Scanning Report

**Generated:** {scan_results['timestamp']}
**Overall Assessment:** {scan_results['overall_assessment']}

## 📊 Security Summary

- **Tools Scanned:** {total}
- **High Risk:** {summary['high_risk']} ({(summary['high_risk']/total)*100:.1f}%)
- **Medium Risk:** {summary['medium_risk']} ({(summary['medium_risk']/total)*100:.1f}%)
- **Low Risk:** {summary['low_risk']} ({(summary['low_risk']/total)*100:.1f}%)
- **Secure-Analyzer Success Rate:** {summary['secure_analyzer_success']}/{total} ({(summary['secure_analyzer_success']/total)*100:.1f}%)

## 🚨 Critical Findings

"""
        
        if scan_results["critical_findings"]:
            for finding in scan_results["critical_findings"]:
                vuln = finding["vulnerability"]
                report += f"""### {finding['tool']} ({finding['service']})
- **Type:** {vuln['type']}
- **Severity:** {vuln['severity'].upper()}
- **Description:** {vuln['description']}
- **Location:** {vuln['location']}
- **Mitigation:** {vuln['mitigation']}

"""
        else:
            report += "No critical security findings detected.\n\n"
        
        report += """## 🛠️ Tool Security Details

"""
        
        for tool_result in scan_results["tool_results"]:
            risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}[tool_result["risk_level"]]
            
            report += f"""### {risk_emoji} {tool_result['tool_name']}
- **Service:** {tool_result['service']}
- **Risk Level:** {tool_result['risk_level'].upper()}
- **Vulnerabilities:** {len(tool_result['vulnerabilities'])}
- **Secure-Analyzer:** {"✅" if tool_result['secure_analyzer_result'].get('success') else "❌"}

"""
            
            if tool_result["vulnerabilities"]:
                report += "**Vulnerabilities:**\n"
                for vuln in tool_result["vulnerabilities"]:
                    report += f"- {vuln['type']} ({vuln['severity']}): {vuln['description']}\n"
                report += "\n"
            
            if tool_result["recommendations"]:
                report += "**Recommendations:**\n"
                for rec in tool_result["recommendations"]:
                    report += f"- {rec}\n"
                report += "\n"
        
        report += """## 🎯 Next Steps

1. **Address Critical Findings:** Fix all high-severity vulnerabilities immediately
2. **Implement Security Controls:** Add authentication, input validation, and access controls
3. **Regular Scanning:** Integrate security scanning into CI/CD pipeline  
4. **Monitor Usage:** Implement logging and monitoring for tool usage
5. **Security Training:** Ensure development team understands secure coding practices

"""
        
        with open(filename, 'w') as f:
            f.write(report)
        
        print(f"🔒 Security report saved to {filename}")

async def main():
    """Main execution function for security scanning"""
    
    print("🔒 Starting Phase 4: Security Scanning with Secure-Analyzer")
    
    scanner = ToolSecurityScanner()
    
    # For demo purposes, create some sample tools
    # In real implementation, this would load from Phase 2 discovery results
    sample_tools = [
        {
            "name": "analysis_service_analyze_document",
            "service": "analysis-service",
            "path": "/api/analyze/document", 
            "method": "POST",
            "category": "analysis",
            "parameters": [
                {"name": "document_id", "type": "string", "required": True, "location": "body"},
                {"name": "analysis_type", "type": "string", "required": False, "location": "query"}
            ]
        },
        {
            "name": "memory_agent_admin_delete",
            "service": "memory-agent", 
            "path": "/admin/delete/all",
            "method": "DELETE",
            "category": "admin",
            "parameters": [
                {"name": "confirm_token", "type": "string", "required": True, "location": "query"}
            ]
        },
        {
            "name": "doc_store_upload_file",
            "service": "doc_store",
            "path": "/upload/file",
            "method": "POST", 
            "category": "storage",
            "parameters": [
                {"name": "file_path", "type": "string", "required": True, "location": "body"},
                {"name": "user_id", "type": "string", "required": True, "location": "body"}
            ]
        }
    ]
    
    try:
        # Run security scanning
        results = await scanner.scan_tool_catalog(sample_tools)
        
        # Create security report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"security_scan_report_{timestamp}.md"
        await scanner.create_security_report(results, report_filename)
        
        # Save detailed results
        results_filename = f"security_scan_results_{timestamp}.json"
        with open(results_filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n🎉 PHASE 4 SECURITY SCANNING COMPLETE!")
        print("=" * 50)
        print(f"🔒 Tools Scanned: {results['tools_scanned']}")
        print(f"🚨 High Risk: {results['security_summary']['high_risk']}")
        print(f"⚠️ Medium Risk: {results['security_summary']['medium_risk']}")
        print(f"✅ Low Risk: {results['security_summary']['low_risk']}")
        print(f"📊 Overall: {results['overall_assessment']}")
        
        print(f"\n📋 Reports generated:")
        print(f"  - {report_filename}")
        print(f"  - {results_filename}")
        
    except Exception as e:
        print(f"❌ Security scanning failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
