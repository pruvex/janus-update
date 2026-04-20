#!/usr/bin/env python3
"""
Debug Script für Cluster 1 spezifische Probleme
"""

import os
import sys
import json
from pathlib import Path

# Backend Imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from data.database import SessionLocal
from services.vision_service import vision_service
from services.vision.utils import get_mapped_portrait_facts

def debug_cluster1():
    """Debug Cluster 1 spezifische Probleme"""
    
    base_path = Path(__file__).parent / "tests" / "vision_matrix" / "cluster_1"
    
    for image_file in sorted(base_path.glob("*.jpg")):
        print(f"\n{'='*80}")
        print(f"DEBUG: {image_file.name}")
        print(f"{'='*80}")
        
        # Lade Ground Truth
        json_file = image_file.with_suffix('.jpg.json')
        with open(json_file, 'r', encoding='utf-8-sig') as f:
            ground_truth = json.load(f)
        
        print(f"EXPECTED: {ground_truth.get('expected', {})}")
        
        # Verarbeite Bild
        db = SessionLocal()
        with open(image_file, 'rb') as f:
            image_bytes = f.read()
        
        vision_result = vision_service.process_image(image_bytes, db)
        db.close()
        
        # Extrahiere Fakten
        feature_report = vision_result.get('feature_report', {})
        context = vision_result.get('context', {})
        
        print(f"\nFEATURE REPORT:")
        for category, items in feature_report.items():
            if items:
                print(f"  {category}:")
                for item in items:
                    print(f"    - {item.get('label', '')} (score: {item.get('score', 0.0):.4f})")
        
        facts = get_mapped_portrait_facts(feature_report, context, vision_mode="eval")
        print(f"\nFINAL FACTS: {facts}")
        
        # Vergleiche mit Expected
        expected = ground_truth.get('expected', {})
        print(f"\nCOMPARISON:")
        for key, expected_value in expected.items():
            found_value = facts.get(key)
            status = "✅ PASS" if str(expected_value) == str(found_value) else "❌ FAIL"
            print(f"  {key}: {expected_value} vs {found_value} {status}")

if __name__ == "__main__":
    debug_cluster1()
