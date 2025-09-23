"""Unit Tests for Summarization Engine in Summarizer Hub Service.

This module tests summarization engine capabilities including:
- Single document summarization with various formats and styles
- Multi-document summarization and aggregation
- Multi-model summarization and ensemble techniques
- Quality evaluation and scoring
- Content categorization and classification
- Response processing and formatting

Tests cover the complete summarization infrastructure within the Summarizer Hub service.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any, List

from main import SummarizeRequest, SummarizeResponse


class TestSummarizationEngine:
    """Test Summarization Engine functionality."""

    @pytest.fixture
    def summarizer(self):
        """Create summarizer instance with test configuration."""
        from main import Summarizer
        return Summarizer()

    @pytest.fixture
    def multi_model_summarizer(self):
        """Create multi-model summarizer instance with test configuration."""
        from main import MultiModelSummarizer
        return MultiModelSummarizer()

    @pytest.fixture
    def quality_evaluator(self):
        """Create quality evaluator instance with test configuration."""
        from main import QualityEvaluator
        return QualityEvaluator()

    @pytest.fixture
    def categorizer(self):
        """Create categorizer instance with test configuration."""
        from main import Categorizer
        return Categorizer()

    @pytest.fixture
    def enterprise_documents(self):
        """Enterprise documents for comprehensive testing."""
        return {
            "technical_specification": {
                "content": """
# Enterprise API Gateway Technical Specification

## Overview
The Enterprise API Gateway is a robust, scalable solution for managing API traffic in large-scale enterprise environments.

## Architecture
- **Microservices Design**: Containerized services with Kubernetes orchestration
- **Load Balancing**: Intelligent traffic distribution with health checks
- **Security**: JWT authentication, OAuth2 flows, rate limiting
- **Monitoring**: Comprehensive metrics collection and alerting

## Features
- Rate limiting and throttling
- Request/response transformation
- API versioning and documentation
- Integration with service mesh
- Multi-region deployment support

## Performance Requirements
- Handle 10,000+ RPS
- 99.9% uptime SLA
- Sub-100ms response times
- Auto-scaling capabilities

## Security Considerations
- End-to-end encryption
- Comprehensive audit logging
- Compliance with GDPR, HIPAA, PCI-DSS
- Zero-trust architecture principles
                """,
                "metadata": {
                    "type": "technical_documentation",
                    "domain": "infrastructure",
                    "audience": "developers",
                    "complexity": "high"
                },
                "expected_summary_length": 150,
                "expected_categories": ["technical", "infrastructure", "api"]
            },
            "business_requirements": {
                "content": """
# E-Commerce Platform Business Requirements

## Executive Summary
The company requires a modern e-commerce platform to increase online sales by 300% within 24 months.

## Objectives
1. **Revenue Growth**: Achieve $50M in online sales by Q4 2025
2. **Market Expansion**: Support international customers in 25+ countries
3. **Customer Experience**: Provide seamless shopping experience across all devices
4. **Operational Efficiency**: Reduce fulfillment time by 50%

## Functional Requirements
### User Management
- User registration and authentication
- Profile management and preferences
- Loyalty program integration
- Social login capabilities

### Product Catalog
- Product search and filtering
- Category management
- Inventory tracking
- Dynamic pricing support

### Order Processing
- Shopping cart functionality
- Payment processing integration
- Order tracking and notifications
- Return and exchange handling

### Analytics and Reporting
- Sales performance dashboards
- Customer behavior analytics
- Inventory optimization reports
- Marketing campaign tracking

## Non-Functional Requirements
- **Performance**: Page load < 2 seconds
- **Availability**: 99.9% uptime
- **Security**: PCI DSS Level 1 compliance
- **Scalability**: Support 1M+ concurrent users

## Success Metrics
- Conversion rate improvement: 25%
- Average order value increase: 15%
- Customer satisfaction score: > 4.5/5
- Mobile commerce revenue: 40% of total
                """,
                "metadata": {
                    "type": "business_requirements",
                    "domain": "ecommerce",
                    "audience": "stakeholders",
                    "complexity": "medium"
                },
                "expected_summary_length": 200,
                "expected_categories": ["business", "requirements", "ecommerce"]
            },
            "research_paper": {
                "content": """
# Advancements in Large Language Model Architectures

