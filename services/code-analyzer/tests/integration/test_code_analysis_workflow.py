"""
Integration tests for complete code analysis workflow.

These tests verify that domain components work together correctly
in realistic end-to-end scenarios.
"""

import pytest


@pytest.mark.integration
class TestCompleteAnalysisWorkflow:
    """Test complete code analysis workflow from start to finish."""
    
    def test_analyze_simple_function_complete_workflow(self):
        """Test complete workflow: create analysis, analyze, get results."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language, AnalysisStatus
        
        # Arrange
        analyzer = CodeAnalyzer()
        code = """
def calculate_sum(a, b):
    '''Calculate sum of two numbers.'''
    return a + b
"""
        
        # Act - Complete workflow
        analysis = analyzer.analyze(code=code, language=Language.PYTHON)
        
        # Assert - Analysis completed successfully
        assert analysis.status == AnalysisStatus.COMPLETED
        assert analysis.results is not None
        
        # Assert - Structure extraction worked
        assert len(analysis.results.structures) == 1
        structure = analysis.results.structures[0]
        assert structure.type == "function"
        assert structure.name == "calculate_sum"
        
        # Assert - Complexity calculation worked
        assert analysis.results.complexity is not None
        assert analysis.results.complexity.cyclomatic_complexity >= 1
        assert 0 <= analysis.results.complexity.maintainability_index <= 100
        
        # Assert - Security scan worked
        assert isinstance(analysis.results.security_findings, list)
        
        # Assert - Style check worked
        assert isinstance(analysis.results.style_issues, list)
    
    def test_analyze_class_with_methods(self):
        """Test analyzing a class with multiple methods."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        
        # Arrange
        analyzer = CodeAnalyzer()
        code = """
class Calculator:
    '''Simple calculator class.'''
    
    def add(self, a, b):
        '''Add two numbers.'''
        return a + b
    
    def subtract(self, a, b):
        '''Subtract two numbers.'''
        return a - b
    
    def multiply(self, a, b):
        '''Multiply two numbers.'''
        return a * b
"""
        
        # Act
        analysis = analyzer.analyze(code=code, language=Language.PYTHON)
        
        # Assert - Found class and methods
        assert len(analysis.results.structures) == 4  # 1 class + 3 methods
        
        class_structures = [s for s in analysis.results.structures if s.type == "class"]
        assert len(class_structures) == 1
        assert class_structures[0].name == "Calculator"
        
        function_structures = [s for s in analysis.results.structures if s.type == "function"]
        assert len(function_structures) == 3
        function_names = {f.name for f in function_structures}
        assert function_names == {"add", "subtract", "multiply"}
    
    def test_analyze_code_with_security_issues(self):
        """Test workflow detects and reports security issues."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language, Severity
        
        # Arrange
        analyzer = CodeAnalyzer()
        code = """
def unsafe_function(user_input):
    # Security issue: eval usage
    result = eval(user_input)
    
    # Security issue: exec usage
    exec("print('hello')")
    
    return result
"""
        
        # Act
        analysis = analyzer.analyze(code=code, language=Language.PYTHON)
        
        # Assert - Completed successfully
        assert analysis.status.name == "COMPLETED"
        
        # Assert - Found security issues
        assert len(analysis.results.security_findings) >= 2
        
        # Assert - Found critical findings
        critical_findings = [
            f for f in analysis.results.security_findings 
            if f.severity == Severity.CRITICAL
        ]
        assert len(critical_findings) >= 2
        
        # Assert - Findings have proper structure
        for finding in critical_findings:
            assert finding.vulnerability_type is not None
            assert finding.line_number > 0
            assert finding.description is not None
            assert finding.recommendation is not None
    
    def test_analyze_code_with_style_issues(self):
        """Test workflow detects and reports style issues."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        
        # Arrange
        analyzer = CodeAnalyzer()
        code = """
def function_with_very_long_line():
    # This is a very long line that exceeds the maximum line length of 79 characters which should be flagged
    return True
"""
        
        # Act
        analysis = analyzer.analyze(code=code, language=Language.PYTHON)
        
        # Assert - Found style issues
        assert len(analysis.results.style_issues) >= 1
        
        # Assert - Found line length issue
        long_line_issues = [
            issue for issue in analysis.results.style_issues
            if "too long" in issue.message.lower()
        ]
        assert len(long_line_issues) >= 1
        assert long_line_issues[0].rule_id == "E501"


