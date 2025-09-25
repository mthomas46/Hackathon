"""Core analysis services for the analysis service.

Provides core analysis functions for commit messages, code structure,
file content, and refactoring suggestions.
"""

from typing import Dict, List

from services.shared.infrastructure.config import load_service_config

from .file_analyzers import analyze_python_file, analyze_js_file, analyze_java_file
from ..utilities.analysis_utils import get_file_type, is_good_commit_message, is_conventional_commit

config = load_service_config()


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
        elif len(message) > config.limits.max_message_length:
            analysis["message_quality"]["needs_improvement"] += 1
            analysis["issues"].append(f"Commit message too long: '{message[:50]}...'")
        elif is_good_commit_message(message):
            analysis["message_quality"]["good_messages"] += 1

            # Additional pattern analysis
            if len(message.split()) > 5:
                analysis["patterns"]["descriptive"] += 1
            if len(message) < 72:
                analysis["patterns"]["concise"] += 1
            if is_conventional_commit(message):
                analysis["patterns"]["conventional_commits"] += 1
            if "#" in message or "fixes" in message.lower() or "closes" in message.lower():
                analysis["patterns"]["has_issue_references"] += 1
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
        file_type = get_file_type(filename)
        analysis["file_types"][file_type] = analysis["file_types"].get(file_type, 0) + 1

        # Check for large files
        lines = file_data.get("lines", [])
        if len(lines) > 500:
            analysis["complexity_indicators"]["large_files"] += 1
            analysis["structure_issues"].append(f"Large file: {filename} ({len(lines)} lines)")

        # Analyze file content if available
        if lines:
            content_analysis = analyze_file_content({"content": "\n".join(lines), "filename": filename}, file_type)
            analysis["complexity_indicators"]["long_functions"] += len(content_analysis.get("long_methods", []))

    # Generate recommendations
    if analysis["complexity_indicators"]["large_files"] > 0:
        analysis["recommendations"].append("Consider breaking down large files into smaller modules")

    if analysis["complexity_indicators"]["long_functions"] > 0:
        analysis["recommendations"].append("Refactor long functions into smaller, focused methods")

    return analysis


def analyze_file_content(file_data: dict, file_type: str) -> dict:
    """Analyze file content for issues and patterns."""
    content = file_data.get("content", "")
    filename = file_data.get("filename", "")

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

    lines = content.split("\n")
    analysis["complexity"]["lines_of_code"] = len([line for line in lines if line.strip()])

    # Language-specific analysis
    if file_type == "python":
        result = analyze_python_file(lines)
        analysis["issues"].extend(result.get("complex_functions", []))
        analysis["long_methods"].extend(result.get("long_methods", []))
    elif file_type == "javascript":
        result = analyze_js_file(lines)
        analysis["issues"].extend(result.get("complex_functions", []))
        analysis["long_methods"].extend(result.get("long_methods", []))
    elif file_type == "java":
        result = analyze_java_file(lines)
        analysis["issues"].extend(result.get("complex_functions", []))
        analysis["long_methods"].extend(result.get("long_methods", []))

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
