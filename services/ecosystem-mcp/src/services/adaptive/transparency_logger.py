"""
Transparency Logger

Logs all actions during documentation generation for complete audit trail
and debugging. Stores data in EXISTING generation_transparency_log table.
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...storage.database import get_database
from ...storage.models_templates import GenerationTransparencyLogModel

logger = logging.getLogger(__name__)


class TransparencyLogger:
    """
    Logs all documentation generation actions for transparency.
    
    Provides complete audit trail by logging every action during
    generation. Stores data in EXISTING generation_transparency_log
    table created in Phase 1.
    """
    
    def __init__(self):
        """Initialize transparency logger."""
        self.sequence_counters: Dict[UUID, int] = {}
        logger.info("TransparencyLogger initialized")
    
    async def log_action(
        self,
        run_id: UUID,
        phase: str,
        action_type: str,
        action_description: str,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> UUID:
        """
        Log a single action during documentation generation.
        
        Args:
            run_id: Documentation run ID
            phase: Generation phase (discovery, template_selection, generation, etc.)
            action_type: Type of action (query, extract, validate, etc.)
            action_description: Human-readable description
            input_data: Input data for this action
            output_data: Output data from this action
            status: Action status (success, failed, skipped)
            error_message: Error message if failed
        
        Returns:
            Log entry ID
        """
        # Get next sequence number for this run
        if run_id not in self.sequence_counters:
            self.sequence_counters[run_id] = 1
        else:
            self.sequence_counters[run_id] += 1
        
        sequence_number = self.sequence_counters[run_id]
        
        async with get_database().session() as session:
            log_entry = GenerationTransparencyLogModel(
                run_id=run_id,
                phase=phase,
                sequence_number=sequence_number,
                action_type=action_type,
                action_description=action_description,
                input_data=input_data,
                output_data=output_data,
                status=status,
                error_message=error_message
            )
            
            session.add(log_entry)
            await session.commit()
            await session.refresh(log_entry)
            
            logger.debug(
                f"📝 Logged action: [{phase}] {action_type} - {action_description} "
                f"(seq: {sequence_number}, status: {status})"
            )
            
            return log_entry.id
    
    async def start_action(
        self,
        run_id: UUID,
        phase: str,
        action_type: str,
        action_description: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Start logging a long-running action.
        
        Args:
            run_id: Documentation run ID
            phase: Generation phase
            action_type: Type of action
            action_description: Description
            input_data: Input data
        
        Returns:
            Log entry ID (use this to complete the action later)
        """
        log_id = await self.log_action(
            run_id=run_id,
            phase=phase,
            action_type=action_type,
            action_description=action_description,
            input_data=input_data,
            status="success"  # Will update if it fails
        )
        
        return log_id
    
    async def complete_action(
        self,
        log_id: UUID,
        output_data: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> None:
        """
        Complete a long-running action by updating the log entry.
        
        Args:
            log_id: Log entry ID from start_action
            output_data: Output data
            status: Final status
            error_message: Error message if failed
        """
        async with get_database().session() as session:
            log_entry = await session.get(GenerationTransparencyLogModel, log_id)
            
            if log_entry:
                log_entry.completed_at = datetime.now(timezone.utc)
                log_entry.duration_ms = int(
                    (log_entry.completed_at - log_entry.started_at).total_seconds() * 1000
                )
                log_entry.output_data = output_data
                log_entry.status = status
                log_entry.error_message = error_message
                
                await session.commit()
                
                logger.debug(
                    f"✅ Completed action: {log_entry.action_type} "
                    f"(duration: {log_entry.duration_ms}ms, status: {status})"
                )
    
    async def get_run_log(
        self,
        run_id: UUID,
        phase: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get complete log for a documentation run.
        
        Args:
            run_id: Documentation run ID
            phase: Optional filter by phase
        
        Returns:
            List of log entries in chronological order
        """
        async with get_database().session() as session:
            query = select(GenerationTransparencyLogModel).filter(
                GenerationTransparencyLogModel.run_id == run_id
            )
            
            if phase:
                query = query.filter(GenerationTransparencyLogModel.phase == phase)
            
            query = query.order_by(GenerationTransparencyLogModel.sequence_number)
            
            result = await session.execute(query)
            entries = result.scalars().all()
            
            return [
                {
                    "id": str(e.id),
                    "phase": e.phase,
                    "sequence": e.sequence_number,
                    "action_type": e.action_type,
                    "description": e.action_description,
                    "input_data": e.input_data,
                    "output_data": e.output_data,
                    "started_at": e.started_at.isoformat() if e.started_at else None,
                    "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                    "duration_ms": e.duration_ms,
                    "status": e.status,
                    "error": e.error_message
                }
                for e in entries
            ]
    
    async def format_transparency_report(
        self,
        run_id: UUID
    ) -> str:
        """
        Format transparency log as a human-readable report.
        
        Args:
            run_id: Documentation run ID
        
        Returns:
            Formatted markdown report
        """
        entries = await self.get_run_log(run_id)
        
        if not entries:
            return "No log entries found for this run."
        
        lines = [
            "# Documentation Generation Transparency Report",
            "",
            f"**Run ID:** `{run_id}`",
            f"**Total Actions:** {len(entries)}",
            f"**Status:** {'✅ Success' if all(e['status'] == 'success' for e in entries) else '❌ Some failures'}",
            "",
            "---",
            ""
        ]
        
        # Group by phase
        phases = {}
        for entry in entries:
            phase = entry["phase"]
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(entry)
        
        for phase_name, phase_entries in phases.items():
            lines.append(f"## Phase: {phase_name}")
            lines.append("")
            lines.append(f"**Actions in this phase:** {len(phase_entries)}")
            lines.append("")
            
            for entry in phase_entries:
                status_icon = "✅" if entry["status"] == "success" else "❌"
                duration = f" ({entry['duration_ms']}ms)" if entry["duration_ms"] else ""
                
                lines.append(
                    f"{entry['sequence']}. {status_icon} **{entry['action_type']}**{duration}"
                )
                lines.append(f"   - {entry['description']}")
                
                if entry["error"]:
                    lines.append(f"   - ❌ Error: {entry['error']}")
                
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    async def get_phase_statistics(
        self,
        run_id: UUID
    ) -> Dict[str, Any]:
        """
        Get statistics about each phase of generation.
        
        Args:
            run_id: Documentation run ID
        
        Returns:
            Phase-level statistics
        """
        entries = await self.get_run_log(run_id)
        
        phases = {}
        for entry in entries:
            phase = entry["phase"]
            if phase not in phases:
                phases[phase] = {
                    "total_actions": 0,
                    "successful_actions": 0,
                    "failed_actions": 0,
                    "total_duration_ms": 0,
                    "action_types": set()
                }
            
            phases[phase]["total_actions"] += 1
            if entry["status"] == "success":
                phases[phase]["successful_actions"] += 1
            else:
                phases[phase]["failed_actions"] += 1
            
            if entry["duration_ms"]:
                phases[phase]["total_duration_ms"] += entry["duration_ms"]
            
            phases[phase]["action_types"].add(entry["action_type"])
        
        # Convert sets to lists for JSON serialization
        for phase_stats in phases.values():
            phase_stats["action_types"] = list(phase_stats["action_types"])
        
        return phases
    
    async def get_failed_actions(
        self,
        run_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get all failed actions for a run.
        
        Args:
            run_id: Documentation run ID
        
        Returns:
            List of failed actions with details
        """
        entries = await self.get_run_log(run_id)
        
        return [
            entry for entry in entries
            if entry["status"] == "failed"
        ]
    
    async def reset_sequence_counter(self, run_id: UUID) -> None:
        """Reset sequence counter for a run."""
        if run_id in self.sequence_counters:
            del self.sequence_counters[run_id]


# Singleton instance
_transparency_logger: Optional[TransparencyLogger] = None


def get_transparency_logger() -> TransparencyLogger:
    """Get or create singleton transparency logger."""
    global _transparency_logger
    if _transparency_logger is None:
        _transparency_logger = TransparencyLogger()
    return _transparency_logger

