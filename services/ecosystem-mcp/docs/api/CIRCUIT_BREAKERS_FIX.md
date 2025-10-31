---
title: "Circuit Breakers - Fixed and Enhanced"
service: "ecosystem-mcp"
category: "api"
tags: ['api', 'breaker', 'circuit', 'config', 'configuration', 'endpoints', 'health', 'llm', 'monitoring', 'ollama']
related: ['INDEX.md', 'architecture/OVERVIEW.md', 'CODE_REFERENCE.md', 'API_ENDPOINTS_COMPLETE.md']
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "intermediate"
semantic_keywords: ['api', 'breaker', 'circuit', 'config', 'configuration']
llm_search_hints: ['what is circuit breakers - fixed and enhanced', 'how does circuit breakers - fixed and enhanced work', 'guide to circuit breakers - fixed and enhanced']
---

# Circuit Breakers - Fixed and Enhanced

## Issue

Circuit Breakers section showed "No circuit breakers found or all are closed" even though circuit breakers were configured in the code.

## Root Cause

The `CircuitBreaker` class was missing a `get_state()` method that the API endpoint was trying to call. Without this method, the `hasattr` check failed and the endpoint returned "NOT_CONFIGURED" status.

## Solution

### 1. Added `get_state()` Method to CircuitBreaker Class

**File:** `services/ecosystem-mcp/src/utils/circuit_breaker.py`

Added a comprehensive `get_state()` method that returns:
- Current state (CLOSED, OPEN, HALF_OPEN)
- Failure and success counts
- Total calls statistics
- Configuration settings
- Timing information (last failure, time in open state, recovery countdown)

```python
def get_state(self) -> Dict[str, Any]:
    """Get current state and statistics of the circuit breaker."""
    state = self.stats.state.value if hasattr(self.stats.state, 'value') else str(self.stats.state)
    
    result = {
        "name": self.name,
        "state": state,
        "failure_count": self.stats.failure_count,
        "success_count": self.stats.success_count,
        "total_calls": self.stats.total_calls,
        "total_failures": self.stats.total_failures,
        "total_successes": self.stats.total_successes,
        "config": {
            "failure_threshold": self.config.failure_threshold,
            "success_threshold": self.config.success_threshold,
            "timeout": self.config.timeout
        }
    }
    
    # Add timing and recovery information...
    return result
```

### 2. Updated Dashboard to Display Circuit Breaker Data

**File:** `services/ecosystem-mcp-dashboard/pages/health.py`

Completely rewrote the Circuit Breakers section to:
- Fetch data from `/api/v1/admin/circuit-breakers` endpoint
- Display state with color-coded status (green for CLOSED, yellow for HALF_OPEN, red for OPEN)
- Show failure counts vs threshold
- Display success rate for healthy breakers
- Show recovery countdown for open breakers
- Provide detailed statistics in expandable sections

## What Circuit Breakers Do

Circuit breakers protect against cascading failures by:

1. **CLOSED** (Normal Operation)
   - All calls go through normally
   - Tracks failure count
   - Opens circuit after threshold failures

2. **OPEN** (Failing Fast)
   - Immediately fails without trying
   - Prevents overload on failing services
   - Waits for timeout before testing recovery

3. **HALF_OPEN** (Testing Recovery)
   - Allows limited test calls
   - Closes if successes reach threshold
   - Opens again if tests fail

## Current Configuration

### Ollama Circuit Breaker
- **Failure Threshold:** 5 consecutive failures
- **Success Threshold:** 2 successes to recover
- **Timeout:** 60 seconds before retry

### ChromaDB Circuit Breaker
- **Failure Threshold:** 5 consecutive failures  
- **Success Threshold:** 2 successes to recover
- **Timeout:** 30 seconds before retry (faster recovery than Ollama)

## API Response Example