@pytest.mark.integration
class TestAnalysisOptionsIntegration:
    """Test integration with different analysis options."""
    
    def test_selective_analysis_security_only(self):
        """Test analyzing with only security scanning enabled."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.entities.analysis_options import AnalysisOptions
        from domain.value_objects import Language
        
        # Arrange
        analyzer = CodeAnalyzer()
        options = AnalysisOptions(
            include_structure=False,
            include_complexity=False,
            include_security=True,
            include_style=False
        )
        code = """
def unsafe():
    eval("print('test')")
"""
        
        # Act
        analysis = analyzer.analyze(code=code, language=Language.PYTHON, options=options)
        
        # Assert - Only security findings present
        assert len(analysis.results.structures) == 0
        assert analysis.results.complexity is None
        assert len(analysis.results.security_findings) >= 1
        assert len(analysis.results.style_issues) == 0
    
    def test_selective_analysis_complexity_only(self):
        """Test analyzing with only complexity calculation enabled."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.entities.analysis_options import AnalysisOptions
        from domain.value_objects import Language
        
        # Arrange
        analyzer = CodeAnalyzer()
        options = AnalysisOptions(
            include_structure=False,
            include_complexity=True,
            include_security=False,
            include_style=False
        )
        code = """
def complex_function(a, b, c):
    if a > 0:
        if b > 0:
            if c > 0:
                return a + b + c
    return 0
"""
        
        # Act
        analysis = analyzer.analyze(code=code, language=Language.PYTHON, options=options)
        
        # Assert - Only complexity metrics present
        assert len(analysis.results.structures) == 0
        assert analysis.results.complexity is not None
        assert analysis.results.complexity.cyclomatic_complexity >= 4
        assert len(analysis.results.security_findings) == 0
        assert len(analysis.results.style_issues) == 0


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test integration of error handling across components."""
    
    def test_syntax_error_workflow(self):
        """Test workflow handles syntax errors gracefully."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language, AnalysisStatus
        
        # Arrange
        analyzer = CodeAnalyzer()
        invalid_code = """
def broken_function(
    return "missing closing parenthesis"
"""
        
        # Act
        analysis = analyzer.analyze(code=invalid_code, language=Language.PYTHON)
        
        # Assert - Analysis marked as failed
        assert analysis.status == AnalysisStatus.FAILED
        assert analysis.error_message is not None
        assert "syntax" in analysis.error_message.lower()
        
        # Assert - No results for failed analysis
        assert analysis.results is None
    
    def test_empty_code_validation(self):
        """Test validation rejects empty code early."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        from domain.exceptions import InvalidCodeError
        
        # Arrange
        analyzer = CodeAnalyzer()
        
        # Act & Assert - Should raise before analysis starts
        with pytest.raises(InvalidCodeError):
            analyzer.analyze(code="", language=Language.PYTHON)


@pytest.mark.integration
class TestComplexityCalculationIntegration:
    """Test integration of complexity calculation with real code."""
    
    def test_simple_code_low_complexity(self):
        """Test simple code has low complexity."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        
        # Arrange
        analyzer = CodeAnalyzer()
        code = """
def simple_add(a, b):
    return a + b
"""
        
        # Act
        analysis = analyzer.analyze(code=code, language=Language.PYTHON)
        
        # Assert - Low complexity
        metrics = analysis.results.complexity
        assert metrics.cyclomatic_complexity <= 2
        assert metrics.maintainability_index >= 80
    
    def test_complex_code_high_complexity(self):
        """Test complex code has high complexity."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        
        # Arrange
        analyzer = CodeAnalyzer()
        code = """
def complex_logic(a, b, c, d, e):
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        return 1
                    else:
                        return 2
                else:
                    return 3
            else:
                return 4
        else:
            return 5
    else:
        return 6
