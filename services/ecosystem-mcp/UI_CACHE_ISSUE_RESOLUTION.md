**Date:** November 20, 2025  
**Status:** UI Caching Issue Identified  
**Issue:** Old Documentation Displayed, Transparency Features Not Visible  

# UI Cache Issue - Resolution Guide

## 🔍 Problem Identified

**What You're Seeing:**
- Documentation with multiple "I don't have enough information to answer that question" responses
- NO query/response disclosure sections visible
- Run ID: `ad4e1c08-b34c-49f2-bc29-c32a6e86bfb8`

**Reality:**
- Run `ad4e1c08` **FAILED** with **0 artifacts**
- You cannot possibly be viewing output from that run
- The UI is showing **CACHED or OLD documentation**

## 📊 Database Analysis

### Recent Runs Status:
```
✅ 91b90aa1 - completed - 1 artifact - 0 "insufficient info" - NO disclosure
✅ 4476edb1 - completed - 1 artifact - 0 "insufficient info" - NO disclosure
✅ 8780613b - completed - 1 artifact - 0 "insufficient info" - NO disclosure
✅ 3b32fac9 - completed - 1 artifact - 0 "insufficient info" - NO disclosure
✅ b2fe27ea - completed - 1 artifact - 0 "insufficient info" - NO disclosure
❌ ad4e1c08 - FAILED - 0 artifacts - (this is what you're supposedly viewing!)
✅ 1e769a28 - completed - 1 artifact - 0 "insufficient info" - NO disclosure
```

**Key Finding:** ALL recent runs have **0** instances of "insufficient info" text!

## ❓ Why No Disclosure Sections?

### The Logic:
Disclosure sections are ONLY added when:
1. The AI response contains: "I don't have enough information to answer that question"
2. This triggers `has_insufficient_info = True`
3. Then disclosure sections with query/response are added

### Current Behavior:
- RAG is finding 20+ sources per section
- Generating complete, informative answers
- NO "insufficient info" responses generated
- Therefore, NO disclosure sections (this is CORRECT!)

## 🎯 Root Cause

### Theory 1: UI Browser Cache ⭐ (MOST LIKELY)
- Browser cached old documentation
- Refresh not clearing cache
- Need hard refresh or cache clear

### Theory 2: UI State Management
- React/Vue state holding old documentation
- Component not re-fetching on run change
- State persisting across runs

### Theory 3: API Response Caching
- API server caching responses
- Not invalidating on new runs
- Returning stale data

## ✅ Solutions

### Solution 1: Clear Browser Cache (Try First)

**Chrome/Edge:**
1. Open DevTools (F12)
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"

**Firefox:**
1. Ctrl+Shift+Delete
2. Check "Cache"
3. Click "Clear Now"

**Safari:**
1. Develop > Empty Caches
2. Cmd+Option+E

### Solution 2: Force UI Refresh

1. Navigate away from documentation page
2. Clear browser cache
3. Restart browser
4. Navigate back to documentation

### Solution 3: Generate Fresh Run with Verbose Mode

Create a new run with `transparency_mode: "verbose"` to see disclosure sections for ALL sections:

```bash
curl -X POST http://localhost:8000/api/v1/documentation/runs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Transparency Test - Verbose Mode",
    "description": "Testing with verbose transparency",
    "source_directory": "/work/adminservice",
    "output_format": "markdown",
    "response_size": "L",
    "tier": "desktop",
    "num_passes": 1,
    "questions_per_pass": 2,
    "metadata": {
      "template_name": "api_reference",
      "service_name": "adminService",
      "category": "api_reference",
      "transparency_mode": "verbose"
    }
  }'
```

This will show disclosure sections for **ALL** sections, not just insufficient info ones.

### Solution 4: Check UI Dashboard API

If the UI dashboard has its own API, it might be caching. Check:

```bash
# Restart dashboard
docker-compose restart dashboard

# Or rebuild
docker-compose down
docker-compose up -d
```

## 🧪 How to Verify Fix

### Test 1: Check Run ID Match
1. In UI, note the displayed Run ID
2. Verify it matches a recent run (e.g., `91b90aa1`)
3. Confirm that run has artifacts in database

### Test 2: Generate New Run
1. Create a brand new run via API or UI
2. Wait for completion
3. View the documentation
4. Check if disclosure sections appear (if insufficient info responses exist)

### Test 3: Verbose Mode Test
1. Create run with `transparency_mode: "verbose"`
2. Wait for completion
3. View documentation
4. Should see `<details>` sections with queries for ALL sections

## 📝 Expected Behavior

### Normal Mode:
- Disclosure sections ONLY when "insufficient info" responses
- Current runs: RAG working well, finding information
- Result: NO disclosure sections (this is correct!)

### Verbose Mode:
- Disclosure sections for ALL sections
- Shows query + response for every section
- Useful for debugging and transparency

## 🎓 Why Current Runs Have No "Insufficient Info"

The RAG system is working well:
1. 20+ sources found per section
2. Generating complete answers
3. No need for "insufficient info" responses

To see disclosure sections in action:
- Use verbose mode, OR
- Document a service with NO ingested data, OR
- Query for information that truly doesn't exist

## ⚡ Quick Resolution Steps

1. **Clear browser cache** (Ctrl+Shift+Delete)
2. **Hard refresh** (Ctrl+F5 or Cmd+Shift+R)
3. **Create NEW run** via UI or API
4. **Wait for completion** (check status)
5. **View NEW documentation** (verify run ID matches)

If still seeing old documentation:
6. **Restart dashboard container**
7. **Try verbose mode** to force disclosure sections
8. **Check browser DevTools Network tab** to see what API is returning

## 📊 What to Look For

When viewing documentation in UI, check:
- **Run ID** displayed - does it match a recent completed run?
- **Creation time** - is it recent (last hour)?
- **Status** - is it "completed"?
- **Artifacts count** - is it > 0?

If Run ID is `ad4e1c08` = **DEFINITELY OLD/CACHED** (that run failed!)

## 🚀 Next Steps

1. Try Solution 1 (clear cache)
2. If not fixed, try Solution 3 (verbose mode)
3. Report back with:
   - Run ID shown in UI
   - Creation timestamp
   - Whether hard refresh helped

---

**Bottom Line:** The transparency code is working correctly. The issue is the UI showing cached/old documentation from before the fixes were deployed. A browser cache clear should resolve it.