## Abstract
This paper presents recent advancements in transformer-based language models, focusing on efficiency improvements and performance enhancements.

## Introduction
Large Language Models (LLMs) have revolutionized natural language processing. However, their computational requirements and environmental impact have become significant concerns.

## Background
### Transformer Architecture
The transformer architecture, introduced in "Attention is All You Need" (Vaswani et al., 2017), forms the foundation of modern LLMs.

### Scaling Laws
Research by Kaplan et al. (2020) established scaling laws that predict model performance based on parameter count, training data size, and computational resources.

## Methodology
### Model Architecture
We propose a novel efficient transformer variant that reduces computational complexity from O(n²) to O(n log n) through the use of:
- Linear attention mechanisms
- Sparse attention patterns
- Hierarchical processing layers

### Training Approach
- Multi-stage training curriculum
- Knowledge distillation from larger models
- Efficient data sampling techniques

## Results
### Performance Metrics
- **Perplexity**: 12.3 (vs 15.7 for baseline)
- **BLEU Score**: 34.2 (vs 31.8 for baseline)
- **Inference Speed**: 2.3x faster than baseline
- **Memory Usage**: 40% reduction compared to baseline

### Ablation Studies
We conducted comprehensive ablation studies to understand the contribution of each architectural component:
- Linear attention: +15% efficiency, -2% performance
- Sparse patterns: +25% efficiency, -1% performance
- Hierarchical layers: +10% efficiency, +3% performance

## Discussion
The results demonstrate that significant efficiency improvements can be achieved without sacrificing model performance. The proposed architecture enables deployment of high-performance LLMs on resource-constrained environments.

## Future Work
- Extension to multimodal models
- Integration with retrieval-augmented generation
- Exploration of self-supervised learning objectives

## Conclusion
This work advances the field of efficient language model architectures, making powerful AI capabilities more accessible and sustainable.
                """,
                "metadata": {
                    "type": "academic_paper",
                    "domain": "artificial_intelligence",
                    "audience": "researchers",
                    "complexity": "very_high"
                },
                "expected_summary_length": 300,
                "expected_categories": ["research", "artificial_intelligence", "technical"]
            },
            "meeting_notes": {
                "content": """
# Q4 Planning Meeting - Development Team

**Date**: December 15, 2024
**Time**: 2:00 PM - 4:30 PM
**Location**: Conference Room A
**Attendees**: Sarah (PM), Mike (Lead Dev), Alex (Dev), Jamie (QA), Tom (DevOps)

## Agenda Items

### 1. Sprint Retrospective (30 min)
**Discussion Points:**
- Sprint velocity was 85% of planned capacity
- Major blockers: Database performance issues
- Successes: Completed user authentication module ahead of schedule

**Action Items:**
- [ ] Investigate database query optimization
- [ ] Update sprint planning template
- [ ] Schedule team-building activity

### 2. Q4 Objectives Review (45 min)
**Current Status:**
- User registration feature: 95% complete
- Payment integration: 70% complete
- Mobile app launch: 40% complete

**Risks Identified:**
- Third-party payment provider API changes
- Resource constraints for mobile development
- Increased security requirements from compliance team

**Mitigation Strategies:**
- Schedule weekly check-ins with payment provider
- Hire additional mobile developer
- Conduct security audit in January

### 3. Technical Debt Discussion (30 min)
**Issues Raised:**
- Legacy authentication system needs modernization
- Test coverage below 80% target
- Documentation outdated for several services

**Proposed Solutions:**
- Migrate to OAuth2 within next 2 sprints
- Implement automated testing pipeline
- Weekly documentation updates

### 4. Resource Planning (45 min)
**Team Capacity:**
- Frontend: 3 developers (2 available for new projects)
- Backend: 4 developers (1 on leave in January)
- QA: 2 engineers (planning to hire 1 more)
- DevOps: 2 engineers (fully allocated)

**Q4 Project Load:**
- E-commerce platform (high priority)
- Mobile app development (medium priority)
- Infrastructure modernization (ongoing)
- Security enhancements (compliance driven)

### 5. Open Floor (30 min)
**Additional Topics:**
- New hire onboarding process
- Remote work policy updates
- Team lunch planning

## Next Meeting
- Date: January 5, 2025 (2:00 PM)
- Focus: Sprint planning for January

