#!/usr/bin/env python3
"""Generate ai-sessions/DEV_TIMELINE.md from Serena custom context.

This script parses the Serena MCP custom context YAML configured in Cursor
settings and extracts a concise development timeline into the project under
ai-sessions/DEV_TIMELINE.md.

It is resilient to missing YAML parsers by treating the YAML as plain text and
extracting the instructions block following "instructions: |".
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


CURSOR_SETTINGS = Path.home() / "Library/Application Support/Cursor/User/settings.json"
OUTPUT_FILE = Path(__file__).resolve().parents[1] / "ai-sessions/DEV_TIMELINE.md"


def read_cursor_settings(settings_path: Path) -> dict:
    if not settings_path.exists():
        raise FileNotFoundError(f"Cursor settings not found: {settings_path}")
    with settings_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_serena_context_path(settings: dict) -> Path | None:
    # settings["mcpServers"]["serena"]["args"] is an array of CLI args
    try:
        args = settings["mcpServers"]["serena"]["args"]
    except Exception:
        return None
    if not isinstance(args, list):
        return None
    for i, val in enumerate(args):
        if val == "--context" and i + 1 < len(args):
            return Path(args[i + 1])
    return None


def extract_instructions_text(yaml_text: str) -> str:
    # Find the line containing "instructions:" and then collect the indented block below it
    lines = yaml_text.splitlines()
    instructions_start = None
    for idx, line in enumerate(lines):
        if re.match(r"^\s*instructions\s*:\s*\|\s*$", line):
            instructions_start = idx + 1
            break
    if instructions_start is None:
        # Fallback: return whole file
        return yaml_text
    collected: list[str] = []
    for line in lines[instructions_start:]:
        # lines in the block are indented by two spaces in our file; accept any >= 2
        if re.match(r"^\s{2,}\S|^\s*$", line):
            collected.append(re.sub(r"^\s{2}", "", line))
        else:
            break
    return "\n".join(collected).strip() + "\n"


def extract_sections(markdown_text: str, section_titles: list[str]) -> str:
    # Extract each requested section (inclusive) until the next "## " heading
    out_parts: list[str] = []
    for title in section_titles:
        pattern = re.compile(rf"(^##\s+{re.escape(title)}\s*$)", re.IGNORECASE | re.MULTILINE)
        m = pattern.search(markdown_text)
        if not m:
            continue
        start = m.start(1)
        # find next top-level heading
        next_heading = re.search(r"^##\s+.+$", markdown_text[m.end(1):], re.MULTILINE)
        if next_heading:
            end = m.end(1) + next_heading.start()
        else:
            end = len(markdown_text)
        out_parts.append(markdown_text[start:end].rstrip())
    return "\n\n".join(out_parts).strip() + ("\n" if out_parts else "")


def build_timeline_md(instructions_md: str) -> str:
    header = "# Development Timeline\n\n"
    # Prefer specific sections if available; otherwise include the whole instructions
    sections = extract_sections(
        instructions_md,
        [
            "Development Timeline",
            "September 14, 2025 Sessions Summary",
        ],
    )
    if not sections:
        sections = instructions_md.strip() + "\n"
    return header + sections


def main() -> int:
    try:
        settings = read_cursor_settings(CURSOR_SETTINGS)
        ctx_path = get_serena_context_path(settings)
        if not ctx_path or not ctx_path.exists():
            print("Could not resolve Serena context path from Cursor settings.")
            return 1
        with ctx_path.open("r", encoding="utf-8") as f:
            yaml_text = f.read()
        instructions_md = extract_instructions_text(yaml_text)
        timeline_md = build_timeline_md(instructions_md)
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with OUTPUT_FILE.open("w", encoding="utf-8") as f:
            f.write(timeline_md)
        print(f"Wrote timeline: {OUTPUT_FILE}")
        return 0
    except Exception as e:
        print(f"Error generating timeline: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())


