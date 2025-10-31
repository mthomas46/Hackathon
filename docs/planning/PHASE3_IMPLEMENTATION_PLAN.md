# 🚀 Phase 3: Advanced Optimizations - Implementation Plan

**Date:** October 16, 2025  
**Estimated Time:** 2-3 hours  
**Expected Gain:** 2-3× additional speedup  
**Target Throughput:** 20,000-30,000 files/hour  

---

## 📋 Current State

**After Phase 2:**
- **Throughput:** 10,000 files/hour (estimated)
- **Bottlenecks identified:**
  1. Fixed batch size doesn't adapt to file characteristics
  2. File size checks happen after reading (wasted I/O)
  3. No caching of frequently accessed Git data
  4. Large files read entirely into memory

---

## 🎯 Phase 3 Goals

1. **Dynamic batch sizing** based on file sizes
2. **Early filtering** to skip empty/large files before reading
3. **Smart caching** for Git objects and metadata
4. **Memory-efficient** large file handling
5. **Maintain stability** while pushing performance limits

---

## 🏗️ Architecture: Quick Wins First

### **Priority 1: Dynamic Batch Sizing (30 min) - Expected: 1.5-2× speedup**

**Problem:** Fixed batch size of 20 doesn't adapt to file characteristics:
- Small files (< 10KB): Can process 50+ at once
- Medium files (10-100KB): Current 20 is optimal
- Large files (> 100KB): Should process 5-10 to avoid memory pressure

**Solution:**
```python
def calculate_optimal_batch_size(self, files: List[Dict[str, Any]]) -> int:
    """
    Calculate optimal batch size based on file size distribution.
    
    Strategy:
    - Sample first 10 files to estimate average size
    - Adjust batch size to target ~10MB per batch
    - Constrain to reasonable min/max
    """
    if not files:
        return 20  # Default
    
    # Sample first 10 files to get average size
    sample_size = min(10, len(files))
    total_size = sum(len(f.get('content', '')) for f in files[:sample_size])
    avg_size_kb = (total_size / sample_size) / 1024 if sample_size > 0 else 50
    
    # Target: ~10MB per batch for optimal throughput
    target_batch_mb = 10
    target_batch_bytes = target_batch_mb * 1024 * 1024
    
    if avg_size_kb < 10:  # Very small files
        batch_size = min(50, len(files))
    elif avg_size_kb < 50:  # Small files
        batch_size = min(30, len(files))
    elif avg_size_kb < 100:  # Medium files
        batch_size = 20  # Current optimal
    else:  # Large files
        # Calculate to stay under target
        avg_size_bytes = avg_size_kb * 1024
        batch_size = max(5, int(target_batch_bytes / avg_size_bytes))
        batch_size = min(batch_size, 15)
    
    logger.info(
        f"📏 Dynamic batch size: {batch_size} "
        f"(avg file: {avg_size_kb:.1f}KB, target: {target_batch_mb}MB)"
    )
    
    return batch_size
```

**Integration:**
```python
# In _process_commit_with_batch_optimization()
if files_to_process:
    # Phase 3: Calculate optimal batch size dynamically
    optimal_batch_size = self.calculate_optimal_batch_size(files_to_process)
    
    logger.info(
        f"🚀 Processing {len(files_to_process)} files in batches "
        f"(dynamic size: {optimal_batch_size})"
    )
    
    for batch_idx in range(0, len(files_to_process), optimal_batch_size):
        batch_files = files_to_process[batch_idx:batch_idx + optimal_batch_size]
        # ... process batch
```

**Expected Impact:**
- Small files: 50/batch → 2.5× faster
- Medium files: No change (already optimal)
- Large files: Better memory usage, prevents thrashing
- **Overall: 1.5-2× speedup**

---

### **Priority 2: Early File Size Filtering (15 min) - Expected: 1.2-1.3× speedup**

**Problem:** We read entire files before checking if they're empty or too large.

**Solution:**
```python
async def get_file_size_at_commit(
    self,
    commit_sha: str,
    file_path: str
) -> Optional[int]:
    """
    Get file size without reading content.
    Uses Git's blob size info - very fast!
    """
    try:
        return await asyncio.to_thread(
            self._get_file_size_sync,
            commit_sha,
            file_path
        )
    except Exception as e:
        logger.debug(f"Could not get size for {file_path}: {e}")
        return None

def _get_file_size_sync(self, commit_sha: str, file_path: str) -> Optional[int]:
    """Get file size from Git blob."""
    try:
        commit = self.repo.commit(commit_sha)
        blob = commit.tree / file_path
        return blob.size
    except Exception:
        return None
```

