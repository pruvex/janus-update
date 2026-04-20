#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from tests.vision_evaluator import VisionEvaluator
from pathlib import Path

evaluator = VisionEvaluator()
clusters = ['cluster_4']
base_path = Path(__file__).parent / 'tests' / 'vision_matrix'

print('=== FINAL MATERIAL-INTELLIGENCE CERTIFICATION ===')
for cluster_name in clusters:
    cluster_path = base_path / cluster_name
    if cluster_path.exists():
        results = evaluator.test_cluster(cluster_path)
        evaluator.print_results(results, cluster_name)
        
        # Show only FAIL results
        failed_results = [r for r in results if r.status == 'FAIL']
        if failed_results:
            print('\nFAILED TESTS:')
            for r in failed_results:
                print(f'  {r.image_name} - {r.category}: Expected "{r.expected}", Found "{r.found}"')
        else:
            print('\n🎉 MATERIAL-INTELLIGENCE 100% CERTIFIED!')
