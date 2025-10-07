"""
Example: Service Integration with Performance Store and MCP Store

This example demonstrates how services should integrate with the
Performance Store and MCP Store using the HTTP clients.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from common.clients import PerformanceStoreClient, MCPStoreClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Example 1: Orchestrator Integration with Performance Store
# ============================================================================

class ExampleOrchestrator:
    """
    Example showing how the Orchestrator service would integrate
    with Performance Store to record execution metrics.
    """
    
    def __init__(self):
        self.perf_client = PerformanceStoreClient()
    
    async def execute_query(
        self,
        query: str,
        mcp_id: str,
        pattern_name: str,
    ) -> Dict[str, Any]:
        """
        Execute a query and record performance metrics.
        
        This is what the actual Orchestrator would do.
        """
        execution_id = f"exec-{datetime.now().timestamp()}"
        start_time = datetime.now()
        
        try:
            logger.info(f"Executing query: {query}")
            logger.info(f"Using MCP: {mcp_id}, Pattern: {pattern_name}")
            
            # Simulate query execution
            await asyncio.sleep(1.5)  # Simulate 1.5 second execution
            
            # Calculate duration
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Record successful execution
            await self.perf_client.record_execution(
                orchestration_id=execution_id,
                mcp_id=mcp_id,
                pattern_name=pattern_name,
                status="success",
                duration_ms=duration_ms,
                query=query,
                confidence=0.95,
                num_sources=3,
                response_length=150,
                metadata={
                    "execution_context": "example",
                    "timestamp": start_time.isoformat(),
                }
            )
            
            logger.info(f"✅ Execution recorded: {execution_id} ({duration_ms:.0f}ms)")
            
            return {
                "execution_id": execution_id,
                "status": "success",
                "duration_ms": duration_ms,
                "response": "This is the query result",
            }
        
        except Exception as e:
            # Calculate duration even on failure
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Record failed execution
            await self.perf_client.record_execution(
                orchestration_id=execution_id,
                mcp_id=mcp_id,
                pattern_name=pattern_name,
                status="failed",
                duration_ms=duration_ms,
                query=query,
                error_message=str(e),
            )
            
            logger.error(f"❌ Execution failed: {execution_id} - {e}")
            raise
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary from Performance Store."""
        summary = await self.perf_client.get_performance_summary(time_window_hours=24)
        logger.info(f"Performance summary (24h): {summary}")
        return summary
    
    async def check_for_anomalies(self):
        """Check for performance anomalies."""
        anomalies = await self.perf_client.detect_orchestration_anomalies(time_window_days=7)
        
        if anomalies:
            logger.warning(f"⚠️ Detected {len(anomalies)} anomalies!")
            for anomaly in anomalies:
                logger.warning(f"  - {anomaly.get('type')}: {anomaly.get('description')}")
        else:
            logger.info("✅ No anomalies detected")
        
        return anomalies
    
    async def close(self):
        """Close HTTP client."""
        await self.perf_client.close()


# ============================================================================
# Example 2: Training Coordinator Integration with MCP Store
# ============================================================================

