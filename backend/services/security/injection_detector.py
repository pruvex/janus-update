"""
Prompt Injection Detection Module

Provides pattern-based detection for prompt injection attacks, specifically
focusing on Instruction Overrides and Rule Bypassing patterns.

Patterns detected:
- ignore (all|rules|instructions|constraints)
- delete (files|data|records)
- override (rules|security)
- bypass (security|rules)
- forget (instructions|rules)
"""

import re
from typing import Optional


# Define injection patterns with their types
INJECTION_PATTERNS = [
    (r"\bignore\s+(all|rules|instructions|constraints|previous|everything|this)\b", "ignore"),
    (r"\bdelete\s+(all\s+)?(files|data|records|database|everything)\b", "delete"),
    (r"\boverride\s+(rules|security|constraints|everything)\b", "override"),
    (r"\bbypass\s+(security|rules|restrictions|everything)\b", "bypass"),
    (r"\bforget\s+(instructions|rules|constraints|everything)\b", "forget"),
]

# Compile regex patterns with case-insensitive flag
COMPILED_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE), injection_type)
    for pattern, injection_type in INJECTION_PATTERNS
]


def detect_injection(user_input: str) -> bool:
    """
    Detect if user input contains prompt injection patterns.
    
    Args:
        user_input: The user input string to check for injection patterns
        
    Returns:
        True if any injection pattern is detected, False otherwise
    """
    if not user_input or not isinstance(user_input, str):
        return False
    
    for pattern, _ in COMPILED_PATTERNS:
        if pattern.search(user_input):
            return True
    
    return False


def get_injection_type(user_input: str) -> Optional[str]:
    """
    Get the type of injection detected in user input.
    
    Args:
        user_input: The user input string to check for injection patterns
        
    Returns:
        The injection type string (e.g., "ignore", "delete") if detected,
        None otherwise
    """
    if not user_input or not isinstance(user_input, str):
        return None
    
    for pattern, injection_type in COMPILED_PATTERNS:
        if pattern.search(user_input):
            return injection_type
    
    return None


def get_all_detected_patterns(user_input: str) -> list[str]:
    """
    Get all injection patterns detected in user input.
    
    Args:
        user_input: The user input string to check for injection patterns
        
    Returns:
        List of injection type strings detected in the input
    """
    if not user_input or not isinstance(user_input, str):
        return []
    
    detected_types = []
    for pattern, injection_type in COMPILED_PATTERNS:
        if pattern.search(user_input):
            detected_types.append(injection_type)
    
    return detected_types
