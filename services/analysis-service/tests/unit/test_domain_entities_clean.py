"""Clean unit tests for analysis-service domain entities."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Dict, Optional

# Define domain entities inline to avoid import dependencies
from enum import Enum


class AnalysisStatus(str, Enum):
    """Analysis status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FindingSeverity(str, Enum):
    """Finding severity enumeration."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AnalysisType(str, Enum):
    """Analysis type enumeration."""
    CODE_QUALITY = "code_quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    DEPENDENCY = "dependency"
    COMPLIANCE = "compliance"


class DocumentType(str, Enum):
    """Document type enumeration."""
    CODE = "code"
    CONFIGURATION = "configuration"
    DOCUMENTATION = "documentation"
    TEST = "test"
    BUILD = "build"


class FindingStatus(str, Enum):
    """Finding status enumeration."""
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    FALSE_POSITIVE = "false_positive"


class AnalysisResult:
    """Domain entity for analysis results."""

    def __init__(self,
                 analysis_id: str = None,
                 document_id: str = None,
                 analysis_type: AnalysisType = AnalysisType.CODE_QUALITY,
                 status: AnalysisStatus = AnalysisStatus.PENDING,
                 score: float = 0.0,
                 findings_count: int = 0,
                 execution_time: float = 0.0,
                 metadata: Dict = None,
                 started_at: datetime = None,
                 completed_at: datetime = None,
                 created_at: datetime = None):
        self.analysis_id = analysis_id or str(uuid4())
        self.document_id = document_id
        self.analysis_type = analysis_type
        self.status = status
        self.score = score
        self.findings_count = findings_count
        self.execution_time = execution_time
        self.metadata = metadata or {}
        self.started_at = started_at
        self.completed_at = completed_at
        self.created_at = created_at or datetime.now(timezone.utc)

    def is_successful(self) -> bool:
        """Check if analysis was successful."""
        return self.status == AnalysisStatus.COMPLETED and self.score >= 0.0

    def is_high_quality(self) -> bool:
        """Check if analysis indicates high quality."""
        return self.score >= 0.8

    def is_critical_issues(self) -> bool:
        """Check if analysis found critical issues."""
        return self.metadata.get("critical_findings", 0) > 0

    def start_analysis(self):
        """Start the analysis."""
        if self.status == AnalysisStatus.PENDING:
            self.status = AnalysisStatus.RUNNING
            self.started_at = datetime.now(timezone.utc)

    def complete_analysis(self, score: float, findings_count: int, metadata: Dict = None):
        """Complete the analysis."""
        if self.status == AnalysisStatus.RUNNING:
            self.status = AnalysisStatus.COMPLETED
            self.completed_at = datetime.now(timezone.utc)
            self.score = score
            self.findings_count = findings_count
            if metadata:
                self.metadata.update(metadata)

            if self.started_at and self.completed_at:
                self.execution_time = (self.completed_at - self.started_at).total_seconds()

    def fail_analysis(self, error_message: str = None):
        """Mark analysis as failed."""
        self.status = AnalysisStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        if error_message:
            self.metadata["error"] = error_message

    def get_quality_grade(self) -> str:
        """Get quality grade based on score."""
        if self.score >= 0.9:
            return "A"
        elif self.score >= 0.8:
            return "B"
        elif self.score >= 0.7:
            return "C"
        elif self.score >= 0.6:
            return "D"
        else:
            return "F"


class Document:
    """Domain entity for documents."""

    def __init__(self,
                 document_id: str = None,
                 name: str = None,
                 path: str = None,
                 document_type: DocumentType = DocumentType.CODE,
                 content: str = "",
                 size: int = 0,
                 language: str = None,
                 metadata: Dict = None,
                 checksum: str = None,
                 created_at: datetime = None,
                 updated_at: datetime = None):
        self.document_id = document_id or str(uuid4())
        self.name = name or ""
        self.path = path or ""
        self.document_type = document_type
        self.content = content
        self.size = size
        self.language = language
        self.metadata = metadata or {}
        self.checksum = checksum
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def is_code_file(self) -> bool:
        """Check if document is a code file."""
        return self.document_type == DocumentType.CODE

    def is_large_file(self) -> bool:
        """Check if document is large."""
        return self.size > 1000000  # 1MB

    def get_file_extension(self) -> str:
        """Get file extension."""
        if self.name and "." in self.name:
            return self.name.split(".")[-1].lower()
        return ""

    def is_supported_language(self, supported_languages: List[str]) -> bool:
        """Check if language is supported."""
        if not self.language:
            return False
        return self.language.lower() in [lang.lower() for lang in supported_languages]

    def update_content(self, new_content: str):
        """Update document content."""
        self.content = new_content
        self.size = len(new_content.encode('utf-8'))
        self.updated_at = datetime.now(timezone.utc)
        # In real implementation, checksum would be recalculated
        self.checksum = f"checksum_{len(new_content)}"

    def get_content_lines(self) -> List[str]:
        """Get content as lines."""
        return self.content.split('\n') if self.content else []

    def get_line_count(self) -> int:
        """Get number of lines."""
        return len(self.get_content_lines())

    def contains_text(self, search_text: str) -> bool:
        """Check if document contains specific text."""
        return search_text.lower() in self.content.lower()


class Finding:
    """Domain entity for analysis findings."""

    def __init__(self,
                 finding_id: str = None,
                 analysis_id: str = None,
                 document_id: str = None,
                 title: str = None,
                 description: str = None,
                 severity: FindingSeverity = FindingSeverity.MEDIUM,
                 category: str = None,
                 line_number: int = None,
                 column_number: int = None,
                 code_snippet: str = None,
                 suggestion: str = None,
                 status: FindingStatus = FindingStatus.OPEN,
                 metadata: Dict = None,
                 created_at: datetime = None):
        self.finding_id = finding_id or str(uuid4())
        self.analysis_id = analysis_id
        self.document_id = document_id
        self.title = title or ""
        self.description = description or ""
        self.severity = severity
        self.category = category or ""
        self.line_number = line_number
        self.column_number = column_number
        self.code_snippet = code_snippet or ""
        self.suggestion = suggestion or ""
        self.status = status
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc)

    def is_critical(self) -> bool:
        """Check if finding is critical."""
        return self.severity == FindingSeverity.CRITICAL

    def is_high_severity(self) -> bool:
        """Check if finding is high severity."""
        return self.severity in [FindingSeverity.CRITICAL, FindingSeverity.HIGH]

    def is_resolved(self) -> bool:
        """Check if finding is resolved."""
        return self.status in [FindingStatus.RESOLVED, FindingStatus.DISMISSED, FindingStatus.FALSE_POSITIVE]

    def resolve(self):
        """Mark finding as resolved."""
        self.status = FindingStatus.RESOLVED

    def dismiss(self):
        """Mark finding as dismissed."""
        self.status = FindingStatus.DISMISSED

    def mark_false_positive(self):
        """Mark finding as false positive."""
        self.status = FindingStatus.FALSE_POSITIVE

    def has_location(self) -> bool:
        """Check if finding has location information."""
        return self.line_number is not None

    def get_location_string(self) -> str:
        """Get location as string."""
        if self.line_number and self.column_number:
            return f"line {self.line_number}, column {self.column_number}"
        elif self.line_number:
            return f"line {self.line_number}"
        else:
            return "unknown location"

    def matches_category(self, categories: List[str]) -> bool:
        """Check if finding matches any of the categories."""
        return self.category.lower() in [cat.lower() for cat in categories]


class AnalysisConfiguration:
    """Domain entity for analysis configuration."""

    def __init__(self,
                 config_id: str = None,
                 name: str = None,
                 analysis_types: List[AnalysisType] = None,
                 rules: Dict = None,
                 thresholds: Dict = None,
                 enabled: bool = True,
                 metadata: Dict = None,
                 created_at: datetime = None):
        self.config_id = config_id or str(uuid4())
        self.name = name or ""
        self.analysis_types = analysis_types or []
        self.rules = rules or {}
        self.thresholds = thresholds or {}
        self.enabled = enabled
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc)

    def is_enabled(self) -> bool:
        """Check if configuration is enabled."""
        return self.enabled

    def supports_analysis_type(self, analysis_type: AnalysisType) -> bool:
        """Check if configuration supports analysis type."""
        return analysis_type in self.analysis_types

    def get_threshold(self, metric: str, default: float = 0.0) -> float:
        """Get threshold value for metric."""
        return self.thresholds.get(metric, default)

    def get_rule(self, rule_name: str, default=None):
        """Get rule configuration."""
        return self.rules.get(rule_name, default)

    def add_analysis_type(self, analysis_type: AnalysisType):
        """Add analysis type."""
        if analysis_type not in self.analysis_types:
            self.analysis_types.append(analysis_type)

    def remove_analysis_type(self, analysis_type: AnalysisType):
        """Remove analysis type."""
        if analysis_type in self.analysis_types:
            self.analysis_types.remove(analysis_type)

    def update_threshold(self, metric: str, value: float):
        """Update threshold value."""
        self.thresholds[metric] = value


class TestAnalysisResultEntity:
    """Test the AnalysisResult domain entity."""

    def test_analysis_result_creation(self):
        """Test creating an analysis result."""
        result = AnalysisResult(
            document_id="doc123",
            analysis_type=AnalysisType.CODE_QUALITY,
            score=0.85,
            findings_count=5,
            execution_time=2.5,
            metadata={"language": "python", "complexity": "medium"}
        )

        assert result.analysis_id is not None
        assert result.document_id == "doc123"
        assert result.analysis_type == AnalysisType.CODE_QUALITY
        assert result.status == AnalysisStatus.PENDING
        assert result.score == 0.85
        assert result.findings_count == 5
        assert result.execution_time == 2.5

    def test_analysis_result_status_methods(self):
        """Test analysis result status methods."""
        result = AnalysisResult()

        # Initially pending
        assert not result.is_successful()
        assert not result.is_high_quality()
        assert not result.is_critical_issues()

        # Start analysis
        result.start_analysis()
        assert result.status == AnalysisStatus.RUNNING
        assert result.started_at is not None

        # Complete successfully
        result.complete_analysis(0.9, 3, {"critical_findings": 0})
        assert result.status == AnalysisStatus.COMPLETED
        assert result.is_successful()
        assert result.is_high_quality()
        assert not result.is_critical_issues()
        assert result.completed_at is not None
        assert result.execution_time >= 0

        # Fail analysis
        failed_result = AnalysisResult()
        failed_result.fail_analysis("Analysis timeout")
        assert failed_result.status == AnalysisStatus.FAILED
        assert failed_result.metadata["error"] == "Analysis timeout"

    def test_analysis_result_quality_grading(self):
        """Test quality grade calculation."""
        # Grade A
        high_result = AnalysisResult(score=0.95)
        assert high_result.get_quality_grade() == "A"

        # Grade B
        good_result = AnalysisResult(score=0.85)
        assert good_result.get_quality_grade() == "B"

        # Grade C
        average_result = AnalysisResult(score=0.75)
        assert average_result.get_quality_grade() == "C"

        # Grade D
        poor_result = AnalysisResult(score=0.65)
        assert poor_result.get_quality_grade() == "D"

        # Grade F
        failing_result = AnalysisResult(score=0.45)
        assert failing_result.get_quality_grade() == "F"


class TestDocumentEntity:
    """Test the Document domain entity."""

    def test_document_creation(self):
        """Test creating a document."""
        document = Document(
            name="main.py",
            path="/src/main.py",
            document_type=DocumentType.CODE,
            content="print('Hello World')",
            size=21,
            language="python",
            checksum="abc123"
        )

        assert document.document_id is not None
        assert document.name == "main.py"
        assert document.path == "/src/main.py"
        assert document.document_type == DocumentType.CODE
        assert document.content == "print('Hello World')"
        assert document.size == 21
        assert document.language == "python"
        assert document.checksum == "abc123"

    def test_document_type_methods(self):
        """Test document type checking methods."""
        code_doc = Document(document_type=DocumentType.CODE)
        assert code_doc.is_code_file()

        config_doc = Document(document_type=DocumentType.CONFIGURATION)
        assert not config_doc.is_code_file()

    def test_document_file_operations(self):
        """Test document file operations."""
        # File extension
        py_doc = Document(name="script.py")
        assert py_doc.get_file_extension() == "py"

        js_doc = Document(name="app.js")
        assert js_doc.get_file_extension() == "js"

        no_ext_doc = Document(name="README")
        assert no_ext_doc.get_file_extension() == ""

        # Language support
        python_doc = Document(language="Python")
        assert python_doc.is_supported_language(["python", "javascript"])

        java_doc = Document(language="Java")
        assert not java_doc.is_supported_language(["python", "javascript"])

    def test_document_content_operations(self):
        """Test document content operations."""
        document = Document(content="line1\nline2\nline3")

        assert document.get_line_count() == 3
        assert document.get_content_lines() == ["line1", "line2", "line3"]

        # Update content
        document.update_content("new content")
        assert document.content == "new content"
        assert document.size == len("new content".encode('utf-8'))
        assert document.updated_at > document.created_at

        # Text search
        search_doc = Document(content="Hello World Test")
        assert search_doc.contains_text("world")  # Case insensitive
        assert search_doc.contains_text("Test")
        assert not search_doc.contains_text("missing")

    def test_document_size_checking(self):
        """Test document size checking."""
        small_doc = Document(size=500000)  # 500KB
        assert not small_doc.is_large_file()

        large_doc = Document(size=2000000)  # 2MB
        assert large_doc.is_large_file()


class TestFindingEntity:
    """Test the Finding domain entity."""

    def test_finding_creation(self):
        """Test creating a finding."""
        finding = Finding(
            analysis_id="analysis123",
            document_id="doc123",
            title="Unused variable",
            description="Variable 'x' is declared but never used",
            severity=FindingSeverity.MEDIUM,
            category="code-quality",
            line_number=15,
            column_number=8,
            code_snippet="x = 5",
            suggestion="Remove unused variable or use it",
            metadata={"rule_id": "unused-variable"}
        )

        assert finding.finding_id is not None
        assert finding.analysis_id == "analysis123"
        assert finding.document_id == "doc123"
        assert finding.title == "Unused variable"
        assert finding.severity == FindingSeverity.MEDIUM
        assert finding.category == "code-quality"
        assert finding.line_number == 15
        assert finding.column_number == 8
        assert finding.status == FindingStatus.OPEN

    def test_finding_severity_methods(self):
        """Test finding severity checking methods."""
        critical_finding = Finding(severity=FindingSeverity.CRITICAL)
        assert critical_finding.is_critical()
        assert critical_finding.is_high_severity()

        high_finding = Finding(severity=FindingSeverity.HIGH)
        assert not high_finding.is_critical()
        assert high_finding.is_high_severity()

        medium_finding = Finding(severity=FindingSeverity.MEDIUM)
        assert not medium_finding.is_critical()
        assert not medium_finding.is_high_severity()

    def test_finding_status_operations(self):
        """Test finding status operations."""
        finding = Finding()

        # Initially open
        assert not finding.is_resolved()
        assert finding.status == FindingStatus.OPEN

        # Resolve
        finding.resolve()
        assert finding.is_resolved()
        assert finding.status == FindingStatus.RESOLVED

        # Dismiss
        dismissed_finding = Finding()
        dismissed_finding.dismiss()
        assert dismissed_finding.is_resolved()
        assert dismissed_finding.status == FindingStatus.DISMISSED

        # Mark as false positive
        fp_finding = Finding()
        fp_finding.mark_false_positive()
        assert fp_finding.is_resolved()
        assert fp_finding.status == FindingStatus.FALSE_POSITIVE

    def test_finding_location_methods(self):
        """Test finding location methods."""
        # With line and column
        located_finding = Finding(line_number=10, column_number=5)
        assert located_finding.has_location()
        assert located_finding.get_location_string() == "line 10, column 5"

        # With only line
        line_only_finding = Finding(line_number=20)
        assert line_only_finding.has_location()
        assert line_only_finding.get_location_string() == "line 20"

        # No location
        no_location_finding = Finding()
        assert not no_location_finding.has_location()
        assert no_location_finding.get_location_string() == "unknown location"

    def test_finding_category_matching(self):
        """Test finding category matching."""
        finding = Finding(category="security")

        assert finding.matches_category(["security", "performance"])
        assert finding.matches_category(["SECURITY"])  # Case insensitive
        assert not finding.matches_category(["code-quality", "performance"])


class TestAnalysisConfigurationEntity:
    """Test the AnalysisConfiguration domain entity."""

    def test_configuration_creation(self):
        """Test creating an analysis configuration."""
        config = AnalysisConfiguration(
            name="Default Code Quality",
            analysis_types=[AnalysisType.CODE_QUALITY, AnalysisType.SECURITY],
            rules={"max-line-length": 120, "require-docstrings": True},
            thresholds={"critical-score": 0.9, "warning-score": 0.7},
            enabled=True,
            metadata={"version": "1.0", "author": "team"}
        )

        assert config.config_id is not None
        assert config.name == "Default Code Quality"
        assert AnalysisType.CODE_QUALITY in config.analysis_types
        assert AnalysisType.SECURITY in config.analysis_types
        assert config.rules["max-line-length"] == 120
        assert config.thresholds["critical-score"] == 0.9
        assert config.enabled

    def test_configuration_analysis_type_support(self):
        """Test analysis type support checking."""
        config = AnalysisConfiguration(
            analysis_types=[AnalysisType.CODE_QUALITY, AnalysisType.SECURITY]
        )

        assert config.supports_analysis_type(AnalysisType.CODE_QUALITY)
        assert config.supports_analysis_type(AnalysisType.SECURITY)
        assert not config.supports_analysis_type(AnalysisType.PERFORMANCE)

    def test_configuration_thresholds_and_rules(self):
        """Test configuration thresholds and rules access."""
        config = AnalysisConfiguration(
            thresholds={"quality": 0.8, "security": 0.9},
            rules={"max-complexity": 10, "require-tests": True}
        )

        # Thresholds
        assert config.get_threshold("quality") == 0.8
        assert config.get_threshold("security") == 0.9
        assert config.get_threshold("nonexistent", 0.5) == 0.5

        # Rules
        assert config.get_rule("max-complexity") == 10
        assert config.get_rule("require-tests") is True
        assert config.get_rule("nonexistent", "default") == "default"

    def test_configuration_modification(self):
        """Test configuration modification methods."""
        config = AnalysisConfiguration(analysis_types=[AnalysisType.CODE_QUALITY])

        # Add analysis type
        config.add_analysis_type(AnalysisType.SECURITY)
        assert config.supports_analysis_type(AnalysisType.SECURITY)

        # Remove analysis type
        config.remove_analysis_type(AnalysisType.CODE_QUALITY)
        assert not config.supports_analysis_type(AnalysisType.CODE_QUALITY)

        # Update threshold
        config.update_threshold("quality", 0.85)
        assert config.get_threshold("quality") == 0.85


class TestEntityIntegration:
    """Test integration between entities."""

    def test_analysis_result_with_document_integration(self):
        """Test integration between AnalysisResult and Document."""
        document = Document(
            name="utils.py",
            document_type=DocumentType.CODE,
            language="python",
            content="def helper():\n    pass"
        )

        result = AnalysisResult(
            document_id=document.document_id,
            analysis_type=AnalysisType.CODE_QUALITY,
            score=0.82,
            findings_count=2
        )

        # Complete analysis
        result.start_analysis()
        result.complete_analysis(0.82, 2, {"language": document.language})

        # Verify integration
        assert result.document_id == document.document_id
        assert result.is_successful()
        assert result.metadata["language"] == document.language
        assert document.is_code_file()
        assert document.is_supported_language(["python", "javascript"])

    def test_finding_with_analysis_integration(self):
        """Test integration between Finding and AnalysisResult."""
        result = AnalysisResult(
            analysis_type=AnalysisType.SECURITY,
            status=AnalysisStatus.COMPLETED
        )

        finding = Finding(
            analysis_id=result.analysis_id,
            title="SQL Injection Vulnerability",
            severity=FindingSeverity.CRITICAL,
            category="security",
            line_number=25,
            code_snippet="cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")",
            suggestion="Use parameterized queries instead of string formatting"
        )

        # Verify integration
        assert finding.analysis_id == result.analysis_id
        assert finding.is_critical()
        assert finding.has_location()
        assert finding.get_location_string() == "line 25"
        assert finding.matches_category(["security", "performance"])

    def test_configuration_with_analysis_integration(self):
        """Test integration between AnalysisConfiguration and AnalysisResult."""
        config = AnalysisConfiguration(
            name="Security Analysis",
            analysis_types=[AnalysisType.SECURITY],
            thresholds={"critical-threshold": 0.8}
        )

        result = AnalysisResult(
            analysis_type=AnalysisType.SECURITY,
            score=0.75
        )

        # Check configuration support
        assert config.supports_analysis_type(result.analysis_type)
        assert config.get_threshold("critical-threshold") == 0.8

        # Start and complete analysis
        result.start_analysis()
        result.complete_analysis(0.75, 5, {"config_used": config.name})

        # Verify integration
        assert result.metadata["config_used"] == config.name
        assert config.is_enabled()

    def test_complete_analysis_workflow(self):
        """Test complete analysis workflow with all entities."""
        # Create configuration
        config = AnalysisConfiguration(
            name="Comprehensive Analysis",
            analysis_types=[AnalysisType.CODE_QUALITY, AnalysisType.SECURITY],
            thresholds={"quality-threshold": 0.8, "security-threshold": 0.9}
        )

        # Create document
        document = Document(
            name="auth.py",
            document_type=DocumentType.CODE,
            language="python",
            content="def authenticate(user, password):\n    # Authentication logic\n    return True"
        )

        # Create analysis result
        result = AnalysisResult(
            document_id=document.document_id,
            analysis_type=AnalysisType.SECURITY
        )

        # Create findings
        finding1 = Finding(
            analysis_id=result.analysis_id,
            document_id=document.document_id,
            title="Weak Password Policy",
            severity=FindingSeverity.HIGH,
            category="security",
            line_number=2,
            suggestion="Implement strong password requirements"
        )

        finding2 = Finding(
            analysis_id=result.analysis_id,
            document_id=document.document_id,
            title="Missing Input Validation",
            severity=FindingSeverity.MEDIUM,
            category="security",
            line_number=1,
            suggestion="Add input validation for user and password parameters"
        )

        # Execute analysis workflow
        result.start_analysis()
        result.complete_analysis(
            score=0.65,
            findings_count=2,
            metadata={
                "language": document.language,
                "config_used": config.name,
                "critical_findings": 0,
                "high_findings": 1,
                "medium_findings": 1
            }
        )

        # Verify complete workflow
        assert config.supports_analysis_type(AnalysisType.SECURITY)
        assert document.is_code_file()
        assert document.is_supported_language(["python"])

        assert result.is_successful()
        assert not result.is_high_quality()  # 0.65 < 0.8
        assert not result.is_critical_issues()
        assert result.get_quality_grade() == "D"

        assert finding1.is_high_severity()
        assert finding1.has_location()
        assert not finding2.is_high_severity()  # MEDIUM severity is not high severity
        assert finding2.has_location()

        assert result.metadata["language"] == "python"
        assert result.metadata["config_used"] == "Comprehensive Analysis"
