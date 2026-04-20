#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from tests.vision_evaluator import VisionEvaluator
from pathlib import Path

def run_diamond_stress_test():
    """3-Fach-Stabilitäts-Lauf für Quad-Cluster Zertifizierung"""
    evaluator = VisionEvaluator()
    clusters = ['cluster_1', 'cluster_2', 'cluster_3', 'cluster_4']
    base_path = Path(__file__).parent / 'tests' / 'vision_matrix'
    
    print('🎯 DIAMOND-STRESS-TEST: 3-FACH-STABILITÄTS-LAUF FÜR QUAD-CLUSTER')
    print('=' * 80)
    
    all_runs_results = []
    
    for run_num in range(1, 4):
        print(f'\n🔹 LAUF {run_num}/3')
        print('-' * 40)
        
        run_results = []
        for cluster_name in clusters:
            cluster_path = base_path / cluster_name
            if cluster_path.exists():
                results = evaluator.test_cluster(cluster_path)
                run_results.extend(results)
        
        # Calculate run statistics
        total = len(run_results)
        passed = sum(1 for r in run_results if r.status == 'PASS')
        failed = total - passed
        percentage = (passed / total * 100) if total > 0 else 0
        
        print(f'LAUF {run_num}: {passed}/{total} Treffer ({percentage:.1f}%)')
        if failed > 0:
            print(f'❌ {failed} Tests fehlgeschlagen')
            failed_results = [r for r in run_results if r.status == 'FAIL']
            for r in failed_results[:5]:  # Show first 5 failures
                print(f'   {r.image_name} - {r.category}: Expected "{r.expected}", Found "{r.found}"')
        else:
            print('✅ PERFEKTER LAUF!')
        
        all_runs_results.append((run_num, passed, total, percentage))
    
    # Final analysis
    print('\n' + '=' * 80)
    print('🏆 DIAMOND-STRESS-TEST ANALYSE')
    print('=' * 80)
    
    all_perfect = all(run[1] == run[2] for run in all_runs_results)
    
    if all_perfect and len(all_runs_results) == 3:
        avg_pass = sum(run[1] for run in all_runs_results) / 3
        avg_total = sum(run[2] for run in all_runs_results) / 3
        avg_percentage = sum(run[3] for run in all_runs_results) / 3
        
        print(f'🎉 DIAMOND-STRESS-TEST ERFOLGREICH!')
        print(f'📊 DURCHSCHNITTLICHE ERGEBNISSE:')
        print(f'   Durchschnitt: {avg_pass:.0f}/{avg_total:.0f} Treffer ({avg_percentage:.1f}%)')
        print(f'   Stabilitäts-Quote: 3/3 Durchgänge absolut identisch')
        print(f'   Status: QUAD-CLUSTER-DIAMOND-CERTIFIED ✅')
        return True
    else:
        print(f'❌ DIAMOND-STRESS-TEST NICHT BESTANDEN')
        print(f'   Stabilitäts-Quote: {len([r for r in all_runs_results if r[1] == r[2]])}/3 Durchgänge identisch')
        return False

if __name__ == "__main__":
    success = run_diamond_stress_test()
    sys.exit(0 if success else 1)
