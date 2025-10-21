"""
Unit tests for CompletenessChecker.
"""

import pytest
from src.services.quality.completeness_checker import (
    CompletenessChecker,
    SectionType,
    get_completeness_checker
)


@pytest.mark.asyncio
class TestCompletenessChecker:
    """Test CompletenessChecker functionality."""
    
    async def test_initialization(self):
        """Test checker initialization."""
        checker = CompletenessChecker()
        assert checker is not None
        assert len(checker.placeholder_patterns) == 11
        assert checker.min_section_words == 50
    
    async def test_singleton(self):
        """Test singleton pattern."""
        checker1 = get_completeness_checker()
        checker2 = get_completeness_checker()
        assert checker1 is checker2
    
    async def test_complete_document(self):
        """Test checking a complete document."""
        checker = CompletenessChecker()
        
        artifact = {
            'title': 'Test Document',
            'type': 'guide',
            'content': '''# Test Document

## Overview
This is a comprehensive overview section with more than fifty words to meet the minimum requirement for section completeness checking. It describes the purpose and scope of the documentation.

## Installation
Step-by-step installation instructions with sufficient detail to guide users through the setup process successfully.

## Usage
Detailed usage examples and instructions with more than fifty words explaining how to use the system effectively.

## Examples
```python
def example():
    return "Hello World"
```

Multiple code examples demonstrating various use cases.
'''
        }
        
        result = await checker.check(artifact)
        
        assert result.overall_score >= 0.8
        assert result.placeholder_count == 0
        assert len(result.missing_sections) == 0
        assert result.has_code_examples is True
    
    async def test_incomplete_document(self):
        """Test checking an incomplete document."""
        checker = CompletenessChecker()
        
        artifact = {
            'title': 'Incomplete Doc',
            'type': 'guide',
            'content': '''# Incomplete Doc

## Overview
Brief overview.

## Installation
TODO: Add installation steps.
'''
        }
        
        result = await checker.check(artifact)
        
        assert result.overall_score < 0.7
        assert result.placeholder_count > 0
        assert len(result.missing_sections) > 0
        assert 'usage' in result.missing_sections
        assert 'examples' in result.missing_sections
    
    async def test_placeholder_detection(self):
        """Test placeholder pattern detection."""
        checker = CompletenessChecker()
        
        artifact = {
            'title': 'Placeholder Test',
            'type': 'guide',
            'content': '''# Test

## Section 1
TODO: Add content here

## Section 2
TBD - Coming soon

## Section 3
FIXME: This needs to be fixed
'''
        }
        
        result = await checker.check(artifact)
        
        assert result.placeholder_count >= 3
        assert len(result.recommendations) > 0
    
    async def test_broken_links(self):
        """Test broken link detection."""
        checker = CompletenessChecker()
        
        artifact = {
            'title': 'Link Test',
            'type': 'guide',
            'content': '''# Test

[Empty link]()
[TODO link](TODO)
[Valid link](https://example.com)
'''
        }
        
        result = await checker.check(artifact)
        
        assert len(result.broken_links) >= 2
    
    async def test_formatting_issues(self):
        """Test formatting issue detection."""
        checker = CompletenessChecker()
        
        artifact = {
            'title': 'Format Test',
            'type': 'guide',
            'content': '''# Test

```python
def test():
    pass


Code block not closed above

###

Empty header above
'''
        }
        
        result = await checker.check(artifact)
        
        assert len(result.formatting_issues) > 0
    
    async def test_code_example_detection(self):
        """Test code example detection."""
        checker = CompletenessChecker()
        
        # With code
        artifact_with_code = {
            'title': 'Code Test',
            'type': 'guide',
            'content': '```python\nprint("hello")\n```'
        }
        result = await checker.check(artifact_with_code)
        assert result.has_code_examples is True
        
        # Without code
        artifact_no_code = {
            'title': 'No Code Test',
            'type': 'guide',
            'content': 'Just plain text'
        }
        result = await checker.check(artifact_no_code)
        assert result.has_code_examples is False
    
    async def test_word_count_analysis(self):
        """Test word count per section."""
        checker = CompletenessChecker()
        
        artifact = {
            'title': 'Word Count Test',
            'type': 'guide',
            'content': '''# Test

## Section A
This is a short section with few words.

## Section B
This is a much longer section with many more words to demonstrate the word count analysis feature. It contains sufficient content to meet the minimum threshold for section completeness.
'''
        }
        
        result = await checker.check(artifact)
        
        assert len(result.section_word_counts) > 0
        assert len(result.incomplete_sections) > 0  # Section A is too short
    
    async def test_recommendations_generation(self):
        """Test recommendation generation."""
        checker = CompletenessChecker()
        
        artifact = {
            'title': 'Recommendations Test',
            'type': 'guide',
            'content': '''# Test

## Overview
TODO

Short section.
'''
        }
        
        result = await checker.check(artifact)
        
        assert len(result.recommendations) > 0
        # Should recommend replacing placeholders
        assert any('placeholder' in r.lower() for r in result.recommendations)
    
    async def test_to_dict(self):
        """Test result serialization."""
        checker = CompletenessChecker()
        
        artifact = {
            'title': 'Serialization Test',
            'type': 'guide',
            'content': '# Test\n\nContent'
        }
        
        result = await checker.check(artifact)
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert 'overall_score' in result_dict
        assert 'missing_sections' in result_dict
        assert 'recommendations' in result_dict


@pytest.mark.asyncio
class TestSectionTypeValidation:
    """Test section type requirements."""
    
    async def test_architecture_doc_requirements(self):
        """Test architecture document requirements."""
        checker = CompletenessChecker()
        
        # Complete architecture doc
        artifact = {
            'title': 'Architecture',
            'type': 'architecture',
            'content': '''# Architecture

## Overview
System overview with sufficient detail.

## Architecture
Detailed architecture description with components and interactions.

## Components
List of system components with descriptions.
'''
        }
        
        result = await checker.check(artifact)
        assert len(result.missing_sections) == 0
    
    async def test_api_reference_requirements(self):
        """Test API reference document requirements."""
        checker = CompletenessChecker()
        
        # Incomplete API doc (missing examples)
        artifact = {
            'title': 'API Reference',
            'type': 'api_reference',
            'content': '''# API Reference

## API
GET /api/endpoint

## Usage
How to use the API
'''
        }
        
        result = await checker.check(artifact)
        assert 'examples' in result.missing_sections

