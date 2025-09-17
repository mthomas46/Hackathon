#!/usr/bin/env python3
"""
Advanced NLP Engine for Interpreter Service - Phase 2 Implementation

Implements advanced natural language processing capabilities with:
- Persistent conversation memory
- Context-aware intent recognition
- Multi-modal query processing
- Advanced conversation management
"""

import asyncio
import json
import uuid
import time
import re
from typing import Dict, Any, List, Optional, Callable, Type, Union, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import hashlib
import threading

from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget
from services.shared.intelligent_caching import get_service_cache


class ConversationState(Enum):
    """Conversation states for advanced dialogue management."""
    INITIAL = "initial"
    QUESTIONING = "questioning"
    CLARIFYING = "clarifying"
    EXECUTING = "executing"
    COMPLETING = "completing"
    ERROR = "error"


class MemoryType(Enum):
    """Types of conversation memory."""
    SHORT_TERM = "short_term"  # Current session
    MEDIUM_TERM = "medium_term"  # Last 24 hours
    LONG_TERM = "long_term"  # Historical patterns
    EPISODIC = "episodic"  # Specific events/memories


class IntentConfidence(Enum):
    """Intent recognition confidence levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class ConversationContext:
    """Advanced conversation context with memory and state."""
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    current_state: ConversationState = ConversationState.INITIAL

    # Memory components
    short_term_memory: List[Dict[str, Any]] = field(default_factory=list)
    medium_term_memory: List[Dict[str, Any]] = field(default_factory=list)
    long_term_memory: List[Dict[str, Any]] = field(default_factory=list)

    # Context information
    current_topic: Optional[str] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    active_entities: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    turn_count: int = 0

    def add_message(self, message: Dict[str, Any], message_type: str = "user"):
        """Add a message to the conversation."""
        message_entry = {
            "id": str(uuid.uuid4()),
            "type": message_type,
            "content": message,
            "timestamp": datetime.now(),
            "turn_number": self.turn_count
        }

        self.conversation_history.append(message_entry)
        self.message_count += 1
        self.last_updated = datetime.now()

        # Update short-term memory
        if len(self.short_term_memory) >= 10:  # Keep last 10 messages
            # Move oldest to medium-term memory
            oldest = self.short_term_memory.pop(0)
            self.medium_term_memory.append(oldest)

        self.short_term_memory.append(message_entry)

    def get_recent_context(self, turns: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation context."""
        return self.conversation_history[-turns:] if self.conversation_history else []

    def update_topic(self, new_topic: str):
        """Update the current conversation topic."""
        self.current_topic = new_topic
        self.last_updated = datetime.now()

    def add_entity(self, entity_type: str, entity_value: Any, confidence: float = 1.0):
        """Add an active entity to the conversation."""
        self.active_entities[entity_type] = {
            "value": entity_value,
            "confidence": confidence,
            "last_updated": datetime.now(),
            "mention_count": self.active_entities.get(entity_type, {}).get("mention_count", 0) + 1
        }

    def get_entity(self, entity_type: str) -> Optional[Dict[str, Any]]:
        """Get an active entity."""
        return self.active_entities.get(entity_type)

    def clear_expired_entities(self, max_age_minutes: int = 30):
        """Clear entities that haven't been mentioned recently."""
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)

        expired_entities = []
        for entity_type, entity_data in self.active_entities.items():
            if entity_data["last_updated"] < cutoff_time:
                expired_entities.append(entity_type)

        for entity_type in expired_entities:
            del self.active_entities[entity_type]

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation."""
        return {
            "conversation_id": self.conversation_id,
            "duration_minutes": (self.last_updated - self.created_at).total_seconds() / 60,
            "message_count": self.message_count,
            "turn_count": self.turn_count,
            "current_topic": self.current_topic,
            "active_entities_count": len(self.active_entities),
            "state": self.current_state.value,
            "last_activity": self.last_updated.isoformat()
        }


@dataclass
class IntentResult:
    """Result of intent recognition with confidence and context."""
    intent: str
    confidence: IntentConfidence
    confidence_score: float
    entities: Dict[str, Any]
    context: Dict[str, Any]
    alternative_intents: List[Dict[str, Any]] = field(default_factory=list)
    processing_time_ms: float = 0.0
    requires_clarification: bool = False
    clarification_question: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "intent": self.intent,
            "confidence": self.confidence.value,
            "confidence_score": self.confidence_score,
            "entities": self.entities,
            "context": self.context,
            "alternative_intents": self.alternative_intents,
            "processing_time_ms": self.processing_time_ms,
            "requires_clarification": self.requires_clarification,
            "clarification_question": self.clarification_question
        }


@dataclass
class MultiModalInput:
    """Multi-modal input processing result."""
    text_content: Optional[str] = None
    audio_transcript: Optional[str] = None
    image_description: Optional[str] = None
    video_transcript: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None

    # Processing metadata
    modalities_used: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    confidence_scores: Dict[str, float] = field(default_factory=dict)

    def get_combined_content(self) -> str:
        """Get combined content from all modalities."""
        content_parts = []

        if self.text_content:
            content_parts.append(f"Text: {self.text_content}")
        if self.audio_transcript:
            content_parts.append(f"Audio: {self.audio_transcript}")
        if self.image_description:
            content_parts.append(f"Image: {self.image_description}")
        if self.video_transcript:
            content_parts.append(f"Video: {self.video_transcript}")

        return " | ".join(content_parts) if content_parts else ""

    def get_primary_content(self) -> Optional[str]:
        """Get the primary content based on confidence scores."""
        if not self.confidence_scores:
            return self.text_content or self.audio_transcript or self.image_description

        # Find modality with highest confidence
        best_modality = max(self.confidence_scores.items(), key=lambda x: x[1])

        if best_modality[0] == "text":
            return self.text_content
        elif best_modality[0] == "audio":
            return self.audio_transcript
        elif best_modality[0] == "image":
            return self.image_description
        elif best_modality[0] == "video":
            return self.video_transcript

        return self.get_combined_content()


class ConversationMemoryManager:
    """Advanced conversation memory management system."""

    def __init__(self):
        self.active_conversations: Dict[str, ConversationContext] = {}
        self.conversation_archive: Dict[str, ConversationContext] = {}
        self.memory_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.cache = get_service_cache(ServiceNames.INTERPRETER)

    async def create_conversation(self, user_id: Optional[str] = None,
                                session_id: Optional[str] = None) -> ConversationContext:
        """Create a new conversation context."""
        context = ConversationContext(user_id=user_id, session_id=session_id)

        # Load user preferences if available
        if user_id:
            context.user_preferences = await self._load_user_preferences(user_id)

        # Load relevant long-term memory
        if user_id:
            context.long_term_memory = await self._load_long_term_memory(user_id)

        self.active_conversations[context.conversation_id] = context

        # Cache conversation
        await self.cache.set(f"conversation_{context.conversation_id}", {
            "conversation_id": context.conversation_id,
            "user_id": context.user_id,
            "created_at": context.created_at.isoformat()
        }, ttl_seconds=3600)

        fire_and_forget("info", f"Created conversation {context.conversation_id} for user {user_id}", ServiceNames.INTERPRETER)
        return context

    async def get_conversation(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get an existing conversation context."""
        # Check active conversations first
        if conversation_id in self.active_conversations:
            return self.active_conversations[conversation_id]

        # Check cache
        cached_data = await self.cache.get(f"conversation_{conversation_id}")
        if cached_data:
            # Restore from archive if needed
            return await self._restore_conversation(conversation_id)

        return None

    async def update_conversation(self, conversation_id: str, updates: Dict[str, Any]) -> bool:
        """Update conversation context."""
        context = await self.get_conversation(conversation_id)
        if not context:
            return False

        # Apply updates
        for key, value in updates.items():
            if hasattr(context, key):
                setattr(context, key, value)

        context.last_updated = datetime.now()

        # Update cache
        await self.cache.set(f"conversation_{conversation_id}", {
            "conversation_id": context.conversation_id,
            "user_id": context.user_id,
            "last_updated": context.last_updated.isoformat()
        }, ttl_seconds=3600)

        return True

    async def archive_conversation(self, conversation_id: str) -> bool:
        """Archive a conversation for long-term storage."""
        context = self.active_conversations.get(conversation_id)
        if not context:
            return False

        # Move to archive
        self.conversation_archive[conversation_id] = context
        del self.active_conversations[conversation_id]

        # Extract patterns for learning
        await self._extract_memory_patterns(context)

        # Persist to long-term storage (would be database in production)
        await self._persist_conversation(context)

        fire_and_forget("info", f"Archived conversation {conversation_id}", ServiceNames.INTERPRETER)
        return True

    async def _load_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Load user preferences from storage."""
        # In production, this would query a database
        cache_key = f"user_preferences_{user_id}"
        preferences = await self.cache.get(cache_key)

        if preferences:
            return preferences

        # Default preferences
        return {
            "language": "en",
            "response_style": "concise",
            "technical_level": "intermediate",
            "preferred_modalities": ["text"],
            "notification_preferences": {"email": True, "push": False}
        }

    async def _load_long_term_memory(self, user_id: str) -> List[Dict[str, Any]]:
        """Load long-term memory patterns for user."""
        # In production, this would query a vector database or similar
        cache_key = f"long_term_memory_{user_id}"
        memory = await self.cache.get(cache_key)

        if memory:
            return memory

        # Default empty memory
        return []

    async def _restore_conversation(self, conversation_id: str) -> Optional[ConversationContext]:
        """Restore a conversation from archive."""
        # In production, this would load from database
        return self.conversation_archive.get(conversation_id)

    async def _extract_memory_patterns(self, context: ConversationContext):
        """Extract memory patterns for learning."""
        if not context.conversation_history:
            return

        # Extract successful interaction patterns
        successful_patterns = []

        for i in range(1, len(context.conversation_history), 2):
            if i + 1 < len(context.conversation_history):
                user_msg = context.conversation_history[i]
                assistant_msg = context.conversation_history[i + 1]

                # Check if this was a successful interaction
                if assistant_msg.get("type") == "assistant":
                    pattern = {
                        "user_input_pattern": self._extract_pattern(user_msg["content"]),
                        "successful_response": assistant_msg["content"],
                        "topic": context.current_topic,
                        "timestamp": assistant_msg["timestamp"]
                    }
                    successful_patterns.append(pattern)

        if successful_patterns:
            user_key = context.user_id or "anonymous"
            self.memory_patterns[user_key].extend(successful_patterns)

            # Keep only recent patterns
            if len(self.memory_patterns[user_key]) > 100:
                self.memory_patterns[user_key] = self.memory_patterns[user_key][-100:]

    def _extract_pattern(self, text: Union[str, Dict[str, Any]]) -> str:
        """Extract pattern from text for memory matching."""
        if isinstance(text, dict):
            text = str(text)

        # Simple pattern extraction - in production would use NLP
        # Remove specific details and keep structure
        pattern = re.sub(r'\b\d+\b', 'NUMBER', text)
        pattern = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'EMAIL', pattern)
        pattern = re.sub(r'\b\d{1,2}/\d{1,2}/\d{4}\b', 'DATE', pattern)

        return pattern.lower()

    async def _persist_conversation(self, context: ConversationContext):
        """Persist conversation to long-term storage."""
        # In production, this would save to database
        # For now, just update cache
        await self.cache.set(f"archived_conversation_{context.conversation_id}",
                           context.get_conversation_summary(), ttl_seconds=604800)  # 7 days

    def get_memory_patterns(self, user_id: str) -> List[Dict[str, Any]]:
        """Get memory patterns for a user."""
        return self.memory_patterns.get(user_id, [])

    def get_active_conversations_count(self) -> int:
        """Get count of active conversations."""
        return len(self.active_conversations)


class AdvancedIntentRecognizer:
    """Advanced intent recognition with context awareness."""

    def __init__(self):
        self.intent_patterns: Dict[str, List[Dict[str, Any]]] = self._load_intent_patterns()
        self.entity_extractors: Dict[str, Callable] = self._load_entity_extractors()
        self.context_analyzer = ContextAnalyzer()

    def _load_intent_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load intent recognition patterns."""
        return {
            "document_analysis": [
                {"pattern": r"analyze|examine|review|check", "weight": 0.8},
                {"pattern": r"document|file|content|text", "weight": 0.6},
                {"pattern": r"consistency|quality|issues|problems", "weight": 0.7}
            ],
            "search_query": [
                {"pattern": r"find|search|lookup|locate", "weight": 0.9},
                {"pattern": r"information|data|details|about", "weight": 0.5}
            ],
            "workflow_execution": [
                {"pattern": r"run|execute|perform|do", "weight": 0.8},
                {"pattern": r"workflow|process|task|job", "weight": 0.7}
            ],
            "data_ingestion": [
                {"pattern": r"import|load|ingest|upload", "weight": 0.8},
                {"pattern": r"data|files|documents|content", "weight": 0.6}
            ],
            "summarization": [
                {"pattern": r"summarize|summary|abstract|overview", "weight": 0.9},
                {"pattern": r"short|brief|concise|key.*points", "weight": 0.6}
            ],
            "clarification_request": [
                {"pattern": r"what|how|when|where|why|who", "weight": 0.4},
                {"pattern": r"mean|clarify|explain|help", "weight": 0.5}
            ]
        }

    def _load_entity_extractors(self) -> Dict[str, Callable]:
        """Load entity extraction functions."""
        return {
            "document_type": self._extract_document_type,
            "file_path": self._extract_file_path,
            "date_range": self._extract_date_range,
            "person_name": self._extract_person_name,
            "organization": self._extract_organization,
            "location": self._extract_location
        }

    async def recognize_intent(self, input_text: str, conversation_context: Optional[ConversationContext] = None) -> IntentResult:
        """Recognize intent from input text with context awareness."""
        start_time = time.time()

        # Preprocess input
        processed_text = self._preprocess_text(input_text)

        # Get base intent scores
        intent_scores = self._calculate_intent_scores(processed_text)

        # Apply context awareness
        if conversation_context:
            intent_scores = await self._apply_context_awareness(intent_scores, conversation_context)

        # Determine primary intent
        primary_intent, confidence_score = self._select_primary_intent(intent_scores)

        # Extract entities
        entities = self._extract_entities(processed_text)

        # Determine confidence level
        confidence_level = self._calculate_confidence_level(confidence_score)

        # Check if clarification is needed
        requires_clarification, clarification_question = self._check_clarification_needed(
            intent_scores, confidence_score, entities
        )

        # Build context
        context = {
            "processed_text": processed_text,
            "intent_scores": intent_scores,
            "conversation_state": conversation_context.current_state.value if conversation_context else "unknown",
            "topic": conversation_context.current_topic if conversation_context else None,
            "entity_count": len(entities)
        }

        # Calculate alternative intents
        alternative_intents = self._get_alternative_intents(intent_scores, primary_intent)

        processing_time = (time.time() - start_time) * 1000

        return IntentResult(
            intent=primary_intent,
            confidence=confidence_level,
            confidence_score=confidence_score,
            entities=entities,
            context=context,
            alternative_intents=alternative_intents,
            processing_time_ms=processing_time,
            requires_clarification=requires_clarification,
            clarification_question=clarification_question
        )

    def _preprocess_text(self, text: str) -> str:
        """Preprocess input text for intent recognition."""
        # Convert to lowercase
        text = text.lower()

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove punctuation (keep some for context)
        text = re.sub(r'[^\w\s\?\.\!\,\:\;\'\"]', '', text)

        return text

    def _calculate_intent_scores(self, text: str) -> Dict[str, float]:
        """Calculate intent scores based on pattern matching."""
        scores = {}

        for intent, patterns in self.intent_patterns.items():
            score = 0.0
            matches = 0

            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                weight = pattern_info["weight"]

                if re.search(pattern, text, re.IGNORECASE):
                    score += weight
                    matches += 1

            # Normalize score based on matches
            if matches > 0:
                scores[intent] = score / matches
            else:
                scores[intent] = 0.0

        return scores

    async def _apply_context_awareness(self, scores: Dict[str, float],
                                     context: ConversationContext) -> Dict[str, float]:
        """Apply context awareness to intent scores."""
        # Boost scores based on conversation state
        if context.current_state == ConversationState.QUESTIONING:
            # More likely to be asking for clarification
            scores["clarification_request"] = scores.get("clarification_request", 0) + 0.3

        # Boost based on current topic
        if context.current_topic:
            topic_keywords = context.current_topic.lower().split()
            for intent in scores:
                intent_keywords = intent.replace("_", " ").split()
                overlap = len(set(topic_keywords) & set(intent_keywords))
                if overlap > 0:
                    scores[intent] += 0.2 * overlap

        # Boost based on recent conversation history
        recent_messages = context.get_recent_context(3)
        for message in recent_messages:
            if message["type"] == "assistant":
                # Look for patterns in assistant responses
                response_text = str(message["content"]).lower()
                for intent in scores:
                    if intent.replace("_", " ") in response_text:
                        scores[intent] += 0.1

        return scores

    def _select_primary_intent(self, scores: Dict[str, float]) -> tuple[str, float]:
        """Select the primary intent from scores."""
        if not scores:
            return "unknown", 0.0

        # Find intent with highest score
        primary_intent = max(scores.items(), key=lambda x: x[1])
        return primary_intent[0], primary_intent[1]

    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from text."""
        entities = {}

        for entity_type, extractor in self.entity_extractors.items():
            extracted = extractor(text)
            if extracted:
                entities[entity_type] = extracted

        return entities

    def _calculate_confidence_level(self, score: float) -> IntentConfidence:
        """Calculate confidence level from score."""
        if score >= 0.8:
            return IntentConfidence.VERY_HIGH
        elif score >= 0.6:
            return IntentConfidence.HIGH
        elif score >= 0.4:
            return IntentConfidence.MEDIUM
        else:
            return IntentConfidence.LOW

    def _check_clarification_needed(self, scores: Dict[str, float], primary_score: float,
                                  entities: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Check if clarification is needed."""
        # Low confidence
        if primary_score < 0.5:
            return True, "Could you please provide more details about what you'd like me to help you with?"

        # Multiple high-confidence intents (ambiguous)
        high_confidence_intents = [intent for intent, score in scores.items() if score >= 0.6]
        if len(high_confidence_intents) > 1:
            intent_names = [intent.replace("_", " ") for intent in high_confidence_intents[:3]]
            return True, f"I detected multiple possible intents: {', '.join(intent_names)}. Could you clarify which one you meant?"

        # Missing critical entities
        if not entities and any(keyword in scores for keyword in ["document_analysis", "search_query"]):
            return True, "Could you specify what document or information you're looking for?"

        return False, None

    def _get_alternative_intents(self, scores: Dict[str, float], primary_intent: str) -> List[Dict[str, Any]]:
        """Get alternative intents sorted by score."""
        alternatives = []

        for intent, score in scores.items():
            if intent != primary_intent and score > 0.3:
                alternatives.append({
                    "intent": intent,
                    "confidence_score": score,
                    "confidence": self._calculate_confidence_level(score).value
                })

        # Sort by confidence score
        alternatives.sort(key=lambda x: x["confidence_score"], reverse=True)

        return alternatives[:3]  # Return top 3 alternatives

    # Entity extraction methods
    def _extract_document_type(self, text: str) -> Optional[str]:
        """Extract document type from text."""
        doc_types = ["pdf", "docx", "doc", "txt", "md", "json", "xml", "html", "csv"]
        for doc_type in doc_types:
            if doc_type in text:
                return doc_type
        return None

    def _extract_file_path(self, text: str) -> Optional[str]:
        """Extract file path from text."""
        # Simple path pattern matching
        path_pattern = r'[\w\-\.\/]+\.[\w]+'
        match = re.search(path_pattern, text)
        return match.group(0) if match else None

    def _extract_date_range(self, text: str) -> Optional[Dict[str, str]]:
        """Extract date range from text."""
        # Simple date pattern matching
        date_pattern = r'\b\d{1,2}/\d{1,2}/\d{4}\b'
        dates = re.findall(date_pattern, text)

        if len(dates) >= 2:
            return {"start_date": dates[0], "end_date": dates[1]}
        elif len(dates) == 1:
            return {"date": dates[0]}

        return None

    def _extract_person_name(self, text: str) -> Optional[str]:
        """Extract person name from text (simplified)."""
        # Look for capitalized words that might be names
        words = text.split()
        potential_names = []

        for word in words:
            if word[0].isupper() and len(word) > 2:
                potential_names.append(word)

        return " ".join(potential_names) if potential_names else None

    def _extract_organization(self, text: str) -> Optional[str]:
        """Extract organization name from text."""
        # Simple organization pattern
        org_keywords = ["inc", "corp", "ltd", "llc", "company", "organization", "team", "group"]
        words = text.split()

        for i, word in enumerate(words):
            if word.lower() in org_keywords and i > 0:
                return " ".join(words[max(0, i-2):i+1])

        return None

    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location from text."""
        # Simple location pattern (could be enhanced with NLP)
        location_indicators = [" in ", " at ", " from ", " to "]

        for indicator in location_indicators:
            if indicator in text:
                parts = text.split(indicator)
                if len(parts) > 1:
                    location_part = parts[1].split()[0]
                    if location_part[0].isupper():
                        return location_part

        return None


class ContextAnalyzer:
    """Context analyzer for conversation understanding."""

    def __init__(self):
        self.topic_keywords = self._load_topic_keywords()

    def _load_topic_keywords(self) -> Dict[str, List[str]]:
        """Load topic keywords for context analysis."""
        return {
            "documentation": ["document", "docs", "manual", "guide", "readme", "api", "code"],
            "analysis": ["analyze", "review", "check", "quality", "consistency", "issues"],
            "search": ["find", "search", "lookup", "query", "information", "data"],
            "workflow": ["run", "execute", "process", "task", "job", "workflow"],
            "data_management": ["import", "export", "upload", "download", "sync", "backup"]
        }

    def analyze_context(self, text: str, conversation_context: Optional[ConversationContext] = None) -> Dict[str, Any]:
        """Analyze context from text and conversation."""
        context_analysis = {
            "detected_topics": [],
            "sentiment": "neutral",
            "complexity": "simple",
            "urgency": "normal",
            "domain_expertise": "general"
        }

        # Detect topics
        context_analysis["detected_topics"] = self._detect_topics(text)

        # Analyze sentiment (simplified)
        context_analysis["sentiment"] = self._analyze_sentiment(text)

        # Analyze complexity
        context_analysis["complexity"] = self._analyze_complexity(text)

        # Analyze urgency
        context_analysis["urgency"] = self._analyze_urgency(text)

        # Determine domain expertise needed
        context_analysis["domain_expertise"] = self._determine_domain_expertise(text, context_analysis["detected_topics"])

        # Incorporate conversation context
        if conversation_context:
            context_analysis.update(self._incorporate_conversation_context(conversation_context))

        return context_analysis

    def _detect_topics(self, text: str) -> List[str]:
        """Detect topics from text."""
        detected_topics = []
        text_lower = text.lower()

        for topic, keywords in self.topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_topics.append(topic)

        return detected_topics

    def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of text (simplified)."""
        positive_words = ["good", "great", "excellent", "amazing", "perfect", "help", "thanks"]
        negative_words = ["bad", "wrong", "error", "problem", "issue", "fail", "broken"]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def _analyze_complexity(self, text: str) -> str:
        """Analyze complexity of text."""
        word_count = len(text.split())
        sentence_count = len([s for s in text.split('.') if s.strip()])

        if word_count > 50 or sentence_count > 3:
            return "complex"
        elif word_count > 20 or sentence_count > 1:
            return "moderate"
        else:
            return "simple"

    def _analyze_urgency(self, text: str) -> str:
        """Analyze urgency from text."""
        urgent_keywords = ["urgent", "asap", "immediately", "critical", "emergency", "now", "quickly"]
        text_lower = text.lower()

        if any(keyword in text_lower for keyword in urgent_keywords):
            return "high"
        elif "?" in text or "help" in text_lower:
            return "medium"
        else:
            return "normal"

    def _determine_domain_expertise(self, text: str, topics: List[str]) -> str:
        """Determine domain expertise needed."""
        if "documentation" in topics or "code" in text.lower():
            return "technical"
        elif "analysis" in topics:
            return "analytical"
        elif "search" in topics:
            return "information_management"
        else:
            return "general"

    def _incorporate_conversation_context(self, context: ConversationContext) -> Dict[str, Any]:
        """Incorporate conversation context into analysis."""
        context_updates = {}

        # Adjust based on conversation state
        if context.current_state == ConversationState.ERROR:
            context_updates["sentiment"] = "negative"
            context_updates["urgency"] = "high"

        # Adjust based on conversation history
        recent_messages = context.get_recent_context(3)
        if len(recent_messages) > 2:
            context_updates["complexity"] = "complex"

        # Adjust based on current topic
        if context.current_topic:
            context_updates["detected_topics"] = [context.current_topic]

        return context_updates


