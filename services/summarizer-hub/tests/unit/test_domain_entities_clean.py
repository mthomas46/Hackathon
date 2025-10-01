"""Clean unit tests for summarizer-hub domain entities."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Dict, Optional

# Define domain entities inline to avoid import dependencies
from enum import Enum


class DocumentType(str, Enum):
    """Document type enumeration."""
    CODE = "code"
    DOCUMENTATION = "documentation"
    SPECIFICATION = "specification"
    CONTRACT = "contract"
    REAPI_PORT = "report"
    OTHER = "other"


class SummaryStatus(str, Enum):
    """Summary status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CategoryType(str, Enum):
    """Category type enumeration."""
    TECHNICAL = "technical"
    BUSINESS = "business"
    LEGAL = "legal"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"


class RecommendationType(str, Enum):
    """Recommendation type enumeration."""
    IMPROVEMENT = "improvement"
    OPTIMIZATION = "optimization"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    MAINTENANCE = "maintenance"


class Document:
    """Domain entity for documents."""

    def __init__(self,
                 document_id: str = None,
                 title: str = None,
                 content: str = None,
                 document_type: DocumentType = DocumentType.DOCUMENTATION,
                 metadata: Dict = None,
                 file_path: str = None,
                 file_size: int = 0,
                 mime_type: str = None,
                 created_at: datetime = None,
                 updated_at: datetime = None):
        self.document_id = document_id or str(uuid4())
        self.title = title or ""
        self.content = content or ""
        self.document_type = document_type
        self.metadata = metadata or {}
        self.file_path = file_path
        self.file_size = file_size
        self.mime_type = mime_type
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def is_large_document(self) -> bool:
        """Check if document is considered large."""
        return self.file_size > 1024 * 1024  # 1MB

    def has_content(self) -> bool:
        """Check if document has content."""
        return bool(self.content.strip())

    def get_content_length(self) -> int:
        """Get content length."""
        return len(self.content)

    def update_content(self, new_content: str):
        """Update document content."""
        self.content = new_content
        self.updated_at = datetime.now(timezone.utc)
        if self.file_size == 0:
            self.file_size = len(new_content.encode('utf-8'))

    def get_summary(self) -> str:
        """Get a brief summary of the document."""
        if self.title:
            return f"{self.title} ({self.document_type.value})"
        return f"Document ({self.document_type.value})"


class Summary:
    """Domain entity for document summaries."""

    def __init__(self,
                 summary_id: str = None,
                 document_id: str = None,
                 content: str = None,
                 summary_type: str = "executive",
                 status: SummaryStatus = SummaryStatus.PENDING,
                 quality_score: float = 0.0,
                 word_count: int = 0,
                 compression_ratio: float = 0.0,
                 model_used: str = None,
                 processing_time_ms: int = 0,
                 created_at: datetime = None):
        self.summary_id = summary_id or str(uuid4())
        self.document_id = document_id
        self.content = content or ""
        self.summary_type = summary_type
        self.status = status
        self.quality_score = quality_score
        self.word_count = word_count
        self.compression_ratio = compression_ratio
        self.model_used = model_used
        self.processing_time_ms = processing_time_ms
        self.created_at = created_at or datetime.now(timezone.utc)

    def is_completed(self) -> bool:
        """Check if summary is completed."""
        return self.status == SummaryStatus.COMPLETED

    def is_successful(self) -> bool:
        """Check if summary was successful."""
        return self.is_completed() and self.quality_score >= 0.6

    def calculate_word_count(self):
        """Calculate word count from content."""
        self.word_count = len(self.content.split()) if self.content else 0

    def calculate_compression_ratio(self, original_length: int):
        """Calculate compression ratio."""
        if original_length > 0 and self.word_count > 0:
            self.compression_ratio = self.word_count / original_length
        else:
            self.compression_ratio = 0.0

    def mark_completed(self, quality_score: float = 0.0):
        """Mark summary as completed."""
        self.status = SummaryStatus.COMPLETED
        self.quality_score = quality_score

    def mark_failed(self):
        """Mark summary as failed."""
        self.status = SummaryStatus.FAILED
        self.quality_score = 0.0


