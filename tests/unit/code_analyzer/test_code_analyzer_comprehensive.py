"""Comprehensive Code Analyzer Tests.

Tests for code analysis, quality assessment, security scanning, style checking,
and automated documentation generation in the LLM Documentation Ecosystem.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import json

# Adjust path for local imports
import sys
from pathlib import Path

# Add the Code Analyzer service directory to Python path
code_analyzer_path = Path(__file__).parent.parent.parent.parent / "services" / "code-analyzer"
sys.path.insert(0, str(code_analyzer_path))

from modules.core.code_analyzer import CodeAnalyzer
from modules.core.quality_scanner import QualityScanner
from modules.core.security_scanner import SecurityScanner
from modules.core.style_checker import StyleChecker
from modules.core.documentation_generator import DocumentationGenerator
from modules.models import AnalysisRequest, CodeAnalysisResult, SecurityFinding

# Test markers for parallel execution and categorization
pytestmark = [
    pytest.mark.unit,
    pytest.mark.parallel_safe,
    pytest.mark.code_analyzer
]


@pytest.fixture
def mock_llm_gateway():
    """Mock LLM Gateway for testing."""
    with patch('modules.core.code_analyzer.LLMGateway') as mock_gateway_class:
        mock_gateway = MagicMock()
        mock_gateway_class.return_value = mock_gateway

        # Mock code analysis responses
        mock_gateway.analyze_code = AsyncMock(return_value={
            "success": True,
            "analysis": {
                "complexity_score": 0.7,
                "maintainability_index": 0.8,
                "issues": ["Minor code style issue"],
                "recommendations": ["Improve variable naming"]
            }
        })

        mock_gateway.generate_documentation = AsyncMock(return_value={
            "success": True,
            "documentation": "# Code Documentation\n\nThis module provides authentication functionality.",
            "coverage": 0.85
        })

        yield mock_gateway


@pytest.fixture
def mock_file_system():
    """Mock file system operations."""
    with patch('modules.core.code_analyzer.FileSystem') as mock_fs_class:
        mock_fs = MagicMock()
        mock_fs_class.return_value = mock_fs

        mock_fs.read_file = AsyncMock(return_value="""
def authenticate_user(username, password):
    '''Authenticate a user with username and password.'''
    if not username or not password:
        return False

    # Check credentials against database
    user = get_user_from_db(username)
    if user and verify_password(password, user.password_hash):
        return True
    return False

def get_user_from_db(username):
    '''Retrieve user from database.'''
    # Database query logic here
    pass

def verify_password(password, password_hash):
    '''Verify password against hash.'''
    # Password verification logic here
    pass
""")

        mock_fs.list_files = AsyncMock(return_value=[
            "auth.py",
            "utils.py",
            "models.py",
            "__init__.py"
        ])

        yield mock_fs


@pytest.fixture
def code_analyzer(mock_llm_gateway, mock_file_system):
    """Create CodeAnalyzer instance for testing."""
    return CodeAnalyzer()


@pytest.fixture
def quality_scanner(mock_llm_gateway):
    """Create QualityScanner instance for testing."""
    return QualityScanner()


@pytest.fixture
def security_scanner():
    """Create SecurityScanner instance for testing."""
    return SecurityScanner()


@pytest.fixture
def style_checker():
    """Create StyleChecker instance for testing."""
    return StyleChecker()


@pytest.fixture
def documentation_generator(mock_llm_gateway):
    """Create DocumentationGenerator instance for testing."""
    return DocumentationGenerator()


class TestCodeAnalyzer:
    """Comprehensive tests for the core code analyzer."""

    def test_analyze_python_file(self, code_analyzer, mock_llm_gateway, mock_file_system):
        """Test analysis of Python source files."""
        file_path = "auth.py"

        result = code_analyzer.analyze_python_file(file_path)

        assert isinstance(result, dict)
        assert "success" in result
        assert "analysis" in result

        analysis = result["analysis"]
        assert "functions" in analysis
        assert "classes" in analysis
        assert "imports" in analysis
        assert "complexity_metrics" in analysis

        functions = analysis["functions"]
        assert len(functions) >= 3  # authenticate_user, get_user_from_db, verify_password

    def test_analyze_codebase_structure(self, code_analyzer, mock_file_system):
        """Test analysis of overall codebase structure."""
        project_path = "/path/to/project"

        structure = code_analyzer.analyze_codebase_structure(project_path)

        assert isinstance(structure, dict)
        assert "modules" in structure
        assert "dependencies" in structure
        assert "architecture_patterns" in structure
        assert "entry_points" in structure

    def test_extract_function_signatures(self, code_analyzer):
        """Test extraction of function signatures."""
        code = """
