"""Unit Tests for Value Objects - Domain Driven Design Foundation.

This module contains comprehensive unit tests for value objects,
testing immutability, validation, equality, and business rules.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from simulation.domain.value_objects import (
    EmailAddress, ProjectName, Duration, Money, Percentage,
    ServiceEndpoint, ServiceHealthStatus, DocumentId, DocumentMetadata,
    SimulationMetrics, EcosystemService, ProjectType, ComplexityLevel,
    ProjectStatus, SimulationStatus, DocumentType, ServiceHealth
)


class TestEmailAddress:
    """Test cases for EmailAddress value object."""

    def test_valid_email_creation(self):
        """Test creating valid email addresses."""
        email = EmailAddress("user@example.com")
        assert email.value == "user@example.com"
        assert email.domain == "example.com"
        assert email.local_part == "user"

    def test_invalid_email_creation(self):
        """Test that invalid emails raise ValueError."""
        with pytest.raises(ValueError, match="Invalid email address"):
            EmailAddress("invalid-email")

        with pytest.raises(ValueError, match="Invalid email address"):
            EmailAddress("user@")

        with pytest.raises(ValueError, match="Invalid email address"):
            EmailAddress("@example.com")

    def test_email_too_long(self):
        """Test that overly long emails are rejected."""
        long_email = "a" * 250 + "@example.com"  # 264 characters total
        with pytest.raises(ValueError, match="Email address too long"):
            EmailAddress(long_email)

    def test_email_equality(self):
        """Test email equality comparison."""
        email1a = EmailAddress("user@example.com")
        email1b = EmailAddress("user@example.com")
        email2 = EmailAddress("other@example.com")

        assert email1a == email1b
        assert email1a != email2

    def test_email_immutability(self):
        """Test that EmailAddress is immutable."""
        email = EmailAddress("user@example.com")

        # Should not be able to modify attributes
        with pytest.raises(AttributeError):
            email.value = "new@example.com"


class TestProjectName:
    """Test cases for ProjectName value object."""

    def test_valid_project_name(self):
        """Test creating valid project names."""
        name = ProjectName("My Awesome Project")
        assert name.value == "My Awesome Project"
        assert name.slug() == "my-awesome-project"

    def test_empty_project_name(self):
        """Test that empty project names are rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            ProjectName("")

        with pytest.raises(ValueError, match="cannot be empty"):
            ProjectName("   ")

    def test_project_name_too_long(self):
        """Test that overly long project names are rejected."""
        long_name = "A" * 101  # 101 characters
        with pytest.raises(ValueError, match="too long"):
            ProjectName(long_name)

    def test_invalid_characters_in_project_name(self):
        """Test that invalid characters are rejected."""
        with pytest.raises(ValueError, match="invalid characters"):
            ProjectName("Project@Name")

        with pytest.raises(ValueError, match="invalid characters"):
            ProjectName("Project#Name")

    def test_valid_special_characters(self):
        """Test that valid special characters are allowed."""
        # Spaces, hyphens, and underscores should be valid
        name1 = ProjectName("Project Name")
        name2 = ProjectName("Project-Name")
        name3 = ProjectName("Project_Name")
        name4 = ProjectName("Project Name_123")

        assert name1.value == "Project Name"
        assert name2.value == "Project-Name"
        assert name3.value == "Project_Name"
        assert name4.value == "Project Name_123"

    def test_project_name_slug_conversion(self):
        """Test URL slug conversion."""
        test_cases = [
            ("My Project", "my-project"),
            ("Project_With_Underscores", "project_with_underscores"),
            ("Project With Spaces", "project-with-spaces"),
            ("MIXED_case_PROJECT", "mixed_case_project"),
            ("Project---Multiple---Dashes", "project---multiple---dashes")
        ]

        for input_name, expected_slug in test_cases:
            name = ProjectName(input_name)
            assert name.slug() == expected_slug


