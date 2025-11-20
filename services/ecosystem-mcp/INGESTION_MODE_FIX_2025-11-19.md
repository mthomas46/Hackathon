**Date:** November 19, 2025  
**Status:** UI Confusion Resolved  
**Issue:** Snapshot Mode Selection Showing Git History  

---

## Problem Summary

A user selected "Snapshot Mode" in the dashboard but the ingestion job (ID: `a6cde656-e894-470b-af99-5057b92089ba`) was still processing complete git history, which should NOT happen in snapshot mode.

## Root Cause Analysis

The dashboard had **two separate mode selectors** that were confusing and not properly connected:

### 1. Non-Functional Selector (Lines 306-356 - Removed)
```python
processing_mode = st.radio(
    "Choose processing mode",
    options=["snapshot", "git_history"],
    ...
)
```

**Problem:**
- This field was sent to the backend as `processing_mode`
- **The backend completely ignored this field** (grep confirmed: `processing_mode` is not used anywhere in backend code)
- Users thought they were selecting snapshot mode here, but it had no effect

### 2. Actual Selector (Line 392 - Enhanced)
```python
mode = st.selectbox(
    "Ingestion Type",
    options=["enriched", "snapshot", "quick", "full", "incremental"],
    ...
)
```

**Problem:**
- This was the ONLY field the backend actually used
- It was labeled as "Ingestion Type" which didn't clearly communicate its importance
- Users likely left it at the default ("enriched") while selecting "snapshot" in the non-functional selector
- The backend behavior for each mode:
  - `snapshot`: No git history (current files only)
  - `enriched`: Current files + light git metadata (no full history)
  - `quick`: **Last 10 commits with FULL git history** ← User's job had this mode
  - `full`: ALL commits with complete git history
  - `incremental`: Only changed files

## The User's Case

- User selected "Snapshot Mode" in the `processing_mode` radio button
- User likely left "Ingestion Type" dropdown at "quick" (or didn't change it)
- Backend received `mode=quick` → processed last 10 commits with full git history
- User saw git history and was confused because they thought they selected snapshot mode

## Solution Implemented

### 1. Removed Non-Functional Selector
- Deleted the `processing_mode` radio button (lines 306-356)
- Removed `processing_mode` from request payload
- Eliminated source of confusion

### 2. Enhanced the Actual Selector
- Changed from simple `st.selectbox` to clearly labeled section: "📋 Ingestion Type"
- Added descriptive `format_func` to show mode impact at a glance:
  ```python
  format_func=lambda x: {
      "snapshot": "📸 Snapshot Mode - Current files only (FASTEST: 5-15 min)",
      "enriched": "✨ Enriched Mode - Current files + git metadata (Fast: 10-20 min)",
      "quick": "⚡ Quick History - Last 10 commits (Slow: 30-60 min)",
      "full": "📚 Full History - All commits (VERY SLOW: 2-4 hours)",
      "incremental": "🔄 Incremental - Only new/changed files"
  }[x]
  ```

- Changed default from `enriched` (index=0) to `snapshot` (index=1) for most common use case
- Added detailed help text explaining each mode's behavior
- Added real-time feedback showing what the selected mode will do:
  - ✅ Success box for `snapshot` (no git history)
  - ℹ️ Info box for `enriched` (light git metadata)
  - ⚠️ Warning box for `quick` (git history - slower)
  - 🚨 Error box for `full` (complete git history - very slow)

### 3. Updated Job Display
- Changed job status display to show clear mode information:
  ```python
  mode_labels = {
      "snapshot": "Snapshot (Current files only)",
      "enriched": "Enriched (Files + git metadata)",
      "quick": "Quick History (Last 10 commits)",
      "full": "Full History (All commits)",
      "incremental": "Incremental (Changed files)"
  }
  ```

## Files Modified

1. **`services/ecosystem-mcp-dashboard/dashboard_views/ingestion_manager.py`**
   - Removed non-functional `processing_mode` selector (lines 306-356)
   - Enhanced `mode` selector with clear labels and real-time feedback (lines 314-478)
   - Removed `processing_mode` from request payload (line 618)
   - Updated job status display with clearer mode labels (lines 1296-1310)

## Verification

After restart, users will now see:

1. **Single, Clear Mode Selector:**
   - "📋 Ingestion Type" heading
   - Dropdown with descriptive labels showing speed/behavior
   - Real-time feedback box showing exactly what will happen
   
2. **No Confusion:**
   - Only one place to select mode
   - Clear indication of whether git history will be processed
   - Default to fastest option (`snapshot`)

3. **Correct Behavior:**
   - Selecting "📸 Snapshot Mode" → sends `mode=snapshot` → backend processes current files only
   - Selecting "⚡ Quick History" → sends `mode=quick` → backend processes last 10 commits (user knows this upfront)

## Backend Reference

The backend (`services/ecosystem-mcp/src/services/ingestion/job_processor.py`) processes modes as follows:

```python
async def _get_commits_for_mode(self, mode: str) -> List[GitCommit]:
    if mode == "snapshot":
        # Snapshot mode: no git history, just current state
        return []  # Empty list signals to use current filesystem state
    
    elif mode == "enriched":
        # Enriched: current files with light git metadata
        return []  # Similar to snapshot but with metadata enrichment
    
    elif mode == "quick":
        # Last 10 commits (or max limit)
        limit = min(10, self.max_commits_to_process)
        return await self.git_service.get_recent_commits(limit=limit)
    
    elif mode == "full":
        # All commits
        return await self.git_service.get_recent_commits()
```

## User Communication

**For users who see this issue:**

"The dashboard had two mode selectors and the wrong one was being sent to the backend. We've fixed this by removing the non-functional selector and making the actual selector much clearer about what each mode does. If you want true snapshot mode (no git history), make sure to select '📸 Snapshot Mode - Current files only (FASTEST: 5-15 min)' from the dropdown."

## Prevention

- All UI controls should have corresponding backend logic
- Mode selectors should have clear, descriptive labels that explain behavior
- Real-time feedback should show users what will happen before they commit
- Default selections should favor the most common/fastest use case

---

**Resolution:** ✅ Fixed - Dashboard UI now has single, clear mode selector with accurate backend behavior mapping.

