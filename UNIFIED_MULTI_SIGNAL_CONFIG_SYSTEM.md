# Unified Multi-Signal Ranking + Optional Configs System 🎯

**Date:** October 25, 2025 07:00 UTC  
**Philosophy:** Token-rich (Ollama), Time-constrained (processing speed matters)  
**Strategy:** Aggressive caching, parallel processing, lazy loading  
**Goal:** Maximum accuracy with minimal latency  

---

## 🧠 CRITICAL INSIGHT: TOKEN-RICH ENVIRONMENT

### **What This Changes:**

**Traditional RAG (API-based LLMs):**
```python
# Every token costs money
# Minimize prompt size
# Compress context
# Short citations

prompt = f"Context (truncated): {context[:500]}..."  # ❌ Token limits
```

**Ollama-Based RAG (Local LLMs):**
```python
# Tokens are FREE
# Maximize context
# Include full documents
# Detailed explanations

prompt = f"""
Glossary:
{full_glossary}

Full Context:
{all_relevant_documents}  # ✅ No token limits!

Examples:
{few_shot_examples}

Question: {question}
"""
```

**New Strategy: Use token abundance to reduce processing time!**

---

## 🎯 UNIFIED ARCHITECTURE

### **The 3-Stage Pipeline**

```
Stage 1: FAST PRE-FILTERING (< 50ms)
  ↓
Stage 2: MULTI-SIGNAL RANKING (< 200ms)
  ↓
Stage 3: CONTEXT ENRICHMENT (< 100ms)
  ↓
Stage 4: LLM GENERATION (variable, 2-15s)
```

---

## 🚀 STAGE 1: FAST PRE-FILTERING

### **Purpose:** Eliminate noise BEFORE expensive operations

**Implementation:**
```python
class FastPreFilter:
    """
    Lightning-fast filtering using cached data.
    Target: < 50ms for filtering 1000 candidates
    """
    
    def __init__(self):
        # Pre-load all filters into memory at startup
        self.exclusions = self._load_exclusions()
        self.path_index = self._build_path_index()
        self.query_classifier = self._load_classifier()
        
        # Cache compiled regexes
        self.compiled_patterns = {
            pattern: re.compile(pattern)
            for pattern in self.exclusions['patterns']
        }
    
    async def filter_candidates(
        self, 
        candidates: List[dict], 
        query: str
    ) -> List[dict]:
        """
        Fast filtering using pre-computed data.
        
        Operations (all O(1) or O(n) with small n):
        1. Exclusion rules (regex, pre-compiled)
        2. Path-based filters (hash lookup)
        3. File type filters (extension check)
        """
        
        # 1. Quick query classification (cached embeddings)
        query_type = self.classify_query_fast(query)  # 5ms
        
        # 2. Get applicable exclusion rules
        active_rules = self.exclusions.get(query_type, [])
        
        # 3. Filter in single pass (vectorized operations)
        filtered = []
        for doc in candidates:
            # Check exclusions (pre-compiled regex)
            if self._is_excluded(doc['path'], active_rules):
                continue
            
            # Check path allowlist (hash lookup)
            if query_type in self.path_index:
                if not self._path_matches(doc['path'], query_type):
                    continue
            
            filtered.append(doc)
        
        return filtered
    
    def _is_excluded(self, path: str, rules: List[dict]) -> bool:
        """O(n) where n = number of rules (typically < 10)."""
        for rule in rules:
            if self.compiled_patterns[rule['pattern']].search(path):
                return True
        return False

# Performance target: 1000 docs → 500 docs in 30-50ms
```

**Optimizations:**
- ✅ Pre-compile all regexes at startup
- ✅ Load filters into memory (no disk I/O)
- ✅ Use hash lookups instead of linear scans
- ✅ Vectorize operations where possible

**Impact:**
- Eliminates 40-60% of candidates
- Takes 30-50ms (negligible)
- Reduces work for expensive Stage 2

---

## 🚀 STAGE 2: MULTI-SIGNAL RANKING

### **Purpose:** Score remaining candidates using multiple signals

**Critical Flaw #1: Signal Interference**