def authenticate_user(username: str, password: str) -> bool:
    pass

def get_user_from_db(username: str) -> Optional[User]:
    pass

async def verify_password(password: str, password_hash: str) -> bool:
    pass
"""

        signatures = code_analyzer.extract_function_signatures(code)

        assert isinstance(signatures, list)
        assert len(signatures) >= 3

        # Check function details
        auth_func = next((s for s in signatures if s.get("name") == "authenticate_user"), None)
        assert auth_func is not None
        assert "parameters" in auth_func
        assert "return_type" in auth_func
        assert auth_func["return_type"] == "bool"

    def test_extract_class_hierarchy(self, code_analyzer):
        """Test extraction of class hierarchy."""
        code = """
class BaseAuthenticator:
    def authenticate(self, credentials):
        pass

class OAuthAuthenticator(BaseAuthenticator):
    def authenticate(self, credentials):
        # OAuth authentication logic
        pass

class JWTAuthenticator(BaseAuthenticator):
    def authenticate(self, credentials):
        # JWT authentication logic
        pass
"""

        hierarchy = code_analyzer.extract_class_hierarchy(code)

        assert isinstance(hierarchy, dict)
        assert "classes" in hierarchy
        assert "inheritance" in hierarchy

        classes = hierarchy["classes"]
        assert len(classes) >= 3

        # Check inheritance relationships
        inheritance = hierarchy["inheritance"]
        assert "OAuthAuthenticator" in inheritance
        assert "JWTAuthenticator" in inheritance
        assert inheritance["OAuthAuthenticator"]["parent"] == "BaseAuthenticator"

    def test_analyze_code_dependencies(self, code_analyzer):
        """Test analysis of code dependencies."""
        code = """
import os
import sys
from pathlib import Path
from typing import Optional, List
from .models import User
from ..utils import validate_input
"""

        dependencies = code_analyzer.analyze_code_dependencies(code)

        assert isinstance(dependencies, dict)
        assert "imports" in dependencies
        assert "external_dependencies" in dependencies
        assert "internal_dependencies" in dependencies

        imports = dependencies["imports"]
        assert len(imports) >= 6

        # Check dependency categorization
        external_deps = dependencies["external_dependencies"]
        assert "os" in external_deps
        assert "pathlib" in external_deps

    def test_calculate_code_metrics(self, code_analyzer):
        """Test calculation of code quality metrics."""
        code = """
def simple_function():
    return "Hello"

def complex_function():
    result = []
    for i in range(10):
        if i % 2 == 0:
            for j in range(5):
                if j > 2:
                    result.append(i * j)
    return result
"""

        metrics = code_analyzer.calculate_code_metrics(code)

        assert isinstance(metrics, dict)
        assert "cyclomatic_complexity" in metrics
        assert "maintainability_index" in metrics
        assert "lines_of_code" in metrics
        assert "comment_ratio" in metrics

        # Complex function should have higher complexity
        assert metrics["cyclomatic_complexity"] >= 3

    def test_identify_code_patterns(self, code_analyzer):
        """Test identification of code patterns and anti-patterns."""
        code = """
# Good pattern - early return
def validate_input(data):
    if not data:
        return False
    if not isinstance(data, dict):
        return False
    return True

# Anti-pattern - nested conditionals
def process_data(data):
    if data:
        if data.get('type') == 'user':
            if data.get('active'):
                return process_user(data)
    return None