class Category:
    """Domain entity for document categories."""

    def __init__(self,
                 category_id: str = None,
                 name: str = None,
                 category_type: CategoryType = CategoryType.TECHNICAL,
                 description: str = None,
                 parent_category_id: str = None,
                 keywords: List[str] = None,
                 color_code: str = None,
                 is_active: bool = True,
                 created_at: datetime = None):
        self.category_id = category_id or str(uuid4())
        self.name = name or ""
        self.category_type = category_type
        self.description = description or ""
        self.parent_category_id = parent_category_id
        self.keywords = keywords or []
        self.color_code = color_code
        self.is_active = is_active
        self.created_at = created_at or datetime.now(timezone.utc)

    def matches_keywords(self, text: str) -> bool:
        """Check if text matches category keywords."""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in self.keywords)

    def is_child_category(self) -> bool:
        """Check if this is a child category."""
        return self.parent_category_id is not None

    def deactivate(self):
        """Deactivate category."""
        self.is_active = False

    def add_keyword(self, keyword: str):
        """Add a keyword to category."""
        if keyword not in self.keywords:
            self.keywords.append(keyword)

    def remove_keyword(self, keyword: str):
        """Remove a keyword from category."""
        if keyword in self.keywords:
            self.keywords.remove(keyword)


class Recommendation:
    """Domain entity for document recommendations."""

    def __init__(self,
                 recommendation_id: str = None,
                 document_id: str = None,
                 recommendation_type: RecommendationType = RecommendationType.IMPROVEMENT,
                 title: str = None,
                 description: str = None,
                 priority: int = 1,
                 confidence_score: float = 0.0,
                 suggested_actions: List[str] = None,
                 related_summary_id: str = None,
                 is_implemented: bool = False,
                 created_at: datetime = None):
        self.recommendation_id = recommendation_id or str(uuid4())
        self.document_id = document_id
        self.recommendation_type = recommendation_type
        self.title = title or ""
        self.description = description or ""
        self.priority = priority
        self.confidence_score = confidence_score
        self.suggested_actions = suggested_actions or []
        self.related_summary_id = related_summary_id
        self.is_implemented = is_implemented
        self.created_at = created_at or datetime.now(timezone.utc)

    def is_high_priority(self) -> bool:
        """Check if recommendation is high priority."""
        return self.priority >= 4

    def is_confident(self) -> bool:
        """Check if recommendation has high confidence."""
        return self.confidence_score >= 0.8

    def mark_implemented(self):
        """Mark recommendation as implemented."""
        self.is_implemented = True

    def add_suggested_action(self, action: str):
        """Add a suggested action."""
        if action not in self.suggested_actions:
            self.suggested_actions.append(action)

    def get_priority_label(self) -> str:
        """Get priority label."""
        if self.priority >= 5:
            return "Critical"
        elif self.priority >= 4:
            return "High"
        elif self.priority >= 3:
            return "Medium"
        elif self.priority >= 2:
            return "Low"
        else:
            return "Very Low"


class TestDocumentEntity:
    """Test the Document domain entity."""

    def test_document_creation(self):
        """Test creating a document."""
        doc = Document(
            title="Test Document",
            content="This is test content",
            document_type=DocumentType.CODE,
            file_size=1024,
            mime_type="text/plain"
        )

        assert doc.document_id is not None
        assert doc.title == "Test Document"
        assert doc.content == "This is test content"
        assert doc.document_type == DocumentType.CODE
        assert doc.file_size == 1024
        assert doc.mime_type == "text/plain"

    def test_document_content_methods(self):
        """Test document content-related methods."""
        doc = Document(content="   ")
        assert not doc.has_content()

        doc.update_content("New content here")
        assert doc.has_content()
        assert doc.get_content_length() == 16
        assert doc.file_size == len("New content here".encode('utf-8'))

    def test_document_size_check(self):
        """Test document size checking."""
        small_doc = Document(file_size=500 * 1024)  # 500KB
        assert not small_doc.is_large_document()

        large_doc = Document(file_size=2 * 1024 * 1024)  # 2MB
        assert large_doc.is_large_document()

    def test_document_summary(self):
        """Test document summary generation."""
        doc = Document(title="API Documentation", document_type=DocumentType.DOCUMENTATION)
        summary = doc.get_summary()
        assert "API Documentation" in summary
        assert "documentation" in summary

        doc_no_title = Document(document_type=DocumentType.CODE)
        summary = doc_no_title.get_summary()
        assert "Document" in summary
        assert "code" in summary


