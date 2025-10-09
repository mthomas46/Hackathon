"""Test configuration and fixtures for code-analyzer service."""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any
from faker import Faker

# Add service path for imports
service_path = Path(__file__).parent.parent
sys.path.insert(0, str(service_path))

# Add shared services path
shared_path = Path(__file__).parent.parent.parent / "shared"
sys.path.insert(0, str(shared_path))

# Initialize Faker for test data
fake = Faker()


# ===== Sample Code Fixtures =====

@pytest.fixture
def simple_python_function() -> str:
    """Fixture providing a simple Python function for testing."""
    return """
def calculate_total(items):
    '''Calculate the total price of items.'''
    total = 0
    for item in items:
        total += item.price
    return total
"""


@pytest.fixture
def python_class_code() -> str:
    """Fixture providing a Python class for testing."""
    return """
class ShoppingCart:
    '''A shopping cart for managing items.'''
    
    def __init__(self):
        self.items = []
    
    def add_item(self, item):
        '''Add an item to the cart.'''
        self.items.append(item)
    
    def get_total(self):
        '''Calculate total price.'''
        return sum(item.price for item in self.items)
    
    def is_empty(self):
        '''Check if cart is empty.'''
        return len(self.items) == 0
"""


@pytest.fixture
def complex_python_code() -> str:
    """Fixture providing complex Python code with high cyclomatic complexity."""
    return """
def process_order(order, user, payment):
    '''Process an order with multiple conditions.'''
    if not order:
        return {'status': 'error', 'message': 'No order'}
    
    if not user.is_authenticated:
        return {'status': 'error', 'message': 'Not authenticated'}
    
    if user.is_banned:
        return {'status': 'error', 'message': 'User banned'}
    
    if order.total > user.credit_limit:
        return {'status': 'error', 'message': 'Exceeds credit limit'}
    
    if not payment.is_valid():
        return {'status': 'error', 'message': 'Invalid payment'}
    
    if payment.amount < order.total:
        return {'status': 'error', 'message': 'Insufficient payment'}
    
    if not order.items:
        return {'status': 'error', 'message': 'Empty order'}
    
    for item in order.items:
        if item.quantity <= 0:
            return {'status': 'error', 'message': 'Invalid quantity'}
        if item.price < 0:
            return {'status': 'error', 'message': 'Invalid price'}
    
    # Process payment
    if payment.process():
        order.status = 'confirmed'
        return {'status': 'success', 'order_id': order.id}
    else:
        return {'status': 'error', 'message': 'Payment failed'}
"""


@pytest.fixture
def code_with_security_issues() -> str:
    """Fixture providing code with potential security vulnerabilities."""
    return """
import os
import subprocess

def execute_command(user_input):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    
    # Command injection vulnerability
    result = os.system(f"ls {user_input}")
    
    # Eval vulnerability
    data = eval(user_input)
    
    # Hardcoded secrets
    api_key = "sk-1234567890abcdef"
    password = "admin123"
    
    return result
"""


# ===== Analysis Request Fixtures =====

@pytest.fixture
def basic_analysis_request() -> Dict[str, Any]:
    """Fixture for a basic code analysis request."""
    return {
        "code": "def hello():\n    return 'world'",
        "language": "python",
        "options": {
            "include_structures": True,
            "include_complexity": True,
            "include_style": True,
            "include_security": True,
            "include_patterns": True
        }
    }


@pytest.fixture
def minimal_analysis_request() -> Dict[str, Any]:
    """Fixture for minimal analysis request."""
    return {
        "code": "x = 1",
        "language": "python"
    }


# ===== Domain Entity Fixtures =====

@pytest.fixture
def sample_code_structure() -> Dict[str, Any]:
    """Fixture for a CodeStructure entity."""
    return {
        "type": "function",
        "name": "calculate_total",
        "line_start": 1,
        "line_end": 5,
        "docstring": "Calculate the total price.",
        "parameters": ["items"],
        "complexity": 3
    }


@pytest.fixture
def sample_complexity_metrics() -> Dict[str, Any]:
    """Fixture for ComplexityMetrics."""
    return {
        "cyclomatic_complexity": 5,
        "cognitive_complexity": 3,
        "maintainability_index": 75.5,
        "lines_of_code": 100,
        "comment_ratio": 0.15
    }


@pytest.fixture
def sample_security_finding() -> Dict[str, Any]:
    """Fixture for SecurityFinding."""
    return {
        "severity": "high",
        "vulnerability_type": "SQL Injection",
        "line_number": 10,
        "description": "Potential SQL injection vulnerability detected",
        "recommendation": "Use parameterized queries"
    }


# ===== API Testing Fixtures =====

@pytest.fixture
def api_client():
    """Fixture providing an HTTP client for API testing."""
    from httpx import AsyncClient
    return AsyncClient(base_url="http://localhost:8003")


@pytest.fixture
def mock_analysis_response() -> Dict[str, Any]:
    """Fixture for a complete analysis response."""
    return {
        "analysis_id": fake.uuid4(),
        "timestamp": fake.iso8601(),
        "language": "python",
        "structures": [
            {
                "type": "function",
                "name": "example_function",
                "line_start": 1,
                "line_end": 10,
                "parameters": ["param1", "param2"],
                "docstring": "Example function",
                "complexity": 3
            }
        ],
        "complexity": {
            "cyclomatic_complexity": 5,
            "cognitive_complexity": 3,
            "maintainability_index": 75.0,
            "lines_of_code": 50,
            "comment_ratio": 0.2
        },
        "style_issues": [],
        "security_findings": [],
        "patterns": ["factory"]
    }


# ===== Test Data Factories =====

@pytest.fixture
def analysis_factory():
    """Factory for creating CodeAnalysis test data."""
    def _create_analysis(
        code: str = None,
        language: str = "python",
        status: str = "pending"
    ):
        return {
            "analysis_id": fake.uuid4(),
            "code_content": code or "def test(): pass",
            "language": language,
            "timestamp": fake.iso8601(),
            "status": status
        }
    return _create_analysis


# ===== Cleanup Fixtures =====

@pytest.fixture(autouse=True)
def reset_test_state():
    """Auto-used fixture to reset state between tests."""
    # Setup
    yield
    # Teardown
    # Add any cleanup logic here


# ===== Performance Testing Fixtures =====

@pytest.fixture
def large_python_file() -> str:
    """Fixture providing a large Python file for performance testing."""
    functions = []
    for i in range(100):
        functions.append(f"""
def function_{i}(param):
    '''Function number {i}.'''
    result = param * {i}
    if result > 100:
        return result
    else:
        return result * 2
""")
    return "\n".join(functions)


# ===== Parametrize Helpers =====

# Language fixtures for parametrized tests
SUPPORTED_LANGUAGES = ["python", "javascript", "typescript"]

@pytest.fixture(params=SUPPORTED_LANGUAGES)
def language(request):
    """Parametrized fixture for testing across multiple languages."""
    return request.param


# ===== Markers Registration =====

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (slower)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (slowest)")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")


# ===== Test Output Customization =====

@pytest.fixture(autouse=True, scope="session")
def setup_test_environment():
    """Setup test environment once per session."""
    print("\n" + "="*70)
    print("🧪 Code Analyzer Test Suite")
    print("="*70)
    yield
    print("\n" + "="*70)
    print("✅ Test Suite Complete")
    print("="*70)
