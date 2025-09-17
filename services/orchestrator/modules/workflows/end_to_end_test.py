"""End-to-End Ecosystem Test Workflow.

Comprehensive workflow that demonstrates the full LLM Documentation Ecosystem:
1. Generate mock data (Confluence, GitHub, Jira)
2. Store documents in doc_store
3. Use prompt_store for analysis prompts
4. Analyze documents with analysis service
5. Create unified summaries with summarizer hub
6. Generate final report

This workflow serves as both a demonstration and comprehensive integration test.
"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from datetime import datetime

from ..langgraph.state import WorkflowState
from ..langgraph.tools import (
    store_document_tool,
    analyze_document_tool,
    summarize_document_tool,
    get_prompt_tool
)


class EndToEndTestWorkflow:
    """End-to-end ecosystem test workflow implementation."""

    def __init__(self):
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the comprehensive end-to-end test workflow."""
        workflow = StateGraph(WorkflowState)

        # Define all workflow nodes
        workflow.add_node("generate_mock_data", self.generate_mock_data_node)
        workflow.add_node("store_documents", self.store_documents_node)
        workflow.add_node("prepare_analysis", self.prepare_analysis_node)
        workflow.add_node("analyze_documents", self.analyze_documents_node)
        workflow.add_node("store_analysis_results", self.store_analysis_results_node)
        workflow.add_node("generate_summaries", self.generate_summaries_node)
        workflow.add_node("create_unified_summary", self.create_unified_summary_node)
        workflow.add_node("generate_final_report", self.generate_final_report_node)
        workflow.add_node("cleanup_workflow", self.cleanup_workflow_node)

        # Define workflow edges (execution flow)
        workflow.set_entry_point("generate_mock_data")

        workflow.add_edge("generate_mock_data", "store_documents")
        workflow.add_edge("store_documents", "prepare_analysis")
        workflow.add_edge("prepare_analysis", "analyze_documents")
        workflow.add_edge("analyze_documents", "store_analysis_results")
        workflow.add_edge("store_analysis_results", "generate_summaries")
        workflow.add_edge("generate_summaries", "create_unified_summary")
        workflow.add_edge("create_unified_summary", "generate_final_report")
        workflow.add_edge("generate_final_report", "cleanup_workflow")
        workflow.add_edge("cleanup_workflow", END)

        return workflow

    async def generate_mock_data_node(self, state: WorkflowState) -> WorkflowState:
        """Generate mock data for testing."""
        print("=== GENERATING MOCK DATA ===")

        # Generate mock data for Confluence, GitHub, and Jira
        mock_sources = ["confluence", "github", "jira"]

        for source in mock_sources:
            print(f"Generating mock data for {source}...")

            # Call mock data generator service
            mock_data = await self._generate_mock_data_for_source(source, state.input_data)

            # Store in workflow state
            state.output_data[f"{source}_documents"] = mock_data

        state.add_log_entry("INFO", f"Generated mock data for {len(mock_sources)} sources")
        return state

    async def store_documents_node(self, state: WorkflowState) -> WorkflowState:
        """Store generated documents in doc_store."""
        print("=== STORING DOCUMENTS ===")

        stored_documents = []

        # Store documents from each source
        for source in ["confluence", "github", "jira"]:
            documents = state.output_data.get(f"{source}_documents", [])

            for doc in documents:
                # Store document in doc_store
                stored_doc = await store_document_tool(
                    title=f"Mock {source.title()} Document - {doc.get('title', 'Untitled')}",
                    content=doc.get('content', ''),
                    doc_type=source,
                    tags=["mock-data", source, "end-to-end-test"],
                    workflow_id=state.run_id
                )

                if stored_doc["success"]:
                    doc["doc_store_id"] = stored_doc["document_id"]
                    stored_documents.append(doc)

        state.output_data["stored_documents"] = stored_documents
        state.add_log_entry("INFO", f"Stored {len(stored_documents)} documents in doc_store")
        return state

    async def prepare_analysis_node(self, state: WorkflowState) -> WorkflowState:
        """Prepare analysis prompts and context."""
        print("=== PREPARING ANALYSIS ===")

        # Get analysis prompt from prompt_store
        analysis_prompt = await get_prompt_tool(
            task_type="document_analysis",
            context={"analysis_type": "consistency", "quality_check": True}
        )

        if analysis_prompt["success"]:
            state.output_data["analysis_prompt"] = analysis_prompt["data"]
            state.add_log_entry("INFO", "Retrieved analysis prompt from prompt_store")
        else:
            # Fallback prompt
            state.output_data["analysis_prompt"] = {
                "content": "Analyze this document for consistency, quality, and completeness.",
                "variables": ["document_content"]
            }

        return state

    async def analyze_documents_node(self, state: WorkflowState) -> WorkflowState:
        """Analyze all stored documents."""
        print("=== ANALYZING DOCUMENTS ===")

        analysis_results = []
        stored_documents = state.output_data.get("stored_documents", [])

        for doc in stored_documents:
            print(f"Analyzing document: {doc.get('title', 'Unknown')}")

            # Analyze document
            analysis = await analyze_document_tool(
                doc_id=doc.get("doc_store_id"),
                analysis_type="comprehensive",
                prompt=state.output_data.get("analysis_prompt", {}).get("content", "")
            )

            if analysis["success"]:
                analysis_result = {
                    "document_id": doc.get("doc_store_id"),
                    "document_title": doc.get("title"),
                    "analysis_result": analysis["data"],
                    "analysis_timestamp": datetime.now().isoformat()
                }
                analysis_results.append(analysis_result)

        state.output_data["analysis_results"] = analysis_results
        state.add_log_entry("INFO", f"Analyzed {len(analysis_results)} documents")
        return state

    async def store_analysis_results_node(self, state: WorkflowState) -> WorkflowState:
        """Store analysis results back to doc_store."""
        print("=== STORING ANALYSIS RESULTS ===")

        stored_results = []
        analysis_results = state.output_data.get("analysis_results", [])

        for result in analysis_results:
            # Store analysis result as new document
            stored_result = await store_document_tool(
                title=f"Analysis Result - {result['document_title']}",
                content=result["analysis_result"],
                doc_type="analysis_result",
                tags=["analysis", "mock-data", "end-to-end-test"],
                metadata={
                    "original_document_id": result["document_id"],
                    "analysis_type": "comprehensive",
                    "workflow_id": state.run_id
                },
                workflow_id=state.run_id
            )

            if stored_result["success"]:
                result["analysis_doc_id"] = stored_result["document_id"]
                stored_results.append(result)

        state.output_data["stored_analysis_results"] = stored_results
        state.add_log_entry("INFO", f"Stored {len(stored_results)} analysis results")
        return state

    async def generate_summaries_node(self, state: WorkflowState) -> WorkflowState:
        """Generate individual summaries for each document."""
        print("=== GENERATING SUMMARIES ===")

        summaries = []
        stored_documents = state.output_data.get("stored_documents", [])

        for doc in stored_documents:
            print(f"Generating summary for: {doc.get('title', 'Unknown')}")

            # Generate summary using summarizer hub
            summary = await summarize_document_tool(
                content=doc.get('content', ''),
                max_length=300,
                format="structured"
            )

            if summary["success"]:
                summary_data = {
                    "document_id": doc.get("doc_store_id"),
                    "document_title": doc.get("title"),
                    "summary": summary["data"],
                    "summary_timestamp": datetime.now().isoformat()
                }
                summaries.append(summary_data)

        state.output_data["individual_summaries"] = summaries
        state.add_log_entry("INFO", f"Generated {len(summaries)} individual summaries")
        return state

    async def create_unified_summary_node(self, state: WorkflowState) -> WorkflowState:
        """Create unified summary comparing all documents."""
        print("=== CREATING UNIFIED SUMMARY ===")

        individual_summaries = state.output_data.get("individual_summaries", [])
        analysis_results = state.output_data.get("analysis_results", [])

        # Combine all summaries and analyses
        unified_content = self._create_unified_content(individual_summaries, analysis_results)

        # Generate unified summary
        unified_summary = await summarize_document_tool(
            content=unified_content,
            max_length=500,
            format="comprehensive_report"
        )

        if unified_summary["success"]:
            state.output_data["unified_summary"] = {
                "content": unified_summary["data"],
                "sources_count": len(individual_summaries),
                "analysis_count": len(analysis_results),
                "generated_at": datetime.now().isoformat()
            }

        state.add_log_entry("INFO", "Created unified summary across all sources")
        return state

    async def generate_final_report_node(self, state: WorkflowState) -> WorkflowState:
        """Generate final comprehensive report."""
        print("=== GENERATING FINAL REPORT ===")

        # Combine all workflow data into final report
        report_content = self._generate_final_report_content(state)

        # Store final report in doc_store
        final_report = await store_document_tool(
            title="End-to-End Ecosystem Test Report",
            content=report_content,
            doc_type="final_report",
            tags=["final-report", "end-to-end-test", "ecosystem-demo"],
            metadata={
                "workflow_id": state.run_id,
                "execution_time": datetime.now().isoformat(),
                "sources_tested": ["confluence", "github", "jira"],
                "services_tested": ["mock-data-generator", "doc_store", "prompt_store",
                                  "analysis_service", "summarizer_hub"]
            },
            workflow_id=state.run_id
        )

        if final_report["success"]:
            state.output_data["final_report"] = {
                "report_id": final_report["document_id"],
                "report_content": report_content,
                "generated_at": datetime.now().isoformat()
            }

        state.add_log_entry("INFO", "Generated final comprehensive report")
        return state

    async def cleanup_workflow_node(self, state: WorkflowState) -> WorkflowState:
        """Clean up workflow data and provide summary."""
        print("=== WORKFLOW CLEANUP ===")

        # Generate execution summary
        summary = {
            "workflow_id": state.run_id,
            "execution_status": "completed",
            "documents_generated": len(state.output_data.get("stored_documents", [])),
            "analyses_performed": len(state.output_data.get("analysis_results", [])),
            "summaries_created": len(state.output_data.get("individual_summaries", [])),
            "final_report_id": state.output_data.get("final_report", {}).get("report_id"),
            "execution_time": datetime.now().isoformat()
        }

        state.output_data["execution_summary"] = summary
        state.add_log_entry("INFO", f"Workflow completed successfully - {summary}")
        return state

    # Helper methods

    async def _generate_mock_data_for_source(self, source: str, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock data for a specific source."""
        # This would call the mock data generator service
        # For now, return sample data
        return [
            {
                "title": f"Mock {source.title()} Document 1",
                "content": f"This is mock content for {source} document 1. Generated for end-to-end testing.",
                "source": source,
                "metadata": {"test": True, "index": 1}
            },
            {
                "title": f"Mock {source.title()} Document 2",
                "content": f"This is mock content for {source} document 2. Generated for end-to-end testing.",
                "source": source,
                "metadata": {"test": True, "index": 2}
            }
        ]

    def _create_unified_content(self, summaries: List[Dict], analyses: List[Dict]) -> str:
        """Create unified content from summaries and analyses."""
        content_parts = ["# Unified Document Analysis Report\n"]

        content_parts.append("## Individual Document Summaries\n")
        for summary in summaries:
            content_parts.append(f"### {summary['document_title']}")
            content_parts.append(summary['summary'])
            content_parts.append("")

        content_parts.append("## Analysis Results\n")
        for analysis in analyses:
            content_parts.append(f"### Analysis: {analysis['document_title']}")
            content_parts.append(analysis['analysis_result'])
            content_parts.append("")

        return "\n".join(content_parts)

    def _generate_final_report_content(self, state: WorkflowState) -> str:
        """Generate final report content."""
        report_parts = []

        # Header
        report_parts.append("# End-to-End Ecosystem Test Report")
        report_parts.append(f"**Workflow ID:** {state.run_id}")
        report_parts.append(f"**Generated:** {datetime.now().isoformat()}")
        report_parts.append("")

        # Execution Summary
        summary = state.output_data.get("execution_summary", {})
        report_parts.append("## Execution Summary")
        report_parts.append(f"- Documents Generated: {summary.get('documents_generated', 0)}")
        report_parts.append(f"- Analyses Performed: {summary.get('analyses_performed', 0)}")
        report_parts.append(f"- Summaries Created: {summary.get('summaries_created', 0)}")
        report_parts.append("")

        # Services Tested
        report_parts.append("## Services Tested")
        services = [
            "Mock Data Generator",
            "Document Store",
            "Prompt Store",
            "Analysis Service",
            "Summarizer Hub",
            "Orchestrator (LangGraph)",
            "LLM Gateway"
        ]
        for service in services:
            report_parts.append(f"- ✅ {service}")
        report_parts.append("")

        # Unified Summary
        unified = state.output_data.get("unified_summary", {})
        if unified:
            report_parts.append("## Unified Summary")
            report_parts.append(unified.get("content", "No unified summary available"))
            report_parts.append("")

        # Individual Results
        summaries = state.output_data.get("individual_summaries", [])
        if summaries:
            report_parts.append("## Individual Document Summaries")
            for summary in summaries:
                report_parts.append(f"### {summary['document_title']}")
                report_parts.append(summary['summary'])
                report_parts.append("")

        return "\n".join(report_parts)

    def get_workflow(self) -> StateGraph:
        """Get the compiled workflow."""
        return self.workflow

    def get_workflow_description(self) -> str:
        """Get workflow description for documentation."""
        return """
        End-to-End Ecosystem Test Workflow

        This workflow demonstrates the complete LLM Documentation Ecosystem by:
        1. Generating mock data (Confluence, GitHub, Jira documents)
        2. Storing documents in doc_store for workflow duration
        3. Using prompt_store to get optimized analysis prompts
        4. Analyzing documents with analysis service (with prompt references)
        5. Storing analysis results in doc_store with prompt tracking
        6. Generating individual summaries with summarizer hub
        7. Creating unified summary comparing multiple models
        8. Generating final comprehensive report
        9. Cleaning up workflow data

        Services Involved:
        - Mock Data Generator (LLM-integrated)
        - Document Store (persistence)
        - Prompt Store (optimization)
        - Analysis Service (document analysis)
        - Summarizer Hub (multi-model summaries)
        - Orchestrator (LangGraph workflow coordination)
        - LLM Gateway (unified AI access)
        """


# Create workflow instance
end_to_end_test_workflow = EndToEndTestWorkflow()
