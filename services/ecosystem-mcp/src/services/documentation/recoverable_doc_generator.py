"""
Recoverable Documentation Generator

Generates documentation with checkpoint support for graceful recovery.
Allows interrupted documentation generation to resume from last checkpoint.
"""

import logging
from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime
import asyncio

from ...utils.job_recovery import (
    JobRecoveryManager,
    RecoverableJob,
    JobType,
    get_recovery_manager
)
from ...storage import get_database

logger = logging.getLogger(__name__)


class RecoverableDocGenerator(RecoverableJob):
    """
    Generates documentation with checkpoint support.
    
    Features:
    - Checkpoint after each pass/question
    - Resume from last completed pass
    - Save intermediate results
    - Graceful interruption handling
    - Progress tracking
    """
    
    def __init__(self, job_id: Optional[str] = None):
        """
        Initialize recoverable doc generator.
        
        Args:
            job_id: Optional job ID (generates UUID if not provided)
        """
        if not job_id:
            job_id = str(uuid4())
        
        # Get recovery manager
        db = get_database()
        recovery_manager = get_recovery_manager(db)
        
        super().__init__(job_id, JobType.DOCUMENTATION, recovery_manager)
        
        logger.info(f"RecoverableDocGenerator initialized: job_id={job_id}")
    
    async def generate_multipass(
        self,
        config: Dict[str, Any],
        resume: bool = True
    ) -> Dict[str, Any]:
        """
        Generate documentation using multi-pass RAG with checkpoints.
        
        Args:
            config: Generation configuration
                {
                    "num_passes": int,
                    "questions_per_pass": int,
                    "output_dir": str,
                    "topic": str,
                    "llm_tier": str,
                    "max_retries": int
                }
            resume: Whether to attempt resume from last checkpoint
        
        Returns:
            Generation results
        """
        logger.info(
            f"🔄 Generating multi-pass documentation (job_id={self.job_id}, "
            f"passes={config['num_passes']}, resume={resume})"
        )
        
        result = {
            "success": False,
            "total_passes": config["num_passes"],
            "completed_passes": 0,
            "total_questions": 0,
            "answered_questions": 0,
            "failed_questions": 0,
            "documents_generated": [],
            "resumed_from_checkpoint": False,
            "checkpoints_created": 0,
            "error": None
        }
        
        try:
            # Load checkpoints from database
            await self.recovery_manager.load_checkpoints(self.job_id)
            
            # Check if we can resume
            start_pass = 0
            completed_docs = []
            
            if resume:
                can_resume = await self.can_resume()
                
                if can_resume:
                    resume_state = await self.get_resume_state()
                    last_checkpoint_data = resume_state["last_checkpoint"]["data"]
                    start_pass = last_checkpoint_data.get("current_pass", 0) + 1
                    completed_docs = last_checkpoint_data.get("documents", [])
                    
                    result["completed_passes"] = start_pass
                    result["answered_questions"] = last_checkpoint_data.get("answered", 0)
                    result["failed_questions"] = last_checkpoint_data.get("failed", 0)
                    result["documents_generated"] = completed_docs
                    result["resumed_from_checkpoint"] = True
                    
                    logger.info(
                        f"📂 Resuming from pass {start_pass + 1}/{config['num_passes']} "
                        f"({len(completed_docs)} documents already generated)"
                    )
            
            # Generate documentation for each pass
            for pass_num in range(start_pass, config["num_passes"]):
                pass_id = pass_num + 1
                
                logger.info(
                    f"📝 Starting pass {pass_id}/{config['num_passes']}: "
                    f"generating {config['questions_per_pass']} questions"
                )
                
                # Create checkpoint for this pass
                checkpoint_id = f"pass_{pass_id}"
                
                await self.create_checkpoint(
                    checkpoint_id=checkpoint_id,
                    data={
                        "current_pass": pass_num,
                        "pass_id": pass_id,
                        "total_passes": config["num_passes"],
                        "answered": result["answered_questions"],
                        "failed": result["failed_questions"],
                        "documents": result["documents_generated"]
                    }
                )
                
                try:
                    # Generate questions for this pass
                    questions = await self._generate_questions(
                        topic=config["topic"],
                        num_questions=config["questions_per_pass"],
                        pass_num=pass_id
                    )
                    
                    result["total_questions"] += len(questions)
                    
                    logger.info(f"❓ Generated {len(questions)} questions for pass {pass_id}")
                    
                    # Process each question
                    pass_docs = []
                    
                    for q_idx, question in enumerate(questions, 1):
                        try:
                            logger.info(
                                f"🤔 Answering question {q_idx}/{len(questions)}: {question[:50]}..."
                            )
                            
                            # Query RAG system
                            answer = await self._query_rag(
                                question=question,
                                tier=config.get("llm_tier", "auto"),
                                max_retries=config.get("max_retries", 3)
                            )
                            
                            # Save document
                            doc_path = await self._save_document(
                                content=answer,
                                question=question,
                                pass_num=pass_id,
                                question_num=q_idx,
                                output_dir=config["output_dir"]
                            )
                            
                            pass_docs.append({
                                "path": doc_path,
                                "question": question,
                                "pass": pass_id,
                                "question_num": q_idx
                            })
                            
                            result["answered_questions"] += 1
                            
                            logger.info(f"✅ Saved document: {doc_path}")
                        
                        except Exception as e:
                            result["failed_questions"] += 1
                            logger.error(f"❌ Failed question {q_idx}: {e}")
                    
                    # Add pass documents to result
                    result["documents_generated"].extend(pass_docs)
                    result["completed_passes"] += 1
                    
                    # Mark checkpoint as completed
                    await self.complete_checkpoint(data={
                        "answered": result["answered_questions"],
                        "failed": result["failed_questions"],
                        "documents": result["documents_generated"],
                        "pass_docs": pass_docs
                    })
                    
                    result["checkpoints_created"] += 1
                    
                    logger.info(
                        f"✅ Pass {pass_id} completed: "
                        f"{len(pass_docs)} documents generated"
                    )
                
                except Exception as e:
                    # Mark checkpoint as failed but continue
                    await self.fail_checkpoint(str(e))
                    logger.error(f"❌ Pass {pass_id} failed: {e}", exc_info=True)
                    # Continue to next pass instead of failing entire job
                    continue
            
            result["success"] = True
            
            # Cleanup old checkpoints
            await self.recovery_manager.cleanup_checkpoints(
                job_id=self.job_id,
                keep_last=5
            )
            
            logger.info(
                f"✅ Documentation generation complete: "
                f"{result['answered_questions']}/{result['total_questions']} questions answered, "
                f"{len(result['documents_generated'])} documents generated"
            )
        
        except Exception as e:
            logger.error(f"❌ Error generating documentation: {e}", exc_info=True)
            result["error"] = str(e)
            
            # Try to save failure checkpoint
            try:
                await self.fail_checkpoint(str(e))
            except:
                pass
        
        return result
    
    async def _generate_questions(
        self,
        topic: str,
        num_questions: int,
        pass_num: int
    ) -> List[str]:
        """
        Generate questions for a documentation pass.
        
        Args:
            topic: Documentation topic
            num_questions: Number of questions to generate
            pass_num: Current pass number
        
        Returns:
            List of questions
        """
        # Import here to avoid circular dependencies
        from ..query.multi_pass_rag import MultiPassRAG
        
        rag = MultiPassRAG()
        questions = await rag.generate_questions(
            topic=topic,
            num_questions=num_questions,
            pass_num=pass_num
        )
        
        return questions
    
    async def _query_rag(
        self,
        question: str,
        tier: str = "auto",
        max_retries: int = 3,
        timeout_seconds: float = 120.0  # PHASE 10 (Day 2 - Task 2.2): LLM timeout
    ) -> str:
        """
        Query RAG system with retry logic and timeout protection.
        
        PHASE 10 (Day 2 - Task 2.2): Enhanced with timeout protection for LLM calls.
        
        Args:
            question: Question to ask
            tier: LLM tier (desktop, docker, auto)
            max_retries: Maximum retry attempts
            timeout_seconds: Timeout for query (default 120s for LLM calls)
        
        Returns:
            Answer text
        
        Raises:
            asyncio.TimeoutError: If query exceeds timeout
        """
        from ..query.enhanced_query import EnhancedQueryService
        
        query_service = EnhancedQueryService()
        
        for attempt in range(max_retries):
            try:
                # PHASE 10: Apply timeout to LLM query
                result = await asyncio.wait_for(
                    query_service.query(
                        query=question,
                        tier=tier,
                        max_results=5
                    ),
                    timeout=timeout_seconds
                )
                
                return result.get("answer", "")
            
            except asyncio.TimeoutError:
                logger.error(
                    f"⏱️  Query timeout ({timeout_seconds}s) on attempt {attempt + 1}: {question[:50]}..."
                )
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"   Retrying in {wait_time}s with longer timeout...")
                    await asyncio.sleep(wait_time)
                    # Increase timeout for retry
                    timeout_seconds *= 1.5
                else:
                    raise
            
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        f"Query attempt {attempt + 1} failed, "
                        f"retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise
    
    async def _save_document(
        self,
        content: str,
        question: str,
        pass_num: int,
        question_num: int,
        output_dir: str
    ) -> str:
        """
        Save generated document to file.
        
        Args:
            content: Document content
            question: Original question
            pass_num: Pass number
            question_num: Question number
            output_dir: Output directory
        
        Returns:
            Saved file path
        """
        import os
        from pathlib import Path
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        safe_question = "".join(c for c in question[:50] if c.isalnum() or c in (' ', '-', '_'))
        safe_question = safe_question.replace(' ', '_')
        filename = f"pass_{pass_num:02d}_q{question_num:02d}_{safe_question}.md"
        
        file_path = output_path / filename
        
        # Write document with metadata
        doc_content = f"""# {question}

**Generated:** {datetime.utcnow().isoformat()}  
**Pass:** {pass_num}  
**Question:** {question_num}

---

{content}
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(doc_content)
        
        return str(file_path)
    
    async def get_progress(self) -> Dict[str, Any]:
        """
        Get current progress for this job.
        
        Returns:
            Progress information
        """
        resume_state = await self.get_resume_state()
        
        if not resume_state.get("can_resume"):
            return {
                "in_progress": False,
                "can_resume": False
            }
        
        last_checkpoint = resume_state["last_checkpoint"]["data"]
        
        return {
            "in_progress": True,
            "can_resume": True,
            "completed_passes": last_checkpoint.get("pass_id", 0),
            "total_passes": last_checkpoint.get("total_passes", 0),
            "answered_questions": last_checkpoint.get("answered", 0),
            "failed_questions": last_checkpoint.get("failed", 0),
            "documents_generated": len(last_checkpoint.get("documents", [])),
            "progress_pct": round(
                (last_checkpoint.get("pass_id", 0) / last_checkpoint.get("total_passes", 1)) * 100,
                1
            )
        }


# Helper function to create or resume doc generation job
async def generate_documentation_with_recovery(
    config: Dict[str, Any],
    job_id: Optional[str] = None,
    resume: bool = True
) -> Dict[str, Any]:
    """
    Generate documentation with automatic checkpoint recovery.
    
    Args:
        config: Generation configuration
        job_id: Optional job ID for resuming
        resume: Whether to attempt resume
    
    Returns:
        Generation results
    """
    generator = RecoverableDocGenerator(job_id=job_id)
    return await generator.generate_multipass(config=config, resume=resume)

