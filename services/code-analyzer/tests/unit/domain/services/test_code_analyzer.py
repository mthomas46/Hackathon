"""
Unit tests for CodeAnalyzer domain service.

These tests follow TDD - written BEFORE implementation.
All tests should FAIL initially (Red Phase).
"""

import pytest


@pytest.mark.unit
@pytest.mark.domain
class TestCodeAnalyzerBasicAnalysis:
    """Test basic code analysis functionality."""
    
    def test_analyze_simple_python_function(self, simple_python_function):
        """Test analyzing a simple Python function."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        
        # Arrange
        analyzer = CodeAnalyzer()
        code = simple_python_function
        language = Language.PYTHON
        
        # Act
        analysis = analyzer.analyze(code=code, language=language)
        
        # Assert
        assert analysis is not None
        assert analysis.status.name == "COMPLETED"
        assert analysis.results is not None
    
    def test_analyze_python_class(self, python_class_code):
        """Test analyzing a Python class."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        
        # Arrange
        analyzer = CodeAnalyzer()
        code = python_class_code
        language = Language.PYTHON
        
        # Act
        analysis = analyzer.analyze(code=code, language=language)
        
        # Assert
        assert analysis.status.name == "COMPLETED"
        assert len(analysis.results.structures) > 0
        # Should find the class
        class_structures = [s for s in analysis.results.structures if s.type == "class"]
        assert len(class_structures) == 1
        assert class_structures[0].name == "ShoppingCart"
    
    def test_analyze_returns_complexity_metrics(self, simple_python_function):
        """Test analysis includes complexity metrics."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        
        # Arrange
        analyzer = CodeAnalyzer()
        
        # Act
        analysis = analyzer.analyze(code=simple_python_function, language=Language.PYTHON)
        
        # Assert
        assert analysis.results.complexity is not None
        assert analysis.results.complexity.cyclomatic_complexity >= 1
        assert 0 <= analysis.results.complexity.maintainability_index <= 100
        assert 0 <= analysis.results.complexity.comment_ratio <= 1


@pytest.mark.unit
@pytest.mark.domain
class TestCodeAnalyzerErrorHandling:
    """Test CodeAnalyzer error handling."""
    
    def test_handle_syntax_error_gracefully(self):
        """Test analyzer handles syntax errors gracefully."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        
        # Arrange
        analyzer = CodeAnalyzer()
        invalid_code = "def broken(\n  return 'missing colon'"
        
        # Act
        analysis = analyzer.analyze(code=invalid_code, language=Language.PYTHON)
        
        # Assert
        assert analysis.status.name == "FAILED"
        assert analysis.error_message is not None
        assert "syntax" in analysis.error_message.lower()
    
    def test_reject_empty_code(self):
        """Test analyzer rejects empty code."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        from domain.exceptions import InvalidCodeError
        
        # Arrange
        analyzer = CodeAnalyzer()
        
        # Act & Assert
        with pytest.raises(InvalidCodeError):
            analyzer.analyze(code="", language=Language.PYTHON)
    
    def test_reject_unsupported_language(self):
        """Test analyzer rejects unsupported language."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.exceptions import UnsupportedLanguageError
        
        # Arrange
        analyzer = CodeAnalyzer()
        code = "def test(): pass"
        
        # Act & Assert
        with pytest.raises(UnsupportedLanguageError):
            analyzer.analyze(code=code, language="fortran")


