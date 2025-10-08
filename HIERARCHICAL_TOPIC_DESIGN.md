# 🎯 Hierarchical Topic Extraction Design

## Overview

This document outlines the design for implementing hierarchical topic extraction using the **summarizer-hub** service to dramatically improve contextual tagging accuracy.

## Problem Statement

Current issues with document generation:
1. **Duplicate sections** - Same topic appears multiple times
2. **No hierarchy** - All topics treated equally, no parent-child relationships
3. **Poor organization** - Related topics not grouped together
4. **Low accuracy** - Keyword-based matching misses semantic relationships

## Solution: Hierarchical Topics with AI

### Core Concept

**Use summarizer-hub's AI capabilities to extract:**
- **Main Topics**: Primary subjects (e.g., "Horus Heresy", "Chaos Gods")
- **Sub-Topics**: Specific aspects (e.g., "Traitor Legions" under "Horus Heresy")
- **Tangential Topics**: Related but secondary (e.g., "Warp Travel", "Pre-Heresy Era")

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Crawled Documents                         │
│              (1,686 Fandom Wiki Pages)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│           Hierarchical Topic Extractor                       │
│                                                              │
│  1. Batch Process Documents (10 at a time)                  │
│  2. Send to Summarizer-Hub                                  │
│  3. Extract Topics via AI                                   │
│  4. Build Topic Hierarchy                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   Summarizer-Hub (Port 5160)                 │
│                                                              │
│  ┌──────────────────────────────────────────┐              │
│  │   /categorize API                        │              │
│  │   - ML-based classification              │              │
│  │   - Confidence scoring                   │              │
│  └──────────────────────────────────────────┘              │
│                                                              │
│  ┌──────────────────────────────────────────┐              │
│  │   /summarize API                         │              │
│  │   - AI topic extraction                  │              │
│  │   - Hierarchical structure               │              │
│  │   - Keyword generation                   │              │
│  └──────────────────────────────────────────┘              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  Document Topics Output                      │
│                                                              │
│  Main Topics:                                               │
│    - Horus Heresy (confidence: 0.95)                       │
│    - Chaos Gods (confidence: 0.92)                         │
│                                                              │
│  Sub-Topics:                                                │
│    - Traitor Legions (parent: Horus Heresy, conf: 0.88)   │
│    - Loyalist Response (parent: Horus Heresy, conf: 0.85) │
│    - Khorne (parent: Chaos Gods, conf: 0.90)              │
│    - Slaanesh (parent: Chaos Gods, conf: 0.87)            │
│                                                              │
│  Tangential Topics:                                         │
│    - Warp Travel (confidence: 0.70)                        │
│    - Pre-Heresy Era (confidence: 0.68)                     │
└─────────────────────────┬───────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Enhanced Contextual Tags                        │
│                                                              │
│  topic:horus-heresy                                         │
│  topic:horus-heresy:traitor-legions                        │
│  topic:horus-heresy:loyalist-response                      │
│  topic:chaos-gods                                           │
│  topic:chaos-gods:khorne                                    │
│  topic:chaos-gods:slaanesh                                  │
│  related:warp-travel                                        │
│  related:pre-heresy-era                                     │
└─────────────────────────────────────────────────────────────┘
```

## API Integration

### 1. Categorization Endpoint

**Purpose**: Get main topics and confidence scores

```python
POST http://localhost:5160/categorize
{
    "text": "Document content...",
    "title": "Horus Heresy",
    "taxonomy": "technical_documents",
    "confidence_threshold": 0.5,
    "include_scores": true,
    "extract_keywords": true
}
```

**Response**:
```json
{
    "categories": [
        {"name": "Horus Heresy", "confidence": 0.95},
        {"name": "Chaos Gods", "confidence": 0.92}
    ],
    "keywords": ["warmaster", "traitor", "heresy", "corruption"],
    "confidence": 0.93
}
```

### 2. Summarization Endpoint

**Purpose**: Extract hierarchical topic structure via AI

```python
POST http://localhost:5160/summarize
{
    "text": "Document content...",
    "prompt": "Analyze this document and extract:\n1. Main topics\n2. Sub-topics\n3. Tangential topics",
    "options": {
        "max_length": 300,
        "format": "text",
        "include_confidence": true
    }
}
```

**Response**:
```json
{
    "summary": "MAIN: Horus Heresy, Chaos Gods\nSUB(Horus Heresy): Traitor Legions, Siege of Terra\nSUB(Chaos Gods): Khorne, Slaanesh, Nurgle, Tzeentch\nTANGENTIAL: Warp Travel, Pre-Heresy Era",
    "confidence": 0.88
}
```

## Implementation Plan

### Phase 1: Core Integration (1-2 hours)

1. ✅ **Create `HierarchicalTopicExtractor` class**
   - Connection to summarizer-hub
   - Health check integration
   - Batch processing support

2. ✅ **Implement topic extraction logic**
   - Single document extraction
   - Batch document extraction
   - AI response parsing

3. ✅ **Define topic data structures**
   - `Topic` dataclass (name, type, confidence, parent, related)
   - `DocumentTopics` dataclass (main, sub, tangential)
   - `TopicType` enum (MAIN, SUB, TANGENTIAL)

### Phase 2: Integration with Tagging System (1 hour)

4. **Integrate with `UniversalTaggingManager`**
   - Add hierarchical topic extraction step
   - Merge with existing contextual tags
   - Maintain tag breakdown (default, contextual, user, hierarchical)

5. **Update `TagCollection` dataclass**
   - Add `hierarchical_tags` field
   - Track topic hierarchy metadata

### Phase 3: Document Generation Enhancement (1 hour)

6. **Update `DocumentProcessor`**
   - Use hierarchical topics for organization
   - Group by main topic, then sub-topics
   - Include tangential topics as "Related Topics" section

7. **Improve document synthesis**
   - Deduplicate by topic hierarchy
   - Organize content by topic tree
   - Add "Topic Map" visualization

### Phase 4: Testing & Validation (1 hour)

8. **Start summarizer-hub service**
   - Verify health endpoint
   - Test categorization API
   - Test summarization API

9. **Run integration tests**
   - Test with Horus Heresy documents
   - Verify topic extraction accuracy
   - Validate document quality improvement

10. **Performance testing**
    - Batch processing efficiency
    - Rate limiting behavior
    - Caching effectiveness

## Benefits

### 1. Improved Tagging Accuracy

**Before**:
```
tags: ["chaos", "daemon", "warp", "khorne"]
```

**After**:
```
tags: [
    "topic:chaos-gods",
    "topic:chaos-gods:khorne",
    "topic:chaos-gods:nurgle",
    "related:warp-entities",
    "related:daemonic-possession"
]
```

### 2. Better Document Organization

**Before**:
- Section 1: Chaos Daemons
- Section 2: Chaos Daemons (duplicate!)
- Section 3: Chaos Daemons (another duplicate!)

**After**:
- **Main Topic**: Chaos Gods
  - **Sub-Topic**: Khorne
  - **Sub-Topic**: Nurgle
  - **Sub-Topic**: Slaanesh
  - **Sub-Topic**: Tzeentch
- **Related Topics**
  - Warp Travel
  - Daemonic Possession

### 3. Enhanced Search & Discovery

Users can now:
- Filter by main topic
- Drill down into sub-topics
- Explore related topics
- Navigate topic hierarchy

### 4. Reduced Duplication

- Intelligent deduplication using topic hierarchy
- Group similar content under common parent
- Eliminate redundant sections

## Configuration

### Environment Variables

```bash
# Summarizer-Hub Configuration
SUMMARIZER_HUB_URL=http://localhost:5160
SUMMARIZER_HUB_TIMEOUT=30
SUMMARIZER_HUB_BATCH_SIZE=10

