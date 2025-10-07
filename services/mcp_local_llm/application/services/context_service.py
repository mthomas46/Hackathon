"""Context Management Application Service."""

from typing import List, Optional

from ...domain.entities.context_session import ContextSession
from ...domain.value_objects.context_message import ContextMessage
from ...domain.repositories.context_repository import ContextRepository


class ContextService:
    """
    Application service for context session management.
    
    Handles conversation context and history.
    """
    
    def __init__(self, context_repo: ContextRepository):
        """Initialize context service."""
        self.context_repo = context_repo
    
    async def create_session(
        self,
        model_id: str,
        user_id: Optional[str] = None,
        context_window_size: int = 4096,
    ) -> ContextSession:
        """
        Create context session.
        
        Args:
            model_id: Model identifier
            user_id: User identifier
            context_window_size: Context window size in tokens
            
        Returns:
            Created context session
        """
        session = ContextSession(
            session_id=f"ctx_{model_id}",
            model_id=model_id,
            user_id=user_id,
            context_window_size=context_window_size,
        )
        
        await self.context_repo.add(session)
        return session
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> ContextSession:
        """
        Add message to session.
        
        Args:
            session_id: Session identifier
            role: Message role (system, user, assistant)
            content: Message content
            
        Returns:
            Updated session
            
        Raises:
            ValueError: If session not found
        """
        session = await self.context_repo.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        message = ContextMessage(
            role=role,
            content=content,
        )
        
        session.add_message(message)
        await self.context_repo.update(session)
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[ContextSession]:
        """Get session by ID."""
        return await self.context_repo.get_by_id(session_id)
    
    async def list_user_sessions(self, user_id: str) -> List[ContextSession]:
        """List sessions for user."""
        return await self.context_repo.list_by_user_id(user_id)
    
    async def clear_session(self, session_id: str) -> ContextSession:
        """
        Clear session history.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Cleared session
        """
        session = await self.context_repo.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        session.messages = []
        session.current_token_count = 0
        await self.context_repo.update(session)
        
        return session