"""

        patterns = code_analyzer.identify_code_patterns(code)

        assert isinstance(patterns, dict)
        assert "good_patterns" in patterns
        assert "anti_patterns" in patterns
        assert "pattern_frequency" in patterns

        # Should identify early return as good pattern
        good_patterns = patterns["good_patterns"]
        assert any("early return" in pattern.lower() for pattern in good_patterns)

    def test_generate_code_summary(self, code_analyzer, mock_llm_gateway):
        """Test generation of code summaries."""
        code = """
class UserManager:
    '''Manages user operations.'''

    def __init__(self, db_connection):
        self.db = db_connection

    def create_user(self, username, email):
        '''Create a new user.'''
        # Validate input
        if not username or not email:
            raise ValueError("Username and email required")

        # Create user in database
        user_id = self.db.insert_user(username, email)
        return user_id

    def get_user(self, user_id):
        '''Retrieve user by ID.'''
        return self.db.get_user_by_id(user_id)

    def update_user(self, user_id, updates):
        '''Update user information.'''
        return self.db.update_user(user_id, updates)

    def delete_user(self, user_id):
        '''Delete user by ID.'''
        return self.db.delete_user(user_id)
"""

        summary = code_analyzer.generate_code_summary(code)

        assert isinstance(summary, dict)
        assert "summary" in summary
        assert "key_components" in summary
        assert "functionality_overview" in summary

        key_components = summary["key_components"]
        assert "UserManager" in str(key_components)

    def test_batch_code_analysis(self, code_analyzer, mock_file_system):
        """Test batch processing of multiple code files."""
        files = ["auth.py", "models.py", "utils.py"]

        batch_results = code_analyzer.batch_analyze_code(files)

        assert isinstance(batch_results, list)
        assert len(batch_results) == len(files)

        for result in batch_results:
            assert isinstance(result, dict)
            assert "file" in result
            assert "analysis" in result

    def test_code_analysis_with_context(self, code_analyzer):
        """Test code analysis with project context."""
        code = """
from .models import User
from .utils import validate_email

class UserService:
    def register_user(self, username, email):
        if not validate_email(email):
            raise ValueError("Invalid email")

        user = User(username=username, email=email)
        return self.save_user(user)
"""

        context = {
            "project_structure": ["models.py", "utils.py", "services.py"],
            "dependencies": ["flask", "sqlalchemy"],
            "coding_standards": ["pep8", "google_style"]
        }

        contextual_analysis = code_analyzer.analyze_code_with_context(code, context)

        assert isinstance(contextual_analysis, dict)
        assert "context_aware_analysis" in contextual_analysis
        assert "project_integration" in contextual_analysis

    def test_incremental_code_analysis(self, code_analyzer, mock_file_system):
        """Test incremental analysis of code changes."""
        # Simulate changed files
        changed_files = ["auth.py", "models.py"]

        # Previous analysis state
        previous_state = {
            "auth.py": {"functions": 5, "classes": 2},
            "models.py": {"functions": 3, "classes": 4}
        }

        incremental = code_analyzer.incremental_analyze_code(changed_files, previous_state)

        assert isinstance(incremental, dict)
        assert "changed_files_analysis" in incremental
        assert "impact_assessment" in incremental
        assert "regression_detection" in incremental


class TestQualityScanner:
    """Comprehensive tests for code quality scanning."""

    def test_scan_code_quality_comprehensive(self, quality_scanner):
        """Test comprehensive code quality scanning."""
        code = """
# Poor quality code with multiple issues
def badFunction(x,y,z):
    if x==None:
        print("x is none")
    elif y!=None:
        for i in range(len(z)):
            if z[i]>10:
                return z[i]*2
    else:
        return None
"""

        quality_report = quality_scanner.scan_code_quality(code)

        assert isinstance(quality_report, dict)
        assert "overall_score" in quality_report
        assert "issues" in quality_report
        assert "metrics" in quality_report
        assert "recommendations" in quality_report

        issues = quality_report["issues"]
        assert len(issues) > 0

        # Should detect multiple quality issues
        issue_types = [issue.get("type") for issue in issues]
        assert "naming" in str(issue_types).lower() or "style" in str(issue_types).lower()

    def test_quality_metrics_calculation(self, quality_scanner):
        """Test calculation of detailed quality metrics."""
        code = """
