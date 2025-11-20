# Prompt Transparency Feature

**Date:** November 20, 2025  
**Feature:** Include prompts in generated documentation  
**Status:** ✅ **DEPLOYED**  

---

## 🎯 Overview

Each section of generated documentation now includes the prompt that was used to generate it, with special handling for scenarios where the LLM indicates insufficient information.

---

## ✨ Features

### 1. **Collapsible Prompt Display**
Prompts are displayed in collapsible `<details>` tags to keep documentation clean:

```markdown
<details>
<summary>📝 View Prompt Used</summary>

```
[prompt content here]
```

</details>
```

### 2. **Transparency Mode Support**

**Verbose Mode** (`transparency_mode='verbose'`):
- Shows prompts for ALL sections
- Good for debugging and understanding generation

**Normal Mode** (`transparency_mode='normal'` - default):
- Only shows prompts when there's insufficient information
- Keeps docs clean for production use

### 3. **Insufficient Information Detection**

Automatically detects when the LLM response contains:
- "don't have enough information"
- "insufficient information"
- "not enough information"
- "no information available"
- "cannot find"

### 4. **Special Formatting for Insufficient Info**

When insufficient information is detected:
```markdown
---
⚠️ **Note: Limited Information Available**

<details>
<summary>📝 Prompt Used to Generate This Section</summary>

```
[prompt content]
```

</details>

---

[LLM response explaining lack of information]
```

---

## 📝 Example Output

### Normal Mode (Sufficient Information)

```markdown
## Overview

<details>
<summary>📝 View Prompt Used</summary>

```
Provide a comprehensive overview of the adminService API.

Include:
- Primary purpose and use cases
- Base URL and versioning scheme
- Authentication methods supported
- Key features and capabilities

Target audience: API consumers and integration developers.
Style: Professional, clear, and concise.

**Framework-Specific Context:**
- Detected framework: Play Framework (Scala)
- Adapt examples to use Play Framework conventions
```

</details>

The adminService API is a RESTful service that provides comprehensive
management capabilities for the admin platform...
```

### Insufficient Information Mode

```markdown
## Rate Limiting

---
⚠️ **Note: Limited Information Available**

<details>
<summary>📝 Prompt Used to Generate This Section</summary>

```
Describe the rate limiting policies for adminService API.

Include:
- Rate limit values (requests per minute/hour)
- HTTP headers used for rate limit information
- Behavior when limits are exceeded
- Different limits for different authentication tiers

If specific values aren't documented, provide best practices.
```

</details>

---

I don't have enough information to provide specific rate limiting
details for this service. The available documentation doesn't contain
information about:
- Specific rate limit values
- Rate limit headers
- Rate limit policies

Please consult the service's API documentation or contact the
development team for accurate rate limiting information.
```

---

## 🔧 Technical Implementation

### File Modified
`src/services/documentation/adaptive_orchestrator.py` (Lines 324-384)

### Logic Flow

```python
# 1. Generate content with RAG
response = await self.rag_service.ask(question=prompt, ...)

# 2. Check for insufficient information
has_insufficient_info = any(phrase in response["answer"].lower() for phrase in [
    "don't have enough information",
    "insufficient information",
    # ...
])

# 3. Build section content with prompt
section_content_parts = []

if has_insufficient_info:
    # Always show prompt with warning
    section_content_parts.append("---")
    section_content_parts.append("⚠️ **Note: Limited Information Available**")
    section_content_parts.append("")
    section_content_parts.append("<details>")
    section_content_parts.append("<summary>📝 Prompt Used to Generate This Section</summary>")
    section_content_parts.append("")
    section_content_parts.append("```")
    section_content_parts.append(prompt)
    section_content_parts.append("```")
    section_content_parts.append("")
    section_content_parts.append("</details>")
    section_content_parts.append("")
    section_content_parts.append("---")
    section_content_parts.append("")
