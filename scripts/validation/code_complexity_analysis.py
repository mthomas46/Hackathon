"""Code Complexity Analysis Script

Analyzes code complexity metrics to ensure the DDD refactor has improved
maintainability and reduced complexity compared to the monolithic approach.
"""

import os
import ast
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import statistics
from dataclasses import dataclass


@dataclass
class ComplexityMetrics:
    """Code complexity metrics for a file."""
    file_path: str
    lines_of_code: int
    functions_count: int
    classes_count: int
    average_function_length: float
    max_function_length: int
    cyclomatic_complexity_avg: float
    cyclomatic_complexity_max: int
    halstead_volume: float
    maintainability_index: float
    comment_ratio: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file_path": self.file_path,
            "lines_of_code": self.lines_of_code,
            "functions_count": self.functions_count,
            "classes_count": self.classes_count,
            "average_function_length": self.average_function_length,
            "max_function_length": self.max_function_length,
            "cyclomatic_complexity_avg": self.cyclomatic_complexity_avg,
            "cyclomatic_complexity_max": self.cyclomatic_complexity_max,
            "halstead_volume": self.halstead_volume,
            "maintainability_index": self.maintainability_index,
            "comment_ratio": self.comment_ratio
        }


class CodeComplexityAnalyzer:
    """Analyzes code complexity across the codebase."""

    def __init__(self, source_directory: str):
        """Initialize analyzer."""
        self.source_dir = Path(source_directory)
        self.metrics = []

    def analyze_codebase(self) -> Dict[str, Any]:
        """Analyze the entire codebase for complexity metrics."""
        print("🔍 Starting Code Complexity Analysis")
        print("=" * 50)

        # Find all Python files
        python_files = list(self.source_dir.glob("**/*.py"))
        print(f"📁 Found {len(python_files)} Python files to analyze")

        # Analyze each file
        for file_path in python_files:
            try:
                metrics = self._analyze_file(file_path)
                if metrics:
                    self.metrics.append(metrics)
                    print(f"✅ Analyzed: {file_path.name}")
                else:
                    print(f"⚠️  Skipped: {file_path.name} (empty or invalid)")
            except Exception as e:
                print(f"❌ Error analyzing {file_path.name}: {e}")

        # Calculate aggregate metrics
        summary = self._calculate_summary_metrics()

        # Generate complexity assessment
        assessment = self._assess_complexity_health(summary)

        # Generate recommendations
        recommendations = self._generate_complexity_recommendations(summary)

        results = {
            "file_metrics": [m.to_dict() for m in self.metrics],
            "summary": summary,
            "assessment": assessment,
            "recommendations": recommendations,
            "analysis_timestamp": __import__('time').time()
        }

        print("\n📊 COMPLEXITY ANALYSIS SUMMARY:")
        print(f"   Files Analyzed: {summary['total_files']}")
        print(f"   Average LOC: {summary['avg_loc']:.0f}")
        print(f"   Complexity Score: {assessment['overall_score']:.1f}/10")
        print(f"   Maintainability: {assessment['maintainability_grade']}")

        return results

    def _analyze_file(self, file_path: Path) -> Optional[ComplexityMetrics]:
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content.strip():
                return None

            # Parse AST
            tree = ast.parse(content)

            # Basic metrics
            lines_of_code = len([line for line in content.split('\n') if line.strip()])
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

            # Function length analysis
            function_lengths = []
            for func in functions:
                func_lines = func.end_lineno - func.lineno
                function_lengths.append(func_lines)

            avg_function_length = statistics.mean(function_lengths) if function_lengths else 0
            max_function_length = max(function_lengths) if function_lengths else 0

            # Cyclomatic complexity (simplified)
            complexity_scores = []
            for func in functions:
                complexity = self._calculate_cyclomatic_complexity(func)
                complexity_scores.append(complexity)

            avg_complexity = statistics.mean(complexity_scores) if complexity_scores else 0
            max_complexity = max(complexity_scores) if complexity_scores else 0

            # Halstead volume (simplified)
            halstead_volume = self._calculate_halstead_volume(content)

            # Maintainability index (simplified)
            maintainability_index = self._calculate_maintainability_index(
                lines_of_code, avg_complexity, halstead_volume
            )

            # Comment ratio
            comment_lines = len(re.findall(r'^\s*#.*', content, re.MULTILINE))
            comment_ratio = (comment_lines / lines_of_code * 100) if lines_of_code > 0 else 0

            return ComplexityMetrics(
                file_path=str(file_path.relative_to(self.source_dir)),
                lines_of_code=lines_of_code,
                functions_count=len(functions),
                classes_count=len(classes),
                average_function_length=avg_function_length,
                max_function_length=max_function_length,
                cyclomatic_complexity_avg=avg_complexity,
                cyclomatic_complexity_max=max_complexity,
                halstead_volume=halstead_volume,
                maintainability_index=maintainability_index,
                comment_ratio=comment_ratio
            )

        except Exception as e:
            print(f"Warning: Could not analyze {file_path}: {e}")
            return None

    def _calculate_cyclomatic_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function (simplified)."""
        complexity = 1  # Base complexity

        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers) + 1

        return complexity

    def _calculate_halstead_volume(self, content: str) -> float:
        """Calculate Halstead volume (simplified)."""
        # Count operators and operands
        operators = len(re.findall(r'[+\-*/=<>!&|^~%]+', content))
        operands = len(re.findall(r'\b\w+\b', content))

        if operators == 0 or operands == 0:
            return 0

        program_length = operators + operands
        vocabulary = len(set(re.findall(r'[+\-*/=<>!&|^~%]+|\b\w+\b', content)))

        if vocabulary == 0:
            return 0

        # Halstead volume = length * log2(vocabulary)
        import math
        return program_length * math.log2(vocabulary)

    def _calculate_maintainability_index(self, loc: int, complexity: float, volume: float) -> float:
        """Calculate maintainability index (simplified version of MI)."""
        # Simplified maintainability index formula
        # Higher values = more maintainable (0-100 scale)
        mi = 171 - 5.2 * (complexity ** 0.5) - 0.23 * (volume / loc if loc > 0 else 0) - 16.2 * (loc ** 0.5)

        # Clamp to 0-100 range
        return max(0, min(100, mi))

    def _calculate_summary_metrics(self) -> Dict[str, Any]:
        """Calculate summary statistics across all files."""
        if not self.metrics:
            return {"total_files": 0}

        # Basic aggregates
        total_files = len(self.metrics)
        total_loc = sum(m.lines_of_code for m in self.metrics)
        avg_loc = total_loc / total_files

        # Function metrics
        all_function_lengths = [m.average_function_length for m in self.metrics if m.functions_count > 0]
        avg_function_length = statistics.mean(all_function_lengths) if all_function_lengths else 0

        # Complexity metrics
        avg_complexity = statistics.mean([m.cyclomatic_complexity_avg for m in self.metrics])
        max_complexity = max([m.cyclomatic_complexity_max for m in self.metrics])

        # Maintainability metrics
        avg_maintainability = statistics.mean([m.maintainability_index for m in self.metrics])

        # File size distribution
        loc_values = [m.lines_of_code for m in self.metrics]
        loc_median = statistics.median(loc_values)
        loc_stddev = statistics.stdev(loc_values) if len(loc_values) > 1 else 0

        return {
            "total_files": total_files,
            "total_loc": total_loc,
            "avg_loc": avg_loc,
            "median_loc": loc_median,
            "loc_stddev": loc_stddev,
            "avg_function_length": avg_function_length,
            "avg_complexity": avg_complexity,
            "max_complexity": max_complexity,
            "avg_maintainability": avg_maintainability,
            "files_over_500_loc": len([m for m in self.metrics if m.lines_of_code > 500]),
            "files_over_1000_loc": len([m for m in self.metrics if m.lines_of_code > 1000]),
            "high_complexity_files": len([m for m in self.metrics if m.cyclomatic_complexity_max > 10])
        }

    def _assess_complexity_health(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall code complexity health."""
        score = 10  # Start with perfect score

        # Penalize for large files
        large_files_penalty = summary.get("files_over_1000_loc", 0) * 2
        score -= large_files_penalty

        # Penalize for high complexity
        high_complexity_penalty = summary.get("high_complexity_files", 0) * 1.5
        score -= high_complexity_penalty

        # Penalize for low maintainability
        avg_maintainability = summary.get("avg_maintainability", 100)
        if avg_maintainability < 50:
            score -= 3
        elif avg_maintainability < 70:
            score -= 1.5

        # Penalize for high LOC variance (indicates inconsistent file sizes)
        loc_stddev = summary.get("loc_stddev", 0)
        avg_loc = summary.get("avg_loc", 0)
        if avg_loc > 0 and loc_stddev / avg_loc > 0.8:  # High variance
            score -= 1

        # Clamp score
        final_score = max(0, min(10, score))

        # Determine grade
        if final_score >= 8.5:
            grade = "A+ (Excellent)"
        elif final_score >= 7.5:
            grade = "A (Very Good)"
        elif final_score >= 6.5:
            grade = "B (Good)"
        elif final_score >= 5.5:
            grade = "C (Fair)"
        elif final_score >= 4.5:
            grade = "D (Poor)"
        else:
            grade = "F (Needs Work)"

        return {
            "overall_score": final_score,
            "maintainability_grade": grade,
            "complexity_health": "excellent" if final_score >= 8 else
                               "good" if final_score >= 6 else
                               "fair" if final_score >= 4 else "poor"
        }

    def _generate_complexity_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving code complexity."""
        recommendations = []

        # Large file recommendations
        large_files = summary.get("files_over_1000_loc", 0)
        if large_files > 0:
            recommendations.append(f"Break down {large_files} files over 1000 LOC into smaller, focused modules")

        # Complexity recommendations
        high_complexity_files = summary.get("high_complexity_files", 0)
        if high_complexity_files > 0:
            recommendations.append(f"Refactor {high_complexity_files} high-complexity functions using extraction methods")

        # Maintainability recommendations
        avg_maintainability = summary.get("avg_maintainability", 100)
        if avg_maintainability < 70:
            recommendations.append("Improve code documentation and add type hints to increase maintainability")

        # Function size recommendations
        avg_function_length = summary.get("avg_function_length", 0)
        if avg_function_length > 50:
            recommendations.append("Extract methods from long functions (average length > 50 lines)")

        # Consistency recommendations
        loc_stddev = summary.get("loc_stddev", 0)
        avg_loc = summary.get("avg_loc", 0)
        if avg_loc > 0 and loc_stddev / avg_loc > 0.8:
            recommendations.append("Standardize file sizes and module organization for better consistency")

        if not recommendations:
            recommendations.append("Code complexity is well-managed - continue following current best practices")

        return recommendations


def main():
    """Main complexity analysis execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Code Complexity Analysis")
    parser.add_argument("--source", default="services/analysis-service",
                       help="Source directory to analyze")
    parser.add_argument("--output", default="code_complexity_analysis.json",
                       help="Output file for results")

    args = parser.parse_args()

    print("🔍 Code Complexity Analysis")
    print("=" * 40)

    analyzer = CodeComplexityAnalyzer(args.source)
    results = analyzer.analyze_codebase()

    # Save results
    import json
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Results saved to: {args.output}")

    # Complexity assessment
    assessment = results.get("assessment", {})
    score = assessment.get("overall_score", 0)

    if score >= 8:
        print("🎉 EXCELLENT: Code complexity is well-managed!")
    elif score >= 6:
        print("✅ GOOD: Code complexity is acceptable")
    elif score >= 4:
        print("⚠️  FAIR: Some complexity improvements recommended")
    else:
        print("❌ CONCERNS: Code complexity needs significant attention")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