class Calculator:
    '''A simple calculator class.'''

    def __init__(self):
        self.result = 0

    def add(self, a: int, b: int) -> int:
        '''Add two numbers.'''
        return a + b

    def multiply(self, a: int, b: int) -> int:
        '''Multiply two numbers.'''
        return a * b
"""

        metrics = quality_scanner.calculate_quality_metrics(code)

        assert isinstance(metrics, dict)
        assert "readability_score" in metrics
        assert "maintainability_score" in metrics
        assert "testability_score" in metrics
        assert "documentation_score" in metrics

        # Well-structured code should have high scores
        assert metrics["readability_score"] > 0.7
        assert metrics["documentation_score"] > 0.8

    def test_identify_code_smells(self, quality_scanner):
        """Test identification of code smells and anti-patterns."""
        smelly_code = """
class GodClass:
    def __init__(self):
        self.data = []
        self.config = {}
        self.logger = None

    def process_data(self):
        # 50+ lines of processing logic
        pass

    def save_to_db(self):
        # Database logic
        pass

    def send_email(self):
        # Email logic
        pass

    def generate_report(self):
        # Report generation logic
        pass

def long_function():
    # 100+ lines of code
    pass
"""

        code_smells = quality_scanner.identify_code_smells(smelly_code)

        assert isinstance(code_smells, list)
        assert len(code_smells) > 0

        # Should detect large class and long method smells
        smell_types = [smell.get("type") for smell in code_smells]
        assert any("large class" in smell_type.lower() or "god class" in smell_type.lower()
                  for smell_type in smell_types)
        assert any("long method" in smell_type.lower() for smell_type in smell_types)

    def test_quality_benchmarking(self, quality_scanner):
        """Test quality benchmarking against standards."""
        quality_scores = {
            "readability": 0.85,
            "maintainability": 0.78,
            "testability": 0.92,
            "documentation": 0.88
        }

        benchmark = quality_scanner.benchmark_quality(quality_scores)

        assert isinstance(benchmark, dict)
        assert "benchmark_score" in benchmark
        assert "grade" in benchmark
        assert "industry_standards" in benchmark
        assert "improvement_areas" in benchmark

    def test_quality_trend_analysis(self, quality_scanner):
        """Test analysis of quality trends over time."""
        historical_quality = [
            {"date": "2024-01-01", "score": 0.7},
            {"date": "2024-01-08", "score": 0.75},
            {"date": "2024-01-15", "score": 0.8},
            {"date": "2024-01-22", "score": 0.85}
        ]

        trends = quality_scanner.analyze_quality_trends(historical_quality)

        assert isinstance(trends, dict)
        assert "trend_direction" in trends
        assert "improvement_rate" in trends
        assert "stability_score" in trends
        assert "forecasted_quality" in trends

        # Should show positive trend
        assert trends["trend_direction"] == "improving"

    def test_language_specific_quality_rules(self, quality_scanner):
        """Test language-specific quality rules."""
        python_code = """
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total
"""

        js_code = """
function calculateTotal(items) {
    let total = 0;
    for (let item of items) {
        total += item.price;
    }
    return total;
}
"""

        python_quality = quality_scanner.apply_language_specific_rules(python_code, "python")
        js_quality = quality_scanner.apply_language_specific_rules(js_code, "javascript")

        assert isinstance(python_quality, dict)
        assert isinstance(js_quality, dict)
        assert "language_specific_score" in python_quality
        assert "language_specific_score" in js_quality

    def test_quality_feedback_generation(self, quality_scanner):
        """Test generation of actionable quality feedback."""
        quality_data = {
            "overall_score": 0.65,
            "issues": [
                {"type": "naming", "severity": "medium", "location": "line 5"},
                {"type": "complexity", "severity": "high", "location": "function xyz"}
            ]
        }

        feedback = quality_scanner.generate_quality_feedback(quality_data)

        assert isinstance(feedback, dict)
        assert "actionable_feedback" in feedback
        assert "priority_actions" in feedback
        assert "estimated_effort" in feedback

        actionable_feedback = feedback["actionable_feedback"]
        assert len(actionable_feedback) > 0

        # Should include specific recommendations
        feedback_texts = [item.get("recommendation", "") for item in actionable_feedback]
        assert any("naming" in text.lower() for text in feedback_texts)


class TestSecurityScanner:
    """Comprehensive tests for security scanning functionality."""

    def test_scan_security_vulnerabilities(self, security_scanner):
        """Test scanning for security vulnerabilities."""
        vulnerable_code = """
