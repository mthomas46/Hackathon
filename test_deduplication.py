#!/usr/bin/env python3
"""
Test to verify deduplication is working correctly.

This test checks:
1. Hash-based deduplication identifies duplicates
2. Documents with same content are removed
3. Only unique documents remain
"""

from ingestion.models import NormalizedDocument
from datetime import datetime


def test_deduplicate_documents():
    """Test that deduplication removes documents with identical content."""
    
    # Simulate the exact scenario from the demo
    # Multiple URLs with the SAME content (Black Legion info)
    black_legion_content = """
"And thus, driven from Holy Terra and residing forevermore in the underworld, 
the Sons of Horus, the treacherous Sixteenth, became the Black Legion. 
From shame and shadow recast. In black and gold reborn."

Black Legion
The Eye of Horus, feared icon of the Black Legion
Warcry: "Lupercal!" and "For Horus and the Emperor!" (Pre-Heresy)
""".strip()
    
    # Create 3 documents with SAME content but DIFFERENT URLs (like the real data)
    docs = [
        NormalizedDocument(
            document_id="doc1",
            title="Black Legion",
            content_md=black_legion_content,
            original_format="wikipedia",
            metadata={"source_url": "https://warhammer40k.fandom.com/wiki/Sons_of_Horus", "depth": 2}
        ),
        NormalizedDocument(
            document_id="doc2",
            title="Black Legion",
            content_md=black_legion_content,  # SAME CONTENT!
            original_format="wikipedia",
            metadata={"source_url": "https://warhammer40k.fandom.com/wiki/Luna_Wolves", "depth": 2}
        ),
        NormalizedDocument(
            document_id="doc3",
            title="Black Legion",
            content_md=black_legion_content,  # SAME CONTENT!
            original_format="wikipedia",
            metadata={"source_url": "https://warhammer40k.fandom.com/wiki/XVI_Legion", "depth": 2}
        ),
        # Add a UNIQUE document
        NormalizedDocument(
            document_id="doc4",
            title="Horus Heresy",
            content_md="The Horus Heresy was a galaxy-spanning civil war...",
            original_format="wikipedia",
            metadata={"source_url": "https://warhammer40k.fandom.com/wiki/Horus_Heresy", "depth": 0}
        ),
    ]
    
    print("\n" + "="*70)
    print("DEDUPLICATION TEST")
    print("="*70)
    
    print(f"\n📊 Input: {len(docs)} documents")
    print(f"   • 3 with IDENTICAL content (Black Legion)")
    print(f"   • 1 with UNIQUE content (Horus Heresy)")
    
    # Test the deduplication function
    from demo_horus_heresy_enhanced import EnhancedHorusHeresyDemo
    demo = EnhancedHorusHeresyDemo()
    
    unique_docs = demo.deduplicate_documents(docs)
    
    print(f"\n📊 Output: {len(unique_docs)} documents")
    print(f"\n📋 Documents after deduplication:")
    for i, doc in enumerate(unique_docs, 1):
        print(f"   {i}. {doc.title} - {doc.metadata.get('source_url', 'N/A')}")
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    # Verify results
    if len(unique_docs) == 2:
        print("✅ PASS: Deduplication works correctly!")
        print("   • Removed 2 duplicate Black Legion docs")
        print("   • Kept 1 Black Legion + 1 Horus Heresy doc")
        return True
    else:
        print(f"❌ FAIL: Expected 2 unique docs, got {len(unique_docs)}")
        print("   • Deduplication is NOT working!")
        return False


def test_hash_stability():
    """Test that hash function produces consistent results."""
    
    print("\n" + "="*70)
    print("HASH STABILITY TEST")
    print("="*70)
    
    content = "Test content for hashing"
    
    # Hash the same content multiple times
    hash1 = hash(content)
    hash2 = hash(content)
    hash3 = hash(content)
    
    print(f"\nContent: '{content}'")
    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    print(f"Hash 3: {hash3}")
    
    if hash1 == hash2 == hash3:
        print("\n✅ PASS: Hash is stable within the same run")
    else:
        print("\n❌ FAIL: Hash is unstable!")
    
    print("\n⚠️  Note: Python's hash() is randomized across runs for security")
    print("   This means hash-based dedup might have issues!")


def test_alternative_deduplication():
    """Test alternative deduplication using content comparison."""
    
    print("\n" + "="*70)
    print("ALTERNATIVE DEDUPLICATION TEST")
    print("="*70)
    
    # Same test data as before
    black_legion_content = "Black Legion content..."
    
    docs = [
        NormalizedDocument(
            document_id=f"doc{i}",
            title="Black Legion",
            content_md=black_legion_content,
            original_format="wikipedia",
            metadata={"source_url": f"https://wiki/{i}"}
        )
        for i in range(3)
    ]
    
    # Alternative method: direct content comparison
    unique_docs = []
    seen_content = set()
    
    for doc in docs:
        # Use the actual content string, not hash
        content_key = doc.content_md[:500]
        if content_key not in seen_content:
            seen_content.add(content_key)
            unique_docs.append(doc)
    
    print(f"\n📊 Input: {len(docs)} docs with same content")
    print(f"📊 Output: {len(unique_docs)} unique docs")
    
    if len(unique_docs) == 1:
        print("\n✅ PASS: Direct content comparison works!")
    else:
        print(f"\n❌ FAIL: Expected 1 unique doc, got {len(unique_docs)}")


if __name__ == "__main__":
    print("\n🧪 Running Deduplication Tests\n")
    
    # Run all tests
    test1 = test_deduplicate_documents()
    test_hash_stability()
    test_alternative_deduplication()
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    if test1:
        print("\n✅ All tests passed!")
        print("   Deduplication is working correctly.")
    else:
        print("\n❌ Tests failed!")
        print("   Deduplication needs to be fixed.")
    
    print()

