#!/usr/bin/env python3
"""
Test deduplication with REAL crawled data to see why it's not working.
"""

import asyncio
from demo_horus_heresy_enhanced import EnhancedHorusHeresyDemo


async def main():
    """Test with real crawled data."""
    
    print("\n" + "="*70)
    print("TESTING DEDUPLICATION WITH REAL CRAWLED DATA")
    print("="*70)
    
    # Initialize demo
    demo = EnhancedHorusHeresyDemo()
    
    # Run a minimal crawl
    print("\n🕷️  Crawling 20 pages...")
    from ingestion.fandom_ingestor import FandomWikiIngestor
    from ingestion.tagging import UniversalTaggingConfig
    
    tagging_config = UniversalTaggingConfig(
        enable_preprocessing=False,
        enable_hierarchical_topics=False,  # Disable for speed
        user_tags=["test"]
    )
    
    ingestor = FandomWikiIngestor(
        origin_url="https://warhammer40k.fandom.com/wiki/Horus_Heresy",
        tagging_config=tagging_config
    )
    
    report = await ingestor.crawl(max_depth=1, max_surface_links=5)
    demo.documents_ingested = report.documents
    
    print(f"✓ Crawled {len(demo.documents_ingested)} documents")
    
    # Test the exact same code path as the demo
    print("\n" + "="*70)
    print("TESTING DEDUPLICATION ON 'horus heresy' KEYWORD")
    print("="*70)
    
    keywords = ['horus', 'heresy', 'war']
    
    # Simulate the keyword scoring logic
    scored_docs = []
    for doc in demo.documents_ingested:
        content_lower = (doc.title + ' ' + doc.content_md).lower()
        score = sum(content_lower.count(kw) for kw in keywords)
        title_score = sum(kw in doc.title.lower() for kw in keywords) * 5
        score += title_score
        
        if score > 0:
            scored_docs.append((score, doc))
    
    scored_docs.sort(reverse=True, key=lambda x: x[0])
    relevant_docs = [doc for score, doc in scored_docs[:15]]
    
    print(f"\n📊 Relevant docs (top 15 by keyword score): {len(relevant_docs)}")
    
    # Show first 500 chars of each to see duplicates
    print("\n📋 Document content samples:")
    for i, doc in enumerate(relevant_docs[:5], 1):
        content_sample = doc.content_md[:100].replace('\n', ' ')
        print(f"  {i}. {doc.title[:30]:30s} - {content_sample}...")
    
    # NOW apply deduplication
    print("\n" + "="*70)
    print("APPLYING DEDUPLICATION")
    print("="*70)
    
    before_dedup = len(relevant_docs)
    unique_docs = demo.deduplicate_documents(relevant_docs)
    after_dedup = len(unique_docs)
    
    print(f"\n📊 Before: {before_dedup} documents")
    print(f"📊 After:  {after_dedup} documents")
    print(f"📊 Removed: {before_dedup - after_dedup} duplicates")
    
    if before_dedup != after_dedup:
        print(f"\n✅ Deduplication WORKED! Removed {before_dedup - after_dedup} duplicates")
    else:
        print(f"\n❌ Deduplication DID NOT WORK! No duplicates removed")
        print("\n🔍 Analyzing why...")
        
        # Check for duplicate content manually
        content_samples = [doc.content_md[:500] for doc in relevant_docs]
        unique_samples = set(content_samples)
        
        print(f"   • Total docs: {len(content_samples)}")
        print(f"   • Unique content samples: {len(unique_samples)}")
        print(f"   • Expected duplicates: {len(content_samples) - len(unique_samples)}")
        
        if len(unique_samples) < len(content_samples):
            print(f"\n⚠️  DUPLICATES EXIST but dedup didn't catch them!")
            print("   Possible causes:")
            print("   1. Hash function issue")
            print("   2. Content samples aren't identical")
            print("   3. Logic error in deduplicate_documents()")
    
    print("\n" + "="*70)
    print("DETAILED CONTENT COMPARISON")
    print("="*70)
    
    # Compare first few docs in detail
    for i in range(min(3, len(relevant_docs))):
        print(f"\nDoc {i+1}: {relevant_docs[i].title}")
        print(f"  First 200 chars: {relevant_docs[i].content_md[:200]}")
        print(f"  Hash: {hash(relevant_docs[i].content_md[:500])}")


if __name__ == "__main__":
    asyncio.run(main())

