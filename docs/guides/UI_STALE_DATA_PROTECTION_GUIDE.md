# UI Stale Data Protection Guide

**Purpose:** Document how to implement stale data warnings in the Streamlit dashboard.

**Status:** Implementation guide provided, ready to add to dashboard.

---

## 🎯 **The Problem**

Users may be viewing stale data without knowing it:
- Network issues prevent updates
- Backend is slow/unresponsive
- Auto-refresh is disabled
- Long-running processes

**Result:** User makes decisions based on old data

---

## ✅ **Solution**

Add timestamp tracking and visual warnings:
1. Track `last_updated` timestamp
2. Calculate data age on each render
3. Show warning if data >60 seconds old
4. Provide refresh button
5. Use color coding (green/yellow/red)

---

## 🏗️ **Implementation**

### **1. Add Timestamp Tracking**

**Location:** `dashboard_views/ingestion_manager.py`

```python
import streamlit as st
from datetime import datetime, timedelta

# At top of show() function
def show():
    """Display ingestion manager UI."""
    
    # Initialize session state for timestamps
    if 'last_data_fetch' not in st.session_state:
        st.session_state.last_data_fetch = {}
    
    # Track when data was last fetched
    current_time = datetime.now()
    
    # Your existing code...
```

### **2. Update Timestamp on Data Fetch**

```python
# When fetching job status
response = httpx.get(f"{API_URL}/api/v1/admin/ingest/{job_id}/status")
if response.status_code == 200:
    job_data = response.json()
    
    # Update timestamp
    st.session_state.last_data_fetch[job_id] = datetime.now()
    
    # Display data
    display_job_status(job_data)
```

### **3. Calculate Data Age**

```python
def get_data_age_seconds(job_id: str) -> float:
    """Calculate how old the data is."""
    if job_id not in st.session_state.last_data_fetch:
        return 0
    
    last_fetch = st.session_state.last_data_fetch[job_id]
    age = (datetime.now() - last_fetch).total_seconds()
    return age

def get_freshness_status(age_seconds: float) -> tuple[str, str]:
    """Get freshness status and color."""
    if age_seconds < 30:
        return ("🟢 Fresh", "green")
    elif age_seconds < 60:
        return ("🟡 Recent", "yellow")
    else:
        return ("🔴 Stale", "red")
```

### **4. Display Warning Banner**

```python
def show_data_freshness_warning(job_id: str):
    """Show warning if data is stale."""
    age_seconds = get_data_age_seconds(job_id)
    status, color = get_freshness_status(age_seconds)
    
    if age_seconds > 60:
        st.warning(
            f"⚠️  **Stale Data Warning**\\n\\n"
            f"This data is {int(age_seconds)} seconds old. "
            f"Click 'Refresh' for latest information.",
            icon="⚠️"
        )
    
    # Show freshness indicator
    st.caption(f"{status} - Last updated: {int(age_seconds)}s ago")
```

### **5. Add Freshness Indicator**

```python
# Compact version for each data section
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Job Status")

with col2:
    age = get_data_age_seconds(job_id)
    status, color = get_freshness_status(age)
    st.markdown(
        f"<p style='text-align: right; color: {color}; margin: 0;'>"
        f"{status} ({int(age)}s ago)</p>",
        unsafe_allow_html=True
    )
```

---

## 📊 **Visual Examples**

### **Example 1: Fresh Data (<30s)**

```
🟢 Fresh - Last updated: 5s ago

Job Status: Processing
Files: 250/1000
Progress: 25%
```

### **Example 2: Recent Data (30-60s)**

```
🟡 Recent - Last updated: 45s ago

Job Status: Processing
Files: 250/1000
Progress: 25%

💡 Consider refreshing for latest progress
```

### **Example 3: Stale Data (>60s)**

```
⚠️  Stale Data Warning

This data is 125 seconds old. Click 'Refresh' for latest information.

🔴 Stale - Last updated: 125s ago

Job Status: Processing (may have changed)
Files: 250/1000 (outdated)
Progress: 25% (outdated)

[Refresh Now] button
```

---

## 🎨 **UI Components**

### **1. Freshness Badge**

