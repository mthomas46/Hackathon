"""Security Scanner Module for Discovery Agent service.

This module provides security scanning capabilities for discovered tools
using the secure-analyzer service integration.
"""

import re
from typing import Dict, Any, List, Optional
from services.shared.clients import ServiceClients


class ToolSecurityScanner:
    """Security scanner for discovered LangGraph tools using secure-analyzer service"""

    def __init__(self, secure_analyzer_url: str = "http://localhost:5070"):
        self.secure_analyzer_url = secure_analyzer_url
        self.service_client = ServiceClients()

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

        security_analysis = {
            "tool_name": tool["name"],
            "service": tool["service"],
            "timestamp": "2025-01-17T21:30:00Z",  # Would use datetime.now()
            "risk_level": "low",
            "vulnerabilities": [],
            "recommendations": [],
            "secure_analyzer_result": None
        }

        # Analyze tool for common security risks
        vulnerabilities = []
        vulnerabilities.extend(self._analyze_injection_risks(tool))
        vulnerabilities.extend(self._analyze_auth_risks(tool))
        vulnerabilities.extend(self._analyze_data_exposure_risks(tool))
        vulnerabilities.extend(self._analyze_file_operation_risks(tool))

        # Use secure-analyzer service for advanced scanning
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
        for param in tool.get("parameters", {}).get("properties", {}):
            param_name = param.lower()

            if any(word in param_name for word in ["query", "command", "script", "code"]):
                vulnerabilities.append({
                    "type": "parameter_injection_risk",
                    "severity": "medium",
                    "description": f"Parameter '{param}' may be vulnerable to injection",
                    "location": f"parameter:{param}",
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
        for param in tool.get("parameters", {}).get("properties", {}):
            param_name = param.lower()

            if any(word in param_name for word in ["token", "password", "key", "secret"]):
                # Check if parameter is in query string (insecure)
                if param in tool.get("parameters", {}).get("query", []):
                    vulnerabilities.append({
                        "type": "credential_exposure_risk",
                        "severity": "high",
                        "description": f"Sensitive parameter '{param}' passed in URL/query",
                        "location": f"parameter:{param}",
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
        for param in tool.get("parameters", {}).get("properties", {}):
            param_name = param.lower()

            if any(word in param_name for word in ["user", "email", "private", "internal"]):
                vulnerabilities.append({
                    "type": "parameter_data_exposure",
                    "severity": "low",
                    "description": f"Parameter '{param}' may expose sensitive information",
                    "location": f"parameter:{param}",
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
        for param in tool.get("parameters", {}).get("properties", {}):
            param_name = param.lower()

            if any(word in param_name for word in ["path", "file", "directory", "folder"]):
                vulnerabilities.append({
                    "type": "path_traversal_risk",
                    "severity": "high",
                    "description": f"Path parameter '{param}' vulnerable to traversal attacks",
                    "location": f"parameter:{param}",
                    "mitigation": "Sanitize paths and restrict to allowed directories"
                })

        return vulnerabilities

    async def _scan_with_secure_analyzer(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Use the secure-analyzer service for advanced security scanning"""

        try:
            # Prepare tool data for secure-analyzer
            scan_data = {
                "content": str(tool),  # Convert tool dict to string for analysis
                "type": "tool_definition",
                "service": tool.get("service"),
                "metadata": {
                    "tool_name": tool.get("name"),
                    "method": tool.get("method"),
                    "path": tool.get("path")
                }
            }

            async with self.service_client.session() as session:
                # Use secure-analyzer's detect-content endpoint
                url = f"{self.secure_analyzer_url}/detect-content"

                async with session.post(url, json=scan_data, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "analysis": result,
                            "response_time": 0.1  # Placeholder
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

        scan_results = {
            "timestamp": "2025-01-17T21:30:00Z",
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

        print(f"🔒 Security scanning {len(tools)} tools...")

        for tool in tools:
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


# Create singleton instance
tool_security_scanner = ToolSecurityScanner()
