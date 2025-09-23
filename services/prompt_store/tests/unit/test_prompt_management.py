"""Unit Tests for Prompt Management in Prompt Store Service.

This module tests prompt lifecycle management including:
- Prompt creation and validation
- Content processing and metadata extraction
- Prompt categorization and tagging
- Access control and permissions
- Prompt relationships and dependencies
- Quality assessment and optimization

Tests cover the core prompt management capabilities within the DDD architecture.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from core.entities import Prompt, PromptTag, PromptRelationship
from core.models import PromptContent, PromptMetadata
from domain.prompts.handlers import PromptCommandHandler
from domain.prompts.repository import PromptRepository
from domain.prompts.service import PromptService


class TestPromptCreation:
    """Test Prompt Creation functionality."""

    @pytest.fixture
    def prompt_handler(self, mock_repository, mock_event_bus):
        """Create prompt command handler instance."""
        return PromptCommandHandler(mock_repository, mock_event_bus)

    def test_basic_prompt_creation(self, prompt_handler, sample_prompt):
        """Test basic prompt creation with minimal required fields."""
        create_command = {
            "name": "Test Analysis Prompt",
            "content": "Analyze this document: {document_content}",
            "category": "analysis",
            "author": "test@example.com"
        }

        result = prompt_handler.handle_create_prompt(create_command)

        assert result["success"] is True
        assert "prompt_id" in result
        assert result["prompt_id"] is not None

    def test_prompt_creation_with_full_metadata(self, prompt_handler):
        """Test prompt creation with comprehensive metadata."""
        create_command = {
            "name": "Advanced Document Analysis Prompt",
            "description": "A sophisticated prompt for analyzing technical documents",
            "content": """You are an expert document analyst. Analyze the following document comprehensively:

Document: {document_content}

Provide:
1. Executive Summary (2-3 sentences)
2. Key Technical Concepts
3. Complexity Assessment
4. Practical Applications
5. Improvement Recommendations

