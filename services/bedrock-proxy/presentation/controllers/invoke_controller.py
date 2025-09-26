"""Invoke controller for handling AI invoke requests."""

from typing import Any, Dict
from fastapi import HTTPException, status

from ..dto.request_dto import InvokeRequestDTO
from ..dto.response_dto import InvokeResponseDTO
from ...infrastructure.processor import process_invoke_request


class InvokeController:
    """Controller for AI invoke operations."""

    @staticmethod
    async def process_invoke_request(request: InvokeRequestDTO) -> InvokeResponseDTO:
        """Process an AI invoke request.

        Args:
            request: The invoke request data

        Returns:
            The invoke response data

        Raises:
            HTTPException: If processing fails
        """
        try:
            # Process the request using the infrastructure layer
            result = await process_invoke_request(
                prompt=request.prompt,
                model=request.model,
                region=request.region,
                template=request.template,
                format=request.format,
                title=request.title,
            )

            return InvokeResponseDTO(
                success=True,
                message="Request processed successfully",
                data=result
            )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Processing failed: {str(e)}"
            )
