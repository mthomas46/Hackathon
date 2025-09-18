"""Security Filter Module for LLM Gateway Service.

Handles security-aware routing and content analysis to ensure sensitive content
is routed to appropriate LLM providers based on security policies.
"""

import re
from typing import Dict, Any, List, Set
from dataclasses import dataclass

from services.shared.config import get_config_value
from services.shared.logging import fire_and_forget
from services.shared.constants_new import ServiceNames


@dataclass
class SecurityAnalysis:
    """Result of security content analysis."""
    is_sensitive: bool
    sensitivity_score: float
    detected_keywords: List[str]
    categories: List[str]
    recommendations: List[str]


class SecurityFilter:
    """Security-aware content analysis and provider routing."""

    def __init__(self):
        self.sensitive_keywords = self._load_sensitive_keywords()
        self.security_policies = self._load_security_policies()

    def _load_sensitive_keywords(self) -> Set[str]:
        """Load sensitive keywords from configuration."""
        # Default sensitive keywords
        default_keywords = {
            # Authentication & Security
            'password', 'passwd', 'pwd', 'secret', 'token', 'key', 'credential',
            'auth', 'authentication', 'authorization', 'oauth', 'bearer',

            # Personal Information
            'ssn', 'social security', 'credit card', 'ccv', 'cvv', 'pin',
            'address', 'phone', 'email', 'birthdate', 'social security number',

            # Financial Information
            'bank account', 'routing number', 'iban', 'swift', 'bitcoin',
            'wallet', 'private key', 'seed phrase',

            # Confidential Business Info
            'confidential', 'internal', 'proprietary', 'trade secret',
            'nd', 'non-disclosure', 'nda', 'intellectual property',

            # Health Information
            'medical', 'health', 'diagnosis', 'treatment', 'patient',
            'phi', 'protected health information',

            # Legal Information
            'contract', 'agreement', 'legal', 'litigation', 'compliance'
        }

        # Try to load from config
        try:
            config_keywords = get_config_value("SENSITIVE_KEYWORDS", "", section="security")
            if config_keywords:
                # Parse comma-separated keywords
                additional_keywords = {kw.strip().lower() for kw in config_keywords.split(',')}
                default_keywords.update(additional_keywords)
        except:
            pass

        return default_keywords

    def _load_security_policies(self) -> Dict[str, Any]:
        """Load security policies from configuration."""
        return {
            "sensitive_only_providers": get_config_value(
                "SECURE_ONLY_MODELS", "ollama,bedrock", section="secure_analyzer"
            ).split(','),

            "all_providers": get_config_value(
                "ALL_PROVIDERS", "bedrock,ollama,openai,anthropic,grok", section="secure_analyzer"
            ).split(','),

            "sensitivity_threshold": float(get_config_value(
                "SENSITIVITY_THRESHOLD", "0.7", section="security"
            )),

            "auto_classify": get_config_value(
                "AUTO_CLASSIFY_SENSITIVE", "true", section="security"
            ).lower() == "true"
        }

    async def analyze_content(self, content: str) -> SecurityAnalysis:
        """Analyze content for security sensitivity."""
        if not content:
            return SecurityAnalysis(
                is_sensitive=False,
                sensitivity_score=0.0,
                detected_keywords=[],
                categories=[],
                recommendations=[]
            )

        content_lower = content.lower()

        # Find sensitive keywords
        detected_keywords = []
        for keyword in self.sensitive_keywords:
            if keyword in content_lower:
                detected_keywords.append(keyword)

        # Calculate sensitivity score
        sensitivity_score = min(len(detected_keywords) * 0.2, 1.0)

        # Determine if content is sensitive
        threshold = self.security_policies["sensitivity_threshold"]
        is_sensitive = sensitivity_score >= threshold

        # Categorize content
        categories = self._categorize_content(content_lower, detected_keywords)

        # Generate recommendations
        recommendations = self._generate_security_recommendations(
            is_sensitive, sensitivity_score, categories
        )

        # Log security analysis
        if is_sensitive or detected_keywords:
            fire_and_forget(
                "llm_gateway_security_analysis",
                f"Content security analysis: sensitive={is_sensitive}, score={sensitivity_score:.2f}",
                ServiceNames.LLM_GATEWAY,
                {
                    "sensitivity_score": sensitivity_score,
                    "detected_keywords_count": len(detected_keywords),
                    "categories": categories,
                    "is_sensitive": is_sensitive
                }
            )

        return SecurityAnalysis(
            is_sensitive=is_sensitive,
            sensitivity_score=sensitivity_score,
            detected_keywords=detected_keywords,
            categories=categories,
            recommendations=recommendations
        )

    def _categorize_content(self, content: str, detected_keywords: List[str]) -> List[str]:
        """Categorize content based on detected patterns."""
        categories = []

        # Authentication & Security
        if any(kw in detected_keywords for kw in ['password', 'token', 'key', 'secret']):
            categories.append("authentication")

        # Personal Information
        if any(kw in detected_keywords for kw in ['ssn', 'email', 'phone', 'address']):
            categories.append("personal_data")

        # Financial Information
        if any(kw in detected_keywords for kw in ['credit card', 'bank account', 'bitcoin']):
            categories.append("financial_data")

        # Health Information
        if any(kw in detected_keywords for kw in ['medical', 'health', 'patient']):
            categories.append("health_data")

        # Business Confidential
        if any(kw in detected_keywords for kw in ['confidential', 'internal', 'proprietary']):
            categories.append("business_confidential")

        # Legal Information
        if any(kw in detected_keywords for kw in ['contract', 'legal', 'compliance']):
            categories.append("legal_information")

        # Code/Security patterns
        if 'import' in content or 'function' in content or 'class' in content:
            if any(kw in detected_keywords for kw in ['secret', 'key', 'token']):
                categories.append("code_security")

        return categories

    def _generate_security_recommendations(self, is_sensitive: bool, score: float,
                                         categories: List[str]) -> List[str]:
        """Generate security recommendations based on analysis."""
        recommendations = []

        if is_sensitive:
            recommendations.append("Content flagged as sensitive - routing to secure providers only")

            if "authentication" in categories:
                recommendations.append("Avoid including authentication credentials in prompts")

            if "personal_data" in categories:
                recommendations.append("Consider anonymizing personal data before processing")

            if "financial_data" in categories:
                recommendations.append("Financial data detected - ensure compliance with regulations")

        if score > 0.8:
            recommendations.append("High sensitivity score - consider manual review")

        if "code_security" in categories:
            recommendations.append("Code with security implications detected - review carefully")

        return recommendations

    async def get_allowed_providers(self, content: str) -> List[str]:
        """Get list of allowed providers for given content."""
        analysis = await self.analyze_content(content)

        if analysis.is_sensitive:
            return self.security_policies["sensitive_only_providers"]
        else:
            return self.security_policies["all_providers"]

    async def should_route_to_secure_provider(self, content: str) -> bool:
        """Determine if content should be routed to secure providers only."""
        analysis = await self.analyze_content(content)
        return analysis.is_sensitive

    def update_sensitive_keywords(self, new_keywords: List[str]):
        """Update the list of sensitive keywords."""
        self.sensitive_keywords.update(kw.lower() for kw in new_keywords)

        fire_and_forget(
            "llm_gateway_security_keywords_updated",
            f"Updated sensitive keywords: added {len(new_keywords)} new keywords",
            ServiceNames.LLM_GATEWAY,
            {"new_keywords_count": len(new_keywords)}
        )

    def get_security_stats(self) -> Dict[str, Any]:
        """Get security analysis statistics."""
        return {
            "sensitive_keywords_count": len(self.sensitive_keywords),
            "security_policies": self.security_policies,
            "auto_classification_enabled": self.security_policies["auto_classify"]
        }
