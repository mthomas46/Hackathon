"""Utility functions for Prompt Store service.

Provides common utilities for data processing, validation, and formatting.
"""

import re
import hashlib
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone


def generate_prompt_hash(content: str, variables: Optional[List[str]] = None) -> str:
    """Generate hash for prompt content to detect duplicates."""
    content_str = content.strip().lower()
    if variables:
        variables_str = ",".join(sorted(variables)).lower()
        content_str += f"|{variables_str}"

    return hashlib.sha256(content_str.encode()).hexdigest()[:16]


def extract_variables_from_template(content: str) -> List[str]:
    """Extract variable names from template content using regex."""
    # Find all {{variable}} patterns
    pattern = r'\{\{([^}]+)\}\}'
    matches = re.findall(pattern, content)
    return list(set(matches))  # Remove duplicates


def validate_template_variables(content: str, declared_variables: List[str]) -> Dict[str, Any]:
    """Validate that template uses only declared variables."""
    used_variables = extract_variables_from_template(content)
    declared_set = set(declared_variables)
    used_set = set(used_variables)

    errors = []
    warnings = []

    # Check for undeclared variables
    undeclared = used_set - declared_set
    if undeclared:
        errors.append(f"Undeclared variables used: {', '.join(undeclared)}")

    # Check for unused declared variables
    unused = declared_set - used_set
    if unused:
        warnings.append(f"Declared variables not used in template: {', '.join(unused)}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "used_variables": used_variables,
        "declared_variables": declared_variables
    }


def calculate_prompt_complexity(content: str, variables: Optional[List[str]] = None) -> float:
    """Calculate complexity score for a prompt (0.0 to 1.0)."""
    score = 0.0

    # Length factor (longer prompts are more complex)
    length = len(content)
    if length > 500:
        score += 0.3
    elif length > 200:
        score += 0.2
    elif length > 100:
        score += 0.1

    # Variable count factor
    var_count = len(variables) if variables else 0
    if var_count > 5:
        score += 0.3
    elif var_count > 3:
        score += 0.2
    elif var_count > 0:
        score += 0.1

    # Template complexity (presence of conditionals, loops, etc.)
    if any(keyword in content.lower() for keyword in ['if', 'then', 'else', 'for', 'while']):
        score += 0.2

    # Code-like content
    if any(keyword in content.lower() for keyword in ['function', 'class', 'def', 'import']):
        score += 0.2

    return min(score, 1.0)


def format_prompt_template(content: str, variables: Dict[str, Any]) -> str:
    """Fill template variables with values."""
    result = content
    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        result = result.replace(placeholder, str(value))
    return result


def sanitize_prompt_content(content: str) -> str:
    """Sanitize prompt content for storage."""
    if not content:
        return ""

    # Remove excessive whitespace
    content = re.sub(r'\s+', ' ', content.strip())

    # Limit length to reasonable size
    max_length = 10000
    if len(content) > max_length:
        content = content[:max_length] + "..."

    return content


def categorize_prompt_tags(tags: List[str]) -> Dict[str, List[str]]:
    """Categorize tags by type (system, domain, quality, etc.)."""
    categories = {
        "system": [],
        "domain": [],
        "quality": [],
        "language": [],
        "other": []
    }

    system_tags = {"draft", "published", "deprecated", "archived", "template", "active"}
    quality_tags = {"high_quality", "needs_review", "experimental", "stable", "production"}
    language_tags = {"english", "spanish", "french", "german", "chinese", "japanese", "python", "javascript", "java", "csharp"}

    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower in system_tags:
            categories["system"].append(tag)
        elif tag_lower in quality_tags:
            categories["quality"].append(tag)
        elif tag_lower in language_tags:
            categories["language"].append(tag)
        elif any(domain in tag_lower for domain in ["ai", "ml", "nlp", "chat", "code", "writing"]):
            categories["domain"].append(tag)
        else:
            categories["other"].append(tag)

    return categories


def calculate_usage_metrics(usage_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate aggregated usage metrics from usage records."""
    if not usage_records:
        return {
            "total_requests": 0,
            "success_rate": 0.0,
            "avg_response_time_ms": 0.0,
            "total_tokens": 0,
            "unique_users": 0
        }

    total_requests = len(usage_records)
    successful_requests = sum(1 for r in usage_records if r.get("success", False))
    success_rate = successful_requests / total_requests if total_requests > 0 else 0

    response_times = [r.get("response_time_ms", 0) for r in usage_records if r.get("response_time_ms")]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0

    total_input_tokens = sum(r.get("input_tokens", 0) for r in usage_records)
    total_output_tokens = sum(r.get("output_tokens", 0) for r in usage_records)

    unique_users = len(set(r.get("user_id") for r in usage_records if r.get("user_id")))

    return {
        "total_requests": total_requests,
        "success_rate": success_rate,
        "avg_response_time_ms": avg_response_time,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tokens": total_input_tokens + total_output_tokens,
        "unique_users": unique_users
    }


def detect_prompt_drift(current_content: str, historical_versions: List[Dict[str, Any]],
                       threshold: float = 0.7) -> Dict[str, Any]:
    """Detect significant changes (drift) in prompt content over time."""
    if not historical_versions:
        return {"drift_detected": False, "drift_score": 0.0, "significant_changes": []}

    # Simple text similarity check (could be enhanced with embeddings)
    current_words = set(current_content.lower().split())
    significant_changes = []

    for version in historical_versions:
        old_content = version.get("content", "")
        old_words = set(old_content.lower().split())

        # Jaccard similarity
        intersection = len(current_words & old_words)
        union = len(current_words | old_words)
        similarity = intersection / union if union > 0 else 0

        if similarity < threshold:
            significant_changes.append({
                "version": version.get("version", 0),
                "similarity": similarity,
                "created_at": version.get("created_at")
            })

    drift_score = 1 - (sum(c["similarity"] for c in significant_changes) / len(significant_changes)) if significant_changes else 0

    return {
        "drift_detected": len(significant_changes) > 0,
        "drift_score": drift_score,
        "significant_changes": significant_changes
    }


def generate_prompt_suggestions(category: str, existing_prompts: List[Dict[str, Any]]) -> List[str]:
    """Generate prompt improvement suggestions based on category and existing prompts."""
    suggestions = []

    if not existing_prompts:
        suggestions.append("Consider adding more specific instructions for better results")
        return suggestions

    # Analyze common patterns
    avg_length = sum(len(p.get("content", "")) for p in existing_prompts) / len(existing_prompts)

    if avg_length < 50:
        suggestions.append("Prompts in this category tend to be short - consider adding more context")

    # Category-specific suggestions
    if category.lower() == "code":
        suggestions.extend([
            "Consider specifying programming language explicitly",
            "Include error handling requirements",
            "Add performance considerations"
        ])
    elif category.lower() == "writing":
        suggestions.extend([
            "Specify target audience and tone",
            "Include length and format requirements",
            "Consider style guidelines"
        ])
    elif category.lower() == "analysis":
        suggestions.extend([
            "Define expected output format",
            "Include evaluation criteria",
            "Specify confidence levels"
        ])

    return suggestions[:5]  # Limit to 5 suggestions