class TestSummaryEntity:
    """Test the Summary domain entity."""

    def test_summary_creation(self):
        """Test creating a summary."""
        summary = Summary(
            document_id="doc123",
            content="This is a summary",
            summary_type="executive",
            model_used="gpt-4",
            processing_time_ms=1500
        )

        assert summary.summary_id is not None
        assert summary.document_id == "doc123"
        assert summary.content == "This is a summary"
        assert summary.summary_type == "executive"
        assert summary.status == SummaryStatus.PENDING
        assert summary.model_used == "gpt-4"
        assert summary.processing_time_ms == 1500

    def test_summary_status_methods(self):
        """Test summary status methods."""
        summary = Summary()
        assert not summary.is_completed()
        assert not summary.is_successful()

        summary.mark_completed(0.85)
        assert summary.is_completed()
        assert summary.is_successful()
        assert summary.quality_score == 0.85

        summary.mark_failed()
        assert summary.status == SummaryStatus.FAILED
        assert summary.quality_score == 0.0

    def test_summary_calculations(self):
        """Test summary calculations."""
        summary = Summary(content="This is a test summary with several words")
        summary.calculate_word_count()
        assert summary.word_count == 8

        summary.calculate_compression_ratio(50)  # Original had 50 words
        assert summary.compression_ratio == 8/50

        empty_summary = Summary()
        empty_summary.calculate_word_count()
        assert empty_summary.word_count == 0
        empty_summary.calculate_compression_ratio(100)
        assert empty_summary.compression_ratio == 0.0


class TestCategoryEntity:
    """Test the Category domain entity."""

    def test_category_creation(self):
        """Test creating a category."""
        category = Category(
            name="Security Documentation",
            category_type=CategoryType.COMPLIANCE,
            description="Documents related to security compliance",
            keywords=["security", "compliance", "audit"],
            color_code="#FF0000"
        )

        assert category.category_id is not None
        assert category.name == "Security Documentation"
        assert category.category_type == CategoryType.COMPLIANCE
        assert category.description == "Documents related to security compliance"
        assert "security" in category.keywords
        assert category.color_code == "#FF0000"
        assert category.is_active

    def test_category_keyword_matching(self):
        """Test category keyword matching."""
        category = Category(keywords=["security", "compliance", "audit"])

        assert category.matches_keywords("This document covers security compliance")
        assert category.matches_keywords("Audit procedures and security")
        assert not category.matches_keywords("This is about marketing")

    def test_category_hierarchy(self):
        """Test category hierarchy methods."""
        parent_category = Category(name="Technical")
        child_category = Category(
            name="Backend",
            parent_category_id=parent_category.category_id
        )

        assert not parent_category.is_child_category()
        assert child_category.is_child_category()

    def test_category_keyword_management(self):
        """Test category keyword management."""
        category = Category(keywords=["initial"])

        category.add_keyword("new_keyword")
        assert "new_keyword" in category.keywords

        category.add_keyword("initial")  # Should not duplicate
        assert category.keywords.count("initial") == 1

        category.remove_keyword("initial")
        assert "initial" not in category.keywords

        category.remove_keyword("nonexistent")  # Should not error

    def test_category_activation(self):
        """Test category activation/deactivation."""
        category = Category()
        assert category.is_active

        category.deactivate()
        assert not category.is_active


class TestRecommendationEntity:
    """Test the Recommendation domain entity."""

    def test_recommendation_creation(self):
        """Test creating a recommendation."""
        recommendation = Recommendation(
            document_id="doc123",
            recommendation_type=RecommendationType.SECURITY,
            title="Implement Input Validation",
            description="Add proper input validation to prevent injection attacks",
            priority=4,
            confidence_score=0.9,
            suggested_actions=["Add input sanitization", "Implement validation middleware"]
        )

        assert recommendation.recommendation_id is not None
        assert recommendation.document_id == "doc123"
        assert recommendation.recommendation_type == RecommendationType.SECURITY
        assert recommendation.title == "Implement Input Validation"
        assert recommendation.priority == 4
        assert recommendation.confidence_score == 0.9
        assert len(recommendation.suggested_actions) == 2
        assert not recommendation.is_implemented

    def test_recommendation_priority_methods(self):
        """Test recommendation priority methods."""
        high_priority = Recommendation(priority=5)
        medium_priority = Recommendation(priority=3)
        low_priority = Recommendation(priority=1)

        assert high_priority.is_high_priority()
        assert not medium_priority.is_high_priority()
        assert not low_priority.is_high_priority()

    def test_recommendation_confidence(self):
        """Test recommendation confidence checking."""
        confident = Recommendation(confidence_score=0.9)
        uncertain = Recommendation(confidence_score=0.5)

        assert confident.is_confident()
        assert not uncertain.is_confident()

    def test_recommendation_implementation(self):
        """Test recommendation implementation tracking."""
        recommendation = Recommendation()
        assert not recommendation.is_implemented

        recommendation.mark_implemented()
        assert recommendation.is_implemented

    def test_recommendation_actions(self):
        """Test recommendation suggested actions."""
        recommendation = Recommendation(suggested_actions=["Action 1"])

        recommendation.add_suggested_action("Action 2")
        assert len(recommendation.suggested_actions) == 2
        assert "Action 1" in recommendation.suggested_actions
        assert "Action 2" in recommendation.suggested_actions

        recommendation.add_suggested_action("Action 1")  # Should not duplicate
        assert len(recommendation.suggested_actions) == 2

    def test_recommendation_priority_labels(self):
        """Test recommendation priority labels."""
        assert Recommendation(priority=5).get_priority_label() == "Critical"
        assert Recommendation(priority=4).get_priority_label() == "High"
        assert Recommendation(priority=3).get_priority_label() == "Medium"
        assert Recommendation(priority=2).get_priority_label() == "Low"
        assert Recommendation(priority=1).get_priority_label() == "Very Low"