@pytest.mark.unit
@pytest.mark.domain
class TestCodeAnalyzerCoordination:
    """Test CodeAnalyzer coordinates sub-analyzers."""
    
    def test_calls_structure_extractor(self, simple_python_function, mocker):
        """Test CodeAnalyzer calls structure extraction."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        
        # Arrange
        analyzer = CodeAnalyzer()
        mock_extractor = mocker.patch.object(analyzer, '_extract_structures')
        mock_extractor.return_value = []
        
        # Act
        analyzer.analyze(code=simple_python_function, language=Language.PYTHON)
        
        # Assert
        mock_extractor.assert_called_once()
    
    def test_calls_complexity_calculator(self, simple_python_function, mocker):
        """Test CodeAnalyzer calls complexity calculation."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        
        # Arrange
        analyzer = CodeAnalyzer()
        mock_calculator = mocker.patch.object(analyzer, '_calculate_complexity')
        mock_calculator.return_value = {}
        
        # Act
        analyzer.analyze(code=simple_python_function, language=Language.PYTHON)
        
        # Assert
        mock_calculator.assert_called_once()
    
    def test_calls_security_scanner(self, simple_python_function, mocker):
        """Test CodeAnalyzer calls security scanning."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        
        # Arrange
        analyzer = CodeAnalyzer()
        mock_scanner = mocker.patch.object(analyzer, '_scan_security')
        mock_scanner.return_value = []
        
        # Act
        analyzer.analyze(code=simple_python_function, language=Language.PYTHON)
        
        # Assert
        mock_scanner.assert_called_once()


@pytest.mark.unit
@pytest.mark.domain
class TestCodeAnalyzerBusinessRules:
    """Test CodeAnalyzer applies business rules."""
    
    def test_flags_high_complexity_functions(self, complex_python_code):
        """Test business rule: flag functions with complexity > 10."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        
        # Arrange
        analyzer = CodeAnalyzer()
        
        # Act
        analysis = analyzer.analyze(code=complex_python_code, language=Language.PYTHON)
        
        # Assert - Complex code should be flagged
        function_structures = [s for s in analysis.results.structures if s.type == "function"]
        complex_functions = [f for f in function_structures if f.complexity > 10]
        assert len(complex_functions) > 0
    
    def test_elevates_critical_security_findings(self, code_with_security_issues):
        """Test business rule: critical findings are elevated."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language, Severity
        
        # Arrange
        analyzer = CodeAnalyzer()
        
        # Act
        analysis = analyzer.analyze(code=code_with_security_issues, language=Language.PYTHON)
        
        # Assert
        critical_findings = [
            f for f in analysis.results.security_findings 
            if f.severity == Severity.CRITICAL
        ]
        # Should find at least the eval() usage as critical
        assert len(critical_findings) > 0


@pytest.mark.unit
@pytest.mark.domain
class TestCodeAnalyzerOptions:
    """Test CodeAnalyzer with different analysis options."""
    
    def test_skip_complexity_analysis_when_disabled(self, simple_python_function):
        """Test can disable complexity analysis."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        from domain.entities.analysis_options import AnalysisOptions
        
        # Arrange
        analyzer = CodeAnalyzer()
        options = AnalysisOptions(include_complexity=False)
        
        # Act
        analysis = analyzer.analyze(
            code=simple_python_function, 
            language=Language.PYTHON,
            options=options
        )
        
        # Assert
        assert analysis.results.complexity is None
    
    def test_skip_security_scan_when_disabled(self, simple_python_function):
        """Test can disable security scanning."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        from domain.entities.analysis_options import AnalysisOptions
        
        # Arrange
        analyzer = CodeAnalyzer()
        options = AnalysisOptions(include_security=False)
        
        # Act
        analysis = analyzer.analyze(
            code=simple_python_function,
            language=Language.PYTHON,
            options=options
        )
        
        # Assert
        assert len(analysis.results.security_findings) == 0
    
    def test_default_options_include_all_analyses(self, simple_python_function):
        """Test default options include all analyses."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        
        # Arrange
        analyzer = CodeAnalyzer()
        
        # Act - No options specified
        analysis = analyzer.analyze(
            code=simple_python_function,
            language=Language.PYTHON
        )
        
        # Assert - All analyses should be present
        assert analysis.results.structures is not None
        assert analysis.results.complexity is not None
        assert analysis.results.security_findings is not None
        assert analysis.results.style_issues is not None