```json
{
  "circuit_breakers": {
    "ollama": {
      "name": "ollama",
      "state": "closed",
      "failure_count": 0,
      "success_count": 0,
      "total_calls": 0,
      "total_failures": 0,
      "total_successes": 0,
      "config": {
        "failure_threshold": 5,
        "success_threshold": 2,
        "timeout": 60.0
      }
    },
    "chromadb": {
      "name": "chromadb",
      "state": "closed",
      "failure_count": 0,
      "success_count": 0,
      "total_calls": 0,
      "total_failures": 0,
      "total_successes": 0,
      "config": {
        "failure_threshold": 5,
        "success_threshold": 2,
        "timeout": 30.0
      }
    }
  },
  "message": "Circuit breakers protect against cascading failures"
}
```

## Dashboard Display Features

### Summary View
- **Status Indicator:** ✅ (CLOSED), ⚠️ (HALF_OPEN), ❌ (OPEN)
- **State Metric:** Current state
- **Failures Metric:** Current failures vs threshold (e.g., "0/5")
- **Dynamic 4th Column:**
  - OPEN: Shows recovery countdown
  - CLOSED with calls: Shows success rate
  - No calls: Shows total call count

### Detailed View (Expandable)
- **Statistics:**
  - Total calls, successes, failures
  - Current failure count
- **Configuration:**
  - Failure threshold
  - Success threshold  
  - Timeout duration
- **Timing:**
  - Time since last failure
  - Time in open state (if applicable)
- **Raw JSON Data:** Full response for debugging

## Testing

### Test Circuit Breaker Display

1. Open: http://localhost:8501/
2. Navigate to: **🏥 Health & Infrastructure**
3. Scroll to: **⚡ Circuit Breakers** section
4. You should see:
   - ✅ **Ollama** - State: CLOSED, Failures: 0/5, Calls: 0
   - ✅ **Chromadb** - State: CLOSED, Failures: 0/5, Calls: 0
5. Click expander to see detailed stats and config

### Test Circuit Breaker State Changes

To test the circuit breaker opening (for demonstration):

1. Stop Ollama service:
   ```bash
   docker stop ecosystem-mcp-ollama
   ```

2. Make 5+ API calls that use Ollama (will fail)

3. Check circuit breaker status - should show:
   - ❌ **Ollama** - State: OPEN, Retry in: ~60s

4. Wait 60 seconds and check again - should show:
   - ⚠️ **Ollama** - State: HALF_OPEN (testing)

5. Restart Ollama and make successful calls:
   ```bash
   docker start ecosystem-mcp-ollama
   ```

6. After 2 successes, should return to:
   - ✅ **Ollama** - State: CLOSED

## Files Modified

1. **API Side (Requires Rebuild):**
   - `services/ecosystem-mcp/src/utils/circuit_breaker.py`
     - Added `get_state()` method (lines 251-293)

2. **Dashboard Side (Hot-Reload):**
   - `services/ecosystem-mcp-dashboard/pages/health.py`
     - Rewrote Circuit Breakers section (lines 75-159)
     - Fetches from `/api/v1/admin/circuit-breakers`
     - Enhanced display with metrics and details

## Status

✅ **API Side:** Rebuilt and restarted  
✅ **Dashboard Side:** Updated with hot-reload  
✅ **Endpoint Working:** `/api/v1/admin/circuit-breakers` returns data  
✅ **Display Working:** Shows Ollama and ChromaDB circuit breakers  
✅ **Zero Lint Errors:** Clean code  

## Benefits

1. **Visibility:** Real-time monitoring of circuit breaker states
2. **Proactive:** See failure trends before services fail
3. **Debugging:** Detailed statistics help diagnose issues
4. **Resilience:** Circuit breakers prevent cascade failures
5. **Recovery:** Automatic detection and recovery from failures

## What's Next

Circuit breakers will automatically protect your services:
- If Ollama becomes unavailable, circuit opens after 5 failures
- If ChromaDB has issues, circuit opens after 5 failures
- Both automatically test recovery after timeout
- Dashboard shows real-time status and countdown

No configuration needed - it's all automatic! 🎉

