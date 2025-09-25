"""
Maintainability Analyzer
Handles maintainability assessments including documentation, organization, error handling, and devops readiness
"""

import os
import ast
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Handle imports for both module and script execution
try:
    from ..config import AuditProfile, get_thresholds_for_profile
    from ..models import ServiceInfo
except ImportError:
    import sys
    from pathlib import Path
    current_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(current_dir))

    from config import AuditProfile
    from config.thresholds import get_thresholds_for_profile

    # Create a simple ServiceInfo if models doesn't exist
    from dataclasses import dataclass
    from pathlib import Path
    from typing import Dict, Any

    @dataclass
    class ServiceInfo:
        name: str
        path: Path
        type: str = "python"
        status: str = "unknown"
        metadata: Dict[str, Any] = None

        def __post_init__(self):
            if self.metadata is None:
                self.metadata = {}


@dataclass
class MaintainabilityAnalysisResult:
    """Results from maintainability analysis"""
    score: float
    documentation_score: float
    organization_score: float
    error_handling_score: float
    devops_readiness_score: float
    scalability_score: float
    linting_quality: Dict[str, Any]
    test_quality: Dict[str, Any]
    test_quality_metrics: Dict[str, Any]
    domain_boundaries: Dict[str, Any]
    api_documentation: Dict[str, Any]
    code_documentation: Dict[str, Any]
    configuration_management: Dict[str, Any]
    logging_practices: Dict[str, Any]
    issues: List[str]
    recommendations: List[str]


