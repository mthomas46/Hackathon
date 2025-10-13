#!/usr/bin/env python3
"""
Debug script to test document IDs and expose duplicate key issues.

This script fetches documents from the API and checks for:
1. Duplicate document IDs
2. Empty/None IDs
3. Simulates Streamlit key generation
"""

import httpx
import hashlib
from collections import Counter


def generate_streamlit_key(doc_id: str, index: int, prefix: str = "doc") -> str:
    """
    Simulate Streamlit key generation (matching dashboard code).
    """
    doc_hash = hashlib.md5(str(doc_id).encode()).hexdigest()[:8]
    unique_key = f"{prefix}_{index}_{doc_hash}"
    return unique_key


def test_documents_for_duplicate_keys(api_url: str = "http://localhost:8000", limit: int = 20):
    """Test documents endpoint for potential duplicate key issues."""
    
    print("=" * 80)
    print("DOCUMENT KEY DUPLICATE DETECTION TEST")
    print("=" * 80)
    print()
    
    # Fetch documents
    print(f"🔍 Fetching {limit} documents from {api_url}/api/v1/documents...")
    try:
        response = httpx.get(
            f"{api_url}/api/v1/documents",
            params={"limit": limit, "offset": 0},
            timeout=10.0
        )
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error fetching documents: {e}")
        return False
    
    data = response.json()
    documents = data.get("documents", [])
    
    print(f"✅ Fetched {len(documents)} documents")
    print()
    
    # Test 1: Check for duplicate document IDs
    print("=" * 80)
    print("TEST 1: Checking for duplicate document IDs")
    print("=" * 80)
    
    doc_ids = [doc.get('id') for doc in documents]
    id_counts = Counter(doc_ids)
    duplicates = {id: count for id, count in id_counts.items() if count > 1}
    
    if duplicates:
        print(f"❌ FOUND {len(duplicates)} DUPLICATE DOCUMENT IDs:")
        for doc_id, count in duplicates.items():
            print(f"   - ID '{doc_id}' appears {count} times")
            # Show which documents have this ID
            matching_docs = [i for i, doc in enumerate(documents) if doc.get('id') == doc_id]
            print(f"     Indices: {matching_docs}")
            for idx in matching_docs:
                print(f"       [{idx}] {documents[idx].get('file_path', 'Unknown')}")
        print()
    else:
        print("✅ No duplicate document IDs found")
        print()
    
    # Test 2: Check for None/empty IDs
    print("=" * 80)
    print("TEST 2: Checking for None/empty document IDs")
    print("=" * 80)
    
    none_ids = [i for i, doc_id in enumerate(doc_ids) if not doc_id]
    
    if none_ids:
        print(f"❌ FOUND {len(none_ids)} documents with None/empty IDs:")
        for idx in none_ids:
            print(f"   - Document {idx}: {documents[idx].get('file_path', 'Unknown')}")
        print()
    else:
        print("✅ All documents have valid IDs")
        print()
    
    # Test 3: Simulate Streamlit key generation
    print("=" * 80)
    print("TEST 3: Simulating Streamlit widget key generation")
    print("=" * 80)
    
    streamlit_keys = []
    for i, doc in enumerate(documents):
        doc_id = doc.get('id', f'unknown_{i}')
        widget_key = generate_streamlit_key(doc_id, i, "content")
        streamlit_keys.append(widget_key)
    
    key_counts = Counter(streamlit_keys)
    duplicate_keys = {key: count for key, count in key_counts.items() if count > 1}
    
    if duplicate_keys:
        print(f"❌ FOUND {len(duplicate_keys)} DUPLICATE STREAMLIT KEYS:")
        for key, count in duplicate_keys.items():
            print(f"   - Key '{key}' would be generated {count} times")
            # Show which documents would generate this key
            matching_indices = [i for i, k in enumerate(streamlit_keys) if k == key]
            print(f"     Indices: {matching_indices}")
            for idx in matching_indices:
                doc = documents[idx]
                print(f"       [{idx}] ID: {doc.get('id')} | Path: {doc.get('file_path', 'Unknown')}")
        print()
        print("⚠️  THIS WOULD CAUSE THE STREAMLIT DUPLICATE KEY ERROR!")
        print()
    else:
        print("✅ All Streamlit widget keys would be unique")
        print()
    
    # Test 4: Show sample of keys
    print("=" * 80)
    print("TEST 4: Sample of generated keys (first 10)")
    print("=" * 80)
    
    for i in range(min(10, len(documents))):
        doc = documents[i]
        doc_id = doc.get('id', 'N/A')
        file_path = doc.get('file_path', 'Unknown')[:60]
        widget_key = streamlit_keys[i]
        
        print(f"{i:2d}. {widget_key}")
        print(f"    Doc ID: {doc_id}")
        print(f"    Path:   {file_path}")
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    issues = []
    if duplicates:
        issues.append(f"❌ {len(duplicates)} duplicate document IDs")
    if none_ids:
        issues.append(f"❌ {len(none_ids)} documents with None/empty IDs")
    if duplicate_keys:
        issues.append(f"❌ {len(duplicate_keys)} duplicate Streamlit keys")
    
    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
        print()
        print("🔧 RECOMMENDATIONS:")
        if duplicates:
            print("  - Fix the documents endpoint to ensure unique IDs")
        if none_ids:
            print("  - Ensure all documents have non-empty IDs")
        if duplicate_keys:
            print("  - Modify key generation to include more unique components")
        return False
    else:
        print("✅ ALL TESTS PASSED - No issues found!")
        print()
        print("The Streamlit duplicate key error must be caused by something else:")
        print("  - Multiple renders of the same page")
        print("  - Session state issues")
        print("  - Tab switching causing re-renders")
        print()
        print("Try:")
        print("  1. Enable Debug Mode in the dashboard sidebar")
        print("  2. Check the debug output for duplicate key messages")
        print("  3. Look for multiple script runs in quick succession")
        return True


if __name__ == "__main__":
    import sys
    
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    success = test_documents_for_duplicate_keys(api_url, limit)
    sys.exit(0 if success else 1)