class MultiModalProcessor:
    """Multi-modal input processor for advanced NLP."""

    def __init__(self):
        self.supported_modalities = ["text", "audio", "image", "video"]
        self.processing_pipelines: Dict[str, Callable] = {}

    async def process_input(self, input_data: Dict[str, Any]) -> MultiModalInput:
        """Process multi-modal input data."""
        start_time = time.time()

        result = MultiModalInput()

        # Process each modality
        for modality in self.supported_modalities:
            if modality in input_data:
                processor = self.processing_pipelines.get(modality, self._default_processor)
                processed_data = await processor(input_data[modality])

                # Store results based on modality
                if modality == "text":
                    result.text_content = processed_data.get("content")
                elif modality == "audio":
                    result.audio_transcript = processed_data.get("transcript")
                elif modality == "image":
                    result.image_description = processed_data.get("description")
                elif modality == "video":
                    result.video_transcript = processed_data.get("transcript")

                result.modalities_used.append(modality)
                result.confidence_scores[modality] = processed_data.get("confidence", 0.5)

        result.processing_time_ms = (time.time() - start_time) * 1000

        return result

    async def _default_processor(self, data: Any) -> Dict[str, Any]:
        """Default processing for unsupported modalities."""
        return {
            "content": str(data),
            "confidence": 0.5
        }

    def register_processor(self, modality: str, processor: Callable):
        """Register a processor for a specific modality."""
        self.processing_pipelines[modality] = processor

    def get_supported_modalities(self) -> List[str]:
        """Get list of supported modalities."""
        return self.supported_modalities.copy()