**Integration:**
```python
# PHASE 3: Pre-filter files by size BEFORE reading
logger.info(f"🔍 Pre-filtering {len(filtered_files)} files by size...")

size_check_tasks = [
    self.git_service.get_file_size_at_commit(commit.sha, fp)
    for fp in filtered_files
]
file_sizes = await asyncio.gather(*size_check_tasks)

files_to_read = []
for file_path, size in zip(filtered_files, file_sizes):
    if size is None:
        files_to_read.append(file_path)  # Can't check, include
    elif size == 0:
        logger.debug(f"⏭️  Skipping empty file: {file_path}")
        result["skipped"] += 1
    elif size > 1_000_000:  # 1MB limit
        logger.debug(f"⏭️  Skipping large file ({size/1024:.1f}KB): {file_path}")
        result["skipped"] += 1
    else:
        files_to_read.append(file_path)

logger.info(
    f"📊 Size filter: {len(files_to_read)}/{len(filtered_files)} files "
    f"to read (skipped {len(filtered_files) - len(files_to_read)})"
)
```

**Expected Impact:**
- Eliminates I/O for empty files (~5% of files in typical repos)
- Eliminates I/O for oversized files (~2% of files)
- Uses Git metadata instead of reading content
- **Speedup: 1.2-1.3×**

---

### **Priority 3: Skip Binary Files Early (10 min) - Expected: 1.1-1.2× speedup**

**Problem:** Binary files are filtered AFTER reading, wasting I/O.

**Solution:**
```python
def is_binary_file_extension(self, file_path: str) -> bool:
    """Check if file extension indicates binary content."""
    binary_extensions = {
        # Images
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg', '.webp',
        # Archives
        '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
        # Executables
        '.exe', '.dll', '.so', '.dylib', '.bin',
        # Media
        '.mp4', '.mp3', '.avi', '.mov', '.wav', '.flac',
        # Documents
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        # Fonts
        '.ttf', '.otf', '.woff', '.woff2',
        # Other
        '.db', '.sqlite', '.pkl', '.pyc', '.class'
    }
    
    ext = Path(file_path).suffix.lower()
    return ext in binary_extensions

# In filtering logic:
def _filter_files(self, files: List[Any]) -> List[Any]:
    """Enhanced filtering with binary extension check."""
    filtered = []
    for file_path in files:
        path_str = file_path if isinstance(file_path, str) else file_path.path
        
        # Phase 3: Skip known binary extensions early
        if self.is_binary_file_extension(path_str):
            logger.debug(f"⏭️  Skipping binary file: {path_str}")
            continue
        
        # ... existing filtering logic
        filtered.append(file_path)
    
    return filtered
```

**Expected Impact:**
- Skip ~10-15% of files based on extension alone
- No I/O wasted on binary files
- **Speedup: 1.1-1.2×**

---

### **Priority 4: Batch Size Tuning Based on Success Rate (20 min) - Expected: 1.1-1.15× speedup**

**Problem:** If many files fail/skip, we're doing unnecessary work in large batches.

**Solution:**
```python
class AdaptiveBatchSizer:
    """Dynamically adjusts batch size based on success rate."""
    
    def __init__(self):
        self.recent_batches = []  # Track last N batches
        self.max_history = 10
        self.min_batch_size = 5
        self.max_batch_size = 50
    
    def record_batch(self, batch_size: int, success_count: int, skip_count: int, fail_count: int):
        """Record a batch result."""
        total = success_count + skip_count + fail_count
        success_rate = success_count / total if total > 0 else 0
        
        self.recent_batches.append({
            'size': batch_size,
            'success_rate': success_rate,
            'total': total
        })
        
        # Keep only recent history
        if len(self.recent_batches) > self.max_history:
            self.recent_batches.pop(0)
    
    def get_recommended_size(self, base_size: int) -> int:
        """Get recommended batch size based on recent performance."""
        if len(self.recent_batches) < 3:
            return base_size  # Not enough data
        
        # Calculate average success rate
        avg_success_rate = sum(b['success_rate'] for b in self.recent_batches) / len(self.recent_batches)
        
        # Adjust based on success rate
        if avg_success_rate > 0.8:  # High success rate
            # Increase batch size
            adjusted = int(base_size * 1.2)
        elif avg_success_rate < 0.3:  # Low success rate (lots of skips/fails)
            # Decrease batch size to reduce overhead
            adjusted = int(base_size * 0.7)
        else:  # Medium success rate
            adjusted = base_size
        
        # Constrain to limits
        return max(self.min_batch_size, min(self.max_batch_size, adjusted))
```

