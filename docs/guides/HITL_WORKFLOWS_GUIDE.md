# 👥 **Human-in-the-Loop Workflows Guide**

## **Complete Guide to HITL Approval System**

---

## **Table of Contents**

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [API Reference](#api-reference)
5. [Workflow Types](#workflow-types)
6. [Usage Examples](#usage-examples)
7. [UI Guide](#ui-guide)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## **Overview**

Human-in-the-Loop (HITL) Workflows enable human review and approval for critical decisions, low-confidence predictions, and policy-sensitive operations.

### **Key Features**

✅ **Approval Queue** - Centralized request management  
✅ **Multiple Decision Types** - High-stakes, confidence-based, policy, manual  
✅ **Review Workflow** - Approve, reject, escalate, request changes  
✅ **Audit Trail** - Complete history tracking  
✅ **Auto-approval** - Smart automatic approval for low-risk decisions  
✅ **Priority Management** - Priority-based queue sorting  

### **Use Cases**

- **Data Operations** - User data deletion, GDPR requests
- **Permission Management** - Role changes, access control
- **Financial Operations** - Payments, refunds, transactions
- **Model Deployment** - Production releases, A/B tests
- **Configuration Changes** - System settings, feature flags

---

## **Architecture**

### **Components**

```
Decision → Approval Check → Queue/Auto-approve → Human Review → Action
```

### **Key Classes**

| Class | Purpose | Key Methods |
|-------|---------|-------------|
| **HITLWorkflow** | Main orchestrator | requires_approval(), process_decision() |
| **ApprovalQueue** | Queue management | add_request(), review_request() |
| **ApprovalRequest** | Request model | Dataclass with audit trail |

---

## **Quick Start**

### **Basic Setup**

```python
from mcp_retrieval.src.hitl_workflows import (
    HITLWorkflow,
    DecisionType,
)

# Initialize workflow
workflow = HITLWorkflow(
    confidence_threshold=0.8,  # 80% confidence minimum
    auto_approve_low_risk=True  # Enable auto-approval
)
```

### **Submit for Approval**

```python
# Submit high-stakes decision
request = workflow.submit_for_approval(
    decision_type=DecisionType.HIGH_STAKES,
    content={"action": "delete_user_data", "user_id": "user_123"},
    metadata={"priority": "high"}
)

print(f"Request ID: {request.request_id}")
print(f"Status: {request.status}")
```

### **Check Approval Status**

```python
# Get request
request = workflow.approval_queue.get_request(request.request_id)

if request.status == ApprovalStatus.APPROVED:
    # Proceed with action
    perform_action(request.content)
elif request.status == ApprovalStatus.REJECTED:
    # Handle rejection
    log_rejection(request)
```

---

## **API Reference**

### **HITLWorkflow**

Main workflow orchestrator.

#### **Constructor**

```python
HITLWorkflow(
    confidence_threshold: float = 0.8,
    auto_approve_low_risk: bool = True
)
```

**Parameters:**
- `confidence_threshold` - Minimum confidence for auto-approval (0-1)
- `auto_approve_low_risk` - Enable automatic approval for low-risk decisions

#### **Methods**

##### **requires_approval()**

```python
requires_approval(
    decision_type: DecisionType,
    confidence: float,
    content: Dict[str, Any]
) -> bool
```

Check if a decision requires human approval.

**Returns:** `True` if approval needed, `False` otherwise

**Example:**
```python
needs_approval = workflow.requires_approval(
    decision_type=DecisionType.HIGH_STAKES,
    confidence=0.95,
    content={"action": "delete_data"}
)
# Returns: True (high-stakes always need approval)
```

##### **submit_for_approval()**

```python
submit_for_approval(
    decision_type: DecisionType,
    content: Dict[str, Any],
    confidence: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ApprovalRequest
```

Submit a decision for approval.

**Returns:** `ApprovalRequest` instance

##### **process_decision()**

```python
process_decision(
    decision_type: DecisionType,
    content: Dict[str, Any],
    confidence: float = 1.0,
    wait_for_approval: bool = False,
    timeout_seconds: float = 30.0
) -> Dict[str, Any]
```

Process a decision with automatic approval handling.

**Returns:** Dictionary with processing result

### **ApprovalQueue**

Queue management for approval requests.

#### **Methods**

##### **create_request()**

```python
create_request(
    decision_type: DecisionType,
    content: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> ApprovalRequest
```

Create a new approval request.

##### **review_request()**

```python
review_request(
    request_id: str,
    action: ReviewAction,
    reviewer: str,
    comment: Optional[str] = None
) -> bool
```

Review and approve/reject a request.

**Actions:**
- `ReviewAction.APPROVE` - Approve request
- `ReviewAction.REJECT` - Reject request
- `ReviewAction.REQUEST_CHANGES` - Ask for changes
- `ReviewAction.ESCALATE` - Escalate to higher authority

##### **get_pending_requests()**

```python
get_pending_requests(
    sort_by: Optional[str] = None
) -> List[ApprovalRequest]
```

Get all pending requests, optionally sorted.

**Sort Options:**
- `"priority"` - Sort by priority (critical → low)
- `"created_at"` - Sort by creation time

### **ApprovalRequest**

Request data model.

```python
@dataclass
class ApprovalRequest:
    request_id: str
    decision_type: DecisionType
    content: Dict[str, Any]
    status: ApprovalStatus
    created_at: datetime
    reviewed_at: Optional[datetime]
    reviewer: Optional[str]
    review_comment: Optional[str]
    metadata: Dict[str, Any]
    audit_trail: List[Dict[str, Any]]
```

---

## **Workflow Types**

### **1. High-Stakes Decisions**

**Description:** Critical operations requiring mandatory review.

**Characteristics:**
- Always require approval
- Cannot be auto-approved
- Highest priority

**Examples:**
```python
# Data deletion
workflow.submit_for_approval(
    decision_type=DecisionType.HIGH_STAKES,
    content={"action": "delete_user_data", "user_id": "user_123"}
)

# Permission changes
workflow.submit_for_approval(
    decision_type=DecisionType.HIGH_STAKES,
    content={"action": "grant_admin_role", "user_id": "user_456"}
)
```

### **2. Confidence Threshold**

**Description:** Decisions with confidence below threshold.

**Characteristics:**
- Auto-approved if confidence > threshold
- Requires review if confidence < threshold
- Conditional approval

**Examples:**
```python
# High confidence - auto-approved
workflow.process_decision(
    decision_type=DecisionType.CONFIDENCE_THRESHOLD,
    content={"action": "classify_document"},
    confidence=0.95  # Above 0.8 threshold
)

# Low confidence - requires review
workflow.process_decision(
    decision_type=DecisionType.CONFIDENCE_THRESHOLD,
    content={"action": "classify_document"},
    confidence=0.60  # Below 0.8 threshold
)
```

### **3. Policy Violation**

**Description:** Potential policy compliance issues.

**Characteristics:**
- Always require approval
- Flagged for policy review
- Documentation required

**Examples:**
```python
# Suspicious transaction
workflow.submit_for_approval(
    decision_type=DecisionType.POLICY_VIOLATION,
    content={
        "action": "process_payment",
        "amount": 50000,
        "flag": "unusual_amount"
    }
)
```

### **4. Manual Review**

**Description:** Explicitly requested human review.

**Characteristics:**
- Always require approval
- User/system requested
- Custom review criteria

**Examples:**
```python
# Requested review
workflow.submit_for_approval(
    decision_type=DecisionType.MANUAL_REVIEW,
    content={"action": "custom_operation"},
    metadata={"requested_by": "user_789"}
)
```

---

## **Usage Examples**

### **Example 1: Complete Approval Workflow**

```python
from mcp_retrieval.src.hitl_workflows import *

# Initialize
workflow = HITLWorkflow(confidence_threshold=0.8)

# Submit decision
request = workflow.submit_for_approval(
    decision_type=DecisionType.HIGH_STAKES,
    content={"action": "delete_account", "account_id": "acc_123"},
    metadata={"priority": "high"}
)

print(f"Submitted: {request.request_id}")

# Wait for approval (in production, this would be async)
result = workflow.wait_for_approval(
    request_id=request.request_id,
    timeout_seconds=300  # 5 minutes
)

if result and result.status == ApprovalStatus.APPROVED:
    print(f"Approved by: {result.reviewer}")
    # Proceed with action
    delete_account("acc_123")
else:
    print("Not approved or timeout")
    # Handle rejection
```

### **Example 2: Auto-Approval Flow**

```python
# High-confidence decision
result = workflow.process_decision(
    decision_type=DecisionType.CONFIDENCE_THRESHOLD,
    content={"action": "categorize_email", "email_id": "email_456"},
    confidence=0.92,  # High confidence
    wait_for_approval=False
)

if result["auto_approved"]:
    print("Auto-approved! Proceeding...")
    categorize_email("email_456")
else:
    print(f"Requires approval: {result['request_id']}")
```

### **Example 3: Manual Review Process**

```python
# Get pending requests
pending = workflow.approval_queue.get_pending_requests(sort_by="priority")

for request in pending:
    print(f"\nReview: {request.request_id}")
    print(f"Type: {request.decision_type.value}")
    print(f"Content: {request.content}")
    print(f"Priority: {request.metadata.get('priority')}")
    
    # Human decides
    decision = input("Approve? (y/n): ")
    
    if decision.lower() == 'y':
        workflow.approval_queue.review_request(
            request_id=request.request_id,
            action=ReviewAction.APPROVE,
            reviewer="admin@company.com",
            comment="Approved after review"
        )
    else:
        workflow.approval_queue.review_request(
            request_id=request.request_id,
            action=ReviewAction.REJECT,
            reviewer="admin@company.com",
            comment="Insufficient justification"
        )
```

### **Example 4: Batch Processing with HITL**

```python
# Process multiple decisions
decisions = [
    {"action": "update_profile", "user_id": "u1", "confidence": 0.95},
    {"action": "delete_post", "post_id": "p1", "confidence": 0.65},
    {"action": "ban_user", "user_id": "u2", "confidence": 0.85},
]

for decision in decisions:
    result = workflow.process_decision(
        decision_type=DecisionType.CONFIDENCE_THRESHOLD,
        content=decision,
        confidence=decision["confidence"],
        wait_for_approval=False
    )
    
    if result["auto_approved"]:
        print(f"✅ Auto-approved: {decision['action']}")
    else:
        print(f"⏳ Queued for review: {result['request_id']}")
```

### **Example 5: Priority-Based Processing**

```python
# Add requests with different priorities
workflow.submit_for_approval(
    decision_type=DecisionType.HIGH_STAKES,
    content={"action": "op1"},
    metadata={"priority": "critical"}
)

workflow.submit_for_approval(
    decision_type=DecisionType.HIGH_STAKES,
    content={"action": "op2"},
    metadata={"priority": "low"}
)

# Get requests sorted by priority
pending = workflow.approval_queue.get_pending_requests(sort_by="priority")

# Process highest priority first
for request in pending:
    priority = request.metadata.get("priority")
    print(f"Processing {priority} priority: {request.request_id}")
```

---

## **UI Guide**

### **Accessing the UI**

Navigate to **HITL Workflows** page in the MCP Dashboard.

### **Configuration Sidebar**

1. **Confidence Threshold** - Set minimum confidence (0-1)
2. **Auto-approve** - Toggle automatic approval
3. **Quick Stats** - View current queue metrics

### **Queue Tab**

- **Filters** - Filter by status and decision type
- **Request List** - View all requests
- **Quick Actions** - Approve/reject/cancel buttons
- **Details** - Expand for full request information

### **Review Tab**

- **Request Selector** - Choose request to review
- **Details View** - See request information
- **Audit Trail** - View request history
- **Review Form** - Submit review with comment

### **Statistics Tab**

- **Metrics** - Total, pending, approved, rejected
- **Charts** - Status and type distributions
- **Priority** - Priority breakdown

---

## **Best Practices**

### **1. Set Appropriate Thresholds**

```python
# For high-risk domains (financial, healthcare)
workflow = HITLWorkflow(confidence_threshold=0.95)

# For low-risk domains (content categorization)
workflow = HITLWorkflow(confidence_threshold=0.75)
```

### **2. Use Priority Levels**

```python
# Critical operations
metadata={"priority": "critical"}

# Routine operations
metadata={"priority": "low"}
```

### **3. Provide Clear Context**

```python
# Good: Detailed content
content={
    "action": "delete_user",
    "user_id": "user_123",
    "reason": "GDPR request",
    "request_date": "2025-10-07",
    "requester": "user_123"
}

# Bad: Minimal content
content={"action": "delete", "id": "123"}
```

### **4. Monitor Queue Depth**

```python
stats = workflow.approval_queue.get_statistics()

if stats["pending"] > 100:
    logger.warning("High queue depth, consider auto-approving more")
```

### **5. Regular Queue Cleanup**

```python
# Periodically clear old completed requests
completed = workflow.approval_queue.filter_requests(
    status=ApprovalStatus.APPROVED
)

for request in completed:
    if (datetime.now() - request.reviewed_at).days > 30:
        del workflow.approval_queue._requests[request.request_id]
```

---

## **Troubleshooting**

### **Problem: Queue Backing Up**

**Symptoms:** Many pending requests, long wait times.

**Solutions:**
1. Lower confidence threshold for auto-approval
2. Enable auto-approve for more decision types
3. Add more reviewers
4. Increase review frequency

### **Problem: Too Many Auto-Approvals**

**Symptoms:** High-risk decisions being auto-approved.

**Solutions:**
1. Raise confidence threshold
2. Classify more operations as HIGH_STAKES
3. Disable auto_approve_low_risk
4. Add manual review checkpoints

### **Problem: Requests Timing Out**

**Symptoms:** wait_for_approval() timing out.

**Solutions:**
1. Increase timeout_seconds
2. Use asynchronous callbacks instead
3. Implement notification system
4. Don't wait synchronously in production

---

## **Integration Examples**

### **With FastAPI**

```python
from fastapi import FastAPI, HTTPException
from mcp_retrieval.src.hitl_workflows import *

app = FastAPI()
workflow = HITLWorkflow()

@app.post("/api/decisions")
async def submit_decision(
    decision_type: str,
    content: dict,
    confidence: float = 1.0
):
    result = workflow.process_decision(
        decision_type=DecisionType(decision_type),
        content=content,
        confidence=confidence,
        wait_for_approval=False
    )
    
    return result

@app.get("/api/approvals/pending")
async def get_pending():
    pending = workflow.approval_queue.get_pending_requests()
    return [
        {
            "id": r.request_id,
            "type": r.decision_type.value,
            "created": r.created_at.isoformat()
        }
        for r in pending
    ]
```

---

## **Resources**

- **Source Code:** `services/mcp_retrieval/src/hitl_workflows.py`
- **Unit Tests:** `tests/unit/test_hitl_workflows.py`
- **UI Page:** `dashboard/pages/hitl_workflows.py`

---

**For support or questions, refer to the MCP documentation or contact the development team.**

---

**Happy Reviewing! 👥**
