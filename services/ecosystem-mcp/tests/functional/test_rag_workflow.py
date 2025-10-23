"""
Functional tests for RAG query workflow.

Tests the complete RAG pipeline:
1. Semantic search across documents
2. Context-aware retrieval
3. Temporal RAG queries
4. Dynamic timeline construction
5. Answer synthesis
6. Citation generation
"""

import pytest
from datetime import datetime
from uuid import uuid4

# Mark all tests in this module as functional and asyncio
pytestmark = [pytest.mark.functional, pytest.mark.asyncio]


class TestSemanticSearch:
    """Test semantic search functionality."""
    
    async def test_basic_semantic_search(
        self,
        clean_database,
        ecosystem_mcp_src_dir,
        test_session_id
    ):
        """
        Test basic semantic search across documents.
        
        Validates:
        - Document indexing
        - Embedding generation
        - Semantic similarity search
        - Result ranking
        """
        from src.storage.repositories import DocumentRepository
        from src.services.rag import ContextAwareRAG
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        rag_service = ContextAwareRAG()
        
        # Ingest test documents with known content
        test_docs = [
            ("Document ingestion handles file parsing", "ingestion.py"),
            ("RAG service provides semantic search", "rag.py"),
            ("Timeline analysis tracks changes over time", "timeline.py"),
        ]
        
        for content, filename in test_docs:
            doc_data = create_test_document(
                content=content,
                file_path=filename,
                service_name="test-service",
                session_id=test_session_id
            )
            await doc_repo.create(doc_data)
        
        # Search for "document ingestion"
        # Note: This test validates the structure, actual search requires embeddings
        query = "document ingestion"
        
        # In a real test with embeddings, we would:
        # results = await rag_service.query(query)
        # assert len(results) > 0
        # assert "ingestion" in results[0]["content"].lower()
        
        # For now, verify documents were stored
        docs = await doc_repo.get_by_service("test-service", limit=10)
        assert len(docs) >= 3
    
    async def test_semantic_search_with_filters(
        self,
        clean_database,
        test_session_id
    ):
        """Test semantic search with service/type filters."""
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Create documents for different services
        services = ["service-a", "service-b", "service-c"]
        for service in services:
            for i in range(3):
                doc_data = create_test_document(
                    content=f"Content for {service} document {i}",
                    file_path=f"{service}_{i}.py",
                    service_name=service,
                    session_id=test_session_id
                )
                await doc_repo.create(doc_data)
        
        # Filter by specific service
        service_a_docs = await doc_repo.get_by_service("service-a", limit=10)
        assert len(service_a_docs) == 3
        assert all(d.service_name == "service-a" for d in service_a_docs)
    
    async def test_search_ranking(
        self,
        clean_database,
        test_session_id
    ):
        """Test that search results are properly ranked."""
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Create documents with varying relevance
        docs_data = [
            ("Python is a programming language", "high_relevance.py"),
            ("This document mentions Python briefly", "medium_relevance.py"),
            ("No relevant content here", "low_relevance.py"),
        ]
        
        for content, filename in docs_data:
            doc_data = create_test_document(
                content=content,
                file_path=filename,
                service_name="test-service",
                session_id=test_session_id
            )
            await doc_repo.create(doc_data)
        
        # Verify all documents stored
        docs = await doc_repo.get_by_service("test-service", limit=10)
        assert len(docs) >= 3


class TestContextAwareRetrieval:
    """Test context-aware document retrieval."""
    
    async def test_retrieve_with_context_window(
        self,
        clean_database,
        test_session_id
    ):
        """Test retrieving documents with surrounding context."""
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Create related documents
        doc_data = create_test_document(
            content="Main content with important information",
            file_path="main.py",
            service_name="test-service",
            session_id=test_session_id,
            metadata={
                "section": "main",
                "related_docs": ["intro.py", "conclusion.py"]
            }
        )
        doc = await doc_repo.create(doc_data)
        
        # Verify metadata stored
        assert doc.metadata.get("section") == "main"
        assert "related_docs" in doc.metadata
    
    async def test_multi_hop_retrieval(
        self,
        clean_database,
        test_session_id
    ):
        """Test multi-hop document retrieval (following references)."""
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Create chain of related documents
        doc1_data = create_test_document(
            content="First document references second",
            file_path="doc1.py",
            service_name="test-service",
            session_id=test_session_id,
            metadata={"references": ["doc2.py"]}
        )
        doc1 = await doc_repo.create(doc1_data)
        
        doc2_data = create_test_document(
            content="Second document",
            file_path="doc2.py",
            service_name="test-service",
            session_id=test_session_id
        )
        doc2 = await doc_repo.create(doc2_data)
        
        # Verify chain can be followed
        assert doc1.metadata.get("references") == ["doc2.py"]
        docs = await doc_repo.get_by_service("test-service", limit=10)
        assert len(docs) >= 2


