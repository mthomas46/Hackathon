"""UI service domain service for DDD compliance."""

from typing import Optional
from ..entities.ui_state import UIStateEntity, UIState
from ..repositories.ui_state_repository import UIStateRepository


class UIService:
    """Domain service for UI operations."""

    def __init__(self, repository: UIStateRepository):
        self._repository = repository

    async def create_ui_state(self, user_id: str, session_id: str, initial_view: str = "dashboard") -> UIStateEntity:
        """Create new UI state for user."""
        ui_state = UIStateEntity(
            id=f"ui_{user_id}_{session_id}",
            user_id=user_id,
            current_view=initial_view,
            session_id=session_id
        )
        await self._repository.save(ui_state)
        return ui_state

    async def update_view(self, user_id: str, new_view: str) -> Optional[UIStateEntity]:
        """Update user's current view."""
        ui_state = await self._repository.find_by_user_id(user_id)
        if ui_state:
            ui_state.update_view(new_view)
            await self._repository.save(ui_state)
        return ui_state

    async def get_ui_state(self, user_id: str) -> Optional[UIStateEntity]:
        """Get UI state for user."""
        return await self._repository.find_by_user_id(user_id)
