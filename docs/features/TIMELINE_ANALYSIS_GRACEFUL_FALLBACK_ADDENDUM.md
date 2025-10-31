# Timeline Analysis: Graceful Fallback & Confidence System
## Addendum to Final Refined Plan (v3.1)

**Critical Issue Identified:** Not all documents have temporal versioning!  
**Validation:** Codebase supports both `git_history` and `snapshot` ingestion modes  
**Impact:** Timeline features must gracefully handle missing temporal data

---

## Table of Contents

1. [Validation Findings](#validation-findings)
2. [Temporal Confidence System](#temporal-confidence-system)
3. [Graceful Fallback Strategies](#graceful-fallback-strategies)
4. [Decision Matrix](#decision-matrix)
5. [Implementation Guidelines](#implementation-guidelines)

---

## Validation Findings

### Confirmed: Two Ingestion Modes

#### Mode 1: `git_history` (Full Temporal Data)
```python
# DocumentModel fields when ingestion_mode='git_history'
{
    "ingestion_mode": "git_history",
    "git_commit_sha": "a1b2c3d4...",  # ✅ Available
    "version": 1,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "commit": {  # ✅ Full commit data via relationship
        "sha": "a1b2c3d4...",
        "author": "John Doe",
        "date": "2024-01-15T10:30:00Z",
        "message": "Add authentication feature"
    }
}
```

**Temporal Capabilities:**
- ✅ Full commit history
- ✅ Accurate timestamps
- ✅ Author information
- ✅ Change messages
- ✅ Can build confident timelines
- ✅ Can track evolution accurately

#### Mode 2: `snapshot` (Limited Temporal Data)
```python
# DocumentModel fields when ingestion_mode='snapshot'
{
    "ingestion_mode": "snapshot",
    "git_commit_sha": None,  # ❌ Not available
    "version": 1,  # Incremental, not tied to commits
    "created_at": "2024-10-22T15:45:00Z",  # Ingestion time, not creation time
    "updated_at": "2024-10-22T15:45:00Z",  # Same as created_at initially
    "commit": None  # ❌ No commit relationship
}
```

**Temporal Capabilities:**
- ❌ No commit history
- ⚠️ Timestamps are ingestion times, not actual creation times
- ❌ No author information
- ❌ No change messages
- ❌ Cannot build confident timelines
- ❌ Cannot track evolution accurately

### Key Constraints

1. **`git_commit_sha` is nullable** - Can be `NULL` for snapshot mode
2. **`created_at`/`updated_at`** - In snapshot mode, these reflect ingestion time, not actual file creation/modification
3. **`version`** - In snapshot mode, this is just an incremental counter, not tied to actual history
4. **No `DocumentVersionModel` entries** - Snapshot mode doesn't create version history entries

---

## Temporal Confidence System

### Confidence Levels

```python
class TemporalConfidence(Enum):
    """
    Confidence level for temporal analysis.
    """
    HIGH = "high"        # Full git history, accurate timestamps
    MEDIUM = "medium"    # Partial data, some inference possible
    LOW = "low"          # Minimal data, high uncertainty
    NONE = "none"        # No temporal data, cannot analyze
```

### Confidence Calculator

```python
class TemporalConfidenceCalculator:
    """
    Calculates confidence level for temporal analysis.
    """
    
    async def calculate_confidence(
        self,
        documents: List[DocumentModel]
    ) -> Dict[str, Any]:
        """
        Calculate temporal confidence for a set of documents.
        
        Returns:
            {
                "confidence": TemporalConfidence,
                "score": float (0.0-1.0),
                "reasons": List[str],
                "capabilities": Dict[str, bool],
                "fallback_strategy": str
            }
        """
        if not documents:
            return {
                "confidence": TemporalConfidence.NONE,
                "score": 0.0,
                "reasons": ["No documents provided"],
                "capabilities": self._no_capabilities(),
                "fallback_strategy": "error"
            }
        
        # Count documents by mode
        git_history_count = sum(1 for d in documents if d.ingestion_mode == 'git_history')
        snapshot_count = sum(1 for d in documents if d.ingestion_mode == 'snapshot')
        total = len(documents)
        
        # Calculate git history percentage
        git_percentage = git_history_count / total if total > 0 else 0.0
        
        # Determine confidence level
        if git_percentage >= 0.9:
            # 90%+ have git history
            confidence = TemporalConfidence.HIGH
            score = 0.9 + (git_percentage - 0.9)
            reasons = [
                f"{git_history_count}/{total} documents have full git history",
                "Can perform accurate temporal analysis"
            ]
            capabilities = self._high_capabilities()
            fallback_strategy = "none_needed"
            
        elif git_percentage >= 0.5:
            # 50-90% have git history
            confidence = TemporalConfidence.MEDIUM
            score = 0.5 + (git_percentage - 0.5) * 0.8
            reasons = [
                f"{git_history_count}/{total} documents have git history",
                f"{snapshot_count} documents lack temporal data",
                "Can perform limited temporal analysis with gaps"
            ]
            capabilities = self._medium_capabilities()
            fallback_strategy = "partial_with_warnings"
            
        elif git_percentage > 0:
            # 1-50% have git history
            confidence = TemporalConfidence.LOW
            score = git_percentage * 0.5
            reasons = [
                f"Only {git_history_count}/{total} documents have git history",
                f"{snapshot_count} documents lack temporal data",
                "Temporal analysis will have significant gaps"
            ]
            capabilities = self._low_capabilities()
            fallback_strategy = "fallback_to_alternatives"
            
        else:
            # 0% have git history (all snapshot)
            confidence = TemporalConfidence.NONE
            score = 0.0
            reasons = [
                "All documents ingested in snapshot mode",
                "No git history available",
                "Cannot perform temporal analysis"
            ]
            capabilities = self._no_capabilities()
            fallback_strategy = "use_alternatives_only"
        
        return {
            "confidence": confidence,
            "score": score,
            "reasons": reasons,
            "capabilities": capabilities,
            "fallback_strategy": fallback_strategy,
            "git_history_count": git_history_count,
            "snapshot_count": snapshot_count,
            "total_documents": total
        }
    
    def _high_capabilities(self) -> Dict[str, bool]:
        """Capabilities with high confidence."""
        return {
            "timeline_creation": True,
            "period_generation": True,
            "evolution_tracking": True,
            "drift_detection": True,
            "gap_analysis": True,
            "temporal_rag": True,
            "historical_context": True,
            "change_attribution": True,
            "accurate_timestamps": True
        }
    
    def _medium_capabilities(self) -> Dict[str, bool]:
        """Capabilities with medium confidence."""
        return {
            "timeline_creation": True,  # With gaps
            "period_generation": True,  # Partial
            "evolution_tracking": True,  # Limited
            "drift_detection": True,    # Partial
            "gap_analysis": True,       # Can detect gaps
            "temporal_rag": True,       # With warnings
            "historical_context": False, # Unreliable
            "change_attribution": False, # Cannot attribute changes
            "accurate_timestamps": False # Mixed accuracy
        }
    
    def _low_capabilities(self) -> Dict[str, bool]:
        """Capabilities with low confidence."""
        return {
            "timeline_creation": False,  # Too many gaps
            "period_generation": False,  # Unreliable
            "evolution_tracking": False, # Cannot track
            "drift_detection": False,    # Cannot detect
            "gap_analysis": True,        # Can identify lack of data
            "temporal_rag": False,       # Not reliable
            "historical_context": False,
            "change_attribution": False,
            "accurate_timestamps": False
        }
    
    def _no_capabilities(self) -> Dict[str, bool]:
        """No temporal capabilities."""
        return {
            "timeline_creation": False,
            "period_generation": False,
            "evolution_tracking": False,
            "drift_detection": False,
            "gap_analysis": False,
            "temporal_rag": False,
            "historical_context": False,
            "change_attribution": False,
            "accurate_timestamps": False
        }
```

---

## Graceful Fallback Strategies

### Strategy 1: Pre-Flight Validation

**When:** Before any timeline operation  
**Purpose:** Check if temporal analysis is possible

```python
class TimelineManager:
    """
    Timeline manager with pre-flight validation.
    """
    
    async def create_timeline(
        self,
        name: str,
        repo_id: str,
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create timeline with pre-flight validation.
        """
        # Step 1: Get documents for this repository
        doc_repo = DocumentRepository(session)
        documents = await doc_repo.get_by_service(repo_id)
        
        # Step 2: Calculate temporal confidence
        confidence_calc = TemporalConfidenceCalculator()
        confidence = await confidence_calc.calculate_confidence(documents)
        
        # Step 3: Decide whether to proceed
        if confidence["confidence"] == TemporalConfidence.NONE:
            # Cannot create timeline
            return {
                "success": False,
                "error": "insufficient_temporal_data",
                "message": "Cannot create timeline: all documents lack git history",
                "confidence": confidence,
                "suggestion": "Re-ingest repository in git_history mode to enable temporal analysis",
                "alternative": "Use snapshot-based features instead (coverage analysis, quality metrics, etc.)"
            }
        
        elif confidence["confidence"] == TemporalConfidence.LOW:
            # Warn user but allow creation
            logger.warning(
                f"⚠️ Creating timeline with LOW confidence: "
                f"{confidence['git_history_count']}/{confidence['total_documents']} "
                f"documents have git history"
            )
            
            # Create timeline but mark as low confidence
            timeline = await self._create_timeline_internal(
                name, repo_id, start_date, end_date,
                confidence_level=confidence["confidence"],
                confidence_score=confidence["score"],
                **kwargs
            )
            
            return {
                "success": True,
                "timeline": timeline,
                "warning": "Timeline created with low confidence",
                "confidence": confidence,
                "limitations": [
                    "Significant gaps in temporal data",
                    "Evolution tracking will be incomplete",
                    "Drift detection may miss changes"
                ]
            }
        
        else:
            # Medium or high confidence - proceed normally
            timeline = await self._create_timeline_internal(
                name, repo_id, start_date, end_date,
                confidence_level=confidence["confidence"],
                confidence_score=confidence["score"],
                **kwargs
            )
            
            return {
                "success": True,
                "timeline": timeline,
                "confidence": confidence
            }
```

### Strategy 2: Feature-Level Fallbacks

**When:** Individual features encounter missing data  
**Purpose:** Gracefully degrade to alternative approaches

```python
class TemporalAnalysisEngine:
    """
    Temporal analysis with fallback strategies.
    """
    
    async def analyze_period(
        self,
        period_id: str,
        timeline_id: str
    ) -> AnalysisReport:
        """
        Analyze period with fallback to snapshot analysis.
        """
        # Get period documents
        period = await self._get_period(period_id, timeline_id)
        documents = await self._get_period_documents(period)
        
        # Check confidence
        confidence_calc = TemporalConfidenceCalculator()
        confidence = await confidence_calc.calculate_confidence(documents)
        
        if confidence["confidence"] in [TemporalConfidence.HIGH, TemporalConfidence.MEDIUM]:
            # Use temporal analysis
            logger.info(f"✅ Using temporal analysis (confidence: {confidence['confidence']})")
            return await self._analyze_with_git_history(period, documents)
        
        else:
            # Fallback to snapshot analysis
            logger.warning(
                f"⚠️ Falling back to snapshot analysis "
                f"(confidence: {confidence['confidence']})"
            )
            return await self._analyze_without_git_history(period, documents)
    
    async def _analyze_with_git_history(
        self,
        period: TimePeriod,
        documents: List[DocumentModel]
    ) -> AnalysisReport:
        """
        Full temporal analysis using git history.
        """
        # Use existing AnalysisEngine with commit context
        analysis_engine = get_analysis_engine()
        
        # Get commit information for context
        commits = [d.commit for d in documents if d.commit]
        
        # Run analysis with temporal context
        analysis = await analysis_engine.analyze(
            plan_id=f"period-{period.id}",
            files=[self._doc_to_file_dict(d) for d in documents],
            repo_path=period.repo_path
        )
        
        # Enhance with temporal metadata
        analysis.temporal_metadata = {
            "has_git_history": True,
            "commit_range": f"{period.start_commit_sha[:8]}..{period.end_commit_sha[:8]}",
            "commits_analyzed": len(commits),
            "confidence": "high"
        }
        
        return analysis
    
    async def _analyze_without_git_history(
        self,
        period: TimePeriod,
        documents: List[DocumentModel]
    ) -> AnalysisReport:
        """
        Snapshot analysis without git history.
        
        Limitations:
        - Cannot track changes over time
        - Cannot attribute changes to commits
        - Timestamps are ingestion times
        """
        # Use existing AnalysisEngine but without commit context
        analysis_engine = get_analysis_engine()
        
        # Run analysis on current state only
        analysis = await analysis_engine.analyze(
            plan_id=f"period-snapshot-{period.id}",
            files=[self._doc_to_file_dict(d) for d in documents],
            repo_path=period.repo_path
        )
        
        # Mark as snapshot-based
        analysis.temporal_metadata = {
            "has_git_history": False,
            "analysis_type": "snapshot",
            "confidence": "none",
            "limitations": [
                "No commit history available",
                "Timestamps reflect ingestion time, not creation time",
                "Cannot track evolution or changes",
                "Cannot detect drift"
            ],
            "warning": "This analysis represents current state only"
        }
        
        return analysis
```

### Strategy 3: Hybrid Approach

**When:** Mixed git_history and snapshot documents  
**Purpose:** Use best available data for each document

```python
class DriftDetector:
    """
    Drift detector with hybrid approach.
    """
    
    async def compare_periods(
        self,
        period1_id: str,
        period2_id: str
    ) -> Dict[str, Any]:
        """
        Compare periods with hybrid approach.
        """
        # Get documents for both periods
        docs1 = await self._get_period_documents(period1_id)
        docs2 = await self._get_period_documents(period2_id)
        
        # Separate by ingestion mode
        git_docs1 = [d for d in docs1 if d.ingestion_mode == 'git_history']
        git_docs2 = [d for d in docs2 if d.ingestion_mode == 'git_history']
        
        snapshot_docs1 = [d for d in docs1 if d.ingestion_mode == 'snapshot']
        snapshot_docs2 = [d for d in docs2 if d.ingestion_mode == 'snapshot']
        
        # Calculate confidence for each set
        git_confidence = await self._calculate_confidence(git_docs1 + git_docs2)
        snapshot_confidence = await self._calculate_confidence(snapshot_docs1 + snapshot_docs2)
        
        result = {
            "comparison_type": "hybrid",
            "git_history_comparison": None,
            "snapshot_comparison": None,
            "overall_confidence": None,
            "warnings": []
        }
        
        # Compare git_history documents if we have enough
        if git_confidence["confidence"] in [TemporalConfidence.HIGH, TemporalConfidence.MEDIUM]:
            logger.info(f"✅ Comparing {len(git_docs1)} + {len(git_docs2)} git_history documents")
            result["git_history_comparison"] = await self._compare_with_git_history(
                git_docs1,
                git_docs2
            )
        else:
            result["warnings"].append(
                f"Insufficient git_history documents for temporal comparison "
                f"({len(git_docs1)} + {len(git_docs2)})"
            )
        
        # Compare snapshot documents using content-based approach
        if snapshot_docs1 or snapshot_docs2:
            logger.info(
                f"⚠️ Comparing {len(snapshot_docs1)} + {len(snapshot_docs2)} "
                f"snapshot documents (content-based only)"
            )
            result["snapshot_comparison"] = await self._compare_without_git_history(
                snapshot_docs1,
                snapshot_docs2
            )
            result["warnings"].append(
                "Snapshot documents compared by content only (no temporal context)"
            )
        
        # Calculate overall confidence
        if result["git_history_comparison"] and result["snapshot_comparison"]:
            result["overall_confidence"] = "mixed"
            result["warnings"].append(
                "Mixed confidence: git_history documents provide temporal context, "
                "snapshot documents provide current state only"
            )
        elif result["git_history_comparison"]:
            result["overall_confidence"] = git_confidence["confidence"]
        elif result["snapshot_comparison"]:
            result["overall_confidence"] = "low"
            result["warnings"].append(
                "All comparisons are content-based only (no temporal context)"
            )
        else:
            result["overall_confidence"] = "none"
            result["error"] = "No documents available for comparison"
        
        return result
```

### Strategy 4: Alternative Features for Snapshot Mode

**When:** Temporal analysis not possible  
**Purpose:** Provide value even without git history

```python
class SnapshotModeFeatures:
    """
    Features that work without git history.
    """
    
    async def analyze_current_state(
        self,
        repo_id: str
    ) -> Dict[str, Any]:
        """
        Analyze current state without temporal context.
        
        Available features:
        - Coverage analysis (current state)
        - Quality metrics (current state)
        - Consistency checking (current state)
        - Dependency analysis (current state)
        - Search and discovery
        """
        # Get all documents
        doc_repo = DocumentRepository(session)
        documents = await doc_repo.get_by_service(repo_id)
        
        # Run current-state analyses
        coverage = await self._analyze_coverage(documents)
        quality = await self._analyze_quality(documents)
        consistency = await self._check_consistency(documents)
        dependencies = await self._analyze_dependencies(documents)
        
        return {
            "analysis_type": "current_state",
            "temporal_analysis_available": False,
            "coverage": coverage,
            "quality": quality,
            "consistency": consistency,
            "dependencies": dependencies,
            "recommendation": (
                "Re-ingest in git_history mode to enable temporal analysis, "
                "evolution tracking, and drift detection"
            )
        }
    
    async def suggest_reingest_strategy(
        self,
        repo_id: str
    ) -> Dict[str, Any]:
        """
        Suggest strategy for re-ingesting to enable temporal features.
        """
        # Check current state
        doc_repo = DocumentRepository(session)
        documents = await doc_repo.get_by_service(repo_id)
        
        snapshot_count = sum(1 for d in documents if d.ingestion_mode == 'snapshot')
        
        if snapshot_count == 0:
            return {
                "needs_reingest": False,
                "message": "All documents have git history"
            }
        
        return {
            "needs_reingest": True,
            "snapshot_documents": snapshot_count,
            "total_documents": len(documents),
            "recommendation": {
                "action": "reingest_in_git_history_mode",
                "reason": "Enable temporal analysis and evolution tracking",
                "benefits": [
                    "Timeline creation and visualization",
                    "Evolution tracking",
                    "Drift detection",
                    "Gap analysis with root cause",
                    "Temporal RAG queries",
                    "Historical context in documentation"
                ],
                "estimated_time": self._estimate_reingest_time(len(documents)),
                "command": f"POST /api/v1/ingestion/start (mode='git_history', repo_id='{repo_id}')"
            }
        }
```

---

## Decision Matrix

### Timeline Creation

| Confidence | Action | User Experience |
|------------|--------|-----------------|
| **HIGH** (90%+ git) | ✅ Create timeline normally | Full features, no warnings |
| **MEDIUM** (50-90% git) | ⚠️ Create with warnings | Partial features, show gaps |
| **LOW** (1-50% git) | ⚠️ Warn strongly, allow if user confirms | Limited features, many gaps |
| **NONE** (0% git) | ❌ Block creation, suggest alternatives | Show snapshot-mode features instead |

### Period Analysis

| Confidence | Action | Fallback |
|------------|--------|----------|
| **HIGH** | Use temporal analysis | N/A |
| **MEDIUM** | Use temporal analysis with gap warnings | Mark gaps clearly |
| **LOW** | Use snapshot analysis | Content-based only |
| **NONE** | Use snapshot analysis | Content-based only |

### Drift Detection

| Confidence | Action | Fallback |
|------------|--------|----------|
| **HIGH** | Full drift detection | N/A |
| **MEDIUM** | Partial drift detection | Mark uncertain changes |
| **LOW** | Content comparison only | No attribution |
| **NONE** | Block feature | Suggest reingest |

### Temporal RAG

| Confidence | Action | Fallback |
|------------|--------|----------|
| **HIGH** | Full temporal queries | N/A |
| **MEDIUM** | Temporal queries with warnings | Mark uncertain dates |
| **LOW** | Standard RAG only | No temporal context |
| **NONE** | Standard RAG only | No temporal context |

### Documentation Generation

| Confidence | Action | Fallback |
|------------|--------|----------|
| **HIGH** | Include evolution sections | N/A |
| **MEDIUM** | Include partial evolution | Mark gaps |
| **LOW** | Skip evolution sections | Current state only |
| **NONE** | Skip evolution sections | Current state only |

---

## Implementation Guidelines

### 1. Add Confidence Metadata to Timeline Model

```python
# Extend TimelineModel
class TimelineModel(Base):
    __tablename__ = "timelines"
    
    # ... existing fields ...
    
    # NEW: Confidence tracking
    confidence_level = Column(String(20))  # high, medium, low, none
    confidence_score = Column(Float)  # 0.0 to 1.0
    git_history_percentage = Column(Float)  # % of docs with git history
    snapshot_percentage = Column(Float)  # % of docs without git history
    confidence_metadata = Column(JSONB)  # Detailed confidence info
```

### 2. Add Validation to All Timeline Endpoints

```python
# In timeline.py API routes
@router.post("/api/v1/timelines")
async def create_timeline(request: CreateTimelineRequest):
    """Create timeline with pre-flight validation."""
    
    # Validate temporal confidence
    confidence = await validate_temporal_confidence(request.repo_id)
    
    if confidence["confidence"] == TemporalConfidence.NONE:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "insufficient_temporal_data",
                "message": "Cannot create timeline: no git history available",
                "confidence": confidence,
                "suggestion": "Re-ingest in git_history mode"
            }
        )
    
    # Create timeline with confidence metadata
    timeline = await timeline_manager.create_timeline(
        **request.dict(),
        confidence_metadata=confidence
    )
    
    return {
        "success": True,
        "timeline": timeline,
        "confidence": confidence
    }
```

### 3. Add Warnings to UI

```python
# In dashboard (Streamlit)
def show_timeline_creation_form():
    """Timeline creation with confidence warnings."""
    
    repo_id = st.selectbox("Repository", get_repositories())
    
    # Check confidence
    confidence = check_temporal_confidence(repo_id)
    
    if confidence["confidence"] == "none":
        st.error("❌ Cannot create timeline: No git history available")
        st.info("💡 Re-ingest this repository in git_history mode to enable temporal analysis")
        st.button("Re-ingest Repository", on_click=trigger_reingest, args=(repo_id,))
        return
    
    elif confidence["confidence"] == "low":
        st.warning(
            f"⚠️ Low confidence: Only {confidence['git_history_percentage']:.1%} "
            f"of documents have git history"
        )
        st.info("Timeline will have significant gaps. Consider re-ingesting for better results.")
        
        if not st.checkbox("I understand the limitations"):
            return
    
    elif confidence["confidence"] == "medium":
        st.info(
            f"ℹ️ Medium confidence: {confidence['git_history_percentage']:.1%} "
            f"of documents have git history"
        )
    
    # Show creation form
    # ...
```

### 4. Document Limitations Clearly

```python
# Add to API responses
def format_timeline_response(timeline, confidence):
    """Format timeline response with confidence info."""
    
    response = {
        "timeline": timeline.to_dict(),
        "confidence": {
            "level": confidence["confidence"],
            "score": confidence["score"],
            "git_history_percentage": confidence["git_history_percentage"]
        }
    }
    
    # Add capabilities and limitations
    if confidence["confidence"] != "high":
        response["limitations"] = []
        
        if not confidence["capabilities"]["evolution_tracking"]:
            response["limitations"].append(
                "Evolution tracking unavailable (insufficient git history)"
            )
        
        if not confidence["capabilities"]["drift_detection"]:
            response["limitations"].append(
                "Drift detection unavailable (insufficient git history)"
            )
        
        if not confidence["capabilities"]["accurate_timestamps"]:
            response["limitations"].append(
                "Timestamps may be inaccurate (mix of git and ingestion times)"
            )
    
    return response
```

### 5. Provide Clear Upgrade Path

```python
class TimelineUpgradeHelper:
    """
    Helps users upgrade from snapshot to git_history mode.
    """
    
    async def suggest_upgrade(
        self,
        timeline_id: str
    ) -> Dict[str, Any]:
        """
        Suggest upgrade path for low-confidence timeline.
        """
        timeline = await self._get_timeline(timeline_id)
        
        if timeline.confidence_level in ["high", "medium"]:
            return {
                "needs_upgrade": False,
                "message": "Timeline has sufficient temporal data"
            }
        
        return {
            "needs_upgrade": True,
            "current_confidence": timeline.confidence_level,
            "current_score": timeline.confidence_score,
            "upgrade_benefits": [
                "Accurate evolution tracking",
                "Precise drift detection",
                "Historical context in documentation",
                "Temporal RAG queries",
                "Root cause analysis for gaps"
            ],
            "upgrade_steps": [
                {
                    "step": 1,
                    "action": "Re-ingest repository in git_history mode",
                    "command": f"POST /api/v1/ingestion/start",
                    "params": {
                        "mode": "git_history",
                        "repo_id": timeline.repo_id
                    }
                },
                {
                    "step": 2,
                    "action": "Rebuild timeline with new data",
                    "command": f"POST /api/v1/timelines/{timeline_id}/rebuild"
                },
                {
                    "step": 3,
                    "action": "Verify improved confidence",
                    "command": f"GET /api/v1/timelines/{timeline_id}/confidence"
                }
            ],
            "estimated_time": "2-4 hours for typical repository"
        }
```

---

## Summary

### Key Principles

1. **Always check confidence before temporal operations**
2. **Fail gracefully with clear error messages**
3. **Provide alternative features when temporal analysis not possible**
4. **Guide users to upgrade path (reingest in git_history mode)**
5. **Be transparent about limitations**

### Implementation Checklist

- [ ] Add `TemporalConfidenceCalculator` class
- [ ] Add confidence fields to `TimelineModel`
- [ ] Add pre-flight validation to all timeline endpoints
- [ ] Implement fallback strategies in all temporal features
- [ ] Add confidence warnings to dashboard UI
- [ ] Document limitations clearly in API responses
- [ ] Provide upgrade helper for low-confidence timelines
- [ ] Add tests for all confidence levels
- [ ] Add tests for all fallback strategies

### Benefits

✅ **Robust** - Handles all ingestion modes gracefully  
✅ **Transparent** - Users understand limitations  
✅ **Helpful** - Provides clear upgrade path  
✅ **Flexible** - Works with mixed data  
✅ **Safe** - Prevents misleading results

---

**Document Version:** 3.1 (Graceful Fallback Addendum)  
**Last Updated:** 2025-10-22  
**Status:** Ready for Implementation  
**Integration:** Extends v3.0 Final Refined Plan


