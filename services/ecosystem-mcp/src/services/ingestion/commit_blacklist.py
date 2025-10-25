"""
Commit Blacklist - Skip known problematic commits

This module maintains a list of commits that are known to cause hangs or issues
during processing. These commits are skipped early to prevent job hangs.

Reasons for blacklisting:
- Commits that hang in GitPython C-level code (immune to async timeouts)
- Commits with corrupted tree objects that cause infinite loops
- Commits with malformed data that cause segfaults

Usage:
    from .commit_blacklist import is_blacklisted, get_blacklist_reason
    
    if is_blacklisted(commit.sha):
        reason = get_blacklist_reason(commit.sha)
        logger.warning(f"Skipping blacklisted commit {commit.sha[:8]}: {reason}")
        continue
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Blacklisted commits with reasons
# Key: commit SHA (full or prefix)
# Value: reason for blacklisting
BLACKLISTED_COMMITS: Dict[str, str] = {
    "f1fc2691db8221cbe043bda42cb46e368fb16dd5": (
        "Hangs indefinitely in GitPython tree traversal. "
        "Likely corrupted tree object that causes C-level infinite loop. "
        "Immune to async timeouts. Observed hanging 270s+ in jobs c656e9a2 and 721c1722."
    ),
    "f1fc2691": "Same as above (short SHA)",
    "2e3977c2": (
        "Hangs indefinitely in GitPython tree traversal. "
        "Same behavior as f1fc2691. Likely corrupted tree object that causes C-level infinite loop. "
        "Immune to async timeouts. Observed hanging 150s+ in job 20f2bf81."
    ),
}

# Blacklist patterns (for matching partial SHAs or patterns)
BLACKLIST_PATTERNS = [
    "f1fc2691",  # Known problematic commit #1
    "2e3977c2",  # Known problematic commit #2
]


def is_blacklisted(commit_sha: str) -> bool:
    """
    Check if a commit is blacklisted.
    
    Args:
        commit_sha: Full or partial commit SHA
    
    Returns:
        True if commit should be skipped, False otherwise
    """
    # Check exact match (full SHA or short SHA)
    if commit_sha in BLACKLISTED_COMMITS:
        return True
    
    # Check if commit starts with any blacklisted pattern
    for pattern in BLACKLIST_PATTERNS:
        if commit_sha.startswith(pattern):
            return True
    
    # Check if any blacklisted SHA starts with the provided SHA (prefix match)
    for blacklisted_sha in BLACKLISTED_COMMITS.keys():
        if blacklisted_sha.startswith(commit_sha):
            return True
    
    return False


def get_blacklist_reason(commit_sha: str) -> Optional[str]:
    """
    Get the reason why a commit is blacklisted.
    
    Args:
        commit_sha: Full or partial commit SHA
    
    Returns:
        Reason string if blacklisted, None otherwise
    """
    # Try exact match first
    if commit_sha in BLACKLISTED_COMMITS:
        return BLACKLISTED_COMMITS[commit_sha]
    
    # Try finding matching blacklisted SHA
    for blacklisted_sha, reason in BLACKLISTED_COMMITS.items():
        if blacklisted_sha.startswith(commit_sha) or commit_sha.startswith(blacklisted_sha):
            return reason
    
    return None


def add_to_blacklist(commit_sha: str, reason: str) -> None:
    """
    Add a commit to the blacklist at runtime.
    
    Args:
        commit_sha: Full or partial commit SHA
        reason: Reason for blacklisting
    """
    BLACKLISTED_COMMITS[commit_sha] = reason
    logger.warning(f"🚫 Added commit {commit_sha[:8]} to blacklist: {reason}")


def get_blacklist_stats() -> Dict[str, int]:
    """
    Get statistics about the blacklist.
    
    Returns:
        Dict with blacklist statistics
    """
    return {
        "total_blacklisted": len(BLACKLISTED_COMMITS),
        "patterns": len(BLACKLIST_PATTERNS)
    }


def log_blacklist_summary() -> None:
    """Log a summary of all blacklisted commits."""
    logger.info(f"🚫 Commit Blacklist: {len(BLACKLISTED_COMMITS)} commits blacklisted")
    for sha, reason in BLACKLISTED_COMMITS.items():
        logger.info(f"  • {sha[:8]}: {reason[:100]}...")