"""
        
        # Act
        analysis = analyzer.analyze(code=code, language=Language.PYTHON)
        
        # Assert - High complexity
        metrics = analysis.results.complexity
        assert metrics.cyclomatic_complexity >= 6
        # Complex code should have lower maintainability than simple code
        assert metrics.maintainability_index < 85


@pytest.mark.integration
class TestEntityLifecycleIntegration:
    """Test entity lifecycle through complete workflows."""
    
    def test_analysis_lifecycle_success(self):
        """Test successful analysis lifecycle: PENDING → ANALYZING → COMPLETED."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.entities.analysis_results import AnalysisResults
        from domain.value_objects import Language, AnalysisStatus
        
        # Arrange
        code = "def test(): pass"
        analysis = CodeAnalysis(code_content=code, language=Language.PYTHON)
        
        # Assert - Initial state
        assert analysis.status == AnalysisStatus.PENDING
        assert analysis.results is None
        
        # Act - Start analysis
        analysis.start_analysis()
        
        # Assert - Analyzing state
        assert analysis.status == AnalysisStatus.ANALYZING
        assert analysis.results is None
        
        # Act - Set results and complete
        results = AnalysisResults(structures=[], complexity_metrics={})
        analysis.set_results(results)
        analysis.complete_analysis()
        
        # Assert - Completed state
        assert analysis.status == AnalysisStatus.COMPLETED
        assert analysis.results is not None
    
    def test_analysis_lifecycle_failure(self):
        """Test failed analysis lifecycle: PENDING → ANALYZING → FAILED."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.value_objects import Language, AnalysisStatus
        
        # Arrange
        code = "def test(): pass"
        analysis = CodeAnalysis(code_content=code, language=Language.PYTHON)
        
        # Act - Start and fail
        analysis.start_analysis()
        analysis.mark_failed("Simulated error")
        
        # Assert - Failed state
        assert analysis.status == AnalysisStatus.FAILED
        assert analysis.error_message == "Simulated error"
        assert analysis.results is None
    
    def test_analysis_immutability_after_completion(self):
        """Test analysis results cannot be modified after completion."""
        from domain.entities.code_analysis import CodeAnalysis
        from domain.entities.analysis_results import AnalysisResults
        from domain.value_objects import Language
        from domain.exceptions import AnalysisImmutableError
        
        # Arrange
        code = "def test(): pass"
        analysis = CodeAnalysis(code_content=code, language=Language.PYTHON)
        analysis.start_analysis()
        
        results1 = AnalysisResults(structures=[], complexity_metrics={})
        analysis.set_results(results1)
        analysis.complete_analysis()
        
        # Act & Assert - Cannot modify after completion
        results2 = AnalysisResults(structures=[], complexity_metrics={})
        with pytest.raises(AnalysisImmutableError):
            analysis.set_results(results2)


@pytest.mark.integration
class TestValueObjectIntegration:
    """Test value objects integrate correctly with entities and services."""
    
    def test_language_detection_and_analysis(self):
        """Test Language value object integrates with analysis."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        
        # Arrange
        analyzer = CodeAnalyzer()
        python_code = "def test(): pass"
        
        # Act - Detect language and analyze
        language = Language.PYTHON
        analysis = analyzer.analyze(code=python_code, language=language)
        
        # Assert
        assert analysis.language == Language.PYTHON
        assert analysis.status.name in ["COMPLETED", "FAILED"]
    
    def test_severity_ordering_in_findings(self):
        """Test Severity value object ordering works in real findings."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language, Severity
        
        # Arrange
        analyzer = CodeAnalyzer()
        code = """
eval("test")  # CRITICAL
exec("test")  # CRITICAL
import pickle
pickle.loads(b"test")  # HIGH
"""
        
        # Act
        analysis = analyzer.analyze(code=code, language=Language.PYTHON)
        
        # Assert - Can sort by severity
        findings = analysis.results.security_findings
        sorted_findings = sorted(findings, key=lambda f: f.severity, reverse=True)
        
        # Critical findings should come first
        assert sorted_findings[0].severity in [Severity.CRITICAL, Severity.HIGH]
        assert sorted_findings[0].severity >= sorted_findings[-1].severity
    
    def test_complexity_metrics_validation_integration(self):
        """Test ComplexityMetrics validation works in real analysis."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        
        # Arrange
        analyzer = CodeAnalyzer()
        code = "def test(): pass"
        
        # Act
        analysis = analyzer.analyze(code=code, language=Language.PYTHON)
        
        # Assert - Metrics are valid
        metrics = analysis.results.complexity
        assert 0 <= metrics.maintainability_index <= 100
        assert 0.0 <= metrics.comment_ratio <= 1.0
        assert metrics.cyclomatic_complexity >= 0
        assert metrics.lines_of_code >= 0

