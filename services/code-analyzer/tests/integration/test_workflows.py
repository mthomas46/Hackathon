"""
Workflow tests for code-analyzer service.

These tests simulate real-world usage scenarios and complete workflows
that users would perform with the service.
"""

import pytest
from typing import List


@pytest.mark.integration
@pytest.mark.workflow
class TestSingleFileAnalysisWorkflow:
    """Test single file analysis workflows."""
    
    def test_analyze_single_python_module(self):
        """Test complete workflow for analyzing a single Python module."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language, AnalysisStatus
        
        # Arrange - User has a Python module to analyze
        analyzer = CodeAnalyzer()
        module_code = """
'''User management module.'''

class UserManager:
    '''Manages user operations.'''
    
    def __init__(self):
        self.users = []
    
    def add_user(self, name, email):
        '''Add a new user.'''
        if not name or not email:
            raise ValueError("Name and email required")
        
        user = {'name': name, 'email': email}
        self.users.append(user)
        return user
    
    def find_user(self, email):
        '''Find user by email.'''
        for user in self.users:
            if user['email'] == email:
                return user
        return None
    
    def remove_user(self, email):
        '''Remove user by email.'''
        user = self.find_user(email)
        if user:
            self.users.remove(user)
            return True
        return False
"""
        
        # Act - User runs analysis
        analysis = analyzer.analyze(code=module_code, language=Language.PYTHON)
        
        # Assert - Analysis completes successfully
        assert analysis.status == AnalysisStatus.COMPLETED
        assert analysis.results is not None
        
        # Assert - Key information extracted
        # Should find 1 class and 4 methods
        structures = analysis.results.structures
        classes = [s for s in structures if s.type == "class"]
        methods = [s for s in structures if s.type == "function"]
        
        assert len(classes) == 1
        assert classes[0].name == "UserManager"
        assert len(methods) == 4
        
        # Assert - Reasonable complexity metrics
        complexity = analysis.results.complexity
        assert complexity.cyclomatic_complexity >= 1
        assert 0 <= complexity.maintainability_index <= 100
        assert complexity.lines_of_code > 0
    
    def test_analyze_utility_functions(self):
        """Test analyzing a file with utility functions."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        
        # Arrange - User has utility functions
        analyzer = CodeAnalyzer()
        utility_code = """
def validate_email(email):
    '''Validate email format.'''
    return '@' in email and '.' in email.split('@')[1]

def format_phone(phone):
    '''Format phone number.'''
    digits = ''.join(c for c in phone if c.isdigit())
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return phone

def calculate_age(birth_year):
    '''Calculate age from birth year.'''
    from datetime import datetime
    current_year = datetime.now().year
    return current_year - birth_year
"""
        
        # Act - User runs analysis
        analysis = analyzer.analyze(code=utility_code, language=Language.PYTHON)
        
        # Assert - Found all utility functions
        functions = [s for s in analysis.results.structures if s.type == "function"]
        assert len(functions) == 3
        
        function_names = {f.name for f in functions}
        assert function_names == {"validate_email", "format_phone", "calculate_age"}


