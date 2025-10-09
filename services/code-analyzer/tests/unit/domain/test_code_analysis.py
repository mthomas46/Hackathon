"""
Unit tests for CodeAnalysis entity (Aggregate Root).

These tests follow TDD - written BEFORE implementation.
All tests should FAIL initially (Red Phase).
"""

import pytest
from datetime import datetime


@pytest.mark.unit
@pytest.mark.domain
class TestCodeAnalysisCreation:
    """Test CodeAnalysis entity creation and validation."""
    
    def test_create_code_analysis_with_valid_inputs(self, simple_python_function):
        """Test creating CodeAnalysis with valid inputs."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.value_objects import Language, AnalysisStatus
        
        # Arrange
        code = simple_python_function
        language = Language.PYTHON
        
        # Act
        analysis = CodeAnalysis(
            code_content=code,
            language=language
        )
        
        # Assert
        assert analysis is not None
        assert analysis.code_content == code
        assert analysis.language == Language.PYTHON
        assert analysis.status == AnalysisStatus.PENDING
        assert analysis.analysis_id is not None
        assert isinstance(analysis.timestamp, datetime)
    
    def test_reject_empty_code(self):
        """Test CodeAnalysis rejects empty code content."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.value_objects import Language
        from domain.exceptions import InvalidCodeError
        
        # Arrange
        empty_code = ""
        
        # Act & Assert
        with pytest.raises(InvalidCodeError):
            CodeAnalysis(code_content=empty_code, language=Language.PYTHON)
    
    def test_reject_whitespace_only_code(self):
        """Test CodeAnalysis rejects whitespace-only code."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.value_objects import Language
        from domain.exceptions import InvalidCodeError
        
        # Arrange
        whitespace_code = "   \n\t  \n  "
        
        # Act & Assert
        with pytest.raises(InvalidCodeError):
            CodeAnalysis(code_content=whitespace_code, language=Language.PYTHON)
    
    def test_reject_none_code(self):
        """Test CodeAnalysis rejects None as code."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.value_objects import Language
        from domain.exceptions import InvalidCodeError
        
        # Act & Assert
        with pytest.raises(InvalidCodeError):
            CodeAnalysis(code_content=None, language=Language.PYTHON)
    
    def test_reject_unsupported_language(self):
        """Test CodeAnalysis rejects unsupported language."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.exceptions import UnsupportedLanguageError
        
        # Arrange
        code = "def test(): pass"
        
        # Act & Assert
        with pytest.raises(UnsupportedLanguageError):
            CodeAnalysis(code_content=code, language="cobol")
    
    def test_generates_unique_analysis_id(self, simple_python_function):
        """Test each CodeAnalysis gets unique ID."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.value_objects import Language
        
        # Arrange & Act
        analysis1 = CodeAnalysis(
            code_content=simple_python_function,
            language=Language.PYTHON
        )
        analysis2 = CodeAnalysis(
            code_content=simple_python_function,
            language=Language.PYTHON
        )
        
        # Assert
        assert analysis1.analysis_id != analysis2.analysis_id


@pytest.mark.unit
@pytest.mark.domain
class TestCodeAnalysisStatus:
    """Test CodeAnalysis status transitions."""
    
    def test_initial_status_is_pending(self, simple_python_function):
        """Test new CodeAnalysis starts with PENDING status."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.value_objects import Language, AnalysisStatus
        
        # Act
        analysis = CodeAnalysis(
            code_content=simple_python_function,
            language=Language.PYTHON
        )
        
        # Assert
        assert analysis.status == AnalysisStatus.PENDING
    
    def test_transition_pending_to_analyzing(self, simple_python_function):
        """Test status transition from PENDING to ANALYZING."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.value_objects import Language, AnalysisStatus
        
        # Arrange
        analysis = CodeAnalysis(
            code_content=simple_python_function,
            language=Language.PYTHON
        )
        
        # Act
        analysis.start_analysis()
        
        # Assert
        assert analysis.status == AnalysisStatus.ANALYZING
    
    def test_transition_analyzing_to_completed(self, simple_python_function):
        """Test status transition from ANALYZING to COMPLETED."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.entities.analysis_results import AnalysisResults
        from domain.value_objects import Language, AnalysisStatus
        
        # Arrange
        analysis = CodeAnalysis(
            code_content=simple_python_function,
            language=Language.PYTHON
        )
        analysis.start_analysis()
        
        # Act - Set results first (business rule requirement)
        results = AnalysisResults(structures=[], complexity_metrics={})
        analysis.set_results(results)
        analysis.complete_analysis()
        
        # Assert
        assert analysis.status == AnalysisStatus.COMPLETED
    
    def test_cannot_transition_from_completed_to_analyzing(self, simple_python_function):
        """Test cannot restart completed analysis."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.entities.analysis_results import AnalysisResults
        from domain.value_objects import Language
        from domain.exceptions import InvalidStatusTransitionError
        
        # Arrange
        analysis = CodeAnalysis(
            code_content=simple_python_function,
            language=Language.PYTHON
        )
        analysis.start_analysis()
        
        # Set results and complete (business rule requirement)
        results = AnalysisResults(structures=[], complexity_metrics={})
        analysis.set_results(results)
        analysis.complete_analysis()
        
        # Act & Assert
        with pytest.raises(InvalidStatusTransitionError):
            analysis.start_analysis()
    
    def test_transition_to_failed_status(self, simple_python_function):
        """Test status transition to FAILED."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.value_objects import Language, AnalysisStatus
        
        # Arrange
        analysis = CodeAnalysis(
            code_content=simple_python_function,
            language=Language.PYTHON
        )
        analysis.start_analysis()
        
        # Act
        error_message = "Analysis failed due to syntax error"
        analysis.mark_failed(error_message)
        
        # Assert
        assert analysis.status == AnalysisStatus.FAILED
        assert analysis.error_message == error_message


@pytest.mark.unit
@pytest.mark.domain
class TestCodeAnalysisResults:
    """Test CodeAnalysis results handling."""
    
    def test_results_initially_none(self, simple_python_function):
        """Test results are None before analysis."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.value_objects import Language
        
        # Act
        analysis = CodeAnalysis(
            code_content=simple_python_function,
            language=Language.PYTHON
        )
        
        # Assert
        assert analysis.results is None
    
    def test_set_results_when_completed(self, simple_python_function, sample_complexity_metrics):
        """Test setting results on completed analysis."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.entities.analysis_results import AnalysisResults
        from domain.value_objects import Language
        
        # Arrange
        analysis = CodeAnalysis(
            code_content=simple_python_function,
            language=Language.PYTHON
        )
        analysis.start_analysis()
        
        results = AnalysisResults(
            structures=[],
            complexity_metrics=sample_complexity_metrics
        )
        
        # Act
        analysis.set_results(results)
        analysis.complete_analysis()
        
        # Assert
        assert analysis.results is not None
        assert analysis.results == results
    
    def test_cannot_modify_results_after_completion(self, simple_python_function):
        """Test results are immutable after analysis complete."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.entities.analysis_results import AnalysisResults
        from domain.value_objects import Language
        from domain.exceptions import AnalysisImmutableError
        
        # Arrange
        analysis = CodeAnalysis(
            code_content=simple_python_function,
            language=Language.PYTHON
        )
        analysis.start_analysis()
        
        results1 = AnalysisResults(structures=[], complexity_metrics={})
        analysis.set_results(results1)
        analysis.complete_analysis()
        
        # Act & Assert
        results2 = AnalysisResults(structures=[], complexity_metrics={})
        with pytest.raises(AnalysisImmutableError):
            analysis.set_results(results2)