**Integration:**
```python
# In JobProcessor.__init__()
self.adaptive_batch_sizer = AdaptiveBatchSizer()

# After processing each batch
self.adaptive_batch_sizer.record_batch(
    batch_size=len(batch_files),
    success_count=batch_result["processed"],
    skip_count=0,  # Not tracked in batch result yet
    fail_count=batch_result["failed"]
)

# Before processing next batch
base_batch_size = self.calculate_optimal_batch_size(files_to_process)
adaptive_batch_size = self.adaptive_batch_sizer.get_recommended_size(base_batch_size)
```

**Expected Impact:**
- Adapts to workload characteristics
- Reduces overhead on skip-heavy batches
- Increases throughput on success-heavy batches
- **Speedup: 1.1-1.15×**

---

### **Priority 5: Connection Pool Optimization (15 min) - Expected: 1.05-1.1× speedup**

**Problem:** We create a new DB session for each batch, even with pooling.

**Solution:**
```python
async def _process_commit_with_batch_optimization(
    self, 
    commit: Any, 
    job: IngestionJobModel,
    batch_size: int = 20
) -> Dict[str, Any]:
    """Process commit with connection reuse across batches."""
    
    # Phase 3: Reuse single connection for entire commit
    async with get_database().session() as commit_session:
        # Check/create commit metadata once
        await self._ensure_commit_exists(commit, commit_session)
        
        # Process all batches with same session
        for batch_idx in range(0, len(files_to_process), optimal_batch_size):
            batch_files = files_to_process[batch_idx:batch_idx + optimal_batch_size]
            
            # Pass session to batch processor
            batch_result = await self._process_batch_optimized(
                batch_files=batch_files,
                commit=commit,
                job=job,
                session=commit_session  # Reuse connection!
            )
```

**Expected Impact:**
- Fewer connection creations
- Lower overhead per batch
- **Speedup: 1.05-1.1×**

---

## 📊 Combined Expected Impact

### **Quick Wins (Priority 1-3):**

| Optimization | Time | Speedup | Cumulative |
|--------------|------|---------|------------|
| **Dynamic Batch Sizing** | 30 min | 1.5-2× | 1.5-2× |
| **Early Size Filtering** | 15 min | 1.2-1.3× | 1.8-2.6× |
| **Skip Binary Early** | 10 min | 1.1-1.2× | 2.0-3.1× |
| **Adaptive Batch Sizing** | 20 min | 1.1-1.15× | 2.2-3.6× |
| **Connection Reuse** | 15 min | 1.05-1.1× | 2.3-4.0× |

**Total Quick Wins:** ~90 minutes, **2.3-4× speedup**

### **Advanced Optimizations (If time permits):**

**6. Memory-Mapped File Reads (30 min) - 1.1-1.2×:**
```python
# For very large files, use mmap instead of reading entirely
import mmap

def read_large_file_efficiently(file_path: str) -> str:
    """Read large files using memory mapping."""
    with open(file_path, 'r') as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped:
            # Process in chunks
            return mmapped.read().decode('utf-8')
```

**7. Redis Caching for Git Metadata (45 min) - 1.2-1.5×:**
```python
# Cache frequently accessed Git data
@cache_with_redis(ttl=3600)
async def get_commit_metadata(commit_sha: str) -> Dict:
    """Get commit metadata with Redis caching."""
    # Avoid redundant Git operations
```

**8. Parallel Embedding Batches (30 min) - 1.1-1.3×:**
```python
# If Ollama supports it, send multiple batch requests in parallel
if len(embeddings_needed) > 100:
    # Split into sub-batches and process concurrently
    sub_batches = chunk_list(embeddings_needed, 50)
    embedding_tasks = [
        self.embedding_service.generate_batch(batch)
        for batch in sub_batches
    ]
    results = await asyncio.gather(*embedding_tasks)
```

