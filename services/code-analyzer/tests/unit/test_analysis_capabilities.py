"""Unit Tests for Analysis Capabilities in Code Analyzer Service.

This module tests analysis capabilities including:
- Code structure analysis and AST parsing
- Function and class extraction
- Design pattern recognition
- Complexity analysis and metrics calculation
- Security vulnerability detection
- Code quality assessment

Tests cover the complete analysis infrastructure within the Code Analyzer service.
"""

import pytest
import ast
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

from main import AnalysisRequest, CodeAnalysisResponse


class TestAnalysisCapabilities:
    """Test Analysis Capabilities functionality."""

    @pytest.fixture
    def analysis_processor(self):
        """Create analysis processor instance with test configuration."""
        from main import AnalysisProcessor
        return AnalysisProcessor()

    @pytest.fixture
    def sample_python_code(self):
        """Sample Python code for analysis testing."""
        return """
class UserService:
    '''Service for managing user operations.'''

    def __init__(self, db_connection):
        self.db = db_connection
        self._cache = {}

    def get_user(self, user_id: int) -> Dict[str, Any]:
        '''Retrieve user by ID with caching.'''
        if user_id in self._cache:
            return self._cache[user_id]

        user = self.db.query("SELECT * FROM users WHERE id = ?", user_id)
        self._cache[user_id] = user
        return user

    def create_user(self, user_data: Dict[str, Any]) -> int:
        '''Create a new user and return ID.'''
        # Validate input
        if not user_data.get('email'):
            raise ValueError("Email is required")

        # Insert user
        user_id = self.db.insert("INSERT INTO users (email, name) VALUES (?, ?)",
                               user_data['email'], user_data['name'])

        # Clear cache
        self._cache.clear()

        return user_id

    def update_user(self, user_id: int, updates: Dict[str, Any]) -> bool:
        '''Update user information.'''
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [user_id]

        result = self.db.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
        self._cache.clear()

        return result.rowcount > 0

    @staticmethod
    def validate_email(email: str) -> bool:
        '''Validate email format.'''
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

class SingletonMeta(type):
    '''Singleton metaclass for implementing singleton pattern.'''

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class DatabaseConnection(metaclass=SingletonMeta):
    '''Database connection using singleton pattern.'''

    def __init__(self):
        self._connection = None

    def connect(self):
        '''Establish database connection.'''
        # Connection logic here
        pass

def factory_function(service_type: str) -> Any:
    '''Factory function for creating service instances.'''
    services = {
        'user': UserService,
        'database': DatabaseConnection,
    }

    service_class = services.get(service_type)
    if not service_class:
        raise ValueError(f"Unknown service type: {service_type}")

    return service_class()
"""

    @pytest.fixture
    def sample_javascript_code(self):
        """Sample JavaScript code for analysis testing."""
        return """
class ApiService {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.cache = new Map();
    }

    async get(endpoint) {
        const cacheKey = `GET:${endpoint}`;

        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`);
            const data = await response.json();
            this.cache.set(cacheKey, data);
            return data;
        } catch (error) {
            console.error(`API call failed: ${error.message}`);
            throw error;
        }
    }

    async post(endpoint, data) {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    }
}

function validateEmail(email) {
    const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return pattern.test(email);
}

const SingletonMixin = (Base) => class extends Base {
    static instance = null;

    static getInstance(...args) {
        if (!this.instance) {
            this.instance = new this(...args);
        }
        return this.instance;
    }
};

const ConfigManager = SingletonMixin(class {
    constructor() {
        this.config = {};
    }

    loadConfig(configData) {
        this.config = { ...this.config, ...configData };
    }

    get(key) {
        return this.config[key];
    }
});

function createService(type) {
    const services = {
        api: ApiService,
        config: ConfigManager
    };

    const ServiceClass = services[type];
    if (!ServiceClass) {
        throw new Error(`Unknown service type: ${type}`);
    }

    return ServiceClass;
}
"""

    @pytest.fixture
    def complex_analysis_request(self):
        """Create a complex analysis request."""
        return AnalysisRequest(
            code="""
def authenticate_user(username, password):
    if not username or not password:
        return False

    user = db.query('SELECT * FROM users WHERE username = ?', username)
    if not user:
        return False

    # Simple password check (NOT secure - for demo only)
    if user['password'] == password:
        return True

    return False

class DataProcessor:
    def __init__(self):
        self.data = []

    def process(self, input_data):
        for item in input_data:
            # Potential SQL injection vulnerability
            query = f"SELECT * FROM table WHERE id = {item['id']}"
            result = db.execute(query)
            self.data.append(result)

    def get_results(self):
        return self.data
""",
            language="python",
            include_functions=True,
            include_classes=True,
            include_patterns=True,
            include_security=True,
            include_complexity=True,
            include_style=True
        )

    def test_python_code_structure_analysis(self, analysis_processor, sample_python_code):
        """Test Python code structure analysis."""
        request = AnalysisRequest(
            code=sample_python_code,
            language="python",
            include_functions=True,
            include_classes=True
        )

        result = analysis_processor.analyze_code(request)

        assert result.success is True
        assert "functions" in result.analysis
        assert "classes" in result.analysis

        # Verify function extraction
        functions = result.analysis["functions"]
        function_names = [f["name"] for f in functions]
        assert "get_user" in function_names
        assert "create_user" in function_names
        assert "update_user" in function_names
        assert "validate_email" in function_names

        # Verify class extraction
        classes = result.analysis["classes"]
        class_names = [c["name"] for c in classes]
        assert "UserService" in class_names
        assert "DatabaseConnection" in class_names

    def test_design_pattern_recognition(self, analysis_processor, sample_python_code):
        """Test design pattern recognition capabilities."""
        request = AnalysisRequest(
            code=sample_python_code,
            language="python",
            include_patterns=True
        )

        result = analysis_processor.analyze_code(request)

        assert result.success is True
        assert "patterns" in result.analysis

        patterns = result.analysis["patterns"]
        pattern_names = [p["name"] for p in patterns]

        # Should identify singleton and factory patterns
        assert any("singleton" in name.lower() for name in pattern_names)
        assert any("factory" in name.lower() for name in pattern_names)

        # Verify pattern details
        singleton_pattern = next((p for p in patterns if "singleton" in p["name"].lower()), None)
        if singleton_pattern:
            assert "confidence" in singleton_pattern
            assert "locations" in singleton_pattern

    def test_complexity_analysis(self, analysis_processor, sample_python_code):
        """Test code complexity analysis."""
        request = AnalysisRequest(
            code=sample_python_code,
            language="python",
            include_complexity=True
        )

        result = analysis_processor.analyze_code(request)

        assert result.success is True
        assert "complexity" in result.analysis

        complexity = result.analysis["complexity"]
        assert "cyclomatic_complexity" in complexity
        assert "cognitive_complexity" in complexity
        assert "overall_score" in complexity

        # Verify complexity scores are reasonable
        assert 0 <= complexity["overall_score"] <= 10

    def test_security_vulnerability_detection(self, analysis_processor, complex_analysis_request):
        """Test security vulnerability detection."""
        result = analysis_processor.analyze_code(complex_analysis_request)

        assert result.success is True
        assert "security" in result.analysis

        security = result.analysis["security"]
        assert "vulnerabilities" in security
        assert "risk_score" in security
        assert "recommendations" in security

        vulnerabilities = security["vulnerabilities"]

        # Should detect insecure password handling
        password_vulns = [v for v in vulnerabilities if "password" in v.get("description", "").lower()]
        assert len(password_vulns) > 0

        # Should detect SQL injection vulnerability
        sql_vulns = [v for v in vulnerabilities if "sql" in v.get("description", "").lower()]
        assert len(sql_vulns) > 0

    def test_code_quality_assessment(self, analysis_processor, sample_python_code):
        """Test code quality assessment."""
        request = AnalysisRequest(
            code=sample_python_code,
            language="python",
            include_style=True
        )

        result = analysis_processor.analyze_code(request)

        assert result.success is True
        assert "style" in result.analysis

        style = result.analysis["style"]
        assert "score" in style
        assert "issues" in style
        assert "recommendations" in style

        # Verify quality score is reasonable
        assert 0.0 <= style["score"] <= 1.0

    def test_javascript_code_analysis(self, analysis_processor, sample_javascript_code):
        """Test JavaScript code analysis capabilities."""
        request = AnalysisRequest(
            code=sample_javascript_code,
            language="javascript",
            include_functions=True,
            include_classes=True,
            include_patterns=True
        )

        result = analysis_processor.analyze_code(request)

        assert result.success is True
        assert "functions" in result.analysis
        assert "classes" in result.analysis

        # Verify JavaScript function extraction
        functions = result.analysis["functions"]
        function_names = [f["name"] for f in functions]
        assert "get" in function_names
        assert "post" in function_names
        assert "validateEmail" in function_names

        # Verify JavaScript class extraction
        classes = result.analysis["classes"]
        class_names = [c["name"] for c in classes]
        assert "ApiService" in class_names
        assert "ConfigManager" in class_names

    def test_language_support_validation(self, analysis_processor):
        """Test language support validation."""
        supported_languages = ["python", "javascript", "java", "csharp"]

        for language in supported_languages:
            request = AnalysisRequest(
                code="def test(): pass",
                language=language,
                include_functions=True
            )

            # Should not raise exception for supported languages
            result = analysis_processor.analyze_code(request)
            assert result is not None

        # Test unsupported language
        request = AnalysisRequest(
            code="def test(): pass",
            language="unsupported_lang",
            include_functions=True
        )

        result = analysis_processor.analyze_code(request)
        assert result.success is False
        assert "unsupported" in str(result.error).lower()

    def test_analysis_configuration_options(self, analysis_processor, sample_python_code):
        """Test analysis configuration options."""
        # Test with all options enabled
        full_request = AnalysisRequest(
            code=sample_python_code,
            language="python",
            include_functions=True,
            include_classes=True,
            include_patterns=True,
            include_security=True,
            include_complexity=True,
            include_style=True
        )

        full_result = analysis_processor.analyze_code(full_request)

        # Should include all analysis types
        expected_keys = ["functions", "classes", "patterns", "security", "complexity", "style"]
        for key in expected_keys:
            assert key in full_result.analysis

        # Test with minimal options
        minimal_request = AnalysisRequest(
            code=sample_python_code,
            language="python",
            include_functions=True,
            include_classes=False,
            include_patterns=False,
            include_security=False,
            include_complexity=False,
            include_style=False
        )

        minimal_result = analysis_processor.analyze_code(minimal_request)

        # Should only include functions
        assert "functions" in minimal_result.analysis
        assert "classes" not in minimal_result.analysis
        assert "patterns" not in minimal_result.analysis

    def test_error_handling_and_recovery(self, analysis_processor):
        """Test error handling and recovery mechanisms."""
        # Test with invalid Python code
        invalid_code = """
def broken_function(
    return "incomplete"
"""

        request = AnalysisRequest(
            code=invalid_code,
            language="python",
            include_functions=True
        )

        result = analysis_processor.analyze_code(request)

        # Should handle syntax errors gracefully
        assert result.success is False
        assert "error" in result.__dict__ or "error" in str(result).lower()

        # Test with empty code
        empty_request = AnalysisRequest(
            code="",
            language="python",
            include_functions=True
        )

        empty_result = analysis_processor.analyze_code(empty_request)

        # Should handle empty code gracefully
        assert empty_result.success is True
        assert "functions" in empty_result.analysis
        assert len(empty_result.analysis["functions"]) == 0

    def test_performance_metrics_collection(self, analysis_processor, sample_python_code):
        """Test performance metrics collection during analysis."""
        request = AnalysisRequest(
            code=sample_python_code,
            language="python",
            include_functions=True,
            include_classes=True,
            include_patterns=True,
            include_complexity=True
        )

        start_time = datetime.now()
        result = analysis_processor.analyze_code(request)
        end_time = datetime.now()

        # Verify analysis completed successfully
        assert result.success is True

        # Verify reasonable performance
        processing_time = (end_time - start_time).total_seconds()
        assert processing_time < 5.0  # Should complete within 5 seconds

        # Check if performance metrics are included
        if hasattr(result, 'metadata'):
            assert "processing_time_seconds" in result.metadata
            assert result.metadata["processing_time_seconds"] > 0

    def test_analysis_result_consistency(self, analysis_processor, sample_python_code):
        """Test analysis result consistency across multiple runs."""
        request = AnalysisRequest(
            code=sample_python_code,
            language="python",
            include_functions=True,
            include_classes=True
        )

        # Run analysis multiple times
        results = []
        for _ in range(3):
            result = analysis_processor.analyze_code(request)
            results.append(result)

        # All results should be consistent
        first_result = results[0]

        for result in results[1:]:
            assert result.success == first_result.success

            # Function count should be consistent
            if "functions" in result.analysis and "functions" in first_result.analysis:
                assert len(result.analysis["functions"]) == len(first_result.analysis["functions"])

            # Class count should be consistent
            if "classes" in result.analysis and "classes" in first_result.analysis:
                assert len(result.analysis["classes"]) == len(first_result.analysis["classes"])

    @pytest.mark.parametrize("language,code_snippet,expected_functions", [
        ("python", "def hello(): pass", ["hello"]),
        ("python", "def func1(): pass\ndef func2(): pass", ["func1", "func2"]),
        ("javascript", "function hello() {}", ["hello"]),
        ("javascript", "const func1 = () => {}; function func2() {}", ["func1", "func2"]),
    ])
    def test_function_extraction_parametrized(self, analysis_processor, language, code_snippet, expected_functions):
        """Test function extraction with parametrized test cases."""
        request = AnalysisRequest(
            code=code_snippet,
            language=language,
            include_functions=True
        )

        result = analysis_processor.analyze_code(request)

        assert result.success is True
        assert "functions" in result.analysis

        function_names = [f["name"] for f in result.analysis["functions"]]

        for expected_func in expected_functions:
            assert expected_func in function_names

    def test_analysis_metadata_enrichment(self, analysis_processor, sample_python_code):
        """Test analysis metadata enrichment."""
        request = AnalysisRequest(
            code=sample_python_code,
            language="python",
            include_functions=True,
            include_classes=True,
            include_patterns=True
        )

        result = analysis_processor.analyze_code(request)

        assert result.success is True

        # Verify analysis metadata
        assert hasattr(result, 'metadata')
        metadata = result.metadata

        assert "language" in metadata
        assert metadata["language"] == "python"

        assert "code_length" in metadata
        assert metadata["code_length"] == len(sample_python_code)

        assert "analysis_timestamp" in metadata

        assert "analysis_version" in metadata

    def test_large_codebase_analysis(self, analysis_processor):
        """Test analysis of large codebases."""
        # Create a large codebase with multiple files/modules
        large_codebase = "\n\n".join([
            f"""
class Module{i}:
    def method_{j}(self):
        return {j}

def function_{i}():
    return Module{i}()
""" for i in range(10) for j in range(5)
        ])

        request = AnalysisRequest(
            code=large_codebase,
            language="python",
            include_functions=True,
            include_classes=True
        )

        result = analysis_processor.analyze_code(request)

        assert result.success is True

        # Should handle large codebases efficiently
        functions = result.analysis.get("functions", [])
        classes = result.analysis.get("classes", [])

        assert len(functions) >= 10  # At least 10 functions
        assert len(classes) >= 10    # At least 10 classes

    def test_incremental_analysis_workflow(self, analysis_processor):
        """Test incremental analysis workflow."""
        # Start with basic code
        base_code = """
class BaseService:
    def process(self):
        return 'base'
"""

        base_request = AnalysisRequest(
            code=base_code,
            language="python",
            include_classes=True
        )

        base_result = analysis_processor.analyze_code(base_request)
        assert base_result.success is True
        assert len(base_result.analysis["classes"]) == 1

        # Add more code incrementally
        extended_code = base_code + """

class ExtendedService(BaseService):
    def advanced_process(self):
        base_result = super().process()
        return f'extended: {base_result}'
"""

        extended_request = AnalysisRequest(
            code=extended_code,
            language="python",
            include_classes=True
        )

        extended_result = analysis_processor.analyze_code(extended_request)
        assert extended_result.success is True
        assert len(extended_result.analysis["classes"]) == 2

        # Verify inheritance relationships
        classes = extended_result.analysis["classes"]
        extended_service = next(c for c in classes if c["name"] == "ExtendedService")
        assert "parent_classes" in extended_service
        assert "BaseService" in extended_service["parent_classes"]