```python
def render_freshness_badge(age_seconds: float):
    """Render a freshness badge."""
    if age_seconds < 30:
        st.success("🟢 Data is fresh", icon="✅")
    elif age_seconds < 60:
        st.info("🟡 Data is recent", icon="ℹ️")
    else:
        st.error(f"🔴 Data is {int(age_seconds)}s old", icon="⚠️")
```

### **2. Refresh Button**

```python
def render_refresh_button(job_id: str):
    """Render refresh button with freshness indicator."""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        age = get_data_age_seconds(job_id)
        st.caption(f"Last updated: {int(age)}s ago")
    
    with col2:
        if st.button("🔄 Refresh", key=f"refresh_{job_id}"):
            st.rerun()
    
    with col3:
        auto_refresh = st.checkbox(
            "Auto",
            value=True,
            key=f"auto_{job_id}"
        )
```

### **3. Countdown Timer**

```python
def render_countdown_timer(job_id: str, threshold_seconds: int = 60):
    """Render countdown to stale threshold."""
    age = get_data_age_seconds(job_id)
    remaining = max(0, threshold_seconds - age)
    
    if remaining > 0:
        st.caption(f"⏱️  Fresh for {int(remaining)}s more")
    else:
        st.caption(f"🔴 Stale for {int(age - threshold_seconds)}s")
```

---

## 🔧 **Integration Points**

### **Job Status Display**

```python
def display_job_status(job_id: str):
    """Display job status with freshness warning."""
    
    # Show freshness warning if stale
    show_data_freshness_warning(job_id)
    
    # Fetch and display data
    job_data = fetch_job_status(job_id)
    
    # Update timestamp
    st.session_state.last_data_fetch[job_id] = datetime.now()
    
    # Display data
    st.metric("Status", job_data['status'])
    st.metric("Progress", f"{job_data['progress']}%")
    
    # Add freshness indicator
    render_freshness_badge(get_data_age_seconds(job_id))
    
    # Add refresh button
    render_refresh_button(job_id)
```

### **Live Progress Stream**

```python
def show_live_progress(job_id: str):
    """Show live progress with freshness tracking."""
    
    # Check data freshness
    age = get_data_age_seconds(job_id)
    
    if age > 60:
        st.warning(
            "⚠️  Live stream data may be stale. "
            "Auto-refresh recommended."
        )
    
    # Display progress
    progress_data = fetch_progress(job_id)
    st.session_state.last_data_fetch[f"progress_{job_id}"] = datetime.now()
    
    # Show data
    st.metric("Files Processed", progress_data['processed'])
    
    # Freshness indicator
    st.caption(f"Updated {int(age)}s ago")
```

### **Active Jobs List**

```python
def show_active_jobs():
    """Show list of active jobs with freshness indicators."""
    
    jobs = fetch_active_jobs()
    st.session_state.last_data_fetch['active_jobs'] = datetime.now()
    
    for job in jobs:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"Job {job['id']}")
        
        with col2:
            st.write(job['status'])
        
        with col3:
            age = get_data_age_seconds('active_jobs')
            status, color = get_freshness_status(age)
            st.markdown(f":{color}[{status}]")
```

---

## 📋 **Configuration**

### **Thresholds**

```python
# At top of file
FRESHNESS_THRESHOLDS = {
    'fresh': 30,      # <30s = fresh (green)
    'recent': 60,     # 30-60s = recent (yellow)
    'stale': 60       # >60s = stale (red)
}

def get_freshness_status(age_seconds: float) -> tuple[str, str]:
    """Get freshness status based on thresholds."""
    if age_seconds < FRESHNESS_THRESHOLDS['fresh']:
        return ("🟢 Fresh", "green")
    elif age_seconds < FRESHNESS_THRESHOLDS['recent']:
        return ("🟡 Recent", "yellow")
    else:
        return ("🔴 Stale", "red")
```

### **Per-Component Thresholds**

```python
COMPONENT_THRESHOLDS = {
    'job_status': 30,          # Job status stale after 30s
    'progress_stream': 10,     # Progress stream stale after 10s
    'active_jobs': 60,         # Active jobs list stale after 60s
    'metrics': 120             # Metrics stale after 2 minutes
}
```

---

## 🎯 **Best Practices**

### **1. Always Show Freshness**

```python
# ✅ Good - Always show freshness indicator
st.metric("Status", job_data['status'])
st.caption(f"Updated {age}s ago")

# ❌ Bad - No freshness indicator
st.metric("Status", job_data['status'])
```

