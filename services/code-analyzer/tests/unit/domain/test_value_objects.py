"""
Unit tests for domain value objects.

These tests follow TDD - written BEFORE implementation.
All tests should FAIL initially (Red Phase).
"""

import pytest


@pytest.mark.unit
@pytest.mark.domain
class TestLanguageValueObject:
    """Test Language value object."""
    
    def test_language_enum_values(self):
        """Test Language has all supported values."""
        from domain.value_objects import Language
        
        # Assert all expected languages exist
        assert hasattr(Language, 'PYTHON')
        assert hasattr(Language, 'JAVASCRIPT')
        assert hasattr(Language, 'TYPESCRIPT')
        assert hasattr(Language, 'JAVA')
        assert hasattr(Language, 'GO')
        assert hasattr(Language, 'RUST')
    
    def test_language_file_extensions(self):
        """Test Language has file extension mappings."""
        from domain.value_objects import Language
        
        # Act & Assert
        assert Language.PYTHON.extensions == ['.py', '.pyw']
        assert Language.JAVASCRIPT.extensions == ['.js', '.mjs']
        assert Language.TYPESCRIPT.extensions == ['.ts']
    
    def test_language_equality(self):
        """Test Language equality comparison."""
        from domain.value_objects import Language
        
        # Arrange
        lang1 = Language.PYTHON
        lang2 = Language.PYTHON
        lang3 = Language.JAVASCRIPT
        
        # Assert
        assert lang1 == lang2
        assert lang1 != lang3
    
    def test_language_is_immutable(self):
        """Test Language value object is immutable."""
        from domain.value_objects import Language
        
        # Arrange
        lang = Language.PYTHON
        
        # Act & Assert - Should not be able to modify
        with pytest.raises(AttributeError):
            lang.name = "Ruby"
    
    def test_language_from_extension(self):
        """Test detecting language from file extension."""
        from domain.value_objects import Language
        
        # Act & Assert
        assert Language.from_extension('.py') == Language.PYTHON
        assert Language.from_extension('.js') == Language.JAVASCRIPT
        assert Language.from_extension('.ts') == Language.TYPESCRIPT
    
    def test_language_from_unknown_extension(self):
        """Test handling unknown file extension."""
        from domain.value_objects import Language
        from domain.exceptions import UnsupportedLanguageError
        
        # Act & Assert
        with pytest.raises(UnsupportedLanguageError):
            Language.from_extension('.xyz')


@pytest.mark.unit
@pytest.mark.domain
class TestAnalysisStatusValueObject:
    """Test AnalysisStatus value object."""
    
    def test_analysis_status_values(self):
        """Test AnalysisStatus has all expected values."""
        from domain.value_objects import AnalysisStatus
        
        # Assert
        assert hasattr(AnalysisStatus, 'PENDING')
        assert hasattr(AnalysisStatus, 'ANALYZING')
        assert hasattr(AnalysisStatus, 'COMPLETED')
        assert hasattr(AnalysisStatus, 'FAILED')
    
    def test_valid_status_transitions(self):
        """Test which status transitions are valid."""
        from domain.value_objects import AnalysisStatus
        
        # PENDING can transition to ANALYZING or FAILED
        assert AnalysisStatus.PENDING.can_transition_to(AnalysisStatus.ANALYZING)
        assert AnalysisStatus.PENDING.can_transition_to(AnalysisStatus.FAILED)
        
        # ANALYZING can transition to COMPLETED or FAILED
        assert AnalysisStatus.ANALYZING.can_transition_to(AnalysisStatus.COMPLETED)
        assert AnalysisStatus.ANALYZING.can_transition_to(AnalysisStatus.FAILED)
        
        # COMPLETED and FAILED are terminal states
        assert not AnalysisStatus.COMPLETED.can_transition_to(AnalysisStatus.ANALYZING)
        assert not AnalysisStatus.FAILED.can_transition_to(AnalysisStatus.ANALYZING)
    
    def test_invalid_status_transitions(self):
        """Test invalid status transitions."""
        from domain.value_objects import AnalysisStatus
        
        # Cannot skip states
        assert not AnalysisStatus.PENDING.can_transition_to(AnalysisStatus.COMPLETED)
        
        # Cannot go backwards
        assert not AnalysisStatus.COMPLETED.can_transition_to(AnalysisStatus.PENDING)
        assert not AnalysisStatus.ANALYZING.can_transition_to(AnalysisStatus.PENDING)


