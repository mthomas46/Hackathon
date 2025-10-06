"""E2E tests for query interpretation and orchestration workflow."""

import pytest
import httpx


class TestQueryWorkflow:
    """Test complete query processing workflow."""
    
    @pytest.mark.asyncio
    async def test_query_interpretation_workflow(
        self,
        http_client: httpx.AsyncClient,
        service_urls: dict,
        test_query: str
    ):
        """Test workflow: interpret query → create workflow → execute."""
        
        # Step 1: Parse query with Interpreter
        print(f"\n🔍 Step 1: Parsing query: '{test_query}'")
        interpreter_url = service_urls["mcp_interpreter"]
        
        response = await http_client.post(
            f"{interpreter_url}/api/v1/queries/parse",
            json={"query": test_query}
        )
        assert response.status_code == 200, f"Parse failed: {response.text}"
        parsed = response.json()
        print(f"✅ Parsed intent: {parsed.get('intent', 'unknown')}")
        print(f"   Confidence: {parsed.get('confidence', 0):.2f}")
        print(f"   Entities: {len(parsed.get('entities', []))}")
        
        # Step 2: Create workflow with Orchestrator
        print("\n🎭 Step 2: Creating workflow...")
        orchestrator_url = service_urls["mcp_orchestrator"]
        
        response = await http_client.post(
            f"{orchestrator_url}/api/v1/workflows",
            json={
                "name": "Test Query Workflow",
                "query": test_query,
                "parsed_query": parsed,
                "pattern": "ensemble_orchestration"
            }
        )
        assert response.status_code in [200, 201], f"Workflow creation failed: {response.text}"
        workflow = response.json()
        workflow_id = workflow.get("workflow_id")
        print(f"✅ Workflow created: {workflow_id}")
        print(f"   Pattern: {workflow.get('pattern', 'unknown')}")
        
        # Step 3: Execute workflow
        print("\n⚡ Step 3: Executing workflow...")
        response = await http_client.post(
            f"{orchestrator_url}/api/v1/workflows/{workflow_id}/execute"
        )
        assert response.status_code == 200, f"Execution failed: {response.text}"
        execution = response.json()
        print(f"✅ Execution started: {execution.get('status', 'unknown')}")
        
        # Step 4: Get workflow status
        print("\n📊 Step 4: Checking workflow status...")
        response = await http_client.get(
            f"{orchestrator_url}/api/v1/workflows/{workflow_id}"
        )
        assert response.status_code == 200
        status = response.json()
        print(f"✅ Status: {status.get('status', 'unknown')}")
        print(f"   Progress: {status.get('progress_percentage', 0):.1f}%")
        
        print("\n" + "="*60)
        print("🎉 QUERY WORKFLOW TEST COMPLETE!")
        print("="*60)
    
    @pytest.mark.asyncio
    async def test_multiple_query_intents(
        self,
        http_client: httpx.AsyncClient,
        service_urls: dict
    ):
        """Test parsing various query types."""
        interpreter_url = service_urls["mcp_interpreter"]
        
        test_queries = [
            "Search for authentication documentation",
            "How many users are in the system?",
            "Compare performance of service A vs service B",
            "Generate a summary of recent changes",
            "What is the status of feature X?",
        ]
        
        print("\n🔍 Testing multiple query intents...")
        results = []
        
        for query in test_queries:
            response = await http_client.post(
                f"{interpreter_url}/api/v1/queries/parse",
                json={"query": query}
            )
            if response.status_code == 200:
                parsed = response.json()
                intent = parsed.get("intent", "unknown")
                confidence = parsed.get("confidence", 0)
                results.append((query[:40], intent, confidence))
                print(f"  ✅ '{query[:40]}...' → {intent} ({confidence:.2f})")
            else:
                print(f"  ❌ '{query[:40]}...' → ERROR")
        
        assert len(results) > 0, "No queries parsed successfully"
        print(f"\n✅ Parsed {len(results)}/{len(test_queries)} queries")

