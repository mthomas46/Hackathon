"""Pytest configuration and shared fixtures for Interpreter Service tests.

This module provides comprehensive test fixtures for enterprise-grade testing
of NLP processing, LLM integration, workflow execution, and document analysis.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime, timedelta

from modules.models import (
    QueryContext, DocumentContext, WorkflowContext,
    IntentClassification, EntityExtraction, NLPResult,
    WorkflowExecution, DocumentAnalysis
)


# =============================================================================
# SHARED TEST FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def request_id():
    """Generate a unique request ID for each test."""
    return str(uuid.uuid4())


@pytest.fixture(scope="function")
def correlation_id():
    """Generate a unique correlation ID for each test."""
    return str(uuid.uuid4())


@pytest.fixture(scope="function")
def test_timestamp():
    """Provide a consistent timestamp for testing."""
    return datetime(2024, 1, 1, 12, 0, 0)


# =============================================================================
# DOMAIN MODEL FIXTURES
# =============================================================================

@pytest.fixture
def sample_query_context():
    """Sample QueryContext for NLP processing."""
    return QueryContext(
        query_id=str(uuid.uuid4()),
        original_query="Find all documents related to AI and machine learning from the last quarter",
        processed_query="documents AI machine learning last quarter",
        query_type="search",
        intent="document_search",
        entities={
            "topics": ["AI", "machine learning"],
            "time_range": "last quarter",
            "document_type": "all"
        },
        metadata={
            "user_id": "test_user",
            "session_id": str(uuid.uuid4()),
            "confidence_score": 0.89,
            "processing_time_ms": 150
        },
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=1)
    )


@pytest.fixture
def sample_document_context():
    """Sample DocumentContext for document processing."""
    return DocumentContext(
        document_id=str(uuid.uuid4()),
        content="This document discusses artificial intelligence and machine learning algorithms...",
        title="AI and ML Overview",
        content_type="text",
        metadata={
            "author": "John Doe",
            "created_date": "2024-01-01",
            "tags": ["AI", "ML", "algorithms"],
            "word_count": 1250,
            "language": "en"
        },
        embeddings=[0.1, 0.2, 0.3],  # Mock embeddings
        analysis_results={
            "sentiment": "neutral",
            "topics": ["artificial intelligence", "machine learning"],
            "entities": ["algorithms", "neural networks"],
            "complexity_score": 0.75
        },
        processing_status="completed",
        processed_at=datetime.now()
    )


@pytest.fixture
def sample_workflow_context():
    """Sample WorkflowContext for workflow execution."""
    return WorkflowContext(
        workflow_id=str(uuid.uuid4()),
        name="Document Analysis Workflow",
        description="Automated document processing and analysis",
        steps=[
            {
                "step_id": "extract_text",
                "name": "Text Extraction",
                "type": "processing",
                "config": {"method": "ocr"},
                "order": 1
            },
            {
                "step_id": "analyze_content",
                "name": "Content Analysis",
                "type": "analysis",
                "config": {"model": "gpt-4", "analysis_type": "comprehensive"},
                "order": 2,
                "depends_on": ["extract_text"]
            },
            {
                "step_id": "generate_summary",
                "name": "Summary Generation",
                "type": "generation",
                "config": {"max_length": 200, "style": "concise"},
                "order": 3,
                "depends_on": ["analyze_content"]
            }
        ],
        input_data={"document_url": "https://example.com/doc.pdf"},
        execution_context={
            "user_id": "test_user",
            "priority": "normal",
            "timeout_seconds": 300,
            "notification_enabled": True
        },
        status="running",
        created_at=datetime.now(),
        started_at=datetime.now(),
        current_step="analyze_content"
    )


@pytest.fixture
def sample_intent_classification():
    """Sample IntentClassification for NLP testing."""
    return IntentClassification(
        query_id=str(uuid.uuid4()),
        primary_intent="document_search",
        confidence_score=0.92,
        secondary_intents=[
            {"intent": "information_retrieval", "confidence": 0.78},
            {"intent": "content_analysis", "confidence": 0.65}
        ],
        intent_features={
            "keywords": ["find", "documents", "related"],
            "question_words": ["what", "how"],
            "action_verbs": ["find", "search", "analyze"],
            "temporal_indicators": ["last", "recent"]
        },
        classification_metadata={
            "model_used": "intent_classifier_v2",
            "processing_time_ms": 45,
            "training_data_version": "2024.01"
        },
        classified_at=datetime.now()
    )


@pytest.fixture
def sample_entity_extraction():
    """Sample EntityExtraction for NLP testing."""
    return EntityExtraction(
        text_id=str(uuid.uuid4()),
        entities=[
            {
                "text": "machine learning",
                "type": "technology",
                "confidence": 0.95,
                "start_pos": 25,
                "end_pos": 41,
                "metadata": {"category": "AI/ML", "aliases": ["ML"]}
            },
            {
                "text": "John Doe",
                "type": "person",
                "confidence": 0.88,
                "start_pos": 100,
                "end_pos": 108,
                "metadata": {"role": "author"}
            },
            {
                "text": "2024-01-15",
                "type": "date",
                "confidence": 0.97,
                "start_pos": 150,
                "end_pos": 160,
                "metadata": {"format": "ISO8601"}
            }
        ],
        extraction_metadata={
            "model_used": "entity_extractor_v3",
            "processing_time_ms": 120,
            "total_entities_found": 15,
            "confidence_threshold": 0.7
        },
        extracted_at=datetime.now()
    )


@pytest.fixture
def sample_nlp_result():
    """Sample NLPResult combining intent and entity extraction."""
    return NLPResult(
        query_id=str(uuid.uuid4()),
        original_text="Find all documents about machine learning written by John Doe in 2024",
        processed_text="find all documents about machine learning written by john doe in 2024",
        intent_classification=IntentClassification(
            query_id=str(uuid.uuid4()),
            primary_intent="document_search",
            confidence_score=0.94,
            secondary_intents=[],
            intent_features={},
            classification_metadata={},
            classified_at=datetime.now()
        ),
        entity_extraction=EntityExtraction(
            text_id=str(uuid.uuid4()),
            entities=[
                {"text": "machine learning", "type": "technology", "confidence": 0.95},
                {"text": "John Doe", "type": "person", "confidence": 0.88},
                {"text": "2024", "type": "date", "confidence": 0.97}
            ],
            extraction_metadata={},
            extracted_at=datetime.now()
        ),
        sentiment_analysis={
            "sentiment": "neutral",
            "confidence": 0.82,
            "scores": {"positive": 0.15, "neutral": 0.70, "negative": 0.15}
        },
        readability_metrics={
            "flesch_reading_ease": 65.2,
            "grade_level": 8.5,
            "complexity_score": 0.45
        },
        processing_metadata={
            "total_processing_time_ms": 285,
            "pipeline_version": "nlp_pipeline_v2.1",
            "models_used": ["intent_classifier", "entity_extractor", "sentiment_analyzer"]
        },
        processed_at=datetime.now()
    )


@pytest.fixture
def sample_workflow_execution():
    """Sample WorkflowExecution for workflow testing."""
    return WorkflowExecution(
        execution_id=str(uuid.uuid4()),
        workflow_id=str(uuid.uuid4()),
        status="running",
        current_step="analyze_content",
        step_results={
            "extract_text": {
                "status": "completed",
                "started_at": datetime.now() - timedelta(minutes=5),
                "completed_at": datetime.now() - timedelta(minutes=4),
                "result": {"text_length": 2500, "pages": 5},
                "metrics": {"processing_time_ms": 1250, "success_rate": 1.0}
            },
            "analyze_content": {
                "status": "running",
                "started_at": datetime.now() - timedelta(minutes=4),
                "result": {"topics_identified": 8, "entities_found": 12},
                "metrics": {"processing_time_ms": 3200}
            }
        },
        input_data={"document_url": "https://example.com/document.pdf"},
        output_data={},
        execution_context={
            "user_id": "test_user",
            "priority": "high",
            "timeout_seconds": 600,
            "retry_policy": {"max_retries": 3, "backoff_factor": 2}
        },
        started_at=datetime.now() - timedelta(minutes=5),
        updated_at=datetime.now(),
        estimated_completion=datetime.now() + timedelta(minutes=3),
        progress_percentage=65.0
    )


@pytest.fixture
def sample_document_analysis():
    """Sample DocumentAnalysis for document processing testing."""
    return DocumentAnalysis(
        document_id=str(uuid.uuid4()),
        analysis_type="comprehensive",
        content_summary="This document provides an overview of machine learning algorithms and their applications in modern AI systems.",
        key_insights=[
            "Machine learning algorithms have become essential for AI applications",
            "Supervised learning methods show 85% accuracy on test datasets",
            "Neural networks perform best with large training datasets"
        ],
        topics_detected=[
            {"topic": "Machine Learning", "confidence": 0.95, "relevance": 0.9},
            {"topic": "AI Applications", "confidence": 0.87, "relevance": 0.8},
            {"topic": "Neural Networks", "confidence": 0.82, "relevance": 0.7}
        ],
        sentiment="positive",
        readability_score=72.5,
        complexity_level="intermediate",
        quality_metrics={
            "completeness_score": 0.88,
            "accuracy_score": 0.92,
            "relevance_score": 0.85,
            "overall_quality": 0.89
        },
        extracted_metadata={
            "word_count": 2150,
            "sentence_count": 95,
            "paragraph_count": 18,
            "language": "en",
            "reading_time_minutes": 8.5
        },
        processing_metadata={
            "model_used": "document_analyzer_v2",
            "processing_time_ms": 2450,
            "api_calls_made": 3,
            "cache_used": False
        },
        analyzed_at=datetime.now()
    )


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_llm_gateway():
    """Mock LLM Gateway client for AI-powered features."""
    mock_llm = AsyncMock()
    mock_llm.generate_response = AsyncMock(return_value={
        "response": "Based on the analysis, this document discusses machine learning algorithms...",
        "tokens_used": 150,
        "model": "gpt-4",
        "confidence": 0.89
    })
    mock_llm.analyze_text = AsyncMock(return_value={
        "sentiment": "positive",
        "topics": ["technology", "innovation"],
        "entities": ["algorithms", "neural networks"],
        "complexity": "medium"
    })
    mock_llm.classify_intent = AsyncMock(return_value={
        "intent": "document_analysis",
        "confidence": 0.92,
        "features": ["analysis", "document", "processing"]
    })
    mock_llm.extract_entities = AsyncMock(return_value=[
        {"text": "machine learning", "type": "technology", "confidence": 0.95},
        {"text": "John Doe", "type": "person", "confidence": 0.88}
    ])
    return mock_llm


@pytest.fixture
def mock_orchestrator():
    """Mock Orchestrator client for workflow coordination."""
    mock_orch = AsyncMock()
    mock_orch.execute_workflow = AsyncMock(return_value={
        "execution_id": str(uuid.uuid4()),
        "status": "running",
        "estimated_completion": datetime.now() + timedelta(minutes=5)
    })
    mock_orch.get_workflow_status = AsyncMock(return_value={
        "status": "completed",
        "progress": 100.0,
        "result": {"processed_items": 150, "success_rate": 0.98}
    })
    mock_orch.list_workflows = AsyncMock(return_value=[
        {"id": str(uuid.uuid4()), "name": "Document Analysis", "status": "active"},
        {"id": str(uuid.uuid4()), "name": "Content Extraction", "status": "active"}
    ])
    return mock_orch


@pytest.fixture
def mock_document_store():
    """Mock Document Store client for document operations."""
    mock_doc = AsyncMock()
    mock_doc.store_document = AsyncMock(return_value={"document_id": str(uuid.uuid4())})
    mock_doc.retrieve_document = AsyncMock(return_value={
        "content": "Sample document content...",
        "metadata": {"author": "Test Author", "created": "2024-01-01"}
    })
    mock_doc.search_documents = AsyncMock(return_value=[
        {"id": str(uuid.uuid4()), "title": "AI Overview", "relevance": 0.95},
        {"id": str(uuid.uuid4()), "title": "ML Algorithms", "relevance": 0.87}
    ])
    mock_doc.update_document = AsyncMock(return_value={"updated": True})
    mock_doc.delete_document = AsyncMock(return_value={"deleted": True})
    return mock_doc


@pytest.fixture
def mock_memory_agent():
    """Mock Memory Agent client for context management."""
    mock_memory = AsyncMock()
    mock_memory.store_context = AsyncMock(return_value={"context_id": str(uuid.uuid4())})
    mock_memory.retrieve_context = AsyncMock(return_value={
        "context": "Previous conversation about AI and ML...",
        "confidence": 0.85,
        "timestamp": datetime.now()
    })
    mock_memory.search_memories = AsyncMock(return_value=[
        {"id": str(uuid.uuid4()), "content": "AI discussion", "relevance": 0.92},
        {"id": str(uuid.uuid4()), "content": "ML algorithms", "relevance": 0.78}
    ])
    return mock_memory


@pytest.fixture
def mock_prompt_store():
    """Mock Prompt Store client for prompt management."""
    mock_prompt = AsyncMock()
    mock_prompt.get_prompt = AsyncMock(return_value={
        "prompt_id": str(uuid.uuid4()),
        "content": "Analyze the following document and provide insights...",
        "category": "analysis",
        "version": "2.1"
    })
    mock_prompt.list_prompts = AsyncMock(return_value=[
        {"id": str(uuid.uuid4()), "name": "Document Analysis", "category": "analysis"},
        {"id": str(uuid.uuid4()), "name": "Content Summary", "category": "summarization"}
    ])
    return mock_prompt


@pytest.fixture
def mock_nlp_processor():
    """Mock NLP processor for text analysis."""
    mock_nlp = MagicMock()
    mock_nlp.process_text = MagicMock(return_value={
        "tokens": ["analyze", "document", "content"],
        "pos_tags": ["VERB", "NOUN", "NOUN"],
        "entities": [{"text": "document", "type": "OBJECT"}],
        "sentiment": "neutral"
    })
    mock_nlp.extract_keywords = MagicMock(return_value=["analysis", "document", "content", "insights"])
    mock_nlp.calculate_similarity = MagicMock(return_value=0.85)
    return mock_nlp


@pytest.fixture
def mock_workflow_engine():
    """Mock workflow execution engine."""
    mock_engine = AsyncMock()
    mock_engine.execute_step = AsyncMock(return_value={
        "status": "completed",
        "result": {"processed_data": "sample_result"},
        "metrics": {"execution_time_ms": 1500, "success": True}
    })
    mock_engine.validate_workflow = AsyncMock(return_value={
        "valid": True,
        "issues": []
    })
    mock_engine.get_execution_status = AsyncMock(return_value={
        "status": "running",
        "progress": 65.0,
        "current_step": "analysis"
    })
    return mock_engine


# =============================================================================
# INTEGRATION TEST FIXTURES
# =============================================================================

@pytest.fixture
def integration_config():
    """Configuration for integration tests."""
    return {
        "llm_gateway_url": "http://localhost:5020",
        "orchestrator_url": "http://localhost:5050",
        "document_store_url": "http://localhost:5010",
        "memory_agent_url": "http://localhost:5040",
        "prompt_store_url": "http://localhost:5110",
        "test_timeout": 30,
        "retry_attempts": 3,
        "test_data": {
            "documents": 10,
            "workflows": 5,
            "queries": 20
        }
    }


@pytest.fixture
def mock_external_services():
    """Mock external services for integration testing."""
    return {
        "llm_gateway": AsyncMock(),
        "orchestrator": AsyncMock(),
        "document_store": AsyncMock(),
        "memory_agent": AsyncMock(),
        "prompt_store": AsyncMock()
    }


# =============================================================================
# PERFORMANCE TEST FIXTURES
# =============================================================================

@pytest.fixture
def performance_test_data():
    """Test data for performance benchmarking."""
    return {
        "queries": [
            {
                "text": f"Analyze document {i} and provide insights about {'AI' if i % 2 == 0 else 'ML'} technologies",
                "type": "analysis",
                "complexity": "high" if i % 3 == 0 else "medium"
            }
            for i in range(100)
        ],
        "documents": [
            {
                "content": f"This is a sample document {i} about technology and innovation in the field of artificial intelligence and machine learning algorithms. " * 50,
                "title": f"Technology Document {i}",
                "word_count": 500 * (i + 1)
            }
            for i in range(50)
        ],
        "workflows": [
            {
                "name": f"Performance Workflow {i}",
                "steps": [
                    {"type": "nlp_processing", "config": {"model": "fast"}},
                    {"type": "analysis", "config": {"depth": "basic" if i % 2 == 0 else "comprehensive"}},
                    {"type": "generation", "config": {"length": "short"}}
                ]
            }
            for i in range(25)
        ]
    }


@pytest.fixture
def load_test_scenario():
    """Load testing scenario configuration."""
    return {
        "duration_seconds": 300,
        "concurrent_users": 50,
        "ramp_up_seconds": 60,
        "scenarios": {
            "query_processing": {
                "weight": 40,
                "steps": ["submit_query", "process_nlp", "generate_response"]
            },
            "document_analysis": {
                "weight": 35,
                "steps": ["upload_document", "analyze_content", "extract_insights", "generate_summary"]
            },
            "workflow_execution": {
                "weight": 25,
                "steps": ["create_workflow", "execute_workflow", "monitor_progress", "retrieve_results"]
            }
        },
        "thresholds": {
            "avg_response_time_ms": 2000,
            "error_rate_percent": 2.0,
            "throughput_queries_per_sec": 25
        }
    }


# =============================================================================
# CHAOS ENGINEERING FIXTURES
# =============================================================================

@pytest.fixture
def chaos_experiment_config():
    """Configuration for chaos engineering experiments."""
    return {
        "experiment_name": "interpreter_service_resilience",
        "duration_minutes": 15,
        "failure_scenarios": [
            {
                "type": "llm_gateway_failure",
                "target": "llm_gateway",
                "duration_seconds": 120,
                "impact": "high",
                "fallback_test": True
            },
            {
                "type": "high_latency",
                "target": "document_store",
                "latency_ms": 5000,
                "duration_seconds": 180,
                "impact": "medium"
            },
            {
                "type": "memory_pressure",
                "target": "interpreter_memory",
                "memory_limit_mb": 100,
                "duration_seconds": 300,
                "impact": "medium"
            }
        ],
        "monitoring": {
            "metrics": ["query_success_rate", "response_time", "error_rate", "memory_usage"],
            "alerts": ["error_rate > 10%", "response_time > 10000ms", "memory_usage > 90%"],
            "recovery_time_sla": 300
        }
    }


@pytest.fixture
def mock_failure_injector():
    """Mock failure injector for chaos testing."""
    mock_injector = MagicMock()
    mock_injector.inject_service_failure = MagicMock(return_value=True)
    mock_injector.inject_network_latency = MagicMock(return_value=True)
    mock_injector.inject_memory_pressure = MagicMock(return_value=True)
    mock_injector.restore_normal_operation = MagicMock(return_value=True)
    mock_injector.get_system_health = MagicMock(return_value={
        "status": "degraded",
        "active_failures": ["llm_gateway_down", "high_latency"],
        "recovery_eta_seconds": 45
    })
    return mock_injector
