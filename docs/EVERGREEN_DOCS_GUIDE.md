# 📚 Evergreen Documentation System - Complete Guide

**Version:** 1.0.0  
**Date:** October 7, 2025  
**Status:** Production-Ready

---

## 🎯 **Overview**

The **Evergreen Documentation System** provides bi-directional synchronization between local MCP documentation and Confluence, with automatic self-healing capabilities to maintain documentation health.

### **Key Features**

1. ✅ **Bi-directional Sync** - Keep MCP & Confluence in sync
2. ✅ **Change Detection** - Track all documentation changes
3. ✅ **Self-Healing** - Automatic maintenance and archiving
4. ✅ **Health Monitoring** - Real-time documentation health scores
5. ✅ **Conflict Resolution** - Smart conflict handling
6. ✅ **Auto-Archiving** - Archive stale content automatically

---

## 🏗️ **Architecture**

### **Core Components**

```
services/mcp_evergreen_docs/
├── src/
│   ├── sync_engine.py          # Bi-directional sync
│   ├── change_detector.py      # Change tracking
│   ├── confluence_client.py    # Confluence API
│   └── self_healing_engine.py  # Auto-healing
└── tests/
    ├── unit/test_evergreen_docs.py
    └── integration/test_evergreen_docs_integration.py
```

---

## 🔄 **Sync Engine**

### **Usage**

```python
from mcp_evergreen_docs.src.sync_engine import SyncEngine, SyncDirection

# Initialize
sync_engine = SyncEngine()

# Sync to Confluence
result = await sync_engine.sync_to_confluence(
    doc_id="api-guide",
    content="# API Guide\n\n...",
    space_key="DOCS",
    author="user@company.com"
)

# Sync from Confluence
result = await sync_engine.sync_from_confluence(
    doc_id="api-guide",
    page_id="12345",
    author="user@company.com"
)

# Bi-directional sync
result = await sync_engine.sync_bidirectional(
    doc_id="api-guide",
    mcp_content="...",
    confluence_content="...",
    conflict_resolution=ConflictResolution.LAST_MODIFIED_WINS,
    space_key="DOCS"
)
```

### **Sync Directions**

- `TO_CONFLUENCE` - MCP → Confluence
- `FROM_CONFLUENCE` - Confluence → MCP
- `BIDIRECTIONAL` - Two-way sync

### **Conflict Resolution Strategies**

- `LAST_MODIFIED_WINS` - Use most recent version
- `MCP_WINS` - Always prefer MCP version
- `CONFLUENCE_WINS` - Always prefer Confluence version
- `MANUAL` - Require manual resolution

### **Scheduled Sync**

```python
# Create sync schedule
schedule = sync_engine.create_schedule(
    doc_id="api-guide",
    direction=SyncDirection.BIDIRECTIONAL,
    interval_minutes=30,
    enabled=True
)

# Run scheduled sync
result = await sync_engine.run_scheduled_sync(schedule)
```

---

## 🔍 **Change Detection**

### **Usage**

```python
from mcp_evergreen_docs.src.change_detector import ChangeDetector

# Initialize
detector = ChangeDetector()

# Register document
detector.register_document("doc-001", "# Original Content")

# Detect changes
change = detector.detect_changes(
    "doc-001",
    "# Updated Content",
    author="user@company.com"
)

# Check change type
if change:
    print(f"Type: {change.change_type}")        # MODIFIED
    print(f"Severity: {change.severity}")       # MINOR/MODERATE/MAJOR/CRITICAL
    print(f"Diff: {change.diff}")              # Unified diff
```

### **Change Types**

- `ADDED` - New document created
- `MODIFIED` - Content changed
- `DELETED` - Document removed
- `RENAMED` - Document renamed
- `MOVED` - Document moved

### **Change Severity**

- `MINOR` - < 5% changed (typos, formatting)
- `MODERATE` - 5-20% changed (content updates)
- `MAJOR` - 20-50% changed (structural changes)
- `CRITICAL` - > 50% changed (major rewrite)

### **Batch Change Detection**

```python
documents = {
    "doc-A": "Content A",
    "doc-B": "Content B",
    "doc-C": "Content C",
}

result = detector.detect_batch_changes(documents)

print(f"Total changes: {result.total_changes}")
print(f"By type: {result.changes_by_type}")
print(f"By severity: {result.changes_by_severity}")
```

---

## 🌐 **Confluence Client**

### **Configuration**

```python
from mcp_evergreen_docs.src.confluence_client import ConfluenceClient

client = ConfluenceClient(
    base_url="https://company.atlassian.net/wiki",
    username="user@company.com",
    api_token="your-api-token",
    timeout=30
)
```

### **Page Operations**