# Vulnerable code with multiple security issues
def authenticate_user(username, password):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    execute_query(query)

def process_file_upload(file):
    # Path traversal vulnerability
    with open(file.filename, 'r') as f:
        content = f.read()
    return content

def hash_password(password):
    # Weak hashing
    import hashlib
    return hashlib.md5(password.encode()).hexdigest()
"""

        vulnerabilities = security_scanner.scan_security_vulnerabilities(vulnerable_code)

        assert isinstance(vulnerabilities, list)
        assert len(vulnerabilities) > 0

        # Should detect multiple vulnerability types
        vuln_types = [vuln.get("type") for vuln in vulnerabilities]
        assert any("sql injection" in vuln_type.lower() for vuln_type in vuln_types)
        assert any("path traversal" in vuln_type.lower() for vuln_type in vuln_types)

    def test_vulnerability_severity_assessment(self, security_scanner):
        """Test assessment of vulnerability severity."""
        vulnerability_data = {
            "type": "sql_injection",
            "location": "line 15",
            "code_context": "query = f\"SELECT * FROM users WHERE id = {user_id}\"",
            "potential_impact": "data_breach",
            "exploitability": "easy"
        }

        severity = security_scanner.assess_vulnerability_severity(vulnerability_data)

        assert isinstance(severity, dict)
        assert "severity_level" in severity
        assert "cvss_score" in severity
        assert "risk_assessment" in severity

        # SQL injection should be high severity
        assert severity["severity_level"] in ["high", "critical"]

    def test_security_recommendations_generation(self, security_scanner):
        """Test generation of security recommendations."""
        vulnerabilities = [
            {"type": "sql_injection", "severity": "high"},
            {"type": "weak_cryptography", "severity": "medium"},
            {"type": "path_traversal", "severity": "high"}
        ]

        recommendations = security_scanner.generate_security_recommendations(vulnerabilities)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Should include specific security recommendations
        recommendation_texts = [rec.get("recommendation", "") for rec in recommendations]
        assert any("parameterized queries" in text.lower() or "prepared statements" in text.lower()
                  for text in recommendation_texts)

    def test_compliance_checking(self, security_scanner):
        """Test compliance checking against security standards."""
        code_to_check = """
def handle_user_input(user_input):
    # Sanitize input
    sanitized = user_input.replace("'", "''")
    query = f"SELECT * FROM users WHERE name = '{sanitized}'"
    return execute_query(query)
"""

        compliance = security_scanner.check_compliance(code_to_check, ["owasp", "pci_dss"])

        assert isinstance(compliance, dict)
        assert "owasp_compliant" in compliance
        assert "pci_dss_compliant" in compliance
        assert "compliance_score" in compliance
        assert "violations" in compliance

    def test_dependency_security_analysis(self, security_scanner):
        """Test security analysis of dependencies."""
        dependencies = {
            "flask": "2.0.0",
            "requests": "2.25.0",  # Known vulnerability
            "sqlalchemy": "1.4.0"
        }

        dependency_analysis = security_scanner.analyze_dependency_security(dependencies)

        assert isinstance(dependency_analysis, dict)
        assert "vulnerable_dependencies" in dependency_analysis
        assert "security_score" in dependency_analysis
        assert "update_recommendations" in dependency_analysis

    def test_security_code_review(self, security_scanner):
        """Test automated security code review."""
        code_for_review = """
def login(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Dangerous: direct string interpolation
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)

    result = cursor.fetchone()
    conn.close()
    return result is not None