class TestDuration:
    """Test cases for Duration value object."""

    def test_valid_duration_creation(self):
        """Test creating valid durations."""
        duration = Duration(weeks=2, days=3)
        assert duration.weeks == 2
        assert duration.days == 3
        assert duration.total_days == 17  # 2*7 + 3
        assert abs(duration.total_weeks - 2.4285714285714288) < 1e-10  # 17/7

    def test_duration_negative_values(self):
        """Test that negative durations are rejected."""
        with pytest.raises(ValueError, match="cannot be negative"):
            Duration(weeks=-1, days=0)

        with pytest.raises(ValueError, match="cannot be negative"):
            Duration(weeks=0, days=-1)

    def test_duration_days_too_large(self):
        """Test that days >= 7 are rejected."""
        with pytest.raises(ValueError, match="should be less than 7"):
            Duration(weeks=1, days=7)

        with pytest.raises(ValueError, match="should be less than 7"):
            Duration(weeks=0, days=10)

    def test_duration_addition(self):
        """Test duration addition."""
        d1 = Duration(weeks=1, days=2)
        d2 = Duration(weeks=0, days=5)

        # d1 = 1 week + 2 days = 9 days
        # d2 = 0 weeks + 5 days = 5 days
        # Total = 9 + 5 = 14 days = 2 weeks + 0 days

        result = d1 + d2
        assert result.weeks == 2
        assert result.days == 0  # 14 days = 2 weeks exactly

    def test_duration_string_representation(self):
        """Test duration string formatting."""
        test_cases = [
            (Duration(weeks=0, days=1), "1 day"),
            (Duration(weeks=0, days=5), "5 days"),
            (Duration(weeks=1, days=0), "1 week"),
            (Duration(weeks=2, days=0), "2 weeks"),
            (Duration(weeks=1, days=1), "1 week 1 day"),
            (Duration(weeks=2, days=3), "2 weeks 3 days")
        ]

        for duration, expected_str in test_cases:
            assert str(duration) == expected_str

    def test_duration_immutability(self):
        """Test that Duration is immutable."""
        duration = Duration(weeks=1, days=2)

        with pytest.raises(AttributeError):
            duration.weeks = 2

        with pytest.raises(AttributeError):
            duration.days = 3


class TestMoney:
    """Test cases for Money value object."""

    def test_valid_money_creation(self):
        """Test creating valid money amounts."""
        money = Money(amount=100.50, currency="USD")
        assert money.amount == 100.50
        assert money.currency == "USD"

    def test_money_negative_amount(self):
        """Test that negative amounts are rejected."""
        with pytest.raises(ValueError, match="cannot be negative"):
            Money(amount=-10.0, currency="USD")

    def test_money_unsupported_currency(self):
        """Test that unsupported currencies are rejected."""
        with pytest.raises(ValueError, match="Unsupported currency"):
            Money(amount=100.0, currency="BTC")

    def test_money_supported_currencies(self):
        """Test supported currencies."""
        for currency in ["USD", "EUR", "GBP"]:
            money = Money(amount=100.0, currency=currency)
            assert money.currency == currency

    def test_money_addition(self):
        """Test money addition."""
        money1 = Money(amount=100.0, currency="USD")
        money2 = Money(amount=50.0, currency="USD")

        result = money1 + money2
        assert result.amount == 150.0
        assert result.currency == "USD"

    def test_money_addition_different_currencies(self):
        """Test that adding different currencies raises error."""
        money1 = Money(amount=100.0, currency="USD")
        money2 = Money(amount=50.0, currency="EUR")

        with pytest.raises(ValueError, match="different currencies"):
            money1 + money2

    def test_money_multiplication(self):
        """Test money multiplication."""
        money = Money(amount=100.0, currency="USD")
        result = money * 1.5
        assert result.amount == 150.0
        assert result.currency == "USD"

    def test_money_string_representation(self):
        """Test money string formatting."""
        money = Money(amount=1234.56, currency="USD")
        assert str(money) == "USD 1,234.56"

    def test_money_immutability(self):
        """Test that Money is immutable."""
        money = Money(amount=100.0, currency="USD")

        with pytest.raises(AttributeError):
            money.amount = 200.0

        with pytest.raises(AttributeError):
            money.currency = "EUR"


