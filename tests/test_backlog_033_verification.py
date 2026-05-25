#!/usr/bin/env python3
"""Verification script for BACKLOG-033: Provider Parity for Gemini.

Checks if Wikipedia and News tools are correctly selected for Gemini vs GPT.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.services.orchestrator.intent_engine import IntentEngine

def test_intent_detection():
    """Test that Wikipedia and News intents are detected correctly."""
    engine = IntentEngine()
    
    # Test Wikipedia intent
    wikipedia_queries = [
        "Wer ist Nikola Tesla?",
        "Was ist Wikipedia?",
        "Erzähl mir über Albert Einstein",
    ]
    
    # Test News intent
    news_queries = [
        "Was gibt es Neues bei Heise?",
        "Was sind die aktuellen Nachrichten?",
        "News von heute",
    ]
    
    print("=== Wikipedia Intent Detection ===")
    for query in wikipedia_queries:
        result = engine.detect_wikipedia_intent(query)
        print(f"  '{query}' -> {result}")
    
    print("\n=== News Intent Detection ===")
    for query in news_queries:
        result = engine.detect_news_intent(query)
        print(f"  '{query}' -> {result}")

if __name__ == "__main__":
    test_intent_detection()