"""

        review_result = security_scanner.perform_security_code_review(code_for_review)

        assert isinstance(review_result, dict)
        assert "security_issues" in review_result
        assert "risk_level" in review_result
        assert "review_recommendations" in review_result

        security_issues = review_result["security_issues"]
        assert len(security_issues) > 0

    def test_security_testing_generation(self, security_scanner):
        """Test generation of security test cases."""
        vulnerable_function = {
            "name": "authenticate_user",
            "parameters": ["username", "password"],
            "vulnerabilities": ["sql_injection", "weak_authentication"]
        }

        security_tests = security_scanner.generate_security_tests(vulnerable_function)

        assert isinstance(security_tests, list)
        assert len(security_tests) > 0

        # Should include SQL injection and authentication tests
        test_descriptions = [test.get("description", "") for test in security_tests]
        assert any("sql injection" in desc.lower() for desc in test_descriptions)
        assert any("authentication" in desc.lower() for desc in test_descriptions)


class TestStyleChecker:
    """Comprehensive tests for code style checking."""

    def test_check_code_style_comprehensive(self, style_checker):
        """Test comprehensive code style checking."""
        style_violations = """
def badFunctionName(x,y,z):
    if x==5:
        return x*2
    elif y!=None:
        for i in range(10):
            if i>5:
                print(i)
    else:
        return None
"""

        style_report = style_checker.check_code_style(style_violations)

        assert isinstance(style_report, dict)
        assert "style_violations" in style_report
        assert "style_score" in style_report
        assert "formatting_issues" in style_report
        assert "naming_issues" in style_report

        violations = style_report["style_violations"]
        assert len(violations) > 0

        # Should detect multiple style issues
        violation_types = [v.get("type") for v in violations]
        assert any("naming" in str(violation_types).lower() for v_type in violation_types)

    def test_enforce_naming_conventions(self, style_checker):
        """Test enforcement of naming conventions."""
        naming_test_cases = [
            ("def badFunction()", "function_naming"),
            ("class badClassName:", "class_naming"),
            ("CONSTANT_VAR = 1", "constant_naming"),
            ("_private_var = 2", "private_var_naming")
        ]

        for code_snippet, expected_issue in naming_test_cases:
            naming_issues = style_checker.check_naming_conventions(code_snippet)
            assert isinstance(naming_issues, list)

            if expected_issue == "function_naming":
                assert len(naming_issues) > 0

    def test_format_code_consistency(self, style_checker):
        """Test checking of code formatting consistency."""
        inconsistent_formatting = """
def func1():
  return True

def func2():
    return False

def func3():
        return None
"""

        formatting_issues = style_checker.check_formatting_consistency(inconsistent_formatting)

        assert isinstance(formatting_issues, list)
        assert len(formatting_issues) > 0

        # Should detect indentation inconsistencies
        issue_types = [issue.get("type") for issue in formatting_issues]
        assert any("indentation" in str(issue_types).lower() for i_type in issue_types)

    def test_style_guide_compliance(self, style_checker):
        """Test compliance with style guides."""
        pep8_violations = """
def function(x,y,z):
    if x == 5:
        print("hello")
    else:
        print("world")
"""

        compliance = style_checker.check_style_guide_compliance(pep8_violations, "pep8")

        assert isinstance(compliance, dict)
        assert "compliant" in compliance
        assert "violations" in compliance
        assert "compliance_score" in compliance

        # Should detect PEP8 violations
        assert compliance["compliant"] is False
        assert len(compliance["violations"]) > 0

    def test_automatic_style_fixing(self, style_checker):
        """Test automatic fixing of style issues."""
        fixable_code = """
def hello   ( name ):
    if name== "world" :
        print ( "hello world" )
    return    "done"
"""

        fixed_code = style_checker.automatic_style_fixing(fixable_code)

        assert isinstance(fixed_code, dict)
        assert "fixed_code" in fixed_code
        assert "fixes_applied" in fixed_code
        assert "fix_success_rate" in fixed_code

        # Fixed code should be better formatted
        assert "def hello(name):" in fixed_code["fixed_code"] or "def hello (name):" not in fixable_code

    def test_custom_style_rules(self, style_checker):
        """Test application of custom style rules."""
        custom_rules = {
            "max_line_length": 80,
            "indent_style": "spaces",
            "quote_style": "double",
            "trailing_whitespace": "disallow"
        }

        code_to_check = """
def function(param):
    if param == "test":
        return "value"
    else:
        return None