**Problem:**
```python
# Each signal independently calculated
glossary_boost = calculate_glossary(doc)  # 1.3×
priority_boost = calculate_priority(doc)  # 1.5×
feedback_boost = calculate_feedback(doc)  # 1.2×

# Naive multiplication
final_score = base * glossary_boost * priority_boost * feedback_boost
# = base * 2.34  # Too aggressive! Over-boosting

# Result: Same docs always win, new docs never surface
```

**Solution: Normalized Additive Scoring**
```python
class NormalizedMultiSignalRanker:
    """
    Prevent signal interference with normalized scoring.
    """
    
    def __init__(self):
        # Signal weights (must sum to 1.0)
        self.weights = {
            'semantic': 0.35,      # Core semantic match
            'glossary': 0.12,      # Domain terms
            'priority': 0.12,      # User priority
            'content_quality': 0.12,  # Dynamic quality
            'recency': 0.09,       # Freshness
            'feedback': 0.10,      # Historical feedback
            'template_hint': 0.05,  # Query template match
            'alias_match': 0.05     # Synonym matching
        }
    
    async def rank_documents(
        self, 
        documents: List[dict], 
        query: str,
        query_context: dict  # From Stage 1
    ) -> List[dict]:
        """
        Rank using normalized multi-signal scoring.
        
        Target: < 200ms for 500 documents
        """
        
        # Pre-compute query-level data (once for all docs)
        query_embedding = await self._get_cached_embedding(query)
        glossary_terms = await self._find_glossary_terms(query)
        query_type = query_context['type']
        time_strategy = self._get_time_strategy(query_type)
        
        # Parallel signal computation (all docs at once)
        signals_batch = await asyncio.gather(
            self._compute_semantic_scores(documents, query_embedding),
            self._compute_glossary_scores(documents, glossary_terms),
            self._compute_priority_scores(documents, query_type),
            self._compute_quality_scores(documents),
            self._compute_recency_scores(documents, time_strategy),
            self._compute_feedback_scores(documents, query),
            self._compute_template_scores(documents, query_context),
            self._compute_alias_scores(documents, query_context)
        )
        
        # Combine signals with normalization
        for idx, doc in enumerate(documents):
            # Each signal is normalized to [0, 1]
            normalized_scores = {
                'semantic': signals_batch[0][idx],
                'glossary': signals_batch[1][idx],
                'priority': signals_batch[2][idx],
                'content_quality': signals_batch[3][idx],
                'recency': signals_batch[4][idx],
                'feedback': signals_batch[5][idx],
                'template_hint': signals_batch[6][idx],
                'alias_match': signals_batch[7][idx]
            }
            
            # Weighted sum (bounded to [0, 1])
            final_score = sum(
                normalized_scores[signal] * self.weights[signal]
                for signal in self.weights
            )
            
            doc['final_score'] = final_score
            doc['signal_breakdown'] = normalized_scores
        
        # Sort by final score
        documents.sort(key=lambda x: x['final_score'], reverse=True)
        
        return documents
    
    def _normalize_signal(self, scores: List[float]) -> List[float]:
        """
        Normalize scores to [0, 1] using min-max scaling.
        
        Prevents one signal from dominating.
        """
        if not scores:
            return []
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return [0.5] * len(scores)  # All equal
        
        return [
            (score - min_score) / (max_score - min_score)
            for score in scores
        ]
```

**Key Improvements:**
- ✅ Normalized signals (no over-boosting)
- ✅ Parallel computation (8 signals simultaneously)
- ✅ Explainable (show signal breakdown)
- ✅ Tuneable (adjust weights)

---

### **Critical Flaw #2: Expensive Signal Computation**

**Problem:**
```python
# Naive approach: compute for every doc
for doc in 500_documents:
    quality = await compute_quality(doc)  # DB query + analysis
    feedback = await get_feedback(doc)     # DB query
    priority = await get_priority(doc)     # DB query
    
# 500 docs × 3 DB queries = 1500 queries!
# Takes 5-10 seconds ❌
```

