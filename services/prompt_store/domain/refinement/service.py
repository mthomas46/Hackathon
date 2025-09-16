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
from services.shared.clients import ServiceClients

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
        self.llm_clients = ServiceClients()
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
        # LLM services are always available through ServiceClients

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

        # Extract refined prompt from document
        refined_content = self._extract_refined_prompt_from_document(result_doc)

        # Get original prompt for comparison
        original_prompt = self.prompt_service.get_entity(prompt_id)
        if not original_prompt:
            raise ValueError(f"Original prompt {prompt_id} not found")

        # Generate detailed change summary
        change_summary = self._generate_refinement_change_summary(
            original_prompt, refined_content, session, result_doc
        )

        # Update the original prompt with versioning
        updated_prompt = self.prompt_service.update_prompt_content(
            prompt_id=prompt_id,
            content=refined_content,
            change_summary=change_summary,
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
        if service_name == "interpreter":
            # Use interpreter service for natural language prompt refinement
            # Convert our refinement request to interpreter format
            interpreter_request = {
                "query": self._format_refinement_query_for_interpreter(request),
                "user_id": request.get("user_id", "system")
            }

            try:
                response = await self.llm_clients.interpret_query(
                    interpreter_request["query"],
                    interpreter_request["user_id"]
                )

                # Extract the refined prompt from interpreter response
                if response.get("success") and "data" in response:
                    interpreted_data = response["data"]
                    # The interpreter returns workflow/intent data, we need to extract refined prompt
                    return self._extract_refined_prompt_from_interpreter_response(interpreted_data, request)
                else:
                    raise ValueError(f"Interpreter service error: {response}")

            except Exception as e:
                raise ValueError(f"Failed to call interpreter service: {str(e)}")

        elif service_name == "bedrock-proxy":
            # Use bedrock-proxy for direct LLM refinement
            bedrock_request = {
                "prompt": self._format_refinement_prompt_for_bedrock(request),
                "template": "summary",  # Use summary template for refinement
                "format": "md",
                "model": "anthropic.claude-3-sonnet-20240229-v1:0"
            }

            try:
                response = await self._call_bedrock_service(bedrock_request)

                # Extract refined prompt from bedrock response
                if "output" in response:
                    return {"refined_content": response["output"]}
                else:
                    raise ValueError(f"Bedrock service returned invalid response: {response}")

            except Exception as e:
                raise ValueError(f"Failed to call bedrock service: {str(e)}")

        else:
            raise ValueError(f"Unsupported LLM service: {service_name}")

    async def _call_bedrock_service(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Call Bedrock proxy service directly."""
        import httpx

        bedrock_url = self.llm_clients.get_config_value("BEDROCK_PROXY_URL", "http://bedrock-proxy:7090/invoke", section="services", env_key="BEDROCK_PROXY_URL")

        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(bedrock_url, json=request)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise ValueError(f"Bedrock service HTTP error: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                raise ValueError(f"Bedrock service error: {str(e)}")

    def _format_refinement_query_for_interpreter(self, request: Dict[str, Any]) -> str:
        """Format refinement request as natural language query for interpreter."""
        original_prompt = request.get("original_prompt", {})
        instructions = request.get("refinement_instructions", "")

        query = f"""
        I have this prompt that needs refinement:

        Original Prompt:
        Name: {original_prompt.get('name', 'N/A')}
        Category: {original_prompt.get('category', 'N/A')}
        Content: {original_prompt.get('content', 'N/A')}

        Refinement Instructions: {instructions}

        Please provide an improved version of this prompt that addresses the refinement instructions.
        Focus on clarity, specificity, and effectiveness.
        """

        return query.strip()

    def _extract_refined_prompt_from_interpreter_response(self, interpreter_data: Dict[str, Any], original_request: Dict[str, Any]) -> Dict[str, Any]:
        """Extract refined prompt from interpreter service response."""
        # The interpreter service returns workflow/intent data
        # For refinement, we look for the interpreted intent and extract refined content

        if "intent" in interpreter_data:
            intent = interpreter_data["intent"]

            # If the intent indicates refinement, extract the refined prompt
            if "refine" in intent.lower() or "improve" in intent.lower():
                # Look for refined content in entities or response_text
                entities = interpreter_data.get("entities", {})
                response_text = interpreter_data.get("response_text", "")

                # Try to extract refined prompt from response
                if response_text:
                    return {"refined_content": response_text}
                elif "refined_prompt" in entities:
                    return {"refined_content": entities["refined_prompt"]}
                else:
                    # Fallback: use the original prompt with some basic improvements
                    original_content = original_request.get("original_prompt", {}).get("content", "")
                    return {"refined_content": f"Improved version of: {original_content}"}

        # Fallback response
        return {"refined_content": "Unable to refine prompt - interpreter service returned unexpected response"}

    def _format_refinement_prompt_for_bedrock(self, request: Dict[str, Any]) -> str:
        """Format refinement request as prompt for Bedrock."""
        original_prompt = request.get("original_prompt", {})
        instructions = request.get("refinement_instructions", "")

        prompt = f"""
You are an expert prompt engineer. Your task is to refine and improve the following prompt based on the given instructions.

Original Prompt:
- Name: {original_prompt.get('name', 'N/A')}
- Category: {original_prompt.get('category', 'N/A')}
- Content: {original_prompt.get('content', 'N/A')}

Refinement Instructions:
{instructions}

Please provide an improved version of this prompt that:
1. Is more clear and specific
2. Better achieves its intended purpose
3. Uses more effective language and structure
4. Addresses any issues mentioned in the refinement instructions

Provide only the refined prompt content, without additional explanation or formatting.
"""

        return prompt.strip()

    async def _store_refinement_result(self, session_id: str, original_prompt: Any,
                                     llm_response: Dict[str, Any], llm_service: str,
                                     user_id: str) -> str:
        """Store refinement result in doc_store."""
        await self.initialize_doc_service()

        # Create document content from LLM response
        doc_content = self._format_refinement_result_as_document(
            session_id, original_prompt, llm_response, llm_service
        )

        # Create document in doc_store with enhanced metadata
        doc_data = {
            "content": doc_content,
            "content_type": "prompt_refinement_result",
            "metadata": {
                "session_id": session_id,
                "original_prompt_id": original_prompt.id,
                "original_prompt_name": original_prompt.name,
                "original_prompt_version": original_prompt.version,
                "llm_service": llm_service,
                "refinement_type": "llm_assisted",
                "user_id": user_id,
                "llm_response": llm_response,  # Store full LLM response for extraction fallback
                "refined_content": llm_response.get('refined_content', ''),
                "created_at": utc_now().isoformat()
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
        content = document.content

        # Parse the document to extract the refined prompt
        # Look for the "Refined Prompt" section
        lines = content.split('\n')
        refined_section_found = False
        refined_prompt_lines = []

        for line in lines:
            if line.startswith('## Refined Prompt'):
                refined_section_found = True
                continue
            elif line.startswith('## ') and refined_section_found:
                # We've reached the next section, stop collecting
                break
            elif refined_section_found and line.startswith('```'):
                # Skip the code block markers
                continue
            elif refined_section_found:
                # Collect the refined prompt content
                refined_prompt_lines.append(line)

        if refined_prompt_lines:
            # Join the lines and clean up any extra whitespace
            refined_content = '\n'.join(refined_prompt_lines).strip()
            # Remove any trailing empty lines
            return '\n'.join([line for line in refined_content.split('\n') if line.strip()])
        else:
            # Fallback: try to extract from LLM response if stored in metadata
            if hasattr(document, 'metadata') and document.metadata:
                llm_response = document.metadata.get('llm_response', {})
                if isinstance(llm_response, dict) and 'refined_content' in llm_response:
                    return llm_response['refined_content']

            # Last resort: return the whole content
            return content

    def _generate_refinement_change_summary(self, original_prompt: Any, refined_content: str,
                                           session: Dict[str, Any], result_doc: Any) -> str:
        """Generate detailed change summary for refinement versioning."""
        import difflib

        # Calculate content differences
        original_lines = original_prompt.content.splitlines(keepends=True)
        refined_lines = refined_content.splitlines(keepends=True)

        # Get diff statistics
        diff = list(difflib.unified_diff(original_lines, refined_lines,
                                       fromfile='original', tofile='refined', lineterm=''))

        added_lines = len([line for line in diff if line.startswith('+') and not line.startswith('+++')])
        removed_lines = len([line for line in diff if line.startswith('-') and not line.startswith('---')])

        # Get session and LLM details
        llm_service = session.get('llm_service', 'unknown')
        refinement_instructions = session.get('refinement_instructions', '')

        # Generate summary
        summary_parts = [
            f"LLM-assisted refinement using {llm_service}",
            f"Content changes: +{added_lines} lines, -{removed_lines} lines"
        ]

        if refinement_instructions:
            # Truncate long instructions for summary
            instructions_preview = refinement_instructions[:100]
            if len(refinement_instructions) > 100:
                instructions_preview += "..."
            summary_parts.append(f"Instructions: {instructions_preview}")

        # Add metadata if available
        if hasattr(result_doc, 'metadata') and result_doc.metadata:
            metadata = result_doc.metadata
            if 'original_prompt_version' in metadata:
                summary_parts.append(f"Applied to version {metadata['original_prompt_version']}")

        return " | ".join(summary_parts)

    async def get_refinement_history(self, prompt_id: str) -> Dict[str, Any]:
        """Get refinement history for a prompt, including version relationships."""
        # Get all versions for this prompt
        versions = self.prompt_service._get_prompt_versions(prompt_id)

        # Get all refinement sessions that might be related to this prompt
        # This would ideally query the database for refinement sessions
        # For now, we'll build the history from version change summaries

        refinement_history = []
        for version in versions:
            if "LLM-assisted refinement" in version.change_summary:
                refinement_history.append({
                    "version": version.version,
                    "change_summary": version.change_summary,
                    "created_by": version.created_by,
                    "created_at": version.created_at.isoformat(),
                    "change_type": version.change_type
                })

        return {
            "prompt_id": prompt_id,
            "refinement_history": refinement_history,
            "total_refinements": len(refinement_history)
        }

    async def get_version_refinement_details(self, prompt_id: str, version: int) -> Dict[str, Any]:
        """Get detailed refinement information for a specific version."""
        # Get the version
        version_entity = self.prompt_service._get_version_repo().get_version_by_number(prompt_id, version)
        if not version_entity:
            raise ValueError(f"Version {version} not found for prompt {prompt_id}")

        # Check if this version was created by refinement
        is_refinement = "LLM-assisted refinement" in version_entity.change_summary

        details = {
            "version": version,
            "change_summary": version_entity.change_summary,
            "created_by": version_entity.created_by,
            "created_at": version_entity.created_at.isoformat(),
            "is_refinement": is_refinement
        }

        if is_refinement:
            # Try to extract refinement details from the summary
            details["refinement_info"] = self._parse_refinement_summary(version_entity.change_summary)

        return details

    def _parse_refinement_summary(self, summary: str) -> Dict[str, Any]:
        """Parse refinement details from version change summary."""
        parts = summary.split(" | ")
        info = {}

        for part in parts:
            if part.startswith("LLM-assisted refinement using "):
                info["llm_service"] = part.replace("LLM-assisted refinement using ", "")
            elif part.startswith("Content changes: "):
                changes = part.replace("Content changes: ", "")
                # Parse +X lines, -Y lines
                import re
                match = re.search(r'\+(\d+) lines, -(\d+) lines', changes)
                if match:
                    info["lines_added"] = int(match.group(1))
                    info["lines_removed"] = int(match.group(2))
            elif part.startswith("Instructions: "):
                info["refinement_instructions"] = part.replace("Instructions: ", "")
            elif part.startswith("Applied to version "):
                info["source_version"] = int(part.replace("Applied to version ", ""))

        return info
