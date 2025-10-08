#!/usr/bin/env python3
"""
Test deep crawling with accurate link counting.
"""
import asyncio
from ingestion.fandom_ingestor import FandomWikiIngestor
from ingestion.tagging import UniversalTaggingConfig

async def test_crawl():
    print("Testing Fandom crawl with different parameters...\n")
    
    # Test 1: Small crawl (current behavior)
    print("=" * 70)
    print("TEST 1: Small crawl (max_links=10, depth=2)")
    print("=" * 70)
    
    config = UniversalTaggingConfig(
        enable_preprocessing=False,
        user_tags=["test:small-crawl"]
    )
    
    ingestor1 = FandomWikiIngestor(tagging_config=config)
    docs1 = await ingestor1.crawl_and_ingest(
        original_page_url="https://warhammer40k.fandom.com/wiki/Horus_Heresy",
        max_surface_links=10,
        max_depth_distance=2
    )
    
    report1 = ingestor1.generate_crawl_report()
    print(f"\nResults:")
    print(f"  Pages crawled: {len(docs1)}")
    print(f"  Depth distribution: {report1.depth_distribution}")
    print(f"  Link stats: {report1.link_statistics}")
    
    # Test 2: Medium crawl
    print("\n" + "=" * 70)
    print("TEST 2: Medium crawl (max_links=50, depth=2)")
    print("=" * 70)
    
    config2 = UniversalTaggingConfig(
        enable_preprocessing=False,
        user_tags=["test:medium-crawl"]
    )
    
    ingestor2 = FandomWikiIngestor(tagging_config=config2)
    docs2 = await ingestor2.crawl_and_ingest(
        original_page_url="https://warhammer40k.fandom.com/wiki/Horus_Heresy",
        max_surface_links=50,
        max_depth_distance=2
    )
    
    report2 = ingestor2.generate_crawl_report()
    print(f"\nResults:")
    print(f"  Pages crawled: {len(docs2)}")
    print(f"  Depth distribution: {report2.depth_distribution}")
    print(f"  Link stats: {report2.link_statistics}")
    
    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)
    print(f"Small crawl (10 links): {len(docs1)} pages")
    print(f"Medium crawl (50 links): {len(docs2)} pages")
    print(f"Increase: {len(docs2) - len(docs1)} pages ({((len(docs2) / len(docs1)) - 1) * 100:.1f}% more)")

if __name__ == "__main__":
    asyncio.run(test_crawl())
