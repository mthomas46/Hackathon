# ✂️ **Context Pruning Guide**

## **Complete Guide to Dynamic Context Pruning**

---

## **Table of Contents**

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [API Reference](#api-reference)
5. [Pruning Strategies](#pruning-strategies)
6. [Usage Examples](#usage-examples)
7. [UI Guide](#ui-guide)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## **Overview**

Context Pruning intelligently reduces context size while preserving the most valuable information. It helps you stay within token budgets without losing critical content.

### **Key Features**

✅ **4 Pruning Strategies** - Relevance, Recency, Hybrid, Importance  
✅ **Token Budget Management** - Strict budget enforcement  
✅ **Metrics & Analytics** - Pruning ratio, token usage  
✅ **Flexible Configuration** - Easy strategy switching  
✅ **Production-Ready** - Comprehensive tests & error handling  

### **Use Cases**

- **LLM Context Optimization** - Fit context within model token limits
- **Cost Reduction** - Minimize API token usage and costs
- **Performance Improvement** - Reduce processing time with smaller contexts
- **Focus Enhancement** - Keep only most relevant information
- **Incremental Updates** - Prune old/irrelevant context periodically

---

## **Architecture**

### **Pruning Flow**

```
Context Items → Strategy Selection → Scoring → Sorting → 
Budget Allocation → Item Selection → Pruned Context
```

### **Strategy Comparison**

| Strategy | Primary Metric | Best For | Order |
|----------|---------------|----------|-------|
| **Relevance** | Relevance Score | Query-focused tasks | Highest score first |
| **Recency** | Timestamp | Time-sensitive updates | Newest first |
| **Hybrid** | Combined (50/50) | General purpose | Balanced score |
| **Importance** | Importance Score | Priority-based tasks | Highest priority first |

---

## **Quick Start**

### **Basic Usage**

```python
from mcp_retrieval.src.context_pruning import (
    ContextPruner,
    PruningStrategy,
    create_context_item,
)
from datetime import datetime, timedelta

# Create context items
items = [
    create_context_item(
        content="High priority bug fix needed",
        timestamp=datetime.now() - timedelta(hours=1),
        relevance_score=0.95,
        importance_score=0.90,
        metadata={"priority": "high"}
    ),
    create_context_item(
        content="Update documentation",
        timestamp=datetime.now() - timedelta(days=7),
        relevance_score=0.60,
        importance_score=0.50,
        metadata={"priority": "medium"}
    ),
    # ... more items
]

# Initialize pruner with strategy
pruner = ContextPruner(strategy=PruningStrategy.HYBRID)

# Prune to fit budget
pruned = pruner.prune(
    items=items,
    target_tokens=200
)

# Access results
print(f"Kept {len(pruned.items)} items")
print(f"Using {pruned.token_count} tokens")
print(f"Pruning ratio: {pruned.pruning_ratio:.1%}")
```

### **Strategy Switching**

```python
# Start with relevance
pruner = ContextPruner(strategy=PruningStrategy.RELEVANCE)

# Prune with relevance
result1 = pruner.prune(items, target_tokens=200)

# Switch to recency
pruner.set_strategy(PruningStrategy.RECENCY)

# Prune with recency
result2 = pruner.prune(items, target_tokens=200)
```

---

## **API Reference**

### **ContextPruner**

Main class for context pruning.

#### **Constructor**

```python
ContextPruner(strategy: PruningStrategy = PruningStrategy.HYBRID)
```

**Parameters:**
- `strategy` - Pruning strategy to use (default: HYBRID)

**Valid Strategies:**
- `PruningStrategy.RELEVANCE` - Relevance-based
- `PruningStrategy.RECENCY` - Recency-based
- `PruningStrategy.HYBRID` - Hybrid (50/50)
- `PruningStrategy.IMPORTANCE` - Importance-based

#### **Methods**

##### **prune()**

```python
prune(
    items: List[ContextItem],
    target_tokens: int,
    query: Optional[str] = None
) -> PrunedContext
```

Prune context items to fit within token budget.

**Parameters:**
- `items` - Context items to prune (required)
- `target_tokens` - Target token budget (required)
- `query` - Optional query for relevance boost (used in Hybrid)

**Returns:**
- `PrunedContext` - Pruned items with metrics

**Example:**
```python
pruned = pruner.prune(
    items=context_items,
    target_tokens=300,
    query="authentication bug"
)

for item in pruned.items:
    print(f"[{item.relevance_score:.2f}] {item.content}")
```

##### **set_strategy()**

```python
set_strategy(strategy: PruningStrategy)
```

Change pruning strategy.

**Parameters:**
- `strategy` - New pruning strategy

**Example:**
```python
pruner.set_strategy(PruningStrategy.RECENCY)
```

### **ContextItem**

Represents a single context item.

```python
@dataclass
class ContextItem:
    content: str              # Item content
    timestamp: datetime       # Creation time
    relevance_score: float    # 0.0 to 1.0
    importance_score: float   # 0.0 to 1.0
    token_count: int          # Token count
    metadata: Dict[str, Any]  # Additional metadata
```

### **PrunedContext**

Result of pruning operation.

```python
@dataclass
class PrunedContext:
    items: List[ContextItem]  # Kept items
    token_count: int          # Total tokens
    pruning_ratio: float      # Tokens kept / original
    strategy: str             # Strategy used
    metadata: Dict[str, Any]  # Pruning metadata
```

### **Helper Functions**

#### **create_context_item()**

```python
create_context_item(
    content: str,
    timestamp: Optional[datetime] = None,
    relevance_score: float = 0.5,
    importance_score: float = 0.5,
    metadata: Optional[Dict[str, Any]] = None
) -> ContextItem
```

Create a context item with automatic token counting.

**Example:**
```python
item = create_context_item(
    content="Fix authentication bug",
    relevance_score=0.9,
    importance_score=0.85,
    metadata={"priority": "high", "category": "bug"}
)
```

#### **estimate_tokens()**

```python
estimate_tokens(text: str) -> int
```

Estimate token count for text (~4 chars per token).

---

## **Pruning Strategies**

### **1. Relevance Strategy**

**Description:** Keeps items with highest relevance scores.

**Use When:**
- Query-focused tasks
- Search results
- Content retrieval
- Relevance is most important

**Algorithm:**
```python
1. Sort items by relevance_score (descending)
2. Add items to result while within budget
3. Return pruned list
```

**Example:**
```python
pruner = ContextPruner(strategy=PruningStrategy.RELEVANCE)
pruned = pruner.prune(items, target_tokens=200)

# Results ordered: highest relevance first
for item in pruned.items:
    print(f"Relevance: {item.relevance_score:.2f}")
```

### **2. Recency Strategy**

**Description:** Keeps most recently created items.

**Use When:**
- Real-time monitoring
- Latest updates
- Time-sensitive content
- Recent activity matters most

**Algorithm:**
```python
1. Sort items by timestamp (most recent first)
2. Add items to result while within budget
3. Return pruned list
```

**Example:**
```python
pruner = ContextPruner(strategy=PruningStrategy.RECENCY)
pruned = pruner.prune(items, target_tokens=200)

# Results ordered: newest first
for item in pruned.items:
    age = datetime.now() - item.timestamp
    print(f"Age: {age}")
```

### **3. Hybrid Strategy (50/50)**

**Description:** Balances relevance and recency equally.

**Use When:**
- General purpose pruning
- Unsure which strategy to use
- Want balanced results
- Both factors are important

**Algorithm:**
```python
1. Normalize recency to 0-1 scale
2. Calculate: score = (relevance * 0.5) + (recency * 0.5)
3. Sort items by combined score (descending)
4. Add items to result while within budget
5. Return pruned list
```

**Example:**
```python
pruner = ContextPruner(strategy=PruningStrategy.HYBRID)
pruned = pruner.prune(items, target_tokens=200, query="bug fix")

# Results ordered: best combined score first
for item in pruned.items:
    print(f"R: {item.relevance_score:.2f}, Age: {datetime.now() - item.timestamp}")
```

### **4. Importance Strategy**

**Description:** Keeps items with highest importance scores.

**Use When:**
- Priority-based workflows
- Critical tasks first
- Importance explicitly set
- Fixed prioritization needed

**Algorithm:**
```python
1. Sort items by importance_score (descending)
2. Add items to result while within budget
3. Return pruned list
```

**Example:**
```python
pruner = ContextPruner(strategy=PruningStrategy.IMPORTANCE)
pruned = pruner.prune(items, target_tokens=200)

# Results ordered: highest importance first
for item in pruned.items:
    print(f"Importance: {item.importance_score:.2f}")
```

---

## **Usage Examples**

### **Example 1: Basic Pruning**

```python
from mcp_retrieval.src.context_pruning import *
from datetime import datetime, timedelta

# Create context items
items = [
    create_context_item(
        "Critical bug in authentication",
        timestamp=datetime.now(),
        relevance_score=0.95,
        importance_score=0.98
    ),
    create_context_item(
        "Update documentation",
        timestamp=datetime.now() - timedelta(days=7),
        relevance_score=0.60,
        importance_score=0.50
    ),
    create_context_item(
        "Refactor legacy code",
        timestamp=datetime.now() - timedelta(days=3),
        relevance_score=0.70,
        importance_score=0.65
    ),
]

# Prune to 100 tokens
pruner = ContextPruner(strategy=PruningStrategy.HYBRID)
pruned = pruner.prune(items, target_tokens=100)

print(f"Kept {len(pruned.items)}/{len(items)} items")
print(f"Tokens: {pruned.token_count}/100")
print(f"Pruning ratio: {pruned.pruning_ratio:.1%}")
```

### **Example 2: LLM Context Window Management**

```python
# Manage context for LLM with 4096 token limit
MAX_TOKENS = 4096
SYSTEM_PROMPT_TOKENS = 100
RESPONSE_BUFFER = 500

# Calculate available tokens for context
available_tokens = MAX_TOKENS - SYSTEM_PROMPT_TOKENS - RESPONSE_BUFFER
# = 3496 tokens

# Prune context to fit
pruner = ContextPruner(strategy=PruningStrategy.RELEVANCE)
pruned = pruner.prune(
    items=conversation_history,
    target_tokens=available_tokens,
    query=user_question
)

# Build prompt
prompt = system_prompt + "\n\n"
for item in pruned.items:
    prompt += item.content + "\n"
prompt += f"\nUser: {user_question}\n"

# Send to LLM
response = llm.complete(prompt)
```

### **Example 3: Progressive Pruning**

```python
# Prune progressively if initial budget too small
target_budgets = [100, 200, 300, 400]

pruner = ContextPruner(strategy=PruningStrategy.HYBRID)

for budget in target_budgets:
    pruned = pruner.prune(items, target_tokens=budget)
    
    if len(pruned.items) >= 5:  # Minimum items threshold
        print(f"Success with budget: {budget}")
        break
else:
    print("Could not achieve minimum items")
```

### **Example 4: Strategy Comparison**

```python
# Compare all strategies
strategies = [
    PruningStrategy.RELEVANCE,
    PruningStrategy.RECENCY,
    PruningStrategy.HYBRID,
    PruningStrategy.IMPORTANCE,
]

results = {}

for strategy in strategies:
    pruner = ContextPruner(strategy=strategy)
    pruned = pruner.prune(items, target_tokens=200)
    
    results[strategy.value] = {
        "items_kept": len(pruned.items),
        "tokens": pruned.token_count,
        "ratio": pruned.pruning_ratio,
        "avg_relevance": sum(i.relevance_score for i in pruned.items) / len(pruned.items),
    }

# Print comparison
for strategy, metrics in results.items():
    print(f"\n{strategy.upper()}:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
```

### **Example 5: Periodic Context Cleanup**

```python
import schedule
import time

def cleanup_context():
    """Periodically prune old context."""
    pruner = ContextPruner(strategy=PruningStrategy.RECENCY)
    
    # Prune to keep last 24 hours of context
    pruned = pruner.prune(
        items=global_context,
        target_tokens=2000
    )
    
    # Update global context
    global_context[:] = pruned.items
    
    print(f"Cleaned up: {len(global_context)} items remaining")

# Schedule cleanup every hour
schedule.every(1).hours.do(cleanup_context)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## **UI Guide**

### **Accessing the UI**

Navigate to the **Context Pruning** page in the MCP Dashboard.

### **Configuration Sidebar**

1. **Strategy Selection**
   - Choose from 4 strategies
   - See strategy description
   
2. **Token Budget**
   - View current token usage
   - Set target budget with slider
   - See pruning target percentage

### **Context Tab**

1. **Generate Sample** - Create sample context items
2. **Add Item** - Manually add new items
3. **Clear All** - Remove all items
4. **View Items** - See table with:
   - Content preview
   - Token counts
   - Relevance/Importance scores
   - Age
   - Priority

### **Prune Tab**

1. **Review Configuration**
   - Strategy
   - Target budget
   
2. **Execute Pruning**
   - Click "Execute Pruning" button
   - View results immediately

3. **Results Display**
   - Summary metrics (4 cards)
   - Before/after comparison
   - Visualizations:
     * Token usage (bar chart)
     * Item count (bar chart)
     * Score distribution (scatter plot)
   - Kept items list (expandable)

### **Analysis Tab**

View detailed analytics:
- Relevance score distribution (histogram)
- Importance score distribution (histogram)
- Token count per item (bar chart)
- Age distribution (histogram)

---

## **Best Practices**

### **1. Choose the Right Strategy**

✅ **Good:**
```python
# Time-sensitive monitoring → Use Recency
pruner = ContextPruner(strategy=PruningStrategy.RECENCY)

# Query-focused search → Use Relevance
pruner = ContextPruner(strategy=PruningStrategy.RELEVANCE)

# General purpose → Use Hybrid
pruner = ContextPruner(strategy=PruningStrategy.HYBRID)
```

❌ **Avoid:**
```python
# Using Recency for query-focused tasks
# Using Relevance for time-sensitive monitoring
```

### **2. Set Realistic Token Budgets**

```python
# Calculate budget based on constraints
total_limit = 4096  # Model limit
system_tokens = 100
response_buffer = 500

# Leave room for response
target_budget = total_limit - system_tokens - response_buffer

pruner.prune(items, target_tokens=target_budget)
```

### **3. Validate Pruned Results**

```python
pruned = pruner.prune(items, target_tokens=200)

# Check minimum requirements
if len(pruned.items) < 3:
    # Not enough items, increase budget
    pruned = pruner.prune(items, target_tokens=300)

# Check average quality
avg_relevance = sum(i.relevance_score for i in pruned.items) / len(pruned.items)
if avg_relevance < 0.5:
    # Quality too low, adjust strategy
    pruner.set_strategy(PruningStrategy.RELEVANCE)
    pruned = pruner.prune(items, target_tokens=200)
```

### **4. Monitor Pruning Metrics**

```python
pruned = pruner.prune(items, target_tokens=200)

# Log metrics
logger.info(f"Pruning completed:")
logger.info(f"  Items: {len(items)} → {len(pruned.items)}")
logger.info(f"  Tokens: {sum(i.token_count for i in items)} → {pruned.token_count}")
logger.info(f"  Ratio: {pruned.pruning_ratio:.1%}")
logger.info(f"  Strategy: {pruned.strategy}")

# Alert if aggressive pruning
if pruned.pruning_ratio < 0.3:
    logger.warning("Aggressive pruning detected (< 30% retained)")
```

### **5. Handle Edge Cases**

```python
# Empty context
if not items:
    print("No items to prune")
    return

# All items fit within budget
total_tokens = sum(i.token_count for i in items)
if total_tokens <= target_tokens:
    print("All items fit, no pruning needed")
    return items

# Single item exceeds budget
if len(items) == 1 and items[0].token_count > target_tokens:
    print("Warning: Single item exceeds budget")
    # Decision: Keep it anyway or truncate content
```

---

## **Troubleshooting**

### **Problem: Too Many Items Pruned**

**Symptoms:** Pruned context is too small, missing important items.

**Solutions:**
1. Increase token budget
2. Switch to less aggressive strategy (e.g., Hybrid instead of Relevance)
3. Boost importance scores of critical items
4. Review score distributions

```python
# Before: Too aggressive
pruned = pruner.prune(items, target_tokens=50)  # Too small

# After: More reasonable
pruned = pruner.prune(items, target_tokens=200)  # Better
```

### **Problem: Low Quality Results**

**Symptoms:** Pruned items have low relevance/importance scores.

**Solutions:**
1. Use Relevance or Importance strategy
2. Increase scores for important items
3. Filter items before pruning
4. Increase token budget to keep more items

```python
# Filter low-quality items first
quality_items = [
    item for item in items
    if item.relevance_score >= 0.5 or item.importance_score >= 0.5
]

# Then prune
pruned = pruner.prune(quality_items, target_tokens=200)
```

### **Problem: Budget Always Exceeded**

**Symptoms:** `pruned.token_count` exceeds `target_tokens`.

**Note:** This should NOT happen - the pruner strictly enforces budgets.

**Check:**
```python
pruned = pruner.prune(items, target_tokens=200)

assert pruned.token_count <= 200, f"Budget violated: {pruned.token_count} > 200"
```

If this fails, there's a bug in the implementation.

### **Problem: No Items Returned**

**Symptoms:** `len(pruned.items) == 0`

**Causes:**
1. Target budget is 0
2. All items exceed budget individually
3. Empty input

**Solutions:**
```python
# Check budget
if target_tokens == 0:
    target_tokens = 100  # Minimum budget

# Check item sizes
if all(item.token_count > target_tokens for item in items):
    # Keep at least the smallest item
    smallest = min(items, key=lambda i: i.token_count)
    pruned.items = [smallest]
```

---

## **Advanced Topics**

### **Custom Scoring Functions**

For advanced use cases, extend scoring:

```python
def custom_score(item: ContextItem, query: str = None) -> float:
    """Calculate custom score."""
    
    # Base scores
    relevance = item.relevance_score
    importance = item.importance_score
    
    # Recency bonus (0-1)
    age_hours = (datetime.now() - item.timestamp).total_seconds() / 3600
    recency = max(0, 1 - (age_hours / 168))  # 1 week decay
    
    # Priority bonus
    priority_bonus = {
        "critical": 0.3,
        "high": 0.2,
        "medium": 0.1,
        "low": 0.0,
    }.get(item.metadata.get("priority"), 0.0)
    
    # Combined score
    score = (relevance * 0.4) + (importance * 0.3) + (recency * 0.2) + priority_bonus
    
    return min(1.0, score)
```

### **Content Truncation**

If items must be kept but exceed budget:

```python
def truncate_item(item: ContextItem, max_tokens: int) -> ContextItem:
    """Truncate item content to fit budget."""
    
    if item.token_count <= max_tokens:
        return item
    
    # Estimate truncation point (~4 chars per token)
    chars_to_keep = max_tokens * 4
    truncated_content = item.content[:chars_to_keep] + "..."
    
    return ContextItem(
        content=truncated_content,
        timestamp=item.timestamp,
        relevance_score=item.relevance_score * 0.9,  # Penalty for truncation
        importance_score=item.importance_score,
        token_count=max_tokens,
        metadata={**item.metadata, "truncated": True}
    )
```

---

## **Resources**

- **Source Code:** `services/mcp_retrieval/src/context_pruning.py`
- **Unit Tests:** `tests/unit/test_context_pruning.py`
- **UI Page:** `dashboard/pages/context_pruning.py`
- **Examples:** See Usage Examples section

---

**For support or questions, refer to the MCP documentation or contact the development team.**

---

**Happy Pruning! ✂️**