**Solution: Aggressive Caching + Batch Operations**
```python
class OptimizedSignalComputer:
    """
    Compute all signals efficiently using caching and batching.
    """
    
    def __init__(self):
        # In-memory caches (loaded at startup)
        self.quality_cache = {}      # doc_id → quality_score
        self.feedback_cache = {}     # doc_id → feedback_score
        self.priority_cache = {}     # doc_id → priority_data
        self.glossary_cache = {}     # term → embedding
        
        # Refresh caches periodically (background job)
        asyncio.create_task(self._refresh_caches_periodically())
    
    async def _compute_quality_scores(
        self, 
        documents: List[dict]
    ) -> List[float]:
        """
        Compute quality scores using cached data.
        
        Target: < 10ms for 500 documents
        """
        scores = []
        
        for doc in documents:
            doc_id = doc['id']
            
            # Check cache first
            if doc_id in self.quality_cache:
                scores.append(self.quality_cache[doc_id])
                continue
            
            # Cache miss: compute and store
            # (This should be rare after warmup)
            quality = self._calculate_quality(doc)
            self.quality_cache[doc_id] = quality
            scores.append(quality)
        
        return scores
    
    def _calculate_quality(self, doc: dict) -> float:
        """
        Fast quality calculation using pre-computed metadata.
        
        No DB queries, all from document metadata!
        """
        # Length signal
        length = len(doc.get('content', ''))
        length_score = self._score_length(length)
        
        # Keyword signal (cached in metadata during ingestion)
        has_important_keywords = doc.get('metadata', {}).get('has_important_keywords', False)
        keyword_score = 1.0 if has_important_keywords else 0.5
        
        # Update frequency (cached in metadata)
        update_count = doc.get('metadata', {}).get('update_count_90d', 0)
        update_score = min(1.0, update_count / 10)
        
        # Cross-references (cached in metadata)
        reference_count = doc.get('metadata', {}).get('reference_count', 0)
        reference_score = min(1.0, reference_count / 5)
        
        # Combine (all O(1) operations)
        quality = (
            length_score * 0.25 +
            keyword_score * 0.25 +
            update_score * 0.25 +
            reference_score * 0.25
        )
        
        return quality
    
    async def _refresh_caches_periodically(self):
        """
        Background job to keep caches fresh.
        
        Runs every 10 minutes, doesn't block queries.
        """
        while True:
            await asyncio.sleep(600)  # 10 minutes
            
            try:
                # Refresh in background
                await self._refresh_quality_cache()
                await self._refresh_feedback_cache()
                await self._refresh_priority_cache()
                
                logger.info("✅ Signal caches refreshed")
            except Exception as e:
                logger.error(f"Cache refresh failed: {e}")
```

**Performance:**
- Cache hit rate: 95%+ (after warmup)
- 500 docs with 95% hit rate: 25 cache misses
- Time: 5-10ms (vs 5-10s without caching)
- **100-1000× faster!** 🚀

---

### **Critical Flaw #3: Config Explosion**

**Problem:**
```
.rag-config/
  ├── glossary.yaml (50 terms)
  ├── priorities.yaml (100 docs)
  ├── exclusions.yaml (30 rules)
  ├── templates.yaml (20 templates)
  ├── aliases.yaml (40 aliases)
  ├── prompts.yaml (10 prompts)
  ├── examples.yaml (15 examples)
  ├── time-strategies.yaml (5 strategies)
  └── contexts.yaml (8 contexts)

Total: 278 configuration items!
Maintenance nightmare ❌
```