class TestPercentage:
    """Test cases for Percentage value object."""

    def test_valid_percentage_creation(self):
        """Test creating valid percentages."""
        percentage = Percentage(value=75.5)
        assert percentage.value == 75.5

    def test_percentage_out_of_range(self):
        """Test that percentages outside 0-100 are rejected."""
        with pytest.raises(ValueError, match="between 0 and 100"):
            Percentage(value=-5.0)

        with pytest.raises(ValueError, match="between 0 and 100"):
            Percentage(value=105.0)

    def test_percentage_boundary_values(self):
        """Test boundary values."""
        zero_percent = Percentage(value=0.0)
        assert zero_percent.value == 0.0

        hundred_percent = Percentage(value=100.0)
        assert hundred_percent.value == 100.0

    def test_percentage_from_fraction(self):
        """Test creating percentage from fraction."""
        percentage = Percentage.from_fraction(1, 4)  # 1/4 = 25%
        assert percentage.value == 25.0

    def test_percentage_from_fraction_zero_denominator(self):
        """Test that zero denominator raises error."""
        with pytest.raises(ValueError, match="cannot be zero"):
            Percentage.from_fraction(1, 0)

    def test_percentage_to_fraction(self):
        """Test converting percentage to fraction."""
        percentage = Percentage(value=50.0)
        assert percentage.to_fraction() == 0.5

    def test_percentage_string_representation(self):
        """Test percentage string formatting."""
        percentage = Percentage(value=75.25)
        assert str(percentage) == "75.2%"  # Banker's rounding: 75.25 rounds to 75.2

    def test_percentage_immutability(self):
        """Test that Percentage is immutable."""
        percentage = Percentage(value=50.0)

        with pytest.raises(AttributeError):
            percentage.value = 75.0


class TestServiceEndpoint:
    """Test cases for ServiceEndpoint value object."""

    def test_valid_service_endpoint_creation(self):
        """Test creating valid service endpoints."""
        endpoint = ServiceEndpoint(
            url="https://api.example.com",
            timeout_seconds=30,
            retries=3
        )

        assert endpoint.url == "https://api.example.com"
        assert endpoint.timeout_seconds == 30
        assert endpoint.retries == 3
        assert endpoint.base_url == "https://api.example.com"
        assert endpoint.is_https == True

    def test_invalid_url_scheme(self):
        """Test that invalid URL schemes are rejected."""
        with pytest.raises(ValueError, match="must start with"):
            ServiceEndpoint(url="ftp://example.com")

    def test_invalid_timeout(self):
        """Test that invalid timeout values are rejected."""
        with pytest.raises(ValueError, match="must be positive"):
            ServiceEndpoint(url="https://api.example.com", timeout_seconds=0)

        with pytest.raises(ValueError, match="must be positive"):
            ServiceEndpoint(url="https://api.example.com", timeout_seconds=-5)

    def test_invalid_retries(self):
        """Test that invalid retry values are rejected."""
        with pytest.raises(ValueError, match="cannot be negative"):
            ServiceEndpoint(url="https://api.example.com", retries=-1)

    def test_http_url(self):
        """Test HTTP URLs."""
        endpoint = ServiceEndpoint(url="http://api.example.com")
        assert endpoint.is_https == False
        assert endpoint.base_url == "http://api.example.com"

    def test_url_with_path_and_query(self):
        """Test URLs with paths and query parameters."""
        endpoint = ServiceEndpoint(url="https://api.example.com/v1/users?limit=10")
        assert endpoint.base_url == "https://api.example.com"


