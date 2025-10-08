#!/usr/bin/env python3
"""
Wikipedia Crawler Demo

Demonstrates Wikipedia crawling with intelligent tagging on multiple topics:
1. Artificial Intelligence
2. Quantum Computing
3. Space Exploration

Features:
- Configurable crawl depth
- Intelligent corpus analysis
- Knowledge graph building
- Tag collection tracking
- Per-topic reports
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


class Colors:
    """Terminal colors."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class WikipediaCrawlerDemo:
    """Wikipedia crawler demonstration."""
    
    def __init__(self):
        # Demo topics
        self.topics = [
            {
                "name": "Artificial Intelligence",
                "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
                "user_tags": ["domain:technology", "category:ai", "type:research"]
            },
            {
                "name": "Quantum Computing",
                "url": "https://en.wikipedia.org/wiki/Quantum_computing",
                "user_tags": ["domain:technology", "category:quantum", "type:research"]
            },
            {
                "name": "Space Exploration",
                "url": "https://en.wikipedia.org/wiki/Space_exploration",
                "user_tags": ["domain:space", "category:exploration", "type:research"]
            }
        ]
        
        # Create run directory
        run_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.run_dir = Path("reports") / f"wikipedia_demo_{run_timestamp}"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # Results
        self.results = []
    
    def print_header(self, text: str):
        """Print section header."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")
    
    def print_info(self, text: str):
        """Print info message."""
        print(f"{Colors.OKBLUE}ℹ️  {text}{Colors.ENDC}")
    
    def print_success(self, text: str):
        """Print success message."""
        print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")
    
    def print_warning(self, text: str):
        """Print warning message."""
        print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")
    
    async def crawl_topic(
        self,
        topic: Dict[str, Any],
        depth: int = 1,
        surface_links: int = 5
    ) -> Dict[str, Any]:
        """
        Crawl a single Wikipedia topic.
        
        Args:
            topic: Topic configuration
            depth: Crawl depth
            surface_links: Links per page
        
        Returns:
            Crawl results
        """
        self.print_header(f"CRAWLING: {topic['name']}")
        
        try:
            # Import ingestion modules
            from ingestion.wikipedia_ingestor import WikipediaIngestor
            from ingestion.tagging import UniversalTaggingConfig
            
            # Configure intelligent tagging
            tagging_config = UniversalTaggingConfig(
                enable_preprocessing=True,
                preprocessing_sample_size=20,
                min_entity_frequency=2,
                enable_relationships=True,
                enable_knowledge_graph=True,
                user_tags=topic['user_tags']
            )
            
            # Create ingestor
            ingestor = WikipediaIngestor(
                tagging_config=tagging_config,
                enable_tagging=True
            )
            
            # Crawl
            self.print_info(f"🕷️  Crawling {topic['url']}...")
            self.print_info(f"   Depth: {depth}, Surface Links: {surface_links}")
            
            import time
            start_time = time.time()
            
            documents = await ingestor.crawl_and_ingest(
                topic['url'],
                max_surface_links=surface_links,
                max_depth_distance=depth
            )
            
            crawl_time = time.time() - start_time
            
            self.print_success(f"Crawled {len(documents)} pages in {crawl_time:.1f}s")
            
            # Get analysis results
            crawl_report = ingestor.generate_crawl_report()
            tag_collection = ingestor.get_tag_collection()
            
            # Display results
            if tag_collection:
                self.print_info(f"   🏷️  {tag_collection.total_count()} unique tags")
                breakdown = tag_collection.breakdown()
                self.print_info(f"   📊 Default: {breakdown['default']}, Contextual: {breakdown['contextual']}, User: {breakdown['user_defined']}")
                
                # Show sample contextual tags
                if tag_collection.contextual_tags:
                    sample_tags = list(tag_collection.contextual_tags)[:8]
                    self.print_info(f"   🎯 Sample tags: {', '.join(sample_tags)}")
            
            # Compile results
            result = {
                'topic': topic['name'],
                'url': topic['url'],
                'documents_crawled': len(documents),
                'crawl_time': crawl_time,
                'tag_collection': tag_collection.to_dict() if tag_collection else {},
                'crawl_report': {
                    'total_pages': crawl_report.total_pages,
                    'duration': crawl_report.duration_seconds,
                    'depth_distribution': crawl_report.depth_distribution,
                    'link_statistics': crawl_report.link_statistics
                }
            }
            
            # Save topic-specific report
            topic_dir = self.run_dir / topic['name'].lower().replace(' ', '_')
            topic_dir.mkdir(exist_ok=True)
            
            report_path = topic_dir / "crawl_report.json"
            report_path.write_text(json.dumps(result, indent=2, default=str))
            
            # Save sample documents
            sample_docs_path = topic_dir / "sample_documents.md"
            with sample_docs_path.open('w') as f:
                f.write(f"# {topic['name']} - Sample Documents\n\n")
                for idx, doc in enumerate(documents[:3], 1):
                    f.write(f"## {idx}. {doc.title}\n\n")
                    f.write(f"**ID**: `{doc.document_id}`\n\n")
                    f.write(f"**Tags**: {', '.join(doc.tags[:10])}\n\n")
                    f.write(f"**Content Preview** ({len(doc.content_md)} chars):\n\n")
                    preview = doc.content_md[:500]
                    f.write(f"{preview}...\n\n")
                    f.write("---\n\n")
            
            self.print_success(f"Reports saved to: {topic_dir}")
            
            return result
        
        except Exception as e:
            self.print_warning(f"Crawl failed: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'topic': topic['name'],
                'url': topic['url'],
                'error': str(e),
                'documents_crawled': 0
            }
    
    async def run_demo(self, depth: int = 1, surface_links: int = 5):
        """
        Run Wikipedia crawler demo on multiple topics.
        
        Args:
            depth: Crawl depth (default 1)
            surface_links: Links per page (default 5)
        """
        self.print_header("WIKIPEDIA CRAWLER DEMONSTRATION")
        
        print(f"{Colors.BOLD}Configuration:{Colors.ENDC}")
        print(f"  • Topics: {len(self.topics)}")
        print(f"  • Crawl Depth: {depth}")
        print(f"  • Surface Links: {surface_links}")
        print(f"  • Run Directory: {self.run_dir}\n")
        
        # Crawl each topic
        for idx, topic in enumerate(self.topics, 1):
            self.print_info(f"Topic {idx}/{len(self.topics)}: {topic['name']}")
            
            result = await self.crawl_topic(
                topic=topic,
                depth=depth,
                surface_links=surface_links
            )
            
            self.results.append(result)
            
            # Brief pause between topics
            if idx < len(self.topics):
                await asyncio.sleep(2)
        
        # Summary
        self.print_header("DEMO COMPLETE - SUMMARY")
        
        total_docs = sum(r.get('documents_crawled', 0) for r in self.results)
        total_time = sum(r.get('crawl_time', 0) for r in self.results)
        
        print(f"{Colors.BOLD}Results:{Colors.ENDC}")
        
        for result in self.results:
            status = "✅" if result.get('documents_crawled', 0) > 0 else "❌"
            docs = result.get('documents_crawled', 0)
            tags = result.get('tag_collection', {}).get('total', 0)
            time_taken = result.get('crawl_time', 0)
            
            print(f"  {status} {result['topic']}: {docs} docs, {tags} tags, {time_taken:.1f}s")
        
        print(f"\n{Colors.BOLD}Totals:{Colors.ENDC}")
        print(f"  • Total Documents: {total_docs}")
        print(f"  • Total Time: {total_time:.1f}s")
        print(f"  • Average Speed: {total_docs/max(total_time, 1):.1f} docs/sec")
        
        # Save combined report
        combined_report_path = self.run_dir / "combined_report.json"
        combined_report_path.write_text(json.dumps({
            'topics': self.topics,
            'configuration': {
                'depth': depth,
                'surface_links': surface_links
            },
            'results': self.results,
            'summary': {
                'total_documents': total_docs,
                'total_time': total_time,
                'success_count': sum(1 for r in self.results if r.get('documents_crawled', 0) > 0),
                'topics_attempted': len(self.topics)
            }
        }, indent=2, default=str))
        
        print(f"\n{Colors.BOLD}Artifacts:{Colors.ENDC}")
        print(f"  📁 Run Directory: {self.run_dir}")
        print(f"  📊 Combined Report: {combined_report_path}")
        
        for result in self.results:
            topic_name = result['topic'].lower().replace(' ', '_')
            print(f"  📄 {result['topic']}: {self.run_dir / topic_name}/")
        
        self.print_success("\n✨ Wikipedia Crawler Demo Complete!")


async def main():
    """Main entry point."""
    import sys
    
    # Parse command line arguments
    depth = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    surface_links = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    demo = WikipediaCrawlerDemo()
    await demo.run_demo(depth=depth, surface_links=surface_links)


if __name__ == "__main__":
    asyncio.run(main())