class MaintainabilityAnalyzer:
    """Analyzer for maintainability metrics and best practices"""

    def __init__(self, profile: AuditProfile):
        self.profile = profile
        self.thresholds = get_thresholds_for_profile(profile)

    async def analyze(self, service: ServiceInfo) -> MaintainabilityAnalysisResult:
        """Perform complete maintainability analysis"""
        scores = {
            'documentation': await self._check_documentation(service),
            'organization': await self._check_organization(service),
            'error_handling': await self._check_error_handling(service),
            'scalability': await self._check_scalability(service),
            'devops': await self._check_devops_readiness(service)
        }

        # Calculate weighted maintainability score
        documentation_weight = 0.35
        organization_weight = 0.25
        error_handling_weight = 0.15
        scalability_weight = 0.15
        devops_weight = 0.10

        maintainability_score = (
            scores['documentation'] * documentation_weight +
            scores['organization'] * organization_weight +
            scores['error_handling'] * error_handling_weight +
            scores['scalability'] * scalability_weight +
            scores['devops'] * devops_weight
        )

        return MaintainabilityAnalysisResult(
            score=round(maintainability_score, 2),
            documentation_score=scores['documentation'],
            organization_score=scores['organization'],
            error_handling_score=scores['error_handling'],
            devops_readiness_score=scores['devops'],
            scalability_score=scores['scalability'],
            linting_quality=await self._analyze_linting_quality(service),
            test_quality=await self._analyze_test_quality(service),
            test_quality_metrics=self._analyze_test_quality_metrics(service),
            domain_boundaries=self._analyze_domain_boundaries(service),
            api_documentation=self._analyze_api_documentation_quality(service),
            code_documentation=self._analyze_code_documentation(service),
            configuration_management=self._analyze_configuration_management(service),
            logging_practices=self._analyze_logging_practices(service),
            issues=self._identify_issues(scores),
            recommendations=self._generate_recommendations(scores)
        )

    async def _check_documentation(self, service: ServiceInfo) -> float:
        """Check documentation quality using interrogate for actual docstring coverage."""
        score = 0.0

        try:
            # Use interrogate for accurate docstring coverage if available
            if self.profile.enable_third_party_tools:
                try:
                    import subprocess
                    import sys

                    # Run interrogate for comprehensive docstring analysis
                    result = subprocess.run([
                        sys.executable, "-m", "interrogate",
                        "--generate-badge", "docs/badge.svg",
                        "--fail-under", str(self.thresholds['documentation']['min_docstring_coverage']),
                        str(service.path)
                    ], capture_output=True, text=True, timeout=60)

                    if result.returncode in [0, 1]:  # interrogate returns 1 for coverage below threshold
                        # Parse output to extract coverage percentage
                        output_lines = result.stdout.split('\n')
                        for line in output_lines:
                            if 'RESULT:' in line or 'actual:' in line:
                                # Extract percentage from output like "RESULT: 85.2%" or "actual: 85.23%"
                                match = re.search(r'(\d+\.?\d*)%', line)
                                if match:
                                    coverage = float(match.group(1))
                                    if coverage >= self.thresholds['documentation']['min_docstring_coverage']:
                                        score += 60  # Good coverage
                                        if coverage >= 90:
                                            score += 20  # Excellent coverage bonus
                                    elif coverage >= 70:
                                        score += 40  # Adequate coverage
                                    else:
                                        score += 20  # Poor coverage

                    # Bonus for proper documentation structure
                    docstring_score = self._analyze_code_documentation(service)
                    if docstring_score.get('docstring_coverage', 0) >= self.thresholds['documentation']['min_docstring_coverage']:
                        score += 20

                except (subprocess.TimeoutExpired, FileNotFoundError, ImportError):
                    # Fallback to basic docstring analysis
                    score = self._fallback_docstring_analysis(service)

            else:
                # Fallback when third-party tools disabled
                score = self._fallback_docstring_analysis(service)

        except Exception:
            score = 30  # Low score on error

        return max(0, min(100, score))

    def _fallback_docstring_analysis(self, service: ServiceInfo) -> float:
        """Fallback docstring analysis when interrogate is not available"""
        score = 0.0
        total_functions = 0
        documented_functions = 0
        total_classes = 0
        documented_classes = 0

        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        tree = ast.parse(content)

                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                                total_functions += 1
                                if ast.get_docstring(node):
                                    documented_functions += 1

                            elif isinstance(node, ast.ClassDef):
                                total_classes += 1
                                if ast.get_docstring(node):
                                    documented_classes += 1

                    except Exception:
                        continue

        # Calculate coverage
        function_coverage = (documented_functions / max(1, total_functions)) * 100 if total_functions > 0 else 0
        class_coverage = (documented_classes / max(1, total_classes)) * 100 if total_classes > 0 else 0

        # Score based on coverage
        if function_coverage >= self.thresholds['documentation']['min_docstring_coverage']:
            score += 40
        elif function_coverage >= 70:
            score += 25
        else:
            score += 10

        if class_coverage >= 90:  # Classes should be well documented
            score += 20
        elif class_coverage >= 70:
            score += 10

        return score

    async def _check_organization(self, service: ServiceInfo) -> float:
        """Check code organization and structure"""
        score = 100.0

        # Check for clear directory structure
        dirs = [d for d in os.listdir(str(service.path)) if os.path.isdir(os.path.join(str(service.path), d))]

        # Penalize too many directories at root level
        if len(dirs) > 15:
            score -= min(20, (len(dirs) - 15) * 2)

        # Check for logical grouping
        logical_groups = ['domain', 'application', 'infrastructure', 'presentation', 'tests', 'docs']
        logical_dirs = sum(1 for d in dirs if any(group in d.lower() for group in logical_groups))

        if logical_dirs > 0:
            score += min(10, logical_dirs * 2)  # Bonus for logical organization

        # Check file organization within directories
        large_dirs_penalty = 0
        for dir_name in dirs:
            dir_path = service.path / dir_name
            if dir_path.is_dir():
                files_in_dir = list(dir_path.glob("*.py"))
                if len(files_in_dir) > 15:  # Too many files in one directory
                    large_dirs_penalty += min(5, (len(files_in_dir) - 15))

        score -= large_dirs_penalty

        # Check for proper Python package structure
        has_init_files = 0
        total_dirs = 0

        for root, dirs, files in os.walk(str(service.path)):
            for dir_name in dirs:
                total_dirs += 1
                init_file = Path(root) / dir_name / "__init__.py"
                if init_file.exists():
                    has_init_files += 1

        if total_dirs > 0:
            init_coverage = (has_init_files / total_dirs) * 100
            if init_coverage >= 80:
                score += 10  # Good package structure
            elif init_coverage >= 50:
                score += 5   # Adequate package structure

        return max(0, min(100, score))

    async def _check_error_handling(self, service: ServiceInfo) -> float:
        """Check error handling quality and patterns"""
        score = 100.0

        error_patterns = {
            'bare_except': 0,
            'generic_exception': 0,
            'missing_finally': 0,
            'unhandled_exceptions': 0,
            'good_error_handling': 0
        }

        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        lines = content.split('\n')

                        for i, line in enumerate(lines):
                            line_strip = line.strip()

                            # Check for bare except clauses
                            if line_strip.startswith('except:') or line_strip.startswith('except :'):
                                error_patterns['bare_except'] += 1

                            # Check for generic Exception catching
                            elif 'except Exception' in line_strip:
                                error_patterns['generic_exception'] += 1

                            # Check for try blocks without proper error handling
                            elif line_strip.startswith('try:'):
                                # Look for corresponding except block
                                has_except = False
                                has_finally = False
                                j = i + 1
                                while j < len(lines) and not lines[j].strip().startswith(('def ', 'class ', 'if ', 'for ', 'while ')):
                                    if lines[j].strip().startswith('except'):
                                        has_except = True
                                    if lines[j].strip().startswith('finally:'):
                                        has_finally = True
                                    j += 1

                                if not has_except:
                                    error_patterns['unhandled_exceptions'] += 1
                                if has_finally:
                                    error_patterns['good_error_handling'] += 1

                    except Exception:
                        continue

        # Apply penalties
        score -= min(30, error_patterns['bare_except'] * 5)
        score -= min(20, error_patterns['generic_exception'] * 3)
        score -= min(25, error_patterns['unhandled_exceptions'] * 4)
        score -= min(15, error_patterns['missing_finally'] * 2)

        # Bonus for good error handling
        score += min(20, error_patterns['good_error_handling'] * 2)

        return max(0, min(100, score))

    async def _check_scalability(self, service: ServiceInfo) -> float:
        """Check scalability indicators and patterns"""
        score = 100.0

        scalability_indicators = {
            'async_usage': 0,
            'concurrency_patterns': 0,
            'caching_usage': 0,
            'pagination_usage': 0,
            'batch_processing': 0,
            'memory_inefficient': 0,
            'blocking_operations': 0
        }

        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Check for async/await usage
                        if 'async def' in content or 'await ' in content:
                            scalability_indicators['async_usage'] += 1

                        # Check for concurrency patterns
                        if any(pattern in content.lower() for pattern in ['asyncio.gather', 'concurrent.futures', 'threading', 'multiprocessing']):
                            scalability_indicators['concurrency_patterns'] += 1

                        # Check for caching
                        if any(pattern in content.lower() for pattern in ['cache', 'redis', 'memcache', 'lru_cache']):
                            scalability_indicators['caching_usage'] += 1

                        # Check for pagination
                        if 'limit' in content.lower() and ('offset' in content.lower() or 'page' in content.lower()):
                            scalability_indicators['pagination_usage'] += 1

                        # Check for batch processing
                        if 'batch' in content.lower() or 'bulk' in content.lower():
                            scalability_indicators['batch_processing'] += 1

                        # Check for memory-inefficient patterns
                        if 'list(' in content and 'range(' in content and '1000' in content:
                            scalability_indicators['memory_inefficient'] += 1

                        # Check for blocking operations
                        if any(pattern in content.lower() for pattern in ['time.sleep', 'requests.get(', 'urllib']):
                            scalability_indicators['blocking_operations'] += 1

                    except Exception:
                        continue

        # Apply scoring
        score += min(15, scalability_indicators['async_usage'] * 3)
        score += min(10, scalability_indicators['concurrency_patterns'] * 5)
        score += min(10, scalability_indicators['caching_usage'] * 4)
        score += min(8, scalability_indicators['pagination_usage'] * 4)
        score += min(7, scalability_indicators['batch_processing'] * 3)

        # Apply penalties
        score -= min(20, scalability_indicators['memory_inefficient'] * 5)
        score -= min(25, scalability_indicators['blocking_operations'] * 4)

        return max(0, min(100, score))

    async def _check_devops_readiness(self, service: ServiceInfo) -> float:
        """Check DevOps readiness and deployment readiness"""
        score = 100.0

        devops_indicators = {
            'dockerfile': False,
            'docker_compose': False,
            'ci_cd_config': False,
            'requirements_file': False,
            'environment_config': False,
            'health_checks': False,
            'logging_config': False,
            'monitoring_setup': False
        }

        # Check for common DevOps files
        devops_files = {
            'Dockerfile': 'dockerfile',
            'docker-compose.yml': 'docker_compose',
            'docker-compose.yaml': 'docker_compose',
            '.github/workflows': 'ci_cd_config',
            '.gitlab-ci.yml': 'ci_cd_config',
            'Jenkinsfile': 'ci_cd_config',
            'requirements.txt': 'requirements_file',
            'pyproject.toml': 'requirements_file',
            'Pipfile': 'requirements_file',
            '.env': 'environment_config',
            '.env.example': 'environment_config',
            'logging.conf': 'logging_config',
            'loguru': 'logging_config'  # Check in code
        }

        # Check for files
        for file_pattern, indicator in devops_files.items():
            if list(service.path.glob(f"**/{file_pattern}")):
                devops_indicators[indicator] = True

        # Check for health endpoints in code
        health_endpoints = 0
        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'health' in content.lower() and ('@app.' in content or '@router.' in content):
                                health_endpoints += 1
                    except Exception:
                        continue

        if health_endpoints > 0:
            devops_indicators['health_checks'] = True

        # Apply scoring
        score += 10 if devops_indicators['dockerfile'] else -5
        score += 8 if devops_indicators['docker_compose'] else -4
        score += 12 if devops_indicators['ci_cd_config'] else -6
        score += 6 if devops_indicators['requirements_file'] else -3
        score += 5 if devops_indicators['environment_config'] else -3
        score += 7 if devops_indicators['health_checks'] else -4
        score += 4 if devops_indicators['logging_config'] else -2

        return max(0, min(100, score))

    # Include the analysis methods from the original framework
    def _analyze_test_quality_metrics(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze test quality metrics"""
        test_metrics = {
            'total_test_files': 0,
            'test_naming_issues': 0,
            'isolation_issues': 0,
            'parametrization_usage': 0,
            'fixture_usage': 0,
            'mock_usage': 0,
            'recommendations': []
        }

        test_files = list(service.path.rglob("test_*.py")) + list(service.path.rglob("*_test.py"))
        test_metrics['total_test_files'] = len(test_files)

        for test_file in test_files[:20]:  # Analyze first 20 test files
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check test naming
                test_functions = [line for line in content.split('\n')
                                if line.strip().startswith('def test_')]

                for func_line in test_functions:
                    # Check naming convention: test_<behavior>_<condition>_<expected>
                    if not any(pattern in func_line.lower() for pattern in
                             ['test_should_', 'test_when_', 'test_given_', 'test_does_']):
                        test_metrics['test_naming_issues'] += 1

                # Check for parametrization
                if '@pytest.mark.parametrize' in content or '@parametrize' in content:
                    test_metrics['parametrization_usage'] += 1

                # Check for fixtures
                if '@pytest.fixture' in content or 'def fixture' in content:
                    test_metrics['fixture_usage'] += 1

                # Check for mocking
                if 'mock' in content.lower() or 'MagicMock' in content or 'patch' in content:
                    test_metrics['mock_usage'] += 1

            except Exception:
                continue

        # Generate recommendations
        if test_metrics['test_naming_issues'] > 0:
            test_metrics['recommendations'].append(
                f"Fix {test_metrics['test_naming_issues']} poorly named test functions"
            )

        return test_metrics

    async def _analyze_linting_quality(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze linting quality with detailed metrics"""
        linting_results = {
            'pylint_score': 0,
            'flake8_issues': 0,
            'total_issues': 0,
            'issues_by_type': {},
            'recommendations': []
        }

        try:
            import subprocess
            import sys

            # Run flake8 for style checking
            flake8_result = subprocess.run([
                sys.executable, "-m", "flake8",
                "--max-line-length=120",
                "--extend-ignore=E203,W503,I100,I201,I202,E402,D401,D400,D205,D107,D202",
                "--format=json",
                str(service.path)
            ], capture_output=True, text=True, timeout=60)

            if flake8_result.returncode in [0, 1]:
                try:
                    import json
                    flake8_data = json.loads(flake8_result.stdout)
                    linting_results['flake8_issues'] = len(flake8_data)
                    linting_results['total_issues'] += len(flake8_data)

                    # Categorize issues
                    for issue in flake8_data:
                        code = issue.get('code', 'unknown')
                        category = code[0] if code else 'unknown'
                        linting_results['issues_by_type'][category] = linting_results['issues_by_type'].get(category, 0) + 1

                except json.JSONDecodeError:
                    # Count issues from text output
                    issues = len([line for line in flake8_result.stdout.split('\n') if line.strip()])
                    linting_results['flake8_issues'] = issues
                    linting_results['total_issues'] += issues

        except (subprocess.TimeoutExpired, FileNotFoundError, ImportError):
            linting_results['recommendations'].append("Install flake8 for comprehensive linting analysis")

        return linting_results

    async def _analyze_test_quality(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze overall test quality"""
        test_quality = {
            'coverage_score': 0,
            'quality_score': 0,
            'structure_score': 0,
            'total_score': 0,
            'recommendations': []
        }

        # Basic test file structure analysis
        test_files = list(service.path.rglob("test_*.py")) + list(service.path.rglob("*_test.py"))
        source_files = [f for f in service.path.rglob("*.py") if not str(f).startswith(str(service.path / "test"))]

        if source_files:
            test_ratio = len(test_files) / len(source_files)
            if test_ratio > 0.8:
                test_quality['structure_score'] = 30
            elif test_ratio > 0.5:
                test_quality['structure_score'] = 20
            elif test_ratio > 0.3:
                test_quality['structure_score'] = 10

        # Test quality metrics
        quality_metrics = self._analyze_test_quality_metrics(service)
        test_quality['quality_score'] = min(30, len(test_files) * 2 + quality_metrics['parametrization_usage'] * 5)

        test_quality['total_score'] = test_quality['coverage_score'] + test_quality['quality_score'] + test_quality['structure_score']

        return test_quality

    def _analyze_domain_boundaries(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze domain boundary integrity"""
        boundaries = {
            'leaks_detected': 0,
            'boundary_violations': [],
            'layer_integrity': True,
            'recommendations': []
        }

        # Check for cross-layer imports that violate boundaries
        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(service.path)

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Check for boundary violations
                        if 'infrastructure' in str(rel_path) and ('domain.' in content or 'application.' in content):
                            boundaries['boundary_violations'].append(str(rel_path))
                            boundaries['leaks_detected'] += 1

                        if 'presentation' in str(rel_path) and 'infrastructure.' in content:
                            boundaries['boundary_violations'].append(str(rel_path))
                            boundaries['leaks_detected'] += 1

                    except Exception:
                        continue

        if boundaries['leaks_detected'] > 0:
            boundaries['layer_integrity'] = False
            boundaries['recommendations'].append(f"Fix {boundaries['leaks_detected']} domain boundary violations")

        return boundaries

    def _analyze_api_documentation_quality(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze API documentation quality"""
        api_docs = {
            'endpoints_documented': 0,
            'total_endpoints': 0,
            'documentation_score': 0,
            'missing_summaries': 0,
            'missing_descriptions': 0,
            'recommendations': []
        }

        # This would be implemented with the endpoint analysis from architecture analyzer
        # For now, return basic structure
        return api_docs

    def _analyze_code_documentation(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze code documentation quality"""
        doc_analysis = {
            'docstring_coverage': 0.0,
            'undocumented_functions': 0,
            'undocumented_classes': 0,
            'total_functions': 0,
            'total_classes': 0,
            'recommendations': []
        }

        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        tree = ast.parse(content)

                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                                doc_analysis['total_functions'] += 1
                                if not ast.get_docstring(node):
                                    doc_analysis['undocumented_functions'] += 1

                            elif isinstance(node, ast.ClassDef):
                                doc_analysis['total_classes'] += 1
                                if not ast.get_docstring(node):
                                    doc_analysis['undocumented_classes'] += 1

                    except Exception:
                        continue

        # Calculate coverage
        if doc_analysis['total_functions'] > 0:
            doc_analysis['docstring_coverage'] = ((doc_analysis['total_functions'] - doc_analysis['undocumented_functions']) / doc_analysis['total_functions']) * 100

        if doc_analysis['undocumented_functions'] > 0:
            doc_analysis['recommendations'].append(f"Add docstrings to {doc_analysis['undocumented_functions']} undocumented functions")

        return doc_analysis

    def _analyze_configuration_management(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze configuration management practices"""
        config_analysis = {
            'hardcoded_values': 0,
            'environment_variables': 0,
            'config_files': 0,
            'security_issues': 0,
            'recommendations': []
        }

        # Check for configuration files
        config_files = ['config.py', 'settings.py', '.env', 'config.yaml', 'config.json']
        for config_file in config_files:
            if list(service.path.glob(f"**/{config_file}")):
                config_analysis['config_files'] += 1

        # Analyze code for configuration issues
        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Check for hardcoded secrets/patterns
                        if any(pattern in content.lower() for pattern in ['password', 'secret', 'key', 'token']):
                            lines = content.split('\n')
                            for line in lines:
                                if any(pattern in line.lower() for pattern in ['password', 'secret', 'key', 'token']):
                                    # Check if it's not an environment variable
                                    if not ('os.environ' in line or 'getenv' in line or 'environ[' in line):
                                        config_analysis['hardcoded_values'] += 1
                                        config_analysis['security_issues'] += 1

                        # Check for environment variable usage
                        if 'os.environ' in content or 'getenv' in content or 'environ[' in content:
                            config_analysis['environment_variables'] += 1

                    except Exception:
                        continue

        if config_analysis['hardcoded_values'] > 0:
            config_analysis['recommendations'].append(f"Replace {config_analysis['hardcoded_values']} hardcoded values with environment variables")

        return config_analysis

    def _analyze_logging_practices(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze logging practices and error handling"""
        logging_analysis = {
            'logging_usage': 0,
            'error_logging': 0,
            'structured_logging': 0,
            'missing_error_logs': 0,
            'logging_levels_used': set(),
            'recommendations': []
        }

        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Check for logging usage
                        if 'logging.' in content or 'logger.' in content:
                            logging_analysis['logging_usage'] += 1

                        # Check for error logging in exception handlers
                        lines = content.split('\n')
                        exception_blocks = []
                        in_except = False

                        for i, line in enumerate(lines):
                            if line.strip().startswith('except'):
                                in_except = True
                                exception_blocks.append(i)
                            elif in_except and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                                in_except = False

                        # Check each exception block for logging
                        for block_start in exception_blocks:
                            has_logging = False
                            for j in range(block_start, min(block_start + 10, len(lines))):
                                if 'logging.' in lines[j] or 'logger.' in lines[j] or 'log.' in lines[j]:
                                    has_logging = True
                                    logging_analysis['error_logging'] += 1
                                    break

                            if not has_logging:
                                logging_analysis['missing_error_logs'] += 1

                        # Check logging levels
                        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                            if f"logging.{level}" in content or f"logger.{level.lower()}" in content:
                                logging_analysis['logging_levels_used'].add(level)

                    except Exception:
                        continue

        if logging_analysis['missing_error_logs'] > 0:
            logging_analysis['recommendations'].append(f"Add error logging to {logging_analysis['missing_error_logs']} exception handlers")

        return logging_analysis

    def _identify_issues(self, scores: Dict[str, float]) -> List[str]:
        """Identify maintainability issues"""
        issues = []
        if scores.get('documentation', 0) < self.thresholds['dimensions']['maintainability']['docstring_coverage_required']:
            issues.append("Insufficient documentation coverage")
        if scores.get('organization', 0) < 70:
            issues.append("Poor code organization and structure")
        if scores.get('error_handling', 0) < 70:
            issues.append("Inadequate error handling patterns")
        if scores.get('scalability', 0) < 70:
            issues.append("Scalability concerns in code design")
        if scores.get('devops', 0) < 70:
            issues.append("DevOps readiness issues")
        return issues

    def _generate_recommendations(self, scores: Dict[str, float]) -> List[str]:
        """Generate maintainability recommendations"""
        recommendations = []
        if scores.get('documentation', 0) < self.thresholds['dimensions']['maintainability']['docstring_coverage_required']:
            recommendations.append(f"Increase docstring coverage to at least {self.thresholds['dimensions']['maintainability']['docstring_coverage_required']}%")
        if scores.get('organization', 0) < 80:
            recommendations.append("Improve code organization with better directory structure")
        if scores.get('error_handling', 0) < 80:
            recommendations.append("Implement proper error handling with specific exception types")
        if scores.get('scalability', 0) < 80:
            recommendations.append("Add async/await patterns and optimize resource usage")
        if scores.get('devops', 0) < 80:
            recommendations.append("Add Docker, CI/CD, and monitoring configurations")
        return recommendations
