# LLM Prompt Configuration Guide

## Overview

This guide explains how to configure and customize LLM prompts used throughout the LLM Documentation Consistency system. The system now supports centralized, user-editable prompts that can be refined and optimized without code changes.

## Architecture

### Prompt Manager (`services/shared/prompt_manager.py`)
- **Centralized Configuration**: Single source of truth for all prompts
- **Template System**: Supports variable substitution
- **Version Control**: Prompts are tracked in git
- **Validation**: Ensures prompt syntax and completeness
- **Fallback Support**: Graceful degradation if prompts fail to load

### Configuration File (`services/shared/prompts.yaml`)
- **YAML Format**: Human-readable and editable
- **Organized by Category**: Grouped by functionality (summarization, analysis, etc.)
- **Template Variables**: Support for dynamic content insertion
- **Versioned**: Each prompt can have version information

## How to Use

### 1. Basic Prompt Usage

```python
from services.shared.prompt_manager import get_prompt

# Get a pre-configured prompt
prompt = get_prompt("summarization.default", content="Your content here")

# Use with LLM service
response = await llm_service.summarize(text, prompt=prompt)
```

### 2. Customizing Prompts

Edit `services/shared/prompts.yaml`:

```yaml
summarization:
  default: |
    You are an expert technical writer specializing in {domain}.
    Summarize the following content concisely while preserving all important technical details.
    
    Content to summarize:
    {content}
    
    Focus on: {focus_areas}
```

### 3. Adding New Prompts

```yaml
# Add to prompts.yaml
your_category:
  your_prompt_name: |
    Your prompt content here with {variables}
```

### 4. Using in Services

```python
# In your service
from services.shared.prompt_manager import get_prompt

@app.post("/analyze")
async def analyze_content(request: AnalysisRequest):
    prompt = get_prompt("analysis.consistency_check", 
                       content=request.content,
                       domain=request.domain)
    
    # Use prompt with LLM
    result = await llm_service.analyze(content, prompt=prompt)
    return result
```

## Prompt Categories

### Summarization
- `default`: General-purpose summarization
- `security_focused`: Security-focused summarization
- `compliance_focused`: Compliance and regulatory focus

### Analysis
- `consistency_check`: Documentation consistency analysis
- `documentation_quality`: Quality assessment

### Code Analysis
- `endpoint_extraction`: API endpoint discovery
- `security_scan`: Security vulnerability detection

### Content Processing
- `document_classification`: Content categorization
- `priority_scoring`: Importance evaluation

### Workflows
- `issue_analysis`: Issue/ticket analysis
- `pr_review_assistance`: Pull request documentation review

## Best Practices

### 1. Prompt Design
- **Clear Instructions**: Be specific about what you want
- **Role Definition**: Define the AI's role clearly
- **Output Format**: Specify desired output structure
- **Context Provision**: Include relevant context and constraints

### 2. Template Variables
- **Descriptive Names**: Use clear variable names
- **Optional Variables**: Use defaults where possible
- **Validation**: Validate required variables

### 3. Version Control
- **Iterative Improvement**: Version prompts as you refine them
- **Testing**: Test prompt changes before deploying
- **Documentation**: Document prompt changes and reasoning

### 4. Error Handling
- **Graceful Degradation**: Fall back to defaults if prompts fail
- **Logging**: Log prompt usage and performance
- **Monitoring**: Monitor prompt effectiveness

## Example Implementation

### Before (Hardcoded)
```python
prompt = "Summarize the following content focusing on security implications..."
```

### After (Configurable)
```python
# prompts.yaml
summarization:
  security_focused: |
    You are a security expert analyzing technical content.
    Summarize the content with particular attention to:
    - Authentication and authorization mechanisms
    - Data protection and privacy considerations
    - Potential security vulnerabilities or risks
    
    Content to analyze:
    {content}

# Service code
from services.shared.prompt_manager import get_prompt

prompt = get_prompt("summarization.security_focused", content=user_content)
```

## Migration Guide

### 1. Identify Hardcoded Prompts
Search for hardcoded prompts in your services:
```bash
grep -r "prompt.*=" services/
grep -r "You are" services/
grep -r "Summarize" services/
```

### 2. Extract to Configuration
Move prompts to `services/shared/prompts.yaml`:
```yaml
your_service:
  your_prompt: |
    [extracted prompt content]
```

### 3. Update Service Code
Replace hardcoded prompts with prompt manager calls:
```python
# Before
prompt = "Hardcoded prompt text"

# After
from services.shared.prompt_manager import get_prompt
prompt = get_prompt("your_service.your_prompt", **variables)
```

### 4. Add Error Handling
Always include fallback handling:
```python
try:
    prompt = get_prompt("your_service.your_prompt", **variables)
except Exception:
    prompt = "Fallback prompt text"
```

## Advanced Features

### 1. Prompt Templates with Logic
```yaml
analysis:
  smart_analysis: |
    You are a {role} analyzing {content_type}.
    {conditional_instructions}
    
    Content: {content}
```

### 2. Environment-Specific Prompts
```python
# Different prompts for different environments
if os.environ.get("ENVIRONMENT") == "production":
    prompt_key = "analysis.production_focused"
else:
    prompt_key = "analysis.development_focused"
```

### 3. A/B Testing Prompts
```python
# Test different prompt versions
import random
if random.random() < 0.5:
    prompt = get_prompt("summarization.version_a")
else:
    prompt = get_prompt("summarization.version_b")
```

## Troubleshooting

### Common Issues
1. **Prompt Not Found**: Check prompt key spelling and category
2. **Missing Variables**: Ensure all template variables are provided
3. **YAML Syntax**: Validate YAML syntax with a linter
4. **Import Errors**: Check that prompt_manager is properly installed

### Validation
```python
# Validate all prompts
from services.shared.prompt_manager import get_prompt_manager
pm = get_prompt_manager()
errors = pm.validate_prompts()
if errors:
    print("Prompt validation errors:", errors)
```

## Future Enhancements

1. **Prompt Performance Tracking**: Monitor which prompts perform best
2. **Dynamic Prompt Generation**: AI-generated prompt optimization
3. **Prompt Versioning**: Track prompt evolution over time
4. **Multi-language Support**: Localized prompts for different regions
5. **Prompt Marketplace**: Community-contributed prompt templates

This system provides a robust foundation for managing LLM prompts while maintaining flexibility for customization and improvement.
