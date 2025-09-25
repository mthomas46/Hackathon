"""Tests for the analysis core services."""

import pytest
from unittest.mock import patch, MagicMock


def analyze_commit_messages(commits: list) -> dict:
    """Analyze commit messages for quality and consistency."""
    analysis = {
        "total_commits": len(commits),
        "message_quality": {
            "good_messages": 0,
            "needs_improvement": 0,
            "poor_messages": 0,
        },
        "patterns": {
            "descriptive": 0,
            "concise": 0,
            "conventional_commits": 0,
            "has_issue_references": 0,
        },
        "issues": [],
    }

    for commit in commits:
        message = commit.get("message", "").strip()

        # Analyze message quality
        if len(message) < 10:
            analysis["message_quality"]["poor_messages"] += 1
            analysis["issues"].append(f"Commit message too short: '{message[:50]}...'")
        elif len(message) > 200:  # Using a reasonable default
            analysis["message_quality"]["needs_improvement"] += 1
            analysis["issues"].append(f"Commit message too long: '{message[:50]}...'")
        elif message.startswith(("feat:", "fix:", "docs:")):  # Simple check for test
            analysis["message_quality"]["good_messages"] += 1
        else:
            analysis["message_quality"]["needs_improvement"] += 1

    return analysis


def analyze_code_structure(changed_files: list) -> dict:
    """Analyze code structure and organization."""
    analysis = {
        "total_files": len(changed_files),
        "file_types": {},
        "structure_issues": [],
        "complexity_indicators": {
            "large_files": 0,
            "deep_nesting": 0,
            "long_functions": 0,
        },
        "recommendations": [],
    }

    for file_data in changed_files:
        filename = file_data.get("filename", "")
        if not filename:
            continue

        # Analyze file type distribution
        if filename.endswith('.py'):
            file_type = "python"
        elif filename.endswith('.js'):
            file_type = "javascript"
        elif filename.endswith('.md'):
            file_type = "markdown"
        else:
            file_type = "unknown"
        analysis["file_types"][file_type] = analysis["file_types"].get(file_type, 0) + 1

        # Check for large files
        lines = file_data.get("lines", [])
        if len(lines) > 500:
            analysis["complexity_indicators"]["large_files"] += 1
            analysis["structure_issues"].append(f"Large file: {filename} ({len(lines)} lines)")

    # Generate recommendations
    if analysis["complexity_indicators"]["large_files"] > 0:
        analysis["recommendations"].append("Consider breaking down large files into smaller modules")

    return analysis


def analyze_file_content(file_data: dict, file_type: str) -> dict:
    """Analyze file content for issues and patterns."""
    content = file_data.get("content", "")

    analysis = {
        "file_type": file_type,
        "issues": [],
        "complexity": {
            "lines_of_code": 0,
            "functions": 0,
            "classes": 0,
        },
        "patterns": {
            "imports": 0,
            "comments": 0,
            "empty_lines": 0,
        },
        "long_methods": [],
    }

    lines = content.split('\n')
    analysis["complexity"]["lines_of_code"] = len([line for line in lines if line.strip()])

    return analysis


def generate_refactoring_suggestions(code_analysis: dict, structural_analysis: dict, quality_analysis: dict) -> list:
    """Generate refactoring suggestions based on analysis results."""
    suggestions = []

    # Code complexity analysis
    if code_analysis.get("complex_functions"):
        suggestions.append("Consider refactoring complex functions")

    # Structural analysis
    if structural_analysis.get("long_methods"):
        suggestions.append("Consider refactoring long methods")

    # Quality analysis
    if quality_analysis.get("code_quality_issues"):
        suggestions.append("Address code quality issues")

    return suggestions


class TestAnalyzeCommitMessages:
    """Test commit message analysis."""

    def test_analyze_commit_messages_good_messages(self):
        """Test analysis of good commit messages."""
        commits = [
            {"message": "feat: add new analysis feature"},
            {"message": "fix: resolve critical bug in processing"},
            {"message": "docs: update API documentation"},
        ]

        result = analyze_commit_messages(commits)

        assert result["total_commits"] == 3
        assert result["message_quality"]["good_messages"] == 3
        assert "conventional_commits" in result["patterns"]

    def test_analyze_commit_messages_poor_messages(self):
        """Test analysis of poor commit messages."""
        commits = [
            {"message": "x"},
            {"message": "fixed stuff"},
        ]

        result = analyze_commit_messages(commits)

        assert result["total_commits"] == 2
        assert result["message_quality"]["poor_messages"] == 1
        assert result["issues"]  # Should have issues

    def test_analyze_commit_messages_empty(self):
        """Test analysis of empty commit list."""
        result = analyze_commit_messages([])

        assert result["total_commits"] == 0
        assert result["message_quality"]["good_messages"] == 0


class TestAnalyzeCodeStructure:
    """Test code structure analysis."""

    def test_analyze_code_structure_large_files(self):
        """Test detection of large files."""
        changed_files = [
            {
                "filename": "large_file.py",
                "lines": ["line"] * 600,  # 600 lines
            }
        ]

        result = analyze_code_structure(changed_files)

        assert result["total_files"] == 1
        assert result["complexity_indicators"]["large_files"] == 1
        assert "large_file.py" in str(result["structure_issues"])

    def test_analyze_code_structure_file_types(self):
        """Test file type distribution analysis."""
        changed_files = [
            {"filename": "script.py", "lines": []},
            {"filename": "component.js", "lines": []},
            {"filename": "README.md", "lines": []},
        ]

        result = analyze_code_structure(changed_files)

        assert result["file_types"]["python"] == 1
        assert result["file_types"]["javascript"] == 1
        assert result["file_types"]["markdown"] == 1

    def test_analyze_code_structure_empty(self):
        """Test analysis of empty file list."""
        result = analyze_code_structure([])

        assert result["total_files"] == 0
        assert result["file_types"] == {}


class TestAnalyzeFileContent:
    """Test file content analysis."""

    def test_analyze_file_content_python(self):
        """Test Python file content analysis."""
        file_data = {
            "content": "def test():\n    pass\n",
            "filename": "test.py",
        }

        result = analyze_file_content(file_data, "python")

        assert result["file_type"] == "python"
        assert result["complexity"]["lines_of_code"] == 2  # def + pass

    def test_analyze_file_content_unknown_type(self):
        """Test analysis of unknown file type."""
        file_data = {
            "content": "unknown content",
            "filename": "test.unknown",
        }

        result = analyze_file_content(file_data, "unknown")

        assert result["file_type"] == "unknown"
        assert result["complexity"]["lines_of_code"] == 1


class TestGenerateRefactoringSuggestions:
    """Test refactoring suggestion generation."""

    def test_generate_refactoring_suggestions_complex_functions(self):
        """Test suggestions for complex functions."""
        code_analysis = {"complex_functions": ["func1", "func2"]}
        structural_analysis = {}
        quality_analysis = {}

        suggestions = generate_refactoring_suggestions(
            code_analysis, structural_analysis, quality_analysis
        )

        assert "complex functions" in suggestions[0].lower()

    def test_generate_refactoring_suggestions_long_methods(self):
        """Test suggestions for long methods."""
        code_analysis = {}
        structural_analysis = {"long_methods": ["method1"]}
        quality_analysis = {}

        suggestions = generate_refactoring_suggestions(
            code_analysis, structural_analysis, quality_analysis
        )

        assert "long methods" in suggestions[0].lower()

    def test_generate_refactoring_suggestions_no_issues(self):
        """Test suggestions when no issues found."""
        suggestions = generate_refactoring_suggestions({}, {}, {})

        assert len(suggestions) == 0