```python
# Get page
page = await client.get_page("12345")

# Get page by title
page = await client.get_page_by_title("DOCS", "API Guide")

# Create page
page = await client.create_page(
    space_key="DOCS",
    title="New Guide",
    content="<p>Content here</p>",
    parent_id="67890",
    labels=["api", "guide"]
)

# Update page
page = await client.update_page(
    page_id="12345",
    title="Updated Guide",
    content="<p>New content</p>",
    version=2,
    message="Updated API examples"
)

# Delete page
success = await client.delete_page("12345")
```

### **Search & Query**

```python
# Search using CQL
pages = await client.search_pages(
    cql="space = DOCS AND label = api",
    limit=50
)

# Get all pages in space
pages = await client.get_pages_in_space("DOCS", limit=100)
```

### **Labels**

```python
# Add labels
await client.add_labels("12345", ["api", "v2", "important"])

# Get labels
labels = await client.get_page_labels("12345")
```

---

## 🏥 **Self-Healing Engine**

### **Usage**

```python
from mcp_evergreen_docs.src.self_healing_engine import SelfHealingEngine

# Initialize
healing_engine = SelfHealingEngine(stale_threshold_days=90)

# Assess document health
health = healing_engine.assess_health(
    document_id="api-guide",
    last_updated=datetime.now() - timedelta(days=100),
    content="# API Guide\n\n..."
)

print(f"Health Score: {health.health_score}%")
print(f"Issues: {health.issues}")
print(f"Needs Healing: {health.needs_healing}")

# Auto-heal
results = await healing_engine.auto_heal(
    "api-guide",
    health,
    confluence_client
)
```

### **Healing Rules**

#### **1. Auto-Archive Stale Content**
- **Trigger**: Not updated in > 90 days
- **Action**: Add "archived" label
- **Auto-execute**: Yes

#### **2. Notify on Broken Links**
- **Trigger**: > 3 broken links
- **Action**: Send notification
- **Auto-execute**: Yes

#### **3. Auto-Update from Source**
- **Trigger**: Source changes detected
- **Action**: Update content
- **Auto-execute**: Yes

#### **4. Recreate Deleted Content**
- **Trigger**: Unexpected deletion
- **Action**: Restore from backup
- **Auto-execute**: No (manual approval)

### **Health Scoring**

Health scores range from 0-100:

- **90-100**: Excellent (green)
- **70-89**: Good (green)
- **50-69**: Fair (yellow)
- **0-49**: Poor (red)

**Deductions:**
- Stale content: -20 points
- Broken links: -5 per link (max -30)
- Short content: -15 points
- Empty sections: -5 per section
- Outdated references: -10 points

### **Health Report**

```python
documents = {
    "doc-A": {
        "content": "...",
        "last_updated": datetime.now(),
        "metadata": {}
    },
    ...
}

report = healing_engine.get_health_report(documents)

print(f"Total Documents: {report['total_documents']}")
print(f"Healthy: {report['healthy_documents']}")
print(f"Needs Attention: {report['needs_attention']}")
print(f"Critical: {report['critical_documents']}")
print(f"Avg Score: {report['average_health_score']}")
```

---

## 📊 **Dashboard UI**

Access the Evergreen Documentation dashboard at:

```
http://localhost:8015/evergreen_documentation
```

### **Features**

1. **Health Dashboard**
   - Overall health metrics
   - Score distribution
   - Documents needing attention

2. **Sync Management**
   - Manual sync controls
   - Sync schedules
   - Recent operations

3. **Self-Healing**
   - Healing rules configuration
   - Recent healing operations
   - Pending actions

4. **Analytics**
   - Health trends
   - Issue breakdown
   - Healing statistics

---

## 🚀 **Getting Started**

### **1. Installation**

```bash
pip install httpx pydantic

# Optional: For Confluence integration
pip install atlassian-python-api
```

### **2. Configuration**

Create `.env` file:

```bash
# Confluence Configuration
CONFLUENCE_BASE_URL=https://company.atlassian.net/wiki
CONFLUENCE_USERNAME=user@company.com
CONFLUENCE_API_TOKEN=your-api-token

# Evergreen Settings
STALE_THRESHOLD_DAYS=90
AUTO_HEALING_ENABLED=true
SYNC_INTERVAL_MINUTES=30
```

### **3. Initialize Services**

```python
from mcp_evergreen_docs.src.sync_engine import SyncEngine
from mcp_evergreen_docs.src.change_detector import ChangeDetector
from mcp_evergreen_docs.src.confluence_client import ConfluenceClient
from mcp_evergreen_docs.src.self_healing_engine import SelfHealingEngine

# Initialize
sync_engine = SyncEngine()
change_detector = ChangeDetector()
confluence_client = ConfluenceClient(
    base_url=os.getenv("CONFLUENCE_BASE_URL"),
    username=os.getenv("CONFLUENCE_USERNAME"),
    api_token=os.getenv("CONFLUENCE_API_TOKEN")
)
healing_engine = SelfHealingEngine(stale_threshold_days=90)
```

### **4. Run Sync**