# Topic Extraction
TOPIC_CONFIDENCE_THRESHOLD=0.5
ENABLE_HIERARCHICAL_TOPICS=true
TOPIC_EXTRACTION_ENABLED=true
```

### Feature Flags

```python
tagging_config = UniversalTaggingConfig(
    enable_preprocessing=True,
    enable_hierarchical_topics=True,  # NEW
    hierarchical_topic_confidence=0.5,  # NEW
    summarizer_url="http://localhost:5160",  # NEW
    user_tags=["domain:warhammer-40k"]
)
```

## Usage Example

```python
from ingestion.tagging.hierarchical_topics import HierarchicalTopicExtractor

# Initialize extractor
async with HierarchicalTopicExtractor() as extractor:
    # Check service health
    if not await extractor.check_service_health():
        print("Summarizer-hub offline, falling back to basic tagging")
        return
    
    # Extract topics from single document
    topics = await extractor.extract_topics_single(
        text=document.content_md,
        title=document.title,
        taxonomy="warhammer_40k_lore"
    )
    
    if topics:
        print(f"Main Topics: {[t.name for t in topics.main_topics]}")
        print(f"Sub-Topics: {[t.name for t in topics.sub_topics]}")
        print(f"Tangential: {[t.name for t in topics.tangential_topics]}")
        
        # Generate hierarchical tags
        hierarchical_tags = extractor.generate_hierarchical_tags(topics)
        print(f"Tags: {hierarchical_tags}")
    
    # Batch processing
    documents = [(doc.content_md, doc.title) for doc in all_docs]
    all_topics = await extractor.extract_topics_batch(
        documents=documents,
        taxonomy="warhammer_40k_lore"
    )
```

## Metrics & Success Criteria

### Tagging Accuracy
- **Target**: 90%+ topic identification accuracy
- **Measurement**: Human review of sample documents
- **Baseline**: Current keyword-based approach (~60%)

### Document Quality
- **Target**: 80%+ reduction in duplicate sections
- **Measurement**: Count of unique topics vs. total sections
- **Baseline**: Current documents (~50% duplication)

### Processing Performance
- **Target**: < 5 seconds per document
- **Measurement**: Average extraction time
- **Batch**: 10 documents in < 30 seconds

### User Satisfaction
- **Target**: Documents are "well-organized" and "easy to navigate"
- **Measurement**: User feedback
- **Metric**: Topic hierarchy is clear and helpful

## Future Enhancements

1. **Topic Relationship Graph**
   - Visualize topic hierarchy
   - Show connections between topics
   - Interactive exploration

2. **Dynamic Taxonomy**
   - Learn new topics from corpus
   - Update hierarchy over time
   - Domain-specific topic trees

3. **Cross-Document Topics**
   - Identify common topics across all documents
   - Build global topic map
   - Suggest related documents

4. **Confidence-Based Filtering**
   - Only show high-confidence topics
   - Flag uncertain classifications
   - Request human validation

## Conclusion

By leveraging the summarizer-hub's AI capabilities, we can:
- **Dramatically improve** contextual tagging accuracy
- **Eliminate duplicates** through hierarchical organization
- **Enhance discoverability** with structured topics
- **Create better documentation** that's easier to navigate

This is a **game-changer** for document quality! 🚀

---

**Next Steps**:
1. Start summarizer-hub service
2. Test hierarchical topic extraction
3. Integrate with document generation
4. Validate improvements

