"""
Unit tests for AccuracyValidator.
"""

import pytest
from src.services.quality.accuracy_validator import (
    AccuracyValidator,
    get_accuracy_validator
)


@pytest.mark.asyncio
class TestAccuracyValidator:
    """Test AccuracyValidator functionality."""
    
    async def test_initialization(self):
        """Test validator initialization."""
        validator = AccuracyValidator()
        assert validator is not None
        assert len(validator.vague_terms) > 0
        assert 'GET' in validator.http_methods
    
    async def test_singleton(self):
        """Test singleton pattern."""
        validator1 = get_accuracy_validator()
        validator2 = get_accuracy_validator()
        assert validator1 is validator2
    
    async def test_valid_python_code(self):
        """Test Python code validation."""
        validator = AccuracyValidator()
        
        artifact = {
            'title': 'Python Test',
            'content': '''# Code Examples

```python
def hello_world():
    print("Hello, World!")
    return True

if __name__ == "__main__":
    hello_world()
```
'''
        }
        
        result = await validator.validate(artifact)
        
        assert result.overall_score >= 0.9
        assert len(result.code_example_issues) == 0
        assert result.validated_examples == 1
        assert result.total_examples == 1
    
    async def test_invalid_python_code(self):
        """Test invalid Python code detection."""
        validator = AccuracyValidator()
        
        artifact = {
            'title': 'Invalid Python',
            'content': '''# Code Examples

```python
def broken_function(:
    print "missing parentheses"
    return
```
'''
        }
        
        result = await validator.validate(artifact)
        
        assert len(result.code_example_issues) > 0
        assert result.overall_score < 0.9
    
    async def test_javascript_validation(self):
        """Test JavaScript code validation."""
        validator = AccuracyValidator()
        
        # Valid JS
        artifact_valid = {
            'title': 'Valid JS',
            'content': '''
```javascript
function test() {
    return {key: "value"};
}
```
'''
        }
        result = await validator.validate(artifact_valid)
        assert len(result.code_example_issues) == 0
        
        # Invalid JS (unbalanced braces)
        artifact_invalid = {
            'title': 'Invalid JS',
            'content': '''
```javascript
function broken() {
    return {key: "value";
}
```
'''
        }
        result = await validator.validate(artifact_invalid)
        assert len(result.code_example_issues) > 0
    
    async def test_json_validation(self):
        """Test JSON validation."""
        validator = AccuracyValidator()
        
        # Valid JSON
        artifact_valid = {
            'title': 'Valid JSON',
            'content': '''
```json
{
    "name": "test",
    "value": 123
}
```
'''
        }
        result = await validator.validate(artifact_valid)
        assert len(result.code_example_issues) == 0
        
        # Invalid JSON
        artifact_invalid = {
            'title': 'Invalid JSON',
            'content': '''
```json
{
    "name": "test"
    "value": 123
}
```
'''
        }
        result = await validator.validate(artifact_invalid)
        assert len(result.code_example_issues) > 0
    
    async def test_empty_code_block(self):
        """Test empty code block detection."""
        validator = AccuracyValidator()
        
        artifact = {
            'title': 'Empty Code',
            'content': '''
```python
```
'''
        }
        
        result = await validator.validate(artifact)
        assert len(result.code_example_issues) > 0
    
    async def test_api_endpoint_validation(self):
        """Test API endpoint validation."""
        validator = AccuracyValidator()
        
        artifact = {
            'title': 'API Documentation',
            'content': '''# API

GET /api/users
POST /api/users
PUT /api/users/:id
DELETE /api/users/:id
'''
        }
        
        # With matching analysis report
        analysis_report = {
            'api_endpoints': [
                'GET /api/users',
                'POST /api/users',
                'DELETE /api/users/:id'
            ]
        }
        
        result = await validator.validate(artifact, analysis_report=analysis_report)
        
        # Should detect undocumented endpoint (PUT) and documented but missing endpoint
        assert len(result.api_mismatches) > 0
    
    async def test_api_endpoint_format_validation(self):
        """Test API endpoint format validation."""
        validator = AccuracyValidator()
        
        artifact = {
            'title': 'Bad API Format',
            'content': '''# API

GET api/users  # Missing leading slash
POST /api/users with spaces
'''
        }
        
        result = await validator.validate(artifact)
        assert len(result.api_mismatches) > 0
    
    async def test_type_consistency(self):
        """Test type consistency checking."""
        validator = AccuracyValidator()
        
        artifact = {
            'title': 'Type Inconsistency',
            'content': '''# Types

The parameter is a string type.
Another parameter is a str value.
Use string for the first one.
Use str for the second.
And string again.
And str once more.
'''
        }
        
        result = await validator.validate(artifact)
        assert len(result.type_errors) > 0
    
    async def test_factual_accuracy_async_sync(self):
        """Test async/sync confusion detection."""
        validator = AccuracyValidator()
        
        artifact = {
            'title': 'Async/Sync',
            'content': '''# Function

This function is synchronous but you can also use async with it.
'''
        }
        
        result = await validator.validate(artifact)
        assert len(result.factual_errors) > 0
    
    async def test_deprecated_without_alternative(self):
        """Test deprecated item detection."""
        validator = AccuracyValidator()
        
        artifact = {
            'title': 'Deprecated',
            'content': 'This method is deprecated.'
        }
        
        result = await validator.validate(artifact)
        assert len(result.factual_errors) > 0
        
        # With alternative
        artifact_with_alt = {
            'title': 'Deprecated with Alt',
            'content': 'This method is deprecated. Use new_method instead.'
        }
        
        result = await validator.validate(artifact_with_alt)
        # Should not flag this as error
        assert len([e for e in result.factual_errors if 'deprecated' in e.lower()]) == 0
    
    async def test_vague_language_detection(self):
        """Test vague language detection."""
        validator = AccuracyValidator()
        
        artifact = {
            'title': 'Vague Language',
            'content': '''# Documentation

This might work in some cases.
It probably will succeed usually.
Maybe you should try this.
'''
        }
        
        result = await validator.validate(artifact)
        assert len(result.warnings) > 0
        assert any('vague' in w.lower() for w in result.warnings)
    
    async def test_multiple_language_validation(self):
        """Test validation of multiple languages."""
        validator = AccuracyValidator()
        
        artifact = {
            'title': 'Multi-Language',
            'content': '''# Examples

```python
def test():
    pass
```

```javascript
function test() {}
```

```json
{"key": "value"}
```

```bash
echo "test"
```
'''
        }
        
        result = await validator.validate(artifact)
        
        assert result.total_examples == 4
        assert result.validated_examples >= 3  # Most should validate
    
    async def test_to_dict(self):
        """Test result serialization."""
        validator = AccuracyValidator()
        
        artifact = {
            'title': 'Serialization Test',
            'content': '# Test\n\n```python\nprint("test")\n```'
        }
        
        result = await validator.validate(artifact)
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert 'overall_score' in result_dict
        assert 'code_example_issues' in result_dict
        assert 'validated_examples' in result_dict
        assert 'total_examples' in result_dict


@pytest.mark.asyncio
class TestValidationRateTracking:
    """Test validation rate calculation."""
    
    async def test_perfect_validation_rate(self):
        """Test 100% validation rate."""
        validator = AccuracyValidator()
        
        artifact = {
            'title': 'Perfect Validation',
            'content': '''
```python
def valid(): pass
```

```json
{"valid": true}
```
'''
        }
        
        result = await validator.validate(artifact)
        
        assert result.validated_examples == result.total_examples
        assert result.total_examples > 0
    
    async def test_partial_validation_rate(self):
        """Test partial validation rate."""
        validator = AccuracyValidator()
        
        artifact = {
            'title': 'Partial Validation',
            'content': '''
```python
def valid(): pass
```

```python
def invalid(:
```
'''
        }
        
        result = await validator.validate(artifact)
        
        assert result.validated_examples < result.total_examples
        assert result.validated_examples > 0