Format your response with clear headings.""",
            "category": "analysis",
            "tags": ["technical", "analysis", "comprehensive", "expert"],
            "custom_metadata": {
                "complexity_level": "advanced",
                "target_audience": "technical_experts",
                "estimated_tokens": 150,
                "model_compatibility": ["gpt-4", "claude-2"]
            },
            "access_control": {
                "owner": "john.doe@company.com",
                "readers": ["team@company.com"],
                "writers": ["john.doe@company.com"]
            },
            "author": "john.doe@company.com"
        }

        result = prompt_handler.handle_create_prompt(create_command)

        assert result["success"] is True
        assert result["prompt"]["name"] == create_command["name"]
        assert result["prompt"]["category"] == create_command["category"]
        assert set(result["prompt"]["tags"]) == set(create_command["tags"])
        assert result["prompt"]["metadata"]["author"] == create_command["author"]

    def test_prompt_creation_validation(self, prompt_handler):
        """Test prompt creation input validation."""
        invalid_commands = [
            # Missing name
            {"content": "Content without name", "category": "analysis", "author": "user@example.com"},
            # Missing content
            {"name": "Name without content", "category": "analysis", "author": "user@example.com"},
            # Invalid category
            {"name": "Test", "content": "Content", "category": "invalid_category", "author": "user@example.com"},
            # Empty name
            {"name": "", "content": "Content", "category": "analysis", "author": "user@example.com"},
            # Content too long (simulate)
            {"name": "Test", "content": "A" * 100000, "category": "analysis", "author": "user@example.com"}
        ]

        for invalid_command in invalid_commands:
            result = prompt_handler.handle_create_prompt(invalid_command)
            assert result["success"] is False
            assert "validation_errors" in result

    def test_prompt_creation_with_variables(self, prompt_handler):
        """Test prompt creation with variable extraction and validation."""
        prompt_with_variables = {
            "name": "Variable Test Prompt",
            "content": "Hello {user_name}! Analyze this {document_type}: {document_content}. Use {analysis_depth} analysis.",
            "category": "analysis",
            "author": "test@example.com"
        }

        result = prompt_handler.handle_create_prompt(prompt_with_variables)

        assert result["success"] is True
        extracted_vars = result["prompt"]["extracted_variables"]
        assert "user_name" in extracted_vars
        assert "document_type" in extracted_vars
        assert "document_content" in extracted_vars
        assert "analysis_depth" in extracted_vars

    def test_prompt_creation_idempotency(self, prompt_handler):
        """Test idempotent prompt creation (preventing duplicates)."""
        create_command = {
            "name": "Unique Test Prompt",
            "content": "Unique content for testing",
            "category": "analysis",
            "author": "test@example.com",
            "idempotency_key": "unique_prompt_key_123"
        }

        # First creation
        result1 = prompt_handler.handle_create_prompt(create_command)
        assert result1["success"] is True
        prompt_id = result1["prompt_id"]

        # Second creation with same idempotency key
        result2 = prompt_handler.handle_create_prompt(create_command)
        assert result2["success"] is True
        assert result2["prompt_id"] == prompt_id  # Same prompt returned

        # Verify only one prompt was actually created
        assert prompt_handler.repository.save_prompt.call_count == 1


class TestPromptContentProcessing:
    """Test Prompt Content Processing functionality."""

    @pytest.fixture
    def content_processor(self, mock_ai_service, mock_validation_service):
        """Create content processor instance."""
        return PromptService(ai_service=mock_ai_service, validation_service=mock_validation_service)

    def test_prompt_content_analysis(self, content_processor, sample_prompt_content):
        """Test comprehensive prompt content analysis."""
        analysis_result = content_processor.analyze_prompt_content(sample_prompt_content)

        assert analysis_result["success"] is True
        assert "content_analysis" in analysis_result
        assert "quality_metrics" in analysis_result
        assert "optimization_suggestions" in analysis_result

        # Verify analysis components
        content_analysis = analysis_result["content_analysis"]
        assert "token_count" in content_analysis
        assert "variable_extraction" in content_analysis
        assert "instruction_clarity" in content_analysis

        # Verify quality metrics
        quality = analysis_result["quality_metrics"]
        assert "clarity_score" in quality
        assert "completeness_score" in quality
        assert "effectiveness_score" in quality

    def test_variable_extraction_and_validation(self, content_processor):
        """Test variable extraction and validation in prompts."""
        test_prompts = [
            {
                "content": "Hello {user_name}, analyze this {document_type}: {content}",
                "expected_vars": ["user_name", "document_type", "content"],
                "should_pass": True
            },
            {
                "content": "Process {unclosed_var , continue with {another_var}",
                "expected_vars": ["unclosed_var", "another_var"],
                "should_pass": False  # Invalid syntax
            },
            {
                "content": "Simple prompt without variables",
                "expected_vars": [],
                "should_pass": True
            }
        ]

        for test_case in test_prompts:
            content = PromptContent(
                prompt_id=str(uuid.uuid4()),
                content=test_case["content"]
            )

            result = content_processor.extract_and_validate_variables(content)

            assert result["extraction_success"] is True
            extracted_vars = result["extracted_variables"]

            if test_case["should_pass"]:
                assert set(extracted_vars) == set(test_case["expected_vars"])
                assert result["validation_passed"] is True
            else:
                assert result["validation_passed"] is False
                assert "syntax_errors" in result

    def test_prompt_quality_assessment(self, content_processor):
        """Test prompt quality assessment and scoring."""
        quality_test_cases = [
            {
                "content": "Analyze this.",
                "expected_quality": "low",
                "issues": ["insufficient_detail", "unclear_instructions", "no_variables"]
            },
            {
                "content": "Please analyze the following document and provide insights: {document_content}",
                "expected_quality": "medium",
                "issues": ["could_be_more_specific"]
            },
            {
                "content": """You are an expert analyst. Analyze the provided document comprehensively.

Document: {document_content}
Analysis Type: {analysis_depth}

Provide:
1. Executive summary
2. Key findings
3. Detailed analysis
4. Recommendations

