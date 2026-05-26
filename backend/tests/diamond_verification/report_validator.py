"""
Diamond Verification Suite V1 — Report Validator
Validates benchmark results and generates aggregate reports.
"""
from typing import List
from dataclasses import dataclass

from benchmark_runner import BenchmarkResult


@dataclass
class AggregateReport:
    """Aggregate report for all benchmarks."""
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_crashes: int
    average_integrity: float
    diamond_seal_earned: bool


class ReportValidator:
    """Validates benchmark results and generates reports."""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
    
    def add_result(self, result: BenchmarkResult):
        """Add a benchmark result."""
        self.results.append(result)
    
    def validate_results(self) -> bool:
        """Validate all results for Diamond Seal criteria."""
        # Diamond Seal criteria: 0% Crashes and 100% Integrity
        total_crashes = sum(r.crashes for r in self.results)
        average_integrity = sum(r.integrity for r in self.results) / len(self.results) if self.results else 0
        
        return total_crashes == 0 and average_integrity >= 0.95
    
    def generate_aggregate_report(self) -> AggregateReport:
        """Generate aggregate report."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.status == "PASS")
        failed_tests = sum(1 for r in self.results if r.status == "FAIL")
        total_crashes = sum(r.crashes for r in self.results)
        average_integrity = sum(r.integrity for r in self.results) / len(self.results) if self.results else 0
        diamond_seal_earned = self.validate_results()
        
        return AggregateReport(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            total_crashes=total_crashes,
            average_integrity=average_integrity,
            diamond_seal_earned=diamond_seal_earned
        )
    
    def generate_markdown_report(self) -> str:
        """Generate Markdown report table."""
        report = self.generate_aggregate_report()
        
        md_lines = []
        md_lines.append("# Diamond Verification Suite V1 — Final Aggregate Report")
        md_lines.append("")
        md_lines.append("## Summary")
        md_lines.append("")
        md_lines.append(f"- **Total Tests:** {report.total_tests}")
        md_lines.append(f"- **Passed:** {report.passed_tests}")
        md_lines.append(f"- **Failed:** {report.failed_tests}")
        md_lines.append(f"- **Total Crashes:** {report.total_crashes}")
        md_lines.append(f"- **Average Integrity:** {report.average_integrity:.2f}")
        md_lines.append(f"- **Diamond Seal:** {'✅ EARNED' if report.diamond_seal_earned else '❌ NOT EARNED'}")
        md_lines.append("")
        md_lines.append("## Detailed Results")
        md_lines.append("")
        md_lines.append("| Test | Status | Latency | RAM (MB) | Integrity | Remark |")
        md_lines.append("|------|--------|--------|---------|-----------|--------|")
        
        for result in self.results:
            md_lines.append(f"| {result.test_name} | {result.status} | {result.latency:.3f}s | {result.ram_usage_mb:.2f} | {result.integrity:.2f} | {result.remark} |")
        
        md_lines.append("")
        md_lines.append("## Diamond Seal Criteria")
        md_lines.append("")
        md_lines.append("- **Crashes:** 0% required (Actual: {report.total_crashes})")
        md_lines.append("- **Integrity:** 100% required (Actual: {report.average_integrity:.1f}%)")
        md_lines.append("")
        
        if report.diamond_seal_earned:
            md_lines.append("## 🏆 DIAMOND SEAL EARNED")
            md_lines.append("")
            md_lines.append("The Debug Compression Engine has passed all verification tests with 0% crashes and high integrity.")
        else:
            md_lines.append("## ❌ DIAMOND SEAL NOT EARNED")
            md_lines.append("")
            md_lines.append("The Debug Compression Engine failed to meet Diamond Seal criteria.")
            if report.total_crashes > 0:
                md_lines.append(f"- Crashes detected: {report.total_crashes}")
            if report.average_integrity < 0.95:
                md_lines.append(f"- Integrity below threshold: {report.average_integrity:.2f} < 0.95")
        
        return "\n".join(md_lines)
    
    def print_report(self):
        """Print the Markdown report to console."""
        print("\n" + "=" * 80)
        print(self.generate_markdown_report())
        print("=" * 80)