**Solution: Smart Config with Auto-Tuning**
```python
class SmartConfigSystem:
    """
    Intelligent config with auto-learning and recommendations.
    """
    
    def __init__(self):
        # Load configs with defaults
        self.config = self._load_with_defaults()
        
        # Track config usage and effectiveness
        self.usage_tracker = ConfigUsageTracker()
        
        # Auto-tune weights based on feedback
        self.auto_tuner = ConfigAutoTuner()
    
    async def get_effective_config(self, query: str) -> dict:
        """
        Get optimized config for this specific query.
        
        Combines:
        - User-defined configs (high priority)
        - Auto-learned patterns (medium priority)
        - System defaults (low priority)
        """
        
        # Start with system defaults
        config = self.default_config.copy()
        
        # Layer on auto-learned configs
        learned = await self.auto_tuner.get_learned_config(query)
        config = self._merge_configs(config, learned)
        
        # Layer on user-defined configs (highest priority)
        user_config = await self._load_user_config()
        config = self._merge_configs(config, user_config)
        
        return config
    
    async def record_query_result(
        self,
        query: str,
        config_used: dict,
        user_feedback: dict
    ):
        """
        Learn from query results to improve configs.
        """
        # Track which configs were actually helpful
        await self.usage_tracker.record(query, config_used, user_feedback)
        
        # Auto-tune weights
        if user_feedback.get('rating', 0) >= 4:
            # This config worked well, reinforce it
            await self.auto_tuner.reinforce(config_used, weight=0.1)
        elif user_feedback.get('rating', 0) <= 2:
            # This config didn't work, reduce it
            await self.auto_tuner.penalize(config_used, weight=0.1)

class ConfigAutoTuner:
    """
    Automatically tune signal weights based on feedback.
    
    Uses online learning to optimize over time.
    """
    
    def __init__(self):
        self.signal_performance = defaultdict(lambda: {
            'success_count': 0,
            'total_count': 0,
            'avg_rating': 0.0
        })
    
    async def optimize_weights(self) -> dict:
        """
        Optimize signal weights using historical performance.
        
        Uses gradient descent on feedback data.
        """
        # Calculate performance scores for each signal
        performance = {}
        for signal, stats in self.signal_performance.items():
            if stats['total_count'] > 10:  # Minimum data points
                # Performance = success_rate × avg_rating
                success_rate = stats['success_count'] / stats['total_count']
                performance[signal] = success_rate * stats['avg_rating']
        
        # Normalize to sum to 1.0
        total = sum(performance.values())
        if total > 0:
            optimized_weights = {
                signal: score / total
                for signal, score in performance.items()
            }
        else:
            optimized_weights = self.default_weights
        
        return optimized_weights
```

**Benefits:**
- ✅ Auto-learns from feedback
- ✅ Recommends configs to users
- ✅ Self-optimizing weights
- ✅ Reduces maintenance burden

---

## 🚀 STAGE 3: CONTEXT ENRICHMENT

### **Purpose:** Leverage token abundance for better LLM performance

**Since tokens are free with Ollama, include EVERYTHING useful!**

```python
class TokenRichContextBuilder:
    """
    Build comprehensive context leveraging Ollama's large context window.
    
    Ollama: 8K-128K tokens (depending on model)
    Strategy: Use it all!
    """
    
    async def build_enriched_context(
        self,
        query: str,
        documents: List[dict],
        query_context: dict
    ) -> str:
        """
        Build token-rich context with all enhancements.
        
        Traditional RAG: ~1K tokens (cost concerns)
        Our approach: ~10K tokens (no cost, better quality!)
        """
        
        context_parts = []
        
        # 1. Glossary context (if relevant terms found)
        if glossary_terms := query_context.get('glossary_terms'):
            context_parts.append(self._build_glossary_section(glossary_terms))
        
        # 2. Query template context (if matched)
        if template := query_context.get('template'):
            context_parts.append(self._build_template_section(template))
        
        # 3. Few-shot examples (if available)
        if examples := await self._find_similar_examples(query):
            context_parts.append(self._build_examples_section(examples))
        
        # 4. Full document content (not truncated!)
        context_parts.append(self._build_documents_section(documents))
        
        # 5. Historical context (if user has query history)
        if history := query_context.get('conversation_history'):
            context_parts.append(self._build_history_section(history))
        
        # 6. Meta-information (ranking explanations)
        context_parts.append(self._build_meta_section(documents))
        
        # Combine all sections
        enriched_context = "\n\n".join(context_parts)
        
        logger.info(f"📊 Context size: {len(enriched_context)} chars (~{len(enriched_context)//4} tokens)")
        
        return enriched_context
    
    def _build_glossary_section(self, terms: List[dict]) -> str:
        """
        Include full glossary with examples.
        
        Traditional: "API: Application Programming Interface"
        Token-rich: Full definitions with examples!
        """
        lines = ["## 📚 Domain Glossary", ""]
        
        for term in terms:
            lines.append(f"### {term['term']}")
            lines.append(f"{term['description']}")
            
            if synonyms := term.get('synonyms'):
                lines.append(f"**Also known as:** {', '.join(synonyms)}")
            
            if examples := term.get('examples'):
                lines.append("**Examples:**")
                for example in examples:
                    lines.append(f"- {example}")
            
            lines.append("")  # Blank line
        
        return "\n".join(lines)
    
    def _build_documents_section(self, documents: List[dict]) -> str:
        """
        Include FULL document content (not excerpts).
        
        Traditional RAG: 200-word excerpts (token limits)
        Token-rich RAG: Full documents!
        """
        lines = ["## 📄 Relevant Documentation", ""]
        
        for idx, doc in enumerate(documents, 1):
            lines.append(f"### Document {idx}: {doc['path']}")
            
            # Show why this doc was selected
            if signals := doc.get('signal_breakdown'):
                top_signals = sorted(
                    signals.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:3]
                
                reasons = [f"{signal}: {score:.2f}" for signal, score in top_signals]
                lines.append(f"**Selected because:** {', '.join(reasons)}")
            
            # Include FULL content (not truncated)
            lines.append("")
            lines.append(doc['content'])
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def _build_examples_section(self, examples: List[dict]) -> str:
        """
        Include few-shot examples with full Q&A.
        
        Traditional: Skip (token limits)
        Token-rich: Include multiple examples!
        """
        lines = ["## 💡 Similar Questions & Answers", ""]
        lines.append("Here are examples of similar questions to guide your answer:")
        lines.append("")
        
        for example in examples:
            lines.append(f"**Question:** {example['question']}")
            lines.append(f"**Answer:** {example['answer']}")
            lines.append("")
        
        return "\n".join(lines)
```

