"""
Phase 3 Functional Demo - Real Code Testing
Tests actual implementation of all Phase 3 components.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add services directory to path to enable proper imports
project_root = Path(__file__).parent
services_path = project_root / "services"
memory_agent_path = project_root / "services" / "memory-agent"
sys.path.insert(0, str(services_path))
sys.path.insert(0, str(memory_agent_path))

# Now import using simple imports (memory-agent directory added to path)
from domain.entities.memory_context import (
    MemoryContext,
    WorkflowResult,
    ArtifactLink,
    WorkflowType
)
from domain.services.context_manager import ContextManager
from domain.services.artifact_linker import ArtifactLinker
from domain.services.context_aggregator import ContextAggregator
from domain.services.context_search import ContextSearch
from infrastructure.integrations.workflow_integration import WorkflowIntegrationHelper


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "=" * 85)
    print(f"  {text}")
    print("=" * 85)


def print_section(text: str):
    """Print formatted section."""
    print(f"\n>>> {text}")
    print("-" * 85)


def print_success(text: str, detail: str = ""):
    """Print success message."""
    if detail:
        print(f"   ✅ {text}: {detail}")
    else:
        print(f"   ✅ {text}")


def print_test(test_name: str, passed: bool, detail: str = ""):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    if detail:
        print(f"   {status}: {test_name} - {detail}")
    else:
        print(f"   {status}: {test_name}")


class Phase3FunctionalTest:
    """Functional test suite for Phase 3."""
    
    def __init__(self):
        """Initialize test components."""
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        
        # Initialize Phase 3 services
        self.context_manager = ContextManager(redis_client=None)
        self.artifact_linker = ArtifactLinker()
        self.context_aggregator = ContextAggregator()
        self.context_search = ContextSearch()
        self.workflow_helper = WorkflowIntegrationHelper(
            self.context_manager,
            self.artifact_linker
        )
    
    def record_test(self, name: str, passed: bool, detail: str = ""):
        """Record test result."""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
        print_test(name, passed, detail)
    
    async def test_context_manager(self):
        """Test ContextManager functionality."""
        print_section("TEST 1: ContextManager - Context Storage & Retrieval")
        
        try:
            # Test: Create context
            result = await self.context_manager.store_workflow_result(
                workflow_id="test_wf_001",
                workflow_type=WorkflowType.WORKFLOW_A,
                result_data={"test": "data"},
                success=True,
                duration_ms=1000.0
            )
            self.record_test(
                "Create workflow result",
                result is not None and result.workflow_id == "test_wf_001",
                f"ID: {result.workflow_id if result else 'None'}"
            )
            
            # Test: Retrieve context
            context = await self.context_manager.get_context("test_wf_001")
            self.record_test(
                "Retrieve context",
                context is not None and context.workflow_id == "test_wf_001",
                f"Found: {context.workflow_id if context else 'None'}"
            )
            
            # Test: Context has correct workflow result
            if context:
                has_result = len(context.workflow_results) > 0
                self.record_test(
                    "Context contains workflow result",
                    has_result,
                    f"Results: {len(context.workflow_results)}"
                )
            
            print_success("ContextManager tests complete", f"{self.tests_passed}/{self.tests_run} passed")
            
        except Exception as e:
            self.record_test("ContextManager", False, f"Error: {str(e)}")
    
    async def test_artifact_linker(self):
        """Test ArtifactLinker functionality."""
        print_section("TEST 2: ArtifactLinker - Multi-Service Artifact Linking")
        
        try:
            # Create a context for testing
            await self.context_manager.store_workflow_result(
                workflow_id="test_wf_artifacts",
                workflow_type=WorkflowType.WORKFLOW_B,
                result_data={"test": "artifacts"},
                success=True,
                duration_ms=1500.0
            )
            context = await self.context_manager.get_context("test_wf_artifacts")
            
            # Test: Link document
            await self.artifact_linker.link_document(
                context=context,
                document_id="doc_test_001",
                validate=False
            )
            self.record_test(
                "Link document",
                len(context.linked_artifacts) > 0,
                f"Artifacts: {len(context.linked_artifacts)}"
            )
            
            # Test: Link prompt
            await self.artifact_linker.link_prompt(
                context=context,
                prompt_id="prompt_test_001",
                validate=False
            )
            self.record_test(
                "Link prompt",
                len(context.linked_artifacts) > 1,
                f"Artifacts: {len(context.linked_artifacts)}"
            )
            
            # Test: Link user
            await self.artifact_linker.link_user(
                context=context,
                user_id="user_test_001",
                validate=False
            )
            self.record_test(
                "Link user",
                len(context.linked_artifacts) > 2,
                f"Artifacts: {len(context.linked_artifacts)}"
            )
            
            # Test: Get all artifacts
            all_artifacts = await self.artifact_linker.get_all_artifacts(context)
            self.record_test(
                "Retrieve all artifacts",
                len(all_artifacts) == 3,
                f"Count: {len(all_artifacts)}"
            )
            
            # Test: Get artifacts by type
            docs = await self.artifact_linker.get_artifacts_by_type(context, "document")
            self.record_test(
                "Filter by artifact type",
                len(docs) == 1,
                f"Documents: {len(docs)}"
            )
            
            print_success("ArtifactLinker tests complete", f"{self.tests_passed}/{self.tests_run} passed")
            
        except Exception as e:
            self.record_test("ArtifactLinker", False, f"Error: {str(e)}")
    
    async def test_workflow_integration(self):
        """Test WorkflowIntegrationHelper functionality."""
        print_section("TEST 3: WorkflowIntegrationHelper - Workflow Coordination")
        
        try:
            # Test: Store Workflow A result
            result_a = await self.workflow_helper.store_workflow_a_result(
                workflow_id="wf_a_integration_test",
                feature_breakdown={"user_stories": 10, "tasks": 25},
                prompts_used=["prompt_001", "prompt_002"],
                documents_generated=["doc_001"],
                duration_ms=2500.0,
                parent_workflow_id="parent_integration_test"
            )
            self.record_test(
                "Store Workflow A result",
                result_a is not None and result_a.workflow_type == WorkflowType.WORKFLOW_A,
                f"Type: {result_a.workflow_type.value if result_a else 'None'}"
            )
            
            # Test: Store Workflow B result
            result_b = await self.workflow_helper.store_workflow_b_result(
                workflow_id="wf_b_integration_test",
                historical_context={"sources": 20},
                documents_retrieved=["doc_hist_001", "doc_hist_002"],
                jira_tickets=["JIRA-123"],
                confluence_pages=["PAGE-456"],
                duration_ms=3000.0,
                parent_workflow_id="parent_integration_test"
            )
            self.record_test(
                "Store Workflow B result",
                result_b is not None and result_b.workflow_type == WorkflowType.WORKFLOW_B,
                f"Type: {result_b.workflow_type.value if result_b else 'None'}"
            )
            
            # Test: Store orchestration result
            result_orch = await self.workflow_helper.store_orchestration_result(
                workflow_id="parent_integration_test",
                orchestration_data={"query": "test query"},
                child_workflow_ids=["wf_a_integration_test", "wf_b_integration_test"],
                duration_ms=5000.0
            )
            self.record_test(
                "Store orchestration result",
                result_orch is not None and result_orch.workflow_type == WorkflowType.ORCHESTRATION,
                f"Children: {len(['wf_a_integration_test', 'wf_b_integration_test'])}"
            )
            
            # Test: Retrieve workflow context
            context_a = await self.workflow_helper.get_workflow_context("wf_a_integration_test")
            self.record_test(
                "Retrieve workflow context",
                context_a is not None and context_a.workflow_id == "wf_a_integration_test",
                f"Artifacts: {len(context_a.linked_artifacts) if context_a else 0}"
            )
            
            print_success("WorkflowIntegrationHelper tests complete", f"{self.tests_passed}/{self.tests_run} passed")
            
        except Exception as e:
            self.record_test("WorkflowIntegrationHelper", False, f"Error: {str(e)}")
    
    async def test_context_aggregator(self):
        """Test ContextAggregator functionality."""
        print_section("TEST 4: ContextAggregator - Result Synthesis")
        
        try:
            # Create multiple contexts for aggregation
            contexts = []
            for i in range(3):
                await self.context_manager.store_workflow_result(
                    workflow_id=f"wf_agg_{i}",
                    workflow_type=WorkflowType.WORKFLOW_A,
                    result_data={"iteration": i},
                    success=True,
                    duration_ms=1000.0 + (i * 500)
                )
                ctx = await self.context_manager.get_context(f"wf_agg_{i}")
                if ctx:
                    contexts.append(ctx)
            
            self.record_test(
                "Create contexts for aggregation",
                len(contexts) == 3,
                f"Created: {len(contexts)}"
            )
            
            # Test: Aggregate parallel workflows
            aggregated = await self.context_aggregator.aggregate_parallel_workflows(contexts)
            self.record_test(
                "Aggregate parallel workflows",
                aggregated is not None and aggregated.get("total_workflows") == 3,
                f"Total: {aggregated.get('total_workflows') if aggregated else 0}"
            )
            
            # Test: Create unified view
            if contexts:
                all_results = []
                for ctx in contexts:
                    all_results.extend(ctx.workflow_results.values())
                unified = await self.context_aggregator.create_unified_view(all_results)
                self.record_test(
                    "Create unified view",
                    unified is not None and "total_results" in unified and unified["total_results"] == 3,
                    f"Results: {unified.get('total_results') if unified else 0}"
                )
            
            # Test: Extract insights
            if aggregated:
                insights = await self.context_aggregator.extract_key_insights(aggregated)
                self.record_test(
                    "Extract insights",
                    insights is not None and len(insights) > 0,
                    f"Insights: {len(insights) if insights else 0}"
                )
            
            print_success("ContextAggregator tests complete", f"{self.tests_passed}/{self.tests_run} passed")
            
        except Exception as e:
            self.record_test("ContextAggregator", False, f"Error: {str(e)}")
    
    async def test_context_search(self):
        """Test ContextSearch functionality."""
        print_section("TEST 5: ContextSearch - Smart Search & Filtering")
        
        try:
            # Create contexts for search testing
            search_contexts = []
            for i in range(5):
                await self.context_manager.store_workflow_result(
                    workflow_id=f"wf_search_{i}",
                    workflow_type=WorkflowType.WORKFLOW_A if i % 2 == 0 else WorkflowType.WORKFLOW_B,
                    result_data={"index": i},
                    success=True,
                    duration_ms=1000.0
                )
                ctx = await self.context_manager.get_context(f"wf_search_{i}")
                if ctx:
                    search_contexts.append(ctx)
            
            self.record_test(
                "Create contexts for search",
                len(search_contexts) == 5,
                f"Created: {len(search_contexts)}"
            )
            
            # Test: Search by workflow type
            workflow_a_results = await self.context_search.search_by_workflow_type(
                search_contexts,
                WorkflowType.WORKFLOW_A,
                limit=10
            )
            self.record_test(
                "Search by workflow type",
                len(workflow_a_results) == 3,  # 0, 2, 4 are WORKFLOW_A
                f"Found: {len(workflow_a_results)}"
            )
            
            # Test: Search recent
            recent = await self.context_search.search_recent(
                search_contexts,
                hours=24,
                limit=10
            )
            self.record_test(
                "Search recent contexts",
                len(recent) > 0,
                f"Found: {len(recent)}"
            )
            
            # Test: Search by success rate
            successful = await self.context_search.search_by_success_rate(
                search_contexts,
                min_success_rate=0.9,
                max_success_rate=1.0,
                limit=10
            )
            self.record_test(
                "Search by success rate",
                len(successful) == 5,  # All were successful
                f"Found: {len(successful)}"
            )
            
            # Test: Find similar contexts
            if search_contexts:
                target = search_contexts[0]
                similar = await self.context_search.find_similar_contexts(
                    target,
                    search_contexts[1:],
                    similarity_threshold=0.0,
                    limit=5
                )
                self.record_test(
                    "Find similar contexts",
                    similar is not None,
                    f"Found: {len(similar) if similar else 0}"
                )
            
            print_success("ContextSearch tests complete", f"{self.tests_passed}/{self.tests_run} passed")
            
        except Exception as e:
            self.record_test("ContextSearch", False, f"Error: {str(e)}")
    
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        print_section("TEST 6: End-to-End - Complete Roadmap Generation")
        
        try:
            # Simulate complete workflow
            parent_id = "e2e_parent"
            
            # Store orchestration
            await self.workflow_helper.store_orchestration_result(
                workflow_id=parent_id,
                orchestration_data={"query": "Build OAuth2 system"},
                child_workflow_ids=["e2e_a", "e2e_b", "e2e_c", "e2e_d"],
                duration_ms=10000.0
            )
            
            # Store all 4 workflow results
            await self.workflow_helper.store_workflow_a_result(
                workflow_id="e2e_a",
                feature_breakdown={"stories": 12, "tasks": 28},
                prompts_used=["p1", "p2"],
                documents_generated=["d1"],
                duration_ms=2500.0,
                parent_workflow_id=parent_id
            )
            
            await self.workflow_helper.store_workflow_b_result(
                workflow_id="e2e_b",
                historical_context={"sources": 40},
                documents_retrieved=["d2", "d3"],
                jira_tickets=["J1"],
                confluence_pages=["C1"],
                duration_ms=3000.0,
                parent_workflow_id=parent_id
            )
            
            # Test: All workflows stored
            parent_ctx = await self.workflow_helper.get_workflow_context(parent_id)
            ctx_a = await self.workflow_helper.get_workflow_context("e2e_a")
            ctx_b = await self.workflow_helper.get_workflow_context("e2e_b")
            
            self.record_test(
                "All workflows stored",
                parent_ctx is not None and ctx_a is not None and ctx_b is not None,
                f"Parent: {parent_ctx is not None}, Children: {ctx_a is not None and ctx_b is not None}"
            )
            
            # Test: Artifacts linked
            if ctx_a and ctx_b:
                total_artifacts = len(ctx_a.linked_artifacts) + len(ctx_b.linked_artifacts)
                self.record_test(
                    "Artifacts linked across workflows",
                    total_artifacts >= 5,  # At least 5 artifacts
                    f"Total: {total_artifacts}"
                )
            
            # Test: Aggregation works
            all_child_contexts = []
            for wf_id in ["e2e_a", "e2e_b"]:
                ctx = await self.workflow_helper.get_workflow_context(wf_id)
                if ctx:
                    all_child_contexts.append(ctx)
            
            if all_child_contexts:
                aggregated = await self.context_aggregator.aggregate_parallel_workflows(all_child_contexts)
                self.record_test(
                    "End-to-end aggregation",
                    aggregated is not None and aggregated.get("total_workflows") >= 2,
                    f"Aggregated: {aggregated.get('total_workflows') if aggregated else 0}"
                )
            
            print_success("End-to-end workflow test complete", f"{self.tests_passed}/{self.tests_run} passed")
            
        except Exception as e:
            self.record_test("End-to-end workflow", False, f"Error: {str(e)}")
    
    def print_final_results(self):
        """Print final test results."""
        print_header("🎯 PHASE 3 FUNCTIONAL TEST RESULTS")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"\n   📊 Total Tests Run: {self.tests_run}")
        print(f"   ✅ Tests Passed: {self.tests_passed}")
        print(f"   ❌ Tests Failed: {self.tests_failed}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_failed == 0:
            print("\n   🎉 ALL TESTS PASSED! Phase 3 code is working correctly!")
        else:
            print(f"\n   ⚠️  {self.tests_failed} test(s) failed. Review implementation.")
        
        return self.tests_failed == 0


async def main():
    """Run all functional tests."""
    print("\n" + "🎯" * 42)
    print("\n  PHASE 3 FUNCTIONAL TEST SUITE")
    print("  Testing Real Implementation of All Phase 3 Components")
    print("\n" + "🎯" * 42)
    
    test_suite = Phase3FunctionalTest()
    
    start_time = datetime.now()
    
    try:
        # Run all test suites
        await test_suite.test_context_manager()
        await test_suite.test_artifact_linker()
        await test_suite.test_workflow_integration()
        await test_suite.test_context_aggregator()
        await test_suite.test_context_search()
        await test_suite.test_end_to_end_workflow()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Print results
        all_passed = test_suite.print_final_results()
        
        print(f"\n   ⏱️  Total Test Duration: {duration:.2f} seconds")
        
        if all_passed:
            print("\n" + "=" * 85)
            print("  ✅ PHASE 3 VERIFICATION COMPLETE - ALL SYSTEMS OPERATIONAL")
            print("=" * 85 + "\n")
            return 0
        else:
            print("\n" + "=" * 85)
            print("  ⚠️  PHASE 3 VERIFICATION INCOMPLETE - SEE FAILURES ABOVE")
            print("=" * 85 + "\n")
            return 1
        
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

