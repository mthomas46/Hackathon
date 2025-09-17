"""Coverage Analyzer - Analyze and report test coverage metrics."""

import os
import json
import subprocess
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
import re


class CoverageAnalyzer:
    """Analyze test coverage and generate reports."""

    def __init__(self, source_dir: str = "services/analysis-service", test_dir: str = "services/analysis-service/tests"):
        self.source_dir = Path(source_dir)
        self.test_dir = Path(test_dir)
        self.coverage_data = {}
        self.coverage_targets = {
            'domain': 90.0,
            'application': 85.0,
            'infrastructure': 80.0,
            'presentation': 75.0,
            'overall': 85.0
        }

    def run_coverage_analysis(self) -> Dict[str, Any]:
        """Run coverage analysis using pytest-cov."""
        try:
            # Run pytest with coverage
            cmd = [
                "python", "-m", "pytest",
                f"--cov={self.source_dir}",
                f"--cov-report=json:coverage.json",
                f"--cov-report=html:htmlcov",
                f"--cov-report=term-missing",
                str(self.test_dir),
                "-v"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.source_dir.parent.parent)

            # Parse coverage data
            coverage_file = self.source_dir.parent.parent / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    self.coverage_data = json.load(f)

            return {
                'success': result.returncode == 0,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'coverage_data': self.coverage_data
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'coverage_data': {}
            }

    def analyze_coverage_by_layer(self) -> Dict[str, Dict[str, Any]]:
        """Analyze coverage metrics by architectural layer."""
        layers = {
            'domain': ['domain/'],
            'application': ['application/'],
            'infrastructure': ['infrastructure/'],
            'presentation': ['presentation/', 'main.py']
        }

        layer_coverage = {}

        for layer_name, patterns in layers.items():
            layer_files = []
            total_lines = 0
            covered_lines = 0

            for file_path, file_data in self.coverage_data.get('files', {}).items():
                if any(pattern in file_path for pattern in patterns):
                    layer_files.append(file_path)
                    total_lines += file_data.get('summary', {}).get('num_statements', 0)
                    covered_lines += file_data.get('summary', {}).get('covered_lines', 0)

            if total_lines > 0:
                coverage_percentage = (covered_lines / total_lines) * 100
            else:
                coverage_percentage = 0.0

            layer_coverage[layer_name] = {
                'files': layer_files,
                'total_lines': total_lines,
                'covered_lines': covered_lines,
                'coverage_percentage': coverage_percentage,
                'target_percentage': self.coverage_targets.get(layer_name, 80.0),
                'status': 'pass' if coverage_percentage >= self.coverage_targets.get(layer_name, 80.0) else 'fail'
            }

        return layer_coverage

    def analyze_uncovered_lines(self) -> Dict[str, List[int]]:
        """Analyze lines that are not covered by tests."""
        uncovered_lines = {}

        for file_path, file_data in self.coverage_data.get('files', {}).items():
            missing_lines = file_data.get('missing_lines', [])
            if missing_lines:
                uncovered_lines[file_path] = missing_lines

        return uncovered_lines

    def identify_critical_uncovered_code(self) -> Dict[str, List[str]]:
        """Identify critical code paths that are not covered."""
        critical_patterns = [
            r'def (create|update|delete|process|analyze|validate)',
            r'class.*Service',
            r'class.*Repository',
            r'class.*Controller',
            r'if.*error',
            r'except.*Exception',
            r'raise.*Exception'
        ]

        critical_uncovered = {}

        for file_path, missing_lines in self.analyze_uncovered_lines().items():
            if not missing_lines:
                continue

            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()

                critical_lines = []
                for line_num in missing_lines:
                    if line_num <= len(lines):
                        line_content = lines[line_num - 1].strip()
                        if any(re.search(pattern, line_content) for pattern in critical_patterns):
                            critical_lines.append(f"Line {line_num}: {line_content}")

                if critical_lines:
                    critical_uncovered[file_path] = critical_lines

            except Exception as e:
                critical_uncovered[file_path] = [f"Error reading file: {str(e)}"]

        return critical_uncovered

    def generate_coverage_report(self) -> Dict[str, Any]:
        """Generate comprehensive coverage report."""
        layer_analysis = self.analyze_coverage_by_layer()
        uncovered_lines = self.analyze_uncovered_lines()
        critical_uncovered = self.identify_critical_uncovered_code()

        # Calculate overall coverage
        total_lines = sum(layer['total_lines'] for layer in layer_analysis.values())
        total_covered = sum(layer['covered_lines'] for layer in layer_analysis.values())

        overall_coverage = (total_covered / total_lines * 100) if total_lines > 0 else 0.0

        report = {
            'timestamp': json.dumps(datetime.now().isoformat()),
            'overall_coverage': {
                'percentage': overall_coverage,
                'target_percentage': self.coverage_targets['overall'],
                'status': 'pass' if overall_coverage >= self.coverage_targets['overall'] else 'fail',
                'total_lines': total_lines,
                'covered_lines': total_covered,
                'uncovered_lines': total_lines - total_covered
            },
            'layer_coverage': layer_analysis,
            'uncovered_lines': uncovered_lines,
            'critical_uncovered': critical_uncovered,
            'test_files_count': len(list(self.test_dir.rglob("test_*.py"))),
            'recommendations': self._generate_recommendations(layer_analysis, critical_uncovered)
        }

        return report

    def _generate_recommendations(self, layer_analysis: Dict[str, Dict[str, Any]],
                                 critical_uncovered: Dict[str, List[str]]) -> List[str]:
        """Generate recommendations for improving coverage."""
        recommendations = []

        # Check layer coverage targets
        for layer_name, layer_data in layer_analysis.items():
            if layer_data['status'] == 'fail':
                recommendations.append(
                    f"Increase {layer_name} layer coverage from "
                    f"{layer_data['coverage_percentage']:.1f}% to target "
                    f"{layer_data['target_percentage']:.1f}%"
                )

        # Check for critical uncovered code
        if critical_uncovered:
            recommendations.append(
                f"Add tests for {len(critical_uncovered)} files with critical uncovered code"
            )

            # Identify most critical files
            critical_files = list(critical_uncovered.keys())[:5]  # Top 5
            if critical_files:
                recommendations.append(
                    f"Priority files to test: {', '.join(critical_files)}"
                )

        # General recommendations
        recommendations.extend([
            "Add integration tests for cross-layer interactions",
            "Add performance tests for critical code paths",
            "Add error handling and edge case tests",
            "Add security and authentication tests",
            "Review and update coverage targets based on code complexity"
        ])

        return recommendations

    def save_report(self, report: Dict[str, Any], output_file: str = "coverage_report.json"):
        """Save coverage report to file."""
        output_path = self.source_dir.parent.parent / output_file

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"Coverage report saved to: {output_path}")

    def print_summary_report(self, report: Dict[str, Any]):
        """Print a summary of the coverage report."""
        print("\n" + "="*80)
        print("TEST COVERAGE ANALYSIS REPORT")
        print("="*80)

        overall = report['overall_coverage']
        print("
OVERALL COVERAGE:"        print(".1f")
        print(f"Target:     {overall['target_percentage']:.1f}%")
        print(f"Status:     {'✅ PASS' if overall['status'] == 'pass' else '❌ FAIL'}")
        print(f"Lines:      {overall['covered_lines']}/{overall['total_lines']}")

        print("
LAYER COVERAGE:"        for layer_name, layer_data in report['layer_coverage'].items():
            status_icon = "✅" if layer_data['status'] == 'pass' else "❌"
            print("6")

        print("
CRITICAL UNCOVERED CODE:"        if report['critical_uncovered']:
            for file_path, lines in list(report['critical_uncovered'].items())[:5]:
                print(f"📁 {Path(file_path).name}:")
                for line in lines[:3]:  # Show first 3 critical lines
                    print(f"   {line}")
                if len(lines) > 3:
                    print(f"   ... and {len(lines) - 3} more critical lines")
        else:
            print("✅ No critical uncovered code found")

        print("
RECOMMENDATIONS:"        for i, rec in enumerate(report['recommendations'][:5], 1):
            print(f"{i}. {rec}")

        print("\n" + "="*80)


class CoverageEnforcer:
    """Enforce minimum coverage requirements."""

    def __init__(self, min_coverage: float = 85.0):
        self.min_coverage = min_coverage

    def enforce_coverage(self, coverage_report: Dict[str, Any]) -> bool:
        """Enforce coverage requirements and return success status."""
        overall_coverage = coverage_report['overall_coverage']['percentage']

        if overall_coverage < self.min_coverage:
            print(f"❌ Coverage requirement not met: {overall_coverage:.1f}% < {self.min_coverage:.1f}%")
            return False

        # Check layer-specific requirements
        layer_coverage = coverage_report['layer_coverage']
        for layer_name, layer_data in layer_coverage.items():
            if layer_data['status'] == 'fail':
                print(f"❌ Layer {layer_name} coverage requirement not met: "
                      f"{layer_data['coverage_percentage']:.1f}% < {layer_data['target_percentage']:.1f}%")
                return False

        print(f"✅ All coverage requirements met: {overall_coverage:.1f}% >= {self.min_coverage:.1f}%")
        return True

    def enforce_critical_coverage(self, coverage_report: Dict[str, Any]) -> bool:
        """Enforce coverage for critical code paths."""
        critical_uncovered = coverage_report['critical_uncovered']

        if critical_uncovered:
            print(f"❌ Critical code paths not covered in {len(critical_uncovered)} files")
            for file_path in list(critical_uncovered.keys())[:3]:
                print(f"   - {Path(file_path).name}")
            if len(critical_uncovered) > 3:
                print(f"   ... and {len(critical_uncovered) - 3} more files")
            return False

        print("✅ All critical code paths are covered")
        return True


class CoverageTracker:
    """Track coverage trends over time."""

    def __init__(self, history_file: str = "coverage_history.json"):
        self.history_file = Path(history_file)
        self.history = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load coverage history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def add_entry(self, coverage_report: Dict[str, Any]):
        """Add a new coverage entry to history."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'overall_coverage': coverage_report['overall_coverage']['percentage'],
            'layer_coverage': {
                layer: data['coverage_percentage']
                for layer, data in coverage_report['layer_coverage'].items()
            },
            'critical_uncovered_count': len(coverage_report['critical_uncovered'])
        }

        self.history.append(entry)

        # Keep only last 30 entries
        if len(self.history) > 30:
            self.history = self.history[-30:]

        self._save_history()

    def _save_history(self):
        """Save coverage history to file."""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def get_trends(self) -> Dict[str, Any]:
        """Get coverage trends over time."""
        if not self.history:
            return {'error': 'No coverage history available'}

        recent_entries = self.history[-10:]  # Last 10 entries

        trends = {
            'overall_trend': self._calculate_trend([e['overall_coverage'] for e in recent_entries]),
            'layer_trends': {},
            'improving_layers': [],
            'declining_layers': []
        }

        # Calculate layer trends
        layer_names = recent_entries[0]['layer_coverage'].keys()
        for layer in layer_names:
            layer_values = [e['layer_coverage'].get(layer, 0) for e in recent_entries]
            trend = self._calculate_trend(layer_values)
            trends['layer_trends'][layer] = trend

            if trend['direction'] == 'improving':
                trends['improving_layers'].append(layer)
            elif trend['direction'] == 'declining':
                trends['declining_layers'].append(layer)

        return trends

    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend direction and magnitude."""
        if len(values) < 2:
            return {'direction': 'stable', 'magnitude': 0.0}

        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]

        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        diff = second_avg - first_avg

        if abs(diff) < 0.1:  # Less than 0.1% change
            direction = 'stable'
        elif diff > 0:
            direction = 'improving'
        else:
            direction = 'declining'

        return {
            'direction': direction,
            'magnitude': abs(diff),
            'first_avg': first_avg,
            'second_avg': second_avg
        }


# Global instances
coverage_analyzer = CoverageAnalyzer()
coverage_enforcer = CoverageEnforcer()
coverage_tracker = CoverageTracker()


def run_coverage_analysis_and_report():
    """Run coverage analysis and generate report."""
    print("🔍 Running Coverage Analysis...")

    # Run analysis
    result = coverage_analyzer.run_coverage_analysis()

    if not result['success']:
        print(f"❌ Coverage analysis failed: {result.get('error', 'Unknown error')}")
        return False

    # Generate report
    report = coverage_analyzer.generate_coverage_report()

    # Save and print report
    coverage_analyzer.save_report(report)
    coverage_analyzer.print_summary_report(report)

    # Track in history
    coverage_tracker.add_entry(report)

    # Enforce requirements
    coverage_ok = coverage_enforcer.enforce_coverage(report)
    critical_ok = coverage_enforcer.enforce_critical_coverage(report)

    if coverage_ok and critical_ok:
        print("🎉 All coverage requirements met!")
        return True
    else:
        print("⚠️  Coverage requirements not fully met. See recommendations above.")
        return False


def get_coverage_trends():
    """Get coverage trends over time."""
    trends = coverage_tracker.get_trends()

    if 'error' in trends:
        print(f"❌ {trends['error']}")
        return

    print("\n📈 COVERAGE TRENDS")
    print("="*50)

    print(f"Overall: {trends['overall_trend']['direction']} "
          f"({trends['overall_trend']['magnitude']:.2f}%)")

    print("
Layer Trends:"    for layer, trend in trends['layer_trends'].items():
        print("6")

    if trends['improving_layers']:
        print(f"\n✅ Improving: {', '.join(trends['improving_layers'])}")

    if trends['declining_layers']:
        print(f"\n❌ Declining: {', '.join(trends['declining_layers'])}")


if __name__ == "__main__":
    # Run analysis when script is executed directly
    success = run_coverage_analysis_and_report()
    get_coverage_trends()

    exit(0 if success else 1)