elif config.get("transparency_mode") == "verbose":
    # Show prompt in verbose mode
    section_content_parts.append("")
    section_content_parts.append("<details>")
    section_content_parts.append("<summary>📝 View Prompt Used</summary>")
    section_content_parts.append("")
    section_content_parts.append("```")
    section_content_parts.append(prompt)
    section_content_parts.append("```")
    section_content_parts.append("")
    section_content_parts.append("</details>")
    section_content_parts.append("")

# 4. Add generated content
section_content_parts.append(response["answer"])

# 5. Combine and render
section_content_with_prompt = "\n".join(section_content_parts)
rendered_content = await self.template_manager.render_section(
    template=template,
    section_name=section["name"],
    content=section_content_with_prompt,
    context={
        "transparency_mode": config.get("transparency_mode", "normal"),
        "has_insufficient_info": has_insufficient_info
    }
)
```

### Enhanced Return Value

```python
return {
    "name": section["name"],
    "content": rendered_content,
    "validation": validation,
    "sources": response.get("sources", []),
    "prompt_execution_id": str(execution_id),
    "prompt_used": prompt,                    # NEW
    "has_insufficient_info": has_insufficient_info  # NEW
}
```

---

## 🎮 Usage

### Enable Verbose Mode (Show All Prompts)

```python
result = await orchestrator.generate_adaptive_documentation(
    service_name="adminservice",
    template_name="api_reference_openapi_style",
    category="api_reference",
    config={
        "include_citations": True,
        "transparency_mode": "verbose"  # ← Shows all prompts
    }
)
```

### Normal Mode (Only Show Insufficient Info Prompts)

```python
result = await orchestrator.generate_adaptive_documentation(
    service_name="adminservice",
    template_name="api_reference_openapi_style",
    category="api_reference",
    config={
        "include_citations": True,
        "transparency_mode": "normal"  # ← Default, cleaner output
    }
)
```

### Via API

```bash
curl -X POST http://localhost:8000/api/v1/documentation/adaptive/generate \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "adminservice",
    "template_name": "api_reference_openapi_style",
    "category": "api_reference",
    "include_citations": true,
    "transparency_mode": "verbose"
  }'
```

---

## 📊 Benefits

### 1. **Transparency**
- Users see exactly what was requested from the AI
- Builds trust in AI-generated content
- Helps understand AI limitations

### 2. **Debugging**
- Easy to identify prompt issues
- Can refine prompts based on results
- Understand why sections are incomplete

### 3. **Reproducibility**
- Users can reuse prompts elsewhere
- Can verify prompt quality
- Can suggest improvements to prompts

### 4. **User Experience**
- Collapsible format doesn't clutter docs
- Prominent warnings for missing info
- Professional, clean formatting
- Easy to expand when needed

---

## ✅ Verification

### Test Results:
```
Testing prompt transparency feature...
======================================================================
Content Length: 21,656 chars
Has <details> tags: True
Has prompt summaries: True
Has insufficient info warnings: False

Sample prompt transparency section:
----------------------------------------------------------------------
<details>
<summary>📝 View Prompt Used</summary>

```
Provide a comprehensive overview of the adminService API.

Include:
- Primary purpose and use cases
- Base URL and versioning scheme
- Authentication methods supported
- Key features and capabilities
...
```

</details>
----------------------------------------------------------------------

✅ Test complete!
```

---

## 📝 Files Changed

| File | Lines Changed | Type |
|------|---------------|------|
| `src/services/documentation/adaptive_orchestrator.py` | 324-344 → 324-384 (60 lines) | Feature addition |

---

## 🚀 Deployment Status

**Status:** ✅ **DEPLOYED AND TESTED**

1. ✅ Code updated in local codebase
2. ✅ File copied to container
3. ✅ Service restarted
4. ✅ Feature tested and verified working
5. ✅ Example output validated

---

## 🎊 Summary

Generated documentation now includes:

- ✅ Prompts for each section (verbose mode)
- ✅ Collapsible format using `<details>` tags
- ✅ Special handling for insufficient information
- ✅ Clear visual separation from content
- ✅ Professional, clean formatting
- ✅ Enhanced section metadata with prompt info

**Impact:** Users can now understand exactly how each section was generated, making the documentation more transparent and trustworthy!