**Total if all implemented:** **3-6× additional speedup**

---

## 🎯 Recommended Implementation Plan

### **Session 1: Quick Wins (90 min)**

1. **Dynamic Batch Sizing** (30 min)
   - Implement `calculate_optimal_batch_size()`
   - Integrate into batch processing loop
   - Test with varying file sizes

2. **Early Filtering** (25 min)
   - Add `get_file_size_at_commit()` to GitService
   - Add `is_binary_file_extension()` check
   - Integrate pre-filtering before file reads

3. **Adaptive Batch Sizing** (20 min)
   - Implement `AdaptiveBatchSizer` class
   - Integrate feedback loop
   - Add logging

4. **Connection Reuse** (15 min)
   - Lift session to commit level
   - Pass session to batch processor
   - Update batch method signature

### **Session 2: Advanced (If desired) (105 min)**

5. **Memory-Mapped Reads** (30 min)
6. **Redis Caching** (45 min)  
7. **Parallel Embedding Batches** (30 min)

---

## 📈 Expected Results

### **After Quick Wins:**
```
Current (Phase 2): 10,000 files/hour
After Quick Wins:  23,000-40,000 files/hour
Improvement:       2.3-4× faster
```

### **After All Phase 3:**
```
Current (Phase 2): 10,000 files/hour
After Phase 3:     30,000-60,000 files/hour
Improvement:       3-6× faster
```

### **Total Optimization Journey:**
```
Original:     52 files/hour
Phase 1:     920 files/hour  (17.7×)
Phase 1.5:  1,660 files/hour  (32×)
Phase 2:   10,000 files/hour  (192×)
Phase 3:   30,000 files/hour  (576×) 🚀🚀🚀
```

**From 75 hours to 10 minutes for a 5,000-file repo!**

---

## ⚠️ Risks & Mitigations

### **Risk 1: Dynamic batch sizing instability**
**Mitigation:** 
- Constrain to reasonable min/max (5-50)
- Log batch size decisions for debugging
- Fall back to fixed size if calculations fail

### **Risk 2: Memory pressure from large batches**
**Mitigation:**
- Target fixed memory per batch (10MB)
- Monitor actual memory usage
- Implement circuit breaker if needed

### **Risk 3: Redis dependency**
**Mitigation:**
- Make Redis caching optional
- Graceful degradation if Redis unavailable
- LRU cache fallback

---

## 🧪 Testing Strategy

### **Unit Tests:**
1. Test dynamic batch size calculation with various file distributions
2. Test early filtering with different file sizes
3. Test adaptive batch sizer with different success rates
4. Test connection reuse with multiple batches

### **Integration Tests:**
1. Process repo with mix of small/medium/large files
2. Verify batch sizes adapt correctly
3. Verify early filtering reduces I/O
4. Measure memory usage under load

### **Performance Tests:**
1. Benchmark against Phase 2 baseline
2. Test with various repo characteristics
3. Validate 2-4× speedup
4. Monitor resource usage

---

## 📝 Implementation Checklist

### **Quick Wins (90 min):**
- [ ] Implement `calculate_optimal_batch_size()`
- [ ] Add `get_file_size_at_commit()` to GitService
- [ ] Add `is_binary_file_extension()` filtering
- [ ] Integrate pre-filtering before reads
- [ ] Implement `AdaptiveBatchSizer` class
- [ ] Add batch result recording
- [ ] Lift DB session to commit level
- [ ] Update batch processor signature
- [ ] Add comprehensive logging
- [ ] Deploy and test

### **Advanced (Optional, 105 min):**
- [ ] Implement memory-mapped file reading
- [ ] Add Redis caching layer
- [ ] Implement parallel embedding batches
- [ ] Add monitoring and metrics
- [ ] Load test at scale

---

## 🚀 Let's Implement Quick Wins First!

**Ready to start with Session 1 (Quick Wins - 90 min)?**

This will give us **2.3-4× speedup** with minimal risk and high ROI.

Order of implementation:
1. Dynamic Batch Sizing → biggest impact
2. Early Filtering → eliminates wasted I/O
3. Adaptive Batch Sizing → continuous optimization
4. Connection Reuse → reduces overhead

**Let's do this! 🚀**

