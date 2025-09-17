"""LLM Gateway Integration Module for Summarizer Hub Service.

Provides integration between the Summarizer Hub and LLM Gateway for:
- Enhanced summarization using LLM Gateway capabilities
- Intelligent provider selection for summarization tasks
- Cost optimization for summarization operations
- Quality enhancement through LLM-powered analysis
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.shared.integrations.clients.clients import ServiceClients
from services.shared.core.constants_new import ServiceNames
from services.shared.monitoring.logging import fire_and_forget
from services.shared.core.config.config import get_config_value


class LLMGatewayIntegration:
    """Integration layer between Summarizer Hub and LLM Gateway."""

    def __init__(self):
        self.clients = ServiceClients()
        self.llm_gateway_url = get_config_value("LLM_GATEWAY_URL", "http://llm-gateway:5055", section="services")

    async def enhance_summarization_with_llm(self, text: str, original_summary: str,
                                           summarization_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM Gateway to enhance and improve existing summarization results."""
        try:
            enhancement_prompt = f"""
You are an expert at improving technical summaries. Review the following text, its original summary, and metadata, then provide an enhanced version.

Original Text (length: {len(text)} characters):
{text[:2000]}...  # Truncated for LLM input limits

Original Summary:
{original_summary}

Summarization Metadata:
{summarization_metadata}

Provide an enhanced summary that:
1. Maintains all critical technical information
2. Improves clarity and readability
3. Adds contextual insights if missing
4. Ensures completeness without redundancy
5. Uses better technical terminology
6. Includes key metrics or data points if relevant

Return only the enhanced summary, no additional explanation.
            """.strip()

            llm_request = {
                "prompt": enhancement_prompt,
                "provider": "ollama",  # Use local for cost efficiency
                "max_tokens": 1000,
                "temperature": 0.3
            }

            response = await self.clients.post_json(f"{self.llm_gateway_url}/query", llm_request)

            if response.get("success"):
                enhanced_summary = response["data"]["response"].strip()

                # Compare original vs enhanced
                original_length = len(original_summary)
                enhanced_length = len(enhanced_summary)
                improvement_ratio = enhanced_length / original_length if original_length > 0 else 1.0

                return {
                    "enhanced_summary": enhanced_summary,
                    "original_summary": original_summary,
                    "enhancement_metadata": {
                        "llm_provider": response["data"]["provider"],
                        "processing_time": response["data"]["processing_time"],
                        "tokens_used": response["data"]["tokens_used"],
                        "original_length": original_length,
                        "enhanced_length": enhanced_length,
                        "improvement_ratio": round(improvement_ratio, 2)
                    },
                    "enhancement_method": "llm_gateway_enhanced"
                }
            else:
                return {
                    "enhanced_summary": original_summary,
                    "error": response.get("message", "LLM Gateway enhancement failed"),
                    "enhancement_method": "original_fallback"
                }

        except Exception as e:
            fire_and_forget(
                "summarizer_llm_enhancement_error",
                f"LLM enhancement error: {str(e)}",
                ServiceNames.SUMMARIZER_HUB,
                {
                    "text_length": len(text),
                    "original_summary_length": len(original_summary),
                    "error": str(e)
                }
            )
            return {
                "enhanced_summary": original_summary,
                "error": str(e),
                "enhancement_method": "error_fallback"
            }

    async def intelligent_provider_selection_for_summary(self, text: str,
                                                      summary_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM Gateway to intelligently select the best provider for summarization."""
        try:
            # Analyze text characteristics
            text_length = len(text)
            is_technical = any(keyword in text.lower() for keyword in [
                'api', 'function', 'class', 'method', 'algorithm', 'database',
                'server', 'client', 'protocol', 'architecture', 'framework'
            ])

            selection_prompt = f"""
You are an expert at selecting the best LLM provider for summarization tasks.

Text Characteristics:
- Length: {text_length} characters
- Technical content: {'Yes' if is_technical else 'No'}
- Summary requirements: {summary_requirements}

Available Providers:
- ollama: Local, cost-effective, good for technical content
- openai: High quality, expensive, good for general content
- anthropic: Excellent reasoning, expensive, good for complex analysis
- bedrock: Secure, good for sensitive content
- grok: Fast, cost-effective, good for general summaries

Based on the text characteristics and requirements, recommend the best provider and explain why.

Return a JSON object with keys: recommended_provider, reasoning, confidence_score, alternative_providers
            """.strip()

            llm_request = {
                "prompt": selection_prompt,
                "provider": "ollama",  # Use local for meta-decisions
                "max_tokens": 600,
                "temperature": 0.2
            }

            response = await self.clients.post_json(f"{self.llm_gateway_url}/query", llm_request)

            if response.get("success"):
                llm_response = response["data"]["response"]
                try:
                    import json
                    provider_recommendation = json.loads(llm_response)
                    return {
                        "provider_recommendation": provider_recommendation,
                        "selection_method": "llm_intelligent",
                        "text_analysis": {
                            "length": text_length,
                            "is_technical": is_technical,
                            "requirements": summary_requirements
                        },
                        "llm_provider": response["data"]["provider"]
                    }
                except json.JSONDecodeError:
                    return {
                        "provider_recommendation": {
                            "recommended_provider": "ollama",
                            "reasoning": "Fallback to local provider due to parsing error",
                            "confidence_score": 0.5
                        },
                        "error": "Failed to parse provider recommendation",
                        "selection_method": "llm_intelligent_fallback"
                    }
            else:
                return {
                    "provider_recommendation": {
                        "recommended_provider": "ollama",
                        "reasoning": "LLM Gateway request failed, using default",
                        "confidence_score": 0.3
                    },
                    "error": response.get("message", "LLM Gateway request failed"),
                    "selection_method": "gateway_error_fallback"
                }

        except Exception as e:
            fire_and_forget(
                "summarizer_provider_selection_error",
                f"Provider selection error: {str(e)}",
                ServiceNames.SUMMARIZER_HUB,
                {
                    "text_length": text_length,
                    "error": str(e)
                }
            )
            return {
                "provider_recommendation": {
                    "recommended_provider": "ollama",
                    "reasoning": f"Error occurred: {str(e)}",
                    "confidence_score": 0.0
                },
                "error": str(e),
                "selection_method": "error_fallback"
            }

    async def quality_assessment_with_llm(self, text: str, summary: str,
                                        quality_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM Gateway to assess summary quality and provide detailed feedback."""
        try:
            assessment_prompt = f"""
You are an expert at evaluating summary quality. Assess the following summary against the original text.

Original Text (length: {len(text)} characters):
{text[:1500]}...  # Truncated for input limits

Summary to Evaluate:
{summary}

Current Quality Metrics:
{quality_metrics}

Provide a comprehensive quality assessment including:
1. Completeness (1-10): How well does the summary capture all important information?
2. Accuracy (1-10): How accurately does the summary represent the original text?
3. Clarity (1-10): How clear and understandable is the summary?
4. Conciseness (1-10): How well does the summary avoid unnecessary information?
5. Overall quality score (1-10)
6. Strengths of the summary
7. Areas for improvement
8. Specific suggestions for enhancement

Return your assessment as a JSON object with keys: completeness, accuracy, clarity, conciseness, overall_score, strengths, improvements, suggestions
            """.strip()

            llm_request = {
                "prompt": assessment_prompt,
                "provider": "ollama",
                "max_tokens": 1000,
                "temperature": 0.2
            }

            response = await self.clients.post_json(f"{self.llm_gateway_url}/query", llm_request)

            if response.get("success"):
                llm_response = response["data"]["response"]
                try:
                    import json
                    quality_assessment = json.loads(llm_response)

                    # Calculate weighted overall score
                    weights = {'completeness': 0.3, 'accuracy': 0.3, 'clarity': 0.2, 'conciseness': 0.2}
                    weighted_score = sum(
                        quality_assessment.get(metric, 5) * weight
                        for metric, weight in weights.items()
                    )

                    quality_assessment['weighted_overall_score'] = round(weighted_score, 1)

                    return {
                        "quality_assessment": quality_assessment,
                        "assessment_method": "llm_enhanced",
                        "original_metrics": quality_metrics,
                        "llm_provider": response["data"]["provider"],
                        "assessment_timestamp": datetime.now().isoformat()
                    }

                except json.JSONDecodeError:
                    return {
                        "quality_assessment": {
                            "completeness": 5,
                            "accuracy": 5,
                            "clarity": 5,
                            "conciseness": 5,
                            "overall_score": 5,
                            "error": "Failed to parse LLM assessment"
                        },
                        "assessment_method": "llm_enhanced_error",
                        "error": "JSON parsing failed"
                    }
            else:
                return {
                    "quality_assessment": {
                        "completeness": quality_metrics.get('completeness', 5),
                        "accuracy": quality_metrics.get('accuracy', 5),
                        "clarity": quality_metrics.get('clarity', 5),
                        "conciseness": quality_metrics.get('conciseness', 5),
                        "overall_score": quality_metrics.get('overall_score', 5),
                        "error": "LLM Gateway assessment failed"
                    },
                    "assessment_method": "original_metrics_fallback",
                    "error": response.get("message", "LLM Gateway request failed")
                }

        except Exception as e:
            fire_and_forget(
                "summarizer_quality_assessment_error",
                f"Quality assessment error: {str(e)}",
                ServiceNames.SUMMARIZER_HUB,
                {
                    "text_length": len(text),
                    "summary_length": len(summary),
                    "error": str(e)
                }
            )
            return {
                "quality_assessment": {
                    "completeness": 5,
                    "accuracy": 5,
                    "clarity": 5,
                    "conciseness": 5,
                    "overall_score": 5,
                    "error": str(e)
                },
                "assessment_method": "error_fallback"
            }

    async def generate_summary_metadata_with_llm(self, text: str, summary: str) -> Dict[str, Any]:
        """Use LLM Gateway to generate rich metadata for summaries."""
        try:
            metadata_prompt = f"""
You are an expert at analyzing documents and summaries. Generate comprehensive metadata for the following summary.

Original Text Preview:
{text[:1000]}...

Generated Summary:
{summary}

Generate metadata including:
1. Main topics/themes
2. Key entities mentioned
3. Document type/category
4. Technical complexity level (1-10)
5. Target audience
6. Key takeaways (3-5 bullet points)
7. Related domains/areas
8. Confidence in summary quality (1-10)

Return the metadata as a JSON object with keys: topics, entities, document_type, technical_complexity, target_audience, key_takeaways, related_domains, confidence_score
            """.strip()

            llm_request = {
                "prompt": metadata_prompt,
                "provider": "ollama",
                "max_tokens": 800,
                "temperature": 0.3
            }

            response = await self.clients.post_json(f"{self.llm_gateway_url}/query", llm_request)

            if response.get("success"):
                llm_response = response["data"]["response"]
                try:
                    import json
                    metadata = json.loads(llm_response)

                    # Add generation metadata
                    metadata['generated_by'] = 'llm_gateway'
                    metadata['llm_provider'] = response["data"]["provider"]
                    metadata['generation_timestamp'] = datetime.now().isoformat()

                    return {
                        "summary_metadata": metadata,
                        "generation_method": "llm_enhanced",
                        "text_length": len(text),
                        "summary_length": len(summary)
                    }

                except json.JSONDecodeError:
                    return {
                        "summary_metadata": {
                            "topics": [],
                            "entities": [],
                            "document_type": "unknown",
                            "technical_complexity": 5,
                            "target_audience": "general",
                            "key_takeaways": [],
                            "related_domains": [],
                            "confidence_score": 5,
                            "error": "Failed to parse LLM metadata"
                        },
                        "generation_method": "llm_enhanced_error",
                        "error": "JSON parsing failed"
                    }
            else:
                return {
                    "summary_metadata": {
                        "topics": [],
                        "entities": [],
                        "document_type": "unknown",
                        "technical_complexity": 5,
                        "target_audience": "general",
                        "key_takeaways": [],
                        "related_domains": [],
                        "confidence_score": 5,
                        "error": "LLM Gateway request failed"
                    },
                    "generation_method": "gateway_error_fallback",
                    "error": response.get("message", "LLM Gateway request failed")
                }

        except Exception as e:
            fire_and_forget(
                "summarizer_metadata_generation_error",
                f"Metadata generation error: {str(e)}",
                ServiceNames.SUMMARIZER_HUB,
                {
                    "text_length": len(text),
                    "summary_length": len(summary),
                    "error": str(e)
                }
            )
            return {
                "summary_metadata": {
                    "topics": [],
                    "entities": [],
                    "document_type": "unknown",
                    "technical_complexity": 5,
                    "target_audience": "general",
                    "key_takeaways": [],
                    "related_domains": [],
                    "confidence_score": 5,
                    "error": str(e)
                },
                "generation_method": "error_fallback"
            }


# Global instance
llm_gateway_integration = LLMGatewayIntegration()
