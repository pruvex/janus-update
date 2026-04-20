#!/usr/bin/env python3
"""
Final Validation Script - Testet nur die erwarteten Kategorien
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

def final_validation():
    """Final Validation für Cluster 1 & 2"""
    
    results = []
    total_tests = 0
    passed_tests = 0
    
    for cluster_name in ["cluster_1", "cluster_2"]:
        base_path = Path(__file__).parent / "tests" / "vision_matrix" / cluster_name
        
        print(f"\n{'='*80}")
        print(f"CLUSTER {cluster_name.upper()}")
        print(f"{'='*80}")
        
        for image_file in sorted(base_path.glob("*.jpg")):
            # Lade Ground Truth
            json_file = image_file.with_suffix('.jpg.json')
            with open(json_file, 'r', encoding='utf-8-sig') as f:
                ground_truth = json.load(f)
            
            expected = ground_truth.get('expected', {})
            if not expected:
                continue
                
            print(f"\n📸 {image_file.name}")
            print(f"🎯 EXPECTED: {expected}")
            
            # Verarbeite Bild
            db = SessionLocal()
            with open(image_file, 'rb') as f:
                image_bytes = f.read()
            
            vision_result = vision_service.process_image(image_bytes, db)
            db.close()
            
            # Extrahiere Fakten
            feature_report = vision_result.get('feature_report', {})
            context = vision_result.get('context', {})
            facts = get_mapped_portrait_facts(feature_report, context, vision_mode="eval")
            
            print(f"🔍 FOUND: {facts}")
            print(f"🔍 FACTS KEYS: {list(facts.keys())}")
            
            # Teste nur erwartete Kategorien
            image_results = []
            for category, expected_value in expected.items():
                found_value = facts.get(category, "")
                print(f"🔍 DEBUG: Looking for '{category}' in facts, found: '{found_value}'")
                status = str(expected_value).lower() == str(found_value).lower()
                total_tests += 1
                if status:
                    passed_tests += 1
                    print(f"  ✅ {category}: {expected_value}")
                else:
                    print(f"  ❌ {category}: {expected_value} vs '{found_value}'")
                
                image_results.append({
                    'image': image_file.name,
                    'cluster': cluster_name,
                    'category': category,
                    'expected': expected_value,
                    'found': found_value,
                    'status': 'PASS' if status else 'FAIL'
                })
            
            results.extend(image_results)
    
    # Summary
    print(f"\n{'='*100}")
    print(f"FINAL VALIDATION REPORT")
    print(f"{'='*100}")
    print(f"📊 GESAMT-SCORE: {passed_tests}/{total_tests} Treffer ({passed_tests/total_tests*100:.1f}%)")
    
    # Cluster Summary
    for cluster_name in ["cluster_1", "cluster_2"]:
        cluster_results = [r for r in results if r['cluster'] == cluster_name]
        cluster_passed = sum(1 for r in cluster_results if r['status'] == 'PASS')
        cluster_total = len(cluster_results)
        cluster_percentage = (cluster_passed / cluster_total * 100) if cluster_total > 0 else 0
        
        print(f"\n📈 {cluster_name.upper()}: {cluster_passed}/{cluster_total} Treffer ({cluster_percentage:.1f}%)")
        
        # Show failed tests
        failed = [r for r in cluster_results if r['status'] == 'FAIL']
        if failed:
            print("❌ Failed Tests:")
            for f in failed:
                print(f"   {f['image']}.{f['category']}: {f['expected']} vs {f['found']}")
    
    print(f"\n🎯 MISSION STATUS: {'✅ SUCCESS' if passed_tests == total_tests else '❌ NEEDS WORK'}")
    print(f"{'='*100}")

if __name__ == "__main__":
    final_validation()