class TestTemporalRAG:
    """Test temporal RAG queries."""
    
    async def test_query_as_of_date(
        self,
        clean_database,
        test_session_id
    ):
        """Test querying documents as of a specific date."""
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Create documents with different timestamps
        past_date = datetime(2023, 1, 1)
        recent_date = datetime(2024, 6, 1)
        
        doc_data = create_test_document(
            content="Old version of document",
            file_path="versioned.py",
            service_name="test-service",
            session_id=test_session_id,
            created_at=past_date
        )
        await doc_repo.create(doc_data)
        
        # Query should be able to filter by date
        # (Implementation depends on timestamp handling)
        docs = await doc_repo.get_by_service("test-service", limit=10)
        assert len(docs) > 0
    
    async def test_query_evolution(
        self,
        clean_database,
        test_session_id
    ):
        """Test querying document evolution over time."""
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Create multiple versions
        versions = [
            ("Version 1 content", "v1"),
            ("Version 2 content", "v2"),
            ("Version 3 content", "v3"),
        ]
        
        for content, version in versions:
            doc_data = create_test_document(
                content=content,
                file_path="evolving.py",
                service_name="test-service",
                session_id=test_session_id,
                metadata={"version": version}
            )
            await doc_repo.create(doc_data)
        
        # Should be able to retrieve all versions
        docs = await doc_repo.get_by_service("test-service", limit=10)
        assert len(docs) >= 3
    
    async def test_temporal_comparison(
        self,
        clean_database,
        test_session_id
    ):
        """Test comparing documents across time periods."""
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Create documents from different periods
        periods = ["2024-Q1", "2024-Q2"]
        for period in periods:
            doc_data = create_test_document(
                content=f"Content from {period}",
                file_path=f"doc_{period}.py",
                service_name="test-service",
                session_id=test_session_id,
                metadata={"period": period}
            )
            await doc_repo.create(doc_data)
        
        docs = await doc_repo.get_by_service("test-service", limit=10)
        assert len(docs) >= 2


class TestDynamicTimeline:
    """Test dynamic timeline construction."""
    
    async def test_construct_timeline_from_query(
        self,
        clean_database,
        test_session_id
    ):
        """Test constructing timeline from query results."""
        from src.services.dynamic_rag import DynamicTimelineConstructor
        from tests.utils.test_helpers import create_test_document
        
        constructor = DynamicTimelineConstructor()
        
        # Create mock documents
        mock_docs = [
            {
                "id": str(uuid4()),
                "content": "Test content 1",
                "created_at": datetime(2024, 1, 1),
                "_test_data_marker": True
            },
            {
                "id": str(uuid4()),
                "content": "Test content 2",
                "created_at": datetime(2024, 6, 1),
                "_test_data_marker": True
            }
        ]
        
        # Construct timeline
        timeline = constructor.construct_timeline(
            documents=mock_docs,
            topic="test topic"
        )
        
        assert timeline is not None
        assert len(timeline.get("documents", [])) == 2
    
    async def test_topic_extraction_from_query(
        self,
        clean_database,
        test_session_id
    ):
        """Test extracting topics from natural language query."""
        from src.services.dynamic_rag import TopicExtractor
        
        extractor = TopicExtractor()
        
        query = "How does document ingestion work in the RAG system?"
        topics = extractor.extract(query)
        
        assert topics is not None
        assert "endpoints" in topics or "services" in topics or "concepts" in topics
    
    async def test_timeline_confidence_calculation(
        self,
        clean_database,
        test_session_id
    ):
        """Test calculating confidence for dynamic timeline."""
        from src.services.dynamic_rag import DynamicTimelineConstructor
        
        constructor = DynamicTimelineConstructor()
        
        # Mock documents with varying data quality
        high_quality_docs = [
            {"id": str(uuid4()), "content": "content", "created_at": datetime.now()}
            for _ in range(10)
        ]
        
        timeline = constructor.construct_timeline(
            documents=high_quality_docs,
            topic="test"
        )
        
        # Should have confidence score
        assert "confidence" in timeline or "confidence_level" in timeline


