"""Unit tests for bedrock proxy template functionality."""

import pytest
from modules.templates import (
    detect_template_from_prompt,
    build_template_sections,
    generate_default_title,
    render_markdown,
    render_text,
    VALID_TEMPLATES,
    VALID_FORMATS,
    SUPPORTED_TEMPLATES,
    SUPPORTED_FORMATS,
    TEMPLATES,
)


class TestTemplateConstants:
    """Test suite for template constants and configuration."""

    def test_valid_templates_list(self):
        """Test that VALID_TEMPLATES matches expected values."""
        expected = ["summary", "risks", "decisions", "pr_confidence", "life_of_ticket"]
        assert VALID_TEMPLATES == expected

    def test_valid_formats_list(self):
        """Test that VALID_FORMATS matches expected values."""
        expected = ["md", "txt", "json"]
        assert VALID_FORMATS == expected

    def test_supported_templates_matches_valid(self):
        """Test that SUPPORTED_TEMPLATES matches VALID_TEMPLATES."""
        assert SUPPORTED_TEMPLATES == VALID_TEMPLATES

    def test_supported_formats_matches_valid(self):
        """Test that SUPPORTED_FORMATS matches VALID_FORMATS."""
        assert SUPPORTED_FORMATS == VALID_FORMATS

    def test_templates_structure(self):
        """Test that TEMPLATES has correct structure."""
        assert isinstance(TEMPLATES, dict)
        assert len(TEMPLATES) == len(VALID_TEMPLATES)

        for template_name in VALID_TEMPLATES:
            assert template_name in TEMPLATES
            template_config = TEMPLATES[template_name]
            assert "sections" in template_config
            assert isinstance(template_config["sections"], dict)


class TestDetectTemplateFromPrompt:
    """Test suite for template detection from prompts."""

    def test_summary_template_detection(self):
        """Test detection of summary template."""
        prompts = [
            "summary of this document",
            "Give me a summary of this content",
            "Provide a brief summary",
            "This is a summary document",
        ]

        for prompt in prompts:
            result = detect_template_from_prompt(prompt)
            assert result == "summary"

    def test_risks_template_detection(self):
        """Test detection of risks template."""
        prompts = [
            "What are the risks involved?",
            "Analyze the risks for this project",
            "Identify potential risks",
            "Risk assessment needed",
        ]

        for prompt in prompts:
            assert detect_template_from_prompt(prompt) == "risks"

    def test_decisions_template_detection(self):
        """Test detection of decisions template."""
        prompts = [
            "What decisions need to be made?",
            "Document the decision process",
            "Decision analysis required",
            "Help me make a decision",
        ]

        for prompt in prompts:
            assert detect_template_from_prompt(prompt) == "decisions"

    def test_pr_confidence_template_detection(self):
        """Test detection of pr_confidence template."""
        prompts = [
            "Analyze this pull request confidence",
            "Check PR confidence",
            "Review the pull request confidence",
            "PR confidence analysis needed",
        ]

        for prompt in prompts:
            result = detect_template_from_prompt(prompt)
            assert result == "pr_confidence"

    def test_life_of_ticket_template_detection(self):
        """Test detection of life_of_ticket template."""
        prompts = [
            "Track this ticket lifecycle",
            "Life of ticket analysis",
            "Jira ticket timeline",
            "Ticket TICKET-123 analysis",
        ]

        # Only the ones with both "ticket" and ("life" or "track") will match
        expected_results = ["life_of_ticket", "life_of_ticket", "", ""]

        for prompt, expected in zip(prompts, expected_results):
            result = detect_template_from_prompt(prompt)
            assert result == expected

    def test_default_template_fallback(self):
        """Test that unknown prompts return empty string."""
        unknown_prompts = [
            "Hello world",
            "Random text without keywords",
            "Unrelated content",
            "Just some words",
        ]

        for prompt in unknown_prompts:
            result = detect_template_from_prompt(prompt)
            assert result == ""

        # Empty prompt also returns empty string
        assert detect_template_from_prompt("") == ""

    def test_case_insensitive_detection(self):
        """Test that detection is case-insensitive."""
        prompts = [
            "SUMMARY this document",
            "What are the RISKS?",
            "DECISIONS needed",
            "analyze this PULL REQUEST confidence",
            "TICKET lifecycle",
        ]

        expected = ["summary", "risks", "decisions", "pr_confidence", "life_of_ticket"]

        for prompt, expected_template in zip(prompts, expected):
            result = detect_template_from_prompt(prompt)
            assert result == expected_template


