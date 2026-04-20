"""
Memory utility functions for Diamond-OS V3.5
Lightweight JSONL-based memory storage
NO complex server, NO Docker - just file-based storage
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any

# Memory file path
MEMORY_FILE = Path(".diamond/memory/memory.jsonl")


def add_memory_entry(entry_type: str, content: str) -> None:
    """
    Write a JSONL line to memory.jsonl
    
    Args:
        entry_type: Type of entry (e.g., 'pattern', 'fail', 'success')
        content: The content to store
    """
    timestamp = "INIT" if entry_type == "system" else str(os.times().system)
    
    entry = {
        "type": entry_type,
        "content": content,
        "timestamp": timestamp
    }
    
    # Ensure directory exists
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Append to file (JSONL format)
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get_recent_entries(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Read the last N entries from memory
    
    Args:
        limit: Number of entries to return (default: 10)
    
    Returns:
        List of memory entries
    """
    entries = []
    
    if not MEMORY_FILE.exists():
        return entries
    
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
    
    # Return last N entries
    return entries[-limit:] if len(entries) > limit else entries


def search_memory(keyword: str) -> List[Dict[str, Any]]:
    """
    Simple keyword search in memory
    
    Args:
        keyword: Search term (case-insensitive)
    
    Returns:
        List of matching memory entries
    """
    matches = []
    keyword_lower = keyword.lower()
    
    if not MEMORY_FILE.exists():
        return matches
    
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entry = json.loads(line)
                    content = str(entry.get("content", "")).lower()
                    entry_type = str(entry.get("type", "")).lower()
                    
                    if keyword_lower in content or keyword_lower in entry_type:
                        matches.append(entry)
                except json.JSONDecodeError:
                    continue
    
    return matches


def find_similar_issue(context: str) -> List[Dict[str, Any]]:
    """
    Smart search for similar issues/patterns in memory
    
    Args:
        context: Search context (e.g., "import error on module B")
    
    Returns:
        List of similar entries sorted by relevance (match count)
    """
    # Split context into keywords
    keywords = [kw.lower() for kw in context.split() if len(kw) > 2]
    
    if not keywords:
        return []
    
    scored_matches = []
    
    if not MEMORY_FILE.exists():
        return []
    
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entry = json.loads(line)
                    # Check all relevant fields
                    text_fields = [
                        str(entry.get("content", "")),
                        str(entry.get("issue", "")),
                        str(entry.get("solution", "")),
                        str(entry.get("attempt", ""))
                    ]
                    all_text = " ".join(text_fields).lower()
                    
                    # Score by number of keyword matches
                    match_count = sum(1 for kw in keywords if kw in all_text)
                    
                    if match_count > 0:
                        scored_matches.append((match_count, entry))
                except json.JSONDecodeError:
                    continue
    
    # Sort by match count (descending) and return entries
    scored_matches.sort(key=lambda x: x[0], reverse=True)
    return [entry for score, entry in scored_matches]


def store_learning(issue: str, solution: str, tags: list = None) -> None:
    """
    Store structured learning entry in memory
    
    Args:
        issue: Description of the problem/issue
        solution: The solution/workaround
        tags: Optional list of tags (e.g., ["bug", "api", "import"])
    """
    entry = {
        "type": "learning",
        "issue": issue,
        "solution": solution,
        "tags": tags or [],
        "timestamp": str(os.times().system)
    }
    
    # Ensure directory exists
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Append to file (JSONL format)
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def store_failure(issue: str, attempt: str) -> None:
    """
    Store failed attempt in memory to avoid repeating same mistakes
    
    Args:
        issue: Description of the problem
        attempt: What was tried and failed
    """
    entry = {
        "type": "failure",
        "issue": issue,
        "attempt": attempt,
        "timestamp": str(os.times().system)
    }
    
    # Ensure directory exists
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Append to file (JSONL format)
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
