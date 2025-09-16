"""Prompt refinement service implementation.

Orchestrates LLM-assisted prompt refinement with document storage and comparison.
"""

import asyncio
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone

from services.prompt_store.domain.prompts.service import PromptService
from services.prompt_store.infrastructure.cache import prompt_store_cache
from services.shared.utilities import generate_id, utc_now

# Import LLM service clients
try:
    from services.shared.clients import ServiceClients
    LLM_SERVICES_AVAILABLE = True
except ImportError:
    LLM_SERVICES_AVAILABLE = False

# Import doc store client
try:
    from services.doc_store.domain.documents.service import DocumentService
    DOC_STORE_AVAILABLE = True
except ImportError:
    DOC_STORE_AVAILABLE = False


class PromptRefinementService:
    """Service for LLM-assisted prompt refinement workflows."""

    def __init__(self):
        self.prompt_service = PromptService()
        self.llm_clients = ServiceClients() if LLM_SERVICES_AVAILABLE else None
        self.doc_service = None  # Will be initialized when needed

    async def initialize_doc_service(self):
        """Initialize doc store service connection."""
        if DOC_STORE_AVAILABLE and not self.doc_service:
            # Import here to avoid circular imports
            from services.doc_store.domain.documents.service import DocumentService
            self.doc_service = DocumentService()

    async def refine_prompt(self, prompt_id: str, refinement_instructions: str,
                           llm_service: str = "interpreter",
                           context_documents: Optional[List[str]] = None,
                           user_id: str = "system") -> Dict[str, Any]:
        """Execute prompt refinement workflow using LLM service.

        1. Get original prompt
        2. Send to LLM service with refinement instructions
        3. Store refinement result in doc_store
        4. Return refinement session info
        """
        if not LLM_SERVICES_AVAILABLE:
            raise ValueError("LLM services not available for prompt refinement")

        await self.initialize_doc_service()
        if not self.doc_service:
            raise ValueError("Doc store service not available for storing refinement results")

        # Get original prompt
        original_prompt = self.prompt_service.get_entity(prompt_id)
        if not original_prompt:
            raise ValueError(f"Prompt {prompt_id} not found")

        # Create refinement session
        session_id = generate_id()
        refinement_session = {
            "id": session_id,
            "original_prompt_id": prompt_id,
            "refinement_instructions": refinement_instructions,
            "llm_service": llm_service,
            "context_documents": context_documents or [],
            "status": "processing",
            "created_at": utc_now(),
            "user_id": user_id
        }

        # Cache session info
        await prompt_store_cache.set(f"refinement_session:{session_id}", refinement_session, ttl=3600)

        # Start async refinement process
        asyncio.create_task(self._execute_refinement_async(session_id, original_prompt,
                                                         refinement_instructions, llm_service,
                                                         context_documents, user_id))

        return {
            "session_id": session_id,
            "status": "processing",
            "message": "Prompt refinement started. Check status for results."
        }

    async def get_refinement_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of a refinement session."""
        session = await prompt_store_cache.get(f"refinement_session:{session_id}")
        if not session:
            raise ValueError(f"Refinement session {session_id} not found")

        return session

    async def compare_prompt_versions(self, prompt_id: str, version_a: Optional[int] = None,
                                    version_b: Optional[int] = None) -> Dict[str, Any]:
        """Compare different versions of a prompt."""
        prompt = self.prompt_service.get_entity(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt {prompt_id} not found")

        # Get versions to compare
        if version_a is None:
            version_a = prompt.version  # Current version
        if version_b is None:
            version_b = max(1, prompt.version - 1)  # Previous version

        # Get version details (this would need to be implemented in the versioning repository)
        version_a_data = await self._get_prompt_version_data(prompt_id, version_a)
        version_b_data = await self._get_prompt_version_data(prompt_id, version_b)

        if not version_a_data or not version_b_data:
            raise ValueError("Version data not available for comparison")

        # Perform diff analysis
        differences = self._calculate_prompt_differences(version_a_data, version_b_data)

        return {
            "prompt_id": prompt_id,
            "comparison": {
                "version_a": version_a_data,
                "version_b": version_b_data,
                "differences": differences
            }
        }

    async def compare_refinement_documents(self, session_a: str, session_b: str) -> Dict[str, Any]:
        """Compare documents from different refinement sessions."""
        await self.initialize_doc_service()

        session_a_data = await prompt_store_cache.get(f"refinement_session:{session_a}")
        session_b_data = await prompt_store_cache.get(f"refinement_session:{session_b}")

        if not session_a_data or not session_b_data:
            raise ValueError("One or both refinement sessions not found")

        doc_a_id = session_a_data.get("result_document_id")
        doc_b_id = session_b_data.get("result_document_id")

        if not doc_a_id or not doc_b_id:
            raise ValueError("Result documents not available for comparison")

        # Get documents from doc store
        doc_a = await self.doc_service.get_entity(doc_a_id)
        doc_b = await self.doc_service.get_entity(doc_b_id)

        if not doc_a or not doc_b:
            raise ValueError("Documents not found in doc store")

        # Compare document contents
        differences = self._calculate_document_differences(doc_a, doc_b)

        return {
            "session_a": session_a,
            "session_b": session_b,
            "document_comparison": {
                "document_a": doc_a.to_dict(),
                "document_b": doc_b.to_dict(),
                "differences": differences
            }
        }

    async def replace_prompt_with_refined(self, prompt_id: str, session_id: str,
                                        user_id: str = "system") -> Dict[str, Any]:
        """Replace original prompt with refined version from session."""
        session = await prompt_store_cache.get(f"refinement_session:{session_id}")
        if not session or session.get("status") != "completed":
            raise ValueError("Refinement session not completed")

        # Get the refined prompt content from the result document
        result_doc_id = session.get("result_document_id")
        if not result_doc_id:
            raise ValueError("No result document found for session")

        await self.initialize_doc_service()
        result_doc = await self.doc_service.get_entity(result_doc_id)
        if not result_doc:
            raise ValueError("Result document not found")

        # Extract refined prompt from document (this would depend on the document structure)
        refined_content = self._extract_refined_prompt_from_document(result_doc)

        # Update the original prompt with versioning
        updated_prompt = self.prompt_service.update_prompt_content(
            prompt_id=prompt_id,
            content=refined_content,
            change_summary=f"Refined using LLM service: {session.get('llm_service')}",
            updated_by=user_id
        )

        # Mark session as applied
        session["applied_to_prompt"] = prompt_id
        session["applied_at"] = utc_now()
        await prompt_store_cache.set(f"refinement_session:{session_id}", session, ttl=3600)

        return {
            "prompt_id": prompt_id,
            "new_version": updated_prompt.version,
            "session_id": session_id,
            "message": f"Prompt updated to version {updated_prompt.version}"
        }

    async def _execute_refinement_async(self, session_id: str, original_prompt: Any,
                                      refinement_instructions: str, llm_service: str,
                                      context_documents: Optional[List[str]],
                                      user_id: str) -> None:
        """Execute the refinement workflow asynchronously."""
        try:
            # Update session status
            session = await prompt_store_cache.get(f"refinement_session:{session_id}")
            session["status"] = "processing"
            await prompt_store_cache.set(f"refinement_session:{session_id}", session, ttl=3600)

            # Prepare LLM request
            llm_request = self._prepare_llm_refinement_request(
                original_prompt, refinement_instructions, context_documents
            )

            # Call LLM service
            llm_response = await self._call_llm_service(llm_service, llm_request)

            # Store result in doc_store
            result_doc_id = await self._store_refinement_result(
                session_id, original_prompt, llm_response, llm_service, user_id
            )

            # Update session with completion
            session["status"] = "completed"
            session["result_document_id"] = result_doc_id
            session["completed_at"] = utc_now()
            await prompt_store_cache.set(f"refinement_session:{session_id}", session, ttl=3600)

        except Exception as e:
            # Update session with error
            session = await prompt_store_cache.get(f"refinement_session:{session_id}")
            session["status"] = "failed"
            session["error"] = str(e)
            session["failed_at"] = utc_now()
            await prompt_store_cache.set(f"refinement_session:{session_id}", session, ttl=3600)

    def _prepare_llm_refinement_request(self, prompt: Any, instructions: str,
                                      context_docs: Optional[List[str]] = None) -> Dict[str, Any]:
        """Prepare the request to send to LLM service for refinement."""
        request = {
            "task": "prompt_refinement",
            "original_prompt": {
                "name": prompt.name,
                "category": prompt.category,
                "content": prompt.content,
                "variables": prompt.variables,
                "description": prompt.description
            },
            "refinement_instructions": instructions,
            "context": []
        }

        # Add context documents if provided
        if context_docs:
            request["context"] = context_docs

        return request

    async def _call_llm_service(self, service_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Call the specified LLM service for refinement."""
        if not self.llm_clients:
            raise ValueError("LLM services not available")

        # This would need to be implemented based on the actual LLM service APIs
        # For now, return a mock response
        if service_name == "interpreter":
            return await self.llm_clients.call_interpreter(request)
        elif service_name == "bedrock-proxy":
            return await self.llm_clients.call_bedrock(request)
        else:
            raise ValueError(f"Unsupported LLM service: {service_name}")

    async def _store_refinement_result(self, session_id: str, original_prompt: Any,
                                     llm_response: Dict[str, Any], llm_service: str,
                                     user_id: str) -> str:
        """Store refinement result in doc_store."""
        await self.initialize_doc_service()

        # Create document content from LLM response
        doc_content = self._format_refinement_result_as_document(
            session_id, original_prompt, llm_response, llm_service
        )

        # Create document in doc_store
        doc_data = {
            "content": doc_content,
            "content_type": "prompt_refinement_result",
            "metadata": {
                "session_id": session_id,
                "original_prompt_id": original_prompt.id,
                "llm_service": llm_service,
                "refinement_type": "llm_assisted",
                "user_id": user_id
            },
            "correlation_id": f"refinement_{session_id}"
        }

        result_doc = await self.doc_service.create_entity(doc_data)
        return result_doc.id

    def _format_refinement_result_as_document(self, session_id: str, original_prompt: Any,
                                            llm_response: Dict[str, Any], llm_service: str) -> str:
        """Format LLM refinement result as a document."""
        # This would format the refinement result in a structured way
        # For now, return a simple formatted document
        return f"""# Prompt Refinement Result

**Session ID:** {session_id}
**Original Prompt:** {original_prompt.name}
**LLM Service:** {llm_service}
**Timestamp:** {utc_now().isoformat()}

## Original Prompt
```
{original_prompt.content}
```

## Refined Prompt
```
{llm_response.get('refined_prompt', 'No refined prompt provided')}
```

## Refinement Analysis
{llm_response.get('analysis', 'No analysis provided')}

## Suggested Improvements
{llm_response.get('suggestions', 'No suggestions provided')}
"""

    async def _get_prompt_version_data(self, prompt_id: str, version: int) -> Optional[Dict[str, Any]]:
        """Get data for a specific prompt version."""
        # This would need to be implemented in the versioning repository
        # For now, return mock data
        return {
            "version": version,
            "content": f"Version {version} content",
            "variables": ["var1", "var2"],
            "created_at": utc_now().isoformat()
        }

    def _calculate_prompt_differences(self, version_a: Dict[str, Any],
                                    version_b: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate differences between prompt versions."""
        differences = {
            "content_changed": version_a.get("content") != version_b.get("content"),
            "variables_added": [],
            "variables_removed": [],
            "content_diff": self._simple_text_diff(
                version_a.get("content", ""),
                version_b.get("content", "")
            )
        }

        # Compare variables
        vars_a = set(version_a.get("variables", []))
        vars_b = set(version_b.get("variables", []))
        differences["variables_added"] = list(vars_b - vars_a)
        differences["variables_removed"] = list(vars_a - vars_b)

        return differences

    def _calculate_document_differences(self, doc_a: Any, doc_b: Any) -> Dict[str, Any]:
        """Calculate differences between refinement result documents."""
        return {
            "content_diff": self._simple_text_diff(doc_a.content, doc_b.content),
            "metadata_diff": self._compare_metadata(doc_a.metadata, doc_b.metadata)
        }

    def _simple_text_diff(self, text_a: str, text_b: str) -> str:
        """Simple text difference calculation."""
        # This is a very basic diff - in production you'd use a proper diff library
        if text_a == text_b:
            return "No differences"
        return f"Content changed from {len(text_a)} to {len(text_b)} characters"

    def _compare_metadata(self, meta_a: Dict[str, Any], meta_b: Dict[str, Any]) -> Dict[str, Any]:
        """Compare document metadata."""
        return {
            "keys_added": list(set(meta_b.keys()) - set(meta_a.keys())),
            "keys_removed": list(set(meta_a.keys()) - set(meta_b.keys())),
            "values_changed": [k for k in meta_a.keys() & meta_b.keys() if meta_a[k] != meta_b[k]]
        }

    def _extract_refined_prompt_from_document(self, document: Any) -> str:
        """Extract refined prompt content from result document."""
        # This would parse the document to extract the refined prompt
        # For now, return the document content as-is
        return document.content
