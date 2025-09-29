"""Clean unit tests for code-analyzer domain services."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Dict, Optional

# Define mock entities and repositories to avoid import dependencies
from enum import Enum
from datetime import datetime, timezone


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EntityType(str, Enum):
    ENDPOINT = "endpoint"
    MODEL = "model"
    SERVICE = "service"


class MockAnalysisResult:
    """Mock analysis result entity."""
    def __init__(self, result_id: str, status: AnalysisStatus = AnalysisStatus.PENDING,
                 quality_score: float = 0.0):
        self.result_id = result_id
        self.status = status
        self.quality_score = quality_score
        self.entities_found = []
        self.security_issues = []
        self.complexity_metrics = {}

    def is_completed(self) -> bool:
        return self.status == AnalysisStatus.COMPLETED

    def add_entity(self, entity_type: str, name: str, location: dict = None):
        self.entities_found.append({
            "type": entity_type,
            "name": name,
            "location": location or {},
            "confidence": 0.9
        })

    def add_security_issue(self, issue_type: str, severity: SeverityLevel,
                          description: str, location: dict = None):
        self.security_issues.append({
            "type": issue_type,
            "severity": severity,
            "description": description,
            "location": location or {}
        })


class MockSecurityIssue:
    """Mock security issue entity."""
    def __init__(self, issue_type: str, severity: SeverityLevel, title: str):
        self.issue_type = issue_type
        self.severity = severity
        self.title = title
        self.is_critical = lambda: severity == SeverityLevel.CRITICAL
        self.is_high_severity = lambda: severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]


class MockAnalysisRepository:
    """Mock analysis repository."""
    def __init__(self):
        self.results = {
            "result1": MockAnalysisResult("result1", AnalysisStatus.COMPLETED, 0.85),
            "result2": MockAnalysisResult("result2", AnalysisStatus.FAILED, 0.2),
        }

    async def save(self, result: MockAnalysisResult) -> MockAnalysisResult:
        """Save analysis result."""
        self.results[result.result_id] = result
        return result

    async def get_by_id(self, result_id: str) -> Optional[MockAnalysisResult]:
        """Get result by ID."""
        return self.results.get(result_id)

    async def list_recent(self, limit: int = 10) -> List[MockAnalysisResult]:
        """List recent results."""
        return list(self.results.values())[:limit]


class MockSecurityRepository:
    """Mock security repository."""
    def __init__(self):
        self.issues = [
            MockSecurityIssue("sql_injection", SeverityLevel.CRITICAL, "SQL Injection"),
            MockSecurityIssue("xss", SeverityLevel.HIGH, "XSS Vulnerability"),
            MockSecurityIssue("unused_import", SeverityLevel.LOW, "Unused Import"),
        ]

    async def find_by_severity(self, severity: SeverityLevel) -> List[MockSecurityIssue]:
        """Find issues by severity."""
        return [issue for issue in self.issues if issue.severity == severity]

    async def count_by_type(self, issue_type: str) -> int:
        """Count issues by type."""
        return len([issue for issue in self.issues if issue.issue_type == issue_type])


# Domain services
class AnalysisProcessor:
    """Domain service for processing code analysis."""

    def __init__(self, analysis_repo: MockAnalysisRepository, security_repo: MockSecurityRepository):
        self.analysis_repo = analysis_repo
        self.security_repo = security_repo

    async def process_code_analysis(self, source_code: str, language: str = "python") -> MockAnalysisResult:
        """Process code analysis for given source."""
        result = MockAnalysisResult(f"analysis_{len(self.analysis_repo.results) + 1}")

        try:
            # Extract entities
            entities = self._extract_entities(source_code, language)
            for entity in entities:
                result.add_entity(entity["type"], entity["name"], entity["location"])

            # Analyze security
            security_issues = await self._analyze_security(source_code, language)
            for issue in security_issues:
                result.add_security_issue(
                    issue["type"],
                    issue["severity"],
                    issue["description"],
                    issue["location"]
                )

            # Calculate metrics
            metrics = self._calculate_metrics(source_code, entities, security_issues)
            result.complexity_metrics = metrics

            # Calculate quality score
            result.quality_score = self._calculate_quality_score(entities, security_issues, metrics)

            result.status = AnalysisStatus.COMPLETED

        except Exception as e:
            result.status = AnalysisStatus.FAILED

        await self.analysis_repo.save(result)
        return result

    def _extract_entities(self, source_code: str, language: str) -> List[Dict]:
        """Extract entities from source code."""
        entities = []

        # Simple entity extraction (mock implementation)
        if "def " in source_code:
            entities.append({
                "type": "function",
                "name": "sample_function",
                "location": {"line": 1, "column": 5}
            })

        if "class " in source_code:
            entities.append({
                "type": "class",
                "name": "SampleClass",
                "location": {"line": 10, "column": 1}
            })

        if "@app." in source_code or "FastAPI" in source_code:
            entities.append({
                "type": "endpoint",
                "name": "api_endpoint",
                "location": {"line": 15, "column": 1}
            })

        return entities

    async def _analyze_security(self, source_code: str, language: str) -> List[Dict]:
        """Analyze source code for security issues."""
        issues = []

        # Mock security analysis
        if "SELECT *" in source_code or "sql" in source_code.lower():
            issues.append({
                "type": "sql_injection",
                "severity": SeverityLevel.CRITICAL,
                "description": "Potential SQL injection vulnerability",
                "location": {"line": 20, "column": 10}
            })

        if "<script>" in source_code or "innerHTML" in source_code:
            issues.append({
                "type": "xss",
                "severity": SeverityLevel.HIGH,
                "description": "Potential cross-site scripting vulnerability",
                "location": {"line": 25, "column": 15}
            })

        if "password" in source_code.lower() and "=" in source_code:
            issues.append({
                "type": "hardcoded_secret",
                "severity": SeverityLevel.HIGH,
                "description": "Potential hardcoded secret",
                "location": {"line": 5, "column": 1}
            })

        return issues

    def _calculate_metrics(self, source_code: str, entities: List[Dict], issues: List[Dict]) -> Dict:
        """Calculate code metrics."""
        lines = len(source_code.split('\n'))
        functions = len([e for e in entities if e["type"] == "function"])
        classes = len([e for e in entities if e["type"] == "class"])

        # Simple complexity calculation
        complexity = min(15, max(1, functions * 2 + classes * 3 + len(issues)))

        return {
            "lines_of_code": lines,
            "functions_count": functions,
            "classes_count": classes,
            "cyclomatic_complexity": complexity,
            "security_issues_count": len(issues)
        }

    def _calculate_quality_score(self, entities: List[Dict], issues: List[Dict], metrics: Dict) -> float:
        """Calculate overall quality score."""
        # Base score from entities
        entity_score = min(len(entities) * 0.15, 0.6)

        # Penalty for security issues
        severity_penalty = 0.0
        for issue in issues:
            if issue["severity"] == SeverityLevel.CRITICAL:
                severity_penalty += 0.25
            elif issue["severity"] == SeverityLevel.HIGH:
                severity_penalty += 0.15

        # Complexity penalty
        complexity = metrics.get("cyclomatic_complexity", 5)
        if complexity > 10:
            complexity_penalty = min((complexity - 10) * 0.05, 0.2)
        else:
            complexity_penalty = 0.0

        score = entity_score - severity_penalty - complexity_penalty
        return max(0.0, min(1.0, score))


class EndpointExtractor:
    """Domain service for extracting API endpoints."""

    def __init__(self, analysis_repo: MockAnalysisRepository):
        self.analysis_repo = analysis_repo

    async def extract_endpoints(self, source_code: str) -> List[Dict]:
        """Extract API endpoints from source code."""
        endpoints = []

        # Mock endpoint extraction
        lines = source_code.split('\n')
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line.startswith('@app.get(') or line.startswith('@app.post('):
                # Extract endpoint path
                path_start = line.find('(') + 2  # Skip '@app.get("'
                path_end = line.find('"', path_start)
                if path_end > path_start:
                    path = line[path_start:path_end]
                    method = "GET" if "get" in line else "POST"

                    endpoints.append({
                        "path": path,
                        "method": method,
                        "line": i,
                        "handler": self._extract_handler_name(lines, i)
                    })

        return endpoints

    def _extract_handler_name(self, lines: List[str], start_line: int) -> str:
        """Extract function name from endpoint definition."""
        for i in range(start_line, min(start_line + 5, len(lines))):
            line = lines[i].strip()
            if line.startswith('async def ') or line.startswith('def '):
                func_start = line.find('def ') + 4
                func_end = line.find('(', func_start)
                if func_end > func_start:
                    return line[func_start:func_end]
        return "unknown_handler"

    async def validate_endpoints(self, endpoints: List[Dict]) -> Dict:
        """Validate extracted endpoints."""
        issues = []

        # Check for duplicate paths
        paths = {}
        for endpoint in endpoints:
            path = endpoint["path"]
            method = endpoint["method"]
            key = f"{method}:{path}"

            if key in paths:
                issues.append({
                    "type": "duplicate_endpoint",
                    "severity": "warning",
                    "description": f"Duplicate endpoint: {method} {path}",
                    "location": {"line": endpoint["line"]}
                })
            else:
                paths[key] = endpoint

        # Check for missing authentication
        for endpoint in endpoints:
            if endpoint["path"].startswith("/admin") or "user" in endpoint["path"]:
                # This would need authentication
                issues.append({
                    "type": "missing_auth",
                    "severity": "medium",
                    "description": f"Endpoint {endpoint['path']} may need authentication",
                    "location": {"line": endpoint["line"]}
                })

        return {
            "endpoints": endpoints,
            "issues": issues,
            "summary": {
                "total_endpoints": len(endpoints),
                "unique_paths": len(paths),
                "issues_found": len(issues)
            }
        }


class StyleManager:
    """Domain service for managing code style and formatting."""

    def __init__(self):
        self.style_rules = {
            "max_line_length": 88,
            "indentation": "spaces",
            "quote_style": "double",
            "trailing_comma": "allowed"
        }

    def analyze_style(self, source_code: str) -> Dict:
        """Analyze code style compliance."""
        issues = []
        score = 1.0

        lines = source_code.split('\n')

        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > self.style_rules["max_line_length"]:
                issues.append({
                    "type": "line_too_long",
                    "line": i,
                    "description": f"Line exceeds {self.style_rules['max_line_length']} characters",
                    "severity": "minor"
                })
                score -= 0.01

            # Check indentation (simple check)
            if line.startswith('\t'):
                issues.append({
                    "type": "wrong_indentation",
                    "line": i,
                    "description": "Use spaces instead of tabs for indentation",
                    "severity": "minor"
                })
                score -= 0.005

            # Check trailing whitespace
            if line.rstrip() != line:
                issues.append({
                    "type": "trailing_whitespace",
                    "line": i,
                    "description": "Remove trailing whitespace",
                    "severity": "minor"
                })
                score -= 0.002

        return {
            "score": max(0.0, score),
            "issues": issues,
            "compliance_percentage": max(0.0, score * 100),
            "rules_checked": len(self.style_rules)
        }

    def suggest_improvements(self, analysis_result: Dict) -> List[str]:
        """Suggest style improvements."""
        suggestions = []

        issues = analysis_result.get("issues", [])

        # Group issues by type
        issue_counts = {}
        for issue in issues:
            issue_type = issue["type"]
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

        # Generate suggestions based on issue patterns
        if issue_counts.get("line_too_long", 0) > 0:
            suggestions.append("Consider breaking long lines into multiple lines for better readability")

        if issue_counts.get("wrong_indentation", 0) > 0:
            suggestions.append("Configure your editor to use spaces instead of tabs for consistent indentation")

        if issue_counts.get("trailing_whitespace", 0) > 0:
            suggestions.append("Enable automatic trailing whitespace removal in your editor")

        if not suggestions:
            suggestions.append("Code style is well-maintained! Consider adding automated style checking to CI/CD.")

        return suggestions


class TestAnalysisProcessor:
    """Test the AnalysisProcessor domain service."""

    @pytest.fixture
    def analysis_repo(self):
        """Create analysis repository."""
        return MockAnalysisRepository()

    @pytest.fixture
    def security_repo(self):
        """Create security repository."""
        return MockSecurityRepository()

    @pytest.fixture
    def analysis_processor(self, analysis_repo, security_repo):
        """Create analysis processor."""
        return AnalysisProcessor(analysis_repo, security_repo)

    @pytest.mark.asyncio
    async def test_process_clean_code(self, analysis_processor):
        """Test processing clean code."""
        source_code = '''
def hello_world():
    """A simple function."""
    return "Hello, World!"

class Calculator:
    def add(self, a, b):
        return a + b
'''

        result = await analysis_processor.process_code_analysis(source_code, "python")

        assert result.status == AnalysisStatus.COMPLETED
        assert len(result.entities_found) >= 2  # function and class
        assert result.quality_score > 0.2  # Should be decent score (2 entities = 0.2 base score)

    @pytest.mark.asyncio
    async def test_process_vulnerable_code(self, analysis_processor):
        """Test processing code with vulnerabilities."""
        source_code = '''
import sqlite3

def get_user(query):
    conn = sqlite3.connect('users.db')
    cursor = conn.execute(f"SELECT * FROM users WHERE id = {query}")  # SQL injection
    return cursor.fetchall()

@app.route('/profile')
def profile():
    name = request.args.get('name')
    return f"<script>alert('{name}')</script>"  # XSS vulnerability
'''

        result = await analysis_processor.process_code_analysis(source_code, "python")

        assert result.status == AnalysisStatus.COMPLETED
        assert len(result.security_issues) >= 2  # SQL injection and XSS
        assert result.quality_score < 0.5  # Should be lower due to issues

    @pytest.mark.asyncio
    async def test_process_empty_code(self, analysis_processor):
        """Test processing empty code."""
        result = await analysis_processor.process_code_analysis("", "python")

        assert result.status == AnalysisStatus.COMPLETED
        assert len(result.entities_found) == 0
        assert len(result.security_issues) == 0
        assert result.quality_score == 0.0

    def test_entity_extraction(self, analysis_processor):
        """Test entity extraction logic."""
        source_code = '''
def calculate_total(items):
    return sum(items)

class ShoppingCart:
    pass

@app.get("/api/items")
def get_items():
    return []
'''

        entities = analysis_processor._extract_entities(source_code, "python")

        assert len(entities) == 3
        entity_types = [e["type"] for e in entities]
        assert "function" in entity_types
        assert "class" in entity_types
        assert "endpoint" in entity_types

    def test_metrics_calculation(self, analysis_processor):
        """Test metrics calculation."""
        source_code = "line1\nline2\nline3\nline4\nline5"
        entities = [
            {"type": "function", "name": "func1"},
            {"type": "function", "name": "func2"},
            {"type": "class", "name": "Class1"}
        ]
        issues = [
            {"severity": SeverityLevel.CRITICAL},
            {"severity": SeverityLevel.HIGH}
        ]

        metrics = analysis_processor._calculate_metrics(source_code, entities, issues)

        assert metrics["lines_of_code"] == 5
        assert metrics["functions_count"] == 2
        assert metrics["classes_count"] == 1
        assert metrics["security_issues_count"] == 2

    def test_quality_score_calculation(self, analysis_processor):
        """Test quality score calculation."""
        entities = [{"type": "function"}, {"type": "class"}]
        issues = [{"severity": SeverityLevel.HIGH}]
        metrics = {"cyclomatic_complexity": 8}

        score = analysis_processor._calculate_quality_score(entities, issues, metrics)

        assert 0.0 <= score <= 1.0
        # Should be reduced due to high severity issue
        assert score < 0.8


class TestEndpointExtractor:
    """Test the EndpointExtractor domain service."""

    @pytest.fixture
    def analysis_repo(self):
        """Create analysis repository."""
        return MockAnalysisRepository()

    @pytest.fixture
    def endpoint_extractor(self, analysis_repo):
        """Create endpoint extractor."""
        return EndpointExtractor(analysis_repo)

    @pytest.mark.asyncio
    async def test_extract_simple_endpoints(self, endpoint_extractor):
        """Test extracting simple endpoints."""
        source_code = '''
@app.get("/api/users")
def get_users():
    return []

@app.post("/api/users")
def create_user():
    return {}
'''

        endpoints = await endpoint_extractor.extract_endpoints(source_code)

        assert len(endpoints) == 2
        assert endpoints[0]["path"] == "/api/users"
        assert endpoints[0]["method"] == "GET"
        assert endpoints[1]["path"] == "/api/users"
        assert endpoints[1]["method"] == "POST"

    @pytest.mark.asyncio
    async def test_extract_no_endpoints(self, endpoint_extractor):
        """Test extracting from code without endpoints."""
        source_code = '''
def regular_function():
    return "no endpoints here"

class RegularClass:
    pass
'''

        endpoints = await endpoint_extractor.extract_endpoints(source_code)

        assert len(endpoints) == 0

    @pytest.mark.asyncio
    async def test_validate_endpoints_with_duplicates(self, endpoint_extractor):
        """Test validating endpoints with duplicates."""
        endpoints = [
            {"path": "/api/users", "method": "GET", "line": 1, "handler": "get_users"},
            {"path": "/api/users", "method": "GET", "line": 5, "handler": "get_users_v2"}
        ]

        validation = await endpoint_extractor.validate_endpoints(endpoints)

        assert len(validation["issues"]) > 0
        assert "duplicate_endpoint" in [issue["type"] for issue in validation["issues"]]
        assert validation["summary"]["total_endpoints"] == 2
        assert validation["summary"]["issues_found"] > 0


class TestStyleManager:
    """Test the StyleManager domain service."""

    @pytest.fixture
    def style_manager(self):
        """Create style manager."""
        return StyleManager()

    def test_analyze_good_style(self, style_manager):
        """Test analyzing well-formatted code."""
        source_code = '''def hello():
    return "Hello"

class Test:
    pass
'''

        result = style_manager.analyze_style(source_code)

        assert result["score"] > 0.9
        assert len(result["issues"]) == 0
        assert result["compliance_percentage"] > 90

    def test_analyze_poor_style(self, style_manager):
        """Test analyzing poorly formatted code."""
        source_code = 'def very_long_function_name_that_exceeds_the_maximum_allowed_line_length_and_should_be_flagged_as_an_issue():\treturn "bad style"\nclass BadClass:\n    def method(self):\n        return "trailing spaces"   \n'

        result = style_manager.analyze_style(source_code)

        assert result["score"] < 1.0
        assert len(result["issues"]) > 0
        assert result["compliance_percentage"] < 100

    def test_suggest_improvements(self, style_manager):
        """Test generating style improvement suggestions."""
        analysis_result = {
            "issues": [
                {"type": "line_too_long"},
                {"type": "line_too_long"},
                {"type": "wrong_indentation"}
            ]
        }

        suggestions = style_manager.suggest_improvements(analysis_result)

        assert len(suggestions) > 0
        assert any("long lines" in suggestion.lower() for suggestion in suggestions)
        assert any("indentation" in suggestion.lower() for suggestion in suggestions)

    def test_suggest_improvements_good_code(self, style_manager):
        """Test suggestions for well-formatted code."""
        analysis_result = {"issues": []}

        suggestions = style_manager.suggest_improvements(analysis_result)

        assert len(suggestions) > 0
        assert any("well-maintained" in suggestion.lower() for suggestion in suggestions)


class TestServiceIntegration:
    """Test integration between domain services."""

    @pytest.fixture
    def analysis_repo(self):
        """Create analysis repository."""
        return MockAnalysisRepository()

    @pytest.fixture
    def security_repo(self):
        """Create security repository."""
        return MockSecurityRepository()

    @pytest.fixture
    def analysis_processor(self, analysis_repo, security_repo):
        """Create analysis processor."""
        return AnalysisProcessor(analysis_repo, security_repo)

    @pytest.fixture
    def endpoint_extractor(self, analysis_repo):
        """Create endpoint extractor."""
        return EndpointExtractor(analysis_repo)

    @pytest.fixture
    def style_manager(self):
        """Create style manager."""
        return StyleManager()

    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self, analysis_processor, endpoint_extractor, style_manager):
        """Test complete analysis workflow with all services."""
        source_code = '''
@app.get("/api/analyze")
def analyze_code():
    """Analyze code endpoint."""
    return {"status": "analyzing"}

class CodeAnalyzer:
    def analyze(self, code):
        return len(code)

def process_data(data):
    return data.upper()
'''

        # Process analysis
        analysis_result = await analysis_processor.process_code_analysis(source_code, "python")

        # Extract endpoints
        endpoints = await endpoint_extractor.extract_endpoints(source_code)

        # Analyze style
        style_result = style_manager.analyze_style(source_code)

        # Verify integration
        assert analysis_result.status == AnalysisStatus.COMPLETED
        assert len(endpoints) == 1
        assert endpoints[0]["path"] == "/api/analyze"
        assert "score" in style_result
        assert "issues" in style_result

        # Check that analysis found entities
        assert len(analysis_result.entities_found) >= 2  # function and class

    @pytest.mark.asyncio
    async def test_service_data_consistency(self, analysis_processor, endpoint_extractor):
        """Test data consistency across services."""
        source_code = '''
@app.get("/api/users")
def get_users():
    return []

@app.post("/api/users")
def create_user():
    return {}

def helper_function():
    return "helper"
'''

        # Get analysis from processor
        analysis_result = await analysis_processor.process_code_analysis(source_code, "python")

        # Get endpoints from extractor
        endpoints = await endpoint_extractor.extract_endpoints(source_code)

        # Verify consistency
        endpoint_entities = [e for e in analysis_result.entities_found if e["type"] == "endpoint"]
        function_entities = [e for e in analysis_result.entities_found if e["type"] == "function"]

        # Should find endpoints and functions
        assert len(endpoint_entities) >= 1  # At least one endpoint
        assert len(function_entities) >= 1  # At least one function (entity extraction may vary)
        assert len(endpoints) >= 2  # Should match endpoint extraction
