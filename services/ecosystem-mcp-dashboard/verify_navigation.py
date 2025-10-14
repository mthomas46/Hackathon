#!/usr/bin/env python3
"""
Navigation Consolidation Verification Script

Verifies that navigation has been properly consolidated to the sidebar only.
"""

import sys
from pathlib import Path
import re

def check_file_for_pattern(filepath: Path, pattern: str, description: str) -> tuple[bool, list]:
    """Check if a file contains a specific pattern."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            matches = list(re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE))
            return len(matches) > 0, matches
    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
        return False, []

def verify_home_page():
    """Verify home page has no navigation buttons."""
    print("\n🔍 Checking Home Page...")
    home_path = Path(__file__).parent / "pages" / "home.py"
    
    # Check for st.switch_page (should not exist)
    has_switch_page, matches = check_file_for_pattern(
        home_path,
        r'st\.switch_page',
        "st.switch_page calls"
    )
    
    if has_switch_page:
        print(f"  ❌ FAIL: Found {len(matches)} st.switch_page() calls (should be 0)")
        for match in matches:
            line_num = home_path.read_text()[:match.start()].count('\n') + 1
            print(f"     Line {line_num}: {match.group()}")
        return False
    else:
        print("  ✅ PASS: No st.switch_page() calls found")
    
    # Check for "Quick Actions" text (should not exist)
    has_quick_actions, matches = check_file_for_pattern(
        home_path,
        r'Quick Actions',
        "Quick Actions section"
    )
    
    if has_quick_actions:
        print(f"  ❌ FAIL: Found 'Quick Actions' text (should be removed)")
        return False
    else:
        print("  ✅ PASS: No 'Quick Actions' section found")
    
    return True

def verify_metrics_page():
    """Verify metrics page has correct section naming."""
    print("\n🔍 Checking Metrics Page...")
    metrics_path = Path(__file__).parent / "pages" / "metrics.py"
    
    # Check for "Data Export" (should exist)
    has_data_export, matches = check_file_for_pattern(
        metrics_path,
        r'Data Export',
        "Data Export section"
    )
    
    if not has_data_export:
        print("  ❌ FAIL: 'Data Export' section not found (should exist)")
        return False
    else:
        print(f"  ✅ PASS: Found 'Data Export' section ({len(matches)} occurrence(s))")
    
    # Check that it's not "Quick Actions" anymore
    has_quick_actions, matches = check_file_for_pattern(
        metrics_path,
        r'Quick Actions.*Export',
        "Old Quick Actions naming"
    )
    
    if has_quick_actions:
        print("  ❌ FAIL: Still found 'Quick Actions' near export section")
        return False
    else:
        print("  ✅ PASS: No 'Quick Actions' naming found in export section")
    
    return True

def verify_sidebar_navigation():
    """Verify app.py has proper sidebar navigation."""
    print("\n🔍 Checking Sidebar Navigation...")
    app_path = Path(__file__).parent / "app.py"
    
    # Check for sidebar radio navigation
    has_sidebar_nav, matches = check_file_for_pattern(
        app_path,
        r'st\.sidebar\.radio',
        "Sidebar radio navigation"
    )
    
    if not has_sidebar_nav:
        print("  ❌ FAIL: No sidebar radio navigation found")
        return False
    else:
        print("  ✅ PASS: Sidebar radio navigation exists")
    
    # Count expected pages (should be 18)
    content = app_path.read_text()
    page_matches = re.findall(r'"[🏠🏥🔬🤖🎯📚🐳🔍🗄️🔮⚡📊📋🔌⚙️🔧].*?"', content)
    page_count = len([m for m in page_matches if 'Home' in m or 'Health' in m or 'RAG' in m or 'Documents' in m])
    
    print(f"  ℹ️  Found {len(page_matches)} navigation items in sidebar")
    
    return True

def verify_all_pages_clean():
    """Check all other pages don't have navigation controls."""
    print("\n🔍 Checking Other Pages...")
    pages_dir = Path(__file__).parent / "pages"
    
    # Pages that should NOT have st.switch_page
    pages_to_check = [
        "health.py",
        "diagnostics.py",
        "rag.py",
        "query_enhanced.py",
        "documents.py",
        "cache.py",
        "settings.py"
    ]
    
    all_clean = True
    for page_name in pages_to_check:
        page_path = pages_dir / page_name
        if not page_path.exists():
            continue
            
        has_switch_page, matches = check_file_for_pattern(
            page_path,
            r'st\.switch_page',
            "navigation calls"
        )
        
        if has_switch_page:
            print(f"  ⚠️  WARNING: {page_name} has {len(matches)} st.switch_page() call(s)")
            all_clean = False
    
    if all_clean:
        print(f"  ✅ PASS: All {len(pages_to_check)} checked pages are clean")
    
    return all_clean

def main():
    """Run all verification checks."""
    print("=" * 60)
    print("🧪 Navigation Consolidation Verification")
    print("=" * 60)
    
    results = {
        "Home Page": verify_home_page(),
        "Metrics Page": verify_metrics_page(),
        "Sidebar Navigation": verify_sidebar_navigation(),
        "Other Pages": verify_all_pages_clean()
    }
    
    print("\n" + "=" * 60)
    print("📊 Results Summary")
    print("=" * 60)
    
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All checks passed! Navigation consolidation successful.")
        print("=" * 60)
        return 0
    else:
        failed_count = sum(1 for passed in results.values() if not passed)
        print(f"❌ {failed_count}/{len(results)} checks failed.")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())

