"""
PR Confidence Analysis Orchestration Workflow

Simplified orchestrator workflow that coordinates analysis across services
without containing the actual analysis business logic.
"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from datetime import datetime

from ..langgraph.state import WorkflowState
from ..langgraph.tools import (
    store_document_tool,
    search_documents_tool,
    send_notification_tool
)


class PRConfidenceOrchestrationWorkflow:
    """Orchestration-focused PR confidence analysis workflow."""

    def __init__(self):
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the orchestration-focused workflow."""
        workflow = StateGraph(WorkflowState)

        # Define workflow nodes
        workflow.add_node("extract_pr_context", self.extract_pr_context_node)
        workflow.add_node("fetch_jira_requirements", self.fetch_jira_requirements_node)
        workflow.add_node("fetch_confluence_docs", self.fetch_confluence_docs_node)
        workflow.add_node("coordinate_analysis", self.coordinate_analysis_node)
        workflow.add_node("generate_report", self.generate_report_node)
        workflow.add_node("send_notifications", self.send_notifications_node)

        # Define workflow edges
        workflow.set_entry_point("extract_pr_context")

        # Sequential flow
        workflow.add_edge("extract_pr_context", "fetch_jira_requirements")
        workflow.add_edge("fetch_jira_requirements", "fetch_confluence_docs")
        workflow.add_edge("fetch_confluence_docs", "coordinate_analysis")
        workflow.add_edge("coordinate_analysis", "generate_report")
        workflow.add_edge("generate_report", "send_notifications")
        workflow.add_edge("send_notifications", END)

        return workflow

    async def extract_pr_context_node(self, state: WorkflowState) -> WorkflowState:
        """Extract and prepare PR context for analysis."""
        print("=== EXTRACTING PR CONTEXT ===")

        pr_data = state["parameters"].get("pr_data", {})
        state["context"]["pr_data"] = pr_data

        state["messages"].append({
            "role": "assistant",
            "content": f"Extracted PR context for {pr_data.get('id', 'unknown PR')}"
        })

        return state

    async def fetch_jira_requirements_node(self, state: WorkflowState) -> WorkflowState:
        """Fetch related Jira requirements."""
        print("=== FETCHING JIRA REQUIREMENTS ===")

        pr_data = state["context"].get("pr_data", {})
        jira_ticket = pr_data.get("jira_ticket")

        if jira_ticket:
            # In production, this would call the source-agent service
            # For now, we'll use the provided jira_data or create mock data
            jira_data = state["parameters"].get("jira_data", self._create_mock_jira_data(jira_ticket))
            state["context"]["jira_data"] = jira_data

            state["messages"].append({
                "role": "assistant",
                "content": f"Fetched Jira requirements for ticket {jira_ticket}"
            })
        else:
            state["context"]["jira_data"] = {}
            state["messages"].append({
                "role": "assistant",
                "content": "No Jira ticket specified"
            })

        return state

    async def fetch_confluence_docs_node(self, state: WorkflowState) -> WorkflowState:
        """Fetch related Confluence documentation."""
        print("=== FETCHING CONFLUENCE DOCUMENTATION ===")

        pr_data = state["context"].get("pr_data", {})
        confluence_docs = state["parameters"].get("confluence_docs", [])

        if not confluence_docs:
            # Create mock confluence docs if none provided
            confluence_docs = self._create_mock_confluence_docs(pr_data)

        state["context"]["confluence_docs"] = confluence_docs

        state["messages"].append({
            "role": "assistant",
            "content": f"Fetched {len(confluence_docs)} Confluence documentation pages"
        })

        return state

    async def coordinate_analysis_node(self, state: WorkflowState) -> WorkflowState:
        """Coordinate analysis across analysis service."""
        print("=== COORDINATING ANALYSIS ACROSS SERVICES ===")

        # Import service client utilities
        from ..shared_utils import get_orchestrator_service_client
        service_client = get_orchestrator_service_client()

        # Prepare analysis request
        analysis_request = {
            "pr_data": state["context"]["pr_data"],
            "jira_data": state["context"]["jira_data"],
            "confluence_docs": state["context"]["confluence_docs"],
            "analysis_scope": state["parameters"].get("analysis_scope", "comprehensive"),
            "include_recommendations": True,
            "confidence_threshold": state["parameters"].get("confidence_threshold", 0.7)
        }

        try:
            # Call analysis service
            analysis_response = await service_client.post_json(
                f"{service_client.analysis_service_url()}/pr-confidence/analyze",
                analysis_request
            )

            if analysis_response and "data" in analysis_response:
                analysis_results = analysis_response["data"]
                state["context"]["analysis_results"] = analysis_results

                # Store analysis results
                await store_document_tool(
                    content=str(analysis_results),
                    metadata={
                        "type": "pr_confidence_analysis",
                        "workflow_id": state["run_id"],
                        "pr_id": analysis_results.get("pr_id"),
                        "confidence_score": analysis_results.get("confidence_score"),
                        "confidence_level": analysis_results.get("confidence_level"),
                        "approval_recommendation": analysis_results.get("approval_recommendation")
                    },
                    source="orchestrator"
                )

                state["messages"].append({
                    "role": "assistant",
                    "content": f"Analysis service completed: {analysis_results.get('confidence_score', 0):.1%} confidence ({analysis_results.get('confidence_level', 'unknown')})"
                })
            else:
                raise Exception("Analysis service returned invalid response")

        except Exception as e:
            print(f"Analysis coordination failed: {e}")
            # Create fallback analysis results
            state["context"]["analysis_results"] = self._create_fallback_analysis_results(state)
            state["messages"].append({
                "role": "assistant",
                "content": f"Analysis coordination failed, using fallback: {e}"
            })

        return state

    async def generate_report_node(self, state: WorkflowState) -> WorkflowState:
        """Generate final report from analysis results."""
        print("=== GENERATING FINAL REPORT ===")

        analysis_results = state["context"].get("analysis_results", {})

        # Import report generator
        from ..analysis.pr_report_generator import pr_report_generator

        # Create mock data for report generation (in production, this would come from analysis results)
        pr_data = state["context"]["pr_data"]
        jira_data = state["context"]["jira_data"]
        confluence_docs = state["context"]["confluence_docs"]

        # Generate report
        report = pr_report_generator.generate_report(
            pr_data, jira_data, confluence_docs,
            type('obj', (object,), analysis_results.get("cross_reference_results", {})),
            type('obj', (object,), {
                "overall_score": analysis_results.get("confidence_score", 0),
                "confidence_level": analysis_results.get("confidence_level", "medium"),
                "approval_recommendation": analysis_results.get("approval_recommendation", "review_required"),
                "component_scores": analysis_results.get("component_scores", {}),
                "critical_concerns": analysis_results.get("critical_concerns", []),
                "risk_factors": [],
                "strengths": analysis_results.get("strengths", []),
                "improvement_areas": analysis_results.get("improvement_areas", [])
            }),
            [type('obj', (object,), gap) for gap in analysis_results.get("detected_gaps", [])],
            analysis_results.get("analysis_duration", 0.0)
        )

        # Save reports
        saved_files = pr_report_generator.save_reports(report, "orchestrator_reports")

        state["context"]["final_report"] = report
        state["context"]["report_files"] = saved_files

        state["messages"].append({
            "role": "assistant",
            "content": f"Final report generated and saved to {saved_files['html_report']}"
        })

        return state

    async def send_notifications_node(self, state: WorkflowState) -> WorkflowState:
        """Send notifications with analysis results."""
        print("=== SENDING NOTIFICATIONS ===")

        pr_data = state["context"]["pr_data"]
        analysis_results = state["context"].get("analysis_results", {})
        report_files = state["context"].get("report_files", {})

        # Prepare notification content
        confidence_score = analysis_results.get("confidence_score", 0)
        confidence_level = analysis_results.get("confidence_level", "medium")
        approval_rec = analysis_results.get("approval_recommendation", "review_required")

        html_report_url = report_files.get('html_report', 'N/A')

        message_parts = [
            f"PR Confidence Analysis Complete: {confidence_score:.1%} confidence",
            f"Recommendation: {approval_rec.replace('_', ' ').title()}",
            f"Confidence Level: {confidence_level.upper()}",
            f"Report Available: {html_report_url}"
        ]

        if analysis_results.get("critical_concerns"):
            message_parts.append(f"⚠️ {len(analysis_results['critical_concerns'])} critical concerns identified")

        message = "\\n".join(message_parts)

        # Determine notification urgency
        urgency = "high" if confidence_level in ['low', 'critical'] or analysis_results.get("critical_concerns") else "normal"

        # Send notification to PR author
        await send_notification_tool(
            message=message,
            recipient=pr_data.get("author", "developer"),
            urgency=urgency,
            additional_data={
                "pr_id": pr_data.get("id"),
                "confidence_level": confidence_level,
                "recommendation": approval_rec,
                "html_report": html_report_url,
                "confidence_score": confidence_score
            }
        )

        # Send notification to tech lead for low confidence or critical issues
        if confidence_level in ['low', 'critical'] or analysis_results.get("critical_concerns"):
            lead_message = f"ATTENTION REQUIRED: PR {pr_data.get('id')} needs review\\n{message}"
            await send_notification_tool(
                message=lead_message,
                recipient="tech_lead",
                urgency="high",
                additional_data=analysis_results
            )

        state["messages"].append({
            "role": "assistant",
            "content": f"Notifications sent with urgency: {urgency}"
        })

        return state

    def _create_mock_jira_data(self, ticket_id: str) -> Dict[str, Any]:
        """Create mock Jira data for testing."""
        return {
            "id": ticket_id,
            "title": "Implement OAuth2 Authentication",
            "description": "As a user, I want to authenticate using OAuth2 so that I can securely access the API.",
            "acceptance_criteria": [
                "User can authenticate with OAuth2 provider",
                "API validates OAuth2 tokens",
                "Token refresh mechanism implemented"
            ],
            "story_points": 8,
            "priority": "High"
        }

    def _create_mock_confluence_docs(self, pr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create mock Confluence docs for testing."""
        return [{
            "id": "API_AUTH_DOCS",
            "title": "Authentication API Documentation",
            "content": "OAuth2 implementation guide with endpoints and security requirements.",
            "last_updated": datetime.now().isoformat()
        }]

    def _create_fallback_analysis_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback analysis results when service call fails."""
        return {
            "workflow_id": state["run_id"],
            "confidence_score": 0.5,
            "confidence_level": "medium",
            "approval_recommendation": "review_required",
            "cross_reference_results": {
                "overall_alignment_score": 0.5,
                "requirement_alignment": {},
                "documentation_consistency": {},
                "identified_gaps": ["Analysis service unavailable"],
                "consistency_issues": ["Unable to perform detailed analysis"],
                "risk_assessment": "medium"
            },
            "detected_gaps": [{
                "gap_type": "analysis",
                "severity": "medium",
                "description": "Analysis service temporarily unavailable",
                "evidence": "Service call failed",
                "recommendation": "Retry analysis or perform manual review",
                "estimated_effort": "low",
                "blocking_approval": False
            }],
            "component_scores": {
                "requirements_alignment": 0.5,
                "code_quality": 0.5,
                "testing_completeness": 0.5,
                "documentation_consistency": 0.5,
                "security_compliance": 0.5
            },
            "recommendations": ["Manual review recommended due to analysis service unavailability"],
            "critical_concerns": [],
            "strengths": ["Basic PR structure appears sound"],
            "improvement_areas": ["Complete automated analysis when service is available"],
            "risk_assessment": "medium",
            "analysis_duration": 0.1
        }


# Create orchestrator-focused workflow instance
pr_confidence_orchestration_workflow = PRConfidenceOrchestrationWorkflow()
