---
description: Run Memory QA Tests and display Health Dashboard
---

## /test-memory Skill

Führt die vollständige Memory QA Test-Suite aus und zeigt das Diamond-Health-Dashboard.

## Steps

1. **Load Test Suite**
   ```python
   from backend.services.memory_qa import MemoryTestRunner
   from pathlib import Path
   
   suite_path = Path("backend/data/fixtures/memory_test_suite.json")
   test_cases = MemoryTestRunner.load_test_suite(suite_path)
   print(f"Loaded {len(test_cases)} test cases from {suite_path}")
   ```

2. **Initialize Runner**
   ```python
   runner = MemoryTestRunner()
   ```

3. **Execute Test Suite**
   ```python
   import asyncio
   
   report = asyncio.run(runner.run_test_suite(test_cases))
   print(f"Suite complete: {report.passed}/{report.total_tests} passed")
   ```

4. **Generate Dashboard**
   ```python
   dashboard = runner.generate_health_dashboard(report.reports)
   print(dashboard)
   ```

5. **Return Summary**
   - Display the ASCII dashboard in chat
   - Log overall score and pass rate
   - Highlight any failed tests

// turbo
6. **Run immediately if called via slash command**
   - Auto-execute steps 1-5 without user confirmation
   - Show dashboard output directly in chat
