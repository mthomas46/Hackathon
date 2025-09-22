"""Unit tests for prompt tuning helper functions."""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from pages.prompt_browser import (
    extract_variables_from_prompt,
    render_variable_manager,
    highlight_variables_in_text,
    estimate_token_count,
    format_prompt_content,
    analyze_prompt_content,
    apply_ai_tuning,
    run_prompt_performance_test,
    display_performance_results,
    generate_mock_version_history,
    get_mock_version_content,
    analyze_version_differences
)


class TestVariableExtraction:
    """Test variable extraction functionality."""

    def test_extract_variables_basic(self):
        """Test basic variable extraction."""
        content = "Hello {{name}}, welcome to {{company}}!"
        variables = extract_variables_from_prompt(content)
        assert variables == ["name", "company"]

    def test_extract_variables_duplicates(self):
        """Test that duplicate variables are removed."""
        content = "Hello {{name}}, {{name}} is great!"
        variables = extract_variables_from_prompt(content)
        assert variables == ["name"]

    def test_extract_variables_no_variables(self):
        """Test content with no variables."""
        content = "Hello world, this is a test."
        variables = extract_variables_from_prompt(content)
        assert variables == []

    def test_extract_variables_complex(self):
        """Test complex variable extraction."""
        content = "Generate {{language}} code for {{task}} with {{framework}} framework."
        variables = extract_variables_from_prompt(content)
        assert variables == ["language", "task", "framework"]


class TestVariableHighlighting:
    """Test variable highlighting functionality."""

    def test_highlight_variables(self):
        """Test variable highlighting in text."""
        content = "Hello {{name}}, welcome!"
        highlighted = highlight_variables_in_text(content)
        assert "**{{name}}**" in highlighted

    def test_highlight_multiple_variables(self):
        """Test highlighting multiple variables."""
        content = "Hello {{name}}, welcome to {{company}}!"
        highlighted = highlight_variables_in_text(content)
        assert "**{{name}}**" in highlighted
        assert "**{{company}}**" in highlighted


class TestTokenEstimation:
    """Test token count estimation."""

    def test_estimate_token_count_simple(self):
        """Test basic token estimation."""
        content = "Hello world"
        tokens = estimate_token_count(content)
        assert tokens == 2  # ~8 characters / 4 = 2

    def test_estimate_token_count_code(self):
        """Test token estimation for code content."""
        content = "def function():\n    return True"
        tokens = estimate_token_count(content)
        assert tokens > 2  # Should be adjusted for code

    def test_estimate_token_count_empty(self):
        """Test token estimation for empty content."""
        content = ""
        tokens = estimate_token_count(content)
        assert tokens == 1  # Minimum 1 token


class TestContentFormatting:
    """Test content formatting functionality."""

    def test_format_prompt_content_basic(self):
        """Test basic prompt formatting."""
        content = "hello   world\n\n\n\ntest"
        formatted = format_prompt_content(content)
        assert "\n\n\n" not in formatted  # Extra newlines removed
        assert formatted[0].isupper()  # First letter capitalized

    def test_format_prompt_content_variables(self):
        """Test formatting preserves variables."""
        content = "hello {{name}}   world"
        formatted = format_prompt_content(content)
        assert "{{name}}" in formatted


class TestContentAnalysis:
    """Test content analysis functionality."""

    def test_analyze_prompt_content_basic(self):
        """Test basic content analysis."""
        content = "This is a test. It has multiple sentences. Each one should be counted."
        analysis = analyze_prompt_content(content)

        assert analysis["Words"] == 13
        assert analysis["Sentences"] == 3
        assert "Variables" in analysis  # Should have variable count

    def test_analyze_prompt_content_markdown(self):
        """Test analysis of markdown content."""
        content = "# Header\n\n## Subheader\n\n- List item 1\n- List item 2\n\n```python\ncode block\n```"
        analysis = analyze_prompt_content(content)

        assert analysis["Words"] > 10  # Should count words in markdown
        assert "Technical Terms" in analysis  # Should count technical terms


class TestAITuning:
    """Test AI tuning functionality."""

    def test_apply_ai_tuning_length(self):
        """Test length optimization."""
        content = "In order to process the data, we need to..."
        tuned = apply_ai_tuning(content, {"optimize_length": True})
        assert len(tuned) < len(content) or "in order to" not in tuned.lower()

    def test_apply_ai_tuning_clarity(self):
        """Test clarity improvements."""
        content = "hello world."
        tuned = apply_ai_tuning(content, {"optimize_clarity": True})
        assert tuned[0].isupper()  # Should be capitalized

    def test_apply_ai_tuning_examples(self):
        """Test example addition."""
        content = "Generate code."
        tuned = apply_ai_tuning(content, {"add_examples": True})
        assert "example" in tuned.lower()

    def test_apply_ai_tuning_variables(self):
        """Test variable optimization."""
        content = "Use {{var}} for processing."
        tuned = apply_ai_tuning(content, {"improve_variables": True})
        # Should replace generic variable names
        assert "{{specific_var}}" in tuned

    def test_apply_ai_tuning_constraints(self):
        """Test safety constraint addition."""
        content = "Generate content."
        tuned = apply_ai_tuning(content, {"add_constraints": True})
        assert "safe" in tuned.lower() or "ethical" in tuned.lower()


class TestPerformanceTesting:
    """Test performance testing functionality."""

    def test_test_prompt_performance_basic(self):
        """Test basic performance testing."""
        content = "Test prompt content"
        results = run_prompt_performance_test(content, 3, ["response_time"])

        assert results["iterations"] == 3
        assert "response_time" in results["metrics"]
        assert "summary" in results
        assert len(results["metrics"]["response_time"]["values"]) == 3

    def test_test_prompt_performance_multiple_metrics(self):
        """Test performance testing with multiple metrics."""
        content = "Test prompt content"
        metrics = ["response_time", "token_usage", "coherence"]
        results = run_prompt_performance_test(content, 2, metrics)

        for metric in metrics:
            assert metric in results["metrics"]
            assert len(results["metrics"][metric]["values"]) == 2


class TestVersionManagement:
    """Test version management functionality."""

    def test_generate_mock_version_history(self):
        """Test mock version history generation."""
        prompt = {"content": "Test content", "id": "test_123"}
        versions = generate_mock_version_history(prompt)

        assert len(versions) >= 2  # At least 2 versions
        assert all(v["version"] >= 1 for v in versions)
        assert any(v["is_current"] for v in versions)  # One should be current

    def test_get_mock_version_content(self):
        """Test mock version content retrieval."""
        content = get_mock_version_content("Current Version")
        assert isinstance(content, str)
        assert len(content) > 0

    def test_analyze_version_differences(self):
        """Test version difference analysis."""
        content_a = "Short content."
        content_b = "This is much longer content with more details."

        differences = analyze_version_differences(content_a, content_b)
        assert len(differences) > 0
        assert any("length" in diff.lower() for diff in differences)


class TestTemplateFunctions:
    """Test template and utility functions."""

    def test_generate_sample_prompt(self):
        """Test sample prompt generation."""
        from pages.prompt_browser import generate_sample_prompt

        prompt = generate_sample_prompt("Basic Chat Prompts", "greeting")
        assert "name" in prompt
        assert "greeting" in prompt["tags"]

    def test_get_standard_prompt_templates(self):
        """Test standard template retrieval."""
        from pages.prompt_browser import get_standard_prompt_templates

        templates = get_standard_prompt_templates()
        assert len(templates) > 0
        assert all("name" in t and "content" in t for t in templates)
