"""
Code Quality Analyzer
Handles code quality assessments including complexity, testing, linting, and duplication
"""

import os
import ast
from pathlib import Path
from typing import Dict, Any, List, Tuple
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
class CodeQualityAnalysisResult:
    """Results from code quality analysis"""
    score: float
    complexity_score: float
    testing_score: float
    linting_score: float
    duplication_score: float
    test_coverage: float
    cyclomatic_complexity: Dict[str, Any]
    test_quality_metrics: Dict[str, Any]
    linting_quality: Dict[str, Any]
    duplication_analysis: Dict[str, Any]
    issues: List[str]
    recommendations: List[str]


class CodeQualityAnalyzer:
    """Analyzer for code quality metrics and standards"""

    def __init__(self, profile: AuditProfile):
        self.profile = profile
        self.thresholds = get_thresholds_for_profile(profile)

    async def analyze(self, service: ServiceInfo) -> CodeQualityAnalysisResult:
        """Perform complete code quality analysis"""
        # Get testing details including coverage data
        testing_score, testing_details = await self._check_testing_with_details(service)

        scores = {
            'complexity': await self._check_complexity(service),
            'testing': testing_score,
            'linting': await self._check_linting(service),
            'duplication': await self._check_duplication(service)
        }

        # Calculate weighted code quality score
        complexity_weight = 0.25
        testing_weight = 0.30
        linting_weight = 0.20
        duplication_weight = 0.15

        code_quality_score = (
            scores['complexity'] * complexity_weight +
            scores['testing'] * testing_weight +
            scores['linting'] * linting_weight +
            scores['duplication'] * duplication_weight
        )

        return CodeQualityAnalysisResult(
            score=round(code_quality_score, 2),
            complexity_score=scores['complexity'],
            testing_score=scores['testing'],
            linting_score=scores['linting'],
            duplication_score=scores['duplication'],
            test_coverage=testing_details.get('coverage_data', {}).get('overall_coverage', 0),
            cyclomatic_complexity=self._analyze_cyclomatic_complexity(service),
            test_quality_metrics=self._analyze_test_quality_metrics(service),
            linting_quality=await self._analyze_linting_quality(service),
            duplication_analysis=await self._analyze_duplication(service),
            issues=self._identify_issues(scores),
            recommendations=self._generate_recommendations(scores)
        )

    async def _check_complexity(self, service: ServiceInfo) -> float:
        """Check code complexity using radon"""
        score = 100.0
        total_functions = 0
        complex_functions = 0

        try:
            # Use radon for complexity analysis if available
            import radon.complexity as radon_cc

            for root, dirs, files in os.walk(str(service.path)):
                for file in files:
                    if file.endswith('.py') and not file.startswith('test_'):
                        file_path = Path(root) / file
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()

                            # Analyze complexity
                            blocks = radon_cc.cc_visit(content)

                            for block in blocks:
                                total_functions += 1
                                if block.complexity > self.thresholds['complexity']['max_cyclomatic_complexity']:
                                    complex_functions += 1
                                    # Penalty for complex functions
                                    score -= min(2, (block.complexity - self.thresholds['complexity']['max_cyclomatic_complexity']) * 0.5)

                        except Exception:
                            continue

        except ImportError:
            # Fallback to AST-based complexity analysis
            for root, dirs, files in os.walk(str(service.path)):
                for file in files:
                    if file.endswith('.py') and not file.startswith('test_'):
                        file_path = Path(root) / file
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()

                            tree = ast.parse(content)
                            for node in ast.walk(tree):
                                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                    total_functions += 1
                                    complexity = self._calculate_cyclomatic_complexity(node)
                                    if complexity > self.thresholds['complexity']['max_cyclomatic_complexity']:
                                        complex_functions += 1
                                        score -= min(2, (complexity - self.thresholds['complexity']['max_cyclomatic_complexity']) * 0.5)

                        except Exception:
                            continue

        # Bonus for low average complexity
        if complex_functions == 0 and total_functions > 0:
            score += 5  # Bonus for no complex functions

        return max(0, min(100, score))

    def _calculate_cyclomatic_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function"""
        complexity = 1  # Base complexity

        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(node, ast.BoolOp) and len(node.values) > 1:
                complexity += len(node.values) - 1
            elif isinstance(node, ast.comprehension):
                complexity += 1

        return complexity

    async def _check_testing_with_details(self, service: ServiceInfo) -> Tuple[float, Dict[str, Any]]:
        """Check testing coverage and quality with actual coverage measurement"""
        score = 0.0
        coverage_data = {}

        try:
            # Test file coverage (basic heuristic)
            test_files = list(service.path.rglob("test_*.py")) + list(service.path.rglob("*_test.py"))
            source_files = [f for f in service.path.rglob("*.py") if not str(f).startswith(str(service.path / "test"))]

            test_ratio = len(test_files) / max(1, len(source_files))

            if test_ratio > 0.8:  # Excellent test coverage
                score += 30
            elif test_ratio > 0.5:  # Good test coverage
                score += 20
            elif test_ratio > 0.3:  # Adequate test coverage
                score += 10

            # Try to measure actual test coverage
            if self.profile.enable_third_party_tools:
                try:
                    import subprocess
                    import sys

                    # Run coverage if available
                    result = subprocess.run([
                        sys.executable, "-m", "coverage", "run", "--source=.",
                        "-m", "pytest", str(service.path), "--tb=no", "-q"
                    ], capture_output=True, text=True, cwd=str(service.path), timeout=60)

                    if result.returncode == 0:
                        # Try to get coverage report
                        coverage_result = subprocess.run([
                            sys.executable, "-m", "coverage", "report", "--json"
                        ], capture_output=True, text=True, cwd=str(service.path))

                        if coverage_result.returncode == 0:
                            try:
                                import json
                                coverage_json = json.loads(coverage_result.stdout)
                                coverage_data = {
                                    'overall_coverage': coverage_json.get('totals', {}).get('percent_covered', 0),
                                    'files_covered': len(coverage_json.get('files', {})),
                                    'total_files': len(source_files)
                                }

                                coverage_pct = coverage_data['overall_coverage']
                                if coverage_pct >= self.thresholds['testing']['min_test_coverage']:
                                    score += 40  # Good coverage
                                    if coverage_pct >= 90:
                                        score += 10  # Excellent coverage bonus
                                elif coverage_pct >= 50:
                                    score += 20  # Adequate coverage

                            except json.JSONDecodeError:
                                pass

                except (subprocess.TimeoutExpired, FileNotFoundError, ImportError):
                    # Coverage not available or failed
                    pass

            # Test quality indicators
            test_quality_score = 0
            for test_file in test_files[:10]:  # Sample first 10 test files
                try:
                    with open(test_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Check for test naming conventions
                    test_functions = len([line for line in content.split('\n')
                                        if line.strip().startswith('def test_')])

                    if test_functions > 0:
                        test_quality_score += 5

                    # Check for parametrized tests
                    if '@pytest.mark.parametrize' in content or '@parametrize' in content:
                        test_quality_score += 3

                    # Check for fixtures
                    if '@pytest.fixture' in content or 'def fixture' in content:
                        test_quality_score += 2

                except Exception:
                    continue

            if len(test_files) > 0:
                avg_test_quality = test_quality_score / len(test_files[:10])
                score += min(20, avg_test_quality * 4)  # Max 20 points for test quality

        except Exception as e:
            # Fallback scoring based on file structure
            score = 20  # Minimal score for having test directory

        coverage_data.setdefault('overall_coverage', 0)
        coverage_data.setdefault('files_covered', 0)
        coverage_data.setdefault('total_files', len(source_files) if 'source_files' in locals() else 0)

        return min(100, score), {'coverage_data': coverage_data}

    async def _check_linting(self, service: ServiceInfo) -> float:
        """Check code linting quality"""
        score = 100.0

        try:
            # Use pylint for comprehensive linting if available
            if self.profile.enable_third_party_tools:
                import subprocess
                import sys

                # Run pylint
                result = subprocess.run([
                    sys.executable, "-m", "pylint",
                    "--output-format=json",
                    str(service.path)
                ], capture_output=True, text=True, timeout=120)

                if result.returncode in [0, 1, 2]:  # pylint returns 0,1,2 for success
                    try:
                        import json
                        pylint_output = json.loads(result.stdout)

                        total_issues = len(pylint_output)
                        score -= min(50, total_issues * 2)  # 2 points per issue, max 50 deduction

                        # Bonus for good pylint score
                        if total_issues < 10:
                            score += 10

                    except json.JSONDecodeError:
                        # Fallback: parse text output
                        issues = len([line for line in result.stdout.split('\n')
                                    if 'rated' not in line.lower() and line.strip()])
                        score -= min(40, issues * 1.5)

        except (subprocess.TimeoutExpired, FileNotFoundError, ImportError):
            # Fallback to basic checks
            score = 60  # Neutral score when pylint not available

        return max(0, min(100, score))

    async def _check_duplication(self, service: ServiceInfo) -> float:
        """Check for code duplication"""
        score = 100.0
        total_lines = 0
        duplicate_lines = 0

        try:
            # Simple duplication detection
            file_contents = {}

            for root, dirs, files in os.walk(str(service.path)):
                for file in files:
                    if file.endswith('.py') and not file.startswith('test_'):
                        file_path = Path(root) / file
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                total_lines += len(lines)

                                # Simple duplicate detection (3+ consecutive lines)
                                for i in range(len(lines) - 2):
                                    block = ''.join(lines[i:i+3]).strip()
                                    if block in file_contents:
                                        duplicate_lines += 3
                                    else:
                                        file_contents[block] = file_path

                        except Exception:
                            continue

            if total_lines > 0:
                duplication_rate = duplicate_lines / total_lines
                if duplication_rate > self.thresholds['maintainability']['max_duplicate_lines_percent'] / 100:
                    penalty = (duplication_rate - self.thresholds['maintainability']['max_duplicate_lines_percent'] / 100) * 200
                    score -= min(40, penalty)

        except Exception:
            score = 70  # Neutral score on error

        return max(0, min(100, score))

    def _analyze_cyclomatic_complexity(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze cyclomatic complexity of functions and methods"""
        complexity_results = {
            'high_complexity_functions': [],
            'total_functions_analyzed': 0,
            'complexity_distribution': {'low': 0, 'medium': 0, 'high': 0, 'very_high': 0},
            'average_complexity': 0.0,
            'recommendations': []
        }

        total_complexity = 0

        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                complexity = self._calculate_cyclomatic_complexity(node)
                                complexity_results['total_functions_analyzed'] += 1
                                total_complexity += complexity

                                if complexity > 20:
                                    complexity_results['complexity_distribution']['very_high'] += 1
                                    complexity_results['high_complexity_functions'].append({
                                        'function': node.name,
                                        'file': str(file_path.relative_to(service.path)),
                                        'complexity': complexity
                                    })
                                elif complexity > 10:
                                    complexity_results['complexity_distribution']['high'] += 1
                                elif complexity > 5:
                                    complexity_results['complexity_distribution']['medium'] += 1
                                else:
                                    complexity_results['complexity_distribution']['low'] += 1

                    except Exception:
                        continue

        if complexity_results['total_functions_analyzed'] > 0:
            complexity_results['average_complexity'] = total_complexity / complexity_results['total_functions_analyzed']

        # Generate recommendations
        if complexity_results['high_complexity_functions']:
            complexity_results['recommendations'].append(
                f"Refactor {len(complexity_results['high_complexity_functions'])} high-complexity functions"
            )

        return complexity_results

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

    async def _analyze_duplication(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze code duplication"""
        duplication_results = {
            'total_duplicate_blocks': 0,
            'duplicate_lines': 0,
            'total_lines_analyzed': 0,
            'duplication_rate': 0.0,
            'recommendations': []
        }

        try:
            # Analyze for duplicate code blocks
            code_blocks = {}

            for root, dirs, files in os.walk(str(service.path)):
                for file in files:
                    if file.endswith('.py') and not file.startswith('test_'):
                        file_path = Path(root) / file
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                duplication_results['total_lines_analyzed'] += len(lines)

                                # Check for duplicate 4-line blocks
                                for i in range(len(lines) - 3):
                                    block = ''.join(lines[i:i+4]).strip()
                                    if len(block) > 50:  # Only check substantial blocks
                                        if block in code_blocks:
                                            duplication_results['total_duplicate_blocks'] += 1
                                            duplication_results['duplicate_lines'] += 4
                                        else:
                                            code_blocks[block] = file_path

                        except Exception:
                            continue

            if duplication_results['total_lines_analyzed'] > 0:
                duplication_results['duplication_rate'] = (
                    duplication_results['duplicate_lines'] / duplication_results['total_lines_analyzed']
                ) * 100

            if duplication_results['duplication_rate'] > 10:
                duplication_results['recommendations'].append(
                    f"High duplication rate ({duplication_results['duplication_rate']:.1f}%) - consider refactoring"
                )

        except Exception:
            duplication_results['recommendations'].append("Code duplication analysis failed")

        return duplication_results

    def _identify_issues(self, scores: Dict[str, float]) -> List[str]:
        """Identify code quality issues"""
        issues = []
        if scores.get('complexity', 0) < 70:
            issues.append("High code complexity detected")
        if scores.get('testing', 0) < self.thresholds['testing']['min_test_coverage']:
            issues.append("Insufficient test coverage")
        if scores.get('linting', 0) < 70:
            issues.append("Code style and linting issues found")
        if scores.get('duplication', 0) < 80:
            issues.append("Code duplication detected")
        return issues

    def _generate_recommendations(self, scores: Dict[str, float]) -> List[str]:
        """Generate code quality recommendations"""
        recommendations = []
        if scores.get('complexity', 0) < 80:
            recommendations.append("Refactor high-complexity functions (>10 cyclomatic complexity)")
        if scores.get('testing', 0) < 70:
            recommendations.append(f"Increase test coverage to at least {self.thresholds['testing']['min_test_coverage']}%")
        if scores.get('linting', 0) < 80:
            recommendations.append("Fix linting issues and improve code style")
        if scores.get('duplication', 0) < 90:
            recommendations.append("Reduce code duplication through refactoring")
        return recommendations