Be thorough but concise.""",
                "expected_quality": "high",
                "issues": []  # No significant issues
            }
        ]

        for test_case in quality_test_cases:
            content = PromptContent(
                prompt_id=str(uuid.uuid4()),
                content=test_case["content"]
            )

            quality_result = content_processor.assess_prompt_quality(content)

            assert quality_result["overall_quality"] == test_case["expected_quality"]
            assessed_issues = quality_result["quality_issues"]

            for expected_issue in test_case["issues"]:
                assert any(expected_issue in issue.lower() for issue in assessed_issues)

    def test_prompt_optimization_suggestions(self, content_processor):
        """Test AI-powered prompt optimization suggestions."""
        optimization_test_cases = [
            {
                "content": "Analyze this document.",
                "expected_suggestions": ["add_variables", "be_more_specific", "add_structure"]
            },
            {
                "content": "You are a helpful assistant. Answer this question: {question}",
                "expected_suggestions": ["add_role_definition", "specify_response_format"]
            }
        ]

        for test_case in test_cases:
            content = PromptContent(
                prompt_id=str(uuid.uuid4()),
                content=test_case["content"]
            )

            optimization_result = content_processor.generate_optimization_suggestions(content)

            assert optimization_result["success"] is True
            suggestions = optimization_result["optimization_suggestions"]

            for expected_suggestion in test_case["expected_suggestions"]:
                assert any(expected_suggestion in suggestion.lower() for suggestion in suggestions)

    def test_prompt_syntax_validation(self, content_processor):
        """Test prompt syntax validation."""
        valid_invalid_prompts = [
            ("Valid prompt with {variable}", True, []),
            ("Prompt with {unclosed_variable", False, ["unclosed_variable"]),
            ("Prompt with {valid_var} and {another_valid}", True, []),
            ("Prompt with {{double_braces}}", False, ["invalid_brace_syntax"]),
            ("Prompt with {var1} {var1} duplicate", True, []),  # Duplicates allowed
        ]

        for content_text, should_be_valid, expected_errors in valid_invalid_prompts:
            content = PromptContent(
                prompt_id=str(uuid.uuid4()),
                content=content_text
            )

            validation_result = content_processor.validate_prompt_syntax(content)

            assert validation_result["syntax_valid"] == should_be_valid

            if not should_be_valid:
                assert len(validation_result["syntax_errors"]) > 0
                for expected_error in expected_errors:
                    assert any(expected_error in error.lower() for error in validation_result["syntax_errors"])


class TestPromptCategorizationAndTagging:
    """Test Prompt Categorization and Tagging functionality."""

    @pytest.fixture
    def categorization_service(self, mock_repository, mock_ai_service):
        """Create categorization service instance."""
        return PromptService(repository=mock_repository, ai_service=mock_ai_service)

    def test_automatic_prompt_categorization(self, categorization_service):
        """Test automatic prompt categorization based on content."""
        categorization_test_cases = [
            {
                "content": "Summarize the key points from this article: {article_text}",
                "expected_category": "summarization",
                "confidence_threshold": 0.8
            },
            {
                "content": "Analyze this code for bugs and improvements: {code_content}",
                "expected_category": "code_analysis",
                "confidence_threshold": 0.85
            },
            {
                "content": "Translate this text to French: {text_content}",
                "expected_category": "translation",
                "confidence_threshold": 0.9
            },
            {
                "content": "Write a creative story about {topic} in {genre} style",
                "expected_category": "creative_writing",
                "confidence_threshold": 0.75
            }
        ]

        for test_case in categorization_test_cases:
            content = PromptContent(
                prompt_id=str(uuid.uuid4()),
                content=test_case["content"]
            )

            categorization_result = categorization_service.categorize_prompt_automatically(content)

            assert categorization_result["success"] is True
            assert categorization_result["category"] == test_case["expected_category"]
            assert categorization_result["confidence"] >= test_case["confidence_threshold"]

    def test_smart_tagging_system(self, categorization_service):
        """Test intelligent tagging based on content analysis."""
        content = PromptContent(
            prompt_id=str(uuid.uuid4()),
            content="""You are a technical documentation expert. Analyze this software documentation and provide:

1. Code examples quality assessment
2. API documentation completeness
3. Technical accuracy evaluation
4. User experience improvements

Documentation: {documentation_content}

