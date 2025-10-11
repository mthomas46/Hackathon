"""
Logs endpoints for external log processing.

Provides access to application logs for analysis and debugging.
"""

import logging
import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class LogEntry(BaseModel):
    """Single log entry."""
    timestamp: str
    level: str
    logger: str
    message: str
    extra: Optional[dict] = None


class LogsResponse(BaseModel):
    """Logs query response."""
    entries: List[LogEntry]
    total: int
    limit: int
    offset: int


class LogFile(BaseModel):
    """Log file information."""
    name: str
    path: str
    size_bytes: int
    modified_at: str
    lines: int


@router.get(
    "/list",
    response_model=List[LogFile],
    summary="List log files",
    description="List available log files"
)
async def list_log_files(
    log_dir: str = Query("./logs", description="Log directory path")
):
    """
    List available log files.
    
    Args:
        log_dir: Log directory path
    
    Returns:
        List of log files with metadata
    """
    log_path = Path(log_dir)
    
    if not log_path.exists():
        raise HTTPException(status_code=404, detail="Log directory not found")
    
    files = []
    for file_path in log_path.glob("*.log"):
        if file_path.is_file():
            stat = file_path.stat()
            
            # Count lines
            try:
                with open(file_path, 'r') as f:
                    line_count = sum(1 for _ in f)
            except:
                line_count = 0
            
            files.append(LogFile(
                name=file_path.name,
                path=str(file_path),
                size_bytes=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                lines=line_count
            ))
    
    return files


@router.get(
    "/tail",
    summary="Tail log file",
    description="Get last N lines from log file"
)
async def tail_log(
    file: str = Query("ecosystem-mcp.log", description="Log file name"),
    lines: int = Query(100, ge=1, le=10000, description="Number of lines"),
    log_dir: str = Query("./logs", description="Log directory path")
):
    """
    Get last N lines from log file.
    
    Args:
        file: Log file name
        lines: Number of lines to return
        log_dir: Log directory path
    
    Returns:
        Last N lines of log file
    """
    log_path = Path(log_dir) / file
    
    if not log_path.exists():
        raise HTTPException(status_code=404, detail="Log file not found")
    
    try:
        with open(log_path, 'r') as f:
            all_lines = f.readlines()
            tail_lines = all_lines[-lines:]
            
        return {
            "file": file,
            "lines_returned": len(tail_lines),
            "content": "".join(tail_lines)
        }
    except Exception as e:
        logger.error(f"Failed to read log file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read log: {e}")


@router.get(
    "/search",
    summary="Search logs",
    description="Search logs by pattern"
)
async def search_logs(
    query: str = Query(..., description="Search query"),
    file: Optional[str] = Query(None, description="Specific log file (or all if None)"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    since: Optional[str] = Query(None, description="Start time (ISO format)"),
    limit: int = Query(100, ge=1, le=10000),
    log_dir: str = Query("./logs", description="Log directory path")
):
    """
    Search logs for matching entries.
    
    Args:
        query: Search query (case-insensitive)
        file: Optional specific log file
        level: Optional log level filter
        since: Optional start timestamp
        limit: Maximum results
        log_dir: Log directory path
    
    Returns:
        Matching log entries
    """
    log_path = Path(log_dir)
    
    if not log_path.exists():
        raise HTTPException(status_code=404, detail="Log directory not found")
    
    # Determine files to search
    if file:
        files = [log_path / file]
    else:
        files = list(log_path.glob("*.log"))
    
    matching_lines = []
    query_lower = query.lower()
    
    for log_file in files:
        if not log_file.exists():
            continue
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    # Simple search - case insensitive
                    if query_lower in line.lower():
                        # Optional level filter
                        if level and level.upper() not in line:
                            continue
                        
                        matching_lines.append({
                            "file": log_file.name,
                            "line": line.strip()
                        })
                        
                        if len(matching_lines) >= limit:
                            break
        except Exception as e:
            logger.error(f"Error reading {log_file}: {e}")
    
    return {
        "query": query,
        "matches": len(matching_lines),
        "results": matching_lines[:limit]
    }


@router.get(
    "/download",
    summary="Download log file",
    description="Download complete log file"
)
async def download_log(
    file: str = Query(..., description="Log file name"),
    log_dir: str = Query("./logs", description="Log directory path")
):
    """
    Download complete log file.
    
    Args:
        file: Log file name
        log_dir: Log directory path
    
    Returns:
        Log file content
    """
    log_path = Path(log_dir) / file
    
    if not log_path.exists():
        raise HTTPException(status_code=404, detail="Log file not found")
    
    try:
        with open(log_path, 'r') as f:
            content = f.read()
        
        return {
            "file": file,
            "size_bytes": len(content),
            "content": content
        }
    except Exception as e:
        logger.error(f"Failed to read log file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read log: {e}")


@router.delete(
    "/clear",
    summary="Clear old logs",
    description="Clear logs older than specified days"
)
async def clear_old_logs(
    days: int = Query(30, ge=1, le=365, description="Keep logs from last N days"),
    log_dir: str = Query("./logs", description="Log directory path")
):
    """
    Clear logs older than specified days.
    
    Args:
        days: Keep logs from last N days
        log_dir: Log directory path
    
    Returns:
        Number of files deleted
    """
    log_path = Path(log_dir)
    
    if not log_path.exists():
        raise HTTPException(status_code=404, detail="Log directory not found")
    
    cutoff_time = datetime.now() - timedelta(days=days)
    deleted = 0
    
    for log_file in log_path.glob("*.log"):
        if log_file.is_file():
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            
            if mtime < cutoff_time:
                try:
                    log_file.unlink()
                    deleted += 1
                    logger.info(f"Deleted old log: {log_file.name}")
                except Exception as e:
                    logger.error(f"Failed to delete {log_file.name}: {e}")
    
    return {
        "deleted": deleted,
        "cutoff_date": cutoff_time.isoformat()
    }

