# Timeline Analysis: Dynamic Temporal RAG Enhancement
## Addendum v3.2 - Context-Driven Timeline Construction

**Purpose:** Enable dynamic timeline construction from RAG queries for highly contextual, temporally-aware answers  
**Status:** Ready for Implementation  
**Last Updated:** 2025-10-22  
**Extends:** v3.1 (Graceful Fallback Addendum)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Feature Overview](#feature-overview)
3. [Architecture](#architecture)
4. [Execution Flow](#execution-flow)
5. [Implementation Details](#implementation-details)
6. [API Specifications](#api-specifications)
7. [Integration Points](#integration-points)
8. [Examples](#examples)
9. [Testing Strategy](#testing-strategy)
10. [Success Metrics](#success-metrics)

---

## Executive Summary

### What We're Adding

A **Dynamic Temporal RAG** system that automatically constructs topic-specific timelines on-the-fly to answer user queries with full temporal context.

### Key Innovation

Instead of requiring users to manually create timelines, the system:
1. **Analyzes the query** using NLP to extract topics, technologies, endpoints, services
2. **Finds relevant documents** using semantic search
3. **Constructs a temporary timeline** around the extracted topics
4. **Performs temporal analysis** to understand evolution
5. **Synthesizes an answer** with full historical context
6. **Cites source documents** with temporal attribution

### Example Flow

```
User Query: "Why does the /api/auth endpoint require a 'refresh_token' parameter?"

System Actions:
1. Extract topics: ["auth endpoint", "refresh_token", "authentication"]
2. Find documents: 47 documents related to authentication
3. Build timeline: Auth system evolution (2023-01 to 2024-10)
4. Analyze: Detect when refresh_token was added (2024-03)
5. Synthesize: "The refresh_token parameter was added in March 2024..."
6. Cite: Links to commit, design doc, and migration guide

User receives: Comprehensive answer with full context and sources
```

### Benefits

- ✅ **No manual timeline creation** - Automatic and instant
- ✅ **Highly contextual answers** - Full temporal understanding
- ✅ **Accurate attribution** - Know when/why changes happened
- ✅ **Better than standard RAG** - Understands evolution, not just current state
- ✅ **Seamless UX** - Users just ask questions naturally

---

## Feature Overview

### Core Capabilities

#### 1. Topic Extraction from Queries

**Input:** Natural language query  
**Output:** Structured topic/entity list

```python
Query: "Why does the /api/auth endpoint require a 'refresh_token' parameter?"

Extracted Topics:
{
    "endpoints": ["/api/auth"],
    "parameters": ["refresh_token"],
    "services": ["authentication"],
    "technologies": ["JWT", "OAuth"],
    "concepts": ["token refresh", "session management"]
}
```

#### 2. Document Discovery

**Input:** Extracted topics  
**Output:** Relevant documents with relevance scores

```python
Discovered Documents (47 total):
- src/api/auth.py (relevance: 0.95, commits: 23)
- docs/authentication.md (relevance: 0.92, commits: 8)
- src/services/token_service.py (relevance: 0.89, commits: 15)
- MIGRATION_AUTH_V2.md (relevance: 0.87, commits: 1)
- ...
```

#### 3. Dynamic Timeline Construction

**Input:** Discovered documents  
**Output:** Temporary topic-specific timeline

```python
Timeline: "Authentication System Evolution"
- Scope: Documents related to auth, tokens, endpoints
- Period: 2023-01-15 to 2024-10-22
- Periods: 8 auto-generated periods
- Documents: 47 placed on timeline
- Confidence: HIGH (95% have git history)
```

#### 4. Temporal Analysis

**Input:** Timeline + specific question  
**Output:** Temporal analysis report

```python
Analysis Results:
- Initial state (2023-01): Basic auth with API keys
- Evolution (2023-06): JWT tokens introduced
- Breaking change (2024-03): Refresh tokens added
- Current state (2024-10): Full OAuth2 flow
- Reason: Security improvement, longer sessions
```

#### 5. Answer Synthesis

**Input:** Query + temporal analysis  
**Output:** Comprehensive answer with citations

```python
Synthesized Answer:
"The /api/auth endpoint requires a 'refresh_token' parameter because of a 
security enhancement implemented in March 2024 (commit a3b7c9d).

Initially (January 2023), the authentication system used simple API keys. 
In June 2023, JWT tokens were introduced for better security. However, 
these tokens had short expiration times (15 minutes), requiring frequent 
re-authentication.

The refresh_token parameter was added in March 2024 to solve this problem. 
It allows clients to obtain new access tokens without re-authenticating, 
improving user experience while maintaining security.

Sources:
- MIGRATION_AUTH_V2.md (2024-03-15): Migration guide
- src/api/auth.py (commit a3b7c9d, 2024-03-12): Implementation
- docs/authentication.md (updated 2024-03-20): Documentation
"
```

### Trigger Mechanisms

The system can be triggered by:

1. **Explicit RAG Queries** - User asks a question
2. **Documentation Reading** - User clicks "Explain this" on generated docs
3. **Technology Selection** - User selects a technology from a list
4. **Endpoint Selection** - User selects an API endpoint
5. **Service Selection** - User selects a service from architecture diagram
6. **Dependency Selection** - User clicks on a dependency in dependency graph

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Interface Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ RAG Query UI │  │ Doc Reader   │  │ Tech Browser │          │
│  │ (text input) │  │ (click explain)│ │ (select tech)│         │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Dynamic Temporal RAG Orchestrator (NEW)            │
│                                                                  │
│  Coordinates the entire flow from query to answer               │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Processing Pipeline (NEW)                     │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ Topic Extractor  │→│ Document Finder  │→│ Timeline      │ │
│  │ (NLP)            │  │ (Semantic Search)│  │ Constructor   │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
│                              ▼                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ Temporal         │→│ Answer           │→│ Citation      │ │
│  │ Analyzer         │  │ Synthesizer      │  │ Formatter     │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Existing Services (LEVERAGED 98%+)                 │
│                                                                  │
│  RAG Service │ Timeline Manager │ Analysis Engine │ Git Service │
│  Embedding   │ Doc Repository   │ Context-Aware RAG│ Versioner  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### New Components (6)

1. **DynamicTemporalRAGOrchestrator**
   - Coordinates entire flow
   - Manages temporary timelines
   - Caches results for performance
   - ~200 lines

2. **TopicExtractor**
   - Extracts topics/entities from queries
   - Uses NLP (spaCy, entity recognition)
   - Classifies into categories (endpoints, services, technologies)
   - ~150 lines

3. **DocumentFinder**
   - Finds documents related to topics
   - Uses semantic search + metadata filtering
   - Ranks by relevance
   - ~100 lines (thin wrapper over existing search)

4. **DynamicTimelineConstructor**
   - Builds temporary timelines from document sets
   - Auto-generates periods
   - Calculates confidence
   - ~150 lines (thin wrapper over TimelineManager)

5. **TemporalAnswerSynthesizer**
   - Combines temporal analysis with RAG
   - Generates narrative answers
   - Includes evolution context
   - ~200 lines

6. **CitationFormatter**
   - Formats citations with temporal context
   - Links to source documents and commits
   - Generates "See also" suggestions
   - ~100 lines

**Total New Code:** ~900 lines (thin facades over existing services)

---

## Execution Flow

### Detailed Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: User Query                                              │
└─────────────────────────────────────────────────────────────────┘
User: "Why does the /api/auth endpoint require a 'refresh_token' parameter?"
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Topic Extraction                                        │
│ Component: TopicExtractor                                       │
└─────────────────────────────────────────────────────────────────┘
Input: Query string
Process:
  - NLP parsing (spaCy)
  - Entity recognition (endpoints, parameters, services)
  - Technology detection (from known tech list)
  - Concept extraction (semantic analysis)
Output:
  {
    "endpoints": ["/api/auth"],
    "parameters": ["refresh_token"],
    "services": ["authentication", "token_service"],
    "technologies": ["JWT", "OAuth"],
    "concepts": ["token refresh", "session management"]
  }
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Document Discovery                                      │
│ Component: DocumentFinder                                       │
└─────────────────────────────────────────────────────────────────┘
Input: Extracted topics
Process:
  - Semantic search for each topic
  - Metadata filtering (file paths, technologies)
  - Relevance ranking
  - Deduplication
Output:
  [
    {
      "doc_id": "uuid-1",
      "file_path": "src/api/auth.py",
      "relevance": 0.95,
      "has_git_history": true,
      "commit_count": 23
    },
    {
      "doc_id": "uuid-2",
      "file_path": "docs/authentication.md",
      "relevance": 0.92,
      "has_git_history": true,
      "commit_count": 8
    },
    ... (47 total)
  ]
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Confidence Check                                        │
│ Component: TemporalConfidenceCalculator                         │
└─────────────────────────────────────────────────────────────────┘
Input: Discovered documents
Process:
  - Calculate git_history percentage
  - Determine confidence level
  - Decide on strategy
Output:
  {
    "confidence": "HIGH",
    "score": 0.95,
    "git_history_count": 45,
    "snapshot_count": 2,
    "strategy": "full_temporal_analysis"
  }

Decision:
  - HIGH/MEDIUM → Proceed with temporal analysis
  - LOW → Warn user, proceed with limited analysis
  - NONE → Fallback to standard RAG (no timeline)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Dynamic Timeline Construction                           │
│ Component: DynamicTimelineConstructor                           │
└─────────────────────────────────────────────────────────────────┘
Input: Discovered documents + confidence
Process:
  - Create temporary timeline
  - Auto-generate periods (monthly, quarterly, or by major commits)
  - Place documents on timeline
  - Store in cache (TTL: 1 hour)
Output:
  {
    "timeline_id": "temp-uuid-123",
    "name": "Authentication System Evolution",
    "start_date": "2023-01-15T00:00:00Z",
    "end_date": "2024-10-22T23:59:59Z",
    "periods": [
      {
        "id": "period-1",
        "name": "Initial Implementation",
        "start": "2023-01-15",
        "end": "2023-06-30",
        "document_count": 8
      },
      {
        "id": "period-2",
        "name": "JWT Migration",
        "start": "2023-07-01",
        "end": "2023-12-31",
        "document_count": 12
      },
      {
        "id": "period-3",
        "name": "Refresh Token Addition",
        "start": "2024-01-01",
        "end": "2024-03-31",
        "document_count": 15
      },
      ... (8 periods total)
    ],
    "confidence": "HIGH",
    "is_temporary": true,
    "expires_at": "2024-10-22T16:45:00Z"
  }
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: Temporal Analysis                                       │
│ Component: TemporalAnalysisEngine                               │
└─────────────────────────────────────────────────────────────────┘
Input: Timeline + original query
Process:
  - Analyze each period
  - Detect changes related to query topics
  - Identify breaking changes
  - Track evolution of concepts
  - Determine root causes
Output:
  {
    "evolution": [
      {
        "period": "Initial Implementation",
        "state": "Basic API key authentication",
        "relevant_changes": []
      },
      {
        "period": "JWT Migration",
        "state": "JWT tokens introduced",
        "relevant_changes": [
          {
            "type": "enhancement",
            "description": "Added JWT token support",
            "commit": "b2c4d6e",
            "date": "2023-06-15",
            "files": ["src/api/auth.py", "src/services/token_service.py"]
          }
        ]
      },
      {
        "period": "Refresh Token Addition",
        "state": "Refresh tokens added",
        "relevant_changes": [
          {
            "type": "breaking_change",
            "description": "Added refresh_token parameter to /api/auth",
            "commit": "a3b7c9d",
            "date": "2024-03-12",
            "files": ["src/api/auth.py"],
            "reason": "Improve UX by reducing re-authentication frequency"
          }
        ]
      }
    ],
    "key_insight": "refresh_token added in March 2024 to improve UX",
    "root_cause": "Short JWT expiration times (15 min) required frequent re-auth"
  }
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 7: Answer Synthesis                                        │
│ Component: TemporalAnswerSynthesizer                            │
└─────────────────────────────────────────────────────────────────┘
Input: Original query + temporal analysis
Process:
  - Generate narrative from temporal analysis
  - Use LLM to synthesize coherent answer
  - Include evolution context
  - Add "why" and "when" information
  - Maintain technical accuracy
Output:
  {
    "answer": "The /api/auth endpoint requires a 'refresh_token' parameter...",
    "sections": [
      {
        "title": "Current State",
        "content": "As of October 2024, the /api/auth endpoint..."
      },
      {
        "title": "Historical Context",
        "content": "Initially (January 2023), the authentication system..."
      },
      {
        "title": "Why This Change",
        "content": "The refresh_token parameter was added in March 2024..."
      }
    ]
  }
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 8: Citation Formatting                                     │
│ Component: CitationFormatter                                    │
└─────────────────────────────────────────────────────────────────┘
Input: Answer + temporal analysis
Process:
  - Extract source documents
  - Format citations with temporal context
  - Add commit links
  - Generate "See also" suggestions
Output:
  {
    "formatted_answer": "...",
    "citations": [
      {
        "id": 1,
        "type": "migration_guide",
        "title": "MIGRATION_AUTH_V2.md",
        "date": "2024-03-15",
        "commit": "a3b7c9d",
        "excerpt": "To migrate to the new authentication system..."
      },
      {
        "id": 2,
        "type": "code",
        "title": "src/api/auth.py",
        "date": "2024-03-12",
        "commit": "a3b7c9d",
        "line_range": "45-78",
        "excerpt": "def authenticate(username, password, refresh_token=None)..."
      }
    ],
    "see_also": [
      "How does token refresh work?",
      "What are the security implications of refresh tokens?",
      "How to migrate from API keys to JWT?"
    ]
  }
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 9: Response Delivery                                       │
└─────────────────────────────────────────────────────────────────┘
User receives:
  ✅ Comprehensive answer with full context
  ✅ Evolution timeline
  ✅ Source citations with dates and commits
  ✅ "See also" suggestions
  ✅ Confidence indicator
```

### Performance Optimizations

1. **Timeline Caching**
   - Cache temporary timelines for 1 hour
   - Reuse for similar queries
   - Key: hash of document IDs

2. **Parallel Processing**
   - Document discovery (parallel semantic searches)
   - Period analysis (parallel)
   - Citation formatting (parallel)

3. **Early Termination**
   - If confidence is NONE, skip timeline construction
   - Fallback to standard RAG immediately

4. **Incremental Results**
   - Stream answer sections as they're generated
   - Show "Analyzing..." progress indicators

---

## Implementation Details

### 1. DynamicTemporalRAGOrchestrator

```python
class DynamicTemporalRAGOrchestrator:
    """
    Orchestrates dynamic temporal RAG queries.
    
    Coordinates:
    - Topic extraction
    - Document discovery
    - Timeline construction
    - Temporal analysis
    - Answer synthesis
    - Citation formatting
    """
    
    def __init__(self):
        self.topic_extractor = TopicExtractor()
        self.doc_finder = DocumentFinder()
        self.timeline_constructor = DynamicTimelineConstructor()
        self.temporal_analyzer = TemporalAnalysisEngine()
        self.answer_synthesizer = TemporalAnswerSynthesizer()
        self.citation_formatter = CitationFormatter()
        self.cache = get_redis_client()
    
    async def query(
        self,
        query: str,
        repo_id: str,
        user_id: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Process a dynamic temporal RAG query.
        
        Args:
            query: User's natural language query
            repo_id: Repository to search in
            user_id: Optional user ID for personalization
            stream: Whether to stream results
        
        Returns:
            Complete answer with citations and temporal context
        """
        # Step 1: Extract topics
        if stream:
            yield {"status": "extracting_topics", "progress": 0.1}
        
        topics = await self.topic_extractor.extract(query)
        
        # Step 2: Find relevant documents
        if stream:
            yield {"status": "finding_documents", "progress": 0.2}
        
        documents = await self.doc_finder.find(
            topics=topics,
            repo_id=repo_id,
            limit=100
        )
        
        if not documents:
            # No documents found - fallback to standard RAG
            return await self._fallback_to_standard_rag(query, repo_id)
        
        # Step 3: Check confidence
        if stream:
            yield {"status": "checking_confidence", "progress": 0.3}
        
        confidence = await self._calculate_confidence(documents)
        
        if confidence["confidence"] == TemporalConfidence.NONE:
            # No git history - fallback to standard RAG
            logger.warning(f"No git history for query: {query}")
            return await self._fallback_to_standard_rag(
                query, repo_id,
                note="Documents found but lack git history"
            )
        
        # Step 4: Construct temporary timeline
        if stream:
            yield {"status": "building_timeline", "progress": 0.4}
        
        timeline = await self._get_or_create_timeline(
            documents=documents,
            topics=topics,
            confidence=confidence
        )
        
        # Step 5: Perform temporal analysis
        if stream:
            yield {"status": "analyzing_timeline", "progress": 0.6}
        
        analysis = await self.temporal_analyzer.analyze_for_query(
            timeline_id=timeline["timeline_id"],
            query=query,
            topics=topics
        )
        
        # Step 6: Synthesize answer
        if stream:
            yield {"status": "synthesizing_answer", "progress": 0.8}
        
        answer = await self.answer_synthesizer.synthesize(
            query=query,
            temporal_analysis=analysis,
            confidence=confidence
        )
        
        # Step 7: Format citations
        if stream:
            yield {"status": "formatting_citations", "progress": 0.9}
        
        formatted = await self.citation_formatter.format(
            answer=answer,
            analysis=analysis,
            timeline=timeline
        )
        
        # Step 8: Return complete response
        if stream:
            yield {"status": "complete", "progress": 1.0, "result": formatted}
        else:
            return formatted
    
    async def _get_or_create_timeline(
        self,
        documents: List[DocumentModel],
        topics: Dict[str, List[str]],
        confidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get cached timeline or create new one.
        """
        # Create cache key from document IDs
        doc_ids = sorted([str(d.id) for d in documents])
        cache_key = f"temp_timeline:{hashlib.md5(''.join(doc_ids).encode()).hexdigest()}"
        
        # Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info(f"✅ Using cached timeline: {cache_key}")
            return json.loads(cached)
        
        # Create new timeline
        timeline = await self.timeline_constructor.construct(
            documents=documents,
            topics=topics,
            confidence=confidence,
            is_temporary=True
        )
        
        # Cache for 1 hour
        await self.cache.setex(
            cache_key,
            3600,  # 1 hour TTL
            json.dumps(timeline)
        )
        
        logger.info(f"✅ Created and cached timeline: {cache_key}")
        return timeline
    
    async def _fallback_to_standard_rag(
        self,
        query: str,
        repo_id: str,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fallback to standard RAG when temporal analysis not possible.
        """
        logger.info(f"⚠️ Falling back to standard RAG: {note}")
        
        # Use existing RAG service
        rag_service = get_rag_service()
        answer = await rag_service.query(
            query=query,
            repo_id=repo_id
        )
        
        return {
            "answer": answer["answer"],
            "temporal_analysis_available": False,
            "note": note or "Temporal analysis not available",
            "suggestion": "Re-ingest repository in git_history mode for temporal analysis",
            "citations": answer.get("sources", [])
        }
```

### 2. TopicExtractor

```python
class TopicExtractor:
    """
    Extracts topics and entities from natural language queries.
    
    Uses:
    - spaCy for NLP
    - Custom entity recognition
    - Technology detection from known list
    """
    
    def __init__(self):
        import spacy
        self.nlp = spacy.load("en_core_web_sm")
        self.tech_detector = TechnologyDetector()
        self.endpoint_pattern = re.compile(r'/api/[a-zA-Z0-9/_-]+')
    
    async def extract(self, query: str) -> Dict[str, List[str]]:
        """
        Extract topics from query.
        
        Returns:
            {
                "endpoints": [...],
                "parameters": [...],
                "services": [...],
                "technologies": [...],
                "concepts": [...]
            }
        """
        doc = self.nlp(query)
        
        topics = {
            "endpoints": [],
            "parameters": [],
            "services": [],
            "technologies": [],
            "concepts": []
        }
        
        # Extract endpoints
        topics["endpoints"] = self.endpoint_pattern.findall(query)
        
        # Extract parameters (words in quotes or after "parameter")
        for token in doc:
            if token.text in ["'", '"']:
                # Next token is likely a parameter
                if token.i + 1 < len(doc):
                    topics["parameters"].append(doc[token.i + 1].text)
        
        # Extract technologies
        topics["technologies"] = await self.tech_detector.detect(query)
        
        # Extract services (proper nouns, capitalized words)
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT"]:
                topics["services"].append(ent.text.lower())
        
        # Extract concepts (noun phrases)
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) >= 2:  # Multi-word concepts
                topics["concepts"].append(chunk.text.lower())
        
        # Deduplicate
        for key in topics:
            topics[key] = list(set(topics[key]))
        
        logger.info(f"📝 Extracted topics: {topics}")
        return topics
```

### 3. DocumentFinder

```python
class DocumentFinder:
    """
    Finds documents relevant to extracted topics.
    
    Uses:
    - Semantic search (embeddings)
    - Metadata filtering
    - Relevance ranking
    """
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.doc_repo = get_document_repository()
    
    async def find(
        self,
        topics: Dict[str, List[str]],
        repo_id: str,
        limit: int = 100
    ) -> List[DocumentModel]:
        """
        Find documents related to topics.
        """
        all_documents = []
        seen_ids = set()
        
        # Search for each topic category
        for category, items in topics.items():
            for item in items:
                # Semantic search
                results = await self._semantic_search(
                    query=item,
                    repo_id=repo_id,
                    limit=20
                )
                
                # Add to results (deduplicate)
                for doc in results:
                    if doc.id not in seen_ids:
                        all_documents.append(doc)
                        seen_ids.add(doc.id)
        
        # Rank by relevance
        ranked = await self._rank_by_relevance(all_documents, topics)
        
        # Return top N
        return ranked[:limit]
    
    async def _semantic_search(
        self,
        query: str,
        repo_id: str,
        limit: int
    ) -> List[DocumentModel]:
        """
        Perform semantic search for a query.
        """
        # Use existing RAG service
        rag_service = get_rag_service()
        results = await rag_service.search(
            query=query,
            repo_id=repo_id,
            limit=limit
        )
        
        return results
    
    async def _rank_by_relevance(
        self,
        documents: List[DocumentModel],
        topics: Dict[str, List[str]]
    ) -> List[DocumentModel]:
        """
        Rank documents by relevance to topics.
        """
        # Calculate relevance score for each document
        scored = []
        for doc in documents:
            score = self._calculate_relevance_score(doc, topics)
            scored.append((doc, score))
        
        # Sort by score (descending)
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, score in scored]
    
    def _calculate_relevance_score(
        self,
        doc: DocumentModel,
        topics: Dict[str, List[str]]
    ) -> float:
        """
        Calculate relevance score for a document.
        """
        score = 0.0
        
        # Check file path
        for endpoint in topics.get("endpoints", []):
            if endpoint.replace("/", "_") in doc.file_path:
                score += 0.3
        
        # Check content
        content_lower = doc.normalized_content.lower()
        for category, items in topics.items():
            for item in items:
                if item.lower() in content_lower:
                    score += 0.1
        
        # Boost for certain file types
        if doc.file_path.endswith((".md", ".rst")):
            score += 0.1  # Documentation files
        elif doc.file_path.endswith(".py"):
            score += 0.05  # Code files
        
        return score
```

### 4. DynamicTimelineConstructor

```python
class DynamicTimelineConstructor:
    """
    Constructs temporary timelines from document sets.
    
    Thin wrapper over TimelineManager with auto-period generation.
    """
    
    def __init__(self):
        self.timeline_manager = get_timeline_manager()
        self.period_generator = get_period_generator()
    
    async def construct(
        self,
        documents: List[DocumentModel],
        topics: Dict[str, List[str]],
        confidence: Dict[str, Any],
        is_temporary: bool = True
    ) -> Dict[str, Any]:
        """
        Construct a temporary timeline from documents.
        """
        # Determine timeline name from topics
        name = self._generate_timeline_name(topics)
        
        # Determine date range from documents
        start_date, end_date = self._get_date_range(documents)
        
        # Create timeline
        timeline = await self.timeline_manager.create_timeline(
            name=name,
            repo_id=documents[0].service_name if documents else "unknown",
            start_date=start_date,
            end_date=end_date,
            confidence_metadata=confidence,
            is_temporary=is_temporary,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        # Auto-generate periods
        periods = await self.period_generator.generate_periods(
            timeline_id=timeline["id"],
            strategy="adaptive"  # Monthly, quarterly, or by major commits
        )
        
        # Place documents on timeline
        await self._place_documents(timeline["id"], documents)
        
        return {
            "timeline_id": timeline["id"],
            "name": name,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "periods": periods,
            "document_count": len(documents),
            "confidence": confidence["confidence"],
            "is_temporary": is_temporary,
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
    
    def _generate_timeline_name(self, topics: Dict[str, List[str]]) -> str:
        """
        Generate a descriptive timeline name from topics.
        """
        # Prioritize endpoints, then services, then technologies
        if topics.get("endpoints"):
            return f"{topics['endpoints'][0]} Evolution"
        elif topics.get("services"):
            return f"{topics['services'][0].title()} System Evolution"
        elif topics.get("technologies"):
            return f"{topics['technologies'][0]} Integration History"
        else:
            return "Topic Evolution"
    
    def _get_date_range(
        self,
        documents: List[DocumentModel]
    ) -> Tuple[datetime, datetime]:
        """
        Get date range from documents.
        """
        dates = []
        for doc in documents:
            if doc.commit and doc.commit.date:
                dates.append(doc.commit.date)
            else:
                dates.append(doc.created_at)
        
        if not dates:
            # Default to last year
            return datetime.utcnow() - timedelta(days=365), datetime.utcnow()
        
        return min(dates), max(dates)
```

### 5. TemporalAnswerSynthesizer

```python
class TemporalAnswerSynthesizer:
    """
    Synthesizes answers from temporal analysis.
    
    Uses LLM to generate coherent narrative with temporal context.
    """
    
    def __init__(self):
        self.llm_client = get_llm_client()
    
    async def synthesize(
        self,
        query: str,
        temporal_analysis: Dict[str, Any],
        confidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesize answer from temporal analysis.
        """
        # Build prompt for LLM
        prompt = self._build_synthesis_prompt(
            query=query,
            analysis=temporal_analysis,
            confidence=confidence
        )
        
        # Generate answer
        response = await self.llm_client.generate(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.3  # Lower temperature for factual accuracy
        )
        
        # Parse response into sections
        sections = self._parse_response(response)
        
        return {
            "answer": response,
            "sections": sections,
            "confidence": confidence["confidence"],
            "temporal_context_included": True
        }
    
    def _build_synthesis_prompt(
        self,
        query: str,
        analysis: Dict[str, Any],
        confidence: Dict[str, Any]
    ) -> str:
        """
        Build prompt for LLM synthesis.
        """
        prompt = f"""You are a technical documentation assistant with access to temporal analysis of a codebase.

User Query: {query}

Temporal Analysis:
{json.dumps(analysis, indent=2)}

Confidence Level: {confidence["confidence"]} ({confidence["score"]:.2f})

Instructions:
1. Answer the user's query comprehensively
2. Include historical context (how things evolved)
3. Explain WHY changes were made (if available)
4. Mention WHEN key changes occurred
5. Be technically accurate
6. Cite specific commits, dates, and files
7. Structure your answer with clear sections:
   - Current State
   - Historical Context
   - Why This Change
   - Additional Context (if relevant)

Generate a comprehensive answer:"""
        
        return prompt
```

---

## API Specifications

### Primary Endpoint

```python
POST /api/v1/rag/temporal/query

Request:
{
    "query": "Why does the /api/auth endpoint require a 'refresh_token' parameter?",
    "repo_id": "ecosystem-mcp",
    "stream": false,  # Optional, default false
    "user_id": "user-123"  # Optional
}

Response (Success):
{
    "success": true,
    "answer": "The /api/auth endpoint requires a 'refresh_token' parameter...",
    "sections": [
        {
            "title": "Current State",
            "content": "..."
        },
        {
            "title": "Historical Context",
            "content": "..."
        },
        {
            "title": "Why This Change",
            "content": "..."
        }
    ],
    "timeline": {
        "timeline_id": "temp-uuid-123",
        "name": "/api/auth Evolution",
        "period_count": 8,
        "document_count": 47,
        "confidence": "HIGH",
        "is_temporary": true
    },
    "citations": [
        {
            "id": 1,
            "type": "migration_guide",
            "title": "MIGRATION_AUTH_V2.md",
            "date": "2024-03-15",
            "commit": "a3b7c9d",
            "url": "/documents/uuid-1"
        }
    ],
    "see_also": [
        "How does token refresh work?",
        "What are the security implications of refresh tokens?"
    ],
    "metadata": {
        "topics_extracted": {
            "endpoints": ["/api/auth"],
            "parameters": ["refresh_token"],
            "services": ["authentication"]
        },
        "documents_analyzed": 47,
        "processing_time_ms": 2345
    }
}

Response (Fallback to Standard RAG):
{
    "success": true,
    "answer": "...",
    "temporal_analysis_available": false,
    "note": "Documents found but lack git history",
    "suggestion": "Re-ingest repository in git_history mode for temporal analysis",
    "citations": [...]
}

Response (Error):
{
    "success": false,
    "error": "no_documents_found",
    "message": "No documents found related to query topics",
    "suggestion": "Try rephrasing your query or check if documents have been ingested"
}
```

### Streaming Endpoint

```python
POST /api/v1/rag/temporal/query (with stream=true)

Response: Server-Sent Events (SSE)

Event 1:
data: {"status": "extracting_topics", "progress": 0.1}

Event 2:
data: {"status": "finding_documents", "progress": 0.2, "documents_found": 47}

Event 3:
data: {"status": "checking_confidence", "progress": 0.3, "confidence": "HIGH"}

Event 4:
data: {"status": "building_timeline", "progress": 0.4}

Event 5:
data: {"status": "analyzing_timeline", "progress": 0.6}

Event 6:
data: {"status": "synthesizing_answer", "progress": 0.8}

Event 7:
data: {"status": "formatting_citations", "progress": 0.9}

Event 8:
data: {"status": "complete", "progress": 1.0, "result": {...}}
```

### Additional Endpoints

```python
# Get cached timeline
GET /api/v1/timelines/temporary/{timeline_id}

# Extend timeline TTL
POST /api/v1/timelines/temporary/{timeline_id}/extend

# Convert temporary timeline to permanent
POST /api/v1/timelines/temporary/{timeline_id}/make-permanent

# Get topic suggestions
GET /api/v1/rag/temporal/topics?repo_id={repo_id}
Response: {
    "endpoints": [...],
    "services": [...],
    "technologies": [...]
}
```

---

## Integration Points

### 1. Documentation Reader Integration

```python
# In generated documentation viewer
<div class="doc-section">
    <h2>Authentication Endpoint</h2>
    <p>The /api/auth endpoint requires...</p>
    
    <!-- Add "Explain this" button -->
    <button onclick="explainThis('authentication endpoint')">
        🤔 Explain this
    </button>
</div>

<script>
async function explainThis(topic) {
    const response = await fetch('/api/v1/rag/temporal/query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            query: `Explain the ${topic} and its evolution`,
            repo_id: currentRepoId
        })
    });
    
    const result = await response.json();
    showExplanationModal(result);
}
</script>
```

### 2. Technology Browser Integration

```python
# In dashboard: Technology Browser page
st.title("🔧 Technology Browser")

# Get available technologies
technologies = get_technologies(repo_id)

# User selects technology
selected_tech = st.selectbox("Select Technology", technologies)

if selected_tech:
    # Trigger dynamic temporal RAG
    with st.spinner("Analyzing technology evolution..."):
        result = query_temporal_rag(
            query=f"How has {selected_tech} been used in this project?",
            repo_id=repo_id
        )
    
    # Display result
    st.markdown(result["answer"])
    
    # Show timeline
    if result.get("timeline"):
        show_timeline_visualization(result["timeline"])
```

### 3. API Explorer Integration

```python
# In dashboard: API Explorer page
st.title("🔌 API Explorer")

# Get available endpoints
endpoints = get_endpoints(repo_id)

# User selects endpoint
selected_endpoint = st.selectbox("Select Endpoint", endpoints)

if selected_endpoint:
    # Show endpoint details
    st.subheader(f"Endpoint: {selected_endpoint}")
    
    # Add "Explain Evolution" button
    if st.button("📜 Explain Evolution"):
        with st.spinner("Analyzing endpoint evolution..."):
            result = query_temporal_rag(
                query=f"Explain the evolution of {selected_endpoint}",
                repo_id=repo_id
            )
        
        st.markdown(result["answer"])
        
        # Show citations
        with st.expander("📚 Sources"):
            for citation in result["citations"]:
                st.markdown(f"- [{citation['title']}]({citation['url']}) ({citation['date']})")
```

### 4. Dependency Graph Integration

```python
# In dashboard: Dependency Graph page
# When user clicks on a dependency edge
def on_dependency_click(source_service, target_service):
    """Handle dependency click."""
    
    # Trigger dynamic temporal RAG
    result = query_temporal_rag(
        query=f"Why does {source_service} depend on {target_service}?",
        repo_id=repo_id
    )
    
    # Show in modal
    show_modal(
        title=f"Dependency: {source_service} → {target_service}",
        content=result["answer"],
        citations=result["citations"]
    )
```

---

## Examples

### Example 1: API Parameter Question

**Query:** "Why does the /api/auth endpoint require a 'refresh_token' parameter?"

**Extracted Topics:**
```json
{
    "endpoints": ["/api/auth"],
    "parameters": ["refresh_token"],
    "services": ["authentication"],
    "technologies": ["JWT", "OAuth"],
    "concepts": ["token refresh", "authentication"]
}
```

**Documents Found:** 47 documents (45 with git history, 2 snapshot)

**Timeline Created:**
- Name: "/api/auth Evolution"
- Period: 2023-01-15 to 2024-10-22
- Periods: 8 (monthly/quarterly)
- Confidence: HIGH (95%)

**Temporal Analysis:**
- **2023-01**: Basic API key auth
- **2023-06**: JWT tokens introduced
- **2024-03**: Refresh tokens added (breaking change)
- **2024-10**: Current state

**Answer:**
```
The /api/auth endpoint requires a 'refresh_token' parameter because of a 
security enhancement implemented in March 2024 (commit a3b7c9d).

**Current State**
As of October 2024, the /api/auth endpoint uses a dual-token system with 
short-lived access tokens (15 minutes) and long-lived refresh tokens (30 days).

**Historical Context**
Initially (January 2023), the authentication system used simple API keys. 
This was secure but inflexible. In June 2023, JWT tokens were introduced 
for better security and stateless authentication. However, these tokens had 
short expiration times (15 minutes) to minimize security risk, which meant 
users had to re-authenticate frequently.

**Why This Change**
The refresh_token parameter was added in March 2024 to solve the UX problem 
of frequent re-authentication while maintaining security. Refresh tokens allow 
clients to obtain new access tokens without re-entering credentials. This 
change was part of a broader OAuth2 migration (see MIGRATION_AUTH_V2.md).

**Additional Context**
The implementation follows RFC 6749 (OAuth 2.0). Refresh tokens are stored 
securely and can be revoked. The change was breaking because it required 
clients to update their authentication flow.

**Sources:**
1. MIGRATION_AUTH_V2.md (2024-03-15, commit a3b7c9d): Migration guide
2. src/api/auth.py (2024-03-12, commit a3b7c9d, lines 45-78): Implementation
3. docs/authentication.md (2024-03-20): Updated documentation
4. SECURITY_AUDIT_2024Q1.md (2024-02-28): Security review that prompted change

**See Also:**
- How does token refresh work?
- What are the security implications of refresh tokens?
- How to migrate from API keys to JWT?
```

### Example 2: Technology Usage Question

**Query:** "How is Redis used in this project?"

**Extracted Topics:**
```json
{
    "technologies": ["Redis"],
    "concepts": ["caching", "data storage"]
}
```

**Documents Found:** 32 documents

**Timeline Created:**
- Name: "Redis Integration History"
- Period: 2023-03-01 to 2024-10-22
- Periods: 6
- Confidence: MEDIUM (65%)

**Answer:**
```
Redis is used in this project for multiple purposes, with its usage evolving 
significantly over time.

**Current State**
As of October 2024, Redis serves three primary functions:
1. L2 caching layer for embeddings (since August 2024)
2. Job queue for background workers (since March 2023)
3. Session storage for the dashboard (since June 2023)

**Historical Context**
Redis was first introduced in March 2023 as a simple job queue using Redis 
Streams. Initially, it only handled ingestion jobs. In June 2023, session 
storage was added for the dashboard. The most significant expansion came in 
August 2024 when Redis was integrated as an L2 cache for the embedding service, 
dramatically improving performance (see EMBEDDING_SERVICE_OPTIMIZATION.md).

**Why These Changes**
Each Redis integration solved a specific problem:
- Job queue (March 2023): Needed reliable background processing
- Session storage (June 2023): Dashboard needed stateful sessions
- Embedding cache (August 2024): Embedding generation was slow (200ms/doc)

**Additional Context**
The project uses Redis 7.0+ with persistence enabled (AOF). The embedding 
cache alone reduced embedding generation time by 85% for duplicate content.

**Sources:**
1. docker-compose.yml (multiple updates): Redis configuration
2. src/utils/redis_client.py: Redis client implementation
3. EMBEDDING_SERVICE_OPTIMIZATION.md (2024-08-15): Performance improvements
4. src/workers/ingestion_worker.py: Job queue usage

**See Also:**
- How does the embedding cache work?
- What happens if Redis goes down?
- How to monitor Redis performance?
```

### Example 3: Service Dependency Question

**Query:** "Why does the dashboard depend on the embedding service?"

**Extracted Topics:**
```json
{
    "services": ["dashboard", "embedding service"],
    "concepts": ["dependency", "service integration"]
}
```

**Documents Found:** 18 documents

**Timeline Created:**
- Name: "Dashboard System Evolution"
- Period: 2024-01-01 to 2024-10-22
- Periods: 4
- Confidence: HIGH (90%)

**Answer:**
```
The dashboard depends on the embedding service to provide real-time embedding 
generation and quality metrics, a dependency that was introduced in August 2024.

**Current State**
As of October 2024, the dashboard uses the embedding service for:
1. Real-time embedding generation (Embeddings Manager page)
2. Embedding quality metrics (cache hit rates, generation times)
3. Model health checks

**Historical Context**
Initially (January-July 2024), the dashboard only displayed pre-generated 
embeddings from the database. It had no direct connection to the embedding 
service. In August 2024, as part of the embedding service optimization project, 
the dashboard was enhanced to interact directly with the embedding service for 
real-time operations and monitoring.

**Why This Change**
This dependency was added to give users visibility and control over the 
embedding generation process. Previously, embeddings were generated silently 
during ingestion with no user feedback. The new integration allows users to:
- Manually trigger embedding generation
- Monitor embedding quality
- Troubleshoot embedding issues
- View cache performance

**Additional Context**
The integration uses the embedding service's REST API (/api/v1/embeddings/*). 
The dashboard includes circuit breakers and fallbacks to handle embedding 
service unavailability gracefully.

**Sources:**
1. services/ecosystem-mcp-dashboard/pages/embeddings_manager.py (2024-08-20)
2. EMBEDDING_SERVICE_INTEGRATION.md (2024-08-15): Integration plan
3. docker-compose.yml (2024-08-20): Service linking
4. services/ecosystem-mcp-embedding/src/api/routes.py: API endpoints

**See Also:**
- How does the embedding service work?
- What happens if the embedding service is down?
- How to monitor embedding quality?
```

---

## Testing Strategy

### Unit Tests

```python
# Test topic extraction
def test_topic_extractor_endpoints():
    extractor = TopicExtractor()
    query = "Why does /api/auth require refresh_token?"
    topics = await extractor.extract(query)
    assert "/api/auth" in topics["endpoints"]
    assert "refresh_token" in topics["parameters"]

# Test document finder
def test_document_finder_relevance():
    finder = DocumentFinder()
    topics = {"endpoints": ["/api/auth"]}
    docs = await finder.find(topics, repo_id="test")
    assert len(docs) > 0
    assert all("auth" in d.file_path.lower() for d in docs[:5])

# Test timeline constructor
def test_dynamic_timeline_constructor():
    constructor = DynamicTimelineConstructor()
    timeline = await constructor.construct(
        documents=test_documents,
        topics={"endpoints": ["/api/auth"]},
        confidence={"confidence": "HIGH"}
    )
    assert timeline["name"] == "/api/auth Evolution"
    assert timeline["is_temporary"] == True
```

### Integration Tests

```python
# Test full flow
async def test_dynamic_temporal_rag_full_flow():
    orchestrator = DynamicTemporalRAGOrchestrator()
    
    result = await orchestrator.query(
        query="Why does /api/auth require refresh_token?",
        repo_id="ecosystem-mcp"
    )
    
    assert result["success"] == True
    assert "refresh_token" in result["answer"]
    assert result["timeline"]["confidence"] == "HIGH"
    assert len(result["citations"]) > 0

# Test fallback to standard RAG
async def test_fallback_when_no_git_history():
    # Setup: Ingest repo in snapshot mode
    await ingest_repo(mode="snapshot")
    
    orchestrator = DynamicTemporalRAGOrchestrator()
    result = await orchestrator.query(
        query="Why does /api/auth require refresh_token?",
        repo_id="test-repo"
    )
    
    assert result["temporal_analysis_available"] == False
    assert "suggestion" in result
```

### End-to-End Tests

```python
# Test from UI to answer
async def test_e2e_rag_query_from_dashboard():
    # Simulate user interaction
    response = await client.post("/api/v1/rag/temporal/query", json={
        "query": "Why does /api/auth require refresh_token?",
        "repo_id": "ecosystem-mcp"
    })
    
    assert response.status_code == 200
    result = response.json()
    
    # Verify answer quality
    assert len(result["answer"]) > 100
    assert "2024" in result["answer"]  # Should mention dates
    assert len(result["citations"]) >= 2
    
    # Verify timeline was created
    timeline_id = result["timeline"]["timeline_id"]
    timeline = await client.get(f"/api/v1/timelines/temporary/{timeline_id}")
    assert timeline.status_code == 200
```

### Performance Tests

```python
# Test response time
async def test_performance_response_time():
    orchestrator = DynamicTemporalRAGOrchestrator()
    
    start = time.time()
    result = await orchestrator.query(
        query="Why does /api/auth require refresh_token?",
        repo_id="ecosystem-mcp"
    )
    elapsed = time.time() - start
    
    # Should complete in < 5 seconds
    assert elapsed < 5.0

# Test caching
async def test_performance_caching():
    orchestrator = DynamicTemporalRAGOrchestrator()
    
    # First query (no cache)
    start1 = time.time()
    result1 = await orchestrator.query(
        query="Why does /api/auth require refresh_token?",
        repo_id="ecosystem-mcp"
    )
    elapsed1 = time.time() - start1
    
    # Second query (with cache)
    start2 = time.time()
    result2 = await orchestrator.query(
        query="Why does /api/auth require refresh_token?",
        repo_id="ecosystem-mcp"
    )
    elapsed2 = time.time() - start2
    
    # Second query should be faster (cached timeline)
    assert elapsed2 < elapsed1 * 0.5
```

---

## Success Metrics

### Technical Metrics

- **Response Time:** < 5s for 90% of queries
- **Cache Hit Rate:** > 60% for timeline cache
- **Accuracy:** > 90% of answers include correct temporal context
- **Fallback Rate:** Track % of queries that fallback to standard RAG

### User Metrics

- **Adoption Rate:** Track usage of dynamic temporal RAG vs standard RAG
- **User Satisfaction:** Gather feedback on answer quality
- **Follow-up Questions:** Track if users ask follow-up questions (indicates incomplete answers)

### Business Metrics

- **Time to Understanding:** Reduce by 50% (users understand faster with temporal context)
- **Documentation Gaps:** Identify gaps through unanswered queries
- **Knowledge Retention:** Improve by 40% (better understanding of evolution)

---

## Implementation Roadmap

### Week 1: Core Components

**Days 1-2: Topic Extraction & Document Finding**
- [ ] Implement `TopicExtractor`
- [ ] Implement `DocumentFinder`
- [ ] Unit tests

**Days 3-4: Timeline Construction & Confidence**
- [ ] Implement `DynamicTimelineConstructor`
- [ ] Integrate with `TemporalConfidenceCalculator`
- [ ] Unit tests

**Days 5-7: Orchestrator & API**
- [ ] Implement `DynamicTemporalRAGOrchestrator`
- [ ] Add API endpoint
- [ ] Integration tests

### Week 2: Synthesis & Integration

**Days 1-2: Answer Synthesis**
- [ ] Implement `TemporalAnswerSynthesizer`
- [ ] Implement `CitationFormatter`
- [ ] Unit tests

**Days 3-4: Dashboard Integration**
- [ ] Add "Explain this" buttons to doc reader
- [ ] Add technology browser integration
- [ ] Add API explorer integration

**Days 5-7: Testing & Optimization**
- [ ] End-to-end tests
- [ ] Performance optimization
- [ ] Caching implementation

---

## Summary

### What We're Adding

A **Dynamic Temporal RAG** system that automatically constructs topic-specific timelines from user queries to provide highly contextual, temporally-aware answers.

### Key Benefits

- ✅ **No manual timeline creation** - Automatic and instant
- ✅ **Highly contextual answers** - Full temporal understanding
- ✅ **Accurate attribution** - Know when/why changes happened
- ✅ **Better than standard RAG** - Understands evolution
- ✅ **Seamless UX** - Natural language queries

### Implementation Scope

- **New Code:** ~900 lines (thin facades)
- **Service Reuse:** 98%+ (leverages all existing services)
- **Timeline:** 2 weeks
- **Risk:** Low (builds on proven infrastructure)

### Integration

- Works seamlessly with existing timeline features
- Enhances RAG queries with temporal context
- Integrates with dashboard, doc reader, tech browser
- Graceful fallback to standard RAG when needed

---

**Document Version:** 3.2  
**Last Updated:** 2025-10-22  
**Status:** Ready for Implementation  
**Extends:** v3.1 (Graceful Fallback Addendum)  
**Integration:** Part of complete timeline analysis suite

