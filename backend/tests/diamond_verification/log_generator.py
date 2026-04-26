"""
Diamond Verification Suite V1 — Log Generator
Generates synthetic log events for testing the Debug Compression Engine.
"""
import sys
from datetime import datetime, timedelta
from typing import List
from dataclasses import dataclass

sys.path.insert(0, 'backend')

from data.schemas_logging import LogEventCreate


@dataclass
class LogGenerationConfig:
    """Configuration for log generation."""
    count: int = 100
    chaos_mode: str = None  # None, 'invalid_data', 'silent_failure', 'mixed_traces'
    skill_count: int = 10
    trace_count: int = 100


class LogGenerator:
    """Generates synthetic log events for testing."""
    
    def __init__(self, config: LogGenerationConfig = None):
        self.config = config or LogGenerationConfig()
    
    def generate_normal_logs(self, count: int) -> List[LogEventCreate]:
        """Generate normal log events."""
        events = []
        base_time = datetime.utcnow()
        
        for i in range(count):
            skill = f"skill_{i % self.config.skill_count}"
            latency_ms = 100 + (i % 1000)
            payload = {"message": f"Normal message {i}"}
            trace_id = f"trace_{i % self.config.trace_count}"
            timestamp = base_time + timedelta(milliseconds=i * 10)
            
            event = LogEventCreate(
                timestamp=timestamp,
                event_type="log",
                skill=skill,
                latency_ms=latency_ms,
                trace_id=trace_id,
                payload=payload
            )
            events.append(event)
        
        return events
    
    def generate_invalid_data_logs(self, count: int) -> List[LogEventCreate]:
        """Generate logs with invalid data for chaos testing."""
        events = []
        base_time = datetime.utcnow()
        
        for i in range(count):
            # Cycle through 4 types of invalid data
            if i % 4 == 0:
                skill = None  # Missing skill
            else:
                skill = f"skill_{i % self.config.skill_count}"
            
            if i % 4 == 1:
                latency_ms = -500  # Invalid latency
            else:
                latency_ms = 100 + (i % 1000)
            
            if i % 4 == 2:
                payload = {"message": "Kaputtes JSON {..."}  # Broken JSON
            else:
                payload = {"message": f"Normal message {i}"}
            
            if i % 4 == 3:
                trace_id = "x" * 6000  # Overly long trace_id
            else:
                trace_id = f"trace_{i % self.config.trace_count}"
            
            timestamp = base_time + timedelta(milliseconds=i * 10)
            
            event = LogEventCreate(
                timestamp=timestamp,
                event_type="log",
                skill=skill,
                latency_ms=latency_ms,
                trace_id=trace_id,
                payload=payload
            )
            events.append(event)
        
        return events
    
    def generate_silent_failure_logs(self, count: int) -> List[LogEventCreate]:
        """Generate logs with silent failures (status='ok' but empty payload)."""
        events = []
        base_time = datetime.utcnow()
        
        for i in range(count):
            skill = f"skill_{i % self.config.skill_count}"
            latency_ms = 100 + (i % 1000)
            
            # Every 3rd event is a silent failure
            if i % 3 == 0:
                payload = {"message": "Tool executed successfully but returned empty result"}
                status = "ok"
            else:
                payload = {"message": f"Normal message {i}"}
                status = None
            
            trace_id = f"trace_{i % self.config.trace_count}"
            timestamp = base_time + timedelta(milliseconds=i * 10)
            
            event = LogEventCreate(
                timestamp=timestamp,
                event_type="log",
                skill=skill,
                latency_ms=latency_ms,
                trace_id=trace_id,
                status=status,
                payload=payload
            )
            events.append(event)
        
        return events
    
    def generate_mixed_trace_logs(self, count: int, trace_count: int = 3) -> List[LogEventCreate]:
        """Generate logs with mixed parallel traces."""
        events = []
        base_time = datetime.utcnow()
        
        for i in range(count):
            skill = f"skill_{i % self.config.skill_count}"
            latency_ms = 100 + (i % 1000)
            payload = {"message": f"Message {i}"}
            
            # Create parallel traces with mixed timestamps
            trace_id = f"trace_{i % trace_count}"
            offset = (i % 5) * timedelta(seconds=10)
            timestamp = base_time + offset + timedelta(milliseconds=i * 10)
            
            event = LogEventCreate(
                timestamp=timestamp,
                event_type="log",
                skill=skill,
                latency_ms=latency_ms,
                trace_id=trace_id,
                payload=payload
            )
            events.append(event)
        
        return events
    
    def generate_logs(self) -> List[LogEventCreate]:
        """Generate logs based on configuration."""
        if self.config.chaos_mode == "invalid_data":
            return self.generate_invalid_data_logs(self.config.count)
        elif self.config.chaos_mode == "silent_failure":
            return self.generate_silent_failure_logs(self.config.count)
        elif self.config.chaos_mode == "mixed_traces":
            return self.generate_mixed_trace_logs(self.config.count, trace_count=3)
        else:
            return self.generate_normal_logs(self.config.count)
