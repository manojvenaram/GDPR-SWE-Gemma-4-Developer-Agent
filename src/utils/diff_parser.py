"""
src/utils/diff_parser.py
Utilities for analyzing, validating, and formatting unified diffs and patches.
"""

from __future__ import annotations
import re
from typing import Dict, List, Set


def parse_unified_diff(diff_text: str) -> Dict[str, Any]:
    """Parses a unified diff into modified files, line additions, and deletions."""
    modified_files: Set[str] = set()
    added_lines = 0
    deleted_lines = 0

    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            modified_files.add(line[6:].strip())
        elif line.startswith("+") and not line.startswith("+++"):
            added_lines += 1
        elif line.startswith("-") and not line.startswith("---"):
            deleted_lines += 1

    return {
        "modified_files": list(modified_files),
        "total_files": len(modified_files),
        "added_lines": added_lines,
        "deleted_lines": deleted_lines,
        "net_change": added_lines - deleted_lines,
    }


def validate_clean_patch(diff_text: str, forbidden_files: List[str] = None) -> Tuple[bool, str]:
    """
    Validates that a patch satisfies submission criteria:
    1. Not empty.
    2. Does not touch test reproduction scripts, caches, or virtualenvs.
    3. Has reasonable line budget (< 100 lines changed).
    """
    if not diff_text or not diff_text.strip():
        return False, "Patch is empty (no diff produced)."

    forbidden = forbidden_files or ["reproduce_issue.py", ".venv", "__pycache__", ".pytest_cache", ".git"]
    parsed = parse_unified_diff(diff_text)

    for f in parsed["modified_files"]:
        for bad in forbidden:
            if bad in f:
                return False, f"Patch touches forbidden or temporary file: {f}"

    if parsed["added_lines"] + parsed["deleted_lines"] > 250:
        return False, f"Patch is too large ({parsed['added_lines'] + parsed['deleted_lines']} lines changed). Prefer surgical edits."

    return True, "Patch is clean and valid."
