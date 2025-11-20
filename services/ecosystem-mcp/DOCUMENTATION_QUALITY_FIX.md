# Documentation Quality Fix - Citation Formatting

**Date:** November 20, 2025  
**Status:** ✅ **RESOLVED**  
**Original Issues:**
1. Citations showed "Document `1...`" instead of filenames
2. Prevalent "Unknown" values in content
3. Citations didn't reference source document names/IDs

---

## 🎯 Root Cause Analysis

### Issue 1: Citations Showing "Document 1..."

**Problem:** Citations formatted as:
```
1. Document `1...` (relevance: 46%)
2. Document `2...` (relevance: 46%)
```

**Root Cause:**
1. Orchestrator was collecting citations from RAG sources
2. Only extracted: `document_id`, `relevance_score`, `content`
3. Did NOT extract `metadata` or `file_path`
4. Citation formatter looked for `metadata["file_path"]` → not found → showed generic "Document ID"

### Issue 2: "Unknown" References in Content

**Problem:** LLM responses included references like:
```
1. **Unknown** - This might be a configuration file
2. **Unknown** - Another configuration file
```

**Root Cause:** Same as Issue 1 - RAG sources didn't include document metadata, so LLM couldn't identify files.

---

## 🔧 The Fix

### Step 1: Enhanced Citation Manager
**File:** `src/services/adaptive/citation_manager.py`

Added method to join citations with documents table to get file_path:
```python
async def _get_citations_with_document_details(self, artifact_id: UUID):
    # Join DocumentationCitationModel with DocumentModel
    # to get file_path and service_name
    query = select(
        DocumentationCitationModel,
        DocumentModel.file_path,
        DocumentModel.service_name
    ).join(DocumentModel, ...)
```

Enhanced formatting:
```python
filename = os.path.basename(file_path)
line = f"{idx}. **{filename}** (relevance: {relevance_pct}%) [`{doc_id}`]"
line += f"\n   📄 `{file_path}`"
```

### Step 2: Construct Metadata from RAG Sources
**File:** `src/services/documentation/adaptive_orchestrator.py`

**Problem:** RAG sources have individual fields, not a `metadata` dict

**Solution:** Construct metadata when collecting citations:
```python
all_citations.extend([
    {
        "section_name": section["name"],
        "document_id": src.get("document_id", src.get("id")),
        "relevance_score": src.get("relevance_score", 0.0),
        "content": src.get("content", ""),
        # ✅ Construct metadata from individual fields
        "metadata": {
            "file_path": src.get("file_path"),
            "quality_score": src.get("quality_score"),
            "quality_grade": src.get("quality_grade"),
            "recency_days": src.get("recency_days"),
            "updated_at": src.get("updated_at")
        }
    }
    for src in section["sources"]
])
```

### Step 3: Improved Citation Formatting
Enhanced `_format_citations` to properly extract filename:
```python
file_path = metadata.get("file_path", metadata.get("filename", ""))

if file_path and file_path != "Unknown":
    filename = os.path.basename(file_path)
    line = f"{idx}. **{filename}** (relevance: {relevance_pct}%) [`{doc_id}`]"
    line += f"\n   📄 `{file_path}`"
else:
    line = f"{idx}. Document `{doc_id}...` (relevance: {relevance_pct}%)"
```

---

## ✅ Results

### Before (Broken):
```markdown
## Sources & References

### overview

1. Document `1...` (relevance: 46%)
2. Document `2...` (relevance: 46%)
3. Document `3...` (relevance: 46%)
```

### After (Fixed):
```markdown
## Sources & References

### overview

1. **Implicits.scala** (relevance: 46%) [`1`]
   📄 `test/scala/helpers/account/Implicits.scala`
2. **ApplyProspectResult.scala** (relevance: 46%) [`2`]
   📄 `app/models/api/ApplyProspectResult.scala`
3. **SiteConnection.scala** (relevance: 46%) [`3`]
   📄 `app/models/api/search/suppliernetworkindex/SiteConnection.scala`
```

---

## 📊 Test Results

### Test Run: `fd6cb414-c42a-435d-988e-b0ec27725e68`

**Status:** ✅ Completed  
**Total Documents:** 1  
**Word Count:** ~850 words

**Citations:**
- ✅ Filenames visible (Implicits.scala, ApplyProspectResult.scala, etc.)
- ✅ Full file paths included
- ✅ Document IDs for traceability
- ✅ Relevance scores displayed
- ✅ No "Unknown" references

---

## 📈 Impact

### What Was Fixed:
- ✅ Citations show actual filenames instead of "Document 1..."
- ✅ Full file paths included for reference
- ✅ Document IDs visible for traceability
- ✅ "Unknown" references eliminated
- ✅ Professional documentation output

### Benefits:
1. **Better Traceability:** Easy to locate source documents
2. **Improved Readability:** Clear, descriptive citations
3. **Enhanced Trust:** Users can verify information sources
4. **Professional Quality:** Documentation looks polished

---

## 🚀 Commits

| Commit | Description |
|--------|-------------|
| `f82647ba` | Fix citation formatting to show filenames and document IDs |
| `8405f220` | Include metadata in citations and improve formatting |
| `4f8c5613` | Construct metadata dict from RAG source fields |

---

## 🔒 Prevention Measures

### Design Principle:
**Always Pass Through Complete Document Metadata**
- RAG sources include file_path, quality_score, etc.
- Citations must construct metadata dict from these fields
- Formatters should handle missing metadata gracefully

### Code Pattern:
```python
# ✅ Good: Construct metadata from available fields
"metadata": {
    "file_path": src.get("file_path"),
    "quality_score": src.get("quality_score"),
    ...
}

# ❌ Bad: Assume metadata exists
"metadata": src.get("metadata", {})  # Will be empty!
```

---

## 📚 Related Issues

### Remaining Quality Concerns:

1. **Content Lightness** ⚠️
   - Some sections still generic
   - May need more specific prompts
   - Consider increasing `n_results` for broader context

2. **Relevance Scores All Same (46%)** ⚠️
   - All documents showing identical relevance
   - May indicate ranking issue
   - Consider investigating score normalization

3. **Generic Responses** ⚠️
   - LLM provides high-level summaries
   - May need more directive prompts
   - Consider adding examples to templates

---

**Resolution Time:** ~1 hour  
**Difficulty:** Medium (metadata mapping, citation formatting)  
**Status:** ✅ FULLY RESOLVED

Citations now properly show filenames and provide full traceability! 🎉