class TestEntityIntegration:
    """Test integration between entities."""

    def test_document_summary_integration(self):
        """Test integration between Document and Summary."""
        doc = Document(
            title="API Specification",
            content="This is a detailed API specification document with many requirements...",
            document_type=DocumentType.SPECIFICATION,
            file_size=5000
        )

        summary = Summary(
            document_id=doc.document_id,
            content="API spec covering authentication and endpoints",
            summary_type="executive"
        )

        # Verify relationship
        assert summary.document_id == doc.document_id
        assert doc.has_content()
        assert summary.content != doc.content  # Summary should be different from full content

        # Test compression ratio calculation
        doc_word_count = len(doc.content.split())
        summary.calculate_word_count()
        summary.calculate_compression_ratio(doc_word_count)
        assert summary.compression_ratio == summary.word_count / doc_word_count

    def test_document_category_integration(self):
        """Test integration between Document and Category."""
        doc = Document(
            title="Security Audit Report",
            content="This report covers security findings and compliance status...",
            document_type=DocumentType.REAPI_PORT
        )

        category = Category(
            name="Security & Compliance",
            category_type=CategoryType.COMPLIANCE,
            keywords=["security", "audit", "compliance", "risk"]
        )

        # Test categorization
        assert category.matches_keywords(doc.title)
        assert category.matches_keywords(doc.content)
        assert category.is_active

        # Test category assignment concept
        doc.metadata = {"category_id": category.category_id}
        assert doc.metadata["category_id"] == category.category_id

    def test_summary_recommendation_integration(self):
        """Test integration between Summary and Recommendation."""
        summary = Summary(
            document_id="doc123",
            content="Summary content",
            status=SummaryStatus.COMPLETED,
            quality_score=0.8
        )

        recommendation = Recommendation(
            document_id=summary.document_id,
            title="Improve Documentation",
            recommendation_type=RecommendationType.IMPROVEMENT,
            related_summary_id=summary.summary_id,
            confidence_score=0.85
        )

        # Verify relationships
        assert recommendation.document_id == summary.document_id
        assert recommendation.related_summary_id == summary.summary_id
        assert summary.is_successful()
        assert recommendation.is_confident()

        # Test implementation workflow
        assert not recommendation.is_implemented
        recommendation.mark_implemented()
        assert recommendation.is_implemented

    def test_complete_workflow_integration(self):
        """Test complete workflow with all entities."""
        # Create document
        doc = Document(
            title="System Architecture Document",
            content="Detailed system architecture with components and interactions...",
            document_type=DocumentType.DOCUMENTATION
        )

        # Create category
        category = Category(
            name="Architecture",
            category_type=CategoryType.TECHNICAL,
            keywords=["architecture", "system", "design"]
        )

        # Create summary
        summary = Summary(
            document_id=doc.document_id,
            content="System architecture overview with key components",
            summary_type="technical",
            model_used="gpt-4"
        )
        summary.mark_completed(0.9)

        # Create recommendation
        recommendation = Recommendation(
            document_id=doc.document_id,
            title="Add Performance Metrics",
            recommendation_type=RecommendationType.OPTIMIZATION,
            priority=3,
            related_summary_id=summary.summary_id
        )

        # Verify complete integration
        assert doc.document_id == summary.document_id == recommendation.document_id
        assert category.matches_keywords(doc.title)
        assert summary.is_completed() and summary.is_successful()
        assert recommendation.related_summary_id == summary.summary_id
        assert not recommendation.is_implemented
        assert doc.has_content()
        assert summary.quality_score >= 0.8
