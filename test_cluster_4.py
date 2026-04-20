#!/usr/bin/env python3
"""
Schneller Test für nur Cluster 4 mit Debug-Logs
"""
import sys
import os
sys.path.append('.')

from backend.tests.vision_evaluator import VisionEvaluator
from pathlib import Path

def test_cluster_4():
    cluster_dir = Path("backend/tests/vision_matrix/cluster_4")
    
    if not cluster_dir.exists():
        print(f"❌ Cluster-Verzeichnis nicht gefunden: {cluster_dir}")
        return
    
    print(f"=== TESTE NUR CLUSTER 4 ===")
    print(f"Pfad: {cluster_dir}")
    
    evaluator = VisionEvaluator(cluster_dir)
    evaluator.run_tests()
    evaluator.print_results()
    
    print(f"\n=== ERGEBNISSE CLUSTER 4 ===")
    for result in evaluator.test_results:
        status = "✅ PASS" if result.status == "PASS" else "❌ FAIL"
        print(f"{result.image_name}: {result.category} - {status}")
        if result.status != "PASS":
            print(f"  Erwartet: {result.expected}")
            print(f"  Gefunden: {result.found}")

if __name__ == "__main__":
    test_cluster_4()