"""

        custom_check = style_checker.apply_custom_style_rules(code_to_check, custom_rules)

        assert isinstance(custom_check, dict)
        assert "custom_violations" in custom_check
        assert "rules_applied" in custom_check

    def test_style_trend_analysis(self, style_checker):
        """Test analysis of style trends over time."""
        historical_style = [
            {"date": "2024-01-01", "score": 0.6},
            {"date": "2024-01-08", "score": 0.7},
            {"date": "2024-01-15", "score": 0.8},
            {"date": "2024-01-22", "score": 0.85}
        ]

        trends = style_checker.analyze_style_trends(historical_style)

        assert isinstance(trends, dict)
        assert "trend_direction" in trends
        assert "improvement_rate" in trends
        assert "consistency_score" in trends

        # Should show positive trend
        assert trends["trend_direction"] == "improving"


class TestDocumentationGenerator:
    """Comprehensive tests for documentation generation."""

    def test_generate_function_documentation(self, documentation_generator, mock_llm_gateway):
        """Test generation of function documentation."""
        function_code = """
def authenticate_user(username: str, password: str) -> bool:
    '''Authenticate a user with credentials.'''
    if not username or not password:
        return False

    user = get_user_from_db(username)
    if user and verify_password(password, user.password_hash):
        return True
    return False
"""

        function_doc = documentation_generator.generate_function_documentation(function_code)

        assert isinstance(function_doc, dict)
        assert "function_name" in function_doc
        assert "documentation" in function_doc
        assert "parameters" in function_doc
        assert "return_type" in function_doc

        assert function_doc["function_name"] == "authenticate_user"
        assert "Authenticate a user" in function_doc["documentation"]

    def test_generate_class_documentation(self, documentation_generator, mock_llm_gateway):
        """Test generation of class documentation."""
        class_code = """
class UserManager:
    '''Manages user operations in the system.'''

    def __init__(self, db_connection):
        '''Initialize with database connection.'''
        self.db = db_connection

    def create_user(self, username, email):
        '''Create a new user account.'''
        pass

    def get_user(self, user_id):
        '''Retrieve user by ID.'''
        pass
"""

        class_doc = documentation_generator.generate_class_documentation(class_code)

        assert isinstance(class_doc, dict)
        assert "class_name" in class_doc
        assert "documentation" in class_doc
        assert "methods" in class_doc
        assert "attributes" in class_doc

        assert class_doc["class_name"] == "UserManager"
        assert len(class_doc["methods"]) >= 3  # __init__, create_user, get_user

    def test_generate_api_documentation(self, documentation_generator, mock_llm_gateway):
        """Test generation of API documentation."""
        api_endpoints = [
            {"method": "GET", "path": "/users", "description": "Get all users"},
            {"method": "POST", "path": "/users", "description": "Create new user"},
            {"method": "GET", "path": "/users/{id}", "description": "Get user by ID"}
        ]

        api_doc = documentation_generator.generate_api_documentation(api_endpoints)

        assert isinstance(api_doc, dict)
        assert "api_documentation" in api_doc
        assert "endpoints" in api_doc
        assert "openapi_spec" in api_doc

        endpoints = api_doc["endpoints"]
        assert len(endpoints) == len(api_endpoints)

    def test_generate_codebase_overview(self, documentation_generator, mock_llm_gateway):
        """Test generation of codebase overview documentation."""
        codebase_info = {
            "modules": ["auth.py", "models.py", "utils.py", "api.py"],
            "main_components": ["UserManager", "APIRouter", "Database"],
            "architecture": "MVC pattern with REST API",
            "technologies": ["Python", "FastAPI", "SQLAlchemy"]
        }

        overview = documentation_generator.generate_codebase_overview(codebase_info)

        assert isinstance(overview, dict)
        assert "overview_documentation" in overview
        assert "architecture_diagram" in overview
        assert "module_descriptions" in overview
        assert "getting_started" in overview

    def test_generate_readme_documentation(self, documentation_generator):
        """Test generation of README documentation."""
        project_info = {
            "name": "User Authentication Service",
            "description": "Provides secure user authentication and authorization",
            "features": ["JWT authentication", "Role-based access", "Password hashing"],
            "installation": ["pip install -r requirements.txt", "python main.py"],
            "usage": ["POST /auth/login", "GET /users/profile"],
            "api_docs": "See /docs for detailed API documentation"
        }

        readme = documentation_generator.generate_readme_documentation(project_info)

        assert isinstance(readme, dict)
        assert "readme_content" in readme
        assert "sections" in readme

        sections = readme["sections"]
        assert "Installation" in sections
        assert "Usage" in sections
        assert "Features" in sections

    def test_generate_inline_documentation(self, documentation_generator):
        """Test generation of inline code documentation."""
        undocumented_code = """
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price * item.quantity
    return total

