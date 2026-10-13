#!/usr/bin/env python3
"""Shared DCSS data-file parser (key = first non-comment, non-blank line)."""
import re

SEP = re.compile(r"^%{4,}\s*$", re.M)


def keyed_entries(text):
    """Return ordered list of (key, body) pairs. Comment-only blocks are skipped."""
    out = []
    for block in SEP.split(text):
        lines = block.splitlines()
        for i, ln in enumerate(lines):
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            out.append((s, "\n".join(lines[i + 1:]).strip("\n")))
            break
    return out


def parse(path):
    """Return dict key -> body (first wins) for a data file; {} when missing."""
    if not path.exists():
        return {}
    out = {}
    for k, b in keyed_entries(path.read_text(encoding="utf-8", errors="replace")):
        out.setdefault(k, b)
    return out