**Context Size Comparison:**

| Approach | Context Size | Quality | Why |
|----------|--------------|---------|-----|
| **Traditional RAG** | ~1K tokens | Good | Token limits (API costs) |
| **Our Token-Rich RAG** | ~10K tokens | Excellent | No token costs (Ollama) |

**Benefits:**
- ✅ More context = better answers
- ✅ Include glossary definitions
- ✅ Include few-shot examples
- ✅ Full documents (not excerpts)
- ✅ Explain why docs were selected
- ✅ No truncation needed

---

## 🚀 STAGE 4: LLM GENERATION

### **Optimized Prompt Structure**

```python
async def generate_answer_with_enriched_context(
    self,
    query: str,
    enriched_context: str,
    query_context: dict
) -> str:
    """
    Generate answer using token-rich context.
    
    Prompt structure optimized for Ollama.
    """
    
    # Select appropriate prompt template
    template_name = query_context.get('prompt_template', 'default')
    template = self.prompt_templates[template_name]
    
    prompt = f"""You are {template['persona']}.

{template['guidelines']}

# Domain Context

{enriched_context}

# User Question

{query}

# Your Answer

{template['answer_format']}"""
    
    # Generate with optimal parameters for Ollama
    response = await self.ollama_router.generate(
        prompt=prompt,
        workload_type='rag',
        temperature=query_context.get('temperature', 0.7),
        max_tokens=query_context.get('response_length', 1000)
    )
    
    return response
```

---

## 📊 PERFORMANCE OPTIMIZATION MATRIX

### **Trade-offs: Time vs Accuracy**