class TestBuildTemplateSections:
    """Test suite for template section building."""

    def test_summary_template_sections(self):
        """Test building sections for summary template."""
        sections = build_template_sections("summary", "Test content")

        assert "Summary" in sections
        assert "Key Points" in sections

        # Summary should be extracted from content
        assert isinstance(sections["Summary"], list)
        # Key Points should be predefined
        assert sections["Key Points"] == ["Decision captured", "Risks identified", "Actions listed"]

    def test_risks_template_sections(self):
        """Test building sections for risks template."""
        sections = build_template_sections("risks", "Some content")

        assert "Risks" in sections
        assert "Mitigations" in sections

        # Both should be predefined lists
        assert isinstance(sections["Risks"], list)
        assert isinstance(sections["Mitigations"], list)
        assert len(sections["Risks"]) > 0
        assert len(sections["Mitigations"]) > 0

    def test_decisions_template_sections(self):
        """Test building sections for decisions template."""
        sections = build_template_sections("decisions", "Content")

        assert "Decisions" in sections
        assert "Rationale" in sections

        assert isinstance(sections["Decisions"], list)
        assert isinstance(sections["Rationale"], list)

    def test_pr_confidence_template_sections(self):
        """Test building sections for pr_confidence template."""
        sections = build_template_sections("pr_confidence", "PR content")

        assert "Inputs" in sections
        assert "Extracted Endpoints" in sections
        assert "Confidence" in sections
        assert "Suggestions" in sections

    def test_life_of_ticket_template_sections(self):
        """Test building sections for life_of_ticket template."""
        sections = build_template_sections("life_of_ticket", "Ticket content")

        assert "Timeline" in sections
        assert "Summary" in sections

    def test_unknown_template_fallback(self):
        """Test fallback behavior for unknown templates."""
        sections = build_template_sections("unknown", "Content")

        # Should return Echo section with bullet points for unknown templates
        assert "Echo" in sections
        assert isinstance(sections["Echo"], list)


class TestGenerateDefaultTitle:
    """Test suite for default title generation."""

    def test_summary_title(self):
        """Test title generation for summary template."""
        title = generate_default_title("summary")
        assert "Summary" in title or "Analysis" in title

    def test_risks_title(self):
        """Test title generation for risks template."""
        title = generate_default_title("risks")
        assert "Risk" in title or "Assessment" in title

    def test_decisions_title(self):
        """Test title generation for decisions template."""
        title = generate_default_title("decisions")
        assert "Decision" in title

    def test_pr_confidence_title(self):
        """Test title generation for pr_confidence template."""
        title = generate_default_title("pr_confidence")
        assert "PR" in title or "Pull Request" in title or "Confidence" in title

    def test_life_of_ticket_title(self):
        """Test title generation for life_of_ticket template."""
        title = generate_default_title("life_of_ticket")
        assert "Ticket" in title or "Lifecycle" in title

    def test_unknown_template_title(self):
        """Test title generation for unknown templates."""
        title = generate_default_title("unknown")
        assert isinstance(title, str)
        assert len(title) > 0


class TestRenderMarkdown:
    """Test suite for markdown rendering."""

    def test_basic_markdown_rendering(self):
        """Test basic markdown rendering with sections."""
        sections = {
            "Summary": ["Point 1", "Point 2"],
            "Details": ["Detail A", "Detail B"]
        }

        result = render_markdown("Test Title", sections)

        assert "# Test Title" in result
        assert "## Summary" in result
        assert "## Details" in result
        assert "- Point 1" in result
        assert "- Point 2" in result
        assert "- Detail A" in result
        assert "- Detail B" in result

    def test_empty_sections(self):
        """Test markdown rendering with empty sections."""
        sections = {}
        result = render_markdown("Empty Title", sections)

        assert "# Empty Title" in result
        assert "##" not in result  # No section headers

    def test_mixed_content_types(self):
        """Test rendering with list content in sections."""
        sections = {
            "List Section": ["Item 1", "Item 2"],
            "Text Section": ["Plain text content"]
        }

        result = render_markdown("Mixed Title", sections)

        assert "# Mixed Title" in result
        assert "## List Section" in result
        assert "## Text Section" in result
        assert "- Item 1" in result
        assert "- Plain text content" in result


class TestRenderText:
    """Test suite for plain text rendering."""

    def test_basic_text_rendering(self):
        """Test basic text rendering with sections."""
        sections = {
            "Summary": ["Point 1", "Point 2"],
            "Details": ["Detail A", "Detail B"]
        }

        result = render_text("Test Title", sections)

        assert "Test Title" in result
        assert "Summary:" in result
        assert "Details:" in result
        assert "Point 1" in result
        assert "Detail A" in result

    def test_empty_sections_text(self):
        """Test text rendering with empty sections."""
        sections = {}
        result = render_text("Empty Title", sections)

        assert "Empty Title" in result
        assert ":" not in result  # No section headers

    def test_text_formatting(self):
        """Test that text rendering uses simple formatting."""
        sections = {
            "Section": ["Item 1", "Item 2"]
        }

        result = render_text("Title", sections)

        # Should use simple text formatting with dashes
        assert "Title" in result
        assert "Section:" in result
        assert "- Item 1" in result
        assert "- Item 2" in result