@pytest.mark.unit
@pytest.mark.domain
class TestComplexityMetricsValueObject:
    """Test ComplexityMetrics value object."""
    
    def test_create_complexity_metrics_with_valid_values(self):
        """Test creating ComplexityMetrics with valid values."""
        from domain.value_objects import ComplexityMetrics
        
        # Arrange & Act
        metrics = ComplexityMetrics(
            cyclomatic_complexity=5,
            cognitive_complexity=3,
            maintainability_index=75.5,
            lines_of_code=100,
            comment_ratio=0.15
        )
        
        # Assert
        assert metrics.cyclomatic_complexity == 5
        assert metrics.cognitive_complexity == 3
        assert metrics.maintainability_index == 75.5
        assert metrics.lines_of_code == 100
        assert metrics.comment_ratio == 0.15
    
    def test_reject_negative_complexity(self):
        """Test ComplexityMetrics rejects negative values."""
        from domain.value_objects import ComplexityMetrics
        from domain.exceptions import InvalidValueError
        
        # Act & Assert
        with pytest.raises(InvalidValueError):
            ComplexityMetrics(
                cyclomatic_complexity=-1,
                cognitive_complexity=3,
                maintainability_index=75.0,
                lines_of_code=100,
                comment_ratio=0.15
            )
    
    def test_maintainability_index_bounds(self):
        """Test maintainability index must be 0-100."""
        from domain.value_objects import ComplexityMetrics
        from domain.exceptions import InvalidValueError
        
        # Valid bounds
        metrics = ComplexityMetrics(
            cyclomatic_complexity=5,
            cognitive_complexity=3,
            maintainability_index=0,
            lines_of_code=100,
            comment_ratio=0.1
        )
        assert metrics.maintainability_index == 0
        
        metrics = ComplexityMetrics(
            cyclomatic_complexity=5,
            cognitive_complexity=3,
            maintainability_index=100,
            lines_of_code=100,
            comment_ratio=0.1
        )
        assert metrics.maintainability_index == 100
        
        # Invalid - too high
        with pytest.raises(InvalidValueError):
            ComplexityMetrics(
                cyclomatic_complexity=5,
                cognitive_complexity=3,
                maintainability_index=101,
                lines_of_code=100,
                comment_ratio=0.1
            )
        
        # Invalid - negative
        with pytest.raises(InvalidValueError):
            ComplexityMetrics(
                cyclomatic_complexity=5,
                cognitive_complexity=3,
                maintainability_index=-1,
                lines_of_code=100,
                comment_ratio=0.1
            )
    
    def test_comment_ratio_bounds(self):
        """Test comment_ratio must be 0.0-1.0."""
        from domain.value_objects import ComplexityMetrics
        from domain.exceptions import InvalidValueError
        
        # Valid bounds
        metrics = ComplexityMetrics(
            cyclomatic_complexity=5,
            cognitive_complexity=3,
            maintainability_index=75.0,
            lines_of_code=100,
            comment_ratio=0.0
        )
        assert metrics.comment_ratio == 0.0
        
        metrics = ComplexityMetrics(
            cyclomatic_complexity=5,
            cognitive_complexity=3,
            maintainability_index=75.0,
            lines_of_code=100,
            comment_ratio=1.0
        )
        assert metrics.comment_ratio == 1.0
        
        # Invalid - too high
        with pytest.raises(InvalidValueError):
            ComplexityMetrics(
                cyclomatic_complexity=5,
                cognitive_complexity=3,
                maintainability_index=75.0,
                lines_of_code=100,
                comment_ratio=1.5
            )
    
    def test_complexity_metrics_equality(self):
        """Test ComplexityMetrics equality comparison."""
        from domain.value_objects import ComplexityMetrics
        
        # Arrange
        metrics1 = ComplexityMetrics(
            cyclomatic_complexity=5,
            cognitive_complexity=3,
            maintainability_index=75.0,
            lines_of_code=100,
            comment_ratio=0.15
        )
        
        metrics2 = ComplexityMetrics(
            cyclomatic_complexity=5,
            cognitive_complexity=3,
            maintainability_index=75.0,
            lines_of_code=100,
            comment_ratio=0.15
        )
        
        metrics3 = ComplexityMetrics(
            cyclomatic_complexity=10,
            cognitive_complexity=5,
            maintainability_index=60.0,
            lines_of_code=200,
            comment_ratio=0.20
        )
        
        # Assert
        assert metrics1 == metrics2
        assert metrics1 != metrics3
    
    def test_complexity_metrics_is_immutable(self):
        """Test ComplexityMetrics is immutable."""
        from domain.value_objects import ComplexityMetrics
        
        # Arrange
        metrics = ComplexityMetrics(
            cyclomatic_complexity=5,
            cognitive_complexity=3,
            maintainability_index=75.0,
            lines_of_code=100,
            comment_ratio=0.15
        )
        
        # Act & Assert - Should not be able to modify
        with pytest.raises(AttributeError):
            metrics.cyclomatic_complexity = 10