### **2. Warn Before Action**

```python
# ✅ Good - Warn if taking action on stale data
if age > 60:
    st.warning("Data is stale. Refresh before taking action.")

if st.button("Cancel Job"):
    # Proceed with action
    ...

# ❌ Bad - Allow action on stale data without warning
if st.button("Cancel Job"):
    ...
```

### **3. Provide Easy Refresh**

```python
# ✅ Good - Prominent refresh button
col1, col2 = st.columns([3, 1])
with col1:
    st.metric("Status", status)
with col2:
    if st.button("🔄 Refresh"):
        st.rerun()

# ❌ Bad - No easy way to refresh
st.metric("Status", status)
```

### **4. Use Color Coding**

```python
# ✅ Good - Visual color coding
if age < 30:
    st.success("🟢 Fresh data")
elif age < 60:
    st.info("🟡 Recent data")
else:
    st.error("🔴 Stale data")

# ❌ Bad - No visual distinction
st.write(f"Data age: {age}s")
```

---

## 🧪 **Testing**

### **Test Scenarios**

1. **Fresh Data**
   - Load page
   - Verify green indicator
   - Verify age <30s

2. **Recent Data**
   - Wait 45 seconds
   - Verify yellow indicator
   - Verify age 30-60s

3. **Stale Data**
   - Wait 90 seconds
   - Verify red indicator
   - Verify warning shown
   - Verify age >60s

4. **Refresh Action**
   - Click refresh button
   - Verify age resets
   - Verify indicator turns green

5. **Auto-Refresh**
   - Enable auto-refresh
   - Verify data updates
   - Verify timestamps update

---

## 📊 **Metrics to Track**

```python
# Track how often users see stale data
if age > 60:
    # Increment stale data views counter
    track_metric("stale_data_views", 1)

# Track refresh button clicks
if st.button("Refresh"):
    track_metric("manual_refreshes", 1)
    st.rerun()
```

---

## ✅ **Implementation Checklist**

- [ ] Add timestamp tracking to session state
- [ ] Update timestamps on data fetch
- [ ] Calculate data age on render
- [ ] Add freshness indicators (green/yellow/red)
- [ ] Show warning banner if stale (>60s)
- [ ] Add refresh buttons
- [ ] Color-code freshness status
- [ ] Add "last updated" captions
- [ ] Test all thresholds
- [ ] Document for users

---

## 🎊 **Summary**

**Stale Data Protection provides:**
- ✅ Visual freshness indicators
- ✅ Automatic warnings
- ✅ Easy refresh mechanism
- ✅ Color-coded status
- ✅ Timestamp tracking

**Result:**
- Users always know data freshness
- No decisions on stale data
- Clear refresh path
- Better user confidence

---

## 📝 **Example Implementation**

**Complete example for Job Status page:**

```python
def show_job_status_page():
    """Show job status with freshness protection."""
    
    st.title("Job Status")
    
    # Get job ID
    job_id = st.text_input("Job ID")
    
    if not job_id:
        return
    
    # Calculate data age
    age = get_data_age_seconds(job_id)
    
    # Show freshness warning if stale
    if age > 60:
        st.error(
            f"⚠️  **Stale Data Warning**\\n\\n"
            f"This data is {int(age)} seconds old.\\n"
            f"Refresh for latest information.",
            icon="⚠️"
        )
    
    # Header with freshness indicator
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader("Current Status")
    
    with col2:
        status, color = get_freshness_status(age)
        st.markdown(f":{color}[{status}]")
        st.caption(f"{int(age)}s ago")
    
    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Fetch and display data
    try:
        response = httpx.get(f"{API_URL}/api/v1/admin/ingest/{job_id}/status")
        if response.status_code == 200:
            job_data = response.json()
            
            # Update timestamp
            st.session_state.last_data_fetch[job_id] = datetime.now()
            
            # Display data
            st.metric("Status", job_data['status'])
            st.metric("Progress", f"{job_data['progress']}%")
            st.metric("Files Processed", job_data['processed'])
            
            # Show freshness badge
            render_freshness_badge(age)
        else:
            st.error("Failed to fetch job status")
    
    except Exception as e:
        st.error(f"Error: {e}")
```

---

**Stale data protection: Fully documented and ready to implement!** 🎯