@pytest.mark.integration
@pytest.mark.workflow
class TestBatchAnalysisWorkflow:
    """Test batch analysis workflows."""
    
    def test_analyze_multiple_files_sequentially(self):
        """Test analyzing multiple files in sequence."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language, AnalysisStatus
        
        # Arrange - User has multiple files to analyze
        analyzer = CodeAnalyzer()
        
        files = [
            ("config.py", "DATABASE_URL = 'postgresql://localhost/db'\nAPI_KEY = 'secret'"),
            ("utils.py", "def helper(): return True"),
            ("models.py", "class User:\n    def __init__(self, name):\n        self.name = name")
        ]
        
        # Act - User analyzes each file
        results = []
        for filename, code in files:
            analysis = analyzer.analyze(code=code, language=Language.PYTHON)
            results.append({
                'filename': filename,
                'status': analysis.status,
                'structures_count': len(analysis.results.structures) if analysis.results else 0
            })
        
        # Assert - All analyses completed
        assert all(r['status'] == AnalysisStatus.COMPLETED for r in results)
        
        # Assert - Each file analyzed independently
        assert len(results) == 3
        assert results[0]['filename'] == 'config.py'
        assert results[1]['structures_count'] >= 1  # utils.py has function
        assert results[2]['structures_count'] >= 1  # models.py has class
    
    def test_batch_analysis_with_error_handling(self):
        """Test batch analysis where some files have errors."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language, AnalysisStatus
        
        # Arrange - Mix of valid and invalid code
        analyzer = CodeAnalyzer()
        
        files = [
            ("valid1.py", "def valid(): pass"),
            ("invalid.py", "def broken(\n  return 'syntax error'"),
            ("valid2.py", "class Valid: pass")
        ]
        
        # Act - Analyze all files, handling errors gracefully
        results = []
        for filename, code in files:
            analysis = analyzer.analyze(code=code, language=Language.PYTHON)
            results.append({
                'filename': filename,
                'status': analysis.status,
                'success': analysis.status == AnalysisStatus.COMPLETED
            })
        
        # Assert - Valid files succeeded, invalid file failed
        assert results[0]['success'] is True
        assert results[1]['success'] is False  # Syntax error
        assert results[2]['success'] is True
        
        # Assert - Batch continued despite error
        assert len(results) == 3


@pytest.mark.integration
@pytest.mark.workflow
class TestCustomOptionsWorkflow:
    """Test workflows with custom analysis options."""
    
    def test_security_focused_analysis_workflow(self):
        """Test workflow for security-focused code review."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.entities.analysis_options import AnalysisOptions
        from domain.value_objects import Language, Severity
        
        # Arrange - Security team wants to scan for vulnerabilities only
        analyzer = CodeAnalyzer()
        options = AnalysisOptions(
            include_structure=False,
            include_complexity=False,
            include_security=True,
            include_style=False
        )
        
        code = """
import os
import pickle

def process_user_input(user_data):
    # Security issues present
    result = eval(user_data)
    exec(f"print({user_data})")
    
    # Unsafe deserialization
    obj = pickle.loads(user_data.encode())
    
    return result
"""
        
        # Act - Run security scan
        analysis = analyzer.analyze(code=code, language=Language.PYTHON, options=options)
        
        # Assert - Only security findings returned
        assert len(analysis.results.structures) == 0
        assert analysis.results.complexity is None
        assert len(analysis.results.style_issues) == 0
        
        # Assert - Security findings present
        assert len(analysis.results.security_findings) >= 3
        
        # Assert - Critical issues flagged
        critical_count = sum(
            1 for f in analysis.results.security_findings 
            if f.severity == Severity.CRITICAL
        )
        assert critical_count >= 2  # eval and exec
    
    def test_code_quality_analysis_workflow(self):
        """Test workflow for code quality assessment."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.entities.analysis_options import AnalysisOptions
        from domain.value_objects import Language
        
        # Arrange - Code quality team wants structure and complexity only
        analyzer = CodeAnalyzer()
        options = AnalysisOptions(
            include_structure=True,
            include_complexity=True,
            include_security=False,
            include_style=False
        )
        
        code = """
def calculate_discount(price, customer_type, loyalty_years):
    '''Calculate discount based on multiple factors.'''
    if customer_type == 'premium':
        if loyalty_years > 5:
            if price > 1000:
                return price * 0.20
            else:
                return price * 0.15
        else:
            return price * 0.10
    elif customer_type == 'regular':
        if loyalty_years > 3:
            return price * 0.05
    return 0
"""
        
        # Act - Run quality analysis
        analysis = analyzer.analyze(code=code, language=Language.PYTHON, options=options)
        
        # Assert - Structure and complexity returned
        assert len(analysis.results.structures) >= 1
        assert analysis.results.complexity is not None
        assert analysis.results.complexity.cyclomatic_complexity >= 6
        
        # Assert - Security and style skipped
        assert len(analysis.results.security_findings) == 0
        assert len(analysis.results.style_issues) == 0