class TestServiceHealthStatus:
    """Test cases for ServiceHealthStatus value object."""

    def test_service_health_status_creation(self):
        """Test creating service health status."""
        status = ServiceHealthStatus(
            service_name="api",
            status=ServiceHealth.HEALTHY,
            response_time_ms=150.5,
            last_checked=datetime(2024, 1, 1, 12, 0, 0),
            error_message=None
        )

        assert status.service_name == "api"
        assert status.status == ServiceHealth.HEALTHY
        assert status.response_time_ms == 150.5
        assert status.is_healthy() == True
        assert status.needs_attention() == False

    def test_service_health_degraded_status(self):
        """Test degraded service status."""
        status = ServiceHealthStatus(
            service_name="api",
            status=ServiceHealth.DEGRADED,
            response_time_ms=5000.0
        )

        assert status.is_healthy() == False
        assert status.needs_attention() == True

    def test_service_health_unhealthy_status(self):
        """Test unhealthy service status."""
        status = ServiceHealthStatus(
            service_name="api",
            status=ServiceHealth.UNHEALTHY,
            error_message="Connection timeout"
        )

        assert status.is_healthy() == False
        assert status.needs_attention() == True

    def test_service_health_unknown_status(self):
        """Test unknown service status."""
        status = ServiceHealthStatus(
            service_name="api",
            status=ServiceHealth.UNKNOWN
        )

        assert status.is_healthy() == False
        assert status.needs_attention() == False


