"""Comprehensive Interpreter Service Tests.

Tests for natural language processing, intent recognition, workflow interpretation,
and AI-powered query understanding for the LLM Documentation Ecosystem.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import json

# Adjust path for local imports
import sys
from pathlib import Path

# Add the Interpreter service directory to Python path
interpreter_path = Path(__file__).parent.parent.parent.parent / "services" / "interpreter"
sys.path.insert(0, str(interpreter_path))

from modules.core.nlp_processor import NLPProcessor
from modules.core.intent_classifier import IntentClassifier
from modules.core.workflow_interpreter import WorkflowInterpreter
from modules.core.query_parser import QueryParser
from modules.models import InterpretationRequest, IntentClassification, WorkflowPlan

# Test markers for parallel execution and categorization
pytestmark = [
    pytest.mark.unit,
    pytest.mark.parallel_safe,
    pytest.mark.interpreter
]


@pytest.fixture
def mock_llm_gateway():
    """Mock LLM Gateway for testing."""
    with patch('modules.core.nlp_processor.LLMGateway') as mock_gateway_class:
        mock_gateway = MagicMock()
        mock_gateway_class.return_value = mock_gateway

        # Mock NLP responses
        mock_gateway.process_nlp = AsyncMock(return_value={
            "success": True,
            "intent": "analyze_documents",
            "confidence": 0.89,
            "entities": ["documents", "analysis"],
            "sentiment": "neutral"
        })

        mock_gateway.classify_intent = AsyncMock(return_value={
            "success": True,
            "primary_intent": "document_analysis",
            "confidence": 0.92,
            "secondary_intents": ["search", "summarize"]
        })

        yield mock_gateway


@pytest.fixture
def mock_orchestrator():
    """Mock Orchestrator for testing."""
    with patch('modules.core.workflow_interpreter.OrchestratorClient') as mock_orch_class:
        mock_orchestrator = MagicMock()
        mock_orch_class.return_value = mock_orchestrator

        mock_orchestrator.execute_workflow = AsyncMock(return_value={
            "success": True,
            "workflow_id": "wf-12345",
            "status": "executing",
            "estimated_completion": "5 minutes"
        })

        yield mock_orchestrator


@pytest.fixture
def nlp_processor(mock_llm_gateway):
    """Create NLPProcessor instance for testing."""
    return NLPProcessor()


@pytest.fixture
def intent_classifier(mock_llm_gateway):
    """Create IntentClassifier instance for testing."""
    return IntentClassifier()


@pytest.fixture
def workflow_interpreter(mock_orchestrator):
    """Create WorkflowInterpreter instance for testing."""
    return WorkflowInterpreter()


@pytest.fixture
def query_parser():
    """Create QueryParser instance for testing."""
    return QueryParser()


class TestNLPProcessor:
    """Comprehensive tests for NLP processing functionality."""

    def test_process_natural_language_query(self, nlp_processor, mock_llm_gateway):
        """Test processing of natural language queries."""
        query = "Analyze all API documentation for consistency and quality"

        result = nlp_processor.process_natural_language_query(query)

        assert isinstance(result, dict)
        assert "success" in result
        assert "intent" in result
        assert "entities" in result
        assert "confidence" in result

        # Verify LLM was called with correct parameters
        mock_llm_gateway.process_nlp.assert_called_once()

    def test_extract_entities_from_query(self, nlp_processor):
        """Test entity extraction from queries."""
        test_queries = [
            ("analyze API docs for quality", ["API docs", "quality"]),
            ("find documents about authentication", ["documents", "authentication"]),
            ("summarize user guides", ["user guides"]),
            ("check consistency between docs", ["consistency", "docs"])
        ]

        for query, expected_entities in test_queries:
            entities = nlp_processor.extract_entities(query)
            assert isinstance(entities, list)

            # Check that expected entities are found
            entity_texts = [e.get("text", "").lower() for e in entities]
            for expected in expected_entities:
                assert any(expected.lower() in text for text in entity_texts)

    def test_sentiment_analysis(self, nlp_processor, mock_llm_gateway):
        """Test sentiment analysis of queries."""
        test_queries = [
            ("This documentation is excellent!", "positive"),
            ("The docs are confusing and incomplete", "negative"),
            ("Please analyze the documentation", "neutral"),
            ("I need help with API documentation", "neutral")
        ]

        for query, expected_sentiment in test_queries:
            sentiment = nlp_processor.analyze_sentiment(query)
            assert isinstance(sentiment, dict)
            assert "sentiment" in sentiment
            # Note: Actual sentiment analysis would be more sophisticated

    def test_query_complexity_assessment(self, nlp_processor):
        """Test assessment of query complexity."""
        simple_query = "analyze docs"
        complex_query = "Analyze all API documentation for consistency, check cross-references, validate against schemas, and generate comprehensive quality reports"

        simple_complexity = nlp_processor.assess_query_complexity(simple_query)
        complex_complexity = nlp_processor.assess_query_complexity(complex_query)

        assert isinstance(simple_complexity, dict)
        assert isinstance(complex_complexity, dict)

        assert "complexity_score" in simple_complexity
        assert "complexity_score" in complex_complexity

        # Complex query should have higher complexity score
        assert complex_complexity["complexity_score"] > simple_complexity["complexity_score"]

    def test_context_awareness(self, nlp_processor):
        """Test context-aware query processing."""
        context = {
            "current_service": "doc_store",
            "recent_actions": ["viewed_document", "searched_api"],
            "user_role": "developer"
        }

        query = "analyze this"

        result = nlp_processor.process_with_context(query, context)

        assert isinstance(result, dict)
        assert "context_influenced" in result
        assert "adapted_intent" in result

    def test_multilingual_query_support(self, nlp_processor):
        """Test support for multilingual queries."""
        multilingual_queries = [
            "analyser la documentation",  # French
            "analizar documentación",     # Spanish
            "dokumentation analysieren",  # German
            "分析文档",                   # Chinese
            "analyze documentation"       # English
        ]

        for query in multilingual_queries:
            result = nlp_processor.process_multilingual_query(query)
            assert isinstance(result, dict)
            assert "detected_language" in result
            assert "translated_query" in result

    def test_query_intent_clarification(self, nlp_processor):
        """Test intent clarification for ambiguous queries."""
        ambiguous_query = "check docs"

        clarification = nlp_processor.clarify_intent(ambiguous_query)

        assert isinstance(clarification, dict)
        assert "needs_clarification" in clarification
        assert "suggested_intents" in clarification
        assert "clarification_questions" in clarification

        # Should suggest multiple possible interpretations
        assert len(clarification["suggested_intents"]) > 1

    def test_query_reformulation(self, nlp_processor):
        """Test query reformulation for better processing."""
        informal_query = "hey can u pls check my docs and tell me if they're good?"

        reformulated = nlp_processor.reformulate_query(informal_query)

        assert isinstance(reformulated, dict)
        assert "original_query" in reformulated
        assert "reformulated_query" in reformulated
        assert "improvements" in reformulated

        # Reformulated query should be more formal
        assert "please" not in reformulated["reformulated_query"].lower()

    def test_query_validation(self, nlp_processor):
        """Test query validation and sanitization."""
        valid_queries = [
            "analyze API documentation",
            "find user guides",
            "summarize technical specs"
        ]

        invalid_queries = [
            "",  # Empty
            "a" * 1000,  # Too long
            "<script>alert('xss')</script>",  # Malicious
            "   ",  # Whitespace only
        ]

        for query in valid_queries:
            validation = nlp_processor.validate_query(query)
            assert validation["valid"] is True

        for query in invalid_queries:
            validation = nlp_processor.validate_query(query)
            assert validation["valid"] is False
            assert "error" in validation

    def test_batch_query_processing(self, nlp_processor, mock_llm_gateway):
        """Test batch processing of multiple queries."""
        queries = [
            "analyze API docs",
            "find user guides",
            "check consistency"
        ]

        results = nlp_processor.batch_process_queries(queries)

        assert isinstance(results, list)
        assert len(results) == 3

        for result in results:
            assert isinstance(result, dict)
            assert "success" in result
            assert "query" in result

    def test_query_history_analysis(self, nlp_processor):
        """Test analysis of query history patterns."""
        query_history = [
            {"query": "analyze API docs", "timestamp": "2024-01-01T10:00:00Z"},
            {"query": "check API consistency", "timestamp": "2024-01-02T10:00:00Z"},
            {"query": "find API documentation", "timestamp": "2024-01-03T10:00:00Z"}
        ]

        analysis = nlp_processor.analyze_query_history(query_history)

        assert isinstance(analysis, dict)
        assert "patterns" in analysis
        assert "frequent_topics" in analysis
        assert "query_evolution" in analysis

        # Should identify API as frequent topic
        assert "api" in [topic.lower() for topic in analysis["frequent_topics"]]


class TestIntentClassifier:
    """Comprehensive tests for intent classification functionality."""

    def test_classify_user_intent(self, intent_classifier, mock_llm_gateway):
        """Test classification of user intents."""
        test_queries = [
            ("analyze all documents", "document_analysis"),
            ("find API documentation", "search"),
            ("summarize user guides", "summarization"),
            ("check document consistency", "quality_check"),
            ("create workflow", "workflow_creation")
        ]

        for query, expected_intent in test_queries:
            result = intent_classifier.classify_intent(query)

            assert isinstance(result, dict)
            assert "success" in result
            assert "primary_intent" in result
            assert "confidence" in result

    def test_multi_intent_detection(self, intent_classifier, mock_llm_gateway):
        """Test detection of multiple intents in a single query."""
        multi_intent_query = "analyze API docs, check consistency, and generate a summary report"

        result = intent_classifier.detect_multiple_intents(multi_intent_query)

        assert isinstance(result, dict)
        assert "intents" in result

        intents = result["intents"]
        assert isinstance(intents, list)
        assert len(intents) >= 2  # Should detect multiple intents

        # Should include analysis, consistency, and summarization
        intent_types = [intent.get("type") for intent in intents]
        assert any("analysis" in intent_type.lower() for intent_type in intent_types)
        assert any("consistency" in intent_type.lower() for intent_type in intent_types)
        assert any("summary" in intent_type.lower() for intent_type in intent_types)

    def test_intent_confidence_scoring(self, intent_classifier):
        """Test confidence scoring for intent classification."""
        clear_query = "analyze API documentation for quality"
        ambiguous_query = "check docs"

        clear_result = intent_classifier.classify_intent(clear_query)
        ambiguous_result = intent_classifier.classify_intent(ambiguous_query)

        # Clear query should have higher confidence
        assert clear_result["confidence"] > ambiguous_result["confidence"]

    def test_context_aware_intent_classification(self, intent_classifier):
        """Test context-aware intent classification."""
        query = "analyze this"

        contexts = [
            {"current_page": "document_browser", "recent_action": "viewed_document"},
            {"current_page": "workflow_dashboard", "recent_action": "created_workflow"},
            {"current_page": "search_results", "recent_action": "searched"}
        ]

        for context in contexts:
            result = intent_classifier.classify_with_context(query, context)

            assert isinstance(result, dict)
            assert "adapted_intent" in result
            assert "context_influence" in result

    def test_intent_hierarchy_classification(self, intent_classifier):
        """Test hierarchical intent classification."""
        query = "analyze API documentation for security vulnerabilities"

        hierarchy = intent_classifier.classify_intent_hierarchy(query)

        assert isinstance(hierarchy, dict)
        assert "primary_category" in hierarchy
        assert "sub_categories" in hierarchy
        assert "specific_actions" in hierarchy

        # Should identify security as a key aspect
        assert "security" in str(hierarchy).lower()

    def test_intent_pattern_learning(self, intent_classifier):
        """Test learning of intent patterns from user behavior."""
        training_data = [
            {"query": "analyze docs", "intent": "analysis", "outcome": "success"},
            {"query": "check quality", "intent": "quality_check", "outcome": "success"},
            {"query": "find documents", "intent": "search", "outcome": "success"}
        ]

        patterns = intent_classifier.learn_intent_patterns(training_data)

        assert isinstance(patterns, dict)
        assert "learned_patterns" in patterns
        assert "accuracy_improvements" in patterns

    def test_intent_ambiguity_resolution(self, intent_classifier):
        """Test resolution of ambiguous intents."""
        ambiguous_query = "process documents"

        resolution = intent_classifier.resolve_ambiguous_intent(ambiguous_query)

        assert isinstance(resolution, dict)
        assert "possible_intents" in resolution
        assert "recommended_action" in resolution
        assert "confidence_levels" in resolution

        # Should provide multiple possible interpretations
        assert len(resolution["possible_intents"]) > 1

    def test_domain_specific_intent_classification(self, intent_classifier):
        """Test domain-specific intent classification."""
        domain_queries = [
            ("analyze code for bugs", "software_development"),
            ("review API documentation", "technical_writing"),
            ("check compliance requirements", "governance"),
            ("find user manuals", "documentation")
        ]

        for query, expected_domain in domain_queries:
            result = intent_classifier.classify_domain_intent(query)

            assert isinstance(result, dict)
            assert "domain" in result
            assert "domain_specific_intent" in result

    def test_intent_temporal_classification(self, intent_classifier):
        """Test temporal aspects of intent classification."""
        temporal_queries = [
            "analyze yesterday's documents",
            "check this week's reports",
            "review last month's changes"
        ]

        for query in temporal_queries:
            result = intent_classifier.classify_temporal_intent(query)

            assert isinstance(result, dict)
            assert "temporal_context" in result
            assert "time_range" in result

    def test_intent_priority_assessment(self, intent_classifier):
        """Test assessment of intent priority levels."""
        priority_queries = [
            ("EMERGENCY: Security vulnerability found", "critical"),
            ("analyze documents when possible", "low"),
            ("review API changes", "medium")
        ]

        for query, expected_priority in priority_queries:
            result = intent_classifier.assess_intent_priority(query)

            assert isinstance(result, dict)
            assert "priority" in result
            assert "urgency_level" in result

    def test_intent_validation(self, intent_classifier):
        """Test validation of classified intents."""
        valid_intent = {"type": "analysis", "confidence": 0.85, "entities": ["docs"]}
        invalid_intent = {"type": "", "confidence": 1.5, "entities": []}

        valid_result = intent_classifier.validate_intent_classification(valid_intent)
        invalid_result = intent_classifier.validate_intent_classification(invalid_intent)

        assert valid_result["valid"] is True
        assert invalid_result["valid"] is False
        assert "validation_errors" in invalid_result


class TestWorkflowInterpreter:
    """Comprehensive tests for workflow interpretation functionality."""

    def test_interpret_query_to_workflow(self, workflow_interpreter, mock_orchestrator):
        """Test interpretation of queries into executable workflows."""
        query = "analyze all API documentation for consistency"

        result = workflow_interpreter.interpret_query_to_workflow(query)

        assert isinstance(result, dict)
        assert "success" in result
        assert "workflow_plan" in result

        plan = result["workflow_plan"]
        assert "steps" in plan
        assert "estimated_duration" in plan
        assert "required_services" in plan

    def test_execute_interpreted_workflow(self, workflow_interpreter, mock_orchestrator):
        """Test execution of interpreted workflows."""
        workflow_plan = {
            "steps": [
                {"action": "fetch_documents", "service": "doc_store"},
                {"action": "analyze_content", "service": "analysis_service"}
            ],
            "parameters": {"doc_type": "api"}
        }

        result = workflow_interpreter.execute_workflow(workflow_plan)

        assert isinstance(result, dict)
        assert "success" in result
        assert "execution_id" in result
        assert "status" in result

        # Verify orchestrator was called
        mock_orchestrator.execute_workflow.assert_called_once()

    def test_workflow_plan_validation(self, workflow_interpreter):
        """Test validation of workflow plans."""
        valid_plan = {
            "steps": [
                {"action": "analyze", "service": "analysis_service", "parameters": {}},
                {"action": "store", "service": "doc_store", "parameters": {}}
            ],
            "required_services": ["analysis_service", "doc_store"]
        }

        invalid_plan = {
            "steps": [],
            "required_services": []
        }

        valid_result = workflow_interpreter.validate_workflow_plan(valid_plan)
        invalid_result = workflow_interpreter.validate_workflow_plan(invalid_plan)

        assert valid_result["valid"] is True
        assert invalid_result["valid"] is False

    def test_dynamic_workflow_adaptation(self, workflow_interpreter):
        """Test dynamic adaptation of workflows based on context."""
        base_workflow = {
            "steps": [{"action": "analyze", "service": "analysis_service"}]
        }

        context = {
            "available_services": ["analysis_service", "summarizer_hub"],
            "user_preferences": {"include_summary": True},
            "data_characteristics": {"document_count": 50}
        }

        adapted = workflow_interpreter.adapt_workflow_dynamically(base_workflow, context)

        assert isinstance(adapted, dict)
        assert "adapted_steps" in adapted
        assert "adaptation_reasoning" in adapted

        # Should add summary step due to user preference
        steps = adapted["adapted_steps"]
        step_actions = [step.get("action") for step in steps]
        assert "summarize" in step_actions

    def test_workflow_dependency_resolution(self, workflow_interpreter):
        """Test resolution of workflow dependencies."""
        workflow_with_deps = {
            "steps": [
                {"action": "analyze", "depends_on": ["fetch"]},
                {"action": "summarize", "depends_on": ["analyze"]},
                {"action": "fetch", "depends_on": []}
            ]
        }

        resolved = workflow_interpreter.resolve_workflow_dependencies(workflow_with_deps)

        assert isinstance(resolved, dict)
        assert "execution_order" in resolved
        assert "dependency_graph" in resolved

        # Should order steps correctly: fetch -> analyze -> summarize
        execution_order = resolved["execution_order"]
        fetch_idx = next(i for i, step in enumerate(execution_order) if step["action"] == "fetch")
        analyze_idx = next(i for i, step in enumerate(execution_order) if step["action"] == "analyze")
        summarize_idx = next(i for i, step in enumerate(execution_order) if step["action"] == "summarize")

        assert fetch_idx < analyze_idx < summarize_idx

    def test_workflow_error_handling(self, workflow_interpreter, mock_orchestrator):
        """Test error handling in workflow execution."""
        mock_orchestrator.execute_workflow.side_effect = Exception("Service unavailable")

        workflow_plan = {"steps": [{"action": "test", "service": "test"}]}

        result = workflow_interpreter.execute_workflow(workflow_plan)

        assert isinstance(result, dict)
        assert result["success"] is False
        assert "error" in result
        assert "recovery_options" in result

    def test_workflow_progress_tracking(self, workflow_interpreter):
        """Test tracking of workflow execution progress."""
        workflow_id = "wf-progress-test"

        progress = workflow_interpreter.track_workflow_progress(workflow_id)

        assert isinstance(progress, dict)
        assert "current_step" in progress
        assert "completed_steps" in progress
        assert "remaining_steps" in progress
        assert "overall_progress" in progress

    def test_workflow_result_aggregation(self, workflow_interpreter):
        """Test aggregation of results from multi-step workflows."""
        step_results = [
            {"step": "fetch", "success": True, "documents_found": 25},
            {"step": "analyze", "success": True, "quality_score": 0.85},
            {"step": "summarize", "success": True, "summary_length": 500}
        ]

        aggregated = workflow_interpreter.aggregate_workflow_results(step_results)

        assert isinstance(aggregated, dict)
        assert "overall_success" in aggregated
        assert "aggregated_data" in aggregated
        assert "key_metrics" in aggregated

        # Should aggregate quality score and other metrics
        assert aggregated["overall_success"] is True

    def test_workflow_template_matching(self, workflow_interpreter):
        """Test matching queries to workflow templates."""
        query = "analyze API docs and create summary"

        templates = [
            {"name": "document_analysis", "triggers": ["analyze", "docs"]},
            {"name": "full_workflow", "triggers": ["analyze", "summary"]},
            {"name": "basic_search", "triggers": ["find", "search"]}
        ]

        matched = workflow_interpreter.match_workflow_template(query, templates)

        assert isinstance(matched, dict)
        assert "matched_template" in matched
        assert "confidence" in matched

        # Should match "full_workflow" template
        assert matched["matched_template"]["name"] == "full_workflow"

    def test_workflow_parameter_extraction(self, workflow_interpreter):
        """Test extraction of parameters from natural language queries."""
        query = "analyze the last 30 days of API documentation for quality issues"

        parameters = workflow_interpreter.extract_workflow_parameters(query)

        assert isinstance(parameters, dict)
        assert "time_range" in parameters
        assert "document_type" in parameters
        assert "analysis_type" in parameters

        # Should extract "30 days" as time range
        assert "30" in str(parameters["time_range"])
        assert parameters["document_type"] == "api"
        assert parameters["analysis_type"] == "quality"

    def test_workflow_optimization(self, workflow_interpreter):
        """Test optimization of workflow execution."""
        workflow_plan = {
            "steps": [
                {"action": "fetch", "service": "doc_store", "estimated_time": 10},
                {"action": "analyze", "service": "analysis_service", "estimated_time": 30},
                {"action": "summarize", "service": "summarizer_hub", "estimated_time": 15}
            ]
        }

        optimized = workflow_interpreter.optimize_workflow(workflow_plan)

        assert isinstance(optimized, dict)
        assert "optimized_steps" in optimized
        assert "estimated_total_time" in optimized
        assert "optimization_applied" in optimized

        # Should optimize step order for parallel execution where possible
        total_time = optimized["estimated_total_time"]
        assert isinstance(total_time, (int, float))


class TestQueryParser:
    """Comprehensive tests for query parsing functionality."""

    def test_parse_complex_query(self, query_parser):
        """Test parsing of complex natural language queries."""
        complex_query = """
        Please analyze all API documentation from the last quarter,
        check for consistency issues, validate against OpenAPI schemas,
        generate quality reports, and create executive summaries.
        Also, identify any security concerns and compliance gaps.
        """

        parsed = query_parser.parse_complex_query(complex_query)

        assert isinstance(parsed, dict)
        assert "main_actions" in parsed
        assert "qualifiers" in parsed
        assert "constraints" in parsed

        # Should identify multiple actions
        actions = parsed["main_actions"]
        assert len(actions) >= 3  # analyze, check, generate, create, identify

    def test_extract_temporal_constraints(self, query_parser):
        """Test extraction of temporal constraints from queries."""
        temporal_queries = [
            ("analyze documents from last week", {"period": "week", "direction": "past"}),
            ("check this month's reports", {"period": "month", "direction": "current"}),
            ("review next quarter's documentation", {"period": "quarter", "direction": "future"})
        ]

        for query, expected in temporal_queries:
            temporal = query_parser.extract_temporal_constraints(query)
            assert isinstance(temporal, dict)
            assert temporal["period"] == expected["period"]

    def test_identify_action_verbs(self, query_parser):
        """Test identification of action verbs in queries."""
        query = "find, analyze, and summarize all user documentation"

        actions = query_parser.identify_action_verbs(query)

        assert isinstance(actions, list)
        assert len(actions) >= 3

        action_verbs = [action.get("verb") for action in actions]
        assert "find" in action_verbs
        assert "analyze" in action_verbs
        assert "summarize" in action_verbs

    def test_parse_conditional_logic(self, query_parser):
        """Test parsing of conditional logic in queries."""
        conditional_query = "if documents are outdated then update them, otherwise just analyze"

        parsed = query_parser.parse_conditional_logic(conditional_query)

        assert isinstance(parsed, dict)
        assert "conditions" in parsed
        assert "actions" in parsed

        conditions = parsed["conditions"]
        assert len(conditions) > 0

        # Should identify the "outdated" condition
        condition_texts = [c.get("text", "") for c in conditions]
        assert any("outdated" in text.lower() for text in condition_texts)

    def test_extract_quantitative_constraints(self, query_parser):
        """Test extraction of quantitative constraints."""
        quantitative_query = "analyze top 50 documents with quality score above 0.8"

        constraints = query_parser.extract_quantitative_constraints(quantitative_query)

        assert isinstance(constraints, dict)
        assert "limits" in constraints
        assert "thresholds" in constraints

        # Should extract limit of 50 and threshold of 0.8
        assert constraints["limits"]["count"] == 50
        assert constraints["thresholds"]["quality_score"] == 0.8

    def test_parse_query_structure(self, query_parser):
        """Test parsing of overall query structure."""
        structured_query = """
        Subject: API Documentation
        Action: Comprehensive Analysis
        Scope: All versions from v1.0 to v2.0
        Output: Detailed report with recommendations
        """

        structure = query_parser.parse_query_structure(structured_query)

        assert isinstance(structure, dict)
        assert "subject" in structure
        assert "action" in structure
        assert "scope" in structure
        assert "output_requirements" in structure

    def test_handle_query_ambiguity(self, query_parser):
        """Test handling of ambiguous queries."""
        ambiguous_query = "process the docs"

        disambiguation = query_parser.handle_query_ambiguity(ambiguous_query)

        assert isinstance(disambiguation, dict)
        assert "ambiguous_terms" in disambiguation
        assert "clarification_options" in disambiguation
        assert "suggested_interpretations" in disambiguation

    def test_query_tokenization_and_normalization(self, query_parser):
        """Test tokenization and normalization of queries."""
        raw_query = "PLS ANALYZE the DOCS!!! and tell me what's wrong???"

        normalized = query_parser.tokenize_and_normalize(raw_query)

        assert isinstance(normalized, dict)
        assert "tokens" in normalized
        assert "normalized_query" in normalized

        # Should normalize case and remove punctuation
        normalized_text = normalized["normalized_query"]
        assert "pls" not in normalized_text.lower()
        assert "!!!" not in normalized_text
        assert "???" not in normalized_text

    def test_query_intent_hierarchy(self, query_parser):
        """Test parsing of hierarchical query intents."""
        hierarchical_query = "As a developer, I need to analyze the API documentation for security vulnerabilities and generate a compliance report for the security team"

        hierarchy = query_parser.parse_intent_hierarchy(hierarchical_query)

        assert isinstance(hierarchy, dict)
        assert "primary_intent" in hierarchy
        assert "secondary_intents" in hierarchy
        assert "stakeholder_context" in hierarchy
        assert "deliverables" in hierarchy

        # Should identify developer as stakeholder
        assert "developer" in str(hierarchy["stakeholder_context"]).lower()

    def test_cross_query_reference_resolution(self, query_parser):
        """Test resolution of references between queries."""
        query_context = [
            {"id": "q1", "query": "analyze API docs"},
            {"id": "q2", "query": "use the results from previous analysis"},
            {"id": "q3", "query": "compare with the first query results"}
        ]

        resolved = query_parser.resolve_cross_query_references(query_context)

        assert isinstance(resolved, dict)
        assert "resolved_queries" in resolved
        assert "reference_map" in resolved

        # Should resolve "previous analysis" to q1 and "first query" to q1
        reference_map = resolved["reference_map"]
        assert "q2" in reference_map
        assert "q3" in reference_map
