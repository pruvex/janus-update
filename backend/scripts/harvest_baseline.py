#!/usr/bin/env python3
"""
Harvest Baseline Script
Runs 5 consecutive real-run batch tests to establish statistical baseline.
"""
import asyncio
import json
import time
import requests
from typing import Dict, List, Any
from datetime import datetime


BASE_URL = "http://localhost:8001"
BATCH_TEST_ENDPOINT = f"{BASE_URL}/api/system/run-batch-tests"
DECISION_REPORT_ENDPOINT = f"{BASE_URL}/api/system/decision-report"
OUTPUT_FILE = "baseline_results.json"


async def run_batch_test(run_number: int) -> Dict[str, Any]:
    """Run a single batch test."""
    print(f"[HARVEST] Starting Run {run_number}/5...")
    
    try:
        response = requests.get(
            BATCH_TEST_ENDPOINT,
            params={"real_run": "true"},
            timeout=300
        )
        response.raise_for_status()
        result = response.json()
        print(f"[HARVEST] Run {run_number} started: {result.get('message', 'OK')}")
        return result
    except Exception as e:
        print(f"[HARVEST] ERROR in Run {run_number}: {e}")
        return {"error": str(e)}


async def wait_for_matrix_update(sleep_seconds: int = 120):
    """Wait for D10 matrix to update."""
    print(f"[HARVEST] Waiting {sleep_seconds}s for matrix update...")
    await asyncio.sleep(sleep_seconds)
    print("[HARVEST] Wait complete")


async def get_decision_report() -> Dict[str, Any]:
    """Get the decision report."""
    print("[HARVEST] Fetching decision report...")
    
    try:
        response = requests.get(DECISION_REPORT_ENDPOINT, timeout=60)
        response.raise_for_status()
        report = response.json()
        print(f"[HARVEST] Decision report fetched: {len(report.get('skills', []))} skills")
        return report
    except Exception as e:
        print(f"[HARVEST] ERROR fetching decision report: {e}")
        return {"error": str(e)}


def extract_top_5_skills(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract top 5 skills with highest escalation_rate or lowest pass_rate."""
    health_matrix = report.get("health_matrix", {})
    matrix = health_matrix.get("matrix", {})
    
    # Convert matrix dict to list of skill entries
    skills = []
    for skill_id, skill_data in matrix.items():
        skills.append({
            "skill_id": skill_id,
            **skill_data
        })
    
    # Sort by escalation_rate (descending) then pass_rate (ascending)
    sorted_skills = sorted(
        skills,
        key=lambda x: (
            x.get("escalation_rate", 0),
            1 - x.get("pass_rate", 1)
        ),
        reverse=True
    )
    
    top_5 = sorted_skills[:5]
    print(f"[HARVEST] Top 5 skills extracted:")
    for i, skill in enumerate(top_5, 1):
        print(f"  {i}. {skill.get('skill_id', 'unknown')} - Pass Rate: {skill.get('pass_rate', 0):.2%}, Escalation Rate: {skill.get('escalation_rate', 0):.2%}")
    
    return top_5


def save_baseline_results(results: Dict[str, Any], filename: str = OUTPUT_FILE):
    """Save baseline results to JSON file."""
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[HARVEST] Results saved to {filename}")


async def main():
    """Main execution function."""
    print("=" * 60)
    print("💎 BASELINE HARVEST STARTING")
    print("=" * 60)
    
    # Run 5 consecutive batch tests
    runs = []
    for i in range(1, 6):
        result = await run_batch_test(i)
        runs.append({
            "run_number": i,
            "timestamp": datetime.now().isoformat(),
            "result": result
        })
        
        # Wait between runs (except after the last run)
        if i < 5:
            await wait_for_matrix_update()
    
    # Get final decision report
    decision_report = await get_decision_report()
    
    # Extract top 5 skills
    top_5_skills = extract_top_5_skills(decision_report)
    
    # Compile baseline results
    baseline_results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_runs": 5,
            "endpoint": BATCH_TEST_ENDPOINT
        },
        "runs": runs,
        "decision_report": decision_report,
        "top_5_skills": top_5_skills
    }
    
    # Save results
    save_baseline_results(baseline_results)
    
    print("=" * 60)
    print("💎 BASELINE HARVEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
