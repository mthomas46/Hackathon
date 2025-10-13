# 🐛 Streamlit Duplicate Key Issue - Debugging & Resolution

**Status**: Enhanced with Debug Mode  
**Date**: October 13, 2025

---

## ✅ What Was Done

### 1. **Diagnostic Test Results**
Ran comprehensive testing on the documents API:
```bash
✅ No duplicate document IDs found
✅ All documents have valid IDs
✅ All Streamlit widget keys would be unique
```

**Conclusion**: The API is returning proper unique IDs. The issue is not with the data.

### 2. **Code Enhancements**

#### **Robust Key Generation**
Added `generate_unique_key()` function that creates keys from:
- Widget prefix
- Loop index (guaranteed unique)
- MD5 hash of document ID (prevents collisions)

```python
def generate_unique_key(doc_id: str, index: int, prefix: str = "doc") -> str:
    doc_hash = hashlib.md5(str(doc_id).encode()).hexdigest()[:8]
    unique_key = f"{prefix}_{index}_{doc_hash}"
    return unique_key
```

#### **Debug Mode**
Added comprehensive debug mode accessible via sidebar:
- Toggle: "🐛 Debug Mode" checkbox in sidebar
- Tracks all widget keys created
- Detects duplicate keys in real-time
- Shows timing and render information
- Displays all generated keys

### 3. **Volume Mounts Activated**
- ✅ Volume mounts are now working
- ✅ Code changes auto-reload
- ✅ No more container rebuilds needed

---

## 🎯 Next Steps for User

### Step 1: Enable Debug Mode

1. Go to: http://localhost:8501/#browse-documents
2. **Look at the LEFT SIDEBAR**
3. Check the box: **"🐛 Debug Mode"**
4. The page will reload with debugging info

### Step 2: Observe Debug Output

With debug mode enabled, you'll see:

**In Sidebar:**
```
### Debug Info
Script run at: 12:34:56.789
Keys created this run: 20
```

**In Browse Documents Tab:**
```
📊 Found 20 documents | Keys will be tracked below
```

**In Each Document Expander:**
```
🔑 Widget key: `content_0_98f55e14` | Doc ID: `2b07e2d0-...` | Index: 0
```

**At Bottom of Page:**
```
### 🔍 Debug Summary
- Total documents: 20
- Unique keys generated: 20
- Duplicate keys: 0

✅ All keys are unique
```

### Step 3: If Error Still Occurs

If you still see the duplicate key error WITH debug mode on:

1. **Check for red error boxes** showing duplicate keys detected
2. **Note the error message** - it will show exactly which key is duplicated
3. **Take a screenshot** of the debug output
4. **Check if the page is rendering multiple times**:
   - Look at "Script run at" timestamp
   - If it shows multiple times in quick succession, something is causing re-renders

### Step 4: Common Causes & Solutions

#### Cause 1: Browser Caching
**Solution:**
```bash
# Hard refresh the browser
- Chrome/Edge: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Firefox: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)
```

#### Cause 2: Streamlit Session State
**Solution:**
```bash
# Clear browser cache and restart dashboard
docker-compose restart dashboard
# Then clear browser cache (Ctrl+Shift+Delete)
```

#### Cause 3: Multiple Tab Renders
**Issue**: Streamlit tabs can cause widgets to render multiple times
**Solution**: Already fixed in code - each widget in each tab has unique keys

#### Cause 4: Old Code Cached in Browser
**Solution:**
```bash
# Verify you're running the latest code
docker exec ecosystem-mcp-dashboard cat /app/pages/documents.py | head -20

# Should show:
# """Document management page with debug mode."""
# import hashlib
# from datetime import datetime
```

---

## 🔍 Testing the Fix

### Quick Test
```bash
# Run the diagnostic script
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp
python3 test_document_keys_debug.py

# Should show:
# ✅ ALL TESTS PASSED - No issues found!
```

### Manual Test
1. Open: http://localhost:8501/#browse-documents
2. Enable Debug Mode (sidebar)
3. Expand several documents
4. Check debug output at bottom
5. Should see: "✅ All keys are unique"

---

## 📊 Debug Mode Features

### Real-Time Key Tracking
```python
# Every widget key is tracked
keys_used = set()

# Duplicate detection
if widget_key in keys_used:
    st.error(f"⚠️ DUPLICATE KEY DETECTED: {widget_key}")
```

