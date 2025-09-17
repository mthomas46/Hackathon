"""LLM Gateway Integration Module for Secure Analyzer Service.

Provides integration between the Secure Analyzer and LLM Gateway for:
- LLM-powered security analysis and threat detection
- Enhanced content classification using LLM capabilities
- Intelligent security recommendations based on LLM analysis
- Automated security policy generation and enforcement
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.shared.integrations.clients.clients import ServiceClients
from services.shared.core.constants_new import ServiceNames
from services.shared.monitoring.logging import fire_and_forget
from services.shared.core.config.config import get_config_value


class LLMGatewayIntegration:
    """Integration layer between Secure Analyzer and LLM Gateway."""

    def __init__(self):
        self.clients = ServiceClients()
        self.llm_gateway_url = get_config_value("LLM_GATEWAY_URL", "http://llm-gateway:5055", section="services")

    async def enhance_security_analysis_with_llm(self, content: str,
                                               basic_findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use LLM Gateway to enhance basic security analysis with intelligent insights."""
        try:
            findings_summary = "\n".join([
                f"- {finding.get('type', 'Unknown')}: {finding.get('description', 'No description')} "
                f"(Severity: {finding.get('severity', 'Unknown')})"
                for finding in basic_findings[:10]  # Limit for LLM input
            ])

            enhancement_prompt = f"""
You are an expert cybersecurity analyst. Review the following content and basic security findings, then provide enhanced analysis.

Content to Analyze:
{content[:2000]}...  # Truncated for input limits

Basic Security Findings:
{findings_summary}

Provide enhanced security analysis including:
1. Risk assessment and potential impact
2. Attack vectors and exploitation scenarios
3. Recommended mitigation strategies
4. Compliance implications
5. Data classification recommendations
6. Additional security concerns not captured by basic analysis

Focus on practical security implications and actionable recommendations.

Return your analysis as a JSON object with keys: risk_assessment, attack_vectors, mitigation_strategies, compliance_implications, data_classification, additional_concerns, overall_risk_level
            """.strip()

            llm_request = {
                "prompt": enhancement_prompt,
                "provider": "ollama",  # Use local for security
                "max_tokens": 1200,
                "temperature": 0.2
            }

            response = await self.clients.post_json(f"{self.llm_gateway_url}/query", llm_request)

            if response.get("success"):
                llm_response = response["data"]["response"]
                try:
                    import json
                    enhanced_analysis = json.loads(llm_response)

                    return {
                        "enhanced_security_analysis": enhanced_analysis,
                        "basic_findings_count": len(basic_findings),
                        "analysis_method": "llm_enhanced",
                        "llm_provider": response["data"]["provider"],
                        "enhancement_timestamp": datetime.now().isoformat()
                    }

                except json.JSONDecodeError:
                    return {
                        "enhanced_security_analysis": {
                            "risk_assessment": "Unable to parse LLM analysis",
                            "attack_vectors": [],
                            "mitigation_strategies": [],
                            "overall_risk_level": "unknown"
                        },
                        "error": "Failed to parse LLM security analysis",
                        "analysis_method": "llm_enhanced_error",
                        "raw_response": llm_response[:500]
                    }
            else:
                return {
                    "enhanced_security_analysis": {
                        "risk_assessment": "LLM analysis unavailable",
                        "attack_vectors": [],
                        "mitigation_strategies": [],
                        "overall_risk_level": "unknown"
                    },
                    "error": response.get("message", "LLM Gateway request failed"),
                    "analysis_method": "gateway_error_fallback"
                }

        except Exception as e:
            fire_and_forget(
                "secure_analyzer_llm_enhancement_error",
                f"LLM security enhancement error: {str(e)}",
                ServiceNames.SECURE_ANALYZER,
                {
                    "content_length": len(content),
                    "basic_findings_count": len(basic_findings),
                    "error": str(e)
                }
            )
            return {
                "enhanced_security_analysis": {
                    "risk_assessment": f"Analysis error: {str(e)}",
                    "attack_vectors": [],
                    "mitigation_strategies": [],
                    "overall_risk_level": "error"
                },
                "error": str(e),
                "analysis_method": "error_fallback"
            }

    async def intelligent_provider_recommendation(self, content: str,
                                                security_findings: List[Dict[str, Any]],
                                                available_providers: List[str]) -> Dict[str, Any]:
        """Use LLM Gateway to recommend the most secure provider for content processing."""
        try:
            findings_summary = "\n".join([
                f"- {finding.get('type', 'Unknown')}: {finding.get('severity', 'Unknown')} severity"
                for finding in security_findings[:5]
            ])

            recommendation_prompt = f"""
You are a security expert advising on LLM provider selection for sensitive content.

Content Security Analysis:
- Content contains sensitive information: {bool(security_findings)}
- Security findings: {findings_summary}
- Content length: {len(content)} characters

Available Providers:
{', '.join(available_providers)}

Security Considerations by Provider:
- ollama: Local processing, highest security, no data transmission
- bedrock: AWS security, encrypted processing, compliance certifications
- openai/anthropic/grok: Cloud processing, data transmission risks, varying security levels

Based on the security analysis, recommend the most appropriate provider and explain your reasoning.

Return a JSON object with keys: recommended_provider, reasoning, security_score, risk_level, alternative_providers
            """.strip()

            llm_request = {
                "prompt": recommendation_prompt,
                "provider": "ollama",  # Use local for security decisions
                "max_tokens": 800,
                "temperature": 0.1
            }

            response = await self.clients.post_json(f"{self.llm_gateway_url}/query", llm_request)

            if response.get("success"):
                llm_response = response["data"]["response"]
                try:
                    import json
                    provider_recommendation = json.loads(llm_response)
                    return {
                        "provider_recommendation": provider_recommendation,
                        "recommendation_method": "llm_security_aware",
                        "content_security_level": "high" if security_findings else "low",
                        "available_providers": available_providers,
                        "llm_provider": response["data"]["provider"]
                    }
                except json.JSONDecodeError:
                    return {
                        "provider_recommendation": {
                            "recommended_provider": "ollama",  # Default to secure
                            "reasoning": "Secure fallback due to parsing error",
                            "security_score": 9,
                            "risk_level": "low"
                        },
                        "error": "Failed to parse provider recommendation",
                        "recommendation_method": "llm_security_aware_error"
                    }
            else:
                return {
                    "provider_recommendation": {
                        "recommended_provider": "ollama",  # Default to secure
                        "reasoning": "Secure fallback due to gateway error",
                        "security_score": 9,
                        "risk_level": "low"
                    },
                    "error": response.get("message", "LLM Gateway request failed"),
                    "recommendation_method": "gateway_error_fallback"
                }

        except Exception as e:
            fire_and_forget(
                "secure_analyzer_provider_recommendation_error",
                f"Provider recommendation error: {str(e)}",
                ServiceNames.SECURE_ANALYZER,
                {
                    "content_length": len(content),
                    "security_findings_count": len(security_findings),
                    "available_providers_count": len(available_providers),
                    "error": str(e)
                }
            )
            return {
                "provider_recommendation": {
                    "recommended_provider": "ollama",  # Always default to secure
                    "reasoning": f"Error occurred, defaulting to secure provider: {str(e)}",
                    "security_score": 10,
                    "risk_level": "minimal"
                },
                "error": str(e),
                "recommendation_method": "error_secure_fallback"
            }

    async def generate_security_policy_with_llm(self, content_patterns: List[Dict[str, Any]],
                                              historical_incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use LLM Gateway to generate intelligent security policies based on patterns and incidents."""
        try:
            patterns_summary = "\n".join([
                f"- {pattern.get('type', 'Unknown')}: {pattern.get('description', 'No description')} "
                f"(Frequency: {pattern.get('frequency', 0)})"
                for pattern in content_patterns[:10]
            ])

            incidents_summary = "\n".join([
                f"- {incident.get('type', 'Unknown')}: {incident.get('description', 'No description')} "
                f"(Impact: {incident.get('impact', 'Unknown')})"
                for incident in historical_incidents[:5]
            ])

            policy_prompt = f"""
You are a security policy expert. Based on content patterns and historical security incidents, generate comprehensive security policies.

Content Patterns Observed:
{patterns_summary}

Historical Security Incidents:
{incidents_summary}

Generate security policies including:
1. Content classification rules
2. Provider selection criteria
3. Data handling procedures
4. Monitoring and alerting rules
5. Incident response procedures
6. Compliance requirements

Focus on practical, implementable policies that balance security with usability.

Return the policy recommendations as a JSON object with keys: content_classification, provider_criteria, data_handling, monitoring_rules, incident_response, compliance_requirements
            """.strip()

            llm_request = {
                "prompt": policy_prompt,
                "provider": "ollama",
                "max_tokens": 1500,
                "temperature": 0.2
            }

            response = await self.clients.post_json(f"{self.llm_gateway_url}/query", llm_request)

            if response.get("success"):
                llm_response = response["data"]["response"]
                try:
                    import json
                    security_policies = json.loads(llm_response)

                    return {
                        "security_policies": security_policies,
                        "generation_method": "llm_intelligent",
                        "input_patterns_count": len(content_patterns),
                        "input_incidents_count": len(historical_incidents),
                        "llm_provider": response["data"]["provider"],
                        "generation_timestamp": datetime.now().isoformat()
                    }

                except json.JSONDecodeError:
                    return {
                        "security_policies": {
                            "content_classification": [],
                            "provider_criteria": {"default_provider": "ollama"},
                            "data_handling": [],
                            "monitoring_rules": [],
                            "incident_response": [],
                            "compliance_requirements": []
                        },
                        "error": "Failed to parse LLM-generated policies",
                        "generation_method": "llm_intelligent_error",
                        "raw_response": llm_response[:500]
                    }
            else:
                return {
                    "security_policies": {
                        "content_classification": [],
                        "provider_criteria": {"default_provider": "ollama"},
                        "data_handling": [],
                        "monitoring_rules": [],
                        "incident_response": [],
                        "compliance_requirements": []
                    },
                    "error": response.get("message", "LLM Gateway request failed"),
                    "generation_method": "gateway_error_fallback"
                }

        except Exception as e:
            fire_and_forget(
                "secure_analyzer_policy_generation_error",
                f"Security policy generation error: {str(e)}",
                ServiceNames.SECURE_ANALYZER,
                {
                    "patterns_count": len(content_patterns),
                    "incidents_count": len(historical_incidents),
                    "error": str(e)
                }
            )
            return {
                "security_policies": {
                    "content_classification": [],
                    "provider_criteria": {"default_provider": "ollama"},
                    "data_handling": [],
                    "monitoring_rules": [],
                    "incident_response": [],
                    "compliance_requirements": []
                },
                "error": str(e),
                "generation_method": "error_fallback"
            }

    async def analyze_compliance_with_llm(self, content: str,
                                        compliance_frameworks: List[str]) -> Dict[str, Any]:
        """Use LLM Gateway to analyze content for compliance with various frameworks."""
        try:
            frameworks_str = ", ".join(compliance_frameworks)

            compliance_prompt = f"""
You are a compliance expert. Analyze the following content for compliance with specified frameworks.

Content to Analyze:
{content[:3000]}...  # Truncated for input limits

Compliance Frameworks: {frameworks_str}

For each framework, assess:
1. Compliance level (compliant/partial/non-compliant)
2. Specific requirements met
3. Requirements not met
4. Recommended remediation actions
5. Risk implications

Consider data handling, privacy, security, and regulatory requirements.

Return your compliance analysis as a JSON object with framework names as keys and compliance assessments as values.
            """.strip()

            llm_request = {
                "prompt": compliance_prompt,
                "provider": "ollama",
                "max_tokens": 1200,
                "temperature": 0.1
            }

            response = await self.clients.post_json(f"{self.llm_gateway_url}/query", llm_request)

            if response.get("success"):
                llm_response = response["data"]["response"]
                try:
                    import json
                    compliance_analysis = json.loads(llm_response)

                    return {
                        "compliance_analysis": compliance_analysis,
                        "analysis_method": "llm_compliance_expert",
                        "frameworks_analyzed": compliance_frameworks,
                        "content_length": len(content),
                        "llm_provider": response["data"]["provider"],
                        "analysis_timestamp": datetime.now().isoformat()
                    }

                except json.JSONDecodeError:
                    return {
                        "compliance_analysis": {
                            framework: {
                                "compliance_level": "unknown",
                                "requirements_met": [],
                                "requirements_not_met": [],
                                "remediation_actions": [],
                                "risk_implications": "Unable to analyze"
                            }
                            for framework in compliance_frameworks
                        },
                        "error": "Failed to parse compliance analysis",
                        "analysis_method": "llm_compliance_expert_error"
                    }
            else:
                return {
                    "compliance_analysis": {
                        framework: {
                            "compliance_level": "unknown",
                            "requirements_met": [],
                            "requirements_not_met": [],
                            "remediation_actions": [],
                            "risk_implications": "Analysis unavailable"
                        }
                        for framework in compliance_frameworks
                    },
                    "error": response.get("message", "LLM Gateway request failed"),
                    "analysis_method": "gateway_error_fallback"
                }

        except Exception as e:
            fire_and_forget(
                "secure_analyzer_compliance_analysis_error",
                f"Compliance analysis error: {str(e)}",
                ServiceNames.SECURE_ANALYZER,
                {
                    "content_length": len(content),
                    "frameworks_count": len(compliance_frameworks),
                    "error": str(e)
                }
            )
            return {
                "compliance_analysis": {
                    framework: {
                        "compliance_level": "error",
                        "requirements_met": [],
                        "requirements_not_met": [],
                        "remediation_actions": [],
                        "risk_implications": str(e)
                    }
                    for framework in compliance_frameworks
                },
                "error": str(e),
                "analysis_method": "error_fallback"
            }


# Global instance
llm_gateway_integration = LLMGatewayIntegration()