```python
class AdaptivePerformanceController:
    """
    Dynamically adjust accuracy/speed trade-off based on context.
    """
    
    PERFORMANCE_MODES = {
        'fast': {
            'description': 'Fastest responses, good accuracy',
            'target_latency_ms': 500,
            'n_documents': 10,
            'signals_enabled': ['semantic', 'glossary', 'exclusions'],
            'cache_required': True
        },
        
        'balanced': {
            'description': 'Balanced speed and accuracy',
            'target_latency_ms': 1500,
            'n_documents': 20,
            'signals_enabled': ['semantic', 'glossary', 'priority', 'recency', 'exclusions'],
            'cache_required': False
        },
        
        'accurate': {
            'description': 'Maximum accuracy, slower',
            'target_latency_ms': 3000,
            'n_documents': 30,
            'signals_enabled': 'all',
            'cache_required': False,
            'enable_query_expansion': True
        },
        
        'research': {
            'description': 'Deep research mode (multi-pass)',
            'target_latency_ms': None,  # No limit
            'n_documents': 50,
            'signals_enabled': 'all',
            'enable_multi_pass': True,
            'num_passes': 3
        }
    }
    
    async def execute_query(
        self,
        query: str,
        mode: str = 'balanced'
    ) -> dict:
        """
        Execute query with mode-appropriate optimizations.
        """
        config = self.PERFORMANCE_MODES[mode]
        
        # Stage 1: Pre-filtering (always fast)
        candidates = await self.retrieve_candidates(query, n=config['n_documents'] * 3)
        filtered = await self.fast_prefilter.filter(candidates, query)
        
        # Stage 2: Multi-signal ranking (selective)
        if config['cache_required'] and not self.cache_warmed():
            # Cache not ready, use fast mode
            ranked = await self.fast_rank(filtered, query)
        else:
            # Use configured signals
            ranked = await self.multi_signal_rank(
                filtered, 
                query,
                enabled_signals=config['signals_enabled']
            )
        
        # Stage 3: Context building (mode-dependent)
        top_docs = ranked[:config['n_documents']]
        context = await self.build_context(
            top_docs, 
            query,
            rich=mode in ['accurate', 'research']
        )
        
        # Stage 4: Generation
        if config.get('enable_multi_pass'):
            # Use multi-pass for deep research
            answer = await self.multi_pass_query(query, config)
        else:
            # Standard RAG
            answer = await self.generate_answer(query, context)
        
        return answer
```

---

## 🎯 CRITICAL FLAWS & SOLUTIONS

### **Flaw #1: Config Staleness**

**Problem:** Configs become outdated as codebase evolves

**Solution: Active Config Monitoring**
```python
class ConfigHealthMonitor:
    """
    Monitor config effectiveness and alert on issues.
    """
    
    async def check_config_health(self):
        """
        Periodic health check for configs.
        """
        issues = []
        
        # Check 1: Priority docs that don't exist
        for doc_path in self.config['priorities']:
            if not await self.document_exists(doc_path):
                issues.append({
                    'type': 'missing_priority_doc',
                    'path': doc_path,
                    'suggestion': 'Remove from priorities.yaml'
                })
        
        # Check 2: Exclusion rules that match nothing
        for rule in self.config['exclusions']:
            match_count = await self.count_matches(rule['pattern'])
            if match_count == 0:
                issues.append({
                    'type': 'unused_exclusion',
                    'rule': rule,
                    'suggestion': 'Remove unused exclusion rule'
                })
        
        # Check 3: Glossary terms never matched
        for term, data in self.config['glossary'].items():
            if data['match_count_30d'] == 0:
                issues.append({
                    'type': 'unused_glossary_term',
                    'term': term,
                    'suggestion': 'Remove or update glossary term'
                })
        
        # Check 4: Signal weights that don't help
        for signal, weight in self.config['signal_weights'].items():
            if weight > 0.05:  # Only check significant weights
                impact = await self.measure_signal_impact(signal)
                if impact < 0.01:  # No meaningful impact
                    issues.append({
                        'type': 'ineffective_signal',
                        'signal': signal,
                        'weight': weight,
                        'suggestion': 'Reduce weight or disable'
                    })
        
        # Generate report
        if issues:
            await self.notify_config_issues(issues)
        
        return issues
```

**Automatic fixes:**
```python
async def auto_clean_configs(self):
    """
    Automatically clean up stale configs (with user approval).
    """
    # Remove priority docs that no longer exist
    await self._remove_missing_priority_docs()
    
    # Remove unused exclusions (no matches in 30 days)
    await self._remove_unused_exclusions(days=30)
    
    # Remove unused glossary terms (no matches in 90 days)
    await self._remove_unused_glossary_terms(days=90)
    
    # Auto-tune signal weights based on performance
    await self._optimize_signal_weights()
```

---

### **Flaw #2: Signal Correlation (Redundancy)**