### Key Visualization
```
View all generated keys (expandable)
0: content_0_98f55e14
1: content_1_1d46fcb2
2: content_2_6c82601f
...
```

### Timing Information
```
Script run at: 12:34:56.789
Keys created this run: 20
```

---

## 🧪 Automated Tests

### Test File Created
- `test_document_keys_debug.py` - Comprehensive diagnostic test
- Tests for duplicate IDs, empty IDs, and key collisions
- Can be run anytime: `python3 test_document_keys_debug.py`

### Integration Tests
- `tests/integration/test_documents_endpoints.py`
  - `TestDocumentUniqueIds` - 3 tests for ID uniqueness
  - `TestDocumentsIntegration::test_documents_ready_for_streamlit`

```bash
# Run document tests
pytest tests/integration/test_documents_endpoints.py::TestDocumentUniqueIds -v
```

---

## 💡 Why This Should Work

### Before (Original Issue)
```python
key=f"doc_content_{doc_id}"  # ❌ Could have duplicates if IDs are similar
```

### After (Current Fix)
```python
# Uses THREE components for uniqueness:
# 1. Index (guaranteed unique in loop)
# 2. Doc ID hash (prevents collisions)
# 3. Prefix (separates different widget types)
key=f"content_{i}_{md5_hash}"  # ✅ Triple-redundant uniqueness
```

### Additional Safety
- All widgets in all tabs have unique keys
- Job expanders have unique keys
- Input widgets have explicit keys
- Debug mode detects any duplicates immediately

---

## 🎨 Code Quality Improvements

### 1. Explicit Keys Everywhere
```python
# Before: Some widgets had no keys
st.button("Search")

# After: All widgets have unique keys
st.button("Search", key="search_button")
```

### 2. Job Expanders Fixed
```python
# Before: Job expanders had no unique keys
with st.expander(f"Job {job_id}"):

# After: Unique keys using index + hash
job_key = f"job_expander_{idx}_{md5_hash}"
with st.expander(f"Job {job_id}", key=job_key):
```

### 3. Form Widgets
All form widgets already have unique keys by being inside a form context.

---

## 📝 Files Modified

1. **`services/ecosystem-mcp-dashboard/pages/documents.py`**
   - Added debug mode
   - Implemented robust key generation
   - Added comprehensive error tracking
   - Fixed all widget keys

2. **`test_document_keys_debug.py`** (NEW)
   - Diagnostic test script
   - Simulates Streamlit key generation
   - Tests for all common issues

3. **`docker-compose.yml`**
   - Added volume mounts (already done)
   - Dashboard auto-reloads on code changes

---

## 🚀 Action Items

### For User:
1. ✅ Enable Debug Mode in dashboard sidebar
2. ✅ Check debug output
3. ✅ Report back what the debug mode shows
4. ✅ If error persists, note exact error message and which keys are duplicated

### If Issue Persists:
Share the following:
1. Screenshot of debug output from bottom of page
2. Screenshot of error message
3. Output of: `docker logs ecosystem-mcp-dashboard | tail -50`
4. Browser developer console output (F12 → Console tab)

---

## 🎯 Expected Result

With the new code:
- ✅ Debug mode should show "All keys are unique"
- ✅ No duplicate key errors
- ✅ All document expanders work smoothly
- ✅ Content previews load correctly

If you still see an error, the debug mode will tell us EXACTLY which key is duplicated and why.

---

## 📞 Quick Reference

### Check Code Version
```bash
docker exec ecosystem-mcp-dashboard head -5 /app/pages/documents.py
# Should show: """Document management page with debug mode."""
```

### Check Volume Mounts
```bash
docker inspect ecosystem-mcp-dashboard | grep -A 5 "Mounts"
# Should show three bind mounts to pages/, utils/, and app.py
```

### Test Documents API
```bash
curl -s "http://localhost:8000/api/v1/documents?limit=5" | jq '.documents[].id'
# Should show 5 unique UUIDs
```

### Run Diagnostic
```bash
python3 test_document_keys_debug.py
# Should show: ✅ ALL TESTS PASSED
```

---

**Status**: Ready for user testing with comprehensive debug capabilities! 🎉