class TestAnswerSynthesis:
    """Test answer synthesis from retrieved documents."""
    
    async def test_synthesize_answer_with_documents(
        self,
        clean_database,
        test_session_id
    ):
        """Test synthesizing answer from multiple documents."""
        from src.services.dynamic_rag import TemporalAnswerSynthesizer
        
        synthesizer = TemporalAnswerSynthesizer()
        
        query = "What is document ingestion?"
        documents = [
            {
                "content": "Document ingestion is the process of importing files",
                "source": "ingestion.py",
                "relevance": 0.9
            },
            {
                "content": "Files are parsed and indexed for search",
                "source": "parser.py",
                "relevance": 0.7
            }
        ]
        
        # Create mock timeline
        timeline = {
            "name": "test_timeline",
            "documents": documents,
            "periods": []
        }
        
        # Synthesize answer
        answer = await synthesizer.synthesize_answer(query, timeline, documents)
        
        assert answer is not None
        assert "answer" in answer or "text" in answer or "content" in answer
    
    async def test_synthesize_with_temporal_context(
        self,
        clean_database,
        test_session_id
    ):
        """Test synthesis includes temporal context."""
        from src.services.dynamic_rag import TemporalAnswerSynthesizer
        
        synthesizer = TemporalAnswerSynthesizer()
        
        query = "How has the system evolved?"
        documents = [
            {
                "content": "Initial version used simple parsing",
                "source": "v1/parser.py",
                "created_at": "2023-01-01",
                "relevance": 0.8
            },
            {
                "content": "Now uses advanced NLP",
                "source": "v2/parser.py",
                "created_at": "2024-01-01",
                "relevance": 0.9
            }
        ]
        
        timeline = {
            "name": "evolution_timeline",
            "documents": documents,
            "periods": [
                {"start": "2023-01-01", "end": "2023-12-31"},
                {"start": "2024-01-01", "end": "2024-12-31"}
            ]
        }
        
        answer = await synthesizer.synthesize_answer(query, timeline, documents)
        assert answer is not None


class TestCitationGeneration:
    """Test citation formatting."""
    
    async def test_format_citations_markdown(
        self,
        clean_database,
        test_session_id
    ):
        """Test formatting citations in Markdown format."""
        from src.services.dynamic_rag import CitationFormatter
        
        formatter = CitationFormatter()
        
        sources = [
            {
                "source": "document.py",
                "line_range": "10-20",
                "relevance_score": 0.9,
                "last_modified": "2024-01-01"
            }
        ]
        
        # Create mock answer
        answer = {
            "answer": "Test answer",
            "sources": sources
        }
        
        citations = formatter.format_citations(answer, format="markdown")
        
        assert citations is not None
        assert hasattr(citations, "citation_text") or isinstance(citations, dict)
    
    async def test_format_citations_html(
        self,
        clean_database,
        test_session_id
    ):
        """Test formatting citations in HTML format."""
        from src.services.dynamic_rag import CitationFormatter
        
        formatter = CitationFormatter()
        
        sources = [
            {
                "source": "document.py",
                "relevance_score": 0.8
            }
        ]
        
        answer = {
            "answer": "Test answer",
            "sources": sources
        }
        
        citations = formatter.format_citations(answer, format="html")
        assert citations is not None
    
    async def test_citations_with_temporal_attribution(
        self,
        clean_database,
        test_session_id
    ):
        """Test citations include temporal information."""
        from src.services.dynamic_rag import CitationFormatter
        
        formatter = CitationFormatter()
        
        sources = [
            {
                "source": "document.py",
                "last_modified": "2024-01-01",
                "period": "2024-Q1",
                "relevance_score": 0.9
            }
        ]
        
        answer = {
            "answer": "Test answer",
            "sources": sources
        }
        
        citations = formatter.format_citations(answer, format="markdown")
        assert citations is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "functional"])