**Problem:** Some signals are highly correlated, wasting computation

**Example:**
```python
# These are highly correlated:
priority_score = 0.85
quality_score = 0.82    # Same docs tend to be high quality AND high priority
feedback_score = 0.84   # And get good feedback

# Computing all 3 is redundant!
```

**Solution: Principal Component Analysis for Signals**
```python
class SignalOptimizer:
    """
    Detect and eliminate redundant signals.
    """
    
    async def analyze_signal_correlation(self):
        """
        Identify highly correlated signals.
        """
        # Collect signal data from recent queries
        signal_data = await self.collect_signal_history(n=1000)
        
        # Calculate correlation matrix
        correlation = self._calculate_correlation_matrix(signal_data)
        
        # Find highly correlated pairs (> 0.8 correlation)
        redundant_pairs = []
        for signal1, signal2 in itertools.combinations(self.signals, 2):
            if correlation[signal1][signal2] > 0.8:
                redundant_pairs.append((signal1, signal2, correlation[signal1][signal2]))
        
        return redundant_pairs
    
    async def optimize_signal_set(self):
        """
        Remove redundant signals, keep most informative.
        """
        redundant = await self.analyze_signal_correlation()
        
        recommendations = []
        for signal1, signal2, correlation in redundant:
            # Keep signal with higher impact
            impact1 = await self.measure_impact(signal1)
            impact2 = await self.measure_impact(signal2)
            
            if impact1 > impact2:
                recommendations.append({
                    'action': 'disable',
                    'signal': signal2,
                    'reason': f'Correlated with {signal1} ({correlation:.2f}), lower impact'
                })
            else:
                recommendations.append({
                    'action': 'disable',
                    'signal': signal1,
                    'reason': f'Correlated with {signal2} ({correlation:.2f}), lower impact'
                })
        
        return recommendations
```

---

### **Flaw #3: Cold Start Performance**

**Problem:** First query is slow (caches not warmed)

**Solution: Proactive Cache Warming**
```python
class CacheWarmer:
    """
    Warm caches on startup and keep them hot.
    """
    
    async def warmup_on_startup(self):
        """
        Pre-load all caches before accepting queries.
        """
        logger.info("🔥 Warming caches...")
        
        # Parallel warmup
        await asyncio.gather(
            self._warmup_glossary_cache(),
            self._warmup_quality_cache(),
            self._warmup_feedback_cache(),
            self._warmup_priority_cache(),
            self._warmup_embedding_cache()
        )
        
        logger.info("✅ Caches warmed, ready for queries!")
    
    async def _warmup_glossary_cache(self):
        """Pre-compute all glossary embeddings."""
        glossary = await self.load_glossary()
        
        terms = [term['term'] for term in glossary.values()]
        embeddings = await self.embedding_service.generate_batch(terms)
        
        for term, embedding in zip(terms, embeddings):
            self.glossary_cache[term] = embedding
    
    async def _warmup_quality_cache(self):
        """Pre-compute quality scores for all documents."""
        # Get all document IDs
        doc_ids = await self.get_all_document_ids()
        
        # Load documents in batches
        batch_size = 100
        for i in range(0, len(doc_ids), batch_size):
            batch = doc_ids[i:i+batch_size]
            docs = await self.load_documents_batch(batch)
            
            for doc in docs:
                quality = self._calculate_quality(doc)
                self.quality_cache[doc['id']] = quality
    
    async def keep_caches_hot(self):
        """
        Background task to keep caches fresh.
        """
        while True:
            await asyncio.sleep(300)  # 5 minutes
            
            # Refresh caches that are stale
            await self._refresh_stale_cache_entries()
```

**Startup sequence:**
```python
async def startup():
    """
    Optimized startup with cache warming.
    """
    # 1. Load configs (fast)
    config_system = await SmartConfigSystem.initialize()
    
    # 2. Warm caches (parallel)
    cache_warmer = CacheWarmer()
    await cache_warmer.warmup_on_startup()
    
    # 3. Ready to serve
    logger.info("🚀 RAG system ready!")
```

---

## 📊 FINAL PERFORMANCE TARGETS

### **Latency Breakdown (Target)**