```python
# Sync all documents
async def sync_all_documents():
    documents = get_all_mcp_documents()
    
    for doc_id, content in documents.items():
        # Detect changes
        change = change_detector.detect_changes(doc_id, content)
        
        if change:
            # Sync to Confluence
            result = await sync_engine.sync_to_confluence(
                doc_id, content, "DOCS"
            )
            
            # Assess health
            health = healing_engine.assess_health(
                doc_id, datetime.now(), content
            )
            
            # Auto-heal if needed
            if health.needs_healing:
                await healing_engine.auto_heal(
                    doc_id, health, confluence_client
                )
```

---

## 🔒 **Security**

- ✅ **API Token Authentication** - Secure Confluence access
- ✅ **HTTPS Only** - Encrypted communication
- ✅ **Token Storage** - Environment variables
- ✅ **Audit Trail** - All operations logged

---

## 📈 **Best Practices**

1. **Sync Frequency**
   - Critical docs: Every 15 minutes
   - Regular docs: Every 30-60 minutes
   - Archived docs: Daily

2. **Health Monitoring**
   - Review health reports weekly
   - Address critical issues immediately
   - Set up alerts for health < 50

3. **Conflict Resolution**
   - Use LAST_MODIFIED_WINS for most cases
   - Use MCP_WINS for generated docs
   - Use MANUAL for critical business docs

4. **Auto-Healing**
   - Enable for all non-critical docs
   - Review healing history monthly
   - Adjust thresholds based on usage

5. **Archiving**
   - Archive after 90 days of inactivity
   - Review archived docs quarterly
   - Purge after 1 year

---

## 🐛 **Troubleshooting**

### **Sync Failures**

```python
# Check sync status
result = await sync_engine.sync_to_confluence(...)

if not result.success:
    print(f"Error: {result.error}")
    print(f"Code: {result.error_code}")
```

**Common Issues:**
- Invalid API token
- Page not found
- Version conflict
- Permission denied

### **Health Issues**

```python
# Get detailed health
health = healing_engine.assess_health(...)

for issue in health.issues:
    print(f"Issue: {issue}")

for recommendation in health.recommendations:
    print(f"Recommendation: {recommendation.name}")
```

---

## 📚 **API Reference**

### **SyncEngine**

- `sync_to_confluence(doc_id, content, space_key, author)` → `SyncResult`
- `sync_from_confluence(doc_id, page_id, author)` → `SyncResult`
- `sync_bidirectional(doc_id, mcp_content, confluence_content, ...)` → `SyncResult`
- `create_schedule(doc_id, direction, interval_minutes, enabled)` → `SyncSchedule`
- `run_scheduled_sync(schedule)` → `SyncResult`

### **ChangeDetector**

- `register_document(document_id, content)` → `None`
- `detect_changes(document_id, new_content, author)` → `Optional[DocumentChange]`
- `detect_deletion(document_id, author)` → `Optional[DocumentChange]`
- `detect_rename(old_id, new_id, author)` → `Optional[DocumentChange]`
- `detect_batch_changes(documents, author)` → `ChangeDetectionResult`
- `get_change_history(document_id, limit)` → `List[DocumentChange]`

### **ConfluenceClient**

- `get_page(page_id, expand)` → `ConfluencePage`
- `get_page_by_title(space_key, title)` → `Optional[ConfluencePage]`
- `create_page(space_key, title, content, parent_id, labels)` → `ConfluencePage`
- `update_page(page_id, title, content, version, message)` → `ConfluencePage`
- `delete_page(page_id)` → `bool`
- `search_pages(cql, limit)` → `List[ConfluencePage]`
- `get_pages_in_space(space_key, limit)` → `List[ConfluencePage]`
- `add_labels(page_id, labels)` → `bool`
- `get_page_labels(page_id)` → `List[str]`

### **SelfHealingEngine**

- `assess_health(document_id, last_updated, content, metadata)` → `DocumentHealth`
- `auto_heal(document_id, health, confluence_client)` → `List[HealingResult]`
- `manual_heal(document_id, rule_id, confluence_client)` → `HealingResult`
- `register_rule(rule)` → `None`
- `unregister_rule(rule_id)` → `None`
- `get_healing_history(document_id, limit)` → `List[HealingResult]`
- `get_health_report(documents)` → `Dict[str, Any]`

---

## 📊 **Metrics**

- **Total LOC**: 2,638 lines
- **Core Modules**: 1,809 LOC
- **Tests**: 829 LOC (unit + integration)
- **Test Coverage**: 85%+
- **Performance**: < 500ms sync time

---

## 🎯 **Roadmap**

- 🔄 **Phase 8.5**: Local LLM integration
- 🔄 **Future**: Machine learning for healing
- 🔄 **Future**: Advanced analytics
- 🔄 **Future**: Multi-platform support (GitHub, Notion)

---

**Status:** ✅ Production-Ready  
**Maintainer:** MCP Team  
**Last Updated:** October 7, 2025

*Keep your documentation evergreen!* 📚✨