@pytest.mark.integration
@pytest.mark.workflow
class TestErrorRecoveryWorkflow:
    """Test error recovery workflows."""
    
    def test_recover_from_syntax_error_and_continue(self):
        """Test recovering from syntax error and continuing workflow."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language, AnalysisStatus
        
        # Arrange - User has code with syntax error, fixes it, analyzes again
        analyzer = CodeAnalyzer()
        
        # Act - First attempt with syntax error
        invalid_code = "def broken(\n  return 'missing paren'"
        first_analysis = analyzer.analyze(code=invalid_code, language=Language.PYTHON)
        
        # Assert - First analysis failed
        assert first_analysis.status == AnalysisStatus.FAILED
        assert "syntax" in first_analysis.error_message.lower()
        
        # Act - User fixes syntax error and retries
        fixed_code = "def fixed():\n    return 'working now'"
        second_analysis = analyzer.analyze(code=fixed_code, language=Language.PYTHON)
        
        # Assert - Second analysis succeeded
        assert second_analysis.status == AnalysisStatus.COMPLETED
        assert second_analysis.results is not None
        assert len(second_analysis.results.structures) >= 1
    
    def test_handle_empty_file_gracefully(self):
        """Test handling of empty/whitespace-only files."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        from domain.exceptions import InvalidCodeError
        
        # Arrange - User accidentally tries to analyze empty file
        analyzer = CodeAnalyzer()
        
        # Act & Assert - Empty code rejected early
        with pytest.raises(InvalidCodeError):
            analyzer.analyze(code="", language=Language.PYTHON)
        
        # Act & Assert - Whitespace-only code rejected
        with pytest.raises(InvalidCodeError):
            analyzer.analyze(code="   \n\t  ", language=Language.PYTHON)


@pytest.mark.integration
@pytest.mark.workflow
class TestSequentialAnalysisWorkflow:
    """Test sequential analysis workflows."""
    
    def test_progressive_analysis_workflow(self):
        """Test progressive analysis: quick scan → full analysis."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.entities.analysis_options import AnalysisOptions
        from domain.value_objects import Language
        
        # Arrange - User wants quick scan first, then full analysis
        analyzer = CodeAnalyzer()
        code = """
def process_data(data):
    result = eval(data)  # Security issue
    if len(data) > 10:
        return result.upper()
    return result
"""
        
        # Act - Phase 1: Quick security scan only
        quick_options = AnalysisOptions(
            include_structure=False,
            include_complexity=False,
            include_security=True,
            include_style=False
        )
        quick_analysis = analyzer.analyze(code=code, language=Language.PYTHON, options=quick_options)
        
        # Assert - Quick scan found security issues
        assert len(quick_analysis.results.security_findings) >= 1
        
        # Act - Phase 2: Full analysis after security review
        full_analysis = analyzer.analyze(code=code, language=Language.PYTHON)
        
        # Assert - Full analysis has all information
        assert len(full_analysis.results.structures) >= 1
        assert full_analysis.results.complexity is not None
        assert len(full_analysis.results.security_findings) >= 1
    
    def test_iterative_improvement_workflow(self):
        """Test workflow where code is iteratively improved."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language
        
        # Arrange - User improves code based on analysis feedback
        analyzer = CodeAnalyzer()
        
        # Act - Version 1: Complex, insecure code
        v1_code = """
def process(input):
    result = eval(input)  # Security issue
    if result > 0:
        if result < 10:
            if result % 2 == 0:
                return "even_small"
            else:
                return "odd_small"
        else:
            return "large"
    return "negative"
"""
        v1_analysis = analyzer.analyze(code=v1_code, language=Language.PYTHON)
        
        # Assert - V1 has high complexity and security issues
        v1_security_count = len(v1_analysis.results.security_findings)
        v1_complexity = v1_analysis.results.complexity.cyclomatic_complexity
        
        assert v1_security_count >= 1  # eval() usage
        assert v1_complexity >= 4  # Nested ifs
        
        # Act - Version 2: Improved code (removed eval, simplified logic)
        v2_code = """
def process(input_value):
    '''Process input value safely.'''
    if input_value <= 0:
        return "negative"
    elif input_value >= 10:
        return "large"
    elif input_value % 2 == 0:
        return "even_small"
    else:
        return "odd_small"
"""
        v2_analysis = analyzer.analyze(code=v2_code, language=Language.PYTHON)
        
        # Assert - V2 has no security issues (complexity may be similar due to elif chain)
        v2_security_count = len(v2_analysis.results.security_findings)
        v2_complexity = v2_analysis.results.complexity.cyclomatic_complexity
        
        assert v2_security_count == 0  # No eval() - security improved!
        assert v2_complexity <= v1_complexity  # Complexity same or better


