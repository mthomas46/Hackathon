"""Test Structure Validation Script

Validates that the test structure is properly organized and follows best practices
after the DDD refactor, without requiring full test execution.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import ast
import re


class TestStructureValidator:
    """Validates test structure and organization."""

    def __init__(self, test_directory: str):
        """Initialize validator."""
        self.test_dir = Path(test_directory)
        self.results = {}

    def validate_test_structure(self) -> Dict[str, Any]:
        """Validate the overall test structure."""
        print("🧪 Validating test structure and organization...")

        structure_validation = self._validate_directory_structure()
        test_files_validation = self._validate_test_files()
        coverage_validation = self._validate_test_coverage()

        # Calculate overall score
        validations = [structure_validation, test_files_validation, coverage_validation]
        overall_score = sum(v.get("score", 0) for v in validations) / len(validations)

        result = {
            "structure_validation": structure_validation,
            "test_files_validation": test_files_validation,
            "coverage_validation": coverage_validation,
            "overall_score": round(overall_score, 2),
            "recommendations": self._generate_recommendations(validations)
        }

        print("\n📊 TEST STRUCTURE VALIDATION:")
        print(f"Overall Score: {result['overall_score']:.1f}/10")

        if result["recommendations"]:
            print("💡 Recommendations:")
            for rec in result["recommendations"]:
                print(f"   • {rec}")

        return result

    def _validate_directory_structure(self) -> Dict[str, Any]:
        """Validate test directory structure follows best practices."""
        expected_structure = {
            "domain": ["test_domain_repositories.py", "test_domain_services.py", "test_domain_entities.py"],
            "application": ["test_application_services.py", "test_use_cases.py", "test_dtos.py"],
            "infrastructure": ["test_repositories.py", "test_external_services.py"],
            "presentation": ["test_controllers.py", "test_models.py"],
            "integration": ["test_end_to_end_integration.py", "test_application_infrastructure_integration.py"],
            "performance": ["test_performance_validation.py"],
            "e2e": ["test_complete_user_workflows.py"]
        }

        score = 0
        issues = []
        found_files = []

        for category, expected_files in expected_structure.items():
            category_path = self.test_dir / category
            if category_path.exists():
                existing_files = [f.name for f in category_path.glob("test_*.py")]
                found_files.extend([f"{category}/{f}" for f in existing_files])

                # Check if we have at least some test files for this category
                if existing_files:
                    score += 1
                else:
                    issues.append(f"No test files found in {category}/")
            else:
                issues.append(f"Missing test directory: {category}/")

        # Bonus points for additional organization
        if (self.test_dir / "fixtures").exists():
            score += 0.5
        if (self.test_dir / "helpers").exists():
            score += 0.5

        return {
            "score": min(10, score * 2),  # Scale to 0-10
            "issues": issues,
            "found_files": found_files,
            "expected_categories": list(expected_structure.keys())
        }

    def _validate_test_files(self) -> Dict[str, Any]:
        """Validate individual test files for best practices."""
        test_files = list(self.test_dir.glob("**/*.py"))
        test_files.extend(list(self.test_dir.glob("*.py")))  # Include root level

        score = 0
        total_files = len(test_files)
        analyzed_files = 0
        issues = []

        for test_file in test_files:
            if test_file.name.startswith("test_") or test_file.name == "conftest.py":
                analyzed_files += 1
                file_score = self._analyze_test_file(test_file)
                score += file_score

                if file_score < 0.7:  # Below 70% quality
                    issues.append(f"Low quality test file: {test_file.name}")

        avg_score = score / analyzed_files if analyzed_files > 0 else 0

        return {
            "score": min(10, avg_score * 10),
            "total_test_files": analyzed_files,
            "issues": issues,
            "average_file_score": round(avg_score, 2)
        }

    def _analyze_test_file(self, file_path: Path) -> float:
        """Analyze a single test file for quality indicators."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse the AST
            tree = ast.parse(content)

            score = 0
            max_score = 6

            # Check for class-based tests
            has_test_classes = any(
                isinstance(node, ast.ClassDef) and node.name.startswith('Test')
                for node in ast.walk(tree)
            )
            if has_test_classes:
                score += 1

            # Check for fixtures
            has_fixtures = 'fixture' in content.lower()
            if has_fixtures:
                score += 1

            # Check for parametrized tests
            has_parametrize = 'parametrize' in content
            if has_parametrize:
                score += 1

            # Check for assertions
            assertion_count = content.count('assert ')
            if assertion_count > 0:
                score += 1

            # Check for docstrings
            has_docstrings = any(
                isinstance(node, (ast.FunctionDef, ast.ClassDef)) and
                ast.get_docstring(node) is not None
                for node in ast.walk(tree)
            )
            if has_docstrings:
                score += 1

            # Check for proper imports
            has_pytest_import = 'import pytest' in content or 'from pytest' in content
            if has_pytest_import:
                score += 1

            return score / max_score

        except Exception as e:
            print(f"Warning: Could not analyze {file_path}: {e}")
            return 0.0

    def _validate_test_coverage(self) -> Dict[str, Any]:
        """Validate test coverage for different layers."""
        layers = {
            "domain": ["entities", "services", "factories"],
            "application": ["use_cases", "dto", "services"],
            "infrastructure": ["repositories", "config"],
            "presentation": ["controllers", "models"]
        }

        coverage_score = 0
        total_components = 0
        covered_components = 0

        for layer, components in layers.items():
            for component in components:
                total_components += 1

                # Check if there's a corresponding test
                test_patterns = [
                    f"{layer}/test_{component}.py",
                    f"{layer}/test_{layer}_{component}.py",
                    f"test_{component}.py"
                ]

                has_test = any(
                    (self.test_dir / pattern).exists()
                    for pattern in test_patterns
                )

                if has_test:
                    covered_components += 1
                    coverage_score += 1

        coverage_percentage = (covered_components / total_components) * 100 if total_components > 0 else 0

        return {
            "score": min(10, coverage_percentage / 10),  # Convert percentage to 0-10 scale
            "coverage_percentage": round(coverage_percentage, 1),
            "covered_components": covered_components,
            "total_components": total_components
        }

    def _generate_recommendations(self, validations: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        # Structure recommendations
        structure_val = next(v for v in validations if "issues" in v)
        if structure_val.get("issues"):
            recommendations.append("Address structural issues in test organization")

        # Test file quality recommendations
        test_files_val = next(v for v in validations if "average_file_score" in v)
        if test_files_val.get("average_file_score", 0) < 0.7:
            recommendations.append("Improve test file quality with better assertions and fixtures")

        # Coverage recommendations
        coverage_val = next(v for v in validations if "coverage_percentage" in v)
        if coverage_val.get("coverage_percentage", 0) < 70:
            recommendations.append("Increase test coverage for better reliability")

        # General recommendations
        if not recommendations:
            recommendations.append("Test structure looks good - maintain current standards")

        return recommendations


def main():
    """Main validation function."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Structure Validation")
    parser.add_argument("--test-dir", default="services/analysis-service/tests",
                       help="Path to test directory")
    parser.add_argument("--output", default="test_structure_validation.json",
                       help="Output file for results")

    args = parser.parse_args()

    print("🧪 Test Structure Validation")
    print("=" * 40)

    validator = TestStructureValidator(args.test_dir)
    results = validator.validate_test_structure()

    # Save results
    import json
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Results saved to: {args.output}")

    # Return appropriate exit code
    if results["overall_score"] >= 7:
        print("✅ EXCELLENT: Test structure is well-organized!")
        return 0
    elif results["overall_score"] >= 5:
        print("⚠️  GOOD: Test structure is acceptable but could be improved")
        return 0
    else:
        print("❌ NEEDS WORK: Test structure requires significant improvements")
        return 1


if __name__ == "__main__":
    sys.exit(main())