class OrderProcessor:
    def process_order(self, order):
        # Process the order
        return validate_and_save(order)
"""

        inline_docs = documentation_generator.generate_inline_documentation(undocumented_code)

        assert isinstance(inline_docs, dict)
        assert "documented_code" in inline_docs
        assert "documentation_added" in inline_docs
        assert "functions_documented" in inline_docs

        # Should add docstrings and comments
        documented_code = inline_docs["documented_code"]
        assert '"""' in documented_code or "'''" in documented_code

    def test_generate_integration_guides(self, documentation_generator):
        """Test generation of integration guides."""
        service_info = {
            "service_name": "Authentication Service",
            "endpoints": ["/auth/login", "/auth/refresh", "/users/profile"],
            "authentication": "JWT Bearer token",
            "rate_limits": "100 requests per minute",
            "error_handling": "Standard HTTP status codes"
        }

        integration_guide = documentation_generator.generate_integration_guide(service_info)

        assert isinstance(integration_guide, dict)
        assert "integration_guide" in integration_guide
        assert "setup_instructions" in integration_guide
        assert "authentication_guide" in integration_guide
        assert "api_examples" in integration_guide

    def test_generate_troubleshooting_docs(self, documentation_generator):
        """Test generation of troubleshooting documentation."""
        error_patterns = [
            {"error": "Invalid credentials", "solution": "Check username/password format"},
            {"error": "Token expired", "solution": "Refresh token using /auth/refresh"},
            {"error": "Rate limit exceeded", "solution": "Implement exponential backoff"}
        ]

        troubleshooting = documentation_generator.generate_troubleshooting_docs(error_patterns)

        assert isinstance(troubleshooting, dict)
        assert "troubleshooting_guide" in troubleshooting
        assert "common_errors" in troubleshooting
        assert "diagnostic_steps" in troubleshooting

    def test_documentation_quality_assessment(self, documentation_generator):
        """Test assessment of documentation quality."""
        documentation = """
# User Authentication API

## Overview
This API provides user authentication functionality.

## Endpoints

### POST /auth/login
Authenticates user credentials.

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "token": "jwt_token",
  "expires_in": 3600
}
```
"""

        quality = documentation_generator.assess_documentation_quality(documentation)

        assert isinstance(quality, dict)
        assert "quality_score" in quality
        assert "completeness_score" in quality
        assert "clarity_score" in quality
        assert "structure_score" in quality

        # Well-structured docs should have high scores
        assert quality["quality_score"] > 0.7

    def test_documentation_update_tracking(self, documentation_generator):
        """Test tracking of documentation updates."""
        code_changes = [
            {"file": "auth.py", "change": "Added MFA support", "date": "2024-01-15"},
            {"file": "api.py", "change": "New endpoint /auth/mfa", "date": "2024-01-16"}
        ]

        update_tracking = documentation_generator.track_documentation_updates(code_changes)

        assert isinstance(update_tracking, dict)
        assert "documentation_updates" in update_tracking
        assert "outdated_sections" in update_tracking
        assert "update_recommendations" in update_tracking

    def test_multilingual_documentation_generation(self, documentation_generator):
        """Test generation of multilingual documentation."""
        base_content = "User authentication functionality"

        multilingual = documentation_generator.generate_multilingual_documentation(
            base_content,
            languages=["es", "fr", "de"]
        )

        assert isinstance(multilingual, dict)
        assert "translations" in multilingual
        assert "base_language" in multilingual

        translations = multilingual["translations"]
        assert len(translations) >= 3  # es, fr, de

        # Each translation should be different
        for lang_code, translated_content in translations.items():
            assert translated_content != base_content
