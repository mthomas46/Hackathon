"""
Human-in-the-Loop (HITL) Workflows UI Page.

Provides interface for:
- Approval queue management
- Request review
- Statistics & monitoring
- Workflow configuration
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import random

# Add services directory to path
services_path = Path(__file__).parent.parent.parent / "services"
sys.path.insert(0, str(services_path))

from mcp_retrieval.src.hitl_workflows import (
    HITLWorkflow,
    ApprovalQueue,
    ApprovalStatus,
    DecisionType,
    ReviewAction,
    create_approval_request,
)


# ============================================================================
# Page Configuration
# ============================================================================

def render():
    """Render the HITL Workflows page."""
    
    st.title("👥 Human-in-the-Loop Workflows")
    st.markdown("""
    Manage approval workflows for high-stakes decisions, low-confidence predictions, and manual reviews.
    """)
    
    # Initialize session state
    if 'hitl_workflow' not in st.session_state:
        st.session_state['hitl_workflow'] = HITLWorkflow(
            confidence_threshold=0.8,
            auto_approve_low_risk=True
        )
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        render_configuration()
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Queue", "✅ Review", "📊 Statistics", "ℹ️ About"])
    
    with tab1:
        render_approval_queue()
    
    with tab2:
        render_review_interface()
    
    with tab3:
        render_statistics()
    
    with tab4:
        render_about()


# ============================================================================
# Configuration Section
# ============================================================================

def render_configuration():
    """Render configuration sidebar."""
    
    st.subheader("🎯 Workflow Settings")
    
    # Confidence threshold
    threshold = st.slider(
        "Confidence Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.8,
        step=0.05,
        help="Minimum confidence for auto-approval"
    )
    
    # Auto-approve toggle
    auto_approve = st.checkbox(
        "Auto-approve low-risk",
        value=True,
        help="Automatically approve high-confidence, low-risk decisions"
    )
    
    # Apply settings
    if st.button("Apply Settings", use_container_width=True):
        st.session_state['hitl_workflow'] = HITLWorkflow(
            confidence_threshold=threshold,
            auto_approve_low_risk=auto_approve
        )
        st.success("Settings applied!")
        st.rerun()
    
    # Queue statistics
    st.subheader("📊 Quick Stats")
    stats = st.session_state['hitl_workflow'].approval_queue.get_statistics()
    
    st.metric("Total Requests", stats["total_requests"])
    st.metric("Pending", stats["pending"])
    st.metric("Approved", stats["approved"])
    st.metric("Rejected", stats["rejected"])


# ============================================================================
# Approval Queue Section
# ============================================================================

def render_approval_queue():
    """Render approval queue interface."""
    
    st.header("📋 Approval Queue")
    
    queue = st.session_state['hitl_workflow'].approval_queue
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("➕ Add Sample Request", use_container_width=True):
            add_sample_request()
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear Completed", use_container_width=True):
            clear_completed_requests()
            st.success("Cleared completed requests")
            st.rerun()
    
    # Filter options
    st.subheader("🔍 Filters")
    col1, col2 = st.columns(2)
    
    with col1:
        status_filter = st.selectbox(
            "Status",
            options=["All", "Pending", "Approved", "Rejected", "Cancelled"],
            index=1  # Default to Pending
        )
    
    with col2:
        type_filter = st.selectbox(
            "Decision Type",
            options=["All", "High Stakes", "Confidence Threshold", "Policy Violation", "Manual Review"]
        )
    
    # Get and filter requests
    if status_filter == "All":
        requests = list(queue._requests.values())
    else:
        status_map = {
            "Pending": ApprovalStatus.PENDING,
            "Approved": ApprovalStatus.APPROVED,
            "Rejected": ApprovalStatus.REJECTED,
            "Cancelled": ApprovalStatus.CANCELLED,
        }
        requests = queue.filter_requests(status=status_map.get(status_filter))
    
    # Display requests
    if requests:
        display_requests(requests)
    else:
        st.info("No requests found. Add sample requests to get started.")


def display_requests(requests):
    """Display list of requests."""
    
    st.subheader(f"📝 Requests ({len(requests)})")
    
    for request in requests:
        with st.expander(
            f"{get_status_icon(request.status)} {request.request_id} - {request.decision_type.value.replace('_', ' ').title()}",
            expanded=(request.status == ApprovalStatus.PENDING)
        ):
            # Request details
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Status:** {request.status.value.upper()}")
                st.markdown(f"**Type:** {request.decision_type.value.replace('_', ' ').title()}")
                st.markdown(f"**Created:** {request.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            with col2:
                priority = request.metadata.get("priority", "medium")
                st.markdown(f"**Priority:** {priority.upper()}")
                
                if request.reviewer:
                    st.markdown(f"**Reviewer:** {request.reviewer}")
                
                if request.reviewed_at:
                    st.markdown(f"**Reviewed:** {request.reviewed_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Content
            st.markdown("**Content:**")
            st.json(request.content)
            
            # Review comment
            if request.review_comment:
                st.info(f"💬 **Comment:** {request.review_comment}")
            
            # Actions for pending requests
            if request.status == ApprovalStatus.PENDING:
                st.divider()
                render_quick_actions(request)


def render_quick_actions(request):
    """Render quick action buttons for a request."""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Approve", key=f"approve_{request.request_id}", use_container_width=True):
            queue = st.session_state['hitl_workflow'].approval_queue
            queue.review_request(
                request_id=request.request_id,
                action=ReviewAction.APPROVE,
                reviewer="dashboard_user",
                comment="Approved via dashboard"
            )
            st.success("Request approved!")
            st.rerun()
    
    with col2:
        if st.button("❌ Reject", key=f"reject_{request.request_id}", use_container_width=True):
            queue = st.session_state['hitl_workflow'].approval_queue
            queue.review_request(
                request_id=request.request_id,
                action=ReviewAction.REJECT,
                reviewer="dashboard_user",
                comment="Rejected via dashboard"
            )
            st.warning("Request rejected!")
            st.rerun()
    
    with col3:
        if st.button("🚫 Cancel", key=f"cancel_{request.request_id}", use_container_width=True):
            queue = st.session_state['hitl_workflow'].approval_queue
            queue.cancel_request(request.request_id)
            st.info("Request cancelled!")
            st.rerun()


def get_status_icon(status):
    """Get icon for status."""
    icons = {
        ApprovalStatus.PENDING: "⏳",
        ApprovalStatus.APPROVED: "✅",
        ApprovalStatus.REJECTED: "❌",
        ApprovalStatus.CANCELLED: "🚫",
    }
    return icons.get(status, "❓")


def add_sample_request():
    """Add a sample approval request."""
    workflow = st.session_state['hitl_workflow']
    
    # Random decision type
    decision_types = [
        DecisionType.HIGH_STAKES,
        DecisionType.CONFIDENCE_THRESHOLD,
        DecisionType.POLICY_VIOLATION,
    ]
    decision_type = random.choice(decision_types)
    
    # Sample content
    sample_contents = [
        {"action": "delete_user_data", "user_id": f"user_{random.randint(1000, 9999)}"},
        {"action": "update_permissions", "role": "admin", "user": f"user_{random.randint(1000, 9999)}"},
        {"action": "process_payment", "amount": random.randint(100, 10000)},
        {"action": "deploy_model", "model_id": f"model_v{random.randint(1, 10)}"},
    ]
    content = random.choice(sample_contents)
    
    # Submit
    workflow.submit_for_approval(
        decision_type=decision_type,
        content=content,
        confidence=random.uniform(0.5, 0.95),
        metadata={"priority": random.choice(["low", "medium", "high", "critical"])}
    )


def clear_completed_requests():
    """Clear completed (approved/rejected) requests."""
    queue = st.session_state['hitl_workflow'].approval_queue
    
    # Get completed request IDs
    completed_ids = [
        req.request_id
        for req in queue._requests.values()
        if req.status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]
    ]
    
    # Remove from queue
    for req_id in completed_ids:
        del queue._requests[req_id]


# ============================================================================
# Review Interface Section
# ============================================================================

def render_review_interface():
    """Render detailed review interface."""
    
    st.header("✅ Review Requests")
    
    queue = st.session_state['hitl_workflow'].approval_queue
    pending = queue.get_pending_requests(sort_by="priority")
    
    if not pending:
        st.info("No pending requests to review.")
        return
    
    # Select request
    request_options = {
        f"{req.request_id} - {req.decision_type.value} (Priority: {req.metadata.get('priority', 'medium')})": req
        for req in pending
    }
    
    selected_label = st.selectbox(
        "Select Request",
        options=list(request_options.keys())
    )
    
    if selected_label:
        request = request_options[selected_label]
        
        # Display request details
        st.subheader("📄 Request Details")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Request ID", request.request_id)
            st.metric("Type", request.decision_type.value.replace('_', ' ').title())
        
        with col2:
            st.metric("Priority", request.metadata.get("priority", "medium").upper())
            age = datetime.now() - request.created_at
            st.metric("Age", f"{age.seconds // 60} minutes")
        
        with col3:
            confidence = request.metadata.get("confidence")
            if confidence:
                st.metric("Confidence", f"{confidence:.2%}")
        
        # Content
        st.markdown("**Content:**")
        st.json(request.content)
        
        # Audit trail
        with st.expander("📜 Audit Trail"):
            for entry in request.audit_trail:
                st.markdown(f"- **{entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}**: {entry['action']}")
        
        # Review form
        st.divider()
        st.subheader("✍️ Review")
        
        col1, col2 = st.columns(2)
        
        with col1:
            action = st.selectbox(
                "Action",
                options=["Approve", "Reject", "Request Changes", "Escalate"]
            )
        
        with col2:
            reviewer = st.text_input(
                "Reviewer ID",
                value="dashboard_user",
                help="Your identifier"
            )
        
        comment = st.text_area(
            "Comment",
            placeholder="Optional review comment...",
            height=100
        )
        
        # Submit review
        if st.button("📝 Submit Review", type="primary", use_container_width=True):
            action_map = {
                "Approve": ReviewAction.APPROVE,
                "Reject": ReviewAction.REJECT,
                "Request Changes": ReviewAction.REQUEST_CHANGES,
                "Escalate": ReviewAction.ESCALATE,
            }
            
            queue.review_request(
                request_id=request.request_id,
                action=action_map[action],
                reviewer=reviewer,
                comment=comment or None
            )
            
            st.success(f"✅ Review submitted: {action}")
            st.rerun()


# ============================================================================
# Statistics Section
# ============================================================================

def render_statistics():
    """Render statistics dashboard."""
    
    st.header("📊 Statistics & Analytics")
    
    queue = st.session_state['hitl_workflow'].approval_queue
    stats = queue.get_statistics()
    
    # Overall metrics
    st.subheader("📈 Overall Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", stats["total_requests"])
    with col2:
        st.metric("Pending", stats["pending"])
    with col3:
        st.metric("Approved", stats["approved"])
    with col4:
        st.metric("Rejected", stats["rejected"])
    
    # Status distribution
    st.subheader("📊 Status Distribution")
    
    status_data = {
        "Status": ["Pending", "Approved", "Rejected", "Cancelled"],
        "Count": [
            stats["pending"],
            stats["approved"],
            stats["rejected"],
            stats["cancelled"]
        ]
    }
    
    fig_status = px.pie(
        status_data,
        values="Count",
        names="Status",
        title="Request Status Distribution"
    )
    st.plotly_chart(fig_status, use_container_width=True)
    
    # Decision type breakdown
    st.subheader("📋 Decision Types")
    
    type_counts = {}
    for request in queue._requests.values():
        type_name = request.decision_type.value
        type_counts[type_name] = type_counts.get(type_name, 0) + 1
    
    if type_counts:
        fig_types = px.bar(
            x=list(type_counts.keys()),
            y=list(type_counts.values()),
            title="Requests by Decision Type",
            labels={"x": "Decision Type", "y": "Count"}
        )
        st.plotly_chart(fig_types, use_container_width=True)
    
    # Priority distribution
    st.subheader("⭐ Priority Distribution")
    
    priority_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for request in queue._requests.values():
        priority = request.metadata.get("priority", "medium")
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Critical", priority_counts["critical"])
    with col2:
        st.metric("High", priority_counts["high"])
    with col3:
        st.metric("Medium", priority_counts["medium"])
    with col4:
        st.metric("Low", priority_counts["low"])


# ============================================================================
# About Section
# ============================================================================

def render_about():
    """Render about/help section."""
    
    st.header("ℹ️ About HITL Workflows")
    
    st.markdown("""
    ## Overview
    
    Human-in-the-Loop (HITL) Workflows enable human review and approval for:
    - **High-stakes decisions** - Critical operations requiring oversight
    - **Low-confidence predictions** - Below confidence threshold
    - **Policy violations** - Potential policy compliance issues
    - **Manual review requests** - Explicitly requested reviews
    
    ## Features
    
    ### Approval Queue
    - ✅ Add/manage approval requests
    - ✅ Filter by status and type
    - ✅ Priority-based sorting
    - ✅ Quick actions (approve/reject/cancel)
    
    ### Review Interface
    - ✅ Detailed request information
    - ✅ Audit trail tracking
    - ✅ Review comments
    - ✅ Multiple actions (approve/reject/escalate)
    
    ### Statistics
    - ✅ Real-time metrics
    - ✅ Status distribution
    - ✅ Decision type breakdown
    - ✅ Priority tracking
    
    ## Workflow Configuration
    
    **Confidence Threshold** (default: 0.8)
    - Decisions above threshold can be auto-approved
    - Decisions below threshold require manual review
    
    **Auto-approve Low-risk** (default: enabled)
    - High-confidence, low-risk decisions auto-approved
    - Reduces review burden
    
    ## Decision Types
    
    | Type | Description | Auto-approve? |
    |------|-------------|---------------|
    | **High Stakes** | Critical operations | Never |
    | **Confidence Threshold** | Below confidence limit | Conditional |
    | **Policy Violation** | Potential policy issues | Never |
    | **Manual Review** | Explicitly requested | Never |
    
    ## Review Actions
    
    - **Approve** - Accept and proceed
    - **Reject** - Deny request
    - **Request Changes** - Ask for modifications
    - **Escalate** - Forward to higher authority
    
    ## Best Practices
    
    ✅ Review pending requests regularly  
    ✅ Provide clear review comments  
    ✅ Set appropriate confidence thresholds  
    ✅ Monitor statistics for bottlenecks  
    ✅ Clear completed requests periodically  
    
    ## Use Cases
    
    - **Data Deletion** - GDPR/privacy requests
    - **Permission Changes** - Role/access updates
    - **Financial Operations** - Payments, refunds
    - **Model Deployment** - Production releases
    - **Configuration Changes** - System settings
    """)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    render()

