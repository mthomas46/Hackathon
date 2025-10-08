#!/usr/bin/env python3
"""
Test ingestion-time deduplication.

Verifies that duplicates are removed BEFORE training the MCP,
solving the problem at the root.
"""

from ingestion.models import NormalizedDocument
from datetime import datetime


def test_ingestion_deduplication():
    """Test that ingestion prevents duplicates at the source."""
    
    print("\n" + "="*70)
    print("INGESTION-TIME DEDUPLICATION TEST")
    print("="*70)
    
    # Create test documents with duplicates
    black_legion_content = """
Black Legion - The treacherous Sixteenth Legion.
Founded from the Sons of Horus and Luna Wolves.
Led by Abaddon the Despoiler.
""".strip()
    
    # Simulate crawled documents with duplicates
    crawled_docs = [
        # Duplicate set 1: Black Legion (3 identical docs)
        NormalizedDocument(
            document_id="sons-of-horus",
            title="Black Legion",
            content_md=black_legion_content,
            original_format="wikipedia",
            metadata={"url": "wiki/Sons_of_Horus"}
        ),
        NormalizedDocument(
            document_id="luna-wolves",
            title="Black Legion",
            content_md=black_legion_content,  # SAME CONTENT
            original_format="wikipedia",
            metadata={"url": "wiki/Luna_Wolves"}
        ),
        NormalizedDocument(
            document_id="xvi-legion",
            title="Black Legion",
            content_md=black_legion_content,  # SAME CONTENT
            original_format="wikipedia",
            metadata={"url": "wiki/XVI_Legion"}
        ),
        # Unique doc
        NormalizedDocument(
            document_id="horus-heresy",
            title="Horus Heresy",
            content_md="The Horus Heresy was a galaxy-spanning civil war...",
            original_format="wikipedia",
            metadata={"url": "wiki/Horus_Heresy"}
        ),
        # Duplicate document ID (should be caught by second protection)
        NormalizedDocument(
            document_id="horus-heresy",  # SAME ID as above!
            title="Horus Heresy",
            content_md="The Horus Heresy was a galaxy-spanning civil war...",
            original_format="wikipedia",
            metadata={"url": "wiki/Horus_Heresy_Duplicate"}
        ),
    ]
    
    print(f"\n📊 Input: {len(crawled_docs)} crawled documents")
    print(f"   • 3 with identical content (Black Legion)")
    print(f"   • 2 with same document_id (horus-heresy)")
    print(f"   • Expected duplicates: 3")
    
    # Test deduplication
    from demo_horus_heresy_enhanced import EnhancedHorusHeresyDemo
    demo = EnhancedHorusHeresyDemo()
    
    # Simulate what happens during ingestion
    unique_docs = demo.deduplicate_documents(crawled_docs)
    
    print(f"\n📊 After deduplication: {len(unique_docs)} documents")
    print(f"\n📋 Unique documents:")
    for i, doc in enumerate(unique_docs, 1):
        print(f"   {i}. {doc.document_id:30s} - {doc.title}")
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    # Verify results
    expected_unique = 2  # 1 Black Legion + 1 Horus Heresy
    
    if len(unique_docs) == expected_unique:
        print(f"✅ PASS: Deduplication works perfectly!")
        print(f"   • Input: {len(crawled_docs)} docs")
        print(f"   • Output: {len(unique_docs)} docs")
        print(f"   • Removed: {len(crawled_docs) - len(unique_docs)} duplicates")
        print(f"   • Duplicate prevention: {((len(crawled_docs) - len(unique_docs)) / len(crawled_docs) * 100):.1f}%")
        return True
    else:
        print(f"❌ FAIL: Expected {expected_unique} unique docs, got {len(unique_docs)}")
        return False