@pytest.mark.unit
@pytest.mark.domain
class TestSeverityValueObject:
    """Test Severity value object."""
    
    def test_severity_levels(self):
        """Test Severity has all expected levels."""
        from domain.value_objects import Severity
        
        # Assert
        assert hasattr(Severity, 'CRITICAL')
        assert hasattr(Severity, 'HIGH')
        assert hasattr(Severity, 'MEDIUM')
        assert hasattr(Severity, 'LOW')
        assert hasattr(Severity, 'INFO')
    
    def test_severity_comparison(self):
        """Test Severity levels can be compared."""
        from domain.value_objects import Severity
        
        # Assert
        assert Severity.CRITICAL > Severity.HIGH
        assert Severity.HIGH > Severity.MEDIUM
        assert Severity.MEDIUM > Severity.LOW
        assert Severity.LOW > Severity.INFO
    
    def test_severity_ordering(self):
        """Test Severity can be sorted."""
        from domain.value_objects import Severity
        
        # Arrange
        severities = [
            Severity.INFO,
            Severity.CRITICAL,
            Severity.MEDIUM,
            Severity.LOW,
            Severity.HIGH
        ]
        
        # Act
        sorted_severities = sorted(severities, reverse=True)
        
        # Assert
        assert sorted_severities == [
            Severity.CRITICAL,
            Severity.HIGH,
            Severity.MEDIUM,
            Severity.LOW,
            Severity.INFO
        ]


@pytest.mark.unit
@pytest.mark.domain
class TestStyleIssueValueObject:
    """Test StyleIssue value object."""
    
    def test_create_style_issue(self):
        """Test creating StyleIssue value object."""
        from domain.value_objects import StyleIssue, Severity
        
        # Arrange & Act
        issue = StyleIssue(
            severity=Severity.WARNING,
            line_number=42,
            message="Line too long (95 > 79 characters)",
            rule_id="E501"
        )
        
        # Assert
        assert issue.severity == Severity.WARNING
        assert issue.line_number == 42
        assert issue.message == "Line too long (95 > 79 characters)"
        assert issue.rule_id == "E501"
    
    def test_style_issue_requires_positive_line_number(self):
        """Test StyleIssue requires positive line number."""
        from domain.value_objects import StyleIssue, Severity
        from domain.exceptions import InvalidValueError
        
        # Act & Assert
        with pytest.raises(InvalidValueError):
            StyleIssue(
                severity=Severity.WARNING,
                line_number=0,
                message="Test message",
                rule_id="E501"
            )
        
        with pytest.raises(InvalidValueError):
            StyleIssue(
                severity=Severity.WARNING,
                line_number=-1,
                message="Test message",
                rule_id="E501"
            )


@pytest.mark.unit
@pytest.mark.domain
class TestSecurityFindingValueObject:
    """Test SecurityFinding value object."""
    
    def test_create_security_finding(self):
        """Test creating SecurityFinding value object."""
        from domain.value_objects import SecurityFinding, Severity
        
        # Arrange & Act
        finding = SecurityFinding(
            severity=Severity.HIGH,
            vulnerability_type="SQL Injection",
            line_number=25,
            description="Potential SQL injection vulnerability detected",
            recommendation="Use parameterized queries instead of string formatting"
        )
        
        # Assert
        assert finding.severity == Severity.HIGH
        assert finding.vulnerability_type == "SQL Injection"
        assert finding.line_number == 25
        assert "SQL injection" in finding.description
        assert "parameterized queries" in finding.recommendation
    
    def test_security_finding_requires_recommendation(self):
        """Test SecurityFinding must have recommendation."""
        from domain.value_objects import SecurityFinding, Severity
        from domain.exceptions import InvalidValueError
        
        # Act & Assert
        with pytest.raises(InvalidValueError):
            SecurityFinding(
                severity=Severity.HIGH,
                vulnerability_type="SQL Injection",
                line_number=25,
                description="SQL injection detected",
                recommendation=""  # Empty recommendation
            )