# Global instances
conversation_memory = ConversationMemoryManager()
intent_recognizer = AdvancedIntentRecognizer()
multi_modal_processor = MultiModalProcessor()


async def initialize_advanced_nlp():
    """Initialize advanced NLP capabilities."""
    print("🧠 Initializing Advanced NLP Engine...")

    # Register multi-modal processors
    multi_modal_processor.register_processor("text", lambda x: {"content": x, "confidence": 1.0})
    multi_modal_processor.register_processor("audio", lambda x: {"transcript": f"[Audio: {x}]", "confidence": 0.8})
    multi_modal_processor.register_processor("image", lambda x: {"description": f"[Image: {x}]", "confidence": 0.7})

    print("✅ Advanced NLP Engine initialized")
    print("   • Conversation memory management: Active")
    print("   • Intent recognition: Context-aware")
    print("   • Multi-modal processing: Ready")
    print("   • Memory patterns: Learning enabled")


# Test functions
async def test_advanced_nlp():
    """Test advanced NLP capabilities."""
    print("🧪 Testing Advanced NLP Engine")
    print("=" * 50)

    # Initialize NLP engine
    await initialize_advanced_nlp()

    # Test conversation creation
    conversation = await conversation_memory.create_conversation("test_user", "test_session")
    print(f"✅ Created conversation: {conversation.conversation_id}")

    # Test intent recognition
    test_queries = [
        "Can you analyze this document for consistency issues?",
        "Find all documentation about API endpoints",
        "Run the workflow for processing customer data",
        "What do you mean by that?"
    ]

    for query in test_queries:
        print(f"\n🔍 Analyzing: '{query}'")

        # Add to conversation
        conversation.add_message({"text": query, "type": "user"})

        # Recognize intent
        intent_result = await intent_recognizer.recognize_intent(query, conversation)

        print(f"   Intent: {intent_result.intent}")
        print(f"   Confidence: {intent_result.confidence.value} ({intent_result.confidence_score:.2f})")
        print(f"   Entities: {intent_result.entities}")
        print(f"   Processing time: {intent_result.processing_time_ms:.2f}ms")

        if intent_result.requires_clarification:
            print(f"   Clarification needed: {intent_result.clarification_question}")

        # Add response to conversation
        conversation.add_message({
            "intent": intent_result.intent,
            "confidence": intent_result.confidence_score
        }, "assistant")

    # Test multi-modal processing
    print("\n🎭 Testing Multi-Modal Processing:")
    multi_modal_input = {
        "text": "Please analyze this image",
        "image": "diagram.png"
    }

    processed = await multi_modal_processor.process_input(multi_modal_input)
    print(f"   Combined content: {processed.get_combined_content()}")
    print(f"   Primary content: {processed.get_primary_content()}")
    print(f"   Modalities used: {processed.modalities_used}")
    print(f"   Processing time: {processed.processing_time_ms:.2f}ms")

    # Test conversation summary
    print("\n📊 Conversation Summary:")
    summary = conversation.get_conversation_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")

    print("\n🎉 Advanced NLP Engine Test Complete!")
    print("Features demonstrated:")
    print("   ✅ Conversation memory management")
    print("   ✅ Context-aware intent recognition")
    print("   ✅ Multi-modal input processing")
    print("   ✅ Entity extraction and analysis")
    print("   ✅ Clarification request generation")
    print("   ✅ Real-time processing performance")


if __name__ == "__main__":
    asyncio.run(test_advanced_nlp())
