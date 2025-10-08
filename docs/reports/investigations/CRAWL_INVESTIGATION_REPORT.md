# Fandom Wiki Crawl Investigation Report

## Issue Reported
User noticed that depth_distribution and number of links seemed inaccurate - only following 10-12 links per page when the Horus Heresy wiki page has many more links embedded in the article.

## Investigation Results

### Actual Link Availability
Testing the Horus Heresy page directly:
- **Total links in content**: 2,674
- **Wiki links**: 2,514  
- **Unique wiki links (after filtering)**: 594

### Current Crawl Behavior
With `max_surface_links=10, depth=2`:
- **Depth 0**: 1 page (original)
- **Depth 1**: 10 pages (limited by parameter)
- **Depth 2**: 62 pages (10 pages × avg 6.2 links each)
- **Total**: 73 pages

### Root Cause
The parameter `max_surface_links` is **MISLEADING**. It doesn't just apply to the "surface" (original page) - it applies to **EVERY page at EVERY depth level**.

Result: The Horus Heresy page has **594 available links**, but we only follow **10 of them** (1.7% of available links).

### Verification Test
Ran comparison crawls:

| Parameter | Pages Crawled | D0 | D1 | D2 | Links Followed |
|-----------|---------------|----|----|----|-----------------| 
| max_links=10 | 73 | 1 | 10 | 62 | 74 |
| max_links=50 | 780 | 1 | 47 | 715 | 887 |
| **Increase** | **+968%** | - | **+370%** | **+1053%** | **+1098%** |

With `max_links=50`, we get:
- **10.7x more pages** crawled
- **4.7x more depth-1 pages** (47 vs 10)
- **11.5x more depth-2 pages** (715 vs 62)

## Findings

### ✅ The Code is Working Correctly
- Link extraction finds 594 links on the Horus Heresy page
- Filtering logic correctly limits to `max_surface_links` per page
- Depth tracking is accurate
- Visited page tracking prevents duplicates

### ⚠️  The Parameter Name is Misleading
- **Current name**: `max_surface_links`
- **Actual behavior**: Limits links followed from **EVERY page at EVERY depth**
- **User expectation**: Limits only the original "surface" page
- **Better name**: `max_links_per_page` or `links_per_page_limit`

### 📊 The Numbers are Accurate
The depth distribution is mathematically correct:
- Depth 0: 1 (original page)
- Depth 1: min(10, 594) = 10 (limited by parameter)
- Depth 2: 10 pages × avg ~6 links each = ~62 pages

With max_links=50:
- Depth 0: 1
- Depth 1: min(50, 594) = 47 (some links already visited)
- Depth 2: 47 pages × avg ~15 links each = 715 pages

## Recommendations

### 1. Improve Logging (IMPLEMENTED)
Changed logging from:
```
[Depth 0] Horus Heresy → 594 links found
```

To:
```
[Depth 0] Horus Heresy → 594 links found, following 50
```

This makes it clear when links are being filtered.

### 2. Update Default Parameters
For deep domain crawls like Horus Heresy:
- **Old default**: `max_surface_links=10` → 73 pages
- **New default**: `max_surface_links=50` → 780 pages  
- **Alternative**: `max_surface_links=100` → 1,500+ pages

### 3. Consider Rename (Future)
Rename `max_surface_links` to `max_links_per_page` in future versions for clarity.

### 4. Document Behavior
Add documentation explaining that the limit applies at every depth level.

## Resolution

### Changes Made:
1. ✅ Enhanced logging to show "X links found, following Y"
2. ✅ Updated demo default from 10 to 50 links per page
3. ✅ Created test script demonstrating the difference
4. ✅ Documented the behavior in this report

### Test Results:
- Small crawl (10 links): 73 pages in ~6s
- Medium crawl (50 links): 780 pages in ~60s
- **968% increase in coverage** with better parameters

## Conclusion

**The crawl depth distribution was ACCURATE**. The issue was the **parameter setting**, not a bug. With `max_surface_links=10`, we correctly limited to 10 links per page at every depth. Increasing to `max_links_per_page=50` provides much better coverage of the wiki while still being manageable.

---

**Date**: October 8, 2025  
**Investigated by**: AI Development Team  
**Status**: ✅ Resolved - Parameter tuning + improved logging
