#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from tests.vision_evaluator import VisionEvaluator
from pathlib import Path

evaluator = VisionEvaluator()
clusters = ['cluster_1', 'cluster_2', 'cluster_3', 'cluster_4']
base_path = Path(__file__).parent / 'tests' / 'vision_matrix'

all_failed = []
for cluster_name in clusters:
    cluster_path = base_path / cluster_name
    if cluster_path.exists():
        results = evaluator.test_cluster(cluster_path)
        failed_results = [r for r in results if r.status == 'FAIL']
        if failed_results:
            print(f'\nFAILED TESTS in {cluster_name}:')
            for r in failed_results:
                print(f'  {r.image_name} - {r.category}: Expected "{r.expected}", Found "{r.found}"')
                all_failed.append((cluster_name, r))

print(f'\nTOTAL FAILED: {len(all_failed)} tests')
for cluster_name, r in all_failed:
    print(f'  {cluster_name}: {r.image_name} - {r.category}')