## Action Items Summary
1. **Sarah**: Update project timeline with new resource allocations
2. **Mike**: Prepare technical debt remediation plan
3. **Alex**: Research OAuth2 migration options
4. **Jamie**: Create test coverage improvement plan
5. **Tom**: Schedule infrastructure architecture review
                """,
                "metadata": {
                    "type": "meeting_notes",
                    "domain": "project_management",
                    "audience": "team",
                    "complexity": "medium"
                },
                "expected_summary_length": 250,
                "expected_categories": ["meeting", "planning", "development"]
            }
        }

    @pytest.fixture
    def summarization_styles(self):
        """Different summarization styles for testing."""
        return {
            "executive": {
                "focus": "high-level overview, key decisions, strategic implications",
                "tone": "professional, concise",
                "audience": "executives, stakeholders",
                "length_preference": "brief"
            },
            "technical": {
                "focus": "technical details, implementation specifics, architectural decisions",
                "tone": "precise, detailed",
                "audience": "developers, architects",
                "length_preference": "comprehensive"
            },
            "operational": {
                "focus": "processes, procedures, timelines, responsibilities",
                "tone": "practical, actionable",
                "audience": "team members, operators",
                "length_preference": "balanced"
            },
            "analytical": {
                "focus": "data analysis, metrics, trends, insights",
                "tone": "objective, evidence-based",
                "audience": "analysts, decision-makers",
                "length_preference": "detailed"
            }
        }

    def test_single_document_summarization(self, summarizer, enterprise_documents):
        """Test single document summarization capabilities."""
        # Test technical specification summarization
        tech_doc = enterprise_documents["technical_specification"]

        with patch("main.summarizer._call_llm_api") as mock_llm:
            mock_llm.return_value = "The Enterprise API Gateway is a scalable microservices solution featuring load balancing, security controls, and monitoring capabilities. Key requirements include handling 10,000+ RPS, 99.9% uptime, and compliance with major security standards."

            result = summarizer.summarize_document(
                content=tech_doc["content"],
                style="technical",
                max_length=tech_doc["expected_summary_length"],
                format="markdown"
            )

            assert result["success"] is True
            assert "summary" in result
            assert len(result["summary"]) > 50
            assert len(result["summary"]) <= tech_doc["expected_summary_length"]
            assert result["metadata"]["style"] == "technical"
            assert result["metadata"]["format"] == "markdown"

        # Test business requirements summarization
        biz_doc = enterprise_documents["business_requirements"]

        with patch("main.summarizer._call_llm_api") as mock_llm:
            mock_llm.return_value = "The company aims to grow online sales by 300% to $50M within 24 months through a modern e-commerce platform. Key requirements include international expansion, seamless customer experience, and operational efficiency improvements targeting 25% conversion rate increase and 50% faster fulfillment."

            result = summarizer.summarize_document(
                content=biz_doc["content"],
                style="executive",
                max_length=biz_doc["expected_summary_length"],
                format="text"
            )

            assert result["success"] is True
            assert result["metadata"]["style"] == "executive"
            assert "sales" in result["summary"].lower()
            assert "300%" in result["summary"]

    def test_multi_document_summarization(self, summarizer, enterprise_documents):
        """Test multi-document summarization and aggregation."""
        # Select multiple related documents
        docs_to_summarize = [
            enterprise_documents["technical_specification"],
            enterprise_documents["business_requirements"]
        ]

        with patch("main.summarizer._call_llm_api") as mock_llm:
            mock_llm.return_value = "The enterprise is implementing a comprehensive e-commerce platform combining technical excellence with business objectives. The API Gateway provides robust infrastructure supporting microservices architecture, while business requirements focus on 300% revenue growth through international expansion and enhanced customer experience. Key technical requirements include high availability, security compliance, and scalable performance."

            result = summarizer.summarize_multiple_documents(
                documents=[doc["content"] for doc in docs_to_summarize],
                aggregation_strategy="comprehensive",
                max_length=400,
                preserve_key_points=True
            )

            assert result["success"] is True
            assert result["document_count"] == 2
            assert "api gateway" in result["summary"].lower()
            assert "e-commerce" in result["summary"].lower()
            assert result["metadata"]["aggregation_strategy"] == "comprehensive"
            assert result["metadata"]["preserve_key_points"] is True

        # Test comparative summarization
        with patch("main.summarizer._call_llm_api") as mock_llm:
            mock_llm.return_value = "Comparison of technical specification and business requirements reveals alignment between infrastructure capabilities and business objectives. Technical implementation supports business goals through scalable architecture, security compliance, and performance optimization."

            result = summarizer.summarize_multiple_documents(
                documents=[doc["content"] for doc in docs_to_summarize],
                aggregation_strategy="comparative",
                focus_areas=["alignment", "gaps", "dependencies"],
                max_length=300
            )

            assert result["success"] is True
            assert "comparison" in result["summary"].lower() or "alignment" in result["summary"].lower()
            assert result["metadata"]["aggregation_strategy"] == "comparative"

    def test_multi_model_summarization(self, multi_model_summarizer, enterprise_documents):
        """Test multi-model summarization and ensemble techniques."""
        research_doc = enterprise_documents["research_paper"]

        # Configure multiple models
        model_configs = [
            {"provider": "openai", "model": "gpt-4", "weight": 0.4},
            {"provider": "anthropic", "model": "claude-3", "weight": 0.4},
            {"provider": "google", "model": "gemini-pro", "weight": 0.2}
        ]

        with patch("main.multi_model_summarizer._call_model_api") as mock_model_call:
            # Mock different model responses
            mock_model_call.side_effect = [
                "Research paper presents efficient transformer architectures reducing complexity from O(n²) to O(n log n) through linear attention, sparse patterns, and hierarchical layers. Results show 2.3x speed improvement and 40% memory reduction with minimal performance loss.",
                "The paper introduces advancements in LLM architectures focusing on computational efficiency. Key innovations include linear attention mechanisms, sparse attention patterns, and hierarchical processing. Performance improvements include 15-25% efficiency gains with maintained accuracy.",
                "Novel transformer variants achieve efficiency improvements through attention optimization and hierarchical processing. Ablation studies demonstrate individual component contributions to overall performance gains."
            ]

            result = multi_model_summarizer.ensemble_summarize(
                content=research_doc["content"],
                models=model_configs,
                ensemble_method="weighted_voting",
                quality_threshold=0.8
            )

            assert result["success"] is True
            assert result["model_count"] == 3
            assert "transformer" in result["summary"].lower()
            assert "efficiency" in result["summary"].lower()
            assert result["metadata"]["ensemble_method"] == "weighted_voting"
            assert result["quality_score"] >= 0.8

        # Test model selection based on content type
        content_type = research_doc["metadata"]["type"]

        selected_models = multi_model_summarizer.select_models_for_content(
            content_type=content_type,
            complexity=research_doc["metadata"]["complexity"],
            domain=research_doc["metadata"]["domain"]
        )

        assert len(selected_models) >= 2
        assert all(model["provider"] in ["openai", "anthropic", "google"] for model in selected_models)

    def test_quality_evaluation_and_scoring(self, quality_evaluator, enterprise_documents):
        """Test quality evaluation and scoring capabilities."""
        tech_doc = enterprise_documents["technical_specification"]

        # Generate a test summary
        test_summary = "The Enterprise API Gateway provides robust API management with microservices architecture, load balancing, security features, and monitoring capabilities. It supports high-performance requirements and enterprise security standards."

        # Evaluate summary quality
        quality_result = quality_evaluator.evaluate_summary_quality(
            original_content=tech_doc["content"],
            summary=test_summary,
            criteria=["completeness", "conciseness", "accuracy", "readability"]
        )

        assert "overall_score" in quality_result
        assert quality_result["overall_score"] >= 0.0 and quality_result["overall_score"] <= 1.0
        assert "criteria_scores" in quality_result
        assert len(quality_result["criteria_scores"]) == 4
        assert all(score >= 0.0 and score <= 1.0 for score in quality_result["criteria_scores"].values())

        # Test summary improvement suggestions
        if quality_result["overall_score"] < 0.9:
            improvement_result = quality_evaluator.suggest_improvements(
                summary=test_summary,
                quality_scores=quality_result["criteria_scores"],
                original_content=tech_doc["content"]
            )

            assert "suggestions" in improvement_result
            assert len(improvement_result["suggestions"]) > 0
            assert all("priority" in suggestion for suggestion in improvement_result["suggestions"])

    def test_content_categorization(self, categorizer, enterprise_documents):
        """Test content categorization and classification."""
        # Test document categorization
        for doc_name, doc_data in enterprise_documents.items():
            categories = categorizer.categorize_document(
                content=doc_data["content"],
                metadata=doc_data["metadata"]
            )

            assert "primary_category" in categories
            assert "secondary_categories" in categories
            assert "confidence_scores" in categories
            assert len(categories["secondary_categories"]) >= 0

            # Verify expected categories are detected
            all_categories = [categories["primary_category"]] + categories["secondary_categories"]
            expected_categories = doc_data["expected_categories"]

            category_match = any(expected_cat in cat.lower() for expected_cat in expected_categories
                               for cat in all_categories)

            assert category_match, f"Expected categories {expected_categories} not found in {all_categories}"

        # Test category-based summarization strategy selection
        tech_categories = categorizer.categorize_document(
            content=enterprise_documents["technical_specification"]["content"]
        )

        strategy = categorizer.select_summarization_strategy(tech_categories)

        assert "style" in strategy
        assert "focus_areas" in strategy
        assert "length_preference" in strategy
        assert strategy["style"] in ["technical", "executive", "operational", "analytical"]

    def test_response_processing_and_formatting(self, summarizer):
        """Test response processing and formatting capabilities."""
        # Test different output formats
        test_summary = "This is a comprehensive summary of the document content covering key points and main ideas."

        formats_to_test = ["markdown", "html", "json", "text", "pdf"]

        for output_format in formats_to_test:
            formatted_result = summarizer.format_summary_output(
                summary=test_summary,
                format=output_format,
                metadata={"word_count": 25, "compression_ratio": 0.3}
            )

            assert formatted_result["success"] is True
            assert "formatted_content" in formatted_result
            assert formatted_result["metadata"]["format"] == output_format

            if output_format == "markdown":
                assert formatted_result["formatted_content"] == test_summary  # Markdown is usually plain
            elif output_format == "html":
                assert "<p>" in formatted_result["formatted_content"] or "<div>" in formatted_result["formatted_content"]
            elif output_format == "json":
                parsed = json.loads(formatted_result["formatted_content"])
                assert "summary" in parsed
                assert "metadata" in parsed

        # Test summary enhancement
        enhanced_result = summarizer.enhance_summary(
            summary=test_summary,
            enhancements=["add_structure", "highlight_key_points", "add_metadata"]
        )

        assert enhanced_result["success"] is True
        assert "enhanced_summary" in enhanced_result
        assert len(enhanced_result["enhanced_summary"]) >= len(test_summary)
        assert "structure" in enhanced_result["enhancement_metadata"]

    def test_summarization_performance_optimization(self, summarizer, enterprise_documents):
        """Test summarization performance optimization."""
        import time

        large_doc = enterprise_documents["research_paper"]["content"] * 3  # Make it larger

        # Test caching performance
        start_time = time.time()

        with patch("main.summarizer._call_llm_api") as mock_llm:
            mock_llm.return_value = "Large research paper summary covering transformer architectures, efficiency improvements, and performance results."

            # First call - should cache
            result1 = summarizer.summarize_document(
                content=large_doc,
                style="technical",
                use_cache=True
            )

            first_call_time = time.time() - start_time

            # Second call - should use cache
            start_time = time.time()
            result2 = summarizer.summarize_document(
                content=large_doc,
                style="technical",
                use_cache=True
            )

            second_call_time = time.time() - start_time

            # Cached call should be significantly faster
            assert second_call_time < first_call_time * 0.5
            assert result1["summary"] == result2["summary"]

        # Test batch processing performance
        batch_docs = [doc["content"] for doc in list(enterprise_documents.values())[:3]]

        batch_start_time = time.time()

        with patch("main.summarizer._call_llm_api") as mock_llm:
            mock_llm.return_value = "Batch processed document summary."

            batch_results = summarizer.batch_summarize(
                documents=batch_docs,
                style="executive",
                parallel_processing=True,
                max_workers=3
            )

            batch_time = time.time() - batch_start_time

            assert len(batch_results) == 3
            assert all(r["success"] for r in batch_results)
            assert batch_time < 10.0  # Should complete within 10 seconds

    def test_adaptive_summarization(self, summarizer, enterprise_documents):
        """Test adaptive summarization based on content analysis."""
        # Test adaptive style selection
        for doc_name, doc_data in enterprise_documents.items():
            adaptive_config = summarizer.analyze_content_for_summarization(
                content=doc_data["content"],
                metadata=doc_data["metadata"]
            )

            assert "recommended_style" in adaptive_config
            assert "estimated_length" in adaptive_config
            assert "content_complexity" in adaptive_config
            assert "key_sections" in adaptive_config

            # Verify style recommendation makes sense for content type
            if doc_data["metadata"]["type"] == "technical_documentation":
                assert adaptive_config["recommended_style"] in ["technical", "analytical"]
            elif doc_data["metadata"]["type"] == "business_requirements":
                assert adaptive_config["recommended_style"] in ["executive", "operational"]

        # Test dynamic length adjustment
        short_content = "This is a brief document."
        long_content = enterprise_documents["research_paper"]["content"]

        short_adaptive = summarizer.analyze_content_for_summarization(short_content)
        long_adaptive = summarizer.analyze_content_for_summarization(long_content)

        assert short_adaptive["estimated_length"] < long_adaptive["estimated_length"]

    def test_enterprise_integration_patterns(self, summarizer, multi_model_summarizer):
        """Test enterprise integration patterns and workflows."""
        # Test summarization pipeline integration
        enterprise_content = """
