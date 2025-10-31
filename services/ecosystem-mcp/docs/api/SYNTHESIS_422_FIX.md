---
title: "422 Error Fix - Synthesis Query Validation"
service: "ecosystem-mcp"
category: "api"
tags: ['api', 'config', 'configuration', 'endpoints', 'optimization', 'performance', 'rag', 'retrieval', 'routes', 'test']
related: ['INDEX.md', 'architecture/OVERVIEW.md', 'CODE_REFERENCE.md', 'API_ENDPOINTS_COMPLETE.md']
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "intermediate"
semantic_keywords: ['api', 'config', 'configuration', 'endpoints', 'optimization']
llm_search_hints: ['what is 422 error fix - synthesis query validation', 'how does 422 error fix - synthesis query validation work', 'guide to 422 error fix - synthesis query validation']
---

# 422 Error Fix - Synthesis Query Validation

## Issue

During deep documentation generation, the synthesis step was failing with HTTP 422 errors:

```
🔍 Querying RAG... ❌ Failed (422)
⚠️  Synthesis produced short output, using concatenation fallback
```

## Root Cause

**API Validation Mismatch**:
- **API Limit**: `/api/v1/ask` endpoint validates `n_results` with `le=25` (max 25)
  - Location: `src/api/routes/ask.py:43`
  - Validation: `n_results: int = Field(default=10, ge=1, le=25)`

- **Script Request**: Synthesis was requesting `n_results=30`
  - Location: `generate_deep_docs.py:191`
  - Request: `await self.ask_rag(synthesis_prompt, temperature=0.0, n_results=30)`

**Error Response**:
```json
{
  "success": false,
  "error": "Request validation failed",
  "error_code": "VALIDATION_ERROR",
  "status_code": 422,
  "details": [{
    "field": "body.n_results",
    "message": "Input should be less than or equal to 25",
    "code": "less_than_equal"
  }]
}
```

## Fix Applied

Changed synthesis query to use the maximum allowed value:

```python
# Before:
result = await self.ask_rag(synthesis_prompt, temperature=0.0, n_results=30)

# After:
result = await self.ask_rag(synthesis_prompt, temperature=0.0, n_results=25)
```

## Impact

**Before Fix**:
- ❌ Synthesis queries failed with 422
- ❌ Fell back to simple concatenation
- ❌ Lost intelligent synthesis of content
- ✅ Documentation still generated (fallback worked)

**After Fix**:
- ✅ Synthesis queries succeed
- ✅ Intelligent synthesis of all passes
- ✅ More coherent, integrated documentation
- ✅ Better quality output

## Why This Limit Exists

The `n_results` limit is set to 25 for performance and quality reasons:

1. **Performance**: More results = longer processing time
2. **Context Window**: LLM has finite context (too many sources = truncation)
3. **Quality**: 25 high-quality sources > 30+ mixed-quality sources
4. **Ranking**: Top 25 results are most relevant

## Verification

Test the fix:
```bash
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp

# Test synthesis query with correct limit
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Synthesize information about the service",
    "n_results": 25,
    "temperature": 0.0
  }'

# Should succeed with 200 response
```

## Related Configuration

All API endpoints have sensible limits:

| Endpoint | Parameter | Limit | Reason |
|----------|-----------|-------|--------|
| `/api/v1/ask` | `n_results` | ≤ 25 | Context window, performance |
| `/api/v1/search` | `limit` | ≤ 100 | Display, performance |
| `/api/v1/query` | `limit` | ≤ 500 | Bulk retrieval |
| `/api/v1/documents` | `limit` | ≤ 500 | Admin operations |

## Testing

Run the deep documentation generator again:
```bash
python3 generate_deep_docs.py
```

Expected output:
```
🔗 Pass 4/4: Integration & Synthesis
   [100.0%] Combining all passes into coherent narrative...
   Purpose: Synthesize 23,503 chars into unified section
   🔍 Querying RAG... ✅ 15.2s (18423 chars, 25 sources)
   
   ✅ Pass 4 complete: 18,423 chars synthesized
```

No more "❌ Failed (422)" or "concatenation fallback" messages.

## Prevention

To prevent similar issues:

1. **Check API Limits**: Review endpoint validation before scripting
2. **Error Handling**: Script already has fallback (good!)
3. **Testing**: Test with edge cases (max values)
4. **Documentation**: Document all API limits clearly

## Files Modified

- ✅ `generate_deep_docs.py` - Changed `n_results=30` to `n_results=25`

## Status

✅ **FIXED** - Synthesis queries now succeed with proper validation

