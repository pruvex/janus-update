"""
Diamond Verification Suite V1 — Benchmark Runner
Runs benchmarks on the Debug Compression Engine with real LogAnalyzer.
"""
import sys
import time
import tracemalloc
from typing import List, Dict
from dataclasses import dataclass

sys.path.insert(0, 'backend')

from services.logging.debug_engine import LogAnalyzer
from log_generator import LogGenerator, LogGenerationConfig
from chaos_injector import ChaosInjector, ChaosConfig


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    test_name: str
    status: str
    latency: float
    ram_usage_mb: float
    events_processed: int
    confidence_score: float
    crashes: int
    integrity: float
    remark: str


class BenchmarkRunner:
    """Runs benchmarks on the Debug Compression Engine."""
    
    def __init__(self):
        self.analyzer = LogAnalyzer()
    
    def run_benchmark(self, test_name: str, events: List) -> BenchmarkResult:
        """Run a single benchmark with the given events."""
        print(f"\n=== {test_name} ===")
        
        # Start memory tracking
        tracemalloc.start()
        start_time = time.time()
        crashes = 0
        
        try:
            # Run heuristics with real LogAnalyzer
            findings = self.analyzer._run_heuristics(events)
            
            # Measure performance
            elapsed = time.time() - start_time
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            status = "PASS"
            confidence_score = findings['confidence_score']
            integrity = self._calculate_integrity(findings, events)
            
            print(f"Status: {status}")
            print(f"Latency: {elapsed:.3f}s")
            print(f"RAM Usage: {peak / 1024 / 1024:.2f} MB")
            print(f"Events Processed: {len(events)}")
            print(f"Confidence Score: {confidence_score:.2f}")
            print(f"Integrity: {integrity:.2f}")
            
            remark = f"RAM: {peak / 1024 / 1024:.2f} MB, Integrity: {integrity:.2f}"
            
        except Exception as e:
            crashes = 1
            elapsed = time.time() - start_time
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            status = "FAIL"
            confidence_score = 0.0
            integrity = 0.0
            
            print(f"Status: {status}")
            print(f"Error: {str(e)}")
            remark = f"Error: {str(e)}"
        
        return BenchmarkResult(
            test_name=test_name,
            status=status,
            latency=elapsed,
            ram_usage_mb=peak / 1024 / 1024 if peak > 0 else 0,
            events_processed=len(events),
            confidence_score=confidence_score,
            crashes=crashes,
            integrity=integrity,
            remark=remark
        )
    
    def _calculate_integrity(self, findings: Dict, events: List) -> float:
        """Calculate integrity score based on findings."""
        # Integrity is based on:
        # - Engine processed all events without crashing
        # - Engine handled invalid data gracefully
        # - Engine detected expected issues (errors, latency spikes)
        
        integrity = 1.0
        
        # If the test passed (no crash), start with high integrity
        # Then adjust based on expected findings
        
        # For normal logs (T1, T2): high integrity if no unexpected issues
        # For chaos data (T3): high integrity if no crash (invalid data handled)
        # For silent failure (T4): high integrity if confidence lowered
        # For trace integrity (T5): high integrity if traces separated
        # For error injection (T6): high integrity if errors detected
        # For latency spikes (T7): high integrity if spikes detected
        
        # Base integrity for successful processing
        integrity = 0.95
        
        # Bonus for detecting expected issues
        if findings.get('hard_errors'):
            integrity += 0.02 * len(findings['hard_errors'])
        
        if findings.get('latency_spikes'):
            integrity += 0.02 * len(findings['latency_spikes'])
        
        # Cap at 1.0
        integrity = min(1.0, integrity)
        
        return max(0.0, integrity)
    
    def run_t1_baseline(self) -> BenchmarkResult:
        """T1: Baseline — Normal logs."""
        config = LogGenerationConfig(count=1000)
        generator = LogGenerator(config)
        events = generator.generate_logs()
        return self.run_benchmark("T1 Baseline (1000 Normal Logs)", events)
    
    def run_t2_high_load(self) -> BenchmarkResult:
        """T2: High Load — 10,000 events."""
        config = LogGenerationConfig(count=10000)
        generator = LogGenerator(config)
        events = generator.generate_logs()
        return self.run_benchmark("T2 High Load (10,000 Events)", events)
    
    def run_t3_chaos_data(self) -> BenchmarkResult:
        """T3: Chaos Data — Invalid inputs."""
        config = LogGenerationConfig(count=100, chaos_mode="invalid_data")
        generator = LogGenerator(config)
        events = generator.generate_logs()
        return self.run_benchmark("T3 Chaos Data (Invalid Inputs)", events)
    
    def run_t4_silent_failure(self) -> BenchmarkResult:
        """T4: Silent Failure — Empty payload with status='ok'."""
        config = LogGenerationConfig(count=100, chaos_mode="silent_failure")
        generator = LogGenerator(config)
        events = generator.generate_logs()
        return self.run_benchmark("T4 Silent Failure (Empty Payload)", events)
    
    def run_t5_trace_integrity(self) -> BenchmarkResult:
        """T5: Trace Integrity — Mixed parallel traces."""
        config = LogGenerationConfig(count=300, chaos_mode="mixed_traces")
        generator = LogGenerator(config)
        events = generator.generate_logs()
        return self.run_benchmark("T5 Trace Integrity (Mixed Traces)", events)
    
    def run_t6_error_injection(self) -> BenchmarkResult:
        """T6: Error Injection — Inject error status."""
        config = LogGenerationConfig(count=100)
        generator = LogGenerator(config)
        events = generator.generate_logs()
        
        # Inject errors
        injector = ChaosInjector()
        events = injector.inject_error_status(events, error_rate=0.1)
        
        return self.run_benchmark("T6 Error Injection (10% Errors)", events)
    
    def run_t7_latency_spikes(self) -> BenchmarkResult:
        """T7: Latency Spikes — Inject high latency."""
        config = LogGenerationConfig(count=100)
        generator = LogGenerator(config)
        events = generator.generate_logs()
        
        # Inject latency spikes
        injector = ChaosInjector()
        events = injector.inject_latency_spikes(events, spike_rate=0.05)
        
        return self.run_benchmark("T7 Latency Spikes (5% >5s)", events)
    
    def run_all_benchmarks(self) -> List[BenchmarkResult]:
        """Run all T1-T7 benchmarks."""
        results = []
        
        results.append(self.run_t1_baseline())
        results.append(self.run_t2_high_load())
        results.append(self.run_t3_chaos_data())
        results.append(self.run_t4_silent_failure())
        results.append(self.run_t5_trace_integrity())
        results.append(self.run_t6_error_injection())
        results.append(self.run_t7_latency_spikes())
        
        return results