@pytest.mark.integration
@pytest.mark.workflow
class TestRealWorldScenarios:
    """Test real-world usage scenarios."""
    
    def test_code_review_workflow(self):
        """Test complete code review workflow."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.value_objects import Language, Severity
        
        # Arrange - Reviewer analyzing pull request
        analyzer = CodeAnalyzer()
        pr_code = """
class PaymentProcessor:
    '''Process payments securely.'''
    
    def __init__(self, api_key):
        self.api_key = api_key
    
    def process_payment(self, amount, card_number):
        '''Process payment with credit card.'''
        # Validate amount
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # This line is too long and should be flagged by style checker for exceeding the 79 character limit
        payment_data = {'amount': amount, 'card': card_number, 'api_key': self.api_key}
        
        # Process payment
        return self._send_to_gateway(payment_data)
    
    def _send_to_gateway(self, data):
        '''Send payment to gateway.'''
        # Mock implementation
        return {'status': 'success', 'transaction_id': '12345'}
"""
        
        # Act - Reviewer runs full analysis
        analysis = analyzer.analyze(code=pr_code, language=Language.PYTHON)
        
        # Assert - Comprehensive review information
        # Structure: should find class and methods
        structures = analysis.results.structures
        assert len(structures) >= 3
        
        # Complexity: should calculate metrics
        assert analysis.results.complexity.cyclomatic_complexity >= 1
        
        # Security: should be clean (no eval/exec)
        critical_security = [
            f for f in analysis.results.security_findings 
            if f.severity == Severity.CRITICAL
        ]
        assert len(critical_security) == 0
        
        # Style: should flag long line
        assert len(analysis.results.style_issues) >= 1
    
    def test_ci_pipeline_workflow(self):
        """Test CI/CD pipeline integration workflow."""
        from domain.services.code_analyzer import CodeAnalyzer
        from domain.entities.analysis_options import AnalysisOptions
        from domain.value_objects import Language, AnalysisStatus
        
        # Arrange - CI pipeline running automated checks
        analyzer = CodeAnalyzer()
        options = AnalysisOptions(
            include_structure=True,
            include_complexity=True,
            include_security=True,
            include_style=True
        )
        
        # Simulated CI pipeline files
        files = {
            "src/main.py": "def main():\n    print('Hello')\n\nif __name__ == '__main__':\n    main()",
            "src/utils.py": "def helper():\n    return True",
            "tests/test_main.py": "def test_main():\n    assert True"
        }
        
        # Act - CI analyzes all files
        pipeline_results = []
        for filepath, code in files.items():
            analysis = analyzer.analyze(code=code, language=Language.PYTHON, options=options)
            pipeline_results.append({
                'file': filepath,
                'status': analysis.status,
                'passed': analysis.status == AnalysisStatus.COMPLETED,
                'security_issues': len(analysis.results.security_findings) if analysis.results else 0
            })
        
        # Assert - All files passed analysis
        assert all(r['passed'] for r in pipeline_results)
        
        # Assert - No security issues found
        total_security_issues = sum(r['security_issues'] for r in pipeline_results)
        assert total_security_issues == 0