COMPANY CONFIDENTIAL - Q4 Business Review

Executive Summary:
Q4 2024 showed strong performance across all business units with 28% revenue growth and 35% profit increase.

Key Achievements:
- Digital transformation completed ahead of schedule
- Customer satisfaction scores reached 4.8/5
- New product launches exceeded expectations
- International expansion successful in 5 new markets

Financial Highlights:
- Revenue: $125M (up 28% from Q4 2023)
- Net Profit: $18.5M (up 35% from Q4 2023)
- Operating Margin: 14.8% (up 2.1% from Q4 2023)
- Free Cash Flow: $22M (up 45% from Q4 2023)

Operational Metrics:
- Customer Acquisition: 25,000 new customers
- Employee Satisfaction: 4.6/5
- System Uptime: 99.9%
- Average Response Time: 1.2 seconds

Challenges Faced:
- Supply chain disruptions in Q4
- Cybersecurity incident requiring incident response
- Market competition increased in key segments

Strategic Initiatives:
- AI/ML implementation across product lines
- Sustainability program expansion
- Remote work policy optimization
- Diversity and inclusion program enhancement

Outlook for 2025:
- Expected revenue growth: 25-30%
- New market entries: 8 countries
- Technology investments: $45M
- Headcount growth: 15%

Risk Factors:
- Economic uncertainty in global markets
- Supply chain volatility
- Regulatory changes in key markets
- Cybersecurity threats evolution
        """

        # Test complete enterprise summarization workflow
        workflow_result = summarizer.execute_enterprise_summarization_workflow(
            content=enterprise_content,
            workflow_type="business_review",
            stakeholder_audience="executive",
            output_formats=["executive_summary", "detailed_analysis", "key_metrics"],
            quality_checks=True
        )

        assert workflow_result["success"] is True
        assert "executive_summary" in workflow_result["outputs"]
        assert "detailed_analysis" in workflow_result["outputs"]
        assert "key_metrics" in workflow_result["outputs"]
        assert workflow_result["quality_score"] >= 0.8

        # Verify executive summary content
        exec_summary = workflow_result["outputs"]["executive_summary"]
        assert any(term in exec_summary.lower() for term in ["revenue", "growth", "profit", "performance"])

        # Test multi-model ensemble for enterprise content
        ensemble_result = multi_model_summarizer.enterprise_ensemble_summarization(
            content=enterprise_content,
            business_context="q4_business_review",
            quality_requirements={"min_score": 0.85, "max_length": 500},
            compliance_checks=["confidentiality", "accuracy"]
        )

        assert ensemble_result["success"] is True
        assert ensemble_result["quality_score"] >= 0.85
        assert len(ensemble_result["summary"]) <= 500
        assert ensemble_result["compliance_check_passed"] is True
