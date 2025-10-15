#!/usr/bin/env python3
"""
Test Navigation Configuration

Verify that the navigation list is properly configured and
includes all expected pages.
"""

import sys
sys.path.insert(0, '/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-dashboard')

# Read app.py and extract navigation
with open('services/ecosystem-mcp-dashboard/app.py', 'r') as f:
    lines = f.readlines()

# Find the navigation list
nav_items = []
in_radio = False
for i, line in enumerate(lines):
    if 'st.sidebar.radio' in line:
        in_radio = True
        continue
    
    if in_radio:
        if ']' in line and ',' not in line:
            break
        
        # Extract string items
        stripped = line.strip()
        if stripped.startswith('"') and stripped.endswith('",'):
            item = stripped[1:-2]  # Remove quotes and comma
            nav_items.append(item)
        elif stripped.startswith('"') and stripped.endswith('"'):
            item = stripped[1:-1]  # Remove quotes only
            nav_items.append(item)

print("=" * 70)
print("📋 NAVIGATION ITEMS TEST")
print("=" * 70)
print(f"\nTotal items: {len(nav_items)}\n")

for i, item in enumerate(nav_items, 1):
    marker = "✅" if "Manager" in item else "  "
    print(f"{marker} {i:2d}. {item}")

print("\n" + "=" * 70)

# Check for our new page
if "🎯 Embeddings Manager" in nav_items:
    idx = nav_items.index("🎯 Embeddings Manager")
    print(f"✅ SUCCESS: '🎯 Embeddings Manager' found at position {idx + 1}")
else:
    print("❌ ERROR: '🎯 Embeddings Manager' NOT found!")
    
print("=" * 70)

# Print routing check
print("\n📍 ROUTING CHECK")
print("=" * 70)

with open('services/ecosystem-mcp-dashboard/app.py', 'r') as f:
    content = f.read()

if 'elif page == "🎯 Embeddings Manager":' in content:
    print("✅ Routing entry found: elif page == '🎯 Embeddings Manager':")
else:
    print("❌ Routing entry NOT found!")

if 'from dashboard_views import embeddings_manager' in content:
    print("✅ Import statement found")
else:
    print("❌ Import statement NOT found!")

if 'embeddings_manager.show(api_base_url)' in content:
    print("✅ Show call found")
else:
    print("❌ Show call NOT found!")

print("=" * 70)

