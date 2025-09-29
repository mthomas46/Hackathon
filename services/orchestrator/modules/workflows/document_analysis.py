"""Document analysis workflow using LangGraph.

This module defines a LangGraph workflow for comprehensive document analysis
leveraging multiple orchestrator services.
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END

from ..langgraph.state import WorkflowState
from ..langgraph.tools import (
    summarize_document_tool,
    extract_key_concepts_tool,
    analyze_document_consistency_tool,
    store_document_tool,
    send_notification_tool
)


def fetch_document_node(state: WorkflowState) -> WorkflowState:
    """Fetch and prepare document for analysis."""
    # In a real implementation, this would fetch from document store
    # For now, we'll use the input data
    state.add_log_entry("INFO", "Starting document analysis workflow")
    return state


def analyze_document_node(state: WorkflowState) -> WorkflowState:
    """Analyze document using multiple services."""
    try:
        document_content = state.input_data.get("content", "")

        # Summarize the document
        summary_result = summarize_document_tool(document_content)
        if summary_result["success"]:
            state.output_data["summary"] = summary_result["data"]

        # Extract key concepts
        concepts_result = extract_key_concepts_tool(document_content)
        if concepts_result["success"]:
            state.output_data["key_concepts"] = concepts_result["data"]

        # Analyze consistency (would need multiple documents)
        consistency_result = analyze_document_consistency_tool(
            [state.input_data.get("doc_id", "current")],
            {"check_references": True, "check_formatting": True}
        )
        if consistency_result["success"]:
            state.output_data["consistency_analysis"] = consistency_result["data"]

        state.add_log_entry("INFO", "Document analysis completed")
        state.current_step = "analysis_complete"

    except Exception as e:
        state.add_error({
            "step": "analysis",
            "error": str(e),
            "error_type": "analysis_error"
        })
        state.current_step = "analysis_failed"

    return state


def store_results_node(state: WorkflowState) -> WorkflowState:
    """Store analysis results."""
    try:
        # Store the analysis results
        analysis_results = {
            "original_content": state.input_data.get("content", ""),
            "summary": state.output_data.get("summary", {}),
            "key_concepts": state.output_data.get("key_concepts", []),
            "consistency_analysis": state.output_data.get("consistency_analysis", {}),
            "workflow_id": state.metadata.workflow_id,
            "timestamp": state.metadata.created_at.isoformat()
        }

        store_result = store_document_tool(
            content=str(analysis_results),
            metadata={
                "type": "document_analysis",
                "workflow_id": state.metadata.workflow_id,
                "analysis_type": "comprehensive"
            },
            source="orchestrator_workflow"
        )

        if store_result["success"]:
            state.output_data["stored_analysis_id"] = store_result["data"].get("id")
            state.add_log_entry("INFO", "Analysis results stored successfully")

        state.current_step = "storage_complete"

    except Exception as e:
        state.add_error({
            "step": "storage",
            "error": str(e),
            "error_type": "storage_error"
        })
        state.current_step = "storage_failed"

    return state


def notify_stakeholders_node(state: WorkflowState) -> WorkflowState:
    """Notify stakeholders of analysis completion."""
    try:
        # Send notification about completed analysis
        notification_message = f"""
        Document analysis completed for workflow {state.metadata.workflow_id}

        Summary: {state.output_data.get('summary', {}).get('summary', 'N/A')[:100]}...

        Key findings:
        - Concepts identified: {len(state.output_data.get('key_concepts', []))}
        - Consistency score: {state.output_data.get('consistency_analysis', {}).get('score', 'N/A')}

        Results stored with ID: {state.output_data.get('stored_analysis_id', 'N/A')}
        """

        notification_result = send_notification_tool(
            message=notification_message,
            channels=["email"],
            priority="normal"
        )

        if notification_result["success"]:
            state.add_log_entry("INFO", "Stakeholders notified successfully")

        state.current_step = "notification_complete"

    except Exception as e:
        state.add_error({
            "step": "notification",
            "error": str(e),
            "error_type": "notification_error"
        })
        state.current_step = "notification_failed"

    return state


def should_retry(state: WorkflowState) -> str:
    """Determine if workflow should retry or end."""
    if state.errors and state.can_retry():
        state.increment_retry()
        return "retry_analysis"
    else:
        return "end"


def create_document_analysis_workflow():
    """Create a LangGraph workflow for document analysis."""

    # Create the workflow graph
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("fetch_document", fetch_document_node)
    workflow.add_node("analyze_document", analyze_document_node)
    workflow.add_node("store_results", store_results_node)
    workflow.add_node("notify_stakeholders", notify_stakeholders_node)
    workflow.add_node("retry_analysis", analyze_document_node)  # Retry node

    # Add edges
    workflow.add_edge("fetch_document", "analyze_document")
    workflow.add_edge("analyze_document", "store_results")
    workflow.add_edge("store_results", "notify_stakeholders")
    workflow.add_edge("notify_stakeholders", END)

    # Add conditional edges for error handling
    workflow.add_conditional_edges(
        "analyze_document",
        should_retry,
        {
            "retry_analysis": "retry_analysis",
            "end": "store_results"
        }
    )

    workflow.add_conditional_edges(
        "retry_analysis",
        should_retry,
        {
            "retry_analysis": "retry_analysis",
            "end": "store_results"
        }
    )

    # Set the entry point
    workflow.set_entry_point("fetch_document")

    # Compile and return the workflow
    return workflow.compile()