Focus on clarity, completeness, and technical precision."""
        )

        tagging_result = categorization_service.generate_smart_tags(content)

        assert tagging_result["success"] is True
        generated_tags = tagging_result["generated_tags"]

        # Should include relevant technical tags
        tag_names = [tag["name"] for tag in generated_tags]
        expected_tags = ["technical", "documentation", "analysis", "code", "api", "quality"]

        matches = sum(1 for expected in expected_tags if any(expected in tag.lower() for tag in tag_names))
        assert matches >= len(expected_tags) * 0.7  # At least 70% match

        # Should have confidence scores
        for tag in generated_tags:
            assert "confidence" in tag
            assert 0 <= tag["confidence"] <= 1

    def test_tag_relationship_management(self, categorization_service, sample_prompt_tag):
        """Test tag relationship and hierarchy management."""
        # Create a tag hierarchy
        parent_tag = sample_prompt_tag

        child_tags = [
            PromptTag(
                id=str(uuid.uuid4()),
                name="code-review",
                display_name="Code Review",
                category="code_analysis",
                parent_tag_id=parent_tag.id,
                created_at=datetime.now()
            ),
            PromptTag(
                id=str(uuid.uuid4()),
                name="api-documentation",
                display_name="API Documentation",
                category="documentation",
                parent_tag_id=parent_tag.id,
                created_at=datetime.now()
            )
        ]

        hierarchy_result = categorization_service.build_tag_hierarchy(parent_tag, child_tags)

        assert hierarchy_result["success"] is True
        hierarchy = hierarchy_result["tag_hierarchy"]

        assert hierarchy["root_tag"]["id"] == parent_tag.id
        assert len(hierarchy["child_tags"]) == 2

        # Verify parent-child relationships
        for child in hierarchy["child_tags"]:
            assert child["parent_tag_id"] == parent_tag.id

    def test_tag_usage_analytics(self, categorization_service):
        """Test tag usage analytics and recommendations."""
        # Simulate tag usage data
        usage_data = {
            "document-analysis": {"usage_count": 150, "trend": "increasing", "popularity_rank": 1},
            "code-review": {"usage_count": 89, "trend": "stable", "popularity_rank": 3},
            "summarization": {"usage_count": 234, "trend": "increasing", "popularity_rank": 2},
            "translation": {"usage_count": 45, "trend": "decreasing", "popularity_rank": 5}
        }

        analytics_result = categorization_service.analyze_tag_usage(usage_data)

        assert analytics_result["success"] is True

        # Should identify popular tags
        popular_tags = analytics_result["popular_tags"]
        assert "document-analysis" in popular_tags
        assert "summarization" in popular_tags

        # Should identify trending tags
        trending_tags = analytics_result["trending_tags"]
        assert "document-analysis" in trending_tags
        assert "summarization" in trending_tags

        # Should provide usage recommendations
        recommendations = analytics_result["usage_recommendations"]
        assert len(recommendations) > 0

    def test_tag_conflict_resolution(self, categorization_service):
        """Test tag conflict resolution for similar or duplicate tags."""
        conflicting_tags = [
            {"name": "document_analysis", "usage": 100},
            {"name": "doc_analysis", "usage": 50},  # Similar
            {"name": "document_analyzer", "usage": 25},  # Similar
            {"name": "code_analysis", "usage": 75},  # Different category
        ]

        resolution_result = categorization_service.resolve_tag_conflicts(conflicting_tags)

        assert resolution_result["success"] is True
        assert "conflict_resolution" in resolution_result

        resolution = resolution_result["conflict_resolution"]

        # Should identify conflicts
        assert len(resolution["identified_conflicts"]) > 0

        # Should suggest merges for similar tags
        assert "suggested_merges" in resolution
        merge_suggestions = resolution["suggested_merges"]

        # Should suggest merging similar document analysis tags
        document_analysis_merges = [merge for merge in merge_suggestions
                                  if "document" in str(merge["tags_to_merge"]).lower()]
        assert len(document_analysis_merges) > 0

        # Should not suggest merging different categories
        cross_category_merges = [merge for merge in merge_suggestions
                               if len(set(str(merge["tags_to_merge"]).split())) > 1 and
                               "code" in str(merge["tags_to_merge"]).lower() and
                               "document" in str(merge["tags_to_merge"]).lower()]
        assert len(cross_category_merges) == 0


class TestPromptRelationships:
    """Test Prompt Relationship Management functionality."""

    @pytest.fixture
    def relationship_manager(self, mock_repository, mock_ai_service):
        """Create relationship manager instance."""
        return PromptService(repository=mock_repository, ai_service=mock_ai_service)

    def test_relationship_discovery(self, relationship_manager):
        """Test automatic relationship discovery between prompts."""
        prompts = [
            {
                "id": str(uuid.uuid4()),
                "content": "Analyze this document: {document_content}. Provide key insights."
            },
            {
                "id": str(uuid.uuid4()),
                "content": "Summarize the analysis: {analysis_content}. Create an executive summary."
            },
            {
                "id": str(uuid.uuid4()),
                "content": "Translate this text to Spanish: {text_content}"
            }
        ]

        discovery_result = relationship_manager.discover_prompt_relationships(prompts)

        assert discovery_result["success"] is True
        discovered_relationships = discovery_result["discovered_relationships"]

        # Should find relationships between analysis and summary prompts
        analysis_relationships = [rel for rel in discovered_relationships
                                if rel["relationship_type"] in ["extends", "complements", "chains_with"]]

        assert len(analysis_relationships) > 0

        # Should not find relationships with unrelated translation prompt
        translation_relationships = [rel for rel in discovered_relationships
                                   if "translate" in str(rel).lower() and rel["strength"] > 0.5]

        assert len(translation_relationships) == 0

    def test_relationship_strength_calculation(self, relationship_manager):
        """Test relationship strength calculation between prompts."""
        prompt_pairs = [
            {
                "prompt1": "Analyze this document: {document}",
                "prompt2": "Summarize the analysis: {analysis}",
                "expected_strength": 0.8,  # High - complementary workflow
                "relationship_type": "complements"
            },
            {
                "prompt1": "Write a summary of: {text}",
                "prompt2": "Translate to French: {text}",
                "expected_strength": 0.6,  # Medium - shared variables but different purposes
                "relationship_type": "shares_variables"
            },
            {
                "prompt1": "Analyze code quality: {code}",
                "prompt2": "Write documentation: {topic}",
                "expected_strength": 0.2,  # Low - minimal overlap
                "relationship_type": "unrelated"
            }
        ]

        for pair in prompt_pairs:
            strength_result = relationship_manager.calculate_relationship_strength(
                pair["prompt1"], pair["prompt2"]
            )

            assert strength_result["success"] is True
            assert abs(strength_result["strength"] - pair["expected_strength"]) < 0.2
            assert strength_result["relationship_type"] == pair["relationship_type"]

    def test_relationship_network_analysis(self, relationship_manager):
        """Test analysis of prompt relationship networks."""
        # Create a network of related prompts
        prompts_network = {
            "analysis_prompt": {
                "content": "Analyze document: {document}",
                "relationships": ["summary_prompt", "insights_prompt"]
            },
            "summary_prompt": {
                "content": "Summarize analysis: {analysis}",
                "relationships": ["analysis_prompt", "translation_prompt"]
            },
            "insights_prompt": {
                "content": "Extract insights: {document}",
                "relationships": ["analysis_prompt"]
            },
            "translation_prompt": {
                "content": "Translate text: {text}",
                "relationships": ["summary_prompt"]
            }
        }

        network_analysis = relationship_manager.analyze_relationship_network(prompts_network)

        assert network_analysis["success"] is True

        # Should identify network structure
        network_structure = network_analysis["network_structure"]
        assert "central_nodes" in network_structure
        assert "leaf_nodes" in network_structure
        assert "network_density" in network_structure

        # Analysis prompt should be central (connected to 2 others)
        assert "analysis_prompt" in network_structure["central_nodes"]

        # Translation and insights should be leaf nodes
        leaf_nodes = network_structure["leaf_nodes"]
        assert "translation_prompt" in leaf_nodes or "insights_prompt" in leaf_nodes

    def test_relationship_validation_and_consistency(self, relationship_manager):
        """Test relationship validation and consistency checking."""
        relationships_to_validate = [
            {
                "source_id": str(uuid.uuid4()),
                "target_id": str(uuid.uuid4()),
                "type": "extends",
                "strength": 0.9,
                "is_valid": True
            },
            {
                "source_id": str(uuid.uuid4()),
                "target_id": str(uuid.uuid4()),
                "type": "invalid_type",
                "strength": 1.5,  # Invalid strength
                "is_valid": False
            },
            {
                "source_id": str(uuid.uuid4()),
                "target_id": str(uuid.uuid4()),
                "type": "extends",
                "strength": 0.1,  # Very weak relationship
                "is_valid": True,  # But should have warning
                "warnings": ["very_weak_relationship"]
            }
        ]

        for rel in relationships_to_validate:
            validation_result = relationship_manager.validate_relationship(rel)

            assert validation_result["is_valid"] == rel["is_valid"]

            if not rel["is_valid"]:
                assert "validation_errors" in validation_result
                assert len(validation_result["validation_errors"]) > 0
            else:
                if "warnings" in rel:
                    assert "warnings" in validation_result
                    for warning in rel["warnings"]:
                        assert any(warning in w.lower() for w in validation_result["warnings"])

    def test_relationship_inference_and_recommendation(self, relationship_manager):
        """Test relationship inference and recommendation system."""
        existing_relationships = [
            {"source": "analysis_prompt", "target": "summary_prompt", "type": "extends"},
            {"source": "summary_prompt", "target": "translation_prompt", "type": "chains_with"}
        ]

        new_prompt = {
            "id": str(uuid.uuid4()),
            "content": "Format the summary as a report: {summary_content}"
        }

        inference_result = relationship_manager.infer_relationships_for_new_prompt(
            new_prompt, existing_relationships
        )

        assert inference_result["success"] is True
        inferred_relationships = inference_result["inferred_relationships"]

        # Should infer relationship with summary_prompt (shared "summary" context)
        summary_relationships = [rel for rel in inferred_relationships
                               if rel["target"] == "summary_prompt"]

        assert len(summary_relationships) > 0

        # Should have reasonable confidence
        for rel in inferred_relationships:
            assert "confidence" in rel
            assert 0.3 <= rel["confidence"] <= 1.0  # Reasonable confidence range

    def test_relationship_maintenance_and_cleanup(self, relationship_manager):
        """Test relationship maintenance and cleanup operations."""
        # Simulate relationships with various issues
        relationships_data = {
            "valid_relationships": [
                {"id": str(uuid.uuid4()), "source_id": str(uuid.uuid4()), "target_id": str(uuid.uuid4()),
                 "strength": 0.8, "last_validated": datetime.now()}
            ],
            "stale_relationships": [
                {"id": str(uuid.uuid4()), "source_id": str(uuid.uuid4()), "target_id": str(uuid.uuid4()),
                 "strength": 0.6, "last_validated": datetime.now() - timedelta(days=100)}
            ],
            "weak_relationships": [
                {"id": str(uuid.uuid4()), "source_id": str(uuid.uuid4()), "target_id": str(uuid.uuid4()),
                 "strength": 0.1, "last_validated": datetime.now()}
            ],
            "orphaned_relationships": [
                {"id": str(uuid.uuid4()), "source_id": "nonexistent_id", "target_id": str(uuid.uuid4()),
                 "strength": 0.7, "last_validated": datetime.now()}
            ]
        }

        maintenance_result = relationship_manager.perform_relationship_maintenance(relationships_data)

        assert maintenance_result["success"] is True
        maintenance_actions = maintenance_result["maintenance_actions"]

        # Should identify stale relationships for review
        assert "stale_relationships_identified" in maintenance_actions
        assert len(maintenance_actions["stale_relationships_identified"]) > 0

        # Should identify weak relationships for cleanup
        assert "weak_relationships_identified" in maintenance_actions
        assert len(maintenance_actions["weak_relationships_identified"]) > 0

        # Should identify orphaned relationships for removal
        assert "orphaned_relationships_identified" in maintenance_actions
        assert len(maintenance_actions["orphaned_relationships_identified"]) > 0

        # Should keep valid relationships
        assert "valid_relationships_preserved" in maintenance_actions
        assert len(maintenance_actions["valid_relationships_preserved"]) > 0
