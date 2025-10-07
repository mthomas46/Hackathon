"""Context Session entity - represents a conversation context."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4


@dataclass
class Message:
    """A single message in the conversation."""
    role: str  # "system", "user", "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    token_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "token_count": self.token_count,
        }


@dataclass
class ContextSession:
    """
    Domain entity representing a conversation context session.
    
    Maintains conversation history and manages context window limits.
    """
    
    id: UUID = field(default_factory=uuid4)
    model_name: str = ""
    messages: List[Message] = field(default_factory=list)
    max_context_tokens: int = 2048
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, token_count: int = 0) -> None:
        """
        Add a message to the context.
        
        Args:
            role: Message role (system/user/assistant)
            content: Message content
            token_count: Number of tokens in message
        """
        message = Message(role=role, content=content, token_count=token_count)
        self.messages.append(message)
        self.last_accessed = datetime.utcnow()
        
        # Trim context if exceeds max tokens
        self._trim_context()
    
    def _trim_context(self) -> None:
        """Trim context to fit within token limit."""
        total_tokens = sum(msg.token_count for msg in self.messages)
        
        # Remove oldest messages (keep system message if present)
        while total_tokens > self.max_context_tokens and len(self.messages) > 1:
            # Keep first message if it's a system message
            if self.messages[0].role == "system" and len(self.messages) > 1:
                removed = self.messages.pop(1)
            else:
                removed = self.messages.pop(0)
            total_tokens -= removed.token_count
    
    def get_total_tokens(self) -> int:
        """Get total token count of context."""
        return sum(msg.token_count for msg in self.messages)
    
    def get_message_count(self) -> int:
        """Get number of messages in context."""
        return len(self.messages)
    
    def clear(self) -> None:
        """Clear all messages except system message."""
        system_messages = [msg for msg in self.messages if msg.role == "system"]
        self.messages = system_messages
        self.last_accessed = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context session to dictionary."""
        return {
            "id": str(self.id),
            "model_name": self.model_name,
            "messages": [msg.to_dict() for msg in self.messages],
            "max_context_tokens": self.max_context_tokens,
            "total_tokens": self.get_total_tokens(),
            "message_count": self.get_message_count(),
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "metadata": self.metadata,
        }