def test_batch_processing_protection():
    """Test that duplicate document IDs are prevented in batch processing."""
    
    print("\n" + "="*70)
    print("BATCH PROCESSING PROTECTION TEST")
    print("="*70)
    
    # Simulate a scenario where the same document appears in different batches
    # (e.g., due to parallel crawling or retry logic)
    
    batch1 = [
        NormalizedDocument(
            document_id="ultramarines",
            title="Ultramarines",
            content_md="The Ultramarines are a Space Marine Chapter...",
            original_format="wikipedia",
            metadata={"batch": 1}
        ),
        NormalizedDocument(
            document_id="dark-angels",
            title="Dark Angels",
            content_md="The Dark Angels are the First Legion...",
            original_format="wikipedia",
            metadata={"batch": 1}
        ),
    ]
    
    batch2 = [
        NormalizedDocument(
            document_id="ultramarines",  # DUPLICATE from batch1!
            title="Ultramarines",
            content_md="The Ultramarines are a Space Marine Chapter...",
            original_format="wikipedia",
            metadata={"batch": 2}
        ),
        NormalizedDocument(
            document_id="blood-angels",
            title="Blood Angels",
            content_md="The Blood Angels are the Ninth Legion...",
            original_format="wikipedia",
            metadata={"batch": 2}
        ),
    ]
    
    all_batches = batch1 + batch2
    
    print(f"\n📊 Input: {len(all_batches)} documents across 2 batches")
    print(f"   • Batch 1: {len(batch1)} docs")
    print(f"   • Batch 2: {len(batch2)} docs")
    print(f"   • Expected duplicate: 'ultramarines' (appears in both batches)")
    
    # Test deduplication across batches
    from demo_horus_heresy_enhanced import EnhancedHorusHeresyDemo
    demo = EnhancedHorusHeresyDemo()
    
    unique_docs = demo.deduplicate_documents(all_batches)
    
    print(f"\n📊 After cross-batch deduplication: {len(unique_docs)} documents")
    print(f"\n📋 Unique documents:")
    for i, doc in enumerate(unique_docs, 1):
        batch_num = doc.metadata.get('batch', 'N/A')
        print(f"   {i}. {doc.document_id:20s} (batch {batch_num})")
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    expected_unique = 3  # ultramarines, dark-angels, blood-angels
    
    if len(unique_docs) == expected_unique:
        print(f"✅ PASS: Batch protection works!")
        print(f"   • Prevented duplicate 'ultramarines' from batch 2")
        print(f"   • Only {expected_unique} unique documents ingested")
        return True
    else:
        print(f"❌ FAIL: Expected {expected_unique} unique docs, got {len(unique_docs)}")
        return False


def test_content_vs_id_deduplication():
    """Test that both content hash AND document ID checks work."""
    
    print("\n" + "="*70)
    print("CONTENT vs ID DEDUPLICATION TEST")
    print("="*70)
    
    # Test different scenarios
    docs = [
        # Scenario 1: Different IDs, same content
        NormalizedDocument(
            document_id="doc-1",
            title="Test",
            content_md="This is test content that will be duplicated.",
            original_format="wikipedia",
            metadata={"scenario": "different_id_same_content"}
        ),
        NormalizedDocument(
            document_id="doc-2",
            title="Test",
            content_md="This is test content that will be duplicated.",  # SAME
            original_format="wikipedia",
            metadata={"scenario": "different_id_same_content"}
        ),
        # Scenario 2: Same ID, different content (should be caught by ID check)
        NormalizedDocument(
            document_id="doc-3",
            title="Test A",
            content_md="This is unique content A.",
            original_format="wikipedia",
            metadata={"scenario": "same_id_different_content"}
        ),
        NormalizedDocument(
            document_id="doc-3",  # SAME ID
            title="Test B",
            content_md="This is unique content B.",  # DIFFERENT
            original_format="wikipedia",
            metadata={"scenario": "same_id_different_content"}
        ),
    ]
    
    print(f"\n📊 Input: {len(docs)} documents")
    print(f"   • Scenario 1: Different IDs, same content (2 docs)")
    print(f"   • Scenario 2: Same ID, different content (2 docs)")
    
    from demo_horus_heresy_enhanced import EnhancedHorusHeresyDemo
    demo = EnhancedHorusHeresyDemo()
    
    unique_docs = demo.deduplicate_documents(docs)
    
    print(f"\n📊 After deduplication: {len(unique_docs)} documents")
    print(f"\n📋 Unique documents:")
    for i, doc in enumerate(unique_docs, 1):
        scenario = doc.metadata.get('scenario', 'N/A')
        print(f"   {i}. {doc.document_id:10s} - {doc.title:10s} ({scenario})")
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    expected_unique = 2  # 1 from scenario 1, 1 from scenario 2
    
    if len(unique_docs) == expected_unique:
        print(f"✅ PASS: Both checks work correctly!")
        print(f"   • Content hash check: Caught scenario 1 duplicate")
        print(f"   • Document ID check: Caught scenario 2 duplicate")
        return True
    else:
        print(f"❌ FAIL: Expected {expected_unique} unique docs, got {len(unique_docs)}")
        return False


if __name__ == "__main__":
    print("\n🧪 Testing Ingestion-Time Deduplication\n")
    
    # Run all tests
    test1 = test_ingestion_deduplication()
    test2 = test_batch_processing_protection()
    test3 = test_content_vs_id_deduplication()
    
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    
    tests_passed = sum([test1, test2, test3])
    tests_total = 3
    
    if tests_passed == tests_total:
        print(f"\n✅ ALL TESTS PASSED ({tests_passed}/{tests_total})!")
        print("\n🎯 Ingestion-time deduplication is working perfectly:")
        print("   1. ✅ Removes duplicate content before training")
        print("   2. ✅ Prevents duplicate document IDs across batches")
        print("   3. ✅ Handles both content hash and ID checks")
        print("\n🛡️  This solves duplication at the ROOT!")
    else:
        print(f"\n⚠️  {tests_passed}/{tests_total} tests passed")
        print(f"   {tests_total - tests_passed} test(s) failed")
    
    print()

