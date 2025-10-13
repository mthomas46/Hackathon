#!/usr/bin/env python3
"""
CSV-Based Multi-Pass Query Batch Processor.

Processes multiple queries from a CSV file with progress tracking,
tier hierarchy integration, and comprehensive logging.
"""

import asyncio
import httpx
import csv
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import sys
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'multi_pass_batch_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class QueryConfig:
    """Configuration for a multi-pass query from CSV."""
    query: str
    num_passes: int = 3
    num_secondary_questions: int = 3
    n_results: int = 10
    temperature: float = 0.7
    tier: str = "auto"
    max_retries: int = 2
    metadata: Dict[str, Any] = None


@dataclass
class BatchResult:
    """Result from processing a batch query."""
    query: str
    config: QueryConfig
    success: bool
    result: Dict[str, Any] = None
    error: str = None
    duration_seconds: float = 0.0
    timestamp: str = None


class MultiPassBatchProcessor:
    """Process multiple multi-pass queries from CSV with tier hierarchy."""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        """Initialize batch processor."""
        self.api_url = api_url
        self.results: List[BatchResult] = []
        
    async def process_csv(
        self,
        csv_path: Path,
        output_dir: Path = None,
        tier_preference: str = "auto"
    ) -> List[BatchResult]:
        """
        Process queries from CSV file.
        
        CSV Format:
        query,num_passes,num_secondary_questions,n_results,temperature,tier
        
        Or simplified:
        query
        
        Args:
            csv_path: Path to CSV file
            output_dir: Output directory for results
            tier_preference: Default tier if not specified in CSV
        
        Returns:
            List of batch results
        """
        logger.info(f"=" * 80)
        logger.info(f"MULTI-PASS BATCH PROCESSOR STARTING")
        logger.info(f"=" * 80)
        logger.info(f"CSV File: {csv_path}")
        logger.info(f"API URL: {self.api_url}")
        logger.info(f"Default Tier: {tier_preference}")
        
        if output_dir is None:
            output_dir = csv_path.parent / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output Directory: {output_dir}")
        logger.info(f"=" * 80)
        
        # Read CSV
        queries = self._read_csv(csv_path, tier_preference)
        logger.info(f"\n📋 Loaded {len(queries)} queries from CSV")
        
        # Check tier availability
        await self._check_tier_status()
        
        # Process each query
        for i, query_config in enumerate(queries, 1):
            logger.info(f"\n{'=' * 80}")
            logger.info(f"PROCESSING QUERY {i}/{len(queries)}")
            logger.info(f"{'=' * 80}")
            
            result = await self._process_single_query(i, query_config)
            self.results.append(result)
            
            # Save individual result
            if result.success and result.result:
                result_file = output_dir / f"query_{i:03d}_result.json"
                with open(result_file, 'w') as f:
                    json.dump(result.result, f, indent=2)
                logger.info(f"💾 Saved result to: {result_file}")
        
        # Save summary
        summary_file = output_dir / "batch_summary.json"
        summary = self._create_summary()
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"\n💾 Saved batch summary to: {summary_file}")
        
        # Save CSV summary
        csv_summary_file = output_dir / "batch_summary.csv"
        self._save_csv_summary(csv_summary_file)
        logger.info(f"💾 Saved CSV summary to: {csv_summary_file}")
        
        # Print final summary
        self._print_final_summary()
        
        return self.results
    
    def _read_csv(self, csv_path: Path, default_tier: str) -> List[QueryConfig]:
        """Read queries from CSV file."""
        queries = []
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Required field
                if 'query' not in row or not row['query'].strip():
                    logger.warning(f"Skipping row with no query: {row}")
                    continue
                
                # Parse optional fields with defaults
                config = QueryConfig(
                    query=row['query'].strip(),
                    num_passes=int(row.get('num_passes', 3)),
                    num_secondary_questions=int(row.get('num_secondary_questions', 3)),
                    n_results=int(row.get('n_results', 10)),
                    temperature=float(row.get('temperature', 0.7)),
                    tier=row.get('tier', default_tier),
                    max_retries=int(row.get('max_retries', 2)),
                    metadata=row if len(row) > 6 else None
                )
                queries.append(config)
        
        return queries
    
    async def _check_tier_status(self):
        """Check and log tier availability."""
        logger.info(f"\n🔌 Checking LLM Tier Availability...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/api/v1/query/tier-status",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    tiers = data.get("tiers", {})
                    
                    logger.info(f"\n  Tier Status:")
                    for tier_name, tier_info in tiers.items():
                        status = "✅ AVAILABLE" if tier_info.get("available") else "❌ UNAVAILABLE"
                        model = tier_info.get("model", "Unknown")
                        logger.info(f"    {tier_name.upper():10s}: {status:15s} ({model})")
                    
                    recommendation = data.get("recommendation", "auto")
                    logger.info(f"\n  💡 Recommended Tier: {recommendation.upper()}")
                else:
                    logger.warning(f"  ⚠️  Could not check tier status: HTTP {response.status_code}")
        
        except Exception as e:
            logger.warning(f"  ⚠️  Could not check tier status: {e}")
    
    async def _process_single_query(
        self,
        query_num: int,
        config: QueryConfig
    ) -> BatchResult:
        """Process a single multi-pass query with comprehensive logging."""
        start_time = datetime.now()
        
        logger.info(f"\n📝 Query: {config.query[:100]}...")
        logger.info(f"⚙️  Configuration:")
        logger.info(f"   • Passes: {config.num_passes}")
        logger.info(f"   • Questions per pass: {config.num_secondary_questions}")
        logger.info(f"   • Total questions: {config.num_passes * config.num_secondary_questions}")
        logger.info(f"   • Documents per question: {config.n_results}")
        logger.info(f"   • Temperature: {config.temperature}")
        logger.info(f"   • Tier: {config.tier.upper()}")
        logger.info(f"   • Max Retries: {config.max_retries}")
        
        try:
            logger.info(f"\n🚀 Sending request to API...")
            logger.info(f"⏳ Estimated time: {self._estimate_duration(config)} seconds")
            logger.info(f"   (This is a long-running operation - please wait...)")
            
            async with httpx.AsyncClient() as client:
                # Make request with extended timeout
                response = await client.post(
                    f"{self.api_url}/api/v1/query/enhanced",
                    json={
                        "question": config.query,
                        "mode": "rag",  # Use full RAG mode
                        "tier": config.tier,
                        "n_results": config.n_results,
                        "temperature": config.temperature,
                        "max_retries": config.max_retries
                    },
                    timeout=900.0  # 15 minutes
                )
                
                duration = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    result = response.json()
                    
                    logger.info(f"\n✅ Query Complete!")
                    logger.info(f"⏱️  Duration: {duration:.2f}s")
                    logger.info(f"🎯 Tier Used: {result.get('tier_used', 'unknown').upper()}")
                    logger.info(f"📚 Sources: {len(result.get('sources', []))}")
                    
                    if result.get('tier_used') != result.get('tier_requested'):
                        logger.warning(
                            f"⚠️  Tier fallback occurred: "
                            f"{result.get('tier_requested', 'unknown').upper()} → "
                            f"{result.get('tier_used', 'unknown').upper()}"
                        )
                    
                    return BatchResult(
                        query=config.query,
                        config=config,
                        success=True,
                        result=result,
                        duration_seconds=duration,
                        timestamp=datetime.now().isoformat()
                    )
                
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.error(f"\n❌ Query Failed: {error_msg}")
                    
                    return BatchResult(
                        query=config.query,
                        config=config,
                        success=False,
                        error=error_msg,
                        duration_seconds=duration,
                        timestamp=datetime.now().isoformat()
                    )
        
        except httpx.TimeoutException:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"Query timed out after {duration:.2f}s"
            logger.error(f"\n❌ {error_msg}")
            logger.info(f"   💡 Try reducing num_passes or num_secondary_questions")
            
            return BatchResult(
                query=config.query,
                config=config,
                success=False,
                error=error_msg,
                duration_seconds=duration,
                timestamp=datetime.now().isoformat()
            )
        
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            logger.error(f"\n❌ Error: {error_msg}", exc_info=True)
            
            return BatchResult(
                query=config.query,
                config=config,
                success=False,
                error=error_msg,
                duration_seconds=duration,
                timestamp=datetime.now().isoformat()
            )
    
    def _estimate_duration(self, config: QueryConfig) -> int:
        """Estimate query duration based on configuration."""
        # Rough estimate: 2-3 seconds per question
        total_questions = config.num_passes * config.num_secondary_questions
        return total_questions * 2.5
    
    def _create_summary(self) -> Dict[str, Any]:
        """Create batch processing summary."""
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
        total_duration = sum(r.duration_seconds for r in self.results)
        avg_duration = total_duration / len(self.results) if self.results else 0
        
        return {
            "total_queries": len(self.results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(self.results) if self.results else 0,
            "total_duration_seconds": total_duration,
            "average_duration_seconds": avg_duration,
            "timestamp": datetime.now().isoformat(),
            "results": [
                {
                    "query": r.query[:100],
                    "success": r.success,
                    "duration_seconds": r.duration_seconds,
                    "error": r.error
                }
                for r in self.results
            ]
        }
    
    def _save_csv_summary(self, csv_path: Path):
        """Save batch results to CSV."""
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'query', 'num_passes', 'num_secondary_questions',
                'tier', 'success', 'duration_seconds',
                'sources_count', 'tier_used', 'error'
            ])
            
            for result in self.results:
                writer.writerow([
                    result.query[:100],
                    result.config.num_passes,
                    result.config.num_secondary_questions,
                    result.config.tier,
                    result.success,
                    f"{result.duration_seconds:.2f}",
                    len(result.result.get('sources', [])) if result.result else 0,
                    result.result.get('tier_used', 'N/A') if result.result else 'N/A',
                    result.error or ''
                ])
    
    def _print_final_summary(self):
        """Print final batch processing summary."""
        logger.info(f"\n{'=' * 80}")
        logger.info(f"BATCH PROCESSING COMPLETE")
        logger.info(f"{'=' * 80}")
        
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
        logger.info(f"\n📊 Summary:")
        logger.info(f"   Total Queries: {len(self.results)}")
        logger.info(f"   ✅ Successful: {len(successful)}")
        logger.info(f"   ❌ Failed: {len(failed)}")
        logger.info(f"   Success Rate: {len(successful) / len(self.results) * 100:.1f}%")
        
        total_duration = sum(r.duration_seconds for r in self.results)
        avg_duration = total_duration / len(self.results) if self.results else 0
        logger.info(f"\n⏱️  Timing:")
        logger.info(f"   Total Duration: {total_duration:.2f}s")
        logger.info(f"   Average per Query: {avg_duration:.2f}s")
        
        if failed:
            logger.info(f"\n❌ Failed Queries:")
            for i, result in enumerate(failed, 1):
                logger.info(f"   {i}. {result.query[:60]}...")
                logger.info(f"      Error: {result.error}")
        
        logger.info(f"\n{'=' * 80}")
        logger.info(f"✅ Batch processing complete!")
        logger.info(f"{'=' * 80}\n")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Process multi-pass queries from CSV file"
    )
    parser.add_argument(
        'csv_file',
        type=Path,
        help="Path to CSV file with queries"
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        help="Output directory for results"
    )
    parser.add_argument(
        '--api-url',
        default="http://localhost:8000",
        help="API base URL"
    )
    parser.add_argument(
        '--tier',
        choices=['auto', 'cursor', 'desktop', 'docker'],
        default='auto',
        help="Default LLM tier preference"
    )
    
    args = parser.parse_args()
    
    if not args.csv_file.exists():
        logger.error(f"CSV file not found: {args.csv_file}")
        return
    
    processor = MultiPassBatchProcessor(api_url=args.api_url)
    await processor.process_csv(
        csv_path=args.csv_file,
        output_dir=args.output_dir,
        tier_preference=args.tier
    )


if __name__ == "__main__":
    asyncio.run(main())