@pytest.mark.unit
@pytest.mark.domain
class TestCodeAnalysisInvariants:
    """Test CodeAnalysis invariants are maintained."""
    
    def test_completed_analysis_must_have_results(self, simple_python_function):
        """Test business rule: completed analysis must have results."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.value_objects import Language
        from domain.exceptions import InvariantViolationError
        
        # Arrange
        analysis = CodeAnalysis(
            code_content=simple_python_function,
            language=Language.PYTHON
        )
        analysis.start_analysis()
        
        # Act & Assert - Cannot complete without results
        with pytest.raises(InvariantViolationError):
            analysis.complete_analysis()
    
    def test_failed_analysis_must_have_error_message(self, simple_python_function):
        """Test business rule: failed analysis must have error message."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.value_objects import Language
        from domain.exceptions import InvariantViolationError
        
        # Arrange
        analysis = CodeAnalysis(
            code_content=simple_python_function,
            language=Language.PYTHON
        )
        analysis.start_analysis()
        
        # Act & Assert - Cannot fail without error message
        with pytest.raises(InvariantViolationError):
            analysis.mark_failed(None)
        
        with pytest.raises(InvariantViolationError):
            analysis.mark_failed("")
    
    def test_analysis_language_is_immutable(self, simple_python_function):
        """Test language cannot be changed after creation."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.value_objects import Language
        
        # Arrange
        analysis = CodeAnalysis(
            code_content=simple_python_function,
            language=Language.PYTHON
        )
        
        # Act & Assert - Language should not have setter
        with pytest.raises(AttributeError):
            analysis.language = Language.JAVASCRIPT
    
    def test_analysis_timestamp_is_set_at_creation(self, simple_python_function):
        """Test timestamp is set when analysis is created."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.value_objects import Language
        
        # Arrange & Act
        before = datetime.now()
        analysis = CodeAnalysis(
            code_content=simple_python_function,
            language=Language.PYTHON
        )
        after = datetime.now()
        
        # Assert
        assert before <= analysis.timestamp <= after


@pytest.mark.unit
@pytest.mark.domain
class TestCodeAnalysisEquality:
    """Test CodeAnalysis equality and identity."""
    
    def test_equality_based_on_analysis_id(self, simple_python_function):
        """Test two analyses with same ID are equal."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.value_objects import Language
        
        # Arrange
        analysis1 = CodeAnalysis(
            code_content=simple_python_function,
            language=Language.PYTHON
        )
        
        # Create second analysis with same ID (for testing)
        analysis2 = CodeAnalysis(
            code_content=simple_python_function,
            language=Language.PYTHON
        )
        analysis2._analysis_id = analysis1.analysis_id
        
        # Act & Assert
        assert analysis1 == analysis2
    
    def test_inequality_with_different_ids(self, simple_python_function):
        """Test two analyses with different IDs are not equal."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.value_objects import Language
        
        # Arrange & Act
        analysis1 = CodeAnalysis(
            code_content=simple_python_function,
            language=Language.PYTHON
        )
        analysis2 = CodeAnalysis(
            code_content=simple_python_function,
            language=Language.PYTHON
        )
        
        # Assert
        assert analysis1 != analysis2