class TestDocumentId:
    """Test cases for DocumentId value object."""

    def test_document_id_creation(self):
        """Test creating document IDs."""
        doc_id = DocumentId("doc-12345")
        assert doc_id.value == "doc-12345"

    def test_empty_document_id(self):
        """Test that empty document IDs are rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            DocumentId("")

        with pytest.raises(ValueError, match="cannot be empty"):
            DocumentId("   ")

    def test_document_id_generate(self):
        """Test generating new document IDs."""
        doc_id1 = DocumentId.generate()
        doc_id2 = DocumentId.generate()

        assert doc_id1 != doc_id2  # Should be unique
        assert len(doc_id1.value) > 0
        assert len(doc_id2.value) > 0

    def test_document_id_string_representation(self):
        """Test document ID string representation."""
        doc_id = DocumentId("doc-12345")
        assert str(doc_id) == "doc-12345"


class TestDocumentMetadata:
    """Test cases for DocumentMetadata value object."""

    def test_valid_document_metadata_creation(self):
        """Test creating valid document metadata."""
        doc_id = DocumentId("doc-123")
        created_at = datetime(2024, 1, 1, 10, 0, 0)

        metadata = DocumentMetadata(
            document_id=doc_id,
            title="API Documentation",
            type=DocumentType.TECHNICAL_DESIGN,
            author="John Doe",
            created_at=created_at,
            word_count=1500,
            complexity_score=0.7,
            tags=["api", "documentation", "technical"]
        )

        assert metadata.document_id == doc_id
        assert metadata.title == "API Documentation"
        assert metadata.type == DocumentType.TECHNICAL_DESIGN
        assert metadata.author == "John Doe"
        assert metadata.created_at == created_at
        assert metadata.word_count == 1500
        assert metadata.complexity_score == 0.7
        assert metadata.tags == ["api", "documentation", "technical"]
        assert metadata.age_days == (datetime.now() - created_at).days

    def test_empty_document_title(self):
        """Test that empty document titles are rejected."""
        doc_id = DocumentId("doc-123")

        with pytest.raises(ValueError, match="cannot be empty"):
            DocumentMetadata(
                document_id=doc_id,
                title="",
                type=DocumentType.PROJECT_REQUIREMENTS,
                author="John Doe",
                created_at=datetime.now()
            )

    def test_negative_word_count(self):
        """Test that negative word counts are rejected."""
        doc_id = DocumentId("doc-123")

        with pytest.raises(ValueError, match="cannot be negative"):
            DocumentMetadata(
                document_id=doc_id,
                title="Test Document",
                type=DocumentType.PROJECT_REQUIREMENTS,
                author="John Doe",
                created_at=datetime.now(),
                word_count=-100
            )

    def test_invalid_complexity_score(self):
        """Test that invalid complexity scores are rejected."""
        doc_id = DocumentId("doc-123")

        with pytest.raises(ValueError, match="between 0 and 1"):
            DocumentMetadata(
                document_id=doc_id,
                title="Test Document",
                type=DocumentType.PROJECT_REQUIREMENTS,
                author="John Doe",
                created_at=datetime.now(),
                complexity_score=1.5
            )

        with pytest.raises(ValueError, match="between 0 and 1"):
            DocumentMetadata(
                document_id=doc_id,
                title="Test Document",
                type=DocumentType.PROJECT_REQUIREMENTS,
                author="John Doe",
                created_at=datetime.now(),
                complexity_score=-0.1
            )

    def test_tag_matching(self):
        """Test tag matching functionality."""
        doc_id = DocumentId("doc-123")

        metadata = DocumentMetadata(
            document_id=doc_id,
            title="Test Document",
            type=DocumentType.PROJECT_REQUIREMENTS,
            author="John Doe",
            created_at=datetime.now(),
            tags=["API", "documentation", "TECHNICAL"]
        )

        # Should be case-insensitive
        assert metadata.matches_tag("api") == True
        assert metadata.matches_tag("API") == True
        assert metadata.matches_tag("documentation") == True
        assert metadata.matches_tag("technical") == True
        assert metadata.matches_tag("unknown") == False


class TestSimulationMetrics:
    """Test cases for SimulationMetrics value object."""

    def test_simulation_metrics_creation(self):
        """Test creating simulation metrics."""
        metrics = SimulationMetrics(
            total_documents=100,
            total_tickets=50,
            total_prs=25,
            total_workflows=10,
            execution_time_seconds=300.5,
            average_response_time_ms=150.0,
            error_count=2,
            success_rate=Percentage(96.0)
        )

        assert metrics.total_documents == 100
        assert metrics.execution_time_seconds == 300.5
        assert metrics.documents_per_second == 100 / 300.5
        assert abs(metrics.workflows_per_minute - ((10 / 300.5) * 60)) < 1e-10

    def test_simulation_metrics_zero_execution_time(self):
        """Test metrics calculation with zero execution time."""
        metrics = SimulationMetrics(
            total_documents=0,
            total_tickets=0,
            total_prs=0,
            total_workflows=0,
            execution_time_seconds=0,
            average_response_time_ms=0.0,
            error_count=0,
            success_rate=Percentage(100.0)
        )

        assert metrics.documents_per_second == 0
        assert metrics.workflows_per_minute == 0

    def test_simulation_metrics_string_representation(self):
        """Test metrics string representation."""
        metrics = SimulationMetrics(
            total_documents=100,
            total_tickets=50,
            total_prs=25,
            total_workflows=10,
            execution_time_seconds=300.0,
            average_response_time_ms=150.0,
            error_count=2,
            success_rate=Percentage(96.0)
        )

        str_repr = str(metrics)
        assert "docs=100" in str_repr
        assert "workflows=10" in str_repr
        assert "time=300.0s" in str_repr
        assert "success=" in str_repr


class TestEcosystemService:
    """Test cases for EcosystemService value object."""

    def test_ecosystem_service_creation(self):
        """Test creating ecosystem service."""
        endpoint = ServiceEndpoint("https://api.example.com")
        service = EcosystemService(
            name="test_api",
            endpoint=endpoint,
            health_check_endpoint="/health",
            required_for_simulation=True,
            description="Test API service"
        )

        assert service.name == "test_api"
        assert service.endpoint == endpoint
        assert service.health_check_endpoint == "/health"
        assert service.required_for_simulation == True
        assert service.description == "Test API service"

    def test_ecosystem_service_health_check_url(self):
        """Test health check URL generation."""
        endpoint = ServiceEndpoint("https://api.example.com/v1")
        service = EcosystemService(
            name="test_api",
            endpoint=endpoint,
            health_check_endpoint="health"
        )

        expected_url = "https://api.example.com/health"
        assert service.get_health_check_url() == expected_url

    def test_ecosystem_service_string_representation(self):
        """Test service string representation."""
        endpoint = ServiceEndpoint("https://api.example.com")
        service = EcosystemService(
            name="test_api",
            endpoint=endpoint
        )

        str_repr = str(service)
        assert "test_api" in str_repr
        assert "https://api.example.com" in str_repr


class TestEnums:
    """Test cases for enum value objects."""

    def test_project_type_enum(self):
        """Test ProjectType enum values."""
        assert ProjectType.WEB_APPLICATION.value == "web_application"
        assert ProjectType.API_SERVICE.value == "api_service"
        assert ProjectType.MOBILE_APPLICATION.value == "mobile_application"
        assert ProjectType.MICROSERVICES.value == "microservices"
        assert ProjectType.DATA_PIPELINE.value == "data_pipeline"
        assert ProjectType.MACHINE_LEARNING.value == "machine_learning"

    def test_complexity_level_enum(self):
        """Test ComplexityLevel enum values."""
        assert ComplexityLevel.SIMPLE.value == "simple"
        assert ComplexityLevel.MEDIUM.value == "medium"
        assert ComplexityLevel.COMPLEX.value == "complex"

    def test_project_status_enum(self):
        """Test ProjectStatus enum values."""
        assert ProjectStatus.CREATED.value == "created"
        assert ProjectStatus.PLANNING.value == "planning"
        assert ProjectStatus.IN_PROGRESS.value == "in_progress"
        assert ProjectStatus.ON_HOLD.value == "on_hold"
        assert ProjectStatus.COMPLETED.value == "completed"
        assert ProjectStatus.CANCELLED.value == "cancelled"

    def test_simulation_status_enum(self):
        """Test SimulationStatus enum values."""
        assert SimulationStatus.CREATED.value == "created"
        assert SimulationStatus.STARTING.value == "starting"
        assert SimulationStatus.RUNNING.value == "running"
        assert SimulationStatus.PAUSED.value == "paused"
        assert SimulationStatus.COMPLETED.value == "completed"
        assert SimulationStatus.FAILED.value == "failed"
        assert SimulationStatus.CANCELLED.value == "cancelled"

    def test_document_type_enum(self):
        """Test DocumentType enum values."""
        assert DocumentType.PROJECT_REQUIREMENTS.value == "project_requirements"
        assert DocumentType.ARCHITECTURE_DIAGRAM.value == "architecture_diagram"
        assert DocumentType.USER_STORY.value == "user_story"
        assert DocumentType.TECHNICAL_DESIGN.value == "technical_design"
        assert DocumentType.CODE_REVIEW_COMMENTS.value == "code_review_comments"
        assert DocumentType.TEST_SCENARIOS.value == "test_scenarios"
        assert DocumentType.DEPLOYMENT_GUIDE.value == "deployment_guide"
        assert DocumentType.MAINTENANCE_DOCS.value == "maintenance_docs"
        assert DocumentType.CHANGE_LOG.value == "change_log"
        assert DocumentType.TEAM_RETROSPECTIVE.value == "team_retrospective"

    def test_service_health_enum(self):
        """Test ServiceHealth enum values."""
        assert ServiceHealth.HEALTHY.value == "healthy"
        assert ServiceHealth.DEGRADED.value == "degraded"
        assert ServiceHealth.UNHEALTHY.value == "unhealthy"
        assert ServiceHealth.UNKNOWN.value == "unknown"