class ExampleTrainingCoordinator:
    """
    Example showing how the Training Coordinator would integrate
    with MCP Store to fetch and store training packages.
    """
    
    def __init__(self):
        self.store_client = MCPStoreClient()
    
    async def get_base_package(self, package_name: str) -> Dict[str, Any]:
        """
        Fetch a base MCP package for training.
        
        This is what the Training Coordinator would do before training.
        """
        logger.info(f"Fetching base package: {package_name}")
        
        # Search for package
        results = await self.store_client.search_packages(query=package_name, limit=1)
        
        if not results:
            logger.warning(f"Package '{package_name}' not found")
            return {}
        
        package = results[0]
        logger.info(f"✅ Found package: {package.get('name')} (ID: {package.get('package_id')})")
        
        return package
    
    async def download_package_version(self, package_id: str, version: str) -> bytes:
        """
        Download a specific package version for training.
        """
        logger.info(f"Downloading package {package_id} version {version}")
        
        file_data = await self.store_client.download_version(package_id, version)
        
        if file_data:
            logger.info(f"✅ Downloaded {len(file_data)} bytes")
        else:
            logger.warning("Failed to download package")
        
        return file_data or b""
    
    async def publish_trained_package(
        self,
        package_id: str,
        version: str,
        training_results: bytes,
    ):
        """
        Publish trained package back to MCP Store.
        
        This is what the Training Coordinator would do after training.
        """
        logger.info(f"Publishing trained package: {package_id} v{version}")
        
        try:
            result = await self.store_client.upload_version(
                package_id=package_id,
                version=version,
                file_data=training_results,
                changelog=f"Trained version {version} with enhanced knowledge",
                metadata={
                    "training_date": datetime.now().isoformat(),
                    "training_source": "example_training",
                }
            )
            
            logger.info(f"✅ Published version: {result.get('version_id')}")
            return result
        
        except Exception as e:
            logger.error(f"❌ Failed to publish package: {e}")
            raise
    
    async def get_trending_packages(self):
        """Get trending packages for recommendations."""
        logger.info("Fetching trending packages...")
        
        trending = await self.store_client.get_trending_packages(time_window_days=7, limit=5)
        
        logger.info(f"📈 Trending packages:")
        for pkg in trending:
            logger.info(f"  - {pkg.get('name')}: {pkg.get('download_count', 0)} downloads")
        
        return trending
    
    async def close(self):
        """Close HTTP client."""
        await self.store_client.close()


# ============================================================================
# Example 3: Complete Workflow
# ============================================================================

async def example_complete_workflow():
    """
    Example of a complete workflow using both clients.
    
    This demonstrates:
    1. Training Coordinator fetches base package from MCP Store
    2. Training happens (simulated)
    3. Trained package uploaded back to MCP Store
    4. Orchestrator uses package to execute queries
    5. Performance metrics recorded in Performance Store
    6. Analytics retrieved
    """
    logger.info("=" * 70)
    logger.info("Example: Complete MCP Workflow")
    logger.info("=" * 70)
    
    orchestrator = ExampleOrchestrator()
    training_coordinator = ExampleTrainingCoordinator()
    
    try:
        # Step 1: Get trending packages
        logger.info("\n📊 Step 1: Check trending packages")
        await training_coordinator.get_trending_packages()
        
        # Step 2: Execute queries and record performance
        logger.info("\n🚀 Step 2: Execute queries and record performance")
        for i in range(3):
            await orchestrator.execute_query(
                query=f"Example query {i + 1}",
                mcp_id="example-mcp",
                pattern_name="chain-of-thought",
            )
            await asyncio.sleep(0.5)
        
        # Step 3: Get performance summary
        logger.info("\n📈 Step 3: Get performance summary")
        await orchestrator.get_performance_summary()
        
        # Step 4: Check for anomalies
        logger.info("\n🔍 Step 4: Check for anomalies")
        await orchestrator.check_for_anomalies()
        
        logger.info("\n✅ Workflow complete!")
    
    except Exception as e:
        logger.error(f"❌ Workflow failed: {e}")
    
    finally:
        await orchestrator.close()
        await training_coordinator.close()


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run examples."""
    logger.info("Service Integration Examples")
    logger.info("=" * 70)
    
    # Check service health
    logger.info("\n🏥 Checking service health...")
    
    perf_client = PerformanceStoreClient()
    store_client = MCPStoreClient()
    
    perf_healthy = await perf_client.health_check()
    store_healthy = await store_client.health_check()
    
    await perf_client.close()
    await store_client.close()
    
    logger.info(f"Performance Store: {'✅ Healthy' if perf_healthy else '❌ Unavailable'}")
    logger.info(f"MCP Store: {'✅ Healthy' if store_healthy else '❌ Unavailable'}")
    
    if not perf_healthy or not store_healthy:
        logger.warning("\n⚠️ Services are not running. Start them with:")
        logger.warning("  cd services/mcp-performance-store && docker-compose up -d")
        logger.warning("  cd services/mcp-store && docker-compose up -d")
        return
    
    # Run complete workflow
    logger.info("\n" + "=" * 70)
    await example_complete_workflow()


if __name__ == "__main__":
    asyncio.run(main())