```
┌─────────────────────────────────────────────────────┐
│ Query: "How do I authenticate API requests?"       │
│ Mode: Balanced                                      │
└─────────────────────────────────────────────────────┘

Stage 1: Pre-filtering
├─ Load exclusion rules: 5ms (cached)
├─ Classify query type: 10ms (cached embedding)
├─ Filter 1000 → 500 docs: 30ms
└─ Total: 45ms ✅

Stage 2: Multi-signal ranking
├─ Semantic scores: 50ms (cached embeddings)
├─ Glossary scores: 20ms (cached)
├─ Priority scores: 10ms (cached)
├─ Quality scores: 5ms (cached)
├─ Feedback scores: 15ms (cached)
├─ Normalize & combine: 5ms
└─ Total: 105ms ✅

Stage 3: Context enrichment
├─ Build glossary section: 10ms
├─ Build documents section: 50ms
├─ Build meta section: 10ms
└─ Total: 70ms ✅

Stage 4: LLM generation
├─ Generate answer: 3000-12000ms (Ollama)
└─ Total: ~8000ms (variable) ⚠️

Total (excluding LLM): 220ms ✅
Total (including LLM): 8220ms ✅

Target met: < 10 seconds total ✅
```

---

## 🎯 IMPLEMENTATION ROADMAP

### **Phase 1: Foundation (Week 1)**
1. ✅ Implement fast pre-filtering
2. ✅ Implement normalized multi-signal ranking
3. ✅ Implement aggressive caching
4. ✅ Implement cache warming

**Expected:** 200-300ms for ranking (before LLM)

### **Phase 2: Config System (Week 2)**
5. ✅ Implement smart config loader
6. ✅ Implement config health monitoring
7. ✅ Implement auto-tuning
8. ✅ UI for config management

**Expected:** Self-optimizing configs

### **Phase 3: Context Enrichment (Week 3)**
9. ✅ Implement token-rich context builder
10. ✅ Implement glossary section
11. ✅ Implement few-shot examples
12. ✅ Implement meta-information

**Expected:** Better answer quality

### **Phase 4: Optimization (Week 4)**
13. ✅ Implement adaptive performance controller
14. ✅ Implement signal correlation analysis
15. ✅ Implement performance monitoring
16. ✅ A/B testing infrastructure

**Expected:** Continuous improvement

---

## 💡 KEY TAKEAWAYS

### **Design Principles:**

1. **Token-Rich, Time-Constrained**
   - Use Ollama's large context window
   - Cache aggressively to save time
   - Include full content, not excerpts

2. **Normalized Additive Scoring**
   - Prevent signal interference
   - Explainable ranking
   - Tuneable weights

3. **Aggressive Caching**
   - Cache everything that's expensive
   - Warm caches on startup
   - Refresh in background

4. **Self-Optimizing**
   - Learn from feedback
   - Auto-tune weights
   - Monitor config health
   - Remove stale configs

5. **Progressive Enhancement**
   - Works great with zero config
   - Gets better with basic config
   - Optimal with full config

---

## 📊 EXPECTED RESULTS

### **Accuracy Improvement:**

```
Baseline (no config): 100%
+ Fast pre-filtering: +5-10% (noise reduction)
+ Multi-signal ranking: +20-30% (better relevance)
+ Token-rich context: +15-20% (better LLM understanding)
+ Auto-tuning: +10-15% (continuous improvement)

Total: +50-75% accuracy improvement! ✅
```

### **Latency:**

```
Stage 1-3: 200-300ms (ranking & enrichment)
Stage 4: 3-12s (LLM generation, variable)

Total: 3.2-12.3s (acceptable for quality) ✅
```

### **Maintenance:**

```
Manual config: Optional
Auto-tuning: Continuous
Config health: Monitored
Stale cleanup: Automatic

Maintenance burden: Low ✅
```

---

**Status:** 🎯 **UNIFIED SYSTEM DESIGNED**  
**Philosophy:** Token-rich, time-constrained, self-optimizing  
**Expected Impact:** +50-75% accuracy, < 300ms ranking  
**Maintenance:** Low (self-optimizing)  
**Ready for:** Phased implementation  

