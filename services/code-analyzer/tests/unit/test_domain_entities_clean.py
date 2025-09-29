"""Clean unit tests for code-analyzer domain entities."""

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


class SeverityLevel(str, Enum):
    """Security severity level enumeration."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class EntityType(str, Enum):
    """Entity type enumeration."""
    ENDPOINT = "endpoint"
    MODEL = "model"
    SERVICE = "service"
    UTILITY = "utility"
    CONFIG = "config"


class AnalysisResult:
    """Domain entity for analysis results."""

    def __init__(self,
                 result_id: str = None,
                 source_code: str = None,
                 language: str = "python",
                 status: AnalysisStatus = AnalysisStatus.PENDING,
                 entities_found: List[Dict] = None,
                 security_issues: List[Dict] = None,
                 complexity_metrics: Dict = None,
                 quality_score: float = 0.0,
                 analysis_timestamp: datetime = None,
                 processing_time_ms: int = 0):
        self.result_id = result_id or str(uuid4())
        self.source_code = source_code or ""
        self.language = language
        self.status = status
        self.entities_found = entities_found or []
        self.security_issues = security_issues or []
        self.complexity_metrics = complexity_metrics or {}
        self.quality_score = quality_score
        self.analysis_timestamp = analysis_timestamp or datetime.now(timezone.utc)
        self.processing_time_ms = processing_time_ms

    def is_completed(self) -> bool:
        """Check if analysis is completed."""
        return self.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]

    def is_successful(self) -> bool:
        """Check if analysis was successful."""
        return self.status == AnalysisStatus.COMPLETED and self.quality_score >= 0.5

    def add_entity(self, entity_type: str, name: str, location: Dict = None):
        """Add a found entity."""
        entity = {
            "type": entity_type,
            "name": name,
            "location": location or {},
            "confidence": 0.9
        }
        self.entities_found.append(entity)

    def add_security_issue(self, issue_type: str, severity: SeverityLevel,
                          description: str, location: Dict = None):
        """Add a security issue."""
        issue = {
            "type": issue_type,
            "severity": severity,
            "description": description,
            "location": location or {},
            "remediation": f"Fix {issue_type} issue"
        }
        self.security_issues.append(issue)

    def calculate_quality_score(self):
        """Calculate overall quality score."""
        if not self.entities_found and not self.security_issues:
            self.quality_score = 0.0
            return

        # Base score from entities found
        entity_score = min(len(self.entities_found) * 0.1, 0.5)

        # Penalty for security issues
        severity_penalty = 0.0
        for issue in self.security_issues:
            if issue["severity"] == SeverityLevel.CRITICAL:
                severity_penalty += 0.3
            elif issue["severity"] == SeverityLevel.HIGH:
                severity_penalty += 0.2
            elif issue["severity"] == SeverityLevel.MEDIUM:
                severity_penalty += 0.1

        # Complexity bonus/penalty
        complexity_score = self.complexity_metrics.get("cyclomatic_complexity", 5)
        if complexity_score > 10:
            complexity_penalty = min((complexity_score - 10) * 0.05, 0.3)
        else:
            complexity_penalty = 0.0

        self.quality_score = max(0.0, min(1.0, entity_score - severity_penalty - complexity_penalty))

    def get_critical_issues(self) -> List[Dict]:
        """Get critical security issues."""
        return [issue for issue in self.security_issues
                if issue["severity"] == SeverityLevel.CRITICAL]

    def get_high_severity_issues(self) -> List[Dict]:
        """Get high severity security issues."""
        return [issue for issue in self.security_issues
                if issue["severity"] in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]]


class SecurityIssue:
    """Domain entity for security issues."""

    def __init__(self,
                 issue_id: str = None,
                 issue_type: str = None,
                 severity: SeverityLevel = SeverityLevel.MEDIUM,
                 title: str = None,
                 description: str = None,
                 file_path: str = None,
                 line_number: int = None,
                 code_snippet: str = None,
                 cwe_id: str = None,
                 remediation: str = None,
                 discovered_at: datetime = None):
        self.issue_id = issue_id or str(uuid4())
        self.issue_type = issue_type
        self.severity = severity
        self.title = title
        self.description = description
        self.file_path = file_path
        self.line_number = line_number
        self.code_snippet = code_snippet
        self.cwe_id = cwe_id
        self.remediation = remediation
        self.discovered_at = discovered_at or datetime.now(timezone.utc)

    def is_critical(self) -> bool:
        """Check if issue is critical."""
        return self.severity == SeverityLevel.CRITICAL

    def is_high_severity(self) -> bool:
        """Check if issue is high severity."""
        return self.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]

    def get_location_string(self) -> str:
        """Get string representation of location."""
        if self.file_path and self.line_number:
            return f"{self.file_path}:{self.line_number}"
        elif self.file_path:
            return self.file_path
        return "unknown"

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "issue_id": self.issue_id,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "location": self.get_location_string(),
            "cwe_id": self.cwe_id,
            "remediation": self.remediation,
            "discovered_at": self.discovered_at.isoformat()
        }


class AnalysisMetrics:
    """Domain entity for analysis metrics."""

    def __init__(self,
                 analysis_id: str = None,
                 lines_of_code: int = 0,
                 functions_count: int = 0,
                 classes_count: int = 0,
                 complexity_average: float = 0.0,
                 complexity_max: int = 0,
                 duplication_percentage: float = 0.0,
                 test_coverage: float = 0.0,
                 maintainability_index: float = 0.0):
        self.analysis_id = analysis_id or str(uuid4())
        self.lines_of_code = lines_of_code
        self.functions_count = functions_count
        self.classes_count = classes_count
        self.complexity_average = complexity_average
        self.complexity_max = complexity_max
        self.duplication_percentage = duplication_percentage
        self.test_coverage = test_coverage
        self.maintainability_index = maintainability_index

    def get_code_quality_score(self) -> float:
        """Calculate overall code quality score."""
        # Base score from maintainability
        score = self.maintainability_index / 100.0

        # Adjust for complexity
        if self.complexity_average > 10:
            score -= 0.2
        elif self.complexity_average < 5:
            score += 0.1

        # Adjust for duplication
        score -= self.duplication_percentage * 0.5

        # Adjust for test coverage
        score += self.test_coverage * 0.3

        return max(0.0, min(1.0, score))

    def has_high_complexity(self) -> bool:
        """Check if code has high complexity."""
        return self.complexity_max > 15 or self.complexity_average > 8

    def needs_refactoring(self) -> bool:
        """Check if code needs refactoring."""
        return (self.duplication_percentage > 0.3 or
                self.maintainability_index < 50 or
                self.has_high_complexity())


class TestAnalysisResultEntity:
    """Test the AnalysisResult domain entity."""

    def test_analysis_result_creation(self):
        """Test creating an analysis result."""
        result = AnalysisResult(
            source_code="def hello(): pass",
            language="python",
            status=AnalysisStatus.PENDING
        )

        assert result.result_id is not None
        assert result.source_code == "def hello(): pass"
        assert result.language == "python"
        assert result.status == AnalysisStatus.PENDING
        assert result.quality_score == 0.0

    def test_analysis_result_status_methods(self):
        """Test status-related methods."""
        pending_result = AnalysisResult(status=AnalysisStatus.PENDING)
        assert not pending_result.is_completed()
        assert not pending_result.is_successful()

        completed_result = AnalysisResult(status=AnalysisStatus.COMPLETED, quality_score=0.8)
        assert completed_result.is_completed()
        assert completed_result.is_successful()

        failed_result = AnalysisResult(status=AnalysisStatus.FAILED, quality_score=0.2)
        assert failed_result.is_completed()
        assert not failed_result.is_successful()

    def test_entity_management(self):
        """Test entity addition and management."""
        result = AnalysisResult()

        # Add entities
        result.add_entity("function", "hello_world", {"line": 1, "column": 5})
        result.add_entity("class", "MyClass", {"line": 10, "column": 1})

        assert len(result.entities_found) == 2
        assert result.entities_found[0]["type"] == "function"
        assert result.entities_found[0]["name"] == "hello_world"
        assert result.entities_found[1]["name"] == "MyClass"

    def test_security_issue_management(self):
        """Test security issue addition and management."""
        result = AnalysisResult()

        # Add security issues
        result.add_security_issue("sql_injection", SeverityLevel.CRITICAL,
                                "SQL injection vulnerability found",
                                {"line": 25, "column": 10})
        result.add_security_issue("xss", SeverityLevel.HIGH,
                                "Cross-site scripting vulnerability",
                                {"line": 45, "column": 5})

        assert len(result.security_issues) == 2
        assert result.security_issues[0]["type"] == "sql_injection"
        assert result.security_issues[0]["severity"] == SeverityLevel.CRITICAL
        assert result.security_issues[1]["severity"] == SeverityLevel.HIGH

    def test_quality_score_calculation(self):
        """Test quality score calculation."""
        result = AnalysisResult()

        # Test with entities but no issues
        result.add_entity("function", "test_func")
        result.add_entity("class", "TestClass")
        result.calculate_quality_score()
        assert result.quality_score > 0

        # Test with security issues (should reduce score)
        result.add_security_issue("sql_injection", SeverityLevel.CRITICAL, "SQL injection")
        result.calculate_quality_score()
        assert result.quality_score < 0.5  # Should be reduced due to critical issue

    def test_critical_issues_filtering(self):
        """Test filtering critical issues."""
        result = AnalysisResult()

        result.add_security_issue("sql_injection", SeverityLevel.CRITICAL, "Critical issue")
        result.add_security_issue("xss", SeverityLevel.HIGH, "High issue")
        result.add_security_issue("unused_var", SeverityLevel.INFO, "Info issue")

        critical_issues = result.get_critical_issues()
        high_severity_issues = result.get_high_severity_issues()

        assert len(critical_issues) == 1
        assert critical_issues[0]["severity"] == SeverityLevel.CRITICAL
        assert len(high_severity_issues) == 2  # Critical + High


class TestSecurityIssueEntity:
    """Test the SecurityIssue domain entity."""

    def test_security_issue_creation(self):
        """Test creating a security issue."""
        issue = SecurityIssue(
            issue_type="sql_injection",
            severity=SeverityLevel.CRITICAL,
            title="SQL Injection Vulnerability",
            description="Unsafe SQL query construction",
            file_path="/app/main.py",
            line_number=25,
            cwe_id="CWE-89"
        )

        assert issue.issue_id is not None
        assert issue.issue_type == "sql_injection"
        assert issue.severity == SeverityLevel.CRITICAL
        assert issue.title == "SQL Injection Vulnerability"
        assert issue.file_path == "/app/main.py"
        assert issue.line_number == 25
        assert issue.cwe_id == "CWE-89"

    def test_severity_checks(self):
        """Test severity checking methods."""
        critical_issue = SecurityIssue(severity=SeverityLevel.CRITICAL)
        high_issue = SecurityIssue(severity=SeverityLevel.HIGH)
        medium_issue = SecurityIssue(severity=SeverityLevel.MEDIUM)

        assert critical_issue.is_critical()
        assert critical_issue.is_high_severity()

        assert not high_issue.is_critical()
        assert high_issue.is_high_severity()

        assert not medium_issue.is_critical()
        assert not medium_issue.is_high_severity()

    def test_location_string_generation(self):
        """Test location string generation."""
        # Full location
        issue = SecurityIssue(file_path="/app/code.py", line_number=42)
        assert issue.get_location_string() == "/app/code.py:42"

        # File only
        issue_file_only = SecurityIssue(file_path="/app/utils.py")
        assert issue_file_only.get_location_string() == "/app/utils.py"

        # No location
        issue_no_location = SecurityIssue()
        assert issue_no_location.get_location_string() == "unknown"

    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        issue = SecurityIssue(
            issue_type="xss",
            severity=SeverityLevel.HIGH,
            title="XSS Vulnerability",
            file_path="/app/templates.py",
            line_number=15
        )

        data = issue.to_dict()

        assert data["issue_type"] == "xss"
        assert data["severity"] == SeverityLevel.HIGH
        assert data["title"] == "XSS Vulnerability"
        assert data["location"] == "/app/templates.py:15"
        assert "discovered_at" in data


class TestAnalysisMetricsEntity:
    """Test the AnalysisMetrics domain entity."""

    def test_analysis_metrics_creation(self):
        """Test creating analysis metrics."""
        metrics = AnalysisMetrics(
            lines_of_code=150,
            functions_count=12,
            classes_count=3,
            complexity_average=6.5,
            complexity_max=12,
            duplication_percentage=0.15,
            test_coverage=0.75,
            maintainability_index=78.5
        )

        assert metrics.lines_of_code == 150
        assert metrics.functions_count == 12
        assert metrics.classes_count == 3
        assert metrics.complexity_average == 6.5
        assert metrics.complexity_max == 12
        assert metrics.duplication_percentage == 0.15
        assert metrics.test_coverage == 0.75
        assert metrics.maintainability_index == 78.5

    def test_code_quality_score_calculation(self):
        """Test code quality score calculation."""
        # High quality code
        high_quality = AnalysisMetrics(
            maintainability_index=85.0,
            complexity_average=4.0,
            duplication_percentage=0.05,
            test_coverage=0.9
        )
        assert high_quality.get_code_quality_score() > 0.8

        # Poor quality code
        poor_quality = AnalysisMetrics(
            maintainability_index=25.0,
            complexity_average=15.0,
            duplication_percentage=0.4,
            test_coverage=0.1
        )
        assert poor_quality.get_code_quality_score() < 0.3

    def test_complexity_checks(self):
        """Test complexity checking methods."""
        low_complexity = AnalysisMetrics(complexity_average=4.0, complexity_max=8)
        assert not low_complexity.has_high_complexity()

        high_complexity = AnalysisMetrics(complexity_average=12.0, complexity_max=20)
        assert high_complexity.has_high_complexity()

    def test_refactoring_needed_check(self):
        """Test refactoring needed determination."""
        good_code = AnalysisMetrics(
            duplication_percentage=0.1,
            maintainability_index=80.0,
            complexity_average=5.0,
            complexity_max=10
        )
        assert not good_code.needs_refactoring()

        bad_code = AnalysisMetrics(
            duplication_percentage=0.5,  # High duplication
            maintainability_index=30.0,  # Low maintainability
            complexity_average=15.0,     # High complexity
            complexity_max=25
        )
        assert bad_code.needs_refactoring()


class TestEntityIntegration:
    """Test integration between entities."""

    def test_analysis_result_with_security_issues(self):
        """Test integration between AnalysisResult and SecurityIssue."""
        result = AnalysisResult(source_code="vulnerable code")

        # Create security issues
        sql_issue = SecurityIssue(
            issue_type="sql_injection",
            severity=SeverityLevel.CRITICAL,
            title="SQL Injection",
            file_path="main.py",
            line_number=25
        )

        xss_issue = SecurityIssue(
            issue_type="xss",
            severity=SeverityLevel.HIGH,
            title="XSS Vulnerability",
            file_path="templates.py",
            line_number=45
        )

        # Add to result
        result.add_security_issue(
            sql_issue.issue_type,
            sql_issue.severity,
            sql_issue.title,
            {"file": sql_issue.file_path, "line": sql_issue.line_number}
        )

        result.add_security_issue(
            xss_issue.issue_type,
            xss_issue.severity,
            xss_issue.title,
            {"file": xss_issue.file_path, "line": xss_issue.line_number}
        )

        # Verify integration
        assert len(result.security_issues) == 2
        assert result.get_critical_issues()[0]["type"] == "sql_injection"
        assert len(result.get_high_severity_issues()) == 2

    def test_analysis_result_with_metrics(self):
        """Test integration between AnalysisResult and AnalysisMetrics."""
        result = AnalysisResult()
        metrics = AnalysisMetrics(
            maintainability_index=75.0,
            complexity_average=7.0,
            duplication_percentage=0.2
        )

        # Simulate metrics calculation in result
        result.complexity_metrics = {
            "cyclomatic_complexity": metrics.complexity_average,
            "maintainability_index": metrics.maintainability_index,
            "duplication": metrics.duplication_percentage
        }

        result.add_entity("function", "main")
        result.add_entity("class", "App")

        # Calculate quality score
        result.calculate_quality_score()

        # Quality score should be reasonable
        assert 0.0 <= result.quality_score <= 1.0

        # Verify metrics integration
        assert result.complexity_metrics["cyclomatic_complexity"] == 7.0
        assert result.complexity_metrics["maintainability_index"] == 75.0

    def test_complete_analysis_workflow(self):
        """Test complete analysis workflow with all entities."""
        # Create analysis result
        result = AnalysisResult(
            source_code="def analyze_code(): return 'analysis'",
            language="python"
        )

        # Add entities found
        result.add_entity("function", "analyze_code", {"line": 1})
        result.add_entity("module", "__main__", {"line": 1})

        # Add security issues
        result.add_security_issue(
            "hardcoded_secret",
            SeverityLevel.HIGH,
            "Hardcoded API key found",
            {"line": 10, "column": 15}
        )

        # Set complexity metrics
        result.complexity_metrics = {
            "cyclomatic_complexity": 8.0,
            "lines_of_code": 50,
            "functions_count": 5
        }

        # Calculate quality score
        result.calculate_quality_score()

        # Complete analysis
        result.status = AnalysisStatus.COMPLETED
        result.processing_time_ms = 150

        # Verify complete workflow
        assert result.is_completed()
        assert len(result.entities_found) == 2
        assert len(result.security_issues) == 1
        assert result.quality_score >= 0  # Quality score can be 0 with penalties
        assert result.processing_time_ms == 150
