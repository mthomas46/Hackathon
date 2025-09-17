"""Summarization Service Domain Service"""

from typing import Dict, Any, List, Optional, Tuple
import re

from ..value_objects.summarization_request import SummarizationRequest


class SummarizationService:
    """Domain service for text summarization operations."""

    def __init__(self):
        """Initialize summarization service."""
        self._ai_providers = self._load_ai_providers()

    def _load_ai_providers(self) -> Dict[str, Dict[str, Any]]:
        """Load available AI providers and their capabilities."""
        # In a real implementation, this would be loaded from configuration
        return {
            'openai_gpt4': {
                'name': 'OpenAI GPT-4',
                'max_tokens': 8192,
                'supported_styles': ['neutral', 'formal', 'casual', 'technical', 'executive'],
                'cost_per_token': 0.03
            },
            'anthropic_claude': {
                'name': 'Anthropic Claude',
                'max_tokens': 100000,
                'supported_styles': ['neutral', 'formal', 'technical', 'executive'],
                'cost_per_token': 0.015
            },
            'local_llm': {
                'name': 'Local LLM',
                'max_tokens': 4096,
                'supported_styles': ['neutral', 'technical'],
                'cost_per_token': 0.0
            }
        }

    def suggest_summarization_providers(self, request: SummarizationRequest) -> Dict[str, Any]:
        """
        Suggest appropriate AI providers for summarization based on content and policies.

        Args:
            request: Summarization request with content and parameters

        Returns:
            Dict containing provider suggestions and policy information
        """
        content_analysis = self._analyze_content(request)
        policy_compliant_providers = self._get_policy_compliant_providers(request, content_analysis)

        # If override policy is set, include all providers
        if request.override_policy:
            policy_compliant_providers = list(self._ai_providers.keys())

        return {
            'content_analysis': content_analysis,
            'allowed_providers': policy_compliant_providers,
            'recommended_provider': self._select_best_provider(policy_compliant_providers, request),
            'policy_override_used': request.override_policy,
            'rationale': self._generate_provider_rationale(policy_compliant_providers, content_analysis)
        }

    def _analyze_content(self, request: SummarizationRequest) -> Dict[str, Any]:
        """Analyze content characteristics for provider selection."""
        content = request.content

        # Basic content metrics
        word_count = len(content.split())
        sentence_count = len(re.split(r'[.!?]+', content))
        avg_words_per_sentence = word_count / sentence_count if sentence_count > 0 else 0

        # Content type detection
        content_type = self._detect_content_type(content)

        # Complexity assessment
        complexity_score = self._assess_complexity(content)

        # Keyword analysis
        keyword_density = len(request.keywords) / word_count if word_count > 0 else 0

        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_words_per_sentence': avg_words_per_sentence,
            'content_type': content_type,
            'complexity_score': complexity_score,
            'keyword_density': keyword_density,
            'estimated_summary_tokens': self._estimate_summary_tokens(content, request)
        }

    def _detect_content_type(self, content: str) -> str:
        """Detect the type of content being summarized."""
        content_lower = content.lower()

        # Technical content indicators
        technical_indicators = ['api', 'function', 'class', 'method', 'algorithm', 'database', 'server']
        technical_score = sum(1 for indicator in technical_indicators if indicator in content_lower)

        # Business content indicators
        business_indicators = ['strategy', 'revenue', 'customer', 'market', 'product', 'sales']
        business_score = sum(1 for indicator in business_indicators if indicator in content_lower)

        # Code indicators
        code_indicators = ['import ', 'def ', 'class ', 'function(', 'const ', 'let ']
        code_score = sum(1 for indicator in code_indicators if indicator in content_lower)

        # Determine content type
        if code_score > business_score and code_score > technical_score:
            return 'code'
        elif technical_score > business_score:
            return 'technical'
        elif business_score > 0:
            return 'business'
        else:
            return 'general'

    def _assess_complexity(self, content: str) -> float:
        """Assess content complexity on a scale of 0-1."""
        # Simple heuristics for complexity assessment
        word_count = len(content.split())
        unique_words = len(set(content.lower().split()))
        avg_word_length = sum(len(word) for word in content.split()) / word_count if word_count > 0 else 0

        # Technical terms (rough approximation)
        technical_terms = ['algorithm', 'infrastructure', 'architecture', 'implementation', 'optimization']
        technical_density = sum(1 for term in technical_terms if term in content.lower()) / len(technical_terms)

        # Complexity score (0-1)
        complexity = min(1.0, (
            (unique_words / word_count if word_count > 0 else 0) * 0.3 +
            (avg_word_length / 10) * 0.3 +
            technical_density * 0.4
        ))

        return complexity

    def _estimate_summary_tokens(self, content: str, request: SummarizationRequest) -> int:
        """Estimate the number of tokens needed for summary."""
        content_tokens = len(content.split()) * 1.3  # Rough token estimation

        # Adjust based on requested length
        if request.max_length:
            max_tokens = min(content_tokens * 0.3, request.max_length * 1.3)
        else:
            max_tokens = content_tokens * 0.2  # Default 20% of original

        if request.min_length:
            min_tokens = request.min_length * 1.3
            return int(max(min_tokens, min(max_tokens, content_tokens * 0.3)))
        else:
            return int(max_tokens)

    def _get_policy_compliant_providers(self, request: SummarizationRequest, content_analysis: Dict[str, Any]) -> List[str]:
        """Get providers that comply with organizational policies."""
        compliant_providers = []

        content_type = content_analysis['content_type']
        complexity = content_analysis['complexity_score']

        for provider_id, provider_info in self._ai_providers.items():
            # Check if provider supports the requested style
            if request.style not in provider_info['supported_styles']:
                continue

            # Policy rules (simplified example)
            if content_type == 'code' and provider_id not in ['local_llm']:
                # Code content should prefer local models for security
                continue

            if complexity > 0.7 and provider_id == 'local_llm':
                # High complexity content needs more capable models
                continue

            compliant_providers.append(provider_id)

        return compliant_providers

    def _select_best_provider(self, allowed_providers: List[str], request: SummarizationRequest) -> Optional[str]:
        """Select the best provider from allowed list."""
        if not allowed_providers:
            return None

        # Simple selection logic (could be more sophisticated)
        if request.override_policy:
            # Prefer most capable provider when policy is overridden
            priority_order = ['openai_gpt4', 'anthropic_claude', 'local_llm']
        else:
            # Prefer cost-effective and local options by default
            priority_order = ['local_llm', 'anthropic_claude', 'openai_gpt4']

        for provider in priority_order:
            if provider in allowed_providers:
                return provider

        return allowed_providers[0]

    def _generate_provider_rationale(self, providers: List[str], content_analysis: Dict[str, Any]) -> str:
        """Generate rationale for provider selection."""
        if not providers:
            return "No providers available that meet policy and capability requirements."

        content_type = content_analysis['content_type']
        complexity = content_analysis['complexity_score']

        rationales = []

        if content_type == 'code':
            rationales.append("Content appears to be code-related, prioritizing local models for security.")
        elif complexity > 0.7:
            rationales.append("High complexity content requires capable AI models.")
        elif 'local_llm' in providers:
            rationales.append("Local model preferred for cost and privacy reasons.")

        if not rationales:
            rationales.append("Standard provider selection based on availability and policies.")

        return ' '.join(rationales)

    def validate_summarization_request(self, request: SummarizationRequest) -> List[str]:
        """Validate summarization request and return list of validation errors."""
        errors = []

        if not request.content or len(request.content.strip()) < 10:
            errors.append("Content must be at least 10 characters long")

        if request.max_length and request.min_length and request.max_length <= request.min_length:
            errors.append("Maximum length must be greater than minimum length")

        if request.keywords and len(request.keywords) > 50:
            errors.append("Cannot specify more than 50 keywords")

        return errors

    def generate_summarization_prompt(self, request: SummarizationRequest, provider: str) -> str:
        """Generate a summarization prompt for the specified provider."""
        provider_info = self._ai_providers.get(provider, {})

        prompt_parts = [
            f"Please provide a {request.style} summary of the following content:"
        ]

        if request.max_length:
            prompt_parts.append(f"Keep the summary under {request.max_length} words.")
        elif request.min_length:
            prompt_parts.append(f"Ensure the summary is at least {request.min_length} words.")

        if request.keywords:
            prompt_parts.append(f"Focus on these key terms: {', '.join(request.keywords)}")

        if request.keyword_document:
            prompt_parts.append(f"Use this context for terminology: {request.keyword_document}")

        prompt_parts.append(f"\nContent to summarize:\n{request.content}")

        return '\n\n'.join(prompt_parts)
