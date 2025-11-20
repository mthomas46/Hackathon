"""
Adaptive Documentation Orchestrator

Orchestrates adaptive documentation generation by integrating all Phase 1-3 components:
- Template Management (Phase 2)
- Discovery Service (Phase 3)
- Prompt Tracking (Phase 3)
- Citation Management (Phase 3)
- Transparency Logging (Phase 3)

Supports multi-pass generation with learning and continuous improvement.
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import select, func

from ...services.templates.template_manager import get_template_manager
from ...services.templates.template_validator import get_template_validator
from ...services.templates.retry_handler import get_retry_handler, get_degradation_handler
from ...services.adaptive.discovery_service import get_discovery_service
from ...services.adaptive.prompt_tracker import get_prompt_tracker
from ...services.adaptive.citation_manager import get_citation_manager
from ...services.adaptive.transparency_logger import get_transparency_logger
from ...services.rag.enhanced_rag_service import get_enhanced_rag_service
from ...storage.database import get_database
from ...storage.models_documentation import DocumentationRunModel

logger = logging.getLogger(__name__)


class AdaptiveDocumentationOrchestrator:
    """
    Orchestrates adaptive, multi-pass documentation generation.
    
    Integrates all adaptive features:
    - Repository discovery for context
    - Template-based structure
    - Prompt tracking for improvement
    - Source citations for transparency
    - Complete audit logging
    - Multi-pass refinement
    """
    
    def __init__(self):
        """Initialize adaptive orchestrator."""
        self.template_manager = get_template_manager()
        self.template_validator = get_template_validator()
        self.retry_handler = get_retry_handler()
        self.degradation_handler = get_degradation_handler()
        self.discovery_service = get_discovery_service()
        self.prompt_tracker = get_prompt_tracker()
        self.citation_manager = get_citation_manager()
        self.transparency_logger = get_transparency_logger()
        self.rag_service = get_enhanced_rag_service()
        
        logger.info("AdaptiveDocumentationOrchestrator initialized")
    
    async def generate_adaptive_documentation(
        self,
        service_name: str,
        template_name: str,
        category: str,
        config: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate adaptive documentation using template and context discovery.
        
        Args:
            service_name: Service to document
            template_name: Template to use
            category: Template category
            config: Optional configuration
                - include_citations: bool (default True)
                - citation_style: str (default "endnotes")
                - transparency_mode: str (default "verbose")
                - enable_multi_pass: bool (default False)
                - max_passes: int (default 2)
            run_id: Optional existing run ID (if None, creates new one)
        
        Returns:
            Generated documentation with metadata
        """
        config = config or {}
        
        # Use provided run_id or create new one
        if run_id:
            run_id = UUID(run_id) if isinstance(run_id, str) else run_id
            logger.info(f"📝 Using existing run_id: {run_id}")
            create_new_run = False
        else:
            run_id = uuid4()
            logger.info(f"🆕 Created new run_id: {run_id}")
            create_new_run = True
        
        # Normalize service_name to match database (case-insensitive lookup)
        service_name = await self._normalize_service_name(service_name)
        
        logger.info(
            f"🚀 Starting adaptive documentation generation\n"
            f"   Service: {service_name}\n"
            f"   Template: {template_name}\n"
            f"   Run ID: {run_id}\n"
            f"   Mode: {'Using existing run' if not create_new_run else 'Creating new run'}"
        )
        
        # Create documentation run record in database (only if new)
        if create_new_run:
            async with get_database().session() as session:
                # Query for repo_id from repository_contexts (foreign key constraint)
                from ...storage.models_analysis import RepositoryContextModel
                
                query = select(RepositoryContextModel.repo_id).filter(
                    RepositoryContextModel.repo_name == service_name
                )
                result = await session.execute(query)
                repo_id = result.scalar_one_or_none()
                
                run = DocumentationRunModel(
                    id=run_id,
                    plan_id=f"adaptive_{service_name}_{template_name}",
                    repo_id=repo_id,  # Use actual repo_id or NULL if not found
                    status="running",
                    passes_completed=0,
                    total_passes=config.get("max_passes", 1),
                    current_pass="discovery",
                    config=config,
                    started_at=datetime.utcnow()
                )
                session.add(run)
                await session.commit()
                logger.info(f"✅ Created documentation run record: {run_id} (repo_id: {repo_id})")
        else:
            logger.info(f"✅ Using existing documentation run record: {run_id}")
        
        try:
            # Phase 1: Discovery
            logger.info(f"🔍 Phase 1: Starting discovery for {service_name}...")
            await self.transparency_logger.log_action(
                run_id=run_id,
                phase="discovery",
                action_type="start",
                action_description=f"Starting discovery for {service_name}"
            )
            
            context = await self._discovery_phase(run_id, service_name)
            logger.info(f"✅ Discovery complete: {len(context.get('frameworks', []))} frameworks, {len(context.get('concepts', []))} concepts")
            
            # Phase 2: Template Selection & Loading
            logger.info(f"📋 Phase 2: Loading template '{template_name}' (category: {category})...")
            await self.transparency_logger.log_action(
                run_id=run_id,
                phase="template_selection",
                action_type="load",
                action_description=f"Loading template: {template_name}"
            )
            
            template = await self.template_manager.load_template(template_name, category)
            logger.info(f"✅ Template loaded: {len(template.get('sections', []))} sections to generate")
            
            # Phase 3: Section Generation
            logger.info(f"✨ Phase 3: Generating sections...")
            sections = await self._generation_phase(
                run_id=run_id,
                template=template,
                context=context,
                service_name=service_name,
                config=config
            )
            logger.info(f"✅ Generated {len(sections)} sections")
            
            # Phase 4: Assembly & Formatting
            logger.info(f"📦 Phase 4: Assembling final documentation...")
            documentation = await self._assembly_phase(
                run_id=run_id,
                template=template,
                sections=sections,
                context=context,
                config=config
            )
            logger.info(f"✅ Assembly complete: {len(documentation.get('content', ''))} characters")
            
            # Phase 5: Save artifacts to database using repository
            logger.info(f"💾 Phase 5: Saving artifacts to database...")
            try:
                from ...storage.repositories.documentation_run_repository import DocumentationRunRepository
                
                # Use the repository to properly save artifacts
                # This automatically updates run totals (total_artifacts, total_words)
                async with get_database().session() as session:
                    repository = DocumentationRunRepository(session)
                    word_count = len(documentation["content"].split())
                    
                    artifact = await repository.add_artifact(
                        run_id=run_id,
                        artifact_type="synthesis",
                        pass_number=1,
                        pass_type="adaptive",
                        title=f"{service_name} - {template_name}",
                        content=documentation["content"],
                        component_name=service_name,
                        format="markdown",
                        word_count=word_count,
                        quality_score=1.0  # Could calculate based on sections/citations
                    )
                    
                    logger.info(f"🔄 About to commit transaction...")
                    await session.commit()
                    logger.info(f"✅ Transaction committed successfully")
                    logger.info(f"✅ Saved artifact: {artifact.title} (ID: {artifact.id})")
                    logger.info(f"✅ Run totals automatically updated: 1 artifact, {word_count} words")
                
            except Exception as e:
                logger.error(f"⚠️ Failed to save artifacts: {e}", exc_info=True)
                # Don't fail the whole generation if artifact save fails
            
            logger.info(
                f"✅ Adaptive documentation generated successfully\n"
                f"   Sections: {len(sections)}\n"
                f"   Total length: {len(documentation['content'])} chars\n"
                f"   Artifacts saved: 1"
            )
            
            return {
                "run_id": str(run_id),
                "service_name": service_name,
                "template_name": template_name,
                "content": documentation["content"],
                "metadata": {
                    "sections_generated": len(sections),
                    "concepts_discovered": len(context.get("concepts", [])),
                    "frameworks_detected": context.get("frameworks", []),
                    "citations_added": documentation.get("citation_count", 0),
                    "transparency_log_available": True
                },
                "transparency_report_url": f"/api/v1/transparency/{run_id}",
                "citations": documentation.get("citations", [])
            }
            
        except Exception as e:
            logger.error(f"❌ Adaptive documentation generation failed: {e}", exc_info=True)
            
            await self.transparency_logger.log_action(
                run_id=run_id,
                phase="error",
                action_type="failure",
                action_description="Documentation generation failed",
                status="failed",
                error_message=str(e)
            )
            
            raise
    
    async def _discovery_phase(
        self,
        run_id: UUID,
        service_name: str
    ) -> Dict[str, Any]:
        """
        Phase 1: Discover repository context.
        
        Uses existing repository_contexts to extract knowledge.
        """
        log_id = await self.transparency_logger.start_action(
            run_id=run_id,
            phase="discovery",
            action_type="query",
            action_description="Discovering repository context"
        )
        
        try:
            # Discover from existing infrastructure
            context = await self.discovery_service.discover_repository_context(service_name)
            
            # Get framework-specific guidance
            guidance = await self.discovery_service.get_framework_specific_guidance(service_name)
            context["framework_guidance"] = guidance
            
            await self.transparency_logger.complete_action(
                log_id=log_id,
                output_data={
                    "frameworks": context.get("frameworks", []),
                    "languages": list(context.get("languages", {}).keys()),
                    "concepts_count": len(context.get("concepts", [])),
                    "architecture": context.get("architecture_type")
                }
            )
            
            logger.info(
                f"📊 Discovery complete:\n"
                f"   Frameworks: {context.get('frameworks', [])}\n"
                f"   Concepts: {len(context.get('concepts', []))}\n"
                f"   Keywords: {len(context.get('keywords', []))}"
            )
            
            return context
            
        except Exception as e:
            import traceback
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
                "phase": "discovery"
            }
            
            await self.transparency_logger.complete_action(
                log_id=log_id,
                status="failed",
                error_message=f"{type(e).__name__}: {str(e)}",
                output_data=error_details
            )
            raise
    
    async def _generation_phase(
        self,
        run_id: UUID,
        template: Dict[str, Any],
        context: Dict[str, Any],
        service_name: str,
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Phase 3: Generate sections using template and context.
        
        For each section in template:
        1. Build context-aware prompt
        2. Execute RAG query
        3. Track prompt execution
        4. Validate against template
        5. Extract citations
        """
        sections = []
        failed_sections = []
        
        template_sections = template["structure"]["sections"]
        logger.info(f"📝 Generating {len(template_sections)} sections...")
        
        for section in template_sections:
            # ✅ DEFENSIVE: Use .get() with default value to handle missing "required" field
            is_required = section.get("required", True)  # Default to True if not specified
            
            if not is_required and not config.get("include_optional_sections", False):
                logger.debug(f"⏭️  Skipping optional section: {section.get('name', 'unnamed')}")
                continue
            
            log_id = await self.transparency_logger.start_action(
                run_id=run_id,
                phase="generation",
                action_type="generate_section",
                action_description=f"Generating section: {section.get('name', 'unnamed')}",
                input_data={
                    "section": section.get("name", "unnamed"),
                    "required": is_required
                }
            )
            
            # Wrap section generation in retry handler
            async def generate_section():
                # Build context-aware prompt
                prompt = await self._build_prompt(section, context, service_name)
                
                # Execute RAG query (using 'ask' method with service_name for cache invalidation)
                response = await self.rag_service.ask(
                    question=prompt,
                    n_results=section.get("documents_needed", 20),
                    prefer_recent=True,
                    service_name=service_name  # Enable intelligent cache invalidation
                )
                
                # If no sources were retrieved, force an insufficient info response
                if not response.get("sources") or len(response.get("sources", [])) == 0:
                    logger.warning(f"No sources retrieved for section '{section['name']}', forcing insufficient info response")
                    response["answer"] = "I don't have enough information to answer that question."
                
                # Track prompt execution
                execution_id = await self.prompt_tracker.track_prompt_execution(
                    run_id=run_id,
                    prompt_template=f"{template['name']}:{section['name']}",
                    prompt_used=prompt,
                    context_provided=context,
                    response=response["answer"],
                    sources_used=response.get("sources", []),
                    section_name=section["name"]
                )
                
                # Enhanced validation with template validator (not async)
                validation = self.template_validator.validate_adherence(
                    template=template,
                    section_name=section["name"],
                    content=response["answer"]
                )
                
                # Check if response indicates lack of information
                has_insufficient_info = any(phrase in response["answer"].lower() for phrase in [
                    "don't have enough information",
                    "insufficient information",
                    "not enough information",
                    "no information available",
                    "cannot find"
                ])
                
                logger.info(f"Section '{section['name']}': has_insufficient_info={has_insufficient_info}, sources={len(response.get('sources', []))}")
                
                # Build section content with query/response transparency
                section_content_parts = []
                
                # Add query/response metadata (with special formatting if insufficient info)
                if has_insufficient_info:
                    logger.info(f"Adding disclosure section for '{section['name']}'  (insufficient info detected)")
                    section_content_parts.append("---")
                    section_content_parts.append("⚠️ **Note: Limited Information Available**")
                    section_content_parts.append("")
                    section_content_parts.append("<details>")
                    section_content_parts.append(f"<summary>🔍 Query & Response for Section: {section['name']}</summary>")
                    section_content_parts.append("")
                    section_content_parts.append("**Query Sent to AI:**")
                    section_content_parts.append("```")
                    section_content_parts.append(prompt)
                    section_content_parts.append("```")
                    section_content_parts.append("")
                    section_content_parts.append("**AI Response:**")
                    section_content_parts.append("```")
                    section_content_parts.append(response["answer"])
                    section_content_parts.append("```")
                    section_content_parts.append("")
                    section_content_parts.append(f"**Sources Used:** {len(response.get('sources', []))} documents")
                    section_content_parts.append("")
                    section_content_parts.append("</details>")
                    section_content_parts.append("")
                    section_content_parts.append("---")
                    section_content_parts.append("")
                elif config.get("transparency_mode") == "verbose":
                    section_content_parts.append("")
                    section_content_parts.append("<details>")
                    section_content_parts.append(f"<summary>🔍 Query & Response for Section: {section['name']}</summary>")
                    section_content_parts.append("")
                    section_content_parts.append("**Query Sent to AI:**")
                    section_content_parts.append("```")
                    section_content_parts.append(prompt)
                    section_content_parts.append("```")
                    section_content_parts.append("")
                    section_content_parts.append("**Synthesized Response:**")
                    section_content_parts.append("```")
                    section_content_parts.append(response["answer"])
                    section_content_parts.append("```")
                    section_content_parts.append("")
                    section_content_parts.append(f"**Sources Used:** {len(response.get('sources', []))} documents")
                    if response.get("confidence"):
                        section_content_parts.append(f"**Confidence Score:** {response['confidence']:.2f}")
                    section_content_parts.append("")
                    section_content_parts.append("</details>")
                    section_content_parts.append("")
                
                # Add the generated content
                section_content_parts.append(response["answer"])
                
                # Combine all parts
                section_content_with_prompt = "\n".join(section_content_parts)
                
                logger.info(f"Section '{section['name']}' content length: {len(section_content_with_prompt)}, has <details>: {'<details>' in section_content_with_prompt}")
                
                # Render section with template formatting
                rendered_content = await self.template_manager.render_section(
                    template=template,
                    section_name=section["name"],
                    content=section_content_with_prompt,
                    context={
                        "transparency_mode": config.get("transparency_mode", "normal"),
                        "has_insufficient_info": has_insufficient_info
                    }
                )
                
                return {
                    "name": section["name"],
                    "content": rendered_content,
                    "validation": validation,
                    "sources": response.get("sources", []),
                    "prompt_execution_id": str(execution_id),
                    "prompt_used": prompt,
                    "has_insufficient_info": has_insufficient_info
                }
            
            # Execute with retry
            result = await self.retry_handler.execute_with_retry(
                operation=generate_section,
                operation_name=f"Generate section: {section['name']}",
                context={"section": section["name"], "template": template["name"]}
            )
            
            if result["success"]:
                section_data = result["data"]
                sections.append(section_data)
                
                validation = section_data.get("validation", {})
                await self.transparency_logger.complete_action(
                    log_id=log_id,
                    output_data={
                        "content_length": len(section_data["content"]),
                        "validation_valid": validation.get("valid", True),
                        "adherence_score": validation.get("adherence_score", 1.0),
                        "sources_count": len(section_data.get("sources", [])),
                        "attempts": result.get("attempts", 1)
                    }
                )
                
                logger.info(
                    f"✅ Section '{section['name']}' generated "
                    f"(adherence: {validation.get('adherence_score', 1.0):.2f}, "
                    f"attempts: {result.get('attempts', 1)})"
                )
            else:
                # Section failed after retries
                failed_sections.append(section["name"])
                
                import traceback
                error_details = {
                    "error_type": result.get("error_type", "Unknown"),
                    "error_message": result.get("error", "Unknown error"),
                    "attempts": result.get("attempts", 0),
                    "circuit_state": result.get("circuit_state", "unknown")
                }
                
                logger.error(
                    f"❌ Failed to generate section '{section['name']}' after "
                    f"{result.get('attempts', 0)} attempts: {result.get('error')}"
                )
                
                await self.transparency_logger.complete_action(
                    log_id=log_id,
                    status="failed",
                    error_message=result.get("error", "Unknown error"),
                    output_data=error_details
                )
                
                # Add fallback content for failed section
                if config.get("enable_graceful_degradation", True):
                    fallback_content = self.degradation_handler.generate_fallback_content(
                        section_name=section["name"],
                        error=result.get("error", "Unknown error"),
                        template_def=section
                    )
                    
                    sections.append({
                        "name": section["name"],
                        "content": fallback_content,
                        "validation": {"valid": False, "adherence_score": 0.0},
                        "sources": [],
                        "is_fallback": True
                    })
                    
                    logger.info(f"📝 Added fallback content for '{section['name']}'")
        
        # Check if we should accept partial documentation
        if failed_sections:
            should_accept = self.degradation_handler.should_degrade(
                failed_sections=failed_sections,
                total_sections=len(template_sections),
                threshold=config.get("min_success_rate", 0.5)
            )
            
            if not should_accept:
                raise ValueError(
                    f"Documentation generation failed: {len(failed_sections)}/{len(template_sections)} "
                    f"sections failed (below threshold)"
                )
        
        return sections
    
    async def _assembly_phase(
        self,
        run_id: UUID,
        template: Dict[str, Any],
        sections: List[Dict[str, Any]],
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Phase 4: Assemble sections and add citations.
        
        Combines all sections, adds citations if enabled, and formats final document.
        """
        log_id = await self.transparency_logger.start_action(
            run_id=run_id,
            phase="assembly",
            action_type="assemble",
            action_description="Assembling final documentation"
        )
        
        try:
            # Combine sections
            content_parts = []
            
            # Add title
            service_name = context.get("service_name", "Service")
            template_category = template.get("category", "documentation")
            
            content_parts.append(f"# {service_name} - {template_category.replace('_', ' ').title()}\n\n")
            
            # Add metadata header
            content_parts.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")
            content_parts.append(f"**Template:** {template['name']}\n")
            
            if context.get("frameworks"):
                content_parts.append(f"**Frameworks:** {', '.join(context['frameworks'])}\n")
            
            content_parts.append("\n---\n\n")
            
            # Add table of contents if configured
            if template.get("render_options", {}).get("include_toc", False):
                content_parts.append("## Table of Contents\n\n")
                for idx, section in enumerate(sections, 1):
                    content_parts.append(f"{idx}. [{section['name']}](#{section['name'].lower().replace(' ', '-')})\n")
                content_parts.append("\n---\n\n")
            
            # Add sections
            all_citations = []
            for section in sections:
                content_parts.append(section["content"])
                content_parts.append("\n\n")
                
                # Collect citations with metadata for better formatting
                if section.get("sources"):
                    all_citations.extend([
                        {
                            "section_name": section["name"],
                            "document_id": src.get("document_id", src.get("id")),
                            "relevance_score": src.get("relevance_score", src.get("score", 0.0)),
                            "content": src.get("content", src.get("text", "")),
                            "metadata": src.get("metadata", {})  # Include metadata (filename, file_path, etc.)
                        }
                        for src in section["sources"]
                    ])
            
            # Add citations section if enabled
            citation_count = 0
            if config.get("include_citations", True) and all_citations:
                citation_style = config.get("citation_style", "endnotes")
                
                # Format citations
                citations_section = self._format_citations(
                    all_citations,
                    style=citation_style
                )
                
                content_parts.append(citations_section)
                citation_count = len(all_citations)
            
            # Add generation metadata footer
            content_parts.append("\n\n---\n\n")
            content_parts.append("*Generated by Ecosystem MCP - Adaptive Documentation System*\n")
            content_parts.append(f"*Run ID: `{run_id}`*\n")
            
            final_content = "".join(content_parts)
            
            await self.transparency_logger.complete_action(
                log_id=log_id,
                output_data={
                    "total_length": len(final_content),
                    "sections_count": len(sections),
                    "citations_count": citation_count
                }
            )
            
            return {
                "content": final_content,
                "citation_count": citation_count,
                "citations": all_citations
            }
            
        except Exception as e:
            import traceback
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
                "phase": "assembly",
                "sections_count": len(sections)
            }
            
            await self.transparency_logger.complete_action(
                log_id=log_id,
                status="failed",
                error_message=f"{type(e).__name__}: {str(e)}",
                output_data=error_details
            )
            raise
    
    async def _build_prompt(
        self,
        section: Dict[str, Any],
        context: Dict[str, Any],
        service_name: str
    ) -> str:
        """
        Build context-aware prompt for section.
        
        Enhances template prompt with discovered context.
        """
        base_prompt = section.get("prompt_template", "")
        
        # Prepare context with service_name (avoid duplicate key error)
        prompt_context = {**context, "service_name": service_name}
        
        # Fill in basic context
        try:
            filled_prompt = base_prompt.format(**prompt_context)
        except KeyError as e:
            # Template has placeholder that context doesn't provide - use safe substitute
            logger.warning(f"Template placeholder {e} not found in context, using empty string")
            from string import Template
            filled_prompt = Template(base_prompt).safe_substitute(**prompt_context)
        
        # Add framework-specific context if available
        guidance = context.get("framework_guidance", {})
        if guidance and guidance != {"guidance": "generic"}:
            filled_prompt += "\n\n**Framework-Specific Context:**\n"
            filled_prompt += f"- Detected framework: {context.get('primary_framework', 'Unknown')}\n"
            
            if "patterns_to_find" in guidance:
                filled_prompt += f"- Look for patterns: {', '.join(guidance['patterns_to_find'][:3])}\n"
        
        # Add discovered concepts
        if context.get("concepts"):
            filled_prompt += f"\n\n**Key Concepts:** {', '.join(context['concepts'][:10])}\n"
        
        return filled_prompt
    
    def _format_citations(
        self,
        citations: List[Dict[str, Any]],
        style: str = "endnotes"
    ) -> str:
        """Format citations section."""
        if style == "endnotes":
            lines = [
                "---",
                "",
                "## Sources & References",
                "",
                "This documentation was generated from the following source documents:",
                ""
            ]
            
            # Group by section
            sections = {}
            for citation in citations:
                section = citation["section_name"]
                if section not in sections:
                    sections[section] = []
                sections[section].append(citation)
            
            for section_name, section_citations in sections.items():
                lines.append(f"### {section_name}")
                lines.append("")
                
                for idx, citation in enumerate(section_citations[:10], 1):  # Limit to 10 per section
                    relevance = citation["relevance_score"]
                    relevance_pct = int(relevance * 100)
                    
                    # Get document metadata
                    doc_id = str(citation.get("document_id", "unknown"))[:8]
                    metadata = citation.get("metadata", {})
                    
                    # Extract document name from metadata (try multiple fields)
                    file_path = metadata.get("file_path", metadata.get("filename", metadata.get("source", "")))
                    
                    if file_path and file_path != "Unknown":
                        # Extract filename from path
                        import os
                        filename = os.path.basename(file_path)
                        
                        # Format: filename (relevance) [ID] + file path
                        line = f"{idx}. **{filename}** (relevance: {relevance_pct}%) [`{doc_id}`]"
                        line += f"\n   📄 `{file_path}`"
                    else:
                        # Fallback format
                        line = f"{idx}. Document `{doc_id}...` (relevance: {relevance_pct}%)"
                    
                    # Add excerpt
                    content = citation.get("content", "")
                    if content:
                        excerpt = content[:150].replace("\n", " ")
                        line += f"\n   > {excerpt}..."
                    
                    lines.append(line)
                
                lines.append("")
            
            return "\n".join(lines)
        
        return ""
    
    async def _normalize_service_name(self, service_name: str) -> str:
        """
        Normalize service_name to match actual casing in database.
        
        Args:
            service_name: Service name (any case)
        
        Returns:
            Service name with correct casing from database
        """
        from sqlalchemy import select, func
        from ...storage.db_models import DocumentModel
        
        async with get_database().session() as session:
            # Find actual service name in database (case-insensitive)
            query = select(DocumentModel.service_name).filter(
                func.lower(DocumentModel.service_name) == service_name.lower(),
                DocumentModel.is_latest == True
            ).limit(1)
            
            result = await session.execute(query)
            actual_service_name = result.scalar_one_or_none()
            
            if actual_service_name:
                logger.info(f"📝 Normalized service_name: '{service_name}' → '{actual_service_name}'")
                return actual_service_name
            else:
                logger.warning(f"⚠️ Service '{service_name}' not found in database, using as-is")
                return service_name


# Singleton instance
_adaptive_orchestrator: Optional[AdaptiveDocumentationOrchestrator] = None


def get_adaptive_orchestrator() -> AdaptiveDocumentationOrchestrator:
    """Get or create singleton adaptive orchestrator."""
    global _adaptive_orchestrator
    if _adaptive_orchestrator is None:
        _adaptive_orchestrator = AdaptiveDocumentationOrchestrator()
    return _adaptive_orchestrator

